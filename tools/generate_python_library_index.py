"""
MODULE: REPO-INTEL-1A
PURPOSE:
    Generate repository intelligence artifacts from module docstrings.

OUTPUTS:
    docs/repository/PYTHON_LIBRARY_INDEX.md

RULES:
    - Read first module docstring only.
    - Do not inspect implementation code.
    - Report files missing headers.
    - Report duplicate module IDs.

STATUS:
    Repository Intelligence Milestone 1
"""

from pathlib import Path
import ast
import re

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'docs' / 'repository' / 'PYTHON_LIBRARY_INDEX.md'

EXCLUDE_DIRS = {
    '.git',
    '__pycache__',
    '.venv',
    'venv'
}


def get_module_docstring(py_file: Path):
    try:
        source = py_file.read_text(encoding='utf-8')
        module = ast.parse(source)
        return ast.get_docstring(module)
    except Exception as exc:
        return f'ERROR: {exc}'


def extract_module_id(docstring: str):
    if not docstring:
        return None
    match = re.search(r'MODULE:\s*([^\n]+)', docstring)
    return match.group(1).strip() if match else None


def iter_python_files(root: Path):
    for path in root.rglob('*.py'):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        yield path


def main():
    rows = []
    missing_headers = []
    module_ids = {}
    duplicates = []

    for py_file in sorted(iter_python_files(ROOT)):
        rel = py_file.relative_to(ROOT)
        doc = get_module_docstring(py_file)

        if not doc or doc.startswith('ERROR:'):
            missing_headers.append(str(rel))
            continue

        module_id = extract_module_id(doc)

        if module_id:
            if module_id in module_ids:
                duplicates.append((module_id, str(rel)))
            module_ids[module_id] = str(rel)

        rows.append((str(rel), module_id or 'UNKNOWN', doc.strip()))

    lines = []
    lines.append('# Python Library Index')
    lines.append('')
    lines.append('AUTO-GENERATED. DO NOT EDIT MANUALLY.')
    lines.append('')

    for rel, module_id, doc in rows:
        lines.append(f'## {rel}')
        lines.append('')
        lines.append(f'**Module:** {module_id}')
        lines.append('')
        lines.append('```')
        lines.append(doc)
        lines.append('```')
        lines.append('')

    lines.append('# Missing Headers')
    lines.append('')
    for item in missing_headers:
        lines.append(f'- {item}')

    lines.append('')
    lines.append('# Duplicate Module IDs')
    lines.append('')
    for module_id, path in duplicates:
        lines.append(f'- {module_id}: {path}')

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text('\n'.join(lines), encoding='utf-8')

    print(f'Generated: {OUTPUT}')
    print(f'Modules: {len(rows)}')
    print(f'Missing Headers: {len(missing_headers)}')
    print(f'Duplicate IDs: {len(duplicates)}')


if __name__ == '__main__':
    main()
