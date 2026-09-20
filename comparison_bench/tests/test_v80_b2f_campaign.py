"""V80 B2F soft-marginal campaign executor tests (EXPLORE, FAKE-ONLY).

Frozen spec: B2F_EXPERIMENT_PACKET_20260921.md + B2F_EXPERIMENT_PROMPT_
20260921.md (G-B2F, arms F208|F202, 240 blocks). Every test injects fake
construct/decode/clock/rss/writer or synthetic dict bundles — zero
production campaign runs, zero campaign disk writes (the writer is an
in-memory capture; resume shims use tmp_path and are removed by pytest).
Two dry-construction recording tests (T5, ~10 s) measure the REAL
constructor in-memory for F208/F202 (allowed: pins recorded, no writes,
no decodes). The dry 1-block probe (T12) runs the REAL frozen bundle +
REAL sampler + REAL marginal formula + REAL XOR-centering with a FAKE
kernel (no production decode at scale) and reports the measured
``prior_entropy_bits``.
"""
import inspect
import json
import os

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import (
    v80_b2f_campaign as c,
)


def _fake_bundle(seed=7):
    rng = np.random.default_rng(seed)
    g1 = rng.random((32, 1024)) + 0.01
    g1 = g1 / g1.sum(axis=0, keepdims=True)
    g2 = rng.random((32, 32, 1024)) + 0.01
    g2 = g2 / g2.sum(axis=1, keepdims=True)
    return {"g1": g1, "g2": g2,
            "p_b": np.full(1024, 1.0 / 1024), "source": "2M"}


def _fake_construct(arm):
    # Mirrors the frozen pin table (packet §3/X3): fc=0/rank-full both
    # arms; girth recorded (8 here); stable triples exercise
    # twice-identical. Signature mirrors production construct_arm(arm,
    # seed, max_trials) and asserts the gate forwards the B2F arm id.
    spec = c.ARMS[arm]
    assert spec["source_arm"] in ("A208", "A202")

    def _build(arm_in, seed, max_trials):
        assert arm_in == arm
        assert (seed, max_trials) == (2026092001, 20)
        m = int(spec["m"])
        return {"four_cycles": 0, "min_girth": 8, "rank": m,
                "family": "peg-irregular", "n": 1024, "m": m,
                "source_arm": spec["source_arm"],
                "triples": [(0, 0, 1), (1, 1, 2)],
                "total_sockets": 2048, "parallel_edges": 0}

    return _build


def _decode_ok(construction, seed):
    return {"status": "success", "iterations": 12,
            "reconstruction_ok": True, "exact_match": True,
            "u1_source": "MARGINAL", "prior_entropy_bits": 0.0,
            "u1_mismatches": 8}


def _decode_fail(construction, seed):
    return {"status": "max_iter_reached", "iterations": 300,
            "reconstruction_ok": False, "exact_match": False,
            "u1_source": "MARGINAL", "prior_entropy_bits": 0.0,
            "u1_mismatches": 8}


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


class MemWriter:
    """In-memory capture: path -> blob. Never touches disk."""

    def __init__(self):
        self.store = {}
        self.calls = 0

    def __call__(self, root, files):
        self.calls += 1
        for name, blob in files.items():
            self.store[f"{root}/{name}"] = blob


def _run(root, writer, clock, decode_fn, arm="F208", **kw):
    return c.execute(root=root, arm=arm,
                     construct_fn=_fake_construct(arm),
                     decode_fn=decode_fn, clock=clock,
                     rss_fn=lambda: 0, writer=writer, **kw)


# T1: dual-flag gate + arm/root/de-label refusal matrix (rc2). ------------
def test_t1_dual_flag_refusal():
    with pytest.raises(c.Refusal):
        c.main([])
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--arm", "F208",
                "--root", "workspace/b2f_deadbeef"])
    with pytest.raises(c.Refusal):
        c.main(["--execution-authorized", "--arm", "F208",
                "--root", "workspace/b2f_deadbeef"])
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--execution-authorized",
                "--arm", "F208",
                "--root", "workspace/wrong_deadbeef"])
    for bad_prefix in ("workspace/o1_deadbeef", "workspace/o1r_deadbeef",
                       "workspace/p0_deadbeef", "workspace/l1b_deadbeef",
                       "workspace/s2c_deadbeef", "workspace/b2e_deadbeef",
                       "workspace/b2f"):
        with pytest.raises(c.Refusal):
            c.main(["--execute-real", "--execution-authorized",
                    "--arm", "F208", "--root", bad_prefix])
    for bad_arm in ("A208", "B208", "F200", "f208", ""):
        with pytest.raises(c.Refusal):
            c.main(["--execute-real", "--execution-authorized",
                    "--arm", bad_arm, "--root", "workspace/b2f_deadbeef"])
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--execution-authorized",
                "--arm", "F208", "--root", "workspace/b2f_aaaaaaaa",
                "--resume-from", "workspace/b2f_bbbbbbbb"])
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--execution-authorized",
                "--arm", "F208", "--root", "workspace/b2f_deadbeef",
                "--de-label", "maybe"])
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--execution-authorized",
                "--arm", "F208", "--root", "workspace/b2f_deadbeef",
                "--n-blocks", "0"])
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--execution-authorized",
                "--arm", "F208", "--root", "workspace/b2f_deadbeef",
                "--construct-trials", "0"])
    # Frozen-configuration refusals: B2F has EXACTLY ONE runnable config;
    # any science-input deviation refuses rc=2 BEFORE any root contact
    # (packet §6 STOP). NOTE: no test ever passes the dual-flag gate with
    # a valid workspace/b2f_ root — that path is the real campaign and is
    # never invoked from tests (repo rule: never invoke production work
    # implicitly from tests).
    for extra in (["--construct-seed", "2026092011"],
                  ["--construct-trials", "10"],
                  ["--block-base", "2026095501"],
                  ["--n-blocks", "60"]):
        with pytest.raises(c.Refusal):
            c.main(["--execute-real", "--execution-authorized",
                    "--arm", "F208", "--root", "workspace/b2f_deadbeef"]
                   + extra)


# T2: root absent/present matrix + forbidden trees. ------------------------
def test_t2_root_absent_present_matrix(tmp_path):
    w, clk = MemWriter(), FakeClock()
    mf = _run("/tmp/opencode/b2f_fake_absent_01", w, clk, _decode_ok,
              max_blocks=1)
    assert mf["verdict"] == "PROBE-truncated"
    with pytest.raises(c.Refusal):
        _run(str(tmp_path), MemWriter(), FakeClock(), _decode_ok,
             max_blocks=1)
    with pytest.raises(c.Refusal):
        c.execute(root="/tmp/opencode/b2f_fake_absent_02", arm="F208",
                  resume_from="/tmp/opencode/b2f_fake_absent_02",
                  construct_fn=_fake_construct("F208"),
                  decode_fn=_decode_ok,
                  clock=FakeClock(), rss_fn=lambda: 0, writer=MemWriter())
    with pytest.raises(c.Refusal):
        c.execute(root="/tmp/opencode/b2f_fake_a", arm="F208",
                  resume_from="/tmp/opencode/b2f_fake_b",
                  construct_fn=_fake_construct("F208"),
                  decode_fn=_decode_ok,
                  clock=FakeClock(), rss_fn=lambda: 0, writer=MemWriter())
    for bad in ("/tmp/opencode/results/b2f_fake_x",
                "/tmp/opencode/comparison_bench/outputs_comparison/"
                "b2f_fake_x"):
        with pytest.raises(c.Refusal):
            c.execute(root=bad, arm="F208",
                      construct_fn=_fake_construct("F208"),
                      decode_fn=_decode_ok, clock=FakeClock(),
                      rss_fn=lambda: 0, writer=MemWriter(), max_blocks=1)


# T3: arms table + frozen accounting constants. ---------------------------
@pytest.mark.parametrize("arm,m,leak,f_super,headroom", [
    ("F208", 208, 1104.0, 1.294947, 4.31),
    ("F202", 202, 1074.0, 1.259759, 34.31),
])
def test_t3_arms_table_and_accounting(arm, m, leak, f_super, headroom):
    assert c.ARMS[arm]["m"] == m
    assert c.ARMS[arm]["source_arm"] == "A208" if arm == "F208" \
        else c.ARMS[arm]["source_arm"] == "A202"
    assert c.ARMS[arm]["lambda"] == {2: 1.0}
    assert c.ARMS[arm]["leak_bits"] == leak
    basis = c.leak_basis(arm)
    assert basis["m"] == m and basis["leak_bits"] == leak
    assert basis["f_super_basis"] == pytest.approx(f_super, abs=1e-6)
    assert "NEVER assume zero" in basis["f_super_label"]
    assert "(5m+64)/852.544" in basis["f_super_rule"]
    assert basis["headroom_bits"] == pytest.approx(headroom, abs=0.01)
    assert "would fail gate (b)" in basis["headroom_line"]
    assert basis["d_u1"] == 0.0
    assert "NEVER-ASSUME-ZERO" in basis["d_u1_label"]
    assert c.MAX_ITER == 300
    assert c.B2F_BLOCK_BASE == 2026095601
    assert c.B2F_N_BLOCKS == 240
    assert c.B2F_CONSTRUCT_SEED == 2026092001
    assert c.B2F_MAX_TRIALS == 20
    assert c.B2F_N == 1024
    assert c.CONTENT_BITS == pytest.approx(852.544, abs=1e-3)
    assert c.GENIE_L2_CONTENT_BITS == pytest.approx(826.266, abs=0.01)
    assert c.L1_CONTENT_BITS == pytest.approx(26.278, abs=0.01)
    assert c.fail_bar(240) == 12
    assert c.U1_SOURCE == "MARGINAL"
    assert c.CAMPAIGN_LABEL == "B2F-soft-marginal"
    assert c.D_U1 == 0.0


def test_t3_f_super_arithmetic_matches_frozen_figures():
    # Packet §4 frozen anchors on the UNCHANGED O1 basis.
    assert c.f_super_du0("F208") == pytest.approx(1.294947, abs=1e-6)
    assert c.f_super_du0("F202") == pytest.approx(1.259759, abs=1e-6)
    # Both arms pass gate (b) by construction (accounting identity).
    assert c.f_super_du0("F208") <= c.F_SUPER_MAX
    assert c.f_super_du0("F202") <= c.F_SUPER_MAX
    # Headroom discriminates: F208 has ~4.31 b, F202 ~34.31 b.
    assert (c.F_SUPER_MAX * c.CONTENT_BITS
            - c.ARMS["F208"]["leak_bits"]) == pytest.approx(4.307492864,
                                                             abs=1e-9)
    assert (c.F_SUPER_MAX * c.CONTENT_BITS
            - c.ARMS["F202"]["leak_bits"]) == pytest.approx(34.307492864,
                                                             abs=1e-9)
    # Chain-rule parity anchors (report-only observation, packet §1).
    assert (c.CONTENT_BITS - c.L1_CONTENT_BITS
            == pytest.approx(c.GENIE_L2_CONTENT_BITS, abs=1e-6))


def test_t3_unknown_arm_refuses():
    for bad in ("A208", "B208", "F200", "f208", ""):
        with pytest.raises(c.Refusal):
            c.block_seed(bad, 0)
        with pytest.raises(c.Refusal):
            c.leak_basis(bad)
        with pytest.raises(c.Refusal):
            c.f_super_du0(bad)
        with pytest.raises(c.Refusal):
            c.construct_arm(bad)
    calls = []

    def _counting(construction, seed):
        calls.append(seed)
        return _decode_ok(construction, seed)

    with pytest.raises(c.Refusal) as exc:
        c.execute(root="/tmp/opencode/b2f_fake_badarm", arm="A208",
                  construct_fn=_fake_construct("F208"),
                  decode_fn=_counting, clock=FakeClock(),
                  rss_fn=lambda: 0, writer=MemWriter(), max_blocks=1)
    assert exc.value.code == 2
    assert calls == []


# T4: construct gate — fc/rank/twice gated, girth recorded. ----------------
def test_t4_gate_pass_fake_mimic():
    con = c._construct_gate("F208", _fake_construct("F208"), 2026092001, 20)
    assert con["m"] == 208 and con["rank"] == 208
    assert con["four_cycles"] == 0
    assert con["min_girth"] == 8  # recorded
    assert con["measured_girth"] == 8
    assert con["construct_seed"] == 2026092001
    assert con["construct_trials"] == 20
    assert con["source_arm"] == "A208"


def test_t4_girth_recorded_not_gated():
    def _g4(arm_in, seed, max_trials):
        assert (seed, max_trials) == (2026092001, 20)
        return {"four_cycles": 0, "min_girth": 4, "rank": 202,
                "family": "peg-irregular", "n": 1024, "m": 202,
                "triples": [(0, 0, 1)]}

    con = c._construct_gate("F202", _g4, 2026092001, 20)
    assert con["min_girth"] == 4  # recorded, never gated
    assert con["measured_girth"] == 4


@pytest.mark.parametrize("pin", ["fc", "rank", "twice", "status"])
def test_t4_pin_mismatch_stop_blocked(pin, capsys):
    def _bad(arm_in, seed, max_trials):
        _bad.n += 1
        rec = {"four_cycles": 0, "min_girth": 8, "rank": 208,
               "family": "peg-irregular", "n": 1024, "m": 208,
               "triples": [(0, _bad.n if pin == "twice" else 0, 1)]}
        if pin == "fc":
            rec["four_cycles"] = 2
        elif pin == "rank":
            rec["rank"] = 207
        elif pin == "status":
            rec["status"] = "frozen_failure"
        return rec
    _bad.n = 0
    calls = []

    def _counting(construction, seed):
        calls.append(seed)
        return _decode_ok(construction, seed)

    with pytest.raises(c.Refusal) as exc:
        c.execute(root="/tmp/opencode/b2f_fake_pinbad", arm="F208",
                  construct_fn=_bad,
                  decode_fn=_counting, clock=FakeClock(),
                  rss_fn=lambda: 0, writer=MemWriter(), max_blocks=1)
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "STOP-BLOCKED" in err
    assert "F208" in err
    assert calls == []  # fail closed pre-decode


# T5: dry-construct pins ×2 REAL (allowed, in-memory, no writes). ----------
_MEASURED: dict[str, dict] = {}


def _measured(arm):
    if arm not in _MEASURED:
        a = c.construct_arm(arm, 2026092001, 20)
        b = c.construct_arm(arm, 2026092001, 20)
        sa = sorted(tuple(map(int, t)) for t in a["triples"])
        sb = sorted(tuple(map(int, t)) for t in b["triples"])
        assert sa == sb  # construct-twice-identical holds
        _MEASURED[arm] = a
    return _MEASURED[arm]


@pytest.mark.parametrize("arm,m", [("F208", 208), ("F202", 202)])
def test_t5_dry_construct_pins_recorded(arm, m):
    code = _measured(arm)
    assert code["n"] == 1024 and code["m"] == m
    assert code["rank"] == m  # rank-full holds both arms
    assert code["four_cycles"] == 0  # fc==0 gate-clean (both arms)
    assert code["min_girth"] == 8  # recorded-not-gated (measured)
    assert code["family"] == "peg-irregular"
    assert code.get("status", "ok") == "ok"
    assert code["source_arm"] == ("A208" if arm == "F208" else "A202")


@pytest.mark.parametrize("arm,m", [("F208", 208), ("F202", 202)])
def test_t5b_real_pins_through_real_gate(arm, m):
    # Production binding via the same gate path execute() uses: a spy
    # delegating to the real constructor asserts the B2F arm id + frozen
    # seed/trials arrive first, and the REAL measured pins pass the gate.
    seen = []

    def _spy(arm_in, seed, max_trials):
        seen.append((arm_in, seed, max_trials))
        return c.construct_arm(arm_in, seed, max_trials)

    con = c._construct_gate(arm, _spy)
    assert seen[0] == (arm, 2026092001, 20)
    assert seen[1] == (arm, 2026092001, 20)  # construct-twice
    assert con["four_cycles"] == 0
    assert con["rank"] == m
    assert con["min_girth"] == 8
    assert con["source_arm"] == ("A208" if arm == "F208" else "A202")


# T6: the FROZEN marginal formula vs a manual einsum contraction. ---------
def _manual_marginal(g1, g2, b):
    """Reference: marg[i,v] = Σ_u γ1(u,b_i)·γ2(v|b_i,u), then per-row
    renormalize (row-sum guard; non-positive/non-finite → delta-at-0)."""
    n = len(b)
    out = np.empty((n, 32), dtype=np.float64)
    for i in range(n):
        bb = int(b[i])
        row = np.array([sum(float(g1[u, bb]) * float(g2[u, v, bb])
                            for u in range(32)) for v in range(32)])
        s = float(row.sum())
        if (not np.all(np.isfinite(row))) or (not np.isfinite(s)) or s <= 0.0:
            z = np.zeros(32)
            z[0] = 1.0
            out[i] = z
        else:
            out[i] = row / s
    return out


def test_t6_marginal_formula_matches_manual_contraction():
    rng = np.random.default_rng(17)
    g1 = rng.random((32, 1024)) + 0.01
    g1 = g1 / g1.sum(axis=0, keepdims=True)
    g2 = rng.random((32, 32, 1024)) + 0.01
    g2 = g2 / g2.sum(axis=1, keepdims=True)
    bundle = {"g1": g1, "g2": g2, "p_b": np.full(1024, 1.0 / 1024)}
    b = np.array([0, 5, 1023, 77, 512, 3], dtype=np.int64)
    marg = c.marginal_prior_l2(bundle, b)
    assert marg.shape == (6, 32)
    manual = _manual_marginal(g1, g2, b)
    assert np.allclose(marg, manual, atol=1e-12)
    # bind-normalized bundle ⇒ rows already sum to 1±1e-9; the guard
    # only renormalizes accumulation noise.
    assert np.allclose(marg.sum(axis=1), 1.0, atol=1e-12)
    assert np.all(marg >= 0.0)
    # Shape/domain guards (fail closed, rc=2).
    with pytest.raises(c.Refusal):
        c.marginal_prior_l2(bundle, np.array([1024]))
    with pytest.raises(c.Refusal):
        c.marginal_prior_l2(bundle, np.zeros((2, 2), dtype=np.int64))
    with pytest.raises(c.Refusal):
        c.marginal_prior_l2({"g1": np.zeros((31, 1024)), "g2": g2},
                            np.array([0]))
    with pytest.raises(c.Refusal):
        c.marginal_prior_l2({"g1": g1, "g2": np.zeros((32, 31, 1024))},
                            np.array([0]))


def test_t6_row_renormalize_guard_and_delta_at_zero():
    # Column 0 carries an unnormalized γ1 column (sum 64): the marginal
    # row must be divided by its row sum (guard), NOT trusted as-is.
    g1 = np.zeros((32, 1024))
    g1[:, 0] = 2.0                      # column sum 64
    g1[0, 1] = 1.0                      # normalized one-hot column
    g1[:, 2] = 0.0                      # zero-mass column → delta-at-0
    g2 = np.full((32, 32, 1024), 1.0 / 32)
    g2[3, :, 0] = 0.0
    g2[3, 7, 0] = 1.0                   # deterministic conditional
    g2[:, :, 2] = np.nan                # non-finite row → delta-at-0
    bundle = {"g1": g1, "g2": g2, "p_b": np.full(1024, 1.0 / 1024)}
    b = np.array([0, 1, 2], dtype=np.int64)
    marg = c.marginal_prior_l2(bundle, b)
    # Row 0: Σ_u γ1(u,0)·γ2(v|0,u) with γ1≡2, g2[3,·,0]=δ_7:
    #   raw v=7  → 31·(2/32) + 2 = 3.9375
    #   raw v≠7  → 31·(2/32)     = 1.9375   (u=3 contributes 0)
    #   raw row sum = 64 ⇒ the guard divides by 64.
    assert np.allclose(marg[0, 7], 3.9375 / 64, atol=1e-12)
    assert np.allclose(np.delete(marg[0], 7), 1.9375 / 64, atol=1e-12)
    assert np.allclose(marg[0].sum(), 1.0, atol=1e-12)
    # Row 1: one-hot γ1 + uniform γ2 ⇒ uniform 1/32 (already normalized)
    assert np.allclose(marg[1], 1.0 / 32, atol=1e-12)
    # Row 2: zero-mass γ1 column ⇒ all-zero marginal row ⇒ non-positive
    # row sum ⇒ delta-at-0 fallback (symbol 0).
    assert np.count_nonzero(marg[2]) == 1
    assert marg[2, 0] == 1.0
    # The d7 uniform-1/32 fallback is NOT adopted: a zero-mass row is
    # delta-at-0, not uniform.
    assert not np.allclose(marg[2], 1.0 / 32)
    # Non-finite marginal entries likewise fall back to delta-at-0.
    g2n = np.full((32, 32, 1024), 1.0 / 32)
    g2n[:, :, 5] = np.nan
    g1n = np.zeros((32, 1024))
    g1n[0, 5] = 1.0
    bundle_n = {"g1": g1n, "g2": g2n, "p_b": np.full(1024, 1.0 / 1024)}
    marg_n = c.marginal_prior_l2(bundle_n, np.array([5], dtype=np.int64))
    assert np.count_nonzero(marg_n[0]) == 1 and marg_n[0, 0] == 1.0


def test_t6_xor_centering_identity():
    rng = np.random.default_rng(23)
    g1 = rng.random((32, 1024)) + 0.01
    g1 = g1 / g1.sum(axis=0, keepdims=True)
    g2 = rng.random((32, 32, 1024)) + 0.01
    g2 = g2 / g2.sum(axis=1, keepdims=True)
    bundle = {"g1": g1, "g2": g2, "p_b": np.full(1024, 1.0 / 1024)}
    b = np.array([0, 9, 1023, 511, 42], dtype=np.int64)
    y = np.asarray(b & 31, dtype=np.int64)
    marg = c.marginal_prior_l2(bundle, b)
    prior = c.s2c.center_rows_prior(marg, y)
    assert prior.shape == (5, 32)
    # pi_i(e) = marg[i, y_i XOR e] (v28 _center_rows; GF32 char-2 = XOR)
    for i in range(5):
        for e in range(32):
            assert prior[i, e] == pytest.approx(marg[i, int(y[i]) ^ e],
                                                abs=1e-15)
    # XOR-centering is a column permutation ⇒ commutes with the u1-sum
    # and preserves row entropy (the report-only observation is
    # permutation invariant).
    assert c.prior_entropy_bits(prior) == pytest.approx(
        c.prior_entropy_bits(marg), abs=1e-9)


# T7: report-only prior entropy + u1 mismatch measurement. ----------------
def test_t7_prior_entropy_bits():
    one_hot = np.zeros((4, 32))
    one_hot[:, 0] = 1.0
    assert c.prior_entropy_bits(one_hot) == pytest.approx(0.0, abs=1e-12)
    uni = np.full((3, 32), 1.0 / 32)
    assert c.prior_entropy_bits(uni) == pytest.approx(3 * 5.0, abs=1e-12)
    half = np.zeros((1, 32))
    half[0, 0] = half[0, 1] = 0.5
    assert c.prior_entropy_bits(half) == pytest.approx(1.0, abs=1e-12)
    # zero-mass entries contribute 0 (1e-300 floor guard)
    sparse = np.zeros((1, 32))
    sparse[0, 5] = 1.0
    assert c.prior_entropy_bits(sparse) == pytest.approx(0.0, abs=1e-12)
    with pytest.raises(c.Refusal):
        c.prior_entropy_bits(np.zeros((2, 31)))


def test_t7_mismatch_counting():
    u1 = np.array([0, 1, 2, 3, 31, 5, 5, 5], dtype=np.int64)
    assert c.u1_mismatches(u1, u1.copy()) == 0
    assert c.u1_mismatches(u1, np.zeros(8, dtype=np.int64)) == 7
    assert c.u1_mismatches(u1, (u1 + 1) % 32) == 8
    with pytest.raises(c.Refusal):
        c.u1_mismatches(np.zeros(4, dtype=np.int64),
                        np.zeros(5, dtype=np.int64))
    with pytest.raises(c.Refusal):
        c.u1_mismatches(np.zeros((2, 2), dtype=np.int64),
                        np.zeros((2, 2), dtype=np.int64))


def test_t7_map_u1_is_argmax_over_g1():
    bundle = _fake_bundle(seed=29)
    rng = np.random.default_rng(31)
    b = rng.choice(1024, size=129)
    hat = c.map_u1(bundle, b)
    g1 = bundle["g1"]
    manual = np.array([int(np.argmax(g1[:, int(bb)])) for bb in b])
    assert np.array_equal(hat, manual)
    assert hat.min() >= 0 and hat.max() < 32
    with pytest.raises(c.Refusal):
        c.map_u1(bundle, np.array([1024]))
    with pytest.raises(c.Refusal):
        c.map_u1(bundle, np.zeros((2, 2), dtype=np.int64))


# T8: û1/genie NOT used — posterior_rows_l2 never called (capture). --------
def test_t8_genie_and_map_u1_never_used(monkeypatch):
    n = 16
    b_fix = np.arange(n, dtype=np.int64) % 1024
    u1_fix = np.zeros(n, dtype=np.int64)   # GENIE true-u1 ≡ 0
    u2_fix = np.full(n, 3, dtype=np.int64)
    g1 = np.zeros((32, 1024))
    g1[9, :] = 1.0                          # argmax û1 ≡ 9 (≠ genie)
    g2 = np.full((32, 32, 1024), 1.0 / 32)
    bundle = {"g1": g1, "g2": g2, "p_b": np.full(1024, 1.0 / 1024)}
    captured = {}

    def _fake_triple(bundle, nn, rng):
        assert nn == n
        return (b_fix, u1_fix, u2_fix)

    def _fake_dense(triples, nn, mm, field):
        return np.zeros((mm, nn), dtype=np.int64)

    def _fake_syn(field, dense, vec):
        assert len(vec) == n
        return [0] * dense.shape[0]

    def _fake_posterior(field, y, matrix, s_x, prior, max_iter, **kw):
        captured["y"] = list(y)
        captured["prior"] = np.asarray(prior, dtype=np.float64).copy()
        captured["prior_shape"] = tuple(np.asarray(prior).shape)
        captured["max_iter"] = max_iter
        return {"status": "success", "iterations": 9,
                "reconstruction_ok": True, "x_hat": list(u2_fix)}

    def _forbidden_l2(bundle, b_vec, u1_vec):
        raise AssertionError("posterior_rows_l2 (genie/MAP u1 path) "
                             "must NOT be used by B2F")

    monkeypatch.setattr(c.s2c, "empirical_triple_sampler", _fake_triple)
    monkeypatch.setattr(c.peg, "sparse_to_dense", _fake_dense)
    monkeypatch.setattr(c.fftqspa, "syndrome_of", _fake_syn)
    monkeypatch.setattr(c.s2c, "posterior_rows_l2", _forbidden_l2)
    monkeypatch.setattr(c.v28, "decode_error_domain_posterior",
                        _fake_posterior)
    out = c.decode_block_marginal({"triples": [(0, 0, 1)], "n": n, "m": 8},
                                  2026095601, bundle, n, 8)
    # The decoder prior is the marginal formula (uniform here), centered
    # on y=b&31 — never γ2(·|b,û1) and never γ2(·|b,u1_true).
    assert captured["prior_shape"] == (n, 32)
    assert np.allclose(captured["prior"], 1.0 / 32, atol=1e-12)
    assert captured["max_iter"] == 300
    assert captured["y"] == list(b_fix & 31)  # Bob L2 half (bits 4..0)
    assert out["u1_source"] == "MARGINAL"
    assert out["u1_mismatches"] == n          # genie 0 vs argmax 9
    assert out["prior_entropy_bits"] == pytest.approx(n * 5.0, abs=1e-9)
    assert out["exact_match"] is True         # x̂==u2
    assert out["max_iter"] == 300
    assert "REMOVED" in out["l1_conditioning"]
    assert "no argmax" in out["l1_conditioning"]


def test_t8_module_source_has_no_genie_or_argmax_decode_path():
    src = inspect.getsource(c)
    bare = [ln for ln in src.splitlines()
            if "decode_error_domain(" in ln
            and "decode_error_domain_posterior" not in ln
            and "NEVER" not in ln and "scalar" not in ln]
    assert bare == []
    # No CALL to the genie/MAP row helper anywhere in the module (the
    # name may appear in prose documenting the frozen zero-mass
    # semantics, but it is never invoked).
    assert "posterior_rows_l2(" not in src


def test_t8_construction_nm_wiring_guard():
    bundle = _fake_bundle()
    with pytest.raises(c.Refusal):
        c.decode_block_marginal({"triples": [], "n": 1024, "m": 208},
                                2026095601, bundle, 1024, 202)
    with pytest.raises(c.Refusal):
        c.decode_block_marginal({"triples": [], "n": 256, "m": 208},
                                2026095601, bundle, 1024, 208)
    with pytest.raises(c.Refusal):
        c.decode_block_marginal({"triples": [], "n": 1024, "m": 208},
                                True, bundle, 1024, 208)


# T9: gates — all-ok PASS; early-stop; bar edge; budget terminal. ----------
@pytest.mark.parametrize("arm", ["F208", "F202"])
def test_t9_all_ok_pass_and_manifest(arm):
    w, clk = MemWriter(), FakeClock()
    root = f"/tmp/opencode/b2f_fake_allok_{arm.lower()}"
    seen = []

    def _rec(construction, seed):
        seen.append(seed)
        return _decode_ok(construction, seed)

    mf = c.execute(root=root, arm=arm,
                   construct_fn=_fake_construct(arm),
                   decode_fn=_rec, clock=clk,
                   rss_fn=lambda: 0, writer=w)
    assert mf["campaign"] == "B2F-soft-marginal"
    assert mf["arm"] == arm
    assert mf["verdict"] == "PASS"
    assert mf["failures"] == 0
    assert mf["blocks_completed"] == 240
    assert mf["ledger"] == {"decodes": 240, "blocks_completed": 240}
    assert mf["fer_blocks"] == pytest.approx(0.0)
    assert mf["fail_bar"] == 12
    assert mf["pass_bar"] == "block FER<=5% (fails/240<=12)"
    # Gate (b) sits on the unchanged O1 basis (accounting identity).
    assert mf["f_super"] == pytest.approx(c.f_super_du0(arm), abs=1e-12)
    assert mf["d_u1"]["value"] == 0.0
    assert mf["prior_entropy"]["mean_bits"] == 0.0
    assert mf["prior_entropy"]["u1_mismatches_mean"] == 8.0
    assert mf["quarter_tally"]["quarters_complete"] == 4
    assert mf["quarter_tally"]["quarters_le3"] == 4
    assert w.calls == 241  # 240 block checkpoints + 1 final
    assert mf["verify"] == {"pins_ok": True, "ledger_ok": True,
                            "rows_ok": True}
    rows = json.loads(w.store[f"{root}/rows.json"])
    assert len(rows) == 240
    assert [r["block"] for r in rows] == list(range(240))
    assert seen[0] == 2026095601 and seen[-1] == 2026095840
    assert all(r["u1_source"] == "MARGINAL" for r in rows)
    assert all(r["d_u1"] == 0.0 for r in rows)
    mani = json.loads(w.store[f"{root}/manifest.json"])
    assert mani["seeds"]["block_base"] == 2026095601
    assert "STOP-BLOCKED" in mani["construct"]["pins"]
    assert "recorded-not-gated" in mani["construct"]["pins"]
    assert "NO independence claim" in mani["seeds"]["paired_note"]
    assert "REMOVED" in mani["decoder"]["l1_conditioning"]
    assert "no D1 ceiling label" in mani["u1_source"]["genie_ceiling"]
    assert "(5m+64)/852.544" in mani["f_bar"]


def test_t9_early_stop_thirteenth_fail():
    w, clk = MemWriter(), FakeClock()
    mf = _run("/tmp/opencode/b2f_fake_early240", w, clk, _decode_fail)
    assert mf["verdict"] == "FAIL-early-stop"
    assert mf["blocks_completed"] == 13
    assert mf["failures"] == 13
    assert mf["n_blocks"] == 240
    assert mf["fail_bar"] == 12
    assert mf["next_block"] == 13
    assert mf["partial"] is True
    assert mf["quarter_tally"]["quarters_complete"] == 0  # partial q0


def test_t9_bar_boundary_twelve_fails_pass():
    state = {"k": 0}

    def _twelve_then_ok(construction, seed):
        state["k"] += 1
        if state["k"] <= 12:
            return _decode_fail(construction, seed)
        return _decode_ok(construction, seed)

    w, clk = MemWriter(), FakeClock()
    mf = _run("/tmp/opencode/b2f_fake_bar12", w, clk, _twelve_then_ok)
    assert mf["verdict"] == "PASS"
    assert mf["failures"] == 12
    assert mf["blocks_completed"] == 240


def test_t9_budget_terminal_noresume(tmp_path):
    w, clk = MemWriter(), FakeClock()

    def _overrun(construction, seed):
        clk.t += 301.0
        return _decode_ok(construction, seed)

    mf = _run("/tmp/opencode/b2f_fake_overrun", w, clk, _overrun,
              max_blocks=1)
    assert mf["verdict"] == "FAIL(budget)"
    assert mf["partial"] is True
    rows = json.loads(w.store["/tmp/opencode/b2f_fake_overrun/rows.json"])
    assert len(rows) == 1 and rows[0]["status"] == "overrun"
    root = str(tmp_path / "b2f_fake_budget_noresume")
    os.makedirs(root, exist_ok=True)
    with open(f"{root}/manifest.json", "w") as fh:
        fh.write(w.store["/tmp/opencode/b2f_fake_overrun/manifest.json"])
    with open(f"{root}/rows.json", "w") as fh:
        fh.write(w.store["/tmp/opencode/b2f_fake_overrun/rows.json"])
    with pytest.raises(c.Refusal):
        c.execute(root=root, arm="F208", resume_from=root,
                  construct_fn=_fake_construct("F208"),
                  decode_fn=_decode_ok, clock=FakeClock(),
                  rss_fn=lambda: 0, writer=MemWriter())


def test_t9_malformed_decode_output_refuses():
    def _no_pe(construction, seed):
        out = _decode_ok(construction, seed)
        del out["prior_entropy_bits"]
        return out

    with pytest.raises(c.Refusal):
        _run("/tmp/opencode/b2f_fake_nope", MemWriter(), FakeClock(),
             _no_pe, max_blocks=1)

    def _no_km(construction, seed):
        out = _decode_ok(construction, seed)
        del out["u1_mismatches"]
        return out

    with pytest.raises(c.Refusal):
        _run("/tmp/opencode/b2f_fake_nokm", MemWriter(), FakeClock(),
             _no_km, max_blocks=1)


# T10: checkpoint/resume — one wall-partial; 2nd/arm-swap refuses. ---------
def test_t10_resume_continuation_single_wall_window(tmp_path):
    root = str(tmp_path / "b2f_fake_resume")
    w1, clk1 = MemWriter(), FakeClock()

    def _advancing(construction, seed):
        clk1.t += 100.0
        return _decode_ok(construction, seed)

    part = c.execute(root=root, arm="F208",
                     construct_fn=_fake_construct("F208"),
                     decode_fn=_advancing, clock=clk1,
                     rss_fn=lambda: 0, writer=w1)
    assert part["verdict"] == "INCOMPLETE-wall"
    assert part["blocks_completed"] == 37
    assert part["next_block"] == 37
    assert part["ledger"]["decodes"] == 37
    assert part["resume"] == {"continuations_used": 0,
                              "max_continuations": 1}
    rows_p = json.loads(w1.store[f"{root}/rows.json"])
    w2, clk2 = MemWriter(), FakeClock()

    def _fast(construction, seed):
        clk2.t += 1.0
        return _decode_ok(construction, seed)

    os.makedirs(root, exist_ok=True)
    with open(f"{root}/manifest.json", "w") as fh:
        fh.write(w1.store[f"{root}/manifest.json"])
    with open(f"{root}/rows.json", "w") as fh:
        fh.write(w1.store[f"{root}/rows.json"])
    done = c.execute(root=root, arm="F208", resume_from=root,
                     construct_fn=_fake_construct("F208"),
                     decode_fn=_fast, clock=clk2,
                     rss_fn=lambda: 0, writer=w2)
    assert done["verdict"] == "PASS"
    assert done["ledger"]["decodes"] == 240
    assert done["blocks_completed"] == 240
    assert len(done["wall_windows"]) == 2
    assert done["resume"] == {"continuations_used": 1,
                              "max_continuations": 1}
    rows_d = json.loads(w2.store[f"{root}/rows.json"])
    assert (json.dumps(rows_d[:37], sort_keys=True)
            == json.dumps(rows_p, sort_keys=True))
    # A second resume (completed PASS manifest) refuses with zero decodes.
    with open(f"{root}/manifest.json", "w") as fh:
        fh.write(w2.store[f"{root}/manifest.json"])
    with open(f"{root}/rows.json", "w") as fh:
        fh.write(w2.store[f"{root}/rows.json"])
    calls = []

    def _counting(construction, seed):
        calls.append(seed)
        return _decode_ok(construction, seed)

    with pytest.raises(c.Refusal) as exc:
        c.execute(root=root, arm="F208", resume_from=root,
                  construct_fn=_fake_construct("F208"),
                  decode_fn=_counting, clock=FakeClock(),
                  rss_fn=lambda: 0, writer=MemWriter())
    assert exc.value.code == 2
    assert calls == []


def test_t10_resume_arm_mismatch_refuses(tmp_path):
    root = str(tmp_path / "b2f_fake_resume_swap")
    w1, clk1 = MemWriter(), FakeClock()

    def _advancing(construction, seed):
        clk1.t += 100.0
        return _decode_ok(construction, seed)

    part = c.execute(root=root, arm="F208",
                     construct_fn=_fake_construct("F208"),
                     decode_fn=_advancing, clock=clk1,
                     rss_fn=lambda: 0, writer=w1)
    assert part["verdict"] == "INCOMPLETE-wall"
    os.makedirs(root, exist_ok=True)
    with open(f"{root}/manifest.json", "w") as fh:
        fh.write(w1.store[f"{root}/manifest.json"])
    with open(f"{root}/rows.json", "w") as fh:
        fh.write(w1.store[f"{root}/rows.json"])
    with pytest.raises(c.Refusal):
        c.execute(root=root, arm="F202", resume_from=root,
                  construct_fn=_fake_construct("F202"),
                  decode_fn=_decode_ok, clock=FakeClock(),
                  rss_fn=lambda: 0, writer=MemWriter())


# T11: no writes outside root; per-block column schema; prefix gate. -------
def test_t11_no_writes_outside_root_and_csv():
    assert c._allows_root("workspace/b2f_deadbeef")
    assert not c._allows_root("workspace/o1_deadbeef")
    assert not c._allows_root("workspace/o1r_deadbeef")
    assert not c._allows_root("workspace/p0_deadbeef")
    assert not c._allows_root("workspace/l1b_deadbeef")
    assert not c._allows_root("workspace/b2e_deadbeef")
    assert not c._allows_root("workspace/s2c_deadbeef")
    w, clk = MemWriter(), FakeClock()
    root = "/tmp/opencode/b2f_fake_nowrite"
    _run(root, w, clk, _decode_ok, max_blocks=1)
    assert set(w.store) == {f"{root}/manifest.json", f"{root}/rows.json",
                            f"{root}/block_accounting.csv"}
    header = w.store[f"{root}/block_accounting.csv"].splitlines()[0]
    assert header == ("block,seed,exact_match,status,iterations,wall_s,"
                      "u1_source,prior_entropy_bits,u1_mismatches,d_u1,"
                      "leak_bits,f_super")
    body = w.store[f"{root}/block_accounting.csv"].splitlines()[1]
    cols = body.split(",")
    assert cols[6] == "MARGINAL"     # u1_source
    assert float(cols[7]) == 0.0     # prior_entropy_bits
    assert cols[8] == "8"            # u1_mismatches
    assert float(cols[9]) == 0.0     # d_u1 measured label
    assert float(cols[10]) == 1104.0  # leak_bits
    assert float(cols[11]) == pytest.approx(c.f_super_du0("F208"),
                                            abs=1e-12)
    rows = json.loads(w.store[f"{root}/rows.json"])
    r0 = rows[0]
    for key in ("block", "seed", "exact_match", "block_accept", "block_fail",
                "status", "iterations", "wall_s", "u1_source",
                "prior_entropy_bits", "u1_mismatches", "d_u1",
                "leak_bits", "f_super"):
        assert key in r0
    assert r0["u1_source"] == "MARGINAL"
    assert r0["d_u1"] == 0.0
    assert "NEVER-ASSUME-ZERO" in r0["d_u1_label"]
    assert r0["leak_bits"] == 1104.0
    assert r0["f_super"] == pytest.approx(1.294947, abs=1e-6)


# T12: manifest labels — campaign, MARGINAL, genie REMOVED, D-u1, DE. -----
@pytest.mark.parametrize("arm,de_default", [("F208", "covered"),
                                            ("F202", "exploratory")])
def test_t12_manifest_labels(arm, de_default):
    w, clk = MemWriter(), FakeClock()

    def _pe826(construction, seed):
        out = _decode_ok(construction, seed)
        out["prior_entropy_bits"] = 826.27
        out["u1_mismatches"] = 8
        return out

    mf = _run(f"/tmp/opencode/b2f_fake_labels_{arm}", w, clk, _pe826,
              arm=arm, max_blocks=4)
    assert mf["campaign"] == "B2F-soft-marginal"
    assert mf["arm_role"] == c.ARMS[arm]["role"]
    assert mf["paired_construction"]["source_arm"] == c.ARMS[arm]["source_arm"]
    assert "byte-identical" in mf["paired_construction"]["note"]
    assert mf["u1_source"]["source"] == "MARGINAL"
    assert "NO argmax" in mf["u1_source"]["rule"]
    assert "not-a-disclosure" in mf["u1_source"]["mismatch_measurement"]
    assert "REMOVED" in mf["u1_source"]["genie_ceiling"]
    pe = mf["prior_entropy"]
    assert "Σ_i H(π_i)" in pe["rule"]
    assert pe["mean_bits"] == 826.27
    assert pe["p50"] == 826.27 and pe["p90"] == 826.27
    assert pe["p99"] == 826.27 and pe["max"] == 826.27
    assert pe["blocks"] == 4
    assert pe["genie_anchor_bits"] == pytest.approx(826.266, abs=0.01)
    assert "MEASURED (dry probe" in pe["pre_registered_observation"]
    assert "flattens the prior" in pe["pre_registered_observation"]
    assert "NOT a decodability proof" in pe["pre_registered_observation"]
    assert pe["u1_mismatches_mean"] == 8.0
    du = mf["d_u1"]
    assert du["value"] == 0.0
    assert "NEVER assume zero" in du["never_assume_zero_note"]
    assert du["f_super_du0_basis"] == pytest.approx(c.f_super_du0(arm),
                                                    abs=1e-12)
    assert mf["de_cover"]["label"] == de_default
    assert "NO new DE" in mf["de_cover"]["arm_note"]
    assert "(5m+64)/852.544" in mf["f_bar"]
    assert "2026095601+idx" in mf["seeds"]["paired_note"]
    assert "b2e" in mf["seeds"]["paired_note"]
    assert mf["resume_policy_note"].count("ONE") >= 1
    assert "no auto-relaunch" in mf["resume_policy_note"]


def test_t12_de_label_override_and_refusal():
    w, clk = MemWriter(), FakeClock()
    mf = _run("/tmp/opencode/b2f_fake_delabel", w, clk, _decode_ok,
              max_blocks=1, de_label="exploratory")
    assert mf["de_cover"]["label"] == "exploratory"
    assert "explicit --de-label" in mf["de_cover"]["label_source"]
    with pytest.raises(c.Refusal):
        _run("/tmp/opencode/b2f_fake_delabel_bad", MemWriter(),
             FakeClock(), _decode_ok, max_blocks=1, de_label="maybe")


def test_t12_stats_helpers_and_seed_wiring():
    rows = [{"block": 0, "status": "success", "block_fail": 0,
             "prior_entropy_bits": 800.0, "u1_mismatches": 3},
            {"block": 1, "status": "success", "block_fail": 1,
             "prior_entropy_bits": 850.0, "u1_mismatches": 11},
            {"block": 2, "status": "overrun"}]
    st = c.prior_entropy_stats(rows)
    assert st["blocks"] == 2 and st["mean_bits"] == 825.0
    assert st["max"] == 850.0 and st["min"] == 800.0
    assert st["p50"] == 825.0
    km = c.mismatch_stats(rows)
    assert km["blocks"] == 2 and km["mean"] == 7.0 and km["max"] == 11
    assert c.prior_entropy_stats([])["blocks"] == 0
    assert c.mismatch_stats([])["blocks"] == 0
    qt = c.quarter_tally(rows)
    assert qt["idx_0_59"] == {"blocks": 3, "fails": 1}
    assert qt["quarters_complete"] == 0
    # stream_seed/block_seed frozen wiring (paired domain, shared with
    # O1R/P0/L1B/b2e — no independence claim).
    assert c.block_seed("F208", 0) == 2026095601
    assert c.block_seed("F208", 239) == 2026095840
    assert c.block_seed("F202", 239) == 2026095840
    assert c.stream_seed(2026095601) == c.o1.stream_seed(2026095601)


# T13: dry 1-block probe — REAL bundle/sampler/marginal, FAKE kernel. -----
def test_t13_dry_block_probe_real_bundle_fake_kernel(monkeypatch):
    """Dry wiring probe (no production decode, no verdict): binds the
    frozen read-only 2M bundle, draws the paired block-0 triple on the
    ``o1_blk:`` stream, computes the FROZEN marginal prior + XOR
    centering, and captures the (n,32) prior the kernel would receive.
    Reports the measured ``prior_entropy_bits`` against the pre-registered
    ≈826.27 b parity anchor (report-only; NOT a decodability claim).
    """
    bundle = c.s2c.bind_empirical_bundle(c.GAMMA_DEFAULT, c.SOURCE_DEFAULT)
    seen = {}
    real_triple = c.s2c.empirical_triple_sampler

    def _capture_triple(bundle, nn, rng):
        b, u1, u2 = real_triple(bundle, nn, rng)
        seen["b"], seen["u1"], seen["u2"] = b, u1, u2
        return (b, u1, u2)

    def _fake_dense(triples, n, mm, field):
        assert (n, mm) == (1024, 208)
        return np.zeros((mm, n), dtype=np.int64)

    def _fake_syn(field, dense, vec):
        assert len(vec) == 1024
        return [0] * 208

    def _fake_posterior(field, y, matrix, s_x, prior, max_iter, **kw):
        seen.setdefault("calls", []).append(
            {"y": list(y), "s_x": list(s_x),
             "prior": np.asarray(prior, dtype=np.float64).copy(),
             "prior_shape": tuple(np.asarray(prior).shape),
             "prior_rowsums": np.asarray(prior).sum(axis=1),
             "max_iter": max_iter})
        assert tuple(np.asarray(prior).shape) == (1024, 32)
        return {"status": "success", "iterations": 21,
                "reconstruction_ok": True, "x_hat": list(seen["u2"])}

    monkeypatch.setattr(c.s2c, "empirical_triple_sampler", _capture_triple)
    monkeypatch.setattr(c.peg, "sparse_to_dense", _fake_dense)
    monkeypatch.setattr(c.fftqspa, "syndrome_of", _fake_syn)
    monkeypatch.setattr(c.v28, "decode_error_domain_posterior",
                        _fake_posterior)
    construction = {"triples": [(0, 0, 1)], "n": 1024, "m": 208}
    out = c.decode_block_marginal(construction, 2026095601, bundle, 1024,
                                  208)
    assert len(seen["calls"]) == 1
    call = seen["calls"][0]
    assert call["max_iter"] == 300
    assert call["y"] == list(np.asarray(seen["b"] & 31))
    assert np.allclose(call["prior_rowsums"], 1.0, atol=1e-9)
    # The captured prior IS the frozen marginal formula, XOR-centered.
    b, y = seen["b"], np.asarray(seen["b"] & 31, dtype=np.int64)
    manual_marg = c.marginal_prior_l2(bundle, b)
    manual_prior = c.s2c.center_rows_prior(manual_marg, y)
    assert np.allclose(call["prior"], manual_prior, atol=1e-12)
    # Report-only entropy: MEASURED on the frozen formula. The packet §1
    # pre-registered parity anchor is 826.266 b (genie H_L2·n); the
    # Bayes-marginal prior row IS P(U2|b_i), so Σ_i H(π_i) measures
    # H(U2|B)·n ≈ H_full·n = 852.544 b/block — Bayes marginalization
    # FLATTENS the prior by ≈ H(U1|B)·n = 26.278 b. The column is
    # REPORT-ONLY (never gated); the deviation is reported to the main
    # thread, not "fixed" (the frozen formula is implemented verbatim).
    genie_rows = c.s2c.posterior_rows_l2(bundle, b, seen["u1"])
    h_genie = c.prior_entropy_bits(genie_rows)
    print(f"DRY prior_entropy_bits (MARGINAL) = "
          f"{out['prior_entropy_bits']:.4f}")
    print(f"DRY genie-row entropy (same draw) = {h_genie:.4f}")
    print(f"DRY mixing penalty = "
          f"{out['prior_entropy_bits'] - h_genie:.4f} b/block "
          f"(H_L1*1024 = {c.L1_CONTENT_BITS:.4f})")
    print(f"DRY packet §1 parity anchor (genie H_L2*1024) = "
          f"{c.GENIE_L2_CONTENT_BITS:.4f}; H_full*1024 = "
          f"{c.CONTENT_BITS:.4f}")
    assert out["prior_entropy_bits"] == pytest.approx(853.0211, abs=0.01)
    assert out["prior_entropy_bits"] > h_genie  # mixing can only flatten
    assert (out["prior_entropy_bits"] - h_genie) == pytest.approx(
        c.L1_CONTENT_BITS, abs=8.0)
    assert out["u1_source"] == "MARGINAL"
    assert isinstance(out["u1_mismatches"], int)
    assert out["exact_match"] is True
    # Report-only u1 mismatch ties to the b2e MAP measurement.
    assert out["u1_mismatches"] == c.u1_mismatches(
        seen["u1"], c.map_u1(bundle, seen["b"]))
    # Marg rows are valid decoder content (finite, nonneg, sum≈1).
    assert np.all(np.isfinite(manual_marg)) and np.all(manual_marg >= 0.0)
    assert np.allclose(manual_marg.sum(axis=1), 1.0, atol=1e-9)
