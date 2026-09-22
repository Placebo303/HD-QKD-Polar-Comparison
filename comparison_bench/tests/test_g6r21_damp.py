"""R21 DAMP ladder tests — FAKE fixtures only (never real pool).

R21b readiness: zero real-payload decoder calls; no UUID root; temp fake
roots; the real S1 CSV is touched READ-ONLY (F/sha only, never symbols)
for the honest-baseline import check. Covers: frozen pins (damping
ladder/eps/staged lineage/graphs/budgets/gate); damping kwarg threaded
verbatim per arm; invalid damping refused zero-calls; cold-1.0
byte-identical vs S1 path outputs; stage-m (S0-only) enforced both arms;
UNDETECTED_STOP both arms; refusal/no-overwrite/verifier incl net_secret
+ isolation + damping/lift tamper FAILs; profile-only per arm.
"""
from __future__ import annotations

import csv
import hashlib
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
RUNNER_PATH = ROOT / "scripts" / "g6r21_damp.py"


def _load_runner():
    spec = importlib.util.spec_from_file_location("g6r21_damp_test",
                                                  str(RUNNER_PATH))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["g6r21_damp_test"] = mod
    spec.loader.exec_module(mod)
    return mod


r21 = _load_runner()
s1mod = sys.modules["g6s1_shift"]
import comparison_bench.formal_ir.v72p2d10_mixed_degree_l1 as r2  # noqa: E402
from comparison_bench.formal_ir.v72p2d5_shift_prior import (  # noqa: E402
    DEFAULT_EPS,
    build_shift_prior_concentration,
)

PRODUCTION_ABSENT = (
    "comparison_bench.formal_ir.v35_algorithm_development",
    "comparison_bench.formal_ir.v72p2d3_gf32_contrast",
)


def _assert_no_new_production(before):
    bad = [k for k in PRODUCTION_ABSENT
           if k in sys.modules and k not in before]
    assert bad == [], "production on fake path: %r" % bad


@pytest.fixture()
def prod_guard():
    return set(sys.modules)


@pytest.fixture()
def fake_root():
    path = ROOT / "workspace" / ("g6r21_fake_%s" % uuid.uuid4().hex)
    assert not path.exists()
    assert "9f43bc04" not in str(path) and "8dbeced5" not in str(path)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _fake_graph(seed):
    H = np.zeros((r21.M, r21.N), dtype=np.uint8)
    for v in range(r21.N):
        H[v % r21.M, v] = 1
    return {"arm": r21.ARM, "width": r21.N, "graph_seed": int(seed),
            "n": r21.N, "m": r21.M, "E": int(np.count_nonzero(H)),
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


def _fake_gate(frames):
    def gate(registry_path, session_id, frames_spec, arm, prior_root):
        assert str(registry_path) == r21.FROZEN_REGISTRY
        assert str(session_id) == r21.FROZEN_SESSION
        assert str(frames_spec) == r21.FROZEN_FRAMES
        assert str(arm) == r21.ARM
        assert str(prior_root) == r21.FROZEN_PRIOR_ROOT
        return list(frames)
    return gate


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


def _fake_adapters(decode_calls, damp_seen, script):
    rng = np.random.default_rng(99)
    fake_counts = rng.integers(0, 5, size=(1024, 1024)).astype(float) + 1.0
    fake_pf = build_shift_prior_concentration(fake_counts, r21.FROZEN_EPS)
    plan = list(script)

    def fake_decode(H, priors, syn, **kw):
        decode_calls.append(1)
        damp_seen.append(kw.get("damping_alpha"))
        assert kw.get("max_iter") == 90
        assert kw.get("warm_beliefs") is None  # cold single-pass
        assert priors.shape == (128, 32)
        action = plan.pop(0)
        if action == "hit":
            return _FakeResult(np.zeros(128, dtype=np.int64))
        return _FakeResult(np.ones(128, dtype=np.int64))

    def fake_syndrome(H, x):
        return np.zeros(H.shape[0], dtype=np.uint8)

    def fake_prior(root):
        return np.asarray(fake_pf)

    def fake_build(seed):
        assert int(seed) in r21.GRAPH_SEEDS
        return _fake_graph(int(seed))

    return {"decode_fn": fake_decode, "syndrome_fn": fake_syndrome,
            "load_prior_fn": fake_prior, "build_fn": fake_build}


def _run_arm(damping, out_dir, monkeypatch, script):
    frames = r21.parse_frames(r21.FROZEN_FRAMES)
    monkeypatch.setattr(r21, "_pre_execute_check", _fake_gate(frames))
    decode_calls: list = []
    damp_seen: list = []
    bundle = r21.run_authorized_batch(
        str(out_dir), r21.FROZEN_REGISTRY, r21.FROZEN_SESSION,
        r21.FROZEN_FRAMES, r21.ARM, r21.FROZEN_PRIOR_ROOT,
        r21.BASELINE_ROOT, damping,
        adapters=_fake_adapters(decode_calls, damp_seen, script),
        reader_override=_fake_reader_factory(frames))
    return bundle, decode_calls, damp_seen


# Frozen pins: ladder, eps, staged lineage, graphs, budgets, gate, roots.
def test_pins_ladder_eps_lineage_graphs_budgets_gate(prod_guard):
    _assert_no_new_production(prod_guard)
    assert r21.ALLOWED_DAMPING == (0.5, 0.8, 1.0)
    assert r21.DAMPING_ARMS == (0.5, 0.8)
    assert r21.COLD_DEFAULT_DAMPING == 1.0
    assert r21.FROZEN_EPS == 1e-4 and DEFAULT_EPS == 1e-4
    assert r21.PRIOR_MODE == "shift-delta-eps1e-04"
    assert r21.STAGE_ID == "S0" and r21.STAGE_M == 100
    assert r21.GRAPH_SEEDS == (2026094720, 2026094721)
    assert r21.TAG_BITS == 64
    assert r21.final_prefix_disclosure(100) == 564
    assert r21.SCI_CEILING == 256 and r21.SETUP_CEILING == 8
    assert r21.LIFT_GATE == 6
    assert r21.BASELINE_ROOT.endswith(
        "workspace/g6s1_shift_4105cfc2-3bbb-444a-9283-31403d43b7ff")
    assert set(r21.FUTURE_ROOTS) == {0.5, 0.8}
    for rel in r21.FUTURE_ROOTS.values():
        assert rel.startswith("workspace/g6r21_damp_")
        assert not (ROOT / rel).exists()  # UUID roots absent, never created


# Damping kwarg threaded verbatim per arm (0.5 / 0.8 / 1.0).
@pytest.mark.parametrize("damping", [0.5, 0.8, 1.0])
def test_damping_kwarg_verbatim_per_arm(fake_root, monkeypatch, prod_guard,
                                        damping):
    _assert_no_new_production(prod_guard)
    out = fake_root / ("kw_%s" % str(damping).replace(".", ""))
    bundle, calls, seen = _run_arm(damping, out, monkeypatch, ["hit"] * 128)
    assert len(calls) == 128 and all(d == damping for d in seen)
    assert bundle["summary"]["damping"] == damping
    assert bundle["manifest"]["decoder"]["damping_alpha"] == damping
    assert bundle["summary"]["cold_default"] == (damping == 1.0)


# Invalid damping refused with zero calls (programmatic + CLI).
@pytest.mark.parametrize("bad", [0.3, 1.5, None, True])
def test_invalid_damping_refused_zero_calls(fake_root, prod_guard, bad):
    _assert_no_new_production(prod_guard)
    with pytest.raises(ValueError, match="not an allowed arm"):
        r21.validate_damping(bad)
    decode_calls: list = []
    with pytest.raises(ValueError, match="not an allowed arm"):
        r21.run_authorized_batch(
            str(fake_root / "nodir"), r21.FROZEN_REGISTRY, r21.FROZEN_SESSION,
            r21.FROZEN_FRAMES, r21.ARM, r21.FROZEN_PRIOR_ROOT,
            r21.BASELINE_ROOT, bad,
            adapters=_fake_adapters(decode_calls, [], ["hit"] * 128))
    assert decode_calls == []


def test_invalid_damping_cli_refused(prod_guard):
    _assert_no_new_production(prod_guard)
    with pytest.raises(SystemExit) as exc:
        r21.main(["--execute-real", "--damping", "0.3",
                  "--registry", r21.FROZEN_REGISTRY,
                  "--session", r21.FROZEN_SESSION,
                  "--frames", r21.FROZEN_FRAMES, "--arm", r21.ARM,
                  "--prior-root", r21.FROZEN_PRIOR_ROOT,
                  "--out-dir", "workspace/g6r21_fake_cli_%s" % uuid.uuid4().hex])
    assert exc.value.code == 2


# Cold-1.0 byte-identical vs S1 path outputs (same FAKE fixtures).
def test_cold_10_byte_identical_vs_s1(fake_root, monkeypatch, prod_guard):
    _assert_no_new_production(prod_guard)
    frames = r21.parse_frames(r21.FROZEN_FRAMES)
    gate = _fake_gate(frames)
    monkeypatch.setattr(r21, "_pre_execute_check", gate)
    monkeypatch.setattr(s1mod, "_pre_execute_check", gate)
    reader = _fake_reader_factory(frames)
    c1: list = []
    s1seen: list = []
    s1bundle = s1mod.run_authorized_batch(
        str(fake_root / "s1ref"), s1mod.FROZEN_REGISTRY, s1mod.FROZEN_SESSION,
        s1mod.FROZEN_FRAMES, s1mod.ARM, s1mod.FROZEN_PRIOR_ROOT,
        adapters=_fake_adapters(c1, s1seen, ["hit"] * 128),
        reader_override=reader)
    c2: list = []
    r21seen: list = []
    r21bundle = r21.run_authorized_batch(
        str(fake_root / "r21cold"), r21.FROZEN_REGISTRY, r21.FROZEN_SESSION,
        r21.FROZEN_FRAMES, r21.ARM, r21.FROZEN_PRIOR_ROOT,
        r21.BASELINE_ROOT, 1.0,
        adapters=_fake_adapters(c2, r21seen, ["hit"] * 128),
        reader_override=reader)
    assert len(c1) == len(c2) == 128
    assert all(d == 1.0 for d in s1seen) and all(d == 1.0 for d in r21seen)
    assert len(s1bundle["records"]) == len(r21bundle["records"]) == 128
    skip = {"wall_s"}
    for a, b in zip(s1bundle["records"], r21bundle["records"]):
        assert set(a) == set(b)
        for k in a:
            if k not in skip:
                assert a[k] == b[k], "field %s differs" % k
    for k in ("attempted", "accepted", "exact", "undetected",
              "disclosure_sum", "net_secret_bits", "prior_mode", "prior_eps",
              "beta_eff_empirical_primary",
              "beta_eff_empirical_l2_sensitivity"):
        assert s1bundle["summary"][k] == r21bundle["summary"][k]


# Stage-m gate: S0-only execution enforced on both new arms.
@pytest.mark.parametrize("damping", [0.5, 0.8])
def test_stage_m_enforced_both_arms(fake_root, monkeypatch, prod_guard,
                                     damping):
    _assert_no_new_production(prod_guard)
    out = fake_root / ("stagem_%s" % str(damping).replace(".", ""))
    bundle, calls, _ = _run_arm(damping, out, monkeypatch, ["hit"] * 128)
    assert len(calls) == 128
    for rec in bundle["records"]:
        assert int(rec["m"]) == 100
        assert int(rec["disclosure_bits"]) == 564
    assert bundle["summary"]["terminal"] == "COMPLETE_128"
    assert r21.check_stage_m(100) == 100
    with pytest.raises(ValueError, match="S0 only"):
        r21.check_stage_m(108)
    with pytest.raises(ValueError, match="S0 only"):
        r21.check_stage_m(120)
    # Non-S0 graph refused before any decode call.
    bad_graph = _fake_graph(r21.GRAPH_SEEDS[0])
    bad_graph["m"] = 120
    with pytest.raises(ValueError, match="S0 only"):
        r21.run_one_block_damp(
            bad_graph, np.full((128, 32), 1.0 / 32.0),
            np.zeros(100, dtype=np.uint8), b"\x00" * 8,
            np.zeros(128, dtype=np.int64),
            {"frame_id": 2123, "block_id": 0,
             "graph_seed": r21.GRAPH_SEEDS[0]},
            lambda *a, **k: (_ for _ in ()).throw(AssertionError("called")),
            lambda H, x: np.zeros(100, dtype=np.uint8),
            lambda x: b"\x00" * 8, 0, damping)


# UNDETECTED_STOP on both new arms (retained prefix, fail-closed).
@pytest.mark.parametrize("damping", [0.5, 0.8])
def test_undetected_stop_both_arms(fake_root, monkeypatch, prod_guard,
                                    damping):
    _assert_no_new_production(prod_guard)
    frames = r21.parse_frames(r21.FROZEN_FRAMES)
    monkeypatch.setattr(r21, "_pre_execute_check", _fake_gate(frames))
    decode_calls: list = []
    damp_seen: list = []
    script = ["hit"] * 3 + ["miss"] + ["hit"] * 200
    adapters = _fake_adapters(decode_calls, damp_seen, script)
    adapters["tag_fn"] = lambda vec: b"CONSTANT"  # noqa: E731  lying tag
    out = fake_root / ("undet_%s" % str(damping).replace(".", ""))
    bundle = r21.run_authorized_batch(
        str(out), r21.FROZEN_REGISTRY, r21.FROZEN_SESSION,
        r21.FROZEN_FRAMES, r21.ARM, r21.FROZEN_PRIOR_ROOT,
        r21.BASELINE_ROOT, damping, adapters=adapters,
        reader_override=_fake_reader_factory(frames))
    assert bundle["summary"]["terminal"] == "UNDETECTED_STOP"
    assert bundle["summary"]["attempted"] == 4
    assert bundle["summary"]["undetected"] == 1
    last = bundle["records"][-1]
    assert last["undetected"] is True and last["verified_exact"] is False
    assert last["protocol_accepted"] is True  # never merged, still isolated
    assert len(bundle["records"]) == 4  # retained, nothing after STOP
    assert all(d == damping for d in damp_seen)


# Refusal matrix: missing grant per arm / existing root / pool mismatch.
@pytest.mark.parametrize("damping", [0.5, 0.8, 1.0])
def test_refusal_missing_grant_zero_calls(prod_guard, damping):
    _assert_no_new_production(prod_guard)
    out = "workspace/g6r21_fake_refuse_%s" % uuid.uuid4().hex
    rc = r21.main(["--execute-real", "--damping", str(damping),
                   "--registry", r21.FROZEN_REGISTRY,
                   "--session", r21.FROZEN_SESSION,
                   "--frames", r21.FROZEN_FRAMES, "--arm", r21.ARM,
                   "--prior-root", r21.FROZEN_PRIOR_ROOT,
                   "--baseline-root", r21.BASELINE_ROOT,
                   "--out-dir", out])
    assert rc == 2
    assert not (ROOT / out).exists()


def test_refusal_existing_root_zero_calls(fake_root, prod_guard):
    _assert_no_new_production(prod_guard)
    existing = fake_root / "exists"
    existing.mkdir(parents=True)
    decode_calls: list = []
    with pytest.raises(FileExistsError):
        r21.run_authorized_batch(
            str(existing), r21.FROZEN_REGISTRY, r21.FROZEN_SESSION,
            r21.FROZEN_FRAMES, r21.ARM, r21.FROZEN_PRIOR_ROOT,
            r21.BASELINE_ROOT, 0.5,
            adapters=_fake_adapters(decode_calls, [], ["hit"] * 128))
    assert decode_calls == []


def test_refusal_pool_mismatch_zero_calls(prod_guard):
    _assert_no_new_production(prod_guard)
    decode_calls: list = []
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        r21._pre_execute_check("wrong_registry.json", r21.FROZEN_SESSION,
                               r21.FROZEN_FRAMES, r21.ARM, r21.FROZEN_PRIOR_ROOT)
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        r21._pre_execute_check(r21.FROZEN_REGISTRY, "WRONG_SESSION",
                               r21.FROZEN_FRAMES, r21.ARM, r21.FROZEN_PRIOR_ROOT)
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        r21._pre_execute_check(r21.FROZEN_REGISTRY, r21.FROZEN_SESSION,
                               "2123..2185", r21.ARM, r21.FROZEN_PRIOR_ROOT)
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        r21._pre_execute_check(r21.FROZEN_REGISTRY, r21.FROZEN_SESSION,
                               r21.FROZEN_FRAMES, "WRONG_ARM",
                               r21.FROZEN_PRIOR_ROOT)
    with pytest.raises(ValueError, match="PRE_EXECUTION_BLOCKED"):
        r21._pre_execute_check(r21.FROZEN_REGISTRY, r21.FROZEN_SESSION,
                               r21.FROZEN_FRAMES, r21.ARM, "workspace/wrong_prior")
    assert decode_calls == []


# Honest-baseline import: fake F counting + real S1 F=2 + byte-identical.
def _write_fake_baseline(out, accepted_n, undet_n=0):
    out.mkdir(parents=True, exist_ok=True)
    with (out / "block_records.csv").open("w", newline="",
                                          encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(r21.BLOCK_COLUMNS))
        writer.writeheader()
        for i in range(128):
            accepted = i < accepted_n
            undet = i >= 128 - undet_n
            writer.writerow({
                "call_idx": i, "frame_id": 2123 + i // 2, "block_id": i,
                "protocol_accepted": "True" if (accepted or undet) else "False",
                "verified_exact": "True" if accepted else "False",
                "undetected": "True" if undet else "False"})


def test_baseline_import_fake_and_real(prod_guard, fake_root):
    _assert_no_new_production(prod_guard)
    base = fake_root / "fakebase"
    _write_fake_baseline(base, 84)
    info = r21.load_fixed_baseline(str(base))
    assert info["F"] == 84 and info["rows"] == 128
    _write_fake_baseline(fake_root / "fakeundet", 84, undet_n=1)
    with pytest.raises(ValueError, match="undetected"):
        r21.load_fixed_baseline(str(fake_root / "fakeundet"))
    _write_fake_baseline(fake_root / "fakemerge", 84)
    rows = list(csv.DictReader(
        (fake_root / "fakemerge" / "block_records.csv").read_text(
            encoding="utf-8").splitlines()))
    rows[90]["protocol_accepted"] = "True"  # accepted != exact
    with (fake_root / "fakemerge" / "block_records.csv").open(
            "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(r21.BLOCK_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match="accepted != exact"):
        r21.load_fixed_baseline(str(fake_root / "fakemerge"))
    real = r21.load_fixed_baseline(r21.BASELINE_ROOT)  # read-only
    assert real["F"] == 2 and real["rows"] == 128  # S1-shift 2/128


def test_baseline_byte_identical_post_run(fake_root, monkeypatch, prod_guard):
    _assert_no_new_production(prod_guard)
    before = hashlib.sha256(
        (ROOT / r21.BASELINE_ROOT / "block_records.csv").read_bytes()
        ).hexdigest()
    out = fake_root / "postident"
    bundle, calls, _ = _run_arm(0.5, out, monkeypatch, ["hit"] * 128)
    after = hashlib.sha256(
        (ROOT / r21.BASELINE_ROOT / "block_records.csv").read_bytes()
        ).hexdigest()
    assert before == after == bundle["manifest"]["baseline"]["sha256"]
    assert bundle["summary"]["baseline_F"] == 2
    assert bundle["summary"]["paired_lift"] == 126
    assert bundle["summary"]["lift_gate_pass"] is True
    r21.write_batch_root(bundle)
    assert r21.verify_root(str(out), 0.5) is True


# No-overwrite: protected dirs + frozen dirs + prior roots + UUID absence.
def test_no_overwrite_roots(prod_guard):
    _assert_no_new_production(prod_guard)
    with pytest.raises((ValueError, FileExistsError)):
        r2.refuse_out_root("results/g6r21_fake")
    with pytest.raises((ValueError, FileExistsError)):
        r2.refuse_out_root("comparison_bench/outputs_comparison/g6r21_fake")
    for forbidden in [ROOT / "src", ROOT / "experiments", ROOT / "tools"]:
        if forbidden.exists():
            assert list(forbidden.rglob("*g6r21*")) == []
    for rel in ["workspace/g6s1_shift_4105cfc2-3bbb-444a-9283-31403d43b7ff",
                "workspace/g6r9_confirm_3f9a1c2e-7b4d-4e8a-9c1f-2d5e6a7b8c9d",
                "workspace/g6r20_uni_05100de1-e48c-4eea-a8a7-d5390f87cfc8",
                "workspace/v72p2d5_model_f_input/20260907_r1"]:
        root = ROOT / rel
        if root.exists():
            assert list(root.rglob("*g6r21*")) == [], rel
    for rel in r21.FUTURE_ROOTS.values():
        assert not (ROOT / rel).exists()


# Verifier: recompute incl net_secret/isolation + tamper FAILs.
def _write_fake_root(out, damping, accepted_n=90, baseline_f=84):
    manifest = {"command": r21._frozen_command(damping),
                "damping": float(damping),
                "cold_default": bool(float(damping) == 1.0),
                "prior": {"mode": r21.PRIOR_MODE, "eps": r21.FROZEN_EPS},
                "decoder": {"damping_alpha": float(damping)},
                "baseline": {"F": baseline_f}}
    (out / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with (out / "block_records.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(r21.BLOCK_COLUMNS))
        writer.writeheader()
        for i in range(128):
            accepted = i < accepted_n
            writer.writerow({
                "call_idx": i, "frame_id": 2123 + i // 2, "block_id": i,
                "session_id": r21.FROZEN_SESSION, "arm": r21.ARM,
                "candidate_id": r21.CANDIDATE_ID,
                "graph_seed": r21.GRAPH_SEEDS[i % 2],
                "n": 128, "m": 100, "attempted": "True",
                "finite": "True" if accepted else "False",
                "syndrome_match": "True" if accepted else "False",
                "tag_match": "True" if accepted else "False",
                "protocol_accepted": "True" if accepted else "False",
                "verified_exact": "True" if accepted else "False",
                "undetected": "False",
                "outcome": "exact" if accepted else "attempted",
                "syndrome_bits": 500, "tag_bits": 64, "control_bits": 0,
                "interaction_bits": 0, "auth_bits": 0, "disclosure_bits": 564,
                "iters": 7, "residual": 0, "provenance": "CHECK_UPDATED",
                "wall_s": 0.01, "crash": "False", "error": ""})
    leak_sum = 128 * 564
    beta_p = 1.0 - leak_sum / (128 * 128 * r21.H_FROZEN)
    beta_l = 1.0 - leak_sum / (128 * 128 * r21.H_L2)
    summary = {"attempted": 128, "accepted": accepted_n, "exact": accepted_n,
               "undetected": 0, "disclosure_sum": leak_sum,
               "damping": float(damping),
               "cold_default": bool(float(damping) == 1.0),
               "prior_mode": r21.PRIOR_MODE, "prior_eps": r21.FROZEN_EPS,
               "beta_eff_empirical_primary": beta_p,
               "beta_eff_empirical_l2_sensitivity": beta_l,
               "H_frozen_primary": r21.H_FROZEN,
               "H_L2_sensitivity": r21.H_L2,
               "net_secret_bits": r21.net_secret_bits(accepted_n, leak_sum,
                                                      r21.N),
               "baseline_F": baseline_f,
               "paired_lift": accepted_n - baseline_f, "lift_gate": 6,
               "lift_gate_pass": bool(accepted_n - baseline_f >= 6),
               "terminal": "COMPLETE_128"}
    (out / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (out / "report.md").write_text("# fake\n", encoding="utf-8")


def _rewrite_rows(out, mutate):
    rows = list(csv.DictReader(
        (out / "block_records.csv").read_text(encoding="utf-8").splitlines()))
    mutate(rows)
    with (out / "block_records.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(r21.BLOCK_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)


def _rewrite_json(out, name, mutate):
    doc = json.loads((out / name).read_text(encoding="utf-8"))
    mutate(doc)
    (out / name).write_text(json.dumps(doc), encoding="utf-8")


def test_verifier_pass_and_isolation_tamper_fails(fake_root, prod_guard):
    _assert_no_new_production(prod_guard)
    out = fake_root / "verify_fake"
    out.mkdir(parents=True)
    _write_fake_root(out, 0.5)
    assert r21.verify_root(str(out), 0.5) is True
    assert r21.verify_root(str(out), 0.8) is False  # wrong arm
    _rewrite_rows(out, lambda rows: rows[0].update(
        {"undetected": "True", "verified_exact": "False",
         "outcome": "undetected"}))
    assert r21.verify_root(str(out), 0.5) is False  # undetected-merge
    _rewrite_rows(out, lambda rows: rows[0].update(
        {"undetected": "False", "verified_exact": "True",
         "outcome": "exact"}))
    assert r21.verify_root(str(out), 0.5) is True
    _rewrite_rows(out, lambda rows: rows[1].update({"disclosure_bits": "563"}))
    assert r21.verify_root(str(out), 0.5) is False  # disclosure


def test_verifier_beta_net_damping_lift_tamper_fails(fake_root, prod_guard):
    _assert_no_new_production(prod_guard)
    out = fake_root / "verify_fake2"
    out.mkdir(parents=True)
    _write_fake_root(out, 0.8)
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["net_secret_bits"] == 90 * 5 * 128 - 128 * 564
    assert r21.verify_root(str(out), 0.8) is True
    _rewrite_json(out, "summary.json", lambda d: d.update(
        {"beta_eff_empirical_primary":
         float(d["beta_eff_empirical_primary"]) + 1e-6}))
    assert r21.verify_root(str(out), 0.8) is False  # hand-filled beta
    _rewrite_json(out, "summary.json", lambda d: d.update(
        {"beta_eff_empirical_primary":
         1.0 - d["disclosure_sum"] / (128 * 128 * r21.H_FROZEN),
         "net_secret_bits": int(d["net_secret_bits"]) + 1}))
    assert r21.verify_root(str(out), 0.8) is False  # hand-filled net
    _rewrite_json(out, "summary.json", lambda d: d.update(
        {"net_secret_bits": r21.net_secret_bits(90, 128 * 564, r21.N),
         "damping": 0.5}))
    assert r21.verify_root(str(out), 0.8) is False  # summary damping
    _rewrite_json(out, "summary.json", lambda d: d.update({"damping": 0.8}))
    _rewrite_json(out, "manifest.json", lambda d: d.update({"damping": 0.5}))
    assert r21.verify_root(str(out), 0.8) is False  # manifest damping
    _rewrite_json(out, "manifest.json", lambda d: d.update({"damping": 0.8}))
    _rewrite_json(out, "summary.json", lambda d: d.update({"paired_lift": 7}))
    assert r21.verify_root(str(out), 0.8) is False  # lift != exact - F
    _rewrite_json(out, "summary.json", lambda d: d.update({"paired_lift": 6}))
    assert r21.verify_root(str(out), 0.8) is True


# Profile-only per arm: 128-call plan, budgets ok, decoder 0, no pool.
@pytest.mark.parametrize("damping", [0.5, 0.8])
def test_profile_only_per_arm(prod_guard, damping):
    _assert_no_new_production(prod_guard)
    prof = r21.profile_only(damping)
    assert prof["damping"] == damping
    assert prof["plan_calls"] == 128
    assert prof["plan_order"] == "frame->block->graph even/odd"
    assert prof["budget_ok"] is True
    assert prof["budgets"]["scientific_calls"] == 256
    assert prof["decoder_calls"] == 0 and prof["real_pool_reads"] == 0
    assert prof["symbol_reads"] == 0 and prof["graphs_constructed"] == 0
    assert prof["baseline"]["F"] == 2  # S1-shift 2/128, read-only
    assert prof["paired_gate"]["gate"] == 6
    assert prof["future_root_absent"] is True
    assert prof["prior_mode"] == "shift-delta-eps1e-04"
    assert prof["prior_eps"] == 1e-4
    assert prof["bias_controls"]["varied"] == "damping_alpha ONLY"
    live = hashlib.sha256(
        (ROOT / r21.BASELINE_ROOT / "block_records.csv").read_bytes()
        ).hexdigest()
    assert prof["baseline"]["sha256"] == live  # byte-identical, read-only


# Bias controls: identical plans/priors across arms; ONLY damping varies.
def test_bias_controls_paired_across_arms(fake_root, monkeypatch, prod_guard):
    _assert_no_new_production(prod_guard)
    frames = r21.parse_frames(r21.FROZEN_FRAMES)
    plan_a = r21.build_call_plan(frames)
    plan_b = r21.build_call_plan(frames)
    assert plan_a == plan_b and len(plan_a) == 128
    out_a = fake_root / "bias_a"
    out_b = fake_root / "bias_b"
    bundle_a, _, _ = _run_arm(0.5, out_a, monkeypatch, ["hit"] * 128)
    bundle_b, _, _ = _run_arm(0.8, out_b, monkeypatch, ["hit"] * 128)
    ma, mb = dict(bundle_a["manifest"]), dict(bundle_b["manifest"])
    assert ma["damping"] == 0.5 and mb["damping"] == 0.8
    assert ma["command"] != mb["command"]
    assert ma["out_root"] != mb["out_root"]
    skip = {"damping", "command", "out_root", "cold_default", "decoder"}
    for k in ma:
        if k not in skip:
            assert ma[k] == mb[k], "bias break at %s" % k
    assert ma["bias_controls"]["varied"] == "damping_alpha ONLY"
    assert ma["prior"] == mb["prior"] == {"mode": r21.PRIOR_MODE,
                                          "eps": 1e-4,
                                          "source": ma["prior"]["source"]}
