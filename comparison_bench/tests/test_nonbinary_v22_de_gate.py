import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.nonbinary_v18_b2_structured_de import build_folded_w
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_v22_de_gate import run_v22_de_gate


def test_v22_de_gate_schema():
    q = 16
    w = np.asarray(build_folded_w(q), dtype=np.float64)
    candidates = [
        {2: 0.5, 3: 0.5},
        {2: 0.6, 3: 0.4},
    ]
    doc = run_v22_de_gate(q=q, w=w, rate=0.6, candidates=candidates,
                          n_samples=200, max_iter=10, seed=2026092001)
    assert doc["schema"] == "nbldpc_v22_de_gate_v1"
    assert doc["n_candidates"] == 2
    assert len(doc["candidates"]) == 2
    assert "gate_passed" in doc
