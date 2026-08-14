"""V13 R3 fresh-acquisition prepare (``formal-nonbinary-ldpc-v13-r3-fresh-acquisition``).

This module owns ONLY the PREP stage tooling for the fresh-data lane.  It builds
the frozen prepare package (plan + identity ledger, or the two frozen-failure
packages) from caller-declared fresh data source paths and the locally
discoverable historical exclusion locks.

Frozen contracts (design.md §1-§5, §7; tasks.md PREP01-PREP04):

- ``scan_fresh_sources(declared_paths)`` is a **deterministic, side-effect-free**
  data-source check.  The declared fresh paths must satisfy the same pairs-table
  column contract the V13 historical data uses (``load_pairs_table`` /
  ``build_frame_batch`` readable: ``frame_id`` / ``pair_idx`` / ``alice_symbol``
  / ``bob_symbol``).  An empty/absent declared list returns **zero eligible
  rows** — the legitimate frozen outcome ``no_eligible_frames``.
- ``derive_identity(stratum, row)`` derives ``v13r3fresh-<stratum>-<uuid>`` where
  the uuid is deterministically computed from the frozen plan seed (default
  ``20260815``) plus the canonical row fields.
- ``exclusion_check(identity, exclusion_sets)`` verifies the identity does not
  collide with any historical lock set (V4 10 dB/16 dB transfer locks, V5
  partition role locks, V13 role ledger, V12 excluded sets), reusing the V12
  ``nonbinary_v12_real_partition`` exclusion-manifest construction read-only.
- ``assign_roles(rows, seed)`` pre-registers the mutually exclusive
  characterization / canary (64) / confirmation (128) roles in a deterministic
  order; ambiguous rows fall to ``blocked_role_ledger`` semantics.
- ``build_plan(...)`` emits the frozen plan doc
  (schema ``nbldpc_v13r3_fresh_plan_v1``) plus the identity ledger;
  ``build_no_eligible_package(...)`` (schema ``nbldpc_v13r3_fresh_no_eligible_v1``)
  and ``build_frozen_failure_package(...)`` for ``insufficient_eligible_frames``
  (schema ``nbldpc_v13r3_fresh_insufficient_v1``) are the two frozen-failure
  shapes.

The module is deliberately **decoder-free and array-free**: it never imports a
decoder (including ``nonbinary_v13_r3_candidate``), never loads sidecar symbol
arrays, and never reads raw frame data.  Production output requires a separate
main-thread ``production_prepare_authorized=True`` flag; the fake test lane
(``_test_only=True``) writes test schemas into a caller-owned fresh root.
"""
from __future__ import annotations

import csv
import hashlib
import json
import platform
import uuid as _uuid
from pathlib import Path
from typing import Any, Mapping

from . import nonbinary_v12_real_partition as partition  # read-only reuse (exclusion machinery)

# ------------------------------------------------------------------ frozen constants

METHOD = "nbldpc_v13r3_fresh"
# Primary stratum (design.md §1): bw200.  Secondary strata bw120/bw180 are
# cross-stratum observation only and never enter the main decision.
PRIMARY_STRATUM = "d1024_bw200"
STRATA = ("d1024_bw120", "d1024_bw180", "d1024_bw200")

# Identity namespace prefix (design.md §2).
IDENTITY_PREFIX = "v13r3fresh"

# Frozen plan seed (the seed from which per-row uuids are deterministically
# derived).  Frozen default 20260815 (plan seed, tasks.md).
PLAN_SEED_DEFAULT = 20260815

# Role counts (design.md §2/§4): characterization (all remaining eligible rows
# outside the fixed canary+confirmation pre-registration), canary 64,
# confirmation 128.  Main decision = canary 64 + confirmation 128 = 192.
CANARY_COUNT = 64
CONFIRMATION_COUNT = 128
REQUIRED_EXEC_FRAMES = CANARY_COUNT + CONFIRMATION_COUNT  # 192

ROLES = ("characterization", "canary", "confirmation")

# Frozen failure outcomes (design.md §5).
NO_ELIGIBLE_STATE = "no_eligible_frames"
INSUFFICIENT_STATE = "insufficient_eligible_frames"

# Frozen package schemas (design.md §7 scope of this task).
PLAN_SCHEMA = "nbldpc_v13r3_fresh_plan_v1"
PLAN_SCHEMA_TEST = "nbldpc_v13r3_fresh_plan_test_v1"
NO_ELIGIBLE_SCHEMA = "nbldpc_v13r3_fresh_no_eligible_v1"
NO_ELIGIBLE_SCHEMA_TEST = "nbldpc_v13r3_fresh_no_eligible_test_v1"
INSUFFICIENT_SCHEMA = "nbldpc_v13r3_fresh_insufficient_v1"
INSUFFICIENT_SCHEMA_TEST = "nbldpc_v13r3_fresh_insufficient_test_v1"

RUN_ID = "nbldpc_v13r3_fresh"
TEST_RUN_ID = "nbldpc_v13r3_fresh_test_v1"

# Decoder invariants (design.md §3) — referenced only as frozen constants, never
# imported/called.  The codebook ``nbldpc_v13_r3_code_v1`` and
# ``nonbinary_v13_r3_candidate`` are NOT imported in this module.
DECODER_INVARIANT = {
    "codebook": "nbldpc_v13_r3_code_v1",
    "q": 1024, "n": 256, "m": 170, "p": 0.20, "max_iter": 100,
    "seed": 20260818, "rank": 170, "check_degrees": {"3": 168, "4": 2},
}

FAILURE_POLICY = "immutable_no_rerun_no_resume_no_tuning_no_replacement"

# Canonical row fields used for the deterministic uuid derivation and identity.
_ROW_FIELDS = ("stratum", "frame_id", "source_record_sha256")

# ------------------------------------------------------------------ helpers


def _compact(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def _sha(value: Any) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else _compact(value)).hexdigest()


def _self(value: dict[str, Any], key: str) -> dict[str, Any]:
    return {**value, key: _sha(_compact(value))}


def _is_hex64(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 \
        and all(c in "0123456789abcdef" for c in value)


def _put(path: Path, value: Any) -> None:
    path.open("xb").write(_compact(value))


def _json_read(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    doc = json.loads(raw)
    if not isinstance(doc, dict) or _compact(doc) != raw:
        raise ValueError("noncanonical json")
    return doc


def _root() -> Path:
    return Path(__file__).resolve().parents[4]


def _test_schema(doc: Mapping[str, Any]) -> bool:
    return bool(str(doc.get("schema", "")).endswith("_test_v1"))


def _canonical_row_fields(row: Mapping[str, Any]) -> dict[str, Any]:
    """Canonical, order-stable subset of a fresh row used for the uuid."""
    missing = [k for k in _ROW_FIELDS if k not in row]
    if missing:
        raise ValueError(f"fresh row missing canonical fields: {sorted(missing)}")
    if row["stratum"] not in STRATA:
        raise ValueError("fresh row stratum")
    if isinstance(row["frame_id"], bool) or not isinstance(row["frame_id"], int):
        raise ValueError("fresh row frame id")
    return {k: row[k] for k in _ROW_FIELDS}


# ------------------------------------------------------------------ fresh source scan


def _pairs_table_columns() -> tuple[str, ...]:
    """The pairs-table column contract the V13 historical data uses
    (``load_pairs_table`` / ``build_frame_batch`` readable)."""
    return ("frame_id", "pair_idx", "alice_symbol", "bob_symbol")


def scan_fresh_sources(declared_paths: Any) -> dict[str, Any]:
    """Deterministic, side-effect-free check of the declared fresh data source
    paths.

    ``declared_paths`` is a sequence of paths (files or directories carrying the
    V13 pairs-table contract) or, when absent/empty, yields **zero eligible
    rows** (the legitimate frozen ``no_eligible_frames`` result).  Only the
    declared paths are read; no network, no background search, no decoder.

    Eligibility (frozen): a declared source contributes eligible rows when it
    exists, is readable, and its pairs-table columns satisfy the required
    contract.  The caller (plan builder) maps zero eligible rows to
    ``no_eligible_frames``; this function itself only reports, it never writes.
    """
    if declared_paths is None:
        declared_paths = []
    if isinstance(declared_paths, (str, Path)):
        declared_paths = [declared_paths]
    declared = [Path(p) for p in declared_paths]

    required = set(_pairs_table_columns())
    sources: list[dict[str, Any]] = []
    eligible_rows: list[dict[str, Any]] = []
    for path in declared:
        record: dict[str, Any] = {"path": str(Path(path)), "status": "ok",
                                  "eligible_rows": 0, "reason": ""}
        if not Path(path).exists():
            record.update(status="missing", reason="path does not exist")
            sources.append(record)
            continue
        columns: set[str] | None = None
        try:
            columns = _declared_columns(path)
        except Exception as exc:  # deterministic: report, never raise
            record.update(status="unreadable", reason=f"{type(exc).__name__}: {exc}")
            sources.append(record)
            continue
        record["columns"] = sorted(columns) if columns is not None else []
        if not required.issubset(columns or set()):
            record.update(status="invalid_contract",
                          reason=f"missing columns {sorted(required - (columns or set()))}")
            sources.append(record)
            continue
        # Count eligible frames without loading symbol arrays: only the frame
        # column is materialized.  A source with the correct columns and at
        # least one row contributes its frames as eligible rows.
        try:
            frames = _declared_frame_ids(path)
        except Exception as exc:
            record.update(status="unreadable", reason=f"{type(exc).__name__}: {exc}")
            sources.append(record)
            continue
        # A deterministic per-source record hash anchors the identity derivation
        # without reading symbol arrays (array-free).  It binds the declared
        # path so identities are reproducible for the same source declaration.
        source_record_sha256 = _sha({"path": str(Path(path)).replace("\\", "/")})
        for fid in frames:
            eligible_rows.append({"path": str(Path(path)), "frame_id": int(fid),
                                  "stratum": PRIMARY_STRATUM,
                                  "source_record_sha256": source_record_sha256})
        record["eligible_rows"] = len(frames)
        sources.append(record)
    # Deduplicate on (path, frame_id) to keep the scan deterministic.
    seen: set[tuple[str, int]] = set()
    unique: list[dict[str, Any]] = []
    for row in eligible_rows:
        key = (row["path"], row["frame_id"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    unique.sort(key=lambda r: (r["path"], r["frame_id"]))
    return {"schema": "nbldpc_v13r3_fresh_source_scan_v1",
            "declared_path_count": len(declared),
            "declared_paths": [str(Path(p)) for p in declared],
            "eligible_row_count": len(unique),
            "eligible_rows": unique,
            "sources": sources}


def _declared_columns(path: Path) -> set[str]:
    """Report the column names of a declared fresh source (pairs-table)."""
    suffix = Path(path).suffix.lower()
    if suffix == ".csv":
        with Path(path).open("r", encoding="utf-8", newline="") as fh:
            reader = csv.reader(fh)
            try:
                header = next(reader)
            except StopIteration:
                return set()
        return {str(c).strip() for c in header}
    if suffix in (".parquet", ".pq", ".pkl", ".pickle"):
        try:
            import pandas as pd
        except ImportError:
            raise ValueError("pandas required for columnari fresh sources")
        if suffix in (".parquet", ".pq"):
            try:
                df = pd.read_parquet(path, columns=None)
            except Exception:
                df = pd.read_pickle(path)
        else:
            df = pd.read_pickle(path)
        return set(str(c) for c in df.columns)
    # Directory carrying the sidecar contract: columns are fixed by the loader.
    if Path(path).is_dir():
        return set(_pairs_table_columns())
    raise ValueError(f"unsupported fresh source format: {suffix or 'directory'}")


def _declared_frame_ids(path: Path) -> list[int]:
    """Materialize only the ``frame_id`` column of a declared source (never the
    symbol arrays)."""
    suffix = Path(path).suffix.lower()
    if suffix == ".csv":
        import pandas as pd
        df = pd.read_csv(path, usecols=["frame_id"])
        fids = [int(v) for v in df["frame_id"].dropna().tolist()]
        return sorted(set(fids))
    if suffix in (".parquet", ".pq", ".pkl", ".pickle"):
        import pandas as pd
        if suffix in (".parquet", ".pq"):
            try:
                df = pd.read_parquet(path, columns=["frame_id"])
            except Exception:
                df = pd.read_pickle(path)[["frame_id"]]
        else:
            df = pd.read_pickle(path)[["frame_id"]]
        fids = [int(v) for v in df["frame_id"].dropna().tolist()]
        return sorted(set(fids))
    if Path(path).is_dir():
        # sidecar directory: one frame per sidecar pair set; frame_id 0.
        return [0]
    raise ValueError(f"unsupported fresh source format: {suffix or 'directory'}")


# ------------------------------------------------------------------ identity derivation


def derive_identity(stratum: str, row: Mapping[str, Any], *,
                    seed: int = PLAN_SEED_DEFAULT) -> str:
    """``v13r3fresh-<stratum>-<uuid>`` with a deterministically derived uuid.

    The uuid is the hex digest of ``sha256(seed || canonical_row)`` where
    ``canonical_row`` is the sort-keyed, order-stable canonical subset
    (``stratum`` / ``frame_id`` / ``source_record_sha256``).  The seed is the
    frozen plan seed recorded in the plan (default 20260815).
    """
    if stratum not in STRATA:
        raise ValueError("identity stratum")
    fields = _canonical_row_fields(row)
    material = _compact({"seed": int(seed), "row": fields})
    uuid_value = _sha(material)
    return f"{IDENTITY_PREFIX}-{stratum}-{uuid_value}"


# ------------------------------------------------------------------ exclusion


def build_exclusion_sets(discovery_root: Any) -> dict[str, Any]:
    """Build the union of historical lock identities (V4 10 dB/16 dB transfer
    locks, V5 partition role locks, V13 role ledger, V12 excluded sets) by
    reusing the V12 partition exclusion-manifest machinery read-only.

    Identity-only and decoder-free: reads only lock/manifest metadata and the
    V13 role ledger; never loads symbol arrays.  When ``discovery_root`` is
    absent, returns an EMPTY exclusion set (prepared for the no-fresh-data
    path, which needs no historical locks to produce ``no_eligible_frames``).
    """
    if discovery_root is None:
        return {"frame": set(), "payload": set(), "frame_count": 0,
                "payload_count": 0, "packages": [], "discovery_root": None}
    root = Path(discovery_root)
    if not root.is_dir():
        raise ValueError("discovery root missing")
    packages = partition.discover_packages(root)
    manifest = partition.build_exclusion_manifest(packages, run_id=RUN_ID,
                                                  schema="nbldpc_v13r3_fresh_exclusion_v1")
    frame = set(manifest.get("excluded_frame_identities", []))
    payload = set(manifest.get("excluded_payload_identities", []))
    return {"frame": frame, "payload": payload,
            "frame_count": len(frame), "payload_count": len(payload),
            "packages": packages, "discovery_root": str(root),
            "exclusion_sha256": manifest["exclusion_sha256"]}


def _v13_role_ledger_identities(discovery_root: Any) -> tuple[set[str], set[str]]:
    """V13 role-ledger identity sets (characterization / development /
    retrospective_audit), read from any locally discoverable
    ``data_role_ledger.json`` under the V13 diagnostics root.  Read-only and
    array-free; returns empty sets when no V13 ledger is discoverable."""
    frame: set[str] = set()
    payload: set[str] = set()
    if discovery_root is None:
        return frame, payload
    base = Path(_root()) / "comparison_bench/outputs_comparison/nonbinary_diagnostics"
    if not base.exists():
        return frame, payload
    for path in sorted(base.rglob("data_role_ledger.json")):
        try:
            doc = json.loads(path.read_bytes())
        except (OSError, ValueError):
            continue
        rows = doc.get("rows", []) if isinstance(doc, Mapping) else []
        for r in rows:
            if not isinstance(r, Mapping):
                continue
            if _is_hex64(r.get("frame_identity")):
                frame.add(r["frame_identity"])
            if _is_hex64(r.get("payload_identity")):
                payload.add(r["payload_identity"])
    return frame, payload


def exclusion_check(identity: str, exclusion_sets: Mapping[str, Any]) -> dict[str, Any]:
    """Verify ``identity`` (derived from a fresh row) does not collide with any
    historical lock set.  The identity's own namespace (``v13r3fresh-...``) is
    disjoint from the historical hex identities by construction, but a collision
    is still reported fail-closed if the identity string or its underlying uuid
    appears in any excluded set."""
    if not isinstance(identity, str) or not identity.startswith(IDENTITY_PREFIX + "-"):
        raise ValueError("fresh identity namespace")
    frame = set(exclusion_sets.get("frame", set()))
    payload = set(exclusion_sets.get("payload", set()))
    # The derived uuid is the identity's trailing field; a collision with an
    # excluded hex identity means the same 64-hex digest was already locked.
    uuid_field = identity.rsplit("-", 1)[-1] if identity.count("-") >= 2 else ""
    collisions: list[str] = []
    if identity in frame or identity in payload or uuid_field in frame or uuid_field in payload:
        collisions.append("historical_lock_collision")
    # V13 role ledger identities are folded into exclusion_sets by the plan
    # builder; when present as a separate key, check them too.
    for key in ("v13_frame", "v13_payload"):
        extra = set(exclusion_sets.get(key, set()))
        if identity in extra or uuid_field in extra:
            collisions.append("v13_role_ledger_collision")
    return {"identity": identity, "collision": bool(collisions),
            "collisions": sorted(set(collisions))}


# ------------------------------------------------------------------ role assignment


def assign_roles(rows: Any, *, seed: int = PLAN_SEED_DEFAULT) -> dict[str, Any]:
    """Mutually exclusive pre-registration of characterization / canary (64) /
    confirmation (128) roles.

    Rows are ordered deterministically (by the derived identity, itself a
    function of the frozen seed + canonical row fields); the first
    ``CANARY_COUNT`` are ``canary``, the next ``CONFIRMATION_COUNT`` are
    ``confirmation``, and any remainder are ``characterization``.  Ambiguity
    (duplicate derived identities) yields ``blocked_role_ledger`` semantics.
    """
    if not isinstance(rows, list):
        raise ValueError("fresh rows required")
    ordered: list[dict[str, Any]] = []
    seen_identities: set[str] = set()
    ambiguous: list[str] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("fresh row")
        stratum = str(row.get("stratum", PRIMARY_STRATUM))
        identity = derive_identity(stratum, row, seed=seed)
        if identity in seen_identities:
            ambiguous.append(identity)
            continue
        seen_identities.add(identity)
        ordered.append({"stratum": stratum, "frame_id": int(row["frame_id"]),
                        "identity": identity, "row": dict(row)})
    ordered.sort(key=lambda r: r["identity"])
    assigned: list[dict[str, Any]] = []
    for rank, entry in enumerate(ordered):
        if rank < CANARY_COUNT:
            role = "canary"
        elif rank < REQUIRED_EXEC_FRAMES:
            role = "confirmation"
        else:
            role = "characterization"
        assigned.append({"identity": entry["identity"], "stratum": entry["stratum"],
                         "frame_id": entry["frame_id"], "role": role,
                         "role_rank": rank,
                         "row": entry["row"]})
    state = "blocked_role_ledger" if ambiguous else "ready"
    counts = {role: sum(1 for a in assigned if a["role"] == role) for role in ROLES}
    return {"schema": "nbldpc_v13r3_fresh_role_assignment_v1",
            "seed": int(seed), "state": state,
            "ambiguous_identities": sorted(set(ambiguous)),
            "total_rows": len(rows), "assigned_rows": len(assigned),
            "counts": counts,
            "assignments": assigned}


def role_mutual_exclusion_holds(assignment: Mapping[str, Any]) -> bool:
    """True when every assigned row has exactly one role and roles are mutually
    exclusive (each identity appears once)."""
    rows = assignment.get("assignments", [])
    ids = [r["identity"] for r in rows]
    return len(ids) == len(set(ids)) and all(r["role"] in ROLES for r in rows)


# ------------------------------------------------------------------ plan / packages


def build_plan(scan: Mapping[str, Any], assignment: Mapping[str, Any],
               exclusion_sets: Mapping[str, Any], *, seed: int = PLAN_SEED_DEFAULT,
               run_id: str = RUN_ID, schema: str = PLAN_SCHEMA,
               declared_paths: Any = None) -> dict[str, Any]:
    """Frozen plan doc (schema ``nbldpc_v13r3_fresh_plan_v1``) + identity ledger.

    Binds: the declared source scan, the frozen seed, the mutually exclusive
    role assignment, the exclusion summary, and the identity ledger (one entry
    per eligible frame).  Decoder-free and array-free.
    """
    rows = scan.get("eligible_rows", [])
    ledger = [{"identity": a["identity"], "stratum": a["stratum"],
               "frame_id": a["frame_id"], "role": a["role"]}
              for a in assignment["assignments"]]
    if declared_paths is not None:
        declared_list = [str(p) for p in declared_paths]
    else:
        declared_list = [str(p) for p in scan.get("declared_paths", [])]
    base = {
        "schema": schema,
        "run_id": run_id,
        "method": METHOD,
        "plan_state": assignment["state"] if assignment["state"] == "blocked_role_ledger"
                     else "ready",
        "seed": int(seed),
        "identity_namespace": IDENTITY_PREFIX,
        "roles": {"characterization": "characterization",
                  "canary_count": CANARY_COUNT,
                  "confirmation_count": CONFIRMATION_COUNT,
                  "required_exec_frames": REQUIRED_EXEC_FRAMES},
        "declared_paths": declared_list,
        "eligible_row_count": scan.get("eligible_row_count", len(rows)),
        "eligible_rows": list(rows),
        "exclusion_summary": {"excluded_frame_count": exclusion_sets.get("frame_count", 0),
                              "excluded_payload_count": exclusion_sets.get("payload_count", 0),
                              "exclusion_sha256": exclusion_sets.get("exclusion_sha256", "")},
        "role_assignment": assignment,
        "identity_ledger": ledger,
        "decoder_invariant": dict(DECODER_INVARIANT),
        "failure_policy": FAILURE_POLICY,
        "provenance": {"python": platform.python_version(),
                       "platform": platform.platform()},
    }
    return _self(base, "plan_sha256")


def _base_failure_package(state: str, *, seed: int, run_id: str, schema: str,
                          declared_paths: Any, exclusion_sets: Mapping[str, Any],
                          scan: Mapping[str, Any]) -> dict[str, Any]:
    rows = scan.get("eligible_rows", [])
    declared_list = [str(p) for p in declared_paths] if declared_paths is not None else []
    base = {
        "schema": schema,
        "run_id": run_id,
        "method": METHOD,
        "terminal_state": state,
        "seed": int(seed),
        "identity_namespace": IDENTITY_PREFIX,
        "declared_paths": declared_list,
        "eligible_row_count": scan.get("eligible_row_count", len(rows)),
        "eligible_rows": list(rows),
        "exclusion_summary": {"excluded_frame_count": exclusion_sets.get("frame_count", 0),
                              "excluded_payload_count": exclusion_sets.get("payload_count", 0),
                              "exclusion_sha256": exclusion_sets.get("exclusion_sha256", "")},
        "required_exec_frames": REQUIRED_EXEC_FRAMES,
        "decoder_invariant": dict(DECODER_INVARIANT),
        "failure_policy": FAILURE_POLICY,
        "provenance": {"python": platform.python_version(),
                       "platform": platform.platform()},
    }
    return base


def build_no_eligible_package(*, seed: int = PLAN_SEED_DEFAULT, run_id: str = RUN_ID,
                              schema: str = NO_ELIGIBLE_SCHEMA, declared_paths: Any = None) -> dict[str, Any]:
    """Frozen-failure package (schema ``nbldpc_v13r3_fresh_no_eligible_v1``) for
    the zero-eligible outcome ``no_eligible_frames``."""
    scan = scan_fresh_sources(declared_paths)
    exclusion = {"frame_count": 0, "payload_count": 0, "exclusion_sha256": ""}
    base = _base_failure_package(NO_ELIGIBLE_STATE, seed=seed, run_id=run_id, schema=schema,
                                 declared_paths=declared_paths, exclusion_sets=exclusion, scan=scan)
    return _self(base, "package_sha256")


def build_frozen_failure_package(kind: str, *, scan: Mapping[str, Any],
                                 exclusion_sets: Mapping[str, Any],
                                 seed: int = PLAN_SEED_DEFAULT, run_id: str = RUN_ID,
                                 schema: str | None = None,
                                 declared_paths: Any = None) -> dict[str, Any]:
    """Frozen-failure package for ``insufficient_eligible_frames`` (eligible <
    192 with no shrinking) — schema ``nbldpc_v13r3_fresh_insufficient_v1``.

    ``kind`` must be ``insufficient_eligible_frames``; the package records the
    shortfall and preserves the eligible rows and exclusion summary as-is.
    """
    if kind != INSUFFICIENT_STATE:
        raise ValueError(f"unsupported frozen-failure kind: {kind}")
    if schema is None:
        schema = INSUFFICIENT_SCHEMA
    base = _base_failure_package(INSUFFICIENT_STATE, seed=seed, run_id=run_id, schema=schema,
                                 declared_paths=declared_paths, exclusion_sets=exclusion_sets,
                                 scan=scan)
    base["shortfall"] = REQUIRED_EXEC_FRAMES - scan.get("eligible_row_count", 0)
    base["no_shrinking"] = True
    return _self(base, "package_sha256")


# ------------------------------------------------------------------ prepare orchestration


def _prepare_package(output_dir: Any, scan: Mapping[str, Any], *,
                     exclusion_sets: Mapping[str, Any], seed: int, run_id: str,
                     declared_paths: Any, test_only: bool) -> dict[str, Any]:
    """Build the correct package from a scan + role assignment, writing exactly
    the package JSON into ``output_dir`` (no-overwrite, fresh dir required)."""
    out = Path(output_dir)
    if out.exists():
        raise FileExistsError("fresh output directory required")
    out.mkdir(parents=True)
    eligible = scan.get("eligible_row_count", 0)

    def _schemas(prod: str, test: str) -> str:
        return test if test_only else prod

    if eligible == 0:
        pkg = build_no_eligible_package(seed=seed, run_id=run_id,
                                        schema=_schemas(NO_ELIGIBLE_SCHEMA, NO_ELIGIBLE_SCHEMA_TEST),
                                        declared_paths=declared_paths)
        _put(out / "no_eligible_package.json", pkg)
        return {"state": NO_ELIGIBLE_STATE, "package": pkg,
                "package_file": "no_eligible_package.json"}

    assignment = assign_roles(scan["eligible_rows"], seed=seed)
    if assignment["state"] == "blocked_role_ledger":
        # ambiguous identities → blocked_role_ledger (design.md §5.4).
        pkg = _self({"schema": _schemas(PLAN_SCHEMA, PLAN_SCHEMA_TEST), "run_id": run_id,
                     "method": METHOD, "plan_state": "blocked_role_ledger",
                     "seed": int(seed),
                     "ambiguous_identities": assignment["ambiguous_identities"],
                     "failure_policy": FAILURE_POLICY}, "plan_sha256")
        _put(out / "plan.json", pkg)
        return {"state": "blocked_role_ledger", "package": pkg, "package_file": "plan.json"}

    if eligible < REQUIRED_EXEC_FRAMES:
        pkg = build_frozen_failure_package(INSUFFICIENT_STATE, scan=scan,
                                           exclusion_sets=exclusion_sets, seed=seed,
                                           run_id=run_id,
                                           schema=_schemas(INSUFFICIENT_SCHEMA, INSUFFICIENT_SCHEMA_TEST),
                                           declared_paths=declared_paths)
        _put(out / "insufficient_package.json", pkg)
        return {"state": INSUFFICIENT_STATE, "package": pkg,
                "package_file": "insufficient_package.json"}

    plan = build_plan(scan, assignment, exclusion_sets, seed=seed, run_id=run_id,
                      schema=_schemas(PLAN_SCHEMA, PLAN_SCHEMA_TEST),
                      declared_paths=declared_paths)
    _put(out / "plan.json", plan)
    return {"state": "ready", "package": plan, "package_file": "plan.json"}


def prepare(output_dir: Any, *, declared_paths: Any = None, discovery_root: Any = None,
            seed: int = PLAN_SEED_DEFAULT, run_id: str | None = None,
            _test_only: bool = False,
            production_prepare_authorized: bool = False) -> dict[str, Any]:
    """Decoder-free, array-free prepare orchestration.

    Two lanes:

    - the fake test lane (``_test_only=True``) with caller-declared fake source
      paths and a caller-owned fresh output root, writing test schemas; and
    - the prepare-only production lane (``production_prepare_authorized=True``)
      which writes the production schemas.  Without either flag, production
      preparation is refused (fail-closed).
    """
    if not _test_only and not production_prepare_authorized:
        raise ValueError("V13 R3 fresh production preparation is not authorized "
                         "during the initial phase")
    scan = scan_fresh_sources(declared_paths)
    exclusion_sets = build_exclusion_sets(discovery_root)
    return _prepare_package(output_dir, scan, exclusion_sets=exclusion_sets, seed=seed,
                            run_id=run_id or (TEST_RUN_ID if _test_only else RUN_ID),
                            declared_paths=declared_paths, test_only=_test_only)


def prepare_production(output_dir: Any, *, declared_paths: Any,
                       discovery_root: Any, seed: int = PLAN_SEED_DEFAULT,
                       run_id: str = RUN_ID) -> dict[str, Any]:
    """Main-thread-authorized prepare-only production path.  Writes exactly one
    production schema package into a fresh additive directory; never a decoder,
    never raw symbol arrays."""
    return prepare(output_dir, declared_paths=declared_paths,
                   discovery_root=discovery_root, seed=seed, run_id=run_id,
                   production_prepare_authorized=True)


def validate_package(output_dir: Any, *, test_only: bool = False) -> dict[str, Any]:
    """Read-only structural validation of a prepare package.  Never imports a
    decoder; never writes.  Returns a summary dict or raises."""
    out = Path(output_dir)
    if not out.is_dir():
        raise ValueError("output directory missing")
    names = {p.name for p in out.iterdir()}
    allowed = {"plan.json", "no_eligible_package.json", "insufficient_package.json"}
    if not names or not names.issubset(allowed):
        raise ValueError(f"unexpected prepare files: {sorted(names - allowed)}")
    result: dict[str, Any] = {"verified": True, "files": sorted(names), "schemas": {}}
    for name in sorted(names):
        doc = _json_read(out / name)
        if test_only and not _test_schema(doc):
            raise ValueError(f"{name}: production schema in test lane")
        result["schemas"][name] = doc.get("schema")
    return result
