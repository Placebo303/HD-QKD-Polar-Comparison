from __future__ import annotations

import csv
import os
import shutil
import subprocess
import sys
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import numpy as np

from src.reconciliation.verification import verification_transcript
from src.runtime_paths import default_project_results_root, repo_relative_results_path, windows_to_wsl_path
from tools.verify_authoritative_results import pack_digest


REPO_ROOT = Path(__file__).resolve().parents[1]


@contextmanager
def _workspace_tempdir():
    path = REPO_ROOT / "workspace" / f"_test_{uuid.uuid4().hex}"
    path.mkdir(parents=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class SmokeTests(unittest.TestCase):
    def test_active_docs_do_not_embed_local_repo_paths_or_foreign_cli(self) -> None:
        active_docs = [
            REPO_ROOT / "README.md",
            REPO_ROOT / "docs" / "CURRENT_MAINLINE.md",
            REPO_ROOT / "docs" / "LATEST_RESULTS_20260327.md",
            REPO_ROOT / "docs" / "POLAR_CODE_MAINFLOW_20260327.md",
            REPO_ROOT / "docs" / "RESULTS_MANIFEST_20260427.md",
        ]
        forbidden = [
            "/D:/Code/HD-QKD_Polar_Release/",
            r"D:\Code\HD-QKD_Polar_Release",
            "--data-provider",
            "--skip-llm",
            "--operator-gate",
            "yfinance",
        ]
        for path in active_docs:
            text = path.read_text(encoding="utf-8")
            for token in forbidden:
                self.assertNotIn(token, text, f"{token!r} found in {path}")

    def test_runtime_paths_respect_results_override(self) -> None:
        repo = Path("repo-root")
        with patch.dict(os.environ, {"PROJECT_RESULTS_ROOT": "custom-results"}):
            self.assertEqual(default_project_results_root(repo), Path("custom-results"))
            self.assertEqual(
                repo_relative_results_path(repo, r"results\authoritative\pack"),
                Path("custom-results") / "authoritative" / "pack",
            )
        self.assertEqual(windows_to_wsl_path(r"D:\Data\Raw Data\x.ttbin"), "/mnt/d/Data/Raw Data/x.ttbin")

    def test_universal_hash_transcript(self) -> None:
        bits = np.array([1, 0, 1, 1, 0, 0], dtype=np.uint8)
        transcript = verification_transcript(
            reference_bits=bits,
            candidate_bits=bits.copy(),
            toeplitz_seed_bits=np.zeros(bits.size + 32 - 1, dtype=np.uint8),
            tag_bits=32,
        )
        self.assertEqual(transcript["verification_pass_flag"], 1)
        self.assertEqual(transcript["verification_fail_flag"], 0)
        self.assertEqual(transcript["verification_bits_used_actual"], 32)

    def test_authoritative_pack_digest_is_deterministic(self) -> None:
        with _workspace_tempdir() as tmp:
            pack = tmp / "pack"
            (pack / "nested").mkdir(parents=True)
            (pack / "a.txt").write_text("alpha\n", encoding="utf-8")
            (pack / "nested" / "b.bin").write_bytes(b"\x00\x01\x02")
            first = pack_digest(pack, workers=2)
            second = pack_digest(pack, workers=1)
            self.assertEqual(first, second)
            self.assertEqual(first["file_count"], 2)
            expected_bytes = sum(path.stat().st_size for path in pack.rglob("*") if path.is_file())
            self.assertEqual(first["total_bytes"], expected_bytes)

    def test_finite_key_builder_with_small_fixture(self) -> None:
        with _workspace_tempdir() as root:
            candidate = root / "candidate_20dB"
            actual = root / "actual_ir"
            output = root / "output"
            _write_csv(
                candidate / "polar_e2e_results.csv",
                [{
                    "dimension": 4,
                    "bin_width_ps": 20,
                    "map_ser": 0.1,
                    "coincidence_rate_hz": 1000.0,
                    "best_hard_PIE": 1.0,
                    "PIE_practical": 0.9,
                    "SKR_measured_bps": 900.0,
                    "layers_success_best": 2,
                    "clean_pair_fraction": 0.75,
                }],
            )
            _write_csv(
                candidate / "polar_diag_summary.csv",
                [{
                    "dimension": 4,
                    "bin_width_ps": 20,
                    "raw_ser": 0.1,
                    "near_neighbor_frac": 0.8,
                    "n_pairs_actual": 1000,
                    "frame_diag_available": 1,
                }],
            )
            _write_csv(
                actual / "actual_ir_point_table.csv",
                [{
                    "loss_db": 20,
                    "dimension": 4,
                    "bin_width_ps": 20,
                    "n_pairs_actual": 1000,
                    "total_leak_ec_bits": 100,
                    "leak_ec_source_tag": "actual_ir_replay_formal",
                    "total_kept_info_bits": 1800,
                    "frame_success_rate": 0.8,
                    "verification_accept_rate": 0.9,
                    "block_success_rate": 0.5,
                    "epsilon_EC_bound": 1e-9,
                }],
            )
            command = [
                sys.executable,
                str(REPO_ROOT / "tools" / "security_reports" / "round2_build_finite_key_audit_table.py"),
                "--input-dirs",
                str(candidate),
                str(actual),
                "--output-dir",
                str(output),
            ]
            completed = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            with (output / "finite_key_audit_point_table.csv").open(newline="", encoding="utf-8") as stream:
                row = next(csv.DictReader(stream))
            self.assertAlmostEqual(float(row["leak_EC_actual_bits"]), 0.1)
            self.assertAlmostEqual(float(row["accepted_frame_fraction"]), 0.8)
            self.assertAlmostEqual(float(row["n_eff_pairs"]), 720.0)
            self.assertEqual(row["n_eff_pairs_rule"], "block_success_already_in_actual_kept_bits")
            self.assertEqual(row["block_success_rate_source_tag"], "actual_verification_accept_rate")
            self.assertEqual(row["leak_EC_source_tag"], "actual_ir_replay_formal")


if __name__ == "__main__":
    unittest.main()
