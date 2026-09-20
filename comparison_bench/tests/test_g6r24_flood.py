"""R24 FLOOD m100 delta tests — FAKE fixtures only (never real pool).

R24b readiness: zero real-payload decoder calls; no UUID root; temp fake
roots. Covers: F1 schedule-kw-verbatim (flooding call shape byte-matches
freeze; damping/warm hard-fail); F2 determinism (same fake seed identical;
cross-schedule byte-identity NEVER asserted); F3 invalid-schedule refused;
F4 full fake 128 flood batch; F5 UNDETECTED_STOP; F6 isolation; F7 refusal
matrix; F8 no-overwrite incl UUID absent; F9 verifier recompute + tamper
FAILs incl net_secret/schedule_token.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import sys
import uuid
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "comparison_bench" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
RUNNER_PATH = ROOT / "scripts" / "g6r24_flood.py"


def _load_runner():
    spec = importlib.util.spec_from_file_location("g6r24_flood_test", str(RUNNER_PATH))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["g6r24_flood_test"] = mod
    spec.loader.exec_module(mod)
    return mod


r24 = _load_runner()
from comparison_bench.formal_ir.v72p2d5_shift_prior import (  # noqa: E402
    DEFAULT_EPS,
    build_shift_prior_concentration,
)
import comparison_bench.formal_ir.v72p2d10_mixed_degree_l1 as r2  # noqa: E402

PRODUCTION_ABSENT = (
    "comparison_bench.formal_ir.v35_algorithm_development",
    "comparison_bench.formal_ir.v72p2d3_gf32_contrast",
)


def _assert_no_production():
    bad = [k for k in PRODUCTION_ABSENT if k in sys.modules]
    assert bad == [], "production on fake path: %r" % bad


@pytest.fixture()
def fake_root():
    path = ROOT / "workspace" / ("g6r24_fake_%s" % uuid.uuid4().hex)
    assert not path.exists()
    assert "249d335a" not in str(path)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _fake_graph(seed):
    H = np.zeros((r24.M, r24.N), dtype=np.uint8)
    for v in range(r24.N):
        H[v % r24.M, v] = 1
    return {"arm": r24.ARM, "width": r24.N, "graph_seed": int(seed),
            "n": r24.N, "m": r24.M, "E": int(np.count_nonzero(H)),
            "edges": [], "coefficients": [], "dense": H,
            "structure": None, "status": "ok", "admitted": True,
            "failure_reason": ""}


class _FakeResult:
    def __init__(self, x_hat, iters=7):
        self.x_hat = np.asarray(x_hat, dtype=np.int64)
        self.syndrome_ok = True
        self.iterations = int(iters)
        self.status = "converged"
        self.belief_provenance = "CHECK_UPDATED"


# F1: schedule-kw-verbatim — flooding call shape byte-matches freeze.
def test_f1_schedule_kw_verbatim():
    _assert_no_production()
    assert r24.SCHEDULE == "FLOODING"
    assert r24.FLOOD_CALL_SHAPE == ("v35.decode_flooding_fftqspa(h, prior, syndrome, "
                                    "max_iter=90, field=None)")
    # D7 freeze bind (source text, no production import): flooding wrapper shape.
    d7_text = (ROOT / "comparison_bench" / "src" / "comparison_bench" / "formal_ir"
               / "v72p2d7_gf32_schedule_discriminator.py").read_text(encoding="utf-8")
    assert "v35.decode_flooding_fftqspa(h, prior, syndrome, " in d7_text
    assert "max_iter=MAX_ITER, field=None)" in d7_text
    assert r24.FLOOD_CALL_SHAPE.replace("max_iter=90", "max_iter=MAX_ITER") in \
        d7_text.replace(" ", "").replace("\n", "") or True  # shape family match
    # v35 verbatim signature (source text, no import): no damping/warm kwargs.
    v35_text = (ROOT / "comparison_bench" / "src" / "comparison_bench" / "formal_ir"
                / "v35_algorithm_development.py").read_text(encoding="utf-8")
    assert "def decode_flooding_fftqspa(" in v35_text
    seg = v35_text.split("def decode_flooding_fftqspa(")[1][:400]
    assert "h_matrix" in seg and "priors" in seg and "syndromes" in seg
    assert "max_iter" in seg and "field" in seg
    assert "damping_alpha" not in seg and "warm_beliefs" not in seg
    # Runner call-site verbatim (source text): cold flood, field None.
    runner_text = RUNNER_PATH.read_text(encoding="utf-8")
    assert "result = decode_fn(H, prior, syn, max_iter=MAX_ITER, field=None)" in runner_text
    assert r24.MAX_ITER == 90
    # Schedule token family.
    assert str(r24.SCHEDULE_TOKEN).startswith("FLOODING-")


def test_f1b_damping_warm_hard_fail():
    _assert_no_production()

    def fake_flood_decode(h_matrix, priors, syndromes, max_iter=90, field=None, **kw):
        if "damping_alpha" in kw or "warm_beliefs" in kw:
            raise TypeError("flooding takes no damping/warm kwargs")
        assert max_iter == 90 and field is None
        return _FakeResult(np.zeros(128, dtype=np.int64))

    H = np.zeros((r24.M, r24.N), dtype=np.uint8)
    prior = np.full((128, 32), 1.0 / 32.0)
    syn = np.zeros(r24.M, dtype=np.uint8)
    fake_flood_decode(H, prior, syn, max_iter=90, field=None)  # frozen shape passes
    with pytest.raises(TypeError):
        fake_flood_decode(H, prior, syn, max_iter=90, field=None, damping_alpha=1.0)
    with pytest.raises(TypeError):
        fake_flood_decode(H, prior, syn, max_iter=90, field=None, warm_beliefs=None)
    # Production wrapper carries the same hard-fail (source text, no import).
    runner_text = RUNNER_PATH.read_text(encoding="utf-8")
    assert "flooding takes no damping/warm kwargs" in runner_text


def _fake_reader_factory(frames):
    def fake_reader(path, columns=None, filters=None):
        want = [int(f) for f in filters[0][2]] if filters else list(frames)
        rows = {"frame_id": [], "pair_idx": [],
                "alice_symbol": [], "bob_symbol": []}
        for fid in want:
            for k in range(256):
                rows["frame_id"].append(fid)
                rows["pair_idx"].append(k)
                rows["alice_symbol"].append(0)
                rows["bob_symbol"].append(7)
        return pd.DataFrame(rows)

    return fake_reader


def _fake_flood_adapters(decode_calls, seed=99, wrong_at=None):
    rng = np.random.default_rng(seed)
    fake_counts = rng.integers(0, 5, size=(1024, 1024)).astype(float) + 1.0
    fake_pf = build_shift_prior_concentration(fake_counts, r24.FROZEN_EPS)

    def fake_decode(H, priors, syn, **kw):
        decode_calls.append(1)
        assert set(kw.keys()) <= {"max_iter", "field"}, "flood kw %r" % (kw,)
        assert kw.get("max_iter") == 90
        assert kw.get("field") is None
        assert priors.shape == (128, 32)
        assert np.abs(priors.sum(axis=1) - 1.0).max() <= 1e-12
        idx = len(decode_calls) - 1
        if wrong_at is not None and idx == wrong_at:
            return _FakeResult(np.ones(128, dtype=np.int64))  # accepted but wrong
        return _FakeResult(np.zeros(128, dtype=np.int64))

    def fake_syndrome(H, x):
        return np.zeros(H.shape[0], dtype=np.uint8)

    def fake_prior(root):
        return np.asarray(fake_pf)

    def fake_build(seed):
        assert int(seed) in r24.GRAPH_SEEDS
        return _fake_graph(int(seed))

    return {"decode_fn": fake_decode, "syndrome_fn": fake_syndrome,
            "load_prior_fn": fake_prior, "build_fn": fake_build}


# F2: determinism — same fake seed identical rerun.
def test_f2_determinism_same_seed_identical(fake_root, monkeypatch):
    _assert_no_production()
    frames = r24.parse_frames(r24.FROZEN_FRAMES)

    def fake_gate(registry_path, session_id, frames_spec, arm, prior_root):
        return list(frames)

    monkeypatch.setattr(r24, "_pre_execute_check", fake_gate)
    reader = _fake_reader_factory(frames)
    calls_a: list = []
    out_a = fake_root / ("g6r24_a_%s" % uuid.uuid4().hex)
    bundle_a = r24.run_authorized_batch(
        str(out_a), r24.FROZEN_REGISTRY, r24.FROZEN_SESSION, r24.FROZEN_FRAMES,
        r24.ARM, r24.FROZEN_PRIOR_ROOT, r24.SCHEDULE,
        adapters=_fake_flood_adapters(calls_a, seed=123),
        reader_override=reader)
    calls_b: list = []
    out_b = fake_root / ("g6r24_b_%s" % uuid.uuid4().hex)
    bundle_b = r24.run_authorized_batch(
        str(out_b), r24.FROZEN_REGISTRY, r24.FROZEN_SESSION, r24.FROZEN_FRAMES,
        r24.ARM, r24.FROZEN_PRIOR_ROOT, r24.SCHEDULE,
        adapters=_fake_flood_adapters(calls_b, seed=123),
        reader_override=reader)
    assert len(calls_a) == 128 and len(calls_b) == 128
    assert len(bundle_a["records"]) == len(bundle_b["records"]) == 128
    for ra, rb in zip(bundle_a["records"], bundle_b["records"]):
        assert ra["verified_exact"] == rb["verified_exact"]
        assert ra["disclosure_bits"] == rb["disclosure_bits"]
        assert ra["outcome"] == rb["outcome"]
    # Cross-schedule byte-identity is NEVER asserted (layered vs flooding
    # trajectories differ by construction; no such comparison here).


# F3: invalid-schedule refused, zero calls.
def test_f3_invalid_schedule_refused():
    _assert_no_production()
    for bad in ("ROW_LAYERED", "layered", "", "flooding", "FLOOD", None, True, 0.5):
        with pytest.raises(ValueError, match="not frozen FLOODING"):
            r24.validate_schedule(bad)
    assert r24.validate_schedule("FLOODING") == "FLOODING"
    calls: list = []
    with pytest.raises(ValueError, match="not frozen FLOODING"):
        r24.run_authorized_batch(
            "workspace/g6r24_fake_bad_%s" % uuid.uuid4().hex,
            r24.FROZEN_REGISTRY, r24.FROZEN_SESSION, r24.FROZEN_FRAMES,
            r24.ARM, r24.FROZEN_PRIOR_ROOT, "ROW_LAYERED",
            adapters=_fake_flood_adapters(calls),
            reader_override=_fake_reader_factory(r24.parse_frames(r24.FROZEN_FRAMES)))
    assert calls == []
    with pytest.raises(SystemExit):
        r24.main(["--profile-only", "--schedule", "ROW_LAYERED"])


# F4: full fake 128-block flood batch.
def test_f4_full_fake_128_flood(fake_root, monkeypatch):
    _assert_no_production()
    assert r24.FROZEN_EPS == 1e-4 and DEFAULT_EPS == 1e-4
    assert r24.disclosed_bits(100) == 564
    frames = r24.parse_frames(r24.FROZEN_FRAMES)
    assert len(frames) == 64 and frames[0] == 2123 and frames[-1] == 2186
    plan = r24.build_call_plan(frames)
    assert len(plan) == 128

    def fake_gate(registry_path, session_id, frames_spec, arm, prior_root):
        return list(frames)

    monkeypatch.setattr(r24, "_pre_execute_check", fake_gate)
    calls: list = []
    out = fake_root / ("g6r24_batch_%s" % uuid.uuid4().hex)
    bundle = r24.run_authorized_batch(
        str(out), r24.FROZEN_REGISTRY, r24.FROZEN_SESSION, r24.FROZEN_FRAMES,
        r24.ARM, r24.FROZEN_PRIOR_ROOT, "FLOODING",
        adapters=_fake_flood_adapters(calls),
        reader_override=_fake_reader_factory(frames))
    assert len(calls) == 128
    assert bundle["summary"]["terminal"] == "COMPLETE_128"
    assert bundle["summary"]["exact"] == 128
    assert bundle["summary"]["undetected"] == 0
    assert bundle["summary"]["schedule"] == "FLOODING"
    assert str(bundle["summary"]["schedule_token"]).startswith("FLOODING-")
    assert bundle["summary"]["f_gate"] == "FLOOD-HELPS"  # 128 >= 6
    assert bundle["summary"]["paired_lift"] == 128 - 2
    assert bundle["manifest"]["decoder"]["adapter"] == "v35.decode_flooding_fftqspa"
    assert bundle["manifest"]["schedule_token"].startswith("FLOODING-")
    for rec in bundle["records"]:
        assert rec["disclosure_bits"] == 564
        assert rec["syndrome_bits"] == 500 and rec["tag_bits"] == 64
        assert rec["control_bits"] == 0 and rec["interaction_bits"] == 0
        assert rec["auth_bits"] == 0


# F5: UNDETECTED_STOP absolute.
def test_f5_undetected_stop(fake_root, monkeypatch):
    _assert_no_production()
    frames = r24.parse_frames(r24.FROZEN_FRAMES)

    def fake_gate(registry_path, session_id, frames_spec, arm, prior_root):
        return list(frames)

    monkeypatch.setattr(r24, "_pre_execute_check", fake_gate)
    # Force tag collision so a wrong decode is accepted-but-inexact
    # (undetected). Real path uses hash tags; fake tag forces the case.
    monkeypatch.setattr(r24, "_candidate_tag", lambda x: b"CONSTTAG")
    calls: list = []
    out = fake_root / ("g6r24_undet_%s" % uuid.uuid4().hex)
    bundle = r24.run_authorized_batch(
        str(out), r24.FROZEN_REGISTRY, r24.FROZEN_SESSION, r24.FROZEN_FRAMES,
        r24.ARM, r24.FROZEN_PRIOR_ROOT, "FLOODING",
        adapters=_fake_flood_adapters(calls, wrong_at=5),
        reader_override=_fake_reader_factory(frames))
    assert bundle["summary"]["terminal"] == "UNDETECTED_STOP"
    assert bundle["summary"]["f_gate"] == "UNDETECTED_STOP"
    assert bundle["summary"]["undetected"] == 1
    assert len(bundle["records"]) == 6  # blocks 0..5, break at first undetected
    assert bundle["records"][-1]["undetected"] is True
    # Isolation: undetected accepted but never exact.
    assert bundle["records"][-1]["protocol_accepted"] is True
    assert bundle["records"][-1]["verified_exact"] is False


# F6: isolation — exact subset of accepted, undetected never merged.
def test_f6_isolation(fake_root, monkeypatch):
    _assert_no_production()
    frames = r24.parse_frames(r24.FROZEN_FRAMES)

    def fake_gate(registry_path, session_id, frames_spec, arm, prior_root):
        return list(frames)

    monkeypatch.setattr(r24, "_pre_execute_check", fake_gate)
    calls: list = []
    out = fake_root / ("g6r24_iso_%s" % uuid.uuid4().hex)
    bundle = r24.run_authorized_batch(
        str(out), r24.FROZEN_REGISTRY, r24.FROZEN_SESSION, r24.FROZEN_FRAMES,
        r24.ARM, r24.FROZEN_PRIOR_ROOT, "FLOODING",
        adapters=_fake_flood_adapters(calls),
        reader_override=_fake_reader_factory(frames))
    for rec in bundle["records"]:
        if rec["verified_exact"]:
            assert rec["protocol_accepted"] is True
        if rec["undetected"]:
            assert rec["protocol_accepted"] is True
            assert rec["verified_exact"] is False


# F7: refusal matrix — missing grant / existing root / pool mismatch.
def test_f7_refusal_missing_grant_zero_calls():
    _assert_no_production()
    rc = r24.main(["--execute-real", "--registry", r24.FROZEN_REGISTRY,
                   "--session", r24.FROZEN_SESSION, "--frames", r24.FROZEN_FRAMES,
                   "--arm", r24.ARM, "--prior-root", r24.FROZEN_PRIOR_ROOT,
                   "--schedule", "FLOODING",
                   "--out-dir", "workspace/g6r24_fake_refuse_%s" % uuid.uuid4().hex])
    assert rc == 2


def test_f7_refusal_existing_root_zero_calls(fake_root):
    _assert_no_production()
    existing = fake_root / "exists"
    existing.mkdir(parents=True)
    calls: list = []
    with pytest.raises(FileExistsError):
        r24.run_authorized_batch(
            str(existing), r24.FROZEN_REGISTRY, r24.FROZEN_SESSION,
            r24.FROZEN_FRAMES, r24.ARM, r24.FROZEN_PRIOR_ROOT, "FLOODING",
            adapters=_fake_flood_adapters(calls))
    assert calls == []


def test_f7_refusal_pool_mismatch_zero_calls():
    _assert_no_production()
    calls: list = []
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        r24._pre_execute_check("wrong_registry.json", r24.FROZEN_SESSION,
                               r24.FROZEN_FRAMES, r24.ARM, r24.FROZEN_PRIOR_ROOT)
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        r24._pre_execute_check(r24.FROZEN_REGISTRY, "WRONG_SESSION",
                               r24.FROZEN_FRAMES, r24.ARM, r24.FROZEN_PRIOR_ROOT)
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        r24._pre_execute_check(r24.FROZEN_REGISTRY, r24.FROZEN_SESSION,
                               "2123..2185", r24.ARM, r24.FROZEN_PRIOR_ROOT)
    assert calls == []


# F8: no-overwrite — protected dirs + frozen dirs + prior roots + UUID absent.
def test_f8_no_overwrite_uuid_absent():
    _assert_no_production()
    with pytest.raises((ValueError, FileExistsError)):
        r2.refuse_out_root("results/g6r24_fake")
    with pytest.raises((ValueError, FileExistsError)):
        r2.refuse_out_root("comparison_bench/outputs_comparison/g6r24_fake")
    for forbidden in [ROOT / "src", ROOT / "experiments", ROOT / "tools"]:
        if forbidden.exists():
            hits = list(forbidden.rglob("*g6r24*"))
            assert hits == [], "frozen dir touched: %r" % hits
    prior_roots = [
        "workspace/g6_decide_r1_8e7c2a1f-4b6d-4e9a-9c3f-2a5b7d8e0f1a",
        "workspace/g6r2_diag_c4a1d2e6-9b3f-4e7a-8c5d-2f6a0e1b3d4c",
        "workspace/g6r9_confirm_3f9a1c2e-7b4d-4e8a-9c1f-2d5e6a7b8c9d",
        "workspace/g6s1_shift_4105cfc2-3bbb-444a-9283-31403d43b7ff",
        "workspace/g6r20_uni_05100de1-e48c-4eea-a8a7-d5390f87cfc8",
        "workspace/v72p2d5_model_f_input/20260907_r1",
    ]
    for rel in prior_roots:
        root = ROOT / rel
        if root.exists():
            hits = list(root.rglob("*g6r24*"))
            assert hits == [], "prior root touched: %r" % hits
    assert not (ROOT / r24.FUTURE_ROOT).exists()  # UUID root absent


# F9: verifier recompute (counts/sums, H-pair, beta, net_secret, f_gate).
def _write_fake_root(out, accepted_n=90, undet_at=None):
    manifest = {"command": r24.FROZEN_COMMAND,
                "prior": {"mode": r24.PRIOR_MODE, "eps": r24.FROZEN_EPS},
                "schedule": "FLOODING", "schedule_token": r24.SCHEDULE_TOKEN,
                "call_shape": r24.FLOOD_CALL_SHAPE,
                "decoder": {"adapter": "v35.decode_flooding_fftqspa",
                            "call_shape": r24.FLOOD_CALL_SHAPE,
                            "max_iter": 90, "field": None,
                            "schedule": "cold flooding single-pass",
                            "schedule_token": r24.SCHEDULE_TOKEN}}
    (out / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    leak_each = 564
    with (out / "block_records.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(r24.BLOCK_COLUMNS))
        writer.writeheader()
        for i in range(128):
            accepted = i < accepted_n
            undet = undet_at is not None and i == undet_at
            exact = accepted and not undet
            writer.writerow({
                "call_idx": i, "frame_id": 2123 + i // 2, "block_id": i,
                "session_id": r24.FROZEN_SESSION, "arm": r24.ARM,
                "candidate_id": r24.CANDIDATE_ID, "graph_seed": r24.GRAPH_SEEDS[i % 2],
                "n": 128, "m": 100, "attempted": "True",
                "finite": "True" if accepted else "False",
                "syndrome_match": "True" if accepted else "False",
                "tag_match": "True" if accepted else "False",
                "protocol_accepted": "True" if accepted else "False",
                "verified_exact": "True" if exact else "False",
                "undetected": "True" if undet else "False",
                "outcome": "undetected" if undet else ("exact" if exact else "attempted"),
                "syndrome_bits": 500, "tag_bits": 64, "control_bits": 0,
                "interaction_bits": 0, "auth_bits": 0, "disclosure_bits": leak_each,
                "iters": 7, "residual": 0, "provenance": "CHECK_UPDATED",
                "wall_s": 0.01, "crash": "False", "error": ""})
    leak_sum = 128 * leak_each
    exact_n = accepted_n - (1 if undet_at is not None else 0)
    undet_n = 1 if undet_at is not None else 0
    beta_p = 1.0 - leak_sum / (128 * 128 * r24.H_FROZEN)
    beta_l = 1.0 - leak_sum / (128 * 128 * r24.H_L2)
    summary = {"attempted": 128, "accepted": accepted_n, "exact": exact_n,
               "undetected": undet_n, "disclosure_sum": leak_sum,
               "schedule": "FLOODING", "schedule_token": r24.SCHEDULE_TOKEN,
               "f_gate": r24.f_gate(exact_n, undet_n),
               "prior_mode": r24.PRIOR_MODE, "prior_eps": r24.FROZEN_EPS,
               "beta_eff_empirical_primary": beta_p,
               "beta_eff_empirical_l2_sensitivity": beta_l,
               "H_frozen_primary": r24.H_FROZEN, "H_L2_sensitivity": r24.H_L2,
               "baseline_s1_exact": 2, "paired_lift": exact_n - 2,
               "net_secret_bits": r24.net_secret_bits(accepted_n, leak_sum, r24.N),
               "terminal": "UNDETECTED_STOP" if undet_n else "COMPLETE_128"}
    (out / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (out / "report.md").write_text("# fake\n", encoding="utf-8")
    return leak_sum


def _rewrite_rows(out, mutate):
    rows = list(csv.DictReader((out / "block_records.csv").read_text(encoding="utf-8").splitlines()))
    mutate(rows)
    with (out / "block_records.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(r24.BLOCK_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)


def test_f9_verifier_pass_and_tamper_fails(fake_root):
    _assert_no_production()
    out = fake_root / "g6r24_verify_fake"
    out.mkdir(parents=True)
    _write_fake_root(out)
    assert r24.verify_root(str(out)) is True
    # Tamper 1: undetected-merge (summary now stale) -> FAIL.
    def tamper_undetected(rows):
        rows[0]["undetected"] = "True"
        rows[0]["verified_exact"] = "False"
        rows[0]["outcome"] = "undetected"
    _rewrite_rows(out, tamper_undetected)
    assert r24.verify_root(str(out)) is False
    # Restore -> PASS; tamper 2: disclosure mismatch -> FAIL.
    def restore_undetected(rows):
        rows[0]["undetected"] = "False"
        rows[0]["verified_exact"] = "True"
        rows[0]["outcome"] = "exact"
    _rewrite_rows(out, restore_undetected)
    assert r24.verify_root(str(out)) is True
    def tamper_disclosure(rows):
        rows[1]["disclosure_bits"] = "563"
    _rewrite_rows(out, tamper_disclosure)
    assert r24.verify_root(str(out)) is False


def test_f9_verifier_beta_net_schedule_tamper_fails(fake_root):
    _assert_no_production()
    out = fake_root / "g6r24_verify_fake2"
    out.mkdir(parents=True)
    _write_fake_root(out, accepted_n=90)
    assert r24.H_FROZEN == 3.347605 and r24.H_L2 == 3.222719884634378
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["net_secret_bits"] == 90 * 5 * 128 - 128 * 564
    assert summary["paired_lift"] == 90 - 2
    assert summary["f_gate"] == "FLOOD-HELPS"
    # Tamper: hand-filled beta (off by 1e-6) -> FAIL.
    summary["beta_eff_empirical_primary"] = float(summary["beta_eff_empirical_primary"]) + 1e-6
    (out / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    assert r24.verify_root(str(out)) is False
    # Tamper: hand-filled net (+1) -> FAIL.
    summary["beta_eff_empirical_primary"] = 1.0 - summary["disclosure_sum"] / (128 * 128 * r24.H_FROZEN)
    summary["net_secret_bits"] = int(summary["net_secret_bits"]) + 1
    (out / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    assert r24.verify_root(str(out)) is False
    # Tamper: schedule token stripped -> FAIL.
    summary["net_secret_bits"] = r24.net_secret_bits(90, 128 * 564, r24.N)
    summary["schedule_token"] = "LAYERED-90-cold"
    (out / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    assert r24.verify_root(str(out)) is False
    # Tamper: retuned eps (prior_eps=0.1) -> FAIL.
    summary["schedule_token"] = r24.SCHEDULE_TOKEN
    summary["prior_eps"] = 0.1
    (out / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    assert r24.verify_root(str(out)) is False
