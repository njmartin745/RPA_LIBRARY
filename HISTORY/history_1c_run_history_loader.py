"""  
HISTORY-1C — Run history loader (9.4.3)  
  
Single responsibility:  
- Load HISTORY artifacts for a run_output_dir:  
  - Run manifest (HISTORY-1A*)  
  - Step outcomes (HISTORY-1B*) from JSONL or JSON  
  
This module is intentionally file-layout tolerant:  
- It scans {run_output_dir}/history first (if present), otherwise scans run_output_dir.  
- It identifies artifacts by 'schema' prefixes (HISTORY-1A / HISTORY-1B).  
  
Deterministic behavior:  
- Candidate paths are processed in sorted order.  
- Step outcomes are returned sorted by (step_index, original_order).  
"""  
  
from __future__ import annotations  
  
import json  
from pathlib import Path  
from typing import Any, Iterable, Mapping  
  
__all__ = [  
    "load_run_history",  
    "dev_smoke",  
]  
  
  
def _iter_candidates(search_root: Path) -> list[Path]:  
    if not search_root.exists():  
        return []  
    paths: list[Path] = []  
    for p in search_root.rglob("*"):  
        if not p.is_file():  
            continue  
        suf = p.suffix.lower()  
        if suf in (".json", ".jsonl"):  
            paths.append(p)  
    return sorted(paths, key=lambda x: x.as_posix())  
  
  
def _load_json_file(path: Path) -> Any:  
    txt = path.read_text(encoding="utf-8")  
    return json.loads(txt)  
  
  
def _iter_jsonl_records(path: Path) -> Iterable[Any]:  
    txt = path.read_text(encoding="utf-8")  
    # splitlines() handles \r\n and \n deterministically  
    for line in txt.splitlines():  
        line = line.strip()  
        if not line:  
            continue  
        yield json.loads(line)  
  
  
def _schema_starts(obj: Any, prefix: str) -> bool:  
    if not isinstance(obj, Mapping):  
        return False  
    s = obj.get("schema")  
    return isinstance(s, str) and s.startswith(prefix)  
  
  
def _pick_manifest(candidates: list[Path]) -> tuple[Path, Mapping[str, Any]]:  
    for p in candidates:  
        if p.suffix.lower() != ".json":  
            continue  
        try:  
            obj = _load_json_file(p)  
        except Exception:  
            continue  
        if _schema_starts(obj, "HISTORY-1A"):  
            return p, obj  # type: ignore[return-value]  
    raise FileNotFoundError("HISTORY-1C: no HISTORY-1A manifest JSON found")  
  
  
def _collect_step_outcomes(candidates: list[Path]) -> tuple[list[Path], list[Mapping[str, Any]]]:  
    used_paths: list[Path] = []  
    outcomes: list[Mapping[str, Any]] = []  
  
    for p in candidates:  
        suf = p.suffix.lower()  
        if suf == ".jsonl":  
            try:  
                recs = list(_iter_jsonl_records(p))  
            except Exception:  
                continue  
            picked = [r for r in recs if _schema_starts(r, "HISTORY-1B")]  
            if picked:  
                used_paths.append(p)  
                outcomes.extend([r for r in picked if isinstance(r, Mapping)])  
            continue  
  
        if suf == ".json":  
            try:  
                obj = _load_json_file(p)  
            except Exception:  
                continue  
            if isinstance(obj, list):  
                picked = [r for r in obj if _schema_starts(r, "HISTORY-1B")]  
                if picked:  
                    used_paths.append(p)  
                    outcomes.extend([r for r in picked if isinstance(r, Mapping)])  
            # If it's a dict, ignore: could be manifest or other JSON.  
  
    if not outcomes:  
        raise FileNotFoundError("HISTORY-1C: no HISTORY-1B step outcomes found")  
  
    # Deterministic sorting: (step_index, original_order)  
    indexed: list[tuple[int, int, Mapping[str, Any]]] = []  
    for i, rec in enumerate(outcomes):  
        si = rec.get("step_index")  
        if isinstance(si, int):  
            indexed.append((si, i, rec))  
        else:  
            indexed.append((10**9, i, rec))  
  
    indexed_sorted = sorted(indexed, key=lambda t: (t[0], t[1]))  
    sorted_outcomes = [t[2] for t in indexed_sorted]  
    return used_paths, sorted_outcomes  
  
  
def load_run_history(*, run_output_dir: str | Path) -> dict[str, Any]:  
    """  
    Load run history artifacts from a run_output_dir.  
  
    Returns:  
      {  
        "schema": "HISTORY-1C",  
        "paths": {"manifest": "...", "step_outcomes": ["...", ...]},  
        "manifest": {...},  
        "step_outcomes": [{...}, ...]  
      }  
    """  
    root = Path(run_output_dir)  
  
    history_dir = root / "history"  
    search_root = history_dir if history_dir.exists() else root  
  
    candidates = _iter_candidates(search_root)  
    manifest_path, manifest = _pick_manifest(candidates)  
    outcome_paths, step_outcomes = _collect_step_outcomes(candidates)  
  
    def rel(p: Path) -> str:  
        return p.resolve().relative_to(root.resolve()).as_posix()  
  
    return {  
        "schema": "HISTORY-1C",  
        "run_output_dir": root.as_posix(),  
        "search_root": search_root.as_posix(),  
        "paths": {  
            "manifest": rel(manifest_path),  
            "step_outcomes": [rel(p) for p in outcome_paths],  
        },  
        "manifest": dict(manifest),  
        "step_outcomes": [dict(x) for x in step_outcomes],  
    }  
  
  
def dev_smoke() -> None:  
    repo_root = Path(__file__).resolve().parents[1]  
    out_root = repo_root / "dev" / "_smoke_artifacts" / "9_4_3"  
  
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
  
    # Create history artifacts using existing modules  
    from HISTORY.history_1a_run_manifest import build_run_manifest, write_run_manifest  
    from HISTORY.history_1b_step_outcomes import build_step_outcome, append_step_outcome  
  
    wf_path = out_root / "wf.yml"  
    wf_path.write_text("name: smoke\nsteps: []\n", encoding="utf-8", newline="\n")  
  
    manifest = build_run_manifest(  
        run_output_dir=out_root,  
        workflow_name="smoke_workflow",  
        workflow_path=wf_path,  
        inputs={"env": "DEV"},  
        started_at_utc="2026-01-01T00:00:00+00:00",  
        finished_at_utc="2026-01-01T00:00:02+00:00",  
        bundle_version="bundle-0",  
        workflow_version="wf-0",  
    )  
    write_run_manifest(run_output_dir=out_root, manifest=manifest, overwrite=True)  
  
    append_step_outcome(  
        run_output_dir=out_root,  
        outcome=build_step_outcome(  
            workflow_name="smoke_workflow",  
            step_index=0,  
            step={"action": "open", "url": "https://example.com"},  
            status="ok",  
            started_at_utc="2026-01-01T00:00:00+00:00",  
            finished_at_utc="2026-01-01T00:00:01+00:00",  
        ),  
    )  
    append_step_outcome(  
        run_output_dir=out_root,  
        outcome=build_step_outcome(  
            workflow_name="smoke_workflow",  
            step_index=1,  
            step={"action": "click_selector", "selector_ref": "app.button.save"},  
            status="error",  
            started_at_utc="2026-01-01T00:00:01+00:00",  
            finished_at_utc="2026-01-01T00:00:02+00:00",  
            error=RuntimeError("boom"),  
        ),  
    )  
  
    loaded = load_run_history(run_output_dir=out_root)  
    assert loaded["schema"] == "HISTORY-1C"  
    assert isinstance(loaded["manifest"], dict)  
    assert isinstance(loaded["step_outcomes"], list)  
    assert len(loaded["step_outcomes"]) == 2  
    assert loaded["step_outcomes"][0].get("step_index") == 0  
    assert loaded["step_outcomes"][1].get("step_index") == 1  
  
    # Schema detection sanity  
    assert str(loaded["manifest"].get("schema", "")).startswith("HISTORY-1A")  
    assert str(loaded["step_outcomes"][0].get("schema", "")).startswith("HISTORY-1B")  
  
  
if __name__ == "__main__":  
    dev_smoke()  
    print("DEV_SMOKE_OK: HISTORY.history_1c_run_history_loader")  