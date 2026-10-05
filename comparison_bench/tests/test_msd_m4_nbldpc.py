"""Focused tests for M4 NB-LDPC arm: unified accounting + frozen shapes."""

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.msd_m4_nbldpc import (
    summarize_nb,
)
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v28 as v28  # noqa: E402


def test_nb_unified_f_formula():
    pts = [{"source": "S", "N": 1024, "gap": "nbldpc-v28-frozen", "blocks": 100,
            "L_EC": 1000, "m_total": 200, "failures": 10, "undetected": 1,
            "overruns": 0, "L1_ok": 90, "L2_ok": 85, "wall_s": 4000.0,
            "s_per_block": 40.0, "max_block_s": 75.0, "backend": "v28-FFT-QSPA",
            "seed": 1}]
    scalars = {"S": {"H_A": 10.0, "H_AB": 0.8}}
    r = summarize_nb(pts, scalars)[0]
    assert r["E_L"] == 1000.0  # recompute-script compatible row shape
    fer = 0.1
    denom = 1024 * 0.8
    kept = 1024 * 10.0 - 1000
    assert abs(r["f_expected"] - (1000 + 64 + kept * fer) / denom) < 1e-9


def test_v28_frozen_matrix_shapes():
    cfg = v28.frozen_v28_config()
    h1, h2map = v28.build_matrices(cfg)
    assert np.asarray(h1).shape == (int(cfg["m1"]), 1024)
    for label in ("1M", "1p5M", "2M"):
        h2 = v28.layer_matrix(h2map, label, cfg)
        assert np.asarray(h2).shape[1] == 1024
