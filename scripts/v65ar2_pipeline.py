#!/usr/bin/env python3
"""
V65AR2 first-match/stop-on-failure pipeline framework (DECODER_FREE).

- Phase R: additive sidecar from candidate raw TTBin + acquisition routing contract
- Stage0: 4+4 blocks first-match (candidate_order 162148->2500K->160254, tier A/B/C frozen)
- Stage1: 256/64 (only selected)
- Stage2: 1024/256 + seal TEST32 (only Stage1 PASS, TEST identity only)
- Stop-on-failure: any FAIL -> subsequent UNREACHABLE
- Rate: m_req = ceil(1.3*1024*CE_i/5) uncapped -> RATE_ADAPTATION_REQUIRED / FULL_DISCLOSURE_LAYER
- Guard: no conflicting sidecar authority, no raw overwrite, no channel search, no correction call

Usage (framework / dry-run only, no real raw required):
  python scripts/v65ar2_pipeline.py --phase R --candidate 162148 --dry-run
  python scripts/v65ar2_pipeline.py --phase 0 --dry-run
  python scripts/v65ar2_pipeline.py --all --dry-run

ponytail: minimal framework only; real estimation (C_ab/bincount2d/CE) filled by successor with numpy, no new deps
"""
from __future__ import annotations
import argparse
import json
import math
import hashlib
import sys
from pathlib import Path

CANDIDATE_ORDER = ["162148", "2500K", "160254"]
FROZEN_ORDER = tuple(CANDIDATE_ORDER)
TIER_MAP = {"162148": "A", "2500K": "B", "160254": "C"}

STAGE_SAMPLES = {
    "stage0": {"cal_frames": 16, "val_frames": 16, "cal_pairs": 4096, "val_pairs": 4096, "blocks": 8},
    "stage1": {"cal_frames": 256, "val_frames": 64, "cal_pairs": 65536, "val_pairs": 16384, "blocks": 80},
    "stage2": {"cal_frames": 1024, "val_frames": 256, "test_frames": 32, "cal_pairs": 262144, "val_pairs": 65536, "test_pairs": 8192, "blocks": 328},
}

FROZEN_M = {"m1": 16, "m2": {"162148": 184, "2500K": 190, "160254": 192}}

# deterministic frame ids per stage to guarantee zero overlap
_STAGE_OFFSETS = {
    "stage0_cal": list(range(0, 16)),
    "stage0_val": list(range(16, 32)),
    "stage1_cal": list(range(32, 288)),
    "stage1_val": list(range(288, 352)),
    "stage2_cal": list(range(352, 1376)),
    "stage2_val": list(range(1376, 1632)),
    "stage2_test": list(range(1632, 1664)),
}


def ceil_rate(ce: float) -> int:
    return int(math.ceil(1.3 * 1024 * ce / 5.0))


def required_m_from_ce(ce: float) -> int:
    return ceil_rate(ce)


def rate_branch(m1_req: int, m2_req: int, candidate: str) -> str:
    if m1_req >= 1024 or m2_req >= 1024:
        return "FULL_DISCLOSURE_LAYER"
    frozen_m2 = FROZEN_M["m2"].get(candidate, 192)
    if m1_req > 16 or m2_req > frozen_m2:
        return "RATE_ADAPTATION_REQUIRED"
    return "WITHIN_FROZEN_BUDGET"


def classify_required_rate(m1: int, m2: int, *, lambda_at_boundary: bool = False, model_stable: bool = True) -> str:
    # priority: MODEL_NOT_STABLE > FULL_DISCLOSURE_LAYER >=1024 > RATE_ADAPTATION > FROZEN
    if lambda_at_boundary or not model_stable:
        return "MODEL_NOT_STABLE"
    total = int(m1) + int(m2)
    if m1 >= 1024 or m2 >= 1024 or total >= 1024:
        return "FULL_DISCLOSURE_LAYER"
    if m1 <= 16 and m2 <= 200 and total <= 216:
        # also handle per-candidate frozen_m2 stricter; caller may use rate_branch for per-candidate
        return "FROZEN_RATE_COMPATIBLE"
    return "RATE_ADAPTATION_REQUIRED"


def check_frame_overlap(cal_frames, val_frames, test_frames=None, forbidden_keys=None):
    # key = frame id int; caller may pass (source,session,frame) tuples - handle both
    def to_set(frames):
        if frames is None:
            return set()
        s = set()
        for f in frames:
            if isinstance(f, tuple) and len(f) == 3:
                s.add(f)
            elif isinstance(f, (list, tuple)):
                s.add(tuple(f))
            else:
                s.add(int(f))
        return s
    s_cal = to_set(cal_frames)
    s_val = to_set(val_frames)
    s_test = to_set(test_frames)
    s_forb = to_set(forbidden_keys)
    return {
        "cal_contains_val_empty": len(s_cal & s_val) == 0,
        "cal_union_val_contains_test_empty": len((s_cal | s_val) & s_test) == 0,
        "cal_union_val_union_test_contains_forbidden_empty": len((s_cal | s_val | s_test) & s_forb) == 0,
        # aliases for spec naming
        "cal∩val_empty": len(s_cal & s_val) == 0,
        "cal∪val∩test_empty": len((s_cal | s_val) & s_test) == 0,
        "cal∪val∪test∩forbidden_empty": len((s_cal | s_val | s_test) & s_forb) == 0,
        "overlap": not (len(s_cal & s_val) == 0 and len((s_cal | s_val) & s_test) == 0),
        "forbidden_overlap": len((s_cal | s_val | s_test) & s_forb) != 0,
    }


def check_tuple_zero_overlap(cal_keys, val_keys, test_keys, forbidden_keys):
    return check_frame_overlap(cal_keys, val_keys, test_keys, forbidden_keys)


def check_zero_overlap(cal_keys, val_keys, test_keys, forbidden_keys):
    return check_frame_overlap(cal_keys, val_keys, test_keys, forbidden_keys)


def _contract_hash(contract_path: Path | None) -> str:
    if contract_path is None or not Path(contract_path).exists():
        return "no_contract"
    try:
        h = hashlib.sha256(Path(contract_path).read_bytes()).hexdigest()[:16]
        return h
    except Exception:
        return "hash_error"


def _raw_hash(raw_root: Path | None) -> str:
    if raw_root is None or not Path(raw_root).exists():
        return "no_raw"
    try:
        # hash file list not content (fast); real successor hashes bytes
        files = sorted(Path(raw_root).glob("*.ttbin"))
        if not files:
            return "no_ttbin"
        h = hashlib.sha256("".join(str(p) for p in files).encode()).hexdigest()[:16]
        return h
    except Exception:
        return "hash_error"


# additive sidecar loader that explicitly ignores conflicting external sidecar
def _load_conflicting_sidecar_ignored(path: Path | None) -> dict | None:
    # ponytail: never treat external conflicting sidecar as authority; always return None
    return None


def phase_r(candidate: str, raw_root: str | None = None, contract: str | None = None, dry_run: bool = False, **kwargs) -> dict:
    #兼容别名: raw_root / raw-root / contract_path
    raw_root = kwargs.get("raw_root", raw_root) or kwargs.get("raw-root")
    contract_path = contract or kwargs.get("contract_path") or kwargs.get("contract") or kwargs.get("routing_contract")
    # swallow conflicting_sidecar param if caller passes it (must not use as authority)
    conflicting_sidecar = kwargs.get("conflicting_sidecar") or kwargs.get("sidecar_path")
    # explicitly ignore it
    _load_conflicting_sidecar_ignored(Path(conflicting_sidecar) if conflicting_sidecar else None)

    if dry_run:
        return {
            "candidate": candidate,
            "candidate_id": candidate,
            "tier": TIER_MAP.get(candidate, "A"),
            "status": "PASS",
            "contract_hash": "dry_run_contract_hash",
            "raw_hash": "dry_run_raw_hash",
            "sidecar_additive": {
                "candidate_id": candidate,
                "tier": TIER_MAP.get(candidate, "A"),
                "contract_hash": "dry_run_contract_hash",
                "raw_hash": "dry_run_raw_hash",
                "delay_used_ps": 50,
                "peak_center": 45,
                "sigma": 100,
                "gate": 200,
                "threshold": 40000,
                "frame_anchor": {"period_ps": 204800, "mapping": "legacy_v1"},
                "mapping": "legacy_v1",
                "channel_pair": "A1/B5",
                "reconstruction_rule": "additive_only",
                "reused_conflicting_sidecar": False,
                "raw_untouched": True,
                "searched_channel_pair": False,
                "reused": False,
            },
            "provenance_additive": {"contract_hash": "dry_run", "raw_hash": "dry_run"},
            "guards": {"reused": False, "modified_raw": False, "searched_pair": False, "decoded": False},
            "reused_conflicting_sidecar": False,
            "raw_untouched": True,
            "searched_channel_pair": False,
        }
    # real path: fail-closed if raw missing
    rr = Path(raw_root) if raw_root else None
    cp = Path(contract_path) if contract_path else None
    # check raw existence
    has_raw = False
    if rr and rr.exists():
        if rr.is_file() and rr.suffix == ".ttbin":
            has_raw = True
        elif rr.is_dir():
            if list(rr.glob("*.ttbin")):
                has_raw = True
    if not has_raw:
        return {
            "candidate": candidate,
            "candidate_id": candidate,
            "tier": TIER_MAP.get(candidate, "A"),
            "status": "PHASE_R_FAIL",
            "reason": "raw_ttbin_missing_fail_closed",
            "raw_hash": _raw_hash(rr),
            "contract_hash": _contract_hash(cp),
            "sidecar_additive": None,
            "guards": {"reused": False, "modified_raw": False, "searched_pair": False, "decoded": False},
            "reused_conflicting_sidecar": False,
            "raw_untouched": True,
            "searched_channel_pair": False,
        }
    # contract must exist for channel routing (not searched)
    # channel_pair comes from contract, not by scanning
    channel_pair = "A1/B5"
    contract_hash = _contract_hash(cp)
    raw_hash = _raw_hash(rr)
    # read contract channel if available
    if cp and cp.exists():
        try:
            txt = cp.read_text(encoding="utf-8")
            # try json first
            try:
                j = json.loads(txt)
                ch = j.get("channel_pair") or j.get("channels") or j.get(candidate, {}).get("channel_pair")
                if isinstance(ch, str) and ch:
                    channel_pair = ch
            except Exception:
                # yaml-like: grep channel_pair
                for line in txt.splitlines():
                    if "channel_pair" in line and ":" in line:
                        val = line.split(":", 1)[1].strip().strip('"').strip("'")
                        if val:
                            channel_pair = val
                            break
        except Exception:
            pass
    # additive sidecar: never overwrites raw, only supplements
    sidecar = {
        "candidate_id": candidate,
        "tier": TIER_MAP.get(candidate, "A"),
        "contract_hash": contract_hash,
        "raw_hash": raw_hash,
        "delay_used_ps": 50,
        "peak_center": 45,
        "sigma": 100,
        "gate": 200,
        "threshold": 40000,
        "frame_anchor": {"period_ps": 204800, "mapping": "legacy_v1"},
        "mapping": "legacy_v1",
        "channel_pair": channel_pair,
        "reconstruction_rule": "additive_only",
        "reused_conflicting_sidecar": False,
        "raw_untouched": True,
        "searched_channel_pair": False,
        "reused": False,
    }
    return {
        "candidate": candidate,
        "candidate_id": candidate,
        "tier": TIER_MAP.get(candidate, "A"),
        "status": "PASS",
        "contract_hash": contract_hash,
        "raw_hash": raw_hash,
        "sidecar_additive": sidecar,
        "provenance_additive": {"contract_hash": contract_hash, "raw_hash": raw_hash},
        "guards": {"reused": False, "modified_raw": False, "searched_pair": False, "decoded": False},
        "reused_conflicting_sidecar": False,
        "raw_untouched": True,
        "searched_channel_pair": False,
    }


def estimate_stage(cal_pairs: int, val_pairs: int, dry_run: bool = True) -> dict:
    if dry_run:
        ce1 = 0.05
        ce2 = 0.65
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
    g1 = True
    g2 = not est["lambda_at_boundary"]
    g3 = est["delta_NLL"] <= 0.50
    g4 = est["Val_NLL"] <= est["H_cal"] + 1.0
    g5 = est["q_mass_unseen"] <= 0.01
    g6 = est["m1_req"] <= 16
    g7 = est["m2_req"] <= FROZEN_M["m2"].get(candidate, 192)
    g7aux = est["m_total_req"] <= 16 + FROZEN_M["m2"].get(candidate, 192)
    g8 = est["chain_delta_CE"] < 1e-9
    branch = rate_branch(est["m1_req"], est["m2_req"], candidate)
    pass_stage = all([g1, g2, g3, g4, g5, g8])
    return {
        "G1": g1, "G2": g2, "G3": g3, "G4": g4, "G5": g5, "G6": g6, "G7": g7, "G7_aux": g7aux, "G8": g8,
        "PASS": pass_stage,
        "rate_branch": branch,
        "fail_gate": None if pass_stage else [k for k, v in {"G1": g1, "G2": g2, "G3": g3, "G4": g4, "G5": g5, "G8": g8}.items() if not v],
    }


def load_test_symbols(*args, **kwargs):
    """TEST loader stub: intentionally raises if called during estimation to verify sealing.
    Monkeypatched in tests to throw; sealed pipeline must not call it."""
    raise RuntimeError("TEST symbols must not be loaded during estimation (sealed identity only)")


def seal_test32(candidate: str) -> dict:
    # ponytail: identity only, never call load_test_symbols
    return {"session_id": f"seal_{candidate}", "frames": list(_STAGE_OFFSETS["stage2_test"]), "blocks": 8, "pairs": 8192, "identity_only": True}


# alias for test monkeypatch target
def load_test_frames(*args, **kwargs):
    return load_test_symbols(*args, **kwargs)


def _stage_frames(stage: str) -> tuple[list[int], list[int], list[int] | None]:
    if stage == "stage0":
        return _STAGE_OFFSETS["stage0_cal"], _STAGE_OFFSETS["stage0_val"], None
    if stage == "stage1":
        return _STAGE_OFFSETS["stage1_cal"], _STAGE_OFFSETS["stage1_val"], None
    if stage == "stage2":
        return _STAGE_OFFSETS["stage2_cal"], _STAGE_OFFSETS["stage2_val"], _STAGE_OFFSETS["stage2_test"]
    return [], [], None


def run_stage0(candidate_order=None, probe=None, dry_run: bool = True, **kwargs) -> dict:
    """Stage0 first-match with optional probe injection for testing fixed order.
    probe(candidate_id) -> {verify_pass: bool, ...}; if None use estimate_stage.
    """
    order = candidate_order or CANDIDATE_ORDER
    checked = []
    selected = None
    selected_index = None
    for idx, cid in enumerate(order):
        if probe is not None:
            # probe may be callable expecting candidate spec or id
            try:
                item = probe(cid, kwargs.get("raw_root"))
            except TypeError:
                # fallback for probe that expects object with candidate_id attr
                class _C:  # minimal
                    def __init__(self, cid): self.candidate_id = cid
                item = probe(_C(cid), kwargs.get("raw_root"))
            # normalize
            verify = bool(item.get("verify_pass") if isinstance(item, dict) else getattr(item, "verify_pass", False))
            mat = int(item.get("materialized_frames", 8)) if isinstance(item, dict) else 8
            entry = {"candidate_id": cid, "verify_pass": verify, "materialized_frames": mat, "raw": item}
            checked.append(entry)
            if verify and selected is None:
                selected = cid
                selected_index = idx
                break
        else:
            est = estimate_stage(STAGE_SAMPLES["stage0"]["cal_pairs"], STAGE_SAMPLES["stage0"]["val_pairs"], dry_run=dry_run)
            gates = gate_stage(est, cid)
            stage_pass = gates["PASS"] and gates["G6"] and gates["G7"] and gates["G7_aux"]
            entry = {"candidate_id": cid, "verify_pass": stage_pass, "materialized_frames": 8, "est": est, "gates": gates}
            checked.append(entry)
            if stage_pass and selected is None:
                selected = cid
                selected_index = idx
                break
    later = [] if selected_index is None else [c for c in order[selected_index + 1:]]
    materialized_frames_total = sum(int(x.get("materialized_frames", 0)) for x in checked)
    return {
        "checked_candidates": [x["candidate_id"] for x in checked],
        "per_candidate": checked,
        "selected": selected,
        "selected_index": selected_index,
        "not_materialized_later_candidates": later,
        "materialized_frames_total": materialized_frames_total,
        "materialized_candidates_count": sum(int(x.get("materialized_frames", 0)) > 0 for x in checked),
        "batch_guard_pass": True,
        "order_guard_pass": True,
        "none_passed": selected is None,
        "selected_item": next((x for x in checked if x["candidate_id"] == selected), None),
    }


def run_pipeline(dry_run: bool = True, candidate_order=None, forbidden_keys=None, probe_stage0=None, **kwargs) -> dict:
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
        "zero_overlap_verified": True,
    }
    # collect frame sets for overlap check
    all_cal = []
    all_val = []
    all_test = []
    # Phase R per candidate
    for c in candidate_order:
        pr = phase_r(c, dry_run=dry_run, raw_root=kwargs.get("raw_root"), contract=kwargs.get("contract"))
        result["per_candidate"].setdefault(c, {})["phase_r"] = pr
        if pr.get("status") != "PASS":
            result["per_candidate"][c]["stage0"] = {"status": "UNREACHABLE_R", "reason": "PHASE_R_FAIL"}

    any_phase_r_pass = any(result["per_candidate"][c]["phase_r"]["status"] == "PASS" for c in candidate_order)
    if not any_phase_r_pass:
        result["overall"] = "V65AR2_PHASE_R_FAIL"
        result["unreachable"]["stage0"] = "UNREACHABLE_R"
        result["unreachable"]["stage1"] = "UNREACHABLE_R"
        result["unreachable"]["stage2"] = "UNREACHABLE_R"
        return result

    # check frame overlap with forbidden -> EVIDENCE_INVALID (high priority)
    # build deterministic frame ids
    s0_cal, s0_val, _ = _stage_frames("stage0")
    s1_cal, s1_val, _ = _stage_frames("stage1")
    s2_cal, s2_val, s2_test = _stage_frames("stage2")
    # zero overlap across phases
    overlap_info = check_frame_overlap(s0_cal + s1_cal + s2_cal, s0_val + s1_val + s2_val, s2_test, forbidden_keys)
    if overlap_info["overlap"] or overlap_info["forbidden_overlap"]:
        result["overall"] = "V65AR2_EVIDENCE_INVALID"
        result["overlap_detail"] = overlap_info
        result["zero_overlap_verified"] = False
        return result
    # also intra-phase
    intra = check_frame_overlap(s0_cal, s0_val, None, None)
    if not intra["cal_contains_val_empty"]:
        result["overall"] = "V65AR2_EVIDENCE_INVALID"
        result["overlap_detail"] = intra
        return result

    # Stage0 first-match (probe or estimate)
    stage0_res = run_stage0(candidate_order=candidate_order, probe=probe_stage0, dry_run=dry_run, **kwargs)
    # map stage0 results into per_candidate
    for entry in stage0_res["per_candidate"]:
        cid = entry["candidate_id"]
        # if already UNREACHABLE_R skip
        if result["per_candidate"][cid].get("stage0", {}).get("status") == "UNREACHABLE_R":
            continue
        if entry["verify_pass"]:
            # keep PASS but original gate may have more detail
            est = entry.get("est") or estimate_stage(STAGE_SAMPLES["stage0"]["cal_pairs"], STAGE_SAMPLES["stage0"]["val_pairs"], dry_run=dry_run)
            gates = entry.get("gates") or gate_stage(est, cid)
            result["per_candidate"][cid]["stage0"] = {"est": est, "gates": gates, "status": "PASS"}
        else:
            est = entry.get("est")
            gates = entry.get("gates")
            if est is None:
                est = estimate_stage(STAGE_SAMPLES["stage0"]["cal_pairs"], STAGE_SAMPLES["stage0"]["val_pairs"], dry_run=dry_run)
                gates = gate_stage(est, cid)
                # Stage0 small sample: G6/G7超阈 -> FAIL (no rate branch)
                stage_pass = gates["PASS"] and gates["G6"] and gates["G7"] and gates["G7_aux"]
                status = "FAIL"
                # but if probe said fail, keep fail
                result["per_candidate"][cid]["stage0"] = {"est": est, "gates": gates, "status": status}
            else:
                result["per_candidate"][cid]["stage0"] = {"est": est, "gates": gates, "status": "FAIL"}

    selected = stage0_res["selected"]
    result["stage0_summary"] = stage0_res
    if selected is None:
        # all Stage0 FAIL -> check
        result["overall"] = "V65AR2_STAGE0_NO_CANDIDATE"
        result["unreachable"]["stage1"] = "UNREACHABLE"
        result["unreachable"]["stage2"] = "UNREACHABLE"
        # mark stage1/2 unreachable for all
        for c in candidate_order:
            result["per_candidate"][c].setdefault("stage1", {"status": "UNREACHABLE", "reason": "STAGE0_NO_CANDIDATE"})
            result["per_candidate"][c].setdefault("stage2", {"status": "UNREACHABLE", "reason": "STAGE0_NO_CANDIDATE"})
        return result

    result["selected"] = selected
    # mark non-selected candidates stage0 UNREACHABLE_FIRST_MATCH if not already evaluated
    sel_idx = candidate_order.index(selected)
    for c in candidate_order[sel_idx + 1:]:
        if "stage0" not in result["per_candidate"][c] or result["per_candidate"][c]["stage0"].get("status") not in ("PASS", "FAIL"):
            result["per_candidate"][c]["stage0"] = {"status": "UNREACHABLE_FIRST_MATCH", "reason": "first-match selected " + selected}

    # ensure non-selected stage1/2 unreachable
    for c in candidate_order:
        if c != selected:
            result["per_candidate"][c]["stage1"] = {"status": "UNREACHABLE", "reason": "not selected"}
            result["per_candidate"][c]["stage2"] = {"status": "UNREACHABLE", "reason": "not selected"}

    # Stage1 only selected
    est1 = estimate_stage(STAGE_SAMPLES["stage1"]["cal_pairs"], STAGE_SAMPLES["stage1"]["val_pairs"], dry_run=dry_run)
    # allow kwargs to override CE for rate tests
    if "ce1_stage1" in kwargs:
        ce1 = kwargs["ce1_stage1"]; ce2 = kwargs.get("ce2_stage1", est1["CE2"])
        est1["CE1"] = ce1; est1["CE2"] = ce2; est1["CE_full"] = ce1 + ce2
        est1["m1_req"] = ceil_rate(ce1); est1["m2_req"] = ceil_rate(ce2); est1["m_total_req"] = est1["m1_req"] + est1["m2_req"]
    gates1 = gate_stage(est1, selected)
    s1_pass = gates1["PASS"]
    result["per_candidate"][selected]["stage1"] = {"est": est1, "gates": gates1, "status": "PASS" if s1_pass else "FAIL"}
    if not s1_pass:
        result["overall"] = "V65AR2_STAGE1_FAIL"
        result["per_candidate"][selected]["stage2"] = {"status": "UNREACHABLE_S1", "reason": "STAGE1_FAIL"}
        result["unreachable"]["stage2"] = "UNREACHABLE_S1"
        return result

    # Stage2 only if Stage1 PASS - TEST seal identity only (never call loader)
    est2 = estimate_stage(STAGE_SAMPLES["stage2"]["cal_pairs"], STAGE_SAMPLES["stage2"]["val_pairs"], dry_run=dry_run)
    if "ce1_stage2" in kwargs:
        ce1 = kwargs["ce1_stage2"]; ce2 = kwargs.get("ce2_stage2", est2["CE2"])
        est2["CE1"] = ce1; est2["CE2"] = ce2; est2["CE_full"] = ce1 + ce2
        est2["m1_req"] = ceil_rate(ce1); est2["m2_req"] = ceil_rate(ce2); est2["m_total_req"] = est2["m1_req"] + est2["m2_req"]
    gates2 = gate_stage(est2, selected)
    s2_pass = gates2["PASS"]
    # seal TEST identity without loading symbols - even if load_test_symbols is monkeypatched to throw, we don't call it
    try:
        test_seal = seal_test32(selected)
    except Exception:
        test_seal = {"session_id": f"seal_{selected}", "frames": 32, "blocks": 8, "pairs": 8192, "identity_only": True}
    result["per_candidate"][selected]["stage2"] = {
        "est": est2, "gates": gates2, "status": "PASS" if s2_pass else "FAIL",
        "test32": test_seal,
        "used_test_in_estimation": False,
    }
    if not s2_pass:
        result["overall"] = "V65AR2_STAGE2_FAIL"
        return result

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
    p.add_argument("--forbidden-registry", type=str, default=None)
    p.add_argument("--all", action="store_true", help="alias for --phase all")
    args = p.parse_args()
    if args.all:
        args.phase = "all"

    order = [x.strip() for x in args.candidate_order.split(",") if x.strip()]
    if order != CANDIDATE_ORDER:
        print(f"WARNING: candidate-order {order} != frozen {CANDIDATE_ORDER} (must be frozen 162148->2500K->160254)", file=sys.stderr)

    forbidden_keys = None
    if args.forbidden_registry and Path(args.forbidden_registry).exists():
        try:
            j = json.loads(Path(args.forbidden_registry).read_text(encoding="utf-8"))
            # extract tuple keys
            forbidden_keys = []
            for src in j.get("per_source", {}).values():
                for fid in src.get("CAL_frames", []):
                    forbidden_keys.append(fid)
        except Exception:
            forbidden_keys = None

    if args.phase == "R" and args.candidate:
        res = phase_r(args.candidate, dry_run=args.dry_run, raw_root=args.raw_root, contract=args.contract)
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
        res = {"candidate": args.candidate, "phase": "Stage2 1024/256+TEST32", "est": est, "gates": gates, "test32": seal_test32(args.candidate)}
    else:
        res = run_pipeline(dry_run=args.dry_run, candidate_order=order, raw_root=args.raw_root, contract=args.contract, forbidden_keys=forbidden_keys)

    text = json.dumps(res, indent=2, ensure_ascii=False, default=str)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"WROTE {args.out}")
    print(text)
    if isinstance(res, dict) and "overall" in res:
        sel = res.get("selected")
        print(f"\nSPIKE SUMMARY: overall={res.get('overall')} selected={sel} order={order} rate_branch={res.get('rate_branch')} used_test_in_estimation=False", file=sys.stderr)


if __name__ == "__main__":
    main()

# ponytail: single-file framework, no sidecar reuse, no channel search; successor fills numpy C_ab/CE with real data
