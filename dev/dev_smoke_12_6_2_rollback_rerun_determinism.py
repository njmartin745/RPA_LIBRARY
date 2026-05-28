from __future__ import annotations  
  
import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT))  
  
from RUN.run_12b_rollback_rerun_determinism import (  
    assemble_rollback_rerun_determinism_report,  
    render_rollback_rerun_determinism_report_markdown,  
    validate_rollback_rerun_determinism_report_basic,  
)  
from REPORT.report_12g_evidence_bundle_assembler import canonical_json_dumps  
  
  
def _run() -> None:  
    r1 = assemble_rollback_rerun_determinism_report(  
        scenario_id="dev_smoke_12_6_2",  
        created_date="2026-04-23",  
        notes="dev_smoke",  
    )  
    r2 = assemble_rollback_rerun_determinism_report(  
        scenario_id="dev_smoke_12_6_2",  
        created_date="2026-04-23",  
        notes="dev_smoke",  
    )  
  
    ok1, p1 = validate_rollback_rerun_determinism_report_basic(r1)  
    ok2, p2 = validate_rollback_rerun_determinism_report_basic(r2)  
    if not ok1:  
        raise AssertionError(f"report1 validation failed: {p1}")  
    if not ok2:  
        raise AssertionError(f"report2 validation failed: {p2}")  
  
    # Determinism: canonical JSON identical across two invocations  
    j1 = canonical_json_dumps(r1)  
    j2 = canonical_json_dumps(r2)  
    if j1 != j2:  
        raise AssertionError("Determinism failure: report canonical JSON differs")  
  
    # Determinism: fingerprint identical  
    if r1["report_fingerprint_sha256"] != r2["report_fingerprint_sha256"]:  
        raise AssertionError("Determinism failure: report fingerprint differs")  
  
    # Rollback invariants must hold  
    inv = r1["invariants"]  
    if inv["a1_equals_a2_result_signature"] is not True:  
        raise AssertionError("Invariant failed: A1 must equal A2 (result signature)")  
    if inv["b1_differs_from_a1_result_signature"] is not True:  
        raise AssertionError("Invariant failed: B1 must differ from A1 (result signature)")  
    if inv["deployments_a_b_differ_fingerprint"] is not True:  
        raise AssertionError("Invariant failed: deployment A and B must differ (fingerprint)")  
    if inv["a1_run_record_fingerprint_differs_from_a2"] is not True:  
        raise AssertionError("Invariant failed: A1 run record fingerprint must differ from A2 (run identity differs)")  
  
    # Markdown write/read  
    md = render_rollback_rerun_determinism_report_markdown(r1)  
    out_path = Path(__file__).resolve().parent / "_artifact_12_6_2_rollback_rerun_determinism.md"  
    out_path.write_text(md, encoding="utf-8")  
    md2 = out_path.read_text(encoding="utf-8")  
    if md2 != md:  
        raise AssertionError("Markdown write/read mismatch")  
  
  
if __name__ == "__main__":  
    try:  
        _run()  
        print("PASS: dev_smoke_12_6_2_rollback_rerun_determinism")  
    except Exception as e:  
        print(f"FAIL: dev_smoke_12_6_2_rollback_rerun_determinism: {e}")  
        raise  