import json

from comparison_bench.src.comparison_bench.cli.run_v19_three_way_compare import run_compare


def _make_nonbinary_doc(tmp_path):
    doc = {
        "schema": "nbldpc_v19_finite_execute_v1",
        "q": 16, "n": 256, "m": 102, "rate": 0.6015625,
        "n_frames": 20, "n_exact_correct": 20, "n_exact_mismatch": 0,
        "n_decode_failed": 0, "fer": 0.0,
        "syndrome_bits_per_frame": 408, "syndrome_bits_per_symbol": 1.59375,
        "channel_entropy_bits_per_symbol": 0.3829,
        "f_plain_qary": 4.16, "wall_seconds": 1.0,
        "outcomes": [],
    }
    p = tmp_path / "nb.json"
    p.write_text(json.dumps(doc), encoding="utf-8")
    return p


def test_compare_schema(tmp_path):
    nb = _make_nonbinary_doc(tmp_path)
    out = tmp_path / "out"
    doc = run_compare(nonbinary_path=nb, out_dir=out)
    assert doc["schema"] == "nbldpc_v19_three_way_comparison_v1"
    assert len(doc["rows"]) == 4
    routes = {r["route"] for r in doc["rows"]}
    assert routes == {"binary_polar_mlc", "binary_ldpc_mlc", "nonbinary_ldpc",
                      "nonbinary_ldpc_q1024"}
    assert (out / "comparison_table.csv").exists()
    assert (out / "comparison_summary.json").exists()
    # Statuses must be preserved; no decode_failed converted to ok.
    assert doc["rows"][2]["status"] == "exact_correct_all"
    assert doc["rows"][3]["status"] == "not_available"
