#!/usr/bin/env python3
# v0.5.0 SOURCE COMMENTARY — Engineering/research utility
# Supports repeatable data generation, audio tests, game-file analysis, or Wine
# probing. Inspect command-line arguments and preserve user-owned game files.
"""Rebuild 22.05k/44.1k/48k MIT KEMAR measured HRIR data included in the A3D DLL.

Usage: python tools/generate_measured_hrir.py /path/to/MIT_KEMAR_normal_pinna.sofa
Requires h5py, numpy, scipy. Source dataset supplied separately by libmysofa.
Copyright 1994 Bill Gardner, Keith Martin, MIT Media Laboratory;
free use provided authors are cited in research/commercial applications.
"""
import argparse
from pathlib import Path
import h5py
import numpy as np
from scipy.signal import resample_poly


def generate(sofa: Path, outfile: Path) -> None:
    with h5py.File(sofa, "r") as f:
        pos = np.array(f["SourcePosition"][:])
        ir = np.array(f["Data.IR"][:, :, :320])
        samplerate = float(f["Data.SamplingRate"][0])
    assert pos.shape == (710, 3) and ir.shape == (710, 2, 320)
    assert samplerate == 44100.0
    a = np.deg2rad(pos[:, :2])
    xyz = np.column_stack((np.cos(a[:, 1]) * np.cos(a[:, 0]),
                           np.cos(a[:, 1]) * np.sin(a[:, 0]), np.sin(a[:, 1])))
    p = ["/* MIT KEMAR measured HRIRs from Debian libmysofa SOFA; Copyright 1994 Bill Gardner, Keith Martin, MIT Media Laboratory.\n",
         " * Provided without restrictions on use provided authors are cited when used in research/commercial applications.\n",
         " * Converted from /usr/share/libmysofa/MIT_KEMAR_normal_pinna.sofa; original 44.1 kHz; resampled for 22.05/48 kHz.\n",
         " * This is NOT Aureal AU8830 coefficient data. All data derived from MIT measurement, no patented API or driver code.\n */",
         "\n#ifndef A3D_MEASURED_DATA_H\n#define A3D_MEASURED_DATA_H\n#define A3D_MEASURED_DIRECTIONS 710\n",
         "static const float a3d_mdir[710][3] = {\n"]
    for v in xyz:
        p.append(" {" + ",".join(f"{float(x):.8f}f" for x in v) + "},\n")
    p.append("};\n")
    for rate, up, down, taps in [(22050, 1, 2, 160), (44100, 1, 1, 320), (48000, 160, 147, 348)]:
        filtered = (resample_poly(ir, up, down, axis=-1) * (rate/44100.0)
                    if rate != 44100 else ir)
        q = np.clip(np.rint(filtered[:, :, :taps] * 32768), -32768, 32767).astype(np.int16)
        p.append(f"#define A3D_TAPS_{rate} {taps}\nstatic const signed short a3d_mhrir_{rate}[710][2][{taps}] = {{\n")
        for left, right in q:
            p.append(" {{" + ",".join(map(str, map(int, left))) + "},{"
                     + ",".join(map(str, map(int, right))) + "}},\n")
        p.append("};\n")
    p.append("#endif\n")
    outfile.parent.mkdir(parents=True, exist_ok=True)
    outfile.write_text("".join(p), encoding="utf-8")
    print(f"Generated {outfile}: {outfile.stat().st_size} bytes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sofa", type=Path)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent.parent / "win32/measured_hrir_data.h")
    args = parser.parse_args()
    generate(args.sofa, args.output)
