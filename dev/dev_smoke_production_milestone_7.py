from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from REGISTRY.action_contract_inspector import (  # noqa: E402
    PROVEN_GOLDEN_PATH_ACTIONS,
    build_action_contract_report,
)
from VAL.val_2a_deploy_bundle_validator import validate_deploy_bundle_1a  # noqa: E402

LOG_REJECTION_FIXTURE = (
    REPO_ROOT
    / "dev"
    / "fixtures"
    / "production_milestone_1"
    / "deploy_bundle_registry_failure.json"
)
PROTECTED_MILESTONE_PREFIXES = (
    "dev/dev_smoke_production_milestone_1.py",
    "dev/dev_smoke_production_milestone_2.py",
    "dev/dev_smoke_production_milestone_3.py",
    "dev/dev_smoke_production_milestone_4.py",
    "dev/dev_smoke_production_milestone_5.py",
    "dev/dev_smoke_production_milestone_6.py",
    "dev/fixtures/production_milestone_1/",
    "dev/fixtures/production_milestone_2/",
    "dev/fixtures/production_milestone_3/",
    "dev/fixtures/production_milestone_4/",
    "dev/fixtures/production_milestone_5/",
    "dev/fixtures/production_milestone_6/",
)


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_no_milestone_1_to_6_changes() -> None:
    cp = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if cp.returncode != 0:
        raise AssertionError(f"git status failed\nstdout={cp.stdout}\nstderr={cp.stderr}")

    changed: list[str] = []
    for raw in cp.stdout.splitlines():
        if not raw.strip():
            continue
        path = raw[3:].replace("\\", "/")
        if path.startswith(PROTECTED_MILESTONE_PREFIXES):
            changed.append(raw)
    assert not changed, "Milestone 1-6 files changed:\n" + "\n".join(changed)


def _assert_log_rejected_by_production_validation() -> None:
    bundle = _read_json(LOG_REJECTION_FIXTURE)
    report = validate_deploy_bundle_1a(bundle, production=True)
    assert report["ok"] is False, report
    assert any(
        "action has no ACT-1A runtime implementation: log" in str(error.get("message", ""))
        for error in report["errors"]
    ), report


def dev_smoke() -> None:
    report = build_action_contract_report()
    data = report.as_dict()

    assert report.registry_actions, data
    assert report.schema_actions, data
    assert report.snap_actions, data
    assert report.act_actions, data

    assert PROVEN_GOLDEN_PATH_ACTIONS <= report.positive_golden_path_actions, data
    assert data["classifications"]["proven_golden_path"] == sorted(PROVEN_GOLDEN_PATH_ACTIONS), data
    assert data["classifications"]["positive_golden_path_actions"] == sorted(
        report.positive_golden_path_actions
    ), data
    assert PROVEN_GOLDEN_PATH_ACTIONS <= report.act_actions, data

    assert "log" in report.registry_actions, data
    assert "log" in report.schema_actions, data
    assert "log" in report.snap_actions, data
    assert "log" not in report.act_actions, data
    assert "log" in data["classifications"]["declared_not_implemented"], data
    assert "log" in data["classifications"]["declared_non_act"], data

    field_mismatch_names = {item["name"] for item in report.field_mismatches}
    assert {"strategy_vs_by", "script_vs_js", "secret_ref_fields"} <= field_mismatch_names, data

    _assert_log_rejected_by_production_validation()
    _assert_no_milestone_1_to_6_changes()


if __name__ == "__main__":
    dev_smoke()
    print("DEV_SMOKE_OK: production_milestone_7")
