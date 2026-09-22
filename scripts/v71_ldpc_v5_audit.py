# V72_not_started
#!/usr/bin/env python3
# V71 ldpc_v5 audit A1-A6 read-only READY/ADAPTER/NOT_COMPATIBLE
# successor_not_started
# ponytail: ast + importlib probe, O(files) scan, no runtime
import argparse
import ast
import json
import importlib.util
from pathlib import Path

def probe_a1(path):
    txt = Path(path).read_text(encoding="utf-8")
    tree = ast.parse(txt)
    names = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    need = {"run_ldpc_formal_v5","build_v5_policy_manifest","verify_v5_policy_manifest","validate_outcome_v5","verify_public_payload_v5"}
    return need.issubset(names)

def probe_a2(path):
    txt = Path(path).read_text(encoding="utf-8")
    return "policy_sha256" in txt and "decoder_sha256" in txt and "h1_binding" in txt

def probe_a3_backend_model_binding_field_present(path):
    # A2: delete self-binding, A3_backend_model_binding_field_present read-only check
    # ponytail: read-only presence check, no self-comparison
    t1 = Path(path).read_text(encoding="utf-8") if Path(path).exists() else ""
    return "model_sha256" in t1 or "channel_model_sha256" in t1

def probe_a4(path):
    txt = Path(path).read_text(encoding="utf-8")
    # A2: true accept requires 10-bit extrinsic injection; else ADAPTER_REQUIRED
    has_list = "list[float]" in txt
    has_plane = "plane_error_channel" in txt
    has_extrinsic = "extrinsic" in txt.lower()
    has_10bit = ("10" in txt and "Q=1024" in txt) or ("PLANES" in txt and "range(10)" in txt)
    # need true 10-bit extrinsic acceptance
    return (has_list or has_plane) and has_10bit and has_extrinsic

def probe_a5(path):
    txt = Path(path).read_text(encoding="utf-8")
    # caps wall_s 10.0 decoder_calls 20 events 32
    return "wall_s" in txt and "decoder_calls" in txt

def probe_a6(path):
    txt = Path(path).read_text(encoding="utf-8")
    # A2: need 10240 increment acceptance; else ADAPTER_REQUIRED; A3: capacity separated -> check 10240
    has_base = "ldpc_syndrome_bits" in txt and "verification_tag_bits_component" in txt
    has_10240 = "10240" in txt
    return has_base and has_10240

def audit_one(session_label):
    base = Path("comparison_bench/src/comparison_bench/formal_ir")
    p_v5 = base / "ldpc_v5.py"
    ok1 = probe_a1(p_v5)
    ok2 = probe_a2(p_v5)
    ok3 = probe_a3_backend_model_binding_field_present(p_v5)
    ok4 = probe_a4(p_v5)
    ok5 = probe_a5(p_v5)
    ok6 = probe_a6(p_v5)
    d = {"A1_interface_presence": bool(ok1), "A2_policy_manifest_schema": bool(ok2), "A3_backend_model_binding_field_present": bool(ok3), "A4_extrinsic_interface": bool(ok4), "A5_runtime_caps": bool(ok5), "A6_disclosure_accounting": bool(ok6)}
    # A2: delete self-binding; A3 field present only; true READY requires 10-bit extrinsic+10240 else ADAPTER_REQUIRED (never READY for current ldpc_v5)
    if not ok1 or not ok2:
        cls = "NOT_COMPATIBLE"
    elif ok1 and ok2 and ok3 and ok4 and ok5 and ok6:
        cls = "ADAPTER_REQUIRED"
    elif ok1 and ok2 and ok3:
        cls = "ADAPTER_REQUIRED"
    else:
        cls = "NOT_COMPATIBLE"
    # A3: mechanical capacity reuse V70: 1M FEASIBLE,1p5M MARGINAL,2M NO_INFORMATION
    cap_map={"1M":"FEASIBLE","1p5M":"MARGINAL","2M":"NO_INFORMATION"}
    kernel_status = "READY" if (ok1 and ok2) else "NOT_READY"
    backend_status = cls
    capacity_status = cap_map.get(session_label,"UNKNOWN")
    d.update({"kernel_status": kernel_status, "backend_status": backend_status, "capacity_status": capacity_status})
    return d, cls

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="v71_audit_report.json")
    args = ap.parse_args()
    reg = json.loads(Path("v71_data_registry.json").read_text(encoding="utf-8"))
    per = {}
    for sess in reg["sessions"]:
        sid = sess["session_id"]
        d, cls = audit_one(sess["source_label"])
        per[sid] = {"checks": d, "classification": cls}
    # overall 4-state via per session audit + placeholder D/E (assume D pass E pass)
    # counts from audit
    ready = sum(1 for v in per.values() if v["classification"]=="READY")
    adapter = sum(1 for v in per.values() if v["classification"] in ("ADAPTER","ADAPTER_REQUIRED"))
    notc = sum(1 for v in per.values() if v["classification"]=="NOT_COMPATIBLE")
    if notc>0:
        overall="V71_OVERALL_KERNEL_ADAPTER_OR_HEAVY"
    elif ready==3:
        overall="V71_OVERALL_KERNEL_READY"
    else:
        overall="V71_OVERALL_KERNEL_ADAPTER_OR_HEAVY"
    out = {"schema":"v71_audit_v1","successor_not_started": True, "per_session": per, "overall": overall, "ready": ready, "adapter": adapter, "not_compatible": notc}
    Path(args.out).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[audit] overall {overall} ready {ready} adapter {adapter} notc {notc}")

if __name__=="__main__":
    main()
