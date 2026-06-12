# RECORD-OUTCOME-1A Contract

## Purpose

`RECORD-OUTCOME-1A` defines the future `{run_output_dir}/history/record_outcomes.jsonl` artifact.

This contract is documentation only until a runtime writer is explicitly implemented. Example fixtures are not runtime-generated proof artifacts.

## Artifact Path

Runtime path, when implemented:

`history/record_outcomes.jsonl`

The path is relative to `run_output_dir`.

## Scope

The artifact records append-only per-record lifecycle outcomes:

- safe record identity
- record ordinal
- record status
- timestamps and duration
- attempt and retry counts when explicit attempt telemetry exists
- worker id when real worker execution exists
- safe error summary
- related step outcome indexes

## Required Fields Per Line

Each JSONL line must contain one JSON object with:

- `schema`: must be `RECORD-OUTCOME-1A`
- `example_only`: boolean
- `runtime_generated`: boolean
- `notes`: string
- `run_id`: string
- `record_id`: string
- `record_index`: integer
- `status`: string
- `timestamps`: object
- `attempt_count`: integer or null
- `retry_count`: integer or null
- `worker_id`: string or null
- `related_step_indexes`: array
- `error`: object or null

## Nullable Fields

Unknown or unproven fields must remain `null`, not `0`:

- `timestamps.finished_at_utc`
- `timestamps.duration_ms`
- `attempt_count`
- `retry_count`
- `worker_id`
- `error`

## Safe Record IDs

`record_id` must be deterministic, non-secret, and workflow-local. If no safe business identifier exists, use an ordinal id such as `record_000001`.

Never use raw customer identifiers, account numbers, emails, credentials, cookies, tokens, secrets, raw payloads, or downloaded contents.

## Compatibility

This artifact is additive. Existing `history/run_manifest.json`, `history/step_outcomes.jsonl`, and reports remain valid without it.

