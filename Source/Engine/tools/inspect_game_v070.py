#!/usr/bin/env python3
"""Read-only Half-Life/Unreal binary inventory for A3D 0.7.0-alpha.

Does not load DLLs, execute games, edit configuration or collect game assets.
Reports only file metadata, imports, selected marker strings and known GUID
offsets. These clues cannot prove a reachable A3D backend or working gameplay.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import uuid
from inspect_alice import pe_imports

GUIDS={
 'CLSID_A3dLegacy':'d8f1eee0-f634-11cf-8700-00a0245d918b',
 'IID_IA3d':'d8f1eee1-f634-11cf-8700-00a0245d918b',
 'IID_IA3d2':'fb80d1e0-98d3-11d1-90fb-006008a1f441',
 'CLSID_A3dApi':'92fa2c24-253c-11d2-90fb-006008a1f441',
 'IID_IA3d3':'c398e560-d90b-11d1-90fb-006008a1f441',
 'IID_IA3d4':'e4c40280-ccba-11d2-9dcf-00500411582f',
 'IID_IA3dGeom':'c398e561-d90b-11d1-90fb-006008a1f441',
 'IID_IA3dSource':'c398e562-d90b-11d1-90fb-006008a1f441',
 'IID_IA3dListener':'c398e563-d90b-11d1-90fb-006008a1f441',
 'IID_IA3d5':'9ae07221-8ac4-11d3-b6aa-00600879f3ee',
 'IID_IA3dGeom2':'4730c6c2-b797-11d3-a33d-00104b67d10e',
 'IID_IA3dSource2':'3d54c5c1-2a5c-11d3-a87f-00600879f3ee',
}
FILES={
 'halflife':('hl.exe','hw.dll','sw.dll','hlds.exe'),
 'unreal':('Unreal.exe','Galaxy.dll','Core.dll','Engine.dll'),
}
def find_file(folder,name):
    matches=[p for p in folder.iterdir() if p.name.casefold()==name.casefold() and p.is_file()]
    if len(matches)>1:raise ValueError('Ambiguous case variants for '+name)
    return matches[0] if matches else None

def inspect_file(path):
    data=path.read_bytes()
    result={'file':path.name,'size':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    try:
        if len(data)<64 or data[:2]!=b'MZ':raise ValueError('Missing DOS/PE header')
        off=struct.unpack_from('<I',data,60)[0]
        if off+26>len(data) or data[off:off+4]!=b'PE\0\0':raise ValueError('Invalid PE offset/signature')
        machine=struct.unpack_from('<H',data,off+4)[0]
        magic=struct.unpack_from('<H',data,off+24)[0]
        result.update(machine=hex(machine),pe32_x86=machine==0x14c and magic==0x10b,imports=pe_imports(data))
    except (ValueError,struct.error,IndexError) as error:
        result.update(pe32_x86=False,format_error=str(error))
    result['guid_evidence']={name:{'guid':value,'file_offset':data.find(uuid.UUID(value).bytes_le)} for name,value in GUIDS.items() if uuid.UUID(value).bytes_le in data}
    markers=[]
    for text in re.findall(rb'[\x20-\x7e]{4,180}',data):
        if any(term in text.lower() for term in (b'a3d',b'aureal',b's_geometry',b's_occlude')):
            markers.append(text.decode('ascii'))
    result['a3d_markers']=sorted(set(markers))[:40]
    return result

def inventory(folder,profile):
    folder=Path(folder)
    if not folder.is_dir():raise ValueError('Game directory does not exist')
    if profile=='unreal' and not find_file(folder,'Unreal.exe'):
        systems=[p for p in folder.iterdir() if p.is_dir() and p.name.casefold()=='system']
        if len(systems)==1:folder=systems[0]
    found=[];missing=[]
    for name in FILES[profile]:
        path=find_file(folder,name)
        if path:found.append(inspect_file(path))
        else:missing.append(name)
    return {'wrapper_version':'0.7.0-alpha','profile':profile,'mode':'read-only static inventory',
            'files':found,'missing_files':missing,
            'note':'Half-Life hw.dll/sw.dll are alternative engine modules; both are useful if present.',
            'gameplay_verified':False,'compatibility':'not established by static evidence'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('profile',choices=FILES)
    parser.add_argument('directory',type=Path)
    parser.add_argument('--out',type=Path)
    args=parser.parse_args()
    try:report=inventory(args.directory,args.profile)
    except (OSError,ValueError) as error:parser.exit(2,str(error)+'\n')
    text=json.dumps(report,indent=2)+'\n'
    if args.out:
        # Refuse replacement, including an accidentally selected game file.
        with args.out.open('x',encoding='utf-8') as output:output.write(text)
    else:print(text,end='')

if __name__=='__main__':main()
