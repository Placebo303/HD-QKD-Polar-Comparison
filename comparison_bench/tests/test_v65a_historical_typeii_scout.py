from __future__ import annotations

import importlib.util
import json
import math
import shutil
import sys
import uuid
from pathlib import Path

import numpy as np
import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "v65a_scout.py"
SPEC = importlib.util.spec_from_file_location("v65a_scout_under_test", SCRIPT)
V = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = V
SPEC.loader.exec_module(V)


@pytest.fixture
def workspace_case():
    path = SCRIPT.parents[1] / "workspace" / f"v65a_unit_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _pairs(frame_count: int) -> V.Observation:
    frames = np.repeat(np.arange(frame_count, dtype=np.int64), 256)
    pair_idx = np.tile(np.arange(256, dtype=np.int64), frame_count)
    alice = np.tile(np.arange(256, dtype=np.int64), frame_count)
    bob = (alice + 1) % 1024
    return V.Observation(frames, pair_idx, alice, bob, {}, "fixture")


def _payload(candidate: V.CandidateSpec, session_dir: Path, source: Path, *, channels=(7, 9)) -> dict:
    return {
        "session_id": candidate.candidate_id,
        "data_dir": str(session_dir),
        "ttbin": str(source),
        "dimension": 1024,
        "bin_width_ps": 200,
        "pairing": {"policy": "nearest", "assignment": "double_pointer_bin_div_dimension"},
        "processing_rule": "legacy_v1",
        "channels": {"A": channels[0], "B": channels[1]},
        "delay_used_ps": -50,
        "peak_center_ps": -50,
        "sigma_ps": 100,
        "gate_ps": 200,
        "threshold_ps": 40000,
        "frame_anchor": {"period_ps": 204800, "frame_bins": 1024, "division": "floor_div"},
        "mapping": "legacy_v1",
    }


def test_provenance_tiers_are_explicit_and_provisional():
    assert [c.provisional_tier for c in V.CANDIDATE_SPECS] == ["B", "B", "B"]
    assert all(c.tier_basis and c.tier_uncertainty for c in V.CANDIDATE_SPECS)


def test_candidate_order_is_frozen():
    assert V.FROZEN_ORDER == (
        "2026-01-13 162148",
        "2026-01-07 2500K",
        "2026-01-07 160254",
    )


def test_stage0_stops_at_first_pass_and_does_not_probe_later():
    seen = []

    def probe(candidate, root):
        seen.append(candidate.candidate_id)
        return {"candidate_id": candidate.candidate_id, "verify_pass": len(seen) == 2, "materialized_frames": 8}

    result = V.run_stage0(None, probe=probe)
    assert seen == [V.FROZEN_ORDER[0], V.FROZEN_ORDER[1]]
    assert result["selected"] == V.FROZEN_ORDER[1]
    assert result["not_materialized_later_candidates"] == [V.FROZEN_ORDER[2]]
    assert result["materialized_frames_total"] == 16
    assert result["batch_guard_pass"]


def test_stage0_all_fail_checks_all_candidates():
    def probe(candidate, root):
        return {"candidate_id": candidate.candidate_id, "verify_pass": False, "materialized_frames": 8}

    result = V.run_stage0(None, probe=probe)
    assert result["selected"] is None
    assert result["checked_candidates"] == list(V.FROZEN_ORDER)
    assert result["materialized_frames_total"] == 24
    assert result["none_passed"]


def test_candidate_specific_channels_are_not_assumed_to_be_1_and_5(workspace_case):
    candidate = V.CANDIDATE_SPECS[1]
    source = workspace_case / "raw.ttbin"
    source.write_bytes(b"raw")
    sidecar = workspace_case / "sidecar.json"
    payload = _payload(candidate, workspace_case, source, channels=(7, 9))
    sidecar.write_text("{}", encoding="utf-8")
    discovery = {"source_path": source, "session_dir": workspace_case, "sidecar_paths": [sidecar]}
    checked = V.validate_candidate_metadata(candidate, discovery, payload)
    assert checked["checks"]["channels"]
    assert checked["metadata"]["channels_used"] == {"A": 7, "B": 9}
    assert checked["verify_pass"]


def test_provenance_path_conflict_blocks_stage0(workspace_case):
    candidate = V.CANDIDATE_SPECS[0]
    source = workspace_case / "raw.ttbin"
    source.write_bytes(b"raw")
    sidecar = workspace_case / "sidecar.json"
    sidecar.write_text("{}", encoding="utf-8")
    payload = _payload(candidate, workspace_case, source)
    payload["data_dir"] = r"D:\SPDC源测试\2026.1.13\other-session"
    payload["ttbin"] = r"D:\SPDC源测试\2026.1.13\other-session\raw.ttbin"
    discovery = {"source_path": source, "session_dir": workspace_case, "sidecar_paths": [sidecar]}
    checked = V.validate_candidate_metadata(candidate, discovery, payload)
    assert not checked["checks"]["provenance"]
    assert not checked["verify_pass"]
    assert checked["status"] == "V65A_INCOMPATIBLE"


def test_ambiguous_sidecars_expose_external_provenance_conflict(workspace_case):
    candidate = V.CANDIDATE_SPECS[0]
    session = workspace_case.joinpath(*candidate.path_parts)
    session.mkdir(parents=True)
    source = session / candidate.raw_name
    source.write_bytes(b"raw")
    payload = _payload(candidate, session, source)
    payload["data_dir"] = r"D:\SPDC源测试\2026.1.13\162148"
    payload["ttbin"] = r"D:\SPDC源测试\2026.1.13\162148\raw.ttbin"
    for name in ("first.meta.json", "second.meta.json"):
        (session / name).write_text(json.dumps(payload), encoding="utf-8")

    result = V.probe_candidate(candidate, workspace_case)
    assert result["status"] == "V65A_INCOMPATIBLE"
    assert result["provenance_conflict"]
    assert len(result["sidecar_details"]) == 2
    assert all(not item["source_dir_matches_candidate"] for item in result["sidecar_details"])


def test_missing_sidecar_is_data_not_ready_without_raw_read(workspace_case):
    root = workspace_case / "root"
    session = root / "2026.1.7"
    session.mkdir(parents=True)
    source = session / V.CANDIDATE_SPECS[1].raw_name
    source.write_bytes(b"raw")
    result = V.probe_candidate(V.CANDIDATE_SPECS[1], root)
    assert result["status"] == "V65A_DATA_NOT_READY"
    assert result["materialized_frames"] == 0


def test_pair_contract_requires_256_pairs_and_symbols():
    valid = V.validate_pairs(_pairs(8), 8)
    assert valid["pass"]
    broken = _pairs(8)
    broken.pair_idx[0] = 999
    assert not V.validate_pairs(broken, 8)["pass"]


def test_conditional_entropy_chain_uses_a_given_b():
    counts = np.zeros((1024, 1024), dtype=float)
    counts[0, 0] = 1
    counts[32, 0] = 1
    counts[0, 1] = 1
    counts[1, 1] = 1
    h_full, h_u1, h_u2 = V._conditional_entropy_parts(counts)
    assert h_full == pytest.approx(1.0)
    assert h_u1 == pytest.approx(0.5)
    assert h_u2 == pytest.approx(0.5)
    assert h_full == pytest.approx(h_u1 + h_u2)


def test_stage1_short_sample_cannot_be_ready():
    result = V.coarse_screen(_pairs(8), excluded_frame_ids=[])
    assert result["coarse_cannot_ready"]
    assert result["overall"] == "V65A_COARSE_REJECTED"
    assert "READY" not in result["overall"]


def test_formal_stage_is_plan_only_and_test_identity_only():
    plan = V.formal_plan("2026-01-07 2500K", [1, 2])
    assert plan["planned_only"]
    assert plan["TEST"]["identity_only"]
    assert not plan["TEST"]["statistics_used"]
    assert plan["sealed_test_identity"]["frames"] is None


def test_source_has_no_forbidden_execution_or_history_fallback_tokens():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "decode_" not in text
    assert "outcome.json" not in text
    assert "synthetic" not in text.lower()


def test_metadata_missing_fields_fails_closed(workspace_case):
    candidate = V.CANDIDATE_SPECS[2]
    source = workspace_case / "raw.ttbin"
    source.write_bytes(b"raw")
    sidecar = workspace_case / "sidecar.json"
    sidecar.write_text("{}", encoding="utf-8")
    discovery = {"source_path": source, "session_dir": workspace_case, "sidecar_paths": [sidecar]}
    checked = V.validate_candidate_metadata(candidate, discovery, {})
    assert not checked["verify_pass"]
    assert checked["status"] == "V65A_INCOMPATIBLE"


def test_required_m_no_cap_no_floor_handfill():
    # R65A-05: m=ceil(1.3*1024*CE/5) no cap/floor/handfill
    assert V.required_m_from_ce(5.0) == int(math.ceil(1.3 * 1024 * 5.0 / 5.0))
    assert V.required_m_from_ce(0.0) == 0
    text = SCRIPT.read_text(encoding="utf-8")
    # ensure no cap pseudo like min(16, ceil) or min/max wrapping for m1/m2
    lower = text.lower()
    assert "min(16" not in lower and "min( 16" not in lower
    assert "max(" not in lower or "maximum" in lower  # allow np.maximum for prob clamping only


def test_rate_branch_over_capacity_maps_to_adaptation_and_full_disclosure():
    # R65A-05: stable but exceeds frozen and <1024 => RATE_ADAPTATION_REQUIRED; >=1024 => FULL_DISCLOSURE_LAYER
    assert V.classify_required_rate(17, 10, lambda_at_boundary=False, model_stable=True) == "RATE_ADAPTATION_REQUIRED"
    assert V.classify_required_rate(10, 201, lambda_at_boundary=False, model_stable=True) == "RATE_ADAPTATION_REQUIRED"
    assert V.classify_required_rate(500, 500, lambda_at_boundary=False, model_stable=True) == "RATE_ADAPTATION_REQUIRED"
    assert V.classify_required_rate(1024, 10, lambda_at_boundary=False, model_stable=True) == "FULL_DISCLOSURE_LAYER"
    assert V.classify_required_rate(10, 1024, lambda_at_boundary=False, model_stable=True) == "FULL_DISCLOSURE_LAYER"
    assert V.classify_required_rate(600, 600, lambda_at_boundary=False, model_stable=True) == "FULL_DISCLOSURE_LAYER"
    # frozen compatible stays compatible
    assert V.classify_required_rate(16, 200, lambda_at_boundary=False, model_stable=True) == "FROZEN_RATE_COMPATIBLE"
    assert V.classify_required_rate(10, 10, lambda_at_boundary=False, model_stable=True) == "FROZEN_RATE_COMPATIBLE"


def test_model_not_stable_priority_over_rate():
    # R65A-05: MODEL_NOT_STABLE has priority even if rate would be FULL_DISCLOSURE
    assert V.classify_required_rate(1024, 1024, lambda_at_boundary=True, model_stable=True) == "MODEL_NOT_STABLE"
    assert V.classify_required_rate(10, 10, lambda_at_boundary=True, model_stable=True) == "MODEL_NOT_STABLE"
    assert V.classify_required_rate(10, 10, lambda_at_boundary=False, model_stable=False) == "MODEL_NOT_STABLE"


def test_stage1_never_grants_rate_ready_even_when_rate_adaptation():
    # R65A-04: Stage1 256/64 never grants READY/RATE_READY, only REJECT or ELIGIBLE_FOR_FORMAL
    result = V.coarse_screen(_pairs(320), excluded_frame_ids=[])
    assert result["coarse_cannot_ready"] is True
    assert "READY" not in result["overall"] or result["overall"] == "V65A_COARSE_REJECTED" or result["overall"] == "V65A_ELIGIBLE_FOR_FORMAL"
    assert result["overall"] in ("V65A_COARSE_REJECTED", "V65A_ELIGIBLE_FOR_FORMAL")
    # rate branch is informative but overall stays ELIGIBLE/REJECT
    assert result["required_rate_classification"] in ("MODEL_NOT_STABLE", "FROZEN_RATE_COMPATIBLE", "RATE_ADAPTATION_REQUIRED", "FULL_DISCLOSURE_LAYER")


def test_missing_data_returns_data_not_ready(workspace_case):
    # R65A-08 / R65A-03: sidecar missing or ambiguous => DATA_NOT_READY not crash, no raw read fallback
    candidate = V.CANDIDATE_SPECS[1]
    missing_root = workspace_case / "missing_root"
    result = V.probe_candidate(candidate, missing_root)
    assert result["status"] == "V65A_DATA_NOT_READY"
    assert result["materialized_frames"] == 0


def test_workspace_uuid_basetemp_no_tempfile_usage():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "TemporaryDirectory" not in text
    assert "tempfile" not in text.lower()
    # formal plan must declare Stage2 still plan-only with at least CAL1024/VAL256/TEST32
    plan = V.formal_plan("2026-01-13 162148", [])
    assert plan["CAL"]["frames"] == 1024 and plan["VAL"]["frames"] == 256 and plan["TEST"]["frames"] == 32
    assert plan["planned_only"] is True
