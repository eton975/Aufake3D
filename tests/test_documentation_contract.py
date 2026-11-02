"""Documentation-only release regression: no game hardware required."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class DocumentationContract(unittest.TestCase):
    def test_core_maintainer_guides(self):
        docs=['DEVELOPER_INDEX.md','SOURCE_ARCHITECTURE.md',
              'COM_ABI_AND_LIFETIMES.md','WAVEOUT_WORKER_CONTRACT.md',
              'PCM_AND_SPATIAL_PIPELINE.md','GEOMETRY_AND_HRTF.md',
              'MILES_PROXY_AND_GAMES.md','SOURCE_FUNCTION_GUIDE.md',
              'BUILD_AND_RELEASE.md','DOCUMENTATION_POLICY.md','HISTORY_INDEX.md']
        for name in docs:
            with self.subTest(name=name):
                self.assertGreater((ROOT/'Docs'/name).stat().st_size,650)
    def test_required_contract_annotations(self):
        paths={'Source/Engine/win32/stream_winmm.inc':['Worker state machine:',
                    'Worker state machine:','stop worker before unpreparing'],
               'Source/Engine/win32/stream_core.h':['Voice registration:',
                    'bounded and no heap allocation','short,\n * nonlooping sources'],
               'Source/Engine/win32/source_probe.inc':['game write transaction',
                    'Complete the game write transaction'],
               'Source/Engine/win32/a3dapi.c':['ABI ownership map',
                    'vtable is a serialized external binary contract'],
               'Source/Alice2011_NameFix_v089/miles_selection_v089.c':['owned by OUR proxy',
                    'No game executable bytes'],}
        for rel,words in paths.items():
            text=(ROOT/rel).read_text()
            for word in words:
                with self.subTest(path=rel,phrase=word):self.assertIn(word,text)
    def test_current_engine_source_not_legacy_readme(self):
        s=(ROOT/'Source/Engine/README.md').read_text()
        self.assertIn('v0.9.0',s)
        self.assertNotIn('v0.7.0-alpha',s)
        self.assertTrue((ROOT/'Docs/History/Engine_Notes/README_V070_ORIGINAL.md').exists())
    def test_new_guide_links(self):
        import re
        names=['DEVELOPER_INDEX.md','HISTORY_INDEX.md',
               'SOURCE_ARCHITECTURE.md','BUILD_AND_RELEASE.md']
        for name in names:
            page=ROOT/'Docs'/name
            for target in re.findall(r'\[[^]\n]+\]\(([^)]+)\)',page.read_text()):
                if '://' in target or target.startswith('#'):continue
                with self.subTest(page=name,target=target):
                    self.assertTrue((page.parent/target.split('#')[0]).exists())
    def test_release_version(self):
        if (ROOT/'RELEASE_FREEZE.json').is_file():
            import json
            self.assertEqual(json.loads((ROOT/'RELEASE_FREEZE.json').read_text())['version'],'0.9.0')
if __name__=='__main__': unittest.main()
