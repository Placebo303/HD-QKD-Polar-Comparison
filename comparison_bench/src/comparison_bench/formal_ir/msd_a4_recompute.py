"""A4 D5/D6 pure-arithmetic recomputation (no decoder, landed artifacts only).

D5: Net_per_used = Net_seg/(B*N); budget-unused fraction = 1-B*N/5M (renamed,
    NOT tail waste); verify Net_per_coin == Net_seg/5M degeneracy; recompute
    beta on head-note basis I_op=H_A-H_AB and f on H_AB basis for the C1 row.
D6: Net@60s portrait Net_seg*60/(B*T_p50) (interp. iff B*T_p50>=60 else n/a);
    C1 override for F1-A3/4096; flag F2-A3 1024-value mis-paste and the
    unrecoverable F1-A3 +6,845.

Reads: workspace/c3_mini/final_cells.json, workspace/c3_mini/final_opt.json,
       workspace/c3_mtune/mt_20261008/cells.json (medians),
       workspace/c3_mtune/mt_20261009c1b/cells.json (C1 override).
Writes: a4_d5.csv/json + a4_d6.csv/json under fresh --output-root.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

C_PLAN = 5_000_000.0
HAB = {"F1": 0.38901, "F2": 0.22579, "F3": 1.03750}
HA = {"F1": 10.0, "F2": 9.0, "F3": 11.0}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    root = Path(args.output_root)
    if root.exists():
        raise SystemExit(f"output root not fresh: {root}")
    root.mkdir(parents=True, exist_ok=True)

    cells = json.load(open("workspace/c3_mini/final_cells.json", encoding="utf-8"))
    opt = json.load(open("workspace/c3_mini/final_opt.json", encoding="utf-8"))
    m2 = json.load(open("workspace/c3_mtune/mt_20261008/cells.json", encoding="utf-8"))
    m2cells = m2 if isinstance(m2, list) else m2.get("cells", [])
    c1 = json.load(open("workspace/c3_mtune/mt_20261009c1b/cells.json", encoding="utf-8"))

    med_of: dict[tuple, float] = {}
    for c in m2cells:
        if not isinstance(c, dict):
            continue
        key = (c.get("WP"), c.get("method"), c.get("variant", "") or "", int(c.get("N", 0)))
        for k in ("T_p50", "median_T_dec", "p50_T_dec"):
            if c.get(k):
                med_of[key] = float(c[k])
                break
    for c in c1:
        med_of[(c.get("WP"), c.get("method"), c.get("variant", "") or "", int(c.get("N", 0)))] = float(c["T_p50"])

    # ---------------- D5 ----------------
    d5 = []
    for c in cells:
        fam, n, b = c.get("family"), c.get("N"), c.get("B")
        net = c.get("Net_seg")
        if fam not in HAB or not n or not b or net is None:
            continue
        per_used = net / (b * n)
        per_coin = net / C_PLAN
        unused = 1.0 - b * n / C_PLAN
        d5.append({"family": fam, "method": c.get("method"),
                   "variant": c.get("variant"), "N": n, "B": b,
                   "Net_seg": round(net, 1),
                   "Net_per_used": round(per_used, 4),
                   "Net_per_coin_5M": round(per_coin, 4),
                   "coin_is_scaled_seg": True,
                   "budget_unused_frac": round(unused, 5),
                   "flag": c.get("flag"), "evidence": c.get("evidence")})
    # C1 head-note cross-checks (arbitration D5 incidentals)
    c1r = c1[0]
    B, N = int(c1r["B"]), int(c1r["N"])
    beta_head = c1r["Net_seg"] / (B * N * (HA["F1"] - HAB["F1"]))
    f_hab = c1r["L_total"] / (B * N * HAB["F1"])
    d5_note = {
        "C1_F1-A3/4096": {
            "Net_per_used": round(c1r["Net_seg"] / (B * N), 4),
            "budget_unused_frac": round(1 - B * N / C_PLAN, 5),
            "beta_artifact_log2q_basis": round(c1r["beta_side"], 4),
            "beta_headnote_Iop_basis": round(beta_head, 4),
            "f_HAB_basis_table": round(f_hab, 4),
            "f_artifact_HA_basis": round(c1r["f_full"], 4),
        }
    }
    (root / "a4_d5.json").write_text(json.dumps({"rows": d5, "c1_note": d5_note}, indent=1), encoding="utf-8")
    with open(root / "a4_d5.csv", "w", encoding="utf-8") as f:
        f.write("family,method,variant,N,B,Net_seg,Net_per_used,Net_per_coin_5M,budget_unused_frac,flag,evidence\n")
        for r in d5:
            f.write(f"{r['family']},{r['method']},{r['variant']},{r['N']},{r['B']},"
                    f"{r['Net_seg']},{r['Net_per_used']},{r['Net_per_coin_5M']},"
                    f"{r['budget_unused_frac']},{r['flag']},{r['evidence']}\n")
    print(f"D5: {len(d5)} rows; C1 beta {c1r['beta_side']:.3f}->head {beta_head:.4f}; "
          f"f {c1r['f_full']:.4f}->HAB {f_hab:.4f}")

    # ---------------- D6 ----------------
    # OPT portrait cells: (fam, method-key, variant-key, N) with Net_seg source.
    opt_cells = [
        ("F1", "A3", "", 4096, 8689788.0, "C1"),
        ("F2", "A3", "", 4096, 10312400.0, "M"),
    ]
    # full OPT portrait from final_cells (best Net_seg per fam/method/var, N<=16384, flag ok)
    best: dict[tuple, dict] = {}
    for c in cells:
        if c.get("evidence", "").startswith(("M1", "M-")) and c.get("flag") == "ok" \
                and c.get("N", 0) <= 16384 and c.get("family") in HAB:
            key = (c["family"], c["method"], c.get("variant", "") or "")
            if key not in best or c["Net_seg"] > best[key]["Net_seg"]:
                best[key] = c
    d6 = []
    for key, c in sorted(best.items()):
        fam, meth, var = key
        B, N, net = int(c["B"]), int(c["N"]), float(c["Net_seg"])
        med = med_of.get((fam, meth, var, N), c.get("median_T_dec") or 0.0)
        tot = B * (med or 0.0)
        net60 = round(net * 60.0 / tot, 0) if tot >= 60.0 else None
        # artifact value from final_opt (pre-C1)
        art = next((o for o in opt if o["family"] == fam and o["method"] == meth
                    and (o.get("variant", "") or "") == var), None)
        d6.append({"family": fam, "method": meth, "variant": var, "N": N,
                   "B": B, "Net_seg": round(net, 0), "T_p50": round(med, 3),
                   "B_T_total": round(tot, 1),
                   "Net60_recomputed": net60,
                   "Net60_artifact": art.get("Net_same_time") if art else None,
                   "artifact_opt_N": art.get("opt_N") if art else None})
    # C1 override row for F1-A3/4096 (post-C1 OPT)
    med_c1 = float(c1r["T_p50"])
    net60_c1 = round(c1r["Net_seg"] * 60.0 / (300 * med_c1), 0)
    d6.append({"family": "F1", "method": "A3", "variant": "", "N": 4096,
               "B": 300, "Net_seg": 8689788.0, "T_p50": round(med_c1, 3),
               "B_T_total": round(300 * med_c1, 1),
               "Net60_recomputed": net60_c1,
               "Net60_artifact": 6845, "note": "artifact +6,845 unrecoverable; "
               "F2-A3 artifact +1,422,931 is the N=1024 value mis-pasted"})
    # Q1-b portrait for F2-A3/4096 (flag 未定 F=8, Net known from M-fresh)
    f2net, f2med = 10312400.0, float(med_of.get(("F2", "A3", "", 4096), 3.8329568500630558))
    d6.append({"family": "F2", "method": "A3", "variant": "", "N": 4096,
               "B": 300, "Net_seg": f2net, "T_p50": round(f2med, 3),
               "B_T_total": round(300 * f2med, 1),
               "Net60_recomputed": round(f2net * 60.0 / (300 * f2med), 0),
               "Net60_artifact": 1422931.2568163406,
               "note": "Q1-b cell (FER 未定 F=8); artifact value is the "
               "N=1024 portrait mis-pasted into the 4096 OPT row"})
    (root / "a4_d6.json").write_text(json.dumps(d6, indent=1), encoding="utf-8")
    with open(root / "a4_d6.csv", "w", encoding="utf-8") as f:
        f.write("family,method,variant,N,B,Net_seg,T_p50,B_T_total,Net60_recomputed,Net60_artifact\n")
        for r in d6:
            f.write(f"{r['family']},{r['method']},{r['variant']},{r['N']},{r['B']},"
                    f"{r['Net_seg']},{r['T_p50']},{r['B_T_total']},"
                    f"{r['Net60_recomputed']},{r.get('Net60_artifact')}\n")
    for r in d6:
        if (r["family"], r["method"]) in (("F1", "A3"), ("F2", "A3")):
            print(f"D6 {r['family']}-{r['method']}/{r['N']}: Net={r['Net_seg']:.0f} "
                  f"T50={r['T_p50']} -> Net60={r['Net60_recomputed']} "
                  f"(artifact {r.get('Net60_artifact')})")
    print(f"wrote D5 ({len(d5)}) + D6 ({len(d6)}) -> {root}")


if __name__ == "__main__":
    main()
