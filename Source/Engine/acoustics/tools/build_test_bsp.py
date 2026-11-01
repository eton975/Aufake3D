#!/usr/bin/env python3
# v0.5.0 SOURCE COMMENTARY — Engineering/research utility
# Supports repeatable data generation, audio tests, game-file analysis, or Wine
# probing. Inspect command-line arguments and preserve user-owned game files.
"""Construct a tiny public-domain IBSP 46 test fixture (triangle + curved patch)."""
import struct
from pathlib import Path

def vertex(x,y,z):
    return struct.pack('<3f2f2f3f4B', x,y,z, 0,0, 0,0, 0,0,1, 255,255,255,255)

def face(kind, base, count, mesh_count=0, patch=(0,0)):
    fields = [0, -1, kind, base, count, 0, mesh_count, -1]
    data = struct.pack('<8i', *fields)
    data += b'\0'*64
    data += struct.pack('<2i', *patch)
    assert len(data)==104
    return data

shaders = b'textures/stone' + b'\0'*(64-len('textures/stone')) + struct.pack('<2i',0,0)
verts = [vertex(0,0,0),vertex(10,0,0),vertex(0,10,0)]
for y in range(3):
    for x in range(3):
        verts.append(vertex(x*10, y*10, 4 if x==1 and y==1 else 0))
vertices = b''.join(verts)
indices = struct.pack('<3i',0,1,2)
faces = face(1,0,3,3) + face(2,3,9,0,(3,3))
lumps={1:shaders,10:vertices,11:indices,13:faces}
off=144
headers=[];body=b''
for index in range(17):
    content=lumps.get(index,b'')
    headers.append(struct.pack('<ii',off,len(content)))
    body+=content
    off+=len(content)
result=b'IBSP'+struct.pack('<i',46)+b''.join(headers)+body
file=Path(__file__).resolve().parents[1]/'samples'/'synthetic_ibsp46.bsp'
file.write_bytes(result)
print(f'Created {file} ({len(result)} bytes)')
