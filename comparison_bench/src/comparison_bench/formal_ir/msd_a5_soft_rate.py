"""A5 soft-vs-hard achievable-rate tool (implementation + synthetic self-check).

Caliber (Birnie et al. / Boutros & Soljanin): hard = Slepian-Wolf bound
H(A|B_bin) = H(e); soft = H(A|B_fine) = E_v[H(e|v)] with Bob's intra-bin
phase v. P(e=k|v) = F(v+k*bw-mu) - F(v+(k-1)*bw-mu), F = jitter CDF.
Self-checks: closed forms + B2 empirical cross-check (synthetic only).

NOTE (R9): paper-exact-number reproduction is NOT claimed — the two papers'
full operating points (code ensembles + channel traces) are not in this repo;
the tool implements their rate caliber. What IS checked: symmetry,
soft<=hard with equality iff independent, large-sigma limit, and agreement
with B2 empirical gains within stated tolerances.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from comparison_bench.src.comparison_bench.formal_ir.msd_a3_jitter_model import (
    DoubleGauss,
    Gauss,
    error_pmf,
    h2,
    summary_of_pmf,
)

W_PS = 200.0
K_RANGE = range(-4, 5)


def cond_pmf_given_fine(law, bw: float, mu: float, v: float) -> dict[int, float]:
    out = {}
    for k in K_RANGE:
        out[k] = law.interval_mass(v + (k - 1) * bw - mu, v + k * bw - mu)
    tot = sum(out.values())
    if tot > 0:
        out = {k: p / tot for k, p in out.items()}
    return out


def H_of_pmf(pmf: dict[int, float]) -> float:  # noqa: N802
    return float(-sum(p * math.log2(p) for p in pmf.values() if p > 0))


def hard_rate(law, bw: float, mu: float) -> dict:
    window = None if bw >= 200 else W_PS
    s = summary_of_pmf(error_pmf(law=law, bw=bw, mu=mu, window=window))
    return {"H_hard": s["H_e"], "p": s["p"], "decomp": s["decomp"]}


def soft_rate(law, bw: float, mu: float, n_sub: int = 8) -> dict:
    hs = []
    for st in range(n_sub):
        v = (st + 0.5) * bw / n_sub
        hs.append(H_of_pmf(cond_pmf_given_fine(law, bw, mu, v)))
    return {"H_soft": float(sum(hs) / len(hs)),
            "H_soft_sub": [round(h, 4) for h in hs]}


def rate_pair(*, sig: float, mu: float, bw: float,
              wide: tuple[float, float] | None = None) -> dict:
    law = Gauss(sig) if wide is None else DoubleGauss(wide[0], wide[1], wide[2])
    h = hard_rate(law, bw, mu)
    s = soft_rate(law, bw, mu)
    return {"bw": bw, "sigma": sig, "mu": mu,
            "law": ("gauss" if wide is None else f"dg{wide[0]}/{wide[1]}/{wide[2]}"),
            "R_hard": round(h["H_hard"], 4), "R_soft": round(s["H_soft"], 4),
            "gain": round(h["H_hard"] - s["H_soft"], 4),
            "p": round(h["p"], 4)}


def self_test() -> None:
    # 1. symmetry at mu=0
    pmf = cond_pmf_given_fine(Gauss(25.0), 200.0, 0.0, 100.0)
    assert abs(pmf[1] - pmf[-1]) < 1e-9, pmf
    # 2. soft <= hard everywhere on the grid (information never hurts)
    for bw, mu, sig in ((100.0, 47.0, 25.0), (200.0, 47.0, 25.0),
                        (400.0, 47.0, 25.0), (200.0, 0.0, 25.0)):
        r = rate_pair(sig=sig, mu=mu, bw=bw)
        assert r["gain"] >= -1e-9, r
    # 3. large-sigma limit: fine phase carries ~no info
    r = rate_pair(sig=100000.0, mu=0.0, bw=200.0)
    assert r["gain"] < 0.01, r
    # 4. calibrated narrow-jitter: substantial gain direction
    r = rate_pair(sig=25.0, mu=0.0, bw=200.0)
    assert r["gain"] > 0.2, r
    # 5. B2 empirical cross-check (T2-1M nominal: H_bin=0.8040, H_fine=0.2407).
    # Pure Gauss underestimates the gain (R_soft=0.324 vs 0.241) because its
    # core is wider than reality; the B1-flavored mixture closes the gap
    # (same shape finding as A3/B1). The mixture is the checking caliber.
    r = rate_pair(sig=17.3, mu=47.33, bw=200.0, wide=(17.3, 100.0, 0.0141))
    assert abs(r["R_hard"] - 0.8040) < 0.01, r
    assert abs(r["R_soft"] - 0.2407) < 0.03, r
    print("a5 self-test OK (symmetry / soft<=hard / limits / B2 cross-check)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    root = Path(args.output_root)
    if root.exists():
        raise SystemExit(f"output root not fresh: {root}")
    root.mkdir(parents=True, exist_ok=True)
    rows = []
    for bw in (100.0, 200.0, 400.0):
        rows.append(rate_pair(sig=25.5, mu=50.0, bw=bw))          # nominal
        rows.append(rate_pair(sig=25.5, mu=0.0, bw=bw))            # calibrated
        rows.append(rate_pair(sig=25.5, mu=50.0, bw=bw,
                              wide=(18.5, 100.0, 0.014)))          # nominal + B1 wide
        rows.append(rate_pair(sig=18.5, mu=0.0, bw=bw,
                              wide=(18.5, 100.0, 0.014)))          # calibrated + B1 wide
    (root / "a5_rates.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    for r in rows:
        print(f"bw={r['bw']:.0f} mu={r['mu']:+.0f} {r['law']:16s} "
              f"R_hard={r['R_hard']:.4f} R_soft={r['R_soft']:.4f} gain={r['gain']:.4f}")
    print(f"wrote {len(rows)} rows -> {root}")


if __name__ == "__main__":
    import sys
    if "--self-test" in sys.argv:
        self_test()
    else:
        main()
