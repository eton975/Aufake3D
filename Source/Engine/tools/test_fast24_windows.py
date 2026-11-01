"""Offline regression for measured HRIR 24-tap time window. No NumPy required."""
import re
import unittest
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
class Fast24HrirTests(unittest.TestCase):
    def test_energy_window_matches_measurements(self):
        txt=(BASE/'win32/measured_hrir_data.h').read_text()
        txt=txt.split('static const signed short a3d_mhrir_48000[710][2][348] = {',1)[1].split('};',1)[0]
        directions=[]
        for line in txt.splitlines():
            if not line.strip(): continue
            vals=[int(x) for x in re.findall(r'-?\d+',line)]
            self.assertEqual(len(vals),696)
            directions.append(vals)
        self.assertEqual(len(directions),710)
        header=(BASE/'win32/hrtf_fast24_window.h').read_text()
        positions=[int(s) for s in re.findall(r'\d+',header.split('static const unsigned char a3d_mhrir_fast24_starts[710] = {',1)[1])]
        self.assertEqual(len(positions),710)
        for direction,(vals,start) in enumerate(zip(directions,positions)):
            left,right=vals[:348],vals[348:]
            energy=[x*x+y*y for x,y in zip(left,right)]
            windows=[sum(energy[i:i+24]) for i in range(348-24+1)]
            self.assertEqual(start,windows.index(max(windows)),f'direction={direction}')
            self.assertGreater(windows[start]/sum(energy),0.60)
if __name__=='__main__':unittest.main()
