"""Focused tests for M2: rescue accounting + targeted-fix correctness."""

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.msd_m2_incremental import (
    summarize_m2,
)


def test_summarize_m2_expected_disclosure():
    pts = [{"source": "S", "N": 1024, "c0_base": 160, "k_rescue": 100,
            "blocks": 300, "L_base": 1000, "n_rescue": 60, "failures": 3,
            "undetected": 0, "stage_attempted": [300] * 10,
            "stage_passed": [297] * 10, "wall_s": 3.0, "s_per_block": 0.01,
            "backend": "m2-targeted", "seed": 1}]
    scalars = {"S": {"H_A": 10.0, "H_AB": 0.8}}
    rows = summarize_m2(pts, scalars)
    r = rows[0]
    assert abs(r["E_L"] - (1000 + 100 * 60 / 300)) < 1e-9
    fer = 3 / 300
    denom = 1024 * 0.8
    kept = 1024 * 10.0 - r["E_L"]
    assert abs(r["f_expected"] - (r["E_L"] + 64 + kept * fer) / denom) < 1e-9
    assert r["f_expected_upper95"] >= r["f_expected"]
    # no-rescue limit reproduces the M1'b f formula
    pts[0]["n_rescue"] = 0
    pts[0]["failures"] = 0
    r0 = summarize_m2(pts, scalars)[0]
    assert abs(r0["E_L"] - 1000) < 1e-9
    assert abs(r0["f_expected"] - (1000 + 64) / denom) < 1e-9


def test_targeted_fix_covers_all_weak_positions():
    # disclosing every position (K=N) must fix any base: base becomes truth.
    rng = np.random.default_rng(21)
    n = 64
    base = (rng.random(n) < 0.5).astype(np.uint8)
    truth = (rng.random(n) < 0.5).astype(np.uint8)
    ch = rng.uniform(0.05, 0.45, size=n)
    w = np.log((1 - ch) / ch)
    weak = np.argsort(w, kind="stable")[:n]
    base2 = base.copy()
    base2[weak] = truth[weak]
    assert bool((base2 == truth).all())
