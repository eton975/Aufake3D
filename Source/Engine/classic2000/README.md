# American McGee's Alice 2000 — A3D selector bridge prototype

This package only extends the existing Sound Driver menu's `a3d2` choice.
The on-disk stock `alice.exe` and `SndDrivers` binaries are NEVER modified.
The launcher DOES change six bytes of executable code **in the child process's RAM**
after checking the expected original 2000 Alice instructions. If memory editing
also violates your requirement, do not use this prototype. No OS driver,
registry, or global installation is performed by this package.

## Prerequisites
- Stock alice.exe (known size 2,209,835 bytes) with Base/*.pk3 and SndDrivers/*.m3d.
- v0.4.2 A3D 2.0 a3dapi.dll and alice.exe.manifest beside the original EXE.
- Wine capable of running 32-bit x86 applications, or native Windows.

## Verify and install
From this extracted directory:

    python3 install_bridge.py "$HOME/Games/ALICE/alice.exe" --check-only
    python3 install_bridge.py "$HOME/Games/ALICE/alice.exe"

This copies only `alice-a3d-bridge.exe` and its manifest beside alice.exe.
It declines altered game executables and existing destination files.

## Launch
Use the existing corrected Wine launcher (included in this ZIP):

    bash ./run_wine.sh "$HOME/Games/ALICE/alice-a3d-bridge.exe"

Your `alice.exe` itself is started automatically as a CHILD process.
The game directory is set as its current working directory to find resources.
The standard Alice UI `Controls > Audio > Sound Driver` already has:
`miles`, `dolby`, `a3d`, `a3d2`, `eax`, and `eax2`.

Choose `a3d` for original A3D Interactive, `a3d2` for Aureal A3D 2.0.
Select/apply, exit and restart using the bridge launcher if necessary.
Expected A3D2 message: `Aureal A3D 2.0 (TM) provider opened.`

IMPORTANT: `a3d` selects the original A3D 1.x Miles module, but the current
v0.4.2 A3D1 emulation is only a preliminary DirectSound compatibility bridge.
The optional `legacy_A3D1/a3d.dll` in the ZIP can be tried only after backing
up any existing a3d.dll; it does not yet reproduce original Vortex HRTFs.
Do NOT copy legacy a3d.dll if a working original is already installed.

## Rollback
Exit Alice and remove only these two NEW files from the game directory:
  alice-a3d-bridge.exe
  alice-a3d-bridge.exe.manifest
Then launch stock alice.exe normally. It has not been altered.

## Limitations
- Only supported (after signature check) for the known original Alice 2000 binary.
- Experimental and NOT tested in Wine/actual gameplay in this environment.
- It does not fix A3D2 sound stuttering, intro/menu failures or guarantee
  COM activation. The 0.4.2 HRTF implementation still needs runtime validation.
- Implementation only changes provider-name translation in runtime memory;
  other games will need different integration. Keep generic A3D engines separate.
- If the bridge refuses startup, do NOT defeat signature checking.
