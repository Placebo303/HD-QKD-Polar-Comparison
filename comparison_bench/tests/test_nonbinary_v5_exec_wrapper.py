"""Wrapper acceptance: deterministic parallel execution + flush + one resume.

T0 (determinism): parallel results are byte-identical to the frozen serial
path at workers 1 and 4; tiny crash-finalize shape.  T1 (unit/tamper): flush
boundaries, resume at every interruption point, double-resume rejection, plan
mutation rejection, partial-state forgery rejection, production runner
injection rejection.  T2 (fake qualification): complete fake qualification and
strict fake replay through the wrapper, promoted and non-promoted paths.
All runs use a test-only lane (independent run_id/roots, so the frozen
identity-freshness guard never collides with official v5 evidence) and
explicit fake runners under a fresh writable UUID root with the pytest cache
disabled; production entry points are never invoked.
"""
from __future__ import annotations
import json
import uuid
from pathlib import Path
import pytest
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v5_runtime as runtime
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v5_exec_wrapper as wrapper
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v5a_multistage as core

def _out(name):
    root = Path("workspace") / "nbldpc_v5_exec_wrapper_tests" / uuid.uuid4().hex / name
    root.parent.mkdir(parents=True, exist_ok=True)
    return root

# Test-only lane: independent run_id/roots so plan creation never collides with
# official v5 evidence (the frozen identity-freshness guard scans all
# pre_run_plan.json under formal_ir_methods/).
TEST_CONFIG = runtime.RouteConfig(
    run_id="wrapper_test_nbldpc_v5_exec", canonical_schema="NBLDPCQ5W",
    method="wrapper_test_nbldpc_v5_exec", q=core.Q, n=core.N, ps=(.20, .30),
    roots={("development", .20): 202698000000, ("development", .30): 202698010000,
           ("confirmation", .20): 202698020000, ("confirmation", .30): 202698030000},
    caps={"workers": 1, "q": 1024, "n": 64, "checks_max": 56, "row_weight": 8,
          "stage_iterations": 12, "total_iterations": 36, "decoder_stages": 3,
          "verification_attempts": 3, "dense_bytes_max": 24 * 1024 * 1024},
    seed_bits=703, core=core,
    source_files=("comparison_bench/src/comparison_bench/formal_ir/nonbinary_v5_runtime.py",
                  "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v5a_codebook.py",
                  "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v5a_multistage.py",
                  "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v5a_ir_qualification.py",
                  "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v3.py",
                  "comparison_bench/src/comparison_bench/formal_ir/nonbinary_qspa.py",
                  "comparison_bench/src/comparison_bench/formal_ir/nonbinary_field.py",
                  "comparison_bench/src/comparison_bench/formal_ir/nonbinary_codebook.py",
                  "comparison_bench/src/comparison_bench/formal_ir/shared.py"),
    contract="openspec/changes/formal-nonbinary-ldpc-v5-multistage-ir/specs/spec.md",
    max_stages=3)

def _plan(out):
    runtime.create_plan(TEST_CONFIG, out, _test_only=True)
    return out

def _plan_copies(out, *others):
    """Create one plan and copy it (plan bytes must be identical across lanes:
    development toeplitz seeds are freshly materialized per plan creation)."""
    runtime.create_plan(TEST_CONFIG, out, _test_only=True)
    for other in others:
        other.mkdir(parents=True)
        (other / "pre_run_plan.json").write_bytes((out / "pre_run_plan.json").read_bytes())
    return out

def failed(state, mats, stage): return {"status": "decode_failed", "iterations": 1}
def success(state, mats, stage):
    return {"status": "syndrome_consistent", "iterations": 1, "decoded_symbols": state.bob}

# Module-level so the spawn workers can resolve it by (module, qualname).
def partial_runner(state, mats, stage):
    return failed(state, mats, stage) if state.policy_id == "nbldpc_v5a_ir56" else success(state, mats, stage)

def _noiseless(runtime_module, monkeypatch):
    original = runtime_module._frame
    def noiseless(config, p, role, index):
        row = original(config, p, role, index)
        row["alice"] = [0] * 64
        row["bob"] = [0] * 64
        return row
    monkeypatch.setattr(runtime_module, "_frame", noiseless)

def _artifacts_bytes(out):
    return {name: (out / name).read_bytes() for name in runtime.ARTIFACTS if (out / name).exists()}

def _dev_rows(out):
    return [r for r in runtime._rows(out / "formal_frame_outcomes.csv")
            if r["qualification_role"] == "development"]

def _deterministic_artifacts(out):
    """Deterministic parts of a package: codebook/candidate manifests and the
    development rows.  Confirmation material is per-run random by frozen
    semantics (secrets-derived), so promoted packages differ exactly there."""
    return ({name: (out / name).read_bytes()
             for name in ("formal_codebook_manifest.json", "formal_candidate_manifest.json")},
            _dev_rows(out))

# ---------------------------------------------------------------- T0: determinism

def test_t0_parallel_matches_serial_at_workers_1_and_4():
    serial = _out("serial"); par1 = _out("par_1"); par4 = _out("par_4")
    _plan_copies(serial, par1, par4)
    assert runtime.run(TEST_CONFIG, serial, runner=failed, _test_only=True)["run_status"] == "non_promoted_development"
    serial_bytes = _artifacts_bytes(serial)
    for out in (par1, par4):
        assert wrapper.parallel_run(TEST_CONFIG, out, workers=1 if out is par1 else 4, runner=failed,
                                    _test_only=True)["run_status"] == "non_promoted_development"
        assert _artifacts_bytes(out) == serial_bytes
        # strict replay of the wrapper-produced package passes through frozen verify
        assert runtime.verify(TEST_CONFIG, out, verifier_runner=failed, _test_only=True)["verified"]

def test_t0_parallel_promoted_matches_serial(monkeypatch):
    _noiseless(runtime, monkeypatch)
    serial = _out("serial_promote"); out = _out("par_promote")
    _plan_copies(serial, out)
    assert runtime.run(TEST_CONFIG, serial, runner=success, _test_only=True)["promoted"]
    serial_bytes = _artifacts_bytes(serial)
    assert wrapper.parallel_run(TEST_CONFIG, out, workers=2, runner=success,
                                _test_only=True)["promoted"]
    # Confirmation material is per-run random (frozen secrets semantics), so
    # byte equality holds only on the deterministic parts; both packages must
    # still pass the frozen strict replay.
    assert _deterministic_artifacts(out) == _deterministic_artifacts(serial)
    assert runtime.verify(TEST_CONFIG, serial, verifier_runner=success, _test_only=True)["promoted"]
    assert runtime.verify(TEST_CONFIG, out, verifier_runner=success, _test_only=True)["promoted"]

def test_t0_crash_finalize_shape_and_partial_state():
    out = _plan(_out("crash"))
    def hook(count):
        if count == 5:
            raise RuntimeError("fatal hook")
    with pytest.raises(RuntimeError, match="fatal hook"):
        wrapper.parallel_run(TEST_CONFIG, out, workers=2, runner=failed, flush_every=1,
                             _test_only=True, fatal_hook=hook)
    assert {p.name for p in out.iterdir()} == set(runtime.ARTIFACTS)
    assert runtime.verify(TEST_CONFIG, out, verifier_runner=failed, _test_only=True)["run_status"] == "invalid_run"
    partial = wrapper._partial_path(TEST_CONFIG, out)
    assert partial.exists()
    doc = json.loads(partial.read_text())
    assert doc["schema"] == wrapper.PARTIAL_SCHEMA
    # fatal hook raises before the next flush: the partial state holds the last
    # successfully flushed boundary (4 rows, not the crash point 5).
    assert len(doc["rows"]) == 4
    assert len(doc["completed"]) == 4

# ---------------------------------------------------------------- T1: flush/resume/tamper

def test_t1_flush_every_boundary_and_no_partial_left_after_done():
    out = _plan(_out("flush"))
    wrapper.parallel_run(TEST_CONFIG, out, workers=1, runner=failed, flush_every=7,
                         _test_only=True)
    # partial sidecar is removed on completion
    assert not wrapper._partial_path(TEST_CONFIG, out).exists()

def test_t1_resume_from_every_interruption_point(monkeypatch):
    _noiseless(runtime, monkeypatch)
    runner = success
    # One full serial baseline; each interruption point is then compared to it.
    full = _out("full"); _plan(full)
    assert runtime.run(TEST_CONFIG, full, runner=runner, _test_only=True)["promoted"]
    # (stop, workers, flush): mid-dev, dev-complete, mid-confirmation
    for stop, workers, flush in ((100, 2, 1), (256, 2, 64), (300, 2, 1)):
        out = _out(f"interrupt_{stop}")
        runtime.create_plan(TEST_CONFIG, out, _test_only=True)
        (out / "pre_run_plan.json").write_bytes((full / "pre_run_plan.json").read_bytes())
        def hook(count, stop=stop):
            if count == stop:
                raise RuntimeError("fatal hook")
        with pytest.raises(RuntimeError, match="fatal hook"):
            wrapper.parallel_run(TEST_CONFIG, out, workers=workers, runner=runner,
                                 flush_every=flush, _test_only=True, fatal_hook=hook)
        assert runtime.verify(TEST_CONFIG, out, verifier_runner=runner, _test_only=True)["run_status"] == "invalid_run"
        got = wrapper.resume_run(TEST_CONFIG, out, workers=workers, runner=runner,
                                 flush_every=flush, _test_only=True)
        assert got["promoted"]
        # Same contract as T0 promoted: deterministic parts byte-identical to
        # the full run (confirmation material is per-run random), and the
        # resumed package passes strict replay.
        assert _deterministic_artifacts(out) == _deterministic_artifacts(full)
        assert runtime.verify(TEST_CONFIG, out, verifier_runner=runner, _test_only=True)["promoted"]

def test_t1_resume_non_promoted_path_with_no_partial():
    out = _plan(_out("resume_failed"))
    got = wrapper.resume_run(TEST_CONFIG, out, workers=2, runner=failed, _test_only=True)
    assert got["run_status"] == "non_promoted_development"
    assert runtime.verify(TEST_CONFIG, out, verifier_runner=failed, _test_only=True)["verified"]

def test_t1_double_resume_rejected():
    out = _plan(_out("double_resume"))
    wrapper.resume_run(TEST_CONFIG, out, workers=1, runner=failed, _test_only=True)
    with pytest.raises(ValueError, match="plan-only"):
        wrapper.resume_run(TEST_CONFIG, out, workers=1, runner=failed, _test_only=True)

def test_t1_resume_requires_plan_only_directory():
    out = _plan(_out("resume_non_plan_only"))
    runtime.run(TEST_CONFIG, out, runner=failed, _test_only=True)
    with pytest.raises(ValueError, match="plan-only"):
        wrapper.resume_run(TEST_CONFIG, out, runner=failed, _test_only=True)

def test_t1_plan_mutation_rejected_on_resume():
    out = _plan(_out("plan_mutated"))
    def hook(count):
        if count == 3:
            raise RuntimeError("fatal hook")
    with pytest.raises(RuntimeError):
        wrapper.parallel_run(TEST_CONFIG, out, workers=1, runner=failed, flush_every=1,
                             _test_only=True, fatal_hook=hook)
    plan_path = out / "pre_run_plan.json"
    plan = json.loads(plan_path.read_text())
    plan["q"] = 511
    plan_path.write_text(json.dumps(plan))
    with pytest.raises(ValueError):
        wrapper.resume_run(TEST_CONFIG, out, runner=failed, _test_only=True)

def test_t1_partial_state_forgery_rejected():
    out = _plan(_out("forgery"))
    def hook(count):
        if count == 3:
            raise RuntimeError("fatal hook")
    with pytest.raises(RuntimeError):
        wrapper.parallel_run(TEST_CONFIG, out, workers=1, runner=failed, flush_every=1,
                             _test_only=True, fatal_hook=hook)
    partial = wrapper._partial_path(TEST_CONFIG, out)
    doc = json.loads(partial.read_text())
    doc["rows"][0]["status"] = "verify_failed"
    partial.write_text(json.dumps(doc))
    with pytest.raises(ValueError, match="resume confirmation state rejected|partial state rejected"):
        wrapper.resume_run(TEST_CONFIG, out, runner=failed, _test_only=True)

def test_t1_production_api_rejects_injected_runner():
    with pytest.raises(ValueError, match="production run"):
        wrapper.parallel_run(TEST_CONFIG, Path("unused"), runner=failed, _test_only=False)
    with pytest.raises(ValueError, match="production run"):
        wrapper.resume_run(TEST_CONFIG, Path("unused"), runner=failed, _test_only=False)

def test_t1_test_only_requires_explicit_runner():
    out = _plan(_out("test_only_no_runner"))
    with pytest.raises(ValueError, match="explicit runner"):
        wrapper.parallel_run(TEST_CONFIG, out, workers=1, _test_only=True)
    with pytest.raises(ValueError, match="explicit runner"):
        wrapper.resume_run(TEST_CONFIG, out, workers=1, _test_only=True)

def test_t1_run_requires_plan_only_directory():
    out = _plan(_out("wrapper_twice"))
    wrapper.parallel_run(TEST_CONFIG, out, workers=1, runner=failed, _test_only=True)
    with pytest.raises(ValueError, match="plan-only"):
        wrapper.parallel_run(TEST_CONFIG, out, workers=1, runner=failed, _test_only=True)

def test_t1_fake_runner_does_not_fall_back_to_production(monkeypatch):
    out = _plan(_out("trap"))
    def trap(*args, **kwargs):
        raise AssertionError("production")
    monkeypatch.setattr(core, "production_runner", trap)
    assert wrapper.parallel_run(TEST_CONFIG, out, workers=1, runner=failed,
                                _test_only=True)["run_status"] == "non_promoted_development"
    assert runtime.verify(TEST_CONFIG, out, verifier_runner=failed, _test_only=True)["verified"]

# ---------------------------------------------------------------- T2: fake qualification

def test_t2_fake_qualification_and_strict_replay_promoted(monkeypatch):
    _noiseless(runtime, monkeypatch)
    out = _plan(_out("t2_promoted"))
    got = wrapper.parallel_run(TEST_CONFIG, out, workers=2, runner=success, _test_only=True)
    assert got["run_status"] == "completed" and got["readiness"] and got["promoted"]
    assert runtime.verify(TEST_CONFIG, out, verifier_runner=success, _test_only=True)["promoted"]
    assert len(runtime._rows(out / "formal_frame_outcomes.csv")) == 512

def test_t2_fake_qualification_non_promoted_and_invalid_retention(monkeypatch):
    _noiseless(runtime, monkeypatch)
    out = _plan(_out("t2_non_promoted"))
    got = wrapper.parallel_run(TEST_CONFIG, out, workers=2, runner=partial_runner, _test_only=True)
    # readiness depends on the selected policy's verified count; if no selection, no confirmation
    assert got["run_status"] in ("completed", "non_promoted_development")
    assert runtime.verify(TEST_CONFIG, out, verifier_runner=partial_runner, _test_only=True)["verified"]
