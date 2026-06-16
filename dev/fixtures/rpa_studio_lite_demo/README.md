# RPA Studio Lite Demo Fixture

This fixture is a controlled local/static page for Production Milestone 13.

It is intentionally small and safe:

- No external website support.
- No credentials.
- No downloads.
- No arbitrary workflow execution.
- No retry, resume, or multi-agent behavior.

The sample workflow opens this page, waits for the input, types demo text,
clicks the submit button, and waits for the local success state.

PM13 run behavior: the Studio Lite UI runs the bundled local sample workflow only. Edited workflow JSON can be built and saved, but custom workflow replay is deferred to a future milestone.
