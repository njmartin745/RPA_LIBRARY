"""  
BUILD-1A: workflow grammar gate entrypoints spec.  
  
Single responsibility:  
- Provide a deterministic mapping of console_script style entrypoints for packaging/CI.  
  
This does not perform packaging; it only returns data (pure helpers).  
"""  
  
from __future__ import annotations  
  
from typing import Dict  
  
__all__ = [  
    "get_workflow_grammar_gate_entrypoints",  
    "get_workflow_grammar_gate_console_scripts",  
]  
  
  
def get_workflow_grammar_gate_console_scripts() -> Dict[str, str]:  
    """  
    Return console_scripts mapping for workflow grammar gate.  
  
    Example:  
      {"workflow-grammar-gate": "ENTRY.entry_1a_workflow_grammar_gate:main"}  
    """  
    return {  
        "workflow-grammar-gate": "ENTRY.entry_1a_workflow_grammar_gate:main",  
    }  
  
  
def get_workflow_grammar_gate_entrypoints() -> Dict[str, Dict[str, str]]:  
    """  
    Return entrypoints grouped by type.  
  
    Compatible with typical Python packaging concepts:  
      {"console_scripts": {...}}  
    """  
    return {  
        "console_scripts": get_workflow_grammar_gate_console_scripts(),  
    }  