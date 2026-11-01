#!/usr/bin/env python3
"""v0.7.3 development archives: clean runtime, opt-in COM helper, full source.

No script auto-registers a COM class or silently changes a game installation.
Checksum manifests and independent contents checks are generated at packaging.
"""
import hashlib,json,os,pathlib,zipfile
from security_audit_v072 import import_table,RESTRICTED,audit_runtime
R=pathlib.Path(__file__).resolve().parents[1]
OUT=pathlib.Path('/mnt/data')
EPOCH=(2026,11,1,0,0,0)
ROOT_DOC='GENERIC_ACTIVATION_V073.md'
RUN_NAMES=('a3dapi.dll','a3d.dll','a3d-direct.exe','a3d-abi-survey.exe')

def sha(b):return hashlib.sha256(b).hexdigest()
def emit(name,contents):
    contents=dict(contents)
    contents['SHA256SUMS.txt']=''.join(f'{sha(v)}  {k}\n' for k,v in sorted(contents.items())).encode()
    p=OUT/name
    with zipfile.ZipFile(p,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for path,data in sorted(contents.items()):
            info=zipfile.ZipInfo(path,EPOCH);info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=(0o100755 if path.endswith('.exe') or path.endswith('.sh') else 0o100644)<<16
            z.writestr(info,data)
    with zipfile.ZipFile(p) as z:
        assert z.testzip() is None
        for line in z.read('SHA256SUMS.txt').decode().splitlines():
            h,k=line.split('  ',1)
            assert sha(z.read(k))==h,(name,k)
    return p

def source():
    # Complete editable source modules and tests, but no generated objects,
    # historical build trees or proprietary game data.
    includes={'win32','experimental','classic2000','remaster2011','native','tools','config',
              'dropin','portable','acoustics','research','docs','release-docs','validation','tests_v070'}
    exts={'.c','.cpp','.h','.hpp','.inc','.def','.py','.md','.txt','.json','.sh','.ps1','.cmd','.yml','.yaml','.csv','.in'}
    files={}
    for f in sorted(R.rglob('*')):
        if not f.is_file() or f.is_symlink():continue
        rel=f.relative_to(R);bits=rel.parts
        if any(x in bits for x in ('build','__pycache__','.git','_dist_v071','history','bin','runtime-v072','runtime-v073','deploy-v0611','deploy-v0612','deploy-v070-alpha','deploy-v0610')):continue
        if len(bits)>1 and bits[0] not in includes:continue
        if len(bits)==1 and not(f.suffix in exts or f.name in ('VERSION','LICENSE_ACOUSTICS.txt')):continue
        if f.suffix.lower() not in exts and f.name not in ('VERSION','LICENSE_ACOUSTICS.txt'):continue
        if f.stat().st_size>9*1024*1024:continue
        files['Full_Source/'+rel.as_posix()]=f.read_bytes()
    return files

def main():
    rt={n:(R/'runtime-v073'/n).read_bytes() for n in RUN_NAMES}
    assert audit_runtime(rt)['passed']
    for n in RUN_NAMES:assert rt[n]==(R/'runtime-v072'/n).read_bytes()
    helper=(R/'runtime-v073/a3d-com-user.exe').read_bytes()
    arch,imports=import_table(helper)
    assert arch=='x86'
    assert not any(x.split('!')[-1].lower() in RESTRICTED for x in imports)
    base_doc=(R/ROOT_DOC).read_bytes()
    good={'Runtime/'+n:b for n,b in rt.items()}
    good['README_START_HERE.md']=base_doc
    std=emit('A3D_v073_Standard_Runtime.zip',good)
    optional={'Optional_COM_Setup/a3d-com-user.exe':helper,
              'README_OPTIONAL_COM.md':base_doc}
    opc=emit('A3D_v073_Optional_User_COM_Setup.zip',optional)
    src=source()
    srczip=emit('A3D_v073_Full_Source.zip',src)
    allcontents=dict(good)
    allcontents.update(optional)
    allcontents.update(src)
    allzip=emit('A3D_v073_AllInOne_GenericActivation_Dev.zip',allcontents)
    with zipfile.ZipFile(std) as z:
        bins=[n for n in z.namelist() if n.endswith(('.dll','.exe'))]
        assert sorted(bins)==sorted('Runtime/'+n for n in RUN_NAMES)
        assert not any('a3d-com-user.exe' in x or 'a3d-launch.exe' in x for x in z.namelist())
    with zipfile.ZipFile(allzip) as z:
        assert z.read('Runtime/a3dapi.dll')==rt['a3dapi.dll']
        assert z.read('Optional_COM_Setup/a3d-com-user.exe')==helper
        assert any(x=='Full_Source/win32/a3d_user_com.c' for x in z.namelist())
        assert not any(x.endswith('a3d-launch.exe') for x in z.namelist())
    for p in (std,opc,srczip,allzip):
        with zipfile.ZipFile(p) as z:count=len(z.namelist())
        print(p.name,'files:',count,'bytes:',p.stat().st_size,'sha256:',sha(p.read_bytes()))

if __name__=='__main__':main()
