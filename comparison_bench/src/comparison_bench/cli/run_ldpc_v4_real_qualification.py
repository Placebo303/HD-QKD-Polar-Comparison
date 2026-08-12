"""Conditional immutable real qualification for formal binary LDPC v4."""
from __future__ import annotations
import argparse, hashlib, importlib.metadata, json, secrets, time
from pathlib import Path
from typing import Any, Callable, Mapping
import numpy as np
from . import run_ldpc_v4_synthetic_qualification as syn
from . import verify_ldpc_v4_synthetic_qualification as synthetic_verify
from ..formal_ir import ldpc_v3_ttbin_data as bridge
from ..formal_ir import ldpc_v4_real_source as real_source
from ..formal_ir.ldpc_v4 import METHOD, run_ldpc_formal_v4
from ..formal_ir.shared import canonical_event, seed_record

RUN_ID="binary_ldpc_v4_real_qualification_v2"; STRATA=("d1024_bw120","d1024_bw180","d1024_bw200"); FRAME_COUNT=128; SEED_BITS=2623
ARTIFACTS=("pre_run_plan.json","real_data_lock.json","formal_frame_outcomes.csv","formal_transcript.jsonl","formal_codebook_manifest.json","formal_selection_manifest.json","formal_channel_model.json","formal_run_manifest.json","formal_qualification_report.json")
FORBIDDEN=syn.FORBIDDEN
def _compact(x:Any)->bytes:return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode("ascii")
def _sha(x:bytes)->str:return hashlib.sha256(x).hexdigest()
def _json_x(p:Path,x:Any)->None:p.open("xb").write(_compact(x))
def _write_x(p:Path,x:bytes)->None:p.open("xb").write(x)
def _root_id(h:str)->str:return _sha(bytes.fromhex(h))
def _source_hashes()->dict[str,str]:
 root=Path(__file__).resolve().parents[1]; ps={"runner.py":"cli/run_ldpc_v4_real_qualification.py","verifier.py":"cli/verify_ldpc_v4_real_qualification.py","source_builder.py":"cli/build_ldpc_v4_real_source_extension.py","method.py":"formal_ir/ldpc_v4.py","channel.py":"formal_ir/ldpc_v4_channel.py","codebook.py":"formal_ir/codebook_v4.py","synthetic_runner.py":"cli/run_ldpc_v4_synthetic_qualification.py","synthetic_verifier.py":"cli/verify_ldpc_v4_synthetic_qualification.py","bridge.py":"formal_ir/ldpc_v3_ttbin_data.py","real_source.py":"formal_ir/ldpc_v4_real_source.py","shared.py":"formal_ir/shared.py"};return {k:_sha((root/v).read_bytes()) for k,v in ps.items()}
def _derive(root:str,stratum:str,count:int=FRAME_COUNT)->np.random.Generator:
 d=_sha(_compact({"schema":"binary_ldpc_v4_real_toeplitz_v1","root_hex":root,"stratum":stratum,"kind":"toeplitz","frame_count":count,"seed_length":SEED_BITS}));return np.random.Generator(np.random.PCG64(int.from_bytes(bytes.fromhex(d[:32]),"big")))
def _seeds(root:str,stratum:str,count:int=FRAME_COUNT)->list[dict[str,Any]]:
 r=_derive(root,stratum,count);return [seed_record(r.integers(0,2,size=SEED_BITS,dtype=np.uint8)) for _ in range(count)]
def _synthetic(path:Path,private:bool)->dict[str,Any]:
 v=synthetic_verify.verify_output(path,_private_test_only=private)
 if v.get("run_status")!="completed" or v.get("promoted") is not True:raise ValueError("synthetic package not strictly verified promoted")
 names=("pre_run_plan.json","formal_run_manifest.json","formal_qualification_report.json","formal_selection_manifest.json","formal_channel_model.json","formal_codebook_manifest.json")
 return {"path":str(path.resolve()),"verification":v,"hashes":{n:_sha((path/n).read_bytes()) for n in names},"docs":{n:json.loads((path/n).read_bytes()) for n in names}}
def _reserved(s:Mapping[str,Any])->set[str]:
 lock=s["docs"]["pre_run_plan.json"]["development_prerequisite"]
 dplan=json.loads((Path(lock["path"])/"pre_run_plan.json").read_bytes()); old=dplan["locked_data"]
 return {x["frame_identity"] for x in old["selected_frames"] if x["role"]=="confirmation"}
def _real_rows(extension:Mapping[str,Any],reserved:set[str],count:int=FRAME_COUNT)->list[dict[str,Any]]:
 pool=real_source.candidate_pool(extension); cal={x["frame_identity"] for x in bridge._selected(extension["base_source_manifest"]) if x["role"]=="calibration"}; out=[]
 for dataset_id in STRATA:
  cand=[]
  for row in pool:
   if row["dataset_id"]!=dataset_id or row["frame_identity"] in reserved or row["frame_identity"] in cal:continue
   rank=_sha(f"binary_ldpc_v4_real_selection_v1|{dataset_id}|{row['frame_identity']}".encode("ascii"));cand.append((rank,row))
  if len(cand)<count:raise ValueError("insufficient unreserved complete real frames")
  for rank,row in sorted(cand,key=lambda x:x[0])[:count]:out.append({**row,"bin_width_ps":real_source._BINS[dataset_id],"selection_rank":rank})
 out.sort(key=lambda x:(STRATA.index(x["dataset_id"]),x["selection_rank"]));return out
def _prior_sets(synthetic:Mapping[str,Any])->tuple[set[int],set[str]]:
 oldroots=set();oldseed=set()
 for s in synthetic["docs"]["pre_run_plan.json"]["generator"]["roots"].values():
  for r in s.values():oldroots.add(int(r["root_hex"],16))
 for s in syn.STRATA: oldseed|={x["seed_id"] for x in syn._generate(synthetic["docs"]["pre_run_plan.json"],s)[2]}
 oldroots|={int(x) for x in synthetic["docs"]["pre_run_plan.json"]["v3_seed_binding"]["root_seeds"].values()}
 oldroots|={int(x["root_integer"]) for x in synthetic["docs"]["pre_run_plan.json"]["development_root_binding"]["roots"]}
 oldseed|=set(synthetic["docs"]["pre_run_plan.json"]["v3_seed_binding"]["toeplitz_seed_ids"])
 return oldroots,oldseed
def _validate_roots(roots:Mapping[str,Any],synthetic:Mapping[str,Any],count:int)->None:
 if not isinstance(roots,Mapping) or set(roots)!=set(STRATA):raise ValueError("real toeplitz strata")
 oldroots,oldseed=_prior_sets(synthetic); ownroots=set();ownseeds=set()
 for st in STRATA:
  rec=roots[st]
  if not isinstance(rec,Mapping) or set(rec)!={"root_hex","root_id","seeds"} or not isinstance(rec.get("root_hex"),str) or len(rec["root_hex"])!=32 or rec["root_hex"].lower()!=rec["root_hex"] or rec["root_id"]!=_root_id(rec["root_hex"]) or rec["seeds"]!=_seeds(rec["root_hex"],st,count):raise ValueError("seed reconstruction")
  value=int(rec["root_hex"],16); ids={x["seed_id"] for x in rec["seeds"]}
  if value in oldroots or value in ownroots or ids & oldseed or ids & ownseeds or len(ids)!=count:raise ValueError("root or seed collision")
  ownroots.add(value);ownseeds|=ids
def _roots(synthetic:Mapping[str,Any],count:int=FRAME_COUNT)->dict[str,Any]:
 oldroots,oldseed=_prior_sets(synthetic)
 out={}; ids=set()
 for st in STRATA:
  raw=secrets.token_bytes(16).hex(); seeds=_seeds(raw,st,count)
  if int(raw,16) in oldroots or int(raw,16) in {int(v["root_hex"],16) for v in out.values()} or any(x["seed_id"] in oldseed or x["seed_id"] in ids for x in seeds):raise ValueError("root or seed collision")
  ids|={x["seed_id"] for x in seeds};out[st]={"root_hex":raw,"root_id":_root_id(raw),"seeds":seeds}
 return out
def _plan(synthetic_dir:Path,extension_path:Path,private:bool=False,count:int=FRAME_COUNT)->tuple[dict[str,Any],dict[str,Any]]:
 s=_synthetic(synthetic_dir,private); dp=json.loads((Path(s["docs"]["pre_run_plan.json"]["development_prerequisite"]["path"])/"pre_run_plan.json").read_bytes()); source=dp["locked_data"]["source_manifest"]; extension,extension_file,_=real_source.selection_pool(extension_path)
 if extension["base_source_manifest"]!=source or extension["base_source_manifest_sha256"]!=source["manifest_sha256"]:raise ValueError("extension base source binding")
 reserved=_reserved(s); rows=_real_rows(extension,reserved,count)
 if len({x["frame_identity"] for x in rows})!=3*count:raise ValueError("real selection disjointness")
 roots=_roots(s,count); lock={"schema":"binary_ldpc_v4_real_data_lock_v2","source_manifest":source,"source_manifest_sha256":source["manifest_sha256"],"source_extension": {"file":extension_file,"manifest":extension},"calibration_frame_identities":sorted({x["frame_identity"] for x in bridge._selected(source) if x["role"]=="calibration"}),"v3_reserved_confirmation_identities":sorted(reserved),"selected_frames":rows,"synthetic_binding":{"path":s["path"],"artifact_hashes":s["hashes"]},"toeplitz":{"schema":"binary_ldpc_v4_real_toeplitz_v1","seed_bits":SEED_BITS,"roots":roots}}
 lock["lock_sha256"]=_sha(_compact(lock)); order=[f"{x['dataset_id']}:{x['selection_rank']}" for x in rows]
 p={"schema":"binary_ldpc_v4_real_plan_v2","run_id":RUN_ID,"method_id":METHOD,"frame_count_per_stratum":count,"strata":list(STRATA),"caps":{"complete_run_s":1800,"per_frame":{"wall_s":5.0,"decoder_calls":10,"events":32}},"gate":{"denominator":count,"verified_success_floor":count if private else syn.qualification_floor(FRAME_COUNT),"forbidden_statuses":sorted(FORBIDDEN)},"real_data_lock_sha256":lock["lock_sha256"],"execution_order":order,"source_sha256":_source_hashes(),"backend_requirement":"ldpc==2.4.1","failure_finalizer":"nine_file_real_failure_retention_v2","_test_only":private};p["plan_sha256"]=_sha(_compact(p));return p,lock
def prepare_plan(output_dir:Path,synthetic_dir:Path,source_extension_manifest:Path)->dict[str,Any]:
 if output_dir.exists():raise FileExistsError("fresh output directory required")
 p,l=_plan(synthetic_dir,source_extension_manifest);output_dir.mkdir(parents=True);_json_x(output_dir/ARTIFACTS[0],p);_json_x(output_dir/ARTIFACTS[1],l);return p
def _prepare_test_plan(output_dir:Path,synthetic_dir:Path,source_extension_manifest:Path,count:int=2)->dict[str,Any]:
 if output_dir.exists():raise FileExistsError("fresh output directory required")
 p,l=_plan(synthetic_dir,source_extension_manifest,True,count);output_dir.mkdir(parents=True);_json_x(output_dir/ARTIFACTS[0],p);_json_x(output_dir/ARTIFACTS[1],l);return p
def _validate(plan:Mapping[str,Any],lock:Mapping[str,Any],private:bool)->None:
 if plan.get("plan_sha256")!=_sha(_compact({k:v for k,v in plan.items() if k!="plan_sha256"})) or lock.get("lock_sha256")!=_sha(_compact({k:v for k,v in lock.items() if k!="lock_sha256"})):raise ValueError("self hash")
 count=2 if private else FRAME_COUNT
 pkeys={"schema","run_id","method_id","frame_count_per_stratum","strata","caps","gate","real_data_lock_sha256","execution_order","source_sha256","backend_requirement","failure_finalizer","_test_only","plan_sha256"}
 lkeys={"schema","source_manifest","source_manifest_sha256","source_extension","calibration_frame_identities","v3_reserved_confirmation_identities","selected_frames","synthetic_binding","toeplitz","lock_sha256"}
 if set(plan)!=pkeys or set(lock)!=lkeys or bool(plan.get("_test_only"))!=private or plan.get("schema")!="binary_ldpc_v4_real_plan_v2" or plan.get("run_id")!=RUN_ID or plan.get("method_id")!=METHOD or plan.get("frame_count_per_stratum")!=count or plan.get("strata")!=list(STRATA) or plan.get("caps")!={"complete_run_s":1800,"per_frame":{"wall_s":5.0,"decoder_calls":10,"events":32}} or plan.get("gate")!={"denominator":count,"verified_success_floor":count if private else syn.qualification_floor(FRAME_COUNT),"forbidden_statuses":sorted(FORBIDDEN)} or plan.get("backend_requirement")!="ldpc==2.4.1" or plan.get("failure_finalizer")!="nine_file_real_failure_retention_v2" or plan.get("real_data_lock_sha256")!=lock.get("lock_sha256") or lock.get("schema")!="binary_ldpc_v4_real_data_lock_v2":raise ValueError("plan identity")
 s=_synthetic(Path(lock["synthetic_binding"]["path"]),private)
 if lock["synthetic_binding"]["artifact_hashes"]!=s["hashes"]:raise ValueError("synthetic binding")
 dp=json.loads((Path(s["docs"]["pre_run_plan.json"]["development_prerequisite"]["path"])/"pre_run_plan.json").read_bytes()); source=dp["locked_data"]["source_manifest"];reserved=_reserved(s);cal=sorted({x["frame_identity"] for x in bridge._selected(source) if x["role"]=="calibration"}); extension_file=lock["source_extension"].get("file",{}); extension,actual_file,_=real_source.selection_pool(Path(str(extension_file.get("path",""))));
 if extension_file!=actual_file or lock["source_extension"].get("manifest")!=extension or extension["base_source_manifest"]!=source or extension["base_source_manifest_sha256"]!=source["manifest_sha256"]:raise ValueError("extension binding")
 rows=_real_rows(extension,reserved,count)
 if lock["source_manifest"]!=source or lock["source_manifest_sha256"]!=source["manifest_sha256"] or lock["calibration_frame_identities"]!=cal or lock["v3_reserved_confirmation_identities"]!=sorted(reserved) or lock["selected_frames"]!=rows or plan["execution_order"]!=[f"{x['dataset_id']}:{x['selection_rank']}" for x in rows]:raise ValueError("selection/order")
 if not private and (plan["source_sha256"]!=_source_hashes() or importlib.metadata.version("ldpc")!="2.4.1"):raise ValueError("source/backend drift")
 if lock["toeplitz"].get("schema")!="binary_ldpc_v4_real_toeplitz_v1" or lock["toeplitz"].get("seed_bits")!=SEED_BITS or set(lock["toeplitz"])!={"schema","seed_bits","roots"}:raise ValueError("toeplitz schema")
 _validate_roots(lock["toeplitz"]["roots"],s,count)
def _arrays(lock:Mapping[str,Any],row:Mapping[str,Any])->tuple[np.ndarray,np.ndarray]:
 return real_source.arrays_for_row(lock["source_extension"]["manifest"],row)
def _finalize(out:Path,plan:Mapping[str,Any],lock:Mapping[str,Any],rows:list[dict[str,Any]],events:list[Mapping[str,Any]],status:str,reason:str)->None:
 binding=json.loads((Path(lock["synthetic_binding"]["path"])/"pre_run_plan.json").read_bytes())["development_binding"]
 for n,k in ((ARTIFACTS[4],"codebook"),(ARTIFACTS[5],"selection"),(ARTIFACTS[6],"channel_model")):
  if not(out/n).exists():_json_x(out/n,binding[k])
 if not(out/ARTIFACTS[2]).exists():_write_x(out/ARTIFACTS[2],syn._csv(rows))
 if not(out/ARTIFACTS[3]).exists():_write_x(out/ARTIFACTS[3],b"".join(canonical_event(x) for x in events))
 index={n:{"sha256":_sha((out/n).read_bytes()),"bytes":(out/n).stat().st_size} for n in ARTIFACTS[:7]};run={"schema":"binary_ldpc_v4_real_run_manifest_v2","run_id":RUN_ID,"run_status":status,"stop_reason":reason,"plan_sha256":plan["plan_sha256"],"outcome_count":len(rows),"artifact_index":index,"decoder_reexecution":False};run["manifest_sha256"]=_sha(_compact(run));_json_x(out/ARTIFACTS[7],run)
 gates={s:syn._gate([r for r in rows if r["stratum"]==s],int(plan["frame_count_per_stratum"]),int(plan["gate"]["verified_success_floor"])) for s in STRATA};rep={"schema":"binary_ldpc_v4_real_report_v2","run_id":RUN_ID,"run_status":status,"stop_reason":reason,"plan_sha256":plan["plan_sha256"],"run_manifest_sha256":_sha((out/ARTIFACTS[7]).read_bytes()),"promotion_gates":gates,"promoted":status=="completed" and all(x["promoted"] for x in gates.values()),"decoder_reexecution":False};rep["report_sha256"]=_sha(_compact(rep));_json_x(out/ARTIFACTS[8],rep)
def _execute(out:Path,runner:Callable[...,dict[str,Any]],private:bool)->None:
 if not out.is_dir() or {x.name for x in out.iterdir()}!=set(ARTIFACTS[:2]):raise ValueError("execute requires lock and reviewed plan only")
 p=json.loads((out/ARTIFACTS[0]).read_bytes());l=json.loads((out/ARTIFACTS[1]).read_bytes());_validate(p,l,private);rows=[];events=[];started=time.monotonic()
 try:
  for idx,key in enumerate(p["execution_order"]):
   if time.monotonic()-started>p["caps"]["complete_run_s"]:raise RuntimeError("complete_run_s")
   row=l["selected_frames"][idx];a,b=_arrays(l,row);seed=l["toeplitz"]["roots"][row["dataset_id"]]["seeds"][idx%int(p["frame_count_per_stratum"])]
   got=runner(a,b,channel_model=json.loads((Path(l["synthetic_binding"]["path"])/"pre_run_plan.json").read_bytes())["development_binding"]["channel_model"],selection_binding=json.loads((Path(l["synthetic_binding"]["path"])/"pre_run_plan.json").read_bytes())["development_binding"]["selection"],locked_seed=seed,dataset_id=row["dataset_id"],frame_id=key,stratum="adjacent_nominal",_caps=p["caps"]["per_frame"]);o=dict(got["outcome"]);o.update(stratum=row["dataset_id"],plan_frame_id=key,alice_sha256=_sha(a.astype("<u2").tobytes()),bob_sha256=_sha(b.astype("<u2").tobytes()),transcript_bytes_len=len(b"".join(canonical_event(x) for x in got["events"])),transcript_bytes_sha256=_sha(b"".join(canonical_event(x) for x in got["events"])));rows.append(o);events.extend(got["events"])
  _finalize(out,p,l,rows,events,"completed","")
 except Exception as e:
  _finalize(out,p,l,rows,events,"failed",f"{type(e).__name__}:{e}")
  if not private: raise
def _execute_test_plan(out:Path,runner:Callable[...,dict[str,Any]])->None:_execute(out,runner,True)
def main()->int:
 a=argparse.ArgumentParser();a.add_argument("--output-dir",type=Path,required=True);a.add_argument("--synthetic-dir",type=Path,required=True);a.add_argument("--source-extension-manifest",type=Path);a.add_argument("--mode",choices=("prepare","execute"),required=True);x=a.parse_args()
 if x.mode=="prepare":
  if x.source_extension_manifest is None:a.error("--source-extension-manifest required for prepare")
  prepare_plan(x.output_dir,x.synthetic_dir,x.source_extension_manifest)
 else:_execute(x.output_dir,run_ldpc_formal_v4,False)
 return 0
if __name__=="__main__":raise SystemExit(main())
