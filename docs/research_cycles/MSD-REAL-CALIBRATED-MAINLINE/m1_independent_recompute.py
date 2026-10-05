"""Independent recomputation of M1 conclusive numbers (no runner imports).

Reads workspace/m1_synthetic/m1_20261005/m1_summary.json + P1_NUMBERS.json,
recomputes FER/F-hat/upper bounds from raw counts with an independent
Wilson implementation, and checks the frozen f formula field-by-field.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def wilson_upper_ind(k: int, n: int, z: float = 1.96) -> float:
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(max(0.0, p * (1 - p) / n + z * z / (4 * n * n))) / d
    return min(1.0, c + h)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--result-root", required=True)
    ap.add_argument("--summary", default="m1_summary.json")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    root = Path(args.result_root)
    rows = json.loads((root / args.summary).read_text(encoding="utf-8"))
    checked = 0
    mismatches: list[str] = []
    operating: list[dict] = []
    for r in rows:
        n, lec = int(r["N"]), int(r["L_EC"]) if "L_EC" in r else None
        # M2 rows carry expected disclosure E_L (+ optional L_base/n_rescue audit)
        if "E_L" in r:
            e_l = float(r["E_L"])
            exp_extra = float(r["k_rescue"]) * int(r["n_rescue"]) / int(r["blocks"])
            if abs(e_l - (float(r["L_base"]) + exp_extra)) > 1e-6:
                mismatches.append(f"{r['source']}/{n}/{r.get('gap', r.get('c0_base'))}: E_L audit")
            lec = e_l
        else:
            lec = float(r["L_EC"])
        label = f"{r['source']}/{n}/{r.get('gap', r.get('c0_base'))}"
        fer = float(r["failures"]) / int(r["blocks"])
        if abs(fer - float(r["FER_exact"])) > 1e-12:
            mismatches.append(f"{label}: FER_exact")
        wu = wilson_upper_ind(int(r["failures"]), int(r["blocks"]))
        if abs(wu - float(r["FER_wilson_upper95"])) > 1e-9:
            mismatches.append(f"{label}: wilson")
        denom = n * float(r["H_AB"])
        kept = n * float(r["H_A"]) - lec
        f_p = (lec + 64 + kept * fer) / denom
        f_u = (lec + 64 + kept * wu) / denom
        if abs(f_p - float(r["f_expected"])) > 1e-9:
            mismatches.append(f"{label}: f_expected")
        if abs(f_u - float(r["f_expected_upper95"])) > 1e-9:
            mismatches.append(f"{label}: f_upper")
        checked += 1
        operating.append(
            {
                "source": r["source"],
                "N": n,
                "gap": r.get("gap", f"c0:{r.get('c0_base')}/K:{r.get('k_rescue')}"),
                "backend": r["backend"],
                "f_expected": f_p,
                "f_expected_upper95": f_u,
                "failures": int(r["failures"]),
                "blocks": int(r["blocks"]),
                "undetected": int(r["undetected"]),
            }
        )
    verdict = "PASS" if not mismatches else "FAIL"
    Path(args.output).write_text(
        json.dumps(
            {"verdict": verdict, "fields_checked": checked, "mismatches": mismatches,
             "operating_rows": operating},
            indent=2,
        ),
        encoding="utf-8",
    )
    print(verdict, f"{checked} rows", f"{len(mismatches)} mismatches")


if __name__ == "__main__":
    main()
