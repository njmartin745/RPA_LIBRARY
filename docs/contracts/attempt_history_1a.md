# ATTEMPT-HISTORY-1A Contract

## Purpose

`ATTEMPT-HISTORY-1A` defines the future `{run_output_dir}/history/attempt_history.jsonl` artifact.

This contract is documentation only until a runtime writer is explicitly implemented. Example fixtures are not runtime-generated proof artifacts and do not prove retry or resume behavior.

## Artifact Path

Runtime path, when implemented:

`history/attempt_history.jsonl`

The path is relative to `run_output_dir`.

## Scope

The artifact records explicit attempt events for run, record, or step scope:

- initial attempts
- future retry attempts
- future resume-triggered attempts
- attempt status
- timestamps and duration
- safe error summary

Repeated smoke runs are not retries. Directory counts are not attempt counts.

## Required Fields Per Line

Each JSONL line must contain one JSON object with:

- `schema`: must be `ATTEMPT-HISTORY-1A`
- `example_only`: boolean
- `runtime_generated`: boolean
- `notes`: string
- `run_id`: string
- `attempt_id`: string
- `scope`: `run`, `record`, or `step`
- `record_id`: string or null
- `step_index`: integer or null
- `attempt_index`: integer
- `max_attempts`: integer or null
- `trigger`: string
- `status`: string
- `timestamps`: object
- `error`: object or null

## Nullable Fields

Unknown or unproven fields must remain `null`, not `0`:

- `record_id`
- `step_index`
- `max_attempts`
- `timestamps.finished_at_utc`
- `timestamps.duration_ms`
- `error`

## Safety

Attempt ids must be non-secret and workflow-local. Error fields must be safe summaries only and must not include credentials, cookies, tokens, raw payloads, or downloaded contents.

## Compatibility

This artifact is additive. Existing proof runs remain valid without attempt history.

