"""S-4d rerun (S4D_PREEXECUTE.md, DECIDE real decode, authorized 2026-10-09).

Level-A frozen S-3 config (shared computation per (source, L-A arm));
level-B two arms: plaintext fallback (S-4b verified) + fixed coded arm with
fine-conditioned priors (prefix-fitted S-curves, test excluded).
Gate verdict selects arms (FAIL -> plaintext + hard control only).
Labels: all results are retests on used data (S-3 sources). Main metric:
leakage bits + net key; f per S-1 denominators, reference only.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np
from scipy import sparse
import scipy.stats as st

from comparison_bench.src.comparison_bench.formal_ir.msd_s3_softdecode import (
    D,
    K2,
    NPROC_OF_N,
    QA,
    TAG,
    HA_OP,
    build_ra,
    decode,
    llr,
    mcnemar,
    p_of_v_mix,
    rate_of,
    real_blocks,
    source_p_bar,
)

SPAN_PS = 204800
BW = 200
N = 4096
GAP = 0.18
N_SUB = 8
RETEST = "retest-on-used-data"


def sub_of(v: np.ndarray) -> np.ndarray:
    return np.minimum((v // (BW // N_SUB)).astype(int), N_SUB - 1)


def block_2B(H_A, H_Bf, H_R, blk: dict, ctx: dict, arm_LA: str) -> dict:
    """One block, both level-B arms. Returns per-arm outcomes + shared level-A."""
    x = blk["x"]
    t0 = time.perf_counter()
    synA = np.asarray((H_A @ x) % 2, dtype=np.uint8).ravel()
    if arm_LA == "hard":
        chA = [llr(ctx["p_bar"])] * len(x)
    else:
        chA = [llr(p_of_v_mix(vv, ctx["sig"], 0.0, ctx["w"])) for vv in blk["v"]]
    xa = decode(H_A, synA, chA)
    okA = bool(np.array_equal(xa, x) and np.array_equal(((H_A @ xa) % 2).ravel(), synA))
    out = {"okA": okA, "T_A": time.perf_counter() - t0, "arms": {},
           "mA": H_A.shape[0], "mk": 0}
    if not okA:
        out["arms"] = {"plain": {"ok": False}, "fixed": {"ok": False}}
        out["T_tot"] = time.perf_counter() - t0
        return out
    # MARKED-SET FIX: xa IS the difference (x=a0^b0, the decoder output), so
    # marked (e!=0) is (xa==1) — NOT (xa!=b0). The latter inflates the set ~8x
    # on real data (identical iff b0=0, hence invisible on synthetic) and feeds
    # an underdetermined system to level-B: the S-3 100%-fail mechanism.
    marked = (xa == 1)
    mk = int(marked.sum())
    mA = H_A.shape[0]
    # XA-AS-A0 FIX: xa is the DIFFERENCE (x=a0^b0, the decoder output), not a0.
    # Recover Alice LSB as a0hat = xa^b0 (exact on okA blocks). Using xa as a0
    # flips ~50% of level-B prior signs on real data (invisible on synthetic
    # with b0=0) — the S-3 100%-fail mechanism. Same fix in recon below.
    a0hat = (xa ^ blk["b0"]).astype(np.uint8)
    # arm P: plaintext (true y on decoded-marked positions; exact checked honestly,
    # so e=±2-type unmarked-but-wrong positions count as failures, not successes)
    y_true = blk["a1"][marked]
    ahat_p = blk["b"].copy()
    sgn_p = (y_true ^ blk["b1"][marked] ^ a0hat[marked]).astype(bool)
    ahat_p[marked] = np.where(sgn_p, (blk["b"][marked] + 1) % D,
                              (blk["b"][marked] - 1) % D)
    exact_p = bool(np.array_equal(ahat_p, blk["a"]))
    out["arms"]["plain"] = {"ok": True, "L_B": mk, "L_R": 0, "exact": exact_p}
    # arm C: fine-conditioned coded
    mB = H_Bf.shape[0]
    y = blk["a1"][marked]
    if mk == 0:
        out["arms"]["fixed"] = {"ok": True, "L_B": mB, "L_R": 0}
    else:
        synB = np.asarray((H_Bf[:, marked] @ y) % 2, dtype=np.uint8).ravel()
        curve = np.array(ctx["curve"])
        pv = curve[sub_of(blk["v"][marked].astype(np.int64))]
        # P(y=1|marked,v,b1,a0): y=b1^a0^sgn -> sign conditions on (b1^a0hat):
        # b1^a0==0: P(y=1)=c -> +LLR; ==1: P(y=1)=1-c -> -LLR.
        L = np.array([math.log((1.0 - p) / p) for p in pv])
        sgn_side = (blk["b1"][marked] ^ a0hat[marked]).astype(bool)
        chB = np.where(sgn_side, -L, L)
        Hsub = H_Bf[:, marked]
        yhat = decode(Hsub, synB, [float(c) for c in chB])
        okB = bool(np.array_equal(yhat, y))
        lb, r = mB, 0
        if not okB:
            synR = np.asarray((H_R[:, marked] @ y) % 2, dtype=np.uint8).ravel()
            Hsub2 = sparse.vstack([Hsub, H_R[:, marked]]).tocsr()
            yhat = decode(Hsub2, np.concatenate([synB, synR]),
                          [float(c) for c in chB])
            okB = bool(np.array_equal(yhat, y))
            r = K2
            lb += K2
        out["arms"]["fixed"] = {"ok": okB, "L_B": lb, "L_R": r,
                                "yhat_ok": okB}
        if okB:
            ahat = blk["b"].copy()
            sgn = (yhat ^ blk["b1"][marked] ^ a0hat[marked]).astype(bool)
            ahat[marked] = np.where(sgn, (blk["b"][marked] + 1) % D,
                                    (blk["b"][marked] - 1) % D)
            out["arms"]["fixed"]["exact"] = bool(np.array_equal(ahat, blk["a"]))
    out["T_tot"] = time.perf_counter() - t0
    out["mA"] = mA
    out["mk"] = mk
    return out


def aggregate(items: list[dict], arm_LA: str, arm_LB: str, Nn: int,
              H_bin: float, H_fine: float) -> dict:
    S = F = U = 0
    LA = LB = RS = 0
    T = []
    for it in items:
        T.append(it["T_tot"])
        if not it["okA"]:
            F += 1
            continue
        b = it["arms"][arm_LB]
        if not b["ok"]:
            F += 1
            continue
        if not b.get("exact", False):
            U += 1
            continue
        S += 1
        LA += it["mA"]
        LB += b["L_B"]
        RS += b["L_R"]
    n = S + F + U
    fer = (F + U) / n
    fails = F + U
    lo = 0.0 if fails == 0 else float(st.beta.ppf(0.025, fails, n - fails + 1))
    hi = 1.0 if fails == n else float(st.beta.ppf(0.975, fails + 1, n - fails))
    net = S * (HA_OP * Nn) - (LA + LB) - S * TAG
    L = LA + LB + RS
    H = H_bin if arm_LA == "hard" else H_fine
    return {"S": S, "F": F, "U": U, "FER": round(fer, 4),
            "FER_CP95": [round(lo, 4), round(hi, 4)],
            "L_A": LA, "L_B": LB, "L_rescue": RS, "L_tot": L,
            "Net_seg": round(net, 0),
            "f_ref": round(L / (n * Nn * H), 4) if H and n else None,
            "T_med": round(float(np.median(T)), 3),
            "T_tot": round(float(sum(T)), 1)}


def self_test() -> None:
    # tiny dual-arm accounting (synthetic only)
    rng = np.random.default_rng(20261012)
    from comparison_bench.src.comparison_bench.formal_ir.msd_s3_softdecode import (
        synth_blocks,
    )
    Nn = 256
    H = build_ra(Nn, int(Nn * 0.4), QA, seed=7)
    HB = build_ra(Nn, int(Nn * 0.15), QA, seed=8)
    HR = build_ra(Nn, 8, QA, seed=9)
    blks = synth_blocks(rng, 6, Nn, 13.0, 0.0, 0.007)
    curve = [0.02, 0.05, 0.2, 0.5, 0.8, 0.95, 0.98, 0.98]
    ctx = {"p_bar": 0.05, "sig": 13.0, "w": 0.007, "curve": curve}
    for blk in blks:
        r = block_2B(H, HB, HR, blk, ctx, "soft")
        assert r["okA"] in (True, False) and set(r["arms"]) == {"plain", "fixed"}
    print("s4d-rerun self-test OK (dual-arm block)")


def load_ctx(src: str, gate_root: Path) -> dict:
    import json as _j
    s2 = _j.load(open("workspace/s_softmap/s2_20261009/s2_summary.json", encoding="utf-8"))
    curves = _j.load(open(gate_root / "s4d_curves.json", encoding="utf-8"))
    fit = s2["sources"][src]["prefix_fit"]
    c200 = s2["sources"][src]["cells"]["200"]
    return {"p_bar": source_p_bar(src), "sig": float(fit["sig"]),
            "w": float(fit["w"]), "curve": curves[src]["curve"],
            "H_bin": c200["H_hard_cal"], "H_fine": c200["H_soft_cal"]}


def do_smoke(root: Path, gate_root: Path) -> dict:
    ctx = load_ctx("T2-1M", gate_root)
    blks = real_blocks("T2-1M", N, {"sig": 1.0, "mu": 0.0, "w": 0.0})[:2]
    m = int(N * (1.0 - rate_of(ctx["p_bar"], GAP)))
    H = build_ra(N, m, QA, seed=5000)
    HB = build_ra(N, int(N * 0.10), QA, seed=5001)
    HR = build_ra(N, K2, QA, seed=5002)
    out = {}
    for la in ("hard", "soft"):
        for lb in ("plain", "fixed"):
            outs = [block_2B(H, HB, HR, b, ctx, la) for b in blks]
            out[f"{la}/{lb}"] = {"n": len(outs),
                                 "T_tot": round(sum(o["T_tot"] for o in outs), 1)}
            print(f"smoke {la}/{lb}: T={out[f'{la}/{lb}']['T_tot']}s", flush=True)
    (root / "s4d_smoke.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


def do_full(root: Path, gate_root: Path) -> dict:
    import json as _j
    gate = _j.load(open(gate_root / "s4d_gate.json", encoding="utf-8"))
    arms_LB = ["plain", "fixed"] if gate["gate"]["pass"] else ["plain"]
    print(f"full LB arms: {arms_LB} (gate pass={gate['gate']['pass']})", flush=True)
    t_start = time.perf_counter()
    BUDGET_CAP = 14400.0
    summary: dict = {"track": "DECIDE-real-decode", "label": RETEST,
                     "gate": gate["gate"], "LB_arms": arms_LB,
                     "cells": {}, "mcnemar": {}}
    jlf = (root / "s4d_blocks.jsonl").open("w", encoding="utf-8")
    s2 = _j.load(open("workspace/s_softmap/s2_20261009/s2_summary.json", encoding="utf-8"))
    for src in ("T2-1M", "T2-1.5M", "T2-2M", "0dB", "4dB"):
        if time.perf_counter() - t_start > BUDGET_CAP:
            summary["cells"][src] = {"stopped": "budget-cap"}
            print(f"{src}: STOPPED budget-cap", flush=True)
            continue
        ctx = load_ctx(src, gate_root)
        c200 = s2["sources"][src]["cells"]["200"]
        ctx["H_bin"], ctx["H_fine"] = c200["H_hard_cal"], c200["H_soft_cal"]
        law = {"sig": 1.0, "mu": 0.0, "w": 0.0}
        blks = real_blocks(src, N, law)  # deterministic same blocks as S-3
        m = int(N * (1.0 - rate_of(ctx["p_bar"], GAP)))
        H = build_ra(N, m, QA, seed=5000)
        HB = build_ra(N, int(N * 0.10), QA, seed=5001)
        HR = build_ra(N, K2, QA, seed=5002)
        per_la: dict = {}
        for la in ("hard", "soft"):
            items = [block_2B(H, HB, HR, b, ctx, la) for b in blks]
            per_la[la] = items
            for bi, it in enumerate(items):
                jlf.write(_j.dumps({"cell": f"{src}/{la}", "block": bi,
                                    "okA": it["okA"],
                                    "plain_ok": it["arms"]["plain"]["ok"],
                                    "fixed_ok": it["arms"].get("fixed", {}).get("ok"),
                                    "mk": it.get("mk", 0)}) + "\n")
        for lb in arms_LB:
            for la in ("hard", "soft"):
                cell = aggregate(per_la[la], la, lb, N, ctx["H_bin"], ctx["H_fine"])
                cell.update({"source": src, "L-A": la, "L-B": lb, "N": N,
                             "label": RETEST})
                summary["cells"][f"{src}/{la}/{lb}"] = cell
                print(f"full {src} {la}/{lb}: S={cell['S']} F={cell['F']} U={cell['U']} "
                      f"FER={cell['FER']}{cell['FER_CP95']} Net={cell['Net_seg']} "
                      f"f_ref={cell['f_ref']}", flush=True)
        for lb in arms_LB:
            ah = [o["okA"] and o["arms"][lb]["ok"] and o["arms"][lb].get("exact", False)
                  for o in per_la["hard"]]
            as_ = [o["okA"] and o["arms"][lb]["ok"] and o["arms"][lb].get("exact", False)
                   for o in per_la["soft"]]
            so = sum(1 for h, s in zip(ah, as_) if (not h) and s)
            ho = sum(1 for h, s in zip(ah, as_) if h and (not s))
            summary["mcnemar"][f"{src}/{lb}"] = {"soft_only": so, "hard_only": ho,
                                                 "p": round(mcnemar(so, ho), 6)}
            print(f"mcnemar {src}/{lb}: {so}/{ho} p={summary['mcnemar'][f'{src}/{lb}']['p']}",
                  flush=True)
        (root / "s4d_cells.json").write_text(_j.dumps(summary, indent=1), encoding="utf-8")
        jlf.flush()
    summary["wall_s_total"] = round(time.perf_counter() - t_start, 1)
    (root / "s4d_cells.json").write_text(_j.dumps(summary, indent=1), encoding="utf-8")
    jlf.close()
    print(f"full done wall={summary['wall_s_total']}s -> {root}")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--output-root", required=False, default=None)
    ap.add_argument("--gate-root", required=False, default=None)
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.output_root:
        raise SystemExit("s4d-rerun requires --output-root")
    root = Path(args.output_root)
    if root.exists():
        raise SystemExit(f"output root not fresh: {root}")
    root.mkdir(parents=True, exist_ok=True)
    if args.smoke or args.full:
        if not args.gate_root:
            raise SystemExit("smoke/full require --gate-root (frozen curves+verdict)")
        gate_root = Path(args.gate_root)
        if not (gate_root / "s4d_curves.json").exists():
            raise SystemExit("gate curves missing (run fixverify --gate first)")
    if args.smoke:
        do_smoke(root, gate_root)
    elif args.full:
        do_full(root, gate_root)
    else:
        raise SystemExit("needs one of --smoke/--full")


if __name__ == "__main__":
    main()
