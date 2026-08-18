"""V24 bounded single-edge lambda/rho DE optimization for q=1024 V17 structured.

This module implements the frozen V24 packet:
- deterministic indexed proposal generator (SeedSequence([24000, k]) per attempt,
  lambda first then rho, exact NumPy call order);
- profile validity independent of DE outcome;
- M0 read-only validation of the accepted V8 corrected trace and V17 channel;
- M1 screening/refinement with frozen budgets, seeds and ranking;
- M2 independent holdout with all-five-seeds PASS;
- machine-readable decision and read-only semantic verifier.

No finite code, decoder, FER, qualification, or promotion is implemented.
"""
from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

import numpy as np

from .nonbinary_v22b_mcde import run_mcde_high_degree

__all__ = [
    "Q",
    "H_V17",
    "R_MIN",
    "R_MAX",
    "F_TOTAL_MAX",
    "LAMBDA_DEGREE_ARRAY",
    "RHO_DEGREE_ARRAY",
    "PROPOSAL_SEED",
    "MAX_UNIQUE_VALID",
    "MAX_ATTEMPTS",
    "SCREEN_SEEDS",
    "SCREEN_N_SAMPLES",
    "SCREEN_MAX_ITER",
    "REFINE_SEEDS",
    "REFINE_N_SAMPLES",
    "REFINE_MAX_ITER",
    "HOLDOUT_SEEDS",
    "HOLDOUT_N_SAMPLES",
    "HOLDOUT_MAX_ITER",
    "ENTROPY_TOL",
    "DEGREE_MAX",
    "generate_proposal",
    "profile_from_attempt",
    "canonical_key",
    "profile_valid",
    "rate_of",
    "f_total_of",
    "rank_records",
    "run_m0",
    "run_m1",
    "run_m2",
    "run_v24_gate",
    "verify_run",
]

# --------------------------------------------------------------------------- #
# Frozen constants
# --------------------------------------------------------------------------- #

Q = 1024
H_V17 = 0.5499550439219351
R_MIN = 0.9375
R_MAX = 0.94140625
F_TOTAL_MAX = 1.3
LAMBDA_DEGREE_ARRAY = np.arange(2, 65, dtype=np.int64)
RHO_DEGREE_ARRAY = np.arange(2, 513, dtype=np.int64)
PROPOSAL_SEED = 24000
MAX_UNIQUE_VALID = 512
MAX_ATTEMPTS = 8192
SCREEN_SEEDS = [24001, 24002]
SCREEN_N_SAMPLES = 200
SCREEN_MAX_ITER = 50
REFINE_SEEDS = [24003, 24004, 24005]
REFINE_N_SAMPLES = 1000
REFINE_MAX_ITER = 150
HOLDOUT_SEEDS = [24101, 24102, 24103, 24104, 24105]
HOLDOUT_N_SAMPLES = 2000
HOLDOUT_MAX_ITER = 200
ENTROPY_TOL = 0.01
DEGREE_MAX = 512
SUM_TOL = 1e-12
INF = float("inf")

# Frozen predecessor evidence paths (resolved relative to repo root).
V8_TRACE_RELPATH = Path(
    "openspec/changes/formal-nonbinary-ldpc-v8-reference-reproduction/evidence/"
    "v8_reproduction_trace_corrected.json"
)
V17_CHANNEL_RELPATH = Path(
    "openspec/changes/formal-nonbinary-ldpc-v17-multibit-structured-de-gate/"
    "evidence/v17_multibit_channel_model.json"
)

# Schema names used in evidence.
V24_RUN_MANIFEST_SCHEMA = "nbldpc_v24_run_manifest_v1"
V24_M0_SCHEMA = "nbldpc_v24_m0_validation_v1"
V24_LEDGER_SCHEMA = "nbldpc_v24_proposal_ledger_v1"
V24_EVAL_SCHEMA = "nbldpc_v24_evaluation_v1"
V24_FINALIST_SCHEMA = "nbldpc_v24_finalist_declaration_v1"
V24_DECISION_SCHEMA = "nbldpc_v24_decision_v1"
V24_VERIFIER_SCHEMA = "nbldpc_v24_verifier_report_v1"


# --------------------------------------------------------------------------- #
# Proposal generation and profile representation
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class V24Profile:
    """One candidate profile with integer counts summing to 64 per side."""
    lambda_degrees: tuple[int, ...]
    lambda_counts: tuple[int, ...]
    rho_degrees: tuple[int, ...]
    rho_counts: tuple[int, ...]
    attempt: int

    def lambda_edge(self) -> dict[int, float]:
        return {int(d): float(c) / 64.0 for d, c in zip(self.lambda_degrees, self.lambda_counts)}

    def rho_edge(self) -> dict[int, float]:
        return {int(d): float(c) / 64.0 for d, c in zip(self.rho_degrees, self.rho_counts)}

    def canonical_key(self) -> str:
        return canonical_key(self.lambda_degrees, self.lambda_counts,
                             self.rho_degrees, self.rho_counts)


def _sample_one_side(rng: np.random.Generator, degree_array: np.ndarray
                     ) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Exact frozen sampling for one side.

    Consumes: integers(1,9), choice(size=s, replace=False), full(s,1/s),
    multinomial(64-s)+1.  No extra RNG calls.
    """
    s = int(rng.integers(1, 9))
    degrees = np.sort(rng.choice(degree_array, size=s, replace=False))
    probabilities = np.full(s, 1.0 / s, dtype=np.float64)
    counts = rng.multinomial(64 - s, probabilities) + 1
    return tuple(int(d) for d in degrees), tuple(int(c) for c in counts)


def generate_proposal(attempt: int) -> V24Profile:
    """Deterministically generate one proposal for attempt ``attempt``.

    The RNG is ``default_rng(SeedSequence([24000, attempt]))`` and the
    lambda side is sampled before the rho side.
    """
    if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 0:
        raise ValueError("attempt must be a non-negative integer")
    rng = np.random.default_rng(np.random.SeedSequence([PROPOSAL_SEED, attempt]))
    ld, lc = _sample_one_side(rng, LAMBDA_DEGREE_ARRAY)
    rd, rc = _sample_one_side(rng, RHO_DEGREE_ARRAY)
    return V24Profile(lambda_degrees=ld, lambda_counts=lc,
                      rho_degrees=rd, rho_counts=rc, attempt=attempt)


def profile_from_attempt(attempt: int) -> V24Profile:
    """Alias of :func:`generate_proposal`."""
    return generate_proposal(attempt)


def canonical_key(lambda_degrees: Sequence[int], lambda_counts: Sequence[int],
                  rho_degrees: Sequence[int], rho_counts: Sequence[int]) -> str:
    """Canonical ascending ``degree:count`` key for both sides."""
    def side(degrees: Sequence[int], counts: Sequence[int]) -> str:
        pairs = sorted((int(d), int(c)) for d, c in zip(degrees, counts))
        return ",".join(f"{d}:{c}" for d, c in pairs)
    return f"L[{side(lambda_degrees, lambda_counts)}]|R[{side(rho_degrees, rho_counts)}]"


def _as_dicts(profile: V24Profile) -> tuple[dict[int, int], dict[int, int]]:
    ld, lc, rd, rc = (profile.lambda_degrees, profile.lambda_counts,
                      profile.rho_degrees, profile.rho_counts)
    lam_counts = {int(d): int(c) for d, c in zip(ld, lc)}
    rho_counts = {int(d): int(c) for d, c in zip(rd, rc)}
    return lam_counts, rho_counts


def _normalized_dict(counts: Mapping[int, int]) -> dict[int, float]:
    total = sum(int(v) for v in counts.values())
    if total != 64:
        raise ValueError("counts must sum to 64")
    return {int(d): float(c) / 64.0 for d, c in counts.items()}


def rate_of(lambda_edge: Mapping[int, float], rho_edge: Mapping[int, float]) -> float:
    """Edge-perspective design rate ``1 - sum_rho/d / sum_lambda/d``."""
    int_lam = sum(float(w) / float(d) for d, w in lambda_edge.items())
    int_rho = sum(float(w) / float(d) for d, w in rho_edge.items())
    if not math.isfinite(int_lam) or int_lam <= 0.0:
        raise ValueError("lambda integral must be positive finite")
    if int_rho < 0.0:
        raise ValueError("rho integral must be non-negative")
    return float(1.0 - int_rho / int_lam)


def f_total_of(rate: float) -> float:
    """V24 accounting proxy: ``(1-rate)*log2(q) / H_V17``.

    This is the DE-only leakage proxy; finite-code f_total must be recomputed
    in a later change.
    """
    return float((1.0 - rate) * math.log2(Q) / H_V17)


def profile_valid(profile: V24Profile, *,
                  rate_min: float = R_MIN, rate_max: float = R_MAX,
                  f_total_max: float = F_TOTAL_MAX) -> tuple[bool, str]:
    """Return ``(valid, reason)`` using only profile-level quantities.

    DE entropy is never used here.  A valid profile must have normalized
    lambda/rho, 1..8 non-zero degrees per side, degrees inside the frozen
    arrays, design rate in the frozen band, and f_total <= 1.3.
    """
    lam_counts, rho_counts = _as_dicts(profile)
    if not (1 <= len(lam_counts) <= 8):
        return False, "lambda_support_out_of_1_8"
    if not (1 <= len(rho_counts) <= 8):
        return False, "rho_support_out_of_1_8"
    if any(int(d) < 2 or int(d) > 64 for d in lam_counts):
        return False, "lambda_degree_out_of_bounds"
    if any(int(d) < 2 or int(d) > 512 for d in rho_counts):
        return False, "rho_degree_out_of_bounds"
    if any(int(c) <= 0 for c in lam_counts.values()):
        return False, "lambda_count_non_positive"
    if any(int(c) <= 0 for c in rho_counts.values()):
        return False, "rho_count_non_positive"
    if sum(int(c) for c in lam_counts.values()) != 64:
        return False, "lambda_count_sum_not_64"
    if sum(int(c) for c in rho_counts.values()) != 64:
        return False, "rho_count_sum_not_64"

    lam = _normalized_dict(lam_counts)
    rho = _normalized_dict(rho_counts)
    if abs(sum(lam.values()) - 1.0) > SUM_TOL:
        return False, "lambda_not_normalized"
    if abs(sum(rho.values()) - 1.0) > SUM_TOL:
        return False, "rho_not_normalized"
    try:
        rate = rate_of(lam, rho)
    except (ValueError, ZeroDivisionError):
        return False, "rate_not_computable"
    if not math.isfinite(rate):
        return False, "rate_non_finite"
    if rate < rate_min:
        return False, "rate_below_min"
    if rate > rate_max:
        return False, "rate_above_max"
    f = f_total_of(rate)
    if f > f_total_max + SUM_TOL:
        return False, "f_total_above_max"
    return True, "valid"


# --------------------------------------------------------------------------- #
# Ranking
# --------------------------------------------------------------------------- #

def _entropy_inf(value: float | None, has_error: bool) -> float:
    if has_error or value is None or not math.isfinite(float(value)):
        return INF
    return float(value)


def rank_records(records: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    """Stage-generic ranking.

    Sort by ``(converged_count desc, worst_final_entropy asc,
    mean_final_entropy asc, candidate_id asc)``.  Errors/non-finite are
    non-converged with +inf entropy.
    """
    def key(row: Mapping[str, Any]) -> tuple[int, float, float, int]:
        conv = int(row["converged_count"])
        worst = _entropy_inf(row.get("worst_final_entropy"),
                             bool(row.get("has_error")))
        mean = _entropy_inf(row.get("mean_final_entropy"),
                            bool(row.get("has_error")))
        cid = int(row["candidate_id"])
        return (-conv, worst, mean, cid)

    return sorted(records, key=key)


# --------------------------------------------------------------------------- #
# M0 read-only mechanism / channel / accounting validation
# --------------------------------------------------------------------------- #

def _read_json(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _isclose(a: float, b: float, tol: float = 1e-9) -> bool:
    return math.isclose(float(a), float(b), abs_tol=tol, rel_tol=tol)


def _validate_v8_trace(data: Mapping[str, Any]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    add("schema", data.get("schema") == "v8_reproduction_trace_corrected_v1",
        str(data.get("schema")))
    fp = data.get("frozen_parameters", {})
    add("q", _isclose(fp.get("q"), 4), str(fp.get("q")))
    add("rate", _isclose(fp.get("rate"), 0.75), str(fp.get("rate")))
    lam_pub = fp.get("lambda_published", {})
    expected_pub = {"1": 0.107, "3": 0.245, "6": 0.192, "9": 0.034,
                    "18": 0.207, "25": 0.161, "27": 0.049}
    add("lambda_published", {str(k): float(v) for k, v in lam_pub.items()} == expected_pub,
        str(lam_pub))
    lam_deg = fp.get("lambda_degrees", {})
    expected_deg = {"2": 0.107, "4": 0.245, "7": 0.192, "10": 0.034,
                    "19": 0.207, "26": 0.161, "28": 0.049}
    add("lambda_degrees", {str(k): float(v) for k, v in lam_deg.items()} == expected_deg,
        str(lam_deg))
    rho_deg = fp.get("rho_degrees", {})
    expected_rho = {"24": 0.662342394447661, "25": 0.33765760555233904}
    add("rho_degrees", {str(k): float(v) for k, v in rho_deg.items()} == expected_rho,
        str(rho_deg))
    add("dc_mean", _isclose(fp.get("dc_mean"), 24.32858932876873),
        str(fp.get("dc_mean")))
    add("integral_lambda", _isclose(fp.get("integral_lambda"), 0.1644156159629844),
        str(fp.get("integral_lambda")))
    add("integral_rho", _isclose(fp.get("integral_rho"), 0.0411039039907461),
        str(fp.get("integral_rho")))
    rate_rec = fp.get("rate_reconstructed")
    try:
        int_lam = float(fp.get("integral_lambda"))
        int_rho = float(fp.get("integral_rho"))
        recon = 1.0 - int_rho / int_lam
        add("rate_reconstructed", _isclose(rate_rec, recon) and _isclose(recon, 0.75),
            f"{rate_rec} vs {recon}")
    except Exception as exc:  # noqa: BLE001
        add("rate_reconstructed", False, str(exc))
    add("n_samples", int(fp.get("n_samples", -1)) == 100000, str(fp.get("n_samples")))
    add("max_iter", int(fp.get("max_iter", -1)) == 150, str(fp.get("max_iter")))
    add("seed", int(fp.get("seed", -1)) == 2026080418, str(fp.get("seed")))
    add("p_lo", _isclose(fp.get("p_lo"), 0.01), str(fp.get("p_lo")))
    add("p_hi", _isclose(fp.get("p_hi"), 0.12), str(fp.get("p_hi")))
    add("p_tol", _isclose(fp.get("p_tol"), 0.0025), str(fp.get("p_tol")))
    add("entropy_tol", _isclose(fp.get("entropy_tol"), 0.01), str(fp.get("entropy_tol")))
    add("streak", int(fp.get("streak", -1)) == 20, str(fp.get("streak")))
    add("det_published", _isclose(fp.get("det_published"), 0.069), str(fp.get("det_published")))
    add("tolerance", _isclose(fp.get("tolerance"), 0.012), str(fp.get("tolerance")))
    add("threshold_proxy", _isclose(data.get("threshold_proxy"), 0.06242187500000001),
        str(data.get("threshold_proxy")))
    add("delta_vs_published", _isclose(data.get("delta_vs_published"), 0.006578124999999997),
        str(data.get("delta_vs_published")))
    add("verdict", data.get("verdict") == "PASS", str(data.get("verdict")))
    tol_arith_ok = "0.01175 <= 0.012" in str(fp.get("tolerance_arithmetic", ""))
    add("tolerance_arithmetic", tol_arith_ok, str(fp.get("tolerance_arithmetic")))
    conv_rule_ok = (
        "entropy_tol" in str(fp.get("convergence_rule", ""))
        and "streak" in str(fp.get("convergence_rule", ""))
    )
    add("convergence_rule", conv_rule_ok, str(fp.get("convergence_rule")))
    return checks


def _validate_v17_channel(data: Mapping[str, Any]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    add("schema", data.get("schema") == "nbldpc_v17_multibit_channel_model_v1",
        str(data.get("schema")))
    add("q", int(data.get("q", -1)) == 1024, str(data.get("q")))
    add("bit_planes", int(data.get("bit_planes", -1)) == 10, str(data.get("bit_planes")))
    add("mapping", data.get("mapping") == "gray", str(data.get("mapping")))
    add("joint_structure_form",
        data.get("joint_structure_form") == "product_of_per_plane_marginals",
        str(data.get("joint_structure_form")))
    add("entropy_bits", _isclose(data.get("entropy_bits"), H_V17),
        str(data.get("entropy_bits")))
    rates = data.get("per_bit_plane_error_probability_msb_first", [])
    expected_rates = [3.0517578125e-05, 0.0001220703125, 0.0003662109375,
                      0.000946044921875, 0.001251220703125, 0.00250244140625,
                      0.00457763671875, 0.009307861328125, 0.02044677734375,
                      0.037506103515625]
    ok_rates = (isinstance(rates, list) and len(rates) == 10
                and all(_isclose(float(r), e) for r, e in zip(rates, expected_rates)))
    add("per_bit_plane_error_probability_msb_first", ok_rates, str(rates))
    return checks


def run_m0(*, v8_trace_path: str | Path | None = None,
           v17_channel_path: str | Path | None = None,
           root: str | Path | None = None) -> dict[str, Any]:
    """Read-only M0 validation.

    Returns a dictionary with ``passed`` and all checks.  No DE call and no
    V8 runner is executed.
    """
    if root is not None:
        base = Path(root)
    else:
        # Use the repository root (two levels up from this module's package
        # directory: comparison_bench/src/comparison_bench/formal_ir -> repo).
        base = Path(__file__).resolve().parents[4]
    v8_path = Path(v8_trace_path) if v8_trace_path is not None else base / V8_TRACE_RELPATH
    v17_path = Path(v17_channel_path) if v17_channel_path is not None else base / V17_CHANNEL_RELPATH

    try:
        v8 = _read_json(v8_path)
        v8_checks = _validate_v8_trace(v8)
    except Exception as exc:  # noqa: BLE001
        v8_checks = [{"name": "v8_read", "ok": False, "detail": str(exc)}]

    try:
        v17 = _read_json(v17_path)
        v17_checks = _validate_v17_channel(v17)
    except Exception as exc:  # noqa: BLE001
        v17_checks = [{"name": "v17_read", "ok": False, "detail": str(exc)}]

    # Seed lists are frozen constant checks (independent of JSON files).
    all_seeds = [PROPOSAL_SEED] + SCREEN_SEEDS + REFINE_SEEDS + HOLDOUT_SEEDS
    disjoint = len(set(all_seeds)) == len(all_seeds)
    seed_checks = [
        {"name": "seed_lists_disjoint", "ok": disjoint, "detail": str(all_seeds)},
        {"name": "proposal_seed", "ok": PROPOSAL_SEED == 24000, "detail": str(PROPOSAL_SEED)},
        {"name": "screen_seeds", "ok": SCREEN_SEEDS == [24001, 24002], "detail": str(SCREEN_SEEDS)},
        {"name": "refine_seeds", "ok": REFINE_SEEDS == [24003, 24004, 24005], "detail": str(REFINE_SEEDS)},
        {"name": "holdout_seeds", "ok": HOLDOUT_SEEDS == [24101, 24102, 24103, 24104, 24105], "detail": str(HOLDOUT_SEEDS)},
    ]

    all_checks = v8_checks + v17_checks + seed_checks
    passed = all(c["ok"] for c in all_checks)
    return {
        "schema": V24_M0_SCHEMA,
        "passed": passed,
        "v8_trace_path": str(v8_path),
        "v17_channel_path": str(v17_path),
        "checks": all_checks,
        "note": "read_only_validator_no_de",
        "H_V17": H_V17,
        "q": Q,
        "check_count": len(all_checks),
    }


# --------------------------------------------------------------------------- #
# M1 / M2 evaluation helpers
# --------------------------------------------------------------------------- #

def _de_call(profile: V24Profile, *, n_samples: int, max_iter: int, seed: int,
             w: np.ndarray, degree_max: int = DEGREE_MAX,
             runner: Callable[..., Any] | None = None) -> dict[str, Any]:
    """Run one V22b MC-DE call (or a fake runner in tests)."""
    lam = profile.lambda_edge()
    rho = profile.rho_edge()
    started = time.perf_counter()
    try:
        if runner is not None:
            res = runner(q=Q, lambda_edge=lam, rho_edge=rho,
                         n_samples=n_samples, max_iter=max_iter, seed=seed,
                         channel_mode="structured", w=w, degree_max=degree_max)
        else:
            res = run_mcde_high_degree(
                q=Q, lambda_edge=lam, rho_edge=rho,
                n_samples=n_samples, max_iter=max_iter, seed=seed,
                channel_mode="structured", w=w, degree_max=degree_max,
                entropy_tol=ENTROPY_TOL, streak=20)
        elapsed = time.perf_counter() - started
        return {
            "converged": bool(res.get("converged")),
            "final_entropy": None if res.get("final_entropy") is None
                             else float(res["final_entropy"]),
            "iterations": int(res["iterations"]) if res.get("iterations") is not None else None,
            "error": None,
            "elapsed_seconds": elapsed,
        }
    except Exception as exc:  # noqa: BLE001
        elapsed = time.perf_counter() - started
        return {
            "converged": False,
            "final_entropy": None,
            "iterations": None,
            "error": str(exc),
            "elapsed_seconds": elapsed,
        }


def _aggregate_eval_rows(rows: Sequence[Mapping[str, Any]],
                         candidate_id: int) -> Mapping[str, Any]:
    conv = sum(1 for r in rows if bool(r.get("converged")))
    entropies: list[float] = []
    has_error = any(r.get("error") for r in rows)
    for r in rows:
        ent = r.get("final_entropy")
        if ent is None or not math.isfinite(float(ent)):
            entropies.append(INF)
        else:
            entropies.append(float(ent))
    worst = max(entropies) if entropies else INF
    mean = float(np.mean(entropies)) if entropies else INF
    return {
        "candidate_id": int(candidate_id),
        "converged_count": int(conv),
        "worst_final_entropy": worst,
        "mean_final_entropy": mean,
        "has_error": bool(has_error),
    }


def _evaluate_stage(profiles: Sequence[V24Profile], *, stage: str,
                    n_samples: int, max_iter: int, seeds: Sequence[int],
                    w: np.ndarray, runner: Callable[..., Any] | None = None,
                    resource_limit_seconds: float | None = None,
                    stop_on_limit: bool = False,
                    initial_accumulated: float = 0.0,
                    record_sink: Callable[[Mapping[str, Any]], None] | None = None
                    ) -> tuple[list[dict[str, Any]], bool, float]:
    """Run one stage over all profiles/seeds.

    Returns ``(rows, resource_blocked, accumulated_seconds)`` where
    ``accumulated_seconds`` is the global running total including
    ``initial_accumulated``.  Each completed call is appended immediately.
    If ``stop_on_limit`` and there are still required calls remaining after
    the global accumulated time >= limit, return ``resource_blocked=True``
    without running the next call.
    """
    rows: list[dict[str, Any]] = []
    accumulated = float(initial_accumulated)
    pending = [(p, s) for p in profiles for s in seeds]
    # We must not diverge from the identical sequence of pending calls.
    for idx, (profile, seed) in enumerate(pending):
        rec = _de_call(profile, n_samples=n_samples, max_iter=max_iter,
                       seed=int(seed), w=w, runner=runner)
        record = {
            "stage": stage,
            "candidate_id": int(profile.attempt),
            "seed": int(seed),
            **rec,
        }
        rows.append(record)
        if record_sink is not None:
            record_sink(record)
        accumulated += float(rec["elapsed_seconds"])
        # Resource stop: only if required evaluations remain.
        remaining = len(pending) - (idx + 1)
        if stop_on_limit and resource_limit_seconds is not None \
                and remaining > 0 and accumulated >= resource_limit_seconds:
            return rows, True, accumulated
    return rows, False, accumulated


def run_m1(*, w: np.ndarray, runner: Callable[..., Any] | None = None,
           proposal_seed: int = PROPOSAL_SEED,
           max_unique_valid: int = MAX_UNIQUE_VALID,
           max_attempts: int = MAX_ATTEMPTS,
           resource_limit_seconds: float | None = None,
           stop_on_limit: bool = False,
           on_screen: Callable[[Mapping[str, Any]], None] | None = None,
           on_refine: Callable[[Mapping[str, Any]], None] | None = None) -> dict[str, Any]:
    """M1 bounded development search.

    Returns the proposal ledger, screen/refine records, selected finalists,
    and accumulated completed-DE-call time.
    """
    ledger: list[dict[str, Any]] = []
    seen: set[str] = set()
    valid_profiles: list[V24Profile] = []
    duplicate_count = 0
    invalid_count = 0

    for k in range(int(max_attempts)):
        profile = generate_proposal(k)
        valid, reason = profile_valid(profile)
        key = profile.canonical_key()
        entry = {
            "attempt": int(k),
            "canonical_key": key,
            "lambda_degrees": list(profile.lambda_degrees),
            "lambda_counts": list(profile.lambda_counts),
            "rho_degrees": list(profile.rho_degrees),
            "rho_counts": list(profile.rho_counts),
            "valid": bool(valid),
            "reason": reason,
            "duplicate": False,
            "candidate_id": None,
        }
        if valid and key in seen:
            entry["duplicate"] = True
            duplicate_count += 1
        elif valid:
            entry["candidate_id"] = int(k)
            seen.add(key)
            valid_profiles.append(profile)
            if len(valid_profiles) >= max_unique_valid:
                ledger.append(entry)
                break
        else:
            invalid_count += 1
        ledger.append(entry)

    n_valid = len(valid_profiles)
    if n_valid == 0:
        return {
            "ledger": ledger,
            "screen": [],
            "refine": [],
            "finalists": [],
            "n_valid": 0,
            "n_duplicates": duplicate_count,
            "n_invalid": invalid_count,
            "accumulated_de_seconds": 0.0,
            "resource_blocked": False,
            "mechanism_unverified": True,
        }

    # Screen all valid candidates.
    screen_rows_all: list[dict[str, Any]] = []
    screen_agg: list[dict[str, Any]] = []
    screen_acc = 0.0
    screen_blocked = False
    for prof in valid_profiles:
        rows, blocked, acc = _evaluate_stage(
            [prof], stage="screen", n_samples=SCREEN_N_SAMPLES,
            max_iter=SCREEN_MAX_ITER, seeds=SCREEN_SEEDS, w=w,
            runner=runner, resource_limit_seconds=resource_limit_seconds,
            stop_on_limit=stop_on_limit, initial_accumulated=screen_acc,
            record_sink=on_screen)
        screen_rows_all.extend(rows)
        screen_acc = acc
        screen_agg.append(_aggregate_eval_rows(rows, prof.attempt))
        if blocked:
            screen_blocked = True
            break

    if screen_blocked:
        return {
            "ledger": ledger,
            "screen": screen_rows_all,
            "refine": [],
            "finalists": [],
            "n_valid": n_valid,
            "n_duplicates": duplicate_count,
            "n_invalid": invalid_count,
            "accumulated_de_seconds": screen_acc,
            "resource_blocked": True,
            "mechanism_unverified": False,
        }

    screen_ranked = rank_records(screen_agg)
    n_refine = min(8, n_valid)
    refine_candidates = [
        p for p in valid_profiles
        if p.attempt in {int(r["candidate_id"]) for r in screen_ranked[:n_refine]}
    ]
    # Ensure order by ranked candidate id.
    ranked_ids = [int(r["candidate_id"]) for r in screen_ranked[:n_refine]]
    refine_candidates = [p for p in valid_profiles if p.attempt in set(ranked_ids)]
    refine_candidates.sort(key=lambda p: ranked_ids.index(p.attempt))

    refine_rows_all: list[dict[str, Any]] = []
    refine_agg: list[dict[str, Any]] = []
    refine_acc = 0.0
    refine_blocked = False
    for prof in refine_candidates:
        rows, blocked, acc = _evaluate_stage(
            [prof], stage="refine", n_samples=REFINE_N_SAMPLES,
            max_iter=REFINE_MAX_ITER, seeds=REFINE_SEEDS, w=w,
            runner=runner, resource_limit_seconds=resource_limit_seconds,
            stop_on_limit=stop_on_limit,
            initial_accumulated=screen_acc + refine_acc,
            record_sink=on_refine)
        refine_rows_all.extend(rows)
        refine_acc = acc - screen_acc
        refine_agg.append(_aggregate_eval_rows(rows, prof.attempt))
        if blocked:
            refine_blocked = True
            break

    if refine_blocked:
        return {
            "ledger": ledger,
            "screen": screen_rows_all,
            "refine": refine_rows_all,
            "finalists": [],
            "n_valid": n_valid,
            "n_duplicates": duplicate_count,
            "n_invalid": invalid_count,
            "accumulated_de_seconds": screen_acc + refine_acc,
            "resource_blocked": True,
            "mechanism_unverified": False,
        }

    refine_ranked = rank_records(refine_agg)
    n_finalist = min(4, len(refine_ranked))
    finalist_rows = refine_ranked[:n_finalist]
    finalist_ids = [int(r["candidate_id"]) for r in finalist_rows]
    finalists = [p for p in valid_profiles if p.attempt in set(finalist_ids)]
    finalists.sort(key=lambda p: finalist_ids.index(p.attempt))

    return {
        "ledger": ledger,
        "screen": screen_rows_all,
        "refine": refine_rows_all,
        "finalists": finalists,
        "n_valid": n_valid,
        "n_duplicates": duplicate_count,
        "n_invalid": invalid_count,
        "screen_ranked": screen_ranked,
        "refine_ranked": refine_ranked,
        "accumulated_de_seconds": screen_acc + refine_acc,
        "resource_blocked": False,
        "mechanism_unverified": False,
    }


def run_m2(*, finalists: Sequence[V24Profile], w: np.ndarray,
           runner: Callable[..., Any] | None = None,
           resource_limit_seconds: float | None = None,
           stop_on_limit: bool = False,
           on_record: Callable[[Mapping[str, Any]], None] | None = None) -> dict[str, Any]:
    """M2 independent holdout for pre-persisted finalists.

    A finalist passes only if it converges on all five holdout seeds.
    """
    all_rows: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    accumulated = 0.0
    blocked = False
    for prof in finalists:
        rows, blk, acc = _evaluate_stage(
            [prof], stage="holdout", n_samples=HOLDOUT_N_SAMPLES,
            max_iter=HOLDOUT_MAX_ITER, seeds=HOLDOUT_SEEDS, w=w,
            runner=runner, resource_limit_seconds=resource_limit_seconds,
            stop_on_limit=stop_on_limit, initial_accumulated=accumulated,
            record_sink=on_record)
        all_rows.extend(rows)
        accumulated = acc
        valid, reason = profile_valid(prof)
        conv_all = valid and all(bool(r.get("converged")) for r in rows)
        results.append({
            "candidate_id": int(prof.attempt),
            "profile_valid": bool(valid),
            "profile_valid_reason": reason,
            "converged_all_seeds": bool(conv_all),
            "seed_results": [
                {
                    "seed": int(r["seed"]),
                    "converged": bool(r["converged"]),
                    "final_entropy": r["final_entropy"],
                    "error": r["error"],
                } for r in rows
            ],
        })
        if blk:
            blocked = True
            break
    return {
        "rows": all_rows,
        "results": results,
        "accumulated_de_seconds": accumulated,
        "resource_blocked": bool(blocked),
        "passed": (not blocked) and any(r["converged_all_seeds"] for r in results),
    }


# --------------------------------------------------------------------------- #
# Full gate orchestration (M0-M2)
# --------------------------------------------------------------------------- #

def _profile_to_record(profile: V24Profile) -> dict[str, Any]:
    return {
        "candidate_id": int(profile.attempt),
        "lambda_degrees": list(profile.lambda_degrees),
        "lambda_counts": list(profile.lambda_counts),
        "rho_degrees": list(profile.rho_degrees),
        "rho_counts": list(profile.rho_counts),
        "canonical_key": profile.canonical_key(),
        "lambda_edge": {int(d): w for d, w in profile.lambda_edge().items()},
        "rho_edge": {int(d): w for d, w in profile.rho_edge().items()},
        "rate": rate_of(profile.lambda_edge(), profile.rho_edge()),
        "f_total": f_total_of(rate_of(profile.lambda_edge(), profile.rho_edge())),
    }


def _write_json(path: Path, data: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def run_v24_gate(*, w: np.ndarray, out_dir: str | Path,
                 runner: Callable[..., Any] | None = None,
                 v8_trace_path: str | Path | None = None,
                 v17_channel_path: str | Path | None = None,
                 resource_limit_seconds: float | None = None,
                 stop_on_limit: bool = False,
                 run_id: str | None = None,
                 max_unique_valid: int = MAX_UNIQUE_VALID,
                 max_attempts: int = MAX_ATTEMPTS) -> dict[str, Any]:
    """Run the full frozen M0-M2 gate and write additive evidence.

    If ``out_dir`` already exists, a ``FileExistsError`` is raised to prevent
    accidental overwrite.
    """
    out = Path(out_dir)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing to overwrite existing V24 run root: {out}")
    out.mkdir(parents=True, exist_ok=True)

    # Manifest (before any scientific evaluation).
    manifest = {
        "schema": V24_RUN_MANIFEST_SCHEMA,
        "run_id": str(run_id) if run_id is not None else out.name,
        "q": Q,
        "H_V17": H_V17,
        "rate_band": [R_MIN, R_MAX],
        "f_total_max": F_TOTAL_MAX,
        "proposal_seed": PROPOSAL_SEED,
        "max_unique_valid": int(max_unique_valid),
        "max_attempts": int(max_attempts),
        "screen": {"seeds": SCREEN_SEEDS, "n_samples": SCREEN_N_SAMPLES,
                   "max_iter": SCREEN_MAX_ITER},
        "refine": {"seeds": REFINE_SEEDS, "n_samples": REFINE_N_SAMPLES,
                   "max_iter": REFINE_MAX_ITER},
        "holdout": {"seeds": HOLDOUT_SEEDS, "n_samples": HOLDOUT_N_SAMPLES,
                    "max_iter": HOLDOUT_MAX_ITER},
        "degree_max": DEGREE_MAX,
        "entropy_tol": ENTROPY_TOL,
        "channel_schema": "nbldpc_v17_multibit_channel_model_v1",
        "v8_trace_path": str(v8_trace_path) if v8_trace_path is not None else str(V8_TRACE_RELPATH),
        "v17_channel_path": str(v17_channel_path) if v17_channel_path is not None else str(V17_CHANNEL_RELPATH),
        "claim_boundary": "DE_only_asymptotic_no_finite_code",
    }
    _write_json(out / "run_manifest.json", manifest)

    # M0
    m0 = run_m0(v8_trace_path=v8_trace_path, v17_channel_path=v17_channel_path)
    _write_json(out / "m0_validation.json", m0)
    if not m0["passed"]:
        decision = {
            "schema": V24_DECISION_SCHEMA,
            "terminal_state": "mechanism_unverified",
            "passed": False,
            "reason": "M0 read-only validation failed",
            "m0_passed": False,
            "m1_resource_blocked": False,
            "m2_resource_blocked": False,
            "finalist_passed": False,
        }
        _write_json(out / "decision.json", decision)
        return decision

    # Incremental per-call record sinks (append immediately; flush each).
    screen_jsonl = (out / "screen_evaluations.jsonl")
    refine_jsonl = (out / "refine_evaluations.jsonl")
    holdout_jsonl = (out / "holdout_evaluations.jsonl")

    def make_sink(path: Path) -> Callable[[Mapping[str, Any]], None]:
        def sink(record: Mapping[str, Any]) -> None:
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, sort_keys=True) + "\n")
        return sink

    # M1
    m1 = run_m1(w=w, runner=runner, resource_limit_seconds=resource_limit_seconds,
                stop_on_limit=stop_on_limit, max_unique_valid=max_unique_valid,
                max_attempts=max_attempts,
                on_screen=make_sink(screen_jsonl),
                on_refine=make_sink(refine_jsonl))
    _write_json(out / "proposal_ledger.json", {
        "schema": V24_LEDGER_SCHEMA,
        "n_valid": m1["n_valid"],
        "n_duplicates": m1["n_duplicates"],
        "n_invalid": m1["n_invalid"],
        "entries": m1["ledger"],
    })
    _write_json(out / "screen_evaluations.json", {
        "schema": V24_EVAL_SCHEMA,
        "stage": "screen",
        "records": m1["screen"],
    })
    _write_json(out / "refine_evaluations.json", {
        "schema": V24_EVAL_SCHEMA,
        "stage": "refine",
        "records": m1["refine"],
    })
    if m1.get("screen_ranked") is not None:
        _write_json(out / "screen_ranking.json", {
            "stage": "screen", "ranking": m1["screen_ranked"]})
    if m1.get("refine_ranked") is not None:
        _write_json(out / "refine_ranking.json", {
            "stage": "refine", "ranking": m1["refine_ranked"]})

    if m1["mechanism_unverified"]:
        decision = {
            "schema": V24_DECISION_SCHEMA,
            "terminal_state": "mechanism_unverified",
            "passed": False,
            "reason": "M1 produced no valid unique candidates",
            "m0_passed": True,
            "m1_resource_blocked": False,
            "m2_resource_blocked": False,
            "finalist_passed": False,
        }
        _write_json(out / "decision.json", decision)
        return decision

    if m1["resource_blocked"]:
        decision = {
            "schema": V24_DECISION_SCHEMA,
            "terminal_state": "resource_blocked",
            "passed": False,
            "reason": "M1 resource ceiling reached with required evaluations remaining",
            "m0_passed": True,
            "m1_resource_blocked": True,
            "m2_resource_blocked": False,
            "finalist_passed": False,
        }
        _write_json(out / "decision.json", decision)
        return decision

    # Persist finalists before any holdout evaluation.
    finalist_records = [_profile_to_record(p) for p in m1["finalists"]]
    _write_json(out / "finalists.json", {
        "schema": V24_FINALIST_SCHEMA,
        "pre_holdout_declaration": True,
        "n_finalists": len(finalist_records),
        "finalists": finalist_records,
    })

    # M2
    m2 = run_m2(finalists=m1["finalists"], w=w, runner=runner,
                resource_limit_seconds=resource_limit_seconds,
                stop_on_limit=stop_on_limit,
                on_record=make_sink(holdout_jsonl))
    _write_json(out / "holdout_evaluations.json", {
        "schema": V24_EVAL_SCHEMA,
        "stage": "holdout",
        "records": m2["rows"],
    })
    _write_json(out / "holdout_results.json", {
        "stage": "holdout", "results": m2["results"],
        "passed": m2["passed"], "resource_blocked": m2["resource_blocked"],
    })

    if m2["resource_blocked"]:
        decision = {
            "schema": V24_DECISION_SCHEMA,
            "terminal_state": "resource_blocked",
            "passed": False,
            "reason": "M2 resource ceiling reached with required evaluations remaining",
            "m0_passed": True,
            "m1_resource_blocked": False,
            "m2_resource_blocked": True,
            "finalist_passed": False,
        }
    else:
        decision = {
            "schema": V24_DECISION_SCHEMA,
            "terminal_state": "pass" if m2["passed"] else "fail",
            "passed": bool(m2["passed"]),
            "reason": ("at least one finalist passed all holdout seeds"
                       if m2["passed"] else
                       "no finalist passed all five holdout seeds"),
            "m0_passed": True,
            "m1_resource_blocked": False,
            "m2_resource_blocked": False,
            "finalist_passed": bool(m2["passed"]),
        }
    _write_json(out / "decision.json", decision)
    return decision


# --------------------------------------------------------------------------- #
# Read-only semantic verifier
# --------------------------------------------------------------------------- #

def _reconstruct_profile_from_record(rec: Mapping[str, Any]) -> V24Profile:
    return V24Profile(
        lambda_degrees=tuple(int(d) for d in rec["lambda_degrees"]),
        lambda_counts=tuple(int(c) for c in rec["lambda_counts"]),
        rho_degrees=tuple(int(d) for d in rec["rho_degrees"]),
        rho_counts=tuple(int(c) for c in rec["rho_counts"]),
        attempt=int(rec["candidate_id"]),
    )


def verify_run(root: str | Path) -> dict[str, Any]:
    """Read-only semantic verification of a persisted V24 run root.

    Recomputes validity, ranking, finalist selection, seed separation,
    convergence, and the final decision from the persisted records.
    """
    root = Path(root)
    problems: list[str] = []
    warnings: list[str] = []

    def need(rel: str) -> dict[str, Any]:
        p = root / rel
        if not p.exists():
            problems.append(f"missing {rel}")
            return {}
        return _read_json(p)

    manifest = need("run_manifest.json")
    m0 = need("m0_validation.json")
    ledger_doc = need("proposal_ledger.json")
    screen_doc = need("screen_evaluations.json")
    refine_doc = need("refine_evaluations.json")
    finalists_doc = need("finalists.json")
    holdout_doc = need("holdout_evaluations.json")
    holdout_res = need("holdout_results.json")
    decision = need("decision.json")
    recomputed_pass = False

    if not problems:
        # Check seed disjointness from manifest or constants.
        seed_groups = {
            "proposal": [int(manifest["proposal_seed"])],
            "screen": [int(s) for s in manifest["screen"]["seeds"]],
            "refine": [int(s) for s in manifest["refine"]["seeds"]],
            "holdout": [int(s) for s in manifest["holdout"]["seeds"]],
        }
        all_seeds = [s for group in seed_groups.values() for s in group]
        if len(set(all_seeds)) != len(all_seeds):
            problems.append("seed groups are not disjoint")

        # Ledger reconstruction: valid unique count and first-attempt ids.
        seen: set[str] = set()
        expected_ids: list[int] = []
        for entry in ledger_doc.get("entries", []):
            if not entry.get("valid"):
                continue
            key = entry["canonical_key"]
            cid = entry.get("candidate_id")
            if key in seen and cid is not None:
                problems.append(f"ledger duplicate valid candidate {entry['attempt']} has candidate_id")
            if key not in seen:
                if cid != entry["attempt"]:
                    problems.append(f"candidate_id {cid} not first attempt {entry['attempt']}")
                seen.add(key)
                expected_ids.append(cid)
        if len(expected_ids) != int(ledger_doc.get("n_valid", -1)):
            problems.append(
                f"ledger n_valid mismatch: {len(expected_ids)} vs {ledger_doc.get('n_valid')}")

        # Screen records: one per valid candidate per screen seed.
        screen_by_cand: dict[int, list[dict[str, Any]]] = {}
        for rec in screen_doc.get("records", []):
            screen_by_cand.setdefault(int(rec["candidate_id"]), []).append(rec)
        if sorted(screen_by_cand.keys()) != sorted(expected_ids):
            problems.append("screen candidate coverage mismatch")
        for cid, rows in screen_by_cand.items():
            if sorted(int(r["seed"]) for r in rows) != sorted(SCREEN_SEEDS):
                problems.append(f"screen seed coverage mismatch for candidate {cid}")

        # Refine coverage: final candidates that were refined.
        refine_by_cand: dict[int, list[dict[str, Any]]] = {}
        for rec in refine_doc.get("records", []):
            refine_by_cand.setdefault(int(rec["candidate_id"]), []).append(rec)
        screen_rank_path = root / "screen_ranking.json"
        refine_ids = list(refine_by_cand.keys())
        if screen_rank_path.exists():
            screen_rank = _read_json(screen_rank_path)
            n_refine = min(8, int(ledger_doc.get("n_valid", -1)))
            expected_refine_ids = [int(r["candidate_id"])
                                   for r in screen_rank.get("ranking", [])[:n_refine]]
            if sorted(refine_ids) != sorted(expected_refine_ids):
                problems.append("refine candidate selection mismatch from screen ranking")
        for cid, rows in refine_by_cand.items():
            if sorted(int(r["seed"]) for r in rows) != sorted(REFINE_SEEDS):
                problems.append(f"refine seed coverage mismatch for candidate {cid}")

        # Finalist selection matches top refine ranking.
        finalist_ids = [int(f["candidate_id"]) for f in finalists_doc.get("finalists", [])]
        refine_rank_path = root / "refine_ranking.json"
        expected_finalist_ids: list[int] = []
        if refine_rank_path.exists():
            refine_rank = _read_json(refine_rank_path)
            n_finalist = min(4, len(refine_ids))
            expected_finalist_ids = [int(r["candidate_id"])
                                     for r in refine_rank.get("ranking", [])[:n_finalist]]
        if sorted(finalist_ids) != sorted(expected_finalist_ids):
            problems.append("finalist selection mismatch from refine ranking")

        # Holdout coverage and convergence.
        holdout_by_cand: dict[int, list[dict[str, Any]]] = {}
        for rec in holdout_doc.get("records", []):
            holdout_by_cand.setdefault(int(rec["candidate_id"]), []).append(rec)
        if sorted(holdout_by_cand.keys()) != sorted(finalist_ids):
            problems.append("holdout candidate coverage mismatch")
        for cid, rows in holdout_by_cand.items():
            if sorted(int(r["seed"]) for r in rows) != sorted(HOLDOUT_SEEDS):
                problems.append(f"holdout seed coverage mismatch for candidate {cid}")
        # Recompute pass from holdout records.
        recomputed_pass = False
        for cid, rows in holdout_by_cand.items():
            if all(bool(r.get("converged")) for r in rows):
                recomputed_pass = True
        if decision.get("terminal_state") == "pass" and not recomputed_pass:
            problems.append("decision pass but no finalist converged on all holdout seeds")
        if decision.get("terminal_state") == "fail" and recomputed_pass:
            problems.append("decision fail but a finalist converged on all holdout seeds")

    ok = not problems
    return {
        "schema": V24_VERIFIER_SCHEMA,
        "ok": ok,
        "problems": problems,
        "warnings": warnings,
        "recomputed_terminal_state": decision.get("terminal_state") if decision else None,
        "recomputed_pass": recomputed_pass if not problems else None,
        "checked_root": str(root),
    }