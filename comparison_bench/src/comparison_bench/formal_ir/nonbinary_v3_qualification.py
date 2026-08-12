"""Plan, bounded execution, and deterministic replay for NBLDPC v3."""
from __future__ import annotations
import csv, hashlib, json, math, platform, subprocess, time
from pathlib import Path
from typing import Any, Callable
import numpy as np
from .nonbinary_v3 import METHOD, CANDIDATE_IDS, build_nbldpc_v3_codebook, decode_nbldpc_v3
from .nonbinary_qspa import nonbinary_syndrome, nonbinary_disclosure_accounting, symbols_to_msb_bits, verify_nonbinary_symbols
from .nonbinary_field import GF2mField
from .shared import materialize_seed_record, locked_seed_bits, canonical_event, toeplitz_tag, transcript_summary

RUN_ID="20260728_v3_nbldpc_synthetic"; Q,N=1024,64; PS=(.20,.30); SEED_BITS=703
ROOTS={("development",.20):202607380000,("development",.30):202607390000,("confirmation",.20):202607400000,("confirmation",.30):202607410000}
CAPS={"decoder_call_s":30,"complete_run_s":10800,"workers":1,"q":Q,"n":N,"checks_max":48,"row_weight":8,"max_iter":12,"dense_bytes_max":24*1024*1024}
ARTIFACTS=("pre_run_plan.json","formal_frame_outcomes.csv","formal_transcript.jsonl","formal_run_manifest.json","formal_codebook_manifest.json","formal_candidate_manifest.json","formal_policy_manifest.json","formal_qualification_report.json")
OFFICIAL_OUTPUT_ROOT=Path("comparison_bench/outputs_comparison/formal_ir_methods")/RUN_ID
_SRC=("comparison_bench/src/comparison_bench/formal_ir/nonbinary_v3.py","comparison_bench/src/comparison_bench/formal_ir/nonbinary_v3_qualification.py","comparison_bench/src/comparison_bench/cli/run_formal_nonbinary_v3_qualification.py")
_CONTRACT="openspec/changes/formal-nonbinary-ldpc-v3-covered-layered/specs/formal-nonbinary-ldpc-v3/spec.md"
def _compact(x): return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
def _sha(x): return hashlib.sha256(x).hexdigest()
def _put(p,x):
    with p.open("xb") as f:f.write(json.dumps(x,sort_keys=True,indent=2,ensure_ascii=True,allow_nan=False).encode()+b"\n")
def _csv(p, rows):
    with p.open("x",newline="",encoding="utf8") as f:
        w=csv.DictWriter(f,fieldnames=sorted({k for r in rows for k in r}) or ["status"]);w.writeheader();w.writerows(rows)
def _rows(p):
    with p.open(newline="",encoding="utf8") as f:return list(csv.DictReader(f))
def _root():return Path(__file__).resolve().parents[4]
def _output(output,*,_test_only):
    official=(_root()/OFFICIAL_OUTPUT_ROOT).resolve(); chosen=official if output is None else Path(output).resolve()
    if chosen!=official and not _test_only:raise ValueError("v3 requires official output root")
    return chosen
def _git_commit():
    try:return subprocess.check_output(["git","-C",str(_root()),"rev-parse","HEAD"],text=True,stderr=subprocess.DEVNULL).strip()
    except (OSError,subprocess.SubprocessError): return "unavailable"
def _git_diagnostic():
    try:return _sha(subprocess.check_output(["git","-C",str(_root()),"status","--porcelain"],stderr=subprocess.DEVNULL))
    except (OSError,subprocess.SubprocessError): return "unavailable"
def _candidate_manifest():
    cb,_=build_nbldpc_v3_codebook();return {"method":METHOD,"candidate_ids":list(CANDIDATE_IDS),"codebook_manifest_id":cb["manifest_id"],"decoder_definitions":{x:{"schedule":"row_layered_fft_qspa","damping":.5 if x.endswith("l050") else .75} for x in CANDIDATE_IDS}}
def _provenance():
    root=_root(); source={f:_sha((root/f).read_bytes()) for f in _SRC}; candidate=_candidate_manifest()
    return {"gates":{"source_sha256":source,"cli_sha256":source[_SRC[-1]],"candidate_manifest_sha256":_sha(_compact(candidate)),"contract_sha256":_sha((root/_CONTRACT).read_bytes()),"environment":{"python":platform.python_version(),"numpy":np.__version__},"git_commit":_git_commit()},"diagnostic":{"worktree_status_sha256":_git_diagnostic()}}
def _frame(p,role,i):
    r=np.random.Generator(np.random.PCG64(ROOTS[role,p]+i)); a=r.integers(0,Q,N,dtype=np.int64); mask=r.random(N)<p; e=r.integers(1,Q,N,dtype=np.int64); b=a.copy();b[mask]^=e[mask]
    return {"frame_id":f"{METHOD}_q1024_p{int(p*100):02d}_{role}_{i:03d}","p":p,"role":role,"index":i,"seed":ROOTS[role,p]+i,"alice":a.tolist(),"bob":b.tolist(),"array_sha256":_sha(a.astype('<i8').tobytes()+b.astype('<i8').tobytes()),"atomic_keys":[f"{METHOD}|{role}|{p}|{i}|{j}" for j in range(N)]}
def _h2(p):return -p*math.log2(p)-(1-p)*math.log2(1-p)
def policy_grid():
    out=[]
    for candidate in CANDIDATE_IDS:
      for margin in (4,8):
        strata=[]
        for p in PS:
          need=math.ceil(N*(_h2(p)+p*math.log2(1023))/10)+margin; check=next((x for x in (24,32,40,48) if x>=need),None);strata.append({"p":p,"needed_checks":need,"check_count":check,"decoder_p":p})
        body={"candidate_id":candidate,"permitted_prefixes":[24,32,40,48],"rate_margin_symbols":margin,"max_iter":12,"strata":strata};out.append(dict(body,policy_sha256=_sha(_compact(body))))
    return out
def _prior_seed_ids(*, exclude=None):
    root=_root()/"comparison_bench/outputs_comparison/formal_ir_methods"; found=set()
    if not root.exists():return found
    for path in root.rglob("*.json"):
        if exclude:
            target=Path(exclude).resolve()
            if path.resolve()==target or (target.is_dir() and path.resolve().is_relative_to(target)):continue
        try:text=path.read_text(encoding="utf8")
        except OSError:continue
        import re; found.update(re.findall(r'"seed_id"\s*:\s*"([0-9a-f]{64})"',text))
    return found
def _prior_identities(*, exclude=None):
    """Only collect fields that older local preplans actually disclose."""
    base=_root()/"comparison_bench/outputs_comparison/formal_ir_methods"; out={"roots":set(),"frame_ids":set(),"arrays":set(),"atomic":set()}
    if not base.exists():return out
    for path in base.rglob("pre_run_plan.json"):
      if exclude:
        target=Path(exclude).resolve()
        if path.resolve()==target or (target.is_dir() and path.resolve().is_relative_to(target)):continue
      try:data=json.loads(path.read_text(encoding="utf8"))
      except (OSError,ValueError):continue
      roots=data.get("roots",data.get("generator",{}).get("roots",{}));out["roots"].update(str(x) for x in (roots.values() if isinstance(roots,dict) else []))
      for frame in data.get("frames",[]):
        if isinstance(frame,dict):out["frame_ids"].add(str(frame.get("frame_id","")));out["arrays"].add(str(frame.get("array_sha256","")));out["atomic"].update(map(str,frame.get("atomic_keys",[])))
    return out
def _identity_overlap(frames, *, exclude=None):
    old=_prior_identities(exclude=exclude); roots={str(x) for x in ROOTS.values()}; ids={str(x["frame_id"]) for x in frames}; arrays={str(x["array_sha256"]) for x in frames}; atomic={str(k) for x in frames for k in x["atomic_keys"]}
    return {"roots":sorted(roots&old["roots"]),"frame_ids":sorted(ids&old["frame_ids"]),"array_sha256":sorted(arrays&old["arrays"]),"atomic_keys":sorted(atomic&old["atomic"])}
def expected_plan():
    frames=[_frame(p,"development",i) for p in PS for i in range(24)]; policies=policy_grid(); records={}
    for policy in policies:
      for frame in frames:records[policy["policy_sha256"]+"|"+frame["frame_id"]]=materialize_seed_record(SEED_BITS)
    return {"canonical_schema":"NBLDPCQ3","run_id":RUN_ID,"method":METHOD,"q":Q,"n":N,"roots":{f"{role}|{p}":seed for (role,p),seed in ROOTS.items()},"caps":CAPS,"frames":frames,"identity_overlap":_identity_overlap(frames),"policies":policies,"development_toeplitz_seeds":records,"confirmation_contract":{"frames_per_stratum":32,"seed_bits":SEED_BITS,"materialize_only_after_readiness":True},"provenance":_provenance()}
def create_plan(output=None,*,_test_only=False):
    out=_output(output,_test_only=_test_only)
    if out.exists():raise FileExistsError(out)
    plan=expected_plan(); records=list(plan["development_toeplitz_seeds"].values()); ids={x["seed_id"] for x in records}
    if len(records)!=192 or len(ids)!=len(records):raise ValueError("development seed uniqueness")
    if ids&_prior_seed_ids(exclude=out):raise ValueError("prior seed overlap")
    out.mkdir(parents=True);_put(out/"pre_run_plan.json",plan);return plan
def _validate_plan(plan, *, plan_path=None):
    if plan.get("canonical_schema")!="NBLDPCQ3" or plan.get("run_id")!=RUN_ID or plan.get("method")!=METHOD:raise ValueError("plan identity")
    if plan.get("caps")!=CAPS or plan.get("roots")!={f"{r}|{p}":s for (r,p),s in ROOTS.items()}:raise ValueError("plan caps/roots")
    frames=plan.get("frames"); expected=[_frame(p,"development",i) for p in PS for i in range(24)]
    if not isinstance(frames,list) or any(not isinstance(x,dict) or x.get("role")!="development" for x in frames):raise ValueError("confirmation leaked into plan")
    if frames!=expected:raise ValueError("development frames")
    if plan.get("identity_overlap")!=_identity_overlap(frames,exclude=plan_path) or any(plan["identity_overlap"].values()):raise ValueError("prior identity overlap")
    if plan.get("policies")!=policy_grid() or plan.get("confirmation_contract")!={"frames_per_stratum":32,"seed_bits":SEED_BITS,"materialize_only_after_readiness":True}:raise ValueError("policy/confirmation contract")
    records=plan.get("development_toeplitz_seeds",{}); expected_keys={p["policy_sha256"]+"|"+f["frame_id"] for p in policy_grid() for f in frames}
    if set(records)!=expected_keys or len(records)!=192:raise ValueError("development seed bindings")
    ids=[]
    for record in records.values():locked_seed_bits(record,SEED_BITS);ids.append(record["seed_id"])
    if len(ids)!=len(set(ids)):raise ValueError("development seed uniqueness")
    if set(ids)&_prior_seed_ids(exclude=plan_path):raise ValueError("prior seed overlap")
    prov=plan.get("provenance",{}); expected_prov=_provenance()
    if prov.get("gates")!=expected_prov["gates"]:raise ValueError("scoped provenance gates")
    return True
def _setting(policy,p):return next(x for x in policy["strata"] if float(x["p"])==float(p))
def _select(rows,grid):
    candidates=[]
    for p in grid:
      rs=rows.get(p["policy_sha256"],[]); allowed={"verified_success","verify_failed","decode_failed","aborted_resource_limit"}; expected=[f"{METHOD}_q1024_p{int(s*100):02d}_development_{i:03d}" for s in PS for i in range(24)]
      if len(rs)!=48 or [x.get("frame_id") for x in rs]!=expected or any(x.get("status") not in allowed or not bool(x.get("denominator_included")) for x in rs) or any(_setting(p,s)["check_count"] is None for s in PS):continue
      counts=[sum(x["status"]=="verified_success" and float(x["stratum_p"])==s for x in rs) for s in PS]; candidates.append((-min(counts),-sum(counts),sum(int(x["key_dependent_disclosure_bits_total"]) for x in rs),sum(int(x.get("iterations",0)) for x in rs),p["policy_sha256"],p))
    if not candidates:return {"selected_policy":None,"selected_policy_sha256":None,"selection_key":None,"reason":"no_eligible_policy"}
    best=min(candidates);return {"selected_policy":best[-1],"selected_policy_sha256":best[-1]["policy_sha256"],"selection_key":list(best[:-1]),"reason":"development_rank"}
def production_runner(bob,syndrome,**kw):return decode_nbldpc_v3(bob_symbols=bob,syndrome=syndrome,**kw)
def _one(frame,policy,seed,runner,cb,mats,clock=time.monotonic):
    setting=_setting(policy,frame["p"]); checks=setting["check_count"]
    if checks is None:return {"frame_id":frame["frame_id"],"stratum_p":frame["p"],"qualification_role":frame["role"],"policy_sha256":policy["policy_sha256"],"status":"unsupported_domain","denominator_included":False,"iterations":0,"key_dependent_disclosure_bits_total":0,"check_count":None,"verification_seed_id":seed["seed_id"],"array_sha256":frame["array_sha256"]}
    syn=nonbinary_syndrome(mats[checks],frame["alice"],GF2mField.create(Q)); started=clock()
    try: result=dict(runner(frame["bob"],syn,candidate_id=policy["candidate_id"],manifest=cb,matrices=mats,check_count=checks,p=frame["p"],max_iter=policy["max_iter"]))
    except Exception as exc: result={"status":"decoder_error","reason":f"{type(exc).__name__}: {exc}","iterations":0}
    elapsed=clock()-started; decoded=result.get("decoded_symbols"); status=result.get("status","decoder_error")
    if elapsed>CAPS["decoder_call_s"]: status="aborted_resource_limit"; result={"status":status,"reason":"decoder_call_s","iterations":int(result.get("iterations",0))}
    if status not in {"syndrome_consistent","decode_failed","aborted_resource_limit","decoder_error","codebook_invalid","invalid_input","unsupported_domain"}:status="decoder_error";result={"status":status,"reason":"unknown_decoder_status","iterations":int(result.get("iterations",0))}
    invoked=status=="syndrome_consistent"; accounting=nonbinary_disclosure_accounting(checks,Q,verification_invoked=invoked,verification_tag_bits=64,public_control_bits=SEED_BITS if invoked else 0)
    if status=="syndrome_consistent":
      check=verify_nonbinary_symbols(frame["alice"],decoded,Q,seed,invoked=True);status="verified_success" if check["verified"] else "verify_failed";accounting=nonbinary_disclosure_accounting(checks,Q,verification_invoked=True)
    events=[{"event_id":0,"frame_key":frame["frame_id"],"method":METHOD,"event_type":"SYNDROME","direction":"alice_to_bob","parent_event_id":-1,"pass_id":0,"plane_id":"q1024","key_dependent_bits":checks*10,"public_control_bits":0,"payload":{"syndrome":list(syn)}},{"event_id":1,"frame_key":frame["frame_id"],"method":METHOD,"event_type":"DECODER","direction":"bob_local","parent_event_id":0,"pass_id":0,"plane_id":"q1024","key_dependent_bits":0,"public_control_bits":0,"payload":{"reason":str(result.get("reason",status))}}]
    if invoked:events.append({"event_id":2,"frame_key":frame["frame_id"],"method":METHOD,"event_type":"VERIFICATION_TAG","direction":"alice_to_bob","parent_event_id":1,"pass_id":0,"plane_id":"q1024","key_dependent_bits":64,"public_control_bits":SEED_BITS,"payload":{"tag":toeplitz_tag(symbols_to_msb_bits(frame["alice"],Q),locked_seed_bits(seed,SEED_BITS)).hex(),"seed_id":seed["seed_id"],"seed_bit_length":SEED_BITS}})
    return {"frame_id":frame["frame_id"],"stratum_p":frame["p"],"qualification_role":frame["role"],"policy_sha256":policy["policy_sha256"],"status":status,"denominator_included":status not in {"unsupported_domain","invalid_input"},"iterations":result.get("iterations",0),"runtime_s":elapsed,"check_count":checks,"verification_invoked":invoked,"verification_seed_id":seed["seed_id"] if invoked else "","array_sha256":frame["array_sha256"],**accounting,**transcript_summary(events),"transcript_event_count":len(events)},events
def _aborted(frame,policy,seed,cb,mats,reason="complete_run_seconds"):
    checks=_setting(policy,frame["p"])["check_count"]; account=nonbinary_disclosure_accounting(checks,Q,verification_invoked=False)
    row,events=_one(frame,policy,seed,lambda *a,**k:{"status":"aborted_resource_limit","reason":reason,"iterations":0},cb,mats,clock=lambda:0.0)
    row["abort_reason"]=reason
    return row,events
def _artifact_hashes(out):return {name:_sha((out/name).read_bytes()) for name in ARTIFACTS if name not in {"formal_run_manifest.json","formal_qualification_report.json"} and (out/name).exists()}
def _write_run(out,rows,events,selection,cb,confirmation_material=None,exception=None):
    ready=bool(selection["selected_policy"] and all(sum(x["status"]=="verified_success" and float(x["stratum_p"])==p for x in rows if x["qualification_role"]=="development" and x["policy_sha256"]==selection["selected_policy_sha256"])>=22 for p in PS)); policy_payload={"selection":selection,"selected_policy_sha256":selection["selected_policy_sha256"],"readiness":ready}
    if ready:policy_payload["confirmation_material"]=confirmation_material
    _put(out/"formal_codebook_manifest.json",cb);_put(out/"formal_candidate_manifest.json",_candidate_manifest());_put(out/"formal_policy_manifest.json",policy_payload);_csv(out/"formal_frame_outcomes.csv",rows)
    with (out/"formal_transcript.jsonl").open("xb") as f:
        for event in events:f.write(canonical_event(event))
    status="completed" if ready else "non_promoted_development"; manifest={"run_id":RUN_ID,"run_status":status,"outcome_count":len(rows),"exception":exception,"artifacts":_artifact_hashes(out)};_put(out/"formal_run_manifest.json",manifest)
    prohibited={"decoder_error","codebook_invalid","invalid_run","syndrome_inconsistent","unsupported_domain"}; gates={str(p):{"requested":32,"denominator_included":sum(x["qualification_role"]=="confirmation" and float(x["stratum_p"])==p and str(x["denominator_included"]).lower()=="true" for x in rows),"verified_success":sum(x["qualification_role"]=="confirmation" and float(x["stratum_p"])==p and x["status"]=="verified_success" for x in rows),"prohibited_failures":sum(x["qualification_role"]=="confirmation" and float(x["stratum_p"])==p and x["status"] in prohibited for x in rows)} for p in PS};_put(out/"formal_qualification_report.json",{"run_id":RUN_ID,"run_status":status,"readiness":ready,"promotion_gates":gates,"promoted":ready and all(x["denominator_included"]==32 and x["verified_success"]>=31 and x["prohibited_failures"]==0 for x in gates.values()),"formal_run_manifest_sha256":_sha((out/"formal_run_manifest.json").read_bytes())})
def _finalize_invalid(out,exc,state=None):
    state=state or {"rows":[],"events":[],"policy":None}
    if not (out/"formal_frame_outcomes.csv").exists():_csv(out/"formal_frame_outcomes.csv",state["rows"])
    if not (out/"formal_transcript.jsonl").exists():(out/"formal_transcript.jsonl").write_bytes(b"".join(canonical_event(x) for x in state["events"]))
    for name in ("formal_codebook_manifest.json","formal_candidate_manifest.json","formal_policy_manifest.json"):
        if not (out/name).exists():_put(out/name,state.get("policy") if name=="formal_policy_manifest.json" and state.get("policy") else {"invalid":True})
    manifest={"run_id":RUN_ID,"run_status":"invalid_run","reason":f"{type(exc).__name__}: {exc}","outcome_count":len(state["rows"]),"artifacts":_artifact_hashes(out)};_put(out/"formal_run_manifest.json",manifest);_put(out/"formal_qualification_report.json",{"run_id":RUN_ID,"run_status":"invalid_run","readiness":False,"promoted":False,"formal_run_manifest_sha256":_sha((out/"formal_run_manifest.json").read_bytes())})
def run(output=None,*,runner:Callable|None=None,_test_only=False,clock:Callable[[],float]=time.monotonic,fatal_hook:Callable[[int],None]|None=None):
    if runner is None:
      if _test_only:raise ValueError("test-only run requires explicit runner")
      runner=production_runner
    out=_output(output,_test_only=_test_only)
    if {x.name for x in out.iterdir()}!={"pre_run_plan.json"}:raise ValueError("run requires plan-only directory")
    plan_path=out/"pre_run_plan.json";plan=json.loads(plan_path.read_text());_validate_plan(plan,plan_path=plan_path);start=clock(); dev={p["policy_sha256"]:[] for p in plan["policies"]};events=[];state={"rows":[],"events":events,"policy":None}
    try:
      cb,mats=build_nbldpc_v3_codebook()
      capped=False
      for policy in plan["policies"]:
        for frame in plan["frames"]:
          seed=plan["development_toeplitz_seeds"][policy["policy_sha256"]+"|"+frame["frame_id"]]
          if capped or clock()-start>CAPS["complete_run_s"]:capped=True;row,ev=_aborted(frame,policy,seed,cb,mats)
          else:row,ev=_one(frame,policy,seed,runner,cb,mats,clock)
          dev[policy["policy_sha256"]].append(row);events+=ev;state["rows"].append(row)
          if fatal_hook is not None:fatal_hook(len(state["rows"]))
      selection=_select(dev,plan["policies"]); rows=state["rows"]; material=None;state["policy"]={"policies":plan["policies"],"development_outcomes":dev,"selection":selection,"selected_policy_sha256":selection["selected_policy_sha256"]}
      ready=bool(selection["selected_policy"] and all(sum(x["status"]=="verified_success" and float(x["stratum_p"])==p for x in dev[selection["selected_policy_sha256"]])>=22 for p in PS))
      if ready:
        policy=selection["selected_policy"]; material={"frames":[],"toeplitz_seeds":{}}; all_ids={x["seed_id"] for x in plan["development_toeplitz_seeds"].values()}|_prior_seed_ids(exclude=out)
        for p in PS:
          for i in range(32):
            frame=_frame(p,"confirmation",i);seed=materialize_seed_record(SEED_BITS)
            if seed["seed_id"] in all_ids:raise RuntimeError("confirmation seed overlap")
            all_ids.add(seed["seed_id"]);material["frames"].append(frame);material["toeplitz_seeds"][policy["policy_sha256"]+"|"+frame["frame_id"]]=seed
        state["policy"]={"policies":plan["policies"],"development_outcomes":dev,"selection":selection,"selected_policy_sha256":selection["selected_policy_sha256"],"confirmation_material":material}
        for frame in material["frames"]:
          seed=material["toeplitz_seeds"][policy["policy_sha256"]+"|"+frame["frame_id"]]
          row,ev=_aborted(frame,policy,seed,cb,mats) if clock()-start>CAPS["complete_run_s"] else _one(frame,policy,seed,runner,cb,mats,clock);rows.append(row);events+=ev
          if fatal_hook is not None:fatal_hook(len(state["rows"]))
      _write_run(out,rows,events,selection,cb,material);return json.loads((out/"formal_qualification_report.json").read_text())
    except Exception as exc:_finalize_invalid(out,exc,state);raise
def _same(expected,row):
    # Wall time is an observed cap diagnostic, not deterministic evidence.  It
    # must be finite/nonnegative, while status and the deterministic transcript
    # prove cap behaviour.  CSV has one header shared by aborted rows.
    actual=dict(row); replay=dict(expected)
    if actual.get("abort_reason")=="":actual.pop("abort_reason")
    try: runtime=float(actual.pop("runtime_s")); replay.pop("runtime_s",None)
    except (TypeError,ValueError):return False
    if not math.isfinite(runtime) or runtime<0:return False
    return {k:str(v) for k,v in replay.items()}=={k:str(v) for k,v in actual.items()}
def verify(output=None,*,verifier_runner:Callable|None=None,_test_only=False):
    out=_output(output,_test_only=_test_only);plan_path=out/"pre_run_plan.json";plan=json.loads(plan_path.read_text());_validate_plan(plan,plan_path=plan_path)
    if {x.name for x in out.iterdir()}=={"pre_run_plan.json"}:return {"verified":True,"plan_only":True,"run_status":"planned","promoted":False}
    manifest=json.loads((out/"formal_run_manifest.json").read_text())
    if manifest.get("run_status")=="invalid_run":
      report=json.loads((out/"formal_qualification_report.json").read_text())
      if {x.name for x in out.iterdir()}!=set(ARTIFACTS) or set(manifest)!={"run_id","run_status","reason","outcome_count","artifacts"} or set(report)!={"run_id","run_status","readiness","promoted","formal_run_manifest_sha256"} or manifest.get("run_id")!=RUN_ID or manifest.get("artifacts")!=_artifact_hashes(out) or not isinstance(manifest.get("reason"),str) or not manifest["reason"] or report.get("run_status")!="invalid_run" or report.get("readiness") is not False or report.get("promoted") is not False or report.get("formal_run_manifest_sha256")!=_sha((out/"formal_run_manifest.json").read_bytes()):raise ValueError("invalid package")
      partial=_rows(out/"formal_frame_outcomes.csv"); raw=(out/"formal_transcript.jsonl").read_bytes(); policy_state=json.loads((out/"formal_policy_manifest.json").read_text())
      if manifest.get("outcome_count")!=len(partial) or json.loads((out/"formal_codebook_manifest.json").read_text())!={"invalid":True} or json.loads((out/"formal_candidate_manifest.json").read_text())!={"invalid":True}:raise ValueError("invalid sentinel replay")
      if not partial and (raw or policy_state!={"invalid":True}):raise ValueError("invalid empty state")
      if partial:
        if verifier_runner is None and _test_only:raise ValueError("test-only verify requires explicit verifier_runner")
        if verifier_runner is None:verifier_runner=production_runner
        cb,mats=build_nbldpc_v3_codebook(); expected=[(f,p,plan["development_toeplitz_seeds"][p["policy_sha256"]+"|"+f["frame_id"]]) for p in plan["policies"] for f in plan["frames"]]
        if len(partial)==len(expected) and policy_state!={"invalid":True}:
          if policy_state.get("policies")!=plan["policies"] or set(policy_state.get("development_outcomes",{}))!={p["policy_sha256"] for p in plan["policies"]}:raise ValueError("invalid complete-development state")
          replay_selection=_select({p["policy_sha256"]:[x for x in partial if x.get("policy_sha256")==p["policy_sha256"]] for p in plan["policies"]},plan["policies"])
          if policy_state.get("selection")!=replay_selection or policy_state.get("selected_policy_sha256")!=replay_selection["selected_policy_sha256"]:raise ValueError("invalid complete-development selection")
          for policy in plan["policies"]:
            stored=policy_state["development_outcomes"][policy["policy_sha256"]]; actual=[x for x in partial if x.get("policy_sha256")==policy["policy_sha256"]]
            if len(stored)!=len(actual) or any(not _same(x,y) for x,y in zip(stored,actual)):raise ValueError("invalid complete-development outcomes")
        elif len(partial)>len(expected):
          if len(partial)>len(expected)+64 or policy_state.get("policies")!=plan["policies"] or policy_state.get("selected_policy_sha256")!=policy_state.get("selection",{}).get("selected_policy_sha256"):raise ValueError("invalid partial confirmation state")
          dev_rows=partial[:len(expected)]
          if set(policy_state.get("development_outcomes",{}))!={p["policy_sha256"] for p in plan["policies"]}:raise ValueError("invalid partial development outcomes")
          replay_selection=_select({p["policy_sha256"]:[x for x in dev_rows if x.get("policy_sha256")==p["policy_sha256"]] for p in plan["policies"]},plan["policies"])
          if policy_state.get("selection")!=replay_selection or not replay_selection["selected_policy"]:raise ValueError("invalid partial selection")
          for policy in plan["policies"]:
            stored=policy_state["development_outcomes"][policy["policy_sha256"]]; actual=[x for x in dev_rows if x.get("policy_sha256")==policy["policy_sha256"]]
            if len(stored)!=len(actual) or any(not _same(x,y) for x,y in zip(stored,actual)):raise ValueError("invalid partial development outcomes")
          material=policy_state.get("confirmation_material"); selected=replay_selection["selected_policy"]
          if not isinstance(material,dict) or len(material.get("frames",[]))!=64 or len(material.get("toeplitz_seeds",{}))!=64:raise ValueError("invalid partial confirmation material")
          confirmation=[]
          for frame in material["frames"]:
            if frame!=_frame(frame.get("p"),"confirmation",frame.get("index")):raise ValueError("invalid partial confirmation frame")
            seed=material["toeplitz_seeds"].get(selected["policy_sha256"]+"|"+frame["frame_id"])
            locked_seed_bits(seed,SEED_BITS);confirmation.append((frame,selected,seed))
          expected+=confirmation
        elif policy_state!={"invalid":True}:raise ValueError("invalid partial sentinel state")
        if [x.get("frame_id") for x in partial]!=[f["frame_id"] for f,_,_ in expected[:len(partial)]] or [x.get("policy_sha256") for x in partial]!=[p["policy_sha256"] for _,p,_ in expected[:len(partial)]]:raise ValueError("invalid partial order")
        parsed=[json.loads(x) for x in raw.splitlines()]
        if b"".join(canonical_event(x) for x in parsed)!=raw:raise ValueError("invalid transcript")
        cursor=0
        for index,(row,(frame,policy,seed)) in enumerate(zip(partial,expected)):
          replay,events=_aborted(frame,policy,seed,cb,mats) if row.get("status")=="aborted_resource_limit" and row.get("abort_reason")=="complete_run_seconds" else _one(frame,policy,seed,verifier_runner,cb,mats,lambda:0.0)
          count=int(row.get("transcript_event_count") or 0); piece=parsed[cursor:cursor+count];cursor+=count
          if not _same(replay,row) or piece!=events:raise ValueError(f"invalid partial replay at {index}")
        if cursor!=len(parsed):raise ValueError("orphan invalid events")
      return {"verified":True,"run_status":"invalid_run","promoted":False}
    if {x.name for x in out.iterdir()}!=set(ARTIFACTS):raise ValueError("normal artifact set")
    if set(manifest)!={"run_id","run_status","outcome_count","exception","artifacts"} or set(json.loads((out/"formal_qualification_report.json").read_text()))!={"run_id","run_status","readiness","promotion_gates","promoted","formal_run_manifest_sha256"}:raise ValueError("normal package shape")
    rows=_rows(out/"formal_frame_outcomes.csv"); policy=json.loads((out/"formal_policy_manifest.json").read_text());report=json.loads((out/"formal_qualification_report.json").read_text())
    if manifest.get("run_id")!=RUN_ID or report.get("run_id")!=RUN_ID or manifest.get("exception") is not None:raise ValueError("normal package identity")
    if verifier_runner is None and _test_only:raise ValueError("test-only verify requires explicit verifier_runner")
    if verifier_runner is None:verifier_runner=production_runner
    if manifest.get("artifacts")!=_artifact_hashes(out) or manifest.get("outcome_count")!=len(rows):raise ValueError("artifact DAG")
    if report.get("formal_run_manifest_sha256")!=_sha((out/"formal_run_manifest.json").read_bytes()):raise ValueError("report manifest hash")
    if json.loads((out/"formal_codebook_manifest.json").read_text())!=build_nbldpc_v3_codebook()[0] or json.loads((out/"formal_candidate_manifest.json").read_text())!=_candidate_manifest():raise ValueError("candidate/codebook replay")
    actual_events=(out/"formal_transcript.jsonl").read_bytes().splitlines(keepends=True)
    cb,mats=build_nbldpc_v3_codebook(); by_id={x["frame_id"]:x for x in plan["frames"]};by_policy={x["policy_sha256"]:x for x in plan["policies"]}; expected_dev=[]
    for pol in plan["policies"]:
      for frame in plan["frames"]:
        seed=plan["development_toeplitz_seeds"][pol["policy_sha256"]+"|"+frame["frame_id"]];expected_dev.append((frame,pol,seed))
    dev=[x for x in rows if x["qualification_role"]=="development"]
    if len(dev)!=192 or [x["frame_id"] for x in dev]!=[x[0]["frame_id"] for x in expected_dev] or [x["policy_sha256"] for x in dev]!=[x[1]["policy_sha256"] for x in expected_dev]:raise ValueError("development row order/count")
    for row,(frame,pol,seed) in zip(dev,expected_dev):
      expected,ev=_aborted(frame,pol,seed,cb,mats) if row["status"]=="aborted_resource_limit" and row.get("abort_reason")=="complete_run_seconds" else _one(frame,pol,seed,verifier_runner,cb,mats,lambda:0.0)
      if not _same(expected,row):raise ValueError("development deterministic replay")
      if [canonical_event(x) for x in ev] != actual_events[:len(ev)]:raise ValueError("transcript row/event replay")
      actual_events=actual_events[len(ev):]
    reconstructed=_select({p["policy_sha256"]:[x for x in dev if x["policy_sha256"]==p["policy_sha256"]] for p in plan["policies"]},plan["policies"])
    if reconstructed!=policy.get("selection") or policy.get("selected_policy_sha256")!=reconstructed["selected_policy_sha256"]:raise ValueError("selection replay")
    selected=reconstructed["selected_policy_sha256"];ready=bool(selected and all(sum(x["status"]=="verified_success" and float(x["stratum_p"])==p for x in dev if x["policy_sha256"]==selected)>=22 for p in PS))
    conf=[x for x in rows if x["qualification_role"]=="confirmation"]
    if ready!=bool(policy.get("readiness")):raise ValueError("readiness replay")
    expected_status="completed" if ready else "non_promoted_development"
    if manifest.get("run_status")!=expected_status or report.get("run_status")!=expected_status or report.get("readiness")!=ready:raise ValueError("normal run status")
    if not ready:
      if conf or "confirmation_material" in policy or report.get("run_status")!="non_promoted_development":raise ValueError("confirmation isolation")
    else:
      material=policy.get("confirmation_material"); selected_pol=reconstructed["selected_policy"]
      if not isinstance(material,dict) or len(material.get("frames",[]))!=64 or len(material.get("toeplitz_seeds",{}))!=64 or len(conf)!=64:raise ValueError("confirmation material/count")
      if [x["frame_id"] for x in conf]!=[x["frame_id"] for x in material["frames"]]:raise ValueError("confirmation row order")
      ids=[]
      for row,frame in zip(conf,material["frames"]):
        if frame!=_frame(frame["p"],"confirmation",frame["index"]):raise ValueError("confirmation frame replay")
        seed=material["toeplitz_seeds"].get(selected_pol["policy_sha256"]+"|"+frame["frame_id"]);locked_seed_bits(seed,SEED_BITS);ids.append(seed["seed_id"])
        expected,ev=_aborted(frame,selected_pol,seed,cb,mats) if row["status"]=="aborted_resource_limit" and row.get("abort_reason")=="complete_run_seconds" else _one(frame,selected_pol,seed,verifier_runner,cb,mats,lambda:0.0)
        if not _same(expected,row):raise ValueError("confirmation deterministic replay")
        if [canonical_event(x) for x in ev] != actual_events[:len(ev)]:raise ValueError("transcript row/event replay")
        actual_events=actual_events[len(ev):]
      dev_ids={x["seed_id"] for x in plan["development_toeplitz_seeds"].values()}
      if len(ids)!=64 or len(set(ids))!=64 or set(ids)&dev_ids or set(ids)&_prior_seed_ids(exclude=out):raise ValueError("confirmation seed isolation")
      if any(_identity_overlap(material["frames"],exclude=out).values()):raise ValueError("confirmation identity isolation")
      if report.get("run_status")!="completed":raise ValueError("report gates")
    if actual_events:raise ValueError("orphan transcript events")
    prohibited={"decoder_error","codebook_invalid","invalid_run","syndrome_inconsistent","unsupported_domain"};gates={str(p):{"requested":32,"denominator_included":sum(x["qualification_role"]=="confirmation" and float(x["stratum_p"])==p and str(x["denominator_included"]).lower()=="true" for x in rows),"verified_success":sum(x["qualification_role"]=="confirmation" and float(x["stratum_p"])==p and x["status"]=="verified_success" for x in rows),"prohibited_failures":sum(x["qualification_role"]=="confirmation" and float(x["stratum_p"])==p and x["status"] in prohibited for x in rows)} for p in PS}
    if report.get("promotion_gates")!=gates or bool(report.get("promoted"))!=(ready and all(x["denominator_included"]==32 and x["verified_success"]>=31 and x["prohibited_failures"]==0 for x in gates.values())):raise ValueError("promotion gates")
    return {"verified":True,"run_status":report["run_status"],"promoted":report["promoted"]}
