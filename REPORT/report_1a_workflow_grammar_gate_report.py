"""  
REPORT-1A: Workflow grammar gate reporting.  
  
Single responsibility:  
- Convert BUILD-2G WorkflowTreeGateResult (and its per-file results) into a  
  deterministic, JSON-serializable report dict + JSON text.  
  
This is additive and does not modify any BUILD modules.  
"""  
  
from __future__ import annotations  
  
import json  
from dataclasses import asdict  
from typing import Any, Dict, List, Mapping, Sequence  
  
from BUILD.build_2g_workflow_tree_grammar_gate import WorkflowTreeGateResult  
  
__all__ = [  
    "build_grammar_gate_report",  
    "dump_grammar_gate_report_json_text",  
]  
  
  
def build_grammar_gate_report(tree_result: WorkflowTreeGateResult) -> Dict[str, Any]:  
    """  
    Build a JSON-serializable report from WorkflowTreeGateResult.  
  
    Output shape (stable):  
      {  
        "root_dir": "...",  
        "total_files": int,  
        "total_violations": int,  
        "files": [  
          {  
            "path": "...",  
            "wrote_file": bool,  
            "violation_count": int,  
            "violations": [{"action": "...", "path": "..."}, ...]  
          },  
          ...  
        ]  
      }  
    """  
    files: List[Dict[str, Any]] = []  
    for r in tree_result.file_results:  
        violations = [v.to_dict() for v in r.violations]  
        files.append(  
            {  
                "path": r.path,  
                "wrote_file": bool(r.wrote_file),  
                "violation_count": len(violations),  
                "violations": violations,  
            }  
        )  
  
    # Deterministic ordering by file path (case-insensitive)  
    files = sorted(files, key=lambda x: str(x["path"]).lower())  
  
    return {  
        "root_dir": tree_result.root_dir,  
        "total_files": tree_result.total_files,  
        "total_violations": tree_result.total_violations,  
        "files": files,  
    }  
  
  
def dump_grammar_gate_report_json_text(  
    report: Mapping[str, Any],  
    *,  
    indent: int = 2,  
    sort_keys: bool = True,  
) -> str:  
    """  
    Deterministically serialize the report to JSON text.  
    """  
    return json.dumps(dict(report), indent=indent, sort_keys=sort_keys, ensure_ascii=False) + "\n"  