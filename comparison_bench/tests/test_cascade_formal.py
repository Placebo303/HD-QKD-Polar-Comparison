from __future__ import annotations

import unittest
from collections import Counter

import numpy as np

import comparison_bench.src.comparison_bench.formal_ir.cascade as cascade
from comparison_bench.src.comparison_bench.formal_ir.cascade import run_cascade_formal
from comparison_bench.src.comparison_bench.formal_ir.shared import seed_record, transcript_summary


class CascadeFormalTest(unittest.TestCase):
    def setUp(self):
        self.a = np.zeros(64, dtype=np.int64); self.seed = seed_record(np.arange(703, dtype=np.uint8) % 2)

    def execute(self, b, **kw): return run_cascade_formal(self.a, b, dimension=1024, dataset_id="d", frame_id="f", locked_seed=kw.pop("locked_seed", self.seed), **kw)

    def test_noiseless_single_error_and_determinism(self):
        clean = self.execute(self.a.copy()); self.assertEqual(clean["outcome"]["status"], "verified_success")
        b = self.a.copy(); b[0] = 1
        one = self.execute(b, include_private_diagnostics=True); again = self.execute(b)
        self.assertEqual(one["outcome"]["status"], "verified_success")
        self.assertEqual(one["private_diagnostics"]["corrected_positions"], [9])  # q=1024 MSB-first: symbol 0 bit 9
        self.assertNotIn("private_diagnostics", again)
        self.assertEqual(one["outcome"]["transcript_sha256"], again["outcome"]["transcript_sha256"])
        self.assertTrue(all("corrected" not in str(e["payload"]).lower() and "raw" not in str(e["payload"]).lower() for e in one["events"]))

    def test_events_accounting_lookback_and_verify_failure(self):
        b = self.a.copy(); b[[0, 2, 4]] = [1, 2, 4]
        r = self.execute(b)
        self.assertTrue(any(e["event_type"] == "LOOKBACK_RECHECK" and e["key_dependent_bits"] == 0 for e in r["events"]))
        self.assertTrue(all(e["direction"] in {"alice_to_bob", "bob_local", "control"} for e in r["events"]))
        self.assertEqual(r["outcome"]["key_dependent_disclosure_bits_total"], transcript_summary(r["events"])["key_dependent_disclosure_bits_total"])
        self.assertTrue(all(e["parent_event_id"] is None or e["parent_event_id"] < e["event_id"] for e in r["events"]))
        old = cascade.verification_result
        try:
            cascade.verification_result = lambda *args, **kwargs: {"verification_invoked": True, "verification_tag_bits": 64, "public_control_bits": 703, "epsilon_ec": 2.0 ** -64, "verified": False}
            bad = self.execute(self.a.copy())
            self.assertEqual(bad["outcome"]["status"], "verify_failed")
        finally:
            cascade.verification_result = old
        out = r["outcome"]
        self.assertEqual(out["cascade_parity_bits"] + out["cascade_primary_bisection_bits"] + out["cascade_lookback_bits"] + out["verification_tag_bits_component"], out["key_dependent_disclosure_bits_total"])

    def test_completed_pass_only_lookback_and_reentry(self):
        # Offline-found fixed q=2 vector; no random search occurs in the test.
        a = np.zeros(64, dtype=np.int64); b = a.copy(); b[[27, 21, 22, 18]] = 1
        r = run_cascade_formal(a, b, dimension=2, mapping="natural", locked_seed=seed_record(np.arange(127, dtype=np.uint8) % 2))
        seen = Counter((e["pass_id"], e["block_id"]) for e in r["events"] if e["event_type"] == "LOOKBACK_RECHECK")
        self.assertGreaterEqual(seen[(0, 1)], 2)  # popped, removed from pending, then re-enqueued
        primary_pass = -1
        for e in r["events"]:
            if e["event_type"] == "BLOCK_PARITY": primary_pass = e["pass_id"]
            if e["event_type"] == "LOOKBACK_RECHECK": self.assertLess(e["pass_id"], primary_pass)

    def test_caps_and_invalid(self):
        b = self.a.copy(); b[0] = 1
        for cap, value in (("events", 1), ("corrections", 0), ("wall_s", -1)):
            r = self.execute(b, caps={cap: value})
            self.assertEqual(r["outcome"]["status"], "aborted_resource_limit")
            self.assertEqual(r["outcome"]["failure_reason"], cap)
            self.assertEqual(r["events"][-1]["event_type"], "ABORT")
        multi = self.a.copy(); multi[[0, 2, 4]] = [1, 2, 4]
        r = self.execute(multi, caps={"queue_pops": 0})
        self.assertEqual((r["outcome"]["status"], r["outcome"]["failure_reason"]), ("aborted_resource_limit", "queue_pops"))
        r = run_cascade_formal([0] * 63, [0] * 63, dimension=3)
        self.assertEqual(r["outcome"]["status"], "invalid_input")
        r = run_cascade_formal(np.zeros(64, dtype=int), np.zeros(64, dtype=int), dimension=3, locked_seed=self.seed)
        self.assertEqual(r["outcome"]["status"], "unsupported_domain")
        r = self.execute(self.a.copy(), locked_seed=None)
        self.assertEqual(r["outcome"]["status"], "invalid_input")
        normal = self.execute(self.a.copy())
        r = self.execute(self.a.copy(), caps={"events": len(normal["events"]) - 1})
        self.assertEqual(r["outcome"]["status"], "aborted_resource_limit")
        self.assertFalse(r["outcome"]["verification_invoked"])
        self.assertFalse(any(e["event_type"].startswith("VERIFICATION_") for e in r["events"]))
