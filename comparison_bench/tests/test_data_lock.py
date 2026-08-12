"""File-free unit coverage for the deterministic data-lock selection policy.

The authoritative CLI verification below remains the file-I/O/hash evidence;
this test intentionally avoids pytest's temporary-directory cleanup.
"""
from __future__ import annotations

import unittest

import pandas as pd

from comparison_bench.src.comparison_bench.data_lock import select_group_disjoint_split


class DataLockSelectionTest(unittest.TestCase):
    def test_group_disjoint_split_is_deterministic_and_complete(self):
        eligible = pd.DataFrame(
            {"dataset_id": [dataset for dataset in ("real_d1024_a", "real_d1024_b") for _ in range(65)],
             "frame_id": list(range(65)) * 2}
        )
        chosen, tuning_groups, confirmation_groups = select_group_disjoint_split(
            eligible, seed=20260725, tuning_frames=60, confirmation_frames=60,
        )
        self.assertEqual(chosen.groupby("split").size().to_dict(), {"confirmation": 60, "tuning": 60})
        self.assertTrue(chosen["locked_frame_key"].is_unique)
        self.assertTrue(set(tuning_groups).isdisjoint(confirmation_groups))
        repeat, _, _ = select_group_disjoint_split(eligible, seed=20260725, tuning_frames=60, confirmation_frames=60)
        self.assertTrue(chosen.equals(repeat))
