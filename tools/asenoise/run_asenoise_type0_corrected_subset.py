#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_ROOT = REPO_ROOT / "tools"
SECURITY_ROOT = TOOLS_ROOT / "security_reports"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))
if str(SECURITY_ROOT) not in sys.path:
    sys.path.insert(0, str(SECURITY_ROOT))

from _security_calibrated_common import (  # type: ignore
    calibrated_effective_sample_count,
    chi_from_visibility,
    dary_mutual_info_proxy,
    delta_fk_calibrated,
)


DATA_ROOT_DEFAULT = Path(r"D:\Data\Raw Data\ASENoise_Type0")
OLD_RUN_NAME = "hdqkd_asenoise_type0_20260426_171401"
INVALID_REASON = "wrong_channels_1_5_for_asenoise_channels_3_2"
DEFAULT_DIMS = "512,1024,2048,4096"
DEFAULT_BWS = "30,60,120,200"
FRANSON_VISIBILITY = 0.95
EPS_SEC = 1e-10
EPS_COR = 1e-10


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _sha256(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _find_head_ttbin(dataset_dir: Path) -> Path:
    heads = [p for p in sorted(dataset_dir.glob("*.ttbin")) if not p.name.lower().endswith(tuple(f".{i}.ttbin" for i in range(10)))]
    # Use regex-like final check without importing re for a tiny rule.
    heads = [p for p in heads if not any(p.name.lower().endswith(f".{i}.ttbin") for i in range(1000))]
    if len(heads) != 1:
        raise RuntimeError(f"expected exactly one head .ttbin in {dataset_dir}, found {len(heads)}")
    return heads[0]


def _run_logged(cmd: list[str], *, cwd: Path, log_path: Path) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8", newline="") as log:
        line = f"[RUN] {_now()} cwd={cwd} cmd={' '.join(cmd)}"
        print(line)
        log.write(line + "\n")
        log.flush()
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert proc.stdout is not None
        for out_line in proc.stdout:
            try:
                print(out_line, end="")
            except UnicodeEncodeError:
                safe_line = out_line.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(
                    sys.stdout.encoding or "utf-8",
                    errors="replace",
                )
                print(safe_line, end="")
            log.write(out_line)
        code = int(proc.wait())
        done = f"[RUN] {_now()} exit={code}"
        print(done)
        log.write(done + "\n")
        return code


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return float("nan")


def _normalize_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for col in cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def _load_asenoise_candidate_frame(*, dataset_label: str, polar_dir: Path) -> pd.DataFrame:
    main_path = polar_dir / "polar_e2e_results.csv"
    diag_path = polar_dir / "polar_diag_summary.csv"
    main = pd.read_csv(main_path)
    diag = pd.read_csv(diag_path) if diag_path.exists() else pd.DataFrame()
    numeric_cols = [
        "dimension",
        "bin_width_ps",
        "map_ser",
        "coincidence_rate_hz",
        "best_hard_PIE",
        "chi_E",
        "PIE_practical",
        "SKR_measured_bps",
        "layers_success_best",
        "threshold_ps",
        "effective_pairing_window_ps",
        "threshold_ratio_to_bw",
        "raw_ser",
        "near_neighbor_frac",
        "n_pairs_actual",
        "frame_diag_available",
        "n_pairs_in_clean_frames",
        "n_pairs_in_ambiguous_frames",
        "clean_pair_fraction",
        "both_multi_frame_fraction",
    ]
    main = _normalize_numeric(main, numeric_cols)
    if not diag.empty:
        diag = _normalize_numeric(diag, numeric_cols)
        keep = [c for c in ["dimension", "bin_width_ps", "raw_ser", "near_neighbor_frac", "n_pairs_actual", "frame_diag_available"] if c in diag.columns]
        if keep:
            main = main.merge(
                diag[keep].drop_duplicates(["dimension", "bin_width_ps"]),
                on=["dimension", "bin_width_ps"],
                how="left",
                suffixes=("", "_diag"),
            )
            for col in ["raw_ser", "near_neighbor_frac", "n_pairs_actual", "frame_diag_available"]:
                diag_col = f"{col}_diag"
                if diag_col in main.columns:
                    if col not in main.columns:
                        main[col] = main[diag_col]
                    else:
                        main[col] = main[col].where(pd.notna(main[col]), main[diag_col])
                    main = main.drop(columns=[diag_col])
    for col in ["raw_ser", "near_neighbor_frac", "n_pairs_actual", "frame_diag_available"]:
        if col not in main.columns:
            main[col] = np.nan

    main["dataset_label"] = str(dataset_label)
    main["accepted_rate_proxy"] = pd.to_numeric(main.get("coincidence_rate_hz"), errors="coerce")

    iab_vals: list[float] = []
    iab_tags: list[str] = []
    beta_vals: list[float] = []
    leak_vals: list[float] = []
    for _, row in main.iterrows():
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
        iab_tags.append(source_tag)
        beta_vals.append(beta_eff)
        leak_vals.append(leak_proxy)
    main["IAB_est"] = iab_vals
    main["IAB_source_tag"] = iab_tags
    main["beta_eff_from_best_hard_pie"] = beta_vals
    main["leak_ec_bits_or_proxy"] = leak_vals
    return main


def _build_asenoise_shadow(frame: pd.DataFrame) -> pd.DataFrame:
    df = frame.copy()
    df["franson_visibility_global"] = FRANSON_VISIBILITY
    df["eps_sec"] = EPS_SEC
    df["eps_cor"] = EPS_COR
    df["shadow_level"] = "shadow_only_no_actual_replay"
    df["actual_ir_model_tag"] = "strict_zhong_like_calibrated_actual_ir_shadow_only"

    leak_vals: list[float] = []
    leak_tags: list[str] = []
    delta_vals: list[float] = []
    n_eff_vals: list[float] = []
    chi_vals: list[float] = []
    pie_vals: list[float] = []
    skr_vals: list[float] = []
    beta_vals: list[float] = []
    driver_tags: list[str] = []

    for _, row in df.iterrows():
        iab = row.get("IAB_est")
        best_hard = row.get("best_hard_PIE")
        leak = np.nan
        if pd.notna(iab) and pd.notna(best_hard):
            leak = max(float(iab) - float(best_hard), 0.0)
        n_eff, fk_meta = calibrated_effective_sample_count(row)
        delta_fk = delta_fk_calibrated(n_eff_pairs=n_eff, eps_sec=EPS_SEC, eps_cor=EPS_COR)
        chi_e = chi_from_visibility(dimension=int(row["dimension"]), franson_visibility=FRANSON_VISIBILITY)
        pie = np.nan
        if pd.notna(iab) and math.isfinite(float(iab)) and math.isfinite(float(leak)) and delta_fk is not None:
            pie = max(0.0, float(iab) - float(leak) - float(chi_e) - float(delta_fk))
        accepted_rate = row.get("accepted_rate_proxy")
        skr = float(pie) * float(accepted_rate) if pd.notna(pie) and pd.notna(accepted_rate) and math.isfinite(float(accepted_rate)) else np.nan
        beta = np.nan
        if pd.notna(iab) and float(iab) > 0.0 and math.isfinite(float(iab)) and math.isfinite(float(leak)):
            beta = max(0.0, float(iab) - float(leak)) / float(iab)

        leak_vals.append(leak)
        leak_tags.append("surrogate_from_best_hard_pie_gap")
        delta_vals.append(delta_fk if delta_fk is not None else np.nan)
        n_eff_vals.append(float(fk_meta.get("n_eff_pairs", np.nan)))
        chi_vals.append(float(chi_e))
        pie_vals.append(pie)
        skr_vals.append(skr)
        beta_vals.append(beta)
        driver_tags.append(str(fk_meta.get("delta_fk_driver_tag", "unknown")))

    df["leak_EC_actual_bits"] = leak_vals
    df["leak_EC_source_tag"] = leak_tags
    df["DeltaFK_calibrated"] = delta_vals
    df["n_eff_pairs_for_fk"] = n_eff_vals
    df["delta_fk_driver_tag"] = driver_tags
    df["chi_E_calibrated"] = chi_vals
    df["PIE_secure_actual_ir"] = pie_vals
    df["SKR_secure_actual_ir_bps"] = skr_vals
    df["beta_eff"] = beta_vals
    return df


def _write_shadow_outputs(*, dataset_label: str, polar_dir: Path, out_dir: Path) -> dict[str, Any]:
    frame = _load_asenoise_candidate_frame(dataset_label=dataset_label, polar_dir=polar_dir)
    shadow = _build_asenoise_shadow(frame)
    out_dir.mkdir(parents=True, exist_ok=True)
    cols = [
        "dataset_label",
        "dimension",
        "bin_width_ps",
        "processing_rule_version",
        "pairing_path_tag",
        "pairing_window_source_tag",
        "threshold_ps",
        "effective_pairing_window_ps",
        "threshold_ratio_to_bw",
        "raw_ser",
        "map_ser",
        "coincidence_rate_hz",
        "accepted_rate_proxy",
        "layers_success_best",
        "best_hard_PIE",
        "chi_E",
        "chi_E_calibrated",
        "IAB_est",
        "IAB_source_tag",
        "franson_visibility_global",
        "leak_EC_actual_bits",
        "leak_EC_source_tag",
        "DeltaFK_calibrated",
        "eps_sec",
        "eps_cor",
        "PIE_practical",
        "SKR_measured_bps",
        "PIE_secure_actual_ir",
        "SKR_secure_actual_ir_bps",
        "beta_eff",
        "actual_ir_model_tag",
        "shadow_level",
        "n_pairs_actual",
        "frame_diag_available",
        "clean_pair_fraction",
        "n_eff_pairs_for_fk",
        "delta_fk_driver_tag",
    ]
    for col in cols:
        if col not in shadow.columns:
            shadow[col] = np.nan
    table_path = out_dir / "actual_ir_finite_key_point_table.csv"
    shadow[cols].to_csv(table_path, index=False)

    perf = pd.to_numeric(shadow["PIE_practical"], errors="coerce")
    secure = pd.to_numeric(shadow["PIE_secure_actual_ir"], errors="coerce")
    skr_secure = pd.to_numeric(shadow["SKR_secure_actual_ir_bps"], errors="coerce")
    best_idx = skr_secure.idxmax() if skr_secure.notna().any() else None
    lines = [
        f"dataset_label: {dataset_label}",
        f"point_count: {len(shadow)}",
        f"franson_visibility_global: {FRANSON_VISIBILITY}",
        f"eps_sec: {EPS_SEC}",
        f"eps_cor: {EPS_COR}",
        "routeA_level: shadow_only_no_actual_replay",
        "finite_key_model_tag: zhong_like_finite_key_calibrated_shadow",
        "reporting_note: PIE_practical/SKR_measured_bps are performance proxies; use PIE_secure_actual_ir/SKR_secure_actual_ir_bps for conservative reporting.",
        f"DeltaFK_calibrated_range: {float(pd.to_numeric(shadow['DeltaFK_calibrated'], errors='coerce').min()):.6g} .. {float(pd.to_numeric(shadow['DeltaFK_calibrated'], errors='coerce').max()):.6g}",
        f"mean_PIE_drop: {float((perf - secure).mean()):.6g}",
    ]
    if best_idx is not None:
        best = shadow.loc[best_idx]
        lines.append(f"best_secure_point: d={int(best['dimension'])},bw={int(best['bin_width_ps'])},PIE={float(best['PIE_secure_actual_ir']):.6g},SKR={float(best['SKR_secure_actual_ir_bps']):.6g}")
    summary_path = out_dir / "actual_ir_finite_key_summary.txt"
    summary_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return {
        "shadow_rows": int(len(shadow)),
        "finite_secure_rows": int(pd.to_numeric(shadow["PIE_secure_actual_ir"], errors="coerce").notna().sum()),
        "point_table": str(table_path),
        "summary": str(summary_path),
    }


def _mark_old_run_invalid(dataset_dir: Path) -> dict[str, Any]:
    old_root = dataset_dir / OLD_RUN_NAME
    marker = old_root / "INVALID_RESULT_DO_NOT_USE.json"
    payload = {
        "invalid": True,
        "reason": INVALID_REASON,
        "created_at": _now(),
        "old_run_root": str(old_root),
        "do_not_use": [
            str(old_root / "polar" / "polar_e2e_results.csv"),
            str(old_root / "polar" / "polar_diag_summary.csv"),
            str(old_root / "polar" / "polar_layer_metrics.csv"),
        ],
        "replacement_policy": "use hdqkd_asenoise_type0_ch3_2_subset_* outputs",
    }
    if old_root.exists():
        _write_json(marker, payload)
        return {"old_run_root": str(old_root), "marker": str(marker), "marked": True}
    return {"old_run_root": str(old_root), "marker": str(marker), "marked": False, "reason": "old_run_missing"}


def _validate_outputs(out_root: Path, old_root: Path) -> dict[str, Any]:
    e2e_root = out_root / "e2e_center_aligned"
    polar_dir = out_root / "polar"
    shadow_dir = out_root / "routeA_shadow"
    grid_rows = _read_csv_rows(e2e_root / "_tmp_grid_table.csv")
    audit_rows = _read_csv_rows(e2e_root / "e2e_alignment_audit.csv")
    polar_rows = _read_csv_rows(polar_dir / "polar_e2e_results.csv")
    diag_rows = _read_csv_rows(polar_dir / "polar_diag_summary.csv")
    shadow_rows = _read_csv_rows(shadow_dir / "actual_ir_finite_key_point_table.csv")

    can_run_count = sum(1 for r in audit_rows if str(r.get("can_run_polar", "")).strip() == "1")
    diag_peak_count = sum(1 for r in diag_rows if str(r.get("peak_center_ps", "")).strip() and str(r.get("peak_to_bg", "")).strip())
    shadow_finite_count = 0
    for r in shadow_rows:
        vals = [r.get("DeltaFK_calibrated"), r.get("chi_E_calibrated"), r.get("PIE_secure_actual_ir"), r.get("SKR_secure_actual_ir_bps")]
        if all(v is not None and str(v).strip() not in {"", "nan", "NaN"} for v in vals):
            shadow_finite_count += 1
    old_polar = old_root / "polar" / "polar_e2e_results.csv"
    new_polar = polar_dir / "polar_e2e_results.csv"
    return {
        "grid_rows": len(grid_rows),
        "audit_rows": len(audit_rows),
        "can_run_polar_rows": can_run_count,
        "polar_rows": len(polar_rows),
        "polar_differs_from_invalid_old": bool(_sha256(new_polar) and _sha256(new_polar) != _sha256(old_polar)),
        "polar_diag_rows": len(diag_rows),
        "polar_diag_peak_rows": diag_peak_count,
        "shadow_rows": len(shadow_rows),
        "shadow_finite_rows": shadow_finite_count,
        "ok": bool(len(grid_rows) == 16 and can_run_count == 16 and len(polar_rows) == 16 and len(shadow_rows) == 16 and shadow_finite_count > 0),
    }


def run_dataset(*, dataset_dir: Path, out_name: str, dims: str, bws: str, workers: int, jobs: int) -> dict[str, Any]:
    out_root = dataset_dir / out_name
    log_path = out_root / "run.log"
    out_root.mkdir(parents=True, exist_ok=True)
    head = _find_head_ttbin(dataset_dir)
    old_marker = _mark_old_run_invalid(dataset_dir)
    item: dict[str, Any] = {
        "dataset_label": dataset_dir.name,
        "dataset_dir": str(dataset_dir),
        "head_ttbin": str(head),
        "out_root": str(out_root),
        "old_invalid_marker": old_marker,
        "started_at": _now(),
        "channels": {"A": 3, "B": 2},
        "dims": dims,
        "bws": bws,
        "commands": [],
        "errors": [],
    }

    e2e_root = out_root / "e2e_center_aligned"
    polar_dir = out_root / "polar"
    polar_dir.mkdir(parents=True, exist_ok=True)

    e2e_cmd = [
        sys.executable,
        "experiments/run_e2e_pipeline.py",
        "--ttbin",
        str(head),
        "--ttbin-ch-a-override",
        "3",
        "--ttbin-ch-b-override",
        "2",
        "--dims",
        dims,
        "--bws",
        bws,
        "--force-align",
        "--skip-polar",
        "--extract-workers",
        str(int(workers)),
        "--jobs",
        str(int(jobs)),
        "--out-root",
        str(e2e_root),
    ]
    code = _run_logged(e2e_cmd, cwd=REPO_ROOT, log_path=log_path)
    item["e2e_exit_code"] = code
    item["commands"].append({"stage": "e2e", "exit_code": code, "cmd": e2e_cmd})
    if code != 0:
        item["errors"].append(f"e2e_failed:{code}")
        return item

    polar_cmd = [
        sys.executable,
        "experiments/run_real_polar_max_pie.py",
        "--jobs",
        str(int(jobs)),
        "--N",
        "4096",
        "--grid-table",
        str(e2e_root / "_tmp_grid_table.csv"),
        "--in-csv",
        str(e2e_root / "_tmp_src_table.csv"),
        "--out-csv",
        str(polar_dir / "polar_e2e_results.csv"),
        "--prefer-sidecar-map-ser",
    ]
    code = _run_logged(polar_cmd, cwd=REPO_ROOT, log_path=log_path)
    item["polar_exit_code"] = code
    item["commands"].append({"stage": "polar", "exit_code": code, "cmd": polar_cmd})
    if code != 0:
        item["errors"].append(f"polar_failed:{code}")
        return item

    shadow = _write_shadow_outputs(dataset_label=dataset_dir.name, polar_dir=polar_dir, out_dir=out_root / "routeA_shadow")
    item["shadow"] = shadow
    item["validation"] = _validate_outputs(out_root, dataset_dir / OLD_RUN_NAME)
    item["finished_at"] = _now()
    _write_json(out_root / "run_manifest.json", item)
    return item


def rebuild_shadow_for_existing(*, dataset_dir: Path, out_name: str) -> dict[str, Any]:
    out_root = dataset_dir / out_name
    item: dict[str, Any] = {
        "dataset_label": dataset_dir.name,
        "dataset_dir": str(dataset_dir),
        "out_root": str(out_root),
        "started_at": _now(),
        "errors": [],
        "warnings": [],
        "mode": "shadow_only_existing_polar",
    }
    _mark_old_run_invalid(dataset_dir)
    if not out_root.exists():
        item["errors"].append(f"missing_existing_out_root:{out_root}")
        item["finished_at"] = _now()
        return item
    polar_dir = out_root / "polar"
    if not (polar_dir / "polar_e2e_results.csv").exists():
        item["errors"].append(f"missing_existing_polar:{polar_dir / 'polar_e2e_results.csv'}")
        item["finished_at"] = _now()
        return item
    shadow = _write_shadow_outputs(dataset_label=dataset_dir.name, polar_dir=polar_dir, out_dir=out_root / "routeA_shadow")
    item["shadow"] = shadow
    item["validation"] = _validate_outputs(out_root, dataset_dir / OLD_RUN_NAME)
    item["finished_at"] = _now()
    _write_json(out_root / "run_manifest.json", item)
    return item


def main() -> int:
    ap = argparse.ArgumentParser(description="Run corrected ASENoise Type0 ch3/ch2 subset E2E, Polar, and finite-key shadow.")
    ap.add_argument("--data-root", default=str(DATA_ROOT_DEFAULT))
    ap.add_argument("--dims", default=DEFAULT_DIMS)
    ap.add_argument("--bws", default=DEFAULT_BWS)
    ap.add_argument("--workers", type=int, default=15)
    ap.add_argument("--jobs", type=int, default=15)
    ap.add_argument("--timestamp", default=datetime.now().strftime("%Y%m%d_%H%M%S"))
    ap.add_argument("--datasets", default="", help="optional comma-separated dataset directory names")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument(
        "--shadow-only",
        action="store_true",
        help="Rebuild Route A shadow outputs from existing timestamped Polar outputs without rerunning E2E/Polar.",
    )
    args = ap.parse_args()

    data_root = Path(args.data_root)
    selected = {x.strip() for x in str(args.datasets).split(",") if x.strip()}
    datasets = [p for p in sorted(data_root.iterdir(), key=lambda x: x.name) if p.is_dir() and (not selected or p.name in selected)]
    out_name = f"hdqkd_asenoise_type0_ch3_2_subset_{args.timestamp}"
    manifest_path = data_root / f"asenoise_type0_corrected_subset_manifest_{args.timestamp}.json"
    master_path = data_root / f"asenoise_type0_actual_ir_finite_key_master_{args.timestamp}.csv"

    results: list[dict[str, Any]] = []
    master_frames: list[pd.DataFrame] = []
    for ds in datasets:
        out_root = ds / out_name
        if bool(args.shadow_only):
            result = rebuild_shadow_for_existing(dataset_dir=ds, out_name=out_name)
            results.append(result)
            table_path = Path(str(((result.get("shadow") or {}).get("point_table") or "")))
            if table_path.exists():
                master_frames.append(pd.read_csv(table_path))
            _write_json(manifest_path, {"created_at": _now(), "results": results})
            continue
        if out_root.exists() and any(out_root.iterdir()):
            if not bool(args.overwrite):
                raise SystemExit(f"output exists: {out_root} (use --overwrite)")
            shutil.rmtree(out_root)
        result = run_dataset(dataset_dir=ds, out_name=out_name, dims=str(args.dims), bws=str(args.bws), workers=int(args.workers), jobs=int(args.jobs))
        results.append(result)
        table_path = Path(str(((result.get("shadow") or {}).get("point_table") or "")))
        if table_path.exists():
            master_frames.append(pd.read_csv(table_path))
        _write_json(manifest_path, {"created_at": _now(), "results": results})

    if master_frames:
        pd.concat(master_frames, ignore_index=True).to_csv(master_path, index=False)
    _write_json(
        manifest_path,
        {
            "created_at": _now(),
            "data_root": str(data_root),
            "dims": str(args.dims),
            "bws": str(args.bws),
            "channels": {"A": 3, "B": 2},
            "routeA_level": "shadow_only_no_actual_replay",
            "franson_visibility_global": FRANSON_VISIBILITY,
            "master_shadow_csv": str(master_path) if master_frames else "",
            "results": results,
        },
    )
    print(f"[ASENOISE] manifest={manifest_path}")
    if master_frames:
        print(f"[ASENOISE] master_shadow_csv={master_path}")
    return 0 if all(not r.get("errors") and (r.get("validation") or {}).get("ok") for r in results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
