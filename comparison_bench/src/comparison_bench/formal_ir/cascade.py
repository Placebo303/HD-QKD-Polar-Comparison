"""Reference-only, transcript-safe Cascade formal v1 state machine."""
from __future__ import annotations

import hashlib
import time
from collections import deque
from typing import Any, Callable

import numpy as np

from ..utils.bitops import bits_per_symbol, flatten_bits, frame_symbol_error_rate
from .shared import locked_seed_bits, toeplitz_tag, transcript_summary, validate_outcome, verification_result

METHOD = "cascade_formal_v1"; BLOCK_SIZES = (16, 32, 64, 128)
DEFAULT_CAPS = {"wall_s": 5.0, "events": 100000, "corrections": 4096, "queue_pops": 10000}


def _parity(bits: np.ndarray, members: np.ndarray) -> int: return int(np.bitwise_xor.reduce(bits[members])) if len(members) else 0

def _seed(frame_key: str, base_seed: int, pass_id: int) -> bytes:
    return hashlib.sha256(f"{METHOD}|frame={frame_key}|base={base_seed}|pass={pass_id}".encode()).digest()[:16]

def _perm(n: int, frame_key: str, base_seed: int, pass_id: int) -> np.ndarray:
    if pass_id == 0: return np.arange(n, dtype=np.int64)
    return np.random.Generator(np.random.PCG64(int.from_bytes(_seed(frame_key, base_seed, pass_id), "big"))).permutation(n).astype(np.int64)

def _input_bits(symbols: Any, q: int, mapping: Any) -> np.ndarray:
    if not isinstance(mapping, str) or mapping.lower() not in {"gray", "natural"}: raise ValueError("mapping must be gray or natural")
    x = np.asarray(symbols)
    if x.shape != (64,) or not np.issubdtype(x.dtype, np.integer) or np.any(x < 0) or np.any(x >= q): raise ValueError("formal Cascade requires 64 in-range integer symbols")
    return flatten_bits(x.astype(np.int64), q, mapping.lower())

def run_cascade_formal(alice_symbols: Any, bob_symbols: Any, *, dimension: int, dataset_id: str = "synthetic", frame_id: str = "0", mapping: str = "gray", base_seed: int = 2026072521, locked_seed: dict[str, Any] | None = None, caps: dict[str, float | int] | None = None, clock: Callable[[], float] = time.monotonic, include_private_diagnostics: bool = False) -> dict[str, Any]:
    """Run one locked frame. Private correction positions are opt-in test diagnostics only."""
    started = clock(); frame_key = f"{dataset_id}:{frame_id}"; events: list[dict[str, Any]] = []; limits = {**DEFAULT_CAPS, **(caps or {})}; next_id = 1; aborted: str | None = None
    raw_ser = float("nan"); alice = np.zeros(1, dtype=np.uint8)

    def append(kind: str, direction: str, p: int, b: int, payload: dict[str, Any], *, parent: int | None = None, key: int = 0, control: int = 0, force: bool = False) -> int:
        nonlocal next_id, aborted
        if not force and len(events) >= int(limits["events"]): aborted = "events"; return -1
        events.append({"event_id": next_id, "frame_key": frame_key, "method": METHOD, "event_type": kind, "direction": direction, "parent_event_id": parent, "pass_id": p, "block_id": b, "key_dependent_bits": key, "public_control_bits": control, "payload": payload}); next_id += 1; return next_id - 1

    def result(status: str, failure: str, decoded: np.ndarray, corrected: list[int], invoke: bool = False) -> dict[str, Any]:
        nonlocal aborted
        verification = {"verification_invoked": False, "verification_tag_bits": 0, "public_control_bits": 0, "epsilon_ec": 0.0, "verified": False}
        if invoke:
            # Seed/tag are an all-or-nothing final public exchange.
            if len(events) + 2 > int(limits["events"]): status, failure, aborted = "aborted_resource_limit", "events", "events"
            else:
                verification = verification_result(alice, decoded, locked_seed, invoked=True)
                seed_bits = locked_seed_bits(locked_seed, len(alice) + 63)
                append("VERIFICATION_SEED", "control", -1, -1, {"seed_id": locked_seed["seed_id"], "seed_bit_length": len(seed_bits)}, control=len(seed_bits))
                append("VERIFICATION_TAG", "alice_to_bob", -1, -1, {"tag": toeplitz_tag(alice, seed_bits).hex()}, key=64)
                if not verification["verified"]: status, failure = "verify_failed", "toeplitz_mismatch"
        if status == "aborted_resource_limit": append("ABORT", "control", -1, -1, {"cap": failure, "reason": "resource_limit"}, control=1, force=True)
        summary = transcript_summary(events)
        parity = sum(e["key_dependent_bits"] for e in events if e["event_type"] == "BLOCK_PARITY")
        primary = sum(e["key_dependent_bits"] for e in events if e["event_type"] == "BISECTION_LEFT_PARITY" and e["payload"]["message_path"] == "primary_left")
        lookback = sum(e["key_dependent_bits"] for e in events if e["event_type"] == "BISECTION_LEFT_PARITY" and e["payload"]["message_path"] == "lookback_left")
        outcome = {"dataset_id": dataset_id, "frame_id": str(frame_id), "n_pairs": 64, "pair_idx_sequence_sha256": hashlib.sha256(b",".join(str(i).encode() for i in range(64))).hexdigest(), "method": METHOD, "attempted": status not in {"invalid_input", "unsupported_domain"}, "denominator_included": status not in {"invalid_input", "unsupported_domain"}, "status": status, "failure_reason": failure, "dimension": dimension, "frame_len_symbols": 64, "raw_ser": raw_ser, "verification_invoked": verification["verification_invoked"], "verification_seed_id": locked_seed["seed_id"] if verification["verification_invoked"] else "", "verification_tag_bits": verification["verification_tag_bits"], "epsilon_ec": verification["epsilon_ec"], "key_dependent_disclosure_bits_total": summary["key_dependent_disclosure_bits_total"], "public_control_bits_total": summary["public_control_bits_total"], "transcript_first_event_id": events[0]["event_id"] if events else None, "transcript_last_event_id": events[-1]["event_id"] if events else None, "transcript_sha256": summary["transcript_sha256"], "runtime_s": max(0., clock()-started), "cascade_parity_bits": parity, "cascade_primary_bisection_bits": primary, "cascade_lookback_bits": lookback, "verification_tag_bits_component": verification["verification_tag_bits"]}
        validate_outcome(outcome)
        out = {"outcome": outcome, "events": events, "decoded_bits": decoded.copy()}
        if include_private_diagnostics: out["private_diagnostics"] = {"corrected_positions": corrected}
        return out

    try:
        if not isinstance(dimension, int) or dimension < 2 or dimension > 1024 or dimension & (dimension-1):
            # A well-shaped frame in an unsupported q is domain, malformed input is invalid.
            if np.asarray(alice_symbols).shape == (64,) and np.asarray(bob_symbols).shape == (64,): return result("unsupported_domain", "q must be 2^m, m=1..10", alice, [])
            raise ValueError("q must be 2^m, m=1..10")
        alice = _input_bits(alice_symbols, dimension, mapping); decoded = _input_bits(bob_symbols, dimension, mapping)
        if locked_seed is None: raise ValueError("locked verification seed is required")
        locked_seed_bits(locked_seed, len(alice)+63)
    except (TypeError, ValueError) as exc: return result("invalid_input", str(exc), alice, [])
    raw_ser = frame_symbol_error_rate(np.asarray(alice_symbols), np.asarray(bob_symbols)); completed: list[list[np.ndarray]] = []; corrected: list[int] = []; cache: dict[tuple[int,int,tuple[int,...]], int] = {}; queue: deque[tuple[int,int,int|None]] = deque(); pending: set[tuple[int,int]] = set(); pops = 0
    def timed() -> bool:
        nonlocal aborted
        if clock()-started >= float(limits["wall_s"]): aborted="wall_s"; return True
        return False
    def bisect(p: int, b: int, members: np.ndarray, parent: int | None, source: tuple[int,int], lookup: bool) -> bool:
        nonlocal aborted
        work = members
        while len(work)>1:
            if timed(): return False
            left=work[:max(1,len(work)//2)]; parity=cache.setdefault((p,b,tuple(left.tolist())), _parity(alice,left)); eid=append("BISECTION_LEFT_PARITY","alice_to_bob",p,b,{"parity":parity,"subblock_range":[0,len(left)],"message_path":"lookback_left" if lookup else "primary_left"},parent=parent,key=1)
            if eid<0:return False
            work=left if parity!=_parity(decoded,left) else work[len(left):];parent=eid
        if len(corrected)>=int(limits["corrections"]):aborted="corrections";return False
        bit=int(work[0]);decoded[bit]^=1;corrected.append(bit)
        if append("CORRECTION","bob_local",p,b,{"source_event_id":parent,"source_block_id":source[1],"source_path":"lookback_bisection" if lookup else "primary_bisection"},parent=parent)<0:return False
        for oldp, blocks in enumerate(completed):
            for oldb, candidate in enumerate(blocks):
                if (oldp,oldb)!=source and bit in candidate and (oldp,oldb) not in pending: queue.append((oldp,oldb,parent));pending.add((oldp,oldb))
        return True
    def drain() -> bool:
        nonlocal pops,aborted
        while queue:
            if timed():return False
            if pops>=int(limits["queue_pops"]):aborted="queue_pops";return False
            p,b,parent=queue.popleft();pending.remove((p,b));pops+=1;members=completed[p][b];eid=append("LOOKBACK_RECHECK","control",p,b,{"source_event_id":parent,"source_block_id":b,"note":"cached_parity"},parent=parent)
            if eid<0:return False
            if _parity(alice,members)!=_parity(decoded,members) and not bisect(p,b,members,eid,(p,b),True):return False
        return True
    for p,size in enumerate(BLOCK_SIZES):
        if timed():return result("aborted_resource_limit",aborted or "wall_s",decoded,corrected)
        if p:
            value=_seed(frame_key,base_seed,p)
            if append("PERMUTATION_SEED","control",p,-1,{"derived_seed_hex":value.hex(),"derived_seed_id":hashlib.sha256(value).hexdigest()},control=128)<0:return result("aborted_resource_limit",aborted or "events",decoded,corrected)
        perm=_perm(len(alice),frame_key,base_seed,p);blocks=[perm[i:i+size] for i in range(0,len(perm),size)]
        for b,members in enumerate(blocks):
            if timed():return result("aborted_resource_limit",aborted or "wall_s",decoded,corrected)
            parity=cache.setdefault((p,b,tuple(members.tolist())),_parity(alice,members));eid=append("BLOCK_PARITY","alice_to_bob",p,b,{"parity":parity,"block_range":[0,len(members)],"message_path":"primary"},key=1)
            if eid<0:return result("aborted_resource_limit",aborted or "events",decoded,corrected)
            if parity!=_parity(decoded,members) and (not bisect(p,b,members,eid,(p,b),False) or not drain()):return result("aborted_resource_limit",aborted or "events",decoded,corrected)
        completed.append(blocks)  # Only a fully processed pass is eligible for look-back.
    return result("verified_success","",decoded,corrected,True)
