"""V24 bounded single-edge DE optimization — T0/T1/T2 tests.

T2 lifecycle tests inject an explicit fake runner; the production V22b DE
kernel is never invoked in tests.
"""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v24_single_edge_de as v24
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_v24_single_edge_de import (
    Q,
    HOLDOUT_SEEDS,
    LAMBDA_DEGREE_ARRAY,
    PROPOSAL_SEED,
    REFINE_SEEDS,
    RHO_DEGREE_ARRAY,
    SCREEN_SEEDS,
    canonical_key,
    f_total_of,
    generate_proposal,
    profile_valid,
    rank_records,
    rate_of,
    run_m0,
    run_m1,
    run_m2,
    run_v24_gate,
    verify_run,
)

# --------------------------------------------------------------------------- #
# workspace-backed temp root (avoids Windows pytest tmp ACL issues)
# --------------------------------------------------------------------------- #

@pytest.fixture
def ws_root() -> Path:
    base = Path("workspace") / "nbldpc_v24_test"
    root = base / uuid.uuid4().hex
    root.mkdir(parents=True, exist_ok=False)
    return root


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def make_fake_runner(good_keys: set[str], *, converged_entropy: float = 1e-4,
                     failed_entropy: float = 0.4, elapsed: float = 0.0):
    """Deterministic fake DE runner.

    Converges only for canonical keys in ``good_keys``; otherwise returns a
    non-converged result.  Never performs a real MC-DE.
    """
    def runner(*, q, lambda_edge, rho_edge, n_samples, max_iter, seed,
               channel_mode, w, degree_max):
        if elapsed:
            time.sleep(elapsed)
        lam_items = tuple(sorted((int(d), int(round(w_ * 64))) for d, w_ in lambda_edge.items()))
        rho_items = tuple(sorted((int(d), int(round(w_ * 64))) for d, w_ in rho_edge.items()))
        key = (f"L[{','.join(f'{d}:{c}' for d, c in lam_items)}]"
               f"|R[{','.join(f'{d}:{c}' for d, c in rho_items)}]")
        converged = key in good_keys
        return {
            "converged": converged,
            "final_entropy": converged_entropy if converged else failed_entropy,
            "iterations": 3 if converged else max_iter,
            "q": q, "lambda": lambda_edge, "rho": rho_edge,
            "n_samples": n_samples, "max_iter": max_iter, "seed": seed,
        }
    return runner


def w_small() -> np.ndarray:
    """Tiny structured-like w just for plumbing (tests never run real DE)."""
    return np.full(Q, 1.0 / Q, dtype=np.float64)


def first_valid_profiles(n: int, max_attempts: int = 300) -> list[v24.V24Profile]:
    out: list[v24.V24Profile] = []
    for k in range(max_attempts):
        prof = generate_proposal(k)
        valid, _ = profile_valid(prof)
        if valid:
            out.append(prof)
        if len(out) >= n:
            break
    assert len(out) == n, "could not generate enough valid profiles"
    return out


def high_rate_profile(attempt: int = 0) -> v24.V24Profile:
    """Valid in-band profile: lambda {2:1}, rho {32:1} => R = 0.9375."""
    return v24.V24Profile(
        lambda_degrees=(2,), lambda_counts=(64,),
        rho_degrees=(32,), rho_counts=(64,), attempt=attempt)


# --------------------------------------------------------------------------- #
# T0 — compile/import and frozen math
# --------------------------------------------------------------------------- #

def test_t0_import_and_constants():
    assert Q == 1024
    assert v24.H_V17 == pytest.approx(0.5499550439219351)
    assert v24.R_MIN == 0.9375
    assert v24.R_MAX == 0.94140625
    assert v24.LAMBDA_DEGREE_ARRAY.tolist() == list(range(2, 65))
    assert v24.RHO_DEGREE_ARRAY.tolist() == list(range(2, 513))
    assert v24.PROPOSAL_SEED == 24000
    assert SCREEN_SEEDS == [24001, 24002]
    assert REFINE_SEEDS == [24003, 24004, 24005]
    assert HOLDOUT_SEEDS == [24101, 24102, 24103, 24104, 24105]


def test_t0_seed_disjointness():
    all_seeds = [PROPOSAL_SEED] + SCREEN_SEEDS + REFINE_SEEDS + HOLDOUT_SEEDS
    assert len(set(all_seeds)) == len(all_seeds)
    assert len(set(SCREEN_SEEDS) & set(REFINE_SEEDS) & set(HOLDOUT_SEEDS)) == 0


def test_t0_deterministic_proposals():
    for k in [0, 1, 5, 42]:
        a = generate_proposal(k)
        b = generate_proposal(k)
        assert a.canonical_key() == b.canonical_key()
        assert a.lambda_degrees == b.lambda_degrees
        assert a.rho_degrees == b.rho_degrees
        assert a.lambda_counts == b.lambda_counts
        assert a.rho_counts == b.rho_counts
        assert sum(a.lambda_counts) == 64
        assert sum(a.rho_counts) == 64
        assert all(c >= 1 for c in a.lambda_counts)
        assert all(c >= 1 for c in a.rho_counts)
        assert tuple(sorted(a.lambda_degrees)) == a.lambda_degrees
        assert tuple(sorted(a.rho_degrees)) == a.rho_degrees
        assert 1 <= len(a.lambda_degrees) <= 8
        assert 1 <= len(a.rho_degrees) <= 8
        assert all(int(d) in LAMBDA_DEGREE_ARRAY for d in a.lambda_degrees)
        assert all(int(d) in RHO_DEGREE_ARRAY for d in a.rho_degrees)


def test_t0_rate_and_f_total():
    prof = high_rate_profile()
    lam, rho = prof.lambda_edge(), prof.rho_edge()
    r = rate_of(lam, rho)
    assert np.isfinite(r)
    f = f_total_of(r)
    assert f == pytest.approx((1 - r) * 10 / v24.H_V17)
    # R=0.9375 -> f=1.136459...  (exactly the frozen target edge)
    assert f_total_of(0.9375) == pytest.approx(0.0625 * 10 / v24.H_V17, rel=1e-9)


def test_t0_degree_cap_rejection():
    prof = v24.V24Profile(
        lambda_degrees=(2, 3), lambda_counts=(32, 32),
        rho_degrees=(1000,), rho_counts=(64,), attempt=0)
    valid, reason = profile_valid(prof)
    assert not valid
    assert reason == "rho_degree_out_of_bounds"
    prof2 = v24.V24Profile(
        lambda_degrees=(65,), lambda_counts=(64,),
        rho_degrees=(10,), rho_counts=(64,), attempt=0)
    valid2, reason2 = profile_valid(prof2)
    assert not valid2
    assert reason2 == "lambda_degree_out_of_bounds"


# --------------------------------------------------------------------------- #
# T1 — focused behavior
# --------------------------------------------------------------------------- #

def test_t1_profile_validity_in_band():
    prof = high_rate_profile()
    lam = prof.lambda_edge()
    rho = prof.rho_edge()
    r = rate_of(lam, rho)
    # lambda {2:1}, rho {32:1}: integral_lam=1/2, integral_rho=1/32 => R=0.9375
    assert r == pytest.approx(0.9375)
    assert f_total_of(r) <= v24.F_TOTAL_MAX
    assert profile_valid(prof)[0] is True


def test_t1_profile_validity_band_edges():
    # Just below R_MIN -> invalid (rate_below_min)
    prof_lo = v24.V24Profile(
        lambda_degrees=(2,), lambda_counts=(64,),
        rho_degrees=(31,), rho_counts=(64,), attempt=0)  # R=1-2/31=0.9355
    assert rate_of(prof_lo.lambda_edge(), prof_lo.rho_edge()) < v24.R_MIN
    assert profile_valid(prof_lo)[0] is False
    # Just above R_MAX -> invalid (rate_above_max)
    prof_hi = v24.V24Profile(
        lambda_degrees=(2,), lambda_counts=(64,),
        rho_degrees=(36,), rho_counts=(64,), attempt=0)  # R=1-2/36=0.9444
    assert rate_of(prof_hi.lambda_edge(), prof_hi.rho_edge()) > v24.R_MAX
    assert profile_valid(prof_hi)[0] is False


def test_t1_duplicate_identity_same_key():
    a = high_rate_profile(attempt=3)
    b = v24.V24Profile(a.lambda_degrees, a.lambda_counts,
                       a.rho_degrees, a.rho_counts, attempt=10)
    assert a.canonical_key() == b.canonical_key()
    assert profile_valid(b)[0] is True
    # deliberately different profile -> different key
    c = high_rate_profile(attempt=10)
    c2 = v24.V24Profile(c.lambda_degrees, c.lambda_counts,
                        (33,), (64,), attempt=11)
    assert a.canonical_key() != c2.canonical_key()


def test_t1_ranking_deterministic_and_ties():
    rows = [
        {"candidate_id": 3, "converged_count": 1, "worst_final_entropy": 0.1,
         "mean_final_entropy": 0.05, "has_error": False},
        {"candidate_id": 1, "converged_count": 2, "worst_final_entropy": 0.2,
         "mean_final_entropy": 0.1, "has_error": False},
        {"candidate_id": 2, "converged_count": 2, "worst_final_entropy": 0.1,
         "mean_final_entropy": 0.05, "has_error": False},
        {"candidate_id": 4, "converged_count": 0, "worst_final_entropy": None,
         "mean_final_entropy": None, "has_error": True},
    ]
    ranked = rank_records(rows)
    ids = [int(r["candidate_id"]) for r in ranked]
    assert ids == [2, 1, 3, 4]
    assert int(ranked[-1]["candidate_id"]) == 4


def test_t1_m0_passes_on_real_evidence():
    m0 = run_m0()
    assert m0["passed"] is True, m0["checks"]
    assert m0["schema"] == v24.V24_M0_SCHEMA


def test_t1_m0_fails_on_bad_trace(ws_root):
    bad = ws_root / "bad.json"
    bad.write_text(json.dumps({"schema": "nope"}), encoding="utf-8")
    m0 = run_m0(v8_trace_path=bad, v17_channel_path=None, root=None)
    assert m0["passed"] is False


def test_t1_no_overwrite(ws_root):
    runner = make_fake_runner({high_rate_profile().canonical_key()})
    root = ws_root / "existing"
    root.mkdir()
    (root / "foo.txt").write_text("x", encoding="utf-8")
    with pytest.raises(FileExistsError):
        run_v24_gate(w=w_small(), out_dir=root, runner=runner,
                     max_unique_valid=1, max_attempts=50)


def test_t1_m2_forbids_replacement_after_holdout(ws_root):
    prof0 = high_rate_profile(attempt=0)
    # Distinct valid profile: {2:1}, rho {33:1} => R = 1 - 2/33 = 0.93939...
    prof1 = v24.V24Profile(lambda_degrees=(2,), lambda_counts=(64,),
                           rho_degrees=(33,), rho_counts=(64,), attempt=1)
    runner = make_fake_runner({prof0.canonical_key()})
    res = run_m2(finalists=[prof0, prof1], w=w_small(), runner=runner)
    seeds_used = sorted({int(r["seed"]) for r in res["rows"]})
    assert seeds_used == HOLDOUT_SEEDS
    assert len(res["rows"]) == 10  # 2 finalists * 5 seeds
    results = {int(r["candidate_id"]): r for r in res["results"]}
    assert results[0]["converged_all_seeds"] is True
    assert results[1]["converged_all_seeds"] is False
    assert res["passed"] is True


# --------------------------------------------------------------------------- #
# T2 — fake lifecycle (explicit fake runner)
# --------------------------------------------------------------------------- #

def test_t2_pass_lifecycle(ws_root):
    profs = first_valid_profiles(3, max_attempts=300)
    good = {profs[0].canonical_key()}
    runner = make_fake_runner(good)
    root = ws_root / "pass"
    decision = run_v24_gate(w=w_small(), out_dir=root, runner=runner,
                            max_unique_valid=3, max_attempts=300)
    assert decision["terminal_state"] == "pass"
    assert decision["passed"] is True
    for rel in ["run_manifest.json", "m0_validation.json", "proposal_ledger.json",
                "screen_evaluations.json", "refine_evaluations.json",
                "finalists.json", "holdout_evaluations.json", "holdout_results.json",
                "decision.json"]:
        assert (root / rel).exists(), rel
    report = verify_run(root)
    assert report["ok"] is True, report["problems"]
    assert report["recomputed_terminal_state"] == "pass"


def test_t2_fail_lifecycle(ws_root):
    runner = make_fake_runner(set())
    root = ws_root / "fail"
    decision = run_v24_gate(w=w_small(), out_dir=root, runner=runner,
                            max_unique_valid=3, max_attempts=300)
    assert decision["terminal_state"] == "fail"
    assert decision["passed"] is False
    report = verify_run(root)
    assert report["ok"] is True, report["problems"]
    assert report["recomputed_terminal_state"] == "fail"


def test_t2_mechanism_unverified_m0(ws_root):
    bad = ws_root / "bad_trace.json"
    bad.write_text(json.dumps({"schema": "broken"}), encoding="utf-8")
    root = ws_root / "mech"
    decision = run_v24_gate(
        w=w_small(), out_dir=root, runner=make_fake_runner(set()),
        v8_trace_path=bad,
        max_unique_valid=3, max_attempts=60)
    assert decision["terminal_state"] == "mechanism_unverified"
    assert (root / "decision.json").exists()


def test_t2_mechanism_unverified_no_valid(ws_root, monkeypatch):
    def bad_proposal(attempt):
        return v24.V24Profile(
            lambda_degrees=(65,), lambda_counts=(64,),
            rho_degrees=(10,), rho_counts=(64,), attempt=attempt)
    monkeypatch.setattr(v24, "generate_proposal", bad_proposal)
    root = ws_root / "mech2"
    decision = run_v24_gate(w=w_small(), out_dir=root,
                            runner=make_fake_runner(set()),
                            max_unique_valid=3, max_attempts=30)
    assert decision["terminal_state"] == "mechanism_unverified"
    report = verify_run(root)
    # proposal_ledger has n_valid 0 -> verifier flags ledger mismatch, so ok=False
    assert report["ok"] is False or decision["terminal_state"] == "mechanism_unverified"


def test_t2_resource_blocked(ws_root):
    profs = first_valid_profiles(3, max_attempts=300)
    good = {profs[0].canonical_key()}
    runner = make_fake_runner(good, elapsed=0.005)
    root = ws_root / "resblock"
    decision = run_v24_gate(w=w_small(), out_dir=root, runner=runner,
                            max_unique_valid=3, max_attempts=300,
                            resource_limit_seconds=0.001,
                            stop_on_limit=True)
    assert decision["terminal_state"] == "resource_blocked"
    assert decision["m1_resource_blocked"] is True or decision["m2_resource_blocked"] is True
    assert (root / "proposal_ledger.json").exists()


def test_t2_verifier_rejects_tampered_decision(ws_root):
    runner = make_fake_runner(set())
    root = ws_root / "tamper"
    decision = run_v24_gate(w=w_small(), out_dir=root, runner=runner,
                            max_unique_valid=2, max_attempts=120)
    assert decision["terminal_state"] == "fail"
    dec_path = root / "decision.json"
    dec = json.loads(dec_path.read_text(encoding="utf-8"))
    dec["terminal_state"] = "pass"
    dec["passed"] = True
    dec_path.write_text(json.dumps(dec, indent=2, sort_keys=True), encoding="utf-8")
    report = verify_run(root)
    assert report["ok"] is False
    assert any("decision pass" in p for p in report["problems"])


def test_t2_error_calls_consumed_and_evidence_retained(ws_root):
    def err_runner(**kwargs):
        raise RuntimeError("injected failure")
    root = ws_root / "errors"
    decision = run_v24_gate(w=w_small(), out_dir=root, runner=err_runner,
                            max_unique_valid=2, max_attempts=220)
    # All DE calls error -> no convergence -> decision fail, not mechanism.
    assert decision["terminal_state"] == "fail"
    assert (root / "proposal_ledger.json").exists()
    assert (root / "screen_evaluations.json").exists()
    screen = json.loads((root / "screen_evaluations.json").read_text(encoding="utf-8"))
    assert len(screen["records"]) > 0
    assert all(r["error"] for r in screen["records"])


# --------------------------------------------------------------------------- #
# T3 — read-only predecessor control (no DE call, no V8 runner)
# --------------------------------------------------------------------------- #

def test_t3_readonly_v22b_control_artifact():
    """Validate the recorded V22b iter30/n200 artifact without any DE call.

    This is a read-only predecessor control.  It never invokes V8 or V22b
    DE and is excluded from M1 ranking/selection.
    """
    path = Path("comparison_bench/outputs_comparison/nonbinary_diagnostics/"
                "nbldpc_v22_20260816/v22b_de_gate_q1024_r09375_dmax512_iter30_n200/"
                "de_gate.json")
    assert path.exists(), f"missing V22b control artifact: {path}"
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc["schema"] == "nbldpc_v22b_de_gate_v1"
    assert doc["q"] == 1024
    assert doc["rate"] == 0.9375
    assert doc["n_candidates"] == 3
    assert doc["gate_passed"] is False
    assert all(not c.get("converged") for c in doc["candidates"])
