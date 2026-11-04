"""v0.9.2 documentation must remain current, linked and safe for players."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT/'Docs'
CURRENT = (
    ROOT/'README.md', ROOT/'CHANGELOG.md', DOCS/'README.md',
    DOCS/'INSTALLATION.md', DOCS/'BUILD_AND_RELEASE.md',
    DOCS/'COMPATIBILITY.md', DOCS/'TROUBLESHOOTING.md',
    DOCS/'DESCENT3_PUBLIC_RELEASE.md', DOCS/'DEVELOPER_INDEX.md',
)


class DocsConsolidation(unittest.TestCase):
    def test_current_docs_explain_build_output(self):
        for p in CURRENT:
            with self.subTest(page=p.name):
                self.assertTrue(p.is_file(), str(p))
                self.assertIn('dist/', p.read_text(encoding='utf-8'))
        self.assertIn('Aufake3D_v0.9.2_Descent3_Experimental_Win32.zip',
                      (ROOT/'README.md').read_text())

    def test_alice_miles_original_preservation_not_lost(self):
        content = (DOCS/'INSTALLATION.md').read_text()
        self.assertIn('14fb663762695a02e06b144c487254b08163185fa009efb32df733882cd570de', content)
        self.assertIn('08bcbe4b549633b24c90a1ab36bf516bd8873432c68b37248c98ee4225506e50', content)
        self.assertIn('a3d_mss_real.dll', content)
        self.assertIn('SndDrivers', content)

    def test_historical_root_release_notes_archived_not_deleted(self):
        for version in ('V0814_RC1', 'V0815', 'V0816', 'V0818', 'V090', 'V091', 'V092'):
            name = f'RELEASE_NOTES_{version}.md'
            with self.subTest(name=name):
                self.assertFalse((ROOT/name).exists())
                self.assertTrue((DOCS/'History/Release_Notes'/name).is_file())

    def test_legacy_build_documentation_retained_in_history(self):
        self.assertTrue((DOCS/'History/Superseded_Guides/DOCS_ONE_CLICK_BUILD_PRE_CONSOLIDATION.md').is_file())
        self.assertTrue((DOCS/'History/Superseded_Guides/DOCS_EASY_INSTALL_WINDOWS_PRE_CONSOLIDATION.md').is_file())
        self.assertTrue((DOCS/'History/Superseded_Guides/DOCS_MANUAL_INSTALLATION_PRE_CONSOLIDATION.md').is_file())

    def test_changed_markdown_links_resolve_in_checkout(self):
        pages = list(CURRENT) + [DOCS/'HISTORY_INDEX.md',DOCS/'ONE_CLICK_BUILD.md',
                                 DOCS/'MANUAL_INSTALLATION.md', DOCS/'EASY_INSTALL_WINDOWS.md',
                                 DOCS/'RELEASE_NOTES.md', ROOT/'BUILDING.md']
        for page in pages:
            for target in re.findall(r'\[[^]\n]+\]\(([^)]+)\)', page.read_text(encoding='utf-8')):
                if '://' in target or target.startswith('#'):
                    continue
                dest = target.split('#',1)[0]
                with self.subTest(page=str(page.relative_to(ROOT)), target=target):
                    self.assertTrue((page.parent/dest).exists(), dest)

    def test_release_docs_are_in_actual_build_packaging(self):
        builder = (ROOT/'scripts/build.py').read_text()
        for name in ('INSTALLATION.md', 'COMPATIBILITY.md', 'TROUBLESHOOTING.md',
                     'DESCENT3_PUBLIC_RELEASE.md'):
            self.assertIn(f"'{name}'", builder)
        self.assertIn('package_descent3_release.py', builder)


if __name__ == '__main__':
    unittest.main()
