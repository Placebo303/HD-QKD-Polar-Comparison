"""V19 binary-MLC prototype: decode each Gray bit-plane with existing v4 H1 LDPC.

This is a synthetic diagnostic. It uses the frozen binary LDPC v4 H1 matrices and
the V17 per-plane BSC error probabilities to show that a per-plane binary MLC
pipeline can correct all synthetic errors with the existing v4 codebook, and to
report the resulting f. It does not change frozen baselines.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from ..formal_ir import codebook_v4
from ..formal_ir import codebook_v5_h2
from ..formal_ir.nonbinary_v18_b2_structured_de import _V17_PER_PLANE_ERROR
from .run_v19_channel_scoping import h2


def run_prototype(*, frames_per_plane: int, seed: int = 2026081901,
                  candidate_id: int = 0) -> dict:
    n = codebook_v4.BLOCK_LENGTH
    h_full = sum(h2(float(p)) for p in _V17_PER_PLANE_ERROR)
    rows = []
    total_failures = 0
    for plane, p in enumerate(_V17_PER_PLANE_ERROR):
        h1 = codebook_v4.matrix_for(plane, candidate_id)
        h2_mat, _ = codebook_v5_h2.generate_h2(plane, h1)
        h_stack = np.vstack((h1, h2_mat)).astype(np.uint8)
        rng = np.random.default_rng(seed + plane)
        failures = 0
        fallbacks = 0
        syndrome_bits_total = 0
        started = time.monotonic()
        for _ in range(frames_per_plane):
            e = np.zeros(n, dtype=np.uint8)
            e[rng.random(n) < float(p)] = 1
            syn1 = (h1 @ e % 2).astype(np.uint8)
            syn_stack = (h_stack @ e % 2).astype(np.uint8)
            try:
                from ldpc import BpOsdDecoder
                dec1 = BpOsdDecoder(
                    h1,
                    error_channel=[float(p)] * n,
                    max_iter=50,
                    bp_method="product_sum",
                    schedule="serial",
                    omp_thread_count=1,
                    serial_schedule_order=list(range(n)),
                    osd_method="OSD_CS",
                    osd_order=2,
                )
                ehat = np.asarray(dec1.decode(syn1)).reshape(-1).astype(np.uint8)
                ok = np.array_equal(ehat, e) and np.array_equal(h1 @ ehat % 2, syn1)
                used_h2 = False
                if not ok:
                    fallbacks += 1
                    used_h2 = True
                    dec2 = BpOsdDecoder(
                        h_stack,
                        error_channel=[float(p)] * n,
                        max_iter=100,
                        bp_method="product_sum",
                        schedule="serial",
                        omp_thread_count=1,
                        serial_schedule_order=list(range(n)),
                        osd_method="OSD_CS",
                        osd_order=2,
                    )
                    ehat = np.asarray(dec2.decode(syn_stack)).reshape(-1).astype(np.uint8)
                    ok = np.array_equal(ehat, e) and np.array_equal(h_stack @ ehat % 2, syn_stack)
                if ok:
                    syndrome_bits_total += int(h1.shape[0]) + (int(h2_mat.shape[0]) if used_h2 else 0)
                else:
                    failures += 1
                    syndrome_bits_total += int(h1.shape[0]) + int(h2_mat.shape[0])
            except Exception:
                failures += 1
                syndrome_bits_total += int(h1.shape[0]) + int(h2_mat.shape[0])
        total_failures += failures
        rows.append({
            "plane_id": plane,
            "p": float(p),
            "h2": float(h2(float(p))),
            "h1_syndrome_bits_per_frame": int(h1.shape[0]),
            "h2_syndrome_bits_per_frame": int(h2_mat.shape[0]),
            "average_syndrome_bits_per_frame": syndrome_bits_total / frames_per_plane,
            "fallbacks": fallbacks,
            "frames": frames_per_plane,
            "failures": failures,
            "fer": failures / frames_per_plane,
            "runtime_s": round(time.monotonic() - started, 4),
        })
    total_syndrome_bits = int(round(sum(r["average_syndrome_bits_per_frame"] for r in rows)))
    f = total_syndrome_bits / (n * h_full)
    return {
        "schema": "nbldpc_v19_binary_mlc_prototype_v1",
        "block_length": n,
        "candidate_id": candidate_id,
        "frames_per_plane": frames_per_plane,
        "per_plane": rows,
        "total_syndrome_bits_per_frame": total_syndrome_bits,
        "h_full_q1024": float(h_full),
        "measured_f": float(f),
        "total_failures": total_failures,
        "status": "all_planes_correct" if total_failures == 0 else "has_failures",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--frames-per-plane", type=int, default=50)
    ap.add_argument("--seed", type=int, default=2026081901)
    args = ap.parse_args()
    doc = run_prototype(frames_per_plane=args.frames_per_plane, seed=args.seed)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "binary_mlc_prototype.json").write_text(
        json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(doc, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
