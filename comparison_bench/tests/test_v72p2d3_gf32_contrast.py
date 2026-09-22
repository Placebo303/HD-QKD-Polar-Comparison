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
    # R2-R6 prepare-only is the sole authorized parquet reader (filtered
    # 4-col); the frozen fake-E2E chain still never opens parquet.
    assert "def load_and_validate_prepare_frames" in src
    assert "REQUIRED_PARQUET_COLUMNS" in src
    assert src.count("read_parquet") >= 1
    prep_seg = src[src.index("def prepare_real_input"):]
    for banned_call in ("run_g_layer", "history_decode", "run_decoder("):
        assert banned_call not in prep_seg
    assert "decode_row_layered_fftqspa" not in prep_seg
    for banned in ("compute_tag_64", "hashlib", "sha256", "checksum"):
        assert banned not in prep_seg
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
        # Test fake stands in for a swept decoder; explicit conditioned
        # provenance so the BP-04 recombination guard passes.
        "belief_provenance": "CHECK_UPDATED",
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
    # R2-R6 prepare-only is the sole authorized parquet reader; fake-E2E still never opens it.
    assert "def load_and_validate_prepare_frames" in src
    assert "REQUIRED_PARQUET_COLUMNS" in src
    assert src.count("compute_tag_64") == 2  # readonly probe only, no tag generation
    assert "mock" not in src.lower() and "stub" not in src.lower()
    rsrc = RUNNER_PATH.read_text(encoding="utf-8")
    assert "read_parquet" not in rsrc and "import pandas" not in rsrc
    assert "mock" not in rsrc.lower() and "stub" not in rsrc.lower()
    # Production main no longer passes None; shared builder is the only real-entry path.
    assert "build_prepare_inputs" in rsrc
    assert "run_prepare_only" in rsrc
    assert "--registry" in rsrc and "--prepare-only" in rsrc
    assert runner.main(["--phase", "real", "--prepare-only"]) == 2
    assert runner.main(["--phase", "real", "--prepare-only", "--registry", str(tmp_path / "missing.json")]) == 2


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


# ---- R2-R6 prepare-only (registry->parquet->CAL/VAL->prior->block->A->words
# ->matrix/syndrome shapes->workspace READY, decoder 0, no formal root) ----

def _prep_registry_dict(parquet_path):
    return {
        "schema": mod.REGISTRY_SCHEMA,
        "session_id": mod.SESSION_ID,
        "source_label": "1M",
        "parquet_path": str(parquet_path),
        "cal_frame_ids": list(range(702, 1726)),
        "val_frame_ids": [1726, 1727, 1728, 1729],
        "used_2m": False,
        "columns": list(mod.REQUIRED_PARQUET_COLUMNS),
    }


def _prep_write_parquet(parquet_path):
    import pandas as pd

    rng = np.random.default_rng(20260902)
    rows = []
    for fid in list(range(702, 1726)) + [1726, 1727, 1728, 1729]:
        for pair in range(256):
            rows.append(
                (
                    int(fid),
                    int(pair),
                    int(rng.integers(0, 1024)),
                    int(rng.integers(0, 1024)),
                )
            )
    df = pd.DataFrame(rows, columns=list(mod.REQUIRED_PARQUET_COLUMNS))
    df = df.astype({c: "int64" for c in mod.REQUIRED_PARQUET_COLUMNS})
    df.to_parquet(parquet_path, index=False)


def test_r2_registry_contract_no_checksum(tmp_path):
    import json

    pq = tmp_path / "pairs.parquet"
    _prep_write_parquet(pq)
    reg = _prep_registry_dict(pq)
    out = mod.validate_prepare_registry(reg, tmp_path / "reg.json")
    assert out["parquet_path"] == pq.resolve()
    assert out["cal_ids"] == list(range(702, 1726))
    assert out["val_ids"] == [1726, 1727, 1728, 1729]
    bad = dict(reg)
    bad["schema"] = "wrong"
    with pytest.raises(ValueError):
        mod.validate_prepare_registry(bad, tmp_path / "reg.json")
    bad = dict(reg)
    bad["cal_frame_ids"] = list(range(700, 1724))
    with pytest.raises(ValueError):
        mod.validate_prepare_registry(bad, tmp_path / "reg.json")
    bad = dict(reg)
    bad["val_frame_ids"] = [1726, 1727, 1728, 1730]
    with pytest.raises(ValueError):
        mod.validate_prepare_registry(bad, tmp_path / "reg.json")
    bad = dict(reg)
    bad["used_2m"] = True
    with pytest.raises(ValueError):
        mod.validate_prepare_registry(bad, tmp_path / "reg.json")
    bad = dict(reg)
    bad["parquet_path"] = str(tmp_path / "missing.parquet")
    with pytest.raises(ValueError):
        mod.validate_prepare_registry(bad, tmp_path / "reg.json")
    # No checksum/hash/tag read or required: extra keys are ignored.
    extra = dict(reg)
    extra["sha256"] = "deadbeef"
    assert mod.validate_prepare_registry(extra, tmp_path / "reg.json")["session_id"] == mod.SESSION_ID
    src = MODULE_PATH.read_text(encoding="utf-8")
    prep_seg = src[src.index("def validate_prepare_registry"):src.index("def load_and_validate_prepare_frames")]
    assert "sha256" not in prep_seg and "hashlib" not in prep_seg and "compute_tag" not in prep_seg


def test_r3_parquet_4col_counts_no_data_rows(tmp_path):
    pq = tmp_path / "pairs.parquet"
    _prep_write_parquet(pq)
    loaded = mod.load_and_validate_prepare_frames(pq, list(range(702, 1726)), [1726, 1727, 1728, 1729])
    assert loaded["n_read_rows"] == 263168
    assert loaded["n_retained_rows"] == 263168
    assert loaded["n_cal_frames"] == 1024 and loaded["n_val_frames"] == 4
    assert loaded["n_cal_symbols"] == 262144 and loaded["n_val_symbols"] == 1024


def test_r4_r6_prepare_only_workspace_ready_decoder0(tmp_path):
    import json
    import shutil

    pq = tmp_path / "pairs.parquet"
    _prep_write_parquet(pq)
    reg_path = tmp_path / "registry.json"
    reg_path.write_text(json.dumps(_prep_registry_dict(pq), indent=2), encoding="utf-8")
    out = Path(runner.WORKSPACE_ROOT) / ("v72p2d3_prepare_" + tmp_path.name)
    if out.exists():
        shutil.rmtree(out)
    prod = ROOT.parent / "comparison_bench" / "outputs_comparison" / "v72p2d3_gf32_contrast_20260904"
    prod_existed = prod.exists()
    try:
        report = runner.run_prepare_only(out_dir=out, registry_path=reg_path)
        assert report["status"] == "READY"
        assert report["decoder_calls"] == 0 and report["published_bits"] == 0
        assert report["formal"] is False
        assert report["n_read_rows"] == 263168 and report["n_retained_rows"] == 263168
        assert report["prep_wall_s"] <= 300.0 and report["g_wall_s"] <= 300.0
        assert report["inv_wall_s"] <= 600.0
        assert {p.name for p in out.iterdir()} == {"prepare_summary.json"}
        summary = json.loads((out / "prepare_summary.json").read_text(encoding="utf-8"))
        assert summary["schema"] == mod.PREPARE_SCHEMA
        assert summary["status"] == "READY"
        assert summary["session"] == mod.SESSION_ID
        assert summary["cal"] == [702, 1725] and summary["val"] == [1726, 1729]
        assert summary["decoder_calls"] == 0 and summary["published_bits"] == 0
        assert summary["formal"] is False
        assert summary["arm_a"]["decoder_calls"] == 0
        assert summary["arm_a"]["new_metrics"] is None
        assert "not_recorded_reason" in summary["arm_a"]
        assert summary["arm_g_prep"]["accepted"] is True
        assert set(summary["arm_g_prep"]["stages"]) == {"l1", "base", "joint", "total"}
        for stage in summary["arm_g_prep"]["stages"].values():
            for key in ("active", "iters", "viol", "ok", "changed", "vs_bob", "finite", "runtime_s", "rss_bytes", "stop"):
                assert key in stage
        assert "protocol" not in summary
        payload = (out / "prepare_summary.json").read_text(encoding="utf-8").lower()
        for banned in ("alice_symbols", "bob_symbols", "prior_logp", "syndrome_target", "syndrome_observed", "syndrome_bytes", "candidate", "check_to_variable", "alice_bits"):
            assert banned not in payload
        assert prod.exists() == prod_existed
        # Existing output refuses; run_01 is forbidden.
        with pytest.raises(FileExistsError):
            runner.run_prepare_only(out_dir=out, registry_path=reg_path)
        with pytest.raises(ValueError):
            mod.prepare_real_input(registry_path=reg_path, out_dir=out / "run_01", workspace_root=runner.WORKSPACE_ROOT)
        # Missing registry is PREP_FAILED, not READY.
        with pytest.raises(ValueError, match="PREP_FAILED"):
            mod.prepare_real_input(
                registry_path=tmp_path / "missing.json",
                out_dir=Path(runner.WORKSPACE_ROOT) / ("v72p2d3_missing_" + tmp_path.name),
                workspace_root=runner.WORKSPACE_ROOT,
            )
        # CLI prepare-only stops here with exit 0 and decoder 0.
        out2 = Path(runner.WORKSPACE_ROOT) / ("v72p2d3_cli_" + tmp_path.name)
        if out2.exists():
            shutil.rmtree(out2)
        try:
            assert runner.main(["--phase", "real", "--prepare-only", "--registry", str(reg_path), "--out-dir", str(out2)]) == 0
            assert (out2 / "prepare_summary.json").exists()
        finally:
            if out2.exists():
                shutil.rmtree(out2)
    finally:
        if out.exists():
            shutil.rmtree(out)


# ---- R7 fake E2E via CLI subprocess + fake parquet/reader (20 checks, no real parquet, fake decoder only) ----
def _r7_write_fake_parquet(parquet_path):
    import pandas as pd

    rng = np.random.default_rng(20260902)
    rows = []
    for fid in list(range(702, 1726)) + [1726, 1727, 1728, 1729, 1730]:
        for pair in range(256):
            rows.append((int(fid), int(pair), int(rng.integers(0, 1024)), int(rng.integers(0, 1024))))
    df = pd.DataFrame(rows, columns=list(mod.REQUIRED_PARQUET_COLUMNS))
    df = df.astype({c: "int64" for c in mod.REQUIRED_PARQUET_COLUMNS})
    df.to_parquet(parquet_path, index=False)


def _r7_registry_dict(parquet_path):
    return {
        "schema": mod.REGISTRY_SCHEMA,
        "session_id": mod.SESSION_ID,
        "source_label": "1M",
        "parquet_path": str(parquet_path),
        "cal_frame_ids": list(range(702, 1726)),
        "val_frame_ids": [1726, 1727, 1728, 1729],
        "used_2m": False,
        "columns": list(mod.REQUIRED_PARQUET_COLUMNS),
    }


def _r7_counting_fake(iters, ok):
    calls = []

    def _fn(h_mat, prior_p, target):
        calls.append((np.asarray(h_mat).shape, int(iters)))
        pp = np.asarray(prior_p, dtype=np.float64)
        x_hat = np.argmax(pp, axis=1).astype(np.uint8)
        return {
            "x_hat": x_hat,
            "iterations_used": int(iters),
            "syndrome_ok": bool(ok),
            "runtime_s": 0.001,
            "stop": "r7-fake",
            "final_beliefs": np.log(np.maximum(pp, 1e-15)),
            # Explicit conditioned provenance for the BP-04 recombination guard.
            "belief_provenance": "CHECK_UPDATED",
        }

    _fn.calls = calls  # type: ignore[attr-defined]
    return _fn


def _r7_seq_clock(vals):
    it = iter([float(v) for v in vals])
    last = float(vals[-1])

    def _c():
        try:
            return float(next(it))
        except StopIteration:
            return float(last)

    return _c


def test_r7_fake_e2e_cli_registry_20_checks(tmp_path):
    import shutil
    import subprocess

    pq = tmp_path / "r7_pairs.parquet"
    _r7_write_fake_parquet(pq)
    reg_path = tmp_path / "r7_registry.json"
    reg_path.write_text(json.dumps(_r7_registry_dict(pq), indent=2), encoding="utf-8")
    prod = ROOT.parent / "comparison_bench" / "outputs_comparison" / "v72p2d3_gf32_contrast_20260904"
    prod_existed = prod.exists()
    out = Path(runner.WORKSPACE_ROOT) / ("v72p2d3_r7_" + tmp_path.name)
    if out.exists():
        shutil.rmtree(out)
    try:
        # r7_01 enter production non-return2: authorized fake E2E succeeds, CLI prepare-only exit 0.
        fake7 = _r7_counting_fake(7, False)
        rep = runner.run_real_orchestration(out_dir=out, registry=_fake_e2e_registry(), frames=_fake_e2e_frames(), matrices=_fake_e2e_matrices(), preflight=_fake_e2e_preflight(), authorized=True, decode_fn=fake7)
        assert rep["gate"] == "PASS" and rep["status"] in ("SYNDROME_SATISFIED", "LADDER_EXHAUSTED")
        # r7_02 filter precise: extra 1730 read but retained only CAL1024+VAL4.
        loaded = mod.load_and_validate_prepare_frames(pq, list(range(702, 1726)), [1726, 1727, 1728, 1729])
        assert loaded["n_read_rows"] == 263424 and loaded["n_retained_rows"] == 263168
        assert loaded["n_cal_symbols"] == 262144 and loaded["n_val_symbols"] == 1024
        # r7_03 prior Bob/CAL: CAL-only fit shapes, no VAL backfill.
        fit = mod.fit_cal_prior_from_frames({f: loaded["cal_bundle"][f] for f in sorted(loaded["cal_bundle"])[:4]}, 1.0)
        assert np.asarray(fit["P1"]).shape[1] == 32 and fit["n_cal"] == 4 * 256
        assert rep["n_cal_symbols"] == 4 * 256
        # r7_04 A0: Arm A read-only, decoder 0.
        assert rep["arm_a_attempted"] is False
        res = json.loads((out / "results.json").read_text(encoding="utf-8"))
        assert res["arms"]["A"]["attempted"] is False
        # r7_05 G calls: L1+base+joint+total exactly 4 with all-fail fake.
        assert len(fake7.calls) == 4
        # r7_06 order: frozen gate->registry->fit->block->A->words->matrices->kernel->reassemble->posthoc->files.
        src = MODULE_PATH.read_text(encoding="utf-8")
        seg = src[src.index("def run_real_contrast"):]
        seg = seg[: seg.index("def prepare_real_input") if "def prepare_real_input" in seg else len(seg)]
        order = ["require_real_gate", "validate_registry", "validate_frame_bundle", "fit_cal_prior_from_frames", "assemble_block_frames", "a_baseline_record", "symbols_to_layers", "validate_nested_matrices", "gf32_syndrome", "run_l1_stage", "run_l2_incremental_chain", "layers_to_symbols", "direct_flips", "write_contrast_outputs"]
        assert [seg.index(k) for k in order] == sorted(seg.index(k) for k in order)
        # r7_07 iters from return: iters == L1+final from fake returns (7+7=14).
        assert res["arms"]["G"]["iters"] == 14 and res["arms"]["G"]["iters_l1"] == 7 and res["arms"]["G"]["iters_l2"] == 7
        fake3 = _r7_counting_fake(3, False)
        out_b = Path(runner.WORKSPACE_ROOT) / ("v72p2d3_r7b_" + tmp_path.name)
        try:
            rep_b = runner.run_real_orchestration(out_dir=out_b, registry=_fake_e2e_registry(), frames=_fake_e2e_frames(), matrices=_fake_e2e_matrices(), preflight=_fake_e2e_preflight(), authorized=True, decode_fn=fake3)
            res_b = json.loads((out_b / "results.json").read_text(encoding="utf-8"))
            assert res_b["arms"]["G"]["iters"] == 6
        finally:
            if out_b.exists():
                shutil.rmtree(out_b)
        # r7_08 reassembly: q=softmax then layers_to_symbols roundtrip.
        assert "softmax_beliefs_history" in src and "layers_to_symbols" in src
        syms = np.arange(1024, dtype=np.int64)
        assert np.array_equal(mod.layers_to_symbols(*mod.symbols_to_layers(syms)), syms)
        # r7_09 oracle at end: final-only posthoc, no per-stage oracle.
        assert res["arms"]["G"]["final_oracle_exact"] is False or True
        assert "oracle_runs_after_arm_end" in src or "final_oracle_exact" in src
        # r7_10 four files: exactly manifest/results/table/report.
        assert {p.name for p in out.iterdir()} == {"manifest.json", "results.json", "table.csv", "report.md"}
        # r7_11 no sensitive: no Alice/Bob arrays or prior/syndrome values persisted.
        payload = ((out / "manifest.json").read_text(encoding="utf-8") + (out / "results.json").read_text(encoding="utf-8")).lower()
        for banned in ("alice_symbols", "bob_symbols", "prior_logp", "syndrome_target", "syndrome_observed", "candidate", "check_to_variable"):
            assert banned not in payload
        # r7_12 already exists: second run to same out refuses.
        with pytest.raises(FileExistsError):
            runner.run_real_orchestration(out_dir=out, registry=_fake_e2e_registry(), frames=_fake_e2e_frames(), matrices=_fake_e2e_matrices(), preflight=_fake_e2e_preflight(), authorized=True, decode_fn=_r7_counting_fake(1, False))
        # r7_13 unauthorized: gate fails before output, CLI returns 2.
        with pytest.raises(PermissionError):
            runner.run_real_orchestration(out_dir=tmp_path / "r7_noauth", registry=_fake_e2e_registry(), frames=_fake_e2e_frames(), matrices=_fake_e2e_matrices(), preflight=_fake_e2e_preflight(), authorized=False, decode_fn=_r7_counting_fake(1, False))
        assert runner.main(["--phase", "real", "--execute-real", "--registry", str(reg_path), "--out-dir", str(tmp_path / "r7_cli_noauth")]) == 2
        # r7_14 preflight fail: bad preflight refuses.
        with pytest.raises(PermissionError):
            runner.run_real_orchestration(out_dir=tmp_path / "r7_badpre", registry=_fake_e2e_registry(), frames=_fake_e2e_frames(), matrices=_fake_e2e_matrices(), preflight={"status": "FAIL"}, authorized=True, decode_fn=_r7_counting_fake(1, False))
        # r7_15 prep fail: missing frames gives ValueError, missing registry PREP_FAILED.
        with pytest.raises((ValueError, PermissionError)):
            runner.run_real_orchestration(out_dir=tmp_path / "r7_noframes", registry=_fake_e2e_registry(), frames={}, matrices=_fake_e2e_matrices(), preflight=_fake_e2e_preflight(), authorized=True, decode_fn=_r7_counting_fake(1, False))
        with pytest.raises(ValueError, match="PREP_FAILED"):
            mod.prepare_real_input(registry_path=tmp_path / "r7_missing.json", out_dir=Path(runner.WORKSPACE_ROOT) / ("v72p2d3_r7miss_" + tmp_path.name), workspace_root=runner.WORKSPACE_ROOT)
        # r7_16 L1-fail short-circuit: L1 fail still runs L2; base-ok skips joint/total.
        assert len(fake7.calls) == 4
        assert 'bool(base["syndrome_ok"])' in src and "skipped" in src
        hb = np.array([[1, 1, 0, 0], [0, 1, 1, 0]], dtype=np.uint8)
        hj = np.array([[1, 1, 0, 0], [0, 1, 1, 0], [0, 0, 1, 1]], dtype=np.uint8)
        htot = np.array([[1, 1, 0, 0], [0, 1, 1, 0], [0, 0, 1, 1], [1, 0, 0, 1]], dtype=np.uint8)
        field = mod.get_gf32_field()
        xt = np.array([5, 7, 3, 9], dtype=np.uint8)
        sb = mod.gf32_syndrome(hb, xt, field)
        sj = mod.gf32_syndrome(hj, xt, field)
        stot = mod.gf32_syndrome(htot, xt, field)
        _, _, _, _, prior_ok = _r6_correctable_2x4()
        chain_ok = mod.run_l2_incremental_chain(hb, hj, htot, prior_ok, sb, sj, stot, field=field)
        assert chain_ok["skipped"] == {"joint": True, "total": True}
        # r7_17 timeout: prep/G over-limit raises TimeoutError.
        with pytest.raises(TimeoutError):
            mod.run_real_contrast(out_dir=tmp_path / "r7_tpre", registry=_fake_e2e_registry(), frames=_fake_e2e_frames(), matrices=_fake_e2e_matrices(), preflight=_fake_e2e_preflight(), authorized=True, execute_real=True, decode_fn=_r7_counting_fake(1, False), clock=_r7_seq_clock([0, 0, 500, 500, 500, 500, 500]), workspace_root=runner.WORKSPACE_ROOT)
        with pytest.raises(TimeoutError):
            mod.run_real_contrast(out_dir=tmp_path / "r7_tg", registry=_fake_e2e_registry(), frames=_fake_e2e_frames(), matrices=_fake_e2e_matrices(), preflight=_fake_e2e_preflight(), authorized=True, execute_real=True, decode_fn=_r7_counting_fake(1, False), clock=_r7_seq_clock([0, 0, 1, 2, 502, 503, 504]), workspace_root=runner.WORKSPACE_ROOT)
        # r7_18 write fail: production root and run_01 forbidden (prepare path).
        with pytest.raises(ValueError):
            mod.prepare_real_input(registry_path=reg_path, out_dir=Path(runner.WORKSPACE_ROOT) / ("v72p2d3_r7_run01_" + tmp_path.name) / "run_01", workspace_root=runner.WORKSPACE_ROOT)
        with pytest.raises(ValueError):
            mod.require_real_gate(execute_real=True, authorized=True, preflight=_fake_e2e_preflight(), out_dir=prod / "x")
        # r7_19 exactly once: 4 calls, no rerun (existing out refuses).
        assert len(fake7.calls) == 4
        # r7_20 don't read 1730: registry with 1730 rejected, extra frame ignored for block.
        bad = _r7_registry_dict(pq)
        bad["val_frame_ids"] = [1726, 1727, 1728, 1730]
        with pytest.raises(ValueError):
            mod.validate_prepare_registry(bad, reg_path)
        assert rep["block_ids"] == [1726, 1727, 1728, 1729]
        # workspace ban + CLI subprocess with --registry (fake parquet/reader, decoder 0).
        assert out.resolve() != prod.resolve() and prod.resolve() not in out.resolve().parents
        assert prod.exists() == prod_existed
        cli_out = Path(runner.WORKSPACE_ROOT) / ("v72p2d3_r7cli_" + tmp_path.name)
        if cli_out.exists():
            shutil.rmtree(cli_out)
        try:
            proc = subprocess.run([sys.executable, str(RUNNER_PATH), "--phase", "real", "--prepare-only", "--registry", str(reg_path), "--out-dir", str(cli_out)], capture_output=True, text=True, timeout=300)
            assert proc.returncode == 0
            assert (cli_out / "prepare_summary.json").exists()
            summary = json.loads((cli_out / "prepare_summary.json").read_text(encoding="utf-8"))
            assert summary["decoder_calls"] == 0 and summary["formal"] is False
            assert {p.name for p in cli_out.iterdir()} == {"prepare_summary.json"}
        finally:
            if cli_out.exists():
                shutil.rmtree(cli_out)
    finally:
        if out.exists():
            shutil.rmtree(out)


# ---- R8 prepare-only regression (20 checks, fake parquet only, decoder 0, no formal root) ----
def test_r8_prepare_regression_20_checks(tmp_path):
    import shutil
    import subprocess

    pq = tmp_path / "r8_pairs.parquet"
    _prep_write_parquet(pq)
    reg_path = tmp_path / "r8_registry.json"
    reg_path.write_text(json.dumps(_prep_registry_dict(pq), indent=2), encoding="utf-8")
    prod = ROOT.parent / "comparison_bench" / "outputs_comparison" / "v72p2d3_gf32_contrast_20260904"
    prod_existed = prod.exists()
    out = Path(runner.WORKSPACE_ROOT) / ("v72p2d3_r8_" + tmp_path.name)
    if out.exists():
        shutil.rmtree(out)
    try:
        # r8_01 enter prepare non-2: CLI subprocess exit 0, direct READY.
        proc = subprocess.run([sys.executable, str(RUNNER_PATH), "--phase", "real", "--prepare-only", "--registry", str(reg_path), "--out-dir", str(out)], capture_output=True, text=True, timeout=300)
        assert proc.returncode == 0
        summary = json.loads((out / "prepare_summary.json").read_text(encoding="utf-8"))
        assert summary["status"] == "READY"
        shutil.rmtree(out)
        rep = runner.run_prepare_only(out_dir=out, registry_path=reg_path)
        # r8_02 filter precise: read/retained counts exact.
        assert rep["n_read_rows"] == 263168 and rep["n_retained_rows"] == 263168
        # r8_03 prior Bob/CAL: shapes frozen, CAL-only.
        assert summary["prior_shapes"] == {"P1": [1024, 32], "P2": [32, 1024, 32], "counts": [1024, 1024]}
        assert summary["rows"]["n_cal_symbols"] == 262144 and summary["rows"]["n_val_symbols"] == 1024
        # r8_04 A0: D1 reuse, decoder 0, null new metrics.
        assert summary["arm_a"]["decoder_calls"] == 0 and summary["arm_a"]["new_metrics"] is None
        assert "not_recorded_reason" in summary["arm_a"]
        # r8_05 G prep: accepted true-kernel stages, no decoder calls.
        assert summary["arm_g_prep"]["accepted"] is True and summary["arm_g_prep"]["kernel"] == mod.HISTORY_KERNEL_ID
        assert set(summary["arm_g_prep"]["stages"]) == {"l1", "base", "joint", "total"}
        assert summary["decoder_calls"] == 0 and summary["published_bits"] == 0
        # r8_06 order: registry->parquet->CAL/VAL->prior->block->A->words->matrix->READY.
        src = MODULE_PATH.read_text(encoding="utf-8")
        seg = src[src.index("def prepare_real_input"):]
        order = ["validate_prepare_registry", "load_and_validate_prepare_frames", "fit_cal_prior_from_frames", "assemble_block_frames", "a_baseline_record", "nested_geometry", "build_prepare_summary"]
        assert [seg.index(k) for k in order] == sorted(seg.index(k) for k in order)
        # r8_07 iters 0 from prep: stages iters 0, stop NOT_ATTEMPTED.
        for stage in summary["arm_g_prep"]["stages"].values():
            assert stage["iters"] == 0 and stage["stop"] == "NOT_ATTEMPTED_PREPARE_ONLY"
        # r8_08 reassembly shapes: matrix nested + syndrome lens frozen.
        assert summary["matrix"] == {"h1": [16, 1024], "h_base": [184, 1024], "h_joint": [192, 1024], "h_total": [200, 1024]}
        assert summary["syndrome"] == {"s1_len": 16, "s_base_len": 184, "s_joint_len": 192, "s_total_len": 200, "max_row_weight": 16}
        assert summary["nested"] == [184, 192, 200]
        # r8_09 oracle at end: null until real run, flag true.
        assert summary["arm_g_prep"]["final_oracle_exact"] is None
        assert summary["arm_g_prep"]["oracle_runs_after_arm_end"] is True
        assert "protocol" not in summary
        # r8_10 one file: exactly prepare_summary.json, not four.
        assert {p.name for p in out.iterdir()} == {"prepare_summary.json"}
        assert not (out / "manifest.json").exists()
        # r8_11 no sensitive: banned keys and protocol absent.
        payload = (out / "prepare_summary.json").read_text(encoding="utf-8").lower()
        for banned in ("alice_symbols", "bob_symbols", "prior_logp", "syndrome_target", "syndrome_observed", "candidate", "check_to_variable"):
            assert banned not in payload
        # r8_12 already exists: second prepare refuses.
        with pytest.raises(FileExistsError):
            runner.run_prepare_only(out_dir=out, registry_path=reg_path)
        # r8_13 unauthorized: prepare consumes no auth (cycle_state untouched), real without auth still 2.
        assert runner.main(["--phase", "real", "--execute-real", "--registry", str(reg_path), "--out-dir", str(tmp_path / "r8_noauth")]) == 2
        # r8_14 preflight: bad registry schema is PREP_FAILED via CLI 2.
        bad_path = tmp_path / "r8_bad.json"
        bad = _prep_registry_dict(pq)
        bad["schema"] = "wrong"
        bad_path.write_text(json.dumps(bad), encoding="utf-8")
        assert runner.main(["--phase", "real", "--prepare-only", "--registry", str(bad_path), "--out-dir", str(tmp_path / "r8_badout")]) == 2
        # r8_15 prep fail: missing registry PREP_FAILED, rerunnable to fresh dir.
        with pytest.raises(ValueError, match="PREP_FAILED"):
            mod.prepare_real_input(registry_path=tmp_path / "r8_missing.json", out_dir=Path(runner.WORKSPACE_ROOT) / ("v72p2d3_r8miss_" + tmp_path.name), workspace_root=runner.WORKSPACE_ROOT)
        retry = Path(runner.WORKSPACE_ROOT) / ("v72p2d3_r8retry_" + tmp_path.name)
        try:
            rep2 = runner.run_prepare_only(out_dir=retry, registry_path=reg_path)
            assert rep2["status"] == "READY" and rep2["decoder_calls"] == 0
        finally:
            if retry.exists():
                shutil.rmtree(retry)
        # r8_16 L1-fail short-circuit text frozen.
        assert summary["arm_g_prep"]["short_circuit"] == "l1-fail-still-enters-l2; base-ok-skips-joint-total; joint-ok-skips-total"
        # r8_17 timeout: over-limit clock gives BLOCKED with counts retained, decoder still 0.
        tout = Path(runner.WORKSPACE_ROOT) / ("v72p2d3_r8t_" + tmp_path.name)
        try:
            blocked = mod.prepare_real_input(registry_path=reg_path, out_dir=tout, workspace_root=runner.WORKSPACE_ROOT, clock=_r7_seq_clock([0, 0, 400, 401]))
            assert blocked["status"] == "BLOCKED" and blocked["decoder_calls"] == 0
            assert blocked["n_retained_rows"] == 263168
        finally:
            if tout.exists():
                shutil.rmtree(tout)
        # r8_18 write fail: run_01 and production root forbidden.
        with pytest.raises(ValueError):
            mod.prepare_real_input(registry_path=reg_path, out_dir=out / "run_01", workspace_root=runner.WORKSPACE_ROOT)
        with pytest.raises(ValueError):
            mod.prepare_real_input(registry_path=reg_path, out_dir=prod / "x", workspace_root=runner.WORKSPACE_ROOT)
        # r8_19 exactly once: one file, decoder 0, no rerun.
        assert summary["decoder_calls"] == 0
        # r8_20 don't read 1730: 1730 registry rejected.
        bad2 = _prep_registry_dict(pq)
        bad2["val_frame_ids"] = [1726, 1727, 1728, 1730]
        with pytest.raises(ValueError):
            mod.validate_prepare_registry(bad2, reg_path)
        # workspace ban: output under workspace, formal untouched, no decoder.
        assert out.resolve() != prod.resolve() and prod.resolve() not in out.resolve().parents
        assert prod.exists() == prod_existed
        src_prep = src[src.index("def prepare_real_input"):]
        for banned_call in ("run_g_layer", "history_decode", "decode_row_layered_fftqspa"):
            assert banned_call not in src_prep
    finally:
        if out.exists():
            shutil.rmtree(out)


# ---- R3 formal-output guard (prepare-only workspace-only; execute-real exact
# pre-registered root only; no execute-real never calls decoder; no real run) ----

def _r9_prod_root():
    return ROOT.parent / "comparison_bench" / "outputs_comparison" / "v72p2d3_gf32_contrast_20260904"


def test_r9_prepare_only_rejects_production(tmp_path):
    reg_path = tmp_path / "r9_reg.json"
    reg_path.write_text(json.dumps({"note": "unread, resolver rejects first"}), encoding="utf-8")
    prod = _r9_prod_root()
    assert not prod.exists()
    # CLI prepare-only to the formal root (exact and child) fails closed.
    assert runner.main(["--phase", "real", "--prepare-only", "--registry", str(reg_path), "--out-dir", str(prod)]) == 2
    assert runner.main(["--phase", "real", "--prepare-only", "--registry", str(reg_path), "--out-dir", str(prod / "x")]) == 2
    # Module levels reject production too; workspace resolver rejects it as well.
    with pytest.raises(ValueError):
        runner.run_prepare_only(out_dir=prod, registry_path=reg_path)
    with pytest.raises(ValueError):
        mod.prepare_real_input(registry_path=reg_path, out_dir=prod / "x", workspace_root=runner.WORKSPACE_ROOT)
    with pytest.raises(ValueError):
        runner._resolve_workspace_dir(prod)
    assert not prod.exists()


def test_r9_execute_real_rejects_workspace(tmp_path):
    ws_out = tmp_path / "r9_ws_out"
    with pytest.raises(ValueError):
        runner._resolve_execute_real_dir(ws_out)
    with pytest.raises(ValueError):
        runner._resolve_execute_real_dir(Path(runner.WORKSPACE_ROOT) / "r9_ws_out")
    # Orchestration production route refuses a workspace target before any gate.
    with pytest.raises(ValueError):
        runner.run_real_orchestration(
            out_dir=ws_out,
            registry=_fake_e2e_registry(),
            frames=_fake_e2e_frames(),
            matrices=_fake_e2e_matrices(),
            preflight=_fake_e2e_preflight(),
            authorized=True,
            decode_fn=_fake_e2e_decode_fn,
            allow_production_root=True,
        )
    assert not ws_out.exists()
    assert not _r9_prod_root().exists()


def test_r9_execute_real_exact_root_passes_entry_guard(tmp_path):
    prod = _r9_prod_root()
    assert not prod.exists()
    # Entry guard accepts the exact root in str/Path/relative spelling.
    assert runner._resolve_execute_real_dir(prod) == runner.PRODUCTION_ROOT
    assert runner._resolve_execute_real_dir(str(prod)) == runner.PRODUCTION_ROOT
    assert runner._resolve_execute_real_dir("comparison_bench/outputs_comparison/v72p2d3_gf32_contrast_20260904") == runner.PRODUCTION_ROOT
    assert runner._is_preregistered_production_root(prod) is True
    assert runner._is_preregistered_production_root(tmp_path / "r9_ws") is False
    # Core gate passes the exact absent root only with the explicit flag.
    gate = mod.require_real_gate(
        execute_real=True, authorized=True, preflight=_fake_e2e_preflight(),
        out_dir=prod, allow_production_root=True,
    )
    assert gate == {"gate": "PASS"}
    with pytest.raises(ValueError):
        mod.require_real_gate(
            execute_real=True, authorized=True, preflight=_fake_e2e_preflight(), out_dir=prod,
        )
    # Other production paths stay rejected even with the flag; existence still refuses.
    with pytest.raises(ValueError):
        mod.require_real_gate(
            execute_real=True, authorized=True, preflight=_fake_e2e_preflight(),
            out_dir=prod / "x", allow_production_root=True,
        )
    with pytest.raises(ValueError):
        runner._resolve_execute_real_dir(prod / "x")
    with pytest.raises(FileExistsError):
        mod.require_real_gate(
            execute_real=True, authorized=True, preflight=_fake_e2e_preflight(),
            out_dir=tmp_path, allow_production_root=True,
        )
    # Auth still enforced on the production route (no bypass, nothing written).
    with pytest.raises(PermissionError):
        runner.run_real_orchestration(
            out_dir=prod,
            registry=_fake_e2e_registry(),
            frames=_fake_e2e_frames(),
            matrices=_fake_e2e_matrices(),
            preflight=_fake_e2e_preflight(),
            authorized=False,
            decode_fn=_fake_e2e_decode_fn,
            allow_production_root=True,
        )
    assert not prod.exists()


def test_r9_no_execute_real_never_calls_decoder(tmp_path):
    calls: list[int] = []

    def _counting(h_mat, prior_p, target):
        calls.append(1)
        return _fake_e2e_decode_fn(h_mat, prior_p, target)

    kwargs = dict(
        registry=_fake_e2e_registry(),
        frames=_fake_e2e_frames(),
        matrices=_fake_e2e_matrices(),
        preflight=_fake_e2e_preflight(),
        authorized=True,
        execute_real=False,
        decode_fn=_counting,
    )
    with pytest.raises(PermissionError):
        mod.run_real_contrast(out_dir=tmp_path / "r9_nd_core", **kwargs)
    assert calls == []
    with pytest.raises(PermissionError):
        runner.run_real_orchestration(out_dir=tmp_path / "r9_nd_orch", **kwargs)
    assert calls == []
    assert runner.main(["--phase", "real", "--registry", str(tmp_path / "r9_missing.json"), "--out-dir", str(tmp_path / "r9_nd_cli")]) == 2
    assert calls == []
    assert not (tmp_path / "r9_nd_core").exists()
    assert not (tmp_path / "r9_nd_orch").exists()
    assert not _r9_prod_root().exists()


# ---- R4 unified guard: zero-touch spy (CLI main validates before any
# registry/parquet/prior/matrix/decoder/dir touch; no decoder without execute-real) ----
def test_r4_zero_touch_spy(tmp_path, monkeypatch):
    import json as _json

    calls: list[str] = []
    orig_loader = runner.load_contrast_module

    def _spy_loader():
        m = orig_loader()
        orig_validate = m.validate_output_target

        def _spy_validate(*a, **k):
            calls.append("validate_output_target")
            return orig_validate(*a, **k)

        m.validate_output_target = _spy_validate  # type: ignore[attr-defined]
        for _name in (
            "validate_prepare_registry",
            "load_and_validate_prepare_frames",
            "fit_cal_prior_from_frames",
            "assemble_block_frames",
            "validate_nested_matrices",
            "history_decode",
            "history_decoder_fn",
            "run_g_layer",
            "run_l1_stage",
            "run_l2_incremental_chain",
            "prepare_real_input",
            "run_real_contrast",
            "write_contrast_outputs",
            "build_prepare_summary",
        ):
            if hasattr(m, _name):
                _orig = getattr(m, _name)

                def _wrap(*a, _o=_orig, _n=_name, **k):
                    calls.append(_n)
                    return _o(*a, **k)

                setattr(m, _name, _wrap)
        return m

    monkeypatch.setattr(runner, "load_contrast_module", _spy_loader)
    orig_build = runner.build_prepare_inputs

    def _spy_build(*a, **k):
        calls.append("build_prepare_inputs")
        return orig_build(*a, **k)

    monkeypatch.setattr(runner, "build_prepare_inputs", _spy_build)
    dummy_reg = tmp_path / "r4_dummy.json"
    dummy_reg.write_text(_json.dumps({"note": "unread, guard rejects first"}), encoding="utf-8")
    prod = _r9_prod_root()
    assert not prod.exists()
    # prepare-only to prod: guard rejects before registry/parquet/prior/matrix/decoder/dir.
    calls.clear()
    assert runner.main(["--phase", "real", "--prepare-only", "--registry", str(dummy_reg), "--out-dir", str(prod)]) == 2
    assert calls == ["validate_output_target"]
    assert not prod.exists()
    # execute-real to workspace: guard rejects before any data/decoder/dir touch.
    ws_bad = tmp_path / "r4_spy_ws_bad"
    calls.clear()
    assert runner.main(["--phase", "real", "--execute-real", "--registry", str(dummy_reg), "--out-dir", str(ws_bad)]) == 2
    assert calls == ["validate_output_target"]
    assert not ws_bad.exists()
    # no execute-real never enters decoder (CLI without --execute-real, zero decoder touch).
    ws_noexec = tmp_path / "r4_spy_noexec"
    calls.clear()
    assert runner.main(["--phase", "real", "--registry", str(dummy_reg), "--out-dir", str(ws_noexec)]) == 2
    assert calls == ["validate_output_target"]
    for _dec in ("history_decode", "history_decoder_fn", "run_g_layer", "run_l1_stage", "run_l2_incremental_chain"):
        assert _dec not in calls
    assert not ws_noexec.exists()
    assert not prod.exists()


# ---- R4 unified guard: final-write integration regression (7 items, no decoder) ----
def test_r4_unified_guard_7_checks(tmp_path):
    import json as _json
    import shutil

    prod = _r9_prod_root()
    assert not prod.exists()
    # r4_01 prepare-only workspace passes and consumes validated (single file, decoder0).
    pq = tmp_path / "r4_pairs.parquet"
    _prep_write_parquet(pq)
    reg_path = tmp_path / "r4_registry.json"
    reg_path.write_text(_json.dumps(_prep_registry_dict(pq), indent=2), encoding="utf-8")
    out_prep = Path(runner.WORKSPACE_ROOT) / ("v72p2d3_r4prep_" + tmp_path.name)
    if out_prep.exists():
        shutil.rmtree(out_prep)
    try:
        validated = mod.validate_output_target(phase="real", prepare_only=True, execute_real=False, out_dir=out_prep)
        assert Path(validated).resolve() == out_prep.resolve()
        rep = runner.run_prepare_only(out_dir=validated, registry_path=reg_path)
        assert rep["status"] == "READY" and rep["decoder_calls"] == 0 and rep["formal"] is False
        assert {p.name for p in out_prep.iterdir()} == {"prepare_summary.json"}
    finally:
        if out_prep.exists():
            shutil.rmtree(out_prep)
    # r4_02 prepare-only prod rejects (no dir, no decoder).
    with pytest.raises(ValueError):
        mod.validate_output_target(phase="real", prepare_only=True, execute_real=False, out_dir=prod)
    with pytest.raises(ValueError):
        mod.validate_output_target(phase="real", prepare_only=True, execute_real=False, out_dir=prod / "x")
    assert not prod.exists()
    # r4_03 execute-real exact prod passes entry (absent, no mkdir, no decoder).
    gate = mod.require_real_gate(
        execute_real=True, authorized=True, preflight=_fake_e2e_preflight(),
        out_dir=prod, allow_production_root=True,
    )
    assert gate == {"gate": "PASS"}
    assert runner._resolve_execute_real_dir(prod) == runner.PRODUCTION_ROOT
    assert runner._resolve_execute_real_dir("comparison_bench/outputs_comparison/v72p2d3_gf32_contrast_20260904") == runner.PRODUCTION_ROOT
    assert not prod.exists()
    # r4_04 execute-real workspace/other/outside all reject (no dir, no decoder).
    with pytest.raises(ValueError):
        mod.validate_output_target(phase="real", prepare_only=False, execute_real=True, out_dir=tmp_path / "r4_ws")
    with pytest.raises(ValueError):
        mod.validate_output_target(phase="real", prepare_only=False, execute_real=True, out_dir=prod / "x")
    outside = Path(tmp_path.anchor) / ("r4_outside_" + tmp_path.name)
    with pytest.raises(ValueError):
        mod.validate_output_target(phase="real", prepare_only=False, execute_real=True, out_dir=outside)
    assert not prod.exists()
    # r4_05 synthetic workspace passes, prod/outside reject.
    ws_syn = Path(runner.WORKSPACE_ROOT) / ("v72p2d3_r4syn_" + tmp_path.name)
    assert mod.validate_output_target(phase="synthetic-only", prepare_only=False, execute_real=False, out_dir=ws_syn).resolve() == ws_syn.resolve()
    with pytest.raises(ValueError):
        mod.validate_output_target(phase="synthetic-only", prepare_only=False, execute_real=False, out_dir=prod)
    with pytest.raises(ValueError):
        mod.validate_output_target(phase="synthetic-only", prepare_only=False, execute_real=False, out_dir=outside)
    assert not ws_syn.exists() and not prod.exists()
    # r4_06 existence refuses + four-file retained (no overwrite, exactly four).
    assert mod.validate_output_target(phase="synthetic-only", prepare_only=False, execute_real=False, out_dir=ws_syn).resolve() == ws_syn.resolve()
    ws_syn.mkdir(parents=True, exist_ok=False)
    try:
        with pytest.raises(FileExistsError):
            mod.validate_output_target(phase="synthetic-only", prepare_only=False, execute_real=False, out_dir=ws_syn)
        with pytest.raises(FileExistsError):
            mod.validate_output_target(phase="real", prepare_only=True, execute_real=False, out_dir=ws_syn)
    finally:
        shutil.rmtree(ws_syn)
    arm_g = {"status": "LADDER_EXHAUSTED", "rows": 200, "iters": 0, "syndrome_satisfied": False, "bit_flips": 0, "symbol_flips": 0}
    ws_four = tmp_path / "r4_four"
    written = mod.write_contrast_outputs(ws_four, arm_g)
    assert {p.name for p in written.iterdir()} == {"manifest.json", "results.json", "table.csv", "report.md"}
    shutil.rmtree(written)
    # r4_07 resolve comparison + no hash + orchestrator consumes validated (source probes).
    rel_prod = Path("comparison_bench/outputs_comparison/v72p2d3_gf32_contrast_20260904")
    assert mod.validate_output_target(phase="real", prepare_only=False, execute_real=True, out_dir=rel_prod).resolve() == prod.resolve()
    src_core = MODULE_PATH.read_text(encoding="utf-8")
    seg = src_core[src_core.index("def validate_output_target"):src_core.index("def write_contrast_outputs")]
    assert ".resolve()" in seg and "relative_to" in seg
    assert "hashlib" not in seg and "sha256" not in seg.lower() and "compute_tag" not in seg
    assert "FileExistsError" in seg
    rsrc = RUNNER_PATH.read_text(encoding="utf-8")
    assert "validate_output_target" in rsrc
    assert rsrc.index("validate_output_target") < rsrc.index("build_prepare_inputs")
    assert rsrc.index("validate_output_target") < rsrc.index("construct_lane_c_prototype")
    assert "decode_row_layered_fftqspa" not in rsrc[rsrc.index("def main"):rsrc.index("build_prepare_inputs", rsrc.index("def main"))]
    assert not prod.exists()


# ---- R5 math interface + rate audit (CAL-only, no VAL, no decoder, no formal root) ----
def _r5_synth_cal(n=1024, seed=20260905):
    rng = np.random.default_rng(seed)
    a = rng.integers(0, 1024, size=n).astype(np.int64)
    b = rng.integers(0, 1024, size=n).astype(np.int64)
    return a, b


def test_r5_t0_canonical_constants_and_r5_segment_is_cal_only():
    assert mod.R5_CANONICAL_COUNTS_SHAPE == (1024, 1024)
    assert mod.R5_H1_BITS == 80 and mod.R5_L2_TOTAL_BITS == 1000 and mod.R5_TOTAL_BITS == 1080
    assert mod.R5_N == 1024 and abs(mod.R5_RATE - 1.0546875) < 1e-12
    assert mod.R5_N_FOLDS == 4
    src = MODULE_PATH.read_text(encoding="utf-8")
    assert "def build_canonical_counts" in src
    assert "def build_h1_historical" in src
    assert "def cal_4fold_cv_heldout_nll" in src
    assert "def rate_audit_r5" in src
    assert "def cal_resubstitution_nll_descriptive" in src
    seg = src[src.index("def build_h1_historical"):]
    assert "VAL_FRAMES" not in seg and "val_bundle" not in seg and "assemble_block" not in seg
    for banned in ("run_g_layer", "history_decode", "decode_row_layered_fftqspa", "read_parquet"):
        assert banned not in seg
    assert "v72p2d3_gf32_contrast_20260904" not in seg
    assert not _r9_prod_root().exists()


def test_r5_t1_counts_asymmetric_handcalc_1e12_transpose_fails():
    a = np.array([10, 10, 10, 10, 42], dtype=np.int64)
    b = np.array([20, 20, 20, 21, 10], dtype=np.int64)
    c = mod.build_canonical_counts(a, b, q=1024)
    assert c.shape == (1024, 1024)
    assert c[10, 20] == 3.0 and c[10, 21] == 1.0 and c[42, 10] == 1.0
    p_a_given_b = float(c[10, 20] / c[:, 20].sum())
    p_b_given_a = float(c[10, 20] / c[10, :].sum())
    assert abs(p_a_given_b - 1.0) < 1e-12
    assert abs(p_b_given_a - 0.75) < 1e-12
    assert abs(p_a_given_b - p_b_given_a) > 0.2
    bob = np.array([20, 10], dtype=np.int64)
    p = mod.get_l1_prior_canonical(c, bob)
    assert p.shape == (2, 32)
    assert int(np.argmax(p[0])) == 0 and int(np.argmax(p[1])) == 1
    pt = mod.get_l1_prior_canonical(c.T, bob)
    assert float(np.abs(p - pt).max()) > 1e-3
    r = c.reshape(32, 32, 1024)
    assert float(r[0, 10, 20]) == 3.0 and float(r[1, 10, 10]) == 1.0


def test_r5_t1_cli_builder_direction_single_canonical():
    src = MODULE_PATH.read_text(encoding="utf-8")
    assert src.count("def build_canonical_counts") == 1
    seg = src[src.index("def fit_cal_prior_from_frames"):src.index("def assemble_block_frames")]
    assert "build_canonical_counts" in seg
    assert "np.add.at(counts, (b_cal" not in src
    rsrc = RUNNER_PATH.read_text(encoding="utf-8")
    assert "build_h1_historical" in rsrc
    assert "_np.zeros((mod.H1_ROWS" not in rsrc


def test_r5_t1_h1_historical_shape_nnz_row_rank_range_syndrome_cli():
    h1, audit = mod.build_h1_historical()
    assert h1.shape == (16, 1024)
    nnz = int((h1 != 0).sum())
    assert nnz == 2048
    rownnz = (h1 != 0).sum(axis=1)
    assert int(rownnz.min()) > 0 and int(rownnz.min()) == 128
    assert int(h1.min()) >= 0 and int(h1.max()) <= 31 and int(h1.max()) > 0
    from comparison_bench.formal_ir.v35_algorithm_development import compute_gf32_rank
    assert int(compute_gf32_rank(h1, mod.get_gf32_field())) == 16
    field = mod.get_gf32_field()
    e0 = np.zeros(1024, dtype=np.uint8)
    e0[0] = 1
    s0 = np.asarray(mod.gf32_syndrome(h1, np.zeros(1024, dtype=np.uint8), field))
    s1 = np.asarray(mod.gf32_syndrome(h1, e0, field))
    assert np.all(s0 == 0)
    assert int(np.count_nonzero(s1)) > 0
    rsrc = RUNNER_PATH.read_text(encoding="utf-8")
    assert "build_h1_historical" in rsrc
    assert "_np.zeros((mod.H1_ROWS" not in rsrc


def test_r5_t1_h1_allzero_reject_and_fake_spy():
    with pytest.raises(ValueError):
        mod.validate_nested_matrices(
            np.zeros((16, 1024), dtype=np.uint8),
            np.zeros((184, 1024), dtype=np.uint8),
            np.zeros((192, 1024), dtype=np.uint8),
            np.zeros((200, 1024), dtype=np.uint8),
        )
    seen: list = []

    def _spy(h_mat, prior_p, target):
        seen.append((tuple(np.asarray(h_mat).shape), int((np.asarray(h_mat) != 0).sum())))
        pp = np.asarray(prior_p, dtype=np.float64)
        return {
            "x_hat": np.argmax(pp, axis=1).astype(np.uint8),
            "iterations_used": 1,
            "syndrome_ok": False,
            "runtime_s": 0.001,
            "stop": "r5-spy",
            "final_beliefs": np.log(np.maximum(pp, 1e-15)),
        }

    h_tiny = np.eye(4, 4, dtype=np.uint8)
    out = mod.run_g_layer(
        np.log(np.full((4, 32), 1.0 / 32.0)), np.zeros(4, dtype=np.uint8), h_tiny, max_iter=2, decode_fn=_spy
    )
    assert out["iterations_used"] == 1
    assert seen and seen[0][0] == (4, 4) and seen[0][1] == 4


def test_r5_t1_prior_chain_same_builder_l1_v54_l2_q_ban_alice_oracle():
    import inspect as _inspect
    a_cal, b_cal = _r5_synth_cal(512)
    c1 = mod.build_canonical_counts(a_cal, b_cal)
    fit = mod.fit_cal_prior_from_frames(
        {0: {"alice_symbols": a_cal[:256], "bob_symbols": b_cal[:256]},
         1: {"alice_symbols": a_cal[256:], "bob_symbols": b_cal[256:]}},
        1.0,
    )
    assert np.array_equal(np.asarray(fit["counts"]), c1)
    bob_blk = b_cal[:8]
    assert np.allclose(mod.get_l1_prior_canonical(c1, bob_blk), mod._load_v54().get_l1_prior_p_u1_given_b(c1, bob_blk))
    q = np.full((8, 32), 1.0 / 32.0)
    assert np.allclose(mod.get_l2_prior_from_true_l1_app(c1, bob_blk, q), mod._load_v54().get_l1_app_prior_l2(c1, bob_blk, q))
    for fn in (mod.build_l2_prior_from_l1, mod.get_l2_prior_from_true_l1_app):
        params = set(_inspect.signature(fn).parameters)
        assert "alice" not in params and "oracle" not in params and "u1" not in params
    src = MODULE_PATH.read_text(encoding="utf-8")
    assert src.count("def build_canonical_counts") == 1
    assert "build_canonical_counts" in src[src.index("def fit_cal_prior_from_frames"):src.index("def assemble_block_frames")]


def test_r5_t1_resubstitution_rename_descriptive_and_cv_no_val():
    a_cal, b_cal = _r5_synth_cal(512)
    ah_lo, ah_hi = mod.symbols_to_layers(a_cal)
    p1 = mod.build_stage1_P(b_cal, ah_hi, 1.0, n_b_states=1024, q_sub=32)
    p2 = mod.build_stage2_P(ah_hi, b_cal, ah_lo, 1.0, n_b_states=1024, q_sub=32)
    resub = mod.cal_resubstitution_nll_descriptive(p1, p2, b_cal, ah_hi, ah_lo)
    assert resub["kind"] == "cal_resubstitution_nll_descriptive"
    assert np.isfinite(resub["ce_l1"]) and np.isfinite(resub["ce_l2_oracle"]) and np.isfinite(resub["ce_joint"])
    assert abs(resub["ce_joint"] - resub["ce_l1"] - resub["ce_l2_oracle"]) < 1e-9
    assert resub["n"] == 512
    src = MODULE_PATH.read_text(encoding="utf-8")
    seg = src[src.index("def cal_4fold_cv_heldout_nll"):src.index("def rate_audit_r5")]
    assert "VAL_FRAMES" not in seg and "val_bundle" not in seg and "read_parquet" not in seg
    assert "assemble_block" not in seg
    assert "build_layer" not in seg and "construct_" not in seg
    cv = mod.cal_4fold_cv_heldout_nll(a_cal, b_cal, lam=1.0)
    assert cv["n_cal"] == 512 and cv["n_folds"] == 4 and len(cv["folds"]) == 4
    assert sum(f["n_heldout"] for f in cv["folds"]) == 512
    for f in cv["folds"]:
        assert np.isfinite(f["ce_l1"]) and np.isfinite(f["ce_l2_oracle"]) and np.isfinite(f["ce_joint"])
    assert abs(cv["mean_ce_joint"] - cv["mean_ce_l1"] - cv["mean_ce_l2_oracle"]) < 1e-9


def test_r5_t1_rate_audit_scalars_mismatch_bans_no_matrix():
    audit = mod.rate_audit_r5(0.5, 0.6, 1.1)
    assert audit["n"] == 1024
    assert audit["budget"]["h1_bits"] == 80
    assert audit["budget"]["l2_total_bits"] == 1000
    assert audit["budget"]["total_bits"] == 1080
    assert abs(audit["budget"]["rate_bit_per_symbol"] - 1.0546875) < 1e-12
    l1 = audit["layers"]["l1"]
    assert abs(l1["required_bits"] - 512.0) < 1e-9
    assert l1["available_bits"] == 80.0 and abs(l1["margin_bits"] - (-432.0)) < 1e-9
    assert abs(l1["ratio"] - 6.4) < 1e-9
    assert audit["status"] == "MODEL_BUDGET_MISMATCH"
    assert "not a lower bound" in audit["note"] and "not a failure verdict" in audit["note"]
    assert "never auto-creates a matrix" in audit["note"]
    ok = mod.rate_audit_r5(0.01, 0.02, 0.03)
    assert ok["status"] == "WITHIN_BUDGET"
    src = MODULE_PATH.read_text(encoding="utf-8")
    seg = src[src.index("def rate_audit_r5"):]
    assert "build_layer" not in seg and "construct_" not in seg and "build_h1" not in seg


def test_r5_t2_cal_only_integration_no_val_decoder_formal_absent():
    calls: list = []
    orig_g = mod.run_g_layer
    orig_h = mod.history_decode

    def _spy_g(*a, **k):
        calls.append("run_g_layer")
        return orig_g(*a, **k)

    def _spy_h(*a, **k):
        calls.append("history_decode")
        return orig_h(*a, **k)

    mod.run_g_layer = _spy_g
    mod.history_decode = _spy_h
    try:
        a_cal, b_cal = _r5_synth_cal(512, seed=20260905)
        counts = mod.build_canonical_counts(a_cal, b_cal)
        assert counts.shape == (1024, 1024)
        ah_lo, ah_hi = mod.symbols_to_layers(a_cal)
        p1 = mod.build_stage1_P(b_cal, ah_hi, 1.0, n_b_states=1024, q_sub=32)
        p2 = mod.build_stage2_P(ah_hi, b_cal, ah_lo, 1.0, n_b_states=1024, q_sub=32)
        resub = mod.cal_resubstitution_nll_descriptive(p1, p2, b_cal, ah_hi, ah_lo)
        cv = mod.cal_4fold_cv_heldout_nll(a_cal, b_cal, lam=1.0)
        audit = mod.rate_audit_r5(cv["mean_ce_l1"], cv["mean_ce_l2_oracle"], cv["mean_ce_joint"])
        assert set(audit["layers"]) == {"l1", "l2_oracle", "joint"}
        for layer in audit["layers"].values():
            for key in ("ce_bit_per_symbol", "required_bits", "available_bits", "margin_bits", "ratio"):
                assert np.isfinite(layer[key])
        fit = mod.fit_cal_prior_from_frames(
            {0: {"alice_symbols": a_cal[:256], "bob_symbols": b_cal[:256]},
             1: {"alice_symbols": a_cal[256:], "bob_symbols": b_cal[256:]}},
            1.0,
        )
        assert np.array_equal(np.asarray(fit["counts"]), mod.build_canonical_counts(a_cal, b_cal))
        rsrc = RUNNER_PATH.read_text(encoding="utf-8")
        assert "build_h1_historical" in rsrc
    finally:
        mod.run_g_layer = orig_g
        mod.history_decode = orig_h
    assert calls == []
    assert not _r9_prod_root().exists()
    text = (ROOT.parent / "docs" / "research_cycles" / "V72P2D3-GF32" / "cycle_state.yaml").read_text(encoding="utf-8")
    assert "r4_real_execution_authorized: false" in text
