from __future__ import annotations  
  
import os  
import tempfile  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
      
from HISTORY.history_12a_audit_logging_replay_spec import (  
    get_audit_log_spec,  
    events_to_jsonl,  
    build_replay_index,  
)  
from REPLAY.replay_12a_index_verifier import (  
    parse_events_jsonl,  
    verify_events_against_replay_index,  
    result_to_json,  
    render_result_markdown,  
    write_text_file,  
)  
  
  
def main() -> int:  
    try:  
        spec = get_audit_log_spec()  
  
        events = [  
            {  
                "seq": 1,  
                "run_id": "RUN-2",  
                "event_type": "step_started",  
                "ts": "2026-01-01T00:00:01Z",  
                "data": {"step": 0},  
            },  
            {  
                "seq": 0,  
                "run_id": "RUN-2",  
                "event_type": "run_started",  
                "ts": "2026-01-01T00:00:00Z",  
                "data": {"workflow": "wf-b"},  
            },  
        ]  
  
        idx = build_replay_index(  
            spec,  
            run_id="RUN-2",  
            bundle_fingerprint="BUNDLE-FP-XYZ",  
            events=events,  
        )  
  
        jsonl = events_to_jsonl(spec, events)  
  
        # Parse + verify passes  
        parsed = parse_events_jsonl(jsonl)  
        res1 = verify_events_against_replay_index(spec, events=parsed, index=idx)  
        res2 = verify_events_against_replay_index(spec, events=parsed, index=idx)  
        assert result_to_json(res1) == result_to_json(res2)  
        assert res1.passed is True  
        assert res1.mismatches == []  
  
        # Introduce a deterministic mismatch  
        parsed_bad = list(parsed)  
        parsed_bad[0] = dict(parsed_bad[0])  
        parsed_bad[0]["data"] = dict(parsed_bad[0]["data"])  
        parsed_bad[0]["data"]["step"] = 999  # changes hash  
        bad = verify_events_against_replay_index(spec, events=parsed_bad, index=idx)  
        assert bad.passed is False  
        assert len(bad.mismatches) >= 1  
  
        md = render_result_markdown(bad)  
        assert "Replay Verification Result" in md  
        assert "Mismatches" in md  
  
        # Write/read artifact  
        with tempfile.TemporaryDirectory() as td:  
            p = os.path.join(td, "replay_verification.md")  
            write_text_file(p, md)  
            with open(p, "r", encoding="utf-8") as f:  
                md2 = f.read()  
            assert md2 == md  
  
        print("PASS: dev_smoke_12_5_4_replay_index_verifier")  
        return 0  
    except Exception as e:  
        print(f"FAIL: dev_smoke_12_5_4_replay_index_verifier :: {e}")  
        return 1  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  