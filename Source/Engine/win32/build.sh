#!/usr/bin/env bash
# v0.5.0 SOURCE COMMENTARY — Freestanding Win32 cross-build script
# Builds PE32/i386 frontends and probes using Clang/lld-link, with manually declared
# Win32 imports. Import-library stubs are link-time constructs; they are not
# replacement operating-system libraries. Keep exported stdcall symbol names and
# architectures unchanged.
set -euo pipefail
cd "$(dirname "$0")"
: "${CC:=clang}"
: "${LINK:=lld-link}"
mkdir -p build
"$LINK" /dll /noentry /machine:x86 /def:kernel32.def /out:build/kernel32-stub.dll /implib:build/kernel32.lib >build/importlib.log 2>&1
"$CC" -target i686-pc-windows-msvc -ffreestanding -fno-stack-protector -fno-builtin -O2 -Wall -Wextra -c a3dapi.c -o build/a3dapi.obj
"$LINK" /dll /noentry /machine:x86 /nodefaultlib /out:build/a3dapi.dll /def:a3dapi.def build/a3dapi.obj build/kernel32.lib \
 /alternatename:__imp__CreateFileA@28=__imp__CreateFileA \
 /alternatename:__imp__WriteFile@20=__imp__WriteFile \
 /alternatename:__imp__CloseHandle@4=__imp__CloseHandle \
 /alternatename:__imp__GetTickCount@0=__imp__GetTickCount \
 /alternatename:__imp__GetFileAttributesA@4=__imp__GetFileAttributesA \
 /alternatename:__imp__DeleteFileA@4=__imp__DeleteFileA \
 /alternatename:__imp__GetEnvironmentVariableA@12=__imp__GetEnvironmentVariableA \
 /alternatename:__imp__InterlockedIncrement@4=__imp__InterlockedIncrement \
 /alternatename:__imp__InterlockedDecrement@4=__imp__InterlockedDecrement \
 /alternatename:__imp__GetProcessHeap@0=__imp__GetProcessHeap \
 /alternatename:__imp__HeapAlloc@12=__imp__HeapAlloc \
 /alternatename:__imp__HeapFree@12=__imp__HeapFree \
 /alternatename:__imp__InitializeCriticalSection@4=__imp__InitializeCriticalSection \
 /alternatename:__imp__EnterCriticalSection@4=__imp__EnterCriticalSection \
 /alternatename:__imp__LeaveCriticalSection@4=__imp__LeaveCriticalSection \
 /alternatename:__imp__InterlockedCompareExchange@12=__imp__InterlockedCompareExchange \
 /alternatename:__imp__InterlockedExchange@8=__imp__InterlockedExchange \
 /alternatename:__imp__CreateThread@24=__imp__CreateThread \
 /alternatename:__imp__SetEvent@4=__imp__SetEvent \
 /alternatename:__imp__CreateEventA@16=__imp__CreateEventA \
 /alternatename:__imp__SetThreadPriority@8=__imp__SetThreadPriority \
 /alternatename:__imp__WaitForSingleObject@8=__imp__WaitForSingleObject \
 /alternatename:__imp__Sleep@4=__imp__Sleep \
 /alternatename:__imp__LoadLibraryA@4=__imp__LoadLibraryA \
 /alternatename:__imp__GetProcAddress@8=__imp__GetProcAddress \
 /implib:build/a3dapi.lib
# The ABI self-test imports only Kernel32; its execution is for Wine/Windows.
"$CC" -target i686-pc-windows-msvc -ffreestanding -fno-stack-protector -fno-builtin -O2 -c selftest.c -o build/selftest.obj
"$LINK" /subsystem:console /machine:x86 /nodefaultlib /entry:start@0 /out:build/a3d-selftest.exe \
 build/selftest.obj build/kernel32.lib \
 /alternatename:__imp__LoadLibraryA@4=__imp__LoadLibraryA \
 /alternatename:__imp__GetProcAddress@8=__imp__GetProcAddress \
 /alternatename:__imp__FreeLibrary@4=__imp__FreeLibrary \
 /alternatename:__imp__ExitProcess@4=__imp__ExitProcess
# The OLE32 import library is only for linking to the REAL Wine/Windows OLE32.dll.
"$LINK" /dll /noentry /machine:x86 /def:ole32.def /out:build/ole32-stub.dll /implib:build/ole32.lib >build/ole32-importlib.log 2>&1
"$CC" -target i686-pc-windows-msvc -ffreestanding -fno-stack-protector -fno-builtin -O2 -Wall -Wextra -c com_test.c -o build/com_test.obj
"$LINK" /subsystem:console /machine:x86 /nodefaultlib /entry:start@0 /out:build/a3d-comtest.exe \
 build/com_test.obj build/ole32.lib build/kernel32.lib \
 /alternatename:__imp__CoInitialize@4=__imp__CoInitialize \
 /alternatename:__imp__CoUninitialize@0=__imp__CoUninitialize \
 /alternatename:__imp__CoCreateInstance@20=__imp__CoCreateInstance \
 /alternatename:__imp__ExitProcess@4=__imp__ExitProcess \
 /alternatename:__imp__GetStdHandle@4=__imp__GetStdHandle \
 /alternatename:__imp__WriteFile@20=__imp__WriteFile
# Native 32-bit Advapi32 registry utility. Runs solely inside the isolated Wine prefix.
"$LINK" /dll /noentry /machine:x86 /def:advapi32.def /out:build/advapi32-stub.dll /implib:build/advapi32.lib >build/advapi32-importlib.log 2>&1
"$CC" -target i686-pc-windows-msvc -ffreestanding -fno-stack-protector -fno-builtin -O2 -Wall -Wextra -c reg32.c -o build/reg32.obj
"$LINK" /subsystem:console /machine:x86 /nodefaultlib /entry:start@0 /out:build/a3d-register32.exe \
 build/reg32.obj build/kernel32.lib build/advapi32.lib \
 /alternatename:__imp__GetStdHandle@4=__imp__GetStdHandle \
 /alternatename:__imp__WriteFile@20=__imp__WriteFile \
 /alternatename:__imp__ExitProcess@4=__imp__ExitProcess \
 /alternatename:__imp__GetFileAttributesA@4=__imp__GetFileAttributesA \
 /alternatename:__imp__RegOpenKeyExA@20=__imp__RegOpenKeyExA \
 /alternatename:__imp__RegCreateKeyExA@36=__imp__RegCreateKeyExA \
 /alternatename:__imp__RegQueryValueExA@24=__imp__RegQueryValueExA \
 /alternatename:__imp__RegSetValueExA@24=__imp__RegSetValueExA \
 /alternatename:__imp__RegCloseKey@4=__imp__RegCloseKey

# Confirm PE/i386 architecture without invoking Wine.
python3 - <<'PYVERIFY'
import struct
for f in ('build/a3dapi.dll','build/a3d-selftest.exe','build/a3d-comtest.exe','build/a3d-register32.exe'):
 data=open(f,'rb').read()
 assert data[:2] == b'MZ'
 pe=struct.unpack_from('<I',data,0x3c)[0]
 assert data[pe:pe+4] == b'PE\x00\x00'
 assert struct.unpack_from('<H',data,pe+4)[0] == 0x14c, f
 print(f, 'PE32/i386 OK')
PYVERIFY
# Standalone diagnostic program: queries the user's original Miles installation.
"$CC" -target i686-pc-windows-msvc -ffreestanding -fno-stack-protector -fno-builtin -O2 -Wall -Wextra -c miles_enum.c -o build/miles_enum.obj
"$LINK" /subsystem:console /machine:x86 /nodefaultlib /entry:start@0 /out:build/a3d-miles-enum.exe \
 build/miles_enum.obj build/kernel32.lib \
 /alternatename:__imp__LoadLibraryA@4=__imp__LoadLibraryA \
 /alternatename:__imp__GetProcAddress@8=__imp__GetProcAddress \
 /alternatename:__imp__FreeLibrary@4=__imp__FreeLibrary \
 /alternatename:__imp__GetCurrentDirectoryA@8=__imp__GetCurrentDirectoryA \
 /alternatename:__imp__GetFileAttributesA@4=__imp__GetFileAttributesA \
 /alternatename:__imp__ExitProcess@4=__imp__ExitProcess \
 /alternatename:__imp__GetStdHandle@4=__imp__GetStdHandle \
 /alternatename:__imp__WriteFile@20=__imp__WriteFile

# Direct provider open diagnostic (Miles 6.x): Fast 2D vs Aureal A3D2.
# The code executes only on Wine/Windows against the owner's own Miles installation.
"$CC" -target i686-pc-windows-msvc -ffreestanding -fno-stack-protector -fno-builtin -O2 -Wall -Wextra -Werror -c miles_open.c -o build/miles_open.obj
"$LINK" /subsystem:console /machine:x86 /nodefaultlib /entry:start@0 /out:build/a3d-miles-open.exe \
 build/miles_open.obj build/kernel32.lib \
 /alternatename:__imp__LoadLibraryA@4=__imp__LoadLibraryA \
 /alternatename:__imp__GetProcAddress@8=__imp__GetProcAddress \
 /alternatename:__imp__FreeLibrary@4=__imp__FreeLibrary \
 /alternatename:__imp__GetCurrentDirectoryA@8=__imp__GetCurrentDirectoryA \
 /alternatename:__imp__GetFileAttributesA@4=__imp__GetFileAttributesA \
 /alternatename:__imp__GetEnvironmentVariableA@12=__imp__GetEnvironmentVariableA \
 /alternatename:__imp__ExitProcess@4=__imp__ExitProcess \
 /alternatename:__imp__GetStdHandle@4=__imp__GetStdHandle \
 /alternatename:__imp__WriteFile@20=__imp__WriteFile

# Standalone no-playback Miles position / synthetic WAV probing (A3D2 only).
"$CC" -target i686-pc-windows-msvc -ffreestanding -fno-stack-protector -fno-builtin -O2 -Wall -Wextra -Werror -c miles_wave.c -o build/miles_wave.obj
"$LINK" /subsystem:console /machine:x86 /nodefaultlib /entry:start@0 /out:build/a3d-miles-wave.exe \
 build/miles_wave.obj build/kernel32.lib \
 /alternatename:__imp__LoadLibraryA@4=__imp__LoadLibraryA \
 /alternatename:__imp__GetProcAddress@8=__imp__GetProcAddress \
 /alternatename:__imp__FreeLibrary@4=__imp__FreeLibrary \
 /alternatename:__imp__GetCurrentDirectoryA@8=__imp__GetCurrentDirectoryA \
 /alternatename:__imp__GetFileAttributesA@4=__imp__GetFileAttributesA \
 /alternatename:__imp__GetEnvironmentVariableA@12=__imp__GetEnvironmentVariableA \
 /alternatename:__imp__ExitProcess@4=__imp__ExitProcess \
 /alternatename:__imp__GetStdHandle@4=__imp__GetStdHandle \
 /alternatename:__imp__Sleep@4=__imp__Sleep \
 /alternatename:__imp__WriteFile@20=__imp__WriteFile

# Separate explicit user-triggered low-volume playback test, no game involved.
"$CC" -target i686-pc-windows-msvc -ffreestanding -fno-stack-protector -fno-builtin -O2 -Wall -Wextra -Werror -c playback_demo.c -o build/playback_demo.obj
"$LINK" /subsystem:console /machine:x86 /nodefaultlib /entry:start@0 /out:build/a3d-playback-demo.exe \
 build/playback_demo.obj build/ole32.lib build/kernel32.lib \
 /alternatename:__imp__CoInitialize@4=__imp__CoInitialize \
 /alternatename:__imp__CoUninitialize@0=__imp__CoUninitialize \
 /alternatename:__imp__CoCreateInstance@20=__imp__CoCreateInstance \
 /alternatename:__imp__ExitProcess@4=__imp__ExitProcess \
 /alternatename:__imp__GetStdHandle@4=__imp__GetStdHandle \
 /alternatename:__imp__WriteFile@20=__imp__WriteFile \
 /alternatename:__imp__Sleep@4=__imp__Sleep

# A3D legacy bridge: old Quake III versions may import _A3dCreate@12 from a3d.dll.
# This is a DirectSound compatibility bridge, NOT full A3D 2.0 Wavetracing.
"$CC" -target i686-pc-windows-msvc -ffreestanding -fno-stack-protector -fno-builtin -O2 -Wall -Wextra -Werror -c a3d_legacy_bridge.c -o build/a3d_legacy_bridge.obj
"$LINK" /dll /noentry /machine:x86 /nodefaultlib /out:build/a3d.dll /def:a3d_legacy_bridge.def \
 build/a3d_legacy_bridge.obj build/kernel32.lib \
 /alternatename:__imp__LoadLibraryA@4=__imp__LoadLibraryA \
 /alternatename:__imp__GetProcAddress@8=__imp__GetProcAddress \
 /alternatename:__imp__CreateFileA@28=__imp__CreateFileA \
 /alternatename:__imp__WriteFile@20=__imp__WriteFile \
 /alternatename:__imp__CloseHandle@4=__imp__CloseHandle \
 /alternatename:__imp__GetEnvironmentVariableA@12=__imp__GetEnvironmentVariableA

# v0.6.5: compile additional Quake III ABI probe required by contract tests.
"$CC" -target i686-pc-windows-msvc -ffreestanding -fno-stack-protector -fno-builtin -O2 -c quake3_lock_test.c -o build/quake3_lock_test.obj
"$LINK" /subsystem:console /machine:x86 /nodefaultlib /entry:start@0 /out:build/a3d-quake3-lock-test.exe \
 build/quake3_lock_test.obj build/kernel32.lib \
 /alternatename:__imp__LoadLibraryA@4=__imp__LoadLibraryA \
 /alternatename:__imp__GetProcAddress@8=__imp__GetProcAddress \
 /alternatename:__imp__GetStdHandle@4=__imp__GetStdHandle \
 /alternatename:__imp__WriteFile@20=__imp__WriteFile \
 /alternatename:__imp__ExitProcess@4=__imp__ExitProcess
