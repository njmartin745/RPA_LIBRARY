"""
STATE-1B — JSONL Manifest Persistence Layer

Purpose
-------
Provide durable JSONL-based persistence for workflow execution state,
audit records, manifests, retries, and item outcomes.

This module serves as the canonical runtime persistence layer used by
PIPE orchestration components.

Public API
----------
utc_ts(...)
append_jsonl_line(...)
write_audit(...)
load_ids_from_manifest(...)
choose_active_manifest(...)
manifest_append(...)
ManifestWriter
open_manifest(...)

Dependencies
------------
Standard Library Only

Architecture Position
---------------------
RUN-1A
    ↓
PIPE-1E
    ↓
PIPE-1A
    ↓
STATE-1B

Responsibilities
----------------
- Persist item execution outcomes
- Write audit records
- Manage JSONL manifests
- Support retry manifest selection
- Provide PIPE-compatible manifest writers
- Load work items from manifest files

Manifest Selection Policy
-------------------------
Retry Manifest
        ↓
If Contains Records
        ↓
Use Retry Manifest

Else
        ↓
Use Baseline Manifest

Status
------
Audited

Notes
-----
This module intentionally remains stdlib-only and acts as the
primary persistence layer for runtime execution history,
retry tracking, and operational auditing.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, MutableMapping, Optional, Union

__all__ = [
    "utc_ts",
    "append_jsonl_line",
    "write_audit",
    "load_ids_from_manifest",
    "choose_active_manifest",
    # Compatibility API expected by PIPE-1A
    "manifest_append",
    "ManifestWriter",
    "open_manifest",
]

_PathLike = Union[str, Path]


def _coerce_path(p: _PathLike) -> Path:
    return p if isinstance(p, Path) else Path(str(p))


def utc_ts() -> str:
    """UTC timestamp suitable for audit/event records."""
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def append_jsonl_line(path: _PathLike, record: Dict[str, Any]) -> None:
    """
    Append one JSON object as a single line to a JSONL file.

    Creates parent directories as needed.
    """
    p = _coerce_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_audit(
    *,
    audit_log_path: _PathLike,
    record: Dict[str, Any],
    swallow_errors: bool = True,
    log: Optional[logging.Logger] = None,
) -> None:
    """
    Append a single audit record to an audit JSONL file.

    - Ensures record has a 'timestamp' field (utc_ts) if missing.
    - If swallow_errors=True, failures are logged (if logger provided) and ignored.
    """
    if "timestamp" not in record:
        record = dict(record)
        record["timestamp"] = utc_ts()

    try:
        append_jsonl_line(audit_log_path, record)
    except Exception:
        if log:
            log.exception("Failed to write audit record to %s", audit_log_path)
        if not swallow_errors:
            raise


def load_ids_from_manifest(manifest_path: _PathLike, *, manifest_key_field: str) -> list[str]:
    """
    Load a list of work item IDs from a manifest JSONL file.

    Each line must be a JSON object. The ID is read from manifest_key_field.
    Empty lines and blank IDs are skipped.
    """
    p = _coerce_path(manifest_path)
    if not p.exists():
        raise FileNotFoundError(f"Manifest not found: {p}")

    ids: list[str] = []
    with p.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            wid = str(rec.get(manifest_key_field, "")).strip()
            if wid:
                ids.append(wid)
    return ids


def _count_nonempty_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as fh:
        return sum(1 for ln in fh if ln.strip())


def choose_active_manifest(
    *,
    baseline_manifest: _PathLike,
    retry_manifest: _PathLike,
    log: Optional[logging.Logger] = None,
) -> Path:
    """
    Select the manifest to use for the current attempt:
    - If retry_manifest exists and contains >=1 non-empty line, use it.
    - Otherwise use baseline_manifest.
    """
    base = _coerce_path(baseline_manifest)
    retry = _coerce_path(retry_manifest)

    if retry.exists():
        try:
            remaining = _count_nonempty_lines(retry)
            if remaining > 0:
                if log:
                    log.warning(
                        "Retry manifest detected with %d remaining IDs; using %s",
                        remaining,
                        retry.name,
                    )
                return retry
            if log:
                log.info("Retry manifest exists but is empty; using baseline manifest.")
        except Exception as e:
            if log:
                log.error("Failed reading retry manifest (%s); using baseline.", e)
            return base
    else:
        if log:
            log.info("No retry manifest detected; using baseline manifest.")

    return base


# ---- Compatibility API expected by PIPE-1A ----
def manifest_append(path: str | Path, record: Dict[str, Any]) -> None:
    """PIPE-facing append function."""
    append_jsonl_line(path, record)


@dataclass
class ManifestWriter:
    """
    PIPE-facing writer object.
    Wraps append_jsonl_line() and knows its destination path.
    """

    path: Path

    def append(self, record: Dict[str, Any]) -> None:
        append_jsonl_line(self.path, record)

    def close(self) -> None:
        return


def open_manifest(cfg: MutableMapping[str, Any]) -> ManifestWriter:
    """
    PIPE-facing opener. Returns a ManifestWriter over the configured manifest path.

    Looks for (in order):
      - cfg["MANIFEST_PATH"]
      - cfg["MANIFEST"]
      - default "data/manifest.jsonl"
    """
    if not isinstance(cfg, MutableMapping):
        raise TypeError(f"open_manifest(cfg) expected a mapping, got: {type(cfg).__name__}")

    path = cfg.get("MANIFEST_PATH") or cfg.get("MANIFEST") or "data/manifest.jsonl"
    if isinstance(path, dict):
        raise TypeError(
            "open_manifest() got a dict for MANIFEST_PATH/MANIFEST. "
            "Expected a path string like 'data/manifest.jsonl'."
        )

    p = Path(str(path)).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    return ManifestWriter(path=p)
