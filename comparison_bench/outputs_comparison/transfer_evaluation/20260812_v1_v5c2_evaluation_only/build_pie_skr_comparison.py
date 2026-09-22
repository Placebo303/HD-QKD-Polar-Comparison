"""Build the PIE/SKR/chiE comparison table (binary LDPC V5-C2 vs Polar),
one row per (loss, bw).

Sources:
  - v5 side: per-frame outcomes from evaluation_report.json in this directory
    (6/16 dB decoded) and from the official 20260801_v2_binary_ldpc_v5_real
    real_frame_outcomes.csv (10 dB, referenced, never re-decoded).
    20 dB uses the pairing_v2 re-evaluation report
    (evaluation_report_20db_pairing_v2.json, frozen V5-C2, evaluation-only;
    sidecars from e2e_20dB_fullgrid_pairing_v2_candidate).  If that report is
    absent, loss 20 falls back to evaluation_report.json (e2e_new_ttbin_fullgrid
    pairing) so the script still runs on a pre-v2 directory.
      best_hard_PIE_v5  = mean over frames of (2560 - key_dependent_disclosure_bits_total) / 256
      PIE_practical_v5  = best_hard_PIE_v5 - chiE
      SKR_v5            = PIE_practical_v5 * (n_symbols / 3.0)   # rate per layer
    n_symbols for 20 dB comes from the pairing_v2 sidecar_meta.json
    (30056/30149/30168), not the e2e_new_ttbin_fullgrid one (30044/30145/30176).
  - Polar side: official cross_loss_security_master_table.csv, dimension=1024,
    bin_width_ps in {120,180,200} (same config points, not best points).
    Exception: loss 16 uses the real pairing_v2 rematerialize Polar run
    (polar_e2e_results.csv, bw150/180/200) instead of the frozen master-table
    rows, because the frozen loss16 rows for bw180/bw200 were exact duplicates
    of the loss6 rows (see POLAR_REAL16_CSV).
  - chiE = 0.4186 bits/symbol: h2(e_p) + e_p*log2(d-1) with e_p=(1-visibility)/2=0.025,
    visibility=0.95, d=1024; IR-independent, identical for every loss.
  - v5_pairing column: which sidecar pairing the v5 numbers come from.
    pairing_v2 = 20 dB (e2e_20dB_fullgrid_pairing_v2_candidate);
    e2e_new_ttbin_fullgrid = 10/16 dB; 6 dB = e2e_pipeline_20260303_105145
    (documented per-loss sidecar special case).

Output: pie_skr_comparison.csv in this directory (regenerated).
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

_HERE = Path(__file__).resolve().parent
_REPORT = _HERE / "evaluation_report.json"
# 20 dB re-evaluation on the pairing_v2 sidecars (frozen V5-C2, evaluation-only).
# Auto-detected: used for loss 20 when present, otherwise falls back to _REPORT.
PAIRING_V2_REPORT = _HERE / "evaluation_report_20db_pairing_v2.json"
PAIRING_V2_ROOT = Path(
    r"D:\Code\HD-QKD_Polar_Release\results\authoritative"
    r"\e2e_20dB_fullgrid_pairing_v2_candidate\sidecars")
REAL10_CSV = (_HERE.parents[1] / "formal_ir_methods"
              / "20260801_v2_binary_ldpc_v5_real" / "real_frame_outcomes.csv")
POLAR_BASE = (Path(r"D:\Code\HD-QKD_Polar_Release\results\paper_grade_v2")
              / "four_loss_parts_tag64")
# Real 16 dB Polar results from the pairing_v2 rematerialize run on the actual
# 16 dB sidecars (bw150/180/200). Replaces the frozen loss16 master-table rows
# for bw180/bw200, which were exact duplicates of the loss6 rows (see polar_row).
POLAR_REAL16_CSV = (Path(r"D:\Code\HD-QKD_Polar_Comparison\comparison_bench\outputs_comparison")
                    / "e2e_16dB_pairing_v2_rematerialize" / "polar_e2e_results.csv")

RAW_ROOT = Path(r"D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s")
ACQ = {
    "6": RAW_ROOT / "Type2_5s_6dB_2026-01-30_224719",
    "10": RAW_ROOT / "Type2_5s_10dB_2026-01-30_224808",
    "16": RAW_ROOT / "Type2_5s_16dB_2026-01-30_224900",
    "20": RAW_ROOT / "Type2_5s_20dB_2026-01-30_224943",
}
SIDECAR_SUB = {
    "6": "e2e_pipeline_20260303_105145/sidecars",
    "10": "e2e_new_ttbin_fullgrid/sidecars",
    "16": "e2e_new_ttbin_fullgrid/sidecars",
    "20": "e2e_new_ttbin_fullgrid/sidecars",
}
LOCK_TO_BW = {"d1024_bw120": "bw120", "d1024_bw180": "bw180", "d1024_bw200": "bw200"}
CHI_E = 0.4186  # bits/symbol, IR-independent (see module docstring)
N = 256
TOTAL_BITS = N * 10  # 256 symbols x 10 bits (Q=1024)
STRATA = ("bw120", "bw180", "bw200")


def _n_symbols(loss: str, bw: str) -> float:
    if loss == "20" and PAIRING_V2_REPORT.exists():
        # SKR rate basis must match the pairing the frames come from:
        # pairing_v2 n_symbols (30056/30149/30168), not the fullgrid one.
        meta = PAIRING_V2_ROOT / f"d1024_{bw}" / "blk0" / "sidecar_meta.json"
    else:
        meta = ACQ[loss] / SIDECAR_SUB[loss] / f"d1024_{bw}" / "blk0" / "sidecar_meta.json"
    return float(json.loads(meta.read_text(encoding="utf-8"))["n_symbols"])


def _report_for(loss: str) -> Path:
    if loss == "20" and PAIRING_V2_REPORT.exists():
        return PAIRING_V2_REPORT
    return _REPORT


def v5_frames(loss: str) -> list[dict]:
    if loss == "10":
        df = pd.read_csv(REAL10_CSV)
        out = []
        for _, r in df.iterrows():
            out.append({"stratum": r["stratum"], "status": str(r["status"]),
                        "raw_ser": float(r["raw_ser"]),
                        "leak": float(r["key_dependent_disclosure_bits_total"])})
        return out
    report = json.loads(_report_for(loss).read_text(encoding="utf-8"))
    return [{"stratum": f["stratum"], "status": f["status"],
             "raw_ser": f["raw_ser"], "leak": f["key_dependent_disclosure_bits_total"]}
            for f in report["per_frame_outcomes"] if str(f["loss_db"]) == loss]


PAIRING_LABEL = {
    "6": "e2e_pipeline_20260303_105145",
    "10": "e2e_new_ttbin_fullgrid",
    "16": "e2e_new_ttbin_fullgrid",
    "20": "pairing_v2" if PAIRING_V2_REPORT.exists() else "e2e_new_ttbin_fullgrid",
}


def v5_metrics(loss: str, bw: str) -> dict:
    frames = [f for f in v5_frames(loss) if f["stratum"] == bw]
    denom = len(frames)
    ok = sum(1 for f in frames if f["status"] == "verified_success")
    best_hard = sum((TOTAL_BITS - f["leak"]) / N for f in frames) / denom
    ser = [f["raw_ser"] for f in frames]
    return {
        "best_hard_pie": best_hard,
        "pie_practical": best_hard - CHI_E,
        "skr_bps": (best_hard - CHI_E) * (_n_symbols(loss, bw) / 3.0),
        "success_rate": ok / denom,
        "denominator": denom,
        "ser_mean": sum(ser) / len(ser),
    }


def polar_row(loss: str, bw: str) -> dict:
    if loss == "16" and POLAR_REAL16_CSV.exists():
        # real values from the 16 dB pairing_v2 rematerialize Polar run;
        # only bws present in that run are overridden (bw120 falls through
        # to the frozen master table, which is real for loss 16)
        df = pd.read_csv(POLAR_REAL16_CSV)
        rows = df[(df["dimension"] == 1024) & (df["bin_width_ps"] == int(bw[2:]))]
        if len(rows) > 1:
            raise ValueError(f"expected 1 real-16dB Polar row for {bw}, got {len(rows)}")
        if len(rows) == 1:
            r = rows.iloc[0]
            return {
                "best_hard_pie": float(r["best_hard_PIE"]),
                "pie_practical": float(r["PIE_practical"]),
                "skr_bps": float(r["SKR_measured_bps"]),
                "note": "ok",
            }
    df = pd.read_csv(POLAR_BASE / f"loss{loss}" / "cross_loss_security_master_table.csv")
    rows = df[(df["dimension"] == 1024) & (df["bin_width_ps"] == int(bw[2:]))]
    if len(rows) != 1:
        raise ValueError(f"expected 1 Polar row for loss{loss} {bw}, got {len(rows)}")
    r = rows.iloc[0]
    note = "ok"
    if loss != "6":
        # data-quality guard: the frozen loss16 master table duplicates the
        # loss6 rows for bw180/bw200 (identical SKR/n_eff/accepted_frame_fraction);
        # detect by exact SKR equality with the loss6 row of the same bw.
        df6 = pd.read_csv(POLAR_BASE / "loss6" / "cross_loss_security_master_table.csv")
        r6 = df6[(df6["dimension"] == 1024) & (df6["bin_width_ps"] == int(bw[2:]))]
        if len(r6) == 1 and abs(float(r6.iloc[0]["SKR_measured_bps"])
                                - float(r["SKR_measured_bps"])) < 1e-6:
            note = "MASTER_TABLE_DUPLICATE_OF_LOSS6_ROW"
    return {
        "best_hard_pie": float(r["best_hard_PIE"]),
        "pie_practical": float(r["PIE_practical"]),
        "skr_bps": float(r["SKR_measured_bps"]),
        "note": note,
    }


def main() -> None:
    losses = ("6", "10", "16", "20")
    rows = []
    for loss in losses:
        for bw in STRATA:
            v = v5_metrics(loss, bw)
            p = polar_row(loss, bw)
            delta_pie = v["pie_practical"] - p["pie_practical"]
            delta_skr_pct = (v["skr_bps"] - p["skr_bps"]) / p["skr_bps"] * 100.0
            rows.append({
                "loss": loss, "bw": bw,
                "polar_best_hard_pie": round(p["best_hard_pie"], 4),
                "polar_pie_practical": round(p["pie_practical"], 4),
                "polar_skr_bps": round(p["skr_bps"], 1),
                "v5_best_hard_pie": round(v["best_hard_pie"], 4),
                "v5_pie_practical": round(v["pie_practical"], 4),
                "v5_skr_bps": round(v["skr_bps"], 1),
                "delta_pie": round(delta_pie, 4),
                "delta_skr_pct": round(delta_skr_pct, 1),
                "chiE(0.4186)": CHI_E,
                "v5_success_rate": round(v["success_rate"], 6),
                "v5_denominator": v["denominator"],
                "v5_ser_mean": round(v["ser_mean"], 6),
                "v5_pairing": PAIRING_LABEL[loss],
                "polar_note": p["note"],
            })
        if loss == "16" and POLAR_REAL16_CSV.exists():
            # v5 evaluation report has no bw150 stratum; Polar side is real.
            p = polar_row("16", "bw150")
            rows.append({
                "loss": "16", "bw": "bw150",
                "polar_best_hard_pie": round(p["best_hard_pie"], 4),
                "polar_pie_practical": round(p["pie_practical"], 4),
                "polar_skr_bps": round(p["skr_bps"], 1),
                "v5_best_hard_pie": "N/A", "v5_pie_practical": "N/A", "v5_skr_bps": "N/A",
                "delta_pie": "N/A", "delta_skr_pct": "N/A",
                "chiE(0.4186)": CHI_E,
                "v5_success_rate": "N/A", "v5_denominator": "N/A", "v5_ser_mean": "N/A",
                "v5_pairing": "N/A (v5 未评估 bw150)",
                "polar_note": p["note"],
            })
    out_df = pd.DataFrame(rows)
    out_path = _HERE / "pie_skr_comparison.csv"
    out_df.to_csv(out_path, index=False, lineterminator="\n")
    print(f"wrote {out_path}")
    for loss in losses:
        print(f"\n===== loss {loss} dB =====")
        sub = out_df[out_df["loss"] == loss]
        print(sub.to_string(index=False))


if __name__ == "__main__":
    main()
