#!/usr/bin/env python3
"""v0.6.11 opt-in automatic weapon forensics package, unified A3D DLL."""
from pathlib import Path
import shutil,hashlib,zipfile,sys
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'deploy-v0610'
OUT=ROOT/'deploy-v0611'
if OUT.exists():shutil.rmtree(OUT)
shutil.copytree(BASE,OUT)
for game in ('Alice2000','Alice2011-VorpalFix','QuakeIII-117'):
 dest=OUT/game
 for name in ('a3dapi.dll','a3d.dll','a3d-selftest.exe','a3d-comtest.exe','a3d-quake3-lock-test.exe'):
  shutil.copy2(ROOT/'win32/build'/name,dest/name)
 # Safe default launchers retain their known-good queue, FPS and logging policy.
 for name in ('RUN_A3D_WINDOWS.cmd','RUN_A3D_WINE.sh'):
  p=dest/name
  t=p.read_text()
  t=t.replace('v0.6.9:', 'v0.6.11:')
  t=t.replace('A3D v0.6.9 /','A3D v0.6.11 /')
  p.write_bytes(t.replace('\r\n','\n').replace('\n','\r\n').encode() if p.suffix=='.cmd' else t.encode())
 for name in ('analyse_weapons_v0611.py','weapon_reference_catalog_v0611.json'):
  shutil.copy2(ROOT/'tools'/name,dest/('ANALYSE_WEAPONS_V0611.py' if name.endswith('.py') else name))
 if game.startswith('Alice'):
  if game=='Alice2000': short='alice2000'
  else:short='alice2011'
  cmdbody='''@echo off
setlocal
rem A3D v0.6.11 AUTO weapon forensics, opt-in only. No disk writes during gameplay.
set "A3D_STAFF_DIAG=1"
set "A3D_WEAPON_CAPTURE=1"
set "A3D_LOG=1"
set "A3D_TRACE_DETAIL=0"
set "A3D_LATENCY_TRACE=0"
set "A3D_PROBE_LOG=%~dp0a3d-v0611-weapon-__GAME__-windows.log"
set "A3D_WEAPON_CAPTURE_PATH=%~dp0a3d-v0611-weapon-__GAME__-windows.bin"
echo A3D weapon-source capture in RAM enabled. Play normally; quit game normally.
call "%~dp0RUN_A3D_WINDOWS.cmd" %*
set "RESULT=%errorlevel%"
echo Generated reports: a3d-v0611-weapon-__GAME__-windows.log and .bin
exit /b %RESULT%
'''.replace('__GAME__',short)
  (dest/'RUN_A3D_WEAPON_DIAGNOSTIC_WINDOWS.cmd').write_bytes(cmdbody.replace('\n','\r\n').encode())
  sh='''#!/usr/bin/env bash
set -euo pipefail
here="$(cd -- "$(dirname -- "$0")" && pwd)"
export A3D_STAFF_DIAG=1 A3D_WEAPON_CAPTURE=1 A3D_LOG=1 A3D_TRACE_DETAIL=0 A3D_LATENCY_TRACE=0
export A3D_PROBE_LOG="$here/a3d-v0611-weapon-__GAME__-wine.log"
export A3D_WEAPON_CAPTURE_PATH="$here/a3d-v0611-weapon-__GAME__-wine.bin"
exec bash "$here/RUN_A3D_WINE.sh" "$@"
'''.replace('__GAME__',short)
  p=dest/'RUN_A3D_WEAPON_DIAGNOSTIC_WINE.sh';p.write_text(sh);p.chmod(0o755)
  # Optional Windows helper, if user has Python installed; NOT a game dependency.
  cmd='''@echo off
setlocal
cd /d "%~dp0"
if not exist "a3d-v0611-weapon-__GAME__-windows.bin" (echo Capture not found. Exit the game normally after running weapon diagnostic. & exit /b 2)
if not exist "Weapons.zip" (echo Place a copy of your own 100-WAV weapons ZIP here as Weapons.zip. & exit /b 3)
python ANALYSE_WEAPONS_V0611.py "a3d-v0611-weapon-__GAME__-windows.bin" --archive Weapons.zip --log "a3d-v0611-weapon-__GAME__-windows.log"
exit /b %errorlevel%
'''.replace('__GAME__',short)
  (dest/'ANALYSE_WEAPONS_WINDOWS.cmd').write_bytes(cmd.replace('\n','\r\n').encode())
# Root docs.
shutil.copy2(ROOT/'README_v0611_WEAPON_FORENSICS.md',OUT/'README_v0611_WEAPON_FORENSICS.md')
shutil.copy2(ROOT/'tools/weapon_reference_catalog_v0611.json',OUT/'weapon_reference_catalog_v0611.json')
# No original WAV content in any generated package.
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert len({sha(OUT/g/'a3dapi.dll') for g in ('Alice2000','Alice2011-VorpalFix','QuakeIII-117')})==1
files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt')
(OUT/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.relative_to(OUT).as_posix()+'\n' for p in files))
print('Packaged:',len(files),'files plus checksums, 3 identical shared DLLs')
for p in OUT.rglob('*.sh'):p.chmod(0o755)
