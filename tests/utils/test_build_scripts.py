"""Build-script checks without CANN: python tests/utils/test_build_scripts.py."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class BuildScriptTests(unittest.TestCase):
    def run_script(self, script, build_exit_code):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copy(ROOT / script, root / script)
            (root / 'deep_ep').mkdir()
            (root / 'bin').mkdir()
            # Leave an extension behind even on failure, so develop.sh must not
            # mistake a partial build for success just because it finds a .so.
            python = root / 'bin/python'
            python.write_text('#!/bin/bash\nmkdir -p build/lib\ntouch build/lib/_C.so\n'
                              f'exit {build_exit_code}\n')
            python.chmod(0o755)
            env = dict(os.environ, PATH=f"{root / 'bin'}:{os.environ['PATH']}")
            result = subprocess.run(['bash', str(root / script)], cwd=root,
                                    env=env, capture_output=True, text=True)
            return result, (root / 'deep_ep/_C.so').is_symlink()

    def test_build_failure_is_propagated(self):
        for script in ('build.sh', 'develop.sh'):
            with self.subTest(script=script):
                result, linked = self.run_script(script, 17)
                self.assertEqual(result.returncode, 17)
                self.assertFalse(linked)
                self.assertNotIn('Success:', result.stdout)

    def test_successful_builds(self):
        for script in ('build.sh', 'develop.sh'):
            with self.subTest(script=script):
                result, linked = self.run_script(script, 0)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(linked, script == 'develop.sh')


if __name__ == '__main__':
    unittest.main()
