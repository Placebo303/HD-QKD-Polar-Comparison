"""V72P2D3 GF32 contrast synthetic qualification; no real data or prod paths."""
from __future__ import annotations

import importlib.util
import inspect
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
# ponytail: one-line src path so frozen V54 absolute import resolves in-path.
sys.path.insert(0, str(ROOT / "src"))
MODULE_PATH = ROOT / "src" / "comparison_bench" / "formal_ir" / "v72p2d3_gf32_contrast.py"
RUNNER_PATH = ROOT.parent / "scripts" / "v72p2d3_gf32_contrast.py"

SPEC = importlib.util.spec_from_file_location("v72p2d3_contrast_test_module", str(MODULE_PATH))
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

RSPEC = importlib.util.spec_from_file_location("v72p2d3_runner_test_module", str(RUNNER_PATH))
assert RSPEC is not None and RSPEC.loader is not None
runner = importlib.util.module_from_spec(RSPEC)
RSPEC.loader.exec_module(runner)


def test_d6_01_field_q32_poly37_known_answers():
    field = mod.get_gf32_field()
    assert int(field.q) == 32
    assert int(field.primitive_polynomial) == 37
    assert field.add(5, 3) == (5 ^ 3)
    assert field.add(0, 17) == 17
    for v in (1, 2, 5, 17, 31):
        assert field.mul(v, 1) == v
        assert field.mul(v, 0) == 0
        assert field.mul(v, field.inverse(v)) == 1
    assert field.inverse(1) == 1
    assert len(field.nonzero_cycle) == 31
    assert len(set(field.nonzero_cycle)) == 31
    # R1/R2: unique history kernel is v35 row-layered FFT-QSPA via V54 chain.
    assert mod.history_kernel_id() == "V35-decode_row_layered_fftqspa-via-V54-chain"
    assert mod.HISTORY_DECODER_FN == "v35_algorithm_development.decode_row_layered_fftqspa"
    assert "V54" in mod.HISTORY_L2_CHAIN
    # Field is unified to v35 (no separate nonbinary_field binding).
    src = MODULE_PATH.read_text(encoding="utf-8")
    assert "v35_algorithm_development" in src
    assert "nonbinary_field" not in src


def test_d6_02_mapping_roundtrip_1024_lsb():
    for s in range(1024):
        low, high = mod.split_symbol(s)
        assert low == (s & 31)
        assert high == ((s >> 5) & 31)
        assert mod.combine_symbol(low, high) == s
    syms = np.arange(1024, dtype=np.int64)
    low_arr, high_arr = mod.symbols_to_layers(syms)
    back = mod.layers_to_symbols(low_arr, high_arr)
    assert np.array_equal(back, syms)


def test_d6_03_s_equals_32u1_plus_u2_direction():
    rng = np.random.default_rng(20260902)
    low = rng.integers(0, 32, size=64, dtype=np.int64)
    high = rng.integers(0, 32, size=64, dtype=np.int64)
    syms = mod.layers_to_symbols(low, high)
    assert np.array_equal(syms, low + 32 * high)
    low2, high2 = mod.symbols_to_layers(syms)
    assert np.array_equal(low2, low)
    assert np.array_equal(high2, high)
    for s in (0, 1, 31, 32, 33, 511, 1023):
        lo, hi = mod.split_symbol(int(s))
        assert int(s) == int(lo) + 32 * int(hi)
    # Frozen history direction: v35 factorize_f03 gives u1=high MSB, u2=low LSB.
    alice = np.array([0, 1, 31, 32, 33, 511, 1023], dtype=np.int64)
    bob = np.zeros_like(alice)
    u1, u2, _, _ = mod.factorize_f03_binding(alice, bob)
    lo_arr, hi_arr = mod.symbols_to_layers(alice)
    assert np.array_equal(u1.astype(np.int64), hi_arr)
    assert np.array_equal(u2.astype(np.int64), lo_arr)


def test_d6_04_h_nested_geometry_shapes_ranks():
    geo = mod.nested_geometry()
    assert geo["m_base"] == 184
    assert geo["h1_rows"] == 16
    assert geo["m_total"] == 200
    assert tuple(geo["nested"]) == (184, 192, 200)
    assert geo["shapes"] == [(184, 1024), (192, 1024), (200, 1024)]
    assert geo["leak"] == (1064, 1104, 1144)
    h_base, h_joint, h_total = mod.build_tiny_nested()
    assert h_base.shape[1] == h_joint.shape[1] == h_total.shape[1] == 8
    assert h_base.shape[0] == 4 and h_joint.shape[0] == 6 and h_total.shape[0] == 8
    assert np.array_equal(h_joint[:4], h_base)
    assert np.array_equal(h_total[:4], h_base)
    assert np.array_equal(h_total[:6], h_joint)
    assert mod._gf2_rank(h_base) == 4
    assert mod._gf2_rank(h_joint) == 6
    assert mod._gf2_rank(h_total) == 8
    assert int(np.max(np.sum(h_total, axis=1))) <= 16
    assert int(np.max(np.sum(h_total, axis=0))) <= 1


def test_d6_05_prior_stage1_normalized():
    rng = np.random.default_rng(20260902)
    bob_cal = rng.integers(0, 8, size=200, dtype=np.int64)
    high_cal = rng.integers(0, 32, size=200, dtype=np.int64)
    p1 = mod.build_stage1_P(bob_cal, high_cal, 1.0, n_b_states=8, q_sub=32)
    assert p1.shape == (8, 32)
    assert np.all(np.isfinite(p1))
    assert np.all(p1 > 0)
    assert np.allclose(p1.sum(axis=1), 1.0)


def test_d6_06_prior_stage2_normalized_per_high_row():
    rng = np.random.default_rng(20260903)
    bob_cal = rng.integers(0, 8, size=300, dtype=np.int64)
    high_cal = rng.integers(0, 4, size=300, dtype=np.int64)
    low_cal = rng.integers(0, 4, size=300, dtype=np.int64)
    p2 = mod.build_stage2_P(high_cal, bob_cal, low_cal, 1.0, n_b_states=8, q_sub=4)
    assert p2.shape == (4, 8, 4)
    assert np.all(np.isfinite(p2))
    assert np.all(p2 > 0)
    for a in range(4):
        for b in range(8):
            assert p2[a, b].sum() == pytest.approx(1.0)


def test_d6_07_k_p_prior_logp_finite_and_exp_matches():
    rng = np.random.default_rng(20260902)
    bob_cal = rng.integers(0, 8, size=200, dtype=np.int64)
    high_cal = rng.integers(0, 32, size=200, dtype=np.int64)
    p1 = mod.build_stage1_P(bob_cal, high_cal, 2.0, n_b_states=8, q_sub=32)
    lp = mod.prior_logp_from_P(p1)
    assert np.all(np.isfinite(lp))
    assert np.all(np.isfinite(p1))
    back = np.exp(lp)
    assert np.allclose(back, p1)
    assert np.allclose(back.sum(axis=1), 1.0)
    assert np.all(back > 0)


def test_d6_08_ce_chain_log2_and_natural_log_conversion():
    rng = np.random.default_rng(20260904)
    n_b, q_sub, n_eval = 8, 4, 120
    bob_cal = rng.integers(0, n_b, size=400, dtype=np.int64)
    high_cal = rng.integers(0, q_sub, size=400, dtype=np.int64)
    low_cal = rng.integers(0, q_sub, size=400, dtype=np.int64)
    p1 = mod.build_stage1_P(bob_cal, high_cal, 1.5, n_b_states=n_b, q_sub=q_sub)
    p2 = mod.build_stage2_P(high_cal, bob_cal, low_cal, 1.5, n_b_states=n_b, q_sub=q_sub)
    bob_ev = rng.integers(0, n_b, size=n_eval, dtype=np.int64)
    high_ev = rng.integers(0, q_sub, size=n_eval, dtype=np.int64)
    low_ev = rng.integers(0, q_sub, size=n_eval, dtype=np.int64)
    ce_high = mod.ce_stage1_log2(p1, bob_ev, high_ev)
    ce_low = mod.ce_stage2_log2(p2, high_ev, bob_ev, low_ev)
    ce_joint = mod.ce_joint_log2(p1, p2, bob_ev, high_ev, low_ev)
    assert np.isfinite(ce_high) and np.isfinite(ce_low) and np.isfinite(ce_joint)
    assert abs(ce_joint - ce_high - ce_low) < 1e-9
    lp1 = mod.prior_logp_from_P(p1)
    manual = float(-np.mean(lp1[bob_ev, high_ev] / mod.LN2))
    assert manual == pytest.approx(ce_high)


def test_d6_09_builder_only_bob_cal_rejects_forbidden_selection():
    for fn in (mod.build_stage1_P, mod.build_stage2_P):
        params = set(inspect.signature(fn).parameters)
        for forbidden in ("alice", "old_session", "val_frame", "val_selection"):
            assert forbidden not in params
    with pytest.raises(TypeError):
        mod.build_stage1_P(
            np.zeros(4, dtype=np.int64),
            np.zeros(4, dtype=np.int64),
            1.0,
            n_b_states=8,
            q_sub=4,
            alice=np.zeros(4, dtype=np.int64),
        )
    with pytest.raises(TypeError):
        mod.build_stage2_P(
            np.zeros(4, dtype=np.int64),
            np.zeros(4, dtype=np.int64),
            np.zeros(4, dtype=np.int64),
            1.0,
            n_b_states=8,
            q_sub=4,
            alice=np.zeros(4, dtype=np.int64),
        )


def test_d6_10_g_hard_cap_90_damping_no_tolerance():
    n = 6
    prior = mod.prior_logp_from_P(np.full((n, 32), 1.0 / 32.0))
    h_mat = np.eye(n, n, dtype=np.uint8)
    target = np.zeros(n, dtype=np.uint8)
    # Production path directly calls the true history kernel (no mock).
    ok = mod.run_g_layer(prior, target, h_mat, max_iter=90, damping_alpha=1.0)
    assert ok["iters"] <= 90
    assert ok["iterations_used"] <= 90
    assert 0 <= ok["iterations_used"] <= 90
    assert ok["finite"]
    assert ok["residual"] == mod.RESIDUAL_NOT_RECORDED
    assert ok["cold_start"] is True
    for key in ("x_hat", "syndrome_observed", "syndrome_ok", "runtime_s", "stop"):
        assert key in ok
    assert np.array_equal(
        np.asarray(ok["syndrome_observed"]),
        np.asarray(mod.gf32_syndrome(h_mat, ok["x_hat"])),
    )
    assert ok["syndrome_ok"] == ok["syndrome_satisfied"]
    with pytest.raises(ValueError):
        mod.run_g_layer(prior, target, h_mat, max_iter=91, damping_alpha=1.0)
    with pytest.raises(ValueError):
        mod.run_g_layer(prior, target, h_mat, max_iter=90, damping_alpha=0.5)
    params = set(inspect.signature(mod.run_g_layer).parameters)
    assert "tol" not in params
    assert "tolerance" not in params
    assert params >= {"prior_logp", "syndrome_target", "h_matrix", "max_iter", "damping_alpha"}
    # R2 ban: no argmax impersonation — source must not compute hard via argmax(prior).
    src = MODULE_PATH.read_text(encoding="utf-8")
    seg = src[src.index("def run_g_layer"):src.index("def run_l1_stage")]
    assert "np.argmax(prior" not in seg
    assert "history_decode" in seg or "decode_row_layered_fftqspa" in seg


def test_d6_10b_cold_start_semantics_belief_warm_is_init_only():
    # R4: each stage is a strict cold start; belief_warm is log-belief init only,
    # never message carry; production helpers always pass None.
    n = 4
    prior = mod.prior_logp_from_P(np.full((n, 32), 1.0 / 32.0))
    h_mat = np.eye(n, n, dtype=np.uint8)
    target = np.zeros(n, dtype=np.uint8)
    cold = mod.run_g_layer(prior, target, h_mat, max_iter=5)
    assert cold["cold_start"] is True
    warm_init = np.log(np.full((n, 32), 1.0 / 32.0))
    warmed = mod.run_g_layer(prior, target, h_mat, max_iter=5, belief_warm=warm_init)
    assert warmed["cold_start"] is False
    # Same uniform init must agree with cold on this trivial case; warm is not carry.
    assert np.array_equal(np.asarray(warmed["x_hat"]), np.asarray(cold["x_hat"]))
    with pytest.raises(ValueError):
        mod.run_g_layer(prior, target, h_mat, max_iter=5, belief_warm=np.zeros((n, 31)))
    l1_src = MODULE_PATH.read_text(encoding="utf-8")
    assert "belief_warm=None" in l1_src
    assert "message carry" in l1_src or "never message carry" in l1_src


def test_d6_10c_true_kernel_reuse_import_and_tiny_answer():
    # R2/D8: thin adapter calls the frozen history kernel (import probe + tiny answer).
    dec = mod.history_decoder_fn()
    assert dec.__name__ == "decode_row_layered_fftqspa"
    assert dec.__module__.endswith("v35_algorithm_development")
    field = mod.get_gf32_field()
    h = np.eye(2, 2, dtype=np.uint8)
    # Codeword x=[0,0] gives syndrome [0,0]; strong prior on truth converges at 0.
    prior_p = np.full((2, 32), 1e-6)
    prior_p[:, 0] = 1.0
    prior_p /= prior_p.sum(axis=1, keepdims=True)
    syn = mod.gf32_syndrome(h, np.zeros(2, dtype=np.uint8), field)
    assert syn.tolist() == [0, 0]
    res = mod.history_decode(h, prior_p, syn, max_iter=90, field=field)
    assert int(res.iterations) == 0
    assert bool(res.syndrome_ok) is True
    assert np.array_equal(np.asarray(res.x_hat).reshape(-1), np.zeros(2, dtype=np.uint8))
    # q@P recombination is exact V54 reuse.
    assert hasattr(mod._load_v54(), "get_l1_app_prior_l2")
    assert hasattr(mod._load_v54(), "get_l1_prior_p_u1_given_b")


def test_d6_11_syndrome_direction_matches_oracle():
    # Arm A binary oracle stays binary-only; G layers SHALL use GF32 history syndrome.
    h_mat = np.array([[1, 1, 0, 0], [0, 1, 1, 0]], dtype=np.uint8)
    x = np.array([1, 0, 1, 1], dtype=np.uint8)
    got = mod.binary_syndrome(h_mat, x)
    expected = ((h_mat.astype(np.int64) @ x.astype(np.int64)) & 1).astype(np.uint8)
    assert np.array_equal(got, expected)
    assert got.tolist() == [1, 1]
    # GF32 direction matches the history oracle (never binary-called-GF32).
    field = mod.get_gf32_field()
    hg = np.array([[1, 2, 0, 3], [4, 0, 5, 6]], dtype=np.uint8)
    xg = np.array([1, 2, 3, 4], dtype=np.uint8)
    assert np.array_equal(
        np.asarray(mod.gf32_syndrome(hg, xg, field)),
        np.asarray(mod._load_v35().syndrome_of_gf32(hg, xg, field)),
    )


def test_d6_12_violation_weight_matches_hand_count():
    h_mat = np.array([[1, 1, 0, 0], [0, 1, 1, 0], [1, 0, 1, 1]], dtype=np.uint8)
    hard = np.array([1, 0, 1, 1], dtype=np.uint8)
    target = np.array([0, 1, 0], dtype=np.uint8)
    for r in (0, 1, 2, 3):
        got = mod.prefix_violation(h_mat, hard, target, r)
        if r == 0:
            assert got == 0
        else:
            obs = ((h_mat[:r].astype(np.int64) @ hard.astype(np.int64)) & 1).astype(np.uint8)
            hand = int(np.count_nonzero((obs ^ target[:r]) & 1))
            assert got == hand
    assert mod.prefix_violation(h_mat, hard, target, 2) == 1
    # GF32 prefix helper uses the history syndrome with GF32 equality.
    field = mod.get_gf32_field()
    hg = np.array([[1, 2, 0, 0], [0, 3, 4, 0], [5, 0, 6, 7]], dtype=np.uint8)
    xg = np.array([1, 2, 3, 4], dtype=np.uint8)
    tg = mod.gf32_syndrome(hg, xg, field)
    assert mod.gf32_prefix_violation(hg, xg, tg, 3, field) == 0
    assert mod.gf32_prefix_violation(hg, xg, tg, 0, field) == 0


def test_d6_12b_l2_chain_short_circuit_follows_v54_order():
    # R5: L1 always feeds L2 (no L1 gate); L2 base-ok skips joint/total;
    # joint-ok skips total; each stage cold (belief_warm=None).
    n = 4
    logp = mod.prior_logp_from_P(np.full((n, 32), 1.0 / 32.0))
    h4 = np.eye(n, n, dtype=np.uint8)
    calls: list[str] = []

    def _counting(name: str, ok: bool):
        def _fn(h, prior_p, target):
            calls.append(name)
            nn = np.asarray(prior_p).shape[0]
            return {
                "x_hat": np.zeros(nn, dtype=np.uint8),
                "iterations_used": 1,
                "syndrome_ok": ok,
                "runtime_s": 0.001,
                "stop": "fake",
                "final_beliefs": np.log(np.maximum(prior_p, 1e-15)),
            }
        return _fn

    # Base-ok short-circuits joint and total (single underlying call each stage
    # would need distinct fns; here chain uses one decode_fn so emulate via ok=True).
    chain_ok = mod.run_l2_incremental_chain(
        h4, h4, h4, np.full((n, 32), 1.0 / 32.0),
        np.zeros(n, dtype=np.uint8), np.zeros(n, dtype=np.uint8), np.zeros(n, dtype=np.uint8),
        decode_fn=_counting("base", True),
    )
    assert chain_ok["skipped"] == {"joint": True, "total": True}
    assert chain_ok["stages"]["joint"] is None and chain_ok["stages"]["total"] is None
    # All production stages are cold (no belief carry).
    src = MODULE_PATH.read_text(encoding="utf-8")
    assert src.count("belief_warm=None") >= 4


def test_d6_13_v64_tag_helper_readonly_no_leak():
    x1 = np.array([1, 2, 3, 4], dtype=np.uint8)
    x2 = np.array([5, 6, 7, 8], dtype=np.uint8)
    t1 = mod.tag_probe_readonly(x1, x2)
    t2 = mod.tag_probe_readonly(x1, x2)
    assert t1 == t2
    assert isinstance(t1, str) and len(t1) == 16
    t3 = mod.tag_probe_readonly(x2, x1)
    assert t3 != t1
    assert mod.TAG_BITS == 0
    assert mod.TAG_OK == "NOT_APPLICABLE"
    assert mod.LEAK_BASE == 1064 and mod.LEAK_S1 == 1104 and mod.LEAK_S2 == 1144
    # Canonical L2-only rows via leak_for_base (184/192/200 -> 1064/1104/1144).
    assert mod.leak_for_base(184) == 1064
    assert mod.leak_for_base(192) == 1104
    assert mod.leak_for_base(200) == 1144
    # m_total alias already includes H1 (200/208/216 -> 1064/1104/1144); do
    # not pass L2-only rows here.
    assert mod.leak_for_m(200) == 1064
    assert mod.leak_for_m(208) == 1104
    assert mod.leak_for_m(216) == 1144
    assert mod.leak_for_source_v54("1M") == (1064, 1104, 1144)


def test_d6_14_candidate_vs_bob_direct_comparison():
    bob = np.array([0, 0, 0, 0], dtype=np.uint8)
    c1 = np.array([0, 1, 0, 1], dtype=np.uint8)
    c2 = np.array([1, 0, 1, 0], dtype=np.uint8)
    assert mod.direct_flips(c1, bob) == 2
    assert mod.direct_flips(c2, bob) == 2
    assert not np.array_equal(c1, c2)
    assert mod.direct_flips(c1, c1) == 0
    sym_bob = np.array([3, 7, 3, 7], dtype=np.int64)
    sym_c = np.array([3, 7, 4, 7], dtype=np.int64)
    assert mod.direct_flips(sym_c, sym_bob) == 1


def test_d6_15_four_file_schema_fake_runner_tmp_only(tmp_path):
    arm_g = {
        "status": "LADDER_EXHAUSTED",
        "rows": 200,
        "iters": 12,
        "syndrome_satisfied": False,
        "bit_flips": 41,
        "symbol_flips": 9,
    }
    out = tmp_path / "contrast_fake"
    written = mod.write_contrast_outputs(out, arm_g)
    assert {p.name for p in written.iterdir()} == {
        "manifest.json",
        "results.json",
        "table.csv",
        "report.md",
    }
    manifest = json.loads((written / "manifest.json").read_text(encoding="utf-8"))
    results = json.loads((written / "results.json").read_text(encoding="utf-8"))
    assert manifest["cycle"] == "V72P2D3-GF32"
    assert manifest["tag_bits"] == 0
    assert manifest["history_kernel"] == "V35-decode_row_layered_fftqspa-via-V54-chain"
    assert results["arms"]["G"]["rows"] == 200
    payload = (written / "results.json").read_text(encoding="utf-8")
    for forbidden in ("prior_logp", "check_to_variable", "syndrome_bytes", "alice_bits"):
        assert forbidden not in payload
    prod = (
        ROOT.parent
        / "comparison_bench"
        / "outputs_comparison"
        / "v72p2d3_gf32_contrast_20260904"
    )
    assert not str(written.resolve()).startswith(str(prod.resolve()))
    with pytest.raises(ValueError):
        mod.write_contrast_outputs(prod, arm_g)


def test_t0_import_has_no_real_side_effects():
    assert mod.Q == 1024 and mod.N == 1024
    assert mod.M_BASE == 184 and mod.M_TOTAL == 200
    assert mod.MAX_ITER == 90 and mod.DAMPING_ALPHA == 1.0
    assert mod.SESSION_ID == "20260123_1M_600k_0dB"
    assert tuple(mod.VAL_FRAMES) == (1726, 1727, 1728, 1729)
    assert (mod.CAL_START, mod.CAL_END) == (702, 1725)
    rec = mod.a_baseline_record()
    assert rec["mother"] == [9036, 10240] and rec["nnz"] == 49620
    assert rec["attempted"] is False
    src = MODULE_PATH.read_text(encoding="utf-8")
    assert "read_parquet" not in src
    assert "v72p2d3_gf32_contrast_20260904" in src
    # Frozen history reference is allowed; stub/mock/simplified decoder is banned.
    assert "decode_row_layered_fftqspa" in src
    assert "v35_algorithm_development" in src
    assert "v54_two_stage_incremental_l2_rescue" in src
    for banned in ("stub", "mock", "simplified_decoder", "fixed_hard"):
        assert banned not in src.lower()
    # No argmax impersonation in the production stage path.
    seg = src[src.index("def run_g_layer"):src.index("def run_l1_stage")]
    assert "np.argmax(prior" not in seg
    rsrc = RUNNER_PATH.read_text(encoding="utf-8")
    assert "mock" not in rsrc.lower()
    assert "stub" not in rsrc.lower()
    assert "read_parquet" not in rsrc


def test_d7_full_dual_layer_budget_and_runner_guards(tmp_path):
    import shutil
    import time

    try:
        import psutil

        have_psutil = True
    except ImportError:
        have_psutil = False
    rng = np.random.default_rng(20260902)
    bob_cal = rng.integers(0, 8, size=300, dtype=np.int64)
    high_cal = rng.integers(0, 4, size=300, dtype=np.int64)
    low_cal = rng.integers(0, 4, size=300, dtype=np.int64)
    t0 = time.monotonic()
    p1 = mod.build_stage1_P(bob_cal, high_cal, 1.0, n_b_states=8, q_sub=4)
    p2 = mod.build_stage2_P(high_cal, bob_cal, low_cal, 1.0, n_b_states=8, q_sub=4)
    n = 8
    prior = mod.prior_logp_from_P(np.full((n, 32), 1.0 / 32.0))
    h_mat = np.eye(n, n, dtype=np.uint8)
    r1 = mod.run_g_layer(prior, np.zeros(n, dtype=np.uint8), h_mat, max_iter=10)
    r2 = mod.run_g_layer(prior, np.zeros(n, dtype=np.uint8), h_mat, max_iter=10)
    wall = time.monotonic() - t0
    assert wall <= 300.0
    if have_psutil:
        import os

        rss = psutil.Process(os.getpid()).memory_info().rss
        assert rss < 2 * 1024**3
    assert r1["finite"] and r2["finite"]
    out = Path(runner.WORKSPACE_ROOT) / ("v72p2d3_test_" + tmp_path.name)
    if out.exists():
        shutil.rmtree(out)
    try:
        report = runner.run_synthetic_contrast(out_dir=out, seed=20260902)
        assert report["status"] == "PASS"
        assert report["real_executed"] is False
        assert {p.name for p in out.iterdir()} == {
            "manifest.json",
            "results.json",
            "table.csv",
            "report.md",
        }
    finally:
        if out.exists():
            shutil.rmtree(out)
    with pytest.raises(ValueError):
        runner.run_synthetic_contrast(out_dir=out / "again", seed=1)
    with pytest.raises(ValueError):
        runner._resolve_workspace_dir(
            ROOT.parent / "comparison_bench" / "outputs_comparison" / "x"
        )
    assert runner.main(["--phase", "real"]) == 2
    assert runner.main(["--phase", "real", "--execute-real"]) == 2


# ---- Fake-E2E real-entry chain (workspace only; no parquet, no true decoder,
# no production root). Each fake exercises the frozen production order with
# max90/damping1.0/cold, CAL702..1725, VAL1726..1729, A read-only, tag 0.

def _fake_e2e_registry():
    return {
        "sessions": [
            {
                "session_id": "20260123_1M_600k_0dB",
                "source_label": "1M",
                "stage2_CAL_frame_ids": list(range(702, 1726)),
                "stage2_VAL_frame_ids": list(range(1726, 1762)),
            }
        ]
    }


def _fake_e2e_frames():
    rng = np.random.default_rng(20260902)
    frames = {}
    for fid in (702, 703, 704, 705, 1726, 1727, 1728, 1729):
        frames[fid] = {
            "alice_symbols": rng.integers(0, 1024, size=256),
            "bob_symbols": rng.integers(0, 1024, size=256),
        }
    return frames


def _fake_e2e_matrices():
    rng = np.random.default_rng(20260903)

    def _sparse(rows):
        h = np.zeros((rows, 1024), dtype=np.uint8)
        for r in range(rows):
            cols = rng.choice(1024, size=8, replace=False)
            h[r, cols] = rng.integers(1, 32, size=8).astype(np.uint8)
        return h

    h_total = _sparse(200)
    return {
        "h1": _sparse(16),
        "h_base": h_total[:184].copy(),
        "h_joint": h_total[:192].copy(),
        "h_total": h_total,
    }


def _fake_e2e_decode_fn(h_mat, prior_p, target):
    # Explicit test-only fake (argmax readout, history syndrome oracle for the
    # observed value only); production passes decode_fn=None (true kernel).
    pp = np.asarray(prior_p, dtype=np.float64)
    x_hat = np.argmax(pp, axis=1).astype(np.uint8)
    obs = np.asarray(mod.gf32_syndrome(np.asarray(h_mat, dtype=np.uint8), x_hat))
    return {
        "x_hat": x_hat,
        "iterations_used": 1,
        "syndrome_ok": bool(np.array_equal(obs, np.asarray(target, dtype=np.uint8) & 31)),
        "runtime_s": 0.001,
        "stop": "fake-e2e",
        "final_beliefs": np.log(np.maximum(pp, 1e-15)),
    }


def _fake_e2e_preflight():
    return {"status": "PASS", "cycle": "V72P2D3-GF32", "synthetic_only": True}


def test_fake_e2e_real_chain_workspace_20_checks():
    import shutil

    out = Path(runner.WORKSPACE_ROOT) / "v72p2d3_real_e2e_fake"
    if out.exists():
        shutil.rmtree(out)
    prod = (
        ROOT.parent
        / "comparison_bench"
        / "outputs_comparison"
        / "v72p2d3_gf32_contrast_20260904"
    )
    prod_existed = prod.exists()
    try:
        report = runner.run_real_orchestration(
            out_dir=out,
            registry=_fake_e2e_registry(),
            frames=_fake_e2e_frames(),
            matrices=_fake_e2e_matrices(),
            preflight=_fake_e2e_preflight(),
            authorized=True,
            decode_fn=_fake_e2e_decode_fn,
        )
        assert report["gate"] == "PASS"  # c01 authorization/preflight/output gate
        assert report["block_ids"] == [1726, 1727, 1728, 1729]  # c02 single VAL block
        assert report["arm_a_attempted"] is False  # c03 A read-only, never rerun
        assert report["branch"] in mod.REAL_BRANCHES  # c04 four-branch discriminant
        assert report["tag_bits"] == 0 and report["tag_ok"] == "NOT_APPLICABLE"  # c05 no tag
        assert report["leak_bits"] in (1064, 1104, 1144)  # c06 frozen leak triple
        assert report["prep_wall_s"] <= 300.0 and report["g_wall_s"] <= 300.0  # c07 prep/G budget
        assert report["inv_wall_s"] <= 600.0  # c08 invocation budget
        assert report["peak_rss_bytes"] is None or report["peak_rss_bytes"] < 2 * 1024**3  # c09 RSS budget
        assert {p.name for p in out.iterdir()} == {"manifest.json", "results.json", "table.csv", "report.md"}  # c10 four files
        assert out.resolve() != prod.resolve() and prod.resolve() not in out.resolve().parents  # c11 outside formal root
        manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["cycle"] == "V72P2D3-GF32" and manifest["tag_bits"] == 0  # c12 manifest schema
        assert manifest["history_kernel"] == "V35-decode_row_layered_fftqspa-via-V54-chain"  # c13 kernel binding
        results = json.loads((out / "results.json").read_text(encoding="utf-8"))
        assert results["arms"]["A"]["attempted"] is False  # c14 A reuse in artifact
        assert results["arms"]["G"]["branch"] == report["branch"]  # c15 G branch persisted
        assert mod.MAX_ITER == 90 and mod.DAMPING_ALPHA == 1.0  # c16 frozen decoder caps
        assert tuple(mod.REAL_CAL_IDS) == tuple(range(702, 1726))  # c17 frozen CAL domain
        assert report["fake_decoder"] is True  # c18 true decoder never ran
        assert report["n_cal_symbols"] == 4 * 256  # c19 CAL-only fit, no VAL backfill
        assert prod.exists() == prod_existed  # c20 formal root untouched
    finally:
        if out.exists():
            shutil.rmtree(out)


def test_real_chain_guards_and_bans(tmp_path):
    frames = _fake_e2e_frames()
    matrices = _fake_e2e_matrices()
    good_preflight = _fake_e2e_preflight()
    with pytest.raises(PermissionError):
        mod.require_real_gate(execute_real=False, authorized=True, preflight=good_preflight, out_dir=tmp_path / "a")
    with pytest.raises(PermissionError):
        mod.require_real_gate(execute_real=True, authorized=False, preflight=good_preflight, out_dir=tmp_path / "b")
    with pytest.raises(PermissionError):
        mod.require_real_gate(execute_real=True, authorized=True, preflight={"status": "FAIL"}, out_dir=tmp_path / "c")
    with pytest.raises(FileExistsError):
        mod.require_real_gate(execute_real=True, authorized=True, preflight=good_preflight, out_dir=tmp_path)
    prod = ROOT.parent / "comparison_bench" / "outputs_comparison" / "v72p2d3_gf32_contrast_20260904"
    with pytest.raises(ValueError):
        mod.require_real_gate(execute_real=True, authorized=True, preflight=good_preflight, out_dir=prod / "x")
    with pytest.raises(ValueError):
        mod.validate_registry({"sessions": []})
    bad_cal = _fake_e2e_registry()
    bad_cal["sessions"][0]["stage2_CAL_frame_ids"] = list(range(700, 1724))
    with pytest.raises(ValueError):
        mod.validate_registry(bad_cal)
    bad_val = _fake_e2e_registry()
    bad_val["sessions"][0]["stage2_VAL_frame_ids"] = list(range(1800, 1836))
    with pytest.raises(ValueError):
        mod.validate_registry(bad_val)
    with pytest.raises(ValueError):
        mod.assemble_block_frames(mod.validate_frame_bundle(frames, [1726, 1727, 1728, 1729]), [1726, 1727, 1728, 1730])
    broken = dict(matrices)
    broken["h_joint"] = (np.asarray(matrices["h_joint"]) ^ np.uint8(1))
    with pytest.raises(ValueError):
        mod.validate_nested_matrices(broken["h1"], broken["h_base"], broken["h_joint"], broken["h_total"])
    with pytest.raises(PermissionError):
        runner.run_real_orchestration(out_dir=tmp_path / "nofakes", registry=None, frames=None, matrices=None)
    assert runner.main(["--phase", "real"]) == 2
    assert runner.main(["--phase", "real", "--execute-real"]) == 2
    assert runner.PREP_LIMIT_S == mod.PREP_LIMIT_S == 300.0
    assert runner.G_LIMIT_S == mod.G_LIMIT_S == 300.0
    assert runner.INV_LIMIT_S == mod.INV_LIMIT_S == 600.0
    assert runner.RSS_LIMIT_BYTES == mod.RSS_LIMIT_BYTES == 2 * 1024**3
    src = MODULE_PATH.read_text(encoding="utf-8")
    assert "read_parquet" not in src
    assert src.count("compute_tag_64") == 2  # readonly probe only, no tag generation
    assert "mock" not in src.lower() and "stub" not in src.lower()
    rsrc = RUNNER_PATH.read_text(encoding="utf-8")
    assert "read_parquet" not in rsrc and "import pandas" not in rsrc
    assert "mock" not in rsrc.lower() and "stub" not in rsrc.lower()


# ---- R6 true-decode (production v35 decode_row_layered_fftqspa, decode_fn=None) ----
# Synthetic tiny only; no parquet, no production root. Each case uses the true
# iterative kernel via run_g_layer/history_decode with cold start.

def _r6_field():
    return mod.get_gf32_field()


def _r6_correctable_2x4():
    # Tree H 2x4 degrees (2,3); one strong wrong prior at pos0, rest correct.
    field = _r6_field()
    h = np.array([[1, 1, 0, 0], [0, 1, 1, 1]], dtype=np.uint8)
    x_true = np.array([5, 7, 3, 9], dtype=np.uint8)
    syn = np.asarray(mod.gf32_syndrome(h, x_true, field), dtype=np.uint8)
    prior = np.full((4, 32), 0.01)
    for i, v in enumerate(x_true.tolist()):
        prior[i, int(v)] += 1.0
    prior[0, :] = 0.01
    prior[0, 0] = 2.0
    prior /= prior.sum(axis=1, keepdims=True)
    return field, h, x_true, syn, prior


def _r6_tree_2x3():
    # Tiny tree 2x3 degrees (2,2), columns (1,2,1): acyclic, BP exact.
    field = _r6_field()
    h = np.array([[1, 2, 0], [0, 3, 4]], dtype=np.uint8)
    x_true = np.array([5, 7, 3], dtype=np.uint8)
    syn = np.asarray(mod.gf32_syndrome(h, x_true, field), dtype=np.uint8)
    prior = np.full((3, 32), 0.01)
    for i, v in enumerate(x_true.tolist()):
        prior[i, int(v)] += 1.0
    prior[0, :] = 0.01
    prior[0, 0] = 2.0
    prior /= prior.sum(axis=1, keepdims=True)
    return field, h, x_true, syn, prior


def _r6_changed_wrong_probe1():
    # Probe1 overwrite style: moved but wrong, syndrome unsatisfied.
    field = _r6_field()
    h = np.array([[1, 1, 1, 0], [0, 1, 2, 1]], dtype=np.uint8)
    x_true = np.array([5, 7, 3, 9], dtype=np.uint8)
    syn = np.asarray(mod.gf32_syndrome(h, x_true, field), dtype=np.uint8)
    prior = np.full((4, 32), 0.001)
    for i, v in enumerate(x_true.tolist()):
        prior[i, int(v)] = 0.9
    prior[0, :] = 1e-6
    prior[0, 0] = 1.0
    prior /= prior.sum(axis=1, keepdims=True)
    return field, h, x_true, syn, prior


def test_r6_01_tiny_tree_matches_exhaustive():
    field, h, x_true, syn, prior = _r6_tree_2x3()
    logp = np.log(np.maximum(prior, 1e-15))
    out = mod.run_g_layer(logp, syn, h, max_iter=20, field=field)
    assert bool(out["syndrome_ok"]) is True
    # Exhaustive MAP over 32^3=32768 subject to syndrome, production logp.
    best_ll, best_x = -1e99, None
    for a in range(32):
        for b in range(32):
            for c in range(32):
                x = np.array([a, b, c], dtype=np.uint8)
                if not np.array_equal(np.asarray(mod.gf32_syndrome(h, x, field)), syn):
                    continue
                ll = float(logp[0, a] + logp[1, b] + logp[2, c])
                if ll > best_ll:
                    best_ll, best_x = ll, (a, b, c)
    assert best_x is not None
    assert out["x_hat"].tolist() == list(best_x)


def test_r6_02_nonuniform_prior_nonzero_syndrome():
    _, h, x_true, syn, prior = _r6_correctable_2x4()
    assert syn.tolist() != [0] * len(syn.tolist())
    assert np.all(np.isfinite(prior)) and np.all(prior > 0)
    assert np.allclose(prior.sum(axis=1), 1.0)
    assert not np.allclose(prior, 1.0 / 32.0)


def test_r6_03_prior_argmax_violates_syndrome():
    field, h, _, syn, prior = _r6_correctable_2x4()
    argmax = np.argmax(prior, axis=1).astype(np.uint8)
    assert not np.array_equal(np.asarray(mod.gf32_syndrome(h, argmax, field)), syn)


def test_r6_04_candidate_changes_after_true_decode():
    field, h, _, syn, prior = _r6_correctable_2x4()
    logp = np.log(np.maximum(prior, 1e-15))
    out = mod.run_g_layer(logp, syn, h, max_iter=20, field=field)
    argmax = np.argmax(prior, axis=1)
    assert bool((np.asarray(out["x_hat"]) != argmax).any()) is True


def test_r6_05_correctable_final_syndrome_satisfied():
    field, h, x_true, syn, prior = _r6_correctable_2x4()
    logp = np.log(np.maximum(prior, 1e-15))
    out = mod.run_g_layer(logp, syn, h, max_iter=20, field=field)
    assert bool(out["syndrome_ok"]) is True
    assert np.array_equal(np.asarray(out["syndrome_observed"]), syn)
    assert np.array_equal(np.asarray(out["x_hat"]), x_true)
    assert 1 <= int(out["iterations_used"]) <= 90


def test_r6_06_uncorrectable_or_budget_short_fails():
    field, h, x_true, syn, _ = _r6_correctable_2x4()
    uni = np.full((4, 32), 1.0 / 32.0)
    out = mod.run_g_layer(np.log(uni), syn, h, max_iter=20, field=field)
    assert bool(out["syndrome_ok"]) is False
    # Same correctable prior with budget 1 is insufficient, with 20 succeeds.
    _, _, _, syn2, prior2 = _r6_correctable_2x4()
    logp2 = np.log(np.maximum(prior2, 1e-15))
    short = mod.run_g_layer(logp2, syn2, h, max_iter=1, field=field)
    full = mod.run_g_layer(logp2, syn2, h, max_iter=20, field=field)
    assert bool(short["syndrome_ok"]) is False
    assert bool(full["syndrome_ok"]) is True


def test_r6_07_iterations_in_1_to_90_and_real():
    field, h, _, syn, prior = _r6_correctable_2x4()
    logp = np.log(np.maximum(prior, 1e-15))
    out = mod.run_g_layer(logp, syn, h, max_iter=20, field=field)
    assert 1 <= int(out["iterations_used"]) <= 90
    assert int(out["iterations_used"]) <= 20
    # Trivial argmax-satisfied case is exactly 0 (no update).
    h0 = np.eye(2, 2, dtype=np.uint8)
    p0 = np.full((2, 32), 1e-6)
    p0[:, 0] = 1.0
    p0 /= p0.sum(axis=1, keepdims=True)
    s0 = mod.gf32_syndrome(h0, np.zeros(2, dtype=np.uint8), field)
    r0 = mod.history_decode(h0, p0, s0, max_iter=90, field=field)
    assert int(r0.iterations) == 0


def test_r6_08_max1_vs_max5_different_trajectory():
    field, h, _, syn, prior = _r6_correctable_2x4()
    logp = np.log(np.maximum(prior, 1e-15))
    r1 = mod.run_g_layer(logp, syn, h, max_iter=1, field=field)
    r5 = mod.run_g_layer(logp, syn, h, max_iter=5, field=field)
    assert int(r1["iterations_used"]) == 1
    assert int(r5["iterations_used"]) == 2
    assert r1["x_hat"].tolist() != r5["x_hat"].tolist()
    assert bool(r1["syndrome_ok"]) is False
    assert bool(r5["syndrome_ok"]) is True


def test_r6_09_row_permuted_layered_consistent():
    field, h, _, syn, prior = _r6_correctable_2x4()
    logp = np.log(np.maximum(prior, 1e-15))
    h_perm, syn_perm = h[::-1].copy(), syn[::-1].copy()
    r1 = mod.run_g_layer(logp, syn, h, max_iter=20, field=field)
    r2 = mod.run_g_layer(logp, syn_perm, h_perm, max_iter=20, field=field)
    assert bool(r1["syndrome_ok"]) and bool(r2["syndrome_ok"])
    assert r1["x_hat"].tolist() == r2["x_hat"].tolist()


def test_r6_10_check_degrees_2_3_ok_degree1_rejected():
    field, h, x_true, syn, prior = _r6_correctable_2x4()
    assert sorted(int((h[r] > 0).sum()) for r in range(h.shape[0])) == [2, 3]
    logp = np.log(np.maximum(prior, 1e-15))
    out = mod.run_g_layer(logp, syn, h, max_iter=20, field=field)
    assert bool(out["syndrome_ok"]) is True
    h1 = np.array([[1, 0, 0, 0], [0, 1, 1, 1]], dtype=np.uint8)
    s1 = mod.gf32_syndrome(h1, x_true, field)
    with pytest.raises(ValueError):
        mod.run_g_layer(logp, s1, h1, max_iter=5, field=field)


def test_r6_11_l1_ok_l2_fail_layer_independent():
    field, ht, xt, st, pt = _r6_tree_2x3()
    l1 = mod.run_g_layer(np.log(np.maximum(pt, 1e-15)), st, ht, max_iter=20, field=field)
    assert bool(l1["syndrome_ok"]) is True
    _, h2, x2, s2, _ = _r6_correctable_2x4()
    uni = np.full((4, 32), 1.0 / 32.0)
    l2 = mod.run_g_layer(np.log(uni), s2, h2, max_iter=20, field=field)
    assert bool(l2["syndrome_ok"]) is False


def test_r6_12_l1_fail_still_runs_l2_no_gate():
    field, ht, _, st, _ = _r6_tree_2x3()
    uni3 = np.full((3, 32), 1.0 / 32.0)
    l1 = mod.run_g_layer(np.log(uni3), st, ht, max_iter=5, field=field)
    assert bool(l1["syndrome_ok"]) is False
    # Production always runs L2 after L1 (no L1 gate); true-kernel L2 chain runs.
    hb = np.array([[1, 1, 0, 0], [0, 1, 1, 0]], dtype=np.uint8)
    hj = np.array([[1, 1, 0, 0], [0, 1, 1, 0], [0, 0, 1, 1]], dtype=np.uint8)
    htot = np.array([[1, 1, 0, 0], [0, 1, 1, 0], [0, 0, 1, 1], [1, 0, 0, 1]], dtype=np.uint8)
    xt = np.array([5, 7, 3, 9], dtype=np.uint8)
    sb = mod.gf32_syndrome(hb, xt, field)
    sj = mod.gf32_syndrome(hj, xt, field)
    stot = mod.gf32_syndrome(htot, xt, field)
    uni4 = np.full((4, 32), 1.0 / 32.0)
    chain = mod.run_l2_incremental_chain(hb, hj, htot, uni4, sb, sj, stot, field=field)
    # Base failure does not short-circuit: joint and total both executed.
    assert chain["skipped"] == {"joint": False, "total": False}
    assert chain["stages"]["joint"] is not None and chain["stages"]["total"] is not None


def test_r6_13_nested_rows_strictly_increasing():
    geo = mod.nested_geometry()
    assert tuple(geo["nested"]) == (184, 192, 200)
    assert 184 < 192 < 200
    hb = np.array([[1, 1, 0, 0], [0, 1, 1, 0]], dtype=np.uint8)
    hj = np.array([[1, 1, 0, 0], [0, 1, 1, 0], [0, 0, 1, 1]], dtype=np.uint8)
    htot = np.array([[1, 1, 0, 0], [0, 1, 1, 0], [0, 0, 1, 1], [1, 0, 0, 1]], dtype=np.uint8)
    assert hb.shape[0] < hj.shape[0] < htot.shape[0]
    assert np.array_equal(hj[:2], hb) and np.array_equal(htot[:3], hj)


def test_r6_14_changed_does_not_imply_oracle_correct():
    field, h, x_true, syn, prior = _r6_changed_wrong_probe1()
    logp = np.log(np.maximum(prior, 1e-15))
    out = mod.run_g_layer(logp, syn, h, max_iter=20, field=field)
    changed = bool((np.asarray(out["x_hat"]) != np.argmax(prior, axis=1)).any())
    oracle = bool(np.array_equal(np.asarray(out["x_hat"]), x_true))
    assert changed is True
    assert oracle is False
    assert bool(out["syndrome_ok"]) is False


def test_r6_15_oracle_uses_final_candidate_only():
    field = _r6_field()
    hb = np.array([[1, 1, 0, 0], [0, 1, 1, 0]], dtype=np.uint8)
    hj = np.array([[1, 1, 0, 0], [0, 1, 1, 0], [0, 0, 1, 1]], dtype=np.uint8)
    htot = np.array([[1, 1, 0, 0], [0, 1, 1, 0], [0, 0, 1, 1], [1, 0, 0, 1]], dtype=np.uint8)
    xt = np.array([5, 7, 3, 9], dtype=np.uint8)
    sb = mod.gf32_syndrome(hb, xt, field)
    sj = mod.gf32_syndrome(hj, xt, field)
    stot = mod.gf32_syndrome(htot, xt, field)
    _, _, _, _, prior_ok = _r6_correctable_2x4()
    chain_ok = mod.run_l2_incremental_chain(hb, hj, htot, prior_ok, sb, sj, stot, field=field)
    assert chain_ok["skipped"] == {"joint": True, "total": True}
    assert chain_ok["final"] is chain_ok["stages"]["base"]
    assert bool(np.array_equal(np.asarray(chain_ok["final"]["x_hat"]), xt)) is True
    uni = np.full((4, 32), 1.0 / 32.0)
    chain_fail = mod.run_l2_incremental_chain(hb, hj, htot, uni, sb, sj, stot, field=field)
    assert chain_fail["final"] is chain_fail["stages"]["total"]
    assert bool(np.array_equal(np.asarray(chain_fail["final"]["x_hat"]), xt)) is False


def test_r6_16_roundtrip_1024_lsb_direction():
    for s in range(1024):
        assert mod.combine_symbol(*mod.split_symbol(s)) == s
    syms = np.arange(1024, dtype=np.int64)
    assert np.array_equal(mod.layers_to_symbols(*mod.symbols_to_layers(syms)), syms)


def test_r6_17_no_tag_hash_in_production_path():
    field, h, _, syn, prior = _r6_correctable_2x4()
    out = mod.run_g_layer(np.log(np.maximum(prior, 1e-15)), syn, h, max_iter=5, field=field)
    assert mod.TAG_BITS == 0
    for banned in ("tag", "hash"):
        assert all(banned not in k.lower() for k in out)
    src = MODULE_PATH.read_text(encoding="utf-8")
    seg = src[src.index("def run_g_layer"):src.index("def run_l2_incremental_chain")]
    assert "hashlib" not in seg and "sha256" not in seg and "compute_tag" not in seg


def test_r6_18_arm_a_binary_decoder0_not_gf32():
    rec = mod.a_baseline_record()
    assert rec["attempted"] is False and rec["reuse"] is True
    h = np.array([[1, 1, 0, 0], [0, 1, 1, 0]], dtype=np.uint8)
    assert np.array_equal(mod.binary_syndrome(h, np.array([1, 0, 1, 1], dtype=np.uint8)), np.array([1, 1], dtype=np.uint8))
    field = _r6_field()
    assert int(field.q) == 32
    src = MODULE_PATH.read_text(encoding="utf-8")
    assert "decode_row_layered_fftqspa" in src


def test_r6_gate_candidate_changed_from_prior_argmax():
    # Key gate: at least one non-trivial synthetic has true motion, else IMPLEMENTATION_FAIL.
    found = []
    for maker in (_r6_correctable_2x4, _r6_tree_2x3, _r6_changed_wrong_probe1):
        field, h, _, syn, prior = maker()
        if np.allclose(prior, 1.0 / 32.0):
            continue
        argmax = np.argmax(prior, axis=1).astype(np.uint8)
        if np.array_equal(np.asarray(mod.gf32_syndrome(h, argmax, field)), syn):
            continue
        if any(int((h[r] > 0).sum()) < 2 for r in range(h.shape[0])):
            continue
        out = mod.run_g_layer(np.log(np.maximum(prior, 1e-15)), syn, h, max_iter=20, field=field)
        changed = bool((np.asarray(out["x_hat"]) != np.argmax(prior, axis=1)).any())
        found.append(changed)
    assert any(found), "IMPLEMENTATION_FAIL: candidate_changed_from_prior_argmax never true on non-trivial synthetics"


def test_r6_19_n1024_frozen_nested_cold_true_kernel():
    # n=1024 synthetic true-kernel via frozen generators; no parquet, no prod root.
    # Matrices reuse frozen V38 Lane C + V54 Δ8+8 increments (deterministic seeds);
    # decode via production path decode_fn=None cold (belief_warm=None default).
    from comparison_bench.formal_ir.v38_architecture_triage import (
        construct_lane_c_prototype,
    )

    v54 = mod._load_v54()
    field = mod.get_gf32_field()
    h_base, _ = construct_lane_c_prototype(source="1M", seed=383102, field=field)
    h_inc1, hs1, _, rd1 = v54.construct_h_inc("1M", 600001)
    h_inc2, hs2, _, rd2 = v54.construct_h_inc("1M", 600004)
    h_base = np.asarray(h_base, dtype=np.uint8)
    h_inc1 = np.asarray(h_inc1, dtype=np.uint8)
    h_inc2 = np.asarray(h_inc2, dtype=np.uint8)
    h_joint = np.vstack([h_base, h_inc1]).astype(np.uint8)
    h_total = np.vstack([h_base, h_inc1, h_inc2]).astype(np.uint8)
    assert h_base.shape == (184, 1024)
    assert h_joint.shape == (192, 1024)
    assert h_total.shape == (200, 1024)
    assert np.array_equal(h_joint[:184], h_base)
    assert np.array_equal(h_total[:184], h_base)
    assert np.array_equal(h_total[:192], h_joint)
    for h in (h_base, h_joint, h_total):
        assert int((h != 0).sum(axis=1).max()) <= 16
    assert int(np.asarray(rd1).max()) <= 16
    assert int(np.asarray(rd2).max()) <= 16
    assert int((np.asarray(hs1) != 0).sum(axis=0).max()) <= 1
    assert int((np.asarray(hs2) != 0).sum(axis=0).max()) <= 1
    # Synthetic truth/prior/syndrome (frozen seed, no CAL/VAL/parquet).
    rng = np.random.default_rng(20260902)
    n = 1024
    x_true = rng.integers(0, 32, size=n).astype(np.uint8)
    syn = np.asarray(mod.gf32_syndrome(h_base, x_true, field), dtype=np.uint8)
    prior = np.full((n, 32), 0.01)
    prior[np.arange(n), x_true.astype(int)] += 1.0
    prior[0, :] = 0.01
    prior[0, 0] = 2.0
    prior /= prior.sum(axis=1, keepdims=True)
    logp = np.log(np.maximum(prior, 1e-15))
    argmax = np.argmax(prior, axis=1).astype(np.uint8)
    assert not np.array_equal(np.asarray(mod.gf32_syndrome(h_base, argmax, field)), syn)
    # Production cold path: decode_fn=None (explicit), belief_warm=None default.
    r1 = mod.run_g_layer(logp, syn, h_base, max_iter=1, field=field, decode_fn=None)
    r5 = mod.run_g_layer(logp, syn, h_base, max_iter=5, field=field, decode_fn=None)
    assert r1["cold_start"] is True and r5["cold_start"] is True
    assert bool(r1["finite"]) and bool(r5["finite"])
    assert 0 <= int(r1["iterations_used"]) <= 1
    assert 0 <= int(r5["iterations_used"]) <= 5
    assert 1 <= int(r1["iterations_used"]) <= 90
    assert 1 <= int(r5["iterations_used"]) <= 90
    assert np.asarray(r1["x_hat"]).tolist() != np.asarray(r5["x_hat"]).tolist()
    assert bool((np.asarray(r5["x_hat"]) != argmax).any()) is True
    assert np.array_equal(
        np.asarray(mod.gf32_syndrome(h_base, np.asarray(r1["x_hat"]).astype(np.uint8), field)),
        np.asarray(r1["syndrome_observed"]),
    )
    assert np.array_equal(
        np.asarray(mod.gf32_syndrome(h_base, np.asarray(r5["x_hat"]).astype(np.uint8), field)),
        np.asarray(r5["syndrome_observed"]),
    )
    assert bool(r5["syndrome_ok"]) is True
    assert np.array_equal(np.asarray(r5["syndrome_observed"]), syn)
    # Lock strict production: no hashlib fallback, no mock in module.
    src = MODULE_PATH.read_text(encoding="utf-8")
    assert "hashlib" not in src
    assert "mock" not in src.lower()
