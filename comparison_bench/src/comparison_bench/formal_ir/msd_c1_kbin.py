"""k-bin generalization for the ``{-k..k}`` -> ``GF(2k+1)`` additive channel.

C-1 implementation batch (OP1), frozen packet
``docs/research_cycles/C-BATCH/C1_PACKET.md`` §3.1.

Scope: pure arithmetic only. ``k`` is the window half-width in bins,
``q = 2k+1`` is the channel modulus (``k = 1, 2, 3`` -> ``q = 3, 5, 7``,
all prime, so ``F_q`` arithmetic is well defined). ``k = 1`` degenerates
to the G-1 ternary error model; the reference numbers quoted below are
copied from the landed ``G1_TERNARY.md`` T2-1M row
(``P0 = 0.76243``, ``P+1 = 0.23619``, ``P-1 = 0.001379``, ``H(e) = 0.8032``)
as pure arithmetic对照 — no raw data is read here.

Error-folding convention (``fold_error``): for a raw integer error ``e``
and difference-domain modulus ``D``, let ``r = e mod D`` in ``[0, D)``.
Values ``r <= k`` map to ``+r``; values ``r >= D - k`` map to ``r - D``
(negative); anything else falls outside ``{-k..k}`` and is reported as
``None`` (rest mass, never silently merged into any bin). When the two
branches overlap (``D <= 2k``) the non-negative branch wins; this tie
only matters for degenerate ``D`` and is documented, not relied upon.

Prior convention (``params_from_stats``): with ``S = {-k..k}``,

    g(0)   = 1 - p - rest
    g(-1)  = p_minus                         # absolute P(e = -1) mass
    g(e)   = (p - p_minus) / (2k - 1)        # every other nonzero e in S
    H_q    = -Σ_{e in S} g(e)·log2 g(e)      # plus -rest·log2(rest) if rest > 0
    ideal_bps = H_q                          # bits per symbol

``p`` is the total in-support error mass ``P(e ≠ 0)``; ``p_minus`` is the
*absolute* mass on ``e = -1`` (the ``PM_ABS``口径 of the C-1 inventory,
``P(e=-1) = 0.001379`` for T2-1M; the conditional fraction is
``p_minus / p``). The remaining ``p - p_minus`` mass is spread uniformly
over the other ``2k - 1`` nonzero bins — symmetric except for the
distinguished ``-1`` sign direction. ``rest`` is out-of-support tail mass
kept as its own explicit outcome (it contributes its own entropy term);
it is never absorbed into ``p`` or spread over bins. For an additive
channel the per-symbol ideal disclosure equals the conditional entropy,
so ``ideal_bps = H_q`` and the ``N``-symbol ideal is ``N·H_q`` (used by
C-3 rate selection).
"""

from __future__ import annotations

import math
import operator

__all__ = ["support_of", "modulus", "fold_error", "params_from_stats"]


def _explicit_integer(value: object, name: str) -> int:
    """Return ``value`` as an int, rejecting bools and non-integers."""
    if isinstance(value, bool):
        raise ValueError(f"{name} must be an integer, not bool")
    try:
        return operator.index(value)
    except TypeError as exc:
        raise ValueError(f"{name} must be an integer") from exc


def _explicit_k(k: object) -> int:
    k = _explicit_integer(k, "k")
    if k < 1:
        raise ValueError("k must be a positive integer")
    return k


def _explicit_probability(value: object, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a real number, not bool")
    try:
        out = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a real number") from exc
    if not math.isfinite(out):
        raise ValueError(f"{name} must be finite")
    return out


def support_of(k: int) -> list[int]:
    """Return the error support ``{-k..k}`` as a list."""
    k = _explicit_k(k)
    return list(range(-k, k + 1))


def modulus(k: int) -> int:
    """Return the channel modulus ``q = 2k+1``."""
    k = _explicit_k(k)
    return 2 * k + 1


def fold_error(e: int, D: int, k: int) -> int | None:
    """Fold a raw integer error ``e`` from a ``mod D`` domain into ``{-k..k}``.

    Returns the folded value, or ``None`` when ``e mod D`` lies outside
    the support (rest mass).
    """
    e = _explicit_integer(e, "e")
    D = _explicit_integer(D, "D")
    k = _explicit_k(k)
    if D < 1:
        raise ValueError("D must be a positive integer")
    r = e % D
    if r <= k:
        return r
    if r >= D - k:
        return r - D
    return None


def params_from_stats(
    *,
    support: object,
    p: float,
    p_minus: float,
    k: int,
    rest: float = 0.0,
) -> tuple[int, float, float]:
    """Build the ``q``-ary additive-channel prior and return ``(q, H_q, ideal_bps)``.

    ``support`` must hold exactly ``{-k..k}`` (order-insensitive); ``p`` is
    the total in-support error mass, ``p_minus`` the absolute ``e = -1``
    mass, ``rest`` the out-of-support tail mass (default 0). See the module
    docstring for the explicit formula. ``H_q`` and ``ideal_bps`` are both
    in bits per symbol.
    """
    k = _explicit_k(k)
    try:
        given = set(support)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("support must be an iterable of integers") from exc
    if given != set(range(-k, k + 1)):
        raise ValueError("support must equal {-k..k}")
    p = _explicit_probability(p, "p")
    p_minus = _explicit_probability(p_minus, "p_minus")
    rest = _explicit_probability(rest, "rest")
    if not 0.0 <= p <= 1.0:
        raise ValueError("p must lie in [0, 1]")
    if not 0.0 <= p_minus <= p:
        raise ValueError("p_minus must lie in [0, p]")
    if not 0.0 <= rest <= 1.0:
        raise ValueError("rest must lie in [0, 1]")
    g0 = 1.0 - p - rest
    if g0 < 0.0:
        raise ValueError("p + rest must not exceed 1")

    q = 2 * k + 1
    # Mass on every nonzero bin except -1, spread uniformly ("对称" part).
    share = (p - p_minus) / (2 * k - 1)
    entropy = 0.0
    if g0 > 0.0:
        entropy -= g0 * math.log2(g0)
    if p_minus > 0.0:
        entropy -= p_minus * math.log2(p_minus)
    if share > 0.0:
        entropy -= (2 * k - 1) * share * math.log2(share)
    if rest > 0.0:
        entropy -= rest * math.log2(rest)
    ideal_bps = entropy
    return (q, entropy, ideal_bps)
