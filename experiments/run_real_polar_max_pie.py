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


def _h2(p: float) -> float:
    p = float(min(1.0 - 1e-12, max(1e-12, p)))
    return -p * math.log2(p) - (1.0 - p) * math.log2(1.0 - p)


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


def _try_layer_sc(ber: float, cap: float, order: np.ndarray) -> float:
    max_err_allowed = int(math.floor(_FER_THRESH * _N_FRAMES - 1e-12))
    k_base = int(math.floor(float(_N) * max(0.0, float(cap) - float(_SC_MARGIN))))
    if k_base <= 16:
        return 0.0

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
            return float(k) / float(_N)
    return 0.0


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


def _try_layer_scl(ber: float, cap: float, order: np.ndarray, rng: np.random.Generator) -> float:
    if _SCL_DECODER is None:
        return 0.0

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
                return float(k) / float(_N)
    return 0.0


def _worker(task: tuple[int, int, str, float, str, str]) -> dict[str, Any]:
    d, bw, status, map_ser, sidecar_verdict, fail_reason = task
    key = (int(d), int(bw))

    rate = _RATE_MAP.get(key, float("nan"))
    if not math.isfinite(rate):
        rate = float("nan")

    def _zero_row(*, chi_e: float, skip_reason: str) -> dict[str, Any]:
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
        a_eff = np.load(a_path)
        b_eff = np.load(b_path)
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

    for i, ber in enumerate(layer_bers):
        cap = float(1.0 - _h2(float(ber)))
        if cap < 0.1:
            continue
        layers_capacity_ge_01 += 1

        gain_sc = _try_layer_sc(ber=float(ber), cap=cap, order=order)
        if gain_sc > 0.0:
            sc_pie += gain_sc
            layers_sc += 1

        gain_scl = _try_layer_scl(
            ber=float(ber),
            cap=cap,
            order=order,
            rng=np.random.default_rng(int(rng.integers(0, 2**31 - 1)) + i * 7919),
        )
        if gain_scl > 0.0:
            scl_pie += gain_scl
            layers_scl += 1

        if max(gain_sc, gain_scl) > 0.0:
            layers_best += 1

    best_hard_pie = max(float(sc_pie), float(scl_pie))
    chi_e = _h2(_E_P) + _E_P * math.log2(int(d) - 1)
    pie_practical = max(0.0, float(best_hard_pie) - float(chi_e))
    skr = float(pie_practical * rate) if math.isfinite(rate) else float("nan")
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
    cols = [
        "dimension",
        "bin_width_ps",
        "status",
        "sidecar_verdict",
        "fail_reason",
        "skip_reason",
        "map_ser",
        "coincidence_rate_hz",
        "sc_hard_PIE",
        "cpp_scl_hard_PIE",
        "best_hard_PIE",
        "chi_E",
        "PIE_practical",
        "SKR_measured_bps",
        "layers_success_sc",
        "layers_success_scl",
        "layers_success_best",
    ]
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in out_rows:
            w.writerow({k: r.get(k) for k in cols})

    print(f"[REAL_POLAR_MAX_PIE] out_csv={out_csv}")
    print(f"[REAL_POLAR_MAX_PIE] rows={len(out_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
