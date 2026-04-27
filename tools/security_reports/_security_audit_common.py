from __future__ import annotations

import math
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
ABS_EPS = 1e-9
REL_EPS = 1e-6

LOSS_CONFIGS: dict[int, dict[str, Any]] = {
    6: {"loss_db": 6, "candidate_dir": REPO_ROOT / "results" / "e2e_6dB_fullgrid_pairing_v2_candidate"},
    10: {"loss_db": 10, "candidate_dir": REPO_ROOT / "results" / "e2e_10dB_fullgrid_pairing_v2_candidate"},
    16: {"loss_db": 16, "candidate_dir": REPO_ROOT / "results" / "e2e_16dB_fullgrid_pairing_v2_candidate"},
    20: {"loss_db": 20, "candidate_dir": REPO_ROOT / "results" / "e2e_20dB_fullgrid_pairing_v2_candidate_t15"},
}


def ensure_output_dir(path: Path, *, overwrite: bool) -> None:
    if path.exists():
        has_contents = any(path.iterdir()) if path.is_dir() else True
        if has_contents and not overwrite:
            raise SystemExit(f"output already exists: {path} (use --overwrite)")
        if overwrite:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
    path.mkdir(parents=True, exist_ok=True)


def write_summary(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"input file not found: {path}")
    return pd.read_csv(path)


def infer_loss_db_from_dir(path: Path) -> int:
    name = path.name.lower()
    for loss_db in sorted(LOSS_CONFIGS, reverse=True):
        if f"{loss_db}db" in name:
            return int(loss_db)
    raise SystemExit(f"cannot infer loss_db from input dir: {path}")


def candidate_main_csv(candidate_dir: Path) -> Path:
    return candidate_dir / "polar_e2e_results.csv"


def candidate_diag_csv(candidate_dir: Path) -> Path:
    return candidate_dir / "polar_diag_summary.csv"


def _normalize_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for col in cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def h2(p: float) -> float:
    p = float(min(1.0 - 1e-12, max(1e-12, p)))
    return -p * math.log2(p) - (1.0 - p) * math.log2(1.0 - p)


def dary_mutual_info_proxy(d: int, ser: float | None) -> float | None:
    if d <= 1 or ser is None:
        return None
    try:
        e = float(ser)
    except Exception:
        return None
    if not math.isfinite(e):
        return None
    e = min(max(e, 1e-12), 1.0 - 1e-12)
    if int(d) <= 1:
        return 0.0
    return float(
        math.log2(int(d))
        + (1.0 - e) * math.log2(1.0 - e)
        + e * math.log2(e / float(int(d) - 1))
    )


def bw_bucket(bw: int | float | None) -> str:
    if bw is None:
        return "unknown"
    try:
        bw_i = int(bw)
    except Exception:
        return "unknown"
    if bw_i in {20, 30, 40, 50}:
        return "bw_small"
    if bw_i in {60, 80, 100}:
        return "bw_mid"
    if bw_i in {120, 150, 180, 200}:
        return "bw_large"
    return "unknown"


def tol_for_values(*vals: Any) -> float:
    mags = [1.0]
    for v in vals:
        if v is None:
            continue
        try:
            fv = float(v)
        except Exception:
            continue
        if not math.isfinite(fv):
            continue
        mags.append(abs(fv))
    return max(ABS_EPS, REL_EPS * max(mags))


def monotonic_increasing(values: list[float]) -> bool:
    if len(values) <= 1:
        return True
    for prev, cur in zip(values, values[1:]):
        if float(cur) - float(prev) < -tol_for_values(prev, cur):
            return False
    return True


def has_interior_peak(sorted_keys: list[int], values: list[float]) -> bool:
    if len(values) < 3:
        return False
    arr = np.asarray(values, dtype=float)
    if np.isnan(arr).all():
        return False
    best_idx = int(np.nanargmax(arr))
    if best_idx == 0 or best_idx == len(values) - 1:
        return False
    best_val = float(values[best_idx])
    if monotonic_increasing(values):
        return False
    if best_val - float(values[0]) <= tol_for_values(best_val, values[0]):
        return False
    if best_val - float(values[-1]) <= tol_for_values(best_val, values[-1]):
        return False
    return True


def load_candidate_frame(candidate_dir: Path) -> pd.DataFrame:
    main = load_csv(candidate_main_csv(candidate_dir))
    diag = load_csv(candidate_diag_csv(candidate_dir))
    numeric_cols = [
        "dimension", "bin_width_ps", "map_ser", "coincidence_rate_hz", "best_hard_PIE", "chi_E", "PIE_practical",
        "SKR_measured_bps", "layers_success_best", "threshold_ps", "effective_pairing_window_ps", "threshold_ratio_to_bw",
        "n_pairs_in_clean_frames", "n_pairs_in_ambiguous_frames", "clean_pair_fraction", "both_multi_frame_fraction",
        "raw_ser", "near_neighbor_frac", "n_pairs_actual", "frame_diag_available",
    ]
    main = _normalize_numeric(main, numeric_cols)
    diag = _normalize_numeric(diag, numeric_cols)
    keep_diag = [c for c in ["dimension","bin_width_ps","raw_ser","near_neighbor_frac","n_pairs_actual","frame_diag_available"] if c in diag.columns]
    merged = main.merge(diag[keep_diag].drop_duplicates(["dimension","bin_width_ps"]), on=["dimension","bin_width_ps"], how="left", suffixes=("", "_diag"))
    for col in ["raw_ser","near_neighbor_frac","n_pairs_actual","frame_diag_available"]:
        diag_col = f"{col}_diag"
        if diag_col in merged.columns:
            if col not in merged.columns:
                merged[col] = merged[diag_col]
            else:
                merged[col] = merged[col].where(pd.notna(merged[col]), merged[diag_col])
            merged = merged.drop(columns=[diag_col])
        if col not in merged.columns:
            merged[col] = np.nan
    loss_db = infer_loss_db_from_dir(candidate_dir)
    merged["loss_db"] = int(loss_db)
    merged["candidate_dir"] = str(candidate_dir)
    merged["frame_span_ps"] = pd.to_numeric(merged["dimension"], errors="coerce") * pd.to_numeric(merged["bin_width_ps"], errors="coerce")
    merged["log2_dimension"] = np.log2(pd.to_numeric(merged["dimension"], errors="coerce"))
    merged["bw_bucket"] = merged["bin_width_ps"].apply(bw_bucket)
    iab_vals = []
    beta_vals = []
    leak_vals = []
    model_tags = []
    for _, row in merged.iterrows():
        d = int(row["dimension"]) if pd.notna(row.get("dimension")) else 0
        iab = dary_mutual_info_proxy(d, row.get("map_ser"))
        iab_vals.append(iab)
        best = row.get("best_hard_PIE")
        if iab is None or best is None or pd.isna(best) or iab <= 0:
            beta_vals.append(np.nan)
            leak_vals.append(np.nan)
        else:
            beta = float(best) / float(iab)
            beta_vals.append(beta)
            leak_vals.append(max(float(iab) - float(best), 0.0))
        model_tags.append("partial_zhong_like")
    merged["IAB_or_proxy"] = iab_vals
    merged["beta_or_proxy"] = beta_vals
    merged["leak_ec_bits_or_proxy"] = leak_vals
    merged["delta_fk"] = 0.0
    merged["security_model_tag"] = model_tags
    return merged
