"""Read-only, paired stage-cap ablation for the persisted V64 records."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORDS = ROOT / "comparison_bench/outputs_comparison/formal_ir_methods/v64_full_symbol_verification/run_01/v64_records.json"
DEFAULT_SUMMARY = DEFAULT_RECORDS.with_name("v64_summary.json")
SOURCES = ("1M", "1p5M", "2M")
M_SOURCE = {"1M": 184, "1p5M": 190, "2M": 192}
STAGES = {"base": 0, "delta8": 1, "delta16": 2}
STAGE_NAMES = {v: k for k, v in STAGES.items()}
FIELDS = (
    "block_id", "source", "frame_ids", "exact_u1", "exact_l2", "exact_full",
    "syndrome_ok_l1", "syndrome_ok_l2", "tag_ok_l2", "tag_ok_full",
    "errors_u1", "errors_u2", "stage_used", "leak_total", "decoder_calls",
    "accepted_l2", "accepted_full", "undetected_l2", "undetected_full",
)
BOOL_FIELDS = tuple(key for key in FIELDS if key.startswith(("exact", "syndrome", "tag", "accepted", "undetected")))


def _validate(records: list[dict[str, Any]], summary: dict[str, Any] | None = None, *, v64: bool = True) -> dict[str, Any]:
    if v64 and len(records) != 24:
        raise ValueError(f"V64 requires 24 records, got {len(records)}")
    ids = [row.get("block_id") for row in records]
    if any(not isinstance(value, str) or not value for value in ids) or len(set(ids)) != len(ids):
        raise ValueError("records need unique non-empty string block_id values")
    source_counts, stage_counts = Counter(), Counter()
    total_calls = total_leak = 0
    for row in records:
        missing = [key for key in FIELDS if key not in row]
        if missing:
            raise ValueError(f"{row.get('block_id', '?')}: missing {missing}")
        source, stage = row["source"], row["stage_used"]
        if source not in M_SOURCE or stage not in STAGES:
            raise ValueError(f"{row['block_id']}: invalid source/stage {source!r}/{stage!r}")
        if any(not isinstance(row[key], bool) for key in BOOL_FIELDS):
            raise ValueError(f"{row['block_id']}: boolean field has non-bool value")
        if row["exact_full"] != (row["exact_u1"] and row["exact_l2"]):
            raise ValueError(f"{row['block_id']}: exact decomposition mismatch")
        if row["accepted_l2"] != (row["syndrome_ok_l2"] and row["tag_ok_l2"]):
            raise ValueError(f"{row['block_id']}: L2 acceptance mismatch")
        if row["accepted_full"] != (row["syndrome_ok_l2"] and row["tag_ok_full"]):
            raise ValueError(f"{row['block_id']}: full acceptance mismatch")
        if row["undetected_l2"] != (row["accepted_l2"] and not row["exact_full"]):
            raise ValueError(f"{row['block_id']}: L2 undetected mismatch")
        if row["undetected_full"] != (row["accepted_full"] and not row["exact_full"]):
            raise ValueError(f"{row['block_id']}: full undetected mismatch")
        if STAGES[stage] < 2 and not row["accepted_full"]:
            raise ValueError(f"{row['block_id']}: early terminal stage is not accepted")
        calls = 2 + STAGES[stage]
        leak = 80 + 5 * M_SOURCE[source] + 40 * STAGES[stage] + 64
        if row["decoder_calls"] != calls or row["leak_total"] != leak:
            raise ValueError(f"{row['block_id']}: terminal call/leak mismatch")
        if not isinstance(row["frame_ids"], list) or not row["frame_ids"] or any(not isinstance(x, int) for x in row["frame_ids"]):
            raise ValueError(f"{row['block_id']}: invalid frame_ids")
        if any(not isinstance(row[key], int) or row[key] < 0 for key in ("errors_u1", "errors_u2")):
            raise ValueError(f"{row['block_id']}: invalid error counts")
        source_counts[source] += 1
        stage_counts[stage] += 1
        total_calls += row["decoder_calls"]
        total_leak += row["leak_total"]
    if v64 and any(source_counts[source] != 8 for source in SOURCES):
        raise ValueError(f"V64 requires 8 records/source, got {dict(source_counts)}")
    summary_ok = None
    if summary is not None:
        checks = {
            "total_blocks": summary.get("total_blocks") == len(records),
            "total_calls": summary.get("total_calls") == total_calls,
            "stage_used": summary.get("stage_used") == dict(stage_counts),
            "exact_full": summary.get("exact_full") == sum(row["exact_full"] for row in records),
            "accepted_full": summary.get("accepted_full") == sum(row["accepted_full"] for row in records),
            "undetected_full": summary.get("undetected_full") == sum(row["undetected_full"] for row in records),
        }
        summary_ok = all(checks.values())
        if v64 and not summary_ok:
            raise ValueError(f"summary disagrees with records: {checks}")
    return {"unique_block_ids": True, "records": len(records), "per_source": dict(source_counts),
            "stage_used": dict(stage_counts), "summary_consistent": summary_ok,
            "total_calls": total_calls, "total_leak_bits": total_leak}


def _cap(records: list[dict[str, Any]], cap: int) -> dict[str, Any]:
    out = {key: 0 for key in ("attempted_blocks", "verified_exact", "unverified", "accepted_wrong", "undetected", "unreached_final", "reached_rejected", "calls", "disclosed_bits")}
    spent = Counter()
    out["attempted_blocks"] = len(records)
    for row in records:
        observed = STAGES[row["stage_used"]]
        used = min(observed, cap)
        reached = observed <= cap
        accepted_wrong = reached and row["accepted_full"] and not row["exact_full"]
        out["verified_exact"] += reached and row["accepted_full"] and row["exact_full"]
        out["accepted_wrong"] += accepted_wrong
        out["undetected"] += reached and row["undetected_full"]
        out["unreached_final"] += not reached
        out["reached_rejected"] += reached and not row["accepted_full"]
        out["calls"] += 2 + used
        out["disclosed_bits"] += 80 + 5 * M_SOURCE[row["source"]] + 40 * used + 64
        spent[STAGE_NAMES[used]] += 1
    out["unverified"] = out["unreached_final"] + out["reached_rejected"]
    if out["accepted_wrong"] != out["undetected"]:
        raise ValueError(f"cap {cap}: accepted-wrong/undetected mismatch")
    if out["attempted_blocks"] != out["verified_exact"] + out["unverified"] + out["undetected"]:
        raise ValueError(f"cap {cap}: outcome partition mismatch")
    out.update({"cap_index": cap, "cap_stage": STAGE_NAMES[cap], "spent_stage_counts": dict(spent),
                "unknown_for_unreached": {"blocks": out["unreached_final"], "earlier_exactness": "UNKNOWN", "earlier_error_counts": "UNKNOWN"}})
    return out


def _failures(records: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for row in records:
        if row["exact_full"]:
            continue
        rows.append({key: row[key] for key in ("block_id", "source", "frame_ids", "errors_u1", "errors_u2", "syndrome_ok_l1", "syndrome_ok_l2", "tag_ok_l2", "tag_ok_full", "accepted_full", "undetected_full", "stage_used")}
                    | {"failure_kind": "accepted_wrong" if row["accepted_full"] else "rejected"})
    per_source = {}
    for source in SOURCES:
        selected = [row for row in rows if row["source"] == source]
        per_source[source] = {"denominator": sum(row["source"] == source for row in records), "failures": len(selected),
                              "rejected": sum(not row["accepted_full"] for row in selected),
                              "accepted_wrong": sum(row["accepted_full"] for row in selected),
                              "undetected": sum(row["undetected_full"] for row in selected),
                              "by_terminal_stage": dict(Counter(row["stage_used"] for row in selected))}
    return {"overall": {"denominator": len(records), "failures": len(rows), "rejected": sum(not row["accepted_full"] for row in rows), "accepted_wrong": sum(row["accepted_full"] for row in rows), "undetected": sum(row["undetected_full"] for row in rows)},
            "per_source": per_source, "records": rows}


def analyze_records(records: list[dict[str, Any]], summary: dict[str, Any] | None = None, *, require_v64: bool = True) -> dict[str, Any]:
    checks = _validate(records, summary, v64=require_v64)
    caps = {str(cap): {"overall": _cap(records, cap), "per_source": {source: _cap([row for row in records if row["source"] == source], cap) for source in SOURCES}} for cap in range(3)}
    return {"schema": "v64_stage_ablation_v1", "checks": checks, "caps": caps, "final_observed_failures": _failures(records),
            "claim_boundary": ["V64 retrospective only; no decoder import or call.", "Caps are paired policy reconstructions: extra stages add rows and decoder calls.", "Unverified excludes accepted-wrong; partition is verified_exact + unverified + undetected.", "Unreached final outcomes keep earlier exactness and residual errors UNKNOWN.", "Two failures do not support causal or temporal clustering claims."]}


def _self_check() -> None:
    def make(block_id: str, stage: str, exact: bool, accepted: bool, wrong: bool = False) -> dict[str, Any]:
        return {"block_id": block_id, "source": "1M", "frame_ids": [0], "exact_u1": True, "exact_l2": exact, "exact_full": exact,
                "syndrome_ok_l1": True, "syndrome_ok_l2": accepted, "tag_ok_l2": accepted, "tag_ok_full": accepted,
                "errors_u1": 0, "errors_u2": 0 if exact else 1, "stage_used": stage,
                "leak_total": 1064 + 40 * STAGES[stage], "decoder_calls": 2 + STAGES[stage], "accepted_l2": accepted,
                "accepted_full": accepted, "undetected_l2": wrong, "undetected_full": wrong}
    result = analyze_records([make("base", "base", True, True), make("delta8", "delta8", True, True), make("wrong", "delta16", False, True, True)], require_v64=False)
    expected = {"0": (1, 2, 0, 0, 6, 3192), "1": (2, 1, 0, 0, 8, 3272), "2": (2, 0, 1, 1, 9, 3312)}
    for cap, values in expected.items():
        got = result["caps"][cap]["overall"]
        actual = tuple(got[key] for key in ("verified_exact", "unverified", "accepted_wrong", "undetected", "calls", "disclosed_bits"))
        if actual != values:
            raise AssertionError(f"self-check cap {cap}: {actual} != {values}")
    if result["final_observed_failures"]["overall"]["accepted_wrong"] != 1:
        raise AssertionError("accepted-wrong was not separated")
    if result["caps"]["2"]["overall"]["unverified"] != 0:
        raise AssertionError("fully reached accepted-wrong must not enter unverified")
    probe = make("l2_probe", "delta16", False, True)
    probe.update({"exact_u1": False, "exact_l2": True, "exact_full": False, "errors_u1": 1, "errors_u2": 0,
                  "tag_ok_full": False, "accepted_full": False, "undetected_l2": True, "undetected_full": False})
    _validate([probe], v64=False)
    if not (probe["accepted_l2"] and probe["undetected_l2"] and not probe["accepted_full"] and not probe["undetected_full"]):
        raise AssertionError("L2-only acceptance/U1-error probe failed")


def _load(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        _self_check()
    records, summary = _load(args.records), _load(args.summary)
    if not isinstance(records, list) or not all(isinstance(row, dict) for row in records) or not isinstance(summary, dict):
        raise ValueError("records must be a list of objects and summary an object")
    result = analyze_records(records, summary)
    if args.self_check:
        result["self_check"] = "PASS"
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
