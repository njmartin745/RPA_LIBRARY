from __future__ import annotations  
  
import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT))  
  
from RUN.run_12c_operational_gates_enforcement import (  
    assemble_operational_gates_enforcement_report,  
    render_operational_gates_enforcement_report_markdown,  
    validate_operational_gates_enforcement_report_basic,  
)  
from REPORT.report_12g_evidence_bundle_assembler import canonical_json_dumps  
  
  
def _run() -> None:  
    r1 = assemble_operational_gates_enforcement_report(  
        scenario_id="dev_smoke_12_6_3",  
        created_date="2026-04-23",  
        notes="dev_smoke",  
    )  
    r2 = assemble_operational_gates_enforcement_report(  
        scenario_id="dev_smoke_12_6_3",  
        created_date="2026-04-23",  
        notes="dev_smoke",  
    )  
  
    ok1, p1 = validate_operational_gates_enforcement_report_basic(r1)  
    ok2, p2 = validate_operational_gates_enforcement_report_basic(r2)  
    if not ok1:  
        raise AssertionError(f"report1 validation failed: {p1}")  
    if not ok2:  
        raise AssertionError(f"report2 validation failed: {p2}")  
  
    # Determinism: canonical JSON identical  
    j1 = canonical_json_dumps(r1)  
    j2 = canonical_json_dumps(r2)  
    if j1 != j2:  
        raise AssertionError("Determinism failure: report canonical JSON differs")  
  
    # Determinism: fingerprint identical  
    if r1["report_fingerprint_sha256"] != r2["report_fingerprint_sha256"]:  
        raise AssertionError("Determinism failure: report fingerprint differs")  
  
    inv = r1["invariants"]  
    # We require at least one interpretable gate and meaningful divergence  
    if inv["interpretable_gate_count"] < 1:  
        raise AssertionError("Expected at least 1 gate with interpretable boolean ok results")  
    if inv["any_gate_good_pass"] is not True:  
        raise AssertionError("Expected at least one gate to pass on good inputs")  
    if inv["any_gate_bad_fail"] is not True:  
        raise AssertionError("Expected at least one gate to fail on bad inputs")  
    if inv["no_all_gates_same_outcome"] is not True:  
        raise AssertionError("Expected not all interpretable gates to have identical outcomes")  
  
    # Markdown write/read  
    md = render_operational_gates_enforcement_report_markdown(r1)  
    out_path = Path(__file__).resolve().parent / "_artifact_12_6_3_operational_gates_enforcement.md"  
    out_path.write_text(md, encoding="utf-8")  
    md2 = out_path.read_text(encoding="utf-8")  
    if md2 != md:  
        raise AssertionError("Markdown write/read mismatch")  
  
  
if __name__ == "__main__":  
    try:  
        _run()  
        print("PASS: dev_smoke_12_6_3_operational_gates_enforcement")  
    except Exception as e:  
        print(f"FAIL: dev_smoke_12_6_3_operational_gates_enforcement: {e}")  
        raise  