"""Sender syndromes and a truth-free conditional-prior receiver boundary.

The sender alone accepts natural Alice symbols. The receiver accepts natural
Bob symbols and public syndromes, and propagates the bits actually recovered
at each preceding stage. A passing syndrome check is not verified success.
"""

from __future__ import annotations

from dataclasses import dataclass
import operator
from typing import Callable, Sequence

import numpy as np
from scipy import sparse

from .msd_conditional_prior import ConditionalPriorModel


@dataclass(frozen=True)
class SyndromeDisclosure:
    """Public syndromes and their transmitted disclosure in bits per block."""

    public_syndromes: tuple[np.ndarray, ...]
    transmitted_row_count_bits_per_block: int


@dataclass(frozen=True)
class SyndromeReceiverResult:
    """Receiver outputs without a success, FER, tag, or truth-comparison field."""

    recovered_stage_bits: tuple[np.ndarray, ...]
    reconstructed_natural_symbols: np.ndarray | None
    attempted_stage_syndrome_passed: tuple[bool, ...]
    unsupported_counts_by_attempted_stage: tuple[int, ...]
    transmitted_row_count_bits_per_block: int


def _integer_vector(values: object, *, name: str, upper_bound: int) -> np.ndarray:
    raw = np.asarray(values)
    if raw.ndim != 1:
        raise ValueError(f"{name} must be a one-dimensional integer vector")
    if raw.size == 0:
        return np.empty(0, dtype=np.int64)
    if raw.dtype.kind not in "iu":
        raise ValueError(f"{name} must contain integer symbols")
    if np.any(raw >= upper_bound) or (
        raw.dtype.kind == "i" and np.any(raw < 0)
    ):
        raise ValueError(f"{name} symbols must lie in [0, {upper_bound})")
    return raw.astype(np.int64, copy=False)


def _parity_matrix(matrix: object, *, block_width: int, stage: int) -> sparse.csr_matrix:
    if not sparse.isspmatrix_csr(matrix):
        raise ValueError(f"parity_check_matrix[{stage}] must be a CSR matrix")
    if matrix.shape[1] != block_width:
        raise ValueError(
            f"parity_check_matrix[{stage}] must have {block_width} columns"
        )
    values = np.asarray(matrix.data)
    if values.dtype.kind not in "biuf" or not np.all((values == 0) | (values == 1)):
        raise ValueError(f"parity_check_matrix[{stage}] must be binary")
    if not matrix.has_canonical_format:
        raise ValueError(f"parity_check_matrix[{stage}] must use canonical CSR format")
    return matrix


def _stage_matrices(
    model: ConditionalPriorModel,
    matrices: object,
    *,
    block_width: int,
) -> tuple[sparse.csr_matrix, ...]:
    if not isinstance(model, ConditionalPriorModel):
        raise ValueError("model must be a ConditionalPriorModel")
    try:
        rows = tuple(matrices)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("parity_check_matrices must be a stage sequence") from exc
    if len(rows) != len(model.stages):
        raise ValueError("one parity-check matrix is required for each model stage")
    return tuple(
        _parity_matrix(matrix, block_width=block_width, stage=stage)
        for stage, matrix in enumerate(rows)
    )


def _binary_vector(values: object, *, length: int, name: str) -> np.ndarray:
    raw = np.asarray(values)
    if raw.ndim != 1 or raw.shape != (length,):
        raise ValueError(f"{name} must be a length-{length} vector")
    if raw.dtype.kind not in "biu" or np.any((raw < 0) | (raw > 1)):
        raise ValueError(f"{name} must contain only binary values 0 or 1")
    return raw.astype(np.uint8, copy=False)


def _decoder_error_vector(values: object, *, block_width: int) -> np.ndarray:
    raw = np.asarray(values)
    if raw.ndim != 1 or raw.shape != (block_width,):
        raise ValueError(
            f"decoder output must be a length-{block_width} binary vector"
        )
    if raw.dtype.kind not in "biuf" or not np.all(np.isfinite(raw)):
        raise ValueError("decoder output must contain binary values 0 or 1")
    if np.any((raw != 0) & (raw != 1)):
        raise ValueError("decoder output must contain binary values 0 or 1")
    return raw.astype(np.uint8, copy=False)


def _syndrome(matrix: sparse.csr_matrix, bits: np.ndarray) -> np.ndarray:
    product = matrix.astype(np.int64, copy=False) @ bits.astype(np.int64, copy=False)
    return np.asarray(product % 2, dtype=np.uint8).reshape(-1)


def _encoded_alice_symbols(
    natural_symbols: np.ndarray, model: ConditionalPriorModel
) -> np.ndarray:
    if model.encoding == "NATURAL":
        return natural_symbols
    if model.encoding == "GRAY":
        return natural_symbols ^ (natural_symbols >> 1)
    raise ValueError("model encoding must be NATURAL or GRAY")


def _natural_symbols_from_stages(
    stage_bits: Sequence[np.ndarray], model: ConditionalPriorModel, block_width: int
) -> np.ndarray:
    labels = np.zeros(block_width, dtype=np.int64)
    for stage, bit_index in enumerate(model.bit_order_from_lsb):
        labels |= stage_bits[stage].astype(np.int64) << bit_index
    if model.encoding == "NATURAL":
        return labels
    if model.encoding == "GRAY":
        natural = labels.copy()
        for shift in range(1, len(model.bit_order_from_lsb)):
            natural ^= labels >> shift
        return natural
    raise ValueError("model encoding must be NATURAL or GRAY")


def disclose_syndromes(
    alice_natural_symbols: object,
    model: ConditionalPriorModel,
    parity_check_matrices: object,
) -> SyndromeDisclosure:
    """Transmit one syndrome per stage and count every disclosed row bit."""
    if not isinstance(model, ConditionalPriorModel):
        raise ValueError("model must be a ConditionalPriorModel")
    alice = _integer_vector(
        alice_natural_symbols,
        name="alice_natural_symbols",
        upper_bound=model.alphabet_size,
    )
    matrices = _stage_matrices(
        model, parity_check_matrices, block_width=alice.size
    )
    labels = _encoded_alice_symbols(alice, model)
    syndromes: list[np.ndarray] = []
    for stage, (bit_index, matrix) in enumerate(
        zip(model.bit_order_from_lsb, matrices)
    ):
        plane = ((labels >> bit_index) & 1).astype(np.uint8)
        syndromes.append(_syndrome(matrix, plane))
    transmitted_rows = sum(int(matrix.shape[0]) for matrix in matrices)
    return SyndromeDisclosure(tuple(syndromes), transmitted_rows)


def receive_syndromes(
    model: ConditionalPriorModel,
    bob_natural_symbols: object,
    parity_check_matrices: object,
    public_syndromes: object,
    decoder_factory: Callable[..., object],
) -> SyndromeReceiverResult:
    """Decode stages from Bob/public inputs using only recovered prefixes.

    Callers selecting :func:`make_bp_decoder` must bind its required
    ``max_iter`` first, for example with ``functools.partial``. This receiver
    has no default decoder factory and no Alice-truth argument.
    """
    if not isinstance(model, ConditionalPriorModel):
        raise ValueError("model must be a ConditionalPriorModel")
    if not callable(decoder_factory):
        raise ValueError("decoder_factory must be explicitly callable")
    bob = _integer_vector(
        bob_natural_symbols,
        name="bob_natural_symbols",
        upper_bound=model.alphabet_size,
    )
    matrices = _stage_matrices(
        model, parity_check_matrices, block_width=bob.size
    )
    try:
        raw_syndromes = tuple(public_syndromes)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("public_syndromes must be a stage sequence") from exc
    if len(raw_syndromes) != len(matrices):
        raise ValueError("one public syndrome is required for each model stage")
    syndromes = tuple(
        _binary_vector(syndrome, length=matrix.shape[0], name=f"syndrome[{stage}]")
        for stage, (syndrome, matrix) in enumerate(zip(raw_syndromes, matrices))
    )

    transmitted_rows = sum(int(matrix.shape[0]) for matrix in matrices)
    recovered: list[np.ndarray] = []
    syndrome_passed: list[bool] = []
    unsupported_counts: list[int] = []
    for stage, matrix in enumerate(matrices):
        if recovered:
            previous_bits = np.stack(recovered, axis=0)
        else:
            previous_bits = np.empty((0, bob.size), dtype=np.uint8)
        query = model.query(stage, bob, previous_bits)
        base = (query.p_one > 0.5).astype(np.uint8)
        error_channel = np.minimum(query.p_one, 1.0 - query.p_one)
        delta = np.bitwise_xor(syndromes[stage], _syndrome(matrix, base))

        decoder = decoder_factory(
            parity_check_matrix=matrix,
            error_channel=error_channel.copy(),
        )
        decode = getattr(decoder, "decode", None)
        if not callable(decode):
            raise ValueError("decoder_factory must return an object with decode()")
        error = _decoder_error_vector(decode(delta), block_width=bob.size)
        recovered_stage = np.bitwise_xor(base, error)
        recovered.append(recovered_stage)
        passed = bool(np.array_equal(_syndrome(matrix, recovered_stage), syndromes[stage]))
        syndrome_passed.append(passed)
        unsupported_counts.append(int(np.count_nonzero(query.unsupported)))
        if not passed:
            break

    all_stages_passed = len(syndrome_passed) == len(matrices) and all(syndrome_passed)
    reconstructed = (
        _natural_symbols_from_stages(recovered, model, bob.size)
        if all_stages_passed
        else None
    )
    return SyndromeReceiverResult(
        recovered_stage_bits=tuple(recovered),
        reconstructed_natural_symbols=reconstructed,
        attempted_stage_syndrome_passed=tuple(syndrome_passed),
        unsupported_counts_by_attempted_stage=tuple(unsupported_counts),
        transmitted_row_count_bits_per_block=transmitted_rows,
    )


def make_bp_decoder(
    *,
    parity_check_matrix: sparse.csr_matrix,
    error_channel: object,
    max_iter: int,
) -> object:
    """Lazily construct the optional ldpc backend with an explicit budget.

    This factory is never selected by :func:`receive_syndromes` implicitly.
    Callers must bind ``max_iter`` explicitly before passing it as a factory.
    """
    if isinstance(max_iter, (bool, np.bool_)):
        raise ValueError("max_iter must be a positive integer")
    try:
        iterations = operator.index(max_iter)
    except TypeError as exc:
        raise ValueError("max_iter must be a positive integer") from exc
    if iterations <= 0:
        raise ValueError("max_iter must be a positive integer")

    matrix = _parity_matrix(
        parity_check_matrix,
        block_width=parity_check_matrix.shape[1]
        if sparse.isspmatrix_csr(parity_check_matrix)
        else -1,
        stage=0,
    )
    raw_channel = np.asarray(error_channel)
    if np.iscomplexobj(raw_channel):
        raise ValueError("error_channel must contain per-variable probabilities")
    channel = np.asarray(raw_channel, dtype=np.float64)
    if (
        channel.ndim != 1
        or channel.shape != (matrix.shape[1],)
        or not np.all(np.isfinite(channel))
        or np.any((channel < 0.0) | (channel > 1.0))
    ):
        raise ValueError("error_channel must match the block width with probabilities in [0, 1]")

    from ldpc import BpDecoder

    return BpDecoder(
        pcm=matrix,
        error_channel=channel.tolist(),
        max_iter=iterations,
        bp_method="product_sum",
        schedule="parallel",
        omp_thread_count=1,
        input_vector_type="syndrome",
        random_serial_schedule=False,
    )
