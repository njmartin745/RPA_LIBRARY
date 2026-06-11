# Action Contract Alignment Report

## Summary

Production Milestone 7 adds read-only inspection for the current action contract. It does not make `REGISTRY/action_registry.json` authoritative, does not change runtime behavior, and does not change production validation semantics.

The current proven golden path action set is:

- `open`
- `wait_for_selector`
- `click_selector`

These actions are present in the registry/schema/SNAP action declarations and are implemented by ACT-1A.

## Registry Status

`REGISTRY/action_registry.json` remains informational in this milestone. It is useful as a declaration inventory, but it is not yet reliable as the runtime source of truth because implementation metadata and field expectations do not fully match ACT-1A.

## Known Gaps

- `log` is declared by the registry, schema, and SNAP allow-list, but it is not implemented by ACT-1A. Production validation should continue rejecting it before runtime.
- `repeat` is declared by the registry, schema, and SNAP allow-list, but it is not implemented by ACT-1A in the proven runtime path.
- ACT-1A implements canonical and alias actions that are not declared in the registry/schema/SNAP action contract, including `get`, `wait`, `wait_for_element`, `click`, `type`, `select`, `js`, `switch_frame`, `switch_tab`, `assert`, and `download_wait`.
- Selector actions declare `strategy` in registry/schema metadata, while ACT-1A runtime execution expects `by`.
- `exec_js` declares `script`, while capture helper code can emit `js` and ACT-1A reads `script` or `path`.
- `type_selector_secret` registry/schema metadata references `secret`, while production validation accepts `secret_ref`, `text_secret_ref`, or `value_secret_ref`, and ACT-1A accepts `secret` or legacy `text`.

## Deferred Actions

Milestone 7 does not add runtime support for `log`, `repeat`, downloads, credentials, retries, idempotency, or external website behavior.

Future work should decide whether the registry becomes partially authoritative only after the declared action names, implementation mapping, field names, and production support levels are reviewed and aligned.
