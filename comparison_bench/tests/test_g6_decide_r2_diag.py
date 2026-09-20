"""G6 DECIDE R2 DIAG delta tests — FAKE fixtures only (never real pool).

Zero real-payload decoder calls; no UUID root; temp/basetemp fake roots.
Frozen ORTHOGONAL arms (main-thread ruling): A1=(uniform,90) isolates the
PRIOR effect; A2=(model_f,300) isolates the ITERATION effect. Fail-closed
admission: any other (prior,iter) combo -> PRE_EXECUTION_BLOCKED, zero calls.
Covers: uniform-prior path (loader untouched); frozen-pair threading
(damping 1.0 cold); F2 refusal set incl (uniform,300)/(model_f,90)
cross-combos; audit isolation; refusal matrix; no-overwrite; parent+triple
layout with aggregate + single-arm verify incl DIAG histograms.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import sys
import uuid
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "comparison_bench" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
RUNNER_PATH = ROOT / "scripts" / "g6_decide_r2_diag.py"


def _load_runner():
    spec = importlib.util.spec_from_file_location("g6_decide_r2_diag_test",
                                                  str(RUNNER_PATH))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["g6_decide_r2_diag_test"] = mod
    spec.loader.exec_module(mod)
    return mod


g2 = _load_runner()

PRODUCTION_ABSENT = (
    "comparison_bench.formal_ir.v35_algorithm_development",
    "comparison_bench.formal_ir.v72p2d3_gf32_contrast",
)


def _assert_no_production():
    bad = [k for k in PRODUCTION_ABSENT if k in sys.modules]
    assert bad == [], "production on fake path: %r" % bad


@pytest.fixture()
def fake_root():
    path = ROOT / "workspace" / ("g6r2_fake_%s" % uuid.uuid4().hex)
    assert not path.exists()
    assert "c4a1d2e6" not in str(path)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _fake_graph(seed):
    H = np.zeros((g2.M, g2.N), dtype=np.uint8)
    for v in range(g2.N):
        H[v % g2.M, v] = 1
    return {"arm": g2.ARM, "width": g2.N, "graph_seed": int(seed),
            "n": g2.N, "m": g2.M, "E": int(np.count_nonzero(H)),
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


def _fake_adapters(decode_behavior, calls, seen_priors=None,
                   loader_calls=None, max_iters_seen=None,
                   prior=None, with_loader=True):
    if prior is None:
        prior = np.full((1024, 1024), 1.0 / 1024.0)

    def fake_decode(H, priors, syn, **kw):
        calls.append(1)
        if seen_priors is not None:
            seen_priors.append(np.asarray(priors, dtype=np.float64).copy())
        if max_iters_seen is not None:
            max_iters_seen.append(kw.get("max_iter"))
        assert kw.get("damping_alpha") == 1.0
        assert kw.get("warm_beliefs") is None  # cold single-pass
        return decode_behavior(H, priors, syn, kw.get("max_iter"))

    def fake_syndrome(H, x):
        return np.zeros(H.shape[0], dtype=np.uint8)

    def fake_prior(root):
        if loader_calls is not None:
            loader_calls.append(1)
        return prior

    out = {"decode_fn": fake_decode, "syndrome_fn": fake_syndrome}
    if with_loader:
        out["load_prior_fn"] = fake_prior
    return out


def _fake_reader(frames):
    frames = [int(f) for f in frames]

    def reader(path, columns=None, filters=None):
        rows = []
        for fid in frames:
            for pid in range(256):
                rows.append({"frame_id": fid, "pair_idx": pid,
                             "alice_symbol": (fid + pid) % 1024,
                             "bob_symbol": (fid * 2 + pid) % 1024})
        df = pd.DataFrame(rows)
        return df[columns] if columns else df
    return reader


def _frozen_frames():
    return g2.r1.parse_frames(g2.FROZEN_FRAMES)


def _matvec_syndrome(H, x):
    H = np.asarray(H, dtype=np.uint8)
    x = np.asarray(x, dtype=np.int64).ravel()
    return (H.astype(np.int64) @ x.astype(np.int64)) % 32


# A1 uniform-prior path: decoder gets 1/32, loader bypassed entirely.
def test_a1_uniform_prior_bypass_no_loader_key(fake_root):
    _assert_no_production()
    calls: list = []
    seen: list = []
    adapters = _fake_adapters(
        lambda H, p, s, k: _FakeResult(np.zeros(g2.N)), calls,
        seen_priors=seen, with_loader=False)  # no load_prior_fn at all
    adapters["build_fn"] = _fake_graph
    bundle = g2.run_diag_arm(
        str(fake_root / "A1"), g2.FROZEN_REGISTRY, g2.FROZEN_SESSION,
        g2.FROZEN_FRAMES, g2.ARM, g2.FROZEN_PRIOR_ROOT, "uniform", 90,
        adapters=adapters, reader_override=_fake_reader(_frozen_frames()),
        frames_override=_frozen_frames())
    assert bundle["summary"]["arm_id"] == "A1"
    assert bundle["summary"]["prior_mode"] == "uniform"
    assert bundle["summary"]["attempted"] == 128
    assert len(calls) == 128  # fake calls only
    assert len(seen) == 128
    for pr in seen:
        assert pr.shape == (g2.N, 32)
        assert np.all(pr == 1.0 / 32.0)


def test_a1_uniform_prior_loader_untouched(fake_root):
    _assert_no_production()
    calls: list = []
    loader_calls: list = []
    adapters = _fake_adapters(
        lambda H, p, s, k: _FakeResult(np.zeros(g2.N)), calls,
        loader_calls=loader_calls)
    adapters["build_fn"] = _fake_graph
    bundle = g2.run_diag_arm(
        str(fake_root / "A1"), g2.FROZEN_REGISTRY, g2.FROZEN_SESSION,
        g2.FROZEN_FRAMES, g2.ARM, g2.FROZEN_PRIOR_ROOT, "uniform", 90,
        adapters=adapters, reader_override=_fake_reader(_frozen_frames()),
        frames_override=_frozen_frames())
    assert bundle["summary"]["attempted"] == 128
    assert loader_calls == []  # Model-F loader never invoked
    # A2 model_f without a loader must fail instead of silently degrading.
    adapters_noload = _fake_adapters(
        lambda H, p, s, k: _FakeResult(np.zeros(g2.N)), [],
        with_loader=False)
    adapters_noload["build_fn"] = _fake_graph
    with pytest.raises(ValueError, match="load_prior_fn"):
        g2.run_diag_arm(
            str(fake_root / "A2"), g2.FROZEN_REGISTRY, g2.FROZEN_SESSION,
            g2.FROZEN_FRAMES, g2.ARM, g2.FROZEN_PRIOR_ROOT, "model_f", 300,
            adapters=adapters_noload, reader_override=_fake_reader(_frozen_frames()),
            frames_override=_frozen_frames())


# Frozen pairs threaded: A1=(uniform,90), A2=(model_f,300); damping 1.0 cold.
def test_frozen_pairs_admitted_and_threaded(fake_root):
    _assert_no_production()
    for prior, iters, ret_iters in (("uniform", 90, 5), ("model_f", 300, 250)):
        calls: list = []
        seen_k: list = []
        adapters = _fake_adapters(
            lambda H, p, s, k: _FakeResult(np.zeros(g2.N), iters=ret_iters),
            calls, max_iters_seen=seen_k)
        adapters["build_fn"] = _fake_graph
        bundle = g2.run_diag_arm(
            str(fake_root / ("A_%s_%d" % (prior, iters))), g2.FROZEN_REGISTRY,
            g2.FROZEN_SESSION, g2.FROZEN_FRAMES, g2.ARM,
            g2.FROZEN_PRIOR_ROOT, prior, iters, adapters=adapters,
            reader_override=_fake_reader(_frozen_frames()),
            frames_override=_frozen_frames())
        assert set(seen_k) == {iters}
        assert all(int(x["max_iter"]) == iters for x in bundle["records"])
        assert all(int(x["iters"]) == ret_iters for x in bundle["records"])
        assert all(bool(x["finite"]) for x in bundle["records"])


# F2 fail-closed: cross-combos + bad values refused, zero calls.
def test_f2_cross_combos_refused_zero_calls(fake_root):
    _assert_no_production()
    # (uniform,300) confounded never-run cell; (model_f,90) R1 replica.
    for prior, iters in (("uniform", 300), ("model_f", 90)):
        calls: list = []
        adapters = _fake_adapters(
            lambda H, p, s, k: _FakeResult(np.zeros(g2.N)), calls)
        adapters["build_fn"] = _fake_graph
        with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
            g2.run_diag_arm(
                str(fake_root / ("x_%s_%d" % (prior, iters))),
                g2.FROZEN_REGISTRY, g2.FROZEN_SESSION, g2.FROZEN_FRAMES,
                g2.ARM, g2.FROZEN_PRIOR_ROOT, prior, iters,
                adapters=adapters, reader_override=_fake_reader(_frozen_frames()),
                frames_override=_frozen_frames())
        assert calls == []
        with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
            g2.validate_diag_flags(prior, iters)
        with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
            g2.arm_id_for(prior, iters)


def test_f2_bad_values_refused_zero_calls(fake_root):
    _assert_no_production()
    for bad in (45, 0, 91, 299, 301, -1, "abc", None):
        calls: list = []
        adapters = _fake_adapters(
            lambda H, p, s, k: _FakeResult(np.zeros(g2.N)), calls)
        adapters["build_fn"] = _fake_graph
        with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
            g2.run_diag_arm(
                str(fake_root / ("bad_%s" % bad)), g2.FROZEN_REGISTRY,
                g2.FROZEN_SESSION, g2.FROZEN_FRAMES, g2.ARM,
                g2.FROZEN_PRIOR_ROOT, "uniform", bad, adapters=adapters,
                reader_override=_fake_reader(_frozen_frames()),
                frames_override=_frozen_frames())
        assert calls == []
    for bad_prior in ("bogus_prior", "", None, "oracle"):
        with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
            g2.validate_diag_flags(bad_prior, 90)


# Audit isolation: decoder counter 0, loader 0, truth post-decision only.
def test_audit_isolation_zero_decoder_calls(fake_root):
    _assert_no_production()
    frames = [2093, 2094]
    r1dir = fake_root / "r1_fake"
    r1dir.mkdir(parents=True)
    (r1dir / "manifest.json").write_text("{}", encoding="utf-8")
    (r1dir / "summary.json").write_text("{}", encoding="utf-8")
    (r1dir / "report.md").write_text("# fake r1\n", encoding="utf-8")
    with (r1dir / "block_records.csv").open("w", newline="",
                                            encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(g2.r1.BLOCK_COLUMNS))
        writer.writeheader()
        i = 0
        for fid in frames:
            for pos in (0, 1):
                writer.writerow({
                    "call_idx": i, "frame_id": fid, "block_id": i,
                    "session_id": g2.FROZEN_SESSION, "arm": g2.ARM,
                    "candidate_id": g2.CANDIDATE_ID,
                    "graph_seed": g2.GRAPH_SEEDS[i % 2],
                    "n": g2.N, "m": g2.M, "attempted": "True",
                    "finite": "False", "syndrome_match": "False",
                    "tag_match": "False", "protocol_accepted": "False",
                    "verified_exact": "False", "undetected": "False",
                    "outcome": "attempted", "syndrome_bits": 5 * g2.M,
                    "tag_bits": 64, "control_bits": 0, "interaction_bits": 0,
                    "auth_bits": 0, "disclosure_bits": 5 * g2.M + 64,
                    "iters": 90, "residual": 3, "provenance": "CHECK_UPDATED",
                    "wall_s": 0.01, "crash": "False", "error": ""})
                i += 1
    calls: list = []
    loader_calls: list = []
    adapters = _fake_adapters(
        lambda H, p, s, k: _FakeResult(np.zeros(g2.N)), calls,
        loader_calls=loader_calls)
    adapters["build_fn"] = _fake_graph
    adapters["syndrome_fn"] = _matvec_syndrome
    bundle = g2.run_audit_batch(
        str(fake_root / "A0"), str(r1dir), g2.FROZEN_REGISTRY,
        g2.FROZEN_SESSION, g2.FROZEN_FRAMES, g2.ARM, adapters=adapters,
        reader_override=_fake_reader(frames), frames_override=frames)
    summary = bundle["summary"]
    assert summary["decoder_calls"] == 0
    assert summary["audit_blocks"] == 4
    assert calls == []  # truth never fed any decoder
    assert loader_calls == []  # no Model-F load on audit path
    # Independent recompute of the true-weight histogram from the generator.
    exp_weights = []
    for fid in frames:
        alice = np.array([(fid + pid) % 1024 for pid in range(256)]) % 32
        for pos in (0, 1):
            exp_weights.append(int(np.count_nonzero(alice[pos * 128:(pos + 1) * 128])))
    exp_hist = {str(k): v for k, v in sorted(Counter(exp_weights).items())}
    assert summary["diag_histograms"]["true_weight_hist"] == exp_hist
    assert [int(x["true_weight"]) for x in bundle["records"]] == exp_weights
    # Residual-weight recompute matches the kernel on truth.
    for rec in bundle["records"]:
        H = np.asarray(_fake_graph(rec["graph_seed"])["dense"], dtype=np.uint8)
        fid, bid = int(rec["frame_id"]), int(rec["block_id"])
        alice = np.array([(fid + pid) % 1024 for pid in range(256)]) % 32
        truth = alice[(bid % 2) * 128:(bid % 2 + 1) * 128]
        assert int(rec["residual"]) == int(np.count_nonzero(_matvec_syndrome(H, truth)))


# Refusal matrix: missing grant rc2, existing root, pool/graph/flag mismatch.
def test_refusal_missing_grant_zero_calls(fake_root):
    _assert_no_production()
    out = fake_root / "A1"
    rc = g2.main(["--execute-real", "--registry", g2.FROZEN_REGISTRY,
                  "--session", g2.FROZEN_SESSION, "--frames", g2.FROZEN_FRAMES,
                  "--arm", g2.ARM, "--prior-root", g2.FROZEN_PRIOR_ROOT,
                  "--prior-mode", "uniform", "--max-iter", "90",
                  "--out-dir", str(out)])
    assert rc == 2
    assert not out.exists()
    rc = g2.main(["--audit-only", "--r1-root", str(fake_root / "r1"),
                  "--registry", g2.FROZEN_REGISTRY, "--session",
                  g2.FROZEN_SESSION, "--frames", g2.FROZEN_FRAMES,
                  "--arm", g2.ARM, "--out-dir", str(fake_root / "A0")])
    assert rc == 2
    assert not (fake_root / "A0").exists()


def test_refusal_existing_root_zero_calls(fake_root):
    _assert_no_production()
    calls: list = []
    adapters = _fake_adapters(
        lambda H, p, s, k: _FakeResult(np.zeros(g2.N)), calls)
    adapters["build_fn"] = _fake_graph
    existing = fake_root / "A2"
    existing.mkdir(parents=True)
    with pytest.raises(FileExistsError):
        g2.run_diag_arm(
            str(existing), g2.FROZEN_REGISTRY, g2.FROZEN_SESSION,
            g2.FROZEN_FRAMES, g2.ARM, g2.FROZEN_PRIOR_ROOT, "model_f", 300,
            adapters=adapters, reader_override=_fake_reader(_frozen_frames()),
            frames_override=_frozen_frames())
    with pytest.raises(FileExistsError):
        g2.run_audit_batch(
            str(existing), str(fake_root / "r1"), g2.FROZEN_REGISTRY,
            g2.FROZEN_SESSION, g2.FROZEN_FRAMES, g2.ARM, adapters=adapters,
            reader_override=_fake_reader([2093]),
            frames_override=[2093],
            r1_records_override=[{"frame_id": 2093, "block_id": 0,
                                  "graph_seed": g2.GRAPH_SEEDS[0],
                                  "residual": 0}])
    assert calls == []


def test_refusal_mismatch_matrix_zero_calls(fake_root):
    _assert_no_production()
    calls: list = []
    adapters = _fake_adapters(
        lambda H, p, s, k: _FakeResult(np.zeros(g2.N)), calls)
    adapters["build_fn"] = _fake_graph
    base = ["--execute-real", "--execution-authorized",
            "--registry", g2.FROZEN_REGISTRY, "--session", g2.FROZEN_SESSION,
            "--frames", g2.FROZEN_FRAMES, "--arm", g2.ARM,
            "--prior-root", g2.FROZEN_PRIOR_ROOT,
            "--prior-mode", "uniform", "--max-iter", "90"]
    # Pool/flag mismatch variants refuse before any read/bind/call.
    for override in (["--registry", "wrong_registry.json"],
                     ["--frames", "2093..2155"],
                     ["--prior-mode", "oracle"],
                     ["--max-iter", "45"],
                     ["--max-iter", "300"]):  # (uniform,300) cross-combo
        argv = list(base) + ["--out-dir",
                             str(fake_root / ("ref_%s" % uuid.uuid4().hex))]
        for flag, val in zip(override[::2], override[1::2]):
            idx = argv.index(flag)
            argv[idx + 1] = val
        rc = g2.main(argv, adapters_override=adapters)
        assert rc == 2
    assert calls == []
    # Graph mismatch: seed outside the frozen pair.
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        g2.build_graph(999)


# No-overwrite: protected dirs + frozen source dirs untouched.
def test_no_overwrite_protected_and_frozen():
    _assert_no_production()
    import comparison_bench.formal_ir.v72p2d10_mixed_degree_l1 as d10r2
    with pytest.raises((ValueError, FileExistsError)):
        d10r2.refuse_out_root("results/g6r2_fake")
    with pytest.raises((ValueError, FileExistsError)):
        d10r2.refuse_out_root("comparison_bench/outputs_comparison/g6r2_fake")
    for forbidden in [ROOT / "src", ROOT / "experiments", ROOT / "tools"]:
        if forbidden.exists():
            hits = list(forbidden.rglob("*g6r2*")) + \
                list(forbidden.rglob("*g6*diag*"))
            assert hits == [], "frozen dir touched: %r" % hits


# Parent+triple layout helpers (frozen structure, no arm-level manifests).
def _make_decode_records(arm_id: str, n_exact: int) -> list[dict]:
    prior, iters = (g2.FROZEN_A1 if arm_id == "A1" else g2.FROZEN_A2)
    leak_each = 5 * g2.M + 64
    rows = []
    for i in range(128):
        accepted = i < n_exact
        rows.append({
            "call_idx": i, "frame_id": 2093 + i // 2, "block_id": i,
            "session_id": g2.FROZEN_SESSION, "arm": g2.ARM,
            "candidate_id": g2.CANDIDATE_ID,
            "graph_seed": g2.GRAPH_SEEDS[i % 2],
            "n": g2.N, "m": g2.M, "attempted": True,
            "finite": accepted, "syndrome_match": accepted,
            "tag_match": accepted, "protocol_accepted": accepted,
            "verified_exact": accepted, "undetected": False,
            "outcome": "exact" if accepted else "attempted",
            "syndrome_bits": 5 * g2.M, "tag_bits": 64, "control_bits": 0,
            "interaction_bits": 0, "auth_bits": 0,
            "disclosure_bits": leak_each, "iters": iters,
            "residual": 0, "provenance": "CHECK_UPDATED",
            "wall_s": 0.01, "crash": False, "error": "",
            "arm_id": arm_id, "prior_mode": prior, "max_iter": iters,
            "true_weight": -1, "r1_residual": -1})
    return rows


def _make_audit_records() -> list[dict]:
    rows = []
    for i in range(128):
        rows.append({
            "call_idx": i, "frame_id": 2093 + i // 2, "block_id": i,
            "session_id": g2.FROZEN_SESSION, "arm": g2.ARM,
            "candidate_id": g2.CANDIDATE_ID,
            "graph_seed": g2.GRAPH_SEEDS[i % 2],
            "n": g2.N, "m": g2.M, "attempted": False,
            "finite": False, "syndrome_match": False,
            "tag_match": False, "protocol_accepted": False,
            "verified_exact": False, "undetected": False,
            "outcome": "audit", "syndrome_bits": 0, "tag_bits": 0,
            "control_bits": 0, "interaction_bits": 0, "auth_bits": 0,
            "disclosure_bits": 0, "iters": -1,
            "residual": i % 3, "provenance": "AUDIT_POST_DECISION",
            "wall_s": 0.0, "crash": False, "error": "",
            "arm_id": "A0", "prior_mode": "none", "max_iter": -1,
            "true_weight": 10 + (i % 5), "r1_residual": 0})
    return rows


def _write_parent_triple(parent: Path):
    extra = {"registry": g2.FROZEN_REGISTRY, "session_id": g2.FROZEN_SESSION,
             "frames": g2.FROZEN_FRAMES, "arm": g2.ARM,
             "candidate_id": g2.CANDIDATE_ID,
             "prior_root": g2.FROZEN_PRIOR_ROOT}
    b1 = g2._decode_bundle(parent / "A1", extra, _make_decode_records("A1", 100),
                           4, "A1", "uniform", 90)
    b2 = g2._decode_bundle(parent / "A2", extra, _make_decode_records("A2", 12),
                           4, "A2", "model_f", 300)
    arecs = _make_audit_records()
    true_hist = {str(k): v for k, v in
                 sorted(Counter(int(x["true_weight"]) for x in arecs).items())}
    syn_hist = {str(k): v for k, v in
                sorted(Counter(int(x["residual"]) for x in arecs).items())}
    b0 = {"resolved": parent / "A0", "manifest": {},
          "records": arecs,
          "summary": {
              "schema": "g6_decide_r2_diag_summary_v1", "mode": "audit",
              "terminal": "AUDIT_COMPLETE", "arm_id": "A0",
              "prior_mode": "none", "max_iter": None,
              "attempted": 0, "accepted": 0, "exact": 0, "undetected": 0,
              "disclosure_sum": 0, "decoder_calls": 0, "audit_blocks": 128,
              "diag_histograms": {"true_weight_hist": true_hist,
                                  "truth_syn_weight_hist": syn_hist},
              "out_root": str(parent / "A0")}}
    return g2.write_diag_root(str(parent), {"A1": b1, "A2": b2, "A0": b0})


def test_verifier_parent_and_single_pass(fake_root):
    _assert_no_production()
    parent = fake_root / "triple"
    psum = _write_parent_triple(parent)
    assert psum["terminal"] == "COMPLETE_256_AUDITED"
    assert psum["attempted"] == 256
    assert psum["accepted"] == 112 and psum["exact"] == 112
    assert psum["undetected"] == 0
    assert psum["decoder_calls"] == 256
    assert psum["audit_blocks"] == 128
    assert set(psum["per_arm"]) == {"A1", "A2", "A0"}
    # Frozen layout: parent manifest+summary; arms CSV+summary(+report).
    assert (parent / "manifest.json").is_file()
    assert (parent / "summary.json").is_file()
    for arm in ("A1", "A2", "A0"):
        assert (parent / arm / "block_records.csv").is_file()
        assert (parent / arm / "summary.json").is_file()
        assert not (parent / arm / "manifest.json").exists()
    pman = json.loads((parent / "manifest.json").read_text(encoding="utf-8"))
    assert pman["frozen_argv"] == {"A1": g2.FROZEN_COMMAND_A1,
                                   "A2": g2.FROZEN_COMMAND_A2,
                                   "A0": g2.FROZEN_COMMAND_A0,
                                   "verify": g2.FROZEN_COMMAND_VERIFY}
    assert g2.verify_diag_root(str(parent)) is True
    assert g2.verify_diag_root(str(parent / "A1")) is True
    assert g2.verify_diag_root(str(parent / "A2")) is True
    assert g2.verify_diag_root(str(parent / "A0")) is True


def test_verifier_tamper_fails(fake_root):
    _assert_no_production()
    parent = fake_root / "triple"

    def _rewrite():
        shutil.rmtree(parent, ignore_errors=True)
        _write_parent_triple(parent)

    _rewrite()
    # Stale honest counts.
    summary_path = parent / "A1" / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["exact"] = 99
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    assert g2.verify_diag_root(str(parent)) is False
    assert g2.verify_diag_root(str(parent / "A1")) is False
    _rewrite()
    # Dropped DIAG histogram bin.
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["diag_histograms"] = {"residual_hist": {"1": 128}}
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    assert g2.verify_diag_root(str(parent)) is False
    _rewrite()
    # Undetected merged without summary update.
    csv_path = parent / "A2" / "block_records.csv"
    rows = list(csv.DictReader(csv_path.read_text(encoding="utf-8").splitlines()))
    rows[0]["undetected"] = "True"
    rows[0]["verified_exact"] = "False"
    rows[0]["outcome"] = "undetected"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(g2.BLOCK_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)
    assert g2.verify_diag_root(str(parent)) is False
    _rewrite()
    # A0 dishonest decoder count.
    a0_summary = parent / "A0" / "summary.json"
    a0 = json.loads(a0_summary.read_text(encoding="utf-8"))
    a0["decoder_calls"] = 1
    a0_summary.write_text(json.dumps(a0), encoding="utf-8")
    assert g2.verify_diag_root(str(parent)) is False
    _rewrite()
    # Stale parent aggregate.
    psum_path = parent / "summary.json"
    psum = json.loads(psum_path.read_text(encoding="utf-8"))
    psum["attempted"] = 255
    psum_path.write_text(json.dumps(psum), encoding="utf-8")
    assert g2.verify_diag_root(str(parent)) is False
    _rewrite()
    # Parent frozen_argv tamper.
    pman_path = parent / "manifest.json"
    pman = json.loads(pman_path.read_text(encoding="utf-8"))
    pman["frozen_argv"]["verify"] = "tampered"
    pman_path.write_text(json.dumps(pman), encoding="utf-8")
    assert g2.verify_diag_root(str(parent)) is False
    # Missing arm subdir breaks the aggregate.
    shutil.rmtree(parent / "A0")
    assert g2.verify_diag_root(str(parent)) is False


# F1 structure end-to-end on FAKE: real run paths -> parent assembly -> verify.
def test_parent_assembled_from_fake_runs(fake_root):
    _assert_no_production()
    frames = _frozen_frames()
    a1_ad = _fake_adapters(
        lambda H, p, s, k: _FakeResult(np.zeros(g2.N)), [],
        with_loader=False)
    a1_ad["build_fn"] = _fake_graph
    a2_ad = _fake_adapters(
        lambda H, p, s, k: _FakeResult(np.zeros(g2.N)), [])
    a2_ad["build_fn"] = _fake_graph
    parent = fake_root / "diag"
    b1 = g2.run_diag_arm(
        str(parent / "A1"), g2.FROZEN_REGISTRY, g2.FROZEN_SESSION,
        g2.FROZEN_FRAMES, g2.ARM, g2.FROZEN_PRIOR_ROOT, "uniform", 90,
        adapters=a1_ad, reader_override=_fake_reader(frames),
        frames_override=frames)
    b2 = g2.run_diag_arm(
        str(parent / "A2"), g2.FROZEN_REGISTRY, g2.FROZEN_SESSION,
        g2.FROZEN_FRAMES, g2.ARM, g2.FROZEN_PRIOR_ROOT, "model_f", 300,
        adapters=a2_ad, reader_override=_fake_reader(frames),
        frames_override=frames)
    r1rows = [{"frame_id": 2093 + (i // 2), "block_id": i,
               "graph_seed": g2.GRAPH_SEEDS[i % 2], "residual": 0}
              for i in range(4)]
    a0_ad = _fake_adapters(
        lambda H, p, s, k: _FakeResult(np.zeros(g2.N)), [])
    a0_ad["build_fn"] = _fake_graph
    a0_ad["syndrome_fn"] = _matvec_syndrome
    b0 = g2.run_audit_batch(
        str(parent / "A0"), str(fake_root / "r1"), g2.FROZEN_REGISTRY,
        g2.FROZEN_SESSION, g2.FROZEN_FRAMES, g2.ARM, adapters=a0_ad,
        reader_override=_fake_reader([2093, 2094]), frames_override=[2093, 2094],
        r1_records_override=r1rows)
    psum = g2.write_diag_root(str(parent), {"A1": b1, "A2": b2, "A0": b0})
    assert psum["terminal"] == "COMPLETE_256_AUDITED"
    assert psum["attempted"] == 256 and psum["audit_blocks"] == 4
    assert g2.verify_diag_root(str(parent)) is True
    for arm in ("A1", "A2", "A0"):
        assert g2.verify_diag_root(str(parent / arm)) is True


# Profile: A1 128 uniform/90 + A2 128 model_f/300, budgets ok, zero calls.
def test_profile_fake_pool_budgets_zero_calls():
    _assert_no_production()
    prof = g2.profile_only()
    assert prof["admitted"] == 2 and prof["total_graphs"] == 2
    assert prof["arms"]["A1"]["calls"] == 128
    assert prof["arms"]["A2"]["calls"] == 128
    assert prof["arms"]["A1"]["prior_mode"] == "uniform"
    assert prof["arms"]["A2"]["prior_mode"] == "model_f"
    assert prof["arms"]["A1"]["max_iter"] == 90
    assert prof["arms"]["A2"]["max_iter"] == 300
    assert prof["plan_calls"] == 256
    assert prof["plan_order"] == "frame->block->graph even/odd"
    assert prof["budgets"]["scientific_calls"] == 256
    assert prof["budgets"]["sci_ceiling"] == 256
    assert prof["budgets"]["setup_calls"] <= 8
    assert prof["budget_ok"] is True
    assert prof["decoder_calls"] == 0
    assert prof["model_f_loads"] == 0
    assert prof["real_pool_reads"] == 0
    assert prof["future_root_absent"] is True
    assert set(prof["frozen_argv"]) == {"A1", "A2", "A0", "verify"}
