"""V80 S2c lambda diagnostic study (EXPLORE observations only; NO gate).

O4+O2 probe (S2_FALLBACK_OPTIONS_20260920.md): de-noise the QSC-vs-empirical
lambda ranking reversal at larger N before any O1/O2 route choice. Read-only
reuse of the frozen S2c executor (v80_s2c_campaign: bind_empirical_bundle,
empirical_triple_sampler, decode_frame_empirical, construct_arm semantics;
m sourced per arm from s2.N_FRAME/s2.M2). Frozen modules are NEVER edited.

Arms (one construction each, seed 2026092001, trials 20):
  A47 = lam{2:1} m2=47 | B47 = lam{2:0.5,3:0.5} m2=47
  C47 = lam{3:1} m2=47 | A50 = lam{2:1} m2=50 (O2 probe; built here with the
  same primitives construct_arm uses: make_rho + peg_construct + reconcile
  inside peg_construct; m=50 -> rate 1-50/256=0.8047,
  f_super=(4x52x5+64)/852.544=1.2950 with m_total=52).
Frames: 64/arm PAIRED (seed block 2026097501+idx, idx 0..63; rg-absence clean
2026-09-20 across src/tests/docs/openspec/.workbuddy/.codebuddy/scripts;
2026098xxx/20260990xx/2026096xxx zones avoided). Decode: identical
empirical-channel semantics (2M gamma/p_b; y=b&31; pi(e)=g2[y^e|b,u1] genie;
decode_error_domain_posterior; max_iter=300; streak=3). NO gate, NO
early-stop. Raw JSON -> /tmp/opencode/s2c_lambda_study.json only.
"""
from __future__ import annotations

import json
import math
import time

import numpy as np

from . import nonbinary_v10_fftqspa as fftqspa
from . import nonbinary_v10_peg as peg
from . import nonbinary_v26_mcde as _mcde  # noqa: F401 (read-only rho reuse)
from . import nonbinary_v28 as v28
from . import v80_s2_peg as s2
from . import v80_s2c_campaign as s2c
from .nonbinary_field import GF2mField

FRAME_BASE = 2026097501  # fresh paired block; idx 0..63
N_FRAMES = 64
CONSTRUCT_SEED = s2c.S2C_CONSTRUCT_SEED  # 2026092001
MAX_TRIALS = s2c.S2C_MAX_TRIALS  # 20
M50 = 50  # O2 probe rows (frozen construct_arm cannot take m; built here)
OUT = "/tmp/opencode/s2c_lambda_study.json"
ARM47 = {"A47": "L-A", "B47": "L-B", "C47": "L-C"}  # study -> frozen S2c arm


def wilson(k: int, n: int, z: float = 1.96) -> list[float]:
    """Wilson 95% score interval for k/n (observation-level error bar)."""
    if n <= 0:
        return [0.0, 1.0]
    p = k / n
    d = 1.0 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [max(0.0, (c - h) / d), min(1.0, (c + h) / d)]


def construct_a50(seed: int = CONSTRUCT_SEED,
                  trials: int = MAX_TRIALS) -> dict:
    """A50 via the SAME primitives as frozen construct_arm (no frozen edit):
    make_rho at rate 1-50/256 + peg_construct (reconcile inside) + family."""
    field = GF2mField.create(s2.Q)
    lam = {2: 1.0}
    rho = _mcde.make_rho(1.0 - M50 / s2.N_FRAME, lam)
    res = peg.peg_construct(s2.N_FRAME, M50, lam, rho, int(seed),
                            max_trials=int(trials), field=field)
    res["family"] = "peg-irregular"
    s2.refuse_three_shift_cyclic({"family": res["family"]})
    res["lambda_edge"] = lam
    res["rho_edge"] = {int(k): float(v) for k, v in rho.items()}
    return res


def decode_a50(construction: dict, seed: int, bundle: dict) -> dict:
    """A50 frame decode: byte-identical channel semantics to frozen
    decode_frame_empirical (same stream seed -> same paired triple), with
    dense dims (256, 50). max_iter=300, streak default (3)."""
    field = GF2mField.create(s2.Q)
    dense = peg.sparse_to_dense(construction["triples"], s2.N_FRAME, M50,
                                field)
    rng = np.random.default_rng(s2c.stream_seed(int(seed)))
    b, u1, u2 = s2c.empirical_triple_sampler(bundle, s2.N_FRAME, rng)
    x = np.asarray(u2, dtype=np.int64)
    y = np.asarray(b & 31, dtype=np.int64)
    s_x = fftqspa.syndrome_of(field, dense, x.tolist())
    rows = s2c.posterior_rows_l2(bundle, b, u1)
    prior = s2c.center_rows_prior(rows, y)
    r = v28.decode_error_domain_posterior(field, y.tolist(), dense, s_x,
                                          prior, s2c.MAX_ITER)
    xh = r.get("x_hat")
    return {"ok": bool(np.array_equal(np.asarray(xh), x))
            if xh is not None else False,
            "iterations": r.get("iterations"), "status": r.get("status")}


def summarize(iters: list, oks: list[bool]) -> dict:
    """Frame stats + group-of-4 pass count (reference only, NOT a gate)."""
    n = len(oks)
    s = sorted(i for i in iters if isinstance(i, int))
    med = (s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2) if s else None
    groups = [all(oks[g * 4:(g + 1) * 4]) for g in range(n // 4)]
    return {"n_ok": sum(1 for o in oks if o), "n": n,
            "wilson95": wilson(sum(1 for o in oks if o), n),
            "groups_pass": sum(1 for g in groups if g),
            "n_groups": len(groups),
            "iter_min": min(s) if s else None, "iter_med": med,
            "iter_max": max(s) if s else None,
            "n_iter300": sum(1 for i in s if i >= 300)}


def main() -> int:
    t0 = time.monotonic()
    bundle = s2c.bind_empirical_bundle(s2c.GAMMA_DEFAULT, s2c.SOURCE_DEFAULT)
    constructions = {a: s2c.construct_arm(s2c_arm, CONSTRUCT_SEED,
                                          MAX_TRIALS)
                     for a, s2c_arm in ARM47.items()}
    constructions["A50"] = construct_a50()
    seeds = [FRAME_BASE + i for i in range(N_FRAMES)]  # paired across arms
    per_arm: dict[str, dict] = {}
    for arm, con in constructions.items():
        m = M50 if arm == "A50" else s2.M2
        oks, iters, st = [], [], []
        for sd in seeds:  # no gate, no early-stop: all 64 frames
            out = (decode_a50(con, sd, bundle) if arm == "A50"
                   else s2c.decode_frame_empirical(con, sd, bundle))
            ok = bool(out.get("exact_match") if arm != "A50"
                      else out.get("ok"))
            oks.append(ok)
            iters.append(out.get("iterations"))
            st.append(out.get("status"))
        per_arm[arm] = {"m2": m, **summarize(iters, oks),
                        "construct": {
                            "four_cycles": con.get("four_cycles"),
                            "min_girth": con.get("min_girth"),
                            "rank": con.get("rank")},
                        "seeds": seeds, "ok": oks, "iters": iters,
                        "status": st}
    discord = {}
    arms = list(per_arm)
    for i in range(len(arms)):
        for j in range(i + 1, len(arms)):
            a, b = per_arm[arms[i]]["ok"], per_arm[arms[j]]["ok"]
            discord[f"{arms[i]}-vs-{arms[j]}"] = {
                "first_only": sum(1 for x, y in zip(a, b) if x and not y),
                "second_only": sum(1 for x, y in zip(a, b) if y and not x),
                "both_ok": sum(1 for x, y in zip(a, b) if x and y)}
    rec = {"track": "EXPLORE diagnostic (observations only; no gate verdict)",
           "frame_base": FRAME_BASE, "n_frames": N_FRAMES, "paired": True,
           "construct_seed": CONSTRUCT_SEED, "max_trials": MAX_TRIALS,
           "decoder": "decode_error_domain_posterior max_iter=300 streak=3",
           "channel": "empirical 2M triple, genie-u1 (S2c semantics)",
           "f_super_A50_info": (4 * (M50 + 2) * 5 + 64) / 852.544,
           "arms": {a: {k: v for k, v in d.items()
                        if k not in ("seeds", "ok", "iters", "status")}
                    for a, d in per_arm.items()},
           "discordant": discord,
           "frames": {a: {"seeds": d["seeds"], "ok": d["ok"],
                           "iters": d["iters"], "status": d["status"]}
                      for a, d in per_arm.items()},
           "wall_s": time.monotonic() - t0}
    with open(OUT, "w") as fh:
        json.dump(rec, fh, indent=1, sort_keys=True, default=str)
    for a, d in per_arm.items():
        print(f"{a} m={d['m2']}: {d['n_ok']}/{d['n']} "
              f"CI[{d['wilson95'][0]:.3f},{d['wilson95'][1]:.3f}] "
              f"grp {d['groups_pass']}/{d['n_groups']} "
              f"iter {d['iter_min']}/{d['iter_med']}/{d['iter_max']} "
              f"n300={d['n_iter300']} fc={d['construct']['four_cycles']} "
              f"g={d['construct']['min_girth']} r={d['construct']['rank']}")
    print(f"discordant={json.dumps(discord, sort_keys=True)} "
          f"wall={rec['wall_s']:.1f}s -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
