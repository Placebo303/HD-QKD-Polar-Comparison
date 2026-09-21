"""Fake-only tests for the R1 histogram re-run executor (G-R1, T-R1-3).

FAKE-ONLY: every histogram/bundle here is synthetic and in-test. No ttbin
data path appears in this file; no production decoder/DE/graph call is made;
the real read path and correlation histogram on real data are never touched
(AGENTS.md §10.1 clause 8). Sparse round-trips use pytest tmp_path only.
Run per-file ONLY:
PYTHONPATH=<root> .venv/bin/python -m pytest -p no:cacheprovider -o addopts="" <this file>
"""

from __future__ import annotations

import inspect
import math

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.cli import r1_histogram_rerun as r
from comparison_bench.src.comparison_bench.cli import p3_census_a1 as a1
from comparison_bench.src.comparison_bench.formal_ir import (
    v80_s2c_campaign as c,
)


def _synthetic_nab(seed=11, n_pairs=300000, n_rows=64, n_cols=96):
    """Synthetic joint counts on a sub-block (FAKE ONLY — no data)."""
    rng = np.random.default_rng(seed)
    a = rng.integers(0, n_rows, size=n_pairs)
    b = rng.integers(0, n_cols, size=n_pairs)
    return np.bincount(a * 1024 + b, minlength=1024 * 1024).reshape(1024, 1024)


# (a) K_B edge cases. -------------------------------------------------------

def test_kb_single_occupied_column():
    N = np.zeros((1024, 1024), dtype=np.int64)
    N[10:20, 7] = np.arange(1, 11)
    assert r.k_b_of_nab(N) == 1
    p_b = r.p_b_of_nab(N)
    assert p_b.shape == (1024,)
    assert abs(float(p_b.sum()) - 1.0) < 1e-12
    assert int((p_b > 0).sum()) == 1 and p_b[7] > 0


def test_kb_full_support():
    N = np.random.default_rng(3).integers(1, 5, size=(1024, 1024)).astype(np.int64)
    assert r.k_b_of_nab(N) == 1024
    p_b = r.p_b_of_nab(N)
    assert p_b.shape == (1024,)
    assert abs(float(p_b.sum()) - 1.0) < 1e-12
    assert bool(np.all(p_b > 0))


# (b) Corrected-vs-old identity. ---------------------------------------------

def test_corrected_vs_old_identity():
    N = _synthetic_nab()
    N_ab = N.astype(np.float64)
    H1, H2, Hf = r.h_full_f03(N_ab)
    K_AB = int(np.count_nonzero(N))
    K_B = r.k_b_of_nab(N_ab)
    Nt = int(N.sum())
    assert 1 < K_B < K_AB  # synthetic sub-block: non-degenerate
    H_corr = Hf + r.mm_corrected(K_AB, K_B, Nt)
    H_old = Hf + r.mm_defective(K_AB, Nt)
    delta = H_old - H_corr
    assert delta >= 0.0
    assert abs(delta - (K_B - 1) / (2 * Nt * math.log(2))) < 1e-12
    assert abs(delta - r.delta_mm(K_B, Nt)) < 1e-15


def test_delta_zero_for_single_column():
    N = np.zeros((1024, 1024), dtype=np.int64)
    N[:, 5] = 3  # one occupied B column over many A rows
    N_ab = N.astype(np.float64)
    _, _, Hf = r.h_full_f03(N_ab)
    K_AB = int(np.count_nonzero(N))
    K_B = r.k_b_of_nab(N)
    assert K_B == 1
    Nt = int(N.sum())
    assert (Hf + r.mm_defective(K_AB, Nt)) - (Hf + r.mm_corrected(K_AB, K_B, Nt)) == 0.0
    assert r.delta_mm(K_B, Nt) == 0.0


# (c) Sparse COO round-trip. --------------------------------------------------

def test_sparse_coo_round_trip(tmp_path):
    N = _synthetic_nab()
    path = tmp_path / "T2-9M_N_ab_train_sparse.npz"
    sums = r.save_sparse_nab(path, N)
    z = np.load(str(path), allow_pickle=False)
    try:
        assert set(z.files) == {"row", "col", "count", "shape", "N_train"}
        for k in ("row", "col", "count"):
            assert z[k].dtype == np.int64
        assert tuple(int(v) for v in np.asarray(z["shape"]).tolist()) == (1024, 1024)
        assert int(z["N_train"]) == int(N.sum())
    finally:
        z.close()
    dense, meta = r.load_sparse_nab(path)
    assert np.array_equal(dense, N)
    assert meta["sum"] == sums["sparse_sum"] == int(N.sum())
    assert meta["nnz"] == sums["sparse_nnz"] == int(np.count_nonzero(N))
    assert meta["N_train"] == int(N.sum())


# (d) bind_empirical_bundle shape/normalization gates (synthetic). ------------

def _synthetic_bundle(seed=7):
    rng = np.random.default_rng(seed)
    g1 = rng.random((32, 1024)) + 0.01
    g1 = g1 / g1.sum(axis=0, keepdims=True)
    g2 = rng.random((32, 32, 1024)) + 0.01
    g2 = g2 / g2.sum(axis=1, keepdims=True)
    return {"g1": g1, "g2": g2,
            "p_b": np.full(1024, 1.0 / 1024), "source": "2M"}


def test_bind_empirical_bundle_synthetic_gates():
    good = _synthetic_bundle()
    bound = c.bind_empirical_bundle(dict(good))
    assert bound["g1"].shape == (32, 1024)
    assert bound["g2"].shape == (32, 32, 1024)
    assert bound["p_b"].shape == (1024,)
    with pytest.raises(c.Refusal):
        c.bind_empirical_bundle(dict(good, p_b=good["p_b"] * 2.0))
    with pytest.raises(c.Refusal):
        c.bind_empirical_bundle({"g1": np.ones((32, 1000)), "g2": good["g2"],
                                 "p_b": good["p_b"]})
    with pytest.raises(c.Refusal):
        c.bind_empirical_bundle({"g1": good["g1"], "g2": good["g2"]})
    zero_col = dict(good, g1=good["g1"].copy())
    zero_col["g1"][:, 3] = 0.0  # colsum 0 != 1 -> bind refuses
    with pytest.raises(c.Refusal):
        c.bind_empirical_bundle(zero_col)


# (e) Gate-logic unit checks. --------------------------------------------------

def test_kb_gate_logic():
    assert r.k_b_gate_pass(1000, 2500) is True
    assert r.k_b_gate_pass(1, 2) is True
    assert r.k_b_gate_pass(1024, 5000) is True
    assert r.k_b_gate_pass(0, 2500) is False
    assert r.k_b_gate_pass(1025, 5000) is False
    assert r.k_b_gate_pass(2500, 2500) is False  # equality signals corruption
    assert r.k_b_gate_pass(2600, 2500) is False


def test_both_or_neither_logic(tmp_path):
    from pathlib import Path as _P
    trio = (_P(str(tmp_path / "T2-9M.json")),
            _P(str(tmp_path / "T2-9M_N_ab_train_sparse.npz")),
            _P(str(tmp_path / "T2-9M_p_b_train.npy")))
    assert r.trio_complete(trio) is False
    for p in trio:
        p.write_bytes(b"x")
    assert r.trio_complete(trio) is True
    trio[2].unlink()
    assert r.trio_complete(trio) is False  # partial ⇒ not complete
    r.remove_trio(trio)
    assert r.trio_complete(trio) is False  # all-or-none after cleanup


def test_span_gate_logic():
    assert r.span_gate_pass(3.0, 2.99, 0.5) is True
    assert r.span_gate_pass(0.0, 0.0, 0.5) is False
    assert r.span_gate_pass(-1.0, -1.0, 0.5) is False
    assert r.span_gate_pass(3.0, 2.0, 0.5) is False
    assert r.span_gate_pass(3.0, None, 0.5) is False
    assert r.span_gate_pass(None, 3.0, 0.5) is False


def test_determinism_check_logic():
    a1_row = {"n_pairs_N": 100, "n_frames": 10,
              "split_train_frames": 6, "split_val_frames": 2,
              "split_hold_frames": 2,
              "offset_ps_derived": 50, "peak_bin_index": 8192,
              "duration_measured_s": 3.0}
    a1_split = {"train_frames": [0, 5], "val_frames": [6, 7],
                "hold_frames": [8, 9]}
    kw = dict(n_pairs_N=100, n_frames=10, split_counts=(6, 2, 2),
              split_ranges=([0, 5], [6, 7], [8, 9]),
              offset_ps_derived=50, peak_bin_index=8192,
              duration_measured_s=3.0,
              a1_row=a1_row, a1_split=a1_split)
    ok = r.determinism_check(**kw)
    assert ok["pass"] is True
    bad = r.determinism_check(**dict(kw, offset_ps_derived=-50))
    assert bad["pass"] is False
    assert bad["fields"]["offset_ps_derived"] is False
    missing = r.determinism_check(**dict(kw, a1_row=None, a1_split=None))
    assert missing["pass"] is False  # fail closed without reference


def test_design_point_arithmetic_vs_recompute():
    # Frozen thresholds (recompute §4 verbatim outputs).
    assert r.threshold_H(208) == pytest.approx(0.829326923076923, abs=1e-12)
    assert r.threshold_H(200) == pytest.approx(0.7992788461538461, abs=1e-12)
    assert r.threshold_H(199) == pytest.approx(0.7955228365384616, abs=1e-12)
    # Full-precision recompute rows (recompute §§1–3).
    row_2m = r.design_point(0.8345846048587662)
    assert row_2m["m_max_raw"] == 209 and row_2m["m_max_capped"] == 208
    assert row_2m["f_at_208"] == pytest.approx(1.291810313446229, abs=1e-12)
    assert row_2m["N_req_at_208"] == 1754
    row_1m = r.design_point(0.8036079281174853)
    assert row_1m["m_max_raw"] == 201
    assert row_1m["N_req_at_mmax"] == 15487
    row_15 = r.design_point(0.8289616869054485)
    assert row_15["m_max_raw"] == 207
    assert row_15["N_req_at_mmax"] == 2700
    raw = 3 * r.SLOPE_FROZEN / (1.3 - 1.2946824979408418)
    assert 2699.0 < raw < 2700.0  # razor-thin ceil boundary (baseline §3 note)
    assert r.n_req_of_f(1.3) is None and r.n_req_of_f(1.5) is None


def test_frozen_path_reused_by_import_not_copied():
    # Acceptance R1-IMPL-1: the frozen estimator/parsers are the SAME objects.
    assert r.h_full_f03 is a1.h_full_f03
    assert r.parse_bases is a1.parse_bases
    assert r.parse_datasets is a1.parse_datasets
    src = inspect.getsource(r)
    assert "def h_full_f03" not in src  # no forked arithmetic
    for name in ("DATASET_IDS", "PRIOR_OFFSET_PS", "PRIOR_BIN", "CH_A",
                 "CH_B", "COIN_WINDOW_PS", "BIN_WIDTH_PS", "FRAME_BINS",
                 "ALIGN_MODE_FRAMING", "POSTSELECT", "PAIRING_THRESHOLD_PS",
                 "FILENAME_DURATION_TAG", "PER_DATASET_CEILING_S"):
        assert getattr(r, name) is getattr(a1, name)


def test_2m_reporter_read_only_no_refit_path():
    # The reporter opens the frozen lineage read-only; the module contains
    # no save/refit/substitution path for bundle artifacts.
    src = inspect.getsource(r)
    assert "np.load" in src
    assert "np.savez" not in src.split("def compare_2m_bundle")[1].split("def ")[0]
    assert "ChannelAdapter" not in src
    # Synthetic reporter mechanics: materiality bars fire as frozen.
    p_b = np.full(1024, 1.0 / 1024)
    rec = r.compare_2m_bundle(N_train=589461, H_L1=0.025, H_L2=0.806,
                              p_b=p_b,
                              gamma_path="/nonexistent/gamma_f03.npz")
    assert rec["ran"] is False and rec["finding"] is False
    assert r.FROZEN_2M_TRAIN_N == 559872.0
    assert (r.DH_MATERIAL, r.PB_MATERIAL) == (0.01, 1e-3)
