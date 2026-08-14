"""Immutable 10 dB transfer qualification; production entry points have no test switches."""
from __future__ import annotations
import argparse, copy, csv, functools, hashlib, json, math, secrets, time
from contextlib import contextmanager
from pathlib import Path
import numpy as np
from . import run_ldpc_v4_synthetic_qualification as syn
from . import verify_ldpc_v4_synthetic_qualification as synthetic_verify
from . import verify_ldpc_v4_16db_transfer_qualification as predecessor_verify
from ..formal_ir import ldpc_v4_10db_source as source
from ..formal_ir.ldpc_v4 import METHOD, run_ldpc_formal_v4
from ..formal_ir.shared import canonical_event, seed_record

RUN_ID="binary_ldpc_v4_10db_transfer_qualification_v1"; STRATA=source.STRATA; FRAME_COUNT=128; SEED_BITS=2623
PREREQUISITE=Path(__file__).resolve().parents[4]/"comparison_bench/outputs_comparison/formal_ir_methods/20260728_v2_binary_ldpc_v4_synthetic"
PREDECESSOR=Path(__file__).resolve().parents[4]/"comparison_bench/outputs_comparison/formal_ir_methods/20260729_v1_binary_ldpc_v4_16db_transfer"
ARTIFACTS=("pre_run_plan.json","real_data_lock.json","formal_frame_outcomes.csv","formal_transcript.jsonl","formal_codebook_manifest.json","formal_selection_manifest.json","formal_channel_model.json","formal_run_manifest.json","formal_qualification_report.json")
PREREQ_HASHES={"formal_channel_model.json":"83a80a2db8d7b7cacc63e5e7531ecc7d4bd4e93605af53aa2fa987257d15cf6c","formal_codebook_manifest.json":"786b48287f0b453a668c1ae1bdab2126aa7d13aeb94439860b80899a34687500","formal_frame_outcomes.csv":"3dd169aa692aba94232abf5018bbaee819645ac210a79c466b1702e0500d6c93","formal_qualification_report.json":"57268f73d4fa7dcbce01c2e63066af6d177502b415aa076312dd3a9c7a3f804a","formal_run_manifest.json":"3a142ff8d6d37c665ac8e0a1a8541fe9b36133ea10e75e3b55cbdc044eb49fa6","formal_selection_manifest.json":"5d3757f7e36e117877e9c2d75fa1e90496d83cc080171cfaa4f3299c44b6b4dd","formal_transcript.jsonl":"c2518fd89ad9a9ca3f884e74419e5801b42c956d3f027d90d9044167b7782b0f","pre_run_plan.json":"6a8c8c11afe7e13061c876a8955592f78911fc12883558fa9ccb3546391874cc"}
PREDECESSOR_HASHES={"formal_channel_model.json":"83a80a2db8d7b7cacc63e5e7531ecc7d4bd4e93605af53aa2fa987257d15cf6c","formal_codebook_manifest.json":"786b48287f0b453a668c1ae1bdab2126aa7d13aeb94439860b80899a34687500","formal_frame_outcomes.csv":"08a99fddb910afce675c05d9a7388165f772c98db2c60e396853600e341dcb73","formal_qualification_report.json":"c9986ca024c23d3111793890688e352062107686db1a634653a6e4e430359e97","formal_run_manifest.json":"64a92178f17e5e669370585a3a72c88ccae986835ed06a53b68de0488bda7550","formal_selection_manifest.json":"5d3757f7e36e117877e9c2d75fa1e90496d83cc080171cfaa4f3299c44b6b4dd","formal_transcript.jsonl":"b3dd574ae9f9bade050a71bdf3c4fa22b70498aa6e4b421ecb98dbb749607f75","pre_run_plan.json":"ce7a582c34b5a99846e5da6631b836bbc8d950d08f760721aa9a7a2435512eee","real_data_lock.json":"9852dad0d57a226913a2391650ab1829b3d155f8cc42908d6196543799ae1bc2"}
def _compact(x):return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()
def _sha(x):return hashlib.sha256(x).hexdigest()
def _self(x,k):return {**x,k:_sha(_compact(x))}
def _jsonx(p,x):p.open("xb").write(_compact(x))
def _root_id(x):return _sha(bytes.fromhex(x))
def _linear_development_rows(p):
 raw=Path(p).read_bytes()
 if not raw.endswith(b"\n") or b"\r" in raw:raise ValueError("csv canonical bytes")
 lines=raw.decode("utf-8").splitlines();raw_lines=raw.splitlines();out=[];development_verify=synthetic_verify.development_verify;fields=development_verify.lane.FIELDS
 for index,r in enumerate(csv.DictReader(lines)):
  if list(r)!=list(fields) or any(v is None for v in r.values()):raise ValueError("csv schema")
  try:
   x={"role":r["role"],"stratum_id":r["stratum_id"],"plane_id":int(r["plane_id"]),"candidate_id":int(r["candidate_id"]),"channel_model_sha256":r["channel_model_sha256"],"policy_sha256":r["policy_sha256"],"matrix_sha256":r["matrix_sha256"],"candidate_valid":r["candidate_valid"]=="true","backend_identity":r["backend_identity"],"frame_id":r["frame_id"],"attempted":r["attempted"]=="true","status":r["status"],"exact_match":r["exact_match"]=="true","syndrome_bits_disclosed":int(r["syndrome_bits_disclosed"]),"runtime_s":float(r["runtime_s"]),"source_sha256":r["source_sha256"]}
   if r["candidate_valid"] not in ("true","false") or r["attempted"] not in ("true","false") or r["exact_match"] not in ("true","false"):raise ValueError
  except Exception as e:raise ValueError("csv encoding") from e
  if not math.isfinite(x["runtime_s"]) or x["runtime_s"]<0:raise ValueError("runtime")
  if development_verify.lane._csv([x]).split(b"\n",1)[1].split(b"\n",1)[0]!=raw_lines[index+1]:raise ValueError("csv noncanonical row")
  out.append(x)
 return out
@contextmanager
def _replay_matrix_cache():
 original=synthetic_verify.matrix_for;development_verify=synthetic_verify.development_verify;original_rows=development_verify._rows;original_entry=development_verify.candidate_entry;cache={};entries={}
 def cached(plane_id,candidate_id):
  key=(plane_id,candidate_id)
  if key not in cache:
   if len(cache)>=40:raise ValueError("replay matrix cache bound")
   cache[key]=np.asarray(original(plane_id,candidate_id),dtype=np.uint8).copy()
  return cache[key].copy()
 synthetic_verify.matrix_for=cached
 def entry(plane_id,candidate_id):
  key=(plane_id,candidate_id)
  if key not in entries:
   if len(entries)>=40:raise ValueError("replay candidate cache bound")
   entries[key]=copy.deepcopy(original_entry(plane_id,candidate_id))
  return copy.deepcopy(entries[key])
 development_verify._rows=_linear_development_rows;development_verify.candidate_entry=entry
 try:yield {"matrices":cache,"candidates":entries}
 finally:
  synthetic_verify.matrix_for=original;development_verify._rows=original_rows;development_verify.candidate_entry=original_entry
def _source_hashes():
 root=Path(__file__).resolve().parents[1]; paths={"runner":"cli/run_ldpc_v4_10db_transfer_qualification.py","verifier":"cli/verify_ldpc_v4_10db_transfer_qualification.py","source":"formal_ir/ldpc_v4_10db_source.py","method":"formal_ir/ldpc_v4.py","codebook":"formal_ir/codebook_v4.py","channel":"formal_ir/ldpc_v4_channel.py","shared":"formal_ir/shared.py","synthetic_runner":"cli/run_ldpc_v4_synthetic_qualification.py","synthetic_verifier":"cli/verify_ldpc_v4_synthetic_qualification.py"};return {k:_sha((root/v).read_bytes()) for k,v in paths.items()}
def _existing_real_plans(excluding_plan_sha256=None):
 out=[]
 for p in PREDECESSOR.parent.glob("*/pre_run_plan.json"):
  try:
   doc=json.loads(p.read_bytes())
  except Exception as exc:raise ValueError("prior real plan parse") from exc
  schema=doc.get("schema","")
  if not isinstance(schema,str) or not isinstance(doc.get("roots"),dict):continue
  if not schema.startswith("binary_ldpc_v4_") or ("transfer_plan" not in schema and "real_plan" not in schema):continue
  if doc.get("plan_sha256")==excluding_plan_sha256:continue
  if doc.get("plan_sha256")!=_sha(_compact({k:v for k,v in doc.items() if k!="plan_sha256"})):raise ValueError("prior real plan self hash")
  out.append({"path":str(p.resolve()),"sha256":_sha(p.read_bytes())})
 return sorted(out,key=lambda x:x["path"])
def _synthetic(path=PREREQUISITE,private=False):
 path=Path(path)
 if not private and path.resolve()!=PREREQUISITE.resolve():raise ValueError("exact synthetic prerequisite")
 if not private and {n:_sha((path/n).read_bytes()) for n in PREREQ_HASHES}!=PREREQ_HASHES:raise ValueError("prerequisite hash")
 with _replay_matrix_cache():got=synthetic_verify.verify_output(path,_private_test_only=private)
 if got.get("run_status")!="completed" or got.get("promoted") is not True:raise ValueError("synthetic prerequisite")
 docs={n:json.loads((path/n).read_bytes()) for n in ("pre_run_plan.json","formal_codebook_manifest.json","formal_selection_manifest.json","formal_channel_model.json")}
 return {"path":str(path.resolve()),"hashes":{n:_sha((path/n).read_bytes()) for n in PREREQ_HASHES},"docs":docs}
@functools.lru_cache(maxsize=2)
def _replay_predecessor(path_text, artifact_hashes):
 return predecessor_verify.verify_output(Path(path_text))
def _predecessor(path=PREDECESSOR,private=False):
 path=Path(path)
 if path.resolve()!=PREDECESSOR.resolve():raise ValueError("exact 16db predecessor")
 hashes={n:_sha((path/n).read_bytes()) for n in PREDECESSOR_HASHES}
 if hashes!=PREDECESSOR_HASHES:raise ValueError("predecessor hash")
 got=_replay_predecessor(str(path.resolve()),tuple(sorted(hashes.items())))
 if got.get("run_status")!="completed" or got.get("promoted") is not False or got.get("outcomes")!=384:raise ValueError("predecessor state")
 report=json.loads((path/"formal_qualification_report.json").read_bytes())
 counts=[report["promotion_gates"][s]["verified_success"] for s in STRATA]
 if counts != [125,128,128] or any(report["promotion_gates"][s]["forbidden_failure_count"] for s in STRATA):raise ValueError("predecessor counts")
 return {"path":str(path.resolve()),"artifact_hashes":hashes}
def _derive(root,st,count):return np.random.Generator(np.random.PCG64(int(_sha(_compact({"root":root,"stratum":st,"count":count}))[:32],16)))
def _seeds(root,st,count):
 r=_derive(root,st,count);return [seed_record(r.integers(0,2,size=SEED_BITS,dtype=np.uint8)) for _ in range(count)]
def _plan_root_sets(doc):
 roots={int(v["root_hex"],16) for v in doc.get("roots",{}).values() if isinstance(v,dict) and "root_hex" in v}
 seeds={x["seed_id"] for v in doc.get("roots",{}).values() if isinstance(v,dict) for x in v.get("seeds",[]) if isinstance(x,dict) and "seed_id" in x}
 return roots,seeds
def _prior_sets(s,pred=None):
 p=s["docs"]["pre_run_plan.json"];roots={int(v["root_hex"],16) for d in p["generator"]["roots"].values() for v in d.values()};seeds={x["seed_id"] for st in syn.STRATA for x in syn._generate(p,st)[2]}
 roots|={int(x) for x in p.get("v3_seed_binding",{}).get("root_seeds",{}).values()};seeds|=set(p.get("v3_seed_binding",{}).get("toeplitz_seed_ids",[]));roots|={int(x["root_integer"]) for x in p.get("development_root_binding",{}).get("roots",[]) if "root_integer" in x}
 if pred is not None:
  pr,ps=_plan_root_sets(json.loads((Path(pred["path"])/"pre_run_plan.json").read_bytes()));roots|=pr;seeds|=ps
 for binding in _existing_real_plans():
  try:pr,ps=_plan_root_sets(json.loads(Path(binding["path"]).read_bytes()));roots|=pr;seeds|=ps
  except Exception:raise ValueError("prior real plan")
 return roots,seeds
def _roots(s,count,pred=None):
 old,oldids=_prior_sets(s,pred);out={};ids=set()
 for st in STRATA:
  raw=secrets.token_bytes(16).hex();ss=_seeds(raw,st,count)
  if int(raw,16) in old or {x["seed_id"] for x in ss}&(oldids|ids):raise ValueError("seed collision")
  out[st]={"root_hex":raw,"root_id":_root_id(raw),"seeds":ss};ids|={x["seed_id"] for x in ss}
 return out
def _validate_roots(roots,s,count,pred=None):
 old,oldids=_prior_sets(s,pred);seen=set();ids=set()
 if set(roots)!=set(STRATA):raise ValueError("root strata")
 for st,r in roots.items():
  if set(r)!={"root_hex","root_id","seeds"} or r["root_id"]!=_root_id(r["root_hex"]) or r["seeds"]!=_seeds(r["root_hex"],st,count):raise ValueError("root reconstruction")
  if int(r["root_hex"],16) in old|seen or {x["seed_id"] for x in r["seeds"]}&(oldids|ids):raise ValueError("root collision")
  seen.add(int(r["root_hex"],16));ids|={x["seed_id"] for x in r["seeds"]}
def _plan(synthetic_dir=PREREQUISITE,private=False,count=FRAME_COUNT,source_lock=None):
 s=_synthetic(synthetic_dir,private);pred=_predecessor(private=private);lock=source_lock or source.build_source_lock();rows=lock["selected_frames"]
 if len(rows)!=3*count or any(sum(x["stratum"]==st for x in rows)!=count for st in STRATA):raise ValueError("source capacity")
 roots=_roots(s,count,pred); order=[f"{x['stratum']}:{x['selection_rank']}" for x in rows]
 data={"schema":"binary_ldpc_v4_10db_transfer_plan_v1","run_id":RUN_ID,"method_id":METHOD,"frame_count_per_stratum":count,"strata":list(STRATA),"gate":{"denominator":count,"verified_success_floor":count if private else 126,"forbidden_statuses":sorted(syn.FORBIDDEN)},"caps":{"complete_run_s":1800,"per_frame":{"wall_s":5.0,"decoder_calls":10,"events":32}},"backend_requirement":"ldpc==2.4.1","failure_finalizer":"nine_file_transfer_failure_retention_v1","prior_real_plan_bindings":_existing_real_plans(),"execution_order":order,"source_lock_sha256":lock["lock_sha256"],"synthetic":{"path":s["path"],"artifact_hashes":s["hashes"]},"predecessor_16db":pred,"roots":roots,"source_sha256":_source_hashes(),"_test_only":private};return _self(data,"plan_sha256"),lock,s
def _validate(p,l,private):
 count=2 if private else FRAME_COUNT
 if p.get("plan_sha256")!=_sha(_compact({k:v for k,v in p.items() if k!="plan_sha256"})) or l.get("lock_sha256")!=_sha(_compact({k:v for k,v in l.items() if k!="lock_sha256"})):raise ValueError("self hash")
 keys={"schema","run_id","method_id","frame_count_per_stratum","strata","gate","caps","backend_requirement","failure_finalizer","prior_real_plan_bindings","execution_order","source_lock_sha256","synthetic","predecessor_16db","roots","source_sha256","_test_only","plan_sha256"}
 gate={"denominator":count,"verified_success_floor":count if private else 126,"forbidden_statuses":sorted(syn.FORBIDDEN)};caps={"complete_run_s":1800,"per_frame":{"wall_s":5.0,"decoder_calls":10,"events":32}}
 if set(p)!=keys or p.get("schema")!="binary_ldpc_v4_10db_transfer_plan_v1" or p.get("run_id")!=RUN_ID or p.get("method_id")!=METHOD or p.get("frame_count_per_stratum")!=count or p.get("strata")!=list(STRATA) or p.get("gate")!=gate or p.get("caps")!=caps or p.get("backend_requirement")!="ldpc==2.4.1" or p.get("failure_finalizer")!="nine_file_transfer_failure_retention_v1" or p.get("prior_real_plan_bindings")!=_existing_real_plans(p["plan_sha256"]) or set(p.get("source_sha256",{}))!={"runner","verifier","source","method","codebook","channel","shared","synthetic_runner","synthetic_verifier"} or bool(p.get("_test_only"))!=private:raise ValueError("plan")
 s=_synthetic(p["synthetic"]["path"],private)
 pred=_predecessor(p["predecessor_16db"]["path"],private)
 if p["synthetic"]["artifact_hashes"]!=s["hashes"] or p["predecessor_16db"]!=pred or p["source_sha256"]!=_source_hashes():raise ValueError("binding drift")
 actual=source.build_source_lock()
 if p["source_lock_sha256"]!=actual["lock_sha256"] or l!=actual:raise ValueError("source lock")
 _validate_roots(p["roots"],s,count,pred)
 if p["execution_order"]!=[f"{x['stratum']}:{x['selection_rank']}" for x in l["selected_frames"]]:raise ValueError("order")
def prepare_plan(output_dir,synthetic_dir=PREREQUISITE):
 if Path(output_dir).exists():raise FileExistsError("fresh output")
 p,l,_=_plan(synthetic_dir);Path(output_dir).mkdir(parents=True);_jsonx(Path(output_dir)/ARTIFACTS[0],p);_jsonx(Path(output_dir)/ARTIFACTS[1],l);return p
def _prepare_test_plan(output_dir,synthetic_dir,source_lock,count=2):
 if Path(output_dir).exists():raise FileExistsError("fresh output")
 p,l,_=_plan(synthetic_dir,True,count,source_lock);Path(output_dir).mkdir(parents=True);_jsonx(Path(output_dir)/ARTIFACTS[0],p);_jsonx(Path(output_dir)/ARTIFACTS[1],l);return p
def _finalize(out,p,l,rows,events,status,reason):
 bind=json.loads(Path(p["synthetic"]["path"],"pre_run_plan.json").read_bytes())["development_binding"]
 for n,k in ((ARTIFACTS[4],"codebook"),(ARTIFACTS[5],"selection"),(ARTIFACTS[6],"channel_model")):_jsonx(out/n,bind[k])
 (out/ARTIFACTS[2]).open("xb").write(syn._csv(rows));(out/ARTIFACTS[3]).open("xb").write(b"".join(canonical_event(e) for e in events))
 idx={n:{"sha256":_sha((out/n).read_bytes()),"bytes":(out/n).stat().st_size} for n in ARTIFACTS[:7]};run=_self({"schema":"binary_ldpc_v4_10db_transfer_run_manifest_v1","run_id":RUN_ID,"run_status":status,"stop_reason":reason,"plan_sha256":p["plan_sha256"],"outcome_count":len(rows),"artifact_index":idx,"decoder_reexecution":False},"manifest_sha256");_jsonx(out/ARTIFACTS[7],run)
 gates={st:syn._gate([r for r in rows if r["stratum"]==st],p["frame_count_per_stratum"],p["gate"]["verified_success_floor"]) for st in STRATA};rep=_self({"schema":"binary_ldpc_v4_10db_transfer_report_v1","run_id":RUN_ID,"run_status":status,"stop_reason":reason,"plan_sha256":p["plan_sha256"],"run_manifest_sha256":_sha((out/ARTIFACTS[7]).read_bytes()),"promotion_gates":gates,"promoted":status=="completed" and all(x["promoted"] for x in gates.values()),"decoder_reexecution":False,"source_relocation":True},"report_sha256");_jsonx(out/ARTIFACTS[8],rep)
def _execute(out,runner,private):
 out=Path(out)
 if {x.name for x in out.iterdir()}!=set(ARTIFACTS[:2]):raise ValueError("execute contract")
 p=json.loads((out/ARTIFACTS[0]).read_bytes());l=json.loads((out/ARTIFACTS[1]).read_bytes());_validate(p,l,private);rows=[];events=[];deadline=time.monotonic()+p["caps"]["complete_run_s"]
 try:
  bind=json.loads(Path(p["synthetic"]["path"],"pre_run_plan.json").read_bytes())["development_binding"]
  for i,frame in enumerate(l["selected_frames"]):
   if time.monotonic()>=deadline:raise TimeoutError("complete_run_s")
   a,b=source.arrays_for_frame(l,frame);st=frame["stratum"];seed=p["roots"][st]["seeds"][sum(x["stratum"]==st for x in l["selected_frames"][:i])];result=runner(a,b,channel_model=bind["channel_model"],selection_binding=bind["selection"],locked_seed=seed,dataset_id=st,frame_id=p["execution_order"][i],stratum="adjacent_nominal",_caps=p["caps"]["per_frame"]);o=dict(result["outcome"]);ev=list(result["events"]);blob=b"".join(canonical_event(e) for e in ev);o.update(stratum=st,plan_frame_id=p["execution_order"][i],alice_sha256=_sha(np.asarray(a,dtype="<u2").tobytes()),bob_sha256=_sha(np.asarray(b,dtype="<u2").tobytes()),transcript_bytes_len=len(blob),transcript_bytes_sha256=_sha(blob));rows.append(o);events.extend(ev)
   if time.monotonic()>=deadline:raise TimeoutError("complete_run_s")
  _finalize(out,p,l,rows,events,"completed","")
 except Exception as e:
  _finalize(out,p,l,rows,events,"failed",f"{type(e).__name__}:{e}")
  if not private:raise
def execute_plan(output_dir):_execute(output_dir,run_ldpc_formal_v4,False)
def _execute_test_plan(output_dir,runner):_execute(output_dir,runner,True)
def main():
 a=argparse.ArgumentParser();a.add_argument("--output-dir",type=Path,required=True);a.add_argument("--mode",choices=("prepare","execute"),required=True);a.add_argument("--synthetic-dir",type=Path,default=PREREQUISITE);x=a.parse_args();prepare_plan(x.output_dir,x.synthetic_dir) if x.mode=="prepare" else execute_plan(x.output_dir);return 0
if __name__=="__main__":raise SystemExit(main())
