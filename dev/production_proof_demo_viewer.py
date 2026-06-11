from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]


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


def _escape(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _artifact_rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        return path.as_posix()


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

    run = report.get("run") if isinstance(report.get("run"), Mapping) else {}
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    workflow = manifest.get("workflow") if isinstance(manifest.get("workflow"), Mapping) else {}
    bundle = manifest.get("bundle") if isinstance(manifest.get("bundle"), Mapping) else {}

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
        "log_summary": log_summary,
        "artifacts": {
            "log": log_path,
            "manifest": manifest_path,
            "step_outcomes": outcomes_path,
            "fingerprint": fingerprint_path,
            "report_json": report_path,
            "report_md": md_path,
        },
    }


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
          <div><dt>Total Steps</dt><dd>{_escape(run.get('total_steps'))}</dd></div>
          <div><dt>Status Counts</dt><dd>{_escape(json.dumps(dict(counts), sort_keys=True))}</dd></div>
          <div><dt>Log Events</dt><dd>{_escape(log_summary.get('events'))} events, {_escape(log_summary.get('errors'))} errors</dd></div>
        </dl>
        <h3>Step Outcomes</h3>
        <table>
          <thead><tr><th>Step</th><th>Action</th><th>Status</th><th>Target</th><th>Error</th></tr></thead>
          <tbody>{_render_step_table(run)}</tbody>
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
    failure_text = json.dumps(failure.get("outcomes", []), sort_keys=True)
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
      .run-card {{
        background: white;
        border: 1px solid #d8dee9;
        border-radius: 8px;
        padding: 18px;
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
      <section>
        <h2>Controlled Failure Detail</h2>
        <p>The failure proof is expected to fail on <code>pm8.missing_element</code> / <code>#pm8-never-appears</code>.</p>
        <pre>{_escape(failure_text)}</pre>
      </section>
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
