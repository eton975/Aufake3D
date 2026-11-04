"""Opt-in Descent 3 outputs must never contaminate the certified v0.9.2 game runtime."""
from __future__ import annotations

import argparse
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from scripts import build_descent3_experimental as d3
from scripts import verify_reproducible as proof

ROOT = Path(__file__).resolve().parents[1]


class Descent3ExperimentalTarget(unittest.TestCase):
    def test_target_is_available_on_windows_and_linux(self):
        self.assertTrue((ROOT/'BUILD_DESCENT3_EXPERIMENTAL_LINUX.sh').is_file())
        self.assertTrue((ROOT/'BUILD_DESCENT3_EXPERIMENTAL_WINDOWS.cmd').is_file())
        self.assertTrue(d3.PROBE_SCRIPT.is_file())
        self.assertEqual(d3.DEST, ROOT/'dist/descent3')
        self.assertIn('NOT the Descent 3 game', d3.__doc__)
        self.assertIn('--audio', (ROOT/'Docs/DESCENT3_EXPERIMENTAL_BINARY_BUILD.md').read_text())

    def test_shim_object_is_not_claimed_as_game_binary(self):
        self.assertIn('standalone', d3.ADAPTER_NAME)
        self.assertNotIn('runtime', d3.ADAPTER_NAME)
        self.assertIn('AUFAKE3D_ADAPTER_STANDALONE',
                      (ROOT/'scripts/build_descent3_experimental.py').read_text())

    def test_invalid_pins_do_not_fall_back_to_system_tools(self):
        args = argparse.Namespace(clang='/missing/pinned-clang', linker='/missing/lld-link',
                                  allow_unpinned_tools=False)
        with self.assertRaisesRegex(RuntimeError, '--allow-unpinned-tools'):
            d3.tools_from_args(args)
        args.linker = None
        with self.assertRaisesRegex(RuntimeError, '--clang AND --linker'):
            d3.tools_from_args(args)

    def test_adapter_coff_validation_refuses_elf(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'adapter.obj'
            target.write_bytes(b'\x7fELF' + b'\x00'*70)
            with self.assertRaisesRegex(RuntimeError, 'COFF'):
                d3.check_coff_i386(target)
            target.write_bytes(struct.pack('<HH',0x14c,1)+b'\x00'*50)
            d3.check_coff_i386(target)

    def test_optional_probe_and_copied_dlls_do_not_change_release_pe_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            main=root/'dist/core/a3dapi.dll'
            main.parent.mkdir(parents=True)
            main.write_bytes(b'MZdummy-certified-main-core')
            for prefix in ('descent3', 'experimental-descent3'):
                probe=root/'dist'/prefix/'a3d-descent3-contract-probe.exe'
                probe.parent.mkdir(parents=True)
                probe.write_bytes(b'MZsynthetic-probe-binary')
                (probe.parent/'a3dapi.dll').write_bytes(main.read_bytes())
            hashes=proof.compiled_pe_hashes(root)
            self.assertEqual(set(hashes),{'dist/core/a3dapi.dll'})

    def test_runtime_release_recipe_does_not_package_descent3_experiment(self):
        source=(ROOT/'scripts/build.py').read_text()
        self.assertNotIn('dist/descent3', source)
        self.assertNotIn('descent3-aureal-standalone-adapter', source)
        self.assertFalse((ROOT/'packaging/Game_Kits/INSTALL_MAP.json').read_text().find('descent3-') >= 0)


if __name__ == '__main__':
    unittest.main()
