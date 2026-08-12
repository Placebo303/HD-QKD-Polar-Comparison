from __future__ import annotations
import json,os,shutil,unittest,uuid
from pathlib import Path
from unittest.mock import patch
import numpy as np
from comparison_bench.src.comparison_bench.cli import run_ldpc_v4_real_qualification as lane
from comparison_bench.src.comparison_bench.cli import verify_ldpc_v4_real_qualification as verify
from comparison_bench.src.comparison_bench.cli import run_ldpc_v4_synthetic_qualification as syn
from comparison_bench.src.comparison_bench.cli import verify_ldpc_v4_synthetic_qualification as synverify
from comparison_bench.src.comparison_bench.formal_ir import ldpc_v4_real_source as real_source
from comparison_bench.tests.test_ldpc_v4_synthetic_qualification import TestSyntheticV4 as _SyntheticFixture,ZeroDecoder
from comparison_bench.src.comparison_bench.utils.bitops import symbols_to_bits
TMP=Path(os.environ.get("FORMAL_IR_TEST_TMP","workspace/formal_ir_test_tmp"))
_REAL_GENERATE=syn._generate
_SyntheticFixture.__test__=False
def runzero(*a,**kw):
 from comparison_bench.src.comparison_bench.formal_ir.ldpc_v4 import run_ldpc_formal_v4
 return run_ldpc_formal_v4(*a,**kw,_decoder_factory=ZeroDecoder,_preflight_result={"status":"ok","dependency_version":"2.4.1","backend_name":"test"})
def real_success(alice,bob,**kw):
 from comparison_bench.src.comparison_bench.formal_ir.ldpc_v4 import run_ldpc_formal_v4
 errors=(symbols_to_bits(alice.astype(np.int64),1024,"gray")!=symbols_to_bits(bob.astype(np.int64),1024,"gray")).astype(np.uint8);state={"plane":0}
 class Decoder:
  def __init__(self,h,**unused):self.plane=state["plane"];state["plane"]+=1
  def decode(self,syndrome):return errors[:,self.plane]
 return run_ldpc_formal_v4(alice,bob,**kw,_decoder_factory=Decoder,_preflight_result={"status":"ok","dependency_version":"2.4.1","backend_name":"test"})
class TestRealV4(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  _SyntheticFixture.setUpClass();cls.dev=_SyntheticFixture._shared
  cls.synthetic=TMP/f"v4real_syn_shared_{uuid.uuid4().hex}";syn._prepare_test_plan(cls.synthetic,cls.dev)
  def gen(p,s):
   n=p["frame_count_per_stratum"];z=np.zeros((n,256),dtype=np.uint16);_,_,seeds=_REAL_GENERATE(p,s);return z,z.copy(),seeds
  with patch.object(syn,"_generate",side_effect=gen):syn._execute_test_plan(cls.synthetic,runzero);synverify.verify_output(cls.synthetic,_private_test_only=True)
  root=TMP/f"v4real_extension_{uuid.uuid4().hex}";root.mkdir(parents=True);main=root/"added.ttbin";chunk=root/"added.1.ttbin";main.write_bytes(b"added-main");chunk.write_bytes(b"added-chunk")
  sidecars={}
  for offset,(dataset_id,bw) in enumerate((("d1024_bw120",120),("d1024_bw180",180),("d1024_bw200",200))):
   sidecar=root/dataset_id;sidecar.mkdir(); values=(np.arange(256,dtype=np.uint16)+np.uint16(700+offset*100))%1024;np.save(sidecar/"a_eff.npy",values);np.save(sidecar/"b_eff.npy",values)
   meta={"joint_source_mode":"from_ttbin","joint_origin":"from_ttbin","materialize_origin":"materialized_from_ttbin","sequence_source_mode":"strict","sequence_is_sampled":False,"loss":20,"materialize_params":{"used_params":{"dimension":1024,"bin_width_ps":bw,"pairing_mode":"nearest","source_ttbin_paths":[str(main.resolve())]}}};(sidecar/"sidecar_meta.json").write_text(json.dumps(meta),encoding="utf-8");sidecars[dataset_id]=sidecar
  base=json.loads((cls.dev/"pre_run_plan.json").read_bytes())["locked_data"]["source_manifest"];cls.extension=root/"extension.json";real_source.write_extension(cls.extension,base,[{"main_ttbin":main,"chunk_ttbin":chunk,"sidecar_dirs":sidecars}])
 def out(self,n):return TMP/f"v4real_{n}_{uuid.uuid4().hex}"
 def promoted(self):
  d=self.out("syn");shutil.copytree(self.synthetic,d);return d
 def gen(self,p,s):
  n=p["frame_count_per_stratum"];z=np.zeros((n,256),dtype=np.uint16);_,_,seeds=_REAL_GENERATE(p,s);return z,z.copy(),seeds
 def test_block_selection_order_and_readonly(self):
  s=self.promoted();o=self.out("real")
  with patch.object(syn,"_generate",side_effect=self.gen):p=lane._prepare_test_plan(o,s,self.extension)
  self.assertEqual({x.name for x in o.iterdir()},set(lane.ARTIFACTS[:2]));self.assertEqual(len(p["execution_order"]),6)
  lock=json.loads((o/"real_data_lock.json").read_text());self.assertEqual(len(lock["selected_frames"]),6);self.assertTrue(set(lock["v3_reserved_confirmation_identities"]).isdisjoint({x["frame_identity"] for x in lock["selected_frames"]}))
  with patch.object(syn,"_generate",side_effect=self.gen):lane._execute_test_plan(o,real_success)
  with patch.object(syn,"_generate",side_effect=self.gen):r=verify.verify_output(o,_private_test_only=True)
  self.assertTrue(r["promoted"]);before={x.name:x.read_bytes() for x in o.iterdir()}
  with patch.object(syn,"_generate",side_effect=self.gen):verify.verify_output(o,_private_test_only=True)
  self.assertEqual(before,{x.name:x.read_bytes() for x in o.iterdir()})
 def test_block_nonpromotion_tamper_overwrite(self):
  s=self.promoted();o=self.out("bad")
  with patch.object(syn,"_generate",side_effect=self.gen):lane._prepare_test_plan(o,s,self.extension)
  def unavailable(*a,**kw):
   from comparison_bench.src.comparison_bench.formal_ir.ldpc_v4 import run_ldpc_formal_v4
   return run_ldpc_formal_v4(*a,**kw,_preflight_result={"status":"backend_unavailable","dependency_version":""})
  with patch.object(syn,"_generate",side_effect=self.gen):lane._execute_test_plan(o,unavailable)
  with patch.object(syn,"_generate",side_effect=self.gen):self.assertFalse(verify.verify_output(o,_private_test_only=True)["promoted"])
  with self.assertRaises(FileExistsError):lane._prepare_test_plan(o,s,self.extension)
  bad=self.out("tamper");shutil.copytree(o,bad);(bad/"real_data_lock.json").write_bytes((bad/"real_data_lock.json").read_bytes()+b" ")
  with self.assertRaises(ValueError):verify.verify_output(bad,_private_test_only=True)
 def test_strict_prerequisite_and_self_hashed_lock_tamper(self):
  s=self.promoted();un=self.out("unpromoted");shutil.copytree(s,un);rep=json.loads((un/"formal_qualification_report.json").read_bytes());rep["promoted"]=False;rep["report_sha256"]=syn._sha(syn._compact({k:v for k,v in rep.items() if k!="report_sha256"}));(un/"formal_qualification_report.json").write_bytes(syn._compact(rep))
  with patch.object(syn,"_generate",side_effect=self.gen):
   with self.assertRaises(ValueError):lane._prepare_test_plan(self.out("blocked"),un,self.extension)
  o=self.out("lock");
  with patch.object(syn,"_generate",side_effect=self.gen):lane._prepare_test_plan(o,s,self.extension)
  lock=json.loads((o/"real_data_lock.json").read_bytes());lock["v3_reserved_confirmation_identities"]=[];lock["lock_sha256"]=lane._sha(lane._compact({k:v for k,v in lock.items() if k!="lock_sha256"}));plan=json.loads((o/"pre_run_plan.json").read_bytes());plan["real_data_lock_sha256"]=lock["lock_sha256"];plan["plan_sha256"]=lane._sha(lane._compact({k:v for k,v in plan.items() if k!="plan_sha256"}));(o/"real_data_lock.json").write_bytes(lane._compact(lock));(o/"pre_run_plan.json").write_bytes(lane._compact(plan))
  with patch.object(syn,"_generate",side_effect=self.gen):
   with self.assertRaises(ValueError):verify.verify_output(o,_private_test_only=True)
 def test_capacity_failure_before_output_creation(self):
  s=self.promoted();o=self.out("capacity")
  self.assertFalse(o.exists())
  with patch.object(syn,"_generate",side_effect=self.gen):
   with self.assertRaises(ValueError): lane._prepare_test_plan(o,s,self.extension,count=128)
  self.assertFalse(o.exists())
 def test_semantic_tamper_collision_and_partial(self):
  s=self.promoted();o=self.out("semantic")
  with patch.object(syn,"_generate",side_effect=self.gen):lane._prepare_test_plan(o,s,self.extension);lane._execute_test_plan(o,real_success);verify.verify_output(o,_private_test_only=True)
  # Change a public syndrome payload, then make the transcript CSV and DAG self-consistent.
  def public_tamper(name,index,payload):
   t=self.out(name);shutil.copytree(o,t);events=[json.loads(x) for x in (t/"formal_transcript.jsonl").read_bytes().splitlines()];events[index]["payload"]=payload;eventfn=__import__('comparison_bench.src.comparison_bench.formal_ir.shared',fromlist=['canonical_event']).canonical_event;raw=b"".join(eventfn(x) for x in events);(t/"formal_transcript.jsonl").write_bytes(raw);rows=verify._rows(t/"formal_frame_outcomes.csv");first=b"".join(eventfn(x) for x in events[:13]);rows[0]["transcript_bytes_len"]=len(first);rows[0]["transcript_bytes_sha256"]=lane._sha(first);rows[0]["transcript_sha256"]=lane._sha(first);(t/"formal_frame_outcomes.csv").write_bytes(syn._csv(rows));run=json.loads((t/"formal_run_manifest.json").read_bytes());run["artifact_index"]={n:{"sha256":lane._sha((t/n).read_bytes()),"bytes":(t/n).stat().st_size} for n in lane.ARTIFACTS[:7]};run["manifest_sha256"]=lane._sha(lane._compact({k:v for k,v in run.items() if k!="manifest_sha256"}));(t/"formal_run_manifest.json").write_bytes(lane._compact(run));rep=json.loads((t/"formal_qualification_report.json").read_bytes());rep["run_manifest_sha256"]=lane._sha((t/"formal_run_manifest.json").read_bytes());rep["report_sha256"]=lane._sha(lane._compact({k:v for k,v in rep.items() if k!="report_sha256"}));(t/"formal_qualification_report.json").write_bytes(lane._compact(rep));return t
  t=public_tamper("syndrome",0,{"syndrome":"00"})
  with patch.object(syn,"_generate",side_effect=self.gen):
   with self.assertRaises(ValueError):verify.verify_output(t,_private_test_only=True)
  tag=public_tamper("tag",11,{"tag":"00"})
  with patch.object(syn,"_generate",side_effect=self.gen):
   with self.assertRaises(ValueError):verify.verify_output(tag,_private_test_only=True)
  c=self.out("collision");shutil.copytree(o,c);lock=json.loads((c/"real_data_lock.json").read_bytes());v3=int(next(iter(json.loads((s/"pre_run_plan.json").read_bytes())["v3_seed_binding"]["root_seeds"].values())));root=v3.to_bytes(16,"big").hex();lock["toeplitz"]["roots"][lane.STRATA[0]]["root_hex"]=root;lock["toeplitz"]["roots"][lane.STRATA[0]]["root_id"]=lane._root_id(root);lock["toeplitz"]["roots"][lane.STRATA[0]]["seeds"]=lane._seeds(root,lane.STRATA[0],2);lock["lock_sha256"]=lane._sha(lane._compact({k:v for k,v in lock.items() if k!="lock_sha256"}));plan=json.loads((c/"pre_run_plan.json").read_bytes());plan["real_data_lock_sha256"]=lock["lock_sha256"];plan["plan_sha256"]=lane._sha(lane._compact({k:v for k,v in plan.items() if k!="plan_sha256"}));(c/"real_data_lock.json").write_bytes(lane._compact(lock));(c/"pre_run_plan.json").write_bytes(lane._compact(plan))
  with patch.object(syn,"_generate",side_effect=self.gen):
   with self.assertRaises(ValueError):verify.verify_output(c,_private_test_only=True)
  q=self.out("partial")
  with patch.object(syn,"_generate",side_effect=self.gen):lane._prepare_test_plan(q,s,self.extension)
  calls={"n":0}
  def partial(*a,**kw):
   calls["n"]+=1
   if calls["n"]>1:raise RuntimeError("stop")
   return real_success(*a,**kw)
  with patch.object(syn,"_generate",side_effect=self.gen):lane._execute_test_plan(q,partial);self.assertEqual(verify.verify_output(q,_private_test_only=True)["run_status"],"failed")
