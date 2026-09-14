"""Focused safety checks for restoring ordinary evidence, without FE imports."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

spec = importlib.util.spec_from_file_location('handoff_tool', Path(__file__).with_name('handoff.py'))
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)

class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'checkout'
        (self.root / 'handoff').mkdir(parents=True)
        self.source = Path(self.temp.name) / 'assets'; self.source.mkdir()
        self.cache = Path(self.temp.name) / 'cache'
        self.patch = patch.object(h, 'ROOT', self.root); self.patch.start(); self.addCleanup(self.patch.stop)

    def fixture(self):
        contents = {'history/a.bin':b'correct A', 'history/b.bin':b'correct B'}
        archive = self.source / 'sample.zip'
        with zipfile.ZipFile(archive, 'w') as z:
            for name, data in contents.items():z.writestr(name, data)
        asset = {'name':archive.name, 'bytes':archive.stat().st_size, 'sha256':h.digest(archive), 'mode':'restore_relative_files',
                 'files':[{'path':n, 'bytes':len(d), 'sha256':hashlib.sha256(d).hexdigest()} for n,d in contents.items()]}
        (self.root/'handoff/evidence_assets.json').write_text(json.dumps({'assets':[asset]}))
        return asset

    def test_reject_escaping_and_windows_paths(self):
        for name in ('../outside', '/absolute', 'C:/outside', 'x\\y', 'x:stream'):
            with self.subTest(name=name), self.assertRaises(ValueError):h.safe_path(self.root, name)

    def test_restore_and_identical_second_read(self):
        self.fixture()
        for _ in range(2):self.assertEqual(h.fetch(None,self.cache,self.source)['status'], 'pass')
        self.assertEqual((self.root/'history/a.bin').read_bytes(), b'correct A')

    def test_existing_different_file_prevents_all_writes(self):
        self.fixture();(self.root/'history').mkdir();(self.root/'history/b.bin').write_bytes(b'user data')
        with self.assertRaises(ValueError):h.fetch(None,self.cache,self.source)
        self.assertFalse((self.root/'history/a.bin').exists())
        self.assertEqual((self.root/'history/b.bin').read_bytes(), b'user data')

    def test_corrupt_archive_rejected_before_extraction(self):
        self.fixture();(self.source/'sample.zip').write_bytes(b'corrupt')
        with self.assertRaises(ValueError):h.fetch(None,self.cache,self.source)
        self.assertFalse((self.root/'history').exists())

    def test_wrong_member_hash_rejected(self):
        asset=self.fixture();asset['files'][0]['sha256']='0'*64
        (self.root/'handoff/evidence_assets.json').write_text(json.dumps({'assets':[asset]}))
        with self.assertRaises(ValueError):h.fetch(None,self.cache,self.source)
        self.assertFalse((self.root/'history/a.bin').exists())

    def test_manifest_detects_changed_file(self):
        file=self.root/'state.txt';file.write_bytes(b'original')
        (self.root/'handoff/repository_manifest.json').write_text(json.dumps({'files':[{'path':'state.txt','bytes':8,'sha256':h.digest(file)}]}))
        self.assertEqual(h.verify()['status'],'pass');file.write_bytes(b'modified')
        with self.assertRaises(ValueError):h.verify()

if __name__ == '__main__':unittest.main()
