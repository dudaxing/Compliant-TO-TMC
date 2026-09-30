"""Restore actual long evidence paths; no science or native trace decoding."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
import zipfile
import handoff

@unittest.skipUnless(os.name == 'nt', 'Windows native path namespace')
class LongPathRecoveryTests(unittest.TestCase):
    def test_long_restore_verify_and_existing_conflict(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root, source, cache = base/'checkout', base/'archives', base/'cache'
            (root/'handoff').mkdir(parents=True)
            source.mkdir()
            name = 'evidence/' + '/'.join(c*85 for c in 'abc') + '/events.ndjson'
            content = b'preserve frozen evidence bytes\n'
            archive = source/'long.zip'
            with zipfile.ZipFile(archive, 'w') as z:
                z.writestr(name, content)
            row = {'path': name, 'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest()}
            asset = {'name': 'long.zip', 'url': 'unused', 'mode': 'restore_relative_files',
                     'bytes': archive.stat().st_size, 'sha256': handoff.digest(archive), 'files': [row]}
            (root/'handoff/evidence_assets.json').write_text(json.dumps({'assets': [asset]}))
            (root/'handoff/repository_manifest.json').write_text(json.dumps({'files': []}))
            result = handoff.fetch(['long.zip'], cache, source, root=root)
            self.assertEqual(result['status'], 'pass')
            target = handoff.safe_path(root, name)
            self.assertGreater(len(str(target)), 260)
            self.assertTrue(str(target).startswith('\\\\?\\'))
            self.assertEqual(target.read_bytes(), content)
            self.assertEqual(handoff.verify(assets=['long.zip'], root=root)['restored_historical_files'], 1)
            target.write_bytes(b'keep independent user bytes')
            with self.assertRaises(ValueError):
                handoff.fetch(['long.zip'], cache, source, root=root)
            self.assertEqual(target.read_bytes(), b'keep independent user bytes')
            # Remove only this fixture via its exact native path so the stdlib
            # TemporaryDirectory cleanup does not depend on Windows policy.
            target.unlink()
            for parent in list(target.parents):
                if parent == handoff.extended_windows_path(root):
                    break
                parent.rmdir()

    def test_unc_and_existing_namespace(self):
        self.assertEqual(str(handoff.extended_windows_path(Path('\\\\server\\share\\folder'))),
                         '\\\\?\\UNC\\server\\share\\folder')
        native = handoff.extended_windows_path(Path('C:/example'))
        self.assertEqual(handoff.extended_windows_path(native), native)

if __name__ == '__main__':
    unittest.main()
