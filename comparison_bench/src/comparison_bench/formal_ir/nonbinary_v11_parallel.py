"""V11 deterministic parallel execution wrapper for the formal MC-DE matrix
(``formal-nonbinary-ldpc-v11-sc-de-gate``, AMEND-2026-08-06-02, V11-30.1'').

Engineering-only operational layer around the frozen :mod:`nonbinary_v11_mcde`
kernel (which is NOT modified).  It adds exactly the capabilities the
amendment authorizes:

- a ``multiprocessing`` worker pool whose process count is parameterized
  (``workers``; frozen suggestion 4-6 on the 20-logical-core machine, final
  value frozen by the formal plan Stage P — this module never freezes it,
  it only supports any value);
- a frozen seed-to-run mapping builder (:func:`formal_matrix_run_specs`:
  2 strata x 3 geometries x 5 seeds x 2 arms = 60 runs, stratum-major /
  geometry-major / seed-major / arm-major deterministic order; the formal
  plan Stage P freezes the final mapping — this builder is the default);
- run IDs ``(stratum, geometry_id, seed, arm) -> unique run ID`` with one
  independent output directory per run;
- every run calls the existing single-threaded ``run_coupled_mcde`` (or the
  control arm = single-position run) unchanged, so the scientific result of a
  run is bit-identical to the serial path (tests assert this);
- RSS: single-run process-tree peak via ``ProcessTreeRSSWatcher`` inside the
  worker (unchanged 3 GiB cap, judged per single run); the summed RSS across
  parallel processes is recorded as evidence but is NOT a gate item
  (rss_semantics, AMEND-2026-08-06-02).

Microbenchmark #3 (exactly-once parallel re-measurement, V11-30.2'') uses
:func:`microbench3_run_specs` (the identical #1/#2 synthetic configuration,
seed 2026110000) and :func:`parallel_matrix_projection` (serial total 66.72 h
/ measured parallel speedup; ``resource_blocked`` if predicted wall > 24 h or
single-run peak RSS > 3 GiB).

No GF(1024) scientific matrix is executed here.  numba import discipline
(AMEND-2026-08-06-01) is unchanged: numba stays confined to
``nonbinary_v11_mcde.py``; this wrapper imports its kernels read-only.
"""
from __future__ import annotations

import json
import math
import multiprocessing
import os
import time
from dataclasses import dataclass
from numbers import Integral
from typing import Any, Mapping

from .nonbinary_v10_common import ProcessTreeRSSWatcher, V10_RSS_CAP_BYTES
from .nonbinary_v11_microbench import RSS_CAP_BYTES  # alias kept consistent with mb module
from .nonbinary_v11_mcde import (
    FROZEN_GEOMETRIES,
    V10_WINNER_S1,
    V10_WINNER_S1_RATE,
    V10_WINNER_S3,
    V10_WINNER_S3_RATE,
    run_coupled_mcde,
    v11_seed,
)
from . import nonbinary_v11_microbench as mb

__all__ = [
    "RunSpec",
    "DEFAULT_WORKERS",
    "run_id_for",
    "formal_matrix_run_specs",
    "microbench3_run_specs",
    "microbench3_serial_baseline",
    "run_parallel",
    "parallel_matrix_projection",
]

#: Frozen suggestion for the 20-logical-core machine (AMEND-2026-08-06-02:
#: "20 逻辑核机器取 4-6"); the low end keeps the single-run RSS headroom
#: largest and the projection most conservative.  The formal plan (Stage P)
#: freezes the final value — this is only the default used by microbenchmark
#: #3 and by the CLI.
DEFAULT_WORKERS = 4

#: Formal matrix shape (design.md §4, V11-A07; frozen, never shrunk).
FORMAL_STRATA = mb.FORMAL_STRATA
FORMAL_N_SEEDS = mb.FORMAL_N_SEEDS
FORMAL_ARMS = mb.FORMAL_ARMS


# --------------------------------------------------------------------------- #
# run specification (one deterministic single-threaded run)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class RunSpec:
    """One deterministic V11 MC-DE run (coupled or uncoupled control arm).

    Everything the worker needs is carried here (picklable plain data);
    ``run_id`` is the unique ``(stratum, geometry_id, seed, arm)`` identifier
    and ``out_dir`` the run's independent output directory.  The worker
    executes the untouched single-threaded :func:`run_coupled_mcde`, so the
    scientific result is bit-identical to a serial run with the same
    parameters.
    """

    run_id: str
    stratum: str
    geometry_id: str
    seed: int
    arm: str                       # "coupled" | "control"
    w: int
    W: int
    n_samples: int
    max_iter: int
    lambda_edge: Mapping[int, float]
    rho_edge: Mapping[int, float]
    p: float
    L: int
    q: int = 1024
    out_dir: str | None = None
    entropy_tol: float = 0.01
    streak: int = 20
    watcher_interval: float = 1.0


def run_id_for(stratum: str, geometry_id: str, seed: int, arm: str) -> str:
    """Canonical run ID ``(stratum, geometry_id, seed, arm) -> unique string``.

    Deterministic and filename-safe: ``S1_G1_seed2026110001_coupled``.
    """
    if not isinstance(stratum, str) or not stratum:
        raise ValueError("stratum must be a non-empty string")
    if not isinstance(geometry_id, str) or not geometry_id:
        raise ValueError("geometry_id must be a non-empty string")
    if isinstance(seed, bool) or not isinstance(seed, Integral):
        raise ValueError("seed must be an integer")
    if arm not in ("coupled", "control"):
        raise ValueError("arm must be 'coupled' or 'control'")
    return f"{stratum}_{geometry_id}_seed{int(seed)}_{arm}"


# --------------------------------------------------------------------------- #
# frozen seed-to-run mapping (default; Stage P freezes the final one)
# --------------------------------------------------------------------------- #


def _harmonic_rho(L: int, w: int, rate: float,
                  lambda_edge: Mapping[Any, Any]) -> dict[int, float]:
    """Harmonic check distribution at the geometry's base rate (read-only
    reuse of the frozen rate contract; same semantics the CLI dry-run uses)."""
    from .nonbinary_v11_mcde import rate_contract
    contract = rate_contract(L, w, rate, lambda_edge)
    return {int(k): float(v) for k, v in contract["rho"].items()}


def formal_matrix_run_specs(*, out_root: str | None = None) -> list[RunSpec]:
    """Build the FROZEN formal matrix of 60 run specs (default seed mapping).

    Order (frozen for replay): stratum-major (S1, S3), geometry-major (G1,
    G2, G3 in frozen order), seed-major (1..5), arm-major (coupled, control).
    Each run's seed is derived with the frozen V11 rule
    ``v11_seed(f"{stratum}:{geometry_id}:{arm}:{n}")`` (202611xx prefix,
    provably disjoint from V8/V9/V10 families).  The control arm is the
    single-position run (w=0, W=1, design.md §4) with the harmonic rho at
    ``R_eff``; the coupled arm uses the frozen V10 S1/S3 winner (V11-A06) and
    the harmonic rho at ``R_base``.

    Engineering/planning machinery only: building specs executes no run.  The
    formal plan (Stage P) freezes the final seed-to-run mapping — this is the
    deterministic default it reviews.
    """
    specs: list[RunSpec] = []
    for stratum, winner, rate in (("S1", V10_WINNER_S1, V10_WINNER_S1_RATE),
                                  ("S3", V10_WINNER_S3, V10_WINNER_S3_RATE)):
        for geometry_id, params in FROZEN_GEOMETRIES.items():
            L = int(params["L"])
            w = int(params["w"])
            W = int(params["W"])
            rho_coupled = _harmonic_rho(L, w, rate, winner)
            rho_control = _harmonic_rho(L, 0, rate, winner)
            for n in range(1, FORMAL_N_SEEDS + 1):
                for arm, arm_w, arm_W, arm_rho in (
                        ("coupled", w, W, rho_coupled),
                        ("control", 0, 1, rho_control)):
                    seed = v11_seed(f"{stratum}:{geometry_id}:{arm}:{n}")
                    run_id = run_id_for(stratum, geometry_id, seed, arm)
                    out_dir = None
                    if out_root is not None:
                        out_dir = os.path.join(out_root, run_id)
                    specs.append(RunSpec(
                        run_id=run_id, stratum=stratum, geometry_id=geometry_id,
                        seed=seed, arm=arm, w=arm_w, W=arm_W,
                        n_samples=mb.FORMAL_N_SAMPLES, max_iter=mb.FORMAL_MAX_ITER,
                        lambda_edge={int(k): float(v) for k, v in winner.items()},
                        rho_edge=arm_rho, p=mb.MICRO_P, L=L, q=mb.MICRO_Q,
                        out_dir=out_dir))
    return specs


# --------------------------------------------------------------------------- #
# microbenchmark #3 run specs (identical #1/#2 configuration)
# --------------------------------------------------------------------------- #


def _microbench_rho() -> dict[int, float]:
    """Harmonic synthetic rho at ``MICRO_SYNTH_RATE`` — byte-identical to the
    #1/#2 ``_synthetic_rho()`` construction (same ``rate_contract(L, 1, ...)``
    call)."""
    from .nonbinary_v11_mcde import rate_contract
    contract = rate_contract(mb.MICRO_L, 1, mb.MICRO_SYNTH_RATE, mb.MICRO_SYNTH_LAMBDA)
    return {int(k): float(v) for k, v in contract["rho"].items()}


def microbench3_run_specs(out_root: str) -> list[RunSpec]:
    """The 8 frozen microbenchmark cells (identical to #1/#2: q=1024, L=32,
    p=0.15, synthetic lambda max-degree 40, seed 2026110000, N=500/2000,
    G1/G2/G3 w/W + control) as parallel run specs with per-cell output dirs."""
    rho = _microbench_rho()
    specs: list[RunSpec] = []
    for cell in mb.MICRO_CELLS:
        label = str(cell["label"])
        geometry_id = label.split("_")[0]
        specs.append(RunSpec(
            run_id=label, stratum="SYNTH", geometry_id=geometry_id,
            seed=mb.MICRO_SEED, arm="coupled",
            w=int(cell["w"]), W=int(cell["W"]), n_samples=int(cell["n_samples"]),
            max_iter=int(cell["max_iter"]),
            lambda_edge={int(k): float(v) for k, v in mb.MICRO_SYNTH_LAMBDA.items()},
            rho_edge=rho, p=mb.MICRO_P, L=mb.MICRO_L, q=mb.MICRO_Q,
            out_dir=os.path.join(out_root, label)))
    return specs


def microbench3_serial_baseline(baseline_path: str) -> dict[str, Any]:
    """Load the frozen #2 serial measurements (the #3 comparison baseline).

    Returns ``{"measurements": {label: wall_seconds}, "serial_cell_sum_seconds",
    "serial_total_hours"}`` read from ``microbenchmark2.json``.  #1/#2
    evidence is immutable — this only reads it.
    """
    if not isinstance(baseline_path, str) or not os.path.isfile(baseline_path):
        raise ValueError(f"serial baseline not found: {baseline_path!r}")
    with open(baseline_path, encoding="utf-8") as handle:
        payload = json.load(handle)
    measurements = payload.get("measurements")
    extrapolation = payload.get("extrapolation")
    if not isinstance(measurements, Mapping) or not isinstance(extrapolation, Mapping):
        raise ValueError("serial baseline JSON is missing measurements/extrapolation")
    per_cell = {}
    for label, measurement in measurements.items():
        if not isinstance(measurement, Mapping) or "wall_seconds" not in measurement:
            raise ValueError(f"serial baseline cell {label!r} has no wall_seconds")
        per_cell[str(label)] = float(measurement["wall_seconds"])
    serial_total_hours = float(extrapolation["total_wall_hours"])
    return {
        "measurements": per_cell,
        "serial_cell_sum_seconds": float(sum(per_cell.values())),
        "serial_total_hours": serial_total_hours,
    }


# --------------------------------------------------------------------------- #
# worker side (module-level so multiprocessing spawn can pickle them)
# --------------------------------------------------------------------------- #


def _warmup_task(_: int) -> str:
    """One tiny coupled run per worker so the njit kernels are compiled before
    the timed batch (the formal matrix pays this cost once per worker too;
    excluding it from the batch wall keeps the speedup a steady-state
    measurement)."""
    from .nonbinary_v11_mcde import V11_DRY_RUN_SEED, fwht_batched
    rho = _harmonic_rho(4, 1, V10_WINNER_S1_RATE, V10_WINNER_S1)
    run_coupled_mcde(8, V10_WINNER_S1, rho, 0.15, L=4, w=1, W=4,
                     n_samples=100, max_iter=1, seed=V11_DRY_RUN_SEED)
    fwht_batched([[1.0] * 8])
    return "warm"

def _execute_task(spec: RunSpec) -> dict[str, Any]:
    """Execute one run spec single-threaded under the process-tree RSS watcher,
    write the per-run artifacts to its independent output directory and return
    the measurement + full result (bit-identical to a serial run)."""
    out_dir = spec.out_dir
    if out_dir is not None:
        os.makedirs(out_dir, exist_ok=True)
    start = time.perf_counter()
    watcher = ProcessTreeRSSWatcher(interval=spec.watcher_interval,
                                    cap_bytes=RSS_CAP_BYTES)
    with watcher:
        result = run_coupled_mcde(
            spec.q, spec.lambda_edge, spec.rho_edge, spec.p,
            L=spec.L, w=spec.w, W=spec.W, n_samples=spec.n_samples,
            max_iter=spec.max_iter, seed=spec.seed,
            entropy_tol=spec.entropy_tol, streak=spec.streak)
    wall_seconds = time.perf_counter() - start
    iterations = int(result["iterations"])
    per_iteration = wall_seconds / iterations if iterations else float("nan")
    measurement = {
        "schema": "v11_parallel_run_measurement_v1",
        "run_id": spec.run_id,
        "stratum": spec.stratum,
        "geometry_id": spec.geometry_id,
        "seed": int(spec.seed),
        "arm": spec.arm,
        "q": int(spec.q), "p": float(spec.p), "L": int(spec.L),
        "w": int(spec.w), "W": int(spec.W),
        "n_samples": int(spec.n_samples), "max_iter": int(spec.max_iter),
        "iterations_executed": iterations,
        "converged": bool(result["converged"]),
        "wall_seconds": wall_seconds,
        "per_iteration_seconds": per_iteration,
        "per_sample_per_iteration_seconds": per_iteration / int(spec.n_samples),
        "peak_rss_bytes": int(watcher.peak_rss_bytes),
        "cap_exceeded": bool(watcher.cap_exceeded),
        "rss_cap_bytes": RSS_CAP_BYTES,
        "output_dir": out_dir,
    }
    if out_dir is not None:
        _write_json(os.path.join(out_dir, "run_result.json"), result)
        _write_json(os.path.join(out_dir, "run_measurement.json"), measurement)
    return {"measurement": measurement, "result": result}


def _write_json(path: str, payload: dict) -> None:
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


# --------------------------------------------------------------------------- #
# pool driver
# --------------------------------------------------------------------------- #


def _validate_workers(workers: Any) -> int:
    if isinstance(workers, bool) or not isinstance(workers, Integral) or int(workers) < 1:
        raise ValueError("workers must be an integer >= 1")
    return int(workers)


def run_parallel(run_specs: list[RunSpec], workers: int, *,
                 warmup: bool = True) -> tuple[list[dict], list[dict], float]:
    """Run ``run_specs`` through a ``multiprocessing`` worker pool.

    Returns ``(measurements, results, batch_wall_seconds)``: the per-run
    measurement dicts and the full ``run_coupled_mcde`` result dicts,
    aligned with ``run_specs`` order (``pool.imap`` preserves the frozen
    input order — the seed-to-run replay order), plus the wall clock of the
    timed batch.  With ``warmup=True`` one tiny run is executed per worker
    before the timed batch so numba compilation is paid once per worker and
    excluded from ``batch_wall_seconds`` (steady-state measurement; the
    formal matrix also pays compilation once per worker).

    Determinism: each task is the untouched single-threaded
    :func:`run_coupled_mcde` with its own frozen seed — parallelism changes
    no single-run result (tests assert bit-identity to serial).
    """
    if not isinstance(run_specs, (list, tuple)) or not run_specs:
        raise ValueError("run_specs must be a non-empty list of RunSpec")
    for spec in run_specs:
        if not isinstance(spec, RunSpec):
            raise ValueError("run_specs must contain RunSpec instances")
    workers = _validate_workers(workers)
    seen: set[str] = set()
    for spec in run_specs:
        if spec.run_id in seen:
            raise ValueError(f"duplicate run_id in parallel batch: {spec.run_id}")
        seen.add(spec.run_id)
    with multiprocessing.Pool(processes=workers) as pool:
        if warmup:
            list(pool.map(_warmup_task, range(workers)))
        start = time.perf_counter()
        outcomes = list(pool.imap(_execute_task, run_specs, chunksize=1))
        batch_wall_seconds = time.perf_counter() - start
    measurements = [outcome["measurement"] for outcome in outcomes]
    results = [outcome["result"] for outcome in outcomes]
    return measurements, results, batch_wall_seconds


# --------------------------------------------------------------------------- #
# formal-matrix parallel projection (microbenchmark #3 decision)
# --------------------------------------------------------------------------- #


def parallel_matrix_projection(*, serial_total_hours: float,
                               parallel_speedup: float, workers: int,
                               peak_rss_bytes: int,
                               serial_cell_sum_seconds: float,
                               parallel_batch_wall_seconds: float) -> dict[str, Any]:
    """Project the frozen formal matrix under the measured parallel speedup.

    Formula (AMEND-2026-08-06-02, identical #1/#2 extrapolation basis: 60
    runs, 9 probes, max_iter 150, N=2000): predicted parallel wall =
    ``serial_total_hours`` (66.72 h, frozen #2 total) / measured
    ``parallel_speedup``; ``per_worker_efficiency = speedup / workers``.
    Verdict per design.md:92-95 and the amendment: ``resource_blocked`` if
    predicted wall > 24 h OR single-run peak RSS > 3 GiB, else
    ``resource_ok``.  Summed parallel RSS is recorded but is NOT a gate.
    """
    if isinstance(workers, bool) or not isinstance(workers, Integral) or int(workers) < 1:
        raise ValueError("workers must be an integer >= 1")
    workers = int(workers)
    if not (isinstance(serial_total_hours, (int, float)) and not isinstance(serial_total_hours, bool)
            and float(serial_total_hours) > 0.0):
        raise ValueError("serial_total_hours must be positive")
    if not (isinstance(parallel_speedup, (int, float)) and not isinstance(parallel_speedup, bool)
            and math.isfinite(float(parallel_speedup)) and float(parallel_speedup) > 0.0):
        raise ValueError("parallel_speedup must be positive and finite")
    if isinstance(peak_rss_bytes, bool) or not isinstance(peak_rss_bytes, Integral) \
            or int(peak_rss_bytes) < 0:
        raise ValueError("peak_rss_bytes must be a non-negative integer")
    serial_total_hours = float(serial_total_hours)
    parallel_speedup = float(parallel_speedup)
    peak_rss_bytes = int(peak_rss_bytes)
    predicted_wall_hours = serial_total_hours / parallel_speedup
    predicted_wall_seconds = predicted_wall_hours * 3600.0
    per_worker_efficiency = parallel_speedup / workers
    wall_blocked = predicted_wall_seconds > mb.WALL_LIMIT_SECONDS
    rss_blocked = peak_rss_bytes > RSS_CAP_BYTES
    status = "resource_blocked" if (wall_blocked or rss_blocked) else "resource_ok"
    return {
        "schema": "v11_parallel_microbench_extrapolation_v1",
        "engineering_only_non_scientific": True,
        "status": status,
        "verdict": {
            "resource_blocked": wall_blocked or rss_blocked,
            "resource_ok": not (wall_blocked or rss_blocked),
            "reasons": {
                "predicted_parallel_wall_over_24h": wall_blocked,
                "single_run_peak_rss_over_3gib": rss_blocked,
            },
        },
        "predicted_parallel_wall_hours": predicted_wall_hours,
        "predicted_parallel_wall_seconds": predicted_wall_seconds,
        "wall_limit_seconds": mb.WALL_LIMIT_SECONDS,
        "serial_total_hours": serial_total_hours,
        "parallel_speedup": parallel_speedup,
        "per_worker_efficiency": per_worker_efficiency,
        "workers": workers,
        "serial_cell_sum_seconds": float(serial_cell_sum_seconds),
        "parallel_batch_wall_seconds": float(parallel_batch_wall_seconds),
        "peak_rss_bytes": peak_rss_bytes,
        "rss_cap_bytes": RSS_CAP_BYTES,
        "n_runs_total": len(FORMAL_STRATA) * len(FROZEN_GEOMETRIES)
                        * FORMAL_N_SEEDS * FORMAL_ARMS,
        "n_probes_per_run": mb.probe_count(mb.SEARCH_P_LO, mb.SEARCH_P_HI, mb.SEARCH_P_TOL),
        "iterations_per_run": mb.probe_count(mb.SEARCH_P_LO, mb.SEARCH_P_HI, mb.SEARCH_P_TOL)
                              * mb.FORMAL_MAX_ITER,
        "assumptions": {
            "A1_serial_basis": "serial total 66.72 h and per-cell walls from "
                               "frozen #2 evidence (microbenchmark2.json); "
                               "extrapolation basis identical to #1/#2 "
                               "(60 runs, 9 probes, max_iter 150, N=2000)",
            "A2_measured_speedup": "parallel speedup measured on the identical "
                                   "8-cell #1/#2 synthetic batch (q=1024, L=32, "
                                   "p=0.15, lambda max-degree 40, seed 2026110000) "
                                   "run concurrently with the frozen worker count; "
                                   "batch wall excludes the one-time per-worker "
                                   "numba warmup",
            "A3_wall_scaling": "predicted parallel wall = serial total / measured "
                               "parallel speedup; each run stays single-threaded "
                               "and deterministic (bit-identical to serial)",
            "A4_per_run_rss": "single-run peak RSS measured per run in the worker "
                              "process tree; 3 GiB cap unchanged, judged per "
                              "single run",
            "A5_summed_rss": "summed RSS across parallel processes recorded as "
                             "evidence only, NOT a gate item (host 33.69 GiB "
                             "measured to accommodate)",
            "A6_frozen_matrix": "matrix 2x3x5x2 never shrunk; no tuning, no "
                                "rerun; #1/#2 evidence unchanged",
        },
    }


# --------------------------------------------------------------------------- #
# module self-check (tiny; no scientific run, no pool)
# --------------------------------------------------------------------------- #


def _self_check() -> None:
    """Assert the run-ID scheme, the frozen matrix shape and the projection
    verdict rule on synthetic numbers (no pool, no run)."""
    specs = formal_matrix_run_specs()
    assert len(specs) == 60, "frozen 2x3x5x2 matrix"
    ids = [spec.run_id for spec in specs]
    assert len(set(ids)) == 60, "run IDs must be unique"
    assert all(run_id_for(s.stratum, s.geometry_id, s.seed, s.arm) == s.run_id
               for s in specs), "run ID scheme mismatch"
    assert specs[0].run_id.startswith("S1_G1_")
    assert specs[-1].run_id.startswith("S3_G3_")
    assert all((spec.arm == "control") == (spec.w == 0 and spec.W == 1)
               for spec in specs), "control arm must be the single-position run"
    # verdict rule: 66.72 h / speedup vs 24 h, and per-run RSS vs 3 GiB
    ok = parallel_matrix_projection(
        serial_total_hours=66.72, parallel_speedup=4.0, workers=4,
        peak_rss_bytes=int(2.7 * 1024 ** 3),
        serial_cell_sum_seconds=126.0, parallel_batch_wall_seconds=31.5)
    assert ok["status"] == "resource_ok", "speedup 4 -> 16.68 h and RSS 2.7 GiB must pass"
    assert ok["predicted_parallel_wall_hours"] == 66.72 / 4.0
    slow = parallel_matrix_projection(
        serial_total_hours=66.72, parallel_speedup=2.0, workers=4,
        peak_rss_bytes=int(2.7 * 1024 ** 3),
        serial_cell_sum_seconds=126.0, parallel_batch_wall_seconds=63.0)
    assert slow["status"] == "resource_blocked", "speedup 2 -> 33.36 h must block"
    rss = parallel_matrix_projection(
        serial_total_hours=66.72, parallel_speedup=4.0, workers=4,
        peak_rss_bytes=int(3.2 * 1024 ** 3),
        serial_cell_sum_seconds=126.0, parallel_batch_wall_seconds=31.5)
    assert rss["status"] == "resource_blocked", "RSS 3.2 GiB must block"
    print(json.dumps({"schema": "v11_parallel_self_check_v1",
                      "ok": True, "n_specs": 60, "default_workers": DEFAULT_WORKERS},
                     sort_keys=True))


if __name__ == "__main__":
    _self_check()
