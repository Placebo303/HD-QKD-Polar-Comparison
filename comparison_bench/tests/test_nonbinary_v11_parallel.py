"""Deterministic tests for V11 parallel execution wrapper
(``formal-nonbinary-ldpc-v11-sc-de-gate``, AMEND-2026-08-06-02).

Verifies:
- parallel output bit-identical to serial for each run (≥2 geometry/seed combos,
  small N/low iterations to keep wall time short)
- run_specs count (60) and stratum-major ordering
- run ID uniqueness
"""
from __future__ import annotations

import os
import tempfile
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_v11_parallel import (
    RunSpec,
    formal_matrix_run_specs,
    run_id_for,
    run_parallel,
)
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_v11_mcde import (
    run_coupled_mcde,
    v11_seed,
)
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_v11_microbench import (
    FORMAL_STRATA,
    FORMAL_N_SEEDS,
    FORMAL_ARMS,
)
import pytest


# ---------------------------------------------------------------------------
# T0: run_specs count, ordering, uniqueness
# ---------------------------------------------------------------------------

def test_formal_matrix_run_specs_count():
    specs = formal_matrix_run_specs()
    assert len(specs) == 60, f"expected 60 runs, got {len(specs)}"


def test_formal_matrix_run_specs_ordering():
    specs = formal_matrix_run_specs()
    ids = [s.run_id for s in specs]
    assert len(set(ids)) == 60, "run IDs must be unique"
    # stratum-major: S1 first, then S3
    s1_end = max(i for i, s in enumerate(specs) if s.stratum == "S1")
    s3_start = min(i for i, s in enumerate(specs) if s.stratum == "S3")
    assert s1_end < s3_start, "S1 must precede S3"
    # within S1: geometry-major (G1 < G2 < G3)
    s1_specs = [s for s in specs if s.stratum == "S1"]
    g_ends = {}
    for i, s in enumerate(s1_specs):
        g_ends[s.geometry_id] = i
    assert g_ends["G1"] < g_ends["G2"] < g_ends["G3"], "G1<G2<G3 within S1"


def test_run_id_for_deterministic():
    id1 = run_id_for("S1", "G1", 2026110001, "coupled")
    id2 = run_id_for("S1", "G1", 2026110001, "coupled")
    assert id1 == id2
    assert id1 == "S1_G1_seed2026110001_coupled"


def test_run_id_for_different_arms():
    c = run_id_for("S1", "G1", 2026110001, "coupled")
    ctrl = run_id_for("S1", "G1", 2026110001, "control")
    assert c != ctrl


# ---------------------------------------------------------------------------
# T1: parallel == serial bit-identity (small N, few iterations)
# ---------------------------------------------------------------------------

def _tiny_specs() -> list[RunSpec]:
    """Two tiny specs: G1 + G3, each with a small N and few iterations."""
    from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v11_microbench as mb
    from comparison_bench.src.comparison_bench.formal_ir.nonbinary_v11_mcde import (
        FROZEN_GEOMETRIES, V10_WINNER_S1, V10_WINNER_S1_RATE, rate_contract,
    )
    specs = []
    for geometry_id in ("G1", "G3"):
        params = FROZEN_GEOMETRIES[geometry_id]
        L, w, W = int(params["L"]), int(params["w"]), int(params["W"])
        contract = rate_contract(L, w, V10_WINNER_S1_RATE, V10_WINNER_S1)
        rho = {int(k): float(v) for k, v in contract["rho"].items()}
        seed = v11_seed(f"tiny:{geometry_id}:test")
        specs.append(RunSpec(
            run_id=f"tiny_{geometry_id}_seed{seed}",
            stratum="TINY", geometry_id=geometry_id,
            seed=seed, arm="coupled",
            w=w, W=W, n_samples=100, max_iter=2,
            lambda_edge={int(k): float(v) for k, v in V10_WINNER_S1.items()},
            rho_edge=rho, p=0.15, L=L, q=1024))
    return specs


def test_parallel_bitidentical_to_serial():
    """Each run spec must produce identical results whether executed in the
    parallel pool or serially (bit-identical scientific output)."""
    specs = _tiny_specs()
    # serial execution
    serial_results = []
    for spec in specs:
        result = run_coupled_mcde(
            spec.q, spec.lambda_edge, spec.rho_edge, spec.p,
            L=spec.L, w=spec.w, W=spec.W, n_samples=spec.n_samples,
            max_iter=spec.max_iter, seed=spec.seed,
            entropy_tol=spec.entropy_tol, streak=spec.streak)
        serial_results.append(result)
    # parallel execution (workers=1 to avoid pool overhead, still through the pool path)
    with tempfile.TemporaryDirectory() as tmp:
        specs_out = []
        for spec in specs:
            from dataclasses import replace
            specs_out.append(replace(spec, out_dir=os.path.join(tmp, spec.run_id)))
        _, parallel_results, _ = run_parallel(specs_out, workers=1, warmup=False)
    for i, (sr, pr) in enumerate(zip(serial_results, parallel_results)):
        assert sr["iterations"] == pr["iterations"], \
            f"run {i}: iterations differ {sr['iterations']} vs {pr['iterations']}"
        assert sr["converged"] == pr["converged"], \
            f"run {i}: converged flag differs"
        # compare the entropy_trace array (the scientific output)
        import numpy as np
        np.testing.assert_array_equal(
            sr["entropy_trace"], pr["entropy_trace"],
            err_msg=f"run {i}: entropy_trace not bit-identical")
        np.testing.assert_array_equal(
            sr["error_trace"], pr["error_trace"],
            err_msg=f"run {i}: error_trace not bit-identical")


def test_parallel_multiworker_bitidentical():
    """Same spec with workers=2 also produces identical results."""
    specs = _tiny_specs()
    serial_results = []
    for spec in specs:
        result = run_coupled_mcde(
            spec.q, spec.lambda_edge, spec.rho_edge, spec.p,
            L=spec.L, w=spec.w, W=spec.W, n_samples=spec.n_samples,
            max_iter=spec.max_iter, seed=spec.seed,
            entropy_tol=spec.entropy_tol, streak=spec.streak)
        serial_results.append(result)
    with tempfile.TemporaryDirectory() as tmp:
        specs_out = []
        for spec in specs:
            from dataclasses import replace
            specs_out.append(replace(spec, out_dir=os.path.join(tmp, spec.run_id)))
        _, parallel_results, _ = run_parallel(specs_out, workers=2, warmup=False)
    for i, (sr, pr) in enumerate(zip(serial_results, parallel_results)):
        assert sr["iterations"] == pr["iterations"]
        import numpy as np
        np.testing.assert_array_equal(sr["entropy_trace"], pr["entropy_trace"])
        np.testing.assert_array_equal(sr["error_trace"], pr["error_trace"])
