"""T0-T3 tests for the v1 binary LDPC v5 sacrificed-development package.

T0 structural/tiny-math, T1 focused unit/tamper, T2 full fake-only
qualification + strict replay, T3 cross-version/broad regression (heavy
real-backend run is opt-in via RUN_HEAVY=1).

Every package materialization uses a fresh additive workspace root and
explicit fakes; production entry points are never invoked with real data.
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from pathlib import Path

import numpy as np
import pytest

# Progress logs (execute/verify) are visible with:
#   pytest -s -o log_cli=true comparison_bench/tests/test_ldpc_v5_development.py
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

from comparison_bench.src.comparison_bench.formal_ir import ldpc_v5_development as core
from comparison_bench.src.comparison_bench.formal_ir import ldpc_v4_10db_source as source
from comparison_bench.src.comparison_bench.formal_ir.ldpc_v5 import (OUTCOME_FIELDS, METHOD,
                                                                     decode_outcome_csv_v5,
                                                                     encode_outcome_csv_v5)
from comparison_bench.src.comparison_bench.cli import run_ldpc_v5_development as run_cli
from comparison_bench.src.comparison_bench.cli import verify_ldpc_v5_development as verify_cli

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def fresh(tmp_path_factory):
    """Fresh workspace-descendant directory; cleaned up by pytest."""
    base = ROOT / "workspace" / "ldpc_v5_development_tests" / str(uuid.uuid4())[:12]
    base.parent.mkdir(parents=True, exist_ok=True)
    yield base
    import shutil
    shutil.rmtree(base.parent, ignore_errors=True)


def _roots(seed: int = 0):
    return [f"{(seed + i) % (1 << 64):064x}" for i in range(18)]


def _nonattempted_outcome(candidate: str, stratum: str, rank: int, reason: str) -> dict:
    """Canonical non-attempted backend_unavailable outcome (finite raw_ser)."""
    return {"dataset_id": stratum, "frame_id": rank, "n_pairs": core.N,
            "pair_idx_sequence_sha256": core.EMPTY_HASH, "method": METHOD, "candidate_id": candidate,
            "attempted": False, "denominator_included": False, "status": "backend_unavailable",
            "failure_reason": reason, "dimension": core.Q, "frame_len_symbols": core.N,
            "raw_ser": 0.0, "fallback_invoked": False, "rounds_attempted": 1,
            "verification_invoked": False, "verification_seed_id_round0": "", "verification_seed_id_round1": "",
            "verification_tag_bits": 0, "epsilon_ec": 0.0, "key_dependent_disclosure_bits_total": 0,
            "public_control_bits_total": 0, "transcript_first_event_id": None,
            "transcript_last_event_id": None, "transcript_sha256": core.EMPTY_HASH,
            "runtime_s": 0.0, "decoder_call_count": 0, "verification_check_count": 0,
            "ldpc_syndrome_bits": 0, "h1_syndrome_bits": 0, "h2_syndrome_bits": 0,
            "verification_tag_bits_component": 0, "feedback_control_bits": 0,
            "selection_sha256": "", "channel_model_sha256": "", "h1_codebook_manifest_sha256": "",
            "h2_manifest_sha256": "", "policy_sha256": "", "mapping": core.MAPPING,
            "leakage_comparison_policy": "method_specific_not_cross_ranked",
            "backend_name": "", "backend_version": ""}


def _fake_runner_backend_unavailable(alice, bob, **kwargs):
    return {"outcome": _nonattempted_outcome(kwargs["candidate_policy"]["candidate_id"],
                                             kwargs["stratum"], int(kwargs["frame_id"]),
                                             "backend unavailable: fake"), "events": []}


def _fake_loader(lock, row):
    rng = np.random.Generator(np.random.PCG64(int(row["role_rank"])))
    a = rng.integers(0, core.Q, core.N, dtype=np.int64)
    return a, a.copy()


def _fake_clock():
    t = [0.0]

    def clock():
        t[0] += 0.001
        return t[0]
    return clock


# ---------------------------------------------------------------- T0 structural

def test_artifact_tuple_and_constants():
    assert len(core.ARTIFACTS) == 12
    assert core.ARTIFACTS[0] == "pre_run_plan.json"
    assert core.ARTIFACTS[7] == "development_frame_outcomes.csv"
    assert core.ARTIFACTS[11] == "development_report.json"
    assert core.RUN_ID == "binary_ldpc_v5_development_v1"
    assert core.ROLE == "sacrificed_development"
    assert (core.N, core.Q, core.MAPPING, core.FRAMES_PER_STRATUM) == (256, 1024, "gray", 512)
    assert core.CANDIDATES == ("V5-C0", "V5-C1", "V5-C2")
    assert core.STRATA == ("bw120", "bw180", "bw200")


def test_attempt_ids_order_and_count():
    ids = core._attempt_ids()
    assert len(ids) == 3 * 3 * 512 == 4608
    assert ids[0] == "V5-C0|bw120|0"
    assert ids[512] == "V5-C0|bw180|0"
    assert ids[1024] == "V5-C0|bw200|0"
    assert ids[1536] == "V5-C1|bw120|0"
    assert len(set(ids)) == 4608


def test_derive_seed_deterministic_and_unique():
    r = _roots()
    a = core.derive_seed(r[0], "V5-C0", "bw120", 0, 0)
    b = core.derive_seed(r[0], "V5-C0", "bw120", 0, 0)
    assert a == b
    c = core.derive_seed(r[0], "V5-C0", "bw120", 0, 1)
    assert a["seed_id"] != c["seed_id"]
    ids = {core.derive_seed(r[0], "V5-C0", "bw120", 0, rank)["seed_id"] for rank in range(512)}
    assert len(ids) == 512
    assert a["seed_bit_length"] == core.SEED_BIT_LENGTH


def test_compact_sha_self_roundtrip():
    doc = {"schema": "x", "n": 1, "b": [True, False]}
    self_doc = core._self(dict(doc), "self_sha256")
    base = dict(self_doc)
    digest = base.pop("self_sha256")
    assert digest == core._sha(core._compact(base))
    assert core._compact(self_doc) == core._compact(self_doc)


def test_scoped_source_files_exist():
    hashes = core._hashes()
    src = ROOT / "comparison_bench" / "src" / "comparison_bench"
    for rel, digest in hashes.items():
        assert (src / rel.removeprefix("comparison_bench/src/comparison_bench/")).exists()
        assert len(digest) == 64


# ---------------------------------------------------------------- T1 unit/tamper

def test_prior_digests_match_frozen():
    assert core._prior_digests() == (core.PRIOR_ROOTS_SHA256, core.PRIOR_SEED_IDS_SHA256)


def test_seed_schedule_rejects_bad_roots():
    with pytest.raises(ValueError):
        core._seed_schedule(_roots()[:-1])          # 17 roots
    with pytest.raises(ValueError):
        core._seed_schedule([_roots()[0]] * 18)     # duplicates
    schedule = core._seed_schedule(_roots())
    assert schedule["schema"] == core.SEED_SCHEDULE_SCHEMA
    assert schedule["seed_count"] == 18 * 512
    assert schedule["isolated"] is True
    assert len(schedule["roots"]) == 18
    base = dict(schedule)
    digest = base.pop("seed_schedule_sha256")
    assert digest == core._sha(core._compact(base))


def test_method_objects_bindings_consistent():
    method = core._method_objects()
    assert set(method["bindings"]) == {"h1_codebook_manifest_sha256", "h1_selection_sha256",
                                       "channel_model_sha256", "h2_manifest_sha256",
                                       "policy_manifest_sha256"}
    assert method["bindings"]["h1_selection_sha256"] == core.SHARED_SELECTION
    assert method["bindings"]["h1_codebook_manifest_sha256"] == core.SHARED_CODEBOOK
    assert method["bindings"]["channel_model_sha256"] == core.SHARED_CHANNEL
    assert len(method["selected"]) == 10
    assert core._sha(method["channel_bytes"]) == core.SHARED_CHANNEL
    assert method["channel"]["model_sha256"] == method["selection"]["channel_model_sha256"]


def test_plan_validate_and_tamper_rejected(fresh):
    method = core._method_objects()
    partition_bytes = core.PARTITION_LOCK.read_bytes()
    lock = json.loads(partition_bytes)
    plan = core._plan(lock, partition_bytes, method, _roots(), test_only=True, output_dir=fresh)
    assert plan["schema"] == core.TEST_PLAN_SCHEMA
    assert plan["run_id"] == core.TEST_RUN_ID
    assert len(plan["execution"]["attempt_ids"]) == 4608
    # tamper: self-hash
    tampered = dict(plan)
    tampered["gates"] = {"denominator_per_stratum": 999, "successes_per_stratum": 510,
                         "forbidden_failure_count_limit": 0, "strata": list(core.STRATA)}
    with pytest.raises(ValueError, match="plan self hash"):
        core._validate_plan(tampered, test_only=True, output_dir=fresh)
    # tamper: method binding changed but self-hash fixed -> frozen equality
    changed = json.loads(core._compact(plan).decode("ascii"))
    changed["method_bindings"]["h1_selection_sha256"] = "0" * 64
    changed = core._self({k: v for k, v in changed.items() if k != "plan_sha256"}, "plan_sha256")
    with pytest.raises(ValueError, match="plan frozen equality"):
        core._validate_plan(changed, test_only=True, output_dir=fresh)
    # valid plan validates
    core._validate_plan(plan, test_only=True, output_dir=fresh)


def test_static_lock_checks_tamper():
    lock = json.loads(core.PARTITION_LOCK.read_bytes())
    core._static_lock_checks(lock)
    changed = json.loads(json.dumps(lock))
    changed["role_digests"]["development_count"] = 999
    changed["partition_sha256"] = core._sha(core._compact({k: v for k, v in changed.items() if k != "partition_sha256"}))
    # locally re-hashed but content drifted: either the frozen content-hash
    # check or the counts check must reject it
    with pytest.raises(ValueError):
        core._static_lock_checks(changed)


def test_classify_forbidden_classes():
    assert core._classify("backend_unavailable", "") == "backend"
    assert core._classify("aborted_resource_limit", "") == "resource"
    assert core._classify("syndrome_inconsistent", "") == "syndrome"
    assert core._classify("invalid_input", "") == "unclassified"
    assert core._classify("unsupported_domain", "") == "unclassified"
    assert core._classify("decoder_error", "backend down") == "backend"
    assert core._classify("decoder_error", "matrix mismatch") == "internal"
    assert core._classify("verified_success", "") is None
    assert core._package_class("package_backend:boom") == "backend"
    assert core._package_class("package_unknown:x") is None
    assert core._package_class("plain error") is None


def test_package_failure_outcome_fields():
    row = core._package_failure_outcome("V5-C2|bw200|7", "internal", "Boom:bad")
    assert row["status"] == "invalid_input"
    assert row["attempted"] is False and row["denominator_included"] is False
    assert row["raw_ser"] == 0.0
    assert row["failure_reason"].startswith("package_internal:")
    assert row["transcript_sha256"] == core.EMPTY_HASH
    assert row["n_pairs"] == core.N and row["dimension"] == core.Q


def test_csv_row_prefix():
    row = core._csv_row("V5-C0|bw120|3", _nonattempted_outcome("V5-C0", "bw120", 3, "r"),
                        "a" * 64, "b" * 64, b"")
    assert row["role"] == "development"
    assert row["plan_frame_id"] == "bw120-3"
    assert row["alice_sha256"] == "a" * 64


def test_selection_ranking_cross_multiply():
    """Rational disclosure-ratio ordering: 10/512 beats 20/1024."""
    plan = {"schema": core.TEST_PLAN_SCHEMA, "run_id": core.TEST_RUN_ID,
            "plan_sha256": "0" * 64,
            "execution": {"attempt_ids": core._attempt_ids()},
            "gates": {"denominator_per_stratum": 512, "successes_per_stratum": 510,
                      "forbidden_failure_count_limit": 0, "strata": list(core.STRATA)},
            "ranking": ["x"], "method_bindings": {"policy_manifest_sha256": "p"},
            "partition_binding": {"partition_sha256": "q"}}
    good = [{"candidate_id": c, "stratum": s, "denominator_included": True,
             "verified": True, "status": "verified_success", "failure_reason": "",
             "key_dependent_disclosure_bits_total": disclosure, "runtime_s": runtime,
             "attempted": True}
            for c, (disclosure, runtime) in (("V5-C0", (10, 1.0)), ("V5-C1", (20, 1.0)))
            for s in core.STRATA]
    rows = []
    for g in good:
        for rank in range(512):
            rows.append({"candidate_id": g["candidate_id"], "stratum": g["stratum"],
                         "denominator_included": True, "status": "verified_success",
                         "failure_reason": "", "key_dependent_disclosure_bits_total": g["key_dependent_disclosure_bits_total"],
                         "runtime_s": g["runtime_s"], "attempted": True})
    selection = core._selection(plan, rows, "f" * 64, "t" * 64)
    summaries = {s["candidate_id"]: s for s in selection["candidate_summaries"]}
    assert summaries["V5-C0"]["mean_disclosure_numerator"] == 10 * 3 * 512
    assert summaries["V5-C1"]["mean_disclosure_numerator"] == 20 * 3 * 512
    assert selection["selected_candidate_id"] == "V5-C0"
    assert selection["selection_status"] == "selected"
    assert summaries["V5-C0"]["selectable"] is True


def test_selection_invalid_when_forbidden():
    plan = {"schema": core.TEST_PLAN_SCHEMA, "run_id": core.TEST_RUN_ID,
            "plan_sha256": "0" * 64,
            "execution": {"attempt_ids": core._attempt_ids()},
            "gates": {"denominator_per_stratum": 512, "successes_per_stratum": 510,
                      "forbidden_failure_count_limit": 0, "strata": list(core.STRATA)},
            "ranking": ["x"], "method_bindings": {"policy_manifest_sha256": "p"},
            "partition_binding": {"partition_sha256": "q"}}
    rows = [{"candidate_id": "V5-C0", "stratum": s, "denominator_included": True,
             "status": "backend_unavailable", "failure_reason": "no backend",
             "key_dependent_disclosure_bits_total": 0, "runtime_s": 0.0, "attempted": False}
            for s in core.STRATA for _ in range(512)]
    selection = core._selection(plan, rows, "f" * 64, "t" * 64)
    assert selection["selected_candidate_id"] is None
    assert selection["selection_status"] == "invalid_execution"
    assert selection["ready_for_synthetic_prepare"] is False


def test_test_dir_checks():
    with pytest.raises(FileExistsError):
        core._test_dir_checks(ROOT)                       # exists
    with pytest.raises(ValueError, match="workspace descendant"):
        core._test_dir_checks(ROOT / "comparison_bench" / "outputs_comparison" / "x_new")
    ok = ROOT / "workspace" / "ldpc_v5_development_tests" / str(uuid.uuid4())[:12]
    core._test_dir_checks(ok)                             # fresh workspace path accepted


def test_prepare_test_package_writes_only_plan(fresh):
    plan = core._prepare_test_package(fresh, deterministic_roots=_roots())
    assert sorted(p.name for p in fresh.iterdir()) == ["pre_run_plan.json"]
    assert plan["output_binding"]["output_directory"] == fresh.resolve().relative_to(ROOT).as_posix()
    with pytest.raises(ValueError, match="deterministic roots"):
        core._prepare_test_package(fresh / "sub", deterministic_roots=_roots()[:-1])
    # no overwrite: second prepare into same dir
    with pytest.raises(FileExistsError):
        core._prepare_test_package(fresh, deterministic_roots=_roots())


def test_production_prepare_guards_official_paths():
    with pytest.raises(ValueError, match="official output path"):
        run_cli.prepare_plan(ROOT / "workspace" / "x", core.PARTITION_LOCK)
    with pytest.raises(ValueError, match="approved partition path"):
        run_cli.prepare_plan(core.OFFICIAL_OUTPUT, ROOT / "workspace" / "lock.json")


def test_execute_requires_only_reviewed_plan(fresh):
    with pytest.raises(ValueError, match="requires only reviewed plan"):
        core._execute(fresh, method_runner=lambda *a, **k: None,
                      array_loader=lambda *a, **k: None, clock=time_now, test_only=True)


def test_missing_fakes_fail_before_package_creation(fresh):
    """Contract §9: omitting method_runner/array_loader fails before creation."""
    core._prepare_test_package(fresh, deterministic_roots=_roots())
    assert sorted(p.name for p in fresh.iterdir()) == ["pre_run_plan.json"]
    with pytest.raises(TypeError):
        core._execute_test_package(fresh, method_runner=None,
                                   array_loader=None, clock=None)
    # no artifact beyond the plan was written
    assert sorted(p.name for p in fresh.iterdir()) == ["pre_run_plan.json"]


def test_production_array_loader_matches_locked_source():
    """Production execute loader: exact membership + bytes identical to source.

    Guards the perf fix: the production loader must not re-validate the
    partition lock per frame (~100 s/frame) and must reject any row that is
    not an exact locked development row.
    """
    lock = json.loads(core.PARTITION_LOCK.read_bytes())
    dev = [x for x in lock["role_rows"] if x["role"] == "development"]
    conf = [x for x in lock["role_rows"] if x["role"] == "confirmation"]
    core._SOURCE_LOCK_CACHE = None
    try:
        a, b = core._production_arrays_for_frame(lock, dev[0])
        src = source.build_source_lock()
        ea, eb = source.arrays_for_frame(src, {"stratum": dev[0]["stratum"],
                                               "frame_id": dev[0]["frame_id"]})
        assert np.array_equal(a, ea) and np.array_equal(b, eb)
        # confirmation rows and foreign rows never load arrays
        with pytest.raises(ValueError, match="development locked-row membership"):
            core._production_arrays_for_frame(lock, conf[0])
        foreign = dict(dev[1]); foreign["frame_id"] = -1
        with pytest.raises(ValueError, match="development locked-row membership"):
            core._production_arrays_for_frame(lock, foreign)
    finally:
        core._SOURCE_LOCK_CACHE = None


def time_now():
    return 0.0


# ---------------------------------------------------------------- T2 full fake qualification

def _run_full(fresh, runner=None):
    core._prepare_test_package(fresh, deterministic_roots=_roots())
    runner = runner or _fake_runner_backend_unavailable
    return core._execute_test_package(fresh, method_runner=runner,
                                      array_loader=_fake_loader, clock=_fake_clock())


def test_full_lifecycle_non_promoted(fresh):
    res = _run_full(fresh)
    assert res["run_status"] == "non_promoted_development"
    assert res["observed_outcomes"] == 4608
    assert sorted(p.name for p in fresh.iterdir()) == sorted(core.ARTIFACTS)
    # manifest consistency
    man = json.loads((fresh / core.ARTIFACTS[10]).read_bytes())
    assert man["run_status"] == "non_promoted_development"
    assert man["observed_outcomes"] == 4608
    # strict read-only replay: contract §8 exact six-field return
    out = core._verify_test_package(fresh)
    assert set(out) == {"status", "run_status", "outcomes", "selected_candidate_id",
                        "ready_for_synthetic_prepare", "decoder_reexecution"}
    assert out["status"] == "verified"
    assert out["run_status"] == "non_promoted_development"
    assert out["outcomes"] == 4608
    assert out["selected_candidate_id"] is None
    assert out["ready_for_synthetic_prepare"] is False
    assert out["decoder_reexecution"] is False
    # row identity: all non-attempted, canonical
    rows = decode_outcome_csv_v5((fresh / core.ARTIFACTS[7]).read_bytes())
    assert all(not r["attempted"] for r in rows)
    assert all(r["status"] == "backend_unavailable" for r in rows)


def test_full_lifecycle_invalid_execution(fresh):
    def boom(alice, bob, **kwargs):
        raise RuntimeError("fake decode failure")
    res = _run_full(fresh, runner=boom)
    assert res["run_status"] == "invalid_execution"
    assert res["failure"]["class"] == "internal"
    assert res["failure"]["attempt_id"] == "V5-C0|bw120|0"
    sel = json.loads((fresh / core.ARTIFACTS[9]).read_bytes())
    assert sel["selection_status"] == "invalid_execution"
    assert sel["selected_candidate_id"] is None
    rows = decode_outcome_csv_v5((fresh / core.ARTIFACTS[7]).read_bytes())
    assert rows[0]["failure_reason"].startswith("package_internal:")
    out = core._verify_test_package(fresh)
    assert out["status"] == "verified" and out["run_status"] == "invalid_execution"


def test_no_overwrite_and_no_resume(fresh):
    res = _run_full(fresh)
    assert res["run_status"] == "non_promoted_development"
    with pytest.raises(ValueError, match="requires only reviewed plan"):
        core._execute_test_package(fresh, method_runner=_fake_runner_backend_unavailable,
                                   array_loader=_fake_loader, clock=_fake_clock())


def test_tamper_outcome_row_rejected(fresh):
    _run_full(fresh)
    csv_path = fresh / core.ARTIFACTS[7]
    raw = csv_path.read_bytes().decode("ascii")
    assert "backend_unavailable" in raw
    # flip the status field of the first data row (header line untouched)
    lines = raw.splitlines()
    header, first, *rest = lines
    assert first.count("backend_unavailable") == 1
    tampered = "\n".join([header, first.replace("backend_unavailable", "verified_success"), *rest]) + "\n"
    assert tampered != raw
    csv_path.write_text(tampered, encoding="ascii")
    with pytest.raises(ValueError):
        core._verify_test_package(fresh)


def test_tamper_frozen_artifact_rejected(fresh):
    _run_full(fresh)
    (fresh / core.ARTIFACTS[5]).write_bytes(b"{}")   # v5_h2_manifest.json
    with pytest.raises(ValueError):
        core._verify_test_package(fresh)


def test_tamper_selection_rejected(fresh):
    _run_full(fresh)
    sel = json.loads((fresh / core.ARTIFACTS[9]).read_bytes())
    sel["selected_candidate_id"] = "V5-C1"
    (fresh / core.ARTIFACTS[9]).write_bytes(core._compact(sel))
    with pytest.raises(ValueError):
        core._verify_test_package(fresh)


def test_verify_cli_main_rejects_test_package(fresh, capsys, monkeypatch):
    """Production CLI has no test switch: a test package must be rejected."""
    _run_full(fresh)
    monkeypatch.setattr("sys.argv", ["verify_ldpc_v5_development", "--output-dir", str(fresh)])
    with pytest.raises(ValueError):
        verify_cli.main()


def test_run_cli_no_test_switch():
    """Production runner exposes only prepare/execute; no test flag exists."""
    source = Path(run_cli.__file__).read_text(encoding="utf-8")
    assert "--test" not in source and "test_only" not in source
    assert "choices=(\"prepare\", \"execute\")" in source or "prepare\", \"execute" in source
    # prepare without --partition-lock is a usage error
    import subprocess, sys
    proc = subprocess.run([sys.executable, "-m",
                           "comparison_bench.src.comparison_bench.cli.run_ldpc_v5_development",
                           "--output-dir", "x", "--mode", "prepare"],
                          capture_output=True, text=True)
    assert proc.returncode == 2 and "--partition-lock" in proc.stderr


# ---------------------------------------------------------------- T3 opt-in real backend

@pytest.mark.skipif(os.environ.get("RUN_HEAVY") != "1",
                    reason="heavy real-backend 4608-frame run; set RUN_HEAVY=1")
def test_real_backend_full_completed(fresh):
    from comparison_bench.src.comparison_bench.formal_ir.ldpc_v5 import run_ldpc_formal_v5
    res = _run_full(fresh, runner=run_ldpc_formal_v5)
    assert res["run_status"] in {"completed", "non_promoted_development", "invalid_execution"}
    out = core._verify_test_package(fresh)
    assert out["status"] == "verified"
    assert out["run_status"] == res["run_status"]
