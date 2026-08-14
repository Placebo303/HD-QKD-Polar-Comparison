from __future__ import annotations

import math
import time

import numpy as np

from ..metrics.leakage import compute_beta_eff_empirical, estimate_cascade_leak_bits
from ..metrics.verification import verify_frames_crc32, verify_frames_hash
from ..types import FrameBatch, IRRunConfig, IRRunResult
from ..utils.bitops import bit_error_rate, bits_per_symbol, flatten_bits, frame_symbol_error_rate, symbols_to_bits


def symbols_to_bits_gray(symbols, dimension: int):
    return symbols_to_bits(np.asarray(symbols), dimension, "gray")


def symbols_to_bits_natural(symbols, dimension: int):
    return symbols_to_bits(np.asarray(symbols), dimension, "natural")


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


def _verify(alice_bits: np.ndarray, decoded_bits: np.ndarray, mode: str) -> bool:
    if mode == "hash":
        return bool(verify_frames_hash(alice_bits.reshape(1, -1), decoded_bits.reshape(1, -1))[0])
    return bool(verify_frames_crc32(alice_bits.reshape(1, -1), decoded_bits.reshape(1, -1))[0])


def _default_block_sizes(frame_bits: int, raw_ber: float) -> list[int]:
    if math.isfinite(raw_ber) and raw_ber > 0.0:
        first = int(round(0.73 / raw_ber))
    else:
        first = frame_bits
    first = max(4, min(frame_bits, first))
    candidates = [first, max(4, first // 2), min(frame_bits, max(4, first * 2)), max(4, int(math.sqrt(frame_bits)))]
    out: list[int] = []
    for size in candidates:
        size = max(1, min(frame_bits, int(size)))
        if size not in out:
            out.append(size)
    return out


def _configured_block_sizes(batch: FrameBatch, frame_bits: int, raw_ber: float) -> list[int]:
    raw = batch.metadata.get("block_size_schedule") or batch.metadata.get("cascade_block_sizes") or batch.metadata.get("block_sizes")
    if raw is None:
        return _default_block_sizes(frame_bits, raw_ber)
    if isinstance(raw, str):
        parts = [x.strip() for x in raw.split(",") if x.strip()]
    else:
        parts = list(raw)
    sizes = []
    for value in parts:
        try:
            sizes.append(max(1, min(frame_bits, int(value))))
        except Exception:
            continue
    return sizes or _default_block_sizes(frame_bits, raw_ber)


def _parity(bits: np.ndarray, indices: np.ndarray) -> int:
    if indices.size == 0:
        return 0
    return int(np.bitwise_xor.reduce(bits[indices].astype(np.uint8)))


def _mismatched_block(alice_bits: np.ndarray, bob_bits: np.ndarray, indices: np.ndarray) -> bool:
    return _parity(alice_bits, indices) != _parity(bob_bits, indices)


def _locate_and_flip(alice_bits: np.ndarray, bob_bits: np.ndarray, indices: np.ndarray) -> tuple[bool, int, int]:
    bisection_disclosures = 0
    work = np.asarray(indices, dtype=np.int64)
    if work.size == 0:
        return False, 0, 0
    if not _mismatched_block(alice_bits, bob_bits, work):
        return False, 0, 0
    while work.size > 1:
        mid = max(1, work.size // 2)
        left = work[:mid]
        bisection_disclosures += 1
        if _mismatched_block(alice_bits, bob_bits, left):
            work = left
        else:
            work = work[mid:]
    bob_bits[int(work[0])] ^= 1
    return True, bisection_disclosures, int(work[0])


def _permutation(n: int, mode: str, seed: int, pass_idx: int) -> np.ndarray:
    if mode == "identity":
        return np.arange(n, dtype=np.int64)
    rng = np.random.default_rng(int(seed) + 7919 * pass_idx)
    return rng.permutation(n)


def _run_frame_cascade(
    alice_bits: np.ndarray,
    bob_bits: np.ndarray,
    block_sizes: list[int],
    seed: int,
    max_passes: int,
    permutation_mode: str,
) -> tuple[np.ndarray, dict[str, int]]:
    decoded = np.asarray(bob_bits, dtype=np.uint8).copy()
    n = decoded.size
    stats = {
        "passes_used": 0,
        "total_blocks_checked": 0,
        "parity_disclosures_bits": 0,
        "bisection_disclosures_bits": 0,
        "candidate_flips": 0,
        "verified_flips": 0,
        "iterations_used": 0,
    }
    history: list[tuple[np.ndarray, int]] = []
    for pass_idx, block_size in enumerate(block_sizes[:max(1, max_passes)]):
        perm = _permutation(n, permutation_mode, seed, pass_idx)
        blocks: list[np.ndarray] = []
        for start in range(0, n, int(block_size)):
            block = perm[start:start + int(block_size)]
            if block.size == 0:
                continue
            blocks.append(block)
            stats["total_blocks_checked"] += 1
            stats["parity_disclosures_bits"] += 2
            if not _mismatched_block(alice_bits, decoded, block):
                continue
            flipped, bisection_bits, flip_idx = _locate_and_flip(alice_bits, decoded, block)
            stats["bisection_disclosures_bits"] += int(bisection_bits)
            stats["iterations_used"] += max(1, int(bisection_bits))
            if not flipped:
                continue
            stats["candidate_flips"] += 1
            if alice_bits[flip_idx] == decoded[flip_idx]:
                stats["verified_flips"] += 1
            history.append((block.copy(), flip_idx))
            # Simplified correction propagation: re-check previous blocks touched by the same bit.
            for prev_block, prev_flip_idx in history[:-1]:
                if prev_flip_idx != flip_idx and flip_idx not in prev_block:
                    continue
                stats["total_blocks_checked"] += 1
                stats["parity_disclosures_bits"] += 2
                if _mismatched_block(alice_bits, decoded, prev_block):
                    reflipped, extra_bits, ref_idx = _locate_and_flip(alice_bits, decoded, prev_block)
                    stats["bisection_disclosures_bits"] += int(extra_bits)
                    stats["iterations_used"] += max(1, int(extra_bits))
                    if reflipped:
                        stats["candidate_flips"] += 1
                        if alice_bits[ref_idx] == decoded[ref_idx]:
                            stats["verified_flips"] += 1
        stats["passes_used"] += 1
    return decoded, stats


def _classify_status(attempted: int, success: int, failed_decode: int, raw_ser: float, post_ser: float) -> str:
    if attempted > 0 and math.isfinite(raw_ser) and math.isfinite(post_ser) and post_ser > raw_ser:
        return "experimental_failed"
    if attempted > 0 and success > 0 and (not math.isfinite(post_ser) or not math.isfinite(raw_ser) or post_ser <= raw_ser):
        return "ok"
    if attempted > 0 and failed_decode >= attempted:
        return "decode_failed"
    if attempted > 0 and success == 0:
        return "no_verified_success"
    return "unavailable"


def run_cascade_lite(batch: FrameBatch, cfg: IRRunConfig) -> IRRunResult:
    start = time.perf_counter()
    mapping = str(batch.metadata.get("mapping") or cfg.method_variant or "gray").lower()
    if mapping not in ("gray", "natural"):
        raise ValueError("cascade_lite mapping must be gray or natural")
    bps = bits_per_symbol(batch.dimension)
    n_frames = int(batch.alice_symbols.shape[0])
    frame_bits = int(batch.frame_len_symbols) * bps
    verify_bits = 32 if cfg.verify_mode in ("crc32", "hash") else 0
    max_passes = int(batch.metadata.get("num_passes", batch.metadata.get("cascade_passes", batch.metadata.get("max_passes", 4))))
    seed = int(batch.metadata.get("seed", batch.metadata.get("cascade_seed", 20260415)))
    permutation_mode = str(batch.metadata.get("permutation_mode", "seeded_random")).lower()

    frame_rows: list[dict[str, float | int | bool | str]] = []
    successes = 0
    failed_decode = 0
    failed_verify = 0
    total_parity_disclosures = 0
    total_bisection_disclosures = 0
    total_other_disclosures = 0
    total_candidate_flips = 0
    total_verified_flips = 0
    total_blocks_checked = 0
    total_iterations = 0
    raw_ser_values: list[float] = []
    raw_ber_values: list[float] = []
    post_ser_values: list[float] = []
    post_ber_values: list[float] = []
    block_sizes_used: list[int] = []

    for frame_idx in range(n_frames):
        frame_start = time.perf_counter()
        alice_sym = np.asarray(batch.alice_symbols[frame_idx], dtype=np.int64)
        bob_sym = np.asarray(batch.bob_symbols[frame_idx], dtype=np.int64)
        alice_bits = symbols_to_bits(alice_sym, batch.dimension, mapping).reshape(-1).astype(np.uint8)
        bob_bits = symbols_to_bits(bob_sym, batch.dimension, mapping).reshape(-1).astype(np.uint8)
        raw_frame_ser = frame_symbol_error_rate(alice_sym, bob_sym)
        raw_frame_ber = bit_error_rate(alice_bits, bob_bits)
        block_sizes = _configured_block_sizes(batch, frame_bits, raw_frame_ber)
        if not block_sizes_used:
            block_sizes_used = block_sizes
        decoded_bits, stats = _run_frame_cascade(
            alice_bits,
            bob_bits,
            block_sizes,
            seed + frame_idx * 104729,
            max_passes,
            permutation_mode,
        )
        decoded_sym = _bits_to_symbols(decoded_bits, batch.dimension, mapping)
        post_frame_ser = frame_symbol_error_rate(alice_sym, decoded_sym)
        post_frame_ber = bit_error_rate(alice_bits, decoded_bits)
        verify_success = _verify(alice_bits, decoded_bits, cfg.verify_mode)
        decode_success = bool(post_frame_ber <= raw_frame_ber)
        if verify_success:
            successes += 1
        elif not decode_success:
            failed_decode += 1
        else:
            failed_verify += 1
        total_parity_disclosures += int(stats["parity_disclosures_bits"])
        total_bisection_disclosures += int(stats["bisection_disclosures_bits"])
        total_other_disclosures += 0
        total_candidate_flips += int(stats["candidate_flips"])
        total_verified_flips += int(stats["verified_flips"])
        total_blocks_checked += int(stats["total_blocks_checked"])
        total_iterations += int(stats["iterations_used"])
        raw_ser_values.append(raw_frame_ser)
        raw_ber_values.append(raw_frame_ber)
        post_ser_values.append(post_frame_ser)
        post_ber_values.append(post_frame_ber)
        frame_rows.append({
            "dataset_id": batch.dataset_id,
            "method": "cascade_lite",
            "frame_idx": frame_idx,
            "decode_success": bool(decode_success),
            "verify_success": bool(verify_success),
            "raw_frame_ser": raw_frame_ser,
            "raw_frame_ber": raw_frame_ber,
            "post_frame_ser": post_frame_ser,
            "post_frame_ber": post_frame_ber,
            "leak_bits_frame": float(stats["parity_disclosures_bits"] + stats["bisection_disclosures_bits"] + verify_bits),
            "iterations_used": int(stats["iterations_used"]),
            "runtime_ms": 1000.0 * (time.perf_counter() - frame_start),
            "passes_used": int(stats["passes_used"]),
            "total_blocks_checked": int(stats["total_blocks_checked"]),
            "parity_disclosures_bits": int(stats["parity_disclosures_bits"]),
            "bisection_disclosures_bits": int(stats["bisection_disclosures_bits"]),
            "verification_bits": int(verify_bits),
            "other_disclosures_bits": 0,
            "candidate_flips": int(stats["candidate_flips"]),
            "verified_flips": int(stats["verified_flips"]),
            "block_size_schedule": ",".join(str(x) for x in block_sizes),
            "num_passes": max_passes,
            "notes": "leakage_accounting=exact_internal_transcript",
        })

    runtime = time.perf_counter() - start
    n_input_bits = int(batch.alice_symbols.size) * bps
    leak = estimate_cascade_leak_bits(total_parity_disclosures + total_bisection_disclosures, verify_bits * n_frames, total_other_disclosures)
    raw_ser = float(np.mean(raw_ser_values)) if raw_ser_values else float("nan")
    raw_ber = float(np.mean(raw_ber_values)) if raw_ber_values else float("nan")
    post_ser = float(np.mean(post_ser_values)) if post_ser_values else float("nan")
    post_ber = float(np.mean(post_ber_values)) if post_ber_values else float("nan")
    method_status = _classify_status(n_frames, successes, failed_decode, raw_ser, post_ser)
    notes = (
        "internal_cascade_lite simplified multi-pass parity/bisection baseline; "
        "leakage_accounting=exact_internal_transcript; "
        f"mapping={mapping}; block_size_schedule={block_sizes_used}; num_passes={max_passes}; permutation_mode={permutation_mode}; "
        f"parity_disclosures_bits={total_parity_disclosures}; bisection_disclosures_bits={total_bisection_disclosures}; "
        f"verification_bits={verify_bits * n_frames}; other_disclosures_bits={total_other_disclosures}; "
        f"candidate_flips={total_candidate_flips}; verified_flips={total_verified_flips}; total_blocks_checked={total_blocks_checked}"
    )
    if method_status != "ok":
        notes += f"; status_reason={method_status}; success={successes}/{n_frames}; raw_ser={raw_ser}; post_ir_ser={post_ser}"
    return IRRunResult(
        dataset_id=batch.dataset_id,
        method="cascade_lite",
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
        leak_EC_per_frame=(leak / n_frames) if n_frames else float("nan"),
        leak_EC_per_input_bit=(leak / n_input_bits) if n_input_bits else float("nan"),
        beta_eff_empirical=compute_beta_eff_empirical(leak, n_input_bits, raw_ber),
        runtime_s=runtime,
        throughput_input_bits_per_s=(n_input_bits / runtime) if runtime > 0 else 0.0,
        throughput_output_bits_per_s=((successes * batch.frame_len_symbols * bps) / runtime) if runtime > 0 else 0.0,
        metadata={
            "method_status": method_status,
            "backend_status": "internal_cascade_lite",
            "notes": notes,
            "frame_results": frame_rows,
            "parity_disclosures_bits": total_parity_disclosures,
            "bisection_disclosures_bits": total_bisection_disclosures,
            "verification_bits": verify_bits * n_frames,
            "other_disclosures_bits": total_other_disclosures,
            "passes_used": max_passes,
            "total_blocks_checked": total_blocks_checked,
            "candidate_flips": total_candidate_flips,
            "verified_flips": total_verified_flips,
            "block_size_schedule": block_sizes_used,
            "permutation_mode": permutation_mode,
        },
    )


def unavailable_result(batch: FrameBatch, cfg: IRRunConfig, error: str) -> IRRunResult:
    bps = bits_per_symbol(batch.dimension)
    n_frames = int(batch.alice_symbols.shape[0])
    n_bits = int(batch.alice_symbols.size) * bps
    raw_ser = frame_symbol_error_rate(batch.alice_symbols, batch.bob_symbols)
    raw_ber = bit_error_rate(flatten_bits(batch.alice_symbols, batch.dimension), flatten_bits(batch.bob_symbols, batch.dimension))
    leak = estimate_cascade_leak_bits(0, 0)
    return IRRunResult(
        dataset_id=batch.dataset_id,
        method="cascade_lite",
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
        metadata={
            "method_status": "unavailable",
            "backend_status": "internal_cascade_lite_failed_before_execution",
            "notes": "internal Cascade-lite did not execute any frame",
            "error_message": error,
        },
    )
