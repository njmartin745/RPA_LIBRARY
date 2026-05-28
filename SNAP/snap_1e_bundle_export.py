from __future__ import annotations  
  
from pathlib import Path  
from typing import Any, Dict, Mapping, Optional, Union  
  
from SNAP.snap_1c_capture_bundle import validate_capture_bundle  
from SNAP.snap_1d_bundle_io import save_capture_bundle_json  
  
__all__ = [  
    "export_capture_bundle_assets",  
    "dev_smoke",  
]  
  
  
def export_capture_bundle_assets(  
    bundle: Mapping[str, Any],  
    out_dir: Union[str, Path],  
    *,  
    repo_root: Optional[Path] = None,  
    validate: bool = True,  
    workflow_filename: str = "workflow.json",  
    selector_pack_filename: str = "selector_pack.json",  
    bundle_filename: str = "capture_bundle.json",  
) -> Dict[str, Path]:  
    """  
    Export deterministic JSON assets from a capture bundle:  
      - capture_bundle.json (entire bundle)  
      - workflow.json (bundle["workflow"])  
      - selector_pack.json (bundle["selector_pack"])  
  
    Returns paths:  
      {"bundle": Path, "workflow": Path, "selector_pack": Path}  
    """  
    if validate:  
        validate_capture_bundle(  
            bundle,  
            repo_root=repo_root,  
            require_registry_compat=(repo_root is not None),  
        )  
  
    out = Path(out_dir)  
    out.mkdir(parents=True, exist_ok=True)  
  
    # 1) Whole bundle  
    bundle_path = save_capture_bundle_json(out / bundle_filename, bundle)  
  
    # 2) Workflow only (stable minimal shape: {"steps": [...]})  
    wf = bundle.get("workflow")  
    if not isinstance(wf, Mapping):  
        raise ValueError("bundle.workflow must be a mapping")  
    workflow_path = save_capture_bundle_json(out / workflow_filename, wf)  
  
    # 3) Selector pack only  
    sp = bundle.get("selector_pack")  
    if not isinstance(sp, Mapping):  
        raise ValueError("bundle.selector_pack must be a mapping")  
    selector_pack_path = save_capture_bundle_json(out / selector_pack_filename, sp)  
  
    return {"bundle": bundle_path, "workflow": workflow_path, "selector_pack": selector_pack_path}  
  
  
def dev_smoke() -> None:  
    # Local-only: just validate shape and write files; no repo-root registry check here.  
    b = {  
        "schema_id": "CAPTURE_BUNDLE_1A",  
        "name": "x",  
        "workflow": {"steps": []},  
        "selector_pack": {"schema_id": "SELECTOR_PACK_1A", "name": "x", "selectors": {}},  
    }  
    import tempfile  
  
    with tempfile.TemporaryDirectory() as td:  
        paths = export_capture_bundle_assets(b, td, validate=False)  
        assert paths["bundle"].exists()  
        assert paths["workflow"].exists()  
        assert paths["selector_pack"].exists()  