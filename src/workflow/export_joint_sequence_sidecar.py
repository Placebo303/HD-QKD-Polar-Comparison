#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.workflow.coarse_grain_joint import coarse_grain_sparse_joint, dense_from_sparse  # type: ignore
from src.workflow.llr_from_joint import load_joint_counts_sparse_from_metrics  # type: ignore
from src.reconciliation.run_nbldpc_demo_point import (  # type: ignore
    _bin_indices_sorted_for_binwidth,
    _load_artifacts,
    _load_resolved_config,
    _pairs_from_sorted_bins,
    _parse_point,
    _read_ttbin_timetags,
)


def file_fingerprint(path: Path) -> dict[str, Any]:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    st = path.stat()
    return {
        "path": str(path),
        "size": int(st.st_size),
        "mtime": float(st.st_mtime),
        "sha256": h.hexdigest(),
    }


def _to_int(v: Any, default: int | None = None) -> int | None:
    try:
        return int(round(float(v)))
    except Exception:
        return default


def _resolve_materialize_max_pairs(d: int, requested: int | None) -> int:
    """
    Resolve sequence extraction cap.
    Return 0 to mean "uncapped/use all available pairs".
    This removes legacy hard caps for high-dimensional points.
    """
    try:
        req = int(round(float(requested))) if requested is not None else 0
    except Exception:
        req = 0
    if req <= 0:
        return 0
    if int(d) >= 1024 and req <= 256:
        return 0
    return max(0, int(req))


def _find_point_dir_from_master(master_csv: Path, d: int, bw: int) -> Path | None:
    if not master_csv.exists():
        return None
    try:
        df = pd.read_csv(master_csv)
    except Exception:
        return None
    hit = df[
        (pd.to_numeric(df.get("dimension"), errors="coerce") == float(d))
        & (pd.to_numeric(df.get("bin_width_ps"), errors="coerce") == float(bw))
    ]
    if hit.empty:
        return None
    row = dict(hit.iloc[-1])
    for key in ("point_dir", "source_point_dir"):
        p = str(row.get(key) or "").strip()
        if p:
            pp = Path(p)
            if pp.exists():
                return pp
    return None


def _fallback_find_point_dir(d: int, bw: int) -> Path | None:
    cands = sorted((REPO_ROOT / "results").glob(f"**/d{d}_bw{bw}"))
    for p in cands:
        if (p / "point_summary.json").exists():
            return p
    return cands[-1] if cands else None


def _find_symbol_arrays_in_point_dir(point_dir: Path) -> tuple[np.ndarray, np.ndarray, str] | None:
    names = {
        "a_eff.npy": "b_eff.npy",
        "a_symbols.npy": "b_symbols.npy",
        "symbols_a.npy": "symbols_b.npy",
        "alice_symbols.npy": "bob_symbols.npy",
    }
    for a_name, b_name in names.items():
        ap = point_dir / a_name
        bp = point_dir / b_name
        if ap.exists() and bp.exists():
            return np.load(ap), np.load(bp), f"{ap}|{bp}"
    return None


def _find_symbol_arrays_in_metrics(metrics_path: Path) -> tuple[np.ndarray, np.ndarray, str] | None:
    try:
        j = json.loads(metrics_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    framed = j.get("framed") if isinstance(j, dict) else None
    if not isinstance(framed, dict):
        return None
    for ak, bk in (
        ("a_eff", "b_eff"),
        ("a_symbols", "b_symbols"),
        ("symbols_a", "symbols_b"),
        ("alice_symbols", "bob_symbols"),
    ):
        va = framed.get(ak)
        vb = framed.get(bk)
        if isinstance(va, list) and isinstance(vb, list) and len(va) == len(vb) and len(va) > 0:
            return np.asarray(va), np.asarray(vb), f"{metrics_path}#framed.{ak}/framed.{bk}"
    return None


def resolve_point_sources(point: str, *, merged_master: str | Path | None = None) -> dict[str, Any]:
    d, bw = _parse_point(point)
    mm = (
        Path(merged_master)
        if merged_master is not None
        else REPO_ROOT / "results" / "fullgrid_20260220_1313" / "updated_merged_grid_master.csv"
    )
    point_dir = _find_point_dir_from_master(mm, d, bw)
    if point_dir is None:
        point_dir = _fallback_find_point_dir(d, bw)
    if point_dir is None:
        raise FileNotFoundError(f"cannot locate point dir for ({d},{bw})")
    arts = _load_artifacts(d, bw, mm)
    cfg = _load_resolved_config(arts)
    # Optional runtime overrides for fast dataset switching without editing all point configs.
    ttbin_override = str(os.getenv("HDQKD_TTBIN_FILE_OVERRIDE") or "").strip()
    ch_a_override = str(os.getenv("HDQKD_TTBIN_CH_A_OVERRIDE") or "").strip()
    ch_b_override = str(os.getenv("HDQKD_TTBIN_CH_B_OVERRIDE") or "").strip()
    if ttbin_override or ch_a_override or ch_b_override:
        ttbin_cfg = cfg.get("ttbin") if isinstance(cfg.get("ttbin"), dict) else {}
        if ttbin_override:
            ttbin_cfg["file"] = ttbin_override
        if ch_a_override or ch_b_override:
            ch = ttbin_cfg.get("channels") if isinstance(ttbin_cfg.get("channels"), dict) else {}
            if ch_a_override:
                try:
                    ch["A"] = int(ch_a_override)
                except Exception:
                    pass
            if ch_b_override:
                try:
                    ch["B"] = int(ch_b_override)
                except Exception:
                    pass
            ttbin_cfg["channels"] = ch
        cfg["ttbin"] = ttbin_cfg
    metrics_path = arts.get("metrics")
    if metrics_path is None or (not metrics_path.exists()):
        raise FileNotFoundError("ttbin_metrics.json not found")
    return {
        "d": int(d),
        "bw": int(bw),
        "point_dir": point_dir,
        "metrics_path": Path(metrics_path),
        "resolved_config": cfg,
    }


def _load_array_from_path(path: Path, preferred_key: str) -> np.ndarray:
    suf = path.suffix.lower()
    if suf == ".npy":
        arr = np.load(path)
        return np.asarray(arr, dtype=np.int64).reshape(-1)
    if suf == ".npz":
        z = np.load(path)
        if preferred_key in z:
            return np.asarray(z[preferred_key], dtype=np.int64).reshape(-1)
        if len(z.files) > 0:
            return np.asarray(z[z.files[0]], dtype=np.int64).reshape(-1)
        raise RuntimeError(f"empty npz: {path}")
    if suf == ".csv":
        df = pd.read_csv(path)
        if preferred_key in df.columns:
            return np.asarray(df[preferred_key].to_numpy(), dtype=np.int64).reshape(-1)
        if len(df.columns) > 0:
            return np.asarray(df.iloc[:, 0].to_numpy(), dtype=np.int64).reshape(-1)
        raise RuntimeError(f"empty csv: {path}")
    raise RuntimeError(f"unsupported sequence file type: {path}")


def _choose_pair(cands_a: list[Path], cands_b: list[Path], block_tokens: list[str]) -> tuple[Path, Path] | None:
    if not cands_a or not cands_b:
        return None
    best: tuple[int, int, int, str, str] | None = None
    for pa in cands_a:
        for pb in cands_b:
            same_parent = 0 if pa.parent == pb.parent else 1
            block_hit = 0
            pstr = (str(pa).lower() + " " + str(pb).lower())
            if block_tokens:
                block_hit = 0 if any(t in pstr for t in block_tokens) else 1
            dist = abs(len(str(pa)) - len(str(pb)))
            key = (same_parent, block_hit, dist, str(pa), str(pb))
            if best is None or key < best:
                best = key
    if best is None:
        return None
    return Path(best[3]), Path(best[4])


def resolve_real_sequence_artifacts(d: int, bw: int, block_index: int, search_root: str) -> dict:
    root = Path(search_root)
    tried_globs = [
        "**/*a_eff*.npy",
        "**/*b_eff*.npy",
        "**/*a_eff*.npz",
        "**/*b_eff*.npz",
        "**/*a_eff*.csv",
        "**/*b_eff*.csv",
        "**/*a_symbols*.npy",
        "**/*b_symbols*.npy",
        "**/*a_symbols*.npz",
        "**/*b_symbols*.npz",
        "**/*a_symbols*.csv",
        "**/*b_symbols*.csv",
        "**/*symbols_a*.npy",
        "**/*symbols_b*.npy",
        "**/*symbols_a*.npz",
        "**/*symbols_b*.npz",
        "**/*symbols_a*.csv",
        "**/*symbols_b*.csv",
        "**/*sequence*a*.npy",
        "**/*sequence*b*.npy",
    ]
    found: dict[str, list[str]] = {"a_eff": [], "b_eff": [], "a_symbols": [], "b_symbols": []}
    if not root.exists():
        return {
            "ok": False,
            "a_eff_path": None,
            "b_eff_path": None,
            "a_symbols_path": None,
            "b_symbols_path": None,
            "chosen_kind": None,
            "tried_globs": tried_globs,
            "found_candidates": found,
        }

    d_tokens = [f"d{d}", f"dimension{d}"]
    bw_tokens = [f"bw{bw}", f"binwidth{bw}", f"bin_width_{bw}", f"bin_width{bw}"]
    block_tokens = [f"blk{block_index}", f"block{block_index}", f"block_{block_index}"]

    def _is_sidecar_artifact(p: Path) -> bool:
        s = str(p).lower().replace("\\", "/")
        if "/sidecars/" in s:
            return True
        if "joint_seq_sidecar_" in s:
            return True
        if "nbldpc_demo_sidecar_run" in s:
            return True
        # Any directory containing sidecar_meta.json is considered derived sidecar data.
        for anc in [p.parent, *p.parents]:
            if (anc / "sidecar_meta.json").exists():
                return True
        return False

    def _match_context(p: Path) -> bool:
        s = str(p).lower()
        if _is_sidecar_artifact(p):
            return False
        d_ok = any(t in s for t in d_tokens)
        bw_ok = any(t in s for t in bw_tokens)
        return bool(d_ok and bw_ok)

    for pat in tried_globs:
        for p in root.glob(pat):
            if not p.is_file():
                continue
            if not _match_context(p):
                continue
            low = p.name.lower()
            if "a_eff" in low:
                found["a_eff"].append(str(p))
            elif "b_eff" in low:
                found["b_eff"].append(str(p))
            elif "a_symbols" in low or "symbols_a" in low:
                found["a_symbols"].append(str(p))
            elif "b_symbols" in low or "symbols_b" in low:
                found["b_symbols"].append(str(p))

    # Dedup and stable sort
    for k in list(found.keys()):
        found[k] = sorted(set(found[k]))

    pair_eff = _choose_pair([Path(x) for x in found["a_eff"]], [Path(x) for x in found["b_eff"]], block_tokens)
    if pair_eff is not None:
        return {
            "ok": True,
            "a_eff_path": str(pair_eff[0]),
            "b_eff_path": str(pair_eff[1]),
            "a_symbols_path": None,
            "b_symbols_path": None,
            "chosen_kind": "eff_pair",
            "tried_globs": tried_globs,
            "found_candidates": found,
        }

    pair_sym = _choose_pair([Path(x) for x in found["a_symbols"]], [Path(x) for x in found["b_symbols"]], block_tokens)
    if pair_sym is not None:
        return {
            "ok": True,
            "a_eff_path": None,
            "b_eff_path": None,
            "a_symbols_path": str(pair_sym[0]),
            "b_symbols_path": str(pair_sym[1]),
            "chosen_kind": "symbols_pair",
            "tried_globs": tried_globs,
            "found_candidates": found,
        }

    return {
        "ok": False,
        "a_eff_path": None,
        "b_eff_path": None,
        "a_symbols_path": None,
        "b_symbols_path": None,
        "chosen_kind": None,
        "tried_globs": tried_globs,
        "found_candidates": found,
    }


def _sample_sequences_from_joint_sparse(
    joint_sparse_eff: list[dict[str, Any]],
    *,
    n_symbols: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    rows: list[tuple[int, int, float]] = []
    for e in joint_sparse_eff:
        try:
            i = int(e.get("i"))
            j = int(e.get("j"))
            c = float(e.get("count"))
        except Exception:
            continue
        if i < 0 or j < 0 or (not math.isfinite(c)) or c <= 0.0:
            continue
        rows.append((i, j, c))
    if not rows:
        raise RuntimeError("cannot sample from empty joint sparse")
    probs = np.asarray([r[2] for r in rows], dtype=np.float64)
    probs = probs / float(np.sum(probs))
    rng = np.random.default_rng(int(seed))
    idx = rng.choice(len(rows), size=int(n_symbols), replace=True, p=probs)
    a_eff = np.asarray([rows[int(k)][0] for k in idx], dtype=np.int64)
    b_eff = np.asarray([rows[int(k)][1] for k in idx], dtype=np.int64)
    return a_eff, b_eff


def _build_chan_ll_table(joint_sparse_eff: list[dict[str, Any]], q: int, eps: float = 1e-300) -> np.ndarray:
    j = dense_from_sparse(joint_sparse_eff, q)
    pb = np.sum(j, axis=0)
    p_agb = np.zeros((q, q), dtype=np.float64)
    for b in range(q):
        if pb[b] > 0.0:
            p_agb[:, b] = j[:, b] / float(pb[b])
        else:
            p_agb[:, b] = 1.0 / float(q)
    out = np.log(p_agb.T + float(eps))
    out = out - np.max(out, axis=1, keepdims=True)
    return np.asarray(out, dtype=np.float64)


def _bits_natural(sym: np.ndarray, m: int) -> np.ndarray:
    x = np.asarray(sym, dtype=np.uint64).reshape(-1)
    out = np.zeros((x.size, m), dtype=np.uint8)
    for k in range(m):
        shift = m - 1 - k
        out[:, k] = ((x >> shift) & 1).astype(np.uint8)
    return out


def _map_sanity(
    chan_ll_table: np.ndarray,
    a_eff: np.ndarray,
    b_eff: np.ndarray,
    q: int,
    *,
    chunk_size: int = 50_000,
) -> tuple[float, float]:
    a = np.asarray(a_eff, dtype=np.int64).reshape(-1)
    b = np.asarray(b_eff, dtype=np.int64).reshape(-1)
    n = min(int(a.size), int(b.size))
    if n <= 0:
        return float("nan"), float("nan")
    aa = np.clip(a[:n], 0, q - 1)
    bb = np.clip(b[:n], 0, q - 1)
    # Avoid building a huge (n_symbols, q) matrix for high-d points.
    # Prediction depends only on Bob symbol b: pred = argmax_a log P(a|b).
    pred_lut = np.argmax(np.asarray(chan_ll_table, dtype=np.float64), axis=1).astype(np.int64, copy=False)
    pred = pred_lut[bb]
    ser = float(np.mean(pred != aa))
    m = int(round(math.log2(float(q))))
    if m <= 0:
        return ser, float("nan")
    step = max(1, int(chunk_size))
    bit_err = 0
    for s in range(0, n, step):
        e = min(n, s + step)
        p_bits = _bits_natural(pred[s:e], m)
        a_bits = _bits_natural(aa[s:e], m)
        bit_err += int(np.count_nonzero(p_bits != a_bits))
    ber = float(bit_err) / float(n * m)
    return ser, ber


def compute_delta_hist(a_eff: np.ndarray, b_eff: np.ndarray, d: int, topk: int = 21) -> dict:
    q = int(d)
    a = np.asarray(a_eff, dtype=np.int64).reshape(-1)
    b = np.asarray(b_eff, dtype=np.int64).reshape(-1)
    n = min(int(a.size), int(b.size))
    if q <= 0 or n <= 0:
        return {
            "topk_rows": [],
            "delta_mode": None,
            "delta_mode_frac": float("nan"),
            "near_neighbor_frac": float("nan"),
            "raw_ser": float("nan"),
            "n_pairs": int(max(0, n)),
        }
    aa = np.clip(a[:n], 0, q - 1)
    bb = np.clip(b[:n], 0, q - 1)
    delta = (bb - aa) % q
    hist = np.bincount(delta, minlength=q).astype(np.int64, copy=False)
    order = np.argsort(-hist)
    rows: list[dict[str, Any]] = []
    tk = max(1, int(topk))
    for rank, idx in enumerate(order[:tk], start=1):
        c = int(hist[int(idx)])
        rows.append(
            {
                "rank": int(rank),
                "delta": int(idx),
                "count": int(c),
                "frac": float(c / n),
            }
        )
    d_mode = int(order[0]) if order.size > 0 else None
    d_mode_frac = float(hist[d_mode] / n) if d_mode is not None else float("nan")
    nn_idx = {0, 1, 2, (q - 1) % q, (q - 2) % q}
    nn_sum = int(sum(int(hist[k]) for k in nn_idx))
    raw_ser = float(np.mean(aa != bb))
    ah = np.bincount(aa, minlength=q).astype(np.int64, copy=False)
    bh = np.bincount(bb, minlength=q).astype(np.int64, copy=False)
    n_unique_a = int(np.count_nonzero(ah))
    n_unique_b = int(np.count_nonzero(bh))
    top_a_frac = float(np.max(ah) / n) if n > 0 and ah.size > 0 else float("nan")
    top_b_frac = float(np.max(bh) / n) if n > 0 and bh.size > 0 else float("nan")
    return {
        "topk_rows": rows,
        "delta_mode": d_mode,
        "delta_mode_frac": d_mode_frac,
        "near_neighbor_frac": float(nn_sum / n),
        "raw_ser": raw_ser,
        "n_pairs": int(n),
        "n_pairs_actual": int(n),
        "n_unique_a": n_unique_a,
        "n_unique_b": n_unique_b,
        "top_a_frac": top_a_frac,
        "top_b_frac": top_b_frac,
    }


def write_materialize_diagnostics(sidecar_root: str, diag: dict) -> dict:
    root = Path(sidecar_root)
    root.mkdir(parents=True, exist_ok=True)
    delta_csv = root / "delta_hist.csv"
    stats_json = root / "seq_pair_stats.json"
    rows = list(diag.get("topk_rows") or [])
    with delta_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["rank", "delta", "count", "frac"])
        w.writeheader()
        for r in rows:
            w.writerow(
                {
                    "rank": int(r.get("rank", 0)),
                    "delta": int(r.get("delta", 0)),
                    "count": int(r.get("count", 0)),
                    "frac": float(r.get("frac", 0.0)),
                }
            )
    stats = {
        "n_pairs": int(diag.get("n_pairs", 0)),
        "n_pairs_actual": int(diag.get("n_pairs_actual", diag.get("n_pairs", 0))),
        "raw_ser": float(diag.get("raw_ser", float("nan"))),
        "delta_mode": int(diag.get("delta_mode")) if diag.get("delta_mode") is not None else None,
        "delta_mode_frac": float(diag.get("delta_mode_frac", float("nan"))),
        "near_neighbor_frac": float(diag.get("near_neighbor_frac", float("nan"))),
        "n_unique_a": int(diag.get("n_unique_a", 0)),
        "n_unique_b": int(diag.get("n_unique_b", 0)),
        "top_a_frac": float(diag.get("top_a_frac", float("nan"))),
        "top_b_frac": float(diag.get("top_b_frac", float("nan"))),
        "d": int(diag.get("d", 0)),
        "note": "delta=(b_eff-a_eff) mod d",
    }
    stats_json.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"delta_hist_path": str(delta_csv), "seq_pair_stats_path": str(stats_json)}


def build_joint_counts_sparse_from_sequences(a_eff: np.ndarray, b_eff: np.ndarray, d: int) -> list[dict[str, float]]:
    q = int(d)
    if q <= 0:
        raise ValueError("d must be >0")
    a = np.asarray(a_eff, dtype=np.int64).reshape(-1)
    b = np.asarray(b_eff, dtype=np.int64).reshape(-1)
    n = min(int(a.size), int(b.size))
    if n <= 0:
        return []
    aa = a[:n]
    bb = b[:n]
    m = (aa >= 0) & (aa < q) & (bb >= 0) & (bb < q)
    if not np.any(m):
        return []
    aa = aa[m]
    bb = bb[m]
    flat = aa * int(q) + bb
    cnt = np.bincount(flat, minlength=int(q) * int(q)).astype(np.int64, copy=False)
    nz = np.nonzero(cnt > 0)[0]
    out: list[dict[str, float]] = []
    for idx in nz:
        i = int(idx // q)
        j = int(idx % q)
        c = int(cnt[idx])
        out.append({"i": i, "j": j, "count": float(c)})
    out.sort(key=lambda x: (int(x["i"]), int(x["j"])))
    return out


def _estimate_peak_stats_from_timetags(
    t0_ps: np.ndarray,
    t1_ps: np.ndarray,
    *,
    scan_range_ps: int = 50_000,
    bin_ps: int = 10,
    frame_period_ps: int | None = None,
    max_hist_bins: int = 400_001,
    debug: bool = False,
) -> dict[str, Any]:
    t0 = np.asarray(t0_ps, dtype=np.int64).reshape(-1)
    t1 = np.asarray(t1_ps, dtype=np.int64).reshape(-1)
    out: dict[str, Any] = {
        "peak_center_ps": 0,
        "peak_sigma_ps": None,
        "peak_to_bg": None,
        "corr_bins": 0,
        "corr_max": 0.0,
        "corr_argmax": None,
        "corr_nonzero": 0,
        "scan_range_ps_used": 0,
        "bin_ps_used": 0,
        "sampled_t0": 0,
        "sampled_t1": int(t1.size),
        "status": "empty_input",
    }
    if t0.size == 0 or t1.size == 0:
        if debug:
            print(
                f"[ALIGN][peak_est] status=empty_input n0={int(t0.size)} n1={int(t1.size)}",
                file=sys.__stdout__,
            )
        return out

    # Sampling controls CPU cost while keeping dense temporal coverage.
    max_n = min(int(t0.size), 300_000)
    if t0.size > max_n:
        idx = np.linspace(0, t0.size - 1, num=max_n, dtype=np.int64)
        a = t0[idx]
    else:
        a = t0
    out["sampled_t0"] = int(a.size)
    out["sampled_t1"] = int(t1.size)

    i = np.searchsorted(t1, a, side="left")
    i0 = np.clip(i - 1, 0, max(0, t1.size - 1))
    i1 = np.clip(i, 0, max(0, t1.size - 1))
    dt0 = t1[i0] - a
    dt1 = t1[i1] - a
    dt = np.where(np.abs(dt1) <= np.abs(dt0), dt1, dt0)

    # Dynamic scan window:
    # - keeps legacy behavior floor (50 ns),
    # - expands with frame period for high-d points,
    # - upper bounded to avoid pathological allocations.
    rg_req = int(max(1, abs(scan_range_ps)))
    if frame_period_ps is not None:
        try:
            fpp = int(max(1, abs(int(frame_period_ps))))
        except Exception:
            fpp = 0
        if fpp > 0:
            rg_req = max(rg_req, int(min(max(4 * fpp, 50_000), 20_000_000)))
    rg = int(max(1, rg_req))
    dt = dt[(dt >= -rg) & (dt <= rg)]
    if dt.size == 0:
        out["scan_range_ps_used"] = int(rg)
        out["status"] = "empty_after_range_filter"
        if debug:
            print(
                f"[ALIGN][peak_est] status=empty_after_range_filter n0={int(t0.size)} n1={int(t1.size)} "
                f"sampled={int(a.size)} rg={int(rg)}",
                file=sys.__stdout__,
            )
        return out

    bp = int(max(1, bin_ps))
    # Keep histogram length bounded to prevent memory spikes.
    target_bins = int(max(1024, max_hist_bins))
    needed_bins = int(math.ceil((2.0 * float(rg)) / float(bp)))
    if needed_bins > target_bins:
        bp = int(max(bp, math.ceil((2.0 * float(rg)) / float(target_bins))))
    edges = np.arange(-rg, rg + bp, bp, dtype=np.int64)
    if edges.size < 2:
        edges = np.asarray([-rg, rg], dtype=np.int64)
    cnt, e = np.histogram(dt, bins=edges)
    out["corr_bins"] = int(cnt.size)
    out["corr_nonzero"] = int(np.count_nonzero(cnt))
    out["scan_range_ps_used"] = int(rg)
    out["bin_ps_used"] = int(bp)
    if cnt.size == 0:
        out["status"] = "empty_hist"
        if debug:
            print(
                f"[ALIGN][peak_est] status=empty_hist sampled={int(a.size)} rg={int(rg)} bp={int(bp)}",
                file=sys.__stdout__,
            )
        return out

    pk = int(np.argmax(cnt))
    peak_h = float(cnt[pk])
    peak_center = int((e[pk] + e[pk + 1]) // 2)
    out["corr_max"] = float(peak_h)
    out["corr_argmax"] = int(pk)
    out["peak_center_ps"] = int(peak_center)

    mask_bg = np.ones(cnt.shape[0], dtype=bool)
    lo = max(0, pk - 2)
    hi = min(cnt.shape[0], pk + 3)
    mask_bg[lo:hi] = False
    bg = float(np.median(cnt[mask_bg])) if np.any(mask_bg) else float(np.median(cnt))
    p2bg = float(peak_h / max(bg, 1e-9))
    out["peak_to_bg"] = float(p2bg)

    # Crude local sigma around peak.
    lag_centers = ((e[:-1] + e[1:]) // 2).astype(np.float64)
    local = slice(max(0, pk - 12), min(cnt.shape[0], pk + 13))
    c_local = cnt[local].astype(np.float64)
    l_local = lag_centers[local]
    w = np.maximum(c_local - bg, 0.0)
    if np.sum(w) > 0:
        mu = float(np.sum(w * l_local) / np.sum(w))
        var = float(np.sum(w * (l_local - mu) ** 2) / np.sum(w))
        out["peak_sigma_ps"] = float(math.sqrt(max(var, 0.0)))
    else:
        out["peak_sigma_ps"] = None
    out["status"] = "ok"

    if debug:
        print(
            f"[ALIGN][peak_est] status=ok n0={int(t0.size)} n1={int(t1.size)} sampled={int(a.size)} "
            f"rg={int(rg)} bp={int(bp)} bins={int(cnt.size)} nz={int(np.count_nonzero(cnt))} "
            f"peak_idx={int(pk)} peak_h={float(peak_h):.3f} peak_center_ps={int(peak_center)} "
            f"peak_to_bg={float(p2bg):.6g}",
            file=sys.__stdout__,
        )
    return out


def _pair_timetags_with_delay_window(
    t0_ps: np.ndarray,
    t1_ps: np.ndarray,
    *,
    delay_ps: int,
    window_ps: int,
    mode: str,
    max_pairs: int,
    frame_period_ps: int | None = None,
) -> np.ndarray:
    def _pair_nearest_vectorized(
        t0_arr: np.ndarray,
        t1_arr: np.ndarray,
        *,
        delay: int,
        max_dist_ps: int,
        max_take: int,
        frame_ps: int | None,
    ) -> np.ndarray:
        if t0_arr.size == 0 or t1_arr.size == 0:
            return np.zeros((0, 2), dtype=np.int64)

        # Absolute-time nearest search:
        # find insertion index for target = tA + delay in sorted Bob timestamps.
        target = t0_arr + np.int64(delay)
        idx = np.searchsorted(t1_arr, target, side="left")
        left = np.clip(idx - 1, 0, max(0, t1_arr.size - 1))
        right = np.clip(idx, 0, max(0, t1_arr.size - 1))

        d_left = np.abs(t1_arr[left] - target)
        d_right = np.abs(t1_arr[right] - target)
        inf = np.int64(np.iinfo(np.int64).max // 4)
        d_left = np.where(idx <= 0, inf, d_left)
        d_right = np.where(idx >= t1_arr.size, inf, d_right)

        use_right = d_right <= d_left
        best_idx = np.where(use_right, right, left).astype(np.int64, copy=False)
        best_dist = np.where(use_right, d_right, d_left).astype(np.int64, copy=False)

        if frame_ps is not None:
            try:
                half_frame = int(max(1, abs(int(frame_ps)) // 2))
            except Exception:
                half_frame = 0
            if half_frame > 0:
                max_dist_ps = min(int(max_dist_ps), int(half_frame))

        keep = best_dist <= np.int64(max(1, int(max_dist_ps)))
        if not np.any(keep):
            return np.zeros((0, 2), dtype=np.int64)

        a_idx = np.flatnonzero(keep).astype(np.int64, copy=False)
        if int(max_take) > 0 and a_idx.size > int(max_take):
            a_idx = a_idx[: int(max_take)]
        b_idx = best_idx[a_idx]
        return np.column_stack((t0_arr[a_idx], t1_arr[b_idx])).astype(np.int64, copy=False)

    t0 = np.asarray(t0_ps, dtype=np.int64).reshape(-1)
    t1 = np.asarray(t1_ps, dtype=np.int64).reshape(-1)
    if t0.size == 0 or t1.size == 0:
        return np.zeros((0, 2), dtype=np.int64)
    mode_l = str(mode).strip().lower()

    w = int(max(1, abs(window_ps)))
    n_take = int(max_pairs)
    if mode_l in {"nearest", "peak_gated"}:
        return _pair_nearest_vectorized(
            t0,
            t1,
            delay=int(delay_ps),
            max_dist_ps=int(w),
            max_take=int(n_take if n_take > 0 else max(1, int(t0.size))),
            frame_ps=frame_period_ps,
        )

    t1_adj = t1 - int(delay_ps)
    idx = np.searchsorted(t1_adj, t0, side="left")
    idx0 = np.clip(idx - 1, 0, max(0, t1_adj.size - 1))
    idx1 = np.clip(idx, 0, max(0, t1_adj.size - 1))
    d0 = t1_adj[idx0] - t0
    d1 = t1_adj[idx1] - t0
    big = np.int64(10**15)
    d0 = np.where(idx <= 0, big, d0)
    d1 = np.where(idx >= t1_adj.size, big, d1)
    if mode_l == "greedy":
        pick_idx = idx1
        pick_dt = d1
    elif mode_l == "two_pointer":
        pick0 = np.abs(d0) < np.abs(d1)
        pick_idx = np.where(pick0, idx0, idx1)
        pick_dt = np.where(pick0, d0, d1)
    else:
        pick_idx = idx1
        pick_dt = d1
    keep = np.abs(pick_dt) <= w
    a_idx = np.nonzero(keep)[0].astype(np.int64)
    b_idx = pick_idx[keep].astype(np.int64)
    if n_take > 0 and a_idx.size > n_take:
        a_idx = a_idx[:n_take]
        b_idx = b_idx[:n_take]
    return np.column_stack((t0[a_idx], t1[b_idx])).astype(np.int64, copy=False) if a_idx.size > 0 else np.zeros((0, 2), dtype=np.int64)


def _paths_match_block(paths: list[str], block_index: int) -> bool:
    toks = [f"blk{block_index}", f"block{block_index}", f"block_{block_index}"]
    s = " ".join(str(x).lower() for x in paths if str(x))
    return any(t in s for t in toks)


def materialize_real_sequences_for_point(
    point,
    factor: int,
    block_index: int,
    out_dir: str,
    *,
    offset_override_ps: int | None = None,
    max_pairs: int | None = None,
    frame_start_override_ps: int | None = None,
    coinc_window_override_ps: int | None = None,
    pairing_mode: str = "nearest",
    peak_gate_sigma: float | None = None,
    delay_override_ps: int | None = None,
    shared_t0_ps: np.ndarray | None = None,
    shared_t1_ps: np.ndarray | None = None,
    global_peak_center_ps: int | None = None,
) -> dict:
    outp = Path(out_dir)
    outp.mkdir(parents=True, exist_ok=True)
    try:
        point_s = str(point)
        ctx = resolve_point_sources(point_s)
        d = int(ctx["d"])
        bw = int(ctx["bw"])
        cfg: dict[str, Any] = ctx["resolved_config"]
        ttbin_cfg = cfg.get("ttbin") if isinstance(cfg.get("ttbin"), dict) else {}
        ttbin_path_raw = str(ttbin_cfg.get("file") or "").strip()
        if not ttbin_path_raw:
            raise ValueError("ttbin.file missing in resolved config")
        ttbin_path = Path(ttbin_path_raw)
        if not ttbin_path.exists():
            raise FileNotFoundError(f"ttbin file not found: {ttbin_path}")

        ch_ids = ttbin_cfg.get("channels")
        raw_ch0 = 1
        raw_ch1 = 2
        if isinstance(ch_ids, dict):
            a_id = ch_ids.get("A")
            b_id = ch_ids.get("B")
            if a_id is not None:
                raw_ch0 = int(a_id)
            if b_id is not None:
                raw_ch1 = int(b_id)
        elif isinstance(ch_ids, (list, tuple)) and len(ch_ids) >= 2:
            raw_ch0 = int(ch_ids[0])
            raw_ch1 = int(ch_ids[1])

        n_take_req = _resolve_materialize_max_pairs(d=int(d), requested=max_pairs)
        # Interpret frame_start override as a deterministic stream slice shift in pair units.
        start_shift_pairs = 0
        if frame_start_override_ps is not None:
            try:
                start_shift_pairs = int(round(float(frame_start_override_ps) / float(max(1, bw))))
            except Exception:
                start_shift_pairs = 0

        if shared_t0_ps is not None and shared_t1_ps is not None:
            t0 = np.asarray(shared_t0_ps, dtype=np.int64).reshape(-1)
            t1 = np.asarray(shared_t1_ps, dtype=np.int64).reshape(-1)
            if t0.size > 1 and np.any(t0[1:] < t0[:-1]):
                t0 = np.sort(t0)
            if t1.size > 1 and np.any(t1[1:] < t1[:-1]):
                t1 = np.sort(t1)
        else:
            tt = _read_ttbin_timetags(ttbin_path, raw_ch0_id=raw_ch0, raw_ch1_id=raw_ch1)
            ch = np.asarray(tt.Ch, dtype=np.int64)
            ts = np.asarray(tt.TimeTag, dtype=np.int64)
            t0 = np.sort(ts[ch == 0])
            t1 = np.sort(ts[ch == 1])
        pairing_mode_req = str(pairing_mode).strip().lower() or "nearest"
        pairing_mode_l = str(pairing_mode_req)
        align_debug = os.getenv("HDQKD_ALIGN_DEBUG", "0") == "1"
        nearest_threshold_ps = max(1, _to_int(os.getenv("HDQKD_NEAREST_FRAME_THRESHOLD_PS", "40000"), 40_000) or 40_000)
        frame_period_ps = int(max(1, int(d)) * max(1, int(bw)))
        auto_force_nearest = bool(frame_period_ps >= int(nearest_threshold_ps))
        pairing_mode_auto_forced = False
        if auto_force_nearest and pairing_mode_l != "nearest":
            pairing_mode_l = "nearest"
            pairing_mode_auto_forced = True
        used_delay_ps = int(delay_override_ps) if delay_override_ps is not None else _to_int(ttbin_cfg.get("delay_ps"), _to_int(ttbin_cfg.get("offset_ps"), 0)) or 0
        peak_center_ps = _to_int(global_peak_center_ps, 0) or 0
        peak_sigma_ps = None
        peak_to_bg = None
        corr_bins = 0
        corr_max = 0.0
        corr_argmax = None
        corr_nonzero = 0
        peak_scan_range_ps = 0
        peak_bin_ps = 0
        peak_status = "not_requested"
        auto_peak_delay_for_nearest = bool(pairing_mode_l == "nearest" and auto_force_nearest and delay_override_ps is None)
        need_peak_stats = (
            (pairing_mode_l == "peak_gated" and (delay_override_ps is None or peak_gate_sigma is not None))
            or auto_peak_delay_for_nearest
            or align_debug
        ) and (global_peak_center_ps is None)
        if need_peak_stats:
            peak_info = _estimate_peak_stats_from_timetags(
                t0,
                t1,
                scan_range_ps=max(50_000, 2 * frame_period_ps),
                bin_ps=max(10, int(max(1, bw // 2))),
                frame_period_ps=frame_period_ps,
                max_hist_bins=400_001,
                debug=bool(align_debug),
            )
            peak_center_ps = _to_int(peak_info.get("peak_center_ps"), 0)
            peak_sigma_ps = peak_info.get("peak_sigma_ps")
            peak_to_bg = peak_info.get("peak_to_bg")
            corr_bins = _to_int(peak_info.get("corr_bins"), 0) or 0
            corr_max = float(peak_info.get("corr_max") or 0.0)
            corr_argmax = _to_int(peak_info.get("corr_argmax"), None)
            corr_nonzero = _to_int(peak_info.get("corr_nonzero"), 0) or 0
            peak_scan_range_ps = _to_int(peak_info.get("scan_range_ps_used"), 0) or 0
            peak_bin_ps = _to_int(peak_info.get("bin_ps_used"), 0) or 0
            peak_status = str(peak_info.get("status") or "unknown")
            if auto_peak_delay_for_nearest and peak_status == "ok":
                used_delay_ps = int(peak_center_ps)
        elif auto_peak_delay_for_nearest and global_peak_center_ps is not None:
            used_delay_ps = int(peak_center_ps)
            peak_status = "from_global_peak"
        gate_width_ps = None
        gate_width_fallback = False

        if pairing_mode_l == "peak_gated":
            if delay_override_ps is None:
                used_delay_ps = int(peak_center_ps)
            if peak_gate_sigma is not None and peak_sigma_ps is not None and math.isfinite(float(peak_sigma_ps)):
                gate_width_ps = int(max(1, round(float(peak_gate_sigma) * float(peak_sigma_ps))))
            else:
                gate_width_ps = int(max(1, _to_int(coinc_window_override_ps, _to_int(ttbin_cfg.get("coincidence_window_ps"), int(bw))) or int(bw)))
                gate_width_fallback = True
            time_pairs = _pair_timetags_with_delay_window(
                t0,
                t1,
                delay_ps=int(used_delay_ps),
                window_ps=int(gate_width_ps),
                mode="peak_gated",
                max_pairs=(
                    int((int(block_index) + 1 + max(0, int(start_shift_pairs))) * int(n_take_req))
                    if int(n_take_req) > 0
                    else 0
                ),
                frame_period_ps=int(frame_period_ps),
            )
            if time_pairs.size == 0:
                raise RuntimeError("no coincidence pairs generated (peak_gated)")
            a_bin = np.floor_divide(time_pairs[:, 0], int(max(1, bw)))
            b_bin = np.floor_divide((time_pairs[:, 1] - int(used_delay_ps)), int(max(1, bw)))
            pairs = np.column_stack((np.mod(a_bin, int(d)), np.mod(b_bin, int(d)))).astype(np.int64, copy=False)
            pmeta = {"n_pairs": int(pairs.shape[0])}
        else:
            # Keep legacy behavior for default nearest path (no override knobs),
            # but never use it when shared timetag arrays are injected (legacy path
            # relies on `tt` object that is not populated in shared-array mode).
            shared_arrays_supplied = (shared_t0_ps is not None) and (shared_t1_ps is not None)
            use_legacy_nearest = (
                pairing_mode_l == "nearest"
                and delay_override_ps is None
                and coinc_window_override_ps is None
                and (not auto_force_nearest)
                and (not shared_arrays_supplied)
            )
            if not use_legacy_nearest and pairing_mode_l in {"nearest", "greedy", "two_pointer"}:
                gate_width_ps = int(max(1, _to_int(coinc_window_override_ps, _to_int(ttbin_cfg.get("coincidence_window_ps"), int(bw))) or int(bw)))
                time_pairs = _pair_timetags_with_delay_window(
                    t0,
                    t1,
                    delay_ps=int(used_delay_ps),
                    window_ps=int(gate_width_ps),
                    mode=pairing_mode_l,
                    max_pairs=(
                        int((int(block_index) + 1 + max(0, int(start_shift_pairs))) * int(n_take_req))
                        if int(n_take_req) > 0
                        else 0
                    ),
                    frame_period_ps=int(frame_period_ps),
                )
                if time_pairs.size == 0:
                    raise RuntimeError(f"no coincidence pairs generated ({pairing_mode_l})")
                a_bin = np.floor_divide(time_pairs[:, 0], int(max(1, bw)))
                b_bin = np.floor_divide((time_pairs[:, 1] - int(used_delay_ps)), int(max(1, bw)))
                pairs = np.column_stack((np.mod(a_bin, int(d)), np.mod(b_bin, int(d)))).astype(np.int64, copy=False)
                pmeta = {"n_pairs": int(pairs.shape[0])}
            else:
                b0, b1, _ = _bin_indices_sorted_for_binwidth(tt, bin_width_ps=int(bw))
                pairs, pmeta = _pairs_from_sorted_bins(b0_sorted=b0, b1_sorted=b1, dimension=int(d))
                if pairs.size == 0:
                    raise RuntimeError("no coincidence pairs generated")

        pairs_eff = (np.asarray(pairs, dtype=np.int64) // int(factor)).astype(np.int64, copy=False)
        n_take = int(n_take_req)
        if n_take <= 0:
            # Uncapped mode: use all available pairs for this block (block_index expected 0 in E2E path).
            n_take = int(max(1, pairs_eff.shape[0]))
        start = max(0, int(block_index) * n_take + int(start_shift_pairs))
        if start >= int(pairs_eff.shape[0]):
            raise RuntimeError(
                f"insufficient pairs after start shift, start={start}, have={pairs_eff.shape[0]}, "
                f"block_index={block_index}, max_pairs={n_take}"
            )
        end = min(start + n_take, int(pairs_eff.shape[0]))
        blk = np.asarray(pairs_eff[start:end], dtype=np.int64)
        a_eff = blk[:, 0].astype(np.int64, copy=False)
        b_eff = blk[:, 1].astype(np.int64, copy=False)

        q_eff = int(d // int(factor))
        if offset_override_ps is not None:
            shift_bins = int(round(float(offset_override_ps) / float(max(1, bw))))
            if q_eff > 0 and shift_bins != 0:
                b_eff = ((b_eff.astype(np.int64) + int(shift_bins)) % int(q_eff)).astype(np.int64)
        if a_eff.size == 0 or b_eff.size == 0:
            raise RuntimeError("empty extracted sequence")
        np.save(outp / "a_eff.npy", a_eff)
        np.save(outp / "b_eff.npy", b_eff)
        ttbin_cfg = cfg.get("ttbin") if isinstance(cfg.get("ttbin"), dict) else {}
        recon_cfg = cfg.get("reconciliation") if isinstance(cfg.get("reconciliation"), dict) else {}
        used_params = {
            "dimension": int(d),
            "bin_width_ps": int(bw),
            "max_pairs": int(n_take),
            "n_pairs_actual": int(min(a_eff.size, b_eff.size)),
            "coincidence_window_ps": ttbin_cfg.get("coincidence_window_ps"),
            "coinc_window_override_ps": coinc_window_override_ps,
            "relative_delay_ps": ttbin_cfg.get("delay_ps"),
            "delay_offset_ps": offset_override_ps,
            "delay_override_ps": delay_override_ps,
            "delay_used_ps": int(used_delay_ps),
            "frame_start_override_ps": frame_start_override_ps,
            "frame_start_ps": ttbin_cfg.get("frame_start_ps"),
            "frame_anchor": ttbin_cfg.get("frame_anchor"),
            "pairing_mode": pairing_mode_l,
            "pairing_mode_requested": pairing_mode_req,
            "pairing_mode_auto_forced": int(bool(pairing_mode_auto_forced)),
            "frame_period_ps": int(frame_period_ps),
            "nearest_threshold_ps": int(nearest_threshold_ps),
            "peak_gate_sigma": peak_gate_sigma,
            "gate_width_ps": gate_width_ps,
            "gate_width_fallback": bool(gate_width_fallback),
            "peak_center_ps": peak_center_ps,
            "peak_sigma_ps": peak_sigma_ps,
            "peak_to_bg": peak_to_bg,
            "peak_status": peak_status,
            "corr_bins": int(corr_bins),
            "corr_nonzero": int(corr_nonzero),
            "corr_argmax": corr_argmax,
            "corr_max": float(corr_max),
            "peak_scan_range_ps": int(peak_scan_range_ps),
            "peak_bin_ps": int(peak_bin_ps),
            "global_peak_center_ps": global_peak_center_ps,
            "mapping": recon_cfg.get("mapping"),
            "source_ttbin_paths": str(ttbin_cfg.get("file") or ""),
            "source_point_dir": str(ctx.get("point_dir") or ""),
            "n_pairs_total_available": int(pmeta.get("n_pairs", 0)),
            "slice_start_pair": int(start),
            "slice_end_pair": int(end),
        }
        meta = {
            "created_at": datetime.now().isoformat(),
            "origin": "materialized_from_ttbin",
            "point": {"d": d, "bw": bw},
            "factor": int(factor),
            "block_index": int(block_index),
            "n_symbols": int(min(a_eff.size, b_eff.size)),
            "resolved_ttbin": str((cfg.get("ttbin") or {}).get("file") if isinstance(cfg.get("ttbin"), dict) else ""),
            "used_params": used_params,
        }
        (outp / "materialize_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "ok": True,
            "a_eff_path": str(outp / "a_eff.npy"),
            "b_eff_path": str(outp / "b_eff.npy"),
            "a_symbols_path": None,
            "b_symbols_path": None,
            "origin": "materialized_from_ttbin",
            "error": None,
            "used_params": used_params,
        }
    except Exception as e:
        return {
            "ok": False,
            "a_eff_path": None,
            "b_eff_path": None,
            "a_symbols_path": None,
            "b_symbols_path": None,
            "origin": None,
            "error": f"{type(e).__name__}: {e}",
            "used_params": None,
        }


def export_sidecar_for_point(
    point,
    factor,
    block_index: int,
    out_root: str,
    sequence_source_mode: str = "strict",
    materialize_missing_real_seq: int = 0,
    joint_source_mode: str = "existing",
    materialize_diagnostics: int = 0,
    materialize_offset_override_ps: int | None = None,
    materialize_max_pairs: int | None = None,
    materialize_frame_start_override_ps: int | None = None,
    materialize_coinc_window_override_ps: int | None = None,
    materialize_pairing_mode: str = "nearest",
    materialize_peak_gate_sigma: float | None = None,
    materialize_delay_override_ps: int | None = None,
    materialize_shared_t0_ps: np.ndarray | None = None,
    materialize_shared_t1_ps: np.ndarray | None = None,
    materialize_global_peak_center_ps: int | None = None,
) -> dict:
    root = Path(out_root)
    root.mkdir(parents=True, exist_ok=True)
    d = 0
    bw = 0
    f = int(factor)
    q = 0
    m = 0
    n_symbols = 0
    map_ser = float("nan")
    map_ber = float("nan")
    fail_reason = ""
    sequence_is_sampled = 0
    source_sequence_path = ""
    source_joint_path = ""
    real_debug: dict[str, Any] = {}
    materialize_attempted = 0
    materialize_ok = 0
    materialize_origin = None
    materialize_out_dir = None
    materialize_error = None
    materialize_max_pairs_eff = 0
    materialize_used_params: dict[str, Any] | None = None
    joint_origin = "existing"
    joint_source_path = ""
    joint_mode_effective = "existing"
    joint_fp: dict[str, Any] = {}
    verdict = "FAIL"
    metrics_fp: dict[str, Any] = {}
    diag_payload: dict[str, Any] = {
        "enabled": int(bool(materialize_diagnostics)),
        "delta_hist_path": None,
        "seq_pair_stats_path": None,
        "n_pairs": None,
        "n_pairs_actual": None,
        "raw_ser": None,
        "delta_mode": None,
        "delta_mode_frac": None,
        "near_neighbor_frac": None,
        "n_unique_a": None,
        "n_unique_b": None,
        "top_a_frac": None,
        "top_b_frac": None,
    }

    try:
        point_s = str(point)
        ctx = resolve_point_sources(point_s)
        d = int(ctx["d"])
        bw = int(ctx["bw"])
        materialize_max_pairs_eff = _resolve_materialize_max_pairs(d=int(d), requested=materialize_max_pairs)
        point_dir: Path = ctx["point_dir"]
        metrics_path: Path = ctx["metrics_path"]
        cfg: dict[str, Any] = ctx["resolved_config"]
        source_joint_path = str(metrics_path) + "#framed.joint_counts_sparse"
        metrics_fp = file_fingerprint(metrics_path)

        if f <= 0 or d % f != 0:
            raise ValueError(f"invalid factor={f} for d={d}")
        q = int(d // f)
        m = int(round(math.log2(float(q))))
        if (1 << m) != q:
            raise ValueError(f"d_eff must be power-of-two, got {q}")

        joint_sparse = load_joint_counts_sparse_from_metrics(metrics_path)
        if not joint_sparse:
            raise RuntimeError("joint_counts_sparse is empty")
        d_eff_joint, joint_sparse_eff = coarse_grain_sparse_joint(joint_sparse, d=d, factor=f)
        if int(d_eff_joint) != q:
            raise RuntimeError(f"coarse-grain dimension mismatch: got {d_eff_joint}, expected {q}")

        mode = str(sequence_source_mode).strip().lower() or "strict"
        if mode not in {"strict", "allow_sampling"}:
            raise ValueError(f"invalid sequence_source_mode={sequence_source_mode}")
        jmode_req = str(joint_source_mode).strip().lower() or "existing"
        if jmode_req not in {"existing", "from_sequence", "from_ttbin"}:
            raise ValueError(f"invalid joint_source_mode={joint_source_mode}")
        joint_mode_effective = jmode_req

        # Prefer indexed real files first for strict publication path.
        seq_local = _find_symbol_arrays_in_point_dir(point_dir)
        seq_metrics = _find_symbol_arrays_in_metrics(metrics_path)
        real_debug = resolve_real_sequence_artifacts(d=d, bw=bw, block_index=int(block_index), search_root=str(REPO_ROOT / "results"))

        if mode == "strict" and int(materialize_missing_real_seq) == 1:
            materialize_attempted = 1
            mat_dir = REPO_ROOT / "results" / "real_sequences" / f"d{d}_bw{bw}" / f"blk{int(block_index)}"
            materialize_out_dir = str(mat_dir)
            mat = materialize_real_sequences_for_point(
                point=point_s,
                factor=f,
                block_index=int(block_index),
                out_dir=str(mat_dir),
                offset_override_ps=materialize_offset_override_ps,
                max_pairs=int(materialize_max_pairs_eff),
                frame_start_override_ps=materialize_frame_start_override_ps,
                coinc_window_override_ps=materialize_coinc_window_override_ps,
                pairing_mode=str(materialize_pairing_mode),
                peak_gate_sigma=materialize_peak_gate_sigma,
                delay_override_ps=materialize_delay_override_ps,
                shared_t0_ps=materialize_shared_t0_ps,
                shared_t1_ps=materialize_shared_t1_ps,
                global_peak_center_ps=materialize_global_peak_center_ps,
            )
            materialize_ok = 1 if bool(mat.get("ok")) else 0
            materialize_origin = mat.get("origin")
            materialize_error = mat.get("error")
            materialize_used_params = mat.get("used_params") if isinstance(mat.get("used_params"), dict) else None
            mat_a = mat_dir / "a_eff.npy"
            mat_b = mat_dir / "b_eff.npy"
            if materialize_ok and mat_a.exists() and mat_b.exists():
                # Pin to freshly materialized arrays to avoid picking stale
                # historical artifacts from broad result-directory search.
                real_debug = {
                    "ok": True,
                    "a_eff_path": str(mat_a),
                    "b_eff_path": str(mat_b),
                    "a_symbols_path": None,
                    "b_symbols_path": None,
                    "chosen_kind": "eff_pair",
                    "tried_globs": ["materialize_out_dir"],
                    "found_candidates": {
                        "a_eff": [str(mat_a)],
                        "b_eff": [str(mat_b)],
                        "a_symbols": [],
                        "b_symbols": [],
                    },
                }
            else:
                real_debug = resolve_real_sequence_artifacts(
                    d=d,
                    bw=bw,
                    block_index=int(block_index),
                    search_root=str(REPO_ROOT / "results"),
                )

        a_eff: np.ndarray
        b_eff: np.ndarray

        if bool(real_debug.get("ok")):
            chosen = str(real_debug.get("chosen_kind") or "")
            if chosen == "eff_pair":
                ap = Path(str(real_debug.get("a_eff_path")))
                bp = Path(str(real_debug.get("b_eff_path")))
                a_raw = _load_array_from_path(ap, "a_eff")
                b_raw = _load_array_from_path(bp, "b_eff")
                a_eff = np.asarray(a_raw, dtype=np.int64).astype(np.int64)
                b_eff = np.asarray(b_raw, dtype=np.int64).astype(np.int64)
                source_sequence_path = f"a_eff={ap};b_eff={bp}"
                if materialize_origin is None and "results\\real_sequences\\" in source_sequence_path.lower().replace("/", "\\"):
                    materialize_origin = "materialized_from_ttbin"
            elif chosen == "symbols_pair":
                ap = Path(str(real_debug.get("a_symbols_path")))
                bp = Path(str(real_debug.get("b_symbols_path")))
                a_raw = _load_array_from_path(ap, "a_symbols")
                b_raw = _load_array_from_path(bp, "b_symbols")
                a_eff = (np.asarray(a_raw, dtype=np.int64) // f).astype(np.int64)
                b_eff = (np.asarray(b_raw, dtype=np.int64) // f).astype(np.int64)
                source_sequence_path = f"a_symbols={ap};b_symbols={bp}"
            else:
                raise RuntimeError("real_debug ok but chosen_kind is empty")
        elif seq_local is not None:
            a_raw, b_raw, src = seq_local
            a_eff = (np.asarray(a_raw, dtype=np.int64) // f).astype(np.int64)
            b_eff = (np.asarray(b_raw, dtype=np.int64) // f).astype(np.int64)
            source_sequence_path = str(src)
        elif seq_metrics is not None:
            a_raw, b_raw, src = seq_metrics
            a_eff = (np.asarray(a_raw, dtype=np.int64) // f).astype(np.int64)
            b_eff = (np.asarray(b_raw, dtype=np.int64) // f).astype(np.int64)
            source_sequence_path = str(src)
        else:
            if mode == "strict":
                fail_reason = "missing_real_sequence"
                raise RuntimeError(fail_reason)
            else:
                recon = cfg.get("reconciliation") if isinstance(cfg.get("reconciliation"), dict) else {}
                nblk = int(recon.get("block_symbols") or 512)
                nblk = max(1, nblk)
                a_eff, b_eff = _sample_sequences_from_joint_sparse(
                    joint_sparse_eff,
                    n_symbols=nblk,
                    seed=1000003 + int(block_index),
                )
                sequence_is_sampled = 1
                source_sequence_path = "joint_sparse_sampling_same_source"

        n_symbols = int(min(a_eff.size, b_eff.size))
        if n_symbols <= 0:
            raise RuntimeError("empty sequence after extraction")
        a_eff = np.asarray(a_eff[:n_symbols], dtype=np.int64)
        b_eff = np.asarray(b_eff[:n_symbols], dtype=np.int64)

        if joint_mode_effective == "existing" and mode == "strict" and int(materialize_missing_real_seq) == 1 and str(materialize_origin) == "materialized_from_ttbin":
            joint_mode_effective = "from_sequence"

        if joint_mode_effective == "existing":
            joint_sparse_used = joint_sparse_eff
            joint_origin = "existing"
            joint_source_path = source_joint_path
        elif joint_mode_effective in {"from_sequence", "from_ttbin"}:
            joint_sparse_used = build_joint_counts_sparse_from_sequences(a_eff=a_eff, b_eff=b_eff, d=q)
            joint_origin = "from_ttbin" if joint_mode_effective == "from_ttbin" else "from_sequence"
            joint_source_path = source_sequence_path
            if not joint_sparse_used:
                raise RuntimeError("joint rebuilt from sequence is empty")
        else:
            raise RuntimeError(f"unsupported joint_source_mode={joint_mode_effective}")

        chan_ll_table = _build_chan_ll_table(joint_sparse_used, q=q)
        map_ser, map_ber = _map_sanity(chan_ll_table, a_eff, b_eff, q=q)
        if int(materialize_diagnostics) == 1:
            diag = compute_delta_hist(a_eff=a_eff, b_eff=b_eff, d=q, topk=21)
            diag["d"] = int(q)
            paths = write_materialize_diagnostics(str(root), diag)
            if isinstance(materialize_used_params, dict):
                # Extend diagnostics with pairing context for auditability.
                try:
                    sp = Path(paths.get("seq_pair_stats_path") or "")
                    if sp.exists():
                        sj = json.loads(sp.read_text(encoding="utf-8"))
                        sj["pairing_mode"] = materialize_used_params.get("pairing_mode")
                        sj["gate_width_ps"] = materialize_used_params.get("gate_width_ps")
                        sj["peak_center_ps"] = materialize_used_params.get("peak_center_ps")
                        sj["peak_sigma_ps"] = materialize_used_params.get("peak_sigma_ps")
                        sj["peak_to_bg"] = materialize_used_params.get("peak_to_bg")
                        sp.write_text(json.dumps(sj, ensure_ascii=False, indent=2), encoding="utf-8")
                except Exception:
                    pass
            diag_payload = {
                "enabled": 1,
                "delta_hist_path": paths.get("delta_hist_path"),
                "seq_pair_stats_path": paths.get("seq_pair_stats_path"),
                "n_pairs": int(diag.get("n_pairs", 0)),
                "n_pairs_actual": int(diag.get("n_pairs_actual", diag.get("n_pairs", 0))),
                "raw_ser": float(diag.get("raw_ser", float("nan"))),
                "delta_mode": diag.get("delta_mode"),
                "delta_mode_frac": float(diag.get("delta_mode_frac", float("nan"))),
                "near_neighbor_frac": float(diag.get("near_neighbor_frac", float("nan"))),
                "n_unique_a": int(diag.get("n_unique_a", 0)),
                "n_unique_b": int(diag.get("n_unique_b", 0)),
                "top_a_frac": float(diag.get("top_a_frac", float("nan"))),
                "top_b_frac": float(diag.get("top_b_frac", float("nan"))),
            }
        np.save(root / "a_eff.npy", a_eff.astype(np.int64, copy=False))
        np.save(root / "b_eff.npy", b_eff.astype(np.int64, copy=False))
        np.save(root / "chan_ll_table.npy", chan_ll_table.astype(np.float64, copy=False))
        joint_sidecar_path = root / "joint_counts_sparse.json"
        joint_sidecar_path.write_text(
            json.dumps({"d_eff": q, "factor": f, "joint_counts_sparse": joint_sparse_used}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        try:
            fp = file_fingerprint(joint_sidecar_path)
            joint_fp = {"size": fp.get("size"), "mtime": fp.get("mtime"), "sha256": fp.get("sha256")}
        except Exception:
            joint_fp = {}
        with (root / "map_sanity.csv").open("w", newline="", encoding="utf-8") as fcsv:
            w = csv.DictWriter(fcsv, fieldnames=["point", "factor", "d_eff", "map_ser", "map_ber", "n_symbols", "note"])
            w.writeheader()
            w.writerow(
                {
                    "point": f"{d},{bw}",
                    "factor": f,
                    "d_eff": q,
                    "map_ser": float(map_ser),
                    "map_ber": float(map_ber),
                    "n_symbols": int(n_symbols),
                    "note": "same-source sidecar",
                }
            )

        if sequence_is_sampled == 1:
            fail_reason = "sampled_sequence_not_allowed"
            verdict = "FAIL"
        elif not (math.isfinite(map_ser) and map_ser < 0.1):
            fail_reason = "map_ser>=0.1"
            verdict = "FAIL"
        else:
            fail_reason = ""
            verdict = "PASS"

        ttbin_cfg = cfg.get("ttbin") if isinstance(cfg.get("ttbin"), dict) else {}
        recon_cfg = cfg.get("reconciliation") if isinstance(cfg.get("reconciliation"), dict) else {}
        meta = {
            "created_at": datetime.now().isoformat(),
            "point": {"d": d, "bw": bw},
            "factor": f,
            "d_eff": q,
            "q": q,
            "m": m,
            "block_index": int(block_index),
            "n_symbols": int(n_symbols),
            "source_point_dir": str(point_dir),
            "source_joint_path": source_joint_path,
            "source_sequence_path": source_sequence_path,
            "sequence_source_mode": mode,
            "sequence_is_sampled": int(sequence_is_sampled),
            "joint_source_mode": joint_mode_effective,
            "joint_origin": joint_origin,
            "joint_source_path": joint_source_path,
            "joint_fingerprint": joint_fp,
            "fail_reason": fail_reason,
            "materialize_attempted": int(materialize_attempted),
            "materialize_ok": int(materialize_ok),
            "materialize_origin": materialize_origin,
            "materialize_out_dir": materialize_out_dir,
            "materialize_error": materialize_error,
            "materialize_params": {
                "offset_override_ps": materialize_offset_override_ps,
                "max_pairs": int(materialize_max_pairs_eff),
                "frame_start_override_ps": materialize_frame_start_override_ps,
                "coinc_window_override_ps": materialize_coinc_window_override_ps,
                "pairing_mode": str(materialize_pairing_mode),
                "peak_gate_sigma": materialize_peak_gate_sigma,
                "delay_override_ps": materialize_delay_override_ps,
                "used_params": materialize_used_params,
            },
            "real_sequence_resolve_debug": real_debug,
            "diagnostics": diag_payload,
            "symbolization_snapshot": {
                "bin_width_ps": _to_int(ttbin_cfg.get("bin_width_ps"), bw),
                "dimension": _to_int(cfg.get("dimension"), d),
                "block_symbols": _to_int(recon_cfg.get("block_symbols"), None),
                "mapping": str(recon_cfg.get("mapping") or ""),
                "bit_order": str(recon_cfg.get("bit_order") or ""),
                "ttbin_file": str(ttbin_cfg.get("file") or ""),
                "offset_ps": ttbin_cfg.get("offset_ps"),
                "delay_ps": ttbin_cfg.get("delay_ps"),
                "pairing_window_ps": ttbin_cfg.get("pairing_window_ps"),
                "coincidence_window_ps": ttbin_cfg.get("coincidence_window_ps"),
                "scanfix_align": recon_cfg.get("scanfix_align"),
                "wrap_rule": "floor_div",
            },
            "source_fingerprints": {"metrics_file": metrics_fp},
            "map_sanity": {"map_ser": float(map_ser), "map_ber": float(map_ber), "verdict": verdict},
        }
        (root / "sidecar_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    except Exception as e:
        if not fail_reason:
            fail_reason = "export_exception" if "missing_real_sequence" not in str(e) else "missing_real_sequence"
        verdict = "FAIL"
        meta = {
            "created_at": datetime.now().isoformat(),
            "point": {"d": d, "bw": bw},
            "factor": f,
            "d_eff": q,
            "q": q,
            "m": m,
            "block_index": int(block_index),
            "n_symbols": int(n_symbols),
            "source_joint_path": source_joint_path,
            "source_sequence_path": source_sequence_path,
            "sequence_source_mode": str(sequence_source_mode).strip().lower() or "strict",
            "sequence_is_sampled": int(sequence_is_sampled),
            "joint_source_mode": joint_mode_effective,
            "joint_origin": joint_origin,
            "joint_source_path": joint_source_path,
            "joint_fingerprint": joint_fp,
            "fail_reason": fail_reason,
            "materialize_attempted": int(materialize_attempted),
            "materialize_ok": int(materialize_ok),
            "materialize_origin": materialize_origin,
            "materialize_out_dir": materialize_out_dir,
            "materialize_error": materialize_error,
            "materialize_params": {
                "offset_override_ps": materialize_offset_override_ps,
                "max_pairs": int(materialize_max_pairs_eff),
                "frame_start_override_ps": materialize_frame_start_override_ps,
                "coinc_window_override_ps": materialize_coinc_window_override_ps,
                "pairing_mode": str(materialize_pairing_mode),
                "peak_gate_sigma": materialize_peak_gate_sigma,
                "delay_override_ps": materialize_delay_override_ps,
                "used_params": materialize_used_params,
            },
            "real_sequence_resolve_debug": real_debug,
            "diagnostics": diag_payload,
            "source_fingerprints": {"metrics_file": metrics_fp} if metrics_fp else {},
            "map_sanity": {"map_ser": float(map_ser), "map_ber": float(map_ber), "verdict": verdict},
            "exception": f"{type(e).__name__}: {e}",
        }
        (root / "sidecar_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "sidecar_root": str(root),
        "map_ser": float(map_ser),
        "map_ber": float(map_ber),
        "d": int(d),
        "bw": int(bw),
        "factor": int(f),
        "d_eff": int(q),
        "q": int(q),
        "m": int(m),
        "n_symbols": int(n_symbols),
        "verdict": verdict,
        "fail_reason": fail_reason,
        "sequence_source_mode": str(sequence_source_mode).strip().lower() or "strict",
        "sequence_is_sampled": int(sequence_is_sampled),
        "source_sequence_path": source_sequence_path,
        "joint_source_mode": joint_mode_effective,
        "joint_origin": joint_origin,
        "joint_source_path": joint_source_path,
        "diagnostics": diag_payload,
        "materialize_attempted": int(materialize_attempted),
        "materialize_ok": int(materialize_ok),
        "materialize_origin": materialize_origin,
        "materialize_error": materialize_error,
        "materialize_params": {
            "offset_override_ps": materialize_offset_override_ps,
            "max_pairs": int(materialize_max_pairs_eff),
            "frame_start_override_ps": materialize_frame_start_override_ps,
            "coinc_window_override_ps": materialize_coinc_window_override_ps,
            "pairing_mode": str(materialize_pairing_mode),
            "peak_gate_sigma": materialize_peak_gate_sigma,
            "delay_override_ps": materialize_delay_override_ps,
            "used_params": materialize_used_params,
        },
        "source_joint_path": source_joint_path,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Export same-source joint+sequence sidecar for NB-LDPC demo.")
    ap.add_argument("--point", required=True, help='format "d,bw", e.g. 1024,200')
    ap.add_argument("--factor", type=int, default=2)
    ap.add_argument("--block-index", type=int, default=0)
    ap.add_argument("--sequence-source-mode", choices=["strict", "allow_sampling"], default="strict")
    ap.add_argument("--materialize-missing-real-seq", type=int, choices=[0, 1], default=0)
    ap.add_argument("--joint-source-mode", choices=["existing", "from_sequence", "from_ttbin"], default="existing")
    ap.add_argument("--materialize-diagnostics", type=int, choices=[0, 1], default=0)
    ap.add_argument("--materialize-offset-override-ps", type=int, default=None)
    ap.add_argument("--materialize-max-pairs", type=int, default=256)
    ap.add_argument("--materialize-frame-start-override-ps", type=int, default=None)
    ap.add_argument("--materialize-coinc-window-override-ps", type=int, default=None)
    ap.add_argument("--materialize-pairing-mode", choices=["nearest", "greedy", "two_pointer", "peak_gated"], default="nearest")
    ap.add_argument("--materialize-peak-gate-sigma", type=float, default=None)
    ap.add_argument("--materialize-delay-override-ps", type=int, default=None)
    ap.add_argument("--out-root", required=True)
    args = ap.parse_args()

    res = export_sidecar_for_point(
        point=args.point,
        factor=int(args.factor),
        block_index=int(args.block_index),
        out_root=str(args.out_root),
        sequence_source_mode=str(args.sequence_source_mode),
        materialize_missing_real_seq=int(args.materialize_missing_real_seq),
        joint_source_mode=str(args.joint_source_mode),
        materialize_diagnostics=int(args.materialize_diagnostics),
        materialize_offset_override_ps=args.materialize_offset_override_ps,
        materialize_max_pairs=int(args.materialize_max_pairs),
        materialize_frame_start_override_ps=args.materialize_frame_start_override_ps,
        materialize_coinc_window_override_ps=args.materialize_coinc_window_override_ps,
        materialize_pairing_mode=str(args.materialize_pairing_mode),
        materialize_peak_gate_sigma=args.materialize_peak_gate_sigma,
        materialize_delay_override_ps=args.materialize_delay_override_ps,
    )
    print(
        f"[SIDEcar] point=({res.get('d',0)},{res.get('bw',0)}) factor={res.get('factor',0)} "
        f"d_eff={res.get('d_eff',0)} n_symbols={res.get('n_symbols',0)}"
    )
    print(f"[SIDEcar] source_joint={res.get('source_joint_path','')}")
    print(
        f"[SIDEcar] sequence_source_mode={res.get('sequence_source_mode','strict')} "
        f"sampled={res.get('sequence_is_sampled',0)} source_seq={res.get('source_sequence_path','')}"
    )
    print(
        f"[SIDEcar] joint_origin={res.get('joint_origin','')} "
        f"joint_mode={res.get('joint_source_mode','')} joint_src={res.get('joint_source_path','')}"
    )
    if int(args.materialize_diagnostics) == 1:
        dg = res.get("diagnostics") if isinstance(res.get("diagnostics"), dict) else {}
        print(
            "[SIDEcar] diag: "
            f"n_pairs={dg.get('n_pairs')} raw_ser={dg.get('raw_ser')} "
            f"delta_mode={dg.get('delta_mode')} delta_mode_frac={dg.get('delta_mode_frac')} "
            f"near_neighbor_frac={dg.get('near_neighbor_frac')}"
        )
    if int(res.get("sequence_is_sampled", 0)) == 1:
        print("[SIDEcar] WARNING: sampled sequence used (publication disabled)")
    print(f"[SIDEcar] map_sanity: map_ser={res.get('map_ser')} map_ber={res.get('map_ber')}")
    print(f"[SIDEcar] verdict: {res.get('verdict','FAIL')}")
    return 0 if res.get("verdict") == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
