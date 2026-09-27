"""Standard-library checks for the follow-up evidence publication contract.

No archive download, mechanics assembly, high-precision computation or restore.
The one-time archive-byte verification is recorded separately in
handoff/main_consolidation_20260927/local_asset_check.json.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

import handoff


ROOT = Path(__file__).resolve().parents[1]
TAG = "hf4-c2-followup-evidence-v1"
STABLE = "hf4-c2-stable-f-saved-production-arrays-v1.zip"
V4 = "hf4-c2-v4-mesh_h00625_v4-payloads-v1.zip"
C1 = "hf4-c2-s0-c1_runs-v1.zip"
C2 = "hf4-c2-s0-c2_runs-v1.zip"
MANIFESTS = {
    STABLE: ("hf4_c2_stable_f_validation/local_evidence_archive_001.json",
             "08cd7ba3a47a9284847adae9b40afbc64d4e7c1fa949cf89cedef661b9e48e06"),
    V4: ("hf4_c2_v4_results/storage/mesh_h00625_v4.external_payloads.json",
         "3809fc3b7bcb566b79d9fd50d1da4baac90c780130d44c43db2042e82b3a163e"),
}


def read(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


class FollowupAssetIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = read("handoff/evidence_assets.json")
        cls.assets = {item["name"]: item for item in cls.index["assets"]}

    def test_original_eleven_assets_unchanged(self):
        original = self.index["assets"][:11]
        canonical = json.dumps(original, sort_keys=True, separators=(",", ":")).encode()
        self.assertEqual(hashlib.sha256(canonical).hexdigest(),
                         "9d117ce1390567d3e80e8eb7182d9cdc9e7011293b054802ebe67ae5785f477f")
        self.assertEqual(self.index["release_tag"], "hf-history-0.5.0")

    def test_new_records_exactly_adapt_frozen_manifests(self):
        for name, (path, frozen_sha) in MANIFESTS.items():
            with self.subTest(asset=name):
                self.assertEqual(handoff.digest(ROOT / path), frozen_sha)
                original, asset = read(path), self.assets[name]
                self.assertEqual(asset["scientific_manifest"], path)
                self.assertEqual(asset["scientific_manifest_sha256"], frozen_sha)
                self.assertEqual(asset["bytes"], original["archive_bytes"])
                self.assertEqual(asset["sha256"], original["archive_sha256"])
                self.assertEqual(asset["name"], original["archive"])
                self.assertEqual(asset["files"], [
                    {key: member[key] for key in ("path", "bytes", "sha256")}
                    for member in original["members"]])
                self.assertEqual(len(asset["files"]), original["member_count"])
                self.assertEqual(sum(row["bytes"] for row in asset["files"]), original["member_bytes"])
                self.assertEqual(asset["mode"], "restore_relative_files")
                self.assertEqual(asset["release_tag"], TAG)
                self.assertEqual(asset["url"],
                    f"https://github.com/dudaxing/Compliant-TO-TMC/releases/download/{TAG}/{name}")

    def test_minimal_dependency_closures(self):
        self.assertEqual([row["name"] for row in handoff.select_assets(ROOT, [STABLE])], [C1, C2, STABLE])
        self.assertEqual([row["name"] for row in handoff.select_assets(ROOT, [V4])], [C1, V4])
        self.assertEqual([row["name"] for row in handoff.select_assets(ROOT, [STABLE, V4])],
                         [C1, C2, STABLE, V4])

    def test_unique_names_paths_and_no_conflicting_destinations(self):
        # select_assets also checks the complete dependency graph and safe paths.
        selected = handoff.select_assets(ROOT)
        self.assertEqual(len(selected), len(self.assets))
        destinations = {}
        for asset in selected:
            for name, row in handoff.asset_destinations(asset):
                identity = (row["bytes"], row["sha256"])
                if name in destinations:
                    self.assertEqual(identity, destinations[name], name)
                destinations[name] = identity

    def test_stable_members_match_committed_driver_bindings(self):
        for member in self.assets[STABLE]["files"]:
            run, relative = member["path"].split("/driver_output/")
            bound = read(f"{run}/driver_output/output_sha256.json")
            self.assertEqual(member["sha256"], bound[relative], member["path"])

    def test_v4_members_match_committed_run_bindings(self):
        path, _ = MANIFESTS[V4]
        original = read(path)
        spec = importlib.util.spec_from_file_location("external_payloads", ROOT / "hf4_c2_v4_results/external_payloads.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        bound = module.bindings(ROOT / original["run"])
        self.assertEqual(len(bound), len(original["members"]))
        for member in original["members"]:
            relative = member["path"][len(original["run"]) + 1:]
            digest, source = bound[relative]
            self.assertEqual(digest, member["sha256"])
            self.assertEqual(original["run"] + "/" + source, member["bound_by"])
        for member in original["kept_in_git"]:
            handoff.check_file(ROOT / member["path"], member)


if __name__ == "__main__":
    unittest.main()
