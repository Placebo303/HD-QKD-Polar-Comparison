"""Non-resumable artifact runner for the frozen long-v3 development grid."""
from __future__ import annotations

import argparse, csv, hashlib, importlib.metadata, json, platform, sys, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from ..formal_ir.codebook_long_v3 import BLOCK_LENGTHS, CANDIDATE_IDS, PLANE_IDS, candidate_manifest
from ..formal_ir.long_v3_development import ROLE, canonical_development_policy, evaluate_candidate, generate_sacrificed_development, select_candidate

RUN_ID = "20260726_v1_binary_ldpc_long_v3_development"
ARTIFACTS = ("pre_run_plan.json", "long_v3_candidate_manifest.json", "development_outcomes.csv", "development_selections.json", "development_run_manifest.json", "development_report.json")
FIELDS = ("n","plane_id","candidate_id","stratum_id","frame_id","attempted","status","terminal_prefix_id","rounds_attempted","syndrome_bits_disclosed","exact_match","policy_id","p_hat","backend_identity","runtime_s","role","source_sha256")

def _compact(value: Any) -> bytes: return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
def _sha(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def _now() -> str: return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
def _write(path: Path, data: bytes) -> None:
    with path.open("xb") as f: f.write(data)
def _json(path: Path, value: Mapping[str, Any]) -> None: _write(path, _compact(value))
def _self(value: dict[str, Any], key: str) -> dict[str, Any]: return {**value, key: _sha(_compact(value))}
def _code_hashes() -> dict[str, str]:
    root = Path(__file__).resolve().parents[1]
    return {name: _sha((root / area / file).read_bytes()) for name, area, file in (
        ("codebook_long_v3.py", "formal_ir", "codebook_long_v3.py"),
        ("long_v3_development.py", "formal_ir", "long_v3_development.py"),
        ("run_ldpc_long_v3_development.py", "cli", "run_ldpc_long_v3_development.py"),
        ("verify_ldpc_long_v3_development.py", "cli", "verify_ldpc_long_v3_development.py"))}

def _plan(*, test_only: bool) -> dict[str, Any]:
    lengths = [256] if test_only else list(BLOCK_LENGTHS); planes = [0] if test_only else list(PLANE_IDS)
    base = {"schema_version":"binary_ldpc_long_v3_development_plan_v1", "run_id":"test_only_binary_ldpc_long_v3_development" if test_only else RUN_ID,
        "role":ROLE,"test_only":test_only,
        "grid":{"block_lengths":lengths,"plane_ids":planes,"candidate_ids":list(CANDIDATE_IDS),"stratum_ids":["p001","p002"],"frames_per_stratum":16,"execution_order":"n,plane_id,candidate_id,stratum_id,frame_index"},
        "policies":{str(n):canonical_development_policy(n) for n in lengths}, "candidate_manifest_sha256":_sha(_compact(candidate_manifest())),
        "backend_requirement":"test_injected" if test_only else "ldpc==2.4.1", "internal_elapsed_cap_s":30 if test_only else 600,
        "required_external_timeout_s":60 if test_only else 660, "expected_outcome_count":len(lengths)*len(planes)*4*2*16,
        "expected_selection_count":len(lengths)*len(planes), "code_sha256":_code_hashes()}
    return _self(base, "plan_sha256")

def _valid_plan(plan: Mapping[str, Any], *, test_only: bool) -> dict[str, Any]:
    if not isinstance(plan, dict) or plan.get("plan_sha256") != _sha(_compact({k:v for k,v in plan.items() if k != "plan_sha256"})): raise ValueError("plan self-hash")
    expected = _plan(test_only=test_only)
    if plan != expected: raise ValueError("plan does not match frozen current production/test plan")
    return dict(plan)

def _prepare(output_dir: Path, *, test_only: bool) -> dict[str, Any]:
    if output_dir.exists(): raise FileExistsError("prepare requires a fresh output directory")
    output_dir.mkdir(parents=True); plan = _plan(test_only=test_only); _json(output_dir / ARTIFACTS[0], plan); return plan
def prepare_plan(output_dir: Path) -> dict: return _prepare(output_dir, test_only=False)
def _prepare_test_plan(output_dir: Path) -> dict: return _prepare(output_dir, test_only=True)

def _csv(rows: list[Mapping[str, Any]]) -> bytes:
    import io
    stream = io.StringIO(newline=""); writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n", extrasaction="raise")
    writer.writeheader()
    for row in rows:
        if set(row) != set(FIELDS): raise ValueError("outcome row schema")
        value = {key: ("true" if row[key] else "false") if key in {"attempted","exact_match"} else repr(float(row[key])) if key in {"p_hat","runtime_s"} else row[key] for key in FIELDS}
        writer.writerow(value)
    return stream.getvalue().encode("utf-8")

def _aggregate(rows: list[Mapping[str, Any]], selections: list[Mapping[str, Any]]) -> dict[str, Any]:
    def group(key: str) -> dict[str, Any]:
        out={}
        for value in sorted({str(r[key]) for r in rows}, key=lambda x:int(x) if x.isdigit() else x):
            part=[r for r in rows if str(r[key])==value]; counts={}
            for r in part: counts[r["status"]]=counts.get(r["status"],0)+1
            out[value]={"status_counts":dict(sorted(counts.items())),"exact_success_count":sum(r["status"]=="development_exact_success" for r in part),"total_syndrome_bits_disclosed":sum(r["syndrome_bits_disclosed"] for r in part)}
        return out
    terminal={}
    for r in rows: terminal[r["terminal_prefix_id"]]=terminal.get(r["terminal_prefix_id"],0)+1
    return {"by_length":group("n"),"by_stratum":group("stratum_id"),"terminal_prefix_counts":dict(sorted(terminal.items()))}

def _finalize(output: Path, plan: Mapping[str, Any], rows: list[dict[str, Any]], selections: list[dict[str, Any]], *, status: str, stop_reason: str, started: str, elapsed: float, test_only: bool) -> dict[str, Any]:
    manifest_bytes = _compact(candidate_manifest()); _write(output / ARTIFACTS[1], manifest_bytes)
    outcomes = _csv(rows); _write(output / ARTIFACTS[2], outcomes)
    select_base={"schema_version":"binary_ldpc_long_v3_development_selections_v1","run_id":plan["run_id"],"role":ROLE,"test_only":test_only,"plan_sha256":plan["plan_sha256"],"outcomes_sha256":_sha(outcomes),"selection_count":len(selections),"selections":selections}
    selection_doc=_self(select_base,"selections_sha256"); _json(output / ARTIFACTS[3], selection_doc)
    index={name:{"sha256":_sha((output/name).read_bytes()),"bytes":(output/name).stat().st_size} for name in ARTIFACTS[:4]}
    run_base={"schema_version":"binary_ldpc_long_v3_development_manifest_v1","run_id":plan["run_id"],"role":ROLE,"test_only":test_only,"status":status,"stop_reason":stop_reason,"utc_start":started,"utc_end":_now(),"actual_argv":["<test-helper>"] if test_only else list(sys.argv),"backend_identity":"test_injected" if test_only else "ldpc==2.4.1","python_version":platform.python_version(),"numpy_version":np.__version__,"dependency_version":"test_injected" if test_only else "2.4.1","process_elapsed_s":float(elapsed),"expected_outcome_count":plan["expected_outcome_count"],"observed_outcome_count":len(rows),"expected_selection_count":plan["expected_selection_count"],"observed_selection_count":len(selections),"code_sha256":plan["code_sha256"],"artifact_index":index}
    run_doc=_self(run_base,"manifest_content_sha256"); _json(output / ARTIFACTS[4],run_doc)
    selected=[{"n":x["n"],"plane_id":x["plane_id"],"candidate_id":x["selected_candidate_id"],"selection_sha256":x["selection_sha256"]} for x in selections]
    report_base={"schema_version":"binary_ldpc_long_v3_development_report_v1","run_id":plan["run_id"],"role":ROLE,"test_only":test_only,"status":status,"stop_reason":stop_reason,"observed_outcome_count":len(rows),"observed_selection_count":len(selections),"aggregates":_aggregate(rows,selections),"selected_candidates":selected,"development_only_not_qualification_or_promotion":True,"plan_sha256":plan["plan_sha256"],"run_manifest_sha256":_sha((output/ARTIFACTS[4]).read_bytes())}
    report=_self(report_base,"report_content_sha256"); _json(output / ARTIFACTS[5],report); return run_doc

def _execute(output_dir: Path, decoder_factory: Callable[..., Any] | None, *, test_only: bool, clock: Callable[[],float]) -> dict[str, Any]:
    if not output_dir.is_dir() or {p.name for p in output_dir.iterdir()} != {ARTIFACTS[0]}: raise ValueError("execute requires exactly one plan artifact")
    plan=_valid_plan(json.loads((output_dir/ARTIFACTS[0]).read_text(encoding="utf-8")),test_only=test_only)
    if not test_only:
        try:
            if importlib.metadata.version("ldpc") != "2.4.1": raise ValueError("pinned backend unavailable")
        except importlib.metadata.PackageNotFoundError as exc: raise ValueError("pinned backend unavailable") from exc
    started=_now(); tick=clock(); rows=[]; selections=[]; status="development_run_completed"; reason="completed"
    try:
        data={(n,p,s):generate_sacrificed_development(n,p,.01 if s=="p001" else .02) for n in plan["grid"]["block_lengths"] for p in plan["grid"]["plane_ids"] for s in plan["grid"]["stratum_ids"]}
        for n in plan["grid"]["block_lengths"]:
          for plane in plan["grid"]["plane_ids"]:
           group=[]
           for candidate in plan["grid"]["candidate_ids"]:
            for stratum in plan["grid"]["stratum_ids"]:
             if clock()-tick > plan["internal_elapsed_cap_s"]: raise TimeoutError("internal cap")
             d=data[(n,plane,stratum)]; result=evaluate_candidate(d["alice_frames"],d["bob_frames"],n=n,plane_id=plane,candidate_id=candidate,p_hat=d["p_hat"],stratum_id=stratum,frame_ids=d["frame_ids"],decoder_factory=decoder_factory)
             for row in result: row.update(role=ROLE,source_sha256=d["source_sha256"])
             rows.extend(result); group.extend(result)
             if clock()-tick > plan["internal_elapsed_cap_s"]: raise TimeoutError("internal cap")
           if len(group)==128: selections.append(select_candidate(group))
        if len(rows)!=plan["expected_outcome_count"] or len(selections)!=plan["expected_selection_count"] or (not test_only and any(r["backend_identity"]!="ldpc==2.4.1" or r["status"]=="development_backend_unavailable" for r in rows)): raise RuntimeError("completion accounting")
    except Exception as exc:
        status="development_run_failed"; reason="internal_cap_exceeded" if isinstance(exc,TimeoutError) else f"exception:{type(exc).__name__}:{exc}"
    return _finalize(output_dir,plan,rows,selections,status=status,stop_reason=reason,started=started,elapsed=clock()-tick,test_only=test_only)

def execute_plan(output_dir: Path) -> dict: return _execute(output_dir,None,test_only=False,clock=time.perf_counter)
def _execute_test_plan(output_dir: Path, decoder_factory: Callable[...,Any], *, clock: Callable[[],float]=time.perf_counter) -> dict: return _execute(output_dir,decoder_factory,test_only=True,clock=clock)

def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--output-dir",type=Path,required=True); parser.add_argument("--mode",choices=("prepare","execute"),required=True); args=parser.parse_args()
    if args.mode=="prepare": prepare_plan(args.output_dir)
    else: execute_plan(args.output_dir)
    return 0
if __name__ == "__main__": raise SystemExit(main())
