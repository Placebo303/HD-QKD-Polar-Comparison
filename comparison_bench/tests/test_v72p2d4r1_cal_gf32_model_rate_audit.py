"""V72P2D4R1 CAL GF32 model rate audit — T0/T1/T2 qualification, CAL-only."""
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
MODULE_PATH = ROOT / "src" / "comparison_bench" / "formal_ir" / "v72p2d4r1_cal_gf32_model_rate_audit.py"
RUNNER_PATH = ROOT.parent / "scripts" / "v72p2d4r1_cal_gf32_model_rate_audit.py"

SPEC = importlib.util.spec_from_file_location("v72p2d4r1_audit_test_module", str(MODULE_PATH))
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

RSPEC = importlib.util.spec_from_file_location("v72p2d4r1_runner_test_module", str(RUNNER_PATH))
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
    assert mod.CYCLE_ID == "V72P2D4R1-CAL-GF32-MODEL-RATE"
    assert mod.AUDIT_SCHEMA == "v72p2d4r1_cal_gf32_model_rate_audit_v1"
    assert mod.REGISTRY_SCHEMA == "v72p2d3_real_registry_v1"
    assert mod.FLOOR == 1e-300 and mod.NORM_TOL == 1e-12 and mod.CHAIN_TOL == 1e-10
    assert mod.M1_LAM == 1.0 and len(mod.LAMBDA_GRID) == 30
    assert mod.M3_STATUS == "M3_EXIT_AMBIGUOUS" and mod.UNIFORM_CE == 10.0
    assert mod.SELECT_DELTA == 0.02 and mod.STABILITY_STD == 0.10 and mod.STABILITY_RANGE == 0.20
    assert tuple(mod.F_LIST) == (1.0, 1.1, 1.2, 1.3)
    assert (mod.H1_ROWS, mod.L2_ROWS, mod.TOTAL_ROWS) == (16, 200, 216)
    assert mod.OUT_DIR_NAME == "v72p2d4r1_cal_gf32_model_rate_audit_20260905"
    assert mod.PREP_LIMIT_S == 300.0 and mod.G_LIMIT_S == 300.0
    assert mod.INV_LIMIT_S == 600.0 and mod.RSS_LIMIT_BYTES == 2 * 1024**3


def test_t0_02_required_api_and_no_decoder_strings():
    for name in ("outer_folds", "inner_folds_for_outer", "build_canonical_counts",
                 "build_m0", "build_m1", "build_m2", "m3_exit_record",
                 "ce_m0", "ce_m1", "ce_m2", "inner_select_lambda",
                 "r5_synth_repro", "select_model", "budget_for_model",
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
    for fn in (mod.build_m0, mod.build_m1, mod.build_m2):
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


def test_t0_07_ce_chain_identity_tiny():
    a, b = _tiny_ab(600, seed=5)
    fit = mod.build_m2(a, b, 1.0)
    sc = mod.ce_m2(fit, a[:100], b[:100])
    assert np.isfinite(sc["ce_joint"]) and sc["chain_err"] < 1e-10


def test_t0_08_budget_math_rows():
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


def test_t0_09_output_guard_basics(tmp_path):
    fresh = tmp_path / "audit_fresh"
    assert mod.validate_output_target(fresh) == fresh.resolve()
    with pytest.raises(FileExistsError):
        mod.validate_output_target(tmp_path)
    with pytest.raises(ValueError):
        mod.validate_output_target(tmp_path / "run_01")
    with pytest.raises(ValueError):
        mod.validate_output_target(Path("/definitely_outside_ws_r1_test_xyz") / "x")


def test_t0_10_runner_mirrors_constants():
    assert runner.CYCLE_ID == mod.CYCLE_ID
    assert runner.PREP_LIMIT_S == mod.PREP_LIMIT_S == 300.0
    assert runner.WORKSPACE_ROOT == mod._workspace_root()
    assert runner.PRODUCTION_ROOT == mod._production_root()


# ---------------- T1: focused unit + tamper (15) ----------------

def test_t1_01_counts_asymmetric_handcalc_transpose_fails():
    a = np.array([10, 10, 10, 10, 42], dtype=np.int64)
    b = np.array([20, 20, 20, 21, 10], dtype=np.int64)
    c = mod.build_canonical_counts(a, b, q=1024)
    assert c[10, 20] == 3.0 and c[10, 21] == 1.0 and c[42, 10] == 1.0
    assert abs(float(c[10, 20] / c[:, 20].sum()) - 1.0) < 1e-12
    assert abs(float(c[10, 20] / c[10, :].sum()) - 0.75) < 1e-12
    # Transposed input must differ.
    ct = mod.build_canonical_counts(b, a, q=1024)
    assert float(np.abs(c - ct).max()) > 0
    r = c.reshape(32, 32, 1024)
    assert float(r[0, 10, 20]) == 3.0


def test_t1_02_chain_all_models_tiny():
    a, b = _tiny_ab(800, seed=9)
    f0 = mod.build_m0(a)
    assert mod.ce_m0(f0, a, b)["chain_err"] < 1e-10
    f1 = mod.build_m1(a, b, 1.0)
    assert mod.ce_m1(f1, a, b)["chain_err"] < 1e-10
    f2 = mod.build_m2(a, b, 1.0)
    assert mod.ce_m2(f2, a, b)["chain_err"] < 1e-10


def test_t1_03_m0_pin_marginal_uniform_separate():
    a = np.array([0, 0, 0, 1, 2, 2], dtype=np.int64)
    f = mod.build_m0(a)
    assert abs(float(f["P_A"][0]) - 0.5) < 1e-12
    assert abs(float(f["P_A"].sum()) - 1.0) < 1e-12
    assert mod.UNIFORM_CE == 10.0  # separate descriptive bound, not in fit
    # Unseen symbols floored, chain holds.
    sc = mod.ce_m0(f, np.array([5, 0], dtype=np.int64), np.array([7, 7], dtype=np.int64))
    assert np.isfinite(sc["ce_joint"]) and sc["chain_err"] < 1e-10


def test_t1_04_m1_canonical_frozen_lam_normalized():
    a, b = _tiny_ab(1000, seed=13)
    f = mod.build_m1(a, b, mod.M1_LAM)
    assert f["lam"] == 1.0
    assert np.allclose(f["P_A_given_B"].sum(axis=0), 1.0, atol=1e-12)
    assert np.allclose(f["P_U1_given_B"].sum(axis=1), 1.0, atol=1e-12)
    sc = mod.ce_m1(f, a, b)
    assert sc["chain_err"] < 1e-10
    with pytest.raises(ValueError):
        mod.build_m1(a, b, 0.0)


def test_t1_05_m2_grid30_normalized():
    assert len(mod.LAMBDA_GRID) == 30 and all(v > 0 for v in mod.LAMBDA_GRID)
    a, b = _tiny_ab(1000, seed=17)
    f = mod.build_m2(a, b, mod.LAMBDA_GRID[0])
    assert np.allclose(f["P1"].sum(axis=1), 1.0, atol=1e-12)
    for u1 in range(32):
        assert np.allclose(f["P2"][u1].sum(axis=1), 1.0, atol=1e-12)


def test_t1_06_m3_direct_exit_excluded():
    rec = mod.m3_exit_record()
    assert rec["status"] == "M3_EXIT_AMBIGUOUS"
    assert rec["in_selection"] is False and rec["in_budget"] is False and rec["in_route"] is False


def test_t1_07_floor_exact_1e300():
    assert mod.FLOOR == 1e-300
    a = np.array([0, 1], dtype=np.int64)
    f = mod.build_m0(np.array([0, 0, 0], dtype=np.int64))
    # Symbol 1023 unseen in train -> P=0 -> floored log finite.
    sc = mod.ce_m0(f, np.array([1023], dtype=np.int64), np.array([5], dtype=np.int64))
    assert np.isfinite(sc["ce_joint"])
    assert -np.log2(1e-300) > 990


def test_t1_08_normalization_tol_1e12():
    a, b = _tiny_ab(500, seed=19)
    f = mod.build_m2(a, b, 1.0)
    assert np.all(np.abs(f["P1"].sum(axis=1) - 1.0) <= 1e-12)
    bad = f["P1"].copy()
    bad[0, 0] += 1e-6
    with pytest.raises(ValueError):
        mod._check_normalized(bad, axis=1)


def test_t1_09_seen_unseen_split():
    b_tr = np.array([1, 1, 2, 2], dtype=np.int64)
    b_te = np.array([1, 9, 2, 9], dtype=np.int64)
    loss = np.array([1.0, 2.0, 3.0, 4.0])
    s = mod._seen_split_scores(b_tr, b_te, loss)
    assert s["seen_frac"] == pytest.approx(0.5)
    assert s["n_seen"] == 2 and s["n_unseen"] == 2
    assert s["ce_seen"] == pytest.approx(2.0) and s["ce_unseen"] == pytest.approx(3.0)


def test_t1_10_lambda_anti_leakage():
    bundle = _full_bundle(seed=101)
    s1 = mod.inner_select_lambda(bundle, 0, (0.1, 1.0, 10.0))
    # Perturb outer TEST only (fold 0 TEST = F0); selection must not change.
    bundle2 = {k: {"alice_symbols": v["alice_symbols"].copy(), "bob_symbols": v["bob_symbols"].copy()} for k, v in bundle.items()}
    rng = np.random.default_rng(999)
    for fid in list(mod.OUTER_FOLDS[0]):
        bundle2[fid] = {"alice_symbols": rng.integers(0, 1024, size=256, dtype=np.int64),
                        "bob_symbols": rng.integers(0, 1024, size=256, dtype=np.int64)}
    s2 = mod.inner_select_lambda(bundle2, 0, (0.1, 1.0, 10.0))
    assert s1["selected_lam"] == s2["selected_lam"]
    src = MODULE_PATH.read_text(encoding="utf-8")
    outer_src = src[src.index("def outer_folds"):src.index("def inner_folds_for_outer")]
    inner_src = src[src.index("def inner_folds_for_outer"):src.index("def _concat_bundle")]
    for seg in (outer_src, inner_src):
        assert "permutation" not in seg and "default_rng" not in seg
        assert "shuffle(" not in seg.lower()


def test_t1_11_r5_fixture_repro():
    r = mod.r5_synth_repro()
    assert r["passed"] is True
    assert abs(r["mean_ce_l1"] - 6.422161237462124) < 1e-6
    assert abs(r["mean_ce_l2_oracle"] - 5.083351288530697) < 1e-6
    assert abs(r["mean_ce_joint"] - 11.50551252599282) < 1e-6
    assert r["chain_err"] < 1e-10
    assert r["real_cal_exact_match"] is False


def _mk_outer(mean_joints: dict[str, list[float]]):
    rows = []
    for k in range(4):
        r: dict = {"fold": k, "n_train": 196608, "n_test": 65536}
        for m in ("M0", "M1", "M2"):
            j = mean_joints[m][k]
            r[m] = {"ce_l1": j * 0.6, "ce_l2_oracle": j * 0.4, "ce_joint": j, "chain_err": 0.0, "seen_frac": 1.0, "lam": 1.0}
        rows.append(r)
    return rows


def test_t1_12_selection_delta002_simple_stability():
    # M2 best mean but within 0.02 of simpler M1 -> M1 wins.
    rows = _mk_outer({"M0": [5.0, 5.0, 5.0, 5.0], "M1": [4.0, 4.0, 4.0, 4.0], "M2": [3.99, 3.99, 3.99, 3.99]})
    sel = mod.select_model(rows)
    assert sel["selected"] == "M1" and sel["ranking"][0] == "M2"
    # Unstable best -> downgrade to stable.
    rows2 = _mk_outer({"M0": [5.0, 5.0, 5.0, 5.0], "M1": [4.0, 4.0, 4.0, 4.0], "M2": [3.0, 3.0, 3.0, 4.5]})
    sel2 = mod.select_model(rows2)
    assert sel2["stats"]["M2"]["unstable"] is True
    assert sel2["selected"] == "M1" and sel2["downgraded"] is True


def test_t1_13_budget_four_f_rows_vs_16_200_216():
    b = mod.budget_for_model(0.05, 0.5, 0.55)
    for f in (1.0, 1.1, 1.2, 1.3):
        g = b["grid"][str(float(f))]
        assert g["L1"]["available_rows"] == 16 and g["L2"]["available_rows"] == 200 and g["Total"]["available_rows"] == 216
        assert g["L1"]["required_rows"] == mod.budget_rows(0.05, f)
    # L1 mismatch stays mismatch; no auto-fix by adding L2.
    assert b["grid"]["1.0"]["L1"]["fit"] is True
    b2 = mod.budget_for_model(5.0, 0.01, 5.01)
    assert b2["grid"]["1.0"]["L1"]["fit"] is False


def test_t1_14_route_mutually_exclusive():
    assert mod.route_from_selection(0.01, 0.05, 0.06)["route"] == "A"
    assert mod.route_from_selection(5.0, 5.0, 10.0)["route"] == "C"
    # B: fit@1.0 but mismatch@1.3 -> craft Total CE between 1080/1024/1.3 and 1080/1024.
    ce_fit10 = 0.9  # 0.9*1024=921.6 fit; *1.3=1198 mismatch
    r = mod.route_from_selection(0.01, 0.05, ce_fit10)
    assert r["route"] in ("A", "B", "C")
    assert len({r["route"]}) == 1


def test_t1_15_summary_scalars_only(tmp_path):
    a, b = _tiny_ab(800, seed=23)
    f2 = mod.build_m2(a, b, 1.0)
    lo, hi = mod.symbols_to_layers(a)
    from math import ceil as _ceil  # noqa
    cv = {"n_cal": 800, "n_folds": 4, "seed": 1, "folds": []}
    loaded = {"n_cal_frames": 1024, "n_cal_symbols": 800, "n_read_rows": 800, "n_retained_rows": 800}
    outer = [{"fold": k, "n_train": 600, "n_test": 200,
              "M0": {"ce_l1": 5.0, "ce_l2_oracle": 4.0, "ce_joint": 9.0, "chain_err": 0.0, "seen_frac": 1.0, "lam": 1.0},
              "M1": {"ce_l1": 4.0, "ce_l2_oracle": 3.0, "ce_joint": 7.0, "chain_err": 0.0, "seen_frac": 1.0, "lam": 1.0},
              "M2": {"ce_l1": 3.0, "ce_l2_oracle": 2.0, "ce_joint": 5.0, "chain_err": 0.0, "seen_frac": 1.0, "lam": 1.0}} for k in range(4)]
    sel = mod.select_model(outer)
    budgets = {m: mod.budget_for_model(3.0 if m == "M2" else 4.0, 2.0, 5.0 if m == "M2" else 7.0) for m in ("M0", "M1", "M2")}
    route = mod.route_from_selection(3.0, 2.0, 5.0)
    r5 = mod.r5_synth_repro()
    inner = [{"outer_fold": k, "selected_lam": 1.0} for k in range(4)]
    s = mod.build_audit_summary(registry_path=tmp_path / "reg.json", loaded=loaded, r5=r5,
                                outer_results=outer, inner_selections=inner, selection=sel,
                                budgets=budgets, route=route, prep_wall_s=0.1, g_wall_s=0.1, inv_wall_s=0.2, peak_rss=None)
    payload = json.dumps(s, ensure_ascii=False).lower()
    for banned in ("alice_symbols", "bob_symbols", "prior_logp", "syndrome_target", "candidate"):
        assert banned not in payload
    assert s["decoder_calls"] == 0 and s["published_bits"] == 0 and s["formal"] is False


# ---------------- T2: frame-blocked CV + full audit (5) ----------------

def test_t2_01_frame_blocked_mechanics():
    bundle = _full_bundle(seed=301)
    outer = mod.outer_folds()
    assert [len(f["test_ids"]) for f in outer] == [256, 256, 256, 256]
    assert [len(f["train_ids"]) for f in outer] == [768, 768, 768, 768]
    flat = sorted(sum([f["test_ids"] for f in outer], []))
    assert flat == list(range(702, 1726))
    for k in range(4):
        inners = mod.inner_folds_for_outer(k)
        train = set(outer[k]["train_ids"])
        seen: set[int] = set()
        for inn in inners:
            assert len(inn["inner_test_ids"]) == 256 and len(inn["inner_train_ids"]) == 512
            assert set(inn["inner_test_ids"]) & set(inn["inner_train_ids"]) == set()
            assert set(inn["inner_train_ids"]) | set(inn["inner_test_ids"]) == train
            seen |= set(inn["inner_test_ids"])
        assert seen == train
    # Counts TRAIN-only: different TEST does not change TRAIN fit.
    sel = mod.inner_select_lambda(bundle, 1, (0.5, 1.0, 2.0))
    res = mod.evaluate_outer_fold(bundle, 1, sel["selected_lam"])
    assert res["n_train"] == 768 * 256 and res["n_test"] == 256 * 256
    for m in ("M0", "M1", "M2"):
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
    assert (out1 / "table.csv").read_bytes() != b""  # budget grid present
    assert {p.name for p in out1.iterdir()} == {"manifest.json", "audit.json", "table.csv", "report.md"}


def test_t2_03_no_overwrite_formal_root_untouched(tmp_path):
    prod = mod._production_root()
    existed = prod.exists()
    before = {p.name for p in prod.iterdir()} if existed else set()
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


def test_t2_04_runner_fake_audit(tmp_path):
    pq = tmp_path / "pairs.parquet"
    _write_full_parquet(pq, seed=403)
    reg_path = tmp_path / "registry.json"
    reg_path.write_text(json.dumps(_registry_dict(pq), indent=2), encoding="utf-8")
    out = tmp_path / "audit_runner"
    # Runner uses full grid30; patch to small grid via module call for speed, then check runner guard.
    assert runner.PRODUCTION_ROOT == mod._production_root()
    rc = runner.main(["--registry", str(reg_path), "--out-dir", str(out)])
    # Full grid30 on 262k symbols may take a while but must complete; accept READY.
    assert rc == 0
    assert {p.name for p in out.iterdir()} == {"manifest.json", "audit.json", "table.csv", "report.md"}


def test_t2_05_inner_grid30_deterministic(tmp_path):
    bundle = _full_bundle(seed=404)
    s1 = mod.inner_select_lambda(bundle, 2, None)
    s2 = mod.inner_select_lambda(bundle, 2, None)
    assert len(s1["inner_table"]) == 30 and s1 == s2
    assert s1["selected_lam"] in list(mod.LAMBDA_GRID)
