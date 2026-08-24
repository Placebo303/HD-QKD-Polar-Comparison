"""Focused T0/T1/fake checks for the V34 candidate CLI.

Every execute flow below injects ``FakeV34Provider`` explicitly and writes to a
fresh child of ``workspace/``. No test is allowed to construct the production
runner or the official V34 root.
"""
from __future__ import annotations

import importlib
import json
import shutil
import uuid
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.cli import (
    run_nonbinary_v34_corrected_matched_empirical_p_finite_control as v34,
)


class FakeV34Provider:
    """Explicit fake binding/runner seam; no decoder dependency."""

    def __init__(self, mode: str = "pass"):
        self.counts = {source: np.ones((v34.N, v34.N), dtype=np.float64)
                       for source in v34.SOURCE_ORDER}
        self.mode = mode
        self.calls: list[dict] = []

    def binding_context(self, _repo_root: Path):
        return {
            "mode": "fake",
            "bindings": {
                "ok": True,
                "schema": "fake_v34_bindings_v1",
                "bindings": {"fixture": {"sha256": "fixture"}},
            },
            "counts": self.counts,
        }

    def run_call(self, request: dict):
        self.calls.append(request)
        if self.mode == "fail":
            return {"exact_l2": False, "syndrome_ok": True,
                    "tag_ok": True, "false_accept": False,
                    "l2_status": "max_iter", "l2_iterations": v34.MAX_ITER}
        if self.mode == "fatal":
            raise RuntimeError("fake interface failure")
        if self.mode == "malformed":
            return {"exact_l2": 1, "syndrome_ok": True,
                    "tag_ok": True, "false_accept": False}
        if self.mode == "nonfinite":
            return {"exact_l2": True, "syndrome_ok": True,
                    "tag_ok": True, "false_accept": False,
                    "runtime_s": float("nan")}
        return {"exact_l2": True, "syndrome_ok": True,
                "tag_ok": True, "false_accept": False,
                "l2_status": "converged", "l2_iterations": 20}


def _fresh_root() -> Path:
    root = v34.WORKSPACE_ROOT / f"v34_impl_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=False)
    root.rmdir()
    return root


@pytest.fixture
def fake_pass():
    provider = FakeV34Provider("pass")
    root = _fresh_root()
    try:
        yield provider, root
    finally:
        if root.exists():
            shutil.rmtree(root)


FAKE_VERIFY = FakeV34Provider("pass")


def test_t0_compile_import_help_and_lazy_decoder():
    module = importlib.import_module(v34.__name__)
    assert module.NUMPY_REQUIRED == "2.4.0"
    assert len(module.enumerate_calls()) == 60
    assert "comparison_bench.src.comparison_bench.cli.run_nonbinary_v32_finite_de_bridge" not in module.sys.modules
    assert v34.main(["test-selfcheck"]) == v34.EXIT_OK


def test_t0_ref1_and_exact_sampler_determinism():
    assert v34.check_sampler_reference()
    counts = np.ones((v34.N, v34.N), dtype=np.float64)
    first = v34.sample_empirical_block(counts, 340101)
    second = v34.sample_empirical_block(counts, 340101)
    for a, b in zip(first, second):
        np.testing.assert_array_equal(a, b)
    assert first[0].shape == (v34.N,)
    assert np.all(first[1] == first[0] // v34.N)
    assert np.all(first[2] == first[0] % v34.N)


def test_t0_schedule_and_authorization_digest():
    calls = v34.enumerate_calls()
    assert [(c["source"], c["seed"]) for c in calls[:2]] == [("1M", 340101), ("1M", 340102)]
    assert calls[20]["source"] == "1p5M" and calls[40]["source"] == "2M"
    assert len({(c["source"], c["block"], c["seed"]) for c in calls}) == 60
    auth = dict(v34.AUTH_EXACT_VALUES)
    auth.update({"implementation_commit": v34.git_head(),
                 "call_matrix_digest": v34.expected_call_matrix_digest(),
                 "granted_by": "test", "decision_id": "test-v34", "granted": True})
    assert v34.validate_execute_auth(auth) is None
    assert v34.validate_execute_auth(dict(auth, decision="NO"))
    assert v34.validate_execute_auth(dict(auth, call_matrix_digest="0" * 64))
    assert v34.validate_execute_auth(dict(auth, implementation_commit="0" * 40))
    assert v34.validate_execute_auth(dict(auth, extra=True))


def test_t1_stage0_real_readonly_and_no_official_root():
    report, counts = v34.stage0_validate(v34.REPO_ROOT)
    assert report["ok"] is True
    assert report["sampler_reference"] is True
    assert report["packet"]["m2"] == v34.M2
    assert set(counts) == set(v34.SOURCE_ORDER)
    assert not v34.OFFICIAL_RUN_ROOT.exists()


def test_t1_probability_fail_closed():
    bad = np.ones((v34.N, v34.N), dtype=np.float64)
    bad[0, 0] = np.nan
    with pytest.raises(ValueError, match="nonfinite_counts"):
        v34.sample_empirical_block(bad, 340101)
    zero = np.zeros((v34.N, v34.N), dtype=np.float64)
    with pytest.raises(ValueError, match="invalid_total"):
        v34.sample_empirical_block(zero, 340101)


def test_t1_fake_end_to_end_exact_60_and_strict_verify(fake_pass):
    provider, root = fake_pass
    rc, final = v34.execute_run(v34.REPO_ROOT, root, provider=provider, fake=True,
                                 auth_info={"mechanism": "fake_runner"})
    assert rc == v34.EXIT_OK
    assert final["overall_terminal"] == v34.TERMINAL_PASS
    assert len(provider.calls) == 60
    records = json.loads((root / "block_records.json").read_text())["records"]
    assert len(records) == 60
    assert [r["ordinal"] for r in records] == list(range(1, 61))
    assert all(r["truth_role"] == "oracle_l1" and r["operational"] is False for r in records)
    assert all(r["sampler_choice_calls"] == 1 for r in records)
    assert v34.cmd_verify(type("Args", (), {"run_root": str(root), "runner": None})()) == v34.EXIT_EVIDENCE_INCONSISTENT
    assert v34.cmd_verify(type("Args", (), {"run_root": str(root),
                                               "runner": f"{__name__}:FAKE_VERIFY"})()) == v34.EXIT_OK


def test_t1_fake_ordinary_fail_continues_and_threshold_terminal():
    provider = FakeV34Provider("fail")
    root = _fresh_root()
    try:
        rc, final = v34.execute_run(v34.REPO_ROOT, root, provider=provider, fake=True,
                                    auth_info={"mechanism": "fake_runner"})
        assert rc == v34.EXIT_OK
        assert final["overall_terminal"] == v34.TERMINAL_FAIL
        assert len(provider.calls) == 60
    finally:
        if root.exists():
            shutil.rmtree(root)


def test_t1_fatal_stops_and_no_resume_or_run02():
    provider = FakeV34Provider("fatal")
    root = _fresh_root()
    try:
        rc, final = v34.execute_run(v34.REPO_ROOT, root, provider=provider, fake=True,
                                    auth_info={"mechanism": "fake_runner"})
        assert rc == v34.EXIT_EVIDENCE_INCONSISTENT
        assert final["overall_terminal"] == v34.TERMINAL_INCONCLUSIVE
        assert len(provider.calls) == 1
        assert not (root.parent / "run_02").exists()
        before = {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}
        rc2, _ = v34.execute_run(v34.REPO_ROOT, root, provider=provider, fake=True,
                                 auth_info={"mechanism": "fake_runner"})
        assert rc2 == v34.EXIT_COLLISION
        after = {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}
        assert before == after
    finally:
        if root.exists():
            shutil.rmtree(root)


@pytest.mark.parametrize("mode", ["malformed", "nonfinite"])
def test_t1_malformed_or_nonfinite_decoder_result_is_fatal(mode):
    provider = FakeV34Provider(mode)
    root = _fresh_root()
    try:
        rc, final = v34.execute_run(v34.REPO_ROOT, root, provider=provider, fake=True,
                                    auth_info={"mechanism": "fake_runner"})
        assert rc == v34.EXIT_EVIDENCE_INCONSISTENT
        assert final["overall_terminal"] == v34.TERMINAL_INCONCLUSIVE
        assert len(provider.calls) == 1
    finally:
        if root.exists():
            shutil.rmtree(root)


def test_t1_strict_replay_rejects_record_tamper(fake_pass):
    provider, root = fake_pass
    assert v34.execute_run(v34.REPO_ROOT, root, provider=provider, fake=True,
                           auth_info={"mechanism": "fake_runner"})[0] == v34.EXIT_OK
    payload = json.loads((root / "block_records.json").read_text())
    payload["records"][0]["sampled_ser"] += 0.01
    (root / "block_records.json").write_text(json.dumps(payload), encoding="utf-8")
    assert v34.cmd_verify(type("Args", (), {"run_root": str(root),
                                               "runner": f"{__name__}:FAKE_VERIFY"})()) == v34.EXIT_EVIDENCE_INCONSISTENT


def test_t1_unauthorized_execute_has_zero_side_effects():
    root = _fresh_root()
    try:
        rc = v34.main(["execute", "--run-root", str(root)])
        assert rc == v34.EXIT_UNAUTHORIZED
        assert not root.exists()
    finally:
        if root.exists():
            shutil.rmtree(root)


def test_t1_official_root_never_created_by_fake(fake_pass):
    provider, root = fake_pass
    v34.execute_run(v34.REPO_ROOT, root, provider=provider, fake=True,
                    auth_info={"mechanism": "fake_runner"})
    assert not v34.OFFICIAL_RUN_ROOT.exists()
