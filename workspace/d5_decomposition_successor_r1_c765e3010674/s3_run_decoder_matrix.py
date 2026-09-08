"""D5 decomposition successor S3: fixed paired development decoder matrix.

Requires selected_partitions.json (refuses otherwise). Explicit injection
only: accepted R2 candidate priors transformed per partition, fixed paired
seeds, preregistered rows, deterministic mothers, historical GF32 decoder
cold start max_iter=90 damping=1.0. Writes decoder_records.csv (scalars
only) + appends command_log.txt. Cell visit-once, no retries.
"""
import importlib.util
import json
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
CORE_PATH = (REPO / "comparison_bench/src/comparison_bench/formal_ir"
             / "v72p2d5_gf32_rate_mother.py")

spec = importlib.util.spec_from_file_location("v72p2d5_core_d5s3", str(CORE_PATH))
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

LOG = ROOT / "command_log.txt"
SEL = ROOT / "selected_partitions.json"
assert SEL.exists(), "selection manifest missing: decoder calls refused"
sel = json.loads(SEL.read_text(encoding="utf-8"))

WATCHDOG = 120
CALL_BUDGET = 600
WALL_BUDGET = 6 * 3600
RSS_CEIL = 2 * 1024 ** 3


def log(msg):
    line = "%s %s" % (time.strftime("%Y-%m-%dT%H:%M:%S"), msg)
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def pack(a, bits):
    out = np.zeros(np.asarray(a).shape, dtype=np.int64)
    a = np.asarray(a, dtype=np.int64)
    for j, b in enumerate(bits):
        out |= ((a >> b) & 1) << j
    return out


t_all = time.perf_counter()
peak_rss = 0
calls = 0
recs = []


def rss():
    global peak_rss
    v = core._rss_bytes()
    if v is not None and v > peak_rss:
        peak_rss = v
    return v


npz = np.load(REPO / "workspace/v72p2d5_model_f_input/20260907_r1/model_f_input.npz")
counts0 = np.asarray(npz["counts_ab"], dtype=np.float64)
pb0 = np.asarray(npz["p_b"], dtype=np.float64)
pb0 /= pb0.sum()

M1, M2 = int(sel["mothers"]["M1"]), int(sel["mothers"]["M2"])
H1M = np.asarray(core.build_dv3_nested_mother(64, M1, M1, int(core.L1_GRAPH_SEED), None),
                dtype=np.int64)
H2M = np.asarray(core.build_dv3_nested_mother(64, M2, M2, int(core.L2_GRAPH_SEED), None),
                dtype=np.int64)
H_SQ = np.asarray(core.build_dv3_nested_mother(64, 64, 64, 2026090801, None), dtype=np.int64)
assert core._gf32_rank(H_SQ) == 64
log("S3 mothers L1(64,%d,%d) L2(64,%d,%d) square-rank-64 decoder=bind_historical_decoder" % (M1, M1, M2, M2))

dec = core.bind_historical_decoder()
ALL_A = np.arange(1024, dtype=np.int64)

for entry in sel["selected"]:
    s1 = tuple(int(b) for b in entry["s1"].split("-"))
    s2 = tuple(b for b in range(10) if b not in s1)
    amap = pack(ALL_A, s1) * 32 + pack(ALL_A, s2)  # original a -> transformed ua
    tcounts = np.zeros_like(counts0)
    tcounts[amap, :] = counts0[ALL_A, :]
    pb, pf = core.prepare_model_f_prior_candidate(tcounts, pb0)
    p1 = np.asarray(core.marginalize_f_to_p1(pf), dtype=np.float64)  # [U1,B]
    p2 = np.asarray(core.conditionalize_f_to_p2(pf), dtype=np.float64)  # [U1,B,U2]
    m1, m2 = int(entry["m1"]), int(entry["m2"])
    geoms = []
    if bool(entry["eligible"]):
        geoms.append(("nonsquare", np.asarray(H1M[:m1]), np.asarray(H2M[:m2]), m1, m2))
    else:
        log("S3 %s NONZERO_RATE_INELIGIBLE m=(%d,%d): square diagnostic only" % (entry["s1"], m1, m2))
    geoms.append(("square", H_SQ, H_SQ, 64, 64))
    for seed in sel["seeds"]:
        blk = core.sample_matched_block(pb, pf, 64, seed)
        assert bool(np.array_equal(pack(blk["alice"], (5, 6, 7, 8, 9)), blk["u1"]))
        u1t = pack(blk["alice"], s1)
        u2t = pack(blk["alice"], s2)
        bob = blk["bob"]
        for geom, h1, h2, r1, r2 in geoms:
            # L1
            pr1 = core._floor_renorm(p1[:, bob].T, core.DECODER_FLOOR)
            tm1 = float(np.mean(pr1[np.arange(64), u1t]))
            syn1 = core._gf32_syndrome(h1, u1t)
            r1res = None  # reset per cell: stale L1 beliefs must never propagate
            # APP L2 needs L1 beliefs first; run L1 then APP then oracle
            for mode in ("L1", "L2-APP", "L2-oracle"):
                assert calls < CALL_BUDGET, "call budget exhausted"
                assert (time.perf_counter() - t_all) < WALL_BUDGET, "wall budget exhausted"
                t0 = time.perf_counter()
                try:
                    if mode == "L1":
                        res = dec(np.asarray(h1), np.asarray(pr1), np.asarray(syn1))
                        xt, h, syn, tm = u1t, h1, syn1, tm1
                    elif mode == "L2-APP":
                        if r1res is None:
                            raise RuntimeError("L1 beliefs unavailable; APP undefined")
                        bel = np.asarray(r1res["final_beliefs"], dtype=np.float64)
                        zz = bel - bel.max(axis=1, keepdims=True)
                        ee = np.exp(zz)
                        q = ee / ee.sum(axis=1, keepdims=True)
                        pr2 = core.app_fed_l2_prior(p2, bob, q)
                        tm = float(np.mean(pr2[np.arange(64), u2t]))
                        res = dec(np.asarray(h2), np.asarray(pr2),
                                  np.asarray(core._gf32_syndrome(h2, u2t)))
                        xt, h, syn = u2t, h2, core._gf32_syndrome(h2, u2t)
                    else:
                        pr2o = core.oracle_l2_prior(p2, bob, u1t)
                        tm = float(np.mean(pr2o[np.arange(64), u2t]))
                        res = dec(np.asarray(h2), np.asarray(pr2o),
                                  np.asarray(core._gf32_syndrome(h2, u2t)))
                        xt, h, syn = u2t, h2, core._gf32_syndrome(h2, u2t)
                    wall = time.perf_counter() - t0
                    xh = np.asarray(res["x_hat"], dtype=np.int64).ravel()
                    exact = bool(np.array_equal(xh, xt))
                    syn_re = bool(np.array_equal(core._gf32_syndrome(np.asarray(h), xh),
                                                np.asarray(syn)))
                    flag = bool(res["syndrome_ok"])
                    bel2 = np.asarray(res["final_beliefs"], dtype=np.float64)
                    nf = bool(not np.all(np.isfinite(bel2)))
                    it = int(res["iterations"])
                    crash = False
                    if mode == "L1":
                        r1res = res
                except Exception as ex:
                    wall = time.perf_counter() - t0
                    exact, syn_re, flag, it, nf, tm = False, False, False, -1, False, float("nan")
                    crash = True
                    log("S3 CRASH %s seed=%d %s %s: %r" % (entry["s1"], seed, geom, mode, ex))
                calls += 1
                recs.append({"partition": entry["s1"], "seed": seed, "geometry": geom,
                             "mode": mode, "rows_l1": r1, "rows_l2": r2,
                             "exact": exact, "syndrome_recomputed": syn_re,
                             "syndrome_decoder_flag": flag,
                             "flag_agree": bool(syn_re == flag),
                             "iterations": it, "nonfinite": nf, "crash": crash,
                             "prior_mass_on_truth": tm, "wall_s": wall,
                             "rss_bytes": rss(), "watchdog_ok": bool(wall <= WATCHDOG)})
    log("S3 partition %s done calls_so_far=%d" % (entry["s1"], calls))

import csv
with open(ROOT / "decoder_records.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(recs[0].keys()))
    w.writeheader()
    w.writerows(recs)
wall = time.perf_counter() - t_all
log("S3 done calls=%d/600 wall_s=%.1f/21600 peak_rss=%s unknown_rss=%s" % (
    calls, wall, peak_rss, any(r["rss_bytes"] is None for r in recs)))
