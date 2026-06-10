from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dev import dev_smoke_production_milestone_5 as pm5  # noqa: E402

SCENARIO = "local-browser-static-site"
PASS_LINE = "PASS: production_proof local-browser"
FAIL_PREFIX = "FAIL: production_proof local-browser"
SKIP_PREFIX = "SKIP: production_proof local-browser real browser unavailable"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "dev" / "_smoke_artifacts" / "production_proof"


def _artifact_paths(output_dir: Path) -> list[str]:
    expected = pm5._read_json(pm5.FIXTURE_DIR / "expected_artifacts.json")
    required = expected.get("required")
    if not isinstance(required, list):
        raise AssertionError("expected_artifacts.json must contain required list")
    return [str((output_dir / rel).resolve()) for rel in required if isinstance(rel, str)]


def _json_summary(
    *,
    status: str,
    run_dir: Path | None,
    browser: str | None,
    artifacts: Sequence[str] = (),
    message: str,
) -> dict[str, Any]:
    return {
        "status": status,
        "scenario": SCENARIO,
        "run_dir": str(run_dir.resolve()) if run_dir is not None else None,
        "browser": browser,
        "artifacts": list(artifacts),
        "message": message,
    }


def _print_result(summary: Mapping[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(dict(summary), indent=2, sort_keys=True, ensure_ascii=True))
        return
    print(str(summary["message"]))
    if summary.get("run_dir"):
        print(f"run_dir: {summary['run_dir']}")
    if summary.get("browser"):
        print(f"browser: {summary['browser']}")


def _browser_unavailable_message(unavailable: Sequence[str]) -> str:
    reason = "; ".join(unavailable) if unavailable else "no compatible browser candidate succeeded"
    return f"{SKIP_PREFIX}: {reason}"


def run_local_browser_proof(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    output_root = Path(args.output_root)
    if not output_root.is_absolute():
        output_root = REPO_ROOT / output_root
    output_root.mkdir(parents=True, exist_ok=True)

    pm5.OUT_ROOT = output_root
    pm5.RUN_OUT_DIR = output_root / f"run_{pm5.time.time_ns()}_{os.getpid()}"
    pm5.RUN_OUT_DIR.mkdir(parents=True, exist_ok=False)

    old_browser = os.environ.get("RPA_PM5_BROWSER")
    old_headed = os.environ.get("RPA_PM5_HEADED")
    if args.browser != "auto":
        os.environ["RPA_PM5_BROWSER"] = args.browser
    else:
        os.environ.pop("RPA_PM5_BROWSER", None)
    if args.headed:
        os.environ["RPA_PM5_HEADED"] = "1"
    else:
        os.environ.pop("RPA_PM5_HEADED", None)

    httpd = None
    thread = None
    selected_browser: str | None = None
    try:
        httpd, thread, site_url = pm5._start_static_server()
        selected_browser, unavailable = pm5._select_available_browser()
        if selected_browser is None:
            message = _browser_unavailable_message(unavailable)
            return 2, _json_summary(
                status="skip",
                run_dir=pm5._run_dir(),
                browser=None,
                message=message,
            )

        try:
            pm5._run_positive_with_browser(selected_browser, site_url)
        except Exception as exc:
            if isinstance(exc, pm5.BrowserUnavailable) or pm5._looks_browser_unavailable(exc):
                unavailable.append(f"{selected_browser}: {type(exc).__name__}: {exc}")
                message = _browser_unavailable_message(unavailable)
                return 2, _json_summary(
                    status="skip",
                    run_dir=pm5._run_dir(),
                    browser=selected_browser,
                    message=message,
                )
            raise

        output_dir = pm5._run_dir() / selected_browser / "positive"
        artifacts = _artifact_paths(output_dir)
        for artifact in artifacts:
            pm5._assert_nonempty(Path(artifact))
        return 0, _json_summary(
            status="pass",
            run_dir=pm5._run_dir(),
            browser=selected_browser,
            artifacts=artifacts,
            message=PASS_LINE,
        )
    except Exception as exc:
        message = f"{FAIL_PREFIX}: {type(exc).__name__}: {exc}"
        return 1, _json_summary(
            status="fail",
            run_dir=pm5.RUN_OUT_DIR,
            browser=selected_browser,
            message=message,
        )
    finally:
        if httpd is not None:
            httpd.shutdown()
            httpd.server_close()
        if thread is not None:
            thread.join(timeout=5)
        if old_browser is None:
            os.environ.pop("RPA_PM5_BROWSER", None)
        else:
            os.environ["RPA_PM5_BROWSER"] = old_browser
        if old_headed is None:
            os.environ.pop("RPA_PM5_HEADED", None)
        else:
            os.environ["RPA_PM5_HEADED"] = old_headed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rpa-production-proof")
    sub = parser.add_subparsers(dest="command", required=True)

    proof = sub.add_parser("run-local-browser-proof", help="Run the fixture-bound local browser production proof.")
    proof.add_argument("--browser", choices=("chrome", "edge", "auto"), default="auto")
    proof.add_argument("--headed", action="store_true")
    proof.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT.relative_to(REPO_ROOT)))
    proof.add_argument("--json", action="store_true", dest="as_json")
    proof.set_defaults(handler=run_local_browser_proof)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.as_json:
        with contextlib.redirect_stdout(io.StringIO()):
            code, summary = args.handler(args)
    else:
        code, summary = args.handler(args)
    _print_result(summary, as_json=bool(args.as_json))
    return int(code)


if __name__ == "__main__":
    raise SystemExit(main())
