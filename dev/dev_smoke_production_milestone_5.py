from __future__ import annotations

import json
import os
import sys
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

FIXTURE_DIR = REPO_ROOT / "dev" / "fixtures" / "production_milestone_5"
SITE_DIR = FIXTURE_DIR / "site"
OUT_ROOT = REPO_ROOT / "dev" / "_smoke_artifacts" / "production_milestone_5"
RUN_OUT_DIR: Path | None = None


class BrowserUnavailable(RuntimeError):
    pass


class _QuietStaticHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(SITE_DIR), **kwargs)

    def log_message(self, format: str, *args: Any) -> None:
        return None


class _SmokeHTTPServer(ThreadingHTTPServer):
    def handle_error(self, request: Any, client_address: Any) -> None:
        exc_type, exc, _tb = sys.exc_info()
        if exc_type in {ConnectionResetError, BrokenPipeError}:
            return
        super().handle_error(request, client_address)


def _run_dir() -> Path:
    if RUN_OUT_DIR is None:
        raise AssertionError("RUN_OUT_DIR must be initialized")
    return RUN_OUT_DIR


def _read_json(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise AssertionError(f"Expected JSON object: {path}")
    return obj


def _write_json(path: Path, obj: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(obj), indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def _assert_nonempty(path: Path) -> None:
    assert path.exists(), f"missing artifact: {path}"
    assert path.is_file(), f"artifact is not a file: {path}"
    assert path.stat().st_size > 0, f"empty artifact: {path}"


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


def _inject_site_url(bundle: Mapping[str, Any], site_url: str) -> dict[str, Any]:
    def replace(obj: Any) -> Any:
        if isinstance(obj, str):
            return obj.replace("__PM5_SITE_URL__", site_url)
        if isinstance(obj, list):
            return [replace(value) for value in obj]
        if isinstance(obj, dict):
            return {str(key): replace(value) for key, value in obj.items()}
        return obj

    out = replace(dict(bundle))
    if not isinstance(out, dict):
        raise AssertionError("run-local deploy bundle must be a JSON object")
    return out


def _start_static_server() -> tuple[ThreadingHTTPServer, threading.Thread, str]:
    httpd = _SmokeHTTPServer(("127.0.0.1", 0), _QuietStaticHandler)
    host, port = httpd.server_address
    thread = threading.Thread(target=httpd.serve_forever, name="pm5-static-server", daemon=True)
    thread.start()
    return httpd, thread, f"http://{host}:{port}/index.html"


def _prepare_run_bundle(site_url: str) -> tuple[dict[str, Any], Path]:
    source = _read_json(FIXTURE_DIR / "deploy_bundle_golden.json")
    bundle = _inject_site_url(source, site_url)
    bundle_path = _run_dir() / "bundle" / "deploy_bundle.golden.run.json"
    _write_json(bundle_path, bundle)
    return bundle, bundle_path


def _production_validation(bundle: Mapping[str, Any]) -> dict[str, Any]:
    from VAL.val_2a_deploy_bundle_validator import validate_deploy_bundle_1a

    report = validate_deploy_bundle_1a(
        bundle,
        require_version_fingerprint=True,
        require_selector_ref=True,
        production=True,
    )
    if not isinstance(report, dict):
        raise AssertionError(f"Expected validation report dict, got: {type(report)!r}")
    return report


def _assert_production_valid(bundle: Mapping[str, Any]) -> None:
    report = _production_validation(bundle)
    if not report.get("ok"):
        raise AssertionError(f"Expected production-valid deploy bundle, got: {report!r}")


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
    if not isinstance(workflow_for_run.get("name"), str) or not workflow_for_run["name"].strip():
        workflow_for_run["name"] = "production_milestone_5_golden"
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
    cfg_overrides.update(_browser_cfg(browser, output_dir))
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
        raise AssertionError("deploy bundle workflow missing")
    steps = workflow.get("steps")
    if not isinstance(steps, list):
        raise AssertionError("deploy bundle workflow.steps missing")

    manifest = build_run_manifest(
        run_output_dir=output_dir,
        workflow_name=str(workflow.get("name") or deploy_bundle.get("name") or "production_milestone_5"),
        run_id=str(runtime_summary.get("run_id") or "production-milestone-5"),
        workflow_path=output_dir / "runtime" / "workflow.json",
        bundle_path=bundle_path,
        bundle_version=str(deploy_bundle.get("version") or ""),
        workflow_version=str(deploy_bundle.get("version") or ""),
        inputs={"fixture": str(FIXTURE_DIR / "deploy_bundle_golden.json")},
        extra={"runtime_summary": dict(runtime_summary)},
    )
    write_run_manifest(run_output_dir=output_dir, manifest=manifest, overwrite=True)

    step_logs = runtime_summary.get("step_logs")
    if not isinstance(step_logs, list):
        raise AssertionError("runtime summary missing step_logs")
    for idx, step in enumerate(steps):
        if not isinstance(step, Mapping):
            continue
        row = step_logs[idx] if idx < len(step_logs) and isinstance(step_logs[idx], Mapping) else {}
        status = "ok" if row.get("status") == "success" else "error"
        append_step_outcome(
            run_output_dir=output_dir,
            outcome=build_step_outcome(
                workflow_name=str(workflow.get("name") or deploy_bundle.get("name") or "production_milestone_5"),
                step_index=idx,
                step=step,
                status=status,
                notes="production_milestone_5",
            ),
        )

    generate_standard_reports(run_output_dir=output_dir, overwrite=True)


def _copy_fingerprint(deploy_bundle: Mapping[str, Any], output_dir: Path) -> None:
    fp = deploy_bundle.get("fingerprint")
    if not isinstance(fp, Mapping):
        raise AssertionError("deploy bundle missing fingerprint")
    _write_json(output_dir / "bundle" / "deploy_bundle_fingerprint.json", fp)


def _assert_required_artifacts(output_dir: Path) -> None:
    expected = _read_json(FIXTURE_DIR / "expected_artifacts.json")
    required = expected.get("required")
    if not isinstance(required, list):
        raise AssertionError("expected_artifacts.json must contain required list")
    for rel in required:
        if not isinstance(rel, str):
            raise AssertionError("artifact path must be a string")
        _assert_nonempty(output_dir / rel)


def _browser_candidates() -> list[str]:
    requested = os.environ.get("RPA_PM5_BROWSER", "").strip().lower()
    if requested:
        if requested not in {"chrome", "edge"}:
            raise AssertionError("RPA_PM5_BROWSER must be 'chrome' or 'edge'")
        return [requested]
    return ["chrome", "edge"]


def _headless_enabled() -> bool:
    return os.environ.get("RPA_PM5_HEADED", "").strip().lower() not in {"1", "true", "yes", "on"}


def _browser_cfg(browser: str, output_dir: Path) -> dict[str, Any]:
    return {
        "HEADLESS": _headless_enabled(),
        "BROWSER": browser,
        "DOWNLOAD_DIR": str(output_dir / "downloads"),
        "IMPLICIT_WAIT": 0,
        "PAGELOAD_TIMEOUT": 10,
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


def _select_available_browser() -> tuple[str | None, list[str]]:
    from ENTRY.entry_1a_webdriver_bootstrap import make_driver

    unavailable: list[str] = []
    for browser in _browser_candidates():
        driver = None
        try:
            driver = make_driver(_browser_cfg(browser, _run_dir() / browser / "preflight"))
            return browser, unavailable
        except Exception as exc:
            if _looks_browser_unavailable(exc):
                unavailable.append(f"{browser}: {type(exc).__name__}: {exc}")
                continue
            raise
        finally:
            if driver is not None:
                driver.quit()
    return None, unavailable


def _run_positive_with_browser(browser: str, site_url: str) -> None:
    from RUN.run_1e_deploy_bundle_runner_adapter import run_deploy_bundle_1a_with_meta
    from WORKFLOWS.workflow_1g_deploy_bundle_loader import load_deploy_bundle_1a_from_path

    output_dir = _run_dir() / browser / "positive"
    bundle, bundle_path = _prepare_run_bundle(site_url)

    _assert_production_valid(bundle)
    loaded = load_deploy_bundle_1a_from_path(str(bundle_path), validate=True)
    _assert_production_valid(loaded)

    def runner(*, workflow: dict[str, Any], selector_pack: dict[str, Any], run_meta: dict[str, Any]) -> dict[str, Any]:
        return _run_existing_runtime_path(
            workflow=workflow,
            selector_pack=selector_pack,
            run_meta=run_meta,
            bundle_path=bundle_path,
            output_dir=output_dir,
            browser=browser,
        )

    runtime_summary, run_meta = run_deploy_bundle_1a_with_meta(
        loaded,
        runner=runner,
        validate=True,
        require_version_fingerprint=True,
        require_selector_ref=True,
    )
    assert isinstance(runtime_summary, dict), "runtime summary must be a dict"
    if runtime_summary.get("success") is not True and any(
        _looks_browser_unavailable(RuntimeError(str(err))) for err in runtime_summary.get("errors", [])
    ):
        raise BrowserUnavailable(str(runtime_summary.get("errors")))
    assert runtime_summary.get("success") is True, runtime_summary
    assert run_meta.get("bundle_version"), run_meta

    step_logs = runtime_summary.get("step_logs")
    if not isinstance(step_logs, list) or len(step_logs) < 4:
        raise AssertionError(f"runtime summary missing expected real-browser step logs: {runtime_summary!r}")
    if not all(isinstance(row, Mapping) and row.get("status") == "success" for row in step_logs):
        raise AssertionError(f"real-browser step logs did not all succeed: {step_logs!r}")

    _copy_fingerprint(loaded, output_dir)
    _write_history_and_reports(
        deploy_bundle=loaded,
        bundle_path=bundle_path,
        runtime_summary=runtime_summary,
        output_dir=output_dir,
    )
    _assert_required_artifacts(output_dir)


def dev_smoke() -> bool:
    global RUN_OUT_DIR

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    RUN_OUT_DIR = OUT_ROOT / f"run_{time.time_ns()}_{os.getpid()}"
    RUN_OUT_DIR.mkdir(parents=True, exist_ok=False)

    httpd: ThreadingHTTPServer | None = None
    thread: threading.Thread | None = None
    try:
        httpd, thread, site_url = _start_static_server()
        browser, unavailable = _select_available_browser()
        if browser is not None:
            try:
                _run_positive_with_browser(browser, site_url)
                return True
            except Exception as exc:
                if isinstance(exc, BrowserUnavailable) or _looks_browser_unavailable(exc):
                    unavailable.append(f"{browser}: {type(exc).__name__}: {exc}")
                else:
                    raise
        reason = "; ".join(unavailable) if unavailable else "no compatible browser candidate succeeded"
        print(f"SKIP: production_milestone_5 real browser unavailable: {reason}")
        return False
    finally:
        if httpd is not None:
            httpd.shutdown()
            httpd.server_close()
        if thread is not None:
            thread.join(timeout=5)


if __name__ == "__main__":
    if dev_smoke():
        print("DEV_SMOKE_OK: production_milestone_5")
