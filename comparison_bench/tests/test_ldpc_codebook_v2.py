from __future__ import annotations

import copy
import os
import tempfile
import unittest
from pathlib import Path

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.codebook_v2 import (
    CANDIDATES_PER_PLANE, PREFIX_RATES, PREFIX_ROWS, codebook_filename,
    generate_master, materialize_selected_codebooks, probe_errors,
    screen_candidate, screening_manifest, verify_screening_manifest,
    verify_selected_codebooks,
)


class LdpcCodebookV2Test(unittest.TestCase):
    def test_candidate_is_deterministic_nested_and_structural(self):
        first, second = generate_master(0, 0), generate_master(0, 0)
        self.assertTrue(np.array_equal(first, second))
        candidate = screen_candidate(0, 0)
        self.assertTrue(candidate["valid"])
        self.assertEqual(candidate["selection_score"][-1], 0)
        for rate, rows in zip(PREFIX_RATES, PREFIX_ROWS):
            metrics = candidate["prefixes"][rate]["metrics"]
            self.assertEqual((metrics["rank"], metrics["zero_columns"], metrics["duplicate_columns"]), (rows, 0, 0))
            self.assertIn("probe_unique_syndrome_count", metrics)
            self.assertNotIn("probe_verified_successes", metrics)
            self.assertTrue(2 <= metrics["row_weight_min"] <= metrics["row_weight_max"] <= 8)
            self.assertTrue(1 <= metrics["column_weight_min"] <= metrics["column_weight_max"] <= 4)
            probe = probe_errors(0, rate)
            self.assertEqual((probe.shape, probe[:32].sum(axis=1).tolist(), probe[32:].sum(axis=1).tolist()), ((64, 64), [1] * 32, [2] * 32))

    def test_screening_manifest_is_complete_deterministic_and_tamper_evident(self):
        first, second = screening_manifest(), screening_manifest()
        self.assertEqual(first, second)
        self.assertEqual(len(first["planes"]), 10)
        self.assertTrue(all(len(row["candidates"]) == CANDIDATES_PER_PLANE for row in first["planes"]))
        verify_screening_manifest(first)
        broken = copy.deepcopy(first); broken["planes"][0]["selected_candidate_id"] = 99
        with self.assertRaises(ValueError):
            verify_screening_manifest(broken)

    def test_materialization_refuses_overwrite_and_verifies_hash_nesting_and_paths(self):
        if os.environ.get("FORMAL_IR_FILE_TESTS") != "1":
            self.skipTest("set FORMAL_IR_FILE_TESTS=1 outside the Windows sandbox ACL")
        with tempfile.TemporaryDirectory(dir=".") as temporary:
            root = Path(temporary) / "run"; result = materialize_selected_codebooks(root)
            verify_selected_codebooks(root, result)
            self.assertEqual(len(list((root / "codebooks").glob("*.hgf2v1"))), 40)
            with self.assertRaises(FileExistsError): materialize_selected_codebooks(root)
            traversal = copy.deepcopy(result); traversal["entries"][0]["filename"] = "../escape"
            with self.assertRaises(ValueError): verify_selected_codebooks(root, traversal)
            self.assertEqual(codebook_filename("r050", 0), "formal_v2_codebook_n64_r050_plane00.hgf2v1")
