"""  
SCHEMA-1A — Step/Action Schema Export (AI-friendly)  
  
Generates:  
- SCHEMA/steps_schema.json  
- SCHEMA/steps_examples.json  
- (compat/alias) SCHEMA/schema_1a_steps.json  
  
Constraints:  
- Do NOT import/execute project modules with side effects.  
- Prefer DOC/library_index.json if present; otherwise statically scan ACT/, PIPE/, VAL/, NAV/.  
- Use static parsing (ast) to infer:  
  - action names  
  - required/optional fields  
  - basic field types (heuristics)  
  - allowed values (heuristics)  
  - examples (from literal dict/list literals in source)  
"""  
  
from __future__ import annotations  
  
import ast  
import json  
import re  
from dataclasses import dataclass, field  
from datetime import datetime, timezone  
from pathlib import Path  
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple  
  
  
__all__ = [  
    "generate_steps_schema",  
    "main",  
]  
  
  
SCAN_DIRS_DEFAULT = ("ACT", "PIPE", "VAL", "NAV")  
INDEX_JSON_REL = Path("DOC") / "library_index.json"  
  
#  
# Canonical STEP_GRAMMAR (do not expand here).  
# This is the contract enforced by BUILD and expected by LINT/SCHEMA.  
#  
CANONICAL_STEP_GRAMMAR_ACTIONS: Tuple[str, ...] = (  
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
  
_CANONICAL_FIELD_SPECS: Dict[str, Dict[str, Any]] = {  
    "open": {  
        "description": "Open a URL in the current tab.",  
        "required_fields": {"action", "url"},  
        "optional_fields": {"name"},  
        "field_types": {"action": "string", "url": "string", "name": "string"},  
    },  
    "click_selector": {  
        "description": "Click a target element by selector_ref or (strategy, selector).",  
        "required_fields": {"action"},  
        "optional_fields": {"name", "selector_ref", "strategy", "selector"},  
        "field_types": {  
            "action": "string",  
            "name": "string",  
            "selector_ref": "string",  
            "strategy": "string",  
            "selector": "string",  
        },  
    },  
    "type_selector_secret": {  
        "description": "Type a secret value into a target element.",  
        "required_fields": {"action", "secret"},  
        "optional_fields": {"name", "selector_ref", "strategy", "selector"},  
        "field_types": {  
            "action": "string",  
            "name": "string",  
            "selector_ref": "string",  
            "strategy": "string",  
            "selector": "string",  
            "secret": "string",  
        },  
    },  
    "wait_for_selector": {  
        "description": "Wait until a target selector is present/ready.",  
        "required_fields": {"action"},  
        "optional_fields": {"name", "selector_ref", "strategy", "selector"},  
        "field_types": {  
            "action": "string",  
            "name": "string",  
            "selector_ref": "string",  
            "strategy": "string",  
            "selector": "string",  
        },  
    },  
    "exec_js": {  
        "description": "Execute inline JavaScript and return a JSON-serializable value.",  
        "required_fields": {"action", "script"},  
        "optional_fields": {"name"},  
        "field_types": {"action": "string", "script": "string", "name": "string"},  
    },  
    "exec_js_file": {  
        "description": "Execute a JavaScript file from disk.",  
        "required_fields": {"action", "path"},  
        "optional_fields": {"name"},  
        "field_types": {"action": "string", "path": "string", "name": "string"},  
    },  
    "repeat": {  
        "description": "Repeat a nested block of steps a fixed number of times.",  
        "required_fields": {"action", "times", "steps"},  
        "optional_fields": {"name"},  
        "field_types": {"action": "string", "times": "int", "steps": "list", "name": "string"},  
    },  
    "log": {  
        "description": "Emit a log message (supports VAR placeholders).",  
        "required_fields": {"action", "message"},  
        "optional_fields": {"name"},  
        "field_types": {"action": "string", "message": "string", "name": "string"},  
    },  
    "switch_back_to_main_tab": {  
        "description": "Switch focus back to the main tab/window.",  
        "required_fields": {"action"},  
        "optional_fields": {"name"},  
        "field_types": {"action": "string", "name": "string"},  
    },  
}  
  
OPTION_ID_RE = re.compile(r"\b[A-Z]{2,10}-\d+[A-Z]\b")  
ACTION_FUNC_RE = re.compile(r"^(?:act|action)_(?P<action>[a-zA-Z0-9_]+)$")  
  
  
def _utc_now_iso() -> str:  
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")  
  
  
def _read_text(p: Path) -> str:  
    return p.read_text(encoding="utf-8", errors="replace")  
  
  
def _safe_json_load(p: Path) -> Optional[dict]:  
    try:  
        return json.loads(_read_text(p))  
    except Exception:  
        return None  
  
  
def _ensure_dir(p: Path) -> None:  
    p.mkdir(parents=True, exist_ok=True)  
  
  
def _as_posix_rel(repo_root: Path, p: Path) -> str:  
    try:  
        return p.resolve().relative_to(repo_root.resolve()).as_posix()  
    except Exception:  
        return p.as_posix()  
  
  
def _infer_option_id_from_text(text: str) -> Optional[str]:  
    m = OPTION_ID_RE.search(text)  
    return m.group(0) if m else None  
  
  
def _looks_like_repo_root(p: Path) -> bool:  
    if not p.exists() or not p.is_dir():  
        return False  
    if (p / "LIBRARY_MAP.md").exists():  
        return True  
    if (p / "DOC" / "library_index.json").exists():  
        return True  
    if any((p / d).is_dir() for d in SCAN_DIRS_DEFAULT):  
        return True  
    if (p / "SCHEMA").is_dir():  
        return True  
    return False  
  
  
def _find_repo_root(start: Path) -> Path:  
    s = start  
    if s.is_file():  
        s = s.parent  
    for cand in [s, *s.parents]:  
        if _looks_like_repo_root(cand):  
            return cand  
    return s  
  
  
def _py_files_under(repo_root: Path, rel_dirs: Iterable[str]) -> List[Path]:  
    out: List[Path] = []  
    for d in rel_dirs:  
        base = repo_root / d  
        if not base.exists() or not base.is_dir():  
            continue  
        for p in base.rglob("*.py"):  
            # Do NOT skip __init__.py or underscore files; we are only parsing AST (no imports).  
            out.append(p)  
    return sorted(set(out))  
  
  
def _modules_from_library_index(repo_root: Path, index_obj: dict) -> List[Tuple[Path, Optional[str]]]:  
    """  
    Best-effort extraction of module paths + option_ids from DOC/library_index.json.  
    """  
    candidates: List[dict] = []  
    for k in ("modules", "entries", "items"):  
        v = index_obj.get(k)  
        if isinstance(v, list):  
            candidates.extend([x for x in v if isinstance(x, dict)])  
  
    if not candidates:  
        for v in index_obj.values():  
            if isinstance(v, list) and v and all(isinstance(x, dict) for x in v):  
                candidates.extend(v)  
  
    out: List[Tuple[Path, Optional[str]]] = []  
    for entry in candidates:  
        path_s = entry.get("path") or entry.get("module_path") or entry.get("file") or entry.get("filepath")  
        if not isinstance(path_s, str):  
            continue  
  
        if not any(path_s.startswith(d + "/") or path_s.startswith(d + "\\") for d in SCAN_DIRS_DEFAULT):  
            continue  
  
        opt = entry.get("option_id") or entry.get("milestone") or entry.get("id")  
        opt = opt if isinstance(opt, str) else None  
  
        p = (repo_root / path_s).resolve()  
        if p.exists() and p.is_file() and p.suffix == ".py":  
            out.append((p, opt))  
  
    seen: Set[Path] = set()  
    dedup: List[Tuple[Path, Optional[str]]] = []  
    for p, opt in out:  
        if p in seen:  
            continue  
        seen.add(p)  
        dedup.append((p, opt))  
  
    return dedup  
  
  
def _const_str(node: ast.AST) -> Optional[str]:  
    if isinstance(node, ast.Constant) and isinstance(node.value, str):  
        return node.value  
    return None  
  
  
def _const_simple(node: ast.AST) -> Optional[Any]:  
    try:  
        return ast.literal_eval(node)  
    except Exception:  
        return None  
  
  
def _is_name(node: ast.AST, names: Set[str]) -> bool:  
    return isinstance(node, ast.Name) and node.id in names  
  
  
def _extract_subscript_key(node: ast.Subscript) -> Optional[str]:  
    sl = node.slice  
    if isinstance(sl, ast.Constant) and isinstance(sl.value, str):  
        return sl.value  
    return None  
  
  
def _step_get_call_key(node: ast.Call, step_names: Set[str]) -> Optional[Tuple[str, Optional[ast.AST]]]:  
    if not isinstance(node.func, ast.Attribute):  
        return None  
    if node.func.attr != "get":  
        return None  
    if not _is_name(node.func.value, step_names):  
        return None  
    if not node.args:  
        return None  
    key = _const_str(node.args[0])  
    if not key:  
        return None  
    default_node = node.args[1] if len(node.args) >= 2 else None  
    return (key, default_node)  
  
  
def _step_subscript_key(node: ast.Subscript, step_names: Set[str]) -> Optional[str]:  
    if not _is_name(node.value, step_names):  
        return None  
    return _extract_subscript_key(node)  
  
  
def _infer_type_from_literal(val: Any) -> str:  
    if val is None:  
        return "any"  
    if isinstance(val, bool):  
        return "bool"  
    if isinstance(val, int) and not isinstance(val, bool):  
        return "int"  
    if isinstance(val, float):  
        return "float"  
    if isinstance(val, str):  
        return "string"  
    if isinstance(val, list):  
        return "list"  
    if isinstance(val, dict):  
        return "object"  
    return "any"  
  
  
@dataclass  
class ActionInfo:  
    action: str  
    description: str = ""  
    required_fields: Set[str] = field(default_factory=set)  
    optional_fields: Set[str] = field(default_factory=set)  
    field_types: Dict[str, str] = field(default_factory=dict)  
    allowed_values: Dict[str, Set[str]] = field(default_factory=dict)  
    examples: List[dict] = field(default_factory=list)  
    implemented_by_module: str = ""  
    implemented_by_option_id: Optional[str] = None  
  
    def merge_from(self, other: "ActionInfo") -> None:  
        if not self.description and other.description:  
            self.description = other.description  
        self.required_fields |= other.required_fields  
        self.optional_fields |= other.optional_fields  
        for k, v in other.field_types.items():  
            self.field_types.setdefault(k, v)  
        for k, vals in other.allowed_values.items():  
            self.allowed_values.setdefault(k, set()).update(vals)  
        seen = {json.dumps(e, sort_keys=True, ensure_ascii=False) for e in self.examples}  
        for e in other.examples:  
            sig = json.dumps(e, sort_keys=True, ensure_ascii=False)  
            if sig not in seen:  
                self.examples.append(e)  
                seen.add(sig)  
  
  
class _StepUsageVisitor(ast.NodeVisitor):  
    def __init__(self, step_names: Set[str]) -> None:  
        self.step_names = set(step_names)  
        self.required_fields: Set[str] = set()  
        self.optional_fields: Set[str] = set()  
        self.allowed_values: Dict[str, Set[str]] = {}  
        self.field_types: Dict[str, str] = {}  
  
    def _record_field_type(self, key: str, literal_value: Any) -> None:  
        t = _infer_type_from_literal(literal_value)  
        if key not in self.field_types or self.field_types[key] == "any":  
            self.field_types[key] = t  
  
    def visit_Subscript(self, node: ast.Subscript) -> Any:  
        key = _step_subscript_key(node, self.step_names)  
        if key:  
            self.required_fields.add(key)  
        self.generic_visit(node)  
  
    def visit_Call(self, node: ast.Call) -> Any:  
        got = _step_get_call_key(node, self.step_names)  
        if got:  
            key, default_node = got  
            self.optional_fields.add(key)  
            if default_node is not None:  
                dv = _const_simple(default_node)  
                if dv is not None:  
                    self._record_field_type(key, dv)  
        self.generic_visit(node)  
  
    def visit_Compare(self, node: ast.Compare) -> Any:  
        field_key = None  
        left = node.left  
  
        if isinstance(left, ast.Call):  
            got = _step_get_call_key(left, self.step_names)  
            if got:  
                field_key = got[0]  
        elif isinstance(left, ast.Subscript):  
            field_key = _step_subscript_key(left, self.step_names)  
  
        if field_key:  
            for op, comp in zip(node.ops, node.comparators):  
                if isinstance(op, (ast.Eq, ast.NotEq)):  
                    s = _const_str(comp)  
                    if s is not None:  
                        self.allowed_values.setdefault(field_key, set()).add(s)  
                        self._record_field_type(field_key, s)  
                elif isinstance(op, ast.In):  
                    lit = _const_simple(comp)  
                    if isinstance(lit, (list, tuple)) and all(isinstance(x, str) for x in lit):  
                        self.allowed_values.setdefault(field_key, set()).update(set(lit))  
                        self._record_field_type(field_key, "x")  
        self.generic_visit(node)  
  
  
class _ActionStringVisitor(ast.NodeVisitor):  
    """  
    Find action strings referenced in:  
    - comparisons involving step['action'] / step.get('action')  
    - match-case mapping patterns  
    - assignments like ACTION="get"  
    - registry-like containers assigned to ACTION-ish names  
    - dict literals containing {"action": "<name>"}  
    """  
  
    ACTION_CONTAINER_NAME_HINTS = ("ACTION", "ACTIONS", "HANDLER", "HANDLERS", "MAP")  
  
    def __init__(self) -> None:  
        self.action_names: Set[str] = set()  
  
    def visit_Assign(self, node: ast.Assign) -> Any:  
        # ACTION = "get" / ACTION_NAME = "get"  
        for t in node.targets:  
            if isinstance(t, ast.Name) and t.id in {"ACTION", "ACTION_NAME", "ACTION_ID"}:  
                s = _const_str(node.value)  
                if s:  
                    self.action_names.add(s)  
  
            # Registry heuristic: VAR_NAME contains ACTION/HANDLER/MAP and value is literal container  
            if isinstance(t, ast.Name):  
                up = t.id.upper()  
                if any(h in up for h in self.ACTION_CONTAINER_NAME_HINTS):  
                    lit = _const_simple(node.value)  
                    if isinstance(lit, dict):  
                        for k in lit.keys():  
                            if isinstance(k, str):  
                                self.action_names.add(k)  
                    elif isinstance(lit, (list, tuple, set)):  
                        for x in lit:  
                            if isinstance(x, str):  
                                self.action_names.add(x)  
  
        self.generic_visit(node)  
  
    def visit_Dict(self, node: ast.Dict) -> Any:  
        # {"action": "get", ...} anywhere in module  
        for k_node, v_node in zip(node.keys, node.values):  
            k = _const_str(k_node) if k_node is not None else None  
            if k == "action":  
                v = _const_str(v_node)  
                if v:  
                    self.action_names.add(v)  
        self.generic_visit(node)  
  
    def visit_Compare(self, node: ast.Compare) -> Any:  
        left = node.left  
  
        def _left_mentions_action(n: ast.AST) -> bool:  
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "get":  
                if n.args and _const_str(n.args[0]) == "action":  
                    return True  
            if isinstance(n, ast.Subscript):  
                k = _extract_subscript_key(n)  
                return k == "action"  
            return False  
  
        if _left_mentions_action(left):  
            for op, comp in zip(node.ops, node.comparators):  
                if isinstance(op, ast.Eq):  
                    s = _const_str(comp)  
                    if s:  
                        self.action_names.add(s)  
  
        self.generic_visit(node)  
  
    def visit_Match(self, node: ast.Match) -> Any:  
        for c in node.cases:  
            pat = c.pattern  
            if isinstance(pat, ast.MatchMapping):  
                keys = pat.keys or []  
                pats = pat.patterns or []  
                for k_node, p_node in zip(keys, pats):  
                    k = _const_str(k_node)  
                    if k != "action":  
                        continue  
                    if isinstance(p_node, ast.MatchValue):  
                        s = _const_str(p_node.value)  
                        if s:  
                            self.action_names.add(s)  
        self.generic_visit(node)  
  
  
class _ExamplesVisitor(ast.NodeVisitor):  
    def __init__(self) -> None:  
        self.examples_by_action: Dict[str, List[dict]] = {}  
  
    def _maybe_record(self, value_node: ast.AST) -> None:  
        lit = _const_simple(value_node)  
        if isinstance(lit, dict):  
            act = lit.get("action")  
            if isinstance(act, str):  
                self.examples_by_action.setdefault(act, []).append(lit)  
        elif isinstance(lit, list):  
            for x in lit:  
                if isinstance(x, dict):  
                    act = x.get("action")  
                    if isinstance(act, str):  
                        self.examples_by_action.setdefault(act, []).append(x)  
  
    def visit_Assign(self, node: ast.Assign) -> Any:  
        for t in node.targets:  
            if isinstance(t, ast.Name) and ("EXAMPLE" in t.id.upper()):  
                self._maybe_record(node.value)  
        self.generic_visit(node)  
  
    def visit_Expr(self, node: ast.Expr) -> Any:  
        self._maybe_record(node.value)  
        self.generic_visit(node)  
  
  
def _extract_action_handlers_from_module(tree: ast.Module) -> List[Tuple[str, ast.AST, str]]:  
    out: List[Tuple[str, ast.AST, str]] = []  
    for node in tree.body:  
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):  
            m = ACTION_FUNC_RE.match(node.name)  
            if not m:  
                continue  
            action = m.group("action")  
            doc = ast.get_docstring(node) or ""  
            desc = doc.strip().splitlines()[0].strip() if doc.strip() else ""  
            out.append((action, node, desc))  
    return out  
  
  
def _infer_step_arg_names(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> Set[str]:  
    names = {a.arg for a in fn.args.args if isinstance(a.arg, str)}  
    preferred = {"step", "s", "st", "item", "spec"}  
    chosen = (names & preferred) or names or {"step"}  
    return set(chosen)  
  
  
def _parse_module_for_actions(repo_root: Path, py_path: Path, option_id: Optional[str]) -> Dict[str, ActionInfo]:  
    text = _read_text(py_path)  
    inferred_opt = option_id or _infer_option_id_from_text(text)  
  
    try:  
        tree = ast.parse(text, filename=str(py_path))  
    except SyntaxError:  
        return {}  
  
    mod_rel = _as_posix_rel(repo_root, py_path)  
  
    exv = _ExamplesVisitor()  
    exv.visit(tree)  
  
    asv = _ActionStringVisitor()  
    asv.visit(tree)  
  
    actions: Dict[str, ActionInfo] = {}  
  
    # Primary: functions named act_<action> / action_<action>  
    for action, node, desc in _extract_action_handlers_from_module(tree):  
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):  
            step_names = _infer_step_arg_names(node)  
            suv = _StepUsageVisitor(step_names=step_names)  
            for stmt in node.body:  
                suv.visit(stmt)  
  
            ai = ActionInfo(  
                action=action,  
                description=desc,  
                required_fields=set(suv.required_fields) | {"action"},  
                optional_fields=set(suv.optional_fields),  
                field_types=dict(suv.field_types),  
                allowed_values={k: set(v) for k, v in suv.allowed_values.items()},  
                examples=list(exv.examples_by_action.get(action, [])),  
                implemented_by_module=mod_rel,  
                implemented_by_option_id=inferred_opt,  
            )  
            ai.field_types.setdefault("action", "string")  
            actions[action] = ai  
  
    # Secondary: action strings referenced in the module (dispatcher/registries/dicts)  
    for action in sorted(asv.action_names):  
        if action in actions:  
            continue  
        ai = ActionInfo(  
            action=action,  
            required_fields={"action"},  
            optional_fields=set(),  
            field_types={"action": "string"},  
            allowed_values={},  
            examples=list(exv.examples_by_action.get(action, [])),  
            implemented_by_module=mod_rel,  
            implemented_by_option_id=inferred_opt,  
        )  
        actions[action] = ai  
  
    # Tertiary: actions appearing only in literal examples  
    for action in sorted(exv.examples_by_action.keys()):  
        if action in actions:  
            continue  
        ai = ActionInfo(  
            action=action,  
            required_fields={"action"},  
            optional_fields=set(),  
            field_types={"action": "string"},  
            allowed_values={},  
            examples=list(exv.examples_by_action.get(action, [])),  
            implemented_by_module=mod_rel,  
            implemented_by_option_id=inferred_opt,  
        )  
        actions[action] = ai  
  
    return actions  
  
  
def generate_steps_schema(  
    repo_root: Optional[Path] = None,  
    out_dir: Optional[Path] = None,  
    prefer_library_index: bool = True,  
) -> dict:  
    detected_root = _find_repo_root(Path(__file__).resolve())  
    if repo_root is None or not _looks_like_repo_root(repo_root):  
        repo_root = detected_root  
  
    # Per milestone spec: outputs go in repo_root/SCHEMA  
    out_dir = repo_root / "SCHEMA" if out_dir is None else out_dir  
    if out_dir.name != "SCHEMA" or (repo_root not in [out_dir, *out_dir.parents]):  
        out_dir = repo_root / "SCHEMA"  
  
    _ensure_dir(out_dir)  
  
    module_list: List[Tuple[Path, Optional[str]]] = []  
    idx_path = repo_root / INDEX_JSON_REL  
    idx_obj = _safe_json_load(idx_path) if (prefer_library_index and idx_path.exists()) else None  
    if isinstance(idx_obj, dict):  
        module_list = _modules_from_library_index(repo_root, idx_obj)  
  
    if not module_list:  
        for p in _py_files_under(repo_root, SCAN_DIRS_DEFAULT):  
            module_list.append((p, None))  
  
    merged: Dict[str, ActionInfo] = {}  
    for py_path, opt in module_list:  
        if not py_path.exists():  
            continue  
        infos = _parse_module_for_actions(repo_root=repo_root, py_path=py_path, option_id=opt)  
        for action, ai in infos.items():  
            if action not in merged:  
                merged[action] = ai  
            else:  
                merged[action].merge_from(ai)  
  
    supported_actions: List[dict] = []  
    examples_by_action: Dict[str, List[dict]] = {}  
  
    # Enforce canonical STEP_GRAMMAR as the only supported action set.  
    # This prevents heuristic “action string” pollution (e.g., click/tap/go/wait)  
    # from breaking LINT for valid workflows.  
    for action in CANONICAL_STEP_GRAMMAR_ACTIONS:  
        ai = merged.get(action) or ActionInfo(action=action)  
        spec = _CANONICAL_FIELD_SPECS.get(action, {})  
  
        req_set = set(spec.get("required_fields") or {"action"})  
        opt_set = set(spec.get("optional_fields") or set())  
        ftypes = dict(spec.get("field_types") or {"action": "string"})  
  
        # keep inferred examples if any, but never allow non-canonical actions  
        examples = ai.examples[:] if ai.examples else []  
  
        supported_actions.append(  
            {  
                "action": action,  
                "description": (spec.get("description") or ai.description or ""),  
                "required_fields": sorted(req_set),  
                "optional_fields": sorted(opt_set - req_set),  
                "field_types": {k: ftypes.get(k, "any") for k in sorted((req_set | opt_set))},  
                "allowed_values": {},  
                "examples": examples,  
                "implemented_by": {  
                    "module": ai.implemented_by_module or "",  
                    "option_id": ai.implemented_by_option_id,  
                },  
            }  
        )  
        examples_by_action[action] = examples  
  
    schema = {  
        "schema_version": "SCHEMA-1A",  
        "generated_at": _utc_now_iso(),  
        "notes": {  
            "var_placeholders": (  
                "String fields may support VAR placeholders like ${VAR}. "  
                "Resolution behavior is defined by VAR-1A and related runtime utilities."  
            ),  
            "guards": (  
                "Some actions/steps may support guard conditions (ACT-1C). "  
                "If guard-related fields are not inferred statically, consult ACT-1C docs/implementation."  
            ),  
            "blocks": (  
                "Block-style actions (PIPE-2B), such as if/group/try, "  
                "may contain nested step lists (e.g., steps/then/else/catch)."  
            ),  
        },  
        "supported_actions": supported_actions,  
    }  
  
    steps_schema_path = out_dir / "steps_schema.json"  
    steps_examples_path = out_dir / "steps_examples.json"  
    alias_path = out_dir / "schema_1a_steps.json"  
  
    steps_schema_path.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")  
    steps_examples_path.write_text(  
        json.dumps(  
            {  
                "schema_version": "SCHEMA-1A",  
                "generated_at": schema["generated_at"],  
                "examples_by_action": examples_by_action,  
            },  
            indent=2,  
            ensure_ascii=False,  
        )  
        + "\n",  
        encoding="utf-8",  
    )  
    alias_path.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")  
  
    return schema  
  
  
def main(argv: Optional[List[str]] = None) -> int:  
    _ = argv  
    schema = generate_steps_schema()  
    out_dir = (_find_repo_root(Path(__file__).resolve()) / "SCHEMA")  
    print(f"[SCHEMA-1A] Wrote: {(out_dir / 'steps_schema.json').as_posix()}")  
    print(f"[SCHEMA-1A] Wrote: {(out_dir / 'steps_examples.json').as_posix()}")  
    print(f"[SCHEMA-1A] Wrote: {(out_dir / 'schema_1a_steps.json').as_posix()}")  
    print(f"[SCHEMA-1A] Actions: {len(schema.get('supported_actions', []))}")  
    return 0  
  
  
if __name__ == "__main__":  
    raise SystemExit(main())  