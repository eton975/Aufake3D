#!/usr/bin/env python3
"""Deterministic, *offline* RtCW (IBSP v47) surface inventory/export.

This exports visual planar/triangle-soup mesh candidates, NOT a complete
collision/acoustic mesh. No native A3D COM calls and no Vortex 2 integration.
Original game/map assets are never modified or included in the distribution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import sys
import tempfile
import zipfile

BSP_VERSION = 47
LUMP_COUNT = 17
HEADER_SIZE = 8 + 8 * LUMP_COUNT
LUMP_SHADERS, LUMP_DRAWVERTS, LUMP_MESHVERTS, LUMP_SURFACES = 1, 10, 11, 13
SHADER_SIZE, DRAWVERT_SIZE, SURFACE_SIZE = 72, 44, 104
MAX_BSP_BYTES = 128 * 1024 * 1024
MAX_TRIANGLES = 250000
# RtCW surface flag names. These are *hints*, never calibrated acoustic values.
SURFACE_HINTS = (
    (0x02000000, 'carpet'), (0x00200000, 'glass'),
    (0x00040000, 'wood'), (0x00001000, 'metal'),
    (0x00100000, 'gravel'), (0x00080000, 'grass'),
    (0x00400000, 'snow'), (0x00800000, 'roof'),
    (0x01000000, 'rubble'), (0x00000040, 'ceramic'),
)


class BSPError(ValueError):
    """Unsafe, unsupported or malformed map data."""


def select_bsp(path: Path, map_name: str | None, list_only: bool = False) -> tuple[bytes, str]:
    """Read a direct BSP or a single named map from a PK3 without extraction."""
    if path.suffix.lower() == '.bsp':
        if list_only:
            return b'', path.name
        if map_name:
            raise BSPError('--map is only valid for a .pk3 archive')
        if path.stat().st_size > MAX_BSP_BYTES:
            raise BSPError('BSP exceeds the 128 MiB safety limit')
        return path.read_bytes(), path.name
    if path.suffix.lower() != '.pk3':
        raise BSPError('Input must be a .bsp map or a .pk3 map archive')
    try:
        with zipfile.ZipFile(path) as archive:
            maps = sorted((i for i in archive.infolist()
                           if not i.is_dir() and i.filename.lower().startswith('maps/')
                           and i.filename.lower().endswith('.bsp')),
                          key=lambda i: i.filename)
            if not maps:
                raise BSPError('PK3 contains no maps/*.bsp files')
            if list_only:
                return b'', '\n'.join(i.filename for i in maps)
            if map_name is None:
                if len(maps) != 1:
                    raise BSPError('PK3 has multiple maps; choose one with --map (see --list-maps)')
                selected = maps[0]
            else:
                found = [i for i in maps if i.filename == map_name]
                if len(found) != 1:
                    raise BSPError('Named map not found (case-sensitive): ' + map_name)
                selected = found[0]
            if selected.file_size > MAX_BSP_BYTES:
                raise BSPError('BSP exceeds the 128 MiB safety limit')
            with archive.open(selected) as stream:
                data = stream.read(MAX_BSP_BYTES + 1)
            if len(data) > MAX_BSP_BYTES:
                raise BSPError('Decompressed BSP exceeds the safety limit')
            return data, selected.filename
    except (zipfile.BadZipFile, RuntimeError, OSError) as exc:
        raise BSPError('Invalid/unreadable PK3 archive: ' + str(exc)) from exc


def checked_lumps(data: bytes) -> list[memoryview]:
    if len(data) < HEADER_SIZE or data[:4] != b'IBSP':
        raise BSPError('Missing or truncated IBSP header')
    version = struct.unpack_from('<i', data, 4)[0]
    if version != BSP_VERSION:
        raise BSPError(f'Expected RtCW BSP v47, found v{version}')
    regions: list[tuple[int, int, int]] = []
    lumps: list[memoryview] = []
    for i in range(LUMP_COUNT):
        offset, length = struct.unpack_from('<ii', data, 8 + i * 8)
        if offset < 0 or length < 0 or offset > len(data) or length > len(data) - offset:
            raise BSPError(f'Lump {i} has invalid offset/size')
        if length:
            if offset < HEADER_SIZE:
                raise BSPError(f'Lump {i} overlaps BSP header')
            regions.append((offset, offset + length, i))
        lumps.append(memoryview(data)[offset:offset + length])
    regions.sort()
    for left, right in zip(regions, regions[1:]):
        if right[0] < left[1]:
            raise BSPError(f'Lumps {left[2]} and {right[2]} overlap')
    for i, size in ((LUMP_SHADERS, SHADER_SIZE), (LUMP_DRAWVERTS, DRAWVERT_SIZE),
                    (LUMP_MESHVERTS, 4), (LUMP_SURFACES, SURFACE_SIZE)):
        if len(lumps[i]) % size:
            raise BSPError(f'Lump {i} is not a multiple of {size} bytes')
    return lumps


def decode_shader_name(raw: bytes) -> str:
    name = raw.split(b'\x00', 1)[0]
    if not name:
        raise BSPError('Shader entry with empty name')
    try:
        return name.decode('ascii')
    except UnicodeDecodeError as exc:
        raise BSPError('Non-ASCII shader name; refusing ambiguous decoding') from exc


def export_map(data: bytes, *, max_triangles: int = MAX_TRIANGLES) -> dict:
    if max_triangles < 1 or max_triangles > 2000000:
        raise BSPError('--max-triangles must be between 1 and 2000000')
    lumps = checked_lumps(data)
    shaders = []
    for pos in range(0, len(lumps[LUMP_SHADERS]), SHADER_SIZE):
        raw = lumps[LUMP_SHADERS][pos:pos + SHADER_SIZE]
        name = decode_shader_name(bytes(raw[:64]))
        flags, contents = struct.unpack_from('<II', raw, 64)
        hints = [hint for flag, hint in SURFACE_HINTS if flags & flag]
        shaders.append({'name': name, 'surface_flags': flags, 'content_flags': contents,
                        'material_hints': hints})

    drawverts = lumps[LUMP_DRAWVERTS]
    total_verts = len(drawverts) // DRAWVERT_SIZE
    vertices: list[list[float]] = []
    for pos in range(0, len(drawverts), DRAWVERT_SIZE):
        point = struct.unpack_from('<3f', drawverts, pos)
        if not all(math.isfinite(v) for v in point):
            raise BSPError('Non-finite draw vertex coordinate')
        vertices.append([float(x) for x in point])

    mesh = lumps[LUMP_MESHVERTS]
    surfaces = lumps[LUMP_SURFACES]
    triangles: list[dict] = []
    skipped_degenerate = 0
    skipped_types: dict[str, int] = {}
    for off in range(0, len(surfaces), SURFACE_SIZE):
        sid = off // SURFACE_SIZE
        shader, _fog, typ, first_vert, num_vert, first_index, num_index = struct.unpack_from('<7i', surfaces, off)
        if not 0 <= shader < len(shaders):
            raise BSPError(f'Surface {sid} references missing shader {shader}')
        if min(first_vert, num_vert, first_index, num_index) < 0:
            raise BSPError(f'Surface {sid} has negative vertex/index range')
        if first_vert > total_verts or num_vert > total_verts - first_vert:
            raise BSPError(f'Surface {sid} has out-of-bounds draw vertices')
        mesh_count = len(mesh) // 4
        if first_index > mesh_count or num_index > mesh_count - first_index:
            raise BSPError(f'Surface {sid} has out-of-bounds mesh indices')
        # RtCW MST_PLANAR=1, MST_PATCH=2, MST_TRIANGLE_SOUP=3.
        # Curved patches and flares require specialised tessellation; never
        # silently present them as represented acoustic geometry.
        if typ not in (1, 3):
            key = str(typ)
            skipped_types[key] = skipped_types.get(key, 0) + 1
            continue
        if num_index % 3:
            raise BSPError(f'Surface {sid}: mesh index count not divisible by three')
        for index in range(first_index, first_index + num_index, 3):
            relative = struct.unpack_from('<3i', mesh, index * 4)
            if not all(0 <= v < num_vert for v in relative):
                raise BSPError(f'Surface {sid}: mesh vertex index outside its vertex span')
            ids = [first_vert + v for v in relative]
            a, b, c = (vertices[v] for v in ids)
            e1 = [b[j] - a[j] for j in range(3)]
            e2 = [c[j] - a[j] for j in range(3)]
            cross = [e1[1]*e2[2] - e1[2]*e2[1],
                     e1[2]*e2[0] - e1[0]*e2[2],
                     e1[0]*e2[1] - e1[1]*e2[0]]
            if sum(v*v for v in cross) < 1e-12:
                skipped_degenerate += 1
                continue
            triangles.append({'vertex_indices': ids, 'shader_index': shader, 'surface_index': sid})
            if len(triangles) > max_triangles:
                raise BSPError(f'Candidate triangles exceed --max-triangles={max_triangles}; refusing to truncate')
    return {
        'format': 'aufake3d-rtcw-static-surface-candidates', 'format_version': 1,
        'source_bsp_sha256': hashlib.sha256(data).hexdigest(),
        'source_bsp_version': BSP_VERSION,
        'coordinate_units': 'original RtCW/id Tech 3 game units; not converted to metres',
        'geometry_complete': False,
        'warning': ('VISUAL PLANAR/MESH SURFACES ONLY: collision brushes, curved patches, '
                    'moving doors, correct acoustic mesh simplification and native A3D '
                    'COM submission are NOT implemented; material hints are not coefficients.'),
        'shaders': shaders, 'vertices': vertices, 'triangles': triangles,
        'statistics': {'draw_vertices': len(vertices), 'surfaces': len(surfaces)//SURFACE_SIZE,
                       'exported_triangles': len(triangles), 'skipped_degenerate': skipped_degenerate,
                       'skipped_surface_types': skipped_types},
    }


def encode_map(model: dict) -> bytes:
    # Always LF, no timestamp, path, locale or machine-specific values.
    return (json.dumps(model, ensure_ascii=True, allow_nan=False, sort_keys=True,
                       separators=(',', ':')) + '\n').encode('ascii')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='An original map BSP or PK3 containing maps/*.bsp')
    parser.add_argument('-o', '--output', type=Path, help='Output JSON acoustic candidate inventory')
    parser.add_argument('--map', dest='map_name', help='Exact internal maps/*.bsp name from PK3')
    parser.add_argument('--list-maps', action='store_true', help='List BSP entries in a PK3; write nothing')
    parser.add_argument('--max-triangles', type=int, default=MAX_TRIANGLES)
    parser.add_argument('--overwrite', action='store_true', help='Explicitly allow replacing an output JSON file')
    args = parser.parse_args(argv)
    try:
        data, selected = select_bsp(args.input, args.map_name, args.list_maps)
        if args.list_maps:
            print(selected)
            return 0
        dst = args.output or args.input.with_name(Path(selected).stem + '.a3dmap.json')
        if dst.resolve() == args.input.resolve():
            raise BSPError('Refusing to overwrite the original BSP or PK3')
        if dst.exists() and not args.overwrite:
            raise BSPError('Output already exists; pass --overwrite explicitly')
        model = export_map(data, max_triangles=args.max_triangles)
        blob = encode_map(model)
        dst.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=dst.parent, prefix='.a3dmap-', suffix='.tmp',
                                         delete=False) as tmp:
            temporary = Path(tmp.name)
            try:
                tmp.write(blob)
                tmp.flush()
                os.fsync(tmp.fileno())
            except BaseException:
                temporary.unlink(missing_ok=True)
                raise
        try:
            os.replace(temporary, dst)
        finally:
            temporary.unlink(missing_ok=True)
        print('Map:', selected)
        print('Output:', dst)
        print('Candidate triangles:', model['statistics']['exported_triangles'])
        print('Skipped surface types:', model['statistics']['skipped_surface_types'])
        print('SHA-256:', hashlib.sha256(blob).hexdigest())
        print('CAUTION: Not a complete acoustic map and not compatible with original Aureal drivers directly.')
        return 0
    except (BSPError, OSError) as exc:
        print('ERROR:', exc, file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
