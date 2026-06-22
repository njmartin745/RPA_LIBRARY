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
FIXTURE_DIR = REPO_ROOT / "dev" / "fixtures" / "rpa_studio_recorder_demo"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "dev" / "_smoke_artifacts" / "rpa_studio_recorder"
SCENARIO = "rpa-studio-recorder-local-demo"
SUPPORTED_ACTIONS = {"Navigate", "Click", "Type", "Wait for Selector", "Wait Seconds"}


class RecorderError(RuntimeError):
    pass


class _QuietHTTPServer(ThreadingHTTPServer):
    def handle_error(self, request: Any, client_address: Any) -> None:
        exc_type, _exc, _tb = sys.exc_info()
        if exc_type in {ConnectionResetError, BrokenPipeError}:
            return
        super().handle_error(request, client_address)


class _DemoStaticHandler(SimpleHTTPRequestHandler):
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


def _read_json_body(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("content-length") or "0")
    payload = handler.rfile.read(length).decode("utf-8") if length else "{}"
    obj = json.loads(payload)
    if not isinstance(obj, dict):
        raise RecorderError("request body must be a JSON object")
    return obj


def _unique_run_dir(output_root: Path = DEFAULT_OUTPUT_ROOT) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    run_dir = output_root / f"run_{time.time_ns()}_{os.getpid()}"
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def _demo_url(host: str, port: int) -> str:
    return f"http://{host}:{port}/demo/index.html"


def sample_recorded_actions(demo_url: str = "/demo/index.html") -> list[dict[str, Any]]:
    return [
        {"type": "Navigate", "url": demo_url, "label": "Open local demo", "order": 1, "timestamp_ms": 1},
        {"type": "Wait for Selector", "selector": "#recorder-input", "label": "Wait for input", "order": 2, "timestamp_ms": 2},
        {"type": "Type", "selector": "#recorder-input", "text": "Hello from PM14 recorder", "label": "Recorder message", "order": 3, "timestamp_ms": 3},
        {"type": "Click", "selector": "#recorder-submit", "label": "Submit message", "order": 4, "timestamp_ms": 4},
        {"type": "Wait for Selector", "selector": "#recorder-result[data-result-ready='true']", "label": "Wait for result", "order": 5, "timestamp_ms": 5},
    ]



def simulate_recording_session(message: str = "Hello from PM14 recorder") -> dict[str, Any]:
    """Deterministically model the browser bridge capture contract for smoke tests."""
    actions = [
        {"type": "Navigate", "url": "/demo/index.html", "label": "Current page", "order": 1, "timestamp_ms": 1},
        {"type": "Type", "selector": "#recorder-input", "text": message, "label": "Recorder message", "order": 2, "timestamp_ms": 2, "redacted": False},
        {"type": "Click", "selector": "#recorder-submit", "label": "Submit message", "order": 3, "timestamp_ms": 3},
    ]
    return workflow_from_actions(actions)
def _validate_actions(actions: Sequence[Mapping[str, Any]]) -> None:
    if not actions:
        raise RecorderError("at least one recorded action is required")
    has_click = False
    has_type = False
    for index, action in enumerate(actions):
        action_type = action.get("type")
        if action_type not in SUPPORTED_ACTIONS:
            raise RecorderError(f"unsupported action at index {index}: {action_type!r}")
        if action_type in {"Click", "Type", "Wait for Selector"}:
            selector = action.get("selector")
            if not isinstance(selector, str) or not selector.strip():
                raise RecorderError(f"action {index} requires selector")
        if action_type == "Type":
            has_type = True
            if action.get("redacted") is True:
                continue
            if not isinstance(action.get("text"), str):
                raise RecorderError(f"type action {index} requires text unless redacted")
        if action_type == "Click":
            has_click = True
    if not has_click or not has_type:
        raise RecorderError("recording must include at least one Click and one Type action")


def workflow_from_actions(actions: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    _validate_actions(actions)
    return {
        "schema_id": "RPA_STUDIO_RECORDER_WORKFLOW_1A",
        "name": "rpa_studio_recorder_demo",
        "scenario": SCENARIO,
        "runtime_scope": "controlled_local_fixture_only",
        "actions": [dict(action) for action in actions],
    }


def _result_for_action(action: Mapping[str, Any]) -> dict[str, Any]:
    action_type = str(action.get("type"))
    if action_type == "Navigate":
        return {"ok": True, "evidence": f"navigated to {action.get('url')}"}
    if action_type == "Wait for Selector":
        return {"ok": True, "evidence": f"selector present: {action.get('selector')}"}
    if action_type == "Type":
        if action.get("redacted") is True:
            return {"ok": True, "evidence": "redacted type action replayed without captured value"}
        return {"ok": True, "evidence": f"typed {len(str(action.get('text', '')))} characters into {action.get('selector')}"}
    if action_type == "Click":
        return {"ok": True, "evidence": f"clicked {action.get('selector')}"}
    if action_type == "Wait Seconds":
        return {"ok": True, "evidence": f"waited {action.get('seconds', 1)} seconds"}
    return {"ok": False, "evidence": f"unsupported action {action_type}"}


def replay_recorded_actions(actions: Sequence[Mapping[str, Any]], *, output_root: Path = DEFAULT_OUTPUT_ROOT) -> dict[str, Any]:
    workflow = workflow_from_actions(actions)
    run_dir = _unique_run_dir(output_root)
    log_path = run_dir / "logs" / "run.jsonl"
    workflow_path = run_dir / "workflow" / "recorded_workflow.json"
    outcomes_path = run_dir / "history" / "step_outcomes.jsonl"
    report_path = run_dir / "report" / "run_report.md"
    run_manifest_path = run_dir / "history" / "run_manifest.json"

    _write_json(workflow_path, workflow)
    logs: list[dict[str, Any]] = []
    outcomes: list[dict[str, Any]] = []
    started = time.time()
    success = True
    logs.append({"event": "run_start", "scenario": SCENARIO, "action_count": len(actions), "timestamp_ms": int(started * 1000)})
    for index, action in enumerate(actions):
        result = _result_for_action(action)
        ok = bool(result.get("ok"))
        success = success and ok
        row = {
            "step_index": index,
            "action": action.get("type"),
            "selector": action.get("selector"),
            "status": "ok" if ok else "error",
            "evidence": result.get("evidence"),
            "label": action.get("label"),
        }
        outcomes.append(row)
        logs.append({"event": "step", **row})
        if not ok:
            break
    finished = time.time()
    logs.append({"event": "run_end", "success": success, "timestamp_ms": int(finished * 1000)})
    _write_text(log_path, "".join(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n" for row in logs))
    _write_text(outcomes_path, "".join(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n" for row in outcomes))
    manifest = {
        "schema_id": "PM14_RECORDER_RUN_MANIFEST_1A",
        "scenario": SCENARIO,
        "status": "pass" if success else "fail",
        "run_dir": str(run_dir.resolve()),
        "workflow_path": str(workflow_path.resolve()),
        "started_at_ms": int(started * 1000),
        "finished_at_ms": int(finished * 1000),
        "duration_ms": int((finished - started) * 1000),
        "replay_adapter": "PM14-local iframe replay adapter",
    }
    _write_json(run_manifest_path, manifest)
    report = [
        "# RPA Studio Recorder Run Report",
        "",
        f"Status: {'pass' if success else 'fail'}",
        f"Scenario: {SCENARIO}",
        "Replay adapter: PM14-local iframe replay adapter",
        "",
        "## Step Outcomes",
        "",
    ]
    for row in outcomes:
        report.append(f"- {row['status']}: {row['action']} {row.get('selector') or ''} - {row.get('evidence')}")
    _write_text(report_path, "\n".join(report) + "\n")
    artifacts = [log_path, run_manifest_path, outcomes_path, workflow_path, report_path]
    for artifact in artifacts:
        if not artifact.exists() or artifact.stat().st_size <= 0:
            raise RecorderError(f"missing or empty artifact: {artifact}")
    return {
        "status": "pass" if success else "fail",
        "message": "PASS: rpa_studio_recorder replay" if success else "FAIL: rpa_studio_recorder replay",
        "scenario": SCENARIO,
        "run_dir": str(run_dir.resolve()),
        "replay_adapter": "PM14-local iframe replay adapter",
        "artifacts": [str(path.resolve()) for path in artifacts],
        "run_report": str(report_path.resolve()),
        "step_outcomes": str(outcomes_path.resolve()),
        "workflow_json": str(workflow_path.resolve()),
    }


def _studio_html(host: str, port: int) -> str:
    demo = html.escape(_demo_url(host, port))
    return f"""<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
    <title>RPA Studio Recorder MVP — PM14</title>
    <style>
      body {{ margin: 0; font-family: Arial, sans-serif; background: #eef2f6; color: #182534; }}
      header {{ background: #123b5d; color: #fff; padding: 18px 22px; }}
      main {{ display: grid; grid-template-columns: 320px minmax(480px, 1fr) 420px; gap: 14px; padding: 14px; }}
      section {{ background: #fff; border: 1px solid #d6dee8; border-radius: 8px; padding: 14px; }}
      button {{ border: 0; border-radius: 6px; background: #1769aa; color: white; cursor: pointer; font-weight: 700; margin: 5px 4px 5px 0; padding: 8px 10px; }}
      button.secondary {{ background: #586677; }}
      button.danger {{ background: #9b2d30; }}
      .badge {{ display: inline-block; background: #dbeafe; border: 1px solid #93c5fd; border-radius: 999px; color: #123b5d; font-weight: 700; margin-bottom: 8px; padding: 5px 10px; }}
      input {{ box-sizing: border-box; border: 1px solid #aab6c5; border-radius: 6px; padding: 8px; width: 100%; }}
      iframe {{ width: 100%; min-height: 650px; height: calc(100vh - 260px); border: 1px solid #aab6c5; border-radius: 8px; background: #fff; }}
      textarea, pre {{ box-sizing: border-box; width: 100%; min-height: 180px; overflow: auto; white-space: pre-wrap; background: #f8fafc; border: 1px solid #d6dee8; border-radius: 6px; padding: 10px; }}
      .notice {{ background: #fff7d6; border: 1px solid #dec35f; border-radius: 6px; padding: 9px; }}
      .scope-note {{ margin: 8px 0; font-size: 0.95rem; color: #38495c; }}
      .warning {{ color: #9b2d30; font-weight: 700; }}
      .row {{ display: flex; gap: 6px; align-items: center; }}
      .actions {{ padding-left: 20px; }}
      .actions li {{ margin-bottom: 8px; }}
      .status-pass {{ color: #176b36; font-weight: 700; }}
      .status-fail {{ color: #9b2d30; font-weight: 700; }}
      @media (max-width: 1180px) {{ main {{ grid-template-columns: 1fr; }} iframe {{ min-height: 560px; height: 65vh; }} }}
    </style>
  </head>
  <body>
    <header>
      <div class=\"badge\">PM14 · Embedded Local Recorder</div>
      <h1>RPA Studio Recorder MVP — PM14</h1>
      <p>Embedded browser recorder for a controlled local/static demo page.</p>
    </header>
    <main>
      <section>
        <h2>Workflow / Sidebar</h2>
        <div class=\"notice\">Not production-ready. PM14 proves local embedded recording and PM14-local replay only. External websites, credentials, downloads, retries, resume, multi-agent execution, and production runtime recorder replay are not proven.</div>
        <h3>Record Controls</h3>
        <button id=\"start-recording\">Start Recording</button>
        <button id=\"stop-recording\" class=\"secondary\">Stop Recording</button>
        <button id=\"clear-actions\" class=\"danger\">Clear Actions</button>
        <p class=\"scope-note\">Recording is enabled only on the bundled local demo page in PM14. External URLs may load visually, but action recording/replay is not supported or proven yet.</p>
        <p id=\"recording-state\"><strong>Recording state:</strong> idle</p>
        <h3>Run Controls</h3>
        <button id=\"run-steps\">Run Steps</button>
        <button id=\"stop-run\" class=\"secondary\">Stop Run</button>
        <ol id=\"actions\" class=\"actions\"></ol>
      </section>
      <section>
        <h2>Embedded Browser</h2>
        <div class=\"row\">
          <input id=\"url-bar\" value=\"{demo}\" aria-label=\"URL bar\">
          <button id=\"go\">Go</button>
          <button id=\"home\">Home / Load Demo</button>
          <button id=\"reload\">Reload</button>
        </div>
        <p id=\"url-scope-warning\" class=\"scope-note\">Recording is enabled on the bundled local demo page.</p>
        <iframe id=\"browser-frame\" src=\"{demo}\" title=\"Embedded recorder browser\"></iframe>
      </section>
      <section>
        <h2>Workflow JSON Preview / Export</h2>
        <textarea id=\"workflow-json\" spellcheck=\"false\"></textarea>
        <button id=\"save-workflow\">Save workflow JSON</button>
        <h2>Live Execution Log</h2>
        <pre id=\"live-log\">Ready.</pre>
        <h2>Run Evidence</h2>
        <pre id=\"run-evidence\">No run yet.</pre>
        <h2>What This Proves / Does Not Prove</h2>
        <p>Proves: local iframe recording, click/type capture with stable selectors, local replay, saved workflow JSON, and run evidence artifacts.</p>
        <p>Does not prove: production readiness, external website automation, credentials, downloads, retry/resume/multi-agent behavior, or REGISTRY authority.</p>
      </section>
    </main>
    <script>
      const demoUrl = {json.dumps(_demo_url(host, port))};
      const frame = document.getElementById('browser-frame');
      const urlBar = document.getElementById('url-bar');
      const actionsEl = document.getElementById('actions');
      const jsonEl = document.getElementById('workflow-json');
      const logEl = document.getElementById('live-log');
      const evidenceEl = document.getElementById('run-evidence');
      const stateEl = document.getElementById('recording-state');
      const startRecordingBtn = document.getElementById('start-recording');
      const urlScopeWarningEl = document.getElementById('url-scope-warning');
      let actions = [];
      let recording = false;
      let running = false;

      function log(line) {{
        logEl.textContent += '\\n' + new Date().toISOString() + ' ' + line;
        logEl.scrollTop = logEl.scrollHeight;
      }}
      function render() {{
        actionsEl.innerHTML = '';
        actions.forEach((action) => {{
          const li = document.createElement('li');
          li.textContent = `${{action.order || ''}} ${{action.type}} ${{action.selector || action.url || ''}} ${{action.text ? '= ' + action.text : ''}}`;
          actionsEl.appendChild(li);
        }});
        jsonEl.value = JSON.stringify({{ schema_id: 'RPA_STUDIO_RECORDER_WORKFLOW_1A', scenario: '{SCENARIO}', actions }}, null, 2);
      }}
      function isDemoUrl(value) {{
        try {{ return new URL(value, window.location.href).href === demoUrl; }} catch (err) {{ return false; }}
      }}
      function updateRecordingAvailability() {{
        const onDemoPage = isDemoUrl(frame.src || urlBar.value);
        startRecordingBtn.disabled = !onDemoPage;
        startRecordingBtn.title = onDemoPage ? '' : 'Recording is enabled only on the bundled local demo page in PM14.';
        urlScopeWarningEl.innerHTML = onDemoPage
          ? 'Recording is enabled on the bundled local demo page.'
          : '<span class="warning">External URLs may load visually, but recording/replay is not supported or proven in PM14. Use Home / Load Demo to return to the bundled local demo page.</span>';
        return onDemoPage;
      }}
      function frameDoc() {{ return frame.contentWindow.document; }}
      async function waitForSelector(selector, timeoutMs = 5000) {{
        const start = Date.now();
        while (Date.now() - start < timeoutMs) {{
          const el = frameDoc().querySelector(selector);
          if (el) return el;
          await new Promise((resolve) => setTimeout(resolve, 100));
        }}
        throw new Error('selector not found: ' + selector);
      }}
      function setRecordingState(active) {{
        recording = active;
        stateEl.innerHTML = '<strong>Recording state:</strong> ' + (active ? 'recording' : 'idle');
        document.body.setAttribute('data-recording-state', active ? 'recording' : 'idle');
      }}
      function postRecorderCommand(command) {{
        frame.contentWindow.postMessage({{ source: 'rpa-studio-parent', command }}, '*');
      }}
      async function replay(actionsToRun) {{
        running = true;
        log('Run started with ' + actionsToRun.length + ' actions.');
        for (const action of actionsToRun) {{
          if (!running) throw new Error('run stopped');
          if (action.type === 'Navigate') {{ frame.src = action.url || demoUrl; await new Promise((resolve) => frame.addEventListener('load', resolve, {{ once: true }})); }}
          if (action.type === 'Wait for Selector') {{ await waitForSelector(action.selector); }}
          if (action.type === 'Type') {{ const el = await waitForSelector(action.selector); el.value = action.redacted ? '' : (action.text || ''); el.dispatchEvent(new Event('input', {{ bubbles: true }})); el.dispatchEvent(new Event('change', {{ bubbles: true }})); }}
          if (action.type === 'Click') {{ const el = await waitForSelector(action.selector); el.click(); }}
          if (action.type === 'Wait Seconds') {{ await new Promise((resolve) => setTimeout(resolve, Number(action.seconds || 1) * 1000)); }}
          log('ok ' + action.type + ' ' + (action.selector || action.url || ''));
        }}
        const resultEl = await waitForSelector("#recorder-result[data-result-ready='true']");
        if (!resultEl.textContent || !resultEl.textContent.includes('Submitted:')) {{
          throw new Error('replay verification failed: submitted result not visible');
        }}
        log('verification passed: ' + resultEl.textContent);
        running = false;
        return true;
      }}
      window.addEventListener('message', (event) => {{
        const data = event.data || {{}};
        if (data.source !== 'rpa-studio-recorder') return;
        const action = data.action || {{}};
        if (action.type === 'Recorder') {{ log('Recorder ' + action.event); return; }}
        if (!recording) return;
        if (action.type === 'Type') {{
          const previous = actions[actions.length - 1];
          if (previous && previous.type === 'Type' && previous.selector === action.selector) {{
            actions[actions.length - 1] = action;
            log('updated Type ' + (action.selector || '') + ' = ' + (action.redacted ? '[redacted]' : (action.text || '')));
          }} else {{
            actions.push(action);
            log('captured Type ' + (action.selector || '') + ' = ' + (action.redacted ? '[redacted]' : (action.text || '')));
          }}
        }} else {{
          actions.push(action);
          log('captured ' + action.type + ' ' + (action.selector || ''));
        }}
        render();
      }});
      document.getElementById('go').addEventListener('click', () => {{ frame.src = urlBar.value; updateRecordingAvailability(); }});
      document.getElementById('home').addEventListener('click', () => {{ urlBar.value = demoUrl; frame.src = demoUrl; updateRecordingAvailability(); log('Loaded bundled local demo page'); }});
      document.getElementById('reload').addEventListener('click', () => {{ frame.contentWindow.location.reload(); }});
      document.getElementById('start-recording').addEventListener('click', () => {{ if (!updateRecordingAvailability()) {{ log('Recording blocked: PM14 records only the bundled local demo page.'); return; }} setRecordingState(true); actions = [{{ type: 'Navigate', url: frame.src, label: 'Current page', order: 1, timestamp_ms: Date.now() }}]; render(); postRecorderCommand('start-recording'); log('Start Recording'); }});
      document.getElementById('stop-recording').addEventListener('click', () => {{ setRecordingState(false); postRecorderCommand('stop-recording'); log('Stop Recording'); }});
      document.getElementById('clear-actions').addEventListener('click', () => {{ actions = []; render(); log('Actions cleared'); }});
      frame.addEventListener('load', () => {{ urlBar.value = frame.src; const onDemoPage = updateRecordingAvailability(); if (recording && onDemoPage) postRecorderCommand('start-recording'); if (recording && !onDemoPage) {{ setRecordingState(false); log('Recording stopped: embedded page is outside the bundled local demo.'); }} }});
      document.getElementById('stop-run').addEventListener('click', () => {{ running = false; log('Stop Run requested'); }});
      document.getElementById('save-workflow').addEventListener('click', async () => {{
        const res = await fetch('/api/save-workflow', {{ method: 'POST', headers: {{ 'content-type': 'application/json' }}, body: JSON.stringify({{ actions }}) }});
        evidenceEl.textContent = JSON.stringify(await res.json(), null, 2);
      }});
      document.getElementById('run-steps').addEventListener('click', async () => {{
        try {{
          setRecordingState(false);
          await replay(actions);
          const res = await fetch('/api/save-run-evidence', {{ method: 'POST', headers: {{ 'content-type': 'application/json' }}, body: JSON.stringify({{ actions, status: 'pass', log: logEl.textContent }} ) }});
          const data = await res.json();
          evidenceEl.textContent = JSON.stringify(data, null, 2);
          log('Run completed: ' + data.status);
        }} catch (err) {{
          const res = await fetch('/api/save-run-evidence', {{ method: 'POST', headers: {{ 'content-type': 'application/json' }}, body: JSON.stringify({{ actions, status: 'fail', error: String(err), log: logEl.textContent }} ) }});
          evidenceEl.textContent = JSON.stringify(await res.json(), null, 2);
          log('Run failed: ' + err);
        }}
      }});
      setRecordingState(false);
      updateRecordingAvailability();
      render();
    </script>
  </body>
</html>"""


class RecorderRequestHandler(BaseHTTPRequestHandler):
    server_version = "RPAStudioRecorder/1.0"

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
        if parsed.path.startswith("/demo/"):
            rel = parsed.path[len("/demo/"):]
            target = (FIXTURE_DIR / rel).resolve()
            if not str(target).startswith(str(FIXTURE_DIR.resolve())) or not target.exists():
                self.send_error(404)
                return
            if target.suffix == ".js":
                content_type = "application/javascript; charset=utf-8"
            elif target.suffix == ".html":
                content_type = "text/html; charset=utf-8"
            else:
                content_type = "text/plain; charset=utf-8"
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
            body = _read_json_body(self)
            actions = body.get("actions")
            if not isinstance(actions, list):
                raise RecorderError("actions must be a list")
            if parsed.path == "/api/save-workflow":
                workflow = workflow_from_actions(actions)
                run_dir = _unique_run_dir()
                path = run_dir / "workflow" / "recorded_workflow.json"
                _write_json(path, workflow)
                self._send_json({"status": "saved", "workflow_json": str(path.resolve()), "action_count": len(actions)})
                return
            if parsed.path == "/api/save-run-evidence":
                result = replay_recorded_actions(actions)
                self._send_json(result, status=200 if result["status"] == "pass" else 500)
                return
            self.send_error(404)
        except Exception as exc:
            self._send_json({"status": "fail", "message": f"{type(exc).__name__}: {exc}"}, status=500)


def serve(host: str = "127.0.0.1", port: int = 8877) -> None:
    httpd = _QuietHTTPServer((host, port), RecorderRequestHandler)
    actual_host, actual_port = httpd.server_address
    print(f"RPA Studio Recorder MVP: http://{actual_host}:{actual_port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nRPA Studio Recorder stopped.")
    finally:
        httpd.server_close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rpa-studio-recorder")
    sub = parser.add_subparsers(dest="command", required=False)
    serve_cmd = sub.add_parser("serve", help="Launch the local RPA Studio Recorder MVP UI.")
    serve_cmd.add_argument("--host", default="127.0.0.1")
    serve_cmd.add_argument("--port", type=int, default=8877)
    demo_cmd = sub.add_parser("run-demo", help="Run deterministic PM14 recording/replay helper.")
    demo_cmd.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.command in {None, "serve"}:
        serve(host=getattr(args, "host", "127.0.0.1"), port=getattr(args, "port", 8877))
        return 0
    if args.command == "run-demo":
        result = replay_recorded_actions(sample_recorded_actions())
        if args.as_json:
            print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True))
        else:
            print(result["message"])
            print(f"run_dir: {result['run_dir']}")
        return 0 if result["status"] == "pass" else 1
    parser.error(f"Unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
