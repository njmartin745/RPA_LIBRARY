from __future__ import annotations  
  
import json  
from pathlib import Path  
from typing import Any, Dict, Mapping, Union  
  
__all__ = [  
    "capture_bundle_to_json",  
    "capture_bundle_from_json",  
    "save_capture_bundle_json",  
    "load_capture_bundle_json",  
    "dev_smoke",  
]  
  
  
def capture_bundle_to_json(  
    bundle: Mapping[str, Any],  
    *,  
    indent: int = 2,  
    sort_keys: bool = True,  
) -> str:  
    """  
    Deterministically serialize a capture bundle to JSON text.  
    """  
    text = json.dumps(  
        bundle,  
        ensure_ascii=False,  
        indent=indent,  
        sort_keys=sort_keys,  
    )  
    if not text.endswith("\n"):  
        text += "\n"  
    return text  
  
  
def capture_bundle_from_json(text: str) -> Dict[str, Any]:  
    """  
    Parse JSON text into a capture bundle dict.  
    """  
    obj = json.loads(text)  
    if not isinstance(obj, dict):  
        raise ValueError("Capture bundle JSON must decode to an object/dict.")  
    return obj  
  
  
def save_capture_bundle_json(  
    path: Union[str, Path],  
    bundle: Mapping[str, Any],  
    *,  
    indent: int = 2,  
    sort_keys: bool = True,  
    encoding: str = "utf-8",  
) -> Path:  
    """  
    Save a capture bundle to disk as deterministic JSON.  
    Creates parent directories if needed.  
    """  
    p = Path(path)  
    p.parent.mkdir(parents=True, exist_ok=True)  
    text = capture_bundle_to_json(bundle, indent=indent, sort_keys=sort_keys)  
    p.write_text(text, encoding=encoding)  
    return p  
  
  
def load_capture_bundle_json(  
    path: Union[str, Path],  
    *,  
    encoding: str = "utf-8",  
) -> Dict[str, Any]:  
    """  
    Load a capture bundle JSON file from disk.  
    """  
    p = Path(path)  
    text = p.read_text(encoding=encoding)  
    return capture_bundle_from_json(text)  
  
  
def dev_smoke() -> None:  
    b = {"schema_id": "CAPTURE_BUNDLE_1A", "name": "x", "workflow": {"steps": []}, "selector_pack": {}}  
    s = capture_bundle_to_json(b)  
    assert s.endswith("\n")  
    b2 = capture_bundle_from_json(s)  
    assert b2 == b  