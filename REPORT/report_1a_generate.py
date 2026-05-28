# REPORT/report_1a_generate.py  
"""  
REPORT-1A — Run Report Generator (HTML + JSON + MD)  
  
Adds:  
- report.json top-level: agent_next_actions (structured extraction only)  
  Derived from:  
    - REASON diagnosis["fixes"] (if present)  
    - HEAL patch presence (if patch present -> review; if missing but diagnosis present -> run HEAL)  
  
No Selenium required.  
"""  
  
from __future__ import annotations  
  
import json  
import os  
from datetime import datetime, timezone  
from pathlib import Path  
from typing import Any, Dict, List, Optional  
  
__all__ = [  
    "generate_report",  
]  
  
  
def _utc_now_iso() -> str:  
    return datetime.now(timezone.utc).isoformat()  
  
  
def _read_text(p: Path) -> str:  
    return p.read_text(encoding="utf-8", errors="replace")  
  
  
def _read_json(p: Path) -> Any:  
    return json.loads(_read_text(p))  
  
  
def _write_text(p: Path, s: str) -> None:  
    p.parent.mkdir(parents=True, exist_ok=True)  
    p.write_text(s, encoding="utf-8")  
  
  
def _write_json(p: Path, obj: Any) -> None:  
    _write_text(p, json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n")  
  
  
def _relpath(target: Path, start_dir: Path) -> str:  
    try:  
        return os.path.relpath(str(target), start=str(start_dir))  
    except Exception:  
        return str(target)  
  
  
def _find_first_by_names(base: Path, names: List[str]) -> Optional[Path]:  
    for n in names:  
        p = base / n  
        if p.exists() and p.is_file():  
            return p  
    return None  
  
  
def _find_first_by_globs(base: Path, patterns: List[str], *, exclude_names: Optional[set[str]] = None) -> Optional[Path]:  
    exclude_names = exclude_names or set()  
    hits: List[Path] = []  
    for pat in patterns:  
        hits.extend([p for p in base.glob(pat) if p.is_file() and p.name not in exclude_names])  
    if not hits:  
        return None  
    hits_sorted = sorted(hits, key=lambda p: (p.name.lower(), str(p).lower()))  
    return hits_sorted[0]  
  
  
def _inputs_record(out_dir: Path, p: Optional[Path]) -> dict:  
    if p is None:  
        return {"present": False, "path": None}  
    return {"present": True, "path": _relpath(p, out_dir)}  
  
  
def _safe_failure_view(failure: Optional[dict]) -> Optional[dict]:  
    # Do not embed potentially sensitive failure.extra content; keep only keys/type.  
    if not isinstance(failure, dict):  
        return None  
    out = dict(failure)  
    if "extra" in out:  
        ex = out.get("extra")  
        if isinstance(ex, dict):  
            out["extra"] = {"_present": True, "keys": sorted(list(ex.keys()))}  
        else:  
            out["extra"] = {"_present": True, "type": type(ex).__name__}  
    return out  
  
  
def _json_pretty(obj: Any, limit: int = 40000) -> str:  
    s = json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False)  
    if len(s) > limit:  
        return s[:limit] + "\n... (truncated)\n"  
    return s  
  
  
def _escape_html(s: str) -> str:  
    return (  
        s.replace("&", "&amp;")  
        .replace("<", "&lt;")  
        .replace(">", "&gt;")  
        .replace('"', "&quot;")  
        .replace("'", "&#39;")  
    )  
  
  
def _extract_agent_next_actions(  
    *,  
    diagnosis: Any,  
    patch_md_path: Optional[Path],  
    patch_json_path: Optional[Path],  
    workflow_name: Optional[str],  
) -> List[dict]:  
    """  
    Structured extraction only (no new reasoning):  
    - If diagnosis.fixes present: emit them as next actions sorted by rank.  
    - If patch present: add "Review patch" action.  
    - If patch missing but diagnosis present: add "Generate patch via HEAL-1A" action.  
    """  
    out: List[dict] = []  
  
    diag = diagnosis if isinstance(diagnosis, dict) else None  
    fixes = (diag.get("fixes") if diag else None)  
    cat = (diag.get("category") if diag else None)  
    conf = (diag.get("confidence") if diag else None)  
  
    if isinstance(fixes, list):  
        normalized = []  
        for f in fixes:  
            if not isinstance(f, dict):  
                continue  
            r = f.get("rank")  
            r_int = r if isinstance(r, int) else 9999  
            normalized.append((r_int, f))  
        for r_int, f in sorted(normalized, key=lambda t: t[0]):  
            out.append(  
                {  
                    "source": "REASON-1A",  
                    "category": cat,  
                    "confidence": conf,  
                    "rank": int(r_int),  
                    "fix": f.get("fix"),  
                    "why": f.get("why"),  
                    "probe": f.get("probe"),  
                    "headless_note": f.get("headless_note"),  
                }  
            )  
  
    patch_present = bool(patch_md_path or patch_json_path)  
    if patch_present:  
        out.insert(  
            0,  
            {  
                "source": "HEAL-1A",  
                "rank": 0,  
                "action": "Review generated workflow patch draft",  
                "workflow_name": workflow_name,  
                "patch_md": str(patch_md_path) if patch_md_path else None,  
                "patch_json": str(patch_json_path) if patch_json_path else None,  
            },  
        )  
    else:  
        # Only if diagnosis exists (derived from patch presence + diagnosis presence).  
        if diag is not None:  
            out.insert(  
                0,  
                {  
                    "source": "HEAL-1A",  
                    "rank": 0,  
                    "action": "Generate a workflow patch draft using HEAL-1A (apply_diagnosis_patch)",  
                    "workflow_name": workflow_name,  
                },  
            )  
  
    return out  
  
  
def generate_report(  
    run_id: str,  
    *,  
    artifacts_dir: str | Path = "artifacts",  
    reports_dir: str | Path = "reports",  
    include_html: bool = True,  
    include_md: bool = True,  
    include_json: bool = True,  
) -> dict:  
    rid = (run_id or "").strip()  
    if not rid:  
        raise ValueError("run_id must be a non-empty string")  
  
    art_base = Path(artifacts_dir) / rid  
    if not art_base.exists() or not art_base.is_dir():  
        raise ValueError(f"Run artifacts folder not found: {art_base.as_posix()}")  
  
    out_base = Path(reports_dir) / rid  
    out_base.mkdir(parents=True, exist_ok=True)  
  
    # SNAP  
    failure_json = (art_base / "failure.json") if (art_base / "failure.json").exists() else None  
    page_json = (art_base / "page.json") if (art_base / "page.json").exists() else None  
    tb_txt = (art_base / "traceback.txt") if (art_base / "traceback.txt").exists() else None  
  
    # OBS timeline (best-effort)  
    timeline_json = _find_first_by_names(  
        art_base,  
        ["timeline.json", "run_timeline.json", "obs_timeline.json", "obs.json", "timeline_obs.json", "obs_1a_timeline.json"],  
    ) or _find_first_by_globs(art_base, ["*timeline*.json", "*obs*.json"], exclude_names={"failure.json", "page.json"})  
  
    # RUN summary (best-effort)  
    run_summary_json = _find_first_by_names(  
        art_base,  
        ["run_summary.json", "summary.json", "run.json", "result.json", "runner_summary.json"],  
    ) or _find_first_by_globs(  
        art_base,  
        ["*run*summary*.json", "*summary*.json", "*result*.json"],  
        exclude_names={"failure.json", "page.json"},  
    )  
  
    # REASON diagnosis (best-effort)  
    diagnosis_json = _find_first_by_names(  
        art_base,  
        ["diagnosis.json", "reason.json", "failure_diagnosis.json"],  
    ) or _find_first_by_globs(art_base, ["*diagnos*.json", "*reason*.json"], exclude_names={"failure.json", "page.json"})  
  
    # Load core content  
    failure_obj = _read_json(failure_json) if failure_json else None  
    page_obj = _read_json(page_json) if page_json else None  
    timeline_obj = _read_json(timeline_json) if timeline_json else None  
    run_obj = _read_json(run_summary_json) if run_summary_json else None  
    diagnosis_obj = _read_json(diagnosis_json) if diagnosis_json else None  
    tb_text = _read_text(tb_txt) if tb_txt else None  
  
    failure_view = _safe_failure_view(failure_obj if isinstance(failure_obj, dict) else None)  
  
    # Summary fields (from failure.json if present)  
    workflow_name = None  
    step_index = None  
    action = None  
    err_type = None  
    err_msg = None  
    if isinstance(failure_obj, dict):  
        workflow_name = failure_obj.get("workflow_name")  
        step_index = failure_obj.get("step_index")  
        action = failure_obj.get("action")  
        err_type = failure_obj.get("error_type")  
        err_msg = failure_obj.get("error_message")  
  
    # HEAL patch outputs:  
    # Prefer inside artifacts, but also look in workflows/ by conventional name if workflow_name known.  
    patch_md = _find_first_by_globs(art_base, ["*__patch.md", "*patch*.md"])  
    patch_json = _find_first_by_globs(art_base, ["*__patch.json", "*patch*.json"], exclude_names={"failure.json", "page.json"})  
  
    if (patch_md is None or patch_json is None) and isinstance(workflow_name, str) and workflow_name.strip():  
        wn = workflow_name.strip()  
        wf_dir = Path("workflows")  
        if patch_md is None:  
            p = wf_dir / f"{wn}__patch.md"  
            if p.exists():  
                patch_md = p  
        if patch_json is None:  
            p = wf_dir / f"{wn}__patch.json"  
            if p.exists():  
                patch_json = p  
  
    patch_md_text = _read_text(patch_md) if patch_md else None  
    patch_obj = _read_json(patch_json) if patch_json else None  
  
    # Artifact list (relative to report dir for file:// friendliness)  
    artifact_files = sorted([p for p in art_base.rglob("*") if p.is_file()], key=lambda p: str(p.relative_to(art_base)).lower())  
    artifact_relpaths = [_relpath(p, out_base) for p in artifact_files]  
  
    inputs_found = {  
        "snap_failure_json": _inputs_record(out_base, failure_json),  
        "snap_page_json": _inputs_record(out_base, page_json),  
        "snap_traceback_txt": _inputs_record(out_base, tb_txt),  
        "obs_timeline_json": _inputs_record(out_base, timeline_json),  
        "run_summary_json": _inputs_record(out_base, run_summary_json),  
        "reason_diagnosis_json": _inputs_record(out_base, diagnosis_json),  
        "heal_patch_md": _inputs_record(out_base, patch_md),  
        "heal_patch_json": _inputs_record(out_base, patch_json),  
    }  
  
    agent_next_actions = _extract_agent_next_actions(  
        diagnosis=diagnosis_obj,  
        patch_md_path=patch_md,  
        patch_json_path=patch_json,  
        workflow_name=str(workflow_name) if workflow_name is not None else None,  
    )  
  
    consolidated = {  
        "run_id": rid,  
        "generated_at": _utc_now_iso(),  
        "inputs_found": inputs_found,  
        "summary": {  
            "workflow_name": workflow_name,  
            "step_index": step_index,  
            "action": action,  
            "error_type": err_type,  
            "error_message": err_msg,  
            "page": page_obj if isinstance(page_obj, dict) else None,  
            "replay_hint": {  
                "python": (  
                    "from REPLAY.replay_1a_run_replay import replay_run\n"  
                    f"replay_run('{rid}', artifacts_dir='{Path(artifacts_dir).as_posix()}', dry_run=True)"  
                )  
            },  
        },  
        "timeline": timeline_obj if isinstance(timeline_obj, dict) else None,  
        "failure": failure_view,  
        "diagnosis": diagnosis_obj if isinstance(diagnosis_obj, dict) else None,  
        "patch": (  
            {  
                "patch_json": patch_obj if isinstance(patch_obj, dict) else None,  
                "patch_md_present": bool(patch_md_text),  
                "patch_md_excerpt": (  
                    (patch_md_text[:4000] + "\n... (truncated)\n")  
                    if isinstance(patch_md_text, str) and len(patch_md_text) > 4000  
                    else patch_md_text  
                ),  
            }  
            if (patch_obj is not None or patch_md_text is not None)  
            else None  
        ),  
        "artifacts": {"paths": artifact_relpaths, "count": len(artifact_relpaths)},  
        "agent_next_actions": agent_next_actions,  
    }  
  
    report_paths: Dict[str, Optional[str]] = {"json": None, "md": None, "html": None}  
  
    if include_json:  
        p = out_base / "report.json"  
        _write_json(p, consolidated)  
        report_paths["json"] = str(p)  
  
    if include_md:  
        md_lines: List[str] = []  
        md_lines.append(f"# Run Report — {rid}\n")  
        md_lines.append(f"- Generated at (UTC): `{consolidated['generated_at']}`\n")  
        md_lines.append("## Summary")  
        md_lines.append(f"- Workflow: `{workflow_name}`")  
        md_lines.append(f"- Step index: `{step_index}`")  
        md_lines.append(f"- Action: `{action}`")  
        md_lines.append(f"- Error: `{err_type}` — {err_msg!r}")  
        if isinstance(page_obj, dict):  
            md_lines.append(f"- Page URL: `{page_obj.get('url')}`")  
            md_lines.append(f"- Page title: `{page_obj.get('title')}`")  
        md_lines.append("")  
        md_lines.append("## Agent next actions")  
        if agent_next_actions:  
            for a in agent_next_actions:  
                if a.get("source") == "REASON-1A":  
                    md_lines.append(f"- (REASON) rank={a.get('rank')}: {a.get('fix')}")  
                else:  
                    md_lines.append(f"- (HEAL) {a.get('action')}")  
        else:  
            md_lines.append("- (none)")  
        md_lines.append("")  
        md_lines.append("## Inputs found")  
        for k, v in inputs_found.items():  
            md_lines.append(f"- {k}: {'yes' if v['present'] else 'no'}" + (f" (`{v['path']}`)" if v["present"] else ""))  
        md_lines.append("")  
        md_lines.append("## Timeline\n```json")  
        md_lines.append(_json_pretty(consolidated["timeline"]) if consolidated["timeline"] else "null")  
        md_lines.append("```\n")  
        md_lines.append("## Failure\n```json")  
        md_lines.append(_json_pretty(consolidated["failure"]) if consolidated["failure"] else "null")  
        md_lines.append("```")  
        if isinstance(tb_text, str) and tb_text.strip():  
            md_lines.append("\n### Traceback\n```")  
            md_lines.append(tb_text[:20000] + ("\n... (truncated)\n" if len(tb_text) > 20000 else ""))  
            md_lines.append("```")  
        md_lines.append("\n## Diagnosis\n```json")  
        md_lines.append(_json_pretty(consolidated["diagnosis"]) if consolidated["diagnosis"] else "null")  
        md_lines.append("```\n")  
        md_lines.append("## Patch\n```json")  
        md_lines.append(_json_pretty(consolidated["patch"]) if consolidated["patch"] else "null")  
        md_lines.append("```\n")  
        md_lines.append("## Artifacts")  
        for rp in artifact_relpaths:  
            md_lines.append(f"- `{rp}`")  
        md_lines.append("\n## Replay\n```python")  
        md_lines.append(consolidated["summary"]["replay_hint"]["python"])  
        md_lines.append("```")  
  
        p = out_base / "report.md"  
        _write_text(p, "\n".join(md_lines) + "\n")  
        report_paths["md"] = str(p)  
  
    if include_html:  
        css = """  
        body { font-family: Arial, sans-serif; margin: 24px; color: #111; }  
        h1 { margin-top: 0; }  
        .meta { color: #444; margin-bottom: 16px; }  
        .section { margin-top: 24px; }  
        pre { background: #f6f8fa; padding: 12px; overflow-x: auto; border: 1px solid #e5e7eb; }  
        code { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }  
        .ok { color: #0a7; font-weight: bold; }  
        .no { color: #a00; font-weight: bold; }  
        ul { padding-left: 18px; }  
        a { color: #0645ad; }  
        """  
        def yn(b: bool) -> str:  
            return '<span class="ok">yes</span>' if b else '<span class="no">no</span>'  
  
        inputs_ul = "\n".join(  
            [  
                f"<li><code>{_escape_html(k)}</code>: {yn(bool(v['present']))}"  
                + (f' — <code>{_escape_html(str(v["path"]))}</code>' if v["present"] and v["path"] else "")  
                + "</li>"  
                for k, v in inputs_found.items()  
            ]  
        )  
  
        actions_ul = "\n".join(  
            [  
                (  
                    f"<li><code>{_escape_html(str(a.get('source')))}</code>: "  
                    f"{_escape_html(str(a.get('fix') or a.get('action') or ''))}</li>"  
                )  
                for a in agent_next_actions  
            ]  
        ) or "<li>(none)</li>"  
  
        artifacts_ul = "\n".join(  
            [f'<li><a href="{_escape_html(rp)}"><code>{_escape_html(rp)}</code></a></li>' for rp in artifact_relpaths]  
        )  
  
        html = f"""<!doctype html>  
<html>  
<head>  
  <meta charset="utf-8" />  
  <title>Run Report — {_escape_html(rid)}</title>  
  <style>{css}</style>  
</head>  
<body>  
  <h1>Run Report — {_escape_html(rid)}</h1>  
  <div class="meta">Generated at (UTC): <code>{_escape_html(consolidated["generated_at"])}</code></div>  
  
  <div class="section">  
    <h2>Summary</h2>  
    <ul>  
      <li>Workflow: <code>{_escape_html(str(workflow_name))}</code></li>  
      <li>Step index: <code>{_escape_html(str(step_index))}</code></li>  
      <li>Action: <code>{_escape_html(str(action))}</code></li>  
      <li>Error: <code>{_escape_html(str(err_type))}</code> — <code>{_escape_html(str(err_msg))}</code></li>  
    </ul>  
    <h3>Replay</h3>  
    <pre><code>{_escape_html(consolidated["summary"]["replay_hint"]["python"])}</code></pre>  
  </div>  
  
  <div class="section">  
    <h2>Agent next actions</h2>  
    <ul>{actions_ul}</ul>  
  </div>  
  
  <div class="section">  
    <h2>Inputs found</h2>  
    <ul>{inputs_ul}</ul>  
  </div>  
  
  <div class="section">  
    <h2>Timeline</h2>  
    <pre><code>{_escape_html(_json_pretty(consolidated["timeline"]) if consolidated["timeline"] else "null")}</code></pre>  
  </div>  
  
  <div class="section">  
    <h2>Failure</h2>  
    <pre><code>{_escape_html(_json_pretty(consolidated["failure"]) if consolidated["failure"] else "null")}</code></pre>  
  </div>  
  
  <div class="section">  
    <h2>Traceback</h2>  
    <pre><code>{_escape_html((tb_text[:20000] + ("\\n... (truncated)\\n" if tb_text and len(tb_text) > 20000 else "")) if tb_text else "null")}</code></pre>  
  </div>  
  
  <div class="section">  
    <h2>Diagnosis</h2>  
    <pre><code>{_escape_html(_json_pretty(consolidated["diagnosis"]) if consolidated["diagnosis"] else "null")}</code></pre>  
  </div>  
  
  <div class="section">  
    <h2>Patch</h2>  
    <pre><code>{_escape_html(_json_pretty(consolidated["patch"]) if consolidated["patch"] else "null")}</code></pre>  
  </div>  
  
  <div class="section">  
    <h2>Artifacts</h2>  
    <ul>{artifacts_ul}</ul>  
  </div>  
</body>  
</html>  
"""  
        p = out_base / "report.html"  
        _write_text(p, html)  
        report_paths["html"] = str(p)  
  
    return {  
        "run_id": rid,  
        "reports_dir": str(out_base),  
        "paths": report_paths,  
        "inputs_present_count": sum(1 for v in inputs_found.values() if v.get("present")),  
        "artifacts_count": len(artifact_relpaths),  
    }  