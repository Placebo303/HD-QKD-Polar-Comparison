"""G8-S0 entropy diagnosis — lean verification (METHOD trap 6).

Read-only on frozen workspace/v72p2d5_model_f_input/20260907_r1/model_f_input.npz
(counts_ab, p_b). Zero decoder/DE/graph calls, zero pool reads. Reuses
build_f_model_concentration / marginalize_f_to_p1 / conditionalize_f_to_p2
(import only, never reimplemented). Run per-file ONLY:
.venv/bin/python -m pytest -p no:cacheprovider -o addopts="" <this file>
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir import v72p2d5_gf32_rate_mother as d5

ROOT = Path(__file__).resolve().parents[2]

NPZ = ROOT / "workspace" / "v72p2d5_model_f_input" / "20260907_r1" / "model_f_input.npz"
RESULT = ROOT / "docs" / "research_cycles" / "V72P3G8-PRIOR-EFFICIENCY" / "S0_RESULT.json"
A = 1024


def _load():
    z = np.load(NPZ)
    return z["counts_ab"].astype(np.float64), z["p_b"].astype(np.float64)


def _h_planes(p_f, p_b):
    p1 = d5.marginalize_f_to_p1(p_f)
    p2 = d5.conditionalize_f_to_p2(p_f)
    with np.errstate(divide="ignore", invalid="ignore"):
        h1 = np.where(p1 > 0, -p1 * np.log2(np.where(p1 > 0, p1, 1)), 0.0).sum(axis=0)
        h1v = float((p_b * h1).sum())
        h2 = np.where(p2 > 0, -p2 * np.log2(np.where(p2 > 0, p2, 1)), 0.0).sum(axis=2)
        h2v = float((p_b[None, :] * p1 * h2).sum())
    return h1v, h2v


def _models():
    counts, p_b = _load()
    n = float(counts.sum())
    dlt = (np.arange(A)[:, None] - np.arange(A)[None, :]) % A
    q = np.array([counts[dlt == k].sum() for k in range(A)]) / n
    pf = {"H_A": d5.build_f_model_concentration(counts, d5.LAMBDA_STAR)}
    pg = counts.sum(axis=1) / n
    for eps in (1e-3, 1e-2):
        pf["H_B_eps_%g" % eps] = (q[dlt] + eps * pg[:, None]) / (1.0 + eps)
    seg, cmat = np.arange(A) // 64, np.zeros((A, A))
    for s in range(16):
        m = seg == s
        ns = counts[:, m].sum()
        qs = np.array([counts[:, m][dlt[:, m] == k].sum() for k in range(A)]) / ns
        cmat[:, m] = qs[dlt[:, m]]
    pf["H_C"] = cmat
    return q, pf, p_b


def test_q_sums_to_1():
    q, _, _ = _models()
    assert abs(float(q.sum()) - 1.0) <= 1e-12


def test_pf_columns_sum_to_1():
    _, pf, _ = _models()
    for k, p in pf.items():
        assert np.abs(p.sum(axis=0) - 1.0).max() <= 1e-12, k


def test_entropies_in_0_5():
    _, pf, p_b = _models()
    for k, p in pf.items():
        h1, h2 = _h_planes(p, p_b)
        assert 0.0 <= h1 <= 5.0 and 0.0 <= h2 <= 5.0, (k, h1, h2)


def test_h_a_l1_in_anchor_band():
    _, pf, p_b = _models()
    h1, _ = _h_planes(pf["H_A"], p_b)
    assert 4.2 <= h1 <= 4.5  # 4.34 anchor band (R14 4.3437 / D7 cap 4.343407)


def test_h_a_l2_sanity_mismatch_tripwire():
    # Frozen sanity gate outcome: L2 does NOT sit at the 4.34 anchor
    # (|H_A_L2-4.34|>0.15 -> SANITY_STOP). Fails if that premise ever changes.
    _, pf, p_b = _models()
    _, h2 = _h_planes(pf["H_A"], p_b)
    assert abs(h2 - 4.34) > 0.15


def test_result_json_matches_recomputation():
    _, pf, p_b = _models()
    got = json.loads(RESULT.read_text())
    key = {"H_A": "H_A", "H_B_eps_0.001": "H_B_eps_0.001",
           "H_B_eps_0.01": "H_B_eps_0.01", "H_C": "H_C"}
    for jk, pk in key.items():
        h1, h2 = _h_planes(pf[pk], p_b)
        assert abs(got["S0_numbers"][jk]["L1"] - h1) <= 1e-9
        assert abs(got["S0_numbers"][jk]["L2"] - h2) <= 1e-9
