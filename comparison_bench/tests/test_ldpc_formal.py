from __future__ import annotations

import inspect
import json
import os
import tempfile
import unittest
from pathlib import Path

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.ldpc import (
    RATES, calibrate_rates, canonical_matrix_bytes, codebook_entry, generate_matrix,
    parse_matrix_bytes, run_ldpc_formal, select_rate, _syndrome,
    _run_ldpc_formal_for_test, materialize_codebooks, verify_codebook_manifest,
)
from comparison_bench.src.comparison_bench.formal_ir.shared import seed_record


class _ZeroDecoder:
    def __init__(self, h, **params): self.h, self.params = h, params
    def decode(self, syndrome): return np.zeros(64, dtype=np.uint8)


class _BadDecoder(_ZeroDecoder):
    def decode(self, syndrome): return np.ones(64, dtype=np.uint8)


class LdpcFormalTest(unittest.TestCase):
    def setUp(self):
        self.seed = seed_record(np.arange(127, dtype=np.uint8) % 2)
        a = np.zeros((2, 64), dtype=np.int64)
        self.cal = calibrate_rates({"d": (a, a.copy())}, sacrificed_frame_keys={"d": ["d:cal0", "d:cal1"]}, calibration_role="sacrificed_tuning_only", mapping="natural", source_bytes=b"sacrificed", dimension=2)
        self.entries = {(rate, p): codebook_entry(rate, p) for rate in RATES for p in range(10)}
        self.bytes = {(rate, p): canonical_matrix_bytes(generate_matrix(rate, p)) for rate in RATES for p in range(10)}
        self.ok = {"status": "ok"}

    def execute(self, a=None, b=None, **kw):
        a = np.zeros(64, dtype=np.int64) if a is None else a; b = a.copy() if b is None else b
        return _run_ldpc_formal_for_test(a, b, dimension=2, mapping="natural", frozen_calibration=kw.pop("frozen_calibration", self.cal), codebook_entries=self.entries, codebook_bytes=self.bytes, dataset_id="d", locked_seed=self.seed, _preflight=kw.pop("_preflight", self.ok), _decoder_factory=kw.pop("_decoder_factory", _ZeroDecoder), **kw)

    def test_all_rates_golden_parse_and_materialize(self):
        self.assertEqual(codebook_entry("r050", 0)["sha256"], "b73a2b73a1d1e63b4ea3817de7e839c8faa5aa0c1ff8687ae13eb1c78093f646")
        for rate, checks in RATES.items():
            h = generate_matrix(rate, 0); self.assertEqual(h.shape, (checks, 64)); self.assertEqual(parse_matrix_bytes(canonical_matrix_bytes(h)).shape, h.shape)
        bad = bytearray(self.bytes[("r050", 0)]); bad[-1] ^= 2
        with self.assertRaises(ValueError): parse_matrix_bytes(bytes(bad))
        wrong = dict(self.entries[("r050", 0)]); wrong["sha256"] = "0" * 64
        from comparison_bench.src.comparison_bench.formal_ir.ldpc import verify_codebook_entry
        with self.assertRaises(ValueError): verify_codebook_entry(wrong, self.bytes[("r050", 0)])
        with self.assertRaises(FileExistsError): materialize_codebooks(Path("."))

    def test_actual_materialize_manifest_and_no_overwrite(self):
        if os.environ.get("FORMAL_IR_FILE_TESTS") != "1":
            self.skipTest("set FORMAL_IR_FILE_TESTS=1 outside the Windows sandbox ACL")
        with tempfile.TemporaryDirectory(dir=".") as td:
            root = Path(td) / "run"
            manifest = materialize_codebooks(root)
            verify_codebook_manifest(root, manifest)
            self.assertEqual(len(list((root / "codebooks").glob("*.hgf2v1"))), 40)
            persisted = json.loads((root / "formal_codebook_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(persisted, manifest)
            with self.assertRaises(FileExistsError): materialize_codebooks(root)
            traversal = json.loads(json.dumps(manifest)); traversal["entries"][0]["filename"] = "../escape"
            with self.assertRaises(ValueError): verify_codebook_manifest(root, traversal)

    def test_plan_only_root_is_the_only_nonempty_materialization_input(self):
        if os.environ.get("FORMAL_IR_FILE_TESTS") != "1":
            self.skipTest("set FORMAL_IR_FILE_TESTS=1 outside the Windows sandbox ACL")
        with tempfile.TemporaryDirectory(dir=".") as td:
            root = Path(td) / "run"; root.mkdir(); (root / "pre_run_plan.json").write_text("{}", encoding="utf-8")
            materialize_codebooks(root, allow_plan_only=True)
            with self.assertRaises(FileExistsError): materialize_codebooks(root, allow_plan_only=True)
            other = Path(td) / "other"; other.mkdir(); (other / "extra.txt").write_text("x", encoding="utf-8")
            with self.assertRaises(FileExistsError): materialize_codebooks(other, allow_plan_only=True)

    def test_selector_calibration_and_confirmation_isolation(self):
        self.assertEqual([select_rate(p) for p in (.05, .10, .15, .20)], ["r050", "r0375", "r025", "r0125"])
        self.assertEqual(self.cal["source_sha256"], "e1f2b35f5e5404050cabc63211e913f8c34b8b23b74219b5da4a141c24a197c4")
        clean = self.execute(); noisy = self.execute(b=np.ones(64, dtype=np.int64))
        self.assertEqual(clean["outcome"]["rate_ids"], noisy["outcome"]["rate_ids"])
        self.assertEqual(clean["outcome"]["status"], "verified_success")
        with self.assertRaises(ValueError):
            calibrate_rates({"d": (np.zeros((1, 64), dtype=int), np.zeros((1, 64), dtype=int))}, sacrificed_frame_keys={"d": ["d:f"]}, calibration_role="confirmation", mapping="natural", source_bytes=b"x", dimension=2)
        captured = []
        class Capture(_ZeroDecoder):
            def __init__(self, h, **params): super().__init__(h, **params); captured.append(params)
        self.execute(_decoder_factory=Capture)
        first = dict(captured[0]); captured.clear()
        self.execute(b=np.ones(64, dtype=np.int64), _decoder_factory=Capture)
        self.assertEqual(first, captured[0])

    def test_calibration_provenance_and_tamper_fail_closed(self):
        dataset = self.cal["datasets"]["d"]
        self.assertEqual((dataset["keys_count"], dataset["ordered_frame_keys"]), (2, ["d:cal0", "d:cal1"]))
        self.assertNotEqual(dataset["selection_sha256"], self.cal["source_sha256"])
        for field, value in (("p_hat", .25), ("rate_id", "r0125"), ("errors", -1), ("selected_input_sha256", "0" * 64)):
            tampered = json.loads(json.dumps(self.cal))
            tampered["datasets"]["d"]["planes"]["0"][field] = value
            outcome = self.execute(frozen_calibration=tampered)["outcome"]
            self.assertEqual((outcome["status"], outcome["attempted"]), ("unsupported_domain", False))
        with self.assertRaises(ValueError):
            a = np.zeros((2, 64), dtype=int)
            calibrate_rates({"d": (a, a)}, sacrificed_frame_keys={"d": ["duplicate", "duplicate"]}, calibration_role="sacrificed_tuning_only", mapping="natural", source_bytes=b"x", dimension=2)

    def test_msb_planes_q2_q4_q8_q1024(self):
        self.assertEqual(_syndrome(np.array([[1, 0, 1], [0, 1, 1]], dtype=np.uint8), np.array([1, 0, 1], dtype=np.uint8)).tolist(), [0, 1])
        for q in (2, 4, 8, 1024):
            a = np.zeros((1, 64), dtype=np.int64)
            cal = calibrate_rates({"d": (a, a.copy())}, sacrificed_frame_keys={"d": ["d:cal0"]}, calibration_role="sacrificed_tuning_only", mapping="natural", source_bytes=f"q={q}".encode(), dimension=q)
            seed = seed_record(np.arange(64 * int(np.log2(q)) + 63, dtype=np.uint8) % 2)
            result = _run_ldpc_formal_for_test(a[0], a[0], dimension=q, mapping="natural", frozen_calibration=cal, codebook_entries=self.entries, codebook_bytes=self.bytes, dataset_id="d", locked_seed=seed, _preflight=self.ok, _decoder_factory=_ZeroDecoder)
            self.assertEqual((result["outcome"]["status"], len(result["outcome"]["rate_ids"])), ("verified_success", int(np.log2(q))))
            planes = int(np.log2(q))
            self.assertEqual(result["outcome"]["key_dependent_disclosure_bits_total"], planes * 32 + 64)
            self.assertEqual(result["outcome"]["public_control_bits_total"], planes * (256 + 32) + 64 * planes + 63)

    def test_statuses_disclosure_and_decoder_params(self):
        got = self.execute(); out = got["outcome"]
        self.assertEqual((out["status"], out["ldpc_syndrome_bits"], out["verification_tag_bits"]), ("verified_success", 32, 64))
        self.assertEqual(out["key_dependent_disclosure_bits_total"], 96)
        self.assertEqual(out["public_control_bits_total"], 256 + 32 + 127)
        self.assertTrue(all("raw" not in str(event["payload"]).lower() and "corrected" not in str(event["payload"]).lower() for event in got["events"]))
        self.assertEqual(sum(e["event_type"] == "PLANE_CONSISTENCY" for e in got["events"]), 1)
        seen = []
        class Capture(_ZeroDecoder):
            def __init__(self, h, **params): super().__init__(h, **params); seen.append(params)
        self.execute(_decoder_factory=Capture)
        self.assertEqual(seen[0], {"error_rate": .0001, "max_iter": 50, "bp_method": "minimum_sum", "ms_scaling_factor": 1.0, "schedule": "serial", "omp_thread_count": 1, "serial_schedule_order": list(range(64)), "osd_method": "OSD_0", "osd_order": 0})
        unavailable = self.execute(_preflight={"status": "preflight_unavailable"}); self.assertEqual((unavailable["outcome"]["status"], unavailable["outcome"]["attempted"]), ("preflight_unavailable", False))
        class Explode: 
            def __init__(self, *args, **kwargs): raise RuntimeError("no fallback")
        self.assertEqual(self.execute(_decoder_factory=Explode)["outcome"]["status"], "decoder_error")
        inconsistent = self.execute(_decoder_factory=_BadDecoder)["outcome"]
        self.assertEqual((inconsistent["status"], inconsistent["attempted"], inconsistent["denominator_included"]), ("syndrome_inconsistent", True, True))

    def test_verify_failure_abort_and_real_backend_smoke(self):
        import comparison_bench.src.comparison_bench.formal_ir.ldpc as mod
        old = mod.verification_result
        try:
            mod.verification_result = lambda *args, **kw: {"verification_invoked": True, "verification_tag_bits": 64, "public_control_bits": 127, "epsilon_ec": 2.0 ** -64, "verified": False}
            self.assertEqual(self.execute()["outcome"]["status"], "verify_failed")
        finally: mod.verification_result = old
        aborted = self.execute(_caps={"wall_s": -1})
        self.assertEqual(aborted["outcome"]["status"], "aborted_resource_limit")
        self.assertFalse(aborted["outcome"]["verification_invoked"])
        self.assertEqual(aborted["events"][-1]["event_type"], "ABORT")
        ticks = iter((0.0, 0.0, 0.0, 0.0, 6.0, 6.0, 6.0))
        post_verify_timeout = self.execute(_clock=lambda: next(ticks, 6.0))
        self.assertEqual(post_verify_timeout["outcome"]["status"], "aborted_resource_limit")
        self.assertTrue(post_verify_timeout["outcome"]["verification_invoked"])
        self.assertEqual(post_verify_timeout["outcome"]["verification_tag_bits"], 64)
        self.assertEqual(post_verify_timeout["events"][-1]["event_type"], "ABORT")
        ca = np.zeros((2, 64), dtype=np.int64); cb = ca.copy(); cb[:, 0] = 1
        real_cal = calibrate_rates({"d": (ca, cb)}, sacrificed_frame_keys={"d": ["d:cal0", "d:cal1"]}, calibration_role="sacrificed_tuning_only", mapping="natural", source_bytes=b"real-backend-smoke", dimension=2)
        bob = np.zeros(64, dtype=np.int64); bob[0] = 1
        actual = run_ldpc_formal(np.zeros(64, dtype=np.int64), bob, dimension=2, mapping="natural", frozen_calibration=real_cal, codebook_entries=self.entries, codebook_bytes=self.bytes, dataset_id="d", locked_seed=self.seed)
        self.assertEqual(actual["outcome"]["status"], "verified_success")
        self.assertNotIn("_decoder_factory", inspect.signature(run_ldpc_formal).parameters)
        self.assertNotIn("_preflight", inspect.signature(run_ldpc_formal).parameters)
