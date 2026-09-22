"""V72P2D4 CAL GF32 model rate audit — T0/T1/T2 qualification, CAL-only."""
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
MODULE_PATH = ROOT / "src" / "comparison_bench" / "formal_ir" / "v72p2d4_cal_gf32_model_rate_audit.py"
RUNNER_PATH = ROOT.parent / "scripts" / "v72p2d4_cal_gf32_model_rate_audit.py"

SPEC = importlib.util.spec_from_file_location("v72p2d4_audit_test_module", str(MODULE_PATH))
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

RSPEC = importlib.util.spec_from_file_location("v72p2d4_runner_test_module", str(RUNNER_PATH))
assert RSPEC is not None and RSPEC.loader is not None
runner = importlib.util.module_from_spec(RSPEC)
RSPEC.loader.exec_module(runner)


def _tiny_cal(n: int = 2000, seed: int = 20260905):
    rng = np.random.default_rng(seed)
    a = rng.integers(0, 1024, size=n, dtype=np.int64)
    b = rng.integers(0, 1024, size=n, dtype=np.int64)
    return a, b


def _write_full_parquet(parquet_path: Path, seed: int = 20260905):
    import pandas as pd

    rng = np.random.default_rng(seed)
    fids = list(range(702, 1726)) + [1726, 1727, 1728, 1729]
    n = len(fids) * 256
    frame_ids = np.repeat(np.array(fids, dtype=np.int64), 256)
    pair_idx = np.tile(np.arange(256, dtype=np.int64), len(fids))
    alice = rng.integers(0, 1024, size=n, dtype=np.int64)
    bob = rng.integers(0, 1024, size=n, dtype=np.int64)
    df = pd.DataFrame(
        {
            "frame_id": frame_ids,
            "pair_idx": pair_idx,
            "alice_symbol": alice,
            "bob_symbol": bob,
        }
    )
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
    assert mod.CYCLE_ID == "V72P2D4-CAL-GF32-MODEL-RATE"
    assert mod.AUDIT_SCHEMA == "v72p2d4_cal_gf32_model_rate_audit_v1"
    assert mod.REGISTRY_SCHEMA == "v72p2d3_real_registry_v1"
    assert mod.DEFAULT_LAM == 1.0
    assert mod.CV_SEED == 20260905 and mod.N_FOLDS == 4
    assert mod.R5_H1_BITS == 80 and mod.R5_L2_TOTAL_BITS == 1000
    assert mod.R5_TOTAL_BITS == 1080 and mod.R5_RATE == pytest.approx(1080.0 / 1024.0)
    assert mod.PREP_LIMIT_S == 300.0 and mod.G_LIMIT_S == 300.0
    assert mod.INV_LIMIT_S == 600.0 and mod.RSS_LIMIT_BYTES == 2 * 1024**3
    assert mod.OUT_DIR_NAME == "v72p2d4_cal_gf32_model_rate_audit_20260905"


def test_t0_02_reuse_bindings_no_reimplementation():
    for name in (
        "symbols_to_layers", "build_stage1_P", "build_stage2_P",
        "ce_stage1_log2", "ce_stage2_log2", "ce_joint_log2",
        "cal_resubstitution_nll_descriptive", "cal_4fold_cv_heldout_nll",
        "rate_audit_r5", "build_canonical_counts", "validate_prepare_registry",
    ):
        assert callable(getattr(mod, name)), name
    src = MODULE_PATH.read_text(encoding="utf-8")
    for name in (
        "def build_stage1_P", "def build_stage2_P", "def ce_stage1_log2",
        "def cal_resubstitution_nll", "def cal_4fold_cv", "def rate_audit_r5",
        "def validate_prepare_registry", "def symbols_to_layers",
        "def build_canonical_counts",
    ):
        assert name not in src


def test_t0_03_no_decoder_attrs_or_params():
    for attr in ("history_decode", "run_g_layer", "run_l1_stage", "run_l2_incremental"):
        assert not hasattr(mod, attr), attr
    params = set(inspect.signature(mod.run_cal_audit).parameters)
    assert {"registry_path", "out_dir", "lam"} <= params
    for forbidden in ("decode_fn", "execute_real", "authorized", "preflight", "frames", "matrices", "val_ids", "val_frames"):
        assert forbidden not in params
    fit_params = set(inspect.signature(mod.fit_cal_model).parameters)
    for forbidden in ("decode_fn", "execute_real", "val_ids", "val_frames"):
        assert forbidden not in fit_params
    load_params = set(inspect.signature(mod.load_cal_arrays).parameters)
    for forbidden in ("decode_fn", "execute_real", "val_frames"):
        assert forbidden not in load_params


def test_t0_04_cli_no_forbidden_options():
    parser = runner.build_parser()
    dests = {a.dest for a in parser._actions}
    assert {"registry", "out_dir", "lam"} <= dests
    for forbidden in ("execute_real", "prepare_only", "phase", "seed", "val", "val_frames", "authorized", "decode"):
        assert forbidden not in dests
    opt_strings: list[str] = []
    for a in parser._actions:
        opt_strings.extend(a.option_strings)
    assert "--execute-real" not in opt_strings
    assert "--prepare-only" not in opt_strings
    assert "--phase" not in opt_strings
    assert not any(s.startswith("--val") for s in opt_strings)
    rsrc = RUNNER_PATH.read_text(encoding="utf-8")
    assert "--execute-real" not in rsrc
    assert "read_parquet" not in rsrc
    assert "import pandas" not in rsrc


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
    assert counts.shape == (1024, 1024)
    assert float(counts.sum()) == 4.0
    assert counts[0, 0] == 1.0 and counts[1023, 1] == 1.0
    with pytest.raises(ValueError):
        mod.build_canonical_counts(np.array([], dtype=np.int64), np.array([], dtype=np.int64))


def test_t0_07_ce_chain_identity_tiny():
    rng = np.random.default_rng(20260905)
    b_cal = rng.integers(0, 8, size=300, dtype=np.int64)
    h_cal = rng.integers(0, 4, size=300, dtype=np.int64)
    l_cal = rng.integers(0, 4, size=300, dtype=np.int64)
    p1 = mod.build_stage1_P(b_cal, h_cal, 1.0, n_b_states=8, q_sub=4)
    p2 = mod.build_stage2_P(h_cal, b_cal, l_cal, 1.0, n_b_states=8, q_sub=4)
    b_ev = rng.integers(0, 8, size=60, dtype=np.int64)
    h_ev = rng.integers(0, 4, size=60, dtype=np.int64)
    l_ev = rng.integers(0, 4, size=60, dtype=np.int64)
    c1 = mod.ce_stage1_log2(p1, b_ev, h_ev)
    c2 = mod.ce_stage2_log2(p2, h_ev, b_ev, l_ev)
    cj = mod.ce_joint_log2(p1, p2, b_ev, h_ev, l_ev)
    assert np.isfinite(c1) and np.isfinite(c2) and np.isfinite(cj)
    assert cj == pytest.approx(c1 + c2)


def test_t0_08_rate_budget_math():
    rate = mod.rate_audit_r5(1.0, 2.0, 3.0)
    assert rate["n"] == 1024
    assert rate["budget"] == {"h1_bits": 80, "l2_total_bits": 1000, "total_bits": 1080, "rate_bit_per_symbol": pytest.approx(1080.0 / 1024.0)}
    assert rate["layers"]["l1"]["required_bits"] == pytest.approx(1024.0)
    assert rate["layers"]["joint"]["available_bits"] == 1080
    assert rate["status"] == "MODEL_BUDGET_MISMATCH"
    ok = mod.rate_audit_r5(0.01, 0.05, 0.06)
    assert ok["status"] == "WITHIN_BUDGET"
    assert "descriptive" in ok["note"]


def test_t0_09_output_guard_basics(tmp_path):
    fresh = tmp_path / "audit_fresh"
    assert mod.validate_output_target(fresh) == fresh.resolve()
    with pytest.raises(FileExistsError):
        mod.validate_output_target(tmp_path)
    with pytest.raises(ValueError):
        mod.validate_output_target(tmp_path / "run_01")
    with pytest.raises(ValueError):
        mod.validate_output_target(Path("/definitely_outside_ws_d4_test_xyz") / "x")


def test_t0_10_runner_mirrors_constants():
    assert runner.CYCLE_ID == mod.CYCLE_ID
    assert runner.PREP_LIMIT_S == mod.PREP_LIMIT_S == 300.0
    assert runner.G_LIMIT_S == mod.G_LIMIT_S == 300.0
    assert runner.INV_LIMIT_S == mod.INV_LIMIT_S == 600.0
    assert runner.RSS_LIMIT_BYTES == mod.RSS_LIMIT_BYTES == 2 * 1024**3
    assert runner.DEFAULT_LAM == mod.DEFAULT_LAM == 1.0
    assert runner.WORKSPACE_ROOT == mod._workspace_root()
    assert runner.PRODUCTION_ROOT == mod._production_root()
    rsrc = RUNNER_PATH.read_text(encoding="utf-8").lower()
    assert "mock" not in rsrc and "stub" not in rsrc


# ---------------- T1: focused unit + tamper (15) ----------------

def test_t1_01_registry_contract(tmp_path):
    pq = tmp_path / "p.parquet"
    pq.write_bytes(b"dummy")
    reg = _registry_dict(pq)
    out = mod.validate_prepare_registry(reg, tmp_path / "reg.json")
    assert out["cal_ids"] == list(range(702, 1726))
    assert out["val_ids"] == [1726, 1727, 1728, 1729]
    for key, val in (("schema", "wrong"), ("session_id", "bad"), ("source_label", "2M")):
        bad = dict(reg)
        bad[key] = val
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
    extra = dict(reg)
    extra["sha256"] = "deadbeef"
    assert mod.validate_prepare_registry(extra, tmp_path / "reg.json")["session_id"] == mod.SESSION_ID


def test_t1_02_loader_and_fit_reject_bad_inputs(tmp_path):
    with pytest.raises(ValueError):
        mod.load_cal_arrays(tmp_path / "missing.parquet")
    with pytest.raises(ValueError):
        mod.load_cal_arrays(tmp_path / "missing.parquet", cal_ids=list(range(700, 1724)))
    import pandas as pd

    tiny = tmp_path / "tiny.parquet"
    pd.DataFrame({"a": [1, 2], "b": [3, 4]}).to_parquet(tiny, index=False)
    with pytest.raises(ValueError):
        mod.load_cal_arrays(tiny)
    tiny2 = tmp_path / "tiny2.parquet"
    pd.DataFrame(
        {
            "frame_id": [702, 702],
            "pair_idx": [0, 1],
            "alice_symbol": [0, 1],
            "bob_symbol": [0, 1],
        }
    ).to_parquet(tiny2, index=False)
    with pytest.raises(ValueError):
        mod.load_cal_arrays(tiny2)
    a, b = _tiny_cal(100)
    with pytest.raises(ValueError):
        mod.fit_cal_model(a[:50], b, 1.0)
    with pytest.raises(ValueError):
        mod.fit_cal_model(np.array([], dtype=np.int64), np.array([], dtype=np.int64), 1.0)
    bad = a.copy()
    bad[0] = 1024
    with pytest.raises(ValueError):
        mod.fit_cal_model(bad, b, 1.0)
    with pytest.raises(ValueError):
        mod.fit_cal_model(a, b, 0.0)
    with pytest.raises(ValueError):
        mod.fit_cal_model(a, b, -1.0)


def test_t1_03_p1_normalized():
    a, b = _tiny_cal()
    fit = mod.fit_cal_model(a, b, 1.0)
    p1 = fit["P1"]
    assert p1.shape == (1024, 32)
    assert np.all(np.isfinite(p1)) and np.all(p1 > 0)
    assert np.allclose(p1.sum(axis=1), 1.0)


def test_t1_04_p2_normalized():
    a, b = _tiny_cal()
    fit = mod.fit_cal_model(a, b, 1.0)
    p2 = fit["P2"]
    assert p2.shape == (32, 1024, 32)
    assert np.all(np.isfinite(p2)) and np.all(p2 > 0)
    assert np.allclose(p2.sum(axis=2), 1.0)


def test_t1_05_resub_joint_equals_sum():
    a, b = _tiny_cal()
    fit = mod.fit_cal_model(a, b, 1.0)
    a_low, a_high = mod.symbols_to_layers(a)
    resub = mod.cal_resubstitution_nll_descriptive(fit["P1"], fit["P2"], b, a_high, a_low)
    assert resub["n"] == a.size
    assert np.isfinite(resub["ce_l1"]) and np.isfinite(resub["ce_joint"])
    assert resub["ce_joint"] == pytest.approx(resub["ce_l1"] + resub["ce_l2_oracle"])
    assert resub["kind"] == "cal_resubstitution_nll_descriptive"


def test_t1_06_cv_deterministic_coverage():
    a, b = _tiny_cal()
    cv1 = mod.cal_4fold_cv_heldout_nll(a, b, 1.0)
    cv2 = mod.cal_4fold_cv_heldout_nll(a, b, 1.0)
    assert cv1["mean_ce_joint"] == pytest.approx(cv2["mean_ce_joint"])
    assert len(cv1["folds"]) == 4
    total_held = sum(f["n_heldout"] for f in cv1["folds"])
    assert total_held == a.size
    for f in cv1["folds"]:
        assert f["n_train"] + f["n_heldout"] == a.size
    means = sum(f["ce_joint"] for f in cv1["folds"]) / 4
    assert cv1["mean_ce_joint"] == pytest.approx(means)


def test_t1_07_cv_frozen_folds_seed_lam():
    a, b = _tiny_cal(200)
    with pytest.raises(ValueError):
        mod.cal_4fold_cv_heldout_nll(a, b, 1.0, n_folds=5)
    with pytest.raises(ValueError):
        mod.cal_4fold_cv_heldout_nll(a[:3], b[:3], 1.0)
    cv = mod.cal_4fold_cv_heldout_nll(a, b, 1.0)
    assert cv["seed"] == 20260905 and cv["n_folds"] == 4 and cv["lam"] == 1.0


def test_t1_08_rate_branches():
    over = mod.rate_audit_r5(5.0, 5.0, 10.0)
    assert over["status"] == "MODEL_BUDGET_MISMATCH"
    within = mod.rate_audit_r5(0.01, 0.02, 0.03)
    assert within["status"] == "WITHIN_BUDGET"
    for layer, ce, avail in (("l1", 0.01, 80), ("l2_oracle", 0.02, 1000), ("joint", 0.03, 1080)):
        row = within["layers"][layer]
        assert row["required_bits"] == pytest.approx(ce * 1024)
        assert row["available_bits"] == avail
        assert row["margin_bits"] == pytest.approx(avail - ce * 1024)
        assert row["ratio"] == pytest.approx(ce * 1024 / avail)


def test_t1_09_rate_rejects_bad_ce():
    for bad in (-1.0, float("inf"), float("nan")):
        with pytest.raises(ValueError):
            mod.rate_audit_r5(bad, 1.0, 1.0)
        with pytest.raises(ValueError):
            mod.rate_audit_r5(1.0, bad, 1.0)


def test_t1_10_audit_files_schema_tmp(tmp_path):
    a, b = _tiny_cal(1500)
    fit = mod.fit_cal_model(a, b, 1.0)
    a_low, a_high = mod.symbols_to_layers(a)
    resub = mod.cal_resubstitution_nll_descriptive(fit["P1"], fit["P2"], b, a_high, a_low)
    cv = mod.cal_4fold_cv_heldout_nll(a, b, 1.0)
    rate = mod.rate_audit_r5(resub["ce_l1"], resub["ce_l2_oracle"], resub["ce_joint"])
    loaded = {"n_cal_frames": 1024, "n_cal_symbols": int(a.size), "n_read_rows": int(a.size), "n_retained_rows": int(a.size)}
    summary = mod.build_audit_summary(
        registry_path=tmp_path / "reg.json", loaded=loaded, fit=fit,
        resub=resub, cv=cv, rate=rate,
        prep_wall_s=0.1, g_wall_s=0.2, inv_wall_s=0.3, peak_rss=None,
    )
    out = tmp_path / "audit_schema"
    written = mod.write_audit_outputs(out, summary)
    assert {p.name for p in written.iterdir()} == {"manifest.json", "audit.json", "table.csv", "report.md"}
    manifest = json.loads((written / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["cycle"] == mod.CYCLE_ID and manifest["cal_only"] is True
    audit = json.loads((written / "audit.json").read_text(encoding="utf-8"))
    assert audit["decoder_calls"] == 0 and audit["formal"] is False
    with pytest.raises(FileExistsError):
        mod.write_audit_outputs(out, summary)


def test_t1_11_summary_scalars_only(tmp_path):
    a, b = _tiny_cal(800)
    fit = mod.fit_cal_model(a, b, 1.0)
    a_low, a_high = mod.symbols_to_layers(a)
    resub = mod.cal_resubstitution_nll_descriptive(fit["P1"], fit["P2"], b, a_high, a_low)
    cv = mod.cal_4fold_cv_heldout_nll(a, b, 1.0)
    rate = mod.rate_audit_r5(resub["ce_l1"], resub["ce_l2_oracle"], resub["ce_joint"])
    loaded = {"n_cal_frames": 1024, "n_cal_symbols": int(a.size), "n_read_rows": int(a.size), "n_retained_rows": int(a.size)}
    summary = mod.build_audit_summary(
        registry_path=tmp_path / "reg.json", loaded=loaded, fit=fit,
        resub=resub, cv=cv, rate=rate,
        prep_wall_s=0.1, g_wall_s=0.1, inv_wall_s=0.2, peak_rss=None,
    )
    payload = json.dumps(summary, ensure_ascii=False).lower()
    for banned in ("alice_symbols", "bob_symbols", "prior_logp", "syndrome_target", "candidate"):
        assert banned not in payload
    assert '"protocol"' not in payload
    assert summary["decoder_calls"] == 0 and summary["published_bits"] == 0
    bad = dict(summary)
    bad["alice_symbols"] = [1, 2, 3]
    with pytest.raises(ValueError):
        mod._check_summary_allowed(bad)


def test_t1_12_output_guard_prod_vs_workspace(tmp_path):
    prod = mod._production_root()
    if not prod.exists():
        assert mod.validate_output_target(prod) == prod
    with pytest.raises(ValueError):
        mod.validate_output_target(prod / "child")
    ws_fresh = tmp_path / "ws_ok"
    assert mod.validate_output_target(ws_fresh) == ws_fresh.resolve()
    with pytest.raises(ValueError):
        mod.validate_output_target(tmp_path / "run_01")


def test_t1_13_cli_missing_registry_fails_closed(tmp_path):
    out = tmp_path / "audit_cli_fail"
    rc = runner.main(["--registry", str(tmp_path / "missing.json"), "--out-dir", str(out)])
    assert rc == 2
    assert not out.exists()
    out2 = tmp_path / "audit_cli_exists"
    out2.mkdir()
    rc2 = runner.main(["--registry", str(tmp_path / "missing.json"), "--out-dir", str(out2)])
    assert rc2 == 2


def test_t1_14_no_val_fit_signature_and_source():
    run_params = set(inspect.signature(mod.run_cal_audit).parameters)
    assert not any(p.startswith("val") for p in run_params)
    fit_params = set(inspect.signature(mod.fit_cal_model).parameters)
    assert not any(p.startswith("val") for p in fit_params)
    src = MODULE_PATH.read_text(encoding="utf-8").lower()
    assert "val_bundle" not in src
    assert "val_frame" not in src
    a, b = _tiny_cal(500)
    fit1 = mod.fit_cal_model(a, b, 1.0)
    fit2 = mod.fit_cal_model(a.copy(), b.copy(), 1.0)
    assert np.array_equal(fit1["counts"], fit2["counts"])


def test_t1_15_no_decoder_tag_hash_in_source():
    src = MODULE_PATH.read_text(encoding="utf-8")
    low = src.lower()
    for banned in ("decode_row_layered_fftqspa", "history_decode", "run_g_layer", "warm_beliefs", "compute_tag_64", "hashlib", "sha256", "checksum", "simplified_decoder", "fixed_hard"):
        assert banned.lower() not in low
    assert "mock" not in low and "stub" not in low
    assert mod.SUMMARY_BANNED_KEYS is not None


# ---------------- T2: full CAL audit + strict replay (5) ----------------

def test_t2_01_full_cal_audit_workspace(tmp_path):
    pq = tmp_path / "pairs.parquet"
    _write_full_parquet(pq)
    reg_path = tmp_path / "registry.json"
    reg_path.write_text(json.dumps(_registry_dict(pq), indent=2), encoding="utf-8")
    out = tmp_path / "audit_full"
    report = mod.run_cal_audit(registry_path=reg_path, out_dir=out)
    assert report["status"] == "READY"
    assert report["rate_status"] in ("WITHIN_BUDGET", "MODEL_BUDGET_MISMATCH")
    assert report["n_cal_symbols"] == 262144
    assert report["decoder_calls"] == 0 and report["formal"] is False and report["cal_only"] is True
    assert {p.name for p in out.iterdir()} == {"manifest.json", "audit.json", "table.csv", "report.md"}
    audit = json.loads((out / "audit.json").read_text(encoding="utf-8"))
    assert np.isfinite(audit["resub"]["ce_joint"]) and np.isfinite(audit["cv"]["mean_ce_joint"])
    assert report["prep_wall_s"] <= 300.0 and report["g_wall_s"] <= 300.0 and report["inv_wall_s"] <= 600.0
    assert report["peak_rss_bytes"] is None or report["peak_rss_bytes"] < 2 * 1024**3


def test_t2_02_strict_replay_identical_rate(tmp_path):
    pq = tmp_path / "pairs.parquet"
    _write_full_parquet(pq)
    reg_path = tmp_path / "registry.json"
    reg_path.write_text(json.dumps(_registry_dict(pq), indent=2), encoding="utf-8")
    out1 = tmp_path / "audit_r1"
    out2 = tmp_path / "audit_r2"
    r1 = mod.run_cal_audit(registry_path=reg_path, out_dir=out1)
    r2 = mod.run_cal_audit(registry_path=reg_path, out_dir=out2)
    a1 = json.loads((out1 / "audit.json").read_text(encoding="utf-8"))
    a2 = json.loads((out2 / "audit.json").read_text(encoding="utf-8"))
    for key in ("resub", "cv", "rate", "rows"):
        assert a1[key] == a2[key]
    assert (out1 / "table.csv").read_bytes() == (out2 / "table.csv").read_bytes()
    assert r1["resub_ce_joint"] == pytest.approx(r2["resub_ce_joint"])
    assert r1["cv_mean_ce_joint"] == pytest.approx(r2["cv_mean_ce_joint"])


def test_t2_03_no_overwrite_second_run_fails(tmp_path):
    pq = tmp_path / "pairs.parquet"
    _write_full_parquet(pq)
    reg_path = tmp_path / "registry.json"
    reg_path.write_text(json.dumps(_registry_dict(pq), indent=2), encoding="utf-8")
    out = tmp_path / "audit_once"
    first = mod.run_cal_audit(registry_path=reg_path, out_dir=out)
    assert first["status"] == "READY"
    with pytest.raises(FileExistsError):
        mod.run_cal_audit(registry_path=reg_path, out_dir=out)
    assert {p.name for p in out.iterdir()} == {"manifest.json", "audit.json", "table.csv", "report.md"}


def test_t2_04_formal_root_untouched(tmp_path):
    prod = mod._production_root()
    existed = prod.exists()
    before = {p.name for p in prod.iterdir()} if existed else set()
    pq = tmp_path / "pairs.parquet"
    _write_full_parquet(pq)
    reg_path = tmp_path / "registry.json"
    reg_path.write_text(json.dumps(_registry_dict(pq), indent=2), encoding="utf-8")
    out = tmp_path / "audit_formal_check"
    mod.run_cal_audit(registry_path=reg_path, out_dir=out)
    assert prod.exists() == existed
    if existed:
        assert {p.name for p in prod.iterdir()} == before
    assert out.resolve() != prod.resolve()


def test_t2_05_budgets_decoder_zero_runner(tmp_path):
    pq = tmp_path / "pairs.parquet"
    _write_full_parquet(pq)
    reg_path = tmp_path / "registry.json"
    reg_path.write_text(json.dumps(_registry_dict(pq), indent=2), encoding="utf-8")
    out = tmp_path / "audit_runner"
    report = runner.run_audit(out_dir=out, registry_path=reg_path, lam=1.0)
    assert report["status"] == "READY"
    assert report["prep_wall_s"] <= 300.0 and report["g_wall_s"] <= 300.0 and report["inv_wall_s"] <= 600.0
    assert report["peak_rss_bytes"] is None or report["peak_rss_bytes"] < 2 * 1024**3
    assert report["decoder_calls"] == 0 and report["published_bits"] == 0
    assert "run_01" not in str(Path(report["output"]).resolve()).split("\\")[-2:]
