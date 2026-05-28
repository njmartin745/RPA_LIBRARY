"""  
ENTRY-1A: Workflow grammar gate entry point.  
  
Single responsibility:  
- Provide a thin ENTRY-layer wrapper around CLI-1H's cli_main, suitable for console entrypoints.  
"""  
  
from __future__ import annotations  
  
from typing import Optional, Sequence  
  
from CLI.cli_1h_workflow_grammar_gate_pipeline import cli_main  
  
__all__ = [  
    "main",  
]  
  
  
def main(argv: Optional[Sequence[str]] = None) -> int:  
    return int(cli_main(argv))  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  