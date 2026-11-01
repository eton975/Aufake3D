#!/usr/bin/env python3
# v0.5.0 SOURCE COMMENTARY — Engineering/research utility
# Supports repeatable data generation, audio tests, game-file analysis, or Wine
# probing. Inspect command-line arguments and preserve user-owned game files.
"""Generate synthetic Alice-style FAKK 42 BSP for structural parser regression tests."""
import struct
from pathlib import Path

def vertex(x,y,z):
    return struct.pack('<3f2f2f3f4B', x,y,z, 0,0, 0,0, 0,0,1, 255,255,255,255)

def surface(kind, base, count, first_index, num_indices, patch=(0,0)):
    # 12 ints, origin vec3, 3 lightmap vectors, patch width and height, subdivision float.
    result=struct.pack('<12i',0,-1,kind,base,count,first_index,num_indices,-1,0,0,0,0)
    result+=b'\0'*48
    result+=struct.pack('<2if', *patch, 8.0)
    assert len(result)==108
    return result

shaders=(b'textures/stone'+b'\0'*(64-len('textures/stone'))+struct.pack('<3i',0,1,4))
verts=[vertex(0,0,0),vertex(10,0,0),vertex(0,10,0)]
for y in range(3):
    for x in range(3):
        verts.append(vertex(x*10,y*10,5 if x==1 and y==1 else 0))
lumps={0:shaders, 3:surface(1,0,3,0,3)+surface(2,3,9,0,0,(3,3)),
       4:b''.join(verts),5:struct.pack('<3i',0,1,2)}
offset=172
headers=[];body=b''
for i in range(20):
    chunk=lumps.get(i,b'')
    headers.append(struct.pack('<ii',offset,len(chunk)))
    body+=chunk
    offset+=len(chunk)
output=b'FAKK'+struct.pack('<ii',42,0xabcdef & 0x7fffffff)+b''.join(headers)+body
path=Path(__file__).resolve().parents[1]/'samples'/'synthetic_alice_fakk42.bsp'
path.write_bytes(output)
print('Created',path,len(output),'bytes')
