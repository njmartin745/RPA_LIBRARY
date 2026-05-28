"""  
run_12a_prod_smoke_pipeline.py  
  
Milestone 12.6.1 — Production readiness smoke: deploy-to-run-to-report pipeline (CI-safe)  
  
This module provides a deterministic harness that:  
- Constructs a minimal workflow + selectors bundle using only supported actions.  
- Validates that only allowed actions are used (including nested repeat steps).  
- Assembles an evidence bundle using REPORT/report_12g_evidence_bundle_assembler.py  
- Produces a deterministic "prod smoke pipeline report" artifact with JSON/Markdown renderers  
  and a stable SHA256 fingerprint over canonical JSON.  
  
No Selenium execution, no timestamps generated. Caller may provide created_date if desired.  
"""  
  
from __future__ import annotations  
  
from hashlib import sha256  
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple  
  
from REPORT.report_12g_evidence_bundle_assembler import (  
    assemble_evidence_bundle,  
    canonical_json_dumps,  
)  
  
__all__ = [  
    "PROD_SMOKE_PIPELINE_SCHEMA_ID",  
    "ALLOWED_WORKFLOW_ACTIONS",  
    "build_minimal_smoke_workflow_bundle",  
    "validate_workflow_allowed_actions",  
    "assemble_prod_smoke_pipeline_report",  
    "render_prod_smoke_pipeline_report_markdown",  
    "validate_prod_smoke_pipeline_report_basic",  
    "compute_prod_smoke_pipeline_report_fingerprint_sha256",  
]  
  
  
PROD_SMOKE_PIPELINE_SCHEMA_ID = "run_12a_prod_smoke_pipeline/v1"  
  
# Hard constraint from user/system prompt: do not use any other actions.  
ALLOWED_WORKFLOW_ACTIONS = (  
    "open",  
    "click_selector",  
    "type_selector_secret",  
    "wait_for_selector",  
    "exec_js",  
    "exec_js_file",  
    "repeat",  
    "log",  
    "switch_back_to_main_tab",  
)  
  
  
def _sha256_hex_text(text: str) -> str:  
    h = sha256()  
    h.update(text.encode("utf-8"))  
    return h.hexdigest()  
  
  
def build_minimal_smoke_workflow_bundle(  
    *,  
    workflow_id: str = "wf_prod_smoke_12_6_1",  
    start_url: str = "https://example.invalid/",  
) -> Dict[str, Any]:  
    """  
    Build a minimal, schema-like workflow + selectors bundle.  
  
    Notes:  
    - Uses only allowed actions.  
    - Prefers selector_ref where selectors are involved.  
    - Designed to be deterministic and CI-safe (no external execution implied).  
    """  
    selectors = {  
        # Minimal selector records; actual selector schema may be richer elsewhere,  
        # but using selector_ref keeps workflows aligned with framework conventions.  
        "smoke.root": {"by": "css", "value": "html"},  
        "smoke.body": {"by": "css", "value": "body"},  
    }  
  
    workflow = {  
        "workflow_id": workflow_id,  
        "steps": [  
            {"action": "open", "url": start_url},  
            {"action": "wait_for_selector", "selector_ref": "smoke.root"},  
            {"action": "log", "message": "prod_smoke: page loaded"},  
            {  
                "action": "repeat",  
                "times": 2,  
                "steps": [  
                    {"action": "wait_for_selector", "selector_ref": "smoke.body"},  
                    {"action": "log", "message": "prod_smoke: repeat tick"},  
                ],  
            },  
            {"action": "switch_back_to_main_tab"},  
        ],  
    }  
  
    return {"workflow": workflow, "selectors": selectors}  
  
  
def validate_workflow_allowed_actions(workflow: Mapping[str, Any]) -> Tuple[bool, List[str]]:  
    """  
    Deterministic validator that enforces the allowed action set, including nested repeat steps.  
    Does not attempt full schema validation; it focuses on the hard governance constraint:  
    the workflow must not contain unsupported actions.  
  
    Returns: (ok, problems)  
    """  
    problems: List[str] = []  
  
    def walk_steps(steps: Any, path: str) -> None:  
        if not isinstance(steps, list):  
            problems.append(f"{path}: steps is not a list")  
            return  
        for i, step in enumerate(steps):  
            sp = f"{path}[{i}]"  
            if not isinstance(step, Mapping):  
                problems.append(f"{sp}: step is not a mapping")  
                continue  
            action = step.get("action")  
            if action not in ALLOWED_WORKFLOW_ACTIONS:  
                problems.append(f"{sp}: unsupported action={action!r}")  
                continue  
            if action == "repeat":  
                walk_steps(step.get("steps"), sp + ".steps")  
  
    walk_steps(workflow.get("steps"), "steps")  
    return (len(problems) == 0), problems  
  
  
def compute_prod_smoke_pipeline_report_fingerprint_sha256(report_wo_fp: Mapping[str, Any]) -> str:  
    """  
    Stable SHA256 fingerprint over canonical JSON of the report object (excluding fingerprint field).  
    """  
    return _sha256_hex_text(canonical_json_dumps(report_wo_fp))  
  
  
def assemble_prod_smoke_pipeline_report(  
    *,  
    scenario_id: str,  
    created_date: Optional[str] = None,  
    workflow_bundle: Mapping[str, Any],  
    # Optional “run outcome” placeholder (CI-safe). Caller supplies deterministic dict.  
    run_outcome: Optional[Mapping[str, Any]] = None,  
    # Optional operator notes  
    notes: Optional[str] = None,  
) -> Dict[str, Any]:  
    """  
    Produces a deterministic smoke report and an attached evidence bundle.  
  
    The evidence bundle is assembled using report_12g_evidence_bundle_assembler, but upstream  
    policy modules are not invoked here; callers can pass their evaluated dict outputs  
    into the evidence bundle by extending this harness later.  
    """  
    if not isinstance(scenario_id, str) or not scenario_id.strip():  
        raise ValueError("scenario_id must be a non-empty string")  
  
    workflow = workflow_bundle.get("workflow")  
    selectors = workflow_bundle.get("selectors")  
  
    if not isinstance(workflow, Mapping):  
        raise ValueError("workflow_bundle.workflow must be a mapping")  
    if not isinstance(selectors, Mapping):  
        raise ValueError("workflow_bundle.selectors must be a mapping")  
  
    ok_actions, problems = validate_workflow_allowed_actions(workflow)  
  
    # Keep report deterministic: summarize selectors/workflow without timestamps.  
    workflow_summary = {  
        "workflow_id": workflow.get("workflow_id"),  
        "step_count": len(workflow.get("steps") or []),  
    }  
    selectors_summary = {  
        "selector_count": len(list(selectors.keys())),  
        "selector_refs_sorted": sorted(selectors.keys()),  
    }  
  
    # Bundle artifacts (text) can include canonical JSON snapshots of key inputs.  
    artifacts_text = {  
        "workflow.json": canonical_json_dumps(dict(workflow)),  
        "selectors.json": canonical_json_dumps(dict(selectors)),  
        "run_outcome.json": canonical_json_dumps(dict(run_outcome or {})),  
    }  
  
    evidence_bundle = assemble_evidence_bundle(  
        bundle_id=f"evidence::{scenario_id}",  
        scope="prod_smoke",  
        created_date=created_date,  
        notes="prod_smoke_pipeline",  
        # Attach the smoke “run” inputs as generic sections; upstream modules can add more.  
        alerting={"derived_from": "prod_smoke", "signals": []},  
        replay_verification={"ok": True, "note": "CI-safe: no replay verification performed"},  
        incident_packet_manifest={"kind": "smoke", "scenario_id": scenario_id},  
        release_readiness={"ok": ok_actions, "problems": problems},  
        artifacts_text=artifacts_text,  
    )  
  
    report_wo_fp: Dict[str, Any] = {  
        "schema": PROD_SMOKE_PIPELINE_SCHEMA_ID,  
        "scenario_id": scenario_id,  
        "created_date": created_date,  
        "notes": notes,  
        "workflow_summary": workflow_summary,  
        "selectors_summary": selectors_summary,  
        "checks": {  
            "allowed_actions_ok": ok_actions,  
            "allowed_actions_problems": problems,  
        },  
        "run_outcome": dict(run_outcome or {}),  
        "evidence_bundle": evidence_bundle,  
    }  
  
    fp = compute_prod_smoke_pipeline_report_fingerprint_sha256(report_wo_fp)  
    report = dict(report_wo_fp)  
    report["report_fingerprint_sha256"] = fp  
    return report  
  
  
def render_prod_smoke_pipeline_report_markdown(report: Mapping[str, Any]) -> str:  
    """  
    Deterministic Markdown renderer for the smoke pipeline report.  
    """  
    schema = report.get("schema", "")  
    scenario_id = report.get("scenario_id", "")  
    created_date = report.get("created_date")  
    notes = report.get("notes")  
    fp = report.get("report_fingerprint_sha256", "")  
  
    lines: List[str] = []  
    lines.append(f"# Prod Smoke Pipeline Report: {scenario_id}".rstrip())  
    lines.append("")  
    lines.append(f"- Schema: `{schema}`")  
    if created_date is not None:  
        lines.append(f"- Created date: `{created_date}`")  
    if notes is not None:  
        lines.append(f"- Notes: {notes}")  
    lines.append(f"- Report fingerprint (sha256): `{fp}`")  
    lines.append("")  
  
    ws = report.get("workflow_summary") or {}  
    ss = report.get("selectors_summary") or {}  
    checks = report.get("checks") or {}  
    ev = report.get("evidence_bundle") or {}  
  
    lines.append("## Workflow summary")  
    lines.append("")  
    lines.append("```json")  
    lines.append(canonical_json_dumps(ws))  
    lines.append("```")  
    lines.append("")  
  
    lines.append("## Selectors summary")  
    lines.append("")  
    lines.append("```json")  
    lines.append(canonical_json_dumps(ss))  
    lines.append("```")  
    lines.append("")  
  
    lines.append("## Checks")  
    lines.append("")  
    lines.append("```json")  
    lines.append(canonical_json_dumps(checks))  
    lines.append("```")  
    lines.append("")  
  
    lines.append("## Evidence bundle (embedded)")  
    lines.append("")  
    lines.append("```json")  
    lines.append(canonical_json_dumps(ev))  
    lines.append("```")  
    lines.append("")  
  
    return "\n".join(lines).rstrip() + "\n"  
  
  
def validate_prod_smoke_pipeline_report_basic(report: Mapping[str, Any]) -> Tuple[bool, List[str]]:  
    """  
    Lightweight deterministic validation of the report structure.  
    """  
    problems: List[str] = []  
    if report.get("schema") != PROD_SMOKE_PIPELINE_SCHEMA_ID:  
        problems.append("schema mismatch or missing")  
    if not isinstance(report.get("scenario_id"), str) or not report.get("scenario_id"):  
        problems.append("scenario_id missing/invalid")  
    fp = report.get("report_fingerprint_sha256")  
    if not isinstance(fp, str) or len(fp) != 64:  
        problems.append("report_fingerprint_sha256 missing/invalid")  
    if not isinstance(report.get("evidence_bundle"), Mapping):  
        problems.append("evidence_bundle missing/invalid")  
    checks = report.get("checks")  
    if not isinstance(checks, Mapping) or "allowed_actions_ok" not in checks:  
        problems.append("checks missing/invalid")  
    return (len(problems) == 0), problems  