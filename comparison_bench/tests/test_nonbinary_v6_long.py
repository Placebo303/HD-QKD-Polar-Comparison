"""NBLDPC6 decoder acceptance: exhaustive GF(4)/GF(8) oracle, noiseless and
planted cases, syndrome orientation, deterministic repeat, iteration and
allocation caps, and fail-closed numerical contracts (A03/A04/A06)."""
from __future__ import annotations
import inspect
from itertools import product
import numpy as np
import pytest
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v6_long as long
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v6_codebook as cb
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_qspa import (_normalise,
                                                                           nonbinary_syndrome,
                                                                           symbols_to_msb_bits)


def _decode(bob, alice, check_count, p, max_iter=50):
    manifest, matrices = cb.codebook()
    syndrome = nonbinary_syndrome(matrices[check_count], alice, GF2mField.create(1024))
    return long.decode_nbldpc_v6_long(bob, syndrome, manifest, matrices,
                                      check_count=check_count, p=p, max_iter=max_iter)


def _interleave(assignments, target, s):
    out = list(assignments)
    out.insert(target, s)
    return out


def _row_dot(row, symbols, field):
    total = 0
    for c, s in zip(row, symbols):
        total = field.add(total, field.mul(c, s))
    return total


def _check_satisfied(coefficients, symbols, syndrome, field):
    return _row_dot(coefficients, symbols, field) == syndrome


# ---------------------------------------------------------------- oracle

def test_exhaustive_gf4_check_convolution_matches_bruteforce():
    field = GF2mField.create(4); q = 4
    for d in (3, 4):
        for coefficients in product(range(1, q), repeat=d):
            for syndrome in range(q):
                for target in range(d):
                    messages = [np.array([0.1 + 0.05 * ((s + k) % q) for s in range(q)]) for k in range(d)]
                    brute = np.array([
                        sum(np.prod([messages[i][x_i] for i, x_i in enumerate(_interleave(assignments, target, s))
                                     if i != target])
                            for assignments in product(range(q), repeat=d - 1)
                            if _check_satisfied(coefficients, _interleave(assignments, target, s), syndrome, field))
                        for s in range(q)], dtype=np.float64)
                    brute = brute / brute.sum()
                    got = long.check_update_fft_qspa(messages, list(coefficients), target, syndrome, field)
                    assert got is not None and np.allclose(got, brute)


def test_exhaustive_gf8_check_convolution_matches_bruteforce():
    field = GF2mField.create(8); q = 8
    for coefficients in product(range(1, q), repeat=3):
        for syndrome in range(q):
            for target in range(3):
                others = [i for i in range(3) if i != target]
                first, second = others
                messages = [np.array([0.2 + 0.1 * ((s + k) % q) for s in range(q)]) for k in range(3)]
                brute = np.array([
                    sum(messages[first][a] * messages[second][b] for a in range(q) for b in range(q)
                        if field.add(field.mul(coefficients[first], a), field.mul(coefficients[second], b))
                        == field.add(syndrome, field.mul(coefficients[target], s)))
                    for s in range(q)], dtype=np.float64)
                brute = brute / brute.sum()
                got = long.check_update_fft_qspa(messages, list(coefficients), target, syndrome, field)
                assert got is not None and np.allclose(got, brute)


def test_coefficient_permutation_and_field_oracle():
    for q in (4, 8):
        field = GF2mField.create(q)
        for c in range(1, q):
            perm = long._forward_permutation(q, c)
            inv = long._inverse_permutation(q, c)
            assert sorted(int(x) for x in perm) == list(range(q))  # bijection
            assert sorted(int(x) for x in inv) == list(range(q))  # bijection
            for y in range(q):
                # inv[y] is the unique x with c*x = y; perm and inv are inverses.
                assert field.mul(c, int(inv[y])) == y
                assert int(perm[int(inv[y])]) == y
        # exhaustive distributivity on the tiny field.
        for x in range(q):
            for y in range(q):
                for z in range(q):
                    assert field.mul(x, field.add(y, z)) == field.add(field.mul(x, y), field.mul(x, z))


def test_syndrome_orientation_matches_bruteforce():
    field = GF2mField.create(4)
    matrix = ((1, 2, 3, 0), (0, 3, 1, 2), (2, 0, 2, 1))
    for symbols in product(range(4), repeat=4):
        expected = tuple(_row_dot(row, symbols, field) for row in matrix)
        assert nonbinary_syndrome(matrix, symbols, field) == expected
        # linearity/orientation: H(x xor e) = H x xor H e.
        e = (1, 2, 0, 3)
        shifted = tuple(int(a) ^ int(b) for a, b in zip(symbols, e))
        assert nonbinary_syndrome(matrix, shifted, field) == tuple(
            field.add(a, b) for a, b in zip(nonbinary_syndrome(matrix, symbols, field),
                                            nonbinary_syndrome(matrix, e, field)))


def test_hard_decision_matches_exhaustive_posterior():
    field = GF2mField.create(4)
    messages = [np.array([0.4, 0.3, 0.2, 0.1]), np.array([0.1, 0.2, 0.3, 0.4])]
    coefficients = [2, 3]; syndrome = 1; target = 0
    posterior = np.array([
        sum(messages[1][b] for b in range(4)
            if field.add(field.mul(coefficients[0], s), field.mul(coefficients[1], b)) == syndrome)
        for s in range(4)], dtype=np.float64)
    posterior = posterior / posterior.sum()
    got = long.check_update_fft_qspa(messages, coefficients, target, syndrome, field)
    assert got is not None and int(np.argmax(got)) == int(np.argmax(posterior))
    assert np.allclose(got, posterior)


# ---------------------------------------------------------------- decoder core

def test_public_signature_has_no_alice_truth_or_callback():
    names = list(inspect.signature(long.decode_nbldpc_v6_long).parameters)
    assert not any(token in name.lower() for name in names for token in ("alice", "truth", "callback"))
    assert long._MAX_ITER == 50 and long._LAMBDA == 0.75


def test_noiseless_frames_decode_in_both_strata():
    manifest, matrices = cb.codebook()
    for check_count, p in ((320, .20), (480, .30)):
        zero = (0,) * 1024
        syndrome = nonbinary_syndrome(matrices[check_count], zero, GF2mField.create(1024))
        result = long.decode_nbldpc_v6_long(zero, syndrome, manifest, matrices,
                                            check_count=check_count, p=p)
        assert result["status"] == "syndrome_consistent" and result["syndrome_consistent"]
        assert result["decoded_symbols"] == zero and 1 <= result["iterations"] <= 50


def test_planted_one_and_two_symbol_errors_are_corrected():
    rng = np.random.default_rng(2026080277)
    for check_count, p in ((320, .20), (480, .30)):
        alice = tuple(int(x) for x in rng.integers(0, 1024, 1024))
        for n_errors in (1, 2):
            bob = list(alice)
            for index in rng.choice(1024, size=n_errors, replace=False):
                bob[int(index)] ^= int(rng.integers(1, 1024))
            result = _decode(tuple(bob), alice, check_count, p)
            assert result["status"] == "syndrome_consistent"
            assert result["decoded_symbols"] == alice


def test_deterministic_repeat_and_msb_symbol_mapping():
    manifest, matrices = cb.codebook()
    syndrome = nonbinary_syndrome(matrices[320], (0,) * 1024, GF2mField.create(1024))
    first = long.decode_nbldpc_v6_long((0,) * 1024, syndrome, manifest, matrices, check_count=320, p=.20)
    second = long.decode_nbldpc_v6_long((0,) * 1024, syndrome, manifest, matrices, check_count=320, p=.20)
    assert first == second
    bits = symbols_to_msb_bits((0, 1, 2, 1023), 1024)
    assert bits.tolist() == [0] * 10 + [0] * 9 + [1] + [0] * 8 + [1, 0] + [1] * 10
    assert len(symbols_to_msb_bits((0,) * 1024, 1024)) == 10240


def test_invalid_input_and_fail_closed_boundaries():
    manifest, matrices = cb.codebook()
    zero = (0,) * 1024
    syndrome = nonbinary_syndrome(matrices[320], zero, GF2mField.create(1024))
    assert long.decode_nbldpc_v6_long(zero, syndrome, manifest, matrices, check_count=320, p=.30)["status"] == "invalid_input"
    assert long.decode_nbldpc_v6_long(zero, syndrome, manifest, matrices, check_count=480, p=.20)["status"] == "invalid_input"
    assert long.decode_nbldpc_v6_long(zero, (0,) * 319, manifest, matrices, check_count=320, p=.20)["status"] == "invalid_input"
    assert long.decode_nbldpc_v6_long((0,) * 1023, syndrome, manifest, matrices, check_count=320, p=.20)["status"] == "invalid_input"
    assert long.decode_nbldpc_v6_long((0,) * 1025, syndrome, manifest, matrices, check_count=320, p=.20)["status"] == "invalid_input"
    assert long.decode_nbldpc_v6_long(tuple([1024] + [0] * 1023), syndrome, manifest, matrices, check_count=320, p=.20)["status"] == "invalid_input"
    assert long.decode_nbldpc_v6_long(zero, syndrome, {"q": 512}, matrices, check_count=320, p=.20)["status"] == "unsupported_domain"
    forged = dict(manifest); forged["ordered_entries"] = forged["ordered_entries"][:1]
    assert long.decode_nbldpc_v6_long(zero, syndrome, forged, matrices, check_count=320, p=.20)["status"] == "codebook_invalid"
    assert long.decode_nbldpc_v6_long(zero, syndrome, manifest, {320: matrices[320][:319]}, check_count=320, p=.20)["status"] == "codebook_invalid"


def test_allocation_cap_and_iteration_bounds(monkeypatch):
    manifest, matrices = cb.codebook()
    zero = (0,) * 1024
    syndrome = nonbinary_syndrome(matrices[320], zero, GF2mField.create(1024))
    assert long.decode_nbldpc_v6_long(zero, syndrome, manifest, matrices, check_count=320, p=.20, max_iter=51)["status"] == "aborted_resource_limit"
    assert long.decode_nbldpc_v6_long(zero, syndrome, manifest, matrices, check_count=320, p=.20, max_iter=0)["status"] == "aborted_resource_limit"
    monkeypatch.setattr(long, "_MAX_DENSE_BYTES", 1)
    result = long.decode_nbldpc_v6_long(zero, syndrome, manifest, matrices, check_count=320, p=.20)
    assert result["status"] == "aborted_resource_limit" and result["reason"] == "dense_message_storage"


def test_declared_dense_message_bytes_are_exact_for_the_frozen_graph():
    declared = long._declared_dense_bytes(1024, 2048, 1024)
    assert declared == (2 * 1024 + 2 * 2048) * 1024 * 8
    assert declared <= 64 * 1024 * 1024


def test_50_iteration_cap_returns_decode_failed_with_full_count():
    # A full-rate random frame is far beyond this development code's capacity
    # and deterministically never reaches syndrome consistency: the decoder
    # must stop at exactly 50 iterations with decode_failed.
    manifest, matrices = cb.codebook()
    rng = np.random.default_rng(2026080242)
    alice = tuple(int(x) for x in rng.integers(0, 1024, 1024))
    errors = tuple(int(x) for x in rng.integers(0, 1024, 1024))
    bob = tuple(int(a) ^ int(e) for a, e in zip(alice, errors))
    syndrome = nonbinary_syndrome(matrices[320], alice, GF2mField.create(1024))
    result = long.decode_nbldpc_v6_long(bob, syndrome, manifest, matrices, check_count=320, p=.20)
    assert result["status"] == "decode_failed" and result["iterations"] == 50
    assert result["reason"] == "iteration_limit"


def test_fail_closed_numerical_cases(monkeypatch):
    manifest, matrices = cb.codebook()
    syndrome = nonbinary_syndrome(matrices[320], (0,) * 1024, GF2mField.create(1024))
    # Normalization helpers reject non-finite / non-positive mass.
    assert _normalise(np.array([np.nan] + [0.0] * 1023)) is None
    assert _normalise(np.array([np.inf] + [0.0] * 1023)) is None
    assert _normalise(np.zeros(1024)) is None
    assert _normalise(np.array([-1e-9] + [1e-9] * 1023)) is None
    valid = np.full(1024, 1 / 1024); norm = _normalise(valid)
    assert norm is not None and np.allclose(norm.sum(), 1.0)
    # Forcing the normalization seam to fail closes the decoder as decoder_error.
    monkeypatch.setattr(long, "_normalise", lambda values: None)
    result = long.decode_nbldpc_v6_long((0,) * 1024, syndrome, manifest, matrices, check_count=320, p=.20)
    assert result["status"] == "decoder_error"


def test_later_row_reads_a_message_written_by_an_earlier_row(monkeypatch):
    manifest, matrices = cb.codebook()
    syndrome = nonbinary_syndrome(matrices[320], (0,) * 1024, GF2mField.create(1024))
    original = long.edge_extrinsic
    observations = []
    def observed(prior, variable_edges, messages, current):
        if current[0] > 0:
            previous = [messages[e].copy() for e in variable_edges if e[0] < current[0]]
            if previous:
                observations.append(previous)
        return original(prior, variable_edges, messages, current)
    monkeypatch.setattr(long, "edge_extrinsic", observed)
    result = long.decode_nbldpc_v6_long((0,) * 1024, syndrome, manifest, matrices, check_count=320, p=.20, max_iter=1)
    assert result["status"] == "syndrome_consistent"
    uniform = np.full(1024, 1 / 1024)
    assert any(any(not np.allclose(message, uniform) for message in group) for group in observations)
