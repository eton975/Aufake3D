"""No-network tests for minimal LLVM asset creation."""
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from scripts import ci_make_slim_llvm as slim

class SlimLLVM(unittest.TestCase):
    def fixture(self, root):
        for path,data in {
            'bin/clang':b'original clang','bin/lld-link':b'original lld',
            'bin/llvm-config':b'unneeded binary',
            'lib/clang/19/include/stddef.h':b'clang resource',
            'lib/libLLVM-19.so':b'dynamic library',
            'lib/static.a':b'not required',
            'LICENSE.TXT':b'Apache-2.0 with LLVM exception',
        }.items():
            p=root/path
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(data)

    def test_minimal_archive_retains_exact_compiler_and_licence(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'original'
            self.fixture(root)
            out=Path(temp)/'small.tar.xz'
            manifest=slim.make_archive(root,'linux',out)
            self.assertEqual(manifest['files_sha256']['bin/clang'],slim.digest(root/'bin/clang'))
            with tarfile.open(out,'r:xz') as z:
                names=set(z.getnames())
                self.assertIn('bin/clang',names)
                self.assertIn('bin/lld-link',names)
                self.assertIn('LLVM_LICENSE.TXT',names)
                self.assertIn('lib/clang/19/include/stddef.h',names)
                self.assertNotIn('bin/llvm-config',names)
                self.assertNotIn('lib/static.a',names)
                self.assertEqual(z.extractfile('bin/clang').read(),b'original clang')
                self.assertEqual(json.loads(z.extractfile('AUFAKE3D_LLVM_PROVENANCE.json').read()),manifest)
                self.assertTrue(all(m.mtime==0 for m in z.getmembers()))

    def test_fails_if_license_or_tool_missing(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            self.fixture(root)
            (root/'LICENSE.TXT').unlink()
            with self.assertRaisesRegex(RuntimeError,'licence'):
                slim.source_files(root,'linux')
            (root/'LICENSE.TXT').write_bytes(b'license')
            (root/'bin/lld-link').unlink()
            with self.assertRaisesRegex(RuntimeError,'lld-link'):
                slim.source_files(root,'linux')
