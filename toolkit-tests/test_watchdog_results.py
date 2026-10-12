"""Run the CI report gate against complete, filtered and misleading JUnit reports."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


class WatchdogResultsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.inventory = self.root / 'inventory.json'
        self.inventory.write_text(json.dumps({'suites': {'server.WatchdogV31ManualSpec': ['retained case']}}))
        self.report('server.WatchdogV31ManualSpec', ['retained case'])
        self.report('server.WatchdogV31CacheSpec', ['compilation reuse'])

    def report(self, name, names, outcome=None):
        suite = ET.Element('testsuite', name=name, tests=str(len(names)), failures='0', errors='0', skipped='0')
        for test in names:
            case = ET.SubElement(suite, 'testcase', name=test, classname=name)
            if outcome:
                ET.SubElement(case, outcome)
        path = self.root / f'TEST-{name}.xml'
        ET.ElementTree(suite).write(path)
        return path

    def gate(self):
        return subprocess.run([sys.executable, str(ROOT / 'tools/check_watchdog_results.py'),
                               '--reports', str(self.root), '--inventory', str(self.inventory)],
                              capture_output=True, text=True, check=False)

    def test_complete_execution_accepts_additional_cases(self):
        self.report('server.WatchdogV31ManualSpec', ['retained case', 'new regression'])
        result = self.gate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('3 passing v3.1 test cases', result.stdout)

    def test_filtered_out_case_is_rejected(self):
        self.report('server.WatchdogV31ManualSpec', ['unrelated test'])
        result = self.gate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('retained case', result.stderr)

    def test_missing_suite_is_rejected(self):
        (self.root / 'TEST-server.WatchdogV31CacheSpec.xml').unlink()
        self.assertNotEqual(self.gate().returncode, 0)

    def test_retired_watchdog_execution_is_rejected(self):
        self.report('server.WatchdogV3ManualSpec', ['old version'])
        result = self.gate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Unexpected watchdog suite', result.stderr)

    def test_skipped_or_failed_case_is_rejected_even_with_successful_summary(self):
        for outcome in ('skipped', 'failure', 'error'):
            with self.subTest(outcome=outcome):
                self.report('server.WatchdogV31ManualSpec', ['retained case'], outcome)
                self.assertNotEqual(self.gate().returncode, 0)

    def test_empty_or_malformed_reports_are_rejected(self):
        path = self.report('server.WatchdogV31ManualSpec', [])
        self.assertNotEqual(self.gate().returncode, 0)
        path.write_text('<broken')
        self.assertNotEqual(self.gate().returncode, 0)

    def test_incomplete_report_with_inflated_total_is_rejected(self):
        path = self.root / 'TEST-server.WatchdogV31ManualSpec.xml'
        path.write_text(path.read_text().replace('tests="1"', 'tests="2"'))
        self.assertNotEqual(self.gate().returncode, 0)
