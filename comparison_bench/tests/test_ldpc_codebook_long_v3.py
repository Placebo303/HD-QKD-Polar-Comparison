from __future__ import annotations

import copy
import hashlib
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.codebook_long_v3 import (
    BLOCK_LENGTHS, CANDIDATE_IDS, MAGIC, PLANE_IDS, STATUS, candidate_entry, candidate_manifest,
    canonical_matrix_bytes, generate_master, parse_matrix_bytes, prefix_rows,
    structural_diagnostics, verify_candidate_manifest,
)


def _actual_gf2_rank(matrix: np.ndarray) -> int:
    """Independent bit-packed Gaussian elimination for the required rank check."""
    basis: dict[int, int] = {}
    for row in np.packbits(matrix, axis=1, bitorder="big"):
        value = int.from_bytes(row.tobytes(), "big")
        while value:
            pivot = value.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = value
                break
            value ^= basis[pivot]
    return len(basis)


def _dense_cycle_proxy(matrix: np.ndarray) -> tuple[int, int | None, int]:
    """Independent dense definition from the frozen design."""
    h = np.asarray(matrix, dtype=np.int64)
    overlap = h.T @ h
    weights = h.sum(axis=0)
    cycles = 0
    values: list[int] = []
    weighted_values = 0
    for left in range(h.shape[1]):
        for right in range(left + 1, h.shape[1]):
            common = int(overlap[left, right])
            multiplicity = common * (common - 1) // 2
            cycles += multiplicity
            if common >= 2:
                value = max(int(weights[left]) - 2, 0) + max(int(weights[right]) - 2, 0)
                values.append(value)
                weighted_values += value * multiplicity
    return cycles, (min(values) if values else None), weighted_values


class LongCodebookV3Test(unittest.TestCase):
    def test_deterministic_prefixes_and_actual_rank_at_all_lengths(self):
        for n in BLOCK_LENGTHS:
            first = generate_master(n, 0, 0)
            self.assertTrue(np.array_equal(first, generate_master(n, 0, 0)))
            rows_by_prefix = prefix_rows(n)
            self.assertEqual(list(rows_by_prefix.values()), [n // 2, 5 * n // 8, 3 * n // 4, 7 * n // 8])
            previous_rows = 0
            for rows in rows_by_prefix.values():
                h = first[:rows]
                self.assertEqual(h.shape, (rows, n))
                if previous_rows:
                    self.assertTrue(np.array_equal(first[:previous_rows], h[:previous_rows]))
                previous_rows = rows
                self.assertEqual(_actual_gf2_rank(h), rows)
                metrics = structural_diagnostics(h)
                self.assertEqual((metrics["zero_columns"], metrics["duplicate_columns"]), (0, 0))
                self.assertTrue(2 <= metrics["row_weight_min"] <= metrics["row_weight_max"] <= 3)
                self.assertTrue(1 <= metrics["column_weight_min"] <= metrics["column_weight_max"] <= 5)
                self.assertEqual(metrics["ace_4cycle_proxy_definition"], "column_pair_extrinsic_degree_v1")

    def test_candidate_ids_change_construction_and_dense_proxy_matches(self):
        masters = [generate_master(256, 3, candidate) for candidate in CANDIDATE_IDS]
        hashes = {hashlib.sha256(canonical_matrix_bytes(master[:128])).hexdigest() for master in masters}
        self.assertEqual(len(hashes), len(CANDIDATE_IDS))
        h = masters[0][:128]
        cycles, ace_min, ace_sum = _dense_cycle_proxy(h)
        metrics = structural_diagnostics(h)
        self.assertEqual(metrics["four_cycles"], cycles)
        self.assertEqual(metrics["ace_4cycle_proxy_min"], ace_min)
        self.assertEqual(metrics["ace_4cycle_proxy_sum"], ace_sum)

    def test_canonical_parser_rejects_mutations(self):
        h = generate_master(256, 1, 2)[:128]
        raw = canonical_matrix_bytes(h)
        self.assertEqual(parse_matrix_bytes(raw).shape, h.shape)
        for broken in (b"BAD" + raw[3:], raw + b"x", raw[:14] + b"\x02" + raw[15:]):
            with self.assertRaises(ValueError):
                parse_matrix_bytes(broken)
        self.assertEqual(raw[:len(MAGIC)], MAGIC)

    def test_complete_tamper_evident_candidate_only_manifest_and_no_output_writes(self):
        manifest = candidate_manifest()
        self.assertEqual(manifest["status"], STATUS)
        self.assertEqual(len(manifest["candidates"]), len(BLOCK_LENGTHS) * len(PLANE_IDS) * len(CANDIDATE_IDS))
        self.assertTrue(all(len(row["prefixes"]) == 4 for row in manifest["candidates"]))
        verify_candidate_manifest(manifest)
        broken = copy.deepcopy(manifest)
        broken["candidates"][0]["prefixes"]["p050"]["m_checks"] += 1
        with self.assertRaises(ValueError):
            verify_candidate_manifest(broken)
        root = Path.cwd()
        before = sorted(path.name for path in root.iterdir())
        with patch("builtins.open", side_effect=AssertionError("unexpected file write")), \
             patch.object(Path, "open", side_effect=AssertionError("unexpected path open")), \
             patch.object(Path, "write_bytes", side_effect=AssertionError("unexpected write_bytes")), \
             patch.object(Path, "write_text", side_effect=AssertionError("unexpected write_text")):
            entry = candidate_entry(256, 0, 0)
            self.assertEqual(entry["n"], 256)
            self.assertEqual(canonical_matrix_bytes(generate_master(256, 0, 0)[:128])[:len(MAGIC)], MAGIC)
            self.assertEqual(candidate_manifest()["status"], STATUS)
        self.assertEqual(sorted(path.name for path in root.iterdir()), before)
