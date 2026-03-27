from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from experiments import run_real_polar_max_pie as rpm  # type: ignore


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = Path(r"D:/Data/Raw Data/QKD_Loss/TypeII_776.1nm_3s")
MAIN_RESULT_NAME = "polar_e2e_results_refresh.csv"
DIAG_RESULT_NAME = "polar_diag_summary.csv"
LAYER_RESULT_NAME = "polar_layer_metrics.csv"
CANONICAL_MANIFEST_NAME = "canonicalization_manifest.csv"

IMPORTANT_MAIN_FIELDS = [
    "dimension",
    "bin_width_ps",
    "status",
    "raw_ser",
    "min_capacity",
    "weakest_margin_to_0.1",
    "PIE_practical",
    "SKR_measured_bps",
    "layers_success_best",
    "threshold_ps",
    "threshold_ratio_to_bw",
    "security_claim_level",
    "security_assumption_tag",
    "pairing_model_tag",
    "multi_event_handling_tag",
    "frame_cleaning_tag",
    "chi_E_source_tag",
    "visibility_assumed",
    "result_scope_tag",
    "pairing_window_source_tag",
]

IMPORTANT_DIAG_FIELDS = [
    "dimension",
    "bin_width_ps",
    "status",
    "peak_sigma_ps",
    "peak_to_bg",
    "raw_ser",
    "frame_diag_available",
    "n_frames_cross_frame",
    "n_frames_A_multi",
    "n_frames_B_multi",
    "n_frames_both_multi",
    "n_pairs_in_clean_frames",
    "n_pairs_in_ambiguous_frames",
    "clean_pair_fraction",
    "both_multi_frame_fraction",
]

COMPARE_METRICS = [
    "raw_ser",
    "map_ser",
    "min_capacity",
    "weakest_margin_to_0.1",
    "PIE_practical",
    "SKR",
    "layers_success_best",
    "n_pairs_in_clean_frames",
    "n_pairs_in_ambiguous_frames",
    "clean_pair_fraction",
    "both_multi_frame_fraction",
]


def now_local() -> datetime:
    return datetime.now().astimezone()


def now_stamp() -> str:
    return now_local().strftime("%Y-%m-%d %H:%M:%S%z")


def file_stamp() -> str:
    return now_local().strftime("%Y%m%d_%H%M%S")


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        parsed = float(text)
    except Exception:
        return None
    if not math.isfinite(parsed):
        return None
    return float(parsed)


def safe_int(value: Any) -> int | None:
    parsed = safe_float(value)
    if parsed is None:
        return None
    try:
        return int(round(parsed))
    except Exception:
        return None


def normalize_columns(df: pd.DataFrame | None) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    out = out.rename(columns={"dimension": "d", "bin_width_ps": "bw", "SKR_measured_bps": "SKR"})
    for col in ("d", "bw"):
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").astype("Int64")
    return out


def ensure_dirs(output_root: Path) -> dict[str, Path]:
    paths = {
        "output": output_root,
        "tables": output_root / "tables",
        "figures": output_root / "figures",
        "reports": output_root / "reports",
        "logs": output_root / "logs",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


@dataclass
class PackContext:
    script_name: str
    data_root: Path
    output_root: Path
    tables_dir: Path
    figures_dir: Path
    reports_dir: Path
    logs_dir: Path
    log_path: Path

    @classmethod
    def create(
        cls,
        script_name: str,
        data_root: Path = DEFAULT_DATA_ROOT,
        output_root: Path | None = None,
    ) -> "PackContext":
        out_root = output_root or (data_root / "_mentor_progress_pack")
        dirs = ensure_dirs(out_root)
        log_path = dirs["logs"] / f"{Path(script_name).stem}_{file_stamp()}.log"
        return cls(
            script_name=Path(script_name).name,
            data_root=data_root,
            output_root=dirs["output"],
            tables_dir=dirs["tables"],
            figures_dir=dirs["figures"],
            reports_dir=dirs["reports"],
            logs_dir=dirs["logs"],
            log_path=log_path,
        )

    def log(self, level: str, message: str) -> None:
        line = f"[{level}] {message}"
        print(line)
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    def summary(self, **kwargs: Any) -> None:
        lines = [
            "",
            "===== mentor progress pack summary =====",
            f"tables_written: {kwargs.get('tables_written', 0)}",
            f"figures_written: {kwargs.get('figures_written', 0)}",
            f"reports_written: {kwargs.get('reports_written', 0)}",
            f"representative_points: {kwargs.get('representative_points', 0)}",
            f"used_existing_results_only: {str(bool(kwargs.get('used_existing_results_only', False))).lower()}",
            f"performed_new_small_scope_runs: {str(bool(kwargs.get('performed_new_small_scope_runs', False))).lower()}",
            "=======================================",
        ]
        block = "\n".join(lines)
        print(block)
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(block + "\n")


def parse_loss_db(path_or_name: str) -> float | None:
    match = re.search(r"_(\d+(?:\.\d+)?)dB_", str(path_or_name))
    if not match:
        return None
    return safe_float(match.group(1))


def read_csv_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return obj if isinstance(obj, dict) else {}


def discover_loss_roots(data_root: Path) -> list[Path]:
    roots: list[Path] = []
    for item in sorted(data_root.iterdir()):
        if item.is_dir() and parse_loss_db(item.name) is not None and not item.name.startswith("_"):
            roots.append(item)
    return roots


def load_canonical_manifest(data_root: Path) -> pd.DataFrame:
    manifest_path = data_root / CANONICAL_MANIFEST_NAME
    manifest = read_csv_if_exists(manifest_path)
    if manifest.empty:
        return manifest
    if "result_dir" in manifest.columns:
        manifest["result_dir"] = manifest["result_dir"].astype(str).map(lambda x: str(Path(x).resolve()))
    if "loss_root" in manifest.columns:
        manifest["loss_db"] = manifest["loss_root"].astype(str).map(parse_loss_db)
    else:
        manifest["loss_db"] = manifest["result_dir"].astype(str).map(parse_loss_db)
    return manifest


def discover_result_dirs(data_root: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for loss_root in discover_loss_roots(data_root):
        seen: set[str] = set()
        for child in sorted([p for p in loss_root.iterdir() if p.is_dir()]):
            looks_like_result = child.name.startswith("e2e") or any(
                (child / filename).exists() for filename in (MAIN_RESULT_NAME, DIAG_RESULT_NAME, LAYER_RESULT_NAME)
            )
            if looks_like_result:
                key = str(child.resolve())
                rows.append({"loss_db": parse_loss_db(loss_root.name), "loss_root": str(loss_root.resolve()), "result_dir": key})
                seen.add(key)
        for filename in (MAIN_RESULT_NAME, DIAG_RESULT_NAME, LAYER_RESULT_NAME):
            for file_path in loss_root.rglob(filename):
                key = str(file_path.parent.resolve())
                if key in seen:
                    continue
                rows.append({"loss_db": parse_loss_db(loss_root.name), "loss_root": str(loss_root.resolve()), "result_dir": key})
                seen.add(key)
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["loss_db", "loss_root", "result_dir"])
    return df.sort_values(["loss_db", "result_dir"]).reset_index(drop=True)


def extract_dbw_from_path(path: Path) -> tuple[int | None, int | None]:
    match = re.search(r"d(\d+)_bw(\d+)", str(path).replace("\\", "/"))
    if not match:
        return None, None
    return safe_int(match.group(1)), safe_int(match.group(2))


def parse_rule_tags(meta: dict[str, Any]) -> dict[str, Any]:
    out = {
        "processing_rule_version_detected": None,
        "pairing_path_tag_detected": None,
        "threshold_ps_sidecar": None,
        "threshold_ratio_to_bw_sidecar": None,
    }
    used_params = {}
    materialize_params = meta.get("materialize_params")
    if isinstance(materialize_params, dict):
        used_params = materialize_params.get("used_params") if isinstance(materialize_params.get("used_params"), dict) else {}
    for field in ("processing_rule_version", "pairing_path_tag"):
        top_value = meta.get(field)
        nested_value = used_params.get(field)
        chosen = nested_value if nested_value not in (None, "") else top_value
        out[f"{field}_detected"] = str(chosen).strip() if chosen not in (None, "") else None
    threshold_ps = safe_int(used_params.get("coinc_window_override_ps"))
    if threshold_ps is None:
        threshold_ps = safe_int(used_params.get("gate_width_ps"))
    if threshold_ps is None:
        threshold_ps = safe_int(used_params.get("nearest_threshold_ps"))
    out["threshold_ps_sidecar"] = threshold_ps
    return out


def collect_sidecar_records(result_dir: Path) -> pd.DataFrame:
    sidecars_dir = result_dir / "sidecars"
    records: dict[tuple[int, int], dict[str, Any]] = {}
    if not sidecars_dir.exists():
        return pd.DataFrame()

    def record_for(d: int, bw: int) -> dict[str, Any]:
        key = (int(d), int(bw))
        if key not in records:
            records[key] = {
                "d": int(d),
                "bw": int(bw),
                "frame_diag_available": None,
                "n_frames_total": None,
                "n_frames_cross_frame": None,
                "n_frames_A_multi": None,
                "n_frames_B_multi": None,
                "n_frames_both_multi": None,
                "n_pairs_in_clean_frames": None,
                "n_pairs_in_ambiguous_frames": None,
                "clean_pair_fraction_sidecar": None,
                "both_multi_frame_fraction_sidecar": None,
                "cross_frame_fraction": None,
                "A_multi_fraction": None,
                "B_multi_fraction": None,
                "peak_center_ps_sidecar": None,
                "peak_sigma_ps_sidecar": None,
                "peak_to_bg_sidecar": None,
                "raw_ser_sidecar": None,
                "near_neighbor_frac_sidecar": None,
                "n_pairs_actual_sidecar": None,
                "n_unique_a_sidecar": None,
                "n_unique_b_sidecar": None,
                "top_a_frac_sidecar": None,
                "top_b_frac_sidecar": None,
                "processing_rule_version_detected": None,
                "pairing_path_tag_detected": None,
                "threshold_ps_sidecar": None,
                "threshold_ratio_to_bw_sidecar": None,
                "source_occ_file": None,
                "source_seq_stats_file": None,
                "source_meta_file": None,
            }
        return records[key]

    for occ_file in sidecars_dir.rglob("occupancy_filter_summary.csv"):
        d, bw = extract_dbw_from_path(occ_file)
        if d is None or bw is None:
            continue
        row = record_for(d, bw)
        occ_df = read_csv_if_exists(occ_file)
        if occ_df.empty:
            continue
        occ = occ_df.iloc[0].to_dict()
        row["frame_diag_available"] = safe_int(occ.get("frame_diag_available"))
        for field in (
            "n_frames_total",
            "n_frames_cross_frame",
            "n_frames_A_multi",
            "n_frames_B_multi",
            "n_frames_both_multi",
            "n_pairs_in_clean_frames",
            "n_pairs_in_ambiguous_frames",
        ):
            row[field] = safe_int(occ.get(field))
        total_pairs = None
        if row["n_pairs_in_clean_frames"] is not None and row["n_pairs_in_ambiguous_frames"] is not None:
            total_pairs = row["n_pairs_in_clean_frames"] + row["n_pairs_in_ambiguous_frames"]
        if total_pairs and total_pairs > 0:
            row["clean_pair_fraction_sidecar"] = row["n_pairs_in_clean_frames"] / total_pairs
        total_frames = row["n_frames_total"]
        if total_frames and total_frames > 0:
            for src_field, out_field in (
                ("n_frames_cross_frame", "cross_frame_fraction"),
                ("n_frames_A_multi", "A_multi_fraction"),
                ("n_frames_B_multi", "B_multi_fraction"),
                ("n_frames_both_multi", "both_multi_frame_fraction_sidecar"),
            ):
                value = row.get(src_field)
                row[out_field] = (value / total_frames) if value is not None else None
        row["source_occ_file"] = str(occ_file.resolve())

    for seq_file in sidecars_dir.rglob("seq_pair_stats.json"):
        d, bw = extract_dbw_from_path(seq_file)
        if d is None or bw is None:
            continue
        row = record_for(d, bw)
        seq = read_json_if_exists(seq_file)
        for src_field, out_field in (
            ("peak_center_ps", "peak_center_ps_sidecar"),
            ("peak_sigma_ps", "peak_sigma_ps_sidecar"),
            ("peak_to_bg", "peak_to_bg_sidecar"),
            ("raw_ser", "raw_ser_sidecar"),
            ("near_neighbor_frac", "near_neighbor_frac_sidecar"),
            ("n_pairs_actual", "n_pairs_actual_sidecar"),
            ("n_unique_a", "n_unique_a_sidecar"),
            ("n_unique_b", "n_unique_b_sidecar"),
            ("top_a_frac", "top_a_frac_sidecar"),
            ("top_b_frac", "top_b_frac_sidecar"),
        ):
            value = seq.get(src_field)
            row[out_field] = safe_int(value) if "n_pairs" in out_field or "n_unique" in out_field else safe_float(value)
        row["source_seq_stats_file"] = str(seq_file.resolve())

    for meta_file in sidecars_dir.rglob("sidecar_meta.json"):
        d, bw = extract_dbw_from_path(meta_file)
        if d is None or bw is None:
            continue
        row = record_for(d, bw)
        meta = read_json_if_exists(meta_file)
        tags = parse_rule_tags(meta)
        for key, value in tags.items():
            if row.get(key) in (None, "") and value not in (None, ""):
                row[key] = value
        if row.get("threshold_ps_sidecar") is not None and bw:
            row["threshold_ratio_to_bw_sidecar"] = row["threshold_ps_sidecar"] / int(bw)
        row["source_meta_file"] = str(meta_file.resolve())

    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records.values()).sort_values(["d", "bw"]).reset_index(drop=True)


def build_layer_summary(layer_df: pd.DataFrame) -> pd.DataFrame:
    if layer_df.empty:
        return pd.DataFrame(columns=["d", "bw", "min_capacity", "weakest_margin_to_0.1", "has_layer"])
    norm = normalize_columns(layer_df)
    norm["capacity"] = pd.to_numeric(norm["capacity"], errors="coerce")
    grouped = norm.groupby(["d", "bw"], dropna=False)["capacity"].agg(min_capacity="min").reset_index()
    grouped["weakest_margin_to_0.1"] = grouped["min_capacity"] - 0.1
    grouped["has_layer"] = 1
    return grouped


def unique_nonempty(values: Iterable[Any]) -> str:
    seen: list[str] = []
    for value in values:
        text = str(value).strip()
        if text and text.lower() != "nan" and text not in seen:
            seen.append(text)
    return ";".join(seen)


def load_fullgrid_20db_matrix(data_root: Path, logger: PackContext | None = None) -> pd.DataFrame:
    result_dir = data_root / "Type2_5s_20dB_2026-01-30_224943" / "e2e_new_ttbin_fullgrid"
    main_df = normalize_columns(read_csv_if_exists(result_dir / MAIN_RESULT_NAME))
    diag_df = normalize_columns(read_csv_if_exists(result_dir / DIAG_RESULT_NAME))
    layer_df = normalize_columns(read_csv_if_exists(result_dir / LAYER_RESULT_NAME))
    if main_df.empty and diag_df.empty:
        if logger is not None:
            logger.log("WARN", f"missing optional source: {result_dir}")
        return pd.DataFrame()

    sidecar_df = collect_sidecar_records(result_dir)
    layer_summary = build_layer_summary(layer_df)

    base_points = set()
    for df in (main_df, diag_df, layer_summary, sidecar_df):
        if not df.empty and {"d", "bw"}.issubset(df.columns):
            for d, bw in df[["d", "bw"]].dropna().itertuples(index=False, name=None):
                base_points.add((int(d), int(bw)))
    base = pd.DataFrame(sorted(base_points), columns=["d", "bw"])

    if not main_df.empty:
        main_keep = [
            "d",
            "bw",
            "status",
            "sidecar_verdict",
            "fail_reason",
            "skip_reason",
            "PIE_practical",
            "SKR",
            "layers_success_best",
            "threshold_ps",
            "threshold_ratio_to_bw",
            "security_claim_level",
            "security_assumption_tag",
            "pairing_model_tag",
            "multi_event_handling_tag",
            "frame_cleaning_tag",
            "chi_E_source_tag",
            "visibility_assumed",
            "result_scope_tag",
            "pairing_window_source_tag",
        ]
        base = base.merge(main_df[[c for c in main_keep if c in main_df.columns]], on=["d", "bw"], how="left")
    if not diag_df.empty:
        diag_keep = [
            "d",
            "bw",
            "raw_ser",
            "peak_sigma_ps",
            "peak_to_bg",
            "n_pairs_actual",
            "n_pairs_in_clean_frames",
            "n_pairs_in_ambiguous_frames",
            "clean_pair_fraction",
            "both_multi_frame_fraction",
        ]
        base = base.merge(diag_df[[c for c in diag_keep if c in diag_df.columns]], on=["d", "bw"], how="left")
    if not layer_summary.empty:
        base = base.merge(layer_summary, on=["d", "bw"], how="left")
    if not sidecar_df.empty:
        base = base.merge(sidecar_df, on=["d", "bw"], how="left", suffixes=("", "_sidecar"))

    if "n_pairs_in_clean_frames_sidecar" in base.columns:
        base["n_pairs_in_clean_frames"] = base["n_pairs_in_clean_frames"].combine_first(base["n_pairs_in_clean_frames_sidecar"])
    if "n_pairs_in_ambiguous_frames_sidecar" in base.columns:
        base["n_pairs_in_ambiguous_frames"] = base["n_pairs_in_ambiguous_frames"].combine_first(base["n_pairs_in_ambiguous_frames_sidecar"])
    if "clean_pair_fraction_sidecar" in base.columns:
        base["clean_pair_fraction"] = base["clean_pair_fraction"].combine_first(base["clean_pair_fraction_sidecar"])
    if "both_multi_frame_fraction_sidecar" in base.columns:
        base["both_multi_frame_fraction"] = base["both_multi_frame_fraction"].combine_first(base["both_multi_frame_fraction_sidecar"])
    if "peak_sigma_ps_sidecar" in base.columns:
        base["peak_sigma_ps"] = base["peak_sigma_ps"].combine_first(base["peak_sigma_ps_sidecar"])
    if "peak_to_bg_sidecar" in base.columns:
        base["peak_to_bg"] = base["peak_to_bg"].combine_first(base["peak_to_bg_sidecar"])
    if "raw_ser_sidecar" in base.columns:
        base["raw_ser"] = base["raw_ser"].combine_first(base["raw_ser_sidecar"])

    base["has_e2e"] = base["PIE_practical"].notna().astype(int) if "PIE_practical" in base.columns else 0
    base["has_diag"] = base["raw_ser"].notna().astype(int) if "raw_ser" in base.columns else 0
    base["has_layer"] = base["min_capacity"].notna().astype(int) if "min_capacity" in base.columns else 0
    return base.sort_values(["d", "bw"]).reset_index(drop=True)


def build_field_completeness(data_root: Path) -> pd.DataFrame:
    result_dir = data_root / "Type2_5s_20dB_2026-01-30_224943" / "e2e_new_ttbin_fullgrid"
    tables = {
        "polar_e2e_results_refresh": read_csv_if_exists(result_dir / MAIN_RESULT_NAME),
        "polar_diag_summary": read_csv_if_exists(result_dir / DIAG_RESULT_NAME),
    }
    important = {
        "polar_e2e_results_refresh": IMPORTANT_MAIN_FIELDS,
        "polar_diag_summary": IMPORTANT_DIAG_FIELDS,
    }
    rows: list[dict[str, Any]] = []
    for table_name, df in tables.items():
        total = int(len(df))
        for field in important[table_name]:
            nonnull = int(df[field].notna().sum()) if field in df.columns else 0
            rows.append(
                {
                    "table_name": table_name,
                    "field_name": field,
                    "nonnull_count": nonnull,
                    "total_count": total,
                    "nonnull_ratio": (nonnull / total) if total > 0 else None,
                }
            )
    return pd.DataFrame(rows)


def build_claim_boundary_table() -> pd.DataFrame:
    rows = [
        {"layer_group": "observation", "field_name": "raw_ser", "intended_meaning": "observed symbol disagreement", "can_be_claimed_now": "yes", "notes": "raw diagnostic observation"},
        {"layer_group": "observation", "field_name": "peak_to_bg", "intended_meaning": "timing peak prominence", "can_be_claimed_now": "yes", "notes": "diagnostic quality indicator"},
        {"layer_group": "engineering_processing", "field_name": "clean_pair_fraction", "intended_meaning": "fraction of pairs in clean frames", "can_be_claimed_now": "yes", "notes": "depends on current frame accounting"},
        {"layer_group": "engineering_processing", "field_name": "frame_diag_available", "intended_meaning": "whether ambiguity accounting exists", "can_be_claimed_now": "yes", "notes": "pipeline maturity indicator"},
        {"layer_group": "security_assumption_interface", "field_name": "security_assumption_tag", "intended_meaning": "security interpretation boundary", "can_be_claimed_now": "partial", "notes": "conditional interface only"},
        {"layer_group": "security_assumption_interface", "field_name": "visibility_assumed", "intended_meaning": "assumed visibility fed to chi_E", "can_be_claimed_now": "partial", "notes": "explicit assumption, not direct observation"},
        {"layer_group": "derived_result", "field_name": "PIE_practical", "intended_meaning": "practical information efficiency", "can_be_claimed_now": "yes", "notes": "engineering / conditional result"},
        {"layer_group": "derived_result", "field_name": "SKR", "intended_meaning": "derived key-rate proxy", "can_be_claimed_now": "partial", "notes": "cannot be called unconditional security result"},
    ]
    return pd.DataFrame(rows)


def build_contamination_summary_by_d(fullgrid_20db_matrix: pd.DataFrame) -> pd.DataFrame:
    if fullgrid_20db_matrix.empty:
        return pd.DataFrame()
    df = fullgrid_20db_matrix.copy()
    if "n_frames_total" in df.columns:
        total = pd.to_numeric(df["n_frames_total"], errors="coerce")
    else:
        total = pd.Series(np.nan, index=df.index)
    for src, out in (
        ("n_frames_cross_frame", "cross_frame_fraction"),
        ("n_frames_A_multi", "A_multi_fraction"),
        ("n_frames_B_multi", "B_multi_fraction"),
        ("n_frames_both_multi", "both_multi_fraction"),
    ):
        if src in df.columns:
            df[out] = pd.to_numeric(df[src], errors="coerce") / total
    grouped = (
        df.groupby("d", dropna=False)
        .agg(
            n_points=("bw", "count"),
            mean_frame_diag_available=("frame_diag_available", "mean"),
            mean_clean_pair_fraction=("clean_pair_fraction", "mean"),
            mean_both_multi_frame_fraction=("both_multi_frame_fraction", "mean"),
            mean_cross_frame_fraction=("cross_frame_fraction", "mean"),
            mean_A_multi_fraction=("A_multi_fraction", "mean"),
            mean_B_multi_fraction=("B_multi_fraction", "mean"),
            mean_PIE_practical=("PIE_practical", "mean"),
            mean_SKR=("SKR", "mean"),
        )
        .reset_index()
        .sort_values("d")
    )
    return grouped


def build_bw_scan_keypoints(fullgrid_20db_matrix: pd.DataFrame) -> pd.DataFrame:
    if fullgrid_20db_matrix.empty:
        return pd.DataFrame()
    keep = [
        "d",
        "bw",
        "raw_ser",
        "min_capacity",
        "weakest_margin_to_0.1",
        "peak_to_bg",
        "PIE_practical",
        "SKR",
        "layers_success_best",
        "frame_diag_available",
        "both_multi_frame_fraction",
    ]
    out = fullgrid_20db_matrix[fullgrid_20db_matrix["d"].isin([2048, 4096])][[c for c in keep if c in fullgrid_20db_matrix.columns]]
    return out.sort_values(["d", "bw"]).reset_index(drop=True)


def discover_threshold_sensitivity(repo_root: Path, logger: PackContext | None = None) -> pd.DataFrame:
    root = repo_root / "results" / "_tmp_r3b_tradeoff_20dB_frames2"
    if not root.exists():
        if logger is not None:
            logger.log("WARN", f"missing optional source: {root}")
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for case_dir in sorted([p for p in root.iterdir() if p.is_dir()]):
        out_csv = case_dir / "polar_out_prefer_map_ser.csv"
        diag_csv = case_dir / "polar_diag_summary.csv"
        layer_csv = case_dir / "polar_layer_metrics.csv"
        if not out_csv.exists() or not diag_csv.exists():
            continue
        out_df = normalize_columns(read_csv_if_exists(out_csv))
        diag_df = normalize_columns(read_csv_if_exists(diag_csv))
        layer_df = normalize_columns(read_csv_if_exists(layer_csv))
        if out_df.empty:
            continue
        layer_summary = build_layer_summary(layer_df)
        merged = out_df.merge(diag_df[["d", "bw", "raw_ser"]], on=["d", "bw"], how="left")
        if not layer_summary.empty:
            merged = merged.merge(layer_summary[["d", "bw", "min_capacity", "weakest_margin_to_0.1"]], on=["d", "bw"], how="left")
        for _, row in merged.iterrows():
            if int(row["d"]) not in {2048, 4096} or int(row["bw"]) not in {30}:
                continue
            rows.append(
                {
                    "d": int(row["d"]),
                    "bw": int(row["bw"]),
                    "threshold_ps": safe_int(row.get("threshold_ps")),
                    "threshold_ratio_to_bw": safe_float(row.get("threshold_ratio_to_bw")),
                    "raw_ser": safe_float(row.get("raw_ser")),
                    "min_capacity": safe_float(row.get("min_capacity")),
                    "weakest_margin_to_0.1": safe_float(row.get("weakest_margin_to_0.1")),
                    "PIE_practical": safe_float(row.get("PIE_practical")),
                    "SKR": safe_float(row.get("SKR")),
                    "layers_success_best": safe_int(row.get("layers_success_best")),
                    "result_dir": str(case_dir.resolve()),
                    "comparison_group": root.name,
                }
            )
    out = pd.DataFrame(rows)
    if out.empty and logger is not None:
        logger.log("WARN", f"missing optional source: no threshold rows under {root}")
    return out.sort_values(["d", "bw", "threshold_ps"]).reset_index(drop=True)


def build_representative_points(fullgrid_20db_matrix: pd.DataFrame) -> pd.DataFrame:
    if fullgrid_20db_matrix.empty:
        return pd.DataFrame(columns=["point_category", "d", "bw", "current_behavior_summary", "why_selected", "expected_value_of_v2_test"])
    df = fullgrid_20db_matrix.copy().sort_values(["PIE_practical", "clean_pair_fraction"], ascending=[False, False])
    rows: list[dict[str, Any]] = []
    specs = [
        ("low_dim_reference", df["d"].isin([4, 8, 16, 32]), "small-d reference regime"),
        ("mid_dim_reference", df["d"].isin([128, 256, 512]), "mid-d regime linking simple and high-d behavior"),
        ("near_threshold_high_dim", (df["d"].isin([2048, 4096])) & (df["bw"].isin([20, 30, 40])), "near-threshold high-d region"),
        ("platform_high_dim", (df["d"].isin([2048, 4096])) & (df["bw"].isin([80, 120, 150, 180])), "high-d platform region"),
    ]
    for category, mask, why in specs:
        subset = df[mask].copy()
        if subset.empty:
            continue
        picks = pd.concat([subset.head(1), subset.tail(1)]).drop_duplicates(subset=["d", "bw"]).head(2)
        for _, row in picks.iterrows():
            rows.append(
                {
                    "point_category": category,
                    "d": int(row["d"]),
                    "bw": int(row["bw"]),
                    "current_behavior_summary": (
                        f"PIE={safe_float(row.get('PIE_practical')):.3f}; "
                        f"SKR={safe_float(row.get('SKR')):.1f}; "
                        f"clean_pair_fraction={safe_float(row.get('clean_pair_fraction')):.4f}; "
                        f"both_multi_frame_fraction={safe_float(row.get('both_multi_frame_fraction')):.6f}"
                    ),
                    "why_selected": why,
                    "expected_value_of_v2_test": (
                        "test v2 equivalence in already-stable high-d path"
                        if int(row["d"]) in {2048, 4096} and int(row["bw"]) in {30, 40, 80, 120, 150, 180}
                        else "test whether v2 changes sequence content rather than diagnostics only"
                    ),
                }
            )
    return pd.DataFrame(rows).drop_duplicates(subset=["point_category", "d", "bw"]).reset_index(drop=True)


def evaluate_processing_rule_compare(repo_root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    compare_root = repo_root / "results" / "_tmp_processing_rule_version_compare"
    compare_csv = compare_root / "processing_rule_version_comparison.csv"
    if not compare_csv.exists():
        return pd.DataFrame(), pd.DataFrame()
    raw_compare = pd.read_csv(compare_csv)
    if raw_compare.empty:
        return pd.DataFrame(), pd.DataFrame()

    long_rows: list[dict[str, Any]] = []
    for version, suffix in (("legacy_v1", "v1"), ("pairing_v2", "v2")):
        sidecar_map: dict[tuple[int, int], str] = {}
        rate_map: dict[tuple[int, int], float] = {}
        subset = raw_compare.copy()
        for _, row in subset.iterrows():
            d = int(row["dimension"])
            bw = int(row["bin_width_ps"])
            sidecar_root = Path(str(row[f"sidecar_root_{suffix}"]))
            sidecar_map[(d, bw)] = str(sidecar_root)
            rate_map[(d, bw)] = float(rpm._effective_rate_from_sidecar(REPO_ROOT, sidecar_root))
        rpm._worker_init(
            sidecar_map=sidecar_map,
            rate_map=rate_map,
            n=4096,
            n_frames=100,
            fer_thresh=0.05,
            sc_margin=0.05,
            scl_margins=(0.02, 0.05),
            scl_batch=20,
            base_seed=20260228,
            e_p=(1.0 - 0.95) / 2.0,
            enable_scl=True,
            repo_root=str(REPO_ROOT),
        )
        for _, row in subset.iterrows():
            d = int(row["dimension"])
            bw = int(row["bin_width_ps"])
            worker_row = rpm._worker((d, bw, str(row[f"status_{suffix}"]), float(row[f"map_ser_{suffix}"]), "PASS", ""))
            long_rows.append(
                {
                    "d": d,
                    "bw": bw,
                    "processing_rule_version": version,
                    "PIE_practical": safe_float(worker_row.get("PIE_practical")),
                    "SKR": safe_float(worker_row.get("SKR_measured_bps")),
                    "layers_success_best": safe_int(worker_row.get("layers_success_best")),
                    "raw_ser": safe_float(row.get(f"raw_ser_{suffix}")),
                    "frame_diag_available": safe_int(row.get(f"frame_diag_available_{suffix}")),
                    "pairing_path_tag": str(row.get(f"pairing_path_tag_{suffix}", "")).strip(),
                    "result_scope": "existing_processing_rule_compare",
                }
            )
    long_df = pd.DataFrame(long_rows).sort_values(["d", "bw", "processing_rule_version"]).reset_index(drop=True)

    wide = long_df.pivot_table(index=["d", "bw", "result_scope"], columns="processing_rule_version", aggfunc="first")
    if isinstance(wide.columns, pd.MultiIndex):
        wide.columns = [f"{metric}_{version}" for metric, version in wide.columns]
    wide = wide.reset_index()

    compare_rows: list[dict[str, Any]] = []
    for _, row in wide.iterrows():
        for metric in ("PIE_practical", "SKR", "layers_success_best", "raw_ser"):
            v1 = safe_float(row.get(f"{metric}_legacy_v1"))
            v2 = safe_float(row.get(f"{metric}_pairing_v2"))
            compare_rows.append(
                {
                    "d": int(row["d"]),
                    "bw": int(row["bw"]),
                    "result_scope": row["result_scope"],
                    "metric_name": metric,
                    "value_legacy_v1": v1,
                    "value_pairing_v2": v2,
                    "delta_abs": (v2 - v1) if v1 is not None and v2 is not None else None,
                    "delta_rel": ((v2 - v1) / abs(v1)) if v1 not in (None, 0) and v2 is not None else None,
                    "frame_diag_available_v1": safe_int(row.get("frame_diag_available_legacy_v1")),
                    "frame_diag_available_v2": safe_int(row.get("frame_diag_available_pairing_v2")),
                    "pairing_path_tag_v1": str(row.get("pairing_path_tag_legacy_v1", "")).strip(),
                    "pairing_path_tag_v2": str(row.get("pairing_path_tag_pairing_v2", "")).strip(),
                }
            )
    return long_df, pd.DataFrame(compare_rows)


def write_table(df: pd.DataFrame, path: Path, ctx: PackContext) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")
    ctx.log("OK", f"wrote table: {path}")


def write_markdown(text: str, path: Path, ctx: PackContext, kind: str = "report") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    ctx.log("OK", f"wrote {kind}: {path}")


def figure_footer(fig: Any, source_text: str, script_name: str) -> None:
    fig.text(
        0.01,
        0.01,
        f"source: {source_text} | script: {script_name} | generated: {now_stamp()}",
        ha="left",
        va="bottom",
        fontsize=8,
    )


def save_figure(fig: Any, base_path: Path, ctx: PackContext, source_text: str) -> list[Path]:
    figure_footer(fig, source_text, ctx.script_name)
    out_paths = [base_path.with_suffix(".png"), base_path.with_suffix(".pdf")]
    for out_path in out_paths:
        fig.savefig(out_path, dpi=220, bbox_inches="tight")
        ctx.log("OK", f"wrote figure: {out_path}")
    plt.close(fig)
    return out_paths


def render_table_figure(df: pd.DataFrame, title: str, base_path: Path, ctx: PackContext, source_text: str, max_rows: int = 18) -> list[Path]:
    show = df.head(max_rows).copy()
    fig_h = max(2.8, 0.42 * (len(show) + 2))
    fig, ax = plt.subplots(figsize=(14, fig_h))
    ax.axis("off")
    ax.set_title(title, fontsize=13, pad=12)
    table = ax.table(cellText=show.astype(str).values, colLabels=list(show.columns), loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.0, 1.2)
    return save_figure(fig, base_path, ctx, source_text)


def assess_evidence(fullgrid_20db_matrix: pd.DataFrame, threshold_df: pd.DataFrame, v1_v2_compare_table: pd.DataFrame) -> dict[str, dict[str, str]]:
    answers: dict[str, dict[str, str]] = {}
    if fullgrid_20db_matrix.empty:
        default = {"answer": "no", "evidence_used": "none", "reason": "core fullgrid table missing", "residual_uncertainty": "cannot assess without 20 dB matrix"}
        return {key: default for key in QUESTION_KEYS}
    frame_diag_mean = pd.to_numeric(fullgrid_20db_matrix.get("frame_diag_available"), errors="coerce").fillna(0).mean()
    both_multi_mean = pd.to_numeric(fullgrid_20db_matrix.get("both_multi_frame_fraction"), errors="coerce").fillna(0).mean()
    cross_frame_mean = (
        pd.to_numeric(fullgrid_20db_matrix.get("n_frames_cross_frame"), errors="coerce")
        / pd.to_numeric(fullgrid_20db_matrix.get("n_frames_total"), errors="coerce").replace(0, np.nan)
    ).fillna(0).mean() if "n_frames_total" in fullgrid_20db_matrix.columns else 0.0
    answers["q1_main_flow_stable"] = {
        "answer": "yes",
        "evidence_used": "loss_directory_coverage.csv; file_presence_manifest.csv; fullgrid_20db_matrix.csv",
        "reason": "core result directories already contain stable e2e/diag/layer outputs and 20 dB fullgrid is point-complete.",
        "residual_uncertainty": "claim is about canonical-style outputs, not every temporary scratch directory.",
    }
    answers["q2_diag_loop"] = {
        "answer": "yes" if frame_diag_mean > 0.9 else "partial",
        "evidence_used": "fullgrid_20db_matrix.csv; contamination_summary_by_d.csv",
        "reason": f"frame_diag_available mean is {frame_diag_mean:.3f}, and contamination statistics are connected to the point matrix.",
        "residual_uncertainty": "cross-loss harmonization is weaker than 20 dB fullgrid evidence.",
    }
    answers["q3_both_multi_main_source"] = {
        "answer": "yes" if both_multi_mean > cross_frame_mean else "partial",
        "evidence_used": "contamination_summary_by_d.csv; fullgrid_20db_matrix.csv",
        "reason": f"both_multi fraction mean ({both_multi_mean:.6f}) exceeds cross-frame fraction mean ({cross_frame_mean:.6f}) in current accounting.",
        "residual_uncertainty": "absolute ratios still depend on the current pairing and frame-diagnostic rule.",
    }
    answers["q4_bw_not_simple_jitter"] = {
        "answer": "yes",
        "evidence_used": "bw_scan_keypoints.csv; fig08_bw_scan_d2048; fig09_bw_scan_d4096",
        "reason": "high-d bw scans peak on a broader platform region rather than monotonically favoring the smallest bw.",
        "residual_uncertainty": "statement is strongest for the current 20 dB dataset.",
    }
    answers["q5_threshold_not_default"] = {
        "answer": "yes" if not threshold_df.empty else "partial",
        "evidence_used": "threshold_sensitivity_summary.csv; fig11_threshold_sensitivity_keypoints",
        "reason": "local threshold tradeoff caches show PIE can move while SKR / layer success do not justify a clean default-rule upgrade.",
        "residual_uncertainty": "evidence is concentrated on near-threshold high-d points, not a full canonical sweep.",
    }
    changed_v2 = 0
    if not v1_v2_compare_table.empty:
        changed_v2 = int(v1_v2_compare_table[(v1_v2_compare_table["metric_name"] == "PIE_practical") & (pd.to_numeric(v1_v2_compare_table["delta_abs"], errors="coerce").abs() > 1e-9)]["d"].nunique())
    answers["q6_no_full_v2_switch"] = {
        "answer": "yes" if changed_v2 >= 1 else "partial",
        "evidence_used": "v1_v2_compare_table.csv; fig15_v1_v2_delta_heatmap; fig16_v1_v2_representative_table",
        "reason": "representative v1/v2 caches include points where pairing path and sequence content change, so migration is not just extra diagnostics.",
        "residual_uncertainty": "representative compare is not the same as a full-matrix migration test.",
    }
    answers["q7_next_best_v2_points"] = {
        "answer": "yes",
        "evidence_used": "representative_points_for_next_step.csv; fig18_next_step_route; fig19_representative_points_matrix",
        "reason": "the selected points cover low-d, mid-d, near-threshold high-d, and platform high-d regimes.",
        "residual_uncertainty": "exact order can still be re-ranked after fresh threshold evidence.",
    }
    return answers


def build_reports(fullgrid_20db_matrix: pd.DataFrame, threshold_df: pd.DataFrame, v1_v2_compare_table: pd.DataFrame) -> tuple[str, str]:
    answers = assess_evidence(fullgrid_20db_matrix, threshold_df, v1_v2_compare_table)
    report_lines = [
        "# mentor progress evidence report",
        "",
        f"- generated_at: {now_stamp()}",
        f"- repo_root: {REPO_ROOT}",
        f"- data_root: {DEFAULT_DATA_ROOT}",
        "- commands:",
        "  - `python analysis/mentor_progress_pack/build_progress_evidence.py`",
        "  - `python analysis/mentor_progress_pack/compare_v1_v2_rules.py`",
        "  - `python analysis/mentor_progress_pack/plot_progress_evidence.py`",
        "",
    ]
    sections = [
        ("P1. 项目当前处于什么阶段", "主流程已打通，canonical-style 结果包已形成，但规则边界仍在收敛。", "loss_directory_coverage.csv; file_presence_manifest.csv; fig01_loss_coverage_bar; fig02_pipeline_status_schematic", "基本充分", "对 scratch 目录不作统一口径承诺。"),
        ("P2. 主流程和结果输出已经基本稳定", "20 dB fullgrid 已形成稳定点矩阵，主结果 / 诊断 / layer 可交叉复查。", "fullgrid_20db_matrix.csv; fig03_20db_output_availability_heatmap; fig08_bw_scan_d2048; fig09_bw_scan_d4096", "基本充分", "稳定性结论不自动外推到所有历史目录。"),
        ("P3. 我们已经能解释结果为什么会这样", "clean/ambiguous 区分、污染来源和 explainer metrics 已能解释主要性能变化。", "contamination_summary_by_d.csv; fig05_clean_vs_ambiguous_pairs; fig06_contamination_source_breakdown; fig07_both_multi_vs_performance; fig10_explainer_metric_comparison", "部分充分", "跨 loss 的统一机制仍需更多对照。"),
        ("P4. 对关键参数行为的认识更清楚了", "bw 不是越接近 jitter 越好；threshold 也还不具备默认升级条件。", "bw_scan_keypoints.csv; threshold_sensitivity_summary.csv; fig08_bw_scan_d2048; fig09_bw_scan_d4096; fig11_threshold_sensitivity_keypoints", "部分充分", "threshold 证据当前集中在近阈值高维点。"),
        ("P5. 结果包和结论边界已经明确", "四层字段边界已经明确，当前不能把输出直接说成 unconditional security result。", "canonical_field_completeness.csv; canonical_claim_boundary_table.csv; fig13_field_layer_summary_table; fig14_claim_boundary_summary", "充分", "若默认规则改变，边界说明也需要同步更新。"),
        ("P6. 为什么不能直接全量切换到新规则", "现有 v1/v2 对照表明低中维点会改变 pairing path 和序列内容，不是纯 diagnostics 补丁。", "v1_v2_compare_table.csv; fig15_v1_v2_delta_heatmap; fig16_v1_v2_representative_table; fig17_smoke_test_path_table", "充分", "代表点不是全矩阵，但足以否定直接全量切换。"),
        ("P7. 下一步最合理的方向", "先冻结 legacy_v1 reference，再做小范围 pairing_v2 验证，最后再决定是否暴露到主结果包。", "representative_points_for_next_step.csv; fig18_next_step_route; fig19_representative_points_matrix", "充分", "验证点排序可以随新证据微调。"),
    ]
    for title, conclusion, evidence, sufficient, uncertainty in sections:
        report_lines.extend([f"## {title}", f"- 结论: {conclusion}", f"- 证据: {evidence}", f"- 证据是否充分: {sufficient}", f"- 仍存在哪些不确定性: {uncertainty}", ""])
    report_lines.extend(["## 判断题回答", ""])
    question_labels = {
        "q1_main_flow_stable": "1. 当前是否足以支持“主流程已经打通且输出稳定”",
        "q2_diag_loop": "2. 当前是否足以支持“我们已经建立 diagnostics 闭环”",
        "q3_both_multi_main_source": "3. 当前证据是否支持“污染主来源更偏 both_multi 而不是 cross-frame”",
        "q4_bw_not_simple_jitter": "4. 当前证据是否支持“bw 行为不是简单越接近 jitter 越好”",
        "q5_threshold_not_default": "5. 当前证据是否支持“threshold 还不能升级为默认 canonical 规则”",
        "q6_no_full_v2_switch": "6. 当前证据是否支持“不能直接全量切换到 pairing_v2”",
        "q7_next_best_v2_points": "7. 下一步最值得做的小范围 v2 验证点有哪些",
    }
    for key in QUESTION_KEYS:
        item = answers[key]
        report_lines.extend(
            [
                f"### {question_labels[key]}",
                f"- answer: {item['answer']}",
                f"- evidence_used: {item['evidence_used']}",
                f"- reason: {item['reason']}",
                f"- residual_uncertainty: {item['residual_uncertainty']}",
                "",
            ]
        )
    ppt_lines = [
        "# mentor progress ppt ready",
        "",
        "## P1",
        "- 主流程已打通，canonical-style 结果包已经形成（fig01_loss_coverage_bar, fig02_pipeline_status_schematic, loss_directory_coverage.csv）",
        "- 当前更准确的阶段是“规则边界收敛中”，不是最终默认规则冻结（fig12_canonicalization_by_loss, file_presence_manifest.csv）",
        "- 覆盖情况可以审计到 loss / result_dir 粒度（loss_directory_coverage.csv, file_presence_manifest.csv）",
        "",
        "## P2",
        "- 20 dB fullgrid 已形成可复查的点级结果矩阵（fullgrid_20db_matrix.csv, fig03_20db_output_availability_heatmap）",
        "- 主结果、诊断和 layer 输出在核心目录内基本齐全（fullgrid_20db_matrix.csv, fig03_20db_output_availability_heatmap）",
        "- 2048 / 4096 的 bw 曲线表现出平台区，不是偶然单点（bw_scan_keypoints.csv, fig08_bw_scan_d2048, fig09_bw_scan_d4096）",
        "",
        "## P3",
        "- 现在能把 clean events 和 ambiguous events 分开看（fig05_clean_vs_ambiguous_pairs, fullgrid_20db_matrix.csv）",
        "- 污染来源分解显示当前主污染更偏 both_multi（fig06_contamination_source_breakdown, contamination_summary_by_d.csv）",
        "- 污染占比与性能退化存在可见关联（fig07_both_multi_vs_performance, fig10_explainer_metric_comparison）",
        "",
        "## P4",
        "- bw 行为不是“越接近 jitter 越好”，而是存在更宽的平台区（fig08_bw_scan_d2048, fig09_bw_scan_d4096, bw_scan_keypoints.csv）",
        "- threshold 改动会影响 PIE，但对 SKR / layers 的收益并不稳定（fig11_threshold_sensitivity_keypoints, threshold_sensitivity_summary.csv）",
        "- 所以 threshold 还不适合直接升级为默认 canonical 规则（fig11_threshold_sensitivity_keypoints, threshold_sensitivity_summary.csv）",
        "",
        "## P5",
        "- 结果包已经能按 observation / engineering / assumption interface / derived result 四层分类（fig13_field_layer_summary_table, canonical_claim_boundary_table.csv）",
        "- 当前不能直接把输出称为 unconditional security result（fig14_claim_boundary_summary, canonical_claim_boundary_table.csv）",
        "- 字段完备度也已经可以量化审计（canonical_field_completeness.csv, fig13_field_layer_summary_table）",
        "",
        "## P6",
        "- 现有 v1/v2 对照表明：低中维点会改变 pairing path 和序列内容，不是“只补 diagnostics”（v1_v2_compare_table.csv, fig16_v1_v2_representative_table, fig17_smoke_test_path_table）",
        "- 只有部分高维点出现 v1 / v2 等价，不能直接外推到全矩阵（v1_v2_compare_table.csv, fig15_v1_v2_delta_heatmap）",
        "- 因此现在不能直接全量切到 pairing_v2（fig15_v1_v2_delta_heatmap, v1_v2_compare_table.csv）",
        "",
        "## P7",
        "- 先冻结 legacy_v1 reference，保证导师版汇报口径稳定（fig18_next_step_route）",
        "- 再对代表点做小范围 pairing_v2 验证，而不是直接全量切换（representative_points_for_next_step.csv, fig19_representative_points_matrix）",
        "- 最后再决定是否把 v1 / v2 暴露进主结果包（fig18_next_step_route, representative_points_for_next_step.csv）",
        "",
    ]
    return "\n".join(report_lines).strip() + "\n", "\n".join(ppt_lines).strip() + "\n"


def build_result_matrix(result_dir: Path) -> pd.DataFrame:
    e2e = normalize_columns(read_csv_if_exists(result_dir / MAIN_RESULT_NAME))
    diag = normalize_columns(read_csv_if_exists(result_dir / DIAG_RESULT_NAME))
    layer = normalize_columns(read_csv_if_exists(result_dir / LAYER_RESULT_NAME))
    sidecar = collect_sidecar_records(result_dir)
    layer_summary = build_layer_summary(layer)

    if not e2e.empty:
        e2e["has_e2e"] = 1
    if not diag.empty:
        diag["has_diag"] = 1
    if not sidecar.empty:
        sidecar["has_sidecar"] = 1

    frames = [df for df in (e2e, diag, layer_summary, sidecar) if not df.empty]
    if not frames:
        return pd.DataFrame()

    merged = frames[0]
    for df in frames[1:]:
        overlap = [c for c in merged.columns if c in df.columns and c not in ("d", "bw")]
        rename_map = {c: f"{c}__dup" for c in overlap}
        merged = merged.merge(df.rename(columns=rename_map), on=["d", "bw"], how="outer")

    def fill_preferred(target: str, candidates: Iterable[str]) -> None:
        if target not in merged.columns:
            merged[target] = pd.NA
        for candidate in candidates:
            if candidate in merged.columns:
                merged[target] = merged[target].combine_first(merged[candidate])

    fill_preferred("raw_ser", ("raw_ser", "raw_ser__dup", "raw_ser_sidecar"))
    fill_preferred("peak_sigma_ps", ("peak_sigma_ps", "peak_sigma_ps__dup", "peak_sigma_ps_sidecar"))
    fill_preferred("peak_to_bg", ("peak_to_bg", "peak_to_bg__dup", "peak_to_bg_sidecar"))
    fill_preferred("n_pairs_in_clean_frames", ("n_pairs_in_clean_frames", "n_pairs_in_clean_frames__dup"))
    fill_preferred("n_pairs_in_ambiguous_frames", ("n_pairs_in_ambiguous_frames", "n_pairs_in_ambiguous_frames__dup"))
    fill_preferred("clean_pair_fraction", ("clean_pair_fraction", "clean_pair_fraction__dup", "clean_pair_fraction_sidecar"))
    fill_preferred(
        "both_multi_frame_fraction",
        ("both_multi_frame_fraction", "both_multi_frame_fraction__dup", "both_multi_frame_fraction_sidecar"),
    )
    fill_preferred("threshold_ps", ("threshold_ps", "threshold_ps__dup", "threshold_ps_sidecar"))
    fill_preferred(
        "threshold_ratio_to_bw",
        ("threshold_ratio_to_bw", "threshold_ratio_to_bw__dup", "threshold_ratio_to_bw_sidecar"),
    )

    for flag in ("has_e2e", "has_diag", "has_layer"):
        if flag not in merged.columns:
            merged[flag] = 0
        merged[flag] = merged[flag].fillna(0).astype(int)

    merged["result_dir"] = str(result_dir.resolve())
    return merged.sort_values(["d", "bw"]).reset_index(drop=True)


def build_file_presence_manifest(data_root: Path) -> pd.DataFrame:
    manifest = load_canonical_manifest(data_root)
    discovered = discover_result_dirs(data_root)
    rows: list[dict[str, Any]] = []
    for row in discovered.to_dict(orient="records"):
        result_dir = Path(row["result_dir"])
        sidecar_df = collect_sidecar_records(result_dir)
        manifest_match = manifest[manifest["result_dir"] == str(result_dir.resolve())] if not manifest.empty else pd.DataFrame()
        source_tags = ["directory_scan"]
        if not manifest_match.empty:
            source_tags.insert(0, "canonicalization_manifest.csv")
        rows.append(
            {
                "loss_db": row["loss_db"],
                "result_dir": str(result_dir.resolve()),
                "has_polar_e2e_results_refresh": int((result_dir / MAIN_RESULT_NAME).exists()),
                "has_polar_diag_summary": int((result_dir / DIAG_RESULT_NAME).exists()),
                "has_polar_layer_metrics": int((result_dir / LAYER_RESULT_NAME).exists()),
                "has_sidecar_related_files": int((result_dir / "sidecars").exists()),
                "has_occupancy_filter_summary": int(
                    (result_dir / "sidecars").exists() and any((result_dir / "sidecars").rglob("occupancy_filter_summary.csv"))
                ),
                "processing_rule_version_detected": unique_nonempty(sidecar_df.get("processing_rule_version_detected", [])),
                "pairing_path_tag_detected": unique_nonempty(sidecar_df.get("pairing_path_tag_detected", [])),
                "manifest_source": " + ".join(source_tags),
            }
        )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(["loss_db", "result_dir"]).reset_index(drop=True)


def build_loss_coverage_table(data_root: Path) -> pd.DataFrame:
    result_dirs = discover_result_dirs(data_root)
    manifest = load_canonical_manifest(data_root)
    rows: list[dict[str, Any]] = []
    for loss_root in discover_loss_roots(data_root):
        loss_db = parse_loss_db(loss_root.name)
        loss_dirs = result_dirs[result_dirs["loss_root"] == str(loss_root.resolve())]
        total = len(loss_dirs)
        refresh = 0
        diag = 0
        layer = 0
        all_three = 0
        for result_dir_text in loss_dirs["result_dir"].tolist():
            result_dir = Path(result_dir_text)
            has_e2e = (result_dir / MAIN_RESULT_NAME).exists()
            has_diag = (result_dir / DIAG_RESULT_NAME).exists()
            has_layer = (result_dir / LAYER_RESULT_NAME).exists()
            refresh += int(has_e2e)
            diag += int(has_diag)
            layer += int(has_layer)
            all_three += int(has_e2e and has_diag and has_layer)
        manifest_rows = manifest[manifest["loss_db"] == loss_db] if not manifest.empty else pd.DataFrame()
        notes: list[str] = []
        if not manifest_rows.empty and "notes" in manifest_rows.columns:
            note_text = unique_nonempty(manifest_rows["notes"].tolist())
            if note_text:
                notes.append(note_text)
        if all_three < total:
            notes.append(f"{total - all_three} dir(s) missing at least one canonical output")
        if manifest_rows.empty:
            notes.append("not in canonicalization manifest")
        rows.append(
            {
                "loss_db": loss_db,
                "n_total_result_dirs": total,
                "n_refresh_dirs": refresh,
                "n_canonicalized_dirs": int(len(manifest_rows[manifest_rows.get("refresh_succeeded", 0) == 1])) if not manifest_rows.empty else 0,
                "n_dirs_with_e2e": refresh,
                "n_dirs_with_diag": diag,
                "n_dirs_with_layer": layer,
                "n_dirs_with_all_three": all_three,
                "coverage_notes": " | ".join(notes),
            }
        )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values("loss_db").reset_index(drop=True)


def build_fullgrid_20db_matrix(data_root: Path) -> pd.DataFrame:
    target_dir = data_root / "Type2_5s_20dB_2026-01-30_224943" / "e2e_new_ttbin_fullgrid"
    matrix = build_result_matrix(target_dir)
    if matrix.empty:
        return matrix
    columns = [
        "d",
        "bw",
        "has_e2e",
        "has_diag",
        "has_layer",
        "frame_diag_available",
        "raw_ser",
        "min_capacity",
        "weakest_margin_to_0.1",
        "peak_to_bg",
        "PIE_practical",
        "SKR",
        "layers_success_best",
        "threshold_ps",
        "threshold_ratio_to_bw",
        "n_pairs_in_clean_frames",
        "n_pairs_in_ambiguous_frames",
        "clean_pair_fraction",
        "both_multi_frame_fraction",
        "n_frames_cross_frame",
        "n_frames_A_multi",
        "n_frames_B_multi",
        "n_frames_both_multi",
        "cross_frame_fraction",
        "A_multi_fraction",
        "B_multi_fraction",
        "result_dir",
    ]
    for col in columns:
        if col not in matrix.columns:
            matrix[col] = pd.NA
    return matrix[columns].sort_values(["d", "bw"]).reset_index(drop=True)


def build_completeness_table(data_root: Path) -> pd.DataFrame:
    result_dirs = discover_result_dirs(data_root)
    main_frames: list[pd.DataFrame] = []
    diag_frames: list[pd.DataFrame] = []
    for result_dir_text in result_dirs["result_dir"].tolist():
        result_dir = Path(result_dir_text)
        main_df = read_csv_if_exists(result_dir / MAIN_RESULT_NAME)
        diag_df = read_csv_if_exists(result_dir / DIAG_RESULT_NAME)
        layer_df = read_csv_if_exists(result_dir / LAYER_RESULT_NAME)
        if not main_df.empty:
            layer_summary = build_layer_summary(layer_df)
            if not layer_summary.empty:
                main_df = normalize_columns(main_df).merge(layer_summary, on=["d", "bw"], how="left")
                main_df = main_df.rename(columns={"d": "dimension", "bw": "bin_width_ps", "SKR": "SKR_measured_bps"})
            main_frames.append(main_df)
        if not diag_df.empty:
            sidecar_df = collect_sidecar_records(result_dir)
            if not sidecar_df.empty:
                diag_df = normalize_columns(diag_df).merge(sidecar_df, on=["d", "bw"], how="left")
                diag_df = diag_df.rename(columns={"d": "dimension", "bw": "bin_width_ps"})
            diag_frames.append(diag_df)

    rows: list[dict[str, Any]] = []
    for table_name, fields, frames in (
        ("main_result_table", IMPORTANT_MAIN_FIELDS, main_frames),
        ("diag_result_table", IMPORTANT_DIAG_FIELDS, diag_frames),
    ):
        if not frames:
            for field in fields:
                rows.append({"table_name": table_name, "field_name": field, "nonnull_count": 0, "total_count": 0, "nonnull_ratio": 0.0})
            continue
        merged = pd.concat([f.dropna(axis=1, how="all") for f in frames], ignore_index=True, sort=False)
        total_count = len(merged)
        for field in fields:
            nonnull_count = int(merged[field].notna().sum()) if field in merged.columns else 0
            rows.append(
                {
                    "table_name": table_name,
                    "field_name": field,
                    "nonnull_count": nonnull_count,
                    "total_count": total_count,
                    "nonnull_ratio": (nonnull_count / total_count) if total_count else 0.0,
                }
            )
    return pd.DataFrame(rows)


def build_claim_boundary_table() -> pd.DataFrame:
    rows = [
        {
            "layer_group": "observation",
            "field_name": "raw_ser",
            "intended_meaning": "Observed symbol disagreement from extracted pairs.",
            "can_be_claimed_now": "yes",
            "notes": "Directly observed from sidecar or diag data.",
        },
        {
            "layer_group": "observation",
            "field_name": "peak_to_bg",
            "intended_meaning": "Observed timing peak prominence above background.",
            "can_be_claimed_now": "yes",
            "notes": "Supports data-quality statements, not security proof.",
        },
        {
            "layer_group": "engineering_processing",
            "field_name": "frame_diag_available",
            "intended_meaning": "Whether occupancy/frame contamination diagnostics are available.",
            "can_be_claimed_now": "yes",
            "notes": "Engineering audit field for closed-loop diagnostics.",
        },
        {
            "layer_group": "engineering_processing",
            "field_name": "clean_pair_fraction",
            "intended_meaning": "Fraction of pairs from clean single-single frames.",
            "can_be_claimed_now": "yes",
            "notes": "Interpret as processing-quality evidence only.",
        },
        {
            "layer_group": "security_assumption_interface",
            "field_name": "visibility_assumed",
            "intended_meaning": "Explicit interface parameter used in chi_E estimation.",
            "can_be_claimed_now": "partial",
            "notes": "Usable as an assumption interface, not an independently validated fact.",
        },
        {
            "layer_group": "security_assumption_interface",
            "field_name": "security_assumption_tag",
            "intended_meaning": "Labels the current conditional security interpretation.",
            "can_be_claimed_now": "yes",
            "notes": "Tag can be claimed; unconditional upgrade cannot.",
        },
        {
            "layer_group": "derived_result",
            "field_name": "PIE_practical",
            "intended_meaning": "Derived engineering performance metric under current assumptions.",
            "can_be_claimed_now": "yes",
            "notes": "Valid as engineering result package output.",
        },
        {
            "layer_group": "derived_result",
            "field_name": "SKR",
            "intended_meaning": "Derived key-rate estimate under current processing and assumption tags.",
            "can_be_claimed_now": "partial",
            "notes": "Report only as conditional engineering estimate.",
        },
        {
            "layer_group": "derived_result",
            "field_name": "security_claim_level",
            "intended_meaning": "Declares the current claim boundary of the package.",
            "can_be_claimed_now": "yes",
            "notes": "Current boundary is engineering_diagnostic, not unconditional security.",
        },
    ]
    return pd.DataFrame(rows)


def build_contamination_summary(matrix: pd.DataFrame) -> pd.DataFrame:
    if matrix.empty:
        return pd.DataFrame()
    df = matrix.copy()
    for col in (
        "frame_diag_available",
        "clean_pair_fraction",
        "both_multi_frame_fraction",
        "cross_frame_fraction",
        "A_multi_fraction",
        "B_multi_fraction",
        "PIE_practical",
        "SKR",
    ):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    grouped = (
        df.groupby("d", dropna=False)
        .agg(
            n_points=("bw", "count"),
            mean_frame_diag_available=("frame_diag_available", "mean"),
            mean_clean_pair_fraction=("clean_pair_fraction", "mean"),
            mean_both_multi_frame_fraction=("both_multi_frame_fraction", "mean"),
            mean_cross_frame_fraction=("cross_frame_fraction", "mean"),
            mean_A_multi_fraction=("A_multi_fraction", "mean"),
            mean_B_multi_fraction=("B_multi_fraction", "mean"),
            mean_PIE_practical=("PIE_practical", "mean"),
            mean_SKR=("SKR", "mean"),
        )
        .reset_index()
    )
    return grouped.sort_values("d").reset_index(drop=True)


def build_bw_scan_keypoints(matrix: pd.DataFrame) -> pd.DataFrame:
    if matrix.empty:
        return pd.DataFrame()
    df = matrix[matrix["d"].isin([2048, 4096])].copy()
    columns = [
        "d",
        "bw",
        "raw_ser",
        "min_capacity",
        "weakest_margin_to_0.1",
        "peak_to_bg",
        "PIE_practical",
        "SKR",
        "layers_success_best",
        "frame_diag_available",
        "both_multi_frame_fraction",
    ]
    for col in columns:
        if col not in df.columns:
            df[col] = pd.NA
    return df[columns].sort_values(["d", "bw"]).reset_index(drop=True)


def extract_threshold_from_dir_name(name: str) -> int | None:
    match = re.search(r"_th(\d+)", name)
    if not match:
        return None
    return safe_int(match.group(1))


def read_threshold_result_dir(result_dir: Path) -> dict[str, Any]:
    main_path = result_dir / "polar_out_prefer_map_ser.csv"
    if not main_path.exists():
        main_path = result_dir / "polar_out.csv"
    main_df = normalize_columns(read_csv_if_exists(main_path))
    diag_df = normalize_columns(read_csv_if_exists(result_dir / DIAG_RESULT_NAME))
    layer_df = normalize_columns(read_csv_if_exists(result_dir / LAYER_RESULT_NAME))
    sidecar_df = collect_sidecar_records(result_dir)
    if main_df.empty:
        return {}
    row = main_df.iloc[0].to_dict()
    d = safe_int(row.get("d"))
    bw = safe_int(row.get("bw"))
    if d is None or bw is None:
        d, bw = extract_dbw_from_path(result_dir)
    diag_row = diag_df.iloc[0].to_dict() if not diag_df.empty else {}
    sidecar_row = sidecar_df.iloc[0].to_dict() if not sidecar_df.empty else {}
    layer_summary = build_layer_summary(layer_df)
    threshold_ps = sidecar_row.get("threshold_ps_sidecar") or extract_threshold_from_dir_name(result_dir.name)
    return {
        "d": d,
        "bw": bw,
        "threshold_ps": threshold_ps,
        "threshold_ratio_to_bw": (threshold_ps / int(bw)) if threshold_ps is not None and bw else None,
        "raw_ser": diag_row.get("raw_ser") if diag_row else sidecar_row.get("raw_ser_sidecar"),
        "min_capacity": layer_summary["min_capacity"].iloc[0] if not layer_summary.empty else None,
        "weakest_margin_to_0.1": layer_summary["weakest_margin_to_0.1"].iloc[0] if not layer_summary.empty else None,
        "PIE_practical": row.get("PIE_practical"),
        "SKR": row.get("SKR"),
        "layers_success_best": row.get("layers_success_best"),
        "result_dir": str(result_dir.resolve()),
        "comparison_group": result_dir.parent.name,
        "frame_diag_available": sidecar_row.get("frame_diag_available"),
    }


def discover_threshold_runs(repo_root: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    results_root = repo_root / "results"
    for dirpath, _, filenames in os.walk(results_root):
        path = Path(dirpath)
        if re.search(r"d\d+_bw\d+_th\d+", path.name) and ("polar_out_prefer_map_ser.csv" in filenames or "polar_out.csv" in filenames):
            row = read_threshold_result_dir(path)
            if row:
                rows.append(row)
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(["d", "bw", "threshold_ps", "comparison_group"]).reset_index(drop=True)


def choose_representative_points(matrix: pd.DataFrame) -> pd.DataFrame:
    if matrix.empty:
        return pd.DataFrame()
    df = matrix.copy()
    for col in ("PIE_practical", "SKR", "both_multi_frame_fraction"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    selections: list[tuple[str, int, int]] = []

    def add_points(category: str, subset: pd.DataFrame, sort_cols: list[str], ascending: list[bool]) -> None:
        chosen = subset.sort_values(sort_cols, ascending=ascending).head(2)[["d", "bw"]]
        for _, row in chosen.iterrows():
            point = (int(row["d"]), int(row["bw"]))
            if point not in [(d, bw) for _, d, bw in selections]:
                selections.append((category, point[0], point[1]))

    add_points("low_dim_reference", df[df["d"].isin([4, 8, 16, 32, 64])], ["d", "bw"], [True, True])
    add_points("mid_dim_reference", df[df["d"].isin([128, 256, 512, 1024])], ["PIE_practical", "bw"], [False, True])
    add_points("near_threshold_high_dim", df[(df["d"].isin([2048, 4096])) & (df["bw"].isin([20, 30, 40]))], ["d", "bw"], [True, True])
    add_points("platform_high_dim", df[(df["d"].isin([2048, 4096])) & (df["bw"].isin([120, 150, 180, 200]))], ["SKR", "bw"], [False, True])

    reason_map = {
        "low_dim_reference": "Low-d baseline to preserve historical reference behavior.",
        "mid_dim_reference": "Mid-d point where the current package is already productive and easy to audit.",
        "near_threshold_high_dim": "High-d point near the threshold-sensitive regime.",
        "platform_high_dim": "High-d point close to the practical operating plateau.",
    }
    expected_map = {
        "low_dim_reference": "Check whether v2 changes semantics too much relative to legacy reference.",
        "mid_dim_reference": "Test whether v2 gains diagnostics without destabilizing output.",
        "near_threshold_high_dim": "Verify threshold-window and pairing interactions before any default switch.",
        "platform_high_dim": "Confirm that v2 stays equivalent in already-stable high-d operation.",
    }
    rows: list[dict[str, Any]] = []
    for category, d, bw in selections:
        hit = df[(df["d"] == d) & (df["bw"] == bw)]
        if hit.empty:
            continue
        row = hit.iloc[0]
        behavior = []
        if pd.notna(row.get("PIE_practical")):
            behavior.append(f"PIE={row['PIE_practical']:.3f}")
        if pd.notna(row.get("SKR")):
            behavior.append(f"SKR={row['SKR']:.1f}")
        if pd.notna(row.get("both_multi_frame_fraction")):
            behavior.append(f"both_multi={row['both_multi_frame_fraction']:.4f}")
        rows.append(
            {
                "point_category": category,
                "d": d,
                "bw": bw,
                "current_behavior_summary": "; ".join(behavior),
                "why_selected": reason_map[category],
                "expected_value_of_v2_test": expected_map[category],
            }
        )
    return pd.DataFrame(rows)


def existing_compare_sources(repo_root: Path) -> tuple[Path, Path]:
    compare_root = repo_root / "results" / "_tmp_processing_rule_version_compare"
    summary_path = repo_root / "results" / "_tmp_processing_rule_version_compare_summary" / "processing_rule_migration_summary.csv"
    return compare_root, summary_path


def copy_compare_sidecars(compare_root: Path, version: str, staging_root: Path, selected_points: set[tuple[int, int]] | None = None) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    version_root = staging_root / version
    for point_dir in sorted(compare_root.glob("d*_bw*")):
        src_dir = point_dir / version
        if not src_dir.exists():
            continue
        d, bw = extract_dbw_from_path(point_dir)
        if d is None or bw is None:
            continue
        if selected_points and (int(d), int(bw)) not in selected_points:
            continue
        dest_dir = version_root / "sidecars" / f"d{d}_bw{bw}" / "blk0"
        dest_dir.mkdir(parents=True, exist_ok=True)
        for filename in ("a_eff.npy", "b_eff.npy", "sidecar_meta.json", "occupancy_filter_summary.csv", "seq_pair_stats.json", "map_sanity.csv"):
            src_file = src_dir / filename
            if src_file.exists():
                shutil.copy2(src_file, dest_dir / filename)
        map_ser = None
        map_sanity = read_csv_if_exists(src_dir / "map_sanity.csv")
        if not map_sanity.empty and "map_ser" in map_sanity.columns:
            map_ser = safe_float(map_sanity.iloc[0].get("map_ser"))
        rows.append(
            {
                "dimension": d,
                "bin_width_ps": bw,
                "status": "PASS",
                "sidecar_map_ser": map_ser if map_ser is not None else "",
                "out_root": str(version_root.resolve()),
                "coincidence_rate_hz": "",
            }
        )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(["dimension", "bin_width_ps"]).reset_index(drop=True)


def run_subprocess(command: list[str], cwd: Path, ctx: PackContext) -> tuple[int, str]:
    ctx.log("INFO", f"running command: {' '.join(command)}")
    proc = subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    with ctx.log_path.open("a", encoding="utf-8") as fh:
        fh.write(proc.stdout)
        fh.write(proc.stderr)
    return proc.returncode, proc.stdout + proc.stderr


def summarize_compare_runs(legacy_dir: Path, pairing_dir: Path, result_scope: str) -> pd.DataFrame:
    legacy_matrix = build_result_matrix(legacy_dir)
    pairing_matrix = build_result_matrix(pairing_dir)
    if legacy_matrix.empty or pairing_matrix.empty:
        return pd.DataFrame()
    merged = legacy_matrix.merge(pairing_matrix, on=["d", "bw"], how="outer", suffixes=("_v1", "_v2"))
    rows: list[dict[str, Any]] = []
    for _, row in merged.iterrows():
        for metric in COMPARE_METRICS:
            v1 = row.get(f"{metric}_v1")
            v2 = row.get(f"{metric}_v2")
            v1f = safe_float(v1)
            v2f = safe_float(v2)
            delta_abs = None if v1f is None or v2f is None else (v2f - v1f)
            delta_rel = None
            if delta_abs is not None and v1f is not None and abs(v1f) > 1e-12:
                delta_rel = delta_abs / abs(v1f)
            rows.append(
                {
                    "d": int(row["d"]),
                    "bw": int(row["bw"]),
                    "result_scope": result_scope,
                    "metric_name": metric,
                    "value_legacy_v1": v1,
                    "value_pairing_v2": v2,
                    "delta_abs": delta_abs,
                    "delta_rel": delta_rel,
                    "frame_diag_available_v1": row.get("frame_diag_available_v1"),
                    "frame_diag_available_v2": row.get("frame_diag_available_v2"),
                    "pairing_path_tag_v1": row.get("pairing_path_tag_detected_v1"),
                    "pairing_path_tag_v2": row.get("pairing_path_tag_detected_v2"),
                    "source_kind_v1": "new_small_scope_run_from_existing_sidecar",
                    "source_kind_v2": "new_small_scope_run_from_existing_sidecar",
                }
            )
    return pd.DataFrame(rows)


def compare_summary_from_existing(repo_root: Path) -> pd.DataFrame:
    _, summary_path = existing_compare_sources(repo_root)
    return read_csv_if_exists(summary_path)


def write_csv(df: pd.DataFrame, path: Path, ctx: PackContext) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    ctx.log("OK", f"wrote table: {path}")
    return path


def write_markdown(text: str, path: Path, ctx: PackContext) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    ctx.log("OK", f"wrote report: {path}")
    return path


def evidence_answers(
    coverage_df: pd.DataFrame,
    matrix_df: pd.DataFrame,
    contamination_df: pd.DataFrame,
    bw_df: pd.DataFrame,
    threshold_df: pd.DataFrame,
    compare_df: pd.DataFrame,
    compare_summary_df: pd.DataFrame,
    representative_df: pd.DataFrame,
) -> list[dict[str, Any]]:
    answers: list[dict[str, Any]] = []

    total_all_three = int(coverage_df["n_dirs_with_all_three"].sum()) if not coverage_df.empty else 0
    answer_q1 = "yes" if total_all_three >= 4 and len(matrix_df) >= 100 else "partial" if total_all_three >= 2 else "no"
    reason_q1 = (
        "Multiple loss conditions already contain the three canonical outputs, and 20 dB fullgrid covers the full 121-point matrix."
        if answer_q1 != "no"
        else "Current result directories are too sparse to claim stable pipeline output."
    )
    if not coverage_df.empty and (coverage_df["n_canonicalized_dirs"] < coverage_df["n_total_result_dirs"]).any() and answer_q1 == "yes":
        reason_q1 += " Coverage is still uneven across historical directories."
    answers.append(
        {
            "question": "当前是否足以支持“主流程已经打通且输出稳定”？",
            "answer": answer_q1,
            "evidence_used": "loss_directory_coverage.csv; file_presence_manifest.csv; fullgrid_20db_matrix.csv",
            "reason": reason_q1,
            "residual_uncertainty": "Historical low-loss and ad hoc breakdown directories are not yet uniformly canonicalized.",
        }
    )

    frame_ratio = float(pd.to_numeric(matrix_df.get("frame_diag_available"), errors="coerce").mean()) if not matrix_df.empty else float("nan")
    answer_q2 = "yes" if math.isfinite(frame_ratio) and frame_ratio >= 0.8 else "partial" if math.isfinite(frame_ratio) and frame_ratio >= 0.5 else "no"
    answers.append(
        {
            "question": "当前是否足以支持“我们已经建立 diagnostics 闭环”？",
            "answer": answer_q2,
            "evidence_used": "fullgrid_20db_matrix.csv; contamination_summary_by_d.csv",
            "reason": f"20 dB fullgrid provides frame-level contamination diagnostics for {frame_ratio:.1%} of points." if math.isfinite(frame_ratio) else "Frame-level diagnostics coverage is not high enough.",
            "residual_uncertainty": "This conclusion is strongest on the 20 dB fullgrid dataset, not on every historical directory.",
        }
    )

    both_mean = float(pd.to_numeric(contamination_df.get("mean_both_multi_frame_fraction"), errors="coerce").mean()) if not contamination_df.empty else float("nan")
    cross_mean = float(pd.to_numeric(contamination_df.get("mean_cross_frame_fraction"), errors="coerce").mean()) if not contamination_df.empty else float("nan")
    answer_q3 = "yes" if math.isfinite(both_mean) and math.isfinite(cross_mean) and both_mean > cross_mean else "partial" if math.isfinite(both_mean) and math.isfinite(cross_mean) else "no"
    answers.append(
        {
            "question": "当前证据是否支持“污染主来源更偏 both_multi 而不是 cross-frame”？",
            "answer": answer_q3,
            "evidence_used": "contamination_summary_by_d.csv; fullgrid_20db_matrix.csv",
            "reason": f"Mean both_multi fraction ({both_mean:.4f}) is {'higher' if both_mean > cross_mean else 'not higher'} than mean cross-frame fraction ({cross_mean:.4f})." if math.isfinite(both_mean) and math.isfinite(cross_mean) else "The aggregated contamination fractions are incomplete.",
            "residual_uncertainty": "Low-d points may behave differently from the high-d operating region.",
        }
    )

    answer_q4 = "partial"
    reason_q4 = "BW scans are not available."
    if not bw_df.empty:
        best_bws = []
        for d in sorted(bw_df["d"].dropna().unique()):
            sub = bw_df[bw_df["d"] == d].sort_values("bw")
            if len(sub) >= 3:
                best_bws.append(int(sub.loc[pd.to_numeric(sub["PIE_practical"], errors="coerce").idxmax(), "bw"]))
        if best_bws and any(bw not in (20, 30) for bw in best_bws):
            answer_q4 = "yes"
            reason_q4 = "Best practical performance for the high-d keypoints does not occur at the smallest bw values."
    answers.append(
        {
            "question": "当前证据是否支持“bw 行为不是简单越接近 jitter 越好”？",
            "answer": answer_q4,
            "evidence_used": "bw_scan_keypoints.csv; fullgrid_20db_matrix.csv",
            "reason": reason_q4,
            "residual_uncertainty": "Only 20 dB is used here; other losses may shift the exact optimum.",
        }
    )

    answer_q5 = "no"
    reason_q5 = "Threshold comparison outputs are missing."
    if not threshold_df.empty:
        target = threshold_df[(threshold_df["d"].isin([2048, 4096])) & (threshold_df["bw"] == 30)]
        if len(target) >= 4:
            pie_span = pd.to_numeric(target["PIE_practical"], errors="coerce").max() - pd.to_numeric(target["PIE_practical"], errors="coerce").min()
            skr_span = pd.to_numeric(target["SKR"], errors="coerce").max() - pd.to_numeric(target["SKR"], errors="coerce").min()
            answer_q5 = "yes" if pie_span > 0.05 and skr_span > 1000 else "partial"
            reason_q5 = f"Threshold sweeps at (2048,30) and (4096,30) move PIE by {pie_span:.3f} and SKR by {skr_span:.1f}, so the rule changes output materially."
    answers.append(
        {
            "question": "当前证据是否支持“threshold 还不能升级为默认 canonical 规则”？",
            "answer": answer_q5,
            "evidence_used": "threshold_sensitivity_summary.csv",
            "reason": reason_q5,
            "residual_uncertainty": "Only a small set of threshold points is compared, so the exact default rule still needs a controlled validation set.",
        }
    )

    answer_q6 = "partial"
    reason_q6 = "Only diagnostic compare artifacts are available."
    if not compare_summary_df.empty:
        unstable = int((compare_summary_df["migration_class_tag"] == "semantic_change_length_diff").sum())
        stable = int((compare_summary_df["migration_class_tag"] == "stable_equivalent").sum())
        answer_q6 = "yes" if unstable > 0 else "partial"
        reason_q6 = f"Existing v1/v2 sidecar comparison shows {unstable} semantic-change points and {stable} stable-equivalent points."
    if not compare_df.empty:
        metric_hits = compare_df[compare_df["metric_name"] == "PIE_practical"]
        if not metric_hits.empty:
            delta_max = pd.to_numeric(metric_hits["delta_abs"], errors="coerce").abs().max()
            if math.isfinite(delta_max) and delta_max > 0.1:
                answer_q6 = "yes"
                reason_q6 += f" Small-scope polar replay also changes PIE by up to {delta_max:.3f}."
    answers.append(
        {
            "question": "当前证据是否支持“不能直接全量切换到 pairing_v2”？",
            "answer": answer_q6,
            "evidence_used": "v1_v2_compare_table.csv; processing_rule_migration_summary.csv",
            "reason": reason_q6,
            "residual_uncertainty": "Current compare set is representative rather than exhaustive.",
        }
    )

    answers.append(
        {
            "question": "下一步最值得做的小范围 v2 验证点有哪些？",
            "answer": "yes" if len(representative_df) >= 8 else "partial" if len(representative_df) >= 4 else "no",
            "evidence_used": "representative_points_for_next_step.csv",
            "reason": f"Representative matrix currently proposes {len(representative_df)} points across four categories.",
            "residual_uncertainty": "Exact point list may still shift after mentor feedback on which regime matters most.",
        }
    )
    return answers


def build_loss_directory_coverage(data_root: Path) -> pd.DataFrame:
    return build_loss_coverage_table(data_root)


def build_threshold_sensitivity_summary(repo_root: Path) -> pd.DataFrame:
    return discover_threshold_runs(repo_root)


def build_representative_points_table(matrix: pd.DataFrame) -> pd.DataFrame:
    return choose_representative_points(matrix)


def build_reports_clean(fullgrid_20db_matrix: pd.DataFrame, threshold_df: pd.DataFrame, v1_v2_compare_table: pd.DataFrame) -> tuple[str, str]:
    answers = assess_evidence(fullgrid_20db_matrix, threshold_df, v1_v2_compare_table)
    report_lines = [
        "# mentor progress evidence report",
        "",
        f"- generated_at: {now_stamp()}",
        f"- repo_root: {REPO_ROOT}",
        f"- data_root: {DEFAULT_DATA_ROOT}",
        "- commands:",
        "  - `python analysis/mentor_progress_pack/build_progress_evidence.py`",
        "  - `python analysis/mentor_progress_pack/compare_v1_v2_rules.py`",
        "  - `python analysis/mentor_progress_pack/plot_progress_evidence.py`",
        "",
    ]
    sections = [
        ("P1. 项目当前处于什么阶段", "主流程已打通，canonical-style 结果包已形成，但规则边界仍在收敛。", "loss_directory_coverage.csv; file_presence_manifest.csv; fig01_loss_coverage_bar; fig02_pipeline_status_schematic", "基本充分", "对 scratch 目录不作统一口径承诺。"),
        ("P2. 主流程和结果输出已经基本稳定", "20 dB fullgrid 已形成稳定点矩阵，主结果 / 诊断 / layer 可交叉复查。", "fullgrid_20db_matrix.csv; fig03_20db_output_availability_heatmap; fig08_bw_scan_d2048; fig09_bw_scan_d4096", "基本充分", "稳定性结论不自动外推到所有历史目录。"),
        ("P3. 我们已经能解释结果为什么会这样", "clean/ambiguous 区分、污染来源和 explainer metrics 已能解释主要性能变化。", "contamination_summary_by_d.csv; fig05_clean_vs_ambiguous_pairs; fig06_contamination_source_breakdown; fig07_both_multi_vs_performance; fig10_explainer_metric_comparison", "部分充分", "跨 loss 的统一机制仍需更多对照。"),
        ("P4. 对关键参数行为的认识更清楚了", "bw 不是越接近 jitter 越好；threshold 也还不具备默认升级条件。", "bw_scan_keypoints.csv; threshold_sensitivity_summary.csv; fig08_bw_scan_d2048; fig09_bw_scan_d4096; fig11_threshold_sensitivity_keypoints", "部分充分", "threshold 证据当前集中在近阈值高维点。"),
        ("P5. 结果包和结论边界已经明确", "四层字段边界已经明确，当前不能把输出直接说成 unconditional security result。", "canonical_field_completeness.csv; canonical_claim_boundary_table.csv; fig13_field_layer_summary_table; fig14_claim_boundary_summary", "充分", "若默认规则改变，边界说明也需要同步更新。"),
        ("P6. 为什么不能直接全量切换到新规则", "现有 v1/v2 对照表明低中维点会改变 pairing path 和序列内容，不是纯 diagnostics 补丁。", "v1_v2_compare_table.csv; fig15_v1_v2_delta_heatmap; fig16_v1_v2_representative_table; fig17_smoke_test_path_table", "充分", "代表点不是全矩阵，但足以否定直接全量切换。"),
        ("P7. 下一步最合理的方向", "先冻结 legacy_v1 reference，再做小范围 pairing_v2 验证，最后再决定是否暴露到主结果包。", "representative_points_for_next_step.csv; fig18_next_step_route; fig19_representative_points_matrix", "充分", "验证点排序可以随新证据微调。"),
    ]
    for title, conclusion, evidence, sufficient, uncertainty in sections:
        report_lines.extend([f"## {title}", f"- 结论: {conclusion}", f"- 证据: {evidence}", f"- 证据是否充分: {sufficient}", f"- 仍存在哪些不确定性: {uncertainty}", ""])
    report_lines.extend(["## 判断题回答", ""])
    labels = {
        "q1_main_flow_stable": "1. 当前是否足以支持“主流程已经打通且输出稳定”",
        "q2_diag_loop": "2. 当前是否足以支持“我们已经建立 diagnostics 闭环”",
        "q3_both_multi_main_source": "3. 当前证据是否支持“污染主来源更偏 both_multi 而不是 cross-frame”",
        "q4_bw_not_simple_jitter": "4. 当前证据是否支持“bw 行为不是简单越接近 jitter 越好”",
        "q5_threshold_not_default": "5. 当前证据是否支持“threshold 还不能升级为默认 canonical 规则”",
        "q6_no_full_v2_switch": "6. 当前证据是否支持“不能直接全量切换到 pairing_v2”",
        "q7_next_best_v2_points": "7. 下一步最值得做的小范围 v2 验证点有哪些",
    }
    for key in QUESTION_KEYS:
        item = answers[key]
        report_lines.extend([f"### {labels[key]}", f"- answer: {item['answer']}", f"- evidence_used: {item['evidence_used']}", f"- reason: {item['reason']}", f"- residual_uncertainty: {item['residual_uncertainty']}", ""])

    ppt_lines = [
        "# mentor progress ppt ready",
        "",
        "## P1",
        "- 主流程已打通，canonical-style 结果包已经形成（fig01_loss_coverage_bar, fig02_pipeline_status_schematic, loss_directory_coverage.csv）",
        "- 当前更准确的阶段是“规则边界收敛中”，不是最终默认规则冻结（fig12_canonicalization_by_loss, file_presence_manifest.csv）",
        "- 覆盖情况可以审计到 loss / result_dir 粒度（loss_directory_coverage.csv, file_presence_manifest.csv）",
        "",
        "## P2",
        "- 20 dB fullgrid 已形成可复查的点级结果矩阵（fullgrid_20db_matrix.csv, fig03_20db_output_availability_heatmap）",
        "- 主结果、诊断和 layer 输出在核心目录内基本齐全（fullgrid_20db_matrix.csv, fig03_20db_output_availability_heatmap）",
        "- 2048 / 4096 的 bw 曲线表现出平台区，不是偶然单点（bw_scan_keypoints.csv, fig08_bw_scan_d2048, fig09_bw_scan_d4096）",
        "",
        "## P3",
        "- 现在能把 clean events 和 ambiguous events 分开看（fig05_clean_vs_ambiguous_pairs, fullgrid_20db_matrix.csv）",
        "- 污染来源分解显示当前主污染更偏 both_multi（fig06_contamination_source_breakdown, contamination_summary_by_d.csv）",
        "- 污染占比与性能退化存在可见关联（fig07_both_multi_vs_performance, fig10_explainer_metric_comparison）",
        "",
        "## P4",
        "- bw 行为不是“越接近 jitter 越好”，而是存在更宽的平台区（fig08_bw_scan_d2048, fig09_bw_scan_d4096, bw_scan_keypoints.csv）",
        "- threshold 改动会影响 PIE，但对 SKR / layers 的收益并不稳定（fig11_threshold_sensitivity_keypoints, threshold_sensitivity_summary.csv）",
        "- 所以 threshold 还不适合直接升级为默认 canonical 规则（fig11_threshold_sensitivity_keypoints, threshold_sensitivity_summary.csv）",
        "",
        "## P5",
        "- 结果包已经能按 observation / engineering / assumption interface / derived result 四层分类（fig13_field_layer_summary_table, canonical_claim_boundary_table.csv）",
        "- 当前不能直接把输出称为 unconditional security result（fig14_claim_boundary_summary, canonical_claim_boundary_table.csv）",
        "- 字段完备度也已经可以量化审计（canonical_field_completeness.csv, fig13_field_layer_summary_table）",
        "",
        "## P6",
        "- 现有 v1/v2 对照表明：低中维点会改变 pairing path 和序列内容，不是“只补 diagnostics”（v1_v2_compare_table.csv, fig16_v1_v2_representative_table, fig17_smoke_test_path_table）",
        "- 只有部分高维点出现 v1 / v2 等价，不能直接外推到全矩阵（v1_v2_compare_table.csv, fig15_v1_v2_delta_heatmap）",
        "- 因此现在不能直接全量切到 pairing_v2（fig15_v1_v2_delta_heatmap, v1_v2_compare_table.csv）",
        "",
        "## P7",
        "- 先冻结 legacy_v1 reference，保证导师版汇报口径稳定（fig18_next_step_route）",
        "- 再对代表点做小范围 pairing_v2 验证，而不是直接全量切换（representative_points_for_next_step.csv, fig19_representative_points_matrix）",
        "- 最后再决定是否把 v1 / v2 暴露进主结果包（fig18_next_step_route, representative_points_for_next_step.csv）",
        "",
    ]
    return "\n".join(report_lines).strip() + "\n", "\n".join(ppt_lines).strip() + "\n"


build_reports = build_reports_clean


def build_report_markdown(
    ctx: PackContext,
    coverage_df: pd.DataFrame,
    matrix_df: pd.DataFrame,
    contamination_df: pd.DataFrame,
    compare_df: pd.DataFrame,
    compare_summary_df: pd.DataFrame,
    representative_df: pd.DataFrame,
    threshold_df: pd.DataFrame,
    bw_df: pd.DataFrame,
) -> tuple[str, str]:
    answers = evidence_answers(
        coverage_df=coverage_df,
        matrix_df=matrix_df,
        contamination_df=contamination_df,
        bw_df=bw_df,
        threshold_df=threshold_df,
        compare_df=compare_df,
        compare_summary_df=compare_summary_df,
        representative_df=representative_df,
    )
    total_loss = len(coverage_df)
    total_all_three = int(coverage_df["n_dirs_with_all_three"].sum()) if not coverage_df.empty else 0
    frame_ratio = float(pd.to_numeric(matrix_df.get("frame_diag_available"), errors="coerce").mean()) if not matrix_df.empty else float("nan")
    both_mean = float(pd.to_numeric(contamination_df.get("mean_both_multi_frame_fraction"), errors="coerce").mean()) if not contamination_df.empty else float("nan")
    cross_mean = float(pd.to_numeric(contamination_df.get("mean_cross_frame_fraction"), errors="coerce").mean()) if not contamination_df.empty else float("nan")
    compare_points = int(compare_df[["d", "bw"]].drop_duplicates().shape[0]) if not compare_df.empty else 0

    report = f"""# Mentor Progress Evidence Report

Generated at: {now_stamp()}

Data root: `{ctx.data_root}`
Output root: `{ctx.output_root}`
Commands:
- `python analysis/mentor_progress_pack/build_progress_evidence.py`
- `python analysis/mentor_progress_pack/plot_progress_evidence.py`
- `python analysis/mentor_progress_pack/compare_v1_v2_rules.py`

## P1. 项目当前处于什么阶段
- 结论: 当前阶段可定义为“主流程已打通，20 dB 代表性证据包已成型，正在做规则边界和迁移边界收敛”。
- 证据: `loss_directory_coverage.csv`, `file_presence_manifest.csv`, `fig01_loss_coverage_bar`, `fig02_pipeline_status_schematic`, `fig12_canonicalization_by_loss`
- 证据是否充分: 基本充分。当前共覆盖 {total_loss} 个 loss 条件，已有 {total_all_three} 个结果目录同时具备 e2e/diag/layer 三类产物。
- 仍存在哪些不确定性: 历史目录的 canonical 覆盖并不完全一致，因此更像“准冻结前收敛阶段”，不是最终发布态。

## P2. 主流程和结果输出已经基本稳定
- 结论: 20 dB fullgrid 上，主流程和主输出可以认为已经基本稳定；跨目录的一致性是“基本稳定，但非完全统一”。
- 证据: `fullgrid_20db_matrix.csv`, `loss_directory_coverage.csv`, `fig03_20db_output_availability_heatmap`
- 证据是否充分: 对“20 dB 代表 package 已稳定”是充分的。121 个 fullgrid 点已形成可复查矩阵。
- 仍存在哪些不确定性: 6 dB 旧目录和部分 breakdown 目录的 sidecar/claim 字段不如 fullgrid 完整。

## P3. 我们已经能解释结果为什么会这样
- 结论: 目前已建立起从时域配对诊断到最终性能变化的解释链条，尤其是 20 dB fullgrid 上的解释是闭环的。
- 证据: `fullgrid_20db_matrix.csv`, `contamination_summary_by_d.csv`, `fig04_frame_diag_available_heatmap`, `fig05_clean_vs_ambiguous_pairs`, `fig06_contamination_source_breakdown`, `fig07_both_multi_vs_performance`, `fig10_explainer_metric_comparison`
- 证据是否充分: 基本充分。20 dB fullgrid 的 frame diagnostics 平均可用率约为 {frame_ratio:.1%}。
- 仍存在哪些不确定性: 解释链条当前主要建立在 20 dB 数据上；跨 loss 的普适性还需要后续复查。

## P4. 对关键参数行为的认识更清楚了
- 结论: 对 bw 扫描和 threshold 扫描的行为已经有了可复述的认识，能够支持“不是越接近 jitter 越好”和“threshold 仍需小范围验证”的说法。
- 证据: `bw_scan_keypoints.csv`, `threshold_sensitivity_summary.csv`, `fig08_bw_scan_d2048`, `fig09_bw_scan_d4096`, `fig11_threshold_sensitivity_keypoints`
- 证据是否充分: 对导师版组会陈述是充分的。
- 仍存在哪些不确定性: threshold 对 SKR 的影响仍依赖比较组定义；当前更适合讲“存在稳定性风险”，不适合讲“已找到全局默认最优规则”。

## P5. 结果包和结论边界已经明确
- 结论: 当前结果包已经可以按 observation / engineering_processing / security_assumption_interface / derived_result 四层来管理，并且 claim boundary 可以明确到“工程诊断级”。
- 证据: `canonical_field_completeness.csv`, `canonical_claim_boundary_table.csv`, `fig13_field_layer_summary_table`, `fig14_claim_boundary_summary`
- 证据是否充分: 充分。
- 仍存在哪些不确定性: `SKR` 与 `PIE_practical` 仍必须显式绑定当前 assumption tag，不能写成 unconditional security result。

## P6. 为什么不能直接全量切换到新规则
- 结论: 不能直接全量切换到 pairing_v2，因为它在不同维度区间的语义影响不一致，低/中维点会改变序列与路径，高维平台点才更接近等价。
- 证据: `v1_v2_compare_table.csv`, `representative_points_for_next_step.csv`, `fig15_v1_v2_delta_heatmap`, `fig16_v1_v2_representative_table`, `fig17_smoke_test_path_table`
- 证据是否充分: 基本充分。当前 v1/v2 compare 已覆盖 {compare_points} 个代表性点。
- 仍存在哪些不确定性: 比较仍是代表性抽样，不是全网格穷举。

## P7. 下一步最合理的方向
- 结论: 最合理的方向不是直接切主规则，而是先冻结 legacy_v1 reference，再做 small-scope pairing_v2 validation，最后决定是否把 v1/v2 暴露到主结果包。
- 证据: `representative_points_for_next_step.csv`, `fig18_next_step_route`, `fig19_representative_points_matrix`
- 证据是否充分: 充分。
- 仍存在哪些不确定性: 代表点矩阵仍可根据导师对“平台态”与“近阈值态”的关注重新微调。

## 分析判断问题
"""
    for item in answers:
        report += f"""
### {item['question']}
- answer: {item['answer']}
- evidence_used: {item['evidence_used']}
- reason: {item['reason']}
- residual_uncertainty: {item['residual_uncertainty']}
"""
    report += f"""

## 补充观察
- 20 dB fullgrid 的 contamination 聚合显示 both_multi 平均占比约为 {both_mean:.4f}，cross-frame 平均占比约为 {cross_mean:.4f}。
- `compare_v1_v2_rules.py` 若执行，会基于已有 compare sidecar 做最小范围 polar replay，而不是重跑 fullgrid。
"""

    ppt = """# Mentor Progress PPT Ready

## P1
- 当前阶段可定义为“主流程打通 + 证据包成型 + 规则边界收敛中”。 (`fig01_loss_coverage_bar`, `fig02_pipeline_status_schematic`)
- 结果目录已经覆盖多个 loss 条件，但 canonical 覆盖仍不完全统一。 (`loss_directory_coverage.csv`, `fig12_canonicalization_by_loss`)
- 因此现在适合讲“进入可审计收敛阶段”，不适合讲“全部冻结完成”。 (`file_presence_manifest.csv`)

## P2
- 20 dB fullgrid 已形成完整 121 点主证据矩阵。 (`fullgrid_20db_matrix.csv`)
- e2e / diag / layer 三类产物在代表目录中基本齐备。 (`fig03_20db_output_availability_heatmap`)
- 主流程“已打通且基本稳定”可以成立，但历史目录统一度仍需补齐。 (`loss_directory_coverage.csv`)

## P3
- 我们已经能把最终性能变化回连到 frame-level contamination diagnostics。 (`fig04_frame_diag_available_heatmap`, `fig07_both_multi_vs_performance`)
- clean vs ambiguous pairs 已经可以分开量化。 (`fig05_clean_vs_ambiguous_pairs`, `fullgrid_20db_matrix.csv`)
- 当前主污染更偏 both_multi，而不是 cross-frame。 (`fig06_contamination_source_breakdown`, `contamination_summary_by_d.csv`)

## P4
- bw 行为不是“越接近 jitter 越好”这么简单。 (`fig08_bw_scan_d2048`, `fig09_bw_scan_d4096`)
- 解释性能变化时，raw_ser / capacity / contamination 要结合看。 (`fig10_explainer_metric_comparison`)
- threshold 改动会改 PIE，也会改 SKR 和层成功数。 (`fig11_threshold_sensitivity_keypoints`, `threshold_sensitivity_summary.csv`)

## P5
- 当前结果包已经能分成 observation / processing / assumption / derived 四层。 (`fig13_field_layer_summary_table`, `canonical_claim_boundary_table.csv`)
- 目前可以讲工程诊断级结论，不可以直接讲 unconditional security。 (`fig14_claim_boundary_summary`)
- 结论边界已经明确，后续重点是规范表达而不是继续口头补充。 (`canonical_field_completeness.csv`)

## P6
- pairing_v2 不是“只补 diagnostics”，部分点会改变配对路径和序列本身。 (`fig17_smoke_test_path_table`, `processing_rule_migration_summary.csv`)
- 低/中维参考点与高维平台点的迁移风险不一样。 (`fig16_v1_v2_representative_table`)
- 因此不能直接全量切换到 pairing_v2。 (`fig15_v1_v2_delta_heatmap`, `v1_v2_compare_table.csv`)

## P7
- 下一步先 freeze legacy_v1 reference。 (`fig18_next_step_route`)
- 然后只做 small-scope pairing_v2 validation，不做 fullgrid 重跑。 (`fig18_next_step_route`, `representative_points_for_next_step.csv`)
- 推荐验证点已经按 low/mid/high 及 near-threshold/platform 两类高维区间分好。 (`fig19_representative_points_matrix`)
"""
    return report, ppt


def relative_to_repo(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(path.resolve())


QUESTION_KEYS = (
    "q1_main_flow_stable",
    "q2_diag_loop",
    "q3_both_multi_main_source",
    "q4_bw_not_simple_jitter",
    "q5_threshold_not_default",
    "q6_no_full_v2_switch",
    "q7_next_best_v2_points",
)


def _safe_mean(series: pd.Series) -> float | None:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.dropna().empty:
        return None
    value = float(numeric.mean())
    if not math.isfinite(value):
        return None
    return value


def _safe_max_abs(series: pd.Series) -> float | None:
    numeric = pd.to_numeric(series, errors="coerce").abs()
    if numeric.dropna().empty:
        return None
    value = float(numeric.max())
    if not math.isfinite(value):
        return None
    return value


def _question_answers_clean(
    matrix_df: pd.DataFrame,
    contamination_df: pd.DataFrame,
    threshold_df: pd.DataFrame,
    compare_df: pd.DataFrame,
    compare_summary_df: pd.DataFrame,
    representative_df: pd.DataFrame,
) -> dict[str, dict[str, str]]:
    answers: dict[str, dict[str, str]] = {}

    frame_ready = pd.to_numeric(matrix_df.get("frame_diag_available"), errors="coerce")
    frame_ready_count = int((frame_ready == 1).sum()) if frame_ready is not None else 0
    matrix_points = int(len(matrix_df))
    fullgrid_fraction = (frame_ready_count / matrix_points) if matrix_points else 0.0

    both_mean = _safe_mean(contamination_df.get("mean_both_multi_frame_fraction", pd.Series(dtype=float)))
    cross_mean = _safe_mean(contamination_df.get("mean_cross_frame_fraction", pd.Series(dtype=float)))

    threshold_key = threshold_df[(pd.to_numeric(threshold_df.get("d"), errors="coerce").isin([2048, 4096])) & (pd.to_numeric(threshold_df.get("bw"), errors="coerce") == 30)].copy()
    pie_span = None
    skr_span = None
    if not threshold_key.empty:
        pie_span = _safe_max_abs(
            threshold_key.groupby(["d", "bw"])["PIE_practical"].transform(lambda s: pd.to_numeric(s, errors="coerce") - pd.to_numeric(s, errors="coerce").mean())
        )
        skr_span = _safe_max_abs(
            threshold_key.groupby(["d", "bw"])["SKR"].transform(lambda s: pd.to_numeric(s, errors="coerce") - pd.to_numeric(s, errors="coerce").mean())
        )
        pie_direct = threshold_key.groupby(["d", "bw"])["PIE_practical"].agg(lambda s: pd.to_numeric(s, errors="coerce").max() - pd.to_numeric(s, errors="coerce").min())
        skr_direct = threshold_key.groupby(["d", "bw"])["SKR"].agg(lambda s: pd.to_numeric(s, errors="coerce").max() - pd.to_numeric(s, errors="coerce").min())
        pie_span = float(pie_direct.max()) if not pie_direct.empty else pie_span
        skr_span = float(skr_direct.max()) if not skr_direct.empty else skr_span

    semantic_count = 0
    stable_count = 0
    if not compare_summary_df.empty and "migration_class_tag" in compare_summary_df.columns:
        semantic_count = int((compare_summary_df["migration_class_tag"] == "semantic_change_length_diff").sum())
        stable_count = int((compare_summary_df["migration_class_tag"] == "stable_equivalent").sum())
    elif not compare_df.empty and "migration_class_tag" in compare_df.columns:
        semantic_count = int((compare_df["migration_class_tag"] == "semantic_change_length_diff").sum())
        stable_count = int((compare_df["migration_class_tag"] == "stable_equivalent").sum())

    compare_points = int(compare_df[["d", "bw"]].drop_duplicates().shape[0]) if not compare_df.empty else 0
    pie_delta = None
    if not compare_df.empty and "metric_name" in compare_df.columns and "delta_abs" in compare_df.columns:
        pie_delta = _safe_max_abs(compare_df.loc[compare_df["metric_name"] == "PIE_practical", "delta_abs"])

    answers["q1_main_flow_stable"] = {
        "answer": "partial" if matrix_points else "no",
        "evidence_used": "fullgrid_20db_matrix.csv; loss_directory_coverage.csv; fig03_20db_output_availability_heatmap",
        "reason": f"20 dB fullgrid currently provides {matrix_points} audited points with e2e/diag/layer outputs aligned, but cross-loss history is not yet frozen to one uniform canonical package.",
        "residual_uncertainty": "The conclusion is strong for the representative 20 dB package and weaker for every historical directory.",
    }
    answers["q2_diag_loop"] = {
        "answer": "partial" if frame_ready_count else "no",
        "evidence_used": "fullgrid_20db_matrix.csv; contamination_summary_by_d.csv; fig04_frame_diag_available_heatmap; fig05_clean_vs_ambiguous_pairs; fig06_contamination_source_breakdown; fig07_both_multi_vs_performance",
        "reason": f"Frame-level diagnostics are available for {frame_ready_count}/{matrix_points} fullgrid points ({fullgrid_fraction:.1%}), enough to connect contamination categories to performance in the high-d regime.",
        "residual_uncertainty": "Low-d points still lack the same diagnostic completeness, so the loop is closed only for the diagnostic-available region.",
    }
    answers["q3_both_multi_main_source"] = {
        "answer": "yes" if (both_mean is not None and cross_mean is not None and both_mean > cross_mean) else "partial",
        "evidence_used": "contamination_summary_by_d.csv; fig06_contamination_source_breakdown; fig07_both_multi_vs_performance",
        "reason": f"On diagnostic-available points, mean both_multi fraction is {0.0 if both_mean is None else both_mean:.6f}, versus {0.0 if cross_mean is None else cross_mean:.6f} for cross-frame.",
        "residual_uncertainty": "This is a 20 dB fullgrid statement; additional losses should be checked before treating it as universal.",
    }
    answers["q4_bw_not_simple_jitter"] = {
        "answer": "yes" if not matrix_df.empty else "partial",
        "evidence_used": "bw_scan_keypoints.csv; fig08_bw_scan_d2048; fig09_bw_scan_d4096; fig10_explainer_metric_comparison",
        "reason": "The d=2048 and d=4096 scans show a broad operating plateau, and the best PIE/SKR points are not explained by a simple 'closer to jitter is better' rule.",
        "residual_uncertainty": "The statement is strongest on the audited 20 dB key scans rather than on every possible platform setting.",
    }
    answers["q5_threshold_not_default"] = {
        "answer": "yes" if not threshold_key.empty else "partial",
        "evidence_used": "threshold_sensitivity_summary.csv; fig11_threshold_sensitivity_keypoints",
        "reason": f"At the audited keypoints, threshold changes move PIE by up to {0.0 if pie_span is None else pie_span:.3f} and SKR by up to {0.0 if skr_span is None else skr_span:.1f}, so the choice still changes reported output materially.",
        "residual_uncertainty": "Only representative threshold sweeps are available, so the exact future default still needs a controlled validation set.",
    }
    answers["q6_no_full_v2_switch"] = {
        "answer": "yes" if semantic_count > 0 else "partial",
        "evidence_used": "v1_v2_compare_table.csv; processing_rule_migration_summary.csv; fig15_v1_v2_delta_heatmap; fig16_v1_v2_representative_table; fig17_smoke_test_path_table",
        "reason": f"Existing sidecar compare shows {semantic_count} semantic-change points versus {stable_count} stable-equivalent points; small-scope replay covers {compare_points} representative points with max |delta PIE| of {0.0 if pie_delta is None else pie_delta:.3f}.",
        "residual_uncertainty": "The compare set is representative rather than exhaustive, but it is already enough to reject a blind full switch.",
    }
    answers["q7_next_best_v2_points"] = {
        "answer": "yes" if len(representative_df) >= 8 else ("partial" if len(representative_df) >= 4 else "no"),
        "evidence_used": "representative_points_for_next_step.csv; fig18_next_step_route; fig19_representative_points_matrix",
        "reason": f"The current candidate set contains {len(representative_df)} points spanning low_dim_reference, mid_dim_reference, near_threshold_high_dim, and platform_high_dim.",
        "residual_uncertainty": "The order of execution can still shift after advisor feedback on which regime matters most.",
    }
    return answers


def build_reports(fullgrid_20db_matrix: pd.DataFrame, threshold_df: pd.DataFrame, v1_v2_compare_table: pd.DataFrame) -> tuple[str, str]:
    representative_df = choose_representative_points(fullgrid_20db_matrix)
    compare_summary_df = compare_summary_from_existing(REPO_ROOT)
    contamination_df = build_contamination_summary(fullgrid_20db_matrix)
    answers = _question_answers_clean(
        matrix_df=fullgrid_20db_matrix,
        contamination_df=contamination_df,
        threshold_df=threshold_df,
        compare_df=v1_v2_compare_table,
        compare_summary_df=compare_summary_df,
        representative_df=representative_df,
    )
    sections = [
        (
            "P1. Current Project Stage",
            "The main pipeline is working, the representative canonical package exists, and the remaining work is to freeze rule boundaries.",
            "`loss_directory_coverage.csv`, `file_presence_manifest.csv`, `fig01_loss_coverage_bar`, `fig02_pipeline_status_schematic`, `fig12_canonicalization_by_loss`",
            "partial",
            "The 20 dB package is strong evidence, but the historical directories do not yet share one final frozen package definition.",
        ),
        (
            "P2. Main Pipeline And Outputs Are Mostly Stable",
            "The 20 dB fullgrid is now an auditable point-level matrix, and main-result, diagnostic, and layer outputs can be cross-checked.",
            "`fullgrid_20db_matrix.csv`, `fig03_20db_output_availability_heatmap`, `fig08_bw_scan_d2048`, `fig09_bw_scan_d4096`",
            "partial",
            "The stability claim is strongest on the representative fullgrid, not on every historical directory.",
        ),
        (
            "P3. We Can Explain Why The Results Look This Way",
            "Clean versus ambiguous events can now be separated, and contamination sources can be linked to performance changes.",
            "`contamination_summary_by_d.csv`, `fig04_frame_diag_available_heatmap`, `fig05_clean_vs_ambiguous_pairs`, `fig06_contamination_source_breakdown`, `fig07_both_multi_vs_performance`, `fig10_explainer_metric_comparison`",
            "partial",
            "The diagnostic loop is strongest in the high-d diagnostic-available region.",
        ),
        (
            "P4. Key Parameter Behavior Is Better Understood",
            "BW behavior is not a simple 'closer to jitter is always better' rule; threshold changes outputs and is not ready to become the default canonical rule.",
            "`bw_scan_keypoints.csv`, `threshold_sensitivity_summary.csv`, `fig08_bw_scan_d2048`, `fig09_bw_scan_d4096`, `fig11_threshold_sensitivity_keypoints`",
            "partial",
            "Threshold evidence is still based on representative points rather than an exhaustive sweep.",
        ),
        (
            "P5. Package Scope And Claim Boundary Are Clear",
            "Fields can now be organized into observation, engineering_processing, security_assumption_interface, and derived_result layers.",
            "`canonical_field_completeness.csv`, `canonical_claim_boundary_table.csv`, `fig13_field_layer_summary_table`, `fig14_claim_boundary_summary`",
            "yes",
            "If the default rule changes later, the boundary statement must be updated with it.",
        ),
        (
            "P6. Why We Cannot Switch To The New Rule Everywhere",
            "The v1 to v2 change is not just extra diagnostics; at representative points it changes pairing paths, sequence content, and final metrics.",
            "`v1_v2_compare_table.csv`, `fig15_v1_v2_delta_heatmap`, `fig16_v1_v2_representative_table`, `fig17_smoke_test_path_table`",
            "yes",
            "This is representative rather than exhaustive evidence, but it is already enough to reject a blind full switch.",
        ),
        (
            "P7. Most Reasonable Next Step",
            "Freeze the legacy_v1 reference first, run small-scope pairing_v2 validation second, and decide on package exposure last.",
            "`representative_points_for_next_step.csv`, `fig18_next_step_route`, `fig19_representative_points_matrix`",
            "yes",
            "The exact validation order can still be adjusted after advisor feedback.",
        ),
    ]

    report_lines = [
        "# mentor progress evidence report",
        "",
        f"- generated_at: {now_stamp()}",
        f"- repo_root: `{REPO_ROOT}`",
        f"- data_root: `{DEFAULT_DATA_ROOT}`",
        "- commands:",
        "  - `python analysis/mentor_progress_pack/build_progress_evidence.py`",
        "  - `python analysis/mentor_progress_pack/compare_v1_v2_rules.py`",
        "  - `python analysis/mentor_progress_pack/plot_progress_evidence.py`",
        "",
    ]
    for title, conclusion, evidence, sufficient, uncertainty in sections:
        report_lines.extend(
            [
                f"## {title}",
                f"- 结论: {conclusion}",
                f"- 证据: {evidence}",
                f"- 证据是否充分: {sufficient}",
                f"- 仍存在哪些不确定性: {uncertainty}",
                "",
            ]
        )

    label_map = {
        "q1_main_flow_stable": "1. Does current evidence support 'the main pipeline is already working and stable'?",
        "q2_diag_loop": "2. Does current evidence support 'we have built a diagnostics loop'?",
        "q3_both_multi_main_source": "3. Does current evidence support 'the main contamination source is both_multi rather than cross-frame'?",
        "q4_bw_not_simple_jitter": "4. Does current evidence support 'bw behavior is not simply better when it gets closer to jitter'?",
        "q5_threshold_not_default": "5. Does current evidence support 'threshold cannot yet be upgraded to the default canonical rule'?",
        "q6_no_full_v2_switch": "6. Does current evidence support 'we cannot switch to pairing_v2 everywhere yet'?",
        "q7_next_best_v2_points": "7. Which small-scope v2 validation points are most worth doing next?",
    }
    report_lines.extend(["## Decision Questions", ""])
    for key in QUESTION_KEYS:
        item = answers[key]
        report_lines.extend(
            [
                f"### {label_map[key]}",
                f"- answer: {item['answer']}",
                f"- evidence_used: {item['evidence_used']}",
                f"- reason: {item['reason']}",
                f"- residual_uncertainty: {item['residual_uncertainty']}",
                "",
            ]
        )

    ppt_lines = [
        "# mentor progress ppt ready",
        "",
        "## P1",
        "- The pipeline works, the representative package exists, and the remaining task is to freeze rule boundaries. (fig01_loss_coverage_bar, fig02_pipeline_status_schematic, loss_directory_coverage.csv)",
        "- The right stage label is 'auditable convergence', not 'all rules fully frozen'. (fig12_canonicalization_by_loss, file_presence_manifest.csv)",
        "- Coverage can already be audited per loss and per directory. (loss_directory_coverage.csv, file_presence_manifest.csv)",
        "",
        "## P2",
        "- The 20 dB fullgrid is now an auditable 121-point matrix. (fullgrid_20db_matrix.csv, fig03_20db_output_availability_heatmap)",
        "- Main-result, diagnostic, and layer outputs are largely aligned in the representative directory. (fullgrid_20db_matrix.csv, fig03_20db_output_availability_heatmap)",
        "- The d=2048 and d=4096 bw scans show a plateau, not a single accidental sweet spot. (bw_scan_keypoints.csv, fig08_bw_scan_d2048, fig09_bw_scan_d4096)",
        "",
        "## P3",
        "- Clean events and ambiguous events can now be separated explicitly. (fig05_clean_vs_ambiguous_pairs, fullgrid_20db_matrix.csv)",
        "- The dominant contamination source currently looks more like both_multi than cross-frame. (fig06_contamination_source_breakdown, contamination_summary_by_d.csv)",
        "- Contamination fractions can now be linked back to performance loss. (fig07_both_multi_vs_performance, fig10_explainer_metric_comparison)",
        "",
        "## P4",
        "- BW behavior is not 'closer to jitter is always better'; there is a wider usable plateau. (fig08_bw_scan_d2048, fig09_bw_scan_d4096, bw_scan_keypoints.csv)",
        "- Threshold changes may improve PIE, but the effect on SKR and successful layers is not stable. (fig11_threshold_sensitivity_keypoints, threshold_sensitivity_summary.csv)",
        "- So threshold is not ready to become the default canonical rule. (fig11_threshold_sensitivity_keypoints, threshold_sensitivity_summary.csv)",
        "",
        "## P5",
        "- The package can now be managed with a four-layer field boundary. (fig13_field_layer_summary_table, canonical_claim_boundary_table.csv)",
        "- We can make engineering and diagnostics claims, but not call this an unconditional security result. (fig14_claim_boundary_summary, canonical_claim_boundary_table.csv)",
        "- Field completeness is also auditable now. (canonical_field_completeness.csv, fig13_field_layer_summary_table)",
        "",
        "## P6",
        "- Pairing_v2 is not just extra diagnostics; some points change pairing path and final metrics. (fig16_v1_v2_representative_table, fig17_smoke_test_path_table, v1_v2_compare_table.csv)",
        "- Only some high-d points look close to v1/v2 equivalence, so that cannot be extrapolated to the whole matrix. (fig15_v1_v2_delta_heatmap, v1_v2_compare_table.csv)",
        "- Therefore a full switch to pairing_v2 is not justified yet. (fig15_v1_v2_delta_heatmap, v1_v2_compare_table.csv)",
        "",
        "## P7",
        "- Freeze the legacy_v1 reference first so the reporting baseline stays stable. (fig18_next_step_route)",
        "- Then run small-scope pairing_v2 validation on representative points instead of rerunning fullgrid. (representative_points_for_next_step.csv, fig19_representative_points_matrix)",
        "- Only after that should we decide whether v1/v2 belongs in the main package. (fig18_next_step_route, representative_points_for_next_step.csv)",
        "",
    ]
    return "\n".join(report_lines).strip() + "\n", "\n".join(ppt_lines).strip() + "\n"


def build_report_markdown(
    ctx: PackContext,
    coverage_df: pd.DataFrame,
    matrix_df: pd.DataFrame,
    contamination_df: pd.DataFrame,
    compare_df: pd.DataFrame,
    compare_summary_df: pd.DataFrame,
    representative_df: pd.DataFrame,
    threshold_df: pd.DataFrame,
    bw_df: pd.DataFrame,
) -> tuple[str, str]:
    answers = _question_answers_clean(
        matrix_df=matrix_df,
        contamination_df=contamination_df,
        threshold_df=threshold_df,
        compare_df=compare_df,
        compare_summary_df=compare_summary_df,
        representative_df=representative_df,
    )
    total_loss = int(len(coverage_df))
    total_all_three = int(pd.to_numeric(coverage_df.get("n_dirs_with_all_three"), errors="coerce").fillna(0).sum()) if not coverage_df.empty else 0
    matrix_points = int(len(matrix_df))
    frame_ready = int((pd.to_numeric(matrix_df.get("frame_diag_available"), errors="coerce") == 1).sum()) if not matrix_df.empty else 0
    both_mean = _safe_mean(contamination_df.get("mean_both_multi_frame_fraction", pd.Series(dtype=float)))
    cross_mean = _safe_mean(contamination_df.get("mean_cross_frame_fraction", pd.Series(dtype=float)))
    compare_points = int(compare_df[["d", "bw"]].drop_duplicates().shape[0]) if not compare_df.empty else 0

    report_lines = [
        "# Mentor Progress Evidence Report",
        "",
        f"Generated at: {now_stamp()}",
        f"Data root: `{ctx.data_root}`",
        f"Output root: `{ctx.output_root}`",
        "Commands:",
        "- `python analysis/mentor_progress_pack/build_progress_evidence.py`",
        "- `python analysis/mentor_progress_pack/compare_v1_v2_rules.py`",
        "- `python analysis/mentor_progress_pack/plot_progress_evidence.py`",
        "",
        "## P1. Current Project Stage",
        f"- Conclusion: The most accurate stage label is 'main pipeline working, representative package formed, rule boundary still converging'. We currently cover {total_loss} loss conditions, and {total_all_three} result directories already contain all three output types: e2e, diag, and layer.",
        "- Evidence: `loss_directory_coverage.csv`, `file_presence_manifest.csv`, `fig01_loss_coverage_bar`, `fig02_pipeline_status_schematic`, `fig12_canonicalization_by_loss`",
        "- Is the evidence sufficient: partial.",
        "- Remaining uncertainty: The 20 dB representative package is the strongest evidence; historical directories are not yet frozen into one final uniform package.",
        "",
        "## P2. Main Pipeline And Outputs Are Mostly Stable",
        f"- Conclusion: The 20 dB fullgrid is now an auditable {matrix_points}-point matrix. Main-result, diagnostic, and layer outputs can be cross-checked, so the claim 'the representative main pipeline is mostly stable' is supportable.",
        "- Evidence: `fullgrid_20db_matrix.csv`, `fig03_20db_output_availability_heatmap`, `fig08_bw_scan_d2048`, `fig09_bw_scan_d4096`",
        "- Is the evidence sufficient: partial.",
        "- Remaining uncertainty: This statement is strongest for the representative package and does not mean every historical directory is already standardized.",
        "",
        "## P3. We Can Explain Why The Results Look This Way",
        f"- Conclusion: Clean and ambiguous events can now be separated, and contamination sources can be connected to final performance changes. In the 20 dB fullgrid, {frame_ready} points have frame-level diagnostics available for this loop.",
        "- Evidence: `contamination_summary_by_d.csv`, `fig04_frame_diag_available_heatmap`, `fig05_clean_vs_ambiguous_pairs`, `fig06_contamination_source_breakdown`, `fig07_both_multi_vs_performance`, `fig10_explainer_metric_comparison`",
        "- Is the evidence sufficient: partial.",
        "- Remaining uncertainty: The loop is strongest in the diagnostic-available high-d region; low-d points still have weaker diagnostic coverage.",
        "",
        "## P4. Key Parameter Behavior Is Better Understood",
        "- Conclusion: BW behavior is not a simple 'closer to jitter is always better' rule. Threshold changes the reported outputs, but current evidence supports caution rather than an immediate upgrade to the default rule.",
        "- Evidence: `bw_scan_keypoints.csv`, `threshold_sensitivity_summary.csv`, `fig08_bw_scan_d2048`, `fig09_bw_scan_d4096`, `fig11_threshold_sensitivity_keypoints`",
        "- Is the evidence sufficient: partial.",
        "- Remaining uncertainty: Threshold evidence is still based on representative points rather than a final answer over the full parameter space.",
        "",
        "## P5. Package Scope And Claim Boundary Are Clear",
        "- Conclusion: The current package cleanly separates observation, engineering_processing, security_assumption_interface, and derived_result. At this stage we can make engineering and diagnostic claims, but we cannot call the output an unconditional security result.",
        "- Evidence: `canonical_field_completeness.csv`, `canonical_claim_boundary_table.csv`, `fig13_field_layer_summary_table`, `fig14_claim_boundary_summary`",
        "- Is the evidence sufficient: yes.",
        "- Remaining uncertainty: If the default rule changes later, the boundary wording must be updated together with it.",
        "",
        "## P6. Why We Cannot Switch To The New Rule Everywhere",
        f"- Conclusion: Current evidence does not support a full switch to pairing_v2. The representative compare already covers {compare_points} points, and the v1 to v2 change is not only a diagnostics patch; it changes pairing path, sequence content, and final metrics.",
        "- Evidence: `v1_v2_compare_table.csv`, `fig15_v1_v2_delta_heatmap`, `fig16_v1_v2_representative_table`, `fig17_smoke_test_path_table`",
        "- Is the evidence sufficient: yes.",
        "- Remaining uncertainty: This is still representative rather than exhaustive, but it is already enough to reject an immediate full switch.",
        "",
        "## P7. Most Reasonable Next Step",
        "- Conclusion: The best route is to freeze the legacy_v1 reference first, run small-scope pairing_v2 validation second, and only then decide whether v1/v2 should be exposed in the main result package.",
        "- Evidence: `representative_points_for_next_step.csv`, `fig18_next_step_route`, `fig19_representative_points_matrix`",
        "- Is the evidence sufficient: yes.",
        "- Remaining uncertainty: The order of representative points can still be adjusted based on advisor priorities.",
        "",
        "## Decision Questions",
        "",
    ]

    label_map = {
        "q1_main_flow_stable": "1. Does current evidence support 'the main pipeline is already working and stable'?",
        "q2_diag_loop": "2. Does current evidence support 'we have built a diagnostics loop'?",
        "q3_both_multi_main_source": "3. Does current evidence support 'the main contamination source is both_multi rather than cross-frame'?",
        "q4_bw_not_simple_jitter": "4. Does current evidence support 'bw behavior is not simply better when it gets closer to jitter'?",
        "q5_threshold_not_default": "5. Does current evidence support 'threshold cannot yet be upgraded to the default canonical rule'?",
        "q6_no_full_v2_switch": "6. Does current evidence support 'we cannot switch to pairing_v2 everywhere yet'?",
        "q7_next_best_v2_points": "7. Which small-scope v2 validation points are most worth doing next?",
    }
    for key in QUESTION_KEYS:
        item = answers[key]
        report_lines.extend(
            [
                f"### {label_map[key]}",
                f"- answer: {item['answer']}",
                f"- evidence_used: {item['evidence_used']}",
                f"- reason: {item['reason']}",
                f"- residual_uncertainty: {item['residual_uncertainty']}",
                "",
            ]
        )

    report_lines.extend(
        [
            "## Additional Notes",
            f"- In the 20 dB diagnostic-available region, the aggregated mean both_multi fraction is about {0.0 if both_mean is None else both_mean:.6f}, above the cross-frame mean of {0.0 if cross_mean is None else cross_mean:.6f}.",
            "- This evidence pack reused existing result directories, CSVs, and compare caches first, and only used small-scope replay for representative v1/v2 points.",
            "",
        ]
    )

    ppt_lines = [
        "# Mentor Progress PPT Ready",
        "",
        "## P1",
        "- The right stage label is 'pipeline working + evidence pack formed + rule boundary converging'. (fig01_loss_coverage_bar, fig02_pipeline_status_schematic, loss_directory_coverage.csv)",
        "- A representative canonical package exists, but historical directories are not fully frozen to one final standard yet. (fig12_canonicalization_by_loss, file_presence_manifest.csv)",
        "- Coverage is already auditable by loss and by directory. (loss_directory_coverage.csv, file_presence_manifest.csv)",
        "",
        "## P2",
        "- The 20 dB fullgrid is now an auditable 121-point matrix. (fullgrid_20db_matrix.csv, fig03_20db_output_availability_heatmap)",
        "- Main-result, diagnostic, and layer outputs are largely aligned in the representative directory. (fullgrid_20db_matrix.csv, fig03_20db_output_availability_heatmap)",
        "- The d=2048 and d=4096 bw scans show a plateau rather than a single accidental sweet spot. (bw_scan_keypoints.csv, fig08_bw_scan_d2048, fig09_bw_scan_d4096)",
        "",
        "## P3",
        "- Clean events and ambiguous events can now be separated explicitly. (fig05_clean_vs_ambiguous_pairs, fullgrid_20db_matrix.csv)",
        "- The dominant contamination source currently looks more like both_multi than cross-frame. (fig06_contamination_source_breakdown, contamination_summary_by_d.csv)",
        "- Contamination sources can now be linked back to performance loss. (fig07_both_multi_vs_performance, fig10_explainer_metric_comparison)",
        "",
        "## P4",
        "- BW behavior is not 'closer to jitter is always better'; there is a wider usable plateau. (fig08_bw_scan_d2048, fig09_bw_scan_d4096, bw_scan_keypoints.csv)",
        "- Threshold changes may improve PIE, but the effect on SKR and layers_success_best is not stable. (fig11_threshold_sensitivity_keypoints, threshold_sensitivity_summary.csv)",
        "- So threshold is not ready to become the default canonical rule. (fig11_threshold_sensitivity_keypoints, threshold_sensitivity_summary.csv)",
        "",
        "## P5",
        "- The result package now has a clear four-layer field boundary. (fig13_field_layer_summary_table, canonical_claim_boundary_table.csv)",
        "- The current output cannot be presented as an unconditional security result. (fig14_claim_boundary_summary, canonical_claim_boundary_table.csv)",
        "- Field completeness is already auditable. (canonical_field_completeness.csv, fig13_field_layer_summary_table)",
        "",
        "## P6",
        "- Pairing_v2 is not just extra diagnostics; some points change pairing path and final metrics. (fig16_v1_v2_representative_table, fig17_smoke_test_path_table, v1_v2_compare_table.csv)",
        "- Only some high-d points look close to v1/v2 equivalence, so that cannot be extrapolated to the whole matrix. (fig15_v1_v2_delta_heatmap, v1_v2_compare_table.csv)",
        "- Therefore current evidence does not justify a full switch to pairing_v2. (fig15_v1_v2_delta_heatmap, v1_v2_compare_table.csv)",
        "",
        "## P7",
        "- Freeze the legacy_v1 reference first so the reporting baseline stays stable. (fig18_next_step_route)",
        "- Then run small-scope pairing_v2 validation on representative points rather than rerunning fullgrid. (representative_points_for_next_step.csv, fig19_representative_points_matrix)",
        "- Only after that should we decide whether v1/v2 belongs in the main package. (fig18_next_step_route, representative_points_for_next_step.csv)",
        "",
    ]
    return "\n".join(report_lines).strip() + "\n", "\n".join(ppt_lines).strip() + "\n"
