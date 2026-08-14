from __future__ import annotations

import copy
import unittest

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.ldpc import calibrate_rates, canonical_matrix_bytes
from comparison_bench.src.comparison_bench.formal_ir.codebook_v2 import PREFIX_RATES, codebook_filename, generate_master, screening_manifest, verify_v2_codebook_entry
from comparison_bench.src.comparison_bench.formal_ir.ldpc_v2 import (
    METHOD, _run_ldpc_formal_v2_for_test, canonical_policy, decoder_params,
    effective_rate, policy_grid, probe_constructors, select_global_policy,
)
from comparison_bench.src.comparison_bench.formal_ir.shared import seed_record


class _ZeroDecoder:
    seen: list[dict] = []
    def __init__(self, h, **params): self.h, self.params = h, params; type(self).seen.append(params)
    def decode(self, syndrome): return np.zeros(64, dtype=np.uint8)


class LdpcFormalV2Test(unittest.TestCase):
    def setUp(self):
        self.seed = seed_record(np.arange(127, dtype=np.uint8) % 2)
        zeros = np.zeros((2, 64), dtype=np.int64)
        self.cal = calibrate_rates({"d": (zeros, zeros.copy())}, sacrificed_frame_keys={"d": ["d:cal0", "d:cal1"]}, calibration_role="sacrificed_tuning_only", mapping="natural", source_bytes=b"sacrificed", dimension=2)
        self.screening = screening_manifest()
        selected = {row["plane_id"]: row["selected_candidate_id"] for row in self.screening["planes"]}
        self.entries, self.bytes = {}, {}
        for plane, candidate in selected.items():
            master = generate_master(plane, candidate)
            for rate, rows in zip(PREFIX_RATES, (32, 40, 48, 56)):
                raw = canonical_matrix_bytes(master[:rows]); entry = {"filename": codebook_filename(rate, plane), "rate_id": rate, "plane_id": plane, "m_checks": rows, "n": 64, "rank": rows, "sha256": __import__("hashlib").sha256(raw).hexdigest(), "selected_candidate_id": candidate}
                self.entries[(rate, plane)], self.bytes[(rate, plane)] = entry, raw
        self.policy = canonical_policy(rate_margin=1, osd_method="OSD_CS", osd_order=2)

    def execute(self, alice=None, bob=None, **kwargs):
        alice = np.zeros(64, dtype=np.int64) if alice is None else alice
        bob = alice.copy() if bob is None else bob
        return _run_ldpc_formal_v2_for_test(alice, bob, dimension=2, mapping="natural", frozen_calibration=self.cal, frozen_policy=self.policy, codebook_entries=self.entries, codebook_bytes=self.bytes, screening_manifest=self.screening, dataset_id="d", locked_seed=self.seed, _preflight={"status": "ok"}, _decoder_factory=kwargs.pop("_decoder_factory", _ZeroDecoder), **kwargs)

    def test_v2_entry_validation_rejects_v1_and_tampering(self):
        entry, raw = self.entries[("r050", 0)], self.bytes[("r050", 0)]
        self.assertEqual(verify_v2_codebook_entry(entry, raw, self.screening).shape, (32, 64))
        for mutate in (lambda e, b: (dict(e, filename="v1_codebook.hgf2v1"), b), lambda e, b: (dict(e, sha256="0" * 64), b), lambda e, b: (dict(e, selected_candidate_id=e["selected_candidate_id"] + 1), b), lambda e, b: (e, b[:-1] + bytes([b[-1] ^ 1]))):
            bad_entry, bad_raw = mutate(entry, raw)
            with self.assertRaises(ValueError): verify_v2_codebook_entry(bad_entry, bad_raw, self.screening)

    def test_exact_grid_hash_and_rate_margin(self):
        grid = policy_grid()
        self.assertEqual(len(grid), 9)
        self.assertEqual({(row["rate_margin"], row["osd_method"], row["osd_order"]) for row in grid}, {(margin, method, order) for margin in (0, 1, 2) for method, order in (("OSD_0", 0), ("OSD_CS", 1), ("OSD_CS", 2))})
        self.assertEqual(canonical_policy(rate_margin=1, osd_method="OSD_CS", osd_order=2), self.policy)
        self.assertEqual([effective_rate(.10, margin) for margin in (0, 1, 2)], ["r0375", "r025", "r0125"])
        self.assertEqual(effective_rate(.20, 2), "r0125")
        with self.assertRaises(ValueError): canonical_policy(rate_margin=0, osd_method="OSD_1", osd_order=1)

    def test_constructor_probes_are_real_and_bounded(self):
        seen = []
        class Capture:
            def __init__(self, h, **params): seen.append(params)
        probes = probe_constructors(decoder_factory=Capture, dependency_version="2.4.1")
        self.assertEqual([(row["osd_method"], row["osd_order"]) for row in probes], [("OSD_0", 0), ("OSD_CS", 1), ("OSD_CS", 2)])
        self.assertTrue(all(row["supported"] for row in probes))
        self.assertEqual([(row["osd_method"], row["osd_order"]) for row in seen], [("OSD_0", 0), ("OSD_CS", 1), ("OSD_CS", 2)])

    def test_global_selection_and_no_per_frame_oracle(self):
        outcomes = {policy["policy_id"]: [{"status": "verified_success", "key_dependent_disclosure_bits_total": 100, "runtime_ns": 20}] for policy in policy_grid()}
        best = policy_grid()[-1]; outcomes[best["policy_id"]] = [{"status": "verified_success", "key_dependent_disclosure_bits_total": 99, "runtime_ns": 30}]
        selected = select_global_policy(outcomes)
        self.assertEqual(selected["selected_policy"], best)
        runtime_only = {policy["policy_id"]: [{"status": "verified_success", "key_dependent_disclosure_bits_total": 100, "runtime_ns": 1}] for policy in policy_grid()}
        slow = policy_grid()[0]
        runtime_only[slow["policy_id"]][0]["runtime_ns"] = 10**18
        first = select_global_policy(runtime_only)
        runtime_only[slow["policy_id"]][0]["runtime_ns"] = 0
        for policy in policy_grid()[1:]:
            runtime_only[policy["policy_id"]][0]["runtime_ns"] = 10**18
        second = select_global_policy(runtime_only)
        self.assertEqual(first["selected_policy"], second["selected_policy"])
        self.assertEqual(first["selection_tuple"][:3], [-1, 100, 0])
        self.assertNotEqual(first["aggregates"][slow["policy_id"]]["runtime_ns"], second["aggregates"][slow["policy_id"]]["runtime_ns"])
        _ZeroDecoder.seen.clear(); clean = self.execute(); noisy = self.execute(bob=np.ones(64, dtype=np.int64))
        self.assertEqual(clean["outcome"]["policy_id"], noisy["outcome"]["policy_id"])
        self.assertEqual(clean["outcome"]["rate_ids"], noisy["outcome"]["rate_ids"])
        self.assertEqual(_ZeroDecoder.seen[0], decoder_params(self.policy, 0.0))

    def test_disclosure_and_failure_status_are_retained(self):
        got = self.execute(); out = got["outcome"]
        self.assertEqual((out["method"], out["status"], out["rate_ids"]), (METHOD, "verified_success", ["r0375"]))
        self.assertEqual((out["ldpc_syndrome_bits"], out["key_dependent_disclosure_bits_total"]), (40, 104))
        self.assertEqual(out["public_control_bits_total"], 256 + 40 + 127)
        class Bad(_ZeroDecoder):
            def decode(self, syndrome): return np.ones(64, dtype=np.uint8)
        failed = self.execute(_decoder_factory=Bad)["outcome"]
        self.assertEqual((failed["status"], failed["attempted"], failed["denominator_included"]), ("syndrome_inconsistent", True, True))
