from __future__ import annotations
import hashlib,json,os,shutil,tempfile,unittest
from pathlib import Path
import numpy as np
from unittest.mock import patch
from ldpc import BpOsdDecoder
from comparison_bench.src.comparison_bench.formal_ir.codebook_v4 import matrix_for
from comparison_bench.src.comparison_bench.formal_ir.ldpc_v4_channel import plane_error_channel
from comparison_bench.src.comparison_bench.formal_ir.ldpc_v4_development_v2 import evaluate_candidate,generate_sacrificed_development
from comparison_bench.src.comparison_bench.cli import run_ldpc_v4_development_v2 as run
from comparison_bench.src.comparison_bench.cli import verify_ldpc_v4_development_v2 as verify

def _compact(v):return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode("ascii")
def _model():
 c={"zero_count":12403,"plus_one_count":3865,"minus_one_count":116};t=16384;pp,pm=c["plus_one_count"]/t,c["minus_one_count"]/t
 b={"schema":"binary_ldpc_v4_adjacent_channel_v1","role":"sacrificed_calibration_only","dimension":1024,"mapping":"gray_msb_first","frame_len_symbols":256,"calibration_frame_count":64,"total_count":t,**c,"sign_convention":"signed_modular_alice_minus_bob","stress_scale":1.25,"probabilities":{"adjacent_nominal":{"plus_one":pp,"minus_one":pm,"zero":c["zero_count"]/t},"adjacent_stress_125":{"plus_one":pp*1.25,"minus_one":pm*1.25,"zero":1-(pp+pm)*1.25}},"source_lock_sha256":"1"*64,"source_manifest_sha256":"2"*64,"selected_frames_sha256":"3"*64,"calibration_bytes_sha256":"4"*64,"calibration_sha256":"5"*64,"source_main_ttbin_sha256":"6"*64,"source_chunk_ttbin_sha256":"7"*64}
 return {**b,"model_sha256":hashlib.sha256(_compact(b)).hexdigest()}
class Zero:
 def __init__(self,h,**kwargs):self.h=h
 def decode(self,s):return np.zeros(256,dtype=np.uint8)
class CorrectionTest(unittest.TestCase):
 def _lock(self):return json.loads(Path("comparison_bench/outputs_comparison/formal_ir_methods/20260726_v1_binary_ldpc_v3_synthetic/pre_run_plan.json").read_text())["locked_data"]
 def test_pinned_constructor_and_corrected_decode(self):
  model=_model();data=generate_sacrificed_development(model,"adjacent_nominal");h=matrix_for(0,0);ec=plane_error_channel(data["bob_frames"][0],0,"adjacent_nominal",model)
  self.assertIsInstance(ec,np.ndarray)
  with self.assertRaises(TypeError):BpOsdDecoder(h,error_channel=ec,max_iter=50,bp_method="product_sum",schedule="serial",omp_thread_count=1,serial_schedule_order=list(range(256)),osd_method="OSD_0",osd_order=0)
  fixed=np.asarray(ec,dtype=np.float64).tolist();self.assertEqual(len(fixed),256);self.assertTrue(all(isinstance(x,float) and np.isfinite(x) and 1e-6<=x<=.49 for x in fixed))
  BpOsdDecoder(h,error_channel=fixed,max_iter=50,bp_method="product_sum",schedule="serial",omp_thread_count=1,serial_schedule_order=list(range(256)),osd_method="OSD_0",osd_order=0)
  rows=evaluate_candidate(data["alice_frames"],data["bob_frames"],model=model,plane_id=0,candidate_id=0,stratum="adjacent_nominal",frame_ids=data["frame_ids"],max_runtime_s=5.0)
  self.assertTrue(all(r["status"]!="development_decoder_error" for r in rows))
 def test_v2_package_nonready_and_tamper_readonly(self):
  root=Path(tempfile.mkdtemp(prefix="v4corr_",dir=os.environ.get("FORMAL_IR_TEST_TMP","workspace")))
  try:
   v3=Path("comparison_bench/outputs_comparison/formal_ir_methods/20260726_v1_binary_ldpc_v3_synthetic/pre_run_plan.json")
   lock=json.loads(v3.read_text(encoding="utf-8"))["locked_data"]
   out=root/"pkg";run._prepare_test_plan(out,lock);run._execute_test_plan(out,Zero)
   got=verify.verify_output(out,_private_test_only=True);self.assertEqual(got["run_status"],"completed");self.assertFalse(got["ready_for_synthetic_prepare"])
   before={p.name:p.read_bytes() for p in out.iterdir()};verify.verify_output(out,_private_test_only=True);self.assertEqual(before,{p.name:p.read_bytes() for p in out.iterdir()})
   (out/"development_report.json").write_bytes(b"{}")
   with self.assertRaises(ValueError):verify.verify_output(out,_private_test_only=True)
  finally:shutil.rmtree(root,ignore_errors=True)
 def test_predecessor_and_semantic_tamper_rejection(self):
  v3=Path("comparison_bench/outputs_comparison/formal_ir_methods/20260726_v1_binary_ldpc_v3_synthetic/pre_run_plan.json")
  old=Path("comparison_bench/outputs_comparison/formal_ir_methods/20260727_v1_binary_ldpc_v4_development")
  self.assertEqual(run._predecessor(old)["artifact_sha256"],run.PREDECESSOR_SHA256)
  root=Path(tempfile.mkdtemp(prefix="v4corr_sem_",dir=os.environ.get("FORMAL_IR_TEST_TMP","workspace")))
  try:
   lock=json.loads(v3.read_text())["locked_data"];base=root/"base";run._prepare_test_plan(base,lock);run._execute_test_plan(base,Zero)
   for name,file,key,value,hashkey in (("plan","pre_run_plan.json","extra",1,"plan_sha256"),("run","development_run_manifest.json","extra",1,"manifest_sha256"),("report","development_report.json","ready_for_synthetic_prepare",True,"report_sha256"),("selection","development_selection.json","extra",1,"selection_sha256"),("outcome","development_plane_outcomes.csv",None,None,None)):
    out=root/name;shutil.copytree(base,out);p=out/file
    if key is None:p.write_bytes(p.read_bytes().replace(b",true,development_",b",maybe,development_",1))
    else:
     d=json.loads(p.read_text());d[key]=value;d[hashkey]=run._sha(run._compact({k:v for k,v in d.items() if k!=hashkey}));p.write_bytes(run._compact(d))
    with self.assertRaises(ValueError):verify.verify_output(out,_private_test_only=True)
  finally:shutil.rmtree(root,ignore_errors=True)
 def test_predecessor_bytes_and_independent_artifact_tamper(self):
  old=Path("comparison_bench/outputs_comparison/formal_ir_methods/20260727_v1_binary_ldpc_v4_development");root=Path(tempfile.mkdtemp(prefix="v4corr_ind_",dir=os.environ.get("FORMAL_IR_TEST_TMP","workspace")))
  try:
   copy=root/"old";shutil.copytree(old,copy)
   for name in run.PREDECESSOR_SHA256:
    p=copy/name;p.write_bytes(p.read_bytes()+b" ")
    with self.assertRaises(ValueError):run._predecessor(copy)
    p.write_bytes((old/name).read_bytes())
   base=root/"base";run._prepare_test_plan(base,self._lock());run._execute_test_plan(base,Zero)
   plan=root/"plan_pre";shutil.copytree(base,plan);p=plan/"pre_run_plan.json";d=json.loads(p.read_text());d["predecessor"]["artifact_sha256"]["x"]="0"*64;d["plan_sha256"]=run._sha(run._compact({k:v for k,v in d.items() if k!="plan_sha256"}));p.write_bytes(run._compact(d))
   with self.assertRaises(ValueError):verify.verify_output(plan,_private_test_only=True)
   for name in ("v4_channel_model.json","v4_candidate_manifest.json"):
    out=root/name;shutil.copytree(base,out);p=out/name;p.write_bytes(p.read_bytes()+b" ")
    with self.assertRaises(ValueError):verify.verify_output(out,_private_test_only=True)
   for field in ("source_sha256","matrix_sha256"):
    out=root/field;shutil.copytree(base,out);p=out/"development_plane_outcomes.csv";rows=p.read_text().splitlines();cols=rows[0].split(',');i=cols.index(field);parts=rows[1].split(',');parts[i]="0"*64;rows[1]=','.join(parts);p.write_text('\n'.join(rows)+'\n')
    with self.assertRaises(ValueError):verify.verify_output(out,_private_test_only=True)
  finally:shutil.rmtree(root,ignore_errors=True)
 def test_overwrite_exception_cap_partial_and_ready(self):
  root=Path(tempfile.mkdtemp(prefix="v4corr_exec_",dir=os.environ.get("FORMAL_IR_TEST_TMP","workspace")))
  try:
   out=root/"x";run._prepare_test_plan(out,self._lock())
   with self.assertRaises(FileExistsError):run._prepare_test_plan(out,self._lock())
   with patch.object(run,"generate_sacrificed_development",side_effect=RuntimeError("boom")):run._execute_test_plan(out,Zero)
   self.assertEqual({p.name for p in out.iterdir()},set(run.ARTIFACTS));self.assertEqual(verify.verify_output(out,_private_test_only=True)["run_status"],"failed")
   cap=root/"cap";run._prepare_test_plan(cap,self._lock())
   with patch.object(run.time,"monotonic",side_effect=[0.,1801.]):run._execute_test_plan(cap,Zero)
   self.assertEqual(verify.verify_output(cap,_private_test_only=True)["run_status"],"failed")
   ready=root/"ready";plan=run._prepare_test_plan(ready,self._lock());model=run.build_adjacent_channel_model(plan["locked_data"]);rows=[]
   for s,p,c in plan["execution_order"]:
    d=run.generate_sacrificed_development(model,s);got=run.evaluate_candidate(d["bob_frames"],d["bob_frames"],model=model,plane_id=p,candidate_id=c,stratum=s,frame_ids=d["frame_ids"],decoder_factory=Zero)[:2]
    for r in got:r.update(status="development_exact_success",exact_match=True,source_sha256=d["source_sha256"])
    rows.extend(got)
   run._finalize(ready,plan,rows,"completed","completed");self.assertTrue(verify.verify_output(ready,_private_test_only=True)["ready_for_synthetic_prepare"])
  finally:shutil.rmtree(root,ignore_errors=True)
