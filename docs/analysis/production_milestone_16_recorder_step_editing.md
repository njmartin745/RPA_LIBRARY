# Production Milestone 16: Recorder Step Editing MVP

## What PM16 Adds

Production Milestone 16 adds a visible step-editing surface to the PM15
Playwright controlled browser recorder. It is not production-ready.

The UI now shows:

- `RPA Studio Step Editor - PM16`
- `PM16 - Recorder Step Editing MVP`
- delete selected step
- insert `Wait for Selector` before or after the selected step
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

## What Is Demoable Now

- Recorded workflows can be edited before replay.
- Disabled steps remain in workflow JSON with `enabled: false`.
- `Wait for Selector` and `Wait Seconds` steps are honored by replay.
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
