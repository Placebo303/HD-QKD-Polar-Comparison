import numpy as np

from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v14_mcde as v14
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_v10_common import concentrated_check_distribution
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_v22b_mcde import run_mcde_high_degree


def test_run_mcde_high_degree_restores_cap():
    q = 16
    lam = {2: 0.5, 3: 0.5}
    rate = 0.6
    conc = concentrated_check_distribution(rate, lam)
    rho = {int(conc["dc_lo"]): float(conc["w_lo"]),
           int(conc["dc_hi"]): float(conc["w_hi"])}
    rho = {d: wgt for d, wgt in rho.items() if wgt > 0.0}
    w = np.full(q, 1.0 / q)
    old = v14.DEGREE_MAX
    res = run_mcde_high_degree(
        q=q, lambda_edge=lam, rho_edge=rho,
        n_samples=100, max_iter=3, seed=2026098001,
        channel_mode="structured", w=w, degree_max=128)
    assert v14.DEGREE_MAX == old
    assert "converged" in res
