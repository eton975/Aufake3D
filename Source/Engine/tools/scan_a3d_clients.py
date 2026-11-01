#!/usr/bin/env python3
"""Read-only scan for A3D ABI evidence in supplied game directories.

At most two levels are scanned by default (typical System/Bin/SndDrivers).
No executable code is loaded. Mere strings/GUIDs are not runtime validation.
Runtime DLLs are identified separately so an old a3dapi.dll cannot by itself
turn an unrelated game into a reported client. Reports contain no raw binaries.
"""
import argparse,json
from pathlib import Path
from inspect_game_v070 import inspect_file
RUNTIMES={'a3d.dll','a3dapi.dll'}
def route(info):
    if info['file'].casefold() in RUNTIMES:return 'runtime_library_not_client_evidence'
    ids=set(info['guid_evidence'])
    if ids&{'IID_IA3d5','IID_IA3dSource2','IID_IA3dGeom2'}:
        return 'a3d3_extension_detected_requires_implementation'
    if ids&{'IID_IA3d3','IID_IA3d4'}:return 'a3d2_com_candidate'
    if 'CLSID_A3dApi' in ids:return 'a3d2_clsid_only_requires_interface_probe'
    if ids&{'CLSID_A3dLegacy','IID_IA3d','IID_IA3d2'} or any('a3d.dll' in x.lower() for x in info.get('imports',[])):
        return 'legacy_a3d1_ds3d_path_not_spatially_wrapped'
    if info['a3d_markers']:return 'markers_only_needs_binary_analysis'
    return 'no_a3d_evidence_found'
def scan(root,depth=2):
    root=Path(root);found=[];errors=[]
    if not root.is_dir():raise ValueError('Not a game directory')
    # Do not follow junctions/symlinks into other installations or loop forever.
    def files(folder,remaining):
        for p in sorted(folder.iterdir()):
            if p.is_symlink() or (hasattr(p,'is_junction') and p.is_junction()):continue
            if p.is_file() and p.suffix.lower() in ('.exe','.dll','.m3d'):yield p
            elif p.is_dir() and remaining:yield from files(p,remaining-1)
    for i,p in enumerate(files(root,depth)):
        if i>=2048:errors.append({'error':'2048-file scan limit reached'});break
        try:
            if p.stat().st_size>128*1024*1024:
                errors.append({'file':p.relative_to(root).as_posix(),'error':'over 128 MiB; not scanned'});continue
            info=inspect_file(p);info['relative_path']=p.relative_to(root).as_posix();info['route']=route(info)
            # Include each inspected binary's metadata, including negative results.
            found.append(info)
        except (OSError,ValueError) as e:errors.append({'file':p.relative_to(root).as_posix(),'error':str(e)})
    # A candidate report describes *evidence*, not a support guarantee.
    # Keep A3D 1.x, 2.x and 3.x signals distinct; an A3D3 client may also
    # expose an A3D2 fallback, which only a game-specific test can establish.
    routes={item['route'] for item in found}
    classes={'legacy_a3d1_ds3d_path_not_spatially_wrapped':'A3D1',
             'a3d2_com_candidate':'A3D2','a3d2_clsid_only_requires_interface_probe':'A3D2',
             'a3d3_extension_detected_requires_implementation':'A3D3'}
    generations=sorted({gen for route,gen in classes.items() if route in routes})
    plugins=sorted(item['relative_path'] for item in found if item['relative_path'].lower().endswith('.m3d'))
    summary={'generations_with_static_evidence':generations,
             'miles_provider_modules_found':plugins,
             'requires_unimplemented_a3d3': 'A3D3' in generations,
             'may_require_unimplemented_a3d1_spatial':'A3D1' in generations,
             'a3d2_candidate_only':'A3D2' in generations,
             'backend_selection_required':True,
             'do_not_conclude':'Neither a GUID nor an M3D plugin is proof that the game uses that interface during gameplay.'}
    return {'wrapper_version':'0.7.1-dev','gameplay_verified':False,'scan_depth':depth,
            'summary':summary,
            'interpretation':'Static ABI clues; no support certification. An A3D3 client may have an A3D2 fallback which requires separate analysis.',
            'files':found,'errors':errors}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path);p.add_argument('--depth',type=int,choices=range(4),default=2);p.add_argument('--out',type=Path);a=p.parse_args()
    try:result=scan(a.directory,a.depth)
    except (OSError,ValueError) as e:p.exit(2,str(e)+'\n')
    text=json.dumps(result,indent=2)+'\n'
    if a.out:
        with a.out.open('x',encoding='utf-8') as f:f.write(text)
    else:print(text,end='')
if __name__=='__main__':main()
