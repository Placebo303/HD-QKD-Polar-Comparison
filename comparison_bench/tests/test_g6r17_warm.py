"""R17 WARM staged tests — FAKE fixtures only (never real pool).

R17b readiness: zero real-payload decoder calls; no UUID root; temp fake
roots; real R9/R11 CSVs touched READ-ONLY (counts only, never symbols)
for the honest F/A import checks. Covers: T-W0 frozen constants/ARGV;
T-W1 warm-carry chain + determinism; T-W2 cold-default byte-identical vs
R11-frozen path; T-W3 staged-m enforced both paths; T-W4 UNDETECTED_STOP
both paths; T-W5 refusal/no-overwrite/verifier incl net_secret;
T-W6 R9-fixed F=1 + R11-cold A=87 imports (read-only, byte-identical,
zero calls); T-W7 profile-only warm plan; T-W8 net_secret frozen values.
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
RUNNER_PATH = ROOT / "scripts" / "g6r17_warm.py"
R11_PATH = ROOT / "scripts" / "g6r11_adaptive.py"


def _load_runner(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


g17 = _load_runner(RUNNER_PATH, "g6r17_warm_test")
g11 = _load_runner(R11_PATH, "g6r11_adaptive_ref_test")

PRODUCTION_ABSENT = (
    "comparison_bench.formal_ir.v35_algorithm_development",
    "comparison_bench.formal_ir.v72p2d3_gf32_contrast",
)


def _assert_no_production():
    bad = [k for k in PRODUCTION_ABSENT if k in sys.modules]
    assert bad == [], "production on fake path: %r" % bad


@pytest.fixture()
def fake_root():
    path = ROOT / "workspace" / ("g6r17_fake_%s" % uuid.uuid4().hex)
    assert not path.exists()
    assert "47bfa9b9" not in str(path)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _fake_mother(seed):
    H = np.zeros((g17.M_MOTHER, g17.N), dtype=np.uint8)
    for v in range(g17.N):
        H[v % g17.M_MOTHER, v] = 1
    prefixes = {int(m): {"m": int(m), "rows": (0, int(m)),
                         "matrix": H[:int(m), :].copy()}
                for m in g17.STAGE_MS}
    return {"arm": g17.ARM, "width": g17.N, "graph_seed": int(seed),
            "n": g17.N, "m": g17.M_MOTHER, "E": int(np.count_nonzero(H)),
            "edges": [], "coefficients": [], "dense": H,
            "structure": None, "prefixes": prefixes, "status": "ok",
            "admitted": True, "failure_reason": ""}


class _FakeResult:
    def __init__(self, x_hat, final_beliefs, iters=5, provenance="CHECK_UPDATED"):
        self.x_hat = np.asarray(x_hat, dtype=np.int64)
        self.iterations = int(iters)
        self.belief_provenance = provenance
        self.final_beliefs = np.asarray(final_beliefs, dtype=np.float64)


def _fake_frame_table():
    rows = []
    for fid in range(2123, 2187):
        for p in range(256):
            rows.append((fid, p, 0, 0))  # all-zero Alice/Bob (fake pool)
    return pd.DataFrame(rows, columns=["frame_id", "pair_idx",
                                       "alice_symbol", "bob_symbol"])


def _fake_pre_execute(registry, session, frames, arm, prior):
    assert registry == g17.FROZEN_REGISTRY
    assert session == g17.FROZEN_SESSION
    assert frames == g17.FROZEN_FRAMES
    assert arm == g17.ARM
    assert prior == g17.FROZEN_PRIOR_ROOT
    return list(range(2123, 2187))


def _fake_adapters(actions, calls, ms_log, warm_log, finals_log, seed,
                   cold_only=False):
    """Scripted fake: each decode pops 'hit' (truth=zeros) or 'miss'.

    final_beliefs are drawn from a seeded RNG in call order (deterministic
    per seed); seeded calls report WARM_START_UNSPECIFIED like the real
    v35 decoder, cold calls CHECK_UPDATED.
    """
    plan = list(actions)
    rng = np.random.default_rng(int(seed))
    prior = np.full((1024, 1024), 1.0 / 1024.0)

    def fake_decode(H, priors, syn, **kw):
        calls.append(1)
        ms_log.append(int(H.shape[0]))
        assert kw.get("max_iter") == 90 and kw.get("damping_alpha") == 1.0
        wb = kw.get("warm_beliefs")
        if cold_only:
            assert wb is None  # cold path never seeds
        warm_log.append(None if wb is None else np.asarray(wb).copy())
        final = rng.standard_normal((g17.N, g17.Q))
        finals_log.append(final.copy())
        prov = "WARM_START_UNSPECIFIED" if wb is not None else "CHECK_UPDATED"
        action = plan.pop(0)
        if action == "hit":
            return _FakeResult(np.zeros(g17.N, dtype=np.int64), final,
                               provenance=prov)
        return _FakeResult(np.ones(g17.N, dtype=np.int64), final,
                           provenance=prov)

    def fake_syndrome(H, x):
        return np.zeros(H.shape[0], dtype=np.uint8)

    def fake_prior(root):
        return prior

    def fake_build(seed):
        assert int(seed) in g17.MOTHER_SEEDS
        return _fake_mother(seed)

    return {"decode_fn": fake_decode, "syndrome_fn": fake_syndrome,
            "load_prior_fn": fake_prior, "build_fn": fake_build,
            "pre_execute_fn": _fake_pre_execute}


def _run_script(actions, out_dir, warm_start, tag_fn=None, seed=7):
    calls: list = []
    ms_log: list = []
    warm_log: list = []
    finals_log: list = []
    adapters = _fake_adapters(actions, calls, ms_log, warm_log, finals_log,
                              seed, cold_only=(not warm_start))
    bundle = g17.run_authorized_batch(
        str(out_dir), g17.FROZEN_REGISTRY, g17.FROZEN_SESSION,
        g17.FROZEN_FRAMES, g17.ARM, g17.FROZEN_PRIOR_ROOT,
        g17.BASELINE_ROOT, g17.COLD_ROOT, int(warm_start),
        adapters=adapters,
        reader_override=lambda frames: _fake_frame_table(),
        tag_fn=tag_fn)
    return bundle, calls, ms_log, warm_log, finals_log


def _run_g11(actions, out_dir, tag_fn=None):
    calls: list = []
    ms_log: list = []

    def fake_decode(H, priors, syn, **kw):
        calls.append(1)
        ms_log.append(int(H.shape[0]))
        assert kw.get("max_iter") == 90 and kw.get("damping_alpha") == 1.0
        assert kw.get("warm_beliefs") is None
        action = plan.pop(0)
        if action == "hit":
            return _SimpleResult(np.zeros(g11.N, dtype=np.int64))
        return _SimpleResult(np.ones(g11.N, dtype=np.int64))

    plan = list(actions)
    prior = np.full((1024, 1024), 1.0 / 1024.0)

    def fake_build(seed):
        H = np.zeros((g11.M_MOTHER, g11.N), dtype=np.uint8)
        for v in range(g11.N):
            H[v % g11.M_MOTHER, v] = 1
        prefixes = {int(m): {"m": int(m), "rows": (0, int(m)),
                             "matrix": H[:int(m), :].copy()}
                    for m in g11.STAGE_MS}
        return {"arm": g11.ARM, "width": g11.N, "graph_seed": int(seed),
                "n": g11.N, "m": g11.M_MOTHER, "E": 0, "edges": [],
                "coefficients": [], "dense": H, "structure": None,
                "prefixes": prefixes, "status": "ok", "admitted": True,
                "failure_reason": ""}

    def fake_pre(registry, session, frames, arm, prior_root):
        return list(range(2123, 2187))

    adapters = {"decode_fn": fake_decode,
                "syndrome_fn": lambda H, x: np.zeros(H.shape[0],
                                                     dtype=np.uint8),
                "load_prior_fn": lambda root: prior,
                "build_fn": fake_build, "pre_execute_fn": fake_pre}
    bundle = g11.run_authorized_batch(
        str(out_dir), g11.FROZEN_REGISTRY, g11.FROZEN_SESSION,
        g11.FROZEN_FRAMES, g11.ARM, g11.FROZEN_PRIOR_ROOT,
        g11.BASELINE_ROOT, adapters=adapters,
        reader_override=lambda frames: _fake_frame_table(),
        tag_fn=tag_fn)
    return bundle, calls, ms_log


class _SimpleResult:
    def __init__(self, x_hat, iters=5):
        self.x_hat = np.asarray(x_hat, dtype=np.int64)
        self.iterations = int(iters)
        self.belief_provenance = "CHECK_UPDATED"


def _assert_stage_order(bundle, ms_log):
    """No same-row retry: per-block stage m strictly increases S0.. prefix."""
    assert list(g17.STAGE_MS) == [100, 108, 120]
    per_block: dict[int, list[int]] = {}
    for sr in bundle["stage_records"]:
        per_block.setdefault(int(sr["block_id"]), []).append(int(sr["m"]))
    for block in bundle["block_records"]:
        bid = int(block["block_id"])
        expect = list(g17.STAGE_MS[:int(block["stages_attempted"])])
        assert per_block[bid] == expect  # strictly increasing, no retry
        assert int(block["m_final"]) == expect[-1]
        assert int(block["disclosure_bits"]) == 5 * expect[-1] + 64
    flat: list[int] = []
    for block in bundle["block_records"]:
        flat.extend(list(g17.STAGE_MS[:int(block["stages_attempted"])]))
    assert ms_log == flat  # decoder saw exactly the staged prefixes


# T-W0: frozen constants + ARGV lock.
def test_w0_frozen_constants_and_argv():
    _assert_no_production()
    assert g17.FROZEN_REGISTRY == "v71_data_registry.json"
    assert g17.FROZEN_SESSION == "20260107_PPLN_1p5M"
    assert g17.FROZEN_FRAMES == "2123..2186"
    assert g17.ARM == "L020"
    assert g17.FROZEN_PRIOR_ROOT == \
        "workspace/v72p2d5_model_f_input/20260907_r1"
    assert g17.BASELINE_ROOT == \
        "workspace/g6r9_confirm_3f9a1c2e-7b4d-4e8a-9c1f-2d5e6a7b8c9d"
    assert g17.COLD_ROOT == \
        "workspace/g6r11_adaptive_3c2b5b2e-897b-467e-a3e6-0cba005914ae"
    assert g17.FUTURE_ROOT == \
        "workspace/g6r17_warm_47bfa9b9-e944-4bad-a105-69bc92a66045"
    assert g17.MOTHER_SEEDS == (2026094722, 2026094723)
    assert tuple(g17.STAGE_MS) == (100, 108, 120)
    assert (g17.MAX_ITER, g17.DAMPING) == (90, 1.0)
    assert (g17.SCI_CEILING, g17.SETUP_CEILING) == (384, 8)
    assert g17.PAIRED_LIFT_GATE == 4
    assert g17.FROZEN_COMMAND == (
        ".venv/bin/python scripts/g6r17_warm.py --execute-real "
        "--execution-authorized --warm-start 1 "
        "--registry v71_data_registry.json "
        "--session 20260107_PPLN_1p5M --frames 2123..2186 --arm L020 "
        "--prior-root workspace/v72p2d5_model_f_input/20260907_r1 "
        "--baseline-root "
        "workspace/g6r9_confirm_3f9a1c2e-7b4d-4e8a-9c1f-2d5e6a7b8c9d "
        "--cold-root "
        "workspace/g6r11_adaptive_3c2b5b2e-897b-467e-a3e6-0cba005914ae "
        "--out-dir workspace/g6r17_warm_47bfa9b9-e944-4bad-a105-69bc92a66045")
    assert "--warm-start 1" in g17.FROZEN_COMMAND
    assert "--warm-start 0" in g17.FROZEN_COMMAND_COLD
    assert g17.build_parser().parse_args(["--profile-only"]).warm_start == 0


# T-W1: warm-carry chain (S0 cold; S1/S2 init = prior final beliefs).
def test_w1_warm_carry_chain(fake_root):
    _assert_no_production()
    out = fake_root / "carry"
    bundle, calls, ms_log, warm_log, finals_log = _run_script(
        ["miss", "hit"] * 128, out, warm_start=1)
    assert len(calls) == 256
    assert len(warm_log) == 256 and len(finals_log) == 256
    for k in range(128):
        assert warm_log[2 * k] is None  # S0 starts cold
        assert np.array_equal(warm_log[2 * k + 1], finals_log[2 * k])
    provs = [(sr["block_id"], sr["stage"], sr["provenance"])
             for sr in bundle["stage_records"][:4]]
    assert [p for _, _, p in provs] == ["CHECK_UPDATED",
                                        "WARM_START_UNSPECIFIED"] * 2
    assert bundle["summary"]["warm_start"] == 1
    _assert_stage_order(bundle, ms_log)
    assert g17.verify_root(str(out)) is False  # not written yet
    g17.write_batch_root(bundle)
    assert g17.verify_root(str(out)) is True


def test_w1_warm_carry_deterministic(fake_root):
    _assert_no_production()
    actions = (["miss", "miss", "hit"] * 128)[:300]
    out1, out2 = fake_root / "det1", fake_root / "det2"
    b1, c1, m1, w1, f1 = _run_script(list(actions), out1, 1, seed=99)
    b2, c2, m2, w2, f2 = _run_script(list(actions), out2, 1, seed=99)
    assert m1 == m2 and len(c1) == len(c2)
    assert len(w1) == len(w2)
    for a, b in zip(w1, w2):
        assert (a is None and b is None) or np.array_equal(a, b)
    for a, b in zip(f1, f2):
        assert np.array_equal(a, b)
    assert b1["block_records"] == b2["block_records"]
    assert b1["stage_records"] == b2["stage_records"]
    s1 = {k: v for k, v in b1["summary"].items() if k != "out_root"}
    s2 = {k: v for k, v in b2["summary"].items() if k != "out_root"}
    assert s1 == s2


# T-W2: cold-default byte-identical vs the R11-frozen path.
def test_w2_cold_default_byte_identical_vs_r11(fake_root):
    _assert_no_production()
    actions = ["miss", "hit"] * 128
    out17, out11 = fake_root / "cold17", fake_root / "cold11"
    bundle, calls, ms_log, warm_log, _ = _run_script(
        list(actions), out17, warm_start=0)
    assert all(w is None for w in warm_log)
    ref, ref_calls, ref_ms = _run_g11(list(actions), out11)
    assert len(calls) == len(ref_calls) == 256
    assert ms_log == ref_ms
    assert bundle["block_records"] == ref["block_records"]
    assert bundle["stage_records"] == ref["stage_records"]
    shared = ("attempted", "accepted", "exact", "undetected",
              "per_stage_exact", "exhausted", "disclosure_sum",
              "reconciled_net_bits", "net_secret_bits",
              "beta_eff_empirical_primary", "beta_eff_empirical_l2_sensitivity",
              "baseline_F", "paired_lift", "lift_gate_pass",
              "scientific_calls", "setup_calls")
    for key in shared:
        assert bundle["summary"][key] == ref["summary"][key], key
    g17.write_batch_root(bundle)
    g11.write_batch_root(ref)
    assert g17.verify_root(str(out17)) is True
    assert g11.verify_root(str(out11)) is True
    for name in ("block_records.csv", "stage_records.csv"):
        assert (out17 / name).read_bytes() == (out11 / name).read_bytes()


# T-W3: staged-m enforced on both paths.
def test_w3_staged_m_both_paths(fake_root):
    _assert_no_production()
    out = fake_root / "w_s0"
    bundle, calls, ms_log, _, _ = _run_script(["hit"] * 128, out, 1)
    assert len(calls) == 128 and bundle["summary"]["warm_start"] == 1
    assert all(b["stage"] == "S0" for b in bundle["block_records"])
    _assert_stage_order(bundle, ms_log)
    out = fake_root / "w_s2"
    bundle, calls, ms_log, warm_log, _ = _run_script(
        ["miss", "miss", "hit"] * 128, out, 1)
    assert len(calls) == 384  # ceiling OK
    assert all(b["stage"] == "S2" for b in bundle["block_records"])
    assert all(b["disclosure_bits"] == 664 for b in bundle["block_records"])
    # S2 init = S1 final (two carries per block).
    assert warm_log[0] is None
    _assert_stage_order(bundle, ms_log)
    g17.write_batch_root(bundle)
    assert g17.verify_root(str(out)) is True
    out = fake_root / "w_exh"
    bundle, calls, ms_log, _, _ = _run_script(["miss"] * 384, out, 1)
    assert bundle["summary"]["terminal"] == "COMPLETE_128"
    assert all(b["stage"] == "exhausted" for b in bundle["block_records"])
    assert bundle["summary"]["disclosure_sum"] == 128 * 664
    _assert_stage_order(bundle, ms_log)
    out = fake_root / "c_s1"
    bundle, calls, ms_log, warm_log, _ = _run_script(
        ["miss", "hit"] * 128, out, 0)
    assert len(calls) == 256
    assert all(w is None for w in warm_log)
    assert all(b["stage"] == "S1" for b in bundle["block_records"])
    _assert_stage_order(bundle, ms_log)


# T-W4: UNDETECTED_STOP on both paths.
def test_w4_undetected_stop_both_paths(fake_root):
    _assert_no_production()
    liar = lambda vec: b"CONSTANT"  # noqa: E731  (test-only lying tag)
    for warm in (0, 1):
        out = fake_root / ("undet%d" % warm)
        bundle, calls, _, _, _ = _run_script(
            ["miss"] + ["hit"] * 400, out, warm, tag_fn=liar)
        s = bundle["summary"]
        assert s["attempted"] == 1 and s["undetected"] == 1
        assert s["terminal"] == "UNDETECTED_STOP"
        assert len(bundle["block_records"]) == 1
        assert len(calls) == 1  # stopped before any further decode
        g17.write_batch_root(bundle)
        assert g17.verify_root(str(out)) is False  # retained-but-FAIL
    # Honest-tag controls: same scripts run the full matrix both paths.
    for warm in (0, 1):
        out = fake_root / ("undet_ctrl%d" % warm)
        bundle, _, _, _, _ = _run_script(
            ["miss", "hit"] + ["hit"] * 400, out, warm)
        assert bundle["summary"]["undetected"] == 0
        assert bundle["summary"]["attempted"] == 128


# T-W5: refusal / no-overwrite / verifier.
def test_w5_refusal_missing_grant_zero_calls(fake_root):
    _assert_no_production()
    for extra in ([], ["--warm-start", "1"]):
        rc = g17.main(["--execute-real", "--registry", g17.FROZEN_REGISTRY,
                       "--session", g17.FROZEN_SESSION, "--frames",
                       g17.FROZEN_FRAMES, "--arm", g17.ARM, "--prior-root",
                       g17.FROZEN_PRIOR_ROOT, "--baseline-root",
                       g17.BASELINE_ROOT, "--cold-root", g17.COLD_ROOT,
                       "--out-dir", str(fake_root / "refuse")] + extra)
        assert rc == 2


def test_w5_refusal_existing_root_zero_calls(fake_root):
    _assert_no_production()
    for warm in (0, 1):
        target = fake_root / ("exists%d" % warm)
        target.mkdir(parents=True)
        calls: list = []
        with pytest.raises(FileExistsError):
            g17.run_authorized_batch(
                str(target), g17.FROZEN_REGISTRY, g17.FROZEN_SESSION,
                g17.FROZEN_FRAMES, g17.ARM, g17.FROZEN_PRIOR_ROOT,
                g17.BASELINE_ROOT, g17.COLD_ROOT, warm,
                adapters=_fake_adapters(["hit"] * 400, calls, [], [], [],
                                        5, cold_only=(not warm)),
                reader_override=lambda frames: _fake_frame_table())
        assert calls == []


def test_w5_no_overwrite():
    _assert_no_production()
    import comparison_bench.formal_ir.v72p2d10_mixed_degree_l1 as r2
    with pytest.raises((ValueError, FileExistsError)):
        r2.refuse_out_root("results/g6r17_fake")
    with pytest.raises((ValueError, FileExistsError)):
        r2.refuse_out_root("comparison_bench/outputs_comparison/g6r17_fake")
    for forbidden in [ROOT / "src", ROOT / "experiments", ROOT / "tools"]:
        if forbidden.exists():
            hits = list(forbidden.rglob("*g6r17*"))
            assert hits == [], "frozen dir touched: %r" % hits
    for prior in [ROOT / "workspace/g6r9_confirm_3f9a1c2e-7b4d-4e8a-9c1f-2d5e6a7b8c9d",
                  ROOT / "workspace/g6r11_adaptive_3c2b5b2e-897b-467e-a3e6-0cba005914ae",
                  ROOT / "workspace/g6r10_ctrl_6f2b8c1d-4a3e-4f9a-b7c2-d5e6f8a9b0c1",
                  ROOT / "workspace/g6_decide_r1_8e7c2a1f-4b6d-4e9a-9c3f-2a5b7d8e0f1a"]:
        if prior.exists():
            hits = list(prior.rglob("*g6r17*"))
            assert hits == [], "prior root touched: %r" % hits
    assert not (ROOT / g17.FUTURE_ROOT).exists()  # UUID root absent


def test_w5_verifier_tamper_fails(fake_root):
    _assert_no_production()
    out = fake_root / "ver"
    bundle, _, _, _, _ = _run_script(["miss", "hit"] * 128, out, 1)
    g17.write_batch_root(bundle)
    assert g17.verify_root(str(out)) is True
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    tampered = dict(summary)
    tampered["beta_eff_empirical_primary"] = \
        float(tampered["beta_eff_empirical_primary"]) + 1e-6
    (out / "summary.json").write_text(json.dumps(tampered), encoding="utf-8")
    assert g17.verify_root(str(out)) is False
    tampered = dict(summary)
    tampered["net_secret_bits"] = int(tampered["net_secret_bits"]) + 1
    (out / "summary.json").write_text(json.dumps(tampered), encoding="utf-8")
    assert g17.verify_root(str(out)) is False
    tampered = dict(summary)
    tampered["lift_vs_cold"] = int(tampered["lift_vs_cold"]) + 1
    (out / "summary.json").write_text(json.dumps(tampered), encoding="utf-8")
    assert g17.verify_root(str(out)) is False
    (out / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    assert g17.verify_root(str(out)) is True
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    manifest["warm_start"] = 0  # mode/command mismatch
    (out / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert g17.verify_root(str(out)) is False


# T-W6: honest imports — R9-fixed F=1 + R11-cold A=87 (read-only, zero calls).
def test_w6_honest_imports():
    _assert_no_production()
    calls: list = []
    base = g11.load_fixed_baseline(g17.BASELINE_ROOT)
    assert calls == []
    assert base["F"] == 1
    assert base["successes"] == [(34, 2140)]
    assert base["rows"] == 128
    raw = Path(g17.BASELINE_ROOT, "block_records.csv").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == base["sha256"]
    base2 = g11.load_fixed_baseline(g17.BASELINE_ROOT)  # byte-identical
    assert base2["sha256"] == base["sha256"] and base2["F"] == 1
    cold = g17.load_cold_reference(g17.COLD_ROOT)
    assert calls == []
    assert cold["A"] == 87
    assert len(cold["successes"]) == 87
    assert cold["rows"] == 128 and cold["terminal"] == "COMPLETE_128"
    raw_c = Path(g17.COLD_ROOT, "block_records.csv").read_bytes()
    assert hashlib.sha256(raw_c).hexdigest() == cold["sha256"]
    cold2 = g17.load_cold_reference(g17.COLD_ROOT)  # byte-identical
    assert cold2["sha256"] == cold["sha256"] and cold2["A"] == 87
    assert calls == []


# T-W7: profile-only warm plan (budgets ok, decoder 0).
def test_w7_profile_only_fake():
    _assert_no_production()
    prof = g17.profile_only()
    assert prof["graphs_constructed"] == 0 and prof["decoder_calls"] == 0
    assert prof["model_f_loads"] == 0 and prof["real_pool_reads"] == 0
    assert prof["symbol_reads"] == 0
    assert prof["warm_start"] == 1
    assert prof["plan_calls"] == 128
    assert prof["max_stage_calls"] == 384 <= 384
    assert prof["budget_ok"] is True
    assert prof["budgets"]["scientific_calls"] == 384
    assert prof["budgets"]["setup_calls"] <= 8
    assert prof["baseline"]["F"] == 1
    assert prof["cold_reference"]["A"] == 87
    assert prof["seed_disjointness"]["passed"] is True
    assert prof["future_root_absent"] is True
    assert not (ROOT / g17.FUTURE_ROOT).exists()


# T-W8: net_secret frozen values + cold-reference diagnostic on a bundle.
def test_w8_net_secret_frozen(fake_root):
    _assert_no_production()
    assert g17.net_secret_bits(1, 564, g17.N) == 76
    assert g17.net_secret_bits(1, 604, g17.N) == 36
    assert g17.net_secret_bits(1, 664, g17.N) == -24
    assert g17.net_secret_bits(0, 664, g17.N) == -664
    # Mixed R11-shape 0/26/61/41: 87*640 - 83432 = -27752.
    assert g17.net_secret_bits(87, 26 * 604 + 61 * 664 + 41 * 664,
                               g17.N) == -27752
    out = fake_root / "r16w"
    bundle, _, _, _, _ = _run_script(["miss", "hit"] * 128, out, 1)
    assert bundle["summary"]["net_secret_bits"] == 128 * 36 == 4608
    assert bundle["summary"]["cold_A"] == 87
    assert bundle["summary"]["lift_vs_cold"] == \
        bundle["summary"]["exact"] - 87
    g17.write_batch_root(bundle)
    assert g17.verify_root(str(out)) is True
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    tampered = dict(summary)
    del tampered["net_secret_bits"]
    (out / "summary.json").write_text(json.dumps(tampered), encoding="utf-8")
    assert g17.verify_root(str(out)) is False
