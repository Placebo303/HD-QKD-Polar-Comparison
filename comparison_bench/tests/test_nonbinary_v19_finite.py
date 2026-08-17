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


def test_construct_codebook_with_explicit_rho():
    from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v9_common as common
    lam = {2: 0.5, 3: 0.5}
    conc = common.concentrated_check_distribution(1 - 24 / 64, lam)
    rho = {int(conc["dc_lo"]): float(conc["w_lo"]),
           int(conc["dc_hi"]): float(conc["w_hi"])}
    rho = {d: w for d, w in rho.items() if w > 0.0}
    code = fin.construct_codebook(n=64, m=24, lambda_edge=lam, q=16, seed=2026082018,
                                  rho_edge=rho)
    assert code["rank"] == code["m"]
    assert code["construction"]["status"] == "ok"


def test_find_two_degree_rho():
    from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v10_common as common
    raw = common.MULLER_Q4_LAMBDA_PUBLISHED_DEGREES
    scale = sum(raw.values())
    lam = {d: v / scale for d, v in raw.items()}
    r = fin.find_two_degree_rho(n=1024, m=73, lambda_edge=lam, max_degree=200)
    assert r["socket_total"] == r["target_socket_total"]
    assert abs(sum(r["rho"].values()) - 1.0) < 1e-12


def test_execute_synthetic_frames_frame_seed_separate():
    q = 16
    n = 64
    m = 24
    lam = {2: 0.5, 3: 0.5}
    w = build_folded_w(q)
    doc = fin.execute_synthetic_frames(
        q=q, n=n, m=m, lambda_edge=lam, w=w,
        n_frames=1, seed=2026083001, frame_seed=2026082055, max_iter=10)
    assert doc["schema"] == "nbldpc_v19_finite_execute_v1"
    assert doc["frame_seed"] == 2026082055
    assert doc["seed"] == 2026083001
    assert len(doc["outcomes"]) == 1
