from __future__ import annotations

import copy
import hashlib

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir.codebook_v4 import (
    BLOCK_LENGTH, CANDIDATE_IDS, MAGIC, PLANE_IDS, ROW_COUNTS, candidate_manifest,
    canonical_matrix_bytes, generate_candidate, parse_matrix_bytes, structural_diagnostics,
    verify_candidate_manifest,
)


def test_all_candidates_are_deterministic_and_structurally_valid():
    for plane_id in PLANE_IDS:
        for candidate_id in CANDIDATE_IDS:
            first, trial = generate_candidate(plane_id, candidate_id)
            second, same_trial = generate_candidate(plane_id, candidate_id)
            assert trial == same_trial
            assert np.array_equal(first, second)
            assert first.shape == (ROW_COUNTS[plane_id], BLOCK_LENGTH)
            metrics = structural_diagnostics(first)
            assert metrics["rank"] == ROW_COUNTS[plane_id]
            assert (metrics["column_weight_min"], metrics["column_weight_max"]) == (3, 3)
            assert np.all(first[np.arange(ROW_COUNTS[plane_id]), np.arange(ROW_COUNTS[plane_id])] == 1)


def test_canonical_parser_rejects_header_length_value_and_plane_mutations():
    matrix, _ = generate_candidate(9, 0)
    raw = canonical_matrix_bytes(matrix, plane_id=9)
    assert raw[:len(MAGIC)] == MAGIC
    assert np.array_equal(parse_matrix_bytes(raw, plane_id=9), matrix)
    broken_value = raw[:len(MAGIC) + 8] + b"\x02" + raw[len(MAGIC) + 9:]
    for broken in (b"BAD" + raw[3:], raw + b"x", broken_value):
        with pytest.raises(ValueError):
            parse_matrix_bytes(broken, plane_id=9)
    with pytest.raises(ValueError):
        parse_matrix_bytes(raw, plane_id=8)


def test_complete_manifest_reconstructs_and_is_tamper_evident():
    manifest = candidate_manifest()
    assert len(manifest["candidates"]) == 40
    assert manifest["manifest_sha256"] == "a4f836bb6ae46cd277ae632c469e6155c1ec18d1ed687eb515e1a925d1d85556"
    assert manifest["manifest_sha256"] == hashlib.sha256(
        __import__("json").dumps({k: v for k, v in manifest.items() if k != "manifest_sha256"}, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    ).hexdigest()
    verify_candidate_manifest(manifest)
    broken = copy.deepcopy(manifest)
    broken["candidates"][0]["accepted_trial"] += 1
    with pytest.raises(ValueError):
        verify_candidate_manifest(broken)


def test_frozen_golden_matrix_hashes_detect_rng_or_call_order_drift():
    expected = {
        (0, 0): "8f6abb42bee69d8ea662583c4b33cc45d1fb364cd1613eac6e50242c7a6d8f71",
        (4, 2): "d25f0fb3108bfc4404945889df3cc2a4e44527f5d41b79a28d681e7a34293322",
        (9, 3): "6b57fba24cf4bfbd70b9684fd99a38734b215f9228af85a9c793d83df98bc219",
    }
    for (plane_id, candidate_id), digest in expected.items():
        matrix, _ = generate_candidate(plane_id, candidate_id)
        assert hashlib.sha256(canonical_matrix_bytes(matrix, plane_id=plane_id)).hexdigest() == digest


def test_plane_8_and_9_candidates_disclose_no_invalidating_low_weight_witnesses():
    for plane_id in (8, 9):
        for candidate_id in CANDIDATE_IDS:
            matrix, _ = generate_candidate(plane_id, candidate_id)
            metrics = structural_diagnostics(matrix)
            assert not metrics["weight_3_witnesses"]
            assert not metrics["weight_4_witnesses"]

