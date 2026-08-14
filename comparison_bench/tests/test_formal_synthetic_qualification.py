from __future__ import annotations

import json
import hashlib
import os
import shutil
import sys
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path

from comparison_bench.src.comparison_bench.cli import run_formal_synthetic_qualification as runner
from comparison_bench.src.comparison_bench.formal_ir.shared import FORMAL_ARTIFACTS
from comparison_bench.src.comparison_bench.formal_ir.shared import canonical_event


class FormalSyntheticQualificationTest(unittest.TestCase):
    @staticmethod
    def _write_json(path: Path, value) -> None:
        path.write_bytes(json.dumps(value, indent=2, sort_keys=True).encode("utf-8") + b"\n")

    def _rebind_plan_hash(self, output: Path) -> None:
        manifest_path = output / "formal_run_manifest.json"; manifest = json.loads(manifest_path.read_text())
        digest = hashlib.sha256((output / "pre_run_plan.json").read_bytes()).hexdigest(); manifest["plan_sha256"] = digest; manifest["artifacts"]["pre_run_plan.json"] = digest; self._write_json(manifest_path, manifest)
        report_path = output / "formal_qualification_report.json"; report = json.loads(report_path.read_text())
        report["formal_run_manifest_sha256"] = hashlib.sha256(manifest_path.read_bytes()).hexdigest(); self._write_json(report_path, report)
    @staticmethod
    @contextmanager
    def _temporary_dir():
        # Never trust or delete the operator-owned base; only a UUID child is ours.
        root = Path(os.environ.get("FORMAL_IR_TEST_TMP", "workspace")); root.mkdir(parents=True, exist_ok=True)
        resolved_root = root.resolve(); child = resolved_root / f"formal-v3-{uuid.uuid4().hex}"
        child.mkdir()
        try:
            yield child
        finally:
            resolved_child = child.resolve()
            if resolved_child.parent != resolved_root: raise RuntimeError("refusing to remove outside formal test root")
            shutil.rmtree(resolved_child)
    @staticmethod
    def _preflight():
        return {"command": [sys.executable, "-m", "pytest", "comparison_bench/tests/test_formal_verification.py", "comparison_bench/tests/test_cascade_formal.py", "comparison_bench/tests/test_ldpc_formal.py", "-q", "-p", "no:cacheprovider", "--basetemp", "fixture"], "exit_code": 0, "passed_count": 17, "output_sha256": "f" * 64, "passed": True}

    @staticmethod
    def _method(*args, **kwargs):
        method = "cascade_formal_v1" if "base_seed" in kwargs else "ldpc_formal_v1"; seed = kwargs["locked_seed"]; key = f"{kwargs['dataset_id']}:{kwargs['frame_id']}"
        event = {"event_id": 1, "frame_key": key, "method": method, "event_type": "BLOCK_PARITY", "direction": "alice_to_bob", "parent_event_id": None, "pass_id": 0, "block_id": 0, "key_dependent_bits": 1, "public_control_bits": 0, "payload": {"parity": 0}}
        return {"events": [event], "outcome": {"dataset_id": kwargs["dataset_id"], "frame_id": kwargs["frame_id"], "n_pairs": 64, "pair_idx_sequence_sha256": "fixture", "method": method, "attempted": True, "denominator_included": True, "status": "verified_success", "failure_reason": "", "dimension": 1024, "frame_len_symbols": 64, "raw_ser": 0., "verification_invoked": True, "verification_seed_id": seed["seed_id"], "verification_tag_bits": 0, "epsilon_ec": 0., "key_dependent_disclosure_bits_total": 1, "public_control_bits_total": 0, "transcript_first_event_id": 1, "transcript_last_event_id": 1, "transcript_sha256": hashlib.sha256(canonical_event(event)).hexdigest(), "runtime_s": 0.}}

    def _package(self, output: Path, method=None) -> None:
        method = method or self._method
        old = (runner._deterministic_preflight, runner.run_cascade_formal, runner.run_ldpc_formal)
        runner._deterministic_preflight = self._preflight; runner.run_cascade_formal = method; runner.run_ldpc_formal = method
        try: runner.run(output)
        finally: runner._deterministic_preflight, runner.run_cascade_formal, runner.run_ldpc_formal = old

    def test_dynamic_package_and_five_tampers(self):
        with self._temporary_dir() as td:
            out = Path(td) / "v3"; self._package(out); runner.verify(out)
            cases = ["pre_run_plan.json", "formal_frame_outcomes.csv", "formal_transcript.jsonl", "formal_codebook_manifest.json", "formal_qualification_report.json"]
            for name in cases:
                original = (out / name).read_bytes(); (out / name).write_bytes(original + b" ")
                with self.assertRaises(ValueError, msg=name): runner.verify(out)
                (out / name).write_bytes(original)

    def test_preflight_plan_exception_finalizes_six_artifacts(self):
        old = runner._deterministic_preflight; runner._deterministic_preflight = self._preflight
        original = runner._plan
        runner._plan = lambda: (_ for _ in ()).throw(RuntimeError("forced before preflight"))
        try:
            with self._temporary_dir() as td:
                out = Path(td) / "failure"
                with self.assertRaises(RuntimeError): runner.run(out)
                self.assertEqual({p.name for p in out.iterdir()}, set(FORMAL_ARTIFACTS))
                report = json.loads((out / "formal_qualification_report.json").read_text())
                self.assertEqual(report["run_status"], "non_promoted")
                runner.verify(out)
        finally: runner._deterministic_preflight = old; runner._plan = original

    def test_bad_method_original_transcript_hash_fails_closed(self):
        def bad_method(*args, **kwargs):
            value = self._method(*args, **kwargs); value["outcome"]["transcript_sha256"] = "0" * 64; return value
        old = (runner._deterministic_preflight, runner.run_cascade_formal, runner.run_ldpc_formal)
        runner._deterministic_preflight = self._preflight; runner.run_cascade_formal = bad_method; runner.run_ldpc_formal = bad_method
        try:
            with self._temporary_dir() as td:
                out = Path(td) / "bad-transcript"
                with self.assertRaisesRegex(ValueError, "original transcript hash"): runner.run(out)
                self.assertTrue(set(FORMAL_ARTIFACTS).issubset({item.name for item in out.iterdir()}))
                self.assertEqual(json.loads((out / "formal_qualification_report.json").read_text())["run_status"], "non_promoted")
        finally: runner._deterministic_preflight, runner.run_cascade_formal, runner.run_ldpc_formal = old

    def test_decode_failed_noninvoked_seed_is_empty_and_verifiable(self):
        def noninvoked(*args, **kwargs):
            value = self._method(*args, **kwargs)
            value["outcome"].update({"status": "decode_failed", "failure_reason": "fixture", "verification_invoked": False, "verification_seed_id": "", "verification_tag_bits": 0, "epsilon_ec": 0.})
            return value
        with self._temporary_dir() as td:
            out = Path(td) / "decode-failed"; self._package(out, noninvoked); runner.verify(out)
            report = json.loads((out / "formal_qualification_report.json").read_text())
            self.assertFalse(any(gate["promoted"] for gate in report["promotion_gates"].values()))

    def test_locked_plan_and_run_id_drift_are_rejected(self):
        with self._temporary_dir() as td:
            out = Path(td) / "drift"; self._package(out)
            plan_path = out / "pre_run_plan.json"; plan = json.loads(plan_path.read_text()); plan["caps"]["frame_s"] = 6; self._write_json(plan_path, plan); self._rebind_plan_hash(out)
            with self.assertRaises(ValueError, msg="caps drift"): runner.verify(out)
        with self._temporary_dir() as td:
            out = Path(td) / "run-id"; self._package(out)
            report_path = out / "formal_qualification_report.json"; report = json.loads(report_path.read_text()); report["run_id"] = "drift"; self._write_json(report_path, report)
            with self.assertRaises(ValueError, msg="run id drift"): runner.verify(out)
