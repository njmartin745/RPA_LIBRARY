"""  
SNAP-1C — Persist snapshot artifacts deterministically (10.1.3)  
  
Single responsibility:  
- Given snapshot payload(s) (from SNAP-1A and optionally SNAP-1B), write artifacts  
  under a provided run output directory in a deterministic layout.  
  
This module does NOT:  
- capture DOM/URL (10.1.1)  
- capture screenshots (10.1.2)  
"""  
  
from __future__ import annotations  
  
import base64  
import json  
import os  
import re  
from pathlib import Path  
from typing import Any, Mapping  
  
__all__ = [  
    "persist_snapshot_artifacts",  
    "dev_smoke",  
]  
  
  
_SAFE_SEGMENT_RE = re.compile(r"[^A-Za-z0-9._-]+")  
  
  
def _sanitize_segment(value: Any, *, default: str, max_len: int = 80) -> str:  
    s = "" if value is None else str(value)  
    s = s.strip()  
    if not s:  
        s = default  
    s = _SAFE_SEGMENT_RE.sub("_", s)  
    s = s.strip("._-") or default  
    if len(s) > max_len:  
        s = s[:max_len]  
    return s  
  
  
def _stable_json_bytes(obj: Any) -> bytes:  
    # Deterministic JSON encoding (stable key sort + stable whitespace)  
    return json.dumps(  
        obj,  
        sort_keys=True,  
        indent=2,  
        ensure_ascii=True,  
    ).encode("utf-8")  
  
  
def _write_bytes(path: Path, data: bytes, *, overwrite: bool) -> None:  
    path.parent.mkdir(parents=True, exist_ok=True)  
    if path.exists() and not overwrite:  
        raise FileExistsError(str(path))  
    path.write_bytes(data)  
  
  
def _write_text(path: Path, text: str, *, overwrite: bool) -> None:  
    path.parent.mkdir(parents=True, exist_ok=True)  
    if path.exists() and not overwrite:  
        raise FileExistsError(str(path))  
    # Force consistent newlines regardless of OS  
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8", newline="\n")  
  
  
def persist_snapshot_artifacts(  
    *,  
    run_output_dir: str | os.PathLike[str],  
    snapshot_payload: Mapping[str, Any],  
    screenshot_payload: Mapping[str, Any] | None = None,  
    overwrite: bool = True,  
) -> dict[str, Any]:  
    """  
    Persist snapshot artifacts under:  
      {run_output_dir}/snapshots/{snapshot_id}/...  
  
    snapshot_id is deterministic based on:  
      - step_index (if present)  
      - action (if present)  
      - captured_at_utc (if present)  
  
    Returns a small manifest describing written artifact paths (absolute + relative).  
  
    Note: `written_relative` is always POSIX-style (forward slashes) for  
    deterministic, cross-platform JSON outputs.  
    """  
    root = Path(run_output_dir)  
    base = root / "snapshots"  
  
    ctx = snapshot_payload.get("context") if isinstance(snapshot_payload, Mapping) else {}  
    if not isinstance(ctx, Mapping):  
        ctx = {}  
  
    step_index = ctx.get("step_index")  
    action = ctx.get("action")  
    captured_at = snapshot_payload.get("captured_at_utc") if isinstance(snapshot_payload, Mapping) else None  
  
    step_part = f"step_{int(step_index):04d}" if isinstance(step_index, int) else "step_unknown"  
    action_part = _sanitize_segment(action, default="action_unknown")  
    ts_part = _sanitize_segment(captured_at, default="time_unknown", max_len=40)  
  
    snapshot_id = f"{step_part}__{action_part}__{ts_part}"  
    out_dir = base / snapshot_id  
  
    # 1) snapshot.json  
    snapshot_json_path = out_dir / "snapshot.json"  
    _write_bytes(snapshot_json_path, _stable_json_bytes(snapshot_payload), overwrite=overwrite)  
  
    written: dict[str, str] = {  
        "snapshot_json": str(snapshot_json_path),  
    }  
  
    # 2) dom.html (optional convenience)  
    dom_html = None  
    browser = snapshot_payload.get("browser") if isinstance(snapshot_payload, Mapping) else None  
    if isinstance(browser, Mapping):  
        dom_html = browser.get("dom_html")  
    if isinstance(dom_html, str) and dom_html != "":  
        dom_path = out_dir / "dom.html"  
        _write_text(dom_path, dom_html, overwrite=overwrite)  
        written["dom_html"] = str(dom_path)  
  
    # 3) screenshot payload + png (optional)  
    if screenshot_payload is not None:  
        screenshot_json_path = out_dir / "screenshot.json"  
        _write_bytes(screenshot_json_path, _stable_json_bytes(screenshot_payload), overwrite=overwrite)  
        written["screenshot_json"] = str(screenshot_json_path)  
  
        # Only write PNG if present + ok  
        ok = screenshot_payload.get("ok") if isinstance(screenshot_payload, Mapping) else False  
        b64 = screenshot_payload.get("screenshot_b64") if isinstance(screenshot_payload, Mapping) else None  
        if ok is True and isinstance(b64, str) and b64:  
            png_bytes = base64.b64decode(b64.encode("ascii"))  
            png_path = out_dir / "screenshot.png"  
            _write_bytes(png_path, png_bytes, overwrite=overwrite)  
            written["screenshot_png"] = str(png_path)  
  
    # Relative manifest (portable + deterministic across OS)  
    root_resolved = root.resolve()  
    rel_written = {  
        k: Path(v).resolve().relative_to(root_resolved).as_posix()  
        for k, v in written.items()  
    }  
  
    return {  
        "schema": "SNAP-1C",  
        "run_output_dir": str(root),  
        "snapshot_id": snapshot_id,  
        "written": written,  
        "written_relative": rel_written,  
    }  
  
  
def dev_smoke() -> None:  
    # Local deterministic output directory inside repo (safe to delete)  
    repo_root = Path(__file__).resolve().parents[1]  
    out_root = repo_root / "dev" / "_smoke_artifacts" / "10_1_3"  
  
    if out_root.exists():  
        # Deterministic cleanup  
        for p in sorted(out_root.rglob("*"), key=lambda x: str(x), reverse=True):  
            if p.is_file():  
                p.unlink()  
            elif p.is_dir():  
                try:  
                    p.rmdir()  
                except OSError:  
                    pass  
        try:  
            out_root.rmdir()  
        except OSError:  
            pass  
  
    from SNAP.snap_1a_failure_capture import capture_failure_snapshot  
    from SNAP.snap_1b_screenshot_capture import capture_screenshot_payload  
  
    class _FakeDriver:  
        current_url = "https://example.com/app"  
        title = "App"  
        page_source = "<html><body><div id='app'>OK</div></body></html>"  
  
        def execute_script(self, script: str) -> str | None:  
            if script == "return document.readyState":  
                return "complete"  
            return None  
  
        def get_screenshot_as_png(self) -> bytes:  
            return b"\x89PNG\r\n\x1a\nFAKEPNG_10_1_3"  
  
    driver = _FakeDriver()  
    step = {"action": "click_selector", "selector_ref": "app.button.save"}  
    err = ValueError("forced failure")  
  
    snap = capture_failure_snapshot(  
        driver=driver,  
        step=step,  
        error=err,  
        workflow_name="wf",  
        step_index=7,  
        captured_at_utc="2026-01-01T00:00:00+00:00",  
    )  
    shot = capture_screenshot_payload(  
        driver=driver,  
        captured_at_utc="2026-01-01T00:00:00+00:00",  
        label="failure",  
    )  
  
    manifest = persist_snapshot_artifacts(  
        run_output_dir=out_root,  
        snapshot_payload=snap,  
        screenshot_payload=shot,  
        overwrite=True,  
    )  
  
    assert manifest["schema"] == "SNAP-1C"  
    assert manifest["snapshot_id"] == "step_0007__click_selector__2026-01-01T00_00_00_00_00"  
  
    # Deterministic expected files (POSIX relative paths)  
    expected_rel = {  
        "snapshot_json": f"snapshots/{manifest['snapshot_id']}/snapshot.json",  
        "dom_html": f"snapshots/{manifest['snapshot_id']}/dom.html",  
        "screenshot_json": f"snapshots/{manifest['snapshot_id']}/screenshot.json",  
        "screenshot_png": f"snapshots/{manifest['snapshot_id']}/screenshot.png",  
    }  
    assert manifest["written_relative"] == expected_rel  
  
    for _, rel in expected_rel.items():  
        assert (out_root / Path(rel)).exists()  
  
    # Spot-check contents  
    snap_json = (out_root / Path(expected_rel["snapshot_json"])).read_text(encoding="utf-8")  
    assert '"schema": "SNAP-1A"' in snap_json  
    assert "https://example.com/app" in snap_json  
  
    dom_html = (out_root / Path(expected_rel["dom_html"])).read_text(encoding="utf-8")  
    assert "<div id='app'>OK</div>" in dom_html  
  
    png_bytes = (out_root / Path(expected_rel["screenshot_png"])).read_bytes()  
    assert png_bytes == b"\x89PNG\r\n\x1a\nFAKEPNG_10_1_3"  
  
  
if __name__ == "__main__":  
    dev_smoke()  
    print("DEV_SMOKE_OK: SNAP.snap_1c_persist_artifacts")  