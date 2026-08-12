"""NBLDPC7 R3 two-layer GF(32) decoder acceptance: EMS with the frozen
``nm=32`` (= q, so the exact full min-sum) as the single production schedule,
the exact FFT-QSPA small-field sum-product ORACLE (reusing the accepted
check-update semantics by identity) for equivalence, layer-0-first short
circuit (layer 1 never invoked, no verification), the conditional layer-1
prior provenance (Bob data + public model data + verified layer-0 output
only), noiseless and planted 1-2 error cases in both strata, deterministic
repeat, invalid boundaries, allocation and iteration caps, fail-closed
numerical cases, and no fallback to the oracle."""
from __future__ import annotations
import inspect
import numpy as np
import pytest
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v7_r3_long as long
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v7_r3_codebook as cb
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v7_r1a_long as r1a_long
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_qspa import nonbinary_syndrome

SEED = 2026080509


def _decode(bob, alice, p, max_iter=100, decoder=long.decode_nbldpc_v7_r3):
    manifest, matrices = cb.codebook()
    m = cb._CHECK_COUNTS[p]
    high, low = cb.split_vector(alice)
    field = GF2mField.create(32)
    syndrome0 = nonbinary_syndrome(matrices[(m, 0)], high, field)
    syndrome1 = nonbinary_syndrome(matrices[(m, 1)], low, field)
    return decoder(bob, syndrome0, syndrome1, manifest, matrices,
                   check_count=2 * m, p=p, max_iter=max_iter)


def _bruteforce_min_sum_check(extrinsics, coefficients, syndrome, field):
    """Independent exhaustive enumeration of the exact min-sum check update.

    In the scaled domain ``z_w = h_w x_w`` the outgoing message is
    ``m_v(x) = min over {z_w, w != v} of sum m_w(h_w^{-1} z_w) subject to
    ``XOR_w z_w = syndrome ^ h_v x``, normalised to the frozen clip bound.
    The ``scaled_w`` vectors are z-indexed, so the XOR constraint is the
    plain XOR of the enumerated z values."""
    q = field.q
    scaled = [message[_inv(q, int(coefficient))] for message, coefficient in zip(extrinsics, coefficients)]
    outgoing = []
    for target in range(len(coefficients)):
        others = [scaled[i] for i in range(len(scaled)) if i != target]
        message = []
        for symbol in range(q):
            target_z = field.mul(int(coefficients[target]), symbol)
            best = None
            for combo in np.ndindex(*((q,) * len(others))):
                xor_sum = 0
                total = 0.0
                for index, z in enumerate(combo):
                    xor_sum ^= int(z)
                    total += others[index][int(z)]
                if xor_sum == (syndrome ^ target_z):
                    best = float(total) if best is None else min(best, float(total))
            message.append(0.0 if best is None else best)
        vector = np.asarray(message, dtype=np.float64)
        outgoing.append(np.minimum(vector - float(vector.min()), long._COST_CLIP))
    return outgoing


def _inv(q, coefficient):
    field = GF2mField.create(q)
    return np.asarray([field.mul(field.inverse(coefficient), s) for s in range(q)], dtype=np.intp)


def _bruteforce_layer1_prior(low_words, high_words, decoded_high, q, p):
    """Independent enumeration of the conditional layer-1 law:
    ``P(alice_low = s) ∝ QSC_p((decoded_high << 5) | s, bob)`` with the
    accepted QSC mass (``1-p`` on the bob symbol, ``p/1023`` elsewhere)."""
    bob = tuple((int(h) << 5) | int(l) for h, l in zip(high_words, low_words))
    out = []
    for index in range(len(bob)):
        masses = []
        for s in range(q):
            candidate = (int(decoded_high[index]) << 5) | s
            masses.append(1.0 - p if candidate == bob[index] else p / 1023.0)
        total = sum(masses)
        out.append(np.asarray(masses, dtype=np.float64) / total)
    return np.asarray(out)


def test_public_signature_has_no_alice_truth_or_callback():
    names = list(inspect.signature(long.decode_nbldpc_v7_r3).parameters)
    assert not any(token in name.lower() for name in names for token in ("alice", "truth", "callback"))
    assert long._MAX_ITER == 100 and long._NM == 32 and long._Q == 32
    assert long._SCHEDULE == "flooding" and long._LAMBDA == 0.75
    assert long._CHECK_COUNTS == {0.20: 404, 0.30: 558}


def test_check_update_semantics_are_reused_by_identity():
    # the frozen small-field FFT-QSPA oracle reuses the ACCEPTED check-update
    # semantics by identity (oracle-tested exhaustively on GF(4)/GF(8) in the
    # R1A suite); production EMS never calls it.
    assert long.check_update_fft_qspa is r1a_long.check_update_fft_qspa


def test_production_runner_is_the_frozen_flooding_ems(monkeypatch):
    captured = {}
    kwdefaults = long.decode_nbldpc_v7_r3.__kwdefaults__
    def observed(*args, **kwargs):
        captured["kwargs"] = dict(kwargs)
        return {"status": "decode_failed", "iterations": 1}
    monkeypatch.setattr(long, "decode_nbldpc_v7_r3", observed)
    long.production_runner((0,) * 1024, (0,) * 404, (0,) * 404, {"q": 32},
                           {(404, 0): (0,), (404, 1): (0,)}, check_count=808, p=.20)
    assert captured["kwargs"]["check_count"] == 808 and captured["kwargs"]["p"] == 0.20
    assert captured["kwargs"].get("max_iter") is None
    assert long._MAX_ITER == 100 and long._MAX_ITER == kwdefaults["max_iter"]
    assert long._SCHEDULE == "flooding" and long._NM == 32


def test_min_plus_convolution_matches_bruteforce():
    rng = np.random.default_rng(SEED + 1)
    for degree in range(2, 5):
        left = rng.random(32) * 10.0
        right = rng.random(32) * 10.0
        result = long.min_plus_convolution(left, right)
        expected = np.asarray([min(left[u] + right[t ^ u] for u in range(32))
                               for t in range(32)], dtype=np.float64)
        assert np.allclose(result, expected)


def test_check_update_min_sum_matches_bruteforce_configurations():
    # EMS with nm=32 equals the exact full min-sum: the pairwise min-plus XOR
    # convolution of the other scaled messages is the exact configuration
    # minimum, verified against exhaustive enumeration for check degrees 2..4.
    field = GF2mField.create(32)
    rng = np.random.default_rng(SEED + 2)
    for degree in range(2, 5):
        messages = [rng.random(32) * 8.0 for _ in range(degree)]
        coefficients = [1 + int(rng.integers(1, 32)) for _ in range(degree)]
        syndrome = int(rng.integers(0, 32))
        got = long.check_update_min_sum(messages, coefficients, syndrome, field)
        assert got is not None
        expected = _bruteforce_min_sum_check(messages, coefficients, syndrome, field)
        for target in range(degree):
            assert np.allclose(got[target], expected[target], atol=1e-9)


def test_ems_and_fft_oracle_agree_on_noiseless_frames():
    for p, m in ((0.20, 404), (0.30, 558)):
        zero = (0,) * 1024
        ems = _decode(zero, zero, p)
        oracle = _decode(zero, zero, p, decoder=long.decode_nbldpc_v7_r3_fft_qspa)
        assert ems["status"] == "syndrome_consistent" and ems["syndrome_consistent"]
        assert oracle["status"] == "syndrome_consistent" and oracle["syndrome_consistent"]
        assert ems["decoded_symbols"] == zero == oracle["decoded_symbols"]
        assert ems["layer0_consistent"] and ems["layer1_consistent"] and ems["layer1_invoked"]
        assert 1 <= ems["iterations"] <= 100


def test_ems_and_fft_oracle_agree_on_planted_one_and_two_symbol_errors():
    manifest, matrices = cb.codebook()
    field = GF2mField.create(32)
    rng = np.random.default_rng(SEED)
    alice = tuple(int(x) for x in rng.integers(0, 1024, 1024))
    for p, m in ((0.20, 404), (0.30, 558)):
        for n_errors in (1, 2):
            bob = list(alice)
            for index in rng.choice(1024, size=n_errors, replace=False):
                bob[int(index)] ^= int(rng.integers(1, 1024))
            ems = _decode(tuple(bob), alice, p)
            oracle = _decode(tuple(bob), alice, p, decoder=long.decode_nbldpc_v7_r3_fft_qspa)
            assert ems["status"] == "syndrome_consistent", (p, n_errors)
            assert ems["decoded_symbols"] == alice
            assert oracle["status"] == "syndrome_consistent", (p, n_errors)
            assert oracle["decoded_symbols"] == alice


def test_deterministic_repeat():
    manifest, matrices = cb.codebook()
    field = GF2mField.create(32)
    syndrome0 = nonbinary_syndrome(matrices[(404, 0)], (0,) * 1024, field)
    syndrome1 = nonbinary_syndrome(matrices[(404, 1)], (0,) * 1024, field)
    first = long.decode_nbldpc_v7_r3((0,) * 1024, syndrome0, syndrome1, manifest, matrices,
                                     check_count=808, p=.20)
    second = long.decode_nbldpc_v7_r3((0,) * 1024, syndrome0, syndrome1, manifest, matrices,
                                      check_count=808, p=.20)
    assert first == second


def test_layer0_failure_short_circuits_before_layer1_and_verification(monkeypatch):
    # Deterministic contract test: a failed layer-0 result must never invoke
    # layer 1 (the conditional prior must never be computed) and must never
    # return reconstructed symbols for verification.
    manifest, matrices = cb.codebook()
    field = GF2mField.create(32)
    syndrome0 = nonbinary_syndrome(matrices[(404, 0)], (0,) * 1024, field)
    syndrome1 = nonbinary_syndrome(matrices[(404, 1)], (0,) * 1024, field)
    calls = {"layer1": 0, "priors": 0}
    def failed_layer0(words, syndrome, matrix, field, priors, max_iter):
        calls["layer1"] += 1
        return {"status": "decode_failed", "decoded": None, "iterations": 7}
    def forbidden_priors(low, high, decoded, q, p):
        calls["priors"] += 1
        raise AssertionError("layer-1 priors must not be computed after a layer-0 failure")
    monkeypatch.setattr(long, "_decode_layer_min_sum", failed_layer0)
    monkeypatch.setattr(long, "conditional_layer1_priors", forbidden_priors)
    result = long.decode_nbldpc_v7_r3((0,) * 1024, syndrome0, syndrome1, manifest, matrices,
                                      check_count=808, p=.20)
    assert result["status"] == "decode_failed"
    assert result["layer0_consistent"] is False and result["layer1_invoked"] is False
    assert result["decoded_symbols"] is None and calls["layer1"] == 1 and calls["priors"] == 0


def test_real_layer0_failure_short_circuits_on_random_frame():
    # Real-decoder short circuit: a full random frame (half the 10-bit symbols
    # wrong) never lets layer 0 converge within the frozen cap; layer 1 is
    # never invoked, no symbols are returned and the reason records the
    # short circuit.  Deterministic for the fixed seed.
    manifest, matrices = cb.codebook()
    field = GF2mField.create(32)
    rng = np.random.default_rng(SEED + 3)
    alice = tuple(int(x) for x in rng.integers(0, 1024, 1024))
    errors = tuple(int(x) for x in rng.integers(0, 1024, 1024))
    bob = tuple(int(a) ^ int(e) for a, e in zip(alice, errors))
    high, low = cb.split_vector(alice)
    syndrome0 = nonbinary_syndrome(matrices[(404, 0)], high, field)
    syndrome1 = nonbinary_syndrome(matrices[(404, 1)], low, field)
    result = long.decode_nbldpc_v7_r3(bob, syndrome0, syndrome1, manifest, matrices,
                                      check_count=808, p=.20, max_iter=1)
    assert result["status"] == "decode_failed" and result["iterations"] == 1
    assert result["reason"] == "layer0_failed_short_circuit"
    assert result["layer0_consistent"] is False and result["layer1_invoked"] is False
    assert result["decoded_symbols"] is None


def test_layer1_prior_provenance_matches_bruteforce_conditional():
    # Layer-1 priors are the exact conditional law of the low word given Bob's
    # two words and the VERIFIED layer-0 output under the frozen QSC model:
    # P(alice_low = s) ∝ QSC_p((decoded_high << 5) | s, bob).  The brute-force
    # enumeration below is independent of the closed formula.
    rng = np.random.default_rng(SEED + 4)
    for p in (0.20, 0.30):
        for n in (1, 7, 64):
            high = tuple(int(x) for x in rng.integers(0, 32, n))
            low = tuple(int(x) for x in rng.integers(0, 32, n))
            decoded = tuple(int(x) for x in rng.integers(0, 32, n))
            got = long.conditional_layer1_priors(low, high, decoded, 32, p)
            expected = _bruteforce_layer1_prior(low, high, decoded, 32, p)
            assert np.allclose(got, expected, atol=1e-12)


def test_layer1_prior_is_uniform_when_layer0_disagrees_with_bob_high():
    # When the verified layer-0 output differs from Bob's high word, every low
    # candidate carries the flat p/1023 mass (uniform): the honest degenerate
    # case of the conditional layer model.
    low = (3, 7, 0, 31)
    high = (1, 1, 1, 1)
    decoded = (0, 0, 0, 0)  # all disagree with Bob's high words
    prior = long.conditional_layer1_priors(low, high, decoded, 32, 0.20)
    assert np.allclose(prior, np.full((4, 32), 1.0 / 32.0), atol=1e-12)
    # when layer 0 agrees, the belief concentrates on Bob's low word.
    agreeing = long.conditional_layer1_priors(low, high, (1, 1, 1, 1), 32, 0.20)
    for index in range(4):
        assert agreeing[index, int(low[index])] > 0.5


def test_invalid_input_and_fail_closed_boundaries():
    manifest, matrices = cb.codebook()
    zero = (0,) * 1024
    syndrome0 = nonbinary_syndrome(matrices[(404, 0)], (0,) * 1024, GF2mField.create(32))
    syndrome1 = nonbinary_syndrome(matrices[(404, 1)], (0,) * 1024, GF2mField.create(32))
    assert long.decode_nbldpc_v7_r3(zero, syndrome0, syndrome1, manifest, matrices,
                                    check_count=807, p=.20)["status"] == "invalid_input"
    assert long.decode_nbldpc_v7_r3(zero, syndrome0, syndrome1, manifest, matrices,
                                    check_count=808, p=.30)["status"] == "invalid_input"
    assert long.decode_nbldpc_v7_r3(zero, syndrome0, syndrome1, manifest, matrices,
                                    check_count=808, p=.25)["status"] == "invalid_input"
    assert long.decode_nbldpc_v7_r3(zero, (0,) * 403, syndrome1, manifest, matrices,
                                    check_count=808, p=.20)["status"] == "invalid_input"
    assert long.decode_nbldpc_v7_r3(zero, syndrome0, (0,) * 403, manifest, matrices,
                                    check_count=808, p=.20)["status"] == "invalid_input"
    assert long.decode_nbldpc_v7_r3((0,) * 1023, syndrome0, syndrome1, manifest, matrices,
                                    check_count=808, p=.20)["status"] == "invalid_input"
    assert long.decode_nbldpc_v7_r3((0,) * 1025, syndrome0, syndrome1, manifest, matrices,
                                    check_count=808, p=.20)["status"] == "invalid_input"
    assert long.decode_nbldpc_v7_r3(tuple([1024] + [0] * 1023), syndrome0, syndrome1, manifest, matrices,
                                    check_count=808, p=.20)["status"] == "invalid_input"
    assert long.decode_nbldpc_v7_r3(zero, syndrome0, syndrome1, {"q": 512}, matrices,
                                    check_count=808, p=.20)["status"] == "unsupported_domain"
    forged = dict(manifest)
    forged["ordered_entries"] = [dict(e) for e in forged["ordered_entries"]]
    forged["ordered_entries"][0]["construction_seed_0"] = 1
    assert long.decode_nbldpc_v7_r3(zero, syndrome0, syndrome1, forged, matrices,
                                    check_count=808, p=.20)["status"] == "codebook_invalid"
    missing = {key: matrix for key, matrix in matrices.items() if key != (404, 1)}
    assert long.decode_nbldpc_v7_r3(zero, syndrome0, syndrome1, manifest, missing,
                                    check_count=808, p=.20)["status"] == "codebook_invalid"
    bad = {key: matrix for key, matrix in matrices.items()}
    bad[(404, 0)] = tuple(list(matrices[(404, 0)])[:403])
    assert long.decode_nbldpc_v7_r3(zero, syndrome0, syndrome1, manifest, bad,
                                    check_count=808, p=.20)["status"] == "codebook_invalid"


def test_allocation_cap_and_iteration_bounds(monkeypatch):
    manifest, matrices = cb.codebook()
    zero = (0,) * 1024
    syndrome0 = nonbinary_syndrome(matrices[(404, 0)], zero, GF2mField.create(32))
    syndrome1 = nonbinary_syndrome(matrices[(404, 1)], zero, GF2mField.create(32))
    assert long.decode_nbldpc_v7_r3(zero, syndrome0, syndrome1, manifest, matrices,
                                    check_count=808, p=.20, max_iter=101)["status"] == "aborted_resource_limit"
    assert long.decode_nbldpc_v7_r3(zero, syndrome0, syndrome1, manifest, matrices,
                                    check_count=808, p=.20, max_iter=0)["status"] == "aborted_resource_limit"
    monkeypatch.setattr(long, "_MAX_DENSE_BYTES", 1)
    result = long.decode_nbldpc_v7_r3(zero, syndrome0, syndrome1, manifest, matrices,
                                      check_count=808, p=.20)
    assert result["status"] == "aborted_resource_limit" and result["reason"] == "dense_message_storage"


def test_declared_dense_message_bytes_are_exact_for_the_two_layer_graph():
    declared = long.declared_dense_bytes()
    assert declared == 2 * (2 * 1024 + 2 * 3072) * 32 * 8
    assert declared == 4_194_304
    assert declared <= long._MAX_DENSE_BYTES == 8 * 1024 * 1024


def test_iteration_cap_returns_decode_failed_with_full_count():
    # A full-rate random frame is far beyond this development code's capacity:
    # layer 0 deterministically never converges within the probe cap and the
    # decoder stops with decode_failed and exactly max_iter layer-0 iterations.
    manifest, matrices = cb.codebook()
    field = GF2mField.create(32)
    rng = np.random.default_rng(SEED + 5)
    alice = tuple(int(x) for x in rng.integers(0, 1024, 1024))
    errors = tuple(int(x) for x in rng.integers(0, 1024, 1024))
    bob = tuple(int(a) ^ int(e) for a, e in zip(alice, errors))
    high, low = cb.split_vector(alice)
    syndrome0 = nonbinary_syndrome(matrices[(404, 0)], high, field)
    syndrome1 = nonbinary_syndrome(matrices[(404, 1)], low, field)
    result = long.decode_nbldpc_v7_r3(bob, syndrome0, syndrome1, manifest, matrices,
                                      check_count=808, p=.20, max_iter=2)
    assert result["status"] == "decode_failed" and result["iterations"] == 2
    assert result["reason"] == "layer0_failed_short_circuit"


def test_fail_closed_numerical_cases(monkeypatch):
    manifest, matrices = cb.codebook()
    zero = (0,) * 1024
    syndrome0 = nonbinary_syndrome(matrices[(404, 0)], zero, GF2mField.create(32))
    syndrome1 = nonbinary_syndrome(matrices[(404, 1)], zero, GF2mField.create(32))
    monkeypatch.setattr(long, "check_update_min_sum", lambda *args, **kwargs: None)
    result = long.decode_nbldpc_v7_r3(zero, syndrome0, syndrome1, manifest, matrices,
                                      check_count=808, p=.20)
    assert result["status"] == "decoder_error"
    monkeypatch.setattr(long, "_costs", lambda priors: np.full((1024, 32), np.nan))
    result = long.decode_nbldpc_v7_r3(zero, syndrome0, syndrome1, manifest, matrices,
                                      check_count=808, p=.20)
    assert result["status"] == "decoder_error"
    assert long._COST_CLIP == 100.0


def test_no_fallback_oracle_is_never_production(monkeypatch):
    # Production runs the frozen EMS only; the exact FFT-QSPA oracle is
    # test-only and is NEVER invoked as a fallback.
    def trap(*args, **kwargs):
        raise AssertionError("oracle decoder entered as a fallback")
    monkeypatch.setattr(long, "decode_nbldpc_v7_r3_fft_qspa", trap)
    manifest, matrices = cb.codebook()
    zero = (0,) * 1024
    syndrome0 = nonbinary_syndrome(matrices[(404, 0)], zero, GF2mField.create(32))
    syndrome1 = nonbinary_syndrome(matrices[(404, 1)], zero, GF2mField.create(32))
    result = long.production_runner(zero, syndrome0, syndrome1, manifest, matrices,
                                    check_count=808, p=.20)
    assert result["status"] == "syndrome_consistent"
