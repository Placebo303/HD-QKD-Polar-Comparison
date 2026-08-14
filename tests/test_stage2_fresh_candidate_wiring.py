from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "pipelines" / "current" / "routeA_run_formal_cross_loss.py"
SPEC = importlib.util.spec_from_file_location("routeA_run_formal_cross_loss", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class Stage2FreshCandidateTests(unittest.TestCase):
    def test_stage0_candidate_requires_recomputed_results_csv(self) -> None:
        replay_index = REPO_ROOT / "workspace" / "_stage2_wiring_test_replay"
        candidate = Path("e2e_20dB_fullgrid_pairing_v2_candidate_t15")
        fresh = replay_index / "_recomputed_replay_inputs" / candidate.name
        try:
            fresh.mkdir(parents=True)
            with self.assertRaises(SystemExit):
                MODULE._fresh_recomputed_candidate_dir(replay_index, candidate)
            (fresh / "polar_e2e_results.csv").write_text("dimension,bin_width_ps\n4,20\n", encoding="utf-8")
            self.assertEqual(MODULE._fresh_recomputed_candidate_dir(replay_index, candidate), fresh)
        finally:
            import shutil

            shutil.rmtree(replay_index, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
