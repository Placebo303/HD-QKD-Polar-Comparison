from __future__ import annotations

import csv
import importlib.util
import json
import unittest
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "experiments" / "run_real_polar_max_pie.py"
SPEC = importlib.util.spec_from_file_location("run_real_polar_max_pie_rate_test", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ArchivedRateAndNuisanceTests(unittest.TestCase):
  def test_archived_d4_bw20_nuisance_path_and_missing_duration_rate(self) -> None:
    sidecar = REPO_ROOT / "results" / "authoritative" / "e2e_20dB_fullgrid_pairing_v2_candidate_t15" / "sidecars" / "d4_bw20" / "blk0"
    self.assertTrue((sidecar / "sidecar_meta.json").is_file())
    nuisance = MODULE._canonical_nuisance_from_sidecar(sidecar)
    self.assertIsNotNone(nuisance["n_pairs_in_clean_frames"])
    self.assertIsNotNone(nuisance["n_pairs_in_ambiguous_frames"])
    self.assertGreater(float(nuisance["clean_pair_fraction"]), 0.0)

    # An unavailable effective rate must preserve the candidate/grid rate;
    # it must not silently become n_symbols / 5 seconds.
    self.assertEqual(
        MODULE._select_coincidence_rate(
            grid_rate=123.0, source_rate=456.0, effective_rate=float("nan")
        ),
        123.0,
    )


if __name__ == "__main__":
    unittest.main()
