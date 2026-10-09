"""A3 offset+jitter analytic model (EXPLORE, landed stats only).

For an arbitrary jitter law of Delta = J + mu (J zero-mean shape, mu residual
offset), the binned error probabilities are (C2_DESIGN section 1.2, eq.1):

    P(e=k) = (1/bw) * int_0^bw [ F((k+1)bw-u-mu) - F(k*bw-u-mu) ] du,

with coincidence-window conditioning (eq.4) via clipping to [-W, W].
Families: gauss / gauss+uniform / double-gauss. Gaussian closed form
cross-checked against C-2 A_func (imported, not modified).

Outputs p_+, p_-, H(e) (full support + rest-as-outcome) and a comparison
table built from landed Z-2 / C-0 / C-2 JSONs (no D:/Data, no decoder).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

W_PS = 200.0  # nominal coincidence window (C-2 A4)


def h2(x: float) -> float:
    if x <= 0.0 or x >= 1.0:
        return 0.0
    return -(x * math.log2(x) + (1.0 - x) * math.log2(1.0 - x))


def _Phi(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


class DeltaLaw:
    """Zero-mean jitter shape J with CDF/interval-mass interface."""

    def interval_mass(self, lo: float, hi: float) -> float:
        raise NotImplementedError


class Gauss(DeltaLaw):
    def __init__(self, sig: float):
        self.sig = float(sig)

    def interval_mass(self, lo: float, hi: float) -> float:
        return _Phi(hi / self.sig) - _Phi(lo / self.sig)


class GaussUniform(DeltaLaw):
    def __init__(self, sig: float, eps: float, w: float = W_PS):
        self.g = Gauss(sig)
        self.eps = float(eps)
        self.w = float(w)

    def interval_mass(self, lo: float, hi: float) -> float:
        gm = self.g.interval_mass(lo, hi)
        um = (min(hi, self.w) - max(lo, -self.w)) / (2.0 * self.w)
        um = max(um, 0.0)
        return (1.0 - self.eps) * gm + self.eps * um


class DoubleGauss(DeltaLaw):
    def __init__(self, s1: float, s2: float, w: float):
        self.g1, self.g2 = Gauss(s1), Gauss(s2)
        self.w = float(w)

    def interval_mass(self, lo: float, hi: float) -> float:
        return ((1.0 - self.w) * self.g1.interval_mass(lo, hi)
                + self.w * self.g2.interval_mass(lo, hi))


def _simpson(f, a: float, b: float, n: int = 256) -> float:
    if n % 2:
        n += 1
    h = (b - a) / n
    s = f(a) + f(b)
    for i in range(1, n):
        s += (4.0 if i % 2 else 2.0) * f(a + i * h)
    return s * h / 3.0


def error_pmf(*, law: DeltaLaw, bw: float, mu: float,
              window: float | None = W_PS, khard: int | None = None) -> dict[int, float]:
    """Full P(e=k) over |k|<=khard (+ mass conservation check)."""
    bw = float(bw)
    if khard is None:
        khard = int(math.ceil(( (window or 0.0) + abs(mu) + 4 * 50.0) / bw)) + 1
    pmf: dict[int, float] = {}
    for k in range(-khard, khard + 1):
        def integrand(u: float, k: int = k) -> float:
            lo, hi = k * bw - u - mu, (k + 1) * bw - u - mu
            if window is not None:
                lo, hi = max(lo, -window), min(hi, window)
                if hi <= lo:
                    return 0.0
            return law.interval_mass(lo, hi)
        pmf[k] = _simpson(integrand, 0.0, bw) / bw
    if window is not None:
        c = sum(pmf.values())
        if c > 0:
            pmf = {k: v / c for k, v in pmf.items()}
    return pmf


def summary_of_pmf(pmf: dict[int, float]) -> dict:
    tot = sum(pmf.values())
    rest = max(0.0, 1.0 - tot)
    ent = -sum(p * math.log2(p) for p in pmf.values() if p > 0)
    if rest > 0:
        ent -= rest * math.log2(rest)
    p0 = pmf.get(0, 0.0)
    p = 1.0 - p0
    p_plus = pmf.get(1, 0.0)
    p_minus = pmf.get(-1, 0.0)
    pm = (p_minus / p) if p > 0 else float("nan")
    return {"p_plus": p_plus, "p_minus": p_minus, "p": p,
            "p_minus_cond": pm, "H_e": ent,
            "decomp": h2(p) + (p * h2(pm) if pm == pm and 0 < pm < 1 else 0.0)}


def self_test() -> None:
    from comparison_bench.src.comparison_bench.formal_ir import msd_c2_fit as c2
    # 1. symmetry at mu=0
    s = summary_of_pmf(error_pmf(law=Gauss(25.0), bw=200.0, mu=0.0, window=None))
    assert abs(s["p_plus"] - s["p_minus"]) < 1e-9, s
    # 2. agreement with C-2 closed form (Gaussian, unconditioned)
    for bw, mu, sig in ((200.0, 47.0, 25.0), (400.0, -50.0, 26.0)):
        pmf = error_pmf(law=Gauss(sig), bw=bw, mu=mu, window=None)
        t = c2.ternary_uncond(bw, sig, mu)
        assert abs(pmf[-1] - t[0]) < 2e-4, (bw, mu, pmf[-1], t)
        assert abs(pmf[0] - t[1]) < 2e-4, (bw, mu, pmf[0], t)
        assert abs(pmf[1] - t[2]) < 2e-4, (bw, mu, pmf[1], t)
    # 3. mixture degeneration
    a = summary_of_pmf(error_pmf(law=Gauss(25.0), bw=200.0, mu=47.0, window=None))
    b = summary_of_pmf(error_pmf(law=GaussUniform(25.0, 0.0), bw=200.0, mu=47.0, window=None))
    c = summary_of_pmf(error_pmf(law=DoubleGauss(25.0, 100.0, 0.0), bw=200.0, mu=47.0, window=None))
    assert abs(a["p"] - b["p"]) < 1e-9 and abs(a["p"] - c["p"]) < 1e-9, (a, b, c)
    # 4. large-bw limit (pure Gauss, unconditioned) -> ~0
    s = summary_of_pmf(error_pmf(law=Gauss(25.0), bw=6400.0, mu=47.0, window=None))
    assert s["p"] < 0.02, s
    print("a3 self-test OK (symmetry / C-2 agreement / degeneration / large-bw)")


def build_table() -> list[dict]:
    z2 = json.load(open("workspace/z2_reframe/z2_20261008/z2_summary.json", encoding="utf-8"))
    c0 = json.load(open("workspace/c0_delayscan/c0_20261008/c0_summary.json", encoding="utf-8"))
    c2 = json.load(open("workspace/c2_fit/c2_20261008/c2_fit.json", encoding="utf-8"))
    sig_of = {src: rec["estC"]["sig"] for src, rec in c2["per_source"].items()}
    mu_of = {src: rec["estC"]["delta"] for src, rec in c2["per_source"].items()}
    obs = {(r["source"], r["bw_ps"]): r for r in z2}
    # C-0 nominal (delta=0) and optimal rows per (source, bw)
    c0rows = {(r["source"], r["bw_ps"], r["delta_ps"]): r for r in c0["rows"] if not r.get("repaired")}
    out = []
    for (src, bw), r in sorted(obs.items()):
        sig, mu = sig_of[src], mu_of[src]
        law = Gauss(sig)
        if bw in (200, 400):
            pmf = error_pmf(law=law, bw=float(bw), mu=float(mu), window=None)
        else:
            pmf = error_pmf(law=law, bw=float(bw), mu=float(mu), window=W_PS)
        pred = summary_of_pmf(pmf)
        row = {"source": src, "bw": bw, "d": r["d"], "n": r["pairs"],
               "sigma_C": sig, "mu_C": mu,
               "obs_p": r["p"], "obs_pm": r["p_minus_cond"],
               "obs_He": r["H_e"], "pred_p": round(pred["p"], 6),
               "pred_pm": round(pred["p_minus_cond"], 4) if pred["p_minus_cond"] == pred["p_minus_cond"] else None,
               "pred_He": round(pred["H_e"], 4),
               "resid_p": round(r["p"] - pred["p"], 6),
               "p_times_bw": round(r["p"] * bw, 1)}
        if bw in (200, 400):
            nom = c0rows.get((src, bw, 0))
            opt = min((v for k, v in c0rows.items() if k[0] == src and k[1] == bw),
                      key=lambda v: v["p"])
            row.update({"c0_nominal_p": nom["p"] if nom else None,
                        "c0_opt_p": opt["p"], "c0_opt_delta": opt["delta_ps"],
                        "c0_opt_pm": opt["p_minus_cond"]})
        out.append(row)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()
    root = Path(args.output_root)
    if root.exists():
        raise SystemExit(f"output root not fresh: {root}")
    root.mkdir(parents=True, exist_ok=True)
    rows = build_table()
    (root / "a3_table.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    cols = ["source", "bw", "n", "sigma_C", "mu_C", "obs_p", "obs_pm",
            "c0_nominal_p", "c0_opt_p", "c0_opt_delta", "pred_p", "pred_pm",
            "resid_p", "obs_He", "pred_He", "p_times_bw"]
    with open(root / "a3_table.csv", "w", encoding="utf-8") as f:
        f.write(",".join(cols) + "\n")
        for r in rows:
            f.write(",".join("" if r.get(c) is None else str(r.get(c)) for c in cols) + "\n")
    for r in rows:
        print(f"{r['source']:8s} bw={r['bw']:4d} obs_p={r['obs_p']:.4f} "
              f"pred_p={r['pred_p']:.4f} resid={r['resid_p']:+.5f} "
              f"p*bw={r['p_times_bw']:.1f} He {r['obs_He']:.4f}/{r['pred_He']:.4f}")
    print(f"wrote {len(rows)} rows -> {root}")


if __name__ == "__main__":
    import sys
    if "--self-test" in sys.argv:
        self_test()
    else:
        main()
