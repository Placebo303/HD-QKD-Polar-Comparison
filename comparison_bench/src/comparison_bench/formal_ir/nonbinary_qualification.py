"""Frozen N3 synthetic qualification lane for ``nbldpc_formal_v1``.

This is deliberately independent of the older binary formal runners.  It is
small enough to audit: the plan contains all generated frames and locked seeds.
Plan-only verification makes no decoder calls; completed-package verification
replays the deterministic decoder to reject coherent outcome tampering.
"""
from __future__ import annotations

import csv, hashlib, json, os, platform, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from .nonbinary_codebook import build_nonbinary_codebook_family, verify_nonbinary_codebook_family
from .nonbinary_field import GF2mField, get_field_spec
from .nonbinary_qspa import (decode_nonbinary_fft_qspa, nonbinary_disclosure_accounting,
    nonbinary_syndrome, symbols_to_msb_bits, verify_nonbinary_symbols)
from .shared import canonical_event, locked_seed_bits, materialize_seed_record, toeplitz_tag, transcript_summary

RUN_ID = "20260726_v1_nbldpc_synthetic"
METHOD, Q, N, SEED_BITS = "nbldpc_formal_v1", 1024, 64, 703
PS, ROLES, COUNTS = (.20, .30), ("development", "confirmation"), {"development": 8, "confirmation": 32}
ARTIFACTS = ("pre_run_plan.json", "formal_frame_outcomes.csv", "formal_transcript.jsonl", "formal_run_manifest.json", "formal_codebook_manifest.json", "formal_policy_manifest.json", "formal_qualification_report.json")
GATE_STATUSES = {"verified_success", "verify_failed", "decode_failed", "syndrome_inconsistent", "aborted_resource_limit", "decoder_error"}
STATUS_PRECEDENCE = ("invalid_run", "aborted_resource_limit", "decoder_error", "unsupported_domain", "codebook_invalid", "decode_failed", "syndrome_inconsistent", "verify_failed", "verified_success")
CAPS = {"decoder_call_s": 10, "complete_run_s": 1800, "workers": 1, "q": Q, "n": N}
OFFICIAL_OUTPUT_ROOT = Path("comparison_bench/outputs_comparison/formal_ir_methods/20260726_v1_nbldpc_synthetic")

def _compact(v: Any) -> bytes: return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
def _sha(v: bytes) -> str: return hashlib.sha256(v).hexdigest()
def _now() -> str: return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
def _write_x(p: Path, data: bytes) -> None:
    with p.open("xb") as h: h.write(data)
def _json_x(p: Path, v: Any) -> None: _write_x(p, json.dumps(v, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False).encode("utf-8") + b"\n")
def _csv_x(p: Path, rows: list[dict[str, Any]]) -> None:
    fields = sorted({k for r in rows for k in r}) or ["status"]
    with p.open("x", encoding="utf-8", newline="") as h:
        w = csv.DictWriter(h, fieldnames=fields); w.writeheader()
        for r in rows: w.writerow({k: json.dumps(v, sort_keys=True) if isinstance(v, (dict, list)) else v for k,v in r.items()})
def _rows(p: Path) -> list[dict[str, str]]:
    with p.open(encoding="utf-8", newline="") as h: return list(csv.DictReader(h))
def _normal(value: Any) -> Any:
    if isinstance(value, str):
        if value in {"True","False"}: return value == "True"
        try: return int(value)
        except ValueError:
            try: return float(value)
            except ValueError: return value
    if isinstance(value, dict): return {k:_normal(v) for k,v in value.items()}
    if isinstance(value, list): return [_normal(v) for v in value]
    return value
def _same_row(actual: Mapping[str,Any], expected: Mapping[str,Any]) -> bool:
    a={k:_normal(v) for k,v in actual.items() if k!="runtime_s"}; b={k:_normal(v) for k,v in expected.items() if k!="runtime_s"}
    return set(a)==set(b) and a==b
def _root() -> Path: return Path(__file__).resolve().parents[4]

def _output(output: Path | None, *, _test_only: bool) -> Path:
    official = (_root() / OFFICIAL_OUTPUT_ROOT).resolve()
    chosen = official if output is None else Path(output).resolve()
    if chosen != official and not _test_only:
        raise ValueError("N3 requires the frozen official output root")
    return chosen

def _id(p: float, role: str, i: int) -> str: return f"{METHOD}_q1024_p{int(p*100):02d}_{role}_{i:03d}"
def _seed(p: float, role: str, i: int) -> int:
    # Roots and order are intentionally literal contract values.
    root = {("development", .20): 202607300000, ("development", .30): 202607310000,
            ("confirmation", .20): 202607320000, ("confirmation", .30): 202607330000}[(role, p)]
    return root + i
def _frame(p: float, role: str, i: int) -> dict[str, Any]:
    rng = np.random.Generator(np.random.PCG64(_seed(p, role, i)))
    alice = rng.integers(0, Q, size=N, dtype=np.int64)
    mask = rng.random(N) < p
    candidates = rng.integers(1, Q, size=N, dtype=np.int64)
    bob = alice.copy(); bob[mask] = alice[mask] ^ candidates[mask]
    return {"frame_id": _id(p, role, i), "p": p, "role": role, "index": i, "seed": _seed(p, role, i),
            "alice": alice.tolist(), "bob": bob.tolist(), "array_sha256": _sha(_canonical_array(alice)+_canonical_array(bob)),
            "atomic_keys": [f"{role}|{p:.2f}|{i}|{j}" for j in range(N)]}
def _frames() -> list[dict[str, Any]]:
    return [_frame(p, role, i) for role in ROLES for p in PS for i in range(COUNTS[role])]

def _canonical_array(values: np.ndarray) -> bytes:
    array=np.asarray(values, dtype="<i8").reshape(-1)
    return len(array).to_bytes(4,"big") + array.tobytes(order="C")

def _h2(p: float) -> float: return -p*np.log2(p) - (1-p)*np.log2(1-p)
def policy_grid() -> list[dict[str, Any]]:
    result=[]
    for margin in (0, 7):
        for scale in (1.0, 1.25):
            for maximum in (10, 20):
                per=[]
                for p in PS:
                    needed=int(np.ceil(N*(_h2(p)+p*np.log2(1023))/10))+margin
                    checks=next((x for x in (16,24,32) if x >= needed), None)
                    if checks is None: raise ValueError("N3 policy cannot select N1 prefix")
                    per.append({"p":p,"check_count":checks,"decoder_p":p*scale})
                body={"rate_margin_symbols":margin,"decoder_p_scale":scale,"max_iter":maximum,"strata":per}
                result.append(dict(body, policy_sha256=_sha(_compact(body))))
    return result

def _prior_seed_ids(*, exclude: Path | None = None) -> set[str]:
    base = _root()/"comparison_bench"/"outputs_comparison"/"formal_ir_methods"
    found=set()
    if base.exists():
        for path in base.rglob("pre_run_plan.json"):
            if exclude is not None and path.resolve() == exclude.resolve(): continue
            try:
                data=json.loads(path.read_text(encoding="utf-8"))
                for group in (data.get("development_toeplitz_seeds",{}), data.get("confirmation_toeplitz_seeds",{})):
                    values=group.values() if isinstance(group,dict) else []
                    found.update(str(x.get("seed_id")) for x in values if isinstance(x,dict))
            except (OSError, ValueError, TypeError): continue
    return found

def _provenance() -> dict[str, Any]:
    modules=("nonbinary_field.py","nonbinary_codebook.py","nonbinary_qspa.py","nonbinary_qualification.py")
    formal=Path(__file__).resolve().parent
    try:
        commit=subprocess.run(["git","rev-parse","HEAD"],cwd=_root(),capture_output=True,check=True).stdout.decode().strip()
        # Ignore only this frozen evidence root: creating the reviewed plan
        # must not invalidate its own provenance snapshot.
        status=subprocess.run(["git","status","--porcelain=v1","--untracked-files=all","--",".",f":(exclude){OFFICIAL_OUTPUT_ROOT.as_posix()}"],cwd=_root(),capture_output=True,check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        commit=None
        status=b""
    cli=Path(__file__).resolve().parents[1]/"cli"/"run_formal_nonbinary_qualification.py"
    return {"python":platform.python_version(),"numpy":np.__version__,"git_commit":commit,"git_dirty":bool(status),"git_status_sha256":_sha(status),
            "module_sha256":{name:_sha((formal/name).read_bytes()) for name in modules},
            "cli_sha256":_sha(cli.read_bytes()),
            "generator_policy_contract_sha256":_sha(_compact({"generator":"PCG64/alice-mask-errors-masked_xor","policies":policy_grid(),"caps":CAPS}))}

def expected_plan(*, exclude_plan: Path | None = None) -> dict[str, Any]:
    frames=_frames(); dev=[x for x in frames if x["role"]=="development"]; conf=[x for x in frames if x["role"]=="confirmation"]
    grid=policy_grid()
    dev_seeds={f"{p['policy_sha256']}|{f['frame_id']}":materialize_seed_record(SEED_BITS) for p in grid for f in dev}
    conf_seeds={f["frame_id"]:materialize_seed_record(SEED_BITS) for f in conf}
    all_ids=[x["seed_id"] for x in list(dev_seeds.values())+list(conf_seeds.values())]
    prior=_prior_seed_ids(exclude=exclude_plan); overlap=sorted(set(all_ids)&prior)
    return {"run_id":RUN_ID,"method":METHOD,"q":Q,"n":N,"mapping":"polynomial_basis_msb_first","channel":"qary_symmetric",
      "frames":frames,"development_execution_order":[x["frame_id"] for x in dev],"confirmation_execution_order":[x["frame_id"] for x in conf],
      "generator":{"pcg":"PCG64","call_order":["integers_alice","random_error_mask","integers_nonzero_errors","masked_xor"],"roots":{"development_p20":202607300000,"development_p30":202607310000,"confirmation_p20":202607320000,"confirmation_p30":202607330000}},
      "generator_sha256":_sha(_compact(frames)),"policies":grid,"policy_hashes":[x["policy_sha256"] for x in grid],"development_toeplitz_seeds":dev_seeds,"confirmation_toeplitz_seeds":conf_seeds,
      "toeplitz":{"seed_bits":SEED_BITS,"input_bits":640,"tag_bits":64,"globally_unique":len(all_ids)==len(set(all_ids)),"prior_plan_overlap_seed_ids":overlap},"caps":CAPS,"status_precedence":list(STATUS_PRECEDENCE),"provenance":_provenance(),"artifact_schema":list(ARTIFACTS)}

def create_plan(output: Path | None = None, *, _test_only: bool = False) -> dict[str, Any]:
    """Plan-only action: creates exactly one file and never calls a decoder."""
    output=_output(output,_test_only=_test_only)
    if output.exists(): raise FileExistsError("fresh output directory required")
    plan=expected_plan(exclude_plan=output/"pre_run_plan.json")
    if plan["toeplitz"]["prior_plan_overlap_seed_ids"]: raise ValueError("prior formal Toeplitz seed overlap")
    output.mkdir(parents=True)
    _json_x(output/"pre_run_plan.json",plan); return plan

def _validate_plan(plan: Mapping[str, Any], *, plan_path: Path | None = None, live_provenance: bool = False) -> None:
    # Reconstruct non-secret deterministic parts; locked CSPRNG seed material is validated structurally.
    probe=expected_plan(exclude_plan=plan_path); keys=("run_id","method","q","n","mapping","channel","frames","development_execution_order","confirmation_execution_order","generator","generator_sha256","policies","policy_hashes","toeplitz","caps","status_precedence","artifact_schema")
    if any(plan.get(k)!=probe.get(k) for k in keys): raise ValueError("plan deterministic reconstruction mismatch")
    for name, expected in (("development_toeplitz_seeds",len(probe["policies"])*16),("confirmation_toeplitz_seeds",64)):
        records=plan.get(name,{});
        if not isinstance(records,dict) or len(records)!=expected: raise ValueError("Toeplitz seed count")
        required = ({f"{p['policy_sha256']}|{f}" for p in plan["policies"] for f in plan["development_execution_order"]}
                    if name == "development_toeplitz_seeds" else set(plan["confirmation_execution_order"]))
        if set(records) != required: raise ValueError("Toeplitz seed bindings")
        for rec in records.values(): locked_seed_bits(rec,SEED_BITS)
    ids=[x["seed_id"] for x in list(plan["development_toeplitz_seeds"].values())+list(plan["confirmation_toeplitz_seeds"].values())]
    # The plan stores the pre-creation scan proof.  Re-scanning here would
    # include this very plan, so uniqueness and the immutable recorded proof
    # are the read-only verification boundary.
    if len(ids)!=len(set(ids)) or plan.get("toeplitz", {}).get("prior_plan_overlap_seed_ids") != []: raise ValueError("Toeplitz overlap")
    if plan_path is not None and set(ids) & _prior_seed_ids(exclude=plan_path): raise ValueError("Toeplitz overlap with prior plan")
    if live_provenance and plan.get("provenance")!=_provenance(): raise ValueError("provenance mismatch")

def _policy_for(policy: Mapping[str, Any], p: float) -> Mapping[str, Any]: return next(x for x in policy["strata"] if float(x["p"])==p)
def _events(frame: str, syndrome: tuple[int,...], result: Mapping[str,Any], seed: Mapping[str,Any], status: str, alice: np.ndarray) -> list[dict[str,Any]]:
    events=[]
    def add(kind: str,direction: str,payload: dict[str,Any], kb: int=0, cb: int=0):
        events.append({"event_id":len(events),"frame_key":frame,"method":METHOD,"event_type":kind,"direction":direction,"parent_event_id":events[-1]["event_id"] if events else -1,"pass_id":0,"block_id":0,"key_dependent_bits":kb,"public_control_bits":cb,"payload":payload})
    add("SYNDROME","alice_to_bob",{"syndrome":list(syndrome)},len(syndrome)*10)
    add("DECODER","bob_local",{"reason":str(result.get("reason",status))})
    if status in {"verified_success","verify_failed"}:
        tag=toeplitz_tag(symbols_to_msb_bits(alice,Q),locked_seed_bits(seed,SEED_BITS)).hex()
        add("VERIFICATION_TAG","alice_to_bob",{"tag":tag,"seed_id":seed["seed_id"],"seed_bit_length":SEED_BITS},64,SEED_BITS)
    return events

def production_runner(alice: np.ndarray, bob: np.ndarray, *, check_count: int, p: float, max_iter: int, manifest: Mapping[str,Any], matrices: Mapping[int,Any]) -> dict[str,Any]:
    field=GF2mField(get_field_spec(Q)); matrix=matrices[check_count]; syndrome=nonbinary_syndrome(matrix,alice,field)
    result=decode_nonbinary_fft_qspa(bob,syndrome,manifest,matrices,check_count=check_count,p=p,max_iter=max_iter)
    return dict(result, syndrome=syndrome)

def _one(frame: Mapping[str,Any], policy: Mapping[str,Any], seed: Mapping[str,Any], *, runner: Callable[...,Mapping[str,Any]], manifest: Mapping[str,Any], matrices: Mapping[int,Any], clock: Callable[[],float]) -> tuple[dict[str,Any],list[dict[str,Any]]]:
    setting=_policy_for(policy,float(frame["p"])); alice=np.asarray(frame["alice"],dtype=np.int64); bob=np.asarray(frame["bob"],dtype=np.int64)
    t=clock()
    try:
        raw=dict(runner(alice,bob,check_count=int(setting["check_count"]),p=float(setting["decoder_p"]),max_iter=int(policy["max_iter"]),manifest=manifest,matrices=matrices))
        elapsed=clock()-t; status=str(raw.get("status","decoder_error"))
        if elapsed>CAPS["decoder_call_s"]: status="aborted_resource_limit"
    except Exception as exc:
        raw={"reason":f"{type(exc).__name__}: {exc}","iterations":0}; elapsed=clock()-t; status="decoder_error"
    expected_syndrome=nonbinary_syndrome(matrices[int(setting["check_count"])],alice,GF2mField(get_field_spec(Q)))
    if "syndrome" in raw and tuple(raw["syndrome"]) != expected_syndrome:
        raw={"reason":"runner syndrome mismatch","iterations":int(raw.get("iterations",0))}; status="decoder_error"
    syndrome=expected_syndrome
    invoked=status=="syndrome_consistent"; verified=False
    if invoked:
        check=verify_nonbinary_symbols(alice,np.asarray(raw.get("decoded_symbols",bob),dtype=np.int64),Q,seed,invoked=True); verified=bool(check["verified"]); status="verified_success" if verified else "verify_failed"
    accounting=nonbinary_disclosure_accounting(int(setting["check_count"]),Q,verification_invoked=invoked,verification_tag_bits=64,public_control_bits=SEED_BITS if invoked else 0)
    events=_events(str(frame["frame_id"]),syndrome,raw,seed,status,alice); summary=transcript_summary(events)
    row={"frame_id":frame["frame_id"],"stratum_p":frame["p"],"qualification_role":frame["role"],"policy_sha256":policy["policy_sha256"],"status":status,"attempted":True,"denominator_included":True,"iterations":int(raw.get("iterations",0)),"runtime_s":elapsed,"verification_invoked":invoked,"verification_seed_id":seed["seed_id"] if invoked else "","check_count":setting["check_count"],"decoder_p":setting["decoder_p"],**accounting,**summary}
    return row,events

def _cap_row(frame: Mapping[str,Any], policy: Mapping[str,Any], seed: Mapping[str,Any], matrices: Mapping[int,Any]) -> tuple[dict[str,Any],list[dict[str,Any]]]:
    setting=_policy_for(policy,float(frame["p"])); check_count=int(setting["check_count"]); alice=np.asarray(frame["alice"],dtype=np.int64)
    syndrome=nonbinary_syndrome(matrices[check_count],alice,GF2mField(get_field_spec(Q)))
    events=_events(str(frame["frame_id"]),syndrome,{"reason":"complete_run_s"},seed,"aborted_resource_limit",alice); summary=transcript_summary(events)
    return ({"frame_id":frame["frame_id"],"stratum_p":frame["p"],"qualification_role":"confirmation","policy_sha256":policy["policy_sha256"],"status":"aborted_resource_limit","attempted":True,"denominator_included":True,"iterations":0,"runtime_s":0.0,"verification_invoked":False,"verification_seed_id":"","check_count":check_count,"decoder_p":setting["decoder_p"],**nonbinary_disclosure_accounting(check_count,Q,verification_invoked=False),**summary},events)

def _select(dev: Mapping[str,list[dict[str,Any]]], grid: list[dict[str,Any]]) -> dict[str,Any]:
    scored=[]
    for p in grid:
        r=dev[p["policy_sha256"]]; scored.append(( -sum(x["status"]=="verified_success" for x in r),sum(int(x["key_dependent_disclosure_bits_total"]) for x in r),sum(int(x["iterations"]) for x in r),p["policy_sha256"],p))
    best=min(scored); return {"selected_policy":best[-1],"selection_key":list(best[:-1])}
def _gate(rows: list[dict[str,Any]]) -> dict[str,Any]:
    good=sum(x["status"]=="verified_success" for x in rows); prohibited=sum(x["status"] not in GATE_STATUSES for x in rows)
    return {"requested":32,"denominator_included":sum(bool(x["denominator_included"]) for x in rows),"verified_success":good,"prohibited_failures":prohibited,"promoted":len(rows)==32 and good>=31 and prohibited==0}

def _artifact_hashes(output:Path) -> dict[str,str]:
    # Exclude the manifest/report themselves to avoid a self-referential hash;
    # bind every preceding evidence artifact, including policy selection.
    names=("pre_run_plan.json","formal_frame_outcomes.csv","formal_transcript.jsonl","formal_codebook_manifest.json","formal_policy_manifest.json")
    return {n:_sha((output/n).read_bytes()) for n in names if (output/n).exists()}
def _finalize(output:Path, exc:BaseException, state:dict[str,Any]) -> None:
    # Finalization is deliberately additive and produces a verifier-readable invalid package.
    if not (output/"formal_frame_outcomes.csv").exists(): _csv_x(output/"formal_frame_outcomes.csv",list(state.get("rows",[])))
    if not (output/"formal_transcript.jsonl").exists(): _write_x(output/"formal_transcript.jsonl",b"".join(canonical_event(x) for x in state.get("events",[])))
    if not (output/"formal_codebook_manifest.json").exists(): _json_x(output/"formal_codebook_manifest.json",{"invalid":True})
    if not (output/"formal_policy_manifest.json").exists(): _json_x(output/"formal_policy_manifest.json",{"invalid":True,"development_outcomes":state.get("dev",{})})
    if not (output/"formal_run_manifest.json").exists(): _json_x(output/"formal_run_manifest.json",{"run_id":RUN_ID,"run_status":"invalid_run","reason":f"{type(exc).__name__}: {exc}","artifacts":_artifact_hashes(output)})
    if not (output/"formal_qualification_report.json").exists(): _json_x(output/"formal_qualification_report.json",{"run_id":RUN_ID,"run_status":"invalid_run","promoted":False,"formal_run_manifest_sha256":_sha((output/"formal_run_manifest.json").read_bytes())})

def run(output:Path | None = None, *, runner:Callable[...,Mapping[str,Any]]=production_runner, clock:Callable[[],float]=time.monotonic, _test_only: bool=False) -> None:
    output=_output(output,_test_only=_test_only)
    if not output.is_dir() or {x.name for x in output.iterdir()} != {"pre_run_plan.json"}: raise ValueError("execute requires exactly reviewed plan-only directory")
    plan_bytes=(output/"pre_run_plan.json").read_bytes(); plan=json.loads(plan_bytes); _validate_plan(plan,plan_path=output/"pre_run_plan.json",live_provenance=not _test_only)
    started=0.0; state={"rows":[],"events":[],"dev":{}}
    try:
        started=clock()
        cb,matrices=build_nonbinary_codebook_family(Q); check=verify_nonbinary_codebook_family(cb,matrices)
        if check.get("status")!="ok": raise RuntimeError("N1 codebook invalid")
        _json_x(output/"formal_codebook_manifest.json",cb)
        byid={x["frame_id"]:x for x in plan["frames"]}; dev={p["policy_sha256"]:[] for p in plan["policies"]}; state["dev"]=dev
        for fid in plan["development_execution_order"]:
            for policy in plan["policies"]:
                if clock()-started>=CAPS["complete_run_s"]: raise TimeoutError("complete run cap during development")
                row,events=_one(byid[fid],policy,plan["development_toeplitz_seeds"][f"{policy['policy_sha256']}|{fid}"],runner=runner,manifest=cb,matrices=matrices,clock=clock); dev[policy["policy_sha256"]].append(row)
        selection=_select(dev,plan["policies"]); chosen=selection["selected_policy"]
        _json_x(output/"formal_policy_manifest.json",{"policies":plan["policies"],"development_outcomes":dev,"selection":selection,"selected_policy_sha256":chosen["policy_sha256"]})
        rows=[]; events=[]; capped=False
        for fid in plan["confirmation_execution_order"]:
            frame=byid[fid]
            if capped or clock()-started>=CAPS["complete_run_s"]:
                capped=True; row,e=_cap_row(frame,chosen,plan["confirmation_toeplitz_seeds"][fid],matrices)
            else: row,e=_one(frame,chosen,plan["confirmation_toeplitz_seeds"][fid],runner=runner,manifest=cb,matrices=matrices,clock=clock)
            rows.append(row); events.extend(e)
        state.update(rows=rows,events=events); _csv_x(output/"formal_frame_outcomes.csv",rows); _write_x(output/"formal_transcript.jsonl",b"".join(canonical_event(x) for x in events))
        gates={f"p{int(p*100):02d}":_gate([x for x in rows if float(x["stratum_p"])==p]) for p in PS}
        manifest={"run_id":RUN_ID,"run_status":"completed","plan_sha256":_sha(plan_bytes),"selected_policy_sha256":chosen["policy_sha256"],"outcome_count":len(rows),"artifacts":_artifact_hashes(output)}; _json_x(output/"formal_run_manifest.json",manifest)
        _json_x(output/"formal_qualification_report.json",{"run_id":RUN_ID,"run_status":"completed","promotion_gates":gates,"promoted":all(x["promoted"] for x in gates.values()),"formal_run_manifest_sha256":_sha((output/"formal_run_manifest.json").read_bytes())})
        if (output/"pre_run_plan.json").read_bytes()!=plan_bytes: raise RuntimeError("plan changed during execution")
    except BaseException as exc:
        _finalize(output,exc,state); raise

def verify(output:Path | None=None, *, verifier_runner:Callable[...,Mapping[str,Any]]=production_runner, _test_only: bool=False) -> dict[str,Any]:
    output=_output(output,_test_only=_test_only)
    names={x.name for x in output.iterdir()}
    if names=={"pre_run_plan.json"}: plan=json.loads((output/"pre_run_plan.json").read_text()); _validate_plan(plan,plan_path=output/"pre_run_plan.json",live_provenance=not _test_only); return {"verified":True,"plan_only":True}
    if names != set(ARTIFACTS): raise ValueError("seven-artifact contract")
    plan=json.loads((output/"pre_run_plan.json").read_text()); _validate_plan(plan,plan_path=output/"pre_run_plan.json",live_provenance=not _test_only)
    manifest=json.loads((output/"formal_run_manifest.json").read_text()); report=json.loads((output/"formal_qualification_report.json").read_text())
    if report.get("formal_run_manifest_sha256")!=_sha((output/"formal_run_manifest.json").read_bytes()) or manifest.get("run_id")!=RUN_ID or report.get("run_id")!=RUN_ID: raise ValueError("run bindings")
    if manifest.get("run_status")=="invalid_run":
        if set(manifest)!={"run_id","run_status","reason","artifacts"} or set(report)!={"run_id","run_status","promoted","formal_run_manifest_sha256"}: raise ValueError("invalid manifest schema")
        if report.get("run_status")!="invalid_run" or report.get("promoted") is not False: raise ValueError("invalid run promotion")
        if manifest.get("artifacts")!=_artifact_hashes(output): raise ValueError("invalid artifact DAG")
        raw=(output/"formal_transcript.jsonl").read_bytes(); events=[json.loads(x) for x in raw.splitlines()]
        if b"".join(canonical_event(x) for x in events)!=raw: raise ValueError("invalid transcript")
        codebook=json.loads((output/"formal_codebook_manifest.json").read_text()); policy=json.loads((output/"formal_policy_manifest.json").read_text())
        if codebook not in ({"invalid":True}, build_nonbinary_codebook_family(Q)[0]): raise ValueError("invalid codebook state")
        if not (policy.get("invalid") is True or (policy.get("policies")==plan["policies"] and isinstance(policy.get("development_outcomes"),dict))): raise ValueError("invalid policy state")
        allowed={x["frame_id"] for x in plan["frames"]}; rows=_rows(output/"formal_frame_outcomes.csv")
        if codebook=={"invalid":True}:
            if policy != {"invalid":True,"development_outcomes":{}} or rows or events: raise ValueError("invalid sentinel state")
        if policy.get("invalid") is True and (rows or events): raise ValueError("invalid policy cannot carry rows")
        if len({x.get("frame_id") for x in rows}) != len(rows) or any(x.get("frame_id") not in allowed or x.get("status") not in GATE_STATUSES for x in rows): raise ValueError("invalid partial rows")
        for row in rows:
            es=[e for e in events if e["frame_key"]==row["frame_id"]]
            if es and transcript_summary(es)["transcript_sha256"]!=row.get("transcript_sha256"): raise ValueError("invalid partial accounting")
        return {"verified":True,"run_status":"invalid_run"}
    manifest_keys={"run_id","run_status","plan_sha256","selected_policy_sha256","outcome_count","artifacts"}
    report_keys={"run_id","run_status","promotion_gates","promoted","formal_run_manifest_sha256"}
    if set(manifest)!=manifest_keys or set(report)!=report_keys or manifest.get("run_status")!="completed" or report.get("run_status")!="completed": raise ValueError("completed manifest schema")
    if manifest.get("plan_sha256")!=_sha((output/"pre_run_plan.json").read_bytes()) or manifest.get("artifacts")!=_artifact_hashes(output) or manifest.get("outcome_count")!=64: raise ValueError("artifact DAG")
    cb=json.loads((output/"formal_codebook_manifest.json").read_text()); expected,mats=build_nonbinary_codebook_family(Q)
    if cb!=expected or verify_nonbinary_codebook_family(cb,mats).get("status")!="ok": raise ValueError("codebook")
    policy=json.loads((output/"formal_policy_manifest.json").read_text()); dev=policy.get("development_outcomes",{})
    if policy.get("policies")!=plan["policies"] or set(dev)!={p["policy_sha256"] for p in plan["policies"]}: raise ValueError("policy grid")
    byid={x["frame_id"]:x for x in plan["frames"]}
    for p in plan["policies"]:
        values=dev[p["policy_sha256"]]
        if len(values)!=16 or [x.get("frame_id") for x in values] != [fid for fid in plan["development_execution_order"] for _ in [0]][:len(values)]:
            # policy-major order is two strata x eight frames, exactly plan order.
            raise ValueError("development order")
        if any(x.get("policy_sha256")!=p["policy_sha256"] or x.get("status") not in GATE_STATUSES for x in values): raise ValueError("development binding")
        for stored, fid in zip(values,plan["development_execution_order"]):
            replay,_=_one(byid[fid],p,plan["development_toeplitz_seeds"][f"{p['policy_sha256']}|{fid}"],runner=verifier_runner,manifest=cb,matrices=mats,clock=lambda:0.0)
            if not _same_row(stored,replay): raise ValueError("development replay")
    selection=_select(dev,plan["policies"])
    if policy.get("selection")!=selection or policy.get("selected_policy_sha256")!=selection["selected_policy"]["policy_sha256"]: raise ValueError("selection")
    if manifest.get("selected_policy_sha256")!=selection["selected_policy"]["policy_sha256"]: raise ValueError("manifest policy binding")
    rows=_rows(output/"formal_frame_outcomes.csv")
    if len(rows)!=64 or [x["frame_id"] for x in rows]!=plan["confirmation_execution_order"]: raise ValueError("confirmation denominator/order")
    if any(x["status"] not in GATE_STATUSES or x["denominator_included"].lower() not in {"true","1"} or x["policy_sha256"]!=selection["selected_policy"]["policy_sha256"] for x in rows): raise ValueError("outcome status")
    raw=(output/"formal_transcript.jsonl").read_bytes(); events=[json.loads(x) for x in raw.splitlines()]
    if b"".join(canonical_event(x) for x in events)!=raw: raise ValueError("transcript canonical")
    # Each row's transcript accounting must match the public transcript slice.
    for row in rows:
        es=[e for e in events if e["frame_key"]==row["frame_id"]]; s=transcript_summary(es)
        if s["transcript_sha256"]!=row["transcript_sha256"] or int(s["key_dependent_disclosure_bits_total"])!=int(row["key_dependent_disclosure_bits_total"]) or int(s["public_control_bits_total"])!=int(row["public_control_bits_total"]): raise ValueError("transcript/accounting")
        frame=byid[row["frame_id"]]; setting=_policy_for(selection["selected_policy"],float(frame["p"]))
        if row["qualification_role"]!="confirmation" or float(row["stratum_p"])!=float(frame["p"]) or int(row["check_count"])!=int(setting["check_count"]) or float(row["decoder_p"])!=float(setting["decoder_p"]): raise ValueError("confirmation setting")
        cap_event = len(es)==2 and es[1].get("event_type")=="DECODER" and es[1].get("payload",{}).get("reason")=="complete_run_s"
        if row["status"] == "aborted_resource_limit" and cap_event:
            replay, expected_events=_cap_row(frame,selection["selected_policy"],plan["confirmation_toeplitz_seeds"][row["frame_id"]],mats)
        else:
            replay, expected_events=_one(frame,selection["selected_policy"],plan["confirmation_toeplitz_seeds"][row["frame_id"]],runner=verifier_runner,manifest=cb,matrices=mats,clock=lambda:0.0)
        if not _same_row(row,replay): raise ValueError("confirmation replay")
        if es != expected_events: raise ValueError("confirmation transcript replay")
    typed=[dict(x, stratum_p=float(x["stratum_p"]), denominator_included=x["denominator_included"].lower() in {"true","1"}) for x in rows]
    gates={f"p{int(p*100):02d}":_gate([x for x in typed if x["stratum_p"]==p]) for p in PS}
    if report.get("promotion_gates")!=gates or report.get("promoted")!=all(x["promoted"] for x in gates.values()): raise ValueError("gate/report")
    return {"verified":True,"run_status":manifest["run_status"],"promoted":report["promoted"]}
