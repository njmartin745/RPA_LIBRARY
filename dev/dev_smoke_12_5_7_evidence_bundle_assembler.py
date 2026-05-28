from __future__ import annotations  
  
import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT))   
  
from REPORT.report_12g_evidence_bundle_assembler import (  
    EVIDENCE_BUNDLE_SCHEMA_ID,  
    assemble_evidence_bundle,  
    canonical_json_dumps,  
    render_evidence_bundle_markdown,  
    sha256_hex_of_text,  
    validate_evidence_bundle_basic,  
)  
  
  
def _run() -> None:  
    # Inputs with intentionally different key insertion orders  
    alerting_a = {"signals": ["RUN_FAILED", "RUN_SLA_BREACH"], "severity": "sev2"}  
    alerting_b = {"severity": "sev2", "signals": ["RUN_FAILED", "RUN_SLA_BREACH"]}  
  
    replay_verification = {"ok": True, "checked_events": 3}  
  
    # artifacts_text maps provided in different orders should yield same inventory ordering/hashes  
    artifacts_text_1 = {  
        "a.json": '{"a":1,"b":2}',  
        "b.json": '{"x":true}',  
    }  
    artifacts_text_2 = {  
        "b.json": '{"x":true}',  
        "a.json": '{"a":1,"b":2}',  
    }  
  
    bundle1 = assemble_evidence_bundle(  
        bundle_id="bundle-dev-smoke-12_5_7",  
        scope="prod",  
        created_date="2026-04-23",  
        notes="dev_smoke",  
        alerting=alerting_a,  
        replay_verification=replay_verification,  
        artifacts_text=artifacts_text_1,  
    )  
  
    bundle2 = assemble_evidence_bundle(  
        bundle_id="bundle-dev-smoke-12_5_7",  
        scope="prod",  
        created_date="2026-04-23",  
        notes="dev_smoke",  
        alerting=alerting_b,  
        replay_verification=replay_verification,  
        artifacts_text=artifacts_text_2,  
    )  
  
    # Basic validation  
    ok1, problems1 = validate_evidence_bundle_basic(bundle1)  
    ok2, problems2 = validate_evidence_bundle_basic(bundle2)  
    if not ok1:  
        raise AssertionError(f"bundle1 validation failed: {problems1}")  
    if not ok2:  
        raise AssertionError(f"bundle2 validation failed: {problems2}")  
  
    # Determinism: canonical JSON of entire bundle should match  
    j1 = canonical_json_dumps(bundle1)  
    j2 = canonical_json_dumps(bundle2)  
    if j1 != j2:  
        raise AssertionError("Determinism failure: canonical JSON differs between bundle1 and bundle2")  
  
    # Determinism: fingerprint should match too  
    if bundle1["bundle_fingerprint_sha256"] != bundle2["bundle_fingerprint_sha256"]:  
        raise AssertionError("Determinism failure: fingerprints differ")  
  
    # Determinism: artifact inventory should be stable and sorted by name  
    inv1 = bundle1.get("artifact_inventory")  
    inv2 = bundle2.get("artifact_inventory")  
    if inv1 != inv2:  
        raise AssertionError("Determinism failure: artifact inventories differ")  
  
    if inv1 is None or len(inv1) != 2:  
        raise AssertionError("Expected artifact_inventory with 2 entries")  
  
    if inv1[0]["name"] != "a.json" or inv1[1]["name"] != "b.json":  
        raise AssertionError("Expected artifact_inventory sorted by name")  
  
    # Rendering + artifact write/read  
    md = render_evidence_bundle_markdown(bundle1)  
    if f"Schema: `{EVIDENCE_BUNDLE_SCHEMA_ID}`" not in md:  
        raise AssertionError("Markdown render missing schema line")  
    if "## Artifact inventory (text-based)" not in md:  
        raise AssertionError("Markdown render missing artifact inventory section")  
  
    out_path = Path(__file__).resolve().parent / "_artifact_12_5_7_evidence_bundle.md"  
    out_path.write_text(md, encoding="utf-8")  
    md2 = out_path.read_text(encoding="utf-8")  
    if md2 != md:  
        raise AssertionError("Markdown write/read mismatch")  
  
    # Stable hash of markdown itself (sanity check determinism of renderer)  
    h1 = sha256_hex_of_text(md)  
    h2 = sha256_hex_of_text(md2)  
    if h1 != h2:  
        raise AssertionError("Markdown hash mismatch after write/read")  
  
  
if __name__ == "__main__":  
    try:  
        _run()  
        print("PASS: dev_smoke_12_5_7_evidence_bundle_assembler")  
    except Exception as e:  
        print(f"FAIL: dev_smoke_12_5_7_evidence_bundle_assembler: {e}")  
        raise  