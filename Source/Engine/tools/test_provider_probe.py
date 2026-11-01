# v0.5.0 SOURCE COMMENTARY — Regression test / harness
# Exercises the release implementation or checks its ABI/packaging contract. Do not
# treat fixture success as proof of native Wine or retail-game compatibility.
import pathlib, unittest
P = pathlib.Path(__file__).resolve().parents[1]
class ProviderScript(unittest.TestCase):
    def test_safe_scope_and_logging(self):
        x=(P/'tools/wine_provider_probe.sh').read_text()
        for k in ["Aureal A3D 2.0 (TM)", "+set s_milesdriver", "+set logfile 1", "restore_console", "a3d-shim-calls.log", "a3d-detection-patch-status.txt", "WINEDEBUG='-all,+loaddll,+ole,+reg'"]:
            self.assertIn(k,x)
        self.assertNotIn('sudo ',x)
        self.assertNotIn('setpci',x)
    def test_real_provider_name_in_original_miles_binary(self):
        b=pathlib.Path('/mnt/data/mssa3d2.m3d')
        if b.exists(): self.assertIn(b'Aureal A3D 2.0 (TM)',b.read_bytes())
