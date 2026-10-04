"""Fake-only tests for the M0 real-frame runner (no .ttbin, no real data).

The only decoder call here is the parity test, which decodes ONE synthetic
superframe drawn from the frozen gamma_f03 channel and checks that the new
real-frame decode path reproduces the frozen b2f procedure bit-for-bit.
"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.cli.probes_closed import m0_realframe_runner as m0

REPO = Path(__file__).resolve().parents[3]


def _fresh_root() -> str:
    return f"workspace/m0__pytest_{uuid.uuid4().hex[:8]}"


def _fake_construct(m, seed, trials):
    return {"triples": [(0, 0, 1)], "status": "ok", "four_cycles": 0,
            "min_girth": 8, "rank": m, "n": m0.N, "m": m}


def _fake_bundle(_source):
    g1 = np.zeros((32, 1024)); g1[0, :] = 1.0
    g2 = np.zeros((32, 32, 1024)); g2[:, 0, :] = 1.0
    return {"g1": g1, "g2": g2, "p_b": np.full(1024, 1 / 1024), "path": "<fake>"}


def _fake_series(n_symbols):
    def fn(_source):
        rng = np.random.default_rng(1)
        a = rng.integers(0, 1024, n_symbols)
        return {"a": a, "b": a.copy(), "ttbin": "<fake>", "offset_ps": 50,
                "n_pairs_eval": n_symbols}
    return fn


def test_main_refuses_without_both_flags():
    with pytest.raises(m0.Refusal):
        m0.main(["--source", "2M", "--root", _fresh_root()])
    with pytest.raises(m0.Refusal):
        m0.main(["--source", "2M", "--root", _fresh_root(), "--execute-real"])


def test_root_rules():
    with pytest.raises(m0.Refusal):
        m0._check_root("workspace/x1_abc")
    with pytest.raises(m0.Refusal):
        m0._check_root("workspace/m0_x/results/y")
    m0._check_root(_fresh_root())  # fresh + right prefix passes


def test_superframes_drop_remainder():
    a = np.arange(2500)
    blocks = m0.superframes(a, a)
    assert len(blocks) == 2
    assert blocks[1][0][0] == 1024 and blocks[1][0].size == 1024


def test_recover_u1_uses_joint_argmax():
    g1 = np.full((32, 1024), 1 / 32)
    g2 = np.full((32, 32, 1024), 1 / 32)
    g2[7, 3, 5] = 1.0  # given b=5 and u2=3, u1=7 is the only strong candidate
    u1 = m0.recover_u1({"g1": g1, "g2": g2}, np.array([5]), np.array([3]))
    assert u1.tolist() == [7]


def test_accounting_and_wilson():
    assert m0.f_super("2M", 208) == pytest.approx(1104 / (1024 * m0.H_CORR["2M"]))
    assert m0.f_notag("2M", 208) == pytest.approx(1040 / (1024 * m0.H_CORR["2M"]))
    lo, hi = m0.wilson(0, 240)
    assert lo == 0.0 and 0.01 < hi < 0.02


def test_execute_with_fakes_counts_classes_and_overrun():
    root = _fresh_root()
    calls = {"n": 0}
    clock_t = {"t": 0.0}

    def clock():
        return clock_t["t"]

    def decode(construction, a, b, bundle, m):
        calls["n"] += 1
        k = calls["n"]
        clock_t["t"] += 400.0 if k == 3 else 1.0  # 3rd decode overruns
        if k == 2:
            return {"exact_match": False, "reconstruction_ok": True, "status": "converged"}
        return {"exact_match": True, "full10_match": k != 4, "reconstruction_ok": True,
                "status": "converged"}

    try:
        s = m0.execute(source="2M", root=root, series_fn=_fake_series(3 * 1024 + 7),
                       bundle_fn=_fake_bundle, construct_fn=_fake_construct,
                       decode_fn=decode, clock=clock, rss_fn=lambda: 0.1)
        assert s["verdict"] == "COMPLETE"
        assert s["n_superframes"] == 3 and s["remainder_symbols"] == 7
        first, second = s["arms"]
        assert (first["m"], second["m"]) == (204, 208)
        # arm 204: decode1 ok, decode2 undetected, decode3 overrun ⇒ 2 fails, 1 undetected
        assert first["fails"] == 2 and first["undetected"] == 1 and first["overruns"] == 1
        # arm 208: decode4 u2-exact but full10 mismatch, decode5/6 ok
        assert second["fails"] == 0 and second["fails_full10"] == 1
        assert second["f_eff"] == pytest.approx(second["f_super"])
        assert Path(root, "M0_RESULT_2M.md").exists()
        assert Path(root, "block_accounting.csv").read_text().count("\n") == 7
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_decode_real_matches_frozen_b2f_on_synthetic_superframe():
    """Wiring parity: same synthetic draw ⇒ identical decode outcome."""
    from comparison_bench.src.comparison_bench.formal_ir import v80_b2f_campaign as b2f
    from comparison_bench.src.comparison_bench.formal_ir import v80_s2c_campaign as s2c
    from comparison_bench.src.comparison_bench.cli import x1_arm_runner as x1

    gamma = str(REPO / "docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz")
    bundle = s2c.bind_empirical_bundle(gamma, "2M")
    m, seed = 208, 2026095601
    construction = x1.construct_standalone(m)
    ref = b2f.decode_block_marginal(construction, seed, bundle, m0.N, m)
    rng = np.random.default_rng(b2f.stream_seed(seed))  # same stream as the frozen draw
    b, u1, u2 = s2c.empirical_triple_sampler(bundle, m0.N, rng)
    a = (u1 << 5) | u2
    out = m0.decode_real(construction, a, b, bundle, m)
    assert out["exact_match"] == ref["exact_match"]
    assert out["iterations"] == ref["iterations"]
