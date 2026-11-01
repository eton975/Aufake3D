# What the user's v0.1.9 Miles enumeration *actually* established

The user ran the original Miles Sound System under Wine-Staging 11.19 in a stand-alone PE32 probe. `mss32.dll` and both `mssa3d.m3d`/`mssa3d2.m3d` loaded. `AIL_startup` returned `1`. `AIL_enumerate_3D_providers` returned:

| Handle | Name |
| --- | --- |
| `0x00000004` | Aureal A3D Interactive (TM) |
| `0x00000005` | Aureal A3D 2.0 (TM) |
| `0x00000006` | Dolby Surround |
| `0x00000007` | Creative Labs EAX (TM) |
| `0x00000008` | Creative Labs EAX 2 (TM) |
| `0x00000009` | Miles Fast 2D Positional Audio |

The enumerator output `AIL_LAST_ERROR=` (empty) and exited `0`.

**Important correction to earlier expectations:** the enumerator did *not* perform a post-digital-driver comparison. It reported `DIGITAL_DRIVER_EXPORTS_MISSING=1` because its particular `_AIL_open_digital_driver@16` name lookup failed. Consequently, we have exactly *one* provider list, not two. This missing function is a limitation of that probe, not evidence of missing game audio.

The prior actual game run produced the console messages `Could not find 3D provider Aureal A3D 2.0 (TM)` and `Could not find 3D provider a3d2`, followed by `Miles Fast 2D Positional Audio provider opened.` Those messages are **not** proof that Miles as a library is unable to enumerate the provider: v0.1.9 shows that enumeration is possible in an independent process.

## v0.2.0: Next narrow, hardware-independent gate

The new `a3d-miles-open.exe` calls `AIL_open_3D_provider` on the exact enumerated A3D2 handle. It also runs a separate Fast 2D control in a *fresh process*. Each process records the result code, immediate `AIL_last_error`, plugin DLL activity and optional calls to our diagnostic A3D COM wrapper. No game binaries are copied, patched or redistributed, Alice.exe is not run, no sound samples are played, and no PCI work is needed. **Opening a provider is not the same as working 3D audio**.

To run on Debian 13 after extracting the archive, from its root:

```bash
bash tools/wine_miles_open.sh '/home/youruser/Games/Alice/Alice.exe'
```

Upload the automatically generated `~/alice-a3d2-miles-open-<UTC timestamp>.tar.gz`. The probe limits each Wine process to 35 seconds and captures independent logs; a timeout or crash is still useful evidence. No need to enter a level or reconfigure the game. `wine_com_probe.sh` is run as a preflight to register the current diagnostic DLL into the already-isolated test Wine prefix.

## Interpretations

- If Fast 2D opens but A3D2 fails: compare the A3D2 `AIL_last_error` and whether `a3dapi.dll` was activated. The gap is provider *activation*; enumeration alone worked.
- If both open: Alice's provider-selection logic or hardware gating is the likely next focus; additionally verify that the COM shim actually received calls, since an empty wrapper log means an alternative path may be used.
- If both fail: investigate the test initialization sequence and/or Wine audio integration before concluding anything about Aureal specifically.
- If either fails with a crash or timeout: inspect the final progress marker (`OPEN_CALL_BEGIN` vs `OPEN_CALL_RETURNED`) to locate the failure.

The wrapper remains diagnostic-only. `IA3dSource`, real PCM capture/rendering, binaural HRTF, and full geometry-aware A3D2 Wavetracing are not implemented. The ultimate scope remains cross-game A3D 1.x/2.0/3.0 on Windows and Wine.
