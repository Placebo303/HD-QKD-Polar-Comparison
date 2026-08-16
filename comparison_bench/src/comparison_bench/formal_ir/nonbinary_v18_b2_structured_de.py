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

def lambda_to_vector(lambda_edge) -> "np.ndarray":
    """Encode a K-entry degree distribution into a V10 DE vector.

    The vector is the inverse of ``de.decode_vector``: degree slots are stored
    as degree-2 and logits as log(weight) (softmax reproduces the weights).
    """
    import numpy as np
    if not isinstance(lambda_edge, dict) or len(lambda_edge) != de._K:
        raise ValueError(f"seed lambda must be a dict with exactly {de._K} entries")
    degrees = sorted(int(d) for d in lambda_edge)
    weights = [float(lambda_edge[d]) for d in degrees]
    if len(set(degrees)) != de._K or any(w <= 0.0 for w in weights):
        raise ValueError("seed lambda must have K distinct positive weights")
    total = sum(weights)
    logits = np.log(np.asarray(weights, dtype=np.float64) / total)
    slots = np.asarray(degrees, dtype=np.float64) - 2.0
    return np.concatenate([slots, logits])


def seeded_population(pop_size: int, search_seed: int,
                      lambda_edge: dict) -> "np.ndarray":
    """Return the deterministic V10 population with the first member replaced
    by a known degree distribution (``lambda_edge``).  The remaining members are
    untouched random DE starts, so the search can locally explore around a
    previously successful distribution while retaining diversity."""
    import numpy as np
    population = de.init_population(pop_size, search_seed)
    population[0] = lambda_to_vector(lambda_edge)
    return population

def run_structured_de_search(*, q, rate, w, search_seed, pop_size, max_gen,
                             F, CR, n_samples, max_iter, entropy_tol=0.01,
                             streak=20, seed_lambda=None, out_dir=None):
    """Minimal DE/rand/1/bin search over the structured channel.

    This is a trimmed copy of V10's loop; no checkpoints/resume.  It returns
    the final best lambda and objective.
    """
    import numpy as np
    if seed_lambda is None:
        population = de.init_population(pop_size, search_seed)
    else:
        population = seeded_population(pop_size, search_seed, seed_lambda)
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


# --------------------------------------------------------------------------- #
# Real structured channel w from V17 per-bit-plane model
# --------------------------------------------------------------------------- #

_V17_PER_PLANE_ERROR = [
    3.0517578125e-05, 0.0001220703125, 0.0003662109375, 0.000946044921875,
    0.001251220703125, 0.00250244140625, 0.00457763671875, 0.009307861328125,
    0.02044677734375, 0.037506103515625,
]


def build_real_w_q1024() -> "np.ndarray":
    """Averaged raw-XOR symbol-difference distribution under Gray mapping.

    For each raw diff d, average over Alice symbol s of the V17 product
    per-bit-plane error probability for the Gray bit difference between s and
    s^d.  This is a translation-averaged approximation; it is diagnostic.
    """
    import numpy as np
    from ..utils.bitops import gray_encode
    q = 1024
    bits = 10
    w = np.zeros(q, dtype=np.float64)
    # Precompute gray bit arrays
    gray = np.array([gray_encode(np.array([s]))[0] for s in range(q)], dtype=np.int64)
    bit = np.array([[(g >> k) & 1 for k in range(bits)] for g in gray], dtype=np.int64)
    p = np.array(_V17_PER_PLANE_ERROR, dtype=np.float64)
    for s in range(q):
        gs = bit[s]
        for d in range(q):
            gd = bit[s ^ d]
            diff = gs ^ gd
            prob = 1.0
            for k in range(bits):
                prob *= (p[k] if diff[k] else 1.0 - p[k])
            w[d] += prob
    w /= w.sum()
    return w


def build_folded_w(q_small: int = 16) -> "np.ndarray":
    """Build a small-q structured w by folding the real q=1024 averaged w."""
    import numpy as np
    from . import nonbinary_v14_channel as v14ch
    if q_small not in (2, 4, 8, 16, 32, 64, 128, 256, 512, 1024):
        raise ValueError("q_small must be a power of two <= 1024")
    m_bits = int(round(np.log2(q_small)))
    return v14ch.fold(build_real_w_q1024(), m_bits)
