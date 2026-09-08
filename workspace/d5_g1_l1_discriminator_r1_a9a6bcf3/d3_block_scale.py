"""D5 L1 discriminator Phase D: conditional block-scaling arm (dev only).

Triggered: n64 failed (0/4 every estimator at every m<64; square 0/4).
Order n=128 then n=256; stop at first width with nonzero-rate recovery.
Development-only diagnostics; never G2. Rate-matched disclosures
{ceil(n*49/64), ceil(n*59/64), n}. Same seeds/estimators/pairing as n64.
Fail-closed on any build/audit failure. No VAL, no formal-root write.
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

spec = importlib.util.spec_from_file_location("v72p2d5_core_l1s", str(CORE_PATH))
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

WATCHDOG = 120
t_all = time.perf_counter()
ev = {"phase": "D-scale", "decoder_calls": 0, "watchdog_s": WATCHDOG,
      "widths": []}
peak_rss = 0


def rss():
    global peak_rss
    v = core._rss_bytes()
    if v is not None and v > peak_rss:
        peak_rss = v
    return v


c1 = json.loads((OUT / "c1_evidence.json").read_text(encoding="utf-8"))
KAP = float(c1["E2_kap_use"])
LAM = float(core.LAMBDA_STAR)

npz = np.load(REPO / "workspace/v72p2d5_model_f_input/20260907_r1/model_f_input.npz")
counts = np.asarray(npz["counts_ab"], dtype=np.float64)
pb = np.asarray(npz["p_b"], dtype=np.float64)
pb /= pb.sum()
n_b = counts.sum(axis=0)
p_global = counts.sum(axis=1) / float(counts.sum())
pf_e1 = (counts + LAM * p_global[:, None]) / (n_b[None, :] + LAM)
p1_e1 = np.asarray(core.marginalize_f_to_p1(pf_e1), dtype=np.float64).T
cnt1 = counts.reshape(32, 32, 1024).sum(axis=1).T
n_b1 = cnt1.sum(axis=1)
p_g1 = cnt1.sum(axis=0) / float(counts.sum())
p1_e2 = np.asarray((cnt1 + KAP * p_g1[None, :]) / (n_b1[:, None] + KAP),
                   dtype=np.float64)
PRIORS = {"E1": p1_e1, "E2": p1_e2}
dec = core.bind_historical_decoder()
SEEDS = [2026090600, 2026090601, 2026090602, 2026090603]


def call(h, prior, syn):
    t0 = time.perf_counter()
    res = dec(np.asarray(h), np.asarray(prior, dtype=np.float64),
              np.asarray(syn))
    return res, time.perf_counter() - t0


def rec(store, tag, est, res, wall, xt, h, syn, tm):
    xh = np.asarray(res["x_hat"], dtype=np.int64).ravel()
    exact_re = bool(np.array_equal(xh, xt))
    syn_re = bool(np.array_equal(core._gf32_syndrome(np.asarray(h), xh),
                                 np.asarray(syn)))
    bel = np.asarray(res["final_beliefs"], dtype=np.float64)
    ev["decoder_calls"] += 1
    store.append({
        "id": tag, "estimator": est, "decoder_calls": 1,
        "exact_recomputed": exact_re, "syndrome_recomputed": syn_re,
        "syndrome_decoder_flag": bool(res["syndrome_ok"]),
        "flag_agree": bool(syn_re == bool(res["syndrome_ok"])),
        "iterations": int(res["iterations"]),
        "nonfinite": bool(not np.all(np.isfinite(bel))),
        "prior_mass_on_truth": tm,
        "wall_s": wall, "rss_bytes": rss(),
        "watchdog_ok": bool(wall <= WATCHDOG)})
    return exact_re and syn_re


recovered_width = None
for n in (128, 256):
    w = {"n": n, "diagnostics": [], "status": "ATTEMPTED"}
    try:
        h_fam = np.asarray(core.build_dv3_nested_mother(n, n, n, 2026090501,
                                                        None), dtype=np.int64)
        h_sq = np.asarray(core.build_dv3_nested_mother(n, n, n, 2026090801,
                                                       None), dtype=np.int64)
        assert core._gf32_rank(h_sq) == n, "square rank %d != %d" % (
            core._gf32_rank(h_sq), n)
        m1, m2 = (n * 49 + 63) // 64, (n * 59 + 63) // 64
        pts = [("m%d" % m1, h_fam[:m1]), ("m%d" % m2, h_fam[:m2]),
               ("m%d-sq" % n, h_sq)]
        w["disclosures"] = [m1, m2, n]
        # S0 delta sanity at this width
        xrng = np.random.default_rng(2026090701)
        xt0 = xrng.integers(0, 32, size=(n,)).astype(np.int64)
        syn0 = core._gf32_syndrome(h_sq, xt0)
        pr0 = np.full((n, 32), 1e-15)
        pr0[np.arange(n), xt0] = 1.0
        pr0 = pr0 / pr0.sum(axis=1, keepdims=True)
        res0, w0 = call(h_sq, pr0, syn0)
        s0ok = rec(w["diagnostics"], "S0-DELTA-L1@n%d" % n, "delta",
                   res0, w0, xt0, h_sq, syn0, 1.0)
        w["s0_recovered"] = bool(s0ok)
        hits = {}
        for sd in SEEDS:
            blk = core.sample_matched_block(pb, pf_e1, n, sd)
            for est in ("E2", "E1"):
                p1 = PRIORS[est]
                for tag, h in pts:
                    pr = np.maximum(np.asarray(p1)[blk["bob"], :],
                                    core.DECODER_FLOOR)
                    pr = pr / pr.sum(axis=1, keepdims=True)
                    tm = float(np.mean(pr[np.arange(n), blk["u1"]]))
                    syn = core._gf32_syndrome(np.asarray(h), blk["u1"])
                    res, wall = call(h, pr, syn)
                    ok = rec(w["diagnostics"], "%s-L1-%s@n%d@%d" % (
                        est, tag, n, sd), est, res, wall, blk["u1"],
                        h, syn, tm)
                    hits.setdefault((est, tag), []).append(ok)
        w["point_rates"] = {("%s %s" % k): "%d/4" % sum(v)
                            for k, v in hits.items()}
        nz = {k: sum(v) for k, v in hits.items()
              if not k[1].endswith("sq")}
        w["nonzero_rate_best"] = max(nz.values()) if nz else 0
        if max(nz.values()) >= 3:
            recovered_width = n
            w["status"] = "RECOVERED_NONZERO_RATE"
        else:
            w["status"] = "NO_RECOVERY"
    except Exception as e:  # fail-closed: record, no improvisation
        w["status"] = "NOT_ATTEMPTED"
        w["error"] = "%s: %s" % (type(e).__name__, str(e)[:200])
    ev["widths"].append(w)
    for d in w["diagnostics"]:
        print(d["id"], "exact", d["exact_recomputed"], "syn",
              d["syndrome_recomputed"], "iters", d["iterations"], "tmass",
              round(d["prior_mass_on_truth"], 4))
    print("width", n, "status", w["status"], "point_rates",
          w.get("point_rates"))
    if recovered_width is not None:
        break
ev["recovered_width"] = recovered_width
ev["wall_s"] = time.perf_counter() - t_all
ev["peak_rss_bytes"] = peak_rss
(OUT / "d3_evidence.json").write_text(json.dumps(ev, indent=2) + "\n",
                                      encoding="utf-8")
print("Phase D-scale calls", ev["decoder_calls"], "wall",
      round(ev["wall_s"], 1), "peak_rss", peak_rss,
      "recovered_width", recovered_width)
