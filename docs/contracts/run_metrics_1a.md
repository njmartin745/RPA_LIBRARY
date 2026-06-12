# RUN-METRICS-1A Contract

## Purpose

`RUN-METRICS-1A` defines the future `{run_output_dir}/metrics/run_metrics.json` artifact.

This contract is documentation only until a runtime writer is explicitly implemented. Example fixtures are not runtime-generated proof artifacts and do not prove retry, resume, multi-agent, record manifest, or idempotency behavior.

## Artifact Path

Runtime path, when implemented:

`metrics/run_metrics.json`

The path is relative to `run_output_dir`.

## Scope

The artifact summarizes run-level operational telemetry:

- run identity and status
- timestamps and duration
- record counts, only when explicit record telemetry exists
- attempt and retry counts, only when explicit attempt telemetry exists
- continuation/resume state, only when explicit resume telemetry exists
- agent/worker counts, only when explicit worker telemetry exists
- relative source artifact paths

## Required Fields

- `schema`: must be `RUN-METRICS-1A`
- `example_only`: boolean
- `runtime_generated`: boolean
- `notes`: string
- `run_id`: string
- `status`: string
- `timestamps`: object
- `manifest_records`: object
- `attempts`: object
- `agents`: object
- `sources`: object

## Nullable Fields

Unknown or unproven fields must remain `null`, not `0`:

- `timestamps.finished_at_utc`
- `timestamps.duration_ms`
- `manifest_records.total`
- `manifest_records.completed`
- `manifest_records.failed`
- `manifest_records.skipped`
- `attempts.total`
- `attempts.retry_attempts`
- `attempts.max_attempts`
- `attempts.continued_after_failure`
- `agents.worker_count`
- per-worker counts and durations
- optional source paths when the source artifact does not exist

## Redaction And Safety

Do not capture credentials, cookies, tokens, secrets, raw payloads, downloaded contents, or raw customer/account/person identifiers.

Safe identifiers must be non-secret and workflow-local.

## Compatibility

Existing proof runs remain valid without this file. The Milestone 10 viewer may read this file if present in a run artifact directory, but must continue to show `Not captured yet` when it is absent.

