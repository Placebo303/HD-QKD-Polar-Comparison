"""V11 Stage X scientific executor for the formal matrix
(``formal-nonbinary-ldpc-v11-sc-de-gate``, design.md §5 Stage X, §6 gate,
V11-40.2).

AUTHORIZATION BOUNDARY (frozen plan V11-A11/A15/A16, tasks.md V11-40.2):
  This module provides the execution capability only.  It does NOT launch the
  GF(1024) scientific matrix on its own.  The CLI refuses ``--execute`` unless
  the caller passes the explicit ``--v11-40-2-authorized`` flag, and the plan
  records that V11-40.2 requires a main-thread decision after the formal-plan
  review (V11-40.1) has passed.  Nothing in this module runs a scientific
  matrix at import time, and the module self-check / dry-run execute no kernel
  runs at all.  The task that added this module performed no scientific
  execution.

What this module provides (all deterministic, evidence-complete):

- :func:`threshold_search_run` — per-run binary search over the frozen
  per-stratum probe range (plan ``threshold_search.p_ranges``: S1
  ``[0.18, 0.26]``, S3 ``[0.28, 0.36]``; plan formula
  ``probe_count = ceil(log2((hi - lo) / tol))`` with ``SEARCH_P_TOL``), every
  probe calling the frozen :func:`run_coupled_mcde` with the run's inherited
  budget (N/max_iter/entropy_tol/streak, plan ``per_probe_budget``).  The
  probe trace records ``(p, converged, entropy, iterations)``.  The per-seed
  threshold estimate is the largest probed ``p`` at which the run converges
  (monotone-convergence assumption, recorded in every probe table so a
  violation is visible in evidence).  Status: ``valid`` | ``invalid`` |
  ``not_converged`` (plan ``stopping_rules``).
- :func:`run_search_parallel` / :func:`execute_formal_matrix` — the 60-task
  matrix (2 strata x 3 geometries x 5 seeds x 2 arms, stratum-major /
  geometry-major / seed-major / arm-major frozen order, ``formal_matrix_run_specs``)
  through a ``multiprocessing`` pool mirroring ``run_parallel``'s semantics
  (order-preserving ``imap``, per-worker numba warmup, per-task process-tree
  RSS watcher), with a wall-clock hard-limit check at task granularity.
- :func:`aggregate_conservative` — per (stratum, geometry, arm) the
  conservative threshold is the min of the 5 per-seed estimates, requiring all
  5 seeds valid and converged (plan ``threshold_search.conservative_threshold_definition``;
  design.md §6).
- :func:`paired_gain` — coupled minus control conservative threshold per
  (stratum, geometry) (design.md §6, >= 0.002).
- :func:`gate_decision` — the complete design.md §6 gate (absolute gates .22 /
  .32, paired gain .002, all-seeds valid+converged, rate/resource/replay/
  structured/semantic checks) -> exactly one of ``ready_for_finite_length``,
  ``failed_reference``, ``failed_coupling``, ``resource_blocked``, plus the
  passing-geometry selection rule (smallest W, then smallest w).
- :func:`seed_integers` — the 60 derived seed integers (non-scientific; the
  frozen ``v11_seed`` rule).

Evidence: per run ``{out_root}/{run_id}/threshold_search.json`` +
``run_measurement.json``; the aggregate summary
``{out_root}/formal_matrix_results.json`` (60-run table, conservative
aggregates, paired gains, gate decision, resource/rate checks).

Execution bookkeeping (V11-40.2 execution support; operational only, no
scientific semantics): ``{out_root}/progress.json`` (60-entry run table:
``pending | running | done | invalid | not_converged`` + timestamps +
results file + probes executed), ``{out_root}/heartbeat.json`` (refreshed
every ``HEARTBEAT_INTERVAL_SECONDS`` by a daemon thread while the batch
runs; hang diagnostic), ``--resume`` skip semantics (a run is re-executed
only when its per-run evidence under the execution root is missing, torn,
or unparseable — any run with complete, parseable, run_id-matching evidence
is loaded instead, never re-run, regardless of its scientific status, per
the frozen plan's ``failed_evidence_immutable``), and the ``--status``
summary (:func:`summarize_status`).

Plan-consistency notes (reported, not silently changed):
- The plan's ``probe_count_per_run: 9`` was computed on the conservative wide
  microbench range ``[0.10, 0.40]``; the frozen per-stratum ranges (width
  0.08) give ``probe_count = 7`` per run by the plan's own formula.  This
  module uses the frozen ranges + the plan's formula (7 probes per run).
- The plan/docstrings call the derived seeds "202611xx-prefixed"; the frozen
  ``v11_seed`` is ``int(sha256("V11:" + tag)[0:8], 16)``, whose values are
  arbitrary sha256-derived 32-bit integers (e.g. 1222026398).  Disjointness
  from V8/V9/V10 therefore holds statistically (independent derivations), not
  by numeric prefix.  This module uses the frozen function as-is.
"""
from __future__ import annotations

import json
import math
import multiprocessing
import os
import tempfile
import threading
import time
import uuid
from datetime import datetime
from numbers import Integral
from typing import Any, Callable, Mapping, Sequence

from .nonbinary_v10_common import ProcessTreeRSSWatcher
from .nonbinary_v11_mcde import (
    FROZEN_GEOMETRIES,
    V10_WINNER_S1,
    V10_WINNER_S1_RATE,
    V10_WINNER_S3,
    V10_WINNER_S3_RATE,
    rate_contract,
    run_coupled_mcde,
    v11_seed,
)
from .nonbinary_v11_microbench import (
    FORMAL_ARMS,
    FORMAL_MAX_ITER,
    FORMAL_N_SAMPLES,
    FORMAL_N_SEEDS,
    FORMAL_STRATA,
    RSS_CAP_BYTES,
    SEARCH_P_TOL,
    WALL_LIMIT_SECONDS,
    probe_count,
)
from .nonbinary_v11_parallel import (
    DEFAULT_WORKERS,
    RunSpec,
    _warmup_task,
    formal_matrix_run_specs,
    run_id_for,
)

__all__ = [
    "PROBE_RANGES",
    "GATE_S1",
    "GATE_S3",
    "PAIRED_GAIN_MIN",
    "threshold_search_run",
    "run_search_parallel",
    "execute_formal_matrix",
    "aggregate_conservative",
    "paired_gain",
    "gate_decision",
    "seed_integers",
    "write_progress",
    "load_progress",
    "write_heartbeat",
    "completed_run_outcome",
    "scan_completed_runs",
    "summarize_status",
]

# --------------------------------------------------------------------------- #
# frozen executor constants (formal_plan.json, design.md §6)
# --------------------------------------------------------------------------- #

#: Frozen per-stratum binary-search probe ranges (plan threshold_search.p_ranges).
PROBE_RANGES: dict[str, tuple[float, float]] = {
    "S1": (0.18, 0.26),
    "S3": (0.28, 0.36),
}
#: Frozen conservative absolute gate per stratum (design.md §6).
GATE_S1 = 0.22
GATE_S3 = 0.32
#: Frozen minimum paired conservative gain (design.md §6).
PAIRED_GAIN_MIN = 0.002
#: Arm order in the frozen matrix (seed-major -> arm-major; formal_matrix_run_specs).
ARM_ORDER = ("coupled", "control")


# --------------------------------------------------------------------------- #
# execution bookkeeping: progress.json / heartbeat.json / resume / status
# (V11-40.2 execution support; operational only — no scientific semantics)
# --------------------------------------------------------------------------- #

#: The five progress states of a run: pending (not started), running (in
#: flight), done (valid), invalid, not_converged (the last three are the
#: scientific terminal statuses, see :func:`_progress_state_for`).
PROGRESS_STATES = ("pending", "running", "done", "invalid", "not_converged")
#: Terminal (non-re-executable) progress states.
TERMINAL_STATES = ("done", "invalid", "not_converged")
#: Heartbeat refresh period while a batch is running (seconds).
HEARTBEAT_INTERVAL_SECONDS = 60.0


def _progress_path(exec_root: str) -> str:
    return os.path.join(exec_root, "progress.json")


def _heartbeat_path(exec_root: str) -> str:
    return os.path.join(exec_root, "heartbeat.json")


def _utc_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _parse_utc_seconds(stamp: str) -> float | None:
    """Epoch seconds of a ``YYYY-MM-DDTHH:MM:SSZ`` stamp (None if unparsable)."""
    try:
        return datetime.fromisoformat(str(stamp).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _init_progress(exec_root: str) -> dict[str, dict[str, Any]]:
    """A fresh 60-entry progress table (every run ``pending``)."""
    return {
        spec.run_id: {"state": "pending", "started_at": None,
                      "finished_at": None, "results_file": None,
                      "probes_executed": 0}
        for spec in formal_matrix_run_specs(out_root=exec_root)
    }


def write_progress(exec_root: str, progress: Mapping[str, Any]) -> None:
    """Persist the progress table atomically (temp file + ``os.replace``).

    Single-writer parent process, so no locking is needed; readers
    (``--status``) only ever see a complete table.
    """
    payload = {
        "schema": "v11_execute_progress_v1",
        "execution_root": os.path.abspath(exec_root),
        "updated_at": _utc_timestamp(),
        "runs": {run_id: dict(entry) for run_id, entry in progress.items()},
    }
    os.makedirs(exec_root, exist_ok=True)
    tmp_path = _progress_path(exec_root) + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
    os.replace(tmp_path, _progress_path(exec_root))


def load_progress(exec_root: str) -> dict[str, dict[str, Any]]:
    """Load the progress table; a missing file falls back to the fresh
    all-pending 60-entry table (idempotent initialization).  A corrupt table
    raises (fail-closed; the temp+replace writer makes this near-impossible)."""
    path = _progress_path(exec_root)
    if not os.path.isfile(path):
        return _init_progress(exec_root)
    try:
        with open(path, encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, ValueError) as exc:
        raise ValueError(
            f"progress.json under {exec_root} is unreadable: {exc}") from exc
    runs = payload.get("runs")
    if not isinstance(runs, Mapping):
        raise ValueError(f"progress.json under {exec_root} has no 'runs' table")
    return {str(run_id): dict(entry) for run_id, entry in runs.items()}


def _progress_state_for(status: str) -> str:
    """Map a search status to its terminal progress state: ``valid`` ->
    ``done``; ``invalid`` / ``not_converged`` pass through unchanged."""
    if status == "valid":
        return "done"
    return status


def write_heartbeat(exec_root: str, *, runs_done: int, runs_running: int) -> None:
    """Refresh the heartbeat file (hang diagnostic; refreshed every
    ``HEARTBEAT_INTERVAL_SECONDS`` by the driver's daemon thread while the
    batch runs, plus one initial and one final write from the main thread)."""
    payload = {
        "schema": "v11_execute_heartbeat_v1",
        "last_active_utc": _utc_timestamp(),
        "runs_done": int(runs_done),
        "runs_running": int(runs_running),
    }
    os.makedirs(exec_root, exist_ok=True)
    with open(_heartbeat_path(exec_root), "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


def completed_run_outcome(exec_root: str, run_id: str) -> dict | None:
    """Reconstruct the ``{"search", "measurement"}`` outcome of a run whose
    per-run evidence under ``exec_root`` is complete and parseable.

    ``None`` when either ``threshold_search.json`` or ``run_measurement.json``
    is missing, unparseable (torn write), or does not match ``run_id`` — such
    a run is re-executed on ``--resume`` (it has no valid evidence, so that is
    a recovery, not a rerun; completed evidence is never re-run).
    """
    search_path = os.path.join(exec_root, run_id, "threshold_search.json")
    measurement_path = os.path.join(exec_root, run_id, "run_measurement.json")
    if not (os.path.isfile(search_path) and os.path.isfile(measurement_path)):
        return None
    try:
        with open(search_path, encoding="utf-8") as handle:
            search = json.load(handle)
        with open(measurement_path, encoding="utf-8") as handle:
            measurement = json.load(handle)
    except (OSError, ValueError, TypeError):
        return None
    if not isinstance(search, Mapping) or not isinstance(measurement, Mapping):
        return None
    if search.get("run_id") != run_id or measurement.get("run_id") != run_id:
        return None
    return {"search": search, "measurement": measurement}


def scan_completed_runs(exec_root: str,
                        run_ids: Sequence[str]) -> tuple[list[str], dict[str, dict]]:
    """The ``--resume`` skip set: ``(completed_run_ids, outcomes)`` for the
    runs whose evidence is complete and parseable under ``exec_root``.

    Skipping is evidence-based (any run with complete, parseable,
    run_id-matching artifacts is loaded instead of re-executed — done,
    invalid, and not_converged alike), which keeps the frozen plan's
    ``failed_evidence_immutable`` intact: interrupted runs (no valid
    artifacts) are the only ones re-executed.
    """
    completed: list[str] = []
    outcomes: dict[str, dict] = {}
    for run_id in run_ids:
        outcome = completed_run_outcome(exec_root, run_id)
        if outcome is not None:
            completed.append(run_id)
            outcomes[run_id] = outcome
    return completed, outcomes


def summarize_status(exec_root: str) -> dict[str, Any]:
    """Read ``progress.json`` (+ optional ``heartbeat.json``) under
    ``exec_root`` and produce the ``--status`` report: total vs terminal
    counts, per (stratum, geometry) distribution, currently-running runs,
    heartbeat recency, and stale-running detection (running entries whose
    heartbeat is older than two intervals — a hang diagnostic)."""
    if not isinstance(exec_root, str) or not os.path.isdir(exec_root):
        raise ValueError(f"execution root not found: {exec_root}")
    progress_path = _progress_path(exec_root)
    if not os.path.isfile(progress_path):
        raise ValueError(f"no progress.json under {exec_root} "
                         "(no execution started in that root)")
    progress = load_progress(exec_root)
    by_state: dict[str, int] = {}
    for entry in progress.values():
        state = entry.get("state", "pending")
        by_state[state] = by_state.get(state, 0) + 1
    specs = formal_matrix_run_specs()
    per_cell: dict[str, dict[str, int]] = {}
    for spec in specs:
        key = f"{spec.stratum}/{spec.geometry_id}"
        cell = per_cell.setdefault(key, {"total": 0, "done": 0})
        cell["total"] += 1
        if progress.get(spec.run_id, {}).get("state") in TERMINAL_STATES:
            cell["done"] += 1
    heartbeat: dict[str, Any] | None = None
    heartbeat_path = _heartbeat_path(exec_root)
    if os.path.isfile(heartbeat_path):
        try:
            with open(heartbeat_path, encoding="utf-8") as handle:
                heartbeat = json.load(handle)
        except (OSError, ValueError):
            heartbeat = None
    heartbeat_age: float | None = None
    if heartbeat:
        stamp = heartbeat.get("last_active_utc")
        parsed = _parse_utc_seconds(stamp) if stamp else None
        if parsed is not None:
            heartbeat_age = time.time() - parsed
    running = [run_id for run_id, entry in progress.items()
               if entry.get("state") == "running"]
    stale_running = list(running)
    if heartbeat_age is not None and heartbeat_age <= 2 * HEARTBEAT_INTERVAL_SECONDS:
        stale_running = []
    return {
        "schema": "v11_execute_status_v1",
        "execution_root": os.path.abspath(exec_root),
        "progress_file": progress_path,
        "heartbeat_file": heartbeat_path if heartbeat else None,
        "n_total": len(progress),
        "n_terminal": sum(by_state.get(s, 0) for s in TERMINAL_STATES),
        "by_state": by_state,
        "per_cell": {key: per_cell[key] for key in sorted(per_cell)},
        "currently_running": running,
        "stale_running": stale_running,
        "heartbeat": heartbeat,
        "heartbeat_age_seconds": heartbeat_age,
    }


def _write_fake_run_evidence(root: str, spec: RunSpec, *,
                             status: str = "valid",
                             threshold: float | None = 0.20) -> None:
    """Write parseable per-run evidence documents for a spec under ``root``
    (structure-only; NO scientific run).  Used by the self-check and the
    resume-simulation tests."""
    out_dir = os.path.join(root, spec.run_id)
    os.makedirs(out_dir, exist_ok=True)
    search = {
        "schema": "v11_execute_threshold_search_v1",
        "run_id": spec.run_id,
        "stratum": spec.stratum,
        "geometry_id": spec.geometry_id,
        "seed": int(spec.seed),
        "arm": spec.arm,
        "probe_range": list(PROBE_RANGES[spec.stratum]),
        "search_tolerance": SEARCH_P_TOL,
        "probe_count_total": 7,
        "probes": [],
        "threshold_estimate": threshold,
        "threshold_below_range": status == "not_converged",
        "status": status,
        "invalid_error": None,
    }
    measurement = {
        "schema": "v11_execute_run_measurement_v1",
        "run_id": spec.run_id,
        "stratum": spec.stratum,
        "geometry_id": spec.geometry_id,
        "seed": int(spec.seed),
        "arm": spec.arm,
        "q": int(spec.q),
        "L": int(spec.L),
        "w": int(spec.w),
        "W": int(spec.W),
        "n_samples": int(spec.n_samples),
        "max_iter": int(spec.max_iter),
        "entropy_tol": float(spec.entropy_tol),
        "streak": int(spec.streak),
        "probe_count": 7,
        "probes_executed": 7,
        "status": status,
        "threshold_estimate": threshold,
        "wall_seconds": 0.0,
        "peak_rss_bytes": 0,
        "cap_exceeded": False,
        "rss_cap_bytes": RSS_CAP_BYTES,
        "output_dir": out_dir,
    }
    _write_json(os.path.join(out_dir, "threshold_search.json"), search)
    _write_json(os.path.join(out_dir, "run_measurement.json"), measurement)


# --------------------------------------------------------------------------- #
# seed integers (non-scientific derivation; frozen v11_seed rule)
# --------------------------------------------------------------------------- #


def _seed_n_for(stratum: str, geometry_id: str, arm: str, seed: int) -> int:
    """Map a derived seed back to its frozen tag index ``n`` in 1..5."""
    for n in range(1, FORMAL_N_SEEDS + 1):
        if v11_seed(f"{stratum}:{geometry_id}:{arm}:{n}") == int(seed):
            return n
    raise ValueError(f"seed {int(seed)} is not in the frozen tag space for "
                     f"{stratum}:{geometry_id}:{arm}")


def seed_integers() -> list[dict[str, Any]]:
    """The 60 frozen seed integers, in the frozen matrix order (stratum-major
    -> geometry-major -> seed-major -> arm-major).

    Deterministic and non-scientific: derives ``v11_seed(tag)`` only.  Returns
    one entry per run: ``run_id``, ``stratum``, ``geometry_id``, ``seed_n``,
    ``arm``, ``tag``, ``seed``.
    """
    entries: list[dict[str, Any]] = []
    for stratum in FORMAL_STRATA:
        for geometry_id in FROZEN_GEOMETRIES:
            for n in range(1, FORMAL_N_SEEDS + 1):
                for arm in ARM_ORDER:
                    tag = f"{stratum}:{geometry_id}:{arm}:{n}"
                    seed = v11_seed(tag)
                    entries.append({
                        "run_id": run_id_for(stratum, geometry_id, seed, arm),
                        "stratum": stratum,
                        "geometry_id": geometry_id,
                        "seed_n": n,
                        "arm": arm,
                        "tag": tag,
                        "seed": int(seed),
                    })
    return entries


# --------------------------------------------------------------------------- #
# threshold-search runner (default = frozen run_coupled_mcde)
# --------------------------------------------------------------------------- #


def _default_probe_runner(spec: RunSpec, p: float) -> dict[str, Any]:
    """One probe = the frozen single-threaded :func:`run_coupled_mcde` with the
    run's inherited budget (plan per_probe_budget) at the probed ``p``.

    Module-level so the pool can pickle it by reference.  The returned dict
    is the compact probe result consumed by the search (converged flag,
    iteration count, final mean entropy, final error probability).
    """
    result = run_coupled_mcde(
        spec.q, spec.lambda_edge, spec.rho_edge, p,
        L=spec.L, w=spec.w, W=spec.W, n_samples=spec.n_samples,
        max_iter=spec.max_iter, seed=spec.seed,
        entropy_tol=spec.entropy_tol, streak=spec.streak)
    return {
        "converged": bool(result["converged"]),
        "iterations": int(result["iterations"]),
        "entropy": float(result["entropy_trace"][-1]),
        "error_prob": float(result["error_trace"][-1]),
    }


def threshold_search_run(spec: RunSpec, *, runner: Callable | None = None,
                         probe_range: Sequence[float] | None = None,
                         search_tol: float = SEARCH_P_TOL) -> dict[str, Any]:
    """Locate one run's conservative convergence threshold by binary search
    over the frozen probe range (plan ``threshold_search``).

    Every probe calls ``runner(spec, p)`` (default: the frozen
    :func:`run_coupled_mcde` with the spec's inherited N/max_iter/entropy_tol/
    streak; plan ``per_probe_budget``).  The binary search shrinks the interval
    to width <= ``search_tol``; the per-seed threshold estimate is the largest
    probed ``p`` at which the run converged (monotone-convergence assumption —
    the full probe table is retained so a non-monotone pattern stays visible in
    evidence).

    Status semantics (plan ``stopping_rules``):
    - ``valid``: every probe executed without a fail-closed error and at least
      one probe converged (``threshold_estimate`` set);
    - ``not_converged``: no probe converged within the search range
      (``threshold_below_range`` True; plan threshold_estimation_failure);
    - ``invalid``: a fail-closed ``ValueError`` escaped the runner (plan
      invalid_runs); the probes executed before the failure are retained, the
      error is recorded, and the run does NOT count as converged or
      non-converged.

    A ``ValueError`` is the fail-closed validation channel enumerated in the
    plan (``_lambda_validate``, ``_validate_pop``, ``_validate_normalized``,
    ``fwht_batched``, ``parse_degree_hist``, ``run_coupled_mcde`` parameter
    validation).  Any other exception propagates (unexpected failure).
    """
    if not isinstance(spec, RunSpec):
        raise ValueError("spec must be a RunSpec")
    if probe_range is None:
        if spec.stratum not in PROBE_RANGES:
            raise ValueError(f"no frozen probe range for stratum {spec.stratum!r}")
        lo, hi = PROBE_RANGES[spec.stratum]
    else:
        lo, hi = float(probe_range[0]), float(probe_range[1])
    if not (0.0 < lo < hi):
        raise ValueError("probe range must satisfy 0 < lo < hi")
    search_tol = float(search_tol)
    if not math.isfinite(search_tol) or search_tol <= 0.0:
        raise ValueError("search_tol must be positive and finite")
    n_probes = probe_count(lo, hi, search_tol)
    probe_runner = runner if runner is not None else _default_probe_runner

    cur_lo, cur_hi = lo, hi
    probes: list[dict[str, Any]] = []
    best_converged_p: float | None = None
    status = "valid"
    invalid_error: dict[str, str] | None = None

    for index in range(1, n_probes + 1):
        p = (cur_lo + cur_hi) / 2.0
        probe: dict[str, Any] = {
            "index": index,
            "p": p,
            "valid": True,
            "converged": None,
            "iterations": None,
            "entropy": None,
            "error_prob": None,
            "error": None,
        }
        try:
            result = probe_runner(spec, p)
        except ValueError as exc:  # fail-closed validation -> invalid run
            probe["valid"] = False
            probe["error"] = {"type": type(exc).__name__, "message": str(exc)}
            probes.append(probe)
            status = "invalid"
            invalid_error = probe["error"]
            break
        probe["converged"] = bool(result["converged"])
        probe["iterations"] = int(result["iterations"])
        probe["entropy"] = float(result["entropy"])
        probe["error_prob"] = float(result.get("error_prob"))
        probes.append(probe)
        if probe["converged"]:
            best_converged_p = p
            cur_lo = p
        else:
            cur_hi = p

    if status == "valid" and best_converged_p is None:
        status = "not_converged"
    return {
        "schema": "v11_execute_threshold_search_v1",
        "run_id": spec.run_id,
        "stratum": spec.stratum,
        "geometry_id": spec.geometry_id,
        "seed": int(spec.seed),
        "arm": spec.arm,
        "probe_range": [lo, hi],
        "search_tolerance": search_tol,
        "probe_count_total": n_probes,
        "probes": probes,
        "threshold_estimate": best_converged_p,
        "threshold_below_range": status == "not_converged",
        "status": status,
        "invalid_error": invalid_error,
    }


# --------------------------------------------------------------------------- #
# conservative aggregation and paired gain (design.md §6 semantics)
# --------------------------------------------------------------------------- #


def aggregate_conservative(searches: Sequence[Mapping[str, Any]], *,
                           stratum: str, geometry_id: str,
                           arm: str) -> dict[str, Any]:
    """Conservative threshold of a (stratum, geometry, arm) cell.

    Plan ``threshold_search.conservative_threshold_definition``: the 5 per-seed
    estimates combine to the MINIMUM (design.md §6; a gap or a non-converged
    seed marks the cell below range).  ``seeds_valid`` / ``seeds_converged``
    require all 5 seeds respectively.  ``conservative_threshold`` is None and
    ``below_range`` True unless every seed is valid and converged.
    """
    if len(searches) != FORMAL_N_SEEDS:
        raise ValueError(f"aggregate_conservative requires {FORMAL_N_SEEDS} "
                         f"per-seed searches, got {len(searches)}")
    thresholds: list[float | None] = []
    seeds_valid = True
    seeds_converged = True
    for search in searches:
        if search["stratum"] != stratum or search["geometry_id"] != geometry_id \
                or search["arm"] != arm:
            raise ValueError("search identity does not match the aggregation cell")
        if search["status"] != "valid":
            seeds_valid = False
        estimate = search["threshold_estimate"]
        if estimate is None:
            seeds_converged = False
            thresholds.append(None)
        else:
            thresholds.append(float(estimate))
    if seeds_valid and seeds_converged:
        conservative = float(min(thresholds))  # all non-None here
        below_range = False
    else:
        conservative = None
        below_range = not seeds_converged
    return {
        "schema": "v11_execute_conservative_aggregate_v1",
        "stratum": stratum,
        "geometry_id": geometry_id,
        "arm": arm,
        "n_seeds": FORMAL_N_SEEDS,
        "seed_thresholds": thresholds,
        "seeds_valid": seeds_valid,
        "seeds_converged": seeds_converged,
        "conservative_threshold": conservative,
        "below_range": below_range,
    }


def paired_gain(coupled: float | None, control: float | None) -> float | None:
    """Paired conservative gain ``coupled - control`` (design.md §6); None
    when either arm's conservative threshold is unavailable."""
    if coupled is None or control is None:
        return None
    return float(coupled) - float(control)


# --------------------------------------------------------------------------- #
# complete design.md §6 gate decision (pure function)
# --------------------------------------------------------------------------- #


def gate_decision(*, conservative: Mapping[str, Mapping[str, Mapping[str, Any]]],
                  gains: Mapping[str, Mapping[str, float | None]],
                  seeds_ok: Mapping[str, Mapping[str, bool]],
                  rate_ok: bool, resource_ok: bool, replay_ok: bool,
                  structured_ok: bool, semantic_ok: bool,
                  gate_s1: float = GATE_S1, gate_s3: float = GATE_S3,
                  gain_min: float = PAIRED_GAIN_MIN) -> dict[str, Any]:
    """The complete design.md §6 gate -> exactly one of the four declared
    states (plan V11-A15), with the passing-geometry selection rule (smallest
    W, then smallest w; no secondary score).

    ``conservative[s][g]`` = {"coupled": float|None, "control": float|None};
    ``gains[s][g]`` = coupled - control (or None); ``seeds_ok[s][g]`` = True
    iff all 5 coupled AND control seeds of that (stratum, geometry) are valid
    and converged.  A geometry passes iff BOTH strata satisfy the absolute
    gate (S1 >= .22, S3 >= .32), the paired gain (>= .002) in each stratum,
    and all-seeds valid+converged in each stratum, AND the global checks
    (rate/resource/replay/structured/semantic) hold.

    Precedence: ``resource_blocked`` (resource check) -> ``failed_reference``
    (rate/replay/structured/semantic) -> scientific gates
    (``failed_coupling`` if none passes) -> ``ready_for_finite_length``.
    """
    for stratum in FORMAL_STRATA:
        for geometry_id in FROZEN_GEOMETRIES:
            if geometry_id not in conservative[stratum]:
                raise ValueError(f"missing conservative cell {stratum}:{geometry_id}")
            if geometry_id not in gains[stratum] or geometry_id not in seeds_ok[stratum]:
                raise ValueError(f"missing gains/seeds_ok cell {stratum}:{geometry_id}")
    checks = {
        "rate_ok": bool(rate_ok),
        "resource_ok": bool(resource_ok),
        "replay_ok": bool(replay_ok),
        "structured_ok": bool(structured_ok),
        "semantic_ok": bool(semantic_ok),
    }

    def _geometry_failure(geometry_id: str) -> str | None:
        for stratum, gate in (("S1", float(gate_s1)), ("S3", float(gate_s3))):
            if not seeds_ok[stratum][geometry_id]:
                return f"{stratum} seeds not all valid+converged"
            coupled = conservative[stratum][geometry_id]["coupled"]
            if coupled is None or coupled < float(gate):
                return (f"{stratum} conservative {coupled} < gate {float(gate)}")
            gain = gains[stratum][geometry_id]
            if gain is None or gain < float(gain_min):
                return f"{stratum} paired gain {gain} < {float(gain_min)}"
        return None

    per_geometry = {}
    for geometry_id in FROZEN_GEOMETRIES:
        reason = _geometry_failure(geometry_id)
        per_geometry[geometry_id] = {"passes": reason is None, "failure_reason": reason}

    if not checks["resource_ok"]:
        state = "resource_blocked"
        selected = None
        summary_reason = "resource limits failed (wall > 24 h or single-run RSS > 3 GiB or cap exceeded)"
    elif not (checks["rate_ok"] and checks["replay_ok"]
              and checks["structured_ok"] and checks["semantic_ok"]):
        state = "failed_reference"
        selected = None
        failed = [name for name, ok in checks.items() if name != "resource_ok" and not ok]
        summary_reason = f"reference/contract checks failed: {', '.join(failed)}"
    else:
        passing = [g for g in FROZEN_GEOMETRIES if per_geometry[g]["passes"]]
        if not passing:
            state = "failed_coupling"
            selected = None
            summary_reason = "no geometry satisfies the absolute + paired-gain + seeds gate"
        else:
            state = "ready_for_finite_length"
            selected = min(passing, key=lambda g: (
                int(FROZEN_GEOMETRIES[g]["W"]), int(FROZEN_GEOMETRIES[g]["w"])))
            summary_reason = f"selected geometry {selected} (smallest W, then smallest w)"

    return {
        "schema": "v11_execute_gate_decision_v1",
        "state": state,
        "selected_geometry": selected,
        "checks": checks,
        "per_geometry": per_geometry,
        "reason": summary_reason,
        "gate_parameters": {"S1": float(gate_s1), "S3": float(gate_s3),
                            "paired_gain_min": float(gain_min)},
        "note": "ready_for_finite_length is not promotion, qualification, or "
                "finite-code evidence (design.md §6).",
    }


# --------------------------------------------------------------------------- #
# rate-contract pre-check (pure arithmetic; no kernel run)
# --------------------------------------------------------------------------- #


def _rate_contract_ok() -> dict[str, Any]:
    """The frozen 6-cell (stratum x geometry) rate contract at 1e-12
    (plan rate_reconstruction; V11-A05).  Arithmetic only — no run."""
    checks: list[dict[str, Any]] = []
    for stratum, winner, rate in (("S1", V10_WINNER_S1, V10_WINNER_S1_RATE),
                                  ("S3", V10_WINNER_S3, V10_WINNER_S3_RATE)):
        for geometry_id, params in FROZEN_GEOMETRIES.items():
            contract = rate_contract(int(params["L"]), int(params["w"]),
                                     rate, winner)
            checks.append({
                "stratum": stratum,
                "geometry_id": geometry_id,
                "ok": bool(contract["ok"]),
                "R_base": contract["R_base"],
                "R_L": contract["R_L"],
                "diff_reconstructed_vs_base": contract["diff_reconstructed_vs_base"],
                "diff_terminated_vs_eff": contract["diff_terminated_vs_eff"],
                "tol": contract["tol"],
            })
    return {"ok": all(c["ok"] for c in checks), "checks": checks}


# --------------------------------------------------------------------------- #
# worker side (module-level so multiprocessing spawn can pickle it)
# --------------------------------------------------------------------------- #


def _write_json(path: str, payload: dict) -> None:
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


def _execute_search_task(task: tuple[RunSpec, Callable | None]) -> dict[str, Any]:
    """Execute one run spec's full threshold search (all probes) under the
    process-tree RSS watcher, write the per-run artifacts to its independent
    output directory, and return ``{"search", "measurement"}``."""
    spec, runner = task
    out_dir = spec.out_dir
    if out_dir is not None:
        os.makedirs(out_dir, exist_ok=True)
    start = time.perf_counter()
    watcher = ProcessTreeRSSWatcher(interval=spec.watcher_interval,
                                    cap_bytes=RSS_CAP_BYTES)
    with watcher:
        search = threshold_search_run(spec, runner=runner)
    wall_seconds = time.perf_counter() - start
    measurement = {
        "schema": "v11_execute_run_measurement_v1",
        "run_id": spec.run_id,
        "stratum": spec.stratum,
        "geometry_id": spec.geometry_id,
        "seed": int(spec.seed),
        "arm": spec.arm,
        "q": int(spec.q),
        "L": int(spec.L),
        "w": int(spec.w),
        "W": int(spec.W),
        "n_samples": int(spec.n_samples),
        "max_iter": int(spec.max_iter),
        "entropy_tol": float(spec.entropy_tol),
        "streak": int(spec.streak),
        "probe_count": int(search["probe_count_total"]),
        "probes_executed": len(search["probes"]),
        "status": search["status"],
        "threshold_estimate": search["threshold_estimate"],
        "wall_seconds": wall_seconds,
        "peak_rss_bytes": int(watcher.peak_rss_bytes),
        "cap_exceeded": bool(watcher.cap_exceeded),
        "rss_cap_bytes": RSS_CAP_BYTES,
        "output_dir": out_dir,
    }
    if out_dir is not None:
        _write_json(os.path.join(out_dir, "threshold_search.json"), search)
        _write_json(os.path.join(out_dir, "run_measurement.json"), measurement)
    return {"search": search, "measurement": measurement}


# --------------------------------------------------------------------------- #
# pool driver (mirrors run_parallel semantics; wall-limit at task granularity)
# --------------------------------------------------------------------------- #


def _validate_workers(workers: Any) -> int:
    if isinstance(workers, bool) or not isinstance(workers, Integral) or int(workers) < 1:
        raise ValueError("workers must be an integer >= 1")
    return int(workers)


def run_search_parallel(run_specs: Sequence[RunSpec], workers: int, *,
                        warmup: bool = True, runner: Callable | None = None,
                        serial: bool = False,
                        wall_limit_seconds: float = WALL_LIMIT_SECONDS,
                        on_progress: Callable[[dict], None] | None = None,
                        ) -> tuple[list[dict], float, list[str]]:
    """Run the 60-task threshold-search matrix through a worker pool.

    Mirrors :func:`nonbinary_v11_parallel.run_parallel`: order-preserving
    ``pool.imap(..., chunksize=1)``, one tiny numba warmup run per worker
    before the timed batch (``_warmup_task``), per-task process-tree RSS
    watcher.  Each task is one run spec's full binary search; the scientific
    single-run results stay bit-identical to serial (same frozen kernel).

    ``on_progress`` (optional; default None) is invoked parent-side with each
    completed outcome as it arrives — the hook the execution driver uses to
    refresh ``progress.json`` per completed run.  When None, behavior is
    unchanged.

    Returns ``(outcomes, batch_wall_seconds, incomplete_run_ids)``.  Every
    outcome carries its own ``run_id`` so callers must not assume positional
    alignment.  ``serial=True`` executes in-process (test/debug path; no
    pickling constraint on ``runner``).  ``runner`` must be picklable for the
    pool path (default: the module-level :func:`_default_probe_runner`).

    Wall-clock hard limit (plan stopping_rules.interrupt_handling): checked at
    task granularity; when exceeded, remaining queued tasks are terminated
    (pool exit) and their run IDs are reported as incomplete.  Mid-task
    preemption of a running kernel is not attempted (kernel-level kill is
    outside this driver's contract; partial artifacts are retained).
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
            raise ValueError(f"duplicate run_id in search batch: {spec.run_id}")
        seen.add(spec.run_id)
    if isinstance(wall_limit_seconds, bool) \
            or not isinstance(wall_limit_seconds, (int, float)) \
            or not math.isfinite(float(wall_limit_seconds)) \
            or float(wall_limit_seconds) <= 0.0:
        raise ValueError("wall_limit_seconds must be positive and finite")
    wall_limit_seconds = float(wall_limit_seconds)
    effective_runner = runner if runner is not None else _default_probe_runner

    outcomes: list[dict] = []
    start = time.perf_counter()
    if serial:
        for spec in run_specs:
            if time.perf_counter() - start > wall_limit_seconds:
                break
            outcome = _execute_search_task((spec, effective_runner))
            outcomes.append(outcome)
            if on_progress is not None:
                on_progress(outcome)
        batch_wall_seconds = time.perf_counter() - start
    else:
        with multiprocessing.Pool(processes=workers) as pool:
            if warmup:
                list(pool.map(_warmup_task, range(workers)))
            start = time.perf_counter()
            iterator = pool.imap(_execute_search_task,
                                 [(spec, effective_runner) for spec in run_specs],
                                 chunksize=1)
            while len(outcomes) < len(run_specs):
                if time.perf_counter() - start > wall_limit_seconds:
                    break
                try:
                    outcome = next(iterator)
                except StopIteration:
                    break
                outcomes.append(outcome)
                if on_progress is not None:
                    on_progress(outcome)
            batch_wall_seconds = time.perf_counter() - start
    done = {outcome["search"]["run_id"] for outcome in outcomes}
    incomplete = [spec.run_id for spec in run_specs if spec.run_id not in done]
    return outcomes, batch_wall_seconds, incomplete


# --------------------------------------------------------------------------- #
# full formal-matrix driver + evidence summary
# --------------------------------------------------------------------------- #


def execute_formal_matrix(*, out_root: str, workers: int = DEFAULT_WORKERS,
                          warmup: bool = True, runner: Callable | None = None,
                          serial: bool = False,
                          wall_limit_seconds: float = WALL_LIMIT_SECONDS,
                          replay_ok: bool = False, structured_ok: bool = False,
                          semantic_ok: bool = False,
                          resume: bool = False,
                          heartbeat_interval: float = HEARTBEAT_INTERVAL_SECONDS,
                          ) -> dict[str, Any]:
    """Execute the frozen 60-run matrix exactly once and write the full
    evidence bundle under ``out_root`` (plan output_paths).

    Writes per-run ``threshold_search.json`` + ``run_measurement.json`` under
    ``{out_root}/{run_id}/`` and the aggregate
    ``{out_root}/formal_matrix_results.json``: 60-run table, conservative
    aggregates, paired gains, rate-contract check, resource evidence, and the
    design.md §6 gate decision (plan V11-A13/A15).

    ``replay_ok`` / ``structured_ok`` / ``semantic_ok`` default False: they are
    produced by V11-40.3 replay / V11-50.x and passed by the main thread; the
    summary marks the gate evaluation accordingly (provisional until the full
    check set is supplied).  If any run is incomplete (wall limit), no gate
    decision is computed (plan: incomplete runs do not contribute).

    Execution bookkeeping (additive, V11-40.2): ``progress.json`` is written
    under ``out_root`` throughout (all 60 entries; refreshed on every run
    completion) and ``heartbeat.json`` every ``heartbeat_interval`` seconds by
    a daemon thread.  ``resume=True`` loads runs whose per-run evidence is
    complete and parseable (see :func:`scan_completed_runs`) instead of
    re-executing them — completed evidence is never re-run; only missing/torn/
    unparseable (i.e. interrupted) runs are re-executed.  ``batch_wall_seconds``
    in the summary measures the current session only (on resume, the pending
    subset); the wall-limit check is enforced per session.

    NOTE: calling this performs SCIENTIFIC execution.  It must only be invoked
    under V11-40.2 main-thread authorization (see module docstring).
    """
    if not isinstance(out_root, str) or not out_root:
        raise ValueError("out_root must be a non-empty path")
    if isinstance(heartbeat_interval, bool) \
            or not isinstance(heartbeat_interval, (int, float)) \
            or float(heartbeat_interval) <= 0.0:
        raise ValueError("heartbeat_interval must be positive and finite")
    os.makedirs(out_root, exist_ok=True)
    specs = formal_matrix_run_specs(out_root=out_root)

    # ---- bookkeeping: load-or-init progress, compute the resume skip set ----
    progress = load_progress(out_root)
    for spec in specs:
        if spec.run_id not in progress:
            progress[spec.run_id] = {
                "state": "pending", "started_at": None, "finished_at": None,
                "results_file": None, "probes_executed": 0,
            }
    completed_run_ids: list[str] = []
    resumed_outcomes: dict[str, dict] = {}
    if resume:
        completed_run_ids, resumed_outcomes = scan_completed_runs(
            out_root, [spec.run_id for spec in specs])
    for run_id in completed_run_ids:
        # skipped runs keep their prior finished_at when the previous session
        # recorded it; the state reflects the loaded evidence (never "pending")
        outcome = resumed_outcomes[run_id]
        entry = progress[run_id]
        entry["state"] = _progress_state_for(str(outcome["search"]["status"]))
        entry["finished_at"] = entry.get("finished_at") or _utc_timestamp()
        entry["results_file"] = os.path.join(run_id, "threshold_search.json")
        entry["probes_executed"] = int(
            outcome["measurement"].get("probes_executed", 0))
    pending_specs = [spec for spec in specs if spec.run_id not in resumed_outcomes]
    for spec in pending_specs:
        progress[spec.run_id].update(state="running", started_at=_utc_timestamp())
    write_progress(out_root, progress)

    # ---- heartbeat daemon (hang diagnostic; must never kill the batch) ----
    stop = threading.Event()

    def _heartbeat_loop() -> None:
        while not stop.wait(heartbeat_interval):
            try:
                table = load_progress(out_root)
                terminal = sum(1 for entry in table.values()
                               if entry.get("state") in TERMINAL_STATES)
                running = sum(1 for entry in table.values()
                              if entry.get("state") == "running")
                write_heartbeat(out_root, runs_done=terminal, runs_running=running)
            except Exception:  # ponytail: a failed heartbeat tick must not stop the matrix
                pass

    heartbeat_thread = threading.Thread(target=_heartbeat_loop, daemon=True)
    heartbeat_thread.start()
    write_heartbeat(out_root, runs_done=0, runs_running=len(pending_specs))

    def _on_progress(outcome: dict) -> None:
        run_id = outcome["search"]["run_id"]
        entry = progress[run_id]
        entry["state"] = _progress_state_for(str(outcome["search"]["status"]))
        entry["finished_at"] = _utc_timestamp()
        entry["results_file"] = os.path.join(run_id, "threshold_search.json")
        entry["probes_executed"] = int(
            outcome["measurement"].get("probes_executed", 0))
        write_progress(out_root, progress)

    try:
        if pending_specs:
            new_outcomes, batch_wall_seconds, _ = run_search_parallel(
                pending_specs, workers, warmup=warmup, runner=runner,
                serial=serial, wall_limit_seconds=wall_limit_seconds,
                on_progress=_on_progress)
        else:
            new_outcomes, batch_wall_seconds = [], 0.0
    finally:
        stop.set()
        terminal = sum(1 for entry in progress.values()
                       if entry.get("state") in TERMINAL_STATES)
        running = sum(1 for entry in progress.values()
                      if entry.get("state") == "running")
        write_heartbeat(out_root, runs_done=terminal, runs_running=running)

    outcomes = list(resumed_outcomes.values()) + list(new_outcomes)

    by_run_id = {outcome["search"]["run_id"]: outcome for outcome in outcomes}
    done_run_ids = set(by_run_id)
    incomplete = [spec.run_id for spec in specs if spec.run_id not in done_run_ids]
    seeds = seed_integers()
    seed_n_by_id = {entry["run_id"]: entry["seed_n"] for entry in seeds}

    runs: list[dict[str, Any]] = []
    for spec in specs:
        outcome = by_run_id.get(spec.run_id)
        if outcome is None:
            continue  # incomplete run; listed separately below
        measurement = outcome["measurement"]
        search = outcome["search"]
        runs.append({
            "run_id": spec.run_id,
            "stratum": spec.stratum,
            "geometry_id": spec.geometry_id,
            "seed_n": seed_n_by_id[spec.run_id],
            "seed": int(spec.seed),
            "arm": spec.arm,
            "w": int(spec.w),
            "W": int(spec.W),
            "L": int(spec.L),
            "q": int(spec.q),
            "n_samples": int(spec.n_samples),
            "max_iter": int(spec.max_iter),
            "entropy_tol": float(spec.entropy_tol),
            "streak": int(spec.streak),
            "probe_range": list(search["probe_range"]),
            "probe_count": int(search["probe_count_total"]),
            "status": search["status"],
            "threshold_estimate": search["threshold_estimate"],
            "wall_seconds": measurement["wall_seconds"],
            "peak_rss_bytes": measurement["peak_rss_bytes"],
            "cap_exceeded": measurement["cap_exceeded"],
        })

    rate = _rate_contract_ok()
    peak_rss = max((r["peak_rss_bytes"] for r in runs), default=0)
    cap_exceeded_runs = [r["run_id"] for r in runs if r["cap_exceeded"]]
    resource_ok = (batch_wall_seconds <= wall_limit_seconds
                   and peak_rss <= RSS_CAP_BYTES and not cap_exceeded_runs)

    summary: dict[str, Any] = {
        "schema": "v11_execute_formal_matrix_results_v1",
        "authorization": "V11-40.2 main-thread authorization required for "
                         "scientific execution (module docstring)",
        "execution_root": out_root,
        "executed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "status": "incomplete" if incomplete else "completed",
        "incomplete_runs": incomplete,
        "n_runs_total": len(specs),
        "n_runs_completed": len(runs),
        "runs": runs,
        "resource": {
            "batch_wall_seconds": batch_wall_seconds,
            "wall_limit_seconds": wall_limit_seconds,
            "wall_ok": batch_wall_seconds <= wall_limit_seconds,
            "peak_rss_bytes": peak_rss,
            "rss_cap_bytes": RSS_CAP_BYTES,
            "rss_ok": peak_rss <= RSS_CAP_BYTES,
            "cap_exceeded_runs": cap_exceeded_runs,
            "resource_ok": resource_ok,
        },
        "rate_contract": rate,
        "bookkeeping": {
            "schema": "v11_execute_bookkeeping_v1",
            "progress_file": _progress_path(out_root),
            "heartbeat_file": _heartbeat_path(out_root),
            "resume": bool(resume),
            "n_skipped_completed": len(completed_run_ids),
            "skipped_run_ids": sorted(completed_run_ids),
            "session_n_runs_executed": len(new_outcomes),
            "session_batch_wall_seconds": batch_wall_seconds,
            "session_wall_note": "batch_wall_seconds covers the current "
                                 "session only; resumed runs are loaded from "
                                 "prior evidence, not re-executed",
        },
    }

    if incomplete:
        summary["gate"] = {
            "schema": "v11_execute_gate_decision_v1",
            "state": "incomplete",
            "note": "incomplete runs do not contribute to threshold decisions "
                    "(plan stopping_rules.interrupt_handling); no gate evaluation.",
        }
        _write_json(os.path.join(out_root, "formal_matrix_results.json"), summary)
        return summary

    conservative: dict[str, dict[str, dict[str, Any]]] = {
        s: {g: {} for g in FROZEN_GEOMETRIES} for s in FORMAL_STRATA}
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for spec in specs:
        outcome = by_run_id[spec.run_id]
        groups.setdefault((spec.stratum, spec.geometry_id, spec.arm), []).append(
            outcome["search"])
    for (stratum, geometry_id, arm), searches in groups.items():
        conservative[stratum][geometry_id][arm] = aggregate_conservative(
            searches, stratum=stratum, geometry_id=geometry_id, arm=arm)

    gains: dict[str, dict[str, float | None]] = {s: {} for s in FORMAL_STRATA}
    seeds_ok: dict[str, dict[str, bool]] = {s: {} for s in FORMAL_STRATA}
    # gate_decision consumes the DOCUMENTED float shape
    # (conservative[s][g][arm] = threshold | None); the summary keeps the full
    # aggregate dicts (aggregate_conservative) unchanged.
    conservative_thresholds: dict[str, dict[str, dict[str, float | None]]] = {
        s: {g: {} for g in FROZEN_GEOMETRIES} for s in FORMAL_STRATA}
    for stratum in FORMAL_STRATA:
        for geometry_id in FROZEN_GEOMETRIES:
            coupled = conservative[stratum][geometry_id]["coupled"]
            control = conservative[stratum][geometry_id]["control"]
            conservative_thresholds[stratum][geometry_id] = {
                "coupled": coupled["conservative_threshold"],
                "control": control["conservative_threshold"],
            }
            gains[stratum][geometry_id] = paired_gain(
                coupled["conservative_threshold"], control["conservative_threshold"])
            seeds_ok[stratum][geometry_id] = (
                coupled["seeds_valid"] and coupled["seeds_converged"]
                and control["seeds_valid"] and control["seeds_converged"])

    decision = gate_decision(
        conservative=conservative_thresholds, gains=gains, seeds_ok=seeds_ok,
        rate_ok=rate["ok"], resource_ok=resource_ok,
        replay_ok=replay_ok, structured_ok=structured_ok,
        semantic_ok=semantic_ok)

    summary["conservative"] = conservative
    summary["paired_gains"] = gains
    summary["seeds_ok"] = seeds_ok
    summary["gate"] = decision
    summary["provisional_note"] = (
        "replay_ok/structured_ok/semantic_ok default to False until V11-40.3 "
        "replay and V11-50.x evidence are produced; the final state is fixed "
        "by the main thread (V11-50.1) with the full check set.")
    _write_json(os.path.join(out_root, "formal_matrix_results.json"), summary)
    return summary


# --------------------------------------------------------------------------- #
# structural self-check (tiny; NO scientific run, NO pool)
# --------------------------------------------------------------------------- #


def _synthetic_search(threshold: float | None, *, stratum: str,
                      geometry_id: str, arm: str, seed: int) -> dict[str, Any]:
    """A deterministic fake per-seed search result for structural checks."""
    return {
        "stratum": stratum,
        "geometry_id": geometry_id,
        "arm": arm,
        "status": "valid" if threshold is not None else "not_converged",
        "threshold_estimate": threshold,
    }


def _self_check() -> None:
    """Structural verification of the executor: frozen matrix shape, seed
    determinism/uniqueness, probe counts, aggregation min semantics, and the
    four-state gate logic on synthetic numbers.  No scientific run."""
    specs = formal_matrix_run_specs()
    assert len(specs) == 60, "frozen 2x3x5x2 matrix"
    seeds = seed_integers()
    assert len(seeds) == 60, "60 seed entries"
    assert seeds == seed_integers(), "seed derivation must be deterministic"
    assert len({entry["seed"] for entry in seeds}) == 60, "60 distinct seeds"
    assert [s.seed for s in specs] == [entry["seed"] for entry in seeds], \
        "seed_integers must agree with formal_matrix_run_specs"
    n_s1 = probe_count(*PROBE_RANGES["S1"], SEARCH_P_TOL)
    n_s3 = probe_count(*PROBE_RANGES["S3"], SEARCH_P_TOL)
    assert n_s1 == 7 and n_s3 == 7, "frozen per-stratum ranges -> 7 probes/run"

    # aggregation min semantics on synthetic per-seed thresholds
    fake = [_synthetic_search(t, stratum="S1", geometry_id="G1", arm="coupled",
                              seed=i) for i, t in enumerate([0.21, 0.20, 0.22, 0.19, 0.21])]
    agg = aggregate_conservative(fake, stratum="S1", geometry_id="G1", arm="coupled")
    assert agg["conservative_threshold"] == 0.19, "conservative = min of 5 seeds"
    assert agg["seeds_valid"] and agg["seeds_converged"]
    bad = list(fake)
    bad[2] = _synthetic_search(None, stratum="S1", geometry_id="G1",
                               arm="coupled", seed=99)
    agg_bad = aggregate_conservative(bad, stratum="S1", geometry_id="G1", arm="coupled")
    assert agg_bad["conservative_threshold"] is None and agg_bad["below_range"], \
        "a non-converged seed marks the cell below range"

    # four gate states on synthetic numbers
    def passing_data() -> tuple[dict, dict, dict]:
        conservative = {}
        gains = {}
        seeds_ok = {}
        for s, gate in (("S1", GATE_S1), ("S3", GATE_S3)):
            conservative[s] = {}
            gains[s] = {}
            seeds_ok[s] = {}
            for g in FROZEN_GEOMETRIES:
                conservative[s][g] = {"coupled": gate + 0.02, "control": gate - 0.005}
                gains[s][g] = 0.025
                seeds_ok[s][g] = True
        return conservative, gains, seeds_ok

    conservative, gains, seeds_ok = passing_data()
    ok_checks = dict(rate_ok=True, resource_ok=True, replay_ok=True,
                     structured_ok=True, semantic_ok=True)
    decision = gate_decision(conservative=conservative, gains=gains,
                             seeds_ok=seeds_ok, **ok_checks)
    assert decision["state"] == "ready_for_finite_length", "all-pass -> ready"
    assert decision["selected_geometry"] == "G1", "smallest W (8) then w (1)"

    # one geometry below the absolute gate -> the selection rule picks the
    # next smallest W among the remaining passing geometries (G2: W=16)
    failing = passing_data()
    failing[0]["S1"]["G1"] = {"coupled": GATE_S1 - 0.01, "control": GATE_S1 - 0.02}
    decision = gate_decision(conservative=failing[0], gains=failing[1],
                             seeds_ok=failing[2], **ok_checks)
    assert decision["state"] == "ready_for_finite_length", \
        "G2/G3 still pass -> ready (G1 below gate)"
    assert decision["selected_geometry"] == "G2", \
        "G2 (W=16) is the next smallest W among passing geometries"

    # no geometry passes -> failed_coupling, no selection
    all_failing = passing_data()
    for s, gate in (("S1", GATE_S1), ("S3", GATE_S3)):
        for g in FROZEN_GEOMETRIES:
            all_failing[0][s][g] = {"coupled": gate - 0.01,
                                    "control": gate - 0.02}
    decision = gate_decision(conservative=all_failing[0], gains=all_failing[1],
                             seeds_ok=all_failing[2], **ok_checks)
    assert decision["state"] == "failed_coupling", \
        "all geometries below gate -> failed_coupling"
    assert decision["selected_geometry"] is None

    decision = gate_decision(conservative=conservative, gains=gains,
                             seeds_ok=seeds_ok, **dict(ok_checks, resource_ok=False))
    assert decision["state"] == "resource_blocked", "resource failure -> blocked"

    decision = gate_decision(conservative=conservative, gains=gains,
                             seeds_ok=seeds_ok, **dict(ok_checks, replay_ok=False))
    assert decision["state"] == "failed_reference", "replay failure -> reference"

    # ---- execution bookkeeping: progress / resume / status (no scientific run) ----
    with tempfile.TemporaryDirectory() as tmp:
        root = os.path.join(tmp, "exec")
        progress = _init_progress(root)
        assert len(progress) == 60, "60-entry progress table"
        assert all(entry["state"] == "pending" for entry in progress.values())
        write_progress(root, progress)
        assert load_progress(root) == progress, "progress round-trip"
        specs = formal_matrix_run_specs(out_root=root)
        for spec in specs[:2]:
            _write_fake_run_evidence(root, spec)
            progress[spec.run_id].update(
                state=_progress_state_for("valid"),
                finished_at=_utc_timestamp(),
                results_file=os.path.join(spec.run_id, "threshold_search.json"),
                probes_executed=7)
        write_progress(root, progress)
        completed, _ = scan_completed_runs(root, [spec.run_id for spec in specs])
        assert completed == [spec.run_id for spec in specs[:2]], \
            "resume skips only evidenced runs"
        assert completed_run_outcome(root, specs[2].run_id) is None, \
            "un-evidenced run is re-executable"
        status = summarize_status(root)
        assert status["n_total"] == 60 and status["n_terminal"] == 2, \
            "status totals"
        assert status["by_state"]["done"] == 2
        assert _progress_state_for("valid") == "done"
        assert _progress_state_for("invalid") == "invalid"
        assert _progress_state_for("not_converged") == "not_converged"

    print(json.dumps({
        "schema": "v11_execute_self_check_v1",
        "ok": True,
        "n_specs": 60,
        "n_probes_s1": n_s1,
        "n_probes_s3": n_s3,
        "gate_states_verified": ["ready_for_finite_length", "failed_coupling",
                                 "resource_blocked", "failed_reference"],
        "bookkeeping_verified": ["progress_write_load", "resume_skip_scan",
                                 "status_summary", "state_mapping"],
    }, indent=2, sort_keys=True))


def _dry_run(out_dir: str) -> dict[str, Any]:
    """Structural dry-run evidence (no scientific execution): matrix shape,
    seed integers, probe counts, synthetic gate logic.  Writes
    ``formal_matrix_dry_run.json`` under ``out_dir``."""
    specs = formal_matrix_run_specs()
    seeds = seed_integers()
    summary = {
        "schema": "v11_execute_dry_run_v1",
        "scientific_executed": False,
        "authorization_note": "V11-40.2 not authorized; structure-only dry run.",
        "n_specs": len(specs),
        "n_seeds": len(seeds),
        "probe_counts": {
            "S1": probe_count(*PROBE_RANGES["S1"], SEARCH_P_TOL),
            "S3": probe_count(*PROBE_RANGES["S3"], SEARCH_P_TOL),
            "wide_microbench_range_reference": probe_count(0.10, 0.40, SEARCH_P_TOL),
        },
        "seed_integers": seeds,
        "run_ids": [spec.run_id for spec in specs],
        "runs_per_cell": {
            "strata": list(FORMAL_STRATA),
            "geometries": {g: dict(p) for g, p in FROZEN_GEOMETRIES.items()},
            "n_seeds": FORMAL_N_SEEDS,
            "arms": list(ARM_ORDER),
            "total": len(FORMAL_STRATA) * len(FROZEN_GEOMETRIES)
                     * FORMAL_N_SEEDS * FORMAL_ARMS,
        },
    }
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "formal_matrix_dry_run.json")
    _write_json(path, summary)
    summary["evidence_path"] = path
    return summary


if __name__ == "__main__":
    _self_check()
