"""V80 B2E MAP-u1 campaign executor tests (EXPLORE, FAKE-ONLY).

Frozen spec: B2E_EXPERIMENT_PACKET_20260921.md + B2E_EXPERIMENT_PROMPT_
20260921.md (G-B2E, arms B208|B202, 240 blocks) read through the
Amendment 2026-09-21 (entropy-sum D-u1 + arm-mean gate (b)). Every test
injects fake construct/decode/clock/rss/writer or synthetic dict bundles
— zero production campaign runs, zero campaign disk writes (the writer is
an in-memory capture; resume shims use tmp_path and are removed by
pytest). Two dry-construction recording tests (T5, ~10 s) measure the
REAL constructor in-memory for B208/B202 (allowed: pins recorded, no
writes, no decodes); all other tests are milliseconds. Dry wrapper tests
(T9/T10) run the REAL decode wrapper with fake matrix pieces (no
production decode at scale).
"""
import inspect
import json
import os

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import (
    v80_b2e_campaign as c,
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
    # Mirrors the frozen pin table (packet §2/X3): fc=0/rank-full both
    # arms; girth recorded (8 here); stable triples exercise
    # twice-identical. Signature mirrors production construct_arm(arm,
    # seed, max_trials) and asserts the gate forwards the B2E arm id.
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
            "u1_source": "MAP", "u1_mismatches": 8,
            "d_u1_bits": 0.0}


def _decode_fail(construction, seed):
    return {"status": "max_iter_reached", "iterations": 300,
            "reconstruction_ok": False, "exact_match": False,
            "u1_source": "MAP", "u1_mismatches": 8,
            "d_u1_bits": 0.0}


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


def _run(root, writer, clock, decode_fn, arm="B208", **kw):
    return c.execute(root=root, arm=arm,
                     construct_fn=_fake_construct(arm),
                     decode_fn=decode_fn, clock=clock,
                     rss_fn=lambda: 0, writer=writer, **kw)


# T1: dual-flag gate + arm/root/de-label refusal matrix (rc2). ------------
def test_t1_dual_flag_refusal():
    with pytest.raises(c.Refusal):
        c.main([])
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--arm", "B208",
                "--root", "workspace/b2e_deadbeef"])
    with pytest.raises(c.Refusal):
        c.main(["--execution-authorized", "--arm", "B208",
                "--root", "workspace/b2e_deadbeef"])
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--execution-authorized",
                "--arm", "B208",
                "--root", "workspace/wrong_deadbeef"])
    for bad_prefix in ("workspace/o1_deadbeef", "workspace/p0_deadbeef",
                       "workspace/l1b_deadbeef", "workspace/s2c_deadbeef",
                       "workspace/b2e"):
        with pytest.raises(c.Refusal):
            c.main(["--execute-real", "--execution-authorized",
                    "--arm", "B208", "--root", bad_prefix])
    for bad_arm in ("A208", "B200", "b208", ""):
        with pytest.raises(c.Refusal):
            c.main(["--execute-real", "--execution-authorized",
                    "--arm", bad_arm, "--root", "workspace/b2e_deadbeef"])
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--execution-authorized",
                "--arm", "B208", "--root", "workspace/b2e_aaaaaaaa",
                "--resume-from", "workspace/b2e_bbbbbbbb"])
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--execution-authorized",
                "--arm", "B208", "--root", "workspace/b2e_deadbeef",
                "--de-label", "maybe"])
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--execution-authorized",
                "--arm", "B208", "--root", "workspace/b2e_deadbeef",
                "--n-blocks", "0"])
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--execution-authorized",
                "--arm", "B208", "--root", "workspace/b2e_deadbeef",
                "--construct-trials", "0"])
    # Frozen-configuration refusals: B2E has EXACTLY ONE runnable config;
    # any science-input deviation refuses rc=2 BEFORE any root contact
    # (packet §6 STOP). NOTE: no test ever passes the dual-flag gate with
    # a valid workspace/b2e_ root — that path is the real campaign and is
    # never invoked from tests (repo rule: never invoke production work
    # implicitly from tests).
    for extra in (["--construct-seed", "2026092011"],
                  ["--construct-trials", "10"],
                  ["--block-base", "2026095501"],
                  ["--n-blocks", "60"]):
        with pytest.raises(c.Refusal):
            c.main(["--execute-real", "--execution-authorized",
                    "--arm", "B208", "--root", "workspace/b2e_deadbeef"]
                   + extra)


# T2: root absent/present matrix + forbidden trees. ------------------------
def test_t2_root_absent_present_matrix(tmp_path):
    w, clk = MemWriter(), FakeClock()
    mf = _run("/tmp/opencode/b2e_fake_absent_01", w, clk, _decode_ok,
              max_blocks=1)
    assert mf["verdict"] == "PROBE-truncated"
    with pytest.raises(c.Refusal):
        _run(str(tmp_path), MemWriter(), FakeClock(), _decode_ok,
             max_blocks=1)
    with pytest.raises(c.Refusal):
        c.execute(root="/tmp/opencode/b2e_fake_absent_02", arm="B208",
                  resume_from="/tmp/opencode/b2e_fake_absent_02",
                  construct_fn=_fake_construct("B208"),
                  decode_fn=_decode_ok,
                  clock=FakeClock(), rss_fn=lambda: 0, writer=MemWriter())
    with pytest.raises(c.Refusal):
        c.execute(root="/tmp/opencode/b2e_fake_a", arm="B208",
                  resume_from="/tmp/opencode/b2e_fake_b",
                  construct_fn=_fake_construct("B208"),
                  decode_fn=_decode_ok,
                  clock=FakeClock(), rss_fn=lambda: 0, writer=MemWriter())
    for bad in ("/tmp/opencode/results/b2e_fake_x",
                "/tmp/opencode/comparison_bench/outputs_comparison/"
                "b2e_fake_x"):
        with pytest.raises(c.Refusal):
            c.execute(root=bad, arm="B208",
                      construct_fn=_fake_construct("B208"),
                      decode_fn=_decode_ok, clock=FakeClock(),
                      rss_fn=lambda: 0, writer=MemWriter(), max_blocks=1)


# T3: arms table + amended accounting constants. ---------------------------
@pytest.mark.parametrize("arm,m,leak,f_du0,headroom", [
    ("B208", 208, 1104.0, 1.294947, 4.31),
    ("B202", 202, 1074.0, 1.259759, 34.31),
])
def test_t3_arms_table_and_accounting(arm, m, leak, f_du0, headroom):
    assert c.ARMS[arm]["m"] == m
    assert c.ARMS[arm]["source_arm"] == "A208" if arm == "B208" \
        else c.ARMS[arm]["source_arm"] == "A202"
    assert c.ARMS[arm]["lambda"] == {2: 1.0}
    assert c.ARMS[arm]["leak_bits"] == leak
    basis = c.leak_basis(arm)
    assert basis["m"] == m and basis["leak_bits"] == leak
    assert basis["f_super_du0_basis"] == pytest.approx(f_du0, abs=1e-6)
    assert "NEVER gated" in basis["f_super_du0_label"]
    assert "mean(d_u1_bits)" in basis["f_super_rule"]
    assert basis["headroom_bits"] == pytest.approx(headroom, abs=0.01)
    assert "fails gate (b)" in basis["headroom_line"]
    assert "5·" in basis["f_super_5k_label"]
    assert basis["d_blind"] == 0.0
    assert "NEVER" in basis["d_blind_label"]
    assert c.MAX_ITER == 300
    assert c.B2E_BLOCK_BASE == 2026095601
    assert c.B2E_N_BLOCKS == 240
    assert c.B2E_CONSTRUCT_SEED == 2026092001
    assert c.B2E_MAX_TRIALS == 20
    assert c.B2E_N == 1024
    assert c.CONTENT_BITS == pytest.approx(852.544, abs=1e-3)
    assert c.L1_CONTENT_BITS == pytest.approx(26.28, abs=0.01)
    assert c.fail_bar(240) == 12
    assert c.U1_SOURCE == "MAP"
    assert c.CAMPAIGN_LABEL == "B2E-map-u1"


def test_t3_f_super_arithmetic_matches_frozen_figures():
    # Amendment pre-registered observation at mean D-u1 = 26.28 b.
    assert c.f_super_conservative("B208", 26.28) == pytest.approx(1.3258,
                                                                 abs=1e-4)
    assert c.f_super_conservative("B202", 26.28) == pytest.approx(1.2906,
                                                                 abs=1e-4)
    # Frozen §4 5×k sensitivity at the measured mean k=8.10 (report-only).
    assert c.f_super_5k("B208", 8.10) == pytest.approx(1.342453, abs=1e-6)
    assert c.f_super_5k("B202", 8.10) == pytest.approx(1.307264, abs=1e-6)
    # Per-block entropy sum feeds the amended gate directly.
    assert (c.f_super_conservative("B208", 30.0)
            > c.F_SUPER_MAX)  # mean 30 b > 4.31 b headroom
    assert (c.f_super_conservative("B202", 30.0)
            <= c.F_SUPER_MAX)  # mean 30 b <= 34.31 b headroom


def test_t3_unknown_arm_refuses():
    for bad in ("A208", "B200", "b208", ""):
        with pytest.raises(c.Refusal):
            c.block_seed(bad, 0)
        with pytest.raises(c.Refusal):
            c.leak_basis(bad)
        with pytest.raises(c.Refusal):
            c.f_super_du0(bad)
        with pytest.raises(c.Refusal):
            c.f_super_conservative(bad, 1.0)
        with pytest.raises(c.Refusal):
            c.f_super_5k(bad, 1)
        with pytest.raises(c.Refusal):
            c.construct_arm(bad)
    calls = []

    def _counting(construction, seed):
        calls.append(seed)
        return _decode_ok(construction, seed)

    with pytest.raises(c.Refusal) as exc:
        c.execute(root="/tmp/opencode/b2e_fake_badarm", arm="A208",
                  construct_fn=_fake_construct("B208"),
                  decode_fn=_counting, clock=FakeClock(),
                  rss_fn=lambda: 0, writer=MemWriter(), max_blocks=1)
    assert exc.value.code == 2
    assert calls == []


# T4: construct gate — fc/rank/twice gated, girth recorded. ----------------
def test_t4_gate_pass_fake_mimic():
    con = c._construct_gate("B208", _fake_construct("B208"), 2026092001, 20)
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

    con = c._construct_gate("B202", _g4, 2026092001, 20)
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
        c.execute(root="/tmp/opencode/b2e_fake_pinbad", arm="B208",
                  construct_fn=_bad,
                  decode_fn=_counting, clock=FakeClock(),
                  rss_fn=lambda: 0, writer=MemWriter(), max_blocks=1)
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "STOP-BLOCKED" in err
    assert "B208" in err
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


@pytest.mark.parametrize("arm,m", [("B208", 208), ("B202", 202)])
def test_t5_dry_construct_pins_recorded(arm, m):
    code = _measured(arm)
    assert code["n"] == 1024 and code["m"] == m
    assert code["rank"] == m  # rank-full holds both arms
    assert code["four_cycles"] == 0  # fc==0 gate-clean (both arms)
    assert code["min_girth"] == 8  # recorded-not-gated (measured)
    assert code["family"] == "peg-irregular"
    assert code.get("status", "ok") == "ok"
    assert code["source_arm"] == ("A208" if arm == "B208" else "A202")


@pytest.mark.parametrize("arm,m", [("B208", 208), ("B202", 202)])
def test_t5b_real_pins_through_real_gate(arm, m):
    # Production binding via the same gate path execute() uses: a spy
    # delegating to the real constructor asserts the B2E arm id + frozen
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
    assert con["source_arm"] == ("A208" if arm == "B208" else "A202")


# T6: MAP û1 semantics — argmax vs manual, domain guards. ------------------
def test_t6_map_u1_matches_manual_argmax():
    bundle = _fake_bundle(seed=5)
    rng = np.random.default_rng(3)
    b = rng.choice(1024, size=257, p=bundle["p_b"])
    u1_hat = c.map_u1(bundle, b)
    assert u1_hat.shape == (257,)
    assert u1_hat.dtype == np.int64
    g1 = bundle["g1"]
    manual = np.array([int(np.argmax(g1[:, int(bb)])) for bb in b])
    assert np.array_equal(u1_hat, manual)
    assert u1_hat.min() >= 0 and u1_hat.max() < 32
    with pytest.raises(c.Refusal):
        c.map_u1(bundle, np.array([1024]))
    with pytest.raises(c.Refusal):
        c.map_u1(bundle, np.zeros((2, 2), dtype=np.int64))
    with pytest.raises(c.Refusal):
        c.map_u1({"g1": np.zeros((31, 1024))}, np.array([0]))


def test_t6_map_u1_one_hot_bundle_is_deterministic():
    g1 = np.zeros((32, 1024))
    g1[7, :] = 1.0  # every column one-hot at symbol 7
    bundle = {"g1": g1, "g2": None, "p_b": np.full(1024, 1.0 / 1024)}
    b = np.arange(1024, dtype=np.int64)
    assert np.all(c.map_u1(bundle, b) == 7)


# T7: mismatch counting (measurement only). --------------------------------
def test_t7_mismatch_counting():
    u1 = np.array([0, 1, 2, 3, 31, 5, 5, 5], dtype=np.int64)
    assert c.u1_mismatches(u1, u1.copy()) == 0
    assert c.u1_mismatches(u1, np.zeros(8, dtype=np.int64)) == 7
    assert c.u1_mismatches(u1, (u1 + 1) % 32) == 8
    assert c.u1_mismatches(np.array([5]), np.array([5])) == 0
    with pytest.raises(c.Refusal):
        c.u1_mismatches(np.zeros(4, dtype=np.int64),
                        np.zeros(5, dtype=np.int64))
    with pytest.raises(c.Refusal):
        c.u1_mismatches(np.zeros((2, 2), dtype=np.int64),
                        np.zeros((2, 2), dtype=np.int64))


# T8: d_u1_bits equals the per-block entropy sum (small fake bundle). ------
def test_t8_d_u1_bits_equals_entropy_sum():
    g1 = np.zeros((32, 1024))
    g1[0, :] = 1.0  # default: one-hot ⇒ H=0
    g1[:, 0] = 1.0 / 32            # uniform ⇒ H = log2 32 = 5
    g1[:, 1] = 0.0
    g1[0, 1] = g1[1, 1] = 0.5      # binary ½/½ ⇒ H = 1
    g1[:, 2] = 0.0
    g1[:4, 2] = 0.25               # 4-way ¼ ⇒ H = 2
    g1[:, 3] = 0.0
    g1[[0, 1, 2, 3], 3] = [0.7, 0.1, 0.1, 0.1]  # H(0.7,0.1,0.1,0.1)
    bundle = {"g1": g1, "g2": None,
              "p_b": np.full(1024, 1.0 / 1024)}
    b = np.array([0, 1, 2, 3, 9], dtype=np.int64)  # col 9 one-hot ⇒ 0
    d = c.d_u1_bits(bundle, b)
    manual = float(-np.sum([0.7, 0.1, 0.1, 0.1]
                           * np.log2([0.7, 0.1, 0.1, 0.1])))
    assert d == pytest.approx(5.0 + 1.0 + 2.0 + manual + 0.0, abs=1e-12)
    # Entropy-sum identity against a manual column-by-column computation.
    rng = np.random.default_rng(11)
    g1r = rng.random((32, 1024)) + 0.01
    g1r = g1r / g1r.sum(axis=0, keepdims=True)
    br = rng.choice(1024, size=64)
    bundle2 = {"g1": g1r, "g2": None, "p_b": np.full(1024, 1.0 / 1024)}
    h = -np.sum(g1r * np.log2(np.maximum(g1r, 1e-300)), axis=0)
    assert c.d_u1_bits(bundle2, br) == pytest.approx(float(h[br].sum()),
                                                     abs=1e-12)
    assert c.d_u1_bits(bundle2, np.array([0], dtype=np.int64)) >= 0.0
    with pytest.raises(c.Refusal):
        c.d_u1_bits(bundle, np.array([1024]))
    with pytest.raises(c.Refusal):
        c.d_u1_bits(bundle, np.zeros((2, 2), dtype=np.int64))


# T9: prior rows use MAP û1, NOT genie true-u1 (monkeypatch capture). -----
def test_t9_prior_rows_use_map_u1_not_genie(monkeypatch):
    n = 16
    b_fix = np.arange(n, dtype=np.int64) % 1024
    u1_fix = np.zeros(n, dtype=np.int64)   # GENIE true-u1 ≡ 0
    u2_fix = np.full(n, 3, dtype=np.int64)
    g1 = np.zeros((32, 1024))
    g1[9, :] = 1.0                          # MAP û1 ≡ 9 (≠ genie)
    bundle = {"g1": g1,
              "g2": np.full((32, 32, 1024), 1.0 / 32),
              "p_b": np.full(1024, 1.0 / 1024)}
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
        captured["prior_shape"] = tuple(np.asarray(prior).shape)
        captured["max_iter"] = max_iter
        return {"status": "success", "iterations": 9,
                "reconstruction_ok": True, "x_hat": list(u2_fix)}

    real_l2 = c.s2c.posterior_rows_l2

    def _spy_l2(bundle, b_vec, u1_vec):
        captured["u1_arg"] = np.asarray(u1_vec).tolist()
        captured["rows_shape"] = np.asarray(
            real_l2(bundle, b_vec, u1_vec)).shape
        return real_l2(bundle, b_vec, u1_vec)

    monkeypatch.setattr(c.s2c, "empirical_triple_sampler", _fake_triple)
    monkeypatch.setattr(c.peg, "sparse_to_dense", _fake_dense)
    monkeypatch.setattr(c.fftqspa, "syndrome_of", _fake_syn)
    monkeypatch.setattr(c.s2c, "posterior_rows_l2", _spy_l2)
    monkeypatch.setattr(c.v28, "decode_error_domain_posterior",
                        _fake_posterior)
    out = c.decode_block_map_u1({"triples": [(0, 0, 1)], "n": n, "m": 8},
                                2026095601, bundle, n, 8)
    assert captured["u1_arg"] == [9] * n      # MAP û1, NOT genie zeros
    assert captured["rows_shape"] == (n, 32)
    assert captured["prior_shape"] == (n, 32)
    assert captured["max_iter"] == 300
    assert captured["y"] == list(b_fix & 31)  # Bob L2 half (bits 4..0)
    assert out["u1_source"] == "MAP"
    assert out["u1_mismatches"] == n          # genie 0 vs MAP 9
    assert out["d_u1_bits"] == 0.0            # one-hot γ1 columns
    assert out["exact_match"] is True         # x̂==u2
    assert out["max_iter"] == 300
    assert "REMOVED" in out["l1_conditioning"]


# T10: dry 1-block wiring — sampler/rows/centering real, kernel fake. -----
def test_t10_dry_block_wiring_posterior_entrypoint(monkeypatch):
    bundle = _fake_bundle(seed=13)
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
    out = c.decode_block_map_u1(construction, 2026095601, bundle, 1024, 208)
    assert len(seen["calls"]) == 1
    call = seen["calls"][0]
    assert call["max_iter"] == 300
    assert call["y"] == list(np.asarray(seen["b"] & 31))
    assert np.allclose(call["prior_rowsums"], 1.0, atol=1e-9)
    assert isinstance(out["u1_mismatches"], int)
    assert isinstance(out["d_u1_bits"], float)
    assert out["d_u1_bits"] > 0.0  # random fake bundle ⇒ positive entropy
    assert out["u1_source"] == "MAP"
    assert out["exact_match"] is True
    # Prior rows must use MAP û1 (recomputed here from the same draw).
    assert out["u1_mismatches"] == c.u1_mismatches(
        seen["u1"], c.map_u1(bundle, seen["b"]))
    assert out["d_u1_bits"] == pytest.approx(
        c.d_u1_bits(bundle, seen["b"]), abs=1e-12)
    src = inspect.getsource(c)
    bare = [ln for ln in src.splitlines()
            if "decode_error_domain(" in ln
            and "decode_error_domain_posterior" not in ln
            and "NEVER" not in ln and "scalar" not in ln]
    assert bare == []


def test_t10_construction_nm_wiring_guard():
    bundle = _fake_bundle()
    with pytest.raises(c.Refusal):
        c.decode_block_map_u1({"triples": [], "n": 1024, "m": 208},
                              2026095601, bundle, 1024, 202)
    with pytest.raises(c.Refusal):
        c.decode_block_map_u1({"triples": [], "n": 256, "m": 208},
                              2026095601, bundle, 1024, 208)
    with pytest.raises(c.Refusal):
        c.decode_block_map_u1({"triples": [], "n": 1024, "m": 208},
                              True, bundle, 1024, 208)


# T11: gates — all-ok PASS; amended mean gate (b); early-stop; bar edge. --
@pytest.mark.parametrize("arm", ["B208", "B202"])
def test_t11_all_ok_pass_and_manifest(arm):
    w, clk = MemWriter(), FakeClock()
    root = f"/tmp/opencode/b2e_fake_allok_{arm.lower()}"
    seen = []

    def _rec(construction, seed):
        seen.append(seed)
        return _decode_ok(construction, seed)

    mf = c.execute(root=root, arm=arm,
                   construct_fn=_fake_construct(arm),
                   decode_fn=_rec, clock=clk,
                   rss_fn=lambda: 0, writer=w)
    assert mf["campaign"] == "B2E-map-u1"
    assert mf["arm"] == arm
    assert mf["verdict"] == "PASS"
    assert mf["failures"] == 0
    assert mf["blocks_completed"] == 240
    assert mf["ledger"] == {"decodes": 240, "blocks_completed": 240}
    assert mf["fer_blocks"] == pytest.approx(0.0)
    assert mf["fail_bar"] == 12
    assert mf["pass_bar"] == "block FER<=5% (fails/240<=12)"
    # d_u1 = 0 fake rows ⇒ gate (b) sits exactly on the du0 report line.
    assert mf["f_super_conservative_mean"] == pytest.approx(
        c.f_super_du0(arm), abs=1e-12)
    assert mf["f_super"] == pytest.approx(c.f_super_du0(arm), abs=1e-12)
    assert mf["d_u1"]["mean_bits"] == 0.0
    assert mf["d_u1"]["u1_mismatches_mean"] == 8.0
    assert mf["d_u1"]["violating_blocks"] == 0
    assert mf["quarter_tally"]["quarters_complete"] == 4
    assert mf["quarter_tally"]["quarters_le3"] == 4
    assert w.calls == 241  # 240 block checkpoints + 1 final
    assert mf["verify"] == {"pins_ok": True, "ledger_ok": True,
                            "rows_ok": True}
    rows = json.loads(w.store[f"{root}/rows.json"])
    assert len(rows) == 240
    assert [r["block"] for r in rows] == list(range(240))
    assert seen[0] == 2026095601 and seen[-1] == 2026095840
    assert all(r["u1_source"] == "MAP" for r in rows)
    mani = json.loads(w.store[f"{root}/manifest.json"])
    assert mani["seeds"]["block_base"] == 2026095601
    assert "STOP-BLOCKED" in mani["construct"]["pins"]
    assert "recorded-not-gated" in mani["construct"]["pins"]
    assert "NO independence claim" in mani["seeds"]["paired_note"]
    assert "REMOVED" in mani["decoder"]["l1_conditioning"]
    assert "no D1 ceiling label" in mani["u1_estimator"]["genie_ceiling"]
    assert "mean(d_u1_bits)" in mani["f_bar"]


@pytest.mark.parametrize("arm,expect", [
    ("B208", "FAIL"),   # mean 30 b > 4.31 b headroom ⇒ gate (b) fails
    ("B202", "PASS"),   # mean 30 b <= 34.31 b headroom ⇒ gate (b) passes
])
def test_t11_amended_mean_gate_discriminates_arms(arm, expect):
    def _d30(construction, seed):
        out = _decode_ok(construction, seed)
        out["d_u1_bits"] = 30.0
        return out

    w, clk = MemWriter(), FakeClock()
    mf = _run(f"/tmp/opencode/b2e_fake_gateb_{arm}", w, clk, _d30, arm=arm)
    assert mf["verdict"] == expect
    assert mf["failures"] == 0  # gate (a) clean; gate (b) decides
    assert mf["d_u1"]["mean_bits"] == 30.0
    assert mf["d_u1"]["p50"] == 30.0
    assert mf["d_u1"]["p90"] == 30.0
    assert mf["d_u1"]["p99"] == 30.0
    assert mf["d_u1"]["max"] == 30.0
    # Report-only lines carried alongside the gated mean.
    assert mf["d_u1"]["f_super_du0_report"] == pytest.approx(
        c.f_super_du0(arm), abs=1e-12)
    assert mf["d_u1"]["f_super_5k_sensitivity"] == pytest.approx(
        c.f_super_5k(arm, 8.0), abs=1e-12)


def test_t11_early_stop_thirteenth_fail():
    w, clk = MemWriter(), FakeClock()
    mf = _run("/tmp/opencode/b2e_fake_early240", w, clk, _decode_fail)
    assert mf["verdict"] == "FAIL-early-stop"
    assert mf["blocks_completed"] == 13
    assert mf["failures"] == 13
    assert mf["n_blocks"] == 240
    assert mf["fail_bar"] == 12
    assert mf["next_block"] == 13
    assert mf["partial"] is True
    assert mf["quarter_tally"]["quarters_complete"] == 0  # partial q0


def test_t11_bar_boundary_twelve_fails_pass():
    state = {"k": 0}

    def _twelve_then_ok(construction, seed):
        state["k"] += 1
        if state["k"] <= 12:
            return _decode_fail(construction, seed)
        return _decode_ok(construction, seed)

    w, clk = MemWriter(), FakeClock()
    mf = _run("/tmp/opencode/b2e_fake_bar12", w, clk, _twelve_then_ok)
    assert mf["verdict"] == "PASS"
    assert mf["failures"] == 12
    assert mf["blocks_completed"] == 240


def test_t11_budget_terminal_noresume(tmp_path):
    w, clk = MemWriter(), FakeClock()

    def _overrun(construction, seed):
        clk.t += 301.0
        return _decode_ok(construction, seed)

    mf = _run("/tmp/opencode/b2e_fake_overrun", w, clk, _overrun,
              max_blocks=1)
    assert mf["verdict"] == "FAIL(budget)"
    assert mf["partial"] is True
    rows = json.loads(w.store["/tmp/opencode/b2e_fake_overrun/rows.json"])
    assert len(rows) == 1 and rows[0]["status"] == "overrun"
    root = str(tmp_path / "b2e_fake_budget_noresume")
    os.makedirs(root, exist_ok=True)
    with open(f"{root}/manifest.json", "w") as fh:
        fh.write(w.store["/tmp/opencode/b2e_fake_overrun/manifest.json"])
    with open(f"{root}/rows.json", "w") as fh:
        fh.write(w.store["/tmp/opencode/b2e_fake_overrun/rows.json"])
    with pytest.raises(c.Refusal):
        c.execute(root=root, arm="B208", resume_from=root,
                  construct_fn=_fake_construct("B208"),
                  decode_fn=_decode_ok, clock=FakeClock(),
                  rss_fn=lambda: 0, writer=MemWriter())


def test_t11_malformed_decode_output_refuses():
    def _no_du(construction, seed):
        out = _decode_ok(construction, seed)
        del out["d_u1_bits"]
        return out

    with pytest.raises(c.Refusal):
        _run("/tmp/opencode/b2e_fake_nodu", MemWriter(), FakeClock(),
             _no_du, max_blocks=1)


# T12: checkpoint/resume — one wall-partial; 2nd/arm-swap refuses. ---------
def test_t12_resume_continuation_single_wall_window(tmp_path):
    root = str(tmp_path / "b2e_fake_resume")
    w1, clk1 = MemWriter(), FakeClock()

    def _advancing(construction, seed):
        clk1.t += 100.0
        return _decode_ok(construction, seed)

    part = c.execute(root=root, arm="B208",
                     construct_fn=_fake_construct("B208"),
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
    done = c.execute(root=root, arm="B208", resume_from=root,
                     construct_fn=_fake_construct("B208"),
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
        c.execute(root=root, arm="B208", resume_from=root,
                  construct_fn=_fake_construct("B208"),
                  decode_fn=_counting, clock=FakeClock(),
                  rss_fn=lambda: 0, writer=MemWriter())
    assert exc.value.code == 2
    assert calls == []


def test_t12_resume_arm_mismatch_refuses(tmp_path):
    root = str(tmp_path / "b2e_fake_resume_swap")
    w1, clk1 = MemWriter(), FakeClock()

    def _advancing(construction, seed):
        clk1.t += 100.0
        return _decode_ok(construction, seed)

    part = c.execute(root=root, arm="B208",
                     construct_fn=_fake_construct("B208"),
                     decode_fn=_advancing, clock=clk1,
                     rss_fn=lambda: 0, writer=w1)
    assert part["verdict"] == "INCOMPLETE-wall"
    os.makedirs(root, exist_ok=True)
    with open(f"{root}/manifest.json", "w") as fh:
        fh.write(w1.store[f"{root}/manifest.json"])
    with open(f"{root}/rows.json", "w") as fh:
        fh.write(w1.store[f"{root}/rows.json"])
    with pytest.raises(c.Refusal):
        c.execute(root=root, arm="B202", resume_from=root,
                  construct_fn=_fake_construct("B202"),
                  decode_fn=_decode_ok, clock=FakeClock(),
                  rss_fn=lambda: 0, writer=MemWriter())


# T13: no writes outside root; per-block column schema; prefix gate. -------
def test_t13_no_writes_outside_root_and_csv():
    assert c._allows_root("workspace/b2e_deadbeef")
    assert not c._allows_root("workspace/o1_deadbeef")
    assert not c._allows_root("workspace/p0_deadbeef")
    assert not c._allows_root("workspace/l1b_deadbeef")
    assert not c._allows_root("workspace/s2c_deadbeef")
    w, clk = MemWriter(), FakeClock()
    root = "/tmp/opencode/b2e_fake_nowrite"
    _run(root, w, clk, _decode_ok, max_blocks=1)
    assert set(w.store) == {f"{root}/manifest.json", f"{root}/rows.json",
                            f"{root}/block_accounting.csv"}
    header = w.store[f"{root}/block_accounting.csv"].splitlines()[0]
    assert header == ("block,seed,exact_match,status,iterations,wall_s,"
                      "u1_source,u1_mismatches,d_u1_bits,d_blind,leak_bits,"
                      "f_super_du0_report,f_super_conservative")
    body = w.store[f"{root}/block_accounting.csv"].splitlines()[1]
    cols = body.split(",")
    assert cols[6] == "MAP"          # u1_source
    assert cols[7] == "8"            # u1_mismatches
    assert float(cols[8]) == 0.0     # d_u1_bits
    assert float(cols[11]) == pytest.approx(c.f_super_du0("B208"),
                                            abs=1e-12)
    assert float(cols[12]) == pytest.approx(c.f_super_du0("B208"),
                                            abs=1e-12)
    rows = json.loads(w.store[f"{root}/rows.json"])
    r0 = rows[0]
    for key in ("block", "seed", "exact_match", "block_accept", "block_fail",
                "status", "iterations", "wall_s", "u1_source",
                "u1_mismatches", "d_u1_bits", "d_blind", "leak_bits",
                "f_super_du0_report", "f_super_conservative"):
        assert key in r0
    assert r0["u1_source"] == "MAP"
    assert r0["d_blind"] == 0.0
    assert "NEVER" in r0["d_blind_label"]
    assert r0["leak_bits"] == 1104.0


# T14: manifest labels — campaign, MAP, genie REMOVED, D-u1 block, DE. ----
@pytest.mark.parametrize("arm,de_default", [("B208", "covered"),
                                            ("B202", "exploratory")])
def test_t14_manifest_labels(arm, de_default):
    w, clk = MemWriter(), FakeClock()

    def _d26(construction, seed):
        out = _decode_ok(construction, seed)
        out["d_u1_bits"] = 26.28
        out["u1_mismatches"] = 8
        return out

    mf = _run(f"/tmp/opencode/b2e_fake_labels_{arm}", w, clk, _d26, arm=arm,
              max_blocks=4)
    assert mf["campaign"] == "B2E-map-u1"
    assert mf["arm_role"] == c.ARMS[arm]["role"]
    assert mf["paired_construction"]["source_arm"] == c.ARMS[arm]["source_arm"]
    assert "byte-identical" in mf["paired_construction"]["note"]
    assert mf["u1_estimator"]["source"] == "MAP"
    assert "argmax" in mf["u1_estimator"]["rule"]
    assert "not-a-disclosure" in mf["u1_estimator"]["mismatch_measurement"]
    du = mf["d_u1"]
    assert "Σ_i H(γ1(·|b_i))" in du["rule"]
    assert du["mean_bits"] == 26.28
    assert du["p50"] == 26.28 and du["p90"] == 26.28
    assert du["p99"] == 26.28 and du["max"] == 26.28
    assert du["blocks"] == 4
    # Report-only per-block violating count (all 4 fake blocks carry
    # d_u1=26.28: B208 per-block f_super 1.3258 > 1.3; B202 1.2906 <= 1.3).
    assert du["violating_blocks"] == (4 if arm == "B208" else 0)
    assert "ARM MEAN" in du["violating_blocks_note"]
    assert du["f_super_conservative_mean"] == pytest.approx(
        c.f_super_conservative(arm, 26.28), abs=1e-12)
    assert du["u1_mismatches_mean"] == 8.0
    assert du["h_l1_anchor_bits"] == pytest.approx(26.28, abs=0.01)
    assert "pre-registered observation" in du["pre_registered_observation"]
    assert mf["de_cover"]["label"] == de_default
    assert "NO new DE" in mf["de_cover"]["arm_note"]
    assert "f_super_conservative" in mf["f_bar"]
    assert "Amendment 2026-09-21" in mf["f_bar"]
    assert "2026095601+idx" in mf["seeds"]["paired_note"]
    assert mf["resume_policy_note"].count("ONE") >= 1
    assert "no auto-relaunch" in mf["resume_policy_note"]


def test_t14_de_label_override_and_refusal():
    w, clk = MemWriter(), FakeClock()
    mf = _run("/tmp/opencode/b2e_fake_delabel", w, clk, _decode_ok,
              max_blocks=1, de_label="exploratory")
    assert mf["de_cover"]["label"] == "exploratory"
    assert "explicit --de-label" in mf["de_cover"]["label_source"]
    with pytest.raises(c.Refusal):
        _run("/tmp/opencode/b2e_fake_delabel_bad", MemWriter(),
             FakeClock(), _decode_ok, max_blocks=1, de_label="maybe")


def test_t14_violating_block_count_and_stats_helpers():
    rows = [{"block": 0, "status": "success", "block_fail": 0,
             "d_u1_bits": 10.0, "f_super_conservative": 1.2,
             "u1_mismatches": 3},
            {"block": 1, "status": "success", "block_fail": 1,
             "d_u1_bits": 40.0, "f_super_conservative": 1.4,
             "u1_mismatches": 11},
            {"block": 2, "status": "overrun"}]
    st = c.d_u1_stats(rows)
    assert st["blocks"] == 2 and st["mean_bits"] == 25.0
    assert st["max"] == 40.0 and st["min"] == 10.0
    assert st["p50"] == 25.0
    assert c.violating_block_count(rows) == 1
    assert c.d_u1_stats([])["blocks"] == 0
    assert c.violating_block_count([]) == 0
    qt = c.quarter_tally(rows)
    # quarter_tally counts every row carrying an int block (the overrun
    # row counts with 0 fails), mirroring the frozen O1/L1B behavior.
    assert qt["idx_0_59"] == {"blocks": 3, "fails": 1}
    assert qt["quarters_complete"] == 0
    # stream_seed/block_seed frozen wiring (paired domain).
    assert c.block_seed("B208", 0) == 2026095601
    assert c.block_seed("B208", 239) == 2026095840
    assert c.block_seed("B202", 239) == 2026095840
    assert c.stream_seed(2026095601) == c.o1.stream_seed(2026095601)
