"""Regression gates for ABI-compatible LLVM 19.1.7 on Ubuntu 26.x CI."""
from pathlib import Path
import os
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/source-ci.yml'
SCRIPT = ROOT / 'scripts/ci_prepare_llvm_compat.sh'


class LLVMCompatibilityTests(unittest.TestCase):
    def test_private_legacy_abi_is_pinned_and_has_no_unsafe_soname_symlink(self):
        source = SCRIPT.read_text(encoding='utf-8')
        self.assertIn('libxml2-${version}.tar.xz', source)
        self.assertIn("version='2.13.9'", source)
        self.assertIn('a2c9ae7b770da34860050c309f903221c67830c86e4a7e760692b803df95143a', source)
        self.assertIn('sha256sum --check --status', source)
        self.assertIn('-DLIBXML2_WITH_ICU=OFF', source)
        self.assertIn('-DLIBXML2_WITH_ZLIB=OFF', source)
        self.assertIn('-DLIBXML2_WITH_LZMA=OFF', source)
        self.assertIn('libxml2.so.2', source)
        self.assertNotIn('ln -s', source)
        self.assertNotIn('ln -sf', source)

    def test_llvm_dependency_resolved_before_compilation_and_ci_environment_exported(self):
        source = SCRIPT.read_text(encoding='utf-8')
        self.assertIn('ldd "$LLVM_PATH/bin/lld-link"', source)
        self.assertIn("grep -q 'not found'", source)
        self.assertIn('grep -Fq "libxml2.so.2 => $LLVM_PATH/lib/libxml2.so.2"', source)
        self.assertIn('"$LLVM_PATH/bin/lld-link" --version', source)
        self.assertIn('"$LLVM_PATH/bin/clang" --version', source)
        self.assertIn("printf 'LD_LIBRARY_PATH=%s\\n'", source)
        self.assertIn('>> "$GITHUB_ENV"', source)
        self.assertIn('install -m 0644 "$build_dir/libxml2.so.2" "$LLVM_PATH/lib/libxml2.so.2"', source)
        self.assertIn('must be built outside the source checkout', source)

    def test_linux_26_targets_both_have_preflight_and_matrix_gate_unchanged(self):
        workflow = WORKFLOW.read_text(encoding='utf-8')
        self.assertIn('ubuntu-24.04, ubuntu-26.04, windows-2022', workflow)
        self.assertIn('ubuntu:26.10@sha256:', workflow)
        self.assertEqual(workflow.count('run: bash scripts/ci_prepare_llvm_compat.sh'), 2)
        self.assertEqual(workflow.count('run: bash scripts/ci_prepare_llvm_compat.sh "$RUNNER_TEMP/aufake3d-libxml2-legacy"'), 2)
        self.assertIn("if: matrix.os == 'ubuntu-26.04'", workflow)
        self.assertIn('Prepare pinned legacy libxml2 for LLVM inside Ubuntu 26.10', workflow)
        self.assertLess(workflow.find('Prepare pinned legacy libxml2 for LLVM on Ubuntu 26.04'),
                        workflow.find('Verify LLVM and build prerequisites'))
        self.assertLess(workflow.find('Prepare pinned legacy libxml2 for LLVM inside Ubuntu 26.10'),
                        workflow.find('Confirm real Ubuntu 26.10 environment'))
        self.assertIn('cross-platform-byte-identity:', workflow)
        self.assertIn('needs: [windows-and-linux, ubuntu-2610-container]', workflow)
        for target in ('ubuntu-24.04=', 'ubuntu-26.04=', 'ubuntu-26.10='):
            self.assertIn(target, workflow)
        self.assertIn('verify_matrix_reproducibility.py', workflow)
        self.assertIn('--expected-commit "${{ github.sha }}"', workflow)

    @unittest.skipIf(os.name == "nt", "Linux CI runs the Bash-only toolchain smoke test")
    def test_shell_syntax_and_fail_closed_when_toolchain_missing(self):
        subprocess.run(['bash', '-n', str(SCRIPT)], check=True, capture_output=True)
        env = dict(os.environ)
        env.pop('LLVM_PATH', None)
        env.pop('GITHUB_ENV', None)
        # Even on a non-Ubuntu 26 host the script must fail, not mutate files.
        run = subprocess.run(['bash', str(SCRIPT), '/tmp/unneeded-libxml-compat'],
                             env=env, capture_output=True, text=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertTrue('LLVM installer must set LLVM_PATH' in run.stderr
                        or 'only for Ubuntu 26.04/26.10' in run.stderr)


if __name__ == '__main__':
    unittest.main()
