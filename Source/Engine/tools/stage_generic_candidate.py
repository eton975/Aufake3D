#!/usr/bin/env python3
"""Create a candidate overlay in a NEW separate directory; never edit a game.

The overlay contains only this project's files and an install conflict report.
It does not copy the game, choose its audio backend, patch instructions, or
promise A3D1/A3D3 support. Manually back up conflicting files before installation.
"""
import argparse,hashlib,json,re,shutil
from pathlib import Path
from inspect_game_v070 import find_file,inspect_file
from scan_a3d_clients import scan
R=Path(__file__).resolve().parents[1]
def stage(directory,exe,out):
    directory=Path(directory).resolve();out=Path(out).resolve()
    if exe.casefold() in ('a3d-launch.exe','a3d-direct.exe','a3d-abi-survey.exe') or not re.fullmatch(r'[A-Za-z0-9_(). -]+\.exe',exe,re.IGNORECASE) or '..' in exe:
        raise ValueError('Use an ASCII .exe basename; paths and shell metacharacters are not accepted')
    if out==directory or out.is_relative_to(directory) or directory.is_relative_to(out):
        raise ValueError('Staging directory must be separate from the game directory')
    game=find_file(directory,exe)
    if not game or not inspect_file(game)['pe32_x86']:raise ValueError('Target must be an existing x86 PE32 executable')
    exe=game.name
    if (R/'experimental/build/a3d-launch.exe').is_file():
        payload={'a3d-launch.exe':R/'experimental/build/a3d-launch.exe',
                 'a3d-direct.exe':R/'experimental/build/a3d-direct.exe',
                 'a3dapi.dll':R/'win32/build/a3dapi.dll','a3d.dll':R/'win32/build/a3d.dll'}
    else:
        payload={name:R/'Generic-A3D2'/name for name in ('a3d-launch.exe','a3d-direct.exe','a3dapi.dll','a3d.dll')}
    survey=(R/'win32/build/a3d-abi-survey.exe')
    if not survey.exists():survey=R/'Generic-A3D2/a3d-abi-survey.exe'
    if survey.exists():payload['a3d-abi-survey.exe']=survey
    for p in payload.values():
        if not p.is_file():raise ValueError('Build the alpha first: missing '+p.name)
    if out.exists():raise ValueError('Staging directory already exists; choose a new directory')
    out.mkdir(parents=True)
    for name,p in payload.items():shutil.copy2(p,out/name)
    manifest=exe+'.manifest'
    (out/manifest).write_text('''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
<assemblyIdentity type="win32" name="Unofficial.A3D.GenericCandidate" version="0.7.1.0" processorArchitecture="x86" />
<file name="a3dapi.dll"><comClass clsid="{92FA2C24-253C-11D2-90FB-006008A1F441}" threadingModel="Both" /></file>
</assembly>
''',encoding='utf-8')
    # Survey has its own manifest because reg-free COM activation is tied to
    # the executable basename, rather than the target game's manifest.
    if 'a3d-abi-survey.exe' in payload:
        (out/'a3d-abi-survey.exe.manifest').write_text((out/manifest).read_text(encoding='utf-8'),encoding='utf-8')
    settings={'A3D_LOG':'0','A3D_LATENCY_TRACE':'0','A3D_WEAPON_CLARITY':'0','A3D_MASTER_GAIN':'5.0','A3D_HRTF_TAPS':'48','A3D_WAVEOUT_QUEUE_HEADERS':'6','A3D_WAVEOUT_SUBBLOCKS':'1','A3D_WAVEOUT_ADAPTIVE':'0'}
    cmd=['@echo off','setlocal','cd /d "%~dp0"']
    sh=['#!/usr/bin/env bash','set -euo pipefail','cd -- "$(dirname -- "$(realpath -- "$0")")"']
    for name,value in settings.items():
        cmd.append(f'if not defined {name} set "{name}={value}"');sh.append('export '+name+'="${'+name+':-'+value+'}"')
    cmd += ['if not defined A3D_PROBE_LOG set "A3D_PROBE_LOG=%~dp0a3d-generic-alpha.log"',
            'echo Unverified generic A3D2 candidate. Select the game audio backend separately.',
            'echo Direct mode: no suspended-process bootstrap or memory modification.',
            '"a3d-direct.exe" --game "'+exe+'" -- %*','exit /b %errorlevel%']
    sh += ['export A3D_PROBE_LOG="${A3D_PROBE_LOG:-$PWD/a3d-generic-alpha.log}"',
           'export WINEDLLOVERRIDES="a3dapi=n,b;a3d=n,b${WINEDLLOVERRIDES:+;$WINEDLLOVERRIDES}"',
           'echo "Unverified generic A3D2 candidate; select the game audio backend separately." >&2',
           'exec "${A3D_WINE_EXECUTABLE:-wine}" ./a3d-direct.exe --game "'+exe+'" -- "$@"']
    (out/'RUN_A3D_WINDOWS.cmd').write_bytes(('\r\n'.join(cmd)+'\r\n').encode())
    (out/'RUN_A3D_WINE.sh').write_text('\n'.join(sh)+'\n',encoding='utf-8',newline='\n')
    # The bootstrap path is a separate, explicit opt-in. It uses suspended-child
    # activation with memory writes. This is not advised on anti-cheat servers.
    bridge_cmd=[line.replace('a3d-direct.exe','a3d-launch.exe').replace('Direct mode: no suspended-process bootstrap or memory modification.',
              'Bridge mode modifies the child process in RAM. Offline or authorised testing only.') for line in cmd]
    bridge_sh=[line.replace('a3d-direct.exe','a3d-launch.exe') for line in sh]
    (out/'RUN_A3D_BRIDGE_WINDOWS.cmd').write_bytes(('\r\n'.join(bridge_cmd)+'\r\n').encode())
    (out/'RUN_A3D_BRIDGE_WINE.sh').write_text('\n'.join(bridge_sh)+'\n',encoding='utf-8',newline='\n')

    # Non-injecting experiment: the game is started directly. This may work
    # with a supported external application manifest or with legacy a3d.dll
    # imports. COM activation is NOT guaranteed, nor anti-cheat approval.
    direct_cmd=cmd[:-3]+['echo Direct-launch experiment: no A3D process bootstrap; A3D2 COM may not activate.',
                       '"'+exe+'" %*','exit /b %errorlevel%']
    (out/'RUN_A3D_DIRECT_WINDOWS.cmd').write_bytes(('\r\n'.join(direct_cmd)+'\r\n').encode())
    direct_sh=sh[:-3]+['echo "Direct-launch experiment: COM activation not guaranteed." >&2',
                       'exec "${A3D_WINE_EXECUTABLE:-wine}" ./"'+exe+'" "$@"']
    (out/'RUN_A3D_DIRECT_WINE.sh').write_text('\n'.join(direct_sh)+'\n',encoding='utf-8')
    if 'a3d-abi-survey.exe' in payload:
        (out/'RUN_A3D_ABI_SURVEY_WINDOWS.cmd').write_bytes(b'@echo off\r\ncd /d "%~dp0"\r\n"a3d-launch.exe" --game "a3d-abi-survey.exe" --\r\nexit /b %errorlevel%\r\n')
        (out/'RUN_A3D_ABI_SURVEY_WINE.sh').write_text('#!/usr/bin/env bash\nset -euo pipefail\ncd -- "$(dirname -- "$0")"\nexport WINEDLLOVERRIDES="a3dapi=n,b;a3d=n,b${WINEDLLOVERRIDES:+;$WINEDLLOVERRIDES}"\nexec "${A3D_WINE_EXECUTABLE:-wine}" ./a3d-launch.exe --game "a3d-abi-survey.exe" --\n',encoding='utf-8')
    (out/'RUN_A3D_DIAGNOSTIC_WINDOWS.cmd').write_bytes(b'@echo off\r\nsetlocal\r\nset "A3D_LOG=1"\r\ncall "%~dp0RUN_A3D_WINDOWS.cmd" %*\r\nexit /b %errorlevel%\r\n')
    (out/'RUN_A3D_DIAGNOSTIC_WINE.sh').write_text('#!/usr/bin/env bash\nset -euo pipefail\nexport A3D_LOG=1\nexec bash "$(dirname -- "$0")/RUN_A3D_WINE.sh" "$@"\n',encoding='utf-8')
    conflicts=[]
    for name in list(payload)+[manifest]+(['a3d-abi-survey.exe.manifest'] if 'a3d-abi-survey.exe' in payload else []):
        original=find_file(directory,name)
        if original:conflicts.append({'file':original.name,'sha256':hashlib.sha256(original.read_bytes()).hexdigest()})
    report={'version':'0.7.1-generic-dev','game':inspect_file(game),'static_a3d_scan':scan(directory,depth=1)['summary'],
            'default_launcher':'a3d-direct.exe (ordinary process start; external COM manifest required)',
            'opt_in_bridge_launcher':'a3d-launch.exe (in-memory bootstrap; offline/authorized use only)' ,'game_directory_modified':False,
            'compatibility':'unverified; generic COM activation only','conflicts_back_up_before_manual_copy':conflicts,
            'warning':'Legacy A3D1 still uses DirectSound fallback; A3D3 interfaces remain unimplemented. The direct launcher is not anti-cheat certified. Do not infer support from activation.'}
    (out/'INSTALL_PLAN.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    (out/'README_CANDIDATE.txt').write_text(
        'UNVERIFIED A3D game candidate. Read INSTALL_PLAN.json first.\n'
        'Back up any conflicting files before manually placing this overlay beside the original game executable.\n'
        'Try RUN_A3D_ABI_SURVEY_* to inspect exposed interfaces without launching the game.\n'
        'Normal RUN_A3D_* uses the low-invasive a3d-direct.exe launcher.\n'
        'RUN_A3D_DIRECT_* bypasses even the direct launcher and runs the game EXE itself.\n'
        'RUN_A3D_BRIDGE_* uses a suspended-process COM activation bootstrap.\n'
        'Either direct path may fail A3D2 COM activation if external manifests are ignored.\n'
        'DO NOT use on anti-cheat-protected multiplayer servers without explicit permission.\n'
        'You must enable the game A3D backend separately. A3D1 HRTF and A3D3 extensions are NOT implemented.\n',encoding='utf-8')
    return report
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path);p.add_argument('--exe',required=True);p.add_argument('--out',required=True,type=Path);a=p.parse_args()
    try:report=stage(a.directory,a.exe,a.out)
    except (OSError,ValueError) as e:p.exit(2,str(e)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
