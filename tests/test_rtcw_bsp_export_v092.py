"""Synthetic, asset-free tests for deterministic RtCW BSP v47 geometry inventory."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT/'Tools/export_rtcw_bsp_acoustics.py'
spec = importlib.util.spec_from_file_location('rtcw_exporter', MODULE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def fixture(*, version=47, typ=1, flags=0x00040000, invalid_index=False, extra_patch=False, extra_planar=False):
    shaders = struct.pack('<64sII', b'textures/test/wood', flags, 0)
    vertices = b''.join(struct.pack('<3f2f2f3f4B', *xyz,
                                     0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 1.0, 255, 255, 255, 255)
                        for xyz in ((0, 0, 0), (10, 0, 0), (0, 20, 0)))
    mesh = struct.pack('<3i', 0, 1, 99 if invalid_index else 2)
    surf = bytearray(104)
    struct.pack_into('<7i', surf, 0, 0, -1, typ, 0, 3, 0, 3)
    if extra_planar:
        surf += surf[:104]
    if extra_patch:
        other = bytearray(104)
        struct.pack_into('<7i', other, 0, 0, -1, 2, 0, 3, 0, 3)
        surf += other
    lumps = {1: shaders, 10: vertices, 11: mesh, 13: bytes(surf)}
    header = bytearray(144)
    header[:8] = b'IBSP' + struct.pack('<i', version)
    data = header
    for i in range(17):
        content = lumps.get(i, b'')
        offset = len(data)
        if content:
            data.extend(content)
        struct.pack_into('<ii', data, 8 + 8*i, offset, len(content))
    return bytes(data)


class RtCWMapExportV092(unittest.TestCase):
    def test_export_real_structure_with_material_hint(self):
        b = fixture()
        model = m.export_map(b)
        self.assertEqual(model['source_bsp_sha256'], hashlib.sha256(b).hexdigest())
        self.assertEqual(model['statistics']['exported_triangles'], 1)
        self.assertEqual(model['shaders'][0]['material_hints'], ['wood'])
        self.assertEqual(model['triangles'][0]['vertex_indices'], [0, 1, 2])
        self.assertFalse(model['geometry_complete'])
        self.assertIn(b'"source_bsp_sha256"', m.encode_map(model))
        self.assertNotIn(b'/tmp', m.encode_map(model))

    def test_identical_output_different_directories(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            b = fixture()
            outputs = []
            for folder in ('a', 'b'):
                (root/folder).mkdir()
                p = root/folder/'test.bsp'
                p.write_bytes(b)
                dest = root/folder/'test.a3dmap.json'
                result = subprocess.run([sys.executable,str(MODULE),str(p),'-o',str(dest)],
                                        capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stderr)
                outputs.append(dest.read_bytes())
                self.assertEqual(p.read_bytes(),b)
            self.assertEqual(outputs[0],outputs[1])

    def test_pk3_single_and_multiple_map_selection(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)/'maps.pk3'
            with zipfile.ZipFile(p,'w') as z:
                z.writestr('maps/a.bsp',fixture())
                z.writestr('maps/b.bsp',fixture(extra_patch=True))
            with self.assertRaisesRegex(m.BSPError,'multiple maps'):
                m.select_bsp(p,None)
            self.assertEqual(m.select_bsp(p,None,True)[1], 'maps/a.bsp\nmaps/b.bsp')
            data, label = m.select_bsp(p,'maps/b.bsp')
            self.assertEqual(label,'maps/b.bsp')
            self.assertEqual(m.export_map(data)['statistics']['skipped_surface_types']['2'],1)

    def test_triangle_soup_type(self):
        result = m.export_map(fixture(typ=3))
        self.assertEqual(result['statistics']['exported_triangles'], 1)

    def test_reject_nonfinite_coordinates(self):
        b = bytearray(fixture())
        offset = struct.unpack_from('<i', b, 8 + 10*8)[0]
        struct.pack_into('<f', b, offset, float('nan'))
        with self.assertRaisesRegex(m.BSPError, 'Non-finite'):
            m.export_map(bytes(b))

    def test_packaging_includes_tool_and_guide(self):
        source = (ROOT/'scripts/build.py').read_text()
        self.assertIn("'Tools/export_rtcw_bsp_acoustics.py'", source)
        self.assertIn("'RTCW_BSP_EXPORT_V092.md'", source)

    def test_reject_incorrect_version(self):
        with self.assertRaisesRegex(m.BSPError,'BSP v47'):
            m.export_map(fixture(version=46))

    def test_reject_bad_indices(self):
        with self.assertRaisesRegex(m.BSPError,'mesh vertex index'):
            m.export_map(fixture(invalid_index=True))

    def test_reject_truncated_or_corrupted_lump(self):
        with self.assertRaises(m.BSPError):
            m.export_map(fixture()[:10])
        bad = bytearray(fixture())
        struct.pack_into('<ii',bad,8+13*8, 4, 104)
        with self.assertRaisesRegex(m.BSPError,'overlaps BSP header'):
            m.export_map(bytes(bad))

    def test_reject_overlapping_lumps(self):
        bad = bytearray(fixture())
        shader_off = struct.unpack_from('<i', bad, 8 + 1*8)[0]
        struct.pack_into('<i', bad, 8 + 10*8, shader_off)
        with self.assertRaisesRegex(m.BSPError,'overlap'):
            m.export_map(bytes(bad))

    def test_reject_triangle_overflow_without_truncation(self):
        with self.assertRaisesRegex(m.BSPError,'exceed'):
            m.export_map(fixture(extra_planar=True),max_triangles=1)

    def test_skip_unsupported_patches_with_explicit_warning(self):
        output = m.export_map(fixture(extra_patch=True))
        self.assertEqual(output['statistics']['skipped_surface_types'],{'2':1})
        self.assertIn('curved patches',output['warning'])

    def test_output_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)/'a.bsp'
            p.write_bytes(fixture())
            out = Path(td)/'a.a3dmap.json'
            out.write_bytes(b'preexisting')
            self.assertEqual(m.main([str(p), '-o', str(out)]),2)
            self.assertEqual(out.read_bytes(),b'preexisting')

    def test_source_is_offline_only(self):
        source = MODULE.read_text()
        self.assertNotIn('ctypes',source)
        self.assertNotIn('LoadLibrary',source)
        self.assertIn('geometry_complete',source)


if __name__ == '__main__':
    unittest.main()
