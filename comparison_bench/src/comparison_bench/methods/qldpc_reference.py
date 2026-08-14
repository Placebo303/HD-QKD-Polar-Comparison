from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..metrics.leakage import compute_beta_eff_empirical, estimate_ldpc_leak_bits
from ..metrics.verification import verify_frames_crc32, verify_frames_hash
from ..types import FrameBatch, IRRunConfig, IRRunResult
from ..utils.bitops import bit_error_rate, bits_per_symbol, flatten_bits, frame_symbol_error_rate
from .qary_ldpc import GF2m, gf_add, gf_mul, make_gf, make_qary_ldpc_h, qary_hard_syndrome_bf, qary_symbol_error_syndrome, qary_syndrome


def _result_from_reference_file(path: Path, batch: FrameBatch, cfg: IRRunConfig) -> IRRunResult | None:
    if not path.exists():
        return None
    if path.suffix.lower() == ".json":
        obj = json.loads(path.read_text(encoding="utf-8"))
        row: dict[str, Any] = obj if isinstance(obj, dict) else {}
    else:
        df = pd.read_csv(path)
        if df.empty:
            return None
        row = dict(df.iloc[0])
    bps = bits_per_symbol(batch.dimension)
    n_frames = int(row.get("n_frames_total", batch.alice_symbols.shape[0]))
    leak = float(row.get("leak_EC_actual_bits", math.nan))
    raw_ber = float(row.get("raw_ber", bit_error_rate(flatten_bits(batch.alice_symbols, batch.dimension), flatten_bits(batch.bob_symbols, batch.dimension))))
    runtime = float(row.get("runtime_s", math.nan))
    declared_status = str(row.get("method_status", "reference"))
    method_status = "ok" if declared_status == "ok" else "reference"
    return IRRunResult(
        dataset_id=batch.dataset_id,
        method="qldpc_reference",
        method_variant=cfg.method_variant,
        frame_len_symbols=batch.frame_len_symbols,
        frame_len_bits=batch.frame_len_symbols * bps,
        n_frames_total=n_frames,
        n_frames_attempted=int(row.get("n_frames_attempted", 0)),
        n_frames_success=int(row.get("n_frames_success", 0)),
        n_frames_failed_decode=int(row.get("n_frames_failed_decode", 0)),
        n_frames_failed_verify=int(row.get("n_frames_failed_verify", 0)),
        raw_ser=float(row.get("raw_ser", frame_symbol_error_rate(batch.alice_symbols, batch.bob_symbols))),
        raw_ber=raw_ber,
        post_ir_ser=float(row.get("post_ir_ser", math.nan)),
        post_ir_ber=float(row.get("post_ir_ber", math.nan)),
        leak_EC_actual_bits=leak,
        leak_EC_per_frame=(leak / n_frames) if n_frames and math.isfinite(leak) else math.nan,
        leak_EC_per_input_bit=(leak / (batch.alice_symbols.size * bps)) if math.isfinite(leak) else math.nan,
        beta_eff_empirical=compute_beta_eff_empirical(leak, int(batch.alice_symbols.size) * bps, raw_ber) if math.isfinite(leak) else math.nan,
        runtime_s=runtime,
        throughput_input_bits_per_s=0.0,
        throughput_output_bits_per_s=0.0,
        metadata={"method_status": method_status, "backend_status": "reference_file", "notes": f"read qLDPC reference file: {path}; declared_status={declared_status}"},
    )


def _verify(alice_bits: np.ndarray, decoded_bits: np.ndarray, mode: str) -> bool:
    if mode == "hash":
        return bool(verify_frames_hash(alice_bits.reshape(1, -1), decoded_bits.reshape(1, -1))[0])
    return bool(verify_frames_crc32(alice_bits.reshape(1, -1), decoded_bits.reshape(1, -1))[0])


def _gf_to_numpy(values: Any) -> np.ndarray:
    try:
        return np.asarray(values, dtype=np.int64).reshape(-1)
    except Exception:
        return np.array([int(v) for v in values], dtype=np.int64).reshape(-1)


def _symbol_frame_bits(symbols: np.ndarray, q: int) -> np.ndarray:
    return flatten_bits(np.asarray(symbols, dtype=np.int64), q).astype(np.uint8)


def _unsatisfied_checks(syndrome: np.ndarray) -> int:
    return int(np.count_nonzero(np.asarray(syndrome, dtype=np.int64)))


def _channel_model(batch: FrameBatch) -> str:
    return str(batch.metadata.get("channel_model") or "qary_symmetric")


def _decoder_name(batch: FrameBatch) -> str:
    return str(batch.metadata.get("decoder") or "qary_hard_syndrome_bf")


def _check_fraction(batch: FrameBatch) -> float:
    return float(batch.metadata.get("check_fraction", batch.metadata.get("qldpc_parity_fraction", 0.50)))


def _row_weight(batch: FrameBatch) -> int:
    return int(batch.metadata.get("row_weight", batch.metadata.get("qldpc_row_weight", 4)))


def _seed(batch: FrameBatch) -> int:
    return int(batch.metadata.get("seed", batch.metadata.get("qldpc_seed", 20260428)))


def _backend_status(gf: Any, decoder: str) -> str:
    gf_name = "galois" if not isinstance(gf, GF2m) else f"internal_gf2m_{gf.q}"
    return f"qary_ldpc_reference_{decoder}_{gf_name}"


def _decode_one_frame(
    alice_sym: np.ndarray,
    bob_sym: np.ndarray,
    q: int,
    gf: Any,
    h: np.ndarray,
    max_iter: int,
    verify_mode: str,
    syndrome_symbols: int,
    channel_model: str,
    decoder: str,
) -> tuple[dict[str, Any], np.ndarray]:
    frame_start = time.perf_counter()
    delta = qary_symbol_error_syndrome(h, alice_sym, bob_sym, gf)
    initial_weight = _unsatisfied_checks(delta)
    raw_frame_ser = frame_symbol_error_rate(alice_sym, bob_sym)
    alice_bits = _symbol_frame_bits(alice_sym, q)
    bob_bits = _symbol_frame_bits(bob_sym, q)
    raw_frame_ber = bit_error_rate(alice_bits, bob_bits)

    if decoder != "qary_hard_syndrome_bf":
        notes = f"decoder={decoder} not implemented for q={q}; using hard decoder fallback"
        decoder = "qary_hard_syndrome_bf"
    else:
        notes = ""

    err, decode_success, diag = qary_hard_syndrome_bf(h, delta, q, gf, max_iter=max_iter)
    decoded_sym = _gf_to_numpy(gf_add(gf, _gf_to_numpy(bob_sym), err)) % int(q)
    decoded_bits = _symbol_frame_bits(decoded_sym, q)
    verify_success = _verify(alice_bits, decoded_bits, verify_mode) if decode_success else False
    post_frame_ser = frame_symbol_error_rate(alice_sym, decoded_sym)
    post_frame_ber = bit_error_rate(alice_bits, decoded_bits)

    failure_reason = ""
    if not decode_success:
        failure_reason = "syndrome_decode_failed"
    elif not verify_success:
        failure_reason = "candidate_failed_verification"
    elif math.isfinite(post_frame_ser) and math.isfinite(raw_frame_ser) and post_frame_ser > raw_frame_ser:
        failure_reason = "post_ir_worse_than_raw"

    frame = {
        "decode_success": bool(decode_success),
        "verify_success": bool(verify_success),
        "raw_frame_ser": raw_frame_ser,
        "raw_frame_ber": raw_frame_ber,
        "post_frame_ser": post_frame_ser,
        "post_frame_ber": post_frame_ber,
        "iterations_used": int(diag.get("iterations_used", 0)),
        "runtime_ms": 1000.0 * (time.perf_counter() - frame_start),
        "failure_reason": failure_reason,
        "unsatisfied_checks_initial": int(diag.get("unsatisfied_checks_initial", initial_weight)),
        "unsatisfied_checks_final": int(diag.get("unsatisfied_checks_final", _unsatisfied_checks(qary_syndrome(h, decoded_sym, gf)))),
        "syndrome_weight_initial": int(diag.get("syndrome_weight_initial", initial_weight)),
        "syndrome_weight_final": int(diag.get("syndrome_weight_final", _unsatisfied_checks(qary_syndrome(h, decoded_sym, gf)))),
        "candidate_updates": int(diag.get("candidate_updates", 0)),
        "notes": f"channel_model={channel_model}; syndrome_symbols={syndrome_symbols}" + (f"; {notes}" if notes else ""),
    }
    return frame, decoded_sym


def run_qldpc_reference(batch: FrameBatch, cfg: IRRunConfig) -> IRRunResult:
    ref_file = batch.metadata.get("qldpc_reference_file")
    if ref_file:
        loaded = _result_from_reference_file(Path(str(ref_file)), batch, cfg)
        if loaded is not None:
            return loaded

    mode = str(batch.metadata.get("qldpc_mode") or cfg.method_variant or "reference").lower()
    if mode == "stub":
        bps = bits_per_symbol(batch.dimension)
        raw_ser = frame_symbol_error_rate(batch.alice_symbols, batch.bob_symbols)
        raw_ber = bit_error_rate(flatten_bits(batch.alice_symbols, batch.dimension), flatten_bits(batch.bob_symbols, batch.dimension))
        return IRRunResult(
            dataset_id=batch.dataset_id,
            method="qldpc_reference",
            method_variant=cfg.method_variant,
            frame_len_symbols=batch.frame_len_symbols,
            frame_len_bits=batch.frame_len_symbols * bps,
            n_frames_total=int(batch.alice_symbols.shape[0]),
            n_frames_attempted=0,
            n_frames_success=0,
            n_frames_failed_decode=0,
            n_frames_failed_verify=0,
            raw_ser=raw_ser,
            raw_ber=raw_ber,
            post_ir_ser=raw_ser,
            post_ir_ber=raw_ber,
            leak_EC_actual_bits=math.nan,
            leak_EC_per_frame=math.nan,
            leak_EC_per_input_bit=math.nan,
            beta_eff_empirical=math.nan,
            runtime_s=0.0,
            throughput_input_bits_per_s=0.0,
            throughput_output_bits_per_s=0.0,
            metadata={"method_status": "stub", "backend_status": "stub", "notes": "qLDPC reference stub explicitly requested; decode did not run"},
        )

    start = time.perf_counter()
    q = int(batch.dimension)
    bps = bits_per_symbol(q)
    n_frames = int(batch.alice_symbols.shape[0])
    n_symbols = int(batch.frame_len_symbols)
    channel_model = _channel_model(batch)
    decoder = _decoder_name(batch)
    verify_bits = 32 if cfg.verify_mode in ("crc32", "hash") else 0
    if q > int(batch.metadata.get("max_q_for_realdata", 256)) and batch.metadata.get("data_mode") == "real_data":
        raw_ser = frame_symbol_error_rate(batch.alice_symbols, batch.bob_symbols)
        raw_ber = bit_error_rate(flatten_bits(batch.alice_symbols, batch.dimension), flatten_bits(batch.bob_symbols, batch.dimension))
        return IRRunResult(
            dataset_id=batch.dataset_id,
            method="qldpc_reference",
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
            leak_EC_actual_bits=math.nan,
            leak_EC_per_frame=math.nan,
            leak_EC_per_input_bit=math.nan,
            beta_eff_empirical=math.nan,
            runtime_s=0.0,
            throughput_input_bits_per_s=0.0,
            throughput_output_bits_per_s=0.0,
            metadata={"method_status": "reference", "backend_status": "skipped_q_too_large", "notes": f"q={q} exceeds max_q_for_realdata; reference not executed"},
        )

    gf = make_gf(q)
    check_fraction = _check_fraction(batch)
    row_weight = _row_weight(batch)
    seed = _seed(batch)
    max_iter = max(1, int(batch.metadata.get("max_iter", cfg.max_iter or 20)))
    m_checks = max(1, min(n_symbols, int(math.ceil(check_fraction * n_symbols))))
    h = make_qary_ldpc_h(n_symbols, m_checks, q, row_weight=row_weight, col_weight=batch.metadata.get("col_weight"), seed=seed)
    syndrome_symbols = int(m_checks)
    syndrome_bits_per_frame = int(m_checks * bps)

    frame_rows: list[dict[str, Any]] = []
    successes = 0
    failed_decode = 0
    failed_verify = 0
    raw_ser_values: list[float] = []
    raw_ber_values: list[float] = []
    post_ser_values: list[float] = []
    post_ber_values: list[float] = []
    total_iterations = 0

    for frame_idx in range(n_frames):
        frame, decoded_sym = _decode_one_frame(
            np.asarray(batch.alice_symbols[frame_idx], dtype=np.int64),
            np.asarray(batch.bob_symbols[frame_idx], dtype=np.int64),
            q=q,
            gf=gf,
            h=h,
            max_iter=max_iter,
            verify_mode=cfg.verify_mode,
            syndrome_symbols=syndrome_symbols,
            channel_model=channel_model,
            decoder=decoder,
        )
        if frame["verify_success"]:
            successes += 1
        elif not frame["decode_success"]:
            failed_decode += 1
        else:
            failed_verify += 1
        raw_ser_values.append(float(frame["raw_frame_ser"]))
        raw_ber_values.append(float(frame["raw_frame_ber"]))
        post_ser_values.append(float(frame["post_frame_ser"]))
        post_ber_values.append(float(frame["post_frame_ber"]))
        total_iterations += int(frame["iterations_used"])
        frame_rows.append({
            "dataset_id": batch.dataset_id,
            "method": "qldpc_reference",
            "frame_idx": frame_idx,
            "decode_success": frame["decode_success"],
            "verify_success": frame["verify_success"],
            "raw_frame_ser": frame["raw_frame_ser"],
            "raw_frame_ber": frame["raw_frame_ber"],
            "post_frame_ser": frame["post_frame_ser"],
            "post_frame_ber": frame["post_frame_ber"],
            "leak_bits_frame": float(syndrome_bits_per_frame + verify_bits),
            "iterations_used": frame["iterations_used"],
            "runtime_ms": frame["runtime_ms"],
            "failure_reason": frame["failure_reason"],
            "unsatisfied_checks_initial": frame["unsatisfied_checks_initial"],
            "unsatisfied_checks_final": frame["unsatisfied_checks_final"],
            "syndrome_weight_initial": frame["syndrome_weight_initial"],
            "syndrome_weight_final": frame["syndrome_weight_final"],
            "candidate_updates": frame["candidate_updates"],
            "notes": frame["notes"],
        })

    runtime = time.perf_counter() - start
    n_input_bits = int(batch.alice_symbols.size) * bps
    leak = estimate_ldpc_leak_bits(syndrome_bits_per_frame * n_frames, verify_bits * n_frames)
    raw_ser = float(np.mean(raw_ser_values)) if raw_ser_values else math.nan
    raw_ber = float(np.mean(raw_ber_values)) if raw_ber_values else math.nan
    post_ser = float(np.mean(post_ser_values)) if post_ser_values else math.nan
    post_ber = float(np.mean(post_ber_values)) if post_ber_values else math.nan
    method_status = "reference"
    if successes > 0 and math.isfinite(raw_ser) and math.isfinite(post_ser) and post_ser <= raw_ser:
        method_status = "ok"
    backend_status = _backend_status(gf, decoder)
    notes = (
        "qLDPC GF(q) syndrome reference decoder executed; not a full industrial qLDPC implementation; "
        f"q={q}; decoder={decoder}; channel_model={channel_model}; check_fraction={check_fraction}; "
        f"row_weight={row_weight}; syndrome_symbols={syndrome_symbols}; syndrome_bits={syndrome_bits_per_frame * n_frames}; "
        f"verification_bits={verify_bits * n_frames}; success={successes}/{n_frames}"
    )
    return IRRunResult(
        dataset_id=batch.dataset_id,
        method="qldpc_reference",
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
        leak_EC_actual_bits=leak,
        leak_EC_per_frame=(leak / n_frames) if n_frames else math.nan,
        leak_EC_per_input_bit=(leak / n_input_bits) if n_input_bits else math.nan,
        beta_eff_empirical=compute_beta_eff_empirical(leak, n_input_bits, raw_ber),
        runtime_s=runtime,
        throughput_input_bits_per_s=(n_input_bits / runtime) if runtime > 0 else 0.0,
        throughput_output_bits_per_s=((successes * batch.frame_len_symbols * bps) / runtime) if runtime > 0 else 0.0,
        metadata={
            "method_status": method_status,
            "backend_status": backend_status,
            "notes": notes,
            "frame_results": frame_rows,
            "syndrome_symbols": syndrome_symbols,
            "syndrome_bits": syndrome_bits_per_frame * n_frames,
            "verification_bits": verify_bits * n_frames,
            "total_iterations_used": total_iterations,
            "h_density": float(np.count_nonzero(h) / h.size) if h.size else 0.0,
            "q": q,
            "decoder": decoder,
            "channel_model": channel_model,
            "check_fraction": check_fraction,
            "row_weight": row_weight,
        },
    )
