"""C-3 mapped-reference derivation (R5: numbers by script, read-only landed rows).

Cross-regime reference only (p=0.24 / p~0.12 NB regimes vs F1/F2 calibrated
p*): NEVER OPT competitors (different p_op). uniform-block rows with F=0,
so per-block mapping is exact. C_total = B*N (w_tail=0 assumption, recorded);
compare across fresh/mapped via f_full + Net_per_used (NOT Net_per_coin,
whose C_total conventions differ: mini uses planning 5M).
"""

import json

from comparison_bench.src.comparison_bench.formal_ir import msd_c1_runner as RU

H_A = 9.9976919099
H_AB = 0.7981344445
I_OP = 10.0 - H_AB


def summarize(tag, rows, N, C_total=None):
    import math
    B = len(rows)
    Ct = float(C_total) if C_total else float(B * N)
    F = sum(1 for r in rows if r["ver"] == 0)
    U = sum(1 for r in rows if r["u"] == 1)
    S = sum(1 for r in rows if r["ver"] == 1 and r["u"] == 0)
    s_kept = sum(r["kept"] for r in rows if r["ver"] == 1 and r["u"] == 0)
    s_lec = sum(r["L_EC"] for r in rows)
    n_tags = sum(1 for r in rows if r["ver"] == 1)
    # Same R16 formula as net_of_cell, per-block sums (non-uniform extension).
    net_seg = s_kept - s_lec - n_tags * 64
    L_total = s_lec + S * 64
    denom = B * N * H_AB
    out = {"Net_seg": net_seg, "L_total": L_total,
           "Net_per_coin": net_seg / Ct, "Net_per_used": net_seg / (B * N),
           "f_full": L_total / denom, "FER_hat": F / B,
           "w_tail": (Ct - B * N) / Ct,
           "beta_side": net_seg / (B * N * I_OP)}
    # Cross-check against net_of_cell on uniform cells.
    lec = [r["L_EC"] for r in rows]
    if all(x == lec[0] for x in lec) and (S == 0 or
            all(r["kept"] == rows[0]["kept"] for r in rows if r["ver"] == 1)):
        ref = RU.net_of_cell(kept_bits=rows[0]["kept"], L_EC_bits=float(lec[0]),
                             tag_bits=64, n_fail=F, n_blocks=B,
                             C_total=Ct, N=N, n_undetected=U,
                             h_op=H_AB, I_op=I_OP)
        for k in out:
            assert abs(out[k] - ref[k]) < 1e-6 * max(1.0, abs(ref[k])), (tag, k)
        out["_via"] = "net_of_cell-exact"
    else:
        out["_via"] = "per-block-sums(same-formula)"
    print(tag, f"B={B} N={N} F={F} U={U} [{out['_via']}]")
    for k in ("Net_seg", "Net_per_coin", "Net_per_used", "f_full",
              "FER_hat", "w_tail", "beta_side"):
        print(f"  {k} = {out[k]}")
    return out


# --- G-5 best + control (synthetic, p=0.24 regime, N=32768, B=300) ---
g5 = [json.loads(x) for x in
      open("workspace/g5_bakeoff/g5_20261008/blocks_g5.jsonl", encoding="utf-8")]
for A, mg, meth in (("RA-q5-gap0.08", 3.0, "A1"),
                    ("polar-SCL8-0.88", 3.0, "A2")):
    cell = [r for r in g5 if r["A"] == A and r["margin"] == mg and r["n"] == 32768]
    assert len(cell) == 300, (A, len(cell))
    rows = []
    for i, r in enumerate(cell):
        rec = dict(r, block=i)
        kept = 32768 * H_A  # raw material; disclosure subtracted once in net
        rows.append(RU.adapt_g5_block(rec, method=meth, N=32768,
                                      kept_bits=kept, code_hash=f"{meth}-N32768-g5-{A}-m{mg}"))
    summarize(f"mapped-{meth} G-5 {A} m{mg} (synthetic p=0.24)", rows, 32768)

# --- F-1 4dB-diff (real-clean-OOS, N=1024, 0/112) ---
f1 = [json.loads(x) for x in
      open("workspace/f1_oos/f1_20261007/blocks_f1.jsonl", encoding="utf-8")]
cell = [r for r in f1 if r["seg"] == "4dB" and r["arm"] == "diff"]
assert len(cell) == 112, len(cell)
rows = []
for r in cell:
    kept = 1024 * H_A  # raw material; disclosure subtracted once in net
    rows.append(RU.adapt_m4_block(
        {"N": 1024, "block": r["block"], "L_EC": r["L_u2"] + r["L_u1"] + r.get("u1_extra", 0),
         "exact_ok": r["exact_full"], "undetected": r["undetected"]},
        method="A6", kept_bits=kept, code_hash="A6-F1-4dB-diff-adapted"))
summarize("mapped-A6 F-1 4dB-diff (real-clean-OOS)", rows, 1024)

# --- D-4 0dB-diff (real-retest, N=1024, 0/260) ---
d4 = [json.loads(x) for x in
      open("workspace/d4_oos/d4_20261007/blocks_d4.jsonl", encoding="utf-8")]
cell = [r for r in d4 if r["arm"] == "diff"]
assert len(cell) == 260, len(cell)
rows = []
for r in cell:
    kept = 1024 * H_A  # raw material; disclosure subtracted once in net
    rows.append(RU.adapt_m4_block(
        {"N": 1024, "block": r["block"], "L_EC": r["L_u2"] + r["L_u1"] + r.get("u1_extra", 0),
         "exact_ok": r["exact_full"], "undetected": r["undetected"]},
        method="A6", kept_bits=kept, code_hash="A6-D4-0dB-diff-adapted"))
summarize("mapped-A6 D-4 0dB-diff (real-retest)", rows, 1024)
print("A5 mapped: absent (no block rows; three_way_compare summary-only) | "
      "A7: unavailable")
