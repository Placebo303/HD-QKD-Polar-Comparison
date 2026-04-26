from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qkd_io.ttbin_pipeline import compute_cross_correlation_histogram, read_ttbin_events


def _write_cross_correlation_csv(path: Path, hist: dict[str, Any]) -> None:
    counts = hist["counts"]
    lag_left = hist["lag_left_ps"]
    lag_right = hist["lag_right_ps"]
    lag_center = hist["lag_center_ps"]
    duration_s = float(hist.get("summary", {}).get("acquisition_duration_s") or 0.0)

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "lag_center_ps",
                "lag_left_ps",
                "lag_right_ps",
                "count",
                "count_rate_hz",
            ],
        )
        w.writeheader()
        for center, left, right, count in zip(lag_center.tolist(), lag_left.tolist(), lag_right.tolist(), counts.tolist()):
            c = int(count)
            w.writerow(
                {
                    "lag_center_ps": f"{float(center):.6g}",
                    "lag_left_ps": int(left),
                    "lag_right_ps": int(right),
                    "count": c,
                    "count_rate_hz": f"{(c / duration_s):.12g}" if duration_s > 0 else "",
                }
            )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Export a ttbin channel cross-correlation histogram as CSV for plotting."
    )
    ap.add_argument("--ttbin", required=True, help="input .ttbin file")
    ap.add_argument("--ch-a", type=int, required=True, help="reference channel A id")
    ap.add_argument("--ch-b", type=int, required=True, help="channel B id; lag is t_B - t_A")
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
    hist = compute_cross_correlation_histogram(
        events=events,
        ch_a=int(args.ch_a),
        ch_b=int(args.ch_b),
        bin_width_ps=int(args.bin_width_ps),
        max_lag_ps=int(args.max_lag_ps),
        chunk_size=int(args.chunk_size),
        time_tag_only=not bool(args.include_non_timetags),
    )

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
