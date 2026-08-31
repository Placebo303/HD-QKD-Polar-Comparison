#!/usr/bin/env python3
"""
V65AR2 first-match/stop-on-failure pipeline framework (DECODER_FREE).

- Phase R: additive sidecar from candidate raw TTBin + acquisition routing contract
- Stage0: 4+4 blocks first-match (candidate_order 162148→2500K→160254, tier A/B/C frozen)
- Stage1: 256/64 (only selected)
- Stage2: 1024/256 + seal TEST32 (only Stage1 PASS, TEST identity only)
- Stop-on-failure: any FAIL -> subsequent UNREACHABLE
- Rate: m_req = ceil(1.3*1024*CE_i/5) uncapped -> RATE_ADAPTATION_REQUIRED / FULL_DISCLOSURE_LAYER
- Decoder-free guard: rg "decode_" 0 hits, py_compile PASS, no raw modification, no conflicting sidecar reuse, no channel pair search

Usage (framework / dry-run only, no real raw required):
  python scripts/v65ar2_pipeline.py --phase R --candidate 162148 --dry-run
  python scripts/v65ar2_pipeline.py --phase 0 --dry-run
  python scripts/v65ar2_pipeline.py --phase 1 --candidate 162148 --dry-run
  python scripts/v65ar2_pipeline.py --phase 2 --candidate 162148 --dry-run
  python scripts/v65ar2_pipeline.py --all --dry-run

ponytail: minimal framework only; real estimation (C_ab/bincount2d/CE) filled by successor with numpy, no new deps
"""
from __future__ import annotations
import argparse
import json
import math
import sys
from pathlib import Path

CANDIDATE_ORDER = ["162148", "2500K", "160254"]
TIER_MAP = {"162148": "A", "2500K": "B", "160254": "C"}  # frozen tie, example binding

STAGE_SAMPLES = {
    "stage0": {"cal_frames": 16, "val_frames": 16, "cal_pairs": 4096, "val_pairs": 4096, "blocks": 8},  # 4+4 blocks
    "stage1": {"cal_frames": 256, "val_frames": 64, "cal_pairs": 65536, "val_pairs": 16384, "blocks": 80},
    "stage2": {"cal_frames": 1024, "val_frames": 256, "test_frames": 32, "cal_pairs": 262144, "val_pairs": 65536, "test_pairs": 8192, "blocks": 328},
}

FROZEN_M = {"m1": 16, "m2": {"162148": 184, "2500K": 190, "160254": 192}}  # per candidate old capacity, also 1M/1p5M/2M mapping


def ceil_rate(ce: float) -> int:
    # ponytail: stdlib math.ceil only
    return int(math.ceil(1.3 * 1024 * ce / 5.0))


def rate_branch(m1_req: int, m2_req: int, candidate: str) -> str:
    if m1_req >= 1024 or m2_req >= 1024:
        return "FULL_DISCLOSURE_LAYER"
    frozen_m2 = FROZEN_M["m2"].get(candidate, 192)
    if m1_req > 16 or m2_req > frozen_m2:
        return "RATE_ADAPTATION_REQUIRED"
    return "WITHIN_FROZEN_BUDGET"


def phase_r(candidate: str, dry_run: bool, contract: str | None, raw_root: str | None) -> dict:
    # Additive sidecar reconstruction (framework only, no real TTBin I/O in dry-run)
    if dry_run:
        return {
            "candidate": candidate,
            "tier": TIER_MAP.get(candidate, "A"),
            "status": "PASS",
            "contract_hash": "dry_run_contract_hash",
            "raw_hash": "dry_run_raw_hash",
            "sidecar_additive": {
                "candidate_id": candidate,
                "tier": TIER_MAP.get(candidate, "A"),
                "delay_used_ps": 50,
                "peak_center": 45,
                "sigma": 100,
                "gate": 200,
                "threshold": 40000,
                "channel_pair": "A1/B5",
                "reconstruction_rule": "additive_only",
                "reused_conflicting_sidecar": False,
                "raw_untouched": True,
                "searched_channel_pair": False,
            },
            "guards": {"reused": False, "modified_raw": False, "searched_pair": False, "decoded": False},
            "provenance_additive": {"contract_hash": "dry_run", "raw_hash": "dry_run"},
        }
    # real path: must read candidate raw TTBin + contract, forbid reuse/search/decode
    # successor implements with numpy/pandas only; this framework stops at dry-run when no real data
    return {"candidate": candidate, "status": "PHASE_R_FAIL", "reason": "real raw not implemented in framework (successor fills)"}


def estimate_stage(cal_pairs: int, val_pairs: int, dry_run: bool) -> dict:
    # Hierarchical estimator placeholder: C_ab -> P_global -> P_lambda -> CE1/CE2 -> m_req
    # dry-run returns synthetic CE values for framework self-check only, not real data
    if dry_run:
        # synthetic CE in [0.1, 0.9] bits/symbol range, deterministic per call for self-check
        ce1 = 0.12
        ce2 = 0.80
        ce_full = ce1 + ce2
        chain_delta = abs(ce_full - ce1 - ce2)
        m1_req = ceil_rate(ce1)
        m2_req = ceil_rate(ce2)
        return {
            "CE1": ce1, "CE2": ce2, "CE_full": ce_full, "chain_delta_CE": chain_delta,
            "m1_req": m1_req, "m2_req": m2_req, "m_total_req": m1_req + m2_req,
            "lambda_star": 10.0, "lambda_at_boundary": False,
            "CV_NLL": 0.9, "Val_NLL": 0.95, "delta_NLL": 0.05,
            "MAP_acc": 0.85, "q_mass_unseen": 0.005, "effective_contexts": 900,
            "H_cal": 0.85, "H1_cal": 0.05, "H2_cal": 0.80, "chain_delta_H": 0.0,
            "used_test_in_estimation": False,
        }
    raise NotImplementedError("real estimation requires numpy bincount2d (successor implements)")


def gate_stage(est: dict, candidate: str) -> dict:
    # G1-8 simplified gates (framework)
    g1 = True  # contract consistent (dry-run)
    g2 = not est["lambda_at_boundary"]
    g3 = est["delta_NLL"] <= 0.50
    g4 = est["Val_NLL"] <= est["H_cal"] + 1.0
    g5 = est["q_mass_unseen"] <= 0.01
    g6 = est["m1_req"] <= 16
    g7 = est["m2_req"] <= FROZEN_M["m2"].get(candidate, 192)
    g7aux = est["m_total_req"] <= 16 + FROZEN_M["m2"].get(candidate, 192)
    g8 = est["chain_delta_CE"] < 1e-9  # CE chain closed
    branch = rate_branch(est["m1_req"], est["m2_req"], candidate)
    # G6/G7超阈不作FAIL而入速率分支，仅G1-5/G8判FAIL
    pass_stage = all([g1, g2, g3, g4, g5, g8])
    return {
        "G1": g1, "G2": g2, "G3": g3, "G4": g4, "G5": g5, "G6": g6, "G7": g7, "G7_aux": g7aux, "G8": g8,
        "PASS": pass_stage,
        "rate_branch": branch,
        "fail_gate": None if pass_stage else [k for k, v in {"G1": g1, "G2": g2, "G3": g3, "G4": g4, "G5": g5, "G8": g8}.items() if not v],
    }


def run_pipeline(dry_run: bool = True, candidate_order=None, out_dir: str | None = None) -> dict:
    candidate_order = candidate_order or CANDIDATE_ORDER
    result: dict = {
        "candidate_order": candidate_order,
        "tier_map": {c: TIER_MAP.get(c, "A") for c in candidate_order},
        "per_candidate": {},
        "selected": None,
        "overall": None,
        "unreachable": {},
        "lifecycle": "PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED",
        "decoder_free": True,
        "used_test_in_estimation": False,
    }

    # Phase R per candidate
    for c in candidate_order:
        pr = phase_r(c, dry_run=dry_run, contract=None, raw_root=None)
        result["per_candidate"].setdefault(c, {})["phase_r"] = pr
        if pr.get("status") != "PASS":
            result["per_candidate"][c]["stage0"] = {"status": "UNREACHABLE_R", "reason": "PHASE_R_FAIL"}

    # Stage0 first-match
    any_phase_r_pass = any(result["per_candidate"][c]["phase_r"]["status"] == "PASS" for c in candidate_order)
    if not any_phase_r_pass:
        result["overall"] = "V65AR2_PHASE_R_FAIL"
        result["unreachable"]["stage0"] = "UNREACHABLE_R"
        result["unreachable"]["stage1"] = "UNREACHABLE_R"
        result["unreachable"]["stage2"] = "UNREACHABLE_R"
        return result

    selected = None
    all_stage0_fail = True
    for c in candidate_order:
        if result["per_candidate"][c].get("stage0", {}).get("status") == "UNREACHABLE_R":
            continue
        est = estimate_stage(STAGE_SAMPLES["stage0"]["cal_pairs"], STAGE_SAMPLES["stage0"]["val_pairs"], dry_run=dry_run)
        gates = gate_stage(est, c)
        # Stage0: G6/G7超阈即FAIL（小样本早筛，不分支）
        stage_pass = gates["PASS"] and gates["G6"] and gates["G7"] and gates["G7_aux"]
        result["per_candidate"][c]["stage0"] = {"est": est, "gates": gates, "status": "PASS" if stage_pass else "FAIL"}
        if stage_pass and selected is None:
            selected = c
            all_stage0_fail = False
            # remaining candidates after first PASS mark UNREACHABLE_FIRST_MATCH
            continue
        if stage_pass:
            all_stage0_fail = False

    # mark candidates after selected as UNREACHABLE_FIRST_MATCH
    if selected is not None:
        sel_idx = candidate_order.index(selected)
        for c in candidate_order[sel_idx + 1:]:
            if result["per_candidate"][c]["stage0"]["status"] == "FAIL":
                # already evaluated before selected? shouldn't happen because selected is first PASS
                pass
            elif result["per_candidate"][c]["stage0"]["status"] not in ("PASS", "FAIL"):
                result["per_candidate"][c]["stage0"] = {"status": "UNREACHABLE_FIRST_MATCH", "reason": "first-match selected " + selected}
            elif result["per_candidate"][c]["stage0"]["status"] == "FAIL" and candidate_order.index(c) > sel_idx:
                # keep FAIL but note not selected
                pass
        result["selected"] = selected
    else:
        # all Stage0 FAIL -> check if any PASS existed
        if all(result["per_candidate"][c]["stage0"]["status"] == "FAIL" for c in candidate_order if "stage0" in result["per_candidate"][c]):
            result["overall"] = "V65AR2_STAGE0_NO_CANDIDATE"
            result["unreachable"]["stage1"] = "UNREACHABLE"
            result["unreachable"]["stage2"] = "UNREACHABLE"
            return result

    # Stage1 only selected
    assert selected is not None
    # ensure non-selected candidates stage1 unreachable
    for c in candidate_order:
        if c != selected:
            result["per_candidate"][c]["stage1"] = {"status": "UNREACHABLE", "reason": "not selected"}
            result["per_candidate"][c]["stage2"] = {"status": "UNREACHABLE", "reason": "not selected"}

    est1 = estimate_stage(STAGE_SAMPLES["stage1"]["cal_pairs"], STAGE_SAMPLES["stage1"]["val_pairs"], dry_run=dry_run)
    gates1 = gate_stage(est1, selected)
    s1_pass = gates1["PASS"]  # G6/G7超阈不判FAIL而入分支
    result["per_candidate"][selected]["stage1"] = {"est": est1, "gates": gates1, "status": "PASS" if s1_pass else "FAIL"}
    if not s1_pass:
        result["overall"] = "V65AR2_STAGE1_FAIL"
        result["per_candidate"][selected]["stage2"] = {"status": "UNREACHABLE_S1", "reason": "STAGE1_FAIL"}
        result["unreachable"]["stage2"] = "UNREACHABLE_S1"
        return result

    # Stage2 only if Stage1 PASS
    est2 = estimate_stage(STAGE_SAMPLES["stage2"]["cal_pairs"], STAGE_SAMPLES["stage2"]["val_pairs"], dry_run=dry_run)
    gates2 = gate_stage(est2, selected)
    s2_pass = gates2["PASS"]
    result["per_candidate"][selected]["stage2"] = {
        "est": est2, "gates": gates2, "status": "PASS" if s2_pass else "FAIL",
        "test32": {"session_id": "seal_dry_run", "frames": 32, "blocks": 8, "pairs": 8192, "identity_only": True},
    }
    if not s2_pass:
        result["overall"] = "V65AR2_STAGE2_FAIL"
        return result

    # rate branch dominates over READY if超旧容量
    branch = rate_branch(est2["m1_req"], est2["m2_req"], selected)
    if branch == "FULL_DISCLOSURE_LAYER":
        result["overall"] = "V65AR2_FULL_DISCLOSURE_LAYER"
    elif branch == "RATE_ADAPTATION_REQUIRED":
        result["overall"] = "V65AR2_RATE_ADAPTATION_REQUIRED"
    else:
        result["overall"] = "V65AR2_READY"
    result["rate_branch"] = branch
    return result


def main():
    p = argparse.ArgumentParser(description="V65AR2 pipeline framework (DECODER_FREE, dry-run default)")
    p.add_argument("--phase", choices=["R", "0", "1", "2", "all"], default="all", help="phase to run")
    p.add_argument("--candidate", type=str, default=None, help="single candidate id")
    p.add_argument("--candidate-order", type=str, default=",".join(CANDIDATE_ORDER), help="comma-separated frozen order")
    p.add_argument("--dry-run", action="store_true", default=True, help="framework dry-run (no real raw)")
    p.add_argument("--no-dry-run", dest="dry_run", action="store_false", help="disable dry-run (requires real data)")
    p.add_argument("--out", type=str, default=None, help="output json path")
    p.add_argument("--raw-root", type=str, default=None)
    p.add_argument("--contract", type=str, default=None)
    args = p.parse_args()

    order = [x.strip() for x in args.candidate_order.split(",") if x.strip()]
    # guard frozen order
    if order != CANDIDATE_ORDER:
        print(f"WARNING: candidate-order {order} != frozen {CANDIDATE_ORDER} (must be frozen 162148→2500K→160254)", file=sys.stderr)

    if args.phase == "R" and args.candidate:
        res = phase_r(args.candidate, dry_run=args.dry_run, contract=args.contract, raw_root=args.raw_root)
    elif args.phase == "0" and args.candidate:
        est = estimate_stage(STAGE_SAMPLES["stage0"]["cal_pairs"], STAGE_SAMPLES["stage0"]["val_pairs"], dry_run=args.dry_run)
        gates = gate_stage(est, args.candidate)
        res = {"candidate": args.candidate, "phase": "Stage0 4+4", "est": est, "gates": gates}
    elif args.phase == "1" and args.candidate:
        est = estimate_stage(STAGE_SAMPLES["stage1"]["cal_pairs"], STAGE_SAMPLES["stage1"]["val_pairs"], dry_run=args.dry_run)
        gates = gate_stage(est, args.candidate)
        res = {"candidate": args.candidate, "phase": "Stage1 256/64", "est": est, "gates": gates}
    elif args.phase == "2" and args.candidate:
        est = estimate_stage(STAGE_SAMPLES["stage2"]["cal_pairs"], STAGE_SAMPLES["stage2"]["val_pairs"], dry_run=args.dry_run)
        gates = gate_stage(est, args.candidate)
        res = {"candidate": args.candidate, "phase": "Stage2 1024/256+TEST32", "est": est, "gates": gates, "test32": {"identity_only": True, "frames": 32}}
    else:
        res = run_pipeline(dry_run=args.dry_run, candidate_order=order)

    text = json.dumps(res, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"WROTE {args.out}")
    print(text)
    # spike summary
    if isinstance(res, dict) and "overall" in res:
        sel = res.get("selected")
        print(f"\nSPIKE SUMMARY: overall={res.get('overall')} selected={sel} order={order} rate_branch={res.get('rate_branch')} used_test_in_estimation=False", file=sys.stderr)


if __name__ == "__main__":
    main()

# ponytail: single-file framework, no decode_, no sidecar reuse, no channel search; successor fills numpy C_ab/CE with real data

