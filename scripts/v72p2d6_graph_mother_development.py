"""D6 development runner — frozen §8 pipeline: structure freeze, blind selection,
canary, confirmation/scaling, scalar evidence. Explicit injection only.

One fresh UUID root per run; refuses to overwrite. Scalar/metadata evidence
only (no symbols, priors, beliefs, matrices persisted). One decoder invocation
per frozen cell, no retries. Watchdog: dedicated respawnable worker process
(120 s per invocation, pids logged).

R1c: parallel-only revision (semantics unchanged): structure arm×layer via
ProcessPoolExecutor; decoder cells across an 18-worker pool (leave 2 cores,
RSS-gated downgrade 18/14/12/8); main-process single-thread sample generation
then read-only share; per-cell PID/wall/RSS; 120 s poll+terminate/respawn;
no retry; chunked append same UUID root each chunk <1.5 h.
"""
import argparse
import concurrent.futures
import csv
import json
import multiprocessing as mp
import os
import pathlib
import queue
import subprocess
import sys
import threading
import time

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "comparison_bench" / "src"))
from comparison_bench.formal_ir.v72p2d6_gf32_graph_mother import (
    ARMS, ROW_BUDGETS, CANARY_SEEDS, CONF_SEEDS, SCALING_SEEDS, T_ARMS, M_ARMS,
    build_mother, build_support, support_window_overflow, d5,
    assert_no_formal_write, write_structure_records, select_decoder_arms,
    select_advancement, structural_rank_list, classify_terminal, audit_extra,
)

CALL_BUDGET = 2500
WALL_BUDGET = 12 * 3600
WATCHDOG = 120
RSS_CEIL = 2 * 1024 ** 3
POINTS = ("f1.0", "f1.2", "square")
MODES = ("L1", "L2-APP", "L2-oracle")
# R1c parallel freeze (mechanics only, no semantic change).
R1C_FULL_WORKERS = 18  # 20 logical cores, leave 2
R1C_FALLBACK_WORKERS = (14, 12, 8)
R1C_CHUNK_WALL_MAX = int(1.5 * 3600)  # each chunk <1.5 h, same UUID root append
R1C_REVISION = "R1c-A1"
# R1c-A1: chunk-wall overrun is an explicit blocking terminal (not warning-only).
R1C_CHUNK_WALL_BLOCKED_TERMINAL = "D6_GRAPH_CHUNK_WALL_BLOCKED"
DECODER_FIELDNAMES = ["call_idx", "arm", "n", "seed", "point", "rows_l1",
                      "rows_l2", "mode", "matrix_id", "exact", "syndrome_ok",
                      "iterations", "finite", "crash", "timeout",
                      "prior_mass_on_truth", "wall_s", "rss_bytes",
                      "watchdog_ok", "worker_pid"]

LOG = []


def log(msg, fh=None):
    line = "%s %s" % (time.strftime("%Y-%m-%dT%H:%M:%S"), msg)
    print(line, flush=True)
    LOG.append(line)
    if fh is not None:
        fh.write(line + "\n")
        fh.flush()


def _worker_main(conn, src_dir):
    sys.path.insert(0, src_dir)
    import numpy as _np
    import os as _os
    from comparison_bench.formal_ir import v72p2d5_gf32_rate_mother as core
    dec = core.bind_historical_decoder()
    # Warmup (setup, counted as 1 setup_decoder_calls by the parent via
    # reserve_setup_idx): compile the decoder on a tiny fixture so no frozen
    # cell absorbs compile time. Setup + scientific must stay <= 2500.
    try:
        hw = _np.eye(8, dtype=_np.uint8)
        pw = _np.full((8, 32), 1.0 / 32, dtype=_np.float64)
        core._decode_block(dec, hw, pw, _np.zeros(8, dtype=_np.int64))
        warm = "ok"
    except Exception as ex:  # noqa: BLE001
        warm = "fail:%r" % (ex,)
    conn.send({"event": "ready", "pid": _os.getpid(),
               "rss": core._rss_bytes(), "warmup": warm})
    while True:
        task = conn.recv()
        if task is None:
            break
        t0 = time.perf_counter()
        try:
            h = _np.asarray(task["h"], dtype=_np.uint8)
            prior = _np.asarray(task["prior"], dtype=_np.float64)
            xt = _np.asarray(task["x_true"], dtype=_np.int64)
            e, s, it, f, bel = core._decode_block(dec, h, prior, xt)
            out = {"exact": bool(e), "syndrome_ok": bool(s),
                   "iterations": int(it), "finite": bool(f),
                   "beliefs": _np.asarray(bel, dtype=_np.float64)
                   if task.get("return_beliefs") and bel is not None else None,
                   "crash": False, "error": ""}
        except Exception as ex:  # noqa: BLE001 - crash consumes the cell
            out = {"exact": False, "syndrome_ok": False, "iterations": -1,
                   "finite": False, "beliefs": None, "crash": True,
                   "error": repr(ex)[:300]}
        out["wall_s"] = time.perf_counter() - t0
        try:
            out["rss"] = core._rss_bytes()
        except Exception:  # noqa: BLE001
            out["rss"] = None
        conn.send(out)


def reserve_setup_idx(state):
    """R1c-A1: reserve one warmup/setup call inside the lock before spawn."""
    lock = state.get("lock")
    if lock is not None:
        lock.acquire()
    try:
        if (int(state.get("setup_calls", 0)) + int(state.get("calls", 0))
                + 1 > CALL_BUDGET
                or time.perf_counter() - state["t0"] > WALL_BUDGET
                or state.get("budget_stop")):
            state["budget_stop"] = True
            raise StopIteration("budget-exhausted-setup")
        state["setup_calls"] = int(state.get("setup_calls", 0)) + 1
        return int(state["setup_calls"])
    finally:
        if lock is not None:
            try:
                lock.release()
            except RuntimeError:
                pass


def reserve_call_idx(state):
    """R1c-A1: atomically reserve one scientific call_idx + budget pre-dispatch."""
    lock = state.get("lock")
    if lock is not None:
        lock.acquire()
    try:
        if (int(state.get("setup_calls", 0)) + int(state.get("calls", 0))
                + 1 > CALL_BUDGET
                or time.perf_counter() - state["t0"] > WALL_BUDGET
                or state.get("budget_stop")):
            state["budget_stop"] = True
            raise StopIteration("budget-exhausted")
        state["calls"] = int(state.get("calls", 0)) + 1
        return int(state["calls"])
    finally:
        if lock is not None:
            try:
                lock.release()
            except RuntimeError:
                pass


class Worker:
    """Dedicated respawnable decoder worker; exactly one task-owned process."""

    def __init__(self, logfh, state=None):
        self.logfh = logfh
        self.state = state
        self.pids = []
        self.proc = None
        self.conn = None
        self.last_rss = None
        self.spawn(reason="initial")

    def spawn(self, reason):
        if self.state is not None:
            reserve_setup_idx(self.state)
        if self.proc is not None:
            try:
                self.conn.close()
            except Exception:  # noqa: BLE001
                pass
        ctx = mp.get_context()
        parent, child = ctx.Pipe(duplex=True)
        p = ctx.Process(target=_worker_main,
                        args=(child, str(ROOT / "comparison_bench" / "src")))
        p.daemon = True
        p.start()
        child.close()
        if not parent.poll(300):
            parent.close()
            p.terminate()
            p.join(10)
            raise RuntimeError("worker spawn timed out")
        hello = parent.recv()
        self.proc = p
        self.conn = parent
        self.pids.append(int(hello["pid"]))
        try:
            self.last_rss = (int(hello["rss"])
                             if hello.get("rss") is not None else None)
        except (TypeError, ValueError):
            self.last_rss = None
        log("worker spawn (%s) pid=%s warmup=%s" % (
            reason, hello["pid"], hello.get("warmup")), self.logfh)

    def call(self, task):
        """One invocation; on watchdog timeout terminate+respawn, no retry."""
        assert self.proc is not None
        self.conn.send(task)
        if not self.conn.poll(WATCHDOG):
            pid = self.proc.pid
            self.conn.close()
            self.proc.terminate()
            self.proc.join(10)
            self.spawn(reason="watchdog-timeout-after-pid-%s" % pid)
            return {"exact": False, "syndrome_ok": False, "iterations": -1,
                    "finite": False, "beliefs": None, "crash": True,
                    "timeout": True, "wall_s": float(WATCHDOG),
                    "rss": None, "error": "watchdog-timeout"}
        res = self.conn.recv()
        res["timeout"] = False
        return res

    def stop(self):
        try:
            self.conn.send(None)
            self.conn.close()
        except Exception:  # noqa: BLE001
            pass
        self.proc.join(10)
        if self.proc.is_alive():
            self.proc.terminate()
            self.proc.join(10)


def pool_aggregate_rss(worker_rss_list, main_rss):
    """R1c-A1: pool sum + main sum (None entries ignored, None main = 0)."""
    total = int(main_rss) if main_rss is not None else 0
    for v in (worker_rss_list or []):
        if v is not None:
            total += int(v)
    return int(total)


def select_effective_workers(requested, worker_rss_list, main_rss,
                             logfh=None):
    """R1c-A1 pure selector: hard ceiling + measured aggregate gate.

    requested is a hard ceiling (never upscale). per_worker is the max of
    measured startup worker RSS; no invented estimate (all-None stays at
    requested with rss-unknown logged). Effective is the largest
    w <= requested with w*per_worker + main < 2GiB, else the floor.
    """
    req = int(requested)
    if req == 1:
        return 1
    cands = [int(w) for w in (R1C_FULL_WORKERS,)
             + tuple(R1C_FALLBACK_WORKERS) if int(w) <= req]
    if not cands:
        cands = [req]
    known = [int(v) for v in (worker_rss_list or []) if v is not None]
    if not known:
        if logfh is not None:
            log("r1c-a1 workers requested=%d effective=%d rss-unknown"
                % (req, req), logfh)
        return int(req)
    per = max(known)
    main = int(main_rss) if main_rss is not None else 0
    for w in cands:
        if int(w) * int(per) + int(main) < RSS_CEIL:
            if logfh is not None:
                log("r1c-a1 workers requested=%d effective=%d "
                    "per_worker_rss=%d main_rss=%s" % (req, int(w), per,
                                                      str(main_rss)),
                    logfh)
            return int(w)
    if logfh is not None:
        log("r1c-a1 workers requested=%d effective=%d (floor, over-budget) "
            "per_worker_rss=%d main_rss=%s" % (req, int(cands[-1]), per,
                                              str(main_rss)), logfh)
    return int(cands[-1])


def choose_worker_count(requested, per_worker_rss=None, main_rss=None,
                        logfh=None):
    """R1c-A1: requested hard ceiling + measured gate (no hardcoded estimate)."""
    req = int(requested)
    if req == 1:
        return 1
    rss_list = ([int(per_worker_rss)]
                if per_worker_rss is not None else [])
    return select_effective_workers(req, rss_list, main_rss, logfh)


def _build_one_arm_layer(job):
    """R1c: top-level picklable unit for arm×layer parallel structure."""
    import sys as _sys
    import pathlib as _pl
    import numpy as _np
    root = _pl.Path(__file__).resolve().parents[1]
    _sys.path.insert(0, str(root / "comparison_bench" / "src"))
    from comparison_bench.formal_ir import v72p2d6_gf32_graph_mother as _d6
    arm, n, layer = job
    _H, _sup = _d6.build_mother(arm, int(n), layer)
    _sup2 = _d6.build_support(arm, int(n), layer)
    _H2, _ = _d6.build_mother(arm, int(n), layer)
    replay_ok = bool(_np.array_equal(_np.asarray(_sup), _np.asarray(_sup2))
                     and _np.array_equal(_np.asarray(_H), _np.asarray(_H2)))
    return (arm, layer, _np.asarray(_H, dtype=_np.uint8),
            _np.asarray(_sup), replay_ok)


def build_structures_parallel(n, logfh, max_workers=18):
    """R1c: arm×layer parallel; deterministic ARMS-order assembly.

    Identical records/summary/mothers to build_structures (replay per task).
    """
    import os as _os
    jobs = [(arm, int(n), layer) for arm in ARMS for layer in ("L1", "L2")]
    t0 = time.perf_counter()
    out = {}
    with concurrent.futures.ProcessPoolExecutor(
            max_workers=int(max_workers)) as ex:
        for arm, layer, H, sup, replay_ok in ex.map(_build_one_arm_layer,
                                                    jobs):
            out[(arm, layer)] = (H, sup, replay_ok)
    # Deterministic assembly in ARMS order (same as sequential).
    records = []
    summary = {}
    mothers = {}
    for arm in ARMS:
        for layer in ("L1", "L2"):
            H, sup, replay_ok = out[(arm, layer)]
            ov = support_window_overflow(arm, n, layer)
            prefixes = (ROW_BUDGETS[n][layer][0], ROW_BUDGETS[n][layer][1], n)
            audits = []
            for k in prefixes:
                rep = d5.audit_prefix(np.asarray(H), int(k))
                merged_extra = audit_extra(np.asarray(H), int(k), arm)
                merged = {**rep, **merged_extra}
                eligible = bool(
                    rep["passed"]
                    and rep["duplicate_projective_columns"] == 0
                    and rep["base_pair_duplicates"] == 0
                    and rep["support_triple_duplicates"] == 0)
                if arm in M_ARMS:
                    eligible = bool(
                        eligible and merged_extra["m_cycle_rank"] == 0)
                merged["eligible"] = eligible
                merged["window_overflow"] = ov
                merged["determinism_ok"] = replay_ok
                merged["prefix_rows"] = int(k)
                audits.append(merged)
                records.append({
                    "arm": arm, "n": n, "layer": layer,
                    "prefix_rows": int(k),
                    "rank": rep["rank"], "zero_rows": rep["zero_rows"],
                    "zero_columns": rep["zero_columns"],
                    "connected_components": rep["connected_components"],
                    "largest_component_fraction":
                        rep["largest_component_fraction"],
                    "four_cycles": rep["four_cycles"],
                    "four_cycle_variable_incidence_max":
                        rep["four_cycle_variable_incidence_max"],
                    "duplicate_projective_columns":
                        rep["duplicate_projective_columns"],
                    "base_pair_duplicates": rep["base_pair_duplicates"],
                    "support_triple_duplicates":
                        rep["support_triple_duplicates"],
                    "row_degree_max": merged_extra["row_degree_max"],
                    "row_degree_sumsq": merged_extra["row_degree_sumsq"],
                    "girth": (merged_extra["girth"]
                              if merged_extra["girth"] is not None
                              else "NOT_COMPUTED"),
                    "girth_reason": merged_extra["girth_reason"] or "",
                    "m_cycle_rank": (merged_extra["m_cycle_rank"]
                                     if merged_extra["m_cycle_rank"] is not None
                                     else ""),
                    "window_overflow": ov, "eligible": eligible,
                    "determinism_ok": replay_ok})
            summary.setdefault(arm, {})[layer] = {"prefix_audits": audits}
            mothers[(arm, layer)] = np.asarray(H, dtype=np.uint8)
    log("structure-parallel n=%d workers=%d wall=%.1f arms=%d records=%d pid=%d"
        % (n, int(max_workers), time.perf_counter() - t0, len(ARMS),
           len(records), _os.getpid()), logfh)
    return records, summary, mothers


def build_structures(n, logfh):
    """Build all arms/layers at width n with replay check; return records,
    summary (f1.2-indexed prefix audits), mothers {(arm,layer): H}."""
    records = []
    summary = {}
    mothers = {}
    for arm in ARMS:
        for layer in ("L1", "L2"):
            H, sup = build_mother(arm, n, layer)
            sup2 = build_support(arm, n, layer)
            H2, _ = build_mother(arm, n, layer)
            replay_ok = bool(np.array_equal(np.asarray(sup), np.asarray(sup2))
                             and np.array_equal(np.asarray(H), np.asarray(H2)))
            ov = support_window_overflow(arm, n, layer)
            prefixes = (ROW_BUDGETS[n][layer][0], ROW_BUDGETS[n][layer][1], n)
            audits = []
            for k in prefixes:
                rep = d5.audit_prefix(np.asarray(H), int(k))
                merged_extra = audit_extra(np.asarray(H), int(k), arm)
                merged = {**rep, **merged_extra}
                eligible = bool(
                    rep["passed"]
                    and rep["duplicate_projective_columns"] == 0
                    and rep["base_pair_duplicates"] == 0
                    and rep["support_triple_duplicates"] == 0)
                if arm in M_ARMS:
                    eligible = bool(
                        eligible and merged_extra["m_cycle_rank"] == 0)
                merged["eligible"] = eligible
                merged["window_overflow"] = ov
                merged["determinism_ok"] = replay_ok
                merged["prefix_rows"] = int(k)
                audits.append(merged)
                records.append({
                    "arm": arm, "n": n, "layer": layer, "prefix_rows": int(k),
                    "rank": rep["rank"], "zero_rows": rep["zero_rows"],
                    "zero_columns": rep["zero_columns"],
                    "connected_components": rep["connected_components"],
                    "largest_component_fraction":
                        rep["largest_component_fraction"],
                    "four_cycles": rep["four_cycles"],
                    "four_cycle_variable_incidence_max":
                        rep["four_cycle_variable_incidence_max"],
                    "duplicate_projective_columns":
                        rep["duplicate_projective_columns"],
                    "base_pair_duplicates": rep["base_pair_duplicates"],
                    "support_triple_duplicates":
                        rep["support_triple_duplicates"],
                    "row_degree_max": merged_extra["row_degree_max"],
                    "row_degree_sumsq": merged_extra["row_degree_sumsq"],
                    "girth": (merged_extra["girth"]
                              if merged_extra["girth"] is not None
                              else "NOT_COMPUTED"),
                    "girth_reason": merged_extra["girth_reason"] or "",
                    "m_cycle_rank": (merged_extra["m_cycle_rank"]
                                     if merged_extra["m_cycle_rank"] is not None
                                     else ""),
                    "window_overflow": ov, "eligible": eligible,
                    "determinism_ok": replay_ok})
            summary.setdefault(arm, {})[layer] = {"prefix_audits": audits}
            mothers[(arm, layer)] = np.asarray(H, dtype=np.uint8)
    log("structure n=%d arms=%d records=%d" % (n, len(ARMS), len(records)),
        logfh)
    return records, summary, mothers


def load_prior(model_f_root, logfh):
    npz = np.load(pathlib.Path(model_f_root) / "model_f_input.npz")
    counts0 = np.asarray(npz["counts_ab"], dtype=np.float64)
    pb0 = np.asarray(npz["p_b"], dtype=np.float64)
    pb0 = pb0 / pb0.sum()
    # D6 keeps the current decomposition A = 32*U1 + U2 (identity: no
    # partition transform), E2 total-concentration/backoff candidate.
    pb, pf = d5.prepare_model_f_prior_candidate(counts0, pb0)
    p1 = np.asarray(d5.marginalize_f_to_p1(pf), dtype=np.float64)
    p2 = np.asarray(d5.conditionalize_f_to_p2(pf), dtype=np.float64)
    log("prior E2 identity counts=%s pb=%s LAMBDA_STAR=%s" % (
        counts0.shape, pb0.shape, d5.LAMBDA_STAR), logfh)
    return pb, pf, p1, p2


def run_cell(worker, H1, H2, r1, r2, p1, p2, block, n, meta, state):
    """One frozen cell: L1 + APP-L2 + oracle-L2 (3 counted invocations).
    Returns cell dict with end-to-end APP exact and per-mode records."""
    bob = block["bob"]
    u1t = np.asarray(block["u1"], dtype=np.int64)
    u2t = np.asarray(block["u2"], dtype=np.int64)
    h1 = np.asarray(H1[:r1], dtype=np.uint8)
    h2 = np.asarray(H2[:r2], dtype=np.uint8)
    pr1 = d5._floor_renorm(p1[:, bob].T, d5.DECODER_FLOOR)
    tm1 = float(np.mean(pr1[np.arange(n), u1t]))
    modes = []
    # L1 (beliefs needed for APP propagation; transient IPC only)
    rec = invoke(worker, state, meta, "L1", h1, pr1, u1t, tm1, True)
    modes.append(rec)
    bel = rec.pop("beliefs", None)
    if bel is not None and not rec["crash"]:
        zz = bel - bel.max(axis=1, keepdims=True)
        ee = np.exp(zz)
        q = ee / ee.sum(axis=1, keepdims=True)
    else:
        q = None
    if q is None:
        rec2 = invoke(worker, state, meta, "L2-APP", h2, None, u2t,
                      float("nan"), False, skip=True)
    else:
        pr2 = d5.app_fed_l2_prior(p2, bob, q)
        tm2 = float(np.mean(pr2[np.arange(n), u2t]))
        rec2 = invoke(worker, state, meta, "L2-APP", h2, pr2, u2t, tm2, False)
    modes.append(rec2)
    pr2o = d5.oracle_l2_prior(p2, bob, u1t)
    tmo = float(np.mean(pr2o[np.arange(n), u2t]))
    rec3 = invoke(worker, state, meta, "L2-oracle", h2, pr2o, u2t, tmo, False)
    modes.append(rec3)
    app_exact = bool(modes[0]["exact"] and modes[1]["exact"])
    app_syn = bool(modes[0]["syndrome_ok"] and modes[1]["syndrome_ok"])
    return {"app_exact": app_exact, "app_syndrome_ok": app_syn,
            "disagreement": bool(app_exact != app_syn),
            "iter_total": max(int(modes[0]["iterations"]), 0)
            + max(int(modes[1]["iterations"]), 0),
            "modes": modes}


def invoke(worker, state, meta, mode, h, prior, xt, tm, ret_bel,
           skip=False):
    """Count one budgeted invocation (or a skipped-APP placeholder).

    R1c-A1: call_idx + call/wall budget reserved atomically inside the lock
    before dispatch; the blocking decoder call runs lock-free; the record is
    appended afterwards with the reserved index. Concurrency never exceeds
    2500 total (setup + scientific) / 12 h wall.
    """
    if skip:
        return {"call_idx": -1, "arm": meta["arm"], "n": meta["n"],
                "seed": meta["seed"], "point": meta["point"],
                "rows_l1": meta["r1"], "rows_l2": meta["r2"], "mode": mode,
                "matrix_id": meta["matrix_id"], "exact": False,
                "syndrome_ok": False, "iterations": -1, "finite": False,
                "crash": True, "timeout": False, "prior_mass_on_truth": tm,
                "wall_s": 0.0, "rss_bytes": "", "watchdog_ok": True,
                "worker_pid": "", "note": "app-undefined-l1-unavailable"}
    call_idx = reserve_call_idx(state)
    task = {"h": np.asarray(h, dtype=np.uint8),
            "prior": np.asarray(prior, dtype=np.float64),
            "x_true": np.asarray(xt, dtype=np.int64),
            "return_beliefs": bool(ret_bel)}
    try:
        res = worker.call(task)
    except StopIteration:
        # Setup-budget exhaustion on watchdog respawn: the reserved
        # scientific call still gets a crash row, then STOP propagates.
        lock = state.get("lock")
        if lock is not None:
            lock.acquire()
        try:
            state["budget_stop"] = True
            rec = {"call_idx": call_idx, "arm": meta["arm"], "n": meta["n"],
                   "seed": meta["seed"], "point": meta["point"],
                   "rows_l1": meta["r1"], "rows_l2": meta["r2"], "mode": mode,
                   "matrix_id": meta["matrix_id"], "exact": False,
                   "syndrome_ok": False, "iterations": -1, "finite": False,
                   "crash": True, "timeout": False,
                   "prior_mass_on_truth": tm, "wall_s": 0.0, "rss_bytes": "",
                   "watchdog_ok": True, "worker_pid": worker.pids[-1],
                   "beliefs": None, "note": "setup-budget-exhausted-respawn"}
            state["records"].append(rec)
        finally:
            if lock is not None:
                try:
                    lock.release()
                except RuntimeError:
                    pass
        raise
    rss = res.get("rss")
    wall = float(res.get("wall_s", 0.0))
    rec = {"call_idx": call_idx, "arm": meta["arm"], "n": meta["n"],
           "seed": meta["seed"], "point": meta["point"],
           "rows_l1": meta["r1"], "rows_l2": meta["r2"], "mode": mode,
           "matrix_id": meta["matrix_id"], "exact": bool(res["exact"]),
           "syndrome_ok": bool(res["syndrome_ok"]),
           "iterations": int(res["iterations"]),
           "finite": bool(res["finite"]), "crash": bool(res["crash"]),
           "timeout": bool(res.get("timeout", False)),
           "prior_mass_on_truth": tm, "wall_s": wall,
           "rss_bytes": "" if rss is None else int(rss),
           "watchdog_ok": bool(wall <= WATCHDOG),
           "worker_pid": worker.pids[-1],
           "beliefs": res.get("beliefs")}
    lock = state.get("lock")
    if lock is not None:
        lock.acquire()
    try:
        if rss is not None and rss > state["peak_rss"]:
            state["peak_rss"] = int(rss)
        state["records"].append(rec)
    finally:
        if lock is not None:
            try:
                lock.release()
            except RuntimeError:
                pass
    return rec


def flush_decoder_records(path, records, logfh=None):
    """R1c-A1: rewrite decoder records in frozen call_idx order + flush/fsync."""
    rows = sorted((r for r in records if int(r.get("call_idx", -1)) >= 0),
                  key=lambda r: int(r["call_idx"]))
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=DECODER_FIELDNAMES)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in DECODER_FIELDNAMES})
        fh.flush()
        try:
            os.fsync(fh.fileno())
        except Exception:  # noqa: BLE001
            pass
    if logfh is not None:
        log("flush decoder_records rows=%d" % len(rows), logfh)


def append_structure_records(path, new_records, logfh=None):
    """R1c-A1: append scaling structures (no header rewrite) + flush/fsync."""
    with open(path, "a", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(new_records[0].keys()))
        w.writerows(new_records)
        fh.flush()
        try:
            os.fsync(fh.fileno())
        except Exception:  # noqa: BLE001
            pass
    if logfh is not None:
        log("append structure_records rows=%d" % len(new_records), logfh)


def note_chunk_wall(phase, wall, logfh, state):
    """R1c-A1: per-chunk wall check; >=5400s is BLOCKED (not warning-only)."""
    ok = bool(float(wall) < R1C_CHUNK_WALL_MAX)
    log("r1c chunk %s wall=%.1f chunk_ok=%s" % (phase, float(wall), ok),
        logfh)
    if not ok:
        state["chunk_wall_blocked"] = True
        state["budget_stop"] = True
        log("BLOCKED chunk-wall %s wall=%.1f >= %d"
            % (phase, float(wall), R1C_CHUNK_WALL_MAX), logfh)
    return ok


def run_cells_parallel(cell_specs, state, logfh, pool_q, max_workers):
    """R1c: cells parallel across worker pool; intra-cell L1→APP sequential.

    cell_specs: list of (H1,H2,r1,r2,p1,p2,block,n,meta) in frozen order.
    Main-thread samples are read-only. Returns (cells, wall) with cells in
    input order. Chunk wall >= 5400 s is BLOCKED (caller sets the blocking
    terminal and stops further dispatch).
    """
    t0 = time.perf_counter()
    cells = [None] * len(cell_specs)

    def _one(idx):
        H1, H2, r1, r2, p1, p2, block, n, meta = cell_specs[idx]
        w = pool_q.get()
        try:
            return run_cell(w, H1, H2, r1, r2, p1, p2, block, n, meta, state)
        finally:
            pool_q.put(w)

    with concurrent.futures.ThreadPoolExecutor(
            max_workers=int(max_workers)) as ex:
        futs = {ex.submit(_one, i): i for i in range(len(cell_specs))}
        for fut in concurrent.futures.as_completed(futs):
            i = futs[fut]
            cells[i] = fut.result()
    wall = time.perf_counter() - t0
    log("r1c chunk cells=%d workers=%d wall=%.1f" % (
        len(cell_specs), int(max_workers), wall), logfh)
    if wall >= R1C_CHUNK_WALL_MAX:
        log("r1c chunk wall exceeds 1.5h", logfh)
    return cells, wall


def tally_safety(cell, safety):
    """Accumulate confirmation safety from one cell's counted invocations."""
    counted = [m for m in cell["modes"] if int(m["call_idx"]) >= 0]
    safety["crashes"] += int(any(m["crash"] for m in counted))
    safety["nonfinite"] += int(any(
        not m["finite"] and not m["crash"] for m in counted))
    safety["disagreements"] += int(cell["disagreement"])
    for m in counted:
        if m["rss_bytes"] == "" or int(m["rss_bytes"]) >= RSS_CEIL:
            safety["rss_known_ok"] = False


def verify_command(out_root):
    """Independent scalar recomputation from saved evidence (T12)."""
    out = pathlib.Path(out_root)
    ok = True

    def check(name, cond, detail=""):
        nonlocal ok
        print("%s %s %s" % ("PASS" if cond else "FAIL", name, detail))
        if not cond:
            ok = False
    sel = json.loads((out / "selected_arms.json").read_text(encoding="utf-8"))
    summ = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    with open(out / "decoder_records.csv", newline="", encoding="utf-8") as fh:
        recs = list(csv.DictReader(fh))
    with open(out / "structure_records.csv", newline="", encoding="utf-8") as fh:
        srecs = list(csv.DictReader(fh))
    check("six-files", all((out / f).exists() for f in (
        "manifest.json", "structure_records.csv", "selected_arms.json",
        "decoder_records.csv", "summary.json", "command_log.txt")))
    check("decoder-set-le-6", len(sel["selected"]) <= 6, str(sel["selected"]))
    check("b0-in-set", "B0_D5_DV3_NATIVE" in sel["selected"])
    counted = [r for r in recs if int(r["call_idx"]) >= 0]
    setup_calls = int(summ.get("setup_decoder_calls", 0))
    check("call-count",
          len(counted) == int(summ["calls"]) and len(counted) <= 2500,
          "csv=%d summary=%d" % (len(counted), summ["calls"]))
    check("setup-plus-scientific-le-2500",
          len(counted) + setup_calls <= 2500,
          "scientific=%d setup=%d" % (len(counted), setup_calls))
    check("no-retry-cells",
          len({(r["arm"], r["seed"], r["point"], r["mode"]) for r in counted})
          == len(counted))
    check("watchdog", all(r["watchdog_ok"] == "True" for r in counted))
    # exact/syndrome/oracle separation: oracle rows never feed APP exact;
    # recompute canary APP-exact counts from L1+L2-APP rows only.
    by_cell = {}
    for r in counted:
        by_cell.setdefault(
            (r["arm"], r["seed"], r["point"]), {})[r["mode"]] = r
    canary_re = {}
    for (arm, seed, point), modes in by_cell.items():
        if int(seed) not in list(CANARY_SEEDS) + list(SCALING_SEEDS):
            continue
        if "L1" in modes and "L2-APP" in modes:
            app = bool(modes["L1"]["exact"] == "True"
                       and modes["L2-APP"]["exact"] == "True")
            d = canary_re.setdefault(
                arm, {"f12_exact": 0, "sq_exact": 0})
            if point == "f1.2":
                d["f12_exact"] += int(app)
            elif point == "square":
                d["sq_exact"] += int(app)
    summ_can = {a: {"f12_exact": v["f12_exact"], "sq_exact": v["sq_exact"]}
                for a, v in summ["canary"].items()}
    check("canary-replay", canary_re == summ_can, str(canary_re))
    itmax = max([int(r["iterations"]) for r in counted] or [0])
    check("iterations-max", itmax == int(summ["iterations_max"]),
          str(itmax))
    # advancement replay
    can = summ["canary"]
    stats = {a: {"f12_exact": v["f12_exact"], "f12_iter": v["f12_iter"],
                 "sq_exact": v["sq_exact"]} for a, v in can.items()}
    sys.path.insert(0, str(ROOT / "comparison_bench" / "src"))
    from comparison_bench.formal_ir.v72p2d6_gf32_graph_mother import (
        select_advancement as _adv, classify_terminal as _cls)
    check("advancement-replay",
          _adv(stats, sel["structural_order_new"]) == summ["advancing"],
          str(summ["advancing"]))
    per_f = [{"exact": summ["confirmation_counts"][a][p]}
             for a in summ["advancing"][:1] for p in POINTS] \
        if summ.get("advancing") and summ.get("confirmation_counts") else None
    if str(summ.get("terminal", "")) == R1C_CHUNK_WALL_BLOCKED_TERMINAL:
        check("terminal-blocked", bool(summ.get("chunk_wall_blocked", False)),
              str(summ.get("terminal")))
    elif per_f is not None and len(summ["advancing"]) == 1 \
            and "SCALING" not in str(summ.get("terminal", "")) \
            and int(summ.get("confirmation_width", 64)) == 64:
        a = summ["advancing"][0]
        c = summ["confirmation_counts"][a]
        rep = _cls([{"exact": c[p]} for p in POINTS],
                   summ["confirmation_safety"]["crashes"],
                   summ["confirmation_safety"]["nonfinite"],
                   summ["confirmation_safety"]["rss_known_ok"],
                   summ["confirmation_safety"]["disagreements"])
        check("terminal-replay", rep == summ["terminal"], rep)
    print("VERIFY %s" % ("PASS" if ok else "FAIL"))
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-f-root", required=False)
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--dry-structure", action="store_true")
    ap.add_argument("--verify", action="store_true")
    # R1c: parallel mechanics only; 1 = sequential fallback for tests.
    ap.add_argument("--workers", type=int, default=18,
                    choices=(18, 14, 12, 8, 1),
                    help="R1c decoder/structure workers (18 full, else RSS-gated)")
    args = ap.parse_args(argv)
    if args.verify:
        sys.exit(0 if verify_command(args.out_root) else 1)
    if not args.model_f_root:
        ap.error("--model-f-root is required (no formal default)")
    out = pathlib.Path(args.out_root)
    assert_no_formal_write(str(out))
    if out.exists():
        print("refusing to overwrite %s" % out, file=sys.stderr)
        sys.exit(2)
    out.mkdir(parents=True)
    logfh = open(out / "command_log.txt", "w", encoding="utf-8")
    state = {"calls": 0, "setup_calls": 0, "t0": time.perf_counter(),
             "records": [], "peak_rss": 0, "budget_stop": False,
             "chunk_wall_blocked": False, "chunk_walls": {}, "worker": None,
             "lock": threading.Lock(), "revision": R1C_REVISION}
    # R1c-A1 worker choice: requested is a hard ceiling; effective is gated
    # by measured startup RSS after spawning (pool + main aggregate recorded).
    req_workers = int(args.workers)
    workers = req_workers
    main_rss = None
    worker_rss_list = []
    rss_info = {"requested": req_workers, "effective": req_workers,
                "main_rss_bytes": None, "worker_rss_bytes": [],
                "aggregate_rss_bytes": None}
    log("r1c-a1 workers requested=%d revision=%s" % (req_workers,
                                                    R1C_REVISION), logfh)
    try:
        # T9: structure + blind freeze (no decoder before this freeze).
        if workers == 1:
            records, summary, mothers = build_structures(64, logfh)
        else:
            records, summary, mothers = build_structures_parallel(
                64, logfh, max_workers=workers)
        write_structure_records(out / "structure_records.csv", records)
        selected, eligible = select_decoder_arms(summary)
        order_new = structural_rank_list(
            summary, [a for a in selected if a in T_ARMS + M_ARMS])
        fallbacks = {"best_T": next((a for a in order_new if a in T_ARMS),
                                    None),
                     "best_M": next((a for a in order_new if a in M_ARMS),
                                    None)}
        with open(out / "selected_arms.json", "w", encoding="utf-8") as fh:
            json.dump({"selected": selected, "eligible": eligible,
                       "fallback_T": fallbacks["best_T"],
                       "fallback_M": fallbacks["best_M"],
                       "structural_order_new": order_new,
                       "freeze": "decoder-blind-from-structure-only"},
                      fh, indent=2, sort_keys=True)
        log("selected=%s fallbacks=%s" % (selected, fallbacks), logfh)
        if args.dry_structure:
            with open(out / "manifest.json", "w",
                       encoding="utf-8") as fh:
                json.dump({"out_root": str(out), "arms": ARMS,
                           "mode": "dry-structure"}, fh, indent=2)
            with open(out / "decoder_records.csv", "w",
                       encoding="utf-8") as fh:
                fh.write("arm,seed,point,exact\n")
            with open(out / "summary.json", "w", encoding="utf-8") as fh:
                json.dump({"selected": selected, "records": len(records)},
                          fh, indent=2)
            log("dry-structure done", logfh)
            return
        # §8 execution.
        pb, pf, p1, p2 = load_prior(args.model_f_root, logfh)
        blocks = {}

        def get_block(n, seed):
            key = (int(n), int(seed))
            if key not in blocks:
                blk = d5.sample_matched_block(pb, pf, int(n), int(seed))
                if key == (64, int(CANARY_SEEDS[0])):
                    assert bool(np.array_equal(
                        32 * np.asarray(blk["u1"])
                        + np.asarray(blk["u2"]), np.asarray(blk["alice"])))
                blocks[key] = blk
            return blocks[key]
        if req_workers == 1:
            workers = 1
            worker = Worker(logfh, state)
            state["worker"] = worker
            pool_q = None
            pool_workers = [worker]
            try:
                main_rss = d5._rss_bytes()
            except Exception:  # noqa: BLE001
                main_rss = None
            worker_rss_list = [worker.last_rss]
            rss_info = {"requested": 1, "effective": 1,
                        "main_rss_bytes": main_rss,
                        "worker_rss_bytes": list(worker_rss_list),
                        "aggregate_rss_bytes": pool_aggregate_rss(
                            worker_rss_list, main_rss)}
            log("r1c-a1 workers requested=1 effective=1 main_rss=%s "
                "worker_rss=%s aggregate=%s setup=%d"
                % (str(main_rss), str(worker_rss_list),
                   str(rss_info["aggregate_rss_bytes"]),
                   int(state.get("setup_calls", 0))), logfh)
        else:
            # R1c-A1: main-process single-thread sample gen, then read-only
            # share; pool sized by measured startup RSS, never above request.
            # 120 s watchdog per worker retained, no retry.
            cand = []
            try:
                for _ in range(req_workers):
                    cand.append(Worker(logfh, state))
            except StopIteration as ex:
                log("STOP setup-budget %s" % ex, logfh)
            try:
                main_rss = d5._rss_bytes()
            except Exception:  # noqa: BLE001
                main_rss = None
            worker_rss_list = [w.last_rss for w in cand]
            workers = select_effective_workers(req_workers, worker_rss_list,
                                               main_rss, logfh)
            for extra in cand[workers:]:
                try:
                    extra.stop()
                except Exception:  # noqa: BLE001
                    pass
            pool_workers = cand[:workers]
            if not pool_workers:
                raise RuntimeError("no workers after setup-budget gate")
            pool_q = queue.Queue()
            for _w in pool_workers:
                pool_q.put(_w)
            state["worker"] = pool_workers[0]
            state["pool"] = pool_workers
            state["pool_q"] = pool_q
            rss_info = {"requested": req_workers, "effective": workers,
                        "main_rss_bytes": main_rss,
                        "worker_rss_bytes": [w.last_rss
                                             for w in pool_workers],
                        "aggregate_rss_bytes": pool_aggregate_rss(
                            [w.last_rss for w in pool_workers], main_rss)}
            log("r1c-a1 workers requested=%d effective=%d main_rss=%s "
                "worker_rss=%s aggregate=%s setup=%d"
                % (req_workers, workers, str(main_rss),
                   str(rss_info["worker_rss_bytes"]),
                   str(rss_info["aggregate_rss_bytes"]),
                   int(state.get("setup_calls", 0))), logfh)
        finalists = [a for a in selected if a in T_ARMS + M_ARMS]
        # Canary §8.2: frozen set x 4 seeds x {f1.2, square}.
        canary = {}
        if workers == 1:
            _t0 = time.perf_counter()
            try:
                for arm in selected:
                    H1 = mothers[(arm, "L1")]
                    H2 = mothers[(arm, "L2")]
                    f12 = {"f12_exact": 0, "f12_iter": 0, "sq_exact": 0}
                    for seed in CANARY_SEEDS:
                        blk = get_block(64, seed)
                        for point, (r1, r2) in (
                                ("f1.2", (59, 52)), ("square", (64, 64))):
                            meta = {"arm": arm, "n": 64, "seed": int(seed),
                                    "point": point, "r1": r1, "r2": r2,
                                    "matrix_id": "%s|n64|L1k%d/L2k%d" % (
                                        arm, r1, r2)}
                            cell = run_cell(worker, H1, H2, r1, r2, p1, p2,
                                            blk, 64, meta, state)
                            if point == "f1.2":
                                f12["f12_exact"] += int(cell["app_exact"])
                                f12["f12_iter"] += int(cell["iter_total"])
                            else:
                                f12["sq_exact"] += int(cell["app_exact"])
                    canary[arm] = f12
                log("canary done advancing-pool=%s" % {
                    a: canary[a] for a in finalists}, logfh)
            except StopIteration as ex:
                log("STOP %s" % ex, logfh)
            _wall = time.perf_counter() - _t0
            flush_decoder_records(out / "decoder_records.csv",
                                  state["records"], logfh)
            state["chunk_walls"]["canary"] = float(_wall)
            note_chunk_wall("canary", _wall, logfh, state)
        else:
            # R1c parallel canary: single-thread pregen, then cells parallel,
            # one chunk (<1.5 h), same tallies.
            try:
                for _s in CANARY_SEEDS:
                    get_block(64, _s)
                specs = []
                order = []
                for arm in selected:
                    H1 = mothers[(arm, "L1")]
                    H2 = mothers[(arm, "L2")]
                    for seed in CANARY_SEEDS:
                        blk = get_block(64, seed)
                        for point, (r1, r2) in (
                                ("f1.2", (59, 52)), ("square", (64, 64))):
                            meta = {"arm": arm, "n": 64, "seed": int(seed),
                                    "point": point, "r1": r1, "r2": r2,
                                    "matrix_id": "%s|n64|L1k%d/L2k%d" % (
                                        arm, r1, r2)}
                            specs.append((H1, H2, r1, r2, p1, p2,
                                          blk, 64, meta))
                            order.append((arm, point))
                _t0 = time.perf_counter()
                cells, _wall = run_cells_parallel(specs, state, logfh, pool_q,
                                                  workers)
                _wall2 = time.perf_counter() - _t0
                wall = max(float(_wall), float(_wall2))
                state["chunk_walls"]["canary"] = float(wall)
                note_chunk_wall("canary", wall, logfh, state)
                flush_decoder_records(out / "decoder_records.csv",
                                      state["records"], logfh)
                log("canary-parallel wall=%.1f chunk_ok=%s" % (
                    wall, bool(wall < R1C_CHUNK_WALL_MAX)), logfh)
                tmp = {a: {"f12_exact": 0, "f12_iter": 0, "sq_exact": 0}
                       for a in selected}
                for (arm, point), cell in zip(order, cells):
                    if point == "f1.2":
                        tmp[arm]["f12_exact"] += int(cell["app_exact"])
                        tmp[arm]["f12_iter"] += int(cell["iter_total"])
                    else:
                        tmp[arm]["sq_exact"] += int(cell["app_exact"])
                canary = tmp
                log("canary done advancing-pool=%s" % {
                    a: canary[a] for a in finalists}, logfh)
            except StopIteration as ex:
                log("STOP %s" % ex, logfh)
        pool_stats = {a: canary[a] for a in finalists if a in canary}
        advancing = select_advancement(pool_stats, order_new)
        log("advancing=%s" % advancing, logfh)
        terminal = None
        conf_counts = {}
        conf_safety = {"crashes": 0, "nonfinite": 0, "disagreements": 0,
                       "rss_known_ok": True}
        width = 64
        if advancing:
            # Confirmation §8.3 at n=64.
            if workers == 1:
                try:
                    for arm in advancing:
                        _t0 = time.perf_counter()
                        H1 = mothers[(arm, "L1")]
                        H2 = mothers[(arm, "L2")]
                        cc = {}
                        for point, (r1, r2) in (
                                ("f1.0", (49, 43)), ("f1.2", (59, 52)),
                                ("square", (64, 64))):
                            ex = 0
                            for seed in CONF_SEEDS:
                                blk = get_block(64, seed)
                                meta = {"arm": arm, "n": 64, "seed": int(seed),
                                        "point": point, "r1": r1, "r2": r2,
                                        "matrix_id": "%s|n64|L1k%d/L2k%d" % (
                                            arm, r1, r2)}
                                cell = run_cell(worker, H1, H2, r1, r2, p1, p2,
                                                blk, 64, meta, state)
                                ex += int(cell["app_exact"])
                                tally_safety(cell, conf_safety)
                            cc[point] = ex
                        conf_counts[arm] = cc
                        _wall = time.perf_counter() - _t0
                        state["chunk_walls"]["confirmation-%s" % arm] = float(
                            _wall)
                        note_chunk_wall("confirmation-%s" % arm, _wall,
                                        logfh, state)
                        flush_decoder_records(out / "decoder_records.csv",
                                              state["records"], logfh)
                        if state.get("chunk_wall_blocked"):
                            break
                    log("confirmation=%s safety=%s" % (
                        conf_counts, conf_safety), logfh)
                except StopIteration as ex:
                    log("STOP %s" % ex, logfh)
                    flush_decoder_records(out / "decoder_records.csv",
                                          state["records"], logfh)
            else:
                # R1c parallel confirmation: pregen then chunks per arm.
                try:
                    for _s in CONF_SEEDS:
                        get_block(64, _s)
                    for arm in advancing:
                        if state.get("chunk_wall_blocked"):
                            break
                        H1 = mothers[(arm, "L1")]
                        H2 = mothers[(arm, "L2")]
                        specs = []
                        order = []
                        for point, (r1, r2) in (
                                ("f1.0", (49, 43)), ("f1.2", (59, 52)),
                                ("square", (64, 64))):
                            for seed in CONF_SEEDS:
                                blk = get_block(64, seed)
                                meta = {"arm": arm, "n": 64,
                                        "seed": int(seed), "point": point,
                                        "r1": r1, "r2": r2,
                                        "matrix_id": "%s|n64|L1k%d/L2k%d" % (
                                            arm, r1, r2)}
                                specs.append((H1, H2, r1, r2, p1, p2,
                                              blk, 64, meta))
                                order.append(point)
                        cells, _wall = run_cells_parallel(specs, state, logfh,
                                                          pool_q, workers)
                        state["chunk_walls"]["confirmation-%s" % arm] = float(
                            _wall)
                        note_chunk_wall("confirmation-%s" % arm, _wall,
                                        logfh, state)
                        flush_decoder_records(out / "decoder_records.csv",
                                              state["records"], logfh)
                        cc = {}
                        idx = 0
                        for point, (r1, r2) in (
                                ("f1.0", (49, 43)), ("f1.2", (59, 52)),
                                ("square", (64, 64))):
                            ex = 0
                            for _ in CONF_SEEDS:
                                cell = cells[idx]
                                idx += 1
                                ex += int(cell["app_exact"])
                                tally_safety(cell, conf_safety)
                            cc[point] = ex
                        conf_counts[arm] = cc
                    log("confirmation=%s safety=%s" % (
                        conf_counts, conf_safety), logfh)
                except StopIteration as ex:
                    log("STOP %s" % ex, logfh)
                    flush_decoder_records(out / "decoder_records.csv",
                                          state["records"], logfh)
            a0 = advancing[0]
            c0 = conf_counts.get(a0, {})
            per_f = [{"exact": c0.get(p, 0)} for p in POINTS]
            terminal = classify_terminal(
                per_f, conf_safety["crashes"], conf_safety["nonfinite"],
                conf_safety["rss_known_ok"], conf_safety["disagreements"])
        else:
            # Scaling branch §8.4: fallbacks only, stop at first signal.
            fb = [x for x in (fallbacks["best_T"], fallbacks["best_M"])
                  if x is not None]
            for n in (128, 256):
                if state.get("chunk_wall_blocked"):
                    break
                if workers == 1:
                    srec, ssum, smothers = build_structures(n, logfh)
                else:
                    srec, ssum, smothers = build_structures_parallel(
                        n, logfh, max_workers=workers)
                append_structure_records(out / "structure_records.csv", srec,
                                         logfh)
                order_n = structural_rank_list(ssum, fb)
                sig = {}
                if workers == 1:
                    _t0 = time.perf_counter()
                    try:
                        for arm in fb:
                            H1 = smothers[(arm, "L1")]
                            H2 = smothers[(arm, "L2")]
                            f12 = {"f12_exact": 0, "f12_iter": 0, "sq_exact": 0}
                            pre = ROW_BUDGETS[n]
                            for seed in SCALING_SEEDS:
                                blk = get_block(n, seed)
                                for point in ("f1.2", "square"):
                                    r1 = pre["L1"][1] if point == "f1.2" \
                                        else pre["L1"][2]
                                    r2 = pre["L2"][1] if point == "f1.2" \
                                        else pre["L2"][2]
                                    meta = {"arm": arm, "n": n,
                                            "seed": int(seed), "point": point,
                                            "r1": r1, "r2": r2,
                                            "matrix_id": "%s|n%d|L1k%d/L2k%d"
                                            % (arm, n, r1, r2)}
                                    cell = run_cell(worker, H1, H2, r1, r2,
                                                    p1, p2, blk, n, meta, state)
                                    if point == "f1.2":
                                        f12["f12_exact"] += int(cell["app_exact"])
                                        f12["f12_iter"] += int(cell["iter_total"])
                                    else:
                                        f12["sq_exact"] += int(
                                            cell["app_exact"])
                            sig[arm] = f12
                        log("scaling n=%d %s" % (n, sig), logfh)
                    except StopIteration as ex:
                        log("STOP %s" % ex, logfh)
                        flush_decoder_records(out / "decoder_records.csv",
                                              state["records"], logfh)
                    _wall = time.perf_counter() - _t0
                    state["chunk_walls"]["scaling-n%d-canary" % n] = float(
                        _wall)
                    note_chunk_wall("scaling-n%d-canary" % n, _wall, logfh,
                                    state)
                    flush_decoder_records(out / "decoder_records.csv",
                                          state["records"], logfh)
                else:
                    # R1c parallel scaling canary: pregen then parallel.
                    try:
                        for _s in SCALING_SEEDS:
                            get_block(n, _s)
                        specs = []
                        order = []
                        for arm in fb:
                            H1 = smothers[(arm, "L1")]
                            H2 = smothers[(arm, "L2")]
                            pre = ROW_BUDGETS[n]
                            for seed in SCALING_SEEDS:
                                blk = get_block(n, seed)
                                for point in ("f1.2", "square"):
                                    r1 = pre["L1"][1] if point == "f1.2" \
                                        else pre["L1"][2]
                                    r2 = pre["L2"][1] if point == "f1.2" \
                                        else pre["L2"][2]
                                    meta = {"arm": arm, "n": n,
                                            "seed": int(seed), "point": point,
                                            "r1": r1, "r2": r2,
                                            "matrix_id": "%s|n%d|L1k%d/L2k%d"
                                            % (arm, n, r1, r2)}
                                    specs.append((H1, H2, r1, r2, p1, p2,
                                                  blk, n, meta))
                                    order.append((arm, point))
                        cells, _wall = run_cells_parallel(specs, state, logfh,
                                                          pool_q, workers)
                        state["chunk_walls"]["scaling-n%d-canary" % n] = float(
                            _wall)
                        note_chunk_wall("scaling-n%d-canary" % n, _wall,
                                        logfh, state)
                        flush_decoder_records(out / "decoder_records.csv",
                                              state["records"], logfh)
                        tmp = {a: {"f12_exact": 0, "f12_iter": 0,
                                   "sq_exact": 0} for a in fb}
                        for (arm, point), cell in zip(order, cells):
                            if point == "f1.2":
                                tmp[arm]["f12_exact"] += int(cell["app_exact"])
                                tmp[arm]["f12_iter"] += int(cell["iter_total"])
                            else:
                                tmp[arm]["sq_exact"] += int(cell["app_exact"])
                        sig = tmp
                        log("scaling n=%d %s" % (n, sig), logfh)
                    except StopIteration as ex:
                        log("STOP %s" % ex, logfh)
                        flush_decoder_records(out / "decoder_records.csv",
                                              state["records"], logfh)
                advancing = select_advancement(sig, order_n)
                if state.get("chunk_wall_blocked"):
                    break
                if advancing:
                    width = n
                    if workers == 1:
                        try:
                            for arm in advancing:
                                if state.get("chunk_wall_blocked"):
                                    break
                                _t0 = time.perf_counter()
                                H1 = smothers[(arm, "L1")]
                                H2 = smothers[(arm, "L2")]
                                pre = ROW_BUDGETS[n]
                                cc = {}
                                for point, idx in (("f1.0", 0), ("f1.2", 1),
                                                   ("square", 2)):
                                    r1, r2 = pre["L1"][idx], pre["L2"][idx]
                                    ex = 0
                                    for seed in CONF_SEEDS:
                                        blk = get_block(n, seed)
                                        meta = {"arm": arm, "n": n,
                                                "seed": int(seed), "point": point,
                                                "r1": r1, "r2": r2,
                                                "matrix_id":
                                                "%s|n%d|L1k%d/L2k%d"
                                                % (arm, n, r1, r2)}
                                        cell = run_cell(worker, H1, H2, r1, r2,
                                                        p1, p2, blk, n, meta,
                                                        state)
                                        ex += int(cell["app_exact"])
                                        tally_safety(cell, conf_safety)
                                cc[point] = ex
                                conf_counts[arm] = cc
                                _wall = time.perf_counter() - _t0
                                state["chunk_walls"][
                                    "scaling-n%d-confirmation-%s" % (n, arm)] \
                                    = float(_wall)
                                note_chunk_wall(
                                    "scaling-n%d-confirmation-%s" % (n, arm),
                                    _wall, logfh, state)
                                flush_decoder_records(
                                    out / "decoder_records.csv",
                                    state["records"], logfh)
                        except StopIteration as ex:
                            log("STOP %s" % ex, logfh)
                            flush_decoder_records(
                                out / "decoder_records.csv",
                                state["records"], logfh)
                    else:
                        # R1c parallel scaling confirmation.
                        try:
                            for _s in CONF_SEEDS:
                                get_block(n, _s)
                            for arm in advancing:
                                if state.get("chunk_wall_blocked"):
                                    break
                                H1 = smothers[(arm, "L1")]
                                H2 = smothers[(arm, "L2")]
                                pre = ROW_BUDGETS[n]
                                specs = []
                                order = []
                                for point, idx in (("f1.0", 0), ("f1.2", 1),
                                                   ("square", 2)):
                                    r1, r2 = pre["L1"][idx], pre["L2"][idx]
                                    for seed in CONF_SEEDS:
                                        blk = get_block(n, seed)
                                        meta = {"arm": arm, "n": n,
                                                "seed": int(seed),
                                                "point": point,
                                                "r1": r1, "r2": r2,
                                                "matrix_id":
                                                "%s|n%d|L1k%d/L2k%d"
                                                % (arm, n, r1, r2)}
                                        specs.append((H1, H2, r1, r2, p1, p2,
                                                      blk, n, meta))
                                        order.append(point)
                                cells, _wall = run_cells_parallel(
                                    specs, state, logfh, pool_q, workers)
                                state["chunk_walls"][
                                    "scaling-n%d-confirmation-%s" % (n, arm)] \
                                    = float(_wall)
                                note_chunk_wall(
                                    "scaling-n%d-confirmation-%s" % (n, arm),
                                    _wall, logfh, state)
                                flush_decoder_records(
                                    out / "decoder_records.csv",
                                    state["records"], logfh)
                                cc = {}
                                idx = 0
                                for point, _ in (("f1.0", 0), ("f1.2", 1),
                                                 ("square", 2)):
                                    ex = 0
                                    for _ in CONF_SEEDS:
                                        cell = cells[idx]
                                        idx += 1
                                        ex += int(cell["app_exact"])
                                        tally_safety(cell, conf_safety)
                                    cc[point] = ex
                                conf_counts[arm] = cc
                        except StopIteration as ex:
                            log("STOP %s" % ex, logfh)
                            flush_decoder_records(
                                out / "decoder_records.csv",
                                state["records"], logfh)
                    a0 = advancing[0]
                    c0 = conf_counts.get(a0, {})
                    per_f = [{"exact": c0.get(p, 0)} for p in POINTS]
                    base = classify_terminal(
                        per_f, conf_safety["crashes"],
                        conf_safety["nonfinite"],
                        conf_safety["rss_known_ok"],
                        conf_safety["disagreements"])
                    terminal = base.replace("N64", "SCALING-n%d" % n)
                    break
            if terminal is None:
                terminal = "D6_GRAPH_TOPOLOGY_NO_USEFUL_RECOVERY"
        if terminal is None:
            terminal = "D6_GRAPH_TOPOLOGY_NO_USEFUL_RECOVERY"
        if state.get("chunk_wall_blocked"):
            terminal = R1C_CHUNK_WALL_BLOCKED_TERMINAL
            log("terminal-overridden chunk-wall-blocked", logfh)
        itmax = max([int(r["iterations"]) for r in state["records"]
                     if int(r["call_idx"]) >= 0] or [0])
        if workers == 1:
            worker.stop()
            all_pids = list(worker.pids)
        else:
            for _w in pool_workers:
                try:
                    _w.stop()
                except Exception:  # noqa: BLE001
                    pass
            all_pids = [p for _w in pool_workers for p in _w.pids]
        flush_decoder_records(out / "decoder_records.csv", state["records"],
                              logfh)
        try:
            head = subprocess.run(
                ["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                cwd=str(ROOT)).stdout.strip()
        except Exception:  # noqa: BLE001
            head = "unknown"
        wall = time.perf_counter() - state["t0"]
        setup_calls = int(state.get("setup_calls", 0))
        sci_calls = int(state.get("calls", 0))
        with open(out / "manifest.json", "w", encoding="utf-8") as fh:
            json.dump({"out_root": str(out), "arms": ARMS,
                       "revision": R1C_REVISION, "workers": workers,
                       "workers_requested": req_workers,
                       "workers_effective": workers,
                       "main_rss_bytes": main_rss,
                       "worker_rss_bytes": rss_info.get(
                           "worker_rss_bytes", []),
                       "aggregate_rss_bytes": rss_info.get(
                           "aggregate_rss_bytes"),
                       "chunk_wall_max_s": R1C_CHUNK_WALL_MAX,
                       "chunk_walls": state.get("chunk_walls", {}),
                       "chunk_wall_blocked": bool(state.get(
                           "chunk_wall_blocked", False)),
                       "canary_seeds": list(CANARY_SEEDS),
                       "confirmation_seeds": list(CONF_SEEDS),
                       "scaling_seeds": list(SCALING_SEEDS),
                       "budgets": {"calls": CALL_BUDGET,
                                   "wall_s": WALL_BUDGET,
                                   "watchdog_s": WATCHDOG,
                                   "rss_bytes": RSS_CEIL},
                       "calls": sci_calls, "setup_decoder_calls": setup_calls,
                       "scientific_calls": sci_calls,
                       "total_decoder_calls": setup_calls + sci_calls,
                       "wall_s": wall,
                       "peak_rss_bytes": state["peak_rss"],
                       "worker_pids": all_pids,
                       "head_sha": head,
                       "budget_stop": state["budget_stop"],
                       "oracle_never_upgrades_exact": True}, fh, indent=2)
        with open(out / "summary.json", "w", encoding="utf-8") as fh:
            json.dump({"selected": selected, "canary": canary,
                       "revision": R1C_REVISION, "workers": workers,
                       "workers_requested": req_workers,
                       "workers_effective": workers,
                       "setup_decoder_calls": setup_calls,
                       "scientific_calls": sci_calls,
                       "total_decoder_calls": setup_calls + sci_calls,
                       "chunk_walls": state.get("chunk_walls", {}),
                       "chunk_wall_blocked": bool(state.get(
                           "chunk_wall_blocked", False)),
                       "advancing": advancing,
                       "confirmation_counts": conf_counts,
                       "confirmation_safety": conf_safety,
                       "confirmation_width": width, "terminal": terminal,
                       "calls": sci_calls, "wall_s": wall,
                       "iterations_max": itmax,
                       "peak_rss_bytes": state["peak_rss"],
                       "budget_stop": state["budget_stop"],
                       "oracle_never_upgrades_exact": True}, fh, indent=2)
        log("done terminal=%s calls=%d setup=%d wall=%.1f peak_rss=%d" % (
            terminal, sci_calls, setup_calls, wall, state["peak_rss"]),
            logfh)
    finally:
        try:
            for _w in state.get("pool", [state.get("worker")] if state.get("worker") is not None else []):
                try:
                    if _w is not None:
                        _w.stop()
                except Exception:  # noqa: BLE001
                    pass
        except Exception:  # noqa: BLE001
            pass
        logfh.close()


if __name__ == "__main__":
    mp.freeze_support()
    main()

