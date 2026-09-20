"""V80 B2G soft-marginal L2 prior FER campaign executor (EXPLORE code — NOT execution).

Frozen contract: ``docs/research_cycles/V80-NBLDPC-JAN21/
B2G_EXPERIMENT_PACKET_20260921.md`` (G-B2G, frozen, NOT granted;
CONTINGENCY RESOLVED 2026-09-21 — ``B2G_BATCH_END_REVIEW_20260921.md``
= PASS) + ``B2G_EXPERIMENT_PROMPT_20260921.md``. Execution needs a fresh
explicit grant + Pre-EXECUTE; this module only provides the executor +
fake-testable mechanics. Synthetic draws from the read-only 2M derived
bundle only; no real/Jan-21 frames; no writes outside the run root;
never writes ``results/`` or ``outputs_comparison/``.

Why this thin NEW module (packet §5/X1): B2G = B2G with EXACTLY ONE
changed scientific input — the construct (PEG) seed **2026092001 (b2f)
→ 2026092011 (b2g)**, the O1R R2 SECOND construction instance of the
same code family (the established two-construction-instance seed series
2026092001 (first instance) → 2026092011 (second instance), already used
and dry-pinned by O1R; no new convention is invented). B2G asks whether
the b2f PASS (F208 0/240, F202 6/240) replicates on a SECOND
construction instance of the same code. The u1 dependence still
disappears from the prior entirely: exact Bayes marginalization of the
frozen bundle — the Bob-side L2 prior becomes π_i(e)=Σ_{u1}
γ1(u1|b_i)·γ2(y_i⊕e | u1, b_i), y_i = b_i&31 — so there is no genie
true-u1, no argmax û1, no L1 code, no estimator, no accounting change
(D-u1 = 0.0 MEASURED label; gates unchanged). This is the d7 ``q @ P``
contraction (``transfer_prior_l1_to_l2`` v72p2d7 L603-610) with q = the
γ1 column, i.e. the same production transfer the d5 ``app_fed_l2_prior``
(v72p2d5 L354-376) uses, evaluated on the frozen empirical bundle.

Semantics (packet §§1–5; identical to b2f/O1R/P0/A208/A202 except the
prior and the ONE construct seed): ONE code n=1024, GF(32), λ={2:1};
acceptance unit = ONE BLOCK = one n=1024 decode with ``exact_match is
True`` (x̂==u2). Two arms only: **F208 PRIMARY** (m=208, the SECOND
construction instance 2026092011 of the A208 code — no L1-row funding
⇒ genie retires with no L1 code at all) and **F202 SECONDARY** (m=202,
the second construction instance 2026092011 of the A202 code — m1=6
accounting room). Both built via ``construct_arm("A208"|"A202",
seed=2026092011, trials=20)`` ⇒ the second construction instance
(recorded as the O1R R2 precedent; NOT byte-identical to the O1/b2f
A208/A202 genie arms — different construct seed; never rebuilt). Pins:
fc==0 AND rank-full AND construct-twice-identical GATED (mismatch →
STOP-BLOCKED pre-decode); girth RECORDED-not-gated (P0/R2-amendment
precedent; O1R measured A208 girth 6 at seed 2026092011 — carried as a
recorded covariate; A202 girth at this seed is MEASURED at the
Pre-EXECUTE dry-construct and recorded, never gated). Per block: triple
draw on the ``o1_blk:{seed}`` stream (frozen sampler, draw order
unchanged; seeds 2026095601+idx, paired with O1R/P0/L1B/b2e/b2f — NO
independence claim); the FROZEN marginal formula (packet §2, never
genie, never argmax); XOR-centered prior into
``decode_error_domain_posterior`` ONLY (the scalar-p
``decode_error_domain`` is NEVER used); max_iter=300/streak 3;
per-decode cap 300 s.

Report-only per block (packet §5/X3): ``prior_entropy_bits`` =
Σ_i H(π_i) (1e-300 floor guard) — the pre-registered observation is
parity with the genie-conditioned prior (chain rule H(U2|B) =
H_full·n − H(U1|B) = 852.544 − 26.278 = 826.266 b vs genie H_L2·n =
1024×0.80690067 = 826.266 b; anchors ``v80_s2_peg`` L77/L79) — and
``u1_mismatches`` (û1 = argmax_u γ1(u|b_i); measurement only, ties to
b2e, NOT a disclosure, NOT a block criterion). Neither column enters
any gate.

Accounting (packet §4, the UNCHANGED O1 basis — no pooling across arms):
gate (b) f_super = (5m+64)/852.544 ≤ 1.3 with D-u1 = 0.0 MEASURED label
(F208 1104/852.544 = 1.294947; F202 1074/852.544 = 1.259759 — both pass
by construction, an accounting identity) and the NEVER-ASSUME-ZERO note
retained. Gate (a): fails/240 ≤ 12 (5% exact), early-stop at the 13th
fail → FAIL, retain partials; gate (a) is the scientific test. No
cross-arm pooling; no cross-instance pooling; no rerun; no tuning.

Reuse from ``v80_o1_campaign``/``v80_s2c_campaign`` (read-only patterns,
never their science): dual-flag gate ``--execute-real
--execution-authorized`` refusing everything else rc=2 pre-anything;
checkpoint manifest+rows overwrite-in-place single writer; append-only
``wall_windows``; explicit ``--resume-from`` with strict pre-decode
validation and ≤1 wall-partial continuation (no auto-relaunch); early-stop
at bar+1 block fails; root policy (fresh additive ``workspace/b2g_<uuid8>``
per arm; ``results/`` + ``outputs_comparison/`` forbidden). Channel
helpers (``bind_empirical_bundle``, ``empirical_triple_sampler``,
``center_rows_prior``) are reused READ-ONLY from ``v80_s2c_campaign`` —
never re-implemented here. The GF(32) field order ``Q`` comes read-only
from the frozen ``v80_s2_peg`` anchor module.

B2G freezes EXACTLY ONE runnable configuration (arms F208/F202 only;
construct seed 2026092011/trials 20 via the A208/A202 second
construction instance; block base 2026095601; 240 blocks), so the CLI
refuses any deviation of ``--construct-seed``/``--construct-trials``/
``--block-base``/``--n-blocks`` from those frozen literals — INCLUDING
2026092001, which is b2f's frozen construct seed, NOT b2g's: any such
change is a science-input change → STOP (packet §6).
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np

from . import nonbinary_v10_fftqspa as fftqspa
from . import nonbinary_v10_peg as peg
from . import nonbinary_v28 as v28
from . import v80_o1_campaign as o1
from . import v80_s2_peg as s2
from . import v80_s2c_campaign as s2c
from .nonbinary_field import GF2mField

__all__ = [
    "B2G_CONSTRUCT_SEED", "B2G_MAX_TRIALS", "B2G_BLOCK_BASE",
    "B2G_N_BLOCKS", "B2G_N", "B2G_ROOT_PREFIX",
    "ARMS", "CAMPAIGN_LABEL", "U1_SOURCE",
    "MAX_ITER", "H_L2_B2G", "H_FULL_B2G", "H_L1_B2G",
    "CONTENT_BITS", "L1_CONTENT_BITS", "GENIE_L2_CONTENT_BITS",
    "D_U1", "F_SUPER_MAX",
    "WALL_CAP_S", "PER_DECODE_CAP_S", "RSS_CAP_GIB",
    "ROOT_PREFIX", "FORBIDDEN_ROOT_PARTS",
    "GAMMA_DEFAULT", "SOURCE_DEFAULT", "DE_LABELS",
    "Refusal", "refuse", "block_seed", "stream_seed", "fail_bar",
    "construct_arm", "marginal_prior_l2", "map_u1", "u1_mismatches",
    "prior_entropy_bits",
    "f_super_du0", "leak_basis", "decode_block_marginal",
    "quarter_tally", "prior_entropy_stats", "mismatch_stats",
    "block_accounting_csv",
    "run_execution", "execute", "main",
]

#: Frozen B2G construction seed (packet §3; both arms): 2026092011 =
#: the O1R R2 SECOND construction instance (series 2026092001 →
#: 2026092011). LITERAL — deliberately NOT ``o1.O1_CONSTRUCT_SEED``
#: (2026092001 is b2f's frozen value, not b2g's).
B2G_CONSTRUCT_SEED = 2026092011
#: Frozen constructor trials (packet §3; both arms).
B2G_MAX_TRIALS = o1.O1_MAX_TRIALS
#: Frozen code length (packet §3): n=1024 GF(32) symbols/block.
B2G_N = o1.O1_N
#: Frozen literal block-seed base (packet §4; LITERAL, paired reuse with
#: O1R/P0/L1B/b2e/b2f — SAME 240 frames; NO independence claim).
B2G_BLOCK_BASE = 2026095601
#: Frozen campaign width (packet §4): 240 blocks = 240 decodes/arm.
B2G_N_BLOCKS = 240
#: Fresh additive B2G run-root prefix (packet §6: workspace/b2g_<uuid8>).
B2G_ROOT_PREFIX = "workspace/b2g_"
ROOT_PREFIX = B2G_ROOT_PREFIX
#: Roots the executor never writes under.
FORBIDDEN_ROOT_PARTS = ("results", "outputs_comparison")
#: Frozen decoder cap (packet §2): max_iter=300, streak default (3).
MAX_ITER = o1.MAX_ITER
#: Frozen caps (packet §6): single window 3600 s; per-decode 300 s; 4 GiB.
WALL_CAP_S = o1.WALL_CAP_S
PER_DECODE_CAP_S = o1.PER_DECODE_CAP_S
RSS_CAP_GIB = o1.RSS_CAP_GIB
#: Frozen entropy anchors (S2/P0 basis; imported read-only from the
#: frozen O1 module, X1): H_full=0.83256272, H_L2=0.80690067.
H_FULL_B2G = o1.H_FULL_O1
H_L2_B2G = o1.H_L2_O1
#: Frozen L1 entropy anchor H_L1=0.02566205 (v3 memo §2.1) — only quoted
#: for the chain-rule arithmetic of the pre-registered observation.
H_L1_B2G = 0.02566205
#: Content basis: 1024 * H_full = 852.544 bits (packet §4).
CONTENT_BITS = B2G_N * H_FULL_B2G
#: L1 content: 1024 * H_L1 ≈ 26.278 bits (chain-rule subtraction).
L1_CONTENT_BITS = B2G_N * H_L1_B2G
#: Genie-conditioned L2 content: 1024 * H_L2 = 826.266 bits (parity
#: reference for the report-only prior-entropy observation).
GENIE_L2_CONTENT_BITS = B2G_N * H_L2_B2G
#: D-u1 = 0 MEASURED label: Bob's prior is computed from b ALONE (the
#: u1 sum is internal to the Bayes marginalization) ⇒ no u1 disclosure.
#: NEVER-ASSUME-ZERO note retained on every record (packet §4/X6).
D_U1 = 0.0
#: Frozen f_super bar (packet §4; UNCHANGED O1 basis).
F_SUPER_MAX = 1.3
#: u1 source label for this campaign (packet §5/X5).
U1_SOURCE = "MARGINAL"
#: Campaign label (packet §6/X7).
CAMPAIGN_LABEL = "B2G-soft-marginal-replication"
#: Read-only derived bundle (packet §2): gamma file + p_b sidecar sibling
#: (same files as S2c/O1; binding helper reused read-only from s2c).
GAMMA_DEFAULT = s2c.GAMMA_DEFAULT
#: Worst-source anchor (packet §2); never auto-merge sources.
SOURCE_DEFAULT = s2c.SOURCE_DEFAULT
#: Allowed DE-cover labels threading into the campaign manifest (packet
#: §6/X7: F208 'covered' carried from the A208-DE precheck; F202
#: 'exploratory' P0 precedent — NO new DE run in B2G).
DE_LABELS = ("covered", "exploratory")
#: Frozen arms table (packet §3; EXACTLY two — no more, no substitutions).
#: ``source_arm`` names the A208/A202 code built by the frozen O1
#: constructor at the B2G construct seed 2026092011 (the SECOND
#: construction instance; NOT byte-identical to the O1/b2f genie arms —
#: different construct seed); every other m is OUT OF SCOPE (not frozen,
#: not runnable).
ARMS: dict[str, dict[str, Any]] = {
    "F208": {"m": 208, "source_arm": "A208", "lambda": {2: 1.0},
             "rate": 1.0 - 208 / 1024, "leak_bits": 208 * 5 + 64,
             "role": "PRIMARY (m=208; second construction instance "
                     "2026092011 of the A208 code; m2=208 leaves NO "
                     "L1-row funding ⇒ genie retires with no L1 code "
                     "at all)"},
    "F202": {"m": 202, "source_arm": "A202", "lambda": {2: 1.0},
             "rate": 1.0 - 202 / 1024, "leak_bits": 202 * 5 + 64,
             "role": "SECONDARY (m=202; second construction instance "
                     "2026092011 of the A202 code; m2=202 = m1=6 "
                     "accounting room)"},
}


class Refusal(SystemExit):
    """rc=2 pre-write refusal (unauthorized / invalid / gate-blocked)."""


def refuse(reason: str) -> "Any":
    print(f"B2G-REFUSAL rc=2: {reason}", file=sys.stderr)
    raise Refusal(2)


def block_seed(arm: str, idx: int, base: int | None = None) -> int:
    """Frozen literal block seed: base+idx (packet §4).

    Default base is the frozen B2G literal 2026095601, idx=0..239
    (paired reuse with O1R/P0/L1B/b2e; NO independence claim). Unknown
    arm refuses (fail closed, rc=2).
    """
    if arm not in ARMS:
        refuse(f"unknown arm {arm} (frozen: F208|F202 only)")
    b = B2G_BLOCK_BASE if base is None else base
    if isinstance(b, bool) or not isinstance(b, int):
        refuse("block base must be an integer literal")
    return int(b) + int(idx)


def fail_bar(n_blocks: int) -> int:
    """Derived pass bar: floor(n_blocks x 0.05) (O1R packet §5/D2).

    240 -> 12. Early-stop fires at bar+1 (= 13th) cumulative fail.
    Reused READ-ONLY from the frozen O1 module (X1).
    """
    return o1.fail_bar(int(n_blocks))


def stream_seed(seed: int) -> int:
    """Frozen stream derivation: ``common.v10_seed(f"o1_blk:{seed}")``.

    SAME ``o1_blk:`` domain as O1R/P0/L1B/b2e (paired reuse;
    byte-identical triple path ⇒ (b,u1,u2) marginal identical). Reused
    READ-ONLY from the frozen O1 module (X1).
    """
    return o1.stream_seed(int(seed))


def construct_arm(arm: str, seed: int = B2G_CONSTRUCT_SEED,
                  max_trials: int = B2G_MAX_TRIALS) -> dict[str, Any]:
    """B2G arm constructor (packet §3/X2): delegate to the FROZEN O1
    constructor on the A208/A202 code — F208 → ``A208``, F202 → ``A202``
    — with the B2G (n, m, λ, seed=2026092011, trials) ⇒ the SECOND
    construction instance 2026092011 (O1R R2 precedent; recorded; NOT
    byte-identical to the O1/b2f A208/A202 genie arms — different
    construct seed; never rebuilt). No re-seed; no tuning. Pure
    in-memory; no disk writes.
    """
    if arm not in ARMS:
        refuse(f"unknown arm {arm} (frozen: F208|F202 only)")
    if isinstance(seed, bool) or not isinstance(seed, int):
        refuse("construct seed must be an integer")
    if isinstance(max_trials, bool) or not isinstance(max_trials, int) \
            or max_trials < 1:
        refuse("construct trials must be a positive int")
    code = o1.construct_arm(ARMS[arm]["source_arm"], int(seed),
                            int(max_trials))
    code["source_arm"] = ARMS[arm]["source_arm"]
    return code


def _renormalize_marginal_rows(marg: Any) -> np.ndarray:
    """Per-row renormalize with the frozen row-sum guard (packet §2).

    ``decode_fftqspa`` ``_content_valid`` (fftqspa L145-158) requires
    each prior row finite, non-negative and positive-sum, while bind
    tolerates 1e-9+1e-9 accumulation ⇒ each marginal row is divided by
    its row sum. A non-finite/non-positive row sum falls back to
    delta-at-0 (``posterior_rows_l2`` zero-mass semantics, s2c L288-316).
    The d7 uniform-1/32 fallback is NOT adopted because bind already
    enforces cond-rowsum=1. No extra floor: the kernel floors internally
    at 1e-15 (fftqspa L355), matching the O1/B2E prior wiring.
    """
    arr = np.asarray(marg, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[1] != 32:
        refuse("marginal rows need shape (n, 32)")
    out = np.empty_like(arr)
    finite = np.all(np.isfinite(arr), axis=1)
    s = arr.sum(axis=1)
    ok = finite & np.isfinite(s) & (s > 0.0)
    out[ok] = arr[ok] / s[ok][:, None]
    if not np.all(ok):
        z = np.zeros(32, dtype=np.float64)
        z[0] = 1.0
        out[~ok] = z
    return out


def marginal_prior_l2(bundle: dict[str, Any], b_vec: Any) -> np.ndarray:
    """EXACT Bayes-marginal L2 prior rows (packet §2, the FROZEN formula).

    ``g1c = g1[:, b]`` → (32,n) γ1(u1|b_i); ``cond = g2[:, :,
    b].transpose(2,0,1)`` → (n,32,32) with cond[i,u1,u2]=γ2(u2|b_i,u1);
    ``marg = np.einsum("nu,nuv->nv", g1c.T, cond)`` ⇒
    marg[i,v] = Σ_{u1} γ1(u1|b_i)·γ2(v|b_i,u1) — the d7 ``q @ P``
    contraction with q = the γ1 column (v72p2d7 L603-610), the same
    production transfer as d5 ``app_fed_l2_prior`` (v72p2d5 L354-376),
    evaluated on the frozen empirical bundle. NO genie true-u1, NO
    argmax û1, NO L1 code, NO refit. Rows are renormalized under the
    frozen row-sum guard (non-finite/non-positive row sum → delta-at-0).
    Returns (n,32) marg = P(U2|b_i).
    """
    g1 = np.asarray(bundle["g1"], dtype=np.float64)
    g2 = np.asarray(bundle["g2"], dtype=np.float64)
    b = np.asarray(b_vec, dtype=np.int64)
    if b.ndim != 1:
        refuse("marginal prior needs 1-D b")
    if g1.shape != (32, 1024):
        refuse(f"marginal prior g1 shape {g1.shape} != (32, 1024)")
    if g2.shape != (32, 32, 1024):
        refuse(f"marginal prior g2 shape {g2.shape} != (32, 32, 1024)")
    for bb in b.tolist():
        if not 0 <= int(bb) < 1024:
            refuse("marginal prior b symbol out of domain")
    g1c = g1[:, b]                        # (32, n)
    cond = g2[:, :, b].transpose(2, 0, 1)  # (n, 32, 32)
    marg = np.einsum("nu,nuv->nv", g1c.T, cond)  # (n, 32)
    return _renormalize_marginal_rows(marg)


def map_u1(bundle: dict[str, Any], b_vec: Any) -> np.ndarray:
    """û1_i = argmax_u g1[u, b_i] (packet §5/X3): REPORT-ONLY measurement
    tied to b2e — the estimate NEVER enters the marginal prior, is NOT a
    disclosure and is NOT a block criterion. Returns an int64 vector.
    """
    g1 = np.asarray(bundle["g1"], dtype=np.float64)
    b = np.asarray(b_vec, dtype=np.int64)
    if b.ndim != 1:
        refuse("u1 measurement needs 1-D b")
    if g1.shape != (32, 1024):
        refuse(f"u1 measurement g1 shape {g1.shape} != (32, 1024)")
    for bb in b.tolist():
        if not 0 <= int(bb) < 1024:
            refuse("u1 measurement b symbol out of domain")
    return np.argmax(g1[:, b], axis=0).astype(np.int64)


def u1_mismatches(u1_true: Any, u1_hat: Any) -> int:
    """k = Σ_i 1[û1_i ≠ u1_i] (packet §5/X3): MEASURED from the same
    draw. Measurement only, labeled not-a-disclosure (true u1 is known
    in the synthetic draw; it never enters the decode).
    """
    a = np.asarray(u1_true, dtype=np.int64)
    h = np.asarray(u1_hat, dtype=np.int64)
    if a.shape != h.shape or a.ndim != 1:
        refuse("mismatch count needs same-shape 1-D (u1_true, u1_hat)")
    return int(np.count_nonzero(a != h))


def prior_entropy_bits(prior: Any) -> float:
    """Σ_i H(π_i) bits (packet §5/X3): per-block entropy of the
    XOR-centered marginal prior actually fed to the decoder, with the
    zero-mass guard (0·log2 0 := 0 via the 1e-300 floor, same guard as
    the b2e ``d_u1_bits`` column). Report-only: never gated, never a
    block criterion.
    """
    p = np.asarray(prior, dtype=np.float64)
    if p.ndim != 2 or p.shape[1] != 32:
        refuse("prior entropy needs (n, 32) prior rows")
    h = -np.sum(p * np.log2(np.maximum(p, 1e-300)), axis=0)
    return float(h.sum())


def f_super_du0(arm: str) -> float:
    """Gate (b) basis (packet §4; UNCHANGED O1 basis, D-u1 = 0.0
    MEASURED label): f_super = (m·5+64)/852.544 — F208 1.294947,
    F202 1.259759 (both pass by construction; accounting identity)."""
    if arm not in ARMS:
        refuse(f"unknown arm {arm} (frozen: F208|F202 only)")
    return float(ARMS[arm]["leak_bits"]) / CONTENT_BITS


def leak_basis(arm: str) -> dict[str, Any]:
    """Frozen B2G accounting (packet §4; the UNCHANGED O1 basis).

    GATING: f_super = (m·5+64)/852.544 ≤ 1.3 with D-u1 = 0.0 MEASURED
    label (Bob's prior is computed from b alone ⇒ no u1 disclosure;
    NEVER assume zero in a claim). Report-only: the per-block
    ``prior_entropy_bits`` distribution (parity observation vs the
    genie H_L2·n = 826.266 b anchor) and the ``u1_mismatches``
    distribution (b2e-tied measurement, not a disclosure, not a
    criterion). No pooling across arms.
    """
    if arm not in ARMS:
        refuse(f"unknown arm {arm} (frozen: F208|F202 only)")
    m = int(ARMS[arm]["m"])
    leak = float(ARMS[arm]["leak_bits"])
    f = leak / CONTENT_BITS
    headroom = F_SUPER_MAX * CONTENT_BITS - leak
    return {
        "arm": arm,
        "m": m,
        "leak_bits": leak,
        "content_bits": CONTENT_BITS,
        "f_super_basis": f,
        "f_super_label": ("UNCHANGED O1 basis, D-u1 = 0.0 MEASURED "
                          "label (A208/A202-comparable line): "
                          f"f_super=(m·5+64)/852.544=({m}·5+64)/852.544"
                          f"≈{f:.6f} (H_full=0.83256272). PASS by "
                          f"construction (accounting identity); "
                          f"NEVER assume zero in a claim (B2G packet §4)"),
        "f_super_rule": ("GATING (packet §4): f_super=(5m+64)/852.544 "
                         "<=1.3 on the UNCHANGED O1 basis (D-u1 = 0.0 "
                         "MEASURED label — Bob's prior is computed from "
                         "b alone, the u1 sum is internal to the Bayes "
                         "marginalization). Gate (a) is the scientific "
                         "test; no cross-arm pooling."),
        "d_u1": D_U1,
        "d_u1_label": ("D-u1 = 0.0 MEASURED label: no u1 disclosure — "
                       "the marginal prior π_i(e)=Σ_u1 γ1(u1|b_i)·"
                       "γ2(y_i⊕e|u1,b_i) is a function of b ALONE. "
                       "NEVER-ASSUME-ZERO note retained (B2G packet "
                       "§4/X6)"),
        "h_l2": H_L2_B2G,
        "h_l1": H_L1_B2G,
        "h_full": H_FULL_B2G,
        "l1_content_bits": L1_CONTENT_BITS,
        "genie_l2_content_bits": GENIE_L2_CONTENT_BITS,
        "prior_entropy_anchor_bits": GENIE_L2_CONTENT_BITS,
        "prior_entropy_note": ("Report-only observation (packet §1, NOT a "
                               "claim). Measured arithmetic from the frozen "
                               "anchors (dry 1-block probe 2026-09-21): the "
                               "Bayes-marginal prior row IS P(U2|b_i), so "
                               "Σ_i H(π_i) → H(U2|B)·n ≈ H_full·n = "
                               "852.544 b/block (dry measured 853.021 b on "
                               "block 0), whereas the genie-conditioned row "
                               "γ2(·|b_i,u1_i) has Σ_i H → H(U2|U1,B)·n ≈ "
                               "H_L2·n = 826.266 b/block (dry measured "
                               "832.604 b on block 0). The packet §1 parity "
                               "line (chain rule H_full·n − H(U1|B) = "
                               "852.544 − 26.278 = 826.266 b) computes "
                               "H(U2|U1,B)·n, i.e. the GENIE row entropy, "
                               "not the marginalized H(U2|B)·n: Bayes "
                               "marginalization over u1 can only FLATTEN "
                               "the prior (mixing penalty ≈ H(U1|B)·n = "
                               "26.278 b). The packet §1 parity line is "
                               "retained verbatim as the pre-registered "
                               "observation; the column is REPORT-ONLY and "
                               "never gated, and entropy parity is NOT a "
                               "decodability proof (a flatter prior is a "
                               "weaker prior ⇒ BP convergence remains the "
                               "open risk, b2e: 300-iter non-convergence "
                               "under MAP conditioning)"),
        "sensitivity": ("Δf_super = D/852.544, i.e. each 8.52544 bits of "
                        "D ≈ +0.01"),
        "headroom_bits": headroom,
        "headroom_line": (f"Gate (b) headroom {headroom:.2f} b on the "
                          f"unchanged O1 basis: any u1 disclosure D > "
                          f"{headroom:.2f} b would fail gate (b) "
                          f"({arm}; D-u1 = 0.0 MEASURED label)"),
    }


def decode_block_marginal(construction: dict[str, Any], seed: int,
                          bundle: dict[str, Any], n: int,
                          m: int) -> dict[str, Any]:
    """One soft-marginal empirical-channel block (packet §2/X2): triple
    draw on the ``o1_blk:{seed}`` stream (frozen sampler, draw order
    UNCHANGED); Alice x=u2; Bob y=b&31; the FROZEN marginal formula
    (``marginal_prior_l2`` — exact Bayes marginalization, NOT genie,
    NOT argmax); XOR-centered prior into
    ``decode_error_domain_posterior`` (NEVER the scalar-p
    ``decode_error_domain``); max_iter=300, streak default (3).
    Returns the raw kernel verdict + exact-match flag
    (``exact_match is True`` gates block acceptance), the MEASURED
    report-only prior-entropy sum and u1 mismatch count. Fail-closed
    wiring guard: (n, m) must match the construction under test.
    """
    if isinstance(seed, bool) or not isinstance(seed, int):
        refuse("block seed must be an integer")
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        refuse("block n must be a positive int")
    if isinstance(m, bool) or not isinstance(m, int) or m < 1:
        refuse("block m must be a positive int")
    if construction.get("n") != int(n) or construction.get("m") != int(m):
        refuse(f"construction (n, m) mismatch: got "
               f"({construction.get('n')}, {construction.get('m')}) "
               f"for block ({int(n)}, {int(m)})")
    field = GF2mField.create(s2.Q)
    dense = peg.sparse_to_dense(construction["triples"], int(n), int(m),
                                field)
    rng = np.random.default_rng(stream_seed(int(seed)))
    b, u1, u2 = s2c.empirical_triple_sampler(bundle, int(n), rng)
    x = np.asarray(u2, dtype=np.int64)  # Alice vector (syndrome source)
    y = np.asarray(b & 31, dtype=np.int64)  # Bob L2 half (F03 bits 4..0)
    u1_hat = map_u1(bundle, b)  # REPORT-ONLY measurement (never used)
    k = u1_mismatches(u1, u1_hat)  # MEASURED (not a disclosure)
    marg = marginal_prior_l2(bundle, b)  # FROZEN marginal formula
    prior = s2c.center_rows_prior(marg, y)
    h_prior = prior_entropy_bits(prior)  # MEASURED report-only
    s_x = fftqspa.syndrome_of(field, dense, x.tolist())
    result = v28.decode_error_domain_posterior(field, y.tolist(), dense,
                                               s_x, prior, MAX_ITER)
    x_hat = result.get("x_hat")
    return {
        "status": result.get("status"),
        "iterations": result.get("iterations"),
        "reconstruction_ok": bool(result.get("reconstruction_ok", False)),
        "exact_match": (bool(np.array_equal(np.asarray(x_hat), x))
                        if x_hat is not None else False),
        "seed": int(seed),
        "max_iter": int(MAX_ITER),
        "u1_source": U1_SOURCE,
        "prior_entropy_bits": float(h_prior),
        "u1_mismatches": int(k),
        "l1_conditioning": ("EXACT Bayes marginalization π_i(e)=Σ_u1 "
                            "γ1(u1|b_i)·γ2(y_i⊕e|u1,b_i) from the frozen "
                            "bundle (marginal_prior_l2; no genie true-u1, "
                            "no argmax û1, no L1 code, no refit). Genie "
                            "ceiling REMOVED for this arm (no D1 ceiling "
                            "label)"),
    }


def quarter_tally(rows: list[dict]) -> dict[str, Any]:
    """Per-60 quarter fail tally, REPORT-ONLY (O1R packet §2).

    Derived from rows (no new decode path): quarter q covers blocks
    [60q, 60q+59]. ``quarters_le3`` counts COMPLETE (60-block) quarters
    with <=3 fails (O1-bar reference); never gated.
    """
    qs: dict[int, dict[str, int]] = {}
    for r in rows:
        b = r.get("block")
        if isinstance(b, bool) or not isinstance(b, int):
            continue
        q = int(b) // 60
        cell = qs.setdefault(q, {"blocks": 0, "fails": 0})
        cell["blocks"] += 1
        cell["fails"] += int(bool(r.get("block_fail")))
    out: dict[str, Any] = {}
    for q in sorted(qs):
        out[f"idx_{q * 60}_{q * 60 + 59}"] = qs[q]
    complete = [v for v in qs.values() if v["blocks"] == 60]
    out["quarters_complete"] = len(complete)
    out["quarters_le3"] = sum(1 for v in complete if v["fails"] <= 3)
    return out


def prior_entropy_stats(rows: list[dict]) -> dict[str, Any]:
    """Per-block prior-entropy distribution (packet §5/X3; REPORTED).

    Linear-interpolation percentiles over the completed blocks'
    ``prior_entropy_bits`` values (error/overrun rows carry no
    measurement). Report-only: never gated.
    """
    vals = [float(r["prior_entropy_bits"]) for r in rows
            if isinstance(r, dict)
            and r.get("status") not in ("error", "overrun")
            and isinstance(r.get("prior_entropy_bits"),
                          (int, float, np.floating))
            and not isinstance(r.get("prior_entropy_bits"), bool)]
    if not vals:
        return {"blocks": 0, "mean_bits": 0.0, "p50": None, "p90": None,
                "p99": None, "max": None, "min": None}
    a = np.asarray(vals, dtype=np.float64)
    return {"blocks": int(a.size), "mean_bits": float(a.mean()),
            "p50": float(np.percentile(a, 50)),
            "p90": float(np.percentile(a, 90)),
            "p99": float(np.percentile(a, 99)),
            "max": float(a.max()), "min": float(a.min())}


def mismatch_stats(rows: list[dict]) -> dict[str, Any]:
    """Per-block u1-mismatch distribution (measurement-only label)."""
    vals = [int(r["u1_mismatches"]) for r in rows
            if isinstance(r, dict)
            and r.get("status") not in ("error", "overrun")
            and isinstance(r.get("u1_mismatches"), (int, np.integer))
            and not isinstance(r.get("u1_mismatches"), bool)]
    if not vals:
        return {"blocks": 0, "mean": 0.0, "max": None}
    a = np.asarray(vals, dtype=np.int64)
    return {"blocks": int(a.size), "mean": float(a.mean()),
            "max": int(a.max())}


def block_accounting_csv(rows: list[dict]) -> str:
    """Per-block accounting table (packet §8 deliverable; X5 columns:
    u1_source=MARGINAL, prior_entropy_bits, u1_mismatches (report-only),
    f_super (unchanged O1 basis), d_u1=0.0 measured label)."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["block", "seed", "exact_match", "status", "iterations",
                "wall_s", "u1_source", "prior_entropy_bits",
                "u1_mismatches", "d_u1", "leak_bits", "f_super"])
    for r in rows:
        if r.get("status") in ("error", "overrun"):
            w.writerow([r.get("block"), "", "", r.get("status"), "",
                        "", "", "", "", "", "", ""])
            continue
        w.writerow([r.get("block"), r.get("seed"), r.get("exact_match"),
                    r.get("status"), r.get("iterations"), r.get("wall_s"),
                    r.get("u1_source"), r.get("prior_entropy_bits"),
                    r.get("u1_mismatches"), r.get("d_u1"),
                    r.get("leak_bits"), r.get("f_super")])
    return buf.getvalue()


def default_writer(root: str, files: dict[str, str]) -> None:
    """Single-writer overwrite-in-place (research code; root policy is
    enforced in ``execute`` — fail closed before the first write)."""
    os.makedirs(root, exist_ok=True)
    for name, blob in files.items():
        with open(os.path.join(root, name), "w") as fh:
            fh.write(blob)


def _default_rss() -> int:
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    except Exception:  # noqa: BLE001 — RSS probe is best-effort only
        return 0


def _allows_root(root: str) -> bool:
    """Fresh additive prefix: B2G ``workspace/b2g_<uuid>`` (packet §6)."""
    return root.startswith(ROOT_PREFIX)


def _check_root(root: str) -> None:
    if not root:
        refuse("root required (fresh additive workspace/b2g_<uuid>)")
    parts = Path(root).parts
    if any(p in FORBIDDEN_ROOT_PARTS for p in parts):
        refuse(f"root under forbidden tree (results/outputs_comparison): {root}")


def _de_cover_record(arm: str, de_label: str | None) -> dict[str, Any]:
    """DE-cover label threading (packet §6/X7): F208 defaults 'covered'
    (carried from the A208-DE precheck, O1 packet §3); F202 defaults
    'exploratory' (P0 precedent). NO new DE run in B2G; gates unchanged.
    """
    if arm not in ARMS:
        refuse(f"unknown arm {arm} (frozen: F208|F202 only)")
    default = "covered" if arm == "F208" else "exploratory"
    label = de_label or default
    if label not in DE_LABELS:
        refuse(f"unknown de-label {label} (frozen: covered|exploratory only)")
    note = ("F208 carries the A208-DE precheck outcome (O1 packet §3: "
            "A208 rho differs {9:0.141,10:0.859}); the label is CARRIED, "
            "B2G runs NO new DE — gates unchanged."
            if arm == "F208" else
            "F202 follows the P0 precedent: rate 0.802734375 has no S1 "
            "cover and B2G runs NO new DE — default 'exploratory'; gates "
            "unchanged.")
    return {"label": label,
            "label_source": ("explicit --de-label" if de_label
                             else (f"default '{default}' carried (no new "
                                   f"DE run in B2G; packet §6/X7)")),
            "arm_note": note}


def _build_manifest(*, arm: str, construction: dict, rows: list[dict],
                    failures: int, blocks_completed: int, verdict: str,
                    partial: bool, next_block: int,
                    wall_windows: list[dict], ledger_decodes: int,
                    elapsed_s: float, de_label: str | None,
                    block_base: int | None = None,
                    n_blocks: int | None = None) -> dict:
    basis = leak_basis(arm)
    spec = ARMS[arm]
    n = len(rows)
    fer = (failures / n) if n else None
    bb = B2G_BLOCK_BASE if block_base is None else int(block_base)
    nb = B2G_N_BLOCKS if n_blocks is None else int(n_blocks)
    bar = fail_bar(nb)
    pe = prior_entropy_stats(rows)
    km = mismatch_stats(rows)
    return {
        "arm": arm,
        "arm_role": spec["role"],
        "campaign": CAMPAIGN_LABEL,
        "u1_source": U1_SOURCE,
        "construction_instance": {
            "source_arm": spec["source_arm"],
            "note": (f"F{spec['m']} is built via the frozen "
                     f"construct_arm(\"{spec['source_arm']}\", seed "
                     f"{construction.get('construct_seed')}, trials "
                     f"{construction.get('construct_trials')}) — the "
                     f"second construction instance "
                     f"{construction.get('construct_seed')} (O1R R2 "
                     f"precedent) of the {spec['source_arm']} code. NOT "
                     f"byte-identical to the O1/b2f A208/A202 genie arms "
                     f"(different construct seed); recorded as a second "
                     f"construction instance, never rebuilt"),
        },
        "n_blocks": nb,
        "fail_bar": bar,
        "single_code": ("acceptance unit = ONE BLOCK = one n=1024 decode "
                        "with exact_match is True. No frames, no "
                        "group-of-4 rule (B2G packet §1; block≠S2c-group, "
                        "not directly comparable to S2c group FER)"),
        "construct": {
            "seed": construction.get("construct_seed"),
            "max_trials": construction.get("construct_trials"),
            "n": construction.get("n"),
            "m": construction.get("m"),
            "source_arm": construction.get("source_arm"),
            "lambda": {str(k): float(v)
                       for k, v in spec["lambda"].items()},
            "four_cycles": construction.get("four_cycles"),
            "min_girth": construction.get("min_girth"),
            "rank": construction.get("rank"),
            "family": construction.get("family"),
            "pins": (f"fc=0/rank-full/twice-identical GATED; girth-"
                     f"measured-{construction.get('min_girth')}-recorded-"
                     f"not-gated ({arm}; constructor seed "
                     f"{construction.get('construct_seed')}/trials "
                     f"{construction.get('construct_trials')} — the SECOND "
                     f"construction instance of the "
                     f"{spec['source_arm']} code; P0/R2-amendment "
                     f"precedent; construct-twice-identical required; "
                     f"mismatch on gated fields halts STOP-BLOCKED)"),
            "sockets_parity": {"sockets": construction.get("total_sockets"),
                               "parity": construction.get("parallel_edges")},
        },
        "seeds": {
            "policy": "literal-frozen (B2G packet §4; NOT derived)",
            "block_base": bb,
            "block_rule": f"base+idx, idx=0..{nb - 1} (block k → idx=k)",
            "n_blocks": nb,
            "fail_bar": bar,
            "stream": "common.v10_seed(f\"o1_blk:{seed}\") (paired across "
                      "arms; distinct domain from S2c s2c_emp:)",
            "paired_note": ("Blocks REUSED paired with O1R/P0/L1B/b2e/b2f: "
                            "literal 2026095601+idx idx=0..239, stream "
                            "o1_blk:{seed} — SAME 240 frames (byte-identical "
                            "triple path ⇒ (b,u1,u2) marginal identical; "
                            "paired soft-marginal-vs-genie contrast on the "
                            "same frames); prior use declared "
                            "(O1R/P0/L1B/b2e/b2f roots+docs = expected "
                            "hits); NO independence claim "
                            "B2G↔O1R↔P0↔L1B↔b2e↔b2f "
                            "(B2G packet §4)"),
        },
        "channel": {
            "source": SOURCE_DEFAULT,
            "bundle": "gamma_f03.npz keys 2M_gamma1_L1 (32,1024) + "
                      "2M_gamma2_L2condU1 (32,32,1024) + sidecar "
                      "gamma_f03_pb.npz key 2M_p_b (1024,) normalized "
                      "sum=1±1e-9 else refuse (read-only, never refit)",
            "sampler": ("per-symbol triple b~p_b; u1~g1[:,b]; u2~g2[u1,:,b]; "
                        "zero-mass→delta-at-0; frozen make_centered_sampler "
                        "L2 order; i.i.d. ×1024/block; Alice x=u2, "
                        "Bob 10-bit b"),
        },
        "budgets": {"wall_cap_s": WALL_CAP_S,
                    "per_decode_cap_s": PER_DECODE_CAP_S,
                    "rss_gib": RSS_CAP_GIB,
                    "max_blocks": nb, "max_decodes": nb},
        "decoder": {
            "entrypoint": ("decode_error_domain_posterior (nonbinary_v28 "
                           "L155-186; takes (n,q) prior; s_e=s_x+H*y; "
                           "x_hat=y+e_hat). Frozen decode_error_domain "
                           "(v10 L491-518, scalar p ONLY) NEVER used here."),
            "kernel": "log-FFT-SPA with per-variable P(E_i) prior",
            "max_iter": MAX_ITER, "streak": "default (3)",
            "wiring": ("y_i=b_i&31 (factor_layers v29 L269-273); "
                       "marg_i(v)=Σ_u1 γ1(u1|b_i)·γ2(v|b_i,u1) via "
                       "np.einsum(\"nu,nuv->nv\", g1c.T, cond) with "
                       "g1c=g1[:,b] and cond=g2[:,:,b].transpose(2,0,1) "
                       "(d7 q@P contraction, v72p2d7 L603-610), per-row "
                       "renormalize under the frozen row-sum guard "
                       "(non-positive/non-finite row sum → delta-at-0); "
                       "pi_i(e)=marg_i[y_i XOR e] (center_rows_prior, "
                       "GF32 char-2 add=XOR, v28 L189-197)"),
            "l1_conditioning": ("EXACT Bayes marginalization π_i(e)="
                                "Σ_u1 γ1(u1|b_i)·γ2(y_i⊕e|u1,b_i) from "
                                "the frozen bundle (marginal_prior_l2; "
                                "no genie true-u1, no argmax û1, no L1 "
                                "code, no refit). Genie ceiling REMOVED "
                                "for this arm (no D1 ceiling label)"),
            "channel": "empirical 2M triple sampler at n=1024 (packet §2)",
        },
        "u1_source": {
            "source": U1_SOURCE,
            "rule": ("π_i(e)=Σ_u1 γ1(u1|b_i)·γ2(y_i⊕e|u1,b_i) — the exact "
                     "Bayes marginal of the frozen bundle; NO genie "
                     "true-u1, NO argmax û1, NO L1 code, NO estimator, "
                     "NO refit (packet §2/X2)"),
            "mismatch_measurement": ("k = Σ_i 1[û1_i≠u1_i] with "
                                     "û1_i=argmax_u g1[u,b_i], measured "
                                     "from the same synthetic draw "
                                     "(b2e-tied); measurement only, "
                                     "labeled not-a-disclosure, NOT a "
                                     "block criterion"),
            "genie_ceiling": ("REMOVED for this arm (no D1 ceiling label; "
                              "O1/O1R/P0/b2e remain the genie/MAP "
                              "ceilings)"),
        },
        "prior_entropy": {
            "rule": ("prior_entropy_bits = Σ_i H(π_i) bits per block "
                     "(1e-300 floor guard), measured on the centered "
                     "marginal prior actually fed to the decoder"),
            "report_only": ("REPORT-ONLY: never gated, never a block "
                            "criterion (packet §5/X3)"),
            "per_block_column": ("rows.json / block_accounting.csv column "
                                 "prior_entropy_bits (one measured value "
                                 "per completed block)"),
            "mean_bits": pe["mean_bits"],
            "p50": pe["p50"], "p90": pe["p90"], "p99": pe["p99"],
            "max": pe["max"], "min": pe["min"],
            "blocks": pe["blocks"],
            "genie_anchor_bits": GENIE_L2_CONTENT_BITS,
            "pre_registered_observation": ("parity observation (packet "
                                           "§1, NOT a claim): chain rule "
                                           "H(U2|B)=852.544−26.278="
                                           "826.266 b vs genie H_L2·n="
                                           "1024×0.80690067=826.266 b ⇒ "
                                           "the packet expects the "
                                           "marginalized prior to carry "
                                           "the same entropy as the genie "
                                           "prior. MEASURED (dry probe "
                                           "2026-09-21): Σ_i H(π_i) ≈ "
                                           "H_full·n = 852.544 b/block "
                                           "(853.021 b on block 0) — "
                                           "Bayes marginalization "
                                           "flattens the prior by ≈ "
                                           "H(U1|B)·n = 26.278 b vs the "
                                           "genie rows (832.604 b on the "
                                           "same block); entropy parity "
                                           "is NOT a decodability proof, "
                                           "and the flatter prior is a "
                                           "weaker prior (BP convergence "
                                           "is the open risk; b2e: "
                                           "300-iter non-convergence "
                                           "under MAP conditioning)"),
            "u1_mismatches_mean": km["mean"],
            "u1_mismatches_max": km["max"],
        },
        "d_u1": {
            "rule": ("D-u1 = 0.0 MEASURED label: Bob's prior is computed "
                     "from b ALONE — the u1 sum is internal to the Bayes "
                     "marginalization, so there is no u1 disclosure to "
                     "account (packet §4/X6)"),
            "gating": ("f_super=(5m+64)/852.544<=1.3 on the UNCHANGED O1 "
                       "basis with D-u1 = 0.0 (both arms PASS by "
                       "construction; an accounting identity)"),
            "value": D_U1,
            "never_assume_zero_note": ("NEVER assume zero in a claim: "
                                       "D-u1 = 0.0 is a MEASURED label of "
                                       "this decode path (no u1 leaves "
                                       "Bob), not an assumption carried "
                                       "into a claim (B2G packet §4)"),
            "f_super_du0_basis": basis["f_super_basis"],
        },
        "de_cover": _de_cover_record(arm, de_label),
        "ledger": {"decodes": ledger_decodes,
                   "blocks_completed": blocks_completed},
        "blocks_completed": blocks_completed,
        "failures": failures,
        "fer_blocks": fer,
        "pass_bar": f"block FER<=5% (fails/{nb}<={bar})",
        "quarter_tally": quarter_tally(rows),
        "leak_bits": basis["leak_bits"],
        "f_super": basis["f_super_basis"],
        "f_super_label": basis["f_super_label"],
        "f_super_rule": basis["f_super_rule"],
        "d_u1_label": basis["d_u1_label"],
        "h_l2": basis["h_l2"],
        "h_full": basis["h_full"],
        "f_bar": (f"f_super=(5m+64)/852.544<={F_SUPER_MAX} on the "
                  f"UNCHANGED O1 basis (D-u1 = 0.0 MEASURED label; "
                  f"packet §4 — no cross-arm pooling)"),
        "verdict": verdict,
        "partial": bool(partial),
        "next_block": int(next_block),
        "resume": {"continuations_used": len(wall_windows) - 1,
                   "max_continuations": 1},
        "wall_windows": list(wall_windows),
        "elapsed_s": float(elapsed_s),
        "n_rows": n,
        "resume_policy_note": ("B2G packet §6: checkpoint-per-block + at "
                               "most ONE explicit wall-partial "
                               "--resume-from in a fresh window; terminal "
                               "FAIL/early-stop states never resume; no "
                               "auto-relaunch. A second resume refuses."),
        "verify": {
            "pins_ok": True,  # construct gate passed pre-run
            "ledger_ok": ledger_decodes == blocks_completed,
            "rows_ok": n == blocks_completed,
        },
    }


def _validate_partial(manifest: dict, rows: list, arm: str,
                      block_base: int = B2G_BLOCK_BASE,
                      n_blocks: int = B2G_N_BLOCKS,
                      construct_seed: int = B2G_CONSTRUCT_SEED) -> dict:
    """Fail-closed partial validation BEFORE any decode (zero decodes on
    refuse). Checks: campaign+arm match, frozen seeds/budgets for THIS
    run's (block_base, n_blocks, construct_seed), ledger internal
    consistency (decodes == blocks, rows contiguous 0..k-1), no final
    verdict (completion is not resumable), at most-one continuation
    unused (exactly one wall window so far)."""
    if not isinstance(manifest, dict):
        refuse("partial manifest not a dict")
    if not isinstance(rows, list):
        refuse("partial rows not a list")
    if manifest.get("campaign") != CAMPAIGN_LABEL:
        refuse("partial campaign mismatch (fail closed)")
    if manifest.get("arm") != arm:
        refuse("partial arm mismatch (fail closed)")
    seeds = manifest.get("seeds", {})
    if (not isinstance(seeds, dict)
            or seeds.get("policy") != "literal-frozen (B2G packet §4; NOT derived)"
            or seeds.get("block_base") != int(block_base)):
        refuse("partial seeds mismatch this run's block base")
    if manifest.get("budgets", None) != {"wall_cap_s": WALL_CAP_S,
                                         "per_decode_cap_s": PER_DECODE_CAP_S,
                                         "rss_gib": RSS_CAP_GIB,
                                         "max_blocks": int(n_blocks),
                                         "max_decodes": int(n_blocks)}:
        refuse("partial budgets mismatch this run's n-blocks")
    if manifest.get("n_blocks", int(n_blocks)) != int(n_blocks):
        refuse("partial n-blocks mismatch this run")
    con = manifest.get("construct", {})
    if (isinstance(con, dict) and "seed" in con
            and con.get("seed") != int(construct_seed)):
        refuse("partial construct seed mismatch this run")
    if manifest.get("verdict") not in ("INCOMPLETE-wall",):
        refuse("partial carries a final/verdict state (nothing resumable; "
               "completion and FAIL states never resume)")
    blocks_completed = manifest.get("blocks_completed")
    failures = manifest.get("failures")
    ledger = manifest.get("ledger", {})
    try:
        k, f = int(blocks_completed), int(failures)
        ld = int(ledger.get("decodes"))
    except Exception:  # noqa: BLE001
        refuse("partial counts corrupt")
    if not 0 <= k < int(n_blocks) or not 0 <= f <= k or ld != k:
        refuse("partial ledger/blocks counts corrupt")
    if len(rows) != k:
        refuse(f"partial rows {len(rows)} != blocks_completed {k}")
    for i, r in enumerate(rows):
        if not isinstance(r, dict) or r.get("block") != i:
            refuse("partial blocks not contiguous 0..k-1")
    windows = manifest.get("wall_windows", None)
    if not isinstance(windows, list) or len(windows) != 1:
        refuse("partial wall_windows != exactly one window "
               "(continuation already used or corrupt)")
    try:
        float(windows[0].get("turn_start"))
        assert windows[0].get("cap") == WALL_CAP_S
    except Exception:  # noqa: BLE001
        refuse("partial wall window corrupt")
    return {"blocks_completed": k, "failures": f, "decodes": ld,
            "windows": windows}


def _load_partial_fs(partial_root: str):
    try:
        with open(os.path.join(partial_root, "manifest.json")) as fh:
            manifest = json.load(fh)
        with open(os.path.join(partial_root, "rows.json")) as fh:
            rows = json.load(fh)
    except Refusal:
        raise
    except Exception as exc:  # noqa: BLE001 — fail closed, zero decodes
        refuse(f"partial load failed ({partial_root}): "
               f"{type(exc).__name__}: {exc}")
    return manifest, rows


def _construct_gate(arm: str, construct_fn: Callable,
                    seed: int = B2G_CONSTRUCT_SEED,
                    trials: int = B2G_MAX_TRIALS) -> dict:
    """Pre-run construction gate (packet §3/X3): build the arm via
    ``construct_fn(arm, seed, trials)`` TWICE and require
    construct-twice-identical; assert four_cycles == 0 AND rank == m
    (GATED; mismatch halts STOP-BLOCKED pre-decode); min_girth is
    RECORDED as-measured, never gated (P0/R2-amendment precedent; O1R
    measured A208 girth 6 at seed 2026092011 — recorded covariate). The
    production ``construct_fn`` is ``construct_arm`` above, which
    delegates to the frozen O1 constructor on the A208/A202 code at the
    B2G seed 2026092011 (second construction instance). Unknown arm
    refuses (rc=2). No alternate seeds; no tuning.
    """
    if arm not in ARMS:
        refuse(f"unknown arm {arm} (frozen: F208|F202 only)")
    if isinstance(seed, bool) or not isinstance(seed, int):
        refuse("construct seed must be an integer")
    if isinstance(trials, bool) or not isinstance(trials, int) or trials < 1:
        refuse("construct trials must be a positive int")
    try:
        code_a = construct_fn(arm, seed, trials)
        code_b = construct_fn(arm, seed, trials)
    except Refusal:
        raise
    except Exception as exc:  # noqa: BLE001 — fail closed pre-decode
        refuse(f"construction failed ({arm}): "
               f"{type(exc).__name__}: {exc}")
    ta, tb = code_a.get("triples"), code_b.get("triples")
    if ta is not None or tb is not None:
        try:
            sa = sorted(tuple(map(int, t)) for t in ta)
            sb = sorted(tuple(map(int, t)) for t in tb)
        except Exception:  # noqa: BLE001
            refuse(f"construction triples corrupt ({arm}; STOP-BLOCKED)")
        if sa != sb:
            refuse(f"construct-twice mismatch ({arm}; not identical; "
                   f"STOP-BLOCKED)")
    if code_a.get("status", "ok") != "ok":
        refuse(f"construction {code_a.get('status')} ({arm}; STOP-BLOCKED)")
    m = int(ARMS[arm]["m"])
    try:
        fc = int(code_a.get("four_cycles"))
        girth = int(code_a.get("min_girth"))
        rank = int(code_a.get("rank"))
    except Exception:  # noqa: BLE001
        refuse(f"construction missing fc/girth/rank pins ({arm}; STOP-BLOCKED)")
    if fc != 0:
        refuse(f"{arm} four_cycles {fc} != 0 (STOP-BLOCKED; B2G packet "
               f"§3/X3; measured girth {girth})")
    if rank != m:
        refuse(f"{arm} rank {rank} != {m} (STOP-BLOCKED; B2G packet "
               f"§3/X3; measured girth {girth})")
    code_a["construct_seed"] = seed
    code_a["construct_trials"] = trials
    code_a["measured_girth"] = girth  # recorded-not-gated
    return code_a


def execute(*, root: str, arm: str,
            bundle: dict[str, Any] | None = None,
            construct_fn: Callable | None = None,
            decode_fn: Callable | None = None,
            clock: Callable | None = None,
            rss_fn: Callable | None = None,
            writer: Callable | None = None,
            resume_from: str | None = None,
            max_blocks: int | None = None,
            de_label: str | None = None,
            block_base: int = B2G_BLOCK_BASE,
            n_blocks: int = B2G_N_BLOCKS,
            construct_seed: int = B2G_CONSTRUCT_SEED,
            construct_trials: int = B2G_MAX_TRIALS) -> dict:
    """Run (or once-continue) the frozen 240-block B2G campaign under
    ``root``.

    One arm per invocation (F208|F202); paired block seeds shared across
    arms (2026095601+idx, ``o1_blk:`` stream). ``max_blocks`` is a
    PROBE-ONLY cap (timing integration; never a CLI flag, never part of
    any verdict). Without an injected ``decode_fn``, ``bundle`` is
    required (no silent production bind — the CLI binds ``--gamma``
    explicitly). Gate (a) fails/240 ≤ 12 with early-stop at the 13th
    fail; gate (b) f_super = (5m+64)/852.544 ≤ 1.3 on the unchanged O1
    basis (D-u1 = 0.0 MEASURED label). All writes stay under ``root``.
    No auto-relaunch: at most ONE explicit wall-partial
    ``--resume-from`` in a fresh window.
    """
    if arm not in ARMS:
        refuse(f"unknown arm {arm} (frozen: F208|F202 only)")
    if de_label is not None and de_label not in DE_LABELS:
        refuse(f"unknown de-label {de_label} (frozen: covered|exploratory)")
    if isinstance(block_base, bool) or not isinstance(block_base, int):
        refuse("block_base must be an integer literal")
    if isinstance(n_blocks, bool) or not isinstance(n_blocks, int) \
            or n_blocks < 1:
        refuse("n_blocks must be a positive int")
    if isinstance(construct_seed, bool) \
            or not isinstance(construct_seed, int):
        refuse("construct_seed must be an integer")
    if isinstance(construct_trials, bool) \
            or not isinstance(construct_trials, int) \
            or construct_trials < 1:
        refuse("construct_trials must be a positive int")
    bar = fail_bar(n_blocks)
    _check_root(root)
    m = int(ARMS[arm]["m"])
    construct_fn = construct_fn or construct_arm
    if decode_fn is None:
        if bundle is None:
            refuse("empirical bundle required (no silent production bind; "
                   "pass bundle or bind --gamma at the CLI)")
        _bundle = bundle

        def decode_fn(construction, seed, _b=_bundle):  # noqa: B023
            return decode_block_marginal(construction, seed, _b, B2G_N, m)
    clock = clock or time.monotonic
    rss_fn = rss_fn or _default_rss
    writer = writer or default_writer
    if max_blocks is not None and (
            not isinstance(max_blocks, int) or max_blocks < 1):
        refuse("max_blocks (probe-only) must be a positive int")

    if resume_from is not None:
        # Explicit continuation: root must equal the partial root.
        if root != resume_from:
            refuse("root/resume-from mismatch (fail closed: pass same path)")
        if not os.path.exists(resume_from):
            refuse(f"nothing to resume (absent): {resume_from}")
        manifest_p, rows_p = _load_partial_fs(resume_from)
        st = _validate_partial(manifest_p, rows_p, arm,
                               block_base=block_base, n_blocks=n_blocks,
                               construct_seed=construct_seed)
        construction = _construct_gate(arm, construct_fn,
                                       construct_seed, construct_trials)
        rows = list(rows_p)
        failures = int(st["failures"])
        ledger_decodes = int(st["decodes"])
        t_start = clock()
        wall_windows = list(st["windows"]) + [
            {"turn_start": float(t_start), "cap": WALL_CAP_S}]
        start_block = int(st["blocks_completed"])
    else:
        if os.path.exists(root):
            refuse(f"root not fresh: {root}")
        construction = _construct_gate(arm, construct_fn,
                                       construct_seed, construct_trials)
        rows = []
        failures = 0
        ledger_decodes = 0
        t_start = clock()
        wall_windows = [{"turn_start": float(t_start), "cap": WALL_CAP_S}]
        start_block = 0

    target = n_blocks if max_blocks is None else min(max_blocks, n_blocks)

    def _flush(verdict: str, partial: bool, next_block: int):
        mf = _build_manifest(
            arm=arm, construction=construction, rows=rows,
            failures=failures, blocks_completed=len(rows), verdict=verdict,
            partial=partial, next_block=next_block,
            wall_windows=wall_windows, ledger_decodes=ledger_decodes,
            elapsed_s=clock() - t_start, de_label=de_label,
            block_base=block_base, n_blocks=n_blocks)
        writer(root, {"manifest.json": json.dumps(mf, indent=1,
                                                  sort_keys=True, default=str),
                      "rows.json": json.dumps(rows, indent=1,
                                              sort_keys=True, default=str),
                      "block_accounting.csv": block_accounting_csv(rows)})
        return mf

    for k in range(start_block, target):
        # Wall check per block (fresh window per invocation).
        if clock() - t_start > WALL_CAP_S:
            return _flush("INCOMPLETE-wall", True, k)
        try:
            rss_gib = float(rss_fn()) / (1024 ** 3)
        except Exception:  # noqa: BLE001 — probe failure never halts
            rss_gib = 0.0
        if rss_gib >= RSS_CAP_GIB:
            return _flush("FAIL(budget)", True, k)
        seed = block_seed(arm, k, block_base)
        t0 = clock()
        try:
            out = decode_fn(construction, seed)
        except Exception as exc:  # noqa: BLE001 — no-retry: retain + halt
            rows.append({"block": k, "status": "error",
                         "error": f"{type(exc).__name__}: {exc}"})
            return _flush("FAIL(budget)", True, k)
        dt = clock() - t0
        if dt > PER_DECODE_CAP_S:
            rows.append({"block": k, "status": "overrun",
                         "decode_s": dt})
            return _flush("FAIL(budget)", True, k)
        # Marginal-decode output contract (fail closed on a malformed row).
        pe = out.get("prior_entropy_bits")
        km = out.get("u1_mismatches")
        if isinstance(pe, bool) or not isinstance(pe, (int, float,
                                                       np.floating)):
            refuse(f"decode output missing numeric prior_entropy_bits "
                   f"(block {k}; fail closed)")
        if isinstance(km, bool) or not isinstance(km, (int, np.integer)):
            refuse(f"decode output missing integer u1_mismatches "
                   f"(block {k}; fail closed)")
        ok = bool(out.get("exact_match") is True)
        if not ok:
            failures += 1
        ledger_decodes += 1
        basis = leak_basis(arm)
        rows.append({
            "block": k,
            "seed": seed,
            "exact_match": bool(out.get("exact_match", False)),
            "block_accept": ok,
            "block_fail": 0 if ok else 1,
            "status": out.get("status"),
            "converged": bool(out.get("reconstruction_ok", False)),
            "iterations": out.get("iterations"),
            "wall_s": dt,
            "u1_source": U1_SOURCE,
            "prior_entropy_bits": float(pe),
            "u1_mismatches": int(km),
            "d_u1": basis["d_u1"],
            "d_u1_label": basis["d_u1_label"],
            "leak_bits": basis["leak_bits"],
            "f_super": basis["f_super_basis"],
        })
        # Checkpoint per COMPLETED block (overwrite-in-place, single writer).
        _flush("INCOMPLETE-wall", True, k + 1)
        if failures > bar:
            # Early-stop: (bar+1)-th block failure makes the bar
            # unpassable (n=240: 13th). Retain partials.
            return _flush("FAIL-early-stop", True, k + 1)

    if max_blocks is not None:
        # Probe-only truncation: no verdict, no claim.
        return _flush("PROBE-truncated", True, target)
    passed = (failures <= bar
              and f_super_du0(arm) <= F_SUPER_MAX)
    return _flush("PASS" if passed else "FAIL", False, n_blocks)


def run_execution(root: str, arm: str,
                  resume_from: str | None = None,
                  gamma: str = GAMMA_DEFAULT,
                  source: str = SOURCE_DEFAULT,
                  bundle: dict[str, Any] | None = None,
                  de_label: str | None = None,
                  block_base: int = B2G_BLOCK_BASE,
                  n_blocks: int = B2G_N_BLOCKS,
                  construct_seed: int = B2G_CONSTRUCT_SEED,
                  construct_trials: int = B2G_MAX_TRIALS) -> int:
    bound = bundle if bundle is not None else s2c.bind_empirical_bundle(
        gamma, source)
    manifest = execute(root=root, arm=arm, bundle=bound,
                       resume_from=resume_from, de_label=de_label,
                       block_base=block_base, n_blocks=n_blocks,
                       construct_seed=construct_seed,
                       construct_trials=construct_trials)
    print(json.dumps({"arm": manifest["arm"],
                      "campaign": manifest["campaign"],
                      "u1_source": U1_SOURCE,
                      "verdict": manifest["verdict"],
                      "failures": manifest["failures"],
                      "fer_blocks": manifest["fer_blocks"],
                      "f_super": manifest["f_super"],
                      "prior_entropy_mean_bits": manifest[
                          "prior_entropy"]["mean_bits"],
                      "u1_mismatches_mean": manifest[
                          "prior_entropy"]["u1_mismatches_mean"],
                      "de_cover": manifest["de_cover"],
                      "ledger": manifest["ledger"],
                      "quarter_tally": manifest["quarter_tally"],
                      "wall_windows": manifest["wall_windows"],
                      "root": root}, indent=1, sort_keys=True, default=str))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute-real", action="store_true", default=False)
    ap.add_argument("--execution-authorized", action="store_true",
                    default=False)
    ap.add_argument("--arm", default="")
    ap.add_argument("--root", default="")
    ap.add_argument("--resume-from", default="")
    ap.add_argument("--gamma", default=GAMMA_DEFAULT)
    ap.add_argument("--source", default=SOURCE_DEFAULT)
    ap.add_argument("--de-label", default="")
    ap.add_argument("--block-base", type=int, default=B2G_BLOCK_BASE)
    ap.add_argument("--n-blocks", type=int, default=B2G_N_BLOCKS)
    ap.add_argument("--construct-seed", type=int,
                    default=B2G_CONSTRUCT_SEED)
    ap.add_argument("--construct-trials", type=int,
                    default=B2G_MAX_TRIALS)
    args = ap.parse_args(argv)
    # Dual-flag gate: refuse EVERYTHING else rc=2 BEFORE any root/contact.
    # There is no profile-only mode and no silent path.
    if not args.execute_real:
        refuse("refusing: --execute-real missing (rc2 pre-anything)")
    if not args.execution_authorized:
        refuse("refusing: --execution-authorized missing (rc2 pre-anything)")
    if args.arm not in ARMS:
        refuse(f"unknown arm {args.arm} (frozen: F208|F202 only)")
    if args.de_label and args.de_label not in DE_LABELS:
        refuse(f"unknown de-label {args.de_label} (frozen: covered|exploratory)")
    if args.resume_from and args.root and args.root != args.resume_from:
        refuse("root/resume-from mismatch (fail closed)")
    if isinstance(args.block_base, bool) or args.block_base is None:
        refuse("block-base must be an integer literal")
    if isinstance(args.n_blocks, bool) or args.n_blocks is None \
            or args.n_blocks < 1:
        refuse("n-blocks must be a positive int")
    if isinstance(args.construct_seed, bool) \
            or args.construct_seed is None:
        refuse("construct-seed must be an integer")
    if isinstance(args.construct_trials, bool) \
            or args.construct_trials is None \
            or args.construct_trials < 1:
        refuse("construct-trials must be a positive int")
    # B2G has EXACTLY ONE frozen configuration: any deviation is a
    # science-input change → STOP (packet §6). The execute() parameters
    # exist for resume validation; the CLI cannot drift them.
    if args.construct_seed != B2G_CONSTRUCT_SEED:
        refuse(f"construct-seed must be the frozen {B2G_CONSTRUCT_SEED} "
               f"(got {args.construct_seed}; B2G packet §3 — 2026092011 "
               f"is the ONLY frozen B2G construct seed (O1R R2 second "
               f"instance); 2026092001 is b2f's frozen value, NOT b2g's; "
               f"any seed change is a science-input change → STOP)")
    if args.construct_trials != B2G_MAX_TRIALS:
        refuse(f"construct-trials must be the frozen {B2G_MAX_TRIALS} "
               f"(got {args.construct_trials}; B2G packet §3 — any trials "
               f"change is a science-input change → STOP)")
    if args.block_base != B2G_BLOCK_BASE:
        refuse(f"block-base must be the frozen {B2G_BLOCK_BASE} "
               f"(got {args.block_base}; B2G packet §4 — any block-seed "
               f"change is a science-input change → STOP)")
    if args.n_blocks != B2G_N_BLOCKS:
        refuse(f"n-blocks must be the frozen {B2G_N_BLOCKS} "
               f"(got {args.n_blocks}; B2G packet §4 — any width change "
               f"is a science-input change → STOP)")
    root = args.resume_from or args.root
    if not root:
        refuse("root required (fresh additive workspace/b2g_<uuid>)")
    if not _allows_root(root):
        refuse(f"root must be fresh additive {ROOT_PREFIX}<uuid> "
               f"(got {root})")
    return run_execution(root=root, arm=args.arm,
                         resume_from=args.resume_from or None,
                         gamma=args.gamma, source=args.source,
                         bundle=None,
                         de_label=args.de_label or None,
                         block_base=args.block_base,
                         n_blocks=args.n_blocks,
                         construct_seed=args.construct_seed,
                         construct_trials=args.construct_trials)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
