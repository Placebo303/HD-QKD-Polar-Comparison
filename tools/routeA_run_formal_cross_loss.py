#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from _longrun_common import candidate_dir_for_loss, python_tool, write_text


def _default_replay_index_dir(loss_db: int) -> Path:
    return Path("results") / "_tmp_longrun_fresh_rerun" / f"full_{int(loss_db)}dB" / "stage1_actual_ir"


def main() -> int:
    ap = argparse.ArgumentParser(description="Run Route A formal correctness rerun across configured losses.")
    ap.add_argument("--losses", default="20,16,10,6")
    ap.add_argument("--output-dir", default="results/_tmp_routeA_correctness_formal_stageD_cross_loss")
    ap.add_argument("--shards", type=int, default=121)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--verification-tag-bits", type=int, default=32)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    losses = [int(x.strip()) for x in str(args.losses).split(",") if x.strip()]

    masters: list[pd.DataFrame] = []
    lines = [
        f"output_dir: {output_dir}",
        f"losses: {','.join(str(x) for x in losses)}",
        f"verification_tag_bits: {int(args.verification_tag_bits)}",
        f"workers: {int(args.workers)}",
        "loss_runs:",
    ]
    for loss_db in losses:
        candidate_dir = candidate_dir_for_loss(loss_db)
        replay_index_dir = _default_replay_index_dir(loss_db)
        loss_root = output_dir / f"loss_{int(loss_db)}dB"
        stage1_dir = loss_root / "stage1_actual_ir"
        stage2_dir = loss_root / "stage2_security"
        python_tool(
            "routeA_run_formal_replay_shards.py",
            "--candidate-dir",
            str(candidate_dir),
            "--replay-index-dir",
            str(replay_index_dir),
            "--output-dir",
            str(stage1_dir),
            "--shards",
            str(int(args.shards)),
            "--workers",
            str(int(args.workers)),
            "--verification-tag-bits",
            str(int(args.verification_tag_bits)),
            *(["--overwrite"] if bool(args.overwrite) else []),
        )
        python_tool(
            "routeA_build_formal_stageC.py",
            "--candidate-dir",
            str(candidate_dir),
            "--stage1-dir",
            str(stage1_dir),
            "--output-dir",
            str(stage2_dir),
            "--overwrite",
        )
        master_path = stage2_dir / "security_calibrated_master_table.csv"
        python_tool(
            "routeA_validate_correctness_formal.py",
            "--stage1-dir",
            str(stage1_dir),
            "--master",
            str(master_path),
            "--expected-points",
            "121",
            "--verification-tag-bits",
            str(int(args.verification_tag_bits)),
            "--output-dir",
            str(loss_root / "validation"),
        )
        master = pd.read_csv(master_path)
        master["routeA_formal_loss_dir"] = str(loss_root)
        masters.append(master)
        formal_rows = int(master.get("epsilon_EC_bound_formula_tag", pd.Series(dtype=str)).astype(str).eq("union_bound_over_blocks_universal_hash").sum())
        lines.append(f"  - loss={int(loss_db)} rows={len(master)} formal_rows={formal_rows} stage2_dir={stage2_dir}")

    merged = pd.concat(masters, ignore_index=True) if masters else pd.DataFrame()
    merged.to_csv(output_dir / "cross_loss_security_master_table.csv", index=False)
    positive_rows = int((pd.to_numeric(merged.get("SKR_secure_actual_ir_bps"), errors="coerce") > 0).sum()) if not merged.empty else 0
    lines.extend(
        [
            f"cross_loss_rows: {len(merged)}",
            f"cross_loss_formal_rows: {int(merged.get('epsilon_EC_bound_formula_tag', pd.Series(dtype=str)).astype(str).eq('union_bound_over_blocks_universal_hash').sum()) if not merged.empty else 0}",
            f"cross_loss_positive_actual_rows: {positive_rows}",
            "claim_boundary: correctness-side verification interface formalized; not strict Zhong 2015 or full Niu 2016.",
        ]
    )
    write_text(output_dir / "routeA_formal_cross_loss_summary.txt", "\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
