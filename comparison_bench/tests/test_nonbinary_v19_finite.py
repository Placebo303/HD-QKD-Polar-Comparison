import numpy as np

from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v19_finite as fin
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_v18_b2_structured_de import build_folded_w


def test_construct_codebook_small_q():
    lam = {2: 0.5, 3: 0.5}
    code = fin.construct_codebook(n=64, m=24, lambda_edge=lam, q=16, seed=2026082004)
    assert code["status"] if "status" in code else True
    assert code["rank"] == code["m"]
    assert len(code["matrix"]) == code["m"]
    assert all(len(row) == code["n"] for row in code["matrix"])


def test_execute_synthetic_frames_tiny():
    q = 16
    n = 64
    m = 24
    lam = {2: 0.5, 3: 0.5}
    w = build_folded_w(q)
    doc = fin.execute_synthetic_frames(
        q=q, n=n, m=m, lambda_edge=lam, w=w,
        n_frames=2, seed=2026082005, max_iter=10)
    assert doc["schema"] == "nbldpc_v19_finite_execute_v1"
    assert doc["n_frames"] == 2
    assert len(doc["outcomes"]) == 2
    assert doc["syndrome_bits_per_frame"] == m * 4
