#!/usr/bin/env python3
"""Check extraction integrity and exact copies, without contacting any hub or source repo."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / 'reference/hubitat-local-mcp-server'
manifest = json.loads((ROOT / 'reference/provenance.json').read_text())
errors = []
for entry in manifest['files']:
    path = REFERENCE / entry['path']
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
        errors.append(entry['path'])
# The active Gradle wrapper evolves independently; its archived originals above
# remain protected by provenance hashes. Other exact copies stay immutable.
copies = {
    'watchdog/e2e-deadman-watchdog-v3-1.groovy': 'e2e-deadman-watchdog-v3-1.groovy',
    'scripts/lease_acquire.sh': '.github/scripts/lease_acquire.sh',
    'scripts/lease_release.sh': '.github/scripts/lease_release.sh',
    'LICENSE': 'LICENSE',
}
for dest, source in copies.items():
    if (ROOT / dest).read_bytes() != (REFERENCE / source).read_bytes():
        errors.append(dest)
if errors:
    raise SystemExit('Extraction integrity failed: ' + ', '.join(errors))
print(f"Verified {len(manifest['files'])} reference files and {len(copies)} exact copies at {manifest['commit']}")
