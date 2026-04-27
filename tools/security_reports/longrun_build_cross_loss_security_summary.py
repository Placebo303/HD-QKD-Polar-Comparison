#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from _longrun_common import write_text


def _load_tables(input_dirs: list[Path]) -> list[pd.DataFrame]:
    frames: list[pd.DataFrame] = []
    for base in input_dirs:
        direct = base / "security_calibrated_master_table.csv"
        cross = base / "cross_loss_security_master_table.csv"
        if direct.exists():
            frames.append(pd.read_csv(direct))
        if cross.exists():
            frames.append(pd.read_csv(cross))
        for nested in sorted(base.glob("loss_*dB/stage2_security/security_calibrated_master_table.csv")):
            frames.append(pd.read_csv(nested))
    return frames


def main() -> int:
    ap = argparse.ArgumentParser(description="Build cross-loss actual-IR security summary.")
    ap.add_argument("--input-dirs", nargs="*", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    frames = _load_tables([Path(p) for p in args.input_dirs])
    if not frames:
        raise SystemExit("no security tables found in --input-dirs")
    merged = pd.concat(frames, ignore_index=True)
    merged = merged.drop_duplicates(subset=["loss_db", "dimension", "bin_width_ps"], keep="last")
    if "actual_coverage_tag" not in merged.columns:
        merged["actual_coverage_tag"] = merged["leak_EC_source_tag"].astype(str).apply(lambda s: "actual" if s.startswith("actual_ir_replay") else ("surrogate" if s.startswith("surrogate") else "missing"))
    merged = merged.sort_values(["loss_db", "dimension", "bin_width_ps"]).reset_index(drop=True)
    merged.to_csv(output_dir / "cross_loss_security_master_table.csv", index=False)

    lines = ["actual_coverage_by_loss:"]
    for loss_db, grp in merged.groupby("loss_db"):
        total = len(grp)
        actual = int(grp["actual_coverage_tag"].eq("actual").sum())
        surrogate = int(grp["actual_coverage_tag"].eq("surrogate").sum())
        best = grp.loc[pd.to_numeric(grp["SKR_secure_actual_ir_bps"], errors="coerce").idxmax()]
        lines.append(
            f"- loss={int(loss_db)} actual={actual}/{total} surrogate={surrogate}/{total} best_point=(d={int(best['dimension'])},bw={int(best['bin_width_ps'])})"
        )
    top = merged.sort_values("SKR_secure_actual_ir_bps", ascending=False).head(12)
    high_dim_losses = sorted(top["loss_db"].dropna().astype(int).unique().tolist())
    lines.extend(
        [
            f"cross_loss_positive_actual_rows: {int((pd.to_numeric(merged['SKR_secure_actual_ir_bps'], errors='coerce') > 0).sum())}",
            f"high_dim_anti_loss_still_visible: {'yes' if any(int(x) in high_dim_losses for x in [16, 20]) else 'partial'}",
            "preliminary_note: losses with low actual coverage should remain preliminary in paper text.",
        ]
    )
    write_text(output_dir / "cross_loss_security_summary.txt", "\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
