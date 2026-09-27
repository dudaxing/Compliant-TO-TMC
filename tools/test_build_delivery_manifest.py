"""Synthetic Git-repository checks; no project files or scientific runs change."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import build_delivery_manifest as builder


class DeliveryManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.run_git("init", "--quiet")
        (self.root / "handoff").mkdir()
        (self.root / builder.MANIFEST).write_text('{"previous":"preserve until success"}\n', encoding="utf-8")
        (self.root / "tracked.bin").write_bytes(b"original")
        self.run_git("add", "--", builder.MANIFEST, "tracked.bin")

    def run_git(self, *args, data=None):
        return subprocess.check_output(["git", *args], cwd=self.root, input=data, stderr=subprocess.PIPE)

    def test_tracked_only_self_exclusion_and_current_worktree_bytes(self):
        (self.root / "new-not-staged.txt").write_bytes(b"not delivery yet")
        (self.root / "restored-evidence.npz").write_bytes(b"local historical evidence")
        (self.root / "tracked.bin").write_bytes(b"current unstaged worktree bytes")
        record, report = builder.build_manifest(self.root)
        self.assertEqual([row["path"] for row in record["files"]], ["tracked.bin"])
        self.assertEqual(record["files"][0]["sha256"],
                         hashlib.sha256(b"current unstaged worktree bytes").hexdigest())
        self.assertEqual(report["excluded_nonignored_untracked_files"],
                         ["new-not-staged.txt", "restored-evidence.npz"])
        self.assertTrue(report["manifest_already_tracked"])
        self.assertEqual(record["science_baseline_commit"], builder.SCIENCE_BASELINE)
        self.assertEqual(record["science_version"], "0.5.0")
        self.assertEqual(record["storage_stage"], "main-consolidation-20260927")
        self.assertEqual(record["previous_delivery_commit"], builder.PREVIOUS_DELIVERY)
        builder.write_manifest(self.root, record)
        self.assertEqual(json.loads((self.root / builder.MANIFEST).read_text()), record)
        self.assertNotIn(builder.MANIFEST, [row["path"] for row in record["files"]])

    def test_staged_new_file_enters_membership(self):
        (self.root / "new.txt").write_bytes(b"delivery")
        before, _ = builder.build_manifest(self.root)
        self.run_git("add", "--", "new.txt")
        after, _ = builder.build_manifest(self.root)
        self.assertEqual(len(after["files"]), len(before["files"]) + 1)
        self.assertIn("new.txt", [row["path"] for row in after["files"]])

    def test_unmerged_index_rejected_before_manifest_write(self):
        original = (self.root / builder.MANIFEST).read_bytes()
        blob = self.run_git("hash-object", "-w", "--stdin", data=b"conflict").decode().strip()
        entries = (f"0 {'0' * 40}\ttracked.bin\n"
                   f"100644 {blob} 1\ttracked.bin\n"
                   f"100644 {blob} 2\ttracked.bin\n"
                   f"100644 {blob} 3\ttracked.bin\n")
        self.run_git("update-index", "--index-info", data=entries.encode())
        with self.assertRaisesRegex(ValueError, "Unresolved index conflict"):
            builder.build_manifest(self.root)
        self.assertEqual((self.root / builder.MANIFEST).read_bytes(), original)

    def test_symlink_index_mode_rejected_even_if_worktree_is_regular(self):
        blob = self.run_git("hash-object", "-w", "--stdin", data=b"../elsewhere").decode().strip()
        self.run_git("update-index", "--cacheinfo", f"120000,{blob},tracked.bin")
        with self.assertRaisesRegex(ValueError, "Non-regular Git index entry"):
            builder.build_manifest(self.root)

    def test_missing_or_directory_tracked_path_rejected(self):
        (self.root / "tracked.bin").unlink()
        with self.assertRaisesRegex(ValueError, "Tracked file is missing"):
            builder.build_manifest(self.root)
        (self.root / "tracked.bin").mkdir()
        with self.assertRaisesRegex(ValueError, "Not an ordinary file"):
            builder.build_manifest(self.root)

    def test_escaping_and_noncanonical_paths_rejected(self):
        for name in ("../outside", "/absolute", "C:/outside", "folder\\file", "./file", "folder//file"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                builder.confined_regular_path(self.root, name, missing_ok=True)


if __name__ == "__main__":
    unittest.main()
