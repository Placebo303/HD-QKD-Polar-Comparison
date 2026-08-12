"""Immutable fresh synthetic qualification package for ``ldpc_formal_v4``.

The command line has no test switches.  Private helpers are deliberately
prefixed and are used only by the focused test module.
"""
from __future__ import annotations

import argparse, csv, hashlib, importlib.metadata, json, secrets, time
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from . import verify_ldpc_v4_development_v2 as development_verify
from ..formal_ir import ldpc_v4_development
from ..formal_ir.codebook_v4 import candidate_manifest
from ..formal_ir.ldpc_v4 import METHOD, run_ldpc_formal_v4
from ..formal_ir.ldpc_v4_channel import build_adjacent_channel_model
from ..formal_ir.shared import canonical_event, locked_seed_bits, seed_record
from ..utils.bitops import symbols_to_bits

RUN_ID = "binary_ldpc_v4_synthetic_qualification_v2"
STRATA = ("adjacent_nominal", "adjacent_stress_125")
FRAME_COUNT = 128
SEED_BITS = 2623
ARTIFACTS = ("pre_run_plan.json", "formal_frame_outcomes.csv", "formal_transcript.jsonl", "formal_codebook_manifest.json", "formal_selection_manifest.json", "formal_channel_model.json", "formal_run_manifest.json", "formal_qualification_report.json")
FORBIDDEN = {"invalid_input", "unsupported_domain", "backend_unavailable", "aborted_resource_limit", "decoder_error", "syndrome_inconsistent", "source_error", "provenance_error", "internal_error", "accounting_error", "unclassified"}
V3_PLAN = Path("comparison_bench/outputs_comparison/formal_ir_methods/20260726_v1_binary_ldpc_v3_synthetic/pre_run_plan.json")

def _compact(x: Any) -> bytes: return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")
def _sha(x: bytes) -> str: return hashlib.sha256(x).hexdigest()
def _self(x: dict[str, Any], key: str) -> dict[str, Any]: return {**x, key: _sha(_compact(x))}
def _json_x(p: Path, x: Any) -> None: p.open("xb").write(_compact(x))
def _write_x(p: Path, x: bytes) -> None: p.open("xb").write(x)
def _root_id(value: str) -> str: return _sha(bytes.fromhex(value))

def qualification_floor(frame_count: int) -> int:
    """Exact one-sided 95% Clopper-Pearson integer gate for p=19/20."""
    if not isinstance(frame_count, int) or isinstance(frame_count, bool) or frame_count < 1: raise ValueError("frame count")
    denominator=20**frame_count
    for successes in range(frame_count + 1):
        tail=sum(__import__("math").comb(frame_count,i)*19**i for i in range(successes,frame_count+1))
        if 20*tail < denominator: return successes
    raise ValueError("no integer qualification floor")

def _source_hashes() -> dict[str, str]:
    root = Path(__file__).resolve().parents[1]
    paths = {"runner.py":"cli/run_ldpc_v4_synthetic_qualification.py", "verifier.py":"cli/verify_ldpc_v4_synthetic_qualification.py", "method.py":"formal_ir/ldpc_v4.py", "channel.py":"formal_ir/ldpc_v4_channel.py", "codebook.py":"formal_ir/codebook_v4.py", "development_runner.py":"cli/run_ldpc_v4_development_v2.py", "development_verifier.py":"cli/verify_ldpc_v4_development_v2.py", "development_evaluator.py":"formal_ir/ldpc_v4_development_v2.py", "shared.py":"formal_ir/shared.py"}
    return {k: _sha((root / v).read_bytes()) for k, v in paths.items()}

def _load_dev(path: Path, *, private: bool) -> dict[str, Any]:
    result = development_verify.verify_output(path, _private_test_only=private)
    if result.get("run_status") != "completed" or result.get("ready_for_synthetic_prepare") is not True:
        raise ValueError("development package is not strictly verified ready")
    docs = {name: json.loads((path / name).read_bytes()) for name in ("pre_run_plan.json", "v4_candidate_manifest.json", "v4_channel_model.json", "development_selection.json", "development_run_manifest.json", "development_report.json")}
    return {"path": str(path.resolve()), "verification": result, "hashes": {k: _sha((path/k).read_bytes()) for k in docs}, "docs": docs}

def _derive(root_hex: str, *, stratum: str, kind: str) -> np.random.Generator:
    digest = _sha(_compact({"schema":"binary_ldpc_v4_synthetic_rng_v1", "root_hex":root_hex, "stratum":stratum, "kind":kind}))
    return np.random.Generator(np.random.PCG64(int.from_bytes(bytes.fromhex(digest[:32]), "big")))

def _roots() -> dict[str, dict[str, dict[str, str]]]:
    out: dict[str, dict[str, dict[str, str]]] = {}
    for s in STRATA:
        out[s] = {}
        for kind in ("bob", "delta", "order", "toeplitz"):
            raw = secrets.token_bytes(16).hex()
            out[s][kind] = {"root_hex": raw, "root_id": _root_id(raw)}
    return out

def _generate(plan: Mapping[str, Any], stratum: str) -> tuple[np.ndarray, np.ndarray, list[dict[str, Any]]]:
    if stratum not in STRATA: raise ValueError("stratum")
    roots = plan["generator"]["roots"][stratum]
    model = plan["development_binding"]["channel_model"]
    n = int(plan["frame_count_per_stratum"])
    bob = _derive(roots["bob"]["root_hex"], stratum=stratum, kind="bob").integers(0, 1024, size=(n, 256), dtype=np.uint16)
    u = _derive(roots["delta"]["root_hex"], stratum=stratum, kind="delta").random((n, 256))
    probs = model["probabilities"][stratum]
    # Frozen consumption/order: one array, minus then plus then zero.
    delta = np.where(u < float(probs["minus_one"]), -1, np.where(u < float(probs["minus_one"]) + float(probs["plus_one"]), 1, 0)).astype(np.int16)
    alice = ((bob.astype(np.int16) + delta) % 1024).astype(np.uint16)
    rng = _derive(roots["toeplitz"]["root_hex"], stratum=stratum, kind="toeplitz")
    records = []
    for _ in range(n):
        bits = rng.integers(0, 2, size=SEED_BITS, dtype=np.uint8)
        records.append(seed_record(bits))
    return alice, bob, records

def _execution_order(plan: Mapping[str, Any]) -> list[str]:
    records = []
    for s in STRATA:
        rng = _derive(plan["generator"]["roots"][s]["order"]["root_hex"], stratum=s, kind="order")
        records.extend([f"{s}:f{i:03d}" for i in rng.permutation(int(plan["frame_count_per_stratum"]))])
    return records

def _root_ints_and_seed_ids(plan: Mapping[str, Any]) -> tuple[set[int], set[str]]:
    root_values: set[int] = set(); seed_ids: set[str] = set()
    for s in STRATA:
        for x in plan["generator"]["roots"][s].values(): root_values.add(int(x["root_hex"], 16))
        _, _, seeds = _generate(plan, s); seed_ids.update(x["seed_id"] for x in seeds)
    return root_values, seed_ids

def _v3_binding() -> dict[str, Any]:
    raw=V3_PLAN.read_bytes(); doc=json.loads(raw)
    roots=doc.get("generator_contract",{}).get("root_seeds",{}); seeds=doc.get("toeplitz_seeds",{})
    if set(roots)!={"calibrated_alice","calibrated_error","stress_125_alice","stress_125_error","execution_order"} or len(seeds)!=64: raise ValueError("bound v3 root/seed schema")
    ids=[]
    for record in seeds.values(): locked_seed_bits(record,SEED_BITS); ids.append(record["seed_id"])
    if len(set(ids))!=64: raise ValueError("bound v3 seed uniqueness")
    return {"path":str(V3_PLAN.resolve()),"plan_sha256":_sha(raw),"root_seeds":roots,"toeplitz_seed_ids":sorted(ids)}

def _development_root_binding(model_sha: str) -> dict[str, Any]:
    roots=[]
    for stratum in STRATA:
        for kind in ("bob","delta"):
            value, raw=ldpc_v4_development._root(model_sha,stratum,kind)
            roots.append({"stratum":stratum,"kind":kind,"root_hex":raw,"root_id":_root_id(raw),"root_integer":value})
    return {"channel_model_sha256":model_sha,"roots":roots}

def _validate_roots(plan: Mapping[str, Any]) -> tuple[set[int], set[str]]:
    roots=plan["generator"]
    if set(roots)!={"schema","algorithm","roots","delta_order","toeplitz_seed_bits"} or roots["schema"]!="binary_ldpc_v4_synthetic_rng_v1" or roots["algorithm"]!="PCG64" or roots["delta_order"]!="minus_one,plus_one,zero" or roots["toeplitz_seed_bits"]!=SEED_BITS or set(roots["roots"])!=set(STRATA): raise ValueError("generator contract")
    for s in STRATA:
        if set(roots["roots"][s])!={"bob","delta","order","toeplitz"}: raise ValueError("generator kinds")
        for record in roots["roots"][s].values():
            raw=record.get("root_hex") if isinstance(record,dict) else None
            if not isinstance(raw,str) or len(raw)!=32 or raw.lower()!=raw or any(c not in "0123456789abcdef" for c in raw) or record.get("root_id")!=_root_id(raw) or set(record)!={"root_hex","root_id"}: raise ValueError("root record")
    root_ints, seed_ids=_root_ints_and_seed_ids(plan)
    bound=plan["v3_seed_binding"]
    if root_ints & {int(x) for x in bound["root_seeds"].values()} or seed_ids & set(bound["toeplitz_seed_ids"]): raise ValueError("old seed/root collision")
    development={int(x["root_integer"]) for x in plan["development_root_binding"]["roots"]}
    if root_ints & development: raise ValueError("development root collision")
    if len(root_ints)!=8 or len(seed_ids)!=2*int(plan["frame_count_per_stratum"]): raise ValueError("root/seed uniqueness")
    return root_ints, seed_ids

def _plan(dev_dir: Path, *, private: bool = False, count: int = FRAME_COUNT) -> dict[str, Any]:
    dev = _load_dev(dev_dir, private=private)
    roots = _roots()
    model = dev["docs"]["v4_channel_model.json"]; selection = dev["docs"]["development_selection.json"]; codebook = dev["docs"]["v4_candidate_manifest.json"]
    base = {"schema":"binary_ldpc_v4_synthetic_plan_v2", "run_id":RUN_ID, "method_id":METHOD, "dimension":1024, "mapping":"gray", "frame_len_symbols":256, "frame_count_per_stratum":count, "strata":list(STRATA), "caps":{"complete_run_s":1800, "per_frame": {"wall_s":5.0, "decoder_calls":10, "events":32}}, "gate":{"denominator":count, "verified_success_floor":count if private else qualification_floor(count), "forbidden_statuses":sorted(FORBIDDEN)}, "development_prerequisite": {"path":dev["path"], "artifact_hashes":dev["hashes"], "development_report_sha256":dev["hashes"]["development_report.json"], "development_run_manifest_sha256":dev["hashes"]["development_run_manifest.json"]}, "development_binding":{"channel_model":model, "selection":selection, "codebook":codebook}, "v3_seed_binding":_v3_binding(), "development_root_binding":_development_root_binding(model["model_sha256"]), "generator":{"schema":"binary_ldpc_v4_synthetic_rng_v1", "algorithm":"PCG64", "roots":roots, "delta_order":"minus_one,plus_one,zero", "toeplitz_seed_bits":SEED_BITS}, "source_sha256":_source_hashes(), "backend_requirement":"ldpc==2.4.1", "failure_finalizer":"eight_file_synthetic_failure_retention_v2", "_test_only":private}
    base["execution_order"] = _execution_order(base)
    provisional = _self(base, "plan_sha256")
    _validate_roots(provisional)
    return provisional

def prepare_plan(output_dir: Path, development_dir: Path) -> dict[str, Any]:
    if output_dir.exists(): raise FileExistsError("fresh output directory required")
    p = _plan(development_dir); output_dir.mkdir(parents=True); _json_x(output_dir / ARTIFACTS[0], p); return p
def _prepare_test_plan(output_dir: Path, development_dir: Path, *, count: int = 2) -> dict[str, Any]:
    if output_dir.exists(): raise FileExistsError("fresh output directory required")
    p = _plan(development_dir, private=True, count=count); output_dir.mkdir(parents=True); _json_x(output_dir / ARTIFACTS[0], p); return p

def _validate_plan(plan: Mapping[str, Any], *, private: bool) -> dict[str, Any]:
    if not isinstance(plan, dict) or plan.get("plan_sha256") != _sha(_compact({k:v for k,v in plan.items() if k != "plan_sha256"})): raise ValueError("plan self hash")
    if bool(plan.get("_test_only")) != private: raise ValueError("test-only plan")
    if plan.get("schema")!="binary_ldpc_v4_synthetic_plan_v2" or plan.get("run_id")!=RUN_ID or plan.get("method_id")!=METHOD or plan.get("dimension")!=1024 or plan.get("mapping")!="gray" or plan.get("frame_len_symbols")!=256 or plan.get("strata")!=list(STRATA) or plan.get("backend_requirement")!="ldpc==2.4.1" or plan.get("failure_finalizer")!="eight_file_synthetic_failure_retention_v2": raise ValueError("plan identity")
    expected_count=2 if private else FRAME_COUNT
    if int(plan["frame_count_per_stratum"]) != expected_count: raise ValueError("frame count")
    if plan.get("caps")!={"complete_run_s":1800,"per_frame":{"wall_s":5.0,"decoder_calls":10,"events":32}}: raise ValueError("plan caps")
    expected_gate={"denominator":expected_count,"verified_success_floor":expected_count if private else qualification_floor(expected_count),"forbidden_statuses":sorted(FORBIDDEN)}
    if plan.get("gate")!=expected_gate: raise ValueError("plan gate")
    dev = _load_dev(Path(plan["development_prerequisite"]["path"]), private=private)
    if plan["development_prerequisite"]["artifact_hashes"] != dev["hashes"]: raise ValueError("development artifact hashes")
    if plan["development_binding"] != {"channel_model":dev["docs"]["v4_channel_model.json"], "selection":dev["docs"]["development_selection.json"], "codebook":dev["docs"]["v4_candidate_manifest.json"]}: raise ValueError("development binding")
    if plan["execution_order"] != _execution_order(plan) or len(set(plan["execution_order"])) != 2 * int(plan["frame_count_per_stratum"]): raise ValueError("execution order")
    if plan["v3_seed_binding"] != _v3_binding(): raise ValueError("v3 binding")
    if plan.get("development_root_binding") != _development_root_binding(plan["development_binding"]["channel_model"]["model_sha256"]): raise ValueError("development root binding")
    _validate_roots(plan)
    if not private and (plan["source_sha256"] != _source_hashes() or importlib.metadata.version("ldpc") != "2.4.1"): raise ValueError("production source/backend drift")
    return dict(plan)

OUTCOME_FIELDS = ("stratum","plan_frame_id","alice_sha256","bob_sha256","transcript_bytes_len","transcript_bytes_sha256","dataset_id","frame_id","n_pairs","pair_idx_sequence_sha256","method","attempted","denominator_included","status","failure_reason","dimension","frame_len_symbols","raw_ser","verification_invoked","verification_seed_id","verification_tag_bits","epsilon_ec","key_dependent_disclosure_bits_total","public_control_bits_total","transcript_first_event_id","transcript_last_event_id","transcript_sha256","runtime_s","decoder_call_count","verification_check_count","ldpc_syndrome_bits","verification_tag_bits_component","selection_sha256","channel_model_sha256","codebook_manifest_sha256","policy_sha256","mapping","leakage_comparison_policy","backend_name","backend_version")
def _csv(rows: list[Mapping[str, Any]]) -> bytes:
    import io
    f=io.StringIO(newline=""); w=csv.DictWriter(f, fieldnames=OUTCOME_FIELDS, lineterminator="\n", extrasaction="raise"); w.writeheader()
    for row in rows:
        if set(row) != set(OUTCOME_FIELDS): raise ValueError("outcome schema")
        w.writerow({k: ("true" if row[k] else "false") if k in {"attempted","denominator_included","verification_invoked"} else repr(float(row[k])) if k in {"raw_ser","epsilon_ec","runtime_s"} else row[k] for k in OUTCOME_FIELDS})
    return f.getvalue().encode("utf-8")

def _gate(rows: list[Mapping[str, Any]], count: int, floor: int) -> dict[str, Any]:
    denominator=len(rows); success=sum(r.get("status")=="verified_success" for r in rows); forbidden=sum(r.get("status") in FORBIDDEN for r in rows)
    return {"denominator":denominator,"verified_success":success,"forbidden_failure_count":forbidden,"promoted":len(rows)==count and denominator==count and success>=floor and forbidden==0}

def _finalize(out: Path, plan: Mapping[str, Any], rows: list[dict[str, Any]], events: list[Mapping[str, Any]], status: str, reason: str) -> None:
    binding=plan["development_binding"]
    for name, obj in ((ARTIFACTS[3],binding["codebook"]),(ARTIFACTS[4],binding["selection"]),(ARTIFACTS[5],binding["channel_model"])):
        if not (out/name).exists(): _json_x(out/name,obj)
    if not (out/ARTIFACTS[1]).exists(): _write_x(out/ARTIFACTS[1],_csv(rows))
    if not (out/ARTIFACTS[2]).exists(): _write_x(out/ARTIFACTS[2],b"".join(canonical_event(e) for e in events))
    index={n:{"sha256":_sha((out/n).read_bytes()),"bytes":(out/n).stat().st_size} for n in ARTIFACTS[:6]}
    run=_self({"schema":"binary_ldpc_v4_synthetic_run_manifest_v2","run_id":RUN_ID,"run_status":status,"stop_reason":reason,"plan_sha256":plan["plan_sha256"],"outcome_count":len(rows),"artifact_index":index,"decoder_reexecution":False},"manifest_sha256")
    if not (out/ARTIFACTS[6]).exists(): _json_x(out/ARTIFACTS[6],run)
    floors=int(plan["gate"]["verified_success_floor"]); gates={s:_gate([r for r in rows if r.get("stratum")==s],int(plan["frame_count_per_stratum"]),floors) for s in STRATA}
    report=_self({"schema":"binary_ldpc_v4_synthetic_report_v2","run_id":RUN_ID,"run_status":status,"stop_reason":reason,"plan_sha256":plan["plan_sha256"],"run_manifest_sha256":_sha((out/ARTIFACTS[6]).read_bytes()),"promotion_gates":gates,"promoted":status=="completed" and all(g["promoted"] for g in gates.values()),"decoder_reexecution":False},"report_sha256")
    if not (out/ARTIFACTS[7]).exists(): _json_x(out/ARTIFACTS[7],report)

def _execute(out: Path, runner: Callable[..., dict[str, Any]], *, private: bool) -> None:
    if not out.is_dir() or {p.name for p in out.iterdir()} != {ARTIFACTS[0]}: raise ValueError("execute requires only reviewed plan")
    plan=_validate_plan(json.loads((out/ARTIFACTS[0]).read_bytes()), private=private); frames={s:_generate(plan,s) for s in STRATA}; rows=[]; events=[]; start=time.monotonic()
    try:
        for key in plan["execution_order"]:
            if time.monotonic()-start >= float(plan["caps"]["complete_run_s"]): raise TimeoutError("complete_run_s")
            s, fid=key.split(":f"); i=int(fid); alice,bob,seeds=frames[s]
            result=runner(alice[i],bob[i],channel_model=plan["development_binding"]["channel_model"],selection_binding=plan["development_binding"]["selection"],locked_seed=seeds[i],dataset_id=f"synthetic_{s}",frame_id=key,stratum=s,_caps=plan["caps"]["per_frame"])
            outcome=dict(result["outcome"]); es=list(result["events"]); blob=b"".join(canonical_event(e) for e in es)
            outcome.update({"stratum":s,"plan_frame_id":key,"alice_sha256":_sha(np.asarray(alice[i],dtype="<u2").tobytes()),"bob_sha256":_sha(np.asarray(bob[i],dtype="<u2").tobytes()),"transcript_bytes_len":len(blob),"transcript_bytes_sha256":_sha(blob)})
            rows.append(outcome); events.extend(es)
        _finalize(out,plan,rows,events,"completed","")
    except Exception as exc:
        _finalize(out,plan,rows,events,"failed",f"{type(exc).__name__}:{exc}")
        if not private: raise

def execute_plan(output_dir: Path) -> None: _execute(output_dir,run_ldpc_formal_v4,private=False)
def _execute_test_plan(output_dir: Path, runner: Callable[...,dict[str,Any]]) -> None: _execute(output_dir,runner,private=True)
def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--output-dir",type=Path,required=True); p.add_argument("--mode",choices=("prepare","execute"),required=True); p.add_argument("--development-dir",type=Path); a=p.parse_args()
    if a.mode=="prepare":
        if a.development_dir is None: p.error("--development-dir required for prepare")
        prepare_plan(a.output_dir,a.development_dir)
    else: execute_plan(a.output_dir)
    return 0
if __name__=="__main__": raise SystemExit(main())
