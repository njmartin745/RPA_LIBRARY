# Action Registry (REGISTRY-1A)

- Generated: `2026-04-23T20:05:20.406427Z`
- Schema version: `SCHEMA-1A`
- Action count: `9`

## Actions

### `click_selector`

- Implemented by: `VAL/val_2a_deploy_bundle_validator.py` (`VAL-2A`)
- Handler: _(unknown)_
- Required fields: `action`
- Optional fields: `name`, `selector`, `selector_ref`, `strategy`
- Smoke tests: _(none discovered)_

### `exec_js`

- Implemented by: ``
- Handler: _(unknown)_
- Required fields: `action`, `script`
- Optional fields: `name`
- Smoke tests: _(none discovered)_

### `exec_js_file`

- Implemented by: ``
- Handler: _(unknown)_
- Required fields: `action`, `path`
- Optional fields: `name`
- Smoke tests: _(none discovered)_

### `log`

- Implemented by: ``
- Handler: _(unknown)_
- Required fields: `action`, `message`
- Optional fields: `name`
- Smoke tests: _(none discovered)_

### `open`

- Implemented by: `PIPE/pipe_1d_step_executor.py` (`PIPE-1D`)
- Handler: _(unknown)_
- Required fields: `action`, `url`
- Optional fields: `name`
- Smoke tests: _(none discovered)_

### `repeat`

- Implemented by: ``
- Handler: _(unknown)_
- Required fields: `action`, `steps`, `times`
- Optional fields: `name`
- Smoke tests: _(none discovered)_

### `switch_back_to_main_tab`

- Implemented by: ``
- Handler: _(unknown)_
- Required fields: `action`
- Optional fields: `name`
- Smoke tests: _(none discovered)_

### `type_selector_secret`

- Implemented by: ``
- Handler: _(unknown)_
- Required fields: `action`, `secret`
- Optional fields: `name`, `selector`, `selector_ref`, `strategy`
- Smoke tests: _(none discovered)_

### `wait_for_selector`

- Implemented by: ``
- Handler: _(unknown)_
- Required fields: `action`
- Optional fields: `name`, `selector`, `selector_ref`, `strategy`
- Smoke tests: _(none discovered)_
