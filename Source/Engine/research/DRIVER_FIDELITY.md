# Windows 9x Aureal driver research: next fidelity milestones

Based on the **user-supplied** 4.06.2041 and 4.06.2048 archives, inspected
read-only. The vendor binaries are not redistributed in this release.

- 2041 and 2048 contain byte-identical `a3d.dll`, 159,744 bytes. Its PE export
  table exposes `_A3dCreate@12` (ordinal 6) and four COM exports (ordinals 2–5).
  Our new independent bridge mirrors those exported symbols, but NOT their
  original implementation.
- `a3dapi.dll` differs considerably: 290,816 bytes (2041), 466,944 bytes
  (2048). Code paths for geometry/occlusion and reflection algorithms require
  function-level comparative disassembly before implementation claims.
- 2041 `Au30DAL.dll` exports `CSpeakerInterface::InitializeHrtf` and
  `CSpeakerInterface::SendHrtf`; these are valuable leads for determining how
  HRTF coefficients were delivered to AU8830. They do NOT yet prove the driver
  holds all HRIR filter coefficient tables.
- The A3D2 wrapper currently uses independently prepared KEMAR HRIRs and an
  approximate ray-based acoustic model. Those are NOT equivalence measurements
  of the AU8830.

## Fidelity-gated test plan

1. Obtain a completed Alice audio scene trace using the *working* COM backend.
2. Trace the 9x `a3dapi.dll` path from `IA3dGeom` submission through material
   reflection allocation; compare 2041 versus 2048 branch conditions.
3. Trace `Au30DAL.dll` `SendHrtf` through the kernel IOCTL, and establish
   register coefficient format (sign, width, rounding, endianness).
4. Build controlled directional HRIR and reflection impulse-response fixtures.
5. After successful software integration, capture physical AU8830 reference
   results from Win98SE; compare sample timing, gain, frequency response,
   reflection delays and eventual waveform hashes.

Until those checks pass, label the implementation *experimental* rather than
"bit-perfect Aureal". This also preserves the project's future integrity as a
public/forkable historical preservation effort.

## Newly verified from 2041 `Au30DAL.dll` disassembly

The DLL's export-table RVAs identify the following three routines (image base
`0x10000000`). Directly disassembling those entry points with `objdump -d -M
intel` reveals concrete `DeviceIoControl` calls, not merely suggestive export
names:

| Export | RVA | Observed IOCTL | What this establishes |
|---|---:|---:|---|
| `CSpeakerInterface::InitializeHrtf` | `0x2e40` | `0x001D2F90` | HRTF setup/initialisation is requested through the driver |
| `CSpeakerInterface::GetHrtfRenderers` | `0x2eb0` | `0x001D2FB8` | HRTF-related data is read through a driver call |
| `CSpeakerInterface::SendHrtf` | `0x2f30` | `0x001D2FE0` | A supplied data buffer and its byte count are passed to the kernel driver |

These are **driver-control codes, not recovered HRTF coefficients**. The kernel
VxD's decoding and the resulting AU8830 register writes still need to be
traced. The three values and the call signatures should be treated as a more
precise starting point than the export names alone.
