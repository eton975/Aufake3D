#!/usr/bin/env python3
"""Build the v0.8.9 app-local Miles proxy using only its independently published
ABI export-name/ordinal surface and Aufake3D source. Does not read, copy or
include a Miles vendor binary; the user must provide that separately at runtime.
"""
from __future__ import annotations
import argparse, json, hashlib, pathlib, shutil, subprocess, sys
ROOT=pathlib.Path(__file__).resolve().parents[2]
PROXY_SRC=ROOT/'Source'/'Alice2011_NameFix_v089'
sys.path.insert(0,str(PROXY_SRC))
from build_scoped_proxy_v089 import assembler
from build_miles_adapter_v074 import exports

def run(argv):
    subprocess.run(argv,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

def build(export_json:pathlib.Path, output:pathlib.Path, strict_hash:bool=False):
    j=json.loads(export_json.read_text())
    records=j['exports']
    e=[(x[0],int(x[1])) for x in records]
    if len(e)!=331 or [o for _,o in e]!=list(range(1,332)) or len(set(n for n,_ in e))!=331:
        raise ValueError('expected exactly 331 unique names with ordinals 1-331')
    if any(not n or not all(c.isalnum() or c in '_@$?' for c in n) for n,_ in e):
        raise ValueError('export name validation failed')
    cc=shutil.which('clang');ld=shutil.which('lld-link')
    if not cc or not ld:raise RuntimeError('clang and lld-link required')
    output.mkdir(parents=True,exist_ok=False)
    (output/'thunks.s').write_text(assembler(e),encoding='ascii')
    targets={'_AIL_enumerate_3D_providers@12':'_a3d_hook_enumerate@12',
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
    if not set(targets).issubset({n for n,_ in e}):raise ValueError('required hooks missing')
    (output/'mss32.def').write_text('LIBRARY mss32.dll\nEXPORTS\n'+''.join(
        f'  {n}={targets.get(n,"a3d_thunk_"+str(o))} @{o}\n' for n,o in e))
    comp=[cc,'-target','i686-pc-windows-msvc','-ffreestanding','-fno-stack-protector',
          '-fno-builtin','-O2','-DA3D_MILES_SLOT_COUNT=332','-c']
    for src,dst in ((output/'thunks.s',output/'thunks.obj'),
                    (PROXY_SRC/'miles_lazy_resolver.c',output/'resolver.obj'),
                    (PROXY_SRC/'miles_selection_v089.c',output/'hooks.obj')):
        run([*comp,str(src),'-o',str(dst)])
    apis={'CreateActCtxA':4,'ActivateActCtx':8,'DeactivateActCtx':8,'ReleaseActCtx':4,
          'SetFilePointer':16,'GetModuleHandleExA':12,'GetModuleFileNameA':12,
          'LoadLibraryA':4,'GetProcAddress':8,'GetLastError':0,'GetCommandLineA':0,
          'FindActCtxSectionGuid':20,'InitOnceExecuteOnce':16,'GetModuleHandleA':4,
          'CoInitialize':4,'CoUninitialize':0,'CoCreateInstance':20,
          'GetEnvironmentVariableA':12,'CreateFileA':28,'WriteFile':20,
          'CloseHandle':4,'ExitProcess':4}
    for module,pred in (('kernel32',lambda k:not k.startswith('Co')),
                        ('ole32',lambda k:k.startswith('Co'))):
        (output/f'{module}.def').write_text(f'LIBRARY {module}.dll\nEXPORTS\n'+''.join(
            '  '+k+'\n' for k in apis if pred(k)))
        run([ld,'/dll','/noentry','/machine:x86','/timestamp:0',
             '/def:'+str(output/f'{module}.def'),'/implib:'+str(output/f'{module}.lib'),
             '/out:'+str(output/f'{module}-stub.dll')])
    cmd=[ld,'/dll','/noentry','/machine:x86','/safeseh:no','/nodefaultlib',
         '/timestamp:0','/def:'+str(output/'mss32.def'),'/out:'+str(output/'mss32.dll'),
         *(str(output/n) for n in ('thunks.obj','resolver.obj','hooks.obj','kernel32.lib','ole32.lib'))]
    cmd += [f'/alternatename:__imp__{n}@{sz}=__imp__{n}' for n,sz in apis.items()]
    run(cmd)
    if exports(output/'mss32.dll')!=e:raise RuntimeError('ABI changed')
    digest = hashlib.sha256((output/'mss32.dll').read_bytes()).hexdigest()
    expected = j['frozen_proxy_sha256']

    if digest != expected:
        message = f'Proxy hash differs: {digest} vs frozen {expected}'
        if strict_hash:
            raise RuntimeError(message)
        print('WARNING:', message, file=sys.stderr)
        print('331-export ABI verified; runtime behaviour not yet verified.',
              file=sys.stderr)

    for p in output.iterdir():
        if p.name != 'mss32.dll':
            p.unlink()

    print('Miles proxy build completed:', digest, 'exports', len(e))

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--exports',type=pathlib.Path,default=PROXY_SRC/'MILES_EXPORT_SURFACE_331.json')
    ap.add_argument('--output',required=True,type=pathlib.Path)
    ap.add_argument(
        '--strict-frozen-hash',
        action='store_true',
        help='Require exact binary identity with the tested reference'
    )
    args = ap.parse_args()
    build(args.exports.resolve(), args.output.resolve(), args.strict_frozen_hash)
