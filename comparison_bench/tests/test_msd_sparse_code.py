"""Fixed structural tests for the MSD sparse accumulator-code candidate."""

from __future__ import annotations

import numpy as np
import pytest
from scipy import sparse

from comparison_bench.src.comparison_bench.formal_ir.msd_sparse_code import (
    build_msd_sparse_code,
)


def _row_pair_occurrences(matrix: sparse.csr_matrix) -> dict[tuple[int, int], int]:
    columns = matrix.tocsc()
    occurrences: dict[tuple[int, int], int] = {}
    for column in range(columns.shape[1]):
        rows = columns.indices[columns.indptr[column] : columns.indptr[column + 1]]
        for left_index, left in enumerate(rows):
            for right in rows[left_index + 1 :]:
                pair = (int(left), int(right))
                occurrences[pair] = occurrences.get(pair, 0) + 1
    return occurrences


def _assert_no_row_pair_repeats(matrix: sparse.csr_matrix) -> None:
    assert all(count <= 1 for count in _row_pair_occurrences(matrix).values())


def _gf2_rank(matrix: sparse.csr_matrix) -> int:
    work = matrix.toarray().astype(np.uint8, copy=True)
    rank = 0
    for column in range(work.shape[1]):
        pivot = next(
            (row for row in range(rank, work.shape[0]) if work[row, column]),
            None,
        )
        if pivot is None:
            continue
        work[[rank, pivot]] = work[[pivot, rank]]
        for row in range(rank + 1, work.shape[0]):
            if work[row, column]:
                work[row] ^= work[rank]
        rank += 1
        if rank == work.shape[0]:
            break
    return rank


def _expected_accumulator(m: int) -> np.ndarray:
    accumulator = np.eye(m, dtype=np.uint8)
    for row in range(1, m):
        accumulator[row, row - 1] = 1
    return accumulator


def test_small_sparse_code_structure_rank_and_no_fallback_four_cycles() -> None:
    parameters = dict(n=12, m=8, information_degree=2, tie_offset=0)
    result = build_msd_sparse_code(**parameters)
    repeated = build_msd_sparse_code(**parameters)
    matrix = result.parity_check_matrix
    information_columns = parameters["n"] - parameters["m"]

    assert sparse.isspmatrix_csr(matrix)
    assert matrix.has_canonical_format
    assert matrix.dtype == np.uint8
    assert np.all(matrix.data == 1)
    assert matrix.shape == (8, 12)
    assert np.array_equal(
        np.diff(matrix[:, :information_columns].tocsc().indptr),
        np.full(information_columns, 2),
    )
    assert np.array_equal(
        matrix[:, information_columns:].toarray(), _expected_accumulator(8)
    )
    assert result.four_cycle_fallback_count == 0
    assert _gf2_rank(matrix) == 8
    _assert_no_row_pair_repeats(matrix)

    assert np.array_equal(matrix.indptr, repeated.parity_check_matrix.indptr)
    assert np.array_equal(matrix.indices, repeated.parity_check_matrix.indices)
    assert np.array_equal(matrix.data, repeated.parity_check_matrix.data)
    assert result.four_cycle_fallback_count == repeated.four_cycle_fallback_count


def test_tie_offset_controls_equal_degree_row_order() -> None:
    offset_zero = build_msd_sparse_code(
        n=5, m=3, information_degree=1, tie_offset=0
    ).parity_check_matrix[:, :2].tocsc()
    offset_one = build_msd_sparse_code(
        n=5, m=3, information_degree=1, tie_offset=1
    ).parity_check_matrix[:, :2].tocsc()
    offset_one_repeated = build_msd_sparse_code(
        n=5, m=3, information_degree=1, tie_offset=4
    ).parity_check_matrix[:, :2].tocsc()

    assert offset_zero.indices[offset_zero.indptr[0] : offset_zero.indptr[1]].tolist() == [0]
    assert offset_zero.indices[offset_zero.indptr[1] : offset_zero.indptr[2]].tolist() == [0]
    assert offset_one.indices[offset_one.indptr[0] : offset_one.indptr[1]].tolist() == [0]
    assert offset_one.indices[offset_one.indptr[1] : offset_one.indptr[2]].tolist() == [1]
    assert np.array_equal(offset_one.indptr, offset_one_repeated.indptr)
    assert np.array_equal(offset_one.indices, offset_one_repeated.indices)


def test_degree_one_placements_keep_row_degrees_balanced() -> None:
    result = build_msd_sparse_code(
        n=20, m=5, information_degree=1, tie_offset=2
    )
    row_degrees = np.asarray(result.parity_check_matrix.sum(axis=1)).reshape(-1)

    assert int(row_degrees.max() - row_degrees.min()) <= 1
    assert result.four_cycle_fallback_count == 0


def test_n_equals_m_returns_only_full_rank_accumulator() -> None:
    result = build_msd_sparse_code(
        n=5, m=5, information_degree=3, tie_offset=7
    )

    assert result.parity_check_matrix.shape == (5, 5)
    assert result.parity_check_matrix.nnz == 2 * 5 - 1
    assert np.array_equal(result.parity_check_matrix.toarray(), _expected_accumulator(5))
    assert result.four_cycle_fallback_count == 0
    assert _gf2_rank(result.parity_check_matrix) == 5


def test_crowded_tiny_fixture_reports_required_four_cycle_fallbacks() -> None:
    result = build_msd_sparse_code(
        n=6, m=3, information_degree=3, tie_offset=0
    )

    assert result.parity_check_matrix.shape == (3, 6)
    assert result.four_cycle_fallback_count == 5
    assert any(
        count > 1
        for count in _row_pair_occurrences(result.parity_check_matrix).values()
    )


@pytest.mark.parametrize(
    "parameters",
    [
        {"n": True, "m": 2, "information_degree": 1, "tie_offset": 0},
        {"n": 4.0, "m": 2, "information_degree": 1, "tie_offset": 0},
        {"n": 2, "m": False, "information_degree": 1, "tie_offset": 0},
        {"n": 2, "m": 0, "information_degree": 1, "tie_offset": 0},
        {"n": 2, "m": 3, "information_degree": 1, "tie_offset": 0},
        {"n": 3, "m": 3, "information_degree": 0, "tie_offset": 0},
        {"n": 3, "m": 3, "information_degree": 4, "tie_offset": 0},
        {"n": 3, "m": 3, "information_degree": 1, "tie_offset": 0.5},
        {"n": 3, "m": 3, "information_degree": 1, "tie_offset": True},
    ],
)
def test_invalid_parameters_are_rejected(parameters) -> None:
    with pytest.raises(ValueError):
        build_msd_sparse_code(**parameters)


def test_required_parameters_have_no_defaults() -> None:
    with pytest.raises(TypeError):
        build_msd_sparse_code(n=4, m=2, information_degree=1)


def test_long_block_fixture_stays_sparse_and_has_expected_edge_count() -> None:
    result = build_msd_sparse_code(
        n=16_384, m=8_192, information_degree=3, tie_offset=0
    )
    matrix = result.parity_check_matrix
    information_columns = 16_384 - 8_192
    accumulator = matrix[:, information_columns:].tocsc()

    assert sparse.isspmatrix_csr(matrix)
    assert matrix.has_canonical_format
    assert matrix.shape == (8_192, 16_384)
    assert matrix.nnz == 8_192 * 3 + 2 * 8_192 - 1
    assert np.all(matrix.data == 1)
    assert np.array_equal(
        np.diff(accumulator.indptr),
        np.array([2] * (8_192 - 1) + [1]),
    )
    for column in (0, 4_096, 8_191):
        rows = accumulator.indices[
            accumulator.indptr[column] : accumulator.indptr[column + 1]
        ]
        expected_rows = [column, column + 1] if column < 8_191 else [column]
        assert rows.tolist() == expected_rows
