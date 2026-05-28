"""  
Deterministic canonicalization / serialization utilities.  
  
Single responsibility:  
- Convert common Python structures into a canonical JSON-compatible form.  
- Provide stable JSON dumps and stable SHA-256 fingerprints.  
  
This is useful for ensuring workflow/selector/bundle generation is deterministic  
(given the same logical inputs, the produced artifacts can be compared reliably).  
"""  
  
from __future__ import annotations  
  
import base64  
import dataclasses  
import datetime as _dt  
import hashlib  
import json  
import math  
from pathlib import Path  
from typing import Any, Mapping, Sequence  
  
__all__ = [  
    "canonicalize_for_json",  
    "stable_json_dumps",  
    "stable_fingerprint_sha256",  
    "dev_smoke",  
]  
  
  
def _raise_on_nonfinite_float(value: float) -> float:  
    if math.isnan(value) or math.isinf(value):  
        raise ValueError("Non-finite floats (NaN/Inf) are not allowed for deterministic JSON.")  
    return value  
  
  
def canonicalize_for_json(obj: Any) -> Any:  
    """  
    Canonicalize an object into a JSON-compatible structure deterministically.  
  
    Rules:  
    - dict-like: keys coerced to str, entries sorted by key  
    - list/tuple: order preserved, elements canonicalized  
    - set/frozenset: converted to a sorted list (sorted by canonical JSON)  
    - dataclass: converted via dataclasses.asdict then canonicalized  
    - Path: converted to str  
    - datetime/date: converted to ISO format  
    - bytes: encoded to base64 with a tagged wrapper for round-trippable identity  
  
    Unsupported types raise TypeError to avoid hidden non-determinism.  
    """  
    if obj is None or isinstance(obj, (str, bool, int)):  
        return obj  
  
    if isinstance(obj, float):  
        return _raise_on_nonfinite_float(obj)  
  
    if dataclasses.is_dataclass(obj):  
        return canonicalize_for_json(dataclasses.asdict(obj))  
  
    if isinstance(obj, (Path,)):  
        return str(obj)  
  
    if isinstance(obj, (_dt.datetime, _dt.date)):  
        # ISO format is deterministic; no timezone conversion is performed here.  
        return obj.isoformat()  
  
    if isinstance(obj, (bytes, bytearray)):  
        b = bytes(obj)  
        return {"__bytes_b64__": base64.b64encode(b).decode("ascii")}  
  
    if isinstance(obj, Mapping):  
        items = []  
        for k, v in obj.items():  
            ks = str(k)  
            items.append((ks, canonicalize_for_json(v)))  
        items.sort(key=lambda kv: kv[0])  
        return {k: v for k, v in items}  
  
    if isinstance(obj, (list, tuple)):  
        return [canonicalize_for_json(x) for x in obj]  
  
    if isinstance(obj, (set, frozenset)):  
        canon_items = [canonicalize_for_json(x) for x in obj]  
        canon_items.sort(key=_stable_sort_key_for_jsonish)  
        return canon_items  
  
    raise TypeError(f"Unsupported type for deterministic JSON canonicalization: {type(obj)!r}")  
  
  
def _stable_sort_key_for_jsonish(value: Any) -> str:  
    """  
    Deterministic sort key for already-canonicalized JSON-ish values.  
    """  
    return json.dumps(  
        value,  
        ensure_ascii=False,  
        sort_keys=True,  
        separators=(",", ":"),  
    )  
  
  
def stable_json_dumps(obj: Any, *, indent: int | None = None) -> str:  
    """  
    Deterministically JSON-serialize `obj` by canonicalizing then dumping with stable settings.  
    """  
    canon = canonicalize_for_json(obj)  
    return json.dumps(  
        canon,  
        ensure_ascii=False,  
        sort_keys=True,  
        separators=(",", ":"),  
        indent=indent,  
    )  
  
  
def stable_fingerprint_sha256(obj: Any) -> str:  
    """  
    Deterministic SHA-256 fingerprint of an object by hashing its canonical JSON form.  
    """  
    s = stable_json_dumps(obj, indent=None)  
    return hashlib.sha256(s.encode("utf-8")).hexdigest()  
  
  
def dev_smoke() -> None:  
    """  
    Minimal deterministic behavior checks.  
    """  
    workflow_a = {  
        "workflow_name": "determinism_smoke",  
        "steps": [  
            {"action": "open", "url": "https://example.com"},  
            {"action": "wait_for_selector", "selector_ref": "example.title"},  
            {"action": "click_selector", "selector_ref": "example.button"},  
            {  
                "action": "type_selector_secret",  
                "selector_ref": "example.password",  
                "secret_ref": "pw",  
            },  
            {"action": "log", "message": "done"},  
        ],  
        "meta": {"tags": {"b", "a", "c"}},  # set canonicalized deterministically  
    }  
  
    # Same logical data, different key insertion orders + different set insertion patterns  
    workflow_b = {  
        "meta": {"tags": {"c", "a", "b"}},  
        "steps": [  
            {"url": "https://example.com", "action": "open"},  
            {"selector_ref": "example.title", "action": "wait_for_selector"},  
            {"selector_ref": "example.button", "action": "click_selector"},  
            {  
                "secret_ref": "pw",  
                "selector_ref": "example.password",  
                "action": "type_selector_secret",  
            },  
            {"message": "done", "action": "log"},  
        ],  
        "workflow_name": "determinism_smoke",  
    }  
  
    j1 = stable_json_dumps(workflow_a)  
    j2 = stable_json_dumps(workflow_b)  
    if j1 != j2:  
        raise AssertionError("stable_json_dumps is not deterministic for equivalent structures.")  
  
    f1 = stable_fingerprint_sha256(workflow_a)  
    f2 = stable_fingerprint_sha256(workflow_b)  
    if f1 != f2:  
        raise AssertionError("stable_fingerprint_sha256 is not deterministic for equivalent structures.")  
  
    # Repeat calls should be stable  
    for _ in range(3):  
        if stable_json_dumps(workflow_a) != j1:  
            raise AssertionError("stable_json_dumps changed across repeated calls.")  
        if stable_fingerprint_sha256(workflow_a) != f1:  
            raise AssertionError("stable_fingerprint_sha256 changed across repeated calls.")  
  
  
if __name__ == "__main__":  
    dev_smoke()  
    print("DEV_SMOKE_OK: BUILD.build_2d_determinism")  