from __future__ import annotations

import json
import hashlib
import math
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

_TTBIN_PARSE_CALLS = 0


@dataclass(frozen=True)
class TTBinEvents:
    time_ps: np.ndarray
    channel: np.ndarray
    event_type: np.ndarray | None = None
    missed_events: np.ndarray | None = None


def _as_int(value: object, *, default: int | None = None) -> int | None:
    if value is None:
        return default
    try:
        return int(value)
    except Exception:
        return default


def _as_float(value: object, *, default: float | None = None) -> float | None:
    if value is None:
        return default
    try:
        return float(value)
    except Exception:
        return default


def _safe_log2(x: float) -> float:
    return math.log(x, 2) if x > 0 else float("-inf")


def compute_delta_distribution_from_joint_sparse(
    *,
    joint_counts_sparse: list[dict[str, Any]],
    dimension: int,
    with_prob: bool = True,
) -> tuple[np.ndarray, np.ndarray | None]:
    """Build delta histogram/probability from sparse joint symbol counts.

    Delta convention:
      delta = (j - i) mod d
    where i/j are symbol indices in the sparse joint list.
    """
    d = int(dimension)
    if d <= 0:
        raise ValueError("dimension must be positive")

    delta_counts = np.zeros((d,), dtype=np.int64)
    for entry in joint_counts_sparse:
        if not isinstance(entry, dict):
            raise ValueError("joint_counts_sparse entries must be objects")
        i = _as_int(entry.get("i"))
        j = _as_int(entry.get("j"))
        count = _as_int(entry.get("count"))
        if i is None or j is None or count is None:
            raise ValueError("joint_counts_sparse entry requires integer i/j/count")
        if count < 0:
            raise ValueError("joint_counts_sparse count must be non-negative")
        if count == 0:
            continue
        delta = (int(j) - int(i)) % d
        delta_counts[delta] += np.int64(count)

    if not with_prob:
        return delta_counts, None

    total = int(np.sum(delta_counts, dtype=np.int64))
    if total > 0:
        delta_prob = delta_counts.astype(np.float64) / float(total)
    else:
        delta_prob = np.zeros((d,), dtype=np.float64)
    return delta_counts, delta_prob


def read_ttbin_events(ttbin_file: Path | str) -> TTBinEvents:
    """Read .ttbin using TimeTagger's FileReader if available.

    This function intentionally does not implement a binary parser for the .ttbin format.
    It relies on the official TimeTagger Python package when installed.
    """
    timing_enabled = os.getenv("HDQKD_TIMING", "0") == "1"
    cache_enabled = os.getenv("HDQKD_TTBIN_CACHE", "0") == "1"
    cache_dir = os.getenv("HDQKD_TTBIN_CACHE_DIR", "").strip()
    global _TTBIN_PARSE_CALLS
    if timing_enabled:
        try:
            _TTBIN_PARSE_CALLS += 1
        except Exception:
            _TTBIN_PARSE_CALLS = 1
        call_idx = int(_TTBIN_PARSE_CALLS)
        t0 = time.perf_counter()
    else:
        call_idx = 0
        t0 = 0.0

    p = Path(ttbin_file)
    if cache_enabled and cache_dir:
        try:
            st = p.stat()
            key = {
                "ttbin": str(p.resolve()),
                "size": int(st.st_size),
                "mtime_ns": int(getattr(st, "st_mtime_ns", int(st.st_mtime * 1e9))),
                "reader": "ttbin_pipeline",
            }
            h = hashlib.sha256(json.dumps(key, sort_keys=True).encode("utf-8")).hexdigest()[:16]
            cache_base = Path(cache_dir)
            cache_base.mkdir(parents=True, exist_ok=True)
            npz_path = cache_base / f"parsed_{h}.npz"
            meta_path = cache_base / f"parsed_{h}.json"
            if npz_path.exists():
                t_load0 = time.perf_counter() if timing_enabled else 0.0
                with np.load(str(npz_path), allow_pickle=False) as z:
                    ch = z["channel"].astype(np.int64, copy=False)
                    ts = z["time_ps"].astype(np.int64, copy=False)
                    et = z["event_type"].astype(np.int64, copy=False) if "event_type" in z else None
                    me = z["missed_events"] if "missed_events" in z else None
                if et is not None and getattr(et, "size", 0) == 0:
                    et = None
                if me is not None and getattr(me, "size", 0) == 0:
                    me = None
                if timing_enabled:
                    dt = time.perf_counter() - t_load0
                    try:
                        print(f"TTBIN_CACHE hit hash={h} load_s={dt:.6g} dir={cache_base}", file=sys.__stdout__)
                    except Exception:
                        pass
                return TTBinEvents(time_ps=ts, channel=ch, event_type=et, missed_events=me)
        except Exception:
            pass
    try:
        from TimeTagger import FileReader  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"TimeTagger package not available; cannot read .ttbin: {exc}") from exc

    reader = FileReader(str(p))
    channels: list[np.ndarray] = []
    timestamps: list[np.ndarray] = []
    event_types: list[np.ndarray] = []
    missed: list[np.ndarray] = []

    while reader.hasData():
        data = reader.getData(1_000_000)
        channels.append(np.asarray(data.getChannels(), dtype=np.int64))
        timestamps.append(np.asarray(data.getTimestamps(), dtype=np.int64))
        try:
            event_types.append(np.asarray(data.getEventTypes(), dtype=np.int64))
        except Exception:
            pass
        try:
            missed.append(np.asarray(data.getMissedEvents()))
        except Exception:
            pass

    ch = np.concatenate(channels) if channels else np.empty((0,), dtype=np.int64)
    ts = np.concatenate(timestamps) if timestamps else np.empty((0,), dtype=np.int64)
    et = np.concatenate(event_types) if event_types else None
    me = np.concatenate(missed) if missed else None
    if cache_enabled and cache_dir:
        try:
            st = p.stat()
            key = {
                "ttbin": str(p.resolve()),
                "size": int(st.st_size),
                "mtime_ns": int(getattr(st, "st_mtime_ns", int(st.st_mtime * 1e9))),
                "reader": "ttbin_pipeline",
            }
            h = hashlib.sha256(json.dumps(key, sort_keys=True).encode("utf-8")).hexdigest()[:16]
            cache_base = Path(cache_dir)
            cache_base.mkdir(parents=True, exist_ok=True)
            npz_path = cache_base / f"parsed_{h}.npz"
            meta_path = cache_base / f"parsed_{h}.json"
            if not npz_path.exists():
                t_save0 = time.perf_counter() if timing_enabled else 0.0
                np.savez_compressed(
                    str(npz_path),
                    time_ps=ts,
                    channel=ch,
                    event_type=(et if et is not None else np.empty((0,), dtype=np.int64)),
                    missed_events=(me if me is not None else np.empty((0,), dtype=np.int64)),
                )
                meta_path.write_text(json.dumps({"key": key, "hash": h}, ensure_ascii=False, indent=2), encoding="utf-8")
                if timing_enabled:
                    dt = time.perf_counter() - t_save0
                    try:
                        print(f"TTBIN_CACHE miss hash={h} save_s={dt:.6g} dir={cache_base}", file=sys.__stdout__)
                    except Exception:
                        pass
        except Exception:
            pass
    if timing_enabled:
        dt = time.perf_counter() - t0
        try:
            print(
                f"TTBIN_PARSE call_idx={call_idx} time_s={dt:.6g} reader=ttbin_pipeline ttbin={p}",
                file=sys.__stdout__,
            )
        except Exception:
            pass
    return TTBinEvents(time_ps=ts, channel=ch, event_type=et, missed_events=me)


def _pair_nearest_unique(*, t_a: np.ndarray, t_b: np.ndarray, window_ps: int, offset_ps: int) -> tuple[np.ndarray, np.ndarray]:
    """Greedy monotonic 1-1 pairing within a symmetric time window."""
    if window_ps <= 0:
        return np.empty((0,), dtype=np.int64), np.empty((0,), dtype=np.int64)
    a = np.asarray(t_a, dtype=np.int64) + np.int64(offset_ps)
    b = np.asarray(t_b, dtype=np.int64)
    if a.size == 0 or b.size == 0:
        return np.empty((0,), dtype=np.int64), np.empty((0,), dtype=np.int64)

    a = np.sort(a)
    b = np.sort(b)
    i = 0
    j = 0
    paired_a: list[int] = []
    paired_b: list[int] = []
    w = np.int64(window_ps)
    while i < a.size and j < b.size:
        da = a[i]
        db = b[j]
        dt = da - db
        if dt < -w:
            i += 1
            continue
        if dt > w:
            j += 1
            continue
        paired_a.append(int(da))
        paired_b.append(int(db))
        i += 1
        j += 1
    return np.asarray(paired_a, dtype=np.int64), np.asarray(paired_b, dtype=np.int64)


def _frame_global(*, t_ps: np.ndarray, bin_width_ps: int, frame_bins: int, t0_ps: int) -> tuple[np.ndarray, np.ndarray]:
    rel = np.asarray(t_ps, dtype=np.int64) - np.int64(t0_ps)
    rel = np.maximum(rel, 0)
    bin_idx = np.floor_divide(rel, np.int64(bin_width_ps)).astype(np.int64)
    frame_idx = np.floor_divide(bin_idx, np.int64(frame_bins)).astype(np.int64)
    sym = np.mod(bin_idx, np.int64(frame_bins)).astype(np.int64)
    return frame_idx, sym


def _frame_sync(
    *,
    t_ps: np.ndarray,
    sync_ps: np.ndarray,
    bin_width_ps: int,
    frame_bins: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Frame relative to the most recent sync timestamp."""
    if sync_ps.size == 0:
        # Fallback to global framing using min timestamp.
        t0 = int(np.min(t_ps)) if t_ps.size else 0
        return _frame_global(t_ps=t_ps, bin_width_ps=bin_width_ps, frame_bins=frame_bins, t0_ps=t0)

    t = np.asarray(t_ps, dtype=np.int64)
    sync = np.sort(np.asarray(sync_ps, dtype=np.int64))
    # idx = index of rightmost sync <= t
    idx = np.searchsorted(sync, t, side="right") - 1
    valid = idx >= 0
    frame_idx = np.full(t.shape, -1, dtype=np.int64)
    sym = np.full(t.shape, -1, dtype=np.int64)
    if not np.any(valid):
        return frame_idx, sym
    t_rel = t[valid] - sync[idx[valid]]
    t_rel = np.maximum(t_rel, 0)
    bin_idx = np.floor_divide(t_rel, np.int64(bin_width_ps)).astype(np.int64)
    sym_valid = np.mod(bin_idx, np.int64(frame_bins)).astype(np.int64)
    frame_idx[valid] = idx[valid].astype(np.int64)
    sym[valid] = sym_valid
    return frame_idx, sym


def compute_ttbin_metrics(*, events: TTBinEvents, cfg: dict[str, Any]) -> dict[str, Any]:
    """Compute step-1 intermediate metrics from ttbin events and config."""
    channels_cfg = (cfg.get("channels") if isinstance(cfg.get("channels"), dict) else {}) or {}
    ch_a = _as_int(channels_cfg.get("A"))
    ch_b = _as_int(channels_cfg.get("B"))
    ch_sync = channels_cfg.get("sync")
    ch_sync_i = _as_int(ch_sync) if ch_sync not in (None, "", "null") else None
    if ch_a is None or ch_b is None:
        raise ValueError("ttbin.channels.A and ttbin.channels.B are required")

    pairing_cfg = (cfg.get("pairing") if isinstance(cfg.get("pairing"), dict) else {}) or {}
    window_ps = _as_int(pairing_cfg.get("coin_window_ps"), default=0) or 0
    offset_ps = _as_int(pairing_cfg.get("offset_ps"), default=0) or 0
    policy = str(pairing_cfg.get("policy") or "nearest_unique")
    if policy != "nearest_unique":
        raise ValueError(f"unsupported pairing.policy: {policy} (supported: nearest_unique)")

    framing_cfg = (cfg.get("framing") if isinstance(cfg.get("framing"), dict) else {}) or {}
    bin_width_ps = _as_int(framing_cfg.get("bin_width_ps"), default=None)
    frame_bins = _as_int(framing_cfg.get("frame_bins"), default=None)
    align = str(framing_cfg.get("align") or "global")
    postselect = str(framing_cfg.get("postselect") or "keep_all")
    if bin_width_ps is None or frame_bins is None:
        raise ValueError("ttbin.framing.bin_width_ps and ttbin.framing.frame_bins are required")
    if bin_width_ps <= 0 or frame_bins <= 1:
        raise ValueError("invalid framing parameters")
    if align not in ("global", "sync"):
        raise ValueError("ttbin.framing.align must be 'global' or 'sync'")
    if postselect not in ("1click_each", "keep_all"):
        raise ValueError("ttbin.framing.postselect must be '1click_each' or 'keep_all'")

    # Event selection: TimeTagger event types: 0=TimeTag. If not present, assume all are time tags.
    if events.event_type is not None:
        valid = np.asarray(events.event_type, dtype=np.int64) == 0
    else:
        valid = np.ones(events.time_ps.shape, dtype=bool)

    time_ps = np.asarray(events.time_ps, dtype=np.int64)
    channel = np.asarray(events.channel, dtype=np.int64)

    t_a = time_ps[valid & (channel == ch_a)]
    t_b = time_ps[valid & (channel == ch_b)]
    sync_ps = time_ps[valid & (channel == ch_sync_i)] if ch_sync_i is not None else np.empty((0,), dtype=np.int64)

    tmin = int(np.min(time_ps)) if time_ps.size else 0
    tmax = int(np.max(time_ps)) if time_ps.size else 0
    t_span = int(max(0, tmax - tmin))
    t_acq_s = float(t_span) * 1e-12

    paired_a, paired_b = _pair_nearest_unique(t_a=t_a, t_b=t_b, window_ps=window_ps, offset_ps=offset_ps)
    total_pairs = int(paired_a.size)
    coincidence_rate_hz = (total_pairs / t_acq_s) if t_acq_s > 0 else None

    # Δt stats after offset applied to A
    dt_ps = (paired_a - paired_b).astype(np.int64) if total_pairs else np.empty((0,), dtype=np.int64)
    dt_mean = float(np.mean(dt_ps)) if dt_ps.size else None
    dt_var = float(np.var(dt_ps)) if dt_ps.size else None
    dt_m4 = float(np.mean(dt_ps.astype(np.float64) ** 4)) if dt_ps.size else None

    # Frame/symbol mapping for paired events.
    if align == "sync":
        frame_a, sym_a = _frame_sync(t_ps=paired_a, sync_ps=sync_ps, bin_width_ps=bin_width_ps, frame_bins=frame_bins)
        frame_b, sym_b = _frame_sync(t_ps=paired_b, sync_ps=sync_ps, bin_width_ps=bin_width_ps, frame_bins=frame_bins)
    else:
        frame_a, sym_a = _frame_global(t_ps=paired_a, bin_width_ps=bin_width_ps, frame_bins=frame_bins, t0_ps=tmin)
        frame_b, sym_b = _frame_global(t_ps=paired_b, bin_width_ps=bin_width_ps, frame_bins=frame_bins, t0_ps=tmin)

    # Keep only pairs with valid frame indices and consistent framing.
    valid_pairs = (frame_a >= 0) & (frame_b >= 0) & (frame_a == frame_b) & (sym_a >= 0) & (sym_b >= 0)
    frame = frame_a[valid_pairs]
    sym_a = sym_a[valid_pairs]
    sym_b = sym_b[valid_pairs]

    if postselect == "1click_each" and frame.size:
        # Keep frames with exactly one pair.
        unique_frames, counts = np.unique(frame, return_counts=True)
        ok_frames = set(int(f) for f, c in zip(unique_frames, counts) if int(c) == 1)
        keep = np.asarray([int(f) in ok_frames for f in frame], dtype=bool)
        frame = frame[keep]
        sym_a = sym_a[keep]
        sym_b = sym_b[keep]

    n_symbols = int(frame.size)
    if n_symbols:
        correct = int(np.sum(sym_a == sym_b))
        qber = 1.0 - (correct / n_symbols)
    else:
        qber = None

    # Joint distribution (sparse)
    joint_sparse: list[dict[str, int]] = []
    i_ab = None
    if n_symbols:
        idx = sym_a * np.int64(frame_bins) + sym_b
        keys, counts = np.unique(idx, return_counts=True)
        for k, c in zip(keys.tolist(), counts.tolist()):
            i = int(k // frame_bins)
            j = int(k % frame_bins)
            joint_sparse.append({"i": i, "j": j, "count": int(c)})

        # Mutual information
        p = np.asarray(counts, dtype=np.float64) / float(n_symbols)
        pi = np.zeros((frame_bins,), dtype=np.float64)
        pj = np.zeros((frame_bins,), dtype=np.float64)
        for entry, prob in zip(joint_sparse, p.tolist()):
            pi[entry["i"]] += prob
            pj[entry["j"]] += prob
        mi = 0.0
        for entry, prob in zip(joint_sparse, p.tolist()):
            denom = pi[entry["i"]] * pj[entry["j"]]
            if prob > 0 and denom > 0:
                mi += prob * _safe_log2(prob / denom)
        i_ab = float(mi)

    delta_counts, delta_prob = compute_delta_distribution_from_joint_sparse(
        joint_counts_sparse=joint_sparse,
        dimension=int(frame_bins),
        with_prob=True,
    )

    # Visibility from segments (optional)
    segments = cfg.get("segments")
    visibility = None
    segment_counts: list[dict[str, Any]] = []
    if isinstance(segments, list) and segments and total_pairs:
        # Use paired A timestamps as segment coordinate.
        for seg in segments:
            if not isinstance(seg, dict):
                continue
            start_ps = _as_int(seg.get("start_ps"))
            end_ps = _as_int(seg.get("end_ps"))
            label = seg.get("phi_label")
            if start_ps is None or end_ps is None:
                continue
            mask = (paired_a >= start_ps) & (paired_a < end_ps)
            cnt = int(np.sum(mask))
            segment_counts.append({"start_ps": start_ps, "end_ps": end_ps, "phi_label": label, "coincidences": cnt})
        if segment_counts:
            vals = [int(s["coincidences"]) for s in segment_counts]
            cmax = max(vals)
            cmin = min(vals)
            denom = cmax + cmin
            visibility = ((cmax - cmin) / denom) if denom > 0 else None

    return {
        "ttbin": {
            "channels": {"A": ch_a, "B": ch_b, "sync": ch_sync_i},
            "pairing": {"coin_window_ps": window_ps, "offset_ps": offset_ps, "policy": policy},
            "framing": {"bin_width_ps": bin_width_ps, "frame_bins": frame_bins, "align": align, "postselect": postselect},
        },
        "events_summary": {
            "total_events": int(time_ps.size),
            "valid_events": int(np.sum(valid)),
            "missed_events_total": int(np.sum(events.missed_events)) if events.missed_events is not None else None,
            "timetag_units": "ps",
            "timetag_min": tmin,
            "timetag_max": tmax,
            "timetag_span": t_span,
            "acquisition_duration_s": t_acq_s,
        },
        "singles": {
            "count_A": int(t_a.size),
            "count_B": int(t_b.size),
            "rate_A_hz": (float(t_a.size) / t_acq_s) if t_acq_s > 0 else None,
            "rate_B_hz": (float(t_b.size) / t_acq_s) if t_acq_s > 0 else None,
        },
        "coincidences": {
            "total_pairs": total_pairs,
            "coincidence_rate_hz": coincidence_rate_hz,
            "delta_t_ps": {"mean": dt_mean, "var": dt_var, "moment4": dt_m4},
        },
        "framed": {
            "n_symbols": n_symbols,
            "qber": qber,
            "mutual_information_bits": i_ab,
            "joint_counts_sparse": joint_sparse,
            "delta_counts": delta_counts.tolist(),
            "delta_prob": delta_prob.tolist() if delta_prob is not None else None,
        },
        "visibility": {
            "segment_counts": segment_counts,
            "visibility": visibility,
        },
    }


def run_ttbin_parse_pipeline(
    *,
    ttbin_file: Path | str,
    output_dir: Path | str,
    ttbin_cfg: dict[str, Any],
    events_override: TTBinEvents | None = None,
) -> Path:
    """End-to-end step1: read .ttbin, compute metrics, and write artifacts into output_dir."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    events = events_override if isinstance(events_override, TTBinEvents) else read_ttbin_events(ttbin_file)
    metrics = compute_ttbin_metrics(events=events, cfg=ttbin_cfg)

    (out / "ttbin_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    # Keep a snapshot of the inputs used for reproducibility.
    (out / "ttbin_config.json").write_text(json.dumps(ttbin_cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "ttbin_source.txt").write_text(str(Path(ttbin_file)), encoding="utf-8")
    return out
