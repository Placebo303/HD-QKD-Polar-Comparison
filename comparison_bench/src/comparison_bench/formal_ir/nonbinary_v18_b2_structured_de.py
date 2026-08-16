"""Route B M2 skeleton — structured-channel DE harness (engineering only).

Imports frozen V14 structured-channel model read-only. No production run yet.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import nonbinary_v14_channel as v14
from . import nonbinary_v10_de as de

SCHEMA = "nbldpc_v18_b2_structured_de_plan_v1"


def build_m2_plan(*, q_small: int = 16, seed: int = 2026081603) -> dict:
    """Draft M2 plan. Not frozen; M1 must pass before this becomes a gate."""
    return {
        "schema": SCHEMA,
        "stage": "m2_structured_de_prep",
        "q_small": q_small,
        "seed": seed,
        "reuse": {
            "v14_channel": "nonbinary_v14_channel",
            "de_search": "nonbinary_v10_de.run_de_search",
        },
        "gate_dependency": "V18-B1 M1 reproduction PASS",
        "execute_policy": "not authorized until M1 replay complete",
    }


def run_smoke(*, q: int = 8, out_dir: str | Path | None = None,
              seed: int = 2026081605, n_samples: int = 1000,
              max_iter: int = 10) -> dict:
    """Small structured-channel MC-DE smoke using a tiny regular config.

    This validates the M2 harness plumbing; it is not a production gate.
    """
    import numpy as np
    from . import nonbinary_v14_mcde as v14mcde
    from . import nonbinary_v9_common as common

    lam = {2: 0.5, 3: 0.5}
    conc = common.concentrated_check_distribution(0.5, lam)
    rho = {int(conc["dc_lo"]): float(conc["w_lo"]),
           int(conc["dc_hi"]): float(conc["w_hi"])}
    w = np.full(q, 0.05)
    w[0] = 0.65
    run = v14mcde.run_mcde(q, lam, rho, n_samples=n_samples, max_iter=max_iter,
                           seed=seed, channel_mode="structured", w=w)
    doc = {
        "schema": "nbldpc_v18_b2_structured_de_smoke_v1",
        "q": q,
        "seed": seed,
        "run": run,
    }
    if out_dir is not None:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "smoke.json").write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return doc


# --------------------------------------------------------------------------- #
# M2 structured-DE search (minimal; reuses V10 DE loop primitives read-only)
# --------------------------------------------------------------------------- #

def evaluate_candidate_structured(lambda_edge, *, q, rate, w, seed, n_samples,
                                  max_iter, entropy_tol=0.01, streak=20):
    """Structured-channel analog of V10 evaluate_candidate."""
    import numpy as np
    from . import nonbinary_v14_mcde as v14mcde
    from . import nonbinary_v9_common as common
    violation = de._structural_violation_amount(lambda_edge)
    canonical = de._canonical_tuple(lambda_edge)
    if violation > 0.0:
        return de.ObjectiveRecord(
            entropy_converged=False, converged_iter=de._SENTINEL_ITER,
            final_entropy=de._SENTINEL_VALUE, error_prob=de._SENTINEL_VALUE,
            threshold_proxy=None, canonical_tuple=canonical,
            penalty=de.PENALTY_STRUCTURAL_BASE + violation)
    try:
        conc = common.concentrated_check_distribution(rate, lambda_edge)
        rho = de._rho_from_concentrated(conc)
        result = v14mcde.run_mcde(q, lambda_edge, rho, n_samples=n_samples,
                                  max_iter=max_iter, seed=seed,
                                  channel_mode="structured", w=w,
                                  entropy_tol=entropy_tol, streak=streak)
    except ValueError:
        return de.ObjectiveRecord(
            entropy_converged=False, converged_iter=de._SENTINEL_ITER,
            final_entropy=de._SENTINEL_VALUE, error_prob=de._SENTINEL_VALUE,
            threshold_proxy=None, canonical_tuple=canonical,
            penalty=de.PENALTY_STRUCTURAL_BASE + 1.0)
    if not result["converged"]:
        return de.ObjectiveRecord(
            entropy_converged=False, converged_iter=de._SENTINEL_ITER,
            final_entropy=de._SENTINEL_VALUE, error_prob=de._SENTINEL_VALUE,
            threshold_proxy=None, canonical_tuple=canonical, penalty=0.0)
    return de.ObjectiveRecord(
        entropy_converged=True, converged_iter=int(result["iterations"]),
        final_entropy=float(result["final_entropy"]),
        error_prob=float(result["error_trace"][-1]),
        threshold_proxy=None, canonical_tuple=canonical, penalty=0.0)


def evaluate_vector_structured(x, *, q, rate, w, seed, n_samples, max_iter,
                               entropy_tol=0.01, streak=20):
    """Evaluate one raw DE vector on the structured channel."""
    try:
        lam = de.decode_vector(x)
    except ValueError:
        return de.ObjectiveRecord(
            entropy_converged=False, converged_iter=de._SENTINEL_ITER,
            final_entropy=de._SENTINEL_VALUE, error_prob=de._SENTINEL_VALUE,
            threshold_proxy=None, canonical_tuple=(), penalty=de.PENALTY_NAN_INF)
    return evaluate_candidate_structured(lam, q=q, rate=rate, w=w, seed=seed,
                                         n_samples=n_samples, max_iter=max_iter,
                                         entropy_tol=entropy_tol, streak=streak)


def run_structured_de_search(*, q, rate, w, search_seed, pop_size, max_gen,
                             F, CR, n_samples, max_iter, entropy_tol=0.01,
                             streak=20, out_dir=None):
    """Minimal DE/rand/1/bin search over the structured channel.

    This is a trimmed copy of V10's loop; no checkpoints/resume.  It returns
    the final best lambda and objective.
    """
    import numpy as np
    population = de.init_population(pop_size, search_seed)
    objectives = [evaluate_vector_structured(population[i], q=q, rate=rate, w=w,
                                             seed=search_seed, n_samples=n_samples,
                                             max_iter=max_iter, entropy_tol=entropy_tol,
                                             streak=streak) for i in range(pop_size)]
    for generation in range(1, max_gen + 1):
        for i in range(pop_size):
            rng = de._mutation_rng(search_seed, generation, i)
            r1, r2, r3 = de._draw_distinct(rng, pop_size, i)
            mutant = population[r1] + F * (population[r2] - population[r3])
            trial = de._binomial_crossover(rng, mutant, population[i], CR)
            trial_obj = evaluate_vector_structured(trial, q=q, rate=rate, w=w,
                                                   seed=search_seed, n_samples=n_samples,
                                                   max_iter=max_iter, entropy_tol=entropy_tol,
                                                   streak=streak)
            if de.objective_compare(trial_obj, objectives[i]) < 0:
                population[i] = trial
                objectives[i] = trial_obj
    best_index = min(range(pop_size), key=lambda i: (objectives[i].penalty,
                                                     not objectives[i].entropy_converged,
                                                     objectives[i].converged_iter,
                                                     objectives[i].final_entropy,
                                                     objectives[i].error_prob,
                                                     objectives[i].canonical_tuple))
    best = objectives[best_index]
    doc = {
        "schema": "nbldpc_v18_b2_structured_de_search_v1",
        "q": q, "rate": rate, "seed": search_seed,
        "pop_size": pop_size, "max_gen": max_gen, "F": F, "CR": CR,
        "n_samples": n_samples, "max_iter": max_iter,
        "best_lambda": de.decode_vector(population[best_index]),
        "best_objective": de.record_to_dict(best),
        "generations_completed": max_gen,
    }
    if out_dir is not None:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "search_result.json").write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return doc


def run_search_smoke(*, q=8, out_dir=None, seed=2026081605, n_samples=200,
                     max_iter=5, pop_size=6, max_gen=2, F=0.85, CR=0.7) -> dict:
    """Tiny structured-DE search smoke using the same w as M2 smoke."""
    import numpy as np
    w = np.full(q, 0.05)
    w[0] = 0.65
    return run_structured_de_search(
        q=q, rate=0.5, w=w, search_seed=seed, pop_size=pop_size, max_gen=max_gen,
        F=F, CR=CR, n_samples=n_samples, max_iter=max_iter, out_dir=out_dir)
