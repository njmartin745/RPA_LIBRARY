"""  
run_12b_rollback_rerun_determinism.py  
  
Milestone 12.6.2 — Production readiness smoke: rollback and re-run determinism (CI-safe)  
  
Deterministically simulates:  
  deploy(A) -> run(A1) -> deploy(B) -> run(B1) -> rollback(to A) -> run(A2)  
  
And produces a single report artifact proving:  
- A1 and A2 have identical deterministic "result signatures" given identical deployment inputs.  
- B1 differs from A1 when deployment inputs differ.  
  
Important note:  
Run records contain run identity (run_id) and evidence bundle ids; therefore  
A1 and A2 full canonical JSON will differ. Determinism is validated via a  
separate run_result_signature_sha256 that excludes run identity.  
"""  
  
from __future__ import annotations  
  
from hashlib import sha256  
from typing import Any, Dict, List, Mapping, Optional, Tuple  
  
from REPORT.report_12g_evidence_bundle_assembler import (  
    assemble_evidence_bundle,  
    canonical_json_dumps,  
)  
from RUN.run_12a_prod_smoke_pipeline import (  
    build_minimal_smoke_workflow_bundle,  
    validate_workflow_allowed_actions,  
)  
  
__all__ = [  
    "ROLLBACK_RERUN_SCHEMA_ID",  
    "build_versioned_workflow_bundle",  
    "assemble_deployment_record",  
    "assemble_run_record",  
    "assemble_rollback_record",  
    "assemble_rollback_rerun_determinism_report",  
    "render_rollback_rerun_determinism_report_markdown",  
    "validate_rollback_rerun_determinism_report_basic",  
]  
  
  
ROLLBACK_RERUN_SCHEMA_ID = "run_12b_rollback_rerun_determinism/v1"  
  
  
def _sha256_hex_text(text: str) -> str:  
    h = sha256()  
    h.update(text.encode("utf-8"))  
    return h.hexdigest()  
  
  
def _fingerprint_obj_sha256(obj: Mapping[str, Any]) -> str:  
    return _sha256_hex_text(canonical_json_dumps(obj))  
  
  
def build_versioned_workflow_bundle(*, version: str) -> Dict[str, Any]:  
    """  
    Build a minimal workflow bundle for a given version using only allowed actions.  
  
    Version A and B differ deterministically (URL + log message), ensuring fingerprints differ.  
    """  
    if version not in ("A", "B"):  
        raise ValueError("version must be 'A' or 'B'")  
  
    base_url = "https://example.invalid/a" if version == "A" else "https://example.invalid/b"  
    wb = build_minimal_smoke_workflow_bundle(  
        workflow_id=f"wf_prod_smoke_12_6_2_{version}",  
        start_url=base_url,  
    )  
  
    # Deterministic version marker (still allowed action: log)  
    steps = list(wb["workflow"]["steps"])  
    steps.insert(3, {"action": "log", "message": f"deploy_version={version}"})  
    wb["workflow"] = dict(wb["workflow"])  
    wb["workflow"]["steps"] = steps  
  
    return wb  
  
  
def assemble_deployment_record(  
    *,  
    deployment_id: str,  
    version: str,  
    workflow_bundle: Mapping[str, Any],  
) -> Dict[str, Any]:  
    """  
    Deterministic deployment record (inputs only; no timestamps).  
    """  
    if not deployment_id.strip():  
        raise ValueError("deployment_id must be non-empty")  
    if version not in ("A", "B"):  
        raise ValueError("version must be 'A' or 'B'")  
  
    workflow = workflow_bundle.get("workflow")  
    selectors = workflow_bundle.get("selectors")  
    if not isinstance(workflow, Mapping) or not isinstance(selectors, Mapping):  
        raise ValueError("workflow_bundle must contain mapping keys: workflow, selectors")  
  
    ok_actions, problems = validate_workflow_allowed_actions(workflow)  
  
    deployment_wo_fp: Dict[str, Any] = {  
        "deployment_id": deployment_id,  
        "version": version,  
        "workflow_id": workflow.get("workflow_id"),  
        "selectors_refs_sorted": sorted(selectors.keys()),  
        "allowed_actions_ok": ok_actions,  
        "allowed_actions_problems": problems,  
        "workflow_canon_sha256": _fingerprint_obj_sha256(dict(workflow)),  
        "selectors_canon_sha256": _fingerprint_obj_sha256(dict(selectors)),  
    }  
    deployment = dict(deployment_wo_fp)  
    deployment["deployment_fingerprint_sha256"] = _fingerprint_obj_sha256(deployment_wo_fp)  
    return deployment  
  
  
def assemble_run_record(  
    *,  
    scenario_id: str,  
    run_id: str,  
    created_date: Optional[str],  
    deployment: Mapping[str, Any],  
    workflow_bundle: Mapping[str, Any],  
) -> Dict[str, Any]:  
    """  
    Deterministic run record derived entirely from inputs (no execution).  
  
    Includes two hashes:  
    - run_fingerprint_sha256: fingerprint of the full run record content excluding that fingerprint  
      (includes run_id and evidence bundle id, so A1 != A2 here).  
    - run_result_signature_sha256: fingerprint of the deterministic result signature excluding run identity  
      (so A1 == A2 here when inputs are identical).  
    """  
    workflow = workflow_bundle["workflow"]  
    selectors = workflow_bundle["selectors"]  
  
    # CI-safe "run outcome": deterministic placeholder (NO run_id so reruns can match)  
    run_outcome = {  
        "status": "SIMULATED_OK",  
        "deployment_id": deployment.get("deployment_id"),  
        "deployment_version": deployment.get("version"),  
    }  
  
    artifacts_text = {  
        "deployment.json": canonical_json_dumps(dict(deployment)),  
        "workflow.json": canonical_json_dumps(dict(workflow)),  
        "selectors.json": canonical_json_dumps(dict(selectors)),  
        "run_outcome.json": canonical_json_dumps(run_outcome),  
    }  
  
    evidence_bundle = assemble_evidence_bundle(  
        bundle_id=f"evidence::{scenario_id}::{run_id}",  # identity varies per run attempt  
        scope="rollback_rerun_smoke",  
        created_date=created_date,  
        notes="run_record",  
        release_readiness={  
            "ok": bool(deployment.get("allowed_actions_ok")),  
            "problems": list(deployment.get("allowed_actions_problems") or []),  
        },  
        incident_packet_manifest={"kind": "smoke", "scenario_id": scenario_id, "run_id": run_id},  
        artifacts_text=artifacts_text,  
    )  
  
    # Result signature excludes run identity (run_id, evidence bundle ids), focusing on stable determinants.  
    run_result_signature_obj: Dict[str, Any] = {  
        "deployment_fingerprint_sha256": deployment.get("deployment_fingerprint_sha256"),  
        "workflow_canon_sha256": deployment.get("workflow_canon_sha256"),  
        "selectors_canon_sha256": deployment.get("selectors_canon_sha256"),  
        "run_outcome": run_outcome,  
    }  
    run_result_signature_sha256 = _fingerprint_obj_sha256(run_result_signature_obj)  
  
    run_wo_fp: Dict[str, Any] = {  
        "run_id": run_id,  
        "deployment_id": deployment.get("deployment_id"),  
        "deployment_version": deployment.get("version"),  
        "created_date": created_date,  
        "run_outcome": run_outcome,  
        "evidence_bundle": evidence_bundle,  
        "run_result_signature_sha256": run_result_signature_sha256,  
    }  
    run = dict(run_wo_fp)  
    run["run_fingerprint_sha256"] = _fingerprint_obj_sha256(run_wo_fp)  
    return run  
  
  
def assemble_rollback_record(  
    *,  
    scenario_id: str,  
    created_date: Optional[str],  
    from_deployment: Mapping[str, Any],  
    to_deployment: Mapping[str, Any],  
    reason: str,  
) -> Dict[str, Any]:  
    """  
    Deterministic rollback record tying together two deployments (inputs only).  
    """  
    if not isinstance(reason, str) or not reason.strip():  
        raise ValueError("reason must be a non-empty string")  
  
    record_wo_fp: Dict[str, Any] = {  
        "scenario_id": scenario_id,  
        "created_date": created_date,  
        "from": {  
            "deployment_id": from_deployment.get("deployment_id"),  
            "version": from_deployment.get("version"),  
            "deployment_fingerprint_sha256": from_deployment.get("deployment_fingerprint_sha256"),  
        },  
        "to": {  
            "deployment_id": to_deployment.get("deployment_id"),  
            "version": to_deployment.get("version"),  
            "deployment_fingerprint_sha256": to_deployment.get("deployment_fingerprint_sha256"),  
        },  
        "reason": reason,  
    }  
    record = dict(record_wo_fp)  
    record["rollback_fingerprint_sha256"] = _fingerprint_obj_sha256(record_wo_fp)  
    return record  
  
  
def assemble_rollback_rerun_determinism_report(  
    *,  
    scenario_id: str,  
    created_date: Optional[str] = None,  
    notes: Optional[str] = None,  
) -> Dict[str, Any]:  
    """  
    Top-level deterministic report artifact for the milestone.  
    """  
    if not isinstance(scenario_id, str) or not scenario_id.strip():  
        raise ValueError("scenario_id must be a non-empty string")  
  
    wb_a = build_versioned_workflow_bundle(version="A")  
    wb_b = build_versioned_workflow_bundle(version="B")  
  
    dep_a = assemble_deployment_record(deployment_id="dep-A", version="A", workflow_bundle=wb_a)  
    dep_b = assemble_deployment_record(deployment_id="dep-B", version="B", workflow_bundle=wb_b)  
  
    run_a1 = assemble_run_record(  
        scenario_id=scenario_id,  
        run_id="A1",  
        created_date=created_date,  
        deployment=dep_a,  
        workflow_bundle=wb_a,  
    )  
    run_b1 = assemble_run_record(  
        scenario_id=scenario_id,  
        run_id="B1",  
        created_date=created_date,  
        deployment=dep_b,  
        workflow_bundle=wb_b,  
    )  
  
    rollback = assemble_rollback_record(  
        scenario_id=scenario_id,  
        created_date=created_date,  
        from_deployment=dep_b,  
        to_deployment=dep_a,  
        reason="smoke_test: rollback to known-good deployment",  
    )  
  
    run_a2 = assemble_run_record(  
        scenario_id=scenario_id,  
        run_id="A2",  
        created_date=created_date,  
        deployment=dep_a,  
        workflow_bundle=wb_a,  
    )  
  
    invariants = {  
        # Determinism should be asserted on result signatures (excludes run identity).  
        "a1_equals_a2_result_signature": (  
            run_a1["run_result_signature_sha256"] == run_a2["run_result_signature_sha256"]  
        ),  
        "b1_differs_from_a1_result_signature": (  
            run_b1["run_result_signature_sha256"] != run_a1["run_result_signature_sha256"]  
        ),  
        "deployments_a_b_differ_fingerprint": (  
            dep_a["deployment_fingerprint_sha256"] != dep_b["deployment_fingerprint_sha256"]  
        ),  
        # Sanity: run record fingerprints differ across attempts due to run_id/evidence identity.  
        "a1_run_record_fingerprint_differs_from_a2": (  
            run_a1["run_fingerprint_sha256"] != run_a2["run_fingerprint_sha256"]  
        ),  
    }  
  
    report_wo_fp: Dict[str, Any] = {  
        "schema": ROLLBACK_RERUN_SCHEMA_ID,  
        "scenario_id": scenario_id,  
        "created_date": created_date,  
        "notes": notes,  
        "deployments": {"A": dep_a, "B": dep_b},  
        "runs": {"A1": run_a1, "B1": run_b1, "A2": run_a2},  
        "rollback": rollback,  
        "invariants": invariants,  
    }  
    report = dict(report_wo_fp)  
    report["report_fingerprint_sha256"] = _fingerprint_obj_sha256(report_wo_fp)  
    return report  
  
  
def render_rollback_rerun_determinism_report_markdown(report: Mapping[str, Any]) -> str:  
    """  
    Deterministic Markdown renderer for the rollback/re-run determinism report.  
    """  
    schema = report.get("schema", "")  
    scenario_id = report.get("scenario_id", "")  
    created_date = report.get("created_date")  
    notes = report.get("notes")  
    fp = report.get("report_fingerprint_sha256", "")  
  
    lines: List[str] = []  
    lines.append(f"# Rollback + Re-run Determinism Report: {scenario_id}".rstrip())  
    lines.append("")  
    lines.append(f"- Schema: `{schema}`")  
    if created_date is not None:  
        lines.append(f"- Created date: `{created_date}`")  
    if notes is not None:  
        lines.append(f"- Notes: {notes}")  
    lines.append(f"- Report fingerprint (sha256): `{fp}`")  
    lines.append("")  
  
    for key in ("invariants", "rollback", "deployments", "runs"):  
        lines.append(f"## {key}")  
        lines.append("")  
        lines.append("```json")  
        lines.append(canonical_json_dumps(report.get(key) or {}))  
        lines.append("```")  
        lines.append("")  
  
    return "\n".join(lines).rstrip() + "\n"  
  
  
def validate_rollback_rerun_determinism_report_basic(report: Mapping[str, Any]) -> Tuple[bool, List[str]]:  
    problems: List[str] = []  
    if report.get("schema") != ROLLBACK_RERUN_SCHEMA_ID:  
        problems.append("schema mismatch or missing")  
    if not isinstance(report.get("scenario_id"), str) or not report.get("scenario_id"):  
        problems.append("scenario_id missing/invalid")  
    fp = report.get("report_fingerprint_sha256")  
    if not isinstance(fp, str) or len(fp) != 64:  
        problems.append("report_fingerprint_sha256 missing/invalid")  
    inv = report.get("invariants")  
    if not isinstance(inv, Mapping):  
        problems.append("invariants missing/invalid")  
    else:  
        for k in (  
            "a1_equals_a2_result_signature",  
            "b1_differs_from_a1_result_signature",  
            "deployments_a_b_differ_fingerprint",  
            "a1_run_record_fingerprint_differs_from_a2",  
        ):  
            if k not in inv:  
                problems.append(f"invariants.{k} missing")  
    return (len(problems) == 0), problems  