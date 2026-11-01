#!/usr/bin/env python3
"""Single source of truth for v0.6.9's three installer-ready launch profiles.

Generates self-contained Windows CMD / Debian Wine shell launchers from the same
profile JSON.  The PE32 engine is a *single* common build, with only the verified
runtime settings changing per game. No user-owned EXEs or game assets are bundled.
"""
import json, pathlib, os, stat, sys
BASE=pathlib.Path(__file__).resolve().parents[1]
P=json.loads((BASE/'config/game_profiles_v069.json').read_text())
OUT=BASE/'deploy-v069'

def write(p,s,exe=False):
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_bytes(s.replace('\n','\r\n').encode('utf-8') if p.suffix.lower()=='.cmd' else s.encode('utf-8'))
 if exe:p.chmod(p.stat().st_mode|stat.S_IXUSR|stat.S_IXGRP|stat.S_IXOTH)

def generate():
 for name,c in P.items():
  d=OUT/name
  exe,bridge=c['game_exe'],c['bridge_exe']
  defaults={
   'A3D_MASTER_GAIN':'5.0','A3D_HRTF_TAPS':'48',
   'A3D_RENDER_SNAPSHOT':str(c['render_snapshot']),
   'A3D_WAVEOUT_QUEUE_HEADERS':str(c['queue_headers']),
   'A3D_WAVEOUT_SUBBLOCKS':str(c['subblocks']),
   'A3D_WAVEOUT_PRIORITY':str(c['thread_priority']),
   'A3D_WAVEOUT_ADAPTIVE':'0','A3D_LOG':'0','A3D_LATENCY_TRACE':'0',
  }
  if name=='QuakeIII-117':defaults.update({'A3D_GEOMETRY_RETRACE_BLOCKS':'4','A3D_REVERB_WET':'0.14'})
  extra=' '.join(c['extra_args'])
  cmd=['@echo off','setlocal','cd /d "%~dp0"',
       'rem Generated from config/game_profiles_v069.json - shared engine, 3 profiles.',
       f'if not exist "{exe}" (echo ERROR: Original {exe} missing. & exit /b 2)',
       f'if not exist "{exe}.manifest" (echo ERROR: Activation manifest missing. & exit /b 3)',
       'if not exist "a3dapi.dll" (echo ERROR: Shared A3D backend missing. & exit /b 3)',
       f'if not exist "{bridge}" (echo ERROR: A3D game activation bridge missing. & exit /b 3)']
  for req in c['required']:cmd.append('if not exist "'+req.replace('/','\\')+'" (echo ERROR: Required original '+req.replace('/','\\')+' missing. & exit /b 4)')
  cmd += [f'if not defined {k} set "{k}={v}"' for k,v in defaults.items()]
  cmd += [f'if not defined A3D_PROBE_LOG set "A3D_PROBE_LOG=%~dp0a3d-v069-{name.lower()}-windows.log"',
           f'echo A3D v0.6.9: {name} shared core, {c["queue_headers"]}x{256*c["subblocks"]}-frame queue, logging opt-in.',
           f'"{bridge}" {extra} %*','exit /b %errorlevel%']
  write(d/'RUN_A3D_WINDOWS.cmd','\n'.join(cmd)+'\n')
  # Quake III 6x256 is the validated default. Retain 3x512 as an explicit fallback.
  if name=='QuakeIII-117':
   fallbackcmd=['@echo off','setlocal','rem Legacy Quake III 3x512 (32ms) profile; user reported severe stutter on their machine.',
      'set "A3D_WAVEOUT_SUBBLOCKS=2"','set "A3D_WAVEOUT_QUEUE_HEADERS=3"',
      'set "A3D_WAVEOUT_ADAPTIVE=0"','call "%~dp0RUN_A3D_WINDOWS.cmd" %*','exit /b %errorlevel%']
   write(d/'RUN_A3D_3x512_FALLBACK_WINDOWS.cmd','\n'.join(fallbackcmd)+'\n')
   # Compatibility with the previous test launcher name: same as the new default.
   write(d/'RUN_A3D_32MS_TEST_WINDOWS.cmd',
         '@echo off\nrem Compatibility alias: 6x256 is now the Quake III default.\nset "A3D_WAVEOUT_SUBBLOCKS=1"\nset "A3D_WAVEOUT_QUEUE_HEADERS=6"\ncall "%~dp0RUN_A3D_WINDOWS.cmd" %*\nexit /b %errorlevel%\n')
  # Diagnostic deliberately opts in, with 1MiB log budget in DLL.
  diagcmd=['@echo off','setlocal','set "A3D_LOG=1"','set "A3D_LATENCY_TRACE=1"',
    'call "%~dp0RUN_A3D_WINDOWS.cmd" %*','exit /b %errorlevel%']
  write(d/'RUN_A3D_DIAGNOSTIC_WINDOWS.cmd','\n'.join(diagcmd)+'\n')
  if name=='Alice2011-VorpalFix':
   # Default is 6x256; let VorpalFix manage FPS unless 144 FPS was explicitly selected.
   write(d/'RUN_A3D_144FPS_WINDOWS.cmd',
         '@echo off\nrem Explicit FPS override. Normal launch respects VorpalFix settings.\ncall "%~dp0RUN_A3D_WINDOWS.cmd" +set com_maxfps 144 %*\nexit /b %errorlevel%\n')
   write(d/'RUN_A3D_4x512_FALLBACK_WINDOWS.cmd',
         '@echo off\nrem Prior proven 4x512 Alice 2011 WaveOut queue; FPS settings left to VorpalFix.\nset "A3D_WAVEOUT_SUBBLOCKS=2"\nset "A3D_WAVEOUT_QUEUE_HEADERS=4"\nset "A3D_WAVEOUT_ADAPTIVE=0"\ncall "%~dp0RUN_A3D_WINDOWS.cmd" %*\nexit /b %errorlevel%\n')
  if name=='Alice2000':
   write(d/'RUN_A3D_6x256_WINDOWS.cmd',
         '@echo off\nrem Validated Alice 2000 6x256 queue; this is the production default.\ncall "%~dp0RUN_A3D_WINDOWS.cmd" %*\nexit /b %errorlevel%\n')
  wine=['#!/usr/bin/env bash','set -euo pipefail','cd -- "$(dirname -- "$(realpath -- "$0")")"',
        '# Generated from config/game_profiles_v069.json; works with Debian 13 amd64 + Wine i386.',
        f'if [[ ! -f {exe} ]]; then',
        ' echo "ERROR: Original '+exe+' absent. On a case-sensitive Linux filesystem check the filename." >&2',
        (' [[ -f Alice.exe ]] && echo "For an original Alice.exe: ln -s Alice.exe alice.exe (do not rename/overwrite original)." >&2' if exe=='alice.exe' else ' true'),
        ' exit 2','fi',
        f'[[ -f {exe}.manifest ]] || {{ echo "Missing activation manifest: {exe}.manifest" >&2; exit 3; }}',
        '[[ -f a3dapi.dll && -f a3d.dll ]] || { echo "Missing shared A3D DLLs" >&2; exit 3; }',
        f'[[ -f {bridge} ]] || {{ echo "Missing activation bridge: {bridge}" >&2; exit 3; }}']
  for req in c['required']:wine += [f'[[ -f "{req}" ]] || {{ echo "Missing original game component: {req}" >&2; exit 4; }}']
  wine += ['command -v "${A3D_WINE_EXECUTABLE:-wine}" >/dev/null || { echo "Wine not found; install Debian 13 Wine with i386 support (see DEBIAN13_WINE.md)." >&2; exit 5; }']
  for k,v in defaults.items():wine.append(f'export {k}="${{{k}:-{v}}}"')
  wine += [f'export A3D_PROBE_LOG="${{A3D_PROBE_LOG:-$(pwd)/a3d-v069-{name.lower()}-wine.log}}"',
    '# Preserve caller Wine overrides while selecting our native 32-bit DLLs.',
    'export WINEDLLOVERRIDES="a3dapi=n,b;a3d=n,b${WINEDLLOVERRIDES:+;$WINEDLLOVERRIDES}"']
  if name=='Alice2011-VorpalFix':wine += ['# VorpalFix requires its own winmm.dll; keep it native.','export WINEDLLOVERRIDES="winmm=n,b;$WINEDLLOVERRIDES"']
  wine += [f'echo "A3D v0.6.9 / {name} / Wine: {c["queue_headers"]} x {256*c["subblocks"]} frames, HRTF 48 taps, gain $A3D_MASTER_GAIN" >&2',
    '# Honour the user’s existing WINEPREFIX, including their working installed games.',
    f'exec "${{A3D_WINE_EXECUTABLE:-wine}}" "./{bridge}" {extra} "$@"']
  write(d/'RUN_A3D_WINE.sh','\n'.join(wine)+'\n',exe=True)
  diagsh=['#!/usr/bin/env bash','set -euo pipefail','export A3D_LOG=1','export A3D_LATENCY_TRACE=1',
    'exec bash "$(dirname -- "$0")/RUN_A3D_WINE.sh" "$@"']
  write(d/'RUN_A3D_DIAGNOSTIC_WINE.sh','\n'.join(diagsh)+'\n',exe=True)
  if name=='Alice2011-VorpalFix':
   write(d/'RUN_A3D_144FPS_WINE.sh',
         '#!/usr/bin/env bash\nset -euo pipefail\n# Explicit 144 FPS override; normal Wine launcher has none.\nexec bash "$(dirname -- "$0")/RUN_A3D_WINE.sh" +set com_maxfps 144 "$@"\n',exe=True)
   write(d/'RUN_A3D_4x512_FALLBACK_WINE.sh',
         '#!/usr/bin/env bash\nset -euo pipefail\nexport A3D_WAVEOUT_SUBBLOCKS=2\nexport A3D_WAVEOUT_QUEUE_HEADERS=4\nexport A3D_WAVEOUT_ADAPTIVE=0\nexec bash "$(dirname -- "$0")/RUN_A3D_WINE.sh" "$@"\n',exe=True)
  if name=='Alice2000':
   write(d/'RUN_A3D_6x256_WINE.sh','#!/usr/bin/env bash\nset -euo pipefail\nexec bash "$(dirname -- "$0")/RUN_A3D_WINE.sh" "$@"\n',exe=True)
  elif name=='QuakeIII-117':
   write(d/'RUN_A3D_3x512_FALLBACK_WINE.sh','#!/usr/bin/env bash\nset -euo pipefail\n# Previous Quake III profile; 3x512 = 32ms.\nexport A3D_WAVEOUT_SUBBLOCKS=2\nexport A3D_WAVEOUT_QUEUE_HEADERS=3\nexport A3D_WAVEOUT_ADAPTIVE=0\nexec bash "$(dirname -- "$0")/RUN_A3D_WINE.sh" "$@"\n',exe=True)
   write(d/'RUN_A3D_32MS_TEST_WINE.sh','#!/usr/bin/env bash\nset -euo pipefail\n# Compatibility alias: 6x256 is now the default.\nexport A3D_WAVEOUT_SUBBLOCKS=1\nexport A3D_WAVEOUT_QUEUE_HEADERS=6\nexec bash "$(dirname -- "$0")/RUN_A3D_WINE.sh" "$@"\n',exe=True)
  # Per-game small text file generated from same source of truth.
  write(d/'PROFILE_v069.txt',f'{name}\n{c["notes"]}\nRelease candidate v0.6.9: the three games use 6x256 (32ms) by default; individual renderers and fallbacks remain available.\n')

if __name__=='__main__':
 generate()
 print('Generated:',', '.join(P))
