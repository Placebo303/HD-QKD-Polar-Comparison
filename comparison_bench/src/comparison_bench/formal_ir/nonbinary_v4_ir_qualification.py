"""Bounded, no-overwrite formal qualification for NBLDPC v4 IR.

The public API deliberately separates plan creation, one execution and one
read-only verifier.  Test paths must supply a fake runner explicitly.
"""
from __future__ import annotations

import csv, hashlib, json, math, platform, secrets, subprocess
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from . import nonbinary_v4_ir as core
from .nonbinary_field import GF2mField
from .nonbinary_qspa import nonbinary_syndrome, symbols_to_msb_bits
from .shared import canonical_event, locked_seed_bits, materialize_seed_record, toeplitz_tag, transcript_summary

RUN_ID = "20260731_v4_nbldpc_ir_synthetic"; Q=N=1024; N=64; PS=(.20,.30); SEED_BITS=703
ROOTS = {("development",.20):202607510000,("development",.30):202607520000,("confirmation",.20):202607530000,("confirmation",.30):202607540000}
CAPS={"workers":1,"q":Q,"n":N,"checks_max":48,"row_weight":8,"stage_iterations":12,"total_iterations":24,"decoder_stages":2,"verification_attempts":2,"dense_bytes_max":24*1024*1024}
ARTIFACTS=("pre_run_plan.json","formal_frame_outcomes.csv","formal_transcript.jsonl","formal_run_manifest.json","formal_codebook_manifest.json","formal_candidate_manifest.json","formal_policy_manifest.json","formal_qualification_report.json")
OFFICIAL_OUTPUT_ROOT=Path("comparison_bench/outputs_comparison/formal_ir_methods")/RUN_ID
_SRC=("comparison_bench/src/comparison_bench/formal_ir/nonbinary_v4_ir.py","comparison_bench/src/comparison_bench/formal_ir/nonbinary_v4_ir_qualification.py","comparison_bench/src/comparison_bench/cli/run_formal_nonbinary_v4_ir_qualification.py","comparison_bench/src/comparison_bench/formal_ir/nonbinary_v3.py","comparison_bench/src/comparison_bench/formal_ir/nonbinary_qspa.py","comparison_bench/src/comparison_bench/formal_ir/nonbinary_field.py","comparison_bench/src/comparison_bench/formal_ir/nonbinary_codebook.py","comparison_bench/src/comparison_bench/formal_ir/shared.py")
_CONTRACT="openspec/changes/formal-nonbinary-ldpc-v4-incremental-redundancy/specs/formal-nonbinary-ldpc-v4-ir/spec.md"
_FORBIDDEN=("residual","posterior","message","cycle","alice","truth","error_location","decision_hash","decoded_symbols")

def _compact(x): return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
def _sha(x): return hashlib.sha256(x).hexdigest()
def _root(): return Path(__file__).resolve().parents[4]
def _put(p,x):
    with p.open("xb") as f:f.write(json.dumps(x,sort_keys=True,indent=2,ensure_ascii=True,allow_nan=False).encode()+b"\n")
def _csv(p,rows):
    with p.open("x",newline="",encoding="utf8") as f:
        w=csv.DictWriter(f,fieldnames=sorted({k for r in rows for k in r}) or ["status"]);w.writeheader();w.writerows(rows)
def _rows(p):
    with p.open(newline="",encoding="utf8") as f:return list(csv.DictReader(f))
def _output(output,*,_test_only):
    official=(_root()/OFFICIAL_OUTPUT_ROOT).resolve(); chosen=official if output is None else Path(output).resolve()
    if chosen!=official and not _test_only:raise ValueError("v4 requires official output root")
    return chosen
def _frame(p,role,index):
    rng=np.random.Generator(np.random.PCG64(ROOTS[role,p]+index)); alice=rng.integers(0,Q,N,dtype=np.int64); mask=rng.random(N)<p; error=rng.integers(1,Q,N,dtype=np.int64); bob=alice.copy();bob[mask]^=error[mask]
    return {"frame_id":f"{core.METHOD}_q1024_p{int(p*100):02d}_{role}_{index:03d}","p":p,"role":role,"index":index,"seed":ROOTS[role,p]+index,"alice":alice.tolist(),"bob":bob.tolist(),"array_sha256":_sha(alice.astype("<i8").tobytes()+bob.astype("<i8").tobytes()),"atomic_keys":[f"{core.METHOD}|{role}|{p}|{index}|{j}" for j in range(N)]}
def _policy():
    out=[]
    for name in core.POLICIES:
        body={"policy_id":name,"decoder":"row_layered_fft_qspa","lambda":.75,"max_stage_iterations":12,"strata":[core.policy_spec(name,p) for p in PS]}
        out.append(dict(body,policy_sha256=_sha(_compact(body))))
    return out
def _provenance():
    root=_root(); cb,_=core.codebook(); candidate={"method":core.METHOD,"policies":list(core.POLICIES),"v3_codebook_manifest_id":cb["manifest_id"]}
    try:commit=subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True,stderr=subprocess.DEVNULL).strip()
    except (OSError,subprocess.SubprocessError):commit="unavailable"
    return {"source_sha256":{p:_sha((root/p).read_bytes()) for p in _SRC},"contract_sha256":_sha((root/_CONTRACT).read_bytes()),"candidate_sha256":_sha(_compact(candidate)),"codebook_sha256":cb["canonical_sha256"],"environment":{"python":platform.python_version(),"numpy":np.__version__},"git_commit":commit}
def _excluded(path, exclude):
    if exclude is None:return False
    target=Path(exclude).resolve(); current=Path(path).resolve()
    # A plan file excludes itself only; a package directory excludes every
    # descendant, including its plan and later policy manifest.
    return current==target if target.suffix else current.is_relative_to(target)
def _prior_seed_ids(exclude=None):
    found=set(); base=_root()/"comparison_bench/outputs_comparison/formal_ir_methods"
    if not base.exists():return found
    for path in base.rglob("*.json"):
        if _excluded(path,exclude):continue
        try: text=path.read_text(encoding="utf8")
        except OSError:continue
        import re;found.update(re.findall(r'"seed_id"\s*:\s*"([0-9a-f]{64})"',text))
    return found
def _prior_identities(exclude=None):
    found={"roots":set(),"frame_ids":set(),"array_sha256":set(),"atomic_keys":set()};base=_root()/"comparison_bench/outputs_comparison/formal_ir_methods"
    if not base.exists():return found
    for path in base.rglob("pre_run_plan.json"):
        if _excluded(path,exclude):continue
        try:doc=json.loads(path.read_text(encoding="utf8"))
        except (OSError,ValueError):continue
        roots=doc.get("roots",{});found["roots"].update(map(str,roots.values()))
        for frame in doc.get("frames",[]):
            if isinstance(frame,dict):
                found["frame_ids"].add(str(frame.get("frame_id","")));found["array_sha256"].add(str(frame.get("array_sha256","")));found["atomic_keys"].update(map(str,frame.get("atomic_keys",[])))
    for path in base.rglob("formal_policy_manifest.json"):
        if _excluded(path,exclude):continue
        try: doc=json.loads(path.read_text(encoding="utf8")); frames=doc.get("confirmation_material",{}).get("frames",[])
        except (OSError,ValueError,AttributeError): continue
        for frame in frames:
            if isinstance(frame,dict):
                found["frame_ids"].add(str(frame.get("frame_id","")));found["array_sha256"].add(str(frame.get("array_sha256","")));found["atomic_keys"].update(map(str,frame.get("atomic_keys",[])))
    return found
def _identity_overlap(frames, *, exclude=None):
    old=_prior_identities(exclude); roots={str(x) for x in ROOTS.values()};now={"roots":roots,"frame_ids":{str(x["frame_id"]) for x in frames},"array_sha256":{str(x["array_sha256"]) for x in frames},"atomic_keys":{str(k) for x in frames for k in x["atomic_keys"]}}
    return {key:sorted(now[key]&old[key]) for key in now}
def expected_plan():
    frames=[_frame(p,"development",i) for p in PS for i in range(64)]; policies=_policy(); seeds={}
    for policy in policies:
        for frame in frames:
            stages=(0,) if policy["policy_id"]=="nbldpc_v4_control" else (0,1)
            for stage in stages:seeds[f"{policy['policy_sha256']}|{frame['frame_id']}|{stage}"]=materialize_seed_record(SEED_BITS)
    return {"canonical_schema":"NBLDPCQ4IR","run_id":RUN_ID,"method":core.METHOD,"q":Q,"n":N,"roots":{f"{r}|{p}":v for (r,p),v in ROOTS.items()},"caps":CAPS,"frames":frames,"identity_overlap":_identity_overlap(frames),"policies":policies,"development_toeplitz_seeds":seeds,"confirmation_contract":{"frames_per_stratum":128,"seed_bits":SEED_BITS,"materialize_only_after_readiness":True},"provenance":_provenance()}
def _validate_plan(plan, *, plan_path=None):
    if plan.get("canonical_schema")!="NBLDPCQ4IR" or plan.get("run_id")!=RUN_ID or plan.get("method")!=core.METHOD:raise ValueError("plan identity")
    if plan.get("roots")!={f"{r}|{p}":v for (r,p),v in ROOTS.items()} or plan.get("caps")!=CAPS or plan.get("policies")!=_policy() or plan.get("provenance")!=_provenance():raise ValueError("plan contract/provenance")
    frames=plan.get("frames"); expected=[_frame(p,"development",i) for p in PS for i in range(64)]
    if frames!=expected or any(x.get("role")!="development" for x in frames):raise ValueError("confirmation leaked into plan")
    if plan.get("confirmation_contract")!={"frames_per_stratum":128,"seed_bits":SEED_BITS,"materialize_only_after_readiness":True}:raise ValueError("confirmation contract")
    if plan.get("identity_overlap")!=_identity_overlap(frames,exclude=plan_path) or any(plan["identity_overlap"].values()):raise ValueError("identity freshness")
    seeds=plan.get("development_toeplitz_seeds",{}); expected_keys=set()
    for policy in _policy():
        for frame in frames:
            for stage in ((0,) if policy["policy_id"]=="nbldpc_v4_control" else (0,1)):expected_keys.add(f"{policy['policy_sha256']}|{frame['frame_id']}|{stage}")
    if set(seeds)!=expected_keys:raise ValueError("development seed binding")
    ids=[]
    for record in seeds.values():locked_seed_bits(record,SEED_BITS);ids.append(record["seed_id"])
    if len(ids)!=len(set(ids)) or set(ids)&_prior_seed_ids(exclude=plan_path):raise ValueError("seed freshness")
    return True
def create_plan(output=None,*,_test_only=False):
    out=_output(output,_test_only=_test_only)
    if out.exists():raise FileExistsError(out)
    plan=expected_plan();_validate_plan(plan);out.mkdir(parents=True);_put(out/"pre_run_plan.json",plan);return plan

def _events(frame, policy, stages, decisions, seeds, syndromes, tags):
    events=[]; eid=0
    def add(kind,direction,parent,key=0,public=0,payload=None):
        nonlocal eid;events.append({"event_id":eid,"frame_key":frame["frame_id"],"method":core.METHOD,"event_type":kind,"direction":direction,"parent_event_id":parent,"pass_id":eid,"plane_id":"q1024","key_dependent_bits":key,"public_control_bits":public,"payload":payload or {"reason":kind}});eid+=1
    for stage, result in enumerate(stages):
        checks=result["check_count"]; disclosed=checks*10 if stage==0 else 80
        payload={"syndrome":list(syndromes[stage])}
        add("SYNDROME_INITIAL" if stage==0 else "SYNDROME_EXTENSION","alice_to_bob",eid-1,disclosed,0,payload)
        add("DECODER_STAGE1" if stage==0 else "DECODER_STAGE2","bob_local",eid-1,0,0,{"reason":result["status"]})
        if result.get("verification_invoked"):
            seed=seeds[stage];add("VERIFICATION_TAG_STAGE1" if stage==0 else "VERIFICATION_TAG_STAGE2","alice_to_bob",eid-1,64,SEED_BITS,{"tag":tags[stage].hex(),"seed_id":seed["seed_id"],"seed_bit_length":SEED_BITS})
        add("STAGE_DECISION_STAGE1" if stage==0 else "STAGE_DECISION_STAGE2","control",eid-1,0,2,{"reason":decisions[stage]})
    return events
def _tag(symbols, seed):
    return toeplitz_tag(symbols_to_msb_bits(symbols,Q),locked_seed_bits(seed,SEED_BITS))

def _result(frame,policy,runner,cb,mats,seeds):
    spec=next(x for x in policy["strata"] if x["p"]==frame["p"]); initial=spec["initial_checks"];final=spec["final_checks"]
    full=nonbinary_syndrome(mats[final],frame["alice"],GF2mField.create(Q)); syn0=full[:initial]; suffix=full[initial:]
    started=core.start(policy["policy_id"],frame["bob"],syn0,cb,p=frame["p"],stage_runner=runner)
    if isinstance(started,dict): state=None; raw=started
    else: state,raw,_=started
    stages=[]; tags=[]; syndromes=[syn0]
    status=raw.get("status","decoder_error"); invoked=status=="syndrome_consistent"
    if invoked:
        alice_tag=_tag(frame["alice"],seeds[0]); bob_tag=_tag(raw["decoded_symbols"],seeds[0]); verified=alice_tag==bob_tag; tags.append(alice_tag)
    else: verified=False; tags.append(b"")
    first={"check_count":initial,"status":"verified_success" if invoked and verified else "verify_failed" if invoked else status,"iterations":int(raw.get("iterations",0)),"verification_invoked":invoked}
    stages.append(first); extend=policy["policy_id"]!="nbldpc_v4_control" and first["status"] in {"decode_failed","verify_failed"}
    decisions=["01" if extend else "00" if first["status"]=="verified_success" else "10"]
    if extend:
        next_state=core.extend(state,suffix,mats,mode="warm" if policy["policy_id"].endswith("warm") else "restart") if state is not None else {"status":"decoder_error"}
        raw2=next_state if isinstance(next_state,dict) else core.run_stage2(next_state,mats,stage_runner=runner)
        status2=raw2.get("status","decoder_error"); invoked2=status2=="syndrome_consistent"
        if invoked2:
            alice_tag=_tag(frame["alice"],seeds[1]); bob_tag=_tag(raw2["decoded_symbols"],seeds[1]); verified2=alice_tag==bob_tag;tags.append(alice_tag)
        else: verified2=False;tags.append(b"")
        stages.append({"check_count":final,"status":"verified_success" if invoked2 and verified2 else "verify_failed" if invoked2 else status2,"iterations":int(raw2.get("iterations",0)),"verification_invoked":invoked2});decisions.append("00" if stages[-1]["status"]=="verified_success" else "10")
        syndromes.append(suffix)
    final_status=stages[-1]["status"];events=_events(frame,policy,stages,decisions,seeds,syndromes,tags);summary=transcript_summary(events)
    return {"frame_id":frame["frame_id"],"stratum_p":frame["p"],"qualification_role":frame["role"],"policy_sha256":policy["policy_sha256"],"policy_id":policy["policy_id"],"status":final_status,"denominator_included":True,"stage1_iterations":stages[0]["iterations"],"stage2_iterations":stages[1]["iterations"] if len(stages)>1 else 0,"initial_prefix":initial,"final_prefix":stages[-1]["check_count"],"extension_used":extend,"verification_attempts":sum(x["verification_invoked"] for x in stages),"outcome_epsilon_ec":2.0**-64 if final_status=="verified_success" else None,"protocol_epsilon_ec_bound":2.0**(-64 if policy["policy_id"]=="nbldpc_v4_control" else -63),"array_sha256":frame["array_sha256"],"transcript_event_count":len(events),**summary},events
def _select(rows,policies):
    ranked=[]
    for policy in policies:
        rs=[x for x in rows if x["policy_sha256"]==policy["policy_sha256"]]; expected=[f"{core.METHOD}_q1024_p{int(p*100):02d}_development_{i:03d}" for p in PS for i in range(64)];counts=[sum(x["status"]=="verified_success" and float(x["stratum_p"])==p for x in rs) for p in PS]
        if len(rs)!=128 or [x.get("frame_id") for x in rs]!=expected or any(str(x.get("denominator_included")).lower()!="true" or x["status"] not in {"verified_success","verify_failed","decode_failed","aborted_resource_limit"} for x in rs) or any(sum(float(x["stratum_p"])==p for x in rs)!=64 for p in PS):continue
        ranked.append((-min(counts),-sum(counts),sum(int(x["key_dependent_disclosure_bits_total"]) for x in rs),sum(int(x["public_control_bits_total"]) for x in rs),sum(int(x["transcript_event_count"]) for x in rs),sum(int(x["stage1_iterations"])+int(x["stage2_iterations"]) for x in rs),policy["policy_sha256"],policy))
    if not ranked:return {"selected_policy":None,"selected_policy_sha256":None,"selection_key":None,"reason":"no_eligible_policy"}
    best=min(ranked);return {"selected_policy":best[-1],"selected_policy_sha256":best[-1]["policy_sha256"],"selection_key":list(best[:-1]),"reason":"development_rank"}
def production_runner(state, matrices, stage):
    """Production adapter: the live v4 state machine is the decoder."""
    return core._run(state, matrices)
def _artifact_hashes(out):
    return {name:_sha((out/name).read_bytes()) for name in ARTIFACTS
            if name not in {"formal_run_manifest.json","formal_qualification_report.json"}
            and (out/name).exists()}

def _candidate_manifest(cb=None):
    cb = core.codebook()[0] if cb is None else cb
    return {"method":core.METHOD,"policies":list(core.POLICIES),
            "v3_codebook_manifest_id":cb["manifest_id"]}

def _write_events(path, events):
    with path.open("xb") as handle:
        for event in events:
            handle.write(canonical_event(event))

def _finalize_invalid(out, exc, state):
    """Atomically complete the eight-artifact invalid package.

    Completed rows/events are evidence, not disposable work.  The sentinel
    documents are deliberately narrow when no deterministic candidate state was
    reached, so a rehashed empty package cannot impersonate a partial replay.
    """
    rows, events = state["rows"], state["events"]
    if not (out/"formal_frame_outcomes.csv").exists(): _csv(out/"formal_frame_outcomes.csv", rows)
    if not (out/"formal_transcript.jsonl").exists(): _write_events(out/"formal_transcript.jsonl", events)
    cb = state.get("codebook")
    policy = state.get("policy")
    if policy is None and cb is not None and len(rows)==384:
        plan=state["plan"]; selection=_select(rows,plan["policies"])
        ready=bool(selection["selected_policy"] and all(sum(x["status"]=="verified_success" and float(x["stratum_p"])==p and x["policy_sha256"]==selection["selected_policy_sha256"] for x in rows)>=63 for p in PS))
        policy={"policies":plan["policies"],"selection":selection,"readiness":ready}
    if not (out/"formal_codebook_manifest.json").exists():
        _put(out/"formal_codebook_manifest.json", cb if cb is not None else {"invalid":True})
    if not (out/"formal_candidate_manifest.json").exists():
        _put(out/"formal_candidate_manifest.json", _candidate_manifest(cb) if cb is not None else {"invalid":True})
    if not (out/"formal_policy_manifest.json").exists():
        _put(out/"formal_policy_manifest.json", policy if policy is not None else {"invalid":True})
    manifest={"run_id":RUN_ID,"run_status":"invalid_run",
              "reason":f"{type(exc).__name__}: {exc}","outcome_count":len(rows),
              "artifacts":_artifact_hashes(out)}
    _put(out/"formal_run_manifest.json",manifest)
    _put(out/"formal_qualification_report.json",{
        "run_id":RUN_ID,"run_status":"invalid_run","readiness":False,
        "promoted":False,
        "formal_run_manifest_sha256":_sha((out/"formal_run_manifest.json").read_bytes())})

def _gates(rows):
    allowed={"verified_success","verify_failed","decode_failed","aborted_resource_limit"}
    return {str(p):{"requested":128,
        "denominator_included":sum(x["qualification_role"]=="confirmation" and float(x["stratum_p"])==p for x in rows),
        "verified_success":sum(x["qualification_role"]=="confirmation" and float(x["stratum_p"])==p and x["status"]=="verified_success" for x in rows),
        "prohibited_failures":sum(x["qualification_role"]=="confirmation" and float(x["stratum_p"])==p and x["status"] not in allowed for x in rows)} for p in PS}

def _write_normal(out, rows, events, cb, policy_doc, ready):
    _put(out/"formal_codebook_manifest.json",cb)
    _put(out/"formal_candidate_manifest.json",_candidate_manifest(cb))
    _put(out/"formal_policy_manifest.json",policy_doc)
    _csv(out/"formal_frame_outcomes.csv",rows); _write_events(out/"formal_transcript.jsonl",events)
    run_status="completed" if ready else "non_promoted_development"; gates=_gates(rows)
    promoted=ready and all(x["denominator_included"]==128 and x["verified_success"]==128 and x["prohibited_failures"]==0 for x in gates.values())
    _put(out/"formal_run_manifest.json",{"run_id":RUN_ID,"run_status":run_status,"outcome_count":len(rows),"artifacts":_artifact_hashes(out)})
    _put(out/"formal_qualification_report.json",{"run_id":RUN_ID,"run_status":run_status,"readiness":ready,"promotion_gates":gates,"promoted":promoted,"formal_run_manifest_sha256":_sha((out/"formal_run_manifest.json").read_bytes())})
    return {"run_status":run_status,"readiness":ready,"promoted":promoted}

def run(output=None,*,runner:Callable|None=None,_test_only=False,
        fatal_hook:Callable[[int],None]|None=None):
    if not _test_only and runner is not None:raise ValueError("production run does not accept runner")
    if runner is None:
        if _test_only:raise ValueError("test-only run requires explicit runner")
        runner=production_runner
    out=_output(output,_test_only=_test_only)
    if {x.name for x in out.iterdir()}!={"pre_run_plan.json"}:raise ValueError("run requires plan-only directory")
    plan_path=out/"pre_run_plan.json";plan=json.loads(plan_path.read_text());_validate_plan(plan,plan_path=plan_path)
    state={"rows":[],"events":[],"codebook":None,"policy":None,"plan":plan}
    try:
      cb,mats=core.codebook(); state["codebook"]=cb
      for policy in plan["policies"]:
        for frame in plan["frames"]:
            seed0=plan["development_toeplitz_seeds"][f"{policy['policy_sha256']}|{frame['frame_id']}|0"]; seed1=plan["development_toeplitz_seeds"].get(f"{policy['policy_sha256']}|{frame['frame_id']}|1",seed0)
            row,event=_result(frame,policy,runner,cb,mats,(seed0,seed1));state["rows"].append(row);state["events"]+=event
            if fatal_hook is not None:fatal_hook(len(state["rows"]))
      rows,events=state["rows"],state["events"]
      selection=_select(rows,plan["policies"]);ready=bool(selection["selected_policy"] and all(sum(x["status"]=="verified_success" and float(x["stratum_p"])==p and x["policy_sha256"]==selection["selected_policy_sha256"] for x in rows)>=63 for p in PS))
      policy_doc={"policies":plan["policies"],"selection":selection,"readiness":ready};state["policy"]=policy_doc
      if ready:
        # Materialize the complete selected lane before its first decode.  This
        # occurs only after development selection and uses additive seed
        # records; it is never present in a plan-only directory.
        selected=selection["selected_policy"]; used={x["seed_id"] for x in plan["development_toeplitz_seeds"].values()}|_prior_seed_ids(exclude=out)
        material={"frames":[],"toeplitz_seeds":{},"frozen_before_decode":True}
        for p in PS:
            for index in range(128):
                frame=_frame(p,"confirmation",index);material["frames"].append(frame)
                for stage in ((0,) if selected["policy_id"]=="nbldpc_v4_control" else (0,1)):
                    seed=materialize_seed_record(SEED_BITS)
                    if seed["seed_id"] in used:raise RuntimeError("confirmation seed overlap")
                    used.add(seed["seed_id"]);material["toeplitz_seeds"][f"{selected['policy_sha256']}|{frame['frame_id']}|{stage}"]=seed
        # Evidence binds identity and seed records, never Alice/Bob arrays.
        policy_doc["confirmation_material"]={"frames":[{k:v for k,v in frame.items() if k not in {"alice","bob"}} for frame in material["frames"]],"toeplitz_seeds":material["toeplitz_seeds"],"frozen_before_decode":True}
        # Freeze and validate the complete material before the first
        # confirmation decoder call.  Any collision is an invalid package with
        # exactly the completed development evidence and zero confirmation rows.
        _confirmation_expected(selected,policy_doc["confirmation_material"],exclude=out,
            development_ids=[x["seed_id"] for x in plan["development_toeplitz_seeds"].values()])
        for frame in material["frames"]:
            seed0=material["toeplitz_seeds"][f"{selected['policy_sha256']}|{frame['frame_id']}|0"]
            seed1=material["toeplitz_seeds"].get(f"{selected['policy_sha256']}|{frame['frame_id']}|1",seed0)
            row,event=_result(frame,selected,runner,cb,mats,(seed0,seed1));rows.append(row);events+=event
            if fatal_hook is not None:fatal_hook(len(rows))
      return _write_normal(out,rows,events,cb,policy_doc,ready)
    except Exception as exc:
      _finalize_invalid(out,exc,state)
      raise
def _reject_diagnostics(value):
    if isinstance(value,Mapping):
        for key,item in value.items():
            if any(token in str(key).lower() for token in _FORBIDDEN):raise ValueError("forbidden diagnostic")
            _reject_diagnostics(item)
    elif isinstance(value,list):
        for item in value:_reject_diagnostics(item)
def _same(expected, actual):
    right=dict(actual)
    if right.get("outcome_epsilon_ec")=="":right["outcome_epsilon_ec"]=None
    return {k:str(v) for k,v in expected.items()}=={k:str(v) for k,v in right.items()}

def _expected_development(plan):
    return [(frame,policy,(plan["development_toeplitz_seeds"][f"{policy['policy_sha256']}|{frame['frame_id']}|0"],
                            plan["development_toeplitz_seeds"].get(f"{policy['policy_sha256']}|{frame['frame_id']}|1",plan["development_toeplitz_seeds"][f"{policy['policy_sha256']}|{frame['frame_id']}|0"])))
            for policy in plan["policies"] for frame in plan["frames"]]

def _confirmation_expected(policy, material, *, exclude, development_ids=()):
    if set(material)!={"frames","toeplitz_seeds","frozen_before_decode"} or material.get("frozen_before_decode") is not True:raise ValueError("confirmation material shape")
    public=material["frames"]; seeds=material["toeplitz_seeds"]
    if len(public)!=256:raise ValueError("confirmation frozen count")
    frames=[]; ids=[]; wanted={}
    for p in PS:
        for index in range(128):
            expected=_frame(p,"confirmation",index); shown={k:v for k,v in expected.items() if k not in {"alice","bob"}}
            actual=public[len(frames)]
            if actual!=shown:raise ValueError("confirmation identity replay")
            frames.append(expected)
            for stage in ((0,) if policy["policy_id"]=="nbldpc_v4_control" else (0,1)):
                key=f"{policy['policy_sha256']}|{expected['frame_id']}|{stage}"; wanted[key]=None
    if set(seeds)!=set(wanted):raise ValueError("confirmation seed keys")
    for key,record in seeds.items():locked_seed_bits(record,SEED_BITS);ids.append(record["seed_id"])
    if len(ids)!=len(set(ids)) or set(ids)&set(development_ids) or set(ids)&_prior_seed_ids(exclude=exclude):raise ValueError("confirmation seed isolation")
    if any(_identity_overlap(frames,exclude=exclude).values()):raise ValueError("confirmation identity isolation")
    return [(frame,policy,(seeds[f"{policy['policy_sha256']}|{frame['frame_id']}|0"],seeds.get(f"{policy['policy_sha256']}|{frame['frame_id']}|1"))) for frame in frames]

def _verify_invalid(out, plan, verifier_runner):
    manifest=json.loads((out/"formal_run_manifest.json").read_text()); report=json.loads((out/"formal_qualification_report.json").read_text())
    if {x.name for x in out.iterdir()}!=set(ARTIFACTS) or set(manifest)!={"run_id","run_status","reason","outcome_count","artifacts"} or set(report)!={"run_id","run_status","readiness","promoted","formal_run_manifest_sha256"}:
        raise ValueError("invalid package shape")
    if manifest.get("run_id")!=RUN_ID or manifest.get("run_status")!="invalid_run" or not isinstance(manifest.get("reason"),str) or not manifest["reason"] or manifest.get("artifacts")!=_artifact_hashes(out) or report!={"run_id":RUN_ID,"run_status":"invalid_run","readiness":False,"promoted":False,"formal_run_manifest_sha256":_sha((out/"formal_run_manifest.json").read_bytes())}:
        raise ValueError("invalid package identity")
    rows=_rows(out/"formal_frame_outcomes.csv"); events=[json.loads(line) for line in (out/"formal_transcript.jsonl").read_bytes().splitlines()]
    if b"".join(canonical_event(event) for event in events)!=(out/"formal_transcript.jsonl").read_bytes() or manifest["outcome_count"]!=len(rows):raise ValueError("invalid transcript")
    cb=json.loads((out/"formal_codebook_manifest.json").read_text()); candidate=json.loads((out/"formal_candidate_manifest.json").read_text()); policy_doc=json.loads((out/"formal_policy_manifest.json").read_text())
    if not rows:
        if cb!={"invalid":True} or candidate!={"invalid":True} or policy_doc!={"invalid":True} or events:raise ValueError("invalid empty sentinel")
        return {"verified":True,"run_status":"invalid_run","promoted":False}
    if cb!=core.codebook()[0] or candidate!=_candidate_manifest(cb):raise ValueError("invalid partial provenance")
    if len(rows)<384:
        if policy_doc!={"invalid":True}:raise ValueError("invalid partial state")
    elif not isinstance(policy_doc,dict) or policy_doc.get("policies")!=plan["policies"]:
        raise ValueError("invalid partial provenance")
    expected=_expected_development(plan)
    # Confirmation is legal only after a complete, selected development lane.
    if len(rows)>len(expected):
        selection=_select(rows[:len(expected)],plan["policies"])
        material=policy_doc.get("confirmation_material",{})
        selected=selection.get("selected_policy")
        if policy_doc.get("selection")!=selection or selected is None:raise ValueError("invalid partial confirmation")
        expected+=_confirmation_expected(selected,material,exclude=out,development_ids=[x["seed_id"] for x in plan["development_toeplitz_seeds"].values()])
    if len(rows)>len(expected):raise ValueError("invalid partial row count")
    if [row.get("frame_id") for row in rows]!=[frame["frame_id"] for frame,_,_ in expected[:len(rows)]] or [row.get("policy_sha256") for row in rows]!=[policy["policy_sha256"] for _,policy,_ in expected[:len(rows)]]:raise ValueError("invalid partial order")
    cursor=0; cb2,mats=core.codebook()
    for index,(actual,(frame,policy,seeds)) in enumerate(zip(rows,expected)):
        replay, row_events=_result(frame,policy,verifier_runner,cb2,mats,seeds); count=int(actual.get("transcript_event_count",0));piece=events[cursor:cursor+count];cursor+=count
        if not _same(replay,actual) or piece!=row_events:raise ValueError(f"invalid partial replay at {index}")
    if cursor!=len(events):raise ValueError("orphan invalid events")
    return {"verified":True,"run_status":"invalid_run","promoted":False}
def verify(output=None,*,verifier_runner:Callable|None=None,_test_only=False):
    if not _test_only and verifier_runner is not None:raise ValueError("production verify does not accept verifier_runner")
    out=_output(output,_test_only=_test_only);plan_path=out/"pre_run_plan.json";plan=json.loads(plan_path.read_text());_validate_plan(plan,plan_path=plan_path)
    if verifier_runner is None and _test_only:raise ValueError("test-only verify requires explicit verifier_runner")
    if {x.name for x in out.iterdir()}=={"pre_run_plan.json"}:return {"verified":True,"plan_only":True,"run_status":"planned","promoted":False}
    manifest=json.loads((out/"formal_run_manifest.json").read_text()) if (out/"formal_run_manifest.json").exists() else {}
    if verifier_runner is None:verifier_runner=production_runner
    if manifest.get("run_status")=="invalid_run":return _verify_invalid(out,plan,verifier_runner)
    if {x.name for x in out.iterdir()}!=set(ARTIFACTS):raise ValueError("artifact set")
    report=json.loads((out/"formal_qualification_report.json").read_text());rows=_rows(out/"formal_frame_outcomes.csv")
    if set(manifest)!={"run_id","run_status","outcome_count","artifacts"} or set(report)!={"run_id","run_status","readiness","promotion_gates","promoted","formal_run_manifest_sha256"}:raise ValueError("normal package schema")
    if manifest.get("run_id")!=RUN_ID or report.get("run_id")!=RUN_ID or manifest.get("artifacts")!=_artifact_hashes(out) or report.get("formal_run_manifest_sha256")!=_sha((out/"formal_run_manifest.json").read_bytes()):raise ValueError("artifact DAG")
    # The reconstructed v3 codebook manifest necessarily contains its frozen
    # structural `cycle_count` proof.  It is not a transient decoder
    # diagnostic; all v4 outcome/transcript/control artifacts are checked.
    for path in (out/"formal_frame_outcomes.csv",out/"formal_transcript.jsonl",out/"formal_policy_manifest.json",out/"formal_candidate_manifest.json"):
        if path.suffix==".csv":_reject_diagnostics(rows)
        elif path.suffix==".jsonl":
            for line in path.read_bytes().splitlines():_reject_diagnostics(json.loads(line))
        else:_reject_diagnostics(json.loads(path.read_text()))
    if json.loads((out/"formal_codebook_manifest.json").read_text())!=core.codebook()[0] or json.loads((out/"formal_candidate_manifest.json").read_text())!=_candidate_manifest():raise ValueError("candidate/codebook replay")
    policy_doc=json.loads((out/"formal_policy_manifest.json").read_text()); dev=[x for x in rows if x["qualification_role"]=="development"]
    confirm=[x for x in rows if x["qualification_role"]=="confirmation"]
    if manifest.get("outcome_count")!=len(rows) or len(dev)!=384 or (manifest["run_status"]=="non_promoted_development" and confirm):raise ValueError("development count")
    if manifest["run_status"]=="completed" and len(confirm)!=256:raise ValueError("confirmation count")
    # Strict replay uses source reconstruction, never private arrays serialized
    # in the manifest.  Runner is deliberately invoked for every stage.
    expected=_expected_development(plan)
    if confirm:
        selected=policy_doc.get("selection",{}).get("selected_policy")
        material=policy_doc.get("confirmation_material",{})
        if selected not in plan["policies"]:raise ValueError("confirmation material")
        expected+=_confirmation_expected(selected,material,exclude=out,development_ids=[x["seed_id"] for x in plan["development_toeplitz_seeds"].values()])
    if len(rows)!=len(expected):raise ValueError("row count")
    parsed=[]
    for line in (out/"formal_transcript.jsonl").read_bytes().splitlines():parsed.append(json.loads(line))
    cursor=0
    for index,(actual,(frame,policy,seeds)) in enumerate(zip(rows,expected)):
        replay, events=_result(frame,policy,verifier_runner,core.codebook()[0],core.codebook()[1],seeds)
        count=int(actual.get("transcript_event_count",0)); piece=parsed[cursor:cursor+count];cursor+=count
        if not _same(replay,actual) or piece!=events:raise ValueError(f"semantic replay at {index}")
    if cursor!=len(parsed):raise ValueError("orphan transcript events")
    replay_selection=_select(dev,plan["policies"])
    if policy_doc.get("selection")!=replay_selection:raise ValueError("selection replay")
    readiness=bool(replay_selection["selected_policy"] and all(sum(x["status"]=="verified_success" and float(x["stratum_p"])==p and x["policy_sha256"]==replay_selection["selected_policy_sha256"] for x in dev)>=63 for p in PS))
    if bool(policy_doc.get("readiness"))!=readiness:raise ValueError("readiness replay")
    expected_status="completed" if readiness else "non_promoted_development"
    if manifest.get("run_status")!=expected_status or report.get("run_status")!=expected_status or (not readiness and confirm):raise ValueError("normal run status")
    gates={str(p):{"requested":128,"denominator_included":sum(x["qualification_role"]=="confirmation" and float(x["stratum_p"])==p for x in rows),"verified_success":sum(x["qualification_role"]=="confirmation" and float(x["stratum_p"])==p and x["status"]=="verified_success" for x in rows),"prohibited_failures":sum(x["qualification_role"]=="confirmation" and float(x["stratum_p"])==p and x["status"] not in {"verified_success","verify_failed","decode_failed","aborted_resource_limit"} for x in rows)} for p in PS}
    promoted=readiness and all(x["denominator_included"]==128 and x["verified_success"]==128 and x["prohibited_failures"]==0 for x in gates.values())
    if report.get("promotion_gates")!=gates or bool(report.get("promoted"))!=promoted:raise ValueError("promotion gates")
    return {"verified":True,"run_status":manifest["run_status"],"promoted":bool(report["promoted"])}
