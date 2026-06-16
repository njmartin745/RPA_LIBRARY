from __future__ import annotations

import argparse
import contextlib
import html
import io
import json
import os
import sys
import threading
import time
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dev import production_proof_local_browser as proof  # noqa: E402

FIXTURE_DIR = REPO_ROOT / "dev" / "fixtures" / "rpa_studio_lite_demo"
SITE_DIR = FIXTURE_DIR
SAMPLE_WORKFLOW_PATH = FIXTURE_DIR / "sample_workflow.json"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "dev" / "_smoke_artifacts" / "rpa_studio_lite"
SUPPORTED_ACTIONS = {"Navigate", "Wait for Selector", "Type", "Click", "Wait Seconds"}
SCENARIO = "rpa-studio-lite-local-demo"


class StudioLiteError(RuntimeError):
    pass


class _QuietStaticHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(SITE_DIR), **kwargs)

    def log_message(self, format: str, *args: Any) -> None:
        return None


class _QuietHTTPServer(ThreadingHTTPServer):
    def handle_error(self, request: Any, client_address: Any) -> None:
        exc_type, _exc, _tb = sys.exc_info()
        if exc_type in {ConnectionResetError, BrokenPipeError}:
            return
        super().handle_error(request, client_address)


def _read_json(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise StudioLiteError(f"Expected JSON object: {path}")
    return obj


def _write_json(path: Path, obj: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(obj), indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def _assert_nonempty(path: Path) -> None:
    if not path.exists() or not path.is_file() or path.stat().st_size <= 0:
        raise StudioLiteError(f"Missing or empty artifact: {path}")


def _unique_run_dir(output_root: Path = DEFAULT_OUTPUT_ROOT) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    run_dir = output_root / f"run_{time.time_ns()}_{os.getpid()}"
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def _canonical_sha(obj: Mapping[str, Any]) -> str:
    data = json.dumps(dict(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return sha256(data).hexdigest()


def _selector_registry(selector_pack: Mapping[str, Any]) -> dict[str, str]:
    selectors = selector_pack.get("selectors")
    if not isinstance(selectors, Mapping):
        return {}
    out: dict[str, str] = {}
    for key, value in selectors.items():
        if isinstance(value, str):
            out[str(key)] = value
        elif isinstance(value, Mapping) and isinstance(value.get("selector"), str):
            out[str(key)] = str(value["selector"])
    return out


def _start_static_server() -> tuple[ThreadingHTTPServer, threading.Thread, str]:
    httpd = _QuietHTTPServer(("127.0.0.1", 0), _QuietStaticHandler)
    host, port = httpd.server_address
    thread = threading.Thread(target=httpd.serve_forever, name="studio-lite-static-server", daemon=True)
    thread.start()
    return httpd, thread, f"http://{host}:{port}/index.html"


def _validate_studio_workflow(workflow: Mapping[str, Any]) -> None:
    if workflow.get("schema_id") != "RPA_STUDIO_LITE_WORKFLOW_1A":
        raise StudioLiteError("Studio workflow must use schema_id RPA_STUDIO_LITE_WORKFLOW_1A")
    actions = workflow.get("actions")
    if not isinstance(actions, list) or not actions:
        raise StudioLiteError("Studio workflow requires a non-empty actions list")
    selectors = workflow.get("selectors")
    if not isinstance(selectors, Mapping):
        raise StudioLiteError("Studio workflow requires selectors mapping")
    for index, action in enumerate(actions):
        if not isinstance(action, Mapping):
            raise StudioLiteError(f"Studio action {index} must be an object")
        action_type = action.get("type")
        if action_type not in SUPPORTED_ACTIONS:
            raise StudioLiteError(f"Unsupported Studio Lite action: {action_type!r}")
        if action_type in {"Wait for Selector", "Type", "Click"}:
            ref = action.get("selector_ref")
            if not isinstance(ref, str) or not ref.strip() or ref not in selectors:
                raise StudioLiteError(f"Studio action {index} selector_ref is missing or unknown")


def _js_type_step(action: Mapping[str, Any], selector: str) -> dict[str, Any]:
    text = str(action.get("text", ""))
    script = (
        "return (function () {"
        f"const el = document.querySelector({json.dumps(selector)});"
        "if (!el) { return {ok:false, code:'missing_selector', message:'Type target not found'}; }"
        f"el.value = {json.dumps(text)};"
        "el.dispatchEvent(new Event('input', {bubbles:true}));"
        "el.dispatchEvent(new Event('change', {bubbles:true}));"
        "return {ok:true, typed:true, chars:el.value.length};"
        "}());"
    )
    return {
        "action": "exec_js",
        "name": str(action.get("name") or "Type text"),
        "script": script,
    }


def studio_workflow_to_deploy_bundle(workflow: Mapping[str, Any], site_url: str) -> dict[str, Any]:
    _validate_studio_workflow(workflow)
    selectors = {str(key): str(value) for key, value in dict(workflow["selectors"]).items()}
    steps: list[dict[str, Any]] = []

    for action in workflow["actions"]:
        action_type = str(action["type"])
        name = str(action.get("name") or action_type)
        if action_type == "Navigate":
            url = str(action.get("url") or site_url).replace("__STUDIO_DEMO_SITE_URL__", site_url)
            steps.append({"action": "open", "name": name, "url": url})
        elif action_type == "Wait for Selector":
            steps.append(
                {
                    "action": "wait_for_selector",
                    "name": name,
                    "selector_ref": str(action["selector_ref"]),
                    "by": "css",
                    "condition": str(action.get("condition") or "visible"),
                    "timeout": int(action.get("timeout") or 5),
                }
            )
        elif action_type == "Click":
            steps.append(
                {
                    "action": "click_selector",
                    "name": name,
                    "selector_ref": str(action["selector_ref"]),
                    "by": "css",
                    "timeout": int(action.get("timeout") or 5),
                }
            )
        elif action_type == "Type":
            selector = selectors[str(action["selector_ref"])]
            steps.append(_js_type_step(action, selector))
        elif action_type == "Wait Seconds":
            steps.append({"action": "wait", "name": name, "seconds": float(action.get("seconds") or 1)})
        else:
            raise StudioLiteError(f"Unsupported Studio Lite action: {action_type}")

    bundle_without_fingerprint: dict[str, Any] = {
        "schema_id": "DEPLOY_BUNDLE_1A",
        "name": str(workflow.get("name") or "rpa_studio_lite_sample"),
        "version": "sha256:pending",
        "workflow": {
            "name": str(workflow.get("name") or "rpa_studio_lite_sample"),
            "steps": steps,
        },
        "selector_pack": {
            "schema_id": "SELECTOR_PACK_1A",
            "name": "rpa_studio_lite_selectors",
            "selectors": selectors,
        },
        "meta": {
            "source_schema_id": "RPA_STUDIO_LITE_WORKFLOW_1A",
            "source_name": str(workflow.get("name") or "rpa_studio_lite_sample"),
            "scenario": SCENARIO,
            "scope": "controlled_local_fixture_only",
        },
    }
    digest = _canonical_sha(bundle_without_fingerprint)
    bundle_without_fingerprint["version"] = f"sha256:{digest[:12]}"
    bundle_without_fingerprint["fingerprint"] = {
        "algo": "sha256",
        "canonicalization": "rpa-studio-lite-demo",
        "sha256": digest,
        "bytes": len(json.dumps(bundle_without_fingerprint, sort_keys=True, ensure_ascii=True).encode("utf-8")),
        "dropped_top_level_keys": [],
    }
    return bundle_without_fingerprint


def _assert_production_valid(bundle: Mapping[str, Any]) -> None:
    from VAL.val_2a_deploy_bundle_validator import validate_deploy_bundle_1a

    report = validate_deploy_bundle_1a(
        bundle,
        require_version_fingerprint=True,
        require_selector_ref=True,
        production=True,
    )
    if not report.get("ok"):
        raise StudioLiteError(f"Generated deploy bundle is not production-valid: {report!r}")


def _run_existing_runtime_path(
    *,
    workflow: dict[str, Any],
    selector_pack: dict[str, Any],
    run_meta: dict[str, Any],
    bundle_path: Path,
    output_dir: Path,
    browser: str,
) -> dict[str, Any]:
    from RUN.run_1a_workflow_runner import run_workflow

    workflow_path = output_dir / "runtime" / "workflow.json"
    workflow_for_run = dict(workflow)
    workflow_for_run.setdefault("name", "rpa_studio_lite_sample")
    _write_json(workflow_path, workflow_for_run)

    cfg_overrides = {
        "SELECTORS": _selector_registry(selector_pack),
        "LOG_JSON": True,
        "QUIET_CONSOLE": True,
        "LOG_JSONL_PATH": str(output_dir / "logs" / "run.jsonl"),
        "LOG_PATH": str(output_dir / "logs" / "run.jsonl"),
        "MANIFEST_PATH": str(output_dir / "state" / "manifest.jsonl"),
        "WORKLIST_XLSX": str(output_dir / "runtime" / "missing_worklist.xlsx"),
        "STOP_ON_ERROR": True,
        "BUNDLE_PATH": str(bundle_path),
        "BUNDLE_VERSION": run_meta.get("bundle_version"),
    }
    cfg_overrides.update(proof._browser_cfg(browser, output_dir))
    summary = run_workflow(workflow_path, cfg_overrides)
    run_id = summary.get("run_id") if isinstance(summary, Mapping) else None
    if isinstance(run_id, str) and run_id:
        scratch = REPO_ROOT / ".dev_tmp" / f"run_1a_steps_{run_id}.json"
        if scratch.exists():
            scratch.unlink()
    return summary


def _write_history_and_reports(
    *,
    deploy_bundle: Mapping[str, Any],
    bundle_path: Path,
    runtime_summary: Mapping[str, Any],
    output_dir: Path,
) -> None:
    from HISTORY.history_1a_run_manifest import build_run_manifest, write_run_manifest
    from HISTORY.history_1b_step_outcomes import append_step_outcome, build_step_outcome
    from REPORT.report_1d_generate_reports import generate_standard_reports

    workflow = deploy_bundle.get("workflow")
    if not isinstance(workflow, Mapping):
        raise StudioLiteError("deploy bundle workflow missing")
    steps = workflow.get("steps")
    if not isinstance(steps, list):
        raise StudioLiteError("deploy bundle workflow.steps missing")

    manifest = build_run_manifest(
        run_output_dir=output_dir,
        workflow_name=str(workflow.get("name") or deploy_bundle.get("name") or "rpa_studio_lite_sample"),
        run_id=str(runtime_summary.get("run_id") or "rpa-studio-lite"),
        workflow_path=output_dir / "runtime" / "workflow.json",
        bundle_path=bundle_path,
        bundle_version=str(deploy_bundle.get("version") or ""),
        workflow_version=str(deploy_bundle.get("version") or ""),
        inputs={"fixture": str(SAMPLE_WORKFLOW_PATH)},
        extra={"runtime_summary": dict(runtime_summary), "scenario": SCENARIO},
    )
    write_run_manifest(run_output_dir=output_dir, manifest=manifest, overwrite=True)

    step_logs = runtime_summary.get("step_logs")
    if not isinstance(step_logs, list):
        raise StudioLiteError("runtime summary missing step_logs")
    for idx, step in enumerate(steps):
        if not isinstance(step, Mapping):
            continue
        row = step_logs[idx] if idx < len(step_logs) and isinstance(step_logs[idx], Mapping) else {}
        status = "ok" if row.get("status") == "success" else "error"
        append_step_outcome(
            run_output_dir=output_dir,
            outcome=build_step_outcome(
                workflow_name=str(workflow.get("name") or deploy_bundle.get("name") or "rpa_studio_lite_sample"),
                step_index=idx,
                step=step,
                status=status,
                notes="rpa_studio_lite_demo",
            ),
        )

    generate_standard_reports(run_output_dir=output_dir, overwrite=True)


def _copy_fingerprint(deploy_bundle: Mapping[str, Any], output_dir: Path) -> None:
    fp = deploy_bundle.get("fingerprint")
    if not isinstance(fp, Mapping):
        raise StudioLiteError("deploy bundle missing fingerprint")
    _write_json(output_dir / "bundle" / "deploy_bundle_fingerprint.json", fp)


def _artifact_paths(output_dir: Path) -> list[str]:
    required = [
        output_dir / "logs" / "run.jsonl",
        output_dir / "history" / "run_manifest.json",
        output_dir / "history" / "step_outcomes.jsonl",
        output_dir / "bundle" / "deploy_bundle_fingerprint.json",
        output_dir / "report" / "run_report.md",
    ]
    for path in required:
        _assert_nonempty(path)
    return [str(path.resolve()) for path in required]


def run_sample_workflow(
    *,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    browser: str = "auto",
    headed: bool = False,
) -> dict[str, Any]:
    from RUN.run_1e_deploy_bundle_runner_adapter import run_deploy_bundle_1a_with_meta
    from WORKFLOWS.workflow_1g_deploy_bundle_loader import load_deploy_bundle_1a_from_path

    run_dir = _unique_run_dir(output_root)
    old_run_dir = proof.RUN_OUT_DIR
    old_out_root = proof.OUT_ROOT
    old_browser = os.environ.get("RPA_PM5_BROWSER")
    old_headed = os.environ.get("RPA_PM5_HEADED")
    old_log_path = os.environ.get("LOG_PATH")
    old_log_jsonl_path = os.environ.get("LOG_JSONL_PATH")
    proof.OUT_ROOT = output_root
    proof.RUN_OUT_DIR = run_dir
    if browser != "auto":
        os.environ["RPA_PM5_BROWSER"] = browser
    else:
        os.environ.pop("RPA_PM5_BROWSER", None)
    if headed:
        os.environ["RPA_PM5_HEADED"] = "1"
    else:
        os.environ.pop("RPA_PM5_HEADED", None)
    os.environ.pop("LOG_PATH", None)
    os.environ.pop("LOG_JSONL_PATH", None)

    httpd: ThreadingHTTPServer | None = None
    thread: threading.Thread | None = None
    selected_browser: str | None = None
    try:
        httpd, thread, site_url = _start_static_server()
        selected_browser, unavailable = proof._select_available_browser()
        if selected_browser is None:
            reason = "; ".join(unavailable) if unavailable else "no compatible browser candidate succeeded"
            return {
                "status": "skip",
                "message": f"SKIP: rpa_studio_lite real browser unavailable: {reason}",
                "browser": None,
                "scenario": SCENARIO,
                "run_dir": str(run_dir.resolve()),
                "artifacts": [],
            }

        studio_workflow = _read_json(SAMPLE_WORKFLOW_PATH)
        saved_workflow_path = run_dir / "studio" / "sample_workflow.json"
        _write_json(saved_workflow_path, studio_workflow)
        deploy_bundle = studio_workflow_to_deploy_bundle(studio_workflow, site_url)
        _assert_production_valid(deploy_bundle)

        output_dir = run_dir / selected_browser / "sample"
        bundle_path = output_dir / "bundle" / "deploy_bundle.generated.json"
        _write_json(bundle_path, deploy_bundle)
        loaded = load_deploy_bundle_1a_from_path(str(bundle_path), validate=True)
        _assert_production_valid(loaded)

        def runner(*, workflow: dict[str, Any], selector_pack: dict[str, Any], run_meta: dict[str, Any]) -> dict[str, Any]:
            return _run_existing_runtime_path(
                workflow=workflow,
                selector_pack=selector_pack,
                run_meta=run_meta,
                bundle_path=bundle_path,
                output_dir=output_dir,
                browser=selected_browser or "auto",
            )

        runtime_summary, run_meta = run_deploy_bundle_1a_with_meta(
            loaded,
            runner=runner,
            validate=True,
            require_version_fingerprint=True,
            require_selector_ref=True,
        )
        if not isinstance(runtime_summary, dict):
            raise StudioLiteError("runtime summary must be a dict")
        if runtime_summary.get("success") is not True:
            if any(proof._looks_browser_unavailable(RuntimeError(str(err))) for err in runtime_summary.get("errors", [])):
                return {
                    "status": "skip",
                    "message": f"SKIP: rpa_studio_lite real browser unavailable: {runtime_summary.get('errors')}",
                    "browser": selected_browser,
                    "scenario": SCENARIO,
                    "run_dir": str(run_dir.resolve()),
                    "artifacts": [],
                }
            raise StudioLiteError(f"sample workflow failed: {runtime_summary!r}")
        if not run_meta.get("bundle_version"):
            raise StudioLiteError(f"missing bundle version metadata: {run_meta!r}")

        _copy_fingerprint(loaded, output_dir)
        _write_history_and_reports(
            deploy_bundle=loaded,
            bundle_path=bundle_path,
            runtime_summary=runtime_summary,
            output_dir=output_dir,
        )
        artifacts = _artifact_paths(output_dir)
        return {
            "status": "pass",
            "message": "PASS: rpa_studio_lite sample workflow",
            "browser": selected_browser,
            "scenario": SCENARIO,
            "run_dir": str(run_dir.resolve()),
            "artifacts": artifacts,
            "run_report": str((output_dir / "report" / "run_report.md").resolve()),
            "step_outcomes": str((output_dir / "history" / "step_outcomes.jsonl").resolve()),
            "saved_workflow": str(saved_workflow_path.resolve()),
        }
    except Exception as exc:
        if isinstance(exc, proof.BrowserUnavailable) or proof._looks_browser_unavailable(exc):
            return {
                "status": "skip",
                "message": f"SKIP: rpa_studio_lite real browser unavailable: {type(exc).__name__}: {exc}",
                "browser": selected_browser,
                "scenario": SCENARIO,
                "run_dir": str(run_dir.resolve()),
                "artifacts": [],
            }
        return {
            "status": "fail",
            "message": f"FAIL: rpa_studio_lite sample workflow: {type(exc).__name__}: {exc}",
            "browser": selected_browser,
            "scenario": SCENARIO,
            "run_dir": str(run_dir.resolve()),
            "artifacts": [],
        }
    finally:
        if httpd is not None:
            httpd.shutdown()
            httpd.server_close()
        if thread is not None:
            thread.join(timeout=5)
        proof.RUN_OUT_DIR = old_run_dir
        proof.OUT_ROOT = old_out_root
        if old_browser is None:
            os.environ.pop("RPA_PM5_BROWSER", None)
        else:
            os.environ["RPA_PM5_BROWSER"] = old_browser
        if old_headed is None:
            os.environ.pop("RPA_PM5_HEADED", None)
        else:
            os.environ["RPA_PM5_HEADED"] = old_headed
        if old_log_path is None:
            os.environ.pop("LOG_PATH", None)
        else:
            os.environ["LOG_PATH"] = old_log_path
        if old_log_jsonl_path is None:
            os.environ.pop("LOG_JSONL_PATH", None)
        else:
            os.environ["LOG_JSONL_PATH"] = old_log_jsonl_path


def save_studio_workflow(workflow: Mapping[str, Any], *, output_root: Path = DEFAULT_OUTPUT_ROOT) -> Path:
    _validate_studio_workflow(workflow)
    run_dir = _unique_run_dir(output_root)
    path = run_dir / "studio" / "workflow_saved_from_builder.json"
    _write_json(path, workflow)
    return path


def _html_page() -> str:
    sample = json.dumps(_read_json(SAMPLE_WORKFLOW_PATH), indent=2, sort_keys=True, ensure_ascii=True)
    escaped_sample = html.escape(sample)
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>RPA Studio Lite</title>
    <style>
      body {{ margin: 0; font-family: Arial, sans-serif; background: #f4f6f8; color: #17202a; }}
      header {{ background: #123b5d; color: white; padding: 22px 28px; }}
      main {{ display: grid; grid-template-columns: minmax(320px, 0.9fr) minmax(360px, 1.1fr); gap: 18px; padding: 20px; }}
      section {{ background: white; border: 1px solid #d8dee8; border-radius: 8px; padding: 18px; }}
      label {{ display: block; font-weight: 700; margin: 12px 0 5px; }}
      input, select, textarea {{ box-sizing: border-box; width: 100%; border: 1px solid #aeb8c7; border-radius: 6px; padding: 8px; }}
      textarea {{ min-height: 340px; font-family: Consolas, monospace; font-size: 13px; }}
      button {{ border: 0; border-radius: 6px; background: #1261a6; color: white; cursor: pointer; font-weight: 700; margin: 10px 8px 0 0; padding: 9px 12px; }}
      button.secondary {{ background: #4f5d6b; }}
      .notice {{ background: #fff7dd; border: 1px solid #e2c35d; border-radius: 6px; padding: 10px; }}
      .result {{ background: #f9fbfd; border: 1px solid #d8dee8; border-radius: 6px; margin-top: 12px; padding: 12px; white-space: pre-wrap; }}
      .actions {{ margin-top: 12px; padding-left: 18px; }}
      @media (max-width: 900px) {{ main {{ grid-template-columns: 1fr; }} }}
    </style>
  </head>
  <body>
    <header>
      <h1>RPA Studio Lite</h1>
      <p>Build and run a controlled local automation proof.</p>
    </header>
    <main>
      <section>
        <h2>Build Automation</h2>
        <div class="notice">
          This is not production-ready. PM13 runs only the bundled controlled local/static sample workflow. Edited workflow JSON can be built and saved, but custom workflow replay is deferred to a future milestone.
        </div>
        <label for="action-type">Action</label>
        <select id="action-type">
          <option>Navigate</option>
          <option>Wait for Selector</option>
          <option>Type</option>
          <option>Click</option>
          <option>Wait Seconds</option>
        </select>
        <label for="action-name">Name</label>
        <input id="action-name" value="New action">
        <label for="action-selector">Selector ref</label>
        <input id="action-selector" value="studio.input">
        <label for="action-url">URL</label>
        <input id="action-url" value="__STUDIO_DEMO_SITE_URL__">
        <label for="action-text">Text</label>
        <input id="action-text" value="Hello from RPA Studio Lite">
        <button id="add-action" type="button">Add action</button>
        <button id="load-sample" class="secondary" type="button">Load sample</button>
        <ol id="actions" class="actions"></ol>
        <button id="save-workflow" type="button">Save workflow JSON</button>
        <p><strong>PM13 run scope:</strong> Run controlled local sample uses the controlled local/static sample only. Edited workflow JSON can be saved but is not executed.</p>
        <button id="run-sample" type="button">Run controlled local sample</button>
      </section>
      <section>
        <h2>Builder JSON / Saved Workflow Preview</h2>
        <textarea id="workflow-json" spellcheck="false">{escaped_sample}</textarea>
        <h2>Current PM13 Behavior</h2>
        <ul>
          <li>Build/edit workflow JSON: supported as a local authoring preview.</li>
          <li>Save workflow JSON: supported.</li>
          <li>Run controlled local sample: supported.</li>
          <li>Run edited/custom workflow: deferred.</li>
        </ul>
        <h2>Run Evidence</h2>
        <div id="run-result" class="result">No run yet.</div>
        <h2>What This Proves</h2>
        <p>The demo proves a user can build and save a small local workflow shape, run the bundled controlled local sample through the existing local browser proof path, and inspect artifacts.</p>
        <h2>What This Does Not Prove</h2>
        <p>It does not prove production readiness, arbitrary workflow execution, edited JSON replay, custom workflow replay, external sites, credentials, downloads, retries, resume, multi-agent execution, or generated operational telemetry.</p>
      </section>
    </main>
    <script>
      const sample = JSON.parse(document.getElementById("workflow-json").value);
      let workflow = structuredClone(sample);
      const actionsEl = document.getElementById("actions");
      const jsonEl = document.getElementById("workflow-json");
      const resultEl = document.getElementById("run-result");

      function render() {{
        actionsEl.innerHTML = "";
        workflow.actions.forEach((action) => {{
          const li = document.createElement("li");
          li.textContent = `${{action.type}} - ${{action.name || ""}}`;
          actionsEl.appendChild(li);
        }});
        jsonEl.value = JSON.stringify(workflow, null, 2);
      }}

      document.getElementById("add-action").addEventListener("click", () => {{
        const type = document.getElementById("action-type").value;
        const action = {{ type, name: document.getElementById("action-name").value || type }};
        if (type === "Navigate") action.url = document.getElementById("action-url").value;
        if (type === "Wait for Selector" || type === "Click" || type === "Type") action.selector_ref = document.getElementById("action-selector").value;
        if (type === "Wait for Selector") {{ action.condition = "visible"; action.timeout = 5; }}
        if (type === "Click") action.timeout = 5;
        if (type === "Type") {{ action.text = document.getElementById("action-text").value; action.timeout = 5; }}
        if (type === "Wait Seconds") action.seconds = 1;
        workflow.actions.push(action);
        render();
      }});

      document.getElementById("load-sample").addEventListener("click", () => {{
        workflow = structuredClone(sample);
        render();
      }});

      document.getElementById("save-workflow").addEventListener("click", async () => {{
        workflow = JSON.parse(jsonEl.value);
        const res = await fetch("/api/save-workflow", {{ method: "POST", headers: {{ "content-type": "application/json" }}, body: JSON.stringify(workflow) }});
        const data = await res.json();
        resultEl.textContent = JSON.stringify(data, null, 2);
      }});

      document.getElementById("run-sample").addEventListener("click", async () => {{
        resultEl.textContent = "Running controlled local sample...";
        const res = await fetch("/api/run-sample", {{ method: "POST" }});
        const data = await res.json();
        resultEl.textContent = JSON.stringify(data, null, 2);
      }});

      render();
    </script>
  </body>
</html>
"""


class StudioRequestHandler(BaseHTTPRequestHandler):
    server_version = "RPAStudioLite/1.0"

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
        path = urlparse(self.path).path
        if path == "/":
            self._send_html(_html_page())
            return
        if path == "/api/sample-workflow":
            self._send_json(_read_json(SAMPLE_WORKFLOW_PATH))
            return
        self.send_error(404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            if path == "/api/save-workflow":
                length = int(self.headers.get("content-length") or "0")
                workflow = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(workflow, dict):
                    raise StudioLiteError("workflow payload must be a JSON object")
                saved = save_studio_workflow(workflow)
                self._send_json({"status": "saved", "path": str(saved.resolve())})
                return
            if path == "/api/run-sample":
                result = run_sample_workflow()
                self._send_json(result, status=200 if result["status"] in {"pass", "skip"} else 500)
                return
            self.send_error(404)
        except Exception as exc:
            self._send_json({"status": "fail", "message": f"{type(exc).__name__}: {exc}"}, status=500)


def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    httpd = _QuietHTTPServer((host, port), StudioRequestHandler)
    actual_host, actual_port = httpd.server_address
    print(f"RPA Studio Lite: http://{actual_host}:{actual_port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nRPA Studio Lite stopped.")
    finally:
        httpd.server_close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rpa-studio-lite")
    sub = parser.add_subparsers(dest="command", required=False)
    serve_cmd = sub.add_parser("serve", help="Launch the local RPA Studio Lite demo UI.")
    serve_cmd.add_argument("--host", default="127.0.0.1")
    serve_cmd.add_argument("--port", type=int, default=8765)
    run_cmd = sub.add_parser("run-sample", help="Run the controlled local sample workflow.")
    run_cmd.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.command in {None, "serve"}:
        serve(host=getattr(args, "host", "127.0.0.1"), port=getattr(args, "port", 8765))
        return 0
    if args.command == "run-sample":
        if args.as_json:
            with contextlib.redirect_stdout(io.StringIO()):
                result = run_sample_workflow()
            print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True))
        else:
            result = run_sample_workflow()
            print(result["message"])
            print(f"run_dir: {result.get('run_dir')}")
            print(f"browser: {result.get('browser')}")
        return 0 if result["status"] == "pass" else 2 if result["status"] == "skip" else 1
    parser.error(f"Unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

