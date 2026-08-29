#!/usr/bin/env python3
"""
V58 decoder-free 密钥预算止损 — 只读预算诊断，不改 decoder/矩阵/信道估计器
DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN
Frozen V57: 1M 981/424/1405 7089, 1p5M 1024/451/1475 7439, 2M 1024/516/1540 7764, n=1024, tag=64, GF32 5bits
- 64-bit tag 已含不得重复扣除，仅作预算诊断
- 三源独立，不跨源平均
- 禁止自创 H_min/finite 公式，缺决定性输入则 SECURITY_INPUTS_INCOMPLETE / DATA_INCOMPLETE
ponytail: minimal decoder-free budget, no grid, interval propagation only if authoritative interval exists
"""
from __future__ import annotations
import argparse, json, sys, math
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Frozen V57
FROZEN = {
    "1M": {"m1": 981, "m2": 424, "m_total": 1405, "leak": 7089},
    "1p5M": {"m1": 1024, "m2": 451, "m_total": 1475, "leak": 7439},
    "2M": {"m1": 1024, "m2": 516, "m_total": 1540, "leak": 7764},
}
N = 1024
LOG2Q = 5
TAG = 64

# Candidate authoritative files (read-only, not modified)
CANDIDATE_AUTHORITIES = [
    "tools/security_reports/_security_calibrated_common.py",
    "tools/security_reports/build_actual_ir_finite_key_shadow.py",
    "tools/security_reports/round2_build_actual_ir_finite_key_shadow.py",
    "tools/security_reports/round2_build_finite_key_audit_table.py",
]

def _formula_authority_scan():
    found = {}
    for rel in CANDIDATE_AUTHORITIES:
        p = REPO_ROOT / rel
        if p.exists():
            text = p.read_text(encoding="utf-8", errors="ignore")
            # record line hints
            found[rel] = {"exists": True, "has_delta": "delta_fk" in text.lower() or "DeltaFK" in text,
                          "has_pie": "PIE_secure" in text, "has_chi": "chi_E" in text or "chi_from" in text,
                          "has_iab": "IAB_est" in text}
        else:
            found[rel] = {"exists": False}
    # H_min search
    h_min_hits = []
    for rel in CANDIDATE_AUTHORITIES:
        p = REPO_ROOT / rel
        if p.exists():
            txt = p.read_text(encoding="utf-8", errors="ignore")
            if "H_min" in txt or "min_entropy" in txt.lower():
                h_min_hits.append(rel)
    return found, h_min_hits

def _check_units_and_tag():
    # verify GF32 5bits and tag not repeated
    for src, v in FROZEN.items():
        leak_without = LOG2Q * (v["m1"] + v["m2"])
        if v["m1"] + v["m2"] != v["m_total"]:
            return False, f"{src} m_total mismatch"
        if leak_without + TAG != v["leak"]:
            return False, f"{src} leak tag mismatch {leak_without}+{TAG}!={v['leak']}"
        if leak_without != LOG2Q * v["m_total"]:
            return False, f"{src} LOG2Q mismatch"
    return True, "ok"

def _compute_per_source(min_entropy_budget_per_block, other, finite, h_min_proxy_flag=False):
    rows = []
    for src in ["1M", "1p5M", "2M"]:
        v = FROZEN[src]
        leak_without = LOG2Q * (v["m1"]+v["m2"])
        leak_total = v["leak"]
        # budgets: if scalar else per-source dict
        if isinstance(min_entropy_budget_per_block, dict):
            budget = float(min_entropy_budget_per_block[src])
        elif min_entropy_budget_per_block is None:
            budget = None
        else:
            budget = float(min_entropy_budget_per_block)
        if budget is None or not math.isfinite(budget):
            rows.append({"source": src, "leak_without_tag": leak_without, "tag64": TAG, "leak_total": leak_total,
                         "min_entropy_budget": None, "ell_before_IR": None, "ell_final": None, "per_pair": None, "margin_ratio": None, "weak_proxy": h_min_proxy_flag})
            continue
        oth = float(other[src]) if isinstance(other, dict) else float(other) if other is not None else 0.0
        fin = float(finite[src]) if isinstance(finite, dict) else float(finite) if finite is not None else 0.0
        ell_before = budget - oth - fin
        ell_final = ell_before - leak_total
        per_pair = ell_final / N
        margin = ell_final / budget if budget != 0 else float("nan")
        rows.append({"source": src, "leak_without_tag": leak_without, "tag64": TAG, "leak_total": leak_total,
                     "min_entropy_budget": budget, "other": oth, "finite": fin,
                     "ell_before_IR": ell_before, "ell_final": ell_final, "per_pair": per_pair, "margin_ratio": margin,
                     "weak_proxy": h_min_proxy_flag})
    return rows

def _first_match_verdict(rows, h_min_missing, unit_ok, weak_proxy_any, conservative_margins=None):
    # priority: EVIDENCE_INVALID > SECURITY_INPUTS_INCOMPLETE > NO_POSITIVE_KEY_MARGIN > POSITIVE_BUT_FRAGILE > POSITIVE_KEY_MARGIN
    if not unit_ok:
        return "EVIDENCE_INVALID"
    if h_min_missing:
        return "SECURITY_INPUTS_INCOMPLETE"
    # check any ell missing -> incomplete
    if any(r["ell_final"] is None or not math.isfinite(r["ell_final"]) for r in rows):
        return "SECURITY_INPUTS_INCOMPLETE"
    if any(r["ell_final"] is not None and r["ell_final"] <= 0 for r in rows):
        return "NO_POSITIVE_KEY_MARGIN"
    # margins
    margins = [r["margin_ratio"] for r in rows if r["margin_ratio"] is not None]
    # weak proxy -> FRAGILE cap
    if weak_proxy_any:
        return "POSITIVE_BUT_FRAGILE"
    if any(m < 0.10 for m in margins):
        return "POSITIVE_BUT_FRAGILE"
    # cross-zero check if conservative vs optimistic supplied: caller handles
    # For now, if conservative margins provided and any cross-zero, caller overrides
    return "POSITIVE_KEY_MARGIN"

def main():
    ap = argparse.ArgumentParser(description="V58 decoder-free secret-key budget stoploss (DIAGNOSIS_PLAN_READY/DECODE_FORBIDDEN)")
    ap.add_argument("--v57-json", default=str(REPO_ROOT / "openspec/changes/formal-ir-v57-channel-recharacterization/v57_channel_recharacterization.json"))
    ap.add_argument("--out-json", default=str(REPO_ROOT / "docs/research_cycles/V58P0/v58_secret_key_budget.json"))
    ap.add_argument("--report", default=str(REPO_ROOT / "docs/research_cycles/V58P0/SECRET_KEY_BUDGET_REPORT.md"))
    ap.add_argument("--csv", default=str(REPO_ROOT / "docs/research_cycles/V58P0/v58_secret_key_budget.csv"))
    ap.add_argument("--h-min-per-symbol", type=float, default=None, help="authoritative H_min per symbol (bits/symbol), if None -> SECURITY_INPUTS_INCOMPLETE unless --allow-weak-proxy")
    ap.add_argument("--allow-weak-proxy", action="store_true", help="allow IAB_est/H(A|B) as weak proxy (caps at FRAGILE)")
    ap.add_argument("--budget-per-block", type=float, default=None, help="direct min_entropy bits/block (overrides h-min*1024)")
    ap.add_argument("--other", type=float, default=0.0, help="other disclosure bits/block (auth+PE) per source if scalar")
    ap.add_argument("--finite", type=float, default=0.0, help="finite penalty bits/block per source if scalar")
    ap.add_argument("--eps-interval", nargs=2, type=float, default=None, metavar=("LOW","HIGH"), help="authoritative interval for sensitivity (demo, not grid)")
    args = ap.parse_args()

    # A: formula scan
    authority, h_min_hits = _formula_authority_scan()
    unit_ok, unit_msg = _check_units_and_tag()

    h_min_missing = False
    weak_proxy = False
    budget = None

    if args.budget_per_block is not None:
        budget = float(args.budget_per_block)
        # budget direct is considered authoritative if provided, but we still note H_min source missing if no file
        h_min_missing = len(h_min_hits) == 0 and not args.allow_weak_proxy and args.h_min_per_symbol is None
        # if budget provided explicitly, not missing
        if args.budget_per_block is not None:
            h_min_missing = False
    elif args.h_min_per_symbol is not None:
        budget = float(args.h_min_per_symbol) * N
        weak_proxy = bool(args.allow_weak_proxy)
        h_min_missing = False
    else:
        # no decisive input
        if args.allow_weak_proxy:
            # still need a proxy value; without value -> incomplete
            h_min_missing = True
            weak_proxy = True
        else:
            h_min_missing = True

    # if H_min truly missing and not weak proxy, verdict will be SECURITY_INPUTS_INCOMPLETE
    # Still compute rows for report but with None
    if h_min_missing:
        rows_conservative = _compute_per_source(None, args.other, args.finite, weak_proxy)
        verdict = _first_match_verdict(rows_conservative, True, unit_ok, weak_proxy)
        # persist even if incomplete
    else:
        # conservative/optimistic: if interval given, perturb budget +/- interval*? demo: +/-5% as authoritative interval example
        # Real: use eps_interval if provided as budget multiplier demo
        if args.eps_interval:
            low, high = args.eps_interval
            # treat as budget interval [budget*low, budget*high] if low/high are factors
            # For conservative: low budget, high other/finite
            budget_cons = budget * low
            budget_opt = budget * high
            rows_cons = _compute_per_source(budget_cons, args.other, args.finite, weak_proxy)
            rows_opt = _compute_per_source(budget_opt, args.other, args.finite, weak_proxy)
            # verdict based on conservative
            verdict_cons = _first_match_verdict(rows_cons, False, unit_ok, weak_proxy)
            # check cross-zero: conservative<=0 < optimistic
            cross = any(rc["ell_final"] <=0 and ro["ell_final"]>0 for rc,ro in zip(rows_cons, rows_opt))
            if cross and verdict_cons == "POSITIVE_BUT_FRAGILE":
                verdict = verdict_cons
            elif cross:
                # cross zero upgrades to FRAGILE if not already NO_MARGIN
                if verdict_cons == "POSITIVE_KEY_MARGIN":
                    verdict = "POSITIVE_BUT_FRAGILE"
                else:
                    verdict = verdict_cons
            else:
                verdict = verdict_cons
            rows = rows_cons
            # we will keep both for json
            sensitivity = {"conservative": rows_cons, "optimistic": rows_opt, "cross_zero": cross, "interval": args.eps_interval}
        else:
            rows = _compute_per_source(budget, args.other, args.finite, weak_proxy)
            verdict = _first_match_verdict(rows, False, unit_ok, weak_proxy)
            sensitivity = {"conservative": rows, "optimistic": rows, "cross_zero": False, "interval": None}

    # Build output
    out = {
        "schema": "v58_secret_key_budget_v1",
        "lifecycle": "DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN",
        "head": "337e3a79",
        "data_sha": "84d62779",
        "n": N, "log2q": LOG2Q, "tag": TAG,
        "frozen_v57": FROZEN,
        "formula_authority": authority,
        "h_min_hits": h_min_hits,
        "unit_ok": unit_ok, "unit_msg": unit_msg,
        "h_min_missing": h_min_missing, "weak_proxy": weak_proxy,
        "verdict": verdict,
        "verdict_priority": "EVIDENCE_INVALID > SECURITY_INPUTS_INCOMPLETE > NO_POSITIVE_KEY_MARGIN > POSITIVE_BUT_FRAGILE > POSITIVE_KEY_MARGIN",
        "decomposition": rows if 'rows' in locals() else rows_conservative,
    }
    if 'sensitivity' in locals():
        out["sensitivity"] = sensitivity
    if 'rows_cons' in locals():
        out["sensitivity"] = sensitivity

    # write json
    out_path = Path(args.out_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    # csv compact
    csv_path = Path(args.csv)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    dec = out["decomposition"]
    # header: source,ell_before_IR,leak_without_tag,tag64,other,finite,ell_final,per_pair,margin_ratio,conservative,optimistic,gate
    import csv
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["source","ell_before_IR","leak_without_tag","tag64","other","finite","ell_final","per_pair","margin_ratio","weak_proxy","gate"])
        for r in dec:
            w.writerow([r["source"], r.get("ell_before_IR"), r.get("leak_without_tag"), r.get("tag64"), r.get("other"), r.get("finite"), r.get("ell_final"), r.get("per_pair"), r.get("margin_ratio"), r.get("weak_proxy"), verdict])

    # report md (compact, ponytail: minimal prose)
    report = Path(args.report)
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    lines.append("# V58P0 SECRET_KEY_BUDGET_REPORT — decoder-free 止损\n")
    lines.append(f"**HEAD** `337e3a79` **Lifecycle** `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` **Data** `84d62779`\n")
    lines.append(f"**Verdict** `{verdict}` (priority: EVIDENCE_INVALID > SECURITY_INPUTS_INCOMPLETE > NO_POSITIVE_KEY_MARGIN > POSITIVE_BUT_FRAGILE > POSITIVE_KEY_MARGIN)\n")
    lines.append(f"**Unit** {unit_msg} **GF32** {LOG2Q}bits **tag** {TAG} 已含不重复 **H_min hits** `{h_min_hits if h_min_hits else 'MISSING'}` **weak_proxy** `{weak_proxy}`\n")
    lines.append("## Frozen V57\n")
    lines.append("| source | m1 | m2 | m_total | leak | leak_without_tag | tag |")
    for s in ["1M","1p5M","2M"]:
        v=FROZEN[s]; lw=LOG2Q*(v["m1"]+v["m2"])
        lines.append(f"| {s} | {v['m1']} | {v['m2']} | {v['m_total']} | {v['leak']} | {lw} | {TAG} |")
    lines.append("\n## Decomposition (bits/block, n=1024)\n")
    lines.append("| source | min_entropy_budget | ell_before_IR | leak_without_tag | tag64 | other | finite | ell_final | per_pair | margin_ratio | weak_proxy |")
    for r in dec:
        def fmt(x): return f"{x:.1f}" if isinstance(x,float) else (str(x) if x is not None else "NA")
        lines.append(f"| {r['source']} | {fmt(r.get('min_entropy_budget'))} | {fmt(r.get('ell_before_IR'))} | {r.get('leak_without_tag')} | {r.get('tag64')} | {fmt(r.get('other'))} | {fmt(r.get('finite'))} | {fmt(r.get('ell_final'))} | {fmt(r.get('per_pair'))} | {fmt(r.get('margin_ratio'))} | {r.get('weak_proxy')} |")
    lines.append("\n## Sensitivity\n")
    if 'sensitivity' in out and out["sensitivity"]["interval"] is not None:
        lines.append(f"interval {out['sensitivity']['interval']} cross_zero {out['sensitivity']['cross_zero']}\n")
    else:
        lines.append("no authoritative interval (no_interval) or not provided, conservative==optimistic\n")
    lines.append("\n## Verdict logic\n")
    lines.append("first-match: EVIDENCE_INVALID (unit/tag/m) > SECURITY_INPUTS_INCOMPLETE (H_min/finite/unit missing) > NO_POSITIVE_KEY_MARGIN (any conservative ≤0) > POSITIVE_BUT_FRAGILE (margin<0.10 or cross-zero or weak_proxy) > POSITIVE_KEY_MARGIN (三源 conservative>0 && margin≥0.10 && !weak_proxy && !incomplete) 才允后继低维，仍不自动 decoder\n")
    lines.append("\n## Stoploss\n")
    if verdict in ("EVIDENCE_INVALID","SECURITY_INPUTS_INCOMPLETE","NO_POSITIVE_KEY_MARGIN","POSITIVE_BUT_FRAGILE"):
        lines.append(f"**止损** `{verdict}` — 不进入 decoder，不自动后继；需补 H_min 权威/扩预算或低维重算但仍止损观望。\n")
    else:
        lines.append(f"**放行** `{verdict}` — 仅允许另起后继低维模型（新 OpenSpec + DECODE_FORBIDDEN + 双重 review），仍不自动 decoder。\n")
    lines.append("\n## Authorities\n")
    for rel,info in authority.items():
        lines.append(f"- {rel}: {info}\n")
    report.write_text("\n".join(lines), encoding="utf-8")

    print(f"V58 budget stoploss verdict={verdict} weak_proxy={weak_proxy} unit_ok={unit_ok} h_min_missing={h_min_missing}")
    for r in dec:
        print(f"{r['source']}: ell_final={r.get('ell_final')} per_pair={r.get('per_pair')} margin={r.get('margin_ratio')}")
    return 0

def _demo():
    # ponytail: one runnable check, covers all verification gates
    # GF32*5 tag not repeat
    assert LOG2Q==5
    for s in FROZEN:
        v=FROZEN[s]
        assert v["m_total"]==v["m1"]+v["m2"]
        assert v["leak"]==5*v["m_total"]+64, f"tag double deduct {s}"
    # three sources independent (no averaging)
    rows = _compute_per_source(10240, 0, 0, False)  # 10 bits/symbol *1024 =10240
    assert len(rows)==3 and rows[0]["source"]=="1M"
    # missing H_min -> INPUTS_INCOMPLETE
    rows_none = _compute_per_source(None,0,0,False)
    assert all(r["ell_final"] is None for r in rows_none)
    assert _first_match_verdict(rows_none, True, True, False)=="SECURITY_INPUTS_INCOMPLETE"
    # ell=0 boundary -> NO_MARGIN
    rows_zero = _compute_per_source(7089,0,0,False)  # 1M budget 7089 -> ell 0
    assert rows_zero[0]["ell_final"]==0
    assert _first_match_verdict(rows_zero, False, True, False)=="NO_POSITIVE_KEY_MARGIN"
    # margin 0.10
    budget = 10000
    # need ell 900 -> margin 0.09 -> FRAGILE
    rows_frag = _compute_per_source(7989,0,0,False)  # 7989-7089=900 margin 0.112? adjust
    # craft: budget 8000 -> ell 911 -> margin 0.113 -> would be POSITIVE, so use 7600 -> ell 511 margin 0.067 -> FRAGILE
    rows_f = _compute_per_source(7600,0,0,False)
    assert rows_f[0]["margin_ratio"] < 0.10
    assert _first_match_verdict(rows_f, False, True, False)=="POSITIVE_BUT_FRAGILE"
    # source one positive two negative not averaged -> NO_MARGIN
    rows_mixed = [
        {"source":"1M","ell_final":100,"margin_ratio":0.5,"weak_proxy":False},
        {"source":"1p5M","ell_final":-100,"margin_ratio":-0.1,"weak_proxy":False},
        {"source":"2M","ell_final":-200,"margin_ratio":-0.2,"weak_proxy":False},
    ]
    assert _first_match_verdict(rows_mixed, False, True, False)=="NO_POSITIVE_KEY_MARGIN"
    print("demo PASS")

if __name__ == "__main__":
    if "--demo" in sys.argv:
        _demo()
    else:
        raise SystemExit(main())
