#!/usr/bin/env python3
"""v0.6.12 experimental weapon clarity, unified 3-game build / deploy."""
from pathlib import Path
import hashlib,shutil,zipfile
ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'deploy-v0611'
OUT=ROOT/'deploy-v0612'
assert OLD.exists(), 'v0.6.11 verified deploy directory required for this packaging pass'
if OUT.exists():shutil.rmtree(OUT)
shutil.copytree(OLD,OUT)
GAMES=('Alice2000','Alice2011-VorpalFix','QuakeIII-117')
for game in GAMES:
 dest=OUT/game
 for name in ('a3dapi.dll','a3d.dll','a3d-selftest.exe','a3d-comtest.exe','a3d-quake3-lock-test.exe'):
  shutil.copy2(ROOT/'win32/build'/name,dest/name)
 # The game-specific version-pinned COM bridges and other known-good files stay untouched.
 for name in ('RUN_A3D_WINDOWS.cmd','RUN_A3D_WINE.sh'):
  p=dest/name
  text=p.read_text().replace('v0.6.11','v0.6.12')
  if game.startswith('Alice'):
   if p.suffix=='.cmd':
    assert 'if not defined A3D_MASTER_GAIN' in text
    text=text.replace('if not defined A3D_MASTER_GAIN',
       'if not defined A3D_WEAPON_CLARITY set "A3D_WEAPON_CLARITY=1"\nif not defined A3D_MASTER_GAIN',1)
   else:
    assert 'export A3D_MASTER_GAIN' in text
    text=text.replace('export A3D_MASTER_GAIN',
       'export A3D_WEAPON_CLARITY="${A3D_WEAPON_CLARITY:-1}"\nexport A3D_MASTER_GAIN',1)
  else:
   if p.suffix=='.cmd':
    text=text.replace('if not defined A3D_MASTER_GAIN',
      'if not defined A3D_WEAPON_CLARITY set "A3D_WEAPON_CLARITY=0"\nif not defined A3D_MASTER_GAIN',1)
   else:
    text=text.replace('export A3D_MASTER_GAIN',
      'export A3D_WEAPON_CLARITY="${A3D_WEAPON_CLARITY:-0}"\nexport A3D_MASTER_GAIN',1)
  p.write_bytes(text.replace('\r\n','\n').replace('\n','\r\n').encode() if p.suffix=='.cmd' else text.encode())
 if game.startswith('Alice'):
  fallback='''@echo off
setlocal
rem v0.6.12 bit-identical legacy limiter/mixer fallback; preserve queue and FPS settings.
set "A3D_WEAPON_CLARITY=0"
call "%~dp0RUN_A3D_WINDOWS.cmd" %*
exit /b %errorlevel%
'''
  (dest/'RUN_A3D_ORIGINAL_MIX_WINDOWS.cmd').write_bytes(fallback.replace('\n','\r\n').encode())
  wine='''#!/usr/bin/env bash
set -euo pipefail
export A3D_WEAPON_CLARITY=0
exec bash "$(dirname -- "$0")/RUN_A3D_WINE.sh" "$@"
'''
  p=dest/'RUN_A3D_ORIGINAL_MIX_WINE.sh';p.write_text(wine);p.chmod(0o755)
  # Direct and legacy diagnostic launchers remain available unchanged.
shutil.copy2(ROOT/'README_v0612_WEAPON_CLARITY.md',OUT/'README_v0612_WEAPON_CLARITY.md')
# No private user-captured PCM, original weapon audio, or ripped game files.
assert not any(p.suffix.lower() in ('.wav','.flac','.bin') for p in OUT.rglob('*') if p.is_file())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for dll in ('a3dapi.dll','a3d.dll'):
 assert len({sha(OUT/game/dll) for game in GAMES})==1
files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt')
(OUT/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.relative_to(OUT).as_posix()+'\n' for p in files))
print(f'Built deploy v0.6.12: {len(files)} files, shared DLL identities PASS')
