#!/usr/bin/env python3
"""Verified v0.9.2a HRTF reference-default source overlay. Dry-run by default."""
from pathlib import Path
import argparse, hashlib, sys, shutil

GAMES = ['Alice_2000', 'Alice_2011_VorpalFix', 'Quake_III_117', 'Half_Life_1011', 'Unreal_Classic', 'Return_to_Castle_Wolfenstein', 'GTA_III', 'GTA_Vice_City']
SUFFICES = ['RUN_AUFAKE3D_WINDOWS.cmd', 'RUN_AUFAKE3D_WINE.sh']
EXPECTED = {'Alice_2000': ['443afe827a80039cd78dc98b05dbeb231332ae86', 'f64c3ca9e7623964a7d3dcb103a11ae4da3a82ec'], 'Alice_2011_VorpalFix': ['e9660fe973b5a1a53fe56b56b95bcd6e45f7e12b', 'e1fe466c04b10be6f8cd3106ebb0b0bb04796b4a'], 'Quake_III_117': ['3c26259af13af354d35cafd616be820d5b2abe2c', '90d31a256f3c5168e61c313ea04efb60667d250c'], 'Half_Life_1011': ['efa9be0d8de96c45680e6810a46f5b523946d69a', '15660395bd1944f45c1c05f79b99340cdd95004f'], 'Unreal_Classic': ['48af0e16a77f03a93efa269814039e420deb4d3f', '8040b1f39f7f6aa23c98b59b7ea689d1af8042d5'], 'Return_to_Castle_Wolfenstein': ['9cefde38913d55ec61a1b0b5eec45d9e753ecc1b', 'abfd6d53edb2222ecbd121595a166f1d0b4e1a8c'], 'GTA_III': ['bab941b50ba4a589bf5400353bfc49e6e043a695', 'da1824a5c88f8851b4d55b992bc55609a44058b2'], 'GTA_Vice_City': ['d1b7edee1e51ab5af674d37aff4f636cb98646eb', '42d558da2fe20ff285e02171ec261c47f831954f']}

def gitblob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()

def run(root, apply=False):
    if not (root/'scripts/build.py').exists():
        raise ValueError('Not an Aufake3D repository root')
    changes={}
    for game in GAMES:
        for idx, suffix in enumerate(SUFFICES):
            rel=Path('packaging/Game_Kits')/game/'COPY_TO_GAME_FOLDER'/suffix
            path=root/rel
            old=path.read_bytes()
            current=gitblob(old)
            if current!=EXPECTED[game][idx]:
                raise ValueError(f'Script not byte-identical to published v0.9.2 source: {rel}; git blob={current}')
            if suffix.endswith('.cmd'):
                prior=b'if not defined A3D_HRTF_MODE set "A3D_HRTF_MODE=fast"'
                desired=b'if not defined A3D_HRTF_MODE set "A3D_HRTF_MODE=reference"'
            else:
                prior=b'export A3D_HRTF_MODE="${A3D_HRTF_MODE:-fast}"'
                desired=b'export A3D_HRTF_MODE="${A3D_HRTF_MODE:-reference}"'
            if old.count(prior)+old.count(desired)!=1:
                raise ValueError(f'Unexpected HRTF declaration: {rel}')
            new=old.replace(prior,desired)
            if new != old:changes[path]=new
    if len(changes)!=10:
        raise ValueError(f'Expected ten defaults to change, got {len(changes)}')
    doc_rel=Path('Docs/AU8830_HRTF_PERFORMANCE_MODES.md')
    doc_old=(root/doc_rel).read_bytes()
    doc_sha=gitblob(doc_old)
    if doc_sha!='7e49aa0fffce1f5f2afbe367a9e6e07057b14d5f':
        raise ValueError(f'HRTF modes documentation differs from published v0.9.2: {doc_sha}')
    doc_new=doc_old
    for before,after in [
       (b'`fast` (default in game launchers)',b'`fast` (optional override)'),
       (b'`reference` | Same 56 taps',b'`reference` (default in game launchers) | Same 56 taps'),
       (b'Or use `reference` or `legacy`. The launcher sets `fast` only if the caller has',b'Or use `fast` or `legacy`. The launcher sets `reference` only if the caller has')]:
        if doc_new.count(before)!=1:
            raise ValueError('Unexpected HRTF modes guide text')
        doc_new=doc_new.replace(before,after)
    changes[root/doc_rel]=doc_new
    rootextras={
      'scripts/package_hrtf_hotfix.py': 'scripts/package_hrtf_hotfix.py',
      'tests/test_hrtf_hotfix_defaults.py':'tests/test_hrtf_hotfix_defaults.py',
      'Docs/HRTF_REFERENCE_DEFAULT_HOTFIX.md':'Docs/HRTF_REFERENCE_DEFAULT_HOTFIX.md',
    }
    archive_root=Path(__file__).resolve().parent
    for target, origin in rootextras.items():
        src=archive_root/origin
        if not src.is_file():raise ValueError(f'Patch payload missing: {src}')
        if (root/target).exists():raise ValueError(f'Refusing to overwrite existing file: {root/target}')
    print('Verified 16 active game launchers against published v0.9.2 Git tree.')
    print('Will replace FAST with REFERENCE in 10 scripts and update HRTF documentation. Six already REFERENCE.')
    if not apply:
        print('DRY RUN: no files modified. Re-run with --apply.')
        return
    for p,new in sorted(changes.items()):
        p.write_bytes(new)
        print('Updated:',p.relative_to(root))
    for target,origin in rootextras.items():
        dest=root/target
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(archive_root/origin,dest)
        print('Added:',target)
    print('PASS: hotfix source changes installed. Validate tests, build and reproducibility before release.')

if __name__ == '__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--apply',action='store_true')
    args=ap.parse_args()
    try:run(args.root.expanduser().resolve(),args.apply)
    except (OSError,ValueError) as e:ap.exit(1,f'ERROR: {e}\n')
