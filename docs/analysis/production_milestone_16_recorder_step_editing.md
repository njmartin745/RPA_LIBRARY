# Production Milestone 16: Recorder Step Editing MVP

## What PM16 Adds

Production Milestone 16 adds a visible step-editing surface to the PM15
Playwright controlled browser recorder. It is not production-ready.

The UI now shows:

- `RPA Studio Step Editor - PM16`
- `PM16 - Recorder Step Editing MVP`
- delete selected step
- insert explicit/custom `Wait for Selector` before or after the selected step
- insert `Wait Seconds` before or after the selected step
- mark a Type step as Secret / Password
- enable or disable a step
- move the selected step up or down
- save the edited workflow JSON
- run all steps or run from the selected step using the edited action list

## How To Launch

```powershell
python dev/rpa_studio_playwright_recorder.py serve
```

Then open:

```text
http://127.0.0.1:8879/
```

## Manual Demo Steps

1. Launch the Playwright recorder.
2. Record Type and Click actions on the controlled local PM15 page.
3. Select a recorded step in the action list.
4. Delete one step.
5. Add `Wait for Selector` for the selected element.
6. Add `Wait Seconds`.
7. Mark a Type step as Secret / Password.
8. Disable one step.
9. Move one step up or down.
10. Save workflow JSON.
11. Run the edited workflow.
12. Confirm run evidence and logs reflect skipped disabled/secret steps.

## Recorder Lifecycle

The UI separates browser, recorder injection, and recording state:

- Browser status shows whether the controlled Playwright browser is open.
- Recorder injection shows whether the active page has the recorder script
  installed.
- Recording state shows whether new actions are actively being captured.

Injection is not the same as active recording. `Inject Recorder / Reattach`
prepares the current page for recording, but user actions are captured only
while Recording state is `recording`. If reattach succeeds while recording is
idle or stopped, the UI reports: `Recorder injected. Click Start Recording to
capture actions.`

`Start Recording` auto-injects the recorder when possible. If injection fails,
recording does not start and the UI/log show the failure reason. Reattach is
primarily for page reloads, page navigation, or cases where capture stops and
the current page needs the recorder script installed again.

## What Is Demoable Now

- Recorded workflows can be edited before replay.
- Disabled steps remain in workflow JSON with `enabled: false`.
- Replay applies a default readiness wait before target interactions.
- Explicit `Wait for Selector` and `Wait Seconds` steps are honored by replay.
- Adjacent duplicate `Navigate` actions to the same URL are deduped.
- Click capture prefers stable clickable ancestors over fragile child selectors.
- Type steps can be converted to redacted `TypeSecret` steps.
- Saved edited workflow JSON omits raw secret text.
- Selected steps can still highlight target elements where selectors resolve.

## What Remains Deferred

- Credential vault support.
- Replaying real secret values.
- Downloads.
- Retry or resume orchestration.
- Multi-agent execution.
- Universal external website support.
- Production readiness.

## Safety Notes

PM16 does not store raw password values. When a user marks a Type step as secret,
the raw `text` field is removed, `TypeSecret` is used, and a placeholder
`secret_ref` is stored. Replay logs a clear skip message because no credential
vault exists yet.

Generated artifacts remain under ignored `dev/_smoke_artifacts/` paths.

## Replay Readiness And Explicit Waits

Replay automatically waits for each target element before normal interaction
steps. For Click, Type, TypeSecret, and Wait for Selector actions, the recorder
uses a default readiness wait equivalent to:

```json
{
  "wait_before": {
    "type": "selector",
    "selector": "the action selector",
    "state": "visible",
    "timeout": 10
  }
}
```

Explicit waits remain available for unusual pacing or custom readiness, but they
are no longer the default way to make every normal interaction safe.

## Selector And Navigation Behavior

Click recording prefers stable clickable ancestors. If a user clicks a child
element inside a stable anchor, button, or role-clickable parent, the recorder
uses the parent selector when it is strong or usable. For example, clicking:

```html
<a id="anch_49"><h3>Device Characteristics</h3></a>
```

should record `#anch_49` with a strong selector instead of a fragile
`#anch_49 > h3:nth-of-type(1)` child selector.

Navigate actions remain useful page-transition checkpoints. Adjacent duplicate
Navigate actions to the same URL are coalesced so they do not clutter the edited
workflow.
