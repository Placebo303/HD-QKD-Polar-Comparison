"""Consolidate existing real_ir_success_first outputs into an evidence package.

Reads existing sweep results (no new sweeps) and produces consolidated CSVs
and a manifest under expanded_real_ir_20260615/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import warnings
from pathlib import Path
from typing import Any

import pandas as pd


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def compute_file_hash(path: Path) -> str:
    """Return SHA-256 hex digest of *path*."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def get_git_commit() -> str:
    """Return short HEAD hash, or ``'unknown'`` if not a git repo."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def load_csv(input_dir: Path, filename: str) -> pd.DataFrame | None:
    """Load *filename* from *input_dir*, returning ``None`` if missing."""
    path = input_dir / filename
    if not path.exists():
        warnings.warn(f"Source file not found, skipping: {path}")
        return None
    return pd.read_csv(path)


# ---------------------------------------------------------------------------
# Output generators
# ---------------------------------------------------------------------------

def make_cascade_optimized(df: pd.DataFrame) -> pd.DataFrame:
    """Select minimum leak_EC_actual_bits per dataset_id (real_ir_success only)."""
    ok = df[df["real_ir_success"] == True].copy()  # noqa: E712
    if ok.empty:
        return pd.DataFrame(columns=df.columns)
    idx = ok.groupby("dataset_id")["leak_EC_actual_bits"].idxmin()
    return ok.loc[idx].reset_index(drop=True)


def make_ldpc_optimized(df: pd.DataFrame) -> pd.DataFrame:
    """Select minimum leak_EC_actual_bits per dataset_id (real_ir_success only)."""
    ok = df[df["real_ir_success"] == True].copy()  # noqa: E712
    if ok.empty:
        return pd.DataFrame(columns=df.columns)
    idx = ok.groupby("dataset_id")["leak_EC_actual_bits"].idxmin()
    return ok.loc[idx].reset_index(drop=True)


def make_qldpc_reference(df: pd.DataFrame) -> pd.DataFrame:
    """Select max n_frames_success per (dataset_id, q, frame_len_symbols).

    Preserves success_classification from source.
    """
    if df.empty:
        return pd.DataFrame(columns=df.columns)
    idx = df.groupby(["dataset_id", "q", "frame_len_symbols"])["n_frames_success"].idxmax()
    return df.loc[idx].reset_index(drop=True)


def make_scalability_summary(
    real_df: pd.DataFrame | None,
    synth_df: pd.DataFrame | None,
) -> pd.DataFrame:
    """Concat real and synthetic scalability data, deduplicate by dataset_id."""
    parts = [d for d in (real_df, synth_df) if d is not None]
    if not parts:
        return pd.DataFrame()
    combined = pd.concat(parts, ignore_index=True)
    combined = combined.drop_duplicates(subset="dataset_id", keep="first")
    cols = [
        "dataset_id", "data_mode", "dimension", "bin_width_ps",
        "frame_len_symbols", "method", "real_ir_success",
        "success_classification", "leak_EC_actual_bits", "runtime_s",
    ]
    present = [c for c in cols if c in combined.columns]
    return combined[present].reset_index(drop=True)


def make_method_comparison(
    cascade_df: pd.DataFrame | None,
    ldpc_df: pd.DataFrame | None,
    scalability_df: pd.DataFrame | None,
) -> pd.DataFrame:
    """Group by ``frame_len_symbols``; count successes and average metrics.

    Only data that carries a genuine ``frame_len_symbols`` column is included.
    Sweep CSVs (cascade, LDPC) lack this column — they are excluded because
    their ``frame_cap`` (= number of frames per batch) is not a frame length
    and would be misleading if labelled as such.
    """
    rows: list[dict[str, Any]] = []
    for label, src in [
        ("cascade_lite", cascade_df),
        ("layered_ldpc_lite", ldpc_df),
    ]:
        if src is None or src.empty:
            continue
        if "frame_len_symbols" not in src.columns:
            continue  # sweep CSVs lack this column — skip
        ok = src[src["real_ir_success"] == True].copy()  # noqa: E712
        if ok.empty:
            continue
        for flen, grp in ok.groupby("frame_len_symbols"):
            rows.append({
                "frame_len_symbols": int(flen),
                "method": label,
                "n_points_success": len(grp),
                "mean_leak_EC_actual_bits": float(grp["leak_EC_actual_bits"].mean()),
                "mean_runtime_s": float(grp["runtime_s"].mean()),
            })
    if scalability_df is not None and not scalability_df.empty:
        if "frame_len_symbols" in scalability_df.columns:
            ok = scalability_df[scalability_df["real_ir_success"] == True].copy()  # noqa: E712
            if not ok.empty:
                for (flen, method), grp in ok.groupby(["frame_len_symbols", "method"]):
                    rows.append({
                        "frame_len_symbols": int(flen),
                        "method": method,
                        "n_points_success": len(grp),
                        "mean_leak_EC_actual_bits": float(grp["leak_EC_actual_bits"].mean()) if "leak_EC_actual_bits" in grp.columns else None,
                        "mean_runtime_s": float(grp["runtime_s"].mean()) if "runtime_s" in grp.columns else None,
                    })
    return pd.DataFrame(rows)


def make_failure_analysis(
    cascade_df: pd.DataFrame | None,
    ldpc_df: pd.DataFrame | None,
) -> pd.DataFrame:
    """Count failures by method/dimension/bin_width."""
    parts: list[pd.DataFrame] = []
    for label, src in [("cascade_lite", cascade_df), ("layered_ldpc_lite", ldpc_df)]:
        if src is None or src.empty:
            continue
        fail = src[src["real_ir_success"] == False].copy()  # noqa: E712
        if fail.empty:
            continue
        fail["method_name"] = label
        parts.append(fail)
    if not parts:
        return pd.DataFrame()
    combined = pd.concat(parts, ignore_index=True)
    agg = (
        combined
        .groupby(["method_name", "dimension", "bin_width_ps", "success_classification"])
        .size()
        .reset_index(name="failure_count")
    )
    return agg.sort_values(["method_name", "dimension", "bin_width_ps"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------

def make_manifest(
    input_dir: Path,
    output_dir: Path,
    output_files: list[str],
) -> dict[str, Any]:
    """Build manifest with source hashes and config snapshots."""
    source_files = {
        "cascade_sweep": "cascade_param_sweep_results.csv",
        "ldpc_sweep": "layered_ldpc_param_sweep_results.csv",
        "qldpc_sweep": "qldpc_param_sweep_results.csv",
        "scalability_real": "scalability/ir_benchmark_results.csv",
        "scalability_synth": "scalability_synth/ir_benchmark_results.csv",
        "source_manifest": "ir_v3_run_manifest.json",
    }
    sources: dict[str, Any] = {}
    for key, relpath in source_files.items():
        full = input_dir / relpath
        if full.exists():
            sources[key] = {
                "path": relpath,
                "sha256": compute_file_hash(full),
            }
        else:
            sources[key] = {"path": relpath, "sha256": None, "status": "missing"}

    # Read source manifest config snapshots
    benchmark_snapshot: dict[str, Any] = {}
    per_stage_snapshots: dict[str, Any] = {}
    manifest_path = input_dir / "ir_v3_run_manifest.json"
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            src_manifest = json.load(f)
        benchmark_snapshot = src_manifest.get("benchmark_config_snapshot", {})
        per_stage_snapshots = src_manifest.get("per_stage_config_snapshots", {})

    return {
        "git_commit": get_git_commit(),
        "source_files": sources,
        "benchmark_config_snapshot": benchmark_snapshot,
        "per_stage_config_snapshots": per_stage_snapshots,
        "output_files": output_files,
    }


# ---------------------------------------------------------------------------
# Write outputs
# ---------------------------------------------------------------------------

def write_outputs(output_dir: Path, outputs: dict[str, pd.DataFrame | dict]) -> list[str]:
    """Write all outputs; return list of written filenames."""
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for name, content in outputs.items():
        path = output_dir / name
        if isinstance(content, dict):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
        else:
            content.to_csv(path, index=False)
        written.append(name)
    return written


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    """Entry point for the evidence-package CLI."""
    parser = argparse.ArgumentParser(
        description="Consolidate real_ir_success_first outputs into an evidence package.",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("comparison_bench/outputs_comparison/real_ir_success_first"),
        help="Directory containing source sweep results.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("comparison_bench/outputs_comparison/expanded_real_ir_20260615"),
        help="Directory for generated outputs.",
    )
    args = parser.parse_args(argv)

    input_dir: Path = args.input_dir
    output_dir: Path = args.output_dir

    print(f"Input dir:  {input_dir}")
    print(f"Output dir: {output_dir}")

    # --- Load inputs --------------------------------------------------------
    cascade_df = load_csv(input_dir, "cascade_param_sweep_results.csv")
    ldpc_df = load_csv(input_dir, "layered_ldpc_param_sweep_results.csv")
    qldpc_df = load_csv(input_dir, "qldpc_param_sweep_results.csv")
    scalability_real = load_csv(input_dir, "scalability/ir_benchmark_results.csv")
    scalability_synth = load_csv(input_dir, "scalability_synth/ir_benchmark_results.csv")

    # --- Generate outputs ---------------------------------------------------
    outputs: dict[str, pd.DataFrame | dict] = {}

    if cascade_df is not None:
        outputs["cascade_optimized_summary.csv"] = make_cascade_optimized(cascade_df)
    if ldpc_df is not None:
        outputs["ldpc_optimized_summary.csv"] = make_ldpc_optimized(ldpc_df)
    if qldpc_df is not None:
        outputs["qldpc_reference_summary.csv"] = make_qldpc_reference(qldpc_df)

    scalability_summary = make_scalability_summary(scalability_real, scalability_synth)
    if not scalability_summary.empty:
        outputs["scalability_summary.csv"] = scalability_summary

    method_comparison = make_method_comparison(cascade_df, ldpc_df, scalability_summary)
    if not method_comparison.empty:
        outputs["method_comparison_by_frame_len.csv"] = method_comparison

    failure_analysis = make_failure_analysis(cascade_df, ldpc_df)
    if not failure_analysis.empty:
        outputs["failure_region_analysis.csv"] = failure_analysis

    # --- Manifest -----------------------------------------------------------
    output_files_list = list(outputs.keys())
    outputs["expanded_evidence_manifest.json"] = make_manifest(
        input_dir, output_dir, output_files_list
    )

    # --- Write --------------------------------------------------------------
    written = write_outputs(output_dir, outputs)

    print(f"\nGenerated {len(written)} files:")
    for name in written:
        print(f"  - {name}")
    print("Done.")


if __name__ == "__main__":
    main()
