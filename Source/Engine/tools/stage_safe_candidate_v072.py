#!/usr/bin/env python3
"""Stage an A3D candidate without adding any memory-modifying launcher.

No game files, registry keys, processes or protected server processes are
changed. Creates an independent overlay only; user must review and install
manually, and obtain multiplayer-server permission before use.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

from inspect_game_v070 import find_file, inspect_file
from scan_a3d_clients import scan
from security_audit_v072 import audit_runtime

ROOT=Path(__file__).resolve().parents[1]
FILES=('a3dapi.dll','a3d.dll','a3d-direct.exe','a3d-abi-survey.exe')


def runtime_directory() -> Path:
    for p in (ROOT/'Runtime',ROOT/'runtime-v072'):
        if all((p/f).is_file() for f in FILES):return p
    raise ValueError('Missing standard runtime files; use the v0.7.2 Runtime kit.')


def stage(directory: Path, exe: str, out: Path) -> dict:
    directory=directory.resolve();out=out.resolve()
    # Only allow an adjacent .exe basename, with no command-shell metacharacters.
    if not re.fullmatch(r'[\w(). -]+\.exe',exe,re.IGNORECASE|re.ASCII) or '..' in exe or exe.casefold() in ('a3d-direct.exe','a3d-abi-survey.exe','a3d-launch.exe'):
        raise ValueError('Specify a simple ASCII .exe basename, not a path')
    if directory==out or directory in out.parents or out in directory.parents:
        raise ValueError('Overlay must be completely separate from game directory')
    game=find_file(directory,exe)
    if not game or not inspect_file(game)['pe32_x86']:
        raise ValueError('Target must be an existing PE32/x86 game executable')
    exe=game.name
    runtime=runtime_directory()
    payload={name:(runtime/name).read_bytes() for name in FILES}
    audit=audit_runtime(payload)
    if not audit['passed']:raise ValueError('Unsafe standard runtime: '+str(audit['issues']))
    if out.exists():raise ValueError('Overlay already exists; choose an empty destination')
    out.mkdir(parents=True)
    for name,b in payload.items():(out/name).write_bytes(b)

    def manifest(identity: str) -> bytes:
        return (f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity type="win32" name="{identity}" version="0.7.2.0" processorArchitecture="x86" />
  <file name="a3dapi.dll"><comClass clsid="{{92FA2C24-253C-11D2-90FB-006008A1F441}}" threadingModel="Both" /></file>
</assembly>
''').encode('utf-8')
    (out/(exe+'.manifest')).write_bytes(manifest('Unofficial.A3D.GenericCandidate'))
    (out/'a3d-abi-survey.exe.manifest').write_bytes(manifest('Unofficial.A3D.Survey'))

    env={'A3D_LOG':'0','A3D_LATENCY_TRACE':'0','A3D_WEAPON_CLARITY':'0',
         'A3D_MASTER_GAIN':'5.0','A3D_HRTF_TAPS':'48',
         'A3D_WAVEOUT_QUEUE_HEADERS':'6','A3D_WAVEOUT_SUBBLOCKS':'1',
         'A3D_WAVEOUT_ADAPTIVE':'0'}
    cmd=['@echo off','setlocal','cd /d "%~dp0"']
    sh=['#!/usr/bin/env bash','set -euo pipefail','cd -- "$(dirname -- "$(realpath -- "$0")")"']
    for k,v in env.items():
        cmd.append(f'if not defined {k} set "{k}={v}"')
        sh.append('export '+k+'="${'+k+':-'+v+'}"')
    sh.extend(['export WINEDLLOVERRIDES="a3dapi=n,b;a3d=n,b${WINEDLLOVERRIDES:+;$WINEDLLOVERRIDES}"'])
    # A conventional process start; no suspended child, memory modification,
    # injection, anti-cheat circumvention or system-wide registry changes.
    (out/'RUN_A3D_WINDOWS.cmd').write_bytes(('\r\n'.join(cmd+[
        'echo Unverified generic A3D audio. Do not use on multiplayer servers without permission.',
        f'"a3d-direct.exe" --game "{exe}" -- %*', 'exit /b %errorlevel%'])+'\r\n').encode())
    (out/'RUN_A3D_WINE.sh').write_text('\n'.join(sh+[
        'echo "Unverified generic A3D audio; multiplayer-server permission required." >&2',
        f'exec "${{A3D_WINE_EXECUTABLE:-wine}}" ./a3d-direct.exe --game "{exe}" -- "$@"'])+'\n',encoding='utf-8')
    (out/'RUN_A3D_ABI_SURVEY_WINDOWS.cmd').write_bytes(b'@echo off\r\ncd /d "%~dp0"\r\n"a3d-abi-survey.exe"\r\nexit /b %errorlevel%\r\n')
    (out/'RUN_A3D_ABI_SURVEY_WINE.sh').write_text('\n'.join(sh[:3]+[sh[-1],
        'exec "${A3D_WINE_EXECUTABLE:-wine}" ./a3d-abi-survey.exe'])+'\n',encoding='utf-8')
    (out/'RUN_A3D_DIAGNOSTIC_WINDOWS.cmd').write_bytes(b'@echo off\r\nsetlocal\r\nset "A3D_LOG=1"\r\ncall "%~dp0RUN_A3D_WINDOWS.cmd" %*\r\nexit /b %errorlevel%\r\n')
    (out/'RUN_A3D_DIAGNOSTIC_WINE.sh').write_text('#!/usr/bin/env bash\nset -euo pipefail\nexport A3D_LOG=1\nexec bash "$(dirname -- "$0")/RUN_A3D_WINE.sh" "$@"\n',encoding='utf-8')
    for script in out.glob('*.sh'):script.chmod(0o755)
    other_files=list(FILES)+[exe+'.manifest','a3d-abi-survey.exe.manifest']
    conflicts=[]
    for f in other_files:
        match=find_file(directory,f)
        if match:conflicts.append({'file':match.name,'sha256':hashlib.sha256(match.read_bytes()).hexdigest()})
    plan={'version':'0.7.2-security-dev','game':inspect_file(game),
          'static_a3d_evidence':scan(directory,depth=1)['summary'],
          'game_directory_modified':False,
          'no_process_memory_modification_in_bundled_runtime_imports':audit['passed'],
          'server_or_anticheat_approved':False,'multiplayer_use':'Only after explicit server/anti-cheat permission',
          'known_limitation':'An external game.exe.manifest can be ignored if the game has an embedded manifest. A3D2 COM activation and game audio are not verified. No full A3D1/A3D3 spatial support.',
          'manual_install_conflicts':conflicts,
          'source_runtime_sha256':{k:hashlib.sha256(b).hexdigest() for k,b in payload.items()}}
    (out/'INSTALL_PLAN.json').write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
    (out/'README_CANDIDATE.txt').write_text('v0.7.2 transparent A3D runtime CANDIDATE, not a verified game patch.\n'
        'No files were changed in your original game directory.\n'
        'Read INSTALL_PLAN.json and back up conflicting files before manual installation.\n'
        'No injected bridge is bundled. This does NOT guarantee COM activation, anti-cheat acceptance, or an antivirus false-positive-free result.\n'
        'Do not use on protected multiplayer servers without explicit approval.\n'
        'For external-manifest limitations and official false-positive review, read SECURITY_AND_SETUP_V072.md in the kit.\n',encoding='utf-8')
    return plan


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('directory',type=Path)
    ap.add_argument('--exe',required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    try:result=stage(args.directory,args.exe,args.out)
    except (ValueError,OSError) as e:ap.exit(2,str(e)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
