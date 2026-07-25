"""Tests for the make_expanded_evidence_package CLI."""
from __future__ import annotations

import json
import hashlib
import shutil
from pathlib import Path

import pandas as pd
import pytest

from comparison_bench.src.comparison_bench.cli.make_expanded_evidence_package import (
    compute_file_hash,
    get_git_commit,
    load_csv,
    make_cascade_optimized,
    make_ldpc_optimized,
    make_qldpc_reference,
    make_scalability_summary,
    make_method_comparison,
    make_failure_analysis,
    make_manifest,
    write_outputs,
    main,
)

TEST_DIR = Path("D:/Code/HD-QKD_Polar_Comparison/workspace/pytest-evidence-test")


def setup_function():
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)
    TEST_DIR.mkdir(parents=True, exist_ok=True)


def teardown_function():
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR, ignore_errors=True)


def _make_input_dir() -> Path:
    """Create minimal input CSVs for testing."""
    d = TEST_DIR / "input"
    d.mkdir(parents=True, exist_ok=True)

    cascade = pd.DataFrame({
        "dataset_id": ["d1", "d1", "d1", "d2", "d2"],
        "dimension": [8, 8, 8, 16, 16],
        "bin_width_ps": [120, 120, 120, 100, 100],
        "frame_cap": [4, 4, 4, 4, 4],
        "frames_used_actual": [4, 4, 4, 4, 4],
        "method": ["cascade_lite"] * 5,
        "method_status": ["ok"] * 5,
        "backend_status": ["ok"] * 5,
        "block_size_schedule": ["8,4,16,13"] * 5,
        "num_passes": [3, 4, 2, 3, 4],
        "permutation_mode": ["seeded_random"] * 5,
        "seed": [0, 0, 0, 0, 0],
        "n_frames_attempted": [4, 4, 4, 4, 4],
        "n_frames_success": [4, 4, 4, 4, 4],
        "n_frames_failed_decode": [0, 0, 0, 0, 0],
        "n_frames_failed_verify": [0, 0, 0, 0, 0],
        "accepted_frame_fraction": [1.0] * 5,
        "raw_ser": [0.1] * 5,
        "post_ir_ser": [0.0] * 5,
        "leak_EC_actual_bits": [700.0, 557.0, 800.0, 900.0, 879.0],
        "leak_EC_per_input_bit": [0.5] * 5,
        "beta_eff_empirical": [0.8] * 5,
        "runtime_s": [0.1, 0.2, 0.15, 0.3, 0.25],
        "notes": [""] * 5,
        "param_hash": ["h1", "h2", "h3", "h4", "h5"],
        "real_ir_success": [True, True, True, True, True],
        "success_classification": ["real_ir_success"] * 5,
    })
    cascade.to_csv(d / "cascade_param_sweep_results.csv", index=False)

    ldpc = pd.DataFrame({
        "dataset_id": ["d1", "d1", "d2", "d2"],
        "dimension": [8, 8, 16, 16],
        "bin_width_ps": [120, 120, 100, 100],
        "frame_cap": [4, 4, 4, 4],
        "frames_used_actual": [4, 4, 4, 4],
        "method": ["layered_ldpc_lite"] * 4,
        "method_status": ["ok", "decode_failed", "ok", "decode_failed"],
        "backend_status": ["ok", "ok", "ok", "ok"],
        "parity_fraction": [0.5, 0.5, 0.5, 0.5],
        "max_iter": [20] * 4,
        "osd_order": [0] * 4,
        "bp_method": ["minimum_sum"] * 4,
        "mapping": ["gray"] * 4,
        "llr_mode": ["hard"] * 4,
        "bitplane_rate_mode": ["per_bitplane_raw_ber"] * 4,
        "n_frames_attempted": [4, 4, 4, 4],
        "n_frames_success": [4, 0, 4, 0],
        "n_frames_failed_decode": [0, 4, 0, 4],
        "n_frames_failed_verify": [0, 0, 0, 0],
        "accepted_frame_fraction": [1.0, 0.0, 1.0, 0.0],
        "raw_ser": [0.1] * 4,
        "post_ir_ser": [0.0, 0.1, 0.0, 0.1],
        "leak_EC_actual_bits": [600.0, 575.0, 850.0, 900.0],
        "leak_EC_per_input_bit": [0.5] * 4,
        "beta_eff_empirical": [0.8, 0.0, 0.8, 0.0],
        "runtime_s": [0.2, 0.1, 0.3, 0.15],
        "notes": [""] * 4,
        "param_hash": ["h1", "h2", "h3", "h4"],
        "real_ir_success": [True, False, True, False],
        "success_classification": ["real_ir_success", "decode_failed", "real_ir_success", "decode_failed"],
    })
    ldpc.to_csv(d / "layered_ldpc_param_sweep_results.csv", index=False)

    qldpc = pd.DataFrame({
        "dataset_id": ["q1", "q1", "q1"],
        "data_mode": ["synthetic", "synthetic", "synthetic"],
        "dimension": [8, 8, 8],
        "bin_width_ps": [None, None, None],
        "q": [8, 8, 8],
        "frame_len_symbols": [64, 64, 64],
        "frame_cap": [4, 4, 4],
        "frames_used_actual": [4, 4, 4],
        "decoder": ["qary_hard_syndrome_bf"] * 3,
        "channel_model": ["qary_symmetric"] * 3,
        "check_fraction": [0.33, 0.4, 0.5],
        "row_weight": [3, 3, 3],
        "max_iter": [20] * 3,
        "method": ["qldpc_reference"] * 3,
        "method_status": ["ok", "ok", "ok"],
        "backend_status": ["ok", "ok", "ok"],
        "n_frames_attempted": [4, 4, 4],
        "n_frames_success": [2, 3, 1],
        "n_frames_failed_decode": [0, 0, 0],
        "n_frames_failed_verify": [2, 1, 3],
        "accepted_frame_fraction": [0.5, 0.75, 0.25],
        "raw_ser": [0.05] * 3,
        "post_ir_ser": [0.02, 0.01, 0.03],
        "leak_EC_actual_bits": [400.0, 350.0, 450.0],
        "leak_EC_per_input_bit": [0.5] * 3,
        "beta_eff_empirical": [0.0] * 3,
        "runtime_s": [0.05] * 3,
        "notes": [""] * 3,
        "param_hash": ["qh1", "qh2", "qh3"],
        "real_ir_success": [False, False, False],
        "success_classification": ["reference_only"] * 3,
    })
    qldpc.to_csv(d / "qldpc_param_sweep_results.csv", index=False)

    (d / "scalability").mkdir(exist_ok=True)
    scal_real = pd.DataFrame({
        "dataset_id": ["d1"],
        "data_mode": ["real_data"],
        "dimension": [8],
        "bin_width_ps": [120],
        "frame_len_symbols": [128],
        "method": ["cascade_lite"],
        "real_ir_success": [True],
        "success_classification": ["real_ir_success"],
        "leak_EC_actual_bits": [500.0],
        "runtime_s": [0.5],
    })
    scal_real.to_csv(d / "scalability" / "ir_benchmark_results.csv", index=False)

    (d / "scalability_synth").mkdir(exist_ok=True)
    scal_synth = pd.DataFrame({
        "dataset_id": ["s1"],
        "data_mode": ["synthetic"],
        "dimension": [16],
        "bin_width_ps": [100],
        "frame_len_symbols": [2048],
        "method": ["cascade_lite"],
        "real_ir_success": [True],
        "success_classification": ["real_ir_success"],
        "leak_EC_actual_bits": [9000.0],
        "runtime_s": [1.0],
    })
    scal_synth.to_csv(d / "scalability_synth" / "ir_benchmark_results.csv", index=False)

    manifest = {
        "benchmark_config_snapshot": {
            "global": {"output_dir": "test"},
            "cascade": {"passes": [2, 3, 4]},
        }
    }
    with open(d / "ir_v3_run_manifest.json", "w") as f:
        json.dump(manifest, f)

    return d


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestComputeFileHash:
    def test_deterministic(self) -> None:
        TEST_DIR.mkdir(parents=True, exist_ok=True)
        f = TEST_DIR / "hash_test.txt"
        f.write_text("hello world")
        h1 = compute_file_hash(f)
        h2 = compute_file_hash(f)
        assert h1 == h2
        assert len(h1) == 64

    def test_different_files(self) -> None:
        TEST_DIR.mkdir(parents=True, exist_ok=True)
        f1 = TEST_DIR / "a.txt"
        f2 = TEST_DIR / "b.txt"
        f1.write_text("aaa")
        f2.write_text("bbb")
        assert compute_file_hash(f1) != compute_file_hash(f2)


class TestGetGitCommit:
    def test_returns_string(self) -> None:
        result = get_git_commit()
        assert isinstance(result, str)
        assert len(result) > 0


class TestLoadCsv:
    def test_loads_existing(self) -> None:
        d = _make_input_dir()
        df = load_csv(d, "cascade_param_sweep_results.csv")
        assert df is not None
        assert len(df) == 5

    def test_returns_none_if_missing(self) -> None:
        d = _make_input_dir()
        df = load_csv(d, "nonexistent.csv")
        assert df is None


class TestMakeCascadeOptimized:
    def test_selects_min_leakage_per_dataset(self) -> None:
        d = _make_input_dir()
        df = load_csv(d, "cascade_param_sweep_results.csv")
        result = make_cascade_optimized(df)
        assert len(result) == 2
        d1 = result[result["dataset_id"] == "d1"]
        assert d1["leak_EC_actual_bits"].iloc[0] == 557.0
        assert d1["num_passes"].iloc[0] == 4
        d2 = result[result["dataset_id"] == "d2"]
        assert d2["leak_EC_actual_bits"].iloc[0] == 879.0

    def test_all_real_ir_success_true(self) -> None:
        d = _make_input_dir()
        df = load_csv(d, "cascade_param_sweep_results.csv")
        result = make_cascade_optimized(df)
        assert all(result["real_ir_success"] == True)  # noqa: E712


class TestMakeLdpcOptimized:
    def test_selects_min_leakage_per_dataset(self) -> None:
        d = _make_input_dir()
        df = load_csv(d, "layered_ldpc_param_sweep_results.csv")
        result = make_ldpc_optimized(df)
        assert len(result) == 2
        d1 = result[result["dataset_id"] == "d1"]
        assert d1["leak_EC_actual_bits"].iloc[0] == 600.0
        d2 = result[result["dataset_id"] == "d2"]
        assert d2["leak_EC_actual_bits"].iloc[0] == 850.0

    def test_excludes_failures(self) -> None:
        d = _make_input_dir()
        df = load_csv(d, "layered_ldpc_param_sweep_results.csv")
        result = make_ldpc_optimized(df)
        assert all(result["real_ir_success"] == True)  # noqa: E712


class TestMakeQldpcReference:
    def test_preserves_success_classification(self) -> None:
        d = _make_input_dir()
        df = load_csv(d, "qldpc_param_sweep_results.csv")
        result = make_qldpc_reference(df)
        assert len(result) >= 1
        assert all(result["success_classification"] == "reference_only")

    def test_selects_max_n_frames_success(self) -> None:
        d = _make_input_dir()
        df = load_csv(d, "qldpc_param_sweep_results.csv")
        result = make_qldpc_reference(df)
        row = result[result["check_fraction"] == 0.4]
        assert row["n_frames_success"].iloc[0] == 3


class TestMakeScalabilitySummary:
    def test_merges_real_and_synth(self) -> None:
        d = _make_input_dir()
        real = load_csv(d, "scalability/ir_benchmark_results.csv")
        synth = load_csv(d, "scalability_synth/ir_benchmark_results.csv")
        result = make_scalability_summary(real, synth)
        assert len(result) == 2
        assert set(result["dataset_id"]) == {"d1", "s1"}

    def test_deduplicates_by_dataset_id(self) -> None:
        d = _make_input_dir()
        real = load_csv(d, "scalability/ir_benchmark_results.csv")
        synth = load_csv(d, "scalability_synth/ir_benchmark_results.csv")
        synth = pd.concat([synth, real], ignore_index=True)
        result = make_scalability_summary(real, synth)
        assert len(result) == 2


class TestMakeMethodComparison:
    def test_groups_by_frame_len(self) -> None:
        """Scalability data with frame_len_symbols is grouped correctly."""
        scal = pd.DataFrame({
            "dataset_id": ["s1", "s1", "s2"],
            "method": ["cascade_lite", "layered_ldpc_lite", "cascade_lite"],
            "frame_len_symbols": [128, 128, 2048],
            "real_ir_success": [True, True, True],
            "leak_EC_actual_bits": [500.0, 600.0, 9000.0],
            "runtime_s": [0.5, 0.8, 1.0],
        })
        result = make_method_comparison(None, None, scal)
        assert len(result) == 3  # 3 rows: cascade at 128, ldpc at 128, cascade at 2048
        assert "frame_len_symbols" in result.columns
        assert "method" in result.columns
        assert list(result["frame_len_symbols"]) == [128, 128, 2048]
        assert list(result["method"]) == ["cascade_lite", "layered_ldpc_lite", "cascade_lite"]

    def test_uses_frame_len_symbols_when_available(self) -> None:
        """When scalability data (with frame_len_symbols) is fed, output uses that key."""
        scal = pd.DataFrame({
            "dataset_id": ["s1"],
            "method": ["cascade_lite"],
            "frame_len_symbols": [2048],
            "real_ir_success": [True],
            "leak_EC_actual_bits": [9000.0],
            "runtime_s": [1.0],
        })
        result = make_method_comparison(None, None, scal)
        assert "frame_len_symbols" in result.columns
        assert result["frame_len_symbols"].iloc[0] == 2048

    def test_skips_sweep_data_missing_frame_len(self) -> None:
        """Sweep CSVs lacking frame_len_symbols are excluded from comparison."""
        d = _make_input_dir()
        cascade = load_csv(d, "cascade_param_sweep_results.csv")
        ldpc = load_csv(d, "layered_ldpc_param_sweep_results.csv")
        # Neither cascade nor ldpc have frame_len_symbols — result is empty
        result = make_method_comparison(cascade, ldpc, None)
        assert result.empty
        assert "frame_cap" not in result.columns
        assert "frame_len_symbols" not in result.columns


class TestMakeFailureAnalysis:
    def test_counts_failures(self) -> None:
        d = _make_input_dir()
        cascade = load_csv(d, "cascade_param_sweep_results.csv")
        ldpc = load_csv(d, "layered_ldpc_param_sweep_results.csv")
        result = make_failure_analysis(cascade, ldpc)
        assert len(result) >= 1
        assert "failure_count" in result.columns
        ldpc_failures = result[result["method_name"] == "layered_ldpc_lite"]
        assert ldpc_failures["failure_count"].sum() == 2


class TestMakeManifest:
    def test_includes_source_hashes(self) -> None:
        d = _make_input_dir()
        output_dir = d / "output"
        output_dir.mkdir(exist_ok=True)
        manifest = make_manifest(d, output_dir, ["test.csv"])
        assert "source_files" in manifest
        assert manifest["source_files"]["cascade_sweep"]["sha256"] is not None
        assert len(manifest["source_files"]["cascade_sweep"]["sha256"]) == 64

    def test_includes_both_config_snapshots(self) -> None:
        d = _make_input_dir()
        output_dir = d / "output"
        output_dir.mkdir(exist_ok=True)
        manifest = make_manifest(d, output_dir, ["test.csv"])
        assert "benchmark_config_snapshot" in manifest
        assert "per_stage_config_snapshots" in manifest
        assert "cascade" in manifest["benchmark_config_snapshot"]

    def test_includes_git_commit(self) -> None:
        d = _make_input_dir()
        output_dir = d / "output"
        output_dir.mkdir(exist_ok=True)
        manifest = make_manifest(d, output_dir, ["test.csv"])
        assert "git_commit" in manifest
        assert isinstance(manifest["git_commit"], str)


class TestWriteOutputs:
    def test_writes_csv_and_json(self) -> None:
        output_dir = TEST_DIR / "write_test"
        output_dir.mkdir(exist_ok=True)
        outputs = {
            "test.csv": pd.DataFrame({"a": [1, 2], "b": [3, 4]}),
            "test.json": {"key": "value"},
        }
        written = write_outputs(output_dir, outputs)
        assert len(written) == 2
        assert "test.csv" in written
        assert "test.json" in written
        assert (output_dir / "test.csv").exists()
        assert (output_dir / "test.json").exists()


class TestEndToEnd:
    def test_cli_generates_all_outputs(self) -> None:
        d = _make_input_dir()
        output_dir = TEST_DIR / "output"
        main(["--input-dir", str(d), "--output-dir", str(output_dir)])
        expected = [
            "cascade_optimized_summary.csv",
            "ldpc_optimized_summary.csv",
            "qldpc_reference_summary.csv",
            "scalability_summary.csv",
            "method_comparison_by_frame_len.csv",
            "failure_region_analysis.csv",
            "expanded_evidence_manifest.json",
        ]
        for name in expected:
            assert (output_dir / name).exists(), f"Missing: {name}"

    def test_idempotent(self) -> None:
        d = _make_input_dir()
        output_dir = TEST_DIR / "output"
        main(["--input-dir", str(d), "--output-dir", str(output_dir)])
        hashes1 = {}
        for f in output_dir.iterdir():
            hashes1[f.name] = compute_file_hash(f)
        main(["--input-dir", str(d), "--output-dir", str(output_dir)])
        hashes2 = {}
        for f in output_dir.iterdir():
            hashes2[f.name] = compute_file_hash(f)
        assert hashes1 == hashes2


class TestGracefulDegradation:
    def test_missing_files_skip_outputs(self) -> None:
        d = TEST_DIR / "empty_input"
        d.mkdir(exist_ok=True)
        output_dir = TEST_DIR / "output"
        with pytest.warns(UserWarning, match="not found"):
            main(["--input-dir", str(d), "--output-dir", str(output_dir)])
