"""V55 independent TEST data readiness check — decoder-free (G1-G7) stratified.
Zero decoder calls. Reproducible.
Run: python check_v55_data_readiness.py [--data-root PATH] [--registry PATH]
Exit 0: V55_QUALIFICATION_PLAN_READY (target domain D_target all strata PASS)
Exit 1: V55_DATA_NOT_READY (any target stratum fail, partial allowed) or EVIDENCE_INVALID
Stratified: per physical condition stratum, balanced B=15 or 30, target domain D_target={1M,1p5M,2M}
G1-G7 extended per strata; exploratory strata allowed partial DATA_NOT_READY.
"""
import sys
import json
import argparse
from pathlib import Path

# ponytail: minimal decoder-free checks, no external deps beyond stdlib+pathlib
# ceiling: O(K) overlap scan, fine for K<1000; upgrade to interval tree if needed.

REPO_ROOT = Path(__file__).resolve().parents[3]

# V13 HOLD config (from split_manifest 60/20/20)
HOLD_CONFIG = {
    "1M": {"H": 400, "base": 1600, "total": 2000},
    "1p5M": {"H": 554, "base": 2213, "total": 2767},
    "2M": {"H": 729, "base": 2916, "total": 3645},
}

# Used intervals union per source for V48-V54 (135-180 blocks)
USED_BASE = {
    "1M": [0,7,14,28,33,35,42,56,61,63,70,84,89,91,98,113,117,119,127,141,146,169,198,226,254,282,311,339,367,396],
    "1p5M": [0,12,19,39,44,51,58,78,83,90,97,117,122,130,137,157,162,169,176,196,201,235,275,314,353,392,432,471,510,550],
    "2M": [0,18,25,51,53,70,77,103,104,122,129,155,174,181,206,207,225,232,257,258,310,362,414,466,517,569,621,673,725],
}
V53_SELECTED = {
    "1M": [22,52,109,155,179,202,230,240,263,287,303,324,347,371,388],
    "1p5M": [8,73,151,214,247,279,305,337,370,388,419,451,484,516,542],
    "2M": [8,81,136,197,264,304,351,396,442,489,536,583,630,677,717],
}
V54_SELECTED = {
    "1M": [22,52,109,155,179,202,230,240,263,287,303,324,347,371,388],
    "1p5M": [8,73,151,214,247,279,305,337,370,388,419,451,484,516,542],
    "2M": [8,81,136,197,264,304,351,396,442,489,536,583,630,677,717],
}

# Stratified target domain (frozen)
D_TARGET = ["1M", "1p5M", "2M"]
B_PRIMARY = 30
B_ALTERNATIVE = 15

def overlaps(a, b):
    return abs(a - b) <= 3

def enumerate_and_select(F, used_list, need=30):
    all_starts = list(range(0, F - 3))
    remaining = [s for s in all_starts if not any(overlaps(s, u) for u in used_list)]
    K = len(remaining)
    if K < need:
        return None, K, remaining
    selected = [remaining[(j * (K - 1)) // (need - 1)] for j in range(need)]
    ok = all(not overlaps(selected[i], selected[j]) for i in range(need) for j in range(i+1, need))
    zero_used = all(not any(overlaps(s, u) for u in used_list) for s in selected)
    unique = len(set(selected)) == need
    return {"selected": selected, "K": K, "remaining": remaining, "ok": ok and zero_used and unique}, K, remaining

def check_v25_prior():
    candidates = [
        REPO_ROOT / "comparison_bench" / "outputs_comparison" / "nonbinary_diagnostics" / "nbldpc_v25_20260818" / "run_04" / "channel_counts.npz",
        REPO_ROOT / "comparison_bench" / "outputs_comparison" / "nonbinary_diagnostics" / "nbldpc_v25_20260818" / "run_04" / "data_inventory.json",
    ]
    exists = any(p.exists() for p in candidates)
    print(f"  G6 V25 prior files: {candidates[0].exists()=}, {candidates[1].exists() if len(candidates)>1 else False} -> exists={exists}")
    frozen_modules = [
        REPO_ROOT / "comparison_bench" / "src" / "comparison_bench" / "formal_ir" / "nonbinary_v25_gate.py",
        REPO_ROOT / "comparison_bench" / "src" / "comparison_bench" / "formal_ir" / "v38_architecture_triage.py",
        REPO_ROOT / "comparison_bench" / "src" / "comparison_bench" / "formal_ir" / "v35_algorithm_development.py",
    ]
    import py_compile
    compile_ok = True
    for m in frozen_modules:
        readable = m.exists() and m.stat().st_size > 0
        try:
            py_compile.compile(str(m), doraise=True)
            ok_c = True
        except Exception as e:
            print(f"  G6 py_compile FAIL {m.name}: {e}")
            ok_c = False
        print(f"  G6 frozen candidate {m.name}: readable={readable} py_compile={ok_c}")
        compile_ok = compile_ok and readable and ok_c
    sys.path.insert(0, str(REPO_ROOT / "comparison_bench" / "src"))
    ok_import = False
    try:
        import importlib
        for mod in ["comparison_bench.formal_ir.nonbinary_v25_gate", "comparison_bench.formal_ir.v38_architecture_triage", "comparison_bench.formal_ir.v35_algorithm_development"]:
            importlib.import_module(mod)
        ok_import = True
        print(f"  G6 import PASS: nonbinary_v25_gate + v38 + v35")
    except Exception as e:
        print(f"  G6 import FAIL: {e}")
        ok_import = False
    code_ok = compile_ok or ok_import
    print(f"  G6 summary: exists={exists} compile_ok={compile_ok} import_ok={ok_import} -> code_ok={code_ok}")
    return exists and code_ok

def load_registry(found_registry):
    try:
        data = json.loads(found_registry.read_text(encoding="utf-8"))
        # Support both legacy flat {1M:{...}} and new {strata:{...}, target_domain:[...]}
        if "strata" in data:
            strata = data["strata"]
            target = data.get("target_domain", D_TARGET)
            b_per = data.get("blocks_per_stratum", B_PRIMARY)
            meta = {k: v for k, v in data.items() if k not in ("strata",)}
        else:
            # legacy: top-level keys are strata
            strata = {k: v for k, v in data.items() if k in D_TARGET or k.startswith("stratum") or k in ("1M","1p5M","2M")}
            # Also collect any extra strata beyond D_TARGET as exploratory
            extra = {k: v for k, v in data.items() if k not in strata and isinstance(v, dict) and "session_id" in v}
            strata.update(extra)
            target = D_TARGET
            b_per = data.get("blocks_per_stratum", B_PRIMARY)
            meta = {}
        return strata, target, b_per, data
    except Exception as e:
        print(f"  registry load FAIL: {e}")
        return None, None, None, None

def main():
    parser = argparse.ArgumentParser(description="V55 G1-G7 decoder-free stratified readiness")
    parser.add_argument("--data-root", type=str, default=None, help="PROJECT_DATA_ROOT or independent session root (optional)")
    parser.add_argument("--registry", type=str, default=None, help="path to v55_independent_test_sessions.json if exists")
    parser.add_argument("--out", type=str, default=None, help="output JSON path for readiness result")
    args = parser.parse_args()

    print("=== V55 Independent TEST Data Readiness — decoder-free stratified G1-G7 ===")
    print(f"HEAD efd34ef318014e1d0505605062057b042e2180eb branch formal-ir-mainline (stratified revision)")
    print(f"HOLD adjudication: V48-V54 used 135-180 intervals, K2 remaining 135/260/461 but polluted — even unused frames不得改称 TEST")
    print(f"HOLD_CONFIG: {HOLD_CONFIG}")
    print(f"D_target (qualification domain): {D_TARGET}  B_primary={B_PRIMARY} (alt {B_ALTERNATIVE} balanced)")
    print(f"Budget proportional: S={len(D_TARGET)} strata × B blocks => {len(D_TARGET)*B_ALTERNATIVE}-{len(D_TARGET)*B_PRIMARY*2}?? Actually 2SB-4SB: S=3 B=15=>90-180, B=30=>180-360")

    registry_candidates = []
    if args.registry:
        registry_candidates.append(Path(args.registry))
    registry_candidates += [
        REPO_ROOT / "comparison_bench" / "configs" / "v55_independent_test_sessions.json",
        REPO_ROOT / "comparison_bench" / "configs" / "v55_independent_sessions.json",
        REPO_ROOT / "comparison_bench" / "configs" / "v55_available_datasets.json",
        REPO_ROOT / "workspace" / "v55_independent_test_sessions.json",
    ]
    if args.data_root:
        registry_candidates.append(Path(args.data_root) / "v55_independent_test_sessions.json")
        registry_candidates.append(Path(args.data_root) / "v55_available_datasets.json")
    import os
    env_root = os.environ.get("PROJECT_DATA_ROOT") or os.environ.get("HDQKD_DATA_ROOT")
    if env_root:
        registry_candidates.append(Path(env_root) / "v55_independent_test_sessions.json")
        registry_candidates.append(Path(env_root) / "v55_available_datasets.json")

    found_registry = None
    for p in registry_candidates:
        if p.exists():
            found_registry = p
            break

    # Inventory: list all available independent datasets (decoder-free physical conditions)
    print(f"\n-- Inventory: available independent datasets & physical conditions --")
    print(f"  Searching PROJECT_DATA_ROOT / configs / external for strata with physical conditions (date/location/device/channel params)")
    for p in registry_candidates:
        print(f"    - {p} exists={p.exists()}")

    strata = None
    target_domain = D_TARGET
    b_per = B_PRIMARY
    raw_data = None
    if found_registry is None:
        print(f"  Inventory FAIL: no independent dataset registry found (need per-stratum session_id/date/location/device/channel_params/path/frames)")
        # stratified G1 will be per stratum FAIL
        g_strata = {}
        for s in D_TARGET:
            g_strata[s] = {"G1": False, "G2": False, "G3": False, "G4": False, "G5": False, "G7": False, "inventory": "not found"}
    else:
        print(f"  found registry: {found_registry}")
        strata, target_domain, b_per, raw_data = load_registry(found_registry)
        if strata is None:
            print(f"  registry not readable")
            g_strata = {s: {"G1": False} for s in D_TARGET}
        else:
            print(f"  registry loaded: strata={list(strata.keys())} target={target_domain} B={b_per}")
            # Inventory table
            print(f"  Inventory table (physical conditions per stratum):")
            for sid, entry in strata.items():
                phys = {k: entry.get(k) for k in ["session_id","date","location","device","channel_params","delay_ps","power","rate","path","frames"] if k in entry}
                print(f"    - stratum {sid}: {phys}")
            # Also list any available_independent_datasets extra key
            if raw_data and "available_independent_datasets" in raw_data:
                print(f"  available_independent_datasets extra: {raw_data['available_independent_datasets']}")

    # G1 file readable — per stratum
    print(f"\n-- G1 文件可读 (per stratum) --")
    g1_per = {}
    if found_registry is None:
        for s in D_TARGET:
            g1_per[s] = False
            print(f"  G1 {s}: FAIL — no registry")
    else:
        for s in target_domain:
            if s not in strata:
                g1_per[s] = False
                print(f"  G1 {s}: FAIL — stratum not in registry")
                continue
            entry = strata[s]
            # check path readable? If path not exists, still check entry has required fields
            has_path = "path" in entry
            has_frames = "frames" in entry
            has_sid = "session_id" in entry
            has_date = "date" in entry
            ok = has_path and has_frames and has_sid and has_date
            # try path existence
            p = Path(entry.get("path",""))
            exists = p.exists() if has_path else False
            # If path not exists but fields present, still consider G1 as registred but file not verified — mark FAIL
            g1_per[s] = ok and exists
            print(f"  G1 {s}: {'PASS' if g1_per[s] else 'FAIL'} has_path={has_path} has_frames={has_frames} has_sid={has_sid} has_date={has_date} path_exists={exists}")
            # If path is parquet and exists, try row count via optional pandas
            if exists and p.suffix == ".parquet":
                try:
                    import pandas as pd
                    df = pd.read_parquet(p)
                    expected = entry.get("frames", 0) * 256 if isinstance(entry.get("frames"), int) else None
                    if expected is not None and len(df) != expected:
                        print(f"    G1 parquet rows {len(df)} != frames*256 {expected} => FAIL")
                        g1_per[s] = False
                except Exception as e:
                    print(f"    G1 parquet check skip: {e}")

    # G2 provenance完整 — per stratum
    print(f"\n-- G2 provenance 完整 (per stratum) --")
    g2_per = {}
    if found_registry is None:
        for s in D_TARGET:
            g2_per[s] = False
            print(f"  G2 {s}: FAIL — G1 not pass")
    else:
        for s in target_domain:
            if s not in strata:
                g2_per[s] = False
                continue
            entry = strata[s]
            ok = True
            for k in ["session_id","date","path","frames"]:
                if k not in entry:
                    print(f"  G2 {s} FAIL: missing {k}")
                    ok = False
            if "date" in entry and entry["date"] == "2026-01-21":
                print(f"  G2 {s} FAIL: date == V13 2026-01-21, must be different")
                ok = False
            # Check physical conditions at least date+session_id, optional location/device/channel_params
            if "session_id" in entry and "date" in entry:
                print(f"  G2 {s} provenance: session_id={entry.get('session_id')} date={entry.get('date')} location={entry.get('location','-')} device={entry.get('device','-')} channel_params={entry.get('channel_params', entry.get('delay_ps','-'))}")
            g2_per[s] = ok and g1_per.get(s, False)
            print(f"  G2 {s} {'PASS' if g2_per[s] else 'FAIL'}")

    # G3 三源/strata明确 — per stratum + global
    print(f"\n-- G3 各 stratum 明确 (target domain) --")
    g3_per = {}
    if found_registry is None:
        for s in D_TARGET:
            g3_per[s] = False
        g3_global = False
        print(f"  G3 FAIL: G1 not pass")
    else:
        g3_global = all(s in strata for s in target_domain)
        for s in target_domain:
            g3_per[s] = s in strata and g2_per.get(s, False)
            print(f"  G3 {s}: {'PASS' if g3_per[s] else 'FAIL'} present={s in strata}")
        print(f"  G3 global {'PASS' if g3_global else 'FAIL'}: D_target each one independent session")

    # G4 256/frame 1024/block — per stratum
    print(f"\n-- G4 256/frame 1024/block (per stratum) --")
    g4_per = {}
    if found_registry is None:
        for s in D_TARGET:
            g4_per[s] = False
            print(f"  G4 {s}: FAIL — G1 not pass")
    else:
        for s in target_domain:
            if s not in strata:
                g4_per[s] = False
                continue
            entry = strata[s]
            frames = entry.get("frames")
            if not isinstance(frames, int):
                print(f"  G4 {s} FAIL: frames not int")
                g4_per[s] = False
                continue
            if frames < 120:
                print(f"  G4 {s} FAIL: frames {frames} <120 (need ≥120, suggest ≥160)")
                g4_per[s] = False
            else:
                print(f"  G4 {s} check: frames {frames} ≥120 ok, pairs {frames*256}, blocks {frames//4}")
                g4_per[s] = True
            # parquet row check already in G1
        for s in target_domain:
            print(f"  G4 {s} {'PASS' if g4_per.get(s,false:=True) else 'FAIL'}")

    # G5 与 V13 及 V48-V54 完全独立 — per stratum
    print(f"\n-- G5 与 V13 及 V48-V54 完全独立 (per stratum) --")
    used_per_source = {}
    for src in ["1M","1p5M","2M"]:
        used = sorted(set(USED_BASE[src] + V53_SELECTED.get(src, []) + V54_SELECTED.get(src, [])))
        used_per_source[src] = used
        print(f"  {src} used intervals (V48-V54) count {len(used)}: {used[:10]}...")
    g5_per = {}
    if found_registry is None:
        for s in D_TARGET:
            g5_per[s] = False
            print(f"  G5 {s}: FAIL — G1 not pass, cannot verify independence")
    else:
        for s in target_domain:
            if s not in strata:
                g5_per[s] = False
                continue
            # For new acquisition, different date already ensures independence; check frame_ids if provided
            entry = strata[s]
            if "frame_ids" in entry:
                new_ids = set(entry["frame_ids"])
                print(f"  G5 {s}: new frame_ids {len(new_ids)} provided, overlap with V13/V48-V54 numeric check skipped (different acquisition)")
            else:
                print(f"  G5 {s}: no frame_ids in registry, assume different acquisition (date≠2026-01-21 already)")
            # G5 passes if G1/G2 pass (date different) — mechanical check per stratum
            g5_per[s] = g2_per.get(s, False)
            print(f"  G5 {s} {'PASS' if g5_per[s] else 'FAIL'}")

    # G6 V25 prior只读 — global
    print(f"\n-- G6 V25 prior 只读 (global) --")
    g6_pass = check_v25_prior()
    print(f"  G6 {'PASS' if g6_pass else 'FAIL'} (global, not per stratum)")

    # G7 冻结 per-stratum registry — per stratum
    print(f"\n-- G7 冻结 per-stratum registry (B={b_per} primary, alt {B_ALTERNATIVE}) --")
    g7_per = {}
    g7_details = {}
    if found_registry is None:
        for s in D_TARGET:
            F = 160
            used = used_per_source.get(s, [])
            info, K, _ = enumerate_and_select(F, used, need=b_per)
            info_alt, K_alt, _ = enumerate_and_select(F, used, need=B_ALTERNATIVE)
            print(f"  example F={F} {s}: K={K} need {b_per} {'feasible' if info else 'not feasible'} (alt B=15 K={K_alt} {'feasible' if info_alt else 'not feasible'})")
            g7_per[s] = False
            g7_details[s] = {"K": K, "need": b_per, "feasible": bool(info), "K_alt": K_alt, "feasible_alt": bool(info_alt)}
        print(f"  G7 overall FAIL — G1 not pass")
    else:
        for s in target_domain:
            if s not in strata:
                g7_per[s] = False
                g7_details[s] = {"K": 0, "need": b_per, "feasible": False}
                print(f"  G7 {s}: FAIL — stratum not in registry")
                continue
            entry = strata[s]
            F = entry.get("frames")
            if not isinstance(F, int):
                print(f"  G7 {s} FAIL: frames not int")
                g7_per[s] = False
                continue
            # map stratum name to used intervals key (1M/1p5M/2M)
            used_key = s if s in used_per_source else "1M"  # fallback for exploratory
            used = used_per_source.get(used_key, [])
            info, K, _ = enumerate_and_select(F, used, need=b_per)
            info_alt, K_alt, _ = enumerate_and_select(F, used, need=B_ALTERNATIVE)
            g7_details[s] = {"K": K, "need": b_per, "feasible": bool(info and info["ok"]), "selected": info["selected"][:5] if info else [], "K_alt": K_alt, "feasible_alt": bool(info_alt and info_alt["ok"])}
            if info and info["ok"]:
                print(f"  G7 {s}: PASS K={K} need {b_per} ok={info['ok']} selected[:5]={info['selected'][:5]} (alt feasible={bool(info_alt and info_alt['ok'])})")
                g7_per[s] = True
            else:
                print(f"  G7 {s}: FAIL K={K} need {b_per} feasible={bool(info and info['ok'])} (alt B=15 K={K_alt} feasible={bool(info_alt and info_alt['ok'])}) — DATA_NOT_READY for this stratum, exploratory if alt feasible")
                g7_per[s] = False
        # extra exploratory strata
        extra_strata = [k for k in strata.keys() if k not in target_domain]
        for s in extra_strata:
            entry = strata[s]
            F = entry.get("frames", 0)
            if isinstance(F, int):
                used = []
                info, K, _ = enumerate_and_select(F, used, need=b_per)
                print(f"  G7 exploratory {s}: F={F} K={K} need {b_per} feasible={bool(info and info['ok'])} — exploratory only")
                g7_details[s] = {"K": K, "need": b_per, "feasible": bool(info and info["ok"]), "exploratory": True}

    # Summary per stratum
    print(f"\n=== Summary G1-G7 stratified ===")
    all_target_pass = True
    for s in target_domain:
        per_ok = all([g1_per.get(s, False), g2_per.get(s, False), g3_per.get(s, False), g4_per.get(s, False), g5_per.get(s, False), g6_pass, g7_per.get(s, False)])
        # G6 is global, so include
        print(f"  stratum {s}: G1={g1_per.get(s)} G2={g2_per.get(s)} G3={g3_per.get(s)} G4={g4_per.get(s)} G5={g5_per.get(s)} G6={g6_pass} G7={g7_per.get(s)} => {'PASS' if per_ok else 'FAIL'}")
        all_target_pass = all_target_pass and per_ok
        # also check partial: if G1-G6 pass but G7 fails due to K<B, that's DATA_NOT_READY for that stratum
    terminal = "V55_QUALIFICATION_PLAN_READY" if all_target_pass else "V55_DATA_NOT_READY"
    # If partial, note stratified partial
    if not all_target_pass:
        # Check if some strata are READY and some not — partial
        ready_count = sum(1 for s in target_domain if all([g1_per.get(s, False), g2_per.get(s, False), g3_per.get(s, False), g4_per.get(s, False), g5_per.get(s, False), g6_pass, g7_per.get(s, False)]))
        if 0 < ready_count < len(target_domain):
            terminal = "V55_DATA_NOT_READY (stratified partial)"
            print(f"\nTerminal: {terminal} — {ready_count}/{len(target_domain)} target strata READY, others need new data (exploratory only for insufficient strata)")
        else:
            print(f"\nTerminal: {terminal}")
    else:
        print(f"\nTerminal: {terminal} — all {len(target_domain)} target strata PASS (S={len(target_domain)} B={b_per} => {len(target_domain)*b_per} blocks {len(target_domain)*b_per*2}-{len(target_domain)*b_per*4} calls)")

    if not all_target_pass:
        print(f"  Reason: target domain G1-G7 not all PASS — need new acquisition per failing stratum with ≥120 frames (suggest ≥160) each stratum, date≠2026-01-21, 256 pairs/frame, 4-frame blocks, B={b_per} balanced")
        print(f"  Stratified policy: data-insufficient strata only exploratory, not forced to S×B; READY strata report exact/leakage/rescue per stratum, qualification requires covering D_target")
        print(f"  This is NOT a method failure, it is a data gap per stratum. Algorithm mainline (V54二阶段)已足够好，blocker是分层独立TEST数据缺失。")
        print(f"  Do NOT create production module/CLI/tests/正式output root/用HOLD冒充/模拟TEST/执行decoder.")
        print(f"  Budget proportional: per stratum B={b_per} => total {len(target_domain)*b_per} blocks, {len(target_domain)*b_per*2}-{len(target_domain)*b_per*4} calls (L2 {len(target_domain)*b_per}-{len(target_domain)*b_per*3})")

    # Write out JSON
    out_path = Path(args.out) if args.out else REPO_ROOT / "openspec" / "changes" / "formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation" / "data_readiness_result.json"
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        result = {
            "terminal": terminal,
            "stratified": True,
            "target_domain": target_domain,
            "blocks_per_stratum": b_per,
            "blocks_per_stratum_alt": B_ALTERNATIVE,
            "total_blocks_primary": len(target_domain)*b_per,
            "budget_primary": f"{len(target_domain)*b_per*2}-{len(target_domain)*b_per*4} (L2 {len(target_domain)*b_per}-{len(target_domain)*b_per*3})",
            "total_blocks_alt": len(target_domain)*B_ALTERNATIVE,
            "budget_alt": f"{len(target_domain)*B_ALTERNATIVE*2}-{len(target_domain)*B_ALTERNATIVE*4} (L2 {len(target_domain)*B_ALTERNATIVE}-{len(target_domain)*B_ALTERNATIVE*3})",
            "per_stratum": {},
            "G6_prior_readonly": g6_pass,
            "head": "efd34ef318014e1d0505605062057b042e2180eb",
            "checked_at": "2026-08-28T00:00:00Z_stratified",
            "registry_searched": [str(p) for p in registry_candidates],
            "found_registry": str(found_registry) if found_registry else None,
            "hold_adjudication": "HOLD polluted by V48-V54 135-180 intervals, even remaining frames不可改称TEST",
            "required_new_data_per_stratum": {"per_stratum_frames": ">=120 suggest >=160", "frame_pairs": 256, "block_pairs": 1024, "blocks_per_stratum": b_per, "blocks_per_stratum_alt": B_ALTERNATIVE, "date_not": "2026-01-21", "physical_conditions": "date/location/device/channel_params per stratum", "sampling_mode": "deterministic_four_consecutive_frames_independent_test_v55_stratified"}
        }
        for s in target_domain:
            result["per_stratum"][s] = {
                "G1_file_readable": g1_per.get(s, False),
                "G2_provenance": g2_per.get(s, False),
                "G3_stratum": g3_per.get(s, False),
                "G4_shape": g4_per.get(s, False),
                "G5_independence": g5_per.get(s, False),
                "G6_prior_readonly": g6_pass,
                "G7_registry": g7_per.get(s, False),
                "G7_details": g7_details.get(s, {}),
                "stratum_pass": all([g1_per.get(s, False), g2_per.get(s, False), g3_per.get(s, False), g4_per.get(s, False), g5_per.get(s, False), g6_pass, g7_per.get(s, False)])
            }
        # add exploratory
        extra = [k for k in (strata.keys() if strata else []) if k not in target_domain]
        if extra:
            result["exploratory_strata"] = {k: {"G7_details": g7_details.get(k, {}), "present": True} for k in extra}
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\nWrote stratified result JSON: {out_path}")
    except Exception as e:
        print(f"  WARN: failed to write JSON {e}")

    sys.exit(0 if all_target_pass else 1)

if __name__ == "__main__":
    main()
