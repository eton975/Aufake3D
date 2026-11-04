#!/usr/bin/env python3
"""Adjust two legacy pinned-reference regression tests for the v0.9.2 revision-aware gate.

Dry-run by default; --apply modifies ONLY tests/test_pinned_local_build.py.
Preserves tests for historical ZIP hash enforcement and mandatory local report,
while mocking the Git-provenance decision that is independently tested by
`test_pinned_reference_revision.py`.
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
from pathlib import Path
import shutil
import sys

TARGET = Path('tests/test_pinned_local_build.py')
GATE = Path('scripts/build_pinned.py')
NEW_TEST = Path('tests/test_pinned_reference_revision.py')
METHODS = (
    'test_reference_hash_mismatch_is_a_hard_error',
    'test_reference_hash_match_requires_mandatory_check_report',
)
MOCK_OLD = "            with patch.object(pin, 'pinned_uv', return_value=cache/'uv'), \\\n"
MOCK_NEW = (
    '            # Git/commit provenance is covered by test_pinned_reference_revision.\n'
    '            # Force the exact-reference branch to exercise the legacy ZIP gate.\n'
    "            with patch.object(pin, 'reference_checkout_is_exact', return_value=True), \\\n"
    "                 patch.object(pin, 'pinned_uv', return_value=cache/'uv'), \\\n"
)


def transform(src: str) -> str:
    if '\r\n' in src:
        raise RuntimeError('Unexpected CRLF in regression source; refusing rewrite')
    sections = []
    for name in METHODS:
        marker = '    def ' + name + '(self):\n'
        if src.count(marker) != 1:
            raise RuntimeError('Expected exactly one test method: ' + name)
        start = src.index(marker)
        end = src.find('\n    def ', start + len(marker))
        if end < 0:
            end = src.find('\n\nif __name__', start + len(marker))
        if end < 0:
            raise RuntimeError('Could not identify method boundary: ' + name)
        section = src[start:end]
        if section.count(MOCK_OLD) != 1:
            raise RuntimeError('Expected original mock block once in ' + name)
        if 'reference_checkout_is_exact' in section:
            raise RuntimeError('Test seems already updated: ' + name)
        sections.append((start, end, section.replace(MOCK_OLD, MOCK_NEW, 1)))
    for start, end, revised in reversed(sections):
        src = src[:start] + revised + src[end:]
    ast.parse(src, filename=str(TARGET))
    return src


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    dest = root/TARGET
    try:
        if not dest.is_file() or not (root/GATE).is_file() or not (root/NEW_TEST).is_file():
            raise RuntimeError('Missing required v0.9.2 test or revision-aware source file')
        if 'def reference_checkout_is_exact(' not in (root/GATE).read_text(encoding='utf-8'):
            raise RuntimeError('Revision-aware historical gate is not installed')
        original = dest.read_text(encoding='utf-8')
        revised = transform(original)
        print('Target:', dest)
        print('Only two existing regression tests will be updated:')
        for name in METHODS:
            print('  -', name)
        print('Pinned build implementation and release binaries: UNCHANGED')
        if not args.apply:
            print('DRY RUN PASSED; no files changed. Re-run with --apply.')
            return 0
        backup = root.parent/('Aufake3D_Pinned_Test_Backup_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
        backup.mkdir(mode=0o700, exist_ok=False)
        shutil.copy2(dest, backup/dest.name)
        dest.write_text(revised, encoding='utf-8', newline='')
        print('PATCH APPLIED. Previous test file backed up outside checkout:', backup/dest.name)
        print('Next: python3 -m unittest discover -s tests -p "test_pinned_*.py" -v')
        print('Then: ./BUILD_LINUX.sh')
        return 0
    except (OSError, ValueError, RuntimeError, SyntaxError) as exc:
        print('PATCH REFUSED:', exc, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
