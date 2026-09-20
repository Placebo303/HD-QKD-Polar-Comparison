"""V80 L1B real-L1 + combined-chain campaign executor tests (EXPLORE, FAKE-ONLY).

Frozen spec: L1B_EXPERIMENT_PACKET_20260920.md (G-L1B, configs C6|C8,
stages A|B, 240 blocks). Every test injects fake construct/decode/clock/
rss/writer or synthetic dict bundles — zero production stage runs, zero
campaign disk writes (the writer is an in-memory capture; resume shims
use tmp_path and are removed by pytest). One dry-construction recording
test (T5, ~20 s) measures the REAL constructor in-memory for m=6/8/202/
200 (allowed: pins recorded, no writes, no decodes); all other tests are
milliseconds. Two dry wrapper tests (T6/T7) run the REAL L1/combined
wrappers with fake matrix pieces (no production decode at scale).
"""
import inspect
import json

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import (
    v80_l1b_campaign as c,
)
from comparison_bench.src.comparison_bench.formal_ir import (
    nonbinary_v10_common as common,
)


def _fake_bundle(seed=7):
    rng = np.random.default_rng(seed)
    g1 = rng.random((32, 1024)) + 0.01
    g1 = g1 / g1.sum(axis=0, keepdims=True)
    g2 = rng.random((32, 32, 1024)) + 0.01
    g2 = g2 / g2.sum(axis=1, keepdims=True)
    return {"g1": g1, "g2": g2,
            "p_b": np.full(1024, 1.0 / 1024), "source": "2M"}


def _fake_construct_cfg(config):
    # Mirrors the frozen pin table (packet §1): fc=0/rank-full both codes;
    # girth recorded (8 here); stable triples exercise twice-identical.
    # Signature mirrors production construct_code(m, seed, max_trials) and
    # asserts the gate forwards the m value first (fake-mask guard).
    spec = c.CONFIGS[config]

    def _build(m_in, seed, max_trials):
        assert (seed, max_trials) == (2026092001, 20)
        assert m_in in (spec["m1"], spec["m2"])
        return {"four_cycles": 0, "min_girth": 8, "rank": m_in,
                "family": "peg-irregular", "n": 1024, "m": m_in,
                "triples": [(0, 0, 1), (1, 1, 2)],
                "total_sockets": 2048, "parallel_edges": 0}

    return _build


def _decode_l1_ok(constructions, seed):
    return {"status": "success", "iterations": 10,
            "reconstruction_ok": True, "l1_exact": True,
            "exact_match": True, "stage": "A"}


def _decode_l1_fail(constructions, seed):
    return {"status": "max_iter_reached", "iterations": 300,
            "reconstruction_ok": False, "l1_exact": False,
            "exact_match": False, "stage": "A"}


def _decode_combined_ok(constructions, seed):
    return {"status": "success", "iterations": 11,
            "reconstruction_ok": True, "l1_status": "success",
            "l1_iterations": 9, "l1_exact": True, "l2_exact": True,
            "l2_skipped": False, "exact_match": True, "stage": "B",
            "chain": "real-L1 chain (genie retired)"}


def _decode_combined_fail(constructions, seed):
    return {"status": "max_iter_reached", "iterations": 300,
            "reconstruction_ok": False, "l1_status": "success",
            "l1_iterations": 9, "l1_exact": True, "l2_exact": False,
            "l2_skipped": False, "exact_match": False, "stage": "B",
            "chain": "real-L1 chain (genie retired)"}


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


def _run(root, writer, clock, decode_fn, stage="A", config="C6", **kw):
    return c.execute(root=root, stage=stage, config=config,
                     construct_fn=_fake_construct_cfg(config),
                     decode_fn=decode_fn, clock=clock,
                     rss_fn=lambda: 0, writer=writer, **kw)


# T1: dual-flag gate + stage/config/root/de-label refusal matrix (rc2). --
def test_t1_dual_flag_refusal():
    with pytest.raises(c.Refusal):
        c.main([])
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--stage", "A", "--config", "C6",
                "--root", "workspace/l1b_deadbeef"])
    with pytest.raises(c.Refusal):
        c.main(["--execution-authorized", "--stage", "A",
                "--config", "C6",
                "--root", "workspace/l1b_deadbeef"])
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--execution-authorized",
                "--stage", "A", "--config", "C6",
                "--root", "workspace/wrong_deadbeef"])
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--execution-authorized",
                "--stage", "A", "--config", "C6",
                "--root", "workspace/o1_deadbeef"])
    for bad_stage in ("C", "a", "AB", ""):
        with pytest.raises(c.Refusal):
            c.main(["--execute-real", "--execution-authorized",
                    "--stage", bad_stage, "--config", "C6",
                    "--root", "workspace/l1b_deadbeef"])
    for bad_cfg in ("C7", "c6", "A208", ""):
        with pytest.raises(c.Refusal):
            c.main(["--execute-real", "--execution-authorized",
                    "--stage", "A", "--config", bad_cfg,
                    "--root", "workspace/l1b_deadbeef"])
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--execution-authorized",
                "--stage", "A", "--config", "C6",
                "--root", "workspace/l1b_aaaaaaaa",
                "--resume-from", "workspace/l1b_bbbbbbbb"])
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--execution-authorized",
                "--stage", "A", "--config", "C6",
                "--root", "workspace/l1b_deadbeef",
                "--de-label", "maybe"])
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--execution-authorized",
                "--stage", "A", "--config", "C6",
                "--root", "workspace/l1b_deadbeef",
                "--n-blocks", "0"])
    with pytest.raises(c.Refusal):
        c.main(["--execute-real", "--execution-authorized",
                "--stage", "A", "--config", "C6",
                "--root", "workspace/l1b_deadbeef",
                "--construct-trials", "0"])


# T2: root absent/present matrix + forbidden trees. -----------------------
def test_t2_root_absent_present_matrix(tmp_path):
    w, clk = MemWriter(), FakeClock()
    mf = _run("/tmp/opencode/l1b_fake_absent_01", w, clk, _decode_l1_ok,
              max_blocks=1)
    assert mf["verdict"] == "PROBE-truncated"
    with pytest.raises(c.Refusal):
        _run(str(tmp_path), MemWriter(), FakeClock(), _decode_l1_ok,
             max_blocks=1)
    with pytest.raises(c.Refusal):
        c.execute(root="/tmp/opencode/l1b_fake_absent_02", stage="A",
                  config="C6",
                  resume_from="/tmp/opencode/l1b_fake_absent_02",
                  construct_fn=_fake_construct_cfg("C6"),
                  decode_fn=_decode_l1_ok,
                  clock=FakeClock(), rss_fn=lambda: 0, writer=MemWriter())
    with pytest.raises(c.Refusal):
        c.execute(root="/tmp/opencode/l1b_fake_a", stage="A", config="C6",
                  resume_from="/tmp/opencode/l1b_fake_b",
                  construct_fn=_fake_construct_cfg("C6"),
                  decode_fn=_decode_l1_ok,
                  clock=FakeClock(), rss_fn=lambda: 0, writer=MemWriter())
    for bad in ("/tmp/opencode/results/l1b_fake_x",
                "/tmp/opencode/comparison_bench/outputs_comparison/"
                "l1b_fake_x"):
        with pytest.raises(c.Refusal):
            c.execute(root=bad, stage="A", config="C6",
                      construct_fn=_fake_construct_cfg("C6"),
                      decode_fn=_decode_l1_ok, clock=FakeClock(),
                      rss_fn=lambda: 0, writer=MemWriter(), max_blocks=1)


# T3: config table + system accounting + f_L1 informational. --------------
@pytest.mark.parametrize("config,m1,m2,f_l1", [
    ("C6", 6, 202, 1.142),
    ("C8", 8, 200, 1.522),
])
def test_t3_config_table_and_accounting(config, m1, m2, f_l1):
    assert c.CONFIGS[config]["m1"] == m1
    assert c.CONFIGS[config]["m2"] == m2
    assert c.CONFIGS[config]["lambda"] == {2: 1.0}
    assert c.CONFIGS[config]["l1_rate"] == pytest.approx(1.0 - m1 / 1024)
    basis = c.leak_basis(config)
    assert basis["m1"] == m1 and basis["m2"] == m2
    assert basis["m_total"] == 208
    assert basis["leak_bits"] == 1104.0
    assert basis["l1_leak_bits"] == float(5 * m1)
    assert basis["f_super_basis"] == pytest.approx(1.294947, abs=1e-6)
    assert "BUDGET MAPPING" in basis["f_super_label"]
    assert "not measured efficiency" in basis["f_super_label"]
    assert basis["f_L1_basis"] == pytest.approx(f_l1, abs=1e-3)
    assert "INFORMATIONAL ONLY" in basis["f_L1_label"]
    assert "never gated" in basis["f_L1_label"]
    assert basis["d_blind"] == 0.0
    assert "NEVER" in basis["d_blind_label"]
    assert "+0.019" in basis["sensitivity"]
    assert "4.31" in basis["blind_risk"]
    assert "D_blind>4" in basis["blind_risk"]
    assert c.MAX_ITER == 300
    assert c.L1B_BLOCK_BASE == 2026095601
    assert c.L1B_N_BLOCKS == 240
    assert c.L1B_CONSTRUCT_SEED == 2026092001
    assert c.fail_bar(240) == 12


def test_t3_unknown_config_refuses():
    for bad in ("C7", "c6", "A202", ""):
        with pytest.raises(c.Refusal):
            c.block_seed(bad, 0)
        with pytest.raises(c.Refusal):
            c.leak_basis(bad)
    calls = []

    def _counting(constructions, seed):
        calls.append(seed)
        return _decode_l1_ok(constructions, seed)

    with pytest.raises(c.Refusal) as exc:
        c.execute(root="/tmp/opencode/l1b_fake_badcfg", stage="A",
                  config="C7",
                  construct_fn=_fake_construct_cfg("C6"),
                  decode_fn=_counting, clock=FakeClock(),
                  rss_fn=lambda: 0, writer=MemWriter(), max_blocks=1)
    assert exc.value.code == 2
    assert calls == []
    with pytest.raises(c.Refusal):
        c.execute(root="/tmp/opencode/l1b_fake_badstage", stage="C",
                  config="C6",
                  construct_fn=_fake_construct_cfg("C6"),
                  decode_fn=_counting, clock=FakeClock(),
                  rss_fn=lambda: 0, writer=MemWriter(), max_blocks=1)
    assert calls == []


# T4: construct gate logic — fc/rank/twice gated, girth recorded. ---------
def test_t4_gate_pass_fake_mimic():
    cons = c._construct_gate("C6", _fake_construct_cfg("C6"),
                             2026092001, 20)
    assert set(cons) == {"m1", "m2"}
    assert cons["m1"]["m"] == 6 and cons["m2"]["m"] == 202
    assert cons["m1"]["construct_seed"] == 2026092001
    assert cons["m2"]["construct_trials"] == 20


def test_t4_girth_recorded_not_gated():
    def _g4(m_in, seed, max_trials):
        assert (seed, max_trials) == (2026092001, 20)
        return {"four_cycles": 0, "min_girth": 4, "rank": m_in,
                "family": "peg-irregular", "n": 1024, "m": m_in,
                "triples": [(0, 0, 1)]}

    cons = c._construct_gate("C8", _g4, 2026092001, 20)
    assert cons["m1"]["min_girth"] == 4  # recorded, never gated


@pytest.mark.parametrize("pin", ["fc", "rank", "twice", "status"])
def test_t4_pin_mismatch_stop_blocked(pin, capsys):
    # Amendment 2026-09-21 (memo option (a)): m1 legs record fc
    # (no gate); m2 legs keep fc==0 GATED. fc poison targets the m2
    # leg only (C6 m2=202); rank/twice/status poison both legs (m1
    # still GATED on those per task; m2 unchanged). Refusal lands on
    # the poisoned leg first (gate loops m1, m2).
    _m2 = c.CONFIGS["C6"]["m2"]

    def _bad(m_in, seed, max_trials):
        _bad.n += 1
        rec = {"four_cycles": 0, "min_girth": 8, "rank": m_in,
               "family": "peg-irregular", "n": 1024, "m": m_in,
               "triples": [(0, _bad.n if pin == "twice" else 0, 1)]}
        if pin == "fc":
            if m_in == _m2:
                rec["four_cycles"] = 1
        elif pin == "rank":
            rec["rank"] = m_in - 1
        elif pin == "status":
            rec["status"] = "frozen_failure"
        return rec
    _bad.n = 0
    calls = []

    def _counting(constructions, seed):
        calls.append(seed)
        return _decode_l1_ok(constructions, seed)

    with pytest.raises(c.Refusal) as exc:
        c.execute(root="/tmp/opencode/l1b_fake_pinbad", stage="A",
                  config="C6", construct_fn=_bad,
                  decode_fn=_counting, clock=FakeClock(),
                  rss_fn=lambda: 0, writer=MemWriter(), max_blocks=1)
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "STOP-BLOCKED" in err
    assert ("C6/m2" if pin == "fc" else "C6/m1") in err
    assert calls == []  # fail closed pre-decode


@pytest.mark.parametrize("config,fc1", [("C6", 34608), ("C8", 18368)])
def test_t4b_m1_dense_covariates_accept_recorded(config, fc1):
    # Amendment 2026-09-21 (memo option (a)): m1 legs (1024,6)/(1024,8)
    # ACCEPT with dense-check covariates recorded (measured 2026-09-20:
    # m=6 fc=34608/g4; m=8 fc=18368/g4); m2 legs stay fc==0 gated.
    spec = c.CONFIGS[config]

    def _dense(m_in, seed, max_trials):
        assert (seed, max_trials) == (2026092001, 20)
        girth, fc = (4, fc1) if m_in == spec["m1"] else (8, 0)
        return {"four_cycles": fc, "min_girth": girth, "rank": m_in,
                "family": "peg-irregular", "n": 1024, "m": m_in,
                "triples": [(0, 0, 1)],
                "total_sockets": 2048, "parallel_edges": 0}

    cons = c._construct_gate(config, _dense, 2026092001, 20)
    assert cons["m1"]["four_cycles"] == fc1  # recorded covariate
    assert cons["m1"]["min_girth"] == 4
    assert cons["m2"]["four_cycles"] == 0  # m2 gate-clean
    # Full gate path through execute: accepts (probe, 1 decode).
    calls = []

    def _counting(constructions, seed):
        calls.append(seed)
        return _decode_l1_ok(constructions, seed)

    w, clk = MemWriter(), FakeClock()
    mf = c.execute(root=f"/tmp/opencode/l1b_fake_m1dense_{config.lower()}",
                   stage="A", config=config, construct_fn=_dense,
                   decode_fn=_counting, clock=clk,
                   rss_fn=lambda: 0, writer=w, max_blocks=1)
    assert mf["verdict"] == "PROBE-truncated"
    assert calls == [2026095601]
    assert mf["construct"]["m1"]["four_cycles"] == fc1  # manifest records


# T5: dry-construct pins ×4 REAL (allowed, in-memory, no writes). ---------
_MEASURED: dict[int, dict] = {}


def _measured(m):
    if m not in _MEASURED:
        a = c.construct_code(m, 2026092001, 20)
        b = c.construct_code(m, 2026092001, 20)
        sa = sorted(tuple(map(int, t)) for t in a["triples"])
        sb = sorted(tuple(map(int, t)) for t in b["triples"])
        assert sa == sb  # construct-twice-identical holds
        _MEASURED[m] = a
    return _MEASURED[m]


@pytest.mark.parametrize("m", [6, 8, 202, 200])
def test_t5_dry_construct_pins_recorded(m):
    code = _measured(m)
    assert code["rank"] == m  # rank-full holds all four legs
    assert code["family"] == "peg-irregular"
    assert isinstance(code["four_cycles"], int)
    assert isinstance(code["min_girth"], int)
    if m in (202, 200):
        assert code["four_cycles"] == 0  # L2 legs gate-clean
        assert code["min_girth"] == 8
    else:
        # L1 legs (m=6/8): dense-check collapse per memo §2a —
        # fc≠0 recorded here; the amended gate ACCEPTS them (T5b,
        # amendment 2026-09-21, memo option (a)). Measured 2026-09-20
        # (seed 2026092001/trials 20): m=6 fc=34608/girth=4; m=8
        # fc=18368/girth=4.
        assert code["four_cycles"] == {6: 34608, 8: 18368}[m]
        assert code["min_girth"] == 4


@pytest.mark.parametrize("config", ["C6", "C8"])
def test_t5b_real_pins_m1_accept_amended(config):
    # Amendment 2026-09-21 (memo option (a)): the REAL measured m1 pins
    # through the REAL gate now ACCEPT (fc recorded-not-gated); m2 legs
    # stay fc==0 gated (gate-clean per T5). Replay serves the dry-
    # measured codes (T5) — pins are real, gate path is real.
    # Predecessor test_t5b_real_pins_stop_blocked_m1 (2026-09-20,
    # STOP-BLOCKED on m1 fc≠0) superseded by this amendment.
    def _replay(m_in, seed, max_trials):
        assert (seed, max_trials) == (2026092001, 20)
        src = _measured(m_in)
        return dict(src, triples=list(src["triples"]))

    calls = []

    def _counting(constructions, seed):
        calls.append(seed)
        return _decode_l1_ok(constructions, seed)

    w, clk = MemWriter(), FakeClock()
    mf = c.execute(root=f"/tmp/opencode/l1b_fake_m1accept_{config.lower()}",
                   stage="A", config=config, construct_fn=_replay,
                   decode_fn=_counting, clock=clk,
                   rss_fn=lambda: 0, writer=w, max_blocks=1)
    assert mf["verdict"] == "PROBE-truncated"
    assert calls == [2026095601]  # gate passed pre-decode; 1 decode ran
    assert mf["construct"]["m1"]["four_cycles"] > 0  # recorded covariate
    assert mf["construct"]["m1"]["four_cycles"] == _measured(
        c.CONFIGS[config]["m1"])["four_cycles"]
    assert mf["construct"]["m2"]["four_cycles"] == 0  # m2 gate-clean


# T6: L1 semantics — y1 mapping, L1-only rows, XOR identity, dry block. --
def test_t6_y1_mapping_matches_factor_layers():
    bundle = _fake_bundle()
    rng = np.random.default_rng(11)
    b, _, _ = c.s2c.empirical_triple_sampler(bundle, 64, rng)
    from comparison_bench.src.comparison_bench.formal_ir import (
        nonbinary_v29 as v29,
    )
    l1_f, l2_f = v29.factor_layers(b.tolist())
    assert np.array_equal(np.asarray((b >> 5) & 31), l1_f)
    assert np.array_equal(np.asarray(b & 31), l2_f)


def test_t6_posterior_rows_l1_no_u1_conditioning():
    bundle = _fake_bundle()
    rng = np.random.default_rng(3)
    b = rng.choice(1024, size=256, p=bundle["p_b"])
    u_a = rng.integers(0, 32, size=256)
    u_b = rng.integers(0, 32, size=256)
    rows = c.posterior_rows_l1(bundle, b)
    assert rows.shape == (256, 32)
    assert np.allclose(rows.sum(axis=1), 1.0, atol=1e-9)
    # EXACT v26 L236-237 semantics: p_u1_gb.T[b], no u1 argument exists.
    assert np.allclose(rows, np.asarray(bundle["g1"].T[b]))
    # L2 rows need u1 and differ (conditioned variant, s2c L288-316).
    rows_l2 = c.s2c.posterior_rows_l2(bundle, b, u_a)
    assert rows_l2.shape == (256, 32)
    assert not np.allclose(rows, rows_l2)
    with pytest.raises(TypeError):
        c.posterior_rows_l1(bundle, b, u_a)  # type: ignore[call-arg]
    with pytest.raises(c.Refusal):
        c.posterior_rows_l1(bundle, np.array([1024]))
    # XOR-centering identity (v28 L189-197 via s2c center_rows_prior).
    y1 = np.asarray((b >> 5) & 31, dtype=np.int64)
    prior = c.s2c.center_rows_prior(rows, y1)
    assert prior.shape == (256, 32)
    assert np.allclose(prior.sum(axis=1), 1.0, atol=1e-9)
    ee = np.arange(32, dtype=np.int64)
    for i in (0, 127, 255):
        assert np.allclose(prior[i], rows[i, y1[i] ^ ee])


def test_t6_dry_l1_block_wiring_posterior_entrypoint(monkeypatch):
    # 1-block dry L1: REAL decode_l1_block wrapper; fake matrix pieces
    # only (dense/syndrome/posterior-kernel). Sampler/rows/centering real.
    bundle = _fake_bundle()
    seen = {}

    def _fake_dense(triples, n, mm, field):
        assert (n, mm) == (1024, 6)
        return np.zeros((mm, n), dtype=np.int64)

    def _fake_syn(field, dense, vec):
        assert len(vec) == 1024
        return [0] * 6

    def _fake_posterior(field, y, matrix, s_x, prior, max_iter, **kw):
        seen.setdefault("calls", []).append(
            {"y": list(y), "s_x": list(s_x),
             "prior_shape": tuple(np.asarray(prior).shape),
             "prior_rowsums": np.asarray(prior).sum(axis=1),
             "max_iter": max_iter})
        assert tuple(np.asarray(prior).shape) == (1024, 32)
        return {"status": "success", "iterations": 7,
                "reconstruction_ok": True, "x_hat": list(y)}

    monkeypatch.setattr(c.peg, "sparse_to_dense", _fake_dense)
    monkeypatch.setattr(c.fftqspa, "syndrome_of", _fake_syn)
    monkeypatch.setattr(c.v28, "decode_error_domain_posterior",
                        _fake_posterior)
    construction = {"triples": [(0, 0, 1)], "n": 1024, "m": 6}
    out = c.decode_l1_block(construction, 2026095601, bundle, 1024, 6)
    assert len(seen["calls"]) == 1
    call = seen["calls"][0]
    assert call["max_iter"] == 300
    assert all(0 <= v < 32 for v in call["y"])
    assert np.allclose(call["prior_rowsums"], 1.0, atol=1e-9)
    # y1 half: bits 9..5 (values <32, and NOT the L2 low half in general).
    assert out["max_iter"] == 300
    assert out["stage"] == "A"
    assert isinstance(out["l1_exact"], bool)
    assert out["exact_match"] == out["l1_exact"]
    assert "no genie" in out["l1_conditioning"]
    src = inspect.getsource(c)
    bare = [ln for ln in src.splitlines()
            if "decode_error_domain(" in ln
            and "decode_error_domain_posterior" not in ln
            and "NEVER" not in ln and "scalar" not in ln]
    assert bare == []


def test_t6_l1_construction_nm_wiring_guard():
    bundle = _fake_bundle()
    with pytest.raises(c.Refusal):
        c.decode_l1_block({"triples": [], "n": 1024, "m": 6},
                          2026095601, bundle, 1024, 8)
    with pytest.raises(c.Refusal):
        c.decode_l1_block({"triples": [], "n": 256, "m": 6},
                          2026095601, bundle, 1024, 6)


# T7: combined wiring — û1-not-genie + dry block + L1-None fail-closed. --
def test_t7_combined_wiring_u1hat_not_genie(monkeypatch):
    # Deterministic triple (u1≡0); L1 leg returns û1≡1; the L2 row call
    # must carry û1≡1 (NOT genie zeros). L2 leg returns y2 ⇒ system fail
    # (recorded, dry only).
    n = 8
    b_fix = np.arange(n, dtype=np.int64) % 1024
    u1_fix = np.zeros(n, dtype=np.int64)
    u2_fix = np.zeros(n, dtype=np.int64)
    captured = {}

    def _fake_triple(bundle, nn, rng):
        assert nn == n
        return (b_fix, u1_fix, u2_fix)

    def _fake_dense(triples, nn, mm, field):
        return np.zeros((mm, nn), dtype=np.int64)

    def _fake_syn(field, dense, vec):
        return [0] * dense.shape[0]

    def _fake_posterior(field, y, matrix, s_x, prior, max_iter, **kw):
        if matrix.shape[0] == 6:  # L1 leg: û1≡1 (≠ genie u1≡0)
            return {"status": "success", "iterations": 5,
                    "reconstruction_ok": True, "x_hat": [1] * n}
        return {"status": "max_iter_reached", "iterations": 300,  # L2 leg
                "reconstruction_ok": False, "x_hat": list(y)}

    real_l2 = c.s2c.posterior_rows_l2

    def _spy_l2(bundle, b_vec, u1_vec):
        captured["u1_arg"] = np.asarray(u1_vec).tolist()
        return real_l2(bundle, b_vec, u1_vec)

    monkeypatch.setattr(c.s2c, "empirical_triple_sampler", _fake_triple)
    monkeypatch.setattr(c.peg, "sparse_to_dense", _fake_dense)
    monkeypatch.setattr(c.fftqspa, "syndrome_of", _fake_syn)
    monkeypatch.setattr(c.s2c, "posterior_rows_l2", _spy_l2)
    monkeypatch.setattr(c.v28, "decode_error_domain_posterior",
                        _fake_posterior)
    bundle = _fake_bundle()
    con1 = {"triples": [(0, 0, 1)], "n": n, "m": 6}
    con2 = {"triples": [(0, 0, 1)], "n": n, "m": 202}
    out = c.decode_combined_block(con1, con2, 2026095601, bundle,
                                  n, 6, 202)
    assert captured["u1_arg"] == [1] * n  # û1, NOT genie zeros
    assert out["stage"] == "B"
    assert out["chain"] == "real-L1 chain (genie retired)"
    assert out["l1_exact"] is False  # û1≡1 vs u1≡0
    assert out["l2_skipped"] is False
    assert out["exact_match"] is False  # system needs BOTH exact
    assert out["max_iter"] == 300


def test_t7_combined_l1_none_skips_l2(monkeypatch):
    n = 8

    def _fake_dense(triples, nn, mm, field):
        return np.zeros((mm, nn), dtype=np.int64)

    def _fake_syn(field, dense, vec):
        return [0] * dense.shape[0]

    calls = []

    def _fake_posterior(field, y, matrix, s_x, prior, max_iter, **kw):
        calls.append(matrix.shape[0])
        return {"status": "success", "iterations": 5,
                "reconstruction_ok": True, "x_hat": None}

    monkeypatch.setattr(c.peg, "sparse_to_dense", _fake_dense)
    monkeypatch.setattr(c.fftqspa, "syndrome_of", _fake_syn)
    monkeypatch.setattr(c.v28, "decode_error_domain_posterior",
                        _fake_posterior)
    out = c.decode_combined_block({"triples": [], "n": n, "m": 6},
                                  {"triples": [], "n": n, "m": 202},
                                  2026095601, _fake_bundle(), n, 6, 202)
    assert calls == [6]  # L2 never attempted
    assert out["l2_skipped"] is True
    assert out["l1_exact"] is False and out["l2_exact"] is False
    assert out["exact_match"] is False


def test_t7_combined_nm_wiring_guard():
    bundle = _fake_bundle()
    good = {"triples": [], "n": 1024, "m": 6}
    with pytest.raises(c.Refusal):
        c.decode_combined_block(good, {"triples": [], "n": 1024,
                                       "m": 200},
                                2026095601, bundle, 1024, 6, 202)
    with pytest.raises(c.Refusal):
        c.decode_combined_block({"triples": [], "n": 256, "m": 6}, good,
                                2026095601, bundle, 1024, 6, 202)


# T8: all-ok per stage-config → PASS; paired seeds; per-60 tally. --------
@pytest.mark.parametrize("stage,decode_ok", [
    ("A", _decode_l1_ok),
    ("B", _decode_combined_ok),
])
@pytest.mark.parametrize("config", ["C6", "C8"])
def test_t8_all_ok_pass_and_manifest(stage, decode_ok, config):
    w, clk = MemWriter(), FakeClock()
    root = f"/tmp/opencode/l1b_fake_allok_{stage.lower()}_{config.lower()}"
    seen = []

    def _rec(constructions, seed):
        _seen = seen
        assert set(constructions) == {"m1", "m2"}
        _seen.append(seed)
        return decode_ok(constructions, seed)

    mf = c.execute(root=root, stage=stage, config=config,
                   construct_fn=_fake_construct_cfg(config),
                   decode_fn=_rec, clock=clk,
                   rss_fn=lambda: 0, writer=w)
    assert mf["campaign"] == "L1B"
    assert mf["stage"] == stage
    assert mf["config"] == config
    assert mf["verdict"] == "PASS"
    assert mf["failures"] == 0
    assert mf["blocks_completed"] == 240
    assert mf["ledger"] == {"decodes": 240, "blocks_completed": 240}
    assert mf["fer_blocks"] == pytest.approx(0.0)
    assert mf["fail_bar"] == 12
    assert mf["pass_bar"] == "block FER<=5% (fails/240<=12)"
    assert mf["f_super"] == pytest.approx(1.294947, abs=1e-6)
    assert mf["quarter_tally"]["quarters_complete"] == 4
    assert mf["quarter_tally"]["quarters_le3"] == 4
    assert w.calls == 241  # 240 block checkpoints + 1 final
    assert mf["verify"] == {"pins_ok": True, "ledger_ok": True,
                            "rows_ok": True}
    rows = json.loads(w.store[f"{root}/rows.json"])
    assert len(rows) == 240
    assert [r["block"] for r in rows] == list(range(240))
    assert seen[0] == 2026095601 and seen[-1] == 2026095840
    assert len(seen) == 240
    mani = json.loads(w.store[f"{root}/manifest.json"])
    assert mani["seeds"]["block_base"] == 2026095601
    assert mani["construct"]["m1"]["m"] == c.CONFIGS[config]["m1"]
    assert mani["construct"]["m2"]["m"] == c.CONFIGS[config]["m2"]
    assert "STOP-BLOCKED" in mani["construct"]["pins"]
    assert "recorded-not-gated" in mani["construct"]["pins"]
    assert "NO independence claim" in mani["seeds"]["paired_note"]
    assert "A6 PASS" in mani["stage_gate"] and "A8 PASS" in mani["stage_gate"]
    assert mani["de_cover"]["label"] == "exploratory"
    assert "INFORMATIONAL ONLY" in mani["f_L1_label"]
    if stage == "A":
        assert "L1-only" in mani["stage_label"]
        assert all(r["l2_exact"] is None for r in rows)
    else:
        assert "real-L1 chain" in mani["stage_label"]
        assert "RETIRED" in mani["decoder"]["l1_conditioning"]
        assert all(r["l2_exact"] is True for r in rows)


# T9: early-stop at the 13th fail; bar-boundary PASS; budget terminal. ----
@pytest.mark.parametrize("stage,decode_fail", [
    ("A", _decode_l1_fail),
    ("B", _decode_combined_fail),
])
def test_t9_n240_early_stop_thirteenth_fail(stage, decode_fail):
    w, clk = MemWriter(), FakeClock()
    mf = c.execute(root=f"/tmp/opencode/l1b_fake_early240_{stage.lower()}",
                   stage=stage, config="C6",
                   construct_fn=_fake_construct_cfg("C6"),
                   decode_fn=decode_fail, clock=clk,
                   rss_fn=lambda: 0, writer=w)
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

    def _twelve_then_ok(constructions, seed):
        state["k"] += 1
        if state["k"] <= 12:
            return _decode_l1_fail(constructions, seed)
        return _decode_l1_ok(constructions, seed)

    w, clk = MemWriter(), FakeClock()
    mf = c.execute(root="/tmp/opencode/l1b_fake_bar12", stage="A",
                   config="C8",
                   construct_fn=_fake_construct_cfg("C8"),
                   decode_fn=_twelve_then_ok, clock=clk,
                   rss_fn=lambda: 0, writer=w)
    assert mf["verdict"] == "PASS"
    assert mf["failures"] == 12
    assert mf["blocks_completed"] == 240


def test_t9_budget_terminal_noresume(tmp_path):
    w, clk = MemWriter(), FakeClock()

    def _overrun(constructions, seed):
        clk.t += 301.0
        return _decode_l1_ok(constructions, seed)

    mf = _run("/tmp/opencode/l1b_fake_overrun", w, clk, _overrun,
              max_blocks=1)
    assert mf["verdict"] == "FAIL(budget)"
    assert mf["partial"] is True
    rows = json.loads(w.store["/tmp/opencode/l1b_fake_overrun/rows.json"])
    assert len(rows) == 1 and rows[0]["status"] == "overrun"
    root = str(tmp_path / "l1b_fake_budget_noresume")
    import os as _os
    _os.makedirs(root, exist_ok=True)
    with open(f"{root}/manifest.json", "w") as fh:
        fh.write(w.store["/tmp/opencode/l1b_fake_overrun/manifest.json"])
    with open(f"{root}/rows.json", "w") as fh:
        fh.write(w.store["/tmp/opencode/l1b_fake_overrun/rows.json"])
    with pytest.raises(c.Refusal):
        c.execute(root=root, stage="A", config="C6",
                  resume_from=root,
                  construct_fn=_fake_construct_cfg("C6"),
                  decode_fn=_decode_l1_ok, clock=FakeClock(),
                  rss_fn=lambda: 0, writer=MemWriter())


# T10: checkpoint/resume — one wall-partial; 2nd/stage-swap refuses. ------
def test_t10_resume_continuation_single_wall_window(tmp_path):
    root = str(tmp_path / "l1b_fake_resume")
    w1, clk1 = MemWriter(), FakeClock()

    def _advancing(constructions, seed):
        clk1.t += 100.0
        return _decode_combined_ok(constructions, seed)

    part = c.execute(root=root, stage="B", config="C6",
                     construct_fn=_fake_construct_cfg("C6"),
                     decode_fn=_advancing, clock=clk1,
                     rss_fn=lambda: 0, writer=w1)
    assert part["verdict"] == "INCOMPLETE-wall"
    assert part["blocks_completed"] == 37
    assert part["next_block"] == 37
    assert part["ledger"]["decodes"] == 37
    rows_p = json.loads(w1.store[f"{root}/rows.json"])
    w2, clk2 = MemWriter(), FakeClock()

    def _fast(constructions, seed):
        clk2.t += 1.0
        return _decode_combined_ok(constructions, seed)

    import os as _os
    _os.makedirs(root, exist_ok=True)
    with open(f"{root}/manifest.json", "w") as fh:
        fh.write(w1.store[f"{root}/manifest.json"])
    with open(f"{root}/rows.json", "w") as fh:
        fh.write(w1.store[f"{root}/rows.json"])
    done = c.execute(root=root, stage="B", config="C6",
                     resume_from=root,
                     construct_fn=_fake_construct_cfg("C6"),
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
    # A resumed-twice partial (2 windows) refuses with zero decodes.
    with open(f"{root}/manifest.json", "w") as fh:
        fh.write(w2.store[f"{root}/manifest.json"])
    with open(f"{root}/rows.json", "w") as fh:
        fh.write(w2.store[f"{root}/rows.json"])
    calls = []

    def _counting(constructions, seed):
        calls.append(seed)
        return _decode_combined_ok(constructions, seed)

    with pytest.raises(c.Refusal) as exc:
        c.execute(root=root, stage="B", config="C6", resume_from=root,
                  construct_fn=_fake_construct_cfg("C6"),
                  decode_fn=_counting, clock=FakeClock(),
                  rss_fn=lambda: 0, writer=MemWriter())
    assert exc.value.code == 2
    assert calls == []


def test_t10_resume_stage_config_mismatch_refuses(tmp_path):
    root = str(tmp_path / "l1b_fake_resume_swap")
    w1, clk1 = MemWriter(), FakeClock()

    def _advancing(constructions, seed):
        clk1.t += 100.0
        return _decode_l1_ok(constructions, seed)

    part = c.execute(root=root, stage="A", config="C6",
                     construct_fn=_fake_construct_cfg("C6"),
                     decode_fn=_advancing, clock=clk1,
                     rss_fn=lambda: 0, writer=w1)
    assert part["verdict"] == "INCOMPLETE-wall"
    import os as _os
    _os.makedirs(root, exist_ok=True)
    with open(f"{root}/manifest.json", "w") as fh:
        fh.write(w1.store[f"{root}/manifest.json"])
    with open(f"{root}/rows.json", "w") as fh:
        fh.write(w1.store[f"{root}/rows.json"])
    for stage, config in (("B", "C6"), ("A", "C8")):
        with pytest.raises(c.Refusal):
            c.execute(root=root, stage=stage, config=config,
                      resume_from=root,
                      construct_fn=_fake_construct_cfg(config),
                      decode_fn=_decode_l1_ok, clock=FakeClock(),
                      rss_fn=lambda: 0, writer=MemWriter())


# T11: no writes outside root; csv schema; l1b prefix gate. ---------------
def test_t11_no_writes_outside_root_and_csv():
    assert c._allows_root("workspace/l1b_deadbeef")
    assert not c._allows_root("workspace/o1_deadbeef")
    assert not c._allows_root("workspace/p0_deadbeef")
    assert not c._allows_root("workspace/s2c_deadbeef")
    w, clk = MemWriter(), FakeClock()
    root = "/tmp/opencode/l1b_fake_nowrite"
    _run(root, w, clk, _decode_combined_ok, stage="B", max_blocks=1)
    assert set(w.store) == {f"{root}/manifest.json", f"{root}/rows.json",
                            f"{root}/block_accounting.csv"}
    assert w.store[f"{root}/block_accounting.csv"].splitlines()[0] == (
        "block,seed,l1_exact,l2_exact,exact_match,status,iterations,"
        "wall_s,d_blind,leak_bits,f_super")
    rows = json.loads(w.store[f"{root}/rows.json"])
    assert rows[0]["chain"] == "real-L1 chain (genie retired)"
    assert rows[0]["l2_skipped"] is False


def test_t11_de_label_threading():
    w, clk = MemWriter(), FakeClock()
    mf = _run("/tmp/opencode/l1b_fake_delabel", w, clk, _decode_l1_ok,
              stage="A", config="C6", max_blocks=1, de_label="covered")
    assert mf["de_cover"]["label"] == "covered"
    assert "explicit --de-label" in mf["de_cover"]["label_source"]
    with pytest.raises(c.Refusal):
        _run("/tmp/opencode/l1b_fake_delabel_bad", MemWriter(),
             FakeClock(), _decode_l1_ok, stage="A", config="C6",
             max_blocks=1, de_label="maybe")


# T12: SCAN trade-scan L1 arms — C12A/C16A Stage-A-only (memo v2 §2). --
def _fake_construct_scan_cfg(config):
    # Stage-A-only mimic: m1 leg only (m2 is None — never constructed).
    # Signature mirrors production construct_code(m, seed, max_trials).
    spec = c.CONFIGS[config]
    assert spec["m2"] is None and spec.get("stage_a_only") is True

    def _build(m_in, seed, max_trials):
        assert (seed, max_trials) == (2026092001, 20)
        assert m_in == spec["m1"]
        return {"four_cycles": 0, "min_girth": 8, "rank": m_in,
                "family": "peg-irregular", "n": 1024, "m": m_in,
                "triples": [(0, 0, 1), (1, 1, 2)],
                "total_sockets": 2048, "parallel_edges": 0}

    return _build


def _run_scan(root, writer, clock, decode_fn, config, **kw):
    return c.execute(root=root, stage="A", config=config,
                     construct_fn=_fake_construct_scan_cfg(config),
                     decode_fn=decode_fn, clock=clock,
                     rss_fn=lambda: 0, writer=writer, **kw)


@pytest.mark.parametrize("config,m1,l1_leak,f_l1", [
    ("C12A", 12, 60.0, 2.2833),
    ("C16A", 16, 80.0, 3.0444),
])
def test_t12_scan_config_table_and_accounting(config, m1, l1_leak, f_l1):
    assert c.CONFIGS[config]["m1"] == m1
    assert c.CONFIGS[config]["m2"] is None  # NOT constructed
    assert c.CONFIGS[config].get("stage_a_only") is True
    assert c.CONFIGS[config]["lambda"] == {2: 1.0}
    assert c.CONFIGS[config]["l1_rate"] == pytest.approx(1.0 - m1 / 1024)
    basis = c.leak_basis(config)
    assert basis["m1"] == m1 and basis["m2"] is None
    assert basis["m_total"] == 208  # frozen total-208 line carried
    assert basis["leak_bits"] == 1104.0
    assert basis["l1_leak_bits"] == l1_leak
    assert basis["f_super_basis"] == pytest.approx(1.294947, abs=1e-6)
    assert "BUDGET MAPPING" in basis["f_super_label"]
    assert "DEFERRED" in basis["f_super_label"]
    assert basis["f_L1_basis"] == pytest.approx(f_l1, abs=1e-3)
    assert "INFORMATIONAL ONLY" in basis["f_L1_label"]
    assert "never gated" in basis["f_L1_label"]
    assert "deferred" in basis["blind_risk"]
    # Paired block seeds work for the new configs.
    assert c.block_seed(config, 0) == 2026095601
    assert c.block_seed(config, 239) == 2026095840


def test_t12_scan_unknown_config_still_refuses():
    for bad in ("C7", "C9", "C12", "C16", "c12a", ""):
        with pytest.raises(c.Refusal):
            c.block_seed(bad, 0)
        with pytest.raises(c.Refusal):
            c.leak_basis(bad)
    calls = []

    def _counting(constructions, seed):
        calls.append(seed)
        return _decode_l1_ok(constructions, seed)

    with pytest.raises(c.Refusal) as exc:
        c.execute(root="/tmp/opencode/l1b_fake_scanbadcfg", stage="A",
                  config="C12",
                  construct_fn=_fake_construct_scan_cfg("C12A"),
                  decode_fn=_counting, clock=FakeClock(),
                  rss_fn=lambda: 0, writer=MemWriter(), max_blocks=1)
    assert exc.value.code == 2
    assert calls == []


def test_t12_scan_gate_constructs_m1_only():
    for config, m1 in (("C12A", 12), ("C16A", 16)):
        seen = []
        inner = _fake_construct_scan_cfg(config)

        def _spy(m_in, seed, max_trials):
            seen.append(m_in)
            return inner(m_in, seed, max_trials)

        cons = c._construct_gate(config, _spy, 2026092001, 20)
        assert set(cons) == {"m1"}  # no m2 leg constructed
        assert cons["m1"]["m"] == m1
        assert cons["m1"]["rank"] == m1  # rank-full gated
        assert cons["m1"]["construct_seed"] == 2026092001
        assert cons["m1"]["construct_trials"] == 20
        assert seen == [m1, m1]  # construct-twice on the m1 leg only


def test_t12_scan_pin_gating_rank_twice_stop_blocked(capsys):
    # Rank/twice mismatch on the m1 leg STOP-BLOCKED pre-decode; dense
    # fc/girth covariates (dry 2026-09-21: m12 fc7767/g4, m16 fc4177/g4)
    # are RECORDED-not-gated per the Amendment.
    def _dense(m_in, seed, max_trials):
        assert (seed, max_trials) == (2026092001, 20)
        fc = {12: 7767, 16: 4177}[m_in]
        return {"four_cycles": fc, "min_girth": 4, "rank": m_in,
                "family": "peg-irregular", "n": 1024, "m": m_in,
                "triples": [(0, 0, 1)],
                "total_sockets": 2048, "parallel_edges": 0}

    cons = c._construct_gate("C16A", _dense, 2026092001, 20)
    assert set(cons) == {"m1"}
    assert cons["m1"]["four_cycles"] == 4177  # recorded covariate
    assert cons["m1"]["min_girth"] == 4

    def _bad_rank(m_in, seed, max_trials):
        return {"four_cycles": 0, "min_girth": 8, "rank": m_in - 1,
                "family": "peg-irregular", "n": 1024, "m": m_in,
                "triples": [(0, 0, 1)]}

    calls = []

    def _counting(constructions, seed):
        calls.append(seed)
        return _decode_l1_ok(constructions, seed)

    with pytest.raises(c.Refusal) as exc:
        c.execute(root="/tmp/opencode/l1b_fake_scanpinbad", stage="A",
                  config="C12A", construct_fn=_bad_rank,
                  decode_fn=_counting, clock=FakeClock(),
                  rss_fn=lambda: 0, writer=MemWriter(), max_blocks=1)
    assert exc.value.code == 2
    assert "STOP-BLOCKED" in capsys.readouterr().err
    assert calls == []  # fail closed pre-decode


@pytest.mark.parametrize("m,fc", [(12, 7767), (16, 4177)])
def test_t12_scan_dry_construct_pins_real(m, fc):
    # Dry construction via the REAL constructor (allowed, in-memory, no
    # writes, no decodes): rank-full + twice-identical gated; fc/girth
    # recorded (dense-check regime per memo v2 §1).
    a = c.construct_code(m, 2026092001, 20)
    b = c.construct_code(m, 2026092001, 20)
    sa = sorted(tuple(map(int, t)) for t in a["triples"])
    sb = sorted(tuple(map(int, t)) for t in b["triples"])
    assert sa == sb  # construct-twice-identical holds
    assert a["rank"] == m
    assert a["four_cycles"] == fc
    assert a["min_girth"] == 4
    # The REAL measured pins through the REAL gate ACCEPT (Amendment).
    gated = c._construct_gate("C12A" if m == 12 else "C16A",
                              c.construct_code, 2026092001, 20)
    assert set(gated) == {"m1"}
    assert gated["m1"]["four_cycles"] == fc


def test_t12_scan_stage_a_execute_probe_manifest():
    w, clk = MemWriter(), FakeClock()
    root = "/tmp/opencode/l1b_fake_scanA_c16a"
    seen = []

    def _rec(constructions, seed):
        assert set(constructions) == {"m1"}
        seen.append(seed)
        return _decode_l1_ok(constructions, seed)

    mf = c.execute(root=root, stage="A", config="C16A",
                   construct_fn=_fake_construct_scan_cfg("C16A"),
                   decode_fn=_rec, clock=clk,
                   rss_fn=lambda: 0, writer=w, max_blocks=1)
    assert mf["campaign"] == "L1B"
    assert mf["stage"] == "A"
    assert mf["config"] == "C16A"
    assert mf["verdict"] == "PROBE-truncated"
    assert mf["n_blocks"] == 240
    assert mf["fail_bar"] == 12
    assert seen == [2026095601]
    mani = json.loads(w.store[f"{root}/manifest.json"])
    assert mani["construct"]["m1"]["m"] == 16
    assert mani["construct"]["m2"]["m"] is None
    assert "NOT CONSTRUCTED" in mani["construct"]["m2"]["note"]
    assert "NOT CONSTRUCTED" in mani["construct"]["pins"]
    assert "STOP-BLOCKED" in mani["construct"]["pins"]
    assert mani["leak_bits"] == 1104.0
    assert mf["f_super"] == pytest.approx(1.294947, abs=1e-6)
    assert mani["de_cover"]["label"] == "exploratory"
    rows = json.loads(w.store[f"{root}/rows.json"])
    assert rows[0]["seed"] == 2026095601
    assert rows[0]["l2_exact"] is None  # Stage A: L1-only


def test_t12_scan_stage_b_refuses_zero_decodes():
    calls = []

    def _counting(constructions, seed):
        calls.append(seed)
        return _decode_combined_ok(constructions, seed)

    for config in ("C12A", "C16A"):
        with pytest.raises(c.Refusal) as exc:
            c.execute(root=f"/tmp/opencode/l1b_fake_scanB_{config.lower()}",
                      stage="B", config=config,
                      construct_fn=_fake_construct_scan_cfg(config),
                      decode_fn=_counting, clock=FakeClock(),
                      rss_fn=lambda: 0, writer=MemWriter(), max_blocks=1)
        assert exc.value.code == 2
        # CLI path refuses identically (dual-flag + stage/config gate).
        with pytest.raises(c.Refusal):
            c.main(["--execute-real", "--execution-authorized",
                    "--stage", "B", "--config", config,
                    "--root", "workspace/l1b_deadbeef"])
    assert calls == []


def test_t12_scan_n240_bar12_early_stop():
    w, clk = MemWriter(), FakeClock()
    mf = c.execute(root="/tmp/opencode/l1b_fake_scan_early240", stage="A",
                   config="C12A",
                   construct_fn=_fake_construct_scan_cfg("C12A"),
                   decode_fn=_decode_l1_fail, clock=clk,
                   rss_fn=lambda: 0, writer=w)
    assert mf["verdict"] == "FAIL-early-stop"
    assert mf["blocks_completed"] == 13
    assert mf["failures"] == 13
    assert mf["n_blocks"] == 240
    assert mf["fail_bar"] == 12
