#!/usr/bin/env python3
"""Reject incomplete, skipped or retired-version watchdog test executions."""
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CACHE_SUITE = 'server.WatchdogV31CacheSpec'


def check_reports(reports, inventory):
    expected = json.loads(inventory.read_text())['suites']
    allowed = set(expected) | {CACHE_SUITE}
    actual = {}
    errors = []
    for path in sorted(reports.glob('TEST-*.xml')):
        suite = ET.parse(path).getroot()
        name = suite.attrib['name']
        if name not in allowed:
            errors.append(f'Unexpected watchdog suite: {name}')
        if name in actual:
            errors.append(f'Duplicate suite report: {name}')
        cases = suite.findall('testcase')
        actual[name] = {case.attrib['name'] for case in cases}
        if len(actual[name]) != len(cases):
            errors.append(f'Duplicate test case names: {name}')
        if not cases:
            errors.append(f'Empty watchdog suite: {name}')
        for key in ('failures', 'errors', 'skipped'):
            if int(suite.attrib.get(key, 0)):
                errors.append(f'{name}: nonzero {key}')
        for case in cases:
            if any(case.find(tag) is not None for tag in ('failure', 'error', 'skipped')):
                errors.append(f'Test did not pass: {name}: {case.attrib["name"]}')
        if int(suite.attrib['tests']) != len(cases):
            errors.append(f'Incomplete test report: {name}')
    for name in sorted(allowed):
        if name not in actual:
            errors.append(f'Missing watchdog suite: {name}')
    for name, cases in expected.items():
        missing = set(cases) - actual.get(name, set())
        if missing:
            errors.append(f'Missing test cases in {name}: {sorted(missing)}')
    if errors:
        raise ValueError('\n'.join(errors))
    total = sum(map(len, actual.values()))
    retained = sum(map(len, expected.values()))
    return f'Verified {total} passing v3.1 test cases; all {retained} retained cases executed; zero skips.'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reports', type=Path, default=ROOT / 'build/test-results/watchdogTest')
    parser.add_argument('--inventory', type=Path, default=ROOT / 'ci/watchdog/v31-test-inventory.json')
    args = parser.parse_args()
    try:
        print(check_reports(args.reports, args.inventory))
    except (ValueError, KeyError, OSError, ET.ParseError) as error:
        raise SystemExit(str(error)) from error


if __name__ == '__main__':
    main()
