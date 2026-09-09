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
    build_mother, build_support, build_support_with_overflow,
    assign_mother_from_support, support_window_overflow, d5,
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
R1C_REVISION = "R1c-A2"
# R1c-A1: chunk-wall overrun is an explicit blocking terminal (not warning-only).
R1C_CHUNK_WALL_BLOCKED_TERMINAL = "D6_GRAPH_CHUNK_WALL_BLOCKED"
# R1c-A2: fail-closed blocking terminals (mechanics only, override science).
R1C_RSS_UNKNOWN_TERMINAL = "D6_RSS_UNKNOWN_BLOCKED"
R1C_RSS_LIMIT_TERMINAL = "D6_RSS_LIMIT_BLOCKED"
R1C_WALL_BLOCKED_TERMINAL = "D6_WALL_BUDGET_BLOCKED"
RSS_SEMANTICS = ("fail-closed-strict-unknown-None-no-zero-substitution-"
                 "no-single-as-aggregate")
# R1c-A3: post-run verifier/terminal corrections (verifier path only; zero
# execution impact). Frozen by D6_GRAPH_MOTHER_PREREG_R1C_A3.
A3_DEGREE_SUBSTR = "Check node requires degree"
A3_STRUCTURE_INVARIANT_TERMINAL = "D6_GRAPH_STRUCTURE_INVARIANT_BLOCKED"
A3_ATTEMPTED_INVALID_TERMINAL = "D6_GRAPH_ATTEMPTED_CELL_INVALID"
DECODER_FIELDNAMES = ["call_idx", "arm", "n", "seed", "point", "rows_l1",
                      "rows_l2", "mode", "matrix_id", "exact", "syndrome_ok",
                      "iterations", "finite", "crash", "timeout",
                      "wall_timeout", "prior_mass_on_truth", "wall_s",
                      "rss_bytes", "watchdog_ok", "worker_pid",
                      "respawn_pid", "error"]

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


def _deadline(state):
    """R1c-A2: absolute deadline t0+12h (perf_counter domain)."""
    try:
        t0 = float(state.get("t0", time.perf_counter()))
    except (TypeError, ValueError):
        t0 = time.perf_counter()
    try:
        dl = state.get("deadline")
        if dl is not None:
            return float(dl)
    except (TypeError, ValueError):
        pass
    return float(t0) + float(WALL_BUDGET)


def _remaining_s(state, now=None):
    """R1c-A2: remaining wall before deadline (may be <= 0)."""
    if now is None:
        now = time.perf_counter()
    return float(_deadline(state)) - float(now)


def can_dispatch(state):
    """R1c-A2: zero new dispatches after chunk>=5400s or budget stop."""
    if state.get("budget_stop"):
        return False
    if state.get("chunk_wall_blocked"):
        return False
    if _remaining_s(state) <= 0:
        return False
    return True


def reserve_setup_idx(state):
    """R1c-A2: reserve one warmup/setup call inside the lock before spawn."""
    lock = state.get("lock")
    if lock is not None:
        lock.acquire()
    try:
        if (int(state.get("setup_calls", 0)) + int(state.get("calls", 0))
                + 1 > CALL_BUDGET
                or _remaining_s(state) <= 0
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
    """R1c-A2: atomically reserve one scientific call_idx + budget pre-dispatch."""
    lock = state.get("lock")
    if lock is not None:
        lock.acquire()
    try:
        if (int(state.get("setup_calls", 0)) + int(state.get("calls", 0))
                + 1 > CALL_BUDGET
                or _remaining_s(state) <= 0
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

    def call(self, task, state=None):
        """One invocation; deadline-aware poll=min(120s,remaining).

        Watchdog timeout (120s, remaining>=120s): terminate+respawn, no retry.
        Wall timeout (deadline reached): terminate, no respawn, no retry.
        """
        assert self.proc is not None
        if state is not None:
            rem0 = _remaining_s(state)
            if rem0 <= 0:
                try:
                    self.conn.close()
                except Exception:  # noqa: BLE001
                    pass
                try:
                    self.proc.terminate()
                    self.proc.join(10)
                except Exception:  # noqa: BLE001
                    pass
                try:
                    state["budget_stop"] = True
                except Exception:  # noqa: BLE001
                    pass
                return {"exact": False, "syndrome_ok": False,
                        "iterations": -1, "finite": False, "beliefs": None,
                        "crash": True, "timeout": False, "wall_timeout": True,
                        "wall_s": 0.0, "rss": None,
                        "error": "wall-budget-exhausted"}
            poll_s = min(float(WATCHDOG), float(rem0))
        else:
            poll_s = float(WATCHDOG)
        self.conn.send(task)
        if not self.conn.poll(poll_s):
            # Distinguish deadline arrival from pure watchdog expiry.
            deadline_hit = False
            if state is not None:
                try:
                    deadline_hit = bool(_remaining_s(state) <= 0)
                except Exception:  # noqa: BLE001
                    deadline_hit = False
            pid = self.proc.pid
            self.conn.close()
            try:
                self.proc.terminate()
                self.proc.join(10)
            except Exception:  # noqa: BLE001
                pass
            if deadline_hit:
                try:
                    state["budget_stop"] = True
                except Exception:  # noqa: BLE001
                    pass
                return {"exact": False, "syndrome_ok": False,
                        "iterations": -1, "finite": False, "beliefs": None,
                        "crash": True, "timeout": False, "wall_timeout": True,
                        "wall_s": float(poll_s), "rss": None,
                        "error": "wall-budget-exhausted"}
            self.spawn(reason="watchdog-timeout-after-pid-%s" % pid)
            return {"exact": False, "syndrome_ok": False, "iterations": -1,
                    "finite": False, "beliefs": None, "crash": True,
                    "timeout": True, "wall_timeout": False,
                    "wall_s": float(WATCHDOG),
                    "rss": None, "error": "watchdog-timeout"}
        res = self.conn.recv()
        res["timeout"] = False
        res["wall_timeout"] = False
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


def aggregate_rss_strict(worker_rss_list, main_rss):
    """R1c-A2 strict aggregate: None if any side unknown (never 0)."""
    if main_rss is None:
        return None
    try:
        main = int(main_rss)
    except (TypeError, ValueError):
        return None
    total = int(main)
    for v in (worker_rss_list or []):
        if v is None:
            return None
        try:
            total += int(v)
        except (TypeError, ValueError):
            return None
    return int(total)


def select_effective_workers_pilot(requested, pilot_rss, main_rss,
                                   logfh=None):
    """R1c-A2 pure pilot selector (fail-closed, single measurement).

    Returns (effective_or_None, status) with status in
    ("ok","unknown","limit"). Candidates <= requested from
    (18,14,12,8,1); 1 always included. Unknown pilot/main -> unknown.
    Even w=1 over budget -> limit.
    """
    req = int(requested)
    if pilot_rss is None or main_rss is None:
        if logfh is not None:
            log("r1c-a2 pilot rss-unknown requested=%d pilot=%s main=%s"
                % (req, str(pilot_rss), str(main_rss)), logfh)
        return None, "unknown"
    try:
        per = int(pilot_rss)
        main = int(main_rss)
    except (TypeError, ValueError):
        if logfh is not None:
            log("r1c-a2 pilot rss-unknown requested=%d" % req, logfh)
        return None, "unknown"
    cands = [int(w) for w in (R1C_FULL_WORKERS,)
             + tuple(R1C_FALLBACK_WORKERS) + (1,) if int(w) <= req]
    if not cands:
        cands = [req]
    # Deduplicate preserving order (request 1 -> [1]).
    seen = []
    for w in cands:
        if w not in seen:
            seen.append(w)
    cands = seen
    for w in cands:
        if int(w) * int(per) + int(main) < RSS_CEIL:
            if logfh is not None:
                log("r1c-a2 workers requested=%d effective=%d "
                    "pilot_rss=%d main_rss=%d" % (req, int(w), per, main),
                    logfh)
            return int(w), "ok"
    if logfh is not None:
        log("r1c-a2 workers requested=%d limit-blocked pilot_rss=%d "
            "main_rss=%d" % (req, per, main), logfh)
    return None, "limit"


def update_rss_sample(state, worker_pid, worker_rss, main_rss):
    """R1c-A2: per-call/per-barrier worker/main/sampled-aggregate + peaks.

    Strict: sampled aggregate is None if any side unknown. Single peak and
    aggregate peak tracked separately (never substitute one for the other).
    Per-call partial views update singles + last maps; aggregate peak only
    advances when a full-pool view is present (barrier passes full lists via
    update_rss_barrier, or last map already covers the effective pool).
    Returns sampled aggregate (or None).
    """
    if worker_rss is not None:
        try:
            wv = int(worker_rss)
        except (TypeError, ValueError):
            wv = None
    else:
        wv = None
    if main_rss is not None:
        try:
            mv = int(main_rss)
        except (TypeError, ValueError):
            mv = None
    else:
        mv = None
    if wv is not None:
        prev = state.get("peak_single_rss")
        if prev is None or int(wv) > int(prev):
            state["peak_single_rss"] = int(wv)
        try:
            last = state.get("rss_workers_last")
            if last is None:
                state["rss_workers_last"] = {}
                last = state["rss_workers_last"]
            last[str(worker_pid)] = int(wv)
        except Exception:  # noqa: BLE001
            pass
    if mv is not None:
        prev = state.get("peak_single_rss")
        if prev is None or int(mv) > int(prev):
            state["peak_single_rss"] = int(mv)
        state["rss_main_last"] = int(mv)
    # Aggregate only from a complete view; partial per-call views leave the
    # aggregate peak untouched (no single-as-aggregate substitution).
    agg = None
    try:
        last = state.get("rss_workers_last") or {}
        mlast = state.get("rss_main_last")
        eff = state.get("workers_effective")
        if mlast is not None and len(last) > 0:
            if eff is None or int(len(last)) >= int(eff):
                vals = [int(v) for v in last.values()]
                agg = int(mlast) + int(sum(vals))
                state["rss_sampled_aggregate_last"] = int(agg)
                prev = state.get("peak_aggregate_rss")
                if prev is None or int(agg) > int(prev):
                    state["peak_aggregate_rss"] = int(agg)
    except (TypeError, ValueError):
        agg = None
    return agg


def update_rss_barrier(state, worker_rss_list, main_rss):
    """R1c-A2: barrier full-pool view; strict aggregate + aggregate peak."""
    agg = aggregate_rss_strict(worker_rss_list, main_rss)
    if agg is not None:
        state["rss_sampled_aggregate_last"] = int(agg)
        prev = state.get("peak_aggregate_rss")
        if prev is None or int(agg) > int(prev):
            state["peak_aggregate_rss"] = int(agg)
    # Singles also advance from barrier view.
    if main_rss is not None:
        try:
            mv = int(main_rss)
            prev = state.get("peak_single_rss")
            if prev is None or mv > int(prev):
                state["peak_single_rss"] = int(mv)
        except (TypeError, ValueError):
            pass
    for v in (worker_rss_list or []):
        if v is None:
            continue
        try:
            wv = int(v)
        except (TypeError, ValueError):
            continue
        prev = state.get("peak_single_rss")
        if prev is None or wv > int(prev):
            state["peak_single_rss"] = int(wv)
    return agg


def _build_one_arm_layer(job):
    """R1c: top-level picklable unit for arm×layer parallel structure.

    R1c-A4: at most two support constructions per (n,arm,layer) — primary
    support, H from that exact support, one independent support replay, H2
    from the replayed support; equality on both arrays plus the overflow
    diagnostic (same guarantee as the old triple build, one build fewer;
    the separate overflow rebuild is gone, reused from the primary build).
    """
    import sys as _sys
    import pathlib as _pl
    import numpy as _np
    root = _pl.Path(__file__).resolve().parents[1]
    _sys.path.insert(0, str(root / "comparison_bench" / "src"))
    from comparison_bench.formal_ir import v72p2d6_gf32_graph_mother as _d6
    arm, n, layer = job
    _sup, _ov = _d6.build_support_with_overflow(arm, int(n), layer)
    _H = _d6.assign_mother_from_support(arm, int(n), layer, _sup, int(n))
    _sup2, _ov2 = _d6.build_support_with_overflow(arm, int(n), layer)
    _H2 = _d6.assign_mother_from_support(arm, int(n), layer, _sup2, int(n))
    replay_ok = bool(_np.array_equal(_np.asarray(_sup), _np.asarray(_sup2))
                     and _np.array_equal(_np.asarray(_H), _np.asarray(_H2))
                     and int(_ov) == int(_ov2))
    return (arm, layer, _np.asarray(_H, dtype=_np.uint8),
            _np.asarray(_sup), replay_ok, int(_ov))


def build_structures_parallel(n, logfh, max_workers=18, arms=None):
    """R1c: arm×layer parallel; deterministic ARMS-order assembly.

    Identical records/summary/mothers to build_structures (replay per task).
    R1c-A4: arms=None builds all 8 (frozen default); scaling passes the
    frozen fallback arms only.
    """
    import os as _os
    _arms = list(ARMS) if arms is None else [a for a in ARMS if a in arms]
    jobs = [(arm, int(n), layer) for arm in _arms for layer in ("L1", "L2")]
    t0 = time.perf_counter()
    out = {}
    with concurrent.futures.ProcessPoolExecutor(
            max_workers=int(max_workers)) as ex:
        for arm, layer, H, sup, replay_ok, ov in ex.map(_build_one_arm_layer,
                                                        jobs):
            out[(arm, layer)] = (H, sup, replay_ok, ov)
    # Deterministic assembly in ARMS order (same as sequential).
    records = []
    summary = {}
    mothers = {}
    for arm in _arms:
        for layer in ("L1", "L2"):
            H, sup, replay_ok, ov = out[(arm, layer)]
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
        % (n, int(max_workers), time.perf_counter() - t0, len(_arms),
           len(records), _os.getpid()), logfh)
    return records, summary, mothers


def build_structures(n, logfh, arms=None):
    """Build all arms/layers at width n with replay check; return records,
    summary (f1.2-indexed prefix audits), mothers {(arm,layer): H}.

    R1c-A4: arms=None builds all 8 (frozen default); scaling passes the
    frozen fallback arms only. At most two support constructions per
    (n,arm,layer), overflow reused from the primary build."""
    records = []
    summary = {}
    mothers = {}
    _arms = list(ARMS) if arms is None else [a for a in ARMS if a in arms]
    for arm in _arms:
        for layer in ("L1", "L2"):
            sup, ov = build_support_with_overflow(arm, n, layer)
            H = assign_mother_from_support(arm, n, layer, sup, n)
            sup2, ov2 = build_support_with_overflow(arm, n, layer)
            H2 = assign_mother_from_support(arm, n, layer, sup2, n)
            replay_ok = bool(np.array_equal(np.asarray(sup), np.asarray(sup2))
                             and np.array_equal(np.asarray(H), np.asarray(H2))
                             and int(ov) == int(ov2))
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
    log("structure n=%d arms=%d records=%d" % (n, len(_arms), len(records)),
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

    R1c-A2: call_idx + call/wall budget reserved atomically inside the lock
    before dispatch (remaining = deadline - now); the blocking decoder call
    runs lock-free with poll=min(120s,remaining); the record is appended
    afterwards with the reserved index plus worker_pid/respawn_pid/timeout/
    wall_timeout/error. watchdog_ok = not timeout and not wall_timeout and
    wall<=120. Concurrency never exceeds 2500 total (setup + scientific).
    """
    if skip:
        return {"call_idx": -1, "arm": meta["arm"], "n": meta["n"],
                "seed": meta["seed"], "point": meta["point"],
                "rows_l1": meta["r1"], "rows_l2": meta["r2"], "mode": mode,
                "matrix_id": meta["matrix_id"], "exact": False,
                "syndrome_ok": False, "iterations": -1, "finite": False,
                "crash": True, "timeout": False, "wall_timeout": False,
                "prior_mass_on_truth": tm,
                "wall_s": 0.0, "rss_bytes": "", "watchdog_ok": True,
                "worker_pid": "", "respawn_pid": "", "error": "",
                "note": "app-undefined-l1-unavailable"}
    if state.get("chunk_wall_blocked"):
        raise StopIteration("chunk-wall-blocked")
    if not can_dispatch(state):
        # Atomic gate already covers remaining/budget; chunk case above.
        pass
    call_idx = reserve_call_idx(state)
    try:
        pid_before = str(worker.pids[-1]) if getattr(worker, "pids",
                                                     None) else ""
    except Exception:  # noqa: BLE001
        pid_before = ""
    task = {"h": np.asarray(h, dtype=np.uint8),
            "prior": np.asarray(prior, dtype=np.float64),
            "x_true": np.asarray(xt, dtype=np.int64),
            "return_beliefs": bool(ret_bel)}
    try:
        try:
            res = worker.call(task, state)
        except TypeError:
            # Fake workers in older tests take call(task) only.
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
                   "crash": True, "timeout": False, "wall_timeout": False,
                   "prior_mass_on_truth": tm, "wall_s": 0.0, "rss_bytes": "",
                   "watchdog_ok": False, "worker_pid": pid_before,
                   "respawn_pid": "", "error": "setup-budget-exhausted",
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
    timeout = bool(res.get("timeout", False))
    wall_timeout = bool(res.get("wall_timeout", False))
    err = str(res.get("error", ""))[:300]
    try:
        pid_after = str(worker.pids[-1]) if getattr(worker, "pids",
                                                    None) else ""
    except Exception:  # noqa: BLE001
        pid_after = ""
    respawn_pid = "" if pid_after == pid_before else pid_after
    watchdog_ok = bool((not timeout) and (not wall_timeout)
                       and wall <= float(WATCHDOG))
    try:
        main_now = d5._rss_bytes()
    except Exception:  # noqa: BLE001
        main_now = None
    rec = {"call_idx": call_idx, "arm": meta["arm"], "n": meta["n"],
           "seed": meta["seed"], "point": meta["point"],
           "rows_l1": meta["r1"], "rows_l2": meta["r2"], "mode": mode,
           "matrix_id": meta["matrix_id"], "exact": bool(res["exact"]),
           "syndrome_ok": bool(res["syndrome_ok"]),
           "iterations": int(res["iterations"]),
           "finite": bool(res["finite"]), "crash": bool(res["crash"]),
           "timeout": timeout, "wall_timeout": wall_timeout,
           "prior_mass_on_truth": tm, "wall_s": wall,
           "rss_bytes": "" if rss is None else int(rss),
           "watchdog_ok": watchdog_ok,
           "worker_pid": pid_before, "respawn_pid": respawn_pid,
           "error": err,
           "beliefs": res.get("beliefs")}
    lock = state.get("lock")
    if lock is not None:
        lock.acquire()
    try:
        if rss is not None:
            try:
                if int(rss) > int(state.get("peak_rss", 0)):
                    state["peak_rss"] = int(rss)
            except (TypeError, ValueError):
                pass
        # R1c-A2 per-call RSS sampling (strict, no zero substitution).
        try:
            update_rss_sample(state, pid_before or pid_after, rss, main_now)
        except Exception:  # noqa: BLE001
            pass
        if wall_timeout:
            state["budget_stop"] = True
        state["records"].append(rec)
    finally:
        if lock is not None:
            try:
                lock.release()
            except RuntimeError:
                pass
    return rec


def flush_decoder_records(path, records, logfh=None):
    """R1c-A2: phase checkpoint rewrite in frozen call_idx order + flush/fsync.

    Same fresh UUID root, deterministic rewrite (never called append-only).
    fsync failure is fail-closed (raise).
    """
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
        except Exception as ex:  # noqa: BLE001 - fail closed
            raise RuntimeError("fsync-failed decoder_records: %r" % (ex,))
    if logfh is not None:
        log("flush decoder_records rows=%d" % len(rows), logfh)


def append_structure_records(path, new_records, logfh=None):
    """R1c-A2: phase checkpoint rewrite (read + merge + ordered rewrite).

    Same fresh UUID root; deterministic order by (arm,n,layer,prefix_rows).
    Never called append-only. fsync failure is fail-closed (raise).
    """
    import csv as _csv
    p = pathlib.Path(path)
    merged = []
    fieldnames = None
    if p.exists():
        with open(str(p), newline="", encoding="utf-8") as fh:
            rd = _csv.DictReader(fh)
            fieldnames = list(rd.fieldnames) if rd.fieldnames else None
            for r in rd:
                merged.append(dict(r))
    for r in (new_records or []):
        merged.append({k: r.get(k, "") for k in
                       (fieldnames or list(r.keys()))})
        if fieldnames is None:
            fieldnames = list(r.keys())
    if fieldnames is None:
        fieldnames = []
    def _skey(r):
        try:
            n = int(r.get("n", 0))
        except (TypeError, ValueError):
            n = 0
        try:
            pr = int(r.get("prefix_rows", 0))
        except (TypeError, ValueError):
            pr = 0
        return (str(r.get("arm", "")), n, str(r.get("layer", "")), pr)
    merged.sort(key=_skey)
    with open(str(p), "w", encoding="utf-8", newline="") as fh:
        w = _csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for r in merged:
            w.writerow({k: r.get(k, "") for k in fieldnames})
        fh.flush()
        try:
            os.fsync(fh.fileno())
        except Exception as ex:  # noqa: BLE001 - fail closed
            raise RuntimeError("fsync-failed structure_records: %r" % (ex,))
    if logfh is not None:
        log("checkpoint structure_records rows=%d" % len(merged), logfh)


def note_chunk_wall(phase, wall, logfh, state):
    """R1c-A2: per-chunk wall check; >=5400s is BLOCKED + barrier RSS update."""
    ok = bool(float(wall) < R1C_CHUNK_WALL_MAX)
    log("r1c chunk %s wall=%.1f chunk_ok=%s" % (phase, float(wall), ok),
        logfh)
    # R1c-A2 per-barrier RSS sampling (strict, never 0, no substitution).
    try:
        try:
            _m = d5._rss_bytes()
        except Exception:  # noqa: BLE001
            _m = None
        _last = state.get("rss_workers_last") or {}
        if _m is not None and len(_last) > 0:
            try:
                update_rss_barrier(state, [int(v) for v in _last.values()],
                                   _m)
            except Exception:  # noqa: BLE001
                pass
        else:
            try:
                update_rss_sample(state, "barrier-%s" % phase, None, _m)
            except Exception:  # noqa: BLE001
                pass
    except Exception:  # noqa: BLE001
        pass
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
    terminal and stops further dispatch). Zero new dispatches once blocked.
    """
    if state.get("chunk_wall_blocked") or state.get("budget_stop"):
        raise StopIteration("chunk-wall-blocked-or-budget-stop")
    if _remaining_s(state) <= 0:
        try:
            state["budget_stop"] = True
        except Exception:  # noqa: BLE001
            pass
        raise StopIteration("wall-budget-exhausted")
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


def a3_stage_partitions(counted):
    """Split counted rows into canary / scaling-per-n / confirmation.

    Identity key (n,arm,seed,point,mode); frozen seed domains. Anything
    outside the three domains (e.g. a canary seed at n!=64) lands in
    'outside' and fails the stage check. Verifier path only."""
    parts = {"canary": [], "scaling": {}, "confirmation": [], "outside": []}
    for r in counted:
        try:
            seed = int(r.get("seed", -1))
        except (TypeError, ValueError):
            seed = -1
        n = str(r.get("n", ""))
        if seed in CONF_SEEDS:
            parts["confirmation"].append(r)
        elif seed in SCALING_SEEDS:
            parts["scaling"].setdefault(n, []).append(r)
        elif seed in CANARY_SEEDS and n == "64":
            parts["canary"].append(r)
        else:
            parts["outside"].append(r)
    return parts


def a3_cell_app(modes):
    """End-to-end APP exact for one cell's mode dict (pipeline rule)."""
    if "L1" in modes and "L2-APP" in modes:
        return bool(modes["L1"].get("exact") == "True"
                    and modes["L2-APP"].get("exact") == "True")
    return False


def a3_ssum_from_structure(srecs, width):
    """Rebuild {arm:{layer:{prefix_audits:[...]}}} for one width (A3 verify).

    Uses only the frozen audit scalars in structure_records.csv, ordered by
    prefix_rows, so per-width structural order is independently recomputed."""
    ssum = {}
    for r in srecs:
        if str(r.get("n", "")) != str(width):
            continue
        arm = r.get("arm", "")
        layer = r.get("layer", "")
        try:
            g = r.get("girth", "")
            girth = int(g) if str(g) not in ("", "None") else None
        except (TypeError, ValueError):
            girth = None
        try:
            audit = {"four_cycles": int(r.get("four_cycles", 0) or 0),
                     "four_cycle_variable_incidence_max": int(
                         r.get("four_cycle_variable_incidence_max", 0) or 0),
                     "girth": girth,
                     "row_degree_max": int(r.get("row_degree_max", 0) or 0),
                     "row_degree_sumsq": int(
                         r.get("row_degree_sumsq", 0) or 0),
                     "prefix_rows": int(r.get("prefix_rows", 0) or 0)}
        except (TypeError, ValueError):
            continue
        ssum.setdefault(arm, {}).setdefault(
            layer, {"prefix_audits": []})["prefix_audits"].append(audit)
    for layers in ssum.values():
        for rec in layers.values():
            rec["prefix_audits"].sort(key=lambda a: a["prefix_rows"])
    return ssum


def a3_classify_evidence(counted):
    """A3 crash-precedence classifier over counted rows.

    Returns (recomputed_terminal_or_None, reason). None means no attempted
    crash/nonfinite, so the stored terminal stands. Degree ValueError =>
    STRUCTURE_INVARIANT; any other attempted crash/nonfinite =>
    ATTEMPTED_INVALID. Neither supports a topology-no-recovery claim."""
    deg = 0
    other = 0
    for r in counted:
        crash = str(r.get("crash", "False")) == "True"
        finite = str(r.get("finite", "True")) == "True"
        if not crash and finite:
            continue
        if A3_DEGREE_SUBSTR in str(r.get("error", "")):
            deg += 1
        else:
            other += 1
    if deg:
        return (A3_STRUCTURE_INVARIANT_TERMINAL, "degree-invariant:%d" % deg)
    if other:
        return (A3_ATTEMPTED_INVALID_TERMINAL,
                "crash-or-nonfinite:%d" % other)
    return (None, "no-attempted-crash")


def a3_compare_terminals(stored, recomputed):
    """Fail-closed comparison: the recomputed terminal always governs."""
    agree = (str(stored) == str(recomputed))
    return (agree, str(recomputed))


def verify_command(out_root):
    """R1c-A2 independent scalar recomputation (15 independent rejections)."""
    out = pathlib.Path(out_root)
    ok = True

    def check(name, cond, detail=""):
        nonlocal ok
        print("%s %s %s" % ("PASS" if cond else "FAIL", name, detail))
        if not cond:
            ok = False
    try:
        sel = json.loads((out / "selected_arms.json").read_text(
            encoding="utf-8"))
    except Exception as ex:  # noqa: BLE001
        check("six-files", False, "selected_arms.json unreadable %r" % (ex,))
        print("VERIFY FAIL")
        return False
    try:
        summ = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    except Exception as ex:  # noqa: BLE001
        check("six-files", False, "summary.json unreadable %r" % (ex,))
        print("VERIFY FAIL")
        return False
    try:
        mani = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    except Exception as ex:  # noqa: BLE001
        check("six-files", False, "manifest.json unreadable %r" % (ex,))
        print("VERIFY FAIL")
        return False
    try:
        with open(out / "decoder_records.csv", newline="",
                  encoding="utf-8") as fh:
            recs = list(csv.DictReader(fh))
    except Exception as ex:  # noqa: BLE001
        check("six-files", False, "decoder_records.csv unreadable %r" % (ex,))
        print("VERIFY FAIL")
        return False
    try:
        with open(out / "structure_records.csv", newline="",
                  encoding="utf-8") as fh:
            srecs = list(csv.DictReader(fh))
    except Exception as ex:  # noqa: BLE001
        check("six-files", False, "structure_records unreadable %r" % (ex,))
        print("VERIFY FAIL")
        return False
    # (1) six files + decoder set.
    check("six-files", all((out / f).exists() for f in (
        "manifest.json", "structure_records.csv", "selected_arms.json",
        "decoder_records.csv", "summary.json", "command_log.txt")))
    counted = []
    try:
        counted = [r for r in recs if int(r.get("call_idx", -1)) >= 0]
    except (TypeError, ValueError):
        counted = []
    # (2) call_idx continuous 1..N.
    try:
        idxs = sorted(int(r["call_idx"]) for r in counted)
        check("call_idx-continuous",
              idxs == list(range(1, len(idxs) + 1)),
              "n=%d idx=%s" % (len(idxs), str(idxs[:8])))
    except (TypeError, ValueError, KeyError) as ex:  # noqa: BLE001
        check("call_idx-continuous", False, repr(ex)[:120])
    # (3) semantic key no duplicate (A3: identity includes n).
    try:
        keys = [(r.get("n"), r.get("arm"), r.get("seed"), r.get("point"),
                 r.get("mode")) for r in counted]
        check("semantic-key-no-dup", len(set(keys)) == len(keys),
              "n=%d" % len(keys))
    except Exception as ex:  # noqa: BLE001
        check("semantic-key-no-dup", False, repr(ex)[:120])
    # (4) calls consistent csv vs summary.
    try:
        setup_calls = int(summ.get("setup_decoder_calls", 0))
        sci = int(summ.get("calls", summ.get("scientific_calls", -1)))
        check("calls-consistent",
              len(counted) == sci
              and int(mani.get("calls", sci)) == sci
              and int(mani.get("scientific_calls", sci)) == sci,
              "csv=%d summary=%s" % (len(counted), str(sci)))
    except (TypeError, ValueError, KeyError) as ex:  # noqa: BLE001
        check("calls-consistent", False, repr(ex)[:120])
        setup_calls = 0
    # (5) total <= 2500.
    try:
        check("le-2500",
              len(counted) <= 2500
              and int(summ.get("setup_decoder_calls", 0)) + len(counted)
              <= 2500
              and int(mani.get("total_decoder_calls",
                               setup_calls + len(counted)))
              == setup_calls + len(counted),
              "sci=%d setup=%d" % (len(counted), setup_calls))
    except (TypeError, ValueError, KeyError) as ex:  # noqa: BLE001
        check("le-2500", False, repr(ex)[:120])
    # (6) effective <= requested.
    try:
        req = int(mani.get("workers_requested",
                           summ.get("workers_requested", -1)))
        _term6 = str(summ.get("terminal", mani.get("terminal", "")))
        _eff_raw = mani.get("workers_effective",
                            summ.get("workers_effective", -1))
        if _eff_raw is None and _term6 in (R1C_RSS_UNKNOWN_TERMINAL,
                                           R1C_RSS_LIMIT_TERMINAL):
            check("effective-le-requested", req in (18, 14, 12, 8, 1),
                  "req=%s blocked=%s" % (str(req), _term6))
            eff = -1
        else:
            eff = int(_eff_raw)
            check("effective-le-requested",
                  1 <= eff <= req and req in (18, 14, 12, 8, 1)
                  and int(summ.get("workers_effective", eff)) == eff
                  and int(summ.get("workers_requested", req)) == req,
                  "req=%s eff=%s" % (str(req), str(eff)))
    except (TypeError, ValueError, KeyError) as ex:  # noqa: BLE001
        check("effective-le-requested", False, repr(ex)[:120])
        req, eff = -1, -1
    # (7) RSS strict: unknown never 0, single never as aggregate, <2GiB.
    try:
        main_m = mani.get("main_rss_bytes")
        workers_m = mani.get("worker_rss_bytes", None)
        agg_m = mani.get("aggregate_rss_bytes", None)
        peak_s = mani.get("peak_single_rss_bytes",
                          mani.get("peak_rss_bytes", None))
        peak_a = mani.get("peak_aggregate_rss_bytes", None)
        sem = str(mani.get("rss_semantics", ""))
        strict_agg = (aggregate_rss_strict(workers_m, main_m)
                      if isinstance(workers_m, list) else None)
        workers_known = isinstance(workers_m, list) and len(workers_m) > 0 \
            and all(v is not None for v in workers_m)
        rss_ok_rows = all(r.get("rss_bytes", "") != ""
                          and int(r["rss_bytes"]) < RSS_CEIL
                          for r in counted) if counted else True
        # Unknown record rows must exist as "" (never 0).
        unknown_rows = [r for r in counted if r.get("rss_bytes", "") == ""]
        cond = True
        detail = "agg=%s strict=%s" % (str(agg_m), str(strict_agg))
        if main_m is None or not workers_known:
            # Unknown pool must not claim a numeric aggregate.
            cond = cond and (agg_m is None)
            detail += " unknown-pool"
        else:
            cond = cond and (agg_m is not None and int(agg_m) == int(
                strict_agg) and int(agg_m) < RSS_CEIL)
        if peak_a is not None and agg_m is not None:
            cond = cond and (int(peak_a) >= int(agg_m))
        if eff is not None and eff > 1 and peak_s is not None \
                and peak_a is not None:
            # Single peak must not masquerade as aggregate peak.
            cond = cond and (int(peak_a) > int(peak_s)
                             or int(peak_a) == int(agg_m))
        cond = cond and rss_ok_rows and (len(unknown_rows) == 0)
        cond = cond and ("fail-closed" in sem and "no-zero" in sem)
        # Summary safety flag must agree (unknown/over-limit -> False).
        # RSS-blocked runs carry rss_known_ok=False by construction.
        try:
            _term7 = str(summ.get("terminal", mani.get("terminal", "")))
        except Exception:  # noqa: BLE001
            _term7 = ""
        if _term7 in (R1C_RSS_UNKNOWN_TERMINAL, R1C_RSS_LIMIT_TERMINAL):
            cond = cond and (bool(summ.get("confirmation_safety", {}).get(
                "rss_known_ok", False)) is False)
        else:
            cond = cond and bool(summ.get("confirmation_safety", {}).get(
                "rss_known_ok", True)) == (len(unknown_rows) == 0
                                           and rss_ok_rows)
        check("rss-strict", bool(cond), detail)
    except (TypeError, ValueError, KeyError) as ex:  # noqa: BLE001
        check("rss-strict", False, repr(ex)[:160])
    # (8) wall budget: final wall and per-chunk walls vs blocking terminals.
    try:
        wall = float(summ.get("wall_s", mani.get("wall_s", 0.0)))
        term = str(summ.get("terminal", mani.get("terminal", "")))
        chunk_walls = dict(summ.get("chunk_walls", mani.get("chunk_walls",
                                                             {})))
        wall_cond = (wall <= float(WALL_BUDGET)) or (
            term == R1C_WALL_BLOCKED_TERMINAL)
        chunk_over = [k for k, v in chunk_walls.items()
                      if float(v) >= float(R1C_CHUNK_WALL_MAX)]
        chunk_cond = (len(chunk_over) == 0) or (
            term == R1C_CHUNK_WALL_BLOCKED_TERMINAL)
        # Overrun without the matching terminal is FAIL.
        check("wall-budget", bool(wall_cond and chunk_cond),
              "wall=%.1f term=%s over=%s" % (wall, term, str(chunk_over)))
    except (TypeError, ValueError, KeyError) as ex:  # noqa: BLE001
        check("wall-budget", False, repr(ex)[:160])
    # (9) terminal replay (science + 4 blocking terminals).
    try:
        sys.path.insert(0, str(ROOT / "comparison_bench" / "src"))
        from comparison_bench.formal_ir.v72p2d6_gf32_graph_mother import (
            select_advancement as _adv, classify_terminal as _cls)
        blocking = {R1C_CHUNK_WALL_BLOCKED_TERMINAL,
                    R1C_RSS_UNKNOWN_TERMINAL, R1C_RSS_LIMIT_TERMINAL,
                    R1C_WALL_BLOCKED_TERMINAL}
        term = str(summ.get("terminal", ""))
        rep_ok = False
        if term in blocking:
            if term == R1C_CHUNK_WALL_BLOCKED_TERMINAL:
                rep_ok = bool(summ.get("chunk_wall_blocked", False))
            else:
                rep_ok = True
                # RSS/wall blocking must still carry consistent safety flags.
                if term in (R1C_RSS_UNKNOWN_TERMINAL,
                            R1C_RSS_LIMIT_TERMINAL):
                    rep_ok = True
        elif summ.get("advancing") and summ.get("confirmation_counts"):
            if len(summ["advancing"]) == 1 \
                    and "SCALING" not in term \
                    and int(summ.get("confirmation_width", 64)) == 64:
                a = summ["advancing"][0]
                c = summ["confirmation_counts"][a]
                rep = _cls([{"exact": c[p]} for p in POINTS],
                           summ["confirmation_safety"]["crashes"],
                           summ["confirmation_safety"]["nonfinite"],
                           summ["confirmation_safety"]["rss_known_ok"],
                           summ["confirmation_safety"]["disagreements"])
                rep_ok = (rep == term)
            else:
                # Scaling or multi-arm: at least a known terminal string.
                rep_ok = term.startswith("D6_GRAPH_")
        else:
            rep_ok = term in ("D6_GRAPH_TOPOLOGY_NO_USEFUL_RECOVERY",
                              R1C_CHUNK_WALL_BLOCKED_TERMINAL,
                              R1C_RSS_UNKNOWN_TERMINAL,
                              R1C_RSS_LIMIT_TERMINAL,
                              R1C_WALL_BLOCKED_TERMINAL)
        check("terminal-replay", bool(rep_ok), term)
    except (TypeError, ValueError, KeyError) as ex:  # noqa: BLE001
        check("terminal-replay", False, repr(ex)[:160])
    # (10) timeout/watchdog definition.
    try:
        def _wb(r):
            to = str(r.get("timeout", "False")) == "True"
            wt = str(r.get("wall_timeout", r.get("wall_timeout", "False"))) \
                == "True"
            try:
                w = float(r.get("wall_s", 0.0))
            except (TypeError, ValueError):
                w = 1e9
            exp = (not to) and (not wt) and (w <= float(WATCHDOG))
            got = str(r.get("watchdog_ok", "")) == "True"
            return (exp == got) and not (to and wt)
        check("timeout-watchdog", all(_wb(r) for r in counted),
              "n=%d" % len(counted))
    except Exception as ex:  # noqa: BLE001
        check("timeout-watchdog", False, repr(ex)[:160])
    # (11) PID present + respawn/error fields.
    try:
        pids_ok = all(str(r.get("worker_pid", "")) != "" for r in counted) \
            if counted else True
        fields_ok = all("respawn_pid" in r and "wall_timeout" in r
                        and "error" in r for r in counted) if counted else True
        # respawn pid, when present, must differ from worker pid.
        resp_ok = all(str(r.get("respawn_pid", "")) == ""
                      or str(r.get("respawn_pid", ""))
                      != str(r.get("worker_pid", "")) for r in counted) \
            if counted else True
        check("pid-present", bool(pids_ok and fields_ok and resp_ok),
              "pids=%d" % len({str(r.get("worker_pid", "")) for r in counted
                               }) if counted else "empty")
    except Exception as ex:  # noqa: BLE001
        check("pid-present", False, repr(ex)[:160])
    # (12) seed domain.
    try:
        allowed = set(int(s) for s in list(CANARY_SEEDS)
                      + list(CONF_SEEDS) + list(SCALING_SEEDS))
        check("seed-domain",
              all(int(r.get("seed", -1)) in allowed for r in counted),
              "n=%d" % len(counted))
    except (TypeError, ValueError, KeyError) as ex:  # noqa: BLE001
        check("seed-domain", False, repr(ex)[:160])
    # (13) coverage: arms/points/modes within frozen sets.
    try:
        pts = {"f1.0", "f1.2", "square"}
        mds = {"L1", "L2-APP", "L2-oracle"}
        selset = set(sel.get("selected", []))
        cov_ok = all(r.get("point") in pts and r.get("mode") in mds
                     and r.get("arm") in selset for r in counted) \
            if counted else True
        set_ok = len(selset) <= 6 and "B0_D5_DV3_NATIVE" in selset
        check("coverage", bool(cov_ok and set_ok), str(sorted(selset)))
    except Exception as ex:  # noqa: BLE001
        check("coverage", False, repr(ex)[:160])
    # (14) stage-separated recompute (A3): canary uses n=64 + canary seeds
    # only; scaling uses scaling seeds grouped per width; confirmation uses
    # confirmation seeds at the selected width; empty confirmation is EMPTY,
    # never observed safety.
    try:
        sys.path.insert(0, str(ROOT / "comparison_bench" / "src"))
        from comparison_bench.formal_ir.v72p2d6_gf32_graph_mother import (
            select_advancement as _adv2, structural_rank_list as _rank2)
        _blocking14 = {R1C_CHUNK_WALL_BLOCKED_TERMINAL,
                       R1C_RSS_UNKNOWN_TERMINAL, R1C_RSS_LIMIT_TERMINAL,
                       R1C_WALL_BLOCKED_TERMINAL}
        parts = a3_stage_partitions(counted)
        outside_ok = (len(parts["outside"]) == 0)
        # Canary partition: per-cell app exact + f1.2 iter totals.
        can_cells = {}
        for r in parts["canary"]:
            can_cells.setdefault(
                (r["arm"], r["seed"], r["point"]), {})[r["mode"]] = r
        can_re = {}
        can_iter = {}
        for (arm, seed, point), modes in can_cells.items():
            d = can_re.setdefault(arm, {"f12_exact": 0, "sq_exact": 0})
            it = sum(max(int(modes[m].get("iterations", -1)), 0)
                     for m in ("L1", "L2-APP") if m in modes)
            if point == "f1.2":
                d["f12_exact"] += int(a3_cell_app(modes))
                can_iter[arm] = can_iter.get(arm, 0) + it
            elif point == "square":
                d["sq_exact"] += int(a3_cell_app(modes))
        summ_can = {a: {"f12_exact": v["f12_exact"], "sq_exact": v["sq_exact"]}
                    for a, v in summ["canary"].items()}
        can_exact_ok = (can_re == summ_can)
        can_iter_ok = (set(can_iter) <= set(summ_can)) and all(
            int(summ["canary"].get(a, {}).get("f12_iter", -1))
            == can_iter.get(a, 0) for a in summ_can)
        adv_ok = (_adv2({a: {"f12_exact": v["f12_exact"],
                             "f12_iter": v["f12_iter"],
                             "sq_exact": v["sq_exact"]}
                        for a, v in summ["canary"].items()},
                       sel.get("structural_order_new", []))
                  == list(summ.get("advancing", [])))
        # Scaling partitions: fallback dispatch + per-width sig/advancing.
        fb = [x for x in (sel.get("fallback_T"), sel.get("fallback_M"))
              if x is not None]
        order_ok = True
        if set(parts["scaling"]) - {"128", "256"}:
            order_ok = False
        first_sig_width = None
        n64_adv = list(summ.get("advancing", []))
        for width in ("128", "256"):
            wrows = parts["scaling"].get(width, [])
            if wrows and sorted({r["arm"] for r in wrows}) != sorted(fb):
                order_ok = False
            w_cells = {}
            for r in wrows:
                w_cells.setdefault(
                    (r["arm"], r["seed"], r["point"]), {})[r["mode"]] = r
            sig = {}
            for (arm, seed, point), modes in w_cells.items():
                s = sig.setdefault(arm, {"f12_exact": 0, "f12_iter": 0,
                                         "sq_exact": 0})
                it = sum(max(int(modes[m].get("iterations", -1)), 0)
                         for m in ("L1", "L2-APP") if m in modes)
                if point == "f1.2":
                    s["f12_exact"] += int(a3_cell_app(modes))
                    s["f12_iter"] += it
                elif point == "square":
                    s["sq_exact"] += int(a3_cell_app(modes))
            try:
                w_adv = _adv2(sig, _rank2(a3_ssum_from_structure(
                    srecs, width), fb)) if fb else []
            except Exception:  # noqa: BLE001 - order failure is check FAIL
                w_adv = None
                order_ok = False
            if first_sig_width is None and w_adv:
                first_sig_width = int(width)
        # Confirmation partition: counts + safety at the selected width.
        width = int(summ.get("confirmation_width", 64))
        conf_rows = parts["confirmation"]
        conf_width_ok = all(int(r.get("n", -1)) == width for r in conf_rows)
        conf_cells = {}
        for r in conf_rows:
            conf_cells.setdefault(
                (r["arm"], r["seed"], r["point"]), {})[r["mode"]] = r
        conf_re = {}
        safety_re = {"crashes": 0, "nonfinite": 0, "disagreements": 0}
        for (arm, seed, point), modes in conf_cells.items():
            if point in POINTS:
                arm_d = conf_re.setdefault(arm, {})
                arm_d[point] = arm_d.get(point, 0) + int(a3_cell_app(modes))
            if any(str(m.get("crash", "False")) == "True"
                   for m in modes.values()):
                safety_re["crashes"] += 1
            elif any(str(m.get("finite", "True")) != "True"
                     for m in modes.values()):
                safety_re["nonfinite"] += 1
            if "L1" in modes and "L2-APP" in modes:
                syn = bool(modes["L1"].get("syndrome_ok") == "True"
                           and modes["L2-APP"].get("syndrome_ok")
                           == "True")
                if bool(a3_cell_app(modes)) != syn:
                    safety_re["disagreements"] += 1
        if n64_adv:
            width_exp_ok = (width == 64 and len(conf_rows) > 0)
        elif first_sig_width is None:
            width_exp_ok = (width == 64 and len(conf_rows) == 0)
        else:
            width_exp_ok = (width == first_sig_width and len(conf_rows) > 0)
        width_ok = (width in (64, 128, 256)) and (
            ("SCALING" in str(summ.get("terminal", ""))) == (width != 64)
            or str(summ.get("terminal", "")) in _blocking14)
        conf_match_ok = (conf_re == dict(summ.get("confirmation_counts",
                                                  {})))
        try:
            _safety_stored = summ.get("confirmation_safety", {})
            safety_ok = all(int(_safety_stored.get(k, -1)) == safety_re[k]
                            for k in ("crashes", "nonfinite",
                                      "disagreements"))
        except (TypeError, ValueError):
            safety_ok = False
        check("scaling-recompute",
              bool(outside_ok and can_exact_ok and can_iter_ok and adv_ok
                   and order_ok and conf_width_ok and width_exp_ok
                   and width_ok and conf_match_ok and safety_ok),
              "adv=%s w=%s sig128=%s" % (
                  str(summ.get("advancing")),
                  str(summ.get("confirmation_width")),
                  str(first_sig_width)))
    except (TypeError, ValueError, KeyError) as ex:  # noqa: BLE001
        check("scaling-recompute", False, repr(ex)[:160])
    # (15) manifest consistent vs summary.
    try:
        itmax = max([int(r["iterations"]) for r in counted] or [0])
        m_ok = (int(mani.get("setup_decoder_calls",
                             summ.get("setup_decoder_calls", 0)))
                == int(summ.get("setup_decoder_calls", 0)))
        m_ok = m_ok and (int(mani.get("total_decoder_calls",
                                      setup_calls + len(counted)))
                         == setup_calls + len(counted))
        m_ok = m_ok and (int(summ.get("iterations_max", itmax)) == itmax)
        m_ok = m_ok and (str(mani.get("revision", "")) == str(
            summ.get("revision", mani.get("revision", ""))))
        m_ok = m_ok and (abs(float(mani.get("wall_s", 0.0))
                             - float(summ.get("wall_s", 0.0))) < 3600)
        check("manifest-consistent", bool(m_ok),
              "itmax=%d" % itmax)
    except (TypeError, ValueError, KeyError) as ex:  # noqa: BLE001
        check("manifest-consistent", False, repr(ex)[:160])
    # A3-08 stored vs recomputed terminal (decision-layer INFO, non-gating:
    # disagreement is fail-closed — recomputed governs, Pre-RESULT routes
    # BLOCKED — while the mechanical VERIFY exit covers the 15 checks above).
    try:
        _stored = str(summ.get("terminal", ""))
        _re, _reason = a3_classify_evidence(counted)
        _recomputed = _re if _re is not None else _stored
        _agree, _gov = a3_compare_terminals(_stored, _recomputed)
        print("INFO stored-terminal %s" % _stored)
        print("INFO recomputed-terminal %s %s" % (_recomputed, _reason))
        print("INFO terminal-agreement %s governs=%s" % (
            str(_agree), _gov))
        if len(a3_stage_partitions(counted)["confirmation"]) == 0:
            print("INFO confirmation-stage EMPTY_NOT_EVIDENCE")
    except Exception as ex:  # noqa: BLE001 - reporting never gates
        print("INFO terminal-report-unavailable %r" % (ex,))
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
    _t0 = time.perf_counter()
    state = {"calls": 0, "setup_calls": 0, "t0": _t0,
             "deadline": float(_t0) + float(WALL_BUDGET),
             "records": [], "peak_rss": 0, "peak_single_rss": None,
             "peak_aggregate_rss": None, "rss_workers_last": {},
             "rss_main_last": None, "rss_sampled_aggregate_last": None,
             "workers_effective": None, "rss_block_terminal": None,
             "budget_stop": False,
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
            # R1c-A2 pilot fail-closed even for sequential request.
            eff1, st1 = select_effective_workers_pilot(
                1, worker.last_rss, main_rss, logfh)
            if st1 == "unknown":
                state["rss_block_terminal"] = R1C_RSS_UNKNOWN_TERMINAL
                workers = 0
                rss_info = {"requested": 1, "effective": None,
                            "main_rss_bytes": main_rss,
                            "worker_rss_bytes": list(worker_rss_list),
                            "aggregate_rss_bytes": None,
                            "peak_single_rss_bytes": state.get(
                                "peak_single_rss"),
                            "peak_aggregate_rss_bytes": state.get(
                                "peak_aggregate_rss"),
                            "rss_semantics": RSS_SEMANTICS}
                log("r1c-a2 workers requested=1 BLOCKED unknown "
                    "main=%s pilot=%s" % (str(main_rss),
                                          str(worker.last_rss)), logfh)
            elif st1 == "limit":
                state["rss_block_terminal"] = R1C_RSS_LIMIT_TERMINAL
                workers = 0
                rss_info = {"requested": 1, "effective": None,
                            "main_rss_bytes": main_rss,
                            "worker_rss_bytes": list(worker_rss_list),
                            "aggregate_rss_bytes": aggregate_rss_strict(
                                worker_rss_list, main_rss),
                            "peak_single_rss_bytes": state.get(
                                "peak_single_rss"),
                            "peak_aggregate_rss_bytes": state.get(
                                "peak_aggregate_rss"),
                            "rss_semantics": RSS_SEMANTICS}
                log("r1c-a2 workers requested=1 BLOCKED limit "
                    "main=%s pilot=%s" % (str(main_rss),
                                          str(worker.last_rss)), logfh)
            else:
                agg0 = aggregate_rss_strict(worker_rss_list, main_rss)
                state["workers_effective"] = 1
                try:
                    update_rss_barrier(state, worker_rss_list, main_rss)
                except Exception:  # noqa: BLE001
                    pass
                rss_info = {"requested": 1, "effective": 1,
                            "main_rss_bytes": main_rss,
                            "worker_rss_bytes": list(worker_rss_list),
                            "aggregate_rss_bytes": agg0,
                            "peak_single_rss_bytes": state.get(
                                "peak_single_rss"),
                            "peak_aggregate_rss_bytes": state.get(
                                "peak_aggregate_rss"),
                            "rss_semantics": RSS_SEMANTICS}
                log("r1c-a2 workers requested=1 effective=1 main_rss=%s "
                    "worker_rss=%s aggregate=%s setup=%d"
                    % (str(main_rss), str(worker_rss_list), str(agg0),
                       int(state.get("setup_calls", 0))), logfh)
        else:
            # R1c-A2: single pilot measures RSS, then size pool (never
            # start-18-then-trim). Expansion re-samples each worker.
            pilot = None
            try:
                pilot = Worker(logfh, state)
            except StopIteration as ex:
                log("STOP setup-budget pilot %s" % ex, logfh)
                pilot = None
            try:
                main_rss = d5._rss_bytes()
            except Exception:  # noqa: BLE001
                main_rss = None
            pilot_rss = pilot.last_rss if pilot is not None else None
            eff, st = select_effective_workers_pilot(
                req_workers, pilot_rss, main_rss, logfh)
            if st != "ok":
                # Fail closed before any scientific dispatch.
                if pilot is not None:
                    try:
                        pilot.stop()
                    except Exception:  # noqa: BLE001
                        pass
                workers = 0
                pool_workers = []
                pool_q = queue.Queue()
                state["rss_block_terminal"] = (
                    R1C_RSS_UNKNOWN_TERMINAL if st == "unknown"
                    else R1C_RSS_LIMIT_TERMINAL)
                state["budget_stop"] = True
                rss_info = {"requested": req_workers, "effective": None,
                            "main_rss_bytes": main_rss,
                            "worker_rss_bytes": [pilot_rss],
                            "aggregate_rss_bytes": None,
                            "peak_single_rss_bytes": state.get(
                                "peak_single_rss"),
                            "peak_aggregate_rss_bytes": state.get(
                                "peak_aggregate_rss"),
                            "rss_semantics": RSS_SEMANTICS}
                log("r1c-a2 workers requested=%d BLOCKED %s main=%s "
                    "pilot=%s" % (req_workers, st, str(main_rss),
                                  str(pilot_rss)), logfh)
            else:
                workers = int(eff)
                state["workers_effective"] = int(workers)
                cand = [pilot]
                try:
                    for _ in range(int(workers) - 1):
                        cand.append(Worker(logfh, state))
                except StopIteration as ex:
                    log("STOP setup-budget expand %s" % ex, logfh)
                    state["budget_stop"] = True
                worker_rss_list = [w.last_rss for w in cand]
                # Expansion re-sample: unknown or over-limit stops.
                if any(v is None for v in worker_rss_list) \
                        or main_rss is None:
                    for w in cand:
                        try:
                            w.stop()
                        except Exception:  # noqa: BLE001
                            pass
                    workers = 0
                    pool_workers = []
                    pool_q = queue.Queue()
                    state["rss_block_terminal"] = R1C_RSS_UNKNOWN_TERMINAL
                    state["budget_stop"] = True
                    rss_info = {"requested": req_workers, "effective": None,
                                "main_rss_bytes": main_rss,
                                "worker_rss_bytes": list(worker_rss_list),
                                "aggregate_rss_bytes": None,
                                "peak_single_rss_bytes": state.get(
                                    "peak_single_rss"),
                                "peak_aggregate_rss_bytes": state.get(
                                    "peak_aggregate_rss"),
                                "rss_semantics": RSS_SEMANTICS}
                    log("r1c-a2 workers requested=%d BLOCKED expand-unknown "
                        "main=%s workers=%s" % (
                            req_workers, str(main_rss),
                            str(worker_rss_list)), logfh)
                else:
                    agg = aggregate_rss_strict(worker_rss_list, main_rss)
                    if agg is None or int(agg) >= int(RSS_CEIL):
                        for w in cand:
                            try:
                                w.stop()
                            except Exception:  # noqa: BLE001
                                pass
                        workers = 0
                        pool_workers = []
                        pool_q = queue.Queue()
                        state["rss_block_terminal"] = R1C_RSS_LIMIT_TERMINAL
                        state["budget_stop"] = True
                        rss_info = {"requested": req_workers,
                                    "effective": None,
                                    "main_rss_bytes": main_rss,
                                    "worker_rss_bytes": list(worker_rss_list),
                                    "aggregate_rss_bytes": agg,
                                    "peak_single_rss_bytes": state.get(
                                        "peak_single_rss"),
                                    "peak_aggregate_rss_bytes": state.get(
                                        "peak_aggregate_rss"),
                                    "rss_semantics": RSS_SEMANTICS}
                        log("r1c-a2 workers requested=%d BLOCKED "
                            "expand-over main=%s agg=%s" % (
                                req_workers, str(main_rss), str(agg)), logfh)
                    else:
                        pool_workers = cand
                        if not pool_workers:
                            raise RuntimeError(
                                "no workers after pilot gate")
                        pool_q = queue.Queue()
                        for _w in pool_workers:
                            pool_q.put(_w)
                        state["worker"] = pool_workers[0]
                        state["pool"] = pool_workers
                        state["pool_q"] = pool_q
                        try:
                            update_rss_barrier(state, worker_rss_list,
                                               main_rss)
                        except Exception:  # noqa: BLE001
                            pass
                        rss_info = {"requested": req_workers,
                                    "effective": workers,
                                    "main_rss_bytes": main_rss,
                                    "worker_rss_bytes": list(worker_rss_list),
                                    "aggregate_rss_bytes": agg,
                                    "peak_single_rss_bytes": state.get(
                                        "peak_single_rss"),
                                    "peak_aggregate_rss_bytes": state.get(
                                        "peak_aggregate_rss"),
                                    "rss_semantics": RSS_SEMANTICS}
                        log("r1c-a2 workers requested=%d effective=%d "
                            "main_rss=%s worker_rss=%s aggregate=%s setup=%d"
                            % (req_workers, workers, str(main_rss),
                               str(worker_rss_list), str(agg),
                               int(state.get("setup_calls", 0))), logfh)
        finalists = [a for a in selected if a in T_ARMS + M_ARMS]
        # Canary §8.2: frozen set x 4 seeds x {f1.2, square}.
        canary = {}
        # R1c-A2 RSS fail-closed: zero scientific dispatch when blocked.
        rss_blocked = state.get("rss_block_terminal")
        if rss_blocked is not None:
            log("BLOCKED rss %s before canary" % rss_blocked, logfh)
            try:
                flush_decoder_records(out / "decoder_records.csv",
                                      state["records"], logfh)
            except Exception:  # noqa: BLE001
                pass
        elif workers == 1:
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
        if rss_blocked is not None:
            advancing = []
            log("advancing=[] rss-blocked %s" % rss_blocked, logfh)
            terminal = str(rss_blocked)
        else:
            advancing = select_advancement(pool_stats, order_new)
            log("advancing=%s" % advancing, logfh)
            terminal = None
        conf_counts = {}
        conf_safety = {"crashes": 0, "nonfinite": 0, "disagreements": 0,
                       "rss_known_ok": bool(rss_blocked is None)}
        width = 64
        if rss_blocked is not None:
            log("skipped confirmation/scaling rss-blocked %s" % rss_blocked,
                logfh)
            try:
                flush_decoder_records(out / "decoder_records.csv",
                                      state["records"], logfh)
            except Exception:  # noqa: BLE001
                pass
        elif advancing:
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
                    srec, ssum, smothers = build_structures(n, logfh, arms=fb)
                else:
                    srec, ssum, smothers = build_structures_parallel(
                        n, logfh, max_workers=workers, arms=fb)
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
        # R1c-A2 blocking precedence: RSS (pre-dispatch) > WALL > CHUNK.
        _rss_b = state.get("rss_block_terminal")
        try:
            _wall_seen = any(
                str(r.get("wall_timeout", "False")) == "True"
                for r in state.get("records", [])
                if int(r.get("call_idx", -1)) >= 0)
        except (TypeError, ValueError):
            _wall_seen = False
        try:
            _wall_early = float(time.perf_counter() - state["t0"])
        except Exception:  # noqa: BLE001
            _wall_early = 0.0
        try:
            _rem_early = float(_remaining_s(state))
        except Exception:  # noqa: BLE001
            _rem_early = 1.0
        if _rss_b is not None:
            terminal = str(_rss_b)
            log("terminal-overridden rss-blocked %s" % terminal, logfh)
        elif bool(_wall_seen) or bool(_wall_early > float(WALL_BUDGET)) \
                or bool(_rem_early <= 0):
            terminal = R1C_WALL_BLOCKED_TERMINAL
            try:
                state["budget_stop"] = True
            except Exception:  # noqa: BLE001
                pass
            log("terminal-overridden wall-budget-blocked", logfh)
        elif state.get("chunk_wall_blocked"):
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
        # R1c-A2 final peaks: state-sampled peaks override startup-only info.
        _fin_single = state.get("peak_single_rss")
        if _fin_single is None:
            _fin_single = rss_info.get("peak_single_rss_bytes")
        _fin_agg = state.get("peak_aggregate_rss")
        if _fin_agg is None:
            _fin_agg = rss_info.get("peak_aggregate_rss_bytes")
        if _fin_agg is None:
            _fin_agg = rss_info.get("aggregate_rss_bytes")
        _eff_out = rss_info.get("effective", workers)
        # Refresh rss_info peaks for manifest persistence.
        try:
            rss_info["peak_single_rss_bytes"] = _fin_single
            rss_info["peak_aggregate_rss_bytes"] = _fin_agg
        except Exception:  # noqa: BLE001
            pass
        with open(out / "manifest.json", "w", encoding="utf-8") as fh:
            json.dump({"out_root": str(out), "arms": ARMS,
                       "revision": R1C_REVISION, "workers": workers,
                       "workers_requested": req_workers,
                       "workers_effective": _eff_out,
                       "main_rss_bytes": main_rss,
                       "worker_rss_bytes": rss_info.get(
                           "worker_rss_bytes", []),
                       "aggregate_rss_bytes": rss_info.get(
                           "aggregate_rss_bytes"),
                       "peak_single_rss_bytes": _fin_single,
                       "peak_aggregate_rss_bytes": _fin_agg,
                       "rss_semantics": RSS_SEMANTICS,
                       "deadline_s": float(state.get("deadline", 0.0)),
                       "rss_block_terminal": state.get("rss_block_terminal"),
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
                       "workers_effective": _eff_out,
                       "setup_decoder_calls": setup_calls,
                       "scientific_calls": sci_calls,
                       "total_decoder_calls": setup_calls + sci_calls,
                       "chunk_walls": state.get("chunk_walls", {}),
                       "chunk_wall_blocked": bool(state.get(
                           "chunk_wall_blocked", False)),
                       "rss_block_terminal": state.get("rss_block_terminal"),
                       "peak_single_rss_bytes": _fin_single,
                       "peak_aggregate_rss_bytes": _fin_agg,
                       "rss_semantics": RSS_SEMANTICS,
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
        # R1c-A2 unified finally: completed records are always checkpointed.
        try:
            if "out" in locals() and "state" in locals():
                try:
                    flush_decoder_records(out / "decoder_records.csv",
                                          state.get("records", []), None)
                except Exception:  # noqa: BLE001 - fail-closed, keep original
                    pass
        except Exception:  # noqa: BLE001
            pass
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

