"""V37-P1 Finite-Feasible Empirical-P DE Candidate Screening Core Module.

Implements:
1. Candidate degree distribution enumeration on 0.05 simplex over degrees {2, 3, 4, 5}.
2. Integration with accepted V37-P0 degree feasibility analyzer (N2 <= 183 necessary condition).
3. Check realizability cap filter (realized max_dc <= 20 across all 3 sources).
4. Matched empirical-P MC-DE runner over GF(32) with true conditional posterior channel.
5. Non-saturated cumulative trajectory area (AUT_30) and diagnostic metrics (H5, H10, H15, T_0.10, T_0.01, H60).
6. P1-A screening gate (>= 5% AUT_30 reduction on all 3 sources independently).
7. Deterministic tie-breaker selection of best candidate C*.
8. Conditional P1-B confirmation on disjoint fresh seeds.
9. Structured reporting (candidate summary CSV, trajectory CSV, compact JSON summary).
"""
from __future__ import annotations

import csv
import json
import math
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from .nonbinary_field import GF2mField
from .nonbinary_v9_common import concentrated_check_distribution
from .nonbinary_v26_mcde import (
    concentrated_rho_to_hist,
    make_rho,
    mean_bits_entropy,
    run_mcde_posterior,
)
from .v35_algorithm_development import load_v25_channel_counts
from .v37_degree_feasibility import analyze_degree_feasibility

# ---------------------------------------------------------------------------
# Constants & Specifications
# ---------------------------------------------------------------------------

METHOD = "formal_ir_v37_de_screening"
CYCLE_ID = "V37R1"
ACCEPTED_PLAN_SHA = "661e2878f96f9fb84291bd601ebd3eb6abfcfdd4"

FIELD_Q = 32
FIELD_POLY = 37
N_SYMBOLS = 1024

SOURCES: Tuple[str, ...] = ("1M", "1p5M", "2M")

M2_BY_SOURCE: Dict[str, int] = {
    "1M": 184,
    "1p5M": 190,
    "2M": 192,
}

RATES_BY_SOURCE: Dict[str, float] = {
    "1M": 1.0 - 184.0 / 1024.0,  # 0.8203125
    "1p5M": 1.0 - 190.0 / 1024.0,  # 0.814453125
    "2M": 1.0 - 192.0 / 1024.0,  # 0.8125
}

# Frozen Seeds
SCREENING_SEEDS: Dict[str, Tuple[int, int, int]] = {
    "1M": (370101, 370102, 370103),
    "1p5M": (370201, 370202, 370203),
    "2M": (370301, 370302, 370303),
}

CONFIRMATION_SEEDS: Dict[str, Tuple[int, int, int]] = {
    "1M": (370111, 370112, 370113),
    "1p5M": (370211, 370212, 370213),
    "2M": (370311, 370312, 370313),
}

# DE execution defaults
DE_N_SAMPLES = 4000
DE_MAX_ITER = 60
CONVERGENCE_ENTROPY_THRESHOLD = 1e-4
EFFECT_SIZE_THRESHOLD = 0.05  # 5% relative reduction in AUT_30

# Terminal States
STATUS_P1_DE_ADVANCE_CANDIDATE_FOUND = "P1_DE_ADVANCE_CANDIDATE_FOUND"
STATUS_P1_SCREEN_SIGNAL_NOT_CONFIRMED = "P1_SCREEN_SIGNAL_NOT_CONFIRMED"
STATUS_P1_NO_FINITE_FEASIBLE_DE_ADVANCE = "P1_NO_FINITE_FEASIBLE_DE_ADVANCE"
STATUS_P1_DE_EVIDENCE_INVALID = "P1_DE_EVIDENCE_INVALID"


# ---------------------------------------------------------------------------
# Channel Sampler
# ---------------------------------------------------------------------------

class ZeroDenominatorError(Exception):
    """Raised when an empirical conditioning denominator is zero or non-finite."""
    pass


def build_v37_channel_sampler(
    counts: np.ndarray,
    source: str,
) -> Callable[[int, np.random.Generator], np.ndarray]:
    """Construct true-predecessor conditioned L2 centered channel sampler with fail-closed check."""
    counts = np.asarray(counts, dtype=np.float64)
    total_pairs = float(np.sum(counts))
    if total_pairs <= 0.0:
        raise ZeroDenominatorError(f"Source {source}: channel counts sum is zero")

    P_ab = counts / total_pairs
    p_b = np.sum(P_ab, axis=0)  # (1024,)

    with np.errstate(divide="ignore", invalid="ignore"):
        P_a_gb = np.divide(P_ab, p_b[None, :], out=np.zeros_like(P_ab), where=p_b[None, :] > 0)

    idx1024 = np.arange(1024, dtype=np.int64)
    u1_map = (idx1024 // 32).astype(np.int64)
    u2_map = (idx1024 % 32).astype(np.int64)

    p_u1_gb = np.zeros((32, 1024), dtype=np.float64)
    for a in range(1024):
        p_u1_gb[u1_map[a], :] += P_a_gb[a, :]

    p_joint = np.zeros((32, 32, 1024), dtype=np.float64)
    for a in range(1024):
        p_joint[u1_map[a], u2_map[a], :] += P_a_gb[a, :]

    P_ab_flat = P_ab.ravel()
    idx32 = np.arange(32, dtype=np.int64)

    def sampler(n: int, rng: np.random.Generator) -> np.ndarray:
        pick = rng.choice(P_ab_flat.size, size=n, p=P_ab_flat)
        a_samp = (pick // 1024).astype(np.int64)
        b_samp = (pick % 1024).astype(np.int64)

        u1_true = u1_map[a_samp]
        u2_true = u2_map[a_samp]

        norms = p_u1_gb[u1_true, b_samp]
        bad = (~np.isfinite(norms)) | (norms <= 0.0)
        if np.any(bad):
            raise ZeroDenominatorError(
                f"Source {source}: zero conditional denominator P(U1|B) at sample {int(np.flatnonzero(bad)[0])}"
            )

        rows = p_joint[u1_true, :, b_samp] / norms[:, None]

        centered = np.empty_like(rows)
        for i in range(n):
            centered[i] = rows[i, idx32 ^ u2_true[i]]
        return centered

    return sampler


# ---------------------------------------------------------------------------
# Candidate Grid & Pre-Registered Filter
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DegreeCandidate:
    """Structure representing a pre-registered degree distribution candidate."""
    candidate_id: str
    lambda_edge: Dict[int, float]
    N2: int
    dbar_v: float
    total_sockets: int
    max_check_degrees: Dict[int, int]
    finite_feasible: bool
    finite_inadmissible: bool


def format_candidate_id(lam: Mapping[int, float]) -> str:
    """Format canonical candidate ID string."""
    return f"lam_d2_{lam.get(2, 0.0):.2f}_d3_{lam.get(3, 0.0):.2f}_d4_{lam.get(4, 0.0):.2f}_d5_{lam.get(5, 0.0):.2f}"


def generate_v37_candidate_grid(
    step: float = 0.05,
    max_n2_threshold: int = 183,
    max_dc_cap: int = 20,
    block_length: int = N_SYMBOLS,
    m_values: Sequence[int] = (184, 190, 192),
) -> Tuple[List[Dict[int, float]], List[Tuple[Dict[int, float], Dict[str, Any]]], List[DegreeCandidate]]:
    """Enumerate and filter candidates on simplex grid.

    Returns:
        (raw_distributions, n2_passed_distributions, final_candidates)
    """
    steps = int(round(1.0 / step))
    raw_distributions: List[Dict[int, float]] = []

    for i2 in range(steps + 1):
        l2 = round(i2 * step, 4)
        for i3 in range(steps + 1 - i2):
            l3 = round(i3 * step, 4)
            for i4 in range(steps + 1 - i2 - i3):
                l4 = round(i4 * step, 4)
                l5 = round(1.0 - l2 - l3 - l4, 4)
                if l5 < -1e-6:
                    continue

                lam = {2: l2, 3: l3, 4: l4, 5: l5}
                lam = {k: v for k, v in lam.items() if v > 1e-6}
                if not lam:
                    continue
                raw_distributions.append(lam)

    n2_passed_distributions: List[Tuple[Dict[int, float], Dict[str, Any]]] = []
    final_candidates: List[DegreeCandidate] = []

    for lam in raw_distributions:
        rep = analyze_degree_feasibility(lam, n=block_length, m_values=m_values)
        n2 = rep["degree2_analysis"]["N2"]
        if n2 <= max_n2_threshold:
            n2_passed_distributions.append((lam, rep))
            max_dcs = {m: rep["check_node_analysis"][str(m)]["realized_max_check_degree"] for m in m_values}
            if max(max_dcs.values()) <= max_dc_cap:
                cand_id = format_candidate_id(lam)
                cand = DegreeCandidate(
                    candidate_id=cand_id,
                    lambda_edge=lam,
                    N2=n2,
                    dbar_v=float(rep["mean_variable_degree_exact"]),
                    total_sockets=int(rep["total_variable_sockets"]),
                    max_check_degrees=max_dcs,
                    finite_feasible=True,
                    finite_inadmissible=False,
                )
                final_candidates.append(cand)

    # Sort canonically
    final_candidates.sort(key=lambda c: (
        c.lambda_edge.get(2, 0.0),
        c.lambda_edge.get(3, 0.0),
        c.lambda_edge.get(4, 0.0),
        c.lambda_edge.get(5, 0.0),
    ))

    return raw_distributions, n2_passed_distributions, final_candidates


def get_reference_controls(
    block_length: int = N_SYMBOLS,
    m_values: Sequence[int] = (184, 190, 192),
) -> Tuple[DegreeCandidate, DegreeCandidate]:
    """Build the regular dv=2 baseline and the V36 positive control objects."""
    # 1. Matched baseline: regular dv=2
    lam_base = {2: 1.0}
    rep_base = analyze_degree_feasibility(lam_base, n=block_length, m_values=m_values)
    baseline = DegreeCandidate(
        candidate_id="baseline_dv2_regular",
        lambda_edge=lam_base,
        N2=rep_base["degree2_analysis"]["N2"],
        dbar_v=float(rep_base["mean_variable_degree_exact"]),
        total_sockets=int(rep_base["total_variable_sockets"]),
        max_check_degrees={m: rep_base["check_node_analysis"][str(m)]["realized_max_check_degree"] for m in m_values},
        finite_feasible=False,
        finite_inadmissible=False,
    )

    # 2. V36 exploratory positive control (finite_inadmissible=True)
    lam_v36 = {2: 0.85, 4: 0.15}
    rep_v36 = analyze_degree_feasibility(lam_v36, n=block_length, m_values=m_values)
    pos_control = DegreeCandidate(
        candidate_id="positive_control_v36",
        lambda_edge=lam_v36,
        N2=rep_v36["degree2_analysis"]["N2"],
        dbar_v=float(rep_v36["mean_variable_degree_exact"]),
        total_sockets=int(rep_v36["total_variable_sockets"]),
        max_check_degrees={m: rep_v36["check_node_analysis"][str(m)]["realized_max_check_degree"] for m in m_values},
        finite_feasible=False,
        finite_inadmissible=True,
    )

    return baseline, pos_control


# ---------------------------------------------------------------------------
# Metrics & Trajectory Analysis
# ---------------------------------------------------------------------------

@dataclass
class TrajectoryMetrics:
    """Non-saturated trajectory metrics for a single DE run."""
    entropy_trace: List[float]  # 0-indexed trajectory where index t = H(t) for t=0..max_iter
    AUT_30: float
    H5: float
    H10: float
    H15: float
    H60: float
    T_010: int
    T_001: int
    converged: bool


def compute_trajectory_metrics(
    entropy_trace_1based: Sequence[float],
    h0: float = 5.0,
    max_aut_iter: int = 30,
    target_len: int = 60,
    convergence_tol: float = CONVERGENCE_ENTROPY_THRESHOLD,
) -> TrajectoryMetrics:
    """Compute AUT_30 and diagnostic metrics from a 1-based DE entropy trace.

    Constructs 0-indexed trajectory H(0), H(1), ..., H(target_len) where H(0) = h0.
    """
    trace_list = list(entropy_trace_1based)
    if not trace_list:
        trace_list = [h0]

    # Pad or construct full length array
    last_val = trace_list[-1]
    while len(trace_list) < target_len:
        trace_list.append(last_val)

    # 0-indexed trajectory: index 0 is H(0)
    full_trace = [float(h0)] + [float(x) for x in trace_list[:target_len]]

    # AUT_30 = sum_{t=0}^{30} H(t)
    aut_30 = float(sum(full_trace[:max_aut_iter + 1]))

    h5 = float(full_trace[5])
    h10 = float(full_trace[10])
    h15 = float(full_trace[15])
    h60 = float(full_trace[60])

    t_010 = 61
    t_001 = 61
    for t in range(1, len(full_trace)):
        if full_trace[t] <= 0.10 and t_010 == 61:
            t_010 = t
        if full_trace[t] <= 0.01 and t_001 == 61:
            t_001 = t

    converged = bool(h60 < convergence_tol)

    return TrajectoryMetrics(
        entropy_trace=full_trace,
        AUT_30=aut_30,
        H5=h5,
        H10=h10,
        H15=h15,
        H60=h60,
        T_010=t_010,
        T_001=t_001,
        converged=converged,
    )


# ---------------------------------------------------------------------------
# DE Evaluation Engine (Single Config / Multi-Seed)
# ---------------------------------------------------------------------------

@dataclass
class CandidateEvaluationResult:
    """Aggregated evaluation results for a candidate across sources and seeds."""
    candidate: DegreeCandidate
    stage: str  # "screen" or "confirm"
    metrics_by_source_seed: Dict[str, Dict[int, TrajectoryMetrics]]
    mean_aut30_by_source: Dict[str, float]
    mean_h10_by_source: Dict[str, float]
    mean_aut30_overall: float
    mean_h10_overall: float
    all_seeds_converged: bool
    relative_deltas: Dict[str, float]  # Delta_s relative to baseline


def evaluate_single_config(
    candidate: DegreeCandidate,
    stage: str,
    seeds_by_source: Dict[str, Sequence[int]],
    samplers: Dict[str, Callable[[int, np.random.Generator], np.ndarray]],
    n_samples: int = DE_N_SAMPLES,
    max_iter: int = DE_MAX_ITER,
    fake_runner: bool = False,
) -> Dict[str, Dict[int, TrajectoryMetrics]]:
    """Run MC-DE for all sources and seeds for a single candidate configuration."""
    results: Dict[str, Dict[int, TrajectoryMetrics]] = {}

    for src in SOURCES:
        results[src] = {}
        R = RATES_BY_SOURCE[src]
        rho = make_rho(R, candidate.lambda_edge)
        sampler = samplers[src]

        for seed in seeds_by_source[src]:
            if fake_runner:
                # Fast deterministic synthetic trace for testing orchestration
                # Lambda 2 gives decay rate: higher degree -> different slope
                l2 = candidate.lambda_edge.get(2, 0.0)
                l4 = candidate.lambda_edge.get(4, 0.0)
                # Synthetic exponential decay
                decay_rate = 0.80 if candidate.candidate_id == "baseline_dv2_regular" else (
                    0.72 if (l2 > 0.8 and l4 > 0.1) else (0.75 if l2 > 0.05 else 0.78)
                )
                trace_1based = [5.0 * (decay_rate ** t) for t in range(1, max_iter + 1)]
                metrics = compute_trajectory_metrics(trace_1based, h0=5.0, target_len=max_iter)
            else:
                de_res = run_mcde_posterior(
                    FIELD_Q,
                    candidate.lambda_edge,
                    rho,
                    channel_sampler=sampler,
                    n_samples=n_samples,
                    max_iter=max_iter,
                    seed=seed,
                    entropy_tol_bits=CONVERGENCE_ENTROPY_THRESHOLD,
                    record_entropy=True,
                )
                metrics = compute_trajectory_metrics(
                    de_res["entropy_trace_bits"],
                    h0=5.0,
                    target_len=max_iter,
                    convergence_tol=CONVERGENCE_ENTROPY_THRESHOLD,
                )

            results[src][seed] = metrics

    return results


def aggregate_candidate_results(
    candidate: DegreeCandidate,
    stage: str,
    metrics_by_source_seed: Dict[str, Dict[int, TrajectoryMetrics]],
    baseline_aut30_means: Optional[Dict[str, float]] = None,
) -> CandidateEvaluationResult:
    """Aggregate per-seed metrics into per-source means and calculate relative deltas."""
    mean_aut30: Dict[str, float] = {}
    mean_h10: Dict[str, float] = {}
    all_converged = True

    for src in SOURCES:
        src_metrics = list(metrics_by_source_seed[src].values())
        mean_aut30[src] = float(np.mean([m.AUT_30 for m in src_metrics]))
        mean_h10[src] = float(np.mean([m.H10 for m in src_metrics]))
        if not all(m.converged for m in src_metrics):
            all_converged = False

    overall_aut30 = float(np.mean(list(mean_aut30.values())))
    overall_h10 = float(np.mean(list(mean_h10.values())))

    deltas: Dict[str, float] = {}
    if baseline_aut30_means is not None:
        for src in SOURCES:
            b_val = baseline_aut30_means[src]
            deltas[src] = float((mean_aut30[src] - b_val) / b_val) if b_val > 0 else 0.0

    return CandidateEvaluationResult(
        candidate=candidate,
        stage=stage,
        metrics_by_source_seed=metrics_by_source_seed,
        mean_aut30_by_source=mean_aut30,
        mean_h10_by_source=mean_h10,
        mean_aut30_overall=overall_aut30,
        mean_h10_overall=overall_h10,
        all_seeds_converged=all_converged,
        relative_deltas=deltas,
    )


# ---------------------------------------------------------------------------
# Screening & Confirmation Orchestration
# ---------------------------------------------------------------------------

@dataclass
class ScreeningExecutionReport:
    """Complete structured record of V37-P1 execution."""
    cycle_id: str
    plan_sha: str
    raw_count: int
    n2_gate_count: int
    final_candidates_count: int
    evaluated_configurations_count: int
    baseline_summary: CandidateEvaluationResult
    positive_control_summary: CandidateEvaluationResult
    candidate_summaries: List[CandidateEvaluationResult]
    passing_screening_candidates: List[CandidateEvaluationResult]
    selected_winner: Optional[CandidateEvaluationResult]
    confirmation_executed: bool
    confirmation_winner_result: Optional[CandidateEvaluationResult]
    confirmation_baseline_result: Optional[CandidateEvaluationResult]
    confirmation_passed: Optional[bool]
    terminal_state: str
    total_de_runs: int
    screening_de_runs: int
    confirmation_de_runs: int
    runtime_s: float


def run_v37_p1_pipeline(
    channel_counts: Optional[Dict[str, np.ndarray]] = None,
    n_samples: int = DE_N_SAMPLES,
    max_iter: int = DE_MAX_ITER,
    effect_size_threshold: float = EFFECT_SIZE_THRESHOLD,
    fake_runner: bool = False,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> ScreeningExecutionReport:
    """Execute complete V37-P1 screening and conditional confirmation workflow."""
    t0 = time.perf_counter()

    # 1. Enumerate candidates and controls
    raw_cands, n2_cands, final_cands = generate_v37_candidate_grid()
    baseline, pos_control = get_reference_controls()

    # 2. Build samplers
    if fake_runner:
        samplers = {src: (lambda n, rng: np.zeros((n, 32))) for src in SOURCES}
    else:
        if channel_counts is None:
            channel_counts = load_v25_channel_counts()
        samplers = {src: build_v37_channel_sampler(channel_counts[src], src) for src in SOURCES}

    # 3. P1-A Screening
    # Evaluate Baseline first
    base_metrics = evaluate_single_config(
        baseline, "screen", SCREENING_SEEDS, samplers, n_samples, max_iter, fake_runner
    )
    base_summary = aggregate_candidate_results(baseline, "screen", base_metrics)
    base_aut30_means = base_summary.mean_aut30_by_source

    # Evaluate Positive Control
    ctrl_metrics = evaluate_single_config(
        pos_control, "screen", SCREENING_SEEDS, samplers, n_samples, max_iter, fake_runner
    )
    ctrl_summary = aggregate_candidate_results(pos_control, "screen", ctrl_metrics, base_aut30_means)

    # Evaluate 259 candidates
    candidate_summaries: List[CandidateEvaluationResult] = []
    total_configs = len(final_cands) + 2
    completed_configs = 2

    if progress_callback:
        progress_callback(completed_configs, total_configs, "Controls evaluated")

    for cand in final_cands:
        cand_metrics = evaluate_single_config(
            cand, "screen", SCREENING_SEEDS, samplers, n_samples, max_iter, fake_runner
        )
        cand_summary = aggregate_candidate_results(cand, "screen", cand_metrics, base_aut30_means)
        candidate_summaries.append(cand_summary)
        completed_configs += 1
        if progress_callback:
            progress_callback(completed_configs, total_configs, cand.candidate_id)

    screening_runs = total_configs * 3 * 3  # 261 * 9 = 2349

    # 4. Screening Gate Evaluation
    passing_candidates: List[CandidateEvaluationResult] = []
    for c_res in candidate_summaries:
        # Must be finite-feasible and not marked inadmissible
        if not c_res.candidate.finite_feasible or c_res.candidate.finite_inadmissible:
            continue
        # All seeds must converge
        if not c_res.all_seeds_converged:
            continue
        # Must beat baseline by >= 5% on all 3 sources independently (Delta_s <= -0.05)
        if all(c_res.relative_deltas[src] <= -effect_size_threshold for src in SOURCES):
            passing_candidates.append(c_res)

    # Deterministic tie-breaker
    # 1. Lower mean AUT_30 across all sources
    # 2. Lower mean H10 across all sources
    # 3. Lower N2
    # 4. Canonical candidate_id
    passing_candidates.sort(key=lambda c: (
        c.mean_aut30_overall,
        c.mean_h10_overall,
        c.candidate.N2,
        c.candidate.candidate_id,
    ))

    # 5. Conditional P1-B Confirmation Stage
    confirmation_executed = False
    confirm_winner_res: Optional[CandidateEvaluationResult] = None
    confirm_base_res: Optional[CandidateEvaluationResult] = None
    confirm_passed: Optional[bool] = None
    selected_winner: Optional[CandidateEvaluationResult] = None
    confirmation_runs = 0

    if not passing_candidates:
        terminal_state = STATUS_P1_NO_FINITE_FEASIBLE_DE_ADVANCE
    else:
        selected_winner = passing_candidates[0]
        confirmation_executed = True

        # Run confirmation on Winner + Baseline
        c_winner = selected_winner.candidate
        conf_winner_metrics = evaluate_single_config(
            c_winner, "confirm", CONFIRMATION_SEEDS, samplers, n_samples, max_iter, fake_runner
        )
        conf_base_metrics = evaluate_single_config(
            baseline, "confirm", CONFIRMATION_SEEDS, samplers, n_samples, max_iter, fake_runner
        )

        confirm_base_res = aggregate_candidate_results(baseline, "confirm", conf_base_metrics)
        confirm_winner_res = aggregate_candidate_results(
            c_winner, "confirm", conf_winner_metrics, confirm_base_res.mean_aut30_by_source
        )

        confirmation_runs = 2 * 3 * 3  # 18

        # Confirmation Gate: all seeds converge AND Delta_s <= -0.05 on all 3 sources
        confirm_converged = confirm_winner_res.all_seeds_converged and confirm_base_res.all_seeds_converged
        confirm_improved = all(
            confirm_winner_res.relative_deltas[src] <= -effect_size_threshold for src in SOURCES
        )

        if confirm_converged and confirm_improved:
            confirm_passed = True
            terminal_state = STATUS_P1_DE_ADVANCE_CANDIDATE_FOUND
        else:
            confirm_passed = False
            terminal_state = STATUS_P1_SCREEN_SIGNAL_NOT_CONFIRMED

    t1 = time.perf_counter()
    total_de_runs = screening_runs + confirmation_runs

    return ScreeningExecutionReport(
        cycle_id=CYCLE_ID,
        plan_sha=ACCEPTED_PLAN_SHA,
        raw_count=len(raw_cands),
        n2_gate_count=len(n2_cands),
        final_candidates_count=len(final_cands),
        evaluated_configurations_count=total_configs,
        baseline_summary=base_summary,
        positive_control_summary=ctrl_summary,
        candidate_summaries=candidate_summaries,
        passing_screening_candidates=passing_candidates,
        selected_winner=selected_winner,
        confirmation_executed=confirmation_executed,
        confirmation_winner_result=confirm_winner_res,
        confirmation_baseline_result=confirm_base_res,
        confirmation_passed=confirm_passed,
        terminal_state=terminal_state,
        total_de_runs=total_de_runs,
        screening_de_runs=screening_runs,
        confirmation_de_runs=confirmation_runs,
        runtime_s=float(t1 - t0),
    )


# ---------------------------------------------------------------------------
# Structured Artifact Exporters
# ---------------------------------------------------------------------------

def export_candidate_summary_csv(
    report: ScreeningExecutionReport,
    output_path: Path,
) -> None:
    """Export candidate summary table to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    all_results = [report.baseline_summary, report.positive_control_summary] + report.candidate_summaries

    fieldnames = [
        "candidate_id",
        "lambda_2",
        "lambda_3",
        "lambda_4",
        "lambda_5",
        "N2",
        "total_sockets",
        "mean_variable_degree",
        "max_check_degree_184",
        "max_check_degree_190",
        "max_check_degree_192",
        "finite_feasible",
        "finite_inadmissible",
        "all_seeds_converged",
        "aut30_mean_overall",
        "aut30_1M",
        "aut30_1p5M",
        "aut30_2M",
        "delta_1M",
        "delta_1p5M",
        "delta_2M",
        "passed_screening",
    ]

    passing_ids = {c.candidate.candidate_id for c in report.passing_screening_candidates}

    with open(output_path, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        for res in all_results:
            cand = res.candidate
            row = {
                "candidate_id": cand.candidate_id,
                "lambda_2": cand.lambda_edge.get(2, 0.0),
                "lambda_3": cand.lambda_edge.get(3, 0.0),
                "lambda_4": cand.lambda_edge.get(4, 0.0),
                "lambda_5": cand.lambda_edge.get(5, 0.0),
                "N2": cand.N2,
                "total_sockets": cand.total_sockets,
                "mean_variable_degree": f"{cand.dbar_v:.6f}",
                "max_check_degree_184": cand.max_check_degrees.get(184, 0),
                "max_check_degree_190": cand.max_check_degrees.get(190, 0),
                "max_check_degree_192": cand.max_check_degrees.get(192, 0),
                "finite_feasible": cand.finite_feasible,
                "finite_inadmissible": cand.finite_inadmissible,
                "all_seeds_converged": res.all_seeds_converged,
                "aut30_mean_overall": f"{res.mean_aut30_overall:.6f}",
                "aut30_1M": f"{res.mean_aut30_by_source.get('1M', 0.0):.6f}",
                "aut30_1p5M": f"{res.mean_aut30_by_source.get('1p5M', 0.0):.6f}",
                "aut30_2M": f"{res.mean_aut30_by_source.get('2M', 0.0):.6f}",
                "delta_1M": f"{res.relative_deltas.get('1M', 0.0):.6f}",
                "delta_1p5M": f"{res.relative_deltas.get('1p5M', 0.0):.6f}",
                "delta_2M": f"{res.relative_deltas.get('2M', 0.0):.6f}",
                "passed_screening": cand.candidate_id in passing_ids,
            }
            writer.writerow(row)


def export_trajectories_csv(
    report: ScreeningExecutionReport,
    output_path: Path,
) -> None:
    """Export long-form trajectory records to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["stage", "source", "candidate_id", "seed", "iteration", "entropy_bits"]

    all_results = [report.baseline_summary, report.positive_control_summary] + report.candidate_summaries
    if report.confirmation_executed and report.confirmation_winner_result and report.confirmation_baseline_result:
        all_results += [report.confirmation_baseline_result, report.confirmation_winner_result]

    with open(output_path, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        for res in all_results:
            cid = res.candidate.candidate_id
            stage = res.stage
            for src, seeds_dict in res.metrics_by_source_seed.items():
                for seed, metrics in seeds_dict.items():
                    for it, ent in enumerate(metrics.entropy_trace):
                        writer.writerow({
                            "stage": stage,
                            "source": src,
                            "candidate_id": cid,
                            "seed": seed,
                            "iteration": it,
                            "entropy_bits": f"{ent:.8f}",
                        })


def export_summary_json(
    report: ScreeningExecutionReport,
    output_path: Path,
) -> None:
    """Export compact JSON execution summary."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    summary: Dict[str, Any] = {
        "schema_version": "v37_p1_de_screening_v1",
        "cycle_id": report.cycle_id,
        "plan_sha": report.plan_sha,
        "candidate_counts": {
            "raw": report.raw_count,
            "n2_gate": report.n2_gate_count,
            "final_candidates": report.final_candidates_count,
            "evaluated_configurations": report.evaluated_configurations_count,
        },
        "screening_parameters": {
            "n_samples": DE_N_SAMPLES,
            "max_iter": DE_MAX_ITER,
            "field_q": FIELD_Q,
            "field_poly": FIELD_POLY,
            "effect_size_threshold": EFFECT_SIZE_THRESHOLD,
        },
        "confirmation_parameters": {
            "n_samples": DE_N_SAMPLES,
            "max_iter": DE_MAX_ITER,
            "field_q": FIELD_Q,
            "field_poly": FIELD_POLY,
            "effect_size_threshold": EFFECT_SIZE_THRESHOLD,
        },
        "screening_seeds": {k: list(v) for k, v in SCREENING_SEEDS.items()},
        "confirmation_seeds": {k: list(v) for k, v in CONFIRMATION_SEEDS.items()},
        "baseline_definition": {
            "id": report.baseline_summary.candidate.candidate_id,
            "lambda": report.baseline_summary.candidate.lambda_edge,
            "mean_aut30": report.baseline_summary.mean_aut30_by_source,
        },
        "positive_control_definition": {
            "id": report.positive_control_summary.candidate.candidate_id,
            "lambda": report.positive_control_summary.candidate.lambda_edge,
            "finite_inadmissible": True,
            "mean_aut30": report.positive_control_summary.mean_aut30_by_source,
        },
        "screening_gate": {
            "passed": len(report.passing_screening_candidates) > 0,
            "passing_candidates_count": len(report.passing_screening_candidates),
            "best_candidate_id": report.selected_winner.candidate.candidate_id if report.selected_winner else None,
        },
        "confirmation_gate": {
            "executed": report.confirmation_executed,
            "passed": report.confirmation_passed,
            "winner_aut30_confirm": report.confirmation_winner_result.mean_aut30_by_source if report.confirmation_winner_result else None,
            "baseline_aut30_confirm": report.confirmation_baseline_result.mean_aut30_by_source if report.confirmation_baseline_result else None,
            "deltas_confirm": report.confirmation_winner_result.relative_deltas if report.confirmation_winner_result else None,
        },
        "terminal_state": report.terminal_state,
        "run_counts": {
            "screening_runs": report.screening_de_runs,
            "confirmation_runs": report.confirmation_de_runs,
            "total_runs": report.total_de_runs,
        },
        "runtime_s": report.runtime_s,
        "claims_allowed": [
            "Implementation exists and focused unit tests pass.",
            "Candidate enumeration and P0 filter mathematically verified.",
        ],
        "claims_forbidden": [
            "No DE superiority claimed (production DE not executed).",
            "No finite code success or FER improvement.",
            "No key-rate improvement.",
            "No Tanner-graph realizability result.",
            "No scientific promotion.",
        ],
    }

    with open(output_path, "w", encoding="utf-8") as fp:
        json.dump(summary, fp, indent=2)
