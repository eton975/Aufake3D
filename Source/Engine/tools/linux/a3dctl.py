#!/usr/bin/env python3
"""A3D Manager: version-independent, game-local A3D installation on Linux.

No Wine invocation, COM registration, game EXE patching, nor replacement of
VorpalFix/Miles files. Uses the existing portable ZIP packages as inputs.

Usage:
  a3dctl register q3 ~/Games/QuakeIII-117-A3D2/quake3.exe --profile quake3
  a3dctl install q3 Hotfix5_Portable.zip
  a3dctl install q3 Hotfix6_Portable.zip --no-backup
  a3dctl uninstall q3 --no-backup
  a3dctl status q3
  a3dctl uninstall q3
  a3dctl rollback q3
  a3dctl backups q3

The receipt schema is deliberately independent of the A3D release number.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import uuid
import zipfile
import xml.etree.ElementTree as ET

MANAGER_VERSION = "1.1.1"
RECEIPT = ".a3dctl-current.json"
BACKUPS = ".a3dctl-backups"
LEGACY_PATTERN = re.compile(r"\.a3d-portable-v[0-9A-Za-z_.-]+\.json\Z")
A3D_CLSID = "{92FA2C24-253C-11D2-90FB-006008A1F441}"
ALICE2011_SHA256 = "08bcbe4b549633b24c90a1ab36bf516bd8873432c68b37248c98ee4225506e50"
ALICE2011_NEEDED = ("winmm.dll", "VorpalFix.ini", "SndDrivers/mss32.dll", "SndDrivers/mssa3d2.m3d")
BIN_NAMES = {"a3d.dll", "a3dapi.dll", "a3d-comtest.exe", "a3d-legacy-probe.exe",
             "alice-a3d-bridge.exe", "alice-a3d2011-bridge.exe"}

class InstallError(Exception):
    pass




def config_path() -> Path:
    base = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home()/'.config')))
    return base / 'a3dctl' / 'games.json'


def load_games() -> dict:
    p = config_path()
    if not p.exists(): return {}
    safe_path(p)
    data=json.loads(p.read_text(encoding='utf8'))
    if not isinstance(data, dict) or any(not isinstance(v, dict) for v in data.values()):
        raise InstallError('Malformed named-game registry')
    return data


def save_games(games: dict) -> None:
    dest = config_path()
    dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.parent.is_symlink():
        raise InstallError('Refusing symlinked configuration directory')
    # Atomic replacement prevents a partial write from corrupting the registry.
    with tempfile.NamedTemporaryFile(prefix='.a3dctl-',dir=dest.parent,delete=False) as f:
        path=Path(f.name)
        try:
            f.write(json_bytes(games));f.flush();os.fsync(f.fileno())
        except BaseException:
            path.unlink(missing_ok=True)
            raise
    os.replace(path,dest)


def resolve_alias(s: str) -> tuple[Path, dict | None]:
    games=load_games()
    if s in games:
        return Path(games[s]['game']), games[s]
    # If it looks like a nickname, don't accidentally treat it as a relative EXE.
    if re.fullmatch('[A-Za-z][A-Za-z0-9_-]{0,63}',s):
        raise InstallError(f'Unknown registered game {s!r}; use register first')
    return Path(s),None


def register(name: str, game: Path, profile: str, mode: str):
    if not re.fullmatch('[A-Za-z][A-Za-z0-9_-]{0,63}',name):
        raise InstallError('Nickname must start with a letter and contain only letters, digits, _, -')
    game, blob, digest=game_info(game)
    profile_check(game,blob,profile)
    games=load_games()
    if name in games and games[name]['game']!=str(game):
        raise InstallError('Nickname already refers to a different game; forget it explicitly first')
    games[name]={'game':str(game),'profile':profile,'mode':mode}
    save_games(games)
    print(f'REGISTERED {name}: {game} ({profile}, {mode})')


def forget(name: str):
    games=load_games()
    if name not in games:
        raise InstallError(f'Nickname not found: {name}')
    del games[name];save_games(games)
    print(f'FORGOT {name}: installed game files were not changed')

def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def pe_arch(data: bytes) -> str:
    if len(data) < 128 or data[:2] != b'MZ':
        raise InstallError('Not a PE32/PE64 executable')
    off = int.from_bytes(data[60:64], 'little')
    if off + 26 > len(data) or data[off:off+4] != b'PE\0\0':
        raise InstallError('Malformed PE header')
    machine = int.from_bytes(data[off+4:off+6], 'little')
    magic = int.from_bytes(data[off+24:off+26], 'little')
    if machine == 0x14c and magic == 0x10b:
        return 'x86'
    if machine == 0x8664 and magic == 0x20b:
        return 'x64'
    raise InstallError('Unsupported PE architecture')


def safe_name(name: str) -> str:
    if not isinstance(name, str) or name in ('', '.', '..') or '/' in name or '\\' in name or name.startswith('.'):
        # Receipts themselves are validated separately and may begin with '.'
        raise InstallError(f'Unsafe owned filename: {name!r}')
    if Path(name).name != name or '\0' in name:
        raise InstallError(f'Unsafe filename: {name!r}')
    return name


def safe_path(path: Path) -> None:
    if path.is_symlink():
        raise InstallError(f'Symlink collision; refusing to alter: {path}')
    if path.exists() and not path.is_file():
        raise InstallError(f'Not an ordinary file: {path}')


def game_info(game: Path) -> tuple[Path, bytes, str]:
    if not game.is_file():
        raise InstallError(f'Game EXE not found: {game}')
    # Resolve aliases once so that receipt/backup paths are stable.
    game = game.resolve(strict=True)
    blob = game.read_bytes()
    if pe_arch(blob) != 'x86':
        raise InstallError('Only 32-bit/x86 A3D builds are available')
    return game, blob, sha_bytes(blob)


def legacy_receipts(root: Path) -> list[Path]:
    return sorted(x for x in root.iterdir() if LEGACY_PATTERN.fullmatch(x.name) and x.is_file())


def read_owned(game: Path, digest: str):
    """Read one independent manager receipt or one old installer receipt.

    Source hashes are used to distinguish managed files from unrelated files.
    Modifications are backed up, never silently deleted.
    """
    current = game.parent / RECEIPT
    old = legacy_receipts(game.parent)
    if current.exists() and old:
        raise InstallError('Both manager and legacy receipts are present; manual review required')
    if len(old) > 1:
        raise InstallError('Multiple old A3D receipts; manual review required')
    record = current if current.exists() else old[0] if old else None
    if record is None:
        return None
    safe_path(record)
    info = json.loads(record.read_text(encoding='utf-8'))
    if info.get('game') != game.name or info.get('game_sha256') != digest:
        raise InstallError('Receipt does not match the game EXE filename and SHA-256')
    if record == current:
        if info.get('schema') != 1 or not isinstance(info.get('files'), dict):
            raise InstallError('Unknown manager receipt schema')
        owned = info['files']
    else:
        if info.get('format') != 1 or not isinstance(info.get('created'), dict):
            raise InstallError('Unknown historical installer receipt format')
        owned = info['created']
    for name, hash_value in owned.items():
        safe_name(name)
        if not re.fullmatch(r'[0-9a-fA-F]{64}', str(hash_value)):
            raise InstallError(f'Invalid SHA-256 for {name}')
        safe_path(game.parent / name)
    return record, info, owned


def owned_status(game: Path, owned: dict) -> dict:
    ans = {}
    for name, expected in owned.items():
        p = game.parent / name
        ans[name] = 'missing' if not p.exists() else 'intact' if sha_file(p) == expected else 'modified'
    return ans


def profile_check(game: Path, blob: bytes, profile: str):
    lower = blob.lower()
    if profile == 'quake3':
        if game.name.lower() != 'quake3.exe' or b's_milesdriver' in lower:
            raise InstallError('Quake III profile expects quake3.exe, not an Alice executable')
        if b's_enable_a3d' not in lower and b's_usinga3d' not in lower:
            print('WARNING: No Quake III A3D markers found', file=sys.stderr)
    elif profile == 'alice':
        if game.name.lower() != 'alice.exe':
            raise InstallError('Classic Alice profile expects alice.exe')
    elif profile == 'alice2011':
        if game.name.lower() != 'alice.exe' or sha_bytes(blob) != ALICE2011_SHA256:
            raise InstallError('2011 selector bridge is only mapped for the exact supplied Alice 2011 EXE')
        absent = [p for p in ALICE2011_NEEDED if not (game.parent / p).is_file()]
        if absent:
            raise InstallError('Alice 2011/VorpalFix prerequisites missing: ' + ', '.join(absent))


def manifest(exe_name: str) -> bytes:
    ns = 'urn:schemas-microsoft-com:asm.v1'
    ET.register_namespace('', ns)
    tag = lambda n: f'{{{ns}}}{n}'
    root = ET.Element(tag('assembly'), {'manifestVersion': '1.0'})
    cleaned = ''.join(c if c.isalnum() or c in '._-' else '_' for c in exe_name)
    ET.SubElement(root, tag('assemblyIdentity'), {'type':'win32', 'name':'Unofficial.A3D.Portable.'+cleaned,
                                                   'version':'1.0.0.0'})
    file = ET.SubElement(root, tag('file'), {'name':'a3dapi.dll'})
    ET.SubElement(file, tag('comClass'), {'clsid':A3D_CLSID, 'threadingModel':'Both'})
    return b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + ET.tostring(root, encoding='utf-8') + b'\n'


class Package:
    """Read only the known binary filenames from a portable folder or ZIP.

    Never extract arbitrary ZIP paths to a game installation. Supports all
    v0.5+/v0.6+ portable packages regardless of their root folder names.
    """
    def __init__(self, path: Path):
        if not path.exists():
            raise InstallError(f'Package not found: {path}')
        self.path = path
        self.members = {}
        self.zf = None
        if path.is_dir():
            roots = [path] if (path / 'bin').is_dir() else [p for p in path.iterdir() if p.is_dir() and (p / 'bin').is_dir()]
            if len(roots) != 1:
                raise InstallError('Provide a portable package directory containing exactly one bin/ directory')
            root = roots[0] / 'bin'
            for n in BIN_NAMES:
                f = root / n
                if f.exists():
                    safe_path(f)
                    self.members[n] = ('path', f)
        else:
            try:
                self.zf = zipfile.ZipFile(path)
            except zipfile.BadZipFile as exc:
                raise InstallError('Package must be a portable ZIP or extracted portable directory') from exc
            candidates = {}
            for inf in self.zf.infolist():
                s = inf.filename.split('/')
                if len(s) >= 2 and s[-2] == 'bin' and s[-1] in BIN_NAMES and not inf.is_dir():
                    candidates.setdefault('/'.join(s[:-2]), {})[s[-1]] = inf
            if len(candidates) != 1:
                raise InstallError('ZIP must have exactly one portable bin/ set. Use the *Portable.zip, not a full-source archive.')
            for name, inf in next(iter(candidates.values())).items():
                if inf.file_size > 32 * 1024 * 1024:
                    raise InstallError(f'Unusually large binary in ZIP: {name}')
                self.members[name] = ('zip', inf)
        if 'a3dapi.dll' not in self.members and 'a3d.dll' not in self.members:
            raise InstallError('No A3D DLLs found in bin/')

    def get(self, name: str) -> bytes:
        item = self.members.get(name)
        if not item:
            raise InstallError(f'Package missing {name}')
        typ, obj = item
        raw = obj.read_bytes() if typ == 'path' else self.zf.read(obj)
        if pe_arch(raw) != 'x86':
            raise InstallError(f'{name} is not a 32-bit Windows binary')
        return raw

    def close(self):
        if self.zf:
            self.zf.close()


def payloads(game: Path, package: Package, profile: str, mode: str, probes: bool) -> dict[str, bytes]:
    wanted = {'both': ['a3d.dll','a3dapi.dll'], 'legacy':['a3d.dll'], 'com':['a3dapi.dll']}[mode]
    if profile == 'alice2011' and mode == 'legacy':
        raise InstallError('Alice 2011 requires com or both mode')
    out = {name: package.get(name) for name in wanted}
    if mode != 'legacy':
        out[game.name + '.manifest'] = manifest(game.name)
    if profile == 'alice' and mode != 'legacy':
        n='alice-a3d-bridge.exe'
        out[n] = package.get(n)
        out[n+'.manifest'] = manifest(n)
    if profile == 'alice2011':
        n='alice-a3d2011-bridge.exe'
        out[n] = package.get(n)
    if probes:
        for n in ('a3d-comtest.exe','a3d-legacy-probe.exe'):
            if (n == 'a3d-comtest.exe' and mode == 'legacy') or (n == 'a3d-legacy-probe.exe' and mode == 'com'):
                continue
            out[n] = package.get(n)
            if n == 'a3d-comtest.exe':
                out[n+'.manifest'] = manifest(n)
    for n in out:
        safe_name(n)
    return out


def json_bytes(info: dict) -> bytes:
    return (json.dumps(info, indent=2, sort_keys=True) + '\n').encode('utf-8')


def ensure_backup_dir(game: Path) -> Path:
    root = game.parent / BACKUPS
    if root.is_symlink():
        raise InstallError(f'Backups directory must not be a symlink: {root}')
    root.mkdir(exist_ok=True)
    return root


def backup_current(game: Path, owned, reason: str) -> str | None:
    """Move *only* receipt-listed files into a durable, rollback-able backup.

    Hash-mismatched and missing files are reported and do not prevent removal.
    This is intentional; old installers blocked the whole operation on those.
    """
    if owned is None:
        return None
    receipt_path, info, hashes = owned
    root = ensure_backup_dir(game)
    ident = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    dest = root / ident
    dest.mkdir(mode=0o700)
    (dest / 'files').mkdir()
    moved = []
    missing = []
    status = owned_status(game, hashes)
    try:
        for n in sorted(hashes):
            src = game.parent / n
            if not src.exists():
                missing.append(n)
                continue
            dst = dest / 'files' / n
            os.replace(src, dst)
            moved.append((src, dst))
        os.replace(receipt_path, dest / receipt_path.name)
        moved.append((receipt_path, dest / receipt_path.name))
        info_backup = {'id': ident, 'game':game.name,'game_sha256':sha_file(game),
                       'receipt':receipt_path.name,'reason':reason,'status':status,
                       'missing':missing,'created_utc':datetime.now(timezone.utc).isoformat()}
        (dest / 'backup.json').write_bytes(json_bytes(info_backup))
    except BaseException:
        for src,dst in reversed(moved):
            if dst.exists():
                os.replace(dst,src)
        shutil.rmtree(dest, ignore_errors=True)
        raise
    print(f'BACKUP: {dest}')
    for n in sorted(status):
        if status[n] != 'intact':
            print(f'  preserved previous {n}: {status[n]}')
    return ident


def stash_current_in_transaction(game: Path, owned, temporary_root: Path) -> list[tuple[Path, Path]]:
    """Temporarily move receipt-owned files aside without creating a backup.

    These files survive *only* until the operation commits. On a failure the
    caller must put them back before the TemporaryDirectory is removed.
    This provides rollback of a failed filesystem operation, NOT user rollback
    after a successful --no-backup operation.
    """
    if owned is None:
        return []
    receipt_path, _, hashes = owned
    moved = []
    try:
        for name in sorted(hashes):
            src = game.parent / name
            safe_path(src)
            if not src.exists():
                continue
            dst = temporary_root / name
            os.replace(src, dst)
            moved.append((src, dst))
        dst = temporary_root / receipt_path.name
        os.replace(receipt_path, dst)
        moved.append((receipt_path, dst))
    except BaseException:
        restore_transaction_stash(moved)
        raise
    return moved


def restore_transaction_stash(moved: list[tuple[Path, Path]]) -> None:
    """Restore source paths after a failed no-backup operation."""
    for original, stashed in reversed(moved):
        if stashed.exists():
            if original.exists():
                raise InstallError(f'Cannot restore transaction: destination occupied: {original}')
            os.replace(stashed, original)


def no_backup_warning(operation: str, game: Path, owned) -> None:
    print(f'WARNING: {operation} --no-backup: replaced/removed managed files will '
          'be permanently discarded after successful completion.', file=sys.stderr)
    if owned:
        statuses = owned_status(game, owned[2])
        for name, status in sorted(statuses.items()):
            if status == 'modified':
                print(f'  WARNING: locally modified managed file will be lost: {name}', file=sys.stderr)


def install(game: Path, package_file: Path, profile: str, mode: str, probes: bool, dry_run: bool, no_backup: bool=False):
    game,blob,digest = game_info(game)
    if profile == 'auto':
        old = read_owned(game, digest)
        profile = old[1].get('profile', 'generic') if old else ('quake3' if game.name.lower() == 'quake3.exe' else 'generic')
    profile_check(game,blob,profile)
    pkg=Package(package_file)
    try:
        output=payloads(game,pkg,profile,mode,probes)
    finally:
        pkg.close()
    old=read_owned(game,digest)
    previous=set(old[2]) if old else set()
    for n in output:
        p=game.parent / n
        safe_path(p)
        if p.exists() and n not in previous:
            raise InstallError(f'Unowned file collision: {p}; refusing to overwrite')
    rc=game.parent/RECEIPT
    if rc.exists() and old is None:
        raise InstallError('Unknown manager receipt already present')
    desc = {'profile':profile,'mode':mode,'package':str(package_file),'files':sorted(output),
            'replacing':old[0].name if old else None, 'backup':not no_backup}
    print(json.dumps(desc,indent=2))
    if dry_run:
        print('DRY RUN: no files changed');return
    if no_backup and old:
        no_backup_warning('install', game, old)
    # Write new files to a private stage before changing the old installation.
    with tempfile.TemporaryDirectory(prefix='.a3dctl-stage-',dir=game.parent) as temp:
        stage=Path(temp)
        for n,data in output.items():
            (stage/n).write_bytes(data)
        if no_backup and old:
            (stage/'prior').mkdir()
        receipt={'schema':1,'manager':MANAGER_VERSION,'game':game.name,
                 'game_sha256':digest,'profile':profile,'mode':mode,
                 'package':package_file.name,'files':{n:sha_bytes(b) for n,b in output.items()}}
        (stage/RECEIPT).write_bytes(json_bytes(receipt))
        backup_id=None if no_backup else backup_current(game,old,'upgrade')
        stashed=stash_current_in_transaction(game,old,stage/'prior') if no_backup and old else []
        created=[]
        try:
            for n in sorted(output):
                dst=game.parent/n
                if dst.exists():
                    raise InstallError(f'Unexpected file collision at commit: {dst}')
                os.replace(stage/n,dst)
                created.append(dst)
            os.replace(stage/RECEIPT,rc)
            created.append(rc)
        except BaseException:
            for p in reversed(created):
                p.unlink(missing_ok=True)
            if backup_id:
                restore_backup(game,backup_id,save_current=False)
            if stashed:
                restore_transaction_stash(stashed)
            raise
    print('INSTALLED: '+profile+' / '+mode+(' (prior installation backed up)' if backup_id else ' (no persistent backup)' if no_backup and old else ''))


def uninstall(game: Path,dry_run: bool,no_backup: bool=False):
    game,_,hash_value=game_info(game)
    owned=read_owned(game,hash_value)
    if not owned:
        print('NOT INSTALLED: no recognised A3D receipt');return
    print(json.dumps({'receipt':owned[0].name,'files':owned_status(game,owned[2]), 'backup':not no_backup},indent=2))
    if dry_run:
        print('DRY RUN: no files changed');return
    if no_backup:
        no_backup_warning('uninstall',game,owned)
        with tempfile.TemporaryDirectory(prefix='.a3dctl-txn-',dir=game.parent) as txn:
            stash_current_in_transaction(game,owned,Path(txn))
        print('UNINSTALLED: managed files discarded; no backup created')
    else:
        backup_current(game,owned,'uninstall')
        print('UNINSTALLED: files moved to backup (recoverable with rollback)')


def list_backups(game: Path) -> list[dict]:
    root = game.parent/BACKUPS
    if not root.exists(): return []
    if root.is_symlink() or not root.is_dir():
        raise InstallError('Unsafe backups directory')
    entries=[]
    for folder in sorted(root.iterdir(),reverse=True):
        meta=folder/'backup.json'
        if folder.is_dir() and not folder.is_symlink() and meta.is_file():
            data=json.loads(meta.read_text(encoding='utf-8'))
            if data.get('id')==folder.name and (folder/data.get('receipt','')).is_file():
                entries.append(data)
    return entries


def restore_backup(game:Path, backup_id:str|None,save_current:bool,no_backup:bool=False):
    game,_,digest=game_info(game)
    entries=list_backups(game)
    if not entries:
        raise InstallError('No saved A3D backups found')
    if not backup_id:
        backup_id=entries[0]['id']
    matched=[e for e in entries if e['id']==backup_id]
    if len(matched)!=1:
        raise InstallError('Unknown backup ID')
    meta=matched[0]
    if meta['game']!=game.name or meta['game_sha256']!=digest:
        raise InstallError('Backup game identity/hash does not match')
    src=game.parent/BACKUPS/backup_id
    receipt_name=meta['receipt']
    if receipt_name != RECEIPT and not LEGACY_PATTERN.fullmatch(receipt_name):
        raise InstallError('Unsafe receipt inside backup')
    receipt=(src/receipt_name)
    if not receipt.is_file() or receipt.is_symlink():
        raise InstallError('Missing backup receipt')
    rdata=json.loads(receipt.read_text())
    filenames=rdata.get('files') if receipt_name==RECEIPT else rdata.get('created')
    if not isinstance(filenames,dict):
        raise InstallError('Unsupported backup receipt')
    for name in filenames:
        safe_name(name)
        p=src/'files'/name
        if p.exists(): safe_path(p)
    current=read_owned(game,digest)
    current_files=set(current[2]) if current else set()
    for name in filenames:
        dest=game.parent/name
        if dest.exists() and name not in current_files:
            raise InstallError(f'Restore would overwrite unowned file: {dest}')
    if (game.parent/receipt_name).exists() and not (current and current[0].name==receipt_name):
        raise InstallError('Restore receipt collision')
    # A --no-backup rollback uses a temporary transaction stash, not a durable
    # rollback-undo snapshot. Preserve current files if restoring the snapshot fails.
    from contextlib import nullcontext
    context = (tempfile.TemporaryDirectory(prefix='.a3dctl-txn-', dir=game.parent)
               if save_current and no_backup and current else nullcontext(None))
    with context as txn:
        stashed = []
        if save_current and current:
            if no_backup:
                no_backup_warning('rollback',game,current)
                stashed = stash_current_in_transaction(game,current,Path(txn))
            else:
                backup_current(game,current,'rollback-undo')
        # Preserve backup contents if restoration fails. An existing backup
        # is consumed on success, while any older backups remain untouched.
        moved=[]
        try:
            for name in sorted(filenames):
                f=src/'files'/name
                if not f.exists():
                    continue
                dst=game.parent/name
                if dst.exists():
                    raise InstallError(f'Restore target occupied: {dst}')
                os.replace(f,dst)
                moved.append((f,dst))
            if (game.parent/receipt_name).exists():
                raise InstallError(f'Restore receipt target occupied: {game.parent/receipt_name}')
            os.replace(receipt,game.parent/receipt_name)
            moved.append((receipt,game.parent/receipt_name))
        except BaseException:
            for original,now in reversed(moved):
                if now.exists(): os.replace(now,original)
            if stashed:
                restore_transaction_stash(stashed)
            raise
        # Preserve consumed backup metadata, but mark it as restored.
        meta['restored_utc']=datetime.now(timezone.utc).isoformat()
        (src/'backup.json').write_bytes(json_bytes(meta))
    print(f'RESTORED: {backup_id}'+(' (current installation not backed up)' if no_backup and current else ''))


def cmd_status(game: Path):
    game,_,digest=game_info(game)
    owned=read_owned(game,digest)
    if not owned:
        print(json.dumps({'installed':False,'game':str(game),'backups':len(list_backups(game))},indent=2))
    else:
        receipt,info,files=owned
        print(json.dumps({'installed':True,'game':str(game),'receipt':receipt.name,
                          'managed_by':'a3dctl' if receipt.name==RECEIPT else 'legacy',
                          'profile':info.get('profile'),'mode':info.get('mode'),
                          'files':owned_status(game,files),'backups':len(list_backups(game))},indent=2))


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--version', action='version', version='a3dctl '+MANAGER_VERSION)
    subs=p.add_subparsers(dest='command',required=True)
    for command in ('status','install','uninstall','rollback','backups','register','forget','games'):
        q=subs.add_parser(command)
        if command in ('status','install','uninstall','rollback','backups'):
            q.add_argument('game',help='Registered nickname (e.g. q3), or full path to game EXE')
        if command=='register':
            q.add_argument('name',help='Short alias, e.g. q3 or alice2011')
            q.add_argument('exe',type=Path,help='Unmodified game EXE')
            q.add_argument('--profile',choices=['generic','quake3','alice','alice2011'],required=True)
            q.add_argument('--mode',choices=['both','legacy','com'],default='both')
        if command=='forget':
            q.add_argument('name',help='Registered nickname')
        if command=='install':
            q.add_argument('package',type=Path,help='Any supported portable release ZIP or extracted folder')
            q.add_argument('--profile',choices=['auto','generic','quake3','alice','alice2011'],default='auto')
            q.add_argument('--mode',choices=['auto','both','legacy','com'],default='auto')
            q.add_argument('--no-probes',action='store_true')
        if command=='rollback':
            q.add_argument('--backup',help='Backup ID; otherwise newest')
        if command in ('install','uninstall','rollback'):
            q.add_argument('--dry-run',action='store_true')
            q.add_argument('--no-backup',action='store_true', help='Do not save a persistent rollback snapshot of the files being replaced or removed (irreversible)')
    args=p.parse_args(argv)
    try:
        if args.command=='register': register(args.name,args.exe,args.profile,args.mode)
        elif args.command=='forget':forget(args.name)
        elif args.command=='games':print(json.dumps(load_games(),indent=2))
        else:
            game, alias=resolve_alias(args.game)
            if args.command=='status': cmd_status(game)
            elif args.command=='backups':
                game,_,digest=game_info(game)
                print(json.dumps(list_backups(game),indent=2))
            elif args.command=='install':
                profile=args.profile
                if profile=='auto' and alias:
                    profile=alias['profile']
                mode=args.mode
                if mode=='auto':
                    if alias:
                        mode=alias['mode']
                    else:
                        oldgame,_,digest=game_info(game)
                        old=read_owned(oldgame,digest)
                        mode=old[1].get('mode','both') if old else 'both'
                install(game,args.package,profile,mode,not args.no_probes,args.dry_run,args.no_backup)
            elif args.command=='uninstall': uninstall(game,args.dry_run,args.no_backup)
            elif args.command=='rollback':
                game,_,digest=game_info(game)
                entries=list_backups(game)
                if args.dry_run:
                    print(json.dumps({'would_restore':args.backup or (entries[0]['id'] if entries else None)},indent=2))
                else:
                    restore_backup(game,args.backup,save_current=True,no_backup=args.no_backup)
        return 0
    except (InstallError,ValueError,OSError,KeyError,json.JSONDecodeError,zipfile.BadZipFile) as exc:
        print(f'ERROR: {exc}',file=sys.stderr)
        return 1

if __name__=='__main__':
    raise SystemExit(main())
