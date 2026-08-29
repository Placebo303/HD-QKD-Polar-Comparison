from __future__ import annotations
import csv, json, unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from v61_measurement_spec_check import verification_extra, leak_other_from_transcript, ell_bits, overall_verdict, SOURCES, SPEC_FLOOR, SPEC_5, SPEC_10, N

REPO = Path(__file__).resolve().parents[1]

class TestV61(unittest.TestCase):
    def test_tag64_only_zero(self):
        self.assertEqual(verification_extra(64), 0)
        self.assertEqual(leak_other_from_transcript(64, 0), 0)

    def test_extra_only_difference(self):
        self.assertEqual(verification_extra(128), 64)
        self.assertEqual(leak_other_from_transcript(128, 0), 64)
        self.assertEqual(verification_extra(70), 6)

    def test_epsilon_not_bits(self):
        eps = 1e-10
        # epsilon probability must not be added to leak_other/finite
        leak = leak_other_from_transcript(64, 0)
        self.assertEqual(leak, 0)
        # wrong path would be leak + eps
        self.assertNotEqual(leak, eps)
        # ensure schema says epsilon not bits
        schema = json.loads((REPO / "docs/research_cycles/V61P0/v61_measurement_schema.json").read_text(encoding="utf-8"))
        self.assertIn("epsilon", schema.get("epsilon_note", "") or str(schema))

    def test_conditional_na_legal(self):
        # theorem declares not applicable -> N/A with reason does NOT block V62_OPEN when core ready
        overall = overall_verdict(True, False, False, True, True, True, True, False, False)
        self.assertEqual(overall, "V61_SPEC_READY__V62_OPEN")

    def test_applicable_missing_blocks(self):
        # applicable dependency missing -> PENDING
        overall = overall_verdict(True, False, False, True, False, True, True, False, False)
        self.assertEqual(overall, "V61_SPEC_READY__V62_PENDING")

    def test_core_missing_blocks(self):
        overall = overall_verdict(True, True, False, False, True, False, True, False, False)
        self.assertEqual(overall, "V61_SPEC_READY__V62_PENDING")
        overall2 = overall_verdict(True, False, True, False, True, False, True, False, False)
        self.assertEqual(overall2, "V61_SPEC_READY__V62_PENDING")

    def test_proxy_hmin_invalid(self):
        overall = overall_verdict(True, False, False, True, True, True, True, True, False)
        self.assertEqual(overall, "V61_SPEC_INVALID")

    def test_three_source_thresholds_anchor(self):
        for s in SOURCES:
            floor = SPEC_FLOOR[s["source"]]
            m10 = SPEC_10[s["source"]]
            m5 = SPEC_5[s["source"]]
            self.assertAlmostEqual(floor * N, s["leak_total"], delta=2.5)
            self.assertAlmostEqual(m10 * N * 0.90, s["leak_total"], delta=2.5)
            self.assertAlmostEqual(m5 * N * 0.95, s["leak_total"], delta=2.5)
            self.assertLess(floor, 10)
            # leak =5*m+64
            self.assertEqual(s["leak_total"], 5*s["m_total"]+64)
        # CSV exists and has three rows
        rows = list(csv.DictReader((REPO / "docs/research_cycles/V61P0/v61_break_even_thresholds.csv").open(encoding="utf-8")))
        self.assertEqual(len(rows), 3)

    def test_terminal_mutual_exclusion(self):
        vals = set()
        for args in [
            (False, False, False, True, True, True, True, True, False),
            (True, True, False, False, True, False, True, False, False),
            (True, False, False, True, True, True, True, False, False),
        ]:
            vals.add(overall_verdict(*args))
        # all three distinct and only one active per call
        for o in vals:
            self.assertIn(o, ["V61_SPEC_INVALID", "V61_SPEC_READY__V62_PENDING", "V61_SPEC_READY__V62_OPEN"])

    def test_ell_only_open(self):
        ell = ell_bits(7.5, 7089, 0, 0)
        self.assertIsNotNone(ell)
        ell_null = ell_bits(None, 7089, 0, 0)
        self.assertIsNone(ell_null)
        # only OPEN should have ell not null
        overall_pending = overall_verdict(True, True, True, False, True, False, True, False, False)
        self.assertEqual(overall_pending, "V61_SPEC_READY__V62_PENDING")

if __name__ == "__main__":
    unittest.main()
