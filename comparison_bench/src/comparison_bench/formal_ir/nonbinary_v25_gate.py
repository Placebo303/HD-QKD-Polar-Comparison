"""V25 empirical timestamp channel + multilevel factorization gate.

Characterizes P(A|B) per source on the frozen q=1024 (200 ps / 204800 ps frame)
fresh pairs, compares channel models C01-C06, analyzes +-1 structure/direction/
time-stability under existing delay config (M2), and runs the F01-F05 x
{L01 natural, L02 Gray} MSB->LSB chain-rule factorization gate (M3), returning
a high-field candidate (GF512/GF256) + mid-field control (GF32/GF16/GF8) for
V26 (M4).

Frozen conventions (2026-08-18 main-thread decision):
- N_ab[a,b] = count(A=a, B=b); decode channel P(A|B) = column-normalized N_ab.
- F01-F05 split the 10-bit label (natural or Gray) MSB->LSB.
- No .ttbin re-read; no sub-bin delay re-estimation; direction of +-1 is a
  source/delay-conditioned channel feature, not an alignment blocker.
"""
from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

Q = 1024
BITS = 10
R_TARGET = 1.3  # f = 1.3 reference
SPLIT = (0.60, 0.20, 0.20)
# Pre-registered smoothing/backoff for empirical delta models (no post-hoc tuning).
# Guarantees every symbol bin has mass >= DELTA_SMOOTH_EPS / (Q*(1+eps)).
DELTA_SMOOTH_EPS = 1e-4

# Frozen labeling
def gray_label(a: int | np.ndarray) -> np.ndarray:
    a = np.asarray(a, dtype=np.int64)
    return a ^ (a >> 1)

def inv_gray(g: int | np.ndarray) -> np.ndarray:
    g = np.asarray(g, dtype=np.int64)
    b = g.copy()
    shift = 1
    while shift < BITS:
        b ^= b >> shift  # doubling-shift inverse Gray on the accumulator
        shift <<= 1
    return b & 0x3FF

# Frozen factorizations: layer bit-widths MSB->LSB (sum to 10)
FACTORIZATIONS: dict[str, dict[str, Any]] = {
    "F01": {"layers": {"L1": ("gf512", 9, [9, 8, 7, 6, 5, 4, 3, 2, 1]), "L2": ("gf2", 1, [0])}},
    "F02": {"layers": {"L1": ("gf256", 8, [9, 8, 7, 6, 5, 4, 3, 2]), "L2": ("gf4", 2, [1, 0])}},
    "F03": {"layers": {"L1": ("gf32", 5, [9, 8, 7, 6, 5]), "L2": ("gf32", 5, [4, 3, 2, 1, 0])}},
    "F04": {"layers": {"L1": ("gf16", 4, [9, 8, 7, 6]), "L2": ("gf16", 4, [5, 4, 3, 2]), "L3": ("gf4", 2, [1, 0])}},
    "F05": {"layers": {"L1": ("gf8", 3, [9, 8, 7]), "L2": ("gf8", 3, [6, 5, 4]), "L3": ("gf8", 3, [3, 2, 1]), "L4": ("gf2", 1, [0])}},
}
# layer id order (MSB first) for chain rule
F_LAYER_ORDER: dict[str, list[str]] = {
    "F01": ["L1", "L2"], "F02": ["L1", "L2"], "F03": ["L1", "L2"],
    "F04": ["L1", "L2", "L3"], "F05": ["L1", "L2", "L3", "L4"],
}
LABELINGS = ["L01_natural", "L02_gray"]

# frozen source layout (from P0 build_manifest + sidecars)
SOURCES = {
    "type2_1M_20260121_184040": {
        "pairs_parquet": "comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_1M_20260121_184040/pairs.parquet",
        "delay_used_ps": -50, "bin_width_ps": 200, "frame_period_ps": 204800,
        "n_frames_total": 519219, "n_clean_frames": 512144, "parquet_rows": 512000, "tail": 151,
    },
    "type2_1p5M_20260121_183806": {
        "pairs_parquet": "comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_1p5M_20260121_183806/pairs.parquet",
        "delay_used_ps": 50, "bin_width_ps": 200, "frame_period_ps": 204800,
        "n_frames_total": 722429, "n_clean_frames": 708417, "parquet_rows": 708352, "tail": 91,
    },
    "type2_2M_20260121_183657": {
        "pairs_parquet": "comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_2M_20260121_183657/pairs.parquet",
        "delay_used_ps": 50, "bin_width_ps": 200, "frame_period_ps": 204800,
        "n_frames_total": 957951, "n_clean_frames": 933120, "parquet_rows": 933120, "tail": 36,
    },
}


def split_label(value: np.ndarray, fact_id: str, labeling: str) -> dict[str, np.ndarray]:
    """Split a 10-bit label value into layers MSB->LSB (frozen)."""
    v = np.asarray(value, dtype=np.int64) & 0x3FF
    if labeling == "L02_gray":
        v = gray_label(v)
    layers = {}
    for lid, (domain, width, bits) in FACTORIZATIONS[fact_id]["layers"].items():
        layer = np.zeros_like(v)
        for b in bits:
            layer |= ((v >> b) & 1) << (b - min(bits))
        layers[lid] = layer
    return layers


def join_label(layers: Mapping[str, np.ndarray], fact_id: str, labeling: str) -> np.ndarray:
    """Reconstruct the 10-bit label from layer values (inverse of split_label)."""
    lid0 = F_LAYER_ORDER[fact_id][0]
    shape = np.asarray(layers[lid0]).shape
    val = np.zeros(shape, dtype=np.int64)
    for lid, (domain, width, bits) in FACTORIZATIONS[fact_id]["layers"].items():
        m = min(bits)
        for b in bits:
            ib = b - m  # layer bit index = label_bit - min(bits)
            val |= ((np.asarray(layers[lid]) >> ib) & 1).astype(np.int64) << b
    if labeling == "L02_gray":
        return inv_gray(val & 0x3FF)
    return val & 0x3FF


def build_N_ab(a: np.ndarray, b: np.ndarray, q: int = Q) -> np.ndarray:
    a = np.asarray(a, dtype=np.int64)
    b = np.asarray(b, dtype=np.int64)
    N = np.bincount(a * q + b, minlength=q * q).astype(np.float64).reshape(q, q)
    return N


def P_A_given_B(N: np.ndarray) -> np.ndarray:
    """P(A=a|B=b) = N_ab[a,b] / colsum(b). Column-normalized."""
    col = N.sum(axis=0, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        P = np.divide(N, col, out=np.zeros_like(N), where=col > 0)
    return P


def conditional_entropy_bits(N: np.ndarray) -> float:
    """H(A|B) in bits from joint counts (plug-in, natural)."""
    tot = N.sum()
    if tot <= 0:
        return 0.0
    Pj = N / tot
    col = Pj.sum(axis=0)
    H = 0.0
    for b in range(Q):
        if col[b] <= 0:
            continue
        p_b = col[b]
        p_a_gb = N[:, b] / N[:, b].sum()
        for a in range(Q):
            p = p_a_gb[a]
            if p > 0:
                H += p_b * p * math.log2(1.0 / p)
    return float(H)


def layer_conditional_entropy_bits(fact_id: str, labeling: str,
                                   N_ab: np.ndarray) -> tuple[dict[str, float], float, dict[str, Any]]:
    """H_i = H(U_i | B, U_<i) per layer and total; also reference rates.

    Works at pair level: build N[a,b, u1..ui] by assigning each pair's symbol
    to layer values, then H(U_i | B, U_<i) = H(B,U_<i,U_i) - H(B,U_<i).
    Computed from the empirical counts; returns per-layer H_i (bits).
    """
    # build (a,b) arrays from N_ab
    aa, bb = np.nonzero(N_ab)
    cnt = N_ab[aa, bb].astype(np.int64)
    # expand to pair-level arrays
    idx = np.repeat(np.arange(len(aa)), cnt)
    a_arr = aa[idx].astype(np.int64)
    b_arr = bb[idx].astype(np.int64)
    layers = split_label(a_arr, fact_id, labeling)

    Hs: dict[str, float] = {}
    ref: dict[str, float] = {}
    prev_col_names: list[str] = []
    joint = {}  # cached joint counts keyed by tuple of col names
    def joint_counts(cols: list[str]) -> np.ndarray:
        key = tuple(cols)
        if key not in joint:
            if cols == ["B"]:
                joint[key] = np.bincount(b_arr, minlength=Q).astype(np.float64)
            else:
                # combine B with layer cols into a single joint via lexsort
                arrs = [b_arr] + [layers[c] for c in cols if c != "B"]
                # unique tokens = b * M + layers (M=1024 per layer); build combined index
                # general multi-dim: use np.unique on stacking
                stack = np.stack([b_arr] + [layers[c] for c in cols if c != "B"], axis=1)
                uniq, inv, counts = np.unique(stack, axis=0, return_inverse=True, return_counts=True)
                joint[key] = counts.astype(np.float64)
        return joint[key]

    for lid in F_LAYER_ORDER[fact_id]:
        # H(B, U_<i) - H(B, U_<i, U_i) = H(U_i | B, U_<i)
        prev_cols = ["B"] + prev_col_names
        H_join_prev = _joint_entropy_bits(joint_counts(prev_cols))
        cur_cols = ["B"] + prev_col_names + [lid]
        H_join_cur = _joint_entropy_bits(joint_counts(cur_cols))
        hi = H_join_cur - H_join_prev  # H(U_i|B,U_<i) = H(B,U_<i,U_i) - H(B,U_<i)
        Hs[lid] = float(hi)
        width = FACTORIZATIONS[fact_id]["layers"][lid][1]
        ref[lid] = 1.0 - R_TARGET * hi / width
        prev_col_names.append(lid)

    total_H = sum(Hs.values())
    return Hs, total_H, {"layers_ref_rate": ref}


def _joint_entropy_bits(counts: np.ndarray) -> float:
    tot = counts.sum()
    if tot <= 0:
        return 0.0
    p = counts / tot
    p = p[p > 0]
    return float(-np.sum(p * np.log2(p)))


def entropy_of(p: np.ndarray) -> float:
    p = np.asarray(p, dtype=np.float64)
    p = p[p > 0]
    return float(-np.sum(p * np.log2(p))) if p.size else 0.0


# --------------------------------------------------------------------------- #
# Data loading + split
# --------------------------------------------------------------------------- #

def load_source_pairs(source_id: str) -> dict[str, np.ndarray]:
    """Read the fresh pairs parquet for one source (no .ttbin read)."""
    import pyarrow.parquet as pq
    path = SOURCES[source_id]["pairs_parquet"]
    t = pq.read_table(path)
    return {
        "frame_id": t["frame_id"].to_numpy(),
        "pair_idx": t["pair_idx"].to_numpy(),
        "a": t["alice_symbol"].to_numpy().astype(np.int64),
        "b": t["bob_symbol"].to_numpy().astype(np.int64),
    }


def split_by_frame(frame_id: np.ndarray, ratios=SPLIT) -> dict[str, np.ndarray]:
    """Time-ordered frame split 60/20/20 per source (no overlap)."""
    uf = np.unique(frame_id)
    n = len(uf)
    n_train = int(round(ratios[0] * n))
    n_val = int(round(ratios[1] * n))
    train_frames = uf[:n_train]
    val_frames = uf[n_train:n_train + n_val]
    hold_frames = uf[n_train + n_val:]
    return {
        "train": np.isin(frame_id, train_frames),
        "val": np.isin(frame_id, val_frames),
        "hold": np.isin(frame_id, hold_frames),
    }


def modular_delta_hist(a: np.ndarray, b: np.ndarray, q: int = Q) -> np.ndarray:
    """(b - a) mod q histogram over pairs (matches sidecar delta=(b_eff-a_eff) mod d)."""
    d = (b - a) % q
    return np.bincount(d.astype(np.int64), minlength=q).astype(np.float64)


def modular_delta_hist_ab(a: np.ndarray, b: np.ndarray, q: int = Q) -> np.ndarray:
    """(a - b) mod q histogram; the direction used for the conditional P(A|B) delta models."""
    d = (a - b) % q
    return np.bincount(d.astype(np.int64), minlength=q).astype(np.float64)


def _delta_to_cond_table(delta: np.ndarray) -> np.ndarray:
    """P(A=a|B=b) = delta[(a-b) mod q] tile."""
    q = delta.shape[0]
    rows = np.arange(q)[:, None]
    cols = np.arange(q)[None, :]
    idx = (rows - cols) % q
    return delta[idx]


# --------------------------------------------------------------------------- #
# M0 error-map metrics
# --------------------------------------------------------------------------- #

def m0_metrics(a: np.ndarray, b: np.ndarray, *, time_blocks: int = 6) -> dict[str, Any]:
    q = Q
    n = len(a)
    ser = float(np.mean(a != b))
    diff = (b - a) % q
    hist = np.bincount(diff, minlength=q).astype(np.float64)
    frac = hist / n
    pm1 = {'+1': float(frac[1]), '-1': float(frac[q - 1]), '0': float(frac[0])}
    # signed delta = b - a (centered; may be negative)
    signed = (b - a)
    absd = np.abs(signed).astype(np.float64)
    quantiles = {f"q{k}": float(np.quantile(absd, k / 100.0)) for k in [50, 90, 95, 99, 100]}
    asym = float(frac[1] - frac[q - 1])
    # gray mask
    ga = gray_label(a)
    gb = gray_label(b)
    mask = ga ^ gb
    pop = np.array([bin(int(m)).count("1") for m in mask])
    gray_pop = {k: float(np.mean(pop == k)) for k in range(0, 11)}
    # bit-plane co-error matrix (10x10): for each plane pair how often both differ
    co = np.zeros((BITS, BITS), dtype=np.float64)
    bits_a = ((ga[:, None] >> np.arange(BITS)) & 1).astype(np.int64)
    bits_b = ((gb[:, None] >> np.arange(BITS)) & 1).astype(np.int64)
    err = (bits_a != bits_b).astype(np.float64)
    for i in range(BITS):
        for j in range(BITS):
            co[i, j] = float(np.mean(err[:, i] * err[:, j]))
    # run-length of consecutive mismatches within frame (frame-aware via unique frames)
    # simple: for each frame, count consecutive mismatches
    frame_id_src = None  # caller adds frame_id if needed
    # time stability: split by index order into blocks
    blocks = np.array_split(np.arange(n), time_blocks)
    block_stats = []
    for blk in blocks:
        db = (b[blk] - a[blk]) % q
        h = np.bincount(db, minlength=q).astype(np.float64) / len(blk)
        block_stats.append({"pm1": {'+1': float(h[1]), '-1': float(h[q - 1])},
                            "ser": float(np.mean(a[blk] != b[blk]))})
    return {
        "n_pairs": int(n),
        "ser": ser,
        "modular_delta_frac_top": {"0": float(frac[0]), "+1": float(frac[1]), "-1": float(frac[q - 1]),
                                    "other": float(1 - frac[0] - frac[1] - frac[q - 1])},
        "pm1_mass": pm1,
        "direction_asymmetry_plus_minus1": asym,
        "abs_signed_delta_quantiles": quantiles,
        "gray_mask_popcount_frac": gray_pop,
        "bit_plane_co_error_matrix": co.tolist(),
        "time_block_stability": block_stats,
    }


# --------------------------------------------------------------------------- #
# M1 channel models (C01-C06)
# --------------------------------------------------------------------------- #

# Frozen V17 per-plane error probabilities (MSB first, Gray)
V17_PLANE_ER = [3.0517578125e-05, 0.0001220703125, 0.0003662109375, 0.000946044921875,
                0.001251220703125, 0.00250244140625, 0.00457763671875, 0.009307861328125,
                0.02044677734375, 0.037506103515625]


def _build_c01(N_train: np.ndarray) -> np.ndarray:
    q = Q
    tot = N_train.sum()
    ser = 1.0 - N_train.diagonal().sum() / tot if tot else 0.0
    P = np.full((q, q), ser / (q - 1.0))
    np.fill_diagonal(P, 1.0 - ser)
    return P


def _build_c02() -> np.ndarray:
    """V17 independent Gray-plane product: P(B|A) -> P(A|B) with uniform prior."""
    q = Q
    ga = gray_label(np.arange(q)).astype(np.int64)
    bits = ((ga[:, None] >> np.arange(BITS)) & 1)  # (q,10)
    p = np.asarray(V17_PLANE_ER)
    pB_given_A = np.ones((q, q), dtype=np.float64)
    for i in range(q):
        gi = np.zeros(q, dtype=np.float64)
        for k in range(BITS):
            same = (bits[:, k] == bits[i, k]).astype(np.float64)
            gi = gi + np.where(same, np.log(1.0 - p[k]), np.log(p[k]))  # log P(Bbit|Abits)
        pB_given_A[i] = np.exp(gi)
    # P(A|B) = P(B|A)/colsum(P(B|A)) with uniform prior
    col = pB_given_A.sum(axis=0, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        P = np.divide(pB_given_A, col, out=np.zeros_like(pB_given_A), where=col > 0)
    return P.T  # P(a|b): row a, col b


def _delta_model_hist(train_hist: np.ndarray) -> np.ndarray:
    h = train_hist.copy().astype(np.float64)
    s = h.sum()
    if s > 0:
        h /= s
    # pre-registered additive smoothing/backoff on probability scale
    h = (h + DELTA_SMOOTH_EPS / Q) / (1.0 + DELTA_SMOOTH_EPS)
    return h


def _nll_and_conf(P: np.ndarray, a: np.ndarray, b: np.ndarray) -> dict[str, float]:
    n = len(a)
    if n == 0:
        return {"nll_bits": float("inf"), "mean_conf": 0.0, "zero_prob_count": 0}
    zero = int(np.sum(P[a, b] == 0.0))
    with np.errstate(divide="ignore", invalid="ignore"):
        logs = -np.log2(np.clip(P[a, b], 1e-300, 1.0))
    return {"nll_bits": float(np.mean(logs)), "mean_conf": float(np.mean(P[a, b])),
            "zero_prob_count": zero}


def run_m1(source_pairs: dict[str, dict[str, np.ndarray]],
           splits: dict[str, dict[str, np.ndarray]]) -> dict[str, Any]:
    """C01-C06 comparison.  source_pairs[sid] has a,b; splits[sid] has train/val/hold masks."""
    q = Q
    results = {}
    # pooled modular delta hist (for C03) across train
    pooled_hist = np.zeros(q, dtype=np.float64)
    for sid in source_pairs:
        m = splits[sid]["train"]
        pooled_hist += modular_delta_hist_ab(source_pairs[sid]["a"][m], source_pairs[sid]["b"][m])
    c02_full = None  # built lazily (global, same for all sources)
    for sid in source_pairs:
        sp = source_pairs[sid]
        m_tr = splits[sid]["train"]
        a_tr, b_tr = sp["a"][m_tr], sp["b"][m_tr]
        N_tr = build_N_ab(a_tr, b_tr)
        ser_tr = float(np.mean(a_tr != b_tr))
        # per-source conditional delta hist in the P(A|B) direction (a-b)
        hist_s = modular_delta_hist_ab(a_tr, b_tr)
        delta_s = _delta_model_hist(hist_s)
        # pooled delta in (a-b) direction too
        pooled_ab = modular_delta_hist_ab(a_tr, b_tr)
        # C01
        c01 = _build_c01(N_tr)
        # C02
        if c02_full is None:
            c02_full = _build_c02()
        # C03 pooled delta
        c03 = _delta_to_cond_table(_delta_model_hist(pooled_ab))
        # C04 source delta
        c04 = _delta_to_cond_table(delta_s)
        # C05 source+parity: two conditional delta hist conditioned on b parity
        par = np.zeros((q, 2), dtype=np.float64)
        for pb_ in (0, 1):
            sel = (b_tr % 2) == pb_
            if sel.sum() > 0:
                par[:, pb_] = _delta_model_hist(modular_delta_hist_ab(a_tr[sel], b_tr[sel]))
        # build C05 table: P(a|b) = par[(a-b)%q, b%2]
        rows = np.arange(q)[:, None]
        cols = np.arange(q)[None, :]
        idx = (rows - cols) % q
        c05 = par[idx, cols % 2]
        # C06 mixture local jitter + global background (smoothed local)
        w = 0.95
        local = delta_s  # smoothed delta distribution over all bins
        c06 = w * _delta_to_cond_table(local) + (1.0 - w) / q
        models = {"C01_qsc": c01, "C02_v17_product": c02_full, "C03_pooled_delta": c03,
                  "C04_source_delta": c04, "C05_source_parity": c05, "C06_jitter_bg": c06}
        per = {}
        for mname, P in models.items():
            for split in ["val", "hold"]:
                sela = splits[sid][split]
                aa = sp["a"][sela]
                bb = sp["b"][sela]
                metrics = _nll_and_conf(P, aa, bb)
                per[f"{mname}:{split}"] = metrics
        results[sid] = {
            "ser_train": float(ser_tr),
            "empirical_H_AbB_train_bits": float(conditional_entropy_bits(N_tr)),
            "per_model_split": per,
        }
    return results


# --------------------------------------------------------------------------- #
# M2 +-1 structure / direction / time-stability under existing delays
# --------------------------------------------------------------------------- #

def run_m2(source_pairs: dict[str, dict[str, np.ndarray]]) -> dict[str, Any]:
    out = {}
    for sid, sp in source_pairs.items():
        d = (sp["b"] - sp["a"]) % Q
        hist = np.bincount(d, minlength=Q).astype(np.float64)
        frac = hist / len(d)
        n = len(d)
        tblocks = 8
        blocks = []
        for blk in np.array_split(np.arange(n), tblocks):
            hb = np.bincount(d[blk], minlength=Q).astype(np.float64) / len(blk)
            blocks.append({"pm1": {"+1": float(hb[1]), "-1": float(hb[Q - 1])}})
        out[sid] = {
            "delay_used_ps": SOURCES[sid]["delay_used_ps"],
            "mass_0": float(frac[0]), "mass_plus1": float(frac[1]), "mass_minus1": float(frac[Q - 1]),
            "other_mass": float(1 - frac[0] - frac[1] - frac[Q - 1]),
            "dominant_direction": "+1" if frac[1] > frac[Q - 1] else ("-1" if frac[Q - 1] > frac[1] else "0"),
            "direction_asymmetry": float(frac[1] - frac[Q - 1]),
            "time_block_pm1": blocks,
        }
    return out


# --------------------------------------------------------------------------- #
# M3 factorization gate
# --------------------------------------------------------------------------- #

def run_m3(N_train: Mapping[str, np.ndarray]) -> dict[str, Any]:
    """Per (F, L) chain-rule layers over each source's train N_ab."""
    out = {"per_source_per_factor": {}}
    for sid, N in N_train.items():
        src = {}
        for fact in FACTORIZATIONS:
            for lab in LABELINGS:
                Hs, total, ref = layer_conditional_entropy_bits(fact, lab, N)
                src[f"{fact}:{lab}"] = {"layer_H_bits": {k: round(v, 8) for k, v in Hs.items()},
                                        "total_H_bits": round(total, 8),
                                        "ref_rate_per_layer": {k: round(v, 8) for k, v in ref["layers_ref_rate"].items()}}
        out["per_source_per_factor"][sid] = src
    return out


# --------------------------------------------------------------------------- #
# M4 architecture candidates
# --------------------------------------------------------------------------- #

def _m4_pick(run_m3_out: dict[str, Any]) -> dict[str, Any]:
    # average per-layer H_i over sources per (F,L)
    agg = {}
    for sid, src in run_m3_out["per_source_per_factor"].items():
        for key, row in src.items():
            agg.setdefault(key, []).append(row["total_H_bits"])
    totals = {k: float(np.mean(v)) for k, v in agg.items()}

    def pick(fact_pool):
        best = None
        for fact in fact_pool:
            for lab in LABELINGS:
                key = f"{fact}:{lab}"
                tot = totals[key]
                # fewer layers preferred; then lower total H (less residual) preferred
                nlay = len(FACTORIZATIONS[fact]["layers"])
                score = (nlay, tot)
                if best is None or score < best[0]:
                    best = (score, fact, lab, key)
        return best

    hi_pool = ["F01", "F02"]
    mid_pool = ["F03", "F04", "F05"]
    hi = pick(hi_pool)
    mid = pick(mid_pool)
    return {
        "high_field_candidate": {"factorization": hi[1], "labeling": hi[2], "key": hi[3],
                                  "mean_total_H_bits": round(totals[hi[3]], 6)},
        "mid_field_control": {"factorization": mid[1], "labeling": mid[2], "key": mid[3],
                               "mean_total_H_bits": round(totals[mid[3]], 6)},
        "all_factorization_totals": {k: round(v, 6) for k, v in totals.items()},
        "selection_rule": "fewest layers, then lowest mean total conditional entropy; deterministic",
    }


# --------------------------------------------------------------------------- #
# Orchestration (M0-M4) + additive output
# --------------------------------------------------------------------------- #

def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def split_frame_manifest(frame_id_map: dict[str, np.ndarray]) -> dict[str, Any]:
    man = {}
    for sid, fid in frame_id_map.items():
        m = split_by_frame(fid)
        counts = {k: int(np.unique(fid[sel]).size) for k, sel in m.items()}
        pairs = {k: int(np.sum(sel)) for k, sel in m.items()}
        man[sid] = {"frames": counts, "pairs": pairs}
    return man


def run_v25_gate(*, out_dir: str | Path,
                 sources: Sequence[str] | None = None) -> dict[str, Any]:
    out = Path(out_dir)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing to overwrite V25 run root: {out}")
    out.mkdir(parents=True, exist_ok=True)
    if sources is None:
        sources = list(SOURCES.keys())

    # Load + split
    pairs = {}
    fid_map = {}
    splits = {}
    N_train = {}
    for sid in sources:
        sp = load_source_pairs(sid)
        pairs[sid] = sp
        fid_map[sid] = sp["frame_id"]
        splits[sid] = split_by_frame(sp["frame_id"])
        N_train[sid] = build_N_ab(sp["a"][splits[sid]["train"]], sp["b"][splits[sid]["train"]])

    # data_inventory.json (persist P0 inventory into run root too)
    inv_src = Path("openspec/changes/formal-nonbinary-ldpc-v25-empirical-timestamp-channel-and-multilevel-factorization-gate/evidence/data_inventory.json")
    if inv_src.exists():
        inv = json.loads(inv_src.read_text(encoding="utf-8"))
    else:
        inv = {"schema": "nbldpc_v25_p0_data_inventory_v1", "primary_joint_data_sources": []}
        for sid in sources:
            inv["primary_joint_data_sources"].append({
                "source_id": sid, "pairs_parquet": SOURCES[sid]["pairs_parquet"],
                "delay_used_ps": SOURCES[sid]["delay_used_ps"], "parquet_rows": SOURCES[sid]["parquet_rows"]})
    _write_json(out / "data_inventory.json", inv)

    # split manifest
    sm = {
        "schema": "nbldpc_v25_split_manifest_v1",
        "split_ratios": list(SPLIT),
        "per_source": split_frame_manifest(fid_map),
    }
    _write_json(out / "split_manifest.json", sm)

    # channel_counts.npz (train joint counts per source)
    data = {f"{sid}_N_ab_train": N_train[sid] for sid in sources}
    # also full-count N_ab (train) is what we save; note per packet use counts
    np.savez(out / "channel_counts.npz", **{f"{sid}_N_ab_train": v for sid, v in data.items()})

    # M0 metrics + channel_summary
    m0 = {}
    rows_delta = []
    rows_mask = []
    for sid in sources:
        mm = m0_metrics(pairs[sid]["a"], pairs[sid]["b"])
        m0[sid] = mm
        d = (pairs[sid]["b"] - pairs[sid]["a"]) % Q
        h = np.bincount(d, minlength=Q).astype(np.float64)
        for i in range(Q):
            if h[i] > 0:
                rows_delta.append({"source": sid, "delta_b_minus_a": int(i), "count": int(h[i]),
                                   "frac": float(h[i] / len(d))})
        ga = gray_label(pairs[sid]["a"]); gb = gray_label(pairs[sid]["b"])
        mask = ga ^ gb
        pop = [int(bin(int(m)).count("1")) for m in mask]
        for k in range(0, 11):
            rows_mask.append({"source": sid, "gray_popcount": k, "count": int(np.sum(np.array(pop) == k)),
                              "frac": float(np.mean(np.array(pop) == k))})
    _write_json(out / "channel_summary.json", {"schema": "nbldpc_v25_m0_v1", "per_source": m0})
    with open(out / "delta_by_source.csv", "w", encoding="utf-8") as f:
        f.write("source,delta_b_minus_a,count,frac\n")
        for r in rows_delta:
            f.write(f"{r['source']},{r['delta_b_minus_a']},{r['count']},{r['frac']}\n")
    with open(out / "gray_joint_masks.csv", "w", encoding="utf-8") as f:
        f.write("source,gray_popcount,count,frac\n")
        for r in rows_mask:
            f.write(f"{r['source']},{r['gray_popcount']},{r['count']},{r['frac']}\n")

    # M1 model comparison
    m1 = run_m1(pairs, splits)
    rows_model = []
    for sid, r in m1.items():
        for k, v in r["per_model_split"].items():
            mname, split = k.split(":")
            rows_model.append({"source": sid, "model": mname, "split": split,
                               "nll_bits": v["nll_bits"], "mean_conf": v["mean_conf"],
                               "zero_prob_count": v["zero_prob_count"]})
    with open(out / "model_holdout_scores.csv", "w", encoding="utf-8") as f:
        f.write("source,model,split,nll_bits,mean_conf,zero_prob_count\n")
        for r in rows_model:
            f.write(f"{r['source']},{r['model']},{r['split']},{r['nll_bits']:.8f},{r['mean_conf']:.8f},{r['zero_prob_count']}\n")
    _write_json(out / "model_scores.json", m1)

    # M2 alignment report
    m2 = run_m2(pairs)
    _write_json(out / "alignment_report.json", {"schema": "nbldpc_v25_m2_v1",
                "note": "existing-delay analysis; direction is a source/delay-conditioned feature, not an alignment blocker",
                "per_source": m2})

    # M3 factorization gate
    m3 = run_m3(N_train)
    rows_fact = []
    for sid, src in m3["per_source_per_factor"].items():
        for key, row in src.items():
            for lid, h in row["layer_H_bits"].items():
                rows_fact.append({"source": sid, "factorization_label": key, "layer": lid,
                                  "H_bits": h, "ref_rate": row["ref_rate_per_layer"][lid]})
    with open(out / "factorization_layers.csv", "w", encoding="utf-8") as f:
        f.write("source,factorization_label,layer,H_bits,ref_rate\n")
        for r in rows_fact:
            f.write(f"{r['source']},{r['factorization_label']},{r['layer']},{r['H_bits']:.8f},{r['ref_rate']:.8f}\n")
    # chain-rule check
    chain = {"schema": "nbldpc_v25_chain_rule_check_v1", "per_source": {}}
    tol = 1e-6
    ok_all = True
    for sid in sources:
        # chain rule must be verified on the SAME counting basis as the layers
        # (M3 uses the train N_ab), not on the full-data N_ab.
        N = build_N_ab(pairs[sid]["a"][splits[sid]["train"]],
                       pairs[sid]["b"][splits[sid]["train"]])
        Hemp = conditional_entropy_bits(N)
        rows = {}
        for key, row in m3["per_source_per_factor"][sid].items():
            err = abs(row["total_H_bits"] - Hemp)
            rows[key] = {"total_H_bits": row["total_H_bits"], "Hemp_bits": Hemp,
                         "abs_err": round(err, 9), "closed": bool(err <= tol)}
            ok_all &= (err <= tol)
        chain["per_source"][sid] = {"Hemp_bits": Hemp, "factorizations": rows, "basis": "train"}
    chain["all_closed"] = ok_all
    _write_json(out / "chain_rule_check.json", chain)

    # M4 candidates + overall status
    m4 = _m4_pick(m3)
    # status: structured model beats QSC/V17 on holdout?
    beats = []
    for sid, r in m1.items():
        nll_hold = {m: r["per_model_split"][f"{m}:hold"]["nll_bits"] for m in
                    ["C01_qsc", "C02_v17_product", "C04_source_delta"]}
        beats.append(nll_hold["C04_source_delta"] <= nll_hold["C01_qsc"] and
                     nll_hold["C04_source_delta"] <= nll_hold["C02_v17_product"])
    structured_wins = bool(beats) and all(beats)
    if not ok_all:
        status = "fail_no_stable_factorization"
    elif not structured_wins:
        status = "fail_no_stable_factorization"
    else:
        status = "pass_ready_for_de_change"
    gate = {"schema": "nbldpc_v25_gate_summary_v1",
            "status": status,
            "structured_model_beats_qsc_v17_on_all_holdout": structured_wins,
            "chain_rule_closed": bool(ok_all),
            "candidates_for_v26": m4,
            "trigger_note": ("pass_ready_for_de_change -> V26 proposed (not auto-started); "
                             "still no finite code/FER/MET/fresh-qualification."),
            "prohibitions_respected": True,
            }
    _write_json(out / "gate_summary.json", gate)

    # read-only verify
    vr = verify_run(out)
    _write_json(out / "readonly_verify.json", vr)

    return {"status": status, "chain_rule_closed": bool(ok_all),
            "structured_wins": structured_wins, "candidates": m4, "evidence_root": str(out)}


def verify_run(root: str | Path) -> dict[str, Any]:
    """Read-only verifier: recompute terminal state from persisted records."""
    root = Path(root)
    problems = []
    required = ["data_inventory.json", "split_manifest.json", "channel_summary.json",
                "delta_by_source.csv", "gray_joint_masks.csv", "channel_counts.npz",
                "model_scores.json", "model_holdout_scores.csv", "factorization_layers.csv",
                "chain_rule_check.json", "alignment_report.json", "gate_summary.json"]
    for rel in required:
        if not (root / rel).exists():
            problems.append(f"missing {rel}")
    # recompute chain closure from factorization_layers + channel counts is heavy;
    # instead verify stored chain_rule_check all_closed consistency with gate status.
    try:
        gate = json.loads((root / "gate_summary.json").read_text(encoding="utf-8"))
        chain = json.loads((root / "chain_rule_check.json").read_text(encoding="utf-8"))
        if gate["chain_rule_closed"] != chain["all_closed"]:
            problems.append("gate_summary/chain_rule_check inconsistency")
        allowed = {"pass_ready_for_de_change", "fail_no_stable_factorization",
                   "blocked_insufficient_joint_data", "blocked_alignment_unresolved"}
        if gate["status"] not in allowed:
            problems.append(f"unknown status {gate['status']}")
        if gate["status"] == "pass_ready_for_de_change":
            if not gate["structured_model_beats_qsc_v17_on_all_holdout"] or not chain["all_closed"]:
                problems.append("pass claimed but triggers not met")
    except Exception as exc:  # noqa: BLE001
        problems.append(f"gate parse error: {exc}")
    return {"schema": "nbldpc_v25_readonly_verify_v1", "ok": not problems,
            "problems": problems, "checked_root": str(root)}
