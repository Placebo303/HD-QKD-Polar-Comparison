from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v19_de_search as de
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_v18_b2_structured_de import build_folded_w


def test_extended_eval_accepts_high_degree():
    w = build_folded_w(16)
    lam = {2: 0.3, 3: 0.3, 4: 0.2, 48: 0.2}
    doc = de.evaluate_extended_lambda(
        q=16, rate=0.65, w=w, lambda_edge=lam,
        n_samples=100, max_iter=5, seed=2026082001)
    assert doc["schema"] == "nbldpc_v19_extended_de_eval_v1"
    assert max(int(d) for d in doc["lambda_edge"]) >= 48
    assert isinstance(doc["converged"], bool)


def test_extended_probe_writes_json(tmp_path):
    w = build_folded_w(16)
    candidates = [{2: 0.5, 3: 0.5}, {2: 0.4, 3: 0.3, 4: 0.3}]
    doc = de.run_extended_degree_probe(
        q=16, rate=0.65, w=w, candidates=candidates,
        n_samples=100, max_iter=5, seed=2026082002,
        out_dir=tmp_path)
    assert doc["n_candidates"] == 2
    assert (tmp_path / "extended_degree_probe.json").exists()


def test_ladder_doc_builder():
    w = build_folded_w(16)
    doc = de.build_ladder_doc(
        q=16, w=w, rates=[0.6, 0.65],
        rows=[{"rate": 0.6, "converged": True}, {"rate": 0.65, "converged": False}],
        seed=1, max_converged_rate=0.6, max_converged_f=4.1785)
    assert doc["schema"] == "nbldpc_v19_rate_ladder_v1"
    assert doc["max_converged_rate"] == 0.6
