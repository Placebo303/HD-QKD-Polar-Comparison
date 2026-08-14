"""In-memory, sacrificed-development evaluator for long-frame v3 candidates."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import time
from collections import Counter
from typing import Any, Mapping, Sequence

import numpy as np

from .codebook_long_v3 import (
    BLOCK_LENGTHS, CANDIDATE_IDS, CONSTRUCTION_ID, CONSTRUCTION_VERSION,
    PLANE_IDS, generate_master, prefix_rows,
)

ROLE = "sacrificed_development_only"
PREFIX_IDS = ("p050", "p0625", "p075", "p0875")
_ALLOWED_STATUSES = {"development_exact_success", "development_decode_failed",
                     "development_syndrome_inconsistent", "development_decoder_error",
                     "development_backend_unavailable"}


def _compact(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _p_id(p: float) -> str:
    if p == .01: return "p001"
    if p == .02: return "p002"
    raise ValueError("p must be exactly .01 or .02")


def canonical_development_policy(n: int) -> dict[str, Any]:
    if n not in BLOCK_LENGTHS: raise ValueError("unsupported block length")
    base = {"dependency_version": "2.4.1", "max_iter": 50, "bp_method": "minimum_sum",
            "ms_scaling_factor": 1.0, "schedule": "serial", "omp_thread_count": 1,
            "serial_schedule_order": list(range(n)), "osd_method": "OSD_0", "osd_order": 0,
            "prefix_ids": list(PREFIX_IDS)}
    return {**base, "policy_id": hashlib.sha256(_compact(base)).hexdigest()}


def _seed(n: int, plane_id: int, p_id: str, kind: str) -> tuple[int, str, str]:
    domain = {"construction_id": CONSTRUCTION_ID, "construction_version": CONSTRUCTION_VERSION,
              "role": ROLE, "kind": kind, "n": n, "plane_id": plane_id, "p": p_id, "frame_count": 16}
    raw = hashlib.sha256(_compact(domain)).digest()[:16]
    return int.from_bytes(raw, "big"), raw.hex(), hashlib.sha256(raw).hexdigest()


def generate_sacrificed_development(n: int, plane_id: int, p: float, frame_count: int = 16) -> dict[str, Any]:
    if n not in BLOCK_LENGTHS or plane_id not in PLANE_IDS or frame_count != 16:
        raise ValueError("unsupported sacrificed-development domain")
    pid = _p_id(p)
    alice_int, alice_hex, alice_id = _seed(n, plane_id, pid, "alice")
    noise_int, noise_hex, noise_id = _seed(n, plane_id, pid, "noise")
    alice = np.random.Generator(np.random.PCG64(alice_int)).integers(0, 2, size=(16, n), dtype=np.uint8)
    noise = (np.random.Generator(np.random.PCG64(noise_int)).random(size=(16, n)) < p).astype(np.uint8)
    bob = alice ^ noise
    ids = [f"dev_n{n}_plane{plane_id:02d}_{pid}_f{index:02d}" for index in range(16)]
    base = {"role": ROLE, "n": n, "plane_id": plane_id, "p": p, "p_id": pid, "frame_count": 16,
            "frame_ids": ids, "alice_seed_hex": alice_hex, "alice_seed_id": alice_id,
            "noise_seed_hex": noise_hex, "noise_seed_id": noise_id,
            "error_count": int(noise.sum()), "total_bits": 16 * n, "p_hat": float(noise.sum() / (16 * n))}
    source = _compact(base) + b"\nALICE\n" + alice.tobytes(order="C") + b"\nBOB\n" + bob.tobytes(order="C")
    return {**base, "source_sha256": hashlib.sha256(source).hexdigest(), "alice_frames": alice, "bob_frames": bob}


def _syndrome(h: np.ndarray, bits: np.ndarray) -> np.ndarray:
    return (np.asarray(h, dtype=np.uint8) @ np.asarray(bits, dtype=np.uint8) % 2).astype(np.uint8)


def _validate_evaluation_inputs(alice: Any, bob: Any, n: int, plane_id: int, candidate_id: int,
                                p_hat: float, stratum_id: str, frame_ids: Sequence[str]) -> tuple[np.ndarray, np.ndarray]:
    if n not in BLOCK_LENGTHS or plane_id not in PLANE_IDS or candidate_id not in CANDIDATE_IDS or stratum_id not in {"p001", "p002"}:
        raise ValueError("unsupported candidate evaluation identity")
    a, b = np.asarray(alice), np.asarray(bob)
    if a.shape != (16, n) or b.shape != (16, n) or a.dtype != np.uint8 or b.dtype != np.uint8 or np.any((a > 1) | (b > 1)):
        raise ValueError("expected matching 16-by-n uint8 binary frames")
    expected = [f"dev_n{n}_plane{plane_id:02d}_{stratum_id}_f{i:02d}" for i in range(16)]
    if list(frame_ids) != expected or not np.isfinite(p_hat) or not 0 <= float(p_hat) < .5:
        raise ValueError("invalid development frame IDs or p_hat")
    return a, b


def _backend(factory: Any) -> tuple[Any | None, str]:
    if factory is not None: return factory, "test_injected"
    try:
        if importlib.metadata.version("ldpc") != "2.4.1": return None, "ldpc_unavailable_or_version_mismatch"
        from ldpc import BpOsdDecoder  # type: ignore[import-not-found]
        return BpOsdDecoder, "ldpc==2.4.1"
    except (ImportError, AttributeError, importlib.metadata.PackageNotFoundError):
        return None, "ldpc_unavailable_or_version_mismatch"


def evaluate_candidate(alice_frames: Any, bob_frames: Any, *, n: int, plane_id: int, candidate_id: int,
                       p_hat: float, stratum_id: str, frame_ids: Sequence[str], decoder_factory: Any = None) -> list[dict[str, Any]]:
    alice, bob = _validate_evaluation_inputs(alice_frames, bob_frames, n, plane_id, candidate_id, p_hat, stratum_id, frame_ids)
    policy = canonical_development_policy(n); factory, identity = _backend(decoder_factory)
    common = {"n": n, "plane_id": plane_id, "candidate_id": candidate_id, "stratum_id": stratum_id,
              "policy_id": policy["policy_id"], "p_hat": float(p_hat), "backend_identity": identity}
    if factory is None:
        return [{**common, "frame_id": frame_id, "attempted": False, "status": "development_backend_unavailable",
                 "terminal_prefix_id": "", "rounds_attempted": 0, "syndrome_bits_disclosed": 0,
                 "exact_match": False, "runtime_s": 0.0} for frame_id in frame_ids]
    master = generate_master(n, plane_id, candidate_id); rows = prefix_rows(n); results = []
    kwargs = {key: policy[key] for key in ("max_iter", "bp_method", "ms_scaling_factor", "schedule", "omp_thread_count", "serial_schedule_order", "osd_method", "osd_order")}
    kwargs["error_rate"] = min(max(float(p_hat), 1e-4), .49)
    for frame_id, a, b in zip(frame_ids, alice, bob):
        started = time.perf_counter(); status = "development_decode_failed"; terminal = ""; rounds = 0; disclosed = 0; exact = False
        for prefix_id in PREFIX_IDS:
            rounds += 1; m = rows[prefix_id]; h = master[:m]; disclosed = m
            delta = _syndrome(h, a) ^ _syndrome(h, b)
            try: error = np.asarray(factory(h, **kwargs).decode(delta)).reshape(-1)
            except Exception: status = "development_decoder_error"; terminal = prefix_id; break
            if error.size != n or np.any((error != 0) & (error != 1)):
                status = "development_decoder_error"; terminal = prefix_id; break
            error = error.astype(np.uint8)
            if not np.array_equal(_syndrome(h, error), delta):
                status = "development_syndrome_inconsistent"; terminal = prefix_id; break
            corrected = b ^ error
            if np.array_equal(corrected, a):
                status = "development_exact_success"; terminal = prefix_id; exact = True; break
            terminal = prefix_id
        results.append({**common, "frame_id": frame_id, "attempted": True, "status": status, "terminal_prefix_id": terminal,
                        "rounds_attempted": rounds, "syndrome_bits_disclosed": disclosed, "exact_match": exact,
                        "runtime_s": time.perf_counter() - started})
    return results


def select_candidate(candidate_outcomes: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    rows = [dict(row) for row in candidate_outcomes]
    if len(rows) != 128: raise ValueError("selection requires exactly 128 development rows")
    required = {"n", "plane_id", "candidate_id", "stratum_id", "frame_id", "attempted", "status", "terminal_prefix_id", "rounds_attempted", "syndrome_bits_disclosed", "exact_match", "policy_id", "p_hat"}
    if any(required.difference(row) for row in rows): raise ValueError("incomplete selection outcome")
    if len({row["n"] for row in rows}) != 1 or len({row["plane_id"] for row in rows}) != 1 or len({row["policy_id"] for row in rows}) != 1:
        raise ValueError("selection grid metadata mismatch")
    for row in rows:
        if (not isinstance(row["candidate_id"], int) or isinstance(row["candidate_id"], bool)
                or row["candidate_id"] not in CANDIDATE_IDS
                or not all(isinstance(row[name], str) for name in ("stratum_id", "frame_id", "status", "policy_id", "terminal_prefix_id"))):
            raise ValueError("invalid selection identity type")
    n, plane, policy_id = rows[0]["n"], rows[0]["plane_id"], rows[0]["policy_id"]
    if (not isinstance(n, int) or isinstance(n, bool) or n not in BLOCK_LENGTHS or not isinstance(plane, int)
            or isinstance(plane, bool) or plane not in PLANE_IDS or policy_id != canonical_development_policy(n)["policy_id"]):
        raise ValueError("selection uses unsupported domain or noncanonical policy")
    aggregates: dict[str, Any] = {}; frame_orders: dict[str, list[str]] = {}; stratum_p_hats: dict[str, float] = {}
    for candidate in CANDIDATE_IDS:
        candidate_rows = [r for r in rows if r["candidate_id"] == candidate]
        if len(candidate_rows) != 32: raise ValueError("incomplete candidate grid")
        successes: dict[str, int] = {}; counts = Counter(); total_bits = 0
        for stratum in ("p001", "p002"):
            group = [r for r in candidate_rows if r["stratum_id"] == stratum]
            if len(group) != 16 or len({r["frame_id"] for r in group}) != 16 or any(r["status"] not in _ALLOWED_STATUSES for r in group): raise ValueError("malformed candidate stratum")
            expected_ids = [f"dev_n{n}_plane{plane:02d}_{stratum}_f{i:02d}" for i in range(16)]
            if [r["frame_id"] for r in group] != expected_ids: raise ValueError("noncanonical development frame order")
            for row in group:
                p_hat = row["p_hat"]
                if isinstance(p_hat, bool) or not isinstance(p_hat, (int, float)) or not np.isfinite(p_hat) or not 0 <= float(p_hat) < .5:
                    raise ValueError("invalid p_hat")
                if not isinstance(row["attempted"], bool) or not isinstance(row["exact_match"], bool): raise ValueError("invalid boolean outcome field")
                for name in ("rounds_attempted", "syndrome_bits_disclosed"):
                    if not isinstance(row[name], int) or isinstance(row[name], bool) or row[name] < 0: raise ValueError("invalid disclosure or rounds")
                status = row["status"]
                if status == "development_backend_unavailable":
                    if row["attempted"] or row["terminal_prefix_id"] != "" or row["rounds_attempted"] != 0 or row["syndrome_bits_disclosed"] != 0 or row["exact_match"]:
                        raise ValueError("invalid backend-unavailable outcome")
                else:
                    terminal = row["terminal_prefix_id"]
                    if not row["attempted"] or terminal not in PREFIX_IDS:
                        raise ValueError("invalid attempted outcome")
                    expected_rounds = PREFIX_IDS.index(terminal) + 1
                    if row["rounds_attempted"] != expected_rounds or row["syndrome_bits_disclosed"] != prefix_rows(n)[terminal]:
                        raise ValueError("invalid terminal prefix accounting")
                    if row["exact_match"] != (status == "development_exact_success"):
                        raise ValueError("exact-match/status mismatch")
                    if status == "development_decode_failed" and terminal != "p0875":
                        raise ValueError("decode failure must exhaust prefixes")
            if len({r["p_hat"] for r in group}) != 1: raise ValueError("p_hat differs within stratum")
            group_p_hat = float(group[0]["p_hat"])
            if stratum in stratum_p_hats and stratum_p_hats[stratum] != group_p_hat: raise ValueError("p_hat differs across candidates")
            stratum_p_hats.setdefault(stratum, group_p_hat)
            order = [r["frame_id"] for r in group]
            if stratum in frame_orders and frame_orders[stratum] != order: raise ValueError("frame order differs across candidates")
            frame_orders.setdefault(stratum, order); successes[stratum] = sum(r["status"] == "development_exact_success" for r in group)
            counts.update(r["status"] for r in group); total_bits += sum(int(r["syndrome_bits_disclosed"]) for r in group)
        aggregates[str(candidate)] = {"successes_by_stratum": successes, "total_successes": sum(successes.values()),
                                      "total_syndrome_bits_disclosed": total_bits, "status_counts": dict(sorted(counts.items()))}
    if {r["candidate_id"] for r in rows} != set(CANDIDATE_IDS) or {r["stratum_id"] for r in rows} != {"p001", "p002"}: raise ValueError("selection identities mismatch")
    tuples = {int(key): (-min(value["successes_by_stratum"].values()), -value["total_successes"], value["total_syndrome_bits_disclosed"], int(key)) for key, value in aggregates.items()}
    selected, selection_tuple = min(tuples.items(), key=lambda item: item[1])
    base = {"n": n, "plane_id": plane, "policy_id": policy_id,
            "aggregates": aggregates, "selected_candidate_id": selected, "selection_tuple": list(selection_tuple)}
    return {**base, "selection_sha256": hashlib.sha256(_compact(base)).hexdigest()}
