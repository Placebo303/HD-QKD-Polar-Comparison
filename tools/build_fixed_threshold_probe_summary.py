#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from _diagnostics_common import ensure_output_dir, load_csv, monotonic_increasing, tol_for_values, write_summary


def _find_loss_dirs(root: Path) -> list[Path]:
    return sorted([p for p in root.iterdir() if p.is_dir() and p.name.startswith('loss_')])


def main() -> int:
    ap = argparse.ArgumentParser(description="Summarize fixed-threshold probe outputs.")
    ap.add_argument("--probe-root", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    probe_root = Path(args.probe_root)
    output_dir = Path(args.output_dir)
    ensure_output_dir(output_dir, overwrite=bool(args.overwrite))

    loss_dirs = _find_loss_dirs(probe_root)
    if not loss_dirs:
        raise SystemExit(f"no loss_* directories under {probe_root}")

    slice_rows: list[dict[str, object]] = []
    summary_lines = [
        f"probe_root: {probe_root}",
        f"loss_dirs: {','.join(p.name for p in loss_dirs)}",
        f"n_loss_dirs: {len(loss_dirs)}",
        "",
    ]
    weakened_all: list[str] = []
    still_all: list[str] = []
    stage_counts: dict[str, int] = {}

    for loss_dir in loss_dirs:
        compare_csv = loss_dir / "fixed_threshold_compare_vs_current.csv"
        df = load_csv(compare_csv)
        loss_db = int(df["loss_db"].iloc[0])
        point_count = len(df)
        probe_thresholds = sorted({str(x) for x in pd.to_numeric(df['probe_threshold_ps'], errors='coerce').dropna().astype(int).tolist()})
        summary_lines.extend([
            f"loss_db: {loss_db}",
            f"compare_csv: {compare_csv}",
            f"point_count: {point_count}",
            f"probe_threshold_ps: {','.join(probe_thresholds) if probe_thresholds else '(unknown)'}",
        ])
        dims = sorted(pd.to_numeric(df["dimension"], errors="coerce").dropna().astype(int).unique())
        loss_weakened: list[str] = []
        loss_still: list[str] = []
        for dim in dims:
            sl = df[pd.to_numeric(df["dimension"], errors="coerce") == dim].copy()
            sl["bin_width_ps"] = pd.to_numeric(sl["bin_width_ps"], errors="coerce")
            sl = sl.sort_values("bin_width_ps")
            current_pie = [float(v) for v in pd.to_numeric(sl["current_PIE_practical"], errors="coerce").tolist() if pd.notna(v)]
            probe_pie = [float(v) for v in pd.to_numeric(sl["probe_PIE_practical"], errors="coerce").tolist() if pd.notna(v)]
            current_up = monotonic_increasing(current_pie)
            probe_up = monotonic_increasing(probe_pie)
            if current_up and not probe_up:
                loss_weakened.append(f"d={dim}")
                weakened_all.append(f"loss={loss_db},d={dim}")
            if probe_up:
                loss_still.append(f"d={dim}")
                still_all.append(f"loss={loss_db},d={dim}")
            stage_series = sl["stage_change_tag"].fillna("")
            stage = stage_series.value_counts().index[0] if len(stage_series.value_counts()) else "unchanged"
            stage_counts[str(stage)] = stage_counts.get(str(stage), 0) + 1
            slice_rows.append(
                {
                    "loss_db": int(loss_db),
                    "dimension": int(dim),
                    "current_pie_monotonic_increasing": "yes" if current_up else "no",
                    "probe_pie_monotonic_increasing": "yes" if probe_up else "no",
                    "dominant_stage_change": str(stage),
                }
            )
        n_current_up = int((pd.DataFrame(slice_rows)[pd.DataFrame(slice_rows)['loss_db'] == int(loss_db)]['current_pie_monotonic_increasing'] == 'yes').sum()) if slice_rows else 0
        n_probe_up = int((pd.DataFrame(slice_rows)[pd.DataFrame(slice_rows)['loss_db'] == int(loss_db)]['probe_pie_monotonic_increasing'] == 'yes').sum()) if slice_rows else 0
        summary_lines.extend(
            [
                f"  current_coupled_pie_vs_bw_monotonic_slices: {n_current_up}/{len(dims)}",
                f"  fixed_threshold_pie_vs_bw_monotonic_slices: {n_probe_up}/{len(dims)}",
                f"  decoupling_weakened_dims: {','.join(loss_weakened) if loss_weakened else '(none)'}",
                f"  probe_still_large_bw_better_dims: {','.join(loss_still) if loss_still else '(none)'}",
                "",
            ]
        )

    stage_text = ", ".join(f"{k}={v}" for k, v in sorted(stage_counts.items()))
    total_slices = len(slice_rows)
    total_current_up = sum(1 for r in slice_rows if r['current_pie_monotonic_increasing'] == 'yes')
    total_probe_up = sum(1 for r in slice_rows if r['probe_pie_monotonic_increasing'] == 'yes')
    summary_lines.extend(
        [
            f"total_slice_count: {total_slices}",
            f"current_coupled_monotonic_slice_count: {total_current_up}",
            f"fixed_threshold_monotonic_slice_count: {total_probe_up}",
            f"current_coupled_mode_pie_vs_bw_overall_trend: {'mostly near-monotonic increasing' if total_current_up >= max(1, total_slices - 2) else 'mixed'}",
            f"fixed_threshold_mode_pie_vs_bw_overall_trend: {'mostly near-monotonic increasing' if total_probe_up >= max(1, total_slices - 2) else 'mixed'}",
            f"weakened_loss_dimension_combinations: {','.join(weakened_all) if weakened_all else '(none)'}",
            f"still_large_bw_better_combinations: {','.join(still_all) if still_all else '(none)'}",
            f"dominant_stage_change_counts: {stage_text if stage_text else '(none)'}",
        ]
    )

    pd.DataFrame(slice_rows).to_csv(output_dir / "fixed_threshold_probe_slice_summary.csv", index=False)
    write_summary(output_dir / "fixed_threshold_probe_summary.txt", summary_lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
