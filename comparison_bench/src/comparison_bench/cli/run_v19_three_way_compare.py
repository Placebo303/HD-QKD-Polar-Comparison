"""N6 three-way comparison table generator (Polar / binary LDPC / nonbinary LDPC).

This CLI reads existing diagnostic JSON evidence (or explicit paths) and emits
a comparison table with the exact schema from the focus plan:
  route, N, q, rate, syndrome_bits, public_bits, f, FER, runtime, status

It never merges statuses or converts ``decode_failed`` into ``ok``.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from ..formal_ir.nonbinary_v19_channel import H_FULL_Q1024

DEFAULT_BINARY_LDPC = Path("comparison_bench") / "outputs_comparison" / "nonbinary_diagnostics" \
    / "v19_binary_mlc_prototype_20260816" / "binary_mlc_prototype.json"

SCHEMA = "nbldpc_v19_three_way_comparison_v1"
COLUMNS = ["route", "N", "q", "rate", "syndrome_bits", "public_bits",
           "f", "FER", "runtime", "status"]


def _load_json(path: str | Path | None) -> dict | None:
    if path is None:
        return None
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"evidence file not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def _binary_ldpc_row(doc: dict) -> dict:
    n_symbols = int(doc.get("block_length", 256))
    total_syndrome = int(round(doc.get("total_syndrome_bits_per_frame", 0)))
    total_bits = n_symbols * 10
    rate = 1.0 - total_syndrome / float(total_bits) if total_bits else None
    runtime = sum(float(r.get("runtime_s", 0.0)) for r in doc.get("per_plane", [])) \
        / float(doc.get("frames_per_plane", 1) or 1)
    return {
        "route": "binary_ldpc_mlc",
        "N": n_symbols,
        "q": 2,
        "rate": round(rate, 6) if rate is not None else None,
        "syndrome_bits": total_syndrome,
        "public_bits": 0,
        "f": round(float(doc.get("measured_f", float("nan"))), 6),
        "FER": 0.0 if int(doc.get("total_failures", 0)) == 0 else
               float(doc.get("total_failures", 0)) / (float(doc.get("frames_per_plane", 1)) * 10),
        "runtime": round(runtime, 6),
        "status": "ok" if int(doc.get("total_failures", 0)) == 0 else "has_failures",
    }


def _nonbinary_row(doc: dict) -> dict:
    n = int(doc.get("n"))
    q = int(doc.get("q"))
    m = int(doc.get("m"))
    total_frames = int(doc.get("n_frames"))
    n_failed = int(doc.get("n_decode_failed", 0))
    n_mismatch = int(doc.get("n_exact_mismatch", 0))
    n_exact = int(doc.get("n_exact_correct", 0))
    fer = float(doc.get("fer") or 0.0)
    runtime_per_frame = float(doc.get("wall_seconds", 0.0)) / total_frames if total_frames else None
    return {
        "route": "nonbinary_ldpc",
        "N": n,
        "q": q,
        "rate": round(float(doc.get("rate")), 6),
        "syndrome_bits": int(m * (q.bit_length() - 1)),
        "public_bits": 0,
        "f": round(float(doc.get("f_plain_qary")), 6),
        "FER": round(fer, 6),
        "runtime": round(runtime_per_frame, 6) if runtime_per_frame is not None else None,
        "status": "exact_correct_all" if n_failed == 0 and n_mismatch == 0 else
                  ("has_decode_failed" if n_failed > 0 else "has_exact_mismatch"),
    }


def _polar_row(doc: dict | None) -> dict:
    if doc is None:
        return {
            "route": "binary_polar_mlc",
            "N": None,
            "q": 2,
            "rate": None,
            "syndrome_bits": None,
            "public_bits": None,
            "f": None,
            "FER": None,
            "runtime": None,
            "status": "not_available",
        }
    # If a future Polar MLC evidence JSON follows the same shape, convert it.
    n_symbols = int(doc.get("block_length", 256))
    total_bits = n_symbols * 10
    syndrome = int(round(doc.get("total_syndrome_bits_per_frame", 0)))
    return {
        "route": "binary_polar_mlc",
        "N": n_symbols,
        "q": 2,
        "rate": round(1.0 - syndrome / float(total_bits), 6) if total_bits else None,
        "syndrome_bits": syndrome,
        "public_bits": 0,
        "f": round(float(doc.get("measured_f", float("nan"))), 6),
        "FER": 0.0 if int(doc.get("total_failures", 0)) == 0 else
               float(doc.get("total_failures", 0)) / (float(doc.get("frames_per_plane", 1)) * 10),
        "runtime": round(float(doc.get("runtime_s", 0.0)), 6),
        "status": "ok" if int(doc.get("total_failures", 0)) == 0 else "has_failures",
    }


def run_compare(*, binary_ldpc_path: str | Path | None = None,
                nonbinary_path: str | Path | None = None,
                nonbinary_q1024_path: str | Path | None = None,
                polar_path: str | Path | None = None,
                out_dir: str | Path | None = None) -> dict:
    binary_doc = _load_json(binary_ldpc_path or DEFAULT_BINARY_LDPC)
    nonbinary_doc = _load_json(nonbinary_path)
    nonbinary_q1024_doc = _load_json(nonbinary_q1024_path)
    polar_doc = _load_json(polar_path)
    rows = [_polar_row(polar_doc), _binary_ldpc_row(binary_doc), _nonbinary_row(nonbinary_doc)]
    # Keep only rows whose evidence exists; missing nonbinary is a hard error
    # for a meaningful N6, but we still emit all rows with explicit status.
    if nonbinary_doc is None:
        rows[2]["status"] = "not_available"
    if nonbinary_q1024_doc is not None:
        row = _nonbinary_row(nonbinary_q1024_doc)
        row["route"] = "nonbinary_ldpc_q1024"
        rows.append(row)
    else:
        rows.append({
            "route": "nonbinary_ldpc_q1024",
            "N": None, "q": 1024, "rate": None, "syndrome_bits": None,
            "public_bits": 0, "f": None, "FER": None, "runtime": None,
            "status": "not_available",
        })
    summary = {
        "schema": SCHEMA,
        "h_full_q1024": H_FULL_Q1024,
        "claim_boundary": "diagnostic_only",
        "rows": rows,
        "notes": [
            "Binary Polar MLC row is marked not_available until a clean per-plane MLC evidence JSON is produced.",
            "Binary LDPC MLC row is from v19_binary_mlc_prototype_20260816 (f~4.17, 0 failures).",
            "Nonbinary LDPC rows are diagnostic_only; statuses preserve decode_failed/exact_mismatch.",
        ],
    }
    if out_dir is not None:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        with (out / "comparison_table.csv").open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        (out / "comparison_summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--binary-ldpc-json", default=None)
    ap.add_argument("--nonbinary-json", required=True)
    ap.add_argument("--nonbinary-q1024-json", default=None)
    ap.add_argument("--polar-json", default=None)
    args = ap.parse_args()
    doc = run_compare(binary_ldpc_path=args.binary_ldpc_json,
                      nonbinary_path=args.nonbinary_json,
                      nonbinary_q1024_path=args.nonbinary_q1024_json,
                      polar_path=args.polar_json,
                      out_dir=Path(args.out_dir))
    print(json.dumps(doc, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
