"""V8 error-domain contract tests (additive; T0/T1).

Covers the frozen error-domain algebra ``H*(x+y) == H*x + H*y == s + H*y``
exhaustively for tiny q=4, randomly for bounded q=8, plus reconstruction
round-trips, coefficient-order invariance, invalid-input and fail-closed
boundaries.
"""
from __future__ import annotations

import itertools
from numbers import Integral

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v8_error_domain as ed

FIELD4 = GF2mField.create(4)
FIELD8 = GF2mField.create(8)


def _full_rank_matrices(n: int, field: GF2mField) -> list[tuple[tuple[int, ...], ...]]:
    """Deterministic full-rank (row) matrices over GF(field.q), n columns,
    including rows with nonzero coefficients."""
    q = field.q
    matrices: list[tuple[tuple[int, ...], ...]] = []
    identity = tuple(tuple(1 if row == col else 0 for col in range(n)) for row in range(n))
    matrices.append(identity)
    all_ones = tuple([1] * n)
    if n == 1:
        matrices.append(((1,),))
        matrices.append(((q - 1,),))
        return matrices
    # identity with an extra all-ones row on top (full rank m=n rows -> n x n).
    stacked = (all_ones,) + identity[:-1]
    matrices.append(tuple(tuple(row) for row in stacked))
    # triangular matrix with nonzero coefficient pattern {2, 3, ...}.
    triangular: list[tuple[int, ...]] = []
    for row in range(n):
        pattern = [(row + col + 2) % (q - 1) + 1 for col in range(n)]
        triangular.append(tuple(0 if col < row else pattern[col] for col in range(n)))
    matrices.append(tuple(triangular))
    return matrices


def test_exhaustive_q4_equivalence_all_x_y_pairs():
    """Exhaustive q=4, n=1..4: for every x,y pair and several deterministic
    full-rank H (incl. nonzero coefficients), the equivalence dict holds and
    H*(x+y) == H*x + H*y == s + H*y."""
    for n in range(1, 5):
        for matrix in _full_rank_matrices(n, FIELD4):
            for x in itertools.product(range(4), repeat=n):
                syndrome = ed.mul_sum_syndrome(FIELD4, matrix, x)
                for y in itertools.product(range(4), repeat=n):
                    result = ed.error_domain_equivalence(FIELD4, matrix, syndrome, x, y)
                    assert result["equivalent"] is True, (n, matrix, x, y, result)
                    assert result["direct_syndrome"] == result["split_syndrome"] == result["derived_d"]
                    expected_direct = ed.mul_sum_syndrome(
                        FIELD4, matrix, ed.error_vector(FIELD4, x, y))
                    assert result["direct_syndrome"] == expected_direct


def test_bounded_q8_random_equivalence():
    """Bounded q=8, n=6: >= 250 seeded random x, y, H trials with the same
    assertions."""
    rng = np.random.default_rng(2026080401)
    trials = 0
    for _ in range(250):
        n = 6
        rows = 3
        matrix = tuple(tuple(int(rng.integers(0, 8)) for _ in range(n)) for _ in range(rows))
        if any(all(value == 0 for value in row) for row in matrix):
            continue
        x = tuple(int(v) for v in rng.integers(0, 8, size=n))
        y = tuple(int(v) for v in rng.integers(0, 8, size=n))
        syndrome = ed.mul_sum_syndrome(FIELD8, matrix, x)
        result = ed.error_domain_equivalence(FIELD8, matrix, syndrome, x, y)
        assert result["equivalent"] is True, (matrix, x, y, result)
        assert result["direct_syndrome"] == result["split_syndrome"] == result["derived_d"]
        trials += 1
    assert trials >= 200


def test_reconstruction_roundtrip():
    """Plant e, y random, e_hat == e -> reconstruct_x(y, e_hat) == x = y+e."""
    for field in (FIELD4, FIELD8):
        rng = np.random.default_rng(2026080402)
        for _ in range(40):
            n = 5
            y = tuple(int(v) for v in rng.integers(0, field.q, size=n))
            e = tuple(int(v) for v in rng.integers(0, field.q, size=n))
            x = ed.error_vector(field, y, e)
            assert ed.reconstruct_x(y, e) == x
            wrong = tuple(field.add(v, 1) if v == 0 else 0 for v in e)
            assert ed.reconstruct_x(y, wrong) != x


def test_coefficient_order_invariance():
    """H*x on a permuted column ordering of the same matrix equals the
    original H*x (the syndrome is order-invariant under a joint column
    permutation)."""
    field = FIELD8
    rng = np.random.default_rng(2026080403)
    n = 5
    matrix = tuple(tuple(int(rng.integers(0, 8)) for _ in range(n)) for _ in range(3))
    x = tuple(int(v) for v in rng.integers(0, 8, size=n))
    permutation = (4, 1, 3, 0, 2)
    permuted_matrix = tuple(tuple(row[col] for col in permutation) for row in matrix)
    permuted_x = tuple(x[col] for col in permutation)
    assert ed.mul_sum_syndrome(field, matrix, x) == ed.mul_sum_syndrome(
        field, permuted_matrix, permuted_x)


def test_invalid_inputs():
    """Out-of-domain symbols, bools, non-rectangular matrices, width and
    length mismatches all raise ValueError (fail closed)."""
    with pytest.raises(ValueError):
        ed.validate_symbols([0, 4], 4)                      # out of domain
    with pytest.raises(ValueError):
        ed.validate_symbols([True, 0], 4)                   # bool
    with pytest.raises(ValueError):
        ed.validate_symbols([0.5, 1], 4)                    # non-Integral
    with pytest.raises(ValueError):
        ed.validate_symbols([0, 1], 4, expected=3)          # wrong length
    with pytest.raises(ValueError):
        ed.validate_matrix([[1, 0], [0, 1, 1]], 2)          # non-rectangular
    with pytest.raises(ValueError):
        ed.validate_matrix([[1, 0]], 3)                     # width mismatch
    with pytest.raises(ValueError):
        ed.validate_matrix([[True, 0]], 2)                  # bool coefficient
    with pytest.raises(ValueError):
        ed.mul_sum_syndrome(FIELD4, [[1, 0], [0, 1]], [1, 1, 1])   # width vs symbols
    with pytest.raises(ValueError):
        ed.mul_sum_syndrome(FIELD4, [[1, 0]], [1, 4])       # out-of-domain symbol
    with pytest.raises(ValueError):
        ed.mul_sum_syndrome(FIELD4, [[1, 4]], [1, 0])       # out-of-domain coefficient
    with pytest.raises(ValueError):
        ed.error_vector(FIELD4, [1, 0], [1])                # length mismatch
    with pytest.raises(ValueError):
        ed.reconstruct_x([1, 0], [1, 0, 0])                 # length mismatch
    with pytest.raises(ValueError):
        ed.error_domain_syndrome([1, 0], [1, 0, 0])         # length mismatch
    with pytest.raises(ValueError):
        ed.error_domain_equivalence(FIELD4, [[1, 0]], [1, 1], [1, 0], [0, 1])  # syndrome length
    with pytest.raises(ValueError):
        ed.mul_sum_syndrome(None, [[1, 0]], [1, 0])         # field type


def test_fail_closed_symbol_domain():
    """Out-of-domain inputs fail closed even when nested in longer vectors."""
    with pytest.raises(ValueError):
        ed.error_domain_equivalence(FIELD4, [[1, 1]], [1], [1, 7], [0, 1])
    with pytest.raises(ValueError):
        ed.validate_symbols(np.asarray([0, 8], dtype=np.int64), 8)   # q=8: 8 is out
    # numpy integer arrays are accepted when in-domain (Integral-compatible).
    out = ed.validate_symbols(np.asarray([0, 7], dtype=np.int64), 8)
    assert out == (0, 7)
    assert all(isinstance(value, Integral) for value in out)


def test_direct_syndrome_row_order():
    """Row order of H is preserved in the syndrome tuple."""
    matrix = ((1, 2, 3), (3, 1, 2), (2, 3, 1))
    x = (1, 2, 3)
    syndrome = ed.mul_sum_syndrome(FIELD4, matrix, x)
    assert len(syndrome) == 3
    for row_index in range(3):
        expected = 0
        for coefficient, symbol in zip(matrix[row_index], x):
            expected = FIELD4.add(expected, FIELD4.mul(coefficient, symbol))
        assert syndrome[row_index] == expected
