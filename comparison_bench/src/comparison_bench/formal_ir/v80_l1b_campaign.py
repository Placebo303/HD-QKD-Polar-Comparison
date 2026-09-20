"""V80 L1B real-L1 + combined-chain campaign executor (EXPLORE code — NOT execution).

Frozen contract: ``docs/research_cycles/V80-NBLDPC-JAN21/
L1B_EXPERIMENT_PACKET_20260920.md`` (G-L1B, frozen, NOT granted).
Execution needs a fresh explicit grant + Pre-EXECUTE; this module only
provides the executor + fake-testable mechanics. Synthetic draws from the
read-only 2M derived bundle only; no real/Jan-21 frames; no writes outside
the run root; never writes ``results/`` or ``outputs_comparison/``.

Two configs, two stages (packet §§1–3). Both configs total 208 rows
(leak 1104 bits, f_super=1104/852.544≈1.294947):
PRIMARY C6 (m1=6, L1 rate 0.994140625 + m2=202 P0-PASS L2) and SECONDARY
C8 (m1=8, rate 0.9921875 + m2=200 P0-PASS L2).
Stage A (L1-only FER) runs FIRST, per config; Stage B (combined chain)
runs only for Stage-A-passing configs, independently per config:
A6 PASS ⇒ B6 may run; A8 PASS ⇒ B8 may run. A FAIL ⇒ no Stage B for
that config. This per-config gating is documented here and carried in
every manifest (``stage_gate``); the executor never auto-proceeds.

E1 Construction: n=1024, GF(32), λ={2:1} (same family); FIXED
``peg_construct`` + ``make_rho`` (frozen v10_peg path, GF(32) labels),
construct seed 2026092001/trials 20, BOTH the L1 (m1) and L2 (m2) codes
at their m values per config (new m ⇒ disjoint outputs). Pins per leg
(amendment 2026-09-21, memo option (a)): m1 legs (1024,6)/(1024,8)
rank-full AND construct-twice-identical GATED (mismatch →
STOP-BLOCKED); four_cycles + min_girth RECORDED-not-gated as
covariates (dense-check regime: expected fc>0/girth 4). m2 legs
(1024,202)/(1024,200) fc==0 AND rank-full AND twice-identical GATED;
girth recorded. Dense-check flag carried (memo §2a: avg check degree
2048/6≈341 for m1=6, 2048/8=256 for m1=8).
E2 L1 decode wrapper (``decode_l1_block``): triple
``empirical_triple_sampler`` (s2c L251-285: b~p_b ``rng.choice(1024,
p=p_b)``; u1~g1[:,b]/sum; u2~g2; zero-mass→delta-at-0); Alice x1=u1;
Bob y1=(b>>5)&31 (``factor_layers`` v29 L269-273); rows=
``posterior_rows_l1``=p_u1_gb.T[b] (v26_channel L236-237, L1-only, no u1
conditioning — L1 decodes first); prior π(e)=rows[y⊕e] via
``center_rows_prior`` (s2c L319-331, XOR identity of v28 L189-197);
entrypoint ``decode_error_domain_posterior`` ONLY (v28 L155-186);
max_iter=300/streak 3; per-decode cap 300 s. L1 exact = û1==u1.
E3 Stage A block wrapper (``execute`` stage A): L1-only per block, one
block = one n=1024 L1 decode. Gates per config (AND): (a) fails/240≤12
(5% exact); (b) system f_super mapping 1.294947≤1.3 carried (total fixed
208 rows; L1 leak share 5×m1 bits = 30/40 b; 64-bit tag counted once at
system level). Early-stop at 13th fail → FAIL, retain partials. Per-60
quarter tally report-only. No rerun/no tuning.
E4 Stage B combined wrapper (``decode_combined_block``): decode L1 from
b → û1 (§E2 semantics); then L2 with û1 in place of genie-u1:
y2=b&31; rows2=``posterior_rows_l2(bundle,b,û1)`` (s2c L288-316,
conditioned on DECODED û1, NOT genie); XOR prior;
``decode_error_domain_posterior``, max_iter=300/streak 3. L1 x_hat None
⇒ L2 skipped, block fails (fail closed, recorded). System success =
BOTH layers exact (û1==u1 AND x̂==u2). Genie label RETIRED; label
``real-L1 chain``. Gates per config (AND): (a) system fails/240≤12;
(b) f_super 1.294947≤1.3 on measured-D_blind basis. Early-stop at 13th;
no rerun/no tuning.
E5 CLI: ``--stage A|B --config C6|C8`` (+ dual-flag gate
``--execute-real --execution-authorized`` refusing everything else rc=2
pre-anything; root prefix ``workspace/l1b_``; checkpoint-per-block;
≤1 wall-partial ``--resume-from``; wall ≤3600 s/window, per-decode
300 s, RSS <4 GiB). No DE-precheck runner lives here (packet §4 DE
precheck is OPTIONAL-with-label and runs as its own quick step outside
this executor; ``--de-label`` defaults ``exploratory``; gates unchanged).
E6 labels/manifest: stage explicit; config + m1/m2 + construct pins for
BOTH codes; f_L1=5m1/26.28 INFORMATIONAL ONLY (f_L1(6)≈1.142,
f_L1(8)≈1.522, never gated); blind-risk line (headroom 4.31 b; any
D_blind>4 bits fails gate (b)); paired note (blocks REUSED
2026095601+idx idx=0..239, stream ``o1_blk:{seed}`` — SAME 240 frames
as O1R/P0; NO independence claim L1B↔P0↔O1R); per-layer outcomes kept
for error-propagation accounting.

Reuse from ``v80_s2c_campaign``/``v80_o1_campaign`` (patterns only,
never their science): dual-flag gate, checkpoint manifest+rows
overwrite-in-place single writer, append-only ``wall_windows``,
explicit ``--resume-from`` with strict pre-decode validation,
early-stop at bar+1 block fails. SCAN trade-scan L1 arms (rework
memo v2 2026-09-21, section 2): Stage-A-only configs C12A (m1=12)
+ C16A (m1=16); m2 legs NOT constructed (pairing deferred to the
Stage B packet); L1-leg pins per the 2026-09-21 Amendment; Stage B
refused for Stage-A-only configs (rc=2 pre-decode); C6/C8 unchanged. Channel helpers
(``bind_empirical_bundle``, ``empirical_triple_sampler``,
``posterior_rows_l2``, ``center_rows_prior``) are reused READ-ONLY from
``v80_s2c_campaign`` — never re-implemented here.
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

from . import nonbinary_v10_common as common
from . import nonbinary_v10_fftqspa as fftqspa
from . import nonbinary_v10_peg as peg
from . import nonbinary_v26_mcde as _mcde  # noqa: F401 (read-only rho reuse; never edited)
from . import nonbinary_v28 as v28
from . import v80_s2_peg as s2
from . import v80_s2c_campaign as s2c
from .nonbinary_field import GF2mField

__all__ = [
    "L1B_CONSTRUCT_SEED", "L1B_MAX_TRIALS", "L1B_BLOCK_BASE",
    "L1B_N_BLOCKS", "L1B_N", "L1B_ROOT_PREFIX",
    "CONFIGS", "STAGES", "MAX_ITER",
    "H_L1_L1B", "H_FULL_L1B", "CONTENT_BITS", "L1_CONTENT_BITS",
    "D_BLIND", "F_SUPER_MAX",
    "WALL_CAP_S", "PER_DECODE_CAP_S", "RSS_CAP_GIB",
    "ROOT_PREFIX", "FORBIDDEN_ROOT_PARTS",
    "GAMMA_DEFAULT", "SOURCE_DEFAULT", "DE_LABELS",
    "Refusal", "refuse", "block_seed", "stream_seed",
    "fail_bar", "quarter_tally", "_allows_root",
    "construct_code", "posterior_rows_l1",
    "decode_l1_block", "decode_combined_block",
    "leak_basis", "block_accounting_csv",
    "run_execution", "execute", "main",
]

#: Frozen L1B construction seed (packet §1; both configs; new m values ⇒
#: disjoint outputs, O1 §2 / P0 §3 precedent).
L1B_CONSTRUCT_SEED = 2026092001
L1B_MAX_TRIALS = 20
#: Frozen literal block-seed base (packet §2; LITERAL, paired reuse with
#: O1R/P0 — SAME 240 frames; NO independence claim L1B↔P0↔O1R).
L1B_BLOCK_BASE = 2026095601
#: Frozen campaign width (packet §§2–3): 240 blocks = 240 decodes/arm.
L1B_N_BLOCKS = 240
#: Frozen code length (packet §1): n=1024 GF(32) symbols/block.
L1B_N = 1024
#: Fresh additive L1B run-root prefix (packet §6: workspace/l1b_<uuid8>).
L1B_ROOT_PREFIX = "workspace/l1b_"
#: Frozen configs (packet §1; both total 208 rows ⇒ leak 1104,
#: f_super≈1.294947). L1 leak share 5×m1 bits (30/40 b). SCAN
#: Stage-A-only configs (rework memo v2 §2): m1=12/16, m2 NOT
#: constructed (None; pairing deferred to the Stage B packet); the
#: frozen total-208 budget line is carried as the system mapping.
CONFIGS: dict[str, dict[str, Any]] = {
    "C6": {"m1": 6, "m2": 202, "lambda": {2: 1.0},
           "l1_rate": 1.0 - 6 / 1024,
           "role": "PRIMARY (m1=6/m2=202 P0-PASS L2)"},
    "C8": {"m1": 8, "m2": 200, "lambda": {2: 1.0},
           "l1_rate": 1.0 - 8 / 1024,
           "role": "SECONDARY (m1=8/m2=200 P0-PASS L2)"},
    "C12A": {"m1": 12, "m2": None, "lambda": {2: 1.0},
             "l1_rate": 1.0 - 12 / 1024, "stage_a_only": True,
             "role": "SCAN Stage-A-only (m1=12/deg~171; "
                     "m2 pairing deferred to Stage B packet)"},
    "C16A": {"m1": 16, "m2": None, "lambda": {2: 1.0},
             "l1_rate": 1.0 - 16 / 1024, "stage_a_only": True,
             "role": "SCAN Stage-A-only (m1=16/deg128; "
                     "m2 pairing deferred to Stage B packet)"},
}
#: Frozen stages (packet §§2–3): A = L1-only (runs FIRST, gates B);
#: B = combined chain (passing configs only).
STAGES = ("A", "B")
#: Frozen decoder cap (packet §2): max_iter=300, streak default (3).
MAX_ITER = s2.MAX_ITER
#: Frozen L1 entropy anchor H_L1=0.02566205 (S1 readiness; packet §1).
H_L1_L1B = 0.02566205
#: Frozen full-content anchor (S2/P0 basis): H_full=0.83256272.
H_FULL_L1B = s2.H_FULL_ANCHOR
#: Content basis: 1024 * H_full = 852.544 bits (packet §1).
CONTENT_BITS = L1B_N * H_FULL_L1B
#: L1 content: 1024 * H_L1 = 26.28 bits (packet §1).
L1_CONTENT_BITS = L1B_N * H_L1_L1B
#: D_blind = 0 MEASURED placeholder (NEVER-ASSUME-ZERO label on records).
D_BLIND = 0.0
#: Frozen f_super bar (packet §§2–3, AND-gated with fails/240≤12).
F_SUPER_MAX = 1.3
#: Frozen caps (packet §6): single window 3600 s; per-decode 300 s; 4 GiB.
WALL_CAP_S = 3600
PER_DECODE_CAP_S = 300
RSS_CAP_GIB = 4
#: Fresh additive run-root prefix (packet §6).
ROOT_PREFIX = L1B_ROOT_PREFIX
#: Roots the executor never writes under.
FORBIDDEN_ROOT_PARTS = ("results", "outputs_comparison")
#: Read-only derived bundle (packet §2): gamma file + p_b sidecar sibling
#: (same files as S2c/O1; binding helper reused read-only from s2c).
GAMMA_DEFAULT = s2c.GAMMA_DEFAULT
#: Worst-source anchor (packet §2); never auto-merge sources.
SOURCE_DEFAULT = s2c.SOURCE_DEFAULT
#: Allowed DE-cover labels threading into the campaign manifest (packet
#: §4: DE precheck OPTIONAL-with-label; Stage A proceeds regardless).
DE_LABELS = ("covered", "exploratory")


class Refusal(SystemExit):
    """rc=2 pre-write refusal (unauthorized / invalid / gate-blocked)."""


def refuse(reason: str) -> "Any":
    print(f"L1B-REFUSAL rc=2: {reason}", file=sys.stderr)
    raise Refusal(2)


def block_seed(config: str, idx: int, base: int | None = None) -> int:
    """Frozen literal block seed: base+idx (packet §2).

    Default base is the frozen L1B literal 2026095601, idx=0..239
    (paired reuse with O1R/P0; NO independence claim). Unknown config
    refuses (fail closed, rc=2).
    """
    if config not in CONFIGS:
        refuse(f"unknown config {config} (frozen: C6|C8|C12A|C16A only)")
    b = L1B_BLOCK_BASE if base is None else base
    if isinstance(b, bool) or not isinstance(b, int):
        refuse("block base must be an integer literal")
    return int(b) + int(idx)


def fail_bar(n_blocks: int) -> int:
    """Derived pass bar: floor(n_blocks x 0.05) (O1R packet §5/D2).

    240 -> 12. Early-stop fires at bar+1 (= 13th) cumulative fail.
    """
    return (int(n_blocks) * 5) // 100


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


def stream_seed(seed: int) -> int:
    """Frozen stream derivation: ``common.v10_seed(f"o1_blk:{seed}")``.

    SAME ``o1_blk:`` domain as O1R/P0 (paired reuse; byte-identical
    triple path ⇒ (b,u1) marginal identical).
    """
    return common.v10_seed(f"o1_blk:{int(seed)}")


def construct_code(m: int, seed: int = L1B_CONSTRUCT_SEED,
                   max_trials: int = L1B_MAX_TRIALS) -> dict[str, Any]:
    """FIXED single-code constructor (packet §1/E1): ``peg_construct`` +
    ``make_rho`` + ``_reconcile_check_counts`` (inside ``peg_construct``),
    GF(32) labels, n=1024/m given. No re-seed; no tuning. Pure in-memory;
    no disk writes."""
    if isinstance(m, bool) or not isinstance(m, int) or m < 1:
        refuse("construct m must be a positive int")
    field = GF2mField.create(s2.Q)
    lam = {2: 1.0}
    rho = _mcde.make_rho(1.0 - m / L1B_N, lam)
    result = peg.peg_construct(L1B_N, m, lam, rho, int(seed),
                               max_trials=int(max_trials), field=field)
    result["family"] = "peg-irregular"
    s2.refuse_three_shift_cyclic({"family": result["family"]})
    result["lambda_edge"] = dict(lam)
    result["rho_edge"] = {int(k): float(v) for k, v in rho.items()}
    return result


def posterior_rows_l1(bundle: dict[str, Any], b_vec: Any) -> np.ndarray:
    """L1 rows_i = P(U1|B=b_i) (``posterior_rows`` v26 L236-237 EXACT).

    ``p_u1_gb.T[b]`` with NO u1 conditioning — L1 decodes first (memo
    §2c). Here g1 IS P(U1|B) (colsums == 1, bound at bind); no
    zero-mass gate applies beyond bind validation.
    """
    g1 = np.asarray(bundle["g1"], dtype=np.float64)
    b = np.asarray(b_vec, dtype=np.int64)
    if b.ndim != 1:
        refuse("posterior L1 rows need 1-D b")
    if g1.shape != (32, 1024):
        refuse(f"L1 g1 shape {g1.shape} != (32, 1024)")
    for bb in b.tolist():
        if not 0 <= int(bb) < 1024:
            refuse("posterior L1 rows symbol out of domain")
    return np.asarray(g1.T[b], dtype=np.float64)


def decode_l1_block(construction_m1: dict[str, Any], seed: int,
                    bundle: dict[str, Any], n: int,
                    m1: int) -> dict[str, Any]:
    """One L1 empirical-channel block (packet §2/E2): triple draw on the
    ``o1_blk:{seed}`` stream; Alice x1=u1; Bob y1=(b>>5)&31; L1-only rows
    (no u1 conditioning); centered (n,32) prior into
    ``decode_error_domain_posterior`` (NEVER the scalar-p
    ``decode_error_domain``); max_iter=300, streak default. Returns the
    raw kernel verdict + L1 exact-match flag (``l1_exact is True``;
    ``exact_match`` mirrors it for Stage A gating). Fail-closed wiring
    guard: (n, m1) must match the construction under test.
    """
    if isinstance(seed, bool) or not isinstance(seed, int):
        refuse("block seed must be an integer")
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        refuse("block n must be a positive int")
    if isinstance(m1, bool) or not isinstance(m1, int) or m1 < 1:
        refuse("block m1 must be a positive int")
    if (construction_m1.get("n") != int(n)
            or construction_m1.get("m") != int(m1)):
        refuse(f"L1 construction (n, m) mismatch: got "
               f"({construction_m1.get('n')}, {construction_m1.get('m')}) "
               f"for block ({int(n)}, {int(m1)})")
    field = GF2mField.create(s2.Q)
    dense = peg.sparse_to_dense(construction_m1["triples"], int(n),
                                int(m1), field)
    rng = np.random.default_rng(stream_seed(int(seed)))
    b, u1, _u2 = s2c.empirical_triple_sampler(bundle, int(n), rng)
    x1 = np.asarray(u1, dtype=np.int64)  # Alice L1 vector
    y1 = np.asarray((b >> 5) & 31, dtype=np.int64)  # Bob L1 half (bits 9..5)
    s_x = fftqspa.syndrome_of(field, dense, x1.tolist())
    rows = posterior_rows_l1(bundle, b)  # L1-only; no u1 conditioning
    prior = s2c.center_rows_prior(rows, y1)
    result = v28.decode_error_domain_posterior(field, y1.tolist(), dense,
                                               s_x, prior, MAX_ITER)
    x_hat = result.get("x_hat")
    l1_exact = (bool(np.array_equal(np.asarray(x_hat), x1))
                if x_hat is not None else False)
    return {
        "status": result.get("status"),
        "iterations": result.get("iterations"),
        "reconstruction_ok": bool(result.get("reconstruction_ok", False)),
        "l1_exact": l1_exact,
        "exact_match": l1_exact,
        "seed": int(seed),
        "max_iter": int(MAX_ITER),
        "stage": "A",
        "l1_conditioning": "real L1 (no genie; L1 decodes first)",
    }


def decode_combined_block(construction_m1: dict[str, Any],
                          construction_m2: dict[str, Any], seed: int,
                          bundle: dict[str, Any], n: int,
                          m1: int, m2: int) -> dict[str, Any]:
    """One combined-chain block (packet §3/E4): ONE triple draw per block;
    decode L1 from b → û1 (E2 semantics); then L2 with û1 in place of
    genie-u1: y2=b&31; rows2=``posterior_rows_l2(bundle,b,û1)`` (DECODED
    û1, NOT genie); XOR prior; ``decode_error_domain_posterior``,
    max_iter=300/streak 3 both layers. L1 x_hat None ⇒ L2 skipped, block
    fails (fail closed, recorded). System success = BOTH layers exact.
    Genie label RETIRED; label ``real-L1 chain``.
    """
    if isinstance(seed, bool) or not isinstance(seed, int):
        refuse("block seed must be an integer")
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        refuse("block n must be a positive int")
    for tag, con, mm in (("m1", construction_m1, m1),
                         ("m2", construction_m2, m2)):
        if isinstance(mm, bool) or not isinstance(mm, int) or mm < 1:
            refuse(f"block {tag} must be a positive int")
        if con.get("n") != int(n) or con.get("m") != int(mm):
            refuse(f"L2-{tag} construction (n, m) mismatch: got "
                   f"({con.get('n')}, {con.get('m')}) "
                   f"for block ({int(n)}, {int(mm)})")
    field = GF2mField.create(s2.Q)
    dense1 = peg.sparse_to_dense(construction_m1["triples"], int(n),
                                 int(m1), field)
    dense2 = peg.sparse_to_dense(construction_m2["triples"], int(n),
                                 int(m2), field)
    rng = np.random.default_rng(stream_seed(int(seed)))
    b, u1, u2 = s2c.empirical_triple_sampler(bundle, int(n), rng)
    # L1 leg (E2 semantics, shared triple).
    x1 = np.asarray(u1, dtype=np.int64)
    y1 = np.asarray((b >> 5) & 31, dtype=np.int64)
    s1 = fftqspa.syndrome_of(field, dense1, x1.tolist())
    rows1 = posterior_rows_l1(bundle, b)
    prior1 = s2c.center_rows_prior(rows1, y1)
    res1 = v28.decode_error_domain_posterior(field, y1.tolist(), dense1,
                                             s1, prior1, MAX_ITER)
    u1_hat = res1.get("x_hat")
    l1_exact = (bool(np.array_equal(np.asarray(u1_hat), x1))
                if u1_hat is not None else False)
    if u1_hat is None:
        return {
            "status": res1.get("status"),
            "iterations": res1.get("iterations"),
            "reconstruction_ok": False,
            "l1_status": res1.get("status"),
            "l1_iterations": res1.get("iterations"),
            "l1_exact": False,
            "l2_exact": False,
            "l2_skipped": True,
            "exact_match": False,
            "seed": int(seed),
            "max_iter": int(MAX_ITER),
            "stage": "B",
            "chain": "real-L1 chain (genie retired)",
        }
    # L2 leg conditioned on DECODED û1 (NOT genie).
    x2 = np.asarray(u2, dtype=np.int64)
    y2 = np.asarray(b & 31, dtype=np.int64)  # Bob L2 half (bits 4..0)
    s2syn = fftqspa.syndrome_of(field, dense2, x2.tolist())
    rows2 = s2c.posterior_rows_l2(bundle, b, np.asarray(u1_hat))
    prior2 = s2c.center_rows_prior(rows2, y2)
    res2 = v28.decode_error_domain_posterior(field, y2.tolist(), dense2,
                                             s2syn, prior2, MAX_ITER)
    x2_hat = res2.get("x_hat")
    l2_exact = (bool(np.array_equal(np.asarray(x2_hat), x2))
                if x2_hat is not None else False)
    system = bool(l1_exact and l2_exact)
    return {
        "status": res2.get("status"),
        "iterations": res2.get("iterations"),
        "reconstruction_ok": bool(l1_exact and res2.get("reconstruction_ok",
                                                         False)),
        "l1_status": res1.get("status"),
        "l1_iterations": res1.get("iterations"),
        "l1_exact": bool(l1_exact),
        "l2_exact": bool(l2_exact),
        "l2_skipped": False,
        "exact_match": system,
        "seed": int(seed),
        "max_iter": int(MAX_ITER),
        "stage": "B",
        "chain": "real-L1 chain (genie retired)",
    }


def leak_basis(config: str) -> dict[str, Any]:
    """Frozen L1B f accounting (packet §1; per-config m1+m2=208).

    System budget mapping: f_super=(208·5+64)/(1024·H_full)
    =1104/852.544≈1.294947 BUDGET MAPPING, not measured efficiency
    (BOTH configs; headroom 1108.31−1104=4.31 b UNCHANGED — TIGHT; any
    D_blind>4 bits fails gate (b)). L1 leak share 5×m1 bits (30/40 b;
    64-bit tag counted once at system level). Layer-local f_L1=(m1·5)/
    (1024·H_L1) INFORMATIONAL ONLY — never gated (f_L1(6)≈1.142,
    f_L1(8)≈1.522).
    """
    if config not in CONFIGS:
        refuse(f"unknown config {config} (frozen: C6|C8|C12A|C16A only)")
    m1 = int(CONFIGS[config]["m1"])
    if CONFIGS[config].get("stage_a_only"):
        # SCAN Stage-A-only (rework memo v2 section 2): m2 pairing
        # deferred to the Stage B packet; the system mapping is carried
        # on the frozen total-208 budget line (both memo splits total
        # 208 rows ⇒ leak 1104, same as C6/C8).
        return _leak_basis_stage_a_only(config, m1)
    m2 = int(CONFIGS[config]["m2"])
    m_total = m1 + m2
    leak = float(m_total * 5 + 64)
    f_super = leak / CONTENT_BITS
    f_l1 = (5 * m1) / L1_CONTENT_BITS
    return {
        "config": config,
        "m1": m1,
        "m2": m2,
        "m_total": m_total,
        "leak_bits": leak,
        "l1_leak_bits": float(5 * m1),
        "content_bits": CONTENT_BITS,
        "f_super_basis": f_super,
        "f_super_label": ("System budget mapping: "
                          "f_super=(m_total·5+64)/(1024·H_full) "
                          f"=({m_total}·5+64)/852.544≈{f_super:.6f} "
                          "(H_full=0.83256272). "
                          "BUDGET MAPPING, not measured efficiency "
                          "(L1B packet §1)"),
        "f_L1_basis": f_l1,
        "f_L1_label": ("Layer-local reported efficiency: "
                       f"f_L1=(m1·5)/(1024·H_L1)=({m1}·5)/(1024×0.02566205)"
                       f"≈{f_l1:.6f}. INFORMATIONAL ONLY — never gated "
                       "(L1B packet §1)"),
        "h_l1": H_L1_L1B,
        "h_full": H_FULL_L1B,
        "d_blind": D_BLIND,
        "d_blind_label": ("MEASURED zero: no blind/puncturing rounds exist "
                          "in the campaign path — NEVER assume zero "
                          "in a claim (L1B packet §9)"),
        "sensitivity": ("Δf = D_blind/852.544, i.e. each 16 bits "
                        "≈ +0.019"),
        "blind_risk": ("Headroom 1108.31−1104=4.31 b UNCHANGED (total "
                       "fixed 208 rows); blind surcharge still open — "
                       "any D_blind>4 bits fails gate (b) "
                       "(L1B packet §9)"),
    }


def _leak_basis_stage_a_only(config: str, m1: int) -> dict[str, Any]:
    """System mapping for a SCAN Stage-A-only config (C12A/C16A).

    Same record shape as ``leak_basis``: the f_super mapping is carried
    on the frozen total-208 budget line (leak 1104 bits,
    f_super=1104/852.544, m2-deferred note) so the AND-gate arithmetic
    stays wired; the L1 leak share is 5*m1 bits (60/80 b) and f_L1 is
    INFORMATIONAL ONLY, never gated.
    """
    leak = 1104.0
    f_super = leak / CONTENT_BITS
    f_l1 = (5 * m1) / L1_CONTENT_BITS
    return {
        "config": config,
        "m1": m1,
        "m2": None,
        "m_total": 208,
        "leak_bits": leak,
        "l1_leak_bits": float(5 * m1),
        "content_bits": CONTENT_BITS,
        "f_super_basis": f_super,
        "f_super_label": ("System budget mapping carried on the frozen "
                          "total-208 line: f_super=(208·5+64)/(1024·H_full) "
                          f"=1104/852.544≈{f_super:.6f} "
                          "(H_full=0.83256272). m2 pairing DEFERRED to the "
                          "Stage B packet (Stage-A-only config). "
                          "BUDGET MAPPING, not measured efficiency"),
        "f_L1_basis": f_l1,
        "f_L1_label": ("Layer-local reported efficiency: "
                       f"f_L1=(m1·5)/(1024·H_L1)=({m1}·5)/(1024×0.02566205)"
                       f"≈{f_l1:.6f}. INFORMATIONAL ONLY — never gated "),
        "h_l1": H_L1_L1B,
        "h_full": H_FULL_L1B,
        "d_blind": D_BLIND,
        "d_blind_label": ("MEASURED zero: no blind/puncturing rounds exist "
                          "in the campaign path — NEVER assume zero "
                          "in a claim (L1B packet §9)"),
        "sensitivity": ("Δf = D_blind/852.544, i.e. each 16 bits "
                        "≈ +0.019"),
        "blind_risk": ("Headroom 1108.31−1104=4.31 b on the frozen "
                       "total-208 line (m2 pairing deferred; Stage-A-only "
                       "config); blind surcharge still open — "
                       "any D_blind>4 bits fails gate (b)"),
    }


def block_accounting_csv(rows: list[dict]) -> str:
    """Per-block accounting table (packet §9 deliverable)."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["block", "seed", "l1_exact", "l2_exact", "exact_match",
                "status", "iterations", "wall_s", "d_blind", "leak_bits",
                "f_super"])
    for r in rows:
        if r.get("status") in ("error", "overrun"):
            w.writerow([r.get("block"), "", "", "", "", r.get("status"),
                        "", "", "", "", ""])
            continue
        w.writerow([r.get("block"), r.get("seed"), r.get("l1_exact"),
                    ("" if r.get("l2_exact") is None else r.get("l2_exact")),
                    r.get("exact_match"), r.get("status"),
                    r.get("iterations"), r.get("wall_s"),
                    r.get("d_blind"), r.get("leak_bits"),
                    r.get("f_super")])
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
    """Fresh additive prefix: L1B ``workspace/l1b_<uuid>`` (packet §6)."""
    return root.startswith(ROOT_PREFIX)


def _check_root(root: str) -> None:
    if not root:
        refuse("root required (fresh additive workspace/l1b_<uuid>)")
    parts = Path(root).parts
    if any(p in FORBIDDEN_ROOT_PARTS for p in parts):
        refuse(f"root under forbidden tree (results/outputs_comparison): {root}")


def _de_cover_record(config: str, de_label: str | None) -> dict[str, Any]:
    label = de_label or "exploratory"
    if label not in DE_LABELS:
        refuse(f"unknown de-label {label} (frozen: covered|exploratory only)")
    if CONFIGS[config].get("stage_a_only"):
        rate = 1.0 - int(CONFIGS[config]["m1"]) / L1B_N
        arm_note = (f"{config} L1 rate {rate:.5f} is far off the S1 L2 "
                    "grid; DE informative-not-decisive; the 240-block "
                    "empirical FER is the gate (SCAN Stage-A-only: "
                    "exploratory, no DE run)")
    else:
        arm_note = (f"{config} L1 rate ≈0.994 is far off the S1 L2 "
                    "grid ⇒ DE informative-not-decisive; the 240-block "
                    "empirical FER is the gate (P0 precedent: "
                    "exploratory, no DE run)")
    return {"label": label,
            "label_source": ("explicit --de-label" if de_label
                             else "default 'exploratory' (DE precheck is "
                                   "OPTIONAL-with-label; Stage A proceeds "
                                   "regardless; gates unchanged; "
                                   "L1B packet §4)"),
            "arm_note": arm_note}


def _build_manifest(*, stage: str, config: str, constructions: dict,
                    rows: list[dict], failures: int, blocks_completed: int,
                    verdict: str, partial: bool, next_block: int,
                    wall_windows: list[dict], ledger_decodes: int,
                    elapsed_s: float, de_label: str | None,
                    block_base: int | None = None,
                    n_blocks: int | None = None) -> dict:
    basis = leak_basis(config)
    spec = CONFIGS[config]
    n = len(rows)
    fer = (failures / n) if n else None
    bb = L1B_BLOCK_BASE if block_base is None else int(block_base)
    nb = L1B_N_BLOCKS if n_blocks is None else int(n_blocks)
    bar = fail_bar(nb)
    c1 = constructions["m1"]
    c2 = constructions.get("m2")  # None for SCAN Stage-A-only configs
    if stage == "A":
        wiring = ("y1_i=(b_i>>5)&31 (factor_layers v29 L269-273); "
                  "rows_i=P(U1|B=b_i) (posterior_rows v26 L236-237, "
                  "L1-only, NO u1 conditioning — L1 decodes first); "
                  "pi_i(e)=rows_i[y1_i XOR e] (center_rows_prior, "
                  "GF32 char-2 add=XOR, v28 L189-197)")
        conditioning = ("Stage A L1-only (packet §2): Alice x1=u1; "
                        "L1 exact = û1==u1. No L2 decode; no genie.")
    else:
        wiring = ("L1 leg as Stage A → û1; then L2 with û1 in place of "
                  "genie-u1: y2_i=b_i&31; rows2_i=gamma_2(.|b_i,û1_i) "
                  "(posterior_rows_l2 s2c L288-316, DECODED û1, NOT "
                  "genie); pi_i(e)=rows2_i[y2_i XOR e]; "
                  "decode_error_domain_posterior both layers, "
                  "max_iter=300/streak 3")
        conditioning = ("real-L1 chain (packet §3): system success = "
                        "BOTH layers exact (û1==u1 AND x̂==u2). "
                        "Genie label RETIRED.")
    return {
        "campaign": "L1B",
        "stage": stage,
        "stage_label": ("Stage A L1-only FER (packet §2; runs FIRST, "
                        "gates Stage B)" if stage == "A"
                        else "Stage B combined chain (packet §3; "
                             "passing configs only; real-L1 chain)"),
        "stage_gate": ("Per-config (packet §2): A6 PASS ⇒ B6 may run; "
                       "A8 PASS ⇒ B8 may run — independently. A FAIL ⇒ "
                       "no Stage B for that config (⇒ rework memo). "
                       "This executor never auto-proceeds; B needs an A "
                       "PASS record + fresh B grant."),
        "config": config,
        "config_role": spec["role"],
        "n_blocks": nb,
        "fail_bar": bar,
        "single_code": ("acceptance unit = ONE BLOCK = one n=1024 decode "
                        "with exact_match is True (Stage A: L1 exact; "
                        "Stage B: BOTH layers exact). No frames, no "
                        "group-of-4 rule (block≠S2c-group, not directly "
                        "comparable to S2c group FER)"),
        "construct": {
            "seed": c1.get("construct_seed"),
            "max_trials": c1.get("construct_trials"),
            "n": L1B_N,
            "m1": {"m": c1.get("m"),
                   "four_cycles": c1.get("four_cycles"),
                   "min_girth": c1.get("min_girth"),
                   "rank": c1.get("rank"),
                   "sockets": c1.get("total_sockets"),
                   "parity": c1.get("parallel_edges")},
            "m2": ({"m": c2.get("m"),
                    "four_cycles": c2.get("four_cycles"),
                    "min_girth": c2.get("min_girth"),
                    "rank": c2.get("rank"),
                    "sockets": c2.get("total_sockets"),
                    "parity": c2.get("parallel_edges")}
                   if c2 is not None else
                   {"m": None,
                    "note": ("NOT CONSTRUCTED (SCAN Stage-A-only config; "
                             "m2 pairing deferred to the Stage B packet)")}),
            "lambda": {str(k): float(v)
                       for k, v in spec["lambda"].items()},
            "family": c1.get("family"),
            "pins": (f"m1 (m={spec['m1']}): rank-full + "
                     f"construct-twice-identical GATED; fc-measured-"
                     f"{c1.get('four_cycles')}/girth-measured-"
                     f"{c1.get('min_girth')}-recorded-not-gated "
                     f"(amendment 2026-09-21 dense-check); m2 "
                     f"(m={spec['m2']}): fc=0/rank-full GATED; girth-"
                     f"measured-{c2.get('min_girth')}-recorded-not-gated; "
                     f"constructor seed {c1.get('construct_seed')}/"
                     f"trials {c1.get('construct_trials')}; "
                     f"construct-twice-identical required; mismatch on "
                     f"gated fields halts STOP-BLOCKED; "
                     f"dense-check flag: avg check deg "
                     f"{2048 // spec['m1']}/{2048 // spec['m2']})"
                     if c2 is not None else
                     f"m1 (m={spec['m1']}): rank-full + "
                     f"construct-twice-identical GATED; fc-measured-"
                     f"{c1.get('four_cycles')}/girth-measured-"
                     f"{c1.get('min_girth')}-recorded-not-gated "
                     f"(amendment 2026-09-21 dense-check); m2 NOT "
                     f"CONSTRUCTED (SCAN Stage-A-only config; pairing "
                     f"deferred to the Stage B packet); "
                     f"constructor seed {c1.get('construct_seed')}/"
                     f"trials {c1.get('construct_trials')}; "
                     f"construct-twice-identical required; mismatch on "
                     f"gated fields halts STOP-BLOCKED; "
                     f"dense-check flag: avg check deg "
                     f"{2048 // spec['m1']}/-"),
        },
        "seeds": {
            "policy": "literal-frozen (L1B packet §2; NOT derived)",
            "block_base": bb,
            "block_rule": (f"base+idx, idx=0..{nb - 1} "
                           f"(block k → idx=k)"),
            "n_blocks": nb,
            "fail_bar": bar,
            "stream": "common.v10_seed(f\"o1_blk:{seed}\") (paired across "
                      "configs/stages; distinct domain from S2c s2c_emp:)",
            "paired_note": ("Blocks REUSED paired with O1R/P0: literal "
                            "2026095601+idx idx=0..239, stream "
                            "o1_blk:{seed} — SAME 240 frames (byte-identical "
                            "triple path ⇒ (b,u1) marginal identical; "
                            "paired L1-vs-L2 contrast on same frames); "
                            "prior use declared (O1R/P0 roots+docs = "
                            "expected hits); NO independence claim "
                            "L1B↔P0↔O1R (L1B packet §2)"),
        },
        "channel": {
            "source": SOURCE_DEFAULT,
            "bundle": "gamma_f03.npz keys 2M_gamma1_L1 (32,1024) + "
                      "2M_gamma2_L2condU1 (32,32,1024) + sidecar "
                      "gamma_f03_pb.npz key 2M_p_b (1024,) normalized "
                      "sum=1±1e-9 else refuse (read-only, never refit)",
            "sampler": ("per-symbol triple b~p_b; u1~g1[:,b]; u2~g2[u1,:,b]; "
                        "zero-mass→delta-at-0; frozen make_centered_sampler "
                        "L2 order; i.i.d. ×1024/block; Alice (x1=u1, x2=u2), "
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
            "wiring": wiring,
            "l1_conditioning": conditioning,
            "channel": "empirical 2M triple sampler at n=1024 (packet §2)",
        },
        "de_cover": _de_cover_record(config, de_label),
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
        "blind_risk": basis["blind_risk"],
        "leak_bits": basis["leak_bits"],
        "f_super": basis["f_super_basis"],
        "f_super_label": basis["f_super_label"],
        "f_L1": basis["f_L1_basis"],
        "f_L1_label": basis["f_L1_label"],
        "h_l1": basis["h_l1"],
        "h_full": basis["h_full"],
        "f_bar": f"f_super<={F_SUPER_MAX}",
        "verdict": verdict,
        "partial": bool(partial),
        "next_block": int(next_block),
        "resume": {"continuations_used": len(wall_windows) - 1,
                   "max_continuations": 1},
        "wall_windows": list(wall_windows),
        "elapsed_s": float(elapsed_s),
        "n_rows": n,
        "resume_policy_note": ("L1B packet §6: checkpoint-per-block + at "
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


def _validate_partial(manifest: dict, rows: list, stage: str,
                      config: str,
                      block_base: int = L1B_BLOCK_BASE,
                      n_blocks: int = L1B_N_BLOCKS,
                      construct_seed: int = L1B_CONSTRUCT_SEED) -> dict:
    """Fail-closed partial validation BEFORE any decode (zero decodes on
    refuse). Checks: stage+config match, frozen seeds/budgets for THIS
    run's (block_base, n_blocks, construct_seed), ledger internal
    consistency (decodes == blocks, rows contiguous 0..k-1), no final
    verdict (completion is not resumable), at most-one continuation
    unused (exactly one wall window so far)."""
    if not isinstance(manifest, dict):
        refuse("partial manifest not a dict")
    if not isinstance(rows, list):
        refuse("partial rows not a list")
    if manifest.get("campaign") != "L1B":
        refuse("partial campaign mismatch (fail closed)")
    if manifest.get("stage") != stage:
        refuse("partial stage mismatch (fail closed)")
    if manifest.get("config") != config:
        refuse("partial config mismatch (fail closed)")
    seeds = manifest.get("seeds", {})
    if (not isinstance(seeds, dict)
            or seeds.get("policy") != "literal-frozen (L1B packet §2; NOT derived)"
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


def _construct_gate(config: str, construct_fn: Callable,
                    seed: int = L1B_CONSTRUCT_SEED,
                    trials: int = L1B_MAX_TRIALS) -> dict:
    """Pre-run construction gate (packet §1/E1 + amendment 2026-09-21):

    BOTH the L1 (m1) and L2 (m2) codes at their m values for this
    config. Per leg (amendment, memo option (a)): m1 legs
    (1024,6)/(1024,8) rank-full AND construct-twice-identical GATED;
    four_cycles + min_girth RECORDED-not-gated as covariates
    (dense-check regime: expected fc>0/girth 4, memo 20260921 §1). m2
    legs (1024,202)/(1024,200) four_cycles==0 AND rank-full AND
    construct-twice-identical GATED; min_girth RECORDED-not-gated
    (P0/R2 precedent). Mismatch on a GATED field halts STOP-BLOCKED;
    unknown config refuses (rc=2). No alternate seeds; no tuning.
    SCAN Stage-A-only configs (C12A/C16A, rework memo v2 section 2):
    the m1 leg ONLY is constructed (m2 is None — pairing deferred to
    the Stage B packet); the m1 leg follows the same Amendment rule
    (rank-full + twice-identical GATED; fc/girth RECORDED).
    ``construct_fn`` convention is ``(m, seed, max_trials)``, mirroring
    ``construct_code``.
    """
    if config not in CONFIGS:
        refuse(f"unknown config {config} (frozen: C6|C8|C12A|C16A only)")
    if isinstance(seed, bool) or not isinstance(seed, int):
        refuse("construct seed must be an integer")
    if isinstance(trials, bool) or not isinstance(trials, int) or trials < 1:
        refuse("construct trials must be a positive int")
    out: dict[str, Any] = {}
    legs = (("m1",) if CONFIGS[config].get("stage_a_only")
            else ("m1", "m2"))
    for tag in legs:
        m = int(CONFIGS[config][tag])
        try:
            code_a = construct_fn(m, seed, trials)
            code_b = construct_fn(m, seed, trials)
        except Refusal:
            raise
        except Exception as exc:  # noqa: BLE001 — fail closed pre-decode
            refuse(f"construction failed ({config}/{tag} m={m}): "
                   f"{type(exc).__name__}: {exc}")
        ta, tb = code_a.get("triples"), code_b.get("triples")
        if ta is not None or tb is not None:
            try:
                sa = sorted(tuple(map(int, t)) for t in ta)
                sb = sorted(tuple(map(int, t)) for t in tb)
            except Exception:  # noqa: BLE001
                refuse(f"construction triples corrupt ({config}/{tag}; "
                       f"STOP-BLOCKED)")
            if sa != sb:
                refuse(f"construct-twice mismatch ({config}/{tag} m={m}; "
                       f"not identical; STOP-BLOCKED)")
        if code_a.get("status", "ok") != "ok":
            refuse(f"construction {code_a.get('status')} ({config}/{tag}; "
                   f"STOP-BLOCKED)")
        try:
            fc = int(code_a.get("four_cycles"))
            girth = int(code_a.get("min_girth"))
            rank = int(code_a.get("rank"))
        except Exception:  # noqa: BLE001
            refuse(f"construction missing fc/girth/rank pins "
                   f"({config}/{tag}; STOP-BLOCKED)")
        if tag == "m1":
            # Amendment 2026-09-21 (memo option (a)): dense-check regime
            # (1024,6)/(1024,8) — fc + girth RECORDED-not-gated as
            # covariates (expected fc>0/girth 4); rank-full + twice
            # remain GATED below. m2 legs keep the fc==0 gate.
            pass
        elif fc != 0:
            refuse(f"{config}/{tag} four_cycles {fc} != 0 "
                   f"(STOP-BLOCKED; L1B packet §1; measured girth {girth})")
        if rank != m:
            refuse(f"{config}/{tag} rank {rank} != {m} "
                   f"(STOP-BLOCKED; L1B packet §1; measured girth {girth})")
        code_a["construct_seed"] = seed
        code_a["construct_trials"] = trials
        out[tag] = code_a
    return out


def execute(*, root: str, stage: str, config: str,
            bundle: dict[str, Any] | None = None,
            construct_fn: Callable | None = None,
            decode_fn: Callable | None = None,
            clock: Callable | None = None,
            rss_fn: Callable | None = None,
            writer: Callable | None = None,
            resume_from: str | None = None,
            max_blocks: int | None = None,
            de_label: str | None = None,
            block_base: int = L1B_BLOCK_BASE,
            n_blocks: int = L1B_N_BLOCKS,
            construct_seed: int = L1B_CONSTRUCT_SEED,
            construct_trials: int = L1B_MAX_TRIALS) -> dict:
    """Run (or once-continue) the frozen L1B stage-config campaign.

    One stage-config per invocation; paired block seeds shared across
    configs/stages. ``max_blocks`` is a PROBE-ONLY cap (timing
    integration; never a CLI flag, never part of any verdict).
    ``decode_fn`` convention is ``(constructions, seed)`` where
    ``constructions`` = ``{"m1": code, "m2": code}`` from the gate
    (``{"m1": code}`` only for SCAN Stage-A-only configs, for which
    Stage B refuses rc=2 pre-decode — m2 not constructed).
    Without an injected ``decode_fn``, ``bundle`` is required (no silent
    production bind — the CLI binds ``--gamma`` explicitly). Stage A
    decodes L1-only; Stage B decodes the combined chain. All writes stay
    under ``root``. The campaign run never requires a DE precheck
    (``de_label`` defaults 'exploratory' if absent).
    """
    if stage not in STAGES:
        refuse(f"unknown stage {stage} (frozen: A|B only)")
    if config not in CONFIGS:
        refuse(f"unknown config {config} (frozen: C6|C8|C12A|C16A only)")
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
    m1 = int(CONFIGS[config]["m1"])
    if CONFIGS[config].get("stage_a_only"):
        if stage != "A":
            refuse(f"Stage B unavailable for Stage-A-only config {config} "
                   f"(m2 not constructed; m2 pairing deferred to the "
                   f"Stage B packet)")
        m2 = None
    else:
        m2 = int(CONFIGS[config]["m2"])
    construct_fn = construct_fn or construct_code
    if decode_fn is None:
        if bundle is None:
            refuse("empirical bundle required (no silent production bind; "
                   "pass bundle or bind --gamma at the CLI)")
        _bundle = bundle

        if stage == "A":
            def decode_fn(constructions, seed, _b=_bundle):  # noqa: B023
                return decode_l1_block(constructions["m1"], seed, _b,
                                       L1B_N, m1)
        else:
            def decode_fn(constructions, seed, _b=_bundle):  # noqa: B023
                return decode_combined_block(constructions["m1"],
                                             constructions["m2"], seed,
                                             _b, L1B_N, m1, m2)
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
        st = _validate_partial(manifest_p, rows_p, stage, config,
                               block_base=block_base, n_blocks=n_blocks,
                               construct_seed=construct_seed)
        constructions = _construct_gate(config, construct_fn,
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
        constructions = _construct_gate(config, construct_fn,
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
            stage=stage, config=config, constructions=constructions,
            rows=rows, failures=failures, blocks_completed=len(rows),
            verdict=verdict, partial=partial, next_block=next_block,
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
        seed = block_seed(config, k, block_base)
        t0 = clock()
        try:
            out = decode_fn(constructions, seed)
        except Exception as exc:  # noqa: BLE001 — no-retry: retain + halt
            rows.append({"block": k, "status": "error",
                         "error": f"{type(exc).__name__}: {exc}"})
            return _flush("FAIL(budget)", True, k)
        dt = clock() - t0
        if dt > PER_DECODE_CAP_S:
            rows.append({"block": k, "status": "overrun",
                         "decode_s": dt})
            return _flush("FAIL(budget)", True, k)
        ok = bool(out.get("exact_match") is True)
        if not ok:
            failures += 1
        ledger_decodes += 1
        basis = leak_basis(config)
        row: dict[str, Any] = {
            "block": k,
            "seed": seed,
            "l1_exact": out.get("l1_exact"),
            "exact_match": bool(out.get("exact_match", False)),
            "block_accept": ok,
            "block_fail": 0 if ok else 1,
            "status": out.get("status"),
            "converged": bool(out.get("reconstruction_ok", False)),
            "iterations": out.get("iterations"),
            "wall_s": dt,
            "d_blind": basis["d_blind"],
            "d_blind_label": basis["d_blind_label"],
            "leak_bits": basis["leak_bits"],
            "f_super": basis["f_super_basis"],
        }
        if stage == "B":
            row["l1_status"] = out.get("l1_status")
            row["l1_iterations"] = out.get("l1_iterations")
            row["l2_exact"] = out.get("l2_exact")
            row["l2_skipped"] = bool(out.get("l2_skipped", False))
            row["chain"] = out.get("chain")
        else:
            row["l2_exact"] = None
        rows.append(row)
        # Checkpoint per COMPLETED block (overwrite-in-place, single writer).
        _flush("INCOMPLETE-wall", True, k + 1)
        if failures > bar:
            # Early-stop: (bar+1)-th block failure makes the bar
            # unpassable (n=240: 13th). Retain partials.
            return _flush("FAIL-early-stop", True, k + 1)

    if max_blocks is not None:
        # Probe-only truncation: no verdict, no claim.
        return _flush("PROBE-truncated", True, target)
    basis = leak_basis(config)
    passed = (failures <= bar
              and basis["f_super_basis"] <= F_SUPER_MAX)
    return _flush("PASS" if passed else "FAIL", False, n_blocks)


def run_execution(root: str, stage: str, config: str,
                  resume_from: str | None = None,
                  gamma: str = GAMMA_DEFAULT,
                  source: str = SOURCE_DEFAULT,
                  bundle: dict[str, Any] | None = None,
                  de_label: str | None = None,
                  block_base: int = L1B_BLOCK_BASE,
                  n_blocks: int = L1B_N_BLOCKS,
                  construct_seed: int = L1B_CONSTRUCT_SEED,
                  construct_trials: int = L1B_MAX_TRIALS) -> int:
    bound = bundle if bundle is not None else s2c.bind_empirical_bundle(
        gamma, source)
    manifest = execute(root=root, stage=stage, config=config,
                       bundle=bound,
                       resume_from=resume_from, de_label=de_label,
                       block_base=block_base, n_blocks=n_blocks,
                       construct_seed=construct_seed,
                       construct_trials=construct_trials)
    print(json.dumps({"campaign": manifest["campaign"],
                      "stage": manifest["stage"],
                      "config": manifest["config"],
                      "verdict": manifest["verdict"],
                      "failures": manifest["failures"],
                      "fer_blocks": manifest["fer_blocks"],
                      "f_super": manifest["f_super"],
                      "f_L1": manifest["f_L1"],
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
    ap.add_argument("--stage", default="")
    ap.add_argument("--config", default="")
    ap.add_argument("--root", default="")
    ap.add_argument("--resume-from", default="")
    ap.add_argument("--gamma", default=GAMMA_DEFAULT)
    ap.add_argument("--source", default=SOURCE_DEFAULT)
    ap.add_argument("--de-label", default="")
    ap.add_argument("--block-base", type=int, default=L1B_BLOCK_BASE)
    ap.add_argument("--n-blocks", type=int, default=L1B_N_BLOCKS)
    ap.add_argument("--construct-seed", type=int,
                    default=L1B_CONSTRUCT_SEED)
    ap.add_argument("--construct-trials", type=int,
                    default=L1B_MAX_TRIALS)
    args = ap.parse_args(argv)
    # Dual-flag gate: refuse EVERYTHING else rc=2 BEFORE any root/contact.
    # There is no profile-only mode and no silent path.
    if not args.execute_real:
        refuse("refusing: --execute-real missing (rc2 pre-anything)")
    if not args.execution_authorized:
        refuse("refusing: --execution-authorized missing (rc2 pre-anything)")
    if args.stage not in STAGES:
        refuse(f"unknown stage {args.stage} (frozen: A|B only)")
    if args.config not in CONFIGS:
        refuse(f"unknown config {args.config} (frozen: C6|C8|C12A|C16A only)")
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
    root = args.resume_from or args.root
    if not root:
        refuse("root required (fresh additive workspace/l1b_<uuid>)")
    if not _allows_root(root):
        refuse(f"root must be fresh additive {ROOT_PREFIX}<uuid> "
               f"(got {root})")
    return run_execution(root=root, stage=args.stage, config=args.config,
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
