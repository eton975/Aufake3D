# A3D v0.7.0-alpha — Half-Life and shared launcher progress

This development snapshot adds a narrowly scoped Half-Life startup workaround, more careful shared capability reporting and launcher diagnostics. It does not certify Half-Life or Unreal audio/gameplay. The previous alpha and v0.6.12 distributions remain separate.

## Half-Life findings

The user confirms the original installation runs normally on this Windows PC. In this agent's isolated test context, the supplied retail 1.0.1.1 launcher exits before loading hw.dll/sw.dll because RegCreateKeyExA for HKLM\Software\Aureal\A3D returns error 5 (access denied). The routine only sets the obsolete vendor SplashScreen DWORD to zero; its failure nevertheless aborts launcher setup. This is an observed test-context failure, not evidence that the user's installation is broken or that the COM manifest causes it.

A private debugger experiment skipped that routine's call, after which the trace reached successful window-class registration and launcher setup and the process stayed alive through the 20-second observation. A Half-Life window was listed by the desktop tool, but that tool could not capture/control it because of a window-identity error. No usable menu, engine audio, map playback or listening result was confirmed.

The release launcher offers an explicit A3D_HALFLIFE_SPLASH_FIX=1 option. In the newly created suspended child's RAM, it checks the x86 PE header, timestamp, entry RVA, image size, routine prologue/tail/call landmarks and adjacent registry/value names before replacing six bytes with a successful return. Unknown layouts or failed memory operations abort that child. It reads the child's actual image base rather than assuming a fixed load address. The original executable and the registry are not changed. This bypasses only optional vendor splash configuration; it does not establish audio compatibility.

The signature matcher was compiled from this source and matched the supplied hl.exe read-only. A separate synthetic PE with matching landmarks exercises the actual Windows child-memory read/protect/write/restore/flush path, activation and exit forwarding. Unknown synthetic editions are rejected. That fixture contains no game implementation. The final production workaround has not yet been exercised successfully in the real game; the private debugger experiment is distinct from that test.

## Shared capabilities

Software/hardware capability records now use an independent byte-based writer. It accepts older short records, fills only complete known DWORDs, preserves dwSize, unknown tails and partial fields, and supports unaligned callers. Software 2D/3D maxima report the actual configured shared voice pool: 128 by default, or the selected A3D_VOICE_LIMIT (clamped by the existing mixer to 8–128). These maxima are not additive allocations. Hardware records do not claim an Aureal accelerator. Native COM tests include a selected limit of 24; portable boundary checks cover sizes 0–80 and canaries.

The IA3d/IA3d2 control-prefix views retain common IUnknown identity. Full legacy A3D1 DirectSound3D spatial interception and A3D3 extension interfaces remain unimplemented; IA3d5 is deliberately rejected rather than returning an incompatible vtable.

## Shared launcher

The fixed Half-Life/Unreal launchers and generic a3d-launch.exe share child-local manifest activation. Generic syntax remains `a3d-launch.exe --game "adjacent.exe" -- [game arguments]`. The launcher rejects recursive self-targets, paths/traversal, missing manifests, non-PE32 targets and oversized arguments. It preserves quoted game arguments, the inherited environment and child status.

Optional launcher diagnostics identify preflight, suspended child creation, bootstrap installation, resume and child exit, with Win32 error codes where applicable. Bootstrap installation is explicitly not proof of bootstrap execution or A3D use. Logs never include the raw game command line or environment. Normal launches create no launcher log. A diagnostic run writes at most 64 KiB, overwriting that run's launcher log rather than growing it indefinitely.

Unreal retains its inspected Galaxy/IA3d4 startup contract and experimental profile; no new Unreal gameplay result is claimed. The generic scanner/stager and compatibility research shortlist remain development tools, not a universal supported-games list. The profile generator now refreshes Generic-A3D2 along with the five title profiles, preventing stale generic payloads after rebuilding.

## Preserved settings

Alice weapon clarity stays on in its normal profiles, with original-mix fallback; generic/Half-Life/Unreal profiles do not enable Alice recognition. The established three titles retain 6×256 buffering, 48-tap HRTF, gain 5.0, Alice 2011 VorpalFix FPS default and explicit 144 override, and logs off. DSP implementation and embedded HRTF data are unchanged from the preceding alpha.

No actual Wine runtime or Linux gameplay was verified. Bash syntax and mock-Wine argument/environment checks are included in regression testing. Read SETUP_CANDIDATES.md and GENERIC_CANDIDATE_SETUP.md before a game test.
