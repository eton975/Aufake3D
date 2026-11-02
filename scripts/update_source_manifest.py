#!/usr/bin/env python3
"""Explicitly refresh the *frozen* source snapshot after reviewing changes.

Never run this as a routine CI step. An ordinary PR must not be blocked just
because its source bytes intentionally changed from the last release.
"""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ignored={'.git','dist','build','__pycache__'}
# Ignore generated freestanding link outputs in Source/Engine paths as well.
# This updater is an explicit release snapshot operation, not a CI preflight.
generated_suffixes={'.exe','.dll','.lib','.obj','.o','.exp','.pdb','.bsp','.pyc','.zip'}
paths=sorted(p for p in ROOT.rglob('*') if p.is_file()
             and not (ignored & set(p.relative_to(ROOT).parts))
             and p.suffix.lower() not in generated_suffixes
             and p.name not in ('SOURCE_MANIFEST_SHA256.json','SHA256SUMS.txt'))
# Prevent Git checkout failures on Windows' usual case-insensitive filesystem.
names={}
for p in paths:
    rel=p.relative_to(ROOT).as_posix()
    folded=rel.casefold()
    if folded in names:
        raise SystemExit('Case-insensitive filename collision: '+names[folded]+' vs '+rel)
    names[folded]=rel
files={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
(ROOT/'SOURCE_MANIFEST_SHA256.json').write_text(json.dumps({'release':'0.9.2',
    'type':'source-only', 'files':files},indent=2,sort_keys=True)+'\n')
(ROOT/'SHA256SUMS.txt').write_text(''.join(f'{h}  {name}\n' for name,h in sorted(files.items(),key=lambda x:x[1])))
print('Frozen source manifest updated:',len(files),'files. Review diff before commit.')
