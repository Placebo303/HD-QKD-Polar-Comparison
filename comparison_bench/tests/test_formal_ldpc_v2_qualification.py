from __future__ import annotations

import copy
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from comparison_bench.src.comparison_bench.cli import run_formal_ldpc_v2_qualification as runner


class ProvenanceCoreTest(unittest.TestCase):
    def test_live_status_drift_is_allowed_but_core_drift_is_rejected(self):
        stored = {"git": {"commit": "abc", "status_porcelain_v1_hex": "7879", "status_porcelain_v1_sha256": runner._sha(b"xy"), "dirty": True},
                  "environment": {"python": "x"}, "source_sha256": {"ldpc_v2.py": "a"}}
        live = copy.deepcopy(stored); live["git"]["status_porcelain_v1_hex"] = "7a"; live["git"]["status_porcelain_v1_sha256"] = runner._sha(b"z"); live["git"]["dirty"] = True
        runner._verify_provenance(stored, live)
        for branch, key, value in (("git", "commit", "other"), ("environment", "python", "other"), ("source_sha256", "ldpc_v2.py", "other")):
            changed = copy.deepcopy(live); changed[branch][key] = value
            with self.assertRaises(ValueError): runner._verify_provenance(stored, changed)


def _fake(*args, **kwargs):
    policy = kwargs["frozen_policy"]
    frame = kwargs["frame_id"]; dataset = kwargs["dataset_id"]
    return {"events": [], "outcome": {"dataset_id": dataset, "frame_id": frame, "method": runner.METHOD,
        "status": "verified_success", "attempted": True, "denominator_included": True,
        "failure_reason": "", "runtime_s": 0.0, "verification_invoked": True,
        "verification_seed_id": kwargs["locked_seed"]["seed_id"], "policy_id": policy["policy_id"],
        "transcript_sha256": runner._sha(b""), "key_dependent_disclosure_bits_total": 0,
        "public_control_bits_total": 0}}


def _probes():
    return [{"supported": True, "dependency_version": "2.4.1", "osd_method": method, "osd_order": order} for method, order in (("OSD_0",0),("OSD_CS",1),("OSD_CS",2))]


@unittest.skipUnless(os.environ.get("FORMAL_IR_FILE_TESTS") == "1", "set FORMAL_IR_FILE_TESTS=1 outside the Windows sandbox ACL")
class FormalLdpcV2QualificationTest(unittest.TestCase):
    def _run(self) -> Path:
        self.temp = tempfile.TemporaryDirectory()
        output = Path(self.temp.name) / "fresh"
        runner.create_plan(output)
        runner.run(output, method_runner=_fake, constructor_probe=_probes)
        return output

    def tearDown(self):
        if hasattr(self, "temp"): self.temp.cleanup()

    def test_generation_orders_global_freeze_and_confirmation_only(self):
        output = self._run(); runner.verify(output)
        plan = json.loads((output / "pre_run_plan.json").read_text())
        policy = json.loads((output / "formal_policy_manifest.json").read_text())
        rows = runner._rows(output / "formal_frame_outcomes.csv")
        self.assertEqual((len(plan["development_toeplitz_seeds"]), len(plan["confirmation_toeplitz_seeds"])), (576, 64))
        self.assertEqual((len(rows), len(set(row["frame_id"] for row in rows))), (64, 64))
        self.assertEqual([row["frame_id"] for row in rows], plan["confirmation_execution_order"])
        self.assertTrue(all(len(rows) == 64 for rows in policy["development_outcomes"].values()))
        self.assertEqual({row["policy_id"] for row in rows}, {policy["selected_policy_sha256"]})
        self.assertTrue(all(gate["verified_success"] == 32 for gate in json.loads((output / "formal_qualification_report.json").read_text())["promotion_gates"].values()))

    def test_plan_review_boundary_and_execute_does_not_generate_new_seeds(self):
        self.temp = tempfile.TemporaryDirectory(); output = Path(self.temp.name) / "fresh"; calls = []
        with self.assertRaises(ValueError): runner.run(output, method_runner=lambda *a, **k: calls.append(1))
        plan = runner.create_plan(output); before = (output / "pre_run_plan.json").read_bytes()
        self.assertEqual(calls, []); self.assertEqual({p.name for p in output.iterdir()}, {"pre_run_plan.json"})
        old = runner.materialize_seed_record
        runner.materialize_seed_record = lambda *a, **k: (_ for _ in ()).throw(AssertionError("new seed"))
        try: runner.run(output, method_runner=_fake, constructor_probe=_probes)
        finally: runner.materialize_seed_record = old
        self.assertEqual(before, (output / "pre_run_plan.json").read_bytes())

    def test_execute_rejects_extra_pre_review_file(self):
        self.temp = tempfile.TemporaryDirectory(); output = Path(self.temp.name) / "fresh"; runner.create_plan(output); (output / "review-note.txt").write_text("x", encoding="utf-8")
        with self.assertRaises(ValueError): runner.run(output, method_runner=_fake, constructor_probe=_probes)

    def test_hash_dag_and_tamper_extra_missing_are_rejected(self):
        output = self._run()
        manifest = json.loads((output / "formal_run_manifest.json").read_text()); manifest["artifacts"]["pre_run_plan.json"] = "0" * 64
        (output / "formal_run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(ValueError): runner.verify(output)

    def test_extra_and_missing_artifacts_are_rejected(self):
        output = self._run(); (output / "unexpected.txt").write_text("x", encoding="utf-8")
        with self.assertRaises(ValueError): runner.verify(output)
        (output / "unexpected.txt").unlink(); (output / "formal_transcript.jsonl").unlink()
        with self.assertRaises(ValueError): runner.verify(output)

    def test_preflight_failure_finalizes_without_method_calls(self):
        self.temp = tempfile.TemporaryDirectory(); output = Path(self.temp.name) / "fresh"; runner.create_plan(output); calls = []
        def never(*args, **kwargs): calls.append(1); return _fake(*args, **kwargs)
        with self.assertRaises(RuntimeError): runner.run(output, method_runner=never, constructor_probe=lambda: [{"supported": False}] * 3)
        self.assertEqual(calls, [])
        self.assertEqual({p.name for p in output.iterdir()}, set(runner.ARTIFACTS))

    def test_tampered_seed_dev_calibration_provenance_and_strata_are_rejected(self):
        output = self._run()
        cases = []
        for name in ("seed", "development", "calibration", "provenance", "strata"):
            target = output.parent / name; shutil.copytree(output, target); cases.append((name, target))
        for name, target in cases:
            if name == "seed":
                plan = json.loads((target / "pre_run_plan.json").read_text()); next(iter(plan["confirmation_toeplitz_seeds"].values()))["seed_id"] = "0" * 64; (target / "pre_run_plan.json").write_text(json.dumps(plan), encoding="utf-8")
            elif name == "development":
                policy = json.loads((target / "formal_policy_manifest.json").read_text()); next(iter(policy["development_outcomes"].values()))[0]["plan_frame_id"] = "drift"; (target / "formal_policy_manifest.json").write_text(json.dumps(policy), encoding="utf-8")
            elif name == "calibration":
                policy = json.loads((target / "formal_policy_manifest.json").read_text()); policy["calibrations"]["p01"]["mapping"] = "natural"; (target / "formal_policy_manifest.json").write_text(json.dumps(policy), encoding="utf-8")
            elif name == "provenance":
                plan = json.loads((target / "pre_run_plan.json").read_text()); plan["provenance"]["environment"]["python"] = "drift"; (target / "pre_run_plan.json").write_text(json.dumps(plan), encoding="utf-8")
            else:
                csv_path = target / "formal_frame_outcomes.csv"; rows = runner._rows(csv_path); original = float(rows[0]["stratum_p"]); rows[0]["stratum_p"] = "0.02" if original == .01 else "0.01"; self.assertNotEqual(float(rows[0]["stratum_p"]), original); csv_path.unlink(); runner._csv_x(csv_path, rows)
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, ".+"):
                    runner.verify(target)

    def test_partial_method_call_is_preserved_by_failure_finalizer(self):
        self.temp = tempfile.TemporaryDirectory(); output = Path(self.temp.name) / "fresh"; runner.create_plan(output); calls = []
        def partial(*args, **kwargs):
            calls.append(1)
            if len(calls) == 2: raise RuntimeError("injected")
            return _fake(*args, **kwargs)
        with self.assertRaises(RuntimeError): runner.run(output, method_runner=partial, constructor_probe=_probes)
        policy = json.loads((output / "formal_policy_manifest.json").read_text())
        self.assertEqual(sum(len(v) for v in policy["development_outcomes"].values()), 1)
