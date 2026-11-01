#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
: "${CC:=clang}"
: "${LINK:=lld-link}"
"$LINK" /lib /def:kernel32.def /machine:x86 /out:kernel32.lib
"$CC" -target i686-pc-windows-msvc -O2 -fno-stack-protector -fno-builtin -ffreestanding -Wall -Wextra -Werror -c alice_a3d2011_bridge.c -o alice_a3d2011_bridge.obj
opts=()
for ent in GetModuleFileNameA:12 GetCommandLineA:0 CreateProcessA:40 ReadProcessMemory:20 WriteProcessMemory:20 VirtualAllocEx:20 VirtualProtectEx:20 FlushInstructionCache:12 ResumeThread:4 WaitForSingleObject:8 GetExitCodeProcess:8 TerminateProcess:8 CloseHandle:4 GetStdHandle:4 WriteFile:20 ExitProcess:4 GetThreadContext:8 SetThreadContext:8 CreateActCtxA:4 ActivateActCtx:8; do
  name=${ent%:*}; size=${ent#*:}
  opts+=("/alternatename:__imp__${name}@${size}=__imp__${name}")
done
"$LINK" /subsystem:console /entry:mainCRTStartup /nodefaultlib /machine:x86 alice_a3d2011_bridge.obj kernel32.lib "${opts[@]}" /out:alice-a3d2011-bridge.exe
printf 'Built alice-a3d2011-bridge.exe (PE32/i386). Actual remaster/VorpalFix/Wine gameplay testing still required.\n'
