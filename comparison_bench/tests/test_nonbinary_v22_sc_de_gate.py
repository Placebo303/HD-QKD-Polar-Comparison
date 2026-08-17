from comparison_bench.src.comparison_bench.formal_ir.nonbinary_v22_sc_de_gate import run_v22_sc_de_gate


def test_v22_sc_de_gate_schema():
    doc = run_v22_sc_de_gate(q=16, p=0.05, n_samples=100, max_iter=5,
                             seed=2026095001)
    assert doc["schema"] == "nbldpc_v22_sc_de_gate_v1"
    assert doc["n_rows"] == 6
    assert "gate_passed" in doc
