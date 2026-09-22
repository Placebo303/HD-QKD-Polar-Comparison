"""R2 W4a: CAL-only estimator calibration + honest frame-blocked held-out (0 calls).

Candidates (predeclared): C0 accepted per-cell lam*; C1 D4R2-F backoff lam*;
C2 raw empirical lam=0 + floor; C3 D4R2-L hierarchical lam*. lam frozen at the
D4R2 nested-CV selection (no new search, no VAL). Held-out reuses the frozen
D4R2 outer frame-blocked folds (TEST256/TRAIN768, deterministic, CAL-only).
Parquet read filters frame_id to CAL 702..1725 only; VAL frames never read.
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

spec = importlib.util.spec_from_file_location("v72p2d5_core_w4a", str(CORE_PATH))
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

FLOOR = 1e-300
Q, QS = 1024, 32
LAM = float(core.LAMBDA_STAR)
t_all = time.perf_counter()
ev = {"workstream": "W4a", "decoder_calls": 0, "lam": LAM,
      "selection_basis": "frozen D4R2 nested-CV (no new search, no VAL)"}

# ---------- candidate builders on count tables ----------

def build_C0(counts):
    return (counts + LAM) / (counts.sum(axis=0, keepdims=True) + Q * LAM)


def build_C1(counts):
    n = float(counts.sum())
    n_b = counts.sum(axis=0)
    p_g = counts.sum(axis=1) / n
    return (counts + LAM * p_g[:, None]) / (n_b[None, :] + LAM)


def joint_ce_of_pf(pf, a_te, b_te):
    return float(-np.mean(np.log2(np.maximum(pf[a_te, b_te], FLOOR))))


def split_pf(pf):
    p1 = core.marginalize_f_to_p1(pf)
    p2 = core.conditionalize_f_to_p2(pf)
    return p1, p2


def build_C3_p1p2(a_tr, b_tr):
    lo, hi = (a_tr & 31).astype(np.int64), ((a_tr >> 5) & 31).astype(np.int64)
    cnt1 = np.zeros((Q, QS))
    np.add.at(cnt1, (b_tr, hi), 1.0)
    n_b1 = cnt1.sum(axis=1)
    p_g1 = cnt1.sum(axis=0) / float(a_tr.size)
    p1 = (cnt1 + LAM * p_g1[None, :]) / (n_b1[:, None] + LAM)  # [B,U1]
    cnt2 = np.zeros((QS, Q, QS))
    np.add.at(cnt2, (hi, b_tr, lo), 1.0)
    n_row = cnt2.sum(axis=2, keepdims=True)
    p_g2 = cnt2.sum(axis=(0, 1)) / float(a_tr.size)
    p2 = (cnt2 + LAM * p_g2[None, None, :]) / (n_row + LAM)  # [U1,B,U2]
    return p1, p2


# ---------- full-counts calibration (resub channel CE + truth mass) ----------
npz = np.load(REPO / "workspace/v72p2d5_model_f_input/20260907_r1/model_f_input.npz")
counts_full = np.asarray(npz["counts_ab"], dtype=np.float64)
pb = np.asarray(npz["p_b"], dtype=np.float64)
pb /= pb.sum()
pf0 = build_C0(counts_full)
pf1 = build_C1(counts_full)
pf2 = np.where(counts_full.sum(axis=0, keepdims=True) > 0,
               counts_full / np.maximum(counts_full.sum(axis=0, keepdims=True), 1),
               1.0 / Q)
cal = {}
for name, pf in (("C0", pf0), ("C1", pf1), ("C2", pf2)):
    j, l1, l2, p1, p2 = core._ce_stats(np.maximum(pf, 0.0), pb)
    masses = []
    for sd in (2026090600, 2026090601, 2026090602, 2026090603):
        blk = core.sample_matched_block(pb, np.maximum(pf, 0.0)
                                        / np.maximum(pf, 0.0).sum(axis=0,
                                                                  keepdims=True),
                                        64, sd)
        po = core.oracle_l2_prior(p2, blk["bob"], blk["u1"])
        masses.append(float(np.mean(po[np.arange(64), blk["u2"]])))
    cal[name] = {"ce_joint": j, "ce_l1": l1, "ce_l2": l2,
                 "truth_mass_mean": float(sum(masses) / len(masses))}
# C3 full-counts
a_all = np.repeat(np.arange(Q, dtype=np.int64),
                  counts_full.sum(axis=1).astype(np.int64))
ev_full_note = "C3 full-counts joint rebuilt as P1*P2 from aggregated counts"
cnt1f = counts_full.reshape(QS, QS, Q).sum(axis=1).T  # [B,U1]
n_b1f = cnt1f.sum(axis=1)
p_g1f = cnt1f.sum(axis=0) / float(counts_full.sum())
p1f = (cnt1f + LAM * p_g1f[None, :]) / (n_b1f[:, None] + LAM)
cnt2f = np.moveaxis(counts_full.reshape(QS, QS, Q), 2, 1)  # [U1,B,U2]
n_rf = cnt2f.sum(axis=2, keepdims=True)
p_g2f = cnt2f.sum(axis=(0, 1)) / float(counts_full.sum())
p2f = (cnt2f + LAM * p_g2f[None, None, :]) / (n_rf + LAM)
pf3 = np.empty((Q, Q))
cube3 = (p1f.T[:, :, None] * p2f).transpose(0, 2, 1)  # [U1,U2,B]
pf3 = cube3.reshape(Q, Q)
j3, l13, l23, _, p23 = core._ce_stats(pf3, pb)
m3 = []
for sd in (2026090600, 2026090601, 2026090602, 2026090603):
    blk = core.sample_matched_block(pb, pf3, 64, sd)
    po = core.oracle_l2_prior(p2f, blk["bob"], blk["u1"])
    m3.append(float(np.mean(po[np.arange(64), blk["u2"]])))
cal["C3"] = {"ce_joint": j3, "ce_l1": l13, "ce_l2": l23,
             "truth_mass_mean": float(sum(m3) / len(m3))}
ev["full_counts_calibration"] = cal
ev["c3_note"] = ev_full_note

# ---------- honest held-out on frozen D4R2 outer folds (CAL-only) ----------
PARQ = (REPO / "comparison_bench/outputs_comparison/v55_intake_20260828/pairs"
        / "20260123_1M_600k_0dB/pairs.parquet")
FOLDS = {"F0": (range(702, 958),), "F1": (range(958, 1214),),
         "F2": (range(1214, 1470),), "F3": (range(1470, 1726),)}
df = pd.read_parquet(PARQ, columns=["frame_id", "alice_symbol", "bob_symbol"],
                     filters=[("frame_id", ">=", 702), ("frame_id", "<=", 1725)])
ev["parquet_rows_cal_only"] = int(len(df))
ev["val_touched"] = False
assert int(len(df)) == 262144
frames = df["frame_id"].to_numpy()
al = df["alice_symbol"].to_numpy().astype(np.int64)
bo = df["bob_symbol"].to_numpy().astype(np.int64)

held = {}
for fk, (test_ids,) in FOLDS.items():
    test_ids = set(int(v) for v in test_ids)
    te_mask = np.array([int(f) in test_ids for f in frames])
    a_tr, b_tr = al[~te_mask], bo[~te_mask]
    a_te, b_te = al[te_mask], bo[te_mask]
    assert a_tr.size == 768 * 256 and a_te.size == 256 * 256
    ctr = np.zeros((Q, Q))
    np.add.at(ctr, (a_tr, b_tr), 1.0)
    row = {"n_train": int(a_tr.size), "n_test": int(a_te.size)}
    row["C0"] = joint_ce_of_pf(build_C0(ctr), a_te, b_te)
    row["C1"] = joint_ce_of_pf(build_C1(ctr), a_te, b_te)
    c2t = np.where(ctr.sum(axis=0, keepdims=True) > 0,
                   ctr / np.maximum(ctr.sum(axis=0, keepdims=True), 1),
                   1.0 / Q)
    row["C2"] = joint_ce_of_pf(c2t, a_te, b_te)
    p1t, p2t = build_C3_p1p2(a_tr, b_tr)
    lo_te, hi_te = (a_te & 31), ((a_te >> 5) & 31)
    j3t = np.maximum(p1t[b_te, hi_te], FLOOR) * np.maximum(
        p2t[hi_te, b_te, lo_te], FLOOR)
    row["C3"] = float(-np.mean(np.log2(np.maximum(j3t, FLOOR))))
    held[fk] = row
ev["heldout_joint_ce"] = held
ev["heldout_means"] = {c: float(sum(held[fk][c] for fk in held) / 4)
                       for c in ("C0", "C1", "C2", "C3")}
ev["wall_s"] = time.perf_counter() - t_all
ev["rss_bytes"] = core._rss_bytes()
(OUT / "w4a_evidence.json").write_text(json.dumps(ev, indent=2) + "\n",
                                       encoding="utf-8")
print(json.dumps({"full_counts": cal, "heldout_means": ev["heldout_means"]},
                 indent=1))
print("W4a wall", round(ev["wall_s"], 1), "rss", ev["rss_bytes"])
