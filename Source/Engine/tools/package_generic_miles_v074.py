#!/usr/bin/env python3
"""Package registration-free standard runtime, optional Miles adapter SOURCE, and full source.

The existing proprietary Miles DLL isn't uploaded or distributed. User-specific
proxy generation must have the user's licensed/original mss32.dll.
"""
from pathlib import Path
import hashlib,zipfile,json,subprocess,sys
from security_audit_v072 import import_table,RESTRICTED,audit_runtime
R=Path(__file__).resolve().parents[1]
OUT=Path('/mnt/data');STAMP=(2026,11,1,0,0,0)
STANDARD=['a3dapi.dll','a3d.dll','a3d-direct.exe','a3d-abi-survey.exe','a3d-regfree-survey.exe','a3d-regfree-survey.exe.manifest']
DOC=(R/'GENERIC_MILES_ACTIVATION_V074.md').read_bytes()
def sha(b):return hashlib.sha256(b).hexdigest()
def emit(name,items):
    entries=dict(items)
    entries['SHA256SUMS.txt']=''.join(f'{sha(v)}  {k}\n' for k,v in sorted(entries.items())).encode()
    p=OUT/name
    with zipfile.ZipFile(p,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=8) as z:
        for n,data in sorted(entries.items()):
            info=zipfile.ZipInfo(n,STAMP);info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=(0o100755 if n.endswith(('.exe','.sh','.py')) else 0o100644)<<16
            z.writestr(info,data)
    with zipfile.ZipFile(p) as z:
        assert z.testzip() is None
        for line in z.read('SHA256SUMS.txt').decode().splitlines():
            h,n=line.split('  ',1)
            assert sha(z.read(n))==h
    return p

def source():
    top={'win32','experimental','classic2000','remaster2011','native','tools','config','dropin','portable','acoustics','research','docs','release-docs','validation','tests_v070','v074'}
    exts={'.c','.cpp','.h','.hpp','.inc','.def','.py','.md','.txt','.json','.sh','.ps1','.cmd','.yaml','.yml','.csv','.in','.manifest'}
    excluded={'build','__pycache__','.git','_dist_v071','history','bin','runtime-v072','runtime-v073','runtime-v074','deploy-v0611','deploy-v0612','deploy-v070-alpha','deploy-v0610','output'}
    data={}
    for f in sorted(R.rglob('*')):
        if not f.is_file() or f.is_symlink():continue
        rel=f.relative_to(R)
        if any(s in excluded for s in rel.parts):continue
        if len(rel.parts)>1 and rel.parts[0] not in top:continue
        if f.suffix not in exts and f.name not in ('VERSION','LICENSE_ACOUSTICS.txt'):continue
        if f.stat().st_size>9*1024*1024:continue
        data['Full_Source/'+rel.as_posix()]=f.read_bytes()
    return data

def main():
    rt={n:(R/'runtime-v074'/n).read_bytes() for n in STANDARD}
    assert audit_runtime({n:rt[n] for n in STANDARD[:4]})['passed']
    for n in STANDARD[:4]:
        assert rt[n]==(R/'runtime-v073'/n).read_bytes(), 'unexpected audio/launcher regression '+n
    assert rt['a3d-regfree-survey.exe']==rt['a3d-abi-survey.exe']
    arch,imports=import_table(rt['a3d-regfree-survey.exe'])
    assert arch=='x86' and not any(f.split('!')[-1].casefold() in RESTRICTED for f in imports)
    standard={'Standard_Runtime/'+n:b for n,b in rt.items()}
    standard['README_START_HERE.md']=DOC
    std=emit('A3D_v074_Standard_Runtime.zip',standard)
    opt={'Experimental_Miles_Adapter/v074/'+n:(R/'v074'/n).read_bytes() for n in ('miles_com_adapter.c','kernel32_v074.def','a3d-miles-local.manifest')}
    for n in ('build_miles_adapter_v074.py','test_miles_adapter_v074.py','security_audit_v072.py'):
        opt['Experimental_Miles_Adapter/tools/'+n]=(R/'tools'/n).read_bytes()
    opt['Experimental_Miles_Adapter/v074/fixture/fake_mss.c']=(R/'v074/fixture/fake_mss.c').read_bytes()
    opt['Experimental_Miles_Adapter/v074/fixture/fake_mss.def']=(R/'v074/fixture/fake_mss.def').read_bytes()
    opt['Experimental_Miles_Adapter/GENERIC_MILES_ACTIVATION_V074.md']=DOC
    optional=emit('A3D_v074_Experimental_Miles_Adapter.zip',opt)
    src=source()
    source_zip=emit('A3D_v074_Full_Source.zip',src)
    combined=dict(standard);combined.update(opt);combined.update(src)
    combined['RELEASE_VERIFICATION_v074.json']=json.dumps({
        'release':'v0.7.4-dev','tests':'133 offline source-tree tests passed',
        'audio_binaries_unchanged':True,
        'gameplay_new_activation_validated':False,
        'wine_gameplay_validated':False,
        'anticheat_approved':False,
        'regfree_miles_shim_is_experimental':True,
        'vendor_mss32_bundled':False},indent=2).encode()
    everything=emit('A3D_v074_AllInOne_Generic_Miles_Dev.zip',combined)
    for archive in (std,optional,source_zip,everything):
        with zipfile.ZipFile(archive) as z:
            entries=z.namelist()
            assert not any('a3d_mss_real.dll' in x for x in entries)
            assert not any('a3d-launch.exe' in x for x in entries)
        print(archive.name,archive.stat().st_size,'bytes',len(entries),'entries','sha256',sha(archive.read_bytes()))
if __name__=='__main__':main()
