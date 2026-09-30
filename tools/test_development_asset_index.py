"""File delivery contracts only; no native gzip or numerical execution."""
import hashlib
import json
from pathlib import Path
import unittest
import handoff

ROOT = Path(__file__).resolve().parents[1]
TAG = 'hf4-c2-development-evidence-20260930-v1'

class DevelopmentAssetIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = json.loads((ROOT / 'handoff/evidence_assets.json').read_text())
        cls.assets = [a for a in cls.index['assets'] if a.get('release_tag') == TAG]
        cls.receipt = json.loads((ROOT / 'handoff/development_20260930/packaging_receipt.json').read_text())

    def test_old_thirteen_assets_unchanged(self):
        canonical = json.dumps(self.index['assets'][:13], sort_keys=True, separators=(',', ':')).encode()
        self.assertEqual(hashlib.sha256(canonical).hexdigest(),
                         '04850a54db828447c8e45dafab0a3c4377fa5e1d2a0afee427d3f0833a865c90')

    def test_complete_roots_and_members(self):
        self.assertEqual(len(self.assets), 6)
        rows = [r for a in self.assets for r in a['files']]
        self.assertEqual(len(rows), 3599)
        self.assertEqual(sum(r['bytes'] for r in rows), 912107444)
        self.assertEqual(len({r['path'] for r in rows}), len(rows))
        self.assertEqual({r['path'].split('/')[1] for r in rows}, set(self.receipt['frozen_roots']))
        self.assertEqual(sum(r['path'].endswith('.pyd') for r in rows), 12)
        self.assertEqual(set(r['path'] for r in rows), set(self.receipt['git_navigation_files']) | set(self.receipt['release_only_files']))
        self.assertFalse(self.receipt['native_gzip_decoded'])
        for asset, receipt in zip(self.assets, self.receipt['archives']):
            self.assertEqual({k: asset[k] for k in receipt}, receipt)
            self.assertEqual(asset['mode'], 'restore_relative_files')
            self.assertTrue(asset['url'].endswith('/' + TAG + '/' + asset['name']))

    def test_latest_stage_restores_native_sources_and_prior_groups(self):
        closure = handoff.select_assets(ROOT, [self.assets[-1]['name']])
        self.assertEqual([a['name'] for a in closure[-6:]], [a['name'] for a in self.assets])
        destinations = {}
        for asset in closure:
            for name, row in handoff.asset_destinations(asset):
                identity = row['bytes'], row['sha256']
                if name in destinations:
                    self.assertEqual(destinations[name], identity)
                destinations[name] = identity
        native = [p for p in destinations if '/micro_trace_002/native/' in p]
        self.assertEqual(len(native), 2)
        self.assertTrue(any(p.endswith('.trace.json.gz') for p in native))
        self.assertTrue(any(p.endswith('.xplane.pb') for p in native))

if __name__ == '__main__':
    unittest.main()
