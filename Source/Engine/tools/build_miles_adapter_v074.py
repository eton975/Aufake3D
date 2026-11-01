#!/usr/bin/env python3
"""Build an EXPERIMENTAL app-local Miles export-forwarding proxy for an owned MSS32.

No game executable modifications, process injection, registry edits, or anti-cheat
bypass. The original MSS32 is copied byte-for-byte into an isolated overlay under
'a3d_mss_real.dll'. Proxy forwards every named export by original ordinal and
wraps only enumeration and provider open for local COM activation + optional trace.

This is not a universal drop-in: original Miles internals, self-imports, RIB,
providers, and anti-cheat restrictions may prevent it working for a given game.
"""
from __future__ import annotations
import argparse,hashlib,json,shutil,struct,subprocess,sys,os
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
CORE=('a3d.dll','a3dapi.dll')
class PEError(ValueError): pass

def exports(path:Path,allow_forwarders:bool=False):
    b=path.read_bytes()
    def need(off,n):
        if off<0 or n<0 or off+n>len(b): raise PEError('PE bounds exceeded')
    def u16(o):need(o,2);return struct.unpack_from('<H',b,o)[0]
    def u32(o):need(o,4);return struct.unpack_from('<I',b,o)[0]
    def asc(o):
        need(o,1);end=b.find(b'\x00',o,min(len(b),o+512))
        if end<0:raise PEError('missing PE string terminator')
        return b[o:end].decode('ascii')
    if len(b)<256 or b[:2]!=b'MZ':raise PEError('not PE')
    base=u32(0x3c);need(base,24)
    if b[base:base+4]!=b'PE\x00\x00' or u16(base+4)!=0x14c:raise PEError('not x86 PE32')
    count=u16(base+6);sz=u16(base+20);opt=base+24
    need(opt,sz)
    if u16(opt)!=0x10b:raise PEError('requires PE32 optional header')
    exp_rva=u32(opt+96);exp_size=u32(opt+100)
    if not exp_rva:raise PEError('no export directory')
    sections=[]
    for i in range(count):
        o=opt+sz+i*40;need(o,40)
        sections.append((u32(o+12),max(u32(o+8),u32(o+16)),u32(o+20),u32(o+16)))
    def rva(x):
        for va,span,raw,rawsz in sections:
            if va<=x<va+span and x-va<rawsz:
                y=raw+x-va;need(y,1);return y
        raise PEError(f'unmapped export RVA {x:08x}')
    p=rva(exp_rva);need(p,40)
    ord_base,nfunc,names=u32(p+16),u32(p+20),u32(p+24)
    if not nfunc or nfunc>8192 or not names or names>8192:raise PEError('unexpected export count')
    fns=u32(p+28);names_ptr=u32(p+32);ords=u32(p+36)
    listed=[];byidx=set()
    for i in range(names):
        name=asc(rva(u32(rva(names_ptr)+4*i)))
        index=u16(rva(ords)+2*i)
        if index>=nfunc:raise PEError('export ordinal index out of range')
        address=u32(rva(fns)+index*4)
        if not address:continue
        if exp_rva<=address<exp_rva+exp_size and not allow_forwarders:raise PEError(f'forwarded export: {name}, unsupported by proxy')
        if index in byidx:raise PEError('multiple export names for one ordinal; ambiguous')
        byidx.add(index)
        if not name or any(ch not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_@$?' for ch in name):
            raise PEError('unsupported export name '+repr(name))
        listed.append((name,ord_base+index))
    live=[i for i in range(nfunc) if u32(rva(fns)+i*4)]
    if len(live)!=len(listed):raise PEError('DLL has unnamed ordinal exports; cannot safely preserve its ABI')
    if len(set(n for n,_ in listed))!=len(listed):raise PEError('duplicate names')
    return sorted(listed,key=lambda x:x[1])

def spec_def(exports):
    open_n=[name for name,_ in exports if name in ('_AIL_open_3D_provider@4','AIL_open_3D_provider')]
    enum_n=[name for name,_ in exports if name in ('_AIL_enumerate_3D_providers@12','AIL_enumerate_3D_providers')]
    if not open_n or not enum_n:
        raise PEError('not a compatible Miles 5/6 MSS32 export surface (enumerate/open not found)')
    lines=['LIBRARY mss32.dll','EXPORTS']
    for name,number in exports:
        if name in open_n:target='_a3d_intercept_open@4'
        elif name in enum_n:target='_a3d_intercept_enumerate@12'
        else:target='a3d_mss_real.'+name
        lines.append('  '+name+'='+target+' @'+str(number))
    return '\n'.join(lines)+'\n'

def build(original:Path,backend:Path,output:Path,just_validate=False):
    if not original.is_file():raise PEError('original MSS32 DLL missing')
    if original.name.lower()!='mss32.dll':raise PEError('input must be named mss32.dll')
    if not backend.is_file() or backend.name.lower()!='a3dapi.dll':raise PEError('expected compiled a3dapi.dll')
    from security_audit_v072 import import_table,RESTRICTED
    if import_table(backend.read_bytes())[0]!='x86':raise PEError('A3D runtime is not PE32')
    exp=exports(original)
    src=spec_def(exp)
    if just_validate:
        print(f'MILES_EXPORTS={len(exp)}\nOPEN_EXPORTS={sum("open_3D_provider" in n for n,_ in exp)}\nVALID=yes')
        return
    if output.exists():raise PEError(f'refusing to overwrite existing output directory: {output}')
    clang=shutil.which('clang');link=shutil.which('lld-link')
    if not clang or not link:raise PEError('clang and lld-link required; Windows user can run prebuilt tool from Linux build host')
    output.mkdir(parents=True)
    try:
        (output/'mss32.def').write_text(src,encoding='ascii')
        subprocess.run([clang,'-target','i686-pc-windows-msvc','-ffreestanding','-fno-stack-protector',
                        '-fno-builtin','-O2','-Wno-unused-function','-c',str(ROOT/'v074/miles_com_adapter.c'),
                        '-o',str(output/'adapter.obj')],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        # Stub import lib only: do not package the synthetic kernel32.dll.
        subprocess.run([link,'/dll','/noentry','/machine:x86','/def:'+str(ROOT/'v074/kernel32_v074.def'),
                        '/out:'+str(output/'kernel32-stub.dll'),'/implib:'+str(output/'kernel32.lib'),'/timestamp:0'],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        alternatives={'LoadLibraryA':4,'GetProcAddress':8,'GetModuleFileNameA':12,
                      'GetModuleHandleA':4,'GetEnvironmentVariableA':12,'CreateFileA':28,
                      'SetFilePointer':16,'WriteFile':20,'CloseHandle':4,
                      'CreateActCtxA':4,'ActivateActCtx':8,'DeactivateActCtx':8,
                      'ReleaseActCtx':4,'GetLastError':0}
        cmd=[link,'/dll','/noentry','/machine:x86','/nodefaultlib','/timestamp:0',
             '/def:'+str(output/'mss32.def'),'/out:'+str(output/'mss32.dll'),str(output/'adapter.obj'),str(output/'kernel32.lib')]
        cmd += ['/alternatename:__imp__'+n+'@'+str(k)+'=__imp__'+n for n,k in alternatives.items()]
        subprocess.run(cmd,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        # The overlay is NOT a replacement directory for the game: users explicitly
        # copy these to a BACKUP test installation's SndDrivers folder after review.
        shutil.copy2(original,output/'a3d_mss_real.dll')
        shutil.copy2(backend,output/'a3dapi.dll')
        shim=backend.parent/'a3d.dll'
        if shim.is_file():shutil.copy2(shim,output/'a3d.dll')
        shutil.copy2(ROOT/'v074/a3d-miles-local.manifest',output/'a3d-miles-local.manifest')
        for name in ('adapter.obj','kernel32-stub.dll','kernel32.lib','mss32.lib','mss32.exp','mss32.def'):
            (output/name).unlink(missing_ok=True)
        arch,imports=import_table((output/'mss32.dll').read_bytes())
        if arch!='x86':raise PEError('compiled wrong machine type')
        if any(x.split('!')[-1].lower() in RESTRICTED for x in imports):raise PEError('proxy imports remote-process modification APIs')
        fingerprint={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir() if p.is_file()}
        (output/'SHA256SUMS.txt').write_text(''.join(v+'  '+n+'\n' for n,v in sorted(fingerprint.items())),encoding='ascii')
        (output/'README_TEST_OVERLAY.txt').write_text(
            'EXPERIMENTAL v0.7.4 app-local Miles activation overlay.\n'
            'Use only in a separate BACKUP/TEST game installation; do not use multiplayer without permission.\n'
            'Source game MSS32 was not modified. All original vendor code belongs to you.\n'
            'Copy these files into the test game SndDrivers folder, after backing it up.\n'
            'The proxy must be the file loaded as mss32.dll. The original is a3d_mss_real.dll.\n'
            'Do not place the proxy alongside another mss32.dll.\n'
            'Set A3D_MILES_TRACE=1 to enable bounded a3d-v074-miles.log in the SndDrivers folder.\n'
            'A successful COM activation does not imply Alice selects the provider.\n'
            'Remove the proxy and restore the original MSS32 to revert.\n',encoding='utf-8')
        print('Built opt-in v0.7.4 overlay:',output,'export count',len(exp))
    except Exception:
        # Do not leave an apparently ready partial overlay if the build failed.
        shutil.rmtree(output,ignore_errors=True)
        raise

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--original-mss32',required=True,type=Path)
    ap.add_argument('--a3dapi',required=True,type=Path)
    ap.add_argument('--output',type=Path)
    ap.add_argument('--validate-only',action='store_true')
    a=ap.parse_args()
    if not a.validate_only and not a.output:ap.error('--output is required for building')
    try:build(a.original_mss32.resolve(),a.a3dapi.resolve(),a.output.resolve() if a.output else Path('.'),a.validate_only)
    except (PEError,subprocess.CalledProcessError) as e:raise SystemExit('ABORTED: '+str(e)+('\n'+e.stderr.decode(errors="replace") if isinstance(e,subprocess.CalledProcessError) and e.stderr else ''))
if __name__=='__main__':main()
