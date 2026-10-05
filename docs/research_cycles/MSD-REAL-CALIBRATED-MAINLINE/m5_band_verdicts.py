"""M5 verdict + f-recompute companion (addresses Pre-RESULT F-A/F-B/F-E).

Reads frozen summaries + P1 scalars; writes verdict fields (band verdicts,
exact binomial p-values, full f inputs incl. H_A/H_AB/tag/kept-penalty) into
a NEW companion file (frozen summaries untouched). Amends NOTHING numerically.
"""

from __future__ import annotations

import argparse
import json
import math
from math import comb
from pathlib import Path


def wilson_up(k: int, n: int, z: float = 1.96) -> float:
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(max(0.0, p * (1 - p) / n + z * z / (4 * n * n))) / d
    return min(1.0, c + h)


def p_ge(k: int, n: int, p: float) -> float:
    return sum(comb(n, i) * (p ** i) * ((1 - p) ** (n - i)) for i in range(k, n + 1))


SYNTH_BANDS = {
    # (synth_k, synth_n) per arm family for H0 upper
    "msd-m2-frozen": (0, 300),
    "nb-R1": (0, 100),
    "nb-R2-T2-1.5M": (1, 100),
    "nb-R2": (0, 100),
}


def band_for(row: dict) -> tuple[int, int]:
    if row["backend"] == "msd-m2-frozen":
        return SYNTH_BANDS["msd-m2-frozen"]
    if row.get("arm") == "P1S1-R2" and row["source"] == "T2-1.5M":
        return SYNTH_BANDS["nb-R2-T2-1.5M"]
    return SYNTH_BANDS["nb-R1"] if row.get("arm") == "P1S1-R1" else SYNTH_BANDS["nb-R2"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--result-root", required=True)
    ap.add_argument("--p1-numbers", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    root = Path(args.result_root)
    p1 = json.loads(Path(args.p1_numbers).read_text(encoding="utf-8"))
    scalars = {}
    for row in p1["analysis_rows"]:
        if row.get("encoding") == "NATURAL" and row.get("order") == "LSB_FIRST":
            scalars[row["source"]] = (float(row["analysis"]["H_A_bits_per_symbol"]),
                                      float(row["analysis"]["H_A_given_B_bits_per_symbol"]))
    out_rows = []
    for name in ("m5_msd_summary.json", "m5_nb_summary.json"):
        rows = json.loads((root / name).read_text(encoding="utf-8"))
        for r in rows:
            n = int(r["blocks"]) if "blocks" in r else int(r.get("N", 0))
            n = int(r["blocks"])
            k = int(r["failures"])
            ha, hab = scalars[r["source"]]
            sk, sn = band_for(r)
            up = wilson_up(sk, sn)
            pv = p_ge(k, n, up)
            verdict = "CONSISTENT" if pv >= 0.05 else "INCONSISTENT"
            nn = int(r["N"])
            lec = float(r["E_L"])
            tag = 64
            kept = nn * ha - lec
            denom = nn * hab
            f_p = (lec + tag + kept * (k / n)) / denom
            f_u = (lec + tag + kept * up) / denom
            wu_obs = wilson_up(k, n)
            f_u_obs = (lec + tag + kept * wu_obs) / denom
            assert abs(f_p - float(r["f_expected"])) < 5e-9, (name, r.get("source"), f_p)
            out_rows.append({
                "source": r["source"], "arm": r.get("arm", r.get("backend")),
                "backend": r["backend"], "N": nn, "blocks": n, "failures": k,
                "FER_exact": k / n, "H_A": ha, "H_AB": hab, "tag_bits": tag,
                "E_L": lec, "kept_weighted_penalty_bits": kept * (k / n),
                "f_expected_recomputed": f_p,
                "f_expected_upper95_recomputed": f_u_obs,
                "f_at_band_upper_recomputed": f_u,
                "f_expected_match": abs(f_p - float(r["f_expected"])) < 5e-9,
                "synth_band_k": sk, "synth_band_n": sn,
                "synth_band_upper95": up, "consistency_p_value": pv,
                "consistency_verdict": verdict,
                "undetected": int(r["undetected"]),
            })
    Path(args.output).write_text(json.dumps({"verdict_rows": out_rows}, indent=2),
                                 encoding="utf-8")
    for r in out_rows:
        print(r["source"], r["arm"], r["backend"], f"FER={r['failures']}/{r['blocks']}",
              f"p={r['consistency_p_value']:.4f}", r["consistency_verdict"],
              f"f_match={r['f_expected_match']}")


if __name__ == "__main__":
    main()
