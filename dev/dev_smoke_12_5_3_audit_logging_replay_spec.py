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
    validate_audit_event,  
    canonical_event_dict,  
    event_to_canonical_json,  
    events_to_jsonl,  
    build_replay_index,  
    validate_replay_index,  
    spec_to_json,  
    render_spec_markdown,  
    replay_index_to_json,  
    render_replay_index_markdown,  
    write_jsonl_file,  
)  
  
  
def main() -> int:  
    try:  
        spec = get_audit_log_spec()  
  
        # Deterministic spec rendering  
        js1 = spec_to_json(spec)  
        js2 = spec_to_json(spec)  
        assert js1 == js2  
        md = render_spec_markdown(spec)  
        assert "Audit-Friendly Logging" in md  
        assert "Allowed event types" in md  
  
        # Sample events (intentionally out of order)  
        events = [  
            {  
                "seq": 2,  
                "run_id": "RUN-1",  
                "event_type": "step_completed",  
                "ts": "2026-01-01T00:00:02Z",  
                "data": {"step": 0, "status": "ok"},  
            },  
            {  
                "seq": 0,  
                "run_id": "RUN-1",  
                "event_type": "run_started",  
                "ts": "2026-01-01T00:00:00Z",  
                "data": {"workflow": "wf-a"},  
            },  
            {  
                "seq": 1,  
                "run_id": "RUN-1",  
                "event_type": "step_started",  
                "ts": "2026-01-01T00:00:01Z",  
                "data": {"step": 0},  
            },  
        ]  
  
        # Validate and canonicalize  
        for e in events:  
            errs = validate_audit_event(spec, e)  
            assert errs == [], f"Event validation errors: {errs}"  
            c = canonical_event_dict(spec, e)  
            assert set(c.keys()) == set(spec.required_fields)  
  
        # Deterministic canonical JSON + hashing stability  
        cjson_a = event_to_canonical_json(spec, events[0])  
        cjson_b = event_to_canonical_json(spec, events[0])  
        assert cjson_a == cjson_b  
  
        # Deterministic JSONL sorting (should begin with seq=0)  
        jsonl = events_to_jsonl(spec, events)  
        assert '"seq":0' in jsonl.splitlines()[0]  
  
        # Write/read JSONL artifact  
        with tempfile.TemporaryDirectory() as td:  
            p = os.path.join(td, "audit_log.jsonl")  
            write_jsonl_file(p, jsonl)  
            with open(p, "r", encoding="utf-8") as f:  
                jsonl_read = f.read()  
            assert jsonl_read == jsonl  
  
        # Replay index determinism across input order  
        idx1 = build_replay_index(  
            spec,  
            run_id="RUN-1",  
            bundle_fingerprint="BUNDLE-FP-ABC",  
            events=events,  
        )  
        idx2 = build_replay_index(  
            spec,  
            run_id="RUN-1",  
            bundle_fingerprint="BUNDLE-FP-ABC",  
            events=list(reversed(events)),  
        )  
        assert replay_index_to_json(idx1) == replay_index_to_json(idx2)  
  
        idx_errs = validate_replay_index(idx1)  
        assert idx_errs == [], f"Replay index validation errors: {idx_errs}"  
  
        rmd = render_replay_index_markdown(idx1)  
        assert "Replay Index" in rmd  
        assert "Event hashes" in rmd  
  
        print("PASS: dev_smoke_12_5_3_audit_logging_replay_spec")  
        return 0  
    except Exception as e:  
        print(f"FAIL: dev_smoke_12_5_3_audit_logging_replay_spec :: {e}")  
        return 1  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  