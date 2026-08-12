from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from ..config import load_config
from ..utils.paths import default_output_dir, repo_root


def _out_dir(cfg: dict) -> Path:
    out = Path((cfg.get("global", {}) or {}).get("output_dir") or default_output_dir())
    if not out.is_absolute():
        out = repo_root() / out
    out.mkdir(parents=True, exist_ok=True)
    return out


def _best_by_point(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    sort_cols = ["accepted_frame_fraction", "post_ir_ser", "leak_EC_per_input_bit"]
    work = df.copy()
    work["accepted_frame_fraction"] = pd.to_numeric(work["accepted_frame_fraction"], errors="coerce").fillna(0.0)
    work["post_ir_ser"] = pd.to_numeric(work["post_ir_ser"], errors="coerce").fillna(1e9)
    work["leak_EC_per_input_bit"] = pd.to_numeric(work["leak_EC_per_input_bit"], errors="coerce").fillna(1e9)
    work = work.sort_values(["dataset_id", "dimension", "bin_width_ps", "accepted_frame_fraction", "post_ir_ser", "leak_EC_per_input_bit"], ascending=[True, True, True, False, True, True])
    return work.groupby(["dataset_id", "dimension", "bin_width_ps"], dropna=False).head(1).reset_index(drop=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Build v3 report tables.")
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    cfg = load_config(Path(args.config))
    out_dir = _out_dir(cfg)
    report_dir = out_dir / "report_tables_v3"
    report_dir.mkdir(parents=True, exist_ok=True)

    cascade = pd.read_csv(out_dir / "cascade_param_sweep_results.csv") if (out_dir / "cascade_param_sweep_results.csv").exists() else pd.DataFrame()
    layered = pd.read_csv(out_dir / "layered_ldpc_param_sweep_results.csv") if (out_dir / "layered_ldpc_param_sweep_results.csv").exists() else pd.DataFrame()
    qldpc = pd.read_csv(out_dir / "qldpc_param_sweep_results.csv") if (out_dir / "qldpc_param_sweep_results.csv").exists() else pd.DataFrame()

    cascade_best = _best_by_point(cascade)
    layered_best = _best_by_point(layered)
    qldpc_best = _best_by_point(qldpc)
    cascade_best.to_csv(report_dir / "cascade_best_by_point.csv", index=False)
    layered_best.to_csv(report_dir / "layered_ldpc_best_by_point.csv", index=False)
    qldpc_best.to_csv(report_dir / "qldpc_best_by_point.csv", index=False)

    compare = pd.concat([cascade_best, layered_best, qldpc_best], ignore_index=True, sort=False)
    compare.to_csv(report_dir / "method_best_comparison_by_point.csv", index=False)

    failure_rows = []
    for name, df in [("cascade_lite", cascade), ("layered_ldpc_lite", layered), ("qldpc_reference", qldpc)]:
        if df.empty:
            continue
        bad = df[df["method_status"].astype(str) != "ok"].copy()
        if bad.empty:
            continue
        grp = bad.groupby(["method", "dimension", "bin_width_ps"], dropna=False).agg(
            raw_ser_mean=("raw_ser", "mean"),
            failure_count=("dataset_id", "count"),
            failure_reason_top=("method_status", lambda s: s.astype(str).value_counts().index[0]),
        ).reset_index()
        failure_rows.append(grp)
    failure_summary = pd.concat(failure_rows, ignore_index=True) if failure_rows else pd.DataFrame(columns=["method", "dimension", "bin_width_ps", "raw_ser_mean", "failure_count", "failure_reason_top"])
    failure_summary.to_csv(report_dir / "failure_region_summary.csv", index=False)

    leak_rows = []
    for df, method in [(cascade, "cascade_lite"), (layered, "layered_ldpc_lite"), (qldpc, "qldpc_reference")]:
        if df.empty:
            continue
        cols = [c for c in ["dataset_id", "dimension", "bin_width_ps", "leak_EC_actual_bits", "leak_EC_per_input_bit", "notes"] if c in df.columns]
        tmp = df[cols].copy()
        tmp["method"] = method
        leak_rows.append(tmp)
    leakage_summary = pd.concat(leak_rows, ignore_index=True) if leak_rows else pd.DataFrame()
    leakage_summary.to_csv(report_dir / "leakage_decomposition_summary.csv", index=False)

    reps = {(8, 180), (64, 120), (256, 100), (1024, 20), (1024, 120), (4096, 20)}
    if not compare.empty:
        rep_mask = compare.apply(
            lambda r: pd.notna(r.get("dimension")) and pd.notna(r.get("bin_width_ps")) and (int(r["dimension"]), int(r["bin_width_ps"])) in reps,
            axis=1,
        )
        rep_rows = compare[rep_mask].copy()
    else:
        rep_rows = pd.DataFrame()
    rep_rows.to_csv(report_dir / "representative_points_for_group_meeting.csv", index=False)
    print(f"wrote report tables: {report_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
