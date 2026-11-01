#!/usr/bin/env python3
"""Read-only reference verifier for 2011 remaster + VorpalFix 4.2.1.
Does not launch or edit the game. Reference hashes are tied to the exact user's
submitted 2011 files; other legitimate updates might have different hashes.
"""
from pathlib import Path
import argparse, hashlib, json, sys

BASELINE = {
    'alice.exe': '08bcbe4b549633b24c90a1ab36bf516bd8873432c68b37248c98ee4225506e50',
    'winmm.dll': '051a1f894c38894eda7f893eb12db80282f3294782f1cefc423b62d9befb689e',
    'SndDrivers/mss32.dll': '14fb663762695a02e06b144c487254b08163185fa009efb32df733882cd570de',
    'SndDrivers/mssa3d2.m3d': 'bda3b0d3f698d5cd397642f93bbc7bd7c430d295b8af498847ddb4aeb143f078',
}
OPTIONAL = ('base/pak6_VorpalFix.pk3', 'base/pak7_VorpalFix_menu.pk3',
            'base/loc/INT/base_e_VorpalFix.pk3', 'VorpalFix.ini')

def scan(game: Path) -> dict:
    root = game.resolve().parent
    result = {'game':str(game.resolve()), 'reference_sha_match':{},'optional':{},'notes':[]}
    for relative, expected in BASELINE.items():
        f = root / relative
        if not f.is_file():
            result['reference_sha_match'][relative] = None
            result['notes'].append('Missing: '+relative)
        else:
            digest = hashlib.sha256(f.read_bytes()).hexdigest()
            result['reference_sha_match'][relative] = digest == expected
            if digest != expected:
                result['notes'].append(relative+': different hash from uploaded reference; investigate version before running version-specific bridge')
    for relative in OPTIONAL:result['optional'][relative]=(root/relative).is_file()
    if not result['optional']['VorpalFix.ini']: result['notes'].append('Missing VorpalFix.ini')
    result['notes'].append('Launcher requires WINEDLLOVERRIDES=winmm=n,b under Wine/Proton')
    return result

if __name__ == '__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('alice_exe',type=Path)
    args=ap.parse_args()
    if args.alice_exe.name.lower() != 'alice.exe':
        ap.error('Rename your legitimate Alice 2011 game executable to alice.exe before using bridge')
    if not args.alice_exe.is_file():ap.error('Executable not found')
    info=scan(args.alice_exe)
    print(json.dumps(info,indent=2))
    if info['reference_sha_match']['alice.exe'] is not True:sys.exit(2)
