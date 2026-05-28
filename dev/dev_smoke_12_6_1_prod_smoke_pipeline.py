from __future__ import annotations  
  
import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT))   
  
from RUN.run_12a_prod_smoke_pipeline import (  
    assemble_prod_smoke_pipeline_report,  
    build_minimal_smoke_workflow_bundle,  
    render_prod_smoke_pipeline_report_markdown,  
    validate_prod_smoke_pipeline_report_basic,  
)  
from REPORT.report_12g_evidence_bundle_assembler import canonical_json_dumps  
  
  
def _run() -> None:  
    # Build the same workflow bundle twice but with selectors inserted in different order  
    wb1 = build_minimal_smoke_workflow_bundle()  
  
    wb2 = {  
        "workflow": wb1["workflow"],  
        "selectors": {  
            # reverse insertion order to test determinism of summaries/artifact inventory  
            "smoke.body": wb1["selectors"]["smoke.body"],  
            "smoke.root": wb1["selectors"]["smoke.root"],  
        },  
    }  
  
    run_outcome_a = {"status": "SIMULATED_OK", "steps_executed": 0}  
    run_outcome_b = {"steps_executed": 0, "status": "SIMULATED_OK"}  # different insertion order  
  
    r1 = assemble_prod_smoke_pipeline_report(  
        scenario_id="dev_smoke_12_6_1",  
        created_date="2026-04-23",  
        workflow_bundle=wb1,  
        run_outcome=run_outcome_a,  
        notes="dev_smoke",  
    )  
    r2 = assemble_prod_smoke_pipeline_report(  
        scenario_id="dev_smoke_12_6_1",  
        created_date="2026-04-23",  
        workflow_bundle=wb2,  
        run_outcome=run_outcome_b,  
        notes="dev_smoke",  
    )  
  
    ok1, p1 = validate_prod_smoke_pipeline_report_basic(r1)  
    ok2, p2 = validate_prod_smoke_pipeline_report_basic(r2)  
    if not ok1:  
        raise AssertionError(f"report1 validation failed: {p1}")  
    if not ok2:  
        raise AssertionError(f"report2 validation failed: {p2}")  
  
    # Determinism: canonical JSON must match  
    j1 = canonical_json_dumps(r1)  
    j2 = canonical_json_dumps(r2)  
    if j1 != j2:  
        raise AssertionError("Determinism failure: report canonical JSON differs")  
  
    # Determinism: fingerprint must match  
    if r1["report_fingerprint_sha256"] != r2["report_fingerprint_sha256"]:  
        raise AssertionError("Determinism failure: report fingerprint differs")  
  
    # Markdown render + write/read  
    md = render_prod_smoke_pipeline_report_markdown(r1)  
    out_path = Path(__file__).resolve().parent / "_artifact_12_6_1_prod_smoke_pipeline.md"  
    out_path.write_text(md, encoding="utf-8")  
    md2 = out_path.read_text(encoding="utf-8")  
    if md2 != md:  
        raise AssertionError("Markdown write/read mismatch")  
  
  
if __name__ == "__main__":  
    try:  
        _run()  
        print("PASS: dev_smoke_12_6_1_prod_smoke_pipeline")  
    except Exception as e:  
        print(f"FAIL: dev_smoke_12_6_1_prod_smoke_pipeline: {e}")  
        raise  