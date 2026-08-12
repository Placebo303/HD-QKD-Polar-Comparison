from __future__ import annotations

import hashlib
import importlib.metadata
import unittest

import numpy as np
import pandas as pd

from comparison_bench.src.comparison_bench.formal_ir.shared import (
    FORMAL_ARTIFACTS, canonical_event, formal_bp_osd_params, frame_provenance, locked_seed_bits, materialize_seed_record,
    pack_bits_msb, preflight_ldpc, seed_record, status_flags, toeplitz_tag,
    transcript_summary, validate_pair_table, verification_result, verification_union_bound,
)


class FormalVerificationTest(unittest.TestCase):
    def test_contract_status_and_preflight_fail_closed(self):
        self.assertEqual(len(FORMAL_ARTIFACTS), 6)
        self.assertEqual(status_flags("preflight_unavailable"), (False, False))
        self.assertEqual(status_flags("decode_failed"), (True, True))
        observed = preflight_ldpc()
        if importlib.metadata.version("ldpc") == "2.4.1":
            self.assertEqual((observed["status"], observed["missing_api_params"], observed["constructor_probe_ok"]), ("ok", [], True))
        else:
            self.assertEqual(observed["status"], "preflight_unavailable")
        self.assertEqual(formal_bp_osd_params(.2)["serial_schedule_order"], list(range(64)))
        incomplete = preflight_ldpc(dependency_version="2.4.1", api_description="error_rate max_iter")
        self.assertEqual(incomplete["status"], "preflight_unavailable")
        self.assertIn("bp_method", incomplete["missing_api_params"])
        api = " ".join(("error_rate", "max_iter", "bp_method", "ms_scaling_factor", "schedule", "omp_thread_count", "serial_schedule_order", "osd_method", "osd_order"))
        complete = preflight_ldpc(dependency_version="2.4.1", api_description=api, decoder_constructor=lambda _h, **_kwargs: object())
        self.assertEqual(complete["status"], "ok")
        self.assertNotIn("random_serial_schedule", formal_bp_osd_params(.2))
        captured = {}
        def rejecting_constructor(_h, **kwargs):
            captured.update(kwargs)
            raise ValueError("unsupported advertised keyword")
        rejected = preflight_ldpc(dependency_version="2.4.1", api_description=api, decoder_constructor=rejecting_constructor)
        self.assertEqual((rejected["status"], rejected["probe_error_class"]), ("preflight_unavailable", "ValueError"))
        self.assertEqual(captured["serial_schedule_order"], list(range(64)))
        self.assertNotIn("random_serial_schedule", captured)

    def test_golden_toeplitz_vector_and_seed_id(self):
        x = np.unpackbits(np.frombuffer(bytes.fromhex("0123456789abcdef"), dtype=np.uint8), bitorder="big")
        raw = bytes.fromhex("192a7c4d8615633fcd4ff3fdaafa622e")
        seed = np.unpackbits(np.frombuffer(raw, dtype=np.uint8), bitorder="big")[:127]
        self.assertEqual(hashlib.sha256(raw).hexdigest(), "46b785fc4ffa59c18eb9bafa71f7399fe48870ded7d3d5a6b7fdaecda8638b84")
        self.assertEqual(toeplitz_tag(x, seed).hex(), "6e0cf65a8a33be65")

    def test_fixed_unequal_vector_rejects_and_locked_seed_is_read_only(self):
        alice = np.zeros(64, dtype=np.uint8); bob = alice.copy(); bob[3] = 1
        record = seed_record(np.arange(127, dtype=np.uint8) % 2)
        self.assertFalse(verification_result(alice, bob, record, invoked=True)["verified"])
        self.assertTrue(np.array_equal(locked_seed_bits(record, 127), np.arange(127, dtype=np.uint8) % 2))
        with self.assertRaises(ValueError): locked_seed_bits({**record, "seed_id": "0" * 64}, 127)

    def test_non_byte_seed_materialization_masks_unused_low_bits(self):
        for _ in range(12):
            record = materialize_seed_record(703)
            raw = bytes.fromhex(record["seed_hex"])
            self.assertEqual((record["seed_bit_length"], len(raw), raw[-1] & 1), (703, 88, 0))
            self.assertEqual(len(locked_seed_bits(record, 703)), 703)

    def test_not_invoked_is_zero_and_crc_is_not_authoritative(self):
        record = seed_record(np.zeros(127, dtype=np.uint8))
        result = verification_result(np.zeros(64), np.zeros(64), record, invoked=False)
        self.assertEqual((result["verification_tag_bits"], result["public_control_bits"], result["epsilon_ec"]), (0, 0, 0.0))
        self.assertFalse(result["verified"])
        self.assertEqual(verification_union_bound(0), 0.0)

    def test_canonical_jsonl_disclosure_and_payload_secrecy(self):
        event = {"event_id": 1, "frame_key": "d:f", "method": "cascade_formal_v1", "event_type": "BLOCK_PARITY", "direction": "alice_to_bob", "parent_event_id": None, "pass_id": 0, "block_id": 0, "key_dependent_bits": 1, "public_control_bits": 2, "payload": {"parity": 1, "block_range": [0, 16]}}
        self.assertEqual(canonical_event(event), b'{"block_id":0,"direction":"alice_to_bob","event_id":1,"event_type":"BLOCK_PARITY","frame_key":"d:f","key_dependent_bits":1,"method":"cascade_formal_v1","parent_event_id":null,"pass_id":0,"payload":{"block_range":[0,16],"parity":1},"public_control_bits":2}\n')
        summary = transcript_summary([event])
        self.assertEqual(summary["key_dependent_disclosure_bits_total"], 1)
        with self.assertRaises(ValueError): canonical_event({**event, "payload": {"corrected_raw_index": 3}})
        missing_pass = dict(event); missing_pass.pop("pass_id")
        with self.assertRaises(ValueError): canonical_event(missing_pass)

    def test_provenance_requires_exact_ordered_64_pairs(self):
        table = pd.DataFrame({"dataset_id": ["d"] * 64, "frame_id": ["f"] * 64, "pair_idx": list(range(64)), "alice_symbol": [0] * 64, "bob_symbol": [0] * 64})
        checked = validate_pair_table(table, b"source")
        self.assertEqual(len(frame_provenance(checked)[0]["atomic_pair_keys"]), 64)
        bad = table.copy(); bad.loc[63, "pair_idx"] = 62
        with self.assertRaises(ValueError): validate_pair_table(bad)
        shuffled = table.sample(frac=1, random_state=1).reset_index(drop=True)
        with self.assertRaises(ValueError): validate_pair_table(shuffled)
