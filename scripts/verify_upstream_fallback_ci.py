#!/usr/bin/env python3
"""Manual/branch CI probe of independently hosted full-archive LLVM fallback.

This downloads large upstream archives on purpose: it is not part of the
normal small-download one-click build or the mandatory four-platform gate.
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import build_pinned as pin


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--host',choices=('linux','windows'),required=True)
    opts=parser.parse_args()
    expected='windows' if os.name=='nt' else 'linux'
    if opts.host!=expected:
        raise RuntimeError('Wrong CI host for upstream fallback probe: '+expected)
    with tempfile.TemporaryDirectory(prefix='aufake3d-upstream-llvm-test-') as temp:
        cache=Path(temp)
        os.environ['A3D_PINNED_FORCE_UPSTREAM']='1'
        llvm=pin.pinned_llvm(cache,opts.host)
        env=pin.build_env(cache,Path(sys.executable),llvm)
        pin.assert_versions(llvm,env)
        suffix='.exe' if opts.host=='windows' else ''
        clang=llvm/('clang'+suffix)
        linker=llvm/('lld-link'+suffix)
        source=cache/'fallback-probe.c'
        obj=cache/'fallback-probe.obj'
        pe=cache/'fallback-probe.dll'
        source.write_text('int llvm_upstream_recovery(void){return 19;}\n',encoding='ascii')
        subprocess.run([str(clang),'-target','i686-pc-windows-msvc',
                        '-ffreestanding','-c',str(source),'-o',str(obj)],
                       env=env,check=True)
        subprocess.run([str(linker),'/dll','/noentry','/nodefaultlib',
                        '/machine:x86','/timestamp:0',str(obj),'/out:'+str(pe)],
                       env=env,check=True)
        if pe.read_bytes()[:2]!=b'MZ':
            raise RuntimeError('Full upstream fallback did not produce valid PE DLL')
        print('PASS: recovered exact CI Clang/LLD from independent upstream LLVM archive.')
        print('PASS: compiled and linked a PE32 Windows DLL without any game modification.')


if __name__=='__main__':
    main()
