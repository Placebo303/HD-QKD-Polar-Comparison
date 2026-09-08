"""R2 W4b: paired decoder matrix, corrected (C1) vs accepted (C0) priors (dev only).

C0 points reused from R1 F2/F3 + W2 square (no repeat calls). New calls: C1
oracle-L2 x 4 paired seeds x {H2[:43] frozen, Hsq[:64] square} = 16, plus C1
APP layered path x 4 seeds at frozen f=1.0 rows = 8. Total 24.
Paired samples share block seeds 2026090600..03. No CLI --phase, no VAL,
no formal-root write.
"""
import importlib.util
import json
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
CORE_PATH = (REPO / "comparison_bench/src/comparison_bench/formal_ir"
             / "v72p2d5_gf32_rate_mother.py")

spec = importlib.util.spec_from_file_location("v72p2d5_core_w4b", str(CORE_PATH))
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

WATCHDOG = 120
t_all = time.perf_counter()
ev = {"workstream": "W4b", "decoder_calls": 0, "watchdog_s": WATCHDOG,
      "diagnostics": []}
peak_rss = 0


def rss():
    global peak_rss
    v = core._rss_bytes()
    if v is not None and v > peak_rss:
        peak_rss = v
    return v


# ---- mothers (deterministic rebuilds) ----
h2 = core.build_dv3_nested_mother(64, core.G1_L2_K_MIN, core.G1_L2_K_MIN,
                                  core.L2_GRAPH_SEED, None)
h1 = core.build_dv3_nested_mother(64, core.G1_L1_K_MIN, core.G1_L1_K_MIN,
                                  core.L1_GRAPH_SEED, None)
H1_49 = np.asarray(h1[:49], dtype=np.int64)
H2_43 = np.asarray(h2[:43], dtype=np.int64)
h_sq = core.build_dv3_nested_mother(64, 64, 64, 2026090801, None)
H_SQ = np.asarray(h_sq, dtype=np.int64)
assert core._gf32_rank(H_SQ) == 64

# ---- priors: C0 accepted, C1 backoff (same counts, same lam) ----
npz = np.load(REPO / "workspace/v72p2d5_model_f_input/20260907_r1/model_f_input.npz")
counts = np.asarray(npz["counts_ab"], dtype=np.float64)
pb = np.asarray(npz["p_b"], dtype=np.float64)
pb /= pb.sum()
LAM = float(core.LAMBDA_STAR)
pf0 = core.build_f_model(counts, LAM)
n_b = counts.sum(axis=0)
p_global = counts.sum(axis=1) / float(counts.sum())
pf1 = (counts + LAM * p_global[:, None]) / (n_b[None, :] + LAM)
_, _, _, _, p2_0 = core._ce_stats(pf0, pb)
_, _, _, p1_1, p2_1 = core._ce_stats(pf1, pb)

dec = core.bind_historical_decoder()
seeds = [2026090600, 2026090601, 2026090602, 2026090603]


def call(h, prior, syn):
    t0 = time.perf_counter()
    res = dec(np.asarray(h), np.asarray(prior, dtype=np.float64),
              np.asarray(syn))
    return res, time.perf_counter() - t0


for sd in seeds:
    blk0 = core.sample_matched_block(pb, pf0, 64, sd)
    blk1 = core.sample_matched_block(pb, pf1, 64, sd)
    # C1 oracle-L2 at frozen rows (paired sample under C1 law)
    po1 = core.oracle_l2_prior(p2_1, blk1["bob"], blk1["u1"])
    tm = float(np.mean(po1[np.arange(64), blk1["u2"]]))
    res, wall = call(H2_43, po1, core._gf32_syndrome(H2_43, blk1["u2"]))
    ev["decoder_calls"] += 1
    ev["diagnostics"].append({
        "id": f"C1-ORACLE-FROZEN@{sd}", "decoder_calls": 1, "block_seed": sd,
        "changed_axis": "prior only (C0 accepted -> C1 backoff); rows frozen",
        "input": "C1 block seed %d, oracle-L2, H2[:43]" % sd,
        "prior_mass_on_truth": tm,
        "exact": bool(np.array_equal(np.asarray(res["x_hat"]).ravel(),
                                     blk1["u2"])),
        "syndrome_ok": bool(res["syndrome_ok"]),
        "iterations": int(res["iterations"]),
        "nonfinite": bool(not np.all(np.isfinite(
            np.asarray(res["final_beliefs"], dtype=np.float64)))),
        "wall_s": wall, "rss_bytes": rss(),
        "watchdog_ok": bool(wall <= WATCHDOG)})
    # C1 oracle-L2 at square disclosure
    res, wall = call(H_SQ, po1, core._gf32_syndrome(H_SQ, blk1["u2"]))
    ev["decoder_calls"] += 1
    ev["diagnostics"].append({
        "id": f"C1-ORACLE-SQUARE@{sd}", "decoder_calls": 1, "block_seed": sd,
        "changed_axis": "prior + mother (C1, H2[:43] -> Hsq[:64])",
        "input": "C1 block seed %d, oracle-L2, Hsq[:64]" % sd,
        "prior_mass_on_truth": tm,
        "exact": bool(np.array_equal(np.asarray(res["x_hat"]).ravel(),
                                     blk1["u2"])),
        "syndrome_ok": bool(res["syndrome_ok"]),
        "iterations": int(res["iterations"]),
        "nonfinite": bool(not np.all(np.isfinite(
            np.asarray(res["final_beliefs"], dtype=np.float64)))),
        "wall_s": wall, "rss_bytes": rss(),
        "watchdog_ok": bool(wall <= WATCHDOG)})
    # C1 full APP layered path at frozen f=1.0 rows
    prior_l1 = core._floor_renorm(p1_1[:, blk1["bob"]].T, core.DECODER_FLOOR)
    r1, w1 = call(H1_49, prior_l1, core._gf32_syndrome(H1_49, blk1["u1"]))
    ev["decoder_calls"] += 1
    xh1 = np.asarray(r1["x_hat"], dtype=np.int64).ravel()
    e1 = bool(np.array_equal(xh1, blk1["u1"]))
    bel = np.asarray(r1["final_beliefs"], dtype=np.float64)
    zz = bel - bel.max(axis=1, keepdims=True)
    ee = np.exp(zz)
    q = ee / ee.sum(axis=1, keepdims=True)
    prior_l2 = core.app_fed_l2_prior(p2_1, blk1["bob"], q)
    r2, w2 = call(H2_43, prior_l2, core._gf32_syndrome(H2_43, blk1["u2"]))
    ev["decoder_calls"] += 1
    xh2 = np.asarray(r2["x_hat"], dtype=np.int64).ravel()
    e2 = bool(np.array_equal(xh2, blk1["u2"]))
    ev["diagnostics"].append({
        "id": f"C1-APP-FROZEN@{sd}", "decoder_calls": 2, "block_seed": sd,
        "changed_axis": "prior only (C0 -> C1); full APP layered path",
        "input": "C1 block seed %d, APP L1 H1[:49] + APP-fed L2 H2[:43]" % sd,
        "l1_exact": e1, "exact": bool(e1 and e2),
        "syndrome_ok": bool(res["syndrome_ok"] and r2["syndrome_ok"]),
        "iterations": int(r1["iterations"]) + int(r2["iterations"]),
        "nonfinite": bool(not (np.all(np.isfinite(bel)) and np.all(
            np.isfinite(np.asarray(r2["final_beliefs"], dtype=np.float64))))),
        "wall_s": w1 + w2, "rss_bytes": rss(),
        "watchdog_ok": bool(max(w1, w2) <= WATCHDOG)})

ev["c0_reference"] = {
    "APP frozen 49/43": "0/4 exact (R1 F2a)",
    "oracle H2[:43]": "0/4 exact (R1 F2b)",
    "oracle H2[:52]": "0/4 exact (R1 F3)",
    "oracle Hsq[:64]": "0/4 exact (R2 W2 S1..S4)",
}
ev["wall_s"] = time.perf_counter() - t_all
ev["peak_rss_bytes"] = peak_rss
(OUT / "w4b_evidence.json").write_text(json.dumps(ev, indent=2) + "\n",
                                       encoding="utf-8")
for d in ev["diagnostics"]:
    print(d["id"], "exact", d["exact"], "syn", d["syndrome_ok"],
          "iters", d["iterations"], "wall", round(d["wall_s"], 3))
print("W4b calls", ev["decoder_calls"], "wall", round(ev["wall_s"], 1),
      "peak_rss", peak_rss)
