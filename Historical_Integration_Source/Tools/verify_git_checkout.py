#!/usr/bin/env python3
"""Check that an actual Git commit preserves all files in the release manifest."""
from pathlib import Path
import subprocess,json,sys
r=Path(__file__).resolve().parent.parent
manifest=json.loads((r/'MANIFEST_SHA256.json').read_text())['files']
try:
    tracked=set(subprocess.check_output(['git','ls-files','--cached','--full-name'],cwd=r,text=True).splitlines())
except (OSError,subprocess.CalledProcessError):
    print('Not a Git checkout; check only in a staged Git repository',file=sys.stderr)
    sys.exit(2)
missing=sorted(set(manifest)-tracked)
if missing:
    print('FAIL: ignored/untracked files named in release manifest:',file=sys.stderr)
    for x in missing:print(' - '+x,file=sys.stderr)
    sys.exit(1)
print('PASS:',len(manifest),'manifest files tracked by Git')
