#!/usr/bin/env python3
"""Compile and execute the portable DSP regression programs; no audio device needed.

Use --cc for a host compiler (not the freestanding PE32 target). On Windows,
Clang/MinGW's default host target is suitable. A nonzero exit fails the run.
"""
import argparse
from pathlib import Path
import subprocess
import tempfile
import os

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cc',default='cc')
    args=parser.parse_args()
    root=Path(__file__).resolve().parent
    # This archived wrapper harness predates the WinMM worker and diagnostics;
    # its OS stubs no longer compile. It is not a portable DSP program. The
    # built PE32 self-test and lock probe exercise the current source ABI.
    excluded={'test_pcm_native.c'}
    sources=[p for p in sorted((root/'tools').glob('test_*native.c')) if p.name not in excluded]+sorted((root/'win32').glob('test_*native.c'))
    print('EXCLUDED: archived test_pcm_native.c (outdated OS stubs; see VERIFICATION.md)',flush=True)
    with tempfile.TemporaryDirectory(prefix='a3d-native-') as temp:
        for source in sources:
            output=Path(temp)/(source.stem+('.exe' if os.name=='nt' else ''))
            print('COMPILE/RUN',source.relative_to(root),flush=True)
            subprocess.run([args.cc,'-std=c11','-O2','-Wall','-Wextra','-I',str(root/'win32'),str(source),'-o',str(output)],check=True)
            subprocess.run([str(output)],check=True,timeout=90)
    print(f'PASS: {len(sources)} native regression programs')

if __name__=='__main__':main()
