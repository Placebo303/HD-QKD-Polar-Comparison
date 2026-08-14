"""V13 existing-data nonbinary LDPC diagnostics — D01 channel characterization,
D02 engineering oracle, D03 telemetry hook equivalence and the V13 role ledger
(``formal-nonbinary-ldpc-v13-existing-data-diagnostics``).

Phase-D engineering scope authorized 2026-08-14 (main thread): D01 (no-decode
channel characterization; aggregate statistics only, raw arrays never
persisted or sent), D02 (test-only engineering oracle), D03 (optional V7 R1A
telemetry hook with strict hook-off/hook-on equivalence), the V13-DT0/DT1/
DT2 diagnostic engineering tests, and — by the 2026-08-14 follow-up main-thread
authorization — D04 (the frozen 32-frame bw200 development baseline probe,
unchanged V7 R1A ``p=.20``, executed exactly once).  D05 (root-cause report),
any R/I/E/A/C task and any decoder execution beyond the 32 pre-registered D04
baseline frames remain unauthorized.

Module boundaries (frozen by the V13 design):

- The module imports **no decoder at import time**: ``nonbinary_v7_r1a_long``
  is imported lazily only inside :func:`run_diagnostic_hook`, and the real
  10 dB source adapter is imported lazily only inside
  :func:`load_production_characterization_frames`.  The read-only verifier
  therefore never imports or calls a decoder.
- Alice truth is allowed only for offline aggregate channel statistics and
  post-hoc exact-equality checks; it never enters a decoder prior, stopping
  rule, candidate selection, retry, frame ordering, or telemetry record.
- The D03 hook is a wrapper/adapter over the frozen V7 R1A decoder; the frozen
  V7 sources are never modified.  Hook-off returns the original decoder result
  element-for-element; hook-on must not change decoded word, status or
  iterations, and persists only aggregate/internal traces (never Alice error
  locations or raw arrays).
- Every artifact is labelled ``diagnostic_only`` / ``retrospective_reuse``.
  ``run_state`` is restricted to the declared V13 set; ``diagnosis_class`` is
  recorded separately and never substitutes for it.  ``promoted``,
  ``qualified`` and ``observed_fresh_correction`` are forbidden.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
import subprocess
import uuid
from collections import Counter
from functools import lru_cache
from io import StringIO
from itertools import product
from numbers import Integral
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from .nonbinary_field import GF2mField
from .nonbinary_qspa import (_declared_dense_bytes, _fwht, _normalise, _result,
                             _symbols, nonbinary_syndrome, qsc_symbol_priors)
from . import nonbinary_v7_r1a_codebook as v7_cb
from ..utils.bitops import frame_symbol_error_rate, gray_encode, symbols_to_bits

METHOD = "nbldpc_v13_diagnostics"
Q, N, M = 1024, 256, 170
P = 0.20
PRIMARY_STRATUM = "d1024_bw200"
D04_FRAME_COUNT = 32
D04_PHASE = "baseline"
STRATA = ("d1024_bw120", "d1024_bw180", "d1024_bw200")
ROLES = ("characterization", "development", "retrospective_audit")
BIT_PLANES = 10
MAX_ITER = 100

# The only V13 run_state values (design.md section 6 / spec.md).
RUN_STATES = ("plan_only", "blocked_role_ledger", "implementation_interface_fault",
              "diagnosis_complete", "diagnosis_inconclusive",
              "failed_existing_data_feasibility", "retrospective_non_ready",
              "ready_for_fresh_confirmation", "invalid_diagnostic_execution")
# The only V13 diagnosis_class values; never substituted for a run_state.
DIAGNOSIS_CLASSES = ("interface", "prior", "decoder", "code", "mixed", "inconclusive")

# The six-file additive package contract (design.md section 7).
ARTIFACTS = ("data_role_ledger.json", "channel_diagnostics.json",
             "diagnostic_outcomes.csv", "decoder_telemetry.jsonl",
             "root_cause_report.json", "diagnostic_run_manifest.json")

LEDGER_SCHEMA = "nbldpc_v13_data_role_ledger_v1"
LEDGER_SCHEMA_TEST = "nbldpc_v13_data_role_ledger_test_v1"
CHANNEL_SCHEMA = "nbldpc_v13_channel_diagnostics_v1"
CHANNEL_SCHEMA_TEST = "nbldpc_v13_channel_diagnostics_test_v1"
TELEMETRY_SCHEMA = "nbldpc_v13_decoder_telemetry_v1"
TELEMETRY_SCHEMA_TEST = "nbldpc_v13_decoder_telemetry_test_v1"
REPORT_SCHEMA = "nbldpc_v13_root_cause_report_v1"
REPORT_SCHEMA_TEST = "nbldpc_v13_root_cause_report_test_v1"
MANIFEST_SCHEMA = "nbldpc_v13_diagnostic_run_manifest_v1"
MANIFEST_SCHEMA_TEST = "nbldpc_v13_diagnostic_run_manifest_test_v1"

OUTCOME_COLUMNS = ("phase", "method", "frame_id", "stratum", "role", "status",
                   "reason", "raw_ser", "iterations", "notes")
V13_PHASES = ("d01", "baseline", "candidate_development", "retrospective_audit")

# Frozen V7 R1A binding (recorded in the V12 memory and reproduced from the
# deterministic codebook reconstruction; never re-searched at runtime).
V7_R1A_METHOD = "nbldpc_formal_v7_r1a_mr0"
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

# Identity-bearing lock file schemas used to reconstruct the traceable 10 dB
# pool (mirrors the V12 partition module; array-free, decoder-free).
_10DB_LOCK_SCHEMAS = {
    "real_data_lock.json": "binary_ldpc_v4_10db_source_lock_v1",
    "partition_lock.json": "binary_ldpc_v5_10db_partition_lock_v1",
}
_ROLE_FIELDS = ("stratum", "frame_id", "frame_identity", "payload_identity",
                "source_pair_start", "source_pair_end", "source_record_sha256")

# Telemetry records may only carry these scalar keys (D03 contract).
_TELEMETRY_PER_ITERATION_KEYS = frozenset({
    "iteration", "normalisation_calls", "normalisation_failures",
    "nonfinite_events", "underflow_events", "satisfied_checks",
    "unsatisfied_checks", "syndrome_consistent", "mean_posterior_max",
    "mean_posterior_entropy_bits", "decoded_changed", "stagnation"})
_TELEMETRY_FORBIDDEN_KEYS = frozenset({"alice", "bob", "alice_symbols",
    "bob_symbols", "error_positions", "error_mask", "mask", "raw_arrays",
    "decoded_symbols", "decoded_word"})


def _compact(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def _sha(value: Any) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else _compact(value)).hexdigest()


def _is_hex64(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 \
        and all(c in "0123456789abcdef" for c in value)


def _test_schema(doc: Mapping[str, Any]) -> bool:
    """True for the *_test_v1 schema variants used by the fake test lanes."""
    return bool(str(doc.get("schema", "")).endswith("_test_v1"))


def _put(path: Path, value: Any) -> None:
    path.open("xb").write(_compact(value))


def _write_bytes(path: Path, value: bytes) -> None:
    path.open("xb").write(value)


def _json_read(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    doc = json.loads(raw)
    if not isinstance(doc, dict) or _compact(doc) != raw:
        raise ValueError("noncanonical json")
    return doc


def _root() -> Path:
    return Path(__file__).resolve().parents[4]


def _provenance() -> dict[str, Any]:
    root = _root()
    try:
        commit = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"],
                                         text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.SubprocessError):
        commit = "unavailable"
    return {"python": platform.python_version(), "numpy": np.__version__,
            "platform": platform.platform(), "git_commit": commit}


# ------------------------------------------------------------------ role ledger

def _identity_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and normalize one identity-bearing pool/lock row (no arrays)."""
    missing = set(_ROLE_FIELDS).difference(row)
    if missing:
        raise ValueError(f"identity row missing fields: {sorted(missing)}")
    if row["stratum"] not in STRATA:
        raise ValueError("identity row stratum")
    if isinstance(row["frame_id"], bool) or not isinstance(row["frame_id"], Integral) \
            or int(row["frame_id"]) < 0:
        raise ValueError("identity row frame id")
    if not (_is_hex64(row.get("frame_identity")) and _is_hex64(row.get("payload_identity"))):
        raise ValueError("identity row identities")
    start, end = row.get("source_pair_start"), row.get("source_pair_end")
    if isinstance(start, bool) or isinstance(end, bool) or not isinstance(start, Integral) \
            or not isinstance(end, Integral) or int(start) < 0 or int(end) - int(start) != N:
        raise ValueError("identity row pair bounds")
    if not isinstance(row.get("source_record_sha256"), str) \
            or not _is_hex64(row.get("source_record_sha256")):
        raise ValueError("identity row source record")
    return {key: (int(row["frame_id"]) if key == "frame_id" else row[key])
            for key in _ROLE_FIELDS}


def scan_identity_locks(discovery_root: Any) -> dict[str, Any]:
    """Decoder-free, array-free identity scan of the locally discoverable 10 dB
    lock files (V4 v1/v2 transfer locks + V5 partition lock), mirroring the
    V12 traceable-pool semantics.  Returns the pool rows, the V4 transfer
    rows, the V5 partition rows and the identity-source records.

    Only identity rows are read; no sidecar arrays and no source adapter are
    touched.  Raises on an identity-less real lock or a missing discovery
    root, and skips lock files of other acquisitions (e.g. the 16 dB lock).
    """
    root = Path(discovery_root)
    if not root.is_dir():
        raise ValueError("discovery root missing")
    pool: list[dict[str, Any]] = []
    transfer: list[dict[str, Any]] = []
    partition: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        for name, schema in _10DB_LOCK_SCHEMAS.items():
            path = d / name
            if not path.is_file():
                continue
            try:
                doc = json.loads(path.read_bytes())
            except (OSError, ValueError):
                continue
            if not isinstance(doc, Mapping) or doc.get("schema") != schema:
                continue
            entries = doc.get("selected_frames") if name == "real_data_lock.json" \
                else doc.get("role_rows")
            if not isinstance(entries, list) or not entries:
                raise ValueError(f"identity-less lock: {path}")
            source = {"name": d.name, "lock_file": name, "path": str(path.resolve()),
                      "schema": schema, "row_count": len(entries)}
            sources.append(source)
            for entry in entries:
                if not isinstance(entry, Mapping):
                    continue
                try:
                    row = _identity_row(entry)
                except ValueError:
                    continue
                key = (row["frame_identity"], row["payload_identity"])
                if key in seen:
                    continue
                seen.add(key)
                pool.append(row)
                if name == "real_data_lock.json":
                    transfer.append(dict(row))
                else:
                    partition.append(dict(row, role=entry.get("role"),
                                          partition_rank=entry.get("partition_rank")))
    if not pool:
        raise ValueError("no identity rows discovered")
    return {"pool_rows": pool, "transfer_rows": transfer, "partition_rows": partition,
            "identity_sources": sources}


def build_role_ledger(pool_rows: Any, transfer_rows: Any, partition_rows: Any, *,
                      schema: str, run_id: str,
                      identity_sources: Any = None) -> dict[str, Any]:
    """Reconstruct the mutually exclusive characterization / development /
    retrospective_audit role ledger for the traceable 10 dB pool.

    Roles (frozen preference, design.md P04):
    - ``characterization``: rows covered by the V4 10 dB transfer locks, used
      only for aggregate channel statistics;
    - ``retrospective_audit``: the 128 sealed V5 confirmation frames per
      stratum (partition ranks 0..127);
    - ``development``: the V5 development partition (ranks 128..639, 512 per
      stratum).

    Every pool row must be assignable to exactly one role; a row that matches
    zero or more than one identity source, or a transfer/partition row that is
    not present in the pool, sets ``ledger_state=blocked_role_ledger`` and no
    D01 characterization is allowed.
    """
    pool = [_identity_row(x) for x in pool_rows]
    transfers = [_identity_row(x) for x in transfer_rows]
    parts = [_identity_row(x) for x in partition_rows]
    pool_ids = {(r["frame_identity"], r["payload_identity"]) for r in pool}
    transfer_ids = {(r["frame_identity"], r["payload_identity"]) for r in transfers}
    part_ids = {(r["frame_identity"], r["payload_identity"]) for r in parts}
    conf_ids = {r["frame_identity"] for r in partition_rows
                if isinstance(r, Mapping) and r.get("role") == "confirmation"}
    dev_ids = {r["frame_identity"] for r in partition_rows
               if isinstance(r, Mapping) and r.get("role") == "development"}

    blocked = False
    reasons: list[str] = []
    if not transfer_ids or not part_ids:
        blocked, reasons = True, reasons + ["empty identity source set"]
    if transfer_ids & part_ids:
        blocked, reasons = True, reasons + ["v4 transfer and v5 partition overlap"]
    if not transfer_ids.issubset(pool_ids) or not part_ids.issubset(pool_ids):
        blocked, reasons = True, reasons + ["identity source not traceable to pool"]
    if any(r["frame_identity"] in conf_ids and r["frame_identity"] in dev_ids
           for r in partition_rows if isinstance(r, Mapping)):
        blocked, reasons = True, reasons + ["ambiguous v5 confirmation/development role"]
    if not blocked:
        for row in pool:
            matches = ((row["frame_identity"], row["payload_identity"]) in transfer_ids,
                       row["frame_identity"] in conf_ids,
                       row["frame_identity"] in dev_ids)
            if sum(matches) != 1:
                blocked, reasons = True, reasons + ["ambiguous or unassigned pool row"]

    sources = list(identity_sources) if identity_sources is not None else []
    rows: list[dict[str, Any]] = []
    if not blocked:
        transfer_paths = [str(s["path"]) for s in sources if s.get("lock_file") == "real_data_lock.json"]
        partition_paths = [str(s["path"]) for s in sources if s.get("lock_file") == "partition_lock.json"]
        for row in pool:
            if (row["frame_identity"], row["payload_identity"]) in transfer_ids:
                role, role_source = "characterization", "v4_10db_transfer_lock"
                source_path = transfer_paths[0] if transfer_paths else ""
            elif row["frame_identity"] in conf_ids:
                role, role_source = "retrospective_audit", "v5_partition_confirmation"
                source_path = partition_paths[0] if partition_paths else ""
            else:
                role, role_source = "development", "v5_partition_development"
                source_path = partition_paths[0] if partition_paths else ""
            rows.append({"stratum": row["stratum"], "frame_id": row["frame_id"],
                         "frame_identity": row["frame_identity"],
                         "payload_identity": row["payload_identity"],
                         "role": role, "source_path": source_path,
                         "provenance": {"role_source": role_source,
                                        "identity_source_paths": [str(s["path"]) for s in sources],
                                        "source_pair_start": row["source_pair_start"],
                                        "source_pair_end": row["source_pair_end"],
                                        "source_record_sha256": row["source_record_sha256"]}})
    by_role: dict[str, int] = Counter(r["role"] for r in rows)
    by_stratum_role = {st: {role: sum(1 for r in rows if r["stratum"] == st and r["role"] == role)
                            for role in ROLES} for st in STRATA}
    unique_frames = {r["frame_identity"] for r in rows}
    ledger_state = "ready" if not blocked and len(rows) == len(pool) \
        and len(unique_frames) == len(rows) else "blocked_role_ledger"
    base = {
        "schema": schema, "run_id": run_id, "method": METHOD,
        "ledger_state": ledger_state,
        "block_reasons": sorted(set(reasons)) if blocked else [],
        "domain": {"q": Q, "n": N, "mapping": "gray", "strata": list(STRATA),
                   "primary_stratum": PRIMARY_STRATUM,
                   "frame_len_symbols": N, "dimension": Q},
        "role_policy": {"roles": list(ROLES), "mutually_exclusive": True,
                        "unambiguous_assignment_required": True,
                        "fresh_claim_forbidden": "retrospective_reuse"},
        "identity_sources": sources,
        "pool_summary": {"traceable_pool_rows": len(pool),
                         "v4_transfer_rows": len(transfers),
                         "v5_partition_rows": len(parts)},
        "counts": {"total_rows": len(rows), "by_role": dict(by_role),
                   "by_stratum_role": by_stratum_role},
        "rows": rows,
        "diagnostic_only": True, "retrospective_reuse": True,
        "note": "identity-traceable 10 dB pool; untraceable complete frames "
                "carry no role provenance and are excluded. Role assignment is "
                "reconstruction of existing V4/V5 identities, never relabeling "
                "or overwriting V5 evidence.",
    }
    return base


def validate_role_ledger(ledger: Any) -> dict[str, Any]:
    if not isinstance(ledger, Mapping):
        raise ValueError("ledger type")
    if ledger.get("schema") not in (LEDGER_SCHEMA, LEDGER_SCHEMA_TEST):
        raise ValueError("ledger schema")
    if ledger.get("ledger_state") not in ("ready", "blocked_role_ledger", "not_built"):
        raise ValueError("ledger state")
    rows = ledger.get("rows")
    if not isinstance(rows, list):
        raise ValueError("ledger rows")
    roles = [r.get("role") for r in rows]
    if any(role not in ROLES for role in roles):
        raise ValueError("ledger role")
    if ledger["ledger_state"] == "ready":
        if not rows:
            raise ValueError("ready ledger without rows")
        if len({r["frame_identity"] for r in rows}) != len(rows):
            raise ValueError("ledger frame identity not unique")
        if len({r["payload_identity"] for r in rows}) != len(rows):
            raise ValueError("ledger payload identity not unique")
        for r in rows:
            if not isinstance(r.get("frame_id"), int) or r.get("stratum") not in STRATA \
                    or not _is_hex64(r.get("frame_identity")) \
                    or not _is_hex64(r.get("payload_identity")) \
                    or not isinstance(r.get("source_path"), str):
                raise ValueError("ledger row identity")
    else:
        if rows:
            raise ValueError("blocked/not-built ledger carries rows")
    counts = ledger.get("counts")
    if not isinstance(counts, Mapping) or set(counts.get("by_role", {})).difference(ROLES):
        raise ValueError("ledger counts")
    return dict(ledger)


def write_role_ledger(path: Any, ledger: Any) -> dict[str, Any]:
    validate_role_ledger(ledger)
    _put(Path(path), ledger)
    return dict(ledger)


def build_production_ledger(discovery_root: Any, *, run_id: str) -> dict[str, Any]:
    """Production lane: scan the real identity locks and rebuild the ledger."""
    scanned = scan_identity_locks(discovery_root)
    return build_role_ledger(scanned["pool_rows"], scanned["transfer_rows"],
                             scanned["partition_rows"], schema=LEDGER_SCHEMA,
                             run_id=run_id, identity_sources=scanned["identity_sources"])


def characterization_rows(ledger: Any, *, stratum: str = PRIMARY_STRATUM) -> list[dict[str, Any]]:
    validate_role_ledger(ledger)
    if ledger["ledger_state"] != "ready":
        raise ValueError("ledger not ready")
    return [dict(r) for r in ledger["rows"]
            if r["role"] == "characterization" and r["stratum"] == stratum]


def load_production_characterization_frames(ledger: Any,
                                            *, stratum: str = PRIMARY_STRATUM) -> list[dict[str, Any]]:
    """Load the characterization-role frame arrays for one stratum from the
    real 10 dB sidecars (D01 authorization: local arrays, aggregates only).

    The real source adapter is imported lazily so the verifier and the test
    lanes never enter a real source loader.
    """
    from . import ldpc_v4_10db_source as source  # real source loader: execute-only
    rows = characterization_rows(ledger, stratum=stratum)
    lock = source.build_source_lock()
    frames: list[dict[str, Any]] = []
    for row in rows:
        alice, bob = source.arrays_for_frame(lock, {"stratum": row["stratum"],
                                                    "frame_id": row["frame_id"]})
        frames.append({"frame_id": int(row["frame_id"]), "stratum": row["stratum"],
                       "role": "characterization", "alice": alice, "bob": bob})
    return frames


def development_rows(ledger: Any, *, stratum: str = PRIMARY_STRATUM) -> list[dict[str, Any]]:
    """Development-role identity rows of one stratum (V13-P04 role policy)."""
    validate_role_ledger(ledger)
    if ledger["ledger_state"] != "ready":
        raise ValueError("ledger not ready")
    return [dict(r) for r in ledger["rows"]
            if r["role"] == "development" and r["stratum"] == stratum]


def pre_registered_d04_frames(ledger: Any, *, stratum: str = PRIMARY_STRATUM,
                              count: int = D04_FRAME_COUNT) -> list[dict[str, Any]]:
    """D04 pre-registration: the first ``count`` development-role rows of the
    primary stratum in the frozen deterministic order (sorted by ``frame_id``,
    ties broken by ``frame_identity``).

    The selection rule is frozen before the probe; the run manifest records the
    rule and the resulting frame identities.  The D04 frames are disjoint from
    the 128 sealed frame-identical audit frames by construction (audit rows are
    V5 confirmation-role, development rows are V5 development-role).
    """
    rows = development_rows(ledger, stratum=stratum)
    if len(rows) < count:
        raise ValueError(f"insufficient development rows: {len(rows)} < {count}")
    ordered = sorted(rows, key=lambda r: (int(r["frame_id"]), str(r["frame_identity"])))
    return [dict(r) for r in ordered[:count]]


def load_production_development_frames(rows: Any) -> list[dict[str, Any]]:
    """Load the D04 development-role frame arrays from the real 10 dB sidecars.

    The real source adapter is imported lazily so the verifier and the test
    lanes never enter a real source loader.  Alice truth is used only for the
    disclosed syndrome and the post-decode exact check, never in the decoder.
    """
    from . import ldpc_v4_10db_source as source  # real source loader: execute-only
    lock = source.build_source_lock()
    frames: list[dict[str, Any]] = []
    for row in rows:
        alice, bob = source.arrays_for_frame(lock, {"stratum": row["stratum"],
                                                    "frame_id": row["frame_id"]})
        frames.append({"frame_id": int(row["frame_id"]), "stratum": row["stratum"],
                       "role": "development",
                       "frame_identity": row["frame_identity"],
                       "alice": alice, "bob": bob})
    return frames


# ------------------------------------------------------------------ D02 oracle

def _check_field_tiny(q: int) -> dict[str, bool]:
    field = GF2mField.create(q)
    symbols = range(q)
    identity = all(field.add(value, 0) == value and field.mul(value, 1) == value
                   and field.mul(value, 0) == 0 for value in symbols)
    inverses = all(field.mul(value, field.inverse(value)) == 1 for value in range(1, q))
    probes = tuple(dict.fromkeys((0, 1, q - 1, *field.nonzero_cycle[::max(1, (q - 1) // 15)])))
    distributive = all(field.mul(left, field.add(right, third))
                       == field.add(field.mul(left, right), field.mul(left, third))
                       for left in probes for right in probes for third in probes)
    return {"cycle_complete": len(field.nonzero_cycle) == q - 1
                             and len(set(field.nonzero_cycle)) == q - 1,
            "identities": identity, "inverses": inverses,
            "distributivity": distributive}


def _gray_decode(value: int) -> int:
    """Inverse binary-reflected Gray code (parallel method)."""
    decoded = value
    shift = 1
    while shift < 16:
        decoded ^= (decoded >> shift)
        shift *= 2
    return decoded


def _check_gray_mapping() -> dict[str, Any]:
    ok = True
    failures: list[str] = []
    known = {0: 0, 1: 1, 2: 3, 3: 2, 4: 6, 5: 7, 6: 5, 7: 4}
    for value, expected in known.items():
        if gray_encode(np.asarray([value]))[0] != expected:
            ok, failures = False, failures + [f"known gray {value}"]
    for value in range(1024):
        if _gray_decode(int(gray_encode(np.asarray([value]))[0])) != value:
            ok, failures = False, failures + [f"gray roundtrip {value}"]
    for value in range(256):
        bits = symbols_to_bits(np.asarray([value]), Q, "gray")[0]
        reconstructed = int(sum(int(b) << (BIT_PLANES - 1 - plane)
                                for plane, b in enumerate(bits)))
        if reconstructed != int(gray_encode(np.asarray([value]))[0]):
            ok, failures = False, failures + [f"msb plane {value}"]
    return {"ok": ok, "failures": failures[:8], "bit_planes": BIT_PLANES}


def _brute_force_syndrome(matrix: Any, symbols: Any, field: GF2mField) -> tuple[int, ...]:
    """Independent explicit-loop syndrome formulation (D02 oracle target)."""
    result: list[int] = []
    for row in matrix:
        total = 0
        for coefficient, symbol in zip(row, symbols):
            total = field.add(total, field.mul(int(coefficient), int(symbol)))
        result.append(total)
    return tuple(result)


def _check_tiny_syndrome() -> dict[str, Any]:
    q, n, m = 4, 4, 2
    field = GF2mField.create(q)
    matrix = ((1, 2, 0, 3), (3, 0, 1, 2))
    checks: dict[str, Any] = {"q": q, "n": n, "m": m}
    for word in product(range(q), repeat=n):
        got = nonbinary_syndrome(matrix, word, field)
        expected = _brute_force_syndrome(matrix, word, field)
        if got != expected:
            return {**checks, "ok": False, "failures": ["brute force mismatch"]}
    counts = Counter(nonbinary_syndrome(matrix, word, field) for word in product(range(q), repeat=n))
    if any(count != q ** (n - m) for count in counts.values()) or len(counts) != q ** m:
        return {**checks, "ok": False, "failures": ["coset cardinality"]}
    # GF addition is XOR in the pinned basis: syndrome is additive.
    rng = np.random.default_rng(7)
    for _ in range(16):
        x = tuple(int(v) for v in rng.integers(0, q, size=n))
        y = tuple(int(v) for v in rng.integers(0, q, size=n))
        if nonbinary_syndrome(matrix, tuple(a ^ b for a, b in zip(x, y)), field) \
                != tuple(a ^ b for a, b in zip(nonbinary_syndrome(matrix, x, field),
                                               nonbinary_syndrome(matrix, y, field))):
            return {**checks, "ok": False, "failures": ["linearity"]}
    # Single-error detection: a one-symbol error e at position i with value v
    # gives syndrome(e) = column_i scaled by v, which is nonzero for v != 0.
    for position in range(n):
        for value in range(1, q):
            error = [0] * n
            error[position] = value
            single = nonbinary_syndrome(matrix, error, field)
            if single == (0,) * m:
                return {**checks, "ok": False, "failures": ["single error missed"]}
    return {**checks, "ok": True, "failures": []}


def _check_wrapper_contract() -> dict[str, Any]:
    manifest, matrix = v7_cb.build_nbldpc_v7_r1a_codebook()
    for key, expected in V7_R1A_FROZEN.items():
        if manifest.get(key) != expected:
            return {"ok": False, "failures": [f"frozen binding {key}"]}
    if len(matrix) != M or any(len(row) != N for row in matrix):
        return {"ok": False, "failures": ["matrix shape"]}
    verified = v7_cb.verify_nbldpc_v7_r1a_codebook(manifest, matrix)
    if verified.get("status") != "ok":
        return {"ok": False, "failures": ["codebook verification"]}
    return {"ok": True, "failures": [], "manifest_id": manifest["manifest_id"],
            "canonical_sha256": manifest["canonical_sha256"], "matrix_shape": (M, N)}


def run_engineering_oracle(*, tiny_q: tuple[int, ...] = (2, 4, 8, 16)) -> dict[str, Any]:
    """D02 engineering oracle (test-only): noiseless / single-error /
    tiny-q / tiny-n field, mapping, syndrome and wrapper-contract checks.

    Any failure returns ``diagnosis_class=interface`` with
    ``run_state=implementation_interface_fault`` and stops before any real
    decode; a pass returns ``status=ok`` with the per-check evidence.
    """
    checks: dict[str, Any] = {}
    failures: list[str] = []
    for q in tiny_q:
        try:
            result = _check_field_tiny(q)
            checks[f"field_q{q}"] = result
            if not all(result.values()):
                failures.append(f"field_q{q}")
        except (ArithmeticError, ValueError) as exc:
            checks[f"field_q{q}"] = {"error": f"{type(exc).__name__}: {exc}"}
            failures.append(f"field_q{q}")
    gray = _check_gray_mapping()
    checks["gray_mapping"] = gray
    if not gray["ok"]:
        failures.append("gray_mapping")
    tiny = _check_tiny_syndrome()
    checks["tiny_syndrome"] = tiny
    if not tiny["ok"]:
        failures.append("tiny_syndrome")
    wrapper = _check_wrapper_contract()
    checks["wrapper_contract"] = wrapper
    if not wrapper["ok"]:
        failures.append("wrapper_contract")
    if failures:
        return {"status": "failed", "diagnosis_class": "interface",
                "run_state": "implementation_interface_fault",
                "failed_checks": failures, "checks": checks}
    return {"status": "ok", "diagnosis_class": None, "run_state": None,
            "failed_checks": [], "checks": checks}


# ------------------------------------------------------------------ D03 hook

def _permutation(field: GF2mField, coefficient: int) -> np.ndarray:
    return np.asarray([field.mul(coefficient, s) for s in range(field.q)], dtype=np.intp)


@lru_cache(maxsize=4096)
def _inverse_permutation(q: int, coefficient: int) -> np.ndarray:
    """Multiplication-by-``coefficient^{-1}`` permutation; identical values to
    the frozen decoder's cache (same field, same math)."""
    if coefficient < 1:
        raise ValueError("coefficient must be nonzero")
    field = GF2mField.create(q)
    return _permutation(field, field.inverse(coefficient))


@lru_cache(maxsize=4096)
def _forward_permutation(q: int, coefficient: int) -> np.ndarray:
    if coefficient < 1:
        raise ValueError("coefficient must be nonzero")
    return _permutation(GF2mField.create(q), coefficient)


def _matrix_edges(matrix: Any) -> tuple[list[tuple[tuple[int, int], ...]], list[list[tuple[int, int]]]]:
    checks = [tuple((column, int(value)) for column, value in enumerate(row) if value)
              for row in matrix]
    variables: list[list[tuple[int, int]]] = [[] for _ in range(N)]
    for row, row_edges in enumerate(checks):
        for column, _ in row_edges:
            variables[column].append((row, column))
    return checks, variables


def _decode_preprocessing(bob_symbols: Any, syndrome: Any, manifest: Mapping[str, Any],
                          matrices: Any, *, check_count: int, p: float):
    """Replicate the frozen decoder's validation/preprocessing happy path so
    the hooked loop sees identical field, symbols, priors, matrix and budget."""
    field = GF2mField.create(Q)
    bob = _symbols(bob_symbols, Q, expected=N)
    disclosed = _symbols(syndrome, Q, expected=check_count)
    priors = qsc_symbol_priors(bob, Q, p)
    verified = v7_cb.verify_nbldpc_v7_r1a_codebook(manifest, matrices)
    if verified.get("status") != "ok":
        raise ValueError("codebook_invalid")
    matrix = tuple(tuple(int(value) for value in row) for row in matrices)
    if len(matrix) != check_count or any(len(row) != N for row in matrix):
        raise ValueError("matrix dimensions")
    checks, variables = _matrix_edges(matrix)
    edge_count = sum(map(len, checks))
    if edge_count != 2 * N or any(len(row_edges) not in (3, 4) for row_edges in checks):
        raise ValueError("edge topology")
    declared = _declared_dense_bytes(N, edge_count, Q)
    codebook_id = manifest.get("canonical_sha256")
    if not isinstance(codebook_id, str):
        raise ValueError("missing codebook id")
    return (field, bob, disclosed, matrix, checks, variables, priors, codebook_id, declared)


def _hooked_decode_flooding(bob, disclosed, matrix, checks, variables, priors, field,
                            check_count, codebook_id, declared, *, max_iter):
    """Mirror of the frozen flooding FFT-QSPA loop that additionally collects
    aggregate per-iteration telemetry.  The computation is bit-identical to
    ``nonbinary_v7_r1a_long._decode_flooding``: all message evolution uses the
    same frozen primitives and the telemetry reads are non-mutating.  Returns
    ``(result_dict, per_iteration_records, decoded_words)``."""
    q = field.q
    edge_keys = [(row, column, coefficient) for row, row_edges in enumerate(checks)
                 for column, coefficient in row_edges]
    v_to_c = {(row, column): priors[column].copy() for row, column, _ in edge_keys}
    c_to_v = {(row, column): np.full(q, 1.0 / q, dtype=np.float64) for row, column, _ in edge_keys}
    records: list[dict[str, Any]] = []
    decoded_words: list[tuple[int, ...]] = []
    rec: dict[str, Any] | None = None
    previous_decoded: tuple[int, ...] | None = None
    previous_max: float | None = None
    try:
        for iteration in range(1, int(max_iter) + 1):
            rec = {"iteration": iteration, "normalisation_calls": 0,
                   "normalisation_failures": 0, "nonfinite_events": 0,
                   "underflow_events": 0, "satisfied_checks": 0,
                   "unsatisfied_checks": 0, "syndrome_consistent": False,
                   "mean_posterior_max": None, "mean_posterior_entropy_bits": None,
                   "decoded_changed": None, "stagnation": None}
            next_c_to_v: dict[tuple[int, int], np.ndarray] = {}
            for row, row_edges in enumerate(checks):
                spectra: list[np.ndarray] = []
                for column, coefficient in row_edges:
                    scaled = v_to_c[(row, column)][_inverse_permutation(q, coefficient)]
                    spectra.append(_fwht(scaled))
                for target, (column, coefficient) in enumerate(row_edges):
                    product = np.ones(q, dtype=np.float64)
                    for other, spectrum in enumerate(spectra):
                        if other != target:
                            product *= spectrum
                    convolved = _fwht(product) / q
                    outgoing = convolved[np.bitwise_xor(_forward_permutation(q, coefficient),
                                                        disclosed[row])]
                    rec["normalisation_calls"] += 1
                    if not np.all(np.isfinite(outgoing)):
                        rec["nonfinite_events"] += 1
                    normal = _normalise(outgoing)
                    if normal is None:
                        if float(np.clip(outgoing, 0.0, None).sum()) <= 0.0:
                            rec["underflow_events"] += 1
                        rec["normalisation_failures"] += 1
                        records.append(rec)
                        return (_result("decoder_error", q=q, n=N, check_count=check_count,
                                        iterations=iteration, field_id=field.spec.field_id,
                                        codebook_id=codebook_id,
                                        declared_dense_message_bytes=declared,
                                        reason="check_message_normalisation"), records, decoded_words)
                    next_c_to_v[(row, column)] = normal
            c_to_v = next_c_to_v
            beliefs: list[np.ndarray] = []
            for column in range(N):
                belief = priors[column].copy()
                for edge in variables[column]:
                    belief *= c_to_v[edge]
                rec["normalisation_calls"] += 1
                if not np.all(np.isfinite(belief)):
                    rec["nonfinite_events"] += 1
                normal = _normalise(belief)
                if normal is None:
                    rec["normalisation_failures"] += 1
                    records.append(rec)
                    return (_result("decoder_error", q=q, n=N, check_count=check_count,
                                    iterations=iteration, field_id=field.spec.field_id,
                                    codebook_id=codebook_id,
                                    declared_dense_message_bytes=declared,
                                    reason="belief_normalisation"), records, decoded_words)
                beliefs.append(normal)
            posterior = np.stack(beliefs)
            maxes = posterior.max(axis=1)
            with np.errstate(divide="ignore", invalid="ignore"):
                logp = np.where(posterior > 0.0, np.log2(posterior), 0.0)
                entropies = -(posterior * logp).sum(axis=1)
            rec["mean_posterior_max"] = float(maxes.mean())
            rec["mean_posterior_entropy_bits"] = float(entropies.mean())
            decoded = tuple(int(np.argmax(beliefs[column])) for column in range(N))
            if previous_decoded is not None:
                rec["decoded_changed"] = decoded != previous_decoded
            previous_decoded = decoded
            decoded_words.append(decoded)
            residual = nonbinary_syndrome(matrix, decoded, field)
            rec["satisfied_checks"] = int(sum(1 for a, b in zip(residual, disclosed) if a == b))
            rec["unsatisfied_checks"] = int(check_count - rec["satisfied_checks"])
            if residual == disclosed:
                rec["syndrome_consistent"] = True
                records.append(rec)
                return (_result("syndrome_consistent", q=q, n=N, check_count=check_count,
                                iterations=iteration, syndrome_consistent=True,
                                field_id=field.spec.field_id, codebook_id=codebook_id,
                                declared_dense_message_bytes=declared,
                                decoded_symbols=decoded), records, decoded_words)
            if previous_max is not None:
                rec["stagnation"] = bool(maxes.mean() <= previous_max)
            previous_max = float(maxes.mean())
            next_v_to_c: dict[tuple[int, int], np.ndarray] = {}
            for row, column, _ in edge_keys:
                message = priors[column].copy()
                for other in variables[column]:
                    if other != (row, column):
                        message *= c_to_v[other]
                rec["normalisation_calls"] += 1
                if not np.all(np.isfinite(message)):
                    rec["nonfinite_events"] += 1
                normal = _normalise(message)
                if normal is None:
                    rec["normalisation_failures"] += 1
                    records.append(rec)
                    return (_result("decoder_error", q=q, n=N, check_count=check_count,
                                    iterations=iteration, field_id=field.spec.field_id,
                                    codebook_id=codebook_id,
                                    declared_dense_message_bytes=declared,
                                    reason="variable_message_normalisation"), records, decoded_words)
                next_v_to_c[(row, column)] = normal
            v_to_c = next_v_to_c
            records.append(rec)
    except (ArithmeticError, FloatingPointError, KeyError, OverflowError, ValueError):
        if rec is not None:
            records.append(rec)
        return (_result("decoder_error", q=q, n=N, check_count=check_count,
                        field_id=field.spec.field_id, codebook_id=codebook_id,
                        declared_dense_message_bytes=declared,
                        reason="numerical_or_field_failure"), records, decoded_words)
    return (_result("decode_failed", q=q, n=N, check_count=check_count,
                    iterations=int(max_iter), field_id=field.spec.field_id,
                    codebook_id=codebook_id, declared_dense_message_bytes=declared,
                    reason="iteration_limit"), records, decoded_words)


def _assert_result_equivalent(reference: Mapping[str, Any], hooked: Mapping[str, Any]) -> None:
    if dict(reference) != dict(hooked):
        raise ValueError("telemetry hook equivalence failure: hook-on changed the "
                         "original decoded word, status, or iterations")


def _telemetry_summary(records: list[Mapping[str, Any]], result: Mapping[str, Any],
                       decoded_words: list[tuple[int, ...]]) -> dict[str, Any]:
    per_iteration = [{key: record[key] for key in _TELEMETRY_PER_ITERATION_KEYS}
                     for record in records]
    oscillation_count = 0
    for index in range(2, len(decoded_words)):
        if decoded_words[index] == decoded_words[index - 2] \
                and decoded_words[index] != decoded_words[index - 1]:
            oscillation_count += 1
    maxes = [r["mean_posterior_max"] for r in records if r["mean_posterior_max"] is not None]
    entropies = [r["mean_posterior_entropy_bits"] for r in records
                 if r["mean_posterior_entropy_bits"] is not None]
    return {
        "final_status": str(result.get("status")),
        "final_iterations": int(result.get("iterations", 0)),
        "iterations_recorded": len(records),
        "normalisation_calls_total": int(sum(r["normalisation_calls"] for r in records)),
        "normalisation_failures_total": int(sum(r["normalisation_failures"] for r in records)),
        "nonfinite_events_total": int(sum(r["nonfinite_events"] for r in records)),
        "underflow_events_total": int(sum(r["underflow_events"] for r in records)),
        "stagnation_iterations": int(sum(1 for r in records if r.get("stagnation"))),
        "oscillation_count": oscillation_count,
        "oscillation_detected": bool(oscillation_count > 0),
        "max_posterior_concentration": float(max(maxes)) if maxes else None,
        "final_mean_posterior_max": float(maxes[-1]) if maxes else None,
        "final_mean_posterior_entropy_bits": float(entropies[-1]) if entropies else None,
        "per_iteration": per_iteration,
    }


def run_diagnostic_hook(bob_symbols: Any, syndrome: Any, manifest: Mapping[str, Any],
                        matrices: Any, *, check_count: int, p: float,
                        schedule: str = "flooding", max_iter: int = MAX_ITER,
                        hook: bool = True) -> dict[str, Any]:
    """Optional V7 R1A diagnostic hook (D03), wrapper/adapter only — the frozen
    decoder source is never modified.

    ``hook=False`` returns the original decoder result element-for-element with
    no telemetry.  ``hook=True`` runs the instrumented mirror, verifies it is
    element-for-element identical to the original result (decoded word, status,
    iterations and all other fields), and returns the original result plus
    aggregate telemetry only.  Any equivalence drift raises (the caller maps it
    to ``invalid_diagnostic_execution``).  Telemetry never contains Alice error
    locations or raw arrays.
    """
    from . import nonbinary_v7_r1a_long as v7_long  # decoder boundary: execute-only
    original = v7_long.decode_nbldpc_v7_r1a(bob_symbols, syndrome, manifest, matrices,
                                            check_count=check_count, p=p,
                                            schedule=schedule, max_iter=max_iter)
    if not hook:
        return {"hook": False, "result": original, "telemetry": None}
    if schedule != "flooding":
        raise ValueError("diagnostic hook instruments the primary flooding schedule only")
    if original.get("status") not in ("syndrome_consistent", "decode_failed", "decoder_error"):
        return {"hook": True, "result": original, "telemetry": None,
                "not_attempted": original.get("status")}
    field, bob, disclosed, matrix, checks, variables, priors, codebook_id, declared = \
        _decode_preprocessing(bob_symbols, syndrome, manifest, matrices,
                              check_count=check_count, p=p)
    hooked, records, decoded_words = _hooked_decode_flooding(
        bob, disclosed, matrix, checks, variables, priors, field, check_count,
        codebook_id, declared, max_iter=int(max_iter))
    _assert_result_equivalent(original, hooked)
    return {"hook": True, "result": original, "telemetry": _telemetry_summary(records, original, decoded_words)}


# ------------------------------------------------------------------ D01 characterization

_RUN_BUCKETS = ((1, 1), (2, 2), (3, 4), (5, 8), (9, 16), (17, 32), (33, 64), (65, 128), (129, 256))


def _ser_histogram(values: list[float], *, bins: int = 20) -> tuple[list[int], list[float]]:
    counts = [0] * bins
    for value in values:
        index = min(bins - 1, max(0, int(math.floor(value * bins))))
        counts[index] += 1
    return counts, [float(i) / bins for i in range(bins + 1)]


def _frame_channel_stats(alice: np.ndarray, bob: np.ndarray, *, q: int, n: int,
                         p: float) -> dict[str, Any]:
    a = np.asarray(alice, dtype=np.int64).reshape(-1)
    b = np.asarray(bob, dtype=np.int64).reshape(-1)
    if a.shape != (n,) or b.shape != (n,) or np.any(a < 0) or np.any(a >= q) \
            or np.any(b < 0) or np.any(b >= q):
        raise ValueError("frame domain")
    diff = np.bitwise_xor(a, b)
    errors = diff != 0
    planes_a = symbols_to_bits(a, q, "gray")
    planes_b = symbols_to_bits(b, q, "gray")
    plane_mismatch = (planes_a != planes_b).sum(axis=0)
    runs: list[int] = []
    run = 0
    for value in errors:
        if value:
            run += 1
        else:
            if run:
                runs.append(run)
                run = 0
    if run:
        runs.append(run)
    if p == 0.0:
        nll = np.zeros(n, dtype=np.float64)
    else:
        nll = np.where(diff == 0, -math.log2(1.0 - p),
                       -math.log2(p / (q - 1)))
    return {"ser": float(np.mean(errors)),
            "diff_counts": np.bincount(diff, minlength=q).astype(np.int64),
            "plane_mismatch_counts": plane_mismatch.astype(np.int64),
            "runs": runs,
            "error_positions": np.nonzero(errors)[0],
            "nll": nll}


def channel_aggregates(frames: Any, *, q: int = Q, n: int = N, mapping: str = "gray",
                       p: float = P) -> dict[str, Any]:
    """D01 no-decode channel characterization over characterization frames.

    Computes per-frame statistics in memory and returns AGGREGATES ONLY:
    bucketed histograms and summary scalars.  No raw arrays, no per-position
    masks, no Alice error locations are returned or persisted.  Empirical
    diagnostics only — never a Shannon or finite-length proof.
    """
    if not isinstance(frames, (list, tuple)) or not frames:
        raise ValueError("characterization frames required")
    diff_total = np.zeros(q, dtype=np.int64)
    plane_total = np.zeros(BIT_PLANES, dtype=np.int64)
    runs_all: list[int] = []
    position_counts = np.zeros(n, dtype=np.int64)
    nll_all: list[float] = []
    ser_values: list[float] = []
    for frame in frames:
        if not isinstance(frame, Mapping):
            raise ValueError("characterization frame")
        stats = _frame_channel_stats(frame["alice"], frame["bob"], q=q, n=n, p=p)
        diff_total += stats["diff_counts"]
        plane_total += stats["plane_mismatch_counts"]
        runs_all.extend(stats["runs"])
        position_counts[stats["error_positions"]] += 1
        nll_all.extend(float(v) for v in stats["nll"])
        ser_values.append(stats["ser"])
    total_symbols = len(frames) * n
    ser_arr = np.asarray(ser_values)
    ser_counts, ser_edges = _ser_histogram(ser_values)
    diff_bucket_width = 32
    diff_counts_buckets = [int(diff_total[i * diff_bucket_width:(i + 1) * diff_bucket_width].sum())
                           for i in range(q // diff_bucket_width)]
    zero_mass = float(diff_total[0]) / total_symbols
    nonzero_counts = int(total_symbols - diff_total[0])
    run_counts = []
    for low, high in _RUN_BUCKETS:
        run_counts.append(sum(1 for run in runs_all if low <= run <= high))
    position_bucket_width = 16
    position_buckets = [int(position_counts[i * position_bucket_width:(i + 1) * position_bucket_width].sum())
                        for i in range(n // position_bucket_width)]
    nonzeros = diff_total[diff_total > 0]
    prob = diff_total / total_symbols
    entropy = float(-(prob[prob > 0] * np.log2(prob[prob > 0])).sum())
    model_entropy = float(-((1.0 - p) * math.log2(1.0 - p)
                            + p * math.log2(p / (q - 1))))
    nll_arr = np.asarray(nll_all)
    nll_mean = float(nll_arr.mean())
    ser_mean = float(ser_arr.mean())
    return {
        "domain": {"q": q, "n": n, "mapping": mapping, "p": float(p),
                   "frames": len(frames), "symbols": total_symbols,
                   "bit_planes": BIT_PLANES},
        "raw_ser": {"mean": ser_mean, "min": float(ser_arr.min()),
                    "max": float(ser_arr.max()), "std": float(ser_arr.std()),
                    "median": float(np.median(ser_arr)),
                    "histogram_bins": ser_edges, "histogram_counts": ser_counts,
                    "bucketed": True},
        "symbol_difference": {"zero_difference_mass": zero_mass,
                              "nonzero_mass": float(nonzero_counts) / total_symbols,
                              "unique_difference_symbols": int(len(nonzeros)),
                              "bucketed_histogram_bins": [i * diff_bucket_width
                                                          for i in range(q // diff_bucket_width + 1)],
                              "bucketed_histogram_counts": diff_counts_buckets,
                              "bin_width": diff_bucket_width},
        "bit_plane_mismatch": {"planes": list(range(BIT_PLANES)),
                               "mismatch_rate": [float(c) / total_symbols
                                                 for c in plane_total],
                               "mean": float(plane_total.mean()) / total_symbols,
                               "min": float(plane_total.min()) / total_symbols,
                               "max": float(plane_total.max()) / total_symbols,
                               "note": "MSB-first binary-reflected Gray planes; "
                                       "aggregate rates only"},
        "bursts_runs": {"run_count": len(runs_all),
                        "runs_per_frame_mean": len(runs_all) / len(frames),
                        "run_length_bins": [f"{low}-{high}" for low, high in _RUN_BUCKETS],
                        "run_length_histogram": run_counts,
                        "max_run_length": max(runs_all) if runs_all else 0,
                        "mean_run_length": float(np.mean(runs_all)) if runs_all else 0.0,
                        "error_symbol_fraction": float(nonzero_counts) / total_symbols},
        "positions": {"bucket_width": position_bucket_width,
                      "error_counts_by_bucket": position_buckets,
                      "error_rate_by_bucket": [c / (len(frames) * position_bucket_width)
                                               for c in position_buckets],
                      "note": "aggregate position buckets only; no per-position data"},
        "qsc_p20": {"model_entropy_bits_per_symbol": model_entropy,
                    "empirical_ser": ser_mean,
                    "calibration_mismatch_abs": abs(ser_mean - p),
                    "nll_mean_bits_per_symbol": nll_mean,
                    "nll_std_bits": float(nll_arr.std()),
                    "nll_vs_model_entropy_gap_bits": nll_mean - model_entropy},
        "conditional_entropy": {
            "empirical_conditional_entropy_bits_per_symbol": entropy,
            "necessary_leakage_lower_bound_bits_per_symbol": entropy,
            "model_qsc_p20_entropy_bits_per_symbol": model_entropy,
            "entropy_gap_bits": entropy - model_entropy,
            "note": "empirical estimate H(diff) over the pooled GF difference "
                    "distribution; empirical diagnostic, not a Shannon or "
                    "finite-length proof"},
        "aggregation": {"mode": "no_decode_aggregate_only",
                        "raw_arrays_persisted": False,
                        "per_position_data_persisted": False,
                        "per_position_masks_persisted": False,
                        "alice_error_locations_persisted": False,
                        "empirical_diagnostics_not_proofs": True},
    }


# ------------------------------------------------------------------ six-file package

def _channel_doc(run_id: str, aggregates: Mapping[str, Any], run_state: str,
                 *, test_only: bool, performed: bool, frame_count: int) -> dict[str, Any]:
    base = {"schema": CHANNEL_SCHEMA_TEST if test_only else CHANNEL_SCHEMA,
            "run_id": run_id, "method": METHOD, "run_state": run_state,
            "characterization_performed": performed,
            "characterization_frame_count": frame_count,
            "diagnostic_only": True, "retrospective_reuse": True}
    if performed:
        base["aggregates"] = dict(aggregates)
    else:
        base["note"] = f"no D01 characterization performed; run_state={run_state}"
    return base


def _outcomes_csv_bytes(rows: Any) -> bytes:
    if not isinstance(rows, (list, tuple)):
        raise ValueError("outcome rows")
    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=OUTCOME_COLUMNS, lineterminator="\n",
                            extrasaction="raise")
    writer.writeheader()
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != set(OUTCOME_COLUMNS):
            raise ValueError("outcome row fields")
        if row["phase"] not in V13_PHASES:
            raise ValueError("outcome phase")
        writer.writerow({key: ("" if row[key] is None else row[key]) for key in OUTCOME_COLUMNS})
    raw = output.getvalue().encode("utf-8")
    if b"\r" in raw:
        raise ValueError("outcome CSV CR")
    return raw


def _telemetry_lines(records: Any, *, run_id: str, schema: str) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    if not records:
        return lines
    for record in records:
        if not isinstance(record, Mapping) or not isinstance(record.get("telemetry"), Mapping) \
                or "per_iteration" not in record["telemetry"]:
            raise ValueError("telemetry record")
        for entry in record["telemetry"]["per_iteration"]:
            if not isinstance(entry, Mapping) or set(entry) != _TELEMETRY_PER_ITERATION_KEYS:
                raise ValueError("telemetry per-iteration keys")
        forbidden = _TELEMETRY_FORBIDDEN_KEYS & set(record["telemetry"])
        if forbidden:
            raise ValueError(f"telemetry forbidden key: {sorted(forbidden)}")
        if set(record).difference({"schema", "run_id", "frame_id", "status",
                                   "iterations", "telemetry"}):
            raise ValueError("telemetry top-level keys")
        lines.append({"schema": schema, "run_id": run_id,
                      "frame_id": int(record["frame_id"]),
                      "status": str(record["status"]),
                      "iterations": int(record["iterations"]),
                      "telemetry": record["telemetry"]})
    return lines


def _report_doc(run_id: str, run_state: str, *, test_only: bool,
                note: str | None = None) -> dict[str, Any]:
    if note is None:
        note = ("state-only placeholder; no D05 conclusion. D04 (baseline "
                "probe) and D05 (root-cause report) remain unauthorized in "
                "this phase; no real-data decode was performed.")
    return {"schema": REPORT_SCHEMA_TEST if test_only else REPORT_SCHEMA,
            "run_id": run_id, "method": METHOD, "run_state": run_state,
            "diagnosis_class": None, "diagnosis_concluded": False,
            "d05_emitted": False,
            "declared_run_states": list(RUN_STATES),
            "declared_diagnosis_classes": list(DIAGNOSIS_CLASSES),
            "note": note,
            "diagnostic_only": True, "retrospective_reuse": True}


def _manifest_doc(run_id: str, run_state: str, *, test_only: bool, oracle: Mapping[str, Any],
                  ledger: Mapping[str, Any] | None, channel: Mapping[str, Any] | None,
                  artifact_bytes: Mapping[str, int], outcome_rows: int,
                  telemetry_records: int, characterization: Mapping[str, Any] | None,
                  command: str, stages_completed: tuple[str, ...] = ("D01",),
                  authorization: Mapping[str, Any] | None = None,
                  baseline: Mapping[str, Any] | None = None) -> dict[str, Any]:
    if authorization is None:
        authorization = {"d04_authorized": False, "d05_authorized": False,
                         "real_decode_authorized": False,
                         "phase": "V13-D01 channel characterization"}
    doc = {
        "schema": MANIFEST_SCHEMA_TEST if test_only else MANIFEST_SCHEMA,
        "run_id": run_id, "method": METHOD, "run_state": run_state,
        "diagnosis_class": None, "run_status": "completed",
        "stages_completed": list(stages_completed),
        "oracle_guard": {"status": oracle.get("status"),
                         "failed_checks": oracle.get("failed_checks", [])},
        "ledger": None if ledger is None else {"ledger_state": ledger["ledger_state"],
                                               "total_rows": ledger["counts"]["total_rows"],
                                               "by_role": ledger["counts"]["by_role"]},
        "characterization": characterization,
        "outcome_rows": outcome_rows, "telemetry_records": telemetry_records,
        "artifact_files": {name: {"bytes": int(artifact_bytes[name])}
                           for name in ARTIFACTS[:-1]},
        "authorization": dict(authorization),
        "command": command,
        "diagnostic_only": True, "retrospective_reuse": True,
        "provenance": _provenance()}
    if baseline is not None:
        doc["baseline"] = dict(baseline)
    return doc


def _write_package(output_dir: Path, *, run_id: str, run_state: str, test_only: bool,
                   oracle: Mapping[str, Any], ledger: Mapping[str, Any] | None,
                   channel: Mapping[str, Any] | None, outcome_rows: list[dict[str, Any]],
                   telemetry_records: Any, characterization: Mapping[str, Any] | None,
                   command: str, stages_completed: tuple[str, ...] = ("D01",),
                   authorization: Mapping[str, Any] | None = None,
                   baseline: Mapping[str, Any] | None = None,
                   report_note: str | None = None) -> dict[str, Any]:
    if not output_dir.is_dir() or any(output_dir.iterdir()):
        raise ValueError("fresh empty output directory required")
    if run_state not in RUN_STATES:
        raise ValueError("undeclared run_state")
    ledger_doc = dict(ledger) if ledger is not None else {
        "schema": LEDGER_SCHEMA_TEST if test_only else LEDGER_SCHEMA,
        "run_id": run_id, "method": METHOD, "ledger_state": "not_built",
        "block_reasons": [], "rows": [], "counts": {"total_rows": 0, "by_role": {},
                                                    "by_stratum_role": {}},
        "diagnostic_only": True, "retrospective_reuse": True,
        "note": "ledger not built: oracle interface guard failed before identity scan"}
    ledger_doc["run_id"] = run_id
    _put(output_dir / "data_role_ledger.json", ledger_doc)
    _put(output_dir / "channel_diagnostics.json", channel or _channel_doc(
        run_id, {}, run_state, test_only=test_only, performed=False, frame_count=0))
    _write_bytes(output_dir / "diagnostic_outcomes.csv", _outcomes_csv_bytes(outcome_rows))
    if telemetry_records:
        schema = TELEMETRY_SCHEMA_TEST if test_only else TELEMETRY_SCHEMA
        telemetry_lines = _telemetry_lines(telemetry_records, run_id=run_id, schema=schema)
        if not telemetry_lines:
            raise ValueError("telemetry records produced no lines")
        _write_bytes(output_dir / "decoder_telemetry.jsonl",
                     b"".join(_compact(line) + b"\n" for line in telemetry_lines))
    else:
        _write_bytes(output_dir / "decoder_telemetry.jsonl", b"")
    _put(output_dir / "root_cause_report.json", _report_doc(run_id, run_state,
                                                            test_only=test_only,
                                                            note=report_note))
    artifact_bytes = {name: (output_dir / name).stat().st_size for name in ARTIFACTS[:-1]}
    manifest = _manifest_doc(run_id, run_state, test_only=test_only, oracle=oracle,
                             ledger=ledger_doc, channel=channel,
                             artifact_bytes=artifact_bytes, outcome_rows=len(outcome_rows),
                             telemetry_records=len(telemetry_lines) if telemetry_records else 0,
                             characterization=characterization, command=command,
                             stages_completed=stages_completed,
                             authorization=authorization, baseline=baseline)
    _put(output_dir / "diagnostic_run_manifest.json", manifest)
    return {"run_id": run_id, "run_state": run_state,
            "package_dir": str(output_dir),
            "artifact_count": len(ARTIFACTS),
            "ledger_state": ledger_doc["ledger_state"],
            "characterization_frames": 0 if channel is None
            else int(channel.get("characterization_frame_count", 0))}


def run_d01(output_dir: Any, *, run_id: str | None = None, discovery_root: Any = None,
            frames: Any = None, ledger: Any = None, telemetry_records: Any = None,
            outcome_rows: Any = None, command: str = "",
            _test_only: bool = False, production_authorized: bool = False) -> dict[str, Any]:
    """Execute the D01 no-decode characterization and write the six-file
    package into one fresh additive root.

    Two lanes (mirroring the V12 prepare lanes): the fake test lane
    (``_test_only=True``, caller-supplied ledger/frames, test schemas, any
    writable fresh root) and the production lane
    (``production_authorized=True``, real identity scan and real characterization
    arrays, production schemas).  Neither lane ever invokes a decoder; a
    production call without the explicit authorization flag is a hard stop.

    Stop conditions (spec.md): an oracle failure produces
    ``implementation_interface_fault``, an ambiguous ledger produces
    ``blocked_role_ledger``; both freeze the artifact package and return
    without any characterization.
    """
    if not _test_only and not production_authorized:
        raise ValueError("V13 production D01 characterization is not authorized "
                         "during the initial phase")
    if run_id is None:
        run_id = f"v13_d01_{uuid.uuid4().hex[:8]}"
    out = Path(output_dir).resolve()
    if out.exists():
        raise FileExistsError("fresh additive output root required")
    out.mkdir(parents=True)
    oracle = run_engineering_oracle()
    characterization = None
    try:
        if oracle["status"] != "ok":
            package = _write_package(out, run_id=run_id, run_state="implementation_interface_fault",
                                     test_only=_test_only, oracle=oracle, ledger=None,
                                     channel=None, outcome_rows=[], telemetry_records=None,
                                     characterization=None, command=command)
            return package
        if ledger is None:
            if discovery_root is None:
                raise ValueError("discovery root required for production lane")
            ledger = build_production_ledger(discovery_root, run_id=run_id)
        validate_role_ledger(ledger)
        if ledger["ledger_state"] != "ready":
            package = _write_package(out, run_id=run_id, run_state="blocked_role_ledger",
                                     test_only=_test_only, oracle=oracle, ledger=ledger,
                                     channel=None, outcome_rows=[], telemetry_records=None,
                                     characterization=None, command=command)
            return package
        if frames is None:
            frames = load_production_characterization_frames(ledger, stratum=PRIMARY_STRATUM)
        aggregates = channel_aggregates(frames)
        channel = _channel_doc(run_id, aggregates, "plan_only", test_only=_test_only,
                               performed=True, frame_count=len(frames))
        characterization = {"performed": True, "stratum": PRIMARY_STRATUM,
                            "role": "characterization", "frames": len(frames),
                            "symbols": len(frames) * N,
                            "raw_ser_mean": aggregates["raw_ser"]["mean"],
                            "empirical_conditional_entropy_bits_per_symbol":
                                aggregates["conditional_entropy"]
                                ["empirical_conditional_entropy_bits_per_symbol"]}
        return _write_package(out, run_id=run_id, run_state="plan_only",
                              test_only=_test_only, oracle=oracle, ledger=ledger,
                              channel=channel, outcome_rows=list(outcome_rows or []),
                              telemetry_records=telemetry_records,
                              characterization=characterization, command=command)
    except Exception:
        # Preserve the frozen stop rule: a retained partial package is written
        # only when it exists; the exception is re-raised for the caller.
        if out.exists() and not any(out.iterdir()):
            out.rmdir()
        raise


# ------------------------------------------------------------------ D04 baseline probe

_D04_AUTHORIZATION = {"d04_authorized": True, "d05_authorized": False,
                      "real_decode_authorized": True,
                      "phase": "V13-D04 baseline probe"}


def _d04_outcome(frame: Mapping[str, Any], result: Mapping[str, Any],
                 raw_ser: float) -> dict[str, Any]:
    """One baseline outcome row: decoder status, exact-correction reason and
    iterations.  ``reason`` is ``exact_correct`` only for a syndrome-consistent
    word that equals Alice symbol-for-symbol; everything else stays a retained
    failure with its decoder reason."""
    if result.get("status") == "syndrome_consistent":
        decoded = tuple(int(v) for v in result.get("decoded_symbols", ()))
        alice = tuple(int(v) for v in frame["alice"])
        reason = "exact_correct" if decoded == alice else "exact_mismatch"
    else:
        reason = str(result.get("reason", "no_decoded_word"))
    return {"phase": D04_PHASE, "method": V7_R1A_METHOD,
            "frame_id": int(frame["frame_id"]), "stratum": PRIMARY_STRATUM,
            "role": "development", "status": str(result.get("status", "unclassified")),
            "reason": reason, "raw_ser": raw_ser,
            "iterations": int(result.get("iterations", 0)),
            "notes": "hook_equivalence=ok"}


def run_d04(output_dir: Any, *, run_id: str | None = None, discovery_root: Any = None,
            ledger: Any = None, frames: Any = None, count: int = D04_FRAME_COUNT,
            p: float = P, max_iter: int = MAX_ITER, command: str = "",
            _test_only: bool = False, production_authorized: bool = False) -> dict[str, Any]:
    """Execute the D04 frozen baseline probe and write the six-file package
    into one fresh additive root.

    Frozen contract (design.md D04 / tasks.md V13-D04): after P08 and
    V13-DT0--DT0-DT2, run the unchanged V7 R1A ``p=.20`` decoder exactly once on
    the 32 pre-registered bw200 development frames (``count``), no retry, no
    substitution, no tuning; V5 is a read-only identity/control reference.  The
    D03 hook runs with ``hook=True`` so per-iteration aggregate telemetry is
    persisted (raw arrays and Alice error locations never are).

    Alice truth is used only in two offline places: the disclosed syndrome
    ``H*alice`` and the post-decode exact-equality check.  It never enters the
    decoder prior, stopping rule, retry, frame ordering or telemetry.

    Stop conditions: an oracle failure freezes the package at
    ``implementation_interface_fault``; an ambiguous ledger freezes it at
    ``blocked_role_ledger``; a hook-equivalence drift or per-frame decoder
    exception freezes the package at ``invalid_diagnostic_execution`` with all
    retained rows.  The package run_state is ``plan_only`` (no D05 conclusion
    is emitted by D04).
    """
    if not _test_only and not production_authorized:
        raise ValueError("V13 production D04 baseline probe is not authorized; "
                         "the main thread must pass --authorized --production")
    if run_id is None:
        run_id = f"v13_d04_{uuid.uuid4().hex[:8]}"
    out = Path(output_dir).resolve()
    if out.exists():
        raise FileExistsError("fresh additive output root required")
    out.mkdir(parents=True)
    oracle = run_engineering_oracle()
    try:
        if oracle["status"] != "ok":
            return _write_package(out, run_id=run_id,
                                  run_state="implementation_interface_fault",
                                  test_only=_test_only, oracle=oracle, ledger=None,
                                  channel=None, outcome_rows=[], telemetry_records=None,
                                  characterization=None, command=command,
                                  stages_completed=("D04",),
                                  authorization=dict(_D04_AUTHORIZATION),
                                  report_note="D02 engineering oracle failed before "
                                              "the D04 baseline probe; no real decode.")
        if ledger is None:
            if discovery_root is None:
                raise ValueError("discovery root required for production lane")
            ledger = build_production_ledger(discovery_root, run_id=run_id)
        validate_role_ledger(ledger)
        if ledger["ledger_state"] != "ready":
            return _write_package(out, run_id=run_id, run_state="blocked_role_ledger",
                                  test_only=_test_only, oracle=oracle, ledger=ledger,
                                  channel=None, outcome_rows=[], telemetry_records=None,
                                  characterization=None, command=command,
                                  stages_completed=("D04",),
                                  authorization=dict(_D04_AUTHORIZATION),
                                  report_note="ambiguous role ledger froze the D04 "
                                              "baseline probe before any decode.")
        rows = pre_registered_d04_frames(ledger, stratum=PRIMARY_STRATUM, count=count)
        manifest, matrix = v7_cb.build_nbldpc_v7_r1a_codebook()
        for key, expected in V7_R1A_FROZEN.items():
            if manifest.get(key) != expected:
                raise ValueError(f"V7 R1A frozen binding drift: {key}")
        if frames is None:
            frames = load_production_development_frames(rows)
        if not isinstance(frames, (list, tuple)) or len(frames) != len(rows):
            raise ValueError("pre-registered frame list mismatch")
        field = GF2mField.create(Q)
        outcome_rows: list[dict[str, Any]] = []
        telemetry_records: list[dict[str, Any]] = []
        baseline_status: Counter = Counter()
        exact_correct = 0
        for row, frame in zip(rows, frames):
            if int(frame["frame_id"]) != int(row["frame_id"]):
                raise ValueError("frame order does not match pre-registration")
            try:
                syndrome = nonbinary_syndrome(matrix, np.asarray(frame["alice"], dtype=np.int64), field)
                raw_ser = float(frame_symbol_error_rate(frame["alice"], frame["bob"]))
                hook = run_diagnostic_hook(frame["bob"], syndrome, manifest, matrix,
                                           check_count=M, p=p, max_iter=max_iter, hook=True)
            except Exception as exc:
                return _write_package(out, run_id=run_id,
                                      run_state="invalid_diagnostic_execution",
                                      test_only=_test_only, oracle=oracle, ledger=ledger,
                                      channel=None, outcome_rows=outcome_rows,
                                      telemetry_records=telemetry_records,
                                      characterization=None, command=command,
                                      stages_completed=("D04",),
                                      authorization=dict(_D04_AUTHORIZATION),
                                      baseline={"selection_rule": "development rows of "
                                               f"{PRIMARY_STRATUM} sorted by frame_id, "
                                               f"first {count}",
                                               "pre_registered_frame_ids":
                                                   [int(r["frame_id"]) for r in rows],
                                               "frames": len(outcome_rows),
                                               "frozen_binding": V7_R1A_FROZEN["manifest_id"]},
                                      report_note=f"hook-equivalence drift or decoder "
                                                  f"exception on frame {frame['frame_id']} "
                                                  f"({type(exc).__name__}: {exc}); probe "
                                                  "frozen at invalid_diagnostic_execution "
                                                  "with retained rows.")
            result = hook["result"]
            outcome_rows.append(_d04_outcome(frame, result, raw_ser))
            baseline_status[str(result.get("status"))] += 1
            if outcome_rows[-1]["reason"] == "exact_correct":
                exact_correct += 1
            telemetry_records.append({"schema": TELEMETRY_SCHEMA_TEST if _test_only
                                      else TELEMETRY_SCHEMA, "run_id": run_id,
                                      "frame_id": int(frame["frame_id"]),
                                      "status": str(result.get("status")),
                                      "iterations": int(result.get("iterations", 0)),
                                      "telemetry": hook["telemetry"]})
        baseline = {"selection_rule": "development rows of "
                    f"{PRIMARY_STRATUM} sorted by frame_id, first {count}",
                    "pre_registered_frame_ids": [int(r["frame_id"]) for r in rows],
                    "frames": len(outcome_rows),
                    "exact_correct": exact_correct,
                    "status_counts": dict(baseline_status),
                    "frozen_binding": V7_R1A_FROZEN["manifest_id"]}
        return _write_package(out, run_id=run_id, run_state="plan_only",
                              test_only=_test_only, oracle=oracle, ledger=ledger,
                              channel=None, outcome_rows=outcome_rows,
                              telemetry_records=telemetry_records,
                              characterization=None, command=command,
                              stages_completed=("D04",),
                              authorization=dict(_D04_AUTHORIZATION),
                              baseline=baseline,
                              report_note="D04 baseline probe completed once; no D05 "
                                          "root-cause conclusion is emitted by this "
                                          "package.")
    except Exception:
        if out.exists() and not any(out.iterdir()):
            out.rmdir()
        raise


# ------------------------------------------------------------------ read-only verify

def _verify_telemetry_file(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    if not raw:
        return {"records": 0, "ok": True}
    lines = raw.splitlines()
    for line in lines:
        doc = json.loads(line)
        if not isinstance(doc, Mapping) or doc.get("schema") not in (TELEMETRY_SCHEMA,
                                                                     TELEMETRY_SCHEMA_TEST):
            raise ValueError("telemetry schema")
        telemetry = doc.get("telemetry")
        if not isinstance(telemetry, Mapping):
            raise ValueError("telemetry body")
        if set(telemetry).difference({"final_status", "final_iterations",
                                      "iterations_recorded", "normalisation_calls_total",
                                      "normalisation_failures_total", "nonfinite_events_total",
                                      "underflow_events_total", "stagnation_iterations",
                                      "oscillation_count", "oscillation_detected",
                                      "max_posterior_concentration",
                                      "final_mean_posterior_max",
                                      "final_mean_posterior_entropy_bits", "per_iteration"}):
            raise ValueError("telemetry aggregate keys")
        for entry in telemetry["per_iteration"]:
            if set(entry) != _TELEMETRY_PER_ITERATION_KEYS:
                raise ValueError("telemetry per-iteration keys")
        if _TELEMETRY_FORBIDDEN_KEYS & set(telemetry):
            raise ValueError("telemetry forbidden key")
    return {"records": len(lines), "ok": True}


def _verify_outcomes_file(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    if b"\r" in raw:
        raise ValueError("outcomes CSV CR")
    text = raw.decode("utf-8")
    reader = csv.DictReader(StringIO(text, newline=""))
    if tuple(reader.fieldnames or ()) != OUTCOME_COLUMNS:
        raise ValueError("outcomes CSV header")
    rows = list(reader)
    for row in rows:
        if row.get("phase") not in V13_PHASES:
            raise ValueError("outcomes phase")
    return {"rows": len(rows), "ok": True}


def verify_package(output_dir: Any, *, _private_test_only: bool = False) -> dict[str, Any]:
    """Read-only, decoder-free verification of a six-file diagnostic package.

    Never imports or calls a decoder, never touches a real source loader and
    never writes to the package.  Structural validation only: schemas, allowed
    state values, mutual exclusivity, aggregate-only channel content, and
    cross-file run_id/run_state consistency.
    """
    out = Path(output_dir)
    if not out.is_dir():
        raise ValueError("package directory missing")
    present = {p.name for p in out.iterdir() if p.is_file()}
    missing = set(ARTIFACTS).difference(present)
    if missing:
        raise ValueError(f"package missing artifacts: {sorted(missing)}")
    if set(present).difference(ARTIFACTS):
        raise ValueError(f"package has unexpected files: {sorted(set(present).difference(ARTIFACTS))}")
    ledger = _json_read(out / "data_role_ledger.json")
    validate_role_ledger(ledger)
    channel = _json_read(out / "channel_diagnostics.json")
    if channel.get("schema") not in (CHANNEL_SCHEMA, CHANNEL_SCHEMA_TEST):
        raise ValueError("channel schema")
    report = _json_read(out / "root_cause_report.json")
    if report.get("schema") not in (REPORT_SCHEMA, REPORT_SCHEMA_TEST):
        raise ValueError("report schema")
    manifest = _json_read(out / "diagnostic_run_manifest.json")
    if manifest.get("schema") not in (MANIFEST_SCHEMA, MANIFEST_SCHEMA_TEST):
        raise ValueError("manifest schema")
    run_id = manifest.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise ValueError("manifest run id")
    for doc, name in ((ledger, "ledger"), (channel, "channel"),
                      (report, "report"), (manifest, "manifest")):
        if doc.get("run_id") != run_id:
            raise ValueError(f"{name} run id mismatch")
    run_state = manifest.get("run_state")
    if run_state not in RUN_STATES:
        raise ValueError("manifest run state")
    for name, doc in (("channel", channel), ("report", report)):
        if doc.get("run_state") != run_state:
            raise ValueError(f"{name} run state mismatch")
    if report.get("diagnosis_class") is not None \
            and report["diagnosis_class"] not in DIAGNOSIS_CLASSES:
        raise ValueError("report diagnosis class")
    if report.get("d05_emitted", False) or report.get("diagnosis_concluded", False):
        raise ValueError("report must not carry a D05 conclusion")
    characterization = manifest.get("characterization")
    if channel.get("characterization_performed"):
        if run_state != "plan_only":
            raise ValueError("characterization requires plan_only run state")
        aggregates = channel.get("aggregates")
        if not isinstance(aggregates, Mapping) or "raw_ser" not in aggregates \
                or "conditional_entropy" not in aggregates:
            raise ValueError("channel aggregates")
        if aggregates["aggregation"]["raw_arrays_persisted"] \
                or aggregates["aggregation"]["per_position_data_persisted"] \
                or aggregates["aggregation"]["alice_error_locations_persisted"]:
            raise ValueError("channel persists forbidden raw data")
        if not isinstance(characterization, Mapping) or not characterization.get("performed"):
            raise ValueError("manifest characterization")
    outcomes = _verify_outcomes_file(out / "diagnostic_outcomes.csv")
    telemetry = _verify_telemetry_file(out / "decoder_telemetry.jsonl")
    artifact_bytes = manifest.get("artifact_files")
    if not isinstance(artifact_bytes, Mapping) or set(artifact_bytes) != set(ARTIFACTS[:-1]):
        raise ValueError("manifest artifact files")
    for name in ARTIFACTS[:-1]:
        if not isinstance(artifact_bytes[name], Mapping) \
                or artifact_bytes[name].get("bytes") != (out / name).stat().st_size:
            raise ValueError("manifest artifact size")
    if telemetry["records"] != int(manifest.get("telemetry_records", 0)):
        raise ValueError("manifest telemetry count")
    if outcomes["rows"] != int(manifest.get("outcome_rows", 0)):
        raise ValueError("manifest outcome count")
    authorization = manifest.get("authorization")
    if not isinstance(authorization, Mapping):
        raise ValueError("manifest authorization")
    stages = tuple(manifest.get("stages_completed") or ())
    if stages == ("D04",):
        # D04 package: real-decode authorization is limited to the frozen
        # baseline probe; no D05 conclusion and no characterization.  Frozen
        # failure packages (oracle guard / blocked ledger / hook drift) carry
        # zero or partial baseline rows and no conclusion either.
        if authorization.get("real_decode_authorized") is not True \
                or authorization.get("d04_authorized") is not True \
                or authorization.get("d05_authorized") is not False:
            raise ValueError("manifest D04 authorization")
        if not str(authorization.get("phase", "")).startswith("V13-D04"):
            raise ValueError("manifest D04 phase")
        if run_state not in ("plan_only", "implementation_interface_fault",
                             "blocked_role_ledger", "invalid_diagnostic_execution"):
            raise ValueError("D04 package run state")
        if channel.get("characterization_performed"):
            raise ValueError("D04 package must not carry characterization")
        if any(row.get("phase") != "baseline" for row in
               csv.DictReader(StringIO((out / "diagnostic_outcomes.csv").read_text("utf-8"), newline=""))):
            raise ValueError("D04 outcome phase")
        baseline = manifest.get("baseline")
        if run_state in ("implementation_interface_fault", "blocked_role_ledger"):
            if baseline is not None or outcomes["rows"] != 0 or telemetry["records"] != 0:
                raise ValueError("manifest D04 failure package")
        else:
            if not isinstance(baseline, Mapping) \
                    or baseline.get("frames") != int(manifest.get("outcome_rows", 0)) \
                    or baseline.get("frozen_binding") != V7_R1A_FROZEN["manifest_id"]:
                raise ValueError("manifest D04 baseline")
            if not _test_schema(manifest) and baseline.get("frames") != D04_FRAME_COUNT:
                raise ValueError("manifest D04 frame count")
    else:
        if authorization.get("real_decode_authorized", True):
            raise ValueError("manifest real-decode authorization")
    return {"verified": True, "run_id": run_id, "run_state": run_state,
            "ledger_state": ledger["ledger_state"],
            "ledger_counts": ledger["counts"],
            "characterization_performed": bool(channel.get("characterization_performed")),
            "telemetry_records": telemetry["records"],
            "outcome_rows": outcomes["rows"]}


def v13_d04_d05_guard(action: str, authorized: bool) -> None:
    """D04/D05 entry guard.

    ``d05`` remains a hard stop (SystemExit 2): the root-cause report requires
    D04 results and a separate main-thread authorization, and is not
    implemented.  ``d04`` exits 2 unless the main thread passed the explicit
    authorization flag; the authorized production probe itself is implemented
    in :func:`run_d04` (the CLI additionally requires ``--production``).  The
    test lane never uses this guard: it calls the module API directly with
    ``_test_only=True`` and fake frames."""
    if action not in ("d04", "d05"):
        raise ValueError(f"unknown guard action: {action}")
    if action == "d05":
        raise SystemExit(2)
    if not authorized:
        raise SystemExit(2)
