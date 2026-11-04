#!/usr/bin/env python3
"""Repackage *unaltered* LLVM 19.1.7 CI compiler inputs into small archives.

The LLVM compiler is sourced solely from the existing full-SHA-pinned CI
installer action. Archive includes executable and resource SHA-256 provenance,
a copy of the LLVM licence, and no Aufake3D runtime components.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

VERSION = '19.1.7'

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()

def source_files(root, host):
    suffix='.exe' if host=='windows' else ''
    selected={}
    for tool in ('clang','lld-link'):
        path=root/'bin'/(tool+suffix)
        if not path.is_file():
            raise RuntimeError('Missing pinned compiler: '+str(path))
        selected['bin/'+tool+suffix]=path
    if host=='windows':
        # Retain any runtime DLL imported by the original Windows compiler.
        candidates=sorted((root/'bin').glob('*.dll'))
    else:
        # Keep shared LLVM libraries and dependent C++ runtime in their
        # original relative directory; never replace the compiled toolchain.
        candidates=[]
        for pattern in ('libLLVM*.so*','libclang-cpp*.so*',
                        'libc++*.so*','libunwind*.so*'):
            candidates+=sorted((root/'lib').glob(pattern))
    for path in candidates:
        if path.is_file():
            selected[path.relative_to(root).as_posix()]=path
    resources=root/'lib'/'clang'
    if not resources.is_dir():
        raise RuntimeError('Missing Clang builtin resource directory')
    for path in sorted(resources.glob('*/include/**/*')):
        if path.is_file():
            selected[path.relative_to(root).as_posix()]=path
    share=root/'share'/'clang'
    if share.is_dir():
        for path in sorted(share.rglob('*')):
            if path.is_file():
                selected[path.relative_to(root).as_posix()]=path
    license_path=next((root/n for n in ('LICENSE.TXT','LICENSE.txt','LICENSE')
                       if (root/n).is_file()),None)
    if license_path is None:
        # Official LLVM win64 NSIS installer drops its top-level licence when
        # unpacked by install-llvm-action. Use the exact upstream 19.1.7
        # tagged-source licence vendored alongside this source-only project.
        license_path = Path(__file__).resolve().parents[1] / 'ThirdParty' / 'LLVM-19.1.7-LICENSE.TXT'
        if not license_path.is_file() or 'Apache License' not in license_path.read_text(encoding='utf-8'):
            raise RuntimeError('LLVM redistribution licence is missing')
    selected['LLVM_LICENSE.TXT']=license_path
    return dict(sorted(selected.items()))

def make_archive(root, host, out):
    selected=source_files(root,host)
    manifest={'schema':1,'llvm_version':VERSION,'host':host,
              'upstream_release':'llvmorg-19.1.7',
              'source_action_sha':'ebc0426251bc40c7cd31162802432c68818ab8f0',
              'licence':'LLVM_LICENSE.TXT',
              'files_sha256':{name:digest(p) for name,p in selected.items()}}
    out.parent.mkdir(parents=True,exist_ok=True)
    with tarfile.open(out,'w:xz',format=tarfile.PAX_FORMAT) as archive:
        for name,path in selected.items():
            info=tarfile.TarInfo(name)
            info.size=path.stat().st_size
            info.uid=info.gid=0
            info.uname=info.gname=''
            info.mtime=0
            info.mode=0o755 if name.startswith('bin/') or '.so' in name else 0o644
            with path.open('rb') as f:
                archive.addfile(info,f)
        data=(json.dumps(manifest,sort_keys=True,indent=2)+'\n').encode()
        info=tarfile.TarInfo('AUFAKE3D_LLVM_PROVENANCE.json')
        info.size=len(data)
        info.uid=info.gid=0
        info.uname=info.gname=''
        info.mtime=0
        info.mode=0o644
        archive.addfile(info,io.BytesIO(data))
    return manifest

def check_archive(path,host,manifest):
    """Extract and execute the *slim* tools, not the full CI installation."""
    with tempfile.TemporaryDirectory(prefix='a3d-llvm-slim-check-') as temp:
        root=Path(temp)
        with tarfile.open(path,'r:xz') as archive:
            for member in archive.getmembers():
                if not member.isfile() or member.name.startswith('/') or '..' in Path(member.name).parts:
                    raise RuntimeError('Unsafe LLVM archive member: '+member.name)
                target=root/member.name
                target.parent.mkdir(parents=True,exist_ok=True)
                with archive.extractfile(member) as inp,target.open('wb') as dest:
                    shutil.copyfileobj(inp,dest)
                target.chmod(member.mode)
        for name,sha in manifest['files_sha256'].items():
            if digest(root/name)!=sha:
                raise RuntimeError('Repacked compiler differs: '+name)
        suffix='.exe' if host=='windows' else ''
        clang=root/'bin'/('clang'+suffix)
        lld=root/'bin'/('lld-link'+suffix)
        env=dict(os.environ)
        if host=='linux':
            env['LD_LIBRARY_PATH']=str(root/'lib')+os.pathsep+env.get('LD_LIBRARY_PATH','')
        for tool,label in ((clang,'clang version 19.1.7'),(lld,'LLD 19.1.7')):
            x=subprocess.run([str(tool),'--version'],capture_output=True,text=True,env=env)
            if x.returncode or label not in x.stdout:
                raise RuntimeError('Slim compiler cannot load: '+str(tool)+' '+x.stderr[:350])
        src=root/'probe.c'
        obj=root/'probe.obj'
        dll=root/'probe.dll'
        src.write_text('int aufake3d_llvm_probe(void){return 17;}\n',encoding='ascii')
        subprocess.run([str(clang),'-target','i686-pc-windows-msvc',
                        '-ffreestanding','-c',str(src),'-o',str(obj)],check=True,env=env)
        subprocess.run([str(lld),'/dll','/noentry','/nodefaultlib',
                        '/machine:x86','/timestamp:0',str(obj),'/out:'+str(dll)],
                       check=True,env=env)
        if dll.read_bytes()[:2]!=b'MZ':
            raise RuntimeError('Slim Clang/LLD failed Windows PE smoke check')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--llvm-root',type=Path,required=True)
    p.add_argument('--host',choices=('linux','windows'),required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    root=a.llvm_root.resolve()
    if not root.is_dir():
        raise RuntimeError('LLVM installation missing: '+str(root))
    m=make_archive(root,a.host,a.out)
    check_archive(a.out,a.host,m)
    print('SLIM LLVM SELF-TEST PASSED:',a.host,flush=True)
    print('MINIMAL LLVM ARCHIVE SHA256:',digest(a.out),flush=True)
    print('MINIMAL LLVM DOWNLOAD BYTES:',a.out.stat().st_size,flush=True)
    for name in ('bin/clang','bin/lld-link'):
        print('ORIGINAL TOOL SHA256:',name,m['files_sha256'][name+('.exe' if a.host=='windows' else '')],flush=True)

if __name__=='__main__':
    try: main()
    except (OSError,RuntimeError,subprocess.CalledProcessError,tarfile.TarError) as exc:
        print('MINIMAL LLVM PACKAGING FAILED:',exc,file=sys.stderr)
        sys.exit(1)
