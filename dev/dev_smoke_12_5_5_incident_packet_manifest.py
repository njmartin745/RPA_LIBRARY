from __future__ import annotations  
  
import os  
import tempfile  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from REPORT.report_12f_incident_packet_manifest import (  
    ArtifactRef,  
    get_incident_packet_template,  
    validate_incident_packet,  
    packet_to_json,  
    render_packet_markdown,  
    packet_fingerprint_sha256,  
    write_packet_markdown,  
)  
  
  
def main() -> int:  
    try:  
        base = get_incident_packet_template(  
            incident_id="INC-1001",  
            run_id="RUN-42",  
            env="prod",  
            summary="Production runs failing after bundle promotion; investigating selector drift.",  
        )  
  
        packet = type(base)(  
            packet_id=base.packet_id,  
            title=base.title,  
            incident_id=base.incident_id,  
            run_id=base.run_id,  
            env=base.env,  
            summary=base.summary,  
            artifacts=(  
                ArtifactRef(kind="run_log", label="latest", path="ARTIFACTS/RUN-42/run.log"),  
                ArtifactRef(kind="audit_log_jsonl", label="latest", path="ARTIFACTS/RUN-42/audit.jsonl"),  
                ArtifactRef(kind="replay_index_json", label="latest", path="ARTIFACTS/RUN-42/replay_index.json"),  
                ArtifactRef(kind="screenshot", label="step-3", path="ARTIFACTS/RUN-42/step_3.png", sha256="0" * 64),  
            ),  
            notes=base.notes,  
        )  
  
        errs = validate_incident_packet(packet)  
        assert errs == [], f"Packet validation errors: {errs}"  
  
        # Deterministic JSON + markdown + fingerprint  
        j1 = packet_to_json(packet)  
        j2 = packet_to_json(packet)  
        assert j1 == j2  
  
        fp1 = packet_fingerprint_sha256(packet)  
        fp2 = packet_fingerprint_sha256(packet)  
        assert fp1 == fp2  
        assert len(fp1) == 64  
  
        md = render_packet_markdown(packet)  
        assert "Incident Packet Manifest" in md  
        assert "Fingerprint (sha256)" in md  
  
        # Write/read markdown  
        with tempfile.TemporaryDirectory() as td:  
            out_md = os.path.join(td, "incident_packet.md")  
            write_packet_markdown(out_md, packet)  
            with open(out_md, "r", encoding="utf-8") as f:  
                md2 = f.read()  
            assert md2 == md  
  
        print("PASS: dev_smoke_12_5_5_incident_packet_manifest")  
        return 0  
    except Exception as e:  
        print(f"FAIL: dev_smoke_12_5_5_incident_packet_manifest :: {e}")  
        return 1  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  