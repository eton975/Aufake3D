"""General candidate tooling tests. None of these certify a retail game."""
from pathlib import Path
import json,os,shutil,subprocess,sys,tempfile,unittest,uuid
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools'))
from inspect_game_v070 import inspect_file
from scan_a3d_clients import scan,route
from stage_generic_candidate import stage
import test_alpha as alpha
pe_fixture=alpha.pe_fixture

class ScanStageTests(unittest.TestCase):
    def test_runtime_not_mistaken_for_client_and_v3_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);b=pe_fixture()+uuid.UUID('9ae07221-8ac4-11d3-b6aa-00600879f3ee').bytes_le
            (root/'a3dapi.dll').write_bytes(b);(root/'game.dll').write_bytes(b)
            report=scan(root,0);routes={i['file']:i['route'] for i in report['files']}
            self.assertEqual(routes['a3dapi.dll'],'runtime_library_not_client_evidence')
            self.assertEqual(routes['game.dll'],'a3d3_extension_detected_requires_implementation')
            self.assertFalse(report['gameplay_verified'])
    def test_scan_depth_and_legacy_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'System').mkdir();(root/'System/client.dll').write_bytes(pe_fixture()+uuid.UUID('d8f1eee1-f634-11cf-8700-00a0245d918b').bytes_le)
            self.assertEqual(scan(root,0)['files'],[])
            self.assertEqual(scan(root,1)['files'][0]['route'],'legacy_a3d1_ds3d_path_not_spatially_wrapped')
    def test_staging_preserves_game_and_identifies_conflicts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);game=root/'game';game.mkdir();(game/'example.exe').write_bytes(pe_fixture());(game/'a3dapi.dll').write_bytes(b'original')
            report=stage(game,'example.exe',root/'overlay')
            self.assertFalse(report['game_directory_modified']);self.assertEqual((game/'a3dapi.dll').read_bytes(),b'original')
            self.assertEqual(report['conflicts_back_up_before_manual_copy'][0]['file'],'a3dapi.dll')
            self.assertFalse((root/'overlay/example.exe').exists())
            self.assertTrue((root/'overlay/example.exe.manifest').exists())
    def test_unsafe_target_and_overlapping_output_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'game.exe').write_bytes(pe_fixture())
            for name in ('../game.exe','sub/game.exe','x&y.exe','x%PATH%.exe','x.dll'):
                with self.assertRaises(ValueError):stage(root,name,root.parent/'not-used-alpha-overlay')
            with self.assertRaises(ValueError):stage(root,'game.exe',root/'overlay')

@unittest.skipUnless(os.name=='nt','Native Windows generic activation')
class GenericActivationTests(alpha.ActivationTests):
    # Reuse the same genuinely compiled synthetic child, not a mock PE image.
    # Inherited tests also exercise fixed launchers against the updated engine.
    def test_generic_spaces_and_contracts(self):
        folder=self.root/'generic';folder.mkdir()
        for dll in ('a3dapi.dll','a3d.dll'):shutil.copy2(R/'win32/build'/dll,folder/dll)
        shutil.copy2(R/'experimental/build/a3d-launch.exe',folder/'a3d-launch.exe')
        shutil.copy2(self.__class__.fixture,folder/'my game.exe')
        shutil.copy2(R/'deploy-v070-alpha/HalfLife-Retail/hl.exe.manifest',folder/'my game.exe.manifest')
        env=os.environ.copy();env['A3D_ALPHA_FIXTURE_TOKEN']='inherited value'
        result=subprocess.run([str(folder/'a3d-launch.exe'),'--game','my game.exe','--','+alpha_probe','two words'],env=env,cwd=self.root,capture_output=True,text=True,timeout=25)
        self.assertEqual(result.returncode,37,result.stdout+result.stderr);self.assertIn('BROAD CONTRACT PASS',result.stdout)
        for name in ('../my game.exe','F:\\game.exe','my game.dll'):
            bad=subprocess.run([str(folder/'a3d-launch.exe'),'--game',name,'--'],capture_output=True,timeout=10)
            self.assertEqual(bad.returncode,2)
