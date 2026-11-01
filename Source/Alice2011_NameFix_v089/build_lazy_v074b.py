#!/usr/bin/env python3
"""Tailored x86 Miles pass-through with first-call app-local DLL loading.

Unlike PE export-forwarder tables, real x86 thunk functions load their target
via absolute path based on THIS proxy's location, so no app-dir duplication or
external library preloading is required. No game EXE or original DLL edits.
"""
from __future__ import annotations
import hashlib, json, shutil, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'source'))
from build_miles_adapter_v074 import exports,PEError

def assembler(e):
    out=['.text','.p2align 4']
    for name,ord_ in e:
        out.extend([
          '.globl _a3d_thunk_'+str(ord_),
          '_a3d_thunk_'+str(ord_)+':',
          f'  movl _target+{ord_*4}, %eax',
          '  testl %eax, %eax',
          f'  jnz .Ljump_{ord_}',
          f'  pushl ${ord_}',
          '  calll _a3d_resolve',
          '  addl $4, %esp',
          f'.Ljump_{ord_}:',
          '  jmp *%eax',
        ])
    return '\n'.join(out)+'\n'

def build(original:Path, out:Path, hooks:bool=False):
    original=Path(original).resolve();out=Path(out).resolve()
    if not original.is_file() or original.name.lower()!='mss32.dll':raise PEError('expected genuine original named mss32.dll')
    if out.exists():raise PEError('refusing overwrite')
    e=exports(original)
    if len(e)<2:raise PEError('too few exports')
    # Dense ordinal inventory guarantees all references are valid by index.
    if [o for n,o in e]!=list(range(1,len(e)+1)):raise PEError('noncontiguous/non-1-based ordinals unsupported in this version')
    cc=shutil.which('clang');link=shutil.which('lld-link')
    if not cc or not link:raise PEError('Clang/LLD required')
    out.mkdir(parents=True)
    try:
        (out/'thunks.s').write_text(assembler(e),encoding='ascii')
        hook_targets={'_AIL_enumerate_3D_providers@12':'_a3d_hook_enumerate@12',
                      '_AIL_open_3D_provider@4':'_a3d_hook_open@4',
                      '_AIL_startup@0':'_a3d_hook_startup@0',
                      '_AIL_open_3D_listener@4':'_a3d_hook_listener@4',
                      '_AIL_close_3D_provider@4':'_a3d_hook_close@4',
                      '_AIL_open_3D_object@4':'_a3d_hook_object@4',
                      '_AIL_3D_speaker_type@4':'_a3d_hook_get_speaker@4',
                      '_AIL_set_3D_speaker_type@8':'_a3d_hook_set_speaker@8',
                      '_AIL_3D_room_type@4':'_a3d_hook_get_room@4',
                      '_AIL_set_3D_room_type@8':'_a3d_hook_set_room@8',
                      '_AIL_set_3D_provider_preference@12':'_a3d_hook_set_preference@12',
                      '_AIL_3D_provider_attribute@12':'_a3d_hook_provider_attribute@12'}
        if hooks and not set(hook_targets).issubset({n for n,o in e}):raise PEError('missing required Miles exports')
        def def_entry(n,o):
            target=hook_targets[n] if hooks and n in hook_targets else 'a3d_thunk_'+str(o)
            return f'  {n}={target} @{o}\n'
        (out/'mss32.def').write_text('LIBRARY mss32.dll\nEXPORTS\n'+''.join(def_entry(n,o) for n,o in e),encoding='ascii')
        # Keep the resolver source byte-for-byte identical to the audited source.
        shutil.copy2(ROOT/'source/miles_lazy_resolver.c',out/'resolver.c')
        comp=[cc,'-target','i686-pc-windows-msvc','-ffreestanding','-fno-stack-protector','-fno-builtin','-O2',f'-DA3D_MILES_SLOT_COUNT={len(e)+1}','-c']
        for source,dest in [(out/'thunks.s',out/'thunks.obj'),(out/'resolver.c',out/'resolver.obj')]+([(ROOT/'source/miles_selection_v074f.c',out/'hooks.obj')] if hooks else []):
            p=subprocess.run([*comp,str(source),'-o',str(dest)],capture_output=True,text=True)
            if p.returncode:raise PEError('compile failed: '+p.stderr)
        apis={'CreateActCtxA':4,'ActivateActCtx':8,'DeactivateActCtx':8,'ReleaseActCtx':4,'SetFilePointer':16,'GetModuleHandleExA':12,'GetModuleFileNameA':12,'LoadLibraryA':4,'GetProcAddress':8,
              'GetLastError':0,'FindActCtxSectionGuid':20,'InitOnceExecuteOnce':16,'GetModuleHandleA':4,'CoInitialize':4,'CoUninitialize':0,'CoCreateInstance':20,
              'GetEnvironmentVariableA':12,'CreateFileA':28,'WriteFile':20,'CloseHandle':4,'ExitProcess':4}
        (out/'kernel32.def').write_text('LIBRARY kernel32.dll\nEXPORTS\n'+''.join('  '+api+'\n' for api in apis if not api.startswith('Co')),encoding='ascii')
        (out/'ole32.def').write_text('LIBRARY ole32.dll\nEXPORTS\n'+''.join('  '+api+'\n' for api in apis if api.startswith('Co')),encoding='ascii')
        r=subprocess.run([link,'/dll','/noentry','/machine:x86','/timestamp:0','/def:'+str(out/'kernel32.def'),'/implib:'+str(out/'kernel32.lib'),'/out:'+str(out/'kernel32-stub.dll')],capture_output=True,text=True)
        if r.returncode:raise PEError('import lib failed: '+r.stderr)
        r=subprocess.run([link,'/dll','/noentry','/machine:x86','/timestamp:0','/def:'+str(out/'ole32.def'),'/implib:'+str(out/'ole32.lib'),'/out:'+str(out/'ole32-stub.dll')],capture_output=True,text=True)
        if r.returncode:raise PEError('ole32 import lib failed: '+r.stderr)
        cmd=[link,'/dll','/noentry','/machine:x86','/safeseh:no','/nodefaultlib','/timestamp:0','/def:'+str(out/'mss32.def'),'/out:'+str(out/'mss32.dll'),str(out/'thunks.obj'),str(out/'resolver.obj')]+([str(out/'hooks.obj')] if hooks else [])+[str(out/'kernel32.lib'),str(out/'ole32.lib')]
        cmd += [f'/alternatename:__imp__{name}@{argc}=__imp__{name}' for name,argc in apis.items()]
        r=subprocess.run(cmd,capture_output=True,text=True)
        if r.returncode:raise PEError('link failed: '+r.stderr)
        result=exports(out/'mss32.dll')
        if result!=e:raise PEError('proxy ABI different from original')
        text=subprocess.check_output(['llvm-objdump','-p',str(out/'mss32.dll')],text=True)
        if 'a3d_mss_real.' in text:raise PEError('proxy must contain NO PE forwarder strings')
        shutil.copy2(original,out/'a3d_mss_real.dll')
        meta={'version':'v0.7.4f' if hooks else 'v0.7.4b','original_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'export_count':len(e),'exports':[list(x) for x in e]}
        (out/'export_inventory.json').write_text(json.dumps(meta,indent=2)+'\n')
        # Source files are shipped separately; archive only runtime necessities.
        for p in list(out.iterdir()):
            if p.name not in ('mss32.dll','a3d_mss_real.dll','export_inventory.json'):p.unlink()
        print('Built lazy Miles '+('activation/trace' if hooks else 'pass-through')+':',len(e),'exports; app-local load by path; no DLL forwarders')
    except BaseException:
        shutil.rmtree(out,ignore_errors=True)
        raise
if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser();a.add_argument('--original',required=True,type=Path);a.add_argument('--output',required=True,type=Path);a.add_argument('--hooks',action='store_true');v=a.parse_args()
    try:build(v.original,v.output,v.hooks)
    except PEError as e:raise SystemExit('ABORTED: '+str(e))
