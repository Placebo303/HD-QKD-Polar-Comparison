"""D5 L1 discriminator Phase D: paired n64 L1 frontier (dev only).

Decoder set {E2 winner, E1 baseline} per prereg (winner E2, E1 runner-up
contrast). Blocks sampled once per seed under the E1 joint law (the D4-family
population both estimators describe); only the L1 prior fed to the decoder
changes -- single estimator axis. (E2 is L1-only and defines no joint law;
same-population prior-only contrast; disclosed in final report.)
Mothers/decoder/seeds/disclosures per prereg. No VAL, no formal-root write.
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

spec = importlib.util.spec_from_file_location("v72p2d5_core_l1d", str(CORE_PATH))
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

WATCHDOG = 120
t_all = time.perf_counter()
ev = {"phase": "D-n64", "decoder_calls": 0, "watchdog_s": WATCHDOG,
      "diagnostics": []}
peak_rss = 0


def rss():
    global peak_rss
    v = core._rss_bytes()
    if v is not None and v > peak_rss:
        peak_rss = v
    return v


c1 = json.loads((OUT / "c1_evidence.json").read_text(encoding="utf-8"))
assert c1["winner"] == "E2", c1["winner"]
KAP = float(c1["E2_kap_use"])
LAM = float(core.LAMBDA_STAR)
ev["kap_star"] = KAP
ev["lam_star"] = LAM

# ---- mothers ----
h1 = core.build_dv3_nested_mother(64, 59, 59, int(core.L1_GRAPH_SEED), None)
H1_49 = np.asarray(h1[:49], dtype=np.int64)
H1_59 = np.asarray(h1[:59], dtype=np.int64)
H_SQ = np.asarray(core.build_dv3_nested_mother(64, 64, 64, 2026090801, None),
                  dtype=np.int64)
assert core._gf32_rank(H_SQ) == 64
ev["mothers"] = {"H1_family": "build_dv3_nested_mother(64,59,59,2026090501)",
                 "square": "build_dv3_nested_mother(64,64,64,2026090801)",
                 "square_rank": 64}

# ---- priors ----
npz = np.load(REPO / "workspace/v72p2d5_model_f_input/20260907_r1/model_f_input.npz")
counts = np.asarray(npz["counts_ab"], dtype=np.float64)
pb = np.asarray(npz["p_b"], dtype=np.float64)
pb /= pb.sum()
n_b = counts.sum(axis=0)
p_global = counts.sum(axis=1) / float(counts.sum())
pf_e1 = (counts + LAM * p_global[:, None]) / (n_b[None, :] + LAM)
p1_e1 = np.asarray(core.marginalize_f_to_p1(pf_e1), dtype=np.float64)  # [U1,B]
cnt1 = counts.reshape(32, 32, 1024).sum(axis=1).T  # [B,U1]
n_b1 = cnt1.sum(axis=1)
p_g1 = cnt1.sum(axis=0) / float(counts.sum())
p1_e2 = np.asarray((cnt1 + KAP * p_g1[None, :]) / (n_b1[:, None] + KAP),
                   dtype=np.float64)  # [B,U1]
PRIORS = {"E1": p1_e1.T, "E2": p1_e2}  # both [B,U1]

dec = core.bind_historical_decoder()
ev["decoder"] = "bind_historical_decoder (GF32 cold, max_iter 90)"
SEEDS = [2026090600, 2026090601, 2026090602, 2026090603]


def call(h, prior, syn):
    t0 = time.perf_counter()
    res = dec(np.asarray(h), np.asarray(prior, dtype=np.float64),
              np.asarray(syn))
    return res, time.perf_counter() - t0


def rec(tag, est, res, wall, xt, h, syn, tm):
    xh = np.asarray(res["x_hat"], dtype=np.int64).ravel()
    exact_re = bool(np.array_equal(xh, xt))
    syn_re = bool(np.array_equal(core._gf32_syndrome(np.asarray(h), xh),
                                 np.asarray(syn)))
    bel = np.asarray(res["final_beliefs"], dtype=np.float64)
    ev["decoder_calls"] += 1
    ev["diagnostics"].append({
        "id": tag, "estimator": est, "decoder_calls": 1,
        "exact_recomputed": exact_re,
        "syndrome_recomputed": syn_re,
        "syndrome_decoder_flag": bool(res["syndrome_ok"]),
        "flag_agree": bool(syn_re == bool(res["syndrome_ok"])),
        "iterations": int(res["iterations"]),
        "nonfinite": bool(not np.all(np.isfinite(bel))),
        "prior_mass_on_truth": tm,
        "wall_s": wall, "rss_bytes": rss(),
        "watchdog_ok": bool(wall <= WATCHDOG)})


# S0 delta sanity on the square mother (signal-sufficiency check)
xrng = np.random.default_rng(2026090701)
xt0 = xrng.integers(0, 32, size=(64,)).astype(np.int64)
syn0 = core._gf32_syndrome(H_SQ, xt0)
pr0 = np.full((64, 32), 1e-15)
pr0[np.arange(64), xt0] = 1.0
pr0 = pr0 / pr0.sum(axis=1, keepdims=True)
res0, w0 = call(H_SQ, pr0, syn0)
rec("S0-DELTA-L1@Hsq[:64]", "delta", res0, w0, xt0, H_SQ, syn0, 1.0)

# Paired frontier: same E1-law blocks for both estimators (prior-only axis)
for sd in SEEDS:
    blk = core.sample_matched_block(pb, pf_e1, 64, sd)
    for est in ("E2", "E1"):
        p1 = PRIORS[est]
        for tag, h in (("H1[:49]", H1_49), ("H1[:59]", H1_59),
                       ("Hsq[:64]", H_SQ)):
            pr = np.maximum(np.asarray(p1, dtype=np.float64)[blk["bob"], :],
                            core.DECODER_FLOOR)
            pr = pr / pr.sum(axis=1, keepdims=True)
            tm = float(np.mean(pr[np.arange(64), blk["u1"]]))
            syn = core._gf32_syndrome(np.asarray(h), blk["u1"])
            res, wall = call(h, pr, syn)
            rec("%s-L1-%s@%d" % (est, tag, sd), est, res, wall, blk["u1"],
                h, syn, tm)

ev["wall_s"] = time.perf_counter() - t_all
ev["peak_rss_bytes"] = peak_rss
(OUT / "d2_evidence.json").write_text(json.dumps(ev, indent=2) + "\n",
                                      encoding="utf-8")
for d in ev["diagnostics"]:
    print(d["id"], "exact", d["exact_recomputed"], "syn",
          d["syndrome_recomputed"], "iters", d["iterations"], "tmass",
          round(d["prior_mass_on_truth"], 4), "wall", round(d["wall_s"], 3))
print("Phase D-n64 calls", ev["decoder_calls"], "wall", round(ev["wall_s"], 1),
      "peak_rss", peak_rss)
