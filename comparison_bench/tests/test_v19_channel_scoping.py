from comparison_bench.src.comparison_bench.cli.run_v19_channel_scoping import compute_scoping


def test_scoping_schema_and_f():
    doc = compute_scoping()
    assert doc["schema"] == "nbldpc_v19_channel_scoping_v1"
    assert len(doc["per_plane_error"]) == 10
    assert doc["sum_h2_per_plane"] > 0.5
    assert abs(doc["ideal_binary_mlc_f"] - 1.0) < 1e-6
