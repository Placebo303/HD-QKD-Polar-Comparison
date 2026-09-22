"""V80 B2E MAP-u1 FER campaign executor (EXPLORE code — NOT execution).

Frozen contract: ``docs/research_cycles/V80-NBLDPC-JAN21/
B2E_EXPERIMENT_PACKET_20260921.md`` (G-B2E, frozen, NOT granted) +
``B2E_EXPERIMENT_PROMPT_20260921.md``, read through the
**Amendment 2026-09-21** (entropy-sum D-u1 + arm-mean gate (b)). Execution
needs a fresh explicit grant + Pre-EXECUTE; this module only provides the
executor + fake-testable mechanics. Synthetic draws from the read-only 2M
derived bundle only; no real/Jan-21 frames; no writes outside the run root;
never writes ``results/`` or ``outputs_comparison/``.

Why this thin NEW module (packet §7): every L2 arm CONDITIONS on u1 —
``posterior_rows_l2`` = γ₂(·|b,u1); the u1 dependence lives entirely in
Bob's per-symbol prior, so retiring genie may not require an L1 CODE, only
a u1 estimate at Bob. B2E switches the u1 source genie → MAP
(û1_i = argmax_u γ1(u1|b_i), free argmax from the frozen bundle — no
refit, no decoder, no DE, no L1 construction) AND moves gate (b) to the
amended measured D-u1 accounting ⇒ a different decode + accounting path
than the O1/O1R/P0 genie arms, which must stay byte-identical for replay.
Frozen modules (``v80_o1_campaign``, ``v80_s2c_campaign``, v10/v26/v28
kernels) are imported READ-ONLY and never edited (L1B precedent).

Semantics (packet §§1–5; identical to A208/A202 except the u1 source):
ONE code n=1024, GF(32), λ={2:1}; acceptance unit = ONE BLOCK = one
n=1024 decode with ``exact_match is True`` (x̂==u2). Two arms only:
**B208 PRIMARY** (m=208, the A208 construction instance — no L1-row
funding) and **B202 SECONDARY** (m=202, the A202 construction instance —
m1=6 accounting room). Both built via ``construct_arm("A208"|"A202",
seed=2026092001, trials=20)`` ⇒ byte-identical paired instances (recorded;
never rebuilt). Pins: fc==0 AND rank-full AND construct-twice-identical
GATED (mismatch → STOP-BLOCKED pre-decode); girth RECORDED-not-gated
(P0/R2-amendment precedent). Per block: triple draw on the
``o1_blk:{seed}`` stream (frozen sampler, draw order unchanged; seeds
2026095601+idx, paired with O1R/P0/L1B — NO independence claim);
û1 = argmax over g1[:,b]; k = Σ_i 1[û1_i≠u1_i] MEASURED (measurement
only, labeled not-a-disclosure); rows = ``posterior_rows_l2(bundle,b,û1)``
(function and zero-mass semantics unchanged — only the u1 argument source
changes); XOR-centered prior; ``decode_error_domain_posterior`` ONLY;
max_iter=300/streak 3; per-decode cap 300 s. û1 correctness is NOT a block
criterion (estimator error may be absorbed by BP). Genie ceiling REMOVED
for this arm (no D1 ceiling label).

Accounting (Amendment 2026-09-21; the conservative reading GATES):
per-block ``d_u1_bits`` = Σ_i H(γ1(·|b_i)) — minimum SW-style disclosure
to resolve u1 from b (expected mean 1024×H_L1 = 26.28 b; measured per
block from the frozen bundle, no refit). Gate (b) (arm-mean, mean-based):
f_super_conservative = (m·5 + 64 + mean(d_u1_bits))/852.544 ≤ 1.3; the
per-block d_u1 distribution (p50/p90/p99/max) is REPORTED. Report-only,
NEVER gated: (i) f_super_du0 = (m·5+64)/852.544 with the D-u1=0.0
MEASURED label (B208 1.294947 / B202 1.259759 — the A208/A202-comparable
line); (ii) the 5×k ultra-conservative reading
f_super_5k = (m·5+64+5·mean(k))/852.544 (frozen §4 history; sensitivity
line only). Gate (a): fails/240 ≤ 12 (5% exact), early-stop at the 13th
fail → FAIL, retain partials. No cross-arm pooling; no rerun; no tuning.

Reuse from ``v80_o1_campaign``/``v80_s2c_campaign`` (read-only patterns,
never their science): dual-flag gate ``--execute-real
--execution-authorized`` refusing everything else rc=2 pre-anything;
checkpoint manifest+rows overwrite-in-place single writer; append-only
``wall_windows``; explicit ``--resume-from`` with strict pre-decode
validation and ≤1 wall-partial continuation (no auto-relaunch); early-stop
at bar+1 block fails; root policy (fresh additive ``workspace/b2e_<uuid8>``
per arm; ``results/`` + ``outputs_comparison/`` forbidden). Channel
helpers (``bind_empirical_bundle``, ``empirical_triple_sampler``,
``posterior_rows_l2``, ``center_rows_prior``) are reused READ-ONLY from
``v80_s2c_campaign`` — never re-implemented here. The GF(32) field order
``Q`` comes read-only from the frozen ``v80_s2_peg`` anchor module.

B2E freezes EXACTLY ONE runnable configuration (arms B208/B202 only;
construct seed 2026092001/trials 20 via the A208/A202 instance; block
base 2026095601; 240 blocks), so the CLI refuses any deviation of
``--construct-seed``/``--construct-trials``/``--block-base``/
``--n-blocks`` from those frozen literals: any such change is a
science-input change → STOP (packet §6).
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
    "B2E_CONSTRUCT_SEED", "B2E_MAX_TRIALS", "B2E_BLOCK_BASE",
    "B2E_N_BLOCKS", "B2E_N", "B2E_ROOT_PREFIX",
    "ARMS", "CAMPAIGN_LABEL", "U1_SOURCE",
    "MAX_ITER", "H_L1_B2E", "H_FULL_B2E", "CONTENT_BITS", "L1_CONTENT_BITS",
    "D_BLIND", "F_SUPER_MAX",
    "WALL_CAP_S", "PER_DECODE_CAP_S", "RSS_CAP_GIB",
    "ROOT_PREFIX", "FORBIDDEN_ROOT_PARTS",
    "GAMMA_DEFAULT", "SOURCE_DEFAULT", "DE_LABELS",
    "Refusal", "refuse", "block_seed", "stream_seed", "fail_bar",
    "construct_arm", "map_u1", "u1_mismatches", "d_u1_bits",
    "f_super_du0", "f_super_conservative", "f_super_5k",
    "leak_basis", "decode_block_map_u1",
    "quarter_tally", "d_u1_stats", "violating_block_count",
    "block_accounting_csv",
    "run_execution", "execute", "main",
]

#: Frozen B2E construction seed (packet §2; both arms; the A208/A202
#: instance — imported read-only from the frozen O1 module, X1).
B2E_CONSTRUCT_SEED = o1.O1_CONSTRUCT_SEED
#: Frozen constructor trials (packet §2; both arms).
B2E_MAX_TRIALS = o1.O1_MAX_TRIALS
#: Frozen code length (packet §1): n=1024 GF(32) symbols/block.
B2E_N = o1.O1_N
#: Frozen literal block-seed base (packet §6; LITERAL, paired reuse with
#: O1R/P0/L1B — SAME 240 frames; NO independence claim).
B2E_BLOCK_BASE = 2026095601
#: Frozen campaign width (packet §6): 240 blocks = 240 decodes/arm.
B2E_N_BLOCKS = 240
#: Fresh additive B2E run-root prefix (packet §6: workspace/b2e_<uuid8>).
B2E_ROOT_PREFIX = "workspace/b2e_"
ROOT_PREFIX = B2E_ROOT_PREFIX
#: Roots the executor never writes under.
FORBIDDEN_ROOT_PARTS = ("results", "outputs_comparison")
#: Frozen decoder cap (packet §3): max_iter=300, streak default (3).
MAX_ITER = o1.MAX_ITER
#: Frozen caps (packet §6): single window 3600 s; per-decode 300 s; 4 GiB.
WALL_CAP_S = o1.WALL_CAP_S
PER_DECODE_CAP_S = o1.PER_DECODE_CAP_S
RSS_CAP_GIB = o1.RSS_CAP_GIB
#: Frozen full-content anchor (S2/P0 basis): H_full=0.83256272 (imported
#: read-only from the frozen O1 module, X1).
H_FULL_B2E = o1.H_FULL_O1
#: Content basis: 1024 * H_full = 852.544 bits (packet §4).
CONTENT_BITS = B2E_N * H_FULL_B2E
#: Frozen L1 entropy anchor H_L1=0.02566205 (S1 readiness; v3 memo §2.1
#: reproduced). Report-only pre-registered observation (26.28 b/block).
H_L1_B2E = 0.02566205
#: L1 content: 1024 * H_L1 ≈ 26.28 bits (v3 memo §2.1).
L1_CONTENT_BITS = B2E_N * H_L1_B2E
#: D_blind = 0 MEASURED placeholder (NEVER-ASSUME-ZERO label on records).
D_BLIND = 0.0
#: Frozen f_super bar (Amendment 2026-09-21, arm-mean reading).
F_SUPER_MAX = 1.3
#: u1 source label for this campaign (packet §3/X5).
U1_SOURCE = "MAP"
#: Campaign label (packet §7/X7).
CAMPAIGN_LABEL = "B2E-map-u1"
#: Read-only derived bundle (packet §3): gamma file + p_b sidecar sibling
#: (same files as S2c/O1; binding helper reused read-only from s2c).
GAMMA_DEFAULT = s2c.GAMMA_DEFAULT
#: Worst-source anchor (packet §3); never auto-merge sources.
SOURCE_DEFAULT = s2c.SOURCE_DEFAULT
#: Allowed DE-cover labels threading into the campaign manifest (packet
#: §7/X7: B208 'covered' carried from the A208-DE precheck; B202
#: 'exploratory' P0 precedent — NO new DE run in B2E).
DE_LABELS = ("covered", "exploratory")
#: Frozen arms table (packet §2; EXACTLY two — no more, no substitutions).
#: ``source_arm`` names the byte-identical paired construction instance in
#: the frozen O1 table (B208→A208, B202→A202); B200 and every other m are
#: OUT OF SCOPE (not frozen, not runnable).
ARMS: dict[str, dict[str, Any]] = {
    "B208": {"m": 208, "source_arm": "A208", "lambda": {2: 1.0},
             "rate": 1.0 - 208 / 1024, "leak_bits": 208 * 5 + 64,
             "role": "PRIMARY (m=208; A208 construction instance; "
                     "m2=208 leaves NO L1-row funding)"},
    "B202": {"m": 202, "source_arm": "A202", "lambda": {2: 1.0},
             "rate": 1.0 - 202 / 1024, "leak_bits": 202 * 5 + 64,
             "role": "SECONDARY (m=202; A202 construction instance; "
                     "m2=202 = m1=6 accounting room)"},
}


class Refusal(SystemExit):
    """rc=2 pre-write refusal (unauthorized / invalid / gate-blocked)."""


def refuse(reason: str) -> "Any":
    print(f"B2E-REFUSAL rc=2: {reason}", file=sys.stderr)
    raise Refusal(2)


def block_seed(arm: str, idx: int, base: int | None = None) -> int:
    """Frozen literal block seed: base+idx (packet §6).

    Default base is the frozen B2E literal 2026095601, idx=0..239
    (paired reuse with O1R/P0/L1B; NO independence claim). Unknown arm
    refuses (fail closed, rc=2).
    """
    if arm not in ARMS:
        refuse(f"unknown arm {arm} (frozen: B208|B202 only)")
    b = B2E_BLOCK_BASE if base is None else base
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

    SAME ``o1_blk:`` domain as O1R/P0/L1B (paired reuse; byte-identical
    triple path ⇒ (b,u1) marginal identical). Reused READ-ONLY from the
    frozen O1 module (X1).
    """
    return o1.stream_seed(int(seed))


def construct_arm(arm: str, seed: int = B2E_CONSTRUCT_SEED,
                  max_trials: int = B2E_MAX_TRIALS) -> dict[str, Any]:
    """B2E arm constructor (packet §2/X2): delegate to the FROZEN O1
    constructor on the paired source instance — B208 → ``A208``, B202 →
    ``A202`` — with the identical (n, m, λ, seed, trials) ⇒ byte-identical
    paired construction instance (recorded as paired construction; never
    rebuilt). No re-seed; no tuning. Pure in-memory; no disk writes.
    """
    if arm not in ARMS:
        refuse(f"unknown arm {arm} (frozen: B208|B202 only)")
    if isinstance(seed, bool) or not isinstance(seed, int):
        refuse("construct seed must be an integer")
    if isinstance(max_trials, bool) or not isinstance(max_trials, int) \
            or max_trials < 1:
        refuse("construct trials must be a positive int")
    code = o1.construct_arm(ARMS[arm]["source_arm"], int(seed),
                            int(max_trials))
    code["source_arm"] = ARMS[arm]["source_arm"]
    return code


def map_u1(bundle: dict[str, Any], b_vec: Any) -> np.ndarray:
    """û1_i = argmax_u g1[u, b_i] (packet §3): free argmax over the frozen
    γ1 = P(U1|B) columns — no decoder, no DE, no L1 construction, no
    refit. Returns an int64 vector of MAP u1 estimates.
    """
    g1 = np.asarray(bundle["g1"], dtype=np.float64)
    b = np.asarray(b_vec, dtype=np.int64)
    if b.ndim != 1:
        refuse("MAP u1 needs 1-D b")
    if g1.shape != (32, 1024):
        refuse(f"MAP u1 g1 shape {g1.shape} != (32, 1024)")
    for bb in b.tolist():
        if not 0 <= int(bb) < 1024:
            refuse("MAP u1 b symbol out of domain")
    return np.argmax(g1[:, b], axis=0).astype(np.int64)


def u1_mismatches(u1_true: Any, u1_hat: Any) -> int:
    """k = Σ_i 1[û1_i ≠ u1_i] (packet §3): MEASURED from the same draw.
    Measurement only, labeled not-a-disclosure (true u1 is known in the
    synthetic draw; it never enters the decode).
    """
    a = np.asarray(u1_true, dtype=np.int64)
    h = np.asarray(u1_hat, dtype=np.int64)
    if a.shape != h.shape or a.ndim != 1:
        refuse("mismatch count needs same-shape 1-D (u1_true, u1_hat)")
    return int(np.count_nonzero(a != h))


def d_u1_bits(bundle: dict[str, Any], b_vec: Any) -> float:
    """Per-block D-u1 (Amendment 2026-09-21, the GATING input):
    Σ_i H(γ1(·|b_i)) bits — minimum SW-style disclosure to resolve u1 from
    b (expected mean 1024×H_L1 ≈ 26.28 b; measured per block from the
    frozen bundle, no refit). Column entropy with the zero-mass guard
    (0·log2 0 := 0 via the 1e-300 floor).
    """
    g1 = np.asarray(bundle["g1"], dtype=np.float64)
    b = np.asarray(b_vec, dtype=np.int64)
    if b.ndim != 1:
        refuse("d_u1_bits needs 1-D b")
    if g1.shape != (32, 1024):
        refuse(f"d_u1_bits g1 shape {g1.shape} != (32, 1024)")
    for bb in b.tolist():
        if not 0 <= int(bb) < 1024:
            refuse("d_u1_bits b symbol out of domain")
    cols = g1[:, b]  # (32, n)
    h = -np.sum(cols * np.log2(np.maximum(cols, 1e-300)), axis=0)
    return float(h.sum())


def f_super_du0(arm: str) -> float:
    """Report-only D-u1=0.0 MEASURED label (A208/A202-comparable line):
    (m·5+64)/852.544 — NEVER gated (Amendment 2026-09-21)."""
    if arm not in ARMS:
        refuse(f"unknown arm {arm} (frozen: B208|B202 only)")
    return float(ARMS[arm]["leak_bits"]) / CONTENT_BITS


def f_super_conservative(arm: str, d_u1: float) -> float:
    """GATING reading (Amendment 2026-09-21): per-block / arm-mean
    f_super = (m·5 + 64 + D-u1)/852.544 with D-u1 = the measured entropy
    sum (arm-mean gates; per-block values are reported)."""
    if arm not in ARMS:
        refuse(f"unknown arm {arm} (frozen: B208|B202 only)")
    if isinstance(d_u1, bool) or not isinstance(d_u1, (int, float, np.floating)):
        refuse("d_u1 must be a number (measured entropy sum, bits)")
    return (float(ARMS[arm]["leak_bits"]) + float(d_u1)) / CONTENT_BITS


def f_super_5k(arm: str, k: float) -> float:
    """Report-only ultra-conservative 5×mismatch reading (frozen §4
    history; sensitivity line only — NEVER gated):
    (m·5 + 64 + 5·k)/852.544."""
    if arm not in ARMS:
        refuse(f"unknown arm {arm} (frozen: B208|B202 only)")
    if isinstance(k, bool) or not isinstance(k, (int, float, np.floating)):
        refuse("k must be a number (measured mismatch count)")
    return (float(ARMS[arm]["leak_bits"]) + 5.0 * float(k)) / CONTENT_BITS


def leak_basis(arm: str) -> dict[str, Any]:
    """Frozen B2E accounting (packet §4 + Amendment 2026-09-21).

    GATING: arm-mean f_super_conservative=(m·5+64+mean(d_u1_bits))/
    852.544 ≤ 1.3 (mean-based; D-u1 = measured per-block entropy sum).
    Report-only, NEVER gated: f_super_du0 (D-u1=0.0 MEASURED label; B208
    1.294947 / B202 1.259759 — the A208/A202-comparable line) and the
    5×k ultra-conservative reading (frozen §4 arithmetic; B208 ≈1.342453 /
    B202 ≈1.307264 at the measured mean 8.10 mismatches). D_blind = 0.0
    MEASURED placeholder (NEVER-ASSUME-ZERO label).
    """
    if arm not in ARMS:
        refuse(f"unknown arm {arm} (frozen: B208|B202 only)")
    m = int(ARMS[arm]["m"])
    leak = float(ARMS[arm]["leak_bits"])
    f_du0 = leak / CONTENT_BITS
    headroom = F_SUPER_MAX * CONTENT_BITS - leak
    return {
        "arm": arm,
        "m": m,
        "leak_bits": leak,
        "content_bits": CONTENT_BITS,
        "f_super_du0_basis": f_du0,
        "f_super_du0_label": ("Report-only D-u1=0.0 MEASURED label "
                              "(A208/A202-comparable line): "
                              f"f_super_du0=(m·5+64)/852.544=({m}·5+64)/"
                              f"852.544≈{f_du0:.6f} (H_full=0.83256272). "
                              "NEVER gated (Amendment 2026-09-21)"),
        "f_super_rule": ("GATING (Amendment 2026-09-21, mean-based): "
                         "arm-mean f_super_conservative=(m·5+64+"
                         "mean(d_u1_bits))/852.544<=1.3, d_u1_bits = "
                         "per-block Σ_i H(γ1(·|b_i)) (minimum SW-style "
                         "disclosure to resolve u1 from b; expected mean "
                         "1024×H_L1≈26.28 b). Per-block d_u1 distribution "
                         "(p50/p90/p99/max) is REPORTED."),
        "f_super_5k_label": ("Report-only ultra-conservative 5×k reading "
                             "(frozen §4 history; sensitivity line only, "
                             "NEVER gated): f_super_5k=(m·5+64+5·"
                             "mean(u1_mismatches))/852.544"),
        "h_l1": H_L1_B2E,
        "h_full": H_FULL_B2E,
        "l1_content_bits": L1_CONTENT_BITS,
        "d_blind": D_BLIND,
        "d_blind_label": ("MEASURED zero: no blind/puncturing rounds exist "
                          "in the campaign path — NEVER assume zero in a "
                          "claim (B2E packet §4)"),
        "sensitivity": ("Δf = D/852.544, i.e. each 8.52544 bits of D-u1 "
                        "≈ +0.01"),
        "headroom_bits": headroom,
        "headroom_line": (f"Gate (b) headroom {headroom:.2f} b on the "
                          f"arm-mean D-u1: any arm-mean D-u1 > "
                          f"{headroom:.2f} b fails gate (b) "
                          f"({arm}; Amendment 2026-09-21)"),
    }


def decode_block_map_u1(construction: dict[str, Any], seed: int,
                        bundle: dict[str, Any], n: int,
                        m: int) -> dict[str, Any]:
    """One MAP-u1 empirical-channel block (packet §3): triple draw on the
    ``o1_blk:{seed}`` stream (frozen sampler, draw order UNCHANGED); Alice
    x=u2; Bob y=b&31; û1 = argmax_u γ1(u|b) (free argmax from the frozen
    bundle — no refit, no decoder, no DE, no L1 construction); rows =
    ``posterior_rows_l2(bundle, b, û1)`` (function and zero-mass semantics
    UNCHANGED — only the u1 argument source changes); XOR-centered prior
    into ``decode_error_domain_posterior`` (NEVER the scalar-p
    ``decode_error_domain``); max_iter=300, streak default (3). Returns
    the raw kernel verdict + exact-match flag (``exact_match is True``
    gates block acceptance), the MEASURED u1 mismatch count and the
    per-block D-u1 entropy sum. û1 correctness is NOT a block criterion.
    Fail-closed wiring guard: (n, m) must match the construction under
    test.
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
    u1_hat = map_u1(bundle, b)  # MAP estimate (no decoder/DE/L1)
    k = u1_mismatches(u1, u1_hat)  # MEASURED (not a disclosure)
    du1 = d_u1_bits(bundle, b)  # amended gating input (entropy sum)
    s_x = fftqspa.syndrome_of(field, dense, x.tolist())
    rows = s2c.posterior_rows_l2(bundle, b, u1_hat)  # MAP û1, NOT genie
    prior = s2c.center_rows_prior(rows, y)
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
        "u1_mismatches": int(k),
        "d_u1_bits": float(du1),
        "l1_conditioning": ("MAP û1 = argmax_u γ1(u|b) from the frozen "
                            "bundle (no refit, no decoder, no DE, no L1 "
                            "construction); genie ceiling REMOVED for "
                            "this arm (no D1 ceiling label)"),
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


def d_u1_stats(rows: list[dict]) -> dict[str, Any]:
    """Per-block D-u1 distribution (Amendment 2026-09-21; REPORTED).

    Linear-interpolation percentiles over the completed blocks'
    ``d_u1_bits`` values (error/overrun rows carry no measurement).
    """
    vals = [float(r["d_u1_bits"]) for r in rows
            if isinstance(r, dict)
            and r.get("status") not in ("error", "overrun")
            and isinstance(r.get("d_u1_bits"), (int, float, np.floating))
            and not isinstance(r.get("d_u1_bits"), bool)]
    if not vals:
        return {"blocks": 0, "mean_bits": 0.0, "p50": None, "p90": None,
                "p99": None, "max": None, "min": None}
    a = np.asarray(vals, dtype=np.float64)
    return {"blocks": int(a.size), "mean_bits": float(a.mean()),
            "p50": float(np.percentile(a, 50)),
            "p90": float(np.percentile(a, 90)),
            "p99": float(np.percentile(a, 99)),
            "max": float(a.max()), "min": float(a.min())}


def _mismatch_stats(rows: list[dict]) -> dict[str, Any]:
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


def violating_block_count(rows: list[dict]) -> int:
    """Count of completed blocks whose per-block f_super_conservative
    exceeds the bar (REPORT-ONLY; the Amendment gates the ARM MEAN, not
    per-block values)."""
    n = 0
    for r in rows:
        v = r.get("f_super_conservative")
        if isinstance(v, (int, float, np.floating)) \
                and not isinstance(v, bool) and float(v) > F_SUPER_MAX:
            n += 1
    return n


def block_accounting_csv(rows: list[dict]) -> str:
    """Per-block accounting table (packet §9 deliverable; X5 columns:
    u1_source, u1_mismatches, d_u1_bits, f_super_conservative,
    f_super_du0_report)."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["block", "seed", "exact_match", "status", "iterations",
                "wall_s", "u1_source", "u1_mismatches", "d_u1_bits",
                "d_blind", "leak_bits", "f_super_du0_report",
                "f_super_conservative"])
    for r in rows:
        if r.get("status") in ("error", "overrun"):
            w.writerow([r.get("block"), "", "", r.get("status"), "",
                        "", "", "", "", "", "", "", ""])
            continue
        w.writerow([r.get("block"), r.get("seed"), r.get("exact_match"),
                    r.get("status"), r.get("iterations"), r.get("wall_s"),
                    r.get("u1_source"), r.get("u1_mismatches"),
                    r.get("d_u1_bits"), r.get("d_blind"),
                    r.get("leak_bits"), r.get("f_super_du0_report"),
                    r.get("f_super_conservative")])
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
    """Fresh additive prefix: B2E ``workspace/b2e_<uuid>`` (packet §6)."""
    return root.startswith(ROOT_PREFIX)


def _check_root(root: str) -> None:
    if not root:
        refuse("root required (fresh additive workspace/b2e_<uuid>)")
    parts = Path(root).parts
    if any(p in FORBIDDEN_ROOT_PARTS for p in parts):
        refuse(f"root under forbidden tree (results/outputs_comparison): {root}")


def _de_cover_record(arm: str, de_label: str | None) -> dict[str, Any]:
    """DE-cover label threading (packet §7/X7): B208 defaults 'covered'
    (carried from the A208-DE precheck, O1 packet §3); B202 defaults
    'exploratory' (P0 precedent). NO new DE run in B2E; gates unchanged.
    """
    if arm not in ARMS:
        refuse(f"unknown arm {arm} (frozen: B208|B202 only)")
    default = "covered" if arm == "B208" else "exploratory"
    label = de_label or default
    if label not in DE_LABELS:
        refuse(f"unknown de-label {label} (frozen: covered|exploratory only)")
    note = ("B208 carries the A208-DE precheck outcome (O1 packet §3: "
            "A208 rho differs {9:0.141,10:0.859}); the label is CARRIED, "
            "B2E runs NO new DE — gates unchanged."
            if arm == "B208" else
            "B202 follows the P0 precedent: rate 0.802734375 has no S1 "
            "cover and B2E runs NO new DE — default 'exploratory'; gates "
            "unchanged.")
    return {"label": label,
            "label_source": ("explicit --de-label" if de_label
                             else (f"default '{default}' carried (no new "
                                   f"DE run in B2E; packet §7/X7)")),
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
    bb = B2E_BLOCK_BASE if block_base is None else int(block_base)
    nb = B2E_N_BLOCKS if n_blocks is None else int(n_blocks)
    bar = fail_bar(nb)
    du = d_u1_stats(rows)
    km = _mismatch_stats(rows)
    mean_d = float(du["mean_bits"])
    f_cons_mean = f_super_conservative(arm, mean_d)
    f5k = f_super_5k(arm, km["mean"])
    return {
        "arm": arm,
        "arm_role": spec["role"],
        "campaign": CAMPAIGN_LABEL,
        "paired_construction": {
            "source_arm": spec["source_arm"],
            "note": (f"B{spec['m']} is built via the frozen "
                     f"construct_arm(\"{spec['source_arm']}\", seed "
                     f"{construction.get('construct_seed')}, trials "
                     f"{construction.get('construct_trials')}) — identical "
                     f"(n, m, λ, seed, trials) ⇒ byte-identical instance "
                     f"to the {spec['source_arm']} genie arm (recorded as "
                     f"paired construction; never rebuilt)"),
        },
        "n_blocks": nb,
        "fail_bar": bar,
        "single_code": ("acceptance unit = ONE BLOCK = one n=1024 decode "
                        "with exact_match is True. No frames, no "
                        "group-of-4 rule (B2E packet §1; block≠S2c-group, "
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
                     f"{construction.get('construct_trials')} via the "
                     f"{spec['source_arm']} instance; P0/R2-amendment "
                     f"precedent; construct-twice-identical required; "
                     f"mismatch on gated fields halts STOP-BLOCKED)"),
            "sockets_parity": {"sockets": construction.get("total_sockets"),
                               "parity": construction.get("parallel_edges")},
        },
        "seeds": {
            "policy": "literal-frozen (B2E packet §6; NOT derived)",
            "block_base": bb,
            "block_rule": f"base+idx, idx=0..{nb - 1} (block k → idx=k)",
            "n_blocks": nb,
            "fail_bar": bar,
            "stream": "common.v10_seed(f\"o1_blk:{seed}\") (paired across "
                      "arms; distinct domain from S2c s2c_emp:)",
            "paired_note": ("Blocks REUSED paired with O1R/P0/L1B: literal "
                            "2026095601+idx idx=0..239, stream "
                            "o1_blk:{seed} — SAME 240 frames (byte-identical "
                            "triple path ⇒ (b,u1) marginal identical; "
                            "paired MAP-vs-genie contrast on same frames); "
                            "prior use declared (O1R/P0/L1B roots+docs = "
                            "expected hits); NO independence claim "
                            "B2E↔O1R↔P0↔L1B (B2E packet §6)"),
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
                       "rows_i=gamma_2(.|b_i,û1_i) (posterior_rows_l2 s2c "
                       "L288-316 — û1 MAP, NOT genie); pi_i(e)=rows_i[y_i "
                       "XOR e] (center_rows_prior, GF32 char-2 add=XOR, "
                       "v28 L189-197)"),
            "l1_conditioning": ("MAP û1 = argmax_u γ1(u|b_i) from the "
                                "frozen bundle (no refit, no decoder, no "
                                "DE, no L1 construction). Genie ceiling "
                                "REMOVED for this arm (no D1 ceiling "
                                "label); û1 correctness is NOT a block "
                                "criterion (estimator error may be "
                                "absorbed by BP)"),
            "channel": "empirical 2M triple sampler at n=1024 (packet §3)",
        },
        "u1_estimator": {
            "source": U1_SOURCE,
            "rule": ("û1_i = argmax_u g1[u,b_i] — free argmax over the "
                     "frozen γ1=P(U1|B) columns; no refit, no decoder, "
                     "no DE, no L1 construction (packet §3)"),
            "mismatch_measurement": ("k = Σ_i 1[û1_i≠u1_i] measured from "
                                     "the same synthetic draw; measurement "
                                     "only, labeled not-a-disclosure"),
            "genie_ceiling": ("REMOVED for this arm (no D1 ceiling label; "
                              "O1/O1R/P0 remain genie ceilings)"),
        },
        "d_u1": {
            "rule": ("D-u1 = per-block Σ_i H(γ1(·|b_i)) bits — minimum "
                     "SW-style disclosure to resolve u1 from b "
                     "(Amendment 2026-09-21; replaces the frozen 5×k "
                     "per-block reading, which stays report-only)"),
            "gating": ("arm-mean f_super_conservative=(m·5+64+"
                       "mean(d_u1_bits))/852.544<=1.3 (mean-based; the "
                       "per-block distribution is REPORTED)"),
            "per_block_values": ("rows.json / block_accounting.csv column "
                                 "d_u1_bits (one measured value per "
                                 "completed block)"),
            "mean_bits": mean_d,
            "p50": du["p50"], "p90": du["p90"], "p99": du["p99"],
            "max": du["max"], "min": du["min"],
            "blocks": du["blocks"],
            "violating_blocks": violating_block_count(rows),
            "violating_blocks_note": ("report-only count of completed "
                                      "blocks with per-block "
                                      "f_super_conservative>1.3; the "
                                      "Amendment gates the ARM MEAN, not "
                                      "per-block values"),
            "f_super_conservative_mean": f_cons_mean,
            "f_super_du0_report": basis["f_super_du0_basis"],
            "f_super_5k_sensitivity": f5k,
            "u1_mismatches_mean": km["mean"],
            "u1_mismatches_max": km["max"],
            "h_l1_anchor_bits": L1_CONTENT_BITS,
            "pre_registered_observation": ("at mean D-u1 = 1024×H_L1 ≈ "
                                           "26.28 b: B202 ≈1.2906 ≤ 1.3 "
                                           "(headroom ~8.0 b) and B208 "
                                           "≈1.3258 > 1.3 (expected — "
                                           "B208 funds no L1 rows); "
                                           "pre-registered observation, "
                                           "not a claim (Amendment "
                                           "2026-09-21)"),
        },
        "de_cover": _de_cover_record(arm, de_label),
        "ledger": {"decodes": ledger_decodes,
                   "blocks_completed": blocks_completed},
        "blocks_completed": blocks_completed,
        "failures": failures,
        "fer_blocks": fer,
        "pass_bar": f"block FER<=5% (fails/{nb}<={bar})",
        "quarter_tally": quarter_tally(rows),
        "d_blind": basis["d_blind"],
        "d_blind_label": basis["d_blind_label"],
        "sensitivity": basis["sensitivity"],
        "headroom_line": basis["headroom_line"],
        "leak_bits": basis["leak_bits"],
        "f_super": basis["f_super_du0_basis"],
        "f_super_label": basis["f_super_du0_label"],
        "f_super_rule": basis["f_super_rule"],
        "f_super_5k_label": basis["f_super_5k_label"],
        "f_super_conservative_mean": f_cons_mean,
        "h_l1": basis["h_l1"],
        "h_full": basis["h_full"],
        "f_bar": ("arm-mean f_super_conservative=(m·5+64+mean(d_u1_bits))"
                  f"/852.544<={F_SUPER_MAX} (Amendment 2026-09-21; "
                  f"mean-based)"),
        "verdict": verdict,
        "partial": bool(partial),
        "next_block": int(next_block),
        "resume": {"continuations_used": len(wall_windows) - 1,
                   "max_continuations": 1},
        "wall_windows": list(wall_windows),
        "elapsed_s": float(elapsed_s),
        "n_rows": n,
        "resume_policy_note": ("B2E packet §6: checkpoint-per-block + at "
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
                      block_base: int = B2E_BLOCK_BASE,
                      n_blocks: int = B2E_N_BLOCKS,
                      construct_seed: int = B2E_CONSTRUCT_SEED) -> dict:
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
            or seeds.get("policy") != "literal-frozen (B2E packet §6; NOT derived)"
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
                    seed: int = B2E_CONSTRUCT_SEED,
                    trials: int = B2E_MAX_TRIALS) -> dict:
    """Pre-run construction gate (packet §2/X3): build the arm via
    ``construct_fn(arm, seed, trials)`` TWICE and require
    construct-twice-identical; assert four_cycles == 0 AND rank == m
    (GATED; mismatch halts STOP-BLOCKED pre-decode); min_girth is
    RECORDED as-measured, never gated (P0/R2-amendment precedent). The
    production ``construct_fn`` is ``construct_arm`` above, which
    delegates to the frozen O1 constructor on the paired A208/A202
    instance (byte-identical). Unknown arm refuses (rc=2). No alternate
    seeds; no tuning.
    """
    if arm not in ARMS:
        refuse(f"unknown arm {arm} (frozen: B208|B202 only)")
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
        refuse(f"{arm} four_cycles {fc} != 0 (STOP-BLOCKED; B2E packet "
               f"§2/X3; measured girth {girth})")
    if rank != m:
        refuse(f"{arm} rank {rank} != {m} (STOP-BLOCKED; B2E packet "
               f"§2/X3; measured girth {girth})")
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
            block_base: int = B2E_BLOCK_BASE,
            n_blocks: int = B2E_N_BLOCKS,
            construct_seed: int = B2E_CONSTRUCT_SEED,
            construct_trials: int = B2E_MAX_TRIALS) -> dict:
    """Run (or once-continue) the frozen 240-block B2E campaign under
    ``root``.

    One arm per invocation (B208|B202); paired block seeds shared across
    arms (2026095601+idx, ``o1_blk:`` stream). ``max_blocks`` is a
    PROBE-ONLY cap (timing integration; never a CLI flag, never part of
    any verdict). Without an injected ``decode_fn``, ``bundle`` is
    required (no silent production bind — the CLI binds ``--gamma``
    explicitly). Gate (a) fails/240 ≤ 12 with early-stop at the 13th
    fail; gate (b) arm-mean f_super_conservative ≤ 1.3 (Amendment
    2026-09-21). All writes stay under ``root``. No auto-relaunch: at
    most ONE explicit wall-partial ``--resume-from`` in a fresh window.
    """
    if arm not in ARMS:
        refuse(f"unknown arm {arm} (frozen: B208|B202 only)")
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
            return decode_block_map_u1(construction, seed, _b, B2E_N, m)
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
        # MAP-u1 decode-output contract (fail closed on a malformed row).
        du = out.get("d_u1_bits")
        km = out.get("u1_mismatches")
        if isinstance(du, bool) or not isinstance(du, (int, float,
                                                       np.floating)):
            refuse(f"decode output missing numeric d_u1_bits (block {k}; "
                   f"fail closed)")
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
            "u1_mismatches": int(km),
            "d_u1_bits": float(du),
            "d_blind": basis["d_blind"],
            "d_blind_label": basis["d_blind_label"],
            "leak_bits": basis["leak_bits"],
            "f_super_du0_report": basis["f_super_du0_basis"],
            "f_super_conservative": f_super_conservative(arm, float(du)),
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
    stats = d_u1_stats(rows)
    f_cons_mean = f_super_conservative(arm, float(stats["mean_bits"]))
    passed = (failures <= bar and f_cons_mean <= F_SUPER_MAX)
    return _flush("PASS" if passed else "FAIL", False, n_blocks)


def run_execution(root: str, arm: str,
                  resume_from: str | None = None,
                  gamma: str = GAMMA_DEFAULT,
                  source: str = SOURCE_DEFAULT,
                  bundle: dict[str, Any] | None = None,
                  de_label: str | None = None,
                  block_base: int = B2E_BLOCK_BASE,
                  n_blocks: int = B2E_N_BLOCKS,
                  construct_seed: int = B2E_CONSTRUCT_SEED,
                  construct_trials: int = B2E_MAX_TRIALS) -> int:
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
                      "f_super_du0": manifest["f_super"],
                      "f_super_conservative_mean": manifest[
                          "f_super_conservative_mean"],
                      "d_u1_mean_bits": manifest["d_u1"]["mean_bits"],
                      "u1_mismatches_mean": manifest["d_u1"][
                          "u1_mismatches_mean"],
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
    ap.add_argument("--block-base", type=int, default=B2E_BLOCK_BASE)
    ap.add_argument("--n-blocks", type=int, default=B2E_N_BLOCKS)
    ap.add_argument("--construct-seed", type=int,
                    default=B2E_CONSTRUCT_SEED)
    ap.add_argument("--construct-trials", type=int,
                    default=B2E_MAX_TRIALS)
    args = ap.parse_args(argv)
    # Dual-flag gate: refuse EVERYTHING else rc=2 BEFORE any root/contact.
    # There is no profile-only mode and no silent path.
    if not args.execute_real:
        refuse("refusing: --execute-real missing (rc2 pre-anything)")
    if not args.execution_authorized:
        refuse("refusing: --execution-authorized missing (rc2 pre-anything)")
    if args.arm not in ARMS:
        refuse(f"unknown arm {args.arm} (frozen: B208|B202 only)")
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
    # B2E has EXACTLY ONE frozen configuration: any deviation is a
    # science-input change → STOP (packet §6). The execute() parameters
    # exist for resume validation; the CLI cannot drift them.
    if args.construct_seed != B2E_CONSTRUCT_SEED:
        refuse(f"construct-seed must be the frozen {B2E_CONSTRUCT_SEED} "
               f"(got {args.construct_seed}; B2E packet §2 — any seed "
               f"change is a science-input change → STOP)")
    if args.construct_trials != B2E_MAX_TRIALS:
        refuse(f"construct-trials must be the frozen {B2E_MAX_TRIALS} "
               f"(got {args.construct_trials}; B2E packet §2 — any trials "
               f"change is a science-input change → STOP)")
    if args.block_base != B2E_BLOCK_BASE:
        refuse(f"block-base must be the frozen {B2E_BLOCK_BASE} "
               f"(got {args.block_base}; B2E packet §6 — any block-seed "
               f"change is a science-input change → STOP)")
    if args.n_blocks != B2E_N_BLOCKS:
        refuse(f"n-blocks must be the frozen {B2E_N_BLOCKS} "
               f"(got {args.n_blocks}; B2E packet §6 — any width change "
               f"is a science-input change → STOP)")
    root = args.resume_from or args.root
    if not root:
        refuse("root required (fresh additive workspace/b2e_<uuid>)")
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
