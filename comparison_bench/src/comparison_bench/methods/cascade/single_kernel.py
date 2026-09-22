"""Single Cascade kernel — formal base + policy-driven adaptation (single file core loop)."""
from __future__ import annotations

import hashlib
import math
import time
from collections import deque
from typing import Any

import numpy as np

from ...metrics.leakage import compute_beta_eff_empirical, estimate_cascade_leak_bits
from ...types import FrameBatch, IRRunConfig, IRRunResult
from ...utils.bitops import bit_error_rate, bits_per_symbol, symbols_to_bits
from ...formal_ir.shared import toeplitz_tag, seed_record, locked_seed_bits, transcript_summary
from .config import CascadeSingleConfig, DEFAULT_CAPS

# ponytail: single-file core loop reuses formal_ir/cascade state machine invariants;
# O(n) per pass, global caps; split into modules only if a second method needs the helpers.


def _is_power_of_two(q: int) -> bool:
    return q >= 2 and (q & (q - 1)) == 0


def _q_branch(q: int) -> str:
    if _is_power_of_two(q):
        m = int(math.log2(q))
        if 1 <= m <= 10:
            return "power_of_two"
        return "unsupported_domain_large_m"
    return "non_power_of_two"


def _bits_per_symbol_generic(q: int) -> int:
    return int(math.ceil(math.log2(int(q))))


def _symbols_to_bits_fast(symbols: np.ndarray, q: int, mapping: str) -> np.ndarray:
    # ponytail: vectorized MSB-first, uses bitops.symbols_to_bits (Gray/natural)
    return symbols_to_bits(symbols.astype(np.int64), q, mapping).reshape(-1).astype(np.uint8)


def _symbols_to_bits_generic(symbols: np.ndarray, q: int) -> np.ndarray:
    # generic base-q: encode symbol as binary with ceil(log2 q) bits, MSB-first, natural
    bps = _bits_per_symbol_generic(q)
    vals = np.asarray(symbols, dtype=np.int64)
    powers = np.arange(bps - 1, -1, -1, dtype=np.int64)
    return ((vals[:, None] >> powers) & 1).astype(np.uint8).reshape(-1)


def _seed_bytes(master_seed: int, pass_id: int, frame_idx: int, dataset_id: str) -> bytes:
    # DESIGN_FROZEN domain-separated: SHA256("cascade_single_kernel|frame=<dataset_id:frame_id>|base=<base_seed>|pass=<p>")[:16] -> PCG64; no q,N
    h = hashlib.sha256(f"cascade_single_kernel|frame={dataset_id}:{frame_idx}|base={master_seed}|pass={pass_id}".encode()).digest()
    return h[:16]


def _perm(n: int, pass_id: int, master_seed: int, frame_idx: int, dataset_id: str) -> np.ndarray:
    if pass_id == 0:
        return np.arange(n, dtype=np.int64)
    seed_b = _seed_bytes(master_seed, pass_id, frame_idx, dataset_id)
    return np.random.Generator(np.random.PCG64(int.from_bytes(seed_b, "big"))).permutation(n).astype(np.int64)


def _parity(bits: np.ndarray, members: np.ndarray) -> int:
    return int(np.bitwise_xor.reduce(bits[members])) if len(members) else 0


def _adaptive_schedule(frame_bits: int, raw_ber: float, coeff: float, caps: dict, num_passes: int, passes_cfg: list[int] | None) -> list[int]:
    # ponytail: O(1) heuristic; if passes_cfg provided use it truncated/padded
    if passes_cfg is not None and len(passes_cfg) >= 1:
        # Use configured passes truncated to num_passes
        return list(passes_cfg[: max(1, num_passes)])
    if math.isfinite(raw_ber) and raw_ber > 0:
        first = int(round(coeff / raw_ber))
    else:
        first = frame_bits
    cmin = int(caps.get("min", 8))
    mf = float(caps.get("max_factor", 0.5))
    max_bs = max(cmin, int(frame_bits * mf))
    first = max(cmin, min(max_bs, first))
    candidates = [first, max(cmin, first // 2), min(max_bs, max(cmin, first * 2)), max(cmin, int(math.sqrt(frame_bits)))]
    out: list[int] = []
    for s in candidates:
        s = max(1, min(frame_bits, int(s)))
        if s not in out:
            out.append(s)
    # truncate to num_passes
    return out[: max(1, num_passes)]


def _verification_seed_bits(n_bits: int, master_seed: int, frame_idx: int, dataset_id: str) -> np.ndarray:
    # deterministic verification seed consistent with formal_ir/shared toeplitz_tag contract: n+63 bits via domain-separated PCG64
    need = n_bits + 63
    seed_b = hashlib.sha256(f"cascade_single_kernel|frame={dataset_id}:{frame_idx}|base={master_seed}|verify".encode()).digest()
    rng = np.random.Generator(np.random.PCG64(int.from_bytes(seed_b[:16], "big")))
    nbytes = (need + 7) // 8
    raw = rng.integers(0, 256, size=nbytes, dtype=np.uint8)
    bits = np.unpackbits(raw, bitorder="big")[:need].astype(np.uint8)
    return bits


def _run_one_frame(
    alice_sym: np.ndarray,
    bob_sym: np.ndarray,
    q: int,
    q_branch: str,
    mapping: str,
    config: CascadeSingleConfig,
    master_seed: int,
    frame_idx: int,
    dataset_id: str,
    limits: dict,
    clock,
    started: float,
) -> dict[str, Any]:
    n_sym = int(alice_sym.size)
    # validate symbol range
    if np.any(alice_sym < 0) or np.any(alice_sym >= q) or np.any(bob_sym < 0) or np.any(bob_sym >= q):
        return {"status": "invalid_input", "q_branch": q_branch, "error": "symbol out of range", "decoded_bits": None}
    # encode
    try:
        if q_branch == "power_of_two":
            alice_bits = _symbols_to_bits_fast(alice_sym, q, mapping)
            bob_bits = _symbols_to_bits_fast(bob_sym, q, mapping)
        else:
            # still encode generically for BER reporting but mark unsupported
            alice_bits = _symbols_to_bits_generic(alice_sym, q)
            bob_bits = _symbols_to_bits_generic(bob_sym, q)
    except Exception as exc:
        return {"status": "invalid_input", "q_branch": q_branch, "error": str(exc), "decoded_bits": None}
    n_bits = int(alice_bits.size)
    if q_branch != "power_of_two":
        return {"status": "unsupported_domain", "q_branch": q_branch, "alice_bits": alice_bits, "bob_bits": bob_bits, "n_bits": n_bits, "raw_ber": float(bit_error_rate(alice_bits, bob_bits))}
    raw_ber = float(bit_error_rate(alice_bits, bob_bits))
    # block schedule
    if config.block_size_policy == "fixed":
        block_sizes = list(config.passes_block_sizes)
    else:
        # adaptive: use adaptive sizer unless fixed schedule explicitly provided
        block_sizes = _adaptive_schedule(n_bits, raw_ber, float(config.block_size_adaptive_coeff), config.block_size_caps, int(config.num_passes), list(config.passes_block_sizes) if config.passes_block_sizes != [16, 32, 64, 128] else None)
        # caps already applied in adaptive schedule; also enforce max_factor/min
        cmin = int(config.block_size_caps["min"])
        mf = float(config.block_size_caps["max_factor"])
        max_bs = max(cmin, int(n_bits * mf))
        block_sizes = [max(cmin, min(max_bs, int(x))) for x in block_sizes]
    # cap num_passes slicing
    block_sizes = block_sizes[: max(1, int(config.num_passes))]
    # cascade state
    decoded = bob_bits.copy()
    events: list[dict[str, Any]] = []
    completed: list[list[np.ndarray]] = []
    cache: dict[tuple[int, int, tuple[int, ...]], int] = {}
    queue: deque[tuple[int, int, int | None]] = deque()
    pending: set[tuple[int, int]] = set()
    pops = 0
    aborted: str | None = None
    next_id = 1
    frame_key = f"{dataset_id}:{frame_idx}"

    def append(kind: str, direction: str, p: int, b: int, payload: dict[str, Any], *, parent: int | None = None, key: int = 0, control: int = 0, force: bool = False) -> int:
        nonlocal next_id, aborted
        if not force and len(events) >= int(limits["max_events"]):
            aborted = "events"
            return -1
        events.append({"event_id": next_id, "frame_key": frame_key, "method": "cascade_single_kernel", "event_type": kind, "direction": direction, "parent_event_id": parent, "pass_id": p, "block_id": b, "key_dependent_bits": key, "public_control_bits": control, "payload": payload})
        next_id += 1
        return next_id - 1

    def timed() -> bool:
        nonlocal aborted
        if clock() - started >= float(limits["per_frame_s"]):
            aborted = "wall_s"
            return True
        return False

    corrected: list[int] = []

    def bisect(p: int, b: int, members: np.ndarray, parent: int | None, source: tuple[int, int], lookup: bool) -> bool:
        nonlocal aborted
        work = members
        while len(work) > 1:
            if timed():
                return False
            left = work[: max(1, len(work) // 2)]
            par = cache.setdefault((p, b, tuple(left.tolist())), _parity(alice_bits, left))
            eid = append("BISECTION_LEFT_PARITY", "alice_to_bob", p, b, {"parity": par, "subblock_range": [0, len(left)], "message_path": "lookback_left" if lookup else "primary_left"}, parent=parent, key=1)
            if eid < 0:
                return False
            work = left if par != _parity(decoded, left) else work[len(left):]
            parent = eid
        if len(corrected) >= int(limits["max_corrections"]):
            aborted = "corrections"
            return False
        bit = int(work[0])
        decoded[bit] ^= 1
        corrected.append(bit)
        if append("CORRECTION", "bob_local", p, b, {"source_event_id": parent, "source_block_id": source[1], "source_path": "lookback_bisection" if lookup else "primary_bisection"}, parent=parent) < 0:
            return False
        for oldp, blocks in enumerate(completed):
            for oldb, cand in enumerate(blocks):
                if (oldp, oldb) != source and bit in cand and (oldp, oldb) not in pending:
                    queue.append((oldp, oldb, parent))
                    pending.add((oldp, oldb))
        return True

    def drain() -> bool:
        nonlocal pops, aborted
        while queue:
            if timed():
                return False
            if pops >= int(limits["max_queue_pops"]):
                aborted = "queue_pops"
                return False
            p, b, parent = queue.popleft()
            pending.remove((p, b))
            pops += 1
            members = completed[p][b]
            eid = append("LOOKBACK_RECHECK", "control", p, b, {"source_event_id": parent, "source_block_id": b, "note": "cached_parity"}, parent=parent)
            if eid < 0:
                return False
            if _parity(alice_bits, members) != _parity(decoded, members) and not bisect(p, b, members, eid, (p, b), True):
                return False
        return True

    for p, size in enumerate(block_sizes):
        if timed():
            break
        if p:
            sb = _seed_bytes(master_seed, p, frame_idx, dataset_id)
            if append("PERMUTATION_SEED", "control", p, -1, {"derived_seed_hex": sb.hex(), "derived_seed_id": hashlib.sha256(sb).hexdigest()}, control=128) < 0:
                aborted = "events"
                break
        perm = _perm(n_bits, p, master_seed, frame_idx, dataset_id)
        blocks = [perm[i: i + int(size)] for i in range(0, len(perm), int(size))]
        for b, members in enumerate(blocks):
            if timed():
                aborted = aborted or "wall_s"
                break
            par = cache.setdefault((p, b, tuple(members.tolist())), _parity(alice_bits, members))
            eid = append("BLOCK_PARITY", "alice_to_bob", p, b, {"parity": par, "block_range": [0, len(members)], "message_path": "primary"}, key=1)
            if eid < 0:
                aborted = "events"
                break
            if par != _parity(decoded, members) and (not bisect(p, b, members, eid, (p, b), False) or not drain()):
                aborted = aborted or "events"
                break
        if aborted:
            break
        completed.append(blocks)

    # outcome
    status = "verified_success"
    failure = ""
    if aborted:
        status = "aborted_resource_limit"
        failure = str(aborted)
    # verification: Toeplitz t=64
    verification_invoked = False
    verification_tag_bits = 0
    epsilon_ec = 0.0
    verified = False
    public_control = sum(int(e["public_control_bits"]) for e in events)
    key_dependent = sum(int(e["key_dependent_bits"]) for e in events)
    if status != "aborted_resource_limit":
        # all-or-nothing final exchange: need 2 events capacity
        if len(events) + 2 > int(limits["max_events"]):
            status = "aborted_resource_limit"
            failure = "events"
            # do not invoke verification
            append("ABORT", "control", -1, -1, {"cap": failure, "reason": "resource_limit"}, control=1, force=True)
        else:
            # Toeplitz verification
            seed_bits = _verification_seed_bits(n_bits, master_seed, frame_idx, dataset_id)
            # seed record
            packed = np.packbits(seed_bits, bitorder="big").tobytes()
            seed_id = hashlib.sha256(packed).hexdigest()
            # store seed_hex for transcript
            append("VERIFICATION_SEED", "control", -1, -1, {"seed_id": seed_id, "seed_bit_length": len(seed_bits)}, control=len(seed_bits))
            tag_alice = toeplitz_tag(alice_bits, seed_bits)
            tag_dec = toeplitz_tag(decoded, seed_bits)
            append("VERIFICATION_TAG", "alice_to_bob", -1, -1, {"tag": tag_alice.hex()}, key=64)
            verification_invoked = True
            verification_tag_bits = 64
            epsilon_ec = 2.0 ** -64
            verified = (tag_alice == tag_dec)
            if not verified:
                status = "verify_failed"
                failure = "toeplitz_mismatch"
            public_control = sum(int(e["public_control_bits"]) for e in events)
            key_dependent = sum(int(e["key_dependent_bits"]) for e in events)
    else:
        append("ABORT", "control", -1, -1, {"cap": failure, "reason": "resource_limit"}, control=1, force=True)
        public_control = sum(int(e["public_control_bits"]) for e in events)
        key_dependent = sum(int(e["key_dependent_bits"]) for e in events)

    # post BER
    post_ber = float(bit_error_rate(alice_bits, decoded)) if n_bits else float("nan")
    # success if verified and decoded == alice
    success = bool(status == "verified_success" and verified and np.array_equal(decoded, alice_bits))
    return {
        "status": status,
        "failure_reason": failure,
        "q_branch": q_branch,
        "n_bits": n_bits,
        "raw_ber": raw_ber,
        "post_ber": post_ber,
        "alice_bits": alice_bits,
        "decoded_bits": decoded,
        "events": events,
        "block_sizes": block_sizes,
        "key_dependent": key_dependent,
        "public_control": public_control,
        "verification_invoked": verification_invoked,
        "verification_tag_bits": verification_tag_bits,
        "epsilon_ec": epsilon_ec,
        "verified": verified,
        "success": success,
        "corrected": corrected,
    }


class CascadeSingleKernel:
    """Thin class wrapper for spec path contract — delegates to run_cascade_single."""
    def __init__(self, config: CascadeSingleConfig | dict):
        if isinstance(config, dict):
            from .config import load_cascade_single_config
            config = load_cascade_single_config(config)
        self.config = config

    def reconcile(self, frame_batch: FrameBatch) -> IRRunResult:
        return run_cascade_single(frame_batch, self.config, master_seed=int(self.config.base_seed))

    # alias for bench adapter
    run = reconcile
    execute = reconcile


def run_cascade_single(frame_batch: FrameBatch, config: CascadeSingleConfig, master_seed: int = 2026072522) -> IRRunResult:
    """Run Cascade single kernel over a FrameBatch (variable N 64..4096; fixed policy validated)."""
    start = time.perf_counter()
    started_mono = time.monotonic()
    clock = time.monotonic
    q = int(frame_batch.dimension)
    n_frames = int(frame_batch.alice_symbols.shape[0])
    n_sym = int(frame_batch.frame_len_symbols)
    # B9: fixed policy frame-length guard — N!=64 is out-of-tested-range / invalid_input for formal schedule
    if config.block_size_policy == "fixed" and n_sym != 64:
        # produce frames with invalid_input status without attempting correction (fail-fast per-frame)
        pass  # handled per-frame below; also mark global note
    # q_branch for manifest (per-run: first frame)
    q_branch_run = _q_branch(q)
    # Validate config already; enforce limits dict naming vs DEFAULT_CAPS
    limits = {
        "per_frame_s": float(config.caps.get("per_frame_s", DEFAULT_CAPS["per_frame_s"])),
        "max_events": int(config.caps.get("max_events", DEFAULT_CAPS["max_events"])),
        "max_corrections": int(config.caps.get("max_corrections", DEFAULT_CAPS["max_corrections"])),
        "max_queue_pops": int(config.caps.get("max_queue_pops", DEFAULT_CAPS["max_queue_pops"])),
    }
    mapping = str(frame_batch.metadata.get("mapping") or "gray").lower()
    if mapping not in ("gray", "natural"):
        mapping = "gray"

    # per-frame loop
    frame_rows: list[dict[str, Any]] = []
    successes = 0
    failed_decode = 0
    failed_verify = 0
    total_key = 0
    total_public = 0
    total_verify_bits = 0
    raw_bers: list[float] = []
    post_bers: list[float] = []
    raw_sers: list[float] = []
    post_sers: list[float] = []
    per_frame_leaks: list[float] = []
    actual_schedule: list[int] | None = None

    # For beta: need n_input_bits and raw_ber mean
    bps_generic = _bits_per_symbol_generic(q) if q_branch_run != "power_of_two" else None
    try:
        bps = bits_per_symbol(q) if q_branch_run == "power_of_two" else int(bps_generic)  # type: ignore[arg-type]
    except Exception:
        bps = int(bps_generic) if bps_generic else 1

    n_input_bits = n_frames * n_sym * bps

    for frame_idx in range(n_frames):
        alice_sym = np.asarray(frame_batch.alice_symbols[frame_idx], dtype=np.int64)
        bob_sym = np.asarray(frame_batch.bob_symbols[frame_idx], dtype=np.int64)
        # symbol error rate per frame
        raw_ser = float(np.mean(alice_sym != bob_sym)) if n_sym else float("nan")
        raw_sers.append(raw_ser)
        # handle q_branch per frame
        qb = _q_branch(q)
        # B9: fixed policy strictly requires frame_len 64 (formal 64 pairs); N!=64 -> invalid_input
        if config.block_size_policy == "fixed" and n_sym != 64:
            raw_ber = float("nan")
            post_ber = float("nan")
            post_ser = raw_ser
            leak = 0.0
            decode_success = False
            verify_success = False
            qb_out = "invalid_input"
            raw_bers.append(raw_ber)
            post_bers.append(post_ber)
            post_sers.append(post_ser)
            per_frame_leaks.append(leak)
            failed_decode += 1
            frame_rows.append({
                "dataset_id": frame_batch.dataset_id,
                "method": "cascade_single_kernel",
                "frame_idx": frame_idx,
                "decode_success": False,
                "verify_success": False,
                "raw_frame_ser": raw_ser,
                "raw_frame_ber": raw_ber,
                "post_frame_ser": post_ser,
                "post_frame_ber": post_ber,
                "leak_bits_frame": float(leak),
                "iterations_used": 0,
                "runtime_ms": 0.0,
                "q_branch": qb_out,
                "block_schedule": "",
                "status": "invalid_input",
            })
            total_key += 0
            continue
        # shape mismatch -> invalid_input
        if alice_sym.size != n_sym or bob_sym.size != n_sym:
            res = {"status": "invalid_input", "q_branch": "invalid_input", "raw_ber": float("nan"), "post_ber": float("nan"), "key_dependent": 0, "public_control": 0, "block_sizes": [], "alice_bits": None, "decoded_bits": None, "success": False, "verified": False, "verification_invoked": False, "verification_tag_bits": 0}
            leak = 0.0
            post_ser = raw_ser
            post_ber = float("nan")
            decode_success = False
            verify_success = False
            qb_out = "invalid_input"
        else:
            out = _run_one_frame(alice_sym, bob_sym, q, qb, mapping, config, int(master_seed), frame_idx, frame_batch.dataset_id, limits, clock, started_mono)
            if out.get("status") in ("invalid_input", "unsupported_domain"):
                # no correction
                raw_ber = float(out.get("raw_ber", float("nan")))
                post_ber = raw_ber
                post_ser = raw_ser
                leak = 0.0
                decode_success = False
                verify_success = False
                qb_out = str(out.get("q_branch", qb))
                raw_bers.append(raw_ber)
                post_bers.append(post_ber)
                post_sers.append(post_ser)
                per_frame_leaks.append(leak)
                # count as failed_decode if attempted but unsupported? Treat as not attempted for IR metrics (denominator excluded)
                # For batch IRRunResult, we count as not attempted? But need to reflect failure.
                # We'll treat unsupported as failed_decode for visibility and set method_status accordingly via metadata.
                if out["status"] == "unsupported_domain":
                    failed_decode += 1  # type: ignore[operator]
                else:
                    failed_decode += 1
                frame_rows.append({
                    "dataset_id": frame_batch.dataset_id,
                    "method": "cascade_single_kernel",
                    "frame_idx": frame_idx,
                    "decode_success": bool(decode_success),
                    "verify_success": bool(verify_success),
                    "raw_frame_ser": raw_ser,
                    "raw_frame_ber": raw_ber,
                    "post_frame_ser": post_ser,
                    "post_frame_ber": post_ber,
                    "leak_bits_frame": float(leak),
                    "iterations_used": 0,
                    "runtime_ms": 0.0,
                    "q_branch": qb_out,
                    "block_schedule": ",".join(str(x) for x in out.get("block_sizes", [])),
                    "status": out["status"],
                })
                total_key += int(out.get("key_dependent", 0))
                continue
            raw_ber = float(out["raw_ber"])
            post_ber = float(out["post_ber"])
            # post SER via bits->symbols if power_of_two else approximate via BER
            if qb == "power_of_two":
                try:
                    # decode symbols to compute post SER
                    # need to map decoded bits back to symbols for SER (not strictly needed for IRRunResult)
                    # approximate via bit comparison
                    decoded_sym = None
                    # reuse bits->symbols via gray decode? For simplicity use raw vs decoded bits equality for SER proxy
                    post_ser = 0.0 if out["success"] else raw_ser  # conservative
                except Exception:
                    post_ser = raw_ser
            else:
                post_ser = raw_ser
            leak = float(out["key_dependent"])
            decode_success = bool(out["success"])
            verify_success = bool(out["verified"] and out["verification_invoked"])
            qb_out = str(out["q_branch"])
            if actual_schedule is None:
                actual_schedule = list(out["block_sizes"])
            raw_bers.append(raw_ber)
            post_bers.append(post_ber)
            post_sers.append(post_ser)
            per_frame_leaks.append(leak)
            total_key += int(out["key_dependent"])
            total_public += int(out["public_control"])
            total_verify_bits += int(out["verification_tag_bits"])
            if decode_success and verify_success:
                successes += 1
            elif out["status"] == "verify_failed":
                failed_verify += 1
            elif out["status"] == "aborted_resource_limit":
                failed_decode += 1
            else:
                failed_decode += 1
            # per-frame row
            frame_rows.append({
                "dataset_id": frame_batch.dataset_id,
                "method": "cascade_single_kernel",
                "frame_idx": frame_idx,
                "decode_success": bool(decode_success),
                "verify_success": bool(verify_success),
                "raw_frame_ser": raw_ser,
                "raw_frame_ber": raw_ber,
                "post_frame_ser": post_ser,
                "post_frame_ber": post_ber,
                "leak_bits_frame": float(leak),
                "iterations_used": int(len(out.get("corrected", []))),
                "runtime_ms": 0.0,
                "q_branch": qb_out,
                "block_schedule": ",".join(str(x) for x in out.get("block_sizes", [])),
                "status": out["status"],
            })
        # common for invalid path already handled
        if 'out' not in locals() or out.get("status") in ("invalid_input",):
            # invalid_input path already appended? handle
            if len(frame_rows) <= frame_idx:
                raw_ber = float("nan")
                post_ber = float("nan")
                post_ser = raw_ser
                leak = 0.0
                raw_bers.append(raw_ber)
                post_bers.append(post_ber)
                post_sers.append(post_ser)
                per_frame_leaks.append(leak)
                frame_rows.append({
                    "dataset_id": frame_batch.dataset_id,
                    "method": "cascade_single_kernel",
                    "frame_idx": frame_idx,
                    "decode_success": False,
                    "verify_success": False,
                    "raw_frame_ser": raw_ser,
                    "raw_frame_ber": raw_ber,
                    "post_frame_ser": post_ser,
                    "post_frame_ber": post_ber,
                    "leak_bits_frame": float(leak),
                    "iterations_used": 0,
                    "runtime_ms": 0.0,
                    "q_branch": "invalid_input",
                    "block_schedule": "",
                    "status": "invalid_input",
                })

    runtime = time.perf_counter() - start
    raw_ber_mean = float(np.nanmean(raw_bers)) if raw_bers else float("nan")
    post_ber_mean = float(np.nanmean(post_bers)) if post_bers else float("nan")
    raw_ser_mean = float(np.nanmean(raw_sers)) if raw_sers else float("nan")
    post_ser_mean = float(np.nanmean(post_sers)) if post_sers else float("nan")
    leak_total = float(total_key)  # key-dependent disclosure total
    # include verification bits already in total_key
    beta = compute_beta_eff_empirical(leak_total, int(n_input_bits), raw_ber_mean)

    # status classification like cascade_lite but isolate undetected: verification failure is not success
    # successes already excludes undetected via verified check
    if q_branch_run != "power_of_two":
        method_status = "unsupported_domain"
    elif any(r.get("status") == "invalid_input" for r in frame_rows):
        method_status = "invalid_input"
    elif successes == n_frames and n_frames > 0:
        method_status = "ok"
    elif successes > 0:
        method_status = "ok" if post_ser_mean <= raw_ser_mean else "experimental_failed"
    elif failed_verify > 0:
        method_status = "no_verified_success"
    elif n_frames == 0:
        method_status = "unavailable"
    else:
        method_status = "decode_failed"

    # actual_block_schedule for manifest
    if actual_schedule is None:
        if config.block_size_policy == "fixed":
            actual_schedule = list(config.passes_block_sizes)
        else:
            actual_schedule = list(config.passes_block_sizes[: int(config.num_passes)])

    notes = (
        f"cascade_single_kernel kernel=single block_size_policy={config.block_size_policy} "
        f"lookback=fifo verification=toeplitz seed_policy=domain-separated q_handling=auto "
        f"q_branch={q_branch_run} actual_block_schedule={actual_schedule} "
        f"key_dependent={total_key} public_control={total_public} verify_bits={total_verify_bits}"
    )

    return IRRunResult(
        dataset_id=frame_batch.dataset_id,
        method="cascade_single_kernel",
        method_variant=f"q_branch={q_branch_run}",
        frame_len_symbols=int(frame_batch.frame_len_symbols),
        frame_len_bits=int(frame_batch.frame_len_symbols * bps),
        n_frames_total=n_frames,
        n_frames_attempted=n_frames if q_branch_run == "power_of_two" else 0,
        n_frames_success=successes,
        n_frames_failed_decode=failed_decode,
        n_frames_failed_verify=failed_verify,
        raw_ser=raw_ser_mean,
        raw_ber=raw_ber_mean,
        post_ir_ser=post_ser_mean,
        post_ir_ber=post_ber_mean,
        leak_EC_actual_bits=leak_total,
        leak_EC_per_frame=(leak_total / n_frames) if n_frames else float("nan"),
        leak_EC_per_input_bit=(leak_total / n_input_bits) if n_input_bits else float("nan"),
        beta_eff_empirical=beta,
        runtime_s=runtime,
        throughput_input_bits_per_s=(n_input_bits / runtime) if runtime > 0 else 0.0,
        throughput_output_bits_per_s=((successes * n_sym * bps) / runtime) if runtime > 0 else 0.0,
        metadata={
            "method_status": method_status,
            "backend_status": "cascade_single_kernel",
            "notes": notes,
            "frame_results": frame_rows,
            "kernel": "single",
            "block_size_policy": config.block_size_policy,
            "actual_block_schedule": actual_schedule,
            "q_branch": q_branch_run,
            "dropped_semantics": [] if config.block_size_policy == "fixed" else [f"adaptive_schedule:{actual_schedule}"],
            "caps": dict(limits),
            "base_seed": int(config.base_seed),
            "passes": list(config.passes_block_sizes),
        },
    )
