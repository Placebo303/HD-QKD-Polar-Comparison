"""Conditional bit priors and a small soft-error adapter for MSD work.

Joint-count rows are natural Alice symbols and columns are natural Bob
symbols. ``GRAY`` maps each natural Alice symbol ``a`` to ``a ^ (a >> 1)``
before selecting bit planes; Bob symbols are never relabeled. Decode-order
prefix rows in a query are ordered by stage, not by bit index.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import operator
from typing import Sequence

import numpy as np

from .msd_information_budget import _normalize_order, validate_counts


@dataclass(frozen=True)
class ConditionalPriorStage:
    """One ordered Alice bit plane, indexed by ``[natural Bob, prefix]``."""

    alice_bit_index_from_lsb: int
    p_one_by_bob_prefix: np.ndarray
    support_by_bob_prefix: np.ndarray


@dataclass(frozen=True)
class PriorQuery:
    """Receiver-side conditional priors for a batch of natural Bob symbols."""

    p_one: np.ndarray
    unsupported: np.ndarray


@dataclass(frozen=True)
class SoftErrorPrior:
    """Binary receiver inputs derived from a conditional-prior query."""

    base_bits: np.ndarray
    p_error: np.ndarray
    llr_natural_log: np.ndarray
    unsupported: np.ndarray


@dataclass(frozen=True)
class ConditionalPriorModel:
    """Per-stage conditional tables and a truth-free receiver query."""

    alphabet_size: int
    encoding: str
    order_name: str
    bit_order_from_lsb: tuple[int, ...]
    stages: tuple[ConditionalPriorStage, ...]

    def query(
        self,
        stage_index: int,
        natural_bob_symbols: object,
        previous_stage_bits: object,
    ) -> PriorQuery:
        """Query using Bob symbols and prior decoded bits only.

        ``previous_stage_bits`` has shape ``(stage_index, N)``. Row ``j`` is
        the already-decoded bit at stage ``j`` in this model's declared order.
        Unsupported Bob/prefix combinations return ``p_one=0.5`` and are
        marked in ``unsupported``.
        """
        if isinstance(stage_index, (bool, np.bool_)):
            raise ValueError("stage_index must be an integer stage")
        try:
            stage = operator.index(stage_index)
        except TypeError as exc:
            raise ValueError("stage_index must be an integer stage") from exc
        if stage < 0 or stage >= len(self.stages):
            raise ValueError("stage_index is outside the bit-plane range")

        bob = _natural_symbol_vector(natural_bob_symbols, self.alphabet_size)
        raw_previous = np.asarray(previous_stage_bits)
        expected_shape = (stage, bob.size)
        if raw_previous.ndim != 2 or raw_previous.shape != expected_shape:
            raise ValueError(
                f"previous_stage_bits must have shape {expected_shape}"
            )
        if raw_previous.dtype.kind not in "biu":
            raise ValueError("previous_stage_bits must contain binary integers")
        if np.any((raw_previous < 0) | (raw_previous > 1)):
            raise ValueError("previous_stage_bits must contain only 0 or 1")

        prefix = np.zeros(bob.size, dtype=np.int64)
        for prior_stage in range(stage):
            prefix |= raw_previous[prior_stage].astype(np.int64) << prior_stage

        prior_stage = self.stages[stage]
        supported = prior_stage.support_by_bob_prefix[bob, prefix]
        p_one = prior_stage.p_one_by_bob_prefix[bob, prefix].copy()
        unsupported = ~supported
        p_one[unsupported] = 0.5
        return PriorQuery(p_one=p_one, unsupported=unsupported)


def _normalize_encoding(encoding: str) -> str:
    if not isinstance(encoding, str):
        raise ValueError("encoding must be NATURAL or GRAY")
    normalized = encoding.strip().upper()
    if normalized not in {"NATURAL", "GRAY"}:
        raise ValueError("encoding must be NATURAL or GRAY")
    return normalized


def _natural_symbol_vector(symbols: object, alphabet_size: int) -> np.ndarray:
    raw = np.asarray(symbols)
    if raw.ndim != 1:
        raise ValueError("natural_bob_symbols must be a one-dimensional vector")
    if raw.size == 0:
        return np.empty(0, dtype=np.int64)
    if raw.dtype.kind not in "iu":
        raise ValueError("natural Bob symbols must be integer indices")
    if np.any(raw >= alphabet_size) or (
        raw.dtype.kind == "i" and np.any(raw < 0)
    ):
        raise ValueError("natural Bob symbol is outside the alphabet")
    return raw.astype(np.int64, copy=False)


def build_conditional_prior_model(
    counts: object,
    *,
    encoding: str,
    order: str | Sequence[int],
) -> ConditionalPriorModel:
    """Build ``P(A_bit=1 | natural B, preceding decoded Alice bits)`` tables.

    Counts are validated with the same finite, nonnegative, square-table and
    complete-order rules used by the P1 information-budget analysis. Rows are
    Alice natural symbols; Gray encoding relabels only the Alice bit label.
    """
    table = validate_counts(counts)
    q = int(table.shape[0])
    n_planes = q.bit_length() - 1
    bit_order, order_name = _normalize_order(order, n_planes)
    normalized_encoding = _normalize_encoding(encoding)

    natural_alice = np.arange(q, dtype=np.int64)
    if normalized_encoding == "GRAY":
        alice_labels = natural_alice ^ (natural_alice >> 1)
    else:
        alice_labels = natural_alice
    natural_bob = np.arange(q, dtype=np.int64)
    stages: list[ConditionalPriorStage] = []

    for stage_index, bit_index in enumerate(bit_order):
        prefix = np.zeros(q, dtype=np.int64)
        for prefix_position, prior_bit_index in enumerate(bit_order[:stage_index]):
            prefix |= (
                ((alice_labels >> prior_bit_index) & 1) << prefix_position
            )
        target_bit = ((alice_labels >> bit_index) & 1).astype(np.float64)
        n_prefixes = 1 << stage_index
        group_codes = (
            natural_bob[None, :] * n_prefixes + prefix[:, None]
        )
        total_mass = np.bincount(
            group_codes.ravel(),
            weights=table.ravel(),
            minlength=q * n_prefixes,
        ).reshape(q, n_prefixes)
        one_mass = np.bincount(
            group_codes.ravel(),
            weights=(table * target_bit[:, None]).ravel(),
            minlength=q * n_prefixes,
        ).reshape(q, n_prefixes)
        support = total_mass > 0.0
        p_one = np.full((q, n_prefixes), 0.5, dtype=np.float64)
        np.divide(one_mass, total_mass, out=p_one, where=support)
        stages.append(
            ConditionalPriorStage(
                alice_bit_index_from_lsb=int(bit_index),
                p_one_by_bob_prefix=p_one,
                support_by_bob_prefix=support,
            )
        )

    return ConditionalPriorModel(
        alphabet_size=q,
        encoding=normalized_encoding,
        order_name=order_name,
        bit_order_from_lsb=tuple(int(bit) for bit in bit_order),
        stages=tuple(stages),
    )


def adapt_soft_error_prior(
    query: PriorQuery,
    *,
    llr_floor: float,
) -> SoftErrorPrior:
    """Map ``p_one`` to a hard base, error probability and natural-log LLR.

    The tie rule is base bit 0. LLR is ``log(P0/P1)`` after flooring each
    probability at the caller-supplied value; the floor must lie in ``(0,.5)``.
    """
    if not isinstance(query, PriorQuery):
        raise ValueError("query must be a PriorQuery")
    if isinstance(llr_floor, (bool, np.bool_)):
        raise ValueError("llr_floor must lie strictly between 0 and 0.5")
    try:
        floor = float(llr_floor)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("llr_floor must lie strictly between 0 and 0.5") from exc
    if not math.isfinite(floor) or not 0.0 < floor < 0.5:
        raise ValueError("llr_floor must lie strictly between 0 and 0.5")

    raw_p_one = np.asarray(query.p_one)
    if np.iscomplexobj(raw_p_one):
        raise ValueError("p_one must contain probabilities in [0, 1]")
    p_one = np.asarray(raw_p_one, dtype=np.float64)
    unsupported = np.asarray(query.unsupported)
    if p_one.ndim != 1 or unsupported.shape != p_one.shape:
        raise ValueError("p_one and unsupported must be matching one-dimensional vectors")
    if unsupported.dtype.kind != "b":
        raise ValueError("unsupported must be a boolean vector")
    if not np.all(np.isfinite(p_one)) or np.any((p_one < 0.0) | (p_one > 1.0)):
        raise ValueError("p_one must contain probabilities in [0, 1]")

    base_bits = (p_one > 0.5).astype(np.uint8)
    p_error = np.minimum(p_one, 1.0 - p_one)
    p_zero_floored = np.maximum(1.0 - p_one, floor)
    p_one_floored = np.maximum(p_one, floor)
    llr = np.log(p_zero_floored) - np.log(p_one_floored)
    return SoftErrorPrior(
        base_bits=base_bits,
        p_error=p_error,
        llr_natural_log=llr,
        unsupported=unsupported.copy(),
    )
