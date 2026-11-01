#!/usr/bin/env python3
"""Create a minimal, audit-friendly v0.7.1 development kit, no old deploy trees."""
from pathlib import Path
import zipfile, shutil, hashlib, json, tempfile, subprocess
R=Path(__file__).resolve().parents[1]
TARGET=Path('/mnt/data/A3D_v071_Generic_DevKit.zip')
SRC=Path('/mnt/data/A3D_v071_Generic_DevKit_Source.zip')
with tempfile.TemporaryDirectory(prefix='a3d-v071-pkg-') as d:
    stage=Path(d)/'A3D_v071_Generic_DevKit'
    generic=stage/'Generic-A3D2'; generic.mkdir(parents=True)
    mapping={
        'a3d-launch.exe':R/'experimental/build/a3d-launch.exe',
        'a3d-direct.exe':R/'experimental/build/a3d-direct.exe',
        'a3d-abi-survey.exe':R/'win32/build/a3d-abi-survey.exe',
    }
    # Preserve the exact v0.7.0 deployed audio DLLs, irrespective of unrelated
    # in-progress local recompilations in the shared win32/build directory.
    previous=Path('/mnt/data/A3D_v070_alpha_HalfLifeProgress_AllInOne.zip')
    with zipfile.ZipFile(previous) as old:
        base='A3D_v070_alpha_HalfLifeProgress/Binaries/Generic-A3D2/'
        for dll in ('a3dapi.dll','a3d.dll'):
            (generic/dll).write_bytes(old.read(base+dll))
    for name,path in mapping.items():
        if not path.is_file():raise FileNotFoundError(path)
        shutil.copy2(path,generic/name)
    for name in ('scan_a3d_clients.py','stage_generic_candidate.py','inspect_game_v070.py','inspect_alice.py'):
        (stage/'tools').mkdir(exist_ok=True)
        shutil.copy2(R/'tools'/name,stage/'tools'/name)
    for name in ('GENERIC_V071_README.md','GENERIC_V071_RELEASE_NOTES.md'):
        shutil.copy2(R/name,stage/name)
    shutil.copy2(R/'docs/v070/COMPATIBILITY_TARGETS.csv',stage/'CANDIDATE_RESEARCH_TARGETS.csv')
    hashes={str(p.relative_to(stage)):hashlib.sha256(p.read_bytes()).hexdigest() for p in stage.rglob('*') if p.is_file()}
    (stage/'SHA256SUMS.txt').write_text(''.join(f'{digest}  {name}\n' for name,digest in sorted(hashes.items())),encoding='utf-8')
    with zipfile.ZipFile(TARGET,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for f in sorted(stage.rglob('*')):
            if f.is_file():z.write(f,f.relative_to(stage.parent).as_posix())
    # Source patch + supporting code required to reproduce the survey; the
    # complete rest of the emulator is already in the prior v0.7.0-alpha source.
    src=Path(d)/'A3D_v071_Generic_Source';src.mkdir()
    include=[
        'win32/abi_probe_generic.c','win32/build_generic_probe.sh',
        'win32/kernel32.def','win32/ole32.def',
        'tools/scan_a3d_clients.py','tools/stage_generic_candidate.py',
        'tools/inspect_game_v070.py','tools/inspect_alice.py',
        'tools/test_generic_v071.py','tools/generate_alpha_profiles.py',
        'experimental/game_activation.c','experimental/direct_launch.c','experimental/generic_target.h',
        'tools/build_generic_v071.py',
        'experimental/native_host.h',
        'experimental/launcher_diagnostics.h','experimental/halflife_splash_compat.h',
        'experimental/halflife_splash_signature.h','native_activation.inc',
        'win32/a3d_legacy_bridge.c','win32/a3dapi.c','win32/a3dapi.def',
        'GENERIC_V071_README.md','GENERIC_V071_RELEASE_NOTES.md',
    ]
    for name in include:
        f=src/name;f.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/name,f)
    # Include code transitively needed for a3dapi.c (not full historic source).
    for f in (R/'win32').iterdir():
        if f.suffix in ('.inc','.h'):
            path=src/'win32'/f.name
            if not path.exists():shutil.copy2(f,path)
    with zipfile.ZipFile(SRC,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for f in sorted(src.rglob('*')):
            if f.is_file():z.write(f,f.relative_to(src.parent).as_posix())
for path in (TARGET,SRC):
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        print(path, path.stat().st_size,'bytes',len(z.namelist()),'files')
