"""Security packaging contract: never confuse audit with malware clearance."""
from pathlib import Path
import unittest, hashlib
ROOT=Path(__file__).resolve().parents[1]
class SecurityPackaging(unittest.TestCase):
    def test_selftest_source_stays_available(self):
        self.assertTrue((ROOT/'Source/Engine/win32/selftest.c').is_file())
        self.assertTrue((ROOT/'Source/Engine/windows-build-recipe.json').is_file())
    def test_legacy_probe_build_script_retained(self):
        self.assertTrue((ROOT/'Source/Engine/portable/build_legacy_probe.sh').is_file())
    def test_advisory_names_reported_components(self):
        s=(ROOT/'Docs/SECURITY_REVIEW_V0814_RC1.md').read_text(encoding='utf-8')
        for name in ['a3d-selftest.exe','a3dapi.dll','a3d.dll','mss32.dll','build_legacy_probe.sh','NOT antivirus-cleared']:
            with self.subTest(name=name): self.assertIn(name,s)
    def test_frozen_core_hash_metadata(self):
        import json
        m=json.loads((ROOT/'CORE_BINARY_HASHES.json').read_text())
        self.assertIn('a3dapi.dll',str(m))
    def test_optional_runtime_binary_not_published(self):
        if (ROOT/'Game_Kits').is_dir():
            self.assertFalse((ROOT/'Extras/Diagnostics/a3d-selftest.exe').exists())
            self.assertEqual(hashlib.sha256((ROOT/'Universal_Core/a3dapi.dll').read_bytes()).hexdigest(),'2e6f500e8d86b641d702f21cbfa2662f6327e15c794af7c07745c24cba8e8db2')
            self.assertEqual(hashlib.sha256((ROOT/'Game_Kits/Alice_2011_VorpalFix/COPY_TO_GAME_FOLDER/mss32.dll').read_bytes()).hexdigest(),'8bc83f25b228849693ef187877388f917d7a5e3475f7db5e0cf9fa9b708426b8')
if __name__=='__main__': unittest.main()
