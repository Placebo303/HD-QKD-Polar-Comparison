from __future__ import annotations
import json, os, shutil, unittest, uuid
from pathlib import Path
from unittest.mock import patch
import numpy as np

from comparison_bench.src.comparison_bench.cli import run_ldpc_v4_development_v2 as dev
from comparison_bench.src.comparison_bench.cli import run_ldpc_v4_synthetic_qualification as lane
from comparison_bench.src.comparison_bench.cli import verify_ldpc_v4_synthetic_qualification as verify
from comparison_bench.src.comparison_bench.formal_ir import ldpc_v4_channel

V3=Path("comparison_bench/outputs_comparison/formal_ir_methods/20260726_v1_binary_ldpc_v3_synthetic/pre_run_plan.json")
FAILED_V1=Path("comparison_bench/outputs_comparison/formal_ir_methods/20260727_v1_binary_ldpc_v4_development")
TMP=Path(os.environ.get("FORMAL_IR_TEST_TMP","workspace/formal_ir_test_tmp"))
REAL_GENERATE=lane._generate
class ZeroDecoder:
 def __init__(self,h,**kw): self.h=h
 def decode(self,s): return np.zeros(256,dtype=np.uint8)
class TestSyntheticV4(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls._shared=TMP/f"v4syn_dev_shared_{uuid.uuid4().hex}"; lock=json.loads(V3.read_text())["locked_data"]; plan=dev._prepare_test_plan(cls._shared,lock); model=ldpc_v4_channel.build_adjacent_channel_model(lock); rows=[]
  for s,p,c in plan["execution_order"]:
   d=dev.generate_sacrificed_development(model,s); got=dev.evaluate_candidate(d["alice_frames"],d["bob_frames"],model=model,plane_id=p,candidate_id=c,stratum=s,frame_ids=d["frame_ids"],decoder_factory=ZeroDecoder,max_runtime_s=5.0)[:2]
   for x in got: x.update(status="development_exact_success",exact_match=True,source_sha256=d["source_sha256"])
   rows.extend(got)
  dev._finalize(cls._shared,plan,rows,"completed","completed")
 def _out(self,n): return TMP/f"v4syn_{n}_{uuid.uuid4().hex}"
 def _dev_ready(self):
  out=self._out("dev"); shutil.copytree(self._shared,out); return out
 def _same_generator(self,plan,s):
  n=plan["frame_count_per_stratum"]; b=np.zeros((n,256),dtype=np.uint16); a=b.copy(); _,_,seeds=REAL_GENERATE(plan,s); return a,b,seeds
 def test_success_nonpromotion_and_readonly(self):
  d=self._dev_ready(); out=self._out("success"); lane._prepare_test_plan(out,d)
  with patch.object(lane,"_generate",side_effect=self._same_generator): lane._execute_test_plan(out,lambda *a,**kw: __import__('comparison_bench.src.comparison_bench.formal_ir.ldpc_v4',fromlist=['run_ldpc_formal_v4']).run_ldpc_formal_v4(*a,**kw,_decoder_factory=ZeroDecoder,_preflight_result={"status":"ok","dependency_version":"2.4.1","backend_name":"test"}))
  with patch.object(lane,"_generate",side_effect=self._same_generator): got=verify.verify_output(out,_private_test_only=True)
  self.assertTrue(got["promoted"]); before={p.name:p.read_bytes() for p in out.iterdir()}
  with patch.object(lane,"_generate",side_effect=self._same_generator): verify.verify_output(out,_private_test_only=True)
  self.assertEqual(before,{p.name:p.read_bytes() for p in out.iterdir()})
  bad=self._out("bad"); lane._prepare_test_plan(bad,d)
  lane._execute_test_plan(bad,lambda *a,**kw: __import__('comparison_bench.src.comparison_bench.formal_ir.ldpc_v4',fromlist=['run_ldpc_formal_v4']).run_ldpc_formal_v4(*a,**kw,_preflight_result={"status":"backend_unavailable","dependency_version":""}))
  bad_result=verify.verify_output(bad,_private_test_only=True); self.assertFalse(bad_result["promoted"])
  report=json.loads((bad/"formal_qualification_report.json").read_text())
  for gate in report["promotion_gates"].values(): self.assertEqual(gate["denominator"],2); self.assertFalse(gate["promoted"]); self.assertEqual(gate["forbidden_failure_count"],2)
 def test_tamper_overwrite_exception_and_cap(self):
  d=self._dev_ready(); out=self._out("base"); lane._prepare_test_plan(out,d)
  with patch.object(lane,"_generate",side_effect=self._same_generator): lane._execute_test_plan(out,lambda *a,**kw: __import__('comparison_bench.src.comparison_bench.formal_ir.ldpc_v4',fromlist=['run_ldpc_formal_v4']).run_ldpc_formal_v4(*a,**kw,_decoder_factory=ZeroDecoder,_preflight_result={"status":"ok","dependency_version":"2.4.1","backend_name":"test"}))
  with self.assertRaises(FileExistsError): lane._prepare_test_plan(out,d)
  for file in lane.ARTIFACTS:
   copy=self._out("tamper"); shutil.copytree(out,copy); p=copy/file; p.write_bytes(p.read_bytes()+b" ")
   with patch.object(lane,"_generate",side_effect=self._same_generator):
    with self.assertRaises(ValueError): verify.verify_output(copy,_private_test_only=True)
  for event_type, payload in (("SYNDROME", {"syndrome":"00"}), ("VERIFICATION_TAG", {"tag":"00"}), ("EVENT_INTERLEAVE", None)):
   semantic=self._out(f"semantic_{event_type.lower()}"); shutil.copytree(out,semantic)
   rows=verify._rows(semantic/"formal_frame_outcomes.csv"); events=[json.loads(x) for x in (semantic/"formal_transcript.jsonl").read_bytes().splitlines()]
   if event_type=="EVENT_INTERLEAVE":
    first_key=events[0]["frame_key"]; first=[event for event in events if event["frame_key"]==first_key]
    events[:len(first)]=[first[10],*first[:10],*first[11:]]
   else:
    target=next(event for event in events if event["event_type"]==event_type); target["payload"]=payload
   first_key=events[0]["frame_key"]; first=[event for event in events if event["frame_key"]==first_key]
   canonical=__import__('comparison_bench.src.comparison_bench.formal_ir.shared',fromlist=['canonical_event']).canonical_event
   blob=b"".join(canonical(event) for event in first)
   rows[0]["transcript_bytes_len"]=len(blob); rows[0]["transcript_bytes_sha256"]=lane._sha(blob); rows[0]["transcript_sha256"]=lane._sha(blob)
   (semantic/"formal_frame_outcomes.csv").write_bytes(lane._csv(rows)); (semantic/"formal_transcript.jsonl").write_bytes(b"".join(canonical(event) for event in events))
   run=json.loads((semantic/"formal_run_manifest.json").read_text()); run["artifact_index"]={name:{"sha256":lane._sha((semantic/name).read_bytes()),"bytes":(semantic/name).stat().st_size} for name in lane.ARTIFACTS[:6]}; run["manifest_sha256"]=lane._sha(lane._compact({k:v for k,v in run.items() if k!="manifest_sha256"})); (semantic/"formal_run_manifest.json").write_bytes(lane._compact(run))
   report=json.loads((semantic/"formal_qualification_report.json").read_text()); report["run_manifest_sha256"]=lane._sha((semantic/"formal_run_manifest.json").read_bytes()); report["report_sha256"]=lane._sha(lane._compact({k:v for k,v in report.items() if k!="report_sha256"})); (semantic/"formal_qualification_report.json").write_bytes(lane._compact(report))
   with patch.object(lane,"_generate",side_effect=self._same_generator):
    with self.assertRaises(ValueError): verify.verify_output(semantic,_private_test_only=True)
  exc=self._out("exc"); lane._prepare_test_plan(exc,d)
  lane._execute_test_plan(exc,lambda *a,**kw: (_ for _ in ()).throw(RuntimeError("boom")))
  self.assertEqual({p.name for p in exc.iterdir()},set(lane.ARTIFACTS)); self.assertEqual(verify.verify_output(exc,_private_test_only=True)["run_status"],"failed")
  cap=self._out("cap"); lane._prepare_test_plan(cap,d)
  with patch.object(lane.time,"monotonic",side_effect=[0.0,1801.0]): lane._execute_test_plan(cap,lambda *a,**kw: (_ for _ in ()).throw(RuntimeError()))
  self.assertEqual(verify.verify_output(cap,_private_test_only=True)["run_status"],"failed")
 def test_seed_collision_and_confirmation_isolation(self):
  d=self._dev_ready(); out=self._out("plan"); p=lane._prepare_test_plan(out,d); self.assertEqual(len(p["execution_order"]),4)
  self.assertEqual(lane.qualification_floor(128),126)
  q=json.loads((out/"pre_run_plan.json").read_text()); q["caps"]={"complete_run_s":1,"per_frame":{"wall_s":5.0,"decoder_calls":10,"events":32}}; q["plan_sha256"]=lane._sha(lane._compact({k:v for k,v in q.items() if k!="plan_sha256"})); (out/"pre_run_plan.json").write_bytes(lane._compact(q))
  with self.assertRaises(ValueError): lane._validate_plan(q,private=True)
  q["caps"]={"complete_run_s":1800,"per_frame":{"wall_s":5.0,"decoder_calls":10,"events":32}}; q["gate"]["verified_success_floor"]=1; q["plan_sha256"]=lane._sha(lane._compact({k:v for k,v in q.items() if k!="plan_sha256"}))
  with self.assertRaises(ValueError): lane._validate_plan(q,private=True)
  collide=self._out("collision"); old=int(next(iter(p["v3_seed_binding"]["root_seeds"].values())))
  with patch.object(lane.secrets,"token_bytes",return_value=old.to_bytes(16,"big")):
   with self.assertRaises(ValueError): lane._prepare_test_plan(collide,d)
  development_collision=self._out("development_collision"); development_root=p["development_root_binding"]["roots"][0]["root_integer"]
  values=[int(development_root).to_bytes(16,"big")]+[i.to_bytes(16,"big") for i in range(1,8)]
  with patch.object(lane.secrets,"token_bytes",side_effect=values):
   with self.assertRaises(ValueError): lane._prepare_test_plan(development_collision,d)
 def test_failed_v1_prerequisite_rejected_before_output_creation(self):
  out=self._out("failed_v1")
  self.assertFalse(out.exists())
  with self.assertRaises(ValueError): lane._prepare_test_plan(out,FAILED_V1)
  self.assertFalse(out.exists())
 def test_tampered_corrected_v2_prerequisite_rejected_before_output_creation(self):
  prerequisite=self._dev_ready(); (prerequisite/"development_report.json").write_bytes((prerequisite/"development_report.json").read_bytes()+b" ")
  out=self._out("tampered_v2")
  self.assertFalse(out.exists())
  with self.assertRaises(ValueError): lane._prepare_test_plan(out,prerequisite)
  self.assertFalse(out.exists())
