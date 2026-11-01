# v0.5.0 SOURCE COMMENTARY — Regression test / harness
# Exercises the release implementation or checks its ABI/packaging contract. Do not
# treat fixture success as proof of native Wine or retail-game compatibility.
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class BinauralLaunch(unittest.TestCase):
 def test_front_back_up(self):
  c=(ROOT/'win32/miles_wave.c').read_text()
  s=(ROOT/'tools/wine_binaural_probe.sh').read_text()
  self.assertIn('for loc in front back up; do',s)
  for label in ('play-front','play-back','play-up'): self.assertIn(label,c)
  self.assertIn('WINEPREFIX=',s)
  self.assertIn('timeout --signal=TERM',s)
  self.assertNotIn('sudo ',s)
if __name__=='__main__':unittest.main()
