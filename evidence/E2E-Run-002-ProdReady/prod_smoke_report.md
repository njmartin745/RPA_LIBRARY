# Prod Smoke Pipeline Report: dev_smoke_12_6_1

- Schema: `run_12a_prod_smoke_pipeline/v1`
- Created date: `2026-04-23`
- Notes: dev_smoke
- Report fingerprint (sha256): `bfc595b3360754b36e2c7a1dcf952a0236dedff8f7d9e4d72248da1fb0a0948e`

## Workflow summary

```json
{"step_count":5,"workflow_id":"wf_prod_smoke_12_6_1"}
```

## Selectors summary

```json
{"selector_count":2,"selector_refs_sorted":["smoke.body","smoke.root"]}
```

## Checks

```json
{"allowed_actions_ok":true,"allowed_actions_problems":[]}
```

## Evidence bundle (embedded)

```json
{"artifact_inventory":[{"name":"run_outcome.json","sha256":"fb5b73f8764a7faad249d970dda31b9c2adb2d769d8407803d8f95121242a7f3","size_bytes":44},{"name":"selectors.json","sha256":"8dde0d5507292c6eb866290e4ef99438f4c09fa6c7b3c820b6dcf6b185d291b3","size_bytes":83},{"name":"workflow.json","sha256":"c7c0dbeee5c6513f5ca76f29d55361d4a3f54a3168ff38649cd4a3156f73d402","size_bytes":400}],"bundle_fingerprint_sha256":"94f25d6c9a6abb08271bf1c4586f0b12b4dbb32e7ba3661ece544213e7da4975","bundle_id":"evidence::dev_smoke_12_6_1","created_date":"2026-04-23","notes":"prod_smoke_pipeline","schema":"report_12g_evidence_bundle_assembler/v1","scope":"prod_smoke","sections":{"alerting":{"derived_from":"prod_smoke","signals":[]},"incident_packet_manifest":{"kind":"smoke","scenario_id":"dev_smoke_12_6_1"},"release_readiness":{"ok":true,"problems":[]},"replay_verification":{"note":"CI-safe: no replay verification performed","ok":true}}}
```
