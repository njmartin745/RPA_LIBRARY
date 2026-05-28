# Repository Intelligence

Purpose: maintain an always-current inventory of repository capabilities.

## Status Definitions

- Exists = File/module exists in repository.
- Tested = Behavior has been executed and verified.
- Signed Off = Capability validated and accepted.

Important:

Exists != Tested
Tested != Signed Off

## Process

1. Build library index.
2. Build capability map.
3. Audit capability.
4. Test capability.
5. Sign off capability.

## Generated Artifacts

- PYTHON_LIBRARY_INDEX.md
- CAPABILITY_MAP.md
- AUDIT_STATUS.md

## Generator

Run:

```bash
python tools/generate_python_library_index.py
```
