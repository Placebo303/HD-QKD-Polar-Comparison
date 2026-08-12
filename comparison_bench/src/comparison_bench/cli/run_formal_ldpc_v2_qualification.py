"""Fresh, non-resumable synthetic qualification for ``ldpc_formal_v2``.

This command deliberately has no default output directory.  The v1 runner is
not imported or branched: its evidence remains immutable.
"""
from __future__ import annotations

import argparse, csv, hashlib, importlib.metadata, json, os, platform, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from ..formal_ir.codebook_v2 import materialize_selected_codebooks, screening_manifest, verify_selected_codebooks
from ..formal_ir.ldpc import calibrate_rates, codebook_entry
from ..formal_ir.ldpc_v2 import METHOD, policy_grid, probe_constructors, run_ldpc_formal_v2, select_global_policy
from ..formal_ir.shared import canonical_event, materialize_seed_record, transcript_summary, verification_union_bound

RUN_ID = "20260725_v2_ldpc_v2_synthetic"
Q, N, SEED_BITS = 1024, 64, 703
ARTIFACTS = ("pre_run_plan.json", "formal_frame_outcomes.csv", "formal_transcript.jsonl", "formal_codebook_manifest.json", "formal_policy_manifest.json", "formal_run_manifest.json", "formal_qualification_report.json")
TOP_LEVEL = set(ARTIFACTS) | {"codebooks"}
GATE_STATUSES = {"verified_success", "verify_failed", "decode_failed", "syndrome_inconsistent", "aborted_resource_limit", "decoder_error"}

def _sha(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def _compact(value: Any) -> bytes: return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
def _now() -> str: return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
def _write_x(path: Path, data: bytes) -> None:
    with path.open("xb") as handle: handle.write(data)
def _json_x(path: Path, value: Any) -> None: _write_x(path, json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False).encode("utf-8") + b"\n")
def _csv_x(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = sorted({key for row in rows for key in row}) or ["status"]
    with path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for row in rows: writer.writerow({key: json.dumps(value, sort_keys=True) if isinstance(value, (list, dict)) else value for key, value in row.items()})

def _flip(alice: np.ndarray, seed: int, p: float) -> np.ndarray:
    rng = np.random.Generator(np.random.PCG64(seed)); flips = rng.random((*alice.shape, 10)) < p
    return np.asarray(alice, dtype=np.int64) ^ (flips.astype(np.int64) * (1 << np.arange(9, -1, -1))).sum(axis=2)

def _batches() -> dict[str, tuple[np.ndarray, np.ndarray]]:
    rng = np.random.Generator(np.random.PCG64(2026072651)); alice = [rng.integers(0, Q, size=(32, N), dtype=np.int64) for _ in range(4)]
    return {"p01_calibration": (alice[0], _flip(alice[0], 2026072661, .01)), "p02_calibration": (alice[1], _flip(alice[1], 2026072662, .02)), "p01_confirmation": (alice[2], _flip(alice[2], 2026072663, .01)), "p02_confirmation": (alice[3], _flip(alice[3], 2026072664, .02))}

def _ids(role: str) -> list[str]:
    return [f"synthetic_q1024_p{int(p*1000):03d}_{role}_f{i:03d}" for p in (.01, .02) for i in range(32)]

def _expected_plan_fields() -> dict[str, Any]:
    cal, confirm = _ids("calibration"), _ids("confirmation")
    dev_order = [cal[int(i)] for i in np.random.Generator(np.random.PCG64(2026072671)).permutation(64)]
    conf_order = [confirm[int(i)] for i in np.random.Generator(np.random.PCG64(2026072672)).permutation(64)]
    grid = policy_grid()
    batches = _batches(); screening = screening_manifest()
    return {"run_id": RUN_ID, "method": METHOD, "dimension": Q, "mapping": "gray", "frame_len_symbols": N,
      "seeds": {"alice_stream": 2026072651, "bsc": [2026072661,2026072662,2026072663,2026072664], "development_order": 2026072671, "confirmation_order": 2026072672},
      "caps": {"method_call_s": 5, "complete_run_s": 1800}, "calibration_ids": cal, "development_execution_order": dev_order, "confirmation_execution_order": conf_order,
      "policy_hashes": [p["policy_id"] for p in grid], "screening_manifest_sha256": screening["manifest_sha256"],
      "synthetic_generation_sha256": {name: _sha(a.tobytes() + b.tobytes()) for name, (a,b) in batches.items()},
      "failure_finalizer": "exclusive_preserve_partial_seven_artifacts"}

def _plan(provenance: Mapping[str, Any]) -> dict[str, Any]:
    base = _expected_plan_fields(); grid = policy_grid()
    base["development_toeplitz_seeds"] = {f"{policy['policy_id']}|{frame}": materialize_seed_record(SEED_BITS) for policy in grid for frame in base["development_execution_order"]}
    base["confirmation_toeplitz_seeds"] = {frame: materialize_seed_record(SEED_BITS) for frame in base["confirmation_execution_order"]}
    base["provenance"] = dict(provenance)
    return base

def _dataset_and_index(frame: str) -> tuple[str, str, int, float]:
    p = .01 if "p010_" in frame else .02
    return (f"synthetic_p{p:.2f}", "p01" if p == .01 else "p02", int(frame[-3:]), p)

def _calibrations(batches: Mapping[str, tuple[np.ndarray,np.ndarray]]) -> dict[str, dict[str, Any]]:
    result = {}
    for label, p in (("p01", .01), ("p02", .02)):
        a,b = batches[f"{label}_calibration"]; dataset=f"synthetic_p{p:.2f}"
        result[label] = calibrate_rates({dataset:(a,b)}, sacrificed_frame_keys={dataset:[f"{label}_calibration_{i:03d}" for i in range(32)]}, calibration_role="sacrificed_tuning_only", mapping="gray", source_bytes=a.tobytes()+b.tobytes(), dimension=Q)
    return result

def _git() -> dict[str, Any]:
    def capture(*args: str) -> bytes: return subprocess.run(["git",*args], cwd=_repo_root(), check=True, capture_output=True).stdout
    status=capture("status","--porcelain=v1","--untracked-files=all")
    return {"commit":capture("rev-parse","HEAD").decode().strip(),"status_porcelain_v1_hex":status.hex(),"status_porcelain_v1_sha256":_sha(status),"dirty":bool(status)}

def _repo_root() -> Path: return Path(__file__).resolve().parents[4]
def _provenance() -> dict[str, Any]:
    formal = Path(__file__).resolve().parents[1] / "formal_ir"
    return {"git": _git(), "environment": {"python": platform.python_version(), "numpy": np.__version__, "ldpc": importlib.metadata.version("ldpc")},
        "source_sha256": {name: _sha((formal / name).read_bytes()) for name in ("ldpc_v2.py", "codebook_v2.py", "shared.py")}}
def _v1_golden_hash_snapshot() -> dict[str, str]:
    return {f"{rate}|{plane}": str(codebook_entry(rate, plane)["sha256"]) for rate in ("r050", "r0375", "r025", "r0125") for plane in range(10)}
def _verify_provenance(stored: Mapping[str, Any], current: Mapping[str, Any]) -> None:
    """Validate a pre-run snapshot without treating later untracked output as drift."""
    git = stored.get("git", {})
    try: status = bytes.fromhex(str(git.get("status_porcelain_v1_hex", "")))
    except ValueError as exc: raise ValueError("stored git status encoding") from exc
    if not isinstance(git.get("commit"), str) or git.get("status_porcelain_v1_sha256") != _sha(status) or git.get("dirty") != bool(status):
        raise ValueError("stored git snapshot")
    for key in ("commit",):
        if git.get(key) != current.get("git", {}).get(key): raise ValueError("live git core provenance")
    for key in ("environment", "source_sha256"):
        if stored.get(key) != current.get(key): raise ValueError(f"live {key} provenance")

def _artifact_hashes(output: Path) -> dict[str,str]:
    return {name:_sha((output/name).read_bytes()) for name in ARTIFACTS[:5] if (output/name).is_file()}

def _finalize(output: Path, exc: BaseException, started: str, provenance: Any, state: Mapping[str, Any]) -> None:
    reason=f"{type(exc).__name__}: {exc}"
    if not (output/"pre_run_plan.json").exists(): _json_x(output/"pre_run_plan.json", {"run_id":RUN_ID,"plan_status":"incomplete","stop_reason":reason})
    if not (output/"formal_frame_outcomes.csv").exists(): _csv_x(output/"formal_frame_outcomes.csv", list(state.get("confirmation_rows", [])))
    if not (output/"formal_transcript.jsonl").exists(): _write_x(output/"formal_transcript.jsonl", b"".join(canonical_event(e) for e in state.get("confirmation_events", [])))
    if not (output/"formal_codebook_manifest.json").exists(): _json_x(output/"formal_codebook_manifest.json", {"entries":[]})
    if not (output/"formal_policy_manifest.json").exists(): _json_x(output/"formal_policy_manifest.json", {"policies":state.get("policies", []),"constructor_probes":state.get("probes", []),"calibrations":state.get("calibrations", {}),"development_outcomes":state.get("development_outcomes", {})})
    if not (output/"formal_run_manifest.json").exists(): _json_x(output/"formal_run_manifest.json", {"run_id":RUN_ID,"run_status":"non_promoted","stop_reason":reason,"exception":{"class":type(exc).__name__,"message":str(exc)},"provenance":provenance,"utc_started":started,"utc_finished":_now(),"artifacts":_artifact_hashes(output)})
    if not (output/"formal_qualification_report.json").exists(): _json_x(output/"formal_qualification_report.json", {"run_id":RUN_ID,"run_status":"non_promoted","stop_reason":reason,"promotion_gates":{},"formal_run_manifest_sha256":_sha((output/"formal_run_manifest.json").read_bytes())})

def create_plan(output: Path) -> dict[str, Any]:
    """Create the sole reviewable pre-run artifact; it performs no method calls."""
    if output.exists(): raise FileExistsError("fresh output directory required for plan")
    provenance = _provenance(); output.mkdir(parents=True)
    plan = _plan(provenance); _json_x(output / "pre_run_plan.json", plan)
    return plan

def _validate_plan(plan: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    expected=_expected_plan_fields()
    for key in ("run_id","method","dimension","mapping","frame_len_symbols","seeds","caps","calibration_ids","development_execution_order","confirmation_execution_order","policy_hashes","screening_manifest_sha256","synthetic_generation_sha256","failure_finalizer"):
        if plan.get(key)!=expected.get(key): raise ValueError(f"plan mismatch: {key}")
    dev_seeds, conf_seeds = plan.get("development_toeplitz_seeds",{}), plan.get("confirmation_toeplitz_seeds",{})
    expected_dev = {f"{policy['policy_id']}|{frame}" for policy in policy_grid() for frame in plan["development_execution_order"]}
    if set(dev_seeds)!=expected_dev or set(conf_seeds)!=set(plan["confirmation_execution_order"]): raise ValueError("seed keys")
    if len(dev_seeds)!=576 or len(conf_seeds)!=64: raise ValueError("seed count")
    from ..formal_ir.shared import locked_seed_bits
    seed_ids=[]
    for record in list(dev_seeds.values()) + list(conf_seeds.values()): locked_seed_bits(record, SEED_BITS); seed_ids.append(record["seed_id"])
    if len(set(seed_ids))!=640: raise ValueError("global seed uniqueness")
    _verify_provenance(plan.get("provenance", {}), _provenance())
    return dict(dev_seeds), dict(conf_seeds)

def _gate(rows: list[dict[str,Any]]) -> dict[str,Any]:
    good=sum(row.get("status")=="verified_success" for row in rows); bad=sum(row.get("status") not in GATE_STATUSES for row in rows)
    return {"requested":32,"verified_success":good,"unclassified_internal_provenance_accounting_failures":bad,"promoted":good >= 31 and bad == 0}

def run(output: Path, *, method_runner: Callable[...,dict[str,Any]]=run_ldpc_formal_v2, constructor_probe: Callable[[],list[dict[str,Any]]]=probe_constructors) -> None:
    if not output.is_dir() or {p.name for p in output.iterdir()} != {"pre_run_plan.json"}: raise ValueError("execute requires exactly one reviewed pre_run_plan.json")
    plan_bytes=(output/"pre_run_plan.json").read_bytes(); plan=json.loads(plan_bytes); _validate_plan(plan)
    provenance=dict(plan["provenance"]); started=_now(); monotonic=time.monotonic(); state: dict[str, Any]={"policies":[],"probes":[],"calibrations":{},"development_outcomes":{},"confirmation_rows":[],"confirmation_events":[]}
    try:
        probes=constructor_probe(); state["probes"]=probes
        if len(probes)!=3 or not all(item.get("supported") for item in probes): raise RuntimeError("required v2 decoder constructor unavailable")
        codebook=materialize_selected_codebooks(output, manifest=screening_manifest(), allow_plan_only=True, manifest_filename="formal_codebook_manifest.json")
        verify_selected_codebooks(output,codebook)
        entries={(e["rate_id"],e["plane_id"]):e for e in codebook["entries"]}; raw={key:(output/"codebooks"/entry["filename"]).read_bytes() for key,entry in entries.items()}
        batches=_batches(); calibrations=_calibrations(batches); policies=policy_grid(); dev: dict[str,list[dict[str,Any]]]={p["policy_id"]:[] for p in policies}; state.update({"calibrations":calibrations,"policies":policies,"development_outcomes":dev})
        for frame in plan["development_execution_order"]:
            dataset,label,index,_=_dataset_and_index(frame); a,b=batches[f"{label}_calibration"]
            for policy in policies:
                if time.monotonic()-monotonic >= 1800: raise TimeoutError("complete_run_s")
                seed=plan["development_toeplitz_seeds"][f"{policy['policy_id']}|{frame}"]
                result=method_runner(a[index],b[index],dimension=Q,frozen_calibration=calibrations[label],frozen_policy=policy,codebook_entries=entries,codebook_bytes=raw,screening_manifest=codebook["screening_manifest"],dataset_id=dataset,frame_id=frame,mapping="gray",locked_seed=seed)
                row=dict(result["outcome"]); row.update({"phase":"development","plan_frame_id":frame,"stratum_p":_dataset_and_index(frame)[3],"runtime_ns":int(round(float(row["runtime_s"])*1e9))}); dev[policy["policy_id"]].append(row)
        selection=select_global_policy(dev); frozen=selection["selected_policy"]
        policy_manifest={"policies":policies,"constructor_probes":probes,"calibrations":calibrations,"calibration_sha256":{k:_sha(_compact(v)) for k,v in calibrations.items()},"development_outcomes":dev,"selection":selection,"selected_policy_sha256":frozen["policy_id"],"v1_golden_hash_snapshot":_v1_golden_hash_snapshot()}
        _json_x(output/"formal_policy_manifest.json",policy_manifest)
        rows=[]; events=[]
        for frame in plan["confirmation_execution_order"]:
            if time.monotonic()-monotonic >= 1800: raise TimeoutError("complete_run_s")
            dataset,label,index,p=_dataset_and_index(frame); a,b=batches[f"{label}_confirmation"]
            result=method_runner(a[index],b[index],dimension=Q,frozen_calibration=calibrations[label],frozen_policy=frozen,codebook_entries=entries,codebook_bytes=raw,screening_manifest=codebook["screening_manifest"],dataset_id=dataset,frame_id=frame,mapping="gray",locked_seed=plan["confirmation_toeplitz_seeds"][frame])
            group=b"".join(canonical_event(event) for event in result["events"]); row=dict(result["outcome"]); row.update({"stratum_p":p,"qualification_role":"confirmation","plan_frame_id":frame,"transcript_bytes_len":len(group),"transcript_bytes_sha256":_sha(group)}); rows.append(row); events.extend(result["events"]); state["confirmation_rows"].append(row); state["confirmation_events"].extend(result["events"])
        _write_x(output/"formal_transcript.jsonl",b"".join(canonical_event(e) for e in events)); _csv_x(output/"formal_frame_outcomes.csv",rows)
        gates={f"p{int(p*100):02d}":_gate([row for row in rows if row["stratum_p"]==p]) for p in (.01,.02)}
        manifest={"run_id":RUN_ID,"run_status":"completed","provenance":provenance,"utc_started":started,"utc_finished":_now(),"plan_sha256":_sha((output/"pre_run_plan.json").read_bytes()),"artifacts":_artifact_hashes(output),"selected_policy_sha256":frozen["policy_id"],"outcome_count":len(rows),"verification_invoked_count":sum(bool(r["verification_invoked"]) for r in rows)}
        _json_x(output/"formal_run_manifest.json",manifest)
        _json_x(output/"formal_qualification_report.json",{"run_id":RUN_ID,"run_status":"completed","promotion_gates":gates,"promoted":all(g["promoted"] for g in gates.values()),"formal_run_manifest_sha256":_sha((output/"formal_run_manifest.json").read_bytes())})
        if (output/"pre_run_plan.json").read_bytes() != plan_bytes: raise RuntimeError("pre-run plan bytes changed during execution")
    except BaseException as exc:
        _finalize(output,exc,started,provenance,state); raise

def _rows(path:Path)->list[dict[str,str]]:
    with path.open(encoding="utf-8",newline="") as handle:return list(csv.DictReader(handle))
def _bool(s:str)->bool:return s.lower() in {"true","1"}

def verify(output: Path) -> None:
    actual={p.name for p in output.iterdir()}
    if not set(ARTIFACTS).issubset(actual) or not actual.issubset(TOP_LEVEL): raise ValueError("seven-artifact top-level contract")
    plan=json.loads((output/"pre_run_plan.json").read_text()); manifest=json.loads((output/"formal_run_manifest.json").read_text()); report=json.loads((output/"formal_qualification_report.json").read_text())
    if [plan.get("run_id"),manifest.get("run_id"),report.get("run_id")] != [RUN_ID]*3: raise ValueError("run id")
    if report.get("formal_run_manifest_sha256") != _sha((output/"formal_run_manifest.json").read_bytes()): raise ValueError("report hash")
    if manifest.get("run_status")=="non_promoted": print(json.dumps({"verified":True,"run_status":"non_promoted"})); return
    if manifest.get("plan_sha256") != _sha((output / "pre_run_plan.json").read_bytes()): raise ValueError("manifest plan hash")
    if manifest.get("artifacts") != _artifact_hashes(output): raise ValueError("manifest artifact DAG")
    dev_seeds, conf_seeds = _validate_plan(plan)
    if manifest.get("provenance") != plan.get("provenance"): raise ValueError("manifest provenance")
    codebook=json.loads((output/"formal_codebook_manifest.json").read_text()); verify_selected_codebooks(output,codebook)
    policy=json.loads((output/"formal_policy_manifest.json").read_text())
    probes=policy.get("constructor_probes")
    if not isinstance(probes,list) or [(x.get("osd_method"),x.get("osd_order"),x.get("dependency_version"),x.get("supported")) for x in probes] != [("OSD_0",0,"2.4.1",True),("OSD_CS",1,"2.4.1",True),("OSD_CS",2,"2.4.1",True)]: raise ValueError("constructor probes")
    if policy.get("policies")!=policy_grid() or set(policy.get("development_outcomes",{}))!={p["policy_id"] for p in policy_grid()}: raise ValueError("policy grid")
    calibrations=_calibrations(_batches())
    if policy.get("calibrations")!=calibrations or policy.get("calibration_sha256")!={k:_sha(_compact(v)) for k,v in calibrations.items()}: raise ValueError("calibration reconstruction")
    if policy.get("v1_golden_hash_snapshot") != _v1_golden_hash_snapshot(): raise ValueError("v1 golden snapshot")
    for policy_id, values in policy["development_outcomes"].items():
        if len(values)!=64 or [row.get("frame_id") for row in values] != plan["development_execution_order"]: raise ValueError("all policies development order")
        for row in values:
            frame=row.get("frame_id"); _,_,_,p=_dataset_and_index(str(frame))
            if row.get("policy_id")!=policy_id or row.get("phase")!="development" or row.get("plan_frame_id")!=frame or row.get("stratum_p")!=p or row.get("verification_seed_id")!=dev_seeds[f"{policy_id}|{frame}"]["seed_id"] or not row.get("attempted") or not row.get("denominator_included") or row.get("status") not in GATE_STATUSES: raise ValueError("development row binding")
    if policy.get("selection")!=select_global_policy(policy["development_outcomes"]) or policy.get("selected_policy_sha256")!=policy["selection"]["selected_policy"]["policy_id"]: raise ValueError("global policy freeze")
    if manifest.get("selected_policy_sha256")!=policy["selected_policy_sha256"]: raise ValueError("manifest selected policy")
    rows=_rows(output/"formal_frame_outcomes.csv")
    if len(rows)!=64 or [r["frame_id"] for r in rows]!=plan["confirmation_execution_order"]: raise ValueError("confirmation 64 only/order")
    events=[json.loads(x) for x in (output/"formal_transcript.jsonl").read_bytes().splitlines()]; cursor=0; grouped={.01:[],.02:[]}
    for row in rows:
        if row["policy_id"]!=policy["selected_policy_sha256"] or not _bool(row["attempted"]) or not _bool(row["denominator_included"]) or not _bool(row["verification_invoked"]): raise ValueError("outcome policy/denominator")
        if row["verification_seed_id"] != conf_seeds[row["frame_id"]]["seed_id"]: raise ValueError("confirmation seed binding")
        key=f"{row['dataset_id']}:{row['frame_id']}"; start=cursor
        while cursor<len(events) and events[cursor]["frame_key"]==key: cursor+=1
        blob=b"".join(canonical_event(e) for e in events[start:cursor]); summary=transcript_summary(events[start:cursor])
        if _sha(blob)!=row["transcript_bytes_sha256"] or str(len(blob))!=row["transcript_bytes_len"] or summary["transcript_sha256"]!=row["transcript_sha256"]: raise ValueError("transcript")
        grouped[float(row["stratum_p"])].append(row)
    if cursor!=len(events) or b"".join(canonical_event(e) for e in events)!=(output/"formal_transcript.jsonl").read_bytes(): raise ValueError("transcript bytes")
    if {p:len(grouped[p]) for p in (.01,.02)} != {.01:32,.02:32}: raise ValueError("confirmation stratum denominator")
    gates={f"p{int(p*100):02d}":_gate(grouped[p]) for p in (.01,.02)}
    if report.get("promotion_gates")!=gates or report.get("promoted")!=all(g["promoted"] for g in gates.values()): raise ValueError("31/32 gates")
    print(json.dumps({"verified":True,"run_id":RUN_ID,"outcomes":64},sort_keys=True))

def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--output-dir",type=Path,required=True); mode=parser.add_mutually_exclusive_group(required=True); mode.add_argument("--plan-only",action="store_true"); mode.add_argument("--execute",action="store_true"); mode.add_argument("--verify",action="store_true"); args=parser.parse_args()
    if args.plan_only: create_plan(args.output_dir)
    elif args.execute: run(args.output_dir)
    else: verify(args.output_dir)
if __name__=="__main__": main()
