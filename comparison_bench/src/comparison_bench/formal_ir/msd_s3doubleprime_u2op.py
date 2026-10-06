"""S-3'' u2 operating reselection (packet scope): u2 base-m curve on Tier1,
combined analytically with S-3' measured u1|u2-exact FER.

Full-symbol FER(m) = 1 - (1 - FER_u2(m)) * (1 - FER_u1_given_u2ok):
valid because u1 planes condition on recovered-u2 prefix, and S-3' measures
u1 outcomes exactly on u2-exact blocks. E[L](m) likewise composed.
Pooled x12 (M4 pattern). R10/R11; full-symbol metric throughout.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic import (  # noqa: E402
    read_p1_scalars,
    wilson_upper,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_s1_proxy import (  # noqa: E402
    load_tier_pairs,
)
from comparison_bench.src.comparison_bench.formal_ir.msd_m4_nb_marginal import (  # noqa: E402
    derive_bundle,
)
from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
    v80_s2c_campaign as _s2c,
)
from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
    nonbinary_v10_peg as _peg,
)
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import (  # noqa: E402
    GF2mField as _GF,
)
from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
    nonbinary_v10_fftqspa as _qq,
)
from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
    nonbinary_v28 as _v28,
)
from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
    v80_b2f_campaign as _b2f,
)
from comparison_bench.src.comparison_bench.cli import (  # noqa: E402
    p1_stage1_runner as _p1,
)

N = 1024
M_LIST = (184, 192, 200)
RESCUE_TO = 208
B = 100
SEED = 20264800
TAG_BITS = 64
WORKERS = 12
# S-3' measured u1|u2-exact inputs (filled after S-3' lands; provisional None)
U1_GIVEN_U2_FER = None
U1_MEAN_DISCLOSURE = None

_W = {}


def _worker_init():
    root = Path("workspace/s1_proxy/s1_20261006")
    pa, pb = load_tier_pairs(root, "T2-1M", "half_a")
    pt = np.asarray(np.load(root / "T2-1M_tier_tables.npz")["half_b"])
    _W["bundle"] = _s2c.bind_empirical_bundle(derive_bundle(pt))
    pinned = _p1.construct_and_pin("P1S1-R1", _p1.PRODUCTION_CONSTRUCT["P1S1-R1"],
                                   _p1.production_rank_fn)
    field = _GF.create(32)
    _W["field"] = field
    _W["full_dense"] = _peg.sparse_to_dense(pinned["full"]["triples"], N, 208, field)
    _W["base_triples_full"] = pinned["base"]["triples"]
    _W["pa"], _W["pb"] = pa, pb
    _W["_peg"], _W["_qq"], _W["_v28"], _W["_b2f"], _W["_s2c"] = _peg, _qq, _v28, _b2f, _s2c


def _decode_one(args) -> dict:
    m_base, blk, seed = args
    pa, pb = _W["pa"], _W["pb"]
    rng = np.random.default_rng(seed + blk * 131 + m_base)
    pick = rng.choice(pa.size, size=N, replace=True)
    alice = pa[pick].astype(np.int64)
    bob = pb[pick].astype(np.int64)
    x = alice & 31
    y = bob & 31
    base_triples = [t for t in _W["base_triples_full"] if int(t[0]) < m_base]
    dense_b = _W["_peg"].sparse_to_dense(base_triples, N, m_base, _W["field"])
    bundle, field = _W["bundle"], _W["field"]
    _qq, _v28, _b2f, _s2c = _W["_qq"], _W["_v28"], _W["_b2f"], _W["_s2c"]
    prior = _s2c.center_rows_prior(_b2f.marginal_prior_l2(bundle, bob), y)
    sxx = _qq.syndrome_of(field, dense_b, x.tolist())
    t = time.perf_counter()
    res = _v28.decode_error_domain_posterior(field, y.tolist(), dense_b, sxx,
                                             prior, 300)
    wall = time.perf_counter() - t
    xh = res.get("x_hat")
    exact = xh is not None and bool(np.array_equal(np.asarray(xh), x))
    rok = bool(res.get("reconstruction_ok", False))
    rescued, l_rows = False, m_base
    if not exact:
        sxx2 = _qq.syndrome_of(field, _W["full_dense"], x.tolist())
        res2 = _v28.decode_error_domain_posterior(
            field, y.tolist(), _W["full_dense"], sxx2, prior, 300)
        xh2 = res2.get("x_hat")
        if xh2 is not None and bool(np.array_equal(np.asarray(xh2), x)):
            exact, res, rok = True, res2, bool(res2.get("reconstruction_ok", False))
        else:
            res = res2
            rok = bool(res2.get("reconstruction_ok", False))
        rescued, l_rows = True, RESCUE_TO
    return {"m_base": m_base, "block": blk, "exact_u2": bool(exact),
            "undetected": bool((not exact) and rok), "rescued": rescued,
            "L_EC": 5 * l_rows, "wall_s": wall}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    if not args.full:
        raise SystemExit("S-3'' runs only with --full")
    import concurrent.futures as cf

    root = Path(args.output_root)
    root.mkdir(parents=True, exist_ok=True)
    jl = root / "blocks_s3pp.jsonl"
    if jl.exists():
        jl.unlink()
    rows = []
    with cf.ProcessPoolExecutor(max_workers=WORKERS,
                                initializer=_worker_init) as ex:
        for m_base in M_LIST:
            t0 = time.perf_counter()
            recs = list(ex.map(_decode_one,
                               [(m_base, b, SEED) for b in range(B)]))
            wall = time.perf_counter() - t0
            with jl.open("a", encoding="utf-8", buffering=1) as fh:
                for r in recs:
                    fh.write(json.dumps(r) + "\n")
            nf = sum(0 if r["exact_u2"] else 1 for r in recs)
            nu = sum(1 for r in recs if r["undetected"])
            nr = sum(1 for r in recs if r["rescued"])
            rows.append({"m_base": m_base, "blocks": B, "u2_failures": nf,
                         "u2_undetected": nu, "n_rescue": nr,
                         "u2_fer": nf / B,
                         "u2_fer_upper95": wilson_upper(nf, B),
                         "wall_s": wall})
            print(f"m={m_base}: u2fail {nf}/{B}", flush=True)
    (root / "s3pp_u2curve.json").write_text(json.dumps(rows, indent=2),
                                            encoding="utf-8")
    print("NOTE: full-symbol composition needs S-3' u1|u2 inputs; see packet.")


if __name__ == "__main__":
    main()
