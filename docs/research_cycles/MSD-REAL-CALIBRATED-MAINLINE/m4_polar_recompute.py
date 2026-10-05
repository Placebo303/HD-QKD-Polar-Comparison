"""M4 Polar-arm recompute (no execution): same-f-metric restatement of the
sibling low_dim_opt final_table (external reference, different data/channel).

f = (H_A - Y) / (H_A - I_AB) per row from h_a_bits / i_ab / y_exp columns;
O4-R shift (+0.158 bit/pair, sibling README/FINAL_SUMMARY) applied as a
labeled approximation identical to REBOOT_HANDOFF 20261004 section 3.1.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

O4R_SHIFT = 0.158  # bit/pair, sibling O4-R adopted gain (approx, uniform)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--table", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    rows = []
    with open(args.table, encoding="utf-8") as fh:
        for rec in csv.DictReader(fh):
            if rec.get("row_kind") != "point":
                continue
            try:
                ha = float(rec["h_a_bits"])
                iab = float(rec["i_ab"])
                y = float(rec["y_exp_O1b2_3seed_mean"])
            except (KeyError, ValueError):
                continue
            hab = ha - iab
            if hab <= 0:
                continue
            f_o1b2 = (ha - y) / hab
            f_o4r = (ha - (y + O4R_SHIFT)) / hab
            rows.append({"d": rec.get("d"), "bin_width_ps": rec.get("bin_width_ps"),
                         "layers": rec.get("layers_active"), "H_A": ha, "I_AB": iab,
                         "Y_O1b2": y, "f_O1b2": f_o1b2, "f_O1b2_O4Rshift": f_o4r})
    o1 = sum(r["f_O1b2"] for r in rows) / len(rows)
    o4 = sum(r["f_O1b2_O4Rshift"] for r in rows) / len(rows)
    Path(args.output).write_text(json.dumps({
        "scope": "EXTERNAL reference restatement only: sibling polarization-entanglement "
                 "curve data (d=32-512), NOT our d=1024 time-bin channel. Not comparable "
                 "head-to-head; same-formula restatement for calibration of expectations.",
        "n_points": len(rows), "mean_f_O1b2": o1, "mean_f_O1b2_O4Rshift": o4,
        "O4R_shift_bit_per_pair": O4R_SHIFT, "rows": rows}, indent=2), encoding="utf-8")
    print(f"points {len(rows)} mean_f_O1b2 {o1:.4f} mean_f_O4Rshift {o4:.4f}")


if __name__ == "__main__":
    main()
