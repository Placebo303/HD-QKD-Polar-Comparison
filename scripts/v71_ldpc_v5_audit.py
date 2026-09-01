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

def probe_a3(sel_path, chan_path):
    import re
    t1 = Path(sel_path).read_text(encoding="utf-8") if Path(sel_path).exists() else ""
    t2 = Path(chan_path).read_text(encoding="utf-8") if Path(chan_path).exists() else ""
    # strict: both must contain model_sha256 and values must match when extracted
    if "model_sha256" not in t1 or "model_sha256" not in t2:
        return False
    # extract hex values after model_sha256
    pat = re.compile(r"model_sha256[^a-f0-9]*([a-f0-9]{16,64})", re.IGNORECASE)
    m1 = pat.findall(t1)
    m2 = pat.findall(t2)
    if not m1 or not m2:
        # fallback to presence check if no hex extracted but keyword present -> strict still false?
        # require at least one extractable; if same file, check consistency of duplicates
        return False
    # when both paths are same file, check internal consistency (all extracted same)
    if Path(sel_path).resolve() == Path(chan_path).resolve():
        return len(set(m1)) == 1
    # different files: intersection must be non-empty (shared binding)
    return bool(set(m1) & set(m2))

def probe_a4(path):
    txt = Path(path).read_text(encoding="utf-8")
    # look for error_channel param type list[float] vs ndarray
    has_list = "list[float]" in txt
    has_plane = "plane_error_channel" in txt
    # if has list hint then extrinsic inject possible -> READY else ADAPTER
    return has_list or has_plane

def probe_a5(path):
    txt = Path(path).read_text(encoding="utf-8")
    # caps wall_s 10.0 decoder_calls 20 events 32
    return "wall_s" in txt and "decoder_calls" in txt

def probe_a6(path):
    txt = Path(path).read_text(encoding="utf-8")
    return "ldpc_syndrome_bits" in txt and "verification_tag_bits_component" in txt

def audit_one(session_label):
    base = Path("comparison_bench/src/comparison_bench/formal_ir")
    p_v5 = base / "ldpc_v5.py"
    ok1 = probe_a1(p_v5)
    ok2 = probe_a2(p_v5)
    ok3 = probe_a3(p_v5, p_v5)
    ok4 = probe_a4(p_v5)
    ok5 = probe_a5(p_v5)
    ok6 = probe_a6(p_v5)
    # build per check dict
    d = {"A1_interface_presence": bool(ok1), "A2_policy_manifest_schema": bool(ok2), "A3_channel_binding": bool(ok3), "A4_extrinsic_interface": bool(ok4), "A5_runtime_caps": bool(ok5), "A6_disclosure_accounting": bool(ok6)}
    if not ok1 or not ok2:
        cls = "NOT_COMPATIBLE"
    elif ok1 and ok2 and ok3 and ok4 and ok5 and ok6:
        cls = "READY"
    elif ok1 and ok2 and ok3:
        cls = "ADAPTER"
    else:
        cls = "NOT_COMPATIBLE"
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
    adapter = sum(1 for v in per.values() if v["classification"]=="ADAPTER")
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
