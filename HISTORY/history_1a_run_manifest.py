"""  
HISTORY-1A — Run manifest (10.2.1)  
  
Single responsibility:  
- Build and write a stable run manifest JSON under a provided run output directory.  
  
Notes:  
- Deterministic JSON formatting (sorted keys, stable indentation).  
- Relative paths normalized to POSIX-style for cross-platform stability.  
- This module does not record step outcomes (10.2.2) and does not normalize errors (10.2.3).  
"""  
  
from __future__ import annotations  
  
import datetime as _dt  
import hashlib  
import json  
import os  
import re  
import sys  
from pathlib import Path  
from typing import Any, Mapping  
  
__all__ = [  
    "build_run_manifest",  
    "write_run_manifest",  
    "dev_smoke",  
]  
  
  
_SAFE_SEGMENT_RE = re.compile(r"[^A-Za-z0-9._-]+")  
  
  
def _utc_now_iso() -> str:  
    return _dt.datetime.now(tz=_dt.timezone.utc).isoformat()  
  
  
def _sanitize_segment(value: Any, *, default: str, max_len: int = 80) -> str:  
    s = "" if value is None else str(value)  
    s = s.strip()  
    if not s:  
        s = default  
    s = _SAFE_SEGMENT_RE.sub("_", s)  
    s = s.strip("._-") or default  
    if len(s) > max_len:  
        s = s[:max_len]  
    return s  
  
  
def _stable_json_bytes(obj: Any) -> bytes:  
    return json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=True).encode("utf-8")  
  
  
def _sha256_file(path: Path) -> str | None:  
    try:  
        h = hashlib.sha256()  
        with path.open("rb") as f:  
            for chunk in iter(lambda: f.read(1024 * 1024), b""):  
                h.update(chunk)  
        return h.hexdigest()  
    except Exception:  
        return None  
  
  
def _norm_path_posix(path: str | os.PathLike[str] | None) -> str | None:  
    if path is None:  
        return None  
    try:  
        return Path(path).as_posix()  
    except Exception:  
        return str(path)  
  
  
def build_run_manifest(  
    *,  
    run_output_dir: str | os.PathLike[str],  
    workflow_name: str,  
    inputs: Mapping[str, Any] | None = None,  
    started_at_utc: str | None = None,  
    finished_at_utc: str | None = None,  
    run_id: str | None = None,  
    workflow_path: str | os.PathLike[str] | None = None,  
    bundle_path: str | os.PathLike[str] | None = None,  
    bundle_version: str | None = None,  
    workflow_version: str | None = None,  
    extra: Mapping[str, Any] | None = None,  
) -> dict[str, Any]:  
    """  
    Build a JSON-serializable run manifest.  
  
    `run_id` is deterministic if `started_at_utc` and `workflow_name` are provided.  
    """  
    if started_at_utc is None:  
        started_at_utc = _utc_now_iso()  
  
    if run_id is None:  
        run_id = f"{_sanitize_segment(workflow_name, default='workflow')}__{_sanitize_segment(started_at_utc, default='time', max_len=40)}"  
  
    wf_path = Path(workflow_path) if workflow_path is not None else None  
    b_path = Path(bundle_path) if bundle_path is not None else None  
  
    wf_sha = _sha256_file(wf_path) if wf_path and wf_path.exists() else None  
    b_sha = _sha256_file(b_path) if b_path and b_path.exists() else None  
  
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"  
  
    manifest: dict[str, Any] = {  
        "schema": "HISTORY-1A",  
        "run_id": run_id,  
        "timestamps": {  
            "started_at_utc": started_at_utc,  
            "finished_at_utc": finished_at_utc,  
        },  
        "workflow": {  
            "name": workflow_name,  
            "version": workflow_version,  
            "path": _norm_path_posix(workflow_path),  
            "sha256": wf_sha,  
        },  
        "bundle": {  
            "version": bundle_version,  
            "path": _norm_path_posix(bundle_path),  
            "sha256": b_sha,  
        },  
        "inputs": dict(inputs or {}),  
        "environment": {  
            "python_version": py_ver,  
            "platform": sys.platform,  
        },  
        "output": {  
            "run_output_dir": _norm_path_posix(run_output_dir),  
            "history_dir": _norm_path_posix(Path(run_output_dir) / "history"),  
        },  
    }  
  
    if extra:  
        manifest["extra"] = {str(k): v for k, v in extra.items()}  
  
    return manifest  
  
  
def write_run_manifest(  
    *,  
    run_output_dir: str | os.PathLike[str],  
    manifest: Mapping[str, Any],  
    overwrite: bool = True,  
) -> dict[str, Any]:  
    """  
    Persist manifest to: {run_output_dir}/history/run_manifest.json  
  
    Returns a small write-result payload.  
    """  
    root = Path(run_output_dir)  
    out_path = root / "history" / "run_manifest.json"  
    out_path.parent.mkdir(parents=True, exist_ok=True)  
  
    if out_path.exists() and not overwrite:  
        raise FileExistsError(str(out_path))  
  
    out_path.write_bytes(_stable_json_bytes(dict(manifest)))  
  
    return {  
        "schema": "HISTORY-1A-WRITE",  
        "path": str(out_path),  
        "path_relative": out_path.resolve().relative_to(root.resolve()).as_posix(),  
        "bytes": out_path.stat().st_size,  
    }  
  
  
def dev_smoke() -> None:  
    repo_root = Path(__file__).resolve().parents[1]  
    out_root = repo_root / "dev" / "_smoke_artifacts" / "10_2_1"  
  
    # deterministic cleanup  
    if out_root.exists():  
        for p in sorted(out_root.rglob("*"), key=lambda x: str(x), reverse=True):  
            if p.is_file():  
                p.unlink()  
            elif p.is_dir():  
                try:  
                    p.rmdir()  
                except OSError:  
                    pass  
        try:  
            out_root.rmdir()  
        except OSError:  
            pass  
  
    out_root.mkdir(parents=True, exist_ok=True)  
  
    # Create a deterministic workflow file so SHA is stable  
    wf_path = out_root / "wf.yml"  
    wf_path.write_text("name: smoke\nsteps: []\n", encoding="utf-8", newline="\n")  
  
    manifest = build_run_manifest(  
        run_output_dir=out_root,  
        workflow_name="smoke_workflow",  
        workflow_path=wf_path,  
        inputs={"env": "DEV", "account": "A1"},  
        started_at_utc="2026-01-01T00:00:00+00:00",  
        finished_at_utc="2026-01-01T00:00:01+00:00",  
        bundle_version="bundle-0",  
        workflow_version="wf-0",  
        extra={"note": "deterministic"},  
    )  
  
    write_info = write_run_manifest(run_output_dir=out_root, manifest=manifest, overwrite=True)  
  
    assert manifest["schema"] == "HISTORY-1A"  
    assert manifest["run_id"] == "smoke_workflow__2026-01-01T00_00_00_00_00"  
    assert manifest["timestamps"]["started_at_utc"] == "2026-01-01T00:00:00+00:00"  
    assert manifest["workflow"]["sha256"] is not None  
    assert write_info["schema"] == "HISTORY-1A-WRITE"  
    assert write_info["path_relative"] == "history/run_manifest.json"  
  
    saved = (out_root / "history" / "run_manifest.json").read_text(encoding="utf-8")  
    assert '"schema": "HISTORY-1A"' in saved  
    assert '"workflow"' in saved  
    assert '"inputs"' in saved  
  
  
if __name__ == "__main__":  
    dev_smoke()  
    print("DEV_SMOKE_OK: HISTORY.history_1a_run_manifest")  