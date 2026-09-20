"""R20 UNIFORM m100 delta tests — FAKE fixtures only (never real pool).

R20 readiness: zero real-payload decoder calls; no UUID root; temp fake
roots. Covers: U1 uniform-1/32 prior + m100-564-disclosure; U2 full fake
128-block uniform path with loader-untouched assert; U3 refusal matrix;
U4 no-overwrite incl ALL prior UUID roots; U5 verifier recompute +
isolation/net_secret/loader tamper FAILs.
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
RUNNER_PATH = ROOT / "scripts" / "g6r20_uniform.py"


def _load_runner():
    spec = importlib.util.spec_from_file_location("g6r20_uniform_test", str(RUNNER_PATH))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["g6r20_uniform_test"] = mod
    spec.loader.exec_module(mod)
    return mod


g20 = _load_runner()
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
    path = ROOT / "workspace" / ("g6r20_fake_%s" % uuid.uuid4().hex)
    assert not path.exists()
    assert "05100de1" not in str(path)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _fake_graph(seed):
    H = np.zeros((g20.M, g20.N), dtype=np.uint8)
    for v in range(g20.N):
        H[v % g20.M, v] = 1
    return {"arm": g20.ARM, "width": g20.N, "graph_seed": int(seed),
            "n": g20.N, "m": g20.M, "E": int(np.count_nonzero(H)),
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


# U1: uniform prior exactly 1/32; m100 disclosure 564; split 500/64; C/I/A 0.
def test_u1_uniform_prior_1_32_and_disclosure_564():
    _assert_no_production()
    assert g20.PRIOR_MODE == "uniform-1/32"
    assert "load_prior" not in g20.PRIOR_MODE
    prior = g20.uniform_l2_prior()
    assert prior.shape == (128, 32)
    assert np.all(prior == 1.0 / 32.0)
    assert np.allclose(prior.sum(axis=1), 1.0)
    assert np.all(np.isfinite(prior))
    # No prior-mode flag exists to misuse (uniform-only single mode).
    assert g20.M == 100
    assert g20.disclosed_bits(100) == 564
    assert g20.disclosed_bits(g20.M) == 564
    frames = g20.parse_frames(g20.FROZEN_FRAMES)
    assert len(frames) == 64 and frames[0] == 2123 and frames[-1] == 2186
    plan = g20.build_call_plan(frames)
    assert len(plan) == 128
    for p in plan:
        assert p["disclosed_bits"] == 564
        assert p["graph_seed"] == g20.GRAPH_SEEDS[p["block_id"] % 2]
    # run_one_block record carries the frozen split with uniform prior.
    graph = _fake_graph(g20.GRAPH_SEEDS[0])
    truth = np.zeros(g20.N, dtype=np.int64)
    rec = g20.run_one_block(
        graph, g20.uniform_l2_prior(), np.zeros(g20.M, dtype=np.uint8),
        g20._candidate_tag(truth), truth,
        {"frame_id": 2123, "block_id": 0, "graph_seed": g20.GRAPH_SEEDS[0],
         "session_id": g20.FROZEN_SESSION},
        lambda H, pr, s, **kw: _FakeResult(truth),
        lambda H, x: np.zeros(g20.M, dtype=np.uint8), 0)
    assert rec["disclosure_bits"] == 564
    assert rec["syndrome_bits"] == 500 and rec["tag_bits"] == 64
    assert rec["control_bits"] == 0 and rec["interaction_bits"] == 0
    assert rec["auth_bits"] == 0
    assert rec["verified_exact"] is True
    # H-pair reported only (same constants as R9, never gated here).
    assert g20.H_FROZEN == 3.347605 and g20.H_L2 == 3.222719884634378


# U-admission: same R9 pair 4720/4721 via accepted builder; disjointness.
def test_u_admission_same_r9_pair():
    _assert_no_production()
    assert g20.GRAPH_SEEDS == (2026094720, 2026094721)
    assert g20.DOMAIN_NAMESPACE == "g6r9-domain"
    assert g20.COEFF_NAMESPACE_TMPL.startswith("g6r9:coeff:")
    graphs = [g20.build_graph(seed) for seed in g20.GRAPH_SEEDS]
    assert sum(1 for g in graphs if g["admitted"]) == 2
    for g in graphs:
        assert g["status"] == "ok" and g["E"] == 349
        assert g["n"] == 128 and g["m"] == 100
    with pytest.raises(ValueError, match="outside"):
        g20.build_graph(2026094601)


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


def _fake_adapters(decode_calls, loader_calls):
    def fake_decode(H, priors, syn, **kw):
        decode_calls.append(1)
        assert kw.get("max_iter") == 90 and kw.get("damping_alpha") == 1.0
        assert kw.get("warm_beliefs") is None  # cold single-pass
        assert priors.shape == (128, 32) and np.all(priors == 1.0 / 32.0)
        return _FakeResult(np.zeros(128, dtype=np.int64))

    def fake_syndrome(H, x):
        return np.zeros(H.shape[0], dtype=np.uint8)

    def fake_prior(root):
        loader_calls.append(1)
        return None

    def fake_build(seed):
        assert int(seed) in g20.GRAPH_SEEDS
        return _fake_graph(int(seed))

    return {"decode_fn": fake_decode, "syndrome_fn": fake_syndrome,
            "load_prior_fn": fake_prior, "build_fn": fake_build}


# U2: full fake 128-block uniform path; loader untouched (0 calls).
# The deep key-gate is R9-frozen (covered by U3 + the real Pre-EXECUTE); here
# a no-I/O gate stub asserts frozen identities so the test stays 100% fake.
def test_u2_uniform_path_loader_untouched_fake_batch(fake_root, monkeypatch):
    _assert_no_production()
    frames = g20.parse_frames(g20.FROZEN_FRAMES)

    def fake_gate(registry_path, session_id, frames_spec, arm, prior_root):
        assert str(registry_path) == g20.FROZEN_REGISTRY
        assert str(session_id) == g20.FROZEN_SESSION
        assert str(frames_spec) == g20.FROZEN_FRAMES
        assert str(arm) == g20.ARM
        assert str(prior_root) == g20.FROZEN_PRIOR_ROOT
        return list(frames)

    monkeypatch.setattr(g20, "_pre_execute_check", fake_gate)
    reader = _fake_reader_factory(frames)
    decode_calls: list = []
    loader_calls: list = []
    out = fake_root / ("g6r20_batch_%s" % uuid.uuid4().hex)
    bundle = g20.run_authorized_batch(
        str(out), g20.FROZEN_REGISTRY, g20.FROZEN_SESSION, g20.FROZEN_FRAMES,
        g20.ARM, g20.FROZEN_PRIOR_ROOT,
        adapters=_fake_adapters(decode_calls, loader_calls),
        reader_override=reader)
    assert loader_calls == []  # Model-F loader never invoked
    assert len(decode_calls) == 128
    assert len(bundle["records"]) == 128
    assert bundle["summary"]["loader_calls"] == 0
    assert bundle["summary"]["prior_mode"] == "uniform-1/32"
    assert bundle["summary"]["terminal"] == "COMPLETE_128"
    assert bundle["summary"]["exact"] == 128
    assert bundle["summary"]["undetected"] == 0
    for r in bundle["records"]:
        assert r["verified_exact"] is True
        assert r["disclosure_bits"] == 564
        assert r["graph_seed"] == g20.GRAPH_SEEDS[r["block_id"] % 2]
    assert bundle["manifest"]["prior"]["mode"] == "uniform-1/32"


# U3: refusal matrix — missing grant / existing root / pool mismatch.
def test_u3_refusal_missing_grant_zero_calls():
    _assert_no_production()
    rc = g20.main(["--execute-real", "--registry", g20.FROZEN_REGISTRY,
                   "--session", g20.FROZEN_SESSION, "--frames", g20.FROZEN_FRAMES,
                   "--arm", g20.ARM, "--prior-root", g20.FROZEN_PRIOR_ROOT,
                   "--out-dir", "workspace/g6r20_fake_refuse_%s" % uuid.uuid4().hex])
    assert rc == 2


def test_u3_refusal_existing_root_zero_calls(fake_root):
    _assert_no_production()
    existing = fake_root / "exists"
    existing.mkdir(parents=True)
    decode_calls: list = []
    loader_calls: list = []
    # refuse_out_root runs BEFORE gate/pool/adapters: no real I/O needed.
    with pytest.raises(FileExistsError):
        g20.run_authorized_batch(
            str(existing), g20.FROZEN_REGISTRY, g20.FROZEN_SESSION,
            g20.FROZEN_FRAMES, g20.ARM, g20.FROZEN_PRIOR_ROOT,
            adapters=_fake_adapters(decode_calls, loader_calls))
    assert decode_calls == [] and loader_calls == []


def test_u3_refusal_pool_mismatch_zero_calls():
    _assert_no_production()
    decode_calls: list = []
    loader_calls: list = []
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        g20._pre_execute_check("wrong_registry.json", g20.FROZEN_SESSION,
                               g20.FROZEN_FRAMES, g20.ARM, g20.FROZEN_PRIOR_ROOT)
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        g20._pre_execute_check(g20.FROZEN_REGISTRY, "WRONG_SESSION",
                               g20.FROZEN_FRAMES, g20.ARM, g20.FROZEN_PRIOR_ROOT)
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        g20._pre_execute_check(g20.FROZEN_REGISTRY, g20.FROZEN_SESSION,
                               "2123..2185", g20.ARM, g20.FROZEN_PRIOR_ROOT)
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        g20._pre_execute_check(g20.FROZEN_REGISTRY, g20.FROZEN_SESSION,
                               g20.FROZEN_FRAMES, "WRONG_ARM", g20.FROZEN_PRIOR_ROOT)
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        g20._pre_execute_check(g20.FROZEN_REGISTRY, g20.FROZEN_SESSION,
                               g20.FROZEN_FRAMES, g20.ARM, "workspace/wrong_prior")
    assert decode_calls == [] and loader_calls == []


# U4: no-overwrite — protected dirs + frozen dirs + ALL prior UUID roots.
def test_u4_no_overwrite_all_prior_roots():
    _assert_no_production()
    with pytest.raises((ValueError, FileExistsError)):
        r2.refuse_out_root("results/g6r20_fake")
    with pytest.raises((ValueError, FileExistsError)):
        r2.refuse_out_root("comparison_bench/outputs_comparison/g6r20_fake")
    for forbidden in [ROOT / "src", ROOT / "experiments", ROOT / "tools"]:
        if forbidden.exists():
            hits = list(forbidden.rglob("*g6r20*"))
            assert hits == [], "frozen dir touched: %r" % hits
    prior_roots = [
        "workspace/g6_decide_r1_8e7c2a1f-4b6d-4e9a-9c3f-2a5b7d8e0f1a",
        "workspace/g6r2_diag_c4a1d2e6-9b3f-4e7a-8c5d-2f6a0e1b3d4c",
        "workspace/g6r9_confirm_3f9a1c2e-7b4d-4e8a-9c1f-2d5e6a7b8c9d",
        "workspace/g6r10_ctrl_6f2b8c1d-4a3e-4f9a-b7c2-d5e6f8a9b0c1",
        "workspace/g6r11_adaptive_3c2b5b2e-897b-467e-a3e6-0cba005914ae",
        "workspace/g6r12_fresh_c97777aa-620d-448f-8a6c-8abda5fb3b48",
        "workspace/v72p2d5_model_f_input/20260907_r1",
    ]
    for rel in prior_roots:
        root = ROOT / rel
        if root.exists():
            hits = list(root.rglob("*g6r20*"))
            assert hits == [], "prior root touched: %r" % hits
    assert not (ROOT / g20.FUTURE_ROOT).exists()  # UUID root absent


# U5: verifier recompute (counts/sums, H-pair, beta, net_secret, loader).
def _write_fake_root(out, accepted_n=90, loader_calls=0):
    manifest = {"command": g20.FROZEN_COMMAND,
                "prior": {"mode": g20.PRIOR_MODE}}
    (out / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    leak_each = 564
    with (out / "block_records.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(g20.BLOCK_COLUMNS))
        writer.writeheader()
        for i in range(128):
            accepted = i < accepted_n
            writer.writerow({
                "call_idx": i, "frame_id": 2123 + i // 2, "block_id": i,
                "session_id": g20.FROZEN_SESSION, "arm": g20.ARM,
                "candidate_id": g20.CANDIDATE_ID, "graph_seed": g20.GRAPH_SEEDS[i % 2],
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
    beta_p = 1.0 - leak_sum / (128 * 128 * g20.H_FROZEN)
    beta_l = 1.0 - leak_sum / (128 * 128 * g20.H_L2)
    summary = {"attempted": 128, "accepted": accepted_n, "exact": accepted_n,
               "undetected": 0, "disclosure_sum": leak_sum,
               "prior_mode": g20.PRIOR_MODE, "loader_calls": loader_calls,
               "beta_eff_empirical_primary": beta_p,
               "beta_eff_empirical_l2_sensitivity": beta_l,
               "H_frozen_primary": g20.H_FROZEN, "H_L2_sensitivity": g20.H_L2,
               "net_secret_bits": g20.net_secret_bits(accepted_n, leak_sum, g20.N),
               "terminal": "COMPLETE_128"}
    (out / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (out / "report.md").write_text("# fake\n", encoding="utf-8")
    return leak_sum


def _rewrite_rows(out, mutate):
    rows = list(csv.DictReader((out / "block_records.csv").read_text(encoding="utf-8").splitlines()))
    mutate(rows)
    with (out / "block_records.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(g20.BLOCK_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)


def test_u5_verifier_pass_and_isolation_tamper_fails(fake_root):
    _assert_no_production()
    out = fake_root / "g6r20_verify_fake"
    out.mkdir(parents=True)
    _write_fake_root(out)
    assert g20.verify_root(str(out)) is True
    # Tamper 1: undetected-merge (summary now stale) -> FAIL.
    def tamper_undetected(rows):
        rows[0]["undetected"] = "True"
        rows[0]["verified_exact"] = "False"
        rows[0]["outcome"] = "undetected"
    _rewrite_rows(out, tamper_undetected)
    assert g20.verify_root(str(out)) is False
    # Restore -> PASS; tamper 2: disclosure mismatch -> FAIL.
    def restore_undetected(rows):
        rows[0]["undetected"] = "False"
        rows[0]["verified_exact"] = "True"
        rows[0]["outcome"] = "exact"
    _rewrite_rows(out, restore_undetected)
    assert g20.verify_root(str(out)) is True
    def tamper_disclosure(rows):
        rows[1]["disclosure_bits"] = "563"
    _rewrite_rows(out, tamper_disclosure)
    assert g20.verify_root(str(out)) is False


def test_u5_verifier_beta_net_loader_tamper_fails(fake_root):
    _assert_no_production()
    out = fake_root / "g6r20_verify_fake2"
    out.mkdir(parents=True)
    _write_fake_root(out, accepted_n=90)
    assert g20.H_FROZEN == 3.347605 and g20.H_L2 == 3.222719884634378
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["net_secret_bits"] == 90 * 5 * 128 - 128 * 564
    assert summary["loader_calls"] == 0
    # Tamper: hand-filled beta (off by 1e-6) -> FAIL.
    summary["beta_eff_empirical_primary"] = float(summary["beta_eff_empirical_primary"]) + 1e-6
    (out / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    assert g20.verify_root(str(out)) is False
    # Tamper: hand-filled net (+1) -> FAIL.
    summary["beta_eff_empirical_primary"] = 1.0 - summary["disclosure_sum"] / (128 * 128 * g20.H_FROZEN)
    summary["net_secret_bits"] = int(summary["net_secret_bits"]) + 1
    (out / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    assert g20.verify_root(str(out)) is False
    # Tamper: loader invoked (loader_calls=1) -> FAIL.
    summary["net_secret_bits"] = g20.net_secret_bits(90, 128 * 564, g20.N)
    summary["loader_calls"] = 1
    (out / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    assert g20.verify_root(str(out)) is False
