"""Read-only lock builder for the pre-registered 10 dB transfer source."""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
import numpy as np

N=256; Q=1024; STRATA=("d1024_bw120","d1024_bw180","d1024_bw200")
ROOT=Path(r"D:\Data\Raw Data\QKD_Loss")
RAW=ROOT/r"TypeII_776.1nm_3s\Type2_5s_10dB_2026-01-30_224808\Type2_5s_10dB_2026-01-30_224808.ttbin"
RAW_SHA="83f85f54a2e0a8573afe2e252fdb9184006f14b2c074998ca8569785b12b1205"
CHUNK_SHA="714e7e7171f254b023b352ba024e75f27eca629c40f8fd5df4f73c93045f3877"
MATERIALIZER_SHA="c05f52f960cf292a4cc5c7a1c0591902a48a1e4fc0d270adc08f9b97b6867d16"
SIDECAR_SHA={"d1024_bw120":("6568dbfa553e19c8f185a3676f95fb247ce7f4e83d637b8a54551419750a19eb","12b616448679e55a22dab02ac2c656aeff9fdfa02401b1d81f039365c448c281","43c3b94bc7934c8545cdc379730e8f166c7e6177b22dbf31f4bd4af72fb1025d"),"d1024_bw180":("4534d286b1cbe1493ec75b5be8ac5d2c24caa21974511eae56e595c9bab062f4","eef858931ead1e1868a55f9ce8c1c58952addcd7f446ee646d0dec4a01c0af65","75b6695f5597af9dcad425d698026c7399d7a6af92a118ecd397d6c54ef191bb"),"d1024_bw200":("f0a9e75ca9626291f8c7222f069be28ac215a31781b79dcfdb8ba8ce99c6f5ab","b6146037b4aa91530c795308b6f32054ae40be434914f8fac9a02a6f14d5cc76","c6846c77c45ffe2a9b8bf3a7a17b313a881d4c95bc367d4cfad74027fff6df6d")}
PROVENANCE_SHA={"run_config.json":"e3e290cc6dfb9354524ca54f3ed2c492e7a5062f690506422f0bd21ae04bb475","results/ttbin_parsing/ttbin_source.txt":"32aa328ca0ea3f917eca54969d8570733db066609a1139c4f8158a99b456402e","results/ttbin_parsing/ttbin_config.json":"b2a0025e9f93090300d53d285123c5d43c17ffe16af5f6ec31d8e252e0f1c24b","results/ttbin_parsing/ttbin_metrics.json":"4c9ff5c523f26de1e0f795842b45e4eb55433443fff4cced3895d9ea4afa6bc7","results/inputs_snapshot.json":"d24a61c0fba4715513c22cd5edcbf7445d60c4e5eead6a9de0fc702ea63b6375","results/resolved_config.json":"3b320c67220eb8f8afda71d7e646b0d5664e437547460d6296023d1817f74dfe","results/run_config.source.txt":"3323d20f7137b105b175d876a95f5ce3282e30a62838edd0ea37993cfe8ae9e6"}
RECORDED_ROOT=Path(r"D:\Data\QKD_Loss")
def _c(x):return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode("ascii")
def _s(x):return hashlib.sha256(x).hexdigest()
def _file(p):
 p=Path(p).resolve(strict=True); b=p.read_bytes();return {"path":str(p),"bytes":len(b),"sha256":_s(b)}
def _self(x,k):return {**x,k:_s(_c(x))}
def _identity(acq,st,i,a,b):
 start=i*N; payload=_s(np.asarray(a[start:start+N],dtype="<u2").tobytes()+np.asarray(b[start:start+N],dtype="<u2").tobytes())
 return _s(_c({"acquisition_id":acq,"stratum":st,"frame_id":i,"payload_identity":payload})),payload
def validate_arrays(a,b,*,minimum_frames=128):
 """Pure array guard used by the frozen lock and disposable fixtures."""
 if a.ndim!=1 or b.ndim!=1 or a.shape!=b.shape or not np.issubdtype(a.dtype,np.integer) or not np.issubdtype(b.dtype,np.integer) or np.any(a<0) or np.any(a>=Q) or np.any(b<0) or np.any(b>=Q) or a.size//N<minimum_frames:raise ValueError("arrays/capacity")
def validate_metadata(meta,*,source_paths,raw,bw,array_size,relocation,expected_processing=None):
 used=meta.get("materialize_params",{}).get("used_params",{})
 snapshot=meta.get("symbolization_snapshot",{})
 if not isinstance(source_paths,(str,list,tuple)) or not source_paths:raise ValueError("metadata source")
 src=list(source_paths) if isinstance(source_paths,(list,tuple)) else [source_paths]
 try:mapped={_map_old(x,relocation) for x in src}
 except Exception as exc:raise ValueError("metadata source") from exc
 loss=meta.get("loss",meta.get("acquisition_loss"));loss=loss if loss is not None else (10 if "10db" in str(next(iter(src))).lower() else None)
 declared=(used.get("n_pairs_actual"),meta.get("n_symbols"),meta.get("n_pairs_actual"))
 processing={k:snapshot.get(k) for k in ("dimension","bin_width_ps","block_symbols","mapping","bit_order","wrap_rule")}
 try:snapshot_raw=_map_old(snapshot.get("ttbin_file"),relocation)
 except Exception as exc:raise ValueError("metadata provenance") from exc
 if meta.get("joint_source_mode")!="from_ttbin" or meta.get("joint_origin")!="from_ttbin" or meta.get("materialize_origin")!="materialized_from_ttbin" or meta.get("sequence_source_mode")!="strict" or meta.get("sequence_is_sampled") not in (0,False) or used.get("pairing_mode")!="nearest" or used.get("dimension")!=Q or used.get("bin_width_ps")!=bw or used.get("mapping")!="gray" or mapped!={str(Path(raw).resolve())} or loss!=10 or any(x is not None and x!=array_size for x in declared) or any(meta.get(k,False) for k in ("padding","padded","tail_padding")) or snapshot_raw!=str(Path(raw).resolve()):raise ValueError("metadata provenance")
 if expected_processing is not None and processing!=expected_processing:raise ValueError("processing semantics")
 return processing
def validate_expected_hashes(records,expected):
 if {k:v.get("sha256") for k,v in records.items()}!=expected:raise ValueError("expected hash")
def validate_file_hash(record,expected):
 if record.get("sha256")!=expected:raise ValueError("file hash")
def validate_unique_payloads(rows):
 if len({x["payload_identity"] for x in rows})!=len(rows):raise ValueError("duplicate payload")
def validate_relocation_suffix(actual_root,raw_parent):
 suffix=Path(r"TypeII_776.1nm_3s\Type2_5s_10dB_2026-01-30_224808")
 if Path(actual_root)/suffix != Path(raw_parent):raise ValueError("relocation suffix")
 return suffix
def validate_snapshot_paths(rel,values,expected):
 for old,want in zip(values,expected):
  try:mapped=Path(_map_old(old,rel)).resolve(strict=True);target=Path(want).resolve(strict=True)
  except Exception as exc:raise ValueError("snapshot relocation") from exc
  if mapped!=target:raise ValueError("snapshot relocation")
def relocation_record(*,actual_root:Path=ROOT,recorded_root:Path=RECORDED_ROOT,provenance_root:Path|None=None):
 actual_root=Path(actual_root).resolve(strict=True); recorded_root=Path(recorded_root)
 if recorded_root.exists():raise ValueError("recorded root unexpectedly resolves")
 provenance_root=provenance_root or RAW.parent
 provenance_root=Path(provenance_root)
 names=("run_config.json","results/ttbin_parsing/ttbin_source.txt","results/ttbin_parsing/ttbin_config.json","results/ttbin_parsing/ttbin_metrics.json","results/inputs_snapshot.json","results/resolved_config.json","results/run_config.source.txt")
 files={n:_file(provenance_root/n) for n in names}
 validate_expected_hashes(files,PROVENANCE_SHA)
 suffix=validate_relocation_suffix(actual_root,RAW.parent.resolve())
 return _self({"schema":"binary_ldpc_v4_source_relocation_v1","recorded_root":str(recorded_root),"actual_root":str(actual_root),"relative_suffix":str(suffix),"recorded_root_resolves":False,"provenance_files":files},"relocation_sha256")
def _map_old(value,rel):
 raw=str(value).replace("/","\\");old=Path(rel["recorded_root"]);new=Path(rel["actual_root"]);prefix=str(old).lower()+"\\"
 if not raw.lower().startswith(prefix):raise ValueError("recorded source path")
 mapped=new/Path(raw[len(str(old))+1:])
 return str(mapped)
def _old_paths(value,root):
 out=[]
 if isinstance(value,dict):
  for x in value.values():out.extend(_old_paths(x,root))
 elif isinstance(value,list):
  for x in value:out.extend(_old_paths(x,root))
 elif isinstance(value,str) and value.replace("/","\\").lower().startswith(str(root).lower()+"\\"):out.append(value)
 return out
def _verify_snapshots(rel):
 actual=Path(rel["actual_root"]); capture=RAW.parent.resolve(); files=rel["provenance_files"]
 def read_json(name):return json.loads(Path(files[name]["path"]).read_text(encoding="utf-8"))
 checks=[
  Path(files["results/ttbin_parsing/ttbin_source.txt"]["path"]).read_text().strip(),
  read_json("run_config.json")["experiment"]["raw_data_dir"],read_json("run_config.json")["output"]["output_directory"],
  read_json("results/resolved_config.json")["experiment"]["raw_data_dir"],read_json("results/resolved_config.json")["output"]["output_directory"],
  read_json("results/inputs_snapshot.json")["extracted_params"]["ttbin_metrics_source"],
  Path(files["results/run_config.source.txt"]["path"]).read_text().strip()]
 expected=(RAW.with_name(RAW.stem+".1.ttbin"),capture,capture/"results",capture,capture/"results",capture/"results/ttbin_parsing/ttbin_metrics.json",capture/"run_config.json")
 validate_snapshot_paths(rel,checks,expected)
 metrics=read_json("results/ttbin_parsing/ttbin_metrics.json")
 for old in _old_paths(metrics,Path(rel["recorded_root"])):
  if not Path(_map_old(old,rel)).exists():raise ValueError("metrics relocation")
def build_source_lock(*,raw:Path=RAW,sidecar_root:Path|None=None,materializer:Path|None=None):
 raw=Path(raw); chunk=raw.with_name(raw.stem+".1.ttbin"); sidecar_root=sidecar_root or raw.parent/"e2e_new_ttbin_fullgrid"/"sidecars"
 materializer=materializer or Path(__file__).resolve().parents[4]/"src/workflow/export_joint_sequence_sidecar.py"
 main,part=_file(raw),_file(chunk)
 validate_file_hash(main,RAW_SHA);validate_file_hash(part,CHUNK_SHA)
 validate_file_hash(_file(materializer),MATERIALIZER_SHA)
 acq=_s(_c({"main":main["sha256"],"chunk":part["sha256"]})); rows=[]; datasets=[]
 for st in STRATA:
  bw=int(st.rsplit("bw",1)[1]); d=Path(sidecar_root)/st/"blk0"; files={n:_file(d/n) for n in ("a_eff.npy","b_eff.npy","sidecar_meta.json")}
  a=np.load(d/"a_eff.npy",allow_pickle=False);b=np.load(d/"b_eff.npy",allow_pickle=False);meta=json.loads((d/"sidecar_meta.json").read_text())
  used=meta.get("materialize_params",{}).get("used_params",{});src=used.get("source_ttbin_paths",meta.get("source_ttbin_paths"));src=src if isinstance(src,list) else [src]
  validate_arrays(a,b)
  rel=relocation_record(); mapped={_map_old(x,rel) for x in src}
  processing=validate_metadata(meta,source_paths=src,raw=raw,bw=bw,array_size=a.size,relocation=rel,expected_processing={"dimension":Q,"bin_width_ps":bw,"block_symbols":N,"mapping":"gray","bit_order":"lsb0","wrap_rule":"floor_div"})
  validate_expected_hashes(files,dict(zip(("a_eff.npy","b_eff.npy","sidecar_meta.json"),SIDECAR_SHA[st])))
  rec={"stratum":st,"bin_width_ps":bw,"sidecar_dir":str(d.resolve()),"files":files,"dtype":{"a":a.dtype.str,"b":b.dtype.str},"array_length":int(a.size),"complete_frames":int(a.size//N),"tail_symbols":int(a.size%N),"acquisition_loss":10,"processing":{**processing,"pairing_mode":"nearest"}};rec["source_record_sha256"]=_s(_c(rec));datasets.append(rec)
  for i in range(a.size//N):
   fid,pid=_identity(acq,st,i,a,b);rows.append({"stratum":st,"frame_id":i,"frame_identity":fid,"payload_identity":pid,"source_record_sha256":rec["source_record_sha256"],"source_pair_start":i*N,"source_pair_end":(i+1)*N})
 validate_unique_payloads(rows)
 selected=[]
 for st in STRATA:
  ranked=sorted(( _s(f"binary_ldpc_v4_10db_transfer_selection_v1|{st}|{r['frame_identity']}".encode()),r) for r in rows if r["stratum"]==st)
  selected += [{**r,"selection_rank":rank} for rank,r in ranked[:128]]
 rel=relocation_record();_verify_snapshots(rel)
 lock={"schema":"binary_ldpc_v4_10db_source_lock_v1","source_relocation":True,"relocation":rel,"raw_main":main,"raw_chunk":part,"materializer_source":_file(materializer),"datasets":datasets,"selected_frames":selected}
 return _self(lock,"lock_sha256")
def arrays_for_frame(lock,frame):
 """Read one frozen contiguous frame; callers must rebuild the lock first."""
 if frame.get("stratum") not in STRATA or not isinstance(frame.get("frame_id"),int):raise ValueError("frame identity")
 dataset=next((x for x in lock["datasets"] if x["stratum"]==frame["stratum"]),None)
 if dataset is None or frame["frame_id"]>=dataset["complete_frames"]:raise ValueError("frame range")
 d=Path(dataset["sidecar_dir"]);start=frame["frame_id"]*N
 a=np.load(d/"a_eff.npy",allow_pickle=False);b=np.load(d/"b_eff.npy",allow_pickle=False)
 return a[start:start+N],b[start:start+N]
