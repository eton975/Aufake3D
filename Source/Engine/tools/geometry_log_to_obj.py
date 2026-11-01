#!/usr/bin/env python3
# v0.5.0 SOURCE COMMENTARY — Engineering/research utility
# Supports repeatable data generation, audio tests, game-file analysis, or Wine
# probing. Inspect command-line arguments and preserve user-owned game files.
"""Convert A3D2 API geometry probe records to a static OBJ (diagnostic only).
Only untransformed triangles/quads; incomplete A3D list/material/dynamic geometry.
"""
from pathlib import Path
import argparse,struct

def read(log):
    mode=None;vertices=[];faces=[];skipped=0
    for line in log.splitlines():
        l=line.strip()
        if l.startswith('IA3dGeom.Begin '):
            mode=int(l.split()[-1],16);vertices=[]
        elif l.startswith('IA3dGeom.Vertex3f '):
            h=l.split()
            if len(h)!=4:continue
            try: v=tuple(struct.unpack('<f',struct.pack('<I',int(x,16)))[0] for x in h[1:])
            except (ValueError,struct.error):continue
            vertices.append(v)
        elif l=='IA3dGeom.End':
            if mode==3:
                for i in range(0,len(vertices)-2,3):faces.append((vertices[i],vertices[i+1],vertices[i+2]))
            elif mode==4:
                for i in range(0,len(vertices)-3,4):
                    a,b,c,d=vertices[i:i+4];faces.extend(((a,b,c),(a,c,d)))
            else:skipped+=len(vertices)
            mode=None;vertices=[]
    return faces,skipped

def as_obj(triangles):
    s=['# A3D2 diagnostic geometry capture; NO transforms/materials applied']
    for face in triangles:
        for x,y,z in face:s.append(f'v {x:.9g} {y:.9g} {z:.9g}')
    for i in range(0,len(triangles)*3,3):s.append(f'f {i+1} {i+2} {i+3}')
    return '\n'.join(s)+'\n'
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('log',type=Path);a.add_argument('--out',type=Path,required=True);args=a.parse_args()
    tris,skipped=read(args.log.read_text(errors='replace'));args.out.write_text(as_obj(tris))
    print(f'{len(tris)} triangles; {skipped} unhandled vertices; wrote {args.out}')
