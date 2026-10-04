"""Fixed algebraic integration checks for the MSD sparse sender/receiver path."""

from __future__ import annotations

import numpy as np
import pytest
from scipy import sparse

from comparison_bench.src.comparison_bench.formal_ir import msd_conditional_prior
from comparison_bench.src.comparison_bench.formal_ir import msd_sparse_code
from comparison_bench.src.comparison_bench.formal_ir import msd_syndrome


ALPHABET_SIZE = 1024
ALICE_BOB_XOR = 513


def _fixed_bijection_case(n: int, encoding: str, order: str):
    bob = (np.arange(n, dtype=np.int64) % ALPHABET_SIZE).astype(np.uint16)
    alice = np.bitwise_xor(bob.astype(np.int64), ALICE_BOB_XOR).astype(np.uint16)

    counts = np.zeros((ALPHABET_SIZE, ALPHABET_SIZE), dtype=np.float64)
    bob_alphabet = np.arange(ALPHABET_SIZE, dtype=np.int64)
    alice_alphabet = np.bitwise_xor(bob_alphabet, ALICE_BOB_XOR)
    counts[alice_alphabet, bob_alphabet] = 1.0
    model = msd_conditional_prior.build_conditional_prior_model(
        counts, encoding=encoding, order=order
    )
    return model, bob, alice


def _must_not_call_backend(calls: list[object]):
    def factory(**kwargs):
        calls.append(kwargs)
        raise AssertionError("deterministic structural fixture called a backend")

    return factory


def _assert_exact_receiver_result(result, alice: np.ndarray, expected_rows: int) -> None:
    assert np.array_equal(result.reconstructed_natural_symbols, alice)
    assert result.attempted_stage_syndrome_passed == (True,) * 10
    assert result.unsupported_counts_by_attempted_stage == (0,) * 10
    assert result.transmitted_row_count_bits_per_block == expected_rows


def _assert_corrupted_first_syndrome_stops(
    *,
    model,
    bob: np.ndarray,
    matrices: tuple[sparse.csr_matrix, ...],
    public_syndromes: tuple[np.ndarray, ...],
    mode: str,
    expected_rows: int,
) -> None:
    corrupted = [value.copy() for value in public_syndromes]
    corrupted[0][0] ^= np.uint8(1)
    calls: list[object] = []
    options = (
        {"skip_fully_deterministic": True}
        if mode == "bypass"
        else {"condition_exact_variables": True}
    )

    result = msd_syndrome.receive_syndromes(
        model,
        bob,
        matrices,
        corrupted,
        _must_not_call_backend(calls),
        **options,
    )

    assert calls == []
    assert result.attempted_stage_syndrome_passed == (False,)
    assert len(result.recovered_stage_bits) == 1
    assert result.reconstructed_natural_symbols is None
    assert result.transmitted_row_count_bits_per_block == expected_rows


@pytest.mark.parametrize(
    ("n", "encoding", "order"),
    [
        pytest.param(1024, "NATURAL", "LSB_FIRST", id="natural-lsb-n1024"),
        pytest.param(16384, "GRAY", "MSB_FIRST", id="gray-msb-n16384"),
    ],
)
def test_full_alphabet_sparse_sender_receiver_known_limit(
    n: int, encoding: str, order: str
) -> None:
    model, bob, alice = _fixed_bijection_case(n, encoding, order)
    m = n // 2
    construction = msd_sparse_code.build_msd_sparse_code(
        n=n, m=m, information_degree=3, tie_offset=0
    )
    matrix = construction.parity_check_matrix

    assert sparse.isspmatrix_csr(matrix)
    assert matrix.shape == (m, n)
    assert matrix.dtype == np.dtype(np.uint8)
    assert matrix.has_canonical_format
    assert np.all((matrix.data == 0) | (matrix.data == 1))

    matrices = (matrix,) * len(model.stages)
    assert len(matrices) == 10
    assert all(stage_matrix is matrix for stage_matrix in matrices)
    disclosure = msd_syndrome.disclose_syndromes(alice, model, matrices)
    expected_rows = 10 * m
    assert len(disclosure.public_syndromes) == 10
    assert disclosure.transmitted_row_count_bits_per_block == expected_rows

    # Recompute selected public bits by XORing encoded Alice bits at the CSR
    # row's column indices, independently of the sender's matrix product.
    labels = (
        alice.astype(np.int64) ^ (alice.astype(np.int64) >> 1)
        if encoding == "GRAY"
        else alice.astype(np.int64)
    )
    selected_rows = (0, m // 3, m - 1)
    for stage, bit_index in enumerate(model.bit_order_from_lsb):
        encoded_plane = ((labels >> bit_index) & 1).astype(np.uint8)
        for row in selected_rows:
            parity = 0
            start, stop = matrix.indptr[row : row + 2]
            for column in matrix.indices[start:stop]:
                parity ^= int(encoded_plane[column])
            assert int(disclosure.public_syndromes[stage][row]) == parity

    bob_copy = bob.copy()
    syndromes_copy = tuple(value.copy() for value in disclosure.public_syndromes)
    matrix_data = matrix.data.copy()
    matrix_indices = matrix.indices.copy()
    matrix_indptr = matrix.indptr.copy()

    for mode, options in (
        ("bypass", {"skip_fully_deterministic": True}),
        ("conditioning", {"condition_exact_variables": True}),
    ):
        calls: list[object] = []
        result = msd_syndrome.receive_syndromes(
            model,
            bob,
            matrices,
            disclosure.public_syndromes,
            _must_not_call_backend(calls),
            **options,
        )
        assert calls == [], mode
        _assert_exact_receiver_result(result, alice, expected_rows)
        _assert_corrupted_first_syndrome_stops(
            model=model,
            bob=bob,
            matrices=matrices,
            public_syndromes=disclosure.public_syndromes,
            mode=mode,
            expected_rows=expected_rows,
        )

    assert np.array_equal(bob, bob_copy)
    for actual, expected in zip(disclosure.public_syndromes, syndromes_copy):
        assert np.array_equal(actual, expected)
    assert np.array_equal(matrix.data, matrix_data)
    assert np.array_equal(matrix.indices, matrix_indices)
    assert np.array_equal(matrix.indptr, matrix_indptr)
