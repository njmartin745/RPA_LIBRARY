"""  
RUNBOOK-1A — Operational Playbook Generator  
  
Pure documentation generator. No Selenium.  
Writes a deterministic Markdown runbook describing how to use/run/debug/maintain the system.  
"""  
  
from __future__ import annotations  
  
from pathlib import Path  
from typing import Dict, Union  
  
__all__ = ["generate_runbook"]  
  
  
_RUNBOOK_MD = """# RPA Automation System — Operational Runbook  
  
## 1) Overview  
This repository is a modular Selenium RPA framework that can:  
- Execute JSON-defined workflows with a small supported step set  
- Capture artifacts (snapshots, logs, reports)  
- Recover from failures via reasoning/healing + retry  
- Learn from historical runs to improve stability (especially selectors)  
  
Key idea: **Workflows are data** (JSON). The system runs them, records outcomes, and produces artifacts for debugging and improvement.  
  
---  
  
## 2) Quick Start  
  
### Run a workflow JSON  
```bash  
rpa run WORKFLOWS/example.json"""