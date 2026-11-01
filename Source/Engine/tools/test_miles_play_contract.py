# v0.5.0 SOURCE COMMENTARY — Regression test / harness
# Exercises the release implementation or checks its ABI/packaging contract. Do not
# treat fixture success as proof of native Wine or retail-game compatibility.
import pathlib
import struct
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent


class MilesPlayContract(unittest.TestCase):
    def test_miles_original_start_export(self):
        data = pathlib.Path('/mnt/data/mss32.dll')
        if data.is_file():
            self.assertIn(b'_AIL_start_3D_sample@4', data.read_bytes())
        source = (ROOT / 'win32/miles_wave.c').read_text()
        self.assertIn('GetProcAddress(lib,"_AIL_start_3D_sample@4")', source)

    def test_optional_explicit_mode_only(self):
        code = (ROOT / 'win32/miles_wave.c').read_text()
        for mode in ('play-left', 'play-center', 'play-right'):
            self.assertIn(mode, code)
        self.assertIn('if(isplay)', code)
        self.assertIn('if(file_result!=1)', code)
        self.assertIn('Sleep(800)', code)
        self.assertIn('TONE_SAMPLES 8820UL', code)
        self.assertIn('AIL_START_3D_SAMPLE_RETURNED=1', code)
        launcher = (ROOT / 'tools/wine_miles_play.sh').read_text()
        self.assertIn('A3D_MILES_WAVE_MODE="play-$loc"', launcher)
        self.assertIn('timeout --signal=TERM', launcher)
        self.assertIn('wine_com_probe.sh', launcher)
        self.assertNotIn('sudo ', launcher)

    def test_bounded_output_gain(self):
        renderer = (ROOT / 'win32/waveout_renderer.inc').read_text()
        math = (ROOT / 'win32/spatial_stereo.h').read_text()
        self.assertIn('float amplitude=source_gain*0.50f', math)
        self.assertIn('if(amplitude>0.50f)amplitude=0.50f;', math)
        self.assertIn('#include "stream_winmm.inc"', renderer)
        stream=(ROOT/'win32/stream_core.h').read_text()
        self.assertIn('a3d_measured_pick(', stream)
        self.assertIn('a3dmix_s16(', stream)
        self.assertIn('a3d_stereo_gains(src,lis,forward,up,coords,source_gain)', (ROOT / 'win32/binaural_approx.h').read_text())

    def test_compiled_program_pe32(self):
        exe = ROOT / 'deliverables/a3d-miles-wave.exe'
        if not exe.exists():
            self.skipTest('deliverables not built yet')
        data = exe.read_bytes()
        self.assertEqual(b'MZ', data[:2])
        offset = struct.unpack_from('<I', data, 0x3c)[0]
        self.assertEqual(b'PE\x00\x00', data[offset:offset+4])
        self.assertEqual(0x14c, struct.unpack_from('<H', data, offset+4)[0])


if __name__ == '__main__':
    unittest.main()
