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
import subprocess
import sys
from pathlib import Path
from typing import Any

import math
import pandas as pd

from _security_round_common import (
    REPO_ROOT,
    candidate_sidecar_root,
    ensure_output_dir,
    infer_loss_db_from_path,
    load_candidate_bundle,
    point_id,
    safe_json,
    safe_load_npy,
    write_summary,
)

REQUIRED_LAYER_COLS = [
    "decoder_mode_best",
    "k_best",
    "rate_best",
    "crc_bits",
    "frozen_count_best",
    "layer_block_symbols",
]


def _default_input_dirs() -> list[Path]:
    return [REPO_ROOT / "results" / "e2e_20dB_fullgrid_pairing_v2_candidate_t15"]


def _parse_int_list(spec: str | None) -> set[int]:
    out: set[int] = set()
    if not spec:
        return out
    for tok in str(spec).split(","):
        t = tok.strip()
        if not t:
            continue
        out.add(int(t))
    return out


def _has_replay_cols(layer_df: pd.DataFrame) -> bool:
    return all(col in layer_df.columns for col in REQUIRED_LAYER_COLS)


def _safe_int(v: Any) -> int:
    try:
        fv = float(v)
    except Exception:
        return 0
    if not math.isfinite(fv):
        return 0
    return int(fv)


def _rerun_layer_metrics(
    candidate_dir: Path,
    out_dir: Path,
    *,
    jobs: int,
    frames: int,
    seed: int,
    dims_filter: set[int],
    bws_filter: set[int],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Path]:
    tmp_out = out_dir / "_recomputed_replay_inputs" / candidate_dir.name / "polar_e2e_results.csv"
    tmp_out.parent.mkdir(parents=True, exist_ok=True)
    only_points = ""
    if dims_filter and bws_filter:
        pts = []
        for d in sorted(dims_filter):
            for bw in sorted(bws_filter):
                pts.append(f"{d},{bw}")
        only_points = ";".join(pts)
    cmd = [
        sys.executable,
        str(REPO_ROOT / "experiments" / "run_real_polar_max_pie.py"),
        "--grid-table",
        str(candidate_dir / "_tmp_grid_table.csv"),
        "--in-csv",
        str(candidate_dir / "_tmp_src_table.csv"),
        "--out-csv",
        str(tmp_out),
        "--jobs",
        str(int(jobs)),
        "--frames",
        str(int(frames)),
        "--seed",
        str(int(seed)),
        "--prefer-sidecar-map-ser",
    ]
    if only_points:
        cmd.extend(["--only-points", only_points])
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT))
    if proc.returncode != 0:
        raise SystemExit(f"run_real_polar_max_pie.py failed for replay index regeneration: rc={proc.returncode}")
    main = pd.read_csv(tmp_out)
    diag = pd.read_csv(tmp_out.parent / "polar_diag_summary.csv")
    layer = pd.read_csv(tmp_out.parent / "polar_layer_metrics.csv")
    return main, diag, layer, tmp_out.parent


def _build_tables(
    candidate_dir: Path,
    output_dir: Path,
    *,
    jobs: int,
    frames: int,
    seed: int,
    recompute_layer_metrics: bool,
    dims_filter: set[int],
    bws_filter: set[int],
) -> tuple[pd.DataFrame, pd.DataFrame, Path, list[str]]:
    main, diag, layer = load_candidate_bundle(candidate_dir)
    if dims_filter:
        main = main[pd.to_numeric(main["dimension"], errors="coerce").isin(sorted(dims_filter))].copy()
        diag = diag[pd.to_numeric(diag["dimension"], errors="coerce").isin(sorted(dims_filter))].copy()
        layer = layer[pd.to_numeric(layer["dimension"], errors="coerce").isin(sorted(dims_filter))].copy()
    if bws_filter:
        main = main[pd.to_numeric(main["bin_width_ps"], errors="coerce").isin(sorted(bws_filter))].copy()
        diag = diag[pd.to_numeric(diag["bin_width_ps"], errors="coerce").isin(sorted(bws_filter))].copy()
        layer = layer[pd.to_numeric(layer["bin_width_ps"], errors="coerce").isin(sorted(bws_filter))].copy()
    source_root = candidate_dir
    notes: list[str] = []
    if recompute_layer_metrics or not _has_replay_cols(layer):
        cached_root = output_dir / "_recomputed_replay_inputs" / candidate_dir.name
        cached_layer = cached_root / "polar_layer_metrics.csv"
        if cached_layer.exists() and not recompute_layer_metrics:
            notes.append(f"missing replay layer cols in {candidate_dir / 'polar_layer_metrics.csv'}; reusing cached replay-only layer tables from {cached_root}")
            main = pd.read_csv(cached_root / "polar_e2e_results.csv")
            diag = pd.read_csv(cached_root / "polar_diag_summary.csv")
            layer = pd.read_csv(cached_layer)
            source_root = cached_root
        else:
            reason = "paper-grade forced recomputation" if recompute_layer_metrics else "missing replay layer cols"
            notes.append(f"{reason}; regenerated replay-only layer tables via run_real_polar_max_pie.py")
            main, diag, layer, source_root = _rerun_layer_metrics(
                candidate_dir,
                output_dir,
                jobs=jobs,
                frames=frames,
                seed=seed,
                dims_filter=dims_filter,
                bws_filter=bws_filter,
            )

    loss_db = infer_loss_db_from_path(candidate_dir)
    diag_key = diag.set_index(["dimension", "bin_width_ps"], drop=False) if not diag.empty else pd.DataFrame()

    point_rows: list[dict[str, Any]] = []
    layer_rows: list[dict[str, Any]] = []
    for _, row in main.iterrows():
        d = int(row["dimension"])
        bw = int(row["bin_width_ps"])
        pid = point_id(loss_db=loss_db, dimension=d, bin_width_ps=bw)
        sidecar_root = candidate_sidecar_root(candidate_dir, d, bw)
        a_path = sidecar_root / "a_eff.npy"
        b_path = sidecar_root / "b_eff.npy"
        meta_path = sidecar_root / "sidecar_meta.json"
        a_eff = safe_load_npy(a_path)
        b_eff = safe_load_npy(b_path)
        a_count = int(a_eff.shape[0]) if a_eff is not None else None
        b_count = int(b_eff.shape[0]) if b_eff is not None else None
        point_layers = layer[(pd.to_numeric(layer["dimension"], errors="coerce") == d) & (pd.to_numeric(layer["bin_width_ps"], errors="coerce") == bw)].copy()

        replay_ready = "yes"
        blocked_reason = ""
        if a_eff is None or b_eff is None:
            replay_ready = "no"
            blocked_reason = "missing_sidecar_arrays"
        elif point_layers.empty:
            replay_ready = "no"
            blocked_reason = "missing_mapping_from_point_to_layer_rows"
        elif not _has_replay_cols(point_layers):
            replay_ready = "no"
            blocked_reason = "missing_per_layer_code_choice_metadata"
        else:
            valid_layer_blocks = pd.to_numeric(point_layers["layer_block_symbols"], errors="coerce").dropna()
            if valid_layer_blocks.empty or int(valid_layer_blocks.iloc[0]) <= 0:
                replay_ready = "no"
                blocked_reason = "ambiguous_block_slicing_rule"

        point_rows.append(
            {
                "loss_db": loss_db,
                "dimension": d,
                "bin_width_ps": bw,
                "point_id": pid,
                "a_eff_source_path": str(a_path) if a_path.exists() else "MISSING",
                "b_eff_source_path": str(b_path) if b_path.exists() else "MISSING",
                "a_eff_count": a_count if a_count is not None else "MISSING",
                "b_eff_count": b_count if b_count is not None else "MISSING",
                "layer_metrics_source_path": str(source_root / "polar_layer_metrics.csv"),
                "sidecar_source_path": str(meta_path) if meta_path.exists() else "MISSING",
                "replay_ready_tag": replay_ready,
                "replay_block_rule_tag": "fixed_blocks_drop_tail" if replay_ready == "yes" else blocked_reason,
            }
        )

        for _, lrow in point_layers.iterrows():
            layer_ready = "yes" if replay_ready == "yes" else "no"
            decoder_mode = str(lrow.get("decoder_mode_best") or "").strip()
            k_best = _safe_int(lrow.get("k_best", 0))
            block_symbols = _safe_int(lrow.get("layer_block_symbols", 0))
            rescue_success = _safe_int(lrow.get("rescue_success", 0))
            if rescue_success != 1 or not decoder_mode or k_best <= 0 or block_symbols <= 0:
                layer_ready = "no"
            layer_rows.append(
                {
                    "loss_db": loss_db,
                    "dimension": d,
                    "bin_width_ps": bw,
                    "point_id": pid,
                    "layer_id": _safe_int(lrow["layer_idx"]),
                    "decoder_mode_best": decoder_mode or "MISSING",
                    "k_best": k_best if k_best > 0 else "MISSING",
                    "rate_best": lrow.get("rate_best", "MISSING"),
                    "crc_bits": lrow.get("crc_bits", "MISSING"),
                    "frozen_count_best": lrow.get("frozen_count_best", "MISSING"),
                    "layer_block_symbols": block_symbols if block_symbols > 0 else "MISSING",
                    "layer_replay_ready_tag": layer_ready,
                }
            )

    return pd.DataFrame(point_rows), pd.DataFrame(layer_rows), source_root, notes


def main() -> int:
    ap = argparse.ArgumentParser(description="Build replay-input index from current Polar outputs and sidecars.")
    ap.add_argument("--input-dirs", nargs="*", default=[])
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--jobs", type=int, default=15)
    ap.add_argument("--frames", type=int, default=100)
    ap.add_argument("--seed", type=int, default=20260228)
    ap.add_argument("--recompute-layer-metrics", action="store_true")
    ap.add_argument("--dimensions", default="")
    ap.add_argument("--bin-widths", default="")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    output_dir = Path(args.output_dir)
    if bool(args.overwrite):
        ensure_output_dir(output_dir, overwrite=True)
    else:
        output_dir.mkdir(parents=True, exist_ok=True)
    input_dirs = [Path(p) for p in args.input_dirs] if args.input_dirs else _default_input_dirs()
    dims_filter = _parse_int_list(args.dimensions)
    bws_filter = _parse_int_list(args.bin_widths)

    point_frames: list[pd.DataFrame] = []
    layer_frames: list[pd.DataFrame] = []
    source_roots: list[str] = []
    notes: list[str] = []
    for candidate_dir in input_dirs:
        point_df, layer_df, source_root, local_notes = _build_tables(
            candidate_dir,
            output_dir,
            jobs=int(args.jobs),
            frames=int(args.frames),
            seed=int(args.seed),
            recompute_layer_metrics=bool(args.recompute_layer_metrics),
            dims_filter=dims_filter,
            bws_filter=bws_filter,
        )
        point_frames.append(point_df)
        layer_frames.append(layer_df)
        source_roots.append(str(source_root))
        notes.extend(local_notes)

    point_table = pd.concat(point_frames, ignore_index=True) if point_frames else pd.DataFrame()
    layer_table = pd.concat(layer_frames, ignore_index=True) if layer_frames else pd.DataFrame()
    point_table.to_csv(output_dir / "replay_index_point_table.csv", index=False)
    layer_table.to_csv(output_dir / "replay_index_layer_table.csv", index=False)

    replay_ready_count = int(point_table["replay_ready_tag"].eq("yes").sum()) if not point_table.empty else 0
    blocked_rows = point_table[point_table["replay_ready_tag"] != "yes"] if not point_table.empty else pd.DataFrame()
    blocked_tags = sorted(str(x) for x in blocked_rows["replay_block_rule_tag"].dropna().unique()) if not blocked_rows.empty else []
    summary_lines = [
        "input_dirs:",
        *[f"  - {p}" for p in input_dirs],
        "layer_metrics_source_roots:",
        *[f"  - {p}" for p in source_roots],
        f"point_count: {len(point_table)}",
        f"layer_count: {len(layer_table)}",
        f"dimensions_filter: {sorted(dims_filter) if dims_filter else 'ALL'}",
        f"bin_widths_filter: {sorted(bws_filter) if bws_filter else 'ALL'}",
        f"replay_ready_points: {replay_ready_count}",
        f"replay_blocked_points: {len(point_table) - replay_ready_count}",
        "round1a_notes:",
        *([f"  - {n}" for n in notes] if notes else ["  - none"]),
        "",
        "answers:",
        f"1. replay metadata complete: {'yes' if replay_ready_count == len(point_table) and len(point_table) > 0 else 'partial'}",
        f"2. missing data sources: {', '.join(blocked_tags) if blocked_tags else 'none'}",
        f"3. replay minimum conditions satisfied: {'yes' if replay_ready_count > 0 else 'no'}",
        f"4. blockers: {', '.join(blocked_tags) if blocked_tags else 'none'}",
    ]
    write_summary(output_dir / "round1a_summary.txt", summary_lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

