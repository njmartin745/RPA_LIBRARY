from __future__ import annotations

import argparse
import html
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

FIXTURE_DIR = REPO_ROOT / "dev" / "fixtures" / "rpa_studio_external_recorder_demo"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "dev" / "_smoke_artifacts" / "rpa_studio_external_recorder"
SCENARIO = "rpa-studio-external-recording-spike"
SUPPORTED_ACTIONS = {"Navigate", "Click", "Type"}


class ExternalRecorderError(RuntimeError):
    pass


class BrowserUnavailable(RuntimeError):
    pass


class _QuietHTTPServer(ThreadingHTTPServer):
    def handle_error(self, request: Any, client_address: Any) -> None:
        exc_type, _exc, _tb = sys.exc_info()
        if exc_type in {ConnectionResetError, BrokenPipeError}:
            return
        super().handle_error(request, client_address)


class _QuietStaticHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(FIXTURE_DIR), **kwargs)

    def log_message(self, format: str, *args: Any) -> None:
        return None


def _write_json(path: Path, obj: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(obj), indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _unique_run_dir(output_root: Path = DEFAULT_OUTPUT_ROOT) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    run_dir = output_root / f"run_{time.time_ns()}_{os.getpid()}"
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def _demo_url(host: str, port: int) -> str:
    return f"http://{host}:{port}/demo/index.html"


def _read_json_body(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("content-length") or "0")
    raw = handler.rfile.read(length).decode("utf-8") if length else "{}"
    obj = json.loads(raw)
    if not isinstance(obj, dict):
        raise ExternalRecorderError("request body must be a JSON object")
    return obj


def _browser_candidates() -> list[str]:
    requested = os.environ.get("RPA_PM15_BROWSER", "").strip().lower()
    if requested:
        if requested not in {"chrome", "edge"}:
            raise ExternalRecorderError("RPA_PM15_BROWSER must be 'chrome' or 'edge'")
        return [requested]
    return ["edge", "chrome"]


def _headless_enabled() -> bool:
    return os.environ.get("RPA_PM15_HEADED", "").strip().lower() not in {"1", "true", "yes", "on"}


def _browser_cfg(browser: str, output_dir: Path, *, headless: bool | None = None) -> dict[str, Any]:
    return {
        "BROWSER": browser,
        "HEADLESS": "true" if (headless if headless is not None else _headless_enabled()) else "false",
        "DOWNLOAD_DIR": str(output_dir / "downloads"),
        "IMPLICIT_WAIT": 0,
        "PAGELOAD_TIMEOUT": 15,
    }


def _looks_browser_unavailable(exc: BaseException) -> bool:
    text = f"{type(exc).__name__}: {exc}".lower()
    markers = (
        "driver not found",
        "unable to obtain driver",
        "cannot find",
        "no such file",
        "session not created",
        "this version of",
        "cannot locate",
        "browser path",
        "chrome failed to start",
        "msedge failed to start",
        "not a valid win32 application",
        "webview2",
    )
    return any(marker in text for marker in markers)


RECORDER_SCRIPT = r"""
(function () {
  if (window.__rpaExternalRecorderInstalled) {
    window.__rpaExternalRecorderActive = true;
    return { ok: true, alreadyInstalled: true };
  }
  window.__rpaExternalRecorderInstalled = true;
  window.__rpaExternalRecorderActive = true;
  window.__rpaRecorderEvents = [];
  window.__rpaRecorderOrder = 0;

  function selectorFor(el) {
    if (!el || !el.tagName) return "";
    if (el.id) return "#" + CSS.escape(el.id);
    if (el.getAttribute("name")) return el.tagName.toLowerCase() + "[name='" + CSS.escape(el.getAttribute("name")) + "']";
    if (el.getAttribute("data-testid")) return "[data-testid='" + CSS.escape(el.getAttribute("data-testid")) + "']";
    if (el.getAttribute("aria-label")) return el.tagName.toLowerCase() + "[aria-label='" + CSS.escape(el.getAttribute("aria-label")) + "']";
    if (el.getAttribute("placeholder")) return el.tagName.toLowerCase() + "[placeholder='" + CSS.escape(el.getAttribute("placeholder")) + "']";
    return el.tagName.toLowerCase();
  }

  function labelFor(el) {
    if (!el) return "";
    return (el.getAttribute("aria-label") || el.getAttribute("placeholder") || el.innerText || el.value || "").toString().slice(0, 80);
  }

  function pushAction(action) {
    action.order = ++window.__rpaRecorderOrder;
    action.timestamp_ms = Date.now();
    action.source_url = window.location.href;
    window.__rpaRecorderEvents.push(action);
  }

  function pushOrReplaceType(action) {
    var events = window.__rpaRecorderEvents;
    var previous = events[events.length - 1];
    if (previous && previous.type === "Type" && previous.selector === action.selector) {
      action.order = previous.order;
      action.timestamp_ms = Date.now();
      action.source_url = window.location.href;
      events[events.length - 1] = action;
      return;
    }
    pushAction(action);
  }

  document.addEventListener("click", function (event) {
    if (!window.__rpaExternalRecorderActive) return;
    var el = event.target;
    if (!el || el.type === "password" || el.type === "hidden") return;
    pushAction({ type: "Click", selector: selectorFor(el), label: labelFor(el) });
  }, true);

  document.addEventListener("input", function (event) {
    if (!window.__rpaExternalRecorderActive) return;
    var el = event.target;
    if (!el || el.type === "hidden") return;
    if (el.type === "password") {
      pushOrReplaceType({ type: "Type", selector: selectorFor(el), label: "password field redacted", redacted: true });
      return;
    }
    pushOrReplaceType({ type: "Type", selector: selectorFor(el), text: String(el.value || ""), label: labelFor(el), redacted: false });
  }, true);

  return { ok: true, alreadyInstalled: false };
})();
"""


def _normalize_actions(actions: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for raw in actions:
        action_type = raw.get("type")
        if action_type not in SUPPORTED_ACTIONS:
            continue
        selector = raw.get("selector")
        action: dict[str, Any] = {
            "type": str(action_type),
            "selector": str(selector or ""),
            "label": str(raw.get("label") or "")[:120],
            "order": int(raw.get("order") or len(normalized) + 1),
            "timestamp_ms": int(raw.get("timestamp_ms") or 0),
            "source_url": str(raw.get("source_url") or ""),
        }
        if action_type == "Type":
            action["redacted"] = bool(raw.get("redacted"))
            if action["redacted"]:
                action["text"] = None
            else:
                action["text"] = str(raw.get("text") or "")
        normalized.append(action)
    return normalized


def _validate_actions(actions: Sequence[Mapping[str, Any]]) -> None:
    if not actions:
        raise ExternalRecorderError("at least one action is required")
    has_click = False
    has_type = False
    for index, action in enumerate(actions):
        action_type = action.get("type")
        if action_type not in SUPPORTED_ACTIONS:
            raise ExternalRecorderError(f"unsupported action at index {index}: {action_type!r}")
        if action_type in {"Click", "Type"}:
            selector = action.get("selector")
            if not isinstance(selector, str) or not selector.strip():
                raise ExternalRecorderError(f"action {index} requires selector")
        if action_type == "Click":
            has_click = True
        if action_type == "Type":
            has_type = True
            if action.get("redacted") is not True and not isinstance(action.get("text"), str):
                raise ExternalRecorderError(f"type action {index} requires text unless redacted")
    if not has_click or not has_type:
        raise ExternalRecorderError("recording must include at least one Click and one Type action")


def workflow_from_actions(actions: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    normalized = _normalize_actions(actions)
    _validate_actions(normalized)
    return {
        "schema_id": "RPA_STUDIO_EXTERNAL_RECORDER_WORKFLOW_1A",
        "name": "rpa_studio_external_recorder_spike",
        "scenario": SCENARIO,
        "runtime_scope": "experimental_external_recording_only",
        "replay_supported": False,
        "actions": normalized,
    }


def save_workflow(actions: Sequence[Mapping[str, Any]], *, output_root: Path = DEFAULT_OUTPUT_ROOT) -> dict[str, Any]:
    workflow = workflow_from_actions(actions)
    run_dir = _unique_run_dir(output_root)
    workflow_path = run_dir / "workflow" / "recorded_workflow.json"
    log_path = run_dir / "logs" / "run.jsonl"
    _write_json(workflow_path, workflow)
    logs = [
        {"event": "workflow_saved", "scenario": SCENARIO, "action_count": len(workflow["actions"]), "timestamp_ms": int(time.time() * 1000)},
        {"event": "external_replay_deferred", "scenario": SCENARIO, "timestamp_ms": int(time.time() * 1000)},
    ]
    _write_text(log_path, "".join(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n" for row in logs))
    return {
        "status": "saved",
        "scenario": SCENARIO,
        "run_dir": str(run_dir.resolve()),
        "workflow_json": str(workflow_path.resolve()),
        "artifacts": [str(workflow_path.resolve()), str(log_path.resolve())],
        "action_count": len(workflow["actions"]),
        "message": "Saved workflow JSON. External replay is deferred.",
    }


class ExternalRecorderSession:
    def __init__(self) -> None:
        self.driver: Any | None = None
        self.browser: str | None = None
        self.actions: list[dict[str, Any]] = []
        self.recording = False
        self.message = "No browser session."
        self.lock = threading.Lock()

    def close(self) -> None:
        with self.lock:
            driver = self.driver
            self.driver = None
            self.recording = False
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass

    def launch(self, *, url: str, browser: str, headed: bool, output_root: Path = DEFAULT_OUTPUT_ROOT) -> dict[str, Any]:
        from ENTRY.entry_1a_webdriver_bootstrap import make_driver

        self.close()
        run_dir = _unique_run_dir(output_root) / "browser"
        cfg = _browser_cfg(browser, run_dir, headless=not headed)
        try:
            driver = make_driver(cfg)
            driver.get(url)
        except Exception as exc:
            if _looks_browser_unavailable(exc):
                raise BrowserUnavailable(str(exc)) from exc
            raise
        with self.lock:
            self.driver = driver
            self.browser = browser
            self.actions = [{"type": "Navigate", "url": url, "source_url": url, "order": 1, "timestamp_ms": int(time.time() * 1000), "label": "Open page"}]
            self.recording = False
            self.message = f"Launched {browser} controlled browser."
        return {"status": "launched", "browser": browser, "current_url": driver.current_url, "message": self.message}

    def inject_recorder(self) -> dict[str, Any]:
        with self.lock:
            driver = self.driver
        if driver is None:
            raise ExternalRecorderError("browser session is not launched")
        try:
            result = driver.execute_script(RECORDER_SCRIPT)
        except Exception as exc:
            raise ExternalRecorderError(f"recorder injection failed: {type(exc).__name__}: {exc}") from exc
        with self.lock:
            self.recording = True
            self.message = "Recording active. Interact with the controlled browser page."
        return {"status": "recording", "injection": result, "message": self.message}

    def stop(self) -> dict[str, Any]:
        with self.lock:
            driver = self.driver
            self.recording = False
        if driver is not None:
            try:
                driver.execute_script("window.__rpaExternalRecorderActive = false;")
            except Exception:
                pass
        return {"status": "stopped", "action_count": len(self.actions), "message": "Recording stopped."}

    def poll_actions(self) -> list[dict[str, Any]]:
        with self.lock:
            driver = self.driver
        if driver is None:
            return list(self.actions)
        try:
            raw = driver.execute_script("return window.__rpaRecorderEvents || [];")
        except Exception:
            raw = []
        if isinstance(raw, list):
            captured = _normalize_actions([row for row in raw if isinstance(row, Mapping)])
            with self.lock:
                nav = [row for row in self.actions if row.get("type") == "Navigate"][:1]
                self.actions = nav + captured
        return list(self.actions)


SESSION = ExternalRecorderSession()


def _studio_html(host: str, port: int) -> str:
    demo = html.escape(_demo_url(host, port))
    return f"""<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
    <title>RPA Studio External Recorder</title>
    <style>
      body {{ margin: 0; font-family: Arial, sans-serif; background: #eef2f6; color: #182534; }}
      header {{ background: #123b5d; color: #fff; padding: 18px 22px; }}
      main {{ display: grid; grid-template-columns: 360px minmax(520px, 1fr); gap: 14px; padding: 14px; }}
      section {{ background: #fff; border: 1px solid #d6dee8; border-radius: 8px; padding: 14px; }}
      button {{ border: 0; border-radius: 6px; background: #1769aa; color: white; cursor: pointer; font-weight: 700; margin: 5px 4px 5px 0; padding: 8px 10px; }}
      button.secondary {{ background: #586677; }}
      button.danger {{ background: #9b2d30; }}
      input, select {{ box-sizing: border-box; border: 1px solid #aab6c5; border-radius: 6px; padding: 8px; width: 100%; }}
      textarea, pre {{ box-sizing: border-box; width: 100%; min-height: 220px; overflow: auto; white-space: pre-wrap; background: #f8fafc; border: 1px solid #d6dee8; border-radius: 6px; padding: 10px; }}
      .notice {{ background: #fff7d6; border: 1px solid #dec35f; border-radius: 6px; padding: 9px; }}
      .actions {{ padding-left: 20px; }}
      .actions li {{ margin-bottom: 8px; }}
      @media (max-width: 980px) {{ main {{ grid-template-columns: 1fr; }} }}
    </style>
  </head>
  <body>
    <header>
      <h1>RPA Studio External Recorder</h1>
      <p>Experimental controlled-browser recording spike. Replay and production external automation are deferred.</p>
    </header>
    <main>
      <section>
        <h2>External Recording Controls</h2>
        <div class=\"notice\">Experimental: PM15 records Click and Type actions only when WebDriver script injection is allowed. It does not prove external replay, universal website support, credentials, downloads, checkout/payment, CAPTCHA, anti-bot bypass, retry/resume, scheduling, or multi-agent execution.</div>
        <label for=\"target-url\">URL</label>
        <input id=\"target-url\" value=\"{demo}\" aria-label=\"Target URL\">
        <label for=\"browser\">Browser</label>
        <select id=\"browser\"><option value=\"edge\">Edge</option><option value=\"chrome\">Chrome</option></select>
        <label><input id=\"headed\" type=\"checkbox\"> Headed debug browser</label>
        <button id=\"launch\">Launch Controlled Browser</button>
        <button id=\"start-recording\">Start Recording</button>
        <button id=\"stop-recording\" class=\"secondary\">Stop Recording</button>
        <button id=\"save-workflow\">Save workflow JSON</button>
        <button id=\"close-browser\" class=\"danger\">Close Browser</button>
        <p id=\"status\">No browser launched.</p>
        <h3>Recorded Actions</h3>
        <ol id=\"actions\" class=\"actions\"></ol>
      </section>
      <section>
        <h2>Workflow JSON Preview</h2>
        <textarea id=\"workflow-json\" spellcheck=\"false\"></textarea>
        <h2>Live Log</h2>
        <pre id=\"live-log\">Ready.</pre>
        <h2>Saved Evidence</h2>
        <pre id=\"evidence\">No workflow saved yet.</pre>
      </section>
    </main>
    <script>
      let actions = [];
      let polling = false;
      const actionsEl = document.getElementById('actions');
      const jsonEl = document.getElementById('workflow-json');
      const logEl = document.getElementById('live-log');
      const statusEl = document.getElementById('status');
      const evidenceEl = document.getElementById('evidence');

      function log(line) {{
        logEl.textContent += '\\n' + new Date().toISOString() + ' ' + line;
        logEl.scrollTop = logEl.scrollHeight;
      }}
      function render() {{
        actionsEl.innerHTML = '';
        actions.forEach((action) => {{
          const li = document.createElement('li');
          li.textContent = `${{action.order || ''}} ${{action.type}} ${{action.selector || action.url || ''}} ${{action.text ? '= ' + action.text : action.redacted ? '= [redacted]' : ''}}`;
          actionsEl.appendChild(li);
        }});
        jsonEl.value = JSON.stringify({{ schema_id: 'RPA_STUDIO_EXTERNAL_RECORDER_WORKFLOW_1A', scenario: '{SCENARIO}', replay_supported: false, actions }}, null, 2);
      }}
      async function pollEvents() {{
        if (!polling) return;
        const res = await fetch('/api/events');
        const data = await res.json();
        actions = data.actions || [];
        render();
        setTimeout(pollEvents, 800);
      }}
      document.getElementById('launch').addEventListener('click', async () => {{
        const body = {{ url: document.getElementById('target-url').value, browser: document.getElementById('browser').value, headed: document.getElementById('headed').checked }};
        const res = await fetch('/api/launch', {{ method: 'POST', headers: {{ 'content-type': 'application/json' }}, body: JSON.stringify(body) }});
        const data = await res.json();
        statusEl.textContent = data.message || data.status;
        log(JSON.stringify(data));
      }});
      document.getElementById('start-recording').addEventListener('click', async () => {{
        const res = await fetch('/api/start-recording', {{ method: 'POST' }});
        const data = await res.json();
        statusEl.textContent = data.message || data.status;
        log(JSON.stringify(data));
        polling = res.ok;
        if (polling) pollEvents();
      }});
      document.getElementById('stop-recording').addEventListener('click', async () => {{
        polling = false;
        const res = await fetch('/api/stop-recording', {{ method: 'POST' }});
        const data = await res.json();
        statusEl.textContent = data.message || data.status;
        log(JSON.stringify(data));
      }});
      document.getElementById('save-workflow').addEventListener('click', async () => {{
        const res = await fetch('/api/save-workflow', {{ method: 'POST', headers: {{ 'content-type': 'application/json' }}, body: JSON.stringify({{ actions }}) }});
        const data = await res.json();
        evidenceEl.textContent = JSON.stringify(data, null, 2);
        log('workflow save: ' + (data.workflow_json || data.message));
      }});
      document.getElementById('close-browser').addEventListener('click', async () => {{
        polling = false;
        const res = await fetch('/api/close-browser', {{ method: 'POST' }});
        const data = await res.json();
        statusEl.textContent = data.message || data.status;
        log(JSON.stringify(data));
      }});
      render();
    </script>
  </body>
</html>"""


class ExternalRecorderRequestHandler(BaseHTTPRequestHandler):
    server_version = "RPAStudioExternalRecorder/1.0"

    def log_message(self, format: str, *args: Any) -> None:
        return None

    def _send_json(self, obj: Mapping[str, Any], status: int = 200) -> None:
        payload = json.dumps(dict(obj), indent=2, sort_keys=True, ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_html(self, body: str) -> None:
        payload = body.encode("utf-8")
        self.send_response(200)
        self.send_header("content-type", "text/html; charset=utf-8")
        self.send_header("content-length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            host, port = self.server.server_address  # type: ignore[attr-defined]
            self._send_html(_studio_html(str(host), int(port)))
            return
        if parsed.path == "/api/events":
            self._send_json({"status": "ok", "actions": SESSION.poll_actions()})
            return
        if parsed.path.startswith("/demo/"):
            rel = parsed.path[len("/demo/"):]
            target = (FIXTURE_DIR / rel).resolve()
            if not str(target).startswith(str(FIXTURE_DIR.resolve())) or not target.exists():
                self.send_error(404)
                return
            content_type = "text/html; charset=utf-8" if target.suffix == ".html" else "text/plain; charset=utf-8"
            data = target.read_bytes()
            self.send_response(200)
            self.send_header("content-type", content_type)
            self.send_header("content-length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        self.send_error(404)

    def do_POST(self) -> None:
        try:
            parsed = urlparse(self.path)
            if parsed.path == "/api/launch":
                body = _read_json_body(self)
                url = str(body.get("url") or "").strip()
                if not url:
                    host, port = self.server.server_address  # type: ignore[attr-defined]
                    url = _demo_url(str(host), int(port))
                browser = str(body.get("browser") or "edge").strip().lower()
                if browser not in {"edge", "chrome"}:
                    raise ExternalRecorderError("browser must be edge or chrome")
                result = SESSION.launch(url=url, browser=browser, headed=bool(body.get("headed")))
                self._send_json(result)
                return
            if parsed.path == "/api/start-recording":
                self._send_json(SESSION.inject_recorder())
                return
            if parsed.path == "/api/stop-recording":
                self._send_json(SESSION.stop())
                return
            if parsed.path == "/api/save-workflow":
                body = _read_json_body(self)
                actions = body.get("actions")
                if not isinstance(actions, list):
                    actions = SESSION.poll_actions()
                self._send_json(save_workflow(actions))
                return
            if parsed.path == "/api/close-browser":
                SESSION.close()
                self._send_json({"status": "closed", "message": "Controlled browser closed."})
                return
            self.send_error(404)
        except BrowserUnavailable as exc:
            self._send_json({"status": "skip", "message": f"real browser unavailable: {exc}"}, status=503)
        except Exception as exc:
            self._send_json({"status": "fail", "message": f"{type(exc).__name__}: {exc}"}, status=500)


def start_fixture_server() -> tuple[ThreadingHTTPServer, threading.Thread, str]:
    httpd = _QuietHTTPServer(("127.0.0.1", 0), _QuietStaticHandler)
    host, port = httpd.server_address
    thread = threading.Thread(target=httpd.serve_forever, name="pm15-fixture-server", daemon=True)
    thread.start()
    return httpd, thread, f"http://{host}:{port}/index.html"


def _select_available_browser(output_root: Path) -> str:
    from ENTRY.entry_1a_webdriver_bootstrap import make_driver

    unavailable: list[str] = []
    for browser in _browser_candidates():
        driver = None
        try:
            driver = make_driver(_browser_cfg(browser, output_root / browser / "preflight"))
            return browser
        except Exception as exc:
            if _looks_browser_unavailable(exc):
                unavailable.append(f"{browser}: {type(exc).__name__}: {exc}")
                continue
            raise
        finally:
            if driver is not None:
                driver.quit()
    raise BrowserUnavailable("; ".join(unavailable) or "no compatible browser candidate succeeded")


def run_controlled_recording_smoke(*, output_root: Path = DEFAULT_OUTPUT_ROOT) -> dict[str, Any]:
    from selenium.webdriver.common.by import By

    httpd, _thread, site_url = start_fixture_server()
    session = ExternalRecorderSession()
    try:
        browser = _select_available_browser(output_root)
        launch = session.launch(url=site_url, browser=browser, headed=False, output_root=output_root)
        session.inject_recorder()
        if session.driver is None:
            raise ExternalRecorderError("driver missing after launch")
        driver = session.driver
        message = "Hello from PM15"
        input_el = driver.find_element(By.ID, "external-message")
        input_el.send_keys("H")
        input_el.send_keys("ello")
        input_el.send_keys(" from")
        input_el.send_keys(" PM15")
        password_el = driver.find_element(By.ID, "external-secret")
        password_el.send_keys("DoNotCapture123!")
        button = driver.find_element(By.ID, "external-submit")
        button.click()
        time.sleep(0.5)
        actions = session.poll_actions()
        result = save_workflow(actions, output_root=output_root)
        result["browser"] = browser
        result["launch"] = launch
        result["actions"] = actions
        result["site_url"] = site_url
        result["typed_message"] = message
        return result
    finally:
        session.close()
        httpd.shutdown()
        httpd.server_close()


def serve(host: str = "127.0.0.1", port: int = 8879) -> None:
    httpd = _QuietHTTPServer((host, port), ExternalRecorderRequestHandler)
    actual_host, actual_port = httpd.server_address
    print(f"RPA Studio External Recorder: http://{actual_host}:{actual_port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nRPA Studio External Recorder stopped.")
    finally:
        SESSION.close()
        httpd.server_close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rpa-studio-external-recorder")
    sub = parser.add_subparsers(dest="command", required=False)
    serve_cmd = sub.add_parser("serve", help="Launch the PM15 external recorder Studio UI.")
    serve_cmd.add_argument("--host", default="127.0.0.1")
    serve_cmd.add_argument("--port", type=int, default=8879)
    smoke_cmd = sub.add_parser("run-controlled-smoke", help="Run deterministic PM15 WebDriver recording helper.")
    smoke_cmd.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.command in {None, "serve"}:
        serve(host=getattr(args, "host", "127.0.0.1"), port=getattr(args, "port", 8879))
        return 0
    if args.command == "run-controlled-smoke":
        try:
            result = run_controlled_recording_smoke()
        except BrowserUnavailable as exc:
            print(f"SKIP: production_milestone_15 real browser unavailable: {exc}")
            return 2
        if args.as_json:
            print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True))
        else:
            print("PASS: production_milestone_15 external recording spike")
            print(f"workflow_json: {result['workflow_json']}")
        return 0
    parser.error(f"Unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
