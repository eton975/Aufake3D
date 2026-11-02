#!/usr/bin/env python3
"""Aufake3D v0.9.2 reversible game-local installer; Python 3 stdlib only.
Does not modify game executables or system registry. Profiles are not compatibility guarantees.
"""
import argparse, hashlib, json, os, shutil, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
PROFILES={'alice2011': 'alice.exe','alice2000':'alice.exe','quake3':'quake3.exe','halflife':'hl.exe','unreal':'unreal.exe','rtcw':'wolfsp.exe'}
PINNED_ALICE='08bcbe4b549633b24c90a1ab36bf516bd8873432c68b37248c98ee4225506e50'
PINNED_MILES='14fb663762695a02e06b144c487254b08163185fa009efb32df733882cd570de'

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for chunk in iter(lambda:f.read(1<<18),b''):h.update(chunk)
    return h.hexdigest()

def kit_layout(profile):
    """Authoritative copy map; shared by manual instructions and automated installers."""
    mapping=json.loads((ROOT/'Game_Kits/INSTALL_MAP.json').read_text(encoding='utf-8'))['profiles'][profile]
    kit=ROOT/'Game_Kits'/mapping['folder']/'COPY_TO_GAME_FOLDER'
    expected={str(p.relative_to(kit)).replace('\\','/') for p in kit.rglob('*') if p.is_file()}
    if set(mapping['files'])!=expected:
        raise ValueError('Game kit content differs from INSTALL_MAP.json; installation refused')
    return mapping, kit

def overlay(profile,exe):
    """Resolve the exact game-local payload, preserving original Miles files.

        Returns a destination->source map; this validates prerequisites but never writes.
        """
    base=exe.parent
    meta,kit=kit_layout(profile)
    if exe.name.lower()!=meta['exe']:
        raise ValueError('Game executable and game kit do not match')
    files={base/Path(rel):kit/rel for rel in meta['files']}
    if profile=='alice2011':
        snd=base/'SndDrivers'
        if not (base/'winmm.dll').is_file() or not (base/'VorpalFix.ini').is_file():
            raise ValueError('Alice 2011/VorpalFix winmm.dll and VorpalFix.ini must already be installed')
        if not (snd/'mssa3d2.m3d').is_file():raise ValueError('Missing game-owned SndDrivers/mssa3d2.m3d')
        vendor=next((p for p in (snd/'a3d_mss_real.dll',snd/'mss32.dll') if p.is_file() and sha(p)==PINNED_MILES),None)
        if vendor is None:raise ValueError('Required exact original 32-bit Miles DLL not found (hash mismatch); refusing unsafe proxy installation')
        # Save the vendor DLL under its *own* filename in both locations, not from the kit.
        for folder in (base,snd):files[folder/'a3d_mss_real.dll']=vendor
    elif profile=='alice2000':
        if not (base/'SndDrivers/mss32.dll').is_file():raise ValueError('Missing original game-owned Alice2000 SndDrivers/mss32.dll')
    return files

def validate(profile,exe):
    exe=exe.expanduser().resolve(strict=True)
    if not exe.is_file() or exe.name.lower()!=PROFILES[profile]:
        raise ValueError(f'Expected original {PROFILES[profile]}, got {exe.name}')
    if profile=='alice2011' and sha(exe)!=PINNED_ALICE:
        raise ValueError('Alice2011 executable hash is not the supported exact build; refusing unsafe version-specific profile')
    # Prevent accidentally staging over executable or outside its folder.
    return exe

def install(profile, exe, dry_run=False):
    """Transactionally stage the game kit and save hashes for guarded rollback.

        No original game executable bytes are changed; a receipt prevents stacking.
        """
    exe=validate(profile,exe)
    mapping=overlay(profile,exe)
    if (exe.parent/'.aufake3d_current.json').exists():raise ValueError('Existing v0.9.2 receipt found; roll back before reinstalling')
    target_root=exe.parent
    for dest,src in mapping.items():
        if not src.is_file() or not dest.parent.is_dir():raise ValueError(f'Missing install input or target folder: {src} -> {dest}')
        if dest.resolve()==exe.resolve():raise ValueError('Refusing game EXE overwrite')
        if dest.is_symlink():raise ValueError(f'Refusing symbolic-link target: {dest}')
    # Source might be an already-installed vendor copy in the same directory.
    # Capture all source file bytes BEFORE any replacement occurs.
    data={str(d):s.read_bytes() for d,s in mapping.items()}
    snapshot=[]
    for d in mapping:
        snapshot.append({'rel':str(d.relative_to(target_root)), 'exists':d.exists(), 'original_sha256':sha(d) if d.exists() else None,'installed_sha256':hashlib.sha256(data[str(d)]).hexdigest()})
    print('Profile:',profile,' Game EXE:',exe,'(sha256:',sha(exe),')')
    for d in mapping:print(' ', ('REPLACE' if d.exists() else 'CREATE'),d.relative_to(target_root))
    if dry_run:return
    backup=target_root/'.aufake3d_backup_v090'/str(time.time_ns())
    backup.mkdir(parents=True,exist_ok=False)
    receipt={'profile':profile,'game_exe':str(exe),'game_exe_sha256':sha(exe),'files':snapshot,'backup_dir':str(backup),'release':'0.9.2','created_at':time.strftime('%Y-%m-%dT%H:%M:%S%z')}
    try:
        for item in snapshot:
            dest=target_root/item['rel']
            if item['exists']:
                b=backup/'original'/item['rel'];b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(dest,b)
        # Installed payload source already cached, including original vendor Miles.
        for d in mapping:
            tmp=d.with_name('.aufake3d-writing-'+d.name)
            tmp.write_bytes(data[str(d)])
            os.replace(tmp,d)
            if d.suffix=='.sh':d.chmod(d.stat().st_mode | 0o111)
        (backup/'receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
        (target_root/'.aufake3d_current.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    except Exception:
        # Best-effort transaction rollback on failure.
        for item in reversed(snapshot):
            dest=target_root/item['rel'];orig=backup/'original'/item['rel']
            if item['exists'] and orig.is_file():shutil.copy2(orig,dest)
            elif not item['exists'] and dest.exists():dest.unlink()
        raise
    print('Installed game-local components. Original game executable unchanged.')
    print('Run:',target_root/'RUN_AUFAKE3D_WINDOWS.cmd','or',target_root/'RUN_AUFAKE3D_WINE.sh')
    print('Rollback: python3 Tools/aufake3d.py rollback --game-exe "'+str(exe)+'"')

def rollback(exe):
    """Restore only files whose hashes still equal the installed payload.

        Refuse rollback if a user edited files after installation.
        """
    exe=exe.expanduser().resolve(strict=True);root=exe.parent;rp=root/'.aufake3d_current.json'
    if not rp.is_file():raise ValueError('No Aufake3D v0.9.2 install receipt found')
    r=json.loads(rp.read_text(encoding='utf-8-sig'))
    if r['game_exe']!=str(exe) or sha(exe)!=r['game_exe_sha256']:
        raise ValueError('Target EXE differs from original installation; refusing rollback')
    backup=Path(r['backup_dir'])
    for item in r['files']:
        dest=root/item['rel']
        if not dest.is_file() or sha(dest)!=item['installed_sha256']:
            raise ValueError('A staged file changed since installation; refusing rollback: '+str(dest))
    for item in reversed(r['files']):
        dest=root/item['rel'];orig=backup/'original'/item['rel']
        if item['exists']:
            if not orig.is_file() or sha(orig)!=item['original_sha256']:
                raise ValueError('Backup corruption: '+str(orig))
            shutil.copy2(orig,dest)
        else:dest.unlink()
    rp.unlink()
    print('Rollback complete. Backup retained at', backup)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    s=ap.add_subparsers(dest='action',required=True)
    p=s.add_parser('install');p.add_argument('--profile',choices=PROFILES,required=True);p.add_argument('--game-exe',type=Path,required=True);p.add_argument('--dry-run',action='store_true')
    p=s.add_parser('rollback');p.add_argument('--game-exe',type=Path,required=True)
    a=ap.parse_args()
    try:
        if a.action=='install':install(a.profile,a.game_exe,a.dry_run)
        else:rollback(a.game_exe)
    except (ValueError,OSError,KeyError) as e:
        print('ERROR:',e,file=sys.stderr);raise SystemExit(2)
if __name__=='__main__':main()
