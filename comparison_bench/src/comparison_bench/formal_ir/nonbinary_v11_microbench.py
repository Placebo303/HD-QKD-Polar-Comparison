"""V11 Stage M resource microbenchmark for the full-vector coupled MC-DE kernel
(``formal-nonbinary-ldpc-v11-sc-de-gate``, design.md §5 Stage M, V11-30.1).

Engineering-only, non-gating, non-scientific scope (design.md §5 Stage M):

- small q=1024 coupled MC-DE runs with a SYNTHETIC non-gating degree
  distribution and a fixed channel p (no threshold search, no winner, no
  gate, no scientific claim of any kind);
- measures per-iteration wall-clock seconds, per-sample-per-iteration cost,
  and process-tree peak RSS under ``ProcessTreeRSSWatcher`` (frozen 3 GiB
  cap, ``nonbinary_v10_common``);
- records the runtime environment (OS, CPU, total RAM, Python, numpy, clock);
- extrapolates the FROZEN formal matrix (2 strata x 3 geometries x 5 seeds x
  2 arms, design.md §4 V11-A07) with explicitly enumerated conservative
  upper-bound assumptions and returns ``resource_ok`` /
  ``resource_blocked`` per design.md:92-95 (predicted wall > 24 h or
  measured/projected peak RSS > 3 GiB => ``resource_blocked``).

The formal matrix size is frozen by design.md §4 and is NEVER shrunk here;
the microbenchmark only projects cost.  Preparing the formal plan is
V11-30.2 (main thread), outside this module.
"""
from __future__ import annotations

import ctypes
import json
import math
import os
import platform
import sys
import time
from ctypes import wintypes
from numbers import Integral
from typing import Any, Mapping

import numpy as np

from .nonbinary_v10_common import ProcessTreeRSSWatcher, V10_RSS_CAP_BYTES
from .nonbinary_v11_mcde import V11_DRY_RUN_SEED, run_coupled_mcde

__all__ = [
    "MICRO_Q",
    "MICRO_P",
    "MICRO_L",
    "MICRO_MAX_DEGREE",
    "MICRO_SYNTH_LAMBDA",
    "MICRO_SYNTH_RATE",
    "MICRO_SEED",
    "MICRO_CELLS",
    "FORMAL_STRATA",
    "FORMAL_N_SEEDS",
    "FORMAL_ARMS",
    "FORMAL_N_SAMPLES",
    "FORMAL_MAX_ITER",
    "SEARCH_P_LO",
    "SEARCH_P_HI",
    "SEARCH_P_TOL",
    "WALL_LIMIT_SECONDS",
    "RSS_CAP_BYTES",
    "probe_count",
    "run_cell",
    "environment_info",
    "extrapolate_formal_matrix",
]

# --------------------------------------------------------------------------- #
# frozen microbenchmark parameters (engineering only; no scientific meaning)
# --------------------------------------------------------------------------- #

#: GF size for the microbenchmark (the formal q=1024).
MICRO_Q = 1024
#: Fixed, non-gating channel crossover probability (no threshold search).
MICRO_P = 0.15
#: Terminated chain length, frozen G1-G3 value (design.md §4).
MICRO_L = 32
#: Synthetic max degree: bounds both frozen winners' max degrees
#: (S1 max 28, S3 max 40) -> conservative per-iteration cost.
MICRO_MAX_DEGREE = 40
#: Synthetic non-gating edge-perspective lambda (NOT the frozen V10 winners;
#: no V11-A06 reuse claim).  Max degree 40 keeps the WHT/product slot count
#: at or above the frozen winners' worst case.
MICRO_SYNTH_LAMBDA = {2: 0.40, 3: 0.20, MICRO_MAX_DEGREE: 0.40}
#: Synthetic effective rate used only to build the harmonic check
#: distribution (midway between the S1/S3 winners' rates).
MICRO_SYNTH_RATE = 0.60
#: Non-scientific engineering seed (V11 prefix, disjoint from all formal
#: seeds; never used for any scientific run).
MICRO_SEED = 2026110000

#: Microbenchmark cells: (label, n_samples, w, W, max_iter).  "few
#: iterations" per the Stage M rule; ``streak=20 > max_iter`` guarantees the
#: full budget runs (no early-convergence interference with timing).
MICRO_CELLS = [
    {"label": "G1_500", "n_samples": 500, "w": 1, "W": 8, "max_iter": 10},
    {"label": "G2_500", "n_samples": 500, "w": 2, "W": 16, "max_iter": 10},
    {"label": "G3_500", "n_samples": 500, "w": 2, "W": 32, "max_iter": 10},
    {"label": "G1_2000", "n_samples": 2000, "w": 1, "W": 8, "max_iter": 5},
    {"label": "G2_2000", "n_samples": 2000, "w": 2, "W": 16, "max_iter": 5},
    {"label": "G3_2000", "n_samples": 2000, "w": 2, "W": 32, "max_iter": 5},
    {"label": "CTRL_500", "n_samples": 500, "w": 0, "W": 1, "max_iter": 10},
    {"label": "CTRL_2000", "n_samples": 2000, "w": 0, "W": 1, "max_iter": 5},
]

# --------------------------------------------------------------------------- #
# frozen formal-matrix projection inputs (design.md §4, §5 Stage M)
# --------------------------------------------------------------------------- #

#: Formal matrix: 2 strata x 3 geometries x 5 seeds x 2 arms (coupled +
#: paired uncoupled control) — frozen, never shrunk after the microbenchmark.
FORMAL_STRATA = ("S1", "S3")
FORMAL_N_SEEDS = 5
FORMAL_ARMS = 2
#: Formal population per DE run: conservative upper bound of the V9/V10
#: convention (V9A_BUDGETS n_samples=2000; V10 refinement n_samples=2000).
FORMAL_N_SAMPLES = 2000
#: Formal iteration budget per probe: conservative upper bound of the V9/V10
#: convention (V9A_BUDGETS max_iter=150; V10 refinement max_iter=100).
FORMAL_MAX_ITER = 150
#: Conservative wide binary-search p range and tolerance (task V11-30.1).
SEARCH_P_LO = 0.10
SEARCH_P_HI = 0.40
SEARCH_P_TOL = 0.001
#: Hard wall limit: 24 h (design.md:92).
WALL_LIMIT_SECONDS = 24 * 3600.0
#: Frozen RSS cap: 3 GiB (design.md:92; V10_RSS_CAP_BYTES).
RSS_CAP_BYTES = V10_RSS_CAP_BYTES

#: Number of probes of a binary search that halves the interval
#: ``(hi - lo)`` until it is at most ``tol``.
def probe_count(lo: float, hi: float, tol: float) -> int:
    """``ceil(log2((hi - lo) / tol))`` — the exact number of binary-search
    probes needed to shrink ``(lo, hi)`` to width ``<= tol``."""
    if not (0.0 < float(lo) < float(hi)):
        raise ValueError("probe range must satisfy 0 < lo < hi")
    if not (isinstance(tol, (int, float)) and not isinstance(tol, bool)
            and math.isfinite(float(tol)) and float(tol) > 0.0):
        raise ValueError("tol must be positive and finite")
    width = float(hi) - float(lo)
    return max(1, int(math.ceil(math.log2(width / float(tol)))))


# --------------------------------------------------------------------------- #
# environment recording (OS / CPU / RAM / clock)
# --------------------------------------------------------------------------- #

class _MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", wintypes.DWORD),
        ("dwMemoryLoad", wintypes.DWORD),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def _total_physical_memory_bytes() -> int | None:
    """Total physical RAM via ``GlobalMemoryStatusEx`` (ctypes only; returns
    None when the API is unavailable)."""
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.GlobalMemoryStatusEx.restype = wintypes.BOOL
        kernel32.GlobalMemoryStatusEx.argtypes = [ctypes.POINTER(_MEMORYSTATUSEX)]
        status = _MEMORYSTATUSEX()
        status.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
        if kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return int(status.ullTotalPhys)
    except (AttributeError, OSError):  # pragma: no cover - non-Windows
        return None
    return None


def environment_info() -> dict[str, Any]:
    """Record the runtime environment: OS, CPU, total RAM, Python, numpy and
    the monotonic clock resolution."""
    clock = time.get_clock_info("perf_counter")
    ram = _total_physical_memory_bytes()
    return {
        "os": platform.platform(),
        "platform": platform.system(),
        "cpu": platform.processor(),
        "cpu_count": os.cpu_count(),
        "total_ram_bytes": ram,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "clock": {
            "implementation": clock.implementation,
            "monotonic": clock.monotonic,
            "resolution_seconds": clock.resolution,
        },
    }


# --------------------------------------------------------------------------- #
# single-cell measurement
# --------------------------------------------------------------------------- #

def _synthetic_rho() -> dict[int, float]:
    """Harmonic check distribution at ``MICRO_SYNTH_RATE`` for the synthetic
    lambda (reused read-only via ``nonbinary_v10_common`` semantics through
    the V11 rate contract helper)."""
    from .nonbinary_v11_mcde import rate_contract
    contract = rate_contract(MICRO_L, 1, MICRO_SYNTH_RATE, MICRO_SYNTH_LAMBDA)
    return {int(k): float(v) for k, v in contract["rho"].items()}


def run_cell(cell: Mapping[str, Any], *, watcher_interval: float = 1.0) -> dict[str, Any]:
    """Run one microbenchmark cell under the process-tree RSS watcher and
    return the measurement dict.

    ``cell`` keys: ``label``, ``n_samples``, ``w``, ``W``, ``max_iter``.
    The run uses the fixed synthetic lambda/rho, ``MICRO_P``, ``MICRO_L``,
    ``MICRO_Q`` and the engineering seed; ``streak=20`` (> ``max_iter``)
    guarantees the full iteration budget executes for timing.
    """
    label = str(cell["label"])
    n_samples = int(cell["n_samples"])
    w = int(cell["w"])
    window = int(cell["W"])
    max_iter = int(cell["max_iter"])
    rho = _synthetic_rho()
    start = time.perf_counter()
    watcher = ProcessTreeRSSWatcher(interval=watcher_interval,
                                    cap_bytes=RSS_CAP_BYTES)
    with watcher:
        result = run_coupled_mcde(
            MICRO_Q, MICRO_SYNTH_LAMBDA, rho, MICRO_P,
            L=MICRO_L, w=w, W=window, n_samples=n_samples,
            max_iter=max_iter, seed=MICRO_SEED)
    wall_seconds = time.perf_counter() - start
    iterations = int(result["iterations"])
    per_iteration = wall_seconds / iterations if iterations else float("nan")
    return {
        "label": label,
        "q": MICRO_Q, "p": MICRO_P, "L": MICRO_L, "w": w, "W": window,
        "n_samples": n_samples, "max_iter": max_iter,
        "iterations_executed": iterations,
        "converged": bool(result["converged"]),
        "wall_seconds": wall_seconds,
        "per_iteration_seconds": per_iteration,
        "per_sample_per_iteration_seconds": per_iteration / n_samples,
        "peak_rss_bytes": int(watcher.peak_rss_bytes),
        "cap_exceeded": bool(watcher.cap_exceeded),
        "rss_cap_bytes": RSS_CAP_BYTES,
    }


# --------------------------------------------------------------------------- #
# formal-matrix extrapolation (conservative upper bound, assumptions explicit)
# --------------------------------------------------------------------------- #

def extrapolate_formal_matrix(measurements: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """Project the frozen formal matrix from measured per-iteration costs.

    ``measurements`` maps cell label -> ``run_cell`` output.  The projection
    uses the N=2000 cells directly (formal population), the conservative wide
    binary search over ``[SEARCH_P_LO, SEARCH_P_HI]`` at
    ``SEARCH_P_TOL``, and ``FORMAL_MAX_ITER`` iterations per probe (every
    probe runs the full budget — no early-convergence saving, conservative).

    Assumptions (all recorded in the returned dict):
      A1 formal matrix = 2 strata x 3 geometries x 5 seeds x 2 arms = 60 runs
         (design.md §4, V11-A07; never shrunk);
      A2 every DE run is a binary search over [.10, .40] at tol .001
         -> ``n_probes`` exact probe count (conservative upper bound: the
         width of the interval after n_probes probes is <= tol);
      A3 every probe runs the full ``FORMAL_MAX_ITER=150`` budget (V9/V10
         convention upper bound; no convergence savings);
      A4 per-iteration wall time at the formal population N=2000 equals the
         measured N=2000 cell value for the same (w, W) (measured directly,
         not scaled);
      A5 the uncoupled control is the single-position run (w=0, W=1) with
         the same per-run budget (design.md §4 control contract);
      A6 sequential execution, one process tree (no parallelism);
      A7 peak RSS = the largest measured single-run peak (largest geometry
         G3 at N=2000); sequential runs do not sum RSS.
    """
    if not isinstance(measurements, Mapping) or not measurements:
        raise ValueError("measurements must be a non-empty mapping")

    def cell(label: str) -> Mapping[str, Any]:
        if label not in measurements:
            raise KeyError(f"missing measurement cell '{label}'")
        return measurements[label]

    n_probes = probe_count(SEARCH_P_LO, SEARCH_P_HI, SEARCH_P_TOL)
    iterations_per_run = n_probes * FORMAL_MAX_ITER

    geometries = {
        "G1": {"w": 1, "W": 8},
        "G2": {"w": 2, "W": 16},
        "G3": {"w": 2, "W": 32},
    }
    per_geometry = {}
    for geometry, params in geometries.items():
        coupled = cell(f"{geometry}_2000")
        control = cell("CTRL_2000")
        runs_per_geometry = len(FORMAL_STRATA) * FORMAL_N_SEEDS
        coupled_wall = (runs_per_geometry * iterations_per_run
                        * float(coupled["per_iteration_seconds"]))
        control_wall = (runs_per_geometry * iterations_per_run
                        * float(control["per_iteration_seconds"]))
        per_geometry[geometry] = {
            "geometry": {"w": params["w"], "W": params["W"]},
            "n_runs": runs_per_geometry,
            "iterations_per_run": iterations_per_run,
            "coupled_wall_seconds": coupled_wall,
            "coupled_per_iteration_seconds": float(coupled["per_iteration_seconds"]),
            "control_wall_seconds": control_wall,
            "control_per_iteration_seconds": float(control["per_iteration_seconds"]),
            "total_wall_seconds": coupled_wall + control_wall,
        }

    total_wall_seconds = sum(row["total_wall_seconds"] for row in per_geometry.values())
    peak_rss_bytes = max(int(cell("G3_2000")["peak_rss_bytes"]),
                         int(cell("CTRL_2000")["peak_rss_bytes"]))

    wall_blocked = total_wall_seconds > WALL_LIMIT_SECONDS
    rss_blocked = peak_rss_bytes > RSS_CAP_BYTES
    status = "resource_blocked" if (wall_blocked or rss_blocked) else "resource_ok"

    n_runs_total = len(FORMAL_STRATA) * len(geometries) * FORMAL_N_SEEDS * FORMAL_ARMS
    return {
        "schema": "v11_microbench_extrapolation_v1",
        "engineering_only_non_scientific": True,
        "status": status,
        "verdict": {
            "resource_blocked": wall_blocked,
            "resource_ok": not (wall_blocked or rss_blocked),
            "reasons": {
                "predicted_wall_over_24h": wall_blocked,
                "peak_rss_over_3gib": rss_blocked,
            },
        },
        "total_wall_seconds": total_wall_seconds,
        "total_wall_hours": total_wall_seconds / 3600.0,
        "wall_limit_seconds": WALL_LIMIT_SECONDS,
        "peak_rss_bytes": peak_rss_bytes,
        "rss_cap_bytes": RSS_CAP_BYTES,
        "n_runs_total": n_runs_total,
        "n_probes_per_run": n_probes,
        "iterations_per_run": iterations_per_run,
        "per_geometry": per_geometry,
        "assumptions": {
            "A1_frozen_matrix": f"{len(FORMAL_STRATA)} strata x "
                                f"{len(geometries)} geometries x {FORMAL_N_SEEDS} "
                                f"seeds x {FORMAL_ARMS} arms = {n_runs_total} runs "
                                "(design.md §4, V11-A07; NEVER shrunk by the "
                                "microbenchmark)",
            "A2_binary_search": f"p in [{SEARCH_P_LO}, {SEARCH_P_HI}], "
                                f"tol <= {SEARCH_P_TOL} -> {n_probes} probes/run",
            "A3_full_budget_per_probe": f"every probe runs the full "
                                        f"{FORMAL_MAX_ITER}-iteration budget "
                                        "(V9/V10 convention upper bound; no "
                                        "early-convergence savings)",
            "A4_measured_per_iteration": "per-iteration wall time at N=2000 "
                                         "taken directly from the measured "
                                         "N=2000 cells (same w, W)",
            "A5_control": "uncoupled control = single-position run (w=0, W=1) "
                          "with the same per-run budget (design.md §4)",
            "A6_sequential": "sequential execution, one process tree "
                             "(workers=1, V9/V10 convention)",
            "A7_peak_rss": "peak RSS = largest measured single-run peak "
                           "(G3 at N=2000); sequential runs do not sum RSS",
            "conservative": "synthetic lambda max degree 40 bounds the frozen "
                            "winners' max degrees (S1 28, S3 40); no "
                            "threshold/winner/gate claims",
        },
    }


# --------------------------------------------------------------------------- #
# module self-check (smallest runnable check for the non-trivial projection)
# --------------------------------------------------------------------------- #

def _self_check() -> None:
    """Assert the probe-count arithmetic and the verdict rule on a synthetic
    measurement dict (tiny; no scientific run)."""
    assert probe_count(0.10, 0.40, 0.001) == 9, "binary search probe count"
    assert probe_count(0.10, 0.60, 0.5) == 1
    assert probe_count(0.10, 0.40, 0.05) == 3
    # synthetic measurements that must project resource_ok
    fake = {label: {
        "label": label, "n_samples": 2000 if label.endswith("2000") else 500,
        "w": int(label.split("_")[0] == "G2" or label.split("_")[0] == "G3"),
        "W": {"G1": 8, "G2": 16, "G3": 32, "CTRL": 1}[label.split("_")[0]],
        "per_iteration_seconds": 1e-4,
        "peak_rss_bytes": 1024 ** 3,
    } for label in ("G1_2000", "G2_2000", "G3_2000", "CTRL_2000")}
    result = extrapolate_formal_matrix(fake)
    assert result["status"] == "resource_ok", "tiny per-iteration cost must pass"
    assert result["n_runs_total"] == 60
    assert result["n_probes_per_run"] == 9
    assert result["iterations_per_run"] == 9 * 150
    # a large per-iteration cost must project resource_blocked
    slow = dict(fake)
    slow["G3_2000"] = dict(fake["G3_2000"], per_iteration_seconds=500.0)
    assert extrapolate_formal_matrix(slow)["status"] == "resource_blocked"
    print(json.dumps({"schema": "v11_microbench_self_check_v1",
                      "ok": True, "n_probes": 9, "n_runs_total": 60}, sort_keys=True))


if __name__ == "__main__":
    _self_check()
