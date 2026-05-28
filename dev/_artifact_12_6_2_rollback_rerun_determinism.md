# Rollback + Re-run Determinism Report: dev_smoke_12_6_2

- Schema: `run_12b_rollback_rerun_determinism/v1`
- Created date: `2026-04-23`
- Notes: dev_smoke
- Report fingerprint (sha256): `92f4f17258dc1d5c77255bf93e212c183cdbfe1e48df1d6b29091f4535f6728e`

## invariants

```json
{"a1_equals_a2_result_signature":true,"a1_run_record_fingerprint_differs_from_a2":true,"b1_differs_from_a1_result_signature":true,"deployments_a_b_differ_fingerprint":true}
```

## rollback

```json
{"created_date":"2026-04-23","from":{"deployment_fingerprint_sha256":"724b7fa3833a9df1725d1c4f09c50c6df98390dc3375eff5780f6c99e1ef23b7","deployment_id":"dep-B","version":"B"},"reason":"smoke_test: rollback to known-good deployment","rollback_fingerprint_sha256":"5d67ee2070de125211f8d81ca0e91c6d7590e2306b407b6b784203e588551475","scenario_id":"dev_smoke_12_6_2","to":{"deployment_fingerprint_sha256":"a2b3d524f392068c4d828cf9729936caf02ddeab20cbe69427c630e5b9c1aaed","deployment_id":"dep-A","version":"A"}}
```

## deployments

```json
{"A":{"allowed_actions_ok":true,"allowed_actions_problems":[],"deployment_fingerprint_sha256":"a2b3d524f392068c4d828cf9729936caf02ddeab20cbe69427c630e5b9c1aaed","deployment_id":"dep-A","selectors_canon_sha256":"8dde0d5507292c6eb866290e4ef99438f4c09fa6c7b3c820b6dcf6b185d291b3","selectors_refs_sorted":["smoke.body","smoke.root"],"version":"A","workflow_canon_sha256":"0bbb0983a24fa19d872c10307ae4e98c1dc126804dc79ed25fc04cd1b7054f55","workflow_id":"wf_prod_smoke_12_6_2_A"},"B":{"allowed_actions_ok":true,"allowed_actions_problems":[],"deployment_fingerprint_sha256":"724b7fa3833a9df1725d1c4f09c50c6df98390dc3375eff5780f6c99e1ef23b7","deployment_id":"dep-B","selectors_canon_sha256":"8dde0d5507292c6eb866290e4ef99438f4c09fa6c7b3c820b6dcf6b185d291b3","selectors_refs_sorted":["smoke.body","smoke.root"],"version":"B","workflow_canon_sha256":"04fb23856b8d785945e378cfc7c21e71fce0ca83baf17ed81c3e663779906b30","workflow_id":"wf_prod_smoke_12_6_2_B"}}
```

## runs

```json
{"A1":{"created_date":"2026-04-23","deployment_id":"dep-A","deployment_version":"A","evidence_bundle":{"artifact_inventory":[{"name":"deployment.json","sha256":"aca68aa7544a99062e074f1250ecb60593ccb6daead0510901fafe0279b1cfa9","size_bytes":468},{"name":"run_outcome.json","sha256":"5ffd9507f7e71d981352eeab3899ee99ea98fc8b955687d411f49c1d1c50c176","size_bytes":74},{"name":"selectors.json","sha256":"8dde0d5507292c6eb866290e4ef99438f4c09fa6c7b3c820b6dcf6b185d291b3","size_bytes":83},{"name":"workflow.json","sha256":"0bbb0983a24fa19d872c10307ae4e98c1dc126804dc79ed25fc04cd1b7054f55","size_bytes":449}],"bundle_fingerprint_sha256":"1391de0ee19030ed524e712a405c17134871c819ae2195f08af8953cbd01bb88","bundle_id":"evidence::dev_smoke_12_6_2::A1","created_date":"2026-04-23","notes":"run_record","schema":"report_12g_evidence_bundle_assembler/v1","scope":"rollback_rerun_smoke","sections":{"incident_packet_manifest":{"kind":"smoke","run_id":"A1","scenario_id":"dev_smoke_12_6_2"},"release_readiness":{"ok":true,"problems":[]}}},"run_fingerprint_sha256":"08308bdef252fe2ffbe499f0fb2cf1c14d2a3a5177cba104535dc80bb141b41a","run_id":"A1","run_outcome":{"deployment_id":"dep-A","deployment_version":"A","status":"SIMULATED_OK"},"run_result_signature_sha256":"f0dcbe3277cdcb76221ff4798cba8495250216b5eada1acc3ca4900a3619c114"},"A2":{"created_date":"2026-04-23","deployment_id":"dep-A","deployment_version":"A","evidence_bundle":{"artifact_inventory":[{"name":"deployment.json","sha256":"aca68aa7544a99062e074f1250ecb60593ccb6daead0510901fafe0279b1cfa9","size_bytes":468},{"name":"run_outcome.json","sha256":"5ffd9507f7e71d981352eeab3899ee99ea98fc8b955687d411f49c1d1c50c176","size_bytes":74},{"name":"selectors.json","sha256":"8dde0d5507292c6eb866290e4ef99438f4c09fa6c7b3c820b6dcf6b185d291b3","size_bytes":83},{"name":"workflow.json","sha256":"0bbb0983a24fa19d872c10307ae4e98c1dc126804dc79ed25fc04cd1b7054f55","size_bytes":449}],"bundle_fingerprint_sha256":"ced3512e5b096193e5b17ef3861cd037c94f586eac5bd6a5c491a51fc1ac79ee","bundle_id":"evidence::dev_smoke_12_6_2::A2","created_date":"2026-04-23","notes":"run_record","schema":"report_12g_evidence_bundle_assembler/v1","scope":"rollback_rerun_smoke","sections":{"incident_packet_manifest":{"kind":"smoke","run_id":"A2","scenario_id":"dev_smoke_12_6_2"},"release_readiness":{"ok":true,"problems":[]}}},"run_fingerprint_sha256":"0babf0cb5111d09fc5b63f5a0244492ce67ccac4a4da0db16713000624b1af90","run_id":"A2","run_outcome":{"deployment_id":"dep-A","deployment_version":"A","status":"SIMULATED_OK"},"run_result_signature_sha256":"f0dcbe3277cdcb76221ff4798cba8495250216b5eada1acc3ca4900a3619c114"},"B1":{"created_date":"2026-04-23","deployment_id":"dep-B","deployment_version":"B","evidence_bundle":{"artifact_inventory":[{"name":"deployment.json","sha256":"6bf1a31eba2d5160d6b7dc8021417e051439b3ceee2aab18cb6ae52c6a539978","size_bytes":468},{"name":"run_outcome.json","sha256":"2ac10e99ae45e3d31f2bb72210db627a6381b25c73c073ccc73f2e9259b8401c","size_bytes":74},{"name":"selectors.json","sha256":"8dde0d5507292c6eb866290e4ef99438f4c09fa6c7b3c820b6dcf6b185d291b3","size_bytes":83},{"name":"workflow.json","sha256":"04fb23856b8d785945e378cfc7c21e71fce0ca83baf17ed81c3e663779906b30","size_bytes":449}],"bundle_fingerprint_sha256":"21c7f68586f5390ef1aabab70ca464bf8b62c464bf5e9c15224897ac4952c32f","bundle_id":"evidence::dev_smoke_12_6_2::B1","created_date":"2026-04-23","notes":"run_record","schema":"report_12g_evidence_bundle_assembler/v1","scope":"rollback_rerun_smoke","sections":{"incident_packet_manifest":{"kind":"smoke","run_id":"B1","scenario_id":"dev_smoke_12_6_2"},"release_readiness":{"ok":true,"problems":[]}}},"run_fingerprint_sha256":"df1a4187c8fecf14cbaadb89260ea138518a2489a1d7f42de99bfd2660427188","run_id":"B1","run_outcome":{"deployment_id":"dep-B","deployment_version":"B","status":"SIMULATED_OK"},"run_result_signature_sha256":"ae03558e745d94772fa24fdc06885e1f371006717461a99aac5a12208ab16549"}}
```
