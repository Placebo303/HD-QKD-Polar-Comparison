from __future__ import annotations

import inspect
from copy import deepcopy

import pytest

from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v2
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_codebook import build_nonbinary_codebook_family
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_qspa import nonbinary_syndrome
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_v2 import (CANDIDATE_IDS, build_nbldpc_v2_codebook,
    decode_nbldpc_v2, verify_nbldpc_v2_codebook)


def test_qc48_reconstructs_factorization_round_permutation_rotation_prefixes_alpha_rank_and_cycles():
    manifest, matrices = build_nbldpc_v2_codebook()
    again, again_matrices = build_nbldpc_v2_codebook()
    assert manifest == again and matrices == again_matrices
    assert len(manifest["round_permutation"]) == 15 and len(manifest["selected_rounds"]) == len(manifest["rotation_vector"]) == 6
    assert manifest["alpha_power_48"] != 1
    factorization = nonbinary_v2._factorization()
    assert len(factorization) == 15 and {edge for matching in factorization for edge in matching} == {
        (left, right) for left in range(16) for right in range(left + 1, 16)
    }
    pairs = [tuple(pair) for pair in manifest["selected_information_pairs"]]
    assert len(set(pairs)) == 48 and all(set(pairs[row]).isdisjoint(pairs[(row + 1) % 48]) for row in range(48))
    assert all(sum(vertex in pair for pair in pairs) == 6 for vertex in range(16))
    assert [entry["check_count"] for entry in manifest["ordered_entries"]] == [24, 32, 40, 48]
    assert all(entry["rank"] == entry["check_count"] and entry["cycle_count"] == 0 for entry in manifest["ordered_entries"])
    assert verify_nbldpc_v2_codebook(manifest, matrices)["status"] == "ok"


def test_qc48_verifier_rejects_tamper():
    manifest, matrices = build_nbldpc_v2_codebook(); bad = deepcopy(manifest); bad["alpha_power_48"] = 1
    assert verify_nbldpc_v2_codebook(bad, matrices)["status"] == "codebook_invalid"


def test_fixed_seed_rejects_alternate_build_and_manifest_seed():
    with pytest.raises(ValueError, match="fixed"):
        build_nbldpc_v2_codebook(construction_seed=7)
    manifest, matrices = build_nbldpc_v2_codebook()
    alternate = deepcopy(manifest); alternate["construction_seed"] = 7
    assert verify_nbldpc_v2_codebook(alternate, matrices)["status"] == "codebook_invalid"
    result = decode_nbldpc_v2(CANDIDATE_IDS[1], (0,) * 64, (0,) * 24, alternate, matrices, check_count=24, p=.2)
    assert result["status"] == "codebook_invalid" and result["candidate_id"] == CANDIDATE_IDS[1]


def test_candidates_are_exact_public_input_only_and_bounded():
    assert len(CANDIDATE_IDS) == 4
    assert not any(word in name.lower() for name in inspect.signature(decode_nbldpc_v2).parameters for word in ("alice", "truth", "callback"))
    manifest, matrices = build_nbldpc_v2_codebook(); zero = (0,) * 64
    syndrome = nonbinary_syndrome(matrices[24], zero, GF2mField.create(1024))
    for candidate in CANDIDATE_IDS[1:]:
        result = decode_nbldpc_v2(candidate, zero, syndrome, manifest, matrices, check_count=24, p=.2, max_iter=1)
        assert result["status"] == "syndrome_consistent"
    assert decode_nbldpc_v2(CANDIDATE_IDS[1], zero, syndrome, manifest, matrices, check_count=24, p=.2, max_iter=21)["status"] == "aborted_resource_limit"


def test_control_identity_and_decoder_numeric_resource_fail_closed(monkeypatch):
    control_manifest, control_matrices = build_nonbinary_codebook_family(1024)
    zero = (0,) * 64
    syndrome = nonbinary_syndrome(control_matrices[16], zero, GF2mField.create(1024))
    control = decode_nbldpc_v2(CANDIDATE_IDS[0], zero, syndrome, control_manifest, control_matrices, check_count=16, p=.2, max_iter=1)
    assert control["candidate_id"] == CANDIDATE_IDS[0] and control["status"] == "syndrome_consistent"
    manifest, matrices = build_nbldpc_v2_codebook()
    monkeypatch.setattr(nonbinary_v2, "_MAX_BYTES", 1)
    assert decode_nbldpc_v2(CANDIDATE_IDS[1], zero, (0,) * 24, manifest, matrices, check_count=24, p=.2)["status"] == "aborted_resource_limit"
    monkeypatch.setattr(nonbinary_v2, "_MAX_BYTES", 16 * 1024 * 1024)
    monkeypatch.setattr(nonbinary_v2, "_normalise", lambda _: None)
    assert decode_nbldpc_v2(CANDIDATE_IDS[1], zero, (0,) * 24, manifest, matrices, check_count=24, p=.2)["status"] == "decoder_error"


def test_decoder_call_time_cap_fails_closed(monkeypatch):
    manifest, matrices = build_nbldpc_v2_codebook()
    ticks = iter((0.0, 21.0))
    monkeypatch.setattr(nonbinary_v2.time, "monotonic", lambda: next(ticks, 21.0))
    result = decode_nbldpc_v2(CANDIDATE_IDS[1], (0,) * 64, (0,) * 24, manifest, matrices, check_count=24, p=.2)
    assert result["status"] == "aborted_resource_limit" and result["reason"] == "decoder_call_seconds"


def test_control_time_cap_and_every_known_candidate_result_binds_identity(monkeypatch):
    monkeypatch.setattr(nonbinary_v2, "decode_nonbinary_fft_qspa", lambda *args, **kwargs: {"status": "syndrome_consistent", "iterations": 1})
    ticks = iter((0.0, 21.0))
    monkeypatch.setattr(nonbinary_v2.time, "monotonic", lambda: next(ticks, 21.0))
    timed = decode_nbldpc_v2(CANDIDATE_IDS[0], (0,) * 64, (0,) * 16, {}, {}, check_count=16, p=.2)
    assert timed["status"] == "aborted_resource_limit" and timed["candidate_id"] == CANDIDATE_IDS[0]
    manifest, matrices = build_nbldpc_v2_codebook()
    invalid = decode_nbldpc_v2(CANDIDATE_IDS[1], (0,) * 64, (0,) * 24, manifest, matrices, check_count=25, p=.2)
    resource = decode_nbldpc_v2(CANDIDATE_IDS[2], (0,) * 64, (0,) * 24, manifest, matrices, check_count=24, p=.2, max_iter=21)
    numerical = decode_nbldpc_v2(CANDIDATE_IDS[3], (0,) * 64, (0,) * 24, manifest, matrices, check_count=24, p=float("nan"))
    assert [row["candidate_id"] for row in (invalid, resource, numerical)] == list(CANDIDATE_IDS[1:])
    unknown = decode_nbldpc_v2("unknown", (), (), {}, {}, check_count=0, p=.2)
    assert unknown["status"] == "invalid_input" and unknown["supplied_candidate_id"] == "unknown"


def test_qc48_decoder_fails_closed_for_invalid_codebook():
    manifest, matrices = build_nbldpc_v2_codebook(); result = decode_nbldpc_v2(CANDIDATE_IDS[1], (0,) * 64, (0,) * 24, {**manifest, "manifest_id": "0" * 64}, matrices, check_count=24, p=.2)
    assert result["status"] == "codebook_invalid"
