"""Deterministic sparse accumulator-code construction candidate.

Constructs ``H = [A | T]`` with explicit information-column degree and a
unit lower-bidiagonal accumulator ``T``. This is structural code generation
only; it does not choose a stage rate or run a decoder.
"""

from __future__ import annotations

from dataclasses import dataclass
import heapq
import itertools
import operator

import numpy as np
from scipy import sparse


@dataclass(frozen=True)
class SparseCodeConstruction:
    """Sparse parity-check matrix and unavoidable four-cycle relaxations."""

    parity_check_matrix: sparse.csr_matrix
    four_cycle_fallback_count: int


def _explicit_integer(value: object, name: str) -> int:
    if isinstance(value, (bool, np.bool_)):
        raise ValueError(f"{name} must be an integer, not bool")
    try:
        return operator.index(value)
    except TypeError as exc:
        raise ValueError(f"{name} must be an integer") from exc


def _row_pair(left: int, right: int) -> tuple[int, int]:
    return (left, right) if left < right else (right, left)


def build_msd_sparse_code(
    *,
    n: int,
    m: int,
    information_degree: int,
    tie_offset: int,
) -> SparseCodeConstruction:
    """Build deterministic ``H=[A|T]`` in canonical binary CSR form.

    ``n`` and ``m`` are the full block and check counts. The first ``n-m``
    columns are information columns of the explicit ``information_degree``;
    the final ``m`` columns form ``T``. Equal-degree row ties are ordered by
    ``(row - tie_offset) mod m``. The fallback count records individual row
    placements that had to relax four-cycle avoidance.
    """
    n = _explicit_integer(n, "n")
    m = _explicit_integer(m, "m")
    information_degree = _explicit_integer(
        information_degree, "information_degree"
    )
    tie_offset = _explicit_integer(tie_offset, "tie_offset")

    if m < 1:
        raise ValueError("m must be at least 1")
    if n < m:
        raise ValueError("n must be at least m")
    if not 1 <= information_degree <= m:
        raise ValueError("information_degree must lie in [1, m]")

    information_columns = n - m
    tie_order = [(row - tie_offset) % m for row in range(m)]

    # T contributes one edge to row 0 and two to every later row. Adjacent
    # rows already share one accumulator column and must be cycle-protected.
    row_degrees = [1] + [2] * (m - 1)
    row_heap = [
        (row_degrees[row], tie_order[row], row) for row in range(m)
    ]
    heapq.heapify(row_heap)
    shared_row_pairs = {(row, row + 1) for row in range(m - 1)}

    row_indices: list[int] = []
    column_indices: list[int] = []
    fallback_count = 0

    for column in range(information_columns):
        selected_rows: list[int] = []
        for _ in range(information_degree):
            skipped: list[tuple[int, int, int]] = []
            selected_entry: tuple[int, int, int] | None = None

            while row_heap:
                entry = heapq.heappop(row_heap)
                row = entry[2]
                if any(
                    _row_pair(row, selected) in shared_row_pairs
                    for selected in selected_rows
                ):
                    skipped.append(entry)
                else:
                    selected_entry = entry
                    break

            if selected_entry is None:
                # All remaining rows are forbidden with an already selected
                # row. skipped preserves heap order, so its first row is the
                # least-degree row under the configured deterministic tie.
                selected_entry = skipped.pop(0)
                fallback_count += 1

            for entry in skipped:
                heapq.heappush(row_heap, entry)

            row = selected_entry[2]
            selected_rows.append(row)
            row_indices.append(row)
            column_indices.append(column)

        # Update degrees once this column is selected; the chosen rows have
        # been temporarily removed while the remaining rows are ranked.
        for row in selected_rows:
            row_degrees[row] += 1
            heapq.heappush(row_heap, (row_degrees[row], tie_order[row], row))

        for left, right in itertools.combinations(selected_rows, 2):
            shared_row_pairs.add(_row_pair(left, right))

    # T has a one on its diagonal and immediately below it where that row
    # exists: T[row, column] = 1 for row == column or row == column + 1.
    for column in range(m):
        full_column = information_columns + column
        row_indices.append(column)
        column_indices.append(full_column)
        if column + 1 < m:
            row_indices.append(column + 1)
            column_indices.append(full_column)

    parity_check_matrix = sparse.coo_matrix(
        (
            np.ones(len(row_indices), dtype=np.uint8),
            (
                np.asarray(row_indices, dtype=np.int64),
                np.asarray(column_indices, dtype=np.int64),
            ),
        ),
        shape=(m, n),
        dtype=np.uint8,
    ).tocsr()
    parity_check_matrix.sum_duplicates()
    parity_check_matrix.eliminate_zeros()
    parity_check_matrix.sort_indices()

    return SparseCodeConstruction(
        parity_check_matrix=parity_check_matrix,
        four_cycle_fallback_count=fallback_count,
    )
