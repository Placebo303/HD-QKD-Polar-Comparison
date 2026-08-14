"""T0-T2 tests for the v1 binary LDPC v5 real qualification package.

T0 structural/tiny-math, T1 focused unit/tamper, T2 complete fake-only
package plus strict read-only replay. Every package materialization uses a fresh
additive workspace root and explicit fakes; production entry points are never
invoked with real data and the official real directory is never touched.
"""
from __future__ import annotations

import hashlib
import json
import logging
import shutil
import uuid
from pathlib import Path
from typing import Any, Mapping
from unittest.mock import patch

import numpy as np
import pytest

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

from comparison_bench.src.comparison_bench.formal_ir import ldpc_v5_real_qualification as core
from comparison_bench.src.comparison_bench.formal_ir import ldpc_v5_confirmation_arrays as confirm
from comparison_bench.src.comparison_bench.formal_ir import ldpc_v5 as ldpc_v5_mod
from comparison_bench.src.comparison_bench.formal_ir.ldpc_v5 import (METHOD, OUTCOME_FIELDS,
                                                                     decode_outcome_csv_v5)
from comparison_bench.src.comparison_bench.cli import run_ldpc_v5_real_qualification as run_cli
from comparison_bench.src.comparison_bench.cli import verify_ldpc_v5_real_qualification as verify_cli

ROOT = Path(__file__).resolve().parents[2]

# ---------- lock stratum mapping ----------
# Real lock has d1024_* prefixed stratum names; public names are bw120/bw180/bw200
_LOCK_STRATA = ("d1024_bw120", "d1024_bw180", "d1024_bw200")
_LOCK_TO_PUB = dict(zip(_LOCK_STRATA, core.REAL_STRATA))
_PUB_TO_LOCK = {v: k for k, v in _LOCK_TO_PUB.items()}


# ---------- fake lock builder ----------

def _fake_lock(lock_sha: str = "aa" * 32, confirm_count: int = 128) -> dict[str, Any]:
    """Build a fake partition lock with d1024_* stratum names, 3 × confirm_count rows."""
    rows = []
    for rank_i in range(len(_LOCK_STRATA) * confirm_count):
        stratum_idx = rank_i // confirm_count
        frame_rank = rank_i % confirm_count
        rows.append({
            "stratum": _LOCK_STRATA[stratum_idx],
            "frame_id": 500 + rank_i,  # arbitrary non-contiguous frame IDs
            "frame_identity": hashlib.sha256(f"fid_{rank_i}".encode()).hexdigest(),
            "partition_rank": frame_rank,
            "payload_identity": hashlib.sha256(f"pid_{rank_i}".encode()).hexdigest(),
            "ranking_sha256": hashlib.sha256(f"rank_{rank_i}".encode()).hexdigest(),
            "role": "confirmation",
            "role_rank": frame_rank,
            "source_pair_start": frame_rank * 256,
            "source_pair_end": frame_rank * 256 + 256,
            "source_record_sha256": hashlib.sha256(f"src_{rank_i}".encode()).hexdigest(),
        })
    return {
        "partition_sha256": lock_sha,
        "role_rows": rows,
    }


# ---------- fake frame arrays ----------

_FAKE_RNG = np.random.default_rng(42)

def _fake_arrays_for_row(row: Mapping) -> tuple[np.ndarray, np.ndarray]:
    """Deterministic fake arrays based on row identity (stable across calls)."""
    seed = int(hashlib.sha256(
        f"{row['stratum']}|{row['frame_id']}|{row.get('role_rank', 0)}".encode()
    ).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    return (rng.integers(0, core.Q, size=core.N, dtype=np.uint16),
            rng.integers(0, core.Q, size=core.N, dtype=np.uint16))


# ---------- shared singleton fake arrays map ----------
# ponytail: module-level lazy singleton — both _execute_with_fakes and _fake_deps
# must patch confirmation_arrays_for_frame with the *same* side_effect so that
# the arrays written during execute match the arrays reconstructed during verify.

_SHARED_FAKE_ARRAYS_MAP: dict | None = None

def _build_shared_fake_arrays_map() -> dict:
    global _SHARED_FAKE_ARRAYS_MAP
    if _SHARED_FAKE_ARRAYS_MAP is None:
        real_lock = core._json_read(core.PARTITION_LOCK)
        _SHARED_FAKE_ARRAYS_MAP = {}
        for row in confirm.confirmation_rows(real_lock):
            a, b = _fake_arrays_for_row(row)
            _SHARED_FAKE_ARRAYS_MAP[(row["stratum"], row["frame_id"])] = (a, b)
    return _SHARED_FAKE_ARRAYS_MAP

def _shared_patched_arrays(lock_map, row):
    """Shared fake confirmation arrays — deterministic, same map for execute and verify."""
    m = _build_shared_fake_arrays_map()
    return m[(row["stratum"], row["frame_id"])]


# ---------- fake development bundle ----------

def _fake_dev_bundle(private: bool = True) -> dict[str, Any]:
    """Minimal fake development bundle for testing."""
    policy = {"candidates": [{"candidate_id": "V5-C2", "some_policy": True}],
              "manifest_sha256": "0" * 64}
    codebook = {"manifest": True, "sha256": "cc" * 32}
    selection = {"plane_selections": [{"candidate_id": "V5-C2"}],
                 "channel_model_sha256": "ee" * 32,
                 "codebook_manifest_sha256": "cc" * 32,
                 "method_id": "ldpc_formal_v4",
                 "schema": "binary_ldpc_v4_selection_v1",
                 "selection_sha256": "dd" * 32}
    channel = {"probabilities": {}, "sha256": "ee" * 32}
    h2 = {"manifest": True, "sha256": "ff" * 32}
    return {
        "path": "/fake/dev",
        "verification": {"status": "verified", "run_status": "completed",
                         "selected_candidate_id": "V5-C2", "ready_for_synthetic_prepare": True,
                         "decoder_reexecution": False},
        "hashes": {
            "formal_codebook_manifest.json": core._sha(core._compact(codebook)),
            "formal_selection_manifest.json": core._sha(core._compact(selection)),
            "formal_channel_model.json": core._sha(core._compact(channel)),
            "v5_h2_manifest.json": core._sha(core._compact(h2)),
            "v5_policy_manifest.json": core._sha(core._compact(policy)),
        },
        "docs": {
            "formal_codebook_manifest.json": codebook,
            "formal_selection_manifest.json": selection,
            "formal_channel_model.json": channel,
            "v5_h2_manifest.json": h2,
            "v5_policy_manifest.json": policy,
        },
        "selected": ["V5-C2"],
        "candidate_policy": policy["candidates"][0],
    }


def _fake_syn_bundle() -> dict[str, Any]:
    report = {"run_status": "completed", "ready_for_real_qualification": True}
    return {
        "path": "/fake/syn",
        "verification": report,
        "hashes": {"synthetic_qualification_report.json": core._sha(core._compact(report))},
    }


# ---------- fake runner factory ----------

def _make_fake_runner(outcome_status: str = "backend_unavailable", *,
                      fail_at: int | None = None, fail_exception: bool = False,
                      cap_seconds: float | None = None):
    """Return a fake method runner. outcome_status applied to every frame."""
    def runner(alice, bob, **kwargs):
        if fail_exception and fail_at is not None:
            raise RuntimeError("fake decode failure")
        attempt_id = kwargs.get("frame_id", "")
        if cap_seconds is not None:
            pass  # handled via time mock
        outcome = {
            "dataset_id": kwargs.get("dataset_id", ""),
            "frame_id": attempt_id, "n_pairs": core.N,
            "pair_idx_sequence_sha256": core._sha(core._compact([])),
            "method": METHOD, "candidate_id": core.CANDIDATE,
            "attempted": outcome_status not in ("backend_unavailable", "invalid_input"),
            "denominator_included": outcome_status not in ("backend_unavailable", "invalid_input"),
            "status": outcome_status, "failure_reason": "",
            "dimension": core.Q, "frame_len_symbols": core.N, "raw_ser": 0.0,
            "fallback_invoked": False, "rounds_attempted": 1,
            "verification_invoked": False,
            "verification_seed_id_round0": "", "verification_seed_id_round1": "",
            "verification_tag_bits": 0, "epsilon_ec": 0.0,
            "key_dependent_disclosure_bits_total": 0, "public_control_bits_total": 0,
            "transcript_first_event_id": None, "transcript_last_event_id": None,
            "transcript_sha256": core._sha(b""), "runtime_s": 0.0,
            "decoder_call_count": 0, "verification_check_count": 0,
            "ldpc_syndrome_bits": 0, "h1_syndrome_bits": 0, "h2_syndrome_bits": 0,
            "verification_tag_bits_component": 0, "feedback_control_bits": 0,
            "selection_sha256": "", "channel_model_sha256": "",
            "h1_codebook_manifest_sha256": "", "h2_manifest_sha256": "",
            "policy_sha256": "", "mapping": core.MAPPING,
            "leakage_comparison_policy": "method_specific_not_cross_ranked",
            "backend_name": "", "backend_version": "",
        }
        return {"outcome": outcome, "events": []}
    return runner


def _make_success_runner():
    """Fake runner that returns verified_success for every frame."""
    def runner(alice, bob, **kwargs):
        attempt_id = kwargs.get("frame_id", "")
        outcome = {
            "dataset_id": kwargs.get("dataset_id", ""),
            "frame_id": attempt_id, "n_pairs": core.N,
            "pair_idx_sequence_sha256": core._sha(core._compact([])),
            "method": METHOD, "candidate_id": core.CANDIDATE,
            "attempted": True, "denominator_included": True,
            "status": "verified_success", "failure_reason": "",
            "dimension": core.Q, "frame_len_symbols": core.N, "raw_ser": 0.0,
            "fallback_invoked": False, "rounds_attempted": 1,
            "verification_invoked": True,
            "verification_seed_id_round0": "s0", "verification_seed_id_round1": "s1",
            "verification_tag_bits": 0, "epsilon_ec": 0.0,
            "key_dependent_disclosure_bits_total": 0, "public_control_bits_total": 0,
            "transcript_first_event_id": None, "transcript_last_event_id": None,
            "transcript_sha256": core._sha(b""), "runtime_s": 0.0,
            "decoder_call_count": 1, "verification_check_count": 0,
            "ldpc_syndrome_bits": 0, "h1_syndrome_bits": 0, "h2_syndrome_bits": 0,
            "verification_tag_bits_component": 0, "feedback_control_bits": 0,
            "selection_sha256": "", "channel_model_sha256": "",
            "h1_codebook_manifest_sha256": "", "h2_manifest_sha256": "",
            "policy_sha256": "", "mapping": core.MAPPING,
            "leakage_comparison_policy": "method_specific_not_cross_ranked",
            "backend_name": "", "backend_version": "",
        }
        return {"outcome": outcome, "events": []}
    return runner


# ---------- test helper: prepare+execute with fakes ----------

def _prepare_test_with_fakes(output_dir: Path, lock: dict | None = None) -> dict:
    """Build a test plan using fakes for dev/syn/lock, write to output_dir."""
    if lock is None:
        # Use the real lock's confirmation rows for frame IDs (since _execute reads from real lock path)
        real_lock = core._json_read(core.PARTITION_LOCK)
        lock = real_lock
    dev = _fake_dev_bundle(private=True)
    syn = _fake_syn_bundle()
    roots = core._new_roots()
    # Create minimal fake dev and syn dirs with required plan files
    fake_dev_dir = output_dir.parent / "fake_dev"
    fake_dev_dir.mkdir(parents=True, exist_ok=True)
    fake_dev_plan = {
        "seed_schedule": {
            "roots": [{"root_hex": "ab" * 32, "candidate_id": "V5-C2",
                        "stratum": "bw120", "verification_round": 0}] * 18
        }
    }
    (fake_dev_dir / "pre_run_plan.json").write_bytes(core._compact(fake_dev_plan))
    fake_syn_dir = output_dir.parent / "fake_syn"
    fake_syn_dir.mkdir(parents=True, exist_ok=True)
    # Synthetic plan needs generator.roots with toeplitz keys
    fake_syn_roots = {}
    for s in ("adjacent_nominal", "adjacent_stress_125"):
        fake_syn_roots[s] = {
            "bob": {"root_hex": "01" * 32, "root_id": core._sha(bytes.fromhex("01" * 32))},
            "delta": {"root_hex": "02" * 32, "root_id": core._sha(bytes.fromhex("02" * 32))},
            "toeplitz_r0": {"root_hex": "03" * 32, "root_id": core._sha(bytes.fromhex("03" * 32)),
                            "verification_round": 0},
            "toeplitz_r1": {"root_hex": "04" * 32, "root_id": core._sha(bytes.fromhex("04" * 32)),
                            "verification_round": 1},
        }
    fake_syn_plan = {"generator": {"roots": fake_syn_roots}}
    syn_plan_path = fake_syn_dir / "pre_run_plan.json"
    syn_plan_path.write_bytes(core._compact(fake_syn_plan))
    (fake_syn_dir / "synthetic_qualification_report.json").write_bytes(core._compact(
        {"run_status": "completed", "ready_for_real_qualification": True}))
    # _seed_schedule expects the synthetic package DIRECTORY (same convention as
    # development_dir and the production call site); it reads pre_run_plan.json inside.
    fake_syn_dir = syn_plan_path.parent

    fake_dev_roots = {"count": 18, "roots_sha256": "dev_roots" + "0" * 57,
                      "roots": ["ab" * 32 for _ in range(18)]}
    fake_dev_seeds = {"count": 18 * 512,
                      "seed_ids_sha256": "dev_seeds" + "0" * 55,
                      "seed_ids": [f"dev_seed_{i}" for i in range(18 * 512)]}
    with patch.object(core, "_development_root_digest", return_value=fake_dev_roots), \
         patch.object(core, "_development_seed_digest", return_value=fake_dev_seeds), \
         patch.object(core, "_load_synthetic", return_value=syn), \
         patch.object(core, "load_development", return_value=dev):
        schedule = core._seed_schedule(roots, lock, private=True,
                                       development_dir=fake_dev_dir,
                                       synthetic_dir=fake_syn_dir)
    attempt_ids = core._attempt_ids(lock)
    # Use the actual fake dir paths (not the fake_dev_bundle paths which don't exist)
    dev["path"] = str(fake_dev_dir.resolve())
    syn["path"] = str(fake_syn_dir.resolve())
    base = {"schema": core.TEST_PLAN_SCHEMA, "run_id": core.TEST_RUN_ID,
            "method_id": METHOD, "role": core.ROLE,
            "domain": {"dimension": core.Q, "frame_len_symbols": core.N,
                       "mapping": core.MAPPING, "candidate": core.CANDIDATE,
                       "strata": list(core.REAL_STRATA),
                       "frame_count_per_stratum": core.FRAMES_PER_STRATUM},
            "execution": {"order": "stratum_frame", "attempt_ids": attempt_ids,
                          "attempt_ids_sha256": core._sha(core._compact(attempt_ids))},
            "output_binding": {"output_directory": output_dir.resolve().relative_to(ROOT).as_posix(),
                               "artifact_names": list(core.ARTIFACTS),
                               "prepare_file_set": [core.ARTIFACTS[0]]},
            "development_binding": {"path": dev["path"], "artifact_hashes": dev["hashes"],
                                     "selected_candidate_id": core.CANDIDATE,
                                     "ready_for_synthetic_prepare": True,
                                     "development_run_status": "completed",
                                     "codebook_manifest_sha256": dev["hashes"]["formal_codebook_manifest.json"],
                                     "selection_manifest_sha256": dev["hashes"]["formal_selection_manifest.json"],
                                     "channel_model_sha256": dev["hashes"]["formal_channel_model.json"],
                                     "h2_manifest_sha256": dev["hashes"]["v5_h2_manifest.json"],
                                     "policy_manifest_sha256": dev["hashes"]["v5_policy_manifest.json"],
                                     "codebook": dev["docs"]["formal_codebook_manifest.json"],
                                     "selection": dev["docs"]["formal_selection_manifest.json"],
                                     "channel_model": dev["docs"]["formal_channel_model.json"],
                                     "h2_manifest": dev["docs"]["v5_h2_manifest.json"],
                                     "policy_manifest": dev["docs"]["v5_policy_manifest.json"]},
            "partition_binding": {"lock_path": str(core.PARTITION_LOCK.resolve()),
                                  "partition_sha256": lock["partition_sha256"],
                                  "confirmation_row_digest": core._sha(core._compact(confirm.confirmation_rows(lock))),
                                  "confirmation_count_per_stratum": core.FRAMES_PER_STRATUM,
                                  "confirmation_access_api": "confirmation_arrays_for_frame"},
            "synthetic_binding": {"path": syn["path"],
                                   "report_sha256": syn["hashes"]["synthetic_qualification_report.json"],
                                   "ready_for_real_qualification": True},
             "generator": {},
            "seed_schedule": schedule,
            "gates": {"denominator_per_stratum": core.FRAMES_PER_STRATUM,
                      "successes_per_stratum": core.GATE_SUCCESSES,
                      "forbidden_failure_count_limit": 0, "strata": list(core.REAL_STRATA)},
            "caps": {"complete_run_s": core.COMPLETE_RUN_CAP_S, "per_frame_wall_s": 10.0,
                     "per_frame_decoder_calls": 20, "per_frame_events": 32},
            "failure_policy": core.FAILURE_POLICY,
            "scoped_source_sha256": core._hashes(),
            "environment": core._environment(True)}
    plan = core._self(base, "plan_sha256")
    if output_dir.exists():
        raise FileExistsError("fresh output directory required")
    output_dir.mkdir(parents=True)
    core._json(output_dir / core.ARTIFACTS[0], plan)
    return plan


def _execute_with_fakes(output_dir: Path, runner) -> None:
    """Execute a test plan with a fake runner and fake confirmation arrays."""
    # Bypass _validate_plan's expensive reads by just checking identity
    def _fast_validate(plan, *, test_only, output_dir):
        if plan.get("schema") != (core.TEST_PLAN_SCHEMA if test_only else core.PLAN_SCHEMA):
            raise ValueError("plan identity")
        return dict(plan)

    with patch.object(confirm, "confirmation_arrays_for_frame", side_effect=_shared_patched_arrays), \
         patch.object(core, "confirmation_arrays_for_frame", side_effect=_shared_patched_arrays), \
         patch.object(core, "_validate_plan", side_effect=_fast_validate), \
         patch.object(core, "verify_public_payload_v5", return_value={"status": "verified"}):
        core._execute_test_plan(output_dir, runner)


def _build_fake_package(output_dir: Path, runner) -> Path:
    """Full prepare + execute with fakes, returns the output dir."""
    _prepare_test_with_fakes(output_dir)
    _execute_with_fakes(output_dir, runner)
    return output_dir


from contextlib import contextmanager

@contextmanager
def _fake_deps():
    """Context manager that patches all dev/syn/lock deps for the verifier."""
    dev = _fake_dev_bundle(private=True)
    syn = _fake_syn_bundle()
    fake_dev_roots = {"count": 18, "roots_sha256": "dev_roots" + "0" * 57,
                      "roots": ["ab" * 32 for _ in range(18)]}
    fake_dev_seeds = {"count": 18 * 512,
                      "seed_ids_sha256": "dev_seeds" + "0" * 55,
                      "seed_ids": [f"dev_seed_{i}" for i in range(18 * 512)]}
    # Build fake arrays map from real lock confirmation rows
    # Use the shared singleton so execute and verify reference the same map.
    _build_shared_fake_arrays_map()

    def _fast_validate(plan, *, test_only, output_dir):
        """Minimal validation that doesn't read from fake dev/syn dirs."""
        if not isinstance(plan, dict):
            raise ValueError("plan type")
        supplied = dict(plan)
        digest = supplied.pop("plan_sha256", None)
        if not isinstance(digest, str) or core._sha(core._compact(supplied)) != digest:
            raise ValueError("plan self hash")
        if plan.get("schema") != (core.TEST_PLAN_SCHEMA if test_only else core.PLAN_SCHEMA):
            raise ValueError("plan identity")
        if plan.get("run_id") != (core.TEST_RUN_ID if test_only else core.RUN_ID):
            raise ValueError("plan identity")
        return dict(plan)

    with patch.object(core, "load_development", return_value=dev), \
         patch.object(core, "_load_synthetic", return_value=syn), \
         patch.object(core, "_development_root_digest", return_value=fake_dev_roots), \
         patch.object(core, "_development_seed_digest", return_value=fake_dev_seeds), \
         patch.object(core, "_validate_plan", side_effect=_fast_validate), \
         patch.object(confirm, "confirmation_arrays_for_frame", side_effect=_shared_patched_arrays), \
         patch.object(core, "confirmation_arrays_for_frame", side_effect=_shared_patched_arrays), \
         patch.object(ldpc_v5_mod, "verify_public_payload_v5", return_value={"status": "verified"}), \
         patch.object(verify_cli, "verify_public_payload_v5", return_value={"status": "verified"}):
        yield


@contextmanager
def _fake_array_loader():
    """Context manager that patches confirmation array loading."""
    lock = core._json_read(core.PARTITION_LOCK)
    fake_arrays_map = {}
    for row in confirm.confirmation_rows(lock):
        a, b = _fake_arrays()
        fake_arrays_map[(row["stratum"], row["frame_id"])] = (a, b)

    def _patched(lock_map, row):
        return fake_arrays_map[(row["stratum"], row["frame_id"])]

    with patch.object(confirm, "confirmation_arrays_for_frame", side_effect=_patched):
        yield


# ========== fixture ==========

@pytest.fixture
def fresh(tmp_path_factory):
    base = ROOT / "workspace" / "ldpc_v5_real_tests" / str(uuid.uuid4())[:12]
    base.mkdir(parents=True, exist_ok=True)
    yield base
    shutil.rmtree(base.parent, ignore_errors=True)


# ---------------------------------------------------------------- T0 structural

class TestT0Structural:
    def test_constants_and_artifacts(self):
        assert core.RUN_ID == "binary_ldpc_v5_real_qualification_v1"
        assert core.CANDIDATE == "V5-C2"
        assert core.REAL_STRATA == ("bw120", "bw180", "bw200")
        assert core.FRAMES_PER_STRATUM == 128
        assert core.GATE_SUCCESSES == 126
        assert core.ARTIFACTS[0] == "pre_run_plan.json"
        assert core.ARTIFACTS[6] == "real_frame_outcomes.csv"
        assert core.ARTIFACTS[9] == "real_qualification_report.json"
        assert len(core.ARTIFACTS) == 10

    def test_lock_strata_mapping(self):
        """Explicit mapping covers all d1024_* lock strata."""
        assert core.LOCK_TO_PUBLIC == {"d1024_bw120": "bw120", "d1024_bw180": "bw180", "d1024_bw200": "bw200"}
        assert core.PUBLIC_TO_LOCK == {"bw120": "d1024_bw120", "bw180": "d1024_bw180", "bw200": "d1024_bw200"}

    def test_attempt_ids_count_from_real_lock(self):
        """Lock has 384 confirmation rows (3 strata × 128); attempt IDs use public stratum names."""
        lock = core._json_read(core.PARTITION_LOCK)
        rows = confirm.confirmation_rows(lock)
        assert len(rows) == 384
        ids = core._attempt_ids(lock)
        assert len(ids) == 384
        assert len(set(ids)) == 384
        # All attempt IDs use public stratum names
        for aid in ids:
            pub = aid.split("|")[0]
            assert pub in core.REAL_STRATA, f"attempt_id uses lock stratum: {aid}"

    def test_attempt_ids_count_from_fake_lock(self):
        """Fake lock with 3 × 128 = 384 rows produces 384 public-named attempt IDs."""
        lock = _fake_lock()
        ids = core._attempt_ids(lock)
        assert len(ids) == 384
        for aid in ids:
            pub = aid.split("|")[0]
            assert pub in core.REAL_STRATA

    def test_derive_seed_deterministic_and_unique(self):
        r = "ab" * 32
        a = core.derive_seed(r, "bw120", 0, 0)
        b = core.derive_seed(r, "bw120", 0, 0)
        assert a == b
        c = core.derive_seed(r, "bw120", 0, 1)
        assert a["seed_id"] != c["seed_id"]
        assert a["seed_bit_length"] == core.SEED_BIT_LENGTH

    def test_compact_json_canonical(self):
        val = {"z": 1, "a": 2, "m": None}
        raw = core._compact(val)
        assert raw == b'{"a":2,"m":null,"z":1}'
        assert core._sha(raw)

    def test_lock_stratum_to_public_rejects_unknown(self):
        with pytest.raises(ValueError, match="unknown lock stratum"):
            core._lock_stratum_to_public("unknown_stratum")


# ---------------------------------------------------------------- T1 unit/tamper

class TestT1PlanRootSeedUniqueness:
    def test_fake_prepare_writes_only_plan(self, fresh):
        """prepare_test writes exactly one file: pre_run_plan.json."""
        out = fresh / "out"
        plan = _prepare_test_with_fakes(out)
        assert sorted(p.name for p in out.iterdir()) == ["pre_run_plan.json"]
        assert plan["schema"] == core.TEST_PLAN_SCHEMA
        assert plan["run_id"] == core.TEST_RUN_ID
        assert plan["domain"]["candidate"] == "V5-C2"
        assert len(plan["seed_schedule"]["roots"]) == 6
        assert plan["seed_schedule"]["seed_count"] == 3 * 128 * 2

    def test_no_overwrite_rejects_existing_dir(self, fresh):
        out = fresh / "out"
        out.mkdir()
        with pytest.raises(FileExistsError, match="fresh output directory required"):
            _prepare_test_with_fakes(out)

    def test_plan_root_uniqueness(self, fresh):
        """All 6 roots are unique hex 64-char strings."""
        out = fresh / "out"
        plan = _prepare_test_with_fakes(out)
        roots = plan["seed_schedule"]["roots"]
        root_hexes = [r["root_hex"] for r in roots]
        assert len(set(root_hexes)) == 6
        for h in root_hexes:
            assert len(h) == 64
            assert all(c in "0123456789abcdef" for c in h)

    def test_seed_id_uniqueness(self, fresh):
        """All 768 seed IDs are unique."""
        out = fresh / "out"
        plan = _prepare_test_with_fakes(out)
        # Re-derive all seed IDs from roots
        lock = _fake_lock()
        all_ids = []
        for rec in plan["seed_schedule"]["roots"]:
            pub_s = rec["stratum"]
            lock_s = _PUB_TO_LOCK[pub_s]
            for row in confirm.confirmation_rows(lock):
                if row["stratum"] == lock_s:
                    s = core.derive_seed(rec["root_hex"], pub_s, rec["verification_round"], row["frame_id"])
                    all_ids.append(s["seed_id"])
        assert len(set(all_ids)) == len(all_ids) == 384 * 2

    def test_attempt_id_stratum_uses_public_names(self, fresh):
        """Attempt IDs in plan use public stratum names, not lock d1024_* names."""
        out = fresh / "out"
        plan = _prepare_test_with_fakes(out)
        for aid in plan["execution"]["attempt_ids"]:
            pub = aid.split("|")[0]
            assert pub in core.REAL_STRATA
            assert "d1024_" not in aid


class TestT1PartitionBinding:
    def test_exact_partition_binding_fields(self, fresh):
        """Plan partition_binding has exact lock path, sha256, digest, counts."""
        out = fresh / "out"
        lock = _fake_lock()
        plan = _prepare_test_with_fakes(out, lock)
        pb = plan["partition_binding"]
        assert pb["lock_path"] == str(core.PARTITION_LOCK.resolve())
        assert pb["partition_sha256"] == lock["partition_sha256"]
        assert pb["confirmation_count_per_stratum"] == 128
        assert pb["confirmation_access_api"] == "confirmation_arrays_for_frame"

    def test_wrong_lock_path_rejected(self, fresh):
        """_load_partition_lock rejects a non-existent path."""
        with pytest.raises((ValueError, FileNotFoundError)):
            core._load_partition_lock(Path("/nonexistent/lock.json"))


class TestT1ConfirmationArrayRoleEnforcement:
    def test_confirmation_arrays_only_for_confirmation_role(self, fresh):
        """confirmation_rows filters only role=confirmation rows."""
        lock = _fake_lock()
        rows = confirm.confirmation_rows(lock)
        assert all(r["role"] == "confirmation" for r in rows)
        assert len(rows) == 384

    def test_attempt_ids_only_from_confirmation_rows(self):
        """_attempt_ids reads only confirmation rows from the lock."""
        lock = _fake_lock()
        ids = core._attempt_ids(lock)
        assert len(ids) == 384


class TestT1PlanTamperRejection:
    def _validate_with_fakes(self, plan, output_dir):
        """Validate a plan with fake dev/syn deps patched."""
        dev_path = plan.get("development_binding", {}).get("path", "/fake/dev")
        dev_hashes = plan.get("development_binding", {}).get("artifact_hashes", {})
        binding = plan.get("development_binding", {})
        dev = {"path": dev_path, "verification": {"status": "verified", "run_status": "completed",
               "selected_candidate_id": "V5-C2", "ready_for_synthetic_prepare": True,
               "decoder_reexecution": False}, "hashes": dev_hashes,
               "docs": {"formal_codebook_manifest.json": binding.get("codebook", {}),
                        "formal_selection_manifest.json": binding.get("selection", {}),
                        "formal_channel_model.json": binding.get("channel_model", {}),
                        "v5_h2_manifest.json": binding.get("h2_manifest", {}),
                        "v5_policy_manifest.json": binding.get("policy_manifest", {})},
               "selected": ["V5-C2"], "candidate_policy": {}}
        syn_path = plan.get("synthetic_binding", {}).get("path", "/fake/syn")
        syn = {"path": syn_path, "verification": {"run_status": "completed",
                "ready_for_real_qualification": True},
               "hashes": {"synthetic_qualification_report.json": plan["synthetic_binding"]["report_sha256"]}}
        fake_dev_roots = {"count": 18, "roots_sha256": "dev_roots" + "0" * 57,
                          "roots": ["ab" * 32 for _ in range(18)]}
        fake_dev_seeds = {"count": 18 * 512,
                          "seed_ids_sha256": "dev_seeds" + "0" * 55,
                          "seed_ids": [f"dev_seed_{i}" for i in range(18 * 512)]}
        with patch.object(core, "_development_root_digest", return_value=fake_dev_roots), \
             patch.object(core, "_development_seed_digest", return_value=fake_dev_seeds), \
             patch.object(core, "_load_synthetic", return_value=syn), \
             patch.object(core, "load_development", return_value=dev), \
             patch.object(core, "_seed_schedule", return_value=plan["seed_schedule"]), \
             patch.object(core, "_validate_roots", return_value=set()):
            return core._validate_plan(plan, test_only=True, output_dir=output_dir)

    def test_tampered_self_hash_rejected(self, fresh):
        """Plan with tampered plan_sha256 is rejected."""
        out = fresh / "out"
        plan = _prepare_test_with_fakes(out)
        tampered = dict(plan)
        tampered["plan_sha256"] = "0" * 64
        with pytest.raises(ValueError, match="plan self hash"):
            self._validate_with_fakes(tampered, out)

    def test_tampered_gates_rejected(self, fresh):
        """Plan with tampered gates fails self-hash check."""
        out = fresh / "out"
        plan = _prepare_test_with_fakes(out)
        tampered = dict(plan)
        tampered["gates"] = {"denominator_per_stratum": 999}
        tampered["plan_sha256"] = "0" * 64
        with pytest.raises(ValueError, match="plan self hash"):
            self._validate_with_fakes(tampered, out)

    def test_tampered_development_binding_rejected(self, fresh):
        """Plan with wrong development binding artifact hash is rejected."""
        out = fresh / "out"
        plan = _prepare_test_with_fakes(out)
        supplied = json.loads(core._compact(plan).decode("ascii"))
        supplied["development_binding"]["artifact_hashes"]["formal_codebook_manifest.json"] = "0" * 64
        supplied["plan_sha256"] = core._sha(core._compact({k: v for k, v in supplied.items() if k != "plan_sha256"}))
        with pytest.raises(ValueError, match="development binding"):
            self._validate_with_fakes(supplied, out)

    def test_tampered_partition_binding_sha_rejected(self, fresh):
        """Plan with wrong partition_sha256 is rejected."""
        out = fresh / "out"
        plan = _prepare_test_with_fakes(out)
        supplied = json.loads(core._compact(plan).decode("ascii"))
        supplied["partition_binding"]["partition_sha256"] = "0" * 64
        supplied["plan_sha256"] = core._sha(core._compact({k: v for k, v in supplied.items() if k != "plan_sha256"}))
        with pytest.raises(ValueError, match="partition binding"):
            self._validate_with_fakes(supplied, out)

    def test_valid_plan_passes_validation(self, fresh):
        """A freshly prepared plan passes _validate_plan."""
        out = fresh / "out"
        plan = _prepare_test_with_fakes(out)
        self._validate_with_fakes(plan, out)


class TestT1NoOverwrite:
    def test_prepare_rejects_existing_directory(self, fresh):
        """prepare_plan raises FileExistsError if output dir exists."""
        out = fresh / "out"
        out.mkdir()
        with pytest.raises(FileExistsError):
            core._prepare_test_plan(out, core.PARTITION_LOCK)

    def test_execute_rejects_wrong_file_set(self, fresh):
        """Execute requires exactly the plan file, nothing else."""
        out = fresh / "out"
        out.mkdir()
        (out / "wrong_file.txt").write_text("x")
        with pytest.raises(ValueError, match="requires only reviewed plan"):
            core._execute_test_plan(out, _make_fake_runner())

    def test_execute_rejects_empty_dir(self, fresh):
        out = fresh / "out"
        out.mkdir()
        with pytest.raises(ValueError, match="requires only reviewed plan"):
            core._execute_test_plan(out, _make_fake_runner())


class TestT1PartialFinalization:
    def test_exception_mid_execution_retains_partial(self, fresh):
        """If the runner raises, the partial package is finalized with all artifacts."""
        out = fresh / "out"
        _prepare_test_with_fakes(out)

        call_count = 0
        def boom(alice, bob, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count > 5:
                raise RuntimeError("fake mid-execution failure")
            return _make_fake_runner()(alice, bob, **kwargs)

        _execute_with_fakes(out, boom)
        assert sorted(p.name for p in out.iterdir()) == sorted(core.ARTIFACTS)
        report = core._json_read(out / core.ARTIFACTS[9])
        assert report["run_status"] == "invalid_execution"
        assert report["promoted"] is False
        assert report["ready_for_real_qualification"] is False


class TestT1TamperDetection:
    """Every artifact tamper must be detected by the verifier."""

    def _build_and_verify(self, fresh):
        """Build a complete fake package, return (out, before_hashes)."""
        out = fresh / "pkg"
        _build_fake_package(out, _make_fake_runner())
        before = {p.name: p.read_bytes() for p in out.iterdir()}
        return out, before

    def _rebuild(self, out, plan_json_bytes, csv_bytes, manifest_json,
                 report_json, transcript_bytes):
        """Rebuild artifacts after tamper for testing."""
        # Not used directly; each test tampers independently

    def _verify_read_only(self, out, before):
        """Verify: package is read-only (hashes unchanged)."""
        after = {p.name: p.read_bytes() for p in out.iterdir()}
        assert before == after

    def test_tamper_plan_self_hash(self, fresh):
        out = fresh / "pkg"
        _build_fake_package(out, _make_fake_runner())
        plan = core._json_read(out / core.ARTIFACTS[0])
        plan["plan_sha256"] = "0" * 64
        (out / core.ARTIFACTS[0]).write_bytes(core._compact(plan))
        before = {p.name: p.read_bytes() for p in out.iterdir()}
        with _fake_deps():
            with pytest.raises(ValueError):
                verify_cli.verify_output(out, _private_test_only=True)
        self._verify_read_only(out, before)

    def test_tamper_csv_status(self, fresh):
        out = fresh / "pkg"
        _build_fake_package(out, _make_fake_runner())
        csv_path = out / core.ARTIFACTS[6]
        raw = csv_path.read_text(encoding="ascii")
        lines = raw.splitlines()
        if len(lines) > 1:
            header, first, *rest = lines
            tampered = "\n".join([header, first.replace("backend_unavailable", "verified_success"), *rest]) + "\n"
            csv_path.write_text(tampered, encoding="ascii")
        before = {p.name: p.read_bytes() for p in out.iterdir()}
        with _fake_deps():
            with pytest.raises(ValueError):
                verify_cli.verify_output(out, _private_test_only=True)
        self._verify_read_only(out, before)

    def test_tamper_manifest_outcome_count(self, fresh):
        out = fresh / "pkg"
        _build_fake_package(out, _make_fake_runner())
        man = core._json_read(out / core.ARTIFACTS[8])
        man["outcome_count"] = man["outcome_count"] - 1
        (out / core.ARTIFACTS[8]).write_bytes(core._compact(man))
        before = {p.name: p.read_bytes() for p in out.iterdir()}
        with _fake_deps():
            with pytest.raises(ValueError):
                verify_cli.verify_output(out, _private_test_only=True)
        self._verify_read_only(out, before)

    def test_tamper_manifest_self_hash(self, fresh):
        out = fresh / "pkg"
        _build_fake_package(out, _make_fake_runner())
        man = core._json_read(out / core.ARTIFACTS[8])
        man["run_manifest_sha256"] = "0" * 64
        (out / core.ARTIFACTS[8]).write_bytes(core._compact(man))
        before = {p.name: p.read_bytes() for p in out.iterdir()}
        with _fake_deps():
            with pytest.raises(ValueError):
                verify_cli.verify_output(out, _private_test_only=True)
        self._verify_read_only(out, before)

    def test_tamper_report_sha(self, fresh):
        out = fresh / "pkg"
        _build_fake_package(out, _make_fake_runner())
        report = core._json_read(out / core.ARTIFACTS[9])
        report["report_sha256"] = "0" * 64
        (out / core.ARTIFACTS[9]).write_bytes(core._compact(report))
        before = {p.name: p.read_bytes() for p in out.iterdir()}
        with _fake_deps():
            with pytest.raises(ValueError):
                verify_cli.verify_output(out, _private_test_only=True)
        self._verify_read_only(out, before)

    def test_tamper_policy_manifest(self, fresh):
        out = fresh / "pkg"
        _build_fake_package(out, _make_fake_runner())
        policy_path = out / core.ARTIFACTS[5]
        doc = core._json_read(policy_path)
        doc["manifest_sha256"] = "1" * 64  # different from original "0" * 64
        policy_path.write_bytes(core._compact(doc))
        before = {p.name: p.read_bytes() for p in out.iterdir()}
        with _fake_deps():
            with pytest.raises(ValueError):
                verify_cli.verify_output(out, _private_test_only=True)
        self._verify_read_only(out, before)

    def test_tamper_codebook_manifest(self, fresh):
        out = fresh / "pkg"
        _build_fake_package(out, _make_fake_runner())
        cb_path = out / core.ARTIFACTS[1]
        doc = core._json_read(cb_path)
        doc["tamp"] = True
        cb_path.write_bytes(core._compact(doc))
        before = {p.name: p.read_bytes() for p in out.iterdir()}
        with _fake_deps():
            with pytest.raises(ValueError):
                verify_cli.verify_output(out, _private_test_only=True)
        self._verify_read_only(out, before)

    def test_extra_file_rejected(self, fresh):
        """Verifier rejects a package with an extra file."""
        out = fresh / "pkg"
        _build_fake_package(out, _make_fake_runner())
        (out / "extra_file.txt").write_text("x")
        with pytest.raises(ValueError, match="10 artifact contract"):
            verify_cli.verify_output(out, _private_test_only=True)

    def test_missing_file_rejected(self, fresh):
        """Verifier rejects a package with a missing file."""
        out = fresh / "pkg"
        _build_fake_package(out, _make_fake_runner())
        (out / core.ARTIFACTS[5]).unlink()
        with pytest.raises(ValueError, match="10 artifact contract"):
            verify_cli.verify_output(out, _private_test_only=True)


# ---------------------------------------------------------------- T2 full fake lifecycle

class TestT2FullLifecycle:
    def test_success_promotion(self, fresh):
        """All 384 attempts verified_success → promoted, status=verified, ready=true."""
        out = fresh / "pkg"
        _build_fake_package(out, _make_success_runner())
        with _fake_deps():
            got = verify_cli.verify_output(out, _private_test_only=True)
        assert got["status"] == "verified"
        assert got["run_status"] == "completed"
        assert got["ready_for_real_qualification"] is True
        assert got["outcomes"] == 384
        manifest = core._json_read(out / core.ARTIFACTS[8])
        assert manifest["run_status"] == "completed"
        report = core._json_read(out / core.ARTIFACTS[9])
        assert report["promoted"] is True
        for gate in report["promotion_gates"].values():
            assert gate["denominator"] == 128
            assert gate["verified_success"] == 128
            assert gate["passed"] is True

    def test_retained_failure_non_promoted(self, fresh):
        """All 384 backend_unavailable → non_promoted, ready=false."""
        out = fresh / "pkg"
        _build_fake_package(out, _make_fake_runner(outcome_status="backend_unavailable"))
        with _fake_deps():
            got = verify_cli.verify_output(out, _private_test_only=True)
        assert got["status"] == "verified"
        assert got["run_status"] == "non_promoted"
        assert got["ready_for_real_qualification"] is False
        assert got["outcomes"] == 384
        report = core._json_read(out / core.ARTIFACTS[9])
        for gate in report["promotion_gates"].values():
            assert gate["verified_success"] == 0
            assert gate["passed"] is False

    def test_partial_success_one_failure_layer(self, fresh):
        """One stratum all failures → that layer fails gate → non_promoted."""
        out = fresh / "pkg"
        def mixed_runner2(alice, bob, **kwargs):
            stratum = kwargs.get("stratum", "")
            if stratum == "bw200":
                return _make_fake_runner(outcome_status="backend_unavailable")(alice, bob, **kwargs)
            return _make_fake_runner(outcome_status="verified_success")(alice, bob, **kwargs)

        _build_fake_package(out, mixed_runner2)
        with _fake_deps():
            got = verify_cli.verify_output(out, _private_test_only=True)
        assert got["status"] == "verified"
        assert got["run_status"] == "non_promoted"
        assert got["ready_for_real_qualification"] is False
        report = core._json_read(out / core.ARTIFACTS[9])
        assert report["promotion_gates"]["bw200"]["verified_success"] == 0
        assert report["promotion_gates"]["bw200"]["passed"] is False
        assert report["promotion_gates"]["bw120"]["passed"] is True

    def test_exception_partial_finalization(self, fresh):
        """Runner raises mid-execution → invalid_execution, partial, ready=false."""
        out = fresh / "out"
        _prepare_test_with_fakes(out)
        call_count = 0
        def boom(alice, bob, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count > 5:
                raise RuntimeError("fake decode failure")
            return _make_fake_runner(outcome_status="verified_success")(alice, bob, **kwargs)

        _execute_with_fakes(out, boom)
        assert sorted(p.name for p in out.iterdir()) == sorted(core.ARTIFACTS)
        with _fake_deps():
            got = verify_cli.verify_output(out, _private_test_only=True)
        assert got["status"] == "verified"
        assert got["run_status"] == "invalid_execution"
        assert got["ready_for_real_qualification"] is False

    def test_cap_timeout(self, fresh):
        """complete_run_s exceeded → invalid_execution."""
        out = fresh / "out"
        _prepare_test_with_fakes(out)
        with patch.object(core.time, "monotonic", side_effect=[0.0, 1801.0]):
            _execute_with_fakes(out, _make_fake_runner())
        with _fake_deps():
            got = verify_cli.verify_output(out, _private_test_only=True)
        assert got["run_status"] == "invalid_execution"
        assert got["ready_for_real_qualification"] is False

    def test_non_attempted_rows(self, fresh):
        """Non-attempted rows (denominator_excluded) are counted correctly."""
        out = fresh / "pkg"
        _build_fake_package(out, _make_fake_runner(outcome_status="backend_unavailable"))
        rows = decode_outcome_csv_v5((out / core.ARTIFACTS[6]).read_bytes())
        assert len(rows) == 384
        assert all(not r["attempted"] for r in rows)
        assert all(r["denominator_included"] is False for r in rows)

    def test_csv_stratum_uses_public_names(self, fresh):
        """CSV rows use public stratum names (bw120/bw180/bw200)."""
        out = fresh / "pkg"
        _build_fake_package(out, _make_fake_runner(outcome_status="backend_unavailable"))
        rows = decode_outcome_csv_v5((out / core.ARTIFACTS[6]).read_bytes())
        for r in rows:
            assert r["stratum"] in core.REAL_STRATA
            assert "d1024_" not in r["stratum"]

    def test_attempt_ids_plan_match_execution(self, fresh):
        """Plan attempt_ids match what the verifier expects."""
        out = fresh / "pkg"
        _build_fake_package(out, _make_fake_runner())
        plan = core._json_read(out / core.ARTIFACTS[0])
        rows = decode_outcome_csv_v5((out / core.ARTIFACTS[6]).read_bytes())
        assert [r["plan_frame_id"] for r in rows] == plan["execution"]["attempt_ids"]

    def test_verify_is_read_only(self, fresh):
        """Verifier does not modify any file."""
        out = fresh / "pkg"
        _build_fake_package(out, _make_fake_runner())
        before = {p.name: p.read_bytes() for p in out.iterdir()}
        with _fake_deps():
            verify_cli.verify_output(out, _private_test_only=True)
            verify_cli.verify_output(out, _private_test_only=True)
        after = {p.name: p.read_bytes() for p in out.iterdir()}
        assert before == after

    def test_no_overwrite_and_no_resume(self, fresh):
        """Executing into a completed directory is rejected."""
        out = fresh / "pkg"
        _build_fake_package(out, _make_fake_runner())
        with pytest.raises(ValueError, match="requires only reviewed plan"):
            core._execute_test_plan(out, _make_fake_runner())


# ---------------------------------------------------------------- production CLI guards

class TestProductionCLIGuards:
    def test_no_test_switch_in_runner_cli(self):
        source = Path(run_cli.__file__).read_text(encoding="utf-8")
        assert "--test" not in source and "test_only" not in source

    def test_production_prepare_requires_official_path(self, fresh):
        with pytest.raises(ValueError, match="official output path"):
            run_cli.prepare_plan(Path("/tmp/fake"), core.PARTITION_LOCK)

    def test_verify_rejects_wrong_file_count(self, fresh):
        (fresh / "plan.json").write_text("{}")
        with pytest.raises(ValueError, match="10 artifact contract"):
            verify_cli.verify_output(fresh, _private_test_only=True)

    def test_verify_rejects_non_canonical_json(self, fresh):
        plan_path = fresh / "pre_run_plan.json"
        plan_path.write_text('{ "a": 1 }\n')
        for name in core.ARTIFACTS[1:]:
            (fresh / name).write_bytes(b"{}")
        with pytest.raises(ValueError):
            verify_cli.verify_output(fresh, _private_test_only=True)

    def test_scoped_includes_verifier(self):
        assert "cli/verify_ldpc_v5_real_qualification.py" in core._SCOPED
