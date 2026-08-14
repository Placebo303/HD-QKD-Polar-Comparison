"""V12 nonbinary LDPC real micro-feasibility: decoder-free exclusion inventory
and partition preparation acceptance (``formal-nonbinary-ldpc-v12-real-micro-feasibility``).

Covers the initially authorized V12-I03 engineering scope and the T0/T1/T2
partition tier: decoder-free/array-free module proof, fake discovery-root
inventory, required-minimum and unclassified-artifact rejection, canonical
first-four-bw200 selection after exclusion, ``source_partition_blocked``,
production preparation hard stops, and one complete fake partition+plan
preparation lifecycle under a fresh ``workspace/nbldpc_v12_tests_<uuid>``
root.  Never touches real sidecars, a real source loader, or an official
output root.
"""
from __future__ import annotations

import hashlib
import json
import sys
import uuid
from pathlib import Path

import pytest

from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v12_real_partition as partition


def _hex64(seed_text: str) -> str:
    return hashlib.sha256(seed_text.encode("ascii")).hexdigest()


def _out(name: str) -> Path:
    root = Path("workspace") / f"nbldpc_v12_tests_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root / name


def _fake_pool(n_bw200: int = 8, *, n_bw120: int = 2, n_bw180: int = 2) -> list[dict]:
    """Canonical-order fake identity pool (no arrays ever)."""
    rows: list[dict] = []
    for i in range(n_bw120):
        rows.append({"stratum": "d1024_bw120", "frame_id": i,
                     "frame_identity": _hex64(f"pool|bw120|{i}"),
                     "payload_identity": _hex64(f"pool|bw120|payload|{i}"),
                     "source_pair_start": i * 256, "source_pair_end": (i + 1) * 256,
                     "source_record_sha256": _hex64("pool|src|bw120")})
    offset = n_bw120
    for i in range(n_bw180):
        rows.append({"stratum": "d1024_bw180", "frame_id": i,
                     "frame_identity": _hex64(f"pool|bw180|{i}"),
                     "payload_identity": _hex64(f"pool|bw180|payload|{i}"),
                     "source_pair_start": (offset + i) * 256, "source_pair_end": (offset + i + 1) * 256,
                     "source_record_sha256": _hex64("pool|src|bw180")})
    offset = n_bw120 + n_bw180
    for i in range(n_bw200):
        rows.append({"stratum": "d1024_bw200", "frame_id": offset + i,
                     "frame_identity": _hex64(f"pool|bw200|{i}"),
                     "payload_identity": _hex64(f"pool|bw200|payload|{i}"),
                     "source_pair_start": (offset + i) * 256, "source_pair_end": (offset + i + 1) * 256,
                     "source_record_sha256": _hex64("pool|src|bw200")})
    return rows


def _bw200(rows: list[dict]) -> list[dict]:
    return [r for r in rows if r["stratum"] == "d1024_bw200"]


def _fake_discovery_root(root: Path, pool: list[dict], *, excluded_indices: tuple[int, ...] = (1, 3, 5)) -> None:
    """Fake historical real packages under ``root`` covering the excluded
    bw200 rows' identities; the required inventory is present.  Indices beyond
    the pool are ignored so small pools can be used for blocked-state tests."""
    bw = _bw200(pool)
    indices = [i for i in excluded_indices if i < len(bw)]

    def lock_frames(rows: list[dict]) -> list[dict]:
        return [{"stratum": r["stratum"], "frame_id": r["frame_id"],
                 "frame_identity": r["frame_identity"], "payload_identity": r["payload_identity"],
                 "source_pair_start": r["source_pair_start"], "source_pair_end": r["source_pair_end"],
                 "source_record_sha256": r["source_record_sha256"], "selection_rank": rank}
                for rank, r in enumerate(rows)]

    for name in ("20260729_v1_binary_ldpc_v4_10db_transfer",
                 "20260729_v2_binary_ldpc_v4_10db_transfer"):
        d = root / name
        d.mkdir(parents=True)
        doc = {"schema": "binary_ldpc_v4_10db_source_lock_v1",
               "selected_frames": lock_frames([bw[i] for i in indices[:2]])}
        (d / "real_data_lock.json").write_text(json.dumps(doc, sort_keys=True))
    d = root / "20260731_v1_binary_ldpc_v5_partition"
    d.mkdir(parents=True)
    role_rows: list[dict] = []
    if indices:
        row = bw[indices[-1]]
        role_rows = [{"role": "confirmation", "role_rank": 0, "partition_rank": 0, **{
            k: row[k] for k in ("stratum", "frame_id", "frame_identity", "payload_identity",
                                "source_pair_start", "source_pair_end", "source_record_sha256")}}]
    doc = {"schema": "binary_ldpc_v5_10db_partition_lock_v1", "role_rows": role_rows}
    (d / "partition_lock.json").write_text(json.dumps(doc, sort_keys=True))
    for name in ("20260727_v2_binary_ldpc_v4_development",
                 "20260728_v2_binary_ldpc_v4_synthetic"):
        (root / name).mkdir(parents=True)
    d = root / "20260729_v1_binary_ldpc_v4_16db_transfer"
    d.mkdir(parents=True)
    doc = {"schema": "binary_ldpc_v4_16db_source_lock_v1", "selected_frames": []}
    (d / "real_data_lock.json").write_text(json.dumps(doc, sort_keys=True))
    # An extra "all formal/final-IR real packages present" entry.
    d = root / "20990101_v1_some_other_real_package"
    d.mkdir(parents=True)
    doc = {"schema": "other_real_lock_v1", "selected_frames": lock_frames([bw[len(bw) - 1]])}
    (d / "real_data_lock.json").write_text(json.dumps(doc, sort_keys=True))


def _prepare(root: Path, pool: list[dict], *, excluded_indices: tuple[int, ...] = (1, 3, 5)) -> dict:
    discovery = root / "discovery"
    _fake_discovery_root(discovery, pool, excluded_indices=excluded_indices)
    out = root / "package"
    return partition.prepare(out, _test_only=True, discovery_root=discovery, pool_rows=pool,
                             run_id=partition.TEST_RUN_ID,
                             source_adapter="fake_adapter",
                             canonical_rule=partition.CANONICAL_RULE)


# ------------------------------------------------------------------ T0

def test_module_imports_and_frozen_contract():
    assert partition.METHOD == "nbldpc_formal_v12_r1_real_micro"
    assert partition.ARTIFACTS == ("exclusion_manifest.json", "partition_lock.json",
                                   "pre_run_plan.json", "real_frame_outcomes.csv",
                                   "real_transcript.jsonl", "real_run_manifest.json",
                                   "real_micro_report.json")
    assert partition.PREPARE_ARTIFACTS == partition.ARTIFACTS[:3]
    assert (partition.Q, partition.N, partition.M) == (1024, 256, 170)
    assert partition.SYNDROME_BITS == 1700 and partition.SEED_BITS == 2623
    assert partition.STRATUM == "d1024_bw200" and partition.ROLE == "sacrificed_real_canary"


def test_partition_module_is_decoder_free_and_array_free():
    """The partition module must not import a decoder or numpy, and must not
    reference any decoder/source-loader entry point."""
    source = Path(partition.__file__).read_text(encoding="utf8")
    assert "nonbinary_v7_r1a_long" not in source
    assert "nonbinary_v7_r1a_codebook" not in source
    assert "from .ldpc_v4_10db_source" not in source
    assert "import ldpc_v4_10db_source" not in source
    assert "confirmation_arrays" not in source
    assert "numpy" not in source
    assert "production_runner" not in source


# ------------------------------------------------------------------ T1

def test_fake_inventory_discovery_and_exclusion_manifest():
    root = _out("inventory")
    pool = _fake_pool()
    discovery = root / "discovery"
    _fake_discovery_root(discovery, pool)
    packages = partition.discover_packages(discovery)
    names = {p["name"] for p in packages}
    for required in partition.REQUIRED_PACKAGE_DIRS:
        assert required in names
    manifest = partition.build_exclusion_manifest(packages, run_id=partition.TEST_RUN_ID,
                                                  schema=partition.TEST_EXCLUSION_SCHEMA)
    partition.validate_exclusion_manifest(manifest)
    assert manifest["excluded_frame_identity_count"] >= 3
    # the v1/v2 real locks and the v5 partition roles are identity-bearing
    for record in packages:
        if record["name"] in partition._REAL_LOCK_PACKAGE_DIRS:
            assert record["frame_identity_count"] > 0
    # excluded identities include the covered bw200 rows 1, 3, 5
    excluded = set(manifest["excluded_frame_identities"])
    bw = _bw200(pool)
    for i in (1, 3, 5):
        assert bw[i]["frame_identity"] in excluded


def test_required_minimum_rejects_missing_package():
    root = _out("missing")
    pool = _fake_pool()
    discovery = root / "discovery"
    _fake_discovery_root(discovery, pool)
    (discovery / "20260729_v2_binary_ldpc_v4_10db_transfer").rename(
        discovery / "renamed_away")
    with pytest.raises(ValueError, match="missing local real package"):
        partition.discover_packages(discovery)


def test_incomplete_inventory_rejected():
    root = _out("incomplete")
    pool = _fake_pool()
    discovery = root / "discovery"
    _fake_discovery_root(discovery, pool)
    # strip the v5 partition lock identities
    (discovery / "20260731_v1_binary_ldpc_v5_partition" / "partition_lock.json").write_text(
        json.dumps({"schema": "binary_ldpc_v5_10db_partition_lock_v1", "role_rows": []}))
    with pytest.raises(ValueError, match="incomplete inventory"):
        partition.discover_packages(discovery)


def test_unclassified_identity_artifact_rejected():
    root = _out("unclassified")
    pool = _fake_pool()
    discovery = root / "discovery"
    _fake_discovery_root(discovery, pool)
    stray = discovery / "20260727_v2_binary_ldpc_v4_development" / "mystery.json"
    stray.write_text(json.dumps({"note": "unclassified", "frame_identity": _hex64("mystery")}))
    with pytest.raises(ValueError, match="unclassified identity-bearing artifact"):
        partition.discover_packages(discovery)


def test_partition_selects_first_four_complete_bw200_after_exclusion():
    root = _out("selection")
    pool = _fake_pool(n_bw200=8)
    res = _prepare(root, pool, excluded_indices=(1, 3, 5))
    lock = res["partition_lock"]
    assert lock["partition_state"] == "ready"
    selected = lock["selected_rows"]
    assert len(selected) == 4
    # canonical pool order: first four *eligible* bw200 rows (0, 2, 4, 6)
    bw = _bw200(pool)
    expected_ids = [bw[i]["frame_identity"] for i in (0, 2, 4, 6)]
    assert [r["frame_identity"] for r in selected] == expected_ids
    assert [r["role"] for r in selected] == ["sacrificed_real_canary"] * 4
    excluded_f = set(res["exclusion_manifest"]["excluded_frame_identities"])
    assert not any(r["frame_identity"] in excluded_f for r in selected)
    assert lock["selected_row_digest"] == partition._sha(partition._compact(
        [{k: r[k] for k in ("stratum", "frame_id", "frame_identity", "payload_identity")} for r in selected]))


def test_partition_state_source_partition_blocked():
    root = _out("blocked")
    # only 2 bw200 rows are eligible after exclusion (1, 3 excluded)
    pool = _fake_pool(n_bw200=4)
    res = _prepare(root, pool, excluded_indices=(1, 3, 5))
    lock = res["partition_lock"]
    assert lock["partition_state"] == "source_partition_blocked"
    # fewer than four collision-free rows can never form the partition
    assert len(lock["selected_rows"]) == 2
    assert lock["pool_summary"]["selected_rows"] == 2


def test_production_preparation_is_blocked_and_official_root_prepare_only():
    with pytest.raises(ValueError, match="production partition preparation is not authorized"):
        partition.prepare(_out("prod"), _test_only=False)
    # The only official v12 directories that may exist are prepare-only: the
    # main-thread-authorized production package holds exactly the three
    # preparation artifacts and never any execute artifact.
    official = Path("comparison_bench/outputs_comparison/formal_ir_methods")
    v12_dirs = [d for d in official.iterdir() if d.is_dir() and "v12" in d.name.lower()]
    for d in v12_dirs:
        assert {p.name for p in d.iterdir()} == set(partition.PREPARE_ARTIFACTS), d.name


def test_production_prepare_lane_writes_preparation_artifacts():
    """The main-thread-authorized prepare-only production lane writes the
    production-schema exclusion manifest and partition lock into a fresh
    directory; production prepare without the authorization flag stays a hard
    stop.  Runs in a fresh workspace root, never in the official package."""
    root = _out("prod_prepare")
    pool = _fake_pool(n_bw200=8)
    discovery = root / "discovery"
    _fake_discovery_root(discovery, pool, excluded_indices=(1, 3, 5))
    out = root / "package"
    res = partition.prepare(out, production_prepare_authorized=True,
                            discovery_root=discovery, pool_rows=pool,
                            run_id=partition.RUN_ID,
                            source_adapter=partition.SOURCE_ADAPTER,
                            canonical_rule=partition.CANONICAL_RULE)
    assert {p.name for p in out.iterdir()} == set(partition.PREPARE_ARTIFACTS[:2])
    assert res["partition_state"] == "ready"
    exclusion = partition._json_read(out / "exclusion_manifest.json")
    lock = partition._json_read(out / "partition_lock.json")
    assert exclusion["schema"] == partition.EXCLUSION_SCHEMA
    assert lock["schema"] == partition.PARTITION_SCHEMA
    assert exclusion["run_id"] == partition.RUN_ID
    assert exclusion["packages"][0]["classification"]
    partition.validate_exclusion_manifest(exclusion)
    partition.validate_partition_lock(lock, exclusion)
    # un-authorized production prepare remains blocked
    with pytest.raises(ValueError, match="production partition preparation is not authorized"):
        partition.prepare(out, _test_only=False)


def test_prepare_test_lane_writes_only_preparation_files():
    root = _out("prepare_only")
    pool = _fake_pool()
    res = _prepare(root, pool)
    out = root / "package"
    assert {p.name for p in out.iterdir()} == set(partition.PREPARE_ARTIFACTS[:2])
    assert res["partition_state"] == "ready"
    # both files are canonical JSON and reconstruct
    partition.validate_exclusion_manifest(partition._json_read(out / "exclusion_manifest.json"))
    partition.validate_partition_lock(partition._json_read(out / "partition_lock.json"),
                                      partition._json_read(out / "exclusion_manifest.json"))


def test_partition_lock_tamper_rejected():
    root = _out("tamper")
    pool = _fake_pool()
    _prepare(root, pool)
    out = root / "package"
    lock_path = out / "partition_lock.json"
    lock = json.loads(lock_path.read_bytes())
    lock["selected_rows"][0]["frame_identity"] = _hex64("forged")
    lock_path.write_bytes(partition._compact(lock))
    with pytest.raises(ValueError, match="partition (self hash|reconstruction)"):
        partition.validate_partition_lock(partition._json_read(lock_path),
                                          partition._json_read(out / "exclusion_manifest.json"))


def test_exclusion_manifest_tamper_rejected():
    root = _out("excl_tamper")
    pool = _fake_pool()
    _prepare(root, pool)
    out = root / "package"
    manifest_path = out / "exclusion_manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["excluded_frame_identities"].append(_hex64("forged"))
    manifest_path.write_bytes(partition._compact(manifest))
    with pytest.raises(ValueError, match="exclusion (self hash|reconstruction)"):
        partition.validate_exclusion_manifest(partition._json_read(manifest_path))


# ------------------------------------------------------------------ T2 (partition+plan preparation)

def test_complete_fake_partition_and_plan_preparation_replay(monkeypatch):
    """One complete fake four-frame preparation: exclusion inventory →
    partition lock → plan, with a plan-only read-only verification.  The
    verifier's plan path never imports or calls a decoder."""
    root = _out("t2_partition")
    pool = _fake_pool(n_bw200=8)
    res = _prepare(root, pool, excluded_indices=(1, 3, 5))
    assert res["partition_state"] == "ready"
    out = root / "package"
    from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v12_real_micro as micro
    frames = []
    for row in res["partition_lock"]["selected_rows"]:
        frames.append({"frame_id": int(row["frame_id"]), "stratum": row["stratum"],
                       "frame_identity": row["frame_identity"],
                       "payload_identity": row["payload_identity"],
                       "source_pair_start": row["source_pair_start"],
                       "source_pair_end": row["source_pair_end"],
                       "source_record_sha256": row["source_record_sha256"],
                       "dataset_id": f"real_10db_{row['stratum']}",
                       "alice": [0] * 256, "bob": [0] * 256})
    seeds = {f["frame_id"]: micro.materialize_seed_record(micro.SEED_BITS) for f in frames}
    plan = micro.create_plan(out, frames=frames, seeds=seeds, _test_only=True)
    assert {p.name for p in out.iterdir()} == set(partition.PREPARE_ARTIFACTS)
    assert plan["schema"] == micro.TEST_PLAN_SCHEMA
    assert plan["partition_binding"]["partition_state"] == "ready"
    # decoder is never imported by the plan path
    assert "nonbinary_v7_r1a_long" not in sys.modules
    # plan-only read-only verification (no decoder, no execute)
    result = micro.verify(out, _test_only=True)
    assert result["plan_only"] and result["run_status"] == "planned"
