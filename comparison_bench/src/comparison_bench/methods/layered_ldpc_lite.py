from __future__ import annotations

import importlib.util
import math
import time

import numpy as np

from ..metrics.leakage import compute_beta_eff_empirical, estimate_ldpc_leak_bits
from ..metrics.verification import verify_frames_crc32, verify_frames_hash
from ..types import FrameBatch, IRRunConfig, IRRunResult
from ..utils.bitops import bit_error_rate, bits_per_symbol, flatten_bits, frame_symbol_error_rate, symbols_to_bits


def split_symbol_bitplanes(symbols, dimension: int, mapping: str = "gray"):
    bits = symbols_to_bits(np.asarray(symbols), dimension, mapping)
    if bits.ndim == 2:
        return [bits[:, i].astype(np.uint8) for i in range(bits.shape[1])]
    return [bits[..., i].astype(np.uint8) for i in range(bits.shape[-1])]


def _gray_decode(values: np.ndarray) -> np.ndarray:
    out = np.asarray(values, dtype=np.int64).copy()
    shift = out >> 1
    while np.any(shift):
        out ^= shift
        shift >>= 1
    return out


def _bits_to_symbols(bits: np.ndarray, dimension: int, mapping: str) -> np.ndarray:
    bps = bits_per_symbol(dimension)
    arr = np.asarray(bits, dtype=np.uint8).reshape(-1, bps)
    powers = np.arange(bps - 1, -1, -1, dtype=np.int64)
    vals = (arr.astype(np.int64) * (1 << powers)).sum(axis=1)
    if mapping == "gray":
        vals = _gray_decode(vals)
    return vals.astype(np.int64)


def _make_parity_check(n_bits: int, m_checks: int, column_weight: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(int(seed))
    m = max(1, int(m_checks))
    n = max(1, int(n_bits))
    w = max(1, min(int(column_weight), m))
    h = np.zeros((m, n), dtype=np.uint8)
    for col in range(n):
        rows = rng.choice(m, size=w, replace=False)
        h[rows, col] = 1
    row_weight = h.sum(axis=1)
    for r in np.where(row_weight == 0)[0]:
        h[r, int(rng.integers(0, n))] = 1
    return h


def _syndrome(h: np.ndarray, bits: np.ndarray) -> np.ndarray:
    return (h @ np.asarray(bits, dtype=np.uint8).reshape(-1) % 2).astype(np.uint8)


def _decode_error_ldpc_backend(
    h: np.ndarray,
    syndrome_delta: np.ndarray,
    max_iter: int,
    error_rate: float,
    osd_order: int = 0,
    bp_method: str = "minimum_sum",
) -> tuple[np.ndarray, bool, int, str]:
    if importlib.util.find_spec("ldpc") is None:
        raise ImportError("ldpc package is not installed")
    from ldpc import BpOsdDecoder  # type: ignore

    p = min(max(float(error_rate), 1e-4), 0.49)
    decoder = BpOsdDecoder(
        h.astype(np.uint8),
        error_rate=p,
        max_iter=max(1, int(max_iter)),
        bp_method=bp_method,
        osd_method="OSD_CS" if int(osd_order) > 0 else "OSD_0",
        osd_order=max(0, int(osd_order)),
    )
    err = np.asarray(decoder.decode(np.asarray(syndrome_delta, dtype=np.uint8)), dtype=np.uint8).reshape(-1) % 2
    ok = bool(np.array_equal(_syndrome(h, err), np.asarray(syndrome_delta, dtype=np.uint8).reshape(-1)))
    return err, ok, int(getattr(decoder, "iter", 0) or 0), "ldpc.BpOsdDecoder"


def _decode_error_bitflip(h: np.ndarray, syndrome_delta: np.ndarray, max_iter: int) -> tuple[np.ndarray, bool, int]:
    n = h.shape[1]
    e = np.zeros(n, dtype=np.uint8)
    residual = np.asarray(syndrome_delta, dtype=np.uint8).reshape(-1).copy()
    col_degree = h.sum(axis=0).astype(np.int64)
    for it in range(int(max_iter) + 1):
        if int(residual.sum()) == 0:
            return e, True, it
        scores = (h.T @ residual).astype(np.int64)
        thresholds = np.maximum(1, (col_degree // 2) + 1)
        flip = scores >= thresholds
        if not np.any(flip):
            best = int(np.argmax(scores))
            if int(scores[best]) <= 0:
                return e, False, it
            flip = np.zeros(n, dtype=bool)
            flip[best] = True
        e[flip] ^= 1
        residual = (syndrome_delta ^ _syndrome(h, e)).astype(np.uint8)
    return e, bool(int(residual.sum()) == 0), int(max_iter)


def _verify(alice_bits: np.ndarray, decoded_bits: np.ndarray, mode: str) -> bool:
    if mode == "hash":
        return bool(verify_frames_hash(alice_bits.reshape(1, -1), decoded_bits.reshape(1, -1))[0])
    return bool(verify_frames_crc32(alice_bits.reshape(1, -1), decoded_bits.reshape(1, -1))[0])


def _classify_status(attempted: int, success: int, failed_decode: int, raw_ser: float, post_ser: float, backend_available: bool) -> str:
    if not backend_available:
        return "unavailable"
    if attempted > 0 and math.isfinite(raw_ser) and math.isfinite(post_ser) and post_ser > raw_ser:
        return "experimental_failed"
    if attempted > 0 and success > 0 and (not math.isfinite(post_ser) or not math.isfinite(raw_ser) or post_ser <= raw_ser):
        return "ok"
    if attempted > 0 and failed_decode >= attempted:
        return "decode_failed"
    if attempted > 0 and success == 0:
        return "no_verified_success"
    return "unavailable"


def _bitplane_fraction(base_fraction: float, ber: float, mode: str) -> float:
    if mode != "per_bitplane_raw_ber":
        return float(base_fraction)
    if ber < 0.02:
        return 0.20
    if ber < 0.05:
        return 0.33
    if ber < 0.10:
        return 0.50
    return 0.67


def run_layered_ldpc_lite(batch: FrameBatch, cfg: IRRunConfig) -> IRRunResult:
    start = time.perf_counter()
    mapping = str(batch.metadata.get("mapping") or cfg.method_variant or "gray").lower()
    if mapping not in ("gray", "natural"):
        raise ValueError("layered_ldpc_lite mapping must be gray or natural")
    parity_fraction = float(batch.metadata.get("parity_fraction", 0.75))
    bitplane_rate_mode = str(batch.metadata.get("bitplane_rate_mode", "uniform")).lower()
    llr_mode = str(batch.metadata.get("llr_mode", "hard")).lower()
    column_weight = int(batch.metadata.get("column_weight", 3))
    seed = int(batch.metadata.get("ldpc_seed", 20260414))
    osd_order = int(batch.metadata.get("osd_order", 0))
    bp_method = str(batch.metadata.get("bp_method", "minimum_sum"))
    unverified_policy = str(batch.metadata.get("unverified_policy", "revert_to_bob_decode_failed")).lower()
    verify_bits = 32 if cfg.verify_mode in ("crc32", "hash") else 0
    bps = bits_per_symbol(batch.dimension)
    n_frames = int(batch.alice_symbols.shape[0])
    plane_len = int(batch.frame_len_symbols)
    backend_available = importlib.util.find_spec("ldpc") is not None
    backend_used = "ldpc.BpOsdDecoder" if backend_available else "internal_bitflip_experimental_fallback"
    backend_errors: list[str] = []

    frame_rows: list[dict[str, float | int | bool | str | list[float] | list[bool]]] = []
    total_iter = 0
    successes = 0
    failed_decode = 0
    failed_verify = 0
    post_ser_values: list[float] = []
    post_ber_values: list[float] = []
    raw_ser_values: list[float] = []
    raw_ber_values: list[float] = []
    leak_total = 0.0

    for frame_idx in range(n_frames):
        frame_start = time.perf_counter()
        alice_sym = np.asarray(batch.alice_symbols[frame_idx], dtype=np.int64)
        bob_sym = np.asarray(batch.bob_symbols[frame_idx], dtype=np.int64)
        alice_bits_by_symbol = symbols_to_bits(alice_sym, batch.dimension, mapping)
        bob_bits_by_symbol = symbols_to_bits(bob_sym, batch.dimension, mapping)
        decoded_bits_by_symbol = bob_bits_by_symbol.copy()
        decode_success = True
        verify_success = False
        iterations_used = 0
        failure_reason = ""
        raw_frame_ber_est = bit_error_rate(alice_bits_by_symbol.reshape(-1), bob_bits_by_symbol.reshape(-1))
        bitplane_raw_ber_list: list[float] = []
        bitplane_success_list: list[bool] = []
        per_plane_syndrome_bits = 0
        h_rows = 0
        h_cols = plane_len
        h_density = 0.0

        for plane_idx in range(bps):
            a_plane = alice_bits_by_symbol[:, plane_idx]
            b_plane = bob_bits_by_symbol[:, plane_idx]
            plane_ber = bit_error_rate(a_plane, b_plane)
            bitplane_raw_ber_list.append(float(plane_ber))
            layer_fraction = _bitplane_fraction(parity_fraction, plane_ber, bitplane_rate_mode)
            m_checks = max(1, min(plane_len, int(math.ceil(layer_fraction * plane_len))))
            per_plane_syndrome_bits += m_checks
            h = _make_parity_check(plane_len, m_checks, column_weight, seed + plane_idx)
            h_rows = m_checks
            h_density = float(np.count_nonzero(h) / h.size) if h.size else 0.0
            syndrome_delta = (_syndrome(h, a_plane) ^ _syndrome(h, b_plane)).astype(np.uint8)
            try:
                if llr_mode == "empirical_bitplane":
                    error_rate = plane_ber
                elif llr_mode == "bsc_estimated":
                    error_rate = raw_frame_ber_est
                else:
                    error_rate = max(plane_ber, raw_frame_ber_est)
                err, ok, iters, local_backend = _decode_error_ldpc_backend(h, syndrome_delta, cfg.max_iter, error_rate, osd_order, bp_method)
                backend_used = local_backend
            except Exception as exc:
                if len(backend_errors) < 5:
                    backend_errors.append(f"{type(exc).__name__}: {exc}")
                err, ok, iters = _decode_error_bitflip(h, syndrome_delta, cfg.max_iter)
                backend_used = "internal_bitflip_experimental_fallback"
                failure_reason = "decoder_exception"
            decoded_bits_by_symbol[:, plane_idx] = b_plane ^ err
            iterations_used += int(iters)
            decode_success = decode_success and bool(ok)
            bitplane_success_list.append(bool(ok))
            if not ok and not failure_reason:
                failure_reason = "syndrome_decode_failed"

        alice_bits_flat = alice_bits_by_symbol.reshape(-1).astype(np.uint8)
        decoded_bits_flat = decoded_bits_by_symbol.reshape(-1).astype(np.uint8)
        verify_success = _verify(alice_bits_flat, decoded_bits_flat, cfg.verify_mode) if decode_success else False
        if decode_success and not verify_success and unverified_policy == "revert_to_bob_decode_failed":
            decoded_bits_by_symbol = bob_bits_by_symbol.copy()
            decoded_bits_flat = decoded_bits_by_symbol.reshape(-1).astype(np.uint8)
            decode_success = False
            failure_reason = "candidate_failed_verification"
        decoded_sym = _bits_to_symbols(decoded_bits_flat, batch.dimension, mapping)
        raw_frame_ser = frame_symbol_error_rate(alice_sym, bob_sym)
        raw_frame_ber = bit_error_rate(alice_bits_flat, bob_bits_by_symbol.reshape(-1))
        post_frame_ser = frame_symbol_error_rate(alice_sym, decoded_sym)
        post_frame_ber = bit_error_rate(alice_bits_flat, decoded_bits_flat)
        if decode_success and verify_success:
            successes += 1
        elif not decode_success:
            failed_decode += 1
        else:
            failed_verify += 1
        if not failure_reason and math.isfinite(post_frame_ser) and math.isfinite(raw_frame_ser) and post_frame_ser > raw_frame_ser:
            failure_reason = "post_ir_worse_than_raw"
        if not failure_reason and decode_success:
            failure_reason = ""
        raw_ser_values.append(raw_frame_ser)
        raw_ber_values.append(raw_frame_ber)
        post_ser_values.append(post_frame_ser)
        post_ber_values.append(post_frame_ber)
        total_iter += iterations_used
        leak_bits_frame = float(estimate_ldpc_leak_bits(per_plane_syndrome_bits, verify_bits))
        leak_total += leak_bits_frame
        frame_rows.append({
            "dataset_id": batch.dataset_id,
            "method": "layered_ldpc_lite",
            "frame_idx": frame_idx,
            "decode_success": bool(decode_success),
            "verify_success": bool(verify_success),
            "raw_frame_ser": raw_frame_ser,
            "raw_frame_ber": raw_frame_ber,
            "post_frame_ser": post_frame_ser,
            "post_frame_ber": post_frame_ber,
            "leak_bits_frame": leak_bits_frame,
            "iterations_used": iterations_used,
            "runtime_ms": 1000.0 * (time.perf_counter() - frame_start),
            "syndrome_bits_frame": int(per_plane_syndrome_bits),
            "verification_bits_frame": int(verify_bits),
            "other_disclosures_bits": 0,
            "parity_fraction": float(parity_fraction),
            "h_rows": int(h_rows),
            "h_cols": int(h_cols),
            "h_density": float(h_density),
            "mapping": mapping,
            "llr_mode": llr_mode,
            "bitplane_rate_mode": bitplane_rate_mode,
            "bitplane_raw_ber_list": [float(x) for x in bitplane_raw_ber_list],
            "bitplane_success_list": [bool(x) for x in bitplane_success_list],
            "estimated_error_rate": float(raw_frame_ber_est),
            "osd_order": int(osd_order),
            "bp_method": bp_method,
            "max_iter": int(cfg.max_iter),
            "fallback_to_raw_bob": bool(not decode_success and failure_reason == "candidate_failed_verification"),
            "failure_reason": failure_reason,
        })

    runtime = time.perf_counter() - start
    n_input_bits = int(batch.alice_symbols.size) * bps
    raw_ber = float(np.mean(raw_ber_values)) if raw_ber_values else float("nan")
    raw_ser = float(np.mean(raw_ser_values)) if raw_ser_values else float("nan")
    post_ser = float(np.mean(post_ser_values)) if post_ser_values else float("nan")
    post_ber = float(np.mean(post_ber_values)) if post_ber_values else float("nan")
    method_status = _classify_status(n_frames, successes, failed_decode, raw_ser, post_ser, backend_available)
    if backend_used == "internal_bitflip_experimental_fallback" and method_status == "ok":
        method_status = "experimental_failed"
    status_note = (
        f"backend={backend_used}; parity_fraction={parity_fraction}; column_weight={column_weight}; seed={seed}; "
        f"osd_order={osd_order}; bp_method={bp_method}; llr_mode={llr_mode}; bitplane_rate_mode={bitplane_rate_mode}; "
        f"unverified_policy={unverified_policy}"
    )
    if backend_errors:
        status_note += "; backend_errors=" + " | ".join(backend_errors)
    if method_status != "ok":
        status_note += f"; status_reason={method_status}; success={successes}/{n_frames}; raw_ser={raw_ser}; post_ir_ser={post_ser}"
    return IRRunResult(
        dataset_id=batch.dataset_id,
        method="layered_ldpc_lite",
        method_variant=cfg.method_variant,
        frame_len_symbols=batch.frame_len_symbols,
        frame_len_bits=batch.frame_len_symbols * bps,
        n_frames_total=n_frames,
        n_frames_attempted=n_frames,
        n_frames_success=successes,
        n_frames_failed_decode=failed_decode,
        n_frames_failed_verify=failed_verify,
        raw_ser=raw_ser,
        raw_ber=raw_ber,
        post_ir_ser=post_ser,
        post_ir_ber=post_ber,
        leak_EC_actual_bits=leak_total,
        leak_EC_per_frame=(leak_total / n_frames) if n_frames else float("nan"),
        leak_EC_per_input_bit=(leak_total / n_input_bits) if n_input_bits else float("nan"),
        beta_eff_empirical=compute_beta_eff_empirical(leak_total, n_input_bits, raw_ber),
        runtime_s=runtime,
        throughput_input_bits_per_s=(n_input_bits / runtime) if runtime > 0 else 0.0,
        throughput_output_bits_per_s=((successes * batch.frame_len_symbols * bps) / runtime) if runtime > 0 else 0.0,
        metadata={
            "method_status": method_status,
            "backend_status": backend_used,
            "notes": status_note,
            "frame_results": frame_rows,
            "total_iterations_used": total_iter,
        },
    )


def unavailable_result(batch: FrameBatch, cfg: IRRunConfig, error: str) -> IRRunResult:
    bps = bits_per_symbol(batch.dimension)
    n_frames = int(batch.alice_symbols.shape[0])
    n_bits = int(batch.alice_symbols.size) * bps
    raw_ser = frame_symbol_error_rate(batch.alice_symbols, batch.bob_symbols)
    raw_ber = bit_error_rate(flatten_bits(batch.alice_symbols, batch.dimension), flatten_bits(batch.bob_symbols, batch.dimension))
    leak = estimate_ldpc_leak_bits(0, 0)
    return IRRunResult(
        dataset_id=batch.dataset_id,
        method="layered_ldpc_lite",
        method_variant=cfg.method_variant,
        frame_len_symbols=batch.frame_len_symbols,
        frame_len_bits=batch.frame_len_symbols * bps,
        n_frames_total=n_frames,
        n_frames_attempted=0,
        n_frames_success=0,
        n_frames_failed_decode=0,
        n_frames_failed_verify=0,
        raw_ser=raw_ser,
        raw_ber=raw_ber,
        post_ir_ser=raw_ser,
        post_ir_ber=raw_ber,
        leak_EC_actual_bits=leak,
        leak_EC_per_frame=0.0,
        leak_EC_per_input_bit=0.0,
        beta_eff_empirical=compute_beta_eff_empirical(leak, n_bits, raw_ber),
        runtime_s=0.0,
        throughput_input_bits_per_s=0.0,
        throughput_output_bits_per_s=0.0,
        metadata={"method_status": "unavailable", "backend_status": "missing", "error_message": error},
    )
