#!/usr/bin/env python3
"""Run baseline contracts/installers and new alpha infrastructure checks.

SciPy is optional for this runner: when absent, explicitly skip the single
synthetic forensic resampling test. Install requirements-test.txt for a full run.
Clang/LLD, Bash and a host cc/gcc on PATH enable compilation/runtime checks.
"""
from pathlib import Path
import importlib.util
import sys
import unittest
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'tools'))
def main():
    if importlib.util.find_spec('numpy') is None:
        raise SystemExit('NumPy required: install requirements-test.txt')
    if importlib.util.find_spec('scipy') is None:
        import test_weapon_forensics_v0611 as forensic
        name='test_synthetic_source_matches_noisy_quiet_and_shifted'
        setattr(forensic.WeaponForensicsV0611,name,unittest.skip('SciPy unavailable; synthetic forensic resampling not run')(getattr(forensic.WeaponForensicsV0611,name)))
    suite=unittest.TestSuite()
    for directory in ('tools','dropin/tests','portable/tests','tests_v070'):
        sys.path.insert(0,str(R/directory))
        suite.addTests(unittest.TestLoader().discover(str(R/directory),pattern='test_*.py'))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1
if __name__=='__main__':sys.exit(main())
