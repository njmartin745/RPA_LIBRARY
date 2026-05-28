import json  
import sys   
from pathlib import Path  
  
PROJECT_ROOT = Path(__file__).resolve().parents[1]  
if str(PROJECT_ROOT) not in sys.path:  
    sys.path.insert(0, str(PROJECT_ROOT)) 
  
from BUILD.build_2c_full_bundle import build_from_nl  
  
  
def main() -> None:  
    out_dir = Path(".dev_tmp/build_2c_smoke")  
    out_dir.mkdir(parents=True, exist_ok=True)  
  
    # Mock submodules to avoid depending on local BUILD-1A/1C implementations in smoke.  
    def spec_fn(description: str, cfg=None):  
        return {  
            "description": description,  
            "steps": [  
                {"action": "open", "url": "https://example.com"},  
                {"action": "log", "message": "verify page title (TODO: add VAL step in spec)"},  
            ],  
            "todos": ["add title verification step via VAL module"],  
        }  
  
    def optimize_fn(spec: dict, cfg=None):  
        # No real optimization; just return a structured envelope  
        return {  
            "spec": spec,  
            "steps": spec.get("steps", []),  
            "optimizations": ["normalized url to https://example.com"],  
            "todos": spec.get("todos", []),  
        }  
  
    def workflow_fn(optimized: dict, output_dir: str = ".", cfg=None):  
        p = Path(cfg.get("workflow_path", Path(output_dir) / "WORKFLOWS" / "smoke.json"))  
        p.parent.mkdir(parents=True, exist_ok=True)  
        # minimal workflow json for file existence  
        wf = {"name": "WF_SMOKE_BUILD_2C", "steps": optimized.get("steps", [])}  
        p.write_text(json.dumps(wf, indent=2), encoding="utf-8")  
        return {"workflow_path": str(p)}  
  
    def smoke_fn(workflow_path: str, output_dir: str = ".", cfg=None):  
        p = Path(cfg.get("smoke_test_path", Path(output_dir) / "dev" / "dev_smoke_smoke.py"))  
        p.parent.mkdir(parents=True, exist_ok=True)  
        p.write_text(  
            "def main():\n"  
            f"    print('SMOKE stub for {workflow_path}')\n"  
            "    print('PASS')\n"  
            "\n"  
            "if __name__ == '__main__':\n"  
            "    main()\n",  
            encoding="utf-8",  
        )  
        return {"smoke_test_path": str(p)}  
  
    out = build_from_nl(  
        "open example.com and verify page title",  
        output_dir=out_dir,  
        cfg={  
            "spec_fn": spec_fn,  
            "optimize_fn": optimize_fn,  
            "workflow_fn": workflow_fn,  
            "smoke_fn": smoke_fn,  
        },  
    )  
  
    assert out["ok"] is True  
    assert out["workflow_path"] and Path(out["workflow_path"]).exists()  
    assert out["smoke_test_path"] and Path(out["smoke_test_path"]).exists()  
  
    print("dev_smoke_build_2c.py: PASS")  
    print(json.dumps(out, indent=2))  
  
  
if __name__ == "__main__":  
    main()  