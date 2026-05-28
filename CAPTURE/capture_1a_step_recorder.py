from __future__ import annotations  
  
from dataclasses import dataclass, field  
from pathlib import Path  
from typing import Any, Iterable, Mapping  
  
  
__all__ = [  
    "SUPPORTED_STEP_ACTIONS",  
    "Capture1AStepRecorder",  
    "event_to_schema_step",  
    "dev_smoke",  
]  
  
  
# Must remain aligned with the framework's allowed step action grammar.  
SUPPORTED_STEP_ACTIONS: tuple[str, ...] = (  
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
  
  
def _to_jsonable(v: Any) -> Any:  
    if isinstance(v, Path):  
        return str(v)  
    return v  
  
  
_KEY_PRIORITY: tuple[str, ...] = (  
    # common  
    "action",  
    # selector preference  
    "selector_ref",  
    "selector",  
    # common action fields  
    "url",  
    "message",  
    "secret_ref",  
    "text",  
    "timeout_ms",  
    "script",  
    "path",  
    # repeat  
    "times",  
    "steps",  
)  
  
  
def _stable_step_dict(action: str, fields: Mapping[str, Any]) -> dict[str, Any]:  
    if action not in SUPPORTED_STEP_ACTIONS:  
        raise ValueError(f"Unsupported step action: {action!r}")  
  
    # Drop None values deterministically  
    cleaned: dict[str, Any] = {k: _to_jsonable(v) for k, v in fields.items() if v is not None}  
  
    # Deterministic ordering of keys (use insertion order of dict)  
    out: dict[str, Any] = {"action": action}  
  
    # priority keys first (if present)  
    for k in _KEY_PRIORITY:  
        if k == "action":  
            continue  
        if k in cleaned:  
            out[k] = cleaned.pop(k)  
  
    # remaining keys in sorted order  
    for k in sorted(cleaned.keys()):  
        out[k] = cleaned[k]  
  
    return out  
  
  
def event_to_schema_step(event: Mapping[str, Any]) -> dict[str, Any]:  
    """  
    Convert a generic "captured event" dict into a SCHEMA-1A step dict.  
  
    Supported event shapes (minimal):  
      - {"type": "open", "url": "..."}  
      - {"type": "click", "selector_ref": "..."} or {"type": "click", "selector": "..."}  
      - {"type": "type_secret", "selector_ref": "...", "secret_ref": "..."}  
      - {"type": "wait_for", "selector_ref": "...", "timeout_ms": 10000}  
      - {"type": "log", "message": "..."}  
      - {"type": "switch_back_to_main_tab"}  
      - {"type": "exec_js", "script": "..."}  
      - {"type": "exec_js_file", "path": "..."}  
      - {"type": "repeat", "times": 2, "steps": [ ... ]}  
  
    If your capture format already uses {"action": "..."} you can pass it through by  
    providing event["action"] and other step fields; this function will normalize and  
    enforce allowed actions.  
    """  
    if not isinstance(event, Mapping):  
        raise TypeError("event must be a mapping/dict")  
  
    # passthrough if already a step-like object  
    if "action" in event:  
        action = event.get("action")  
        if not isinstance(action, str):  
            raise TypeError("event['action'] must be a string")  
        fields = {k: v for k, v in event.items() if k != "action"}  
        return _stable_step_dict(action, fields)  
  
    et = event.get("type")  
    if not isinstance(et, str) or not et.strip():  
        raise ValueError("event missing required string field 'type' (or 'action')")  
  
    et = et.strip()  
  
    if et == "open":  
        return _stable_step_dict("open", {"url": event.get("url")})  
  
    if et == "click":  
        return _stable_step_dict(  
            "click_selector",  
            {"selector_ref": event.get("selector_ref"), "selector": event.get("selector")},  
        )  
  
    if et == "type_secret":  
        return _stable_step_dict(  
            "type_selector_secret",  
            {  
                "selector_ref": event.get("selector_ref"),  
                "selector": event.get("selector"),  
                "secret_ref": event.get("secret_ref"),  
            },  
        )  
  
    if et == "wait_for":  
        return _stable_step_dict(  
            "wait_for_selector",  
            {  
                "selector_ref": event.get("selector_ref"),  
                "selector": event.get("selector"),  
                "timeout_ms": event.get("timeout_ms"),  
            },  
        )  
  
    if et == "log":  
        return _stable_step_dict("log", {"message": event.get("message")})  
  
    if et == "switch_back_to_main_tab":  
        return _stable_step_dict("switch_back_to_main_tab", {})  
  
    if et == "exec_js":  
        return _stable_step_dict("exec_js", {"script": event.get("script")})  
  
    if et == "exec_js_file":  
        return _stable_step_dict("exec_js_file", {"path": event.get("path")})  
  
    if et == "repeat":  
        return _stable_step_dict(  
            "repeat",  
            {"times": event.get("times"), "steps": event.get("steps")},  
        )  
  
    raise ValueError(f"Unsupported capture event type: {et!r}")  
  
  
@dataclass  
class Capture1AStepRecorder:  
    """  
    In-memory recorder for supported SCHEMA-1A workflow steps.  
  
    This does not interact with Selenium; it is a deterministic step recorder that  
    CAPTURE tooling can call once it has identified what happened (open/click/type/etc).  
    """  
  
    _steps: list[dict[str, Any]] = field(default_factory=list)  
  
    def record_step(self, action: str, **fields: Any) -> dict[str, Any]:  
        step = _stable_step_dict(action, fields)  
        self._steps.append(step)  
        return step  
  
    def record_event(self, event: Mapping[str, Any]) -> dict[str, Any]:  
        step = event_to_schema_step(event)  
        self._steps.append(step)  
        return step  
  
    def extend_events(self, events: Iterable[Mapping[str, Any]]) -> None:  
        for e in events:  
            self.record_event(e)  
  
    def as_steps(self) -> list[dict[str, Any]]:  
        # return a shallow copy for safety  
        return list(self._steps)  
  
    # Convenience methods (optional for callers)  
    def open(self, url: str) -> dict[str, Any]:  
        return self.record_step("open", url=url)  
  
    def click(self, *, selector_ref: str | None = None, selector: str | None = None) -> dict[str, Any]:  
        return self.record_step("click_selector", selector_ref=selector_ref, selector=selector)  
  
    def type_secret(  
        self,  
        *,  
        selector_ref: str | None = None,  
        selector: str | None = None,  
        secret_ref: str | None = None,  
    ) -> dict[str, Any]:  
        return self.record_step(  
            "type_selector_secret",  
            selector_ref=selector_ref,  
            selector=selector,  
            secret_ref=secret_ref,  
        )  
  
    def wait_for(  
        self,  
        *,  
        selector_ref: str | None = None,  
        selector: str | None = None,  
        timeout_ms: int | None = None,  
    ) -> dict[str, Any]:  
        return self.record_step(  
            "wait_for_selector",  
            selector_ref=selector_ref,  
            selector=selector,  
            timeout_ms=timeout_ms,  
        )  
  
    def log(self, message: str) -> dict[str, Any]:  
        return self.record_step("log", message=message)  
  
    def switch_back_to_main_tab(self) -> dict[str, Any]:  
        return self.record_step("switch_back_to_main_tab")  
  
  
def dev_smoke() -> dict[str, Any]:  
    r = Capture1AStepRecorder()  
    r.open("https://example.invalid/")  
    r.click(selector_ref="LOGIN.USERNAME")  
    r.type_secret(selector_ref="LOGIN.PASSWORD", secret_ref="PORTAL_PASSWORD")  
    r.wait_for(selector_ref="DASHBOARD.ROOT", timeout_ms=10_000)  
    r.log("arrived at dashboard")  
    r.switch_back_to_main_tab()  
  
    steps = r.as_steps()  
  
    # Deterministic + only allowed actions  
    assert [s["action"] for s in steps] == [  
        "open",  
        "click_selector",  
        "type_selector_secret",  
        "wait_for_selector",  
        "log",  
        "switch_back_to_main_tab",  
    ]  
    for s in steps:  
        assert s["action"] in SUPPORTED_STEP_ACTIONS  
  
    return {"ok": True, "steps_count": len(steps), "steps": steps}  
  
  
if __name__ == "__main__":  
    raise SystemExit(0 if dev_smoke().get("ok") else 1)  