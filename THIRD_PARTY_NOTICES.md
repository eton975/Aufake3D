# Third-party attributions, notices and dependencies

This notice accompanies the source-only release and separate minimal core binary package.

## MIT Media Laboratory — KEMAR HRTF measurement data (1994)

**Copyright 1994 MIT Media Laboratory.** Original authors and required attribution:

- Bill Gardner
- Keith Martin
- MIT Media Laboratory, Machine Listening Group

Reference: Gardner, W. G. and Martin, K. D., *HRTF Measurements of a KEMAR Dummy-Head Microphone*, MIT Media Laboratory, 1994.

The original dataset permits free use without restrictions provided the authors are credited when used in a research or commercial application. **These measurement data are not licensed under Aufake3D's MIT *software* licence.**

Aufake3D's generated HRIR tables are in:

- `Source/Engine/win32/measured_hrir_data.h`
- `Source/NameFix_Tests/offline_sources/measured_hrir_data.h`

They were derived from the `MIT_KEMAR_normal_pinna.sofa` dataset distributed with Debian's `libmysofa`, with rate conversion/quantization by `Source/Engine/tools/generate_measured_hrir.py`. The original `.sofa` file is **not distributed**.

Dataset notice source: https://sources.debian.org/src/libmysofa/1.3.1~dfsg0-1/tests/LICENSE.MIT_KEMAR_pinnae
Dataset reference: https://sound.media.mit.edu/resources/KEMAR.html

## Independent acoustics module

The `Source/Engine/acoustics/` module is MIT-licensed under its existing notice identifying 2026 *Alice A3D Acoustics Prototype contributors*. Its original licence is included at `Source/Engine/acoustics/LICENSE` and reproduced in `Source/Engine/LICENSE_ACOUSTICS.txt`. Preserve that attribution even if the rest of Aufake3D is MIT-licensed.

## Aureal A3D interoperability reference

The original Aureal A3D 1.x, 2.0 and 3.x SDKs informed COM GUIDs, interface layout and behavioural expectations. Aufake3D is an independent software implementation and must not be described as an official Aureal product. Original SDK code, documents, drivers, logos and retail binaries have **not** intentionally been included in the distribution. Interoperability information does **not** mean original vendor implementation code is publicly licensed.

## Miles Sound System and games

Miles/RAD Game Tools libraries are commercial dependencies supplied by end users with their games. **Original vendor Miles DLLs are not bundled**, and Aufake3D does not convey permission to copy them between unrelated installations. The Aufake3D `mss32.dll` compatibility *proxy* is **not bundled** in this source-only edition; its source and a published 331-export name/ordinal ABI map are included. It rebuilds byte-for-byte without proprietary Miles files at build time. A separately distributed full-runtime review candidate carries the proxy, which loads a matching, legitimately owned original `a3d_mss_real.dll` at game runtime. Neither build reproducibility nor the availability of interface metadata establishes a blanket right to redistribute original vendor code.

Retail game executables/data, VorpalFix, original Aureal drivers and original Miles DLLs are absent. Microsoft Windows, Wine, LLVM/Clang/LLD, Python, CMake and other development tools are external dependencies and not redistributed here.
