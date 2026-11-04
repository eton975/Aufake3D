"""Structure/ABI regressions for the game-free A3D2 Descent 3 probe."""
import re
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'Source/Engine/win32'

class Descent3ContractProbe(unittest.TestCase):
    def test_direct_factory_no_registry_or_binary_patch(self):
        s=(SRC/'descent3_contract_probe.c').read_text()
        self.assertIn('DllGetClassObject',s)
        self.assertIn('LoadLibraryA("a3dapi.dll")',s)
        self.assertIn('Factory.CreateInstance(IA3d4)',s)
        self.assertNotIn('CoCreateInstance(',s)
        for forbidden in ('WriteProcessMemory','VirtualProtectEx','RegSetValue','CreateRemoteThread'):
            self.assertNotIn(forbidden,s)

    def test_source_abi_slots_from_real_vtable(self):
        game=(SRC/'descent3_contract_probe.c').read_text()
        engine=(SRC/'source_probe.inc').read_text()
        names={int(slot):name for name,slot in re.findall(r'\(void\*\)(sr_\w+)\s*/\*\s*(\d+)\s',engine)}
        expected={5:'sr_allocwave',7:'sr_setformat',11:'sr_lock',12:'sr_unlock',
                  13:'sr_play',14:'sr_stop',20:'sr_setpos',32:'sr_setvel',38:'sr_setminmax'}
        for slot,name in expected.items():
            self.assertEqual(names[slot],name)
            self.assertRegex(game,rf'CALL\(src,{slot},')

    def test_geometry_and_material_abi(self):
        probe=(SRC/'descent3_contract_probe.c').read_text()
        geom=(SRC/'geom_trace.inc').read_text()
        self.assertIn('A3D_QUADS',probe)
        self.assertIn('A3D_1ST_REFLECTIONS', (ROOT/'Docs/DESCENT3_A3D_API_PROBE.md').read_text())
        for symbol in ('g_NewMaterial','g_BindMaterial','g_NewList','g_Begin','g_Vertex3f','g_End'):
            self.assertIn('(void*)'+symbol,geom)
        for val in ('0.2f,0.5f,0.9f,0.8f','1.0f,0.3f,0.8f,0.7f','0.1f,0.1f,0.95f,0.85f'):
            self.assertIn(val,probe)
        self.assertIn('r!=3',probe)

    def test_audio_not_automatic(self):
        s=(SRC/'descent3_contract_probe.c').read_text()
        self.assertIn('if(audio)',s)
        self.assertIn('flag_audio()',s)
        self.assertIn('Source playback skipped',s)

    def test_build_is_separate_and_double_verified(self):
        s=(ROOT/'scripts/build_descent3_contract_probe.py').read_text()
        self.assertIn('if a != b',s)
        self.assertIn('i686-pc-windows-msvc',s)
        self.assertIn('experimental-descent3',s)
        self.assertIn('/timestamp:0',s)
        self.assertNotIn('scripts/build.py',s)

if __name__=='__main__': unittest.main()
