from __future__ import annotations
import json, os, shutil, unittest, uuid
from pathlib import Path
from unittest.mock import patch
import numpy as np
from comparison_bench.src.comparison_bench.cli import run_ldpc_v4_development as run
from comparison_bench.src.comparison_bench.cli import verify_ldpc_v4_development as verify

PLAN=Path("comparison_bench/outputs_comparison/formal_ir_methods/20260726_v1_binary_ldpc_v3_synthetic/pre_run_plan.json")
TMP=Path(os.environ.get("FORMAL_IR_TEST_TMP","workspace/formal_ir_test_tmp")); TMP.mkdir(parents=True,exist_ok=True)
class ZeroDecoder:
 def __init__(self,h,**kw): self.h=h
 def decode(self,s): return np.zeros(256,dtype=np.uint8)
class PackageTest(unittest.TestCase):
 def _out(self,name): return TMP/f"{name}_{uuid.uuid4().hex}"
 def _lock(self): return json.loads(PLAN.read_text())["locked_data"]
 def test_completed_nonready_readonly_overwrite_and_tamper(self):
  out=self._out("complete");run._prepare_test_plan(out,self._lock());run._execute_test_plan(out,ZeroDecoder)
  got=verify.verify_output(out,_private_test_only=True);self.assertEqual(got["run_status"],"completed");self.assertFalse(got["ready_for_synthetic_prepare"])
  before={x.name:x.read_bytes() for x in out.iterdir()};verify.verify_output(out,_private_test_only=True);self.assertEqual(before,{x.name:x.read_bytes() for x in out.iterdir()})
  with self.assertRaises(FileExistsError):run._prepare_test_plan(out,self._lock())
  (out/"v4_channel_model.json").write_bytes((out/"v4_channel_model.json").read_bytes()+b" ")
  with self.assertRaises(ValueError):verify.verify_output(out,_private_test_only=True)
 def test_backend_exception_and_partial_finalization(self):
  out=self._out("exception");run._prepare_test_plan(out,self._lock())
  with patch.object(run,"generate_sacrificed_development",side_effect=RuntimeError("source boom")):run._execute_test_plan(out,ZeroDecoder)
  self.assertEqual({x.name for x in out.iterdir()},set(run.ARTIFACTS));self.assertEqual(verify.verify_output(out,_private_test_only=True)["run_status"],"failed")
 def test_tamper_matrix_source_selection_run_report_and_malformed_accounting(self):
  base=self._out("base");run._prepare_test_plan(base,self._lock());run._execute_test_plan(base,ZeroDecoder)
  def case(name,change):
   out=self._out(name);shutil.copytree(base,out);change(out)
   with self.assertRaises(ValueError):verify.verify_output(out,_private_test_only=True)
  case("matrix",lambda d:(d/"v4_candidate_manifest.json").write_bytes((d/"v4_candidate_manifest.json").read_bytes()+b" "))
  case("source",lambda d:(d/"v4_channel_model.json").write_bytes((d/"v4_channel_model.json").read_bytes()+b" "))
  case("selection",lambda d:(d/"development_selection.json").write_bytes(b'{"schema":"wrong"}'))
  case("run",lambda d:(d/"development_run_manifest.json").write_bytes(b'{"schema":"wrong"}'))
  case("report",lambda d:(d/"development_report.json").write_bytes(b'{"schema":"wrong"}'))
  def malformed(d):
   p=d/"development_plane_outcomes.csv";p.write_bytes(p.read_bytes().replace(b",true,development_",b",maybe,development_",1))
  case("malformed",malformed)
 def test_cap_failure_finalization(self):
  out=self._out("cap");run._prepare_test_plan(out,self._lock())
  with patch.object(run.time,"monotonic",side_effect=[0.0,1801.0]):run._execute_test_plan(out,ZeroDecoder)
  self.assertEqual(verify.verify_output(out,_private_test_only=True)["run_status"],"failed")
 def test_ready_selection_aggregation_reconstruction(self):
  out=self._out("ready");plan=run._prepare_test_plan(out,self._lock());model=run.build_adjacent_channel_model(plan["locked_data"]);rows=[]
  for s,p,c in plan["execution_order"]:
   d=run.generate_sacrificed_development(model,s);got=run.evaluate_candidate(d["alice_frames"],d["bob_frames"],model=model,plane_id=p,candidate_id=c,stratum=s,frame_ids=d["frame_ids"],decoder_factory=ZeroDecoder,max_runtime_s=5.0)[:2]
   for r in got:r.update(status="development_exact_success",exact_match=True,source_sha256=d["source_sha256"])
   rows.extend(got)
  run._finalize(out,plan,rows,"completed","completed")
  self.assertTrue(verify.verify_output(out,_private_test_only=True)["ready_for_synthetic_prepare"])
 def test_semantic_self_hashed_run_report_and_extra_key_rejected(self):
  base=self._out("semantic_base");run._prepare_test_plan(base,self._lock());run._execute_test_plan(base,ZeroDecoder)
  def mutate(name,file,key,value,hashkey):
   out=self._out(name);shutil.copytree(base,out);p=out/file;doc=json.loads(p.read_text());doc[key]=value;doc[hashkey]=run._sha(run._compact({k:v for k,v in doc.items() if k!=hashkey}));p.write_bytes(run._compact(doc))
   with self.assertRaises(ValueError):verify.verify_output(out,_private_test_only=True)
  mutate("run_semantic","development_run_manifest.json","run_status","failed","manifest_sha256")
  mutate("report_semantic","development_report.json","ready_for_synthetic_prepare",True,"report_sha256")
  mutate("run_extra","development_run_manifest.json","extra",1,"manifest_sha256")
 def test_plan_and_report_selection_semantic_tamper(self):
  base=self._out("bind_base");run._prepare_test_plan(base,self._lock());run._execute_test_plan(base,ZeroDecoder)
  for file,key,value,hashkey in (("pre_run_plan.json","caps",{"complete_run_s":1,"per_frame_s":5.0},"plan_sha256"),("development_report.json","selection_sha256","0"*64,"report_sha256")):
   out=self._out("bind");shutil.copytree(base,out);p=out/file;doc=json.loads(p.read_text());doc[key]=value;doc[hashkey]=run._sha(run._compact({k:v for k,v in doc.items() if k!=hashkey}));p.write_bytes(run._compact(doc))
   with self.assertRaises(ValueError):verify.verify_output(out,_private_test_only=True)
 def test_selection_exception_fails_and_keyboard_interrupt_escapes(self):
  out=self._out("selectfail");plan=run._prepare_test_plan(out,self._lock())
  rows=[]
  with patch.object(run,"select_candidates",side_effect=RuntimeError("selection")),patch.object(run,"aggregate_frame_development",side_effect=RuntimeError("selection")):
   run._finalize(out,plan,rows,"x","failed")
  self.assertEqual(json.loads((out/"development_run_manifest.json").read_text())["run_status"],"failed")
  out2=self._out("interrupt");run._prepare_test_plan(out2,self._lock())
  with patch.object(run,"evaluate_candidate",side_effect=KeyboardInterrupt),patch.object(run,"_finalize") as fin:
   with self.assertRaises(KeyboardInterrupt):run._execute_test_plan(out2,ZeroDecoder)
   fin.assert_not_called()
