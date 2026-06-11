from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from ACT import act_1a_action_engine
from SNAP.snap_1a_workflow_capture import ALLOWED_WORKFLOW_ACTIONS

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "REGISTRY" / "action_registry.json"
SCHEMA_PATH = REPO_ROOT / "SCHEMA" / "steps_schema.json"
FIXTURE_ROOT = REPO_ROOT / "dev" / "fixtures"

PROVEN_GOLDEN_PATH_ACTIONS = frozenset({"open", "wait_for_selector", "click_selector"})
FIELD_MISMATCHES = (
    {
        "name": "strategy_vs_by",
        "actions": ["click_selector", "type_selector_secret", "wait_for_selector"],
        "registry_schema_fields": ["strategy"],
        "runtime_fields": ["by"],
        "status": "reported_only",
    },
    {
        "name": "script_vs_js",
        "actions": ["exec_js"],
        "registry_schema_fields": ["script"],
        "capture_helper_fields": ["js"],
        "runtime_fields": ["script", "path"],
        "status": "reported_only",
    },
    {
        "name": "secret_ref_fields",
        "actions": ["type_selector_secret"],
        "registry_schema_fields": ["secret"],
        "validation_fields": ["secret_ref", "text_secret_ref", "value_secret_ref"],
        "runtime_fields": ["secret", "text"],
        "status": "reported_only",
    },
)


@dataclass(frozen=True)
class ActionContractReport:
    registry_actions: set[str]
    schema_actions: set[str]
    snap_actions: set[str]
    act_actions: set[str]
    fixture_actions: set[str]
    fixture_actions_by_file: dict[str, list[str]]
    classifications: dict[str, list[str]]
    field_mismatches: list[dict[str, Any]]

    def as_dict(self) -> dict[str, Any]:
        return {
            "registry_actions": sorted(self.registry_actions),
            "schema_actions": sorted(self.schema_actions),
            "snap_actions": sorted(self.snap_actions),
            "act_actions": sorted(self.act_actions),
            "fixture_actions": sorted(self.fixture_actions),
            "fixture_actions_by_file": {
                path: list(actions)
                for path, actions in sorted(self.fixture_actions_by_file.items())
            },
            "classifications": {
                key: list(values)
                for key, values in sorted(self.classifications.items())
            },
            "field_mismatches": self.field_mismatches,
        }


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_registry_actions(path: Path = REGISTRY_PATH) -> set[str]:
    payload = _read_json(path)
    actions = payload.get("actions")
    if not isinstance(actions, list):
        raise ValueError(f"{path} must contain an actions list")
    found: set[str] = set()
    for item in actions:
        if not isinstance(item, Mapping):
            continue
        action = item.get("action")
        if isinstance(action, str) and action.strip():
            found.add(action.strip())
    return found


def load_schema_actions(path: Path = SCHEMA_PATH) -> set[str]:
    payload = _read_json(path)
    actions = payload.get("supported_actions")
    if not isinstance(actions, list):
        raise ValueError(f"{path} must contain a supported_actions list")
    found: set[str] = set()
    for item in actions:
        if not isinstance(item, Mapping):
            continue
        action = item.get("action")
        if isinstance(action, str) and action.strip():
            found.add(action.strip())
    return found


def load_snap_actions() -> set[str]:
    return {str(action) for action in ALLOWED_WORKFLOW_ACTIONS}


def load_act_actions() -> set[str]:
    actions = getattr(act_1a_action_engine, "_ACTIONS", None)
    if not isinstance(actions, Mapping):
        raise ValueError("ACT.act_1a_action_engine._ACTIONS must be a mapping")
    return {
        str(action)
        for action, handler in actions.items()
        if isinstance(action, str) and callable(handler)
    }


def _iter_step_actions(value: Any) -> Iterable[str]:
    if isinstance(value, Mapping):
        action = value.get("action")
        if isinstance(action, str) and action.strip():
            yield action.strip()
        for child in value.values():
            yield from _iter_step_actions(child)
        return
    if isinstance(value, list):
        for child in value:
            yield from _iter_step_actions(child)


def load_production_fixture_actions(root: Path = FIXTURE_ROOT) -> tuple[set[str], dict[str, list[str]]]:
    found: set[str] = set()
    by_file: dict[str, list[str]] = {}
    for path in sorted(root.glob("production_milestone_*/*.json")):
        payload = _read_json(path)
        actions = sorted(set(_iter_step_actions(payload)))
        if not actions:
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        by_file[rel] = actions
        found.update(actions)
    return found, by_file


def build_action_contract_report() -> ActionContractReport:
    registry_actions = load_registry_actions()
    schema_actions = load_schema_actions()
    snap_actions = load_snap_actions()
    act_actions = load_act_actions()
    fixture_actions, fixture_actions_by_file = load_production_fixture_actions()

    declared_actions = registry_actions | schema_actions | snap_actions
    classifications = {
        "proven_golden_path": sorted(PROVEN_GOLDEN_PATH_ACTIONS),
        "declared_and_implemented": sorted(declared_actions & act_actions),
        "declared_not_implemented": sorted(declared_actions - act_actions),
        "implemented_not_declared": sorted(act_actions - declared_actions),
        "declared_non_act": sorted({"log", "repeat"} & declared_actions - act_actions),
        "field_mismatch": sorted({action for item in FIELD_MISMATCHES for action in item["actions"]}),
        "fixture_actions": sorted(fixture_actions),
    }

    return ActionContractReport(
        registry_actions=registry_actions,
        schema_actions=schema_actions,
        snap_actions=snap_actions,
        act_actions=act_actions,
        fixture_actions=fixture_actions,
        fixture_actions_by_file=fixture_actions_by_file,
        classifications=classifications,
        field_mismatches=[dict(item) for item in FIELD_MISMATCHES],
    )


def main() -> int:
    report = build_action_contract_report()
    print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
