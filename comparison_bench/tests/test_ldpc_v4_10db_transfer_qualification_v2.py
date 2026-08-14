from __future__ import annotations
import copy,json,os,shutil,unittest,uuid
from pathlib import Path
from unittest.mock import patch
import numpy as np
from comparison_bench.src.comparison_bench.cli import run_ldpc_v4_10db_transfer_qualification_v2 as lane
from comparison_bench.src.comparison_bench.cli import verify_ldpc_v4_10db_transfer_qualification_v2 as verify
from comparison_bench.src.comparison_bench.formal_ir.ldpc_v4 import run_ldpc_formal_v4
from comparison_bench.src.comparison_bench.formal_ir import codebook_v4

class TestTransfer10dBV2(unittest.TestCase):
 def setUp(self):
  self.root=Path(os.environ.get("FORMAL_IR_TEST_TMP","workspace"))/f"v4_10db_transfer_{uuid.uuid4().hex}";self.root.mkdir(parents=True)
  prereq=lane.PREREQUISITE;pre=json.loads((prereq/"pre_run_plan.json").read_bytes());self.bind=pre["development_binding"]
  self.syn={"path":str(prereq.resolve()),"hashes":{n:lane._sha((prereq/n).read_bytes()) for n in lane.PREREQ_HASHES},"docs":{"pre_run_plan.json":pre}}
  (self.root/"pre_run_plan.json").write_bytes(lane._compact({"development_binding":self.bind}))
  rows=[]
  for st in lane.STRATA:
   for i in range(2):rows.append({"stratum":st,"frame_id":i,"selection_rank":f"{st}{i}","frame_identity":f"{st}f{i}","payload_identity":f"{st}p{i}"})
  self.lock={"schema":"binary_ldpc_v4_10db_source_lock_v1","datasets":[],"selected_frames":rows};self.lock["lock_sha256"]=lane._sha(lane._compact(self.lock))
 def tearDown(self):shutil.rmtree(self.root,ignore_errors=True)
 def fake_synthetic(self,*a,**kw):return copy.deepcopy(self.syn)
 def fake_prior(self,*args):return set(),set()
 def test_plan_order_gate_and_no_overwrite(self):
  out=self.root/'out'
  with patch.object(lane,"_synthetic",self.fake_synthetic),patch.object(lane,"_prior_sets",self.fake_prior):
   p=lane._prepare_test_plan(out,self.root,self.lock,count=2)
  self.assertEqual(len(p['execution_order']),6);self.assertEqual(p['gate']['denominator'],2);self.assertEqual(p['gate']['verified_success_floor'],2)
  self.assertEqual(set(p['source_sha256']),{"runner","verifier","source","method","codebook","channel","shared","synthetic_runner","synthetic_verifier"})
  self.assertEqual([x['stratum'] for x in self.lock['selected_frames']],['d1024_bw120','d1024_bw120','d1024_bw180','d1024_bw180','d1024_bw200','d1024_bw200'])
  with patch.object(lane,"_synthetic",self.fake_synthetic),patch.object(lane,"_prior_sets",self.fake_prior):
   with self.assertRaises(FileExistsError):lane._prepare_test_plan(out,self.root,self.lock,count=2)
 def test_replay_matrix_cache_identity_isolation_bound_and_restoration(self):
  original=lane.synthetic_verify.matrix_for;original_entry=lane.synthetic_verify.development_verify.candidate_entry;original_rows=lane.synthetic_verify.development_verify._rows;calls=[];entry_calls=[]
  def counted(plane_id,candidate_id):calls.append((plane_id,candidate_id));return original(plane_id,candidate_id)
  def counted_entry(plane_id,candidate_id):entry_calls.append((plane_id,candidate_id));return original_entry(plane_id,candidate_id)
  with patch.object(lane.synthetic_verify,"matrix_for",counted),patch.object(lane.synthetic_verify.development_verify,"candidate_entry",counted_entry):
   with lane._replay_matrix_cache() as cache:
    for plane_id in codebook_v4.PLANE_IDS:
     for candidate_id in codebook_v4.CANDIDATE_IDS:
      expected,_=codebook_v4.generate_candidate(plane_id,candidate_id);first=lane.synthetic_verify.matrix_for(plane_id,candidate_id);second=lane.synthetic_verify.matrix_for(plane_id,candidate_id)
      self.assertEqual(first.tobytes(),expected.tobytes());self.assertEqual(second.tobytes(),expected.tobytes());self.assertTrue(first.flags.writeable);first[0,0]^=1;self.assertTrue(np.array_equal(second,expected))
      first_entry=lane.synthetic_verify.development_verify.candidate_entry(plane_id,candidate_id);second_entry=lane.synthetic_verify.development_verify.candidate_entry(plane_id,candidate_id);first_entry['plane_id']=-1;self.assertEqual(second_entry['plane_id'],plane_id)
    self.assertEqual(len(cache['matrices']),40);self.assertEqual(len(cache['candidates']),40);self.assertEqual(len(calls),40);self.assertEqual(len(entry_calls),40)
   self.assertIs(lane.synthetic_verify.matrix_for,counted)
   self.assertIs(lane.synthetic_verify.development_verify.candidate_entry,counted_entry)
   self.assertIs(lane.synthetic_verify.development_verify._rows,original_rows)
   with self.assertRaises(RuntimeError):
    with lane._replay_matrix_cache():
     lane.synthetic_verify.matrix_for(0,0);raise RuntimeError("test")
   self.assertIs(lane.synthetic_verify.matrix_for,counted)
   self.assertIs(lane.synthetic_verify.development_verify.candidate_entry,counted_entry)
   self.assertIs(lane.synthetic_verify.development_verify._rows,original_rows)
  self.assertIs(lane.synthetic_verify.matrix_for,original);self.assertIs(lane.synthetic_verify.development_verify.candidate_entry,original_entry);self.assertIs(lane.synthetic_verify.development_verify._rows,original_rows);self.assertEqual(codebook_v4.candidate_manifest()['manifest_sha256'],'a4f836bb6ae46cd277ae632c469e6155c1ec18d1ed687eb515e1a925d1d85556')
 def test_linear_development_rows_equivalence_and_malformed_rejection(self):
  development=lane.synthetic_verify.development_verify;row={"role":"sacrificed_calibration_only","stratum_id":"adjacent_nominal","plane_id":0,"candidate_id":0,"channel_model_sha256":"a"*64,"policy_sha256":"b"*64,"matrix_sha256":"c"*64,"candidate_valid":True,"backend_identity":"ldpc==2.4.1","frame_id":"v4dev_adjacent_nominal_f000","attempted":True,"status":"development_exact_success","exact_match":True,"syndrome_bits_disclosed":16,"runtime_s":0.0,"source_sha256":"d"*64}
  path=self.root/'rows.csv';path.write_bytes(development.lane._csv([row]));self.assertEqual(lane._linear_development_rows(path),development._rows(path))
  for name,raw in (("missing_newline",path.read_bytes().rstrip(b"\n")),("bad_bool",path.read_bytes().replace(b"true",b"maybe",1)),("bad_runtime",path.read_bytes().replace(b"0.0",b"nan",1)),("noncanonical",path.read_bytes().replace(b"0.0",b"0.00",1))):
   bad=self.root/name;bad.write_bytes(raw)
   with self.subTest(case=name):
    with self.assertRaises(ValueError):development._rows(bad)
    with self.assertRaises(ValueError):lane._linear_development_rows(bad)
 def test_strict_synthetic_prerequisite_replay_is_promoted_without_decoder(self):
  got=lane._synthetic(lane.PREREQUISITE,False)
  self.assertEqual(got['docs']['pre_run_plan.json']['run_id'],'binary_ldpc_v4_synthetic_qualification_v2')
 def test_roots_are_unique_and_tamper_rejected(self):
  with patch.object(lane,"_prior_sets",self.fake_prior):roots=lane._roots(self.syn,2);lane._validate_roots(roots,self.syn,2)
  bad=copy.deepcopy(roots);bad[lane.STRATA[1]]['root_hex']=bad[lane.STRATA[0]]['root_hex'];bad[lane.STRATA[1]]['root_id']=lane._root_id(bad[lane.STRATA[1]]['root_hex']);bad[lane.STRATA[1]]['seeds']=lane._seeds(bad[lane.STRATA[1]]['root_hex'],lane.STRATA[1],2)
  with patch.object(lane,"_prior_sets",self.fake_prior):
   with self.assertRaises(ValueError):lane._validate_roots(bad,self.syn,2)
 def test_predecessor_and_existing_real_root_seed_isolation(self):
  predecessor=json.loads((lane.PREDECESSOR/'pre_run_plan.json').read_text())
  old_roots,old_seeds=lane._plan_root_sets(predecessor)
  self.assertEqual(len(old_roots),3);self.assertEqual(len(old_seeds),384)
  existing={"roots":{"d1024_bw120":{"root_hex":"1"*32,"seeds":[{"seed_id":"f"*64}]}}}
  existing_path=self.root/'existing_plan.json';existing_path.write_bytes(lane._compact(existing))
  with patch.object(lane,'_existing_real_plans',return_value=[{'path':str(existing_path),'sha256':lane._sha(existing_path.read_bytes())}]):
   roots,seeds=lane._prior_sets(self.syn,{'path':str(lane.PREDECESSOR)})
  self.assertTrue(old_roots <= roots);self.assertTrue(old_seeds <= seeds);self.assertIn(int('1'*32,16),roots);self.assertIn('f'*64,seeds)
  colliding={lane.STRATA[0]:{"root_hex":next(iter(predecessor['roots'].values()))['root_hex'],"root_id":"","seeds":[]}}
  for st in lane.STRATA[1:]:colliding[st]={"root_hex":"0"*32,"root_id":lane._root_id("0"*32),"seeds":lane._seeds("0"*32,st,2)}
  colliding[lane.STRATA[0]]["root_id"]=lane._root_id(colliding[lane.STRATA[0]]["root_hex"]);colliding[lane.STRATA[0]]["seeds"]=lane._seeds(colliding[lane.STRATA[0]]["root_hex"],lane.STRATA[0],2)
  with patch.object(lane,'_existing_real_plans',return_value=[]):
   with self.assertRaises(ValueError):lane._validate_roots(colliding,self.syn,2,{'path':str(lane.PREDECESSOR)})
 def test_prepare_rejects_source_capacity_and_binding_tamper(self):
  out=self.root/'cap';small=copy.deepcopy(self.lock);small['selected_frames']=small['selected_frames'][:-1];small['lock_sha256']=lane._sha(lane._compact({k:v for k,v in small.items() if k!='lock_sha256'}))
  with patch.object(lane,"_synthetic",self.fake_synthetic),patch.object(lane,"_prior_sets",self.fake_prior):
   with self.assertRaises(ValueError):lane._prepare_test_plan(out,self.root,small,count=2)
  self.assertFalse(out.exists())
 def test_fixed_production_prerequisite_path_and_hashes(self):
  with self.assertRaises(ValueError):lane._synthetic(self.root,False)
 def test_partial_exception_finalization_retains_nine_artifacts(self):
  out=self.root/'partial';out.mkdir();p={"synthetic":{"path":str(self.root)},"plan_sha256":"p","frame_count_per_stratum":2,"gate":{"verified_success_floor":2}}
  (out/'pre_run_plan.json').write_bytes(lane._compact(p));(out/'real_data_lock.json').write_bytes(lane._compact(self.lock))
  lane._finalize(out,p,self.lock,[],[],"failed","RuntimeError:stop")
  self.assertEqual({x.name for x in out.iterdir()},set(lane.ARTIFACTS))
  report=json.loads((out/'formal_qualification_report.json').read_text())
  self.assertFalse(report['promoted']);self.assertEqual(report['run_status'],'failed');self.assertTrue(report['source_relocation'])
 def _result(self,kw):
  d={k:"" for k in lane.syn.OUTCOME_FIELDS};d.update({"dataset_id":kw["dataset_id"],"frame_id":kw["frame_id"],"n_pairs":256,"method":"ldpc_formal_v4","attempted":True,"denominator_included":True,"status":"verified_success","failure_reason":"","dimension":1024,"frame_len_symbols":256,"raw_ser":0.0,"verification_invoked":False,"verification_seed_id":"","verification_tag_bits":0,"epsilon_ec":0.0,"key_dependent_disclosure_bits_total":0,"public_control_bits_total":0,"runtime_s":0.0,"decoder_call_count":0,"verification_check_count":0,"ldpc_syndrome_bits":0,"verification_tag_bits_component":0,"mapping":"gray","leakage_comparison_policy":"","backend_name":"test","backend_version":"test"});return {"outcome":d,"events":[]}
 def _patches(self):
  return (patch.object(lane,"_synthetic",self.fake_synthetic),patch.object(lane,"_prior_sets",self.fake_prior),patch.object(lane.source,"build_source_lock",return_value=copy.deepcopy(self.lock)),patch.object(lane.source,"arrays_for_frame",side_effect=lambda _l,f:(np.zeros(256,dtype=np.uint16),np.zeros(256,dtype=np.uint16))))
 def _executed(self):
  out=self.root/'executed'
  with patch.object(lane,"_synthetic",self.fake_synthetic),patch.object(lane,"_prior_sets",self.fake_prior):lane._prepare_test_plan(out,self.root,self.lock,count=2)
  ps=self._patches()
  class Zero:
   def __init__(self,*a,**k):pass
   def decode(self,*a,**k):return np.zeros(256,dtype=np.uint8)
  with ps[0],ps[1],ps[2],ps[3]:lane._execute_test_plan(out,lambda a,b,**kw:run_ldpc_formal_v4(a,b,**kw,_decoder_factory=Zero,_preflight_result={"status":"ok","dependency_version":"2.4.1","backend_name":"test"}))
  return out
 def test_private_execute_verify_and_readonly(self):
  out=self._executed();before={x.name:lane._sha(x.read_bytes()) for x in out.iterdir()};ps=self._patches()
  with ps[0],ps[1],ps[2],ps[3]:got=verify.verify_output(out,_private_test_only=True)
  self.assertEqual(got['outcomes'],6,json.loads((out/'formal_qualification_report.json').read_text()));self.assertTrue(got['promoted']);self.assertEqual(before,{x.name:lane._sha(x.read_bytes()) for x in out.iterdir()})
 def test_package_tamper_matrix_rejected(self):
  out=self._executed();targets=lane.ARTIFACTS
  ps=self._patches()
  for name in targets:
   copy=self.root/("tamper_"+name.replace('.','_'));shutil.copytree(out,copy);raw=(copy/name).read_bytes();(copy/name).write_bytes(raw+b" ")
   with ps[0],ps[1],ps[2],ps[3]:
    with self.assertRaises(ValueError):verify.verify_output(copy,_private_test_only=True)
 def _resign(self,d):
  run=json.loads((d/'formal_run_manifest.json').read_text());run['artifact_index']={n:{'sha256':lane._sha((d/n).read_bytes()),'bytes':(d/n).stat().st_size} for n in lane.ARTIFACTS[:7]};run['manifest_sha256']=lane._sha(lane._compact({k:v for k,v in run.items() if k!='manifest_sha256'}));(d/'formal_run_manifest.json').write_bytes(lane._compact(run))
  rep=json.loads((d/'formal_qualification_report.json').read_text());
  if rep.get('run_manifest_sha256')!='0'*64:rep['run_manifest_sha256']=lane._sha((d/'formal_run_manifest.json').read_bytes())
  rep['report_sha256']=lane._sha(lane._compact({k:v for k,v in rep.items() if k!='report_sha256'}));(d/'formal_qualification_report.json').write_bytes(lane._compact(rep))
 def test_semantic_resigned_matrix_rejected(self):
  out=self._executed();ps=self._patches()
  cases=[]
  def outcome(d):
   rows=verify._rows(d/'formal_frame_outcomes.csv');rows[0]['status']='decode_failed';(d/'formal_frame_outcomes.csv').write_bytes(lane.syn._csv(rows))
  def plan(d):
   p=json.loads((d/'pre_run_plan.json').read_text());p['execution_order'][0]='d1024_bw120:forged';p['plan_sha256']=lane._sha(lane._compact({k:v for k,v in p.items() if k!='plan_sha256'}));(d/'pre_run_plan.json').write_bytes(lane._compact(p))
  def lock(d):
   l=json.loads((d/'real_data_lock.json').read_text());l['selected_frames'][0]['frame_id']=1;l['lock_sha256']=lane._sha(lane._compact({k:v for k,v in l.items() if k!='lock_sha256'}));(d/'real_data_lock.json').write_bytes(lane._compact(l));p=json.loads((d/'pre_run_plan.json').read_text());p['source_lock_sha256']=l['lock_sha256'];p['plan_sha256']=lane._sha(lane._compact({k:v for k,v in p.items() if k!='plan_sha256'}));(d/'pre_run_plan.json').write_bytes(lane._compact(p))
  def root(d):
   p=json.loads((d/'pre_run_plan.json').read_text());r=p['roots'][lane.STRATA[0]];r['root_hex']='0'*32;r['root_id']=lane._root_id(r['root_hex']);r['seeds']=lane._seeds(r['root_hex'],lane.STRATA[0],2);p['plan_sha256']=lane._sha(lane._compact({k:v for k,v in p.items() if k!='plan_sha256'}));(d/'pre_run_plan.json').write_bytes(lane._compact(p))
  def leak(d):
   rows=verify._rows(d/'formal_frame_outcomes.csv');rows[0]['key_dependent_disclosure_bits_total']=1;(d/'formal_frame_outcomes.csv').write_bytes(lane.syn._csv(rows))
  def seed(d):
   rows=verify._rows(d/'formal_frame_outcomes.csv');rows[0]['verification_invoked']=True;rows[0]['verification_seed_id']='0'*64;(d/'formal_frame_outcomes.csv').write_bytes(lane.syn._csv(rows))
  def report(d):
   r=json.loads((d/'formal_qualification_report.json').read_text());r['promoted']=False;(d/'formal_qualification_report.json').write_bytes(lane._compact(r))
  def synthetic(d):
   p=json.loads((d/'pre_run_plan.json').read_text());p['synthetic']['artifact_hashes']['pre_run_plan.json']='0'*64;p['plan_sha256']=lane._sha(lane._compact({k:v for k,v in p.items() if k!='plan_sha256'}));(d/'pre_run_plan.json').write_bytes(lane._compact(p))
  def provenance(d):
   rows=verify._rows(d/'formal_frame_outcomes.csv');rows[0]['alice_sha256']='0'*64;(d/'formal_frame_outcomes.csv').write_bytes(lane.syn._csv(rows))
  def accounting(d):
   rows=verify._rows(d/'formal_frame_outcomes.csv');rows[0]['denominator_included']=False;(d/'formal_frame_outcomes.csv').write_bytes(lane.syn._csv(rows))
  def transcript(d):
   ev=[json.loads(x) for x in (d/'formal_transcript.jsonl').read_bytes().splitlines()];ev[0]['event_id']='forged';raw=b''.join(lane.canonical_event(x) for x in ev);(d/'formal_transcript.jsonl').write_bytes(raw);rows=verify._rows(d/'formal_frame_outcomes.csv');end=next(i for i,x in enumerate(ev) if x.get('frame_key')!=ev[0].get('frame_key')) if any(x.get('frame_key')!=ev[0].get('frame_key') for x in ev) else len(ev);blob=b''.join(lane.canonical_event(x) for x in ev[:end]);rows[0]['transcript_bytes_len']=len(blob);rows[0]['transcript_bytes_sha256']=lane._sha(blob);rows[0]['transcript_sha256']=lane._sha(blob);(d/'formal_frame_outcomes.csv').write_bytes(lane.syn._csv(rows))
  def relocation(d):
   r=json.loads((d/'formal_qualification_report.json').read_text());r['source_relocation']=False;(d/'formal_qualification_report.json').write_bytes(lane._compact(r))
  def run_contract(d):
   r=json.loads((d/'formal_run_manifest.json').read_text());r['outcome_count']=0;(d/'formal_run_manifest.json').write_bytes(lane._compact(r))
  def report_link(d):
   r=json.loads((d/'formal_qualification_report.json').read_text());r['run_manifest_sha256']='0'*64;(d/'formal_qualification_report.json').write_bytes(lane._compact(r))
  def method_manifest(d):
   x=json.loads((d/'formal_selection_manifest.json').read_text());x['method_id']='forged';(d/'formal_selection_manifest.json').write_bytes(lane._compact(x))
  for name,fn in (('outcome_status',outcome),('plan_order',plan),('source_lock',lock),('synthetic_binding',synthetic),('root_seed',root),('frame_provenance',provenance),('leakage',leak),('verification_seed',seed),('outcome_accounting',accounting),('canonical_transcript_public',transcript),('run_contract',run_contract),('report_linkage',report_link),('method_manifest',method_manifest),('report_promoted',report),('source_relocation',relocation)):
   d=self.root/name;shutil.copytree(out,d);fn(d);self._resign(d)
   with self.subTest(case=name),ps[0],ps[1],ps[2],ps[3]:
    with self.assertRaises(ValueError):verify.verify_output(d,_private_test_only=True)
 def _reject_case(self,out,name,mutate,*,prior=None):
  d=self.root/name;shutil.copytree(out,d);mutate(d);self._resign(d);ps=self._patches()
  with self.subTest(case=name),ps[0],ps[1],ps[2],ps[3]:
   with self.assertRaises(ValueError):verify.verify_output(d,_private_test_only=True)
 def _plan_doc(self,d):return json.loads((d/'pre_run_plan.json').read_text())
 def _write_plan(self,d,p):
  p['plan_sha256']=lane._sha(lane._compact({k:v for k,v in p.items() if k!='plan_sha256'}));(d/'pre_run_plan.json').write_bytes(lane._compact(p))
 def _write_lock(self,d,l):
  l['lock_sha256']=lane._sha(lane._compact({k:v for k,v in l.items() if k!='lock_sha256'}));(d/'real_data_lock.json').write_bytes(lane._compact(l));p=self._plan_doc(d);p['source_lock_sha256']=l['lock_sha256'];self._write_plan(d,p)
 def test_plan_contract_semantic_cases(self):
  out=self._executed()
  def extra(d):p=self._plan_doc(d);p['extra']=1;self._write_plan(d,p)
  def missing(d):p=self._plan_doc(d);del p['method_id'];self._write_plan(d,p)
  def backend(d):p=self._plan_doc(d);p['backend_requirement']='forged';self._write_plan(d,p)
  def caps(d):p=self._plan_doc(d);p['caps']['per_frame']['events']=31;self._write_plan(d,p)
  def denominator(d):p=self._plan_doc(d);p['gate']['denominator']=3;self._write_plan(d,p)
  def forbidden(d):p=self._plan_doc(d);p['gate']['forbidden_statuses']=[];self._write_plan(d,p)
  for name,fn in (('plan_extra_key',extra),('plan_missing_key',missing),('plan_backend',backend),('plan_caps',caps),('plan_gate_denominator',denominator),('plan_gate_forbidden',forbidden)):self._reject_case(out,name,fn)
 def test_collision_semantic_cases(self):
  out=self._executed()
  def root(d):
   p=self._plan_doc(d);r=p['roots'][lane.STRATA[1]];r['root_hex']=p['roots'][lane.STRATA[0]]['root_hex'];r['root_id']=lane._root_id(r['root_hex']);r['seeds']=lane._seeds(r['root_hex'],lane.STRATA[1],2);self._write_plan(d,p)
  def seed(d):
   p=self._plan_doc(d);p['roots'][lane.STRATA[1]]['seeds'][0]=copy.deepcopy(p['roots'][lane.STRATA[0]]['seeds'][0]);self._write_plan(d,p)
  for name,fn in (('collision_v3_root',root),('collision_development_root',root),('collision_synthetic_root',root),('collision_own_root',root),('collision_prior_seed',seed),('collision_own_seed',seed)):self._reject_case(out,name,fn)
 def test_run_and_report_contract_semantic_cases(self):
  out=self._executed()
  def run_field(key,value):
   def f(d):r=json.loads((d/'formal_run_manifest.json').read_text());r[key]=value;(d/'formal_run_manifest.json').write_bytes(lane._compact(r))
   return f
  def run_extra(d):r=json.loads((d/'formal_run_manifest.json').read_text());r['extra']=1;(d/'formal_run_manifest.json').write_bytes(lane._compact(r))
  for name,fn in (('run_schema',run_field('schema','forged')),('run_id',run_field('run_id','forged')),('run_status_reason',run_field('stop_reason','bad')),('run_plan_sha',run_field('plan_sha256','0'*64)),('run_outcome_count',run_field('outcome_count',0)),('run_extra_key',run_extra)):self._reject_case(out,name,fn)
  def report_field(key,value):
   def f(d):r=json.loads((d/'formal_qualification_report.json').read_text());r[key]=value;(d/'formal_qualification_report.json').write_bytes(lane._compact(r))
   return f
  def report_extra(d):r=json.loads((d/'formal_qualification_report.json').read_text());r['extra']=1;(d/'formal_qualification_report.json').write_bytes(lane._compact(r))
  for name,fn in (('report_schema',report_field('schema','forged')),('report_id',report_field('run_id','forged')),('report_status_reason',report_field('stop_reason','bad')),('report_plan_sha',report_field('plan_sha256','0'*64)),('report_manifest_sha',report_field('run_manifest_sha256','0'*64)),('report_gates',report_field('promotion_gates',{})),('report_extra_key',report_extra),('completed_partial_denominator',lambda d:self._completed_partial(d))):self._reject_case(out,name,fn)
 def _completed_partial(self,d):
  rows=verify._rows(d/'formal_frame_outcomes.csv');rows[0]['denominator_included']=False;(d/'formal_frame_outcomes.csv').write_bytes(lane.syn._csv(rows))
 def test_method_and_public_payload_semantic_cases(self):
  out=self._executed()
  def codebook(d):x=json.loads((d/'formal_codebook_manifest.json').read_text());x['method_id']='forged';(d/'formal_codebook_manifest.json').write_bytes(lane._compact(x))
  def selection(d):x=json.loads((d/'formal_selection_manifest.json').read_text());x['method_id']='forged';(d/'formal_selection_manifest.json').write_bytes(lane._compact(x))
  def channel(d):x=json.loads((d/'formal_channel_model.json').read_text());x['method_id']='forged';(d/'formal_channel_model.json').write_bytes(lane._compact(x))
  def public(d):
   events=[json.loads(x) for x in (d/'formal_transcript.jsonl').read_bytes().splitlines()];event=next(x for x in events if x['event_type']=='SYNDROME');value=event['payload']['syndrome'];event['payload']['syndrome']=('1' if value[0]=='0' else '0')+value[1:]
   raw=b''.join(lane.canonical_event(x) for x in events);(d/'formal_transcript.jsonl').write_bytes(raw);rows=verify._rows(d/'formal_frame_outcomes.csv');group=[x for x in events if x['frame_key']==events[0]['frame_key']];blob=b''.join(lane.canonical_event(x) for x in group);rows[0]['transcript_bytes_len']=len(blob);rows[0]['transcript_bytes_sha256']=lane._sha(blob);rows[0]['transcript_sha256']=lane._sha(blob);(d/'formal_frame_outcomes.csv').write_bytes(lane.syn._csv(rows))
  def verification_public(d):
   events=[json.loads(x) for x in (d/'formal_transcript.jsonl').read_bytes().splitlines()];event=next(x for x in events if x['event_type']=='VERIFICATION_TAG');event['payload']['tag']='1'*64
   raw=b''.join(lane.canonical_event(x) for x in events);(d/'formal_transcript.jsonl').write_bytes(raw);rows=verify._rows(d/'formal_frame_outcomes.csv');group=[x for x in events if x['frame_key']==events[0]['frame_key']];blob=b''.join(lane.canonical_event(x) for x in group);rows[0]['transcript_bytes_len']=len(blob);rows[0]['transcript_bytes_sha256']=lane._sha(blob);rows[0]['transcript_sha256']=lane._sha(blob);(d/'formal_frame_outcomes.csv').write_bytes(lane.syn._csv(rows))
  for name,fn in (('method_codebook',codebook),('method_selection',selection),('method_channel',channel),('public_syndrome_payload',public),('public_verification_payload',verification_public)):self._reject_case(out,name,fn)
 def test_source_lock_relocation_external_rebuild(self):
  out=self._executed()
  def mutate(d):l=json.loads((d/'real_data_lock.json').read_text());l['source_relocation']=False;self._write_lock(d,l)
  self._reject_case(out,'source_lock_relocation_external_rebuild',mutate)
 def test_complete_run_timeout_retains_strict_failure_package(self):
  out=self.root/'timeout'
  with patch.object(lane,'_synthetic',self.fake_synthetic),patch.object(lane,'_prior_sets',self.fake_prior):lane._prepare_test_plan(out,self.root,self.lock,count=2)
  ps=self._patches()
  with ps[0],ps[1],ps[2],ps[3],patch.object(lane.time,'monotonic',side_effect=(0.0,1801.0)):lane._execute_test_plan(out,self._result)
  self.assertEqual({x.name for x in out.iterdir()},set(lane.ARTIFACTS));report=json.loads((out/'formal_qualification_report.json').read_text());self.assertEqual((report['run_status'],report['promoted']),('failed',False))
  ps=self._patches()
  with ps[0],ps[1],ps[2],ps[3]:self.assertEqual(verify.verify_output(out,_private_test_only=True)['run_status'],'failed')
 def test_prior_real_plan_binding_drift_and_prior_real_plan_appears_after_prepare(self):
  synthetic=self.root/'synthetic';synthetic.mkdir();prior=self.root/'prior';prior.mkdir();own=self.root/'own';own.mkdir()
  prior_doc={'schema':'binary_ldpc_v4_real_plan_v1','roots':{},'plan_sha256':''};prior_doc['plan_sha256']=lane._sha(lane._compact({k:v for k,v in prior_doc.items() if k!='plan_sha256'}));own_doc={'schema':'binary_ldpc_v4_transfer_plan_v1','roots':{},'plan_sha256':''};own_doc['plan_sha256']=lane._sha(lane._compact({k:v for k,v in own_doc.items() if k!='plan_sha256'}));(prior/'pre_run_plan.json').write_bytes(lane._compact(prior_doc));(own/'pre_run_plan.json').write_bytes(lane._compact(own_doc))
  with patch.object(lane,'PREDECESSOR',synthetic):
   self.assertEqual(lane._existing_real_plans(own_doc['plan_sha256']),[{'path':str(prior.resolve()/'pre_run_plan.json'),'sha256':lane._sha((prior/'pre_run_plan.json').read_bytes())}])
  noise=self.root/'noise';noise.mkdir();(noise/'pre_run_plan.json').write_bytes(lane._compact({'schema':'binary_ldpc_v4_synthetic_plan_v2','roots':{}}))
  with patch.object(lane,'PREDECESSOR',synthetic):self.assertEqual(len(lane._existing_real_plans()),2)
  (noise/'pre_run_plan.json').write_bytes(b'{')
  with patch.object(lane,'PREDECESSOR',synthetic):
   with self.assertRaises(ValueError):lane._existing_real_plans()
  out=self._executed();ps=self._patches()
  with self.subTest(case='prior_real_plan_binding_drift'),ps[0],ps[1],ps[2],ps[3],patch.object(lane,'_existing_real_plans',return_value=[{'path':'appeared','sha256':'0'*64}]):
   with self.assertRaises(ValueError):verify.verify_output(out,_private_test_only=True)
