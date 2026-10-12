"""Exercise the extraction gate against real files in isolated fixture copies."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReferenceIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for name in ('tools', 'reference', 'watchdog', 'scripts', 'gradle'):
            shutil.copytree(ROOT / name, self.root / name,
                            ignore=shutil.ignore_patterns('build', '.gradle', '__pycache__'))
        for name in ('gradlew', 'gradlew.bat', 'LICENSE'):
            shutil.copyfile(ROOT / name, self.root / name)

    def verify(self):
        return subprocess.run([sys.executable, str(self.root / 'tools/verify_reference.py')],
                              capture_output=True, text=True, check=False)

    def test_active_wrapper_can_evolve(self):
        for name in ('gradlew', 'gradlew.bat', 'gradle/wrapper/gradle-wrapper.jar',
                     'gradle/wrapper/gradle-wrapper.properties'):
            with self.subTest(name=name):
                path = self.root / name
                path.write_bytes(path.read_bytes() + b'\nupdated wrapper fixture\n')
                result = self.verify()
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_archived_wrapper_change_is_rejected(self):
        path = self.root / 'reference/hubitat-local-mcp-server/gradle/wrapper/gradle-wrapper.properties'
        path.write_text(path.read_text() + '\nchanged\n')
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('gradle/wrapper/gradle-wrapper.properties', result.stderr)

    def test_watchdog_copy_change_is_rejected(self):
        path = self.root / 'watchdog/e2e-deadman-watchdog-v3-1.groovy'
        path.write_text(path.read_text() + '\n// changed\n')
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('watchdog/e2e-deadman-watchdog-v3-1.groovy', result.stderr)
