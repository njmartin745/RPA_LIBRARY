"""
MODULE: REPO-INTEL-1A
PURPOSE:
    Generate repository intelligence artifacts from module docstrings.

OUTPUTS:
    docs/repository/PYTHON_LIBRARY_INDEX.md
    docs/repository/python_library_index.json

RULES:
    - Read first module docstring only.
    - Do not inspect implementation code.
    - Report files missing headers.
    - Report duplicate module IDs.
"""

from pathlib import Path
import ast
import json
import re
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / 'docs' / 'repository'
OUTPUT_MD = DOCS_DIR / 'PYTHON_LIBRARY_INDEX.md'
OUTPUT_JSON = DOCS_DIR / 'python_library_index.json'

EXCLUDE_DIRS = {'.git', '__pycache__', '.venv', 'venv'}
MODULE_PATTERN = re.compile(r'([A-Z]+-\d+[A-Z]?)')


def get_module_docstring(py_file: Path):
    try:
        source = py_file.read_text(encoding='utf-8')
        module = ast.parse(source)
        return ast.get_docstring(module)
    except Exception:
        return None


def extract_module_id(docstring: str):
    if not docstring:
        return None

    explicit = re.search(r'MODULE:\s*([^\n]+)', docstring)
    if explicit:
        return explicit.group(1).strip()

    for line in docstring.splitlines():
        line = line.strip()
        if not line:
            continue
        match = MODULE_PATTERN.search(line)
        if match:
            return match.group(1)

    return None


def extract_title(docstring: str):
    if not docstring:
        return ''
    for line in docstring.splitlines():
        line = line.strip()
        if line:
            return line
    return ''


def iter_python_files(root: Path):
    for path in root.rglob('*.py'):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        yield path


def main():
    modules = []
    missing_headers = []
    duplicates = []
    module_ids = {}
    categories = Counter()

    for py_file in sorted(iter_python_files(ROOT)):
        rel = str(py_file.relative_to(ROOT))
        doc = get_module_docstring(py_file)

        if not doc:
            missing_headers.append(rel)
            continue

        module_id = extract_module_id(doc)
        category = module_id.split('-')[0] if module_id else 'UNKNOWN'
        title = extract_title(doc)

        if module_id:
            if module_id in module_ids:
                duplicates.append((module_id, rel))
            module_ids[module_id] = rel

        categories[category] += 1

        modules.append({
            'module_id': module_id or 'UNKNOWN',
            'category': category,
            'file': rel,
            'title': title,
            'docstring': doc.strip(),
            'audited': False,
            'tested': False,
            'signed_off': False
        })

    lines = [
        '# Python Library Index',
        '',
        'AUTO-GENERATED. DO NOT EDIT MANUALLY.',
        '',
        '## Repository Summary',
        '',
        '| Category | Count |',
        '|----------|-------|'
    ]

    for category, count in sorted(categories.items()):
        lines.append(f'| {category} | {count} |')

    lines.extend([
        f'| TOTAL | {len(modules)} |',
        '',
        '## Capability Summary',
        '',
        '| Module | Description |',
        '|--------|-------------|'
    ])

    for module in sorted(modules, key=lambda m: m['module_id']):
        lines.append(f"| {module['module_id']} | {module['title']} |")

    lines.append('')

    for module in modules:
        lines.append(f"## {module['file']}")
        lines.append('')
        lines.append(f"**Module ID:** {module['module_id']}")
        lines.append('')
        lines.append('```')
        lines.append(module['docstring'])
        lines.append('```')
        lines.append('')

    lines.append('# Missing Module Headers')
    lines.append('')
    for item in missing_headers:
        lines.append(f'- {item}')

    lines.append('')
    lines.append('# Duplicate Module IDs')
    lines.append('')
    for module_id, path in duplicates:
        lines.append(f'- {module_id}: {path}')

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text('\n'.join(lines), encoding='utf-8')

    OUTPUT_JSON.write_text(json.dumps({
        'module_count': len(modules),
        'missing_header_count': len(missing_headers),
        'duplicate_count': len(duplicates),
        'categories': dict(categories),
        'modules': modules
    }, indent=2), encoding='utf-8')

    print(f'Generated: {OUTPUT_MD}')
    print(f'Generated: {OUTPUT_JSON}')
    print(f'Modules: {len(modules)}')
    print(f'Missing Headers: {len(missing_headers)}')
    print(f'Duplicate IDs: {len(duplicates)}')


if __name__ == '__main__':
    main()
