"""R11 ADAPTIVE staged tests — FAKE fixtures only (never real pool).

R11b readiness: zero real-payload decoder calls; no UUID root; temp fake
roots; real R9 CSV touched READ-ONLY (frame/call counts only, never
symbols) for the honest-baseline import check. Covers: T-S1 stage
accounting (S0/S1/S2-success/exhausted -> 564/604/664/664; sum-over-stages
FAILs); T-S2 undetected-at-Sk global STOP + retained; T-S3
refusal/no-overwrite/verifier; T-S4 honest-baseline import (zero fixed
calls, byte-identical); T-S5 deterministic replay + admission predicate
on fake prefix slices.
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
RUNNER_PATH = ROOT / "scripts" / "g6r11_adaptive.py"


def _load_runner():
    spec = importlib.util.spec_from_file_location("g6r11_adaptive_test",
                                                  str(RUNNER_PATH))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["g6r11_adaptive_test"] = mod
    spec.loader.exec_module(mod)
    return mod


g11 = _load_runner()

PRODUCTION_ABSENT = (
    "comparison_bench.formal_ir.v35_algorithm_development",
    "comparison_bench.formal_ir.v72p2d3_gf32_contrast",
)


def _assert_no_production():
    bad = [k for k in PRODUCTION_ABSENT if k in sys.modules]
    assert bad == [], "production on fake path: %r" % bad


@pytest.fixture()
def fake_root():
    path = ROOT / "workspace" / ("g6r11_fake_%s" % uuid.uuid4().hex)
    assert not path.exists()
    assert "3c2b5b2e" not in str(path)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _fake_mother(seed):
    H = np.zeros((g11.M_MOTHER, g11.N), dtype=np.uint8)
    for v in range(g11.N):
        H[v % g11.M_MOTHER, v] = 1
    prefixes = {int(m): {"m": int(m), "rows": (0, int(m)),
                         "matrix": H[:int(m), :].copy()}
                for m in g11.STAGE_MS}
    return {"arm": g11.ARM, "width": g11.N, "graph_seed": int(seed),
            "n": g11.N, "m": g11.M_MOTHER, "E": int(np.count_nonzero(H)),
            "edges": [], "coefficients": [], "dense": H,
            "structure": None, "prefixes": prefixes, "status": "ok",
            "admitted": True, "failure_reason": ""}


class _FakeResult:
    def __init__(self, x_hat, iters=5):
        self.x_hat = np.asarray(x_hat, dtype=np.int64)
        self.iterations = int(iters)
        self.belief_provenance = "CHECK_UPDATED"


def _fake_frame_table():
    rows = []
    for fid in range(2123, 2187):
        for p in range(256):
            rows.append((fid, p, 0, 0))  # all-zero Alice/Bob (fake pool)
    return pd.DataFrame(rows, columns=["frame_id", "pair_idx",
                                       "alice_symbol", "bob_symbol"])


def _fake_pre_execute(registry, session, frames, arm, prior):
    assert registry == g11.FROZEN_REGISTRY
    assert session == g11.FROZEN_SESSION
    assert frames == g11.FROZEN_FRAMES
    assert arm == g11.ARM
    assert prior == g11.FROZEN_PRIOR_ROOT
    return list(range(2123, 2187))


def _fake_adapters(actions, calls, ms_log):
    """Scripted fake: each decode pops 'hit' (truth=zeros) or 'miss'."""
    plan = list(actions)
    prior = np.full((1024, 1024), 1.0 / 1024.0)

    def fake_decode(H, priors, syn, **kw):
        calls.append(1)
        ms_log.append(int(H.shape[0]))
        assert kw.get("max_iter") == 90 and kw.get("damping_alpha") == 1.0
        assert kw.get("warm_beliefs") is None  # cold single-pass
        action = plan.pop(0)
        if action == "hit":
            return _FakeResult(np.zeros(g11.N, dtype=np.int64))
        return _FakeResult(np.ones(g11.N, dtype=np.int64))

    def fake_syndrome(H, x):
        return np.zeros(H.shape[0], dtype=np.uint8)

    def fake_prior(root):
        return prior

    def fake_build(seed):
        assert int(seed) in g11.MOTHER_SEEDS
        return _fake_mother(seed)

    return {"decode_fn": fake_decode, "syndrome_fn": fake_syndrome,
            "load_prior_fn": fake_prior, "build_fn": fake_build,
            "pre_execute_fn": _fake_pre_execute}


def _run_script(actions, out_dir, tag_fn=None):
    calls: list = []
    ms_log: list = []
    adapters = _fake_adapters(actions, calls, ms_log)
    bundle = g11.run_authorized_batch(
        str(out_dir), g11.FROZEN_REGISTRY, g11.FROZEN_SESSION,
        g11.FROZEN_FRAMES, g11.ARM, g11.FROZEN_PRIOR_ROOT,
        g11.BASELINE_ROOT, adapters=adapters,
        reader_override=lambda frames: _fake_frame_table(),
        tag_fn=tag_fn)
    return bundle, calls, ms_log


def _assert_stage_order(bundle, ms_log):
    """No same-row retry: per-block stage m strictly increases S0.. prefix."""
    assert list(g11.STAGE_MS) == [100, 108, 120]
    per_block: dict[int, list[int]] = {}
    for sr in bundle["stage_records"]:
        per_block.setdefault(int(sr["block_id"]), []).append(int(sr["m"]))
    for block in bundle["block_records"]:
        bid = int(block["block_id"])
        expect = list(g11.STAGE_MS[:int(block["stages_attempted"])])
        assert per_block[bid] == expect  # strictly increasing, no retry
        assert int(block["m_final"]) == expect[-1]
        assert int(block["disclosure_bits"]) == 5 * expect[-1] + 64
    flat: list[int] = []
    for block in bundle["block_records"]:
        flat.extend(list(g11.STAGE_MS[:int(block["stages_attempted"])]))
    assert ms_log == flat  # decoder saw exactly the staged prefixes


# T-S1: stage accounting — final-prefix disclosure, never summed.
def test_s1_s0_success_564(fake_root):
    _assert_no_production()
    out = fake_root / "s0"
    bundle, calls, ms_log = _run_script(["hit"] * 128, out)
    g11.write_batch_root(bundle)
    s = bundle["summary"]
    assert s["attempted"] == 128 and s["exact"] == 128 and s["undetected"] == 0
    assert s["per_stage_exact"] == {"S0": 128, "S1": 0, "S2": 0}
    assert all(b["stage"] == "S0" and b["m_final"] == 100
               for b in bundle["block_records"])
    assert all(b["disclosure_bits"] == 564 for b in bundle["block_records"])
    assert s["disclosure_sum"] == 128 * 564
    assert len(calls) == 128 and s["scientific_calls"] == 128
    assert s["reconciled_net_bits"] == 128 * 28 * 5
    assert s["paired_lift"] == 127 and s["lift_gate_pass"] is True
    _assert_stage_order(bundle, ms_log)
    assert g11.verify_root(str(out)) is True


def test_s1_s1_success_604(fake_root):
    _assert_no_production()
    out = fake_root / "s1"
    bundle, calls, ms_log = _run_script(["miss", "hit"] * 128, out)
    g11.write_batch_root(bundle)
    s = bundle["summary"]
    assert s["exact"] == 128 and s["undetected"] == 0
    assert s["per_stage_exact"] == {"S0": 0, "S1": 128, "S2": 0}
    assert all(b["stage"] == "S1" and b["m_final"] == 108
               for b in bundle["block_records"])
    assert all(b["disclosure_bits"] == 604 for b in bundle["block_records"])
    assert s["disclosure_sum"] == 128 * 604
    assert len(calls) == 256 and s["scientific_calls"] == 256
    assert s["reconciled_net_bits"] == 128 * 20 * 5
    _assert_stage_order(bundle, ms_log)
    assert g11.verify_root(str(out)) is True


def test_s1_s2_success_664(fake_root):
    _assert_no_production()
    out = fake_root / "s2"
    bundle, calls, ms_log = _run_script(["miss", "miss", "hit"] * 128, out)
    g11.write_batch_root(bundle)
    s = bundle["summary"]
    assert s["exact"] == 128 and s["undetected"] == 0
    assert s["per_stage_exact"] == {"S0": 0, "S1": 0, "S2": 128}
    assert all(b["stage"] == "S2" and b["m_final"] == 120
               for b in bundle["block_records"])
    assert all(b["disclosure_bits"] == 664 for b in bundle["block_records"])
    assert s["disclosure_sum"] == 128 * 664
    assert len(calls) == 384 and s["scientific_calls"] == 384  # ceiling OK
    assert s["reconciled_net_bits"] == 128 * 8 * 5
    _assert_stage_order(bundle, ms_log)
    assert g11.verify_root(str(out)) is True


def test_s1_exhausted_664(fake_root):
    _assert_no_production()
    out = fake_root / "exh"
    bundle, calls, ms_log = _run_script(["miss"] * 384, out)
    g11.write_batch_root(bundle)
    s = bundle["summary"]
    assert s["exact"] == 0 and s["accepted"] == 0 and s["undetected"] == 0
    assert s["exhausted"] == 128 and s["terminal"] == "COMPLETE_128"
    assert all(b["stage"] == "exhausted" and b["m_final"] == 120
               for b in bundle["block_records"])
    assert all(b["disclosure_bits"] == 664 for b in bundle["block_records"])
    assert s["disclosure_sum"] == 128 * 664  # failures charged final prefix
    assert len(calls) == 384
    assert s["paired_lift"] == -1 and s["lift_gate_pass"] is False
    _assert_stage_order(bundle, ms_log)
    assert g11.verify_root(str(out)) is True


def test_s1_sum_over_stages_fails(fake_root):
    _assert_no_production()
    out = fake_root / "sumtamper"
    bundle, _, _ = _run_script(["miss", "hit"] * 128, out)
    g11.write_batch_root(bundle)
    assert g11.verify_root(str(out)) is True
    rows = list(csv.DictReader(
        (out / "block_records.csv").read_text(encoding="utf-8").splitlines()))

    def rewrite(value):
        rows[0]["disclosure_bits"] = str(value)
        with (out / "block_records.csv").open("w", newline="",
                                              encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(g11.BLOCK_COLUMNS))
            writer.writeheader()
            writer.writerows(rows)

    rewrite(564 + 604)
    assert g11.verify_root(str(out)) is False  # partial sum 1168 FAILs
    rewrite(564 + 604 + 664)
    assert g11.verify_root(str(out)) is False  # full sum 1832 FAILs


# T-S2: undetected at Sk -> global STOP + retained.
def test_s2_undetected_stop_retained(fake_root):
    _assert_no_production()
    out = fake_root / "undet"
    liar = lambda vec: b"CONSTANT"  # noqa: E731  (test-only lying tag)
    bundle, calls, _ = _run_script(["miss"] + ["hit"] * 400, out,
                                   tag_fn=liar)
    s = bundle["summary"]
    assert s["attempted"] == 1 and s["undetected"] == 1
    assert s["terminal"] == "UNDETECTED_STOP"
    assert len(bundle["block_records"]) == 1  # retained, nothing more
    assert len(bundle["stage_records"]) == 1
    assert len(calls) == 1  # stopped before any further decode
    g11.write_batch_root(bundle)
    assert g11.verify_root(str(out)) is False  # retained-but-FAIL
    # Honest-tag control: same script misses S0 cleanly, no stop.
    out2 = fake_root / "undet_ctrl"
    bundle2, _, _ = _run_script(["miss", "hit"] + ["hit"] * 400, out2)
    assert bundle2["summary"]["undetected"] == 0
    assert bundle2["summary"]["attempted"] == 128


# T-S3: refusal / no-overwrite / verifier.
def test_s3_refusal_missing_grant_zero_calls(fake_root):
    _assert_no_production()
    rc = g11.main(["--execute-real", "--registry", g11.FROZEN_REGISTRY,
                   "--session", g11.FROZEN_SESSION, "--frames",
                   g11.FROZEN_FRAMES, "--arm", g11.ARM, "--prior-root",
                   g11.FROZEN_PRIOR_ROOT, "--baseline-root",
                   g11.BASELINE_ROOT,
                   "--out-dir", str(fake_root / "refuse")])
    assert rc == 2


def test_s3_refusal_existing_root_zero_calls(fake_root):
    _assert_no_production()
    target = fake_root / "exists"
    target.mkdir(parents=True)
    calls: list = []
    ms_log: list = []
    with pytest.raises(FileExistsError):
        g11.run_authorized_batch(
            str(target), g11.FROZEN_REGISTRY, g11.FROZEN_SESSION,
            g11.FROZEN_FRAMES, g11.ARM, g11.FROZEN_PRIOR_ROOT,
            g11.BASELINE_ROOT,
            adapters=_fake_adapters(["hit"] * 400, calls, ms_log),
            reader_override=lambda frames: _fake_frame_table())
    assert calls == [] and ms_log == []


def test_s3_no_overwrite():
    _assert_no_production()
    import comparison_bench.formal_ir.v72p2d10_mixed_degree_l1 as r2
    with pytest.raises((ValueError, FileExistsError)):
        r2.refuse_out_root("results/g6r11_fake")
    with pytest.raises((ValueError, FileExistsError)):
        r2.refuse_out_root("comparison_bench/outputs_comparison/g6r11_fake")
    for forbidden in [ROOT / "src", ROOT / "experiments", ROOT / "tools"]:
        if forbidden.exists():
            hits = list(forbidden.rglob("*g6r11*"))
            assert hits == [], "frozen dir touched: %r" % hits
    for prior in [ROOT / "workspace/g6r9_confirm_3f9a1c2e-7b4d-4e8a-9c1f-2d5e6a7b8c9d",
                  ROOT / "workspace/g6r10_ctrl_6f2b8c1d-4a3e-4f9a-b7c2-d5e6f8a9b0c1",
                  ROOT / "workspace/g6_decide_r1_8e7c2a1f-4b6d-4e9a-9c3f-2a5b7d8e0f1a"]:
        if prior.exists():
            hits = list(prior.rglob("*g6r11*"))
            assert hits == [], "prior root touched: %r" % hits
    assert not (ROOT / g11.FUTURE_ROOT).exists()  # UUID root absent


def test_s3_verifier_beta_tamper_fails(fake_root):
    _assert_no_production()
    out = fake_root / "beta"
    bundle, _, _ = _run_script(["hit"] * 128, out)
    g11.write_batch_root(bundle)
    assert g11.verify_root(str(out)) is True
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    summary["beta_eff_empirical_primary"] = \
        float(summary["beta_eff_empirical_primary"]) + 1e-6
    (out / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    assert g11.verify_root(str(out)) is False


# T-S4: honest-baseline import (read-only R9 CSV; zero fixed decode calls).
def test_s4_honest_baseline_import():
    _assert_no_production()
    calls: list = []
    base = g11.load_fixed_baseline(g11.BASELINE_ROOT)
    assert calls == []
    assert base["F"] == 1
    assert base["successes"] == [(34, 2140)]
    assert base["rows"] == 128
    raw = Path(g11.BASELINE_ROOT, "block_records.csv").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == base["sha256"]
    base2 = g11.load_fixed_baseline(g11.BASELINE_ROOT)  # byte-identical
    assert base2["sha256"] == base["sha256"] and base2["F"] == 1
    assert calls == []


def test_s4_baseline_shape_rejects_nonpaired(fake_root):
    _assert_no_production()
    # Non-128 baseline refused (not pairable); uses fake root only.
    root = fake_root / "badbase"
    root.mkdir(parents=True)
    with (root / "block_records.csv").open("w", newline="",
                                           encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["protocol_accepted",
                                                "verified_exact",
                                                "undetected", "call_idx",
                                                "frame_id"])
        writer.writeheader()
        writer.writerow({"protocol_accepted": "True", "verified_exact": "True",
                         "undetected": "False", "call_idx": 0,
                         "frame_id": 2123})
    with pytest.raises(ValueError, match="!= 128"):
        g11.load_fixed_baseline(str(root))


# T-S5: deterministic replay + admission predicate on fake prefix slices.
def test_s5_deterministic_replay_fake_mother():
    _assert_no_production()
    first, second = _fake_mother(2026094722), _fake_mother(2026094722)
    assert np.array_equal(first["dense"], second["dense"])
    for m in g11.STAGE_MS:
        assert np.array_equal(first["prefixes"][m]["matrix"],
                              second["prefixes"][m]["matrix"])
        assert first["prefixes"][m]["rows"] == (0, int(m))


def test_s5_admission_predicate_prefix_slices():
    _assert_no_production()
    ok, _ = g11.check_nested_prefixes(_fake_mother(2026094722))
    assert ok is True
    bad_missing = _fake_mother(2026094722)
    del bad_missing["prefixes"][108]
    ok, reason = g11.check_nested_prefixes(bad_missing)
    assert ok is False and "108" in reason
    bad_rows = _fake_mother(2026094722)
    bad_rows["prefixes"][108] = {"m": 108, "rows": (8, 108),
                                 "matrix": bad_rows["prefixes"][108]["matrix"]}
    ok, _ = g11.check_nested_prefixes(bad_rows)
    assert ok is False  # non-nested slice rejected
    # Out-of-pair mother seed refused (construction gate).
    with pytest.raises(ValueError, match="outside frozen R11 pair"):
        g11.build_mother(2026094720)
    # Fresh pair disjoint from the frozen ban set (numeric proof).
    banned = ({2026094601, 2026094602}
              | set(range(2026094701, 2026094709))
              | set(range(2026094711, 2026094720))
              | {2026094720, 2026094721})
    assert not (set(g11.MOTHER_SEEDS) & banned)
    assert g11.verify_seed_disjointness()["passed"] is True


# R16: net_secret_bits staged exact integers; old fields + beta frozen; tamper FAILs.
def test_r16_net_secret_bits_staged_frozen_tamper(fake_root):
    _assert_no_production()
    # Single-block staged values: S0 +76; S1 +36; S2 -24; exhausted -664.
    assert g11.net_secret_bits(1, 564, g11.N) == 76
    assert g11.net_secret_bits(1, 604, g11.N) == 36
    assert g11.net_secret_bits(1, 664, g11.N) == -24
    assert g11.net_secret_bits(0, 664, g11.N) == -664
    # Full-bundle staged paths via scripted fakes.
    out = fake_root / "r16s0"
    bundle, _, _ = _run_script(["hit"] * 128, out)
    assert bundle["summary"]["net_secret_bits"] == 128 * 76 == 9728
    assert bundle["summary"]["reconciled_net_bits"] == 128 * 28 * 5  # frozen
    out = fake_root / "r16s1"
    bundle, _, _ = _run_script(["miss", "hit"] * 128, out)
    assert bundle["summary"]["net_secret_bits"] == 128 * 36 == 4608
    assert bundle["summary"]["reconciled_net_bits"] == 128 * 20 * 5  # frozen
    out = fake_root / "r16s2"
    bundle, _, _ = _run_script(["miss", "miss", "hit"] * 128, out)
    assert bundle["summary"]["net_secret_bits"] == 128 * -24 == -3072
    assert bundle["summary"]["reconciled_net_bits"] == 128 * 8 * 5  # frozen
    out = fake_root / "r16exh"
    bundle, _, _ = _run_script(["miss"] * 384, out)
    assert bundle["summary"]["net_secret_bits"] == 128 * -664 == -84992
    # Mixed R11-shape 0/26/61/41: 87*640 - 83432 = -27752.
    assert g11.net_secret_bits(87, 26 * 604 + 61 * 664 + 41 * 664, g11.N) == -27752
    # Beta unchanged on one bundle (recompute identically).
    g11.write_batch_root(bundle)
    s = bundle["summary"]
    leak = s["disclosure_sum"]
    assert s["beta_eff_empirical_primary"] == 1.0 - leak / (128 * 128 * g11.H_FROZEN)
    assert g11.verify_root(str(out)) is True
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    tampered = dict(summary)
    tampered["net_secret_bits"] = int(tampered["net_secret_bits"]) + 1
    (out / "summary.json").write_text(json.dumps(tampered), encoding="utf-8")
    assert g11.verify_root(str(out)) is False
    tampered = dict(summary)
    del tampered["net_secret_bits"]
    (out / "summary.json").write_text(json.dumps(tampered), encoding="utf-8")
    assert g11.verify_root(str(out)) is False
