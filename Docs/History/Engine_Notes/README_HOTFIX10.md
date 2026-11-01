# A3D v0.6.0 – Hotfix 10: Quake III 1.17 acoustic-list crash correction

**Experimental in Wine, but with a precisely identified and corrected API-contract violation.**
Build lineage: Hotfix 9 (which itself derives from Hotfix 7), NOT the experimental Hotfix 8 PCM-tail branch.

## Diagnosis – Quake III crash at 0x0042D02F / EAX=0xABABABAB

The genuine Quake III Arena 1.17 executable (27 April 2000) deliberately
stores the 32-bit placeholder 0xABABABAB at 0x0042D11F in its internal table of
Aureal acoustic list pointers. Later it calls the IA3dList::Call method (COM
vtable slot 5, +0x14) at 0x0042D032 and adds EAX, the Call return value, to a
running number of polygons at 0x0042D035. It repeats until that count reaches
its geometry budget.

The emulator previously returned HRESULT S_OK, numerically zero, even after
successfully executing a list containing polygons. The count could therefore
remain zero, causing the game to walk beyond the resolved list pointers and
attempt a virtual call on its own 0xABABABAB placeholder at 0x0042D02F.

The published Aureal A3D 3.0 API manual, `IA3dList::Call` and
`IA3dList::Begin, IA3dList::End` reference pages, specifies a successful
`Call` / `End` result as **nNumPolygons**, not S_OK. Despite the `HRESULT`
prototype, a positive integer is the intended successful result.
Source: https://manualzz.com/doc/1629249/aureal-a3d-api-engine-audio-user-manual

## Correction

- `IA3dList::End` returns the recorded *polygon* count.
- `IA3dList::Call` returns the number of submitted polygons, not S_OK=0.
- Count original triangle/quad primitives separately from internal
  triangulation (one quad = one polygon = two ray-tracing triangles).
- Preserve negative failure return values for invalid lists/capacity errors.
- Keep prior 128-voice pool, 48-tap measured HRTF and adaptive geometry caching.
- No game executable modifications; no Wine registry installation.

## Test

`win32/test_list_polygon_count_hf10_native.c` exercises the actual COM-list
functions with native Win32 allocator stubs; asserts Begin success, End=3,
Call=3 for a list of two triangles plus one quad, and checks interface slots,
recorded triangle count, repeated calls, and empty-list semantics.
`build_and_test_v060.sh` runs the new regression plus all previous suites.

## Install with Linux a3dctl v1.1.1

    a3dctl install q3 "$HOME/Downloads/A3D_v0.6.0_Q3_ListCount_Hotfix10_Portable.zip" --no-backup
    a3dctl status q3

Remove `--no-backup` if you prefer to preserve a rollback snapshot.

## Run the same Demo 1

    cd "$HOME/Games/QuakeIII-117-A3D2"
    LOG="$(winepath -w "$PWD/a3d-hf10-demo1.log")"
    env -u A3D_TRACE_DETAIL \
      A3D_PROBE_LOG="$LOG" \
      A3D_GEOMETRY_TRACE=1 A3D_GEOMETRY_RETRACE_BLOCKS=8 \
      A3D_MASTER_GAIN=0.1 A3D_HRTF_TAPS=48 A3D_REVERB_WET=0 \
      A3D_VOICE_LIMIT=128 A3D_WAVEOUT_QUEUE_HEADERS=3 \
      A3D_WAVEOUT_SUBBLOCKS=2 A3D_Q3_DMA_CLOCK=0 \
      wine ./quake3.exe

Keep `s_mixahead=0.35` and `s_mixPreStep=0.05` for comparisons.
Report whether Demo 1 completes **past the previous crash point**, FPS and
stuttering, and upload `a3d-hf10-demo1.log` after a normal exit.

This corrects the *identified* crash mechanism. Remaining native game bugs,
other ABI incompatibilities and actual Wine gameplay are unverified.
