#!/usr/bin/env bash
# v0.5.0 SOURCE COMMENTARY — Legacy probe build automation
# Builds the minimal A3dCreate probe for detecting legacy export availability. The
# probe verifies DLL loading and DirectSound creation only.
set -euo pipefail
cd "$(dirname "$0")/../win32"
: "${CC:=clang}"; : "${LINK:=lld-link}"
mkdir -p build
"$CC" -target i686-pc-windows-msvc -ffreestanding -fno-stack-protector -fno-builtin -O2 -Wall -Wextra -Werror -c legacy_probe.c -o build/legacy_probe.obj
"$LINK" /subsystem:console /machine:x86 /nodefaultlib /entry:start@0 /out:build/a3d-legacy-probe.exe build/legacy_probe.obj build/kernel32.lib \
 /alternatename:__imp__LoadLibraryA@4=__imp__LoadLibraryA \
 /alternatename:__imp__GetProcAddress@8=__imp__GetProcAddress \
 /alternatename:__imp__GetStdHandle@4=__imp__GetStdHandle \
 /alternatename:__imp__WriteFile@20=__imp__WriteFile \
 /alternatename:__imp__ExitProcess@4=__imp__ExitProcess
