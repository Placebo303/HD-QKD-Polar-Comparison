"""T0-T2 tests for the v1 binary LDPC v5 synthetic qualification package.

T0 structural/tiny-math, T1 focused unit/tamper, T2 complete fake-only
package + strict read-only replay. Every package materialization uses a fresh
additive workspace root and explicit fakes; production entry points are never
invoked with real data and the official synthetic directory is never touched.
"""
from __future__ import annotations

import json
import logging
import shutil
import uuid
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

from comparison_bench.src.comparison_bench.formal_ir import ldpc_v5_synthetic_qualification as core
from comparison_bench.src.comparison_bench.formal_ir.ldpc_v5 import (METHOD, OUTCOME_FIELDS,
                                                                     decode_outcome_csv_v5)
from comparison_bench.src.comparison_bench.cli import run_ldpc_v5_synthetic_qualification as run_cli
from comparison_bench.src.comparison_bench.cli import verify_ldpc_v5_synthetic_qualification as verify_cli

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def fresh(tmp_path_factory):
    base = ROOT / "workspace" / "ldpc_v5_synthetic_tests" / str(uuid.uuid4())[:12]
    base.parent.mkdir(parents=True, exist_ok=True)
    yield base
    shutil.rmtree(base.parent, ignore_errors=True)


def _nonattempted_outcome(stratum: str, attempt_id: str, reason: str) -> dict:
    return {"dataset_id": f"synthetic_{stratum}", "frame_id": attempt_id, "n_pairs": core.N,
            "pair_idx_sequence_sha256": core._sha(b""), "method": METHOD, "candidate_id": core.CANDIDATE,
            "attempted": False, "denominator_included": False, "status": "backend_unavailable",
            "failure_reason": reason, "dimension": core.Q, "frame_len_symbols": core.N,
            "raw_ser": 0.0, "fallback_invoked": False, "rounds_attempted": 1,
            "verification_invoked": False, "verification_seed_id_round0": "",
            "verification_seed_id_round1": "", "verification_tag_bits": 0, "epsilon_ec": 0.0,
            "key_dependent_disclosure_bits_total": 0, "public_control_bits_total": 0,
            "transcript_first_event_id": None, "transcript_last_event_id": None,
            "transcript_sha256": core._sha(b""), "runtime_s": 0.0, "decoder_call_count": 0,
            "verification_check_count": 0, "ldpc_syndrome_bits": 0, "h1_syndrome_bits": 0,
            "h2_syndrome_bits": 0, "verification_tag_bits_component": 0, "feedback_control_bits": 0,
            "selection_sha256": "", "channel_model_sha256": "", "h1_codebook_manifest_sha256": "",
            "h2_manifest_sha256": "", "policy_sha256": "", "mapping": core.MAPPING,
            "leakage_comparison_policy": "method_specific_not_cross_ranked",
            "backend_name": "", "backend_version": ""}


def _fake_runner(alice, bob, **kwargs):
    attempt_id = kwargs["frame_id"]
    stratum = attempt_id.split("|")[0]
    return {"outcome": _nonattempted_outcome(stratum, attempt_id, "backend unavailable: fake"),
            "events": []}


def _fake_clock():
    t = [0.0]

    def clock():
        t[0] += 0.001
        return t[0]
    return clock


def _prepare_and_execute(fresh, runner=None):
    core._prepare_test_plan(fresh, core.DEVELOPMENT_PKG)
    core._execute_test_plan(fresh, runner or _fake_runner)
    return fresh


# ---------------------------------------------------------------- T0 structural

def test_constants_and_artifacts():
    assert core.RUN_ID == "binary_ldpc_v5_synthetic_qualification_v1"
    assert core.CANDIDATE == "V5-C2"
    assert core.CHANNEL_STRATA == ("adjacent_nominal", "adjacent_stress_125")
    assert core.FRAMES_PER_STRATUM == 128
    assert core.DATA_STRATUM == "bw120"
    assert core.GATE_SUCCESSES == 126
    assert core.ARTIFACTS[0] == "pre_run_plan.json"
    assert core.ARTIFACTS[6] == "synthetic_frame_outcomes.csv"
    assert core.ARTIFACTS[9] == "synthetic_qualification_report.json"
    assert len(core.ARTIFACTS) == 10


def test_attempt_ids_order_and_count():
    ids = core._attempt_ids()
    assert len(ids) == 256
    assert ids[0] == "adjacent_nominal|f000"
    assert ids[127] == "adjacent_nominal|f127"
    assert ids[128] == "adjacent_stress_125|f000"
    assert ids[-1] == "adjacent_stress_125|f127"
    assert len(set(ids)) == 256


def test_derive_seed_deterministic_and_unique():
    r = "ab" * 32
    a = core.derive_seed(r, "adjacent_nominal", 0, 0)
    b = core.derive_seed(r, "adjacent_nominal", 0, 0)
    assert a == b
    c = core.derive_seed(r, "adjacent_nominal", 0, 1)
    assert a["seed_id"] != c["seed_id"]
    ids = {core.derive_seed(r, "adjacent_nominal", 0, i)["seed_id"] for i in range(128)}
    assert len(ids) == 128
    assert a["seed_bit_length"] == core.SEED_BIT_LENGTH


def test_generator_deterministic_and_distribution(fresh):
    plan = core._plan(core.load_development(core.DEVELOPMENT_PKG, private=True),
                      core._new_roots(), test_only=True, output_dir=fresh)
    a1, b1 = core._generate(plan, "adjacent_nominal")
    a2, b2 = core._generate(plan, "adjacent_nominal")
    assert np.array_equal(a1, a2) and np.array_equal(b1, b2)
    delta = ((a1.astype(np.int16) - b1.astype(np.int16)) % core.Q).astype(np.int16)
    delta = np.where(delta > core.Q // 2, delta - core.Q, delta)
    assert set(np.unique(delta)) <= {-1, 0, 1}
    model = plan["development_binding"]["channel_model"]
    probs = model["probabilities"]["adjacent_nominal"]
    ser = np.count_nonzero(delta) / delta.size
    assert abs(ser - (float(probs["plus_one"]) + float(probs["minus_one"]))) < 0.02
    _, bstress = core._generate(plan, "adjacent_stress_125")
    assert not np.array_equal(b1, bstress)


def test_plan_rejects_bad_roots(fresh):
    dev = core.load_development(core.DEVELOPMENT_PKG, private=True)
    with patch.object(core.secrets, "token_bytes", side_effect=[b"\x00" * 32] + [b"\x01" * 32] * 10):
        with pytest.raises(ValueError, match="root uniqueness"):
            core._plan(dev, core._new_roots(), test_only=True, output_dir=fresh)


# ---------------------------------------------------------------- T1 unit/tamper

def test_prepare_writes_only_plan(fresh):
    plan = core._prepare_test_plan(fresh, core.DEVELOPMENT_PKG)
    assert sorted(p.name for p in fresh.iterdir()) == ["pre_run_plan.json"]
    assert plan["schema"] == core.TEST_PLAN_SCHEMA
    assert plan["run_id"] == core.TEST_RUN_ID
    assert plan["domain"]["candidate"] == "V5-C2"
    assert plan["domain"]["frame_count_per_stratum"] == 128
    assert plan["gates"]["successes_per_stratum"] == 126
    assert len(plan["seed_schedule"]["roots"]) == 4
    assert plan["seed_schedule"]["seed_count"] == 512
    with pytest.raises(FileExistsError):
        core._prepare_test_plan(fresh, core.DEVELOPMENT_PKG)


def test_plan_tamper_rejected(fresh):
    core._prepare_test_plan(fresh, core.DEVELOPMENT_PKG)
    plan = core._json_read(fresh / "pre_run_plan.json")
    tampered = dict(plan)
    tampered["gates"] = {"denominator_per_stratum": 999, "successes_per_stratum": 126,
                         "forbidden_failure_count_limit": 0, "strata": list(core.CHANNEL_STRATA)}
    with pytest.raises(ValueError, match="plan self hash"):
        core._validate_plan(tampered, test_only=True, output_dir=fresh)
    changed = json.loads(core._compact(plan).decode("ascii"))
    changed["development_binding"]["policy_manifest_sha256"] = "0" * 64
    changed = core._self({k: v for k, v in changed.items() if k != "plan_sha256"}, "plan_sha256")
    with pytest.raises(ValueError, match="development binding"):
        core._validate_plan(changed, test_only=True, output_dir=fresh)
    changed2 = json.loads(core._compact(plan).decode("ascii"))
    changed2["generator"]["delta_order"] = "zero,plus_one,minus_one"
    changed2 = core._self({k: v for k, v in changed2.items() if k != "plan_sha256"}, "plan_sha256")
    with pytest.raises(ValueError, match="generator contract"):
        core._validate_plan(changed2, test_only=True, output_dir=fresh)
    core._validate_plan(plan, test_only=True, output_dir=fresh)


def test_root_collision_with_development_rejected(fresh):
    dev_plan = core._json_read(core.DEVELOPMENT_PKG / "pre_run_plan.json")
    dev_root = bytes.fromhex(dev_plan["seed_schedule"]["roots"][0]["root_hex"])
    with patch.object(core.secrets, "token_bytes", side_effect=[dev_root] + [bytes([0x11 + i]) * 32 for i in range(7)]):
        with pytest.raises(ValueError, match="development root collision"):
            core._prepare_test_plan(fresh, core.DEVELOPMENT_PKG)


def test_root_collision_with_predecessor_rejected(fresh):
    prior_roots, _ = core.dev._extract_prior()
    prior = bytes.fromhex(prior_roots[0])
    with patch.object(core.secrets, "token_bytes", side_effect=[prior] + [bytes([0x21 + i]) * 32 for i in range(7)]):
        with pytest.raises(ValueError, match="predecessor root collision"):
            core._prepare_test_plan(fresh, core.DEVELOPMENT_PKG)


def test_seed_schedule_reconstruction(fresh):
    core._prepare_test_plan(fresh, core.DEVELOPMENT_PKG)
    plan = core._json_read(fresh / "pre_run_plan.json")
    rebuilt = core._seed_schedule(plan["generator"]["roots"], private=True,
                                  development_dir=Path(plan["development_binding"]["path"]))
    assert plan["seed_schedule"] == rebuilt


def test_tampered_development_prerequisite_rejected_before_output(fresh):
    bad = ROOT / "workspace" / "ldpc_v5_synthetic_tests" / f"bad_dev_{uuid.uuid4().hex}"
    shutil.copytree(core.DEVELOPMENT_PKG, bad)
    (bad / "development_report.json").write_bytes((bad / "development_report.json").read_bytes() + b" ")
    out = fresh / "out"
    with pytest.raises(ValueError):
        core._prepare_test_plan(out, bad)
    assert not out.exists()
    shutil.rmtree(bad, ignore_errors=True)


def test_missing_development_dir_rejected():
    with pytest.raises((ValueError, FileNotFoundError, OSError)):
        core._prepare_test_plan(ROOT / "workspace" / f"x_missing_{uuid.uuid4().hex[:8]}",
                                ROOT / "workspace" / "no_such_development_pkg")


# ---------------------------------------------------------------- T2 full fake lifecycle

def test_full_lifecycle_completed_non_promoted(fresh):
    out = _prepare_and_execute(fresh)
    assert sorted(p.name for p in out.iterdir()) == sorted(core.ARTIFACTS)
    manifest = core._json_read(out / core.ARTIFACTS[8])
    assert manifest["run_status"] == "non_promoted"
    report = core._json_read(out / core.ARTIFACTS[9])
    assert report["promoted"] is False
    assert report["ready_for_real_qualification"] is False
    for gate in report["promotion_gates"].values():
        assert gate["denominator"] == 128
        assert gate["verified_success"] == 0
        assert gate["passed"] is False
    got = verify_cli.verify_output(out, _private_test_only=True)
    assert set(got) == {"status", "run_status", "outcomes", "selected_candidate_id",
                        "ready_for_real_qualification", "decoder_reexecution"}
    assert got["status"] == "verified"
    assert got["run_status"] == "non_promoted"
    assert got["outcomes"] == 256
    assert got["selected_candidate_id"] == "V5-C2"
    assert got["ready_for_real_qualification"] is False
    assert got["decoder_reexecution"] is False
    rows = decode_outcome_csv_v5((out / core.ARTIFACTS[6]).read_bytes())
    assert len(rows) == 256
    assert all(r["role"] == "confirmation" and r["stratum"] == "bw120" for r in rows)
    assert all(not r["attempted"] and r["status"] == "backend_unavailable" for r in rows)


def test_full_lifecycle_failed_exception(fresh):
    def boom(alice, bob, **kwargs):
        raise RuntimeError("fake decode failure")
    out = _prepare_and_execute(fresh, runner=boom)
    assert sorted(p.name for p in out.iterdir()) == sorted(core.ARTIFACTS)
    got = verify_cli.verify_output(out, _private_test_only=True)
    assert got["status"] == "verified"
    assert got["run_status"] == "invalid_execution"
    assert got["ready_for_real_qualification"] is False
    rows = decode_outcome_csv_v5((out / core.ARTIFACTS[6]).read_bytes())
    assert rows[0]["failure_reason"].startswith("package_internal:")
    assert not rows[0]["attempted"]


def test_full_lifecycle_cap(fresh):
    out = fresh
    core._prepare_test_plan(out, core.DEVELOPMENT_PKG)
    with patch.object(core.time, "monotonic", side_effect=[0.0, 1801.0]):
        core._execute_test_plan(out, _fake_runner)
    got = verify_cli.verify_output(out, _private_test_only=True)
    assert got["run_status"] == "invalid_execution"


def test_no_overwrite_and_no_resume(fresh):
    _prepare_and_execute(fresh)
    with pytest.raises(ValueError, match="requires only reviewed plan"):
        core._execute_test_plan(fresh, _fake_runner)


def test_tamper_csv_status_rejected(fresh):
    out = _prepare_and_execute(fresh)
    csv_path = out / core.ARTIFACTS[6]
    raw = csv_path.read_text(encoding="ascii")
    lines = raw.splitlines()
    header, first, *rest = lines
    tampered = "\n".join([header, first.replace("backend_unavailable", "verified_success"), *rest]) + "\n"
    csv_path.write_text(tampered, encoding="ascii")
    with pytest.raises(ValueError):
        verify_cli.verify_output(out, _private_test_only=True)


def test_tamper_manifest_rejected(fresh):
    out = _prepare_and_execute(fresh)
    man = core._json_read(out / core.ARTIFACTS[8])
    man["outcome_count"] = man["outcome_count"] - 1  # real drift; self-hash now invalid
    (out / core.ARTIFACTS[8]).write_bytes(core._compact(man))
    with pytest.raises(ValueError):
        verify_cli.verify_output(out, _private_test_only=True)


def test_tamper_policy_manifest_rejected(fresh):
    out = _prepare_and_execute(fresh)
    policy_path = out / core.ARTIFACTS[5]
    doc = core._json_read(policy_path)
    doc["manifest_sha256"] = "0" * 64
    (policy_path).write_bytes(core._compact(doc))
    with pytest.raises(ValueError):
        verify_cli.verify_output(out, _private_test_only=True)


def test_verify_is_read_only(fresh):
    out = _prepare_and_execute(fresh)
    before = {p.name: p.read_bytes() for p in out.iterdir()}
    verify_cli.verify_output(out, _private_test_only=True)
    verify_cli.verify_output(out, _private_test_only=True)
    after = {p.name: p.read_bytes() for p in out.iterdir()}
    assert before == after


def test_production_cli_guards_and_no_test_switch(fresh):
    source = Path(run_cli.__file__).read_text(encoding="utf-8")
    assert "--test" not in source and "test_only" not in source
    # production prepare requires the official output path
    with pytest.raises(ValueError, match="official output path"):
        run_cli.prepare_plan(fresh, core.DEVELOPMENT_PKG)
    # production prepare into the official dir requires the official development dir
    with pytest.raises(ValueError, match="development prerequisite path"):
        run_cli.prepare_plan(core.OFFICIAL_OUTPUT, fresh)
