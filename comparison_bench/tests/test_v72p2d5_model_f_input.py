"""V72P2D5 Model-F input — builder/writer/loader + prepare/verify (fake only)."""
from __future__ import annotations

import importlib.util
import inspect
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "comparison_bench" / "src"))
CORE_PATH = (
    ROOT / "comparison_bench" / "src" / "comparison_bench"
    / "formal_ir" / "v72p2d5_model_f_input.py"
)
CLI_PATH = ROOT / "scripts" / "v72p2d5_prepare_model_f_input.py"

_SPEC = importlib.util.spec_from_file_location(
    "v72p2d5_model_f_input", str(CORE_PATH))
assert _SPEC is not None and _SPEC.loader is not None
mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(mod)

_CSPEC = importlib.util.spec_from_file_location(
    "v72p2d5_prepare_model_f_input_cli", str(CLI_PATH))
assert _CSPEC is not None and _CSPEC.loader is not None
cli = importlib.util.module_from_spec(_CSPEC)
_CSPEC.loader.exec_module(cli)

CORE_SRC = CORE_PATH.read_text(encoding="utf-8")


def _snapshot_dir(path):
    p = Path(path)
    if not p.exists():
        return None
    return {q.name: (q.stat().st_size, q.stat().st_mtime_ns)
            for q in p.iterdir() if q.is_file()}


# Frozen formal-root relpaths mirrored from the rate-mother core (which owns
# the P0/G1/G2/G0/G0-recovery/structure constants; this module only defines
# MODEL_F_FORMAL_ROOT). Literals for snapshotting only — never assert absence.
_P0_FORMAL_REL = "workspace/v72p2d5_p0_cost/20260906_r1"
_G1_FORMAL_REL = "workspace/v72p2d5_g1/20260906_r1"
_G2_FORMAL_REL = "workspace/v72p2d5_g2/20260906_r1"
_G0_FORMAL_REL = "workspace/v72p2d5_g0/20260905_r2"
_G0_RECOVERY_FORMAL_REL = "workspace/v72p2d5_g0_recovery/20260906_r1"
_STRUCTURE_FORMAL_REL = "workspace/v72p2d5_structure/20260905_r2"


def _formal_roots():
    return [ROOT / _P0_FORMAL_REL, ROOT / _G1_FORMAL_REL,
            ROOT / _G2_FORMAL_REL, ROOT / _G0_FORMAL_REL,
            ROOT / _G0_RECOVERY_FORMAL_REL,
            ROOT / mod.MODEL_F_FORMAL_ROOT,
            ROOT / _STRUCTURE_FORMAL_REL]


def _snapshot_formal_roots():
    return {str(r): _snapshot_dir(r) for r in _formal_roots()}


def _assert_formal_roots_unchanged(before):
    for key, old in before.items():
        now = _snapshot_dir(key)
        assert now == old, (
            f"formal root touched during test: {key} "
            f"(before={old!r}, after={now!r}); tests must snapshot-and-compare "
            f"formal roots, never assert their absence")


def _valid_full(seed=11):
    rng = np.random.default_rng(seed)
    frames = np.repeat(np.arange(702, 1726, dtype=np.int64), 256)
    alice = rng.integers(0, 1024, size=262144, dtype=np.int64)
    bob = rng.integers(0, 1024, size=262144, dtype=np.int64)
    return alice, bob, frames


def _sparse_full():
    alice = np.zeros(262144, dtype=np.int64)
    bob = np.zeros(262144, dtype=np.int64)
    alice[0] = 1
    bob[0] = 1
    alice[1] = 1023
    bob[1] = 1022
    frames = np.repeat(np.arange(702, 1726, dtype=np.int64), 256)
    return alice, bob, frames


def test_M01_axis_transpose_must_fail(tmp_path):
    alice, bob, frames = _valid_full()
    built_ab = mod.build_model_f_input(alice, bob, frames)
    built_ba = mod.build_model_f_input(bob, alice, frames)
    c_ab = built_ab["counts_ab"]
    c_ba = built_ba["counts_ab"]
    assert c_ab.shape == (1024, 1024)
    assert np.array_equal(c_ab.T, c_ba)
    assert not np.array_equal(c_ab, c_ba)
    # axis0-derived p_b differs from axis1-derived; wrong one must fail
    p_wrong = c_ab.sum(axis=1).astype(np.float64) / 262144.0
    assert not np.allclose(built_ab["p_b"], p_wrong)
    with pytest.raises(ValueError):
        mod.write_model_f_input(tmp_path / "wrong", c_ab, p_wrong)


def test_M02_sparse_tiny_sum_marginal():
    alice, bob, frames = _sparse_full()
    built = mod.build_model_f_input(alice, bob, frames)
    c = built["counts_ab"]
    assert c.shape == (1024, 1024)
    assert int(c.sum()) == 262144
    assert c.dtype.kind in ("i", "u")
    pb = built["p_b"]
    assert pb.shape == (1024,)
    assert pb.dtype.kind == "f"
    assert abs(float(pb.sum()) - 1.0) < 1e-8
    expect = c.sum(axis=0).astype(np.float64) / 262144.0
    assert np.allclose(pb, expect, atol=1e-12)


def test_M03_frames_missing_dup_range_non256():
    alice, bob, frames = _valid_full()
    # missing: drop frame 702, duplicate 703 to keep length
    bad = frames.copy()
    bad[0:256] = 703
    with pytest.raises(ValueError):
        mod.build_model_f_input(alice, bob, bad)
    # dup/non-256: one frame 255, another 257 (keep total + frames set ok)
    bad2 = frames.copy()
    # move one row from frame 702 to 703: frame 702 now 255, 703 now 257
    idx_702 = np.flatnonzero(bad2 == 702)[0]
    bad2[idx_702] = 703
    with pytest.raises(ValueError):
        mod.build_model_f_input(alice, bob, bad2)
    # out-of-range frame
    bad3 = frames.copy()
    bad3[0] = 701
    with pytest.raises(ValueError):
        mod.build_model_f_input(alice, bob, bad3)
    bad4 = frames.copy()
    bad4[0] = 1726
    with pytest.raises(ValueError):
        mod.build_model_f_input(alice, bob, bad4)


def test_M04_len_mismatch():
    alice, bob, frames = _valid_full()
    with pytest.raises(ValueError):
        mod.build_model_f_input(alice[:100], bob, frames)
    with pytest.raises(ValueError):
        mod.build_model_f_input(alice, bob[:100], frames)
    with pytest.raises(ValueError):
        mod.build_model_f_input(alice, bob, frames[:100])


def test_M05_nonint_nan_neg_overflow():
    alice, bob, frames = _valid_full()
    bad = alice.astype(np.float64)
    bad[0] = 1.5
    with pytest.raises(ValueError):
        mod.build_model_f_input(bad, bob, frames)
    bad2 = alice.astype(np.float64)
    bad2[0] = float("nan")
    with pytest.raises(ValueError):
        mod.build_model_f_input(bad2, bob, frames)
    bad3 = alice.copy()
    bad3[0] = -1
    with pytest.raises(ValueError):
        mod.build_model_f_input(bad3, bob, frames)
    bad4 = alice.copy()
    bad4[0] = 1024
    with pytest.raises(ValueError):
        mod.build_model_f_input(bad4, bob, frames)
    with pytest.raises(ValueError):
        mod.build_model_f_input(["a"] * 262144, bob, frames)


def test_M06_pb_derived_not_handfilled():
    params = set(inspect.signature(mod.build_model_f_input).parameters)
    assert "p_b" not in params
    assert "pb" not in params
    alice, bob, frames = _valid_full(seed=12)
    built = mod.build_model_f_input(alice, bob, frames)
    c = built["counts_ab"]
    expect = c.sum(axis=0).astype(np.float64) / 262144.0
    assert np.allclose(built["p_b"], expect, atol=1e-12)
    uniform = np.full(1024, 1.0 / 1024)
    if not np.allclose(uniform, expect):
        with pytest.raises(ValueError):
            mod.write_model_f_input(Path("/tmp/never_created_m06"), c, uniform)
    with pytest.raises(TypeError):
        mod.build_model_f_input(alice, bob, frames, p_b=uniform)  # type: ignore[call-arg]


def test_M07_exactly_two_files(tmp_path):
    alice, bob, frames = _valid_full()
    built = mod.build_model_f_input(alice, bob, frames)
    out = tmp_path / "m07"
    mod.write_model_f_input(out, built["counts_ab"], built["p_b"])
    names = sorted(p.name for p in out.iterdir())
    assert names == ["model_f_input.npz", "model_f_input_summary.json"]


def test_M08_second_write_refuses_first_unchanged(tmp_path):
    alice, bob, frames = _valid_full()
    built = mod.build_model_f_input(alice, bob, frames)
    out = tmp_path / "m08"
    mod.write_model_f_input(out, built["counts_ab"], built["p_b"])
    before = {p.name: (p.stat().st_size, p.stat().st_mtime_ns) for p in out.iterdir()}
    before_bytes = {p.name: p.read_bytes() for p in out.iterdir()}
    with pytest.raises(FileExistsError):
        mod.write_model_f_input(out, built["counts_ab"], built["p_b"])
    after = {p.name: (p.stat().st_size, p.stat().st_mtime_ns) for p in out.iterdir()}
    assert before == after
    for name, data in before_bytes.items():
        assert (out / name).read_bytes() == data


def test_M09_keys_exactly_two(tmp_path):
    alice, bob, frames = _valid_full()
    built = mod.build_model_f_input(alice, bob, frames)
    out = tmp_path / "m09"
    mod.write_model_f_input(out, built["counts_ab"], built["p_b"])
    data = np.load(str(out / "model_f_input.npz"), allow_pickle=False)
    assert set(str(k) for k in data.files) == {"counts_ab", "p_b"}
    # extra key must fail on load
    out2 = tmp_path / "m09_extra"
    out2.mkdir()
    np.savez_compressed(
        str(out2 / "model_f_input.npz"),
        counts_ab=built["counts_ab"], p_b=built["p_b"],
        extra=np.zeros(3),
    )
    (out2 / "model_f_input_summary.json").write_text(
        (out / "model_f_input_summary.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        mod.load_model_f_input(out2)
    # extra file in dir must fail
    (out / "extra.txt").write_text("x", encoding="utf-8")
    with pytest.raises(ValueError):
        mod.load_model_f_input(out)


def test_M10_no_object_pickle(tmp_path):
    alice, bob, frames = _valid_full()
    built = mod.build_model_f_input(alice, bob, frames)
    out = tmp_path / "m10"
    mod.write_model_f_input(out, built["counts_ab"], built["p_b"])
    data = np.load(str(out / "model_f_input.npz"), allow_pickle=False)
    for key in data.files:
        assert np.asarray(data[key]).dtype.kind != "O"
    # object payload must be rejected
    out2 = tmp_path / "m10_obj"
    out2.mkdir()
    obj = np.empty(3, dtype=object)
    obj[:] = [1, 2, 3]
    np.savez(str(out2 / "model_f_input.npz"),
             counts_ab=obj, p_b=built["p_b"])
    (out2 / "model_f_input_summary.json").write_text(
        (out / "model_f_input_summary.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        mod.load_model_f_input(out2)
    low = CORE_SRC.lower()
    assert "allow_pickle=false" in low.replace(" ", "")


def test_M11_summary_frozen(tmp_path):
    alice, bob, frames = _valid_full()
    built = mod.build_model_f_input(alice, bob, frames)
    out = tmp_path / "m11"
    mod.write_model_f_input(out, built["counts_ab"], built["p_b"])
    summary = json.loads(
        (out / "model_f_input_summary.json").read_text(encoding="utf-8"))
    assert summary["schema"] == "v72p2d5_model_f_input_v1"
    assert summary["cycle"] == "V72P2D5-GF32-RATE-MOTHER"
    assert summary["session"] == "20260123_1M_600k_0dB"
    assert summary["source"] == "1M"
    assert (summary["cal_start"], summary["cal_end"]) == (702, 1725)
    assert summary["n_frames"] == 1024
    assert summary["pairs_per_frame"] == 256
    assert summary["n_symbols"] == 262144
    assert summary["axis"] == ["Alice", "Bob"]
    assert summary["dims"] == [1024, 1024]
    assert summary["mapping"] == "symbol=low+32*high;high=U1;low=U2"
    assert summary["field"] == {"q": 32, "poly": 37}
    assert summary["lambda_star"] == 137.3823795883264
    assert summary["selection"] == "D4R2 nested-CV refit"
    assert summary["cal_only"] is True
    assert summary["val_rows_read"] == 0
    assert summary["decoder_calls"] == 0
    assert summary["p0_calls"] == 0
    assert summary["formal"] is False
    assert summary["status"] == "MODEL_F_INPUT_CANDIDATE"
    assert summary["artifact_files"] == [
        "model_f_input.npz", "model_f_input_summary.json"]
    loaded = mod.load_model_f_input(out)
    assert loaded["summary"] == summary


def test_M12_shape_err(tmp_path):
    alice, bob, frames = _valid_full()
    built = mod.build_model_f_input(alice, bob, frames)
    bad_counts = np.zeros((1023, 1024), dtype=np.int64)
    with pytest.raises(ValueError):
        mod.write_model_f_input(tmp_path / "s12a", bad_counts, built["p_b"])
    bad_pb = np.zeros(1023)
    with pytest.raises(ValueError):
        mod.write_model_f_input(tmp_path / "s12b", built["counts_ab"], bad_pb)


def test_M13_sum_err(tmp_path):
    alice, bob, frames = _valid_full()
    built = mod.build_model_f_input(alice, bob, frames)
    bad = built["counts_ab"].copy()
    bad[0, 0] = int(bad[0, 0]) - 1
    with pytest.raises(ValueError):
        mod.write_model_f_input(tmp_path / "s13", bad, built["p_b"])
    # loader sum err via tampered file
    out = tmp_path / "s13_load"
    mod.write_model_f_input(out, built["counts_ab"], built["p_b"])
    data = dict(np.load(str(out / "model_f_input.npz"), allow_pickle=False))
    tampered = np.asarray(data["counts_ab"]).copy()
    tampered[0, 0] = int(tampered[0, 0]) - 1
    # recompute p_b for tampered? keep old p_b so sum fails first
    np.savez_compressed(str(out / "model_f_input.npz"),
                        counts_ab=tampered, p_b=np.asarray(data["p_b"]))
    with pytest.raises(ValueError):
        mod.load_model_f_input(out)


def test_M14_marginal_err(tmp_path):
    alice, bob, frames = _valid_full()
    built = mod.build_model_f_input(alice, bob, frames)
    bad_pb = built["p_b"].copy()
    bad_pb[0] += 0.01
    bad_pb = bad_pb / bad_pb.sum()
    with pytest.raises(ValueError):
        mod.write_model_f_input(tmp_path / "s14", built["counts_ab"], bad_pb)


def test_M15_lambda_session_cal_err(tmp_path):
    alice, bob, frames = _valid_full()
    built = mod.build_model_f_input(alice, bob, frames)
    out = tmp_path / "s15"
    mod.write_model_f_input(out, built["counts_ab"], built["p_b"])
    summary_path = out / "model_f_input_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    for key, val in (("lambda_star", 1.0), ("session", "bad"),
                     ("cal_start", 700), ("cal_end", 1700),
                     ("n_symbols", 100)):
        tampered = dict(summary)
        tampered[key] = val
        summary_path.write_text(json.dumps(tampered, indent=2), encoding="utf-8")
        with pytest.raises(ValueError):
            mod.load_model_f_input(out)
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    assert mod.load_model_f_input(out)["summary"] == summary


def test_M16_prepare_unauthorized_zeros(tmp_path, monkeypatch):
    calls = {"loader": 0, "mkdir": 0}

    def _boom_loader(*a, **k):
        calls["loader"] += 1
        raise AssertionError("loader entered while unauthorized")

    orig_mkdir = Path.mkdir

    def _boom_mkdir(self, *a, **k):
        calls["mkdir"] += 1
        return orig_mkdir(self, *a, **k)

    monkeypatch.setattr(cli, "_load_cal_arrays", _boom_loader)
    monkeypatch.setattr(Path, "mkdir", _boom_mkdir)
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "reg.json"
    reg.write_text("{}", encoding="utf-8")
    out = tmp_path / "should_not_exist"
    rc = cli.main(["--phase", "prepare", "--registry", str(reg),
                   "--out-dir", str(out)])
    assert rc == 3
    assert calls == {"loader": 0, "mkdir": 0}
    assert not out.exists()
    assert list(tmp_path.rglob("model_f_input.npz")) == []
    rc2 = cli.main(["--phase", "verify", "--registry", str(reg),
                    "--out-dir", str(tmp_path / "nope")])
    assert rc2 == 3


def test_M17_authorized_fake_loader(tmp_path, monkeypatch):
    alice, bob, frames = _valid_full(seed=21)

    def _fake(_reg):
        return alice, bob, frames

    monkeypatch.setattr(cli, "_load_cal_arrays", _fake)
    reg = tmp_path / "fake_reg.json"
    reg.write_text("{}", encoding="utf-8")
    out = tmp_path / "m17"
    rc = cli.main(["--phase", "prepare", "--registry", str(reg),
                   "--out-dir", str(out), "--execution-authorized"])
    assert rc == 0
    assert sorted(p.name for p in out.iterdir()) == [
        "model_f_input.npz", "model_f_input_summary.json"]
    summary = json.loads(
        (out / "model_f_input_summary.json").read_text(encoding="utf-8"))
    assert summary["val_rows_read"] == 0
    assert summary["decoder_calls"] == 0
    assert summary["p0_calls"] == 0
    assert summary["status"] == "MODEL_F_INPUT_CANDIDATE"
    loaded = mod.load_model_f_input(out)
    assert int(loaded["counts_ab"].sum()) == 262144


def test_M18_verify_readonly(tmp_path, monkeypatch):
    alice, bob, frames = _valid_full(seed=22)
    built = mod.build_model_f_input(alice, bob, frames)
    out = tmp_path / "m18"
    mod.write_model_f_input(out, built["counts_ab"], built["p_b"])
    before = {p.name: p.read_bytes() for p in out.iterdir()}

    def _boom_loader(*a, **k):
        raise AssertionError("verify must not load parquet")

    monkeypatch.setattr(cli, "_load_cal_arrays", _boom_loader)
    reg = tmp_path / "reg.json"
    reg.write_text("{}", encoding="utf-8")
    rc = cli.main(["--phase", "verify", "--registry", str(reg),
                   "--out-dir", str(out), "--execution-authorized"])
    assert rc == 0
    after = {p.name: p.read_bytes() for p in out.iterdir()}
    assert before == after
    res = cli.run_verify(out_dir=out)
    assert res["phase"] == "verify"
    assert res["n_symbols"] == 262144


def test_M24_formal_roots_absent(tmp_path, monkeypatch):
    # Lifecycle-aware invariance: this test touches no formal root.
    # Absent-at-start + absent-at-end passes; present-at-start + identical
    # passes; creation/deletion/modification fails loudly (no validity
    # claim, INVALID_UNAUTHORIZED_TEST_TRIGGERED).
    monkeypatch.chdir(tmp_path)
    formal_before = _snapshot_formal_roots()
    assert list(tmp_path.rglob("model_f_input.npz")) == []
    _assert_formal_roots_unchanged(formal_before)


FROZEN_REL = "comparison_bench/outputs_comparison/v55_intake_20260828/pairs/20260123_1M_600k_0dB/pairs.parquet"


def test_P01_root_relative_resolves_no_row_read():
    src = inspect.getsource(cli._resolve_parquet_path)
    assert "read_parquet" not in src
    assert "pandas" not in src
    resolved = cli._resolve_parquet_path(FROZEN_REL)
    expected = (ROOT / FROZEN_REL).resolve()
    assert resolved == expected
    assert resolved.exists()
    assert resolved.is_file()


def test_P02_relative_registry_invocation_correct():
    reg_rel = Path("workspace/v72p2d3_real_registry_20260904.json")
    resolved = cli._resolve_parquet_path(FROZEN_REL)
    expected = (ROOT / FROZEN_REL).resolve()
    assert resolved == expected
    assert resolved.exists()
    assert resolved.is_file()
    wrong = ((ROOT / str(reg_rel)).parent / FROZEN_REL).resolve()
    assert wrong != resolved
    assert not wrong.exists()


def test_P03_absolute_registry_same():
    reg_abs = ROOT / "workspace/v72p2d3_real_registry_20260904.json"
    resolved = cli._resolve_parquet_path(FROZEN_REL)
    expected = (ROOT / FROZEN_REL).resolve()
    assert resolved == expected
    assert resolved.exists()
    wrong = (reg_abs.parent / FROZEN_REL).resolve()
    assert wrong != resolved
    assert not wrong.exists()
    assert resolved == cli._resolve_parquet_path(FROZEN_REL)


def test_P04_cwd_tmp_same(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    resolved = cli._resolve_parquet_path(FROZEN_REL)
    expected = (ROOT / FROZEN_REL).resolve()
    assert resolved == expected
    assert resolved.exists()
    assert resolved.is_file()


def test_P05_absolute_direct(tmp_path):
    fake = tmp_path / "abs.parquet"
    fake.write_bytes(b"fake")
    resolved = cli._resolve_parquet_path(str(fake.resolve()))
    assert resolved == fake.resolve()
    assert resolved.is_file()
    frozen_abs = str((ROOT / FROZEN_REL).resolve())
    resolved2 = cli._resolve_parquet_path(frozen_abs)
    assert resolved2 == (ROOT / FROZEN_REL).resolve()
    assert resolved2.is_file()


def test_P06_empty_rejects(tmp_path):
    with pytest.raises(ValueError):
        cli._resolve_parquet_path("")
    with pytest.raises(ValueError):
        cli._resolve_parquet_path("   ")
    with pytest.raises(ValueError):
        cli._resolve_parquet_path(None)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        cli._resolve_parquet_path(123)  # type: ignore[arg-type]
    assert list(tmp_path.rglob("model_f_input.npz")) == []


def test_P07_nonexistent_fails_before_read(tmp_path, monkeypatch):
    import pandas as pd

    calls = {"read": 0, "mkdir": 0}
    orig_read = pd.read_parquet
    orig_mkdir = Path.mkdir

    def _count_read(*a, **k):
        calls["read"] += 1
        return orig_read(*a, **k)

    def _count_mkdir(self, *a, **k):
        calls["mkdir"] += 1
        return orig_mkdir(self, *a, **k)

    monkeypatch.setattr(pd, "read_parquet", _count_read)
    monkeypatch.setattr(Path, "mkdir", _count_mkdir)
    bad_rel = "comparison_bench/outputs_comparison/v55_intake_20260828/pairs/20260123_1M_600k_0dB/nonexistent_xyz.parquet"
    assert not (ROOT / bad_rel).exists()
    with pytest.raises(FileNotFoundError):
        cli._resolve_parquet_path(bad_rel)
    reg = tmp_path / "bad_reg.json"
    reg.write_text(json.dumps({
        "schema": "v72p2d3_real_registry_v1",
        "session_id": "20260123_1M_600k_0dB",
        "cal_frame_ids": list(range(702, 1726)),
        "val_frame_ids": [1726, 1727, 1728, 1729],
        "parquet_path": bad_rel,
    }), encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        cli._load_cal_arrays(str(reg))
    out = tmp_path / "should_not_exist_p07"
    with pytest.raises(FileNotFoundError):
        cli.run_prepare(registry_path=str(reg), out_dir=str(out))
    assert calls == {"read": 0, "mkdir": 0}
    assert not out.exists()
    assert list(tmp_path.rglob("model_f_input.npz")) == []


def test_P08_no_registry_parent_join():
    cli_src = CLI_PATH.read_text(encoding="utf-8")
    assert "(Path(registry_path).parent" not in cli_src
    rsrc = inspect.getsource(cli._resolve_parquet_path)
    assert "registry_path" not in rsrc
    assert "getcwd" not in rsrc
    assert "chdir" not in rsrc
    reg_abs = ROOT / "workspace/v72p2d3_real_registry_20260904.json"
    wrong = (reg_abs.parent / FROZEN_REL).resolve()
    assert not wrong.exists()
    assert not wrong.is_file()
    resolved = cli._resolve_parquet_path(FROZEN_REL)
    assert resolved.exists()
    assert resolved.is_file()
    assert resolved != wrong


def test_P09_authorized_fake_loader_still_pass(tmp_path, monkeypatch):
    alice, bob, frames = _valid_full(seed=31)

    def _fake(_reg):
        return alice, bob, frames

    monkeypatch.setattr(cli, "_load_cal_arrays", _fake)
    reg = tmp_path / "fake_reg.json"
    reg.write_text("{}", encoding="utf-8")
    out = tmp_path / "p09"
    rc = cli.main(["--phase", "prepare", "--registry", str(reg),
                   "--out-dir", str(out), "--execution-authorized"])
    assert rc == 0
    assert sorted(p.name for p in out.iterdir()) == [
        "model_f_input.npz", "model_f_input_summary.json"]
    loaded = mod.load_model_f_input(out)
    assert int(loaded["counts_ab"].sum()) == 262144


def test_P10_unauthorized_before_resolver(tmp_path, monkeypatch):
    calls = {"resolver": 0, "loader": 0, "mkdir": 0}
    orig_resolve = cli._resolve_parquet_path
    orig_loader = cli._load_cal_arrays
    orig_mkdir = Path.mkdir

    def _boom_resolve(*a, **k):
        calls["resolver"] += 1
        return orig_resolve(*a, **k)

    def _boom_loader(*a, **k):
        calls["loader"] += 1
        return orig_loader(*a, **k)

    def _boom_mkdir(self, *a, **k):
        calls["mkdir"] += 1
        return orig_mkdir(self, *a, **k)

    monkeypatch.setattr(cli, "_resolve_parquet_path", _boom_resolve)
    monkeypatch.setattr(cli, "_load_cal_arrays", _boom_loader)
    monkeypatch.setattr(Path, "mkdir", _boom_mkdir)
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "reg.json"
    reg.write_text("{}", encoding="utf-8")
    out = tmp_path / "should_not_exist_p10"
    rc = cli.main(["--phase", "prepare", "--registry", str(reg),
                   "--out-dir", str(out)])
    assert rc == 3
    rc2 = cli.main(["--phase", "verify", "--registry", str(reg),
                    "--out-dir", str(tmp_path / "nope")])
    assert rc2 == 3
    assert calls == {"resolver": 0, "loader": 0, "mkdir": 0}
    assert not out.exists()
    assert list(tmp_path.rglob("model_f_input.npz")) == []


def test_P11_verify_unaffected(tmp_path, monkeypatch):
    alice, bob, frames = _valid_full(seed=32)
    built = mod.build_model_f_input(alice, bob, frames)
    out = tmp_path / "p11"
    mod.write_model_f_input(out, built["counts_ab"], built["p_b"])
    before = {p.name: p.read_bytes() for p in out.iterdir()}

    def _boom_resolve(*a, **k):
        raise AssertionError("verify must not resolve parquet")

    def _boom_loader(*a, **k):
        raise AssertionError("verify must not load parquet")

    monkeypatch.setattr(cli, "_resolve_parquet_path", _boom_resolve)
    monkeypatch.setattr(cli, "_load_cal_arrays", _boom_loader)
    reg = tmp_path / "reg.json"
    reg.write_text("{}", encoding="utf-8")
    rc = cli.main(["--phase", "verify", "--registry", str(reg),
                   "--out-dir", str(out), "--execution-authorized"])
    assert rc == 0
    after = {p.name: p.read_bytes() for p in out.iterdir()}
    assert before == after


def test_P12_formal_roots_absent(tmp_path, monkeypatch):
    # Lifecycle-aware invariance (see M24): prove no formal root touched,
    # no absence assert (legitimate artifacts may exist).
    monkeypatch.chdir(tmp_path)
    formal_before = _snapshot_formal_roots()
    assert list(tmp_path.rglob("model_f_input.npz")) == []
    _assert_formal_roots_unchanged(formal_before)
