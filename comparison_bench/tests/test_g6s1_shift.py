"""S1 SHIFT m100 delta tests — FAKE fixtures only (never real pool).

S1 readiness: zero real-payload decoder calls; no UUID root; temp fake
roots. Covers: T1 shift-build column sums/determinism/eps-sensitivity/
zero-column/all-zero; T2 shift path disclosure/plan/prior-shape; T3 full
fake 128-block shift batch; T4 refusal matrix; T5 no-overwrite incl ALL
prior UUID roots; T6 verifier recompute + isolation/net_secret/eps tamper
FAILs.
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
RUNNER_PATH = ROOT / "scripts" / "g6s1_shift.py"


def _load_runner():
    spec = importlib.util.spec_from_file_location("g6s1_shift_test", str(RUNNER_PATH))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["g6s1_shift_test"] = mod
    spec.loader.exec_module(mod)
    return mod


s1 = _load_runner()
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
    path = ROOT / "workspace" / ("g6s1_fake_%s" % uuid.uuid4().hex)
    assert not path.exists()
    assert "4105cfc2" not in str(path)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _fake_graph(seed):
    H = np.zeros((s1.M, s1.N), dtype=np.uint8)
    for v in range(s1.N):
        H[v % s1.M, v] = 1
    return {"arm": s1.ARM, "width": s1.N, "graph_seed": int(seed),
            "n": s1.N, "m": s1.M, "E": int(np.count_nonzero(H)),
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


# T1: shift build — column sums, determinism, eps sensitivity, fallbacks.
def test_t1_shift_build_columns_determinism_eps():
    _assert_no_production()
    assert s1.FROZEN_EPS == 1e-4 and DEFAULT_EPS == 1e-4
    assert "shift" in s1.PRIOR_MODE and "1e-04" in s1.PRIOR_MODE
    rng = np.random.default_rng(20260919)
    counts = rng.integers(0, 5, size=(32, 40)).astype(float)
    for eps in (1e-5, 1e-4, 1e-3, 1e-2, 0.1):
        p = build_shift_prior_concentration(counts, eps)
        assert p.shape == (32, 40)
        assert np.all(np.isfinite(p))
        assert np.abs(p.sum(axis=0) - 1.0).max() <= 1e-12
    a = build_shift_prior_concentration(counts, 1e-4)
    b = build_shift_prior_concentration(counts, 1e-4)
    assert np.array_equal(a, b)  # determinism
    c = build_shift_prior_concentration(counts, 0.1)
    assert not np.array_equal(a, c)  # eps sensitivity
    assert np.abs(c.sum(axis=0) - 1.0).max() <= 1e-12


def test_t1_shift_build_zero_column_and_all_zero():
    _assert_no_production()
    rng = np.random.default_rng(7)
    counts = rng.integers(0, 5, size=(16, 6)).astype(float)
    counts[:, 3] = 0.0  # zero Bob column falls back, stays stochastic
    p = build_shift_prior_concentration(counts, 1e-4)
    assert np.all(np.isfinite(p))
    assert np.abs(p.sum(axis=0) - 1.0).max() <= 1e-12
    with pytest.raises(ValueError, match="all zero"):
        build_shift_prior_concentration(np.zeros((8, 8)), 1e-4)
    with pytest.raises(ValueError, match="eps"):
        build_shift_prior_concentration(np.ones((4, 4)), -1.0)


# T2: shift path — m100-564 disclosure, 128 plan, shift prior shape/rows.
def test_t2_shift_path_disclosure_plan_prior_shape():
    _assert_no_production()
    assert s1.M == 100
    assert s1.disclosed_bits(100) == 564
    assert s1.disclosed_bits(s1.M) == 564
    frames = s1.parse_frames(s1.FROZEN_FRAMES)
    assert len(frames) == 64 and frames[0] == 2123 and frames[-1] == 2186
    plan = s1.build_call_plan(frames)
    assert len(plan) == 128
    for p in plan:
        assert p["disclosed_bits"] == 564
        assert p["graph_seed"] == s1.GRAPH_SEEDS[p["block_id"] % 2]
    rng = np.random.default_rng(11)
    fake_counts = rng.integers(0, 5, size=(1024, 1024)).astype(float) + 1.0
    p_f = build_shift_prior_concentration(fake_counts, s1.FROZEN_EPS)
    bob = np.full(128, 7, dtype=np.int64)
    prior = s1.marginal_l2_prior(p_f, bob)
    assert prior.shape == (128, 32)
    assert np.all(np.isfinite(prior))
    assert np.abs(prior.sum(axis=1) - 1.0).max() <= 1e-12
    # H-pair reported only (same constants as R9, never gated here).
    assert s1.H_FROZEN == 3.347605 and s1.H_L2 == 3.222719884634378


# T-admission: same R9 pair 4720/4721 via accepted builder; disjointness.
def test_t_admission_same_r9_pair():
    _assert_no_production()
    assert s1.GRAPH_SEEDS == (2026094720, 2026094721)
    assert s1.DOMAIN_NAMESPACE == "g6r9-domain"
    assert s1.COEFF_NAMESPACE_TMPL.startswith("g6r9:coeff:")
    graphs = [s1.build_graph(seed) for seed in s1.GRAPH_SEEDS]
    assert sum(1 for g in graphs if g["admitted"]) == 2
    for g in graphs:
        assert g["status"] == "ok" and g["E"] == 349
        assert g["n"] == 128 and g["m"] == 100
    with pytest.raises(ValueError, match="outside"):
        s1.build_graph(2026094601)


def _fake_reader_factory(frames):
    """Fake pool reader: all-zero truth symbols (fake payload, never real)."""

    def fake_reader(path, columns=None, filters=None):
        # pandas-style filters: [("frame_id", "in", [ids])]
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


def _fake_adapters(decode_calls):
    rng = np.random.default_rng(99)
    fake_counts = rng.integers(0, 5, size=(1024, 1024)).astype(float) + 1.0
    fake_pf = build_shift_prior_concentration(fake_counts, s1.FROZEN_EPS)

    def fake_decode(H, priors, syn, **kw):
        decode_calls.append(1)
        assert kw.get("max_iter") == 90 and kw.get("damping_alpha") == 1.0
        assert kw.get("warm_beliefs") is None  # cold single-pass
        assert priors.shape == (128, 32)
        assert np.abs(priors.sum(axis=1) - 1.0).max() <= 1e-12
        return _FakeResult(np.zeros(128, dtype=np.int64))

    def fake_syndrome(H, x):
        return np.zeros(H.shape[0], dtype=np.uint8)

    def fake_prior(root):
        return np.asarray(fake_pf)

    def fake_build(seed):
        assert int(seed) in s1.GRAPH_SEEDS
        return _fake_graph(int(seed))

    return {"decode_fn": fake_decode, "syndrome_fn": fake_syndrome,
            "load_prior_fn": fake_prior, "build_fn": fake_build}


# T3: full fake 128-block shift path (fake prior table, fake pool).
def test_t3_shift_path_fake_batch(fake_root, monkeypatch):
    _assert_no_production()
    frames = s1.parse_frames(s1.FROZEN_FRAMES)

    def fake_gate(registry_path, session_id, frames_spec, arm, prior_root):
        assert str(registry_path) == s1.FROZEN_REGISTRY
        assert str(session_id) == s1.FROZEN_SESSION
        assert str(frames_spec) == s1.FROZEN_FRAMES
        assert str(arm) == s1.ARM
        assert str(prior_root) == s1.FROZEN_PRIOR_ROOT
        return list(frames)

    monkeypatch.setattr(s1, "_pre_execute_check", fake_gate)
    reader = _fake_reader_factory(frames)
    decode_calls: list = []
    out = fake_root / ("g6s1_batch_%s" % uuid.uuid4().hex)
    bundle = s1.run_authorized_batch(
        str(out), s1.FROZEN_REGISTRY, s1.FROZEN_SESSION, s1.FROZEN_FRAMES,
        s1.ARM, s1.FROZEN_PRIOR_ROOT,
        adapters=_fake_adapters(decode_calls),
        reader_override=reader)
    assert len(decode_calls) == 128
    assert len(bundle["records"]) == 128
    assert bundle["summary"]["prior_mode"] == s1.PRIOR_MODE
    assert bundle["summary"]["prior_eps"] == s1.FROZEN_EPS
    assert bundle["summary"]["terminal"] == "COMPLETE_128"
    assert bundle["summary"]["exact"] == 128
    assert bundle["summary"]["undetected"] == 0
    for r in bundle["records"]:
        assert r["verified_exact"] is True
        assert r["disclosure_bits"] == 564
        assert r["graph_seed"] == s1.GRAPH_SEEDS[r["block_id"] % 2]
    assert bundle["manifest"]["prior"]["mode"] == s1.PRIOR_MODE
    assert bundle["manifest"]["prior"]["eps"] == s1.FROZEN_EPS


# T4: refusal matrix — missing grant / existing root / pool mismatch.
def test_t4_refusal_missing_grant_zero_calls():
    _assert_no_production()
    rc = s1.main(["--execute-real", "--registry", s1.FROZEN_REGISTRY,
                  "--session", s1.FROZEN_SESSION, "--frames", s1.FROZEN_FRAMES,
                  "--arm", s1.ARM, "--prior-root", s1.FROZEN_PRIOR_ROOT,
                  "--out-dir", "workspace/g6s1_fake_refuse_%s" % uuid.uuid4().hex])
    assert rc == 2


def test_t4_refusal_existing_root_zero_calls(fake_root):
    _assert_no_production()
    existing = fake_root / "exists"
    existing.mkdir(parents=True)
    decode_calls: list = []
    # refuse_out_root runs BEFORE gate/pool/adapters: no real I/O needed.
    with pytest.raises(FileExistsError):
        s1.run_authorized_batch(
            str(existing), s1.FROZEN_REGISTRY, s1.FROZEN_SESSION,
            s1.FROZEN_FRAMES, s1.ARM, s1.FROZEN_PRIOR_ROOT,
            adapters=_fake_adapters(decode_calls))
    assert decode_calls == []


def test_t4_refusal_pool_mismatch_zero_calls():
    _assert_no_production()
    decode_calls: list = []
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        s1._pre_execute_check("wrong_registry.json", s1.FROZEN_SESSION,
                              s1.FROZEN_FRAMES, s1.ARM, s1.FROZEN_PRIOR_ROOT)
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        s1._pre_execute_check(s1.FROZEN_REGISTRY, "WRONG_SESSION",
                              s1.FROZEN_FRAMES, s1.ARM, s1.FROZEN_PRIOR_ROOT)
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        s1._pre_execute_check(s1.FROZEN_REGISTRY, s1.FROZEN_SESSION,
                              "2123..2185", s1.ARM, s1.FROZEN_PRIOR_ROOT)
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        s1._pre_execute_check(s1.FROZEN_REGISTRY, s1.FROZEN_SESSION,
                              s1.FROZEN_FRAMES, "WRONG_ARM", s1.FROZEN_PRIOR_ROOT)
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        s1._pre_execute_check(s1.FROZEN_REGISTRY, s1.FROZEN_SESSION,
                              s1.FROZEN_FRAMES, s1.ARM, "workspace/wrong_prior")
    assert decode_calls == []


# T5: no-overwrite — protected dirs + frozen dirs + ALL prior UUID roots.
def test_t5_no_overwrite_all_prior_roots():
    _assert_no_production()
    with pytest.raises((ValueError, FileExistsError)):
        r2.refuse_out_root("results/g6s1_fake")
    with pytest.raises((ValueError, FileExistsError)):
        r2.refuse_out_root("comparison_bench/outputs_comparison/g6s1_fake")
    for forbidden in [ROOT / "src", ROOT / "experiments", ROOT / "tools"]:
        if forbidden.exists():
            hits = list(forbidden.rglob("*g6s1*"))
            assert hits == [], "frozen dir touched: %r" % hits
    prior_roots = [
        "workspace/g6_decide_r1_8e7c2a1f-4b6d-4e9a-9c3f-2a5b7d8e0f1a",
        "workspace/g6r2_diag_c4a1d2e6-9b3f-4e7a-8c5d-2f6a0e1b3d4c",
        "workspace/g6r9_confirm_3f9a1c2e-7b4d-4e8a-9c1f-2d5e6a7b8c9d",
        "workspace/g6r20_uni_05100de1-e48c-4eea-a8a7-d5390f87cfc8",
        "workspace/v72p2d5_model_f_input/20260907_r1",
    ]
    for rel in prior_roots:
        root = ROOT / rel
        if root.exists():
            hits = list(root.rglob("*g6s1*"))
            assert hits == [], "prior root touched: %r" % hits
    assert not (ROOT / s1.FUTURE_ROOT).exists()  # UUID root absent


# T6: verifier recompute (counts/sums, H-pair, beta, net_secret, eps).
def _write_fake_root(out, accepted_n=90):
    manifest = {"command": s1.FROZEN_COMMAND,
                "prior": {"mode": s1.PRIOR_MODE, "eps": s1.FROZEN_EPS}}
    (out / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    leak_each = 564
    with (out / "block_records.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(s1.BLOCK_COLUMNS))
        writer.writeheader()
        for i in range(128):
            accepted = i < accepted_n
            writer.writerow({
                "call_idx": i, "frame_id": 2123 + i // 2, "block_id": i,
                "session_id": s1.FROZEN_SESSION, "arm": s1.ARM,
                "candidate_id": s1.CANDIDATE_ID, "graph_seed": s1.GRAPH_SEEDS[i % 2],
                "n": 128, "m": 100, "attempted": "True",
                "finite": "True" if accepted else "False",
                "syndrome_match": "True" if accepted else "False",
                "tag_match": "True" if accepted else "False",
                "protocol_accepted": "True" if accepted else "False",
                "verified_exact": "True" if accepted else "False",
                "undetected": "False", "outcome": "exact" if accepted else "attempted",
                "syndrome_bits": 500, "tag_bits": 64, "control_bits": 0,
                "interaction_bits": 0, "auth_bits": 0, "disclosure_bits": leak_each,
                "iters": 7, "residual": 0, "provenance": "CHECK_UPDATED",
                "wall_s": 0.01, "crash": "False", "error": ""})
    leak_sum = 128 * leak_each
    beta_p = 1.0 - leak_sum / (128 * 128 * s1.H_FROZEN)
    beta_l = 1.0 - leak_sum / (128 * 128 * s1.H_L2)
    summary = {"attempted": 128, "accepted": accepted_n, "exact": accepted_n,
               "undetected": 0, "disclosure_sum": leak_sum,
               "prior_mode": s1.PRIOR_MODE, "prior_eps": s1.FROZEN_EPS,
               "beta_eff_empirical_primary": beta_p,
               "beta_eff_empirical_l2_sensitivity": beta_l,
               "H_frozen_primary": s1.H_FROZEN, "H_L2_sensitivity": s1.H_L2,
               "net_secret_bits": s1.net_secret_bits(accepted_n, leak_sum, s1.N),
               "terminal": "COMPLETE_128"}
    (out / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (out / "report.md").write_text("# fake\n", encoding="utf-8")
    return leak_sum


def _rewrite_rows(out, mutate):
    rows = list(csv.DictReader((out / "block_records.csv").read_text(encoding="utf-8").splitlines()))
    mutate(rows)
    with (out / "block_records.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(s1.BLOCK_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)


def test_t6_verifier_pass_and_isolation_tamper_fails(fake_root):
    _assert_no_production()
    out = fake_root / "g6s1_verify_fake"
    out.mkdir(parents=True)
    _write_fake_root(out)
    assert s1.verify_root(str(out)) is True
    # Tamper 1: undetected-merge (summary now stale) -> FAIL.
    def tamper_undetected(rows):
        rows[0]["undetected"] = "True"
        rows[0]["verified_exact"] = "False"
        rows[0]["outcome"] = "undetected"
    _rewrite_rows(out, tamper_undetected)
    assert s1.verify_root(str(out)) is False
    # Restore -> PASS; tamper 2: disclosure mismatch -> FAIL.
    def restore_undetected(rows):
        rows[0]["undetected"] = "False"
        rows[0]["verified_exact"] = "True"
        rows[0]["outcome"] = "exact"
    _rewrite_rows(out, restore_undetected)
    assert s1.verify_root(str(out)) is True
    def tamper_disclosure(rows):
        rows[1]["disclosure_bits"] = "563"
    _rewrite_rows(out, tamper_disclosure)
    assert s1.verify_root(str(out)) is False


def test_t6_verifier_beta_net_eps_tamper_fails(fake_root):
    _assert_no_production()
    out = fake_root / "g6s1_verify_fake2"
    out.mkdir(parents=True)
    _write_fake_root(out, accepted_n=90)
    assert s1.H_FROZEN == 3.347605 and s1.H_L2 == 3.222719884634378
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["net_secret_bits"] == 90 * 5 * 128 - 128 * 564
    assert summary["prior_eps"] == s1.FROZEN_EPS
    # Tamper: hand-filled beta (off by 1e-6) -> FAIL.
    summary["beta_eff_empirical_primary"] = float(summary["beta_eff_empirical_primary"]) + 1e-6
    (out / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    assert s1.verify_root(str(out)) is False
    # Tamper: hand-filled net (+1) -> FAIL.
    summary["beta_eff_empirical_primary"] = 1.0 - summary["disclosure_sum"] / (128 * 128 * s1.H_FROZEN)
    summary["net_secret_bits"] = int(summary["net_secret_bits"]) + 1
    (out / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    assert s1.verify_root(str(out)) is False
    # Tamper: retuned eps (prior_eps=0.1) -> FAIL.
    summary["net_secret_bits"] = s1.net_secret_bits(90, 128 * 564, s1.N)
    summary["prior_eps"] = 0.1
    (out / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    assert s1.verify_root(str(out)) is False
