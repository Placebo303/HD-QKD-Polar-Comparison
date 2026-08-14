"""V9 full-vector GF(1024) MC-DE kernel tests (additive; V9-10 scope).

Covers the own batched WHT against a hand-computed q=4 case, the
coefficient-correct check convolution against the independent V8 direct
oracle (q=4 exhaustive, q=8 >= 40, q=32 >= 20, q=1024 bounded dense and
sparse-support; frozen tolerance 1e-9), deterministic multi-seed MC-DE runs,
entropy math, fail-closed boundaries, and the no-production-import boundary
(V8 is a test-only oracle; no V1-V7 / qspa / decoder / production import).
"""
from __future__ import annotations

import itertools
import math
import re
import types

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v9_mcde as de
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v9_common as common
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v8_reference as ref

FIELD4 = GF2mField.create(4)
FIELD8 = GF2mField.create(8)
FIELD32 = GF2mField.create(32)
FIELD1024 = GF2mField.create(1024)

# Frozen tolerance for the scalable FFT route vs the independent direct oracle.
_ORACLE_TOL = 1e-9

V9_MODULE_PATHS = {
    "mcde": "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v9_mcde.py",
    "common": "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v9_common.py",
}


def _random_normalized(rng: np.random.Generator, q: int) -> np.ndarray:
    vector = rng.random(q)
    return vector / vector.sum()


def _rho_from_concentrated(conc: dict) -> dict[int, float]:
    return {int(conc["dc_lo"]): conc["w_lo"]} if conc["w_hi"] <= 0.0 else {
        int(conc["dc_lo"]): conc["w_lo"], int(conc["dc_hi"]): conc["w_hi"]}


def _q4_config():
    lam = {2: 0.5, 3: 0.5}
    rho = _rho_from_concentrated(common.concentrated_check_distribution(0.5, lam))
    return lam, rho


# --------------------------------------------------------------------------- #
# 1. WHT kernel
# --------------------------------------------------------------------------- #


def test_fwht_batched_hand_computed_q4():
    vector = np.array([1.0, 2.0, 3.0, 4.0])
    out = de.fwht_batched(vector)
    assert np.allclose(out, [10.0, -2.0, -4.0, 0.0], atol=1e-12)
    assert np.allclose(de.fwht_batched(out) / 4.0, vector, atol=1e-12)


def test_fwht_batched_vectorized_over_leading_axes():
    rng = np.random.default_rng(2026090101)
    batch = np.stack([rng.random(8) for _ in range(5)])       # (5, 8)
    for row in range(5):
        assert np.allclose(de.fwht_batched(batch)[row],
                           de.fwht_batched(batch[row]), atol=1e-12)
    tensor = rng.random((2, 3, 4))
    flat = de.fwht_batched(tensor)
    for a in range(2):
        for b in range(3):
            assert np.allclose(flat[a, b], de.fwht_batched(tensor[a, b]), atol=1e-12)
    with pytest.raises(ValueError):
        de.fwht_batched(np.array([1.0, 2.0, 3.0]))            # not a power of two
    with pytest.raises(ValueError):
        de.fwht_batched(np.array([1.0, np.nan, 2.0, 3.0]))


# --------------------------------------------------------------------------- #
# 2. coefficient-correct check convolution vs the V8 direct oracle
# --------------------------------------------------------------------------- #


def test_check_update_fft_vs_oracle_exhaustive_q4():
    """Exhaustive q=4: all coefficient combos from {1,2,3} for dc=3 and dc=4,
    syndromes 0..3, three deterministic message sets, every target; dc=5
    bounded (two coefficient sets, every target, all syndromes)."""
    message_sets = [
        [np.array([0.5, 0.25, 0.25, 0.0]), np.array([0.1, 0.2, 0.3, 0.4]),
         np.array([0.7, 0.1, 0.1, 0.1]), np.array([0.25, 0.25, 0.25, 0.25])],
        [np.array([0.8, 0.05, 0.1, 0.05]), np.array([0.2, 0.4, 0.2, 0.2]),
         np.array([0.6, 0.3, 0.05, 0.05]), np.array([0.1, 0.7, 0.1, 0.1])],
        [np.array([0.34, 0.22, 0.31, 0.13]), np.array([0.52, 0.14, 0.09, 0.25]),
         np.array([0.07, 0.61, 0.23, 0.09]), np.array([0.44, 0.19, 0.28, 0.09])],
    ]
    comparisons = 0
    for dc in (3, 4):
        for coefficients in itertools.product((1, 2, 3), repeat=dc):
            for syndrome in range(4):
                for set_index, base_messages in enumerate(message_sets):
                    messages = base_messages[:dc]
                    for target in range(dc):
                        fft = de.check_update_fft(messages, list(coefficients),
                                                  target, syndrome, FIELD4)
                        oracle = ref.oracle_check_update_dense(
                            messages, list(coefficients), target, syndrome, FIELD4)
                        assert oracle is not None
                        assert np.max(np.abs(fft - oracle)) < _ORACLE_TOL, (
                            dc, coefficients, syndrome, set_index, target)
                        comparisons += 1
    for coefficients in ([1, 2, 3, 2, 1], [3, 1, 1, 3, 2]):
        for syndrome in range(4):
            for target in range(5):
                messages5 = message_sets[0][:4] + [message_sets[0][0]]
                fft = de.check_update_fft(messages5, list(coefficients),
                                          target, syndrome, FIELD4)
                oracle = ref.oracle_check_update_dense(
                    messages5, list(coefficients), target, syndrome, FIELD4)
                assert oracle is not None
                assert np.max(np.abs(fft - oracle)) < _ORACLE_TOL
                comparisons += 1
    assert comparisons == (27 * 4 * 3 * 3) + (81 * 4 * 3 * 4) + (2 * 4 * 5)


def test_check_update_fft_vs_oracle_bounded_q8():
    """Bounded q=8: >= 40 seeded random cases, dc=3..5, mixed coefficient sets
    (incl. permutations of {1,3,7,5}), syndromes 0 and nonzero, every target."""
    rng = np.random.default_rng(2026090102)
    comparisons = 0
    coefficient_sets = [[1] * 5, [1, 3, 7, 5, 1], [7, 1, 3, 5, 1], [5, 7, 3, 1, 3]]
    for _ in range(12):
        dc = int(rng.integers(3, 6))
        messages = [_random_normalized(rng, 8) for _ in range(dc)]
        for coefficients in coefficient_sets:
            for syndrome in (0, 3, 7):
                for target in range(dc):
                    fft = de.check_update_fft(messages, coefficients[:dc],
                                              target, syndrome, FIELD8)
                    oracle = ref.oracle_check_update_dense(
                        messages, coefficients[:dc], target, syndrome, FIELD8)
                    assert oracle is not None
                    assert np.max(np.abs(fft - oracle)) < _ORACLE_TOL
                    comparisons += 1
    assert comparisons >= 40


def test_check_update_fft_vs_oracle_bounded_q32():
    """Bounded q=32: >= 20 seeded random cases, dc=3..5, mixed coefficient
    sets, syndromes incl. nonzero, every target."""
    rng = np.random.default_rng(2026090103)
    comparisons = 0
    coefficient_sets = [[1] * 5, [1, 3, 7, 5, 1], [7, 1, 3, 5, 1], [5, 7, 3, 1, 3]]
    for _ in range(8):
        dc = int(rng.integers(3, 6))
        messages = [_random_normalized(rng, 32) for _ in range(dc)]
        for coefficients in coefficient_sets:
            for syndrome in (0, 13, 31):
                for target in range(dc):
                    fft = de.check_update_fft(messages, coefficients[:dc],
                                              target, syndrome, FIELD32)
                    oracle = ref.oracle_check_update_dense(
                        messages, coefficients[:dc], target, syndrome, FIELD32)
                    assert oracle is not None
                    assert np.max(np.abs(fft - oracle)) < _ORACLE_TOL
                    comparisons += 1
    assert comparisons >= 20


def test_check_update_fft_vs_oracle_q1024_dense():
    """Bounded dense q=1024 (deterministic seeds): dc=3..5, coefficient sets
    incl. the frozen {1,3,7,255} permutations, syndromes incl. nonzero, every
    target; tolerance 1e-9."""
    rng = np.random.default_rng(2026090104)
    coefficient_sets = [[1] * 5, [1, 3, 7, 255, 1], [255, 1, 7, 3, 1], [7, 3, 255, 1, 7]]
    comparisons = 0
    for dc in (3, 4, 5):
        for _ in range(2):
            messages = [_random_normalized(rng, 1024) for _ in range(dc)]
            for coefficients in coefficient_sets:
                for syndrome in (0, 1, 511, 1023):
                    for target in range(dc):
                        fft = de.check_update_fft(messages, coefficients[:dc],
                                                  target, syndrome, FIELD1024)
                        oracle = ref.oracle_check_update_dense(
                            messages, coefficients[:dc], target, syndrome, FIELD1024)
                        assert oracle is not None
                        assert np.max(np.abs(fft - oracle)) < _ORACLE_TOL, (
                            dc, coefficients[:dc], syndrome, target)
                        comparisons += 1
    assert comparisons >= 3 * 2 * 3 * 4 * 3


def test_check_update_fft_vs_oracle_q1024_sparse_support():
    """Bounded sparse-support q=1024: incoming messages with small support
    (2..4 nonzero symbols) compared against the exact support-product oracle;
    deterministic seeds, dc=3..5, coefficients incl. {1,3,7,255}, syndromes
    incl. nonzero, every target."""
    rng = np.random.default_rng(2026090105)
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

    for dc in (3, 4, 5):
        for _ in range(3):
            messages = [sparse_message() for _ in range(dc)]
            for coefficients in coefficient_sets:
                for syndrome in (0, 1, 1023):
                    for target in range(dc):
                        fft = de.check_update_fft(messages, coefficients[:dc],
                                                  target, syndrome, FIELD1024)
                        oracle = ref.oracle_check_update_sparse(
                            messages, coefficients[:dc], target, syndrome, FIELD1024)
                        assert np.max(np.abs(fft - oracle)) < _ORACLE_TOL, (
                            dc, coefficients[:dc], syndrome, target)
                        comparisons += 1
    assert comparisons >= 3 * 3 * 3 * 3 * 3


def test_check_update_fft_fail_closed():
    good = [np.array([0.5, 0.25, 0.25, 0.0]), np.array([0.25, 0.25, 0.25, 0.25]),
            np.array([0.7, 0.1, 0.1, 0.1])]
    with pytest.raises(ValueError):
        de.check_update_fft(good, [1, 1, 1], 0, 0, object())       # not a field
    with pytest.raises(ValueError):
        de.check_update_fft(good, [1, 1, 1], -1, 0, FIELD4)        # bad target
    with pytest.raises(ValueError):
        de.check_update_fft(good, [1, 1, 1], 3, 0, FIELD4)         # bad target
    with pytest.raises(ValueError):
        de.check_update_fft(good, [1, 1], 0, 0, FIELD4)            # len mismatch
    with pytest.raises(ValueError):
        de.check_update_fft(good, [1, 0, 1], 0, 0, FIELD4)         # zero coeff
    with pytest.raises(ValueError):
        de.check_update_fft(good, [1, 5, 1], 0, 0, FIELD4)         # coeff ood
    with pytest.raises(ValueError):
        de.check_update_fft(good, [1, 1, 1], 0, 5, FIELD4)         # syndrome ood
    bad = [np.full(4, np.nan), good[1], good[2]]
    with pytest.raises(ValueError):
        de.check_update_fft(bad, [1, 1, 1], 0, 0, FIELD4)
    bad = [np.full(4, -0.25), good[1], good[2]]
    with pytest.raises(ValueError):
        de.check_update_fft(bad, [1, 1, 1], 0, 0, FIELD4)
    bad = [np.full(4, 0.5), good[1], good[2]]                      # not normalized
    with pytest.raises(ValueError):
        de.check_update_fft(bad, [1, 1, 1], 0, 0, FIELD4)
    with pytest.raises(ValueError):
        de.check_update_fft(good[:1], [1], 0, 0, FIELD4)           # dc < 2


# --------------------------------------------------------------------------- #
# 3. deterministic multi-seed MC-DE
# --------------------------------------------------------------------------- #


def test_run_mcde_determinism():
    lam, rho = _q4_config()
    first = de.run_mcde(4, lam, rho, 0.1, n_samples=500, max_iter=60, seed=2026090111)
    second = de.run_mcde(4, lam, rho, 0.1, n_samples=500, max_iter=60, seed=2026090111)
    assert first["entropy_trace"] == second["entropy_trace"]
    assert first["error_trace"] == second["error_trace"]
    assert first["iterations"] == second["iterations"]
    assert first["converged"] == second["converged"]
    third = de.run_mcde(4, lam, rho, 0.1, n_samples=500, max_iter=60, seed=2026090112)
    assert third["entropy_trace"] != first["entropy_trace"]


def test_run_mcde_converges_below_threshold():
    lam = {3: 1.0}
    rho = _rho_from_concentrated(common.concentrated_check_distribution(0.5, lam))
    assert rho == {6: 1.0}
    run = de.run_mcde(8, lam, rho, 0.05, n_samples=500, max_iter=60, seed=2026090113)
    assert run["converged"] is True
    assert run["entropy_trace"][-1] < 0.01
    assert run["error_trace"][-1] == 0.0


def test_run_mcde_q1024_bounded_deterministic():
    """The production-size kernel executes end-to-end deterministically on a
    bounded budget (n=100, max_iter=5) — the same seed reproduces the trace."""
    lam = {3: 1.0}
    rho = _rho_from_concentrated(common.concentrated_check_distribution(0.5, lam))
    first = de.run_mcde(1024, lam, rho, 0.05, n_samples=100, max_iter=5, seed=2026090111)
    second = de.run_mcde(1024, lam, rho, 0.05, n_samples=100, max_iter=5, seed=2026090111)
    assert first["entropy_trace"] == second["entropy_trace"]
    assert len(first["entropy_trace"]) == 5


def test_threshold_binary_search_deterministic():
    lam, rho = _q4_config()
    result = de.threshold_binary_search(4, lam, rho, n_samples=500, max_iter=60,
                                        seed=2026090111, p_lo=0.01, p_hi=0.49, p_tol=0.01)
    again = de.threshold_binary_search(4, lam, rho, n_samples=500, max_iter=60,
                                       seed=2026090111, p_lo=0.01, p_hi=0.49, p_tol=0.01)
    assert result["threshold_proxy"] == again["threshold_proxy"]
    assert result["probes"] == again["probes"]
    assert 0.0 < result["threshold_proxy"] < 0.49
    assert len(result["probes"]) >= 2
    assert abs(result["probes"][0]["p"] - 0.25) < 1e-12   # (0.01+0.49)/2


# --------------------------------------------------------------------------- #
# 4. entropy math
# --------------------------------------------------------------------------- #


def test_entropy_base_q_math():
    uniform = np.full((10, 4), 0.25)
    assert abs(de.entropy_base_q(uniform) - 1.0) < 1e-12
    delta = np.zeros((10, 4))
    delta[:, 0] = 1.0
    assert de.entropy_base_q(delta) == 0.0
    qsc = np.stack([de.qsc_channel_message(8, 0.2)] * 5)
    expected = -(0.8 * math.log(0.8) + 0.2 * math.log(0.2 / 7)) / math.log(8)
    assert abs(de.entropy_base_q(qsc) - expected) < 1e-12


# --------------------------------------------------------------------------- #
# 5. fail-closed boundaries
# --------------------------------------------------------------------------- #


def test_fail_closed_updates_and_params():
    lam, rho = _q4_config()
    rng = np.random.default_rng(7)
    good = np.full((8, 4), 0.25)
    rho_ok = {int(k): float(v) for k, v in rho.items()}
    for bad in (np.full((8, 4), np.nan), np.full((8, 4), np.inf),
                np.full((8, 4), -0.25), np.zeros((8, 4))):
        with pytest.raises(ValueError):
            de.variable_update_mcde(good, [2, 3], [0.5, 0.5], bad, rng, 4)
        with pytest.raises(ValueError):
            de.check_update_mcde(bad, list(rho_ok.keys()), list(rho_ok.values()), rng, 4)
        with pytest.raises(ValueError):
            de.belief_update_mcde(bad, [2, 3], [0.5, 0.5], good, rng, 4)
        with pytest.raises(ValueError):
            de.entropy_base_q(bad)
    with pytest.raises(ValueError):
        de.variable_update_mcde(good, [2, 3], [0.5, 0.5], good, rng, 3)   # q not pow2
    with pytest.raises(ValueError):
        de.check_update_mcde(good, list(rho_ok.keys()), list(rho_ok.values()), rng, 2048)
    with pytest.raises(ValueError):
        de.qsc_channel_message(4, 0.0)
    with pytest.raises(ValueError):
        de.qsc_channel_message(4, 0.75)        # (q-1)/q boundary excluded
    with pytest.raises(ValueError):
        de.run_mcde(4, lam, rho, 0.0, n_samples=500, max_iter=60, seed=1)
    with pytest.raises(ValueError):
        de.run_mcde(4, lam, rho, 0.1, n_samples=99, max_iter=60, seed=1)
    with pytest.raises(ValueError):
        de.run_mcde(4, lam, rho, 0.1, n_samples=500, max_iter=2001, seed=1)
    with pytest.raises(ValueError):
        de.run_mcde(3, lam, rho, 0.1, n_samples=500, max_iter=60, seed=1)
    with pytest.raises(ValueError):
        de.run_mcde(2048, lam, rho, 0.1, n_samples=500, max_iter=60, seed=1)
    with pytest.raises(ValueError):
        de.run_mcde(4, {}, rho, 0.1, n_samples=500, max_iter=60, seed=1)
    with pytest.raises(ValueError):
        de.run_mcde(4, {2: math.nan}, rho, 0.1, n_samples=500, max_iter=60, seed=1)
    with pytest.raises(ValueError):
        de.threshold_binary_search(4, lam, rho, n_samples=500, max_iter=60,
                                   seed=1, p_lo=0.5, p_hi=0.4, p_tol=0.01)


# --------------------------------------------------------------------------- #
# 6. no-production-import boundary
# --------------------------------------------------------------------------- #


def test_v9_no_production_import_boundary():
    """Importing the V9 modules must not bind any V1-V8 / qspa / decoder /
    production module object, and their source must contain no forbidden
    import lines.  V8 is a test-only oracle import in this test file only."""
    import comparison_bench.src.comparison_bench.formal_ir.nonbinary_v9_mcde as m_de
    import comparison_bench.src.comparison_bench.formal_ir.nonbinary_v9_common as m_common
    forbidden_module_names = ("nonbinary_qspa", "nonbinary_v1", "nonbinary_v2",
                              "nonbinary_v3", "nonbinary_v4", "nonbinary_v5",
                              "nonbinary_v6", "nonbinary_v7", "nonbinary_v8")
    for module in (m_de, m_common):
        for value in vars(module).values():
            if isinstance(value, types.ModuleType):
                assert not value.__name__.startswith(
                    ("nonbinary_v", "nonbinary_qspa")), (module.__name__, value.__name__)
                assert "decode" not in value.__name__ and "production" not in value.__name__
    forbidden_import = re.compile(
        r"^\s*(from|import)\s+.*(nonbinary_qspa|nonbinary_v[1-8]|"
        r"decode_|production|numpy\s*\.\s*fft)", re.MULTILINE)
    for name, path in V9_MODULE_PATHS.items():
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        assert not forbidden_import.search(source), f"{name}: forbidden import line"
        assert "nonbinary_qspa" not in source, f"{name}: qspa token in source"
