from comparison_bench.src.comparison_bench.cli.run_v19_binary_mlc_prototype import run_prototype


def test_prototype_schema_and_success():
    doc = run_prototype(frames_per_plane=2, seed=2026081902)
    assert doc["schema"] == "nbldpc_v19_binary_mlc_prototype_v1"
    assert doc["block_length"] == 256
    assert len(doc["per_plane"]) == 10
    assert doc["total_syndrome_bits_per_frame"] > 0
    assert doc["measured_f"] > 1.0
    assert doc["status"] in {"all_planes_correct", "has_failures"}
