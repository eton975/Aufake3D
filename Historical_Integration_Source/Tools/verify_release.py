#!/usr/bin/env python3
"""Check every distributed file against relative SHA-256 manifest."""
from pathlib import Path
import hashlib,sys,json
r=Path(__file__).resolve().parent.parent
m=json.loads((r/'MANIFEST_SHA256.json').read_text(encoding='utf-8'))
fail=[]
for rel,expect in m['files'].items():
 p=r/rel
 if not p.is_file():fail.append('missing '+rel);continue
 h=hashlib.sha256(p.read_bytes()).hexdigest()
 if h!=expect:fail.append('hash mismatch '+rel)
extra=[str(x.relative_to(r)).replace('\\','/') for x in r.rglob('*') if x.is_file() and x.name!='MANIFEST_SHA256.json' and '.git' not in x.parts and '__pycache__' not in x.parts and x.suffix != '.pyc' and str(x.relative_to(r)).replace('\\','/') not in m['files']]
fail += ['unlisted '+x for x in extra]
if fail:print('\n'.join(fail),file=sys.stderr);sys.exit(1)
print('PASS:',len(m['files']),'files match SHA-256 manifest')
