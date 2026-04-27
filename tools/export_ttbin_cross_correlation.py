from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qkd_io.ttbin_pipeline import TTBinEvents, read_ttbin_events


def _centered_lag_axis(*, max_lag_ps: int, bin_width_ps: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return bin edges/centers for a lag axis whose centers include zero."""
    n_side = int(math.floor(int(max_lag_ps) / int(bin_width_ps)))
    centers = (np.arange(-n_side, n_side + 1, dtype=np.int64) * np.int64(bin_width_ps)).astype(np.float64)
    half = float(bin_width_ps) / 2.0
    left = centers - half
    right = centers + half
    return left, right, centers


def _select_two_signal_channels(events: TTBinEvents) -> tuple[int, int, dict[str, int]]:
    channel = np.asarray(events.channel, dtype=np.int64)
    if channel.size == 0:
        raise ValueError("ttbin contains no events")
    keys, vals = np.unique(channel, return_counts=True)
    counts = {str(int(k)): int(v) for k, v in zip(keys.tolist(), vals.tolist())}
    signal = [(int(k), int(v)) for k, v in zip(keys.tolist(), vals.tolist()) if int(k) < 1000]
    if len(signal) < 2:
        signal = [(int(k), int(v)) for k, v in zip(keys.tolist(), vals.tolist())]
    signal.sort(key=lambda x: (-x[1], x[0]))
    if len(signal) < 2:
        raise ValueError(f"need at least two channels, found: {counts}")
    return int(signal[0][0]), int(signal[1][0]), counts


def compute_cross_correlation_histogram(
    *,
    events: TTBinEvents,
    ch_a: int,
    ch_b: int,
    bin_width_ps: int,
    max_lag_ps: int,
    center_lag_ps: int = 0,
    chunk_size: int = 100_000,
    time_tag_only: bool = True,
) -> dict[str, Any]:
    """Compute a binned cross-correlation histogram for two ttbin channels.

    Lag convention: raw_lag_ps = t_B - t_A. The output lag axis is centered
    at center_lag_ps, so lag_center_ps=0 means raw_lag_ps=center_lag_ps.
    """
    ch_a = int(ch_a)
    ch_b = int(ch_b)
    bin_width_ps = int(bin_width_ps)
    max_lag_ps = int(max_lag_ps)
    center_lag_ps = int(center_lag_ps)
    chunk_size = int(chunk_size)
    if bin_width_ps <= 0:
        raise ValueError("bin_width_ps must be positive")
    if max_lag_ps <= 0:
        raise ValueError("max_lag_ps must be positive")
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    time_ps = np.asarray(events.time_ps, dtype=np.int64)
    channel = np.asarray(events.channel, dtype=np.int64)
    if time_tag_only and events.event_type is not None:
        valid = np.asarray(events.event_type, dtype=np.int64) == 0
    else:
        valid = np.ones(time_ps.shape, dtype=bool)

    t_a = np.sort(time_ps[valid & (channel == ch_a)])
    t_b = np.sort(time_ps[valid & (channel == ch_b)])

    tmin = int(np.min(time_ps)) if time_ps.size else 0
    tmax = int(np.max(time_ps)) if time_ps.size else 0
    acquisition_duration_s = float(max(0, tmax - tmin)) * 1e-12

    lag_left, lag_right, centers = _centered_lag_axis(max_lag_ps=max_lag_ps, bin_width_ps=bin_width_ps)
    n_side = (centers.size - 1) // 2
    n_bins = int(centers.size)
    counts = np.zeros((n_bins,), dtype=np.int64)

    if t_a.size and t_b.size:
        for start in range(0, int(t_a.size), chunk_size):
            a_chunk = t_a[start : start + chunk_size]
            left = np.searchsorted(t_b, a_chunk + np.int64(center_lag_ps) - np.int64(max_lag_ps), side="left")
            right = np.searchsorted(t_b, a_chunk + np.int64(center_lag_ps) + np.int64(max_lag_ps), side="right")
            for a, lo, hi in zip(a_chunk.tolist(), left.tolist(), right.tolist()):
                if hi <= lo:
                    continue
                lags = (t_b[lo:hi] - np.int64(a) - np.int64(center_lag_ps)).astype(np.float64, copy=False)
                bin_idx = (np.floor((lags + (float(bin_width_ps) / 2.0)) / float(bin_width_ps)) + n_side).astype(
                    np.int64
                )
                bin_idx = bin_idx[(bin_idx >= 0) & (bin_idx < n_bins)]
                if bin_idx.size:
                    counts += np.bincount(bin_idx, minlength=n_bins).astype(np.int64, copy=False)

    raw_centers = centers + float(center_lag_ps)
    return {
        "lag_left_ps": lag_left,
        "lag_right_ps": lag_right,
        "lag_center_ps": centers,
        "raw_lag_center_ps": raw_centers,
        "counts": counts,
        "summary": {
            "channel_A": ch_a,
            "channel_B": ch_b,
            "bin_width_ps": bin_width_ps,
            "max_lag_ps": max_lag_ps,
            "center_lag_ps": center_lag_ps,
            "lag_convention": "t_B_minus_t_A",
            "lag_axis": "zero_centered_bins",
            "count_A": int(t_a.size),
            "count_B": int(t_b.size),
            "total_pairs_in_window": int(np.sum(counts, dtype=np.int64)),
            "acquisition_duration_s": acquisition_duration_s,
            "time_tag_only": bool(time_tag_only),
        },
    }


def estimate_cross_correlation_peak(
    *,
    events: TTBinEvents,
    ch_a: int,
    ch_b: int,
    search_range_ps: int,
    coarse_bin_width_ps: int,
    chunk_size: int,
    time_tag_only: bool,
) -> dict[str, Any]:
    hist = compute_cross_correlation_histogram(
        events=events,
        ch_a=int(ch_a),
        ch_b=int(ch_b),
        bin_width_ps=int(coarse_bin_width_ps),
        max_lag_ps=int(search_range_ps),
        center_lag_ps=0,
        chunk_size=int(chunk_size),
        time_tag_only=bool(time_tag_only),
    )
    counts = np.asarray(hist["counts"], dtype=np.int64)
    if counts.size == 0 or int(np.max(counts)) <= 0:
        return {
            "ok": False,
            "peak_center_ps": 0,
            "peak_count": 0,
            "search_range_ps": int(search_range_ps),
            "coarse_bin_width_ps": int(coarse_bin_width_ps),
        }
    peak_idx = int(np.argmax(counts))
    return {
        "ok": True,
        "peak_center_ps": int(round(float(hist["lag_center_ps"][peak_idx]))),
        "peak_count": int(counts[peak_idx]),
        "search_range_ps": int(search_range_ps),
        "coarse_bin_width_ps": int(coarse_bin_width_ps),
    }


def _write_cross_correlation_csv(path: Path, hist: dict[str, Any]) -> None:
    counts = hist["counts"]
    lag_left = hist["lag_left_ps"]
    lag_right = hist["lag_right_ps"]
    lag_center = hist["lag_center_ps"]
    raw_lag_center = hist["raw_lag_center_ps"]
    duration_s = float(hist.get("summary", {}).get("acquisition_duration_s") or 0.0)

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "lag_center_ps",
                "raw_lag_center_ps",
                "lag_left_ps",
                "lag_right_ps",
                "count",
                "count_rate_hz",
            ],
        )
        w.writeheader()
        for center, raw_center, left, right, count in zip(
            lag_center.tolist(),
            raw_lag_center.tolist(),
            lag_left.tolist(),
            lag_right.tolist(),
            counts.tolist(),
        ):
            c = int(count)
            w.writerow(
                {
                    "lag_center_ps": f"{float(center):.6g}",
                    "raw_lag_center_ps": f"{float(raw_center):.6g}",
                    "lag_left_ps": f"{float(left):.6g}",
                    "lag_right_ps": f"{float(right):.6g}",
                    "count": c,
                    "count_rate_hz": f"{(c / duration_s):.12g}" if duration_s > 0 else "",
                }
            )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Export a ttbin channel cross-correlation histogram as CSV for plotting."
    )
    ap.add_argument("--ttbin", required=True, help="input .ttbin file")
    ap.add_argument("--ch-a", type=int, default=None, help="reference channel A id")
    ap.add_argument("--ch-b", type=int, default=None, help="channel B id; lag is t_B - t_A")
    ap.add_argument("--auto-channels", action="store_true", help="use the two most populated non-sync channels")
    ap.add_argument("--auto-align", action="store_true", help="estimate channel delay first, then center the output histogram on the peak")
    ap.add_argument("--center-lag-ps", type=int, default=0, help="manual raw lag center ps; ignored when --auto-align is set")
    ap.add_argument("--align-search-range-ps", type=int, default=5_000_000, help="coarse auto-align half-width in ps")
    ap.add_argument("--align-bin-width-ps", type=int, default=100, help="coarse auto-align bin width in ps")
    ap.add_argument("--bin-width-ps", type=int, default=10, help="histogram bin width in ps")
    ap.add_argument("--max-lag-ps", type=int, default=10_000, help="half-width of lag scan range in ps")
    ap.add_argument("--chunk-size", type=int, default=100_000, help="number of A timestamps processed per chunk")
    ap.add_argument("--include-non-timetags", action="store_true", help="include non-TimeTag events if event types exist")
    ap.add_argument("--out-csv", required=True, help="output CSV path")
    ap.add_argument("--out-json", default="", help="optional summary JSON path")
    args = ap.parse_args(argv)

    ttbin_path = Path(args.ttbin)
    if not ttbin_path.exists() or ttbin_path.suffix.lower() != ".ttbin":
        raise FileNotFoundError(f"ttbin file not found: {ttbin_path}")

    events = read_ttbin_events(ttbin_path)
    ch_a = args.ch_a
    ch_b = args.ch_b
    channels_available: dict[str, int] = {}
    if bool(args.auto_channels) or ch_a is None or ch_b is None:
        ch_a, ch_b, channels_available = _select_two_signal_channels(events)
    else:
        _, _, channels_available = _select_two_signal_channels(events)

    center_lag_ps = int(args.center_lag_ps)
    peak_info: dict[str, Any] | None = None
    if bool(args.auto_align):
        peak_info = estimate_cross_correlation_peak(
            events=events,
            ch_a=int(ch_a),
            ch_b=int(ch_b),
            search_range_ps=int(args.align_search_range_ps),
            coarse_bin_width_ps=int(args.align_bin_width_ps),
            chunk_size=int(args.chunk_size),
            time_tag_only=not bool(args.include_non_timetags),
        )
        if bool(peak_info.get("ok")):
            center_lag_ps = int(peak_info.get("peak_center_ps") or 0)
            refine_hist = compute_cross_correlation_histogram(
                events=events,
                ch_a=int(ch_a),
                ch_b=int(ch_b),
                bin_width_ps=int(args.bin_width_ps),
                max_lag_ps=int(args.max_lag_ps),
                center_lag_ps=int(center_lag_ps),
                chunk_size=int(args.chunk_size),
                time_tag_only=not bool(args.include_non_timetags),
            )
            refine_counts = np.asarray(refine_hist["counts"], dtype=np.int64)
            if refine_counts.size and int(np.max(refine_counts)) > 0:
                refine_idx = int(np.argmax(refine_counts))
                refine_offset_ps = int(round(float(refine_hist["lag_center_ps"][refine_idx])))
                center_lag_ps += refine_offset_ps
                peak_info["refine_offset_ps"] = refine_offset_ps
                peak_info["refined_peak_center_ps"] = int(center_lag_ps)
                peak_info["refined_peak_count"] = int(refine_counts[refine_idx])

    hist = compute_cross_correlation_histogram(
        events=events,
        ch_a=int(ch_a),
        ch_b=int(ch_b),
        bin_width_ps=int(args.bin_width_ps),
        max_lag_ps=int(args.max_lag_ps),
        center_lag_ps=int(center_lag_ps),
        chunk_size=int(args.chunk_size),
        time_tag_only=not bool(args.include_non_timetags),
    )
    hist["summary"]["channels_available"] = channels_available
    hist["summary"]["auto_channels"] = bool(args.auto_channels or args.ch_a is None or args.ch_b is None)
    hist["summary"]["auto_align"] = bool(args.auto_align)
    hist["summary"]["align_peak"] = peak_info

    out_csv = Path(args.out_csv)
    _write_cross_correlation_csv(out_csv, hist)
    print(f"[CROSS_CORR] out_csv={out_csv}")
    print(f"[CROSS_CORR] summary={json.dumps(hist['summary'], ensure_ascii=False)}")

    if args.out_json:
        out_json = Path(args.out_json)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(hist["summary"], ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[CROSS_CORR] out_json={out_json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
