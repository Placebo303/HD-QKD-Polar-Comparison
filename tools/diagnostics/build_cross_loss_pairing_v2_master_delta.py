#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SECURITY_REPORTS = REPO_ROOT / "tools" / "security_reports"
for _p in (REPO_ROOT, SECURITY_REPORTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import csv
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


LOSS_CONFIGS = [
    {
        "loss_db": 6,
        "legacy_main": r"D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s\Type2_5s_6dB_2026-01-30_224719\e2e_pipeline_20260303_105145\polar_e2e_results_refresh.csv",
        "legacy_diag": r"D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s\Type2_5s_6dB_2026-01-30_224719\e2e_pipeline_20260303_105145\polar_diag_summary.csv",
        "v2_main": r"D:\Code\HD-QKD_Polar_Release\results\e2e_6dB_fullgrid_pairing_v2_candidate\polar_e2e_results.csv",
        "v2_diag": r"D:\Code\HD-QKD_Polar_Release\results\e2e_6dB_fullgrid_pairing_v2_candidate\polar_diag_summary.csv",
    },
    {
        "loss_db": 10,
        "legacy_main": r"D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s\Type2_5s_10dB_2026-01-30_224808\e2e_new_ttbin_fullgrid\polar_e2e_results_refresh.csv",
        "legacy_diag": r"D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s\Type2_5s_10dB_2026-01-30_224808\e2e_new_ttbin_fullgrid\polar_diag_summary.csv",
        "v2_main": r"D:\Code\HD-QKD_Polar_Release\results\e2e_10dB_fullgrid_pairing_v2_candidate\polar_e2e_results.csv",
        "v2_diag": r"D:\Code\HD-QKD_Polar_Release\results\e2e_10dB_fullgrid_pairing_v2_candidate\polar_diag_summary.csv",
    },
    {
        "loss_db": 16,
        "legacy_main": r"D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s\Type2_5s_16dB_2026-01-30_224900\e2e_new_ttbin_fullgrid\polar_e2e_results_refresh.csv",
        "legacy_diag": r"D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s\Type2_5s_16dB_2026-01-30_224900\e2e_new_ttbin_fullgrid\polar_diag_summary.csv",
        "v2_main": r"D:\Code\HD-QKD_Polar_Release\results\e2e_16dB_fullgrid_pairing_v2_candidate\polar_e2e_results.csv",
        "v2_diag": r"D:\Code\HD-QKD_Polar_Release\results\e2e_16dB_fullgrid_pairing_v2_candidate\polar_diag_summary.csv",
    },
    {
        "loss_db": 20,
        "legacy_main": r"D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s\Type2_5s_20dB_2026-01-30_224943\e2e_new_ttbin_fullgrid\polar_e2e_results_refresh.csv",
        "legacy_diag": r"D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s\Type2_5s_20dB_2026-01-30_224943\e2e_new_ttbin_fullgrid\polar_diag_summary.csv",
        "v2_main": r"D:\Code\HD-QKD_Polar_Release\results\e2e_20dB_fullgrid_pairing_v2_candidate_t15\polar_e2e_results.csv",
        "v2_diag": r"D:\Code\HD-QKD_Polar_Release\results\e2e_20dB_fullgrid_pairing_v2_candidate_t15\polar_diag_summary.csv",
    },
]

OUT_ROOT = Path(r"D:\Code\HD-QKD_Polar_Release\results\_tmp_cross_loss_legacy_vs_pairing_v2_master")


def _to_int(v: Any) -> int | None:
    try:
        s = str(v).strip()
        if s == "":
            return None
        return int(float(s))
    except Exception:
        return None


def _to_float(v: Any) -> float | None:
    try:
        s = str(v).strip()
        if s == "":
            return None
        x = float(s)
        if x != x:
            return None
        return x
    except Exception:
        return None


def _fmt(v: Any) -> str:
    return "" if v is None else str(v)


def _key(row: dict[str, Any]) -> tuple[int, int] | None:
    d = _to_int(row.get("dimension"))
    bw = _to_int(row.get("bin_width_ps"))
    if d is None or bw is None:
        return None
    return (d, bw)


def _read_keyed_csv(path: Path) -> dict[tuple[int, int], dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    out: dict[tuple[int, int], dict[str, Any]] = {}
    for row in rows:
        k = _key(row)
        if k is not None:
            out[k] = row
    return out


def _pick_pie(row: dict[str, Any] | None) -> float | None:
    if not row:
        return None
    for col in ("PIE_practical", "best_hard_PIE", "pie_best"):
        val = _to_float(row.get(col))
        if val is not None:
            return val
    return None


def _pick_skr(row: dict[str, Any] | None) -> float | None:
    if not row:
        return None
    for col in ("SKR_measured_bps", "skr_best_bps"):
        val = _to_float(row.get(col))
        if val is not None:
            return val
    return None


def _bw_bucket(bw: int | None) -> str:
    if bw in {20, 30, 40, 50}:
        return "bw_small"
    if bw in {60, 80, 100}:
        return "bw_mid"
    if bw in {120, 150, 180, 200}:
        return "bw_large"
    return "unknown"


def _delta(v2: float | int | None, legacy: float | int | None) -> float | int | None:
    if v2 is None or legacy is None:
        return None
    return v2 - legacy


def _change_class(delta_layers: int | None, abs_delta_map: float | None, abs_delta_pie: float | None, abs_delta_skr: float | None, missing: bool) -> str:
    if missing:
        return "missing_side"
    if delta_layers is not None and delta_layers != 0:
        return "layer_change"
    if any(v is not None and v > 1e-9 for v in (abs_delta_skr, abs_delta_pie, abs_delta_map)):
        return "metric_change_only"
    return "exact_match"


def _mean_or_none(values: list[float]) -> float | None:
    return mean(values) if values else None


def _max_or_none(values: list[float]) -> float | None:
    return max(values) if values else None


def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)

    master_rows: list[dict[str, Any]] = []
    per_loss_stats: dict[int, dict[str, Any]] = {}

    for cfg in LOSS_CONFIGS:
        loss_db = int(cfg["loss_db"])
        legacy_main = _read_keyed_csv(Path(cfg["legacy_main"]))
        legacy_diag = _read_keyed_csv(Path(cfg["legacy_diag"]))
        v2_main = _read_keyed_csv(Path(cfg["v2_main"]))
        v2_diag = _read_keyed_csv(Path(cfg["v2_diag"]))

        keys = sorted(set(legacy_main) | set(v2_main))
        counts = Counter()
        top_abs_skr: list[tuple[float, int, int]] = []
        layer_change_count = 0
        status_flip_count = 0

        for dim, bw in keys:
            l_main = legacy_main.get((dim, bw))
            l_diag = legacy_diag.get((dim, bw))
            v_main = v2_main.get((dim, bw))
            v_diag = v2_diag.get((dim, bw))

            raw_ser_legacy = _to_float((l_diag or {}).get("raw_ser"))
            raw_ser_v2 = _to_float((v_diag or {}).get("raw_ser"))
            map_ser_legacy = _to_float((l_main or {}).get("map_ser"))
            map_ser_v2 = _to_float((v_main or {}).get("map_ser"))
            layers_legacy = _to_int((l_main or {}).get("layers_success_best"))
            layers_v2 = _to_int((v_main or {}).get("layers_success_best"))
            pie_legacy = _pick_pie(l_main)
            pie_v2 = _pick_pie(v_main)
            skr_legacy = _pick_skr(l_main)
            skr_v2 = _pick_skr(v_main)
            status_legacy = str((l_main or {}).get("status") or "")
            status_v2 = str((v_main or {}).get("status") or "")

            delta_raw = _delta(raw_ser_v2, raw_ser_legacy)
            delta_map = _delta(map_ser_v2, map_ser_legacy)
            delta_layers = _delta(layers_v2, layers_legacy)
            delta_pie = _delta(pie_v2, pie_legacy)
            delta_skr = _delta(skr_v2, skr_legacy)

            abs_delta_raw = abs(delta_raw) if delta_raw is not None else None
            abs_delta_map = abs(delta_map) if delta_map is not None else None
            abs_delta_pie = abs(delta_pie) if delta_pie is not None else None
            abs_delta_skr = abs(delta_skr) if delta_skr is not None else None

            missing = l_main is None or v_main is None
            change_class = _change_class(delta_layers, abs_delta_map, abs_delta_pie, abs_delta_skr, missing)
            status_flip_tag = "flip" if (not missing and status_legacy != status_v2) else "same"

            row = {
                "loss_db": loss_db,
                "dimension": dim,
                "bin_width_ps": bw,
                "processing_rule_version_legacy": (l_main or {}).get("processing_rule_version", ""),
                "processing_rule_version_v2": (v_main or {}).get("processing_rule_version", ""),
                "pairing_path_tag_legacy": (l_main or {}).get("pairing_path_tag", ""),
                "pairing_path_tag_v2": (v_main or {}).get("pairing_path_tag", ""),
                "pairing_window_source_tag_v2": (v_main or {}).get("pairing_window_source_tag", ""),
                "raw_ser_legacy": raw_ser_legacy,
                "map_ser_legacy": map_ser_legacy,
                "layers_success_best_legacy": layers_legacy,
                "PIE_legacy": pie_legacy,
                "SKR_legacy": skr_legacy,
                "status_legacy": status_legacy,
                "raw_ser_v2": raw_ser_v2,
                "map_ser_v2": map_ser_v2,
                "layers_success_best_v2": layers_v2,
                "PIE_v2": pie_v2,
                "SKR_v2": skr_v2,
                "status_v2": status_v2,
                "delta_raw_ser": delta_raw,
                "delta_map_ser": delta_map,
                "delta_layers_success_best": delta_layers,
                "delta_PIE": delta_pie,
                "delta_SKR": delta_skr,
                "abs_delta_raw_ser": abs_delta_raw,
                "abs_delta_map_ser": abs_delta_map,
                "abs_delta_PIE": abs_delta_pie,
                "abs_delta_SKR": abs_delta_skr,
                "bw_bucket": _bw_bucket(bw),
                "change_class_tag": change_class,
                "status_flip_tag": status_flip_tag,
            }
            master_rows.append(row)

            counts[change_class] += 1
            if not missing:
                counts["join_success"] += 1
                if status_flip_tag == "flip":
                    status_flip_count += 1
            if delta_layers is not None and delta_layers != 0:
                layer_change_count += 1
            if abs_delta_skr is not None:
                top_abs_skr.append((abs_delta_skr, dim, bw))

        top_abs_skr.sort(reverse=True)
        per_loss_stats[loss_db] = {
            "total_points": len(keys),
            "counts": counts,
            "top_abs_skr": top_abs_skr[:5],
            "layer_change_count": layer_change_count,
            "status_flip_count": status_flip_count,
        }

    master_fields = [
        "loss_db",
        "dimension",
        "bin_width_ps",
        "processing_rule_version_legacy",
        "processing_rule_version_v2",
        "pairing_path_tag_legacy",
        "pairing_path_tag_v2",
        "pairing_window_source_tag_v2",
        "raw_ser_legacy",
        "map_ser_legacy",
        "layers_success_best_legacy",
        "PIE_legacy",
        "SKR_legacy",
        "status_legacy",
        "raw_ser_v2",
        "map_ser_v2",
        "layers_success_best_v2",
        "PIE_v2",
        "SKR_v2",
        "status_v2",
        "delta_raw_ser",
        "delta_map_ser",
        "delta_layers_success_best",
        "delta_PIE",
        "delta_SKR",
        "abs_delta_raw_ser",
        "abs_delta_map_ser",
        "abs_delta_PIE",
        "abs_delta_SKR",
        "bw_bucket",
        "change_class_tag",
        "status_flip_tag",
    ]
    with (OUT_ROOT / "cross_loss_legacy_vs_pairing_v2_master_delta.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=master_fields)
        w.writeheader()
        for row in sorted(master_rows, key=lambda r: (int(r["loss_db"]), int(r["dimension"]), int(r["bin_width_ps"]))):
            w.writerow({k: _fmt(row.get(k)) for k in master_fields})

    by_loss_dim_rows: list[dict[str, Any]] = []
    dim_groups: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for row in master_rows:
        dim_groups[(int(row["loss_db"]), int(row["dimension"]))].append(row)
    for (loss_db, dim), rows in sorted(dim_groups.items()):
        by_loss_dim_rows.append({
            "loss_db": loss_db,
            "dimension": dim,
            "n_points": len(rows),
            "n_layer_change": sum(1 for r in rows if r["change_class_tag"] == "layer_change"),
            "n_metric_change_only": sum(1 for r in rows if r["change_class_tag"] == "metric_change_only"),
            "n_status_flip": sum(1 for r in rows if r["status_flip_tag"] == "flip"),
            "mean_abs_delta_map_ser": _mean_or_none([r["abs_delta_map_ser"] for r in rows if r["abs_delta_map_ser"] is not None]),
            "max_abs_delta_map_ser": _max_or_none([r["abs_delta_map_ser"] for r in rows if r["abs_delta_map_ser"] is not None]),
            "mean_abs_delta_PIE": _mean_or_none([r["abs_delta_PIE"] for r in rows if r["abs_delta_PIE"] is not None]),
            "max_abs_delta_PIE": _max_or_none([r["abs_delta_PIE"] for r in rows if r["abs_delta_PIE"] is not None]),
            "mean_abs_delta_SKR": _mean_or_none([r["abs_delta_SKR"] for r in rows if r["abs_delta_SKR"] is not None]),
            "max_abs_delta_SKR": _max_or_none([r["abs_delta_SKR"] for r in rows if r["abs_delta_SKR"] is not None]),
        })
    with (OUT_ROOT / "cross_loss_legacy_vs_pairing_v2_by_loss_dimension.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(by_loss_dim_rows[0].keys()) if by_loss_dim_rows else [])
        if by_loss_dim_rows:
            w.writeheader()
            for row in by_loss_dim_rows:
                w.writerow({k: _fmt(v) for k, v in row.items()})

    by_loss_bw_rows: list[dict[str, Any]] = []
    bw_groups: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in master_rows:
        bw_groups[(int(row["loss_db"]), str(row["bw_bucket"]))].append(row)
    bucket_order = {"bw_small": 0, "bw_mid": 1, "bw_large": 2, "unknown": 3}
    for (loss_db, bucket), rows in sorted(bw_groups.items(), key=lambda kv: (kv[0][0], bucket_order.get(kv[0][1], 99))):
        by_loss_bw_rows.append({
            "loss_db": loss_db,
            "bw_bucket": bucket,
            "n_points": len(rows),
            "n_layer_change": sum(1 for r in rows if r["change_class_tag"] == "layer_change"),
            "n_metric_change_only": sum(1 for r in rows if r["change_class_tag"] == "metric_change_only"),
            "n_status_flip": sum(1 for r in rows if r["status_flip_tag"] == "flip"),
            "mean_abs_delta_map_ser": _mean_or_none([r["abs_delta_map_ser"] for r in rows if r["abs_delta_map_ser"] is not None]),
            "max_abs_delta_map_ser": _max_or_none([r["abs_delta_map_ser"] for r in rows if r["abs_delta_map_ser"] is not None]),
            "mean_abs_delta_PIE": _mean_or_none([r["abs_delta_PIE"] for r in rows if r["abs_delta_PIE"] is not None]),
            "max_abs_delta_PIE": _max_or_none([r["abs_delta_PIE"] for r in rows if r["abs_delta_PIE"] is not None]),
            "mean_abs_delta_SKR": _mean_or_none([r["abs_delta_SKR"] for r in rows if r["abs_delta_SKR"] is not None]),
            "max_abs_delta_SKR": _max_or_none([r["abs_delta_SKR"] for r in rows if r["abs_delta_SKR"] is not None]),
        })
    with (OUT_ROOT / "cross_loss_legacy_vs_pairing_v2_by_loss_bw_bucket.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(by_loss_bw_rows[0].keys()) if by_loss_bw_rows else [])
        if by_loss_bw_rows:
            w.writeheader()
            for row in by_loss_bw_rows:
                w.writerow({k: _fmt(v) for k, v in row.items()})

    top_dim_counter: Counter[int] = Counter()
    for loss_db, stats in per_loss_stats.items():
        for _, dim, _ in stats["top_abs_skr"]:
            top_dim_counter[dim] += 1
    layer_bucket_counter: Counter[str] = Counter(row["bw_bucket"] for row in master_rows if row["change_class_tag"] == "layer_change")

    loss_mean_abs_skr: dict[int, float] = {}
    for loss_db in per_loss_stats:
        vals = [r["abs_delta_SKR"] for r in master_rows if int(r["loss_db"]) == loss_db and r["abs_delta_SKR"] is not None]
        loss_mean_abs_skr[loss_db] = mean(vals) if vals else 0.0
    loss_n_layer_change: dict[int, int] = {loss_db: int(stats["layer_change_count"]) for loss_db, stats in per_loss_stats.items()}

    layer_bucket_by_loss = defaultdict(dict)
    skr_bucket_by_loss = defaultdict(dict)
    for row in by_loss_bw_rows:
        loss_db = int(row["loss_db"])
        bucket = str(row["bw_bucket"])
        layer_bucket_by_loss[loss_db][bucket] = _to_int(row["n_layer_change"]) or 0
        skr_bucket_by_loss[loss_db][bucket] = _to_float(row["mean_abs_delta_SKR"]) or 0.0
    pattern_stable = all(
        max(layer_bucket_by_loss[loss_db].items(), key=lambda kv: kv[1])[0] == "bw_small"
        and max(skr_bucket_by_loss[loss_db].items(), key=lambda kv: kv[1])[0] == "bw_large"
        for loss_db in sorted(per_loss_stats.keys())
    )

    summary_lines: list[str] = []
    for loss_db in sorted(per_loss_stats.keys()):
        stats = per_loss_stats[loss_db]
        counts = stats["counts"]
        summary_lines.append(f"loss {loss_db} dB")
        summary_lines.append(f"  total_points: {stats['total_points']}")
        summary_lines.append(f"  join_success: {counts.get('join_success', 0)}")
        summary_lines.append(f"  exact_match: {counts.get('exact_match', 0)}")
        summary_lines.append(f"  layer_change: {counts.get('layer_change', 0)}")
        summary_lines.append(f"  metric_change_only: {counts.get('metric_change_only', 0)}")
        summary_lines.append(f"  missing_side: {counts.get('missing_side', 0)}")
        summary_lines.append(f"  status_flip: {stats['status_flip_count']}")
        summary_lines.append(f"  delta_layers_success_best_nonzero: {stats['layer_change_count']}")
        summary_lines.append("  top_abs_delta_SKR:")
        for abs_skr, dim, bw in stats["top_abs_skr"]:
            summary_lines.append(f"    d={dim}, bw={bw}, abs_delta_SKR={abs_skr}")
        summary_lines.append("")

    top_dim = top_dim_counter.most_common(1)[0][0] if top_dim_counter else None
    top_layer_bucket = layer_bucket_counter.most_common(1)[0][0] if layer_bucket_counter else None
    max_mean_abs_skr_loss = max(loss_mean_abs_skr.items(), key=lambda kv: kv[1])[0] if loss_mean_abs_skr else None
    max_layer_change_loss = max(loss_n_layer_change.items(), key=lambda kv: kv[1])[0] if loss_n_layer_change else None
    summary_lines.append("cross_loss")
    summary_lines.append(f"  top_abs_delta_SKR_hot_dimension: {top_dim}")
    summary_lines.append(f"  most_common_layer_change_bw_bucket: {top_layer_bucket}")
    summary_lines.append(f"  max_mean_abs_delta_SKR_loss: {max_mean_abs_skr_loss}")
    summary_lines.append(f"  max_n_layer_change_loss: {max_layer_change_loss}")
    if pattern_stable:
        summary_lines.append("  conclusion: across 6/10/16/20 dB, pairing_v2 vs legacy consistently shows bw_small-driven layer transition and bw_large-driven metric amplification.")
    else:
        summary_lines.append("  conclusion: the bw_small-driven layer transition / bw_large-driven metric amplification split is only partially stable across losses.")

    (OUT_ROOT / "cross_loss_legacy_vs_pairing_v2_summary.txt").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

