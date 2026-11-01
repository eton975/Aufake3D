#!/usr/bin/env python3
"""Rebuild the two GENERIC x86 PE32 launchers with Clang/LLD (no CRT).

The direct launcher deliberately links no process-memory modification API.
Do not conflate an import-table check with behavioral security certification.
"""
from pathlib import Path
import shutil, subprocess
R=Path(__file__).resolve().parents[1]
E=R/'experimental'; B=E/'build';B.mkdir(exist_ok=True)
CC=shutil.which('clang');LINK=shutil.which('lld-link')
if not CC or not LINK:raise SystemExit('clang and lld-link required')
def run(args):subprocess.run(args,cwd=E,check=True)
run([LINK,'/dll','/noentry','/machine:x86','/def:kernel32.def','/out:build/kernel32-stub.dll','/implib:build/kernel32.lib','/timestamp:0'])
base=[CC,'-target','i686-pc-windows-msvc','-ffreestanding','-fno-stack-protector','-fno-builtin','-O2','-Wall','-Wextra','-Werror','-Wno-unused-function']
run(base+['-c','direct_launch.c','-o','build/a3d-direct.obj'])
run(base+['-DA3D_GENERIC=1','-DGAME_EXE="unused.exe"','-c','game_activation.c','-o','build/a3d-launch.obj'])
shared=['/subsystem:console','/machine:x86','/nodefaultlib','/entry:mainCRTStartup','/timestamp:0','build/kernel32.lib']
def alt(table):return ['/alternatename:__imp__'+fn+'@'+str(argc)+'=__imp__'+fn for fn,argc in table.items()]
common={'GetModuleFileNameA':12,'GetCommandLineA':0,'CreateProcessA':40,'WaitForSingleObject':8,'GetExitCodeProcess':8,'CloseHandle':4,'GetStdHandle':4,'WriteFile':20,'ExitProcess':4,'CreateFileA':28,'ReadFile':20,'SetFilePointer':16}
run([LINK,*shared,'/out:build/a3d-direct.exe','build/a3d-direct.obj',*alt(common)])
boost={'WriteProcessMemory':20,'VirtualAllocEx':20,'FlushInstructionCache':12,'ResumeThread':4,'TerminateProcess':8,'GetThreadContext':8,'SetThreadContext':8,'CreateActCtxA':4,'ActivateActCtx':8,'GetEnvironmentVariableA':12,'GetLastError':0,'ReadProcessMemory':20,'VirtualProtectEx':20}
run([LINK,*shared,'/out:build/a3d-launch.exe','build/a3d-launch.obj',*alt({**common,**boost})])
print('Built two generic x86 launchers')
