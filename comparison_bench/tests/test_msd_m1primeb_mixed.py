"""Focused tests for M1'b: PEG determinism/canonical form + mixed spec."""

import numpy as np
from scipy import sparse

from comparison_bench.src.comparison_bench.formal_ir.msd_m1primeb_mixed import (
    build_mixed_point,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_peg_code import (
    build_peg_code,
)


def test_peg_deterministic_and_canonical():
    a = build_peg_code(n=128, m=100, variable_degree=3).parity_check_matrix
    b = build_peg_code(n=128, m=100, variable_degree=3).parity_check_matrix
    assert sparse.isspmatrix_csr(a) and sparse.isspmatrix_csr(b)
    assert a.has_canonical_format, "receiver requires canonical CSR"
    assert (a != b).nnz == 0
    assert a.shape == (100, 128)
    assert set(np.unique(a.data)) <= {0, 1}


def test_peg_validation_rejects_bad_params():
    for kw in (dict(n=0, m=4, variable_degree=1), dict(n=8, m=0, variable_degree=1),
               dict(n=8, m=4, variable_degree=5), dict(n=8, m=4, variable_degree=True)):
        try:
            build_peg_code(**kw)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {kw}")


def test_mixed_spec_disclosure_rule():
    h_plane = [0.7882, 0.0099] + [0.0] * 8
    matrices, factories, kinds, m_list = build_mixed_point(1024, h_plane, 160, 32, 64)
    import math

    assert m_list[0] == math.ceil(1024 * 0.7882 + 160)
    assert m_list[1] == math.ceil(1024 * 0.0099 + 32)
    assert m_list[2:] == [16] * 8  # SPC g=64 -> 1024/64 checks
    assert kinds[0].startswith("peg") and kinds[2].startswith("spc")
    assert len(factories) == 10
