"""Small metadata-only test candidates; no saved inputs or mechanics are loaded.

These tests are prepared for a separately authorized check and have not been run.
"""

import copy
from pathlib import Path
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "example"))
from compare_saved_designs import bind_observation, pair_rows, require_same_contract


class CompareMetadataTests(unittest.TestCase):
    def test_repeated_displacements_keep_target_and_leg_pairs(self):
        left = [
            {"original_target_index": 0, "leg": "origin", "d_mm": 0.0},
            {"original_target_index": 4, "leg": "loading", "d_mm": 0.4},
            {"original_target_index": 20, "leg": "unloading", "d_mm": 0.4},
            {"original_target_index": 24, "leg": "unloading", "d_mm": 0.0},
        ]
        right = copy.deepcopy(left)

        pairs = pair_rows(left, right)

        self.assertEqual(len(pairs), 4)
        self.assertEqual(
            [(row["original_target_index"], row["leg"], row["d_mm"]) for row in pairs],
            [(0, "origin", 0.0), (4, "loading", 0.4),
             (20, "unloading", 0.4), (24, "unloading", 0.0)],
        )
        self.assertEqual(
            [(row["pair_index"], row["left_row_index"], row["right_row_index"])
             for row in pairs],
            [(0, 0, 0), (1, 1, 1), (2, 2, 2), (3, 3, 3)],
        )
        right[2]["original_target_index"] = 19
        with self.assertRaises(ValueError):
            pair_rows(left, right)

    def test_same_displacement_does_not_bind_a_different_state_sha(self):
        state = {
            "accepted_row_index": 4,
            "state_sha256": "a" * 64,
            "original_target_index": 4,
            "leg": "loading",
            "d_mm": 0.4,
        }
        observed = {
            "index": 4,
            "state_sha256": "a" * 64,
            "original_target_index": 4,
            "leg": "loading",
            "d_mm": 0.4,
        }
        self.assertEqual(
            bind_observation(state, observed),
            {"state": state, "observation": observed},
        )

        observed["state_sha256"] = "b" * 64
        with self.assertRaises(ValueError):
            bind_observation(state, observed)

    def test_different_physical_declarations_reject_a_common_contract(self):
        contract = {
            "alpha": 5e-7,
            "workpiece": {"center_mm": [71.0, 40.0], "side_mm": 18.0},
        }
        self.assertIsNone(require_same_contract(contract, copy.deepcopy(contract)))

        different_alpha = copy.deepcopy(contract)
        different_alpha["alpha"] = 1e-6
        different_workpiece = copy.deepcopy(contract)
        different_workpiece["workpiece"]["side_mm"] = 20.0
        for changed in (different_alpha, different_workpiece):
            with self.subTest(contract=changed), self.assertRaises(ValueError):
                require_same_contract(contract, changed)


if __name__ == "__main__":
    unittest.main()
