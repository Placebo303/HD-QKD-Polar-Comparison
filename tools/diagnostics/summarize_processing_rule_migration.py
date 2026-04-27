#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SECURITY_REPORTS = REPO_ROOT / "tools" / "security_reports"
for _p in (REPO_ROOT, SECURITY_REPORTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def _parse_bool(v: Any) -> bool | None:
    if v is None:
        return None
    s = str(v).strip().lower()
    if s in {"true", "1", "yes"}:
        return True
    if s in {"false", "0", "no"}:
        return False
    if s == "":
        return None
    return None


def _parse_int(v: Any) -> int | None:
    try:
        s = str(v).strip()
        if s == "":
            return None
        return int(float(s))
    except Exception:
        return None


def _path_relation_tag(row: dict[str, Any]) -> str:
    if str(row.get("comparison_status") or "") != "ok":
        return "unknown"
    p1 = str(row.get("pairing_path_tag_v1") or "").strip()
    p2 = str(row.get("pairing_path_tag_v2") or "").strip()
    if not p1 or not p2:
        return "unknown"
    return "same_path" if p1 == p2 else "different_path"


def _sequence_relation_tag(row: dict[str, Any]) -> str:
    if str(row.get("comparison_status") or "") != "ok":
        return "unknown"
    a_eq = _parse_bool(row.get("a_sequence_equal"))
    b_eq = _parse_bool(row.get("b_sequence_equal"))
    a_len_same = _parse_bool(row.get("a_len_same"))
    b_len_same = _parse_bool(row.get("b_len_same"))
    if a_eq is True and b_eq is True:
        return "exact_same"
    if a_len_same is True and b_len_same is True:
        return "same_length_but_content_diff"
    if a_len_same is False or b_len_same is False:
        return "length_diff"
    return "unknown"


def _diagnostics_relation_tag(row: dict[str, Any]) -> str:
    if str(row.get("comparison_status") or "") != "ok":
        return "unknown"
    d1 = _parse_int(row.get("frame_diag_available_v1"))
    d2 = _parse_int(row.get("frame_diag_available_v2"))
    if d1 == 1 and d2 == 1:
        return "both_available"
    if d1 == 0 and d2 == 1:
        return "v2_gain"
    if d1 == 0 and d2 == 0:
        return "no_gain"
    return "unknown"


def _migration_class_tag(
    comparison_status: str,
    path_relation_tag: str,
    sequence_relation_tag: str,
    diagnostics_relation_tag: str,
) -> str:
    if comparison_status != "ok":
        return "failed_compare"
    if sequence_relation_tag == "exact_same" and path_relation_tag == "same_path":
        return "stable_equivalent"
    if sequence_relation_tag == "exact_same" and diagnostics_relation_tag in {"both_available", "v2_gain"}:
        return "provenance_gain_only"
    if sequence_relation_tag == "same_length_but_content_diff":
        return "semantic_change_same_length"
    if sequence_relation_tag == "length_diff":
        return "semantic_change_length_diff"
    return "other"


def _migration_recommendation_tag(migration_class_tag: str) -> str:
    if migration_class_tag in {"stable_equivalent", "provenance_gain_only"}:
        return "safe_to_merge"
    if migration_class_tag in {"semantic_change_same_length", "semantic_change_length_diff"}:
        return "keep_legacy_reference"
    if migration_class_tag == "failed_compare":
        return "failed"
    return "needs_more_check"


def main() -> int:
    ap = argparse.ArgumentParser(description="Summarize v1/v2 processing rule migration comparison CSV.")
    ap.add_argument("--comparison-csv", required=True)
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--print-summary", type=int, choices=[0, 1], default=0)
    args = ap.parse_args()

    comparison_csv = Path(args.comparison_csv)
    out_root = Path(args.out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    with comparison_csv.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    summary_rows: list[dict[str, Any]] = []
    overall_counts: Counter[str] = Counter()
    diag_counts: Counter[str] = Counter()
    dim_counts: dict[str, Counter[str]] = defaultdict(Counter)

    for row in rows:
        comparison_status = str(row.get("comparison_status") or "")
        path_relation_tag = _path_relation_tag(row)
        sequence_relation_tag = _sequence_relation_tag(row)
        diagnostics_relation_tag = _diagnostics_relation_tag(row)
        migration_class_tag = _migration_class_tag(
            comparison_status=comparison_status,
            path_relation_tag=path_relation_tag,
            sequence_relation_tag=sequence_relation_tag,
            diagnostics_relation_tag=diagnostics_relation_tag,
        )
        migration_recommendation_tag = _migration_recommendation_tag(migration_class_tag)

        out_row = {
            "dimension": row.get("dimension"),
            "bin_width_ps": row.get("bin_width_ps"),
            "pairing_path_tag_v1": row.get("pairing_path_tag_v1"),
            "pairing_path_tag_v2": row.get("pairing_path_tag_v2"),
            "frame_diag_available_v1": row.get("frame_diag_available_v1"),
            "frame_diag_available_v2": row.get("frame_diag_available_v2"),
            "a_len_same": row.get("a_len_same"),
            "b_len_same": row.get("b_len_same"),
            "a_sequence_equal": row.get("a_sequence_equal"),
            "b_sequence_equal": row.get("b_sequence_equal"),
            "status_v1": row.get("status_v1"),
            "status_v2": row.get("status_v2"),
            "comparison_status": comparison_status,
            "path_relation_tag": path_relation_tag,
            "sequence_relation_tag": sequence_relation_tag,
            "diagnostics_relation_tag": diagnostics_relation_tag,
            "migration_class_tag": migration_class_tag,
            "migration_recommendation_tag": migration_recommendation_tag,
        }
        summary_rows.append(out_row)
        overall_counts[migration_class_tag] += 1
        diag_counts[diagnostics_relation_tag] += 1
        dim_counts[str(row.get("dimension"))][migration_class_tag] += 1

    summary_csv = out_root / "processing_rule_migration_summary.csv"
    with summary_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()) if summary_rows else [])
        if summary_rows:
            w.writeheader()
            w.writerows(summary_rows)

    counts_rows: list[dict[str, Any]] = []
    for metric, value in sorted(overall_counts.items()):
        counts_rows.append({"group_type": "overall", "group_key": "ALL", "metric": metric, "value": value})
    for dim_key in sorted(dim_counts.keys(), key=lambda x: int(x)):
        for metric, value in sorted(dim_counts[dim_key].items()):
            counts_rows.append({"group_type": "dimension", "group_key": dim_key, "metric": metric, "value": value})
    for metric, value in sorted(diag_counts.items()):
        counts_rows.append({"group_type": "diagnostics_relation", "group_key": "ALL", "metric": metric, "value": value})

    counts_csv = out_root / "processing_rule_migration_counts.csv"
    with counts_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["group_type", "group_key", "metric", "value"])
        w.writeheader()
        w.writerows(counts_rows)

    if int(args.print_summary) == 1:
        print(f"total points: {len(summary_rows)}")
        for metric in [
            "stable_equivalent",
            "provenance_gain_only",
            "semantic_change_same_length",
            "semantic_change_length_diff",
            "failed_compare",
        ]:
            print(f"{metric}: {overall_counts.get(metric, 0)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

