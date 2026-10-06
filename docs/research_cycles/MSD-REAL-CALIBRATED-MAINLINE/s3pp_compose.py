"""S-3'' composition generator (provenance for s3pp_composition.json).

Inputs: s3pp_u2curve.json (per-m u2 fails/rescues/undetected), S-3' u1|u2
measured inputs (CLI args), P1 scalars. Rescue disclosure is (208-m_base)*5
bits per rescued block (nested rows), NOT flat +40. Full-symbol f with
u1|u2 approximation stated.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def wilson_up(k: int, n: int, z: float = 1.96) -> float:
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(max(0.0, p * (1 - p) / n + z * z / (4 * n * n))) / d
    return min(1.0, c + h)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--u2curve", required=True)
    ap.add_argument("--u1-fails", type=int, required=True)
    ap.add_argument("--u1-blocks", type=int, required=True)
    ap.add_argument("--u1-disc", type=float, required=True)
    ap.add_argument("--h-a", type=float, required=True)
    ap.add_argument("--h-ab", type=float, required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    curve = json.loads(Path(args.u2curve).read_text(encoding="utf-8"))
    rows = []
    for r in curve:
        m, n = int(r["m_base"]), int(r["blocks"])
        nf, nr = int(r["u2_failures"]), int(r["n_rescue"])
        e_u2 = 5 * m + (208 - m) * 5 * nr / n
        e_l = e_u2 + args.u1_disc
        f_u2 = nf / n
        f1 = args.u1_fails / args.u1_blocks
        f_full = 1 - (1 - f_u2) * (1 - f1)
        denom = 1024 * args.h_ab
        kept = 1024 * args.h_a - e_l
        f_p = (e_l + 64 + kept * f_full) / denom
        f_up = (e_l + 64 + kept * wilson_up(nf, n)) / denom
        rows.append({"m_base": m, "u2_fer": f_u2, "n_rescue_u2": nr,
                     "u2_undetected": int(r.get("u2_undetected", 0)),
                     "E_u2": e_u2, "E_L": e_l, "full_fer": f_full,
                     "full_f": f_p, "full_f_upper95": f_up})
    rows.sort(key=lambda r: r["full_f"])
    out = {"m_curve": rows, "optimum_m": rows[0]["m_base"],
           "u1_given_u2": {"fails": args.u1_fails, "blocks": args.u1_blocks,
                           "disclosure_mean": args.u1_disc,
                           "note": "measured once (u2 m=200 stream); applied to all m"},
           "real_prediction": "proxy Tier1 overestimates u2 FER ~2x vs M5-real; "
                              "real full-symbol expectation by analogy, NOT a measurement"}
    Path(args.output).write_text(json.dumps(out, indent=2), encoding="utf-8")
    for r in rows:
        print(r["m_base"], round(r["full_f"], 3), round(r["full_f_upper95"], 3),
              "E_L", round(r["E_L"], 1))


if __name__ == "__main__":
    main()
