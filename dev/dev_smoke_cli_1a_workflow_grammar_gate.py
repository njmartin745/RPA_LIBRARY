from __future__ import annotations  
  
import io  
import json  
import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT))   
from tempfile import TemporaryDirectory  
  
from CLI.cli_1a_workflow_grammar_gate import cli_workflow_grammar_gate  
from DOCTOR.doctor_1b_workflow_grammar_gate import doctor_workflow_grammar_gate_diagnosis  
from HISTORY.history_1a_workflow_grammar_gate_history import read_workflow_grammar_gate_history_jsonl  
  
  
def main() -> None:  
    with TemporaryDirectory() as td:  
        td = Path(td)  
        base = td / "base"  
        new = td / "new"  
        out_dir = td / "out"  
        base.mkdir(parents=True, exist_ok=True)  
        new.mkdir(parents=True, exist_ok=True)  
  
        wf_ok = {"name": "ok", "steps": [{"action": "log", "message": "hi"}]}  
        wf_bad = {"name": "bad", "steps": [{"action": "wait_seconds", "seconds": 1}]}  
  
        (base / "ok.json").write_text(json.dumps(wf_ok), encoding="utf-8")  
        (new / "ok.json").write_text(json.dumps(wf_ok), encoding="utf-8")  
        (new / "bad.json").write_text(json.dumps(wf_bad), encoding="utf-8")  
  
        # Build baseline report JSON file (schema-tolerant: CLI only needs dict)  
        dbase = doctor_workflow_grammar_gate_diagnosis(str(base), mode="check", in_place=False)  
        assert dbase.report is not None  
        baseline_path = td / "baseline_report.json"  
        baseline_path.write_text(json.dumps(dbase.report, sort_keys=True), encoding="utf-8")  
  
        hist_path = td / "history.jsonl"  
        meta_path = td / "meta.json"  
        meta_path.write_text(json.dumps({"suite": "dev_smoke"}), encoding="utf-8")  
  
        out = io.StringIO()  
        err = io.StringIO()  
  
        # check should fail  
        ec1 = cli_workflow_grammar_gate(  
            [  
                str(new),  
                "--mode",  
                "check",  
                "--no-in-place",  
                "--baseline-report",  
                str(baseline_path),  
                "--max-total-violations",  
                "0",  
                "--max-files-with-violations",  
                "0",  
                "--max-delta-total-violations",  
                "0",  
                "--history-jsonl",  
                str(hist_path),  
                "--history-meta-json",  
                str(meta_path),  
            ],  
            out=out,  
            err=err,  
        )  
        assert ec1 == 2  
        assert "FAIL" in out.getvalue()  
  
        out = io.StringIO()  
        err = io.StringIO()  
  
        # fix should succeed (guard defaults off for mode=fix)  
        ec2 = cli_workflow_grammar_gate(  
            [  
                str(new),  
                "--mode",  
                "fix",  
                "--no-in-place",  
                "--output-dir",  
                str(out_dir),  
                "--history-jsonl",  
                str(hist_path),  
                "--history-meta-json",  
                str(meta_path),  
            ],  
            out=out,  
            err=err,  
        )  
        assert ec2 == 0  
  
        out = io.StringIO()  
        err = io.StringIO()  
  
        # check fixed output should pass  
        ec3 = cli_workflow_grammar_gate(  
            [  
                str(out_dir),  
                "--mode",  
                "check",  
                "--no-in-place",  
                "--baseline-report",  
                str(baseline_path),  
                "--max-total-violations",  
                "0",  
                "--max-files-with-violations",  
                "0",  
                "--max-delta-total-violations",  
                "0",  
                "--history-jsonl",  
                str(hist_path),  
                "--history-meta-json",  
                str(meta_path),  
            ],  
            out=out,  
            err=err,  
        )  
        assert ec3 == 0  
        assert "OK" in out.getvalue()  
  
        rows = read_workflow_grammar_gate_history_jsonl(str(hist_path))  
        assert len(rows) == 3  
        assert rows[0]["meta"]["suite"] == "dev_smoke"  
  
    print("dev_smoke_cli_1a_workflow_grammar_gate: OK")  
  
  
if __name__ == "__main__":  
    main()  