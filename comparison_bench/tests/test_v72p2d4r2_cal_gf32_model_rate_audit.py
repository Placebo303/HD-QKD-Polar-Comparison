"""V72P2D4R2 CAL GF32 model rate audit — T0/T1/T2 qualification, CAL-only U/G/F/L."""
from __future__ import annotations

import importlib.util
import inspect
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
MODULE_PATH = ROOT / "src" / "comparison_bench" / "formal_ir" / "v72p2d4r2_cal_gf32_model_rate_audit.py"
RUNNER_PATH = ROOT.parent / "scripts" / "v72p2d4r2_cal_gf32_model_rate_audit.py"
R1_MODULE_PATH = ROOT / "src" / "comparison_bench" / "formal_ir" / "v72p2d4r1_cal_gf32_model_rate_audit.py"

SPEC = importlib.util.spec_from_file_location("v72p2d4r2_audit_test_module", str(MODULE_PATH))
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

RSPEC = importlib.util.spec_from_file_location("v72p2d4r2_runner_test_module", str(RUNNER_PATH))
assert RSPEC is not None and RSPEC.loader is not None
runner = importlib.util.module_from_spec(RSPEC)
RSPEC.loader.exec_module(runner)


def _tiny_ab(n: int = 2000, seed: int = 7):
    rng = np.random.default_rng(seed)
    a = rng.integers(0, 1024, size=n, dtype=np.int64)
    b = rng.integers(0, 1024, size=n, dtype=np.int64)
    return a, b


def _tiny_bundle(n_frames: int = 8, seed: int = 11, start: int = 702):
    rng = np.random.default_rng(seed)
    bundle: dict[int, dict[str, np.ndarray]] = {}
    for i in range(n_frames):
        fid = start + i
        bundle[fid] = {
            "alice_symbols": rng.integers(0, 1024, size=256, dtype=np.int64),
            "bob_symbols": rng.integers(0, 1024, size=256, dtype=np.int64),
        }
    return bundle


def _full_bundle(seed: int = 20260905):
    rng = np.random.default_rng(seed)
    bundle: dict[int, dict[str, np.ndarray]] = {}
    for fid in range(702, 1726):
        bundle[fid] = {
            "alice_symbols": rng.integers(0, 1024, size=256, dtype=np.int64),
            "bob_symbols": rng.integers(0, 1024, size=256, dtype=np.int64),
        }
    return bundle


def _write_full_parquet(parquet_path: Path, seed: int = 20260905):
    import pandas as pd

    rng = np.random.default_rng(seed)
    fids = list(range(702, 1726)) + [1726, 1727, 1728, 1729]
    n = len(fids) * 256
    frame_ids = np.repeat(np.array(fids, dtype=np.int64), 256)
    pair_idx = np.tile(np.arange(256, dtype=np.int64), len(fids))
    alice = rng.integers(0, 1024, size=n, dtype=np.int64)
    bob = rng.integers(0, 1024, size=n, dtype=np.int64)
    df = pd.DataFrame({"frame_id": frame_ids, "pair_idx": pair_idx, "alice_symbol": alice, "bob_symbol": bob})
    df.to_parquet(parquet_path, index=False)
    return parquet_path


def _registry_dict(parquet_path: Path):
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


# ---------------- T0: import / structural / tiny math (10) ----------------

def test_t0_01_constants_frozen():
    assert mod.Q == 1024 and mod.Q_SUB == 32 and mod.N == 1024
    assert (mod.CAL_START, mod.CAL_END) == (702, 1725)
    assert mod.SESSION_ID == "20260123_1M_600k_0dB"
    assert mod.CYCLE_ID == "V72P2D4R2-CAL-GF32-MODEL-RATE"
    assert mod.AUDIT_SCHEMA == "v72p2d4r2_cal_gf32_model_rate_audit_v1"
    assert mod.REGISTRY_SCHEMA == "v72p2d3_real_registry_v1"
    assert mod.FLOOR == 1e-300 and mod.NORM_TOL == 1e-12 and mod.CHAIN_TOL == 1e-10
    assert len(mod.LAMBDA_GRID) == 30 and all(v > 0 for v in mod.LAMBDA_GRID)
    assert mod.M3_STATUS == "M3_EXIT_AMBIGUOUS"
    assert mod.CIRCULANT_STATUS == "CIRCULANT_DEFERRED"
    assert mod.UNIFORM_CE_L1 == 5.0 and mod.UNIFORM_CE_L2 == 5.0 and mod.UNIFORM_CE_JOINT == 10.0
    assert mod.UNIFORM_STATUS == "uniform_reference_descriptive"
    assert mod.SELECT_DELTA == 0.02 and mod.STABILITY_STD == 0.10 and mod.STABILITY_RANGE == 0.20
    assert tuple(mod.F_LIST) == (1.0, 1.1, 1.2, 1.3)
    assert tuple(mod.MODEL_ORDER) == ("G", "F", "L")
    assert (mod.H1_ROWS, mod.L2_ROWS, mod.TOTAL_ROWS) == (16, 200, 216)
    assert mod.OUT_DIR_NAME == "v72p2d4r2_cal_gf32_model_rate_audit_20260905"
    assert mod.PREP_LIMIT_S == 300.0 and mod.G_LIMIT_S == 300.0
    assert mod.INV_LIMIT_S == 600.0 and mod.RSS_LIMIT_BYTES == 2 * 1024**3


def test_t0_02_required_api_and_no_decoder_hash_strings():
    for name in ("outer_folds", "inner_folds_for_outer", "build_canonical_counts",
                 "build_g", "build_f", "build_l", "m3_exit_record",
                 "circulant_deferred_record", "uniform_reference_record", "uniform_ce",
                 "ce_g", "ce_f", "ce_l", "inner_select_lambda_for_f",
                 "r5_synth_repro", "select_model", "budget_for_model", "budget_rows",
                 "route_from_selection", "run_cal_audit", "validate_output_target",
                 "validate_registry", "load_cal_arrays"):
        assert callable(getattr(mod, name)), name
    src = MODULE_PATH.read_text(encoding="utf-8")
    low = src.lower()
    for banned in ("decode_row_layered", "history_decode", "run_g_layer", "warm_beliefs",
                   "compute_tag", "hashlib", "sha256", "md5", "checksum"):
        assert banned.lower() not in low, banned
    assert "zeros((16,1024))" not in src
    assert "VAL1726" not in src
    assert "val_bundle" not in low and "val_frame" not in low
    assert "mock" not in low and "stub" not in low


def test_t0_03_no_decoder_params():
    params = set(inspect.signature(mod.run_cal_audit).parameters)
    assert {"registry_path", "out_dir", "lam_grid"} <= params
    for forbidden in ("decode_fn", "execute_real", "authorized", "preflight", "frames", "matrices", "val_ids", "val_frames"):
        assert forbidden not in params
    for fn in (mod.build_g, mod.build_f, mod.build_l):
        fp = set(inspect.signature(fn).parameters)
        for forbidden in ("decode_fn", "execute_real", "val_ids", "val_frames"):
            assert forbidden not in fp


def test_t0_04_cli_no_forbidden_options():
    parser = runner.build_parser()
    dests = {a.dest for a in parser._actions}
    assert {"registry", "out_dir"} <= dests
    for forbidden in ("execute_real", "prepare_only", "phase", "seed", "val", "val_frames", "authorized", "decode", "lam"):
        assert forbidden not in dests
    opt_strings: list[str] = []
    for a in parser._actions:
        opt_strings.extend(a.option_strings)
    assert "--execute-real" not in opt_strings and "--lam" not in opt_strings
    assert not any(s.startswith("--val") for s in opt_strings)
    rsrc = RUNNER_PATH.read_text(encoding="utf-8")
    assert "--execute-real" not in rsrc and "read_parquet" not in rsrc
    assert "import pandas" not in rsrc and "mock" not in rsrc.lower()


def test_t0_05_mapping_direction_lsb():
    syms = np.array([0, 1, 31, 32, 33, 511, 1023], dtype=np.int64)
    low, high = mod.symbols_to_layers(syms)
    assert low.tolist() == [0, 1, 31, 0, 1, 31, 31]
    assert high.tolist() == [0, 0, 0, 1, 1, 15, 31]
    assert np.array_equal(low + 32 * high, syms)


def test_t0_06_canonical_counts_shape():
    a = np.array([0, 1, 1023, 512], dtype=np.int64)
    b = np.array([0, 0, 1, 1], dtype=np.int64)
    counts = mod.build_canonical_counts(a, b, q=1024)
    assert counts.shape == (1024, 1024) and float(counts.sum()) == 4.0
    assert counts[0, 0] == 1.0 and counts[1023, 1] == 1.0
    with pytest.raises(ValueError):
        mod.build_canonical_counts(np.array([], dtype=np.int64), np.array([], dtype=np.int64))


def test_t0_07_budget_math_rows():
    assert mod.budget_rows(1.0, 1.0) == 205  # ceil(1024/5)
    b = mod.budget_for_model(0.01, 0.05, 0.06)
    assert set(b["grid"]) == {"1.0", "1.1", "1.2", "1.3"}
    cell = b["grid"]["1.0"]["L1"]
    assert cell["available_rows"] == 16 and cell["required_rows"] == mod.budget_rows(0.01, 1.0)
    assert b["grid"]["1.3"]["Total"]["available_rows"] == 216
    r = mod.route_from_selection(0.01, 0.05, 0.06)
    assert r["route"] == "A"
    r2 = mod.route_from_selection(5.0, 5.0, 10.0)
    assert r2["route"] == "C"


def test_t0_08_output_guard_basics(tmp_path):
    fresh = tmp_path / "audit_fresh"
    assert mod.validate_output_target(fresh) == fresh.resolve()
    with pytest.raises(FileExistsError):
        mod.validate_output_target(tmp_path)
    with pytest.raises(ValueError):
        mod.validate_output_target(tmp_path / "run_01")
    with pytest.raises(ValueError):
        mod.validate_output_target(Path("/definitely_outside_ws_r2_test_xyz") / "x")


def test_t0_09_runner_mirrors_constants():
    assert runner.CYCLE_ID == mod.CYCLE_ID
    assert runner.PREP_LIMIT_S == mod.PREP_LIMIT_S == 300.0
    assert runner.WORKSPACE_ROOT == mod._workspace_root()
    assert runner.PRODUCTION_ROOT == mod._production_root()


def test_t0_10_exit_deferred_records_excluded():
    m3 = mod.m3_exit_record()
    assert m3["status"] == "M3_EXIT_AMBIGUOUS"
    assert m3["in_selection"] is False and m3["in_budget"] is False and m3["in_route"] is False
    cd = mod.circulant_deferred_record()
    assert cd["status"] == "CIRCULANT_DEFERRED"
    assert cd["in_selection"] is False and cd["in_budget"] is False and cd["in_route"] is False
    u = mod.uniform_reference_record()
    assert u["status"] == "uniform_reference_descriptive"
    assert u["in_selection"] is False and u["in_budget"] is False and u["in_route"] is False


# ---------------- T1: focused unit + tamper ----------------

def test_t1_01_uniform_exact():
    u = mod.uniform_ce()
    assert u["ce_l1"] == 5.0 and u["ce_l2"] == 5.0 and u["ce_joint"] == 10.0
    rec = mod.uniform_reference_record()
    assert rec["ce_l1"] == 5.0 and rec["ce_l2"] == 5.0 and rec["ce_joint"] == 10.0
    # Exactness: -log2(1/1024)=10, -log2(1/32)=5.
    assert -np.log2(1.0 / 1024.0) == pytest.approx(10.0)
    assert -np.log2(1.0 / 32.0) == pytest.approx(5.0)
    assert rec["p"] == pytest.approx(1.0 / 1024.0)


def test_t1_02_g_b_independent():
    a = np.array([0, 0, 0, 1, 2, 2, 5, 5], dtype=np.int64)
    b1 = np.array([0, 1, 2, 3, 4, 5, 6, 7], dtype=np.int64)
    b2 = np.array([7, 6, 5, 4, 3, 2, 1, 0], dtype=np.int64)
    fg = mod.build_g(a)
    # P_G depends only on A counts, not on B.
    assert abs(float(fg["P_A"][0]) - 3.0 / 8.0) < 1e-12
    assert abs(float(fg["P_A"].sum()) - 1.0) < 1e-12
    s1 = mod.ce_g(fg, a, b1)
    s2 = mod.ce_g(fg, a, b2)
    assert s1["ce_joint"] == pytest.approx(s2["ce_joint"])
    assert s1["ce_l1"] == pytest.approx(s2["ce_l1"])


def test_t1_03_counts_transpose_handcalc():
    a = np.array([10, 10, 10, 10, 42], dtype=np.int64)
    b = np.array([20, 20, 20, 21, 10], dtype=np.int64)
    c = mod.build_canonical_counts(a, b, q=1024)
    assert c[10, 20] == 3.0 and c[10, 21] == 1.0 and c[42, 10] == 1.0
    assert abs(float(c[10, 20] / c[:, 20].sum()) - 1.0) < 1e-12
    assert abs(float(c[10, 20] / c[10, :].sum()) - 0.75) < 1e-12
    ct = mod.build_canonical_counts(b, a, q=1024)
    assert float(np.abs(c - ct).max()) > 0
    r = c.reshape(32, 32, 1024)
    assert float(r[0, 10, 20]) == 3.0


def test_t1_04_marginalization_f_u1_given_b():
    # F's P(U1|B) must equal P(A|B) marginalized over U2.
    a, b = _tiny_ab(1000, seed=13)
    ff = mod.build_f(a, b, 1.0)
    pab = np.asarray(ff["P_A_given_B"])
    pu1b = np.asarray(ff["P_U1_given_B"])
    cube = pab.reshape(32, 32, 1024)
    manual = cube.sum(axis=1).T
    assert np.allclose(pu1b, manual, atol=1e-12)
    assert np.allclose(pu1b.sum(axis=1), 1.0, atol=1e-12)


def test_t1_05_l_product_joint():
    # L joint must equal P1*P2 product; chain holds.
    a, b = _tiny_ab(800, seed=21)
    fl = mod.build_l(a, b, 1.0)
    p1 = np.asarray(fl["P1"])
    p2 = np.asarray(fl["P2"])
    a_te, b_te = a[:200], b[:200]
    low, high = mod.symbols_to_layers(a_te)
    joint = np.maximum(p1[b_te, high], mod.FLOOR) * np.maximum(p2[high, b_te, low], mod.FLOOR)
    joint = np.maximum(joint, mod.FLOOR)
    ce_j = float(-np.mean(np.log2(joint)))
    sc = mod.ce_l(fl, a_te, b_te)
    assert sc["ce_joint"] == pytest.approx(ce_j)
    assert sc["chain_err"] < 1e-10


def test_t1_06_handcalc_g_marginal_small():
    a = np.array([0, 0, 0, 1, 2, 2], dtype=np.int64)
    fg = mod.build_g(a)
    # Hand: P(0)=3/6=0.5, P(1)=1/6, P(2)=2/6.
    assert abs(float(fg["P_A"][0]) - 0.5) < 1e-12
    assert abs(float(fg["P_A"][1]) - 1.0 / 6.0) < 1e-9  # after floor+renorm, close
    assert abs(float(fg["P_A"].sum()) - 1.0) < 1e-12
    # Unseen symbol floored, chain holds.
    sc = mod.ce_g(fg, np.array([5, 0], dtype=np.int64), np.array([7, 7], dtype=np.int64))
    assert np.isfinite(sc["ce_joint"]) and sc["chain_err"] < 1e-10


def test_t1_07_grid30_properties():
    assert len(mod.LAMBDA_GRID) == 30 and all(v > 0 for v in mod.LAMBDA_GRID)
    assert all(np.isfinite(v) for v in mod.LAMBDA_GRID)
    # logspace(-2,3,30) endpoints.
    assert mod.LAMBDA_GRID[0] == pytest.approx(0.01)
    assert mod.LAMBDA_GRID[-1] == pytest.approx(1000.0)
    a, b = _tiny_ab(600, seed=17)
    for lam in (mod.LAMBDA_GRID[0], mod.LAMBDA_GRID[-1]):
        ff = mod.build_f(a, b, lam)
        assert np.allclose(np.asarray(ff["P_A_given_B"]).sum(axis=0), 1.0, atol=1e-12)
        fl = mod.build_l(a, b, lam)
        assert np.allclose(np.asarray(fl["P1"]).sum(axis=1), 1.0, atol=1e-12)


def test_t1_08_zero_leakage_grid30_outer_forbidden():
    src = MODULE_PATH.read_text(encoding="utf-8")
    # Grid constant is defined once; selection lives in inner path only.
    assert "LAMBDA_GRID" in src
    eval_src = src[src.index("def evaluate_outer_fold"):src.index("def inner_select_lambda_for_f")]
    assert "LAMBDA_GRID" not in eval_src
    assert "logspace" not in eval_src
    # Inner selection must not reference outer TEST ids (inner held-out only).
    inner_src = src[src.index("def inner_select_lambda_for_f"):src.index("def r5_synth_repro")]
    assert '["test_ids"]' not in inner_src and "['test_ids']" not in inner_src
    assert '["train_ids"]' not in inner_src and "['train_ids']" not in inner_src
    # Fold builders are deterministic: no shuffle machinery.
    fold_src = src[src.index("def outer_folds"):src.index("def _concat_bundle")]
    assert "permutation" not in fold_src and "default_rng" not in fold_src
    assert "shuffle(" not in fold_src.lower()


def test_t1_09_perturbation_invariant_outer_test():
    bundle = _full_bundle(seed=101)
    s1 = mod.inner_select_lambda_for_f(bundle, 0, (0.1, 1.0, 10.0))
    bundle2 = {k: {"alice_symbols": v["alice_symbols"].copy(), "bob_symbols": v["bob_symbols"].copy()} for k, v in bundle.items()}
    rng = np.random.default_rng(999)
    for fid in list(mod.OUTER_FOLDS[0]):
        bundle2[fid] = {"alice_symbols": rng.integers(0, 1024, size=256, dtype=np.int64),
                        "bob_symbols": rng.integers(0, 1024, size=256, dtype=np.int64)}
    s2 = mod.inner_select_lambda_for_f(bundle2, 0, (0.1, 1.0, 10.0))
    assert s1["selected_lam"] == s2["selected_lam"]


def test_t1_10_blocked_invalid_inputs():
    a, b = _tiny_ab(200, seed=31)
    with pytest.raises(ValueError):
        mod.build_g(np.array([], dtype=np.int64))
    with pytest.raises(ValueError):
        mod.build_f(a, b, 0.0)
    with pytest.raises(ValueError):
        mod.build_l(a, b, -1.0)
    with pytest.raises(ValueError):
        mod.inner_select_lambda_for_f(_full_bundle(seed=33), 0, ())
    with pytest.raises(ValueError):
        mod.inner_select_lambda_for_f(_full_bundle(seed=33), 0, (0.0, 1.0))
    with pytest.raises(ValueError):
        mod.build_canonical_counts(np.array([], dtype=np.int64), np.array([], dtype=np.int64))
    with pytest.raises(ValueError):
        mod.ce_f(mod.build_f(a, b, 1.0), np.array([], dtype=np.int64), np.array([], dtype=np.int64))
    # Wrong schema / missing registry is BLOCKED (fail-closed, no run started).
    with pytest.raises(ValueError):
        mod.validate_registry({"schema": "wrong"}, None)
    # Wrong audit schema refuses to write (blocked, no overwrite).
    with pytest.raises(ValueError):
        mod.write_audit_outputs(Path("/tmp/does_not_matter_r2_blocked"), {"schema": "wrong"})


def test_t1_11_normalized_chain_all_models():
    a, b = _tiny_ab(800, seed=9)
    fg = mod.build_g(a)
    assert mod.ce_g(fg, a, b)["chain_err"] < 1e-10
    assert np.all(np.abs(np.asarray(fg["P_A"]).sum() - 1.0) <= 1e-9)
    ff = mod.build_f(a, b, 1.0)
    assert mod.ce_f(ff, a, b)["chain_err"] < 1e-10
    assert np.all(np.abs(np.asarray(ff["P_A_given_B"]).sum(axis=0) - 1.0) <= 1e-12)
    fl = mod.build_l(a, b, 1.0)
    assert mod.ce_l(fl, a, b)["chain_err"] < 1e-10
    assert np.all(np.abs(np.asarray(fl["P1"]).sum(axis=1) - 1.0) <= 1e-12)
    bad = np.asarray(fl["P1"]).copy()
    bad[0, 0] += 1e-6
    with pytest.raises(ValueError):
        mod._check_normalized(bad, axis=1)


def test_t1_12_seen_sum_not_dropped():
    b_tr = np.array([1, 1, 2, 2], dtype=np.int64)
    b_te = np.array([1, 9, 2, 9], dtype=np.int64)
    loss = np.array([1.0, 2.0, 3.0, 4.0])
    s = mod._seen_split_scores(b_tr, b_te, loss)
    assert s["seen_frac"] == pytest.approx(0.5)
    assert s["n_seen"] == 2 and s["n_unseen"] == 2
    assert s["n_seen"] + s["n_unseen"] == 4
    assert s["ce_seen"] == pytest.approx(2.0) and s["ce_unseen"] == pytest.approx(3.0)


def test_t1_13_f_budget_four_tiers_vs_history():
    b = mod.budget_for_model(0.05, 0.5, 0.55)
    for f in (1.0, 1.1, 1.2, 1.3):
        g = b["grid"][str(float(f))]
        assert g["L1"]["available_rows"] == 16 and g["L2"]["available_rows"] == 200 and g["Total"]["available_rows"] == 216
        assert g["L1"]["required_rows"] == mod.budget_rows(0.05, f)
        assert g["L1"]["required_bits"] == pytest.approx(1024 * 0.05 * f)
    assert b["grid"]["1.0"]["L1"]["fit"] is True
    b2 = mod.budget_for_model(5.0, 0.01, 5.01)
    assert b2["grid"]["1.0"]["L1"]["fit"] is False


def test_t1_14_r1m2_r5_fixture_repro():
    r = mod.r5_synth_repro()
    assert r["passed"] is True
    assert abs(r["mean_ce_l1"] - 6.422161237462124) < 1e-6
    assert abs(r["mean_ce_l2_oracle"] - 5.083351288530697) < 1e-6
    assert abs(r["mean_ce_joint"] - 11.50551252599282) < 1e-6
    assert r["chain_err"] < 1e-10
    assert r["real_cal_exact_match"] is False
    assert r["root_cause"] == "R5_FIXTURE_REPRODUCED"
    # R1 M2 arithmetic equivalence: R2 L == R1 M2, R2 G == R1 M0, R2 F(lam=1) == R1 M1.
    r1spec = importlib.util.spec_from_file_location("v72p2d4r1_ref", str(R1_MODULE_PATH))
    assert r1spec is not None and r1spec.loader is not None
    r1 = importlib.util.module_from_spec(r1spec)
    r1spec.loader.exec_module(r1)
    a, b = _tiny_ab(500, seed=41)
    fg2 = mod.build_g(a)
    fm0 = r1.build_m0(a)
    assert np.allclose(np.asarray(fg2["P_A"]), np.asarray(fm0["P_A"]), atol=1e-12)
    ff2 = mod.build_f(a, b, 1.0)
    fm1 = r1.build_m1(a, b, 1.0)
    assert np.allclose(np.asarray(ff2["P_A_given_B"]), np.asarray(fm1["P_A_given_B"]), atol=1e-12)
    fl2 = mod.build_l(a, b, 1.0)
    fm2 = r1.build_m2(a, b, 1.0)
    assert np.allclose(np.asarray(fl2["P1"]), np.asarray(fm2["P1"]), atol=1e-12)
    assert np.allclose(np.asarray(fl2["P2"]), np.asarray(fm2["P2"]), atol=1e-12)


def _mk_outer(mean_joints: dict[str, list[float]]):
    rows = []
    for k in range(4):
        r: dict = {"fold": k, "n_train": 196608, "n_test": 65536}
        for m in ("G", "F", "L"):
            j = mean_joints[m][k]
            r[m] = {"ce_l1": j * 0.6, "ce_l2_oracle": j * 0.4, "ce_joint": j, "chain_err": 0.0, "seen_frac": 1.0, "lam": 1.0}
        rows.append(r)
    return rows


def test_t1_15_selection_delta002_simple_stability():
    assert mod.SELECT_DELTA == 0.02
    rows = _mk_outer({"G": [5.0, 5.0, 5.0, 5.0], "F": [4.0, 4.0, 4.0, 4.0], "L": [3.99, 3.99, 3.99, 3.99]})
    sel = mod.select_model(rows)
    assert sel["selected"] == "F" and sel["ranking"][0] == "L"
    rows2 = _mk_outer({"G": [5.0, 5.0, 5.0, 5.0], "F": [4.0, 4.0, 4.0, 4.0], "L": [3.0, 3.0, 3.0, 4.5]})
    sel2 = mod.select_model(rows2)
    assert sel2["stats"]["L"]["unstable"] is True
    assert sel2["selected"] == "F" and sel2["downgraded"] is True


def test_t1_16_root_cause_u_g_f_l():
    outer = [{"fold": k, "n_train": 600, "n_test": 200,
              "G": {"ce_l1": 5.0, "ce_l2_oracle": 4.0, "ce_joint": 9.0, "chain_err": 0.0, "seen_frac": 1.0},
              "F": {"ce_l1": 4.0, "ce_l2_oracle": 3.0, "ce_joint": 7.0, "chain_err": 0.0, "seen_frac": 1.0, "lam": 1.0},
              "L": {"ce_l1": 3.0, "ce_l2_oracle": 2.0, "ce_joint": 5.0, "chain_err": 0.0, "seen_frac": 1.0, "lam": 1.0}} for k in range(4)]
    sel = mod.select_model(outer)
    budgets = {m: mod.budget_for_model(4.0 if m != "L" else 3.0, 2.0, 7.0 if m != "L" else 5.0) for m in ("G", "F", "L")}
    route = mod.route_from_selection(3.0, 2.0, 5.0)
    r5 = mod.r5_synth_repro()
    inner = [{"outer_fold": k, "selected_lam": 1.0} for k in range(4)]
    loaded = {"n_cal_frames": 1024, "n_cal_symbols": 800, "n_read_rows": 800, "n_retained_rows": 800}
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        s = mod.build_audit_summary(registry_path=Path(td) / "reg.json", loaded=loaded, r5=r5,
                                    outer_results=outer, inner_selections=inner, selection=sel,
                                    budgets=budgets, route=route, prep_wall_s=0.1, g_wall_s=0.1, inv_wall_s=0.2, peak_rss=None)
    rc = s["root_cause_decomposition"]
    assert rc["u_to_g"] == pytest.approx(10.0 - 9.0)
    assert rc["g_to_f"] == pytest.approx(9.0 - 7.0)
    assert rc["f_to_l"] == pytest.approx(7.0 - 5.0)
    assert rc["u_to_selected"] == pytest.approx(10.0 - 5.0)
    assert s["uniform_reference_descriptive"]["ce_joint"] == 10.0
    assert s["m3"]["status"] == "M3_EXIT_AMBIGUOUS"
    assert s["circulant"]["status"] == "CIRCULANT_DEFERRED"


def test_t1_17_val0_decoder0_no_array(tmp_path):
    a, b = _tiny_ab(800, seed=23)
    fl = mod.build_l(a, b, 1.0)
    outer = [{"fold": k, "n_train": 600, "n_test": 200,
              "G": {"ce_l1": 5.0, "ce_l2_oracle": 4.0, "ce_joint": 9.0, "chain_err": 0.0, "seen_frac": 1.0},
              "F": {"ce_l1": 4.0, "ce_l2_oracle": 3.0, "ce_joint": 7.0, "chain_err": 0.0, "seen_frac": 1.0, "lam": 1.0},
              "L": {"ce_l1": 3.0, "ce_l2_oracle": 2.0, "ce_joint": 5.0, "chain_err": 0.0, "seen_frac": 1.0, "lam": 1.0}} for k in range(4)]
    sel = mod.select_model(outer)
    budgets = {m: mod.budget_for_model(3.0 if m == "L" else 4.0, 2.0, 5.0 if m == "L" else 7.0) for m in ("G", "F", "L")}
    route = mod.route_from_selection(3.0, 2.0, 5.0)
    r5 = mod.r5_synth_repro()
    inner = [{"outer_fold": k, "selected_lam": 1.0} for k in range(4)]
    loaded = {"n_cal_frames": 1024, "n_cal_symbols": 800, "n_read_rows": 800, "n_retained_rows": 800}
    s = mod.build_audit_summary(registry_path=tmp_path / "reg.json", loaded=loaded, r5=r5,
                                outer_results=outer, inner_selections=inner, selection=sel,
                                budgets=budgets, route=route, prep_wall_s=0.1, g_wall_s=0.1, inv_wall_s=0.2, peak_rss=None)
    payload = json.dumps(s, ensure_ascii=False).lower()
    for banned in ("alice_symbols", "bob_symbols", "prior_logp", "syndrome_target", "candidate"):
        assert banned not in payload
    assert s["decoder_calls"] == 0 and s["published_bits"] == 0 and s["formal"] is False
    assert s["cal_only"] is True
    # VAL0: registry validation never reads held-out parquet rows beyond CAL.
    assert "decoder" not in inspect.signature(mod.build_g).parameters
    src = MODULE_PATH.read_text(encoding="utf-8").lower()
    assert "val_bundle" not in src and "val_frame" not in src


# ---------------- T2: frame-blocked CV + full audit (5) ----------------

def test_t2_01_frame_blocked_mechanics_inner_no_shuffle():
    bundle = _full_bundle(seed=301)
    outer = mod.outer_folds()
    assert [len(f["test_ids"]) for f in outer] == [256, 256, 256, 256]
    assert [len(f["train_ids"]) for f in outer] == [768, 768, 768, 768]
    flat = sorted(sum([f["test_ids"] for f in outer], []))
    assert flat == list(range(702, 1726))
    for k in range(4):
        inners = mod.inner_folds_for_outer(k)
        train = set(outer[k]["train_ids"])
        test = set(outer[k]["test_ids"])
        seen: set[int] = set()
        for inn in inners:
            assert len(inn["inner_test_ids"]) == 256 and len(inn["inner_train_ids"]) == 512
            assert set(inn["inner_test_ids"]) & set(inn["inner_train_ids"]) == set()
            assert set(inn["inner_train_ids"]) | set(inn["inner_test_ids"]) == train
            assert set(inn["inner_test_ids"]) & test == set()
            seen |= set(inn["inner_test_ids"])
        assert seen == train
    sel = mod.inner_select_lambda_for_f(bundle, 1, (0.5, 1.0, 2.0))
    res = mod.evaluate_outer_fold(bundle, 1, sel["selected_lam"])
    assert res["n_train"] == 768 * 256 and res["n_test"] == 256 * 256
    # L reuses F lam (same-fold, no independent search).
    assert res["F"]["lam"] == res["L"]["lam"] == sel["selected_lam"]
    for m in ("G", "F", "L"):
        assert res[m]["chain_err"] < 1e-10 and np.isfinite(res[m]["ce_joint"])


def test_t2_02_full_workspace_audit_small_grid_replay(tmp_path):
    pq = tmp_path / "pairs.parquet"
    _write_full_parquet(pq, seed=401)
    reg_path = tmp_path / "registry.json"
    reg_path.write_text(json.dumps(_registry_dict(pq), indent=2), encoding="utf-8")
    out1 = tmp_path / "audit_r1"
    out2 = tmp_path / "audit_r2"
    r1 = mod.run_cal_audit(registry_path=reg_path, out_dir=out1, lam_grid=(0.5, 1.0, 2.0))
    r2 = mod.run_cal_audit(registry_path=reg_path, out_dir=out2, lam_grid=(0.5, 1.0, 2.0))
    assert r1["status"] == "READY" and r1["decoder_calls"] == 0 and r1["formal"] is False
    a1 = json.loads((out1 / "audit.json").read_text(encoding="utf-8"))
    a2 = json.loads((out2 / "audit.json").read_text(encoding="utf-8"))
    assert a1["outer_results"] == a2["outer_results"] and a1["selection"] == a2["selection"]
    assert (out1 / "table.csv").read_bytes() != b""
    assert {p.name for p in out1.iterdir()} == {"manifest.json", "audit.json", "table.csv", "report.md"}
    # U/G/F/L + M3 + circulant present, U excluded from selection.
    assert a1["uniform_reference_descriptive"]["ce_joint"] == 10.0
    assert a1["m3"]["status"] == "M3_EXIT_AMBIGUOUS"
    assert a1["circulant"]["status"] == "CIRCULANT_DEFERRED"
    assert a1["selection"]["selected"] in ("G", "F", "L")


def test_t2_03_no_overwrite_old_dirs_unchanged(tmp_path):
    prod = mod._production_root()
    existed = prod.exists()
    before = {p.name for p in prod.iterdir()} if existed else set()
    # R1 and Attempt-0 roots must exist and stay untouched.
    repo = Path(__file__).resolve().parents[2]
    r1_root = repo / "comparison_bench" / "outputs_comparison" / "v72p2d4r1_cal_gf32_model_rate_audit_20260905"
    a0_root = repo / "comparison_bench" / "outputs_comparison" / "v72p2d4_cal_gf32_model_rate_audit_20260905"
    assert r1_root.is_dir() and a0_root.is_dir()
    r1_before = {p.name for p in r1_root.iterdir()}
    a0_before = {p.name for p in a0_root.iterdir()}
    r1_bytes = {p.name: p.read_bytes() for p in r1_root.iterdir() if p.is_file()}
    a0_bytes = {p.name: p.read_bytes() for p in a0_root.iterdir() if p.is_file()}
    pq = tmp_path / "pairs.parquet"
    _write_full_parquet(pq, seed=402)
    reg_path = tmp_path / "registry.json"
    reg_path.write_text(json.dumps(_registry_dict(pq), indent=2), encoding="utf-8")
    out = tmp_path / "audit_once"
    first = mod.run_cal_audit(registry_path=reg_path, out_dir=out, lam_grid=(1.0, 2.0))
    assert first["status"] == "READY"
    with pytest.raises(FileExistsError):
        mod.run_cal_audit(registry_path=reg_path, out_dir=out, lam_grid=(1.0, 2.0))
    assert prod.exists() == existed
    if existed:
        assert {p.name for p in prod.iterdir()} == before
    assert {p.name for p in r1_root.iterdir()} == r1_before
    assert {p.name for p in a0_root.iterdir()} == a0_before
    for name, data in r1_bytes.items():
        assert (r1_root / name).read_bytes() == data
    for name, data in a0_bytes.items():
        assert (a0_root / name).read_bytes() == data


def test_t2_04_runner_fake_audit(tmp_path):
    pq = tmp_path / "pairs.parquet"
    _write_full_parquet(pq, seed=403)
    reg_path = tmp_path / "registry.json"
    reg_path.write_text(json.dumps(_registry_dict(pq), indent=2), encoding="utf-8")
    out = tmp_path / "audit_runner"
    assert runner.PRODUCTION_ROOT == mod._production_root()
    rc = runner.main(["--registry", str(reg_path), "--out-dir", str(out)])
    assert rc == 0
    assert {p.name for p in out.iterdir()} == {"manifest.json", "audit.json", "table.csv", "report.md"}


def test_t2_05_inner_grid30_deterministic():
    bundle = _full_bundle(seed=404)
    s1 = mod.inner_select_lambda_for_f(bundle, 2, None)
    s2 = mod.inner_select_lambda_for_f(bundle, 2, None)
    assert len(s1["inner_table"]) == 30 and s1 == s2
    assert s1["selected_lam"] in list(mod.LAMBDA_GRID)
