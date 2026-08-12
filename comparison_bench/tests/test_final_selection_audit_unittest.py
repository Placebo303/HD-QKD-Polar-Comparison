import unittest

from comparison_bench.src.comparison_bench.final_selection_audit import decide_paired_outcome, exact_two_sided_binomial


class ExactPairedTest(unittest.TestCase):
    def test_one_discordant_pair_is_not_significant(self):
        self.assertEqual(exact_two_sided_binomial(1, 0), 1.0)

    def test_balanced_discordance_is_not_significant(self):
        self.assertEqual(exact_two_sided_binomial(3, 3), 1.0)

    def test_one_discordant_pair_is_no_decision(self):
        self.assertEqual(
            decide_paired_outcome(eligible=True, cascade_only_success=1, layered_ldpc_only_success=0, p_value=1.0, alpha=0.05)[0],
            "no_decision",
        )

    def test_significant_cascade_direction(self):
        p_value = exact_two_sided_binomial(6, 0)
        self.assertEqual(
            decide_paired_outcome(eligible=True, cascade_only_success=6, layered_ldpc_only_success=0, p_value=p_value, alpha=0.05)[0],
            "cascade_lite",
        )

    def test_significant_ldpc_direction(self):
        p_value = exact_two_sided_binomial(0, 6)
        self.assertEqual(
            decide_paired_outcome(eligible=True, cascade_only_success=0, layered_ldpc_only_success=6, p_value=p_value, alpha=0.05)[0],
            "layered_ldpc_lite",
        )

    def test_insufficient_evidence_when_gate_fails(self):
        self.assertEqual(
            decide_paired_outcome(eligible=False, cascade_only_success=6, layered_ldpc_only_success=0, p_value=0.03125, alpha=0.05)[0],
            "insufficient_evidence",
        )
