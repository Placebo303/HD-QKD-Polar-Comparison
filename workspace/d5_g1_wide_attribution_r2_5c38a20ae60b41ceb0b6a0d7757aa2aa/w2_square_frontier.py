"""R2 W2: square-disclosure discriminator + compact paired frontier (dev only).

Predeclared: square mother build_dv3_nested_mother(n=64,m_max=64,k_min=64,
seed=2026090801); paired block seeds 2026090600..03; accepted Model-F prior;
oracle-L2 path. Frontier reuses R1 F3 frozen-row points (no repeat calls).
No CLI --phase, no formal-root write, no VAL.
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

spec = importlib.util.spec_from_file_location("v72p2d5_core_w2", str(CORE_PATH))
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

WATCHDOG = 120
t_all = time.perf_counter()
ev = {"workstream": "W2", "decoder_calls": 0, "watchdog_s": WATCHDOG,
      "diagnostics": []}
peak_rss = 0


def rss():
    global peak_rss
    v = core._rss_bytes()
    if v is not None and v > peak_rss:
        peak_rss = v
    return v


# ---- square mother (predeclared deterministic build) ----
SQ_SEED = 2026090801
t0 = time.perf_counter()
h_sq = core.build_dv3_nested_mother(64, 64, 64, SQ_SEED, None)
H_SQ = np.asarray(h_sq, dtype=np.int64)
build_wall = time.perf_counter() - t0
rank = core._gf32_rank(H_SQ)
audit = core.audit_prefix(H_SQ, 64)
ev["square_mother"] = {
    "seed": SQ_SEED, "shape": list(H_SQ.shape), "rank": rank,
    "full_rank": bool(rank == 64), "audit_status": audit["status"],
    "audit_passed": bool(audit["passed"]),
    "four_cycles": audit["four_cycles"],
    "duplicate_projective_columns": audit["duplicate_projective_columns"],
    "base_pair_duplicates": audit["base_pair_duplicates"],
    "build_wall_s": build_wall,
}
print("square mother rank", rank, "status", audit["status"])
rss()

# ---- accepted prior tables (read-only) ----
npz = np.load(REPO / "workspace/v72p2d5_model_f_input/20260907_r1/model_f_input.npz")
counts = np.asarray(npz["counts_ab"], dtype=np.float64)
pb0 = np.asarray(npz["p_b"], dtype=np.float64)
pb = pb0 / pb0.sum()
pf = core.build_f_model(counts, core.LAMBDA_STAR)
_, _, _, p1, p2 = core._ce_stats(pf, pb)
dec = core.bind_historical_decoder()


def guarded_call(h, prior, syn):
    t0 = time.perf_counter()
    res = dec(np.asarray(h), np.asarray(prior, dtype=np.float64),
              np.asarray(syn))
    wall = time.perf_counter() - t0
    return res, wall


# ---- S0 sanity: delta prior on square mother (matrix/decoder separation) ----
xrng = np.random.default_rng(2026090701)
xt = xrng.integers(0, 32, size=(64,)).astype(np.int64)
syn0 = core._gf32_syndrome(H_SQ, xt)
pr0 = np.full((64, 32), 1e-15)
pr0[np.arange(64), xt] = 1.0
pr0 = pr0 / pr0.sum(axis=1, keepdims=True)
res0, w0 = guarded_call(H_SQ, pr0, syn0)
ev["decoder_calls"] += 1
ev["diagnostics"].append({
    "id": "S0-DELTA@Hsq[:64]", "decoder_calls": 1,
    "changed_axis": "mother only (new square mother; signal prior)",
    "input": "delta prior on rng(2026090701) word; square mother",
    "exact": bool(np.array_equal(np.asarray(res0["x_hat"]).ravel(), xt)),
    "syndrome_ok": bool(res0["syndrome_ok"]),
    "iterations": int(res0["iterations"]),
    "nonfinite": bool(not np.all(np.isfinite(
        np.asarray(res0["final_beliefs"], dtype=np.float64)))),
    "wall_s": w0, "rss_bytes": rss(), "watchdog_ok": bool(w0 <= WATCHDOG),
})
print("S0", ev["diagnostics"][-1]["exact"], ev["diagnostics"][-1]["syndrome_ok"],
      ev["diagnostics"][-1]["iterations"])

# ---- S1..S4: square oracle-L2 with accepted prior, paired frozen seeds ----
seeds = [2026090600, 2026090601, 2026090602, 2026090603]
for sd in seeds:
    blk = core.sample_matched_block(pb, pf, 64, sd)
    prior_o = core.oracle_l2_prior(p2, blk["bob"], blk["u1"])
    tmass = float(np.mean(prior_o[np.arange(64), blk["u2"]]))
    res, wall = guarded_call(H_SQ, prior_o, core._gf32_syndrome(H_SQ, blk["u2"]))
    ev["decoder_calls"] += 1
    xh = np.asarray(res["x_hat"], dtype=np.int64).ravel()
    d = {"id": f"SQ-ORACLE@{sd}", "decoder_calls": 1, "block_seed": sd,
         "changed_axis": "mother only (frozen H2[:43] -> square Hsq[:64]); "
                         "prior unchanged (accepted oracle-L2)",
         "input": "Model-F block seed %d, n=64, square disclosure m=n=64" % sd,
         "prior_mass_on_truth": tmass,
         "exact": bool(np.array_equal(xh, blk["u2"])),
         "syndrome_ok": bool(res["syndrome_ok"]),
         "iterations": int(res["iterations"]),
         "nonfinite": bool(not np.all(np.isfinite(
             np.asarray(res["final_beliefs"], dtype=np.float64)))),
         "wall_s": wall, "rss_bytes": rss(), "watchdog_ok": bool(wall <= WATCHDOG)}
    ev["diagnostics"].append(d)
    print(d["id"], "exact", d["exact"], "syn", d["syndrome_ok"],
          "iters", d["iterations"], "wall", round(wall, 3))

ev["frontier_accepted_prior"] = {
    "note": "paired frontier reuses R1 F3 frozen-row points (no repeat calls)",
    "H2[:43]": {"exact": "0/4 (R1 F2b)", "source": "R1 diag03"},
    "H2[:52]": {"exact": "0/4 (R1 F3)", "source": "R1 diag03"},
    "Hsq[:64]": {"exact": "%d/4 (this script S1..S4)" % sum(
        1 for d in ev["diagnostics"] if d["id"].startswith("SQ-ORACLE")
        and d["exact"]), "source": "R2 W2"},
}
ev["wall_s"] = time.perf_counter() - t_all
ev["peak_rss_bytes"] = peak_rss
(OUT / "w2_evidence.json").write_text(json.dumps(ev, indent=2) + "\n",
                                      encoding="utf-8")
print("W2 calls", ev["decoder_calls"], "wall", round(ev["wall_s"], 2),
      "peak_rss", peak_rss)
