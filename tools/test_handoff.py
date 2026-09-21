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

    def write_index(self, assets):
        (self.root/'handoff/evidence_assets.json').write_text(json.dumps({'assets':assets}), encoding='utf-8')

    def make_asset(self, name, contents, requires=None, mode='restore_relative_files'):
        archive = self.source / name
        with zipfile.ZipFile(archive, 'w') as z:
            for path, data in contents.items():
                z.writestr(path, data)
        asset = {'name':name, 'bytes':archive.stat().st_size, 'sha256':h.digest(archive), 'mode':mode}
        if mode == 'save_archive':
            asset['destination'] = 'saved/' + name
        else:
            asset['files'] = [{'path':p, 'bytes':len(d), 'sha256':hashlib.sha256(d).hexdigest()}
                              for p,d in contents.items()]
        if requires is not None:
            asset['requires'] = requires
        return asset

    def write_manifest(self, paths=('handoff/evidence_assets.json',)):
        records = [{'path':p, 'bytes':(self.root/p).stat().st_size, 'sha256':h.digest(self.root/p)} for p in paths]
        (self.root/'handoff/repository_manifest.json').write_text(json.dumps({'files':records}), encoding='utf-8')

    def dependency_fixture(self):
        base = self.make_asset('base.zip', {'history/base.txt':b'base'})
        middle = self.make_asset('middle.zip', {'history/middle.txt':b'middle'}, ['base.zip'])
        final = self.make_asset('final.zip', {'history/final.txt':b'final'}, ['middle.zip', 'base.zip'])
        spare = self.make_asset('spare.zip', {'history/spare.txt':b'spare'})
        # Deliberately reverse dependency order in the index.
        self.write_index([final, spare, middle, base])
        return base, middle, final, spare

    def test_reject_escaping_and_windows_paths(self):
        for name in ('../outside', '/absolute', 'C:/outside', 'x\\y', 'x:stream', '', '.', './x', 'x//y', 'x/'):
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

    def test_transitive_dependency_order_and_deduplication(self):
        self.dependency_fixture()
        result = h.fetch(['final.zip'], self.cache, self.source)
        self.assertEqual(result['asset_closure'], ['base.zip', 'middle.zip', 'final.zip'])
        self.assertFalse((self.root/'history/spare.txt').exists())
        self.assertEqual((self.root/'history/final.txt').read_bytes(), b'final')

    def test_multiple_roots_share_one_dependency(self):
        self.dependency_fixture()
        selected = h.select_assets(self.root, ['middle.zip', 'final.zip'])
        self.assertEqual([a['name'] for a in selected], ['base.zip', 'middle.zip', 'final.zip'])

    def test_unknown_selection_rejected_before_cache_or_output(self):
        self.fixture()
        with self.assertRaisesRegex(ValueError, 'Unknown --asset'):
            h.fetch(['unknown.zip'], self.cache, self.source)
        self.assertFalse(self.cache.exists())

    def test_duplicate_selection_rejected(self):
        self.fixture()
        with self.assertRaisesRegex(ValueError, 'Duplicate --asset'):
            h.fetch(['sample.zip', 'sample.zip'], self.cache, self.source)

    def test_duplicate_asset_name_rejected(self):
        asset = self.fixture(); self.write_index([asset, asset])
        with self.assertRaisesRegex(ValueError, 'Duplicate asset name'):
            h.fetch(None, self.cache, self.source)
        self.assertFalse(self.cache.exists())

    def test_missing_dependency_rejected_even_for_unrelated_selection(self):
        base, middle, final, spare = self.dependency_fixture()
        final['requires'] = ['missing.zip']; self.write_index([base, middle, final, spare])
        with self.assertRaisesRegex(ValueError, 'Unknown dependency'):
            h.fetch(['spare.zip'], self.cache, self.source)
        self.assertFalse(self.cache.exists())

    def test_dependency_cycles_rejected_before_any_write(self):
        for dependencies in (['base.zip'], ['final.zip']):
            with self.subTest(dependencies=dependencies):
                base, middle, final, spare = self.dependency_fixture()
                base['requires'] = dependencies; self.write_index([base, middle, final, spare])
                with self.assertRaisesRegex(ValueError, 'dependency cycle'):
                    h.fetch(['spare.zip'], self.cache, self.source)
                self.assertFalse(self.cache.exists())

    def test_bad_dependency_types_and_duplicates_rejected(self):
        for requires in ('sample.zip', [1], ['sample.zip', 'sample.zip']):
            with self.subTest(requires=requires):
                asset = self.fixture(); asset['requires'] = requires; self.write_index([asset])
                with self.assertRaises(ValueError):
                    h.select_assets(self.root)

    def test_dependency_destination_conflict_prevents_earlier_writes(self):
        self.dependency_fixture()
        (self.root/'history').mkdir()
        (self.root/'history/final.txt').write_bytes(b'user data')
        with self.assertRaises(ValueError):
            h.fetch(['final.zip'], self.cache, self.source)
        self.assertFalse((self.root/'history/base.txt').exists())
        self.assertFalse(self.cache.exists())
        self.assertEqual((self.root/'history/final.txt').read_bytes(), b'user data')

    def test_contradictory_asset_destinations_rejected(self):
        first = self.make_asset('first.zip', {'history/same.txt':b'one'})
        second = self.make_asset('second.zip', {'history/same.txt':b'two'}, ['first.zip'])
        self.write_index([first, second])
        with self.assertRaisesRegex(ValueError, 'Conflicting asset destination'):
            h.fetch(['second.zip'], self.cache, self.source)
        self.assertFalse(self.cache.exists())

    def test_non_directory_parent_rejected_before_other_restoration(self):
        first = self.make_asset('first.zip', {'history/good.txt':b'one'})
        second = self.make_asset('second.zip', {'blocked/child.txt':b'two'}, ['first.zip'])
        self.write_index([first, second]); (self.root/'blocked').write_bytes(b'keep this file')
        with self.assertRaisesRegex(ValueError, 'parent is not a directory'):
            h.fetch(['second.zip'], self.cache, self.source)
        self.assertFalse((self.root/'history').exists())
        self.assertFalse(self.cache.exists())

    def test_nested_asset_file_destinations_rejected(self):
        asset = self.make_asset('nested.zip', {'history/item':b'one', 'history/item/child':b'two'})
        self.write_index([asset])
        with self.assertRaisesRegex(ValueError, 'nested inside another file'):
            h.fetch(None, self.cache, self.source)
        self.assertFalse(self.cache.exists())

    def test_bad_later_member_does_not_write_first_member(self):
        asset = self.fixture(); asset['files'][1]['sha256'] = '0'*64; self.write_index([asset])
        with self.assertRaises(ValueError):
            h.fetch(None, self.cache, self.source)
        self.assertFalse((self.root/'history').exists())

    def test_archive_extra_member_rejected(self):
        asset = self.fixture()
        with zipfile.ZipFile(self.source/'sample.zip', 'a') as z:
            z.writestr('history/unlisted.txt', b'unlisted')
        asset['bytes'] = (self.source/'sample.zip').stat().st_size
        asset['sha256'] = h.digest(self.source/'sample.zip'); self.write_index([asset])
        with self.assertRaisesRegex(ValueError, 'membership differs'):
            h.fetch(None, self.cache, self.source)
        self.assertFalse((self.root/'history').exists())

    def test_escaping_member_rejected_before_download(self):
        asset = self.make_asset('escape.zip', {'../outside.txt':b'bad'}); self.write_index([asset])
        with self.assertRaises(ValueError):
            h.fetch(None, self.cache, self.source)
        self.assertFalse((self.root.parent/'outside.txt').exists())
        self.assertFalse(self.cache.exists())

    def test_default_verify_does_not_require_archived_assets(self):
        self.dependency_fixture(); self.write_manifest()
        result = h.verify()
        self.assertEqual(result['status'], 'pass')
        self.assertEqual(result['asset_closure'], [])
        with self.assertRaises(ValueError):
            h.verify(full=True)
        with self.assertRaises(ValueError):
            h.verify(assets=['final.zip'])

    def test_verify_selected_closure_and_full_missing_asset(self):
        self.dependency_fixture(); self.write_manifest()
        h.fetch(['final.zip'], self.cache, self.source)
        result = h.verify(assets=['final.zip'])
        self.assertEqual(result['restored_historical_files'], 3)
        with self.assertRaises(ValueError):
            h.verify(full=True)
        h.fetch(['spare.zip'], self.cache, self.source)
        self.assertEqual(h.verify(full=True)['restored_historical_files'], 4)
        (self.root/'history/base.txt').unlink()
        with self.assertRaises(ValueError):
            h.verify(assets=['final.zip'])

    def test_verify_full_and_selection_mutually_exclusive(self):
        with self.assertRaisesRegex(ValueError, 'either --full or --asset'):
            h.verify(full=True, assets=['sample.zip'])

    def test_save_archive_backward_compatibility(self):
        asset = self.make_asset('saved.zip', {'inside.txt':b'evidence'}, mode='save_archive')
        self.write_index([asset]); self.write_manifest()
        h.fetch(None, self.cache, self.source)
        self.assertEqual((self.root/'saved/saved.zip').read_bytes(), (self.source/'saved.zip').read_bytes())
        result = h.verify(full=True)
        self.assertEqual(result['saved_archives_checked'], 1)
        self.assertEqual(result['restored_historical_files'], 0)
        h.fetch(None, self.cache, self.source)
        (self.root/'saved/saved.zip').write_bytes(b'changed')
        with self.assertRaises(ValueError):
            h.verify(full=True)

    def test_prepare_replay_is_independent_manifest_only_root(self):
        self.dependency_fixture()
        (self.root/'tracked.txt').write_bytes(b'bound content')
        (self.root/'unlisted.txt').write_bytes(b'do not copy')
        (self.root/'.git').mkdir(); (self.root/'.git/private').write_bytes(b'private')
        (self.root/'.venv').mkdir(); (self.root/'.venv/private').write_bytes(b'private')
        self.write_manifest(['handoff/evidence_assets.json', 'tracked.txt'])
        destination = self.root.parent/'fresh-replay'
        manifest_bytes = (self.root/'handoff/repository_manifest.json').read_bytes()
        with patch.object(h, 'inspect', side_effect=AssertionError('No environment or evaluator import')):
            result = h.prepare_replay(destination, ['final.zip'], self.cache, self.source)
        self.assertEqual(result['status'], 'pass')
        self.assertEqual(result['repository_files_copied'], 2)
        self.assertEqual(result['source_manifest_sha256'], hashlib.sha256(manifest_bytes).hexdigest())
        self.assertEqual((destination/'handoff/repository_manifest.json').read_bytes(), manifest_bytes)
        self.assertEqual(result['asset_closure'], ['base.zip', 'middle.zip', 'final.zip'])
        self.assertFalse(result['mechanics_run']); self.assertFalse(result['high_precision_run'])
        self.assertFalse((self.root/'history').exists())
        self.assertFalse((destination/'unlisted.txt').exists())
        self.assertFalse((destination/'.git').exists()); self.assertFalse((destination/'.venv').exists())
        self.assertEqual((destination/'history/base.txt').read_bytes(), b'base')
        self.assertEqual(h.ROOT, self.root)
        self.assertEqual(h.verify(assets=['final.zip'], root=destination)['status'], 'pass')

    def test_prepare_replay_rejects_existing_or_nested_destination(self):
        self.fixture(); self.write_manifest()
        existing = self.root.parent/'existing'; existing.mkdir()
        for destination in (existing, self.root/'nested'):
            with self.subTest(destination=destination), self.assertRaises(ValueError):
                h.prepare_replay(destination, ['sample.zip'], self.cache, self.source)
        self.assertFalse((self.root/'nested').exists())

    def test_prepare_replay_refuses_unbound_index(self):
        self.fixture(); self.write_manifest([])
        destination = self.root.parent/'fresh-replay'
        with self.assertRaisesRegex(ValueError, 'manifest-bound evidence_assets'):
            h.prepare_replay(destination, ['sample.zip'], self.cache, self.source)
        self.assertFalse(destination.exists())

    def test_prepare_replay_refuses_changed_source_before_creating_destination(self):
        self.fixture(); self.write_manifest()
        (self.root/'handoff/evidence_assets.json').write_text('{"assets":[]}')
        destination = self.root.parent/'fresh-replay'
        with self.assertRaises(ValueError):
            h.prepare_replay(destination, ['sample.zip'], self.cache, self.source)
        self.assertFalse(destination.exists())

    def test_cli_verify_asset_and_prepare_replay(self):
        self.fixture(); self.write_manifest()
        destination = self.root.parent/'fresh-cli-replay'
        args = ['handoff.py', 'prepare-replay', '--asset', 'sample.zip', '--destination', str(destination),
                '--cache-dir', str(self.cache), '--from-dir', str(self.source)]
        with patch('sys.argv', args), patch('builtins.print'):
            h.main()
        with patch.object(h, 'ROOT', destination), patch('sys.argv', ['handoff.py', 'verify', '--asset', 'sample.zip']), patch('builtins.print'):
            h.main()

if __name__ == '__main__':unittest.main()
