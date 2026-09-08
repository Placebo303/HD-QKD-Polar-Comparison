"""D5 decomposition successor S1: CAL-only scoring of all 252 ordered 5-of-10 partitions.

Frozen prereg D5_DECOMPOSITION_SUCCESSOR_PREREG_R1.md sections 4.1-4.3, 4.7.
CAL-only: canonical CAL-TRAIN 702..1725, 4 frozen outer folds, accepted R2
total-concentration/backoff contract (build_f_model_concentration at frozen
LAMBDA_STAR; no new search, no VAL). NO decoder import/use in this script.
Writes partition_scores.csv (scalars only) + appends command_log.txt.
"""
import importlib.util
import itertools
import json
import math
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
CORE_PATH = (REPO / "comparison_bench/src/comparison_bench/formal_ir"
             / "v72p2d5_gf32_rate_mother.py")

spec = importlib.util.spec_from_file_location("v72p2d5_core_d5s1", str(CORE_PATH))
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
assert not hasattr(core, "decode_row_layered_fft_qspa"), "decoder must stay unbound"

LOG = ROOT / "command_log.txt"


def log(msg):
    line = "%s %s" % (time.strftime("%Y-%m-%dT%H:%M:%S"), msg)
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


t_all = time.perf_counter()
LAM = float(core.LAMBDA_STAR)
FLOOR = float(core.AUDIT_FLOOR)
FOLDS = {"F0": range(702, 958), "F1": range(958, 1214),
         "F2": range(1214, 1470), "F3": range(1470, 1726)}
PARQ = (REPO / "comparison_bench/outputs_comparison/v55_intake_20260828/pairs"
        / "20260123_1M_600k_0dB/pairs.parquet")

df = pd.read_parquet(PARQ, columns=["frame_id", "alice_symbol", "bob_symbol"],
                     filters=[("frame_id", ">=", 702), ("frame_id", "<=", 1725)])
assert int(len(df)) == 262144, len(df)
frames = df["frame_id"].to_numpy()
al = df["alice_symbol"].to_numpy().astype(np.int64)
bo = df["bob_symbol"].to_numpy().astype(np.int64)
log("S1 loaded CAL rows=%d val_touched=False" % len(df))

PARTS = [tuple(sorted(c)) for c in itertools.combinations(range(10), 5)]
assert len(PARTS) == 252 and len(set(PARTS)) == 252


def pack(a, bits):
    out = np.zeros(a.shape, dtype=np.int64)
    for j, b in enumerate(bits):
        out |= ((a >> b) & 1) << j
    return out


def unpack(u, bits):
    a = np.zeros(u.shape, dtype=np.int64)
    for j, b in enumerate(bits):
        a |= ((u >> j) & 1) << b
    return a


# reversibility over all 1024 symbols for every partition
all_a = np.arange(1024, dtype=np.int64)
for s1 in PARTS:
    s2 = tuple(b for b in range(10) if b not in s1)
    u1 = pack(all_a, s1)
    u2 = pack(all_a, s2)
    assert set(np.unique(u1)) == set(range(32)) and set(np.unique(u2)) == set(range(32))
    assert bool(np.array_equal(unpack(u1, s1) | unpack(u2, s2), all_a))
log("S1 reversibility PASS for all 252 partitions x 1024 symbols")

fold_masks = {}
for fk, test_ids in FOLDS.items():
    tids = set(int(v) for v in test_ids)
    te = np.array([int(f) in tids for f in frames])
    assert int(te.sum()) == 256 * 256 and int((~te).sum()) == 768 * 256, fk
    fold_masks[fk] = te
log("S1 fold accounting PASS (TRAIN 196608 / TEST 65536 per fold)")

rows_out = []
for pi, s1 in enumerate(PARTS):
    t0 = time.perf_counter()
    s2 = tuple(b for b in range(10) if b not in s1)
    u1_all = pack(al, s1)
    u2_all = pack(al, s2)
    ua_all = u1_all * 32 + u2_all
    jl1, jl2, jj, cerr = [], [], [], []
    for fk in ("F0", "F1", "F2", "F3"):
        te = fold_masks[fk]
        ctr = np.zeros((1024, 1024))
        np.add.at(ctr, (ua_all[~te], bo[~te]), 1.0)
        assert ctr.sum() == 196608, fk
        pf = core.build_f_model_concentration(ctr, LAM)
        assert np.all(np.isfinite(pf))
        p1 = np.asarray(core.marginalize_f_to_p1(pf), dtype=np.float64)  # [U1,B]
        assert np.all(np.abs(p1.sum(axis=0) - 1.0) < 1e-12)
        p2 = np.asarray(core.conditionalize_f_to_p2(pf), dtype=np.float64)  # [U1,B,U2]
        assert np.all(np.abs(p2.sum(axis=2) - 1.0) < 1e-12)
        b_te, u1_te, u2_te, ua_te = bo[te], u1_all[te], u2_all[te], ua_all[te]
        n1 = float(-np.mean(np.log2(np.maximum(p1[u1_te, b_te], FLOOR))))
        n2 = float(-np.mean(np.log2(np.maximum(p2[u1_te, b_te, u2_te], FLOOR))))
        nj = float(-np.mean(np.log2(np.maximum(pf[ua_te, b_te], FLOOR))))
        assert np.isfinite(n1) and np.isfinite(n2) and np.isfinite(nj)
        cerr.append(abs(nj - (n1 + n2)))
        jl1.append(n1)
        jl2.append(n2)
        jj.append(nj)
    ce_l1 = float(sum(jl1) / 4)
    ce_l2 = float(sum(jl2) / 4)
    ce_j = float(sum(jj) / 4)
    m1 = int(math.ceil(64 * ce_l1 * 1.2 / 5))
    m2 = int(math.ceil(64 * ce_l2 * 1.2 / 5))
    assert m1 == core._rows_required(ce_l1, 64, 1.2) and m2 == core._rows_required(ce_l2, 64, 1.2)
    rows_out.append({
        "s1": "-".join(str(b) for b in s1),
        "ce_l1": ce_l1, "ce_l2": ce_l2, "ce_joint": ce_j,
        "ce_l1_std": float(np.std(jl1, ddof=1)), "ce_l2_std": float(np.std(jl2, ddof=1)),
        "ce_joint_std": float(np.std(jj, ddof=1)),
        "chain_max_abs_err": float(max(cerr)),
        "m1": m1, "m2": m2,
        "eligible": bool(m1 < 64 and m2 < 64),
        "wall_s": time.perf_counter() - t0,
    })
    if (pi + 1) % 63 == 0:
        log("S1 scored %d/252" % (pi + 1))

assert max(r["chain_max_abs_err"] for r in rows_out) < 1e-9, "chain identity violated"
pd.DataFrame(rows_out).to_csv(ROOT / "partition_scores.csv", index=False)
wall = time.perf_counter() - t_all
rss = core._rss_bytes()
log("S1 done 252 partitions wall_s=%.1f peak_rss=%s chain_max_err=%.2e" % (
    wall, rss, max(r["chain_max_abs_err"] for r in rows_out)))
for r in rows_out:
    if r["s1"] in ("5-6-7-8-9", "0-1-2-3-4"):
        log("S1 control %s ce_l1=%.6f ce_l2=%.6f ce_joint=%.6f m1=%d m2=%d elig=%s" % (
            r["s1"], r["ce_l1"], r["ce_l2"], r["ce_joint"], r["m1"], r["m2"], r["eligible"]))
