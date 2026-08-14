"""Frozen, additive NBLDPC v2 synthetic qualification machinery.

This module owns evidence packages only; it neither reads real data nor mutates
the v1 lane.  Plan creation is the only operation which obtains CSPRNG seeds.
"""
from __future__ import annotations
import csv, hashlib, json, math, platform, subprocess, time
from pathlib import Path
from typing import Any, Callable, Mapping
import numpy as np
from .nonbinary_v2 import METHOD, CANDIDATE_IDS, build_nbldpc_v2_codebook, verify_nbldpc_v2_codebook, decode_nbldpc_v2
from .nonbinary_codebook import build_nonbinary_codebook_family, verify_nonbinary_codebook_family
from .nonbinary_field import GF2mField, get_field_spec
from .nonbinary_qspa import nonbinary_syndrome, nonbinary_disclosure_accounting, symbols_to_msb_bits, verify_nonbinary_symbols
from .shared import canonical_event, locked_seed_bits, materialize_seed_record, toeplitz_tag, transcript_summary

RUN_ID="20260726_v2_nbldpc_synthetic"; Q,N=1024,64; PS=(.20,.30); SEED_BITS=703
ARTIFACTS=("pre_run_plan.json","formal_frame_outcomes.csv","formal_transcript.jsonl","formal_run_manifest.json","formal_codebook_manifest.json","formal_candidate_manifest.json","formal_policy_manifest.json","formal_qualification_report.json")
CAPS={"decoder_call_s":20,"complete_run_s":21600,"workers":1,"q":Q,"n":N,"checks_max":48,"row_weight":4,"max_iter":20,"dense_bytes_max":16*1024*1024}
STATUSES={"verified_success","verify_failed","decode_failed","syndrome_inconsistent","aborted_resource_limit","decoder_error","unsupported_domain","codebook_invalid","invalid_run","non_promoted_development"}
ROOTS={("development",.20):202607340000,("development",.30):202607350000,("confirmation",.20):202607360000,("confirmation",.30):202607370000}
OFFICIAL_OUTPUT_ROOT=Path("comparison_bench/outputs_comparison/formal_ir_methods")/RUN_ID
def _compact(x): return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
def _sha(x): return hashlib.sha256(x).hexdigest()
def _put(p,x):
    with p.open("xb") as f:f.write(json.dumps(x,sort_keys=True,indent=2,ensure_ascii=True,allow_nan=False).encode()+b"\n")
def _csv(p,rows):
    with p.open("x",newline="",encoding="utf8") as f:
        w=csv.DictWriter(f,fieldnames=sorted({k for r in rows for k in r}) or ["status"]);w.writeheader();w.writerows(rows)
def _rows(p):
    with p.open(newline="",encoding="utf8") as f:return list(csv.DictReader(f))
def _root(): return Path(__file__).resolve().parents[4]
def _output(output:Path|None,*,_test_only:bool)->Path:
    official=(_root()/OFFICIAL_OUTPUT_ROOT).resolve()
    chosen=official if output is None else Path(output).resolve()
    if chosen!=official and not _test_only: raise ValueError("v2 requires the frozen official output root")
    return chosen
def _frame(p,role,i):
    seed=ROOTS[role,p]+i; r=np.random.Generator(np.random.PCG64(seed)); a=r.integers(0,Q,N,dtype=np.int64); m=r.random(N)<p; e=r.integers(1,Q,N,dtype=np.int64); b=a.copy();b[m]^=e[m]
    return {"frame_id":f"{METHOD}_q1024_p{int(p*100):02d}_{role}_{i:03d}","p":p,"role":role,"index":i,"seed":seed,"alice":a.tolist(),"bob":b.tolist(),"array_sha256":_sha(a.astype('<i8').tobytes()+b.astype('<i8').tobytes()),"atomic_keys":[f"{role}|{p}|{i}|{j}" for j in range(N)]}
def _h2(p): return -p*math.log2(p)-(1-p)*math.log2(1-p)
def policy_grid():
    out=[]
    for candidate in CANDIDATE_IDS:
      prefixes=(16,24,32) if candidate==CANDIDATE_IDS[0] else (24,32,40,48)
      for margin in (0,4,8):
       for maximum in (10,20):
        strata=[]
        for p in PS:
          need=math.ceil(N*(_h2(p)+p*math.log2(1023))/10)+margin; checks=next((x for x in prefixes if x>=need),None)
          strata.append({"p":p,"needed_checks":need,"check_count":checks,"decoder_p":p})
        body={"candidate_id":candidate,"permitted_prefixes":list(prefixes),"rate_margin_symbols":margin,"max_iter":maximum,"strata":strata}
        out.append(dict(body,policy_sha256=_sha(_compact(body))))
    return out
def _candidate_manifest():
    qc,_=build_nbldpc_v2_codebook(); n1,_=build_nonbinary_codebook_family(Q)
    return {"method":METHOD,"candidate_ids":list(CANDIDATE_IDS),
      "codebook_by_candidate":{CANDIDATE_IDS[0]:"control_n1",**{x:"qc48" for x in CANDIDATE_IDS[1:]}},
      "canonical_codebooks":{
        "control_n1":{"manifest_id":n1["manifest_id"],"ordered_codebook_ids":[x["codebook_id"] for x in n1["ordered_entries"]]},
        "qc48":{"manifest_id":qc["manifest_id"],"ordered_codebook_ids":[x["codebook_id"] for x in qc["ordered_entries"]]}},
      "decoder_definitions":{
        CANDIDATE_IDS[0]:{"schedule":"flooding","damping":None,"tempering":None},
        CANDIDATE_IDS[1]:{"schedule":"flooding","damping":None,"tempering":None},
        CANDIDATE_IDS[2]:{"schedule":"flooding","damping":.5,"tempering":None},
        CANDIDATE_IDS[3]:{"schedule":"flooding","damping":.5,"tempering":.8}},
      "float":"float64","truth_isolated":True}
def _prior_seed_ids(*,exclude:Path|None=None):
    base=_root()/"comparison_bench"/"outputs_comparison"/"formal_ir_methods"; found=set()
    if base.exists():
      for path in base.rglob("pre_run_plan.json"):
       if exclude is not None and path.resolve()==exclude.resolve(): continue
       try:
        data=json.loads(path.read_text(encoding="utf8"))
        for group in (data.get("development_toeplitz_seeds",{}),data.get("confirmation_toeplitz_seeds",{})):
         if isinstance(group,dict):
          found.update(str(v["seed_id"]) for v in group.values() if isinstance(v,dict) and "seed_id" in v)
       except (OSError,ValueError,TypeError): pass
    return found
def _provenance():
    formal=Path(__file__).parent; cli=Path(__file__).parents[1]/"cli"/"run_formal_nonbinary_v2_qualification.py"; names=("nonbinary_field.py","nonbinary_codebook.py","nonbinary_qspa.py","nonbinary_v2.py","nonbinary_v2_qualification.py")
    try:
      commit=subprocess.run(["git","rev-parse","HEAD"],cwd=_root(),capture_output=True,check=True).stdout.decode().strip()
      status=subprocess.run(["git","status","--porcelain=v1","--untracked-files=all","--",".",f":(exclude){OFFICIAL_OUTPUT_ROOT.as_posix()}"],cwd=_root(),capture_output=True,check=True).stdout
    except Exception: commit=None;status=b""
    roots={f"{role}_p{int(p*100):02d}": ROOTS[role,p] for role in ("development","confirmation") for p in PS}
    return {"git":{"commit":commit,"status_porcelain_v1_sha256":_sha(status),"dirty":bool(status)},"environment":{"python":platform.python_version(),"numpy":np.__version__},"source_sha256":{x:_sha((formal/x).read_bytes()) for x in names},"cli_sha256":_sha(cli.read_bytes()),"candidate_manifest_sha256":_sha(_compact(_candidate_manifest())),"contract_sha256":_sha(_compact({"roots":roots,"grid":policy_grid(),"caps":CAPS}))}
def _verify_provenance(stored,live):
    for k in ("environment","source_sha256","cli_sha256","candidate_manifest_sha256","contract_sha256"):
      if stored.get(k)!=live.get(k): raise ValueError("scoped provenance drift")
    if stored.get("git",{}).get("commit")!=live.get("git",{}).get("commit"):raise ValueError("commit drift")
def expected_plan(*, materialize:bool=True,exclude_plan:Path|None=None):
    fs=[_frame(p,r,i) for r,c in (("development",24),("confirmation",32)) for p in PS for i in range(c)];dev=[x for x in fs if x["role"]=="development"];con=[x for x in fs if x["role"]=="confirmation"];grid=policy_grid()
    ds={f"{x['policy_sha256']}|{f['frame_id']}":materialize_seed_record(SEED_BITS) for x in grid for f in dev} if materialize else {}; cs={f["frame_id"]:materialize_seed_record(SEED_BITS) for f in con} if materialize else {}; ids=[x["seed_id"] for x in (*ds.values(),*cs.values())]
    overlap=sorted(set(ids)&_prior_seed_ids(exclude=exclude_plan))
    return {"canonical_schema":"NBLDPCQ2","run_id":RUN_ID,"method":METHOD,"q":Q,"n":N,"frames":fs,"development_execution_order":[f["frame_id"] for f in dev],"confirmation_execution_order":[f["frame_id"] for f in con],"generator":{"pcg":"PCG64","call_order":["integers_alice","random_error_mask","integers_nonzero_errors","masked_xor"],"roots":{f"{r}_p{int(p*100):02d}":ROOTS[r,p] for r in ("development","confirmation") for p in PS}},"generator_sha256":_sha(_compact(fs)),"policies":grid,"development_toeplitz_seeds":ds,"confirmation_toeplitz_seeds":cs,"toeplitz":{"input_bits":640,"tag_bits":64,"seed_bits":SEED_BITS,"globally_unique":len(ids)==len(set(ids)),"prior_plan_overlap_seed_ids":overlap},"caps":CAPS,"artifact_schema":list(ARTIFACTS),"candidate_manifest_sha256":_sha(_compact(_candidate_manifest())),"provenance":_provenance()}
def create_plan(output:Path|None=None,*,_test_only:bool=False):
    output=_output(output,_test_only=_test_only)
    if output.exists():raise FileExistsError("fresh output required")
    plan=expected_plan(exclude_plan=output/ARTIFACTS[0])
    if plan["toeplitz"]["prior_plan_overlap_seed_ids"]: raise ValueError("prior formal Toeplitz seed overlap")
    output.mkdir(parents=True);_put(output/ARTIFACTS[0],plan);return plan
def _validate(plan,*,plan_path:Path|None=None,live=False):
    probe=expected_plan(materialize=False,exclude_plan=plan_path); keys=("canonical_schema","run_id","method","q","n","frames","development_execution_order","confirmation_execution_order","generator","generator_sha256","policies","caps","artifact_schema","candidate_manifest_sha256")
    if any(plan.get(k)!=probe.get(k) for k in keys):raise ValueError("plan reconstruction")
    if plan.get("toeplitz",{}).get("input_bits")!=640 or plan.get("toeplitz",{}).get("tag_bits")!=64 or len(plan["development_toeplitz_seeds"])!=1152 or len(plan["confirmation_toeplitz_seeds"])!=64:raise ValueError("seed count")
    ss=[*plan["development_toeplitz_seeds"].values(),*plan["confirmation_toeplitz_seeds"].values()]
    expected_dev={f"{p['policy_sha256']}|{f}" for p in plan["policies"] for f in plan["development_execution_order"]}
    if set(plan["development_toeplitz_seeds"])!=expected_dev or set(plan["confirmation_toeplitz_seeds"])!=set(plan["confirmation_execution_order"]): raise ValueError("seed bindings")
    if len({x["seed_id"] for x in ss})!=len(ss) or any(locked_seed_bits(x,SEED_BITS) is None for x in ss):raise ValueError("seed integrity")
    if plan["toeplitz"].get("prior_plan_overlap_seed_ids") or (plan_path and {x["seed_id"] for x in ss}&_prior_seed_ids(exclude=plan_path)): raise ValueError("seed overlap")
    if live:_verify_provenance(plan["provenance"],_provenance())
def _setting(policy,p):return next(x for x in policy["strata"] if x["p"]==p)
def _select(dev,grid):
    scored=[]
    for p in grid:
      rows=dev[p["policy_sha256"]]; a=[sum(x["status"]=="verified_success" for x in rows if x["stratum_p"]==s) for s in PS]
      allowed={"verified_success","verify_failed","decode_failed","aborted_resource_limit"}
      eligible=all(_setting(p,s)["check_count"] is not None for s in PS) and len(rows)==48 and all(x.get("status") in allowed for x in rows)
      if eligible: scored.append((-min(a),-sum(a),sum(int(x["key_dependent_disclosure_bits_total"]) for x in rows),sum(int(x["iterations"]) for x in rows),p["policy_sha256"],p))
    if not scored:return {"selected_policy":None,"selected_policy_sha256":None,"selection_key":None,"reason":"no_eligible_policy"}
    x=min(scored);return {"selected_policy":x[-1],"selected_policy_sha256":x[-1]["policy_sha256"],"selection_key":list(x[:-1]),"reason":None}
def _one(frame,policy,seed,runner,cb,mats,clock=time.monotonic):
    s=_setting(policy,frame["p"]); check=s["check_count"]
    base={"frame_id":frame["frame_id"],"stratum_p":frame["p"],"qualification_role":frame["role"],"policy_sha256":policy["policy_sha256"],"candidate_id":policy["candidate_id"],"attempted":True,"denominator_included":True}
    if check is None:return {**base,"status":"unsupported_domain","iterations":0,"runtime_s":0.0,"verification_invoked":False,"verification_seed_id":"","check_count":"","decoder_p":frame["p"],"key_dependent_disclosure_bits_total":0,"public_control_bits_total":0,"transcript_event_count":0,"transcript_sha256":_sha(b"")},[]
    a=np.asarray(frame["alice"]);b=np.asarray(frame["bob"]); syndrome=nonbinary_syndrome(mats[check],a,GF2mField(get_field_spec(Q)))
    started=clock()
    try: raw=dict(runner(b,syndrome,candidate_id=policy["candidate_id"],check_count=check,p=frame["p"],max_iter=policy["max_iter"],manifest=cb,matrices=mats))
    except Exception as exc: raw={"status":"decoder_error","reason":f"{type(exc).__name__}: {exc}","iterations":0}
    elapsed=clock()-started; status=raw.get("status","decoder_error")
    if elapsed>CAPS["decoder_call_s"]: status="aborted_resource_limit"; raw={"status":status,"reason":"decoder_call_s","iterations":int(raw.get("iterations",0))}
    if status not in STATUSES|{"syndrome_consistent"}: status="decoder_error"; raw={"status":status,"reason":"unknown decoder status","iterations":int(raw.get("iterations",0))}
    invoked=status=="syndrome_consistent"
    if invoked: status="verified_success" if verify_nonbinary_symbols(a,np.asarray(raw.get("decoded_symbols",b)),Q,seed,invoked=True)["verified"] else "verify_failed"
    acc=nonbinary_disclosure_accounting(check,Q,verification_invoked=invoked,verification_tag_bits=64,public_control_bits=SEED_BITS if invoked else 0); ev=[{"event_id":0,"frame_key":frame["frame_id"],"method":METHOD,"event_type":"SYNDROME","direction":"alice_to_bob","parent_event_id":-1,"pass_id":0,"block_id":0,"key_dependent_bits":check*10,"public_control_bits":0,"payload":{"syndrome":list(syndrome)}},{"event_id":1,"frame_key":frame["frame_id"],"method":METHOD,"event_type":"DECODER","direction":"bob_local","parent_event_id":0,"pass_id":0,"block_id":0,"key_dependent_bits":0,"public_control_bits":0,"payload":{"reason":str(raw.get("reason",status))}}]
    if invoked:ev.append({"event_id":2,"frame_key":frame["frame_id"],"method":METHOD,"event_type":"VERIFICATION_TAG","direction":"alice_to_bob","parent_event_id":1,"pass_id":0,"block_id":0,"key_dependent_bits":64,"public_control_bits":SEED_BITS,"payload":{"tag":toeplitz_tag(symbols_to_msb_bits(a,Q),locked_seed_bits(seed,SEED_BITS)).hex(),"seed_id":seed["seed_id"],"seed_bit_length":SEED_BITS}})
    row={**base,"status":status,"iterations":int(raw.get("iterations",0)),"runtime_s":elapsed,"verification_invoked":invoked,"verification_seed_id":seed["seed_id"] if invoked else "","check_count":check,"decoder_p":frame["p"],**acc,**transcript_summary(ev),"transcript_event_count":len(ev)};return row,ev
def production_runner(bob,syndrome,**kw):
    return decode_nbldpc_v2(kw.pop("candidate_id"),bob,syndrome,kw["manifest"],kw["matrices"],check_count=kw["check_count"],p=kw["p"],max_iter=kw["max_iter"])
def _same_row(actual,expected):
    def norm(v):
      if isinstance(v,str):
       if v in ("True","False"): return v=="True"
       try:return int(v)
       except ValueError:
        try:return float(v)
        except ValueError:return v
      return v
    # DictWriter emits blank cells for fields used only by other status rows.
    a={k:norm(v) for k,v in actual.items() if k!="runtime_s" and not (v=="" and k not in expected)}
    b={k:norm(v) for k,v in expected.items() if k!="runtime_s"}
    return a==b
def _cap(frame,policy,seed,cb,mats):
    def capped(*args,**kwargs): return {"status":"aborted_resource_limit","reason":"complete_run_s","iterations":0}
    return _one(frame,policy,seed,capped,cb,mats,clock=lambda:0.0)
# The run manifest cannot hash itself (and the report binds its final hash).
# Bind exactly the six preceding evidence artifacts, including policy selection.
_DAG_ARTIFACTS=("pre_run_plan.json","formal_frame_outcomes.csv","formal_transcript.jsonl","formal_codebook_manifest.json","formal_candidate_manifest.json","formal_policy_manifest.json")
def _dag(o):return {n:_sha((o/n).read_bytes()) for n in _DAG_ARTIFACTS}
def _artifact_hashes(o):
    names=("pre_run_plan.json","formal_frame_outcomes.csv","formal_transcript.jsonl","formal_codebook_manifest.json","formal_candidate_manifest.json","formal_policy_manifest.json")
    return {n:_sha((o/n).read_bytes()) for n in names if (o/n).exists()}
def _finalize(o,exc,state):
    if not (o/"formal_frame_outcomes.csv").exists(): _csv(o/"formal_frame_outcomes.csv",state.get("rows",[]))
    if not (o/"formal_transcript.jsonl").exists(): (o/"formal_transcript.jsonl").write_bytes(b"".join(canonical_event(x) for x in state.get("events",[])))
    for name,sentinel in (("formal_codebook_manifest.json",{"invalid":True}),("formal_candidate_manifest.json",{"invalid":True}),("formal_policy_manifest.json",{"invalid":True})):
      if not (o/name).exists(): _put(o/name,sentinel)
    if not (o/"formal_run_manifest.json").exists(): _put(o/"formal_run_manifest.json",{"run_id":RUN_ID,"run_status":"invalid_run","reason":f"{type(exc).__name__}: {exc}","artifacts":_artifact_hashes(o)})
    if not (o/"formal_qualification_report.json").exists(): _put(o/"formal_qualification_report.json",{"run_id":RUN_ID,"run_status":"invalid_run","promoted":False,"formal_run_manifest_sha256":_sha((o/"formal_run_manifest.json").read_bytes())})
def run(output:Path|None=None,*,runner:Callable=production_runner,clock:Callable=time.monotonic,_test_only:bool=False):
    output=_output(output,_test_only=_test_only)
    if not output.is_dir() or {x.name for x in output.iterdir()}!={ARTIFACTS[0]}:raise ValueError("execute requires reviewed plan only")
    plan_path=output/ARTIFACTS[0]; plan_bytes=plan_path.read_bytes(); plan=json.loads(plan_bytes);_validate(plan,plan_path=plan_path,live=not _test_only)
    state={"rows":[],"events":[]}
    try:
      started=clock(); qc_cb,qc_mats=build_nbldpc_v2_codebook(); n1_cb,n1_mats=build_nonbinary_codebook_family(Q)
      if verify_nbldpc_v2_codebook(qc_cb,qc_mats)["status"]!="ok" or verify_nonbinary_codebook_family(n1_cb,n1_mats)["status"]!="ok":raise RuntimeError("codebook_invalid")
      cb={"qc48":qc_cb,"control_n1":n1_cb}; _put(output/"formal_codebook_manifest.json",cb);_put(output/"formal_candidate_manifest.json",_candidate_manifest())
      by={x["frame_id"]:x for x in plan["frames"]};dev={p["policy_sha256"]:[] for p in plan["policies"]}
      for p in plan["policies"]:
       active_cb,active_mats=(n1_cb,n1_mats) if p["candidate_id"]==CANDIDATE_IDS[0] else (qc_cb,qc_mats)
       for fid in plan["development_execution_order"]:
        if clock()-started>=CAPS["complete_run_s"]: raise TimeoutError("complete_run_s during development")
        row,ev=_one(by[fid],p,plan["development_toeplitz_seeds"][p["policy_sha256"]+"|"+fid],runner,active_cb,active_mats,clock);dev[p["policy_sha256"]].append(row);state["rows"].append(row);state["events"]+=ev
      sel=_select(dev,plan["policies"]); chosen=sel["selected_policy"]
      ready=chosen is not None and all(sum(x["status"]=="verified_success" for x in dev[chosen["policy_sha256"]] if x["stratum_p"]==p)>=22 for p in PS)
      selected_hash=chosen["policy_sha256"] if chosen else None
      _put(output/"formal_policy_manifest.json",{"policies":plan["policies"],"development_outcomes":dev,"selection":sel,"selected_policy_sha256":selected_hash,"readiness":ready})
      confirmation=[]
      if ready:
       active_cb,active_mats=(n1_cb,n1_mats) if chosen["candidate_id"]==CANDIDATE_IDS[0] else (qc_cb,qc_mats)
       capped=False
       for fid in plan["confirmation_execution_order"]:
        capped=capped or clock()-started>=CAPS["complete_run_s"]
        row,ev=(_cap if capped else _one)(by[fid],chosen,plan["confirmation_toeplitz_seeds"][fid],*( (active_cb,active_mats) if capped else (runner,active_cb,active_mats) ),**({} if capped else {"clock":clock}))
        confirmation.append(row);state["rows"].append(row);state["events"]+=ev
      _csv(output/"formal_frame_outcomes.csv",state["rows"]);(output/"formal_transcript.jsonl").write_bytes(b"".join(canonical_event(x) for x in state["events"]))
      gates={f"p{int(p*100):02d}":{"requested":32,"denominator_included":sum(x["stratum_p"]==p for x in confirmation),"verified_success":sum(x["stratum_p"]==p and x["status"]=="verified_success" for x in confirmation),"prohibited_failures":sum(x["stratum_p"]==p and x["status"] in {"syndrome_inconsistent","decoder_error","codebook_invalid","invalid_run"} for x in confirmation)} for p in PS}
      for g in gates.values(): g["promoted"]=ready and g["denominator_included"]==32 and g["verified_success"]>=31 and g["prohibited_failures"]==0
      status="completed" if ready else "non_promoted_development";_put(output/"formal_run_manifest.json",{"run_id":RUN_ID,"run_status":status,"plan_sha256":_sha(plan_bytes),"selected_policy_sha256":selected_hash,"outcome_count":len(state["rows"]),"artifacts":_artifact_hashes(output)});_put(output/"formal_qualification_report.json",{"run_id":RUN_ID,"run_status":status,"promotion_gates":gates,"promoted":ready and all(x["promoted"] for x in gates.values()),"formal_run_manifest_sha256":_sha((output/"formal_run_manifest.json").read_bytes())})
      if plan_path.read_bytes()!=plan_bytes: raise RuntimeError("plan mutation")
    except BaseException as exc:
      _finalize(output,exc,state); raise
def verify(output:Path|None=None,*,verifier_runner:Callable=production_runner,_test_only:bool=False):
    output=_output(output,_test_only=_test_only)
    names={x.name for x in output.iterdir()};
    plan_path=output/ARTIFACTS[0]
    if names=={ARTIFACTS[0]}:_validate(json.loads(plan_path.read_text()),plan_path=plan_path,live=not _test_only);return {"verified":True,"plan_only":True,"worktree_diagnostic":_provenance()["git"]}
    if names!=set(ARTIFACTS):raise ValueError("eight-artifact contract")
    plan=json.loads(plan_path.read_text());_validate(plan,plan_path=plan_path); live=_provenance();_verify_provenance(plan["provenance"],live)
    manifest=json.loads((output/"formal_run_manifest.json").read_text());report=json.loads((output/"formal_qualification_report.json").read_text())
    if report.get("formal_run_manifest_sha256")!=_sha((output/"formal_run_manifest.json").read_bytes()) or manifest.get("artifacts")!=_artifact_hashes(output):raise ValueError("hash DAG")
    if manifest.get("run_status")=="invalid_run":
      if set(manifest)!={"run_id","run_status","reason","artifacts"} or set(report)!={"run_id","run_status","promoted","formal_run_manifest_sha256"} or manifest.get("run_id")!=RUN_ID or report.get("run_id")!=RUN_ID or report.get("run_status")!="invalid_run" or report.get("promoted") is not False: raise ValueError("invalid run report")
      raw=(output/"formal_transcript.jsonl").read_bytes()
      partial_events=[json.loads(x) for x in raw.splitlines()]
      if b"".join(canonical_event(x) for x in partial_events)!=raw: raise ValueError("invalid transcript")
      codebook=json.loads((output/"formal_codebook_manifest.json").read_text()); candidates=json.loads((output/"formal_candidate_manifest.json").read_text()); policy=json.loads((output/"formal_policy_manifest.json").read_text())
      expected_qc,expected_qc_mats=build_nbldpc_v2_codebook(); expected_n1,expected_n1_mats=build_nonbinary_codebook_family(Q)
      if codebook not in ({"invalid":True},{"qc48":expected_qc,"control_n1":expected_n1}): raise ValueError("invalid codebook state")
      if candidates not in ({"invalid":True},_candidate_manifest()): raise ValueError("invalid candidate state")
      if policy!={"invalid":True} and not (policy.get("policies")==plan["policies"] and isinstance(policy.get("development_outcomes"),dict) and "selection" in policy and "selected_policy_sha256" in policy and "readiness" in policy): raise ValueError("invalid policy state")
      partial_rows=_rows(output/"formal_frame_outcomes.csv"); cursor=0; by={x["frame_id"]:x for x in plan["frames"]}
      expected_sequence=[(p,fid) for p in plan["policies"] for fid in plan["development_execution_order"]]
      if policy!={"invalid":True}:
       stored_dev=policy.get("development_outcomes",{})
       if set(stored_dev)!={p["policy_sha256"] for p in plan["policies"]}: raise ValueError("invalid policy development")
       selection=_select(stored_dev,plan["policies"]); chosen=selection["selected_policy"]
       ready=chosen is not None and all(sum(x["status"]=="verified_success" for x in stored_dev[chosen["policy_sha256"]] if float(x["stratum_p"])==p)>=22 for p in PS)
       if policy.get("selection")!=selection or policy.get("selected_policy_sha256")!=(chosen["policy_sha256"] if chosen else None) or policy.get("readiness")!=ready: raise ValueError("invalid policy selection")
       if ready: expected_sequence += [(chosen,fid) for fid in plan["confirmation_execution_order"]]
      if len(partial_rows)>len(expected_sequence): raise ValueError("invalid partial length")
      if partial_rows and (codebook=={"invalid":True} or candidates=={"invalid":True}): raise ValueError("rows without candidate state")
      for index,(row,(p,fid)) in enumerate(zip(partial_rows,expected_sequence)):
       cb,mats=((expected_n1,expected_n1_mats) if p["candidate_id"]==CANDIDATE_IDS[0] else (expected_qc,expected_qc_mats))
       seed=(plan["development_toeplitz_seeds"][p["policy_sha256"]+"|"+fid] if by[fid]["role"]=="development" else plan["confirmation_toeplitz_seeds"][fid])
       count=int(row.get("transcript_event_count") or row.get("event_count") or 0); piece=partial_events[cursor:cursor+count];cursor+=count
       capped=row.get("status")=="aborted_resource_limit" and any(x.get("payload",{}).get("reason")=="complete_run_s" for x in piece)
       replay,events=(_cap(by[fid],p,seed,cb,mats) if capped else _one(by[fid],p,seed,verifier_runner,cb,mats,lambda:0.0))
       if not _same_row(row,replay) or piece!=events: raise ValueError(f"invalid partial replay at {index}")
      if cursor!=len(partial_events): raise ValueError("orphan invalid events")
      return {"verified":True,"run_status":"invalid_run","promoted":False,"worktree_diagnostic":live["git"]}
    manifest_keys={"run_id","run_status","plan_sha256","selected_policy_sha256","outcome_count","artifacts"}; report_keys={"run_id","run_status","promotion_gates","promoted","formal_run_manifest_sha256"}
    if set(manifest)!=manifest_keys or set(report)!=report_keys or manifest.get("run_id")!=RUN_ID or report.get("run_id")!=RUN_ID or manifest.get("run_status") not in {"completed","non_promoted_development"} or manifest.get("plan_sha256")!=_sha(plan_path.read_bytes()): raise ValueError("manifest")
    qc_cb,qc_mats=build_nbldpc_v2_codebook(); n1_cb,n1_mats=build_nonbinary_codebook_family(Q)
    if json.loads((output/"formal_codebook_manifest.json").read_text())!={"qc48":qc_cb,"control_n1":n1_cb} or verify_nbldpc_v2_codebook(qc_cb,qc_mats)["status"]!="ok" or verify_nonbinary_codebook_family(n1_cb,n1_mats)["status"]!="ok":raise ValueError("codebook")
    if json.loads((output/"formal_candidate_manifest.json").read_text())!=_candidate_manifest(): raise ValueError("candidate manifest")
    raw=(output/"formal_transcript.jsonl").read_bytes();ev=[json.loads(x) for x in raw.splitlines()]
    if b"".join(canonical_event(x) for x in ev)!=raw:raise ValueError("transcript")
    policy=json.loads((output/"formal_policy_manifest.json").read_text()); dev=policy.get("development_outcomes",{})
    if policy.get("policies")!=plan["policies"] or set(dev)!={x["policy_sha256"] for x in plan["policies"]}: raise ValueError("policy grid")
    by={x["frame_id"]:x for x in plan["frames"]}; replay_rows=[]; replay_events=[]
    for p in plan["policies"]:
      cb,mats=(n1_cb,n1_mats) if p["candidate_id"]==CANDIDATE_IDS[0] else (qc_cb,qc_mats)
      stored=dev[p["policy_sha256"]]
      if len(stored)!=48 or [x["frame_id"] for x in stored]!=plan["development_execution_order"]: raise ValueError("development order")
      for old,fid in zip(stored,plan["development_execution_order"]):
       row,events=_one(by[fid],p,plan["development_toeplitz_seeds"][p["policy_sha256"]+"|"+fid],verifier_runner,cb,mats,lambda:0.0)
       if not _same_row(old,row): raise ValueError("development replay")
       replay_rows.append(row); replay_events+=events
    selection=_select(dev,plan["policies"]);chosen=selection["selected_policy"];ready=chosen is not None and all(sum(x["status"]=="verified_success" for x in dev[chosen["policy_sha256"]] if float(x["stratum_p"])==p)>=22 for p in PS)
    selected_hash=chosen["policy_sha256"] if chosen else None
    if policy.get("selection")!=selection or policy.get("selected_policy_sha256")!=selected_hash or policy.get("readiness")!=ready or manifest.get("selected_policy_sha256")!=selected_hash: raise ValueError("selection")
    rows=_rows(output/"formal_frame_outcomes.csv")
    if len(rows)!=(1152+(64 if ready else 0)) or [x["frame_id"] for x in rows[:1152]]!=[f for p in plan["policies"] for f in plan["development_execution_order"]]: raise ValueError("outcome order")
    for old,new in zip(rows[:1152],replay_rows):
      if not _same_row(old,new): raise ValueError("development CSV")
    confirmation=rows[1152:]
    if ready:
      if [x["frame_id"] for x in confirmation]!=plan["confirmation_execution_order"]: raise ValueError("confirmation order")
      cb,mats=(n1_cb,n1_mats) if chosen["candidate_id"]==CANDIDATE_IDS[0] else (qc_cb,qc_mats)
      for old,fid in zip(confirmation,plan["confirmation_execution_order"]):
       frame_events=[x for x in ev if x["frame_key"]==fid and x["event_id"] in range(3)]
       capped=old["status"]=="aborted_resource_limit" and any(x.get("payload",{}).get("reason")=="complete_run_s" for x in frame_events)
       row,events=(_cap(by[fid],chosen,plan["confirmation_toeplitz_seeds"][fid],cb,mats) if capped else _one(by[fid],chosen,plan["confirmation_toeplitz_seeds"][fid],verifier_runner,cb,mats,lambda:0.0))
       if not _same_row(old,row) or frame_events!=events: raise ValueError("confirmation replay")
       replay_events+=events
    if ev!=replay_events: raise ValueError("transcript replay")
    typed=[{**x,"stratum_p":float(x["stratum_p"])} for x in confirmation]
    gates={f"p{int(p*100):02d}":{"requested":32,"denominator_included":sum(x["stratum_p"]==p for x in typed),"verified_success":sum(x["stratum_p"]==p and x["status"]=="verified_success" for x in typed),"prohibited_failures":sum(x["stratum_p"]==p and x["status"] in {"syndrome_inconsistent","decoder_error","codebook_invalid","invalid_run"} for x in typed)} for p in PS}
    for g in gates.values(): g["promoted"]=ready and g["denominator_included"]==32 and g["verified_success"]>=31 and g["prohibited_failures"]==0
    expected_status="completed" if ready else "non_promoted_development"
    if manifest.get("run_status")!=expected_status or report.get("run_status")!=expected_status or report.get("promotion_gates")!=gates or report.get("promoted")!=(ready and all(x["promoted"] for x in gates.values())): raise ValueError("report gates")
    if manifest.get("outcome_count")!=len(rows): raise ValueError("outcome count")
    return {"verified":True,"run_status":manifest["run_status"],"promoted":report["promoted"],"worktree_diagnostic":live["git"]}
