#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import multiprocessing as mp
import sys
from pathlib import Path
from typing import Any

import numpy as np
from numba import njit

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.reconciliation.cpp_scl_wrapper import PolarSCLDecoder  # type: ignore
from src.reconciliation.real_polar_sc_rescue import (  # type: ignore
    _polar_weight_order,
    polar_encode_non_systematic,
    polar_sc_decode,
)


def _as_int(v: Any) -> int:
    return int(float(v))


def _as_float(v: Any) -> float:
    return float(v)


def _to_float_or_none(v: Any) -> float | None:
    if v is None:
        return None
    if isinstance(v, str) and str(v).strip() == "":
        return None
    try:
        fv = float(v)
    except Exception:
        return None
    if not math.isfinite(fv):
        return None
    return float(fv)


def _to_int_or_none(v: Any) -> int | None:
    if v is None:
        return None
    if isinstance(v, str) and str(v).strip() == "":
        return None
    try:
        return int(float(v))
    except Exception:
        return None


def _json_dict(path: Path) -> dict[str, Any]:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return obj if isinstance(obj, dict) else {}


def _resolve_sidecar_path(sidecar_root: Path, path_text: str | None) -> Path | None:
    p = str(path_text or "").strip()
    if not p:
        return None
    pp = Path(p)
    if pp.is_absolute():
        return pp
    return (sidecar_root / pp).resolve()


def _compute_light_pair_stats(a_eff: np.ndarray, b_eff: np.ndarray, d: int) -> dict[str, Any]:
    out: dict[str, Any] = {
        "raw_ser": None,
        "near_neighbor_frac": None,
        "n_pairs_actual": None,
        "n_unique_a": None,
        "n_unique_b": None,
        "top_a_frac": None,
        "top_b_frac": None,
    }
    q = int(d)
    n = int(min(a_eff.size, b_eff.size))
    if q <= 0 or n <= 0:
        return out
    aa = np.clip(np.asarray(a_eff[:n], dtype=np.int64), 0, q - 1)
    bb = np.clip(np.asarray(b_eff[:n], dtype=np.int64), 0, q - 1)

    out["n_pairs_actual"] = int(n)
    out["raw_ser"] = float(np.mean(aa != bb))

    delta = (bb - aa) % q
    hist_delta = np.bincount(delta, minlength=q).astype(np.int64, copy=False)
    nn_idx = {0}
    if q > 1:
        nn_idx.update({1, (q - 1) % q})
    if q > 2:
        nn_idx.update({2, (q - 2) % q})
    out["near_neighbor_frac"] = float(sum(int(hist_delta[k]) for k in nn_idx) / float(n))

    ah = np.bincount(aa, minlength=q).astype(np.int64, copy=False)
    bh = np.bincount(bb, minlength=q).astype(np.int64, copy=False)
    out["n_unique_a"] = int(np.count_nonzero(ah))
    out["n_unique_b"] = int(np.count_nonzero(bh))
    out["top_a_frac"] = float(np.max(ah) / float(n)) if ah.size > 0 else None
    out["top_b_frac"] = float(np.max(bh) / float(n)) if bh.size > 0 else None
    return out


def _diag_from_sidecar(sidecar_root: Path, d: int) -> dict[str, Any]:
    out: dict[str, Any] = {
        "sidecar_verdict": "",
        "peak_center_ps": None,
        "peak_sigma_ps": None,
        "peak_to_bg": None,
        "raw_ser": None,
        "near_neighbor_frac": None,
        "n_pairs_actual": None,
        "n_unique_a": None,
        "n_unique_b": None,
        "top_a_frac": None,
        "top_b_frac": None,
    }
    meta_path = sidecar_root / "sidecar_meta.json"
    meta = _json_dict(meta_path) if meta_path.exists() else {}

    map_sanity = meta.get("map_sanity") if isinstance(meta.get("map_sanity"), dict) else {}
    verdict = str(map_sanity.get("verdict") or "").strip().upper()
    if verdict:
        out["sidecar_verdict"] = verdict

    mparams = meta.get("materialize_params") if isinstance(meta.get("materialize_params"), dict) else {}
    used = mparams.get("used_params") if isinstance(mparams.get("used_params"), dict) else {}
    out["peak_center_ps"] = _to_int_or_none(used.get("peak_center_ps"))
    out["peak_sigma_ps"] = _to_float_or_none(used.get("peak_sigma_ps"))
    out["peak_to_bg"] = _to_float_or_none(used.get("peak_to_bg"))

    diag = meta.get("diagnostics") if isinstance(meta.get("diagnostics"), dict) else {}
    for k in ("raw_ser", "near_neighbor_frac", "top_a_frac", "top_b_frac"):
        out[k] = _to_float_or_none(diag.get(k))
    for k in ("n_pairs_actual", "n_unique_a", "n_unique_b"):
        out[k] = _to_int_or_none(diag.get(k))

    seq_stats_path: Path | None = None
    if isinstance(diag, dict):
        seq_stats_path = _resolve_sidecar_path(sidecar_root, diag.get("seq_pair_stats_path"))
    if seq_stats_path is None:
        fallback_stats = sidecar_root / "seq_pair_stats.json"
        if fallback_stats.exists():
            seq_stats_path = fallback_stats
    if seq_stats_path is not None and seq_stats_path.exists():
        sj = _json_dict(seq_stats_path)
        if out["peak_center_ps"] is None:
            out["peak_center_ps"] = _to_int_or_none(sj.get("peak_center_ps"))
        if out["peak_sigma_ps"] is None:
            out["peak_sigma_ps"] = _to_float_or_none(sj.get("peak_sigma_ps"))
        if out["peak_to_bg"] is None:
            out["peak_to_bg"] = _to_float_or_none(sj.get("peak_to_bg"))
        for k in ("raw_ser", "near_neighbor_frac", "top_a_frac", "top_b_frac"):
            if out[k] is None:
                out[k] = _to_float_or_none(sj.get(k))
        for k in ("n_pairs_actual", "n_unique_a", "n_unique_b"):
            if out[k] is None:
                out[k] = _to_int_or_none(sj.get(k))

    if out["n_pairs_actual"] is None:
        out["n_pairs_actual"] = _to_int_or_none(meta.get("n_symbols"))

    need_fallback = any(
        out[k] is None
        for k in ("raw_ser", "near_neighbor_frac", "n_pairs_actual", "n_unique_a", "n_unique_b", "top_a_frac", "top_b_frac")
    )
    if need_fallback:
        a_path = sidecar_root / "a_eff.npy"
        b_path = sidecar_root / "b_eff.npy"
        if a_path.exists() and b_path.exists():
            try:
                a_eff = np.load(a_path, mmap_mode="r")
                b_eff = np.load(b_path, mmap_mode="r")
                fb = _compute_light_pair_stats(a_eff=a_eff, b_eff=b_eff, d=int(d))
                for k in ("raw_ser", "near_neighbor_frac", "n_pairs_actual", "n_unique_a", "n_unique_b", "top_a_frac", "top_b_frac"):
                    if out[k] is None:
                        out[k] = fb.get(k)
            except Exception:
                pass

    return out


def _map_ser_from_sidecar(sidecar_root: Path) -> float | None:
    meta_path = sidecar_root / "sidecar_meta.json"
    meta = _json_dict(meta_path) if meta_path.exists() else {}
    map_sanity = meta.get("map_sanity") if isinstance(meta.get("map_sanity"), dict) else {}
    return _to_float_or_none(map_sanity.get("map_ser"))


def _claim_tags_from_sidecar(sidecar_root: Path | None, *, visibility_assumed: float) -> dict[str, Any]:
    out: dict[str, Any] = {
        "security_claim_level": "engineering_diagnostic",
        "security_assumption_tag": "zhang2014_niu2016_style_conditional_not_unconditional",
        "pairing_model_tag": "unknown",
        "multi_event_handling_tag": "not_recorded",
        "frame_cleaning_tag": "not_recorded",
        "chi_E_source_tag": "visibility_assumed_interface",
        "visibility_assumed": float(visibility_assumed),
        "result_scope_tag": "polar_reconciliation_evaluation",
    }
    if sidecar_root is None:
        return out
    meta_path = sidecar_root / "sidecar_meta.json"
    meta = _json_dict(meta_path) if meta_path.exists() else {}
    mparams = meta.get("materialize_params") if isinstance(meta.get("materialize_params"), dict) else {}
    used = mparams.get("used_params") if isinstance(mparams.get("used_params"), dict) else {}
    pairing_mode = str(used.get("pairing_mode") or "").strip().lower()
    if pairing_mode:
        out["pairing_model_tag"] = pairing_mode

    occ = used.get("occupancy_filter") if isinstance(used.get("occupancy_filter"), dict) else {}
    diag = meta.get("diagnostics") if isinstance(meta.get("diagnostics"), dict) else {}
    occ_path = str(diag.get("occupancy_filter_summary_path") or "").strip()
    occ_enabled = _to_int_or_none(occ.get("filter_enabled"))

    if occ_enabled == 1:
        out["multi_event_handling_tag"] = "candidate_pair_multievent_filtered"
        out["frame_cleaning_tag"] = "corrected_frame_candidate_pair_filtered"
    elif occ_path or bool(occ):
        out["multi_event_handling_tag"] = "candidate_pair_multievent_diagnostic_only"
        out["frame_cleaning_tag"] = "corrected_frame_candidate_pair_diagnostic_only"
    return out


def _pairing_window_tags_from_sidecar(sidecar_root: Path | None, *, bin_width_ps: int) -> dict[str, Any]:
    out: dict[str, Any] = {
        "threshold_ps": None,
        "threshold_ratio_to_bw": None,
        "pairing_window_source_tag": "unknown",
    }
    if sidecar_root is None:
        return out
    meta_path = sidecar_root / "sidecar_meta.json"
    meta = _json_dict(meta_path) if meta_path.exists() else {}
    mparams = meta.get("materialize_params") if isinstance(meta.get("materialize_params"), dict) else {}
    used = mparams.get("used_params") if isinstance(mparams.get("used_params"), dict) else {}

    override_ps = _to_int_or_none(used.get("coinc_window_override_ps"))
    threshold_ps = override_ps
    if threshold_ps is None:
        threshold_ps = _to_int_or_none(used.get("gate_width_ps"))
    if threshold_ps is None:
        threshold_ps = _to_int_or_none(used.get("nearest_threshold_ps"))
    out["threshold_ps"] = threshold_ps

    bw = int(max(1, int(bin_width_ps)))
    if threshold_ps is not None:
        out["threshold_ratio_to_bw"] = float(threshold_ps) / float(bw)

    explicit_source_tag = str(used.get("pairing_window_source_tag") or "").strip()
    if explicit_source_tag:
        out["pairing_window_source_tag"] = explicit_source_tag
    elif override_ps is not None:
        out["pairing_window_source_tag"] = "coinc_window_override"
    elif threshold_ps is not None and threshold_ps == bw:
        out["pairing_window_source_tag"] = "default_equals_bw"
    elif threshold_ps is not None:
        out["pairing_window_source_tag"] = "sidecar_used_param"
    return out


def _processing_rule_tags_from_sidecar(sidecar_root: Path | None) -> dict[str, Any]:
    out: dict[str, Any] = {
        "processing_rule_version": None,
        "pairing_path_tag": None,
        "effective_pairing_window_ps": None,
    }
    if sidecar_root is None:
        return out
    meta_path = sidecar_root / "sidecar_meta.json"
    meta = _json_dict(meta_path) if meta_path.exists() else {}
    mparams = meta.get("materialize_params") if isinstance(meta.get("materialize_params"), dict) else {}
    used = mparams.get("used_params") if isinstance(mparams.get("used_params"), dict) else {}

    processing_rule_version = str(used.get("processing_rule_version") or mparams.get("processing_rule_version") or "").strip()
    if processing_rule_version:
        out["processing_rule_version"] = processing_rule_version

    pairing_path_tag = str(used.get("pairing_path_tag") or "").strip()
    if pairing_path_tag:
        out["pairing_path_tag"] = pairing_path_tag

    out["effective_pairing_window_ps"] = _to_int_or_none(used.get("effective_pairing_window_ps"))
    return out


def _canonical_nuisance_from_sidecar(sidecar_root: Path | None) -> dict[str, Any]:
    out: dict[str, Any] = {
        "n_pairs_in_clean_frames": None,
        "n_pairs_in_ambiguous_frames": None,
        "clean_pair_fraction": None,
        "both_multi_frame_fraction": None,
    }
    if sidecar_root is None:
        return out

    meta_path = sidecar_root / "sidecar_meta.json"
    meta = _json_dict(meta_path) if meta_path.exists() else {}
    diag = meta.get("diagnostics") if isinstance(meta.get("diagnostics"), dict) else {}

    occ_path = _resolve_sidecar_path(sidecar_root, diag.get("occupancy_filter_summary_path")) if isinstance(diag, dict) else None
    if occ_path is None:
        fallback = sidecar_root / "occupancy_filter_summary.csv"
        if fallback.exists():
            occ_path = fallback
    if occ_path is None or (not occ_path.exists()):
        return out

    try:
        with occ_path.open("r", encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
    except Exception:
        return out
    if not rows:
        return out

    row = rows[0]
    if _to_int_or_none(row.get("frame_diag_available")) != 1:
        return out

    n_clean = _to_int_or_none(row.get("n_pairs_in_clean_frames"))
    n_amb = _to_int_or_none(row.get("n_pairs_in_ambiguous_frames"))
    n_frames_total = _to_int_or_none(row.get("n_frames_total"))
    n_frames_both_multi = _to_int_or_none(row.get("n_frames_both_multi"))

    out["n_pairs_in_clean_frames"] = n_clean
    out["n_pairs_in_ambiguous_frames"] = n_amb

    total_pairs = None
    if n_clean is not None and n_amb is not None:
        total_pairs = int(n_clean) + int(n_amb)
    if total_pairs and total_pairs > 0:
        out["clean_pair_fraction"] = float(n_clean) / float(total_pairs) if n_clean is not None else None

    if n_frames_total is not None and n_frames_total > 0 and n_frames_both_multi is not None:
        out["both_multi_frame_fraction"] = float(n_frames_both_multi) / float(n_frames_total)

    return out


def _frame_diag_tags_from_sidecar(sidecar_root: Path | None) -> dict[str, Any]:
    out: dict[str, Any] = {
        "frame_diag_available": None,
    }
    if sidecar_root is None:
        return out

    meta_path = sidecar_root / "sidecar_meta.json"
    meta = _json_dict(meta_path) if meta_path.exists() else {}
    diag = meta.get("diagnostics") if isinstance(meta.get("diagnostics"), dict) else {}

    occ_path = _resolve_sidecar_path(sidecar_root, diag.get("occupancy_filter_summary_path")) if isinstance(diag, dict) else None
    if occ_path is None:
        fallback = sidecar_root / "occupancy_filter_summary.csv"
        if fallback.exists():
            occ_path = fallback
    if occ_path is None or (not occ_path.exists()):
        return out

    try:
        with occ_path.open("r", encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
    except Exception:
        return out
    if not rows:
        return out

    out["frame_diag_available"] = _to_int_or_none(rows[0].get("frame_diag_available"))
    return out


def _csv_cell(v: Any) -> Any:
    if v is None:
        return ""
    if isinstance(v, float) and not math.isfinite(v):
        return ""
    return v


def _h2(p: float) -> float:
    p = float(min(1.0 - 1e-12, max(1e-12, p)))
    return -p * math.log2(p) - (1.0 - p) * math.log2(1.0 - p)


def _dary_mutual_info_proxy(*, dimension: int, ser: float | None) -> float | None:
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
    if d <= 1:
        return 0.0
    return float(
        math.log2(float(d))
        + (1.0 - e) * math.log2(1.0 - e)
        + e * math.log2(e / float(d - 1))
    )


def _security_proxy_terms(*, dimension: int, map_ser: float, best_hard_pie: float, coincidence_rate_hz: float) -> dict[str, Any]:
    iab_est = _dary_mutual_info_proxy(dimension=int(dimension), ser=float(map_ser) if math.isfinite(map_ser) else None)
    beta_or_proxy = None
    leak_ec_bits_or_proxy = None
    if iab_est is not None and math.isfinite(iab_est) and iab_est > 0.0:
        beta_or_proxy = float(best_hard_pie) / float(iab_est)
        leak_ec_bits_or_proxy = max(float(iab_est) - float(best_hard_pie), 0.0)
    return {
        "accepted_rate_proxy": float(coincidence_rate_hz) if math.isfinite(coincidence_rate_hz) else float("nan"),
        "IAB_est": float(iab_est) if iab_est is not None and math.isfinite(iab_est) else float("nan"),
        "IAB_or_proxy": float(iab_est) if iab_est is not None and math.isfinite(iab_est) else float("nan"),
        "beta_or_proxy": float(beta_or_proxy) if beta_or_proxy is not None and math.isfinite(beta_or_proxy) else float("nan"),
        "leak_ec_bits_or_proxy": float(leak_ec_bits_or_proxy) if leak_ec_bits_or_proxy is not None and math.isfinite(leak_ec_bits_or_proxy) else float("nan"),
    }


def calc_crc16(bits: np.ndarray) -> list[int]:
    reg = 0x0000
    poly = 0x1021
    for b in bits:
        top = (reg >> 15) & 1
        reg = ((reg << 1) & 0xFFFF)
        if top ^ (int(b) & 1):
            reg ^= poly
    return [(reg >> (15 - i)) & 1 for i in range(16)]


def _crc16_append(msg_bits: np.ndarray) -> np.ndarray:
    crc_bits = calc_crc16(msg_bits)
    out = np.empty(msg_bits.size + 16, dtype=np.uint8)
    out[: msg_bits.size] = msg_bits.astype(np.uint8)
    for i in range(16):
        out[msg_bits.size + i] = np.uint8(crc_bits[i] & 1)
    return out


@njit(cache=True)
def _simulate_layer_sc_fer_early(
    ber: float,
    n: int,
    k: int,
    info_idx: np.ndarray,
    mask: np.ndarray,
    n_frames: int,
    llr_clip: float,
    n_log: int,
    max_err_allowed: int,
) -> float:
    if k <= 0:
        return 1.0

    p = ber
    if p < 1e-6:
        p = 1e-6
    if p > 1.0 - 1e-6:
        p = 1.0 - 1e-6
    lam = math.log((1.0 - p) / p)
    frame_err = 0

    for _ in range(n_frames):
        u = np.zeros(n, dtype=np.int8)
        for t in range(k):
            u[info_idx[t]] = np.int8(np.random.randint(0, 2))

        x = polar_encode_non_systematic(u, n_log)
        llr = np.empty(n, dtype=np.float64)
        for i in range(n):
            flip = 1 if np.random.random() < p else 0
            y = x[i] ^ np.int8(flip)
            v = lam if y == 0 else -lam
            if v > llr_clip:
                v = llr_clip
            elif v < -llr_clip:
                v = -llr_clip
            llr[i] = v

        u_hat = polar_sc_decode(llr, mask, n_log)
        bad = 0
        for t in range(k):
            idx = info_idx[t]
            if u_hat[idx] != u[idx]:
                bad = 1
                break
        frame_err += bad
        if frame_err > max_err_allowed:
            return float(frame_err) / float(n_frames)

    return float(frame_err) / float(n_frames)


_ORDER: np.ndarray | None = None
_SIDECAR_MAP: dict[tuple[int, int], str] = {}
_RATE_MAP: dict[tuple[int, int], float] = {}
_N = 4096
_N_LOG = 12
_N_FRAMES = 100
_FER_THRESH = 0.05
_SC_MARGIN = 0.05
_SCL_MARGINS: tuple[float, ...] = (0.02, 0.05)
_SCL_BATCH = 20
_BASE_SEED = 20260228
_E_P = 0.025
_SCL_DECODER: PolarSCLDecoder | None = None


def _worker_init(
    sidecar_map: dict[tuple[int, int], str],
    rate_map: dict[tuple[int, int], float],
    n: int,
    n_frames: int,
    fer_thresh: float,
    sc_margin: float,
    scl_margins: tuple[float, ...],
    scl_batch: int,
    base_seed: int,
    e_p: float,
    enable_scl: bool,
    repo_root: str,
) -> None:
    global _ORDER, _SIDECAR_MAP, _RATE_MAP, _N, _N_LOG, _N_FRAMES, _FER_THRESH
    global _SC_MARGIN, _SCL_MARGINS, _SCL_BATCH, _BASE_SEED, _E_P, _SCL_DECODER

    _SIDECAR_MAP = dict(sidecar_map)
    _RATE_MAP = dict(rate_map)
    _N = int(n)
    _N_LOG = int(round(math.log2(_N)))
    _N_FRAMES = int(n_frames)
    _FER_THRESH = float(fer_thresh)
    _SC_MARGIN = float(sc_margin)
    _SCL_MARGINS = tuple(float(x) for x in scl_margins)
    _SCL_BATCH = int(scl_batch)
    _BASE_SEED = int(base_seed)
    _E_P = float(e_p)
    _ORDER = _polar_weight_order(_N)[::-1]

    # JIT warm-up for SC path.
    idx = np.asarray([_ORDER[0]], dtype=np.int64)
    mask = np.zeros(_N, dtype=np.int8)
    mask[idx] = 1
    _ = _simulate_layer_sc_fer_early(0.1, _N, 1, idx, mask, 1, 20.0, _N_LOG, 0)

    _SCL_DECODER = None
    if enable_scl:
        _SCL_DECODER = PolarSCLDecoder(repo_root=Path(repo_root), force_rebuild=False)


def _extract_real_layer_bers(a_eff: np.ndarray, b_eff: np.ndarray, d: int) -> np.ndarray:
    bits = int(round(math.log2(int(d))))
    if 2**bits != int(d):
        raise ValueError(f"dimension={d} is not power-of-two")
    n = int(min(a_eff.size, b_eff.size))
    if n <= 0:
        raise ValueError("empty aligned sequence")
    a = np.asarray(a_eff[:n], dtype=np.int64)
    b = np.asarray(b_eff[:n], dtype=np.int64)
    bers = np.zeros(bits, dtype=np.float64)
    for layer_idx in range(bits):
        shift = bits - 1 - layer_idx
        abit = (a >> shift) & 1
        bbit = (b >> shift) & 1
        bers[layer_idx] = float(np.mean(abit != bbit))
    return bers


def _build_candidates(k_base: int, n: int) -> list[int]:
    cands: list[int] = []
    for s in (1.0, 0.95, 0.90, 0.85, 0.80, 0.70, 0.60, 0.50):
        k = int(math.floor(float(k_base) * float(s)))
        if k > n:
            k = n
        if k > 16:
            cands.append(k)
    return sorted(set(cands), reverse=True)


def _try_layer_sc(ber: float, cap: float, order: np.ndarray) -> dict[str, Any]:
    max_err_allowed = int(math.floor(_FER_THRESH * _N_FRAMES - 1e-12))
    k_base = int(math.floor(float(_N) * max(0.0, float(cap) - float(_SC_MARGIN))))
    if k_base <= 16:
        return {
            "decoder_mode": "sc",
            "gain": 0.0,
            "k": 0,
            "rate": 0.0,
            "crc_bits": 0,
            "frozen_count": int(_N),
            "layer_block_symbols": int(_N),
        }

    for k in _build_candidates(k_base=k_base, n=_N):
        info_idx = np.asarray(order[:k], dtype=np.int64)
        mask = np.zeros(_N, dtype=np.int8)
        mask[info_idx] = 1
        fer = float(
            _simulate_layer_sc_fer_early(
                float(ber),
                _N,
                int(k),
                info_idx,
                mask,
                _N_FRAMES,
                20.0,
                _N_LOG,
                max_err_allowed,
            )
        )
        if fer < _FER_THRESH:
            return {
                "decoder_mode": "sc",
                "gain": float(k) / float(_N),
                "k": int(k),
                "rate": float(k) / float(_N),
                "crc_bits": 0,
                "frozen_count": int(_N - int(k)),
                "layer_block_symbols": int(_N),
            }
    return {
        "decoder_mode": "sc",
        "gain": 0.0,
        "k": 0,
        "rate": 0.0,
        "crc_bits": 0,
        "frozen_count": int(_N),
        "layer_block_symbols": int(_N),
    }


def _simulate_layer_scl_fer_early(
    *,
    ber: float,
    n: int,
    n_log: int,
    k: int,
    info_idx: np.ndarray,
    mask: np.ndarray,
    n_frames: int,
    rng: np.random.Generator,
    llr_clip: float = 20.0,
) -> float:
    if _SCL_DECODER is None:
        return 1.0
    msg_len = int(k) - 16
    if msg_len <= 0:
        return 1.0

    p = float(min(1.0 - 1e-6, max(1e-6, float(ber))))
    lam = float(math.log((1.0 - p) / p))
    max_err_allowed = int(math.floor(_FER_THRESH * float(n_frames) - 1e-12))
    err_count = 0
    seen = 0

    while seen < int(n_frames):
        bsz = min(int(_SCL_BATCH), int(n_frames) - seen)
        infos = np.empty((bsz, int(k)), dtype=np.uint8)
        llrs = np.empty((bsz, int(n)), dtype=np.float32)

        for f in range(bsz):
            msg = rng.integers(0, 2, size=int(msg_len), dtype=np.uint8)
            info = _crc16_append(msg)
            infos[f, :] = info

            u = np.zeros(int(n), dtype=np.int8)
            u[info_idx] = info.astype(np.int8)
            x = polar_encode_non_systematic(u, int(n_log)).astype(np.uint8)
            flips = (rng.random(int(n)) < p).astype(np.uint8)
            y = np.bitwise_xor(x, flips)
            v = np.where(y == 0, lam, -lam)
            v = np.clip(v, -llr_clip, llr_clip)
            llrs[f, :] = v.astype(np.float32)

        out_bits = _SCL_DECODER.decode_batch(int(n), int(k), int(bsz), mask, llrs)
        frame_err = np.any(out_bits != infos, axis=1)
        err_count += int(np.sum(frame_err))
        seen += int(bsz)

        if err_count > max_err_allowed:
            return float(err_count) / float(max(1, seen))

    return float(err_count) / float(max(1, seen))


def _try_layer_scl(ber: float, cap: float, order: np.ndarray, rng: np.random.Generator) -> dict[str, Any]:
    if _SCL_DECODER is None:
        return {
            "decoder_mode": "scl",
            "gain": 0.0,
            "k": 0,
            "rate": 0.0,
            "crc_bits": 16,
            "frozen_count": int(_N),
            "layer_block_symbols": int(_N),
        }

    for margin in _SCL_MARGINS:
        k_base = int(math.floor(float(_N) * max(0.0, float(cap) - float(margin))))
        if k_base <= 16:
            continue
        for k in _build_candidates(k_base=k_base, n=_N):
            info_idx = np.sort(np.asarray(order[:k], dtype=np.int64))
            mask = np.zeros(_N, dtype=np.uint8)
            mask[info_idx] = 1
            fer = _simulate_layer_scl_fer_early(
                ber=float(ber),
                n=_N,
                n_log=_N_LOG,
                k=int(k),
                info_idx=info_idx,
                mask=mask,
                n_frames=_N_FRAMES,
                rng=rng,
            )
            if fer < _FER_THRESH:
                return {
                    "decoder_mode": "scl",
                    "gain": float(k) / float(_N),
                    "k": int(k),
                    "rate": float(k) / float(_N),
                    "crc_bits": 16,
                    "frozen_count": int(_N - int(k)),
                    "layer_block_symbols": int(_N),
                }
    return {
        "decoder_mode": "scl",
        "gain": 0.0,
        "k": 0,
        "rate": 0.0,
        "crc_bits": 16,
        "frozen_count": int(_N),
        "layer_block_symbols": int(_N),
    }


def _worker(task: tuple[int, int, str, float, str, str]) -> dict[str, Any]:
    d, bw, status, map_ser, sidecar_verdict, fail_reason = task
    key = (int(d), int(bw))

    rate = _RATE_MAP.get(key, float("nan"))
    if not math.isfinite(rate):
        rate = float("nan")

    def _zero_row(*, chi_e: float, skip_reason: str) -> dict[str, Any]:
        proxy_terms = _security_proxy_terms(
            dimension=int(d),
            map_ser=float(map_ser),
            best_hard_pie=0.0,
            coincidence_rate_hz=float(rate),
        )
        return {
            "dimension": int(d),
            "bin_width_ps": int(bw),
            "status": str(status),
            "sidecar_verdict": str(sidecar_verdict),
            "fail_reason": str(fail_reason),
            "skip_reason": str(skip_reason),
            "map_ser": float(map_ser),
            "coincidence_rate_hz": float(rate),
            "sc_hard_PIE": 0.0,
            "cpp_scl_hard_PIE": 0.0,
            "best_hard_PIE": 0.0,
            "chi_E": float(chi_e),
            "PIE_practical": 0.0,
            "SKR_measured_bps": 0.0 if math.isfinite(rate) else float("nan"),
            "layers_success_sc": 0,
            "layers_success_scl": 0,
            "layers_success_best": 0,
            "layer_metrics": [],
            **proxy_terms,
        }

    if int(d) <= 1 or (2 ** int(round(math.log2(int(d)))) != int(d)):
        return _zero_row(chi_e=0.0, skip_reason="invalid_dimension")

    sidecar_root_s = _SIDECAR_MAP.get(key)
    if not sidecar_root_s:
        chi_e = _h2(_E_P) + _E_P * math.log2(int(d) - 1)
        return _zero_row(chi_e=chi_e, skip_reason="missing_sidecar")

    try:
        sidecar_root = Path(sidecar_root_s)
        a_path = sidecar_root / "a_eff.npy"
        b_path = sidecar_root / "b_eff.npy"
        if (not a_path.exists()) or (not b_path.exists()):
            chi_e = _h2(_E_P) + _E_P * math.log2(int(d) - 1)
            return _zero_row(chi_e=chi_e, skip_reason="missing_a_eff_or_b_eff")
        a_eff = np.load(a_path, mmap_mode="r")
        b_eff = np.load(b_path, mmap_mode="r")
        if int(a_eff.size) <= 0 or int(b_eff.size) <= 0:
            chi_e = _h2(_E_P) + _E_P * math.log2(int(d) - 1)
            return _zero_row(chi_e=chi_e, skip_reason="empty_a_eff_or_b_eff")
        layer_bers = _extract_real_layer_bers(a_eff=a_eff, b_eff=b_eff, d=int(d))
    except Exception as e:
        chi_e = _h2(_E_P) + _E_P * math.log2(int(d) - 1)
        return _zero_row(chi_e=chi_e, skip_reason=f"sidecar_load_exception:{type(e).__name__}")

    order = _ORDER if _ORDER is not None else _polar_weight_order(_N)[::-1]
    rng = np.random.default_rng(_BASE_SEED + int(d) * 1009 + int(bw) * 1013)

    sc_pie = 0.0
    scl_pie = 0.0
    layers_sc = 0
    layers_scl = 0
    layers_best = 0
    layers_capacity_ge_01 = 0
    layer_metrics: list[dict[str, Any]] = []

    for i, ber in enumerate(layer_bers):
        cap = float(1.0 - _h2(float(ber)))
        gain_sc = 0.0
        gain_scl = 0.0
        if cap < 0.1:
            layer_metrics.append(
                {
                    "layer_idx": int(i),
                    "layer_ber": float(ber),
                    "capacity": float(cap),
                    "rescue_success": 0,
                }
            )
            continue
        layers_capacity_ge_01 += 1

        sc_meta = _try_layer_sc(ber=float(ber), cap=cap, order=order)
        gain_sc = float(sc_meta.get("gain", 0.0))
        if gain_sc > 0.0:
            sc_pie += gain_sc
            layers_sc += 1

        scl_meta = _try_layer_scl(
            ber=float(ber),
            cap=cap,
            order=order,
            rng=np.random.default_rng(int(rng.integers(0, 2**31 - 1)) + i * 7919),
        )
        gain_scl = float(scl_meta.get("gain", 0.0))
        if gain_scl > 0.0:
            scl_pie += gain_scl
            layers_scl += 1

        if max(gain_sc, gain_scl) > 0.0:
            layers_best += 1
        chosen_meta = sc_meta if gain_sc >= gain_scl else scl_meta
        layer_metrics.append(
            {
                "layer_idx": int(i),
                "layer_ber": float(ber),
                "capacity": float(cap),
                "rescue_success": int(1 if max(gain_sc, gain_scl) > 0.0 else 0),
                "decoder_mode_best": str(chosen_meta.get("decoder_mode", "")) if max(gain_sc, gain_scl) > 0.0 else "",
                "k_best": int(chosen_meta.get("k", 0) or 0),
                "rate_best": float(chosen_meta.get("rate", 0.0) or 0.0),
                "crc_bits": int(chosen_meta.get("crc_bits", 0) or 0),
                "frozen_count_best": int(chosen_meta.get("frozen_count", _N) or _N),
                "layer_block_symbols": int(chosen_meta.get("layer_block_symbols", _N) or _N),
            }
        )

    best_hard_pie = max(float(sc_pie), float(scl_pie))
    chi_e = _h2(_E_P) + _E_P * math.log2(int(d) - 1)
    pie_practical = max(0.0, float(best_hard_pie) - float(chi_e))
    skr = float(pie_practical * rate) if math.isfinite(rate) else float("nan")
    proxy_terms = _security_proxy_terms(
        dimension=int(d),
        map_ser=float(map_ser),
        best_hard_pie=float(best_hard_pie),
        coincidence_rate_hz=float(rate),
    )
    skip_reason = ""
    if layers_capacity_ge_01 == 0:
        skip_reason = "strategy_no_layer_capacity_ge_0.1"
    elif layers_best == 0:
        skip_reason = "strategy_all_layers_failed_fer"

    return {
        "dimension": int(d),
        "bin_width_ps": int(bw),
        "status": str(status),
        "sidecar_verdict": str(sidecar_verdict),
        "fail_reason": str(fail_reason),
        "skip_reason": str(skip_reason),
        "map_ser": float(map_ser),
        "coincidence_rate_hz": float(rate),
        "sc_hard_PIE": float(sc_pie),
        "cpp_scl_hard_PIE": float(scl_pie),
        "best_hard_PIE": float(best_hard_pie),
        "chi_E": float(chi_e),
        "PIE_practical": float(pie_practical),
        "SKR_measured_bps": float(skr),
        "layers_success_sc": int(layers_sc),
        "layers_success_scl": int(layers_scl),
        "layers_success_best": int(layers_best),
        "layer_metrics": layer_metrics,
        **proxy_terms,
    }


def _parse_only_points(spec: str | None) -> set[tuple[int, int]]:
    out: set[tuple[int, int]] = set()
    if not spec:
        return out
    for tok in str(spec).split(";"):
        t = tok.strip()
        if not t:
            continue
        parts = [x.strip() for x in t.split(",")]
        if len(parts) != 2:
            continue
        try:
            out.add((int(parts[0]), int(parts[1])))
        except Exception:
            continue
    return out


def _resolve_path(repo_root: Path, p: str | Path) -> Path:
    pp = Path(str(p))
    if pp.is_absolute():
        return pp
    return (repo_root / pp).resolve()


def _recover_rate_from_sidecar(repo_root: Path, sidecar_root: Path) -> float:
    meta_path = sidecar_root / "sidecar_meta.json"
    if not meta_path.exists():
        return float("nan")
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return float("nan")
    source_point_dir = meta.get("source_point_dir")
    if not source_point_dir:
        return float("nan")
    spath = _resolve_path(repo_root, str(source_point_dir))
    if not spath.exists():
        return float("nan")
    for scan_csv in spath.rglob("pie_skr_scan.csv"):
        try:
            sdf = list(csv.DictReader(scan_csv.open("r", encoding="utf-8", newline="")))
        except Exception:
            continue
        if not sdf:
            continue
        v = sdf[0].get("coincidence_rate_hz")
        try:
            fv = float(v) if v is not None and str(v).strip() != "" else float("nan")
        except Exception:
            fv = float("nan")
        if math.isfinite(fv):
            return fv
    return float("nan")


def _extract_acquisition_duration_s_from_metrics(metrics: dict[str, Any]) -> float:
    try:
        events = metrics.get("events_summary") if isinstance(metrics.get("events_summary"), dict) else {}
        v = events.get("acquisition_duration_s")
        if v is not None and str(v).strip() != "":
            fv = float(v)
            if math.isfinite(fv) and fv > 0.0:
                return fv
        span = events.get("timetag_span")
        if span is not None and str(span).strip() != "":
            fs = float(span) * 1e-12
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


def _effective_rate_from_sidecar(repo_root: Path, sidecar_root: Path) -> float:
    a_path = sidecar_root / "a_eff.npy"
    if not a_path.exists():
        return float("nan")
    try:
        n_symbols = int(np.load(a_path, mmap_mode="r").shape[0])
    except Exception:
        return float("nan")
    if n_symbols <= 0:
        return float("nan")

    meta_path = sidecar_root / "sidecar_meta.json"
    acq_s = float("nan")
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            meta = {}
        src_joint = str(meta.get("source_joint_path") or "").strip()
        metrics_path = None
        if src_joint:
            metrics_path_s = src_joint.split("#", 1)[0].strip()
            if metrics_path_s:
                mp = _resolve_path(repo_root, metrics_path_s)
                if mp.exists():
                    metrics_path = mp
        if metrics_path is not None:
            try:
                mj = json.loads(metrics_path.read_text(encoding="utf-8"))
            except Exception:
                mj = {}
            acq_s = _extract_acquisition_duration_s_from_metrics(mj)
    if (not math.isfinite(acq_s)) or acq_s <= 0.0:
        acq_s = 5.0
    return float(n_symbols) / float(acq_s)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Unified real-sequence Polar envelope scan (SC + C++ CA-SCL + in-script practical SKR)"
    )
    ap.add_argument("--jobs", type=int, default=15)
    ap.add_argument("--N", type=int, default=4096)
    ap.add_argument("--frames", type=int, default=100)
    ap.add_argument("--fer-thresh", type=float, default=0.05)
    ap.add_argument("--sc-margin", type=float, default=0.05)
    ap.add_argument("--scl-margins", default="0.02,0.05")
    ap.add_argument("--scl-batch", type=int, default=20)
    ap.add_argument("--seed", type=int, default=20260228)
    ap.add_argument("--visibility", type=float, default=0.95)
    ap.add_argument("--disable-scl", action="store_true")
    ap.add_argument("--in-csv", default="results/mlc_polar_full_grid_20260228.csv")
    ap.add_argument("--grid-table", default="results/grid_mixed_full_table.csv")
    ap.add_argument("--out-csv", default="results/real_polar_max_pie_grid.csv")
    ap.add_argument("--only-points", default="", help='e.g. "32,30;1024,150"')
    ap.add_argument(
        "--prefer-sidecar-map-ser",
        action="store_true",
        help="when sidecar exists, prefer sidecar_meta.json->map_sanity.map_ser over in-csv/grid-table map_ser",
    )
    args = ap.parse_args()

    if int(args.N) not in (1024, 2048, 4096):
        raise SystemExit("--N must be one of 1024/2048/4096")
    n_log = int(round(math.log2(int(args.N))))
    if 2**n_log != int(args.N):
        raise SystemExit("N must be a power of two")

    repo_root = Path(__file__).resolve().parents[1]
    in_csv = (repo_root / args.in_csv).resolve()
    grid_table = (repo_root / args.grid_table).resolve()
    out_csv = (repo_root / args.out_csv).resolve()
    only_points = _parse_only_points(args.only_points)
    e_p = max(0.0, min(0.5, (1.0 - float(args.visibility)) / 2.0))
    scl_margins = tuple(float(x.strip()) for x in str(args.scl_margins).split(",") if x.strip())
    if not scl_margins:
        scl_margins = (0.02, 0.05)

    with grid_table.open("r", encoding="utf-8", newline="") as f:
        grid_rows = list(csv.DictReader(f))
    src_rows: list[dict[str, str]] = []
    if in_csv.exists():
        with in_csv.open("r", encoding="utf-8", newline="") as f:
            src_rows = list(csv.DictReader(f))

    src_meta: dict[tuple[int, int], tuple[str, float, str, str]] = {}
    for r in src_rows:
        try:
            d = _as_int(r.get("dimension", "nan"))
            bw = _as_int(r.get("bin_width_ps", "nan"))
        except Exception:
            continue
        status = str(r.get("status", "")).strip().upper()
        sidecar_verdict = str(r.get("sidecar_verdict", "")).strip().upper()
        fail_reason = str(r.get("fail_reason", "")).strip()
        try:
            map_ser = _as_float(r.get("map_ser", "nan"))
        except Exception:
            map_ser = float("nan")
        src_meta[(int(d), int(bw))] = (status, float(map_ser), sidecar_verdict, fail_reason)

    sidecar_map: dict[tuple[int, int], str] = {}
    rate_map: dict[tuple[int, int], float] = {}
    tasks: list[tuple[int, int, str, float, str, str]] = []
    seen: set[tuple[int, int]] = set()

    for r in grid_rows:
        try:
            d = _as_int(r.get("dimension", "nan"))
            bw = _as_int(r.get("bin_width_ps", "nan"))
        except Exception:
            continue
        key = (int(d), int(bw))
        if key in seen:
            continue
        seen.add(key)
        if only_points and key not in only_points:
            continue

        grid_status = str(r.get("status", "")).strip().upper()
        grid_map_ser = float("nan")
        try:
            grid_map_ser = _as_float(r.get("sidecar_map_ser", "nan"))
        except Exception:
            pass

        src_status, src_map_ser, src_verdict, src_fail_reason = src_meta.get(key, ("", float("nan"), "", ""))
        status = src_status if src_status else grid_status
        map_ser = src_map_ser if math.isfinite(src_map_ser) else grid_map_ser
        sidecar_verdict = src_verdict if src_verdict else status
        fail_reason = src_fail_reason

        out_root_s = str(r.get("out_root", "")).strip()
        if out_root_s:
            out_root = _resolve_path(repo_root, out_root_s)
            sidecar_root = out_root / "sidecars" / f"d{d}_bw{bw}" / "blk0"
            if (sidecar_root / "a_eff.npy").exists() and (sidecar_root / "b_eff.npy").exists():
                sidecar_map[key] = str(sidecar_root)
                if bool(args.prefer_sidecar_map_ser):
                    map_ser_sidecar = _map_ser_from_sidecar(sidecar_root)
                    if map_ser_sidecar is not None:
                        map_ser = float(map_ser_sidecar)

        try:
            rate = _as_float(r.get("coincidence_rate_hz", "nan"))
        except Exception:
            rate = float("nan")
        if key in sidecar_map:
            sidecar_root = Path(sidecar_map[key])
            # Always prefer effective symbol rate from extracted sequence length.
            rate_eff = _effective_rate_from_sidecar(repo_root, sidecar_root)
            if math.isfinite(rate_eff) and rate_eff > 0.0:
                rate = float(rate_eff)
            elif not math.isfinite(rate):
                rate = _recover_rate_from_sidecar(repo_root, sidecar_root)
        rate_map[key] = float(rate) if math.isfinite(rate) else float("nan")

        tasks.append((int(d), int(bw), status, float(map_ser), sidecar_verdict, fail_reason))

    tasks.sort(key=lambda x: (x[0], x[1]))
    total = len(tasks)
    if total == 0:
        raise SystemExit("No tasks found after filters.")

    if not args.disable_scl:
        decoder = PolarSCLDecoder(repo_root=repo_root, force_rebuild=False)
        print(f"[REAL_POLAR_MAX_PIE] loaded C++ SCL lib: {decoder.lib_path}")

    out_rows: list[dict[str, Any]] = []
    done = 0
    with mp.get_context("spawn").Pool(
        processes=max(1, int(args.jobs)),
        initializer=_worker_init,
        initargs=(
            sidecar_map,
            rate_map,
            int(args.N),
            int(args.frames),
            float(args.fer_thresh),
            float(args.sc_margin),
            tuple(float(x) for x in scl_margins),
            int(args.scl_batch),
            int(args.seed),
            float(e_p),
            (not bool(args.disable_scl)),
            str(repo_root),
        ),
    ) as pool:
        for row in pool.imap_unordered(_worker, tasks, chunksize=1):
            out_rows.append(row)
            done += 1
            if done % 5 == 0 or done == total:
                print(f"[REAL_POLAR_MAX_PIE] done={done}/{total}")

    out_rows.sort(key=lambda x: (int(x["dimension"]), int(x["bin_width_ps"])))
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    claim_cols = [
        "security_claim_level",
        "security_assumption_tag",
        "pairing_model_tag",
        "multi_event_handling_tag",
        "frame_cleaning_tag",
        "chi_E_source_tag",
        "visibility_assumed",
        "result_scope_tag",
    ]
    processing_rule_cols = [
        "processing_rule_version",
        "pairing_path_tag",
        "effective_pairing_window_ps",
    ]
    threshold_cols = [
        "threshold_ps",
        "threshold_ratio_to_bw",
        "pairing_window_source_tag",
    ]
    nuisance_cols = [
        "n_pairs_in_clean_frames",
        "n_pairs_in_ambiguous_frames",
        "clean_pair_fraction",
        "both_multi_frame_fraction",
    ]
    claim_by_key: dict[tuple[int, int], dict[str, Any]] = {}
    processing_rule_by_key: dict[tuple[int, int], dict[str, Any]] = {}
    threshold_by_key: dict[tuple[int, int], dict[str, Any]] = {}
    nuisance_by_key: dict[tuple[int, int], dict[str, Any]] = {}
    diag_by_key: dict[tuple[int, int], dict[str, Any]] = {}
    frame_diag_by_key: dict[tuple[int, int], dict[str, Any]] = {}
    for r in out_rows:
        key = (int(r["dimension"]), int(r["bin_width_ps"]))
        sidecar_root_s = sidecar_map.get(key, "")
        sidecar_root = Path(sidecar_root_s) if sidecar_root_s else None
        claim_by_key[key] = _claim_tags_from_sidecar(sidecar_root, visibility_assumed=float(args.visibility))
        processing_rule_by_key[key] = _processing_rule_tags_from_sidecar(sidecar_root)
        threshold_by_key[key] = _pairing_window_tags_from_sidecar(
            sidecar_root,
            bin_width_ps=int(r["bin_width_ps"]),
        )
        nuisance_by_key[key] = _canonical_nuisance_from_sidecar(sidecar_root)
        frame_diag_by_key[key] = _frame_diag_tags_from_sidecar(sidecar_root)
        diag_by_key[key] = _diag_from_sidecar(sidecar_root, d=int(r["dimension"])) if sidecar_root is not None else {}
    cols = [
        "dimension",
        "bin_width_ps",
        "status",
        "sidecar_verdict",
        "fail_reason",
        "skip_reason",
        "raw_ser",
        "map_ser",
        "near_neighbor_frac",
        "n_pairs_actual",
        "frame_diag_available",
        "coincidence_rate_hz",
        "sc_hard_PIE",
        "cpp_scl_hard_PIE",
        "best_hard_PIE",
        "chi_E",
        "PIE_practical",
        "SKR_measured_bps",
        "accepted_rate_proxy",
        "IAB_est",
        "IAB_or_proxy",
        "beta_or_proxy",
        "leak_ec_bits_or_proxy",
        "layers_success_sc",
        "layers_success_scl",
        "layers_success_best",
    ] + claim_cols + processing_rule_cols + threshold_cols + nuisance_cols
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in out_rows:
            key = (int(r["dimension"]), int(r["bin_width_ps"]))
            row = dict(r)
            row.update(
                {
                    "raw_ser": diag_by_key.get(key, {}).get("raw_ser"),
                    "near_neighbor_frac": diag_by_key.get(key, {}).get("near_neighbor_frac"),
                    "n_pairs_actual": diag_by_key.get(key, {}).get("n_pairs_actual"),
                }
            )
            row.update(claim_by_key.get(key, {}))
            row.update(processing_rule_by_key.get(key, {}))
            row.update(threshold_by_key.get(key, {}))
            row.update(nuisance_by_key.get(key, {}))
            row.update(frame_diag_by_key.get(key, {}))
            w.writerow({k: row.get(k) for k in cols})

    diag_csv = out_csv.parent / "polar_diag_summary.csv"
    diag_cols = [
        "dimension",
        "bin_width_ps",
        "status",
        "sidecar_verdict",
        "fail_reason",
        "skip_reason",
        "map_ser",
        "layers_success_best",
        "coincidence_rate_hz",
        "peak_center_ps",
        "peak_sigma_ps",
        "peak_to_bg",
        "raw_ser",
        "near_neighbor_frac",
        "n_pairs_actual",
        "frame_diag_available",
        "accepted_rate_proxy",
        "IAB_est",
        "IAB_or_proxy",
        "beta_or_proxy",
        "leak_ec_bits_or_proxy",
        "n_unique_a",
        "n_unique_b",
        "top_a_frac",
        "top_b_frac",
    ] + claim_cols + processing_rule_cols + threshold_cols + nuisance_cols
    with diag_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=diag_cols)
        w.writeheader()
        for r in out_rows:
            d = int(r.get("dimension", 0))
            bw = int(r.get("bin_width_ps", 0))
            key = (d, bw)
            sidecar_root_s = sidecar_map.get(key, "")
            diag = dict(diag_by_key.get(key, {}))
            sidecar_verdict = str(diag.get("sidecar_verdict") or "").strip().upper()
            if not sidecar_verdict:
                sidecar_verdict = str(r.get("sidecar_verdict", "")).strip().upper()
            row = {
                "dimension": d,
                "bin_width_ps": bw,
                "status": r.get("status", ""),
                "sidecar_verdict": sidecar_verdict,
                "fail_reason": r.get("fail_reason", ""),
                "skip_reason": r.get("skip_reason", ""),
                "map_ser": r.get("map_ser"),
                "layers_success_best": r.get("layers_success_best"),
                "coincidence_rate_hz": r.get("coincidence_rate_hz"),
                "peak_center_ps": diag.get("peak_center_ps"),
                "peak_sigma_ps": diag.get("peak_sigma_ps"),
                "peak_to_bg": diag.get("peak_to_bg"),
                "raw_ser": diag.get("raw_ser"),
                "near_neighbor_frac": diag.get("near_neighbor_frac"),
                "n_pairs_actual": diag.get("n_pairs_actual"),
                "frame_diag_available": frame_diag_by_key.get(key, {}).get("frame_diag_available"),
                "accepted_rate_proxy": r.get("accepted_rate_proxy"),
                "IAB_est": r.get("IAB_est"),
                "IAB_or_proxy": r.get("IAB_or_proxy"),
                "beta_or_proxy": r.get("beta_or_proxy"),
                "leak_ec_bits_or_proxy": r.get("leak_ec_bits_or_proxy"),
                "n_unique_a": diag.get("n_unique_a"),
                "n_unique_b": diag.get("n_unique_b"),
                "top_a_frac": diag.get("top_a_frac"),
                "top_b_frac": diag.get("top_b_frac"),
            }
            row.update(claim_by_key.get(key, {}))
            row.update(processing_rule_by_key.get(key, {}))
            row.update(threshold_by_key.get(key, {}))
            row.update(nuisance_by_key.get(key, {}))
            w.writerow({k: _csv_cell(row.get(k)) for k in diag_cols})

    layer_csv = out_csv.parent / "polar_layer_metrics.csv"
    layer_cols = [
        "dimension",
        "bin_width_ps",
        "layer_idx",
        "layer_ber",
        "capacity",
        "rescue_success",
        "decoder_mode_best",
        "k_best",
        "rate_best",
        "crc_bits",
        "frozen_count_best",
        "layer_block_symbols",
    ]
    with layer_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=layer_cols)
        w.writeheader()
        for r in out_rows:
            d = int(r.get("dimension", 0))
            bw = int(r.get("bin_width_ps", 0))
            metrics = r.get("layer_metrics")
            if not isinstance(metrics, list) or not metrics:
                continue
            for lm in metrics:
                if not isinstance(lm, dict):
                    continue
                row = {
                    "dimension": d,
                    "bin_width_ps": bw,
                    "layer_idx": lm.get("layer_idx"),
                    "layer_ber": lm.get("layer_ber"),
                    "capacity": lm.get("capacity"),
                    "rescue_success": lm.get("rescue_success"),
                    "decoder_mode_best": lm.get("decoder_mode_best"),
                    "k_best": lm.get("k_best"),
                    "rate_best": lm.get("rate_best"),
                    "crc_bits": lm.get("crc_bits"),
                    "frozen_count_best": lm.get("frozen_count_best"),
                    "layer_block_symbols": lm.get("layer_block_symbols"),
                }
                w.writerow({k: _csv_cell(row.get(k)) for k in layer_cols})

    print(f"[REAL_POLAR_MAX_PIE] out_csv={out_csv}")
    print(f"[REAL_POLAR_MAX_PIE] diag_csv={diag_csv}")
    print(f"[REAL_POLAR_MAX_PIE] layer_csv={layer_csv}")
    print(f"[REAL_POLAR_MAX_PIE] rows={len(out_rows)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
