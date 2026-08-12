"""Fail-closed formal LDPC-v1 single-frame protocol and codebook helpers."""
from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from ..utils.bitops import frame_symbol_error_rate, symbols_to_bits
from .shared import (
    formal_bp_osd_params, locked_seed_bits, preflight_ldpc, sha256_bytes,
    toeplitz_tag, transcript_summary, validate_outcome, verification_result,
)

METHOD = "ldpc_formal_v1"
GENERATOR_ID = "gf2_sparse_accumulator_v1"
N = 64
RATES = {"r050": 32, "r0375": 40, "r025": 48, "r0125": 56}
FRACTIONS = {name: checks / N for name, checks in RATES.items()}
DEFAULT_CAPS = {"wall_s": 5.0}


def _domain(rate_id: str, plane_id: int, column_id: int) -> bytes:
    return f"{GENERATOR_ID}|n=64|rate={rate_id}|plane={plane_id}|column={column_id}".encode("utf-8")


def gf2_rank(matrix: np.ndarray) -> int:
    work = np.asarray(matrix, dtype=np.uint8).copy() % 2; row = 0
    for col in range(work.shape[1]):
        found = next((i for i in range(row, work.shape[0]) if work[i, col]), None)
        if found is None: continue
        work[[row, found]] = work[[found, row]]
        for i in range(work.shape[0]):
            if i != row and work[i, col]: work[i] ^= work[row]
        row += 1
        if row == work.shape[0]: break
    return row


def generate_matrix(rate_id: str, plane_id: int) -> np.ndarray:
    if rate_id not in RATES or not isinstance(plane_id, int) or plane_id < 0 or plane_id >= 10:
        raise ValueError("unknown formal codebook")
    m = RATES[rate_id]; a_cols = N - m; h = np.zeros((m, N), dtype=np.uint8)
    for col in range(a_cols):
        seed = int.from_bytes(hashlib.sha256(_domain(rate_id, plane_id, col)).digest()[:16], "big")
        rows = np.random.Generator(np.random.PCG64(seed)).choice(m, size=min(3, m), replace=False)
        h[rows, col] = 1
    h[:, a_cols:] = np.eye(m, dtype=np.uint8)
    h[1:, a_cols:-1] ^= np.eye(m - 1, dtype=np.uint8)
    if gf2_rank(h) != m: raise ValueError("generated codebook rank mismatch")
    return h


def canonical_matrix_bytes(matrix: np.ndarray) -> bytes:
    h = np.asarray(matrix, dtype=np.uint8)
    if h.ndim != 2 or h.shape[1] != N or np.any((h != 0) & (h != 1)):
        raise ValueError("invalid HGF2V1 matrix")
    return b"HGF2V1" + np.asarray(h.shape, dtype="<u4").tobytes() + h.tobytes(order="C")


def parse_matrix_bytes(raw: bytes) -> np.ndarray:
    if len(raw) < 14 or raw[:6] != b"HGF2V1": raise ValueError("invalid HGF2V1 header")
    m, n = np.frombuffer(raw[6:14], dtype="<u4")
    if n != N or m not in RATES.values() or len(raw) != 14 + int(m) * int(n): raise ValueError("invalid HGF2V1 dimensions")
    h = np.frombuffer(raw[14:], dtype=np.uint8).reshape(int(m), int(n)).copy()
    if np.any((h != 0) & (h != 1)) or gf2_rank(h) != int(m): raise ValueError("invalid HGF2V1 rank")
    return h


def codebook_filename(rate_id: str, plane_id: int) -> str:
    if rate_id not in RATES or not 0 <= plane_id < 10: raise ValueError("unknown codebook")
    return f"formal_codebook_n64_{rate_id}_plane{plane_id:02d}.hgf2v1"


def codebook_entry(rate_id: str, plane_id: int) -> dict[str, Any]:
    h = generate_matrix(rate_id, plane_id); raw = canonical_matrix_bytes(h)
    return {"filename": codebook_filename(rate_id, plane_id), "sha256": sha256_bytes(raw), "m_checks": int(h.shape[0]), "n": N, "rank": gf2_rank(h), "design_rate": 1 - h.shape[0] / N, "rate_id": rate_id, "plane_id": plane_id, "generator_id": GENERATOR_ID, "construction_domain": _domain(rate_id, plane_id, 0).decode().rsplit("|column=", 1)[0]}


def materialize_codebooks(fresh_run_dir: Path, *, allow_plan_only: bool = False) -> dict[str, Any]:
    root = Path(fresh_run_dir)
    if root.exists():
        names = {item.name for item in root.iterdir()}
        if names and (not allow_plan_only or names != {"pre_run_plan.json"}):
            raise FileExistsError("formal codebook run directory must be fresh or plan-only")
    else: root.mkdir(parents=True)
    book = root / "codebooks"; book.mkdir(); entries = []
    for rate in RATES:
        for plane in range(10):
            h = generate_matrix(rate, plane); raw = canonical_matrix_bytes(h); path = book / codebook_filename(rate, plane)
            with path.open("xb") as handle: handle.write(raw)
            entries.append(codebook_entry(rate, plane))
    manifest = {"generator_id": GENERATOR_ID, "entries": entries}
    with (root / "formal_codebook_manifest.json").open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(manifest, sort_keys=True, separators=(",", ":")))
    return manifest


def verify_codebook_entry(entry: Mapping[str, Any], raw: bytes) -> np.ndarray:
    h = parse_matrix_bytes(raw)
    if entry.get("sha256") != sha256_bytes(raw) or entry.get("filename") != codebook_filename(str(entry.get("rate_id")), int(entry.get("plane_id", -1))):
        raise ValueError("codebook hash or filename mismatch")
    if (entry.get("n"), entry.get("m_checks"), entry.get("rank"), entry.get("generator_id")) != (N, h.shape[0], gf2_rank(h), GENERATOR_ID): raise ValueError("codebook metadata mismatch")
    expected_rate = 1 - h.shape[0] / N
    expected_domain = _domain(str(entry["rate_id"]), int(entry["plane_id"]), 0).decode().rsplit("|column=", 1)[0]
    if float(entry.get("design_rate", -1)) != expected_rate or entry.get("construction_domain") != expected_domain:
        raise ValueError("codebook rate or construction-domain mismatch")
    if not np.array_equal(h, generate_matrix(str(entry["rate_id"]), int(entry["plane_id"]))): raise ValueError("codebook generator mismatch")
    return h


def verify_codebook_manifest(run_dir: Path, manifest: Mapping[str, Any]) -> None:
    if manifest.get("generator_id") != GENERATOR_ID or not isinstance(manifest.get("entries"), list) or len(manifest["entries"]) != 40:
        raise ValueError("formal codebook manifest must index exactly 40 v1 matrices")
    expected = {(rate, plane) for rate in RATES for plane in range(10)}
    seen: set[tuple[str, int]] = set()
    for entry in manifest["entries"]:
        identity = (str(entry.get("rate_id")), int(entry.get("plane_id", -1)))
        if identity in seen or identity not in expected: raise ValueError("duplicate or unknown codebook identity")
        seen.add(identity)
        expected_filename = codebook_filename(*identity)
        if entry.get("filename") != expected_filename: raise ValueError("codebook manifest filename mismatch")
        path = Path(run_dir) / "codebooks" / expected_filename
        verify_codebook_entry(entry, path.read_bytes())
    if seen != expected: raise ValueError("incomplete formal codebook manifest")


def select_rate(p_hat: float) -> str:
    p = min(max(float(p_hat), 1e-4), .49); h2 = -p * math.log2(p) - (1 - p) * math.log2(1 - p); need = min(.875, 1.20 * h2)
    return next((rate for rate in RATES if FRACTIONS[rate] >= need), "unsupported_domain")


def _selection_hash(source_sha256: str, dataset_id: str, ordered_frame_keys: list[str], mapping: str, dimension: int) -> str:
    lock = {"source_sha256": source_sha256, "dataset_id": dataset_id, "ordered_frame_keys": ordered_frame_keys, "mapping": mapping, "dimension": dimension}
    return sha256_bytes(json.dumps(lock, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8"))


def calibrate_rates(
    sacrificed_pairs: Mapping[str, tuple[np.ndarray, np.ndarray]],
    *,
    sacrificed_frame_keys: Mapping[str, list[str]],
    calibration_role: str,
    mapping: str,
    source_bytes: bytes,
    dimension: int,
) -> dict[str, Any]:
    """Only caller-labelled sacrificed tuning pairs are accepted; no confirmation input exists here."""
    if calibration_role != "sacrificed_tuning_only" or not sacrificed_pairs:
        raise ValueError("explicit sacrificed_tuning_only calibration frames required")
    if mapping not in {"gray", "natural"} or dimension < 2 or dimension > 1024 or dimension & (dimension - 1):
        raise ValueError("calibration mapping or dimension unsupported")
    source_hash = sha256_bytes(source_bytes)
    rows: dict[str, Any] = {}
    for dataset, (alice, bob) in sacrificed_pairs.items():
        a, b = np.asarray(alice), np.asarray(bob)
        if a.shape != b.shape or a.ndim != 2 or a.shape[1] != 64: raise ValueError("calibration requires sacrificed 64-symbol frames")
        keys = sacrificed_frame_keys.get(dataset)
        if not isinstance(keys, list) or len(keys) != a.shape[0] or len(set(keys)) != len(keys) or any(not isinstance(k, str) or not k for k in keys):
            raise ValueError("calibration requires ordered unique sacrificed frame keys")
        if np.any(a < 0) or np.any(b < 0) or np.any(a >= dimension) or np.any(b >= dimension):
            raise ValueError("calibration symbol outside locked dimension")
        selection_hash = _selection_hash(source_hash, str(dataset), keys, mapping, dimension)
        ab, bb = symbols_to_bits(a, dimension, mapping), symbols_to_bits(b, dimension, mapping)
        planes = {}
        for plane in range(ab.shape[-1]):
            errors, total = int(np.count_nonzero(ab[:, :, plane] ^ bb[:, :, plane])), int(ab[:, :, plane].size); p = errors / total
            planes[str(plane)] = {"errors": errors, "total_bits": total, "p_hat": p, "rate_id": select_rate(p), "selected_input_sha256": selection_hash, "mapping": mapping}
        rows[str(dataset)] = {"ordered_frame_keys": list(keys), "keys_count": len(keys), "selection_sha256": selection_hash, "planes": planes}
    if set(rows) != {str(k) for k in sacrificed_frame_keys}: raise ValueError("frame-key datasets must exactly match calibration datasets")
    return {"calibration_role": calibration_role, "mapping": mapping, "dimension": dimension, "source_sha256": source_hash, "datasets": rows}


def _input(symbols: Any, q: int, mapping: str) -> np.ndarray:
    a = np.asarray(symbols)
    if a.shape != (64,) or not np.issubdtype(a.dtype, np.integer) or np.any(a < 0) or np.any(a >= q): raise ValueError("formal LDPC requires 64 in-range integer symbols")
    return symbols_to_bits(a.astype(np.int64), q, mapping).astype(np.uint8)


def _syndrome(h: np.ndarray, x: np.ndarray) -> np.ndarray: return (h @ x % 2).astype(np.uint8)


def _run_ldpc_formal_for_test(
    alice_symbols: Any,
    bob_symbols: Any,
    *,
    dimension: int,
    frozen_calibration: Mapping[str, Any],
    codebook_entries: Mapping[tuple[str, int], Mapping[str, Any]],
    codebook_bytes: Mapping[tuple[str, int], bytes],
    dataset_id: str = "synthetic",
    frame_id: str = "0",
    mapping: str = "gray",
    locked_seed: Mapping[str, Any] | None = None,
    _caps: Mapping[str, float] | None = None,
    _clock: Callable[[], float] = time.monotonic,
    _decoder_factory: Callable[..., Any] | None = None,
    _preflight: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    started = _clock(); events: list[dict[str, Any]] = []; key = f"{dataset_id}:{frame_id}"; raw_ser = float("nan"); limits = {**DEFAULT_CAPS, **(_caps or {})}; next_id = 1
    def add(kind: str, direction: str, plane: int, payload: dict[str, Any], kb=0, cb=0):
        nonlocal next_id
        events.append({"event_id": next_id, "frame_key": key, "method": METHOD, "event_type": kind, "direction": direction, "parent_event_id": None, "pass_id": -1, "plane_id": plane, "key_dependent_bits": kb, "public_control_bits": cb, "payload": payload}); next_id += 1
    def finish(status: str, failure: str, decoded: np.ndarray | None = None, invoke: bool = False, rates: list[str] | None = None, codebook_ids: list[str] | None = None):
        ver = {"verification_invoked": False, "verification_tag_bits": 0, "epsilon_ec": 0.0}
        if invoke and _clock() - started >= float(limits["wall_s"]):
            status, failure, invoke = "aborted_resource_limit", "wall_s", False
        if invoke and decoded is not None:
            ver = verification_result(alice.reshape(-1), decoded.reshape(-1), locked_seed, invoked=True); seed = locked_seed_bits(locked_seed, alice.size + 63)
            add("VERIFICATION_SEED", "control", -1, {"seed_id": locked_seed["seed_id"], "seed_bit_length": len(seed)}, cb=len(seed)); add("VERIFICATION_TAG", "alice_to_bob", -1, {"tag": toeplitz_tag(alice.reshape(-1), seed).hex()}, kb=64)
            if not ver["verified"]: status, failure = "verify_failed", "toeplitz_mismatch"
            if _clock() - started >= float(limits["wall_s"]): status, failure = "aborted_resource_limit", "wall_s"
        if status == "aborted_resource_limit":
            add("ABORT", "control", -1, {"cap": failure, "reason": "resource_limit"}, cb=1)
        summary = transcript_summary(events); syndrome_bits = sum(e["key_dependent_bits"] for e in events if e["event_type"] == "SYNDROME")
        out = {"dataset_id": dataset_id, "frame_id": str(frame_id), "n_pairs": 64, "pair_idx_sequence_sha256": hashlib.sha256(b",".join(str(i).encode() for i in range(64))).hexdigest(), "method": METHOD, "attempted": status not in {"preflight_unavailable", "invalid_input", "unsupported_domain", "backend_unavailable"}, "denominator_included": status not in {"preflight_unavailable", "invalid_input", "unsupported_domain", "backend_unavailable"}, "status": status, "failure_reason": failure, "dimension": dimension, "frame_len_symbols": 64, "raw_ser": raw_ser, "verification_invoked": ver["verification_invoked"], "verification_seed_id": locked_seed["seed_id"] if ver["verification_invoked"] else "", "verification_tag_bits": ver["verification_tag_bits"], "epsilon_ec": ver["epsilon_ec"], "key_dependent_disclosure_bits_total": summary["key_dependent_disclosure_bits_total"], "public_control_bits_total": summary["public_control_bits_total"], "transcript_first_event_id": events[0]["event_id"] if events else None, "transcript_last_event_id": events[-1]["event_id"] if events else None, "transcript_sha256": summary["transcript_sha256"], "runtime_s": max(0., _clock()-started), "ldpc_syndrome_bits": syndrome_bits, "verification_tag_bits_component": ver["verification_tag_bits"], "rate_ids": rates or [], "codebook_ids": codebook_ids or [], "calibration_source_sha256": frozen_calibration.get("source_sha256", ""), "mapping": mapping, "leakage_comparison_policy": "method_specific_not_cross_ranked"}
        validate_outcome(out); return {"outcome": out, "events": events, "decoded_bits": None if decoded is None else decoded.copy()}
    try:
        if not isinstance(dimension, int) or dimension < 2 or dimension > 1024 or dimension & (dimension - 1):
            return finish("unsupported_domain", "q must be 2^m, m=1..10") if np.asarray(alice_symbols).shape == (64,) else finish("invalid_input", "malformed symbols")
        if mapping not in {"gray", "natural"} or locked_seed is None: raise ValueError("mapping and locked seed required")
        alice, bob = _input(alice_symbols, dimension, mapping), _input(bob_symbols, dimension, mapping); locked_seed_bits(locked_seed, alice.size + 63)
    except (TypeError, ValueError) as exc: return finish("invalid_input", str(exc))
    raw_ser = frame_symbol_error_rate(np.asarray(alice_symbols), np.asarray(bob_symbols)); check = dict(_preflight) if _preflight is not None else preflight_ldpc()
    if check.get("status") != "ok": return finish("preflight_unavailable", "ldpc pinned dependency/API unavailable")
    if frozen_calibration.get("calibration_role") != "sacrificed_tuning_only" or frozen_calibration.get("mapping") != mapping or frozen_calibration.get("dimension") != dimension or not frozen_calibration.get("source_sha256"):
        return finish("unsupported_domain", "frozen calibration contract mismatch")
    dataset_calibration = frozen_calibration.get("datasets", {}).get(str(dataset_id))
    if not isinstance(dataset_calibration, Mapping): return finish("unsupported_domain", "no frozen dataset calibration")
    frame_keys = dataset_calibration.get("ordered_frame_keys")
    selection_hash = dataset_calibration.get("selection_sha256")
    planes = dataset_calibration.get("planes")
    expected_selection_hash = _selection_hash(str(frozen_calibration["source_sha256"]), str(dataset_id), frame_keys, mapping, dimension) if isinstance(frame_keys, list) and all(isinstance(k, str) for k in frame_keys) else ""
    if not isinstance(frame_keys, list) or not frame_keys or any(not k for k in frame_keys) or len(set(frame_keys)) != len(frame_keys) or dataset_calibration.get("keys_count") != len(frame_keys) or selection_hash != expected_selection_hash or not isinstance(planes, Mapping):
        return finish("unsupported_domain", "invalid frozen dataset calibration provenance")
    decoded = bob.copy(); rates: list[str] = []; ids: list[str] = []
    for plane in range(alice.shape[1]):
        if _clock() - started >= float(limits["wall_s"]): return finish("aborted_resource_limit", "wall_s", decoded, rates=rates, codebook_ids=ids)
        record = planes.get(str(plane)); rate = record.get("rate_id") if isinstance(record, Mapping) else None
        p_hat = record.get("p_hat") if isinstance(record, Mapping) else None
        errors = record.get("errors") if isinstance(record, Mapping) else None
        total = record.get("total_bits") if isinstance(record, Mapping) else None
        valid_counts = isinstance(errors, int) and not isinstance(errors, bool) and isinstance(total, int) and not isinstance(total, bool) and total > 0 and 0 <= errors <= total
        valid_p = isinstance(p_hat, (float, int)) and not isinstance(p_hat, bool) and math.isfinite(float(p_hat)) and valid_counts and math.isclose(float(p_hat), errors / total, rel_tol=0.0, abs_tol=1e-15)
        if rate not in RATES or not valid_p or rate != select_rate(float(p_hat)) or record.get("selected_input_sha256") != selection_hash or record.get("mapping") != mapping:
            return finish("unsupported_domain", "missing or inconsistent frozen plane calibration", decoded, rates=rates, codebook_ids=ids)
        try: h = verify_codebook_entry(codebook_entries[(rate, plane)], codebook_bytes[(rate, plane)])
        except (KeyError, ValueError) as exc: return finish("unsupported_domain", f"codebook: {exc}", decoded, rates=rates, codebook_ids=ids)
        rates.append(rate); ids.append(str(codebook_entries[(rate, plane)]["sha256"]))
        add("MATRIX_SELECTOR", "control", plane, {"matrix_id": ids[-1]}, cb=256); add("RATE_SELECTOR", "control", plane, {"rate_id": rate}, cb=len(rate.encode("ascii")) * 8)
        syndrome = _syndrome(h, alice[:, plane]); delta = syndrome ^ _syndrome(h, bob[:, plane]); add("SYNDROME", "alice_to_bob", plane, {"syndrome": np.packbits(syndrome, bitorder="big").tobytes().hex()}, kb=len(syndrome))
        try:
            if _decoder_factory is None:
                from ldpc import BpOsdDecoder  # type: ignore
                _decoder_factory = BpOsdDecoder
            p_locked = min(max(float(record["p_hat"]), 1e-4), .49)
            err = np.asarray(_decoder_factory(h, **formal_bp_osd_params(p_locked)).decode(delta), dtype=np.uint8).reshape(-1) % 2
        except Exception as exc:
            if _clock() - started >= float(limits["wall_s"]): return finish("aborted_resource_limit", "wall_s", decoded, rates=rates, codebook_ids=ids)
            return finish("decoder_error", type(exc).__name__, decoded, rates=rates, codebook_ids=ids)
        if _clock() - started >= float(limits["wall_s"]): return finish("aborted_resource_limit", "wall_s", decoded, rates=rates, codebook_ids=ids)
        if err.size != N: return finish("decoder_error", "decoder returned wrong length", decoded, rates=rates, codebook_ids=ids)
        if not np.array_equal(_syndrome(h, err), delta): return finish("syndrome_inconsistent", "decoder error syndrome mismatch", decoded, rates=rates, codebook_ids=ids)
        decoded[:, plane] = bob[:, plane] ^ err
        corrected_syndrome = _syndrome(h, decoded[:, plane])
        if not np.array_equal(corrected_syndrome, syndrome): return finish("syndrome_inconsistent", "corrected plane syndrome mismatch", decoded, rates=rates, codebook_ids=ids)
        add("PLANE_CONSISTENCY", "bob_local", plane, {"commitment": sha256_bytes(np.packbits(corrected_syndrome, bitorder="big").tobytes())})
    return finish("verified_success", "", decoded, True, rates, ids)


def run_ldpc_formal(
    alice_symbols: Any,
    bob_symbols: Any,
    *,
    dimension: int,
    frozen_calibration: Mapping[str, Any],
    codebook_entries: Mapping[tuple[str, int], Mapping[str, Any]],
    codebook_bytes: Mapping[tuple[str, int], bytes],
    dataset_id: str = "synthetic",
    frame_id: str = "0",
    mapping: str = "gray",
    locked_seed: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Production entrypoint: pinned real backend, fixed 5-second cap, no test seams."""
    return _run_ldpc_formal_for_test(
        alice_symbols, bob_symbols, dimension=dimension, frozen_calibration=frozen_calibration,
        codebook_entries=codebook_entries, codebook_bytes=codebook_bytes, dataset_id=dataset_id,
        frame_id=frame_id, mapping=mapping, locked_seed=locked_seed,
    )
