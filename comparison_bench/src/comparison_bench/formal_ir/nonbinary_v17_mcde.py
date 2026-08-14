"""V17 Stage 2 — pre-registered multibit candidate point evaluation
(``formal-nonbinary-ldpc-v17-multibit-structured-de-gate``, additive layer).

Three candidates are pre-registered before execution (design section 4,
no search / no tuning / no subsetting); each evaluates the FULL frozen point set
``m in {15, 16, 17, 18}`` (rate 0.9297–0.9414, n=256, q=1024 — the same protocol
and codeblock as V14):

1. **Cohen-style bit-plane decomposition** (``bitplane``): the q=1024 channel is
   Gray-sliced into 10 binary planes; each plane runs an independent binary DE
   (the SAME frozen kernel at ``q=2``, per-plane BSC crossover = the frozen
   per-plane error probability), planes coupled only through the joint
   convergence judgement (every plane must converge).  ``f`` from the total
   leakage ``sum_i h2(p_i)``.
2. **Multibit edge-label symbol-level DE** (``edgelabel``): a q=1024 symbol-level
   structured DE (V14 structured branch reused read-only) whose structured prior
   is the independent per-bit-plane symbol-difference distribution (edge labels
   follow the bit-plane pattern: MSB high reliability, LSB low reliability).
3. **Bit-plane-weighted structured prior** (``planeweight``): a second structured
   symbol-level DE whose prior modulates the independent per-bit-plane prior by
   the per-plane mismatch weights (a distinct, frozen weighting).

Convergence is ``entropy <= entropy_tol`` (base-q) for ``streak`` consecutive
iterations (V14 frozen convention); ``f`` is computed per the V14 convention
``f = (m * 10 / n) / H_channel`` where ``H_channel`` is the channel entropy in
bits/symbol (the total leakage ``sum_i h2(p_i)`` under the independent-plane
declaration).  A candidate point PASSes iff it converges AND ``f <= f_limit``.

Budget-friendly frozen defaults (design section 5): ``n_samples=1e4``,
``max_iter=150`` per point, seeded PCG64, deterministic per-point seed.

Only numpy/numba and the read-only V14/V9 helpers are imported; this module
never reads frame data at import time and never executes a decoder.
"""
from __future__ import annotations

import math
from numbers import Integral
from typing import Any, Mapping

import numpy as np

# Read-only reuse of the V14 structured DE kernel + frozen stage constants.
from .nonbinary_v14_mcde import (MS, N_BLOCKS, QSC, STAGE2_ENTROPY_TOL,
                                 STAGE2_MAX_ITER, STAGE2_N_SAMPLES,
                                 STAGE2_STREAK, STRUCTURED, PROFILES,
                                 run_mcde, structured_rho, stage2_f_achieved)

from .nonbinary_v17_channel import (BIT_PLANES, Q, total_leakage_bits)

__all__ = [
    "QSC", "STRUCTURED",
    "Q", "BIT_PLANES", "N_BLOCKS", "MS",
    "STAGE2_N_SAMPLES", "STAGE2_MAX_ITER", "STAGE2_ENTROPY_TOL", "STAGE2_STREAK",
    "CANDIDATES", "STAGE2_SEED_ROOT", "F_LIMIT",
    "bitplane_prior", "planeweight_prior",
    "evaluate_bitplane_point", "evaluate_symbol_point",
    "evaluate_candidate", "build_stage2_doc",
    "build_gate_decision_doc", "build_gate_manifest_doc",
]

#: Frozen efficiency limit (design section 4): f <= 1.3.
F_LIMIT = 1.3

#: Frozen per-point seed root (disjoint 202609030x prefix).
STAGE2_SEED_ROOT = 2026090300

#: Pre-registered candidate state (frozen before execution; no search).
CANDIDATES = [
    {"id": "bitplane",   "label": "Cohen-style bit-plane decomposition",
     "profile": 1, "mechanism": "bitplane"},
    {"id": "edgelabel",  "label": "multibit edge-label symbol-level DE",
     "profile": 1, "mechanism": "symbol_structured"},
    {"id": "planeweight", "label": "bit-plane-weighted structured prior",
     "profile": 2, "mechanism": "symbol_structured_weighted"},
]

# Sanity: every candidate's profile id resolves in PROFILES.
_ASSERT_PROFILE_IDS = {p["id"] for p in PROFILES}


def _profile_lambda(profile_id: int) -> dict:
    for profile in PROFILES:
        if int(profile["id"]) == int(profile_id):
            return dict(profile["lambda"])
    raise ValueError(f"unknown profile id {profile_id}")


def _struct_rho(rate: float, lam: dict) -> dict:
    conc = structured_rho(rate, lam)
    return {int(k): float(v) for k, v in
            ((conc["dc_lo"], conc["w_lo"]), (conc["dc_hi"], conc["w_hi"]))
            if float(v) > 0.0}


# --------------------------------------------------------------------------- #
# structured priors from the frozen per-plane rates
# --------------------------------------------------------------------------- #

def _validate_plane_rates(rates: Any) -> np.ndarray:
    vector = np.asarray(rates, dtype=np.float64)
    if vector.shape != (BIT_PLANES,) or not np.all(np.isfinite(vector)) \
            or np.any(vector < 0.0) or np.any(vector > 1.0) or np.any(vector == 0.0):
        raise ValueError(f"per-plane rates must be a strictly-positive length-{BIT_PLANES} vector")
    return vector


def bitplane_prior(rates: Any) -> np.ndarray:
    """Independent per-bit-plane symbol-difference prior over GF(1024).

    ``w[d] = prod_b (p_b if bit_b(gray? no: d) else 1 - p_b)`` — the difference
    ``d`` is sliced by its native (XOR) bit planes, bit ``b`` of ``d`` set with
    probability ``p_b``.  (The symbol-difference domain is the XOR error, whose
    bit planes are the native integer bits; the per-plane ``p_b`` are the V13
    gray-labelled mismatch rates, reused as the frozen per-bit-plane structure.)
    """
    rates = _validate_plane_rates(rates)
    w = np.full(Q, 1.0, dtype=np.float64)
    for b in range(BIT_PLANES):
        pb = float(rates[b])
        plane = (np.arange(Q, dtype=np.int64) >> b) & 1
        w = np.where(plane == 1, w * pb, w * (1.0 - pb))
    total = float(w.sum())
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError("bitplane prior has invalid total mass")
    w = w / total
    # Smooth below by reassigning exact-zero mass to a tiny floor (structured
    # mode requires strictly positive? run_mcde floors per row; keep finite).
    w = np.maximum(w, 1e-300)
    w = w / float(w.sum())
    return w


def planeweight_prior(rates: Any) -> np.ndarray:
    """Bit-plane-weighted structured prior: the independent prior re-weighted so
    that each bit-plane's reliability contribution is modulated by its mismatch
    (a distinct frozen weighting vs the plain ``bitplane_prior``).

    ``w[d] = prod_b (p_b^beta if bit set else (1-p_b)^beta)`` with a frozen
    ``beta=0.5`` exponent hardens the MSB (low-``p``) planes and softens the LSB
    (high-``p``) planes, i.e. a stronger MSB-first reliability gradient.
    """
    rates = _validate_plane_rates(rates)
    beta = 0.5
    w = np.full(Q, 1.0, dtype=np.float64)
    for b in range(BIT_PLANES):
        pb = float(rates[b])
        plane = (np.arange(Q, dtype=np.int64) >> b) & 1
        w = np.where(plane == 1, w * (pb ** beta), w * ((1.0 - pb) ** beta))
    total = float(w.sum())
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError("planeweight prior has invalid total mass")
    w = w / total
    w = np.maximum(w, 1e-300)
    return w / float(w.sum())


# --------------------------------------------------------------------------- #
# point evaluation
# --------------------------------------------------------------------------- #

def evaluate_bitplane_point(rates: Any, lambda_edge: Mapping[Any, Any],
                            rho_edge: Mapping[Any, Any], m: int, *,
                            n_samples: int, max_iter: int, seed: int,
                            entropy_tol: float = STAGE2_ENTROPY_TOL,
                            streak: int = STAGE2_STREAK) -> dict:
    """Cohen-style bit-plane decomposition at one m point: 10 independent binary
    DEs (one per plane) with the frozen same-seed protocol; the point converges
    iff EVERY plane converges (joint convergence)."""
    lam = dict(lambda_edge)
    rho = dict(rho_edge)
    rate = 1.0 - int(m) / float(N_BLOCKS)
    plane_runs: list[dict[str, Any]] = []
    for plane in range(BIT_PLANES):
        run = run_mcde(2, lam, rho, channel_mode=QSC, p=float(rates[plane]),
                       n_samples=int(n_samples), max_iter=int(max_iter),
                       seed=int(seed), entropy_tol=float(entropy_tol),
                       streak=int(streak))
        plane_runs.append({"plane": plane, "crossover": float(rates[plane]),
                           "converged": bool(run["converged"]),
                           "iterations": int(run["iterations"]),
                           "final_entropy": run["final_entropy"]})
    joint = bool(plane_runs) and all(r["converged"] for r in plane_runs)
    return {"m": int(m), "rate": float(rate), "joint_converged": joint,
            "plane_runs": plane_runs,
            "final_entropy": float(max(r["final_entropy"] or 0.0
                                       for r in plane_runs)) if plane_runs else None}


def evaluate_symbol_point(w: Any, lambda_edge: Mapping[Any, Any],
                          rho_edge: Mapping[Any, Any], m: int, *,
                          n_samples: int, max_iter: int, seed: int,
                          entropy_tol: float = STAGE2_ENTROPY_TOL,
                          streak: int = STAGE2_STREAK) -> dict:
    """Symbol-level structured DE at one m point (V14 structured branch)."""
    lam = dict(lambda_edge)
    rho = dict(rho_edge)
    rate = 1.0 - int(m) / float(N_BLOCKS)
    run = run_mcde(Q, lam, rho, channel_mode=STRUCTURED, w=w,
                   n_samples=int(n_samples), max_iter=int(max_iter),
                   seed=int(seed), entropy_tol=float(entropy_tol), streak=int(streak))
    return {"m": int(m), "rate": float(rate),
            "converged": bool(run["converged"]),
            "iterations": int(run["iterations"]),
            "final_entropy": run["final_entropy"]}


def evaluate_candidate(candidate: Mapping[str, Any], rates: Any, *,
                       n_samples: int = STAGE2_N_SAMPLES,
                       max_iter: int = STAGE2_MAX_ITER,
                       entropy_tol: float = STAGE2_ENTROPY_TOL,
                       streak: int = STAGE2_STREAK,
                       seed_root: int = STAGE2_SEED_ROOT,
                       f_limit: float = F_LIMIT) -> dict:
    """Evaluate one pre-registered candidate over the FULL point set
    ``m in {15,16,17,18}`` (no subsetting)."""
    rates_arr = _validate_plane_rates(rates)
    pid = int(candidate["profile"])
    if pid not in _ASSERT_PROFILE_IDS:
        raise ValueError(f"candidate profile {pid} not in frozen PROFILES")
    lam = _profile_lambda(pid)
    mech = str(candidate["mechanism"])
    hb = float(total_leakage_bits(rates_arr))
    points: list[dict[str, Any]] = []
    # Build the structured prior once per candidate (symbol-level mechanisms).
    w_prior = None
    if mech != "bitplane":
        w_prior = (planeweight_prior(rates_arr) if mech == "symbol_structured_weighted"
                   else bitplane_prior(rates_arr))
    for m in MS:
        m = int(m)
        rate = 1.0 - m / float(N_BLOCKS)
        rho = _struct_rho(rate, lam)
        f_achieved = float((m * 10.0 / float(N_BLOCKS)) / hb)
        seed = int(seed_root) + pid * 100 + m
        if mech == "bitplane":
            raw = evaluate_bitplane_point(rates_arr, lam, rho, m,
                                          n_samples=n_samples, max_iter=max_iter,
                                          seed=seed, entropy_tol=entropy_tol,
                                          streak=streak)
            converged = bool(raw["joint_converged"])
            final_entropy = raw["final_entropy"]
            iterations = max(r["iterations"] for r in raw["plane_runs"]) if raw["plane_runs"] else 0
        else:
            raw = evaluate_symbol_point(w_prior, lam, rho, m,
                                        n_samples=n_samples, max_iter=max_iter,
                                        seed=seed, entropy_tol=entropy_tol,
                                        streak=streak)
            converged = bool(raw["converged"])
            final_entropy = raw["final_entropy"]
            iterations = int(raw["iterations"])
        points.append({
            "candidate": str(candidate["id"]),
            "m": m, "rate": rate, "profile": pid, "lambda": lam, "rho": rho,
            "f_achieved": f_achieved,
            "converged": converged,
            "iterations": iterations,
            "final_entropy": final_entropy,
        })
    return {
        "candidate": str(candidate["id"]),
        "label": str(candidate["label"]),
        "mechanism": mech,
        "profile": pid,
        "entropy_bits_channel": hb,
        "f_limit": float(f_limit),
        "any_point_pass": bool(
            any(p["converged"] and float(p["f_achieved"]) <= float(f_limit)
                for p in points)),
        "points": points,
    }


# --------------------------------------------------------------------------- #
# stage doc + gate decision
# --------------------------------------------------------------------------- #

def build_stage2_doc(*, candidates: list[dict], rates: Any,
                     n_samples: int = STAGE2_N_SAMPLES,
                     max_iter: int = STAGE2_MAX_ITER,
                     entropy_tol: float = STAGE2_ENTROPY_TOL,
                     streak: int = STAGE2_STREAK,
                     f_limit: float = F_LIMIT) -> dict:
    """Stage 2 doc (schema ``nbldpc_v17_stage2_v1``): one candidate block with
    the full 4-point record each."""
    return {
        "schema": "nbldpc_v17_stage2_v1",
        "q": Q, "bit_planes": BIT_PLANES,
        "n_samples": int(n_samples), "max_iter": int(max_iter),
        "entropy_tol": float(entropy_tol), "streak": int(streak),
        "f_limit": float(f_limit),
        "point_set": [int(m) for m in MS],
        "candidates": candidates,
        "diagnostic_only": True,
    }


def build_gate_decision_doc(*, stage0: dict, stage1: dict, stage2: dict,
                            f_limit: float = F_LIMIT) -> dict:
    """Frozen gate decision (schema ``nbldpc_v17_gate_decision_v1``).

    PASS iff Stage 0 (both anchors) AND Stage 1 (model built) AND there exists a
    candidate point that converges with ``f_achieved <= f_limit``; a Stage 0
    failure freezes as ``mechanism_unverified`` and Stage 2 is not considered.
    """
    stage0_ok = bool(stage0.get("both_anchors_verified"))
    stage1_ok = bool(stage1.get("schema") == "nbldpc_v17_multibit_channel_model_v1")
    pass_points: list[dict] = []
    if stage0_ok and stage1_ok:
        for cand in stage2.get("candidates", []):
            for pt in cand.get("points", []):
                if pt.get("converged") and pt.get("f_achieved") is not None \
                        and float(pt["f_achieved"]) <= float(f_limit):
                    pass_points.append({**pt, "candidate": cand.get("candidate")})
    if not stage0_ok:
        gate_state = "mechanism_unverified"
    elif not stage1_ok:
        gate_state = "model_unbuilt"
    elif pass_points:
        gate_state = "pass"
    else:
        gate_state = "fail"
    winner = None
    if pass_points:
        winner = max(pass_points, key=lambda p: (float(p["f_achieved"]),
                                                  str(p.get("candidate", ""))))
    return {
        "schema": "nbldpc_v17_gate_decision_v1",
        "gate_state": gate_state,
        "stage0_mechanism_verified": stage0_ok,
        "stage1_model_built": stage1_ok,
        "exists_converged_point": bool(pass_points),
        "f_limit": float(f_limit),
        "pass_point": winner,
        "stage2_point_count": sum(len(c.get("points", []))
                                  for c in stage2.get("candidates", [])),
        "points_summary": [
            {"candidate": c.get("candidate"), "m": int(pt["m"]),
             "converged": bool(pt["converged"]),
             "f_achieved": pt.get("f_achieved"),
             "final_entropy": pt.get("final_entropy")}
            for c in stage2.get("candidates", []) for pt in c.get("points", [])],
        "diagnostic_only": True,
    }


def build_gate_manifest_doc(*, command: str, git_commit: str | None = None,
                            wall_seconds: float, peak_rss_bytes: int | None = None,
                            rss_cap_bytes: int | None = None,
                            **extra: Any) -> dict:
    """Gate run manifest (schema ``nbldpc_v17_gate_manifest_v1``)."""
    return {
        "schema": "nbldpc_v17_gate_manifest_v1",
        "command": command,
        "git_commit": git_commit,
        "wall_seconds": float(wall_seconds),
        "peak_rss_bytes": peak_rss_bytes,
        "rss_cap_bytes": rss_cap_bytes,
        "rss_cap_exceeded": bool(peak_rss_bytes is not None and rss_cap_bytes is not None
                                 and peak_rss_bytes > rss_cap_bytes),
        **extra,
    }
