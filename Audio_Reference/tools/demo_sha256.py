#!/usr/bin/env python3
"""Print SHA-256 for any supplied demo file, to confirm copies match."""
import hashlib
import pathlib
import sys
if len(sys.argv) < 2:
    raise SystemExit('Usage: python tools/demo_sha256.py path/to/demo.dm3 [more files]')
for name in sys.argv[1:]:
    h = hashlib.sha256()
    with open(name, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    print(f'{h.hexdigest()}  {pathlib.Path(name)}')
