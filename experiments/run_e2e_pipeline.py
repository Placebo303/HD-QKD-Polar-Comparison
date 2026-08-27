#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import concurrent.futures
import json
import math
import multiprocessing.shared_memory
import os
import re
import subprocess
import sys
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.runtime_paths import default_project_results_root, resolve_repo_path
from src.workflow.export_joint_sequence_sidecar import (  # type: ignore
    _estimate_peak_stats_from_timetags,
    export_sidecar_for_point,
    resolve_point_sources,
)
from src.reconciliation.run_nbldpc_demo_point import _read_ttbin_timetags  # type: ignore

_G_GRID_MAP: dict[tuple[int, int], dict[str, str]] | None = None
_G_OUT_ROOT_S: str = ""
_G_FORCE_ALIGN: bool = False
_G_OFFSET_OVERRIDE_PS: int | None = None
_G_COINC_WINDOW_OVERRIDE_PS: int | None = None
_G_SHARED_BY_TTBIN: dict[str, dict[str, Any]] = {}
_G_TTBIN_BY_POINT: dict[str, str] = {}
_G_REPAIR_DIAGNOSTICS: bool = False
_G_MATERIALIZE_PROCESSING_RULE_VERSION: str = "legacy_v1"
_G_REAL_SEQ_POOL_ROOT: str = ""


def _progress(iterable, *, total: int, desc: str):
    try:
        from tqdm import tqdm  # type: ignore

        return tqdm(iterable, total=total, desc=desc)
    except Exception:
        return iterable


def _init_extract_worker(
    grid_map: dict[tuple[int, int], dict[str, str]],
    out_root_s: str,
    force_align: bool,
    offset_override_ps: int | None = None,
    coinc_window_override_ps: int | None = None,
    shared_by_ttbin: dict[str, dict[str, Any]] | None = None,
    ttbin_by_point: dict[str, str] | None = None,
    repair_diagnostics: bool = False,
    materialize_processing_rule_version: str = "legacy_v1",
    real_seq_pool_root: str = "",
) -> None:
    global _G_GRID_MAP, _G_OUT_ROOT_S, _G_FORCE_ALIGN, _G_OFFSET_OVERRIDE_PS, _G_COINC_WINDOW_OVERRIDE_PS, _G_SHARED_BY_TTBIN, _G_TTBIN_BY_POINT, _G_REPAIR_DIAGNOSTICS, _G_MATERIALIZE_PROCESSING_RULE_VERSION, _G_REAL_SEQ_POOL_ROOT
    _G_GRID_MAP = grid_map
    _G_OUT_ROOT_S = str(out_root_s)
    _G_FORCE_ALIGN = bool(force_align)
    _G_OFFSET_OVERRIDE_PS = int(offset_override_ps) if offset_override_ps is not None else None
    _G_COINC_WINDOW_OVERRIDE_PS = int(coinc_window_override_ps) if coinc_window_override_ps is not None else None
    _G_SHARED_BY_TTBIN = dict(shared_by_ttbin or {})
    _G_TTBIN_BY_POINT = dict(ttbin_by_point or {})
    _G_REPAIR_DIAGNOSTICS = bool(repair_diagnostics)
    _G_MATERIALIZE_PROCESSING_RULE_VERSION = str(materialize_processing_rule_version or "legacy_v1").strip().lower() or "legacy_v1"
    _G_REAL_SEQ_POOL_ROOT = str(real_seq_pool_root or "").strip()


def _extract_one_point(d: int, bw: int) -> dict[str, Any]:
    logs: list[str] = []
    try:
        if _G_GRID_MAP is None:
            raise RuntimeError("extract worker is not initialized")
        grid_map = _G_GRID_MAP
        out_root = _resolve_path(_G_OUT_ROOT_S)
        force_align = bool(_G_FORCE_ALIGN)
        processing_rule_version_use = str(_G_MATERIALIZE_PROCESSING_RULE_VERSION or "legacy_v1").strip().lower() or "legacy_v1"
        key = (int(d), int(bw))

        grid_row = grid_map.get(key)
        input_status = str((grid_row or {}).get("status") or "").strip().upper()
        sidecar_verdict = ""
        fail_reason = ""
        if grid_row is None:
            ttbin_override = str(os.getenv("HDQKD_TTBIN_FILE_OVERRIDE") or "").strip()
            if ttbin_override:
                input_status = "OVERRIDE"
                logs.append(f"[E2E] point=({d},{bw}) synthetic grid row from --ttbin override")
                grid_row = {
                    "dimension": str(d),
                    "bin_width_ps": str(bw),
                    "status": "OVERRIDE",
                    "out_root": str(out_root),
                    "coincidence_rate_hz": "",
                }
            else:
                try:
                    boot = _bootstrap_missing_point(d=int(d), bw=int(bw), grid_map=grid_map, out_root=out_root)
                    input_status = "BOOTSTRAP"
                    logs.append(f"[E2E] point=({d},{bw}) bootstrap from {boot.get('template_point')}")
                    grid_row = {
                        "dimension": str(d),
                        "bin_width_ps": str(bw),
                        "status": "BOOTSTRAP",
                        "out_root": str(out_root),
                        "coincidence_rate_hz": str(boot.get("rate", "")),
                    }
                except Exception as e:
                    return {
                    "key": key,
                    "audit_row": {
                        "dimension": int(d),
                        "bin_width_ps": int(bw),
                        "sidecar_root": "",
                        "ttbin_path": "",
                        "cond_A_missing_a_or_b": 1,
                        "cond_B_ttbin_newer_than_aeff": 0,
                        "cond_C_force_align": int(force_align),
                        "cond_D_missing_diagnostics": 0,
                        "need_realign": 1,
                        "realign_ok": 0,
                        "realign_error": f"point_not_in_grid_mixed_full_table:{type(e).__name__}:{e}",
                        "can_run_polar": 0,
                        "input_status": input_status,
                        "status_output": "",
                        "sidecar_verdict": "",
                        "fail_reason": "",
                        "map_ser": "",
                        "coincidence_rate_hz": "",
                        "corr_bins": "",
                        "corr_nonzero": "",
                        "corr_argmax": "",
                        "corr_max": "",
                        "peak_center_ps": "",
                        "peak_sigma_ps": "",
                        "peak_to_bg": "",
                        "peak_status": "",
                        "peak_scan_range_ps": "",
                        "peak_bin_ps": "",
                    },
                    "run_grid_row": None,
                    "run_src_row": None,
                    "runnable_key": None,
                    "logs": logs + [f"[E2E] point=({d},{bw}) missing in grid and bootstrap failed: {e}"],
                }

        # Always write/read sidecars inside current run out_root to avoid cross-run path mismatch.
        sidecar_root = out_root / "sidecars" / f"d{d}_bw{bw}" / "blk0"
        a_path = sidecar_root / "a_eff.npy"
        b_path = sidecar_root / "b_eff.npy"
        meta_path = sidecar_root / "sidecar_meta.json"
        meta = _read_json(meta_path)

        ttbin_path = _extract_ttbin_from_meta(meta)
        if ttbin_path is None:
            ttbin_path = _extract_ttbin_from_ctx(f"{d},{bw}")

        cond_A_missing = (not a_path.exists()) or (not b_path.exists())
        cond_B_newer_ttbin = False
        if (ttbin_path is not None) and ttbin_path.exists() and a_path.exists():
            cond_B_newer_ttbin = ttbin_path.stat().st_mtime > a_path.stat().st_mtime
        cond_C_force = bool(force_align)
        cond_D_diag_incomplete = False
        if bool(_G_REPAIR_DIAGNOSTICS) and (not cond_A_missing) and meta:
            diag_ok, diag_reason = _sidecar_diagnostics_complete(sidecar_root, meta)
            cond_D_diag_incomplete = not bool(diag_ok)
            if cond_D_diag_incomplete:
                logs.append(f"[E2E][DIAG_REPAIR] point=({d},{bw}) reason={diag_reason}")
        need_realign = bool(cond_A_missing or cond_B_newer_ttbin or cond_C_force or cond_D_diag_incomplete)

        re_align_ok = None
        re_align_reason = ""
        map_ser = float("nan")
        factor = 1

        if isinstance(meta.get("factor"), (int, float)):
            try:
                factor = int(meta.get("factor"))
            except Exception:
                factor = 1

        if need_realign:
            mparams = meta.get("materialize_params") if isinstance(meta.get("materialize_params"), dict) else {}
            if _G_OFFSET_OVERRIDE_PS is not None:
                mparams = dict(mparams)
                # User-forced delay/offset in ps to bypass peak-search/template constraints.
                mparams["offset_override_ps"] = int(_G_OFFSET_OVERRIDE_PS)
                mparams["delay_override_ps"] = int(_G_OFFSET_OVERRIDE_PS)
            if _G_COINC_WINDOW_OVERRIDE_PS is not None:
                mparams = dict(mparams)
                mparams["coinc_window_override_ps"] = int(_G_COINC_WINDOW_OVERRIDE_PS)
            max_pairs_use = _materialize_max_pairs_for_dimension(d=int(d), requested=mparams.get("max_pairs"))
            frame_period_ps = int(max(1, int(d)) * max(1, int(bw)))
            nearest_threshold_ps = max(1, int(float(os.getenv("HDQKD_NEAREST_FRAME_THRESHOLD_PS", "40000"))))
            force_nearest_highdim = bool(frame_period_ps >= nearest_threshold_ps)
            pairing_mode_req = str(mparams.get("pairing_mode") or "nearest").strip().lower() or "nearest"
            pairing_mode_use = "nearest" if force_nearest_highdim else pairing_mode_req
            delay_override_req = mparams.get("delay_override_ps")
            delay_override_use = delay_override_req
            if force_nearest_highdim and str(delay_override_req).strip() in {"", "0", "0.0", "None", "nan"}:
                delay_override_use = None
            if force_nearest_highdim:
                logs.append(
                    f"[E2E][PAIRING_POLICY] point=({d},{bw}) frame_period_ps={frame_period_ps} "
                    f"threshold_ps={nearest_threshold_ps} mode_req={pairing_mode_req} mode_use={pairing_mode_use} "
                    f"delay_req={delay_override_req} delay_use={delay_override_use}"
                )
            if cond_C_force:
                pre = _extract_align_debug_from_meta(meta)
                logs.append(
                    f"[E2E][ALIGN_DEBUG][pre] point=({d},{bw}) "
                    f"corr_bins={pre.get('corr_bins')} corr_max={pre.get('corr_max')} "
                    f"corr_nonzero={pre.get('corr_nonzero')} peak_status={pre.get('peak_status')} "
                    f"peak_center_ps={pre.get('peak_center_ps')} peak_to_bg={pre.get('peak_to_bg')}"
                )
            shm_a: multiprocessing.shared_memory.SharedMemory | None = None
            shm_b: multiprocessing.shared_memory.SharedMemory | None = None
            shared_t0: np.ndarray | None = None
            shared_t1: np.ndarray | None = None
            global_peak_center_ps: int | None = None
            try:
                point_key = f"{int(d)},{int(bw)}"
                ttbin_key = _G_TTBIN_BY_POINT.get(point_key)
                if ttbin_key:
                    sm = _G_SHARED_BY_TTBIN.get(ttbin_key)
                    if isinstance(sm, dict):
                        dtype = np.dtype(str(sm.get("dtype", "int64")))
                        shape_a = tuple(int(x) for x in sm.get("shape_a", []))
                        shape_b = tuple(int(x) for x in sm.get("shape_b", []))
                        shm_a_name = str(sm.get("shm_a_name") or "")
                        shm_b_name = str(sm.get("shm_b_name") or "")
                        if shm_a_name and shm_b_name and shape_a and shape_b:
                            shm_a = multiprocessing.shared_memory.SharedMemory(name=shm_a_name)
                            shm_b = multiprocessing.shared_memory.SharedMemory(name=shm_b_name)
                            shared_t0 = np.ndarray(shape_a, dtype=dtype, buffer=shm_a.buf)
                            shared_t1 = np.ndarray(shape_b, dtype=dtype, buffer=shm_b.buf)
                            gpk = sm.get("global_peak_center_ps")
                            try:
                                global_peak_center_ps = int(gpk) if gpk is not None else None
                            except Exception:
                                global_peak_center_ps = None
                res = export_sidecar_for_point(
                    point=f"{d},{bw}",
                    factor=int(factor),
                    block_index=0,
                    out_root=str(sidecar_root),
                    sequence_source_mode="strict",
                    materialize_missing_real_seq=1,
                    joint_source_mode="from_ttbin",
                    materialize_diagnostics=1,
                    materialize_offset_override_ps=mparams.get("offset_override_ps"),
                    materialize_max_pairs=int(max_pairs_use),
                    materialize_frame_start_override_ps=mparams.get("frame_start_override_ps"),
                    materialize_coinc_window_override_ps=mparams.get("coinc_window_override_ps"),
                    materialize_pairing_mode=str(pairing_mode_use),
                    materialize_peak_gate_sigma=mparams.get("peak_gate_sigma"),
                    materialize_delay_override_ps=delay_override_use,
                    materialize_processing_rule_version=processing_rule_version_use,
                    materialize_shared_t0_ps=shared_t0,
                    materialize_shared_t1_ps=shared_t1,
                    materialize_global_peak_center_ps=global_peak_center_ps,
                    pool_root=(str(_G_REAL_SEQ_POOL_ROOT) if _G_REAL_SEQ_POOL_ROOT else None),
                )
                map_ser = float(res.get("map_ser", float("nan")))
                sidecar_verdict = str(res.get("verdict") or "").strip().upper()
                fail_reason = str(res.get("fail_reason") or "").strip()
                can_files = (sidecar_root / "a_eff.npy").exists() and (sidecar_root / "b_eff.npy").exists()
                re_align_ok = bool(can_files)
                if not can_files:
                    re_align_reason = str(res.get("fail_reason") or "materialize_no_output_files")
                if cond_C_force:
                    res_mparams = res.get("materialize_params") if isinstance(res.get("materialize_params"), dict) else {}
                    used = res_mparams.get("used_params") if isinstance(res_mparams.get("used_params"), dict) else {}
                    logs.append(
                        f"[E2E][ALIGN_DEBUG][post] point=({d},{bw}) "
                        f"corr_bins={used.get('corr_bins')} corr_max={used.get('corr_max')} "
                        f"corr_nonzero={used.get('corr_nonzero')} corr_argmax={used.get('corr_argmax')} "
                        f"peak_status={used.get('peak_status')} peak_center_ps={used.get('peak_center_ps')} "
                        f"peak_to_bg={used.get('peak_to_bg')} scan_range={used.get('peak_scan_range_ps')} "
                        f"bin_ps={used.get('peak_bin_ps')}"
                    )
            except Exception as e:
                re_align_ok = False
                re_align_reason = f"{type(e).__name__}: {e}"
            finally:
                if shm_a is not None:
                    try:
                        shm_a.close()
                    except Exception:
                        pass
                if shm_b is not None:
                    try:
                        shm_b.close()
                    except Exception:
                        pass
        else:
            ms_csv = sidecar_root / "map_sanity.csv"
            if ms_csv.exists():
                try:
                    with ms_csv.open("r", encoding="utf-8", newline="") as f:
                        rr = list(csv.DictReader(f))
                    if rr:
                        map_ser = float(rr[0].get("map_ser", "nan"))
                except Exception:
                    map_ser = float("nan")
            if not math.isfinite(map_ser) and isinstance(meta.get("map_sanity"), dict):
                try:
                    map_ser = float(meta["map_sanity"].get("map_ser", "nan"))
                except Exception:
                    map_ser = float("nan")

        meta = _read_json(meta_path)
        align_dbg = _extract_align_debug_from_meta(meta)
        meta_map_sanity = meta.get("map_sanity") if isinstance(meta.get("map_sanity"), dict) else {}
        sidecar_verdict_meta = str(meta_map_sanity.get("verdict") or "").strip().upper()
        if sidecar_verdict_meta:
            sidecar_verdict = sidecar_verdict_meta
        fail_reason_meta = str(meta.get("fail_reason") or "").strip()
        if fail_reason_meta:
            fail_reason = fail_reason_meta
        rate = float("nan")
        try:
            rate = _as_float((grid_row or {}).get("coincidence_rate_hz", "nan"))
        except Exception:
            rate = float("nan")
        if not math.isfinite(rate):
            rate = _recover_rate_from_sidecar_meta(meta)
        can_run = a_path.exists() and b_path.exists()
        if can_run:
            rate_eff = _compute_effective_rate_from_sidecar(sidecar_root, meta)
            if math.isfinite(rate_eff) and rate_eff > 0.0:
                rate = float(rate_eff)
        if not sidecar_verdict:
            if can_run and math.isfinite(map_ser):
                sidecar_verdict = "PASS" if float(map_ser) < 0.1 else "FAIL"
            elif can_run:
                sidecar_verdict = "UNKNOWN"
            else:
                sidecar_verdict = "MISSING"
        status_output = sidecar_verdict if can_run else "MISSING"
        run_grid_row = None
        run_src_row = None
        runnable_key = None
        if can_run:
            runnable_key = key
            run_grid_row = {
                "dimension": int(d),
                "bin_width_ps": int(bw),
                "status": status_output,
                "out_root": str(out_root),
                "coincidence_rate_hz": rate if math.isfinite(rate) else "",
            }
            run_src_row = {
                "dimension": int(d),
                "bin_width_ps": int(bw),
                "status": status_output,
                "input_status": input_status,
                "sidecar_verdict": sidecar_verdict,
                "fail_reason": fail_reason,
                "map_ser": map_ser if math.isfinite(map_ser) else "",
            }

        audit_row = {
            "dimension": int(d),
            "bin_width_ps": int(bw),
            "sidecar_root": str(sidecar_root),
            "ttbin_path": str(ttbin_path) if ttbin_path is not None else "",
            "cond_A_missing_a_or_b": int(cond_A_missing),
            "cond_B_ttbin_newer_than_aeff": int(cond_B_newer_ttbin),
            "cond_C_force_align": int(cond_C_force),
            "cond_D_missing_diagnostics": int(cond_D_diag_incomplete),
            "need_realign": int(need_realign),
            "realign_ok": "" if re_align_ok is None else int(bool(re_align_ok)),
            "realign_error": re_align_reason,
            "can_run_polar": int(can_run),
            "input_status": input_status,
            "status_output": status_output,
            "sidecar_verdict": sidecar_verdict,
            "fail_reason": fail_reason,
            "map_ser": map_ser if math.isfinite(map_ser) else "",
            "coincidence_rate_hz": rate if math.isfinite(rate) else "",
            "corr_bins": align_dbg.get("corr_bins", ""),
            "corr_nonzero": align_dbg.get("corr_nonzero", ""),
            "corr_argmax": align_dbg.get("corr_argmax", ""),
            "corr_max": align_dbg.get("corr_max", ""),
            "peak_center_ps": align_dbg.get("peak_center_ps", ""),
            "peak_sigma_ps": align_dbg.get("peak_sigma_ps", ""),
            "peak_to_bg": align_dbg.get("peak_to_bg", ""),
            "peak_status": align_dbg.get("peak_status", ""),
            "peak_scan_range_ps": align_dbg.get("peak_scan_range_ps", ""),
            "peak_bin_ps": align_dbg.get("peak_bin_ps", ""),
            "materialize_processing_rule_version": processing_rule_version_use,
        }
        logs.append(
            f"[E2E] point=({d},{bw}) need_realign={int(need_realign)} "
            f"A={int(cond_A_missing)} B={int(cond_B_newer_ttbin)} C={int(cond_C_force)} D={int(cond_D_diag_incomplete)} "
            f"can_run={int(can_run)}"
        )
        return {
            "key": key,
            "audit_row": audit_row,
            "run_grid_row": run_grid_row,
            "run_src_row": run_src_row,
            "runnable_key": runnable_key,
            "logs": logs,
        }
    except Exception as e:
        key = (int(d), int(bw))
        return {
            "key": key,
            "audit_row": {
                "dimension": int(d),
                "bin_width_ps": int(bw),
                "sidecar_root": "",
                "ttbin_path": "",
                "cond_A_missing_a_or_b": "",
                "cond_B_ttbin_newer_than_aeff": "",
                "cond_C_force_align": int(_G_FORCE_ALIGN),
                "cond_D_missing_diagnostics": "",
                "need_realign": "",
                "realign_ok": 0,
                "realign_error": f"worker_exception:{type(e).__name__}:{e}",
                "can_run_polar": 0,
                "input_status": "",
                "status_output": "",
                "sidecar_verdict": "",
                "fail_reason": "",
                "map_ser": "",
                "coincidence_rate_hz": "",
                "corr_bins": "",
                "corr_nonzero": "",
                "corr_argmax": "",
                "corr_max": "",
                "peak_center_ps": "",
                "peak_sigma_ps": "",
                "peak_to_bg": "",
                "peak_status": "",
                "peak_scan_range_ps": "",
                "peak_bin_ps": "",
                "materialize_processing_rule_version": str(_G_MATERIALIZE_PROCESSING_RULE_VERSION or "legacy_v1").strip().lower() or "legacy_v1",
            },
            "run_grid_row": None,
            "run_src_row": None,
            "runnable_key": None,
            "logs": logs + [f"[E2E] point=({d},{bw}) worker_exception: {type(e).__name__}: {e}"],
        }


def _parse_int_list(spec: str) -> list[int]:
    out: list[int] = []
    for t in str(spec).split(","):
        s = t.strip()
        if not s:
            continue
        out.append(int(s))
    return sorted(set(out))


def _as_float(v: Any) -> float:
    return float(v)


def _to_float_or_none(v: Any) -> float | None:
    try:
        fv = float(v)
    except Exception:
        return None
    return fv if math.isfinite(fv) else None


def _resolve_path(p: str | Path) -> Path:
    return resolve_repo_path(REPO_ROOT, p)


def _load_grid_rows(grid_table: Path) -> dict[tuple[int, int], dict[str, str]]:
    with grid_table.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    out: dict[tuple[int, int], dict[str, str]] = {}
    for r in rows:
        try:
            d = int(float(r.get("dimension", "nan")))
            bw = int(float(r.get("bin_width_ps", "nan")))
        except Exception:
            continue
        out[(d, bw)] = r
    return out


def _read_rate_from_attempt_scan(attempt_dir: Path) -> float:
    scan_csv = attempt_dir / "scan" / "pie_skr_scan.csv"
    if not scan_csv.exists():
        return float("nan")
    try:
        with scan_csv.open("r", encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
    except Exception:
        return float("nan")
    if not rows:
        return float("nan")
    try:
        v = rows[0].get("coincidence_rate_hz")
        return float(v) if v is not None and str(v).strip() != "" else float("nan")
    except Exception:
        return float("nan")


def _bootstrap_missing_point(
    *,
    d: int,
    bw: int,
    grid_map: dict[tuple[int, int], dict[str, str]],
    out_root: Path,
) -> dict[str, Any]:
    # Prefer highest available dimension at same bw as template.
    cand_dims = sorted([dd for (dd, bb) in grid_map.keys() if int(bb) == int(bw)], reverse=True)
    if cand_dims:
        template_d = int(cand_dims[0])
        template_bw = int(bw)
    else:
        # Fallback for out-of-grid bin widths: pick nearest available bw, then highest d.
        bws = sorted(set(int(bb) for (_, bb) in grid_map.keys()))
        if not bws:
            raise FileNotFoundError(f"no template points found in grid for bootstrap (target bw={bw})")
        template_bw = min(bws, key=lambda x: (abs(int(x) - int(bw)), x))
        cand_dims2 = sorted([dd for (dd, bb) in grid_map.keys() if int(bb) == int(template_bw)], reverse=True)
        if not cand_dims2:
            raise FileNotFoundError(f"no template points found for nearest bw={template_bw} (target bw={bw})")
        template_d = int(cand_dims2[0])
    template_point = f"{template_d},{template_bw}"
    ctx = resolve_point_sources(template_point)
    point_dir = Path(ctx["point_dir"])
    metrics_path = Path(ctx["metrics_path"])
    cfg = dict(ctx["resolved_config"])

    # Build minimal point artifacts expected by find_point_artifacts().
    boot_point_dir = REPO_ROOT / "results" / "e2e_bootstrap_points" / f"d{d}_bw{bw}"
    attempt_dir = boot_point_dir / "results" / "attempt_0"
    metrics_out = attempt_dir / "ttbin_parsing" / "ttbin_metrics.json"
    cfg_out = attempt_dir / "resolved_config.json"
    attempt_dir.mkdir(parents=True, exist_ok=True)
    metrics_out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(metrics_path, metrics_out)

    # Patch config dimension/framing to target.
    cfg["dimension"] = int(d)
    ttbin_cfg = cfg.get("ttbin") if isinstance(cfg.get("ttbin"), dict) else {}
    framing = ttbin_cfg.get("framing") if isinstance(ttbin_cfg.get("framing"), dict) else {}
    framing["frame_bins"] = int(d)
    framing["bin_width_ps"] = int(bw)
    ttbin_cfg["framing"] = framing
    cfg["ttbin"] = ttbin_cfg
    cfg_out.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    (boot_point_dir / "point_summary.json").write_text(
        json.dumps({"chosen_attempt": "attempt_0", "bootstrap_from_point": template_point}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    template_attempt = point_dir / "results" / "attempt_0"
    rate = _read_rate_from_attempt_scan(template_attempt)
    return {
        "ok": True,
        "template_point": template_point,
        "boot_point_dir": str(boot_point_dir),
        "rate": rate,
    }


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _resolve_sidecar_artifact_path(sidecar_root: Path, path_text: Any, default_name: str) -> Path:
    p = str(path_text or "").strip()
    if p:
        pp = Path(p)
        if pp.is_absolute():
            return pp
        return (sidecar_root / pp).resolve()
    return sidecar_root / default_name


def _sidecar_diagnostics_complete(sidecar_root: Path, meta: dict[str, Any]) -> tuple[bool, str]:
    mparams = meta.get("materialize_params") if isinstance(meta.get("materialize_params"), dict) else {}
    used = mparams.get("used_params") if isinstance(mparams.get("used_params"), dict) else {}
    peak_sigma_ps = _to_float_or_none(used.get("peak_sigma_ps"))
    peak_to_bg = _to_float_or_none(used.get("peak_to_bg"))
    if peak_sigma_ps is None:
        return False, "missing_peak_sigma_ps"
    if peak_to_bg is None:
        return False, "missing_peak_to_bg"

    diag = meta.get("diagnostics") if isinstance(meta.get("diagnostics"), dict) else {}
    if int(diag.get("enabled") or 0) != 1:
        return False, "diagnostics_disabled"

    stats_path = _resolve_sidecar_artifact_path(sidecar_root, diag.get("seq_pair_stats_path"), "seq_pair_stats.json")
    if not stats_path.exists():
        return False, "missing_seq_pair_stats_json"
    stats = _read_json(stats_path)
    for key in (
        "raw_ser",
        "near_neighbor_frac",
        "n_pairs_actual",
        "n_unique_a",
        "n_unique_b",
        "top_a_frac",
        "top_b_frac",
    ):
        v = stats.get(key)
        if v is None or str(v).strip() == "":
            return False, f"missing_{key}"
    return True, ""


def _extract_ttbin_from_meta(meta: dict[str, Any]) -> Path | None:
    mparams = meta.get("materialize_params") if isinstance(meta.get("materialize_params"), dict) else {}
    used = mparams.get("used_params") if isinstance(mparams.get("used_params"), dict) else {}
    cand = str(used.get("source_ttbin_paths") or "").strip()
    if not cand:
        return None
    tokens = [x.strip() for x in cand.split(";") if x.strip()]
    for t in tokens:
        if ".ttbin" in t.lower():
            if "=" in t:
                t = t.split("=", 1)[-1].strip()
            p = _resolve_path(t)
            if p.exists() and p.suffix.lower() == ".ttbin":
                return p
    p = _resolve_path(cand)
    if p.exists() and p.suffix.lower() == ".ttbin":
        return p
    return None


def _extract_ttbin_from_ctx(point: str) -> Path | None:
    try:
        ctx = resolve_point_sources(point)
    except Exception:
        return None
    cfg = ctx.get("resolved_config") if isinstance(ctx.get("resolved_config"), dict) else {}
    ttbin_cfg = cfg.get("ttbin") if isinstance(cfg.get("ttbin"), dict) else {}
    p = str(ttbin_cfg.get("file") or "").strip()
    if not p:
        return None
    pp = _resolve_path(p)
    if pp.exists() and pp.suffix.lower() == ".ttbin":
        return pp
    return None


def _recover_rate_from_sidecar_meta(meta: dict[str, Any]) -> float:
    # First try direct metrics path if sidecar stores it.
    try:
        src_joint = str(meta.get("source_joint_path") or "").strip()
        if src_joint:
            metrics_path_s = src_joint.split("#", 1)[0].strip()
            if metrics_path_s:
                mp = _resolve_path(metrics_path_s)
                if mp.exists():
                    mj = _read_json(mp)
                    coinc = mj.get("coincidences") if isinstance(mj.get("coincidences"), dict) else {}
                    v = coinc.get("coincidence_rate_hz")
                    if v is not None and str(v).strip() != "":
                        fv = float(v)
                        if math.isfinite(fv):
                            return fv
    except Exception:
        pass

    src = str(meta.get("source_point_dir") or "").strip()
    if not src:
        return float("nan")
    sp = _resolve_path(src)
    if not sp.exists():
        return float("nan")
    for scan_csv in sp.rglob("pie_skr_scan.csv"):
        try:
            with scan_csv.open("r", encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader(f))
        except Exception:
            continue
        if not rows:
            continue
        v = rows[0].get("coincidence_rate_hz")
        try:
            fv = float(v) if v is not None and str(v).strip() != "" else float("nan")
        except Exception:
            fv = float("nan")
        if math.isfinite(fv):
            return fv
    return float("nan")


def _extract_acquisition_duration_s_from_metrics(metrics: dict[str, Any]) -> float:
    """Best-effort acquisition duration extraction from ttbin metrics payload."""
    try:
        events = metrics.get("events_summary") if isinstance(metrics.get("events_summary"), dict) else {}
        v = events.get("acquisition_duration_s")
        if v is not None and str(v).strip() != "":
            fv = float(v)
            if math.isfinite(fv) and fv > 0.0:
                return fv
        span = events.get("timetag_span")
        if span is not None and str(span).strip() != "":
            fs = float(span) * 1e-12  # project convention: ps -> s
            if math.isfinite(fs) and fs > 0.0:
                return fs
    except Exception:
        pass

    try:
        v = metrics.get("acquisition_duration_s")
        if v is not None and str(v).strip() != "":
            fv = float(v)
            if math.isfinite(fv) and fv > 0.0:
                return fv
    except Exception:
        pass
    return float("nan")


def _resolve_metrics_path_from_meta(meta: dict[str, Any]) -> Path | None:
    try:
        src_joint = str(meta.get("source_joint_path") or "").strip()
        if src_joint:
            mp_s = src_joint.split("#", 1)[0].strip()
            if mp_s:
                mp = _resolve_path(mp_s)
                if mp.exists():
                    return mp
    except Exception:
        pass

    try:
        src = str(meta.get("source_point_dir") or "").strip()
        if src:
            sp = _resolve_path(src)
            if sp.exists():
                cands = sorted(sp.rglob("ttbin_metrics.json"))
                if cands:
                    return cands[-1]
    except Exception:
        pass
    return None


def _compute_effective_rate_from_sidecar(sidecar_root: Path, meta: dict[str, Any]) -> float:
    """
    Effective symbol rate used for SKR:
      coincidence_rate_hz = n_symbols_effective / acquisition_duration_s
    """
    n_symbols = 0
    a_path = sidecar_root / "a_eff.npy"
    if a_path.exists():
        try:
            n_symbols = int(np.load(a_path, mmap_mode="r").shape[0])
        except Exception:
            n_symbols = 0
    if n_symbols <= 0:
        try:
            n_symbols = int(float(meta.get("n_symbols") or 0))
        except Exception:
            n_symbols = 0
    if n_symbols <= 0:
        return float("nan")

    acq_s = float("nan")
    mp = _resolve_metrics_path_from_meta(meta)
    if mp is not None and mp.exists():
        mj = _read_json(mp)
        acq_s = _extract_acquisition_duration_s_from_metrics(mj)
    if (not math.isfinite(acq_s)) or acq_s <= 0.0:
        acq_s = 5.0
    return float(n_symbols) / float(acq_s)


def _materialize_max_pairs_for_dimension(d: int, requested: Any) -> int:
    """
    Resolve max_pairs for sidecar materialization.
    Return 0 to mean "uncapped/use all available pairs".
    This removes legacy hard caps (e.g., 16384 wall) for high-d points.
    """
    try:
        req = int(round(float(requested)))
    except Exception:
        req = 0
    if req <= 0:
        return 0
    # Legacy tiny defaults (often 256) should not cap high-dimensional extraction.
    if int(d) >= 1024 and req <= 256:
        return 0
    return max(0, int(req))


def _extract_align_debug_from_meta(meta: dict[str, Any]) -> dict[str, Any]:
    mparams = meta.get("materialize_params") if isinstance(meta.get("materialize_params"), dict) else {}
    used = mparams.get("used_params") if isinstance(mparams.get("used_params"), dict) else {}
    return {
        "corr_bins": used.get("corr_bins"),
        "corr_nonzero": used.get("corr_nonzero"),
        "corr_argmax": used.get("corr_argmax"),
        "corr_max": used.get("corr_max"),
        "peak_center_ps": used.get("peak_center_ps"),
        "peak_sigma_ps": used.get("peak_sigma_ps"),
        "peak_to_bg": used.get("peak_to_bg"),
        "peak_status": used.get("peak_status"),
        "peak_scan_range_ps": used.get("peak_scan_range_ps"),
        "peak_bin_ps": used.get("peak_bin_ps"),
    }


def _write_tmp_csv(path: Path, rows: list[dict[str, Any]], cols: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def _extract_channels_from_cfg(cfg: dict[str, Any]) -> tuple[int, int]:
    ch_ids = (cfg.get("ttbin") if isinstance(cfg.get("ttbin"), dict) else {}).get("channels")
    raw_ch0 = 1
    raw_ch1 = 2
    if isinstance(ch_ids, dict):
        a_id = ch_ids.get("A")
        b_id = ch_ids.get("B")
        if a_id is not None:
            raw_ch0 = int(a_id)
        if b_id is not None:
            raw_ch1 = int(b_id)
    elif isinstance(ch_ids, (list, tuple)) and len(ch_ids) >= 2:
        raw_ch0 = int(ch_ids[0])
        raw_ch1 = int(ch_ids[1])
    return int(raw_ch0), int(raw_ch1)


def _preflight_ttbin_source_for_point(
    d: int,
    bw: int,
    grid_map: dict[tuple[int, int], dict[str, str]],
) -> dict[str, Any] | None:
    point = f"{int(d)},{int(bw)}"
    ctx = None
    try:
        ctx = resolve_point_sources(point)
    except Exception:
        ctx = None
    if ctx is None:
        # Match bootstrap behavior: use highest available dimension at same bw as template.
        cand_dims = sorted([dd for (dd, bb) in grid_map.keys() if int(bb) == int(bw)], reverse=True)
        if cand_dims:
            template_point = f"{int(cand_dims[0])},{int(bw)}"
        else:
            # Fallback for out-of-grid bin widths: nearest available bw then highest d.
            bws = sorted(set(int(bb) for (_, bb) in grid_map.keys()))
            if not bws:
                return None
            bw_near = min(bws, key=lambda x: (abs(int(x) - int(bw)), x))
            cand_dims2 = sorted([dd for (dd, bb) in grid_map.keys() if int(bb) == int(bw_near)], reverse=True)
            if not cand_dims2:
                return None
            template_point = f"{int(cand_dims2[0])},{int(bw_near)}"
        try:
            ctx = resolve_point_sources(template_point)
        except Exception:
            return None
    if not isinstance(ctx, dict):
        return None
    cfg = ctx.get("resolved_config") if isinstance(ctx.get("resolved_config"), dict) else {}
    ttbin_cfg = cfg.get("ttbin") if isinstance(cfg.get("ttbin"), dict) else {}
    ttbin_path_s = str(ttbin_cfg.get("file") or "").strip()
    if not ttbin_path_s:
        return None
    ttbin_path = _resolve_path(ttbin_path_s)
    if not ttbin_path.exists():
        return None
    raw_ch0, raw_ch1 = _extract_channels_from_cfg(cfg)
    return {
        "point_key": point,
        "d": int(d),
        "bw": int(bw),
        "ttbin_key": str(ttbin_path.resolve()),
        "raw_ch0": int(raw_ch0),
        "raw_ch1": int(raw_ch1),
        "frame_period_ps": int(max(1, int(d)) * max(1, int(bw))),
    }


def _create_shared_for_ttbin_group(items: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], list[multiprocessing.shared_memory.SharedMemory]]:
    if not items:
        return {}, []
    first = items[0]
    ttbin_key = str(first["ttbin_key"])
    ttbin_path = Path(ttbin_key)
    raw_ch0 = int(first["raw_ch0"])
    raw_ch1 = int(first["raw_ch1"])
    # Parse once in main process.
    tt = _read_ttbin_timetags(ttbin_path, raw_ch0_id=raw_ch0, raw_ch1_id=raw_ch1)
    ch = np.asarray(tt.Ch, dtype=np.int64)
    ts = np.asarray(tt.TimeTag, dtype=np.int64)
    t0 = np.sort(ts[ch == 0])
    t1 = np.sort(ts[ch == 1])
    if t0.size == 0 or t1.size == 0:
        return {}, []

    max_frame_ps = max(int(it["frame_period_ps"]) for it in items)
    min_bw = min(int(it["bw"]) for it in items)
    peak_info = _estimate_peak_stats_from_timetags(
        t0,
        t1,
        scan_range_ps=max(50_000, 2 * int(max_frame_ps)),
        bin_ps=max(10, int(max(1, min_bw // 2))),
        frame_period_ps=int(max_frame_ps),
        max_hist_bins=400_001,
        debug=False,
    )
    gpeak = int(peak_info.get("peak_center_ps") or 0)

    shm_a = multiprocessing.shared_memory.SharedMemory(create=True, size=int(t0.nbytes))
    shm_b = multiprocessing.shared_memory.SharedMemory(create=True, size=int(t1.nbytes))
    try:
        a_view = np.ndarray(t0.shape, dtype=t0.dtype, buffer=shm_a.buf)
        b_view = np.ndarray(t1.shape, dtype=t1.dtype, buffer=shm_b.buf)
        a_view[:] = t0
        b_view[:] = t1
    except Exception:
        try:
            shm_a.close()
            shm_a.unlink()
        except Exception:
            pass
        try:
            shm_b.close()
            shm_b.unlink()
        except Exception:
            pass
        raise

    shared_meta = {
        ttbin_key: {
            "shm_a_name": str(shm_a.name),
            "shm_b_name": str(shm_b.name),
            "shape_a": list(t0.shape),
            "shape_b": list(t1.shape),
            "dtype": str(t0.dtype),
            "global_peak_center_ps": int(gpeak),
            "ttbin_path": str(ttbin_key),
            "raw_ch0": int(raw_ch0),
            "raw_ch1": int(raw_ch1),
        }
    }
    return shared_meta, [shm_a, shm_b]


def _run_extract_batch(
    points_batch: list[tuple[int, int]],
    *,
    extract_workers: int,
    grid_map: dict[tuple[int, int], dict[str, str]],
    out_root: Path,
    force_align: bool,
    offset_override_ps: int | None = None,
    coinc_window_override_ps: int | None = None,
    shared_by_ttbin: dict[str, dict[str, Any]] | None = None,
    ttbin_by_point: dict[str, str] | None = None,
    repair_diagnostics: bool = False,
    materialize_processing_rule_version: str = "legacy_v1",
    real_seq_pool_root: str = "",
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    _init_extract_worker(
        grid_map=grid_map,
        out_root_s=str(out_root),
        force_align=bool(force_align),
        offset_override_ps=offset_override_ps,
        coinc_window_override_ps=coinc_window_override_ps,
        shared_by_ttbin=shared_by_ttbin,
        ttbin_by_point=ttbin_by_point,
        repair_diagnostics=bool(repair_diagnostics),
        materialize_processing_rule_version=str(materialize_processing_rule_version),
        real_seq_pool_root=str(real_seq_pool_root or ""),
    )
    if extract_workers <= 1:
        iter_points = _progress(points_batch, total=len(points_batch), desc="E2E extract")
        for d, bw in iter_points:
            out.append(_extract_one_point(int(d), int(bw)))
        return out

    with concurrent.futures.ProcessPoolExecutor(
        max_workers=extract_workers,
        initializer=_init_extract_worker,
        initargs=(
            grid_map,
            str(out_root),
            bool(force_align),
            offset_override_ps,
            coinc_window_override_ps,
            dict(shared_by_ttbin or {}),
            dict(ttbin_by_point or {}),
            bool(repair_diagnostics),
            str(materialize_processing_rule_version),
            str(real_seq_pool_root or ""),
        ),
    ) as ex:
        fut_map: dict[concurrent.futures.Future[dict[str, Any]], tuple[int, int]] = {}
        for d, bw in points_batch:
            fut = ex.submit(_extract_one_point, int(d), int(bw))
            fut_map[fut] = (int(d), int(bw))
        done_iter = _progress(concurrent.futures.as_completed(fut_map), total=len(fut_map), desc="E2E extract")
        for fut in done_iter:
            key = fut_map[fut]
            try:
                out.append(fut.result())
            except Exception as e:
                out.append(
                    {
                        "key": key,
                        "audit_row": {
                            "dimension": int(key[0]),
                            "bin_width_ps": int(key[1]),
                            "sidecar_root": "",
                            "ttbin_path": "",
                            "cond_A_missing_a_or_b": "",
                            "cond_B_ttbin_newer_than_aeff": "",
                            "cond_C_force_align": int(bool(force_align)),
                            "need_realign": "",
                            "realign_ok": 0,
                            "realign_error": f"future_exception:{type(e).__name__}:{e}",
                            "can_run_polar": 0,
                            "map_ser": "",
                            "coincidence_rate_hz": "",
                            "corr_bins": "",
                            "corr_nonzero": "",
                            "corr_argmax": "",
                            "corr_max": "",
                            "peak_center_ps": "",
                            "peak_sigma_ps": "",
                            "peak_to_bg": "",
                            "peak_status": "",
                            "peak_scan_range_ps": "",
                            "peak_bin_ps": "",
                        },
                        "run_grid_row": None,
                        "run_src_row": None,
                        "runnable_key": None,
                        "logs": [f"[E2E] point=({key[0]},{key[1]}) future_exception: {type(e).__name__}: {e}"],
                    }
                )
    return out


def _resolve_ttbin_override_path(value: str) -> Path:
    """
    Resolve user-provided ttbin override path.
    - If value is a file: must be .ttbin.
    - If value is a directory: auto-pick main header .ttbin (exclude *.N.ttbin chunks).
    """
    p = _resolve_path(value)
    if p.is_file():
        if p.suffix.lower() != ".ttbin":
            raise FileNotFoundError(f"--ttbin-override points to non-ttbin file: {p}")
        return p.resolve()
    if not p.is_dir():
        raise FileNotFoundError(f"--ttbin-override path not found: {p}")

    # Swabian chunk files look like name.1.ttbin / name.2.ttbin...
    # Main header file should be *.ttbin and NOT match .*.<digits>.ttbin
    re_chunk = re.compile(r"\.\d+\.ttbin$", re.IGNORECASE)
    cands = [x for x in sorted(p.glob("*.ttbin")) if x.is_file() and (re_chunk.search(x.name) is None)]
    if not cands:
        raise FileNotFoundError(
            f"No main header .ttbin found in directory: {p}. "
            "Expected a file like data.ttbin (not data.1.ttbin / data.2.ttbin)."
        )
    if len(cands) == 1:
        return cands[0].resolve()

    # Prefer file whose stem matches directory name; otherwise shortest name.
    dir_name = p.name.lower()
    prefer = [x for x in cands if x.stem.lower() == dir_name]
    if prefer:
        return sorted(prefer)[0].resolve()
    return sorted(cands, key=lambda x: (len(x.name), x.name.lower()))[0].resolve()


def main() -> int:
    ap = argparse.ArgumentParser(
        description="E2E pipeline with stale-cache prevention (.ttbin mtime guard)",
        allow_abbrev=False,
    )
    ap.add_argument("--dims", required=True, help='e.g. "32,1024"')
    ap.add_argument("--bws", required=True, help='e.g. "30,150"')
    ap.add_argument("--force-align", action="store_true")
    ap.add_argument("--grid-table", default="results/grid_mixed_full_table.csv")
    ap.add_argument("--out-root", default="")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument(
        "--extract-workers",
        type=int,
        default=8,
        help="parallel workers for sidecar extraction stage (default: 8, capped to 15)",
    )
    ap.add_argument(
        "--offset-ps",
        type=int,
        default=None,
        help="manual delay/offset override in ps for sidecar extraction (applies to all requested points)",
    )
    ap.add_argument(
        "--coinc-window-override-ps",
        type=float,
        default=None,
        help="override coincidence/pairing window in ps for sidecar materialization (applies to all requested points)",
    )
    ap.add_argument("--N", type=int, default=4096)
    ap.add_argument("--frames", type=int, default=100)
    ap.add_argument("--visibility", type=float, default=0.95)
    ap.add_argument("--disable-scl", action="store_true")
    ap.add_argument("--acq-time", type=float, default=None, help="compat flag (currently unused)")
    ap.add_argument(
        "--skip-polar",
        action="store_true",
        help="complete sidecar repair/rematerialize and audit, but skip automatic polar refresh",
    )
    ap.add_argument(
        "--repair-diagnostics",
        action="store_true",
        help="reuse existing sidecars in out-root and rematerialize only points with missing peak/stat diagnostics",
    )
    ap.add_argument(
        "--ttbin",
        "--ttbin-override",
        "--ttbin-file-override",
        dest="ttbin_override",
        default="",
        help="override ttbin source for all points: accepts .ttbin file OR directory containing main header .ttbin",
    )
    ap.add_argument(
        "--ttbin-ch-a-override",
        type=int,
        default=None,
        help="override ttbin channel A id for all requested points (optional)",
    )
    ap.add_argument(
        "--ttbin-ch-b-override",
        type=int,
        default=None,
        help="override ttbin channel B id for all requested points (optional)",
    )
    ap.add_argument(
        "--materialize-processing-rule-version",
        choices=["legacy_v1", "pairing_v2"],
        default="legacy_v1",
        help="sidecar materialization processing rule version; use a dedicated --out-root for pairing_v2 batch runs",
    )
    ap.add_argument(
        "--real-seq-pool-root",
        dest="real_seq_pool_root",
        default="",
        help=(
            "optional root directory for materialized real-sequence pools "
            "(pools land at <root>/d{d}_bw{bw}/blk{b}; default: results/real_sequences)"
        ),
    )
    args = ap.parse_args()

    dims = _parse_int_list(args.dims)
    bws = _parse_int_list(args.bws)
    points = [(d, bw) for d in dims for bw in bws]

    # Runtime source overrides are propagated to worker processes via env.
    ttbin_override = str(args.ttbin_override or "").strip()
    if ttbin_override:
        ttbin_override_path = _resolve_ttbin_override_path(ttbin_override)
        os.environ["HDQKD_TTBIN_FILE_OVERRIDE"] = str(ttbin_override_path)
        print(f"[E2E] ttbin override file={ttbin_override_path}")
    else:
        os.environ.pop("HDQKD_TTBIN_FILE_OVERRIDE", None)
    if args.ttbin_ch_a_override is not None:
        os.environ["HDQKD_TTBIN_CH_A_OVERRIDE"] = str(int(args.ttbin_ch_a_override))
        print(f"[E2E] ttbin channel override A={int(args.ttbin_ch_a_override)}")
    else:
        os.environ.pop("HDQKD_TTBIN_CH_A_OVERRIDE", None)
    if args.ttbin_ch_b_override is not None:
        os.environ["HDQKD_TTBIN_CH_B_OVERRIDE"] = str(int(args.ttbin_ch_b_override))
        print(f"[E2E] ttbin channel override B={int(args.ttbin_ch_b_override)}")
    else:
        os.environ.pop("HDQKD_TTBIN_CH_B_OVERRIDE", None)
    if args.offset_ps is not None:
        print(f"[E2E] manual offset override ps={int(args.offset_ps)}")
    coinc_window_override_ps: int | None = None
    if args.coinc_window_override_ps is not None:
        coinc_window_override_ps = int(round(float(args.coinc_window_override_ps)))
        if coinc_window_override_ps <= 0:
            raise SystemExit("--coinc-window-override-ps must be > 0")
        print(f"[E2E] coincidence window override ps={coinc_window_override_ps}")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    real_seq_pool_root = str(args.real_seq_pool_root or "").strip()
    if real_seq_pool_root:
        print(f"[E2E] real-seq pool root={_resolve_path(real_seq_pool_root)}")
    out_root = _resolve_path(args.out_root) if str(args.out_root).strip() else (default_project_results_root(REPO_ROOT) / f"e2e_pipeline_{ts}")
    out_root.mkdir(parents=True, exist_ok=True)
    print(f"[E2E] materialize processing rule version={args.materialize_processing_rule_version}")

    grid_table = _resolve_path(args.grid_table)
    if grid_table.exists():
        grid_map = _load_grid_rows(grid_table)
    else:
        print(f"[E2E] grid_table not found, using override-only synthetic mode: {grid_table}")
        grid_map = {}

    audit_rows: list[dict[str, Any]] = []
    run_grid_rows: list[dict[str, Any]] = []
    run_src_rows: list[dict[str, Any]] = []
    runnable_points: list[tuple[int, int]] = []

    print(f"[E2E] points={points}")
    extract_workers = max(1, min(int(args.extract_workers), 15))
    print(f"[E2E] extraction workers={extract_workers}")
    # Preflight ttbin sources for shared-memory batches.
    preflight_items: list[dict[str, Any]] = []
    fallback_points: list[tuple[int, int]] = []
    for d, bw in points:
        pf = _preflight_ttbin_source_for_point(int(d), int(bw), grid_map=grid_map)
        if isinstance(pf, dict):
            preflight_items.append(pf)
        else:
            fallback_points.append((int(d), int(bw)))

    grouped: dict[str, list[dict[str, Any]]] = {}
    for it in preflight_items:
        grouped.setdefault(str(it["ttbin_key"]), []).append(it)

    all_results: list[dict[str, Any]] = []

    # Read-Once / Process-Many per ttbin group.
    for ttbin_key, items in grouped.items():
        shared_blocks: list[multiprocessing.shared_memory.SharedMemory] = []
        shared_by_ttbin: dict[str, dict[str, Any]] = {}
        ttbin_by_point: dict[str, str] = {}
        batch_points = [(int(it["d"]), int(it["bw"])) for it in items]
        try:
            shared_by_ttbin, shared_blocks = _create_shared_for_ttbin_group(items)
            if shared_by_ttbin:
                ttbin_by_point = {str(it["point_key"]): str(ttbin_key) for it in items}
                gpk = shared_by_ttbin.get(str(ttbin_key), {}).get("global_peak_center_ps")
                print(f"[E2E][SHM] ttbin={ttbin_key} points={len(batch_points)} global_peak_center_ps={gpk}")
            else:
                print(f"[E2E][SHM] ttbin={ttbin_key} shared_setup=skipped (empty channels)")
            batch_res = _run_extract_batch(
                batch_points,
                extract_workers=extract_workers,
                grid_map=grid_map,
                out_root=out_root,
                force_align=bool(args.force_align),
                offset_override_ps=args.offset_ps,
                coinc_window_override_ps=coinc_window_override_ps,
                shared_by_ttbin=shared_by_ttbin,
                ttbin_by_point=ttbin_by_point,
                repair_diagnostics=bool(args.repair_diagnostics),
                materialize_processing_rule_version=str(args.materialize_processing_rule_version),
                real_seq_pool_root=real_seq_pool_root,
            )
            all_results.extend(batch_res)
        finally:
            # Safe cleanup to avoid RAM leaks.
            for shm in shared_blocks:
                try:
                    shm.close()
                except Exception:
                    pass
                try:
                    shm.unlink()
                except Exception:
                    pass

    if fallback_points:
        print(f"[E2E][SHM] fallback points without preflight/shared source: {len(fallback_points)}")
        all_results.extend(
            _run_extract_batch(
                fallback_points,
                extract_workers=extract_workers,
                grid_map=grid_map,
                out_root=out_root,
                force_align=bool(args.force_align),
                offset_override_ps=args.offset_ps,
                coinc_window_override_ps=coinc_window_override_ps,
                shared_by_ttbin={},
                ttbin_by_point={},
                repair_diagnostics=bool(args.repair_diagnostics),
                materialize_processing_rule_version=str(args.materialize_processing_rule_version),
                real_seq_pool_root=real_seq_pool_root,
            )
        )

    for res in all_results:
        for line in res.get("logs") or []:
            print(line)
        audit_rows.append(dict(res["audit_row"]))
        rg = res.get("run_grid_row")
        rs = res.get("run_src_row")
        rk = res.get("runnable_key")
        if isinstance(rg, dict) and isinstance(rs, dict) and isinstance(rk, tuple):
            run_grid_rows.append(rg)
            run_src_rows.append(rs)
            runnable_points.append((int(rk[0]), int(rk[1])))

    audit_rows.sort(key=lambda r: (int(r.get("dimension", 10**9) or 10**9), int(r.get("bin_width_ps", 10**9) or 10**9)))
    run_grid_rows.sort(key=lambda r: (int(r.get("dimension", 10**9) or 10**9), int(r.get("bin_width_ps", 10**9) or 10**9)))
    run_src_rows.sort(key=lambda r: (int(r.get("dimension", 10**9) or 10**9), int(r.get("bin_width_ps", 10**9) or 10**9)))
    runnable_points = sorted(set(runnable_points))

    audit_csv = out_root / "e2e_alignment_audit.csv"
    _write_tmp_csv(
        audit_csv,
        audit_rows,
        [
            "dimension",
            "bin_width_ps",
            "sidecar_root",
            "ttbin_path",
            "cond_A_missing_a_or_b",
            "cond_B_ttbin_newer_than_aeff",
            "cond_C_force_align",
            "cond_D_missing_diagnostics",
            "need_realign",
            "realign_ok",
            "realign_error",
            "can_run_polar",
            "input_status",
            "status_output",
            "sidecar_verdict",
            "fail_reason",
            "map_ser",
            "coincidence_rate_hz",
            "corr_bins",
            "corr_nonzero",
            "corr_argmax",
            "corr_max",
            "peak_center_ps",
            "peak_sigma_ps",
            "peak_to_bg",
            "peak_status",
            "peak_scan_range_ps",
            "peak_bin_ps",
            "materialize_processing_rule_version",
        ],
    )
    print(f"[E2E] audit_csv={audit_csv}")

    if not runnable_points:
        print("[E2E] No runnable points (no valid sidecar sequences).")
        return 0

    tmp_grid = out_root / "_tmp_grid_table.csv"
    tmp_src = out_root / "_tmp_src_table.csv"
    _write_tmp_csv(tmp_grid, run_grid_rows, ["dimension", "bin_width_ps", "status", "out_root", "coincidence_rate_hz"])
    _write_tmp_csv(
        tmp_src,
        run_src_rows,
        ["dimension", "bin_width_ps", "status", "input_status", "sidecar_verdict", "fail_reason", "map_ser"],
    )

    if bool(args.skip_polar):
        print("[E2E] skip polar refresh: enabled by --skip-polar")
        print(f"[E2E] tmp_grid={tmp_grid}")
        print(f"[E2E] tmp_src={tmp_src}")
        return 0

    pts = ";".join(f"{d},{bw}" for (d, bw) in runnable_points)
    out_csv = out_root / "polar_e2e_results.csv"
    cmd = [
        sys.executable,
        str(REPO_ROOT / "experiments" / "run_real_polar_max_pie.py"),
        "--grid-table",
        str(tmp_grid),
        "--in-csv",
        str(tmp_src),
        "--out-csv",
        str(out_csv),
        "--only-points",
        pts,
        "--jobs",
        str(max(1, int(args.jobs))),
        "--N",
        str(int(args.N)),
        "--frames",
        str(int(args.frames)),
        "--visibility",
        str(float(args.visibility)),
    ]
    if bool(args.disable_scl):
        cmd.append("--disable-scl")

    print("[E2E] Running polar stage:")
    print(" ".join(cmd))
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT))
    if proc.returncode != 0:
        print(f"[E2E] polar stage failed rc={proc.returncode}")
        return int(proc.returncode)

    # Append-style consolidated log
    append_csv = REPO_ROOT / "results" / "e2e_pipeline_append.csv"
    rows = []
    with out_csv.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    append_exists = append_csv.exists()
    with append_csv.open("a", encoding="utf-8", newline="") as f:
        cols = ["timestamp"] + list(rows[0].keys()) if rows else ["timestamp"]
        w = csv.DictWriter(f, fieldnames=cols)
        if not append_exists:
            w.writeheader()
        for r in rows:
            rr = {"timestamp": datetime.now().isoformat()}
            rr.update(r)
            w.writerow(rr)

    print(f"[E2E] out_csv={out_csv}")
    print(f"[E2E] append_csv={append_csv}")
    for r in rows:
        d = int(float(r["dimension"]))
        bw = int(float(r["bin_width_ps"]))
        print(
            f"[E2E][RESULT] ({d},{bw}) PIE_practical={r.get('PIE_practical')} "
            f"SKR_measured_bps={r.get('SKR_measured_bps')}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
