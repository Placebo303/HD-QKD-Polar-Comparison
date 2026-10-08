"""C-3 FINAL joint assembly (R5: script-built from landed artifacts only).

Primary: M-wave (OP-M1 cells.json + M net_detail_m.csv) — fullsym kept,
raised caps, no timeouts. Reference: mini Net_fullsym (pilot, q-ary era,
superseded for ranking) + mapped cross-regime rows (C3_MAPPED).
f_full RECOMPUTED everywhere on H_AB_op basis (channel property, shared):
F1 0.38901 / F2 0.22579 / F3 1.03750. beta recomputed on true I_op =
H_A_op - H_AB_op (F1 9.61099 / F2 8.77421 / F3 9.96250).
Literal rule: complete + (F<=9 or S<=9) -> 未定 (excluded from argmax);
argmax-invariance proof printed (ESCALATE if exclusion flips argmax).
Same-time: min-anchor interpolation per family over OPT cells.
"""

import csv
import json
import math
from pathlib import Path

HAB = {"F1": 0.38901, "F2": 0.22579, "F3": 1.03750}
HA = {"F1": 10.0, "F2": 9.0, "F3": 11.0}
N_MAX_VALID = 16384
OUT = Path("workspace/c3_mini/final_cells.json")


def num(x, total, other):
    if isinstance(x, (int, float)):
        return int(x)
    if x == "未定":
        return int(total) - int(other)
    return int(x)


def flag_of(B, F, S, complete):
    if not complete:
        return "short" if B > 0 else "missing"
    if F <= 9 or S <= 9:
        return "未定"
    return "ok"


def recount_m1(wp, meth, var, N):
    """Exact recount of a short cell from landed block rows (M1 root)."""
    import glob as _g
    cands = _g.glob(f"workspace/c3_mtune/mt_a1a2_opm1/blocks/{wp}_{meth}*_N{N}_*.jsonl")
    if var:
        cands = [p for p in cands if var in p] or cands
    rows = []
    for p in cands:
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def recount_m(wp, meth, N, M="2.5"):
    """Exact recount of a short cell from OP-M2 block rows."""
    import glob as _g
    tag = meth.replace("-", "")
    pats = _g.glob(f"workspace/c3_mtune/mt_20261008/blocks/{wp}_{meth}_N{N}_*.jsonl")
    pats += _g.glob(f"workspace/c3_mtune/mt_20261008/blocks/{wp}_{tag}_N{N}_*.jsonl")
    rows = []
    for p in dict.fromkeys(pats):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def main() -> None:
    cells = []

    def add(fam, meth, var, N, B, S, F, U, net, Ltot, tmed, ev):
        complete = (B >= 300)
        fl = flag_of(B, F, S, complete)
        complete = (B >= 300)
        fl = flag_of(B, F, S, complete)
        H = HAB[fam]
        f = Ltot / (B * N * H) if B and N and H else None
        iop = HA[fam] - H
        beta = net / (B * N * iop) if (B and N and iop) else None
        cells.append({"family": fam, "method": meth, "variant": var,
                      "N": N, "B": B, "S": S, "F": F, "U": U,
                      "Net_seg": net, "L_total": Ltot,
                      "Net_per_coin_5M": net / 5_000_000.0,
                      "f_full": f, "FER_disp": ("未定" if fl == "未定"
                                                else (F / B if B else None)),
                      "beta_side": beta, "median_T_dec": tmed,
                      "evidence": ev, "flag": fl})

    # --- OP-M1 cells (fullsym already; kept_per_success=N*H_A) ---
    m1 = json.load(open("workspace/c3_mtune/mt_a1a2_opm1/cells.json"))
    m1cells = m1 if isinstance(m1, list) else m1.get("cells", [])
    for c in m1cells:
        if not isinstance(c, dict):
            continue
        n = c.get("net") or {}
        if not isinstance(n, dict) or not n:
            continue
        B, S = int(c.get("B", 0)), int(n.get("S_main", 0))
        F = int(n.get("F", B - S))
        U = int(n.get("U", 0))
        # short cells: recount exact from block rows (never trust partial sums)
        Brow = int(c.get("rows", B))
        if Brow < 300 or B < 300:
            rows = recount_m1(c.get("WP", "?"), c.get("method", "?"),
                              c.get("variant", ""), int(c.get("N", 0)))
            if rows:
                B = len(rows)
                S = sum(1 for r in rows if r.get("ver") == 1
                        and not r.get("u"))
                F = sum(1 for r in rows if r.get("ver") == 0)
                U = sum(1 for r in rows if r.get("u"))
                kept = sum(r.get("kept", 0.0) for r in rows
                           if r.get("ver") == 1 and not r.get("u"))
                lec = sum(r.get("L_EC", 0) for r in rows)
                tag = sum(r.get("tag", 0) for r in rows
                          if r.get("ver") == 1)
                n["Net_seg"] = kept - lec - tag
                n["L_total"] = lec + tag
                n["S_main"], n["F"], n["U"] = S, F, U
                tds = sorted(r.get("T_dec", 0.0) for r in rows)
                c["median_T_dec"] = tds[len(tds) // 2]
        add(c.get("WP", "?"), c.get("method", "?"),
            c.get("variant", ""), int(c.get("N", 0)), B, S, F, U,
            float(n.get("Net_seg", 0.0)),
            float(n.get("L_total", 0.0)),
            float(c.get("median_T_dec", 0.0) or 0.0), "M1-fresh")

    # --- M detail (OP-M2 BLOCK FILES are primary; CSV may predate late cells).
    # Recount everything from rows (verdicts live here, not in summaries).
    import glob as _g
    import re as _re
    mseen: dict[tuple, list] = {}
    for p in _g.glob("workspace/c3_mtune/mt_20261008/blocks/*.jsonl"):
        m = _re.match(r"([A-Z0-9]+)_([A-Za-z0-9]+?)(?:-(SC|SCL8))?_N(\d+)_M([\d.]+)\.jsonl$",
                      Path(p).name)
        if not m:
            print("UNPARSED filename:", p)
            continue
        wp, meth, var, N, Mv = m.group(1), m.group(2), m.group(3) or "", \
            int(m.group(4)), m.group(5)
        rows = []
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
        mseen.setdefault((wp, meth, var, N, Mv), []).extend(rows)
    for (wp, meth, var, N, Mv), rows in sorted(mseen.items()):
        B = len(rows)
        S = sum(1 for r in rows if r.get("ver") == 1 and not r.get("u"))
        F = sum(1 for r in rows if r.get("ver") == 0)
        U = sum(1 for r in rows if r.get("u"))
        kept = sum(r.get("kept", 0.0) for r in rows
                   if r.get("ver") == 1 and not r.get("u"))
        lec = sum(r.get("L_EC", 0) for r in rows)
        tag = sum(r.get("tag", 0) for r in rows if r.get("ver") == 1)
        tds = sorted(float(r.get("T_dec", 0.0)) for r in rows)
        med = tds[len(tds) // 2] if tds else 0.0
        net = kept - lec - tag
        Lt = lec + tag
        fam = wp  # WP names are F1/F2/F3 already
        if fam not in HAB:
            print("SKIP non-family file:", wp, meth, var, N)
            continue
        H = HAB[fam]
        f = Lt / (B * N * H) if B and N else None
        iop = HA[fam] - H
        beta = net / (B * N * iop) if (B and N and iop) else None
        fl = flag_of(B, F, S, B >= 300)
        cells.append({"family": fam, "method": meth, "variant": var,
                      "N": N, "B": B, "S": S, "F": F, "U": U,
                      "M": Mv, "Net_seg": net, "L_total": Lt,
                      "Net_per_coin_5M": net / 5_000_000.0,
                      "f_full": f, "FER_disp": ("未定" if fl == "未定"
                                                else (F / B if B else None)),
                      "beta_side": beta, "median_T_dec": med,
                      "evidence": "M-fresh", "flag": fl})
        print(f"M-recount {fam} {meth} {var or '-'} N={N} M={Mv} "
              f"B={B} S={S} net={net:.0f} f={f:.3f} {fl}")

    # --- mini pilot (Net_fullsym already recomputed; reference only) ---
    mini = json.load(open("workspace/c3_mini/mini_cells.json"))
    for c in mini:
        if c.get("Net_fullsym") is None:
            continue
        B, S, F = c["B"], c["S"], c["F"]
        U = c.get("U", 0)
        L = c.get("L", 1)
        var = ("SCL8" if (c["method"] == "A4" and L == 8)
               else ("SC" if c["method"] == "A4" else ""))
        # L_total for f: recompute basis consistent -> use stored f*
        # (mini f_full already H_AB-basis); L_total back-out:
        H = HAB[c["family"]]
        Lt = (c["f_full"] or 0.0) * B * c["N"] * H if c.get("f_full") else 0.0
        add(c["family"], c["method"], var + "-pilot" if var else "pilot",
            c["N"], B, S, F, U, c["Net_fullsym"], Lt,
            c.get("median_T_dec", 0.0), "mini-pilot")

    # --- mapped cross-regime reference (C3_MAPPED.md frozen values) ---
    mapped = [
        ("G5-p0.24", "A1", "RA-best", 32768, 300, 300, 0, 0, 89338610.55,
         1.1397810138, "synthetic"),
        ("G5-p0.24", "A2", "SCL8", 32768, 300, 300, 0, 0, 89250410.55,
         1.1510224382, "synthetic"),
        ("F1-clean", "A6", "diff", 1024, 112, 112, 0, 0, 1020647.29,
         1.3761513517, "real-clean-OOS"),
        ("D4-retest", "A6", "diff", 1024, 260, 260, 0, 0, 2335265.49,
         1.5365985870, "real-retest"),
    ]
    for fam, meth, var, N, B, S, F, U, net, f, ev in mapped:
        H = 0.7981344445  # T2-1M scalar per PAPER_NUMBERS (mapped basis)
        Lt = f * B * N * H
        iop = 10.0 - H
        cells.append({"family": fam, "method": meth, "variant": var,
                      "N": N, "B": B, "S": S, "F": F, "U": U,
                      "Net_seg": net, "L_total": Lt,
                      "Net_per_coin_5M": None, "f_full": f,
                      "FER_disp": F / B if B else None,
                      "beta_side": net / (B * N * iop),
                      "median_T_dec": None, "evidence": "mapped-" + ev,
                      "flag": "ref"})

    OUT.write_text(json.dumps(cells, indent=1), encoding="utf-8")
    print(f"final cells: {len(cells)} -> {OUT}")
    # OPT per (family, method, variant) over M-fresh primary.
    picks = []
    for fam in ("F1", "F2", "F3"):
        for meth in ("A1", "A2", "A3", "A4", "A6"):
            variants = sorted(set(
                c["variant"] for c in cells if c["family"] == fam
                and c["method"] == meth
                and c["evidence"].startswith(("M1", "M-"))))
            for var in variants:
                pool = [c for c in cells if c["family"] == fam
                        and c["method"] == meth and c["variant"] == var
                        and c["evidence"].startswith(("M1", "M-"))
                        and c["N"] <= N_MAX_VALID
                        and c["flag"] in ("ok", "未定")]
                if not pool:
                    print(fam, meth, var, "M: (no complete M cells)")
                    continue
                best_all = max(pool, key=lambda c: c["Net_seg"])
                okp = [c for c in pool if c["flag"] == "ok"]
                best_ok = max(okp, key=lambda c: c["Net_seg"]) \
                    if okp else None
                inv = best_ok is not None and best_ok["N"] == best_all["N"]
                pick = best_ok or best_all
                picks.append((fam, meth, var, pick, inv, pool))
                print(fam, meth, var,
                      f"OPT N={pick['N']} net={pick['Net_seg']:.0f} "
                      f"f={pick['f_full']:.3f} FER={pick['FER_disp']} "
                      f"pool={[ (c['N'],c['flag']) for c in pool ]} "
                      f"invariant={inv}" + ("" if inv else " ESCALATE"))
    # Same-time: FIXED budget T=60s, interpolation-only (S1 decision).
    # min-anchor degenerates (fastest cell forces 1000-20000x downscales);
    # max-anchor extrapolates recklessly. T=60s: cells with total_T>=60
    # interpolate (exact under i.i.d. proportionality); faster cells report
    # n/a (no upward extrapolation). S1 curves (mini_curves.json + M rows)
    # carry the full budget sweep; this column is one readable slice.
    for fam in ("F1", "F2", "F3"):
        for (f, m, v, p, inv, pool) in picks:
            if f != fam:
                continue
            tot = p["B"] * (p["median_T_dec"] or 0.0)
            if tot >= 60.0:
                p["Net_60s"] = p["Net_seg"] * 60.0 / tot
                p["Net_60s_note"] = "interp."
            else:
                p["Net_60s"] = None
                p["Net_60s_note"] = "n/a-beyond-measured"
            print(f"sameT60 {f} {m} {v}: total={tot:.1f}s "
                  f"net {p['Net_seg']:.0f}->"
                  f"{p['Net_60s'] if p['Net_60s'] is None else round(p['Net_60s']):} "
                  f"({p['Net_60s_note']})")
    # Pilot leaders (mini-pilot reference only, superseded for ranking).
    for fam in ("F1", "F2", "F3"):
        for meth in ("A3", "A4"):
            pl = [c for c in cells if c["family"] == fam
                  and c["method"] == meth and c["evidence"] == "mini-pilot"
                  and c["N"] <= N_MAX_VALID and c["flag"] == "ok"]
            if pl:
                b = max(pl, key=lambda c: c["Net_seg"])
                print(f"pilot-ref {fam} {meth} {b.get('variant')}: "
                      f"N={b['N']} net={b['Net_seg']:.0f} f={b['f_full']:.3f}")
    json.dump([{"family": f, "method": m, "variant": v,
                "opt_N": p["N"], "B": p["B"], "Net_seg": p["Net_seg"],
                "Net_per_coin_5M": p["Net_per_coin_5M"],
                "f_full": p["f_full"], "FER": p["FER_disp"],
                "U": p["U"], "median_T_dec": p["median_T_dec"],
                "beta_side": p["beta_side"],
                "Net_same_time": p.get("Net_60s"),
                "same_time_note": (p.get("Net_60s_note") or "") + "; S1 curves",
                "excluded_undet": sorted(set(
                    c["N"] for c in pool if c["flag"] == "未定")),
                "argmax_invariant": inv,
                "status": ("ok" if any(c["flag"] == "ok" for c in pool)
                           else "all-undetermined")}
               for (f, m, v, p, inv, pool) in picks],
              open("workspace/c3_mini/final_opt.json", "w", encoding="utf-8"),
              indent=1)
    print("wrote workspace/c3_mini/final_opt.json")


if __name__ == "__main__":
    main()
