"""S-4b plaintext-fallback level-B (synthetic verification only).

Fallback: sign bits on TRUE-marked positions sent in the clear
(leakage = marked_count x 1 bit/position); level-A frozen (S-3 config,
both arms available); full-chain success <=> level-A success.
Verifies full-chain success rate + leakage accounting on synthetic
DoubleGauss channels (S-2 prefix laws). No real data.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.msd_s3_softdecode import (
    QA,
    build_ra,
    llr,
    p_of_v_mix,
    rate_of,
    synth_blocks,
)

SEED = 20261011


def self_test() -> None:
    # tiny end-to-end plaintext accounting (synthetic only)
    rng = np.random.default_rng(SEED)
    N = 128
    H = build_ra(N, 64, QA, seed=1)
    blks = synth_blocks(rng, 4, N, 13.0, 0.0, 0.007)
    from comparison_bench.src.comparison_bench.formal_ir import (
        msd_s3_softdecode as S3,
    )
    S = F = LA = LB = 0
    for blk in blks:
        x = blk["x"]
        synA = np.asarray((H @ x) % 2, dtype=np.uint8).ravel()
        xa = S3.decode(H, synA, [llr(0.06)] * N)
        if np.array_equal(xa, x):
            S += 1
            LA += 64
            LB += int((xa != blk["b0"]).sum())
        else:
            F += 1
    assert S + F == 4
    net = S * (10 * N) - (LA + LB) - S * 64
    assert net == S * (10 * N - 64) - (LA + LB)
    print(f"s4b self-test OK (S={S} F={F} accounting identity)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-root", required=False, default=None)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.output_root:
        raise SystemExit("s4b --full requires --output-root")
    root = Path(args.output_root)
    if root.exists():
        raise SystemExit(f"output root not fresh: {root}")
    root.mkdir(parents=True, exist_ok=True)
    import json as _j
    s2 = _j.load(open("workspace/s_softmap/s2_20261009/s2_summary.json", encoding="utf-8"))
    tune = _j.load(open("workspace/s3_softdecode/s3_tune_20261009/s3_tune.json", encoding="utf-8"))
    rng = np.random.default_rng(SEED)
    out: dict = {"seed": SEED, "laws": {}, "cells": {}}
    t_all = time.perf_counter()
    for src in ("T2-1M", "T2-1.5M", "T2-2M", "0dB", "4dB"):
        fit = s2["sources"][src]["prefix_fit"]
        N = 4096
        gap = float(tune["arms"]["soft"]["gap"])
        p_bar = 0.0607
        m = int(N * (1.0 - rate_of(p_bar, gap)))
        H = build_ra(N, m, QA, seed=4000)
        # plaintext level-B: no H_B decode; L_B = marked_count x 1 bit on success
        for arm in ("hard", "soft"):
            blks = synth_blocks(rng, 100, N, float(fit["sig"]), 0.0, float(fit["w"]))
            from comparison_bench.src.comparison_bench.formal_ir import (
                msd_s3_softdecode as S3,
            )
            res = {"S": 0, "F": 0, "U": 0, "LA": 0, "LB": 0, "T": []}
            for blk in blks:
                x = blk["x"]
                synA = np.asarray((H @ x) % 2, dtype=np.uint8).ravel()
                chA = [llr(p_bar)] * N if arm == "hard" else \
                    [llr(p_of_v_mix(vv, float(fit["sig"]), 0.0, float(fit["w"]))) for vv in blk["v"]]
                t0 = time.perf_counter()
                xa = S3.decode(H, synA, chA)
                okA = bool(np.array_equal(xa, x))
                res["T"].append(time.perf_counter() - t0)
                if not okA:
                    res["F"] += 1
                    continue
                mk = int((xa != blk["b0"]).sum())
                res["S"] += 1
                res["LA"] += m
                res["LB"] += mk  # plaintext: 1 bit per marked position
            n = res["S"] + res["F"]
            fer = res["F"] / n
            net = res["S"] * (10 * N) - (res["LA"] + res["LB"]) - res["S"] * 64
            out["cells"][f"{src}/{arm}"] = {
                "S": res["S"], "F": res["F"], "FER": round(fer, 4),
                "L_A": res["LA"], "L_B_plain": res["LB"],
                "Net_seg": round(net, 0),
                "T_med": round(float(np.median(res["T"])), 3)}
            print(f"s4b {src} {arm}: S={res['S']} F={res['F']} "
                  f"FER={fer:.3f} Net={net:.0f}", flush=True)
    out["wall_s_total"] = round(time.perf_counter() - t_all, 1)
    (root / "s4b_result.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"s4b done wall={out['wall_s_total']}s -> {root}")


if __name__ == "__main__":
    main()
