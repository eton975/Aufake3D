#!/usr/bin/env python3
"""Safely integrate the experimental A3D helper into a Descent 3 *source* tree.

Never modifies or patches retail game executables. Requires explicit --apply;
by default only verifies exact expected old-source anchors. The source tree
must have the conditional A3D code (e.g. revision 07262f6 before PR #345).
"""
from __future__ import annotations
import argparse
from pathlib import Path
import shutil

HERE=Path(__file__).resolve().parent
HELPER=HERE/'aufake3d_aureal.cpp'
FLAG='// #define SUPPORT_AUREAL'
CPPS='  ssl_lib.cpp)'

def plan(checkout:Path)->tuple[Path,Path,Path,str,str]:
    checkout=checkout.resolve()
    header=checkout/'dd_sndlib/auddev.h'
    cmake=checkout/'dd_sndlib/CMakeLists.txt'
    dest=checkout/'dd_sndlib/aufake3d_aureal.cpp'
    if not header.is_file() or not cmake.is_file():
        raise ValueError('Not a historical Descent 3 Windows audio source tree')
    h=header.read_text(encoding='utf-8')
    c=cmake.read_text(encoding='utf-8')
    if h.count(FLAG)!=1 or c.count(CPPS)!=1 or dest.exists():
        raise ValueError('Source layout changed or adapter already installed; leaving untouched')
    # Never silently alter a modern tree from which the legacy backend was removed.
    if not (checkout/'dd_sndlib/geometry.cpp').is_file() or 'Ds3dlib.cpp' not in c:
        raise ValueError('Missing historical geometry/mixer source; refusing integration')
    return header,cmake,dest,h.replace(FLAG,'#define SUPPORT_AUREAL'),c.replace(CPPS,'  ssl_lib.cpp\n  aufake3d_aureal.cpp)')

def main()->int:
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('checkout',type=Path,help='historical Descent 3 source checkout, never the retail game folder')
    a.add_argument('--apply',action='store_true',help='modify the source checkout, with backup copies')
    ns=a.parse_args()
    try:header,cmake,dest,h,c=plan(ns.checkout)
    except (OSError,ValueError) as e:a.exit(2,f'REFUSED: {e}\n')
    if not ns.apply:
        print('CHECK PASS: found expected historical auddev.h and CMake source anchors; no files modified')
        print('Use --apply to install the adapter into this source checkout.')
        return 0
    shutil.copy2(header,header.with_name(header.name+'.aufake3d.bak'))
    shutil.copy2(cmake,cmake.with_name(cmake.name+'.aufake3d.bak'))
    header.write_text(h,encoding='utf-8',newline='')
    cmake.write_text(c,encoding='utf-8',newline='')
    shutil.copy2(HELPER,dest)
    print('Installed source-only experimental adapter; original header and CMake backed up.')
    print('This has not built, altered, launched or certified the retail game.')
    return 0
if __name__=='__main__':raise SystemExit(main())
