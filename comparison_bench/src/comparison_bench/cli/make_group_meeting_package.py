#!/usr/bin/env python3
"""Generate the consolidated group-meeting analysis package from sweep outputs.

Reads all sweep outputs from flen64/, flen128/, flen256/ subdirectories,
reads Polar existing baseline, and produces 9 CSVs + manifest + report.

Usage:
    python -m comparison_bench.src.comparison_bench.cli.make_group_meeting_package

Outputs: comparison_bench/outputs_comparison/group_meeting_ir_20260615/
    1. success_rate_by_method.csv
    2. leakage_by_method.csv
    3. runtime_by_method.csv
    4. cascade_best_config_by_dataset.csv
    5. ldpc_parity_threshold.csv
    6. qldpc_reference_feasibility.csv
    7. beta_by_frame_length.csv
    8. failure_region_summary.csv
    9. method_recommendation_matrix.csv
   10. group_meeting_ir_manifest.json
"""

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd

from ..io.polar_existing_bridge import benchmark_rows_from_polar_output, locate_existing_polar_outputs, select_polar_output

BASE_DIR = Path("comparison_bench/outputs_comparison/group_meeting_ir_20260615")
FLEN_DIRS = {64: BASE_DIR / "flen64", 128: BASE_DIR / "flen128", 256: BASE_DIR / "flen256"}

OUTPUT_FILES: list[str] = []
OUT = BASE_DIR

# ---------- helpers ----------

def _hash_file(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def _register_output(fname: str) -> Path:
    OUTPUT_FILES.append(fname)
    return OUT / fname


def _flen_label(n: int) -> str:
    return f"{n} symbols"


# ---------- 1. success_rate_by_method ----------

def make_success_rate_by_method() -> pd.DataFrame:
    rows = []
    for flen, dirpath in FLEN_DIRS.items():
        for fname in ["cascade_param_sweep_results.csv", "layered_ldpc_param_sweep_results.csv",
                        "qldpc_param_sweep_results.csv"]:
            path = dirpath / fname
            if not path.exists():
                continue
            df = pd.read_csv(path)
            for _, r in df.iterrows():
                rows.append({
                    "dataset_id": r.get("dataset_id"),
                    "dimension": r.get("dimension"),
                    "bin_width_ps": r.get("bin_width_ps"),
                    "method": r.get("method"),
                    "frame_len_symbols": flen,
                    "n_frames_attempted": r.get("n_frames_attempted", 0),
                    "n_frames_success": r.get("n_frames_success", 0),
                    "accepted_frame_fraction": r.get("accepted_frame_fraction", 0),
                    "success_classification": r.get("success_classification", "unknown"),
                    "param_hash": r.get("param_hash", ""),
                })

    # Add Polar existing baseline
    try:
        polar_path = select_polar_output(locate_existing_polar_outputs())
        if polar_path and polar_path.exists():
            polar_df = benchmark_rows_from_polar_output(polar_path)
            if polar_df is not None and not polar_df.empty:
                for _, r in polar_df.iterrows():
                    rows.append({
                        "dataset_id": r.get("dataset_id"),
                        "dimension": r.get("dimension"),
                        "bin_width_ps": r.get("bin_width_ps"),
                        "method": "polar_historical",
                        "frame_len_symbols": r.get("frame_len_symbols", 64),
                        "n_frames_attempted": r.get("n_frames_attempted", 0),
                        "n_frames_success": r.get("n_frames_success", 0),
                        "accepted_frame_fraction": r.get("accepted_frame_fraction", 0),
                        "success_classification": "historical_baseline",
                        "param_hash": "",
                    })
    except Exception as e:
        print(f"  WARNING: Polar baseline unavailable: {e}")

    result = pd.DataFrame(rows)
    path = _register_output("success_rate_by_method.csv")
    result.to_csv(path, index=False)
    print(f"  Wrote {len(result)} rows to {path.name}")
    return result


# ---------- 2. leakage_by_method ----------

def make_leakage_by_method() -> pd.DataFrame:
    rows = []
    for flen, dirpath in FLEN_DIRS.items():
        for fname in ["cascade_param_sweep_results.csv", "layered_ldpc_param_sweep_results.csv"]:
            path = dirpath / fname
            if not path.exists():
                continue
            df = pd.read_csv(path)
            for _, r in df.iterrows():
                rows.append({
                    "dataset_id": r.get("dataset_id"),
                    "dimension": r.get("dimension"),
                    "bin_width_ps": r.get("bin_width_ps"),
                    "method": r.get("method"),
                    "frame_len_symbols": flen,
                    "param_hash": r.get("param_hash", ""),
                    "leak_EC_actual_bits": r.get("leak_EC_actual_bits"),
                    "leak_EC_per_input_bit": r.get("leak_EC_per_input_bit"),
                    "leakage_accounting": "raw_EC_bits",
                })

    result = pd.DataFrame(rows)
    path = _register_output("leakage_by_method.csv")
    result.to_csv(path, index=False)
    print(f"  Wrote {len(result)} rows to {path.name}")
    return result


# ---------- 3. runtime_by_method ----------

def make_runtime_by_method() -> pd.DataFrame:
    rows = []
    for flen, dirpath in FLEN_DIRS.items():
        for fname in ["cascade_param_sweep_results.csv", "layered_ldpc_param_sweep_results.csv",
                        "qldpc_param_sweep_results.csv"]:
            path = dirpath / fname
            if not path.exists():
                continue
            df = pd.read_csv(path)
            for _, r in df.iterrows():
                rows.append({
                    "dataset_id": r.get("dataset_id"),
                    "dimension": r.get("dimension"),
                    "bin_width_ps": r.get("bin_width_ps"),
                    "method": r.get("method"),
                    "frame_len_symbols": flen,
                    "param_hash": r.get("param_hash", ""),
                    "runtime_s": r.get("runtime_s"),
                    "n_frames_attempted": r.get("n_frames_attempted", 0),
                })
    result = pd.DataFrame(rows)
    path = _register_output("runtime_by_method.csv")
    result.to_csv(path, index=False)
    print(f"  Wrote {len(result)} rows to {path.name}")
    return result


# ---------- 4. cascade_best_config_by_dataset ----------

def make_cascade_best_config_by_dataset() -> pd.DataFrame:
    rows = []
    for flen, dirpath in FLEN_DIRS.items():
        path = dirpath / "cascade_param_sweep_results.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path)
        # Best config = lowest leak_EC_per_input_bit among successful runs
        success = df[df.get("accepted_frame_fraction", 0) > 0].copy()
        if success.empty:
            continue
        # Group by dataset_id and find best
        for ds_id, grp in success.groupby("dataset_id"):
            best = grp.loc[grp["leak_EC_per_input_bit"].idxmin()]
            rows.append({
                "dataset_id": ds_id,
                "dimension": best.get("dimension"),
                "bin_width_ps": best.get("bin_width_ps"),
                "frame_len_symbols": flen,
                "best_block_schedule": best.get("block_size_schedule"),
                "best_num_passes": best.get("num_passes"),
                "best_leak_EC_per_input_bit": best.get("leak_EC_per_input_bit"),
                "best_accepted_frame_fraction": best.get("accepted_frame_fraction"),
                "best_runtime_s": best.get("runtime_s"),
                "param_hash": best.get("param_hash"),
            })
    result = pd.DataFrame(rows)
    path = _register_output("cascade_best_config_by_dataset.csv")
    result.to_csv(path, index=False)
    print(f"  Wrote {len(result)} rows to {path.name}")
    return result


# ---------- 5. ldpc_parity_threshold ----------

def make_ldpc_parity_threshold() -> pd.DataFrame:
    rows = []
    for flen, dirpath in FLEN_DIRS.items():
        path = dirpath / "layered_ldpc_param_sweep_results.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path)
        success = df[df.get("accepted_frame_fraction", 0) > 0].copy()
        if success.empty:
            continue
        # Find min parity_fraction that achieves success
        for ds_id, grp in success.groupby("dataset_id"):
            min_parity = grp["parity_fraction"].min()
            best_of_min = grp[grp["parity_fraction"] == min_parity].iloc[0]
            rows.append({
                "dataset_id": ds_id,
                "dimension": best_of_min.get("dimension"),
                "bin_width_ps": best_of_min.get("bin_width_ps"),
                "frame_len_symbols": flen,
                "min_successful_parity_fraction": min_parity,
                "llr_mode": best_of_min.get("llr_mode"),
                "bitplane_rate_mode": best_of_min.get("bitplane_rate_mode"),
                "leak_EC_per_input_bit": best_of_min.get("leak_EC_per_input_bit"),
                "accepted_frame_fraction": best_of_min.get("accepted_frame_fraction"),
            })
    result = pd.DataFrame(rows)
    path = _register_output("ldpc_parity_threshold.csv")
    result.to_csv(path, index=False)
    print(f"  Wrote {len(result)} rows to {path.name}")
    return result


# ---------- 6. qldpc_reference_feasibility ----------

def make_qldpc_reference_feasibility() -> pd.DataFrame:
    rows = []
    flen = 64
    dirpath = FLEN_DIRS[flen]
    path = dirpath / "qldpc_param_sweep_results.csv"
    if path.exists():
        df = pd.read_csv(path)
        for _, r in df.iterrows():
            rows.append({
                "dataset_id": r.get("dataset_id"),
                "dimension": r.get("dimension"),
                "bin_width_ps": r.get("bin_width_ps"),
                "frame_len_symbols": flen,
                "check_fraction": r.get("check_fraction"),
                "row_weight": r.get("row_weight"),
                "n_frames_attempted": r.get("n_frames_attempted", 0),
                "n_frames_success": r.get("n_frames_success", 0),
                "accepted_frame_fraction": r.get("accepted_frame_fraction", 0),
                "success_classification": r.get("success_classification", "reference_only"),
                "leak_EC_per_input_bit": r.get("leak_EC_per_input_bit"),
                "runtime_s": r.get("runtime_s"),
                "notes": "qLDPC reference — not industrial-grade qLDPC",
            })
    result = pd.DataFrame(rows)
    path = _register_output("qldpc_reference_feasibility.csv")
    result.to_csv(path, index=False)
    print(f"  Wrote {len(result)} rows to {path.name}")
    return result


# ---------- 7. beta_by_frame_length ----------

def make_beta_by_frame_length() -> pd.DataFrame:
    rows = []
    for flen, dirpath in FLEN_DIRS.items():
        for fname in ["cascade_param_sweep_results.csv", "layered_ldpc_param_sweep_results.csv"]:
            path = dirpath / fname
            if not path.exists():
                continue
            df = pd.read_csv(path)
            success = df[df.get("accepted_frame_fraction", 0) > 0].copy()
            if success.empty:
                continue
            for _, r in success.iterrows():
                rows.append({
                    "dataset_id": r.get("dataset_id"),
                    "dimension": r.get("dimension"),
                    "bin_width_ps": r.get("bin_width_ps"),
                    "method": r.get("method"),
                    "frame_len_symbols": flen,
                    "param_hash": r.get("param_hash"),
                    "leak_EC_per_input_bit": r.get("leak_EC_per_input_bit"),
                    "beta_eff_empirical": r.get("beta_eff_empirical") if "beta_eff_empirical" in r else None,
                    "raw_ser": r.get("raw_ser"),
                    "post_ir_ser": r.get("post_ir_ser"),
                })
    result = pd.DataFrame(rows)
    path = _register_output("beta_by_frame_length.csv")
    result.to_csv(path, index=False)
    print(f"  Wrote {len(result)} rows to {path.name}")
    return result


# ---------- 8. failure_region_summary ----------

def make_failure_region_summary() -> pd.DataFrame:
    rows = []
    for flen, dirpath in FLEN_DIRS.items():
        for fname, method in [("cascade_param_sweep_results.csv", "cascade_lite"),
                              ("layered_ldpc_param_sweep_results.csv", "layered_ldpc")]:
            path = dirpath / fname
            if not path.exists():
                continue
            df = pd.read_csv(path)
            for _, r in df.iterrows():
                frac = r.get("accepted_frame_fraction", 1)
                if frac is None or frac == 1:
                    continue
                rows.append({
                    "dataset_id": r.get("dataset_id"),
                    "dimension": r.get("dimension"),
                    "bin_width_ps": r.get("bin_width_ps"),
                    "method": method,
                    "frame_len_symbols": flen,
                    "param_hash": r.get("param_hash"),
                    "accepted_frame_fraction": frac,
                    "n_frames_failed_decode": r.get("n_frames_failed_decode", 0),
                    "n_frames_failed_verify": r.get("n_frames_failed_verify", 0),
                    "n_frames_attempted": r.get("n_frames_attempted", 0),
                })
    result = pd.DataFrame(rows)
    path = _register_output("failure_region_summary.csv")
    result.to_csv(path, index=False)
    print(f"  Wrote {len(result)} rows to {path.name}")
    return result


# ---------- 9. method_recommendation_matrix ----------

def make_method_recommendation_matrix(success_rate_df: pd.DataFrame) -> pd.DataFrame:
    if success_rate_df.empty:
        print("  WARNING: empty success_rate data for recommendations")
        return pd.DataFrame()

    # Per method+dataset summary
    summary = success_rate_df.groupby(["dataset_id", "method", "frame_len_symbols"]).agg(
        dimension=("dimension", "first"),
        bin_width_ps=("bin_width_ps", "first"),
        success_rate_max=("accepted_frame_fraction", "max"),
        n_rows=("param_hash", "count"),
    ).reset_index()

    # Determine recommended method per dataset
    recommendations = []
    for ds_id, grp in summary.groupby("dataset_id"):
        dim = grp["dimension"].iloc[0]
        bw = grp["bin_width_ps"].iloc[0]
        best_row = grp.loc[grp["success_rate_max"].idxmax()]
        # Classification
        if best_row["method"] in ("cascade_lite",):
            classification = "preferred_non_polar"
        elif best_row["method"] in ("layered_ldpc",):
            classification = "control_baseline"
        elif best_row["method"] in ("qldpc_reference",):
            classification = "reference_only"
        elif best_row["method"] in ("polar_historical",):
            classification = "historical_baseline"
        else:
            classification = "other"

        recommendations.append({
            "dataset_id": ds_id,
            "dimension": dim,
            "bin_width_ps": bw,
            "recommended_method": best_row["method"],
            "max_success_rate": best_row["success_rate_max"],
            "recommendation_classification": classification,
            "note": _recommendation_note(best_row["method"], dim, bw),
        })

    result = pd.DataFrame(recommendations)
    path = _register_output("method_recommendation_matrix.csv")
    result.to_csv(path, index=False)
    print(f"  Wrote {len(result)} rows to {path.name}")
    return result


def _recommendation_note(method: str, dim: int, bw: int) -> str:
    if method == "cascade_lite":
        return "Cascade: preferred non-Polar candidate for group meeting"
    elif method == "layered_ldpc":
        return "LDPC: control baseline, may need higher parity fraction"
    elif method == "qldpc_reference":
        return "qLDPC reference: not industrial-grade; feasibility only"
    elif method == "polar_historical":
        return "Polar: historical imported baseline, not same-run rerun"
    return ""


# ---------- Manifest ----------

def make_manifest() -> None:
    # Collect all output file hashes
    file_hashes = {}
    for fname in OUTPUT_FILES:
        fpath = OUT / fname
        if fpath.exists():
            file_hashes[fname] = _hash_file(fpath)

    # Get git info
    git_commit = ""
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            capture_output=True, text=True, cwd=BASE_DIR.parents[1]
        )
        if result.returncode == 0:
            git_commit = result.stdout.strip()
    except Exception:
        pass

    # Collect source file hashes
    source_hashes = {}
    for flen, dirpath in FLEN_DIRS.items():
        for f in dirpath.glob("*.csv"):
            source_hashes[str(f.relative_to(BASE_DIR))] = _hash_file(f)
        for f in dirpath.glob("*.parquet"):
            source_hashes[str(f.relative_to(BASE_DIR))] = _hash_file(f)

    # Read config snapshots from component manifests
    config_snapshots = {}
    for flen, dirpath in FLEN_DIRS.items():
        manifest_path = dirpath / "ir_v3_run_manifest.json"
        if manifest_path.exists():
            try:
                m = json.loads(manifest_path.read_text())
                config_snapshots[f"flen{flen}"] = {
                    "config": m.get("config", {}),
                    "stages": m.get("completed_stages", []),
                    "notes": m.get("notes", ""),
                }
            except Exception:
                pass

    manifest = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "git_commit": git_commit,
        "description": "Group-meeting IR large comparison — expanded sweeps on 14 datasets × 3 frame lengths",
        "output_directory": str(BASE_DIR),
        "output_files": file_hashes,
        "source_sweep_files": source_hashes,
        "config_snapshots": config_snapshots,
        "method_notes": {
            "cascade_lite": "preferred non-Polar candidate",
            "layered_ldpc": "control baseline",
            "qldpc_reference": "reference only — not industrial qLDPC",
            "polar_historical": "historical imported baseline",
        },
        "known_limitations": [
            "d=8/d=16/d=32 real data limited to 4 frames each (batch had only 4)",
            "d=1024 data has 64 frames per dataset for scalability perspective",
            "Longer frames (128, 256) built by regrouping — fewer frames at longer lengths",
            "qLDPC only run on low-noise subset (bw >= 180ps)",
        ],
        "no_overwrite_confirmation": True,
    }

    path = _register_output("group_meeting_ir_manifest.json")
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"  Wrote manifest to {path.name}")


# ---------- main ----------

def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()

    print("Generating group-meeting analysis package...")
    print(f"  Output dir: {OUT}")

    success_rate = make_success_rate_by_method()
    leakage = make_leakage_by_method()
    runtime = make_runtime_by_method()
    cascade_best = make_cascade_best_config_by_dataset()
    ldpc_thresh = make_ldpc_parity_threshold()
    qldpc_feas = make_qldpc_reference_feasibility()
    beta_flen = make_beta_by_frame_length()
    failure = make_failure_region_summary()
    rec = make_method_recommendation_matrix(success_rate)
    make_manifest()

    dt = time.perf_counter() - t0
    print(f"\nAll {len(OUTPUT_FILES)} files generated in {dt:.1f}s")
    print(f"Output directory: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
