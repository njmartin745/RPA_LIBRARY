"""  
CLI-1B — Configuration Loader.  
  
Loads configuration from JSON or YAML files and expands environment variables like:  
  ${HOME}  
  ${RUN_ID}  
  
Format support:  
- JSON: always supported.  
- YAML: supported via PyYAML (yaml.safe_load) if installed.  
  If PyYAML is unavailable, default behavior is "JSON-only" (clear error for YAML).  
  
Compatibility / preserving existing functionality:  
- This module still includes the prior minimal YAML parser for very simple YAML files.  
  It is **opt-in** when PyYAML is not installed by setting:  
      CLI_CONFIG_ALLOW_MINIMAL_YAML=1  
  (This preserves the previously-working fallback behavior without violating the  
  "JSON-only without PyYAML" default expectation.)  
  
Environment expansion:  
- Expands ${VAR_NAME} in string *values* recursively (not keys).  
- If a referenced env var is missing, raises a clear error.  
"""  
  
from __future__ import annotations  
  
import json  
import os  
import re  
from pathlib import Path  
from typing import Any, Dict, Union  
  
__all__ = ["load_config"]  
  
_ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")  
  
  
def _expand_env_in_str(s: str) -> str:  
    def repl(m: re.Match) -> str:  
        key = m.group(1)  
        if key not in os.environ:  
            raise ValueError(f"Missing environment variable for config expansion: {key}")  
        return os.environ[key]  
  
    return _ENV_PATTERN.sub(repl, s)  
  
  
def _expand_env_values(obj: Any) -> Any:  
    """  
    Expand env vars in string values recursively.  
    (Keys are preserved as-is except cast to str to normalize.)  
    """  
    if obj is None:  
        return None  
    if isinstance(obj, str):  
        return _expand_env_in_str(obj)  
    if isinstance(obj, list):  
        return [_expand_env_values(x) for x in obj]  
    if isinstance(obj, dict):  
        return {str(k): _expand_env_values(v) for k, v in obj.items()}  
    return obj  
  
  
def _parse_scalar(v: str) -> Any:  
    s = v.strip()  
    if s == "":  
        return ""  
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):  
        return s[1:-1]  
    low = s.lower()  
    if low in ("true", "yes", "on"):  
        return True  
    if low in ("false", "no", "off"):  
        return False  
    if low in ("null", "none", "~"):  
        return None  
    # numbers  
    try:  
        if "." in s:  
            return float(s)  
        return int(s)  
    except Exception:  
        pass  
    # inline list: [a, b, c]  
    if s.startswith("[") and s.endswith("]"):  
        inner = s[1:-1].strip()  
        if not inner:  
            return []  
        parts = [p.strip() for p in inner.split(",")]  
        return [_parse_scalar(p) for p in parts]  
    return s  
  
  
def _simple_yaml_load(text: str) -> Dict[str, Any]:  
    """  
    Minimal YAML loader (top-level mapping + simple lists) used only when:  
    - PyYAML is not installed, AND  
    - CLI_CONFIG_ALLOW_MINIMAL_YAML=1  
  
    For anything complex, install PyYAML.  
    """  
    out: Dict[str, Any] = {}  
    current_list_key: Union[str, None] = None  
  
    for raw in text.splitlines():  
        line = raw.strip("\n")  
  
        # strip comments (best-effort)  
        if "#" in line:  
            line = line.split("#", 1)[0]  
        if not line.strip():  
            continue  
  
        if line.lstrip().startswith("- "):  
            if current_list_key is None or not isinstance(out.get(current_list_key), list):  
                raise ValueError("Invalid YAML: list item without a list key context")  
            item_txt = line.lstrip()[2:].strip()  
            out[current_list_key].append(_parse_scalar(item_txt))  
            continue  
  
        if ":" not in line:  
            raise ValueError(f"Invalid YAML line (expected key: value): {raw}")  
  
        key, val = line.split(":", 1)  
        key = key.strip()  
        val = val.strip()  
  
        if val == "":  
            # start a list context (supports subsequent "- item" lines)  
            out[key] = []  
            current_list_key = key  
        else:  
            out[key] = _parse_scalar(val)  
            current_list_key = None  
  
    return out  
  
  
def _load_yaml(text: str) -> Any:  
    """  
    Load YAML using PyYAML if available.  
  
    If PyYAML is unavailable:  
    - default: raise clear error (JSON-only fallback)  
    - optional: allow minimal YAML via CLI_CONFIG_ALLOW_MINIMAL_YAML=1  
    """  
    try:  
        import yaml  # type: ignore  
    except ModuleNotFoundError:  
        if os.environ.get("CLI_CONFIG_ALLOW_MINIMAL_YAML", "").strip() == "1":  
            return _simple_yaml_load(text)  
        raise ValueError(  
            "YAML config requested but PyYAML is not installed. "  
            "Install with: pip install pyyaml, or use a JSON config instead."  
        )  
  
    try:  
        return yaml.safe_load(text)  
    except Exception as e:  
        raise ValueError(f"YAML parse error: {e}") from e  
  
  
def load_config(path: str) -> dict:  
    """  
    Load JSON (.json) or YAML (.yml/.yaml) config file and expand ${ENV_VAR} in string values.  
  
    Raises clear errors for:  
    - file not found  
    - unsupported format  
    - parse error  
    - missing env vars referenced in config  
  
    Note: Does not print file contents (avoids accidental secret leakage).  
    """  
    p = Path(path)  
    if not p.exists():  
        raise FileNotFoundError(f"Config file not found: {p}")  
  
    ext = p.suffix.lower()  
    try:  
        text = p.read_text(encoding="utf-8")  
    except Exception as e:  
        raise OSError(f"Unable to read config file: {p}") from e  
  
    try:  
        if ext == ".json":  
            data = json.loads(text)  
        elif ext in (".yml", ".yaml"):  
            data = _load_yaml(text)  
        else:  
            raise ValueError(f"Unsupported config format: {ext} (expected .json/.yml/.yaml)")  
    except ValueError:  
        raise  
    except Exception as e:  
        raise ValueError(f"Config parse error for {p}: {e}") from e  
  
    if data is None:  
        data = {}  
    if not isinstance(data, dict):  
        raise ValueError("Config root must be a mapping/object (dict).")  
  
    return _expand_env_values(data)  