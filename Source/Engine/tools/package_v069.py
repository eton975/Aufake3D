#!/usr/bin/env python3
"""Create deterministic common-core 3-game v0.6.9 candidate from one source checkout."""
from pathlib import Path
import hashlib,json,shutil,zipfile
ROOT=Path(__file__).resolve().parents[1]
DEPLOY=ROOT/'deploy-v069'
P=json.loads((ROOT/'config/game_profiles_v069.json').read_text())
shutil.rmtree(DEPLOY,ignore_errors=True)
from generate_launchers_v069 import generate
generate()
for game,setting in P.items():
 d=DEPLOY/game
 common=ROOT/'win32/build'
 for fname in ('a3dapi.dll','a3d.dll','a3d-selftest.exe','a3d-comtest.exe','a3d-quake3-lock-test.exe'):
  shutil.copy2(common/fname,d/fname)
 shutil.copy2(ROOT/setting['bridge_src'],d/setting['bridge_exe'])
 manifest='quake3.exe.manifest' if game=='QuakeIII-117' else 'Alice.exe.manifest'
 shutil.copy2(ROOT/'dropin'/manifest,d/(setting['game_exe']+'.manifest'))
 shutil.copy2(ROOT/'dropin/a3d-comtest.exe.manifest',d/'a3d-comtest.exe.manifest')
 if game=='Alice2011-VorpalFix':
  # THIS IS A MANIFEST/PE32 DELIVERY, not bundling user game files.
  # VorpalFix's winmm.dll and Miles plugins must already exist in game dir.
  pass
# root documents
for fname in ('README_v069.md','DEBIAN13_WINE.md','DEBIAN13_PREFLIGHT.sh','DEBIAN13_ABI_SMOKE.sh'):
 shutil.copy2(ROOT/fname,DEPLOY/fname)
# copy known-good defaults from pre-v069 rollback, not a replacement for user backup.
backup=DEPLOY/'KnownGoodReferences'
for game,setting in P.items():
 d=backup/game;d.mkdir(parents=True,exist_ok=True)
 baseline=ROOT/'profiles'/game
 for fname in ('RUN_A3D_WINDOWS.cmd','RUN_A3D_WINE.sh'):
  if (baseline/fname).exists():shutil.copy2(baseline/fname,d/fname)
 # True compiled code rollback is in user backed-up original game, not this folder.
 (d/'README.txt').write_text('Reference-only launcher configuration. Back up your installed DLLs before upgrading; these are not complete rollback binaries.\n')
# Hash input binaries to prove byte-identical shared core.
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for fname in ('a3dapi.dll','a3d.dll'):
 assert len({sha(DEPLOY/g/fname) for g in P})==1,(fname,'not identical')
files=sorted(p for p in DEPLOY.rglob('*') if p.is_file())
(DEPLOY/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.relative_to(DEPLOY).as_posix()+'\n' for p in files))
print('Dist complete:',len(files),'files plus checksums; shared DLL hashes identical across profiles')
