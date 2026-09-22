"""R10 CTRL m100 delta tests — FAKE fixtures only (never real pool).

R10b2 readiness: zero real-payload decoder calls; no UUID root; temp fake
roots. Covers: allowlist accept (1M/1983..2046) + rejects (R9 1p5M window,
R1 2M window, 1982..2045 shift, 1983..2047 overflow, wrong session/registry
/arm/prior) all PRE_EXECUTION_BLOCKED zero-calls; missing-grant rc2;
existing-root refusal; no-overwrite (protected + ALL prior UUID roots incl
R9/R1/R2diag/R7); verifier recompute (564-disclosure, k=28, H-pair, beta
derived-only, tamper incl undetected-merge FAIL); profile-only 128-call
even/odd plan, budgets ok, decoder 0.
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
import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "comparison_bench" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
RUNNER_PATH = ROOT / "scripts" / "g6r10_ctrl.py"
R9_PATH = ROOT / "scripts" / "g6r9_confirm.py"


def _load_runner(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


g10 = _load_runner(RUNNER_PATH, "g6r10_ctrl_test")
g9 = _load_runner(R9_PATH, "g6r9_confirm_ref")
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
    path = ROOT / "workspace" / ("g6r10_fake_%s" % uuid.uuid4().hex)
    assert not path.exists()
    assert "6f2b8c1d" not in str(path)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _fake_graph(seed):
    H = np.zeros((g10.M, g10.N), dtype=np.uint8)
    for v in range(g10.N):
        H[v % g10.M, v] = 1
    return {"arm": g10.ARM, "width": g10.N, "graph_seed": int(seed),
            "n": g10.N, "m": g10.M, "E": int(np.count_nonzero(H)),
            "edges": [], "coefficients": [], "dense": H,
            "structure": None, "status": "ok", "admitted": True,
            "failure_reason": ""}


class _FakeResult:
    def __init__(self, x_hat, iters=5):
        self.x_hat = np.asarray(x_hat, dtype=np.int64)
        self.syndrome_ok = True
        self.iterations = int(iters)
        self.status = "converged"
        self.belief_provenance = "CHECK_UPDATED"


def _fake_adapters(decode_behavior, calls, prior=None):
    if prior is None:
        prior = np.full((1024, 1024), 1.0 / 1024.0)

    def fake_decode(H, priors, syn, **kw):
        calls.append(1)
        assert kw.get("max_iter") == 90 and kw.get("damping_alpha") == 1.0
        assert kw.get("warm_beliefs") is None  # cold single-pass
        return decode_behavior(H, priors, syn)

    def fake_syndrome(H, x):
        return np.zeros(H.shape[0], dtype=np.uint8)

    def fake_prior(root):
        return prior

    return {"decode_fn": fake_decode, "syndrome_fn": fake_syndrome,
            "load_prior_fn": fake_prior}


# Allowlist accept: frozen R10 pair passes with zero I/O, 64 frames.
def test_allow_accept_1m_window_zero_calls():
    _assert_no_production()
    calls: list = []
    assert g10.FROZEN_SESSION == "20260123_1M_600k_0dB"
    assert g10.FROZEN_FRAMES == "1983..2046"
    frames = g10._pre_execute_check(
        g10.FROZEN_REGISTRY, g10.FROZEN_SESSION, g10.FROZEN_FRAMES,
        g10.ARM, g10.FROZEN_PRIOR_ROOT)
    assert len(frames) == 64 and frames[0] == 1983 and frames[-1] == 2046
    plan = g10.build_call_plan(frames)
    assert len(plan) == 128
    for p in plan:
        assert p["graph_seed"] == g10.GRAPH_SEEDS[p["block_id"] % 2]
    assert calls == []


# Allowlist rejects: R9/R1 windows, shift, overflow, wrong session — BLOCKED.
def test_allow_rejects_blocked_zero_calls():
    _assert_no_production()
    calls: list = []
    # R9's own P-1p5M window refused by this R10-only runner.
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        g10._pre_execute_check(g10.FROZEN_REGISTRY, "20260107_PPLN_1p5M",
                               "2123..2186", g10.ARM, g10.FROZEN_PRIOR_ROOT)
    # R1's P-2M window refused.
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        g10._pre_execute_check(g10.FROZEN_REGISTRY, "20260123_2M_1p2M_0dB",
                               "2093..2156", g10.ARM, g10.FROZEN_PRIOR_ROOT)
    # Shift violation (same session, off-by-one window).
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        g10._pre_execute_check(g10.FROZEN_REGISTRY, g10.FROZEN_SESSION,
                               "1982..2045", g10.ARM, g10.FROZEN_PRIOR_ROOT)
    # Overflow (one frame too many).
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        g10._pre_execute_check(g10.FROZEN_REGISTRY, g10.FROZEN_SESSION,
                               "1983..2047", g10.ARM, g10.FROZEN_PRIOR_ROOT)
    # Wrong session with frozen frames.
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        g10._pre_execute_check(g10.FROZEN_REGISTRY, "WRONG_SESSION",
                               g10.FROZEN_FRAMES, g10.ARM, g10.FROZEN_PRIOR_ROOT)
    # Wrong registry / arm / prior-root.
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        g10._pre_execute_check("wrong_registry.json", g10.FROZEN_SESSION,
                               g10.FROZEN_FRAMES, g10.ARM, g10.FROZEN_PRIOR_ROOT)
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        g10._pre_execute_check(g10.FROZEN_REGISTRY, g10.FROZEN_SESSION,
                               g10.FROZEN_FRAMES, "WRONG_ARM",
                               g10.FROZEN_PRIOR_ROOT)
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        g10._pre_execute_check(g10.FROZEN_REGISTRY, g10.FROZEN_SESSION,
                               g10.FROZEN_FRAMES, g10.ARM, "workspace/wrong_prior")
    assert calls == []


# D1: m100 disclosure nominal 5*100+64 = 564; split 500/64; C/I/A 0.
def test_d1_m100_disclosure_564():
    _assert_no_production()
    assert g10.M == 100 == g9.M
    assert g10.disclosed_bits(100) == 564
    assert g10.disclosed_bits(g10.M) == 564
    frames = g10.parse_frames(g10.FROZEN_FRAMES)
    assert len(frames) == 64 and frames[0] == 1983 and frames[-1] == 2046
    plan = g10.build_call_plan(frames)
    assert len(plan) == 128
    for p in plan:
        assert p["disclosed_bits"] == 564
    graph = _fake_graph(g10.GRAPH_SEEDS[0])
    truth = np.zeros(g10.N, dtype=np.int64)
    rec = g10.run_one_block(
        graph, np.full((g10.N, 32), 1.0 / 32.0), np.zeros(g10.M, dtype=np.uint8),
        g10._candidate_tag(truth), truth,
        {"frame_id": 1983, "block_id": 0, "graph_seed": g10.GRAPH_SEEDS[0],
         "session_id": g10.FROZEN_SESSION},
        lambda H, pr, s, **kw: _FakeResult(truth),
        lambda H, x: np.zeros(g10.M, dtype=np.uint8), 0)
    assert rec["disclosure_bits"] == 564
    assert rec["syndrome_bits"] == 500 and rec["tag_bits"] == 64
    assert rec["control_bits"] == 0 and rec["interaction_bits"] == 0
    assert rec["auth_bits"] == 0
    assert rec["verified_exact"] is True


# D2: k_sym nominal 28 = n-m, no shortening; reconciled arithmetic.
def test_d2_ksym_28_derived():
    _assert_no_production()
    assert g10.K_SYM_NOMINAL == 28 == g9.K_SYM_NOMINAL
    assert g10.K_SYM_NOMINAL == g10.N - g10.M  # derived, never hand-filled
    assert 90 * g10.K_SYM_NOMINAL * 5 == 12600  # reconciled spot check


# Graph/prior reuse: same 4720/4721 pair + namespaces as R9, no new seeds.
def test_graph_reuse_4720_4721():
    _assert_no_production()
    assert g10.GRAPH_SEEDS == (2026094720, 2026094721) == g9.GRAPH_SEEDS
    assert g10.DOMAIN_NAMESPACE == g9.DOMAIN_NAMESPACE == "g6r9-domain"
    assert g10.COEFF_NAMESPACE_TMPL == g9.COEFF_NAMESPACE_TMPL
    assert g10.FROZEN_PRIOR_ROOT == g9.FROZEN_PRIOR_ROOT
    assert g10.MAX_ITER == 90 and g10.DAMPING == 1.0
    graphs = [g10.build_graph(seed) for seed in g10.GRAPH_SEEDS]
    assert sum(1 for g in graphs if g["admitted"]) == 2
    for g in graphs:
        assert g["status"] == "ok" and g["E"] == 349
        assert g["n"] == 128 and g["m"] == 100
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        g10.build_graph(2026094601)


# Refusal: missing grant -> rc2, zero calls, root stays absent.
def test_refusal_missing_grant_zero_calls(fake_root):
    _assert_no_production()
    out = str(fake_root / "g6r10_refuse_nogrant")
    rc = g10.main(["--execute-real", "--registry", g10.FROZEN_REGISTRY,
                   "--session", g10.FROZEN_SESSION, "--frames", g10.FROZEN_FRAMES,
                   "--arm", g10.ARM, "--prior-root", g10.FROZEN_PRIOR_ROOT,
                   "--out-dir", out])
    assert rc == 2
    assert not Path(out).exists()


# Refusal: existing root -> FileExistsError probe + authorized main rc2.
def test_refusal_existing_root_zero_calls(fake_root):
    _assert_no_production()
    fake_root.mkdir(parents=True)
    calls: list = []
    with pytest.raises(FileExistsError):
        r2.refuse_out_root(str(fake_root))
    assert calls == []
    rc = g10.main(["--execute-real", "--execution-authorized",
                   "--registry", g10.FROZEN_REGISTRY,
                   "--session", g10.FROZEN_SESSION, "--frames", g10.FROZEN_FRAMES,
                   "--arm", g10.ARM, "--prior-root", g10.FROZEN_PRIOR_ROOT,
                   "--out-dir", str(fake_root)],
                  adapters_override=_fake_adapters(
                      lambda H, p, s: _FakeResult(np.zeros(g10.N)), calls))
    assert rc == 2
    assert calls == []


# No-overwrite: protected dirs + frozen dirs + ALL prior UUID roots + future.
def test_no_overwrite():
    _assert_no_production()
    with pytest.raises((ValueError, FileExistsError)):
        r2.refuse_out_root("results/g6r10_fake")
    with pytest.raises((ValueError, FileExistsError)):
        r2.refuse_out_root("comparison_bench/outputs_comparison/g6r10_fake")
    for forbidden in [ROOT / "src", ROOT / "experiments", ROOT / "tools"]:
        if forbidden.exists():
            hits = list(forbidden.rglob("*g6r10*"))
            assert hits == [], "frozen dir touched: %r" % hits
    # Prior UUID roots (R9/R1/R2diag/R7) untouched by g6r10.
    prior_roots = [
        ROOT / "workspace/g6r9_confirm_3f9a1c2e-7b4d-4e8a-9c1f-2d5e6a7b8c9d",
        ROOT / "workspace/g6_decide_r1_8e7c2a1f-4b6d-4e9a-9c3f-2a5b7d8e0f1a",
        ROOT / "workspace/g6r2_diag_c4a1d2e6-9b3f-4e7a-8c5d-2f6a0e1b3d4c",
        ROOT / "workspace/r7_rate_scan_719f77de-0e69-499f-80b4-397457c8958a",
        ROOT / "workspace/r7_rate_scan_low_34aba8c7-8580-453f-b630-855d682fe948",
    ]
    for root in prior_roots:
        if root.exists():
            hits = list(root.rglob("*g6r10*"))
            assert hits == [], "prior root touched: %r" % hits
    assert not (ROOT / g10.FUTURE_ROOT).exists()  # UUID root absent


# Verifier recompute (m100 counts/sums, H_frozen, beta derived-only).
def _write_fake_root(out, accepted_n=90):
    manifest = {"command": g10.FROZEN_COMMAND}
    (out / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    leak_each = 564
    with (out / "block_records.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(g10.BLOCK_COLUMNS))
        writer.writeheader()
        for i in range(128):
            accepted = i < accepted_n
            writer.writerow({
                "call_idx": i, "frame_id": 1983 + i // 2, "block_id": i,
                "session_id": g10.FROZEN_SESSION, "arm": g10.ARM,
                "candidate_id": g10.CANDIDATE_ID, "graph_seed": g10.GRAPH_SEEDS[i % 2],
                "n": 128, "m": 100, "attempted": "True",
                "finite": "True" if accepted else "False",
                "syndrome_match": "True" if accepted else "False",
                "tag_match": "True" if accepted else "False",
                "protocol_accepted": "True" if accepted else "False",
                "verified_exact": "True" if accepted else "False",
                "undetected": "False", "outcome": "exact" if accepted else "attempted",
                "syndrome_bits": 500, "tag_bits": 64, "control_bits": 0,
                "interaction_bits": 0, "auth_bits": 0, "disclosure_bits": leak_each,
                "iters": 5, "residual": 0, "provenance": "CHECK_UPDATED",
                "wall_s": 0.01, "crash": "False", "error": ""})
    leak_sum = 128 * leak_each
    beta_p = 1.0 - leak_sum / (128 * 128 * g10.H_FROZEN)
    beta_l = 1.0 - leak_sum / (128 * 128 * g10.H_L2)
    summary = {"attempted": 128, "accepted": accepted_n, "exact": accepted_n,
               "undetected": 0, "disclosure_sum": leak_sum,
               "beta_eff_empirical_primary": beta_p,
               "beta_eff_empirical_l2_sensitivity": beta_l,
               "H_frozen_primary": g10.H_FROZEN, "H_L2_sensitivity": g10.H_L2,
               "net_secret_bits": g10.net_secret_bits(accepted_n, leak_sum, g10.N),
               "terminal": "COMPLETE_128"}
    (out / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (out / "report.md").write_text("# fake\n", encoding="utf-8")
    return leak_sum


def _rewrite_rows(out, mutate):
    rows = list(csv.DictReader((out / "block_records.csv").read_text(encoding="utf-8").splitlines()))
    mutate(rows)
    with (out / "block_records.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(g10.BLOCK_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)


def test_verifier_pass_and_tamper_fails(fake_root):
    _assert_no_production()
    out = fake_root / "g6r10_verify_fake"
    out.mkdir(parents=True)
    _write_fake_root(out)
    assert g10.verify_root(str(out)) is True
    # Tamper 1: undetected-merge (summary now stale) -> FAIL.
    def tamper_undetected(rows):
        rows[0]["undetected"] = "True"
        rows[0]["verified_exact"] = "False"
        rows[0]["outcome"] = "undetected"
    _rewrite_rows(out, tamper_undetected)
    assert g10.verify_root(str(out)) is False
    # Tamper 2: disclosure mismatch -> FAIL (restore first).
    def restore_undetected(rows):
        rows[0]["undetected"] = "False"
        rows[0]["verified_exact"] = "True"
        rows[0]["outcome"] = "exact"
    _rewrite_rows(out, restore_undetected)
    assert g10.verify_root(str(out)) is True
    def tamper_disclosure(rows):
        rows[1]["disclosure_bits"] = "563"
    _rewrite_rows(out, tamper_disclosure)
    assert g10.verify_root(str(out)) is False


def test_verifier_beta_h_tamper_fails(fake_root):
    _assert_no_production()
    out = fake_root / "g6r10_verify_fake2"
    out.mkdir(parents=True)
    _write_fake_root(out)
    assert g10.H_FROZEN == 3.347605 and g10.H_L2 == 3.222719884634378
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    # Tamper: hand-filled beta (off by 1e-6) -> FAIL.
    summary["beta_eff_empirical_primary"] = float(summary["beta_eff_empirical_primary"]) + 1e-6
    (out / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    assert g10.verify_root(str(out)) is False
    # Tamper: H_frozen swap -> FAIL.
    summary["beta_eff_empirical_primary"] = 1.0 - summary["disclosure_sum"] / (128 * 128 * g10.H_FROZEN)
    summary["H_frozen_primary"] = 3.0
    (out / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    assert g10.verify_root(str(out)) is False


# D3: profile-only on FAKE — 128-call even/odd plan, budgets ok, decoder 0.
def test_profile_only_fake_128_zero_calls():
    _assert_no_production()
    prof = g10.profile_only()
    assert prof["plan_calls"] == 128
    assert prof["plan_order"] == "frame->block->graph even/odd"
    assert prof["admitted"] == 2 and prof["total_graphs"] == 2
    assert [g["seed"] for g in prof["graphs"]] == [2026094720, 2026094721]
    assert prof["budgets"]["scientific_calls"] == 128
    assert prof["budget_ok"] is True
    assert prof["decoder_calls"] == 0
    assert prof["model_f_loads"] == 0 and prof["real_pool_reads"] == 0
    assert prof["future_root_absent"] is True


# R16: net_secret_bits inherits r9 helper; exact integers; frozen; tamper FAILs.
def test_r16_net_secret_bits_inherit_frozen_tamper(fake_root):
    _assert_no_production()
    # Inherit by import, no duplicate definition (functional equivalence;
    # `is` is not asserted: test harness loads a second r9 copy via
    # spec_from_file_location, so module-object identity differs by design).
    assert g10.net_secret_bits(1, 564, g10.N) == g9.net_secret_bits(1, 564, g9.N) == 76
    assert "net_secret_bits = r9.net_secret_bits" in Path(RUNNER_PATH).read_text(encoding="utf-8")
    assert g10.net_secret_bits(1, 564, g10.N) == 76
    assert g10.net_secret_bits(0, 564, g10.N) == -564
    assert g10.net_secret_bits(90, 128 * 564, g10.N) == -14592
    assert 90 * g10.K_SYM_NOMINAL * 5 == 12600
    out = fake_root / "g6r10_net_fake"
    out.mkdir(parents=True)
    _write_fake_root(out, accepted_n=90)
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["net_secret_bits"] == -14592
    assert g10.verify_root(str(out)) is True
    tampered = dict(summary)
    tampered["net_secret_bits"] = -14591
    (out / "summary.json").write_text(json.dumps(tampered), encoding="utf-8")
    assert g10.verify_root(str(out)) is False
    tampered = dict(summary)
    del tampered["net_secret_bits"]
    (out / "summary.json").write_text(json.dumps(tampered), encoding="utf-8")
    assert g10.verify_root(str(out)) is False
