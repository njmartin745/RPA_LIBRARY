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

FIXTURE_DIR = REPO_ROOT / "dev" / "fixtures" / "production_milestone_1"
OUT_ROOT = REPO_ROOT / "dev" / "_smoke_artifacts" / "production_milestone_1"
RUN_OUT_DIR: Path | None = None


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
        if value != "#pm1-ready-button":
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


def _assert_nonempty(path: Path) -> None:
    assert path.exists(), f"missing artifact: {path}"
    assert path.is_file(), f"artifact is not a file: {path}"
    assert path.stat().st_size > 0, f"empty artifact: {path}"


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
    from RUN.run_1a_workflow_runner import run_workflow

    workflow_path = output_dir / "runtime" / "workflow.json"
    _write_json(workflow_path, workflow)

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
    from HISTORY.history_1b_step_outcomes import build_step_outcome, append_step_outcome
    from REPORT.report_1d_generate_reports import generate_standard_reports

    workflow = deploy_bundle.get("workflow")
    if not isinstance(workflow, Mapping):
        raise AssertionError("deploy bundle workflow missing")
    steps = workflow.get("steps")
    if not isinstance(steps, list):
        raise AssertionError("deploy bundle workflow.steps missing")

    manifest = build_run_manifest(
        run_output_dir=output_dir,
        workflow_name=str(workflow.get("name") or deploy_bundle.get("name") or "production_milestone_1"),
        run_id=str(runtime_summary.get("run_id") or "production-milestone-1"),
        workflow_path=output_dir / "runtime" / "workflow.json",
        bundle_path=bundle_path,
        bundle_version=str(deploy_bundle.get("version") or ""),
        workflow_version=str(deploy_bundle.get("version") or ""),
        inputs={"fixture": bundle_path.name},
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
                workflow_name=str(workflow.get("name") or deploy_bundle.get("name") or "production_milestone_1"),
                step_index=idx,
                step=step,
                status=status,
                notes="production_milestone_1",
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


def test_positive_golden_path() -> None:
    from RUN.run_1e_deploy_bundle_runner_adapter import run_deploy_bundle_1a_with_meta
    from VAL.val_2a_deploy_bundle_validator import assert_deploy_bundle_1a
    from WORKFLOWS.workflow_1g_deploy_bundle_loader import load_deploy_bundle_1a_from_path

    bundle_path = FIXTURE_DIR / "deploy_bundle_golden.json"
    deploy_bundle = _read_json(bundle_path)

    assert_deploy_bundle_1a(deploy_bundle, require_version_fingerprint=True, require_selector_ref=True, production=True)
    loaded = load_deploy_bundle_1a_from_path(str(bundle_path), validate=True)

    output_dir = _run_dir() / "positive"
    output_dir.mkdir(parents=True, exist_ok=True)

    original_make_driver = _patch_driver_factory()

    def runner(*, workflow: dict[str, Any], selector_pack: dict[str, Any], run_meta: dict[str, Any]) -> dict[str, Any]:
        return _run_existing_runtime_path(
            workflow=workflow,
            selector_pack=selector_pack,
            run_meta=run_meta,
            bundle_path=bundle_path,
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
        bundle_path=bundle_path,
        runtime_summary=runtime_summary,
        output_dir=output_dir,
    )
    _assert_required_artifacts(output_dir)


def test_reject_todo_placeholder() -> None:
    from VAL.val_2a_deploy_bundle_validator import validate_deploy_bundle_1a

    deploy_bundle = _read_json(FIXTURE_DIR / "deploy_bundle_todo_placeholder.json")
    report = validate_deploy_bundle_1a(
        deploy_bundle,
        require_version_fingerprint=True,
        require_selector_ref=True,
        production=True,
    )
    assert report["ok"] is False, report
    assert any("TODO placeholder" in e["message"] for e in report["errors"]), report


def test_reject_registry_mapping_failure() -> None:
    from VAL.val_2a_deploy_bundle_validator import validate_deploy_bundle_1a

    deploy_bundle = _read_json(FIXTURE_DIR / "deploy_bundle_registry_failure.json")
    report = validate_deploy_bundle_1a(
        deploy_bundle,
        require_version_fingerprint=True,
        require_selector_ref=True,
        production=True,
    )
    assert report["ok"] is False, report
    assert any("no ACT-1A runtime implementation" in e["message"] for e in report["errors"]), report


def dev_smoke() -> None:
    global RUN_OUT_DIR

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    RUN_OUT_DIR = OUT_ROOT / f"run_{time.time_ns()}_{os.getpid()}"
    RUN_OUT_DIR.mkdir(parents=True, exist_ok=False)

    test_positive_golden_path()
    test_reject_todo_placeholder()
    test_reject_registry_mapping_failure()


if __name__ == "__main__":
    dev_smoke()
    print("DEV_SMOKE_OK: production_milestone_1")
