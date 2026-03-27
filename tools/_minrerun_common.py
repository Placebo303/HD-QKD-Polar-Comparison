from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from _security_round_common import REPO_ROOT, ensure_output_dir, point_id, write_summary

KEY_COLS = ["loss_db", "dimension", "bin_width_ps"]
FRESH_ROOT = REPO_ROOT / "results" / "_tmp_longrun_fresh_rerun"
FRESH_LOSS_ORDER = [20, 16, 10, 6]
ABS_EPS = 1e-9


def fresh_loss_root(loss_db: int) -> Path:
    return FRESH_ROOT / f"full_{int(loss_db)}dB"


def fresh_candidate_dir(loss_db: int) -> Path:
    return fresh_loss_root(loss_db) / "candidate_rerun"


def fresh_stage1_dir(loss_db: int) -> Path:
    return fresh_loss_root(loss_db) / "stage1_actual_ir"


def fresh_stage2_dir(loss_db: int) -> Path:
    return fresh_loss_root(loss_db) / "stage2_security"


def existing_fresh_losses() -> list[int]:
    return [loss for loss in FRESH_LOSS_ORDER if fresh_loss_root(loss).exists()]


def csv_read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def safe_float(v: Any) -> float | None:
    try:
        fv = float(v)
    except Exception:
        return None
    if not math.isfinite(fv):
        return None
    return fv


def safe_int(v: Any) -> int | None:
    fv = safe_float(v)
    if fv is None:
        return None
    return int(fv)


def normalize_verification_source_tag(tag: Any, bits: Any) -> str:
    t = str(tag or "").strip().lower()
    b = safe_float(bits)
    if t in {"configured_crc_budget", "configured_budget", "ok_configured_crc_budget"}:
        return "configured_budget"
    if t in {"actual_zero", "actual_replay", "ok_actual_zero"}:
        return "actual_replay"
    if b is not None and abs(b) <= ABS_EPS:
        return "actual_replay"
    return "missing"


def sidecar_root(candidate_dir: Path, dimension: int, bin_width_ps: int) -> Path:
    return candidate_dir / "sidecars" / f"d{int(dimension)}_bw{int(bin_width_ps)}" / "blk0"


def occupancy_summary_path(candidate_dir: Path, dimension: int, bin_width_ps: int) -> Path:
    return sidecar_root(candidate_dir, dimension, bin_width_ps) / "occupancy_filter_summary.csv"


def load_occupancy_summary(candidate_dir: Path, dimension: int, bin_width_ps: int) -> dict[str, Any]:
    path = occupancy_summary_path(candidate_dir, dimension, bin_width_ps)
    if not path.exists():
        return {"_path": "MISSING", "_available": False}
    try:
        df = pd.read_csv(path)
    except Exception:
        return {"_path": str(path), "_available": False}
    if df.empty:
        return {"_path": str(path), "_available": False}
    row = df.iloc[0].to_dict()
    row["_path"] = str(path)
    row["_available"] = True
    return row


def load_stage1_tables(stage1_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    block_df = csv_read(stage1_dir / "actual_ir_block_table.csv")
    point_df = csv_read(stage1_dir / "actual_ir_point_table.csv")
    for frame in (block_df, point_df):
        for col in KEY_COLS:
            if col in frame.columns:
                frame[col] = pd.to_numeric(frame[col], errors="coerce").astype(int)
    return block_df, point_df


def load_stage2_master(stage2_dir: Path) -> pd.DataFrame:
    path = stage2_dir / "security_calibrated_master_table.csv"
    if not path.exists():
        path = stage2_dir / "round2_security_master_table.csv"
    df = csv_read(path)
    for col in KEY_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype(int)
    return df


def load_stage2_audit(stage2_dir: Path) -> pd.DataFrame:
    df = csv_read(stage2_dir / "finite_key_audit_point_table.csv")
    for col in KEY_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype(int)
    return df


def candidate_point_frame(candidate_dir: Path) -> pd.DataFrame:
    df = csv_read(candidate_dir / "polar_e2e_results.csv")
    for col in KEY_COLS[1:]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype(int)
    loss_db = safe_int(df.get("loss_db", pd.Series([np.nan])).iloc[0])
    if loss_db is None:
        stem = str(candidate_dir).lower()
        for maybe in (20, 16, 10, 6):
            if f"{maybe}db" in stem:
                loss_db = maybe
                break
    df["loss_db"] = int(loss_db)
    df["point_id"] = df.apply(lambda r: point_id(loss_db=int(r["loss_db"]), dimension=int(r["dimension"]), bin_width_ps=int(r["bin_width_ps"])), axis=1)
    return df


def build_frame_audit_from_candidate(candidate_dir: Path, point_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for _, row in point_df.iterrows():
        loss_db = int(row["loss_db"])
        d = int(row["dimension"])
        bw = int(row["bin_width_ps"])
        occ = load_occupancy_summary(candidate_dir, d, bw)
        if occ.get("_available"):
            candidate_frame_count = safe_int(occ.get("n_frames_total"))
            accepted_frame_count = safe_int(occ.get("n_frames_clean_single_single"))
            rejected_frame_count = None
            if candidate_frame_count is not None and accepted_frame_count is not None:
                rejected_frame_count = max(0, candidate_frame_count - accepted_frame_count)
            accepted_frame_fraction = None
            rejected_frame_fraction = None
            if candidate_frame_count and candidate_frame_count > 0 and accepted_frame_count is not None:
                accepted_frame_fraction = float(accepted_frame_count) / float(candidate_frame_count)
                rejected_frame_fraction = float(rejected_frame_count) / float(candidate_frame_count) if rejected_frame_count is not None else None
            source_tag = "actual_sidecar_occupancy_summary"
            frame_success_rate = accepted_frame_fraction
            frame_success_rate_source_tag = source_tag
        else:
            candidate_frame_count = None
            accepted_frame_count = None
            rejected_frame_count = None
            accepted_frame_fraction = None
            rejected_frame_fraction = None
            source_tag = "missing"
            frame_success_rate = None
            frame_success_rate_source_tag = "missing"
        rows.append(
            {
                "loss_db": loss_db,
                "dimension": d,
                "bin_width_ps": bw,
                "point_id": str(row["point_id"]),
                "candidate_frame_count": candidate_frame_count if candidate_frame_count is not None else "MISSING",
                "accepted_frame_count": accepted_frame_count if accepted_frame_count is not None else "MISSING",
                "rejected_frame_count": rejected_frame_count if rejected_frame_count is not None else "MISSING",
                "accepted_frame_fraction": accepted_frame_fraction if accepted_frame_fraction is not None else np.nan,
                "rejected_frame_fraction": rejected_frame_fraction if rejected_frame_fraction is not None else np.nan,
                "frame_success_count": accepted_frame_count if accepted_frame_count is not None else "MISSING",
                "frame_success_rate": frame_success_rate if frame_success_rate is not None else np.nan,
                "accepted_frame_fraction_source_tag": source_tag,
                "frame_success_rate_source_tag": frame_success_rate_source_tag,
                "occupancy_summary_path": occ.get("_path", "MISSING"),
                "n_frames_cross_frame": safe_int(occ.get("n_frames_cross_frame")) if occ.get("_available") else "MISSING",
                "n_frames_a_multi": safe_int(occ.get("n_frames_A_multi")) if occ.get("_available") else "MISSING",
                "n_frames_b_multi": safe_int(occ.get("n_frames_B_multi")) if occ.get("_available") else "MISSING",
                "n_frames_both_multi": safe_int(occ.get("n_frames_both_multi")) if occ.get("_available") else "MISSING",
            }
        )
    return pd.DataFrame(rows).sort_values(KEY_COLS).reset_index(drop=True)


def recompute_finite_key(master_old: pd.DataFrame, audit_old: pd.DataFrame, frame_point: pd.DataFrame) -> pd.DataFrame:
    if "point_id" not in audit_old.columns:
        audit_old = audit_old.copy()
        audit_old["point_id"] = audit_old.apply(
            lambda r: point_id(loss_db=int(r["loss_db"]), dimension=int(r["dimension"]), bin_width_ps=int(r["bin_width_ps"])),
            axis=1,
        )
    if "point_id" not in master_old.columns:
        master_old = master_old.copy()
        master_old["point_id"] = master_old.apply(
            lambda r: point_id(loss_db=int(r["loss_db"]), dimension=int(r["dimension"]), bin_width_ps=int(r["bin_width_ps"])),
            axis=1,
        )
    df = audit_old.merge(frame_point, on=KEY_COLS + ["point_id"], how="left", suffixes=("", "_frame"))
    accepted_col = "accepted_frame_fraction_frame" if "accepted_frame_fraction_frame" in df.columns else "accepted_frame_fraction"
    rejected_col = "rejected_frame_fraction_frame" if "rejected_frame_fraction_frame" in df.columns else "rejected_frame_fraction"
    accepted_source_col = "accepted_frame_fraction_source_tag_frame" if "accepted_frame_fraction_source_tag_frame" in df.columns else "accepted_frame_fraction_source_tag"
    frame_rate_source_col = "frame_success_rate_source_tag_frame" if "frame_success_rate_source_tag_frame" in df.columns else "frame_success_rate_source_tag"
    accepted_count_col = "accepted_frame_count"
    rejected_count_col = "rejected_frame_count"
    candidate_count_col = "candidate_frame_count"
    frame_success_count_col = "frame_success_count"
    verification_bits_col = "verification_bits_used_actual"
    verification_source_col = "verification_source_tag"

    accepted = pd.to_numeric(df[accepted_col], errors="coerce")
    frame_rate = pd.to_numeric(df["frame_success_rate"], errors="coerce")
    block_rate = pd.to_numeric(df["block_success_rate_used"], errors="coerce")
    coincidence = pd.to_numeric(df["coincidence_rate_hz"], errors="coerce")
    n_pairs = pd.to_numeric(df["n_pairs_actual"], errors="coerce")
    layer_fraction = pd.to_numeric(df["layer_fraction"], errors="coerce")
    eps_sec = pd.to_numeric(df["eps_sec"], errors="coerce")
    eps_cor = pd.to_numeric(df["eps_cor"], errors="coerce")
    accepted_rate_proxy = coincidence * accepted * block_rate
    n_eff_pairs = n_pairs * layer_fraction * accepted * block_rate
    delta_fk = np.where(
        (n_eff_pairs > 0) & np.isfinite(n_eff_pairs),
        4.0 * np.sqrt(np.log2(2.0 / eps_sec) / n_eff_pairs) + 2.0 * np.log2(2.0 / eps_cor) / n_eff_pairs,
        np.nan,
    )
    post_sel = accepted

    verification_bits_used_actual = pd.to_numeric(df.get("verification_bits_used_actual"), errors="coerce")
    pie_actual = np.maximum(
        0.0,
        pd.to_numeric(df["IAB_est"], errors="coerce")
        - pd.to_numeric(df["leak_EC_actual_bits"], errors="coerce")
        - pd.to_numeric(df["chi_E_calibrated"], errors="coerce")
        - delta_fk
        - post_sel.fillna(0.0),
    )
    beta = pd.to_numeric(master_old.get("beta_baseline", 0.90), errors="coerce").fillna(0.90)
    pie_beta = np.maximum(
        0.0,
        beta * pd.to_numeric(df["IAB_est"], errors="coerce")
        - pd.to_numeric(df["chi_E_calibrated"], errors="coerce")
        - delta_fk
        - post_sel.fillna(0.0),
    )
    skr_actual = pie_actual * accepted_rate_proxy
    skr_beta = pie_beta * accepted_rate_proxy

    out = master_old.merge(df[KEY_COLS + [
        "accepted_frame_fraction",
        "rejected_frame_fraction",
        "frame_success_rate",
        "accepted_frame_fraction_source_tag",
        "frame_success_rate_source_tag",
        "candidate_frame_count",
        "accepted_frame_count",
        "rejected_frame_count",
        "frame_success_count",
        "verification_bits_used_actual",
        "verification_source_tag",
    ]], on=KEY_COLS, how="left")
    out["accepted_frame_fraction"] = accepted
    out["rejected_frame_fraction"] = pd.to_numeric(df[rejected_col], errors="coerce")
    out["frame_success_rate"] = frame_rate
    out["accepted_frame_fraction_source_tag"] = df[accepted_source_col].astype(str)
    out["frame_success_rate_source_tag"] = df[frame_rate_source_col].astype(str)
    out["candidate_frame_count"] = df[candidate_count_col]
    out["accepted_frame_count"] = df[accepted_count_col]
    out["rejected_frame_count"] = df[rejected_count_col]
    out["frame_success_count"] = df[frame_success_count_col]
    out["verification_bits_used_actual"] = pd.to_numeric(df[verification_bits_col], errors="coerce")
    out["verification_source_tag"] = df[verification_source_col].astype(str)
    out["post_selection_correction"] = post_sel
    out["accepted_rate_proxy"] = accepted_rate_proxy
    out["n_eff_pairs"] = n_eff_pairs
    out["DeltaFK_calibrated"] = delta_fk
    out["PIE_secure_actual_ir"] = pie_actual
    out["SKR_secure_actual_ir_bps"] = skr_actual
    out["PIE_secure_beta_baseline"] = pie_beta
    out["SKR_secure_beta_baseline_bps"] = skr_beta
    return out.sort_values(KEY_COLS).reset_index(drop=True)
