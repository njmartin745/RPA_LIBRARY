"""  
DOC-1A: Workflow grammar gate documentation builder.  
  
Single responsibility:  
- Produce deterministic Markdown documentation for the workflow grammar gate subsystem.  
- No I/O; formatting only.  
"""  
  
from __future__ import annotations  
  
from typing import Sequence  
  
from BUILD.build_2d_step_grammar_gate import ALLOWED_ACTIONS  
  
__all__ = [  
    "build_workflow_grammar_gate_markdown",  
]  
  
  
def _format_actions_md(actions: Sequence[str]) -> str:  
    items = "\n".join([f"- `{a}`" for a in sorted(map(str, actions))])  
    return items  
  
  
def build_workflow_grammar_gate_markdown(*, allowed_actions: Sequence[str] = ALLOWED_ACTIONS) -> str:  
    actions_md = _format_actions_md(allowed_actions)  
  
    return "\n".join(  
        [  
            "# Workflow Grammar Gate (SCHEMA-1A)",  
            "",  
            "This framework supports a constrained workflow action grammar. The grammar gate provides:",  
            "- **Check**: detect unsupported actions (no writes); CI-friendly exit code",  
            "- **Fix**: sanitize workflows by stripping unsupported actions (optional writes)",  
            "",  
            "## Supported actions",  
            actions_md,  
            "",  
            "## Pipeline behavior (PIPE-1A)",  
            "- `mode=check`: does not write; exit code `0` if clean, else `2` if violations found",  
            "- `mode=fix`: sanitizes; exit code `0` (unless error)",  
            "- exit code `1`: unexpected error (e.g., missing root_dir)",  
            "",  
            "## CLI (CLI-1H)",  
            "Command: `workflow-grammar-gate`",  
            "",  
            "### Examples",  
            "Check a directory (prints report, exit 2 on violations):",  
            "```bash",  
            "workflow-grammar-gate ./workflows --mode check",  
            "```",  
            "",  
            "Write JSON + text reports without printing to stdout:",  
            "```bash",  
            "workflow-grammar-gate ./workflows --mode check --report-json ./out/report.json --report-text ./out/report.txt --quiet",  
            "```",  
            "",  
            "Sanitize into an output directory (preserves relative paths):",  
            "```bash",  
            "workflow-grammar-gate ./workflows --mode fix --output-dir ./sanitized --quiet",  
            "```",  
            "",  
            "Sanitize in place:",  
            "```bash",  
            "workflow-grammar-gate ./workflows --mode fix --in-place --quiet",  
            "```",  
        ]  
    )  