"""NBLDPC7 R2 decoder acceptance: layered FFT-QSPA at n=1024, reuse of the
accepted check-update semantics, noiseless and planted cases, deterministic
repeat, iteration and allocation caps, fail-closed numerical contracts, and
the single frozen layered schedule."""
from __future__ import annotations
import inspect
import numpy as np
import pytest
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v7_r2_long as long
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v7_r2_codebook as cb
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v7_r1a_long as r1a_long
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_qspa import (_normalise,
                                                                            nonbinary_syndrome,
                                                                            symbols_to_msb_bits)

SEED = 2026080407


def _decode(bob, alice, p, max_iter=100):
    manifest, matrices = cb.codebook()
    syndrome = nonbinary_syndrome(matrices[cb._CHECK_COUNTS[p]], alice, GF2mField.create(1024))
    return long.decode_nbldpc_v7_r2(bob, syndrome, manifest, matrices,
                                    check_count=cb._CHECK_COUNTS[p], p=p, max_iter=max_iter)


def test_public_signature_has_no_alice_truth_or_callback():
    names = list(inspect.signature(long.decode_nbldpc_v7_r2).parameters)
    assert not any(token in name.lower() for name in names for token in ("alice", "truth", "callback"))
    assert long._MAX_ITER == 100 and long._LAMBDA == 0.75
    assert long._SCHEDULE == "layered"
    assert long._CHECK_COUNTS == {0.20: 321, 0.30: 458}


def test_check_update_semantics_are_reused_by_identity():
    # the frozen R2 check update IS the accepted R1A check update (which is
    # oracle-tested exhaustively on GF(4)/GF(8) in the R1A suite).
    assert long.check_update_fft_qspa is r1a_long.check_update_fft_qspa


def test_production_runner_is_the_frozen_layered_schedule(monkeypatch):
    captured = {}
    kwdefaults = long.decode_nbldpc_v7_r2.__kwdefaults__
    def observed(*args, **kwargs):
        captured["kwargs"] = dict(kwargs)
        return {"status": "decode_failed", "iterations": 1}
    monkeypatch.setattr(long, "decode_nbldpc_v7_r2", observed)
    long.production_runner((0,) * 1024, (0,) * 321, {"q": 1024}, {321: (0,)}, check_count=321, p=.20)
    # The frozen production contract: layered FFT-QSPA with max_iter=100 is the
    # decode default (_MAX_ITER); production_runner forwards check_count/p and
    # never overrides max_iter, so the frozen 100-iteration cap applies.
    assert captured["kwargs"]["check_count"] == 321 and captured["kwargs"]["p"] == 0.20
    assert captured["kwargs"].get("max_iter") is None
    assert long._MAX_ITER == 100 and long._MAX_ITER == kwdefaults["max_iter"]
    assert long._SCHEDULE == "layered"


def test_noiseless_frames_decode_in_both_strata():
    manifest, matrices = cb.codebook()
    field = GF2mField.create(1024)
    for p, m in ((0.20, 321), (0.30, 458)):
        zero = (0,) * 1024
        syndrome = nonbinary_syndrome(matrices[m], zero, field)
        result = long.decode_nbldpc_v7_r2(zero, syndrome, manifest, matrices,
                                          check_count=m, p=p)
        assert result["status"] == "syndrome_consistent" and result["syndrome_consistent"]
        assert result["decoded_symbols"] == zero and 1 <= result["iterations"] <= 100


def test_planted_one_and_two_symbol_errors_are_corrected():
    manifest, matrices = cb.codebook()
    field = GF2mField.create(1024)
    rng = np.random.default_rng(SEED)
    alice = tuple(int(x) for x in rng.integers(0, 1024, 1024))
    for n_errors in (1, 2):
        bob = list(alice)
        for index in rng.choice(1024, size=n_errors, replace=False):
            bob[int(index)] ^= int(rng.integers(1, 1024))
        syndrome = nonbinary_syndrome(matrices[321], alice, field)
        result = long.decode_nbldpc_v7_r2(tuple(bob), syndrome, manifest, matrices,
                                          check_count=321, p=.20)
        assert result["status"] == "syndrome_consistent"
        assert result["decoded_symbols"] == alice


def test_deterministic_repeat_and_msb_symbol_mapping():
    manifest, matrices = cb.codebook()
    syndrome = nonbinary_syndrome(matrices[321], (0,) * 1024, GF2mField.create(1024))
    first = long.decode_nbldpc_v7_r2((0,) * 1024, syndrome, manifest, matrices, check_count=321, p=.20)
    second = long.decode_nbldpc_v7_r2((0,) * 1024, syndrome, manifest, matrices, check_count=321, p=.20)
    assert first == second
    bits = symbols_to_msb_bits((0, 1, 2, 1023), 1024)
    assert bits.tolist() == [0] * 10 + [0] * 9 + [1] + [0] * 8 + [1, 0] + [1] * 10
    assert len(symbols_to_msb_bits((0,) * 1024, 1024)) == 10240


def test_invalid_input_and_fail_closed_boundaries():
    manifest, matrices = cb.codebook()
    zero = (0,) * 1024
    syndrome = nonbinary_syndrome(matrices[321], zero, GF2mField.create(1024))
    assert long.decode_nbldpc_v7_r2(zero, syndrome, manifest, matrices, check_count=322, p=.20)["status"] == "invalid_input"
    assert long.decode_nbldpc_v7_r2(zero, syndrome, manifest, matrices, check_count=321, p=.30)["status"] == "invalid_input"
    assert long.decode_nbldpc_v7_r2(zero, syndrome, manifest, matrices, check_count=321, p=.25)["status"] == "invalid_input"
    assert long.decode_nbldpc_v7_r2(zero, (0,) * 320, manifest, matrices, check_count=321, p=.20)["status"] == "invalid_input"
    assert long.decode_nbldpc_v7_r2((0,) * 1023, syndrome, manifest, matrices, check_count=321, p=.20)["status"] == "invalid_input"
    assert long.decode_nbldpc_v7_r2((0,) * 1025, syndrome, manifest, matrices, check_count=321, p=.20)["status"] == "invalid_input"
    assert long.decode_nbldpc_v7_r2(tuple([1024] + [0] * 1023), syndrome, manifest, matrices,
                                    check_count=321, p=.20)["status"] == "invalid_input"
    assert long.decode_nbldpc_v7_r2(zero, syndrome, {"q": 512}, matrices, check_count=321, p=.20)["status"] == "unsupported_domain"
    forged = dict(manifest)
    forged["ordered_entries"] = [dict(e) for e in forged["ordered_entries"]]
    forged["ordered_entries"][0]["construction_seed"] = 1
    assert long.decode_nbldpc_v7_r2(zero, syndrome, forged, matrices, check_count=321, p=.20)["status"] == "codebook_invalid"
    assert long.decode_nbldpc_v7_r2(zero, syndrome, manifest, {321: matrices[321]}, check_count=321, p=.20)["status"] == "codebook_invalid"
    bad = {m: matrix for m, matrix in matrices.items()}
    bad[321] = tuple(list(matrices[321])[:320])
    assert long.decode_nbldpc_v7_r2(zero, syndrome, manifest, bad, check_count=321, p=.20)["status"] == "codebook_invalid"


def test_allocation_cap_and_iteration_bounds(monkeypatch):
    manifest, matrices = cb.codebook()
    zero = (0,) * 1024
    syndrome = nonbinary_syndrome(matrices[321], zero, GF2mField.create(1024))
    assert long.decode_nbldpc_v7_r2(zero, syndrome, manifest, matrices, check_count=321, p=.20,
                                    max_iter=101)["status"] == "aborted_resource_limit"
    assert long.decode_nbldpc_v7_r2(zero, syndrome, manifest, matrices, check_count=321, p=.20,
                                    max_iter=0)["status"] == "aborted_resource_limit"
    monkeypatch.setattr(long, "_MAX_DENSE_BYTES", 1)
    result = long.decode_nbldpc_v7_r2(zero, syndrome, manifest, matrices, check_count=321, p=.20)
    assert result["status"] == "aborted_resource_limit" and result["reason"] == "dense_message_storage"


def test_declared_dense_message_bytes_are_exact_for_the_frozen_graph():
    declared = long.declared_dense_bytes()
    assert declared == (2 * 1024 + 2 * 3072) * 1024 * 8
    assert declared == 67_108_864
    assert declared <= long._MAX_DENSE_BYTES == 80 * 1024 * 1024


def test_iteration_cap_returns_decode_failed_with_full_count():
    # A full-rate random frame is far beyond this development code's capacity
    # and deterministically never reaches syndrome consistency within the
    # probe iteration cap: the decoder must stop at exactly max_iter with
    # decode_failed.  (The probe uses max_iter=2 to keep the unit test fast;
    # the 100-iteration cap path is identical.)
    manifest, matrices = cb.codebook()
    rng = np.random.default_rng(SEED + 1)
    alice = tuple(int(x) for x in rng.integers(0, 1024, 1024))
    errors = tuple(int(x) for x in rng.integers(0, 1024, 1024))
    bob = tuple(int(a) ^ int(e) for a, e in zip(alice, errors))
    syndrome = nonbinary_syndrome(matrices[321], alice, GF2mField.create(1024))
    result = long.decode_nbldpc_v7_r2(bob, syndrome, manifest, matrices, check_count=321, p=.20,
                                      max_iter=2)
    assert result["status"] == "decode_failed" and result["iterations"] == 2
    assert result["reason"] == "iteration_limit"


def test_later_row_reads_a_message_written_by_an_earlier_row(monkeypatch):
    # Layered contract: row r+1 reads a message written by row r.
    manifest, matrices = cb.codebook()
    syndrome = nonbinary_syndrome(matrices[321], (0,) * 1024, GF2mField.create(1024))
    original = long.edge_extrinsic
    observations = []
    def observed(prior, variable_edges, messages, current):
        if current[0] > 0:
            previous = [messages[e].copy() for e in variable_edges if e[0] < current[0]]
            if previous:
                observations.append(previous)
        return original(prior, variable_edges, messages, current)
    monkeypatch.setattr(long, "edge_extrinsic", observed)
    result = long.decode_nbldpc_v7_r2((0,) * 1024, syndrome, manifest, matrices,
                                      check_count=321, p=.20, max_iter=1)
    assert result["status"] == "syndrome_consistent"
    uniform = np.full(1024, 1 / 1024)
    assert any(any(not np.allclose(message, uniform) for message in group) for group in observations)


def test_fail_closed_numerical_cases(monkeypatch):
    manifest, matrices = cb.codebook()
    syndrome = nonbinary_syndrome(matrices[321], (0,) * 1024, GF2mField.create(1024))
    assert _normalise(np.array([np.nan] + [0.0] * 1023)) is None
    assert _normalise(np.array([np.inf] + [0.0] * 1023)) is None
    assert _normalise(np.zeros(1024)) is None
    monkeypatch.setattr(long, "_normalise", lambda values: None)
    result = long.decode_nbldpc_v7_r2((0,) * 1024, syndrome, manifest, matrices,
                                      check_count=321, p=.20)
    assert result["status"] == "decoder_error"
