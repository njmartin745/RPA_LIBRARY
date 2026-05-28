# E2E-Run-001 (baseline)

## Canonical E2E definition
- Canonical run name: Production Smoke Pipeline
- Canonical entrypoint: PIPE/pipe_1e_runner.py
- Canonical smoke reference: dev/dev_smoke_12_6_1_prod_smoke_pipeline.py

## Run evidence (this baseline)
- run_id: <PASTE RUN_ID HERE>
- exit_code: 0
- steps source: WORKFLOWS\e2e_smoke_example_com.json
- artifacts:
  - run.log.jsonl
  - run.manifest.jsonl
  - pipe_1e_manifest__t2of33i.jsonl (legacy capture)

## Readiness criteria (from canonical definition)
- workflow grammar gates pass
- pipeline execution completes
- release manifest is generated
- bundle fingerprint is generated
- DOCTOR gates pass
- GUARD gates pass