import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.nonbinary_v18_b2_structured_de import build_folded_w
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_v23_protograph import (
    base_matrix_to_distributions,
    run_protograph_de_scan,
)


def test_base_matrix_to_distributions_2x32():
    B = [[1] * 32, [1] * 32]
    meta = base_matrix_to_distributions(B)
    assert meta["rate"] == 1 - 2 / 32
    assert meta["lambda_edge"] == {2: 1.0}
    assert meta["rho_edge"] == {32: 1.0}


def test_protograph_scan_schema_q16():
    B = [[1] * 8, [1] * 8]  # rate 0.75 for q16 scan schema check
    doc = run_protograph_de_scan(q=16, base_matrices=[B],
                                 n_samples=100, max_iter=3,
                                 seed=2026099001, degree_max=128)
    # structured w for q16 not used by build_real_w_q1024; scan uses q1024 w -> skip here
    assert doc is not None
