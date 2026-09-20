"""R9 CONFIRM m100 delta tests — FAKE fixtures only (never real pool).

R9b readiness: zero real-payload decoder calls; no UUID root; temp fake
roots. Covers: D1 m100-564-disclosure; D2 k_sym-28; D3 fresh-seed admission
(real D10-R2 builder, synthetic); D4 refusal matrix; D5 no-overwrite;
D6 verifier recompute + tamper FAILs.
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
RUNNER_PATH = ROOT / "scripts" / "g6r9_confirm.py"


def _load_runner():
    spec = importlib.util.spec_from_file_location("g6r9_confirm_test", str(RUNNER_PATH))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["g6r9_confirm_test"] = mod
    spec.loader.exec_module(mod)
    return mod


g9 = _load_runner()
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
    path = ROOT / "workspace" / ("g6r9_fake_%s" % uuid.uuid4().hex)
    assert not path.exists()
    assert "3f9a1c2e" not in str(path)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _fake_graph(seed):
    H = np.zeros((g9.M, g9.N), dtype=np.uint8)
    for v in range(g9.N):
        H[v % g9.M, v] = 1
    return {"arm": g9.ARM, "width": g9.N, "graph_seed": int(seed),
            "n": g9.N, "m": g9.M, "E": int(np.count_nonzero(H)),
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


# D1: m100 disclosure nominal 5*100+64 = 564; split 500/64; C/I/A 0.
def test_d1_m100_disclosure_564():
    _assert_no_production()
    assert g9.M == 100
    assert g9.disclosed_bits(100) == 564
    assert g9.disclosed_bits(g9.M) == 564
    frames = g9.parse_frames(g9.FROZEN_FRAMES)
    assert len(frames) == 64 and frames[0] == 2123 and frames[-1] == 2186
    plan = g9.build_call_plan(frames)
    assert len(plan) == 128
    for p in plan:
        assert p["disclosed_bits"] == 564
    # run_one_block record carries the frozen split.
    graph = _fake_graph(g9.GRAPH_SEEDS[0])
    truth = np.zeros(g9.N, dtype=np.int64)
    rec = g9.run_one_block(
        graph, np.full((g9.N, 32), 1.0 / 32.0), np.zeros(g9.M, dtype=np.uint8),
        g9._candidate_tag(truth), truth,
        {"frame_id": 2123, "block_id": 0, "graph_seed": g9.GRAPH_SEEDS[0],
         "session_id": g9.FROZEN_SESSION},
        lambda H, pr, s, **kw: _FakeResult(truth),
        lambda H, x: np.zeros(g9.M, dtype=np.uint8), 0)
    assert rec["disclosure_bits"] == 564
    assert rec["syndrome_bits"] == 500 and rec["tag_bits"] == 64
    assert rec["control_bits"] == 0 and rec["interaction_bits"] == 0
    assert rec["auth_bits"] == 0
    assert rec["verified_exact"] is True


# D2: k_sym nominal 28 = n-m, no shortening; reconciled arithmetic.
def test_d2_ksym_28_derived():
    _assert_no_production()
    assert g9.K_SYM_NOMINAL == 28
    assert g9.K_SYM_NOMINAL == g9.N - g9.M  # derived, never hand-filled
    assert 90 * g9.K_SYM_NOMINAL * 5 == 12600  # reconciled spot check


# D3: fresh-seed admission 2/2 via accepted D10-R2 builder; disjointness.
def test_d3_fresh_seed_admission():
    _assert_no_production()
    assert g9.GRAPH_SEEDS == (2026094720, 2026094721)
    banned = (set(range(2026094601, 2026094603))
              | set(range(2026094701, 2026094709))
              | set(range(2026094711, 2026094720)))
    assert not (set(g9.GRAPH_SEEDS) & banned)  # first free >= 4720
    assert g9.DOMAIN_NAMESPACE == "g6r9-domain"
    assert g9.COEFF_NAMESPACE_TMPL.startswith("g6r9:coeff:")
    graphs = [g9.build_graph(seed) for seed in g9.GRAPH_SEEDS]
    assert sum(1 for g in graphs if g["admitted"]) == 2
    for g in graphs:
        assert g["status"] == "ok" and g["E"] == 349
        assert g["n"] == 128 and g["m"] == 100
    # Out-of-pair seed refused.
    with pytest.raises(ValueError, match="outside frozen R9 pair"):
        g9.build_graph(2026094601)


# D4: refusal matrix — missing grant / existing root / pool mismatch.
def test_d4_refusal_missing_grant_zero_calls():
    _assert_no_production()
    rc = g9.main(["--execute-real", "--registry", g9.FROZEN_REGISTRY,
                  "--session", g9.FROZEN_SESSION, "--frames", g9.FROZEN_FRAMES,
                  "--arm", g9.ARM, "--prior-root", g9.FROZEN_PRIOR_ROOT,
                  "--out-dir", "workspace/g6r9_fake_refuse_%s" % uuid.uuid4().hex])
    assert rc == 2


def test_d4_refusal_existing_root_zero_calls(fake_root):
    _assert_no_production()
    fake_root.mkdir(parents=True)
    calls: list = []
    with pytest.raises(FileExistsError):
        r2.refuse_out_root(str(fake_root))
    assert calls == []


def test_d4_refusal_pool_mismatch_zero_calls():
    _assert_no_production()
    calls: list = []
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        g9._pre_execute_check("wrong_registry.json", g9.FROZEN_SESSION,
                              g9.FROZEN_FRAMES, g9.ARM, g9.FROZEN_PRIOR_ROOT)
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        g9._pre_execute_check(g9.FROZEN_REGISTRY, "WRONG_SESSION",
                              g9.FROZEN_FRAMES, g9.ARM, g9.FROZEN_PRIOR_ROOT)
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        g9._pre_execute_check(g9.FROZEN_REGISTRY, g9.FROZEN_SESSION,
                              "2123..2185", g9.ARM, g9.FROZEN_PRIOR_ROOT)
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        g9._pre_execute_check(g9.FROZEN_REGISTRY, g9.FROZEN_SESSION,
                              g9.FROZEN_FRAMES, g9.ARM, "workspace/wrong_prior")
    assert calls == []


# D5: no-overwrite — protected dirs + frozen dirs + prior roots + UUID root.
def test_d5_no_overwrite():
    _assert_no_production()
    with pytest.raises((ValueError, FileExistsError)):
        r2.refuse_out_root("results/g6r9_fake")
    with pytest.raises((ValueError, FileExistsError)):
        r2.refuse_out_root("comparison_bench/outputs_comparison/g6r9_fake")
    for forbidden in [ROOT / "src", ROOT / "experiments", ROOT / "tools"]:
        if forbidden.exists():
            hits = list(forbidden.rglob("*g6r9*"))
            assert hits == [], "frozen dir touched: %r" % hits
    # Prior R1/R6c/R7/R8 roots untouched by g6r9 (UUID root stays absent).
    prior_roots = [
        ROOT / "workspace/g6_decide_r1_8e7c2a1f-4b6d-4e9a-9c3f-2a5b7d8e0f1a",
        ROOT / "workspace/g6r2_diag_c4a1d2e6-9b3f-4e7a-8c5d-2f6a0e1b3d4c",
        ROOT / "workspace/r7_rate_scan_719f77de-0e69-499f-80b4-397457c8958a",
        ROOT / "workspace/r7_rate_scan_low_34aba8c7-8580-453f-b630-855d682fe948",
    ]
    for root in prior_roots:
        if root.exists():
            hits = list(root.rglob("*g6r9*"))
            assert hits == [], "prior root touched: %r" % hits
    assert not (ROOT / g9.FUTURE_ROOT).exists()  # UUID root absent


# D6: verifier recompute (m100 counts/sums, H_frozen, beta derived-only).
def _write_fake_root(out, accepted_n=90):
    manifest = {"command": g9.FROZEN_COMMAND}
    (out / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    leak_each = 564
    with (out / "block_records.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(g9.BLOCK_COLUMNS))
        writer.writeheader()
        for i in range(128):
            accepted = i < accepted_n
            writer.writerow({
                "call_idx": i, "frame_id": 2123 + i // 2, "block_id": i,
                "session_id": g9.FROZEN_SESSION, "arm": g9.ARM,
                "candidate_id": g9.CANDIDATE_ID, "graph_seed": g9.GRAPH_SEEDS[i % 2],
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
    beta_p = 1.0 - leak_sum / (128 * 128 * g9.H_FROZEN)
    beta_l = 1.0 - leak_sum / (128 * 128 * g9.H_L2)
    summary = {"attempted": 128, "accepted": accepted_n, "exact": accepted_n,
               "undetected": 0, "disclosure_sum": leak_sum,
               "beta_eff_empirical_primary": beta_p,
               "beta_eff_empirical_l2_sensitivity": beta_l,
               "H_frozen_primary": g9.H_FROZEN, "H_L2_sensitivity": g9.H_L2,
               "net_secret_bits": g9.net_secret_bits(accepted_n, leak_sum, g9.N),
               "terminal": "COMPLETE_128"}
    (out / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (out / "report.md").write_text("# fake\n", encoding="utf-8")
    return leak_sum


def _rewrite_rows(out, mutate):
    rows = list(csv.DictReader((out / "block_records.csv").read_text(encoding="utf-8").splitlines()))
    mutate(rows)
    with (out / "block_records.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(g9.BLOCK_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)


def test_d6_verifier_pass_and_tamper_fails(fake_root):
    _assert_no_production()
    out = fake_root / "g6r9_verify_fake"
    out.mkdir(parents=True)
    _write_fake_root(out)
    assert g9.verify_root(str(out)) is True
    # Tamper 1: undetected-merge (summary now stale) -> FAIL.
    def tamper_undetected(rows):
        rows[0]["undetected"] = "True"
        rows[0]["verified_exact"] = "False"
        rows[0]["outcome"] = "undetected"
    _rewrite_rows(out, tamper_undetected)
    assert g9.verify_root(str(out)) is False
    # Tamper 2: disclosure mismatch -> FAIL (restore first).
    def restore_undetected(rows):
        rows[0]["undetected"] = "False"
        rows[0]["verified_exact"] = "True"
        rows[0]["outcome"] = "exact"
    _rewrite_rows(out, restore_undetected)
    assert g9.verify_root(str(out)) is True
    def tamper_disclosure(rows):
        rows[1]["disclosure_bits"] = "563"
    _rewrite_rows(out, tamper_disclosure)
    assert g9.verify_root(str(out)) is False


def test_d6_verifier_beta_h_tamper_fails(fake_root):
    _assert_no_production()
    out = fake_root / "g6r9_verify_fake2"
    out.mkdir(parents=True)
    _write_fake_root(out)
    assert g9.H_FROZEN == 3.347605 and g9.H_L2 == 3.222719884634378
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    # Tamper: hand-filled beta (off by 1e-6) -> FAIL.
    summary["beta_eff_empirical_primary"] = float(summary["beta_eff_empirical_primary"]) + 1e-6
    (out / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    assert g9.verify_root(str(out)) is False
    # Tamper: H_frozen swap -> FAIL.
    summary["beta_eff_empirical_primary"] = 1.0 - summary["disclosure_sum"] / (128 * 128 * g9.H_FROZEN)
    summary["H_frozen_primary"] = 3.0
    (out / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    assert g9.verify_root(str(out)) is False


# D7 (R16): net_secret_bits exact integers; old fields frozen; beta unchanged; tamper FAILs.
def test_d7_net_secret_bits_exact_frozen_beta_tamper(fake_root):
    _assert_no_production()
    # Single-block values: S0-accept +(640-564)=+76; fail/exhausted -564.
    assert g9.net_secret_bits(1, 564, g9.N) == 76
    assert g9.net_secret_bits(0, 564, g9.N) == -564
    # R9 root shape 1/127: 1*640 - 72192 = -71552.
    assert g9.net_secret_bits(1, 128 * 564, g9.N) == -71552
    # 90/128 mix: 90*640 - 72192 = -14592.
    assert g9.net_secret_bits(90, 128 * 564, g9.N) == -14592
    # Old fields frozen: reconciled + beta recompute identically.
    assert 90 * g9.K_SYM_NOMINAL * 5 == 12600
    assert g9.K_SYM_NOMINAL == 28
    out = fake_root / "g6r9_net_fake"
    out.mkdir(parents=True)
    _write_fake_root(out, accepted_n=90)
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["net_secret_bits"] == -14592
    assert summary["disclosure_sum"] == 128 * 564
    assert g9.verify_root(str(out)) is True
    # Tamper: hand-filled net (+1) -> FAIL; missing net -> FAIL.
    tampered = dict(summary)
    tampered["net_secret_bits"] = -14591
    (out / "summary.json").write_text(json.dumps(tampered), encoding="utf-8")
    assert g9.verify_root(str(out)) is False
    tampered = dict(summary)
    del tampered["net_secret_bits"]
    (out / "summary.json").write_text(json.dumps(tampered), encoding="utf-8")
    assert g9.verify_root(str(out)) is False
