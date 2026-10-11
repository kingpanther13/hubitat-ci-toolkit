#!/usr/bin/env python3
"""Build a reproducible Hubitat bundle from an explicit ordered manifest (stdlib only)."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NAME = re.compile(r'[A-Za-z0-9_.-]+\Z')


def build_bundle(manifest: Path, output: Path) -> str:
    """Validate all inputs, atomically write the bundle, return its SHA256."""
    manifest = Path(manifest).resolve()
    output = Path(output).resolve()
    root = manifest.parent
    config = json.loads(manifest.read_text(encoding='utf-8'))
    if not isinstance(config, dict):
        raise ValueError('manifest must be an object')
    for key in ('namespace', 'name'):
        if not isinstance(config.get(key), str) or not NAME.fullmatch(config[key]):
            raise ValueError(f'{key} must contain only letters, numbers, dots, underscores or dashes')
    entries = config.get('files')
    if not isinstance(entries, list) or not entries:
        raise ValueError('files must be a nonempty ordered list')
    payloads = {}
    lines = [config['namespace'], config['name']]
    for entry in entries:
        if not isinstance(entry, dict) or entry.get('type') not in ('library', 'driver', 'app'):
            raise ValueError('each file needs type library, driver or app')
        relative = entry.get('path')
        if not isinstance(relative, str) or not relative:
            raise ValueError('each file needs a relative path')
        path = (root / relative).resolve()
        if Path(relative).is_absolute() or not path.is_relative_to(root):
            raise ValueError('source paths must stay inside the manifest directory')
        if path.suffix != '.groovy' or not NAME.fullmatch(path.name):
            raise ValueError('source basenames must be simple .groovy filenames')
        if path.name in payloads:
            raise ValueError('archive basenames must be unique')
        if path == output or output == manifest:
            raise ValueError('output must not overwrite an input')
        payloads[path.name] = path.read_bytes()
        lines.append(f"{entry['type']} {path.name}")
    # Preserve the project's license in distributed source bundles when present.
    license_path = root / 'LICENSE'
    if license_path.exists():
        resolved_license = license_path.resolve()
        if not resolved_license.is_relative_to(root):
            raise ValueError('license must stay inside the manifest directory')
        if output == resolved_license:
            raise ValueError('output must not overwrite the license')
        payloads['LICENSE'] = license_path.read_bytes()
    install = ('\n'.join(lines) + '\n').encode('utf-8')
    payloads['install.txt'] = install
    payloads['update.txt'] = install
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=output.parent, prefix='.bundle-', delete=False) as stream:
            temporary = Path(stream.name)
            # ZIP_STORED is deterministic across zlib versions and appropriate for source bundles.
            with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_STORED) as archive:
                for name, data in payloads.items():
                    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                    info.create_system = 3
                    info.external_attr = 0o100644 << 16
                    archive.writestr(info, data)
        temporary.replace(output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return hashlib.sha256(output.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=ROOT / 'bundle.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'dist/hubitat-bundle.zip')
    args = parser.parse_args()
    try:
        checksum = build_bundle(args.manifest, args.output)
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Bundle build failed: {exc}\n')
    print(f'{checksum}  {args.output.name}')


if __name__ == '__main__':
    main()
