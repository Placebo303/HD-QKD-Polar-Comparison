"""V8 independent probability-domain oracle tests (additive; T0/T1).

Covers sparse/dense oracle agreement, oracle-vs-production agreement at
q=4 (exhaustive), q=8 (bounded) and one-check GF(1024) (frozen tolerance
1e-9), brute-force tiny-code MAP vs reference BP on cycle-free star graphs,
fail-closed boundaries and the import-independence boundary.

The production check update is imported TEST-ONLY for the oracle comparison
and is never executed as a runner:
``from comparison_bench.src.comparison_bench.formal_ir import
nonbinary_v7_r1a_long as v7_long`` then ``v7_long.check_update_fft_qspa``.
"""
from __future__ import annotations

import inspect
import itertools
import re

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v8_reference as ref
from comparison_bench.src.comparison_bench.formal_ir import (
    nonbinary_v7_r1a_long as v7_long,
)

FIELD4 = GF2mField.create(4)
FIELD8 = GF2mField.create(8)
FIELD1024 = GF2mField.create(1024)

# Frozen tolerance for oracle-vs-production agreement (both compute the same
# object; the production FWHT route has ~1e-15 rounding).
_PROD_TOL = 1e-9


def _random_normalized(rng: np.random.Generator, q: int) -> np.ndarray:
    vector = rng.random(q)
    return vector / vector.sum()


def _scaled_message(field: GF2mField, message: np.ndarray, coefficient: int) -> np.ndarray:
    out = np.zeros(field.q, dtype=np.float64)
    for symbol in range(field.q):
        out[field.mul(coefficient, symbol)] = message[symbol]
    return out


# --------------------------------------------------------------------------- #
# 1. sparse vs dense oracle paths
# --------------------------------------------------------------------------- #


def test_sparse_vs_dense_agree_deterministic():
    """Sparse and dense oracle paths agree exactly on deterministic q=4/q=8
    cases: dc=3..5, all-unity and mixed nonzero coefficients, syndrome 0 and
    nonzero, random normalized messages, fixed seeds."""
    rng = np.random.default_rng(2026080411)
    cases = 0
    for q, field in ((4, FIELD4), (8, FIELD8)):
        for dc in (3, 4, 5):
            for coefficients in ([1] * dc, [1, 2, 3, 1, 3][:dc], [2, 1, 1, 2, 2][:dc]):
                for syndrome in (0, q - 1):
                    messages = [_random_normalized(rng, q) for _ in range(dc)]
                    for target in range(dc):
                        dense = ref.oracle_check_update_dense(
                            messages, coefficients, target, syndrome, field)
                        sparse = ref.oracle_check_update_sparse(
                            messages, coefficients, target, syndrome, field)
                        assert dense is not None and sparse is not None
                        assert np.max(np.abs(dense - sparse)) < 1e-12, (
                            q, dc, coefficients, syndrome, target)
                        cases += 1
    assert cases >= 90


# --------------------------------------------------------------------------- #
# 2. oracle vs production check update
# --------------------------------------------------------------------------- #


def test_oracle_vs_production_exhaustive_q4():
    """Exhaustive q=4 dc=3 and dc=4: all coefficient combos from {1,2,3},
    syndromes 0..3, several deterministic message sets, every target position.
    Both oracle paths agree with the production FFT-QSPA check update within
    1e-9."""
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
                        prod = v7_long.check_update_fft_qspa(
                            [np.asarray(m, dtype=np.float64) for m in messages],
                            list(coefficients), target, syndrome, FIELD4)
                        dense = ref.oracle_check_update_dense(
                            messages, list(coefficients), target, syndrome, FIELD4)
                        sparse = ref.oracle_check_update_sparse(
                            messages, list(coefficients), target, syndrome, FIELD4)
                        assert prod is not None and dense is not None and sparse is not None
                        assert np.max(np.abs(dense - prod)) < _PROD_TOL, (
                            dc, coefficients, syndrome, set_index, target)
                        assert np.max(np.abs(sparse - prod)) < _PROD_TOL
                        comparisons += 1
    assert comparisons == (27 * 4 * 3 * 3) + (81 * 4 * 3 * 4)


def test_oracle_vs_production_bounded_q8():
    """Bounded q=8: >= 40 seeded random cases, dc=3..5, mixed coefficients and
    syndromes, both oracle paths within 1e-9 of production."""
    rng = np.random.default_rng(2026080412)
    comparisons = 0
    for _ in range(60):
        dc = int(rng.integers(3, 6))
        coefficients = [int(rng.integers(1, 8)) for _ in range(dc)]
        syndrome = int(rng.integers(0, 8))
        messages = [_random_normalized(rng, 8) for _ in range(dc)]
        for target in range(dc):
            prod = v7_long.check_update_fft_qspa(
                [np.asarray(m, dtype=np.float64) for m in messages],
                coefficients, target, syndrome, FIELD8)
            dense = ref.oracle_check_update_dense(messages, coefficients, target, syndrome, FIELD8)
            sparse = ref.oracle_check_update_sparse(messages, coefficients, target, syndrome, FIELD8)
            assert prod is not None and dense is not None and sparse is not None
            assert np.max(np.abs(dense - prod)) < _PROD_TOL
            assert np.max(np.abs(sparse - prod)) < _PROD_TOL
            comparisons += 1
    assert comparisons >= 40


def test_oracle_vs_production_one_check_gf1024():
    """ONE-CHECK GF(1024) comparison (frozen; every case parameter is recorded
    below).  dc=4, deterministic seeded messages:
      - sparse-support vectors (support sizes 2,3,4) via the sparse oracle path;
      - dense vectors (uniform + one dominant symbol, and mildly peaked) via
        the dense oracle path;
    syndromes {0, 17, 999}, coefficients {1, 3, 7, 255}, every target position.
    Frozen tolerance: max abs diff <= 1e-9 (production FWHT rounding ~1e-15).

    Case parameters (frozen summary): q=1024, dc=4, syndrome in
    {0, 17, 999}, coefficient tuples = all 24 permutations of the 4 distinct
    values {1, 3, 7, 255} assigned to the 4 message slots, target in 0..3,
    message families:
      sparse A: support {0, 137}  mass 0.6/0.4
      sparse B: support {0, 255, 512} mass 0.5/0.3/0.2
      sparse C: support {1, 17, 999, 1023} mass 0.4/0.3/0.2/0.1
      dense D1: uniform plus a dominant symbol (0.7 at symbol 77)
      dense D2: mildly peaked (0.95 at symbol 0)
      dense D3: mildly peaked (0.8 at symbol 0)
      dense D4: mildly peaked (0.9 at symbol 3)
    The sparse oracle uses three sparse-support messages (A, B, C plus a second
    B); the dense oracle uses the four dense families.
    """
    rng = np.random.default_rng(2026080413)
    q = 1024

    def sparse_msg(support: list[int], mass: list[float]) -> np.ndarray:
        vector = np.zeros(q, dtype=np.float64)
        for symbol, weight in zip(support, mass):
            vector[symbol] = weight
        return vector

    sparse_family = {
        "A": sparse_msg([0, 137], [0.6, 0.4]),
        "B": sparse_msg([0, 255, 512], [0.5, 0.3, 0.2]),
        "C": sparse_msg([1, 17, 999, 1023], [0.4, 0.3, 0.2, 0.1]),
    }
    dense1 = np.full(q, 0.3 / (q - 1), dtype=np.float64)
    dense1[77] = 0.7
    dense2 = np.full(q, 0.05 / (q - 1), dtype=np.float64)
    dense2[0] = 0.95
    dense3 = np.full(q, 0.2 / (q - 1), dtype=np.float64)
    dense3[0] = 0.8
    dense4 = np.full(q, 0.1 / (q - 1), dtype=np.float64)
    dense4[3] = 0.9

    coefficient_values = [1, 3, 7, 255]
    coefficient_assignments = list(itertools.permutations(coefficient_values))
    comparisons = 0
    for coefficients in coefficient_assignments:
        for syndrome in (0, 17, 999):
            for target in range(4):
                # sparse-support vectors via the sparse path
                sparse_messages = [sparse_family["A"], sparse_family["B"], sparse_family["C"],
                                   sparse_family["B"]]
                sparse_out = ref.oracle_check_update_sparse(
                    sparse_messages, list(coefficients), target, syndrome, FIELD1024)
                prod_sparse = v7_long.check_update_fft_qspa(
                    [np.asarray(m, dtype=np.float64) for m in sparse_messages],
                    list(coefficients), target, syndrome, FIELD1024)
                assert sparse_out is not None and prod_sparse is not None
                assert np.max(np.abs(sparse_out - prod_sparse)) < _PROD_TOL, (
                    coefficients, syndrome, target)
                # dense vectors via the dense path
                dense_messages = [dense1, dense2, dense3, dense4]
                dense_out = ref.oracle_check_update_dense(
                    dense_messages, list(coefficients), target, syndrome, FIELD1024)
                prod_dense = v7_long.check_update_fft_qspa(
                    [np.asarray(m, dtype=np.float64) for m in dense_messages],
                    list(coefficients), target, syndrome, FIELD1024)
                assert dense_out is not None and prod_dense is not None
                assert np.max(np.abs(dense_out - prod_dense)) < _PROD_TOL, (
                    coefficients, syndrome, target)
                comparisons += 2
    assert comparisons == 24 * 3 * 4 * 2


# --------------------------------------------------------------------------- #
# 3. brute-force MAP vs reference BP on a cycle-free star graph
# --------------------------------------------------------------------------- #


def _qsc_priors(rng: np.random.Generator, q: int, n: int, p: float) -> list[np.ndarray]:
    """QSC symbol priors for a deterministic received symbol vector y."""
    received = [int(v) for v in rng.integers(0, q, size=n)]
    priors = []
    for symbol in received:
        vector = np.full(q, p / (q - 1.0), dtype=np.float64)
        vector[symbol] = 1.0 - p
        priors.append(vector)
    return priors


def _star_graph_bp_check(field: GF2mField, priors: list[np.ndarray], matrix_row: tuple,
                         syndrome: int, coefficients: list[int]) -> list[np.ndarray]:
    """One BP round on a single-check star graph: check update then belief."""
    n = len(priors)
    messages = []
    for target in range(n):
        out = ref.oracle_check_update_dense(priors, coefficients, target, syndrome, field)
        assert out is not None
        messages.append(out)
    beliefs = []
    for index in range(n):
        belief = ref.oracle_belief(priors[index], [messages[index]])
        assert belief is not None
        beliefs.append(belief)
    return beliefs


@pytest.mark.parametrize(
    "q,n,matrix_row,coefficients,p,seed",
    [
        (4, 4, (1, 1, 1, 1), [1, 1, 1, 1], 0.10, 2026080414),
        (4, 4, (1, 2, 3, 1), [1, 2, 3, 1], 0.15, 2026080415),
        (8, 3, (1, 1, 1), [1, 1, 1], 0.08, 2026080416),
        (8, 3, (1, 3, 2), [1, 3, 2], 0.12, 2026080417),
    ],
)
def test_bruteforce_map_vs_reference_bp_star(q, n, matrix_row, coefficients, p, seed):
    """On a cycle-free star graph (single check row), one reference-BP round
    yields the exact posterior: belief marginals match the brute-force coset
    marginals within 1e-9 and the belief argmax agrees with the posterior
    marginal argmax.  (The brute-force MAP *vector* need not equal the
    coordinate-wise marginal argmaxes because the syndrome couples the
    coordinates; the marginal argmax is the correct comparison target.)"""
    field = GF2mField.create(q)
    rng = np.random.default_rng(seed)
    priors = _qsc_priors(rng, q, n, p)
    matrix = (tuple(matrix_row),)
    x = tuple(int(v) for v in rng.integers(0, q, size=n))
    syndrome = ref_mul_syndrome(field, matrix, x)
    beliefs = _star_graph_bp_check(field, priors, matrix_row, syndrome[0], coefficients)
    brute = ref.bruteforce_coset_map(field, matrix, syndrome, priors)
    assert brute["map_symbols"] is not None
    coset_total = sum(brute["marginals"].values())
    for index in range(n):
        posterior = np.zeros(q, dtype=np.float64)
        for vector, mass in brute["marginals"].items():
            posterior[vector[index]] += mass / coset_total
        assert np.max(np.abs(beliefs[index] - posterior)) < 1e-9, (
            q, n, index, beliefs[index], posterior)
        assert int(np.argmax(beliefs[index])) == int(np.argmax(posterior))


def test_bruteforce_error_map_reconstructs_x():
    """bruteforce_error_map: with the planted-error QSC prior, the MAP error
    equals the planted error (and x is reconstructed exactly) when the planted
    error IS the MAP of its coset: e = 0, and any planted error in a singleton
    coset (invertible full-rank H).  A symmetric QSC prior always prefers the
    minimum-weight coset member, so a non-minimal planted error is a genuine
    decoding failure, not a bug — asserted via the syndrome consistency of the
    MAP output."""
    # e = 0: the zero error is the unique MAP of the kernel coset.
    for q, n, row, p, seed in (
        (4, 3, (1, 2, 1), 0.10, 2026080418),
        (8, 2, (1, 1), 0.12, 2026080419),
    ):
        field = GF2mField.create(q)
        rng = np.random.default_rng(seed)
        matrix = (tuple(row),)
        y = tuple(int(v) for v in rng.integers(0, q, size=n))
        e = (0,) * n
        x = tuple(field.add(a, b) for a, b in zip(y, e))
        error_syndrome = ref_mul_syndrome(field, matrix, e)
        error_priors = []
        for _ in range(n):
            vector = np.full(q, p / (q - 1.0), dtype=np.float64)
            vector[0] = 1.0 - p
            error_priors.append(vector)
        result = ref.bruteforce_error_map(field, matrix, error_syndrome, error_priors, y)
        assert result["coset_size"] > 0
        assert result["e_hat"] == e
        assert result["x_hat"] == x
    # Singleton coset: invertible 2x2 H over GF(4), n=2 -> the planted error is
    # the unique coset member and reconstruction is exact for any planted e.
    field4 = GF2mField.create(4)
    rng = np.random.default_rng(2026080421)
    matrix = ((1, 1), (1, 2))
    n = 2
    p = 0.10
    for _ in range(10):
        y = tuple(int(v) for v in rng.integers(0, 4, size=n))
        e = tuple(int(v) for v in rng.integers(0, 4, size=n))
        error_syndrome = ref_mul_syndrome(field4, matrix, e)
        error_priors = []
        for _ in range(n):
            vector = np.full(4, p / 3.0, dtype=np.float64)
            vector[0] = 1.0 - p
            error_priors.append(vector)
        result = ref.bruteforce_error_map(field4, matrix, error_syndrome, error_priors, y)
        assert result["coset_size"] == 1
        assert result["e_hat"] == e
        assert result["x_hat"] == tuple(field4.add(a, b) for a, b in zip(y, e))
    # Non-minimal planted error: the MAP still satisfies the syndrome
    # constraint (a legitimate decoding failure otherwise).
    field4b = GF2mField.create(4)
    matrix_b = ((1, 1, 1),)
    n_b = 3
    y_b = (1, 2, 3)
    e_b = (1, 2, 0)          # weight-2 error; a weight-1 representative exists
    error_syndrome_b = ref_mul_syndrome(field4b, matrix_b, e_b)
    priors_b = []
    for _ in range(n_b):
        vector = np.full(4, 0.1 / 3.0, dtype=np.float64)
        vector[0] = 0.9
        priors_b.append(vector)
    result_b = ref.bruteforce_error_map(field4b, matrix_b, error_syndrome_b, priors_b, y_b)
    assert result_b["coset_size"] > 0
    assert ref_mul_syndrome(field4b, matrix_b, result_b["e_hat"]) == error_syndrome_b
    assert result_b["x_hat"] == tuple(field4b.add(a, b) for a, b in zip(y_b, result_b["e_hat"]))


# --------------------------------------------------------------------------- #
# 4. invalid inputs / fail-closed
# --------------------------------------------------------------------------- #


def test_oracle_invalid_inputs_fail_closed():
    """NaN/Inf/negative/zero-mass/non-normalized messages -> ValueError;
    unbounded sparse enumeration raises; malformed arguments raise."""
    rng = np.random.default_rng(2026080420)
    good = _random_normalized(rng, 4)
    messages = [good, good, good]
    coefficients = [1, 1, 1]
    for bad in (np.full(4, np.nan), np.full(4, np.inf), np.array([-0.1, 0.5, 0.3, 0.3]),
                np.zeros(4), np.array([0.2, 0.2, 0.2, 0.2])):
        with pytest.raises(ValueError):
            ref.oracle_check_update_dense([bad, good, good], coefficients, 0, 0, FIELD4)
        with pytest.raises(ValueError):
            ref.oracle_check_update_sparse([bad, good, good], coefficients, 0, 0, FIELD4)
    with pytest.raises(ValueError):
        ref.oracle_check_update_dense([good, good], [1, 1], 2, 0, FIELD4)   # target out of range
    with pytest.raises(ValueError):
        ref.oracle_check_update_dense([good, good, good], [1, 1], 0, 0, FIELD4)  # coeff count
    with pytest.raises(ValueError):
        ref.oracle_check_update_dense([good, good], [1, 1], 0, 0, None)     # field type
    with pytest.raises(ValueError):
        ref.oracle_check_update_dense([good, good], [0, 1], 0, 0, FIELD4)   # zero coefficient
    # emergent invalid mass -> None (fail closed, like the production
    # _normalise contract): disjoint delta priors have a zero-mass product.
    delta0 = np.array([1.0, 0.0, 0.0, 0.0])
    delta1 = np.array([0.0, 1.0, 0.0, 0.0])
    assert ref.oracle_variable_update(delta0, [delta1]) is None
    assert ref.oracle_belief(delta0, [delta1]) is None
    # unbounded sparse enumeration: q=1024 dense dc=4 -> q^(dc-1) > 2_000_000
    dense1024 = np.full(1024, 1.0 / 1024, dtype=np.float64)
    with pytest.raises(ValueError):
        ref.oracle_check_update_sparse([dense1024] * 4, [1, 1, 1, 1], 0, 0, FIELD1024)
    # q=8 dc=8 dense -> 8^7 = 2_097_152 > 2_000_000 also raises
    dense8 = np.full(8, 1.0 / 8, dtype=np.float64)
    with pytest.raises(ValueError):
        ref.oracle_check_update_sparse([dense8] * 8, [1] * 8, 0, 0, FIELD8)


def test_bruteforce_bounds_and_invalid():
    """q^n > 4096 raises; wrong-shaped inputs raise."""
    priors = [np.full(4, 0.25) for _ in range(6)]           # 4^6 = 4096: allowed
    result = ref.bruteforce_coset_map(FIELD4, ((1,) * 6,), (0,), priors)
    assert result["coset_size"] >= 1
    priors7 = [np.full(4, 0.25) for _ in range(7)]          # 4^7 = 16384: too large
    with pytest.raises(ValueError):
        ref.bruteforce_coset_map(FIELD4, ((1,) * 7,), (0,), priors7)
    with pytest.raises(ValueError):
        ref.bruteforce_coset_map(FIELD4, ((1, 1),), (0, 0), priors)   # syndrome length
    with pytest.raises(ValueError):
        ref.bruteforce_coset_map(FIELD4, ((1, 1),), (0,), [np.full(4, 0.25)])  # width


# --------------------------------------------------------------------------- #
# 5. import independence boundary
# --------------------------------------------------------------------------- #

V8_MODULE_PATHS = {
    "error_domain": "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v8_error_domain.py",
    "reference": "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v8_reference.py",
    "mcde": "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v8_mcde.py",
}


def test_assert_oracle_independent():
    """The oracle's own independence scan returns no violations."""
    assert ref.assert_oracle_independent() == []


def test_v8_modules_have_no_forbidden_import_lines():
    """Source scan of all three V8 modules: no forbidden import lines (no
    V1-V7 module, no numpy.fft / FWHT, no production decoder import)."""
    forbidden_pattern = re.compile(
        r"^\s*(from|import)\s+.*(nonbinary_v[1-7]|nonbinary_qspa|"
        r"decode_nbldpc|production_runner|numpy\s*\.\s*fft)", re.MULTILINE)
    fwht_pattern = re.compile(r"\bfwht\b", re.IGNORECASE)
    for name, path in V8_MODULE_PATHS.items():
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        assert not forbidden_pattern.search(source), (
            f"{name}: forbidden import line present")
        if name == "mcde":
            assert not fwht_pattern.search(source), "mcde must not use FWHT"


# --------------------------------------------------------------------------- #
# helpers (test-local; the oracle module must not depend on them)
# --------------------------------------------------------------------------- #


def ref_mul_syndrome(field: GF2mField, matrix: tuple, symbols: tuple) -> tuple:
    """Direct H*x for the tests (independent of the module's own helper)."""
    result = []
    for row in matrix:
        total = 0
        for coefficient, symbol in zip(row, symbols):
            total = field.add(total, field.mul(coefficient, symbol))
        result.append(total)
    return tuple(result)
