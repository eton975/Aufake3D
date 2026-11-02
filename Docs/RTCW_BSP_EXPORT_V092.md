# v0.9.2: deterministic RtCW BSP v47 surface-inventory exporter

**Research-only intermediate — not a playable RtCW A3D mod.** This tool is for
preparing data before we implement the real `IA3dGeom` / `IA3dMaterial` backend.
The output is **not** imported by today's Aufake3D audio DLLs, and it is not
accepted directly by the Aureal Vortex 2 drivers.

## What it actually reads

`Tools/export_rtcw_bsp_acoustics.py` reads **original Return to Castle
Wolfenstein (`IBSP`, version 47)** map files, either as individual `.bsp`
files or directly from an original user-owned `.pk3` archive. It validates
lump bounds/overlap and index references, and extracts planar and triangle-soup
**rendering-surface candidates** (not collision brush planes). Curved patches,
flares and other unsupported surface types are counted but **not exported**.
The resulting `.a3dmap.json` contains original BSP vertex coordinates,
indexed candidate triangles, shader names, original surface/content flags,
uncalibrated material hints, source BSP SHA-256, and explicit completeness
warnings.

**No acoustic absorption/transmission coefficients are invented.** RtCW
surface flags describe game materials, not measured frequency-dependent
acoustic properties. Visual triangles can also fail to represent collision
walls or dynamic doors. The output must not be treated as an accurate
acoustic scene until a validated geometry stage (brush clipping, patch
conversion, deduplication and dynamic scene updates) is implemented.

## Usage (modern Windows PowerShell / Debian terminal)

Requires Python 3.10+; **the exporter itself is an offline developer tool and
is not intended to run under Windows 95/98/ME/2000**.

```powershell
python Tools/export_rtcw_bsp_acoustics.py "C:\Games\RtCW\Main\pak0.pk3" --list-maps
python Tools/export_rtcw_bsp_acoustics.py "C:\Games\RtCW\Main\pak0.pk3" --map "maps/escape1.bsp" -o "escape1.a3dmap.json"
```

The map name above is an *example only*; use the name printed by `--list-maps`
for your particular archive. On Linux the same commands work with `python3`.
For a single `.bsp` file:

```bash
python3 Tools/export_rtcw_bsp_acoustics.py /path/to/level.bsp -o level.a3dmap.json
```

By default the tool refuses to overwrite any output. Use `--overwrite` only
when intentional. An invalid or unsupported map causes a nonzero exit, and
input archives/maps are never modified. The default limit is 250,000 exported
candidate triangles; oversized or malformed input is rejected, not silently
truncated. Do not distribute commercial game maps or generated asset-derived
geometry without verifying applicable rights.

## Reproducibility and testing

- The JSON is UTF-8/ASCII with sorted keys, stable vertex/triangle order, LF
  line endings, no generated timestamps, and no absolute source path.
- `source_bsp_sha256` binds output to the precise original game data.
- `tests/test_rtcw_bsp_export_v092.py` uses synthetic BSP/PK3 assets to test
  valid maps, malformed ranges, unsupported patches, non-overwrite safety and
  byte-identical output from separate directories.
- A matching result on different hosts has not yet been established for all
  real game maps; Python/runtime versions should be pinned for strict release
  qualification.

## Next work for native AU8830/Vortex 2 compatibility

1. Verify actual RtCW v47 structures against representative licensed maps.
2. Derive a conservative acoustic scene from collision brushes and surfaces,
   with explicit, calibratable material reflectance/transmission tables.
3. Simplify and budget the geometry for actual Vortex 2 driver limits.
4. Implement an optional RtCW engine audio backend calling **original Aureal
   A3D 2.0 COM methods** on period Windows and Aufake3D on modern systems.
5. Qualify hardware operation separately with proper v2041/v2048 Win9x drivers
   and the distinct Windows 2000 driver series. No hardware functionality has
   been demonstrated by this exporter.

The current RtCW `Game_Kits/Return_to_Castle_Wolfenstein` folder remains
**probe-only**. Copying those DLLs beside retail `WolfSP.exe` does not add
A3D support to the original executable.
