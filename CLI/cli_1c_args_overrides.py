"""  
CLI-1C — CLI Flags + Overrides  
  
Adds argparse flags and a pure function to apply runtime overrides onto an existing  
config dict (typically produced by CLI-1B load_config()).  
  
Integration snippet (CLI-1A style)  
----------------------------------  
    from CLI.cli_1b_config_loader import load_config  
    from CLI.cli_1c_args_overrides import build_arg_parser, apply_overrides  
  
    parser = build_arg_parser()  
    args = parser.parse_args()  
  
    cfg = {}  
    if args.config:  
        cfg = load_config(args.config)  
  
    cfg = apply_overrides(cfg, args)  
  
Rules  
-----  
- Flags take precedence over config values.  
- apply_overrides does NOT mutate the incoming cfg; it returns a new dict.  
"""  
  
from __future__ import annotations  
  
import argparse  
from typing import Any, Dict, Optional  
  
__all__ = ["build_arg_parser", "apply_overrides"]  
  
  
def _str2bool(v: str) -> bool:  
    s = v.strip().lower()  
    if s in ("true", "1", "yes", "y", "on"):  
        return True  
    if s in ("false", "0", "no", "n", "off"):  
        return False  
    raise argparse.ArgumentTypeError(f"Expected true|false, got: {v!r}")  
  
  
def build_arg_parser() -> argparse.ArgumentParser:  
    parser = argparse.ArgumentParser(description="Run the automation pipeline (with overrides).")  
  
    # Included for CLI-1A/1B integration; loading remains handled elsewhere.  
    parser.add_argument("--config", default=None, help="Path to config YAML/JSON file")  
  
    parser.add_argument("--browser", choices=["edge", "chrome"], default=None, help="Browser to use")  
    parser.add_argument("--headless", type=_str2bool, default=None, help="true|false")  
    parser.add_argument("--resume", type=_str2bool, default=None, help="true|false (resume semantics)")  
    parser.add_argument("--max-items", type=int, default=None, help="Limit number of work items processed")  
    parser.add_argument("--stop-on-error", type=_str2bool, default=None, help="true|false")  
    parser.add_argument("--download-dir", default=None, help="Download directory path")  
    parser.add_argument("--run-id", default=None, help="Optional run identifier override")  
  
    return parser  
  
  
def apply_overrides(cfg: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:  
    """  
    Return a new cfg dict with CLI overrides applied. Does not mutate cfg.  
    """  
    if not isinstance(cfg, dict):  
        raise TypeError("cfg must be a dict")  
  
    out: Dict[str, Any] = dict(cfg)  
  
    # Only apply when provided (None means "no override").  
    if getattr(args, "browser", None) is not None:  
        out["BROWSER"] = args.browser  
  
    if getattr(args, "headless", None) is not None:  
        out["HEADLESS"] = bool(args.headless)  
  
    if getattr(args, "resume", None) is not None:  
        out["RESUME"] = bool(args.resume)  
  
    if getattr(args, "max_items", None) is not None:  
        if args.max_items < 0:  
            raise ValueError("--max-items must be >= 0")  
        out["MAX_ITEMS"] = int(args.max_items)  
  
    if getattr(args, "stop_on_error", None) is not None:  
        out["STOP_ON_ERROR"] = bool(args.stop_on_error)  
  
    if getattr(args, "download_dir", None) is not None:  
        out["DOWNLOAD_DIR"] = str(args.download_dir)  
  
    if getattr(args, "run_id", None) is not None:  
        out["RUN_ID"] = str(args.run_id)  
  
    return out  