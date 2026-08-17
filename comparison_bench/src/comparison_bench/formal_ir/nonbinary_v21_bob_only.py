"""V21 Bob-only decoder strategies (diagnostic).

These strategies never access Alice.  They use only Bob-visible data: the
received word ``bob``, Alice's syndrome ``s_x``, the channel prior ``w``, and
the code matrix.  Alice is allowed only in the offline metric phase outside
this module.
"""
from __future__ import annotations

from typing import Any, Sequence

import numpy as np

from .nonbinary_field import GF2mField
from .nonbinary_v10_fftqspa import decode_fftqspa, syndrome_of
from .nonbinary_v19_bounded_ml import bounded_weight_ml_decode

__all__ = [
    "decode_bp_only",
    "decode_bounded4_only",
    "decode_bp_then_bounded4",
    "run_bob_only_strategy",
]


def _error_syndrome(field: GF2mField, matrix: Any, bob: Sequence[int],
                    s_x: Sequence[int]) -> list[int]:
    s_bob = syndrome_of(field, matrix, bob)
    return [int(field.add(int(a), int(b))) for a, b in zip(s_x, s_bob)]


def _syndrome_ok(field: GF2mField, matrix: Any, bob: Sequence[int],
                 e_hat: Sequence[int], s_x: Sequence[int]) -> bool:
    x_hat = [int(field.add(int(y), int(e))) for y, e in zip(bob, e_hat)]
    return syndrome_of(field, matrix, x_hat) == list(s_x)


def decode_bp_only(*, field: GF2mField, matrix: Any, bob: Sequence[int],
                   s_x: Sequence[int], w: Any,
                   max_iter: int = 60) -> list[int] | None:
    """S0: accept FFT-QSPA output only if syndrome-consistent."""
    s_e = _error_syndrome(field, matrix, bob, s_x)
    res = decode_fftqspa(prior=w, matrix=matrix, error_syndrome=s_e,
                         field=field, max_iter=max_iter, streak=3)
    e_hat = res.get("e_hat")
    if e_hat is None:
        return None
    if not _syndrome_ok(field, matrix, bob, e_hat, s_x):
        return None
    return list(e_hat)


def decode_bounded4_only(*, field: GF2mField, matrix: Any, bob: Sequence[int],
                         s_x: Sequence[int], w: Any,
                         max_iter: int = 60) -> list[int] | None:
    """S1: always run bounded-weight ML (max weight 4) and accept if syndrome-consistent."""
    s_e = _error_syndrome(field, matrix, bob, s_x)
    e_hat = bounded_weight_ml_decode(field=field, matrix=matrix,
                                     syndrome=s_e, w=w, max_weight=4)
    if e_hat is None:
        return None
    if not _syndrome_ok(field, matrix, bob, e_hat, s_x):
        return None
    return list(e_hat)


def decode_bp_then_bounded4(*, field: GF2mField, matrix: Any, bob: Sequence[int],
                            s_x: Sequence[int], w: Any,
                            max_iter: int = 60) -> list[int] | None:
    """S2: BP first; fallback to bounded4 only when BP is not syndrome-consistent."""
    bp = decode_bp_only(field=field, matrix=matrix, bob=bob, s_x=s_x,
                        w=w, max_iter=max_iter)
    if bp is not None:
        return bp
    return decode_bounded4_only(field=field, matrix=matrix, bob=bob, s_x=s_x,
                                w=w, max_iter=max_iter)


def run_bob_only_strategy(*, strategy: str, field: GF2mField, matrix: Any,
                          bob: Sequence[int], s_x: Sequence[int], w: Any,
                          max_iter: int = 60) -> list[int] | None:
    """Dispatch to one of S0/S1/S2. Bob-only."""
    if strategy == "S0":
        return decode_bp_only(field=field, matrix=matrix, bob=bob, s_x=s_x,
                              w=w, max_iter=max_iter)
    if strategy == "S1":
        return decode_bounded4_only(field=field, matrix=matrix, bob=bob,
                                    s_x=s_x, w=w, max_iter=max_iter)
    if strategy == "S2":
        return decode_bp_then_bounded4(field=field, matrix=matrix, bob=bob,
                                       s_x=s_x, w=w, max_iter=max_iter)
    raise ValueError(f"unknown strategy: {strategy}")
