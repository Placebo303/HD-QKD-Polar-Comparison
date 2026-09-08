"""R2 W4c: C1-prior disclosure frontier bisect (dev only).

C1-L1 @ {H1[:49], H1[:59], Hsq[:64]} x 4 seeds = 12 calls;
C1-oracle-L2 @ H2[:52] x 4 seeds = 4 calls. Total 16.
Same square mother (seed 2026090801) reused for the L1 square point (recorded).
Paired block seeds 2026090600..03. No CLI --phase, no VAL, no formal write.
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

spec = importlib.util.spec_from_file_location("v72p2d5_core_w4c", str(CORE_PATH))
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

WATCHDOG = 120
t_all = time.perf_counter()
ev = {"workstream": "W4c", "decoder_calls": 0, "watchdog_s": WATCHDOG,
      "diagnostics": []}
peak_rss = 0


def rss():
    global peak_rss
    v = core._rss_bytes()
    if v is not None and v > peak_rss:
        peak_rss = v
    return v


h1 = core.build_dv3_nested_mother(64, core.G1_L1_K_MIN, core.G1_L1_K_MIN,
                                  core.L1_GRAPH_SEED, None)
h2 = core.build_dv3_nested_mother(64, core.G1_L2_K_MIN, core.G1_L2_K_MIN,
                                  core.L2_GRAPH_SEED, None)
H1_49 = np.asarray(h1[:49], dtype=np.int64)
H1_59 = np.asarray(h1[:59], dtype=np.int64)
H2_52 = np.asarray(h2[:52], dtype=np.int64)
H_SQ = np.asarray(core.build_dv3_nested_mother(64, 64, 64, 2026090801, None),
                  dtype=np.int64)

npz = np.load(REPO / "workspace/v72p2d5_model_f_input/20260907_r1/model_f_input.npz")
counts = np.asarray(npz["counts_ab"], dtype=np.float64)
pb = np.asarray(npz["p_b"], dtype=np.float64)
pb /= pb.sum()
LAM = float(core.LAMBDA_STAR)
n_b = counts.sum(axis=0)
p_global = counts.sum(axis=1) / float(counts.sum())
pf1 = (counts + LAM * p_global[:, None]) / (n_b[None, :] + LAM)
_, _, _, p1_1, p2_1 = core._ce_stats(pf1, pb)
dec = core.bind_historical_decoder()
seeds = [2026090600, 2026090601, 2026090602, 2026090603]


def call(h, prior, syn):
    t0 = time.perf_counter()
    res = dec(np.asarray(h), np.asarray(prior, dtype=np.float64),
              np.asarray(syn))
    return res, time.perf_counter() - t0


def rec(dd, res, wall, xt):
    ev["decoder_calls"] += 1
    ev["diagnostics"].append({
        "id": dd["id"], "decoder_calls": 1, "block_seed": dd.get("seed"),
        "changed_axis": dd["axis"], "input": dd["input"],
        "prior_mass_on_truth": dd.get("tmass"),
        "exact": bool(np.array_equal(np.asarray(res["x_hat"]).ravel(), xt)),
        "syndrome_ok": bool(res["syndrome_ok"]),
        "iterations": int(res["iterations"]),
        "nonfinite": bool(not np.all(np.isfinite(
            np.asarray(res["final_beliefs"], dtype=np.float64)))),
        "wall_s": wall, "rss_bytes": rss(),
        "watchdog_ok": bool(wall <= WATCHDOG)})


for sd in seeds:
    blk = core.sample_matched_block(pb, pf1, 64, sd)
    # L1 points with C1-P1
    for tag, h in (("H1[:49]", H1_49), ("H1[:59]", H1_59),
                   ("Hsq[:64]", H_SQ)):
        pr1 = core._floor_renorm(p1_1[:, blk["bob"]].T, core.DECODER_FLOOR)
        tm = float(np.mean(pr1[np.arange(64), blk["u1"]]))
        res, wall = call(h, pr1, core._gf32_syndrome(h, blk["u1"]))
        rec({"id": f"C1-L1-{tag}@{sd}", "seed": sd,
             "axis": "rows only (C1 prior fixed)",
             "input": f"C1 block {sd}, L1 prior, {tag}", "tmass": tm},
            res, wall, blk["u1"])
    # oracle-L2 at f=1.2 frozen rows
    po = core.oracle_l2_prior(p2_1, blk["bob"], blk["u1"])
    tm = float(np.mean(po[np.arange(64), blk["u2"]]))
    res, wall = call(H2_52, po, core._gf32_syndrome(H2_52, blk["u2"]))
    rec({"id": f"C1-ORACLE-H2[:52]@{sd}", "seed": sd,
         "axis": "rows only (C1 prior fixed; f=1.0 -> f=1.2 frozen)",
         "input": f"C1 block {sd}, oracle-L2, H2[:52]", "tmass": tm},
        res, wall, blk["u2"])

ev["wall_s"] = time.perf_counter() - t_all
ev["peak_rss_bytes"] = peak_rss
(OUT / "w4c_evidence.json").write_text(json.dumps(ev, indent=2) + "\n",
                                       encoding="utf-8")
for d in ev["diagnostics"]:
    print(d["id"], "exact", d["exact"], "syn", d["syndrome_ok"],
          "iters", d["iterations"], "tmass", round(d["prior_mass_on_truth"], 4))
print("W4c calls", ev["decoder_calls"], "wall", round(ev["wall_s"], 1),
      "peak_rss", peak_rss)
