import importlib.util
from pathlib import Path
import tempfile
import unittest
import wave

import numpy as np
from scipy.io import wavfile

MODULE_FILE = Path(__file__).resolve().parents[1]/'tools'/'analyze_five_way.py'
spec = importlib.util.spec_from_file_location('five_way_analyzer', MODULE_FILE)
analyzer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analyzer)


class TestAudioFormats(unittest.TestCase):
    def test_float32_wav(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'float32.wav'
            audio = np.tile(np.array([[.25,-.125]],dtype=np.float32),(96000,1))
            wavfile.write(str(path), 48000, audio)
            rate, value = analyzer.read_audio(path)
            self.assertEqual(rate,48000)
            self.assertAlmostEqual(float(value[2,0]),.25,places=5)
            self.assertAlmostEqual(float(value[2,1]),-.125,places=5)

    def test_24bit_pcm_wav_left_justification(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'pcm24.wav'
            vals = (4194304,-2097152)*96000  # +0.5, -0.25 in signed 24-bit PCM
            raw = b''.join(v.to_bytes(3, byteorder='little', signed=True) for v in vals)
            with wave.open(str(path),'wb') as f:
                f.setnchannels(2)
                f.setsampwidth(3)
                f.setframerate(48000)
                f.writeframes(raw)
            rate, data=analyzer.read_audio(path)
            self.assertEqual(rate,48000)
            self.assertAlmostEqual(float(data[0,0]),.5,places=5)
            self.assertAlmostEqual(float(data[0,1]),-.25,places=5)


if __name__=='__main__':
    unittest.main()
