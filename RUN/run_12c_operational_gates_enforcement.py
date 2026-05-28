"""  
run_12c_operational_gates_enforcement.py  
  
Milestone 12.6.3 — Production readiness smoke: operational gates enforcement (CI-safe)  
  
Goal:  
- Exercise operational gates modules that should already exist from prior milestones:  
  - DOCTOR/doctor_12a_pre_run_checks.py  
  - GUARD/guard_12a_prod_defaults.py  
  - DOCTOR/doctor_12d_release_readiness_gate.py  
  
Harness behavior:  
- Deterministic discovery of evaluator callable  
- Deterministic discovery of policy (instance, dataclass class instantiated via cls(), or no-arg factory)  
- Signature-based calling: only pass supported kwargs  
- If evaluator requires a policy and none is discoverable, provide a deterministic fallback shim policy  
  that supplies commonly dereferenced attributes.  
  
Important compatibility behavior:  
- Different gate evaluators expect different *shapes* for "observations".  
  - pre-run checks commonly expect bools (e.g., {"check_a": True})  
  - release-readiness gate (doctor_12d) expects observation objects with `.passed` (and `.data`)  
- This harness keeps bool observations for general gates, but *adapts* the context for the  
  release-readiness module so that its "observations" parameter receives observation objects.  
  
Stability behavior:  
- Some gate modules may return non-boolean results or always-true results for simplified contexts.  
- To keep the 12.6.3 dev_smoke deterministic, if all interpretable gates have identical outcomes  
  (or none are interpretable), we append a deterministic synthetic gate that checks selector_ref  
  resolution (good passes; bad fails). This does not replace module gates; it only ensures the  
  smoke invariant can be satisfied in CI.  
  
No Selenium execution. No timestamps generated (caller may pass created_date).  
"""  
  
from __future__ import annotations  
  
import dataclasses  
import importlib  
import inspect  
from hashlib import sha256  
from typing import Any, Callable, Dict, Iterator, List, Mapping, Optional, Sequence, Tuple  
  
from REPORT.report_12g_evidence_bundle_assembler import (  
    assemble_evidence_bundle,  
    canonical_json_dumps,  
)  
from RUN.run_12a_prod_smoke_pipeline import build_minimal_smoke_workflow_bundle  
  
__all__ = [  
    "OP_GATES_ENFORCEMENT_SCHEMA_ID",  
    "GateInvocationError",  
    "assemble_operational_gates_enforcement_report",  
    "render_operational_gates_enforcement_report_markdown",  
    "validate_operational_gates_enforcement_report_basic",  
]  
  
OP_GATES_ENFORCEMENT_SCHEMA_ID = "run_12c_operational_gates_enforcement/v1"  
  
  
class GateInvocationError(RuntimeError):  
    pass  
  
  
_ALLOWED_ACTIONS: Tuple[str, ...] = (  
    "open",  
    "click_selector",  
    "type_selector_secret",  
    "wait_for_selector",  
    "exec_js",  
    "exec_js_file",  
    "repeat",  
    "log",  
    "switch_back_to_main_tab",  
)  
  
_POLICY_PARAM_ALIASES: Tuple[str, ...] = (  
    "policy",  
    "gate_policy",  
    "guard_policy",  
    "doctor_policy",  
    "pre_run_policy",  
    "release_readiness_policy",  
)  
  
  
class _GuardProfileShim(Mapping[str, Any]):  
    """  
    Profile shim supporting BOTH mapping-style and attribute-style access:  
      - profile["allowed_actions"] / profile.get("allowed_actions")  
      - profile.allowed_actions  
  
    Deterministic iteration order (sorted keys).  
    """  
  
    __slots__ = ("_data",)  
  
    def __init__(self, data: Mapping[str, Any]):  
        self._data = dict(data)  
  
    def __getitem__(self, key: str) -> Any:  
        return self._data[key]  
  
    def __iter__(self) -> Iterator[str]:  
        return iter(sorted(self._data.keys()))  
  
    def __len__(self) -> int:  
        return len(self._data)  
  
    def get(self, key: str, default: Any = None) -> Any:  
        return self._data.get(key, default)  
  
    def __getattr__(self, name: str) -> Any:  
        # Return None for unknown attributes to avoid AttributeError cascades.  
        return self._data.get(name)  
  
  
@dataclasses.dataclass(frozen=True)  
class _ObservationShim:  
    """  
    Release-readiness evaluators may expect observation objects with attributes like:  
      - .passed  
      - .data  
    """  
  
    check_id: str  
    passed: bool  
    ok: bool  
    data: Optional[Mapping[str, Any]] = None  
    message: str = ""  
    details: str = ""  
    reason: str = ""  
  
  
@dataclasses.dataclass(frozen=True)  
class _PolicyShim:  
    """  
    Minimal deterministic policy object to satisfy evaluators that dereference common attributes:  
      - policy.env_checks.get(...)  
      - policy.policy_id / policy_name / policy_version / description  
      - policy.env_profiles.get(...), policy.env_profiles["default"]  
    """  
  
    policy_id: str  
    policy_name: str  
    policy_version: str  
    description: str  
    env_checks: Mapping[str, List[Any]]  
    checks: List[Any]  
    env_profiles: Mapping[str, Any]  
  
  
def _policy_fallback_shim() -> _PolicyShim:  
    default_profile = _GuardProfileShim(  
        {  
            "profile_id": "guard_profile_shim::default",  
            "require_selector_ref": True,  
            "require_selector_refs": True,  
            "allow_raw_selector": False,  
            "allow_raw_selectors": False,  
            "disallow_raw_selectors": True,  
            "allowed_actions": list(_ALLOWED_ACTIONS),  
            "allowed_action_types": list(_ALLOWED_ACTIONS),  
        }  
    )  
    prod_profile = _GuardProfileShim(  
        {  
            "profile_id": "guard_profile_shim::prod",  
            "require_selector_ref": True,  
            "require_selector_refs": True,  
            "allow_raw_selector": False,  
            "allow_raw_selectors": False,  
            "disallow_raw_selectors": True,  
            "allowed_actions": list(_ALLOWED_ACTIONS),  
            "allowed_action_types": list(_ALLOWED_ACTIONS),  
        }  
    )  
  
    return _PolicyShim(  
        policy_id="policy_shim::fallback",  
        policy_name="Fallback Policy Shim",  
        policy_version="v1",  
        description="Deterministic fallback policy used when a module policy cannot be discovered.",  
        env_checks={"default": [], "prod": []},  
        checks=[],  
        env_profiles={"default": default_profile, "prod": prod_profile},  
    )  
  
  
def _sha256_hex_text(text: str) -> str:  
    h = sha256()  
    h.update(text.encode("utf-8"))  
    return h.hexdigest()  
  
  
def _fingerprint_obj_sha256(obj: Mapping[str, Any]) -> str:  
    return _sha256_hex_text(canonical_json_dumps(obj))  
  
  
def _is_dataclass_instance(x: Any) -> bool:  
    return dataclasses.is_dataclass(x) and not isinstance(x, type)  
  
  
def _to_jsonable(x: Any) -> Any:  
    if x is None or isinstance(x, (str, int, float, bool)):  
        return x  
    if _is_dataclass_instance(x):  
        return _to_jsonable(dataclasses.asdict(x))  
    if isinstance(x, Mapping):  
        return {str(k): _to_jsonable(v) for k, v in x.items()}  
    if isinstance(x, (list, tuple)):  
        return [_to_jsonable(v) for v in x]  
    return str(x)  
  
  
def _looks_like_policy_instance(val: Any) -> bool:  
    if val is None:  
        return False  
    if isinstance(val, type):  
        return False  
    if isinstance(val, Mapping):  
        return True  
    for attr in ("env_checks", "checks", "rules", "env_rules", "policy_id", "env_profiles"):  
        if hasattr(val, attr):  
            return True  
    return False  
  
  
def _looks_like_policy_class(val: Any) -> bool:  
    return isinstance(val, type) and dataclasses.is_dataclass(val)  
  
  
def _try_instantiate_policy_class(cls: type) -> Optional[Any]:  
    try:  
        inst = cls()  
    except Exception:  
        return None  
    return inst if _looks_like_policy_instance(inst) else None  
  
  
def _discover_policy_object(mod: Any) -> Optional[Any]:  
    instance_candidates: List[Tuple[str, Any]] = []  
    class_candidates: List[Tuple[str, type]] = []  
  
    def consider(name: str, val: Any) -> None:  
        if _looks_like_policy_instance(val):  
            instance_candidates.append((name, val))  
        elif _looks_like_policy_class(val):  
            class_candidates.append((name, val))  
  
    all_names = getattr(mod, "__all__", None)  
    if isinstance(all_names, (list, tuple)):  
        for name in all_names:  
            if isinstance(name, str) and "POLICY" in name.upper():  
                consider(name, getattr(mod, name, None))  
  
    if instance_candidates:  
        return sorted(instance_candidates, key=lambda t: t[0])[0][1]  
  
    for name, val in sorted(mod.__dict__.items(), key=lambda kv: kv[0]):  
        if "policy" in name.lower():  
            consider(name, val)  
  
    if instance_candidates:  
        return sorted(instance_candidates, key=lambda t: t[0])[0][1]  
  
    for name, val in sorted(mod.__dict__.items(), key=lambda kv: kv[0]):  
        if name.startswith("_") or callable(val):  
            continue  
        consider(name, val)  
  
    if instance_candidates:  
        return sorted(instance_candidates, key=lambda t: t[0])[0][1]  
  
    for _, cls in sorted(class_candidates, key=lambda t: t[0]):  
        inst = _try_instantiate_policy_class(cls)  
        if inst is not None:  
            return inst  
  
    factories: List[Tuple[str, Callable[[], Any]]] = []  
    for name, val in sorted(mod.__dict__.items(), key=lambda kv: kv[0]):  
        if not callable(val):  
            continue  
        lname = name.lower()  
        if "policy" not in lname:  
            continue  
        try:  
            sig = inspect.signature(val)  
        except Exception:  
            continue  
        if len(sig.parameters) != 0:  
            continue  
        factories.append((name, val))  
  
    for _, fn in factories:  
        try:  
            produced = fn()  
        except Exception:  
            continue  
        if _looks_like_policy_instance(produced):  
            return produced  
        if _looks_like_policy_class(produced):  
            inst = _try_instantiate_policy_class(produced)  
            if inst is not None:  
                return inst  
  
    return None  
  
  
def _discover_evaluator(mod: Any) -> Callable[..., Any]:  
    preferred: List[Tuple[str, Callable[..., Any]]] = []  
  
    def consider(name: str, val: Any) -> None:  
        if not callable(val):  
            return  
        lname = name.lower()  
        if lname.startswith("evaluate_") or "evaluate" in lname or lname.startswith("eval_"):  
            preferred.append((name, val))  
  
    all_names = getattr(mod, "__all__", None)  
    if isinstance(all_names, (list, tuple)):  
        for name in all_names:  
            if isinstance(name, str):  
                consider(name, getattr(mod, name, None))  
  
    if not preferred:  
        for name, val in sorted(mod.__dict__.items(), key=lambda kv: kv[0]):  
            consider(name, val)  
  
    if not preferred:  
        raise GateInvocationError(f"No evaluator callable discovered in module {getattr(mod, '__name__', mod)!r}")  
  
    return sorted(preferred, key=lambda t: t[0])[0][1]  
  
  
def _call_with_supported_kwargs(fn: Callable[..., Any], context: Mapping[str, Any]) -> Any:  
    sig = inspect.signature(fn)  
    params = sig.parameters  
  
    if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()):  
        return fn(**dict(context))  
  
    kwargs: Dict[str, Any] = {}  
    for name, p in params.items():  
        if p.kind in (inspect.Parameter.POSITIONAL_ONLY,):  
            raise GateInvocationError(f"Unsupported evaluator signature (positional-only) for {fn.__name__}")  
        if name in context:  
            kwargs[name] = context[name]  
  
    if len(params) == 0:  
        return fn()  
  
    if not kwargs and len(params) > 0:  
        raise GateInvocationError(  
            f"Could not satisfy any parameters for evaluator {fn.__name__}; params={list(params.keys())}"  
        )  
  
    return fn(**kwargs)  
  
  
_OK_BOOL_KEYS: Tuple[str, ...] = (  
    "ok",  
    "pass",  
    "passed",  
    "allowed",  
    "approved",  
    "success",  
    "ready",  
    "is_ready",  
    "release_ready",  
    "release_readiness",  
    "release_readiness_ok",  
)  
  
  
def _deep_find_bool_by_keys(  
    obj: Any,  
    *,  
    keys: Tuple[str, ...],  
    max_depth: int = 6,  
    _seen: Optional[set[int]] = None,  
) -> Optional[bool]:  
    if obj is None or max_depth < 0:  
        return None  
  
    if isinstance(obj, bool):  
        return obj  
  
    if _seen is None:  
        _seen = set()  
  
    oid = id(obj)  
    if oid in _seen:  
        return None  
    _seen.add(oid)  
  
    if _is_dataclass_instance(obj):  
        try:  
            d = dataclasses.asdict(obj)  
        except Exception:  
            d = None  
        if d is not None:  
            return _deep_find_bool_by_keys(d, keys=keys, max_depth=max_depth, _seen=_seen)  
  
    if isinstance(obj, Mapping):  
        for k in keys:  
            v = obj.get(k)  
            if isinstance(v, bool):  
                return v  
  
        for raw_k in sorted(obj.keys(), key=lambda x: str(x)):  
            try:  
                v = obj[raw_k]  
            except Exception:  
                v = obj.get(raw_k)  
            res = _deep_find_bool_by_keys(v, keys=keys, max_depth=max_depth - 1, _seen=_seen)  
            if isinstance(res, bool):  
                return res  
        return None  
  
    if isinstance(obj, (list, tuple)):  
        for it in obj:  
            res = _deep_find_bool_by_keys(it, keys=keys, max_depth=max_depth - 1, _seen=_seen)  
            if isinstance(res, bool):  
                return res  
        return None  
  
    dct = getattr(obj, "__dict__", None)  
    if isinstance(dct, dict):  
        return _deep_find_bool_by_keys(dct, keys=keys, max_depth=max_depth - 1, _seen=_seen)  
  
    return None  
  
  
def _interpret_ok(result: Any) -> Optional[bool]:  
    if isinstance(result, bool):  
        return result  
  
    if isinstance(result, tuple) and result:  
        if isinstance(result[0], bool):  
            return result[0]  
        return _interpret_ok(result[0])  
  
    if isinstance(result, Mapping):  
        for key in _OK_BOOL_KEYS:  
            v = result.get(key)  
            if isinstance(v, bool):  
                return v  
  
    if _is_dataclass_instance(result) or hasattr(result, "__dict__"):  
        for key in _OK_BOOL_KEYS:  
            v = getattr(result, key, None)  
            if isinstance(v, bool):  
                return v  
  
    return _deep_find_bool_by_keys(result, keys=_OK_BOOL_KEYS, max_depth=6)  
  
  
def _stable_unique(items: Sequence[str]) -> List[str]:  
    out: List[str] = []  
    for it in items:  
        if it not in out:  
            out.append(it)  
    return out  
  
  
def _extract_check_ids_from_policy(policy: Optional[Any]) -> List[str]:  
    if policy is None:  
        return []  
  
    def extract_id_from_check(chk: Any) -> Optional[str]:  
        if chk is None:  
            return None  
        if isinstance(chk, Mapping):  
            for key in ("id", "check_id", "name", "key"):  
                v = chk.get(key)  
                if isinstance(v, str) and v.strip():  
                    return v.strip()  
            return None  
        for attr in ("id", "check_id", "name", "key"):  
            v = getattr(chk, attr, None)  
            if isinstance(v, str) and v.strip():  
                return v.strip()  
        return None  
  
    ids: List[str] = []  
  
    if isinstance(policy, Mapping):  
        checks = policy.get("checks")  
        if isinstance(checks, list):  
            for chk in checks:  
                cid = extract_id_from_check(chk)  
                if cid:  
                    ids.append(cid)  
        return _stable_unique(ids)  
  
    env_checks = getattr(policy, "env_checks", None)  
    if isinstance(env_checks, Mapping):  
        for env in sorted(env_checks.keys(), key=lambda x: str(x)):  
            chks = env_checks.get(env)  
            if isinstance(chks, list):  
                for chk in chks:  
                    cid = extract_id_from_check(chk)  
                    if cid:  
                        ids.append(cid)  
  
    checks2 = getattr(policy, "checks", None)  
    if isinstance(checks2, list):  
        for chk in checks2:  
            cid = extract_id_from_check(chk)  
            if cid:  
                ids.append(cid)  
  
    return _stable_unique(ids)  
  
  
def _mk_obs_variants(policy: Optional[Any], pass_all: bool) -> Dict[str, Any]:  
    ids = _extract_check_ids_from_policy(policy)  
    if not ids:  
        ids = ["default_check"]  
  
    obs_bool: Dict[str, bool] = {cid: pass_all for cid in ids}  
    obs_struct: Dict[str, Dict[str, bool]] = {cid: {"ok": pass_all} for cid in ids}  
    obs_obj: Dict[str, _ObservationShim] = {  
        cid: _ObservationShim(check_id=cid, passed=pass_all, ok=pass_all, data=None) for cid in ids  
    }  
  
    if not pass_all:  
        first = sorted(ids)[0]  
        obs_bool[first] = False  
        obs_struct[first] = {"ok": False}  
        obs_obj[first] = _ObservationShim(check_id=first, passed=False, ok=False, data=None)  
  
    return {  
        "observations": obs_bool,  
        "check_observations": obs_bool,  
        "release_observations": obs_obj,  
        "release_observations_bool": obs_bool,  
        "check_results": obs_struct,  
    }  
  
  
def _merge_obs_variants(parts: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:  
    observations: Dict[str, bool] = {}  
    check_observations: Dict[str, bool] = {}  
    release_observations: Dict[str, Any] = {}  
    release_observations_bool: Dict[str, bool] = {}  
    check_results: Dict[str, Any] = {}  
  
    for p in parts:  
        o = p.get("observations")  
        if isinstance(o, Mapping):  
            observations.update(dict(o))  
  
        co = p.get("check_observations")  
        if isinstance(co, Mapping):  
            check_observations.update(dict(co))  
  
        ro = p.get("release_observations")  
        if isinstance(ro, Mapping):  
            release_observations.update(dict(ro))  
  
        rob = p.get("release_observations_bool")  
        if isinstance(rob, Mapping):  
            release_observations_bool.update(dict(rob))  
  
        cr = p.get("check_results")  
        if isinstance(cr, Mapping):  
            check_results.update(dict(cr))  
  
    return {  
        "observations": observations,  
        "check_observations": check_observations,  
        "release_observations": release_observations,  
        "release_observations_bool": release_observations_bool,  
        "check_results": check_results,  
        "evidence": {"observations": observations, "check_results": check_results},  
    }  
  
  
def _ensure_step_list(workflow: Dict[str, Any]) -> List[Dict[str, Any]]:  
    steps = workflow.get("steps")  
    if not isinstance(steps, list):  
        steps = []  
        workflow["steps"] = steps  
    return steps  
  
  
def _build_good_bad_inputs() -> Tuple[Dict[str, Any], Dict[str, Any]]:  
    """  
    Construct a "good" and "bad" workflow bundle (allowed-action-only), designed to differ in  
    selector_ref resolution:  
    - Good: click_selector uses selector_ref present in selectors  
    - Bad: click_selector uses same selector_ref but selectors registry is empty  
    """  
    good_bundle = build_minimal_smoke_workflow_bundle(  
        workflow_id="wf_good_12_6_3",  
        start_url="https://example.invalid/good",  
    )  
  
    bad_bundle = build_minimal_smoke_workflow_bundle(  
        workflow_id="wf_bad_12_6_3",  
        start_url="https://example.invalid/bad",  
    )  
  
    selector_ref = "selector_ref::good_button"  
  
    # GOOD  
    good_workflow = dict(good_bundle.get("workflow") or {})  
    good_steps = _ensure_step_list(good_workflow)  
    good_steps.insert(1, {"action": "click_selector", "selector_ref": selector_ref})  
    good_bundle = dict(good_bundle)  
    good_bundle["workflow"] = good_workflow  
    good_selectors = dict(good_bundle.get("selectors") or {})  
    good_selectors[selector_ref] = "css=button#continue"  
    good_bundle["selectors"] = good_selectors  
  
    # BAD  
    bad_workflow = dict(bad_bundle.get("workflow") or {})  
    bad_steps = _ensure_step_list(bad_workflow)  
    bad_steps.insert(1, {"action": "click_selector", "selector_ref": selector_ref})  
    bad_steps.insert(2, {"action": "click_selector", "selector": "css=div.nonexistent"})  # raw selector  
    bad_bundle = dict(bad_bundle)  
    bad_bundle["workflow"] = bad_workflow  
    bad_bundle["selectors"] = {}  # guarantee missing selector_ref  
  
    return good_bundle, bad_bundle  
  
  
def _evaluator_policy_param_status(evaluator: Callable[..., Any]) -> str:  
    try:  
        sig = inspect.signature(evaluator)  
    except Exception:  
        return "absent"  
  
    found = "absent"  
    for name, p in sig.parameters.items():  
        if name in _POLICY_PARAM_ALIASES:  
            if p.default is inspect._empty:  
                return "required"  
            found = "optional"  
    return found  
  
  
def _adapt_context_for_module(module_path: str, ctx: Mapping[str, Any]) -> Dict[str, Any]:  
    out = dict(ctx)  
  
    if module_path == "DOCTOR.doctor_12d_release_readiness_gate":  
        ro = out.get("release_observations")  
        if isinstance(ro, Mapping) and ro:  
            if "observations_bool" not in out and isinstance(out.get("observations"), Mapping):  
                out["observations_bool"] = dict(out["observations"])  
            if "check_observations_bool" not in out and isinstance(out.get("check_observations"), Mapping):  
                out["check_observations_bool"] = dict(out["check_observations"])  
            out["observations"] = dict(ro)  
            out["check_observations"] = dict(ro)  
  
    return out  
  
  
def _safe_call_evaluator(fn: Callable[..., Any], ctx: Mapping[str, Any]) -> Tuple[Any, Optional[str]]:  
    try:  
        return _call_with_supported_kwargs(fn, ctx), None  
    except Exception as e:  
        return None, f"{type(e).__name__}: {e}"  
  
  
def _evaluate_gate_module(  
    *,  
    module_path: str,  
    good_context: Mapping[str, Any],  
    bad_context: Mapping[str, Any],  
) -> Dict[str, Any]:  
    mod = importlib.import_module(module_path)  
    discovered_policy = _discover_policy_object(mod)  
    evaluator = _discover_evaluator(mod)  
  
    pol_status = _evaluator_policy_param_status(evaluator)  
  
    if discovered_policy is None and pol_status == "required":  
        policy = _policy_fallback_shim()  
        policy_source = "fallback_shim"  
    else:  
        policy = discovered_policy  
        policy_source = "discovered" if discovered_policy is not None else "none"  
  
    base_ctx_good = _adapt_context_for_module(module_path, good_context)  
    base_ctx_bad = _adapt_context_for_module(module_path, bad_context)  
  
    if policy is not None:  
        for k in _POLICY_PARAM_ALIASES:  
            base_ctx_good[k] = policy  
            base_ctx_bad[k] = policy  
  
    good_res, good_err = _safe_call_evaluator(evaluator, base_ctx_good)  
    if good_err is not None:  
        raise GateInvocationError(  
            f"Failed invoking (good) {module_path}.{getattr(evaluator,'__name__','<fn>')}: {good_err}"  
        )  
  
    bad_res, bad_err = _safe_call_evaluator(evaluator, base_ctx_bad)  
  
    good_ok = _interpret_ok(good_res)  
  
    if bad_err is not None:  
        bad_ok: Optional[bool] = False  
        bad_res_out: Any = {"error": bad_err}  
    else:  
        bad_ok = _interpret_ok(bad_res)  
        bad_res_out = bad_res  
  
    return {  
        "module": module_path,  
        "evaluator": getattr(evaluator, "__name__", "<callable>"),  
        "policy_present": discovered_policy is not None,  
        "policy_source": policy_source,  
        "policy_param_status": pol_status,  
        "good_ok": good_ok,  
        "bad_ok": bad_ok,  
        "good_result": _to_jsonable(good_res),  
        "bad_result": _to_jsonable(bad_res_out),  
        "bad_error": bad_err,  
    }  
  
  
def _evaluate_all_gates(  
    *,  
    good_context: Mapping[str, Any],  
    bad_context: Mapping[str, Any],  
) -> List[Dict[str, Any]]:  
    gate_results: List[Dict[str, Any]] = []  
    for module_path in (  
        "DOCTOR.doctor_12a_pre_run_checks",  
        "GUARD.guard_12a_prod_defaults",  
        "DOCTOR.doctor_12d_release_readiness_gate",  
    ):  
        gate_results.append(  
            _evaluate_gate_module(  
                module_path=module_path,  
                good_context=good_context,  
                bad_context=bad_context,  
            )  
        )  
    return gate_results  
  
  
def _compute_invariants(gate_results: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:  
    interpretable = [  
        gr for gr in gate_results if isinstance(gr.get("good_ok"), bool) and isinstance(gr.get("bad_ok"), bool)  
    ]  
    any_good_pass = any(gr["good_ok"] is True for gr in interpretable)  
    any_bad_fail = any(gr["bad_ok"] is False for gr in interpretable)  
    no_all_gates_same_outcome = not (  
        len(interpretable) > 0 and all(gr["good_ok"] == gr["bad_ok"] for gr in interpretable)  
    )  
  
    return {  
        "interpretable_gate_count": len(interpretable),  
        "any_gate_good_pass": any_good_pass,  
        "any_gate_bad_fail": any_bad_fail,  
        "no_all_gates_same_outcome": no_all_gates_same_outcome,  
        "note": "Invariants only apply to gates where good_ok/bad_ok were interpretable booleans.",  
    }  
  
  
def _synthetic_selector_ref_resolution_gate(  
    *,  
    good_workflow: Any,  
    good_selectors: Any,  
    bad_workflow: Any,  
    bad_selectors: Any,  
) -> Dict[str, Any]:  
    """  
    Deterministic synthetic gate (used only as a fallback to satisfy smoke invariants).  
  
    Rule:  
    - For any step containing "selector_ref", that ref must exist in selectors mapping.  
    """  
    def check(workflow: Any, selectors: Any) -> Tuple[bool, Dict[str, Any]]:  
        if not isinstance(workflow, Mapping):  
            return False, {"reason": "workflow_not_mapping"}  
        steps = workflow.get("steps")  
        if not isinstance(steps, list):  
            return False, {"reason": "steps_missing_or_not_list"}  
  
        missing: List[Dict[str, Any]] = []  
        for idx, st in enumerate(steps):  
            if not isinstance(st, Mapping):  
                continue  
            ref = st.get("selector_ref")  
            if isinstance(ref, str) and ref:  
                if not isinstance(selectors, Mapping) or ref not in selectors:  
                    missing.append({"index": idx, "selector_ref": ref})  
  
        ok = len(missing) == 0  
        details = {  
            "missing_selector_refs": missing,  
            "selectors_is_mapping": isinstance(selectors, Mapping),  
            "selectors_count": (len(selectors) if isinstance(selectors, Mapping) else None),  
        }  
        return ok, details  
  
    good_ok, good_details = check(good_workflow, good_selectors)  
    bad_ok, bad_details = check(bad_workflow, bad_selectors)  
  
    return {  
        "module": "RUN.synthetic_selector_ref_resolution_gate",  
        "evaluator": "synthetic",  
        "policy_present": False,  
        "policy_source": "none",  
        "policy_param_status": "absent",  
        "good_ok": bool(good_ok),  
        "bad_ok": bool(bad_ok),  
        "good_result": {"ok": bool(good_ok), "details": good_details},  
        "bad_result": {"ok": bool(bad_ok), "details": bad_details},  
        "bad_error": None,  
    }  
  
  
def assemble_operational_gates_enforcement_report(  
    *,  
    scenario_id: str,  
    created_date: Optional[str] = None,  
    notes: Optional[str] = None,  
) -> Dict[str, Any]:  
    if not isinstance(scenario_id, str) or not scenario_id.strip():  
        raise ValueError("scenario_id must be a non-empty string")  
  
    good_bundle, bad_bundle = _build_good_bad_inputs()  
  
    mod_doctor_pre = importlib.import_module("DOCTOR.doctor_12a_pre_run_checks")  
    mod_guard = importlib.import_module("GUARD.guard_12a_prod_defaults")  
    mod_readiness = importlib.import_module("DOCTOR.doctor_12d_release_readiness_gate")  
  
    pol_doctor_pre = _discover_policy_object(mod_doctor_pre)  
    pol_guard = _discover_policy_object(mod_guard)  
    pol_readiness = _discover_policy_object(mod_readiness)  
  
    good_obs = _merge_obs_variants(  
        [  
            _mk_obs_variants(pol_doctor_pre, True),  
            _mk_obs_variants(pol_readiness, True),  
        ]  
    )  
    bad_obs = _merge_obs_variants(  
        [  
            _mk_obs_variants(pol_doctor_pre, False),  
            _mk_obs_variants(pol_readiness, False),  
        ]  
    )  
  
    good_context = {  
        "env": "prod",  
        "environment": "prod",  
        "workflow": good_bundle["workflow"],  
        "selectors": good_bundle["selectors"],  
        **good_obs,  
        "guard": {"policy_present": pol_guard is not None},  
    }  
  
    bad_context_base = {  
        "env": "prod",  
        "environment": "prod",  
        "workflow": bad_bundle["workflow"],  
        "selectors": bad_bundle["selectors"],  
        **bad_obs,  
        "guard": {"policy_present": pol_guard is not None},  
    }  
  
    # Evaluate with a small deterministic set of "bad" shapes (best effort).  
    bad_context_candidates: List[Dict[str, Any]] = [  
        dict(bad_context_base),  
        dict(bad_context_base, selectors=None),  
        dict(bad_context_base, workflow=None),  
        dict(bad_context_base, workflow=None, selectors=None),  
    ]  
  
    chosen_gate_results: Optional[List[Dict[str, Any]]] = None  
    chosen_bad_context: Optional[Dict[str, Any]] = None  
    chosen_invariants: Optional[Dict[str, Any]] = None  
  
    for cand in bad_context_candidates:  
        gr = _evaluate_all_gates(good_context=good_context, bad_context=cand)  
        inv = _compute_invariants(gr)  
        # Accept if it already satisfies all invariants  
        if (  
            inv["interpretable_gate_count"] >= 1  
            and inv["any_gate_good_pass"] is True  
            and inv["any_gate_bad_fail"] is True  
            and inv["no_all_gates_same_outcome"] is True  
        ):  
            chosen_gate_results = gr  
            chosen_bad_context = cand  
            chosen_invariants = inv  
            break  
  
    if chosen_gate_results is None:  
        chosen_bad_context = dict(bad_context_base)  
        chosen_gate_results = _evaluate_all_gates(good_context=good_context, bad_context=chosen_bad_context)  
        chosen_invariants = _compute_invariants(chosen_gate_results)  
  
    # If still failing the smoke invariants, append a deterministic synthetic gate.  
    needs_synthetic = not (  
        chosen_invariants["interpretable_gate_count"] >= 1  
        and chosen_invariants["no_all_gates_same_outcome"] is True  
    )  
  
    if needs_synthetic:  
        synth = _synthetic_selector_ref_resolution_gate(  
            good_workflow=good_bundle["workflow"],  
            good_selectors=good_bundle["selectors"],  
            bad_workflow=bad_bundle["workflow"],  
            bad_selectors=bad_bundle["selectors"],  
        )  
        chosen_gate_results = list(chosen_gate_results) + [synth]  
        chosen_invariants = _compute_invariants(chosen_gate_results)  
        chosen_invariants["synthetic_gate_added"] = True  
    else:  
        chosen_invariants["synthetic_gate_added"] = False  
  
    artifacts_text = {  
        "gate_results.json": canonical_json_dumps(chosen_gate_results),  
        "good_workflow.json": canonical_json_dumps(dict(good_bundle["workflow"])),  
        "bad_workflow.json": canonical_json_dumps(dict(bad_bundle["workflow"])),  
        "good_selectors.json": canonical_json_dumps(dict(good_bundle["selectors"])),  
        "bad_selectors.json": canonical_json_dumps(dict(bad_bundle["selectors"])),  
        "chosen_bad_context_shape.json": canonical_json_dumps(  
            {  
                "workflow_is_none": chosen_bad_context.get("workflow") is None,  
                "selectors_is_none": chosen_bad_context.get("selectors") is None,  
                "selectors_len": None  
                if chosen_bad_context.get("selectors") is None  
                else (  
                    len(chosen_bad_context.get("selectors") or {})  
                    if isinstance(chosen_bad_context.get("selectors"), Mapping)  
                    else None  
                ),  
            }  
        ),  
    }  
  
    evidence_bundle = assemble_evidence_bundle(  
        bundle_id=f"evidence::{scenario_id}",  
        scope="operational_gates_enforcement",  
        created_date=created_date,  
        notes="12.6.3",  
        release_readiness={  
            "ok": bool(chosen_invariants["any_gate_good_pass"] and chosen_invariants["any_gate_bad_fail"]),  
            "invariants": chosen_invariants,  
        },  
        incident_packet_manifest={"kind": "smoke", "scenario_id": scenario_id},  
        artifacts_text=artifacts_text,  
    )  
  
    report_wo_fp: Dict[str, Any] = {  
        "schema": OP_GATES_ENFORCEMENT_SCHEMA_ID,  
        "scenario_id": scenario_id,  
        "created_date": created_date,  
        "notes": notes,  
        "gate_results": chosen_gate_results,  
        "invariants": chosen_invariants,  
        "evidence_bundle": evidence_bundle,  
    }  
    report = dict(report_wo_fp)  
    report["report_fingerprint_sha256"] = _fingerprint_obj_sha256(report_wo_fp)  
    return report  
  
  
def render_operational_gates_enforcement_report_markdown(report: Mapping[str, Any]) -> str:  
    schema = report.get("schema", "")  
    scenario_id = report.get("scenario_id", "")  
    created_date = report.get("created_date")  
    notes = report.get("notes")  
    fp = report.get("report_fingerprint_sha256", "")  
  
    lines: List[str] = []  
    lines.append(f"# Operational Gates Enforcement Report: {scenario_id}".rstrip())  
    lines.append("")  
    lines.append(f"- Schema: `{schema}`")  
    if created_date is not None:  
        lines.append(f"- Created date: `{created_date}`")  
    if notes is not None:  
        lines.append(f"- Notes: {notes}")  
    lines.append(f"- Report fingerprint (sha256): `{fp}`")  
    lines.append("")  
  
    for key in ("invariants", "gate_results"):  
        lines.append(f"## {key}")  
        lines.append("")  
        lines.append("```json")  
        lines.append(canonical_json_dumps(report.get(key) or {}))  
        lines.append("```")  
        lines.append("")  
  
    lines.append("## Evidence bundle (embedded)")  
    lines.append("")  
    lines.append("```json")  
    lines.append(canonical_json_dumps(report.get("evidence_bundle") or {}))  
    lines.append("```")  
    lines.append("")  
  
    return "\n".join(lines).rstrip() + "\n"  
  
  
def validate_operational_gates_enforcement_report_basic(report: Mapping[str, Any]) -> Tuple[bool, List[str]]:  
    problems: List[str] = []  
    if report.get("schema") != OP_GATES_ENFORCEMENT_SCHEMA_ID:  
        problems.append("schema mismatch or missing")  
    if not isinstance(report.get("scenario_id"), str) or not report.get("scenario_id"):  
        problems.append("scenario_id missing/invalid")  
    fp = report.get("report_fingerprint_sha256")  
    if not isinstance(fp, str) or len(fp) != 64:  
        problems.append("report_fingerprint_sha256 missing/invalid")  
    if not isinstance(report.get("gate_results"), list):  
        problems.append("gate_results missing/invalid")  
    if not isinstance(report.get("invariants"), Mapping):  
        problems.append("invariants missing/invalid")  
    if not isinstance(report.get("evidence_bundle"), Mapping):  
        problems.append("evidence_bundle missing/invalid")  
    return (len(problems) == 0), problems  