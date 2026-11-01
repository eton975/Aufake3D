#!/usr/bin/env python3
"""Stage candidate launchers; no game installation or game config writes."""
from pathlib import Path
import json,shutil
R=Path(__file__).resolve().parents[1]
D=R/'deploy-v070-alpha'
PROFILES=json.loads((R/'config/game_profiles_v070_alpha.json').read_text())['profiles']
DEFAULTS={'A3D_MASTER_GAIN':'5.0','A3D_HRTF_TAPS':'48','A3D_WEAPON_CLARITY':'0',
          'A3D_RENDER_SNAPSHOT':'1','A3D_WAVEOUT_QUEUE_HEADERS':'6','A3D_WAVEOUT_SUBBLOCKS':'1',
          'A3D_WAVEOUT_ADAPTIVE':'0','A3D_WAVEOUT_PRIORITY':'0','A3D_LOG':'0','A3D_LATENCY_TRACE':'0'}
MANIFEST='''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity type="win32" name="Unofficial.A3D.Alpha.{name}" version="0.7.0.0" processorArchitecture="x86" />
  <file name="a3dapi.dll"><comClass clsid="{{92FA2C24-253C-11D2-90FB-006008A1F441}}" threadingModel="Both" /></file>
</assembly>
'''
def write(path,text):path.write_text(text,encoding='utf-8',newline='')
def main():
    D.mkdir(exist_ok=True)
    # Established profiles retain all prior policy; use the new engine binary.
    for name in ('Alice2000','Alice2011-VorpalFix','QuakeIII-117'):
        shutil.copytree(R/'deploy-v0612'/name,D/name,dirs_exist_ok=True)
        for script in (D/name).iterdir():
            if script.suffix in ('.cmd','.sh'):
                text=script.read_text(encoding='utf-8').replace('v0.6.12','v0.7.0-alpha').replace('a3d-v0612-','a3d-v070-alpha-')
                write(script,text.replace('\n','\r\n') if script.suffix=='.cmd' else text)
    for name,p in PROFILES.items():
        folder=D/name;folder.mkdir(exist_ok=True)
        write(folder/(p['game_exe']+'.manifest'),MANIFEST.format(name=name))
        checks=p['required']+['a3dapi.dll','a3d.dll',p['game_exe']+'.manifest',p['launcher']]
        cmd=['@echo off','setlocal','cd /d "%~dp0"']
        sh=['#!/usr/bin/env bash','set -euo pipefail','cd -- "$(dirname -- "$(realpath -- "$0")")"']
        for required in checks:
            cmd.append('if not exist "'+required+'" (echo ERROR: Missing '+required+' & exit /b 2)')
            sh.append('[[ -f "'+required+'" ]] || { echo "Missing '+required+' (case-sensitive filename)" >&2; exit 2; }')
        for variable,value in DEFAULTS.items():
            cmd.append(f'if not defined {variable} set "{variable}={value}"')
            sh.append('export '+variable+'="${'+variable+':-'+value+'}"')
        cmd.append('if not defined A3D_PROBE_LOG set "A3D_PROBE_LOG=%~dp0a3d-v070-alpha.log"')
        sh += ['export A3D_PROBE_LOG="${A3D_PROBE_LOG:-$PWD/a3d-v070-alpha.log}"',
               'command -v "${A3D_WINE_EXECUTABLE:-wine}" >/dev/null || { echo "Wine not found" >&2; exit 5; }',
               'export WINEDLLOVERRIDES="a3dapi=n,b;a3d=n,b${WINEDLLOVERRIDES:+;$WINEDLLOVERRIDES}"']
        warning='A3D v0.7.0-alpha / '+name+': unverified compatibility candidate.'
        cmd.append('echo '+warning)
        sh.append('echo "'+warning+'" >&2')
        cmd += ['"'+p['launcher']+'" '+' '.join(p['args'])+' %*','exit /b %errorlevel%']
        sh.append('exec "${A3D_WINE_EXECUTABLE:-wine}" "./'+p['launcher']+'" '+' '.join(p['args'])+' "$@"')
        write(folder/'RUN_A3D_WINDOWS.cmd','\r\n'.join(cmd)+'\r\n')
        write(folder/'RUN_A3D_WINE.sh','\n'.join(sh)+'\n')
        write(folder/'RUN_A3D_DIAGNOSTIC_WINDOWS.cmd','@echo off\r\nsetlocal\r\nset "A3D_LOG=1"\r\ncall "%~dp0RUN_A3D_WINDOWS.cmd" %*\r\nexit /b %errorlevel%\r\n')
        write(folder/'RUN_A3D_DIAGNOSTIC_WINE.sh','#!/usr/bin/env bash\nset -euo pipefail\nexport A3D_LOG=1\nexec bash "$(dirname -- "$0")/RUN_A3D_WINE.sh" "$@"\n')
        if name=='HalfLife-Retail':
            write(folder/'RUN_A3D_SPLASH_FIX_WINDOWS.cmd','@echo off\r\nsetlocal\r\nset "A3D_HALFLIFE_SPLASH_FIX=1"\r\ncall "%~dp0RUN_A3D_WINDOWS.cmd" %*\r\nexit /b %errorlevel%\r\n')
            write(folder/'RUN_A3D_SPLASH_FIX_WINE.sh','#!/usr/bin/env bash\nset -euo pipefail\nexport A3D_HALFLIFE_SPLASH_FIX=1\nexec bash "$(dirname -- "$0")/RUN_A3D_WINE.sh" "$@"\n')
        shutil.copy2(R/'experimental/build'/p['launcher'],folder/p['launcher'])
    generic=D/'Generic-A3D2';generic.mkdir(exist_ok=True)
    shutil.copy2(R/'experimental/build/a3d-launch.exe',generic/'a3d-launch.exe')
    # Shared read-only ABI survey is useful before trying unknown client titles.
    survey=R/'win32/build/a3d-abi-survey.exe'
    if survey.is_file():shutil.copy2(survey,generic/'a3d-abi-survey.exe')
    shutil.copy2(D/'HalfLife-Retail/hl.exe.manifest',generic/'GAME.exe.manifest.template')
    write(generic/'README_GENERIC.txt','Generic A3D2 candidate. Use tools/stage_generic_candidate.py to prepare a separate overlay; see GENERIC_CANDIDATE_SETUP.md. Gameplay remains unverified.\n')
    for folder in (p for p in D.iterdir() if p.is_dir()):
        for name in ('a3dapi.dll','a3d.dll','a3d-selftest.exe','a3d-comtest.exe','a3d-quake3-lock-test.exe'):
            shutil.copy2(R/'win32/build'/name,folder/name)
        shutil.copy2(R/'deploy-v0612/Alice2000/a3d-comtest.exe.manifest',folder/'a3d-comtest.exe.manifest')
    print('Staged 5 title profiles plus Generic-A3D2; Half-Life/Unreal remain unverified candidates.')
if __name__=='__main__':main()
