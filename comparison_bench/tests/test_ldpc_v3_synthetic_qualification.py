from __future__ import annotations

import json, os, shutil, unittest
from pathlib import Path

import numpy as np

from comparison_bench.src.comparison_bench.cli import run_ldpc_v3_synthetic_qualification as lane
from comparison_bench.src.comparison_bench.cli.verify_ldpc_v3_synthetic_qualification import verify
from comparison_bench.src.comparison_bench.formal_ir import ldpc_v3
from comparison_bench.src.comparison_bench.formal_ir.shared import materialize_seed_record


class ZeroDecoder:
    def __init__(self, h, **kwargs): self.h = h
    def decode(self, syndrome): return np.zeros(256, dtype=np.uint8)


class SyntheticQualificationTest(unittest.TestCase):
    def setUp(self):
        root = os.environ.get("FORMAL_IR_TEST_TMP")
        if not root: self.skipTest("FORMAL_IR_TEST_TMP must be explicit")
        self.root = Path(root) / "phase6b_synthetic"
        if self.root.exists(): shutil.rmtree(self.root)
        self.root.mkdir(parents=True)
        planes=[{"plane_id":i,"errors":0,"total_bits":64*256,"p_hat":0.0} for i in range(10)]
        self.cal={"calibration_role":"sacrificed_tuning_only","dimension":1024,"mapping":"gray","frame_len_symbols":256,"source_sha256":"a"*64,"planes":planes}
        self.cal["calibration_sha256"]=lane._sha(lane._compact(self.cal))
    def tearDown(self):
        if self.root.exists(): shutil.rmtree(self.root)
    def _plan(self, out:Path):
        plan={"run_id":lane.RUN_ID,"frozen_calibration":self.cal,"caps":{"per_frame":ldpc_v3.DEFAULT_CAPS,"complete_run_s":1800},"execution_order":lane._order(),"toeplitz_seeds":{},"_test_only":True,"selected_candidate_binding_sha256":ldpc_v3.SELECTION_BINDING_SHA256,"generator_contract":{"algorithm":"PCG64","root_seeds":lane.ROOT_SEEDS,"mask_call_order":"stratum, plane 0..9, rng.random((32,256))","gray_inverse":"xor shifts 1,2,4,8"}}
        plan["toeplitz_seeds"]={k:materialize_seed_record(2623) for k in plan["execution_order"]}
        plan["plan_sha256"]=lane._sha(lane._compact({k:v for k,v in plan.items() if k!="plan_sha256"}))
        out.mkdir(); lane._json_x(out/"pre_run_plan.json",plan)
    def test_exact_generator_and_private_execution(self):
        production_style={"_test_only":False,"value":"production-style"}; lane._seal_plan(production_style)
        self.assertEqual(production_style["plan_sha256"],lane._sha(lane._compact({"_test_only":False,"value":"production-style"})))
        a,b=lane._synthetic_pair("calibrated",0,self.cal)
        self.assertTrue(np.array_equal(a,b))
        self.assertEqual(lane._synthetic_pair("stress_125",3,self.cal)[0].shape,(256,))
        out=self.root/"private"; self._plan(out)
        lane.run(out,_test_only=True,method_runner=lambda *a,**kw: ldpc_v3.run_ldpc_formal_v3(*a,**kw,_preflight={"status":"ok","dependency_version":"2.4.1","backend_name":"test"},_decoder_factory=ZeroDecoder))
        self.assertEqual({x.name for x in out.iterdir()},set(lane.ARTIFACTS))
        self.assertEqual(len((out/"formal_frame_outcomes.csv").read_text().splitlines()),65)
        self.assertEqual(verify(out,_private_test_only=True)["outcomes"],64)
        with self.assertRaises(ValueError): verify(out)
        with self.assertRaises(ValueError): lane.run(out,_test_only=True)
    def test_failure_finalizes_and_cli_test_plan_is_rejected(self):
        out=self.root/"failure"; self._plan(out)
        with self.assertRaises(RuntimeError): lane.run(out,_test_only=True,method_runner=lambda *a,**kw: (_ for _ in ()).throw(RuntimeError("boom")))
        self.assertEqual({x.name for x in out.iterdir()},set(lane.ARTIFACTS))
        self.assertFalse(json.loads((out/"formal_qualification_report.json").read_text())["promoted"])
        self.assertEqual(verify(out,_private_test_only=True)["run_status"],"non_promoted")
    def test_nonattempted_and_tamper_rejection(self):
        out=self.root/"nonattempted"; self._plan(out)
        lane.run(out,_test_only=True,method_runner=lambda *a,**kw: ldpc_v3.run_ldpc_formal_v3(*a,**kw,_preflight={"status":"preflight_unavailable","dependency_version":"","backend_name":""}))
        self.assertEqual(verify(out,_private_test_only=True)["outcomes"],64)
        originals={name:(out/name).read_bytes() for name in lane.ARTIFACTS}
        mutations={"extra.txt":b"x","pre_run_plan.json":b"{}\n","formal_codebook_manifest.json":b"{}\n","formal_frame_outcomes.csv":originals["formal_frame_outcomes.csv"].replace(b"preflight_unavailable",b"unknown_status_____",1),"formal_transcript.jsonl":b"{}\n","formal_qualification_report.json":b"{}\n"}
        for name,value in mutations.items():
            if name=="extra.txt": (out/name).write_bytes(value)
            else: (out/name).write_bytes(value)
            with self.assertRaises(ValueError): verify(out,_private_test_only=True)
            if name=="extra.txt": (out/name).unlink()
            else: (out/name).write_bytes(originals[name])
        with self.assertRaises(FileExistsError): lane.create_plan(out,{},_test_only=True)
        with self.assertRaises(ValueError): lane.run(out,_test_only=True)
