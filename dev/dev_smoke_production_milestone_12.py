from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Iterable, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPO_ROOT / "dev" / "fixtures" / "telemetry_contracts"

JSON_FIXTURES = {
    "run_metrics_1a_example.json": "RUN-METRICS-1A",
    "record_manifest_1a_example.json": "RECORD-MANIFEST-1A",
}
JSONL_FIXTURES = {
    "record_outcomes_1a_example.jsonl": "RECORD-OUTCOME-1A",
    "attempt_history_1a_example.jsonl": "ATTEMPT-HISTORY-1A",
}
REQUIRED_COMMON = {"schema", "example_only", "runtime_generated", "notes", "run_id"}
FORBIDDEN_KEY_PARTS = (
    "password",
    "token",
    "cookie",
    "credential",
    "sensitive",
    "secret_value",
    "raw_payload",
    "downloaded_content",
)
FORBIDDEN_VALUE_PARTS = (
    "SHOULD_NOT_APPEAR",
    "password",
    "token",
    "cookie",
    "sensitive",
    "secret-value",
)


def _load_json(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(obj, dict), f"expected JSON object: {path}"
    return obj


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        text = line.strip()
        if not text:
            continue
        obj = json.loads(text)
        assert isinstance(obj, dict), f"expected JSON object at {path}:{line_no}"
        records.append(obj)
    assert records, f"expected at least one record: {path}"
    return records


def _walk(obj: Any) -> Iterable[tuple[str | None, Any]]:
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            yield str(key), value
            yield from _walk(value)
    elif isinstance(obj, list):
        for value in obj:
            yield None, value


def _assert_no_forbidden_secrets(obj: Mapping[str, Any], path: Path) -> None:
    for key, value in _walk(obj):
        if key is not None:
            lowered = key.lower()
            if any(part in lowered for part in FORBIDDEN_KEY_PARTS):
                raise AssertionError(f"forbidden secret-bearing key {key!r} in {path}")
        if isinstance(value, str):
            lowered_value = value.lower()
            if any(part.lower() in lowered_value for part in FORBIDDEN_VALUE_PARTS):
                raise AssertionError(f"forbidden secret-like value in {path}: {value!r}")


def _assert_common(obj: Mapping[str, Any], *, path: Path, schema: str) -> None:
    missing = REQUIRED_COMMON - set(obj.keys())
    assert not missing, f"missing required keys in {path}: {sorted(missing)}"
    assert obj["schema"] == schema, f"wrong schema in {path}: {obj.get('schema')!r}"
    assert obj["example_only"] is True, f"example_only must be true in {path}"
    assert obj["runtime_generated"] is False, f"runtime_generated must be false in {path}"
    assert "Contract example only" in str(obj["notes"]), f"notes must label fixture as contract example: {path}"
    resolved = path.resolve()
    assert str(resolved).startswith(str(FIXTURE_DIR.resolve())), f"fixture outside telemetry fixture dir: {path}"
    assert "dev/_smoke_artifacts" not in resolved.as_posix(), f"fixture must not be under smoke artifacts: {path}"
    _assert_no_forbidden_secrets(obj, path)


def _assert_unproven_nulls(obj: Mapping[str, Any], schema: str, path: Path) -> None:
    if schema == "RUN-METRICS-1A":
        assert obj["timestamps"]["duration_ms"] is None, path
        assert obj["timestamps"]["finished_at_utc"] is None, path
        assert obj["manifest_records"]["total"] is None, path
        assert obj["manifest_records"]["completed"] is None, path
        assert obj["manifest_records"]["failed"] is None, path
        assert obj["manifest_records"]["skipped"] is None, path
        assert obj["attempts"]["total"] is None, path
        assert obj["attempts"]["retry_attempts"] is None, path
        assert obj["attempts"]["max_attempts"] is None, path
        assert obj["attempts"]["continued_after_failure"] is None, path
        assert obj["agents"]["worker_count"] is None, path
    elif schema == "RECORD-MANIFEST-1A":
        assert obj["expected_records"]["total"] is None, path
        assert obj["expected_records"]["completed"] is None, path
        assert obj["expected_records"]["failed"] is None, path
        assert obj["expected_records"]["skipped"] is None, path
        assert obj["source"]["path"] is None, path
        assert obj["source"]["sha256"] is None, path
    elif schema == "RECORD-OUTCOME-1A":
        assert obj["timestamps"]["duration_ms"] is None, path
        assert obj["timestamps"]["finished_at_utc"] is None, path
        assert obj["attempt_count"] is None, path
        assert obj["retry_count"] is None, path
        assert obj["worker_id"] is None, path
        assert obj["error"] is None, path
    elif schema == "ATTEMPT-HISTORY-1A":
        assert obj["timestamps"]["duration_ms"] is None, path
        assert obj["timestamps"]["finished_at_utc"] is None, path
        assert obj["max_attempts"] is None, path
        assert obj["step_index"] is None, path
        assert obj["error"] is None, path


def _assert_git_status_clean() -> None:
    cp = subprocess.run(
        ["git", "status", "--short", "--branch"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if cp.returncode != 0:
        raise AssertionError(f"git status failed\nstdout={cp.stdout}\nstderr={cp.stderr}")
    allowed = {
        "docs/contracts/run_metrics_1a.md",
        "docs/contracts/record_outcomes_1a.md",
        "docs/contracts/attempt_history_1a.md",
        "docs/contracts/record_manifest_1a.md",
        "docs/analysis/operational_telemetry_contract.md",
        "dev/fixtures/telemetry_contracts/run_metrics_1a_example.json",
        "dev/fixtures/telemetry_contracts/record_outcomes_1a_example.jsonl",
        "dev/fixtures/telemetry_contracts/attempt_history_1a_example.jsonl",
        "dev/fixtures/telemetry_contracts/record_manifest_1a_example.json",
        "dev/dev_smoke_production_milestone_12.py",
    }
    dirty: list[str] = []
    for line in cp.stdout.splitlines()[1:]:
        if not line.strip():
            continue
        path = line[3:].replace("\\", "/")
        if path not in allowed:
            dirty.append(line)
    assert not dirty, cp.stdout


def dev_smoke() -> None:
    for filename, schema in JSON_FIXTURES.items():
        path = FIXTURE_DIR / filename
        obj = _load_json(path)
        _assert_common(obj, path=path, schema=schema)
        _assert_unproven_nulls(obj, schema, path)

    for filename, schema in JSONL_FIXTURES.items():
        path = FIXTURE_DIR / filename
        for obj in _load_jsonl(path):
            _assert_common(obj, path=path, schema=schema)
            _assert_unproven_nulls(obj, schema, path)

    _assert_git_status_clean()


if __name__ == "__main__":
    dev_smoke()
    print("DEV_SMOKE_OK: production_milestone_12")
