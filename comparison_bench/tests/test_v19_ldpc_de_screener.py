from comparison_bench.src.comparison_bench.cli.run_v19_ldpc_de_screener import run_screener


def test_screener_schema():
    doc = run_screener(n=512, overhead=1.3, n_samples=200, max_iter=50, p_tol=0.02)
    assert doc["schema"] == "nbldpc_v19_ldpc_de_screener_v1"
    assert len(doc["rows"]) == 10
    assert "f_with_fallback" in doc
    assert doc["n"] == 512
