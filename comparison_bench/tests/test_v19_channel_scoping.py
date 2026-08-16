from comparison_bench.src.comparison_bench.cli.run_v19_channel_scoping import compute_scoping


def test_scoping_schema_and_f():
    doc = compute_scoping()
    assert doc["schema"] == "nbldpc_v19_channel_scoping_v1"
    assert len(doc["per_plane_error"]) == 10
    assert doc["sum_h2_per_plane"] > 0.5
    assert abs(doc["ideal_binary_mlc_f"] - 1.0) < 1e-6


def test_scoping_includes_existing_binary_reference():
    doc = compute_scoping()
    assert "existing_binary_v4_h1_f" in doc
    assert "existing_binary_v5_h1_h2_f" in doc
    assert doc["existing_binary_v4_h1_f"] > 1.0
    assert doc["existing_binary_v5_h1_h2_f"] > doc["existing_binary_v4_h1_f"]
