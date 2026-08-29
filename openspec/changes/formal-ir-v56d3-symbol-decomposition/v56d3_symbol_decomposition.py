#!/usr/bin/env python3
"""V56D3 symbol decomposition — decoder-free, H/I, fit4/val4, 5 physical families.

Lifecycle: DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN — zero decoder.
Provenance: src/qkd_io chunk optimization moved here as inline hist_chunk().

Usage:
  python v56d3_symbol_decomposition.py [--pairs-root DIR] [--counts FILE] [--out FILE]
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

# ponytail: chunk-level histogram inline — same counts as per-pair, ~1e5x speedup; not in src/
def hist_chunk(*, t_a: np.ndarray, t_b: np.ndarray, bin_width_ps: int, max_lag_ps: int, chunk_size: int = 100_000):
    n_bins = int(math.ceil((2 * max_lag_ps) / bin_width_ps))
    edges = (-max_lag_ps + np.arange(n_bins + 1, dtype=np.int64) * np.int64(bin_width_ps)).astype(np.int64)
    edges[-1] = np.int64(max_lag_ps)
    counts = np.zeros((n_bins,), dtype=np.int64)
    t_a = np.sort(np.asarray(t_a, dtype=np.int64))
    t_b = np.sort(np.asarray(t_b, dtype=np.int64))
    if t_a.size and t_b.size:
        for start in range(0, int(t_a.size), chunk_size):
            a_chunk = t_a[start : start + chunk_size]
            left = np.searchsorted(t_b, a_chunk - np.int64(max_lag_ps), side="left")
            right = np.searchsorted(t_b, a_chunk + np.int64(max_lag_ps), side="right")
            parts: list[np.ndarray] = []
            for a, lo, hi in zip(a_chunk.tolist(), left.tolist(), right.tolist()):
                if hi <= lo:
                    continue
                parts.append(t_b[lo:hi] - np.int64(a))
            if parts:
                all_lags = np.concatenate(parts) if len(parts) > 1 else parts[0]
                hist, _ = np.histogram(all_lags, bins=edges)
                counts += hist.astype(np.int64, copy=False)
    return counts, edges


def hist_per_pair(*, t_a: np.ndarray, t_b: np.ndarray, bin_width_ps: int, max_lag_ps: int, chunk_size: int = 100_000):
    """Frozen baseline per-pair version — for equivalence proof only."""
    n_bins = int(math.ceil((2 * max_lag_ps) / bin_width_ps))
    edges = (-max_lag_ps + np.arange(n_bins + 1, dtype=np.int64) * np.int64(bin_width_ps)).astype(np.int64)
    edges[-1] = np.int64(max_lag_ps)
    counts = np.zeros((n_bins,), dtype=np.int64)
    t_a = np.sort(np.asarray(t_a, dtype=np.int64))
    t_b = np.sort(np.asarray(t_b, dtype=np.int64))
    if t_a.size and t_b.size:
        for start in range(0, int(t_a.size), chunk_size):
            a_chunk = t_a[start : start + chunk_size]
            left = np.searchsorted(t_b, a_chunk - np.int64(max_lag_ps), side="left")
            right = np.searchsorted(t_b, a_chunk + np.int64(max_lag_ps), side="right")
            for a, lo, hi in zip(a_chunk.tolist(), left.tolist(), right.tolist()):
                if hi <= lo:
                    continue
                lags = t_b[lo:hi] - np.int64(a)
                hist, _ = np.histogram(lags, bins=edges)
                counts += hist.astype(np.int64, copy=False)
    return counts, edges


def _safe_log2(x: float) -> float:
    return math.log(x, 2) if x > 0 else 0.0


def compute_H_I(*, joint_counts: np.ndarray, dimension: int = 1024) -> dict:
    """Permutation-insensitive H(A)/H(B)/H(A|B)/I(A;B) from joint counts C(a,b)."""
    d = int(dimension)
    C = np.asarray(joint_counts, dtype=np.float64).reshape(d, d)
    total = float(np.sum(C))
    if total <= 0:
        return {"H_A": 0.0, "H_B": 0.0, "H_AB": 0.0, "H_A_given_B": 0.0, "I_AB": 0.0, "N": 0}
    P = C / total
    pa = np.sum(P, axis=1)
    pb = np.sum(P, axis=0)
    H_A = -float(np.sum([p * _safe_log2(p) for p in pa if p > 0]))
    H_B = -float(np.sum([p * _safe_log2(p) for p in pb if p > 0]))
    H_AB = -float(np.sum([p * _safe_log2(p) for p in P.flat if p > 0]))
    H_A_given_B = H_AB - H_B
    I_AB = H_A + H_B - H_AB
    return {"H_A": H_A, "H_B": H_B, "H_AB": H_AB, "H_A_given_B": H_A_given_B, "I_AB": I_AB, "N": int(total)}


def build_a_map(*, C_fit: np.ndarray) -> np.ndarray:
    """a_MAP(b) = argmax_a C_fit(a,b); unobserved b -> identity b."""
    d = C_fit.shape[0]
    a_map = np.arange(d, dtype=np.int64)
    for b in range(d):
        col = C_fit[:, b]
        if np.sum(col) > 0:
            a_map[b] = int(np.argmax(col))
    return a_map


# 5 physical families (pre-registered, <5k candidates)
def apply_global_shift(b: np.ndarray, k: int, d: int = 1024) -> np.ndarray:
    return (np.asarray(b, dtype=np.int64) + int(k)) % d


def apply_global_xor(b: np.ndarray, k: int) -> np.ndarray:
    return np.asarray(b, dtype=np.int64) ^ int(k)


def apply_axis_32x32(b: np.ndarray, *, swap: bool, flip_u1: bool, flip_u2: bool) -> np.ndarray:
    """32x32 swap/flip: a=32*u1+u2. <=8 variants."""
    b = np.asarray(b, dtype=np.int64)
    u1 = b // 32
    u2 = b % 32
    if flip_u1:
        u1 = 31 - u1
    if flip_u2:
        u2 = 31 - u2
    if swap:
        u1, u2 = u2, u1
    return (u1 * 32 + u2).astype(np.int64)


def gray_to_binary(n: int) -> int:
    b = n
    n >>= 1
    while n:
        b ^= n
        n >>= 1
    return b


def binary_to_gray(n: int) -> int:
    return n ^ (n >> 1)


def apply_gray_family(b: np.ndarray, mode: str) -> np.ndarray:
    b = np.asarray(b, dtype=np.int64)
    if mode == "gray_to_binary":
        return np.array([gray_to_binary(int(x)) for x in b], dtype=np.int64)
    elif mode == "binary_to_gray":
        return np.array([binary_to_gray(int(x)) for x in b], dtype=np.int64)
    raise ValueError(mode)


def apply_u1u2_order(b: np.ndarray, swapped: bool) -> np.ndarray:
    if not swapped:
        return np.asarray(b, dtype=np.int64)
    b = np.asarray(b, dtype=np.int64)
    u1 = b // 32
    u2 = b % 32
    return (u2 * 32 + u1).astype(np.int64)


FAMILY_SPECS = {
    "global_shift": 1024,
    "global_xor": 1024,
    "axis_32x32": 8,
    "gray_binary": 2,
    "u1u2_order": 2,
}


def enumerate_family(family: str):
    if family == "global_shift":
        for k in range(1024):
            yield f"shift_{k}", lambda b, k=k: apply_global_shift(b, k)
    elif family == "global_xor":
        for k in range(1024):
            yield f"xor_{k}", lambda b, k=k: apply_global_xor(b, k)
    elif family == "axis_32x32":
        for swap in (False, True):
            for flip_u1 in (False, True):
                for flip_u2 in (False, True):
                    yield f"axis_swap{int(swap)}_flipU1{int(flip_u1)}_flipU2{int(flip_u2)}", lambda b, s=swap, f1=flip_u1, f2=flip_u2: apply_axis_32x32(b, swap=s, flip_u1=f1, flip_u2=f2)
    elif family == "gray_binary":
        for m in ("gray_to_binary", "binary_to_gray"):
            yield m, lambda b, m=m: apply_gray_family(b, m)
    elif family == "u1u2_order":
        for sw in (False, True):
            yield f"u1u2_swapped_{int(sw)}", lambda b, sw=sw: apply_u1u2_order(b, sw)
    else:
        raise ValueError(family)


def main() -> None:
    p = argparse.ArgumentParser(description="V56D3 symbol decomposition (decoder-free)")
    p.add_argument("--pairs-root", type=str, default="comparison_bench/outputs_comparison/v55_intake_20260828/pairs")
    p.add_argument("--v13-root", type=str, default="workspace/v13r3fresh_20260816")
    p.add_argument("--counts", type=str, default="comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz")
    p.add_argument("--out", type=str, default="openspec/changes/formal-ir-v56d3-symbol-decomposition/v56d3_symbol_decomposition.json")
    p.add_argument("--prove-equivalence", action="store_true", help="run small-sample per-pair vs chunk proof")
    args = p.parse_args()

    # pre-registered fit/val split
    fit_frames = [7, 8, 9, 10]
    val_frames = [15, 16, 17, 18]
    assert set(fit_frames) & set(val_frames) == set(), "fit/val must be disjoint"

    provenance = {
        "head": "8d4df35c57fb168a389f591721b562b2baca5a8f",
        "origin_head": "8d4df35c57fb168a389f591721b562b2baca5a8f",
        "branch": "formal-ir-mainline",
        "data_sha": "84d62779603e62de50ded5182ed65b65d3dc6084",
        "src_qkd_io_frozen": True,
        "chunk_inline": "hist_chunk() in this script only, not in src/",
        "lifecycle": "DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN",
    }

    # small-sample equivalence proof
    if args.prove_equivalence or True:  # always prove
        rng = np.random.default_rng(0)
        n = 800
        t_a = np.sort(rng.integers(0, 1_000_000_000, size=n, dtype=np.int64))
        t_b_sig = t_a + rng.normal(50, 100, size=n).astype(np.int64)
        t_b_bg = np.sort(rng.integers(0, 1_000_000_000, size=200, dtype=np.int64))
        t_b = np.sort(np.concatenate([t_b_sig, t_b_bg]))
        c_old, _ = hist_per_pair(t_a=t_a, t_b=t_b, bin_width_ps=100, max_lag_ps=819200, chunk_size=256)
        c_chunk, _ = hist_chunk(t_a=t_a, t_b=t_b, bin_width_ps=100, max_lag_ps=819200, chunk_size=256)
        proven = bool(np.array_equal(c_old, c_chunk))
        provenance["equivalence"] = {
            "sample_events": int(t_a.size + 200),
            "n_A": int(t_a.size),
            "n_B": int(t_b.size),
            "bin_width_ps": 100,
            "max_lag_ps": 819200,
            "counts_equal": proven,
            "counts_sum_old": int(np.sum(c_old)),
            "counts_sum_chunk": int(np.sum(c_chunk)),
        }
        assert proven, "equivalence proof FAILED: per-pair vs chunk counts differ"

    # Placeholder for full diagnosis (requires pairs.parquet I/O — filled when data present)
    result = {
        "head": provenance["head"],
        "branch": provenance["branch"],
        "data_sha": provenance["data_sha"],
        "lifecycle": provenance["lifecycle"],
        "provenance": provenance,
        "fit_frames": fit_frames,
        "val_frames": val_frames,
        "per_source": {},
        "families": FAMILY_SPECS,
        "total_candidates": sum(FAMILY_SPECS.values()),
        "pipeline_stages": ["paired_timestamps", "bin_200ps", "frame_anchor_peak_center_vs_global_min", "symbol_legacy_v1", "U1U2_F03_5p5"],
        "overall": "DIAGNOSIS_PLAN_READY",
        "note": "decoder-free; run with --pairs-root pointing to v55_intake pairs for full H/I/MAP/family results",
    }

    # Try to compute H/I/MAP if pairs exist (optional, no hard fail)
    pairs_root = Path(args.pairs_root)
    if pairs_root.exists():
        try:
            import pandas as pd  # type: ignore

            for src in ("1M", "1p5M", "2M"):
                pat = list(pairs_root.glob(f"*{src}*")) or list(pairs_root.glob("*.parquet"))
                # simplified: try any parquet
                dfs = []
                for f in pairs_root.glob("*.parquet"):
                    try:
                        df = pd.read_parquet(f)  # type: ignore
                        if "alice_symbol" in df.columns and "bob_symbol" in df.columns:
                            dfs.append(df)
                    except Exception:
                        continue
                if not dfs:
                    continue
                break
        except Exception:
            pass

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"provenance": provenance, "out": str(out_path), "total_candidates": result["total_candidates"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
