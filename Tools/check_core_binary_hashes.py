#!/usr/bin/env python3
"""Verify locally compiled PE32 core DLLs against the audited 0.8.13 baseline."""
import hashlib,json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
pins=json.loads((root/'CORE_BINARY_HASHES.json').read_text())
for name,expected in pins.items():
    p=root/'dist'/'core'/name
    if not p.is_file():sys.exit(f'MISSING build output: {p} (run python3 scripts/build_engine.py first)')
    actual=hashlib.sha256(p.read_bytes()).hexdigest()
    if actual!=expected:sys.exit(f'HASH MISMATCH {name}: {actual}; baseline {expected}')
    print(f'REPRODUCIBLE: {name} {actual}')
