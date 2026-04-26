from __future__ import annotations

import math
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
LOSS_CONFIGS: dict[int, dict[str, Any]] = {
    6: {
        "loss_db": 6,
        "candidate_dir": REPO_ROOT / "results" / "e2e_6dB_fullgrid_pairing_v2_candidate",
    },
    10: {
        "loss_db": 10,
        "candidate_dir": REPO_ROOT / "results" / "e2e_10dB_fullgrid_pairing_v2_candidate",
    },
    16: {
        "loss_db": 16,
        "candidate_dir": REPO_ROOT / "results" / "e2e_16dB_fullgrid_pairing_v2_candidate",
    },
    20: {
        "loss_db": 20,
        "candidate_dir": REPO_ROOT / "results" / "e2e_20dB_fullgrid_pairing_v2_candidate_t15",
    },
}
ABS_EPS = 1e-9
REL_EPS = 1e-6


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



def candidate_main_csv(candidate_dir: Path) -> Path:
    return candidate_dir / "polar_e2e_results.csv"



def candidate_diag_csv(candidate_dir: Path) -> Path:
    return candidate_dir / "polar_diag_summary.csv"



def infer_loss_db_from_dir(path: Path) -> int:
    name = str(path).lower()
    for loss_db in sorted(LOSS_CONFIGS, reverse=True):
        if f"{loss_db}db" in name:
            return int(loss_db)
    raise SystemExit(f"cannot infer loss_db from input dir: {path}")



def default_input_dirs() -> list[Path]:
    return [Path(LOSS_CONFIGS[k]["candidate_dir"]) for k in sorted(LOSS_CONFIGS)]



def _normalize_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for col in cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out



def h2(p: float) -> float:
    p = float(min(1.0 - 1e-12, max(1e-12, p)))
    return -p * math.log2(p) - (1.0 - p) * math.log2(1.0 - p)



def chi_from_visibility(*, dimension: int, franson_visibility: float) -> float:
    d = int(dimension)
    if d <= 1:
        return 0.0
    vis = min(max(float(franson_visibility), 0.0), 1.0)
    e_p = max(0.0, min(0.5, (1.0 - vis) / 2.0))
    return float(h2(e_p) + e_p * math.log2(max(1, d - 1)))



def dary_mutual_info_proxy(*, dimension: int, ser: float | None) -> float | None:
    d = int(dimension)
    if d <= 1 or ser is None:
        return None
    try:
        e = float(ser)
    except Exception:
        return None
    if not math.isfinite(e):
        return None
    e = min(max(e, 1e-12), 1.0 - 1e-12)
    return float(
        math.log2(float(d))
        + (1.0 - e) * math.log2(1.0 - e)
        + e * math.log2(e / float(max(1, d - 1)))
    )



def safe_div(num: float | None, den: float | None) -> float | None:
    if num is None or den is None:
        return None
    try:
        a = float(num)
        b = float(den)
    except Exception:
        return None
    if (not math.isfinite(a)) or (not math.isfinite(b)) or abs(b) <= ABS_EPS:
        return None
    return float(a / b)



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



def monotonic_decreasing(values: list[float]) -> bool:
    if len(values) <= 1:
        return True
    for prev, cur in zip(values, values[1:]):
        if float(cur) - float(prev) > tol_for_values(prev, cur):
            return False
    return True



def has_interior_peak(*, keys: list[int], values: list[float]) -> bool:
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
    main = pd.read_csv(candidate_main_csv(candidate_dir))
    diag = pd.read_csv(candidate_diag_csv(candidate_dir))
    numeric_cols = [
        "dimension", "bin_width_ps", "map_ser", "coincidence_rate_hz", "best_hard_PIE", "chi_E",
        "PIE_practical", "SKR_measured_bps", "layers_success_best", "threshold_ps", "effective_pairing_window_ps",
        "threshold_ratio_to_bw", "raw_ser", "near_neighbor_frac", "n_pairs_actual", "frame_diag_available",
        "n_pairs_in_clean_frames", "n_pairs_in_ambiguous_frames", "clean_pair_fraction", "both_multi_frame_fraction",
    ]
    main = _normalize_numeric(main, numeric_cols)
    diag = _normalize_numeric(diag, numeric_cols)
    keep_diag = [c for c in ["dimension", "bin_width_ps", "raw_ser", "near_neighbor_frac", "n_pairs_actual", "frame_diag_available"] if c in diag.columns]
    merged = main.merge(diag[keep_diag].drop_duplicates(["dimension", "bin_width_ps"]), on=["dimension", "bin_width_ps"], how="left", suffixes=("", "_diag"))
    for col in ["raw_ser", "near_neighbor_frac", "n_pairs_actual", "frame_diag_available"]:
        diag_col = f"{col}_diag"
        if diag_col in merged.columns:
            if col not in merged.columns:
                merged[col] = merged[diag_col]
            else:
                merged[col] = merged[col].where(pd.notna(merged[col]), merged[diag_col])
            merged = merged.drop(columns=[diag_col])
        if col not in merged.columns:
            merged[col] = np.nan
    merged["loss_db"] = int(infer_loss_db_from_dir(candidate_dir))
    merged["candidate_dir"] = str(candidate_dir)
    merged["accepted_rate_proxy"] = pd.to_numeric(merged.get("coincidence_rate_hz"), errors="coerce")

    iab_vals: list[float] = []
    iab_source_tags: list[str] = []
    beta_eff_vals: list[float] = []
    leak_proxy_vals: list[float] = []
    for _, row in merged.iterrows():
        d = int(row["dimension"]) if pd.notna(row.get("dimension")) else 0
        map_ser = row.get("map_ser")
        raw_ser = row.get("raw_ser")
        ser = map_ser if pd.notna(map_ser) else raw_ser
        source_tag = "map_ser_proxy" if pd.notna(map_ser) else ("raw_ser_proxy" if pd.notna(raw_ser) else "missing")
        iab = dary_mutual_info_proxy(dimension=d, ser=float(ser) if pd.notna(ser) else None)
        best = row.get("best_hard_PIE")
        beta_eff = np.nan
        leak_proxy = np.nan
        if iab is not None and math.isfinite(iab) and iab > 0.0 and pd.notna(best):
            beta_eff = float(max(0.0, min(1.5, float(best) / float(iab))))
            leak_proxy = float(max(iab - float(best), 0.0))
        iab_vals.append(float(iab) if iab is not None and math.isfinite(iab) else np.nan)
        iab_source_tags.append(source_tag)
        beta_eff_vals.append(beta_eff)
        leak_proxy_vals.append(leak_proxy)
    merged["IAB_est"] = iab_vals
    merged["IAB_source_tag"] = iab_source_tags
    merged["beta_eff_from_best_hard_pie"] = beta_eff_vals
    merged["leak_ec_bits_or_proxy"] = leak_proxy_vals
    return merged



def calibrated_effective_sample_count(row: pd.Series) -> tuple[float | None, dict[str, float | str]]:
    n_pairs = row.get("n_pairs_actual")
    if pd.isna(n_pairs):
        n_pairs = row.get("n_pairs_in_clean_frames")
    if pd.isna(n_pairs):
        return None, {
            "n_eff_pairs": np.nan,
            "layer_fraction_used": np.nan,
            "clean_fraction_used": np.nan,
            "delta_fk_driver_tag": "missing_sample_count",
        }
    d = int(row.get("dimension", 0) or 0)
    bits = max(1.0, math.log2(float(max(2, d))))
    layers = row.get("layers_success_best")
    layer_fraction = 0.0
    if pd.notna(layers):
        layer_fraction = min(1.0, max(float(layers) / bits, 1.0 / bits))
    else:
        layer_fraction = 1.0 / bits
    clean_fraction = 1.0
    if pd.notna(row.get("clean_pair_fraction")):
        clean_fraction = min(1.0, max(0.0, float(row.get("clean_pair_fraction"))))
    elif pd.notna(row.get("frame_diag_available")) and int(float(row.get("frame_diag_available"))) != 1:
        clean_fraction = 0.9
    n_eff = float(n_pairs) * float(layer_fraction) * float(clean_fraction)
    if not math.isfinite(n_eff) or n_eff <= 0.0:
        return None, {
            "n_eff_pairs": np.nan,
            "layer_fraction_used": layer_fraction,
            "clean_fraction_used": clean_fraction,
            "delta_fk_driver_tag": "nonpositive_n_eff",
        }
    return n_eff, {
        "n_eff_pairs": float(n_eff),
        "layer_fraction_used": float(layer_fraction),
        "clean_fraction_used": float(clean_fraction),
        "delta_fk_driver_tag": "n_pairs_times_layer_and_clean_fraction",
    }



def delta_fk_calibrated(*, n_eff_pairs: float | None, eps_sec: float, eps_cor: float) -> float | None:
    if n_eff_pairs is None:
        return None
    n_eff = float(n_eff_pairs)
    if (not math.isfinite(n_eff)) or n_eff <= 0.0:
        return None
    term1 = 4.0 * math.sqrt(math.log2(2.0 / float(eps_sec)) / n_eff)
    term2 = 2.0 * math.log2(2.0 / float(eps_cor)) / n_eff
    return float(term1 + term2)



def find_direct_leak_fields(frame: pd.DataFrame) -> dict[str, bool]:
    wanted = [
        "syndrome_bits_revealed",
        "verification_bits_revealed",
        "total_leak_ec_bits",
        "block_success_flag",
        "block_success_rate",
        "frame_success_rate",
        "decode_fail_count",
        "kept_block_count",
        "dropped_block_count",
    ]
    return {field: field in frame.columns for field in wanted}



def format_float(v: Any, digits: int = 6) -> str:
    try:
        fv = float(v)
    except Exception:
        return "nan"
    if not math.isfinite(fv):
        return "nan"
    return f"{fv:.{digits}f}"
