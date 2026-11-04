"""Prevent CI LLVM toolchain downloads exhausting three-build verification."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import importlib.util

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('verify_reproducible_storage', ROOT/'scripts/verify_reproducible.py')
repro = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repro)


class LLVMStorageIsolation(unittest.TestCase):
    def test_every_installer_places_llvm_outside_checkout(self):
        workflow = (ROOT / '.github/workflows/source-ci.yml').read_text(encoding='utf-8')
        # One installer serves the three native matrix targets; one serves
        # the isolated Ubuntu 26.10 container. Both must explicitly move LLVM.
        installer = 'uses: KyleMayes/install-llvm-action@'
        self.assertEqual(workflow.count(installer), 2)
        self.assertEqual(workflow.count('directory: ${{ runner.temp }}/aufake3d-llvm'), 2)
        self.assertIn('ubuntu-24.04, ubuntu-26.04, windows-2022', workflow)
        self.assertIn('ubuntu-2610-container:', workflow)
        self.assertIn('cross-platform-byte-identity:', workflow)

    def test_real_llvm_directory_is_not_copied_to_clean_builds(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / 'checkout'
            destination = Path(td) / 'fresh'
            (source / 'llvm' / 'bin').mkdir(parents=True)
            (source / 'llvm' / 'lib').mkdir()
            (source / 'llvm' / 'bin' / 'clang').write_bytes(b'fake compiler for test')
            (source / 'llvm' / 'lib' / 'large_archive').write_bytes(b'X' * 4096)
            (source / 'scripts').mkdir()
            (source / 'scripts' / 'build.py').write_text('important source')
            (source / 'dist').mkdir()
            (source / 'dist' / 'binary.dat').write_bytes(b'output')
            with patch.object(repro, 'ROOT', source):
                repro.copy_clean_source(destination)
            self.assertFalse((destination / 'llvm').exists())
            self.assertFalse((destination / 'dist').exists())
            self.assertEqual((destination / 'scripts' / 'build.py').read_text(), 'important source')

    def test_nested_project_source_named_llvm_remains_in_copy(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / 'checkout'
            (source / 'include' / 'llvm').mkdir(parents=True)
            (source / 'include' / 'llvm' / 'api.h').write_text('real source')
            destination = Path(td) / 'fresh'
            with patch.object(repro, 'ROOT', source):
                repro.copy_clean_source(destination)
            self.assertEqual((destination / 'include' / 'llvm' / 'api.h').read_text(), 'real source')

    def test_source_folder_named_llvm_without_compiler_is_not_excluded(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / 'checkout'
            (source / 'llvm').mkdir(parents=True)
            (source / 'llvm' / 'README.md').write_text('actual source')
            destination = Path(td) / 'fresh'
            with patch.object(repro, 'ROOT', source):
                repro.copy_clean_source(destination)
            self.assertEqual((destination / 'llvm' / 'README.md').read_text(), 'actual source')


if __name__ == '__main__':
    unittest.main()
