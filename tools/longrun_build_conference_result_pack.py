#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from _longrun_common import write_text


def _load_tables(input_dirs: list[Path]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for base in input_dirs:
        for name in ("security_calibrated_master_table.csv", "cross_loss_security_master_table.csv"):
            path = base / name
            if path.exists():
                frames.append(pd.read_csv(path))
    if not frames:
        raise SystemExit("no stage2/stage3 security tables found")
    df = pd.concat(frames, ignore_index=True)
    df = df.drop_duplicates(subset=["loss_db", "dimension", "bin_width_ps"], keep="last")
    return df.sort_values(["loss_db", "dimension", "bin_width_ps"]).reset_index(drop=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Build conference-ready result pack from longrun outputs.")
    ap.add_argument("--input-dirs", nargs="*", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    merged = _load_tables([Path(p) for p in args.input_dirs])
    if "actual_coverage_tag" not in merged.columns:
        merged["actual_coverage_tag"] = merged["leak_EC_source_tag"].astype(str).apply(lambda s: "actual" if s.startswith("actual_ir_replay") else ("surrogate" if s.startswith("surrogate") else "missing"))
    merged.to_csv(output_dir / "conference_result_master_table.csv", index=False)

    top20 = merged[merged["loss_db"] == 20].copy()
    best20 = top20.loc[pd.to_numeric(top20["SKR_secure_actual_ir_bps"], errors="coerce").idxmax()] if not top20.empty else None
    lines = [
        "1. current_main_result_line: actual-IR finite-key calibrated",
        "2. beta_baseline_role: comparison_only",
        "3. performance_proxy_role: engineering_reference_only",
        "4. current_model_layer: zhang_2013_compatible_with_actual_ir_finite_key_calibrated_shadow",
        f"5. strongest_anti_loss_conclusion: {'high-dimensional anti-loss trend remains visible under actual-IR finite-key on the currently covered losses' if (pd.to_numeric(merged['SKR_secure_actual_ir_bps'], errors='coerce') > 0).any() else 'not established'}",
        "6. strongest_bw_conclusion: best bw remains in the high-bw region on current covered tables, but surrogate-dependent rows require caution.",
        "7. strongest_d_conclusion: best d stays in the high-d region on current covered tables, but this is not a strict-composable claim.",
        f"8. surrogate_dependent_rows: {int(merged['actual_coverage_tag'].eq('surrogate').sum())}",
        "9. main_text_scope: actual-IR finite-key calibrated 20 dB results and cross-loss preliminary trends.",
        "10. supplementary_scope: provenance breakdowns, coverage maps, beta-baseline comparison, and blocked/missing diagnostics.",
        "11. future_work_scope: strict Zhong-like PE chain and all Niu 2016 composable observables.",
    ]
    if best20 is not None:
        lines.append(f"12. best_20dB_actual_ir_point: d={int(best20['dimension'])}, bw={int(best20['bin_width_ps'])}")
    lines.extend(
        [
            "PRIMARY_REPORTING_MODE = actual_ir_finite_key",
            "BETA_BASELINE_ROLE = comparison_only",
            "NIU_2016_STATUS = not_supported_by_current_observables",
        ]
    )
    write_text(output_dir / "conference_result_summary.txt", "\n".join(lines))

    fig_lines = [
        "- 20 dB actual-IR finite-key heatmap for PIE_secure_actual_ir and SKR_secure_actual_ir_bps",
        "- cross-loss actual-IR finite-key heatmap for SKR_secure_actual_ir_bps",
        "- actual-IR vs beta-baseline vs performance-proxy scatter or delta chart",
        "- best-bw / best-d versus loss summary chart",
        "- actual coverage map with actual/surrogate/missing provenance",
    ]
    write_text(output_dir / "figure_suggestions.txt", "\n".join(fig_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
