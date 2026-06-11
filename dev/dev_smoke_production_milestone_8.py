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

FIXTURE_DIR = REPO_ROOT / "dev" / "fixtures" / "production_milestone_8"
SITE_DIR = FIXTURE_DIR / "site"
OUT_ROOT = REPO_ROOT / "dev" / "_smoke_artifacts" / "production_milestone_8"
_SELF_STATUS_PATHS = {
    "dev/dev_smoke_production_milestone_8.py",
    "dev/fixtures/production_milestone_8/deploy_bundle_missing_selector.json",
    "dev/fixtures/production_milestone_8/expected_artifacts.json",
    "dev/fixtures/production_milestone_8/site/index.html",
}
_SELF_STATUS_PREFIXES = ("dev/fixtures/production_milestone_8/",)


class BrowserUnavailable(RuntimeError):
    pass


class _QuietStaticHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(SITE_DIR), **kwargs)

    def log_message(self, format: str, *args: Any) -> None:
        return None


class _SmokeHTTPServer(ThreadingHTTPServer):
    def handle_error(self, request: Any, client_address: Any) -> None:
        exc_type, _exc, _tb = sys.exc_info()
        if exc_type in {ConnectionResetError, BrokenPipeError}:
            return
        super().handle_error(request, client_address)


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


def _start_static_server() -> tuple[ThreadingHTTPServer, threading.Thread, str]:
    httpd = _SmokeHTTPServer(("127.0.0.1", 0), _QuietStaticHandler)
    host, port = httpd.server_address
    thread = threading.Thread(target=httpd.serve_forever, name="pm8-static-server", daemon=True)
    thread.start()
    return httpd, thread, f"http://{host}:{port}/index.html"


def _inject_site_url(bundle: Mapping[str, Any], site_url: str) -> dict[str, Any]:
    def replace(obj: Any) -> Any:
        if isinstance(obj, str):
            return obj.replace("__PM8_SITE_URL__", site_url)
        if isinstance(obj, list):
            return [replace(value) for value in obj]
        if isinstance(obj, dict):
            return {str(key): replace(value) for key, value in obj.items()}
        return obj

    out = replace(dict(bundle))
    if not isinstance(out, dict):
        raise AssertionError("run-local deploy bundle must be a JSON object")
    return out


def _prepare_run_bundle(run_dir: Path, site_url: str) -> tuple[dict[str, Any], Path]:
    source = _read_json(FIXTURE_DIR / "deploy_bundle_missing_selector.json")
    bundle = _inject_site_url(source, site_url)
    bundle_path = run_dir / "bundle" / "deploy_bundle.missing_selector.run.json"
    _write_json(bundle_path, bundle)
    return bundle, bundle_path


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


def _browser_candidates() -> list[str]:
    requested = os.environ.get("RPA_PM8_BROWSER", "").strip().lower()
    if requested:
        if requested not in {"chrome", "edge"}:
            raise AssertionError("RPA_PM8_BROWSER must be 'chrome' or 'edge'")
        return [requested]
    return ["chrome", "edge"]


def _headless_enabled() -> bool:
    return os.environ.get("RPA_PM8_HEADED", "").strip().lower() not in {"1", "true", "yes", "on"}


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


def _select_available_browser(run_dir: Path) -> tuple[str | None, list[str]]:
    from ENTRY.entry_1a_webdriver_bootstrap import make_driver

    unavailable: list[str] = []
    for browser in _browser_candidates():
        driver = None
        try:
            driver = make_driver(_browser_cfg(browser, run_dir / browser / "preflight"))
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
        workflow_for_run["name"] = "production_milestone_8_missing_selector"
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


def _copy_fingerprint(deploy_bundle: Mapping[str, Any], output_dir: Path) -> None:
    fp = deploy_bundle.get("fingerprint")
    if not isinstance(fp, Mapping):
        raise AssertionError("deploy bundle missing fingerprint")
    _write_json(output_dir / "bundle" / "deploy_bundle_fingerprint.json", fp)


def _ensure_failure_log(output_dir: Path, runtime_summary: Mapping[str, Any]) -> None:
    log_path = output_dir / "logs" / "run.jsonl"
    if log_path.exists() and log_path.stat().st_size > 0:
        return

    from LOG.log_1a_structured_logging import bind_context, log_event, setup_logging

    cfg: dict[str, Any] = {
        "RUN_ID": str(runtime_summary.get("run_id") or "production-milestone-8"),
        "LOG_JSON": True,
        "QUIET_CONSOLE": True,
        "LOG_JSONL_PATH": str(log_path),
        "LOG_PATH": str(log_path),
    }
    logger = setup_logging(cfg)
    bind_context(cfg, run_id=cfg["RUN_ID"])
    log_event(
        logger,
        "runtime_failure_artifact",
        milestone="production_milestone_8",
        success=runtime_summary.get("success"),
        errors=runtime_summary.get("errors"),
    )


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
        workflow_name=str(workflow.get("name") or deploy_bundle.get("name") or "production_milestone_8"),
        run_id=str(runtime_summary.get("run_id") or "production-milestone-8"),
        workflow_path=output_dir / "runtime" / "workflow.json",
        bundle_path=bundle_path,
        bundle_version=str(deploy_bundle.get("version") or ""),
        workflow_version=str(deploy_bundle.get("version") or ""),
        inputs={"fixture": str(FIXTURE_DIR / "deploy_bundle_missing_selector.json")},
        extra={"runtime_summary": dict(runtime_summary), "expected_failure": "missing_selector"},
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
        err_text = row.get("error") if isinstance(row.get("error"), str) else None
        append_step_outcome(
            run_output_dir=output_dir,
            outcome=build_step_outcome(
                workflow_name=str(workflow.get("name") or deploy_bundle.get("name") or "production_milestone_8"),
                step_index=idx,
                step=step,
                status=status,
                error=RuntimeError(err_text) if err_text else None,
                notes="production_milestone_8",
            ),
        )

    generate_standard_reports(run_output_dir=output_dir, overwrite=True)


def _assert_required_artifacts(output_dir: Path) -> None:
    expected = _read_json(FIXTURE_DIR / "expected_artifacts.json")
    required = expected.get("required")
    if not isinstance(required, list):
        raise AssertionError("expected_artifacts.json must contain required list")
    for rel in required:
        if not isinstance(rel, str):
            raise AssertionError("artifact path must be a string")
        _assert_nonempty(output_dir / rel)


def _assert_failure_semantics(output_dir: Path, runtime_summary: Mapping[str, Any]) -> str:
    assert runtime_summary.get("success") is False, runtime_summary
    errors = runtime_summary.get("errors")
    assert isinstance(errors, list) and errors, runtime_summary
    assert any("wait_for_selector failed" in str(err) for err in errors), runtime_summary

    step_logs = runtime_summary.get("step_logs")
    assert isinstance(step_logs, list) and len(step_logs) == 2, runtime_summary
    assert isinstance(step_logs[0], Mapping) and step_logs[0].get("status") == "success", step_logs
    assert isinstance(step_logs[1], Mapping) and step_logs[1].get("status") == "failure", step_logs
    assert "wait_for_selector failed" in str(step_logs[1].get("error")), step_logs

    outcomes = (output_dir / "history" / "step_outcomes.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(outcomes) == 2, outcomes
    outcome_records = [json.loads(line) for line in outcomes]
    assert outcome_records[0]["status"] == "ok", outcome_records
    assert outcome_records[1]["status"] == "error", outcome_records
    assert outcome_records[1]["step_index"] == 1, outcome_records
    assert "wait_for_selector failed" in outcome_records[1]["error"]["message"], outcome_records

    report = _read_json(output_dir / "report" / "run_report.json")
    assert report["run"]["status"] == "error", report
    assert report["summary"]["status_counts"]["ok"] == 1, report
    assert report["summary"]["status_counts"]["error"] == 1, report
    assert report["summary"]["error_steps"] == [1], report

    md = (output_dir / "report" / "run_report.md").read_text(encoding="utf-8")
    assert "- **status**: error" in md, md
    assert "### Failed step 1" in md, md
    assert "wait_for_selector failed" in md, md

    manifest = _read_json(output_dir / "history" / "run_manifest.json")
    assert manifest["extra"]["expected_failure"] == "missing_selector", manifest

    return "missing_selector_runtime_failure"


def _run_failure_proof_once(*, run_dir: Path, site_url: str, browser: str) -> str:
    from RUN.run_1e_deploy_bundle_runner_adapter import run_deploy_bundle_1a_with_meta
    from WORKFLOWS.workflow_1g_deploy_bundle_loader import load_deploy_bundle_1a_from_path

    output_dir = run_dir / browser / "missing_selector"
    bundle, bundle_path = _prepare_run_bundle(run_dir, site_url)

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
    assert run_meta.get("bundle_version"), run_meta

    _ensure_failure_log(output_dir, runtime_summary)
    _copy_fingerprint(loaded, output_dir)
    _write_history_and_reports(
        deploy_bundle=loaded,
        bundle_path=bundle_path,
        runtime_summary=runtime_summary,
        output_dir=output_dir,
    )
    _assert_required_artifacts(output_dir)
    return _assert_failure_semantics(output_dir, runtime_summary)


def _assert_git_status_clean() -> None:
    import subprocess

    cp = subprocess.run(
        ["git", "status", "--short", "--branch"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if cp.returncode != 0:
        raise AssertionError(f"git status failed\nstdout={cp.stdout}\nstderr={cp.stderr}")
    dirty: list[str] = []
    for line in cp.stdout.splitlines()[1:]:
        if not line.strip():
            continue
        path = line[3:].replace("\\", "/")
        if path in _SELF_STATUS_PATHS:
            continue
        if path.startswith(_SELF_STATUS_PREFIXES):
            continue
        dirty.append(line)
    assert not dirty, cp.stdout


def dev_smoke() -> bool:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    base = time.time_ns()
    run_dirs = [OUT_ROOT / f"run_{base}_{os.getpid()}_{idx}" for idx in range(2)]
    for run_dir in run_dirs:
        run_dir.mkdir(parents=True, exist_ok=False)

    httpd: ThreadingHTTPServer | None = None
    thread: threading.Thread | None = None
    try:
        httpd, thread, site_url = _start_static_server()
        browser, unavailable = _select_available_browser(run_dirs[0])
        if browser is None:
            reason = "; ".join(unavailable) if unavailable else "no compatible browser candidate succeeded"
            print(f"SKIP: production_milestone_8 real browser unavailable: {reason}")
            return False

        classifications = [
            _run_failure_proof_once(run_dir=run_dir, site_url=site_url, browser=browser)
            for run_dir in run_dirs
        ]
        assert run_dirs[0] != run_dirs[1], run_dirs
        assert classifications == ["missing_selector_runtime_failure", "missing_selector_runtime_failure"], classifications
        _assert_git_status_clean()
        return True
    finally:
        if httpd is not None:
            httpd.shutdown()
            httpd.server_close()
        if thread is not None:
            thread.join(timeout=5)


if __name__ == "__main__":
    if dev_smoke():
        print("DEV_SMOKE_OK: production_milestone_8")
