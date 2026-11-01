#!/usr/bin/env python3
"""Offline provenance spot-check. This is not a legal copyright audit."""
from pathlib import Path
import json,hashlib,sys
r=Path(__file__).resolve().parent.parent
inventory=json.loads((r/'Docs/RELEASE_ARTIFACT_INVENTORY.json').read_text())
assert (r/'LICENSE').read_text().startswith('MIT License')
notices=(r/'THIRD_PARTY_NOTICES.md').read_text()
for who in ('Bill Gardner','Keith Martin','MIT Media Laboratory'):
 assert who in notices, who
assert (r/'Source/Engine/acoustics/LICENSE').is_file()
assert not (r/'Game_Kits/Alice_2011_VorpalFix/COPY_TO_GAME_FOLDER/a3d_mss_real.dll').exists()
for entry in inventory['entries']:
 p=r/entry['path']
 if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=entry['sha256']:
  print('FAIL: missing/changed audit entry',entry['path'],file=sys.stderr);sys.exit(1)
print('PASS:',len(inventory['entries']),'audited file hashes; licence and KEMAR attribution present')
