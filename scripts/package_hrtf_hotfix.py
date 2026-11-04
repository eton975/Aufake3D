#!/usr/bin/env python3
"""Repackage an authentic v0.9.2 runtime with reference-default launchers.

The binary DLLs are copied unchanged. This only changes game launchers and
rebuilds checksums/ZIP metadata. It is not proof of improved spatial quality.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

HOTFIX_VERSION = '0.9.2a-HRTF-hotfix'
ORIGINAL_VERSION = '0.9.2'
ORIGINAL_PREFIX = 'Aufake3D-v0.9.2-Local/'
HOTFIX_PREFIX = 'Aufake3D-v0.9.2a-HRTF-hotfix-Local/'
OFFICIAL_SHA256 = '6952672bfbd60130bf2d8bb16a445f35707458bd817d0907e0853e033c8d28ad'
FROZEN_CI_SHA256 = 'a64f99e63e235e310c4d8dd45dff05f7b77271d744c9d060a9ca84a9b28f3848'
GAME_KITS = ('Alice_2000', 'Alice_2011_VorpalFix', 'Quake_III_117',
             'Half_Life_1011', 'Unreal_Classic', 'Return_to_Castle_Wolfenstein',
             'GTA_III', 'GTA_Vice_City')
SUFFIXES = ('RUN_AUFAKE3D_WINDOWS.cmd', 'RUN_AUFAKE3D_WINE.sh')

NOTES = """Aufake3D v0.9.2a-HRTF-hotfix: REFERENCE DEFAULT LAUNCHER HOTFIX

Source baseline: published Git tag v0.9.2 (commit 4eeb00fc5443e2e8d0f2664df08d6f36a01f3b28).
Every active Game_Kits Windows CMD and Linux/Wine SH launcher now defaults to
A3D_HRTF_MODE=reference, but explicit environment-variable overrides are honoured.
GTA III, Vice City and Alice 2011 were already reference-default in v0.9.2.

The universal a3d.dll and a3dapi.dll, auxiliary binaries, game data and
DSP algorithms are UNCHANGED. This is a launcher-configuration repack.
WARNING: v0.9.2 FAST/REFERENCE are designed for identical PCM output. No
claim of better perceived 3D or corrected HRTF is justified without testing.
A game kit is not proof the game supports A3D or that gameplay was certified.
Retail Descent 3 has no game launcher in its separate DLL-only kit; this
hotfix does not change that standalone ZIP.

This archive has an updated LOCAL_BUILD_SHA256.json manifest and reproducible
fixed-metadata ZIP entries. SHA-256 identity across the release CI matrix
must be independently checked; a local archive alone is NOT certification.
Use headphones at low volume initially: default A3D_MASTER_GAIN=5.0.
""".encode('utf-8')


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replacement(rel: str, original: bytes) -> tuple[bytes, bool]:
    if rel.endswith('.cmd'):
        prior = b'if not defined A3D_HRTF_MODE set "A3D_HRTF_MODE=fast"'
        desired = b'if not defined A3D_HRTF_MODE set "A3D_HRTF_MODE=reference"'
    else:
        prior = b'export A3D_HRTF_MODE="${A3D_HRTF_MODE:-fast}"'
        desired = b'export A3D_HRTF_MODE="${A3D_HRTF_MODE:-reference}"'
    if original.count(prior) + original.count(desired) != 1:
        raise ValueError(f'Unknown or ambiguous HRTF launcher layout: {rel}')
    result = original.replace(prior, desired)
    assert result.count(desired) == 1
    return result, result != original


def create(input_zip: Path, output_zip: Path, *, from_built: bool = False,
           allow_frozen_ci_base: bool = False) -> tuple[str, int, int]:
    if input_zip.resolve() == output_zip.resolve():
        raise ValueError('Input and output ZIP must be different')
    whole_sha = sha(input_zip.read_bytes())
    if from_built:
        provenance = 'source-rebuilt locally; verification pending'
    elif whole_sha == OFFICIAL_SHA256:
        provenance = 'published v0.9.2 release archive (exact SHA-256)'
    elif allow_frozen_ci_base and whole_sha == FROZEN_CI_SHA256:
        provenance = 'frozen earlier v0.9.2 CI archive (NOT the published release)'
    else:
        raise ValueError('Input is not the published v0.9.2 runtime.\n'
                         f'  received SHA-256: {whole_sha}\n'
                         f'  expected SHA-256: {OFFICIAL_SHA256}\n'
                         'Use --from-built only for your newly rebuilt patched source, '
                         'or --allow-frozen-ci-base to inspect the historic CI candidate.')
    with zipfile.ZipFile(input_zip, 'r') as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f'Input ZIP CRC failure: {bad}')
        members = archive.infolist()
        if len({m.filename for m in members}) != len(members):
            raise ValueError('Duplicate ZIP member names')
        content = {}
        for member in members:
            name = member.filename
            if member.is_dir() or not name.startswith(ORIGINAL_PREFIX):
                raise ValueError(f'Unexpected ZIP member: {name}')
            rel = name[len(ORIGINAL_PREFIX):]
            p = PurePosixPath(rel)
            if not rel or rel.startswith('/') or '..' in p.parts or '\\' in rel:
                raise ValueError(f'Unsafe ZIP member: {name}')
            content[rel] = archive.read(member)

    key = 'LOCAL_BUILD_SHA256.json'
    if key not in content or 'UNIFIED_ENGINE_SHA256.json' not in content:
        raise ValueError('Missing runtime integrity manifests')
    manifest = json.loads(content[key])
    if manifest.get('version') != ORIGINAL_VERSION or not isinstance(manifest.get('sha256'), dict):
        raise ValueError('Unexpected original runtime manifest')
    existing_hashes = {rel: sha(data) for rel, data in content.items() if rel != key}
    if manifest['sha256'] != existing_hashes:
        raise ValueError('Original runtime file hashes differ from its embedded SHA-256 manifest')

    expected = {
        f'Game_Kits/{game}/COPY_TO_GAME_FOLDER/{suffix}'
        for game in GAME_KITS for suffix in SUFFIXES
    }
    actual = {name for name in content if name.startswith('Game_Kits/')
              and (name.endswith('RUN_AUFAKE3D_WINDOWS.cmd') or name.endswith('RUN_AUFAKE3D_WINE.sh'))}
    if actual != expected:
        raise ValueError(f'Unexpected launcher set; missing={sorted(expected - actual)} extras={sorted(actual - expected)}')
    changed = 0
    for rel in sorted(expected):
        content[rel], did_change = replacement(rel, content[rel])
        changed += did_change
    if from_built and changed:
        raise ValueError('Patched source build still contains FAST-default launchers')
    if not from_built and changed != 10:
        raise ValueError(f'Expected exactly ten FAST-default scripts in base, found {changed}')
    # Keep the current HRTF guide aligned with these defaults; old archives
    # explicitly say FAST is the launcher default, which is now inaccurate.
    doc = 'Docs/AU8830_HRTF_PERFORMANCE_MODES.md'
    if doc not in content:
        raise ValueError('Required current HRTF modes guide missing')
    docdata = content[doc]
    for old, new in (
        (b'`fast` (default in game launchers)', b'`fast` (optional override)'),
        (b'`reference` | Same 56 taps', b'`reference` (default in game launchers) | Same 56 taps'),
        (b'Or use `reference` or `legacy`. The launcher sets `fast` only if the caller has',
         b'Or use `fast` or `legacy`. The launcher sets `reference` only if the caller has'),
    ):
        if docdata.count(old) == 1:
            docdata = docdata.replace(old, new)
        elif docdata.count(new) != 1:
            raise ValueError('Unexpected HRTF modes guide text; cannot update safely')
    content[doc] = docdata
    if from_built and docdata != content[doc]:
        raise AssertionError('Internal documentation update error')
    content['HRTF_HOTFIX_NOTES.txt'] = NOTES
    manifest['version'] = HOTFIX_VERSION
    manifest['kind'] = 'unverified-local-runtime-hrtf-default-hotfix'
    manifest['sha256'] = {name:sha(data) for name,data in sorted(content.items()) if name != key}
    content[key] = (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode('utf-8')

    output_zip.parent.mkdir(parents=True, exist_ok=True)
    if output_zip.exists():
        raise FileExistsError(f'Will not overwrite an existing output: {output_zip}')
    try:
        with zipfile.ZipFile(output_zip, 'w', compression=zipfile.ZIP_STORED) as out:
            for rel,data in sorted(content.items()):
                info = zipfile.ZipInfo(HOTFIX_PREFIX + rel, date_time=(2026, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.compress_type = zipfile.ZIP_STORED
                info.external_attr = ((0o755 if rel.endswith('.sh') else 0o644) << 16)
                out.writestr(info, data)
        with zipfile.ZipFile(output_zip) as check:
            assert check.testzip() is None
            assert len(check.namelist()) == len(content)
            for rel in expected:
                assert b'reference' in check.read(HOTFIX_PREFIX + rel)
        print('Input provenance:', provenance)
        print('Base archive SHA-256:', whole_sha)
        print('Output ZIP:', output_zip)
        print('Output SHA-256:', sha(output_zip.read_bytes()))
        print('Source launcher defaults updated:', changed, '| Already reference:', 16-changed)
        print('Generated entries:', len(content))
        print('WARNING: 3D improvement NOT proven; five-platform release certification NOT performed.')
        return sha(output_zip.read_bytes()), len(content), changed
    except BaseException:
        output_zip.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='Official v0.9.2 runtime ZIP or locally rebuilt base ZIP')
    parser.add_argument('--output', type=Path, help='Output path, defaults next to input')
    parser.add_argument('--from-built', action='store_true', help='Accept locally built v0.9.2 package only if all launchers already use reference')
    parser.add_argument('--allow-frozen-ci-base', action='store_true', help='Only for an older archived 2026-11-04 CI candidate, not the published release')
    args = parser.parse_args()
    output = args.output or args.input.with_name('Aufake3D_v0.9.2a-HRTF-hotfix_Local_Runtime.zip')
    try:
        create(args.input, output, from_built=args.from_built, allow_frozen_ci_base=args.allow_frozen_ci_base)
    except (OSError, ValueError, KeyError, AssertionError, zipfile.BadZipFile) as exc:
        parser.exit(1, f'HOTFIX REPACK FAILED: {exc}\n')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
