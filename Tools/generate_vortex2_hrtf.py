#!/usr/bin/env python3
"""Validate a contributor-provided AU8830 register dump and emit a CRT-free C table.

No original Aureal SDK headers/binaries are needed. This generates source data,
not hardware-exact DSP arithmetic. Redistribution requires coefficient owner consent.
"""
from __future__ import annotations
import argparse, csv, hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CSV=ROOT/'data/vortex2_hrtf_grid_15deg_fixed180.csv'
OUT=ROOT/'Source/Engine/win32/vortex2_hrtf_table.h'
TAPS=56


def generate(src:Path=CSV):
    raw=src.read_bytes()
    rows=list(csv.DictReader(raw.decode('utf-8-sig').splitlines()))
    assert len(rows)==217, f'expected 217 grid positions, got {len(rows)}'
    expected=[(az,el) for el in range(-45,76,15) for az in range(0,360,15)]+[(0,90)]
    actual=[(int(r['az_deg']),int(r['el_deg'])) for r in rows]
    assert actual==expected, 'noncanonical azimuth/elevation ordering or duplicate rows'
    table=[]; itd=[]
    for row in rows:
        taps=[]
        for side in ('left','right'):
            ear=[int(row[f'{side}{i}']) for i in range(TAPS)]
            assert all(-32768<=v<=32767 for v in ear),'coefficient outside signed Q15'
            taps.append(ear)
        word=int(row['itd_word'],16)
        delays=[word&0xffff, (word>>16)&0xffff]
        assert max(delays)<=0x5000, 'implausible AU8830 ITD; possible 180-degree corruption'
        for i in range(2):
            sample=float(row['itd_left_samples' if i==0 else 'itd_right_samples'])
            assert abs(sample-delays[i]/512.0)<0.0002,'ITD word/sample mismatch'
        table.append(taps);itd.append(delays)
    # Fixed 180-degree entries must not contain the original anomalous 40-sample delays.
    assert all(itd[el*24+12]==[0,0] for el in range(9))
    lines=['/* Generated from contributor-supplied corrected AU8830 filter capture.',
           ' * Do not edit; regenerate via tools/generate_vortex2_hrtf.py.',
           f' * SHA256 input CSV: {hashlib.sha256(raw).hexdigest()}',
           ' * 56 taps, signed Q15; ITD 1/512 sample, 48 kHz. Not a bit-exact DSP model.',
           ' */','#ifndef AUFAKE_VORTEX2_HRTF_TABLE_H','#define AUFAKE_VORTEX2_HRTF_TABLE_H',
           '#define AUFAKE_V2_DIRECTIONS 217u','#define AUFAKE_V2_TAPS 56u',
           'static const signed short aufake_v2_coeff[217][2][56] = {']
    for taps in table:
        lines.append(' {{'+','.join(str(x) for x in taps[0])+'},')
        lines.append('  {'+','.join(str(x) for x in taps[1])+'}},')
    lines+=['};','static const unsigned short aufake_v2_itd[217][2] = {']
    lines.extend(' {%d,%d},' %tuple(delay) for delay in itd)
    lines+=['};','#endif']
    return '\n'.join(lines)+'\n'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
    generated=generate()
    if args.check:
        assert OUT.read_text()==generated, 'table is stale: regenerate first'
        print('AU8830 source table verified: 217 positions, 56 taps/ear')
    else:
        OUT.write_text(generated)
        print(f'Wrote {OUT}: {len(generated)} characters')
