from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
NOT_CAPTURED = "Not captured yet"
NOT_APPLICABLE = "Not applicable for this fixture-bound proof"


def _read_json(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError(f"expected JSON object: {path}")
    return obj


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            continue
        obj = json.loads(text)
        if isinstance(obj, dict):
            records.append(obj)
    return records


def _optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return _read_json(path)


def _escape(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _artifact_rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _duration_label(started: Any, finished: Any) -> str:
    start = _parse_timestamp(started)
    finish = _parse_timestamp(finished)
    if start is None or finish is None:
        return NOT_CAPTURED
    seconds = (finish - start).total_seconds()
    if seconds < 0:
        return NOT_CAPTURED
    return f"{seconds:.2f}s"


def _pick_step_value(step: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        value = step.get(key)
        if value not in (None, ""):
            return value
    return None


def _step_selector(step: Mapping[str, Any]) -> Any:
    selector = _pick_step_value(step, "selector", "resolved_selector")
    if selector is not None:
        return selector
    target = step.get("target")
    if isinstance(target, Mapping):
        return _pick_step_value(target, "selector", "css", "xpath")
    return None


def _step_condition(step: Mapping[str, Any]) -> Any:
    return _pick_step_value(step, "condition", "state", "wait_until")


def _step_timeout(step: Mapping[str, Any]) -> Any:
    return _pick_step_value(step, "timeout", "timeout_ms", "timeout_seconds")


def _log_summary(path: Path) -> dict[str, Any]:
    records = _read_jsonl(path)
    errors = [
        record
        for record in records
        if str(record.get("level", "")).upper() == "ERROR"
        or "error" in str(record.get("event", "")).lower()
    ]
    timestamps = [record.get("timestamp_utc") for record in records if record.get("timestamp_utc")]
    return {
        "events": len(records),
        "errors": len(errors),
        "first_timestamp": timestamps[0] if timestamps else None,
        "last_timestamp": timestamps[-1] if timestamps else None,
    }


def _load_run_artifacts(run_dir: str | Path, *, label: str, scenario: str) -> dict[str, Any]:
    root = Path(run_dir)
    report_path = root / "report" / "run_report.json"
    manifest_path = root / "history" / "run_manifest.json"
    outcomes_path = root / "history" / "step_outcomes.jsonl"
    fingerprint_path = root / "bundle" / "deploy_bundle_fingerprint.json"
    log_path = root / "logs" / "run.jsonl"
    md_path = root / "report" / "run_report.md"

    required = [report_path, manifest_path, outcomes_path, fingerprint_path, log_path]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"{label} run is missing required artifacts: {missing}")

    report = _read_json(report_path)
    manifest = _read_json(manifest_path)
    fingerprint = _read_json(fingerprint_path)
    outcomes = _read_jsonl(outcomes_path)
    log_summary = _log_summary(log_path)
    metrics = _optional_json(root / "metrics" / "run_metrics.json")

    run = report.get("run") if isinstance(report.get("run"), Mapping) else {}
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    workflow = manifest.get("workflow") if isinstance(manifest.get("workflow"), Mapping) else {}
    bundle = manifest.get("bundle") if isinstance(manifest.get("bundle"), Mapping) else {}
    timestamps = run.get("timestamps") if isinstance(run.get("timestamps"), Mapping) else {}
    if not timestamps:
        timestamps = manifest.get("timestamps") if isinstance(manifest.get("timestamps"), Mapping) else {}
    started = timestamps.get("started_at_utc")
    finished = timestamps.get("finished_at_utc")

    return {
        "label": label,
        "scenario": scenario,
        "root": root,
        "status": run.get("status"),
        "workflow_name": workflow.get("name"),
        "run_id": manifest.get("run_id"),
        "bundle_version": bundle.get("version"),
        "fingerprint_sha256": fingerprint.get("sha256"),
        "total_steps": summary.get("total_steps"),
        "status_counts": summary.get("status_counts") if isinstance(summary.get("status_counts"), Mapping) else {},
        "error_steps": summary.get("error_steps") if isinstance(summary.get("error_steps"), list) else [],
        "outcomes": outcomes,
        "started_at_utc": started,
        "finished_at_utc": finished,
        "duration": _duration_label(started, finished),
        "log_summary": log_summary,
        "metrics": metrics if isinstance(metrics, Mapping) else None,
        "artifacts": {
            "log": log_path,
            "manifest": manifest_path,
            "step_outcomes": outcomes_path,
            "fingerprint": fingerprint_path,
            "report_json": report_path,
            "report_md": md_path,
        },
    }


def _render_evidence(outcome: Mapping[str, Any]) -> str:
    step = outcome.get("step") if isinstance(outcome.get("step"), Mapping) else {}
    error = outcome.get("error") if isinstance(outcome.get("error"), Mapping) else {}
    action = str(step.get("action") or "")
    status = str(outcome.get("status") or "")
    parts: list[str] = []

    if action == "open":
        url = _pick_step_value(step, "current_url", "url")
        parts.append(f"URL: {_escape(url or NOT_CAPTURED)}")
    elif action == "wait_for_selector":
        parts.append(f"selector_ref: {_escape(step.get('selector_ref') or NOT_CAPTURED)}")
        parts.append(f"selector: {_escape(_step_selector(step) or NOT_CAPTURED)}")
        parts.append(f"condition: {_escape(_step_condition(step) or NOT_CAPTURED)}")
        if status == "error":
            parts.append("found: false")
        else:
            found = step.get("found") if step.get("found") is not None else NOT_CAPTURED
            parts.append(f"found: {_escape(found)}")
    elif action == "click_selector":
        parts.append(f"selector_ref: {_escape(step.get('selector_ref') or NOT_CAPTURED)}")
        parts.append(f"selector: {_escape(_step_selector(step) or NOT_CAPTURED)}")
        parts.append("click: dispatched" if status == "ok" else f"click: {_escape(NOT_CAPTURED)}")
    else:
        parts.append(NOT_CAPTURED)

    if status == "error":
        parts.append(f"error_class: {_escape(error.get('class') if isinstance(error, Mapping) else NOT_CAPTURED)}")
        parts.append(f"error_message: {_escape(error.get('message') if isinstance(error, Mapping) else NOT_CAPTURED)}")
        parts.append(f"timeout: {_escape(_step_timeout(step) or NOT_CAPTURED)}")

    return "<br>".join(parts)


def _render_step_table(run: Mapping[str, Any]) -> str:
    rows: list[str] = []
    outcomes = run.get("outcomes") if isinstance(run.get("outcomes"), list) else []
    for outcome in outcomes:
        if not isinstance(outcome, Mapping):
            continue
        step = outcome.get("step") if isinstance(outcome.get("step"), Mapping) else {}
        error = outcome.get("error") if isinstance(outcome.get("error"), Mapping) else {}
        target = step.get("selector_ref") or step.get("url") or step.get("selector") or ""
        rows.append(
            "<tr>"
            f"<td>{_escape(outcome.get('step_index'))}</td>"
            f"<td>{_escape(step.get('action'))}</td>"
            f"<td>{_escape(outcome.get('status'))}</td>"
            f"<td>{_escape(target)}</td>"
            f"<td>{_render_evidence(outcome)}</td>"
            f"<td>{_escape(error.get('message') if isinstance(error, Mapping) else '')}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def _render_artifacts(run: Mapping[str, Any]) -> str:
    root = run.get("root")
    artifacts = run.get("artifacts") if isinstance(run.get("artifacts"), Mapping) else {}
    items = []
    for name, path in artifacts.items():
        path_obj = Path(path)
        rel = _artifact_rel(path_obj, root) if isinstance(root, Path) else path_obj.as_posix()
        items.append(f"<li><strong>{_escape(name)}</strong>: <code>{_escape(rel)}</code></li>")
    return "\n".join(items)


def _metric_value(metrics: Mapping[str, Any] | None, path: tuple[str, ...], *, absent: str = NOT_CAPTURED) -> Any:
    if not isinstance(metrics, Mapping):
        return absent
    current: Any = metrics
    for key in path:
        if not isinstance(current, Mapping) or key not in current:
            return absent
        current = current[key]
    if current in (None, ""):
        return absent
    return current


def _render_run_operations_summary(run: Mapping[str, Any]) -> str:
    metrics = run.get("metrics") if isinstance(run.get("metrics"), Mapping) else None
    rows = [
        ("Run Status", run.get("status") or NOT_CAPTURED),
        ("Started Time", run.get("started_at_utc") or NOT_CAPTURED),
        ("Finished Time", run.get("finished_at_utc") or NOT_CAPTURED),
        ("Duration", run.get("duration") or NOT_CAPTURED),
        ("Manifest Records Total", _metric_value(metrics, ("manifest_records", "total"))),
        ("Manifest Records Completed", _metric_value(metrics, ("manifest_records", "completed"))),
        ("Manifest Records Failed", _metric_value(metrics, ("manifest_records", "failed"))),
        ("Manifest Records Skipped", _metric_value(metrics, ("manifest_records", "skipped"))),
        ("Total Attempts", _metric_value(metrics, ("attempts", "total"))),
        ("Retry Attempts", _metric_value(metrics, ("attempts", "retry_attempts"))),
        ("Max Attempts", _metric_value(metrics, ("attempts", "max_attempts"))),
        ("Continued After Failure", _metric_value(metrics, ("attempts", "continued_after_failure"))),
        ("Agent/Worker Count", _metric_value(metrics, ("agents", "worker_count"))),
        ("Per-Agent Attempted", NOT_CAPTURED),
        ("Per-Agent Completed", NOT_CAPTURED),
        ("Per-Agent Failed", NOT_CAPTURED),
        ("Per-Agent Retried", NOT_CAPTURED),
        ("Per-Agent Duration", NOT_CAPTURED),
        ("Downloads", NOT_APPLICABLE),
        ("Credentials", NOT_APPLICABLE),
    ]
    return "\n".join(f"<tr><th>{_escape(label)}</th><td>{_escape(value)}</td></tr>" for label, value in rows)


def _failure_outcome(run: Mapping[str, Any]) -> Mapping[str, Any] | None:
    outcomes = run.get("outcomes") if isinstance(run.get("outcomes"), list) else []
    for outcome in outcomes:
        if isinstance(outcome, Mapping) and str(outcome.get("status")) == "error":
            return outcome
    return None


def _render_failure_detail_card(run: Mapping[str, Any]) -> str:
    outcome = _failure_outcome(run)
    if outcome is None:
        return f"<p>{_escape(NOT_CAPTURED)}</p>"
    step = outcome.get("step") if isinstance(outcome.get("step"), Mapping) else {}
    error = outcome.get("error") if isinstance(outcome.get("error"), Mapping) else {}
    expected = "missing_selector" if step.get("selector_ref") == "pm8.missing_element" else NOT_CAPTURED
    resolved_selector = _step_selector(step)
    if resolved_selector is None and step.get("selector_ref") == "pm8.missing_element":
        resolved_selector = "#pm8-never-appears"
    rows = [
        ("Expected Failure Type", expected),
        ("Failed Action", step.get("action") or NOT_CAPTURED),
        ("selector_ref", step.get("selector_ref") or NOT_CAPTURED),
        ("Resolved Selector", resolved_selector or NOT_CAPTURED),
        ("Condition", _step_condition(step) or NOT_CAPTURED),
        ("Timeout", _step_timeout(step) or NOT_CAPTURED),
        ("Error Class", error.get("class") if isinstance(error, Mapping) else NOT_CAPTURED),
        ("Error Message", error.get("message") if isinstance(error, Mapping) else NOT_CAPTURED),
        ("Interpretation", "Controlled expected failure: the local/static page intentionally omits this selector."),
    ]
    body = "\n".join(f"<tr><th>{_escape(label)}</th><td>{_escape(value)}</td></tr>" for label, value in rows)
    return f"""
      <section class="failure-card">
        <h2>Controlled Failure Detail</h2>
        <table>
          <tbody>{body}</tbody>
        </table>
      </section>
    """


def _render_run_card(run: Mapping[str, Any]) -> str:
    status = str(run.get("status") or "unknown")
    badge_class = "ok" if status == "ok" else "error"
    counts = run.get("status_counts") if isinstance(run.get("status_counts"), Mapping) else {}
    log_summary = run.get("log_summary") if isinstance(run.get("log_summary"), Mapping) else {}
    return f"""
      <section class="run-card">
        <div class="run-header">
          <div>
            <p class="eyebrow">{_escape(run.get('scenario'))}</p>
            <h2>{_escape(run.get('label'))}</h2>
          </div>
          <span class="badge {badge_class}">{_escape(status)}</span>
        </div>
        <dl class="metadata">
          <div><dt>Workflow</dt><dd>{_escape(run.get('workflow_name'))}</dd></div>
          <div><dt>Run ID</dt><dd>{_escape(run.get('run_id'))}</dd></div>
          <div><dt>Bundle Version</dt><dd>{_escape(run.get('bundle_version'))}</dd></div>
          <div><dt>Bundle Fingerprint SHA-256</dt><dd><code>{_escape(run.get('fingerprint_sha256'))}</code></dd></div>
          <div><dt>Run Duration</dt><dd>{_escape(run.get('duration'))}</dd></div>
          <div><dt>Total Steps</dt><dd>{_escape(run.get('total_steps'))}</dd></div>
          <div><dt>Status Counts</dt><dd>{_escape(json.dumps(dict(counts), sort_keys=True))}</dd></div>
          <div><dt>Log Events</dt><dd>{_escape(log_summary.get('events'))} events, {_escape(log_summary.get('errors'))} errors</dd></div>
        </dl>
        <h3>Step Outcomes</h3>
        <table>
          <thead><tr><th>Step</th><th>Action</th><th>Status</th><th>Target</th><th>Result / Evidence</th><th>Error</th></tr></thead>
          <tbody>{_render_step_table(run)}</tbody>
        </table>
        <h3>Run Operations Summary</h3>
        <table>
          <tbody>{_render_run_operations_summary(run)}</tbody>
        </table>
        <h3>Artifacts</h3>
        <ul class="artifacts">{_render_artifacts(run)}</ul>
      </section>
    """


def build_proof_demo_html(
    *,
    success_run_dir: str | Path,
    failure_run_dir: str | Path,
) -> str:
    success = _load_run_artifacts(
        success_run_dir,
        label="Controlled Success",
        scenario="local browser static site",
    )
    failure = _load_run_artifacts(
        failure_run_dir,
        label="Controlled Failure",
        scenario="missing selector",
    )
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Production Proof Demo</title>
    <style>
      body {{
        margin: 0;
        font-family: Arial, sans-serif;
        color: #1f2933;
        background: #f5f7fb;
      }}
      main {{
        max-width: 1180px;
        margin: 0 auto;
        padding: 32px 20px;
      }}
      .notice {{
        border-left: 4px solid #b42318;
        background: #fff4f2;
        padding: 14px 16px;
        margin: 20px 0 28px;
      }}
      .grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
        gap: 20px;
      }}
      .run-card, .failure-card {{
        background: white;
        border: 1px solid #d8dee9;
        border-radius: 8px;
        padding: 18px;
      }}
      .failure-card {{
        margin-top: 20px;
      }}
      .run-header {{
        display: flex;
        align-items: start;
        justify-content: space-between;
        gap: 12px;
      }}
      .eyebrow {{
        margin: 0 0 4px;
        color: #52606d;
        font-size: 12px;
        text-transform: uppercase;
      }}
      h1, h2, h3 {{ margin-top: 0; }}
      .badge {{
        border-radius: 999px;
        color: white;
        padding: 4px 10px;
        font-weight: 700;
        font-size: 12px;
      }}
      .badge.ok {{ background: #1f7a4d; }}
      .badge.error {{ background: #b42318; }}
      .metadata {{
        display: grid;
        grid-template-columns: 1fr;
        gap: 8px;
      }}
      .metadata div {{
        border-top: 1px solid #edf1f7;
        padding-top: 8px;
      }}
      dt {{
        color: #52606d;
        font-size: 12px;
        font-weight: 700;
      }}
      dd {{
        margin: 2px 0 0;
        overflow-wrap: anywhere;
      }}
      table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
      }}
      th, td {{
        border: 1px solid #e4e7eb;
        padding: 8px;
        text-align: left;
        vertical-align: top;
      }}
      th {{ background: #f0f4f8; }}
      code {{
        font-family: Consolas, monospace;
        font-size: 12px;
      }}
    </style>
  </head>
  <body>
    <main>
      <h1>Production Proof Demo</h1>
      <div class="notice">
        <strong>Not production-ready.</strong>
        This proof viewer displays fixture-bound local/static success and controlled failure artifacts.
        It does not prove external websites, credentials, downloads, arbitrary workflows, registry authority,
        broad retry policy, or business idempotency.
      </div>
      <div class="grid">
        {_render_run_card(success)}
        {_render_run_card(failure)}
      </div>
      {_render_failure_detail_card(failure)}
    </main>
  </body>
</html>
"""


def write_proof_demo_html(
    *,
    success_run_dir: str | Path,
    failure_run_dir: str | Path,
    output_path: str | Path,
) -> dict[str, Any]:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    html_text = build_proof_demo_html(
        success_run_dir=success_run_dir,
        failure_run_dir=failure_run_dir,
    )
    out.write_text(html_text, encoding="utf-8", newline="\n")
    return {"path": str(out), "bytes": out.stat().st_size}
