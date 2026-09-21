"""P3 A1 census arm — trio-only H_full census with mandatory pre-pairing alignment.

DECIDE track, Acceptance ID G-P3 (A1 arm only). Per dataset, IN ORDER:
  1. open ONLY the base ``X.ttbin`` member (vendor auto-follow covers ``.1``);
     NEVER open both members, NEVER concatenate;
  2. derive correlation alignment per packet §3A via the additive
     ``comparison_bench/.../io/align_wrapper.py`` (frozen histogram call);
  3. alignment FAIL ⇒ STOP-BLOCKED for that dataset: record, continue to the
     next dataset (no abort, no fallback, never 0/borrowed/recorded offset);
  4. ONLY for passed datasets: pairing/histogram/entropy with the frozen trio
     parameters and the DERIVED offset, via the frozen ``compute_ttbin_metrics``
     (read-only) plus per-pair series from the same frozen pairing/framing
     arithmetic (read-only imports), asserted equal on aggregates;
  5. record all outputs.

Frozen trio parameters (preflight): d=1024, bw=200 ps, period=204800 ps,
pairing nearest (loader policy ``nearest_unique``), rule legacy_v1,
pairing_threshold_ps=40000 (template provenance, not consumed by the frozen
loader), gate/coin_window_ps=200 (== acquisition FileWriter window 200),
corr 16384 bins (100 ps / ±819200 ps), channels A=1/B=5, framing global,
postselect keep_all (loader defaults; recorded explicitly per row).
Prior recorded offsets (COMPARISON ONLY, never used): T2-1M -50 (bin 8191),
T2-1.5M +50 (bin 8192), T2-2M +50 (bin 8192).

Frozen estimator: H_full = H_L1 + H_L2, F03 (u1=a>>5, u2=a&31), plug-in
P(a|b) on the TRAIN pool, bits per GF(32) symbol; Miller-Madow
(K-1)/(2N·ln2); frame-level bootstrap (frozen seed); split 60/20/20
consecutive-time by ascending frame index; anchor 0.83256272 ± 0.01.

House style follows ``comparison_bench/.../cli/p3_stage05_probe.py``:
``main() -> int`` + ``if __name__ == "__main__": raise SystemExit(main())``.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import resource
import time
from pathlib import Path
from typing import Any

import numpy as np

from comparison_bench.src.comparison_bench.io.ttbin_compat import install_timetagger_alias
from comparison_bench.src.comparison_bench.io import align_wrapper as aw

# Frozen A1 scope: the Jan-21 trio ONLY.
DATASET_IDS = ["T2-1M", "T2-1.5M", "T2-2M"]
PRIOR_OFFSET_PS = {"T2-1M": -50, "T2-1.5M": 50, "T2-2M": 50}
PRIOR_BIN = {"T2-1M": 8191, "T2-1.5M": 8192, "T2-2M": 8192}

# Frozen trio ports (see module docstring).
CH_A, CH_B = 1, 5
COIN_WINDOW_PS = 200
BIN_WIDTH_PS = 200
FRAME_BINS = 1024
ALIGN_MODE_FRAMING = "global"
POSTSELECT = "keep_all"
PAIRING_THRESHOLD_PS = 40000  # template provenance only (unused by frozen loader)

# Frozen estimator / gate constants.
ANCHOR_H_FULL = 0.83256272
ANCHOR_TOL = 0.01
SUPPORT_CI_THRESHOLD = 0.02
FILENAME_DURATION_TAG = "3s"

# Frozen budgets (packet §10).
PER_DATASET_CEILING_S = 1800.0


def parse_bases(raw: str) -> list[str]:
    bases = [b.strip() for b in raw.split(";") if b.strip()]
    if len(bases) != 3:
        raise SystemExit(f"expected exactly 3 semicolon-separated trio base paths, got {len(bases)}")
    for b in bases:
        if not b.endswith(".ttbin") or b.endswith(".1.ttbin"):
            raise SystemExit(f"base must be an X.ttbin member, got: {b}")
        if not os.path.exists(b):
            raise SystemExit(f"base path does not exist: {b}")
    return bases


def parse_datasets(raw: str) -> list[str]:
    ids = [d.strip() for d in raw.split(";") if d.strip()]
    if len(ids) != 3 or any(d not in DATASET_IDS for d in ids):
        raise SystemExit(f"--datasets must be exactly the trio {DATASET_IDS}, got: {ids}")
    return ids


def h_full_f03(N_ab: np.ndarray) -> tuple[float, float, float]:
    """Frozen estimator: H_L1, H_L2, H_full (F03 plug-in, bits/GF(32) symbol)."""
    N = np.asarray(N_ab, dtype=np.float64)
    tot = float(N.sum())
    if tot <= 0:
        return 0.0, 0.0, 0.0
    col = N.sum(axis=0, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        Pagb = np.divide(N, col, out=np.zeros_like(N), where=col > 0)
    p_b = (N.sum(axis=0) / tot)
    u1 = (np.arange(1024) >> 5).astype(np.int64)
    u2 = (np.arange(1024) & 31).astype(np.int64)
    H1 = 0.0
    for b in range(1024):
        if p_b[b] <= 0:
            continue
        pu1 = np.bincount(u1, weights=Pagb[:, b], minlength=32)
        pu1 = pu1[pu1 > 0]
        if pu1.size:
            H1 += p_b[b] * float(-np.sum(pu1 * np.log2(pu1)))
    H2 = 0.0
    for b in range(1024):
        if p_b[b] <= 0:
            continue
        for uu in range(32):
            sel = u1 == uu
            s = float(Pagb[sel, b].sum())
            if s <= 0:
                continue
            row = Pagb[sel, b] / s
            pu2 = np.bincount(u2[sel], weights=row, minlength=32)
            pu2 = pu2[pu2 > 0]
            if pu2.size:
                H2 += p_b[b] * s * float(-np.sum(pu2 * np.log2(pu2)))
    return float(H1), float(H2), float(H1 + H2)


def acf(x: np.ndarray, lag: int) -> float | None:
    """Lag-k autocorrelation (mean-centered). None when undefined."""
    x = np.asarray(x, dtype=np.float64)
    n = x.size
    if n <= lag or lag <= 0:
        return None
    v = float(np.var(x))
    if v <= 0:
        return None
    m = float(np.mean(x))
    return float(np.mean((x[: n - lag] - m) * (x[lag:] - m)) / v)


def run_dataset(
    dataset_id: str,
    base: str,
    root: Path,
    per_read_timeout_s: float,
    global_deadline: float,
    bootstrap_seed: int,
    bootstrap_resamples: int,
    splits_so_far: dict[str, Any],
) -> dict[str, Any]:
    """Execute ONE dataset arm. Returns the per-dataset record (always)."""
    t_ds = time.monotonic()
    rec: dict[str, Any] = {
        "dataset_id": dataset_id,
        "family": "B",
        "ttbin_path": base,
        "ttbin_member_used": None,
        "duration_measured_s": None,
        "filename_duration_tag": FILENAME_DURATION_TAG,
        "tag_disputed": None,
        "alignment_mode": "CONFIGURED",
        "channels_A": CH_A,
        "channels_B": CH_B,
        "offset_ps": None,
        "coin_window_ps": COIN_WINDOW_PS,
        "pairing_threshold_ps": PAIRING_THRESHOLD_PS,
        "bin_width_ps": BIN_WIDTH_PS,
        "frame_bins": FRAME_BINS,
        "align": ALIGN_MODE_FRAMING,
        "postselect": POSTSELECT,
        "framing_provenance": "MEASURED",
        "offset_ps_prior_recorded": PRIOR_OFFSET_PS[dataset_id],
        "prior_bin_index": PRIOR_BIN[dataset_id],
        "status": "BLOCKED",
    }

    def wall_left(ds_elapsed: float) -> bool:
        return ds_elapsed <= PER_DATASET_CEILING_S and time.monotonic() <= global_deadline

    # (1) Open base member ONLY. Any failure ⇒ BLOCKED (no .1 fallback: A1 is base-only).
    from TimeTagger import FileReader  # noqa: E402  (alias installed in main)

    try:
        reader = FileReader(base)
    except Exception as exc:
        rec["align_status"] = "blocked_open_failed"
        rec["block_reason"] = f"base open failed (single member only, never both): {exc}"
        return rec
    rec["ttbin_member_used"] = base
    # (1b) Read events via the frozen loader (full vendor-auto-followed stream).
    from src.qkd_io.ttbin_pipeline import (  # noqa: E402  (frozen, read-only)
        _frame_global,
        _pair_nearest_unique,
        compute_ttbin_metrics,
        read_ttbin_events,
    )

    t_read = time.monotonic()
    try:
        events = read_ttbin_events(base)
    except Exception as exc:
        rec["align_status"] = "blocked_read_failed"
        rec["block_reason"] = f"frozen read_ttbin_events failed: {exc}"
        return rec
    finally:
        try:
            reader.close()
        except Exception:
            pass
    read_s = time.monotonic() - t_read
    rec["read_wall_s"] = read_s
    if read_s > per_read_timeout_s:
        rec["status"] = "INCOMPLETE"
        rec["block_reason"] = f"per-read wall {read_s:.1f}s exceeded {per_read_timeout_s:.0f}s"
        return rec
    t = np.asarray(events.time_ps, dtype=np.int64)
    if t.size:
        rec["duration_measured_s"] = float(t.max() - t.min()) * 1e-12
        rec["tag_disputed"] = bool(abs(rec["duration_measured_s"] - 3.0) > 0.5)

    # (2) Derive alignment per §3A (frozen histogram + gates).
    t_align = time.monotonic()
    align = aw.derive_alignment(events=events, ch_a=CH_A, ch_b=CH_B)
    align["align_wall_s"] = time.monotonic() - t_align
    for k in ("offset_ps_derived", "peak_bin_index", "peak_center_ps",
              "peak_to_bg", "sigma_crude_ps", "align_status"):
        rec[k] = align[k]
    rec["alignment"] = {k: v for k, v in align.items()
                        if k in ("bin_width_ps", "max_lag_ps", "n_bins", "count_A",
                                 "count_B", "total_pairs_in_window", "single_mode_ok",
                                 "n_local_maxima", "n_secondary_violations", "align_wall_s")}
    # A1 one-bin agreement (FINDING if disagree — never adjusted).
    rec["one_bin_check"] = aw.offsets_agree_one_bin(
        derived_offset_ps=align["offset_ps_derived"] if align["offset_ps_derived"] is not None else -10**12,
        derived_bin=align["peak_bin_index"] if align["peak_bin_index"] is not None else -10**12,
        prior_offset_ps=PRIOR_OFFSET_PS[dataset_id], prior_bin=PRIOR_BIN[dataset_id])

    # (3) Alignment FAIL ⇒ STOP-BLOCKED for this dataset: record, continue batch.
    if align["align_status"] != "ok":
        rec["status"] = "BLOCKED"
        rec["block_reason"] = f"alignment {align['align_status']}; no pairing/entropy (no fallback)"
        return rec

    # (4) Passed only: adopt the DERIVED offset (gate raises otherwise).
    offset = aw.require_alignment_passed(align)
    rec["offset_ps"] = offset
    cfg = {
        "channels": {"A": CH_A, "B": CH_B},
        "pairing": {"coin_window_ps": COIN_WINDOW_PS, "offset_ps": offset,
                    "policy": "nearest_unique"},
        "framing": {"bin_width_ps": BIN_WIDTH_PS, "frame_bins": FRAME_BINS,
                    "align": ALIGN_MODE_FRAMING, "postselect": POSTSELECT},
    }
    metrics = compute_ttbin_metrics(events=events, cfg=cfg)
    rec["ttbin_config"] = cfg
    rec["qber"] = metrics["framed"]["qber"]
    rec["mutual_information_bits"] = metrics["framed"]["mutual_information_bits"]

    # Per-pair series from the SAME frozen arithmetic (read-only reuse).
    valid = (np.asarray(events.event_type, dtype=np.int64) == 0) \
        if events.event_type is not None else np.ones(t.shape, dtype=bool)
    ch = np.asarray(events.channel, dtype=np.int64)
    t_a = t[valid & (ch == CH_A)]
    t_b = t[valid & (ch == CH_B)]
    tmin = int(t.min()) if t.size else 0
    del events  # raw stream no longer needed; bound RSS
    pa, pb = _pair_nearest_unique(t_a=t_a, t_b=t_b,
                                  window_ps=COIN_WINDOW_PS, offset_ps=offset)
    del t_a, t_b
    if ALIGN_MODE_FRAMING == "global":
        fa, sa = _frame_global(t_ps=pa, bin_width_ps=BIN_WIDTH_PS,
                               frame_bins=FRAME_BINS, t0_ps=tmin)
        fb, sb = _frame_global(t_ps=pb, bin_width_ps=BIN_WIDTH_PS,
                               frame_bins=FRAME_BINS, t0_ps=tmin)
    else:  # pragma: no cover — frozen A1 choice is global
        raise SystemExit("A1 framing is frozen to global")
    keep = (fa >= 0) & (fb >= 0) & (fa == fb) & (sa >= 0) & (sb >= 0)
    frame, sa, sb = fa[keep], sa[keep], sb[keep]
    del pa, pb, fa, fb
    # Control-arm equality assertion vs the frozen aggregates.
    assert int(frame.size) == int(metrics["framed"]["n_symbols"]), \
        f"series/aggregate n_symbols mismatch: {frame.size} vs {metrics['framed']['n_symbols']}"
    rec["n_pairs_N"] = int(frame.size)
    rec["n_frames"] = int(np.unique(frame).size) if frame.size else 0

    # Split manifest 60/20/20 consecutive-time by ascending frame index —
    # decided AND written BEFORE any statistic is computed.
    uframes = np.unique(frame)
    nfr = int(uframes.size)
    n_tr = int(nfr * 0.6)
    n_va = int(nfr * 0.2)
    split = {
        "rule": "60/20/20 consecutive-time by ascending frame index (V49 convention)",
        "train_frames": [int(uframes[0]), int(uframes[n_tr - 1])] if n_tr else None,
        "val_frames": [int(uframes[n_tr]), int(uframes[n_tr + n_va - 1])] if n_va else None,
        "hold_frames": [int(uframes[n_tr + n_va]), int(uframes[-1])] if nfr - n_tr - n_va else None,
        "split_train_frames": n_tr,
        "split_val_frames": n_va,
        "split_hold_frames": int(nfr - n_tr - n_va),
    }
    rec["split_train_frames"] = n_tr
    rec["split_val_frames"] = n_va
    rec["split_hold_frames"] = int(nfr - n_tr - n_va)
    splits_so_far[dataset_id] = split
    with open(root / "split_manifest.json", "w", encoding="utf-8") as fh:
        json.dump(splits_so_far, fh, indent=2)

    # Frame positions for per-frame / block / bootstrap statistics.
    order = np.argsort(frame, kind="stable")
    fs = frame[order]
    as_ = sa[order]
    bs = sb[order]
    uniq, inv, cnt = np.unique(fs, return_inverse=True, return_counts=True)
    # Per-frame mismatch counts in frame order.
    mis = (as_ != bs).astype(np.int64)
    w = np.bincount(inv, weights=mis, minlength=nfr).astype(np.int64)
    rec["per_frame_weight_mean"] = float(np.mean(w)) if nfr else None
    rec["per_frame_weight_median"] = float(np.median(w)) if nfr else None
    rec["per_frame_weight_min"] = int(np.min(w)) if nfr else None
    rec["per_frame_weight_max"] = int(np.max(w)) if nfr else None
    rec["per_frame_weight_p99"] = float(np.percentile(w, 99)) if nfr else None
    rec["per_frame_weight_hist"] = np.bincount(w).tolist() if nfr else []
    # Per-frame u1 plug-in entropy series (operator definition, stated in outputs).
    u1s = (as_ >> 5).astype(np.int64)
    h1f = np.empty(nfr, dtype=np.float64)
    start = 0
    for i, c in enumerate(cnt.tolist()):
        seg = u1s[order[start:start + c]]
        p = np.bincount(seg, minlength=32).astype(np.float64) / c
        p = p[p > 0]
        h1f[i] = float(-np.sum(p * np.log2(p)))
        start += c
    rec["acf_lag1_mismatch"] = acf(w, 1)
    rec["acf_lag2_mismatch"] = acf(w, 2)
    rec["acf_lag1_HL1"] = acf(h1f, 1)
    rec["acf_lag2_HL1"] = acf(h1f, 2)

    # TRAIN-pool estimator + support/occupancy/MM.
    tr_mask = inv < n_tr
    tr_idx = order[tr_mask]
    N_ab = np.bincount(as_[tr_idx] * 1024 + bs[tr_idx],
                       minlength=1024 * 1024).reshape(1024, 1024).astype(np.float64)
    N = int(N_ab.sum())
    K = int(np.count_nonzero(N_ab))
    H1, H2, Hf = h_full_f03(N_ab)
    mm = (K - 1) / (2 * N * math.log(2)) if N > 0 else None
    rec["support_cells"] = K
    rec["occupancy"] = K / (1024 * 1024)
    rec["H_L1"] = H1
    rec["H_L2"] = H2
    rec["H_full_plug"] = Hf
    rec["H_full_MM"] = (Hf + mm) if mm is not None else None
    rec["MM_correction"] = mm

    # Held-out gap (V49 convention): NLL of HOLD under TRAIN P(a|b), covered only.
    col = N_ab.sum(axis=0, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        Pagb = np.divide(N_ab, col, out=np.zeros_like(N_ab), where=col > 0)
    ho_mask = inv >= (n_tr + n_va)
    ho_idx = order[ho_mask]
    ph = Pagb[as_[ho_idx], bs[ho_idx]]
    covered = ph > 0
    rec["hold_uncovered_pairs"] = int((~covered).sum())
    rec["hold_pairs"] = int(ho_idx.size)
    if int(covered.sum()) > 0:
        nll = float(np.mean(-np.log2(ph[covered])))
    else:
        nll = None
    rec["NLL_HOLD"] = nll
    rec["delta_hold"] = (nll - Hf) if nll is not None else None

    # Frame-level bootstrap CI (frozen seed, >=200 resamples).
    rng = np.random.default_rng(int(bootstrap_seed))
    # Group TRAIN pair positions by frame for resampling.
    tr_inv = inv[tr_mask]
    tr_order = np.argsort(tr_inv, kind="stable")
    bounds = np.searchsorted(tr_inv[tr_order], np.arange(n_tr + 1))
    flat = tr_idx[tr_order]
    boots = np.empty(int(bootstrap_resamples))
    for r in range(int(bootstrap_resamples)):
        pick = rng.integers(0, n_tr, size=n_tr)
        idx = np.concatenate([flat[bounds[p]:bounds[p + 1]] for p in pick.tolist()])
        Nb = np.bincount(as_[idx] * 1024 + bs[idx],
                         minlength=1024 * 1024).reshape(1024, 1024).astype(np.float64)
        _, _, boots[r] = h_full_f03(Nb)
    rec["bootstrap_resamples"] = int(bootstrap_resamples)
    rec["bootstrap_seed"] = int(bootstrap_seed)
    rec["bootstrap_CI_halfwidth"] = float((np.percentile(boots, 97.5) - np.percentile(boots, 2.5)) / 2)
    rec["bootstrap_CI_lo"] = float(np.percentile(boots, 2.5))
    rec["bootstrap_CI_hi"] = float(np.percentile(boots, 97.5))

    # Block-to-block drift: consecutive superframes of 4 frames.
    n_sup = nfr // 4
    rec["n_superframes"] = int(n_sup)
    bh = np.empty(n_sup)
    for s in range(n_sup):
        m = (inv >= 4 * s) & (inv < 4 * s + 4)
        ii = order[m]
        Nb = np.bincount(as_[ii] * 1024 + bs[ii],
                         minlength=1024 * 1024).reshape(1024, 1024).astype(np.float64)
        _, _, bh[s] = h_full_f03(Nb)
    rec["drift_block_Hfull_max_min"] = float(bh.max() - bh.min()) if n_sup else None
    if n_sup >= 2:
        x = np.arange(n_sup, dtype=np.float64)
        slope = float(np.polyfit(x, bh, 1)[0])
    else:
        slope = None
    rec["drift_slope"] = slope
    rec["block_Hfull_series"] = bh.tolist() if n_sup else []

    # Anchor comparison (frozen tolerance; [TO BE CONFIRMED] per packet §9.4).
    rec["anchor_H_full"] = ANCHOR_H_FULL
    rec["anchor_delta"] = float(Hf - ANCHOR_H_FULL)
    rec["anchor_reproduced_within_0p01"] = bool(abs(Hf - ANCHOR_H_FULL) <= ANCHOR_TOL)
    rec["comparable_by_anchor"] = "YES"
    rec["split_side"] = "TRAIN plug-in (held-out gap reported separately; never quoted as held-out)"
    if rec["bootstrap_CI_halfwidth"] is not None and rec["bootstrap_CI_halfwidth"] > SUPPORT_CI_THRESHOLD:
        rec["status"] = "INSUFFICIENT-SUPPORT"
    else:
        rec["status"] = "OK"

    ds_wall = time.monotonic() - t_ds
    rec["dataset_wall_s"] = ds_wall
    if not wall_left(ds_wall):
        rec["status"] = "INCOMPLETE"
        rec["block_reason"] = f"dataset wall {ds_wall:.1f}s exceeded ceiling"
    return rec


def write_shared_tables(records: list[dict[str, Any]], root: Path) -> None:
    align_lines = ["# P3 A1 alignment + duration table", "",
                   "| id | duration_measured_s | offset_ps_derived | peak_bin_index | "
                   "peak_center_ps | peak_to_bg | sigma_crude_ps | align_status | "
                   "prior | one_bin_agree | finding |",
                   "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in records:
        ob = r.get("one_bin_check") or {}
        agree = ob.get("agree_one_bin")
        finding = "FINDING" if agree is False else ""
        align_lines.append(
            f"| {r['dataset_id']} | {r.get('duration_measured_s')} | "
            f"{r.get('offset_ps_derived')} | {r.get('peak_bin_index')} | "
            f"{r.get('peak_center_ps')} | {r.get('peak_to_bg')} | "
            f"{r.get('sigma_crude_ps')} | {r.get('align_status')} | "
            f"{r.get('offset_ps_prior_recorded')} | {agree} | {finding} |")
    (root / "alignment_table.md").write_text("\n".join(align_lines) + "\n", encoding="utf-8")

    h_lines = ["# P3 A1 H_full table (TRAIN plug-in; split side stated per row)", "",
               "| id | N | support | occupancy | H_full_plug | MM | H_full_MM | "
               "CI_halfwidth | CI_lo | CI_hi | split_side | anchor_Δ | within_±0.01 | status |",
               "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in records:
        h_lines.append(
            f"| {r['dataset_id']} | {r.get('n_pairs_N')} | {r.get('support_cells')} | "
            f"{r.get('occupancy')} | {r.get('H_full_plug')} | {r.get('MM_correction')} | "
            f"{r.get('H_full_MM')} | {r.get('bootstrap_CI_halfwidth')} | "
            f"{r.get('bootstrap_CI_lo')} | {r.get('bootstrap_CI_hi')} | "
            f"{r.get('split_side')} | {r.get('anchor_delta')} | "
            f"{r.get('anchor_reproduced_within_0p01')} | {r.get('status')} |")
    (root / "H_full_table.md").write_text("\n".join(h_lines) + "\n", encoding="utf-8")

    m_lines = ["# P3 A1 memory / stationarity battery", ""]
    for r in records:
        m_lines += [
            f"## {r['dataset_id']} (status={r.get('status')})", "",
            f"- per-frame weight: mean={r.get('per_frame_weight_mean')} "
            f"median={r.get('per_frame_weight_median')} min={r.get('per_frame_weight_min')} "
            f"max={r.get('per_frame_weight_max')} p99={r.get('per_frame_weight_p99')}",
            f"- drift: n_superframes={r.get('n_superframes')} "
            f"max_min={r.get('drift_block_Hfull_max_min')} slope={r.get('drift_slope')}",
            f"- acf mismatch lag1={r.get('acf_lag1_mismatch')} lag2={r.get('acf_lag2_mismatch')}; "
            f"acf H_L1 lag1={r.get('acf_lag1_HL1')} lag2={r.get('acf_lag2_HL1')}",
            f"- split: train={r.get('split_train_frames')} val={r.get('split_val_frames')} "
            f"hold={r.get('split_hold_frames')}; NLL_HOLD={r.get('NLL_HOLD')} "
            f"Δhold={r.get('delta_hold')} uncovered={r.get('hold_uncovered_pairs')}/{r.get('hold_pairs')}",
            ""]
    m_lines += ["Memoryless-assumption verdict: stated by the main thread from the numbers "
                "above; this record draws no conclusion (packet §7.5).", ""]
    (root / "memory_stationarity.md").write_text("\n".join(m_lines), encoding="utf-8")

    cols = ["dataset_id", "family", "ttbin_path", "ttbin_member_used", "duration_measured_s",
            "filename_duration_tag", "tag_disputed", "alignment_mode", "channels_A", "channels_B",
            "offset_ps", "coin_window_ps", "bin_width_ps", "frame_bins", "align", "postselect",
            "framing_provenance", "offset_ps_derived", "peak_bin_index", "peak_center_ps",
            "peak_to_bg", "sigma_crude_ps", "align_status", "offset_ps_prior_recorded",
            "n_frames", "n_pairs_N", "support_cells", "occupancy", "H_L1", "H_L2",
            "H_full_plug", "H_full_MM", "NLL_HOLD", "delta_hold", "bootstrap_CI_halfwidth",
            "n_superframes", "per_frame_weight_mean", "per_frame_weight_median",
            "per_frame_weight_min", "per_frame_weight_max", "per_frame_weight_p99",
            "drift_block_Hfull_max_min", "drift_slope", "acf_lag1_mismatch", "acf_lag1_HL1",
            "split_train_frames", "split_val_frames", "split_hold_frames",
            "comparable_by_anchor", "status"]
    with open(root / "census_table.csv", "w", encoding="utf-8", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(cols)
        for r in records:
            wr.writerow([r.get(c) for c in cols])
    with open(root / "census_table.json", "w", encoding="utf-8") as fh:
        json.dump([{c: r.get(c) for c in cols} for r in records], fh, indent=2)


def main() -> int:
    ap = argparse.ArgumentParser(description="P3 A1 trio census (G-P3, A1 arm only).")
    ap.add_argument("--bases", required=True,
                    help="semicolon-separated base X.ttbin paths, exactly 3 (trio order)")
    ap.add_argument("--datasets", default=";".join(DATASET_IDS),
                    help="semicolon-separated dataset ids (must be exactly the trio)")
    ap.add_argument("--root", required=True, help="fresh additive output root")
    ap.add_argument("--per-read-timeout-s", type=float, default=300.0)
    ap.add_argument("--budget-s", type=float, default=5400.0)
    ap.add_argument("--bootstrap-seed", type=int, default=20260921)
    ap.add_argument("--bootstrap-resamples", type=int, default=200)
    args = ap.parse_args()

    if args.per_read_timeout_s <= 0:
        raise SystemExit("--per-read-timeout-s must be > 0")
    if args.budget_s <= 0:
        raise SystemExit("--budget-s must be > 0")
    if args.bootstrap_resamples < 200:
        raise SystemExit("--bootstrap-resamples must be >= 200 (frozen minimum)")
    bases = parse_bases(args.bases)
    ids = parse_datasets(args.datasets)
    root = Path(args.root)
    if root.exists():
        raise SystemExit(f"output root already exists (refusing to overwrite): {root}")
    root.mkdir(parents=True, exist_ok=False)

    install_timetagger_alias()
    import TimeTagger  # noqa: F401,E402  (resolves via alias; proves Q1 inside the run)

    wall0 = time.monotonic()
    global_deadline = wall0 + float(args.budget_s)
    records: list[dict[str, Any]] = []
    splits: dict[str, Any] = {}
    for did, base in zip(ids, bases, strict=True):
        if time.monotonic() > global_deadline:
            records.append({"dataset_id": did, "family": "B", "ttbin_path": base,
                            "status": "INCOMPLETE", "block_reason": "global budget exhausted",
                            "filename_duration_tag": FILENAME_DURATION_TAG})
            continue
        rec = run_dataset(did, base, root, args.per_read_timeout_s, global_deadline,
                          args.bootstrap_seed, args.bootstrap_resamples, splits)
        with open(root / f"{did}.json", "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        records.append(rec)
        print(f"{did}: status={rec['status']} align={rec.get('align_status')} "
              f"offset={rec.get('offset_ps_derived')} H_full={rec.get('H_full_plug')} "
              f"wall={rec.get('dataset_wall_s')}", flush=True)
        if rec.get("status") == "INCOMPLETE":
            print("wall hit: STOPPING batch, retaining everything (never continued).", flush=True)
            break
    write_shared_tables(records, root)
    wall_dt = time.monotonic() - wall0
    peak_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(f"done: n={len(records)} wall_s={wall_dt:.1f} peak_rss_kb={peak_kb}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
