#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SECURITY_REPORTS = REPO_ROOT / "tools" / "security_reports"
for _p in (REPO_ROOT, SECURITY_REPORTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import argparse
from pathlib import Path

import pandas as pd

from _longrun_common import candidate_dir_for_loss, python_tool, write_text


def _fresh_recomputed_candidate_dir(replay_index_dir: Path, candidate_dir: Path) -> Path:
    """Return the Stage 0 recomputed candidate, refusing the stale source candidate."""
    fresh_candidate_dir = replay_index_dir / "_recomputed_replay_inputs" / candidate_dir.name
    required_csv = fresh_candidate_dir / "polar_e2e_results.csv"
    if not required_csv.is_file():
        raise SystemExit(
            "Stage 0 recomputed candidate is missing required polar_e2e_results.csv: "
            f"{required_csv}"
        )
    return fresh_candidate_dir

def main() -> int:
    ap = argparse.ArgumentParser(description="Run Route A formal correctness rerun across configured losses.")
    ap.add_argument("--losses", default="20,16,10,6")
    ap.add_argument("--output-dir", default="results/paper_grade_v2/four_loss_full")
    ap.add_argument("--shards", type=int, default=121)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--metric-jobs", type=int, default=4)
    ap.add_argument("--frames", type=int, default=100)
    ap.add_argument("--seed", type=int, default=20260228)
    ap.add_argument("--verification-tag-bits", type=int, default=64)
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
        if not candidate_dir.exists():
            archived_candidate = REPO_ROOT / "results" / "authoritative" / candidate_dir.name
            if archived_candidate.exists():
                candidate_dir = archived_candidate
        loss_root = output_dir / f"loss_{int(loss_db)}dB"
        replay_index_dir = loss_root / "stage0_replay_index"
        stage1_dir = loss_root / "stage1_actual_ir"
        stage2_dir = loss_root / "stage2_security"
        stage0_ready = (
            (replay_index_dir / "replay_index_point_table.csv").exists()
            and (replay_index_dir / "replay_index_layer_table.csv").exists()
            and (replay_index_dir / "round1a_summary.txt").exists()
        )
        if bool(args.overwrite) or not stage0_ready:
            python_tool(
                "round1a_build_replay_index.py",
                "--input-dirs",
                str(candidate_dir),
                "--output-dir",
                str(replay_index_dir),
                "--jobs",
                str(int(args.metric_jobs)),
                "--frames",
                str(int(args.frames)),
                "--seed",
                str(int(args.seed)),
                "--recompute-layer-metrics",
                *(["--overwrite"] if bool(args.overwrite) else []),
            )
        fresh_candidate_dir = _fresh_recomputed_candidate_dir(replay_index_dir, candidate_dir)
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
            str(fresh_candidate_dir),
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
        lines.append(
            f"  - loss={int(loss_db)} rows={len(master)} formal_rows={formal_rows} "
            f"stage0_dir={replay_index_dir} fresh_candidate_dir={fresh_candidate_dir} stage2_dir={stage2_dir}"
        )

    merged = pd.concat(masters, ignore_index=True) if masters else pd.DataFrame()
    merged.to_csv(output_dir / "cross_loss_security_master_table.csv", index=False)
    positive_rows = int((pd.to_numeric(merged.get("SKR_secure_actual_ir_bps"), errors="coerce") > 0).sum()) if not merged.empty else 0
    lines.extend(
        [
            f"cross_loss_rows: {len(merged)}",
            f"cross_loss_formal_rows: {int(merged.get('epsilon_EC_bound_formula_tag', pd.Series(dtype=str)).astype(str).eq('union_bound_over_blocks_universal_hash').sum()) if not merged.empty else 0}",
            f"cross_loss_positive_actual_rows: {positive_rows}",
            "claim_boundary: paper-grade reconciliation and correctness evidence; calibrated security shadow is not a composable HD-QKD key-rate proof.",
        ]
    )
    write_text(output_dir / "routeA_formal_cross_loss_summary.txt", "\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

