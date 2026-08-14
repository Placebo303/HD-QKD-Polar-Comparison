"""V12 real micro-feasibility: decoder-free exclusion inventory and partition
preparation (``formal-nonbinary-ldpc-v12-real-micro-feasibility``).

This module owns the first two preparation artifacts of the exact seven-file
V12 package contract plus the shared V12 constants:

    exclusion_manifest.json   binds the reviewed package inventory and the
                              union of excluded frame/payload identities;
    partition_lock.json       binds the 10 dB source adapter and its
                              canonical-order rule plus the four selected rows.

Contracts (frozen by the V12 design):

- the module is deliberately **decoder-free and array-free**: it never imports
  a decoder, never loads ``a_eff.npy``/``b_eff.npy`` sidecars, never calls the
  real source adapter and never exposes V5 development/confirmation roles as
  candidates.  Only caller-supplied identity rows enter the partition rule.
- the minimum required inventory is the V4 10 dB v1/v2 real locks, the V5
  predecessor package set, and the V5 development/confirmation partition
  roles.  A missing local real package, an unclassified identity-bearing
  artifact, or an inventory with no identities in the real-lock packages is
  rejected before any partition is built.
- production preparation has two lanes: the fake test lane (``_test_only=True``
  with explicit fake discovery data and a fresh writable test root) and the
  main-thread-authorized prepare-only production lane
  (``production_prepare_authorized=True``, V12-RP01/RP02) which writes the
  production schemas from the real discovery inventory.  Neither lane can
  invoke a decoder; production decode/execute remains a hard stop elsewhere.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

METHOD = "nbldpc_formal_v12_r1_real_micro"
Q, N, M = 1024, 256, 170
STRATUM = "d1024_bw200"
STRATA = ("d1024_bw120", "d1024_bw180", "d1024_bw200")
P = 0.20
SYNDROME_BITS = M * 10  # 1700 key-dependent bits (full 170-check syndrome)
SEED_BITS = N * 10 + 63  # 2623-bit Toeplitz seed for the 2560-bit Gray word
TAG_BITS = 64
ROLE = "sacrificed_real_canary"
FRAME_COUNT = 4

# Exact seven-file package contract (design.md section 6).
ARTIFACTS = (
    "exclusion_manifest.json",
    "partition_lock.json",
    "pre_run_plan.json",
    "real_frame_outcomes.csv",
    "real_transcript.jsonl",
    "real_run_manifest.json",
    "real_micro_report.json",
)
# Prepare writes and reviews these three before any execute; none invokes a
# decoder (design.md section 6).
PREPARE_ARTIFACTS = ARTIFACTS[:3]

RUN_ID = "nbldpc_v12_real_micro"
TEST_RUN_ID = "nbldpc_v12_real_micro_test_v1"

EXCLUSION_SCHEMA = "nbldpc_v12_exclusion_manifest_v1"
PARTITION_SCHEMA = "nbldpc_v12_partition_lock_v1"
TEST_EXCLUSION_SCHEMA = "nbldpc_v12_exclusion_manifest_test_v1"
TEST_PARTITION_SCHEMA = "nbldpc_v12_partition_lock_test_v1"

# Design.md section 4: the minimum required local inventory.  The V4 10 dB
# v1/v2 real locks and the V5 partition roles are identity-bearing; the other
# V5 predecessor packages must at least be present and discovered.
REQUIRED_PACKAGE_DIRS = (
    "20260727_v2_binary_ldpc_v4_development",
    "20260728_v2_binary_ldpc_v4_synthetic",
    "20260729_v1_binary_ldpc_v4_16db_transfer",
    "20260729_v1_binary_ldpc_v4_10db_transfer",
    "20260729_v2_binary_ldpc_v4_10db_transfer",
    "20260731_v1_binary_ldpc_v5_partition",
)
_REAL_LOCK_PACKAGE_DIRS = (
    "20260729_v1_binary_ldpc_v4_10db_transfer",
    "20260729_v2_binary_ldpc_v4_10db_transfer",
    "20260731_v1_binary_ldpc_v5_partition",
)

SOURCE_ADAPTER = "comparison_bench.formal_ir.ldpc_v4_10db_source.build_source_lock"
CANONICAL_RULE = "first_four_complete_bw200_rows_in_canonical_full_pool_order_after_exclusion"
_IDENTITY_KEYS = ("frame_identity", "payload_identity")
# The 10 dB pool binds only the 10 dB source locks and the V5 10 dB partition
# roles.  The V4 16 dB lock reuses the same stratum strings but is a
# different acquisition: its rows stay in the exclusion manifest and never
# enter the 10 dB pool (V12 design section 4).
_10DB_LOCK_SCHEMAS = {
    "real_data_lock.json": "binary_ldpc_v4_10db_source_lock_v1",
    "partition_lock.json": "binary_ldpc_v5_10db_partition_lock_v1",
}


def _compact(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def _sha(value: Any) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else _compact(value)).hexdigest()


def _self(value: dict[str, Any], key: str) -> dict[str, Any]:
    return {**value, key: _sha(_compact(value))}


def _is_hex64(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _put(path: Path, value: Any) -> None:
    path.open("xb").write(_compact(value))


def _json_read(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    doc = json.loads(raw)
    if not isinstance(doc, dict) or _compact(doc) != raw:
        raise ValueError("noncanonical json")
    return doc


# ------------------------------------------------------------------ identity extraction

def _selected_frames_identities(doc: Any) -> tuple[list[str], list[str]]:
    """(frame_identities, payload_identities) of a ``real_data_lock.json``."""
    fids: list[str] = []
    pids: list[str] = []
    frames = doc.get("selected_frames", []) if isinstance(doc, Mapping) else []
    if isinstance(frames, list):
        for entry in frames:
            if not isinstance(entry, Mapping):
                continue
            if _is_hex64(entry.get("frame_identity")):
                fids.append(entry["frame_identity"])
            if _is_hex64(entry.get("payload_identity")):
                pids.append(entry["payload_identity"])
    return fids, pids


def _role_rows_identities(doc: Any) -> tuple[list[str], list[str]]:
    """(frame_identities, payload_identities) of a V5 ``partition_lock.json``."""
    fids: list[str] = []
    pids: list[str] = []
    rows = doc.get("role_rows", []) if isinstance(doc, Mapping) else []
    if isinstance(rows, list):
        for entry in rows:
            if not isinstance(entry, Mapping):
                continue
            if _is_hex64(entry.get("frame_identity")):
                fids.append(entry["frame_identity"])
            if _is_hex64(entry.get("payload_identity")):
                pids.append(entry["payload_identity"])
    return fids, pids


def _plan_identities(doc: Any) -> tuple[list[str], list[str]]:
    """(frame_identities, payload_identities) of a ``pre_run_plan.json`` that
    embeds a ``locked_data.selected_frames`` identity list."""
    fids: list[str] = []
    pids: list[str] = []
    locked = doc.get("locked_data") if isinstance(doc, Mapping) else None
    frames = locked.get("selected_frames") if isinstance(locked, Mapping) else None
    if isinstance(frames, list):
        for entry in frames:
            if not isinstance(entry, Mapping):
                continue
            if _is_hex64(entry.get("frame_identity")):
                fids.append(entry["frame_identity"])
            if _is_hex64(entry.get("payload_identity")):
                pids.append(entry["payload_identity"])
    return fids, pids


def _contains_identity_keys(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in _IDENTITY_KEYS and _is_hex64(item):
                return True
            if _contains_identity_keys(item):
                return True
    elif isinstance(value, list):
        return any(_contains_identity_keys(item) for item in value)
    return False


def _classify(name: str) -> str:
    """Per-entry classification for the exclusion inventory (V12-RP01)."""
    if "evaluation" in name:
        return "evaluation_only"
    if "10db_transfer" in name:
        return "v4_10db_transfer_lock"
    if "16db_transfer" in name:
        return "v4_16db_transfer_lock"
    if "v5_partition" in name:
        return "v5_partition_role"
    if "v5_development" in name:
        return "v5_development_role"
    if "v5_real" in name:
        return "v5_real_qualification"
    if "v5_synthetic" in name:
        return "v5_synthetic"
    if "synthetic" in name:
        return "synthetic"
    if "development" in name:
        return "development"
    if "real_cascade" in name:
        return "real_cascade"
    return "formal_package"


def _discover_package(d: Path) -> dict[str, Any]:
    """Read-only identity scan of one package directory.  Never loads arrays."""
    fids: list[str] = []
    pids: list[str] = []
    lock_files: list[dict[str, Any]] = []
    for name in ("real_data_lock.json", "partition_lock.json"):
        path = d / name
        if path.is_file():
            doc = json.loads(path.read_bytes())
            if name == "real_data_lock.json":
                f, p = _selected_frames_identities(doc)
            else:
                f, p = _role_rows_identities(doc)
            fids += f
            pids += p
            lock_files.append({"name": name, "sha256": _sha(path.read_bytes()),
                               "bytes": path.stat().st_size,
                               "frame_identity_count": len(set(f)),
                               "payload_identity_count": len(set(p))})
    for path in sorted(d.iterdir()):
        if not path.is_file() or path.suffix != ".json":
            continue
        if path.name in ("real_data_lock.json", "partition_lock.json"):
            continue
        try:
            doc = json.loads(path.read_bytes())
        except (OSError, ValueError):
            continue
        if path.name == "pre_run_plan.json":
            f, p = _plan_identities(doc)
            fids += f
            pids += p
            # Any identity keys outside the bounded locked_data shape are
            # unclassified identity-bearing material and abort the inventory.
            remaining = {k: v for k, v in doc.items() if k != "locked_data"} if isinstance(doc, Mapping) else doc
            if _contains_identity_keys(remaining):
                raise ValueError(f"unclassified identity-bearing artifact: {path}")
        elif _contains_identity_keys(doc):
            raise ValueError(f"unclassified identity-bearing artifact: {path}")
    return {"name": d.name, "path": str(d.resolve()), "classification": _classify(d.name),
            "lock_files": lock_files,
            "frame_identities": sorted(set(fids)), "payload_identities": sorted(set(pids)),
            "frame_identity_count": len(set(fids)), "payload_identity_count": len(set(pids))}


def discover_packages(root: Any) -> list[dict[str, Any]]:
    """Discover every locally discoverable real package under ``root``.

    Read-only identity scan: only lock/plan JSON metadata is parsed, no frame
    arrays, no source adapter, no decoder.  ``root`` may be a single path or a
    sequence of discovery roots (the combined inventory is validated).  Raises
    on a missing discovery root, an unclassified identity-bearing artifact, or
    an incomplete required inventory.
    """
    roots = [Path(r) for r in root] if isinstance(root, (list, tuple)) else [Path(root)]
    for r in roots:
        if not r.is_dir():
            raise ValueError("discovery root missing")
    packages: list[dict[str, Any]] = []
    for r in roots:
        packages += [_discover_package(d) for d in sorted(p for p in r.iterdir() if p.is_dir())]
    validate_inventory(packages)
    return packages


def build_traceable_pool(discovery_root: Any) -> list[dict[str, Any]]:
    """Reconstruct the complete traceable 10 dB pool in canonical full-pool
    order (stratum-major, frame_id ascending, exactly the source adapter's
    ``ldpc_v4_10db_source`` row semantics).

    Decoder-free and array-free: reads only ``real_data_lock.json`` /
    ``partition_lock.json`` metadata and binds the identity rows they expose;
    duplicate identities (e.g. the byte-identical V4 v1/v2 locks or the V5
    development copy of the V5 partition lock) are kept once.  Rows whose
    identities cannot be traced from manifests never enter the pool.
    """
    root = Path(discovery_root)
    if not root.is_dir():
        raise ValueError("discovery root missing")
    seen: set[tuple[str, str]] = set()
    rows: list[dict[str, Any]] = []
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        for name in ("real_data_lock.json", "partition_lock.json"):
            path = d / name
            if not path.is_file():
                continue
            try:
                doc = json.loads(path.read_bytes())
            except (OSError, ValueError):
                continue
            if not isinstance(doc, Mapping) or doc.get("schema") != _10DB_LOCK_SCHEMAS[name]:
                continue
            entries = doc.get("selected_frames") if name == "real_data_lock.json" else doc.get("role_rows")
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, Mapping):
                    continue
                row = {key: entry.get(key) for key in
                       ("stratum", "frame_id", "frame_identity", "payload_identity",
                        "source_pair_start", "source_pair_end", "source_record_sha256")}
                if row["stratum"] not in STRATA or any(v is None for v in row.values()):
                    continue
                key = (row["frame_identity"], row["payload_identity"])
                if key in seen:
                    continue
                seen.add(key)
                rows.append(row)
    order = {"d1024_bw120": 0, "d1024_bw180": 1, "d1024_bw200": 2}
    return sorted(rows, key=lambda r: (order[r["stratum"]], int(r["frame_id"])))


def validate_inventory(packages: Any) -> None:
    """Reject a missing local real package or an identity-less real lock."""
    if not isinstance(packages, list):
        raise ValueError("package inventory")
    by_name = {p.get("name"): p for p in packages if isinstance(p, Mapping)}
    missing = [name for name in REQUIRED_PACKAGE_DIRS if name not in by_name]
    if missing:
        raise ValueError(f"missing local real package: {sorted(missing)}")
    for name in _REAL_LOCK_PACKAGE_DIRS:
        record = by_name[name]
        if record.get("frame_identity_count", 0) == 0 and record.get("payload_identity_count", 0) == 0:
            raise ValueError(f"incomplete inventory: {name} carries no identities")


# ------------------------------------------------------------------ exclusion manifest

def build_exclusion_manifest(packages: Any, *, run_id: str, schema: str) -> dict[str, Any]:
    """Bind the reviewed package inventory and the union of excluded
    frame/payload identities."""
    validate_inventory(packages)
    fids: list[str] = []
    pids: list[str] = []
    for record in packages:
        if not isinstance(record, Mapping):
            raise ValueError("package record")
        fids += record.get("frame_identities", [])
        pids += record.get("payload_identities", [])
    excluded_f = sorted(set(fids))
    excluded_p = sorted(set(pids))
    base = {"schema": schema, "run_id": run_id, "package_count": len(packages),
            "packages": packages,
            "excluded_frame_identity_count": len(excluded_f),
            "excluded_payload_identity_count": len(excluded_p),
            "excluded_frame_identities_sha256": _sha(_compact(excluded_f)),
            "excluded_payload_identities_sha256": _sha(_compact(excluded_p)),
            "excluded_frame_identities": excluded_f,
            "excluded_payload_identities": excluded_p}
    return _self(base, "exclusion_sha256")


def validate_exclusion_manifest(manifest: Any) -> dict[str, Any]:
    if not isinstance(manifest, Mapping):
        raise ValueError("exclusion manifest")
    supplied = dict(manifest)
    digest = supplied.pop("exclusion_sha256", None)
    if not _is_hex64(digest) or _sha(_compact(supplied)) != digest:
        raise ValueError("exclusion self hash")
    rebuilt = build_exclusion_manifest(manifest["packages"], run_id=manifest["run_id"],
                                       schema=manifest["schema"])
    if dict(manifest) != rebuilt:
        raise ValueError("exclusion reconstruction")
    return dict(manifest)


# ------------------------------------------------------------------ partition lock

def _identity_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Canonical identity-only row; the V12 selection never carries arrays."""
    required = {"stratum", "frame_id", "frame_identity", "payload_identity",
                "source_pair_start", "source_pair_end", "source_record_sha256"}
    missing = required.difference(row)
    if missing:
        raise ValueError(f"pool row missing fields: {sorted(missing)}")
    if row["stratum"] not in {"d1024_bw120", "d1024_bw180", "d1024_bw200"}:
        raise ValueError("pool row stratum")
    if isinstance(row["frame_id"], bool) or not isinstance(row["frame_id"], int) or row["frame_id"] < 0:
        raise ValueError("pool row frame id")
    if not (_is_hex64(row.get("frame_identity")) and _is_hex64(row.get("payload_identity"))):
        raise ValueError("pool row identities")
    start, end = row.get("source_pair_start"), row.get("source_pair_end")
    if isinstance(start, bool) or isinstance(end, bool) or not isinstance(start, int) or not isinstance(end, int) \
            or start < 0 or end - start != N:
        raise ValueError("pool row pair bounds")
    return {key: row[key] for key in required}


def build_partition_lock(pool_rows: Any, exclusion: Mapping[str, Any], *, run_id: str,
                         schema: str, source_adapter: str, canonical_rule: str) -> dict[str, Any]:
    """Select the first four complete, collision-free bw200 rows in canonical
    pool order after exclusion.  Decoder-free: only identity rows are used."""
    if not isinstance(exclusion, Mapping) or not _is_hex64(exclusion.get("exclusion_sha256")):
        raise ValueError("exclusion binding")
    if not isinstance(pool_rows, list):
        raise ValueError("pool rows")
    excluded_f = set(exclusion.get("excluded_frame_identities", []))
    excluded_p = set(exclusion.get("excluded_payload_identities", []))
    pool: list[dict[str, Any]] = []
    eligible: list[dict[str, Any]] = []
    for row in pool_rows:
        identity = _identity_row(row)
        pool.append(identity)
        if identity["stratum"] != STRATUM:
            continue
        if identity["frame_identity"] in excluded_f or identity["payload_identity"] in excluded_p:
            continue
        eligible.append(dict(identity, role=ROLE))
    selected = [dict(row) for row in eligible[:FRAME_COUNT]]
    state = "ready" if len(selected) == FRAME_COUNT else "source_partition_blocked"
    base = {"schema": schema, "run_id": run_id,
            "source_binding": {"source_adapter": source_adapter, "canonical_rule": canonical_rule},
            "exclusion_binding": {"exclusion_sha256": exclusion["exclusion_sha256"],
                                  "excluded_frame_identity_count": len(excluded_f),
                                  "excluded_payload_identity_count": len(excluded_p)},
            "pool_summary": {"pool_rows": len(pool), "eligible_bw200_rows": len(eligible),
                             "selected_rows": len(selected)},
            "pool_rows": pool, "eligible_rows": eligible, "selected_rows": selected,
            "partition_state": state,
            "selected_row_digest": _sha(_compact([{k: r[k] for k in
                                                  ("stratum", "frame_id", "frame_identity", "payload_identity")}
                                                 for r in selected]))}
    return _self(base, "partition_sha256")


def validate_partition_lock(lock: Any, exclusion: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(lock, Mapping):
        raise ValueError("partition lock")
    supplied = dict(lock)
    digest = supplied.pop("partition_sha256", None)
    if not _is_hex64(digest) or _sha(_compact(supplied)) != digest:
        raise ValueError("partition self hash")
    binding = lock["source_binding"]
    rebuilt = build_partition_lock(lock["pool_rows"], exclusion, run_id=lock["run_id"],
                                   schema=lock["schema"], source_adapter=binding["source_adapter"],
                                   canonical_rule=binding["canonical_rule"])
    if dict(lock) != rebuilt:
        raise ValueError("partition reconstruction")
    if lock["exclusion_binding"]["exclusion_sha256"] != exclusion["exclusion_sha256"]:
        raise ValueError("partition exclusion binding")
    return dict(lock)


# ------------------------------------------------------------------ preparation

def prepare(output_dir: Any, *, _test_only: bool = False, production_prepare_authorized: bool = False,
            discovery_root: Any = None, pool_rows: Any = None, run_id: str | None = None,
            source_adapter: str | None = None, canonical_rule: str | None = None) -> dict[str, Any]:
    """Write ``exclusion_manifest.json`` and ``partition_lock.json`` into a
    fresh directory (decoder-free).

    Two preparation lanes exist:

    - the fake test lane (``_test_only=True``) with caller-supplied fake
      discovery root and identity pool, writing the test schemas; and
    - the prepare-only production lane (``production_prepare_authorized=True``,
      main-thread authorized for V12-RP01/RP02) which writes the production
      schemas from a real discovery inventory.  Neither lane can call a
      decoder; production decode/execute remains a hard stop elsewhere.
    """
    if not _test_only and not production_prepare_authorized:
        raise ValueError("V12 production partition preparation is not authorized during the initial phase")
    if discovery_root is None or pool_rows is None or run_id is None \
            or source_adapter is None or canonical_rule is None:
        raise ValueError("partition preparation requires explicit discovery "
                         "root, pool rows, run id, adapter and rule")
    out = Path(output_dir)
    if out.exists():
        raise FileExistsError("fresh output directory required")
    packages = discover_packages(discovery_root)
    exclusion = build_exclusion_manifest(packages, run_id=run_id,
                                         schema=TEST_EXCLUSION_SCHEMA if _test_only else EXCLUSION_SCHEMA)
    validate_exclusion_manifest(exclusion)
    lock = build_partition_lock(list(pool_rows), exclusion, run_id=run_id,
                                schema=TEST_PARTITION_SCHEMA if _test_only else PARTITION_SCHEMA,
                                source_adapter=source_adapter, canonical_rule=canonical_rule)
    validate_partition_lock(lock, exclusion)
    out.mkdir(parents=True)
    _put(out / "exclusion_manifest.json", exclusion)
    _put(out / "partition_lock.json", lock)
    return {"exclusion_manifest": exclusion, "partition_lock": lock,
            "partition_state": lock["partition_state"]}
