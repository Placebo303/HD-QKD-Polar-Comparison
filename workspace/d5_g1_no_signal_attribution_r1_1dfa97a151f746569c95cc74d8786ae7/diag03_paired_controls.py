"""D5-G1 attribution R1 — batch 3: AC05 nontrivial machinery + AC06 paired controls.

F1 (AC05b, nontrivial): decoy-peaked priors force real BP iterations on each
    frozen prefix; convergence proves graph+decoder machinery works.
F2 (AC06 prior axis, paired): 4 deterministic Model-F blocks (first 4 formal
    seeds, same sample/seed within pair); APP-layered vs oracle-L2, frozen rows.
F3 (AC06 rows axis, paired): same 4 blocks, oracle prior, frozen H2[:43] vs
    stronger full-disclosure H2[:52] control (f=1.0).
F4 (AC06 cap axis): 1 block, oracle, frozen prefix, max_iter 90 vs 180 control.

Direct injected decoder calls only. No CLI phase, no formal-root write.
"""
import importlib.util
import json
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CORE_PATH = (REPO / "comparison_bench/src/comparison_bench/formal_ir"
             / "v72p2d5_gf32_rate_mother.py")
OUT = Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location("v72p2d5_core_diag3", str(CORE_PATH))
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

import numpy as np  # noqa: E402

_rss = core._rss_bytes
t_all = time.perf_counter()
ev = {"batch": 3, "decoder_calls": 0, "watchdog_s": 120, "diagnostics": []}

h1 = core.build_dv3_nested_mother(64, core.G1_L1_K_MIN, core.G1_L1_K_MIN,
                                  core.L1_GRAPH_SEED, None)
h2 = core.build_dv3_nested_mother(64, core.G1_L2_K_MIN, core.G1_L2_K_MIN,
                                  core.L2_GRAPH_SEED, None)
H1_49 = np.asarray(h1[:49], dtype=np.int64)
H1_59 = np.asarray(h1[:59], dtype=np.int64)
H2_43 = np.asarray(h2[:43], dtype=np.int64)
H2_52 = np.asarray(h2[:52], dtype=np.int64)

dec = core.bind_historical_decoder()
xrng = np.random.default_rng(2026090702)


def call(h, prior, syn, max_iter=None):
    t0 = time.perf_counter()
    if max_iter is None:
        res = dec(np.asarray(h), np.asarray(prior, dtype=np.float64),
                  np.asarray(syn))
    else:  # cap control: same frozen kwargs except max_iter (single axis)
        raw = core._load_g0_decoder()
        r = raw(np.asarray(h, dtype=np.uint8),
                np.asarray(prior, dtype=np.float64),
                np.asarray(syn, dtype=np.uint8), max_iter=max_iter,
                damping_alpha=core.DAMPING_ALPHA, warm_beliefs=None, field=None)
        res = {"x_hat": np.asarray(r.x_hat), "syndrome_ok": bool(r.syndrome_ok),
               "iterations": int(r.iterations),
               "final_beliefs": np.asarray(r.final_beliefs)}
    return res, time.perf_counter() - t0


def rec(dd, res, wall, extra=None):
    xh = np.asarray(res["x_hat"], dtype=np.int64).ravel()
    d = {"id": dd["id"], "decoder_calls": 1, "changed_axis": dd["axis"],
         "input": dd["input"], "exact": bool(np.array_equal(xh, dd["xtrue"])),
         "syndrome_ok": bool(res["syndrome_ok"]),
         "iterations": int(res["iterations"]),
         "nonfinite": bool(not np.all(np.isfinite(np.asarray(
             res["final_beliefs"], dtype=np.float64)))),
         "wall_s": wall, "rss_bytes": _rss(), "result": dd["res"]}
    if extra:
        d.update(extra)
    ev["diagnostics"].append(d)
    ev["decoder_calls"] += 1
    return d

# ---- F1: decoy priors (6 misled positions) force real iterations ----
for name, h in (("H1[:49]", H1_49), ("H1[:59]", H1_59),
                ("H2[:43]", H2_43), ("H2[:52]", H2_52)):
    n = h.shape[1]
    xt = xrng.integers(0, 32, size=(n,)).astype(np.int64)
    syn = core._gf32_syndrome(h, xt)
    pr = np.full((n, 32), 0.05 / 31)
    pr[np.arange(n), xt] = 0.95
    mis = xrng.choice(n, size=6, replace=False)
    for i in mis:
        decoy = (int(xt[i]) + 7) % 32
        pr[i, :] = 0.05 / 31
        pr[i, decoy] = 0.65
        pr[i, int(xt[i])] = 0.30
    res, wall = call(h, pr, syn)
    rec({"id": f"F1@{name}", "axis": "none",
         "input": "0.95 prior + 6 decoy-peaked positions; frozen prefix",
         "xtrue": xt, "res": "nontrivial machinery"}, res, wall,
        {"syndrome_weight": int(np.count_nonzero(syn))})

# ---- accepted Model-F tables (read-only) + 4 paired blocks ----
npz = np.load(REPO / "workspace/v72p2d5_model_f_input/20260907_r1/model_f_input.npz")
counts = np.asarray(npz["counts_ab"], dtype=np.float64)
pb0 = np.asarray(npz["p_b"], dtype=np.float64)
pb = pb0 / pb0.sum()
pf = core.build_f_model(counts, core.LAMBDA_STAR)
_, _, _, p1, p2 = core._ce_stats(pf, pb)

seeds = [2026090600, 2026090601, 2026090602, 2026090603]
for sd in seeds:
    blk = core.sample_matched_block(pb, pf, 64, sd)
    # texture: prior mass on truth (zero-call)
    m1 = float(np.mean(p1[blk["u1"], blk["bob"]]))
    po = core.oracle_l2_prior(p2, blk["bob"], blk["u1"])
    m2 = float(np.mean(po[np.arange(64), blk["u2"]]))
    tex = {"block_seed": sd, "p1_mass_on_truth": m1,
           "oracle_p2_mass_on_truth": m2}
    # F2a: full APP layered path, frozen f=1.0 rows
    prior_l1 = core._floor_renorm(p1[:, blk["bob"]].T, core.DECODER_FLOOR)
    r1, w1 = call(H1_49, prior_l1, core._gf32_syndrome(H1_49, blk["u1"]))
    xh1 = np.asarray(r1["x_hat"], dtype=np.int64).ravel()
    e1 = bool(np.array_equal(xh1, blk["u1"]))
    ev["decoder_calls"] += 1
    # APP L2 fed from L1 beliefs (production path replica, records kept flat)
    bel = np.asarray(r1["final_beliefs"], dtype=np.float64)
    q = core._softmax_rows(bel) if bel.shape == prior_l1.shape \
        else np.full_like(prior_l1, 1.0 / prior_l1.shape[1])
    prior_l2 = core.app_fed_l2_prior(p2, blk["bob"], q)
    r2, w2 = call(H2_43, prior_l2, core._gf32_syndrome(H2_43, blk["u2"]))
    xh2 = np.asarray(r2["x_hat"], dtype=np.int64).ravel()
    e2 = bool(np.array_equal(xh2, blk["u2"]))
    ev["decoder_calls"] += 1
    ev["diagnostics"].append({
        "id": f"F2a-APP@{sd}", "decoder_calls": 2, "changed_axis": "none",
        "input": f"Model-F block seed {sd}, n=64, frozen f=1.0 rows",
        "exact": bool(e1 and e2), "l1_exact": e1,
        "syndrome_ok": bool(r1["syndrome_ok"] and r2["syndrome_ok"]),
        "iterations": int(r1["iterations"]) + int(r2["iterations"]),
        "nonfinite": bool(not (np.all(np.isfinite(bel)) and np.all(
            np.isfinite(np.asarray(r2["final_beliefs"], dtype=np.float64))))),
        "wall_s": w1 + w2, "rss_bytes": _rss(),
        "result": "formal-prior APP path", **tex})
    # F2b: oracle L2 on same block, frozen rows (prior axis only differs)
    r3, w3 = call(H2_43, po, core._gf32_syndrome(H2_43, blk["u2"]))
    rec({"id": f"F2b-ORACLE@{sd}", "axis": "prior only (APP-fed -> oracle-true-U1)",
         "input": f"same block seed {sd}; H2[:43]",
         "xtrue": blk["u2"], "res": "prior-axis pair"}, r3, w3, tex)
    # F3: oracle, stronger full-disclosure rows (rows axis only differs)
    r4, w4 = call(H2_52, po, core._gf32_syndrome(H2_52, blk["u2"]))
    rec({"id": f"F3-ROWS@{sd}", "axis": "rows only (H2[:43] -> H2[:52] full)",
         "input": f"same block seed {sd}; oracle prior",
         "xtrue": blk["u2"], "res": "rows-axis pair"}, r4, w4, tex)

# ---- F4: iteration-cap control on first block (oracle, frozen rows) ----
blk0 = core.sample_matched_block(pb, pf, 64, seeds[0])
po0 = core.oracle_l2_prior(p2, blk0["bob"], blk0["u1"])
s0 = core._gf32_syndrome(H2_43, blk0["u2"])
r5, w5 = call(H2_43, po0, s0, max_iter=180)
rec({"id": "F4-CAP@2026090600", "axis": "cap only (90 -> 180)",
     "input": "block seed 2026090600; oracle prior; H2[:43]",
     "xtrue": blk0["u2"], "res": "cap-axis control"}, r5, w5)

ev["wall_s"] = time.perf_counter() - t_all
with open(OUT / "diag03_paired_controls.json", "w", encoding="utf-8") as fh:
    json.dump(ev, fh, indent=2, sort_keys=True,
              default=lambda o: int(o) if isinstance(o, np.integer) else float(o))
print(json.dumps({"calls": ev["decoder_calls"], "wall_s": ev["wall_s"],
                  "summary": [(d["id"], d["exact"], d["syndrome_ok"],
                               d["iterations"], round(d["wall_s"], 3))
                              for d in ev["diagnostics"]]}, indent=1))
