"""V80 S1 readiness runner (EXPLORE-readiness, NOT execution).

Thin additive wrapper over the frozen V26 MC-DE kernel
(:mod:`nonbinary_v26_mcde`, imported read-only, never edited). This module
performs ZERO scientific DE calls: it only freezes the S1 D-de config,
builds the capped evaluation plan (profile-only dry pass), enforces the
split/caps/no-retry/overlap/resource gates in code, and refuses (rc=2)
anything execution-shaped.

Real gamma_i binding is deferred: the channel enters only via the injected
``channel_sampler`` interface (fake sampler in tests; real binding needs a
separate explicit execution grant + Pre-EXECUTE).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

from . import nonbinary_v26_mcde as _K  # noqa: F401  (read-only reuse; never edited)

# ---------------------------------------------------------------- frozen S1 D-de config
N_FRAME = 256
M_GRID = (24, 25, 26, 27, 28, 29, 30, 31)
SCREEN = {"n_samples": 4000, "max_iter": 60, "tol": 1e-4, "streak": 20}
CONFIRM = {"n_samples": 16000, "max_iter": 100, "tol": 1e-4, "streak": 20}
DV_SUPPORT = (2, 3, 4, 5, 8, 13, 20)
DV_CEILING = 40  # BOUND_HIT rule armed; never exceed in S1
L1_FIXED = {2: 1.0}
OUTER_DE = {"sparse_K": 4, "min_weight": 0.05, "sum_tol": 1e-12,
            "polish": False, "workers": 1}
POP_GEN = {"PRIMARY": (10, 14), "SECONDARY": (10, 5)}
CAPS = {"PRIMARY": 420, "SECONDARY": 180, "TOTAL": 600, "SETUP": 12}
# Disjoint from D16 (4001-4012/4101-4108), D17 (2026094201..08),
# D18 (2026094301..4308 + bare 4301..4308), D19 graphs (2026094401..4412) +
# D19 blocks (2026094501..4508/4511..4518), G6 (4601/4602/4720/4721),
# R7 (4701..4708/4711..4719), R11 (4722/4723), R23 (4801..4816/4831..4884+),
# CLI defaults (5001/8001/9001); 20260949xx hundred-block clean repo-wide
# (zero rg hits in src/tests/docs/openspec/.workbuddy). Confirm reuses screen set.
SCREEN_SEEDS = (2026094951, 2026094952)
CONFIRM_SEEDS = (2026094951, 2026094952)
BUDGETS = {"wall_total_s": 3600, "per_call_s": 300,
           "rss_gib": 4, "cpus": 1}
NO_RETRY = True
# Planning means only (profile arithmetic, not code caps; hard gate stays
# per_call_s=300 with resource_blocked terminal on overrun).
SCREEN_MEAN_S = 4.0
CONFIRM_PLAN_ITERS = 5  # early-stop expectation for confirm wall/node planning
CONFIRM_MEAN_S = 8.0
BANNED_CONSTRUCTION_KEYS = ("matrix", "peg", "parity", "generator",
                            "cyclic", "shift", "construct")

# ------------------------------------------------- S1 execution path (D1 delta)
# Frozen D-de execution semantics (S1 freeze: design.md S1 essentials +
# S1_READINESS.md frozen D-de config). Code only; NO execution runs here.
# Real gamma binding (gamma_f03.npz, read-only) + DE loop activate ONLY under
# --execute-real + --execution-authorized (both, default-false). Anything else
# execution-shaped refuses rc=2 BEFORE any root/bind/DE/kernel contact.
# Recorded here + in code comments per main-thread ruling; no new OpenSpec
# change (completes the frozen design, not new scope).
RECORDED_CONFIG_HASH = ("60ab1e44dc179e6d783d1792dae59fd691c5657e386056498140d37fe0"
                        "4fb0da")
# F1 hash rotation (S1-fix 2026-09-19, packet §2/T-HASH): old 57e5da44…684 →
# new 60ab1e44…0da. Field entered frozen_config(): "primary_m2_grid" (44–60);
# no field left ("m_grid" stays SECONDARY-only 24–31). _validate_partial /
# RECORDED_CONFIG_HASH / verify_manifest consistency rotated together; old
# 420-slot PRIMARY root (old hash) is foreign post-rotation (resume refuses),
# retained untouched, never overwritten.
# R2 disposition (reviewer-flagged, kept-with-rationale): sampler binding
# (L1/L2/JOINT selection in execute()/execute_arm()) lives OUTSIDE
# frozen_config() — the hashed dict covers only kernel/n_frame/m_grid/
# screen/confirm/dv_support/dv_ceiling/L1_fixed/outer_de/pop_gen/caps/seeds/
# budgets/no_retry. Binding SECONDARY to the joint (n,1024) sampler therefore
# does NOT alter frozen_config() or config_hash(); RECORDED_CONFIG_HASH stays
# 60ab1e44…0da (57e5da44…684 is the pre-rotation historical value) with zero
# silent drift (pinned by tests: binding-outside-hash + hash-recorded pins
# both green).
# F3 disposition (Q0 sampler-semantics fix, kept-with-rationale): the Q0 fix
# rewrites only sampler internals (empirical joint + XOR centering, Q5 axis
# [u1,u2,b]); frozen_config() verified to contain no sampler/p_b/channel
# keys, so the fix is outside the hashed scope like the R2 binding — hash
# kept, no re-freeze (pinned by tests + profile-only).
# F3 disposition (production p_b binding, fail closed): the production path is
# uniform ONLY by silent fallback — bind_gamma never loaded p_b and
# gamma_f03.npz carries no p_b keys, so bundle.get("p_b",None) fell through to
# np.full(1024,1/1024) on every production bind while only tests injected p_b.
# Fix: empirical per-source p_b (train colsum/N from the SAME counts-npz the
# S1r-gamma step used) lives in a NEW sidecar file gamma_f03_pb.npz next to
# gamma_f03.npz (choice: sidecar, NOT a full copy — cited gamma_f03.npz bytes
# stay untouched, no gamma duplication/skew; runner resolves the sibling).
# File-bound bind REQUIRES normalized p_b (absent/misnormalized -> refuse
# BEFORE any DE call). Uniform fallback survives ONLY for explicitly-flagged
# fake bundles (flag FAKE_BUNDLE_FLAG, frozen below + pinned in tests).
# Hash kept: like the R2/F3 dispositions, all of this lives outside
# frozen_config() (no sampler/p_b/channel keys in the hashed dict) — hash
# stays 60ab1e44…0da (57e5da44…684 pre-rotation historical) with zero silent
# drift (pinned by tests).
GAMMA_DEFAULT = "docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz"
PB_SIDECAR_NAME = "gamma_f03_pb.npz"  # sibling of the gamma file, never in-place
FAKE_BUNDLE_FLAG = "_fake"  # frozen: uniform-p_b fallback ONLY when truthy
FROZEN_ROOT = "workspace/s1_mcde_07723233-e537-4a2e-857a-954e3a94d030"
# Worst-source TRAIN H anchors (2M; readiness S1r-gamma verification values).
H_ANCHORS = {"L1": 0.02566205, "L2": 0.80690067}
H_TOTAL_ANCHOR = H_ANCHORS["L1"] + H_ANCHORS["L2"]
F03_TARGETS = {"L1": 0.025, "L2": 0.795}  # ±0.02 binding gate (readiness S1r)
LAYER_WIDTH = {"PRIMARY": 5, "SECONDARY": 10}  # GF(32) L2 layer / direct-q1024
# F1 (S1-fix 2026-09-19, packet §2): PRIMARY layer-local grid.
# L2 feasibility bound: 1 − H_L2/5 = 1 − 0.80690067/5 = 0.83862. Full-symbol
# m 24–31 → rate 0.879–0.906, ALL above the bound → 0/420 theory-consistent.
# Correct layer-local mapping: m2 = ceil(f·H_L2·n/5) = ceil(41.31·f), n=256.
# f=1.3 → m2≈54; sweep f≈1.05–1.45 → m2≈44–60 (ceil(41.31·1.05)=44,
# ceil(41.31·1.3)=54, ceil(41.31·1.45)=60).
# PRIMARY uses PRIMARY_M2_GRID (44–60, width-5 L2 budget) ONLY; M_GRID (24–31)
# is SECONDARY-only (width-10 direct-q1024, feasible as a budget — its
# gate/reporting still needed the §3 F2 rework). Full-symbol m 24–31 MUST NOT
# be reused for L2 (disjointness asserted; PRIMARY path uses PRIMARY_M2_GRID
# exclusively, no M_GRID fallback).
L2_FEASIBILITY_BOUND = 1.0 - H_ANCHORS["L2"] / 5  # 0.83862
PRIMARY_M2_GRID = tuple(range(44, 61))  # 44–60 inclusive, 17 pts
assert set(PRIMARY_M2_GRID).isdisjoint(set(M_GRID)), \
    "F1: PRIMARY m2 must not reuse full-symbol m 24–31"
GATE_F_ENS = 1.15  # per-arm gate: ∃ converged row with 1.0 ≤ f_row ≤ 1.15 (F2)


def primary_m2_for_f(f: float) -> int:
    """F1 layer-local mapping: m2 = ceil(f·H_L2·n/5) = ceil(41.31·f)."""
    import math
    return math.ceil(float(f) * H_ANCHORS["L2"] * N_FRAME / 5)
FLIP_MARGIN = 0.05
FLIP_MIN_PTS = 2
FLIP_REQUIRED_M = (27, 29)  # flip needs wins incl. m27/m29; COMPUTE only
EXEC_SOURCE_DEFAULT = "2M"  # worst-source anchor; never auto-merge sources
DE_MUT_F = 0.5
DE_MUT_CR = 0.9


class Refusal(SystemExit):
    """rc=2 pre-write refusal (invalid config / unauthorized execution)."""


def refuse(reason: str) -> "NoReturn":
    print(f"S1-REFUSAL rc=2: {reason}", file=sys.stderr)
    raise Refusal(2)


def frozen_config() -> dict:
    # F1 hash rotation (packet §2/T-HASH): PRIMARY layer-local grid enters the
    # hashed config as "primary_m2_grid" (44–60); "m_grid" stays SECONDARY-only
    # (24–31). Old hash 57e5da44…684 → new hash (see RECORDED_CONFIG_HASH).
    return {
        "kernel": "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v26_mcde.py",
        "n_frame": N_FRAME, "m_grid": list(M_GRID),
        "primary_m2_grid": list(PRIMARY_M2_GRID),
        "screen": dict(SCREEN), "confirm": dict(CONFIRM),
        "dv_support": list(DV_SUPPORT), "dv_ceiling": DV_CEILING,
        "L1_fixed": {str(k): v for k, v in L1_FIXED.items()},
        "outer_de": dict(OUTER_DE), "pop_gen": {k: list(v) for k, v in POP_GEN.items()},
        "caps": dict(CAPS),
        "screen_seeds": list(SCREEN_SEEDS), "confirm_seeds": list(CONFIRM_SEEDS),
        "budgets": dict(BUDGETS), "no_retry": NO_RETRY,
    }


def config_hash(cfg: dict | None = None) -> str:
    blob = json.dumps(cfg if cfg is not None else frozen_config(), sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


def validate_lambda(lambda_edge: dict) -> None:
    tot = sum(float(v) for v in lambda_edge.values())
    if abs(tot - 1.0) > 1e-12:
        refuse(f"unnormalized lambda (sum={tot})")
    for dv in lambda_edge:
        if int(dv) > DV_CEILING:
            refuse(f"bound violation dv={dv} > ceiling {DV_CEILING}")
        if int(dv) not in DV_SUPPORT and int(dv) != 2 and len(lambda_edge) > 1:
            refuse(f"dv={dv} outside searched support {list(DV_SUPPORT)}")


def validate_rho(rho_edge: dict) -> None:
    tot = sum(float(v) for v in rho_edge.values())
    if abs(tot - 1.0) > 1e-12:
        refuse(f"invalid rho (sum={tot})")
    if not rho_edge:
        refuse("invalid rho (empty)")


def assert_no_construction(plan: dict) -> None:
    """S1 outputs degree profiles ONLY — fail closed on construction commitment."""
    blob = json.dumps(plan).lower()
    for key in BANNED_CONSTRUCTION_KEYS:
        if key in blob:
            refuse(f"construction commitment banned in S1 ({key})")


def build_plan() -> dict:
    """Deterministic capped plan. No DE, no RNG, no channel reads."""
    rows: list[dict] = []
    # PRIMARY: pop10 x gen14 = 140 individuals; screen 2 seeds, confirm 1 reuse seed.
    # F1: PRIMARY uses its own layer-local PRIMARY_M2_GRID (44–60) ONLY — the
    # old M_GRID-shared path for PRIMARY is removed, never a fallback.
    pop, gen = POP_GEN["PRIMARY"]
    for slot in range(pop * gen):
        m = PRIMARY_M2_GRID[slot % len(PRIMARY_M2_GRID)]
        for s in SCREEN_SEEDS:
            rows.append({"arm": "PRIMARY", "phase": "screen", "m": m,
                         "rate": 1 - m / N_FRAME, "n_samples": SCREEN["n_samples"],
                         "max_iter": SCREEN["max_iter"], "seed": s,
                         "slot": slot, "reuse": False, "kind": "de"})
    for slot in range(pop * gen):
        m = PRIMARY_M2_GRID[slot % len(PRIMARY_M2_GRID)]
        rows.append({"arm": "PRIMARY", "phase": "confirm", "m": m,
                     "rate": 1 - m / N_FRAME, "n_samples": CONFIRM["n_samples"],
                     "max_iter": CONFIRM["max_iter"], "seed": CONFIRM_SEEDS[0],
                     "slot": slot, "reuse": True, "kind": "de"})
    # SECONDARY: pop10 x gen5 = 50 individuals; screen 2 seeds;
    # confirm 40 rate-winners (top-5/m x 8 m) x 2 reuse seeds.
    pop, gen = POP_GEN["SECONDARY"]
    for slot in range(pop * gen):
        m = M_GRID[slot % len(M_GRID)]
        for s in SCREEN_SEEDS:
            rows.append({"arm": "SECONDARY", "phase": "screen", "m": m,
                         "rate": 1 - m / N_FRAME, "n_samples": SCREEN["n_samples"],
                         "max_iter": SCREEN["max_iter"], "seed": s,
                         "slot": slot, "reuse": False, "kind": "de"})
    for w in range(40):
        m = M_GRID[w % len(M_GRID)]
        for s in CONFIRM_SEEDS:
            rows.append({"arm": "SECONDARY", "phase": "confirm", "m": m,
                         "rate": 1 - m / N_FRAME, "n_samples": CONFIRM["n_samples"],
                         "max_iter": CONFIRM["max_iter"], "seed": s,
                         "slot": w, "reuse": True, "kind": "de"})
    # +12 setup (non-DE): 8 rate targets + 2 perm tables + hash + plan check.
    for m in M_GRID:
        rows.append({"arm": "SETUP", "phase": "setup", "m": m,
                     "rate": 1 - m / N_FRAME, "kind": "setup"})
    for q in (32, 1024):
        rows.append({"arm": "SETUP", "phase": "setup", "q": q, "kind": "setup"})
    rows.append({"arm": "SETUP", "phase": "setup", "op": "config_hash",
                 "kind": "setup"})
    rows.append({"arm": "SETUP", "phase": "setup", "op": "plan_check",
                 "kind": "setup"})
    n_p = sum(1 for r in rows if r["arm"] == "PRIMARY")
    n_s = sum(1 for r in rows if r["arm"] == "SECONDARY")
    n_t = sum(1 for r in rows if r.get("kind") == "de")
    n_u = sum(1 for r in rows if r.get("kind") == "setup")
    assert (n_p, n_s, n_t, n_u) == (CAPS["PRIMARY"], CAPS["SECONDARY"],
                                   CAPS["TOTAL"], CAPS["SETUP"]), (n_p, n_s, n_t, n_u)
    n_screen = sum(1 for r in rows if r.get("phase") == "screen")
    n_confirm = sum(1 for r in rows if r.get("phase") == "confirm")
    node_updates = (n_screen * SCREEN["n_samples"] * SCREEN["max_iter"]
                    + n_confirm * CONFIRM["n_samples"] * CONFIRM_PLAN_ITERS)
    wall_s = n_screen * SCREEN_MEAN_S + n_confirm * CONFIRM_MEAN_S
    return {"config_hash": config_hash(), "rows": rows,
            "totals": {"PRIMARY": n_p, "SECONDARY": n_s, "de": n_t,
                       "setup": n_u, "node_updates": node_updates,
                       "wall_s": wall_s}}


def resource_gate(used_s: float, rss_gib: float) -> str:
    """Overrun -> resource_blocked terminal; never retry, never resume silently."""
    if used_s > BUDGETS["wall_total_s"] or rss_gib >= BUDGETS["rss_gib"]:
        return "resource_blocked"
    return "ok"


def main(argv: list[str] | None = None, channel_sampler=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execution-authorized", action="store_true", default=False)
    ap.add_argument("--profile-only", action="store_true", default=False)
    ap.add_argument("--execute-real", action="store_true", default=False)
    ap.add_argument("--gamma", default=GAMMA_DEFAULT)
    ap.add_argument("--source", default=EXEC_SOURCE_DEFAULT)
    ap.add_argument("--root", default="")
    ap.add_argument("--resume-from", default="")  # explicit resume, default OFF
    ap.add_argument("--repro-gate", action="store_true", default=False)
    args = ap.parse_args(argv)
    if args.repro_gate:
        # G-REPRO gate (packet 2026-09-20): ONLY the 30 gate cells,
        # single-turn, fresh additive root. Execution-shaped: BOTH flags
        # required; every non-authorized shape refuses rc=2 pre-anything
        # (before any root/bind/DE/kernel contact).
        import uuid as _uuid
        if args.profile_only:
            refuse("repro-gate with --profile-only (ambiguous; rc2 pre-anything)")
        if args.resume_from:
            refuse("repro-gate is single-turn: --resume-from refused "
                   "(rc2 pre-anything)")
        if not args.execute_real:
            refuse("repro-gate without --execute-real (rc2 pre-anything)")
        if not args.execution_authorized:
            refuse("repro-gate without --execution-authorized "
                   "(rc2 pre-anything)")
        root = args.root or (REPRO_ROOT_PREFIX + _uuid.uuid4().hex[:8])
        if not root.startswith(REPRO_ROOT_PREFIX):
            refuse("repro root must be fresh additive "
                   f"{REPRO_ROOT_PREFIX}<uuid> (got {root})")
        return run_repro_execution(root=root,
                                   gamma_source=args.gamma,
                                   source=args.source)
    if args.resume_from and not args.execute_real:
        refuse("resume-from without --execute-real (resume is execution; "
               "rc2 pre-anything)")
    if args.resume_from and args.profile_only:
        refuse("resume-from with --profile-only (ambiguous; rc2 pre-anything)")
    if args.execute_real:
        # BOTH flags required; refuse BEFORE any root/bind/DE/kernel contact.
        if not args.execution_authorized:
            refuse("execute-real without --execution-authorized (rc2 pre-anything)")
        if args.resume_from:
            if args.root and args.root != args.resume_from:
                refuse("root/resume-from mismatch (fail closed)")
            return run_execution(root=args.resume_from,
                                 gamma_source=args.gamma, source=args.source,
                                 resume_from=args.resume_from)
        return run_execution(root=args.root or FROZEN_ROOT,
                             gamma_source=args.gamma, source=args.source)
    if not args.profile_only:
        if not args.execution_authorized:
            refuse("default --execution-authorized=false (rc2 pre-anything)")
        refuse("readiness build only: no execution grant; real gamma binding "
               "deferred to execution Pre-EXECUTE")
    cfg = frozen_config()
    validate_lambda({2: 1.0})
    validate_rho(_K.make_rho(1 - M_GRID[0] / N_FRAME, {2: 1.0}))
    plan = build_plan()
    assert_no_construction(plan)
    if resource_gate(plan["totals"]["wall_s"], 0.0) != "ok":
        refuse("plan exceeds wall budget")
    if args.root and os.path.exists(args.root):
        refuse(f"root not fresh: {args.root}")
    # Profile-only: never invoke channel_sampler, never create root, never DE.
    print(json.dumps({"config_hash": plan["config_hash"],
                      "totals": plan["totals"],
                      "scientific_de_calls": 0}, indent=1))
    return 0


# ------------------------------------------------ execution-path helpers
# All injectable (de_fn/clock/rss_fn/writer/samplers) so tests run FAKE-only
# with zero production run_mcde_posterior calls and zero disk writes.


class Ledger:
    """Live call ledger. Refuse-before-exceed; counts never adjusted down."""

    def __init__(self) -> None:
        self.counts = {"PRIMARY": 0, "SECONDARY": 0, "TOTAL": 0, "SETUP": 0}

    def charge(self, arm: str, kind: str = "de") -> None:
        if kind == "setup":
            if self.counts["SETUP"] + 1 > CAPS["SETUP"]:
                refuse(f"ledger cap: SETUP > {CAPS['SETUP']}")
            self.counts["SETUP"] += 1
            return
        if arm not in ("PRIMARY", "SECONDARY"):
            refuse(f"ledger: unknown arm {arm}")
        if self.counts[arm] + 1 > CAPS[arm]:
            refuse(f"ledger cap: {arm} > {CAPS[arm]}")
        if self.counts["TOTAL"] + 1 > CAPS["TOTAL"]:
            refuse(f"ledger cap: TOTAL > {CAPS['TOTAL']}")
        self.counts[arm] += 1
        self.counts["TOTAL"] += 1


def _check_pb(pb: "object", ctx: str):  # fail closed, never renormalize silently
    import numpy as np
    arr = np.asarray(pb, dtype=np.float64)
    if (arr.shape != (1024,) or not np.all(np.isfinite(arr))
            or np.any(arr < 0.0) or abs(float(arr.sum()) - 1.0) > 1e-9):
        refuse(f"{ctx} p_b not normalized (shape/finite/nonneg/sum=1±1e-9)")
    return arr


def _resolve_pb(bundle: dict):
    """Sampler-side p_b: honor the bound vector; fake-only uniform otherwise.

    The ONLY np.full(1024,1/1024) in this module lives in the flagged-fake
    branch below. Production bundles without p_b refuse here (defense in
    depth — bind_gamma already refused earlier). No silent rescale anywhere.
    """
    import numpy as np
    _pb = bundle.get("p_b", None)
    if _pb is None:
        if bundle.get(FAKE_BUNDLE_FLAG, False):
            return np.full(1024, 1.0 / 1024)  # fake-only uniform
        refuse("sampler without bound p_b on production bundle (fail closed)")
    return _check_pb(_pb, "sampler-bound")


def bind_gamma(gamma_source, source: str = EXEC_SOURCE_DEFAULT) -> dict:
    """Load gamma_f03.npz read-only + assert shapes/normalization vs the
    readiness record. Fail closed BEFORE any DE call. Accepts an already
    loaded mapping (tests) with bundle keys gamma1/gamma2/H_L1/H_L2.
    Axes (Q5 branch-a fix): g1[u1,b], g2[u1,u2,b] = V26 pjoint convention
    (cond-rowsum over axis=1); artifact untouched.
    F3: file-bound bundles MUST carry empirical p_b from the sibling sidecar
    (PB_SIDECAR_NAME); absent/misnormalized p_b on a production (non-fake-
    flagged) bind refuses. Dict bundles: explicit p_b honored (validated);
    missing p_b requires the frozen fake flag, else refuse."""
    import numpy as np
    _fake = False
    if isinstance(gamma_source, str):
        try:
            npz = np.load(gamma_source)  # read-only load; never refit
            try:
                g1 = np.asarray(npz[f"{source}_gamma1_L1"], dtype=np.float64)
                g2 = np.asarray(npz[f"{source}_gamma2_L2condU1"], dtype=np.float64)
                h1 = float(npz[f"{source}_H_L1"])
                h2 = float(npz[f"{source}_H_L2"])
            finally:
                npz.close()
        except Refusal:
            raise
        except Exception as exc:  # noqa: BLE001 — fail closed on load failure
            refuse(f"gamma load failed for {gamma_source}[{source}]: "
                   f"{type(exc).__name__}: {exc}")
        side = Path(gamma_source).parent / PB_SIDECAR_NAME
        try:
            sp = np.load(side)  # read-only sidecar; never refit
            try:
                _pb = np.asarray(sp[f"{source}_p_b"], dtype=np.float64)
            finally:
                sp.close()
        except Refusal:
            raise
        except Exception as exc:  # noqa: BLE001 — fail closed, no uniform
            refuse(f"p_b sidecar missing/unreadable ({side}[{source}_p_b]): "
                   f"{type(exc).__name__}: {exc}")
        p_b = _check_pb(_pb, "file-bound")
    else:
        g1, g2 = gamma_source["gamma1"], gamma_source["gamma2"]
        h1, h2 = float(gamma_source["H_L1"]), float(gamma_source["H_L2"])
        _pb = gamma_source.get("p_b", None)
        if _pb is None:
            if not gamma_source.get(FAKE_BUNDLE_FLAG, False):
                refuse("production bundle without p_b: uniform fallback is "
                       "fake-only (flag '_fake'); refusing")
            p_b = None  # fake-only: sampler applies uniform downstream
            _fake = True  # propagate so _resolve_pb tells fake from prod
        else:
            p_b = _check_pb(_pb, "dict-bound")
            _fake = False
    if g1.shape != (32, 1024):
        refuse(f"gamma1 shape {g1.shape} != (32, 1024)")
    if g2.shape != (32, 32, 1024):
        refuse(f"gamma2 shape {g2.shape} != (32, 32, 1024)")
    if not np.allclose(g1.sum(axis=0), 1.0, atol=1e-9):
        refuse("gamma1 colsums != 1")
    # Q5 branch (a): artifact is [u1,u2,b] = V26 pjoint convention
    # (axis-entropy signature 2M H(ax0|B)=0.02537~=0.02566 U1 vs
    # H(ax1|U1,B)=0.80696~=0.80690 U2, uniform-p_b read-only neutral;
    # cond-rowsum over axis=1, verified sums axis1==1 axis0!=1).
    # Prior axis=0 assumption was wrong; artifact untouched, runner fixed.
    if not np.allclose(g2.sum(axis=1), 1.0, atol=1e-9):
        refuse("gamma2 cond-rowsums != 1")
    for got, tgt, nm in ((h1, F03_TARGETS["L1"], "H_L1"),
                         (h2, F03_TARGETS["L2"], "H_L2")):
        if not (0.0 < got <= 1.0) or abs(got - tgt) > 0.02:
            refuse(f"{nm}={got} outside F03 target {tgt} ±0.02")
    out = {"gamma1": g1, "gamma2": g2, "H_L1": h1, "H_L2": h2,
           "source": source, "p_b": p_b}
    if not isinstance(gamma_source, str) and _fake:
        out[FAKE_BUNDLE_FLAG] = True  # fake-unbound marker for _resolve_pb
    return out


def make_centered_sampler(bundle: dict, layer: str):
    """Frozen binding: empirical train-joint + XOR/GF-add centering (Q0 fix).

    V26-validated A02 semantics (nonbinary_v26_channel 259-280 pattern):
    (A,B)~P_ab joint pick, rows from the posterior tables, out[i] =
    rows[i, idx[:q] ^ tv] (true symbol to index 0, kernel's centered
    contract). Frozen validated config governs; the prior uniform-B +
    cyclic-shift construction was never chartered (freeze gap closed here).
    Axes (Q5 branch-a): g1[u1,b], g2[u1,u2,b] = V26 pjoint convention;
    artifact untouched. L1/L2 distinction otherwise unchanged (shapes,
    renormalize + delta-at-0 fallback on zero-mass intact). RNG-only.
    B marginal (F3): the bound empirical p_b, resolved fail-closed at
    construction (production without p_b refuses; uniform ONLY for bundles
    carrying the frozen fake flag). All draws via choice
    with p; no uniform-int / cyclic-shift path remains."""
    import numpy as np
    g1, g2 = bundle["gamma1"], bundle["gamma2"]
    p_b = _resolve_pb(bundle)
    _idx32 = np.arange(32, dtype=np.int64)

    def sampler(n: int, rng):
        if layer == "L1":
            b = rng.choice(1024, size=n, p=p_b)
            cols = g1[:, b].T  # (n, 32) P(U1|B)
            out = np.empty_like(cols)
            for i in range(n):
                col = cols[i]
                tot = col.sum()
                if not np.isfinite(tot) or tot <= 0.0:
                    col = np.zeros(32)
                    col[0] = 1.0
                else:
                    col = col / tot
                tv = int(rng.choice(32, p=col))
                out[i] = col[_idx32 ^ tv]
            return out
        b = rng.choice(1024, size=n, p=p_b)
        out = np.empty((n, 32), dtype=np.float64)
        for i in range(n):
            bb = int(b[i])
            g1col = g1[:, bb]
            s1 = g1col.sum()
            if not np.isfinite(s1) or s1 <= 0.0:
                u1t = 0
            else:
                u1t = int(rng.choice(32, p=g1col / s1))
            row = np.asarray(g2[u1t, :, bb], dtype=np.float64)
            tot = row.sum()
            if not np.isfinite(tot) or tot <= 0.0:
                row = np.zeros(32)
                row[0] = 1.0
            else:
                row = row / tot
            u2t = int(rng.choice(32, p=row))
            out[i] = row[_idx32 ^ u2t]
        return out
    return sampler


def make_joint_sampler(bundle: dict):
    """Full-symbol (n,1024) centered sampler from bound g1/g2 (D5 fix, Q0+Q5).

    Joint P(U1,U2|B=b) = g1[u1,b] * g2[u2|b,u1] (bundle axes g1[u1,b],
    g2[u1,u2,b] = V26 pjoint convention per Q5 branch-a; cond-rowsum over
    axis=1); row j = u1*32+u2 (F03 natural: U = U1<<5 | U2). g2 already
    carries the frozen posterior_rows delta-at-0 fallback for P(U1|B)=0
    cells (S1_READINESS S1r-gamma), so those joint entries vanish via the
    g1 factor — same convention the L1/L2 samplers use (renormalize +
    delta-at-0 on zero-mass). Q0: empirical joint pick + XOR/GF-add
    centering (V26 259-280 pattern); prior uniform-B + cyclic-shift was
    never chartered. RNG-only randomness. SECONDARY (direct-q1024) binds
    here; PRIMARY stays on the L2 sampler. B marginal (F3): bound empirical
    p_b, resolved fail-closed at construction (see make_centered_sampler).
    """
    import numpy as np
    g1, g2 = bundle["gamma1"], bundle["gamma2"]
    p_b = _resolve_pb(bundle)
    j3 = np.empty((32, 32, 1024), dtype=np.float64)
    for u1 in range(32):
        j3[u1] = g2[u1, :, :] * g1[u1][None, :]
    joint = j3.reshape(1024, 1024)  # row j = u1*32+u2 (C-order merge)
    _idx1024 = np.arange(1024, dtype=np.int64)

    def sampler(n: int, rng):
        b = rng.choice(1024, size=n, p=p_b)
        cols = joint[:, b].T  # (n, 1024)
        sums = cols.sum(axis=1)
        out = np.empty_like(cols)
        for i in range(n):
            col, tot = cols[i], sums[i]
            if not np.isfinite(tot) or tot <= 0.0:
                # frozen posterior_rows fallback: zero-mass -> delta-at-0
                col = np.zeros(1024)
                col[0] = 1.0
                tot = 1.0
            else:
                col = col / tot
            u = rng.choice(1024, p=col)
            out[i] = col[_idx1024 ^ int(u)]
        return out
    return sampler


def _assert_sampler_shape(sampler, q: int) -> None:
    """Pre-DE (n,q)-shape gate: probe sampler(4) on an isolated fixed-seed
    RNG, refuse (rc=2) on shape mismatch BEFORE any DE call. This gate would
    have caught D5 (SECONDARY q=1024 bound to an (n,32) sampler). The probe
    RNG is isolated — DE randomness untouched; probing is not a DE call."""
    import numpy as np
    try:
        probe = np.asarray(sampler(4, np.random.default_rng(0)))
    except Refusal:
        raise
    except Exception as exc:  # noqa: BLE001 — fail closed on probe failure
        refuse(f"sampler probe failed for q={q}: {type(exc).__name__}: {exc}")
    if probe.shape != (4, int(q)):
        refuse(f"sampler/q mismatch: sampler -> {tuple(probe.shape)} "
               f"!= (n=4, q={q})")


def validate_result_row(row: dict) -> None:
    """Degree profiles ONLY flow into results; construction-shaped output
    fails closed (execution-side ban assert)."""
    assert_no_construction(row)


def layer_efficiency(rate: float, h_meas: float, width: int) -> float:
    return (1.0 - rate) * width / h_meas


def recompute_expected() -> dict:
    """Pure-arithmetic verify path: nominal m/leak/rate + implied f vs the
    frozen worst-source H anchors (no DE, no channel)."""
    out = {}
    for m in M_GRID:
        rate = 1 - m / N_FRAME
        leak = 10 * m + 64
        out[str(m)] = {"rate": rate, "leak": leak,
                       "f_implied": 10 * m / (N_FRAME * H_TOTAL_ANCHOR)}
    return out


def propose_trial(rng, pop: list[list[float]] | None,
                  current: list[float] | None) -> dict:
    """Sparse-simplex trial over DV_SUPPORT (K<=4 support, min weight 0.05,
    sum 1±1e-12; rho always via make_rho downstream; polish OFF)."""
    import numpy as np
    n = len(DV_SUPPORT)
    if current is None or pop is None or len(pop) < 4 or rng.random() < 0.3:
        k = int(rng.integers(1, OUTER_DE["sparse_K"] + 1))
        idx = rng.choice(n, size=k, replace=False)
        w = np.array(rng.random(k) + 0.2)
    else:
        pick = rng.choice(len(pop), size=3, replace=False)
        a, b, c = (np.array(pop[i]) for i in pick)
        v = np.array(current) + DE_MUT_F * (b - c)
        mask = rng.random(n) < DE_MUT_CR
        v = np.where(mask, v, np.array(current))
        order = np.argsort(v)[::-1]
        k = int(rng.integers(1, OUTER_DE["sparse_K"] + 1))
        idx, w = order[:k], np.maximum(v[order[:k]], 0.0) + 1e-6
        _ = a  # DE base drawn from pop triple (rand/1 form)
    w = np.maximum(w, 0.0)
    w = w + OUTER_DE["min_weight"]
    w = w / w.sum()
    lam = {int(DV_SUPPORT[int(i)]): float(w[j]) for j, i in enumerate(idx)}
    for dv in lam:
        if dv > DV_CEILING:
            return {"terminal": "BOUND_HIT", "lambda": lam}
    tot = sum(lam.values())
    if abs(tot - 1.0) > 1e-12:
        refuse(f"trial lambda unnormalized (sum={tot})")
    return {"lambda": lam}


def run_once(ledger: Ledger, seen: set, identity: tuple, de_fn,
             clock, arm: str, kind: str, call_kwargs: dict) -> tuple[str, dict | None]:
    """One ledger-charged DE call with overlap-dedupe (same identity twice ->
    second skipped, never rerun), per-call timing, and no-retry (crash ->
    error retained, caller halts terminally, no second attempt)."""
    if identity in seen:
        return "skipped", None
    _sampler, _q = call_kwargs.get("channel_sampler"), call_kwargs.get("q")
    if _sampler is not None and _q is not None:
        _assert_sampler_shape(_sampler, int(_q))  # fail closed pre-DE (D5)
    ledger.charge(arm, kind)  # refuse-before-exceed, pre-call
    t0 = clock()
    try:
        res = de_fn(**call_kwargs)
    except Exception as exc:  # noqa: BLE001 — no-retry: retain + STOP
        return "error", {"error": f"{type(exc).__name__}: {exc}"}
    dt = clock() - t0
    seen.add(identity)
    return ("overrun" if dt > BUDGETS["per_call_s"] else "ok",
            {"result": res, "elapsed_s": dt})


def execute_arm(arm: str, bundle: dict, samplers: dict, ledger: Ledger,
                seen: set, de_fn, clock, rss_fn, t_start: float,
                rows: list[dict], l1_lambda: dict, checkpoint_fn=None,
                resume_snapshot=None) -> str:
    """Frozen D-de loop for one arm. Returns the arm terminal.

    Kill-safe delta (no science change): optional ``checkpoint_fn`` is called
    after EVERY completed DE evaluation (overwrite-in-place manifest+rows, same
    schema + verbatim seen-set/ledger); optional ``resume_snapshot`` restores
    the exact outer-loop state (RNG + cur/pop/slots + indices) so a resumed run
    replays the identical trial sequence and charges only missing identities.
    Defaults (both None) preserve the frozen single-shot behavior exactly.
    """
    import copy
    import numpy as np
    pop, gens = POP_GEN[arm]
    width = LAYER_WIDTH[arm]
    q = 32 if arm == "PRIMARY" else 1024
    # D5 fix: SECONDARY is direct-q1024 full-symbol joint P(U1,U2|B)=g1·g2,
    # NOT the (n,32) L1 layer sampler; PRIMARY stays on the L2 sampler.
    skey = "L2" if arm == "PRIMARY" else "JOINT"
    if skey not in samplers:
        refuse(f"missing sampler binding for arm {arm} (key {skey})")
    _assert_sampler_shape(samplers[skey], q)  # fail closed pre-any-DE-call
    seed_off = 0 if arm == "PRIMARY" else 1
    if resume_snapshot is not None:
        rs = _normalize_snapshot(resume_snapshot, arm)
        if rs["phase"] == "done":
            return ""  # already complete: zero calls, gate downstream
        rng = np.random.default_rng()
        rng.bit_generator.state = dict(rs["rng_state"])
        cur = [None if c is None else list(c) for c in rs["cur"]]
        cur_fit = list(rs["cur_fit"])
        pop_vec = [list(v) for v in rs["pop_vec"]]
        slots = [{**sl, "lambda": dict(sl["lambda"])} for sl in rs["slots"]]
        g0, i0 = int(rs["g"]), int(rs["i"])
        resume_phase = rs["phase"]
        resume_winners = rs["winners"]
        resume_cidx = int(rs["confirm_idx"])
        resume_mid_lam = rs.get("mid_lam", None)
        resume_mid_fits = rs.get("mid_fits", None)
        resume_mid_si = rs.get("mid_si", None)
    else:
        rng = np.random.default_rng(SCREEN_SEEDS[0] + seed_off)
        cur = [None] * pop
        cur_fit = [float("inf")] * pop
        pop_vec = [[0.0] * len(DV_SUPPORT) for _ in range(pop)]
        slots = []
        g0, i0 = 0, 0
        resume_phase = "screen"
        resume_winners = None
        resume_cidx = 0
        resume_mid_lam = resume_mid_fits = resume_mid_si = None

    def gate_check():
        if clock() - t_start > BUDGETS["wall_total_s"]:
            return "resource_blocked"
        if rss_fn() >= BUDGETS["rss_gib"] * (1024 ** 3):
            return "resource_blocked"
        return "ok"

    def _snap(phase, g, i, cidx, winners,
                mid_lam=None, mid_fits=None, mid_si=None):
        # Mid-trial persist: current-trial lam + partial fits + next si.
        # Trial-boundary snapshots carry all three as None (exact current
        # behavior). Mid-trial (after screen si=0) carries lam + [fit0] + 1
        # so resume skips propose_trial and runs only the missing si=1.
        return {"phase": phase, "g": int(g), "i": int(i),
                "confirm_idx": int(cidx),
                "rng_state": copy.deepcopy(rng.bit_generator.state),
                "cur": copy.deepcopy(cur), "cur_fit": list(cur_fit),
                "pop_vec": copy.deepcopy(pop_vec),
                "slots": copy.deepcopy(slots),
                "winners": copy.deepcopy(winners),
                "mid_lam": (None if mid_lam is None
                            else {int(k): float(v)
                                  for k, v in dict(mid_lam).items()}),
                "mid_fits": (None if mid_fits is None
                             else [float(x) for x in mid_fits]),
                "mid_si": (None if mid_si is None else int(mid_si))}

    def _flush(phase, g, i, cidx, winners,
               mid_lam=None, mid_fits=None, mid_si=None):
        if checkpoint_fn is not None:
            checkpoint_fn(_snap(phase, g, i, cidx, winners,
                                mid_lam, mid_fits, mid_si))

    if resume_phase == "confirm":
        # Screen already complete: jump straight to confirm with restored state.
        winners = [({**sl, "lambda": dict(sl["lambda"])}, int(s))
                   for sl, s in resume_winners]
    else:
        mid_pending = (resume_snapshot is not None
                       and resume_phase == "screen"
                       and resume_mid_lam is not None)
        for g in range(gens):
            for i in range(pop):
                if g < g0 or (g == g0 and i < i0):
                    continue  # already-completed trial: RNG already past it
                if gate_check() != "ok":
                    return "resource_blocked"
                if mid_pending and g == g0 and i == i0:
                    # Mid-trial resume: SKIP propose_trial (RNG already past
                    # it), reuse persisted lam, re-derive rho via make_rho.
                    lam = dict(resume_mid_lam)
                    validate_lambda(lam)
                    mid_si = int(resume_mid_si)
                else:
                    trial = propose_trial(rng, pop_vec if g else None, cur[i])
                    if trial.get("terminal") == "BOUND_HIT":
                        return "BOUND_HIT"
                    lam = trial["lambda"]
                    validate_lambda(lam)
                    mid_si = 0
                slot = g * pop + i
                # F1 branch separation: PRIMARY layer-local grid ONLY, never
                # M_GRID (no shared-path fallback); SECONDARY keeps M_GRID.
                if arm == "PRIMARY":
                    m = PRIMARY_M2_GRID[slot % len(PRIMARY_M2_GRID)]
                else:
                    m = M_GRID[slot % len(M_GRID)]
                rate = 1 - m / N_FRAME
                rho = _K.make_rho(rate, lam)  # rho always via make_rho
                validate_rho(rho)
                fits = []
                if mid_pending and g == g0 and i == i0:
                    # Reuse cached fit for si=0 (persisted row, never rerun).
                    ident0 = (arm, "screen", m, SCREEN_SEEDS[0], slot,
                              tuple(sorted(lam.items())),
                              tuple(sorted(rho.items())))
                    cached0 = _find_cached_fit(rows, ident0)
                    if cached0 is not None:
                        fits.append(cached0)
                    elif resume_mid_fits:
                        fits.append(float(resume_mid_fits[0]))
                last = len(SCREEN_SEEDS) - 1
                for si, s in enumerate(SCREEN_SEEDS):
                    if mid_pending and g == g0 and i == i0 and si < mid_si:
                        continue  # already persisted: run ONLY missing si=1
                    ident = (arm, "screen", m, s, slot,
                             tuple(sorted(lam.items())),
                             tuple(sorted(rho.items())))
                    st, out = run_once(
                        ledger, seen, ident, de_fn, clock, arm, "de",
                        {"q": q, "lambda_edge": lam, "rho_edge": rho,
                         "channel_sampler": samplers[skey],
                          "n_samples": SCREEN["n_samples"],
                         "max_iter": SCREEN["max_iter"], "seed": s,
                         "entropy_tol_bits": SCREEN["tol"],
                         "streak": SCREEN["streak"],
                         "record_entropy": True,
                         "record_channel_entropy": True})
                    if st == "skipped":
                        # Resume mid-trial: cached fit keeps cur/pop identical.
                        cached = _find_cached_fit(rows, ident)
                        if cached is not None:
                            fits.append(cached)
                        continue  # never rerun same identity
                    if st == "error":
                        rows.append({"arm": arm, "phase": "screen", "m": m,
                                     "status": "error", **out})
                        _flush("screen", g, i, 0, None)
                        return "STOP"  # no-retry: retain + halt
                    if st == "overrun":
                        rows.append(_row(arm, "screen", m, rate, s, slot, lam,
                                         rho, out["result"], width, bundle,
                                         out["elapsed_s"], status="overrun"))
                        _flush("screen", g, i, 0, None)
                        return "resource_blocked"  # retain partial, halt
                    if st == "ok":
                        fits.append(out["result"]["final_entropy_bits"])
                        rows.append(_row(arm, "screen", m, rate, s, slot, lam,
                                         rho, out["result"], width, bundle,
                                         out["elapsed_s"]))
                        if si != last:
                            _flush("screen", g, i, 0, None,
                                   mid_lam=lam, mid_fits=list(fits),
                                   mid_si=si + 1)
                    # "skipped" overlap-reuse: never rerun same identity
                fit = sum(fits) / len(fits) if fits else float("inf")
                if fit < cur_fit[i]:
                    cur_fit[i], cur[i] = fit, [lam[d] if d in lam else 0.0
                                               for d in DV_SUPPORT]
                    pop_vec[i] = list(cur[i])
                slots.append({"slot": slot, "m": m, "rate": rate,
                              "lambda": lam, "fit": fit})
                # Advance to next trial (persisted with the second-seed flush).
                ni, ng = i + 1, g
                if ni >= pop:
                    ni, ng = 0, g + 1
                _flush("screen", ng, ni, 0, None)
                if mid_pending and g == g0 and i == i0:
                    mid_pending = False  # mid-trial consumed; rest boundary
        # Confirm: PRIMARY all slots x 1 reuse seed; SECONDARY top-5/m x 2 seeds.
        if arm == "PRIMARY":
            winners = [(sl, s) for sl in slots for s in (CONFIRM_SEEDS[0],)]
        else:
            by_m: dict[int, list] = {}
            for sl in slots:
                by_m.setdefault(sl["m"], []).append(sl)
            winners = [(sl, s) for m in M_GRID
                       for sl in sorted(by_m.get(m, []),
                                        key=lambda r: r["fit"])[:5]
                       for s in CONFIRM_SEEDS]
        resume_cidx = 0
    for idx in range(resume_cidx, len(winners)):
        sl, s = winners[idx]
        if gate_check() != "ok":
            return "resource_blocked"
        lam = sl["lambda"]
        rho = _K.make_rho(sl["rate"], lam)
        ident = (arm, "confirm", sl["m"], s, sl["slot"],
                 tuple(sorted(lam.items())), tuple(sorted(rho.items())))
        st, out = run_once(
            ledger, seen, ident, de_fn, clock, arm, "de",
            {"q": q, "lambda_edge": lam, "rho_edge": rho,
             "channel_sampler": samplers[skey],
              "n_samples": CONFIRM["n_samples"],
             "max_iter": CONFIRM["max_iter"], "seed": s,
             "entropy_tol_bits": CONFIRM["tol"], "streak": CONFIRM["streak"],
             "record_entropy": True, "record_channel_entropy": True})
        if st == "skipped":
            continue  # already persisted: never rerun, never duplicate
        if st == "error":
            rows.append({"arm": arm, "phase": "confirm", "m": sl["m"],
                         "status": "error", **out})
            _flush("confirm", gens, pop, idx, winners)
            return "STOP"
        if st == "overrun":
            rows.append(_row(arm, "confirm", sl["m"], sl["rate"], s,
                             sl["slot"], lam, rho, out["result"], width,
                             bundle, out["elapsed_s"], status="overrun"))
            _flush("confirm", gens, pop, idx, winners)
            return "resource_blocked"
        if st == "ok":
            rows.append(_row(arm, "confirm", sl["m"], sl["rate"], s,
                             sl["slot"], lam, rho, out["result"], width,
                             bundle, out["elapsed_s"]))
            _flush("confirm", gens, pop, idx + 1, winners)
    _flush("done", gens, pop, len(winners), winners)
    return ""  # gate evaluated downstream (SELECT / NO-IMPROVING)


def _row(arm, phase, m, rate, seed, slot, lam, rho, res, width,
         bundle, elapsed_s, status="ok") -> dict:
    trace = res.get("channel_entropy_trace_bits") or []
    h_meas = (sum(trace) / len(trace)) if trace else None
    row = {"arm": arm, "phase": phase, "m": m, "rate": rate, "seed": seed,
           "slot": slot, "lambda": {str(k): v for k, v in lam.items()},
           "rho": {str(k): v for k, v in rho.items()},
           "converged": res.get("converged"),
           "iterations": res.get("iterations"),
           "final_entropy_bits": res.get("final_entropy_bits"),
           "h_meas_bits": h_meas, "width": width,
           "source": bundle.get("source", EXEC_SOURCE_DEFAULT),
           "elapsed_s": elapsed_s, "status": status}
    if h_meas:
        row["f_row"] = layer_efficiency(rate, h_meas, width)
    validate_result_row(row)  # ban assert: profiles only, fail closed
    return row


def evaluate_gate(rows: list[dict]) -> dict:
    """F2 gate: pass iff ∃ converged confirm row with 1.0 ≤ f_row ≤ 1.15.

    Screens ``converged`` (never max-of-unconverged); empty converged set ⇒
    explicit non-pass (f_ens=None, pass=False, n counts converged rows only).
    f < 1 is a Slepian–Wolf-bound violation: informative failure, never a
    pass, excluded from every pass computation (counted in sw_violations).
    Concrete bars: SECONDARY needs an m=24 config to converge (f_row≈1.126,
    the only grid point ≤1.15); PRIMARY-fixed needs m₂ ≤ 47
    (1.15·H_L2·256/5 ≈ 47.5). f_ens = min over converged valid (best).
    """
    out = {}
    for arm in ("PRIMARY", "SECONDARY"):
        conv = [r for r in rows
                if r["arm"] == arm and r["phase"] == "confirm"
                and r.get("status") == "ok" and r.get("converged") is True
                and "f_row" in r]
        n_viol = sum(1 for r in conv if r["f_row"] < 1.0)
        valid = [r["f_row"] for r in conv if r["f_row"] >= 1.0]
        passing = [f for f in valid if f <= GATE_F_ENS]
        f_ens = min(valid) if valid else None
        out[arm] = {"f_ens": f_ens, "n": len(conv),
                    "pass": bool(passing), "sw_violations": n_viol}
    return out


def evaluate_flip_rule(rows: list[dict]) -> dict:
    """Secondary-vs-primary best-f margin per m. COMPUTE only — never
    auto-promote; promotion is a separate DECIDE gate.

    F2 cross-unit guard: PRIMARY f (width-5 layer units) vs SECONDARY f
    (width-10 full-symbol units) must NOT be compared. Only a shared unit
    basis (equal widths + overlapping m) computes margins; otherwise
    withheld-with-reason (empty margins, flip False, reason in note) — never
    a silent margin. Fixed grids (PRIMARY 44–60 vs SECONDARY 24–31) are
    disjoint by design → withheld.
    """
    best: dict[str, dict[int, float]] = {"PRIMARY": {}, "SECONDARY": {}}
    widths: dict[str, set] = {"PRIMARY": set(), "SECONDARY": set()}
    for arm in best:
        for r in rows:
            if (r["arm"] == arm and r["phase"] == "confirm"
                    and r.get("status") == "ok" and "f_row" in r):
                m = r["m"]
                if m not in best[arm] or r["f_row"] < best[arm][m]:
                    best[arm][m] = r["f_row"]
                if "width" in r:
                    widths[arm].add(r["width"])
    # Cross-unit: explicit widths present on both arms and disjoint/differing
    # → withhold. Legacy width-less fakes (baseline flip test) share the old
    # M_GRID basis → still compute.
    if widths["PRIMARY"] and widths["SECONDARY"] and (
            widths["PRIMARY"] != widths["SECONDARY"]):
        return {"margins": {}, "wins": [], "flip": False,
                "note": "withheld: cross-unit PRIMARY-layer vs "
                        "SECONDARY-full-symbol (distinct widths); no comparison"}
    margins = {m: best["PRIMARY"][m] - best["SECONDARY"][m]
               for m in M_GRID if m in best["PRIMARY"] and m in best["SECONDARY"]}
    if not margins and (set(best["PRIMARY"]) or set(best["SECONDARY"])):
        # Disjoint m sets (fixed grids 44–60 vs 24–31): no shared basis.
        return {"margins": {}, "wins": [], "flip": False,
                "note": "withheld: no shared m basis (PRIMARY m2 44–60 vs "
                        "SECONDARY m 24–31); no cross-unit comparison"}
    wins = [m for m, d in margins.items() if d > FLIP_MARGIN]
    flip = (len(wins) >= FLIP_MIN_PTS
            and all(m in wins for m in FLIP_REQUIRED_M))
    return {"margins": margins, "wins": wins, "flip": flip,
            "note": "computed only; no auto-promotion"}


def _encode_identity(ident: tuple) -> list:
    """JSON-safe completed-identity (persisted verbatim, never reconstructed)."""
    arm, phase, m, s, slot, lam_items, rho_items = ident
    return [arm, phase, int(m), int(s), int(slot),
            [[int(k), float(v)] for k, v in lam_items],
            [[int(k), float(v)] for k, v in rho_items]]


def _decode_identity(lst) -> tuple:
    try:
        arm, phase, m, s, slot, lam_list, rho_list = lst
    except Exception:  # noqa: BLE001 — fail closed on corrupt partial
        refuse("partial completed-identities corrupt (shape)")
    if arm not in ("PRIMARY", "SECONDARY"):
        refuse(f"partial identity unknown arm {arm}")
    if phase not in ("screen", "confirm"):
        refuse(f"partial identity unknown phase {phase}")
    try:
        m_i, s_i, slot_i = int(m), int(s), int(slot)
    except Exception:  # noqa: BLE001
        refuse("partial identity m/seed/slot not ints")
    # F1: per-arm grid binding — PRIMARY m2 44–60 ONLY (never 24–31 reuse).
    _allowed = PRIMARY_M2_GRID if arm == "PRIMARY" else M_GRID
    if m_i not in _allowed:
        refuse(f"partial identity m={m_i} outside {arm} grid")
    if s_i not in list(SCREEN_SEEDS) + list(CONFIRM_SEEDS):
        refuse(f"partial identity seed {s_i} not frozen")
    try:
        lam_items = tuple(sorted((int(k), float(v)) for k, v in lam_list))
        rho_items = tuple(sorted((int(k), float(v)) for k, v in rho_list))
    except Exception:  # noqa: BLE001
        refuse("partial completed-identities corrupt (lam/rho)")
    if not lam_items or not rho_items:
        refuse("partial identity empty lam/rho")
    return (arm, phase, m_i, s_i, slot_i, lam_items, rho_items)


def _ident_sort_key(enc: list) -> str:
    return json.dumps(enc, sort_keys=True, default=str)


def _row_matches_identity(row: dict, ident: tuple) -> bool:
    try:
        arm, phase, m, s, slot, lam_items, rho_items = ident
        if row.get("arm") != arm or row.get("phase") != phase:
            return False
        if int(row.get("m")) != int(m) or int(row.get("seed")) != int(s):
            return False
        if int(row.get("slot")) != int(slot):
            return False
        lam_d = {str(k): float(v) for k, v in lam_items}
        rho_d = {str(k): float(v) for k, v in rho_items}
        rl, rr = row.get("lambda", {}), row.get("rho", {})
        if set(rl.keys()) != set(lam_d.keys()):
            return False
        if set(rr.keys()) != set(rho_d.keys()):
            return False
        for k in lam_d:
            if abs(float(rl[k]) - float(lam_d[k])) > 1e-12:
                return False
        for k in rho_d:
            if abs(float(rr[k]) - float(rho_d[k])) > 1e-12:
                return False
        return True
    except Exception:  # noqa: BLE001 — non-match on any malformed row
        return False


def _find_cached_fit(rows: list[dict], ident: tuple):
    """Resume helper: fit of an already-seen screen identity from loaded rows."""
    for r in rows:
        if not isinstance(r, dict) or r.get("status") != "ok":
            continue
        if _row_matches_identity(r, ident):
            try:
                return float(r["final_entropy_bits"])
            except Exception:  # noqa: BLE001
                return None
    return None


def _build_manifest(ledger: Ledger, rows: list[dict], terminals: dict,
                    gamma_source, source: str, l1_lambda: dict, root: str,
                    completed_enc: list, resume_state: dict,
                    partial: bool) -> dict:
    """Single manifest builder (fresh + checkpoint + final share the schema)."""
    manifest = {"config_hash": config_hash(),
                "recorded_hash": RECORDED_CONFIG_HASH,
                "seeds": {"screen": list(SCREEN_SEEDS),
                          "confirm": list(CONFIRM_SEEDS)},
                "budgets": dict(BUDGETS),
                "caps": dict(CAPS),
                "ledger": dict(ledger.counts),
                "scientific_de_calls": ledger.counts["TOTAL"],
                "terminals": dict(terminals),
                "gate": evaluate_gate(rows),
                "flip_rule": evaluate_flip_rule(rows),
                "recompute_expected": recompute_expected(),
                "provenance": {"kernel": frozen_config()["kernel"],
                               "gamma": (gamma_source if isinstance(
                                   gamma_source, str) else "injected-bundle"),
                               "source": source, "root": root,
                               "l1_fixed": {str(k): v for k, v in
                                            l1_lambda.items()}},
                "n_rows": len(rows),
                "completed_identities": list(completed_enc),
                "resume": dict(resume_state),
                # W-wall-restart: per-turn operational windows (append-only,
                # one entry per invocation; fresh run starts with one). Wall =
                # per-turn operational safety; ledger = frozen scientific
                # budget (continues verbatim, never reset by a new window).
                "wall_windows": list(resume_state.get("wall_windows", [])),
                "partial": bool(partial)}
    manifest["verify"] = verify_manifest(manifest, rows)
    return manifest


def _normalize_lam(d) -> dict:
    try:
        return {int(k): float(v) for k, v in dict(d).items()}
    except Exception:  # noqa: BLE001
        refuse("partial resume lam keys corrupt")


def _normalize_snapshot(snap, arm: str):
    """JSON round-trip restores int lam keys; validate shape, fail closed."""
    if snap is None:
        return None
    if not isinstance(snap, dict) or snap.get("phase") not in (
            "screen", "confirm", "done"):
        refuse(f"partial resume arm {arm} phase corrupt")
    try:
        g = int(snap.get("g", 0))
        i = int(snap.get("i", 0))
        cidx = int(snap.get("confirm_idx", 0))
    except Exception:  # noqa: BLE001
        refuse(f"partial resume arm {arm} indices corrupt")
    rng_state = snap.get("rng_state", None)
    if not isinstance(rng_state, dict) or rng_state.get(
            "bit_generator") != "PCG64":
        refuse(f"partial resume arm {arm} rng_state corrupt")
    cur = snap.get("cur", None)
    cur_fit = snap.get("cur_fit", None)
    pop_vec = snap.get("pop_vec", None)
    slots = snap.get("slots", None)
    winners = snap.get("winners", None)
    pop, _gens = POP_GEN[arm]
    if not isinstance(cur, list) or len(cur) != pop:
        refuse(f"partial resume arm {arm} cur corrupt")
    if not isinstance(cur_fit, list) or len(cur_fit) != pop:
        refuse(f"partial resume arm {arm} cur_fit corrupt")
    if (not isinstance(pop_vec, list) or len(pop_vec) != pop
            or any(not isinstance(v, list) or len(v) != len(DV_SUPPORT)
                   for v in pop_vec)):
        refuse(f"partial resume arm {arm} pop_vec corrupt")
    if not isinstance(slots, list):
        refuse(f"partial resume arm {arm} slots corrupt")
    norm_slots = []
    for sl in slots:
        if not isinstance(sl, dict):
            refuse(f"partial resume arm {arm} slot corrupt")
        norm_slots.append({"slot": int(sl["slot"]), "m": int(sl["m"]),
                           "rate": float(sl["rate"]),
                           "lambda": _normalize_lam(sl["lambda"]),
                           "fit": float(sl["fit"])})
    norm_winners = None
    if winners is not None:
        if not isinstance(winners, list):
            refuse(f"partial resume arm {arm} winners corrupt")
        norm_winners = []
        for w in winners:
            sl, s = w  # [slot_dict, seed]
            norm_winners.append([{"slot": int(sl["slot"]),
                                  "m": int(sl["m"]),
                                  "rate": float(sl["rate"]),
                                  "lambda": _normalize_lam(sl["lambda"]),
                                  "fit": float(sl["fit"])}, int(s)])
    norm_cur = [None if c is None else [float(x) for x in c] for c in cur]
    norm_fit = [float(x) for x in cur_fit]
    norm_pop = [[float(x) for x in v] for v in pop_vec]
    # Mid-trial fields (absent/None on old + trial-boundary snapshots).
    mid_lam_raw = snap.get("mid_lam", None)
    mid_fits_raw = snap.get("mid_fits", None)
    mid_si_raw = snap.get("mid_si", None)
    if mid_lam_raw is None and mid_fits_raw is None and mid_si_raw is None:
        mid_lam = mid_fits = mid_si = None
    else:
        if snap.get("phase") != "screen":
            refuse(f"partial resume arm {arm} mid-trial outside screen")
        if not isinstance(mid_lam_raw, dict) or not mid_lam_raw:
            refuse(f"partial resume arm {arm} mid_lam corrupt")
        mid_lam = _normalize_lam(mid_lam_raw)
        try:
            mid_fits = [float(x) for x in mid_fits_raw]
        except Exception:  # noqa: BLE001
            refuse(f"partial resume arm {arm} mid_fits corrupt")
        try:
            mid_si = int(mid_si_raw)
        except Exception:  # noqa: BLE001
            refuse(f"partial resume arm {arm} mid_si corrupt")
        if mid_si != 1 or len(mid_fits) != 1:
            refuse(f"partial resume arm {arm} mid_si/fits corrupt")
        validate_lambda(mid_lam)
    return {"phase": snap["phase"], "g": g, "i": i,
            "confirm_idx": cidx, "rng_state": rng_state,
            "cur": norm_cur, "cur_fit": norm_fit,
            "pop_vec": norm_pop, "slots": norm_slots,
            "winners": norm_winners,
            "mid_lam": mid_lam, "mid_fits": mid_fits, "mid_si": mid_si}


def _validate_partial(manifest: dict, rows: list,
                      requested_source: str):
    """Fail-closed partial validation BEFORE any DE call (zero calls on refuse).

    Checks: config-hash == RECORDED, seeds/budgets/caps frozen, provenance
    source + l1_fixed, ledger internally consistent (SETUP==12, TOTAL==n_rows,
    per-arm tallies, caps), completed-identities persisted verbatim (no dup,
    each matches an ok/overrun row => completed ⊆ planned rows; overrun rows
    stay completed-but-not-ok so an overrun-halted partial remains resumable
    while the gate still excludes them), resume shape, no
    error rows (no-retry: resume after STOP refuses, zero retry).
    """
    if not isinstance(manifest, dict):
        refuse("partial manifest not a dict")
    if not isinstance(rows, list):
        refuse("partial rows not a list")
    if manifest.get("config_hash") != RECORDED_CONFIG_HASH:
        refuse("partial config-hash mismatch (foreign root)")
    if config_hash() != RECORDED_CONFIG_HASH:
        refuse("config-hash drift vs readiness record; STOP")
    if manifest.get("recorded_hash") != RECORDED_CONFIG_HASH:
        refuse("partial recorded-hash mismatch")
    seeds = manifest.get("seeds", None)
    if (not isinstance(seeds, dict)
            or list(seeds.get("screen", [])) != list(SCREEN_SEEDS)
            or list(seeds.get("confirm", [])) != list(CONFIRM_SEEDS)):
        refuse("partial seeds mismatch frozen")
    if manifest.get("budgets", None) != dict(BUDGETS):
        refuse("partial budgets mismatch frozen")
    if manifest.get("caps", None) != dict(CAPS):
        refuse("partial caps mismatch frozen")
    prov = manifest.get("provenance", {})
    if not isinstance(prov, dict) or prov.get("source") != requested_source:
        refuse("partial source mismatch (fail closed)")
    if prov.get("l1_fixed", {}) != {"2": 1.0}:
        refuse("partial l1_fixed mismatch (must stay {2:1})")
    ledger = manifest.get("ledger", None)
    if (not isinstance(ledger, dict)
            or set(ledger.keys()) != {"PRIMARY", "SECONDARY",
                                      "TOTAL", "SETUP"}):
        refuse("partial ledger corrupt")
    try:
        lp, ls, lt, lu = (int(ledger["PRIMARY"]),
                          int(ledger["SECONDARY"]),
                          int(ledger["TOTAL"]), int(ledger["SETUP"]))
    except Exception:  # noqa: BLE001
        refuse("partial ledger counts not ints")
    if lu != CAPS["SETUP"]:
        refuse(f"partial SETUP {lu} != {CAPS['SETUP']}")
    if (lp < 0 or ls < 0 or lt < 0 or lp > CAPS["PRIMARY"]
            or ls > CAPS["SECONDARY"] or lt > CAPS["TOTAL"]):
        refuse("partial ledger out of caps")
    if lt != lp + ls:
        refuse("partial ledger TOTAL != PRIMARY+SECONDARY")
    if lt != len(rows):
        refuse(f"partial ledger TOTAL {lt} != n_rows {len(rows)}")
    for arm in ("PRIMARY", "SECONDARY"):
        n_arm = sum(1 for r in rows
                    if isinstance(r, dict) and r.get("arm") == arm)
        if n_arm != ledger[arm]:
            refuse(f"partial ledger {arm} {ledger[arm]} != rows {n_arm}")
    for r in rows:
        if isinstance(r, dict) and r.get("status") == "error":
            refuse("partial contains error STOP "
                   "(no-retry: refusing resume, zero retry)")
        if isinstance(r, dict):
            assert_no_construction(r)
    comp = manifest.get("completed_identities", None)
    if not isinstance(comp, list):
        refuse("partial missing completed-identities set "
               "(must persist verbatim)")
    seen: set = set()
    for enc in comp:
        ident = _decode_identity(enc)
        if ident in seen:
            refuse("partial completed-identities duplicate")
        seen.add(ident)
    n_ok = sum(1 for r in rows
               if isinstance(r, dict) and r.get("status") == "ok")
    n_overrun = sum(1 for r in rows
                    if isinstance(r, dict) and r.get("status") == "overrun")
    if len(seen) != n_ok + n_overrun:
        refuse(f"partial completed {len(seen)} != ok+overrun rows "
               f"{n_ok}+{n_overrun}")
    for ident in seen:
        if not any(isinstance(r, dict)
                   and r.get("status") in ("ok", "overrun")
                   and _row_matches_identity(r, ident) for r in rows):
            refuse("partial completed identity without matching row")
    resume = manifest.get("resume", None)
    if not isinstance(resume, dict):
        refuse("partial missing resume snapshot")
    if resume.get("next_arm") not in ("PRIMARY", "SECONDARY", "DONE"):
        refuse("partial resume next_arm corrupt")
    if not isinstance(resume.get("arms", None), dict):
        refuse("partial resume arms corrupt")
    for arm, snap in resume["arms"].items():
        if arm not in ("PRIMARY", "SECONDARY"):
            refuse(f"partial resume unknown arm {arm}")
        if (not isinstance(snap, dict) or snap.get("phase") not in (
                "screen", "confirm", "done")):
            refuse(f"partial resume arm {arm} phase corrupt")
    try:
        wall_start = float(resume.get("wall_start", 0.0))
    except Exception:  # noqa: BLE001
        refuse("partial wall_start corrupt")
    # W-wall-restart: wall_windows is operational (per-turn safety), validated
    # fail-closed when present; absent (pre-wall-windows partial, e.g. the S1
    # 389-call turn) synthesizes a single window from wall_start so the resume
    # still restarts cleanly. Cap must stay the SAME 3600s value; last window
    # must match wall_start verbatim.
    raw_windows = manifest.get("wall_windows", None)
    if raw_windows is None:
        wall_windows_old = [{"turn_start": float(wall_start),
                             "cap": BUDGETS["wall_total_s"]}]
    else:
        if not isinstance(raw_windows, list) or not raw_windows:
            refuse("partial wall_windows corrupt (non-empty list required)")
        wall_windows_old = []
        for w in raw_windows:
            if not isinstance(w, dict):
                refuse("partial wall_windows entry corrupt (not a dict)")
            try:
                ts = float(w.get("turn_start"))
                cap = w.get("cap")
            except Exception:  # noqa: BLE001
                refuse("partial wall_windows entry corrupt (turn_start/cap)")
            if cap != BUDGETS["wall_total_s"]:
                refuse("partial wall_windows cap mismatch frozen (same 3600s)")
            wall_windows_old.append({"turn_start": float(ts), "cap": cap})
        if (wall_windows_old[-1]["turn_start"] != float(wall_start)):
            refuse("partial wall_windows last turn_start != wall_start")
    return ({"PRIMARY": lp, "SECONDARY": ls,
             "TOTAL": lt, "SETUP": lu}, seen, resume, wall_start,
            wall_windows_old)


def _load_partial_fs(partial_root: str):
    try:
        with open(os.path.join(partial_root, "manifest.json")) as fh:
            manifest = json.load(fh)
        with open(os.path.join(partial_root, "rows.json")) as fh:
            rows = json.load(fh)
    except Refusal:
        raise
    except Exception as exc:  # noqa: BLE001 — fail closed, zero DE calls
        refuse(f"partial load failed ({partial_root}): "
               f"{type(exc).__name__}: {exc}")
    return manifest, rows


def verify_manifest(manifest: dict, rows: list[dict]) -> dict:
    """Recompute path: config-hash, f_ens decomposition, per-arm breakdown
    and H-anchor recompute re-derived from rows (never trusted blind).

    F2: verify.ok is hash + gate-recompute consistency ONLY — NOT gate
    adjudication. Pass/fail lives in gate[arm]["pass"]; no caller may treat
    verify.ok as a pass verdict.
    """
    gate = evaluate_gate(rows)
    ok = (manifest["config_hash"] == RECORDED_CONFIG_HASH
          and manifest["gate"] == gate)
    return {"hash_ok": manifest["config_hash"] == RECORDED_CONFIG_HASH,
            "gate_recomputed": gate,
            "gate_match": manifest["gate"] == gate,
            "recompute_expected": recompute_expected(),
            "anchors": dict(H_ANCHORS),
            "note": "verify.ok is non-adjudicating (hash + gate-recompute "
                    "consistency only); pass/fail lives in gate[arm]['pass']",
            "ok": ok}


def default_writer(root: str, files: dict[str, str]) -> None:
    # Single-writer overwrite-in-place (research code): root-fresh policy is
    # enforced in execute() (fail closed); the writer allows per-eval
    # checkpoint rewrites + resume overwrites of the same scratch root.
    os.makedirs(root, exist_ok=True)
    for name, blob in files.items():
        with open(os.path.join(root, name), "w") as fh:
            fh.write(blob)


def execute(*, root: str = FROZEN_ROOT, gamma_source=GAMMA_DEFAULT,
            source: str = EXEC_SOURCE_DEFAULT, l1_lambda: dict | None = None,
            de_fn=None, clock=None, rss_fn=None, writer=None,
            samplers: dict | None = None,
            resume_from: str | None = None) -> dict:
    """Frozen D-de execution. Pre-checks (L1 fixed, root fresh, gamma bound,
    hash) run BEFORE any DE call; ledger/resource/no-retry enforced live.

    Kill-safe delta (no science change): per-eval checkpoint flush rewrites
    manifest.json + rows.json after EVERY completed DE evaluation (same schema
    + verbatim seen-set/ledger + resume snapshot, overwrite-in-place, single
    writer). Explicit resume via ``resume_from`` (default OFF): fresh runs
    require root ABSENT; resume loads + validates the partial (hash/seeds/
    budgets/ledger/identities) BEFORE any DE call and continues ONLY missing
    identities. Never silent auto-resume.
    """
    import time
    de_fn = de_fn or _K.run_mcde_posterior
    clock = clock or time.monotonic
    rss_fn = rss_fn or _default_rss
    writer = writer or default_writer
    l1_lambda = {2: 1.0} if l1_lambda is None else l1_lambda
    if l1_lambda != {2: 1.0} or 2 not in l1_lambda or len(l1_lambda) != 1:
        refuse("L1 lambda must stay fixed {2:1}; no L1 search path exists")
    if resume_from is not None:
        # Explicit resume: root must equal the partial root (fail closed on
        # ambiguity); absent/invalid partial refuses rc2 with zero DE calls.
        if root != resume_from:
            refuse("root/resume-from mismatch (fail closed: pass same path)")
        if not os.path.exists(resume_from):
            refuse(f"nothing to resume (absent): {resume_from}")
        manifest_p, rows_p = _load_partial_fs(resume_from)
        counts, seen, resume_loaded, _wall_old, wall_windows_old = (
            _validate_partial(manifest_p, rows_p, source))
        bundle = bind_gamma(gamma_source, source)  # fail closed pre-DE
        if config_hash() != RECORDED_CONFIG_HASH:
            refuse("config-hash drift vs readiness record; STOP")
        samplers = samplers or {"L1": make_centered_sampler(bundle, "L1"),
                                "L2": make_centered_sampler(bundle, "L2"),
                                "JOINT": make_joint_sampler(bundle)}
        ledger = Ledger()
        ledger.counts = dict(counts)  # CONTINUE verbatim: never reset,
        # never double-charge (missing identities only, via seen-set dedupe)
        rows = list(rows_p)
        # W-wall-restart: wall = per-turn OPERATIONAL safety (fresh window at
        # resume time, SAME 3600s cap value); the SCIENTIFIC budget is the DE
        # ledger (600+12, frozen, continues verbatim across resume). First
        # turn consumed ~3584s for 389 calls; resume needs a fresh wall
        # window, not a budget extension.
        t_start = clock()
        wall_windows = list(wall_windows_old) + [
            {"turn_start": float(t_start), "cap": BUDGETS["wall_total_s"]}]
        resume_state = {"next_arm": resume_loaded.get("next_arm", "PRIMARY"),
                        "arms": dict(resume_loaded.get("arms", {})),
                        "wall_start": float(t_start),
                        "wall_windows": wall_windows}

        def _ckpt_resume(arm, snap):
            resume_state["arms"][arm] = snap
            comp = sorted((_encode_identity(i) for i in seen),
                          key=_ident_sort_key)
            mf = _build_manifest(
                ledger, rows, {}, gamma_source, source, l1_lambda, root,
                comp, {"next_arm": resume_state["next_arm"],
                       "arms": dict(resume_state["arms"]),
                       "wall_start": resume_state["wall_start"],
                       "wall_windows": list(
                           resume_state["wall_windows"])},
                partial=True)
            writer(root, {"manifest.json": json.dumps(
                mf, indent=1, sort_keys=True, default=str),
                "rows.json": json.dumps(rows, indent=1, sort_keys=True,
                                        default=str)})

        order = ("PRIMARY", "SECONDARY")
        terminals: dict[str, str] = {}
        if resume_state["next_arm"] == "DONE":
            for arm in order:
                gate = evaluate_gate([r for r in rows if r["arm"] == arm])
                terminals[arm] = ("SELECT" if gate[arm]["pass"]
                                  else "NO-IMPROVING")
        else:
            start = order.index(resume_state["next_arm"])
            for arm in order[start:]:
                resume_state["next_arm"] = arm
                snap = _normalize_snapshot(
                    resume_state["arms"].get(arm, None), arm)
                term = execute_arm(
                    arm, bundle, samplers, ledger, seen, de_fn, clock,
                    rss_fn, t_start, rows, l1_lambda,
                    checkpoint_fn=lambda s, _a=arm: _ckpt_resume(_a, s),
                    resume_snapshot=snap)
                if not term:
                    gate = evaluate_gate(
                        [r for r in rows if r["arm"] == arm])
                    term = ("SELECT" if gate[arm]["pass"]
                            else "NO-IMPROVING")
                terminals[arm] = term
                if term in ("resource_blocked", "STOP", "BOUND_HIT"):
                    break  # halt; retain partial; never resume silently
            for arm in order[:start]:
                if arm not in terminals:
                    gate = evaluate_gate(
                        [r for r in rows if r["arm"] == arm])
                    terminals[arm] = ("SELECT" if gate[arm]["pass"]
                                      else "NO-IMPROVING")
        if (len(terminals) == 2 and all(
                v not in ("resource_blocked", "STOP", "BOUND_HIT")
                for v in terminals.values())):
            resume_state["next_arm"] = "DONE"
        comp = sorted((_encode_identity(i) for i in seen),
                      key=_ident_sort_key)
        manifest = _build_manifest(
            ledger, rows, terminals, gamma_source, source, l1_lambda, root,
            comp, {"next_arm": resume_state["next_arm"],
                   "arms": dict(resume_state["arms"]),
                   "wall_start": resume_state["wall_start"],
                   "wall_windows": list(resume_state["wall_windows"])},
            partial=(resume_state["next_arm"] != "DONE"))
        writer(root, {"manifest.json": json.dumps(
            manifest, indent=1, sort_keys=True, default=str),
            "rows.json": json.dumps(rows, indent=1, sort_keys=True,
                                    default=str)})
        return manifest
    if os.path.exists(root):
        refuse(f"root not fresh: {root}")
    bundle = bind_gamma(gamma_source, source)  # fail closed pre-DE
    if config_hash() != RECORDED_CONFIG_HASH:
        refuse("config-hash drift vs readiness record; STOP")
    samplers = samplers or {"L1": make_centered_sampler(bundle, "L1"),
                            "L2": make_centered_sampler(bundle, "L2"),
                            "JOINT": make_joint_sampler(bundle)}
    ledger, seen, rows = Ledger(), set(), []
    t_start = clock()
    for _m in M_GRID:  # 8 rate targets
        ledger.charge("SETUP", "setup")
    ledger.charge("SETUP", "setup")  # perm table q32
    ledger.charge("SETUP", "setup")  # perm table q1024
    ledger.charge("SETUP", "setup")  # config_hash
    ledger.charge("SETUP", "setup")  # plan check
    resume_state = {"next_arm": "PRIMARY", "arms": {},
                    "wall_start": float(t_start),
                    "wall_windows": [{"turn_start": float(t_start),
                                      "cap": BUDGETS["wall_total_s"]}]}

    def _ckpt_fresh(arm, snap):
        resume_state["arms"][arm] = snap
        comp = sorted((_encode_identity(i) for i in seen),
                      key=_ident_sort_key)
        mf = _build_manifest(
            ledger, rows, {}, gamma_source, source, l1_lambda, root,
            comp, {"next_arm": resume_state["next_arm"],
                   "arms": dict(resume_state["arms"]),
                   "wall_start": resume_state["wall_start"],
                   "wall_windows": list(resume_state["wall_windows"])},
            partial=True)
        writer(root, {"manifest.json": json.dumps(
            mf, indent=1, sort_keys=True, default=str),
            "rows.json": json.dumps(rows, indent=1, sort_keys=True,
                                    default=str)})

    terminals = {}
    for arm in ("PRIMARY", "SECONDARY"):
        resume_state["next_arm"] = arm
        term = execute_arm(arm, bundle, samplers, ledger, seen, de_fn,
                           clock, rss_fn, t_start, rows, l1_lambda,
                           checkpoint_fn=lambda s, _a=arm: _ckpt_fresh(_a, s),
                           resume_snapshot=None)
        if not term:  # gate decision downstream of the loop
            gate = evaluate_gate([r for r in rows if r["arm"] == arm])
            term = "SELECT" if gate[arm]["pass"] else "NO-IMPROVING"
        terminals[arm] = term
        if term in ("resource_blocked", "STOP", "BOUND_HIT"):
            break  # halt; retain partial; never resume silently
    if (len(terminals) == 2 and all(
            v not in ("resource_blocked", "STOP", "BOUND_HIT")
            for v in terminals.values())):
        resume_state["next_arm"] = "DONE"
    comp = sorted((_encode_identity(i) for i in seen),
                  key=_ident_sort_key)
    manifest = _build_manifest(
        ledger, rows, terminals, gamma_source, source, l1_lambda, root,
        comp, {"next_arm": resume_state["next_arm"],
               "arms": dict(resume_state["arms"]),
               "wall_start": resume_state["wall_start"],
               "wall_windows": list(resume_state["wall_windows"])},
        partial=(resume_state["next_arm"] != "DONE"))
    writer(root, {"manifest.json": json.dumps(manifest, indent=1,
                                              sort_keys=True, default=str),
                  "rows.json": json.dumps(rows, indent=1,
                                          sort_keys=True, default=str)})
    return manifest


def _default_rss() -> int:
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    except Exception:  # noqa: BLE001 — RSS probe is best-effort only
        return 0


def run_execution(root: str, gamma_source, source: str,
                  resume_from: str | None = None) -> int:
    manifest = execute(root=root, gamma_source=gamma_source, source=source,
                       resume_from=resume_from)
    print(json.dumps({"terminals": manifest["terminals"],
                      "ledger": manifest["ledger"],
                      "scientific_de_calls": manifest["scientific_de_calls"],
                      "gate": manifest["gate"],
                      "flip_rule": manifest["flip_rule"],
                      "root": root}, indent=1, sort_keys=True, default=str))
    return 0


# ------------------------------------------------- G-REPRO gate (packet 2026-09-20)
# Gate-local ONLY: nothing in this section enters frozen_config(), so
# config_hash() stays 60ab1e44…0da (hash-neutrality pinned by tests).
# Each cell re-evaluates the frozen m2=47 slot-105 winner profile
# (lambda {2:1.0}) in ONE DE call with CONFIRM sampling params; restart r
# varies ONLY the gate-local seed seed_eff = base_seed + r*7919 (r=0
# recovers the exact frozen seeds). pop10xgen14 is the frozen outer-search
# shape the winner came from (provenance only, recorded in the manifest).
REPRO_M2 = (46, 47, 48)
REPRO_N_RESTARTS = 5
REPRO_RESTART_STEP = 7919
REPRO_LAMBDA = {2: 1.0}
REPRO_Q = 32
REPRO_ARM = "PRIMARY"
REPRO_WIDTH = LAYER_WIDTH["PRIMARY"]
H_FULL_ANCHOR = 0.83256272  # frozen whole-frame-with-tag content anchor
REPRO_PASS_LO = 1.0
REPRO_PASS_HI = GATE_F_ENS  # 1.15, frozen gate bound
REPRO_MIN_PER_SEED = 3  # >=3/5 passing restarts on EACH m47 seed
REPRO_STAB_HALF = 0.02  # pooled converged-m47 f range <= 2*half (0.04)
REPRO_ROOT_PREFIX = "workspace/s1_repro_"


def repro_seed(base_seed: int, restart: int) -> int:
    """Gate-local restart derivation (outside frozen_config)."""
    return int(base_seed) + int(restart) * REPRO_RESTART_STEP


def build_repro_plan() -> list[dict]:
    """30 confirm cells: m2 x CONFIRM_SEEDS x R=5 restarts. No DE, no RNG."""
    cells = [{"m": m, "base_seed": s, "restart": r,
              "seed_eff": repro_seed(s, r)}
             for m in REPRO_M2 for s in CONFIRM_SEEDS
             for r in range(REPRO_N_RESTARTS)]
    assert (len(cells) == len(REPRO_M2) * len(CONFIRM_SEEDS)
            * REPRO_N_RESTARTS == 30)
    return cells


def superframe_efficiency(m2: int) -> float:
    """Frozen whole-frame-with-tag superframe-n=1024 f (packet §5).

    Single-frame leak = 5*m_total + 64 (m_total = m2 + 2); superframe
    leak = 4*5*m_total + 64; content = 1024*H_full (H_full = 0.83256272).
    m2=47 -> 1044 / 852.54 ≈ 1.22.
    """
    m_total = int(m2) + 2
    return (4 * 5 * m_total + 64) / (1024 * H_FULL_ANCHOR)


def evaluate_repro_gate(rows: list[dict]) -> dict:
    """Frozen G-REPRO bar arithmetic (packet §2): m2=47 per-cell passes
    (converged AND 1.0<=f_row<=1.15) >= 3/5 on BOTH seeds AND pooled
    converged-m47 f range <= 0.04. Pure arithmetic; no interpretation."""
    per_seed = {(47, s): {"n_pass": 0, "fs_pass": []}
                for s in CONFIRM_SEEDS}
    conv47: list[float] = []
    for r in rows:
        if not (r.get("arm") == REPRO_ARM and r.get("phase") == "confirm"
                and r.get("status") == "ok"
                and r.get("converged") is True and "f_row" in r):
            continue
        try:
            f = float(r["f_row"])
        except Exception:  # noqa: BLE001 — malformed row never counts
            continue
        if int(r.get("m", -1)) != 47 or r.get("base_seed") not in CONFIRM_SEEDS:
            continue
        conv47.append(f)
        if REPRO_PASS_LO <= f <= REPRO_PASS_HI:
            slot = per_seed[(47, r["base_seed"])]
            slot["n_pass"] += 1
            slot["fs_pass"].append(f)
    n0 = per_seed[(47, CONFIRM_SEEDS[0])]["n_pass"]
    n1 = per_seed[(47, CONFIRM_SEEDS[1])]["n_pass"]
    frange = (max(conv47) - min(conv47)) if conv47 else None
    passed = (n0 >= REPRO_MIN_PER_SEED and n1 >= REPRO_MIN_PER_SEED
              and frange is not None and frange <= 2 * REPRO_STAB_HALF)
    return {"m47_per_seed_pass": {str(CONFIRM_SEEDS[0]): n0,
                                  str(CONFIRM_SEEDS[1]): n1},
            "m47_min_per_seed": REPRO_MIN_PER_SEED,
            "m47_converged_n": len(conv47),
            "m47_f_range": frange,
            "m47_stab_band": 2 * REPRO_STAB_HALF,
            "pass": bool(passed)}


def execute_repro(*, root: str, gamma_source=GAMMA_DEFAULT,
                  source: str = EXEC_SOURCE_DEFAULT, de_fn=None,
                  clock=None, rss_fn=None, writer=None,
                  samplers: dict | None = None) -> dict:
    """Frozen G-REPRO execution: ONLY the 30 gate cells, single-turn.

    Fresh additive root required (present -> refuse rc=2, zero DE calls).
    No resume (no resume_from parameter exists); NO_RETRY (error retains +
    STOP); per-call cap + wall/RSS halt (resource_blocked, partial
    retained); checkpoint-per-eval manifest+rows flush. Setup ledger stays
    0: the 30 DE calls are the entire scientific spend (frozen S1 setup
    accounting already covers rate targets/perm/hash/plan).
    """
    import time
    de_fn = de_fn or _K.run_mcde_posterior
    clock = clock or time.monotonic
    rss_fn = rss_fn or _default_rss
    writer = writer or default_writer
    if os.path.exists(root):
        refuse(f"repro root not fresh: {root}")
    if config_hash() != RECORDED_CONFIG_HASH:
        refuse("config-hash drift vs readiness record; STOP")
    bundle = bind_gamma(gamma_source, source)  # fail closed pre-DE
    samplers = samplers or {"L2": make_centered_sampler(bundle, "L2")}
    if "L2" not in samplers:
        refuse("repro missing L2 sampler binding (fail closed)")
    _assert_sampler_shape(samplers["L2"], REPRO_Q)  # fail closed pre-any-DE
    ledger, seen, rows = Ledger(), set(), []
    t_start = clock()
    cells = build_repro_plan()

    def _ckpt(terminals: dict, partial: bool) -> dict:
        manifest = {"mode": "repro-gate",
                    "config_hash": config_hash(),
                    "recorded_hash": RECORDED_CONFIG_HASH,
                    "cells_planned": len(cells),
                    "cells_completed": len(rows),
                    "m2": list(REPRO_M2),
                    "seeds": {"confirm": list(CONFIRM_SEEDS)},
                    "n_restarts": REPRO_N_RESTARTS,
                    "restart_step": REPRO_RESTART_STEP,
                    "repro_lambda": {str(k): v for k, v in
                                     REPRO_LAMBDA.items()},
                    "outer_search_shape": list(POP_GEN["PRIMARY"]),
                    "confirm": dict(CONFIRM),
                    "budgets": dict(BUDGETS),
                    "ledger": dict(ledger.counts),
                    "scientific_de_calls": ledger.counts["TOTAL"],
                    "terminals": dict(terminals),
                    "repro_gate": evaluate_repro_gate(rows),
                    "gate": evaluate_gate(rows),
                    "h_full_anchor": H_FULL_ANCHOR,
                    "provenance": {
                        "kernel": frozen_config()["kernel"],
                        "gamma": (gamma_source if isinstance(
                            gamma_source, str) else "injected-bundle"),
                        "source": source, "root": root,
                        "winner": ("PRIMARY m2=47 slot-105 "
                                   "lambda {2:1.0}")},
                    "n_rows": len(rows),
                    "partial": bool(partial)}
        manifest["verify"] = verify_manifest(manifest, rows)
        writer(root, {"manifest.json": json.dumps(
            manifest, indent=1, sort_keys=True, default=str),
            "rows.json": json.dumps(rows, indent=1, sort_keys=True,
                                    default=str)})
        return manifest

    terminal = ""
    for idx, cell in enumerate(cells):
        if clock() - t_start > BUDGETS["wall_total_s"]:
            terminal = "resource_blocked"
            break
        if rss_fn() >= BUDGETS["rss_gib"] * (1024 ** 3):
            terminal = "resource_blocked"
            break
        m, seff = int(cell["m"]), int(cell["seed_eff"])
        rate = 1 - m / N_FRAME
        lam = dict(REPRO_LAMBDA)
        rho = _K.make_rho(rate, lam)  # rho always via make_rho
        validate_lambda(lam)
        validate_rho(rho)
        ident = (REPRO_ARM, "confirm", m, seff, idx,
                 tuple(sorted(lam.items())), tuple(sorted(rho.items())))
        st, out = run_once(
            ledger, seen, ident, de_fn, clock, REPRO_ARM, "de",
            {"q": REPRO_Q, "lambda_edge": lam, "rho_edge": rho,
             "channel_sampler": samplers["L2"],
             "n_samples": CONFIRM["n_samples"],
             "max_iter": CONFIRM["max_iter"], "seed": seff,
             "entropy_tol_bits": CONFIRM["tol"],
             "streak": CONFIRM["streak"],
             "record_entropy": True,
             "record_channel_entropy": True})
        if st == "skipped":
            continue  # fresh single-turn: unreachable; never rerun
        if st == "error":
            rows.append({"arm": REPRO_ARM, "phase": "confirm", "m": m,
                         "seed": seff, "base_seed": cell["base_seed"],
                         "restart": cell["restart"],
                         "status": "error", **out})
            _ckpt({"REPRO": "STOP"}, True)
            terminal = "STOP"
            break
        row = _row(REPRO_ARM, "confirm", m, rate, seff, idx, lam, rho,
                   out["result"], REPRO_WIDTH, bundle, out["elapsed_s"],
                   status=st)
        row["base_seed"] = cell["base_seed"]
        row["restart"] = cell["restart"]
        row["f_superframe"] = superframe_efficiency(m)
        rows.append(row)
        if st == "overrun":
            _ckpt({"REPRO": "resource_blocked"}, True)
            terminal = "resource_blocked"
            break
        _ckpt({"REPRO": "RUNNING"}, True)
    if not terminal:
        terminal = "COMPLETE"
    return _ckpt({"REPRO": terminal}, terminal != "COMPLETE")


def run_repro_execution(root: str, gamma_source, source: str) -> int:
    manifest = execute_repro(root=root, gamma_source=gamma_source,
                             source=source)
    print(json.dumps({"mode": "repro-gate",
                      "terminals": manifest["terminals"],
                      "ledger": manifest["ledger"],
                      "scientific_de_calls":
                          manifest["scientific_de_calls"],
                      "repro_gate": manifest["repro_gate"],
                      "root": root}, indent=1, sort_keys=True,
                     default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
