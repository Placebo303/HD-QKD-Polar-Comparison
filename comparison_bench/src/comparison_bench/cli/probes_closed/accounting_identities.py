"""Shape-aware accounting identities for pricing arithmetic (fake-only helper).

Standard library only. No scientific imports, no data contact of any kind:
every check below runs on hand constants supplied by the caller.

Single-block shape (one joint syndrome + one tag: the joint code, the
mainline m-basis): the f-derived ceil IS the tag-inclusive total.
  TOTAL(f, H) = ceil(f * N * H)   # tag-inclusive
  LEAK        = TOTAL - TAG       # tag-exclusive, only where a leak figure
                                  # is genuinely needed
  fit <=> TOTAL <= BUDGET  <=>  LEAK <= (BUDGET - TAG)

Ten-block shape (ten per-plane syndromes + ONE shared tag): each plane
parity is pure parity for that plane; the frame total adds the tag once.
  FRAME_TOTAL = sum(parities) + TAG
"""

from __future__ import annotations

import math


def joint_total(fmult: float, n_sym: int, h: float) -> int:
    """Tag-inclusive single-block total: ceil(f * N * H)."""
    return int(math.ceil(float(fmult) * int(n_sym) * float(h)))


def leak_of(total: int, tag: int) -> int:
    """Tag-exclusive leak form: TOTAL - TAG."""
    return int(total) - int(tag)


def check_c1_total_identity(fmult: float, n_sym: int, h: float,
                            total: int, tag: int, budget: int) -> bool:
    """C-1: TOTAL == ceil(f*N*H), LEAK == TOTAL - TAG, and the two gates agree.

    Returns True iff the total construction is honest: the total equals the
    ceil (no tag added onto it, none omitted), the leak is exactly total
    minus tag, and TOTAL <= budget holds iff LEAK <= budget - tag.
    """
    expect = joint_total(fmult, n_sym, h)
    if int(total) != expect:
        return False
    if leak_of(total, tag) != int(total) - int(tag):
        return False
    fit_total = int(total) <= int(budget)
    fit_leak = leak_of(total, tag) <= int(budget) - int(tag)
    return fit_total == fit_leak


def check_c2_no_double_count(budget_compared: int, fmult: float,
                             n_sym: int, h: float, budget: int) -> bool:
    """C-2 (trap): the budget-compared quantity must equal the bare ceil.

    Returns True iff Q - B == ceil(f*N*H) - B. A stage that forms its
    compared quantity as ceil(f*N*H) + TAG (tag counted twice) supplies
    Q = ceil + TAG and FAILS this check. That is the trap working.
    """
    expect = joint_total(fmult, n_sym, h)
    return (int(budget_compared) - int(budget)) == (expect - int(budget))


def check_c3_frame_shape(plane_parities: list[int], frame_total: int,
                         tag: int) -> bool:
    """C-3: ten-block shape adds the shared tag exactly once.

    Returns True iff FRAME_TOTAL - sum(parities) == TAG exactly. Both a
    tag-omitted total (difference 0) and a tag-doubled total (difference
    2*TAG) trip this check.
    """
    return int(frame_total) - sum(int(m) for m in plane_parities) == int(tag)
