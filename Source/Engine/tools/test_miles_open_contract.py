# v0.5.0 SOURCE COMMENTARY — Regression test / harness
# Exercises the release implementation or checks its ABI/packaging contract. Do not
# treat fixture success as proof of native Wine or retail-game compatibility.
"""Build/ABI contracts for v0.2.0's standalone, non-invasive Miles open test.
This deliberately DOES NOT claim the Wine runtime test has executed."""
import pathlib
import struct
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class TestOpenProbe(unittest.TestCase):
    def test_win32_binary(self):
        data = (ROOT / "deliverables/a3d-miles-open.exe").read_bytes()
        self.assertEqual(data[:2], b"MZ")
        pe_offset = struct.unpack_from("<I", data, 0x3c)[0]
        self.assertEqual(data[pe_offset:pe_offset + 4], b"PE\x00\x00")
        self.assertEqual(struct.unpack_from("<H", data, pe_offset + 4)[0], 0x14c)

    def test_open_and_close_exports(self):
        src = (ROOT / "win32/miles_open.c").read_text()
        for symbol in ("_AIL_open_3D_provider@4", "_AIL_close_3D_provider@4",
                       "_AIL_enumerate_3D_providers@12", "_AIL_last_error@0"):
            self.assertIn(symbol, src)
        self.assertIn("result==0", src)

    def test_control_and_target_process_isolation(self):
        shell = (ROOT / "tools/wine_miles_open.sh").read_text()
        self.assertIn("run_one fast2d\nrun_one a3d2", shell)
        self.assertIn('timeout --signal=TERM --kill-after=5s 35s', shell)
        self.assertIn('WINEPREFIX=', shell)
        self.assertIn("A3D_PROBE_LOG", shell)
        self.assertNotIn('wine "$(basename "$exe")"', shell)

    def test_no_original_dlls_bundled(self):
        names = {p.name.lower() for p in (ROOT / "deliverables").iterdir()}
        self.assertNotIn("mss32.dll", names)
        self.assertNotIn("mssa3d2.m3d", names)


if __name__ == "__main__":
    unittest.main()
