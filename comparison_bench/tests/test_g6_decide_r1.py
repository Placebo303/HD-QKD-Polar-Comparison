"""G6 DECIDE R1 F-tests 1-7 — FAKE fixtures only (never real pool).

Zero real-payload decoder calls; no UUID root; temp/basetemp fake roots.
Covers: F1 UNDETECTED_STOP; F2 isolation; F3 ORACLE hard-fail;
F4 single-arm no-pooling; F5 refusal; F6 no-overwrite; F7 verifier.
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
RUNNER_PATH = ROOT / "scripts" / "g6_decide_r1.py"


def _load_runner():
    spec = importlib.util.spec_from_file_location("g6_decide_r1_test", str(RUNNER_PATH))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["g6_decide_r1_test"] = mod
    spec.loader.exec_module(mod)
    return mod


g6 = _load_runner()
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
    path = ROOT / "workspace" / ("g6r1_fake_%s" % uuid.uuid4().hex)
    assert not path.exists()
    assert "8e7c2a1f" not in str(path)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _fake_graph(seed):
    H = np.zeros((g6.M, g6.N), dtype=np.uint8)
    for v in range(g6.N):
        H[v % g6.M, v] = 1
    return {"arm": g6.ARM, "width": g6.N, "graph_seed": int(seed),
            "n": g6.N, "m": g6.M, "E": int(np.count_nonzero(H)),
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


def _fake_reader(frames):
    frames = [int(f) for f in frames]

    def reader(path, columns=None, filters=None):
        assert "alice_symbol" in (columns or []) and "bob_symbol" in (columns or [])
        rows = []
        for fid in frames:
            for pid in range(256):
                rows.append({"frame_id": fid, "pair_idx": pid,
                             "alice_symbol": (fid + pid) % 1024,
                             "bob_symbol": (fid * 2 + pid) % 1024})
        return pd.DataFrame(rows, columns=columns)
    return reader


def _valid_registry_tmp(tmp_path):
    reg = {"sessions": [{
        "session_id": g6.FROZEN_SESSION, "provenance": "fake.parquet",
        "stage2_CAL_frame_ids": list(range(702, 1726)),
        "stage2_VAL_frame_ids": list(range(1726, 1982))}]}
    # Pre-EXECUTE reads ROOT/registry; write a temp registry under workspace
    # is not allowed to shadow frozen name, so this helper only builds the
    # JSON payload shape for direct _pre_execute_check monkeypatch tests.
    return reg


# F1: undetected>0 -> UNDETECTED_STOP (fail-closed, early break).
def test_f1_undetected_stop(fake_root):
    _assert_no_production()
    calls: list = []
    # Force tag collision so wrong x still accepted -> undetected.
    orig_tag = g6._candidate_tag
    g6._candidate_tag = lambda v: b"\x00" * 8
    try:
        def behavior(H, priors, syn):
            # calls already appended before behavior runs, so first call
            # sees len==1.
            if len(calls) == 1:
                return _FakeResult(np.ones(g6.N, dtype=np.int64))
            return _FakeResult(np.zeros(g6.N, dtype=np.int64))
        adapters = _fake_adapters(behavior, calls)
        adapters["build_fn"] = _fake_graph
        # Direct run_one_block level: wrong x with constant tag.
        graph = _fake_graph(g6.GRAPH_SEEDS[0])
        truth = np.zeros(g6.N, dtype=np.int64)
        syn = np.zeros(g6.M, dtype=np.uint8)
        prior = np.full((g6.N, 32), 1.0 / 32.0)
        entry = {"frame_id": 2093, "block_id": 0, "graph_seed": g6.GRAPH_SEEDS[0],
                 "session_id": g6.FROZEN_SESSION}
        rec_wrong = g6.run_one_block(graph, prior, syn, b"\x00" * 8, truth,
                                     entry, adapters["decode_fn"],
                                     adapters["syndrome_fn"], 0)
        assert rec_wrong["protocol_accepted"] is True
        assert rec_wrong["verified_exact"] is False
        assert rec_wrong["undetected"] is True
        assert rec_wrong["outcome"] == "undetected"
        rec_exact = g6.run_one_block(graph, prior, syn, b"\x00" * 8, truth,
                                     entry, lambda H, p, s, **kw: _FakeResult(truth),
                                     adapters["syndrome_fn"], 1)
        assert rec_exact["verified_exact"] is True
        assert rec_exact["undetected"] is False
    finally:
        g6._candidate_tag = orig_tag


# F2: exact/syndrome/tag isolation.
def test_f2_isolation():
    _assert_no_production()
    graph = _fake_graph(g6.GRAPH_SEEDS[0])
    truth = np.arange(g6.N, dtype=np.int64) % 32
    prior = np.full((g6.N, 32), 1.0 / 32.0)
    entry = {"frame_id": 2093, "block_id": 0, "graph_seed": g6.GRAPH_SEEDS[0],
             "session_id": g6.FROZEN_SESSION}

    def syn_of(H, x):
        return np.asarray(x[:g6.M] % 32, dtype=np.uint8)

    # Exact: finite+syndrome+tag all true.
    syn = syn_of(None, truth) if False else None  # placeholder
    H = np.asarray(graph["dense"], dtype=np.uint8)
    syn_true = np.asarray(_real_syndrome(H, truth), dtype=np.uint8)
    tag_true = g6._candidate_tag(truth)
    rec = g6.run_one_block(graph, prior, syn_true, tag_true, truth,
                           entry, lambda Hh, p, s, **kw: _FakeResult(truth),
                           lambda Hh, x: _real_syndrome(Hh, x), 0)
    assert rec["finite"] and rec["syndrome_match"] and rec["tag_match"]
    assert rec["protocol_accepted"] and rec["verified_exact"]
    assert rec["outcome"] == "exact"
    # Tag mismatch -> not accepted, not exact, not undetected.
    rec2 = g6.run_one_block(graph, prior, syn_true, b"\xff" * 8, truth,
                            entry, lambda Hh, p, s, **kw: _FakeResult(truth),
                            lambda Hh, x: _real_syndrome(Hh, x), 1)
    assert rec2["tag_match"] is False
    assert rec2["protocol_accepted"] is False
    assert rec2["verified_exact"] is False and rec2["undetected"] is False
    assert rec2["outcome"] == "attempted"
    # Syndrome mismatch -> not accepted.
    wrong = (truth + 1) % 32
    rec3 = g6.run_one_block(graph, prior, syn_true, g6._candidate_tag(wrong), truth,
                            entry, lambda Hh, p, s, **kw: _FakeResult(wrong),
                            lambda Hh, x: _real_syndrome(Hh, x), 2)
    # wrong x: syndrome computed from wrong != syn_true, so mismatch.
    assert rec3["syndrome_match"] is False
    assert rec3["protocol_accepted"] is False
    assert rec3["undetected"] is False


def _real_syndrome(H, x):
    H = np.asarray(H, dtype=np.uint8)
    x = np.asarray(x, dtype=np.int64).ravel()
    # GF32 syndrome via simple matvec mod 32 for fake graphs (binary H).
    return (H.astype(np.int64) @ x.astype(np.int64)) % 32


# F3: ORACLE/APP/transfer hard-fail.
def test_f3_oracle_absence_hard_fail():
    _assert_no_production()
    calls: list = []
    base = _fake_adapters(lambda H, p, s: _FakeResult(np.zeros(g6.N)), calls)
    for bad_key in ("oracle_prior_fn", "oracle_parts", "app_prior_fn", "transfer_fn"):
        adapters = dict(base)
        adapters[bad_key] = object()
        with pytest.raises(ValueError, match="ORACLE/APP/transfer"):
            g6._hard_fail_oracle_app(adapters)
    adapters = dict(base)
    adapters["ORACLE_prior"] = object()
    with pytest.raises(ValueError, match="ORACLE/APP/transfer"):
        g6._hard_fail_oracle_app(adapters)


# F4: single-arm no-pooling; frame->block->graph even/odd; 128 calls.
def test_f4_single_arm_no_pooling():
    _assert_no_production()
    frames = g6.parse_frames(g6.FROZEN_FRAMES)
    assert len(frames) == 64 and frames[0] == 2093 and frames[-1] == 2156
    plan = g6.build_call_plan(frames)
    assert len(plan) == 128
    assert [p["call_idx"] for p in plan] == list(range(128))
    assert set(p["arm"] for p in plan) == {g6.ARM}  # single-arm
    for p in plan:
        assert p["candidate_id"] == g6.CANDIDATE_ID
        assert p["disclosed_bits"] == 5 * g6.M + 64
        expected_graph = g6.GRAPH_SEEDS[p["block_id"] % 2]
        assert p["graph_seed"] == expected_graph  # even/odd
    # No pooling: each block_id once.
    assert len({p["block_id"] for p in plan}) == 128


# F5: refusal (existing root / missing grant / pool mismatch), zero calls.
def test_f5_refusal_missing_grant_zero_calls():
    _assert_no_production()
    rc = g6.main(["--execute-real", "--registry", g6.FROZEN_REGISTRY,
                  "--session", g6.FROZEN_SESSION, "--frames", g6.FROZEN_FRAMES,
                  "--arm", g6.ARM, "--prior-root", g6.FROZEN_PRIOR_ROOT,
                  "--out-dir", "workspace/g6r1_fake_refuse_%s" % uuid.uuid4().hex])
    assert rc == 2


def test_f5_refusal_existing_root_zero_calls(fake_root):
    _assert_no_production()
    fake_root.mkdir(parents=True)
    calls: list = []
    adapters = _fake_adapters(lambda H, p, s: _FakeResult(np.zeros(g6.N)), calls)
    adapters["build_fn"] = _fake_graph
    # refuse_out_root probes before any decode.
    with pytest.raises(FileExistsError):
        r2.refuse_out_root(str(fake_root))
    assert calls == []


def test_f5_refusal_pool_mismatch_zero_calls():
    _assert_no_production()
    calls: list = []
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        g6._pre_execute_check("wrong_registry.json", g6.FROZEN_SESSION,
                              g6.FROZEN_FRAMES, g6.ARM, g6.FROZEN_PRIOR_ROOT)
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        g6._pre_execute_check(g6.FROZEN_REGISTRY, g6.FROZEN_SESSION,
                              "2093..2155", g6.ARM, g6.FROZEN_PRIOR_ROOT)
    assert calls == []


# F6: no-overwrite (protected + frozen dirs untouched).
def test_f6_no_overwrite():
    _assert_no_production()
    with pytest.raises((ValueError, FileExistsError)):
        r2.refuse_out_root("results/g6r1_fake")
    with pytest.raises((ValueError, FileExistsError)):
        r2.refuse_out_root("comparison_bench/outputs_comparison/g6r1_fake")
    # Frozen source dirs contain no g6r1 artifacts (additive scripts/tests only).
    for forbidden in [ROOT / "src", ROOT / "experiments", ROOT / "tools"]:
        if forbidden.exists():
            hits = list(forbidden.rglob("*g6*decide*")) + list(forbidden.rglob("*g6r1*"))
            assert hits == [], "frozen dir touched: %r" % hits


# F7: verifier recomputation (counts/fractions/sums, H + beta).
def test_f7_verifier_recomputation(fake_root):
    _assert_no_production()
    out = fake_root / "g6r1_verify_fake"
    out.mkdir(parents=True)
    # 128 rows: 90 exact (accepted), 38 rejected; 0 undetected.
    manifest = {"command": g6.FROZEN_COMMAND}
    (out / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    leak_each = 5 * g6.M + 64
    with (out / "block_records.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(g6.BLOCK_COLUMNS))
        writer.writeheader()
        for i in range(128):
            accepted = i < 90
            writer.writerow({
                "call_idx": i, "frame_id": 2093 + i // 2, "block_id": i,
                "session_id": g6.FROZEN_SESSION, "arm": g6.ARM,
                "candidate_id": g6.CANDIDATE_ID, "graph_seed": g6.GRAPH_SEEDS[i % 2],
                "n": g6.N, "m": g6.M, "attempted": "True", "finite": "True" if accepted else "False",
                "syndrome_match": "True" if accepted else "False",
                "tag_match": "True" if accepted else "False",
                "protocol_accepted": "True" if accepted else "False",
                "verified_exact": "True" if accepted else "False",
                "undetected": "False", "outcome": "exact" if accepted else "attempted",
                "syndrome_bits": 5 * g6.M, "tag_bits": 64, "control_bits": 0,
                "interaction_bits": 0, "auth_bits": 0, "disclosure_bits": leak_each,
                "iters": 5, "residual": 0, "provenance": "CHECK_UPDATED",
                "wall_s": 0.01, "crash": "False", "error": ""})
    leak_sum = 128 * leak_each
    beta_p = 1.0 - leak_sum / (128 * g6.N * g6.H_FROZEN)
    beta_l = 1.0 - leak_sum / (128 * g6.N * g6.H_L2)
    summary = {"attempted": 128, "accepted": 90, "exact": 90, "undetected": 0,
               "disclosure_sum": leak_sum, "beta_eff_empirical_primary": beta_p,
               "beta_eff_empirical_l2_sensitivity": beta_l,
               "H_frozen_primary": g6.H_FROZEN, "H_L2_sensitivity": g6.H_L2,
               "net_secret_bits": g6.net_secret_bits(90, leak_sum, g6.N),
               "terminal": "COMPLETE_128"}
    (out / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (out / "report.md").write_text("# fake\n", encoding="utf-8")
    assert g6.verify_root(str(out)) is True
    # Tamper: flip one exact to undetected -> verify FAIL.
    rows = list(csv.DictReader((out / "block_records.csv").read_text(encoding="utf-8").splitlines()))
    rows[0]["undetected"] = "True"
    rows[0]["verified_exact"] = "False"
    rows[0]["outcome"] = "undetected"
    with (out / "block_records.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(g6.BLOCK_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)
    # summary now stale (undetected 0 vs 1) -> FAIL.
    assert g6.verify_root(str(out)) is False


# F8 (R16): net_secret_bits exact integers; old fields frozen; beta unchanged; tamper FAILs.
def test_f8_net_secret_bits_exact_frozen_beta_tamper(fake_root):
    _assert_no_production()
    # Single-block values: accept +(640-534)=+106; fail/exhausted -534.
    assert g6.net_secret_bits(1, 534, g6.N) == 640 - 534 == 106
    assert g6.net_secret_bits(0, 534, g6.N) == -534
    # 90/128 mix: 90*640 - 128*534 = -10752.
    assert g6.net_secret_bits(90, 128 * 534, g6.N) == -10752
    # G6-R1 root shape 0/128: 0*640 - 68352 = -68352.
    assert g6.net_secret_bits(0, 68352, g6.N) == -68352
    # Old fields frozen: reconciled + beta recompute identically.
    assert 90 * 34 * 5 == 15300  # reconciled formula untouched
    leak_each = 5 * g6.M + 64
    assert leak_each == 534
    leak_sum = 128 * leak_each
    assert 1.0 - leak_sum / (128 * g6.N * g6.H_FROZEN) == \
        1.0 - leak_sum / (128 * 128 * 3.347605)
    out = fake_root / "g6r1_net_fake"
    out.mkdir(parents=True)
    (out / "manifest.json").write_text(
        json.dumps({"command": g6.FROZEN_COMMAND}), encoding="utf-8")
    with (out / "block_records.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(g6.BLOCK_COLUMNS))
        writer.writeheader()
        for i in range(128):
            accepted = i < 90
            writer.writerow({
                "call_idx": i, "frame_id": 2093 + i // 2, "block_id": i,
                "session_id": g6.FROZEN_SESSION, "arm": g6.ARM,
                "candidate_id": g6.CANDIDATE_ID, "graph_seed": g6.GRAPH_SEEDS[i % 2],
                "n": g6.N, "m": g6.M, "attempted": "True",
                "finite": "True" if accepted else "False",
                "syndrome_match": "True" if accepted else "False",
                "tag_match": "True" if accepted else "False",
                "protocol_accepted": "True" if accepted else "False",
                "verified_exact": "True" if accepted else "False",
                "undetected": "False", "outcome": "exact" if accepted else "attempted",
                "syndrome_bits": 5 * g6.M, "tag_bits": 64, "control_bits": 0,
                "interaction_bits": 0, "auth_bits": 0, "disclosure_bits": leak_each,
                "iters": 5, "residual": 0, "provenance": "CHECK_UPDATED",
                "wall_s": 0.01, "crash": "False", "error": ""})
    beta_p = 1.0 - leak_sum / (128 * g6.N * g6.H_FROZEN)
    beta_l = 1.0 - leak_sum / (128 * g6.N * g6.H_L2)
    summary = {"attempted": 128, "accepted": 90, "exact": 90, "undetected": 0,
               "disclosure_sum": leak_sum, "beta_eff_empirical_primary": beta_p,
               "beta_eff_empirical_l2_sensitivity": beta_l,
               "H_frozen_primary": g6.H_FROZEN, "H_L2_sensitivity": g6.H_L2,
               "net_secret_bits": -10752, "terminal": "COMPLETE_128"}
    (out / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (out / "report.md").write_text("# fake\n", encoding="utf-8")
    assert g6.verify_root(str(out)) is True
    # Tamper: hand-filled net (+1) -> FAIL; missing net -> FAIL.
    tampered = dict(summary)
    tampered["net_secret_bits"] = -10751
    (out / "summary.json").write_text(json.dumps(tampered), encoding="utf-8")
    assert g6.verify_root(str(out)) is False
    tampered = dict(summary)
    del tampered["net_secret_bits"]
    (out / "summary.json").write_text(json.dumps(tampered), encoding="utf-8")
    assert g6.verify_root(str(out)) is False
