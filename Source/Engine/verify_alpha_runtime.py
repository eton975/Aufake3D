#!/usr/bin/env python3
"""Check the canonical deployment: PE32 files, shared engine and Bash syntax.

Windows runs the three ABI programs per profile. Wine hosts may opt in to
real Wine ABI smoke separately through DEBIAN13_ABI_SMOKE.sh. No game starts.
"""
from pathlib import Path
import hashlib,os,subprocess,json,shutil
R=Path(__file__).resolve().parent
D=R/'deploy-v070-alpha'
games=('Alice2000','Alice2011-VorpalFix','QuakeIII-117','HalfLife-Retail','Unreal-Galaxy','Generic-A3D2')
def main():
    for dll in ('a3dapi.dll','a3d.dll'):
        assert len({hashlib.sha256((D/g/dll).read_bytes()).digest() for g in games})==1
    count=0
    for p in sorted(D.rglob('*')):
        if p.suffix.lower() in ('.dll','.exe'):
            b=p.read_bytes();off=int.from_bytes(b[60:64],'little')
            assert b[:2]==b'MZ' and b[off:off+4]==b'PE\0\0'
            assert int.from_bytes(b[off+4:off+6],'little')==0x14c,p
            assert int.from_bytes(b[off+24:off+26],'little')==0x10b,p
            count+=1
        if p.suffix=='.sh':subprocess.run(['bash','-n',str(p)],check=True)
    print(f'PASS: {count} PE32 files; shared DLL identity; all deployed Bash syntax')
    if os.name=='nt':
        env=os.environ.copy();env.update(A3D_LOG='0',A3D_LATENCY_TRACE='0',A3D_STAFF_DIAG='0',A3D_WEAPON_CAPTURE='0')
        for g in games:
            for name in ('a3d-selftest.exe','a3d-comtest.exe','a3d-quake3-lock-test.exe'):
                print('WINDOWS ABI',g,name,flush=True)
                subprocess.run([str((D/g/name).resolve())],cwd=D/g,env=env,check=True,timeout=30)
        print('PASS: 18 native Windows ABI smoke executions; no games or audio playback')
    print('Real Wine runtime smoke: not run by this script. Linux gameplay: unverified.')
if __name__=='__main__':main()

