"""V80 S2 PEG construction for the GF(32) L2 layer (EXPLORE construction code).

Frozen spec: ``docs/research_cycles/V80-NBLDPC-JAN21/S2_ENTRY_PACKET_20260920.md``
(G-S2ENTRY) + ``S2_ACCOUNTING_MAP_20260920.md`` + ``PROGRAM_PLAN.md`` §1.3/S2.

Scope: S2 construction code + superframe grouping + decoder hook ONLY.
NO FER campaign execution (needs review + Pre-EXECUTE + fresh run — NOT
authorized). Synthetic inputs only; no real-data/Jan-21 frames; no writes to
``results/``, ``outputs_comparison/`` or any ``workspace/`` root (all helpers
are pure in-memory).

Construction family (frozen, packet §1): PEG / improved-PEG + 4-cycle /
short-cycle control only. BAN (frozen): "Three-shift-cyclic GF(32) mothers
FROZEN-excluded for S2" — V29 d_min<=2: 15 support groups / max multiplicity
69 / 303 duplicate projective classes / 922 columns in duplicate classes /
1107 proportional-column pairs. Our constructor never emits that family
(``family="peg-irregular"`` stamped on every output) and
:func:`refuse_three_shift_cyclic` fails closed on any banned provenance.

Degree basis (frozen, no invention):
- L2 layer lambda = ``{2: 1.0}`` (edge perspective): the frozen m2=47
  slot-105 winner profile recorded in ``S1_REPRO_PREEXEC_20260920.md``
  (frozen contract) and pinned in code as
  ``v80_s1_mcde_runner.REPRO_LAMBDA``; rho is the S1-concentrated check
  distribution via ``nonbinary_v26_mcde.make_rho`` (read-only import — the
  exact S1 function), evaluated at the construction rate ``1 - m2/n``.
- L1 fixed lambda = ``{2: 1}`` (``S1_READINESS.md``; runner L1 guard).
- L1 row count m1≈2 rows per 256-frame is an ACCOUNTING basis from
  ``S2_ACCOUNTING_MAP_20260920.md`` (m_total=49), stated explicitly in
  :func:`construction_basis` — the L1 matrix itself is NOT constructed here.
"""
from __future__ import annotations

import math
from numbers import Integral
from typing import Any, Callable, Mapping

import numpy as np

from . import nonbinary_v10_common as common
from . import nonbinary_v10_fftqspa as fftqspa
from . import nonbinary_v10_peg as peg
from . import nonbinary_v26_mcde as _mcde  # noqa: F401 (read-only rho reuse; never edited)
from .nonbinary_field import GF2mField

__all__ = [
    "Q", "N_FRAME", "M2", "M1_BASIS", "M_TOTAL", "GROUP_FRAMES",
    "H_FULL_ANCHOR", "H_L2_ANCHOR", "L2_LAMBDA", "L1_LAMBDA",
    "MAX_ITER", "QBER_SYNTH",
    "FOUR_CYCLE_GATE_THRESHOLD", "FOUR_CYCLE_GATE_STATUS",
    "PER_FRAME_FER_FOR_SUPERFRAME_5PCT",
    "construction_basis",
    "construct_l2",
    "refuse_three_shift_cyclic",
    "count_four_cycles",
    "four_cycle_report",
    "evaluate_superframe",
    "superframe_leakage",
    "qsc_pair_sampler",
    "smoke_decode_frame",
]

#: Frozen L2 layer field (GF(32), width 5 bits/symbol).
Q = 32
#: Frozen frame length (symbols/frame; frame format unchanged).
N_FRAME = 256
#: Frozen L2 check count (DE basis: repro f_layer≈1.1375, G-REPRO PASS).
M2 = 47
#: L1 small-part row basis per 256-frame (ACCOUNTING basis only, per
#: S2_ACCOUNTING_MAP_20260920.md — stated, not constructed here).
M1_BASIS = 2
#: Total rows per 256-frame on the frozen basis (m2 + m1).
M_TOTAL = M2 + M1_BASIS
#: Superframe group size (group rule (a): four independent n=256 codes).
GROUP_FRAMES = 4
#: Frozen whole-frame-with-tag content anchor (bits/symbol).
H_FULL_ANCHOR = 0.83256272
#: L2 layer entropy anchor (2M source; S1 layer-efficiency basis).
H_L2_ANCHOR = 0.80690067
#: Frozen L2 winner profile (edge perspective): m2=47 slot-105 winner
#: (S1_REPRO_PREEXEC frozen contract; v80_s1_mcde_runner.REPRO_LAMBDA).
L2_LAMBDA = {2: 1.0}
#: Frozen L1 profile (fixed; S1_READINESS + runner L1 guard).
L1_LAMBDA = {2: 1.0}
#: Frozen decoder iteration cap (packet §3: log-FFT-SPA, <=300 iter).
MAX_ITER = 300
#: Frozen synthetic channel point (packet §3: V17/V25-class, QBER≈5%).
QBER_SYNTH = 0.05

#: 4-cycle gate threshold: EXPLICIT TBD — S2_ENTRY_PACKET sets no numeric
#: 4-cycle pass threshold (§5 gates are superframe FER + f only). The count
#: is REPORTED ONLY; never invent a pass/fail bar here.
FOUR_CYCLE_GATE_THRESHOLD = None
FOUR_CYCLE_GATE_STATUS = (
    "TBD — packet leaves the 4-cycle gate open; count reported only, "
    "no pass/fail adjudication"
)

#: Group rule (a) arithmetic (packet §2): superframe FER<=5% with
#: any-frame-fail ⇒ group-fail implies per-frame FER <= 1-(1-0.05)^(1/4).
PER_FRAME_FER_FOR_SUPERFRAME_5PCT = 1.0 - (1.0 - 0.05) ** (1.0 / GROUP_FRAMES)

#: Banned construction family token (frozen ban, packet §1).
BANNED_FAMILY = "three-shift-cyclic"


def construction_basis() -> dict[str, Any]:
    """State the frozen S2 construction/accounting basis explicitly.

    L1 (m1≈2, lambda {2:1}) is an accounting basis from
    S2_ACCOUNTING_MAP_20260920.md — stated here, NOT constructed.
    """
    rate_l2 = 1.0 - M2 / N_FRAME
    f_layer = 5 * M2 / (N_FRAME * H_L2_ANCHOR)
    f_super = superframe_leakage(0.0) / (GROUP_FRAMES * N_FRAME * H_FULL_ANCHOR)
    return {
        "field_q": Q,
        "n_frame": N_FRAME,
        "m2": M2,
        "m1_basis": M1_BASIS,
        "m1_basis_source": "S2_ACCOUNTING_MAP_20260920.md (stated, not constructed)",
        "m_total": M_TOTAL,
        "l2_lambda": dict(L2_LAMBDA),
        "l2_lambda_source": "S1_REPRO_PREEXEC_20260920.md frozen contract "
                            "(m2=47 slot-105 winner; runner REPRO_LAMBDA)",
        "l1_lambda": dict(L1_LAMBDA),
        "l1_lambda_source": "S1_READINESS.md (L1 fixed {2:1}; runner L1 guard)",
        "rho": "concentrated via nonbinary_v26_mcde.make_rho (exact S1 function)",
        "rate_l2": rate_l2,
        "f_layer_repro_basis": f_layer,
        "f_super_basis": f_super,
        "family": "peg-irregular",
        "banned_family": BANNED_FAMILY,
    }


def refuse_three_shift_cyclic(provenance: Mapping[str, Any]) -> None:
    """Fail closed on the frozen-banned three-shift-cyclic mother family.

    Raises ``ValueError`` iff ``provenance["family"]`` names the banned
    family (case/space/hyphen-insensitive). Anything else passes silently.
    V29 evidence: d_min<=2 (15 support groups / multiplicity 69 / 303
    duplicate projective classes / 922 columns / 1107 proportional pairs).
    """
    if not isinstance(provenance, Mapping):
        raise ValueError("provenance must be a mapping")
    family = str(provenance.get("family", "")).lower().replace("_", "-").replace(" ", "-")
    while "--" in family:
        family = family.replace("--", "-")
    if family == BANNED_FAMILY:
        raise ValueError(
            "FROZEN-excluded for S2: three-shift-cyclic GF(32) mothers "
            "(V29 d_min<=2; see S2_ENTRY_PACKET_20260920.md §1)")


def construct_l2(seed: int, max_trials: int = 20) -> dict[str, Any]:
    """PEG-construct the frozen L2 layer code (GF(32), n=256, m2=47).

    Placement primitives are the accepted ``nonbinary_v10_peg`` path
    (``peg_construct`` over an injected GF(32) field); rho is the
    S1-concentrated distribution (``make_rho`` at rate ``1-m2/n``).
    Output carries ``family="peg-irregular"`` (ban-guard stamped),
    the 4-cycle report, and the stated (not constructed) L1 basis.
    Pure in-memory; no disk writes.
    """
    if isinstance(seed, bool) or not isinstance(seed, Integral):
        raise ValueError("seed must be an integer")
    if isinstance(max_trials, bool) or not isinstance(max_trials, Integral) \
            or int(max_trials) < 1:
        raise ValueError("max_trials must be a positive integer")
    field = GF2mField.create(Q)
    lam = {int(k): float(v) for k, v in L2_LAMBDA.items()}
    rho = _mcde.make_rho(1.0 - M2 / N_FRAME, lam)
    result = peg.peg_construct(N_FRAME, M2, lam, rho, int(seed),
                               max_trials=int(max_trials), field=field)
    result["family"] = "peg-irregular"
    refuse_three_shift_cyclic({"family": result["family"]})
    result["four_cycles"] = count_four_cycles(result["triples"], N_FRAME, M2)
    result["four_cycle_gate_threshold"] = FOUR_CYCLE_GATE_THRESHOLD
    result["four_cycle_gate_status"] = FOUR_CYCLE_GATE_STATUS
    result["basis"] = construction_basis()
    result["lambda_edge"] = lam
    result["rho_edge"] = {int(k): float(v) for k, v in rho.items()}
    return result


def count_four_cycles(triples: Any, n: int, m: int) -> int:
    """Count 4-cycles in the Tanner graph (exact).

    Triples are ``(row=check, col=variable, coeff)`` (v10 peg convention).
    Each 4-cycle {v1,v2,c1,c2} is counted once: for every check pair
    occurring at ``k`` variables, add C(k,2).
    """
    var_checks: dict[int, list[int]] = {}
    for row, col, _ in triples:
        row, col = int(row), int(col)
        if not 0 <= row < int(m) or not 0 <= col < int(n):
            raise ValueError("sparse triple out of (m, n) bounds")
        var_checks.setdefault(col, []).append(row)
    pair_counts: dict[tuple[int, int], int] = {}
    for checks in var_checks.values():
        ordered = sorted(set(checks))
        for i in range(len(ordered)):
            for j in range(i + 1, len(ordered)):
                key = (ordered[i], ordered[j])
                pair_counts[key] = pair_counts.get(key, 0) + 1
    return sum(k * (k - 1) // 2 for k in pair_counts.values())


def four_cycle_report(construction: Mapping[str, Any]) -> dict[str, Any]:
    """Report-only 4-cycle summary (no pass/fail adjudication — TBD gate)."""
    return {
        "four_cycles": int(construction.get("four_cycles", 0)),
        "gate_threshold": FOUR_CYCLE_GATE_THRESHOLD,
        "gate_status": FOUR_CYCLE_GATE_STATUS,
        "min_girth": construction.get("min_girth"),
    }


def superframe_leakage(d_blind: float) -> float:
    """Frozen superframe leakage (bits): 4·5·m_total + 64 + D_blind.

    ``D_blind`` counts ALL extra disclosed bits beyond scheduled syndrome
    (packet §3); it is INJECTED by the caller and defaults to 0.0 ONLY as a
    placeholder — NEVER assume 0 in a claim (see ``d_blind_label``).
    """
    if isinstance(d_blind, bool) or not isinstance(d_blind, (int, float)) \
            or not math.isfinite(float(d_blind)) or float(d_blind) < 0.0:
        raise ValueError("d_blind must be finite and >= 0")
    return float(GROUP_FRAMES * 5 * M_TOTAL + 64 + float(d_blind))


def evaluate_superframe(frame_ok: Any, d_blind: float = 0.0) -> dict[str, Any]:
    """Whole-group accept/discard for one 4×n=256 superframe (rule (a)).

    ``frame_ok``: exactly 4 per-frame booleans. Group accept iff ALL four
    succeed (any-frame-fail ⇒ group fail). Reports per-frame AND superframe
    FER bookkeeping plus the frozen whole-frame-with-tag f with the injected
    D_blind surcharge. Group rule math: superframe FER<=5% needs per-frame
    FER<=1.274% (``PER_FRAME_FER_FOR_SUPERFRAME_5PCT``) — never reuse the
    single-frame 5% gate for superframes.
    """
    flags = [bool(v) for v in frame_ok]
    if len(flags) != GROUP_FRAMES:
        raise ValueError(f"superframe needs exactly {GROUP_FRAMES} frame outcomes, "
                         f"got {len(flags)}")
    n_ok = sum(flags)
    n_fail = GROUP_FRAMES - n_ok
    leak = superframe_leakage(d_blind)
    content = GROUP_FRAMES * N_FRAME * H_FULL_ANCHOR
    return {
        "n_frames": GROUP_FRAMES,
        "n_ok": n_ok,
        "n_fail": n_fail,
        "per_frame_fer": n_fail / GROUP_FRAMES,
        "group_accept": n_fail == 0,
        "superframe_fail": 1 if n_fail else 0,
        "d_blind": float(d_blind),
        "d_blind_label": ("NEVER-ASSUME-ZERO placeholder: claim runs must "
                          "inject measured D_blind (packet §3)"),
        "leak_bits": leak,
        "f_super": leak / content,
        "per_frame_fer_for_superframe_5pct": PER_FRAME_FER_FOR_SUPERFRAME_5PCT,
    }


def qsc_pair_sampler(rng: np.random.Generator, n: int, q: int = Q,
                     p: float = QBER_SYNTH) -> tuple[np.ndarray, np.ndarray]:
    """Default SYNTHETIC channel sampler hook (QSC, symbol error rate ``p``).

    Stand-in for the packet's "synthetic V17/V25-class, QBER≈5%" point —
    it is NOT the V17/V25 kernel and NOT real data. Returns
    ``(alice, bob)`` uniform-alice symbol vectors with ``bob = alice + e``,
    ``e`` i.i.d. QSC(p) (nonzero uniform over the other q-1 symbols).
    Inject any conforming ``sampler(rng, n) -> (alice, bob)`` callable to
    replace this default.
    """
    if not isinstance(rng, np.random.Generator):
        raise ValueError("rng must be a numpy Generator")
    if isinstance(n, bool) or not isinstance(n, Integral) or int(n) < 1:
        raise ValueError("n must be a positive integer")
    if not 0.0 < float(p) < 1.0:
        raise ValueError("p must be in (0, 1)")
    n = int(n)
    alice = rng.integers(0, int(q), size=n)
    flip = rng.random(n) < float(p)
    nonzero_shift = rng.integers(1, int(q), size=n)
    # NOTE: GF(32) is characteristic 2 (add = XOR on 5-bit symbols), so a
    # uniform nonzero XOR-shift keeps bob in-domain; this sampler is valid
    # ONLY for q a power of 2 (frozen Q=32).
    if int(q) != Q:
        raise ValueError("synthetic hook is pinned to GF(32)")
    bob = np.where(flip, alice ^ nonzero_shift, alice)
    return alice.astype(np.int64), bob.astype(np.int64)


def smoke_decode_frame(construction: Mapping[str, Any], seed: int,
                       sampler: Callable[..., Any] | None = None,
                       max_iter: int = MAX_ITER,
                       qber: float = QBER_SYNTH) -> dict[str, Any]:
    """Single-frame smoke decode: construction + ONE synthetic block.

    Binds the V10 log-FFT-SPA kernel read-only
    (``decode_error_domain``; ``max_iter``<=300 per packet §3) with Alice's
    syndrome and Bob's observation from the injected sampler hook. Returns
    the raw kernel verdict + exact-match flag. A smoke RUN is asserted —
    decode SUCCESS is not (no FER claim at any N).
    """
    if isinstance(seed, bool) or not isinstance(seed, Integral):
        raise ValueError("seed must be an integer")
    if isinstance(max_iter, bool) or not isinstance(max_iter, Integral) \
            or not 1 <= int(max_iter) <= MAX_ITER:
        raise ValueError(f"max_iter must be in 1..{MAX_ITER}")
    field = GF2mField.create(Q)
    dense = peg.sparse_to_dense(construction["triples"], N_FRAME, M2, field)
    rng = np.random.default_rng(common.v10_seed(f"s2_smoke:{int(seed)}"))
    hook = sampler if sampler is not None else qsc_pair_sampler
    alice, bob = hook(rng, N_FRAME)
    alice = np.asarray(alice, dtype=np.int64)
    bob = np.asarray(bob, dtype=np.int64)
    s_x = fftqspa.syndrome_of(field, dense, alice.tolist())
    result = fftqspa.decode_error_domain(bob.tolist(), dense, s_x, float(qber),
                                         field, int(max_iter))
    x_hat = result.get("x_hat")
    return {
        "status": result.get("status"),
        "iterations": result.get("iterations"),
        "reconstruction_ok": bool(result.get("reconstruction_ok")),
        "exact_match": (bool(np.array_equal(np.asarray(x_hat), alice))
                        if x_hat is not None else False),
        "seed": int(seed),
        "max_iter": int(max_iter),
        "qber": float(qber),
        "note": "smoke run only — success/failure carries no FER meaning",
    }
