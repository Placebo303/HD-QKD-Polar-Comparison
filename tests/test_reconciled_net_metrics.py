import unittest
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "tools" / "security_reports"))

from tools.security_reports.round2_build_finite_key_audit_table import compute_reconciled_net
from tools.security_reports.round2_build_security_round2_summary import apply_reconciled_main_mapping


class ReconciledNetMetricsTests(unittest.TestCase):
    def test_formula_uses_total_bits_over_actual_pairs(self):
        result = compute_reconciled_net(
            total_kept_info_bits=1800,
            total_leak_ec_bits=100,
            n_pairs_actual=1000,
            coincidence_rate_hz=50,
            leak_source_tag="actual_ir_replay_formal",
            coincidence_rate_verified=True,
        )
        self.assertAlmostEqual(result["PIE_reconciled_net"], 1.7)
        self.assertAlmostEqual(result["SKR_reconciled_net_bps"], 85.0)
        self.assertEqual(result["reconciliation_evidence_status"], "verified_actual_ir_replay_reconciled_net")
        self.assertEqual(result["claim_boundary"], "public_ec_only_not_secure")

    def test_missing_actual_replay_or_pairs_or_rate_is_blocked(self):
        for kwargs in (
            dict(total_kept_info_bits=1800, total_leak_ec_bits=100, n_pairs_actual=1000, coincidence_rate_hz=50, leak_source_tag="surrogate_proxy"),
            dict(total_kept_info_bits=1800, total_leak_ec_bits=100, n_pairs_actual=0, coincidence_rate_hz=50, leak_source_tag="actual_ir_replay_formal"),
            dict(total_kept_info_bits=1800, total_leak_ec_bits=100, n_pairs_actual=1000, coincidence_rate_hz=np.nan, leak_source_tag="actual_ir_replay_formal"),
        ):
            result = compute_reconciled_net(**kwargs)
            self.assertTrue(pd.isna(result["PIE_reconciled_net"]))
            self.assertTrue(pd.isna(result["SKR_reconciled_net_bps"]))
            self.assertTrue(str(result["reconciliation_evidence_status"]).startswith("blocked_"))

    def test_main_mapping_uses_reconciled_columns(self):
        mapped = apply_reconciled_main_mapping(
            pd.DataFrame(
                {
                    "PIE_secure_actual_ir": [99.0],
                    "SKR_secure_actual_ir_bps": [999.0],
                    "PIE_reconciled_net": [1.7],
                    "SKR_reconciled_net_bps": [85.0],
                }
            )
        )
        self.assertEqual(mapped.loc[0, "PIE_main"], 1.7)
        self.assertEqual(mapped.loc[0, "SKR_main_bps"], 85.0)
        self.assertEqual(mapped.loc[0, "main_result_source"], "actual_ir_reconciled_net_not_secure")
        self.assertEqual(mapped.loc[0, "main_result_claim"], "public_ec_only_reconciled_net_not_secret_key_rate")

    def test_unverified_rate_is_blocked(self):
        result = compute_reconciled_net(
            total_kept_info_bits=1800,
            total_leak_ec_bits=100,
            n_pairs_actual=1000,
            coincidence_rate_hz=50,
            leak_source_tag="actual_ir_replay_formal",
            coincidence_rate_verified=False,
        )
        self.assertEqual(result["reconciliation_evidence_status"], "blocked_missing_verified_coincidence_rate")
        self.assertTrue(pd.isna(result["PIE_reconciled_net"]))


if __name__ == "__main__":
    unittest.main()
