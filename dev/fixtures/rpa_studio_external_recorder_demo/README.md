# PM15 External Recorder Demo Fixture

This fixture is a deterministic local HTTP page for Production Milestone 15.

It is intentionally safe:

- no external network dependency
- no credentials
- no downloads
- stable selectors for a text input, password field, submit button, and result area

The PM15 smoke opens this page in a real Selenium/WebDriver-controlled browser,
injects the experimental recorder script, captures Click and Type actions, and
verifies that password field values are skipped or redacted.
