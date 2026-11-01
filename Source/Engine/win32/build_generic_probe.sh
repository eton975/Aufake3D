#!/usr/bin/env bash
# Build a standalone, read-only A3D ABI survey executable. Requires the
# import libs created by `bash win32/build.sh` (never ships stub DLLs).
set -euo pipefail
cd "$(dirname "$0")"
: "${CC:=clang}"; : "${LINK:=lld-link}"
mkdir -p build
# Import libraries are link-time descriptions of Windows/Wine system DLLs.
# Do not distribute the temporary stub DLLs produced by these commands.
"$LINK" /dll /noentry /machine:x86 /def:kernel32.def /out:build/kernel32-stub.dll /implib:build/kernel32.lib >build/generic-kernel32.log 2>&1
"$LINK" /dll /noentry /machine:x86 /def:ole32.def /out:build/ole32-stub.dll /implib:build/ole32.lib >build/generic-ole32.log 2>&1
"$CC" -target i686-pc-windows-msvc -ffreestanding -fno-stack-protector -fno-builtin -O2 -Wall -Wextra -Werror -c abi_probe_generic.c -o build/abi_probe_generic.obj
"$LINK" /subsystem:console /machine:x86 /nodefaultlib /entry:start@0 /out:build/a3d-abi-survey.exe build/abi_probe_generic.obj build/ole32.lib build/kernel32.lib \
 /alternatename:__imp__CoInitialize@4=__imp__CoInitialize \
 /alternatename:__imp__CoUninitialize@0=__imp__CoUninitialize \
 /alternatename:__imp__CoCreateInstance@20=__imp__CoCreateInstance \
 /alternatename:__imp__LoadLibraryA@4=__imp__LoadLibraryA \
 /alternatename:__imp__GetProcAddress@8=__imp__GetProcAddress \
 /alternatename:__imp__ExitProcess@4=__imp__ExitProcess \
 /alternatename:__imp__GetStdHandle@4=__imp__GetStdHandle \
 /alternatename:__imp__WriteFile@20=__imp__WriteFile
