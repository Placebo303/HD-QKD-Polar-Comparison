"""V19 Nonbinary LDPC DE search helpers (Route N2).

This additive layer extends the frozen V18-B2 structured-DE harness without
modifying it.  It provides:

- ``run_rate_ladder``: warm-started rate ladder from a previous best lambda,
  early-stopping at the first non-converged rate (N2a).
- ``run_qsc_control``: equal-entropy QSC control runs for attribution (B-1).
- ``run_extended_degree_probe``: direct structured-channel MC-DE evaluation of
  variable-degree distributions with degrees up to 64 (N2c), bypassing the
  frozen V10 K=8/40-degree encoding.

All scientific outputs are ``diagnostic_only``; no production/qualification
claim is made.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from . import nonbinary_v18_b2_structured_de as v18
from . import nonbinary_v10_de as de
from . import nonbinary_v14_mcde as v14
from . import nonbinary_v9_common as common
from .nonbinary_v19_channel import build_qsc_w, f_plain_qary, symbol_entropy_bits

__all__ = [
    "run_rate_ladder",
    "run_qsc_control",
    "evaluate_extended_lambda",
    "run_extended_degree_probe",
    "build_ladder_doc",
]


def run_rate_ladder(*, q: int, w: Any, rates: list[float],
                    seed: int, pop_size: int = 8, max_gen: int = 3,
                    n_samples: int = 1000, max_iter: int = 40,
                    F: float = 0.85, CR: float = 0.7,
                    warm_start: bool = True,
                    seed_lambda: Mapping[int, float] | None = None,
                    out_dir: str | Path | None = None,
                    early_stop: bool = True) -> dict:
    """Run a warm-started rate ladder on the structured channel.

    Each rate uses :func:`v18.run_structured_de_search`.  When ``warm_start``
    and a previous converged lambda exists, that lambda is injected as the
    first population member of the next rate.  The ladder stops at the first
    rate that does not produce a converged best objective when ``early_stop``
    is true.

    The default budget is intentionally small (for smoke/test); production
    diagnostics should pass a larger budget explicitly.
    """
    if isinstance(q, bool) or not isinstance(q, int) or int(q) < 2:
        raise ValueError("q must be a positive integer")
    q = int(q)
    w = np.asarray(w, dtype=np.float64)
    if w.shape != (q,) or not np.all(np.isfinite(w)) or np.any(w < 0.0):
        raise ValueError("w must be a finite non-negative length-q vector")
    if not np.isclose(float(w.sum()), 1.0, atol=1e-9):
        w = w / float(w.sum())
    rows: list[dict] = []
    previous_lambda: dict[int, float] | None = (
        {int(k): float(v) for k, v in seed_lambda.items()} if seed_lambda else None)
    max_converged_rate = None
    max_converged_f = None
    for rate in rates:
        rate = float(rate)
        search_kwargs = dict(
            q=q, rate=rate, w=w, search_seed=seed, pop_size=pop_size,
            max_gen=max_gen, F=F, CR=CR, n_samples=n_samples,
            max_iter=max_iter)
        if warm_start and previous_lambda is not None:
            if len(previous_lambda) == 8 and len(set(previous_lambda)) == 8:
                search_kwargs["seed_lambda"] = previous_lambda
        doc = v18.run_structured_de_search(**search_kwargs)
        best = doc["best_objective"]
        converged = bool(best["entropy_converged"])
        best_lambda = doc["best_lambda"]
        row = {
            "rate": rate,
            "converged": converged,
            "best_lambda": {int(k): float(v) for k, v in best_lambda.items()},
            "best_objective": best,
            "seed": seed,
        }
        h_bits = float(symbol_entropy_bits(w))
        row["f_plain_qary"] = float(f_plain_qary(rate=rate, q=q, h_bits=h_bits))
        rows.append(row)
        if converged:
            max_converged_rate = rate
            max_converged_f = row["f_plain_qary"]
            previous_lambda = {int(k): float(v) for k, v in best_lambda.items()}
        else:
            if early_stop:
                break
    doc = build_ladder_doc(q=q, w=w, rates=[r["rate"] for r in rows], rows=rows,
                           seed=seed, max_converged_rate=max_converged_rate,
                           max_converged_f=max_converged_f)
    if out_dir is not None:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "rate_ladder.json").write_text(
            json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return doc


def run_qsc_control(*, q: int, p: float, rates: list[float], seeds: list[int],
                    pop_size: int = 20, max_gen: int = 20,
                    n_samples: int = 10000, max_iter: int = 100,
                    out_dir: str | Path | None = None) -> dict:
    """Run equal-entropy QSC control searches (B-1 attribution).

    The channel is a QSC distribution with the same entropy as the folded real
    channel.  This is a diagnostic control; it does not change frozen results.
    """
    w = build_qsc_w(q, p)
    rows = []
    n_converged = 0
    for rate in rates:
        for seed in seeds:
            doc = v18.run_structured_de_search(
                q=q, rate=rate, w=w, search_seed=int(seed), pop_size=pop_size,
                max_gen=max_gen, F=0.85, CR=0.7, n_samples=n_samples,
                max_iter=max_iter)
            best = doc["best_objective"]
            converged = bool(best["entropy_converged"])
            n_converged += int(converged)
            rows.append({
                "rate": float(rate), "seed": int(seed),
                "converged": converged,
                "best_objective": best,
                "best_lambda": doc["best_lambda"],
            })
    doc = {
        "schema": "nbldpc_v19_qsc_control_v1",
        "q": q, "p": p,
        "entropy_bits": float(symbol_entropy_bits(w)),
        "rates": [float(r) for r in rates],
        "seeds": [int(s) for s in seeds],
        "n_runs": len(rows), "n_converged": n_converged, "n_failed": len(rows) - n_converged,
        "rows": rows,
        "claim_boundary": "diagnostic_only",
    }
    if out_dir is not None:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "qsc_control.json").write_text(
            json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return doc


def evaluate_extended_lambda(*, q: int, rate: float, w: Any,
                             lambda_edge: Mapping[int, float],
                             n_samples: int = 2000, max_iter: int = 50,
                             seed: int = 2026081601,
                             entropy_tol: float = 0.01, streak: int = 20) -> dict:
    """Evaluate one variable-degree distribution (degrees can exceed 40) on the
    structured channel using the V14 MC-DE evaluator.

    This is the N2c probe path: it does not use the frozen V10 K=8 vector
    encoding, so it can explore degree-64 variable nodes and the corresponding
    concentrated check-degree distribution without modifying V10/V14.
    """
    q = int(q)
    w = np.asarray(w, dtype=np.float64)
    if w.shape != (q,) or not np.all(np.isfinite(w)) or np.any(w < 0.0):
        raise ValueError("w must be a finite non-negative length-q vector")
    if not np.isclose(float(w.sum()), 1.0, atol=1e-9):
        w = w / float(w.sum())
    lam = {int(k): float(v) for k, v in lambda_edge.items()}
    if not lam:
        raise ValueError("lambda_edge must be non-empty")
    # The concentrated check distribution is exact for any valid degree <= 64.
    conc = common.concentrated_check_distribution(float(rate), lam)
    rho = {int(conc["dc_lo"]): float(conc["w_lo"]),
           int(conc["dc_hi"]): float(conc["w_hi"])}
    result = v14.run_mcde(
        q, lam, rho, n_samples=n_samples, max_iter=max_iter, seed=seed,
        channel_mode="structured", w=w, entropy_tol=entropy_tol, streak=streak)
    return {
        "schema": "nbldpc_v19_extended_de_eval_v1",
        "q": q, "rate": float(rate), "seed": int(seed),
        "lambda_edge": lam, "rho_edge": rho,
        "converged": bool(result["converged"]),
        "iterations": int(result["iterations"]),
        "final_entropy": float(result["final_entropy"]),
        "error_prob": float(result["error_trace"][-1]),
        "entropy_trace": [float(x) for x in result["entropy_trace"]],
        "claim_boundary": "diagnostic_only",
    }


def run_extended_degree_probe(*, q: int, rate: float, w: Any,
                              candidates: list[Mapping[int, float]],
                              n_samples: int = 2000, max_iter: int = 50,
                              seed: int = 2026081601,
                              out_dir: str | Path | None = None) -> dict:
    """Evaluate a list of extended-degree lambda candidates on the structured
    channel.  Returns per-candidate convergence diagnostics."""
    rows = []
    for idx, lam in enumerate(candidates):
        row = evaluate_extended_lambda(
            q=q, rate=rate, w=w, lambda_edge=lam,
            n_samples=n_samples, max_iter=max_iter, seed=seed + idx)
        row["candidate_index"] = idx
        rows.append(row)
    doc = {
        "schema": "nbldpc_v19_extended_degree_probe_v1",
        "q": q, "rate": float(rate),
        "n_candidates": len(rows),
        "rows": rows,
        "claim_boundary": "diagnostic_only",
    }
    if out_dir is not None:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "extended_degree_probe.json").write_text(
            json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return doc


def build_ladder_doc(*, q: int, w: Any, rates: list[float], rows: list[dict],
                     seed: int, max_converged_rate: float | None,
                     max_converged_f: float | None) -> dict:
    """Assemble the rate-ladder document schema."""
    from .nonbinary_v19_channel import symbol_entropy_bits
    h_bits = float(symbol_entropy_bits(w))
    return {
        "schema": "nbldpc_v19_rate_ladder_v1",
        "q": q,
        "entropy_bits": h_bits,
        "seed": seed,
        "rates": [float(r) for r in rates],
        "rows": rows,
        "max_converged_rate": max_converged_rate,
        "max_converged_f_plain": max_converged_f,
        "claim_boundary": "diagnostic_only",
    }
