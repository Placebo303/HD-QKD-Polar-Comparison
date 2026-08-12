"""Two-step, immutable synthetic qualification package for formal LDPC v3.

This module deliberately has no default output path.  Its private injection
points are test-only; the command line always uses the production decoder.
"""
from __future__ import annotations

import argparse, csv, hashlib, json, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from ..formal_ir import ldpc_v3, ldpc_v3_ttbin_data as data
from ..formal_ir.codebook_long_v3 import canonical_matrix_bytes, generate_master, prefix_rows
from ..formal_ir.shared import FORMAL_ARTIFACTS, canonical_event, materialize_seed_record, sha256_bytes, transcript_summary
from ..utils.bitops import symbols_to_bits

RUN_ID = "binary_ldpc_v3_phase6b_synthetic_v1"
ARTIFACTS = FORMAL_ARTIFACTS
SEED_BITS = 2623
ROOT_SEEDS = {"calibrated_alice": 2026072601, "calibrated_error": 2026072602,
              "stress_125_alice": 2026072603, "stress_125_error": 2026072604,
              "execution_order": 2026072605}
GATE_FAILURES = {"preflight_unavailable", "invalid_input", "unsupported_domain", "backend_unavailable", "decoder_error", "syndrome_inconsistent", "aborted_resource_limit"}

def _compact(v: Any) -> bytes: return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
def _sha(v: bytes) -> str: return hashlib.sha256(v).hexdigest()
def _now() -> str: return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
def _write_x(path: Path, value: bytes) -> None:
    with path.open("xb") as h: h.write(value)
def _json_x(path: Path, value: Any) -> None: _write_x(path, json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False).encode("ascii") + b"\n")
def _csv_x(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = sorted({k for r in rows for k in r}) or ["status"]
    with path.open("x", encoding="utf-8", newline="") as h:
        w = csv.DictWriter(h, fieldnames=fields); w.writeheader()
        for row in rows: w.writerow({k: json.dumps(v, sort_keys=True) if isinstance(v, (dict, list)) else v for k,v in row.items()})
def _source_hashes() -> dict[str, str]:
    root = Path(__file__).resolve().parents[1]
    return {name: _sha((root / rel).read_bytes()) for name, rel in {
        "ldpc_v3.py":"formal_ir/ldpc_v3.py", "ldpc_v3_ttbin_data.py":"formal_ir/ldpc_v3_ttbin_data.py",
        "codebook_long_v3.py":"formal_ir/codebook_long_v3.py", "shared.py":"formal_ir/shared.py",
        "runner.py":"cli/run_ldpc_v3_synthetic_qualification.py", "verifier.py":"cli/verify_ldpc_v3_synthetic_qualification.py"}.items()}
def _codebook_manifest() -> dict[str, Any]:
    entries=[]
    for plane, candidate in enumerate(ldpc_v3.CANDIDATE_IDS):
        for prefix, rows in prefix_rows(ldpc_v3.N).items():
            raw=canonical_matrix_bytes(generate_master(ldpc_v3.N, plane, candidate)[:rows])
            entries.append({"plane_id":plane,"candidate_id":candidate,"prefix_id":prefix,"sha256":_sha(raw),"bytes":len(raw)})
    out={"method":ldpc_v3.METHOD,"selection_binding_sha256":ldpc_v3.SELECTION_BINDING_SHA256,"entries":entries}; out["manifest_sha256"]=_sha(_compact(out)); return out
def _synthetic_pair(stratum: str, index: int, calibration: Mapping[str, Any]) -> tuple[np.ndarray,np.ndarray]:
    if stratum not in ("calibrated", "stress_125") or not 0 <= index < 32: raise ValueError("synthetic identity")
    p=np.asarray([float(x["p_hat"]) for x in calibration["planes"]], dtype=float)
    if stratum == "stress_125": p=np.minimum(.49, 1.25*p)
    a=np.random.Generator(np.random.PCG64(ROOT_SEEDS[f"{stratum}_alice"])).integers(0,1024,size=(32,256),dtype=np.int64)[index]
    bits=symbols_to_bits(a,1024,"gray").astype(np.uint8)
    # Fixed call order: one generator, plane 0..9, frame-major (32,256) draws.
    rng=np.random.Generator(np.random.PCG64(ROOT_SEEDS[f"{stratum}_error"]))
    masks=np.empty((32,256,10),dtype=np.uint8)
    for plane in range(10): masks[:,:,plane]=(rng.random((32,256)) < p[plane]).astype(np.uint8)
    bb=bits ^ masks[index]
    words=(bb.astype(np.int64) * (1 << np.arange(9,-1,-1))).sum(axis=1)
    # inverse Gray code, vectorised over q=1024 words
    natural=words.copy()
    for shift in (1,2,4,8): natural ^= natural >> shift
    return a, natural
def _order() -> list[str]:
    ids=[f"{s}:f{i:03d}" for s in ("calibrated","stress_125") for i in range(32)]
    return [ids[int(i)] for i in np.random.Generator(np.random.PCG64(ROOT_SEEDS["execution_order"])).permutation(64)]
def _base_plan(lock: Mapping[str,Any]) -> dict[str,Any]:
    data.verify_locked_data(lock); cal=lock["calibration"]
    plan={"run_id":RUN_ID,"method":ldpc_v3.METHOD,"dimension":1024,"mapping":"gray","frame_len_symbols":256,
          "source_manifest_sha256":lock["source_manifest_sha256"],"locked_data_sha256":lock["lock_sha256"],"locked_data":dict(lock),"frozen_calibration":cal,
          "selected_candidate_binding_sha256":ldpc_v3.SELECTION_BINDING_SHA256,"source_sha256":_source_hashes(),
          "caps":{"per_frame":ldpc_v3.DEFAULT_CAPS,"complete_run_s":1800},"generator_contract":{"algorithm":"PCG64","root_seeds":ROOT_SEEDS,"mask_call_order":"stratum, plane 0..9, rng.random((32,256))","gray_inverse":"xor shifts 1,2,4,8"},
          "execution_order":_order(),"failure_finalizer":"exclusive_preserve_completed_rows_six_artifacts"}
    plan["toeplitz_seeds"]={key:materialize_seed_record(SEED_BITS) for key in plan["execution_order"]}
    return plan
def _seal_plan(plan: dict[str, Any]) -> dict[str, Any]:
    plan["plan_sha256"]=_sha(_compact({k:v for k,v in plan.items() if k != "plan_sha256"})); return plan
def create_plan(output: Path, lock: Mapping[str,Any], *, _test_only: bool=False) -> dict[str,Any]:
    if output.exists(): raise FileExistsError("fresh output directory required")
    plan=_base_plan(lock); plan["_test_only"] = bool(_test_only); _seal_plan(plan)
    output.mkdir(parents=True); _json_x(output/ARTIFACTS[0],plan); return plan
def _gate(rows: list[dict[str,Any]]) -> dict[str,Any]:
    success=sum(r.get("status")=="verified_success" for r in rows); bad=sum(r.get("status") in GATE_FAILURES or r.get("status") not in {"verified_success","verify_failed","decode_failed"} for r in rows)
    return {"denominator":sum(bool(r.get("denominator_included")) for r in rows),"verified_success":success,"unclassified_internal_provenance_accounting_failures":bad,"promoted":len(rows)==32 and sum(bool(r.get("denominator_included")) for r in rows)==32 and success>=31 and bad==0}
def _artifact_hashes(output:Path) -> dict[str,str]:
    return {name:_sha((output/name).read_bytes()) for name in (ARTIFACTS[0],ARTIFACTS[1],ARTIFACTS[2],ARTIFACTS[4])}
def _manifest(status:str, plan_hash:str, output:Path, count:int, reason:str="") -> dict[str,Any]:
    return {"run_id":RUN_ID,"schema":"binary_ldpc_v3_phase6b_run_manifest_v1","run_status":status,"stop_reason":reason,"plan_sha256":plan_hash,"artifacts":_artifact_hashes(output),"outcome_count":count,"decoder_reexecution":False}
def _report(status:str, manifest_hash:str, gates:dict[str,Any], reason:str="") -> dict[str,Any]:
    return {"run_id":RUN_ID,"schema":"binary_ldpc_v3_phase6b_report_v1","run_status":status,"stop_reason":reason,"promotion_gates":gates,"promoted":status=="completed" and all(x["promoted"] for x in gates.values()),"formal_run_manifest_sha256":manifest_hash,"decoder_reexecution":False}
def _finalize(output:Path, exc:BaseException, plan:Mapping[str,Any]|None, rows:list[dict[str,Any]], events:list[Mapping[str,Any]]) -> None:
    reason=f"{type(exc).__name__}: {exc}"
    if not (output/ARTIFACTS[1]).exists(): _csv_x(output/ARTIFACTS[1],rows)
    if not (output/ARTIFACTS[2]).exists(): _write_x(output/ARTIFACTS[2],b"".join(canonical_event(e) for e in events))
    if not (output/ARTIFACTS[4]).exists(): _json_x(output/ARTIFACTS[4],_codebook_manifest())
    if not (output/ARTIFACTS[3]).exists(): _json_x(output/ARTIFACTS[3],_manifest("non_promoted",_sha((output/ARTIFACTS[0]).read_bytes()),output,len(rows),reason))
    if not (output/ARTIFACTS[5]).exists(): _json_x(output/ARTIFACTS[5],_report("non_promoted",_sha((output/ARTIFACTS[3]).read_bytes()),{s:_gate([r for r in rows if r.get("stratum")==s]) for s in ("calibrated","stress_125")},reason))
def run(output:Path, *, method_runner:Callable[...,dict[str,Any]]=ldpc_v3.run_ldpc_formal_v3, _test_only:bool=False) -> None:
    if not output.is_dir() or {p.name for p in output.iterdir()} != {ARTIFACTS[0]}: raise ValueError("execute requires exactly one reviewed pre_run_plan.json")
    plan=json.loads((output/ARTIFACTS[0]).read_text());
    if bool(plan.get("_test_only")) != bool(_test_only): raise ValueError("test-only plan rejected")
    if plan.get("plan_sha256") != _sha(_compact({k:v for k,v in plan.items() if k != "plan_sha256"})): raise ValueError("plan hash")
    rows=[]; events=[]; started=time.monotonic()
    try:
        if not _test_only: _source_hashes() == plan["source_sha256"] or (_ for _ in ()).throw(ValueError("source hashes"))
        _json_x(output/ARTIFACTS[4],_codebook_manifest())
        for key in plan["execution_order"]:
            if time.monotonic()-started >= 1800: raise TimeoutError("complete_run_s")
            s, fid=key.split(":f"); a,b=_synthetic_pair(s,int(fid),plan["frozen_calibration"])
            result=method_runner(a,b,frozen_calibration=plan["frozen_calibration"],locked_seed=plan["toeplitz_seeds"][key],dataset_id=f"synthetic_{s}",frame_id=key,_caps=plan["caps"]["per_frame"])
            row=dict(result["outcome"]); group=b"".join(canonical_event(e) for e in result["events"]); row.update({"stratum":s,"plan_frame_id":key,"transcript_bytes_len":len(group),"transcript_bytes_sha256":_sha(group),"alice_sha256":_sha(np.asarray(a,dtype="<i8").tobytes()),"bob_sha256":_sha(np.asarray(b,dtype="<i8").tobytes())}); rows.append(row); events.extend(result["events"])
        _write_x(output/ARTIFACTS[2],b"".join(canonical_event(e) for e in events)); _csv_x(output/ARTIFACTS[1],rows)
        gates={s:_gate([r for r in rows if r["stratum"]==s]) for s in ("calibrated","stress_125")}
        _json_x(output/ARTIFACTS[3],_manifest("completed",_sha((output/ARTIFACTS[0]).read_bytes()),output,len(rows)))
        _json_x(output/ARTIFACTS[5],_report("completed",_sha((output/ARTIFACTS[3]).read_bytes()),gates))
    except BaseException as exc:
        _finalize(output,exc,plan,rows,events); raise
def main()->None:
    p=argparse.ArgumentParser(); p.add_argument("--output-dir",type=Path,required=True); p.add_argument("--mode",choices=("prepare","execute"),required=True); p.add_argument("--lock-json",type=Path)
    a=p.parse_args()
    if a.mode=="prepare":
        if a.lock_json is None: p.error("--lock-json required for prepare")
        create_plan(a.output_dir,json.loads(a.lock_json.read_text()))
    else: run(a.output_dir)
if __name__=="__main__": main()
