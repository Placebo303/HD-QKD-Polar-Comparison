"""Route B M0 — small-q DE reproduction harness (diagnostic/gate engineering).

Reuses existing frozen DE/MC-DE assets; does not modify them.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import nonbinary_v10_de as de
from . import nonbinary_v8_mcde as v8

SCHEMA = "nbldpc_v18_b1_repro_v1"
SMOKE_Q = 4
SMOKE_RATE = 0.75
SMOKE_P_GATE = 0.069
SMOKE_SEED = 20260816

# --- M1 frozen production budget ------------------------------------------- #
# Inherits: V8 MC-DE conventions (n_samples/max_iter/p-grid/tolerance) and
# V10A DE-search conventions (pop_size/max_gen/F/CR).  Changing any of these
# constants after a production result exists would violate the no-tuning rule;
# the plan test asserts them verbatim.
PRODUCTION_Q = 4
PRODUCTION_RATE = 0.75
PRODUCTION_P_GATE = v8.REPRODUCTION_DET_PUBLISHED          # 0.069, Müller 2024 Table 1 row 0.75
PRODUCTION_DET_PUBLISHED = v8.REPRODUCTION_DET_PUBLISHED
PRODUCTION_TOL = v8.REPRODUCTION_TOL                       # 0.012 (V8-60 audited arithmetic)
PRODUCTION_SEED = 2026081602                               # distinct from V8 2026080418 / smoke 20260816
PRODUCTION_POP_SIZE = 20                                   # V10A convention
PRODUCTION_MAX_GEN = 29
PRODUCTION_F = 0.5
PRODUCTION_CR = 0.9
PRODUCTION_N_SAMPLES = v8.REPRODUCTION_N_SAMPLES           # 100000
PRODUCTION_MAX_ITER = v8.REPRODUCTION_MAX_ITER             # 150
PRODUCTION_P_LO = v8.REPRODUCTION_P_LO
PRODUCTION_P_HI = v8.REPRODUCTION_P_HI
PRODUCTION_P_TOL = v8.REPRODUCTION_P_TOL
PRODUCTION_ENTROPY_TOL = v8.REPRODUCTION_ENTROPY_TOL
PRODUCTION_STREAK = v8.REPRODUCTION_STREAK


def production_plan() -> dict:
    """Frozen M1 production budget; any field change changes the plan."""
    return {
        "schema": SCHEMA + "_plan_v1",
        "mode": "production",
        "change": "formal-nonbinary-ldpc-v18-b1-smallq-de-reproduction",
        "stage": "M1 production budget freeze",
        "q": PRODUCTION_Q,
        "rate": PRODUCTION_RATE,
        "p_gate": PRODUCTION_P_GATE,
        "det_published": PRODUCTION_DET_PUBLISHED,
        "tol": PRODUCTION_TOL,
        "seed": PRODUCTION_SEED,
        "pop_size": PRODUCTION_POP_SIZE,
        "max_gen": PRODUCTION_MAX_GEN,
        "F": PRODUCTION_F,
        "CR": PRODUCTION_CR,
        "n_samples": PRODUCTION_N_SAMPLES,
        "max_iter": PRODUCTION_MAX_ITER,
        "threshold_p_lo": PRODUCTION_P_LO,
        "threshold_p_hi": PRODUCTION_P_HI,
        "threshold_p_tol": PRODUCTION_P_TOL,
        "entropy_tol": PRODUCTION_ENTROPY_TOL,
        "streak": PRODUCTION_STREAK,
        "workers": 1,
        "execute_policy": "execute exactly once + strict replay; no rerun, no tuning",
        "gate": ("threshold_proxy is not null and "
                 "|threshold_proxy - det_published| <= tol"),
    }


def run_smoke(q: int = SMOKE_Q, out_dir: str | Path | None = None,
              seed: int = SMOKE_SEED) -> dict:
    """Run a tiny DE search smoke. Writes a repro JSON if out_dir is given."""
    out = Path(out_dir) if out_dir is not None else None
    if out is not None:
        out.mkdir(parents=True, exist_ok=True)
    result = de.run_de_search(
        q=q, p_gate=SMOKE_P_GATE, rate=SMOKE_RATE, search_seed=seed,
        pop_size=8, max_gen=2, f=0.85, cr=0.7,
        n_samples=2000, max_iter=30, entropy_tol=0.01, streak=20,
        threshold_p_lo=0.01, threshold_p_hi=0.12, threshold_p_tol=0.0025,
        compute_threshold=True,
        out_dir=None if out is None else str(out / "de_search"),
    )
    doc = {
        "schema": SCHEMA,
        "mode": "smoke",
        "q": q,
        "rate": SMOKE_RATE,
        "p_gate": SMOKE_P_GATE,
        "seed": seed,
        "result": result,
    }
    if out is not None:
        (out / "repro.json").write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return doc


def evaluate_reproduction(result: dict,
                          det_published: float = PRODUCTION_DET_PUBLISHED,
                          tol: float = PRODUCTION_TOL) -> dict:
    """Reproduction gate: |threshold_proxy - published DET| <= tol.

    Uses the top-level ``threshold_proxy`` if present; otherwise falls back to
    the best (max) threshold among ``eligible_candidates``.  This avoids
    misreporting NO_THRESHOLD when the search produced eligible candidates but
    the top-level best-objective record was not updated with a threshold.
    """
    tp = result.get("threshold_proxy")
    if tp is None:
        elig = result.get("eligible_candidates") or []
        tps = [float(c.get("threshold_proxy")) for c in elig
               if c.get("threshold_proxy") is not None]
        if tps:
            tp = max(tps)
    if tp is None:
        delta, verdict = None, "NO_THRESHOLD"
    else:
        delta = abs(float(tp) - float(det_published))
        verdict = "PASS" if delta <= tol else "FAIL"
    return {"threshold_proxy": tp, "det_published": det_published, "tol": tol,
            "delta": delta, "verdict": verdict}


def run_production(out_dir: str | Path, seed: int = PRODUCTION_SEED) -> dict:
    """One production DE search under the frozen M1 budget.

    Writes ``pre_run_plan.json`` BEFORE running (refuses to overwrite an
    existing plan), then ``repro.json`` with the search result plus the
    reproduction delta/verdict.  No rerun/tuning is authorized here.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    plan_path = out / "pre_run_plan.json"
    if plan_path.exists():
        raise ValueError(f"refusing to overwrite frozen plan: {plan_path}")
    plan = production_plan()
    plan["seed"] = int(seed)
    plan_path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result = de.run_de_search(
        q=PRODUCTION_Q, p_gate=PRODUCTION_P_GATE, rate=PRODUCTION_RATE,
        search_seed=int(seed),
        pop_size=PRODUCTION_POP_SIZE, max_gen=PRODUCTION_MAX_GEN,
        f=PRODUCTION_F, cr=PRODUCTION_CR,
        n_samples=PRODUCTION_N_SAMPLES, max_iter=PRODUCTION_MAX_ITER,
        entropy_tol=PRODUCTION_ENTROPY_TOL, streak=PRODUCTION_STREAK,
        threshold_p_lo=PRODUCTION_P_LO, threshold_p_hi=PRODUCTION_P_HI,
        threshold_p_tol=PRODUCTION_P_TOL, compute_threshold=True,
        out_dir=str(out / "de_search"),
    )
    doc = {
        "schema": SCHEMA,
        "mode": "production",
        "q": PRODUCTION_Q,
        "rate": PRODUCTION_RATE,
        "p_gate": PRODUCTION_P_GATE,
        "seed": int(seed),
        "plan": plan,
        "result": result,
        "reproduction": evaluate_reproduction(result),
    }
    (out / "repro.json").write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return doc


def run_execute(q: int = SMOKE_Q, out_dir: str | Path | None = None,
                 seed: int = SMOKE_SEED, *,
                 pop_size: int = 15, max_gen: int = 5,
                 n_samples: int = 50000, max_iter: int = 150) -> dict:
    """Run a larger q=4 reproduction search (execution-mode budget)."""
    out = Path(out_dir) if out_dir is not None else None
    if out is not None:
        out.mkdir(parents=True, exist_ok=True)
    result = de.run_de_search(
        q=q, p_gate=SMOKE_P_GATE, rate=SMOKE_RATE, search_seed=seed,
        pop_size=pop_size, max_gen=max_gen, f=0.85, cr=0.7,
        n_samples=n_samples, max_iter=max_iter, entropy_tol=0.01, streak=20,
        threshold_p_lo=0.01, threshold_p_hi=0.12, threshold_p_tol=0.0025,
        compute_threshold=True,
        out_dir=None if out is None else str(out / "de_search"),
    )
    doc = {
        "schema": SCHEMA,
        "mode": "execute",
        "q": q,
        "rate": SMOKE_RATE,
        "p_gate": SMOKE_P_GATE,
        "seed": seed,
        "result": result,
    }
    if out is not None:
        (out / "repro.json").write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return doc


# --- M1b corrected screening p_gate ---
# V8 reproduction threshold_proxy ~0.0624; using published DET 0.069 as the
# DE screening gate is above our MC-DE threshold and yields 0 eligible.
# M1b is a new attempt with a corrected gate, not a rerun of M1.
M1B_P_GATE = 0.062
M1B_SEED = 2026081604


def run_m1b(out_dir: str | Path, seed: int = M1B_SEED) -> dict:
    """Corrected M1b production DE search: screen at p_gate=0.062."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    plan_path = out / "pre_run_plan.json"
    if plan_path.exists():
        raise ValueError(f"refusing to overwrite frozen plan: {plan_path}")
    plan = production_plan()
    plan["seed"] = int(seed)
    plan["p_gate"] = M1B_P_GATE
    plan["attempt"] = "M1b corrected screening p_gate"
    plan_path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result = de.run_de_search(
        q=PRODUCTION_Q, p_gate=M1B_P_GATE, rate=PRODUCTION_RATE,
        search_seed=int(seed),
        pop_size=PRODUCTION_POP_SIZE, max_gen=PRODUCTION_MAX_GEN,
        f=PRODUCTION_F, cr=PRODUCTION_CR,
        n_samples=PRODUCTION_N_SAMPLES, max_iter=PRODUCTION_MAX_ITER,
        entropy_tol=PRODUCTION_ENTROPY_TOL, streak=PRODUCTION_STREAK,
        threshold_p_lo=PRODUCTION_P_LO, threshold_p_hi=PRODUCTION_P_HI,
        threshold_p_tol=PRODUCTION_P_TOL, compute_threshold=True,
        out_dir=str(out / "de_search"),
    )
    doc = {
        "schema": SCHEMA,
        "mode": "m1b",
        "q": PRODUCTION_Q,
        "rate": PRODUCTION_RATE,
        "p_gate": M1B_P_GATE,
        "seed": int(seed),
        "plan": plan,
        "result": result,
        "reproduction": evaluate_reproduction(result),
    }
    (out / "repro.json").write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return doc
