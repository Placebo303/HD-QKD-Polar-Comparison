"""G-4b RA confirmation (packet scope): RA-structured [P1|P2-dual-diag] ensemble
(q=5) at gap 0.10 vs regular dv3 gap 0.15, N=16384, B=300, full level-A decode
with model priors + K rescue. Tests whether RA saves ~0.05 gap at equal FER.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np
from scipy import sparse

N = 16384
P = 0.2376
PM_ABS = 0.00138
GAP_RA = 0.10
B = 300
K = 400
SEED = 20267300
TAG_BITS = 64
WORKERS = 12

_W = {}


def h2(x: float) -> float:
    return -(x * math.log2(x) + (1 - x) * math.log2(1 - x))


def ra_matrix(n: int, m: int, q: int, seed: int):
    k = n - m
    rng = np.random.default_rng(seed)
    rows = []
    cols = []
    order = rng.permutation(m * ((q * k) // m + 1))[:q * k]
    for j in range(k):
        for t in range(q):
            rows.append(int(order[(j * q + t) % len(order)] % m))
            cols.append(j)
    for i in range(m):
        rows.append(i)
        cols.append(k + i)
        if i > 0:
            rows.append(i)
            cols.append(k + i - 1)
    return sparse.csr_matrix((np.ones(len(rows), dtype=np.uint8), (rows, cols)),
                             shape=(m, n))


def _worker_init(payload):
    import pickle
    from comparison_bench.src.comparison_bench.formal_ir.msd_syndrome import (  # noqa: E402
        make_bp_decoder as _mbp,
    )
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
        load_train_table,
    )
    dense, pa_l = pickle.loads(payload)
    _W["H"] = dense
    t = None
    _W["pa"] = np.asarray(pa_l)
    _W["_mbp"] = _mbp


def _decode_one(args) -> dict:
    blk, seed = args
    import numpy as _np
    from comparison_bench.src.comparison_bench.formal_ir.msd_syndrome import (  # noqa: E402
        _syndrome as _syn,
    )
    H = _W["H"]
    Hd = _np.asarray(H.toarray(), dtype=_np.uint8)
    rng = _np.random.default_rng(seed + blk)
    aks = _np.arange(1024)
    a = rng.choice(aks, size=N, p=_W["pa"])
    u = rng.random(size=N)
    e = _np.where(u < 1 - P, 0, _np.where(u < 1 - PM_ABS, 1, 1023)).astype(_np.int64)
    alice = a.astype(_np.int64)
    bob = ((a + e) % 1024).astype(_np.int64)
    xt = (alice & 1).astype(_np.uint8)
    pa_l = _W["pa"]
    lik0, likp, likm = 1 - P, P - PM_ABS, PM_ABS
    a_cand = _np.stack([(bob - 1) % 1024, bob, (bob + 1) % 1024], axis=0)
    w = _np.stack([likm * pa_l[(bob - 1) % 1024], lik0 * pa_l[bob],
                   likp * pa_l[(bob + 1) % 1024]], axis=0)
    w = w / w.sum(axis=0, keepdims=True)
    p1 = (w * ((a_cand & 1).astype(float))).sum(axis=0)
    base = (p1 > 0.5).astype(_np.uint8)
    ch = _np.minimum(p1, 1 - p1).copy()
    syn = (Hd @ xt) % 2
    delta = _np.bitwise_xor(syn, (Hd @ base) % 2)
    dec = _W["_mbp"](parity_check_matrix=H, error_channel=ch.copy(), max_iter=200)
    err = _np.asarray(dec.decode(delta.copy())).astype(_np.uint8)
    rec = _np.bitwise_xor(base, err)
    ok = bool(_np.array_equal((Hd @ rec) % 2, syn)) and bool(_np.array_equal(rec, xt))
    extra = 0
    if not ok:
        w8 = _np.log((1 - _np.maximum(ch, 1e-300)) / _np.maximum(ch, 1e-300))
        weak = _np.argsort(w8, kind="stable")[:K]
        base[weak] = xt[weak]
        extra = K
        delta2 = _np.bitwise_xor(syn, (Hd @ base) % 2)
        dec2 = _W["_mbp"](parity_check_matrix=H, error_channel=ch.copy(),
                          max_iter=200)
        rec = _np.bitwise_xor(base, np.asarray(dec2.decode(delta2.copy())).astype(np.uint8))
        ok = bool(_np.array_equal((Hd @ rec) % 2, syn)) and bool(_np.array_equal(rec, xt))
    return {"block": blk, "exact_A": ok, "L_A": int(H.shape[0]), "extra": extra}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    if not args.full:
        raise SystemExit("G-4b confirm runs only with --full")
    import concurrent.futures as cf
    import pickle
    from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
        load_train_table,
        read_p1_scalars,
        wilson_upper,
    )

    root = Path(args.output_root)
    root.mkdir(parents=True, exist_ok=True)
    t = np.asarray(load_train_table("T2-1M"), dtype=np.float64)
    pa = (t.sum(axis=1) / t.sum()).tolist()
    m = min(N - 1, max(1, int(math.ceil(N * (h2(P) + GAP_RA)))))
    H = ra_matrix(N, m, 5, 0)
    payload = pickle.dumps((H, pa))
    jl = root / "blocks_g4b.jsonl"
    if jl.exists():
        raise SystemExit(f"refusing to overwrite {jl}")
    t0 = time.perf_counter()
    with cf.ProcessPoolExecutor(max_workers=WORKERS,
                                initializer=_worker_init,
                                initargs=(payload,)) as ex:
        recs = list(ex.map(_decode_one, [(b, SEED) for b in range(B)]))
    wall = time.perf_counter() - t0
    with jl.open("w", encoding="utf-8", buffering=1) as fh:
        for r in recs:
            fh.write(json.dumps(r) + "\n")
    nb = len(recs)
    nf = sum(0 if r["exact_A"] else 1 for r in recs)
    e_l = sum(r["L_A"] + r.get("extra", 0) for r in recs) / nb
    scalars = read_p1_scalars()["T2-1M"]
    fer = nf / nb
    denom = N * scalars["H_AB"]
    kept = N * scalars["H_A"] - e_l
    f_p = (e_l + TAG_BITS + kept * fer) / denom
    row = {"ensemble": "RA-q5", "gap": GAP_RA, "N": N, "m_A": m, "blocks": nb,
           "failures": nf, "E_L_A": e_l, "FER_A": fer,
           "FER_wilson_upper95": wilson_upper(nf, nb), "f_levelA_only": f_p,
           "wall_s": wall}
    (root / "g4b_summary.json").write_text(json.dumps([row], indent=2),
                                           encoding="utf-8")
    print(json.dumps([row], indent=2))


if __name__ == "__main__":
    main()
