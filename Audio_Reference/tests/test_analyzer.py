#!/usr/bin/env python3
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT/'tools'


class TestFiveWay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.base = Path(cls.temp.name)
        r = subprocess.run([sys.executable, str(TOOLS/'make_synthetic_fixture.py'), '--out', str(cls.base/'wav'), '--seconds', '14'],
                           text=True, capture_output=True)
        if r.returncode:
            raise RuntimeError(r.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def run_analysis(self, *extra, profile=None, output='report'):
        return subprocess.run([sys.executable, str(TOOLS/'analyze_five_way.py'), str(profile or (self.base/'wav'/'profile.json')),
                               '--out', str(self.base/output), *extra], capture_output=True,text=True)

    def test_five_way_writes_artifacts(self):
        p = self.run_analysis()
        self.assertEqual(p.returncode,0,p.stdout+'\n'+p.stderr)
        report = json.loads((self.base/'report'/'report.json').read_text())
        self.assertEqual(len(report['captures']),5)
        self.assertEqual(len(report['groups']['alice2000']['alignment']),3)
        self.assertEqual(len(report['groups']['alice2011']['alignment']),2)
        self.assertEqual(len(report['pairs']),4)
        self.assertTrue((self.base/'report'/'summary.csv').is_file())
        self.assertTrue((self.base/'report'/'windows.csv').is_file())
        self.assertTrue((self.base/'report'/'report.txt').is_file())
        self.assertGreater(report['captures']['alice2000_windows']['stats']['side_mid_db'],
                           report['captures']['alice2000_wine']['stats']['side_mid_db'])

    def test_auto_alignment(self):
        p = self.run_analysis()
        self.assertEqual(p.returncode, 0, p.stderr)
        report = json.loads((self.base/'report'/'report.json').read_text())
        off = report['groups']['alice2000']['alignment']['alice2000_wine']
        # Synthetic Wine recording starts 1.35 s later than synthetic Windows.
        self.assertEqual(off['method'],'auto')
        self.assertAlmostEqual(off['start_seconds']-report['groups']['alice2000']['alignment']['alice2000_windows']['start_seconds'],
                               1.35, delta=.11)
        self.assertGreater(off['envelope_similarity_to_reference'],.7)

    def test_missing_recording_rejected(self):
        prof = json.loads((self.base/'wav'/'profile.json').read_text())
        prof['captures'][-1]['file']='does_not_exist.wav'
        path = self.base/'wav'/'nohw.json'
        path.write_text(json.dumps(prof))
        p = self.run_analysis(profile=path,output='missing')
        self.assertNotEqual(p.returncode,0)

    def test_partial_allows_missing_recording(self):
        prof = json.loads((self.base/'wav'/'profile.json').read_text())
        prof['captures'][-1]['file']='does_not_exist.wav'
        path = self.base/'wav'/'partial.json'
        path.write_text(json.dumps(prof))
        p = self.run_analysis('--allow-partial',profile=path, output='partial')
        self.assertEqual(p.returncode,0,p.stderr)
        report=json.loads((self.base/'partial'/'report.json').read_text())
        self.assertEqual(len(report['captures']),4)

    def test_mixed_rates_rejected_without_resample(self):
        from scipy.io import wavfile
        import numpy as np
        prof = json.loads((self.base/'wav'/'profile.json').read_text())
        source = self.base/'wav'/'alice2000_wine.wav'
        rate, data = wavfile.read(str(source))
        newfile = self.base/'wav'/'rate44100.wav'
        # Not a physical resampling, but sufficient to test explicit consent gate.
        wavfile.write(str(newfile),44100, data)
        prof['captures'][1]['file']='rate44100.wav'
        path = self.base/'wav'/'mixed.json'
        path.write_text(json.dumps(prof))
        p = self.run_analysis(profile=path,output='bad_rates')
        self.assertNotEqual(p.returncode,0)
        self.assertIn('48000',p.stderr)

    def test_manual_starts(self):
        prof = json.loads((self.base/'wav'/'profile.json').read_text())
        prof['captures'][0]['start_seconds']=2.0
        prof['captures'][1]['start_seconds']=3.35
        path=self.base/'wav'/'manual.json'
        path.write_text(json.dumps(prof))
        p=self.run_analysis(profile=path,output='manual')
        self.assertEqual(p.returncode,0,p.stderr)
        rpt=json.loads((self.base/'manual'/'report.json').read_text())
        self.assertEqual(rpt['groups']['alice2000']['alignment']['alice2000_wine']['method'],'manual')
        self.assertEqual(rpt['captures']['alice2000_wine']['analysis_start_seconds'],3.35)


if __name__=='__main__':
    unittest.main()
