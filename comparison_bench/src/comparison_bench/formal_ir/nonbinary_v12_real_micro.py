"""V12 nonbinary LDPC real micro-feasibility method wrapper and lifecycle
(``formal-nonbinary-ldpc-v12-real-micro-feasibility``).

Implements the frozen V12 delta specification:

- **V12-I01** immutable V7 R1 reconstruction/binding checks against the frozen
  GF(1024) ``n=256`` ``m=170`` degree-2 PEG codebook (``NBLDPC7``,
  seed ``2026080400``);
- **V12-I02** the V12 method wrapper.  The Alice-information boundary is
  enforced **before** any method runner is invoked: the public full syndrome
  (1700 key-dependent bits) is the only Alice-derived input that crosses the
  runner boundary, together with Bob's symbols, the frozen ``p=.20`` QSC
  prior and the frozen decoder constants.  The runner never receives Alice
  truth, frame-specific SER, error locations, or verification feedback;
- **V12-I04** canonical transcript, conditional Toeplitz verification and
  leakage accounting (1700-bit full syndrome; 64-bit tag and 2623-bit public
  seed only when verification is invoked; local outcome events carry zero
  disclosure bits), retained outcome rows, and the four terminal states
  ``source_partition_blocked`` / ``invalid_execution`` / ``failed_canary`` /
  ``observed_real_correction``;
- **V12-I05** separated plan / execute / read-only verification.  A
  main-thread-authorized **prepare-only** production path
  (:func:`prepare_production`, V12-RP01..RP03) writes exactly the three
  preparation artifacts into one fresh additive package directory without
  decoding; production execute stays a hard stop and test-only execution
  requires an explicit fake runner and a test-owned fresh
  ``workspace/nbldpc_v12_tests_<uuid>`` root.  The read-only verifier never
  imports or calls a decoder (the only decoder import is lazy, inside
  :func:`production_runner`).

The exact seven-file package contract is implemented (design.md section 6) but
used only in fake test roots during this phase.  Binary V5 leakage values are
not copied; leakage is reconstructed from canonical events only.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
import re
import subprocess
import time
from io import StringIO
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from ..utils.bitops import frame_symbol_error_rate
from .nonbinary_field import GF2mField
from .nonbinary_qspa import nonbinary_syndrome, symbols_to_msb_bits
from .shared import (canonical_event, locked_seed_bits, materialize_seed_record,
                     toeplitz_tag, transcript_summary)
from . import nonbinary_v7_r1a_codebook as v7_cb
from . import nonbinary_v12_real_partition as partition

METHOD = partition.METHOD
Q, N, M = partition.Q, partition.N, partition.M
STRATUM = partition.STRATUM
P = partition.P
SYNDROME_BITS = partition.SYNDROME_BITS
SEED_BITS = partition.SEED_BITS
TAG_BITS = partition.TAG_BITS
ROLE = partition.ROLE
FRAME_COUNT = partition.FRAME_COUNT
ARTIFACTS = partition.ARTIFACTS
PREPARE_ARTIFACTS = partition.PREPARE_ARTIFACTS
RUN_ID = partition.RUN_ID
TEST_RUN_ID = partition.TEST_RUN_ID

PLAN_SCHEMA = "nbldpc_v12_real_plan_v1"
TEST_PLAN_SCHEMA = "nbldpc_v12_real_plan_test_v1"
RUN_MANIFEST_SCHEMA = "nbldpc_v12_real_run_manifest_v1"
TEST_RUN_MANIFEST_SCHEMA = "nbldpc_v12_real_run_manifest_test_v1"
REPORT_SCHEMA = "nbldpc_v12_real_report_v1"
TEST_REPORT_SCHEMA = "nbldpc_v12_real_report_test_v1"
SEED_SCHEDULE_SCHEMA = "nbldpc_v12_seed_schedule_v1"
FAILURE_POLICY = "immutable_no_rerun_no_resume_no_tuning_no_replacement"
TERMINAL_STATES = ("source_partition_blocked", "invalid_execution",
                   "failed_canary", "observed_real_correction")

# ------------------------------------------------------------------ frozen V7 R1 binding (I01)

V7_R1A_METHOD = "nbldpc_formal_v7_r1a_mr0"
# Immutable binding reconstructed from the accepted V7 R1A codebook
# (nonbinary_v7_r1a_codebook.py).  These values were computed once from the
# frozen deterministic reconstruction and are never re-searched at runtime.
V7_R1A_FROZEN = {
    "canonical_schema": "NBLDPC7",
    "method": V7_R1A_METHOD,
    "q": 1024,
    "n": 256,
    "m": 170,
    "construction_seed": 2026080400,
    "rank": 170,
    "edge_count": 512,
    "check_degree_histogram": {"3": 168, "4": 2},
    "manifest_id": "93267fc5f069c4189c358342f7fbd7981f7b0093d577784b7eb231a177f66ad8",
    "canonical_sha256": "75f625bbbe1ebd74b0cf8b0b3646fa1af9ce6e5a66562e07a75507d175570608",
}

_ALLOWED_RAW_STATUSES = {"syndrome_consistent", "decode_failed", "decoder_error",
                         "codebook_invalid", "invalid_input", "unsupported_domain",
                         "aborted_resource_limit"}
# Allowed scientific outcomes (spec.md): verified_success / verify_failed /
# decode_failed.  Everything else is a forbidden failure that invalidates the run.
_ALLOWED_STATUSES = {"verified_success", "verify_failed", "decode_failed"}
_FORBIDDEN_STATUSES = {"decoder_error", "codebook_invalid", "invalid_input",
                       "unsupported_domain", "aborted_resource_limit",
                       "syndrome_inconsistent"}

OUTCOME_FIELDS = (
    "frame_id", "dataset_id", "method", "attempted", "denominator_included",
    "status", "failure_reason", "dimension", "frame_len_symbols", "mapping",
    "raw_ser", "check_count", "iterations", "verification_invoked",
    "verification_seed_id", "verification_tag_bits", "epsilon_ec",
    "key_dependent_disclosure_bits_total", "public_control_bits_total",
    "transcript_first_event_id", "transcript_last_event_id",
    "transcript_sha256", "runtime_s", "leakage_comparison_policy",
)
CSV_PREFIX_FIELDS = ("role", "stratum", "plan_frame_id", "alice_sha256",
                     "bob_sha256", "transcript_bytes_len", "transcript_bytes_sha256")
CSV_FIELDS = CSV_PREFIX_FIELDS + OUTCOME_FIELDS
_MAX_ITER = 100
CAPS = {"workers": 1, "q": Q, "n": N, "m": M, "max_iter": _MAX_ITER,
        "dense_bytes_max": 16 * 1024 * 1024, "per_frame_events": 8}
GATES = {"denominator": FRAME_COUNT, "verified_success_min": 1, "forbidden_failure_limit": 0}
LEAKAGE_CONTRACT = {"syndrome_bits": SYNDROME_BITS, "tag_bits": TAG_BITS,
                    "seed_bits": SEED_BITS, "local_event_disclosure_bits": 0,
                    "source": "v12 design.md section 5; binary V5 leakage values not copied"}

_SCOPED_SOURCES = (
    "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v12_real_micro.py",
    "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v12_real_partition.py",
    "comparison_bench/src/comparison_bench/cli/run_formal_nonbinary_v12_real_micro.py",
    "comparison_bench/src/comparison_bench/cli/verify_formal_nonbinary_v12_real_micro.py",
    "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v7_r1a_codebook.py",
    "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v7_r1a_long.py",
    "comparison_bench/src/comparison_bench/formal_ir/nonbinary_field.py",
    "comparison_bench/src/comparison_bench/formal_ir/nonbinary_qspa.py",
    "comparison_bench/src/comparison_bench/formal_ir/shared.py",
)
CONTRACT = ("openspec/changes/formal-nonbinary-ldpc-v12-real-micro-feasibility/"
            "specs/formal-nonbinary-ldpc-v12-real-micro-feasibility/spec.md")


def _compact(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def _sha(value: Any) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else _compact(value)).hexdigest()


def _self(value: dict[str, Any], key: str) -> dict[str, Any]:
    return {**value, key: _sha(_compact(value))}


def _is_hex(value: Any, width: int) -> bool:
    return isinstance(value, str) and len(value) == width and value == value.lower() \
        and all(c in "0123456789abcdef" for c in value)


def _is_hex64(value: Any) -> bool:
    return _is_hex(value, 64)


def _root() -> Path:
    return Path(__file__).resolve().parents[4]


def _put(path: Path, value: Any) -> None:
    path.open("xb").write(_compact(value))


def _write(path: Path, value: bytes) -> None:
    path.open("xb").write(value)


def _json_read(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    doc = json.loads(raw)
    if not isinstance(doc, dict) or _compact(doc) != raw:
        raise ValueError("noncanonical json")
    return doc


def _array_sha(values: Any) -> str:
    data = np.asarray(values, dtype=np.int64)
    return _sha(np.asarray(data, dtype="<u2").tobytes())


def _prior_seed_ids(exclude: Any = None) -> set[str]:
    """Read-only scan of locally discoverable formal evidence seed records."""
    found: set[str] = set()
    base = _root() / "comparison_bench/outputs_comparison/formal_ir_methods"
    if not base.exists():
        return found
    for path in base.rglob("*.json"):
        if exclude is not None and path.resolve() == Path(exclude).resolve():
            continue
        try:
            text = path.read_text(encoding="utf8")
        except OSError:
            continue
        found.update(re.findall(r'"seed_id"\s*:\s*"([0-9a-f]{64})"', text))
    return found


def _provenance() -> dict[str, Any]:
    root = _root()
    source_sha256 = {rel: _sha((root / rel).read_bytes()) for rel in _SCOPED_SOURCES}
    try:
        commit = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"],
                                         text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.SubprocessError):
        commit = "unavailable"
    return {"source_sha256": source_sha256,
            "contract_sha256": _sha((root / CONTRACT).read_bytes()),
            "environment": {"python": platform.python_version(), "numpy": np.__version__,
                            "platform": platform.platform()},
            "git_commit": commit}


# ------------------------------------------------------------------ V7 R1 reconstruction (I01)

def reconstruct_v7_r1a() -> tuple[dict[str, Any], Any]:
    """Reconstruct the frozen V7 R1A GF(1024) ``n=256`` ``m=170`` codebook
    without modifying its matrix.  Deterministic and cached by the V7 module."""
    return v7_cb.build_nbldpc_v7_r1a_codebook()


def verify_v7_r1a_binding() -> dict[str, Any]:
    """Fail closed unless the reconstructed V7 R1A binding equals the frozen
    constants (method identity, field/geometry, seed, rank, edge count, check
    degree histogram, manifest id and canonical byte hash)."""
    manifest, matrix = reconstruct_v7_r1a()
    for key, expected in V7_R1A_FROZEN.items():
        if manifest.get(key) != expected:
            raise ValueError(f"V7 R1A frozen binding mismatch: {key}")
    if len(matrix) != M or any(len(row) != N for row in matrix):
        raise ValueError("V7 R1A matrix shape mismatch")
    return {"status": "ok", "method": V7_R1A_METHOD,
            "manifest_id": manifest["manifest_id"],
            "canonical_sha256": manifest["canonical_sha256"],
            "matrix_shape": (M, N)}


# ------------------------------------------------------------------ method wrapper (I02)

def production_runner(bob_symbols: Any, syndrome: Any, manifest: Mapping[str, Any],
                      matrices: Any, *, check_count: int, p: float) -> dict[str, Any]:
    """V12 production method runner: the frozen V7 R1A primary undamped
    flooding FFT-QSPA, reconstructed without modification.

    The decoder import is lazy and lives only here, so the plan / verify paths
    never import a decoder.  The runner receives only Bob symbols, the public
    syndrome, the frozen codebook binding and the frozen ``p=.20`` prior.
    """
    from . import nonbinary_v7_r1a_long as v7_long  # decoder boundary: execute-only
    return v7_long.production_runner(bob_symbols, syndrome, manifest, matrices,
                                     check_count=check_count, p=p)


def _frame_events(frame_key: str, raw_status: str, syndrome: Any, *, invoked: bool,
                  tag: bytes, seed: Mapping[str, Any], match_value: str,
                  final_status: str, start_id: int) -> list[dict[str, Any]]:
    """Canonical V12 events for one frame.  The full syndrome (1700 bits) is
    disclosed on every attempted frame; the 64-bit tag and 2623-bit public
    seed only when verification is invoked; local decoder/verification outcome
    events carry zero disclosure bits (design.md section 5)."""
    events: list[dict[str, Any]] = []
    event_id = start_id

    def add(kind: str, direction: str, key: int, public: int, payload: dict[str, Any]) -> None:
        nonlocal event_id
        events.append({"event_id": event_id, "frame_key": frame_key, "method": METHOD,
                       "event_type": kind, "direction": direction, "parent_event_id": None,
                       "pass_id": 0, "plane_id": "q1024", "key_dependent_bits": key,
                       "public_control_bits": public, "payload": payload})
        event_id += 1

    add("SYNDROME", "alice_to_bob", SYNDROME_BITS, 0, {"syndrome": list(syndrome)})
    add("DECODER_STAGE", "bob_local", 0, 0, {"reason": raw_status})
    if invoked:
        add("VERIFICATION_SEED", "control", 0, SEED_BITS,
            {"seed_id": seed["seed_id"], "seed_bit_length": SEED_BITS})
        add("VERIFICATION_TAG", "alice_to_bob", TAG_BITS, 0, {"tag": tag.hex()})
        add("FRAME_TAG_CHECK", "bob_local", 0, 0, {"value": match_value})
    # Local audit record, never protocol disclosure: zero disclosure bits.
    add("STAGE_DECISION", "control", 0, 0, {"reason": final_status})
    return events


def _frame_array(frame: Mapping[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    alice = np.asarray(frame.get("alice"), dtype=np.int64)
    bob = np.asarray(frame.get("bob"), dtype=np.int64)
    if alice.shape != (N,) or bob.shape != (N,) \
            or np.any(alice < 0) or np.any(alice >= Q) or np.any(bob < 0) or np.any(bob >= Q):
        raise ValueError("frame domain")
    return alice, bob


def _frame_result(frame: Mapping[str, Any], seed: Mapping[str, Any], runner: Callable[..., Any],
                  cb: Mapping[str, Any], mats: Any, field: GF2mField, event_start: int,
                  *, _clock: Callable[[], float] = time.monotonic) -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    """Run one frame through the explicit runner and bind the outcome,
    verification accounting and canonical events.

    The Alice-information boundary is enforced BEFORE the runner is invoked:
    the public full syndrome is computed from Alice here, and the runner is
    called with only ``(bob, syndrome, cb, mats, check_count, p)``.  Alice
    truth, frame SER, error locations and verification feedback never cross
    that boundary.  Invalid runner output fails closed to a forbidden status.
    """
    alice, bob = _frame_array(frame)
    syndrome = nonbinary_syndrome(mats, alice, field)
    started = _clock()
    raw = runner(bob, syndrome, cb, mats, check_count=M, p=P)
    runtime_s = round(_clock() - started, 3)
    if not isinstance(raw, Mapping):
        raw = {}
    raw_status = str(raw.get("status", "decoder_error"))
    if raw_status not in _ALLOWED_RAW_STATUSES:
        raw_status, reason = "decoder_error", "unknown_stage_status"
    else:
        reason = raw_status
    try:
        iterations = int(raw.get("iterations", 0))
    except (TypeError, ValueError):
        iterations = 0
    if not 0 <= iterations <= _MAX_ITER:
        raw_status, reason = "aborted_resource_limit", "iterations"
    final, invoked, tag, match_value = raw_status, False, b"", ""
    if raw_status == "syndrome_consistent":
        try:
            decoded = tuple(int(x) for x in raw["decoded_symbols"])
            valid = len(decoded) == N and all(0 <= x < Q for x in decoded)
        except (KeyError, TypeError, ValueError):
            valid = False
        if not valid:
            raw_status, reason = "decoder_error", "decoded_symbols"
            final = raw_status
        elif nonbinary_syndrome(mats, decoded, field) != syndrome:
            # The returned word is not consistent with the public syndrome:
            # forbidden failure, never a verified success (spec.md).
            raw_status, reason = "syndrome_inconsistent", "public_syndrome_mismatch"
            final = raw_status
        else:
            seed_bits = locked_seed_bits(seed, SEED_BITS)
            alice_tag = toeplitz_tag(symbols_to_msb_bits(alice, Q), seed_bits)
            bob_tag = toeplitz_tag(symbols_to_msb_bits(decoded, Q), seed_bits)
            matched = alice_tag == bob_tag
            final = "verified_success" if matched else "verify_failed"
            tag, invoked, match_value = alice_tag, True, "match" if matched else "mismatch"
    expected_key = SYNDROME_BITS + (TAG_BITS if invoked else 0)
    expected_public = SEED_BITS if invoked else 0
    frame_key = f"{frame['dataset_id']}:{frame['frame_id']}"
    events = _frame_events(frame_key, reason, syndrome, invoked=invoked, tag=tag, seed=seed,
                           match_value=match_value, final_status=final, start_id=event_start)
    summary = transcript_summary(events)
    if summary["key_dependent_disclosure_bits_total"] != expected_key \
            or summary["public_control_bits_total"] != expected_public:
        raise ValueError("disclosure accounting drift")
    raw_ser = float(frame_symbol_error_rate(alice, bob))
    row = {"frame_id": int(frame["frame_id"]), "dataset_id": str(frame["dataset_id"]),
           "method": METHOD, "attempted": True, "denominator_included": True,
           "status": final, "failure_reason": reason, "dimension": Q,
           "frame_len_symbols": N, "mapping": "gray", "raw_ser": raw_ser,
           "check_count": M, "iterations": iterations,
           "verification_invoked": invoked,
           "verification_seed_id": str(seed["seed_id"]) if invoked else "",
           "verification_tag_bits": TAG_BITS if invoked else 0,
           "epsilon_ec": 2.0 ** -64 if invoked else 0.0,
           "key_dependent_disclosure_bits_total": summary["key_dependent_disclosure_bits_total"],
           "public_control_bits_total": summary["public_control_bits_total"],
           "transcript_first_event_id": events[0]["event_id"],
           "transcript_last_event_id": events[-1]["event_id"],
           "transcript_sha256": summary["transcript_sha256"], "runtime_s": runtime_s,
           "leakage_comparison_policy": "method_specific_not_cross_ranked"}
    validate_outcome_v12(row, events)
    return row, events, final


# ------------------------------------------------------------------ validation / accounting (I04)

def validate_outcome_v12(row: Mapping[str, Any], events: Any = None) -> None:
    if not isinstance(row, Mapping) or tuple(row) != OUTCOME_FIELDS:
        raise ValueError("v12 outcome identity")
    if row["method"] != METHOD or row["dimension"] != Q or row["frame_len_symbols"] != N \
            or row["mapping"] != "gray" or row["check_count"] != M \
            or row["leakage_comparison_policy"] != "method_specific_not_cross_ranked":
        raise ValueError("v12 outcome identity")
    for flag in ("attempted", "denominator_included", "verification_invoked"):
        if type(row[flag]) is not bool:
            raise ValueError("v12 outcome flags")
    # Every V12 frame enters the denominator exactly once (spec.md lifecycle).
    if not row["attempted"] or not row["denominator_included"]:
        raise ValueError("v12 denominator")
    status = row["status"]
    if status not in _ALLOWED_STATUSES and status not in _FORBIDDEN_STATUSES:
        raise ValueError("v12 unregistered status")
    if row["verification_invoked"]:
        if status not in _ALLOWED_STATUSES or row["verification_tag_bits"] != TAG_BITS \
                or row["epsilon_ec"] != 2.0 ** -64 or row["verification_seed_id"] == "" \
                or not _is_hex64(row["verification_seed_id"]):
            raise ValueError("v12 verification accounting")
    else:
        if row["verification_tag_bits"] != 0 or row["epsilon_ec"] != 0.0 \
                or row["verification_seed_id"] != "":
            raise ValueError("v12 non-invoked verification accounting")
    expected_key = SYNDROME_BITS + (TAG_BITS if row["verification_invoked"] else 0)
    expected_public = SEED_BITS if row["verification_invoked"] else 0
    if row["key_dependent_disclosure_bits_total"] != expected_key \
            or row["public_control_bits_total"] != expected_public:
        raise ValueError("v12 disclosure accounting")
    if events is not None:
        if not isinstance(events, list) or not events:
            raise ValueError("v12 empty events")
        summary = transcript_summary(events)
        if summary["transcript_sha256"] != row["transcript_sha256"] \
                or summary["key_dependent_disclosure_bits_total"] != expected_key \
                or summary["public_control_bits_total"] != expected_public:
            raise ValueError("v12 transcript summary")
        ids = [e["event_id"] for e in events]
        if ids != list(range(row["transcript_first_event_id"], row["transcript_last_event_id"] + 1)):
            raise ValueError("v12 transcript ids")
        for event in events:
            canonical_event(event)
        _validate_event_flow(events, row)


def _validate_event_flow(events: list[Mapping[str, Any]], row: Mapping[str, Any]) -> None:
    expected = ["SYNDROME", "DECODER_STAGE"]
    if row["verification_invoked"]:
        expected += ["VERIFICATION_SEED", "VERIFICATION_TAG", "FRAME_TAG_CHECK"]
    expected.append("STAGE_DECISION")
    if [e["event_type"] for e in events] != expected:
        raise ValueError("v12 event order")
    frame_key = f"{row['dataset_id']}:{row['frame_id']}"
    for event in events:
        if event["frame_key"] != frame_key or event["method"] != METHOD \
                or event["plane_id"] != "q1024" or event["pass_id"] != 0 \
                or event["parent_event_id"] is not None \
                or event["direction"] not in {"alice_to_bob", "bob_local", "control"}:
            raise ValueError("v12 event identity")
    syndrome_events = [e for e in events if e["event_type"] == "SYNDROME"]
    if len(syndrome_events) != 1 or syndrome_events[0]["direction"] != "alice_to_bob" \
            or syndrome_events[0]["key_dependent_bits"] != SYNDROME_BITS \
            or syndrome_events[0]["public_control_bits"] != 0 \
            or set(syndrome_events[0]["payload"]) != {"syndrome"}:
        raise ValueError("v12 syndrome envelope")
    if row["verification_invoked"]:
        seed_events = [e for e in events if e["event_type"] == "VERIFICATION_SEED"]
        tag_events = [e for e in events if e["event_type"] == "VERIFICATION_TAG"]
        check_events = [e for e in events if e["event_type"] == "FRAME_TAG_CHECK"]
        if len(seed_events) != 1 or len(tag_events) != 1 or len(check_events) != 1:
            raise ValueError("v12 verification events")
        seed = seed_events[0]
        if seed["direction"] != "control" or seed["key_dependent_bits"] != 0 \
                or seed["public_control_bits"] != SEED_BITS \
                or set(seed["payload"]) != {"seed_id", "seed_bit_length"} \
                or seed["payload"]["seed_bit_length"] != SEED_BITS \
                or not _is_hex64(seed["payload"]["seed_id"]):
            raise ValueError("v12 seed envelope")
        tag = tag_events[0]
        if tag["direction"] != "alice_to_bob" or tag["key_dependent_bits"] != TAG_BITS \
                or tag["public_control_bits"] != 0 or set(tag["payload"]) != {"tag"} \
                or not _is_hex(tag["payload"]["tag"], 16):
            raise ValueError("v12 tag envelope")
        check = check_events[0]
        if check["direction"] != "bob_local" or check["key_dependent_bits"] != 0 \
                or check["public_control_bits"] != 0 or set(check["payload"]) != {"value"} \
                or check["payload"]["value"] not in {"match", "mismatch"}:
            raise ValueError("v12 check envelope")
        if check["payload"]["value"] == "match" and row["status"] != "verified_success":
            raise ValueError("v12 terminal status")
        if check["payload"]["value"] == "mismatch" and row["status"] != "verify_failed":
            raise ValueError("v12 terminal status")
    elif any(e["event_type"] in {"VERIFICATION_SEED", "VERIFICATION_TAG", "FRAME_TAG_CHECK"}
             for e in events):
        raise ValueError("v12 verification invoked without flag")


def _gate(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    return {"denominator": len(rows),
            "verified_success": sum(r["status"] == "verified_success" for r in rows),
            "verify_failed": sum(r["status"] == "verify_failed" for r in rows),
            "decode_failed": sum(r["status"] == "decode_failed" for r in rows),
            "forbidden_failure_count": sum(r["status"] in _FORBIDDEN_STATUSES for r in rows),
            "passed": len(rows) == FRAME_COUNT
                      and not any(r["status"] in _FORBIDDEN_STATUSES for r in rows)
                      and any(r["status"] == "verified_success" for r in rows)}


def terminal_state(rows: list[Mapping[str, Any]]) -> str:
    """Frozen terminal states (design.md section 7).  ``source_partition_blocked``
    is a preparation-time state recorded before any plan exists; the three
    execution states are decided here from the retained outcome rows."""
    if len(rows) != FRAME_COUNT or any(not bool(r.get("denominator_included")) for r in rows):
        return "invalid_execution"
    if any(r.get("status") in _FORBIDDEN_STATUSES for r in rows):
        return "invalid_execution"
    if any(r.get("status") == "verified_success" for r in rows):
        return "observed_real_correction"
    return "failed_canary"


# ------------------------------------------------------------------ CSV (I04/I05)

def _csv_scalar(name: str, value: Any) -> str:
    if name in {"attempted", "denominator_included", "verification_invoked"}:
        if type(value) is not bool:
            raise ValueError("v12 CSV boolean")
        return "true" if value else "false"
    if name in {"raw_ser", "epsilon_ec", "runtime_s"}:
        if not isinstance(value, (float, int)) or isinstance(value, bool) \
                or not math.isfinite(float(value)) or (name == "runtime_s" and float(value) < 0):
            raise ValueError("v12 CSV float")
        return repr(float(value))
    if name in {"transcript_first_event_id", "transcript_last_event_id"}:
        if value is None:
            return ""
        if type(value) is not int:
            raise ValueError("v12 CSV optional int")
        return str(value)
    if isinstance(value, (dict, list, tuple)) or value is None:
        raise ValueError("v12 CSV scalar")
    return str(value)


def _validate_csv_prefix(row: Mapping[str, Any]) -> None:
    if row["role"] != ROLE or row["stratum"] != STRATUM:
        raise ValueError("v12 CSV prefix identity")
    if not isinstance(row["plan_frame_id"], str) or not row["plan_frame_id"].startswith(f"{STRATUM}|"):
        raise ValueError("v12 CSV prefix plan id")
    if not (_is_hex64(row["alice_sha256"]) and _is_hex64(row["bob_sha256"])
            and _is_hex64(row["transcript_bytes_sha256"])):
        raise ValueError("v12 CSV prefix hashes")
    if type(row["transcript_bytes_len"]) is not int or row["transcript_bytes_len"] < 0:
        raise ValueError("v12 CSV prefix transcript len")


def encode_outcome_csv_v12(rows: Any) -> bytes:
    if not isinstance(rows, (list, tuple)) or not rows:
        raise ValueError("v12 CSV rows")
    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS, lineterminator="\n", extrasaction="raise")
    writer.writeheader()
    for row in rows:
        if not isinstance(row, Mapping) or tuple(row) != CSV_FIELDS:
            raise ValueError("v12 CSV fields")
        validate_outcome_v12({key: row[key] for key in OUTCOME_FIELDS})
        _validate_csv_prefix(row)
        writer.writerow({key: _csv_scalar(key, row[key]) for key in CSV_FIELDS})
    raw = output.getvalue().encode("utf-8")
    if b"\r" in raw:
        raise ValueError("v12 CSV CR")
    return raw


def decode_outcome_csv_v12(raw: bytes) -> list[dict[str, Any]]:
    if not isinstance(raw, bytes) or b"\r" in raw:
        raise ValueError("v12 CSV bytes")
    if not raw:
        return []
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("v12 CSV utf8") from exc
    if not text.endswith("\n"):
        raise ValueError("v12 CSV LF")
    reader = csv.DictReader(StringIO(text, newline=""))
    if tuple(reader.fieldnames or ()) != CSV_FIELDS:
        raise ValueError("v12 CSV header")
    bool_fields = {"attempted", "denominator_included", "verification_invoked"}
    int_fields = {"frame_id", "dimension", "frame_len_symbols", "check_count", "iterations",
                  "verification_tag_bits", "key_dependent_disclosure_bits_total",
                  "public_control_bits_total", "transcript_bytes_len"}
    float_fields = {"raw_ser", "epsilon_ec", "runtime_s"}
    opt_int = {"transcript_first_event_id", "transcript_last_event_id"}
    rows: list[dict[str, Any]] = []
    for wire in reader:
        if set(wire) != set(CSV_FIELDS) or None in wire:
            raise ValueError("v12 CSV row")
        row: dict[str, Any] = {}
        for key, value in wire.items():
            if key in bool_fields:
                if value not in {"true", "false"}:
                    raise ValueError("v12 CSV bool")
                row[key] = value == "true"
            elif key in float_fields:
                try:
                    number = float(value)
                except ValueError as exc:
                    raise ValueError("v12 CSV float") from exc
                if not math.isfinite(number) or repr(number) != value:
                    raise ValueError("v12 CSV float canonical")
                row[key] = number
            elif key in int_fields:
                if not value or str(int(value)) != value:
                    raise ValueError("v12 CSV integer")
                row[key] = int(value)
            elif key in opt_int:
                if value == "":
                    row[key] = None
                elif str(int(value)) == value:
                    row[key] = int(value)
                else:
                    raise ValueError("v12 CSV optional integer")
            else:
                row[key] = value
        rows.append(row)
    if encode_outcome_csv_v12(rows) != raw:
        raise ValueError("v12 CSV roundtrip")
    return rows


# ------------------------------------------------------------------ plan (I05)

def _seed_schedule(records: list[Mapping[str, Any]], prior: set[str]) -> dict[str, Any]:
    ids = [record["seed_id"] for record in records]
    if len(ids) != len(set(ids)) or set(ids) & prior:
        raise ValueError("seed freshness")
    base = {"schema": SEED_SCHEDULE_SCHEMA, "seed_count": len(records),
            "records": records, "seed_ids_sha256": _sha(_compact(sorted(ids))),
            "prior_seed_id_count": len(prior),
            "prior_seed_ids_sha256": _sha(_compact(sorted(prior))),
            "disjoint_from_prior": True}
    return _self(base, "seed_schedule_sha256")


def _plan_base(exclusion: Mapping[str, Any], lock: Mapping[str, Any], out: Path) -> dict[str, Any]:
    """Shared plan content (route V12-R1 binding) used by both the ready and
    the ``source_partition_blocked`` plan shapes.  Identity-only: never holds
    Alice/Bob symbols or syndrome values."""
    cb, _ = reconstruct_v7_r1a()
    return {
        "method_id": METHOD, "role": ROLE,
        "domain": {"q": Q, "n": N, "m": M, "p": P, "mapping": "gray",
                   "stratum": STRATUM, "frame_len_symbols": N,
                   "frame_count": FRAME_COUNT, "syndrome_bits": SYNDROME_BITS},
        "output_binding": {"output_directory": out.resolve().relative_to(_root()).as_posix(),
                           "artifact_names": list(ARTIFACTS),
                           "prepare_file_set": list(PREPARE_ARTIFACTS)},
        "exclusion_binding": {"exclusion_sha256": exclusion["exclusion_sha256"],
                              "excluded_frame_identity_count": exclusion["excluded_frame_identity_count"],
                              "excluded_payload_identity_count": exclusion["excluded_payload_identity_count"]},
        "partition_binding": {"partition_sha256": lock["partition_sha256"],
                              "selected_row_digest": lock["selected_row_digest"],
                              "partition_state": lock["partition_state"]},
        "codebook_binding": {"method": V7_R1A_METHOD,
                             "manifest_id": cb["manifest_id"],
                             "canonical_sha256": cb["canonical_sha256"],
                             "q": Q, "n": N, "m": M,
                             "construction_seed": V7_R1A_FROZEN["construction_seed"],
                             "rank": cb["rank"], "edge_count": cb["edge_count"]},
        "caps": dict(CAPS), "gates": dict(GATES),
        "failure_policy": FAILURE_POLICY, "leakage": dict(LEAKAGE_CONTRACT),
        "provenance": _provenance(),
    }


def _build_plan(exclusion: Mapping[str, Any], lock: Mapping[str, Any], frames: list[Mapping[str, Any]],
                records: list[Mapping[str, Any]], out: Path, *, test_only: bool) -> dict[str, Any]:
    selected = lock["selected_rows"]
    attempt_ids = [f"{STRATUM}|{row['frame_id']}" for row in selected]
    prior = _prior_seed_ids()
    base = _plan_base(exclusion, lock, out)
    base["schema"] = TEST_PLAN_SCHEMA if test_only else PLAN_SCHEMA
    base["run_id"] = TEST_RUN_ID if test_only else RUN_ID
    base["plan_state"] = "ready"
    base["execution"] = {"order": "canonical_pool_order", "attempt_ids": attempt_ids,
                         "attempt_ids_sha256": _sha(_compact(attempt_ids))}
    base["frames"] = frames
    base["seed_schedule"] = _seed_schedule(records, prior)
    return _self(base, "plan_sha256")


def _build_blocked_plan(exclusion: Mapping[str, Any], lock: Mapping[str, Any], out: Path) -> dict[str, Any]:
    """No-decode production plan bound to a ``source_partition_blocked``
    partition: zero attempt ids, zero frames, zero seed records (no symbols,
    no syndromes, no Toeplitz seeds are ever emitted)."""
    prior = _prior_seed_ids()
    base = _plan_base(exclusion, lock, out)
    base["schema"] = PLAN_SCHEMA
    base["run_id"] = RUN_ID
    base["plan_state"] = "source_partition_blocked"
    base["execution"] = {"order": "canonical_pool_order", "attempt_ids": [],
                         "attempt_ids_sha256": _sha(_compact([]))}
    base["frames"] = []
    base["seed_schedule"] = _seed_schedule([], prior)
    return _self(base, "plan_sha256")


def _is_identity_only_frame(frame: Mapping[str, Any], row: Mapping[str, Any]) -> bool:
    """A plan frame either carries Alice/Bob arrays (fake test lanes only) or
    is identity-only (production plans must never hold symbols)."""
    required = {"stratum", "frame_id", "frame_identity", "payload_identity",
                "source_pair_start", "source_pair_end", "source_record_sha256"}
    if not required.issubset(set(frame)) or {"alice", "bob"} & set(frame):
        return False
    if not set(frame).issubset(required | {"role"}):
        return False
    return all(frame[key] == row[key] for key in required)


def _validate_plan_frame(frame: Mapping[str, Any], row: Mapping[str, Any]) -> None:
    if int(frame.get("frame_id")) != int(row["frame_id"]) \
            or frame.get("frame_identity") != row["frame_identity"] \
            or frame.get("payload_identity") != row["payload_identity"]:
        raise ValueError("plan frame binding")
    if {"alice", "bob"} & set(frame):
        _frame_array(frame)
    elif not _is_identity_only_frame(frame, row):
        raise ValueError("plan identity-only frame")


def _validate_plan(plan: Any, *, test_only: bool, output_dir: Any) -> dict[str, Any]:
    if not isinstance(plan, Mapping):
        raise ValueError("plan type")
    supplied = dict(plan)
    digest = supplied.pop("plan_sha256", None)
    if not _is_hex64(digest) or _sha(_compact(supplied)) != digest:
        raise ValueError("plan self hash")
    if plan.get("schema") != (TEST_PLAN_SCHEMA if test_only else PLAN_SCHEMA) \
            or plan.get("run_id") != (TEST_RUN_ID if test_only else RUN_ID) \
            or plan.get("method_id") != METHOD or plan.get("role") != ROLE:
        raise ValueError("plan identity")
    if plan.get("domain") != {"q": Q, "n": N, "m": M, "p": P, "mapping": "gray",
                              "stratum": STRATUM, "frame_len_symbols": N,
                              "frame_count": FRAME_COUNT, "syndrome_bits": SYNDROME_BITS}:
        raise ValueError("plan domain")
    out = Path(output_dir).resolve()
    expected_out = {"output_directory": out.relative_to(_root()).as_posix(),
                    "artifact_names": list(ARTIFACTS),
                    "prepare_file_set": list(PREPARE_ARTIFACTS)}
    if plan.get("output_binding") != expected_out:
        raise ValueError("plan output binding")
    exclusion = partition.validate_exclusion_manifest(_json_read(out / "exclusion_manifest.json"))
    lock = partition.validate_partition_lock(_json_read(out / "partition_lock.json"), exclusion)
    if plan.get("exclusion_binding") != {"exclusion_sha256": exclusion["exclusion_sha256"],
                                         "excluded_frame_identity_count": exclusion["excluded_frame_identity_count"],
                                         "excluded_payload_identity_count": exclusion["excluded_payload_identity_count"]}:
        raise ValueError("plan exclusion binding")
    if plan.get("partition_binding") != {"partition_sha256": lock["partition_sha256"],
                                         "selected_row_digest": lock["selected_row_digest"],
                                         "partition_state": lock["partition_state"]}:
        raise ValueError("plan partition binding")
    if lock["partition_state"] == "ready":
        _validate_ready_plan(plan, lock, out)
    else:
        if plan.get("plan_state") != "source_partition_blocked":
            raise ValueError("plan blocked state")
        if plan.get("frames") != []:
            raise ValueError("plan blocked frames")
        if plan.get("execution") != {"order": "canonical_pool_order", "attempt_ids": [],
                                     "attempt_ids_sha256": _sha(_compact([]))}:
            raise ValueError("plan blocked execution")
        records = plan.get("seed_schedule", {}).get("records")
        if records != []:
            raise ValueError("plan blocked seeds")
        prior = _prior_seed_ids()
        if plan.get("seed_schedule") != _seed_schedule([], prior):
            raise ValueError("plan seed schedule")
    if plan.get("caps") != dict(CAPS) or plan.get("gates") != dict(GATES):
        raise ValueError("plan caps/gates")
    if plan.get("failure_policy") != FAILURE_POLICY or plan.get("leakage") != dict(LEAKAGE_CONTRACT):
        raise ValueError("plan policy")
    return dict(plan)


def _validate_ready_plan(plan: Mapping[str, Any], lock: Mapping[str, Any], out: Path) -> None:
    """Ready-partition plan content: four bound frames (array-bearing in fake
    test lanes, identity-only in production plans) and four unique fresh seed
    records."""
    if plan.get("plan_state") != "ready":
        raise ValueError("plan ready state")
    selected = lock["selected_rows"]
    frames = plan.get("frames")
    if not isinstance(frames, list) or len(frames) != FRAME_COUNT or len(selected) != FRAME_COUNT:
        raise ValueError("plan frames")
    for frame, row in zip(frames, selected):
        _validate_plan_frame(frame, row)
    attempt_ids = [f"{STRATUM}|{row['frame_id']}" for row in selected]
    if plan.get("execution") != {"order": "canonical_pool_order", "attempt_ids": attempt_ids,
                                 "attempt_ids_sha256": _sha(_compact(attempt_ids))}:
        raise ValueError("plan execution")
    schedule = plan.get("seed_schedule")
    records = schedule.get("records")
    if not isinstance(records, list) or len(records) != FRAME_COUNT:
        raise ValueError("plan seeds")
    ids = [record["seed_id"] for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError("plan seed uniqueness")
    for record in records:
        if not isinstance(record, Mapping) or set(record) != {"seed_hex", "seed_bit_length", "seed_id"} \
                or record["seed_bit_length"] != SEED_BITS:
            raise ValueError("plan seed record contract")
        locked_seed_bits(record, SEED_BITS)
    prior = _prior_seed_ids(exclude=out / "pre_run_plan.json")
    if set(ids) & prior:
        raise ValueError("plan seed freshness")
    if schedule != _seed_schedule(records, prior):
        raise ValueError("plan seed schedule")
    cb, _ = reconstruct_v7_r1a()
    if plan.get("codebook_binding") != {"method": V7_R1A_METHOD,
                                        "manifest_id": cb["manifest_id"],
                                        "canonical_sha256": cb["canonical_sha256"],
                                        "q": Q, "n": N, "m": M,
                                        "construction_seed": V7_R1A_FROZEN["construction_seed"],
                                        "rank": cb["rank"], "edge_count": cb["edge_count"]}:
        raise ValueError("plan codebook binding")


def create_plan(output_dir: Any, *, frames: Any = None, seeds: Any = None, _test_only: bool = False,
                production_prepare_authorized: bool = False) -> dict[str, Any]:
    """Prepare ``pre_run_plan.json`` after the exclusion inventory and
    partition lock are in place (decoder-free, identity-only).

    Two plan lanes exist: the fake test lane (``_test_only=True``) and the
    prepare-only production lane (``production_prepare_authorized=True``,
    main-thread authorized for V12-RP03).  A ``source_partition_blocked``
    partition yields a blocked plan with zero frames and zero seed records;
    a ready partition yields the full four-frame plan with four unique fresh
    seed records and identity-only frames (never symbols).
    """
    if not _test_only and not production_prepare_authorized:
        raise ValueError("V12 production plan preparation is not authorized during the initial phase")
    out = Path(output_dir).resolve()
    if not out.is_dir() or {x.name for x in out.iterdir()} != set(PREPARE_ARTIFACTS[:2]):
        raise ValueError("plan requires exclusion+partition only directory")
    exclusion = partition.validate_exclusion_manifest(_json_read(out / "exclusion_manifest.json"))
    lock = partition.validate_partition_lock(_json_read(out / "partition_lock.json"), exclusion)
    if lock.get("partition_state") != "ready":
        if _test_only or frames or seeds:
            raise ValueError("source_partition_blocked")
        plan = _build_blocked_plan(exclusion, lock, out)
        _validate_plan(plan, test_only=False, output_dir=out)
        _put(out / "pre_run_plan.json", plan)
        return plan
    if not isinstance(frames, list) or len(frames) != FRAME_COUNT:
        raise ValueError("plan frame count")
    if not isinstance(seeds, Mapping) or set(seeds) != {f["frame_id"] for f in frames}:
        raise ValueError("plan seed binding")
    selected = lock["selected_rows"]
    for frame, row in zip(frames, selected):
        _validate_plan_frame(frame, row)
    records = [seeds[f["frame_id"]] for f in frames]
    for record in records:
        if not isinstance(record, Mapping) or set(record) != {"seed_hex", "seed_bit_length", "seed_id"}:
            raise ValueError("plan seed record contract")
        locked_seed_bits(record, SEED_BITS)
    plan = _build_plan(exclusion, lock, frames, records, out, test_only=_test_only)
    _validate_plan(plan, test_only=_test_only, output_dir=out)
    _put(out / "pre_run_plan.json", plan)
    return plan


# ------------------------------------------------------------------ execute (I05)

def _csv_row(frame: Mapping[str, Any], row: Mapping[str, Any], events: list[Mapping[str, Any]]) -> dict[str, Any]:
    transcript = b"".join(canonical_event(event) for event in events)
    prefix = {"role": ROLE, "stratum": STRATUM,
              "plan_frame_id": f"{STRATUM}|{frame['frame_id']}",
              "alice_sha256": _array_sha(frame["alice"]), "bob_sha256": _array_sha(frame["bob"]),
              "transcript_bytes_len": len(transcript),
              "transcript_bytes_sha256": _sha(transcript)}
    return {**prefix, **dict(row)}


def _finalize(out: Path, plan: Mapping[str, Any], csv_rows: list[dict[str, Any]],
              events: list[Mapping[str, Any]], status: str, reason: str, *, test_only: bool) -> None:
    """Execute finalizes the other four artifacts, even on a retained invalid
    partial run when possible (design.md section 6).  No-overwrite only."""
    if not (out / "real_frame_outcomes.csv").exists():
        _write(out / "real_frame_outcomes.csv", encode_outcome_csv_v12(csv_rows) if csv_rows else b"")
    if not (out / "real_transcript.jsonl").exists():
        _write(out / "real_transcript.jsonl", b"".join(canonical_event(event) for event in events))
    index = {name: {"sha256": _sha((out / name).read_bytes()), "bytes": (out / name).stat().st_size}
             for name in ("real_frame_outcomes.csv", "real_transcript.jsonl")}
    rows = [dict(row) for row in csv_rows]
    term = terminal_state(rows) if status == "completed" else "invalid_execution"
    run_status = "completed" if status == "completed" and term != "invalid_execution" else "invalid_execution"
    manifest = _self({"schema": TEST_RUN_MANIFEST_SCHEMA if test_only else RUN_MANIFEST_SCHEMA,
                      "run_id": TEST_RUN_ID if test_only else RUN_ID,
                      "run_status": run_status, "stop_reason": reason,
                      "terminal_state": term, "plan_sha256": plan["plan_sha256"],
                      "outcome_count": len(rows), "artifact_file_sha256": index,
                      "decoder_reexecution": False}, "run_manifest_sha256")
    if not (out / "real_run_manifest.json").exists():
        _put(out / "real_run_manifest.json", manifest)
    report = _self({"schema": TEST_REPORT_SCHEMA if test_only else REPORT_SCHEMA,
                    "run_id": TEST_RUN_ID if test_only else RUN_ID,
                    "run_status": run_status, "stop_reason": reason,
                    "terminal_state": term, "plan_sha256": plan["plan_sha256"],
                    "run_manifest_sha256": manifest["run_manifest_sha256"],
                    "gate": _gate(rows), "decoder_reexecution": False}, "report_sha256")
    if not (out / "real_micro_report.json").exists():
        _put(out / "real_micro_report.json", report)


def run(output_dir: Any = None, *, runner: Callable[..., Any] | None = None,
        _test_only: bool = False, fatal_hook: Callable[[int], None] | None = None,
        _clock: Callable[[], float] = time.monotonic) -> dict[str, Any]:
    """Execute the frozen four-frame canary exactly once.

    Production execution is a hard stop in the initially authorized phase.
    Test-only execution requires an explicit fake runner and a fresh writable
    test root; a run without an explicit runner can never fall back to the
    production decoder.  A retained invalid partial run finalizes the package
    and re-raises (no rerun, no resume, no replacement)."""
    if not _test_only:
        raise ValueError("V12 production execution is not authorized during the initial phase")
    if runner is None:
        raise ValueError("test-only execution requires an explicit fake runner")
    out = Path(output_dir).resolve()
    if {x.name for x in out.iterdir()} != set(PREPARE_ARTIFACTS):
        raise ValueError("run requires plan-only directory (exclusion_manifest, partition_lock, pre_run_plan)")
    plan = _validate_plan(_json_read(out / "pre_run_plan.json"), test_only=True, output_dir=out)
    exclusion = partition.validate_exclusion_manifest(_json_read(out / "exclusion_manifest.json"))
    lock = partition.validate_partition_lock(_json_read(out / "partition_lock.json"), exclusion)
    if lock.get("partition_state") != "ready":
        raise ValueError("source_partition_blocked")
    state: dict[str, Any] = {"rows": [], "events": []}
    try:
        cb, mats = reconstruct_v7_r1a()
        verify_v7_r1a_binding()
        field = GF2mField.create(Q)
        event_id = 1
        for frame in plan["frames"]:
            record = plan["seed_schedule"]["records"][plan["frames"].index(frame)]
            row, events, _ = _frame_result(frame, record, runner, cb, mats, field, event_id,
                                           _clock=_clock)
            state["rows"].append(_csv_row(frame, row, events))
            state["events"] += events
            event_id += len(events)
            if fatal_hook is not None:
                fatal_hook(len(state["rows"]))
        _finalize(out, plan, state["rows"], state["events"], "completed", "", test_only=True)
        rows = [dict(r) for r in state["rows"]]
        term = terminal_state(rows)
        return {"run_status": "completed" if term != "invalid_execution" else "invalid_execution",
                "terminal_state": term, "outcome_count": len(rows)}
    except Exception as exc:
        _finalize(out, plan, state["rows"], state["events"], "invalid_execution",
                  f"{type(exc).__name__}: {exc}", test_only=True)
        raise


# ------------------------------------------------------------------ read-only verify (I05)

def _verify_frame_public(frame: Mapping[str, Any], record: Mapping[str, Any], row: Mapping[str, Any],
                         events: list[Mapping[str, Any]], mats: Any, field: GF2mField) -> None:
    """Decoder-free per-frame reconstruction: public syndrome from Alice,
    Toeplitz tag from Alice + locked seed, leakage and terminal status.  The
    decoded word is never reconstructed and no decoder is imported or called."""
    alice, _ = _frame_array(frame)
    expected_syndrome = nonbinary_syndrome(mats, alice, field)
    syndrome_events = [e for e in events if e["event_type"] == "SYNDROME"]
    if len(syndrome_events) != 1 \
            or list(syndrome_events[0]["payload"]["syndrome"]) != list(expected_syndrome):
        raise ValueError("v12 public syndrome")
    if row["verification_invoked"]:
        seed_events = [e for e in events if e["event_type"] == "VERIFICATION_SEED"]
        tag_events = [e for e in events if e["event_type"] == "VERIFICATION_TAG"]
        check_events = [e for e in events if e["event_type"] == "FRAME_TAG_CHECK"]
        if len(seed_events) != 1 or len(tag_events) != 1 or len(check_events) != 1:
            raise ValueError("v12 verification events")
        if seed_events[0]["payload"]["seed_id"] != record["seed_id"]:
            raise ValueError("v12 public seed identity")
        seed_bits = locked_seed_bits(record, SEED_BITS)
        expected_tag = toeplitz_tag(symbols_to_msb_bits(alice, Q), seed_bits)
        if tag_events[0]["payload"]["tag"] != expected_tag.hex():
            raise ValueError("v12 public tag")
        check_value = check_events[0]["payload"]["value"]
        if check_value == "match" and row["status"] != "verified_success":
            raise ValueError("v12 public terminal status")
        if check_value == "mismatch" and row["status"] != "verify_failed":
            raise ValueError("v12 public terminal status")
    else:
        if any(e["event_type"] in {"VERIFICATION_SEED", "VERIFICATION_TAG", "FRAME_TAG_CHECK"}
               for e in events):
            raise ValueError("v12 uninvoked verification")
        if row["status"] not in {"decode_failed"} | set(_FORBIDDEN_STATUSES):
            raise ValueError("v12 non-verification status")


def verify(output_dir: Any = None, *, _test_only: bool = False) -> dict[str, Any]:
    """Strict read-only verification.  Reconstructs every identity, event,
    leakage field, gate and terminal state from the reviewed source and the
    transcript.  The verifier never imports or calls a decoder; production
    verification is a hard stop in the initially authorized phase."""
    out = Path(output_dir).resolve()
    if not out.is_dir():
        raise ValueError("output directory missing")
    names = {x.name for x in out.iterdir()}
    if names == set(PREPARE_ARTIFACTS):
        plan = _validate_plan(_json_read(out / "pre_run_plan.json"), test_only=_test_only, output_dir=out)
        ts = plan["partition_binding"]["partition_state"]
        return {"verified": True, "plan_only": True, "run_status": "planned",
                "terminal_state": None if ts == "ready" else ts,
                "decoder_reexecution": False}
    if names != set(ARTIFACTS):
        raise ValueError("seven-artifact contract")
    if not _test_only:
        raise ValueError("V12 production verification is not authorized during the initial phase")
    before = {name: _sha((out / name).read_bytes()) for name in ARTIFACTS}
    exclusion = partition.validate_exclusion_manifest(_json_read(out / "exclusion_manifest.json"))
    lock = partition.validate_partition_lock(_json_read(out / "partition_lock.json"), exclusion)
    plan = _validate_plan(_json_read(out / "pre_run_plan.json"), test_only=True, output_dir=out)
    cb, mats = reconstruct_v7_r1a()
    field = GF2mField.create(Q)
    rows = decode_outcome_csv_v12((out / "real_frame_outcomes.csv").read_bytes())
    manifest = _json_read(out / "real_run_manifest.json")
    if len(rows) != int(manifest["outcome_count"]) or len(rows) > FRAME_COUNT:
        raise ValueError("v12 outcome accounting")
    attempt_ids = plan["execution"]["attempt_ids"]
    # A retained invalid partial run keeps a prefix of the denominator; a
    # completed run has the full denominator in the frozen order.
    if [r["plan_frame_id"] for r in rows] != attempt_ids[:len(rows)]:
        raise ValueError("v12 execution order")
    transcript = (out / "real_transcript.jsonl").read_bytes()
    if b"".join(canonical_event(event) for event in
                (json.loads(line) for line in transcript.splitlines())) != transcript:
        raise ValueError("v12 transcript canonicalization")
    cursor = 0
    for row, frame, record in zip(rows, plan["frames"], plan["seed_schedule"]["records"]):
        raw_slice = transcript[cursor:cursor + int(row["transcript_bytes_len"])]
        cursor += int(row["transcript_bytes_len"])
        events_row = [json.loads(line) for line in raw_slice.splitlines()] if raw_slice else []
        formal = {key: row[key] for key in OUTCOME_FIELDS}
        validate_outcome_v12(formal, events_row)
        _verify_frame_public(frame, record, formal, events_row, mats, field)
        if _sha(raw_slice) != row["transcript_bytes_sha256"] or _sha(raw_slice) != formal["transcript_sha256"]:
            raise ValueError("v12 transcript slice hash")
        if _array_sha(frame["alice"]) != row["alice_sha256"] or _array_sha(frame["bob"]) != row["bob_sha256"]:
            raise ValueError("v12 array hash")
    if cursor != len(transcript):
        raise ValueError("v12 orphan transcript events")
    rows_formal = [{key: row[key] for key in OUTCOME_FIELDS} for row in rows]
    term = terminal_state(rows_formal)
    gate = _gate(rows_formal)
    report = _json_read(out / "real_micro_report.json")
    expected_run_status = "invalid_execution" if term == "invalid_execution" else "completed"
    if manifest.get("run_status") != expected_run_status:
        raise ValueError("v12 manifest run status")
    expected_manifest = _self({k: v for k, v in manifest.items() if k != "run_manifest_sha256"},
                              "run_manifest_sha256")
    if manifest != expected_manifest:
        raise ValueError("v12 manifest hash")
    index = {name: {"sha256": _sha((out / name).read_bytes()), "bytes": (out / name).stat().st_size}
             for name in ("real_frame_outcomes.csv", "real_transcript.jsonl")}
    if manifest.get("plan_sha256") != plan["plan_sha256"] or manifest.get("outcome_count") != len(rows) \
            or manifest.get("decoder_reexecution") is not False \
            or manifest.get("terminal_state") != term or manifest.get("artifact_file_sha256") != index:
        raise ValueError("v12 manifest fields")
    expected_report = _self({"schema": TEST_REPORT_SCHEMA if _test_only else REPORT_SCHEMA,
                             "run_id": manifest["run_id"], "run_status": manifest["run_status"],
                             "stop_reason": manifest.get("stop_reason"), "terminal_state": term,
                             "plan_sha256": plan["plan_sha256"],
                             "run_manifest_sha256": manifest["run_manifest_sha256"],
                             "gate": gate, "decoder_reexecution": False}, "report_sha256")
    if report != expected_report:
        raise ValueError("v12 report reconstruction")
    after = {name: _sha((out / name).read_bytes()) for name in ARTIFACTS}
    if before != after:
        raise ValueError("v12 artifact immutability")
    return {"verified": True, "run_status": manifest["run_status"], "terminal_state": term,
            "outcomes": len(rows), "decoder_reexecution": False}


# ------------------------------------------------------------------ production prepare (RP01-RP03)

def prepare_production(output_dir: Any, *, discovery_roots: Any, pool_rows: Any = None) -> dict[str, Any]:
    """Main-thread-authorized prepare-only production path (V12-RP01..RP03):
    exclusion inventory -> partition lock -> pre-run plan into one fresh
    additive package directory.

    Decoder-free and array-free: reads only manifests and identity rows,
    never loads Alice/Bob arrays and never imports or calls a decoder.  Writes
    exactly the three preparation artifacts; decode/execute remain hard stops
    elsewhere.
    """
    out = Path(output_dir)
    if out.exists():
        raise FileExistsError("fresh output directory required")
    roots = list(discovery_roots)
    pool = list(pool_rows) if pool_rows is not None else partition.build_traceable_pool(roots[0])
    prepared = partition.prepare(out, production_prepare_authorized=True,
                                 discovery_root=roots, pool_rows=pool,
                                 run_id=RUN_ID, source_adapter=partition.SOURCE_ADAPTER,
                                 canonical_rule=partition.CANONICAL_RULE)
    exclusion = partition.validate_exclusion_manifest(_json_read(out / "exclusion_manifest.json"))
    lock = partition.validate_partition_lock(_json_read(out / "partition_lock.json"), exclusion)
    if lock["partition_state"] == "ready":
        frames = [dict(row) for row in lock["selected_rows"]]
        seeds = {f["frame_id"]: materialize_seed_record(SEED_BITS) for f in frames}
        plan = create_plan(out, frames=frames, seeds=seeds, production_prepare_authorized=True)
    else:
        plan = create_plan(out, production_prepare_authorized=True)
    names = {p.name for p in out.iterdir()}
    if names != set(PREPARE_ARTIFACTS):
        raise ValueError("prepare artifact set")
    return {"package_dir": out.resolve().relative_to(_root()).as_posix(),
            "partition_state": lock["partition_state"],
            "plan_state": plan.get("plan_state"),
            "exclusion_sha256": exclusion["exclusion_sha256"],
            "partition_sha256": lock["partition_sha256"],
            "plan_sha256": plan["plan_sha256"],
            "artifacts": sorted(names)}
