from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from BUILD.build_3h_capture_to_deploy_bundle_pipeline import (  # noqa: E402
    build_write_deploy_bundle_1a_from_capture_bundle_path,
)
from VAL.val_2a_deploy_bundle_validator import validate_deploy_bundle_1a  # noqa: E402

FIXTURE_DIR = REPO_ROOT / "dev" / "fixtures" / "production_milestone_2"
OUT_DIR = REPO_ROOT / "dev" / "_smoke_artifacts" / "production_milestone_2"

SELECTOR_ACTIONS = {"click_selector", "wait_for_selector", "type_selector_secret"}


def _read_json(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise AssertionError(f"Expected JSON object: {path}")
    return obj


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _iter_json_values(obj: Any) -> Any:
    if isinstance(obj, Mapping):
        for value in obj.values():
            yield from _iter_json_values(value)
        return
    if isinstance(obj, list):
        for value in obj:
            yield from _iter_json_values(value)
        return
    yield obj


def _has_todo_placeholder(obj: Any) -> bool:
    for value in _iter_json_values(obj):
        if not isinstance(value, str):
            continue
        text = value.strip().upper()
        if text == "TODO" or text.startswith("TODO_") or text.startswith("TODO:"):
            return True
    return False


def _iter_steps(steps: Any) -> Any:
    if not isinstance(steps, list):
        return
    for step in steps:
        if not isinstance(step, Mapping):
            continue
        yield step
        if step.get("action") == "repeat":
            yield from _iter_steps(step.get("steps"))


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


def _build_fixture(fixture_name: str, output_name: str) -> dict[str, Any]:
    capture_path = FIXTURE_DIR / fixture_name
    deploy_path = OUT_DIR / output_name
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    build_write_deploy_bundle_1a_from_capture_bundle_path(
        str(capture_path),
        str(deploy_path),
        strict=True,
        require_version_fingerprint=True,
        require_selector_ref=True,
        pretty=False,
        atomic=True,
    )
    return _read_json(deploy_path)


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


def _assert_deploy_bundle_shape(bundle: Mapping[str, Any]) -> None:
    if bundle.get("schema_id") != "DEPLOY_BUNDLE_1A":
        raise AssertionError(f"Expected DEPLOY_BUNDLE_1A, got: {bundle.get('schema_id')!r}")
    if bundle.get("name") != "production_milestone_2_golden":
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
    if _has_todo_placeholder(bundle):
        raise AssertionError("Generated deploy bundle must not contain TODO placeholders")


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


def test_positive_capture_to_deploy_bundle() -> None:
    first = _build_fixture("capture_bundle_golden.json", "deploy_bundle_golden.generated.json")
    second = _build_fixture("capture_bundle_golden.json", "deploy_bundle_golden.generated.second.json")

    _assert_deploy_bundle_shape(first)
    _assert_selector_ref_first(first)
    _assert_production_valid(first)

    if _canonical_json(first) != _canonical_json(second):
        raise AssertionError("Repeated BUILD-3H generation from the same fixture must be deterministic")
    if first.get("fingerprint", {}).get("sha256") != second.get("fingerprint", {}).get("sha256"):
        raise AssertionError("Repeated generation must preserve the deploy bundle fingerprint")


def test_reject_todo_placeholder() -> None:
    bundle = _build_fixture("capture_bundle_todo_placeholder.json", "deploy_bundle_todo_placeholder.generated.json")
    _assert_production_invalid(bundle, "unresolved TODO placeholder")


def test_selector_ref_first_generation_or_rejection() -> None:
    bundle = _build_fixture("capture_bundle_raw_selector.json", "deploy_bundle_raw_selector.generated.json")
    report = _production_validation(bundle)
    if report.get("ok"):
        _assert_selector_ref_first(bundle)
        return
    errors = report.get("errors", [])
    if not any("raw selector is not allowed" in str(e.get("message", "")) for e in errors if isinstance(e, Mapping)):
        raise AssertionError(f"Expected raw selector rejection or selector_ref conversion, got: {report!r}")


def test_reject_registry_mapping_failure() -> None:
    bundle = _build_fixture("capture_bundle_registry_failure.json", "deploy_bundle_registry_failure.generated.json")
    _assert_production_invalid(bundle, "action has no ACT-1A runtime implementation")


def dev_smoke() -> None:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    test_positive_capture_to_deploy_bundle()
    test_reject_todo_placeholder()
    test_selector_ref_first_generation_or_rejection()
    test_reject_registry_mapping_failure()


if __name__ == "__main__":
    dev_smoke()
    print("DEV_SMOKE_OK: production_milestone_2")
