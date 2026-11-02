"""Source + packaging checks for experimental AU8830-reference HRTF modes.
The existence of a test never implies hardware-sample exactness or gameplay support.
"""
import csv
import json
from pathlib import Path
import sys
import unittest

# `unittest discover -s tests` can put tests/ rather than the repository root
# on sys.path, particularly with Windows Python 3.13. Import the standalone
# generator by its known on-disk location instead of assuming `tools` is a package.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Tools"))
from generate_vortex2_hrtf import generate, CSV, OUT
class Vortex2Reference(unittest.TestCase):
    def test_case_sensitive_generator_path(self):
        # Windows hides folder-name case errors that break Linux CI.
        generator = ROOT / "Tools" / "generate_vortex2_hrtf.py"
        self.assertTrue(generator.is_file(), f"Missing tracked generator: {generator}")
        build_script = (ROOT / "scripts" / "build.py").read_text()
        self.assertIn("ROOT/'Tools/generate_vortex2_hrtf.py'", build_script)

    @classmethod
    def setUpClass(cls):
        with CSV.open() as source:cls.rows=list(csv.DictReader(source))

    def test_table_matches_authored_csv(self):
        self.assertEqual(OUT.read_text(),generate())
        self.assertEqual(len(self.rows),217)
        self.assertIn('aufake_v2_coeff[217][2][56]',OUT.read_text())

    def test_pole_and_180_corrections(self):
        for el in range(-45,76,15):
            row=next(r for r in self.rows if int(r['az_deg'])==180 and int(r['el_deg'])==el)
            self.assertEqual(int(row['itd_word'],16),0)
            self.assertTrue(abs(int(row['left0']))<20000)
        self.assertEqual([(int(r['az_deg']),int(r['el_deg'])) for r in self.rows if int(r['el_deg'])==90],[(0,90)])

    def test_exact_56_tap_modes_and_logging(self):
        engine=(ROOT/'Source/Engine/win32/stream_core.h').read_text()
        core=(ROOT/'Source/Engine/win32/a3dapi.c').read_text()
        self.assertIn('for(unsigned k=0;k<56u;k++)',engine)
        self.assertIn('A3D_HRTF_MODE',core)
        self.assertIn('AU8830 BIT-EXACT UNAVAILABLE',core)
        self.assertIn('A3D.HRTF.mode',core)
        self.assertIn('2097152.0f',engine)
        self.assertIn('524288.0f',engine)
        self.assertIn('aufake_v2_delay',engine)

    def test_performance_policy(self):
        for folder in ('Alice_2000','Alice_2011_VorpalFix','Quake_III_117','Half_Life_1011',
                       'Unreal_Classic','Return_to_Castle_Wolfenstein'):
            for filename in ('RUN_AUFAKE3D_WINDOWS.cmd','RUN_AUFAKE3D_WINE.sh'):
                content=(ROOT/'packaging/Game_Kits'/folder/'COPY_TO_GAME_FOLDER'/filename).read_text()
                with self.subTest(folder=folder,filename=filename):
                    self.assertIn('A3D_HRTF_MODE',content)
                    self.assertIn('A3D_WAVEOUT_QUEUE_HEADERS',content)
                    self.assertIn('A3D_WAVEOUT_SUBBLOCKS',content)

    def test_expanded_kits_are_probes_not_false_claims(self):
        j=json.loads((ROOT/'packaging/Game_Kits/INSTALL_MAP.json').read_text())
        self.assertEqual(j['version'],'0.9.0')
        self.assertEqual(set(j['profiles']),{'alice2000','alice2011','quake3','halflife','unreal','rtcw'})
        for name in ('unreal','rtcw'):
            self.assertEqual(len(j['profiles'][name]['files']),5)
            txt=(ROOT/'packaging/Game_Kits'/j['profiles'][name]['folder']/'COPY_TO_GAME_FOLDER'/'RUN_AUFAKE3D_WINDOWS.cmd').read_text()
            self.assertIn('experimental',txt.lower())

if __name__=='__main__':unittest.main()
