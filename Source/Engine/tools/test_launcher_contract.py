# v0.5.0 SOURCE COMMENTARY — Regression test / harness
# Exercises the release implementation or checks its ABI/packaging contract. Do not
# treat fixture success as proof of native Wine or retail-game compatibility.
import pathlib
import unittest

R = pathlib.Path(__file__).resolve().parents[1]

class LaunchContract(unittest.TestCase):
    def test_game_name_and_log_isolation(self):
        script = (R / 'tools/wine_alice_probe.sh').read_text()
        self.assertIn('Alice.exe', script)
        self.assertIn('A3D_PROBE_LOG=', script)
        self.assertIn('A3D2Lab', script)
        self.assertNotIn('cp "$here/deliverables/a3dapi.dll" "$gamedir', script)

    def test_readme_spells_out_scope(self):
        roadmap = (R / 'docs/CROSS_GAME_ROADMAP.md').read_text()
        for term in ('A3D 1.x', 'A3D 2.0', 'A3D 3.0', 'Wine', 'Alice'):
            self.assertIn(term, roadmap)

    def test_dll_supports_custom_log_path(self):
        source = (R / 'win32/a3dapi.c').read_text()
        self.assertIn('GetEnvironmentVariableA("A3D_PROBE_LOG"', source)
