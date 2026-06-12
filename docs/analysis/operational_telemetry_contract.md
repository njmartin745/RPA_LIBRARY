# Operational Telemetry Contract

## Summary

This document indexes the Production Milestone 12 telemetry contracts.

These contracts and examples are not runtime-generated proof artifacts yet. They do not prove retry, resume, multi-agent, record manifest, or business idempotency behavior.

## Contracts

- `docs/contracts/run_metrics_1a.md`: future `metrics/run_metrics.json`
- `docs/contracts/record_outcomes_1a.md`: future `history/record_outcomes.jsonl`
- `docs/contracts/attempt_history_1a.md`: future `history/attempt_history.jsonl`
- `docs/contracts/record_manifest_1a.md`: future optional `history/record_manifest.json`

## Example Fixtures

- `dev/fixtures/telemetry_contracts/run_metrics_1a_example.json`
- `dev/fixtures/telemetry_contracts/record_outcomes_1a_example.jsonl`
- `dev/fixtures/telemetry_contracts/attempt_history_1a_example.jsonl`
- `dev/fixtures/telemetry_contracts/record_manifest_1a_example.json`

The fixtures are examples only. They are not emitted by runtime and must not be copied into proof run artifact directories.

## Current Compatibility

Existing proof artifacts remain valid without these telemetry files. The static proof viewer may read `metrics/run_metrics.json` from a run artifact directory if present, but the fixture examples are not viewer inputs.

Reports and runtime modules should not require these artifacts until a future runtime telemetry writer milestone explicitly implements them.

## Safety Rules

- Unknown or unproven operational fields remain `null`, not `0`.
- Safe ids are non-secret and workflow-local.
- Raw customer/account/person identifiers, credentials, cookies, tokens, secrets, raw payloads, and downloaded contents must not be captured.
- Runtime output paths are relative to `run_output_dir`.
- Metrics must come from explicit runtime events or artifacts, not inference from repeated smoke runs, step counts, directory counts, process counts, or browser counts.

## Future Writer Ownership

Future runtime writers should be additive and should likely live near HISTORY/telemetry code, with REPORT and viewer support remaining read-only consumers.

