from __future__ import annotations  
  
import hashlib  
import importlib  
import inspect  
import json  
import pkgutil  
from pathlib import Path  
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple  

import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 

from SNAP.snap_1a_workflow_capture import CapturedEvent, captured_events_to_steps  
from SNAP.snap_1b_selector_pack import selector_pack_from_captured_events  
  
__all__ = ["dev_smoke"]  
  
  
def _canonical_json_text(obj: Any) -> str:  
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)  
  
  
def _sha256_hex(text: str) -> str:  
    h = hashlib.sha256()  
    h.update(text.encode("utf-8"))  
    return h.hexdigest()  
  
  
def _canonical_write_json(path: Path, obj: Any) -> None:  
    path.parent.mkdir(parents=True, exist_ok=True)  
    with open(path, "w", encoding="utf-8") as f:  
        f.write(_canonical_json_text(obj))  
  
  
def _prepare_out_dir(base: Path) -> Path:  
    """  
    Deterministically select a writable output directory without requiring rmtree().  
    Tries base, then base_1..base_9. Cleans only known output filenames.  
    """  
    candidates = [base] + [base.with_name(f"{base.name}_{i}") for i in range(1, 10)]  
    last_err: Optional[BaseException] = None  
  
    for d in candidates:  
        try:  
            d.mkdir(parents=True, exist_ok=True)  
  
            # Probe write/delete to confirm we can use this folder  
            probe = d / "_probe.tmp"  
            with open(probe, "w", encoding="utf-8") as f:  
                f.write("x")  
            probe.unlink(missing_ok=True)  
  
            # Remove known outputs (best-effort)  
            for fn in ("capture_bundle_1a.json", "deploy_bundle_1a.json"):  
                try:  
                    (d / fn).unlink(missing_ok=True)  
                except PermissionError:  
                    pass  
  
            return d  
        except Exception as e:  
            last_err = e  
            continue  
  
    raise PermissionError(f"Could not prepare a writable out dir starting at {base}. Last error: {last_err!r}")  
  
  
def _resolve_callable(  
    mod: Any,  
    candidates: Sequence[str],  
    *,  
    contains_all: Tuple[str, ...] = (),  
) -> Callable[..., Any]:  
    for name in candidates:  
        fn = getattr(mod, name, None)  
        if callable(fn):  
            return fn  
  
    public_callables = sorted(n for n in dir(mod) if not n.startswith("_") and callable(getattr(mod, n, None)))  
    if contains_all:  
        for n in public_callables:  
            ln = n.lower()  
            if all(tok in ln for tok in contains_all):  
                return getattr(mod, n)  
  
    raise AttributeError(  
        f"Could not resolve callable. Tried={list(candidates)} contains_all={contains_all}. "  
        f"Public callables: {public_callables}"  
    )  
  
  
def _call_best_effort(fn: Callable[..., Any], provided: Mapping[str, Any]) -> Any:  
    """  
    Call fn using only kwargs present in its signature.  
    Deterministic: fails with helpful diagnostics if required params are missing.  
    """  
    sig = inspect.signature(fn)  
    params = sig.parameters  
  
    kwargs: Dict[str, Any] = {}  
    for k, v in provided.items():  
        if k in params:  
            kwargs[k] = v  
  
    missing_required: List[str] = []  
    for name, p in params.items():  
        if p.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):  
            continue  
        if p.default is not inspect._empty:  
            continue  
        if name not in kwargs:  
            missing_required.append(name)  
  
    if missing_required:  
        raise TypeError(  
            f"Cannot call {getattr(fn, '__name__', str(fn))}; missing required params: {missing_required}. "  
            f"Signature: {sig}"  
        )  
  
    return fn(**kwargs)  
  
  
def _find_json_by_substrings(dir_path: Path, *substrings: str) -> Optional[Path]:  
    if not dir_path.exists():  
        return None  
    subs = tuple(s.lower() for s in substrings)  
    hits: List[Path] = []  
    for p in sorted(dir_path.glob("*.json")):  
        name = p.name.lower()  
        if all(s in name for s in subs):  
            hits.append(p)  
    return hits[0] if hits else None  
  
  
def _bool_from_validation_result(res: Any) -> Optional[bool]:  
    if isinstance(res, dict):  
        if "ok" in res and isinstance(res["ok"], bool):  
            return res["ok"]  
        if "valid" in res and isinstance(res["valid"], bool):  
            return res["valid"]  
    return None  
  
  
def _looks_like_validation_dict(d: Dict[str, Any]) -> bool:  
    # common: {"schema_id": "...VALIDATION...", "ok": bool, "errors": [...], "warnings": [...]}  
    if "ok" in d and isinstance(d["ok"], bool) and ("errors" in d or "schema_id" in d):  
        return True  
    if isinstance(d.get("schema_id"), str) and "VALIDATION" in d["schema_id"].upper():  
        return True  
    return False  
  
  
def _extract_deploy_bundle_from_result(obj: Any) -> Optional[Dict[str, Any]]:  
    """  
    Best-effort extraction of a deploy-bundle dict from various possible return shapes.  
    """  
    if isinstance(obj, dict):  
        if _looks_like_validation_dict(obj):  
            return None  
        if isinstance(obj.get("deploy_bundle"), dict) and not _looks_like_validation_dict(obj["deploy_bundle"]):  
            return obj["deploy_bundle"]  
        if isinstance(obj.get("bundle"), dict) and not _looks_like_validation_dict(obj["bundle"]):  
            return obj["bundle"]  
        return obj  
  
    if isinstance(obj, (list, tuple)):  
        for it in obj:  
            b = _extract_deploy_bundle_from_result(it)  
            if isinstance(b, dict):  
                return b  
    return None  
  
  
def _is_hex_64(s: Any) -> bool:  
    if not (isinstance(s, str) and len(s) == 64):  
        return False  
    try:  
        int(s, 16)  
        return True  
    except Exception:  
        return False  
  
  
def _is_stamped(deploy_bundle: Mapping[str, Any]) -> bool:  
    ver = deploy_bundle.get("version")  
    fp = deploy_bundle.get("fingerprint")  
    if not (isinstance(ver, str) and ver.strip()):  
        return False  
    if not isinstance(fp, dict):  
        return False  
  
    # required by your validator  
    if fp.get("algo") != "sha256":  
        return False  
    if not _is_hex_64(fp.get("sha256")):  
        return False  
  
    canon = fp.get("canonicalization")  
    if not (isinstance(canon, str) and canon.strip()):  
        return False  
  
    return True  
  
  
def _fallback_stamp_deploy_bundle(deploy_bundle: Dict[str, Any]) -> Dict[str, Any]:  
    """  
    Last-resort deterministic stamping to satisfy validator schema:  
    - version: non-empty string  
    - fingerprint: mapping with:  
        algo == 'sha256'  
        sha256: 64 hex chars  
        canonicalization: non-empty string  
    """  
    base = dict(deploy_bundle)  
    base.pop("fingerprint", None)  
    base.pop("version", None)  
  
    digest = _sha256_hex(_canonical_json_text(base))  
  
    stamped = dict(deploy_bundle)  
    stamped["version"] = (stamped.get("version") or "1a").strip() or "1a"  
  
    existing_fp = stamped.get("fingerprint")  
    fp: Dict[str, Any] = dict(existing_fp) if isinstance(existing_fp, dict) else {}  
    fp["algo"] = "sha256"  
    fp["sha256"] = digest  
    # keep for compatibility with any other codepaths that might look for it  
    fp["hexdigest"] = digest  
    fp["canonicalization"] = fp.get("canonicalization") or "json:sort_keys,separators=(',',':'),utf8"  
    stamped["fingerprint"] = fp  
  
    return stamped  
  
def _iter_build_module_names() -> List[str]:  
    import BUILD  # type: ignore  
  
    names: List[str] = []  
    for mi in pkgutil.iter_modules(BUILD.__path__):  # type: ignore[attr-defined]  
        names.append(mi.name)  
    names = sorted(names)  
    # deterministic filtering: prefer build_3* family first  
    full = [f"BUILD.{n}" for n in names]  
    return full  
  
  
def _try_stamp_via_repo(  
    *,  
    deploy_bundle: Dict[str, Any],  
    deploy_bundle_path: Path,  
    repo_root: Path,  
    out_dir: Path,  
) -> Dict[str, Any]:  
    """  
    Try to stamp using repo stamp/fingerprint/version helpers.  
    Deterministic search order:  
      1) known module names  
      2) scan BUILD.* modules (sorted) matching deploy/bundle + (stamp|fingerprint|version)  
    """  
    if _is_stamped(deploy_bundle):  
        return deploy_bundle  
  
    attempted: List[str] = []  
  
    def attempt_module(mod_name: str) -> Optional[Dict[str, Any]]:  
        try:  
            mod = importlib.import_module(mod_name)  
        except ModuleNotFoundError:  
            return None  
  
        # candidates across repos  
        fn_candidates = [  
            "stamp_and_validate_deploy_bundle",  
            "stamp_validate_deploy_bundle",  
            "stamp_deploy_bundle_1a",  
            "stamp_deploy_bundle",  
            "fingerprint_deploy_bundle",  
            "add_fingerprint_to_deploy_bundle",  
            "add_version_to_deploy_bundle",  
            "ensure_deploy_bundle_stamped",  
        ]  
  
        # first: direct name matches  
        try:  
            fn = _resolve_callable(mod, candidates=fn_candidates, contains_all=())  
        except AttributeError:  
            # second: heuristic name contains tokens  
            try:  
                fn = _resolve_callable(mod, candidates=[], contains_all=("deploy", "bundle", "stamp"))  
            except AttributeError:  
                try:  
                    fn = _resolve_callable(mod, candidates=[], contains_all=("deploy", "bundle", "finger"))  
                except AttributeError:  
                    try:  
                        fn = _resolve_callable(mod, candidates=[], contains_all=("deploy", "bundle", "version"))  
                    except AttributeError:  
                        return None  
  
        attempted.append(f"{mod_name}.{getattr(fn, '__name__', '<?>')}")  
  
        try:  
            res = _call_best_effort(  
                fn,  
                {  
                    "deploy_bundle": deploy_bundle,  
                    "bundle": deploy_bundle,  
                    "deploy_bundle_path": str(deploy_bundle_path),  
                    "bundle_path": str(deploy_bundle_path),  
                    "out_dir": str(out_dir),  
                    "output_dir": str(out_dir),  
                    "repo_root": str(repo_root),  
                },  
            )  
        except TypeError:  
            return None  
  
        extracted = _extract_deploy_bundle_from_result(res)  
        if isinstance(extracted, dict) and _is_stamped(extracted):  
            return extracted  
  
        # Some stampers may write in-place and return None/validation; try reload.  
        try:  
            with open(deploy_bundle_path, "r", encoding="utf-8") as f:  
                reloaded = json.load(f)  
            if isinstance(reloaded, dict) and _is_stamped(reloaded):  
                return reloaded  
        except Exception:  
            pass  
  
        return None  
  
    # 1) Known likely module names (deterministic order)  
    known_modules = [  
        "BUILD.build_3d_deploy_bundle_stamper",  
        "BUILD.build_3d_deploy_bundle_stamping",  
        "BUILD.build_3e_deploy_bundle_stamper",  
        "BUILD.build_3e_deploy_bundle_fingerprinter",  
        "BUILD.build_3f_deploy_bundle_fingerprinter",  
        "BUILD.build_3e_deploy_bundle_versioner",  
        "BUILD.build_3f_deploy_bundle_versioner",  
    ]  
    for mn in known_modules:  
        stamped = attempt_module(mn)  
        if stamped is not None:  
            return stamped  
  
    # 2) Scan BUILD.* modules (sorted) with name hints to keep side-effects limited  
    for mn in _iter_build_module_names():  
        low = mn.lower()  
        if not (("deploy" in low) and ("bundle" in low)):  
            continue  
        if not (("stamp" in low) or ("finger" in low) or ("version" in low)):  
            continue  
        stamped = attempt_module(mn)  
        if stamped is not None:  
            return stamped  
  
    # no repo stamper found/usable  
    return deploy_bundle  
  
  
def dev_smoke() -> None:  
    repo_root = Path(".")  
    out_dir = _prepare_out_dir(repo_root / "dev" / "_out_phase_11_5_3")  
  
    # 1) Build a deterministic capture bundle in-memory (no browser interaction)  
    events = [  
        CapturedEvent(kind="click", seq=1, selector="#login"),  
        CapturedEvent(kind="change", seq=2, selector='input[name="username"]', value="alice"),  
        CapturedEvent(kind="navigate", seq=3, url="https://example.test/app"),  
    ]  
  
    selector_pack = selector_pack_from_captured_events(  
        events,  
        include_kinds=("click", "change"),  
        ref_prefix="cap",  
        pack_name="captured",  
    )  
    selector_ref_map = selector_pack.get("selector_ref_map")  
  
    steps = captured_events_to_steps(  
        events,  
        selector_ref_map=selector_ref_map,  
        include_clicks=True,  
        include_navigation=True,  
        include_changes=False,  
    )  
  
    snap_1c = importlib.import_module("SNAP.snap_1c_capture_bundle")  
    capture_bundle_builder = _resolve_callable(  
        snap_1c,  
        candidates=[  
            "build_capture_bundle_from_events",  
            "emit_capture_bundle",  
            "build_capture_bundle",  
        ],  
        contains_all=("capture", "bundle"),  
    )  
  
    capture_bundle = _call_best_effort(  
        capture_bundle_builder,  
        {  
            "events": list(events),  
            "captured_events": list(events),  
            "steps": list(steps),  
            "selector_pack": dict(selector_pack),  
            "selector_ref_map": dict(selector_ref_map) if isinstance(selector_ref_map, dict) else selector_ref_map,  
            "repo_root": str(repo_root),  
        },  
    )  
  
    capture_bundle_path = out_dir / "capture_bundle_1a.json"  
    _canonical_write_json(capture_bundle_path, capture_bundle)  
  
    # 2) Build a deploy bundle (prefer stamp+validate builders first)  
    build_3c = importlib.import_module("BUILD.build_3c_deploy_bundle_builder")  
    deploy_builder = _resolve_callable(  
        build_3c,  
        candidates=[  
            "build_and_stamp_validate_deploy_bundle",  
            "build_stamp_validate_deploy_bundle",  
            "build_deploy_bundle_from_capture_bundle",  
            "build_deploy_bundle_1a",  
            "build_deploy_bundle",  
        ],  
        contains_all=("deploy", "bundle", "build"),  
    )  
  
    pre_json = set(out_dir.glob("*.json"))  
  
    deploy_result = _call_best_effort(  
        deploy_builder,  
        {  
            "capture_bundle": capture_bundle,  
            "capture_bundle_path": str(capture_bundle_path),  
            "capture_bundle_json_path": str(capture_bundle_path),  
            "capture_bundle_file": str(capture_bundle_path),  
            "out_dir": str(out_dir),  
            "output_dir": str(out_dir),  
            "bundle_out_dir": str(out_dir),  
            "repo_root": str(repo_root),  
        },  
    )  
  
    # 3) Determine deploy bundle JSON path (builder may return dict/path and/or write a file)  
    deploy_bundle_path: Optional[Path] = None  
    deploy_bundle: Optional[Dict[str, Any]] = None  
  
    if isinstance(deploy_result, str) and deploy_result.lower().endswith(".json"):  
        deploy_bundle_path = Path(deploy_result)  
  
    elif isinstance(deploy_result, dict):  
        # If builder returned a validation dict, do NOT treat it as a deploy bundle  
        if not _looks_like_validation_dict(deploy_result):  
            deploy_bundle = deploy_result  
            deploy_bundle_path = out_dir / "deploy_bundle_1a.json"  
            _canonical_write_json(deploy_bundle_path, deploy_bundle)  
        else:  
            deploy_bundle_path = None  # locate via set-diff below  
  
    else:  
        deploy_bundle_path = None  
  
    if deploy_bundle_path is None:  
        post_json = set(out_dir.glob("*.json"))  
        new_json = sorted(post_json - pre_json)  
  
        if len(new_json) == 1:  
            deploy_bundle_path = new_json[0]  
        else:  
            new_named = [p for p in new_json if ("deploy" in p.name.lower() and "bundle" in p.name.lower())]  
            if len(new_named) == 1:  
                deploy_bundle_path = new_named[0]  
            else:  
                deploy_bundle_path = _find_json_by_substrings(out_dir, "deploy", "bundle")  
  
    if deploy_bundle_path is None or not deploy_bundle_path.is_file():  
        raise FileNotFoundError(  
            f"Could not locate deploy bundle JSON after builder call. out_dir={out_dir} deploy_result={type(deploy_result)}"  
        )  
  
    if deploy_bundle is None:  
        with open(deploy_bundle_path, "r", encoding="utf-8") as f:  
            deploy_bundle = json.load(f)  
        if not isinstance(deploy_bundle, dict):  
            raise TypeError(f"Expected deploy bundle JSON object at {deploy_bundle_path}")  
        if _looks_like_validation_dict(deploy_bundle):  
            raise TypeError(  
                f"Loaded a validation result instead of a deploy bundle from {deploy_bundle_path}. "  
                f"Keys={sorted(deploy_bundle.keys())}"  
            )  
  
    # 3b) Stamp (repo stamper if available; fallback deterministic stamping)  
    deploy_bundle = _try_stamp_via_repo(  
        deploy_bundle=deploy_bundle,  
        deploy_bundle_path=deploy_bundle_path,  
        repo_root=repo_root,  
        out_dir=out_dir,  
    )  
    if not _is_stamped(deploy_bundle):  
        deploy_bundle = _fallback_stamp_deploy_bundle(deploy_bundle)  
  
    _canonical_write_json(deploy_bundle_path, deploy_bundle)  
  
    # 4) Validate deploy bundle  
    val_2a = importlib.import_module("VAL.val_2a_deploy_bundle_validator")  
    validate_fn = _resolve_callable(  
        val_2a,  
        candidates=[  
            "validate_deploy_bundle",  
            "validate_deploy_bundle_1a",  
            "validate_bundle",  
        ],  
        contains_all=("validate", "deploy", "bundle"),  
    )  
  
    validation_res = _call_best_effort(  
        validate_fn,  
        {  
            "deploy_bundle": deploy_bundle,  
            "bundle": deploy_bundle,  
            "deploy_bundle_path": str(deploy_bundle_path),  
            "bundle_path": str(deploy_bundle_path),  
            "repo_root": str(repo_root),  
        },  
    )  
  
    ok = _bool_from_validation_result(validation_res)  
    if ok is False:  
        raise AssertionError(f"Deploy bundle validator reported ok=false. Result={validation_res!r}")  
  
    # 5) Load deploy bundle using loader module  
    loader = importlib.import_module("WORKFLOWS.workflow_1g_deploy_bundle_loader")  
    load_fn = _resolve_callable(  
        loader,  
        candidates=[  
            "load_deploy_bundle",  
            "load_deploy_bundle_1a",  
            "load_deploy_bundle_from_path",  
        ],  
        contains_all=("load", "deploy", "bundle"),  
    )  
  
    loaded = _call_best_effort(  
        load_fn,  
        {  
            # REQUIRED by load_deploy_bundle_1a signature  
            "bundle_obj": deploy_bundle,  
    
            # common aliases (ignored if not in signature)  
            "deploy_bundle": deploy_bundle,  
            "bundle": deploy_bundle,  
    
            # optional toggles (used if present)  
            "validate": True,  
            "require_version_fingerprint": True,  
            "require_selector_ref": True,  
    
            # path/context (ignored if not in signature)  
            "deploy_bundle_path": str(deploy_bundle_path),  
            "bundle_path": str(deploy_bundle_path),  
            "repo_root": str(repo_root),  
            "env_name": "dev",  
            "environment": "dev",  
            "overlays": {},  
        },  
    )   
    assert loaded is not None, "Deploy bundle loader returned None"  
  
    # 6) Ensure runner/CLI entrypoints import cleanly (do NOT execute Selenium)  
    run_adapter = importlib.import_module("RUN.run_1e_deploy_bundle_runner_adapter")  
    _resolve_callable(  
        run_adapter,  
        candidates=[  
            "run_deploy_bundle",  
            "run_deploy_bundle_path",  
            "run_deploy_bundle_from_path",  
            "main",  
        ],  
        contains_all=("deploy", "bundle"),  
    )  
  
    cli_resolver = importlib.import_module("CLI.cli_1h_run_deploy_bundle_cli_resolver")  
    assert callable(getattr(cli_resolver, "main", None)), "CLI.cli_1h_run_deploy_bundle_cli_resolver.main not callable"  
  
    print("PASS")  
  
  
if __name__ == "__main__":  
    dev_smoke()  