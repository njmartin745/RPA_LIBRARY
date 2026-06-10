"""
VAL-2A — Deploy Bundle Validator

Purpose
-------
Perform deterministic validation of DEPLOY_BUNDLE_1A
artifacts before runtime execution.

Ensures workflow structure, selector references,
versioning metadata, and bundle integrity meet
platform requirements.

Acts as the primary quality gate between deploy
bundle loading and workflow execution.

Public API
----------
validate_deploy_bundle_1a(...)
assert_deploy_bundle_1a(...)

Dependencies
------------
BUILD-3A
SNAP-1A

Architecture Position
---------------------
DEPLOY_BUNDLE_1A
        ↓
WORKFLOW-1G
        ↓
VAL-2A
        ↓
RUN-1A
        ↓
PIPE-1A
        ↓
ACT-1A

Status
------
Audited

Notes
-----
Validation Areas:

DEPLOY_BUNDLE_1A
        ↓
Schema Validation
        ↓
Workflow Validation
        ↓
Selector Validation
        ↓
Version/Fingerprint Validation
        ↓
Deterministic Report

Supports both report-based validation and
fail-fast exception-based validation.

Responsibilities
----------------
- Validate deploy bundle structure
- Validate workflow definitions
- Validate selector references
- Validate repeat block structure
- Validate version metadata
- Validate fingerprint metadata
- Enforce selector_ref-first policy
- Produce deterministic validation reports
- Protect runtime execution from invalid artifacts

Validation Categories
---------------------
- Schema validation
- Workflow validation
- Selector integrity validation
- Version validation
- Fingerprint validation
- Runtime policy validation

Runtime Policy Enforcement
--------------------------
Deploy bundles are expected to be
selector_ref-first.

When require_selector_ref=True:

- selector_ref is required
- raw selectors generate warnings
- selector references must exist within
  selector_pack.selectors

Deterministic Guarantees
------------------------
Validation results are:

- Repeatable
- Deterministic
- Sorted for stable output
- Suitable for CI and audit reporting

Architecture Notes
------------------
This module represents the final validation
boundary before runtime execution.

Upstream systems are responsible for creating
valid deployment artifacts.

Downstream runtime systems assume artifacts
have passed validation and may rely on those
guarantees without performing duplicate checks.

This validator serves as the central quality
gate for deployment portability, replayability,
runtime safety, and artifact integrity.
"""

from __future__ import annotations  
  
import importlib
from dataclasses import dataclass  
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple  
  
from BUILD.build_3a_deploy_bundle_format import DEPLOY_BUNDLE_SCHEMA_ID  
from SNAP.snap_1a_workflow_capture import ALLOWED_WORKFLOW_ACTIONS  
  
__all__ = [  
    "ValidationIssue",  
    "validate_deploy_bundle_1a",  
    "assert_deploy_bundle_1a",  
    "dev_smoke",  
]  
  
  
@dataclass(frozen=True)  
class ValidationIssue:  
    level: str  # "error" | "warning"  
    path: str   # JSON-pointer-ish path  
    message: str  
  
    def as_dict(self) -> Dict[str, str]:  
        return {"level": self.level, "path": self.path, "message": self.message}  
  
  
def _is_nonempty_str(x: Any) -> bool:  
    return isinstance(x, str) and x.strip() != ""  
  
  
def _json_pointer_escape(token: str) -> str:  
    return token.replace("~", "~0").replace("/", "~1")  
  
  
def _join(path: str, token: str) -> str:  
    if path == "":  
        return "/" + _json_pointer_escape(token)  
    return path + "/" + _json_pointer_escape(token)  
  
  
def _hex64(x: Any) -> bool:  
    if not isinstance(x, str) or len(x) != 64:  
        return False  
    try:  
        int(x, 16)  
        return True  
    except Exception:  
        return False  
  
  
def _iter_steps_with_paths(steps: Any, base_path: str) -> Iterable[Tuple[str, Mapping[str, Any]]]:  
    if not isinstance(steps, list):  
        return  
    for i, step in enumerate(steps):  
        if isinstance(step, Mapping):  
            yield (_join(base_path, str(i)), step)  
  
  
def _collect_selector_refs(steps: Any, base_path: str) -> List[Tuple[str, str]]:  
    """  
    Returns list of (path_to_selector_ref, selector_ref_value) in traversal order.  
    """  
    out: List[Tuple[str, str]] = []  
  
    def walk(cur_steps: Any, cur_path: str) -> None:  
        for sp, step in _iter_steps_with_paths(cur_steps, cur_path):  
            action = step.get("action")  
            if action == "repeat":  
                walk(step.get("steps"), _join(sp, "steps"))  
  
            ref = step.get("selector_ref")  
            if isinstance(ref, str) and ref.strip():  
                out.append((_join(sp, "selector_ref"), ref.strip()))  
  
    walk(steps, base_path)  
    return out  


def _iter_json_values(obj: Any, base_path: str = "") -> Iterable[Tuple[str, Any]]:
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            yield from _iter_json_values(v, _join(base_path, str(k)))
        return
    if isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _iter_json_values(v, _join(base_path, str(i)))
        return
    yield (base_path or "/", obj)


def _is_todo_placeholder(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    s = value.strip().upper()
    return s == "TODO" or s.startswith("TODO_") or s.startswith("TODO:")


def _runtime_action_names() -> Set[str]:
    try:
        mod = importlib.import_module("ACT.act_1a_action_engine")
    except Exception:
        return set()
    actions = getattr(mod, "_ACTIONS", None)
    if not isinstance(actions, Mapping):
        return set()
    return {str(k) for k, v in actions.items() if isinstance(k, str) and callable(v)}
  
  
def validate_deploy_bundle_1a(  
    bundle: Mapping[str, Any],  
    *,  
    require_version_fingerprint: bool = True,  
    require_selector_ref: bool = True,  
    production: bool = False,
) -> Dict[str, Any]:  
    """  
    Deterministic pre-deploy validation for DEPLOY_BUNDLE_1A.  
  
    Returns:  
      {  
        "ok": bool,  
        "schema_id": "DEPLOY_BUNDLE_VALIDATION_1A",  
        "errors": [ {level,path,message}, ... ],  
        "warnings": [ ... ]  
      }  
    """  
    issues: List[ValidationIssue] = []  
  
    def err(path: str, msg: str) -> None:  
        issues.append(ValidationIssue("error", path, msg))  
  
    def warn(path: str, msg: str) -> None:  
        issues.append(ValidationIssue("warning", path, msg))  
  
    if not isinstance(bundle, Mapping):  
        err("/", "bundle must be a mapping")  
        return {  
            "schema_id": "DEPLOY_BUNDLE_VALIDATION_1A",  
            "ok": False,  
            "errors": [i.as_dict() for i in issues],  
            "warnings": [],  
        }  
  
    if bundle.get("schema_id") != DEPLOY_BUNDLE_SCHEMA_ID:  
        err("/schema_id", f"schema_id must be {DEPLOY_BUNDLE_SCHEMA_ID}")  
  
    if not _is_nonempty_str(bundle.get("name")):  
        err("/name", "name must be a non-empty string")  
  
    wf = bundle.get("workflow")  
    if not isinstance(wf, Mapping):  
        err("/workflow", "workflow must be a mapping")  
        wf = {}  
  
    steps = wf.get("steps") if isinstance(wf, Mapping) else None  
    if not isinstance(steps, list):  
        err("/workflow/steps", "workflow.steps must be a list")  
        steps = []  
  
    sp = bundle.get("selector_pack")  
    if not isinstance(sp, Mapping):  
        err("/selector_pack", "selector_pack must be a mapping")  
        sp = {}  
  
    selectors = sp.get("selectors") if isinstance(sp, Mapping) else None  
    if not isinstance(selectors, Mapping):  
        err("/selector_pack/selectors", "selector_pack.selectors must be a mapping")  
        selectors = {}  
  
    # version/fingerprint requirements  
    if require_version_fingerprint:  
        if not _is_nonempty_str(bundle.get("version")):  
            err("/version", "version is required (non-empty string)")  
  
        fp = bundle.get("fingerprint")  
        if not isinstance(fp, Mapping):  
            err("/fingerprint", "fingerprint is required (mapping)")  
        else:  
            if fp.get("algo") != "sha256":  
                err("/fingerprint/algo", "fingerprint.algo must be 'sha256'")  
            if not _hex64(fp.get("sha256")):  
                err("/fingerprint/sha256", "fingerprint.sha256 must be 64 hex chars")  
            if not _is_nonempty_str(fp.get("canonicalization")):  
                warn("/fingerprint/canonicalization", "fingerprint.canonicalization should be non-empty")  

    if production:
        for p, value in _iter_json_values(bundle):
            if _is_todo_placeholder(value):
                err(p, f"unresolved TODO placeholder is not allowed in production deploy bundles: {value!r}")
  
    # step validation  
    allowed = set(ALLOWED_WORKFLOW_ACTIONS)  
    runtime_actions = _runtime_action_names() if production else set()
  
    def validate_step(step: Any, step_path: str) -> None:  
        if not isinstance(step, Mapping):  
            err(step_path, "step must be a mapping")  
            return  
  
        action = step.get("action")  
        if not _is_nonempty_str(action):  
            err(_join(step_path, "action"), "action must be a non-empty string")  
            return  
        action = str(action).strip()  
  
        if action not in allowed:  
            err(_join(step_path, "action"), f"unsupported action: {action}")  
            return  
  
        if action == "open":  
            if not _is_nonempty_str(step.get("url")):  
                err(_join(step_path, "url"), "open requires url")  
  
        if action in {"click_selector", "wait_for_selector", "type_selector_secret"}:  
            has_ref = _is_nonempty_str(step.get("selector_ref"))  
            has_sel = _is_nonempty_str(step.get("selector"))  
  
            if require_selector_ref:  
                if not has_ref:  
                    err(_join(step_path, "selector_ref"), f"{action} requires selector_ref (deploy bundles are selector_ref-first)")  
                if has_sel:  
                    if production:
                        err(_join(step_path, "selector"), "raw selector is not allowed in production deploy bundle steps; use selector_ref")
                    else:
                        warn(_join(step_path, "selector"), "raw selector present; prefer selector_ref-only in deploy bundles")  
            else:  
                if not (has_ref or has_sel):  
                    err(step_path, f"{action} requires selector_ref or selector")  
  
            if action == "type_selector_secret":  
                # Require at least one secret ref field (names used across the framework)  
                if not any(_is_nonempty_str(step.get(k)) for k in ("secret_ref", "text_secret_ref", "value_secret_ref")):  
                    err(step_path, "type_selector_secret requires secret_ref/text_secret_ref/value_secret_ref")  
  
        if action == "repeat":  
            nested = step.get("steps")  
            if not isinstance(nested, list):  
                err(_join(step_path, "steps"), "repeat.steps must be a list")  
            else:  
                for i, child in enumerate(nested):  
                    validate_step(child, _join(_join(step_path, "steps"), str(i)))  
  
            count = step.get("times", step.get("count"))  
            if not isinstance(count, int) or count <= 0:  
                err(step_path, "repeat requires a positive integer in 'times' or 'count'")  

        if production and action not in runtime_actions:
            err(_join(step_path, "action"), f"action has no ACT-1A runtime implementation: {action}")
  
    for i, step in enumerate(steps):  
        validate_step(step, _join("/workflow/steps", str(i)))  
  
    # selector_ref existence check  
    selector_ref_paths = _collect_selector_refs(steps, "/workflow/steps")  
    selector_ids = set(k for k in selectors.keys() if isinstance(k, str))  
  
    for p, ref in selector_ref_paths:  
        if ref not in selector_ids:  
            err(p, f"selector_ref not found in selector_pack.selectors: {ref}")  
  
    # deterministic ordering  
    errors = sorted([i for i in issues if i.level == "error"], key=lambda x: (x.path, x.message))  
    warnings = sorted([i for i in issues if i.level == "warning"], key=lambda x: (x.path, x.message))  
  
    return {  
        "schema_id": "DEPLOY_BUNDLE_VALIDATION_1A",  
        "ok": len(errors) == 0,  
        "errors": [e.as_dict() for e in errors],  
        "warnings": [w.as_dict() for w in warnings],  
    }  
  
  
def assert_deploy_bundle_1a(  
    bundle: Mapping[str, Any],  
    *,  
    require_version_fingerprint: bool = True,  
    require_selector_ref: bool = True,  
    production: bool = False,
) -> None:  
    report = validate_deploy_bundle_1a(  
        bundle,  
        require_version_fingerprint=require_version_fingerprint,  
        require_selector_ref=require_selector_ref,  
        production=production,
    )  
    if not report["ok"]:  
        msgs = "\n".join(f"{e['path']}: {e['message']}" for e in report["errors"])  
        raise ValueError(f"DEPLOY_BUNDLE_1A validation failed:\n{msgs}")  
  
  
def dev_smoke() -> None:  
    good = {  
        "schema_id": "DEPLOY_BUNDLE_1A",  
        "name": "x",  
        "version": "sha256:aaaaaaaaaaaa",  
        "fingerprint": {"algo": "sha256", "canonicalization": "x", "sha256": "0" * 64, "bytes": 1, "dropped_top_level_keys": []},  
        "workflow": {"steps": [{"action": "open", "url": "https://example.test"}, {"action": "click_selector", "selector_ref": "cap_001"}]},  
        "selector_pack": {"schema_id": "SELECTOR_PACK_1A", "name": "x", "selectors": {"cap_001": {"selector": "#a", "type": "css"}}},  
        "meta": {"source_schema_id": "CAPTURE_BUNDLE_1A", "source_name": "x"},  
    }  
    rep = validate_deploy_bundle_1a(good)  
    assert rep["ok"] is True  
  
    bad = dict(good)  
    bad["workflow"] = {"steps": [{"action": "click_selector", "selector_ref": "missing"}]}  
    rep2 = validate_deploy_bundle_1a(bad)  
    assert rep2["ok"] is False  
    assert any("not found" in e["message"] for e in rep2["errors"])  
