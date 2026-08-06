"""V10 error-domain FFT-QSPA decoder tests (additive; V10-40 scope, T0/T1).

Covers the log-domain coefficient-correct check step against the independent
V8 direct oracle (q=4 exhaustive-bounded, q=8 bounded, q=1024 sparse-support;
V8 is a test-only import), coefficient permutation identity, small acyclic
graph decodes with nonzero syndrome and non-unit edge coefficients at
q=4/q=8 (brute-force MAP oracle) and bounded q=1024 (syndrome identity +
reconstruction), error-domain reconstruction x_hat = y + e_hat, the
no-Alice-truth signature guard, NaN/Inf fail-closed, the RSS guard, the exact
iteration transcript, early syndrome success, and the max_iter bound.
"""
from __future__ import annotations

import inspect
import itertools
import math

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v10_fftqspa as fft
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v10_common as common
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v8_reference as ref

FIELD4 = GF2mField.create(4)
FIELD8 = GF2mField.create(8)
FIELD1024 = GF2mField.create(1024)

_ORACLE_TOL = 1e-9


def _random_normalized(rng: np.random.Generator, q: int) -> np.ndarray:
    vector = rng.random(q)
    return vector / vector.sum()


def _qsc_prior(q: int, p: float) -> np.ndarray:
    return common.qsc_channel_message(q, p)


def _log_of(vector: np.ndarray) -> np.ndarray:
    return np.log(np.maximum(vector, 1e-15))


# --------------------------------------------------------------------------- #
# T0: coefficient permutation + FWHT
# --------------------------------------------------------------------------- #


def test_fwht_batched_hand_computed_q4():
    vector = np.array([1.0, 2.0, 3.0, 4.0])
    out = fft.fwht_batched(vector)
    assert np.allclose(out, [10.0, -2.0, -4.0, 0.0], atol=1e-12)
    assert np.allclose(fft.fwht_batched(out) / 4.0, vector, atol=1e-12)


def test_coefficient_permutation_identity():
    """scaled[c (x) s] = msg[s] for every symbol s and nonzero coefficient c."""
    rng = np.random.default_rng(2026100211)
    for field in (FIELD4, FIELD8):
        message = _random_normalized(rng, field.q)
        for coefficient in range(1, field.q):
            scaled = fft._scale_log_by_coefficient(field, _log_of(message), coefficient)
            for symbol in range(field.q):
                assert abs(scaled[field.mul(coefficient, symbol)] - math.log(max(message[symbol], 1e-15))) < 1e-12


# --------------------------------------------------------------------------- #
# T0/T1: check step vs the V8 direct oracle
# --------------------------------------------------------------------------- #


def test_check_update_log_vs_oracle_q4_bounded_exhaustive():
    """Bounded q=4 exhaustive: all coefficient combos from {1,2,3} for dc=3,
    syndromes {0,1,3}, two message sets, every target."""
    message_sets = [
        [np.array([0.5, 0.25, 0.25, 0.0]), np.array([0.1, 0.2, 0.3, 0.4]),
         np.array([0.7, 0.1, 0.1, 0.1]), np.array([0.25, 0.25, 0.25, 0.25])],
        [np.array([0.8, 0.05, 0.1, 0.05]), np.array([0.2, 0.4, 0.2, 0.2]),
         np.array([0.6, 0.3, 0.05, 0.05]), np.array([0.1, 0.7, 0.1, 0.1])],
    ]
    comparisons = 0
    for coefficients in itertools.product((1, 2, 3), repeat=3):
        for syndrome in (0, 1, 3):
            for set_index, base_messages in enumerate(message_sets):
                messages = base_messages[:3]
                for target in range(3):
                    own = np.exp(fft.check_update_log(
                        [_log_of(m) for m in messages], list(coefficients),
                        target, syndrome, FIELD4))
                    oracle = ref.oracle_check_update_dense(
                        messages, list(coefficients), target, syndrome, FIELD4)
                    assert oracle is not None
                    assert np.max(np.abs(own - oracle)) < _ORACLE_TOL, (
                        coefficients, syndrome, set_index, target)
                    comparisons += 1
    assert comparisons == 27 * 3 * 2 * 3


def test_check_update_log_vs_oracle_q8_bounded():
    rng = np.random.default_rng(2026100212)
    comparisons = 0
    coefficient_sets = [[1] * 5, [1, 3, 7, 5, 1], [7, 1, 3, 5, 1]]
    for _ in range(6):
        dc = int(rng.integers(3, 6))
        messages = [_random_normalized(rng, 8) for _ in range(dc)]
        for coefficients in coefficient_sets:
            for syndrome in (0, 3, 7):
                for target in range(dc):
                    own = np.exp(fft.check_update_log(
                        [_log_of(m) for m in messages], coefficients[:dc],
                        target, syndrome, FIELD8))
                    oracle = ref.oracle_check_update_dense(
                        messages, coefficients[:dc], target, syndrome, FIELD8)
                    assert oracle is not None
                    assert np.max(np.abs(own - oracle)) < _ORACLE_TOL
                    comparisons += 1
    assert comparisons >= 6 * 3 * 3 * 3


def test_check_update_log_vs_oracle_q1024_sparse_support():
    rng = np.random.default_rng(2026100213)
    coefficient_sets = [[1] * 5, [1, 3, 7, 255, 1], [255, 1, 3, 7, 3]]
    comparisons = 0

    def sparse_message():
        support = np.arange(1024)[rng.random(1024) < 0.003]
        if len(support) < 2:
            support = np.array([0, 1])
        vector = np.zeros(1024)
        weights = rng.random(len(support)) + 0.1
        vector[support] = weights
        return vector / vector.sum()

    for _ in range(3):
        dc = int(rng.integers(3, 5))
        messages = [sparse_message() for _ in range(dc)]
        for coefficients in coefficient_sets:
            for syndrome in (0, 1, 1023):
                for target in range(dc):
                    own = np.exp(fft.check_update_log(
                        [_log_of(m) for m in messages], coefficients[:dc],
                        target, syndrome, FIELD1024))
                    oracle = ref.oracle_check_update_sparse(
                        messages, coefficients[:dc], target, syndrome, FIELD1024)
                    assert np.max(np.abs(own - oracle)) < _ORACLE_TOL
                    comparisons += 1
    assert comparisons >= 3 * 3 * 3 * 3


def test_check_update_log_fail_closed():
    good = [_log_of(np.array([0.5, 0.25, 0.25, 0.0])),
            _log_of(np.array([0.25, 0.25, 0.25, 0.25])),
            _log_of(np.array([0.7, 0.1, 0.1, 0.1]))]
    with pytest.raises(ValueError):
        fft.check_update_log(good, [1, 1, 1], 0, 0, object())
    with pytest.raises(ValueError):
        fft.check_update_log(good, [1, 1, 1], -1, 0, FIELD4)
    with pytest.raises(ValueError):
        fft.check_update_log(good, [1, 1], 0, 0, FIELD4)
    with pytest.raises(ValueError):
        fft.check_update_log(good, [1, 0, 1], 0, 0, FIELD4)
    with pytest.raises(ValueError):
        fft.check_update_log(good, [1, 1, 1], 0, 5, FIELD4)
    bad = [np.full(4, np.nan), good[1], good[2]]
    with pytest.raises(ValueError):
        fft.check_update_log(bad, [1, 1, 1], 0, 0, FIELD4)
    with pytest.raises(ValueError):
        fft.check_update_log(good[:1], [1], 0, 0, FIELD4)


# --------------------------------------------------------------------------- #
# T1: small acyclic graph decodes vs the brute-force MAP oracle
#
# The QSC prior is channel-symmetric, so nonzero syndromes often admit several
# equally-likely coset vectors (ties).  The decoder's hard decision is the
# per-variable argmax of the (tree-exact) beliefs, verified by the syndrome
# check; the oracle agreement is therefore asserted in two complementary ways:
# (a) the final beliefs equal the exact coset marginals from the V8
# brute-force oracle (belief propagation on a tree is exact marginalization),
# and (b) whenever the decoder reports success, its e_hat equals the oracle's
# MAP vector and satisfies the syndrome identity.
# --------------------------------------------------------------------------- #


def _chain_q4():
    """Chain tree: v0 - c0 - v1 - c1 - v2 with non-unit GF(4) coefficients."""
    matrix = [[1, 2, 0], [0, 3, 1]]
    return matrix


def _chain_q8():
    matrix = [[1, 3, 0], [0, 2, 5]]
    return matrix


def _oracle_marginals(field, matrix, syndrome, priors):
    result = ref.bruteforce_coset_map(field, matrix, syndrome, priors)
    n, q = len(priors), field.q
    marginals = np.zeros((n, q))
    for vector, mass in result["marginals"].items():
        for index in range(n):
            marginals[index, vector[index]] += mass
    return result, marginals


def test_decode_q4_chain_vs_bruteforce():
    p = 0.2
    matrix = _chain_q4()
    error_syndrome = [0, 1]
    y = [0, 0, 0]
    prior = _qsc_prior(4, p)
    result = fft.decode_fftqspa(prior, matrix, error_syndrome, FIELD4, max_iter=30, streak=5)
    assert result["status"] == fft.STATUS_SUCCESS
    priors = [prior.copy() for _ in range(3)]
    oracle, oracle_marginals = _oracle_marginals(FIELD4, matrix, error_syndrome, priors)
    assert oracle["map_symbols"] is not None
    assert tuple(result["e_hat"]) == oracle["map_symbols"]
    assert result["beliefs"] is not None
    for variable in range(3):
        assert np.max(np.abs(result["beliefs"][variable] - oracle_marginals[variable])) < 1e-9
    assert fft.syndrome_of(FIELD4, matrix, result["e_hat"]) == error_syndrome
    # error-domain reconstruction through the wrapper.
    s_x = list(np.bitwise_xor(error_syndrome, fft.syndrome_of(FIELD4, matrix, y)))
    wrapped = fft.decode_error_domain(y, matrix, s_x, p, FIELD4, max_iter=30, streak=5)
    assert wrapped["status"] == fft.STATUS_SUCCESS
    assert wrapped["x_hat"] == list(np.bitwise_xor(y, result["e_hat"]))
    assert wrapped["reconstruction_ok"] is True
    assert fft.syndrome_of(FIELD4, matrix, wrapped["x_hat"]) == s_x


def test_decode_q8_chain_vs_bruteforce():
    p = 0.2
    matrix = _chain_q8()
    error_syndrome = [0, 1]
    y = [0, 0, 0]
    prior = _qsc_prior(8, p)
    result = fft.decode_fftqspa(prior, matrix, error_syndrome, FIELD8, max_iter=30, streak=5)
    assert result["status"] == fft.STATUS_SUCCESS
    priors = [prior.copy() for _ in range(3)]
    oracle, oracle_marginals = _oracle_marginals(FIELD8, matrix, error_syndrome, priors)
    assert tuple(result["e_hat"]) == oracle["map_symbols"]
    for variable in range(3):
        assert np.max(np.abs(result["beliefs"][variable] - oracle_marginals[variable])) < 1e-9
    s_x = list(np.bitwise_xor(error_syndrome, fft.syndrome_of(FIELD8, matrix, y)))
    wrapped = fft.decode_error_domain(y, matrix, s_x, p, FIELD8, max_iter=30, streak=5)
    assert wrapped["status"] == fft.STATUS_SUCCESS
    assert wrapped["reconstruction_ok"] is True
    assert fft.syndrome_of(FIELD8, matrix, wrapped["x_hat"]) == s_x


def test_decode_converged_no_syndrome_still_exact_marginals():
    """On a tree the messages converge to the exact coset marginals even when
    the bit-wise hard decision is not in the coset — the decoder must then
    fail closed (converged_no_syndrome), never a false success."""
    p = 0.2
    matrix = _chain_q8()
    error_syndrome = [1, 2]   # bit-wise mode vector violates the syndrome
    prior = _qsc_prior(8, p)
    result = fft.decode_fftqspa(prior, matrix, error_syndrome, FIELD8, max_iter=30, streak=5)
    assert result["status"] == fft.STATUS_CONVERGED_NO_SYNDROME
    priors = [prior.copy() for _ in range(3)]
    _, oracle_marginals = _oracle_marginals(FIELD8, matrix, error_syndrome, priors)
    for variable in range(3):
        assert np.max(np.abs(result["beliefs"][variable] - oracle_marginals[variable])) < 1e-9
    assert fft.syndrome_of(FIELD8, matrix, result["e_hat"]) != error_syndrome


def test_decode_q1024_bounded_acyclic():
    """Bounded GF(1024) chain: nonzero syndrome, non-unit coefficients; verify
    the syndrome identity and the error-domain reconstruction (the brute-force
    oracle is bounded to q^n <= 4096 and cannot run here)."""
    p = 0.25
    matrix = [[7, 3, 0], [0, 255, 9]]
    error_syndrome = [13, 0]
    y = [1, 2, 3]
    prior = _qsc_prior(1024, p)
    result = fft.decode_fftqspa(prior, matrix, error_syndrome, FIELD1024, max_iter=30, streak=5)
    assert result["status"] == fft.STATUS_SUCCESS
    assert fft.syndrome_of(FIELD1024, matrix, result["e_hat"]) == error_syndrome
    s_x = list(np.bitwise_xor(error_syndrome, fft.syndrome_of(FIELD1024, matrix, y)))
    wrapped = fft.decode_error_domain(y, matrix, s_x, p, FIELD1024, max_iter=30, streak=5)
    assert wrapped["status"] == fft.STATUS_SUCCESS
    assert wrapped["x_hat"] == list(np.bitwise_xor(y, result["e_hat"]))
    assert wrapped["reconstruction_ok"] is True
    assert fft.syndrome_of(FIELD1024, matrix, wrapped["x_hat"]) == s_x


# --------------------------------------------------------------------------- #
# T1: guards, fail-closed, transcript
# --------------------------------------------------------------------------- #


def test_no_alice_truth_signature():
    for name in ("decode_fftqspa", "decode_error_domain"):
        parameters = inspect.signature(getattr(fft, name)).parameters
        assert "x" not in parameters, name
        assert "e" not in parameters, name


def test_decode_nan_inf_fail_closed():
    prior = _qsc_prior(4, 0.2)
    bad_prior = prior.copy()
    bad_prior[1] = np.nan
    matrix = [[1, 2, 0, 0], [0, 0, 3, 2]]
    result = fft.decode_fftqspa(bad_prior, matrix, [1, 2], FIELD4, max_iter=10)
    assert result["status"] == fft.STATUS_DECODE_FAILED
    assert result["e_hat"] is None


def test_decode_rss_guard():
    class _CapWatcher:
        cap_exceeded = True

    matrix = [[1, 2, 0, 0], [0, 0, 3, 2]]
    result = fft.decode_fftqspa(_qsc_prior(4, 0.2), matrix, [1, 2], FIELD4,
                                max_iter=20, rss_watcher=_CapWatcher())
    assert result["status"] == fft.STATUS_RESOURCE_ABORT


def test_decode_transcript_completeness():
    p = 0.2
    matrix = _chain_q4()
    error_syndrome = [0, 1]
    result = fft.decode_fftqspa(_qsc_prior(4, p), matrix, error_syndrome, FIELD4,
                                max_iter=30, streak=5)
    assert result["status"] == fft.STATUS_SUCCESS
    assert result["iterations"] == len(result["transcript"])
    for entry in result["transcript"]:
        assert set(entry) == {"iteration", "mean_entropy", "syndrome_ok", "e_hat_stable",
                              "e_hat"}
        assert isinstance(entry["mean_entropy"], float)
        assert 0.0 <= entry["mean_entropy"] <= 1.0 + 1e-9
        assert isinstance(entry["syndrome_ok"], bool)
        assert isinstance(entry["e_hat_stable"], bool)
    assert result["transcript"][-1]["syndrome_ok"] is True
    assert result["final_mean_entropy"] == result["transcript"][-1]["mean_entropy"]


def test_decode_early_syndrome_success():
    """Zero error: e_hat = 0 satisfies s_e = 0 immediately (iteration 1)."""
    matrix = [[1, 2, 0, 0], [0, 0, 3, 2]]
    result = fft.decode_fftqspa(_qsc_prior(4, 0.2), matrix, [0, 0], FIELD4,
                                max_iter=20, streak=3)
    assert result["status"] == fft.STATUS_SUCCESS
    assert result["iterations"] == 1
    assert result["e_hat"] == [0, 0, 0, 0]


def test_decode_max_iter_bound():
    """A nonzero syndrome that the zero-prior-decoding e_hat never satisfies,
    with a streak longer than max_iter -> max_iter_reached."""
    matrix = [[1, 2, 0, 0], [0, 0, 3, 2]]
    result = fft.decode_fftqspa(_qsc_prior(4, 0.2), matrix, [1, 2], FIELD4,
                                max_iter=3, streak=10)
    assert result["status"] == fft.STATUS_MAX_ITER
    assert result["iterations"] == 3
    assert len(result["transcript"]) == 3


def test_decode_error_domain_validation():
    matrix = [[1, 2, 0, 0], [0, 0, 3, 2]]
    with pytest.raises(ValueError):
        fft.decode_error_domain([0, 0, 0], matrix, [0, 0], 0.2, FIELD4, max_iter=5)  # y len mismatch
    with pytest.raises(ValueError):
        fft.decode_error_domain([0, 0, 0, 0], matrix, [0], 0.2, FIELD4, max_iter=5)  # s_x len mismatch
    with pytest.raises(ValueError):
        fft.decode_error_domain([0, 0, 0, 0], matrix, [0, 0], 0.2, FIELD4, max_iter=5, streak=0)
