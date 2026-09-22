"""Fake-only tests for the X1 bundle builder/verifier (T-X1S-3).

FAKE-ONLY: every histogram/bundle here is synthetic and in-test. No ttbin
data path appears in this file; no production decoder/DE/graph call is made;
no frozen module is modified (AGENTS.md §10.1 clause 8). All disk use is in
pytest tmp_path. Run per-file ONLY:
PYTHONPATH=<root> .venv/bin/python -m pytest -p no:cacheprovider -o addopts="" <this file>
"""

from __future__ import annotations

import inspect
import json

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.cli import x1_bundle_build as x
from comparison_bench.src.comparison_bench.formal_ir import (
    v80_s2c_campaign as c,
)


def _synthetic_counts(seed=11, n_pairs=20000):
    """Synthetic joint counts on the full 1024x1024 domain (FAKE ONLY)."""
    rng = np.random.default_rng(seed)
    a = rng.integers(0, 1024, size=n_pairs)
    b = rng.integers(0, 1024, size=n_pairs)
    N = np.zeros((1024, 1024), dtype=np.int64)
    np.add.at(N, (a, b), 1)
    return N


def _write_coo(path, N):
    rows, cols = np.nonzero(N)
    np.savez(str(path), row=rows.astype(np.int64), col=cols.astype(np.int64),
             count=N[rows, cols].astype(np.int64),
             shape=np.array([1024, 1024], dtype=np.int64),
             N_train=np.int64(int(N.sum())))


# (a) COO -> dense -> ChannelAdapter round-trip on synthetic histograms. ------

def test_synthetic_coo_round_trip_keys_shapes_dtypes(tmp_path):
    N = _synthetic_counts()
    p = tmp_path / "T2-9M_N_ab_train_sparse.npz"
    _write_coo(p, N)
    dense, meta = x.load_sparse_coo(p)
    assert dense.shape == (1024, 1024) and dense.dtype == np.int64
    assert np.array_equal(dense, N)
    assert meta["sum"] == meta["N_train"] == int(N.sum())
    assert meta["nnz"] == int(np.count_nonzero(N))
    z = np.load(str(p), allow_pickle=False)
    try:
        assert set(z.files) == {"row", "col", "count", "shape", "N_train"}
        for k in ("row", "col", "count"):
            assert z[k].dtype == np.int64
        assert tuple(int(v) for v in np.asarray(z["shape"]).tolist()) == (1024, 1024)
    finally:
        z.close()


def test_synthetic_factorize_shapes_and_normalization():
    N = _synthetic_counts()
    fac = x.factorize("type2_1M_20260121_184040", N)
    assert fac["g1"].shape == (32, 1024)
    assert fac["g2"].shape == (32, 32, 1024)
    assert fac["p_b"].shape == (1024,)
    assert np.all(np.isfinite(fac["g1"])) and np.all(fac["g1"] >= 0.0)
    assert np.allclose(fac["g1"].sum(axis=0), 1.0, atol=1e-9)
    assert np.all(np.isfinite(fac["g2"])) and np.all(fac["g2"] >= 0.0)
    assert np.allclose(fac["g2"].sum(axis=1), 1.0, atol=1e-9)
    assert abs(float(fac["p_b"].sum()) - 1.0) < 1e-12
    # Built p_b equals COO colsum/N exactly.
    ref = N.sum(axis=0).astype(np.float64) / float(N.sum())
    assert float(np.max(np.abs(fac["p_b"] - ref))) == 0.0
    assert fac["H_L1"] > 0.0 and fac["H_L2"] > 0.0


def test_source_table_read_from_v26_not_invented():
    table = x.source_table()
    assert table == {
        "T2-1M": {"v26_source": "type2_1M_20260121_184040", "prefix": "1M"},
        "T2-1.5M": {"v26_source": "type2_1p5M_20260121_183806", "prefix": "1p5M"},
        "T2-2M": {"v26_source": "type2_2M_20260121_183657", "prefix": "2M"},
    }


# (b) Bind gates: PASS on synthetic bundle; refusal on tamper/label swap. -----

def _synthetic_bundle_files(tmp_path, prefix="1M"):
    N = _synthetic_counts()
    fac = x.factorize("type2_1M_20260121_184040", N)
    main = tmp_path / "x1_gamma_f03r1.npz"
    np.savez(str(main), **{f"{prefix}_gamma1_L1": fac["g1"],
                           f"{prefix}_gamma2_L2condU1": fac["g2"],
                           f"{prefix}_p_b": fac["p_b"]})
    np.savez(str(tmp_path / "gamma_f03_pb.npz"),
             **{f"{prefix}_p_b": np.array(fac["p_b"])})
    return main, fac


def test_bind_pass_and_tamper_refusals(tmp_path):
    main, fac = _synthetic_bundle_files(tmp_path)
    bound = c.bind_empirical_bundle(str(main), "1M")  # frozen gate, path-form
    assert bound["g1"].shape == (32, 1024)
    assert bound["g2"].shape == (32, 32, 1024)
    # Tampered shape refuses (dict form, no disk).
    with pytest.raises(c.Refusal):
        c.bind_empirical_bundle({"g1": np.ones((32, 1000)),
                                 "g2": fac["g2"], "p_b": fac["p_b"]})
    with pytest.raises(c.Refusal):
        c.bind_empirical_bundle({"g1": fac["g1"],
                                 "g2": np.ones((32, 31, 1024)),
                                 "p_b": fac["p_b"]})
    # Tampered normalization refuses.
    with pytest.raises(c.Refusal):
        c.bind_empirical_bundle({"g1": fac["g1"], "g2": fac["g2"],
                                 "p_b": fac["p_b"] * 2.0})
    bad_g1 = np.array(fac["g1"])
    bad_g1[:, 5] = 0.0  # colsum 0 != 1
    with pytest.raises(c.Refusal):
        c.bind_empirical_bundle({"g1": bad_g1, "g2": fac["g2"],
                                 "p_b": fac["p_b"]})


def test_cross_source_label_swap_refuses(tmp_path):
    main, _ = _synthetic_bundle_files(tmp_path, prefix="1M")
    # File carries only 1M keys (+1M sidecar): binding another label refuses.
    with pytest.raises(c.Refusal):
        c.bind_empirical_bundle(str(main), "1p5M")


# (c) Checksum identities on synthetic data. -----------------------------------

def test_checksum_identities_synthetic(tmp_path):
    N = _synthetic_counts()
    js = {"N_train": int(N.sum()), "K_AB_train": int(np.count_nonzero(N)),
          "K_B_train": int((N.sum(axis=0) > 0).sum())}
    chk = x.checksum_record(N, js)
    assert chk["N_ok"] and chk["K_AB_ok"] and chk["K_B_ok"]
    assert chk["K_B_coo"] <= 1024 and chk["K_B_coo"] < chk["K_AB_coo"]
    bad = dict(js, N_train=js["N_train"] + 1)
    assert x.checksum_record(N, bad)["N_ok"] is False


# (d) Root refusal on a pre-existing directory. ---------------------------------

def test_build_refuses_preexisting_root(tmp_path):
    root = tmp_path / "x1_bundles_deadbeef"
    root.mkdir()
    with pytest.raises(SystemExit):
        x.run_build(str(root), str(tmp_path))
    with pytest.raises(SystemExit):
        x.main(["--root", str(root), "--r1-root", str(tmp_path),
                "--mode", "build"])


def test_verify_refuses_absent_root(tmp_path):
    with pytest.raises(SystemExit):
        x.run_verify(str(tmp_path / "nope"), str(tmp_path), str(tmp_path))


# (e) F1 sibling-copy identity. -------------------------------------------------

def test_f1_sibling_copy_identity(tmp_path):
    main, fac = _synthetic_bundle_files(tmp_path)
    zb = np.load(str(main), allow_pickle=False)
    zs = np.load(str(tmp_path / "gamma_f03_pb.npz"), allow_pickle=False)
    try:
        assert np.array_equal(np.asarray(zb["1M_p_b"]),
                              np.asarray(zs["1M_p_b"]))
    finally:
        zb.close()
        zs.close()


# (f) Static guards: no ttbin/decoder surface in the builder. -------------------

def test_builder_has_no_ttbin_or_decoder_surface():
    # Functional surface only (the docstring names `.ttbin` solely to state
    # the hard negative — no such import, path, or call exists here).
    src = inspect.getsource(x)
    for token in ("TimeTagger", "install_timetagger_alias", "read_ttbin",
                  ".ttbin\"", ".ttbin'", "decode_error_domain",
                  "construct_arm", "make_channel_sampler"):
        assert token not in src
    assert "ChannelAdapter" in src and "bind_empirical_bundle" in src


def test_cli_help_works(capsys):
    with pytest.raises(SystemExit) as exc:
        x.main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "--root" in out and "--mode" in out and "build" in out
