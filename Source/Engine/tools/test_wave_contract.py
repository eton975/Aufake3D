# v0.5.0 SOURCE COMMENTARY — Regression test / harness
# Exercises the release implementation or checks its ABI/packaging contract. Do not
# treat fixture success as proof of native Wine or retail-game compatibility.
import pathlib,struct,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
class TestWaveProbe(unittest.TestCase):
    def test_pe32(self):
        p=(ROOT/'deliverables/a3d-miles-wave.exe').read_bytes()
        k=struct.unpack_from('<I',p,0x3c)[0]
        self.assertEqual(p[:2],b'MZ')
        self.assertEqual(p[k:k+4],b'PE\0\0')
        self.assertEqual(struct.unpack_from('<H',p,k+4)[0],0x14c)
    def test_no_playback(self):
        c=(ROOT/'win32/miles_wave.c').read_text()
        self.assertIn('_AIL_set_3D_sample_file@8',c)
        self.assertIn('_AIL_set_3D_position@16',c)
        # The legacy SILENT launcher does not opt into the new play modes.
        # The shared executable now supports explicitly requested playback.
        shell=(ROOT/'tools/wine_miles_wave.sh').read_text()
        self.assertNotIn('play-left',shell)
        self.assertNotIn('play-center',shell)
        self.assertNotIn('play-right',shell)
        self.assertIn('AIL_start_3D_sample',c)
        self.assertIn('for(i=44;i<sizeof(synthetic_wave);i++)synthetic_wave[i]=128;',c)
    def test_two_modes_and_timeout(self):
        sh=(ROOT/'tools/wine_miles_wave.sh').read_text()
        self.assertIn('run_one position\nrun_one wave\nrun_one wave16',sh)
        self.assertIn('A3D_MILES_WAVE_MODE="$mode"',sh)
        self.assertIn('timeout --signal=TERM --kill-after=5s 35s',sh)
    def test_pcm_16bit_variant(self):
        c=(ROOT/'win32/miles_wave.c').read_text()
        self.assertIn('little16(synthetic_wave16+34,16)', c)
        self.assertIn('little32(synthetic_wave16+40,4096)', c)
        self.assertIn('synthetic16_init();wave_data=synthetic_wave16', c)
    def test_pcm_header_declared(self):
        c=(ROOT/'win32/miles_wave.c').read_text()
        for t in ('little32(synthetic_wave+4,36+2048)', 'little16(synthetic_wave+20,1)', 'little16(synthetic_wave+22,1)', 'little32(synthetic_wave+24,22050)', 'little16(synthetic_wave+34,8)', 'little32(synthetic_wave+40,2048)'):
            self.assertIn(t,c)
if __name__=='__main__': unittest.main()
