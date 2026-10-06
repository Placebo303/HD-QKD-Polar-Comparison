"""S-4 sibling-method row (S4_PACKET_DRAFT scope): sibling canonical recipe
(build_msd_llr_tables_shift, diff_pmf smoothing=1.0) feeding OUR MSD chain.

msd_eval proper cannot run on our data (its link_pair_streams pairs H/V-basis
polarization-curve files; ours are time-bin Type2 — porting its front-end is
out of scope; reason recorded here). Instead: sibling table builder (read-only
use, zero edits to sibling repo) + our disclose/staging/BP/rescue/f machinery
on S-1 Tier1. MSB-first layer order (their convention); matrices = S-2 Tier1
m per bit (same disclosure → isolates prior effect). Bit-mapping verified by
sign-agreement gate (>=90% else refuse). Full-symbol metric (R11).
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
    plane_conditional_entropies,
    read_p1_scalars,
    wilson_upper,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_m1primeb_mixed import (  # noqa: E402
    build_mixed_point,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_syndrome import (  # noqa: E402
    _syndrome,
    disclose_syndromes,
    make_bp_decoder,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_m2_incremental import (  # noqa: E402
    summarize_m2,
)

N = 16384
C0 = 2000
K = 400
B = 100
SEED = 20263401
TAG_BITS = 64


def build_tables(prior_counts: np.ndarray):
    import sys
    sys.path.insert(0, "D:/Code/HD-QKD_Polar_Release")
    from low_dim_opt.core import msd_conditional as mc
    tables, delta = mc.build_msd_llr_tables_shift(
        np.asarray(prior_counts, dtype=np.float64), 1024,
        smoothing=1.0, smoothing_mode="diff_pmf")
    return tables, np.asarray(delta)


def pack_prefix(rec_by_bit: dict, s: int, n: int) -> np.ndarray:
    """Pack previously decoded layers 0..s-1 (bits 9..10-s) MSB-first integer."""
    if s <= 0:
        return np.zeros(n, dtype=np.int64)
    out = np.zeros(n, dtype=np.int64)
    for t in range(s):
        out = (out << 1) | (np.asarray(rec_by_bit[9 - t], dtype=np.int64) & 1)
    return out


def verify_mapping(tables, our_model, pa: np.ndarray, pb: np.ndarray) -> float:
    """Sign agreement between sibling layer LLRs and our bit MAP (genie prefix).

    Sibling layer s <-> our bit (9-s) under MSB-first hypothesis; prefix packed
    MSB-first per prefix_from_bits. Returns agreement fraction in [0, 1].
    """
    import sys
    sys.path.insert(0, "D:/Code/HD-QKD_Polar_Release")
    from low_dim_opt.core import msd_conditional as mc
    n = 2048
    alice, bob = pa[:n].astype(np.int64), pb[:n].astype(np.int64)
    agree, tot = 0, 0
    truth_by_bit = {b: ((alice >> b) & 1).astype(np.uint8) for b in range(10)}
    for s in range(10):
        bit = 9 - s
        pre = pack_prefix(truth_by_bit, s, n)
        llr = np.asarray(mc.conditional_llr(tables, s, bob, pre)).reshape(-1)
        assert llr.shape == (n,), f"layer {s} LLR shape {llr.shape}"
        sib_base = (llr < 0).astype(np.uint8)
        truth = truth_by_bit[bit]
        agree += int((sib_base == truth).sum())
        tot += n
    return agree / tot


def run_s4(*, pairs_a: np.ndarray, pairs_b: np.ndarray, tables,
           m_list: list[int], n_blocks: int, seed: int,
           jsonl_path: Path) -> dict:
    import sys
    sys.path.insert(0, "D:/Code/HD-QKD_Polar_Release")
    from low_dim_opt.core import msd_conditional as mc
    import functools
    # per-bit matrices in LSB-bit order reused from S-2 Tier1 m (same disclosure)
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1primea_repetition import (  # noqa: E402
        spc_matrix,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_peg_code import (  # noqa: E402
        build_peg_code,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_conditional_prior import (  # noqa: E402
        build_conditional_prior_model,
    )
    mats_by_bit = {}
    for bit in range(10):
        m = m_list[bit]
        if bit <= 1:
            mats_by_bit[bit] = build_peg_code(n=N, m=m, variable_degree=3).parity_check_matrix
        else:
            from comparison_bench.src.comparison_bench.formal_ir.msd_m1primea_repetition import (  # noqa: E402
                split_groups,
            )
            mats_by_bit[bit] = spc_matrix(split_groups(N, 64 if N == 1024 else 256), N)
    bp = functools.partial(make_bp_decoder, max_iter=200)
    # disclosure needs a model object: build thin wrapper via S-2 Tier1 prior
    # table is unavailable here; disclose per-bit directly:
    n_fail = n_und = n_res = n_vw = 0
    rng = np.random.default_rng(seed)
    t0 = time.perf_counter()
    with jsonl_path.open("a", encoding="utf-8", buffering=1) as fh:
        for blk in range(n_blocks):
            pick = rng.choice(pairs_a.size, size=N, replace=True)
            alice = pairs_a[pick].astype(np.int64)
            bob = pairs_b[pick].astype(np.int64)
            recovered = {}
            passed, exacts = {}, {}
            extra, rescued = 0, False
            l_dis = 0
            for s in range(10):
                bit = 9 - s
                mat = mats_by_bit[bit]
                plane = ((alice >> bit) & 1).astype(np.uint8)
                syn = (np.asarray(mat.toarray(), dtype=np.int64) @ plane.astype(np.int64)) % 2
                syn = np.asarray(syn, dtype=np.uint8).reshape(-1)
                l_dis += int(mat.shape[0])
                pre = pack_prefix(recovered, s, N)
                llr = np.asarray(mc.conditional_llr(tables, s, bob, pre)).reshape(-1)
                assert llr.shape == (N,), f"block LLR shape {llr.shape}"
                llr = np.clip(llr, -30.0, 30.0)
                base = (llr < 0).astype(np.uint8)
                p1 = 1.0 / (1.0 + np.exp(llr))
                ch = np.minimum(p1, 1.0 - p1)
                delta = np.bitwise_xor(syn, (np.asarray(mat.toarray(), dtype=np.uint8) @ base) % 2)
                delta = np.asarray(delta, dtype=np.uint8).reshape(-1)
                plane_rec, rescued = base, False
                extra = 0
                if bit == 0:
                    dec = bp(parity_check_matrix=mat, error_channel=ch.copy())
                    err = np.asarray(dec.decode(delta.copy())).astype(np.uint8)
                    rec = np.bitwise_xor(base, err)
                    if not bool(np.array_equal((np.asarray(mat.toarray(), dtype=np.uint8) @ rec) % 2, syn)):
                        rescued, extra = True, K
                        weak = np.argsort(np.abs(llr), kind="stable")[:K]
                        base[weak] = plane[weak]
                        ch2 = np.minimum(1.0 / (1.0 + np.exp(np.clip(llr, -30, 30))), 1 - 1.0 / (1.0 + np.exp(np.clip(llr, -30, 30))))
                        ch[weak] = 0.0
                        delta2 = np.bitwise_xor(syn, (np.asarray(mat.toarray(), dtype=np.uint8) @ base) % 2)
                        dec2 = bp(parity_check_matrix=mat,
                                  error_channel=np.asarray(ch, dtype=np.float64))
                        rec = np.bitwise_xor(
                            base, np.asarray(dec2.decode(np.asarray(delta2, dtype=np.uint8).copy())).astype(np.uint8))
                    plane_rec = rec
                else:
                    from comparison_bench.src.comparison_bench.formal_ir.msd_m1primea_repetition import (  # noqa: E402
                        GroupMLDecoder,
                    )
                    # planes>=... use BP for plane1, exact-ML for SPC planes
                    from scipy import sparse as _sp
                    if bit == 1:
                        dec = bp(parity_check_matrix=mat, error_channel=ch.copy())
                        err = np.asarray(dec.decode(delta.copy())).astype(np.uint8)
                        plane_rec = np.bitwise_xor(base, err)
                    else:
                        n_g = N // (64 if N == 1024 else 256)
                        groups = [np.arange(i * (N // n_g), (i + 1) * (N // n_g),
                                            dtype=np.int64) for i in range(n_g)]
                        dec = GroupMLDecoder(groups, "spc", ch.copy(), 0)
                        plane_rec = np.bitwise_xor(base, dec.decode(delta))
                ok = bool(np.array_equal((np.asarray(mat.toarray(), dtype=np.uint8) @ plane_rec) % 2, syn))
                ex = bool(np.array_equal(plane_rec, plane))
                passed[bit], exacts[bit] = ok, ex
                if ok and not ex:
                    pass  # counted below
                recovered[bit] = plane_rec
                if not ok:
                    # remaining planes unattempted (report-only truncation)
                    for b2 in range(10):
                        if b2 not in passed:
                            passed[b2], exacts[b2] = False, False
                    break
            vw = sum(1 for b in range(10) if passed.get(b) and not exacts.get(b))
            full = all(passed.get(b, False) for b in range(10)) and all(
                exacts.get(b, False) for b in range(10))
            # reconstruct symbol for exact check
            recon = np.zeros(N, dtype=np.int64)
            for b in range(10):
                recon |= recovered.get(b, np.zeros(N, dtype=np.uint8)).astype(np.int64) << b
            exact = full and bool(np.array_equal(recon, alice))
            und = full and not exact
            n_fail += 0 if exact else 1
            n_und += 1 if und else 0
            n_vw += vw
            fh.write(json.dumps({"block": blk, "exact_ok": bool(exact),
                                 "undetected": bool(und), "valid_wrong": vw,
                                 "extra": extra if bit == 0 else 0,
                                 "rescued": rescued if bit == 0 else False}) + "\n")
    wall = time.perf_counter() - t0
    return {"failures": n_fail, "undetected": n_und, "valid_wrong_total": n_vw,
            "blocks": n_blocks, "wall_s": wall, "s_per_block": wall / n_blocks}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--proxy-root", required=True)
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    if not args.full:
        raise SystemExit("S-4 runs only with --full")
    root = Path(args.output_root)
    root.mkdir(parents=True, exist_ok=True)
    scalars = read_p1_scalars()["T2-1M"]
    z = np.load(Path(args.proxy_root) / "T2-1M_tier_pairs.npz")
    pa, pb = (np.asarray(z["a_half_a"], dtype=np.int64),
              np.asarray(z["b_half_a"], dtype=np.int64))
    pt = np.asarray(np.load(Path(args.proxy_root) / "T2-1M_tier_tables.npz")["half_b"])
    tables, _ = build_tables(pt)
    # mapping gate (genie prefix, verification only)
    from comparison_bench.src.comparison_bench.formal_ir.msd_conditional_prior import (  # noqa: E402
        build_conditional_prior_model as _bcp,
    )
    our = _bcp(pt, encoding="NATURAL", order="LSB_FIRST")
    agr = verify_mapping(tables, our, pa, pb)
    print("mapping agreement", round(agr, 4), flush=True)
    if not (0.90 <= agr <= 1.0):
        raise SystemExit(f"bit-mapping gate FAILED: {agr:.4f} outside [0.90, 1.0]")
    # SAME disclosure as S-2 Tier1 (isolates prior effect): m_0 from half_b
    # plug-in h + C0 rule, m_1 = M1_16384 fixed, planes>=2 N/256 SPC.
    h = plane_conditional_entropies(pt)
    m_list = ([min(N - 1, max(1, int(math.ceil(N * h[0] + 2000)))), 600]
              + [N // 256] * 8)
    jl = root / "blocks_s4.jsonl"
    if jl.exists():
        jl.unlink()
    r = run_s4(pairs_a=pa, pairs_b=pb, tables=tables, m_list=m_list,
               n_blocks=B, seed=SEED,
               jsonl_path=jl)
    e_l = sum(m_list) + K * sum(
        json.loads(l)["extra"] > 0 for l in open(jl, encoding="utf-8")) / B
    fer = r["failures"] / B
    denom = N * scalars["H_AB"]
    kept = N * scalars["H_A"] - e_l
    f_p = (e_l + TAG_BITS + kept * fer) / denom
    row = {**r, "E_L": e_l, "FER_exact": fer,
           "FER_wilson_upper95": wilson_upper(r["failures"], B),
           "f_expected": f_p, "source": "T2-1M", "N": N,
           "backend": "sibling-tables-msd-chain", "mapping_agreement": agr}
    (root / "s4_summary.json").write_text(json.dumps([row], indent=2), encoding="utf-8")
    print(json.dumps([row], indent=2))


if __name__ == "__main__":
    main()
