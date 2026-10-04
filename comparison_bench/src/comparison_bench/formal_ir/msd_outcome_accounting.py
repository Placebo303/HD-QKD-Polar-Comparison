"""Outcome and expected-yield accounting for complete native symbol blocks.

Tag serialization and the actual verification protocol are supplied by the
caller.  This module contains no cryptographic primitive and evaluates no
decoder or scientific input.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import operator
from typing import Callable, Sequence

import numpy as np


OUTCOMES = (
    "syndrome_rejected",
    "tag_rejected",
    "verified_exact",
    "accepted_wrong",
)
_INT64 = np.iinfo(np.int64)


@dataclass(frozen=True)
class BlockOutcome:
    """One candidate's local verification outcome, without security claims."""

    outcome: str
    N_symbols: int
    syndrome_ok: bool
    exact_match: bool | None
    tag_match: bool | None
    operationally_accepted: bool


@dataclass(frozen=True)
class NativeBlockLedger:
    """Actual costs and expected-yield terms for one native block."""

    N_symbols: int
    outcome: str
    disclosure_bits: int
    tag_bits: int
    H_A_total_bits: float
    kept_bits: float
    failure_indicator: int
    failure_penalty_bits: float
    Y_expected_bits: float
    expected_f_numerator_bits: float
    H_A_given_B_total_bits: float
    f_expected_dimensionless: float | None
    valid_yield: bool


@dataclass(frozen=True)
class AggregateLedger:
    """Sums of native ledgers, retaining the per-block failure weighting."""

    block_count: int
    N_symbols: int
    outcome_counts: tuple[tuple[str, int], ...]
    H_A_total_bits: float
    H_A_given_B_total_bits: float
    disclosure_bits: int
    tag_bits: int
    kept_bits: float
    failure_indicator_sum: int
    failure_penalty_bits: float
    Y_expected_bits: float
    expected_f_numerator_bits: float
    f_expected_dimensionless: float | None
    valid_yield: bool


@dataclass(frozen=True)
class PairedYieldComparison:
    """Long-minus-control f comparison at one matched complete-symbol volume."""

    long: AggregateLedger
    control: AggregateLedger
    f_difference_long_minus_control: float | None


def _alphabet(alphabet_size: object) -> int:
    if isinstance(alphabet_size, (bool, np.bool_)):
        raise ValueError("alphabet_size must be a positive int64-representable integer")
    try:
        size = operator.index(alphabet_size)
    except TypeError as exc:
        raise ValueError("alphabet_size must be a positive int64-representable integer") from exc
    if size <= 0 or size > _INT64.max:
        raise ValueError("alphabet_size must be a positive int64-representable integer")
    return size


def _natural_symbols(values: object, *, name: str, alphabet_size: int) -> np.ndarray:
    raw = np.asarray(values)
    if raw.ndim != 1:
        raise ValueError(f"{name} must be a one-dimensional integer vector")
    if raw.dtype.kind not in "iu":
        raise ValueError(f"{name} must contain integer symbols")
    if raw.size:
        if raw.dtype.kind == "u" and np.any(raw > _INT64.max):
            raise ValueError(f"{name} symbols must be representable as np.int64")
        if raw.dtype.kind == "i" and (
            np.any(raw < _INT64.min) or np.any(raw > _INT64.max)
        ):
            raise ValueError(f"{name} symbols must be representable as np.int64")
        if np.any(raw < 0) or np.any(raw >= alphabet_size):
            raise ValueError(f"{name} symbols must lie in [0, {alphabet_size})")
    return raw.astype(np.int64, copy=True)


def _tag_bytes(tag_function: Callable[[np.ndarray], bytes], symbols: np.ndarray) -> bytes:
    result = tag_function(symbols.copy())
    if not isinstance(result, bytes):
        raise ValueError("tag_function must return bytes")
    return result


def evaluate_block_outcome(
    alice_natural_symbols: object,
    receiver_natural_symbols: object | None,
    *,
    alphabet_size: int,
    syndrome_ok: bool,
    tag_function: Callable[[np.ndarray], bytes],
) -> BlockOutcome:
    """Classify one complete candidate using a caller-owned byte tag function.

    The callback receives a disposable copy of the validated natural-symbol
    vector as ``np.int64``.  It returns bytes; serialization remains the
    caller's responsibility.  Alice truth is not an input to the receiver.
    """

    size = _alphabet(alphabet_size)
    if not isinstance(syndrome_ok, (bool, np.bool_)):
        raise ValueError("syndrome_ok must be bool")
    syndrome_passed = bool(syndrome_ok)
    if not callable(tag_function):
        raise ValueError("tag_function must be explicitly callable")

    alice = _natural_symbols(
        alice_natural_symbols, name="alice_natural_symbols", alphabet_size=size
    )
    candidate = None
    if receiver_natural_symbols is not None:
        candidate = _natural_symbols(
            receiver_natural_symbols,
            name="receiver_natural_symbols",
            alphabet_size=size,
        )
        if candidate.size != alice.size:
            raise ValueError("receiver_natural_symbols must match the sender block length")
    if syndrome_passed and candidate is None:
        raise ValueError("a syndrome-passing outcome requires a complete receiver candidate")

    exact_match = (
        bool(np.array_equal(alice, candidate)) if candidate is not None else None
    )
    reference_tag = _tag_bytes(tag_function, alice)
    if not syndrome_passed:
        return BlockOutcome(
            outcome="syndrome_rejected",
            N_symbols=int(alice.size),
            syndrome_ok=False,
            exact_match=exact_match,
            tag_match=None,
            operationally_accepted=False,
        )

    assert candidate is not None
    candidate_tag = _tag_bytes(tag_function, candidate)
    tag_match = candidate_tag == reference_tag
    if not tag_match:
        outcome = "tag_rejected"
    elif exact_match:
        outcome = "verified_exact"
    else:
        outcome = "accepted_wrong"
    return BlockOutcome(
        outcome=outcome,
        N_symbols=int(alice.size),
        syndrome_ok=True,
        exact_match=exact_match,
        tag_match=tag_match,
        operationally_accepted=bool(tag_match),
    )


def _integer_cost(value: object, *, name: str) -> int:
    if isinstance(value, (bool, np.bool_)):
        raise ValueError(f"{name} must be a nonnegative integer bit count")
    try:
        count = operator.index(value)
    except TypeError as exc:
        raise ValueError(f"{name} must be a nonnegative integer bit count") from exc
    if count < 0:
        raise ValueError(f"{name} must be a nonnegative integer bit count")
    return count


def _finite_real(value: object, *, name: str) -> float:
    if isinstance(value, (bool, np.bool_, str, bytes)):
        raise ValueError(f"{name} must be a finite real number")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be a finite real number") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def native_block_ledger(
    *,
    N_symbols: int,
    H_A_bits_per_symbol: float,
    H_A_given_B_bits_per_symbol: float,
    disclosure_bits: int,
    tag_bits: int,
    classification: BlockOutcome,
) -> NativeBlockLedger:
    """Account actual native-block bits and the classified outcome."""

    if isinstance(N_symbols, (bool, np.bool_)):
        raise ValueError("N_symbols must be a positive integer")
    try:
        N = operator.index(N_symbols)
    except TypeError as exc:
        raise ValueError("N_symbols must be a positive integer") from exc
    if N <= 0:
        raise ValueError("N_symbols must be a positive integer")
    H_A = _finite_real(H_A_bits_per_symbol, name="H_A_bits_per_symbol")
    H_AB = _finite_real(
        H_A_given_B_bits_per_symbol, name="H_A_given_B_bits_per_symbol"
    )
    if H_A < 0.0 or H_AB < 0.0 or H_AB > H_A:
        raise ValueError("entropies must satisfy 0 <= H(A|B) <= H(A)")
    disclosed = _integer_cost(disclosure_bits, name="disclosure_bits")
    tag = _integer_cost(tag_bits, name="tag_bits")
    if not isinstance(classification, BlockOutcome) or classification.outcome not in OUTCOMES:
        raise ValueError("classification must be a valid L1 BlockOutcome")
    if N != classification.N_symbols:
        raise ValueError("N_symbols must match the classified sender vector length")

    H_A_total = N * H_A
    kept = H_A_total - disclosed
    failure_indicator = int(classification.outcome != "verified_exact")
    failure_penalty = kept * failure_indicator
    expected_yield = kept - tag - failure_penalty
    numerator = disclosed + tag + failure_penalty
    denominator = N * H_AB
    valid_yield = kept >= 0.0
    f_expected = numerator / denominator if valid_yield and denominator > 0.0 else None
    return NativeBlockLedger(
        N_symbols=N,
        outcome=classification.outcome,
        disclosure_bits=disclosed,
        tag_bits=tag,
        H_A_total_bits=H_A_total,
        kept_bits=kept,
        failure_indicator=failure_indicator,
        failure_penalty_bits=failure_penalty,
        Y_expected_bits=expected_yield,
        expected_f_numerator_bits=numerator,
        H_A_given_B_total_bits=denominator,
        f_expected_dimensionless=f_expected,
        valid_yield=valid_yield,
    )


def aggregate_native_ledgers(ledgers: Sequence[NativeBlockLedger]) -> AggregateLedger:
    """Sum native ledgers, preserving each block's own kept-bits penalty."""

    blocks = tuple(ledgers)
    if not blocks:
        raise ValueError("at least one native block ledger is required")
    if any(not isinstance(block, NativeBlockLedger) for block in blocks):
        raise ValueError("all entries must be NativeBlockLedger values")

    counts = tuple((outcome, sum(block.outcome == outcome for block in blocks)) for outcome in OUTCOMES)
    H_A_total = math.fsum(block.H_A_total_bits for block in blocks)
    H_AB_total = math.fsum(block.H_A_given_B_total_bits for block in blocks)
    disclosure = sum(block.disclosure_bits for block in blocks)
    tags = sum(block.tag_bits for block in blocks)
    kept = math.fsum(block.kept_bits for block in blocks)
    failure_penalties = math.fsum(block.failure_penalty_bits for block in blocks)
    failure_sum = sum(block.failure_indicator for block in blocks)
    expected_yield = math.fsum(block.Y_expected_bits for block in blocks)
    numerator = disclosure + tags + failure_penalties
    valid_yield = all(block.valid_yield for block in blocks)
    f_expected = numerator / H_AB_total if valid_yield and H_AB_total > 0.0 else None
    return AggregateLedger(
        block_count=len(blocks),
        N_symbols=sum(block.N_symbols for block in blocks),
        outcome_counts=counts,
        H_A_total_bits=H_A_total,
        H_A_given_B_total_bits=H_AB_total,
        disclosure_bits=disclosure,
        tag_bits=tags,
        kept_bits=kept,
        failure_indicator_sum=failure_sum,
        failure_penalty_bits=failure_penalties,
        Y_expected_bits=expected_yield,
        expected_f_numerator_bits=numerator,
        f_expected_dimensionless=f_expected,
        valid_yield=valid_yield,
    )


def compare_paired_native_ledgers(
    long_ledgers: Sequence[NativeBlockLedger],
    control_ledgers: Sequence[NativeBlockLedger],
) -> PairedYieldComparison:
    """Compare aggregate f at equal input volume and common entropy totals.

    Source and role provenance are caller-owned and cannot be inferred from
    matching numerical totals.
    """

    long = aggregate_native_ledgers(long_ledgers)
    control = aggregate_native_ledgers(control_ledgers)
    if long.N_symbols != control.N_symbols:
        raise ValueError("paired ledgers must have equal complete-symbol volume")
    if not math.isclose(long.H_A_total_bits, control.H_A_total_bits, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError("paired ledgers must have a common H_A_total_bits")
    if not math.isclose(
        long.H_A_given_B_total_bits,
        control.H_A_given_B_total_bits,
        rel_tol=0.0,
        abs_tol=1e-9,
    ):
        raise ValueError("paired ledgers must have a common H_A_given_B_total_bits")
    difference = (
        long.f_expected_dimensionless - control.f_expected_dimensionless
        if long.f_expected_dimensionless is not None
        and control.f_expected_dimensionless is not None
        else None
    )
    return PairedYieldComparison(long, control, difference)
