"""Offline packaging contracts; runs only in the hub-free CI job."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class BundleTests(unittest.TestCase):
    def load_builder(self):
        path = ROOT / 'tools/build_bundle.py'
        self.assertTrue(path.is_file(), 'the reusable bundle builder must exist')
        spec = importlib.util.spec_from_file_location('build_bundle', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.build_bundle

    def fixture(self, root):
        (root / 'app.groovy').write_text('definition(name: "Sample", namespace: "example")\n')
        (root / 'lib.groovy').write_text('library(name: "Helpers", namespace: "example")\n')
        config = {'namespace': 'example', 'name': 'sample', 'files': [
            {'type': 'library', 'path': 'lib.groovy'},
            {'type': 'app', 'path': 'app.groovy'}]}
        path = root / 'bundle.json'
        path.write_text(json.dumps(config))
        return path, config

    def test_reproducible_bundle_with_explicit_install_order(self):
        build = self.load_builder()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest, _ = self.fixture(root)
            out = root / 'dist/sample.zip'
            build(manifest, out)
            first = out.read_bytes()
            build(manifest, out)
            self.assertEqual(first, out.read_bytes())
            with zipfile.ZipFile(out) as z:
                expected = b'example\nsample\nlibrary lib.groovy\napp app.groovy\n'
                self.assertEqual(z.read('install.txt'), expected)
                self.assertEqual(z.read('update.txt'), expected)
                self.assertEqual(z.read('app.groovy'), (root/'app.groovy').read_bytes())

    def test_rejects_escaping_paths_without_touching_existing_output(self):
        build = self.load_builder()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest, config = self.fixture(root)
            config['files'][0]['path'] = '../outside.groovy'
            manifest.write_text(json.dumps(config))
            out = root/'existing.zip'
            out.write_bytes(b'keep existing artifact')
            with self.assertRaises(ValueError):
                build(manifest, out)
            self.assertEqual(out.read_bytes(), b'keep existing artifact')

    def test_rejects_symlink_escape(self):
        build = self.load_builder()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sub = root/'project'; sub.mkdir()
            manifest, config = self.fixture(sub)
            outside = root/'outside.groovy'; outside.write_text('secret')
            (sub/'linked.groovy').symlink_to(outside)
            config['files'][0]['path'] = 'linked.groovy'
            manifest.write_text(json.dumps(config))
            with self.assertRaises(ValueError):
                build(manifest, sub/'out.zip')

    def test_rejects_duplicate_archive_names_and_manifest_injection(self):
        build = self.load_builder()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest, config = self.fixture(root)
            for mutate in (
                lambda c: c.update(name='sample\napp extra.groovy'),
                lambda c: c['files'].append(c['files'][0]),
                lambda c: c['files'][0].update(type='firmware'),
                lambda c: c.update(files=[]),
            ):
                candidate = json.loads(json.dumps(config))
                mutate(candidate)
                manifest.write_text(json.dumps(candidate))
                with self.assertRaises(ValueError):
                    build(manifest, root/'out.zip')


if __name__ == '__main__':
    unittest.main()
