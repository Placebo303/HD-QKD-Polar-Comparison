"""Read-only five-package binding required before v5 source use."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Any, Mapping

def _c(v: Any)->bytes:return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode("ascii")
def _s(v: bytes)->str:return hashlib.sha256(v).hexdigest()
_P=(
 ("v4_corrected_development","20260727_v2_binary_ldpc_v4_development","comparison_bench.src.comparison_bench.cli.verify_ldpc_v4_development_v2.verify_output",{
"development_plane_outcomes.csv":"c48d00ba68fe37e2104794348734d6c22a5f295d3e90826362f9e094124d3018","development_report.json":"31f51cec0625fe7be0f36a4b746de37e1a512a7bc63c182501baaedbe5b6bfa5","development_run_manifest.json":"7ff6cb96ef25be36c92d54c10e74a75e757a07a11227c0444b4193ff5dd5b713","development_selection.json":"5d3757f7e36e117877e9c2d75fa1e90496d83cc080171cfaa4f3299c44b6b4dd","pre_run_plan.json":"0b690fe2e4ac56cf1d742368877b07f72ad3cc84dc0c7de894caf1c3a9919255","v4_candidate_manifest.json":"786b48287f0b453a668c1ae1bdab2126aa7d13aeb94439860b80899a34687500","v4_channel_model.json":"83a80a2db8d7b7cacc63e5e7531ecc7d4bd4e93605af53aa2fa987257d15cf6c"}),
 ("v4_promoted_synthetic","20260728_v2_binary_ldpc_v4_synthetic","comparison_bench.src.comparison_bench.cli.verify_ldpc_v4_synthetic_qualification.verify_output",{"formal_channel_model.json":"83a80a2db8d7b7cacc63e5e7531ecc7d4bd4e93605af53aa2fa987257d15cf6c","formal_codebook_manifest.json":"786b48287f0b453a668c1ae1bdab2126aa7d13aeb94439860b80899a34687500","formal_frame_outcomes.csv":"3dd169aa692aba94232abf5018bbaee819645ac210a79c466b1702e0500d6c93","formal_qualification_report.json":"57268f73d4fa7dcbce01c2e63066af6d177502b415aa076312dd3a9c7a3f804a","formal_run_manifest.json":"3a142ff8d6d37c665ac8e0a1a8541fe9b36133ea10e75e3b55cbdc044eb49fa6","formal_selection_manifest.json":"5d3757f7e36e117877e9c2d75fa1e90496d83cc080171cfaa4f3299c44b6b4dd","formal_transcript.jsonl":"c2518fd89ad9a9ca3f884e74419e5801b42c956d3f027d90d9044167b7782b0f","pre_run_plan.json":"6a8c8c11afe7e13061c876a8955592f78911fc12883558fa9ccb3546391874cc"}),
 ("v4_16db_non_promoted","20260729_v1_binary_ldpc_v4_16db_transfer","comparison_bench.src.comparison_bench.cli.verify_ldpc_v4_16db_transfer_qualification.verify_output",{"formal_channel_model.json":"83a80a2db8d7b7cacc63e5e7531ecc7d4bd4e93605af53aa2fa987257d15cf6c","formal_codebook_manifest.json":"786b48287f0b453a668c1ae1bdab2126aa7d13aeb94439860b80899a34687500","formal_frame_outcomes.csv":"08a99fddb910afce675c05d9a7388165f772c98db2c60e396853600e341dcb73","formal_qualification_report.json":"c9986ca024c23d3111793890688e352062107686db1a634653a6e4e430359e97","formal_run_manifest.json":"64a92178f17e5e669370585a3a72c88ccae986835ed06a53b68de0488bda7550","formal_selection_manifest.json":"5d3757f7e36e117877e9c2d75fa1e90496d83cc080171cfaa4f3299c44b6b4dd","formal_transcript.jsonl":"b3dd574ae9f9bade050a71bdf3c4fa22b70498aa6e4b421ecb98dbb749607f75","pre_run_plan.json":"ce7a582c34b5a99846e5da6631b836bbc8d950d08f760721aa9a7a2435512eee","real_data_lock.json":"9852dad0d57a226913a2391650ab1829b3d155f8cc42908d6196543799ae1bc2"}),
 ("v4_10db_v1_invalid_pre_execute","20260729_v1_binary_ldpc_v4_10db_transfer",None,{"pre_run_plan.json":"dae9d27a068bf9b15f25ae684bd3cf290623524b0e92af8989869579b0ac523c","real_data_lock.json":"6596316074b0e473de26ba44a87556016f23b082dc36239e06a65fa4e7d11baf"}),
 ("v4_10db_v2_non_promoted","20260729_v2_binary_ldpc_v4_10db_transfer","comparison_bench.src.comparison_bench.cli.verify_ldpc_v4_10db_transfer_qualification_v2.verify_output",{"formal_channel_model.json":"83a80a2db8d7b7cacc63e5e7531ecc7d4bd4e93605af53aa2fa987257d15cf6c","formal_codebook_manifest.json":"786b48287f0b453a668c1ae1bdab2126aa7d13aeb94439860b80899a34687500","formal_frame_outcomes.csv":"7e906a5749b5f8c9d126798f2975ba5caec3cbd4592aef13ff50e7a39eb54d41","formal_qualification_report.json":"960e59f6f5b8acee191d6572421cc8d928707c771b99267dcf80a1a31d02a343","formal_run_manifest.json":"3a75b74227a84a9e8f6aea80e10af2477656ad89cbfe310fbbea5b96ddf1d67c","formal_selection_manifest.json":"5d3757f7e36e117877e9c2d75fa1e90496d83cc080171cfaa4f3299c44b6b4dd","formal_transcript.jsonl":"f1decb49c9209a4a546eade3b158776853f997422dd9e56d7967022b0508aedf","pre_run_plan.json":"ff7d5f987a3eec19d30a92c5781d77ba612b7305530f38744b6bd9a9872c63ed","real_data_lock.json":"6596316074b0e473de26ba44a87556016f23b082dc36239e06a65fa4e7d11baf"}))
def _files(p: Path, expected: Mapping[str, str]) -> list[dict[str, Any]]:
    if not p.is_dir() or {x.name for x in p.iterdir()} != set(expected):
        raise ValueError("predecessor filename set")
    out=[]
    for name in sorted(expected):
        raw=(p/name).read_bytes(); digest=_s(raw)
        if digest != expected[name]: raise ValueError("predecessor file hash")
        out.append({"name":name,"size_bytes":len(raw),"sha256":digest})
    return out
def _normal_result(package_id: str, path: Path) -> dict[str, Any]:
    if package_id == "v4_10db_v1_invalid_pre_execute":
        plan=json.loads((path/"pre_run_plan.json").read_bytes()); lock=json.loads((path/"real_data_lock.json").read_bytes())
        if plan.get("_test_only") is not False or len(lock.get("selected_frames",[])) != 384: raise ValueError("invalid predecessor v1 semantics")
        forbidden={"formal_frame_outcomes.csv","formal_transcript.jsonl","formal_run_manifest.json","formal_qualification_report.json"}
        present=sorted(forbidden & {x.name for x in path.iterdir()})
        if present: raise ValueError("invalid predecessor v1 outputs")
        return {"status":"invalid_pre_execute_self_collision","canonical_json_files":["pre_run_plan.json","real_data_lock.json"],"production_test_only":False,"selected_frames":384,"forbidden_output_files_present":[]}
    if package_id == "v4_corrected_development":
        from ..cli import verify_ldpc_v4_development_v2 as mod
        result=mod.verify_output(path); wanted={"status":"verified","run_status":"completed","ready_for_synthetic_prepare":True,"decoder_reexecution":False,"scope":"predecessor_source_model_codebook_development_selection_accounting"}
    elif package_id == "v4_promoted_synthetic":
        from ..cli import verify_ldpc_v4_synthetic_qualification as mod
        result=mod.verify_output(path); wanted={"status":"verified","run_status":"completed","promoted":True,"outcomes":256,"decoder_reexecution":False}
    elif package_id == "v4_16db_non_promoted":
        from ..cli import verify_ldpc_v4_16db_transfer_qualification as mod
        result=mod.verify_output(path); wanted={"status":"verified","run_status":"completed","promoted":False,"outcomes":384,"decoder_reexecution":False,"source_relocation":True,"successes_by_stratum":{"bw120":125,"bw180":128,"bw200":128},"forbidden_failure_count":0}
    else:
        from ..cli import verify_ldpc_v4_10db_transfer_qualification_v2 as mod
        result=mod.verify_output(path); wanted={"status":"verified","run_status":"completed","promoted":False,"outcomes":384,"decoder_reexecution":False,"source_relocation":True,"successes_by_stratum":{"bw120":125,"bw180":127,"bw200":128},"forbidden_failure_count":0}
    if package_id in {"v4_16db_non_promoted","v4_10db_v2_non_promoted"}:
        # Historical verifiers expose aggregate gates, not the normalized counts.
        report=json.loads((path/"formal_qualification_report.json").read_bytes())
        gates=report.get("promotion_gates",{})
        got={"bw120":gates.get("d1024_bw120",{}).get("verified_success"),"bw180":gates.get("d1024_bw180",{}).get("verified_success"),"bw200":gates.get("d1024_bw200",{}).get("verified_success")}
        if got != wanted["successes_by_stratum"]: raise ValueError("predecessor successes")
        if any(gates.get(f"d1024_{name}",{}).get("forbidden_failure_count") != 0 for name in ("bw120","bw180","bw200")):
            raise ValueError("predecessor forbidden failures")
    if any(result.get(k)!=v for k,v in wanted.items() if k not in {"successes_by_stratum","forbidden_failure_count"}): raise ValueError("predecessor verifier result")
    return wanted
def build_predecessor_binding(base_root: Path) -> dict:
    root=Path(base_root)
    # Do the entire immutable byte binding before installing the bounded
    # historical replay cache.  The cache is shared by all four verifiers,
    # never by their conclusions, and is restored by its own finally block.
    checked=[_files(root/directory, expected) for _,directory,_,expected in _P]
    shared={
        "selection": "5d3757f7e36e117877e9c2d75fa1e90496d83cc080171cfaa4f3299c44b6b4dd",
        "codebook": "786b48287f0b453a668c1ae1bdab2126aa7d13aeb94439860b80899a34687500",
        "channel": "83a80a2db8d7b7cacc63e5e7531ecc7d4bd4e93605af53aa2fa987257d15cf6c",
    }
    for files in checked:
        by={x["name"]:x["sha256"] for x in files}
        for filename, digest in (("development_selection.json",shared["selection"]),("formal_selection_manifest.json",shared["selection"]),("v4_candidate_manifest.json",shared["codebook"]),("formal_codebook_manifest.json",shared["codebook"]),("v4_channel_model.json",shared["channel"]),("formal_channel_model.json",shared["channel"])):
            if filename in by and by[filename] != digest:
                raise ValueError("predecessor shared method hash")
    from ..cli import run_ldpc_v4_16db_transfer_qualification as replay_lane
    packages=[]
    with replay_lane._replay_matrix_cache():
        for (package_id,directory,verifier,expected),files in zip(_P, checked):
            path=root/directory; mode="canonical_semantic_only" if verifier is None else "read_only_verifier"
            packages.append({"package_id":package_id,"directory_name":directory,"verification_mode":mode,"verifier":verifier,"files":files,"verified_result":_normal_result(package_id,path)})
    base={"schema":"binary_ldpc_v5_predecessor_binding_v1","contract_id":"binary_ldpc_v5_five_predecessors_20260729","base_root_policy":"caller_supplied_unhashed_location","packages":packages}
    return {**base,"binding_sha256":_s(_c(base))}
def validate_predecessor_binding(record: Mapping[str,object],base_root: Path)->None:
    got=dict(record); digest=got.pop("binding_sha256",None)
    if not isinstance(digest,str) or _s(_c(got))!=digest: raise ValueError("predecessor binding hash")
    if dict(record)!=build_predecessor_binding(Path(base_root)): raise ValueError("predecessor binding reconstruction")
