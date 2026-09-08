"""D6 development runner — frozen §8 pipeline: structure freeze, blind selection,
canary, confirmation/scaling, scalar evidence. Explicit injection only.

One fresh UUID root per run; refuses to overwrite. Scalar/metadata evidence
only (no symbols, priors, beliefs, matrices persisted). One decoder invocation
per frozen cell, no retries. Watchdog: dedicated respawnable worker process
(120 s per invocation, pids logged).
"""
import argparse
import csv
import json
import multiprocessing as mp
import os
import pathlib
import subprocess
import sys
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
    # Warmup (setup only, never counted): compile the decoder on a tiny
    # fixture so no frozen cell absorbs compile time.
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


class Worker:
    """Dedicated respawnable decoder worker; exactly one task-owned process."""

    def __init__(self, logfh):
        self.logfh = logfh
        self.pids = []
        self.proc = None
        self.conn = None
        self.spawn(reason="initial")

    def spawn(self, reason):
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
    """Count one budgeted invocation (or a skipped-APP placeholder)."""
    if skip:
        return {"call_idx": -1, "arm": meta["arm"], "n": meta["n"],
                "seed": meta["seed"], "point": meta["point"],
                "rows_l1": meta["r1"], "rows_l2": meta["r2"], "mode": mode,
                "matrix_id": meta["matrix_id"], "exact": False,
                "syndrome_ok": False, "iterations": -1, "finite": False,
                "crash": True, "timeout": False, "prior_mass_on_truth": tm,
                "wall_s": 0.0, "rss_bytes": "", "watchdog_ok": True,
                "worker_pid": "", "note": "app-undefined-l1-unavailable"}
    if not (state["calls"] + 1 <= CALL_BUDGET
            and time.perf_counter() - state["t0"] <= WALL_BUDGET):
        state["budget_stop"] = True
        raise StopIteration("budget-exhausted")
    task = {"h": np.asarray(h, dtype=np.uint8),
            "prior": np.asarray(prior, dtype=np.float64),
            "x_true": np.asarray(xt, dtype=np.int64),
            "return_beliefs": bool(ret_bel)}
    res = worker.call(task)
    state["calls"] += 1
    rss = res.get("rss")
    if rss is not None and rss > state["peak_rss"]:
        state["peak_rss"] = int(rss)
    wall = float(res.get("wall_s", 0.0))
    rec = {"call_idx": state["calls"], "arm": meta["arm"], "n": meta["n"],
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
            "worker_pid": state["worker"].pids[-1],
            "beliefs": res.get("beliefs")}
    state["records"].append(rec)
    return rec


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
    check("call-count",
          len(counted) == int(summ["calls"]) and len(counted) <= 2500,
          "csv=%d summary=%d" % (len(counted), summ["calls"]))
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
    if per_f is not None and len(summ["advancing"]) == 1 \
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
    state = {"calls": 0, "t0": time.perf_counter(), "records": [],
             "peak_rss": 0, "budget_stop": False, "worker": None}
    try:
        # T9: structure + blind freeze (no decoder before this freeze).
        records, summary, mothers = build_structures(64, logfh)
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
        worker = Worker(logfh)
        state["worker"] = worker
        finalists = [a for a in selected if a in T_ARMS + M_ARMS]
        # Canary §8.2: frozen set x 4 seeds x {f1.2, square}.
        canary = {}
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
            try:
                for arm in advancing:
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
                log("confirmation=%s safety=%s" % (
                    conf_counts, conf_safety), logfh)
            except StopIteration as ex:
                log("STOP %s" % ex, logfh)
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
                srec, ssum, smothers = build_structures(n, logfh)
                with open(out / "structure_records.csv", "a", newline="",
                           encoding="utf-8") as fh:
                    w = csv.DictWriter(fh, fieldnames=list(srec[0].keys()))
                    w.writerows(srec)
                order_n = structural_rank_list(ssum, fb)
                sig = {}
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
                advancing = select_advancement(sig, order_n)
                if advancing:
                    width = n
                    try:
                        for arm in advancing:
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
                    except StopIteration as ex:
                        log("STOP %s" % ex, logfh)
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
        itmax = max([int(r["iterations"]) for r in state["records"]
                     if int(r["call_idx"]) >= 0] or [0])
        worker.stop()
        with open(out / "decoder_records.csv", "w", newline="",
                   encoding="utf-8") as fh:
            keys = ["call_idx", "arm", "n", "seed", "point", "rows_l1",
                    "rows_l2", "mode", "matrix_id", "exact", "syndrome_ok",
                    "iterations", "finite", "crash", "timeout",
                    "prior_mass_on_truth", "wall_s", "rss_bytes",
                    "watchdog_ok", "worker_pid"]
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            for r in state["records"]:
                w.writerow({k: r.get(k, "") for k in keys})
        try:
            head = subprocess.run(
                ["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                cwd=str(ROOT)).stdout.strip()
        except Exception:  # noqa: BLE001
            head = "unknown"
        wall = time.perf_counter() - state["t0"]
        with open(out / "manifest.json", "w", encoding="utf-8") as fh:
            json.dump({"out_root": str(out), "arms": ARMS,
                       "canary_seeds": list(CANARY_SEEDS),
                       "confirmation_seeds": list(CONF_SEEDS),
                       "scaling_seeds": list(SCALING_SEEDS),
                       "budgets": {"calls": CALL_BUDGET,
                                   "wall_s": WALL_BUDGET,
                                   "watchdog_s": WATCHDOG,
                                   "rss_bytes": RSS_CEIL},
                       "calls": state["calls"], "wall_s": wall,
                       "peak_rss_bytes": state["peak_rss"],
                       "worker_pids": worker.pids,
                       "head_sha": head,
                       "budget_stop": state["budget_stop"],
                       "oracle_never_upgrades_exact": True}, fh, indent=2)
        with open(out / "summary.json", "w", encoding="utf-8") as fh:
            json.dump({"selected": selected, "canary": canary,
                       "advancing": advancing,
                       "confirmation_counts": conf_counts,
                       "confirmation_safety": conf_safety,
                       "confirmation_width": width, "terminal": terminal,
                       "calls": state["calls"], "wall_s": wall,
                       "iterations_max": itmax,
                       "peak_rss_bytes": state["peak_rss"],
                       "budget_stop": state["budget_stop"],
                       "oracle_never_upgrades_exact": True}, fh, indent=2)
        log("done terminal=%s calls=%d wall=%.1f peak_rss=%d" % (
            terminal, state["calls"], wall, state["peak_rss"]), logfh)
    finally:
        try:
            if state.get("worker") is not None:
                state["worker"].stop()
        except Exception:  # noqa: BLE001
            pass
        logfh.close()


if __name__ == "__main__":
    mp.freeze_support()
    main()

