#!/usr/bin/env python3
"""Build explicit x86 per-user COM registration helper (freestanding Win32)."""
from pathlib import Path
import subprocess,shutil
ROOT=Path(__file__).resolve().parents[1]
WIN=ROOT/'win32';BUILD=WIN/'build';BUILD.mkdir(exist_ok=True)
CC=shutil.which('clang');LLD=shutil.which('lld-link')
if not CC or not LLD:raise SystemExit('clang and lld-link required')
def run(x):subprocess.run(x,cwd=WIN,check=True)
# Import libs are generated from explicit allow-listed APIs.
for lib,names in {'kernel32':['GetModuleFileNameA','GetCommandLineA','GetFileAttributesA','GetStdHandle','WriteFile','ExitProcess'],
                  'advapi32':['RegOpenKeyExA','RegCreateKeyExA','RegQueryValueExA','RegSetValueExA','RegDeleteValueA','RegEnumValueA','RegDeleteKeyA','RegCloseKey']}.items():
    defn=BUILD/(lib+'-v073.def');defn.write_text('LIBRARY '+lib.upper()+'.dll\nEXPORTS\n'+''.join(' '+x+'\n' for x in names))
    run([LLD,'/dll','/noentry','/machine:x86','/def:'+str(defn),'/out:build/'+lib+'-v073-stub.dll','/implib:build/'+lib+'-v073.lib','/timestamp:0'])
run([CC,'-target','i686-pc-windows-msvc','-ffreestanding','-fno-stack-protector','-fno-builtin','-mno-stack-arg-probe','-O2','-Wall','-Wextra','-Werror','-c','a3d_user_com.c','-o','build/a3d-com-user.obj'])
exports={'GetModuleFileNameA':12,'GetCommandLineA':0,'GetFileAttributesA':4,'GetStdHandle':4,'WriteFile':20,'ExitProcess':4,
         'RegOpenKeyExA':20,'RegCreateKeyExA':36,'RegQueryValueExA':24,'RegSetValueExA':24,'RegDeleteValueA':8,'RegEnumValueA':32,'RegDeleteKeyA':8,'RegCloseKey':4}
cmd=[LLD,'/subsystem:console','/machine:x86','/nodefaultlib','/entry:start@0','/timestamp:0','/out:build/a3d-com-user.exe','build/a3d-com-user.obj','build/kernel32-v073.lib','build/advapi32-v073.lib']
cmd += ['/alternatename:__imp__'+name+'@'+str(n)+'=__imp__'+name for name,n in exports.items()]
run(cmd)
print('Built',BUILD/'a3d-com-user.exe')
