"""D5 L1 discriminator Phase C: CAL-only L1 estimator comparison (0 decoder calls).

Estimators (prereg G1_L1_ESTIMATOR_DISCRIMINATOR_PREREG_R1.md):
  E1 joint-F backoff (frozen lam*) marginalized to L1 (no selection).
  E2 direct aggregated P(U1|B) backoff, kap selected on held-out L1 NLL
     over grid30 logspace(-2,3), same 4 outer folds.
  E3 direct aggregated P(U1|B) backoff at frozen kap=lam* (no selection).
CAL-only; VAL never touched. No decoder import/use here.
"""
import importlib.util
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
CORE_PATH = (REPO / "comparison_bench/src/comparison_bench/formal_ir"
             / "v72p2d5_gf32_rate_mother.py")

spec = importlib.util.spec_from_file_location("v72p2d5_core_l1c", str(CORE_PATH))
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

FLOOR = 1e-300
DFLOOR = 1e-15
Q, QS = 1024, 32
LAM = float(core.LAMBDA_STAR)
GRID = np.logspace(-2, 3, 30)
SEEDS = [2026090600, 2026090601, 2026090602, 2026090603]
t_all = time.perf_counter()
ev = {"phase": "C", "decoder_calls": 0, "lam_star": LAM,
      "grid": "logspace(-2,3,30)", "selection": "held-out CAL L1 NLL only"}

PARQ = (REPO / "comparison_bench/outputs_comparison/v55_intake_20260828/pairs"
        / "20260123_1M_600k_0dB/pairs.parquet")
FOLDS = {"F0": range(702, 958), "F1": range(958, 1214),
         "F2": range(1214, 1470), "F3": range(1470, 1726)}
df = pd.read_parquet(PARQ, columns=["frame_id", "alice_symbol", "bob_symbol"],
                     filters=[("frame_id", ">=", 702), ("frame_id", "<=", 1725)])
ev["parquet_rows_cal_only"] = int(len(df))
ev["val_touched"] = False
assert int(len(df)) == 262144
frames = df["frame_id"].to_numpy()
al = df["alice_symbol"].to_numpy().astype(np.int64)
bo = df["bob_symbol"].to_numpy().astype(np.int64)
u1_all = ((al >> 5) & 31).astype(np.int64)


def fit_joint_backoff(ctr, lam):
    n_b = ctr.sum(axis=0)
    p_g = ctr.sum(axis=1) / float(ctr.sum())
    return (ctr + lam * p_g[:, None]) / (n_b[None, :] + lam)


def fit_l1_backoff(a_tr, b_tr, kap):
    cnt1 = np.zeros((Q, QS))
    np.add.at(cnt1, (b_tr, ((a_tr >> 5) & 31).astype(np.int64)), 1.0)
    n_b1 = cnt1.sum(axis=1)
    p_g1 = cnt1.sum(axis=0) / float(a_tr.size)
    p1 = (cnt1 + kap * p_g1[None, :]) / (n_b1[:, None] + kap)  # [B,U1]
    return p1, n_b1


def l1_nll(p1_bu, b_te, u1_te):
    return float(-np.mean(np.log2(np.maximum(p1_bu[b_te, u1_te], FLOOR))))


held = {}
for fk, test_ids in FOLDS.items():
    test_ids = set(int(v) for v in test_ids)
    te = np.array([int(f) in test_ids for f in frames])
    a_tr, b_tr = al[~te], bo[~te]
    a_te, b_te = al[te], bo[te]
    u1_te = ((a_te >> 5) & 31).astype(np.int64)
    assert a_tr.size == 768 * 256 and a_te.size == 256 * 256
    ctr = np.zeros((Q, Q))
    np.add.at(ctr, (a_tr, b_tr), 1.0)
    # E1: joint backoff lam* -> marginalize
    pf1 = fit_joint_backoff(ctr, LAM)
    p1_e1 = core.marginalize_f_to_p1(pf1)  # [U1,B]
    row = {"n_train": int(a_tr.size), "n_test": int(a_te.size)}
    row["E1"] = float(-np.mean(np.log2(np.maximum(p1_e1[u1_te, b_te], FLOOR))))
    # E2: grid over kap on direct L1
    nlls = []
    for kap in GRID:
        p1, _ = fit_l1_backoff(a_tr, b_tr, float(kap))
        nlls.append(l1_nll(p1, b_te, u1_te))
    row["E2_grid_nll"] = [float(v) for v in nlls]
    row["E2_best_kap"] = float(GRID[int(np.argmin(nlls))])
    row["E2"] = float(min(nlls))
    # E3: direct L1 at frozen kap
    p1_e3, _ = fit_l1_backoff(a_tr, b_tr, LAM)
    row["E3"] = l1_nll(p1_e3, b_te, u1_te)
    held[fk] = row
ev["heldout_l1_nll"] = {k: {c: held[k][c] for c in ("E1", "E2", "E3",
                                                   "E2_best_kap")}
                        for k in held}
means = {c: float(sum(held[fk][c] for fk in held) / 4) for c in ("E1", "E2", "E3")}
ses = {c: float(np.std([held[fk][c] for fk in held], ddof=1) / 2.0)
       for c in ("E1", "E2", "E3")}
ev["heldout_means"] = means
ev["heldout_se"] = ses
order = sorted(means, key=means.get)
winner = order[0]
if abs(means[order[0]] - means[order[1]]) < 0.01:
    for cand in ("E1", "E3"):
        if cand in order[:2]:
            winner = cand
            break
ev["winner"] = winner
ev["E2_best_kap_per_fold"] = {k: held[k]["E2_best_kap"] for k in held}

# ---- full-counts diagnostics (resub channel stats + paired model-sampled mass)
npz = np.load(REPO / "workspace/v72p2d5_model_f_input/20260907_r1/model_f_input.npz")
counts_full = np.asarray(npz["counts_ab"], dtype=np.float64)
pb = np.asarray(npz["p_b"], dtype=np.float64)
pb /= pb.sum()
a_full = np.repeat(np.arange(Q, dtype=np.int64),
                   counts_full.sum(axis=1).astype(np.int64))
u1_full = ((a_full >> 5) & 31).astype(np.int64)
n_b = counts_full.sum(axis=0)
diag = {}
pf_e1 = fit_joint_backoff(counts_full, LAM)
p1_full_e1 = core.marginalize_f_to_p1(pf_e1)
# aggregate directly from the count table (exact, no resampling)
cnt1f = counts_full.reshape(QS, QS, Q).sum(axis=1).T  # [B,U1]
n_b1f = cnt1f.sum(axis=1)
p_g1f = cnt1f.sum(axis=0) / float(counts_full.sum())
# E2 kap: kap minimizing the mean held-out NLL across folds (pooled rule);
# per-fold winners are diagnostics only.
kaps = [held[k]["E2_best_kap"] for k in held]
mean_grid = [float(sum(held[fk]["E2_grid_nll"][gi] for fk in held) / 4)
             for gi in range(len(GRID))]
kap_use = float(GRID[int(np.argmin(mean_grid))])
ev["E2_mean_grid_best_kap"] = float(kap_use)
ev["E2_kap_use"] = float(kap_use)
p1_full_e2 = (cnt1f + kap_use * p_g1f[None, :]) / (n_b1f[:, None] + kap_use)
p1_full_e3 = (cnt1f + LAM * p_g1f[None, :]) / (n_b1f[:, None] + LAM)


def l1_stats(p1_bu, tag):
    ce = float(-sum(pb[b] * float(np.sum(
        p1_bu[b] * np.log2(np.maximum(p1_bu[b], FLOOR)))) for b in range(Q)))
    m1 = np.array([float(np.sum(pb * p1_bu[:, u])) for u in range(QS)])
    m1 /= m1.sum()
    h1 = float(-np.sum(m1 * np.log2(np.maximum(m1, FLOOR))))
    return {"ce_l1": ce, "entropy_u1": h1, "mi_l1": h1 - ce,
            "support_col_min": float(n_b.min()), "support_col_max": float(n_b.max()),
            "support_col_mean": float(n_b.mean())}


for tag, p1 in (("E1", p1_full_e1.T), ("E2", p1_full_e2), ("E3", p1_full_e3)):
    d = l1_stats(np.asarray(p1, dtype=np.float64), tag)
    masses = []
    for sd in SEEDS:
        blk = core.sample_matched_block(pb, pf_e1, 64, sd)
        pr = np.asarray(p1, dtype=np.float64)[blk["bob"], :]
        pr = np.maximum(pr, DFLOOR)
        pr = pr / pr.sum(axis=1, keepdims=True)
        masses.append(float(np.mean(pr[np.arange(64), blk["u1"]])))
    d["truth_mass_paired_e1law_floored"] = float(sum(masses) / len(masses))
    diag[tag] = d
diag["E1"]["prior_frac"] = float(LAM / (256.0 + LAM))
diag["E2"]["prior_frac"] = float(kap_use / (256.0 + kap_use))
diag["E3"]["prior_frac"] = float(LAM / (256.0 + LAM))
diag["E2"]["kap"] = float(kap_use)
diag["E1"]["kap"] = float(LAM)
diag["E3"]["kap"] = float(LAM)
ev["full_counts_diagnostics"] = diag
ev["uniform_chance_nll"] = 5.0
ev["wall_s"] = time.perf_counter() - t_all
ev["peak_rss_bytes"] = core._rss_bytes()
(OUT / "c1_evidence.json").write_text(json.dumps(ev, indent=2) + "\n",
                                      encoding="utf-8")
print(json.dumps({"means": means, "se": ses, "winner": winner,
                  "kaps": kaps, "kap_use": kap_use,
                  "mass": {k: diag[k]["truth_mass_paired_e1law_floored"]
                           for k in diag},
                  "ce": {k: diag[k]["ce_l1"] for k in diag},
                  "mi": {k: diag[k]["mi_l1"] for k in diag}}, indent=1))
print("Phase C wall", round(ev["wall_s"], 1), "rss", ev["peak_rss_bytes"])
