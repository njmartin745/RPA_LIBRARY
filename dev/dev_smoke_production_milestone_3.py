from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from BUILD.build_3h_capture_to_deploy_bundle_pipeline import (  # noqa: E402
    build_write_deploy_bundle_1a_from_capture_bundle_path,
)
from VAL.val_2a_deploy_bundle_validator import validate_deploy_bundle_1a  # noqa: E402

FIXTURE_DIR = REPO_ROOT / "dev" / "fixtures" / "production_milestone_3"
OUT_ROOT = REPO_ROOT / "dev" / "_smoke_artifacts" / "production_milestone_3"
SELECTOR_ACTIONS = {"click_selector", "wait_for_selector", "type_selector_secret"}
RUN_OUT_DIR: Path | None = None
RUNTIME_INVOCATIONS = 0


class _FakeElement:
    tag_name = "button"
    text = "Ready"

    def __init__(self) -> None:
        self.clicked = False

    def is_displayed(self) -> bool:
        return True

    def is_enabled(self) -> bool:
        return True

    def click(self) -> None:
        self.clicked = True


class _FakeDriver:
    def __init__(self) -> None:
        self.urls: list[str] = []
        self.element = _FakeElement()

    def get(self, url: str) -> None:
        self.urls.append(url)

    def find_element(self, by: str, value: str) -> _FakeElement:
        if value != "#pm3-ready-button":
            raise AssertionError(f"Unexpected selector lookup: {by}={value}")
        return self.element

    def execute_script(self, script: str, *args: Any) -> Any:
        if "return true" in script:
            return True
        return None

    def quit(self) -> None:
        return None


def _run_dir() -> Path:
    if RUN_OUT_DIR is None:
        raise AssertionError("RUN_OUT_DIR must be initialized")
    return RUN_OUT_DIR


def _read_json(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise AssertionError(f"Expected JSON object: {path}")
    return obj


def _write_json(path: Path, obj: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(obj), indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _assert_nonempty(path: Path) -> None:
    assert path.exists(), f"missing artifact: {path}"
    assert path.is_file(), f"artifact is not a file: {path}"
    assert path.stat().st_size > 0, f"empty artifact: {path}"


def _iter_steps(steps: Any) -> Any:
    if not isinstance(steps, list):
        return
    for step in steps:
        if not isinstance(step, Mapping):
            continue
        yield step
        if step.get("action") == "repeat":
            yield from _iter_steps(step.get("steps"))


def _selector_registry(selector_pack: Mapping[str, Any]) -> dict[str, str]:
    selectors = selector_pack.get("selectors")
    if not isinstance(selectors, Mapping):
        return {}
    out: dict[str, str] = {}
    for key, value in selectors.items():
        if isinstance(value, str):
            out[str(key)] = value
        elif isinstance(value, Mapping) and isinstance(value.get("selector"), str):
            out[str(key)] = str(value["selector"])
    return out


def _build_fixture(fixture_name: str, output_name: str) -> dict[str, Any]:
    deploy_path = _run_dir() / output_name
    deploy_path.parent.mkdir(parents=True, exist_ok=True)
    build_write_deploy_bundle_1a_from_capture_bundle_path(
        str(FIXTURE_DIR / fixture_name),
        str(deploy_path),
        strict=True,
        require_version_fingerprint=True,
        require_selector_ref=True,
        pretty=False,
        atomic=True,
    )
    return _read_json(deploy_path)


def _production_validation(bundle: Mapping[str, Any]) -> dict[str, Any]:
    report = validate_deploy_bundle_1a(
        bundle,
        require_version_fingerprint=True,
        require_selector_ref=True,
        production=True,
    )
    if not isinstance(report, dict):
        raise AssertionError(f"Expected validation report dict, got: {type(report)!r}")
    return report


def _assert_production_valid(bundle: Mapping[str, Any]) -> None:
    report = _production_validation(bundle)
    if not report.get("ok"):
        raise AssertionError(f"Expected production-valid deploy bundle, got: {report!r}")


def _assert_production_invalid(bundle: Mapping[str, Any], expected_message: str) -> None:
    report = _production_validation(bundle)
    if report.get("ok"):
        raise AssertionError("Expected production validation to reject deploy bundle")
    errors = report.get("errors")
    if not isinstance(errors, list):
        raise AssertionError(f"Expected validation errors list, got: {report!r}")
    if not any(expected_message in str(e.get("message", "")) for e in errors if isinstance(e, Mapping)):
        raise AssertionError(f"Expected validation error containing {expected_message!r}, got: {report!r}")


def _assert_generated_shape(bundle: Mapping[str, Any]) -> None:
    if bundle.get("schema_id") != "DEPLOY_BUNDLE_1A":
        raise AssertionError(f"Expected DEPLOY_BUNDLE_1A, got: {bundle.get('schema_id')!r}")
    if bundle.get("name") != "production_milestone_3_golden":
        raise AssertionError(f"Unexpected deploy bundle name: {bundle.get('name')!r}")
    workflow = bundle.get("workflow")
    if not isinstance(workflow, Mapping) or not isinstance(workflow.get("steps"), list):
        raise AssertionError("Generated deploy bundle must include workflow.steps")
    selector_pack = bundle.get("selector_pack")
    if not isinstance(selector_pack, Mapping) or not isinstance(selector_pack.get("selectors"), Mapping):
        raise AssertionError("Generated deploy bundle must include selector_pack.selectors")
    meta = bundle.get("meta")
    if not isinstance(meta, Mapping) or meta.get("source_schema_id") != "CAPTURE_BUNDLE_1A":
        raise AssertionError(f"Expected CAPTURE_BUNDLE_1A source metadata, got: {meta!r}")
    version = bundle.get("version")
    if not isinstance(version, str) or not version.strip():
        raise AssertionError("Generated deploy bundle must include non-empty version")
    fingerprint = bundle.get("fingerprint")
    if not isinstance(fingerprint, Mapping):
        raise AssertionError("Generated deploy bundle must include fingerprint mapping")
    sha256 = fingerprint.get("sha256")
    if not isinstance(sha256, str) or len(sha256) != 64:
        raise AssertionError(f"Generated deploy bundle must include fingerprint.sha256, got: {sha256!r}")


def _assert_selector_ref_first(bundle: Mapping[str, Any]) -> None:
    workflow = bundle.get("workflow")
    steps = workflow.get("steps") if isinstance(workflow, Mapping) else None
    for step in _iter_steps(steps):
        if step.get("action") not in SELECTOR_ACTIONS:
            continue
        if not isinstance(step.get("selector_ref"), str) or not step["selector_ref"].strip():
            raise AssertionError(f"Selector action is missing selector_ref: {step!r}")
        if "selector" in step:
            raise AssertionError(f"Runnable deploy step contains raw selector: {step!r}")


def _patch_driver_factory() -> Any:
    import PIPE.pipe_1a_run_orchestrator as orchestrator

    original = orchestrator.make_driver
    orchestrator.make_driver = lambda cfg: _FakeDriver()  # type: ignore[assignment]
    return original


def _restore_driver_factory(original: Any) -> None:
    import PIPE.pipe_1a_run_orchestrator as orchestrator

    orchestrator.make_driver = original  # type: ignore[assignment]


def _run_existing_runtime_path(
    *,
    workflow: dict[str, Any],
    selector_pack: dict[str, Any],
    run_meta: dict[str, Any],
    bundle_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    global RUNTIME_INVOCATIONS

    from RUN.run_1a_workflow_runner import run_workflow

    RUNTIME_INVOCATIONS += 1
    workflow_path = output_dir / "runtime" / "workflow.json"
    workflow_for_run = dict(workflow)
    if not isinstance(workflow_for_run.get("name"), str) or not workflow_for_run["name"].strip():
        workflow_for_run["name"] = "production_milestone_3_golden"
    _write_json(workflow_path, workflow_for_run)

    cfg_overrides = {
        "SELECTORS": _selector_registry(selector_pack),
        "LOG_JSON": True,
        "QUIET_CONSOLE": True,
        "LOG_JSONL_PATH": str(output_dir / "logs" / "run.jsonl"),
        "LOG_PATH": str(output_dir / "logs" / "run.jsonl"),
        "MANIFEST_PATH": str(output_dir / "state" / "manifest.jsonl"),
        "WORKLIST_XLSX": str(output_dir / "runtime" / "missing_worklist.xlsx"),
        "STOP_ON_ERROR": True,
        "HEADLESS": True,
        "BUNDLE_PATH": str(bundle_path),
        "BUNDLE_VERSION": run_meta.get("bundle_version"),
    }
    summary = run_workflow(workflow_path, cfg_overrides)
    run_id = summary.get("run_id") if isinstance(summary, Mapping) else None
    if isinstance(run_id, str) and run_id:
        scratch = REPO_ROOT / ".dev_tmp" / f"run_1a_steps_{run_id}.json"
        if scratch.exists():
            scratch.unlink()
    return summary


def _write_history_and_reports(
    *,
    deploy_bundle: Mapping[str, Any],
    bundle_path: Path,
    runtime_summary: Mapping[str, Any],
    output_dir: Path,
) -> None:
    from HISTORY.history_1a_run_manifest import build_run_manifest, write_run_manifest
    from HISTORY.history_1b_step_outcomes import append_step_outcome, build_step_outcome
    from REPORT.report_1d_generate_reports import generate_standard_reports

    workflow = deploy_bundle.get("workflow")
    if not isinstance(workflow, Mapping):
        raise AssertionError("deploy bundle workflow missing")
    steps = workflow.get("steps")
    if not isinstance(steps, list):
        raise AssertionError("deploy bundle workflow.steps missing")

    manifest = build_run_manifest(
        run_output_dir=output_dir,
        workflow_name=str(workflow.get("name") or deploy_bundle.get("name") or "production_milestone_3"),
        run_id=str(runtime_summary.get("run_id") or "production-milestone-3"),
        workflow_path=output_dir / "runtime" / "workflow.json",
        bundle_path=bundle_path,
        bundle_version=str(deploy_bundle.get("version") or ""),
        workflow_version=str(deploy_bundle.get("version") or ""),
        inputs={"fixture": str(FIXTURE_DIR / "capture_bundle_golden.json")},
        extra={"runtime_summary": dict(runtime_summary)},
    )
    write_run_manifest(run_output_dir=output_dir, manifest=manifest, overwrite=True)

    step_logs = runtime_summary.get("step_logs")
    if not isinstance(step_logs, list):
        raise AssertionError("runtime summary missing step_logs")
    for idx, step in enumerate(steps):
        if not isinstance(step, Mapping):
            continue
        row = step_logs[idx] if idx < len(step_logs) and isinstance(step_logs[idx], Mapping) else {}
        status = "ok" if row.get("status") == "success" else "error"
        append_step_outcome(
            run_output_dir=output_dir,
            outcome=build_step_outcome(
                workflow_name=str(workflow.get("name") or deploy_bundle.get("name") or "production_milestone_3"),
                step_index=idx,
                step=step,
                status=status,
                notes="production_milestone_3",
            ),
        )

    generate_standard_reports(run_output_dir=output_dir, overwrite=True)


def _copy_fingerprint(deploy_bundle: Mapping[str, Any], output_dir: Path) -> None:
    fp = deploy_bundle.get("fingerprint")
    if not isinstance(fp, Mapping):
        raise AssertionError("deploy bundle missing fingerprint")
    _write_json(output_dir / "bundle" / "deploy_bundle_fingerprint.json", fp)


def _assert_required_artifacts(output_dir: Path) -> None:
    expected = _read_json(FIXTURE_DIR / "expected_artifacts.json")
    required = expected.get("required")
    if not isinstance(required, list):
        raise AssertionError("expected_artifacts.json must contain required list")
    for rel in required:
        if not isinstance(rel, str):
            raise AssertionError("artifact path must be a string")
        _assert_nonempty(output_dir / rel)


def test_positive_full_golden_path() -> None:
    from RUN.run_1e_deploy_bundle_runner_adapter import run_deploy_bundle_1a_with_meta
    from WORKFLOWS.workflow_1g_deploy_bundle_loader import load_deploy_bundle_1a_from_path

    output_dir = _run_dir() / "positive"
    first_path = output_dir / "bundle" / "deploy_bundle.generated.json"
    second_path = output_dir / "bundle" / "deploy_bundle.generated.second.json"

    first = _build_fixture("capture_bundle_golden.json", "positive/bundle/deploy_bundle.generated.json")
    second = _build_fixture("capture_bundle_golden.json", "positive/bundle/deploy_bundle.generated.second.json")

    if _canonical_json(first) != _canonical_json(second):
        raise AssertionError("Repeated BUILD-3H generation from the same fixture must be deterministic")
    if first.get("fingerprint", {}).get("sha256") != second.get("fingerprint", {}).get("sha256"):
        raise AssertionError("Repeated generation must preserve the deploy bundle fingerprint")

    _assert_generated_shape(first)
    _assert_selector_ref_first(first)
    _assert_production_valid(first)

    loaded = load_deploy_bundle_1a_from_path(str(first_path), validate=True)
    _assert_production_valid(loaded)
    _assert_generated_shape(loaded)

    original_make_driver = _patch_driver_factory()

    def runner(*, workflow: dict[str, Any], selector_pack: dict[str, Any], run_meta: dict[str, Any]) -> dict[str, Any]:
        return _run_existing_runtime_path(
            workflow=workflow,
            selector_pack=selector_pack,
            run_meta=run_meta,
            bundle_path=first_path,
            output_dir=output_dir,
        )

    try:
        runtime_summary, run_meta = run_deploy_bundle_1a_with_meta(
            loaded,
            runner=runner,
            validate=True,
            require_version_fingerprint=True,
            require_selector_ref=True,
        )
    finally:
        _restore_driver_factory(original_make_driver)

    assert isinstance(runtime_summary, dict), "runtime summary must be a dict"
    assert runtime_summary.get("success") is True, runtime_summary
    assert run_meta.get("bundle_version"), run_meta

    _copy_fingerprint(loaded, output_dir)
    _write_history_and_reports(
        deploy_bundle=loaded,
        bundle_path=first_path,
        runtime_summary=runtime_summary,
        output_dir=output_dir,
    )
    _assert_required_artifacts(output_dir)

    if not second_path.exists():
        raise AssertionError(f"missing second deterministic output: {second_path}")


def test_reject_todo_placeholder_before_execution() -> None:
    before = RUNTIME_INVOCATIONS
    bundle = _build_fixture("capture_bundle_todo_placeholder.json", "negative_todo.generated.json")
    _assert_production_invalid(bundle, "unresolved TODO placeholder")
    if RUNTIME_INVOCATIONS != before:
        raise AssertionError("TODO placeholder negative case must not invoke runtime")


def test_selector_ref_first_generation_or_rejection_before_execution() -> None:
    before = RUNTIME_INVOCATIONS
    bundle = _build_fixture("capture_bundle_raw_selector.json", "negative_raw_selector.generated.json")
    report = _production_validation(bundle)
    if report.get("ok"):
        _assert_selector_ref_first(bundle)
    else:
        errors = report.get("errors", [])
        if not any("raw selector is not allowed" in str(e.get("message", "")) for e in errors if isinstance(e, Mapping)):
            raise AssertionError(f"Expected raw selector rejection or selector_ref conversion, got: {report!r}")
    if RUNTIME_INVOCATIONS != before:
        raise AssertionError("raw selector negative case must not invoke runtime")


def test_reject_registry_mapping_failure_before_execution() -> None:
    before = RUNTIME_INVOCATIONS
    bundle = _build_fixture("capture_bundle_registry_failure.json", "negative_registry.generated.json")
    _assert_production_invalid(bundle, "action has no ACT-1A runtime implementation")
    if RUNTIME_INVOCATIONS != before:
        raise AssertionError("registry/action negative case must not invoke runtime")


def dev_smoke() -> None:
    global RUN_OUT_DIR, RUNTIME_INVOCATIONS

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    RUN_OUT_DIR = OUT_ROOT / f"run_{time.time_ns()}_{os.getpid()}"
    RUN_OUT_DIR.mkdir(parents=True, exist_ok=False)
    RUNTIME_INVOCATIONS = 0

    test_positive_full_golden_path()
    test_reject_todo_placeholder_before_execution()
    test_selector_ref_first_generation_or_rejection_before_execution()
    test_reject_registry_mapping_failure_before_execution()


if __name__ == "__main__":
    dev_smoke()
    print("DEV_SMOKE_OK: production_milestone_3")
