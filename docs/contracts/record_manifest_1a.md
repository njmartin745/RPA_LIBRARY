# RECORD-MANIFEST-1A Contract

## Purpose

`RECORD-MANIFEST-1A` defines the future optional `{run_output_dir}/history/record_manifest.json` artifact.

This contract is documentation only until a runtime writer is explicitly implemented. Example fixtures are not runtime-generated proof artifacts and do not prove record manifest processing.

## Artifact Path

Runtime path, when implemented:

`history/record_manifest.json`

The path is relative to `run_output_dir`.

## Scope

The artifact describes the record source for a run:

- safe record id strategy
- expected record counts when explicitly known
- source artifact reference and fingerprint
- redaction policy metadata
- schema versions for related record telemetry

It must not contain raw record payloads.

## Required Fields

- `schema`: must be `RECORD-MANIFEST-1A`
- `example_only`: boolean
- `runtime_generated`: boolean
- `notes`: string
- `run_id`: string
- `record_id_strategy`: object
- `source`: object
- `expected_records`: object
- `redaction`: object

## Nullable Fields

Unknown or unproven fields must remain `null`, not `0`:

- `source.path`
- `source.sha256`
- `expected_records.total`
- `expected_records.completed`
- `expected_records.failed`
- `expected_records.skipped`

## Safe IDs And Redaction

Record ids must be deterministic, non-secret, and workflow-local. Prefer generated ordinal ids such as `record_000001` when no safe identifier exists.

Do not capture raw customer/account/person identifiers, credentials, cookies, tokens, secrets, raw payloads, or downloaded contents.

## Compatibility

This artifact is optional and additive. Future `record_outcomes.jsonl` can reference the strategy defined here, but existing proof runs remain valid without it.

