"""S-3''' summary recompute (unit fix): L_u2 rows x 5 bits.

The runner stored per-block L_u2 in ROW units; correct E_u2 = 5*mean(L_u2).
Recomputes E_L/FER/f per m from block JSONL (no rerun).
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
    ap.add_argument("--root", required=True)
    args = ap.parse_args()
    root = Path(args.root)
    ha, hab, n, tag = 9.9976919099, 0.7981344445, 1024, 64
    recs = [json.loads(l) for l in open(root / "blocks_s3t.jsonl", encoding="utf-8")]
    rows = []
    for m in sorted(set(r["m_base"] for r in recs)):
        a = [r for r in recs if r["m_base"] == m]
        nb = len(a)
        nf = sum(0 if r["exact_full"] else 1 for r in a)
        nu = sum(1 for r in a if r["undetected"])
        e_u2 = sum(5 * r["L_u2"] for r in a) / nb
        e_u1 = sum((r["L_u1"] + r.get("u1_extra", 0)) if r.get("u2_ok", True) else 0
                   for r in a) / nb
        e_l = e_u2 + e_u1
        fer = nf / nb
        denom = n * hab
        kept = n * ha - e_l
        f_p = (e_l + tag + kept * fer) / denom
        f_up = (e_l + tag + kept * wilson_up(nf, nb)) / denom
        rows.append({"m_base": m, "blocks": nb, "failures": nf, "undetected": nu,
                     "E_u2": e_u2, "E_u1": e_u1, "E_L": e_l, "FER_exact": fer,
                     "FER_wilson_upper95": wilson_up(nf, nb),
                     "f_expected": f_p, "f_expected_upper95": f_up,
                     "source": "T2-1M", "N": n, "backend": "nb-u1chain-mgrid"})
        print(f"m={m}: fail {nf}/{nb} E_L={e_l:.0f} f={f_p:.3f} (up {f_up:.3f})",
              flush=True)
    (root / "s3t_summary_fixed.json").write_text(json.dumps(rows, indent=2),
                                                encoding="utf-8")


if __name__ == "__main__":
    main()
