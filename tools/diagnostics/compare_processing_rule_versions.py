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
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.workflow.export_joint_sequence_sidecar import export_sidecar_for_point  # type: ignore

DEFAULT_POINTS = [
    "4,30",
    "16,50",
    "128,80",
    "256,120",
    "1024,30",
    "2048,30",
    "4096,40",
]

PROCESSING_RULES = ["legacy_v1", "pairing_v2"]


def _parse_point(point: str) -> tuple[int, int]:
    left, right = [x.strip() for x in str(point).split(",", 1)]
    return int(left), int(right)


def _load_point_specs(points_csv: str | None, points_cli: list[str]) -> list[dict[str, Any]]:
    if points_csv:
        rows: list[dict[str, Any]] = []
        with Path(points_csv).open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader, start=2):
                label = str(row.get("point_label") or "").strip()
                dim_raw = row.get("dimension")
                bw_raw = row.get("bin_width_ps")
                try:
                    if dim_raw is None or str(dim_raw).strip() == "":
                        raise ValueError("missing dimension")
                    if bw_raw is None or str(bw_raw).strip() == "":
                        raise ValueError("missing bin_width_ps")
                    d = int(float(str(dim_raw).strip()))
                    bw = int(round(float(str(bw_raw).strip())))
                    rows.append(
                        {
                            "point": f"{d},{bw}",
                            "dimension": d,
                            "bin_width_ps": bw,
                            "point_label": label,
                            "parse_error": "",
                        }
                    )
                except Exception as e:
                    rows.append(
                        {
                            "point": "",
                            "dimension": str(dim_raw or ""),
                            "bin_width_ps": str(bw_raw or ""),
                            "point_label": label,
                            "parse_error": f"csv_row_parse_error(line={idx}): {e}",
                        }
                    )
        return rows
    if points_cli:
        out: list[dict[str, Any]] = []
        for p in points_cli:
            d, bw = _parse_point(p)
            out.append(
                {
                    "point": p,
                    "dimension": d,
                    "bin_width_ps": bw,
                    "point_label": "",
                    "parse_error": "",
                }
            )
        return out
    return [
        {
            "point": p,
            "dimension": _parse_point(p)[0],
            "bin_width_ps": _parse_point(p)[1],
            "point_label": "",
            "parse_error": "",
        }
        for p in DEFAULT_POINTS
    ]


def _sha256_array(path: Path) -> str | None:
    if not path.exists():
        return None
    arr = np.load(path)
    h = hashlib.sha256()
    h.update(np.ascontiguousarray(arr).view(np.uint8).tobytes())
    return h.hexdigest()


def _load_array(path: Path) -> np.ndarray | None:
    if not path.exists():
        return None
    return np.asarray(np.load(path))


def _safe_float(v: Any) -> float | None:
    try:
        return float(v)
    except Exception:
        return None


def _safe_int(v: Any) -> int | None:
    try:
        return int(v)
    except Exception:
        return None


def _read_sidecar_fields(sidecar_root: Path) -> dict[str, Any]:
    out: dict[str, Any] = {
        "processing_rule_version": None,
        "pairing_path_tag": None,
        "frame_diag_available": None,
        "effective_pairing_window_ps": None,
        "pairing_window_source_tag": None,
        "a_len": None,
        "b_len": None,
        "a_sequence_sha256": None,
        "a_sequence_equal_ref": None,
        "b_sequence_sha256": None,
        "b_sequence_equal_ref": None,
        "n_pairs_total": None,
        "n_pairs_actual": None,
        "raw_ser": None,
        "map_ser": None,
        "n_pairs_in_clean_frames": None,
        "n_pairs_in_ambiguous_frames": None,
        "clean_pair_fraction": None,
        "both_multi_frame_fraction": None,
        "_meta_fail_reason": None,
        "_meta_exception": None,
        "_materialize_ok": None,
        "_materialize_error": None,
        "_map_verdict": None,
        "_a_exists": False,
        "_b_exists": False,
    }
    meta_path = sidecar_root / "sidecar_meta.json"
    if not meta_path.exists():
        return out
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    used = (((meta.get("materialize_params") or {}).get("used_params")) or {})
    diag = meta.get("diagnostics") or {}
    occ_path = diag.get("occupancy_filter_summary_path")
    occ_csv = Path(occ_path) if occ_path else (sidecar_root / "occupancy_filter_summary.csv")

    out["_meta_fail_reason"] = meta.get("fail_reason")
    out["_meta_exception"] = meta.get("exception")
    out["_materialize_ok"] = meta.get("materialize_ok")
    out["_materialize_error"] = meta.get("materialize_error")
    out["_map_verdict"] = ((meta.get("map_sanity") or {}).get("verdict"))
    out["processing_rule_version"] = used.get("processing_rule_version")
    out["pairing_path_tag"] = used.get("pairing_path_tag")
    out["effective_pairing_window_ps"] = used.get("effective_pairing_window_ps")
    out["pairing_window_source_tag"] = used.get("pairing_window_source_tag")
    out["n_pairs_total"] = used.get("n_pairs_total_available")
    out["map_ser"] = ((meta.get("map_sanity") or {}).get("map_ser"))
    out["n_pairs_actual"] = diag.get("n_pairs_actual")
    out["raw_ser"] = diag.get("raw_ser")

    a_path = sidecar_root / "a_eff.npy"
    b_path = sidecar_root / "b_eff.npy"
    out["_a_exists"] = bool(a_path.exists())
    out["_b_exists"] = bool(b_path.exists())
    a_arr = _load_array(a_path)
    b_arr = _load_array(b_path)
    if a_arr is not None:
        out["a_len"] = int(a_arr.size)
        out["a_sequence_sha256"] = _sha256_array(a_path)
    if b_arr is not None:
        out["b_len"] = int(b_arr.size)
        out["b_sequence_sha256"] = _sha256_array(b_path)

    if occ_csv.exists():
        row = next(csv.DictReader(occ_csv.open("r", encoding="utf-8", newline="")), None)
        if row is not None:
            out["frame_diag_available"] = _safe_int(row.get("frame_diag_available"))
            out["n_pairs_in_clean_frames"] = _safe_int(row.get("n_pairs_in_clean_frames"))
            out["n_pairs_in_ambiguous_frames"] = _safe_int(row.get("n_pairs_in_ambiguous_frames"))
            n_frames_total = _safe_int(row.get("n_frames_total"))
            n_frames_both_multi = _safe_int(row.get("n_frames_both_multi"))
            if n_frames_total and n_frames_total > 0 and n_frames_both_multi is not None:
                out["both_multi_frame_fraction"] = float(n_frames_both_multi) / float(n_frames_total)
            n_clean = out["n_pairs_in_clean_frames"]
            n_amb = out["n_pairs_in_ambiguous_frames"]
            if n_clean is not None and n_amb is not None and (n_clean + n_amb) > 0:
                out["clean_pair_fraction"] = float(n_clean) / float(n_clean + n_amb)
    return out


def _detect_sidecar_materialization_failure(fields: dict[str, Any]) -> tuple[bool, str]:
    fail_reason = str(fields.get("_meta_fail_reason") or "").strip()
    exception = str(fields.get("_meta_exception") or "").strip()
    materialize_error = str(fields.get("_materialize_error") or "").strip()
    materialize_ok = fields.get("_materialize_ok")
    a_exists = bool(fields.get("_a_exists"))
    b_exists = bool(fields.get("_b_exists"))
    map_verdict = str(fields.get("_map_verdict") or "").strip().upper()

    reasons: list[str] = []
    if fail_reason == "export_exception":
        reasons.append(f"fail_reason={fail_reason}")
    if exception:
        reasons.append(f"exception={exception}")
    if (not a_exists) or (not b_exists):
        reasons.append(f"missing_arrays=a_eff:{a_exists},b_eff:{b_exists}")
    if materialize_ok in {0, "0"}:
        reasons.append("materialize_ok=0")
    if materialize_error:
        reasons.append(f"materialize_error={materialize_error}")
    if map_verdict in {"ERROR"}:
        reasons.append(f"map_verdict={map_verdict}")

    if reasons:
        return True, "sidecar_internal_failure(" + "; ".join(reasons) + ")"
    return False, ""


def _infer_side_health_status(fields: dict[str, Any]) -> tuple[str, str]:
    # status_v1/status_v2 represent only side health for comparison readiness.
    # They intentionally ignore result-quality verdicts such as map_ser>=0.1.
    # A side is OK if its sidecar/materialization completed and the sequences
    # needed for comparison are readable; otherwise it is ERROR.
    existing_error = str(fields.get("error_message") or "").strip()
    if existing_error:
        return "ERROR", existing_error
    side_failed, side_failure_msg = _detect_sidecar_materialization_failure(fields)
    if side_failed:
        return "ERROR", side_failure_msg
    return "OK", ""


def _run_one(point: str, out_root: Path, factor: int, block_index: int, processing_rule_version: str) -> dict[str, Any]:
    d, bw = _parse_point(point)
    case_root = out_root / f"d{d}_bw{bw}" / processing_rule_version
    error_message = ""
    try:
        res = export_sidecar_for_point(
            point=point,
            factor=int(factor),
            block_index=int(block_index),
            out_root=str(case_root),
            sequence_source_mode="strict",
            materialize_missing_real_seq=1,
            joint_source_mode="from_ttbin",
            materialize_diagnostics=1,
            materialize_occupancy_filter=0,
            materialize_pairing_mode="nearest",
            materialize_processing_rule_version=str(processing_rule_version),
        )
        sidecar_root = Path(str(res.get("sidecar_root") or case_root))
        fields = _read_sidecar_fields(sidecar_root)
        fields.update(
            {
                "status": "",
                "error_message": "",
                "sidecar_root": str(sidecar_root),
                "raw_ser": res.get("diagnostics", {}).get("raw_ser", fields.get("raw_ser")) if isinstance(res.get("diagnostics"), dict) else fields.get("raw_ser"),
                "n_pairs_actual": res.get("diagnostics", {}).get("n_pairs_actual", fields.get("n_pairs_actual")) if isinstance(res.get("diagnostics"), dict) else fields.get("n_pairs_actual"),
                "map_ser": res.get("map_ser", fields.get("map_ser")),
            }
        )
        fields["status"], fields["error_message"] = _infer_side_health_status(fields)
        return fields
    except Exception as e:
        error_message = f"{type(e).__name__}: {e}"
        return {
            "status": "ERROR",
            "error_message": f"outer_exception({error_message})",
            "sidecar_root": str(case_root),
            "processing_rule_version": processing_rule_version,
            "pairing_path_tag": None,
            "frame_diag_available": None,
            "effective_pairing_window_ps": None,
            "pairing_window_source_tag": None,
            "a_len": None,
            "b_len": None,
            "a_sequence_sha256": None,
            "b_sequence_sha256": None,
            "n_pairs_total": None,
            "n_pairs_actual": None,
            "raw_ser": None,
            "map_ser": None,
            "n_pairs_in_clean_frames": None,
            "n_pairs_in_ambiguous_frames": None,
            "clean_pair_fraction": None,
            "both_multi_frame_fraction": None,
        }


def main() -> int:
    ap = argparse.ArgumentParser(description="Compare legacy_v1 vs pairing_v2 sidecar outputs on representative points.")
    ap.add_argument("--point", action="append", default=[], help='repeatable, format "d,bw"')
    ap.add_argument("--points-csv", default="", help="CSV with columns dimension, bin_width_ps and optional point_label")
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--block-index", type=int, default=0)
    ap.add_argument("--factor", type=int, default=1)
    args = ap.parse_args()

    if args.points_csv and args.point:
        print("[COMPARE] --points-csv provided; ignoring --point values")
    point_specs = _load_point_specs(str(args.points_csv or "").strip() or None, list(args.point))
    out_root = Path(args.out_root)
    out_root.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []

    for spec in point_specs:
        point = str(spec.get("point") or "")
        point_label = str(spec.get("point_label") or "")
        parse_error = str(spec.get("parse_error") or "")
        d = spec.get("dimension")
        bw = spec.get("bin_width_ps")
        if parse_error:
            rows.append(
                {
                    "point_label": point_label,
                    "dimension": d,
                    "bin_width_ps": bw,
                    "processing_rule_version_v1": "legacy_v1",
                    "pairing_path_tag_v1": None,
                    "frame_diag_available_v1": None,
                    "effective_pairing_window_ps_v1": None,
                    "pairing_window_source_tag_v1": None,
                    "processing_rule_version_v2": "pairing_v2",
                    "pairing_path_tag_v2": None,
                    "frame_diag_available_v2": None,
                    "effective_pairing_window_ps_v2": None,
                    "pairing_window_source_tag_v2": None,
                    "a_len_v1": None,
                    "b_len_v1": None,
                    "a_len_v2": None,
                    "b_len_v2": None,
                    "a_len_same": None,
                    "b_len_same": None,
                    "a_sequence_equal": None,
                    "b_sequence_equal": None,
                    "a_sequence_sha256_v1": None,
                    "a_sequence_sha256_v2": None,
                    "b_sequence_sha256_v1": None,
                    "b_sequence_sha256_v2": None,
                    "n_pairs_total_v1": None,
                    "n_pairs_total_v2": None,
                    "n_pairs_actual_v1": None,
                    "n_pairs_actual_v2": None,
                    "raw_ser_v1": None,
                    "raw_ser_v2": None,
                    "map_ser_v1": None,
                    "map_ser_v2": None,
                    "n_pairs_in_clean_frames_v1": None,
                    "n_pairs_in_clean_frames_v2": None,
                    "n_pairs_in_ambiguous_frames_v1": None,
                    "n_pairs_in_ambiguous_frames_v2": None,
                    "clean_pair_fraction_v1": None,
                    "clean_pair_fraction_v2": None,
                    "both_multi_frame_fraction_v1": None,
                    "both_multi_frame_fraction_v2": None,
                    "status_v1": "ERROR",
                    "status_v2": "ERROR",
                    "comparison_status": "failed_compare",
                    "error_message_v1": parse_error,
                    "error_message_v2": parse_error,
                    "sidecar_root_v1": "",
                    "sidecar_root_v2": "",
                }
            )
            continue

        v1 = _run_one(point, out_root, int(args.factor), int(args.block_index), "legacy_v1")
        v2 = _run_one(point, out_root, int(args.factor), int(args.block_index), "pairing_v2")

        a_len_same = (v1.get("a_len") == v2.get("a_len")) if (v1.get("a_len") is not None and v2.get("a_len") is not None) else None
        b_len_same = (v1.get("b_len") == v2.get("b_len")) if (v1.get("b_len") is not None and v2.get("b_len") is not None) else None
        a_sequence_equal = (v1.get("a_sequence_sha256") == v2.get("a_sequence_sha256")) if (v1.get("a_sequence_sha256") and v2.get("a_sequence_sha256")) else None
        b_sequence_equal = (v1.get("b_sequence_sha256") == v2.get("b_sequence_sha256")) if (v1.get("b_sequence_sha256") and v2.get("b_sequence_sha256")) else None

        v1_failed = str(v1.get("status") or "").upper() == "ERROR"
        v2_failed = str(v2.get("status") or "").upper() == "ERROR"

        if v1_failed and v2_failed:
            comparison_status = "both_failed"
        elif v1_failed:
            comparison_status = "v1_failed"
        elif v2_failed:
            comparison_status = "v2_failed"
        else:
            comparison_status = "ok"

        row = {
            "point_label": point_label,
            "dimension": d,
            "bin_width_ps": bw,
            "processing_rule_version_v1": v1.get("processing_rule_version"),
            "pairing_path_tag_v1": v1.get("pairing_path_tag"),
            "frame_diag_available_v1": v1.get("frame_diag_available"),
            "effective_pairing_window_ps_v1": v1.get("effective_pairing_window_ps"),
            "pairing_window_source_tag_v1": v1.get("pairing_window_source_tag"),
            "processing_rule_version_v2": v2.get("processing_rule_version"),
            "pairing_path_tag_v2": v2.get("pairing_path_tag"),
            "frame_diag_available_v2": v2.get("frame_diag_available"),
            "effective_pairing_window_ps_v2": v2.get("effective_pairing_window_ps"),
            "pairing_window_source_tag_v2": v2.get("pairing_window_source_tag"),
            "a_len_v1": v1.get("a_len"),
            "b_len_v1": v1.get("b_len"),
            "a_len_v2": v2.get("a_len"),
            "b_len_v2": v2.get("b_len"),
            "a_len_same": a_len_same,
            "b_len_same": b_len_same,
            "a_sequence_equal": a_sequence_equal,
            "b_sequence_equal": b_sequence_equal,
            "a_sequence_sha256_v1": v1.get("a_sequence_sha256"),
            "a_sequence_sha256_v2": v2.get("a_sequence_sha256"),
            "b_sequence_sha256_v1": v1.get("b_sequence_sha256"),
            "b_sequence_sha256_v2": v2.get("b_sequence_sha256"),
            "n_pairs_total_v1": v1.get("n_pairs_total"),
            "n_pairs_total_v2": v2.get("n_pairs_total"),
            "n_pairs_actual_v1": v1.get("n_pairs_actual"),
            "n_pairs_actual_v2": v2.get("n_pairs_actual"),
            "raw_ser_v1": v1.get("raw_ser"),
            "raw_ser_v2": v2.get("raw_ser"),
            "map_ser_v1": v1.get("map_ser"),
            "map_ser_v2": v2.get("map_ser"),
            "n_pairs_in_clean_frames_v1": v1.get("n_pairs_in_clean_frames"),
            "n_pairs_in_clean_frames_v2": v2.get("n_pairs_in_clean_frames"),
            "n_pairs_in_ambiguous_frames_v1": v1.get("n_pairs_in_ambiguous_frames"),
            "n_pairs_in_ambiguous_frames_v2": v2.get("n_pairs_in_ambiguous_frames"),
            "clean_pair_fraction_v1": v1.get("clean_pair_fraction"),
            "clean_pair_fraction_v2": v2.get("clean_pair_fraction"),
            "both_multi_frame_fraction_v1": v1.get("both_multi_frame_fraction"),
            "both_multi_frame_fraction_v2": v2.get("both_multi_frame_fraction"),
            "status_v1": v1.get("status"),
            "status_v2": v2.get("status"),
            "comparison_status": comparison_status,
            "error_message_v1": v1.get("error_message"),
            "error_message_v2": v2.get("error_message"),
            "sidecar_root_v1": v1.get("sidecar_root"),
            "sidecar_root_v2": v2.get("sidecar_root"),
        }
        rows.append(row)

    out_csv = out_root / "processing_rule_version_comparison.csv"
    cols = list(rows[0].keys()) if rows else ["dimension", "bin_width_ps"]
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    print(f"[COMPARE] wrote {out_csv}")
    print(f"[COMPARE] rows={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

