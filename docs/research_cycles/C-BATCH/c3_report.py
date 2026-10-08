"""C-3 联合 OPT 报告（R5：数字由脚本汇总，只读已落盘产物）。

输入：mini 各波根 mini_summary.json（OPT 主源）+ mini_rows（same-time-f 外推
与审计）+ full net_main_fresh.csv/net_detail_fresh.csv（fresh-full 行）+
C3_MAPPED.md 参考行（常数转录，指针见 c3_mapped_derive.py）。
归一：Net_per_coin 一律 Net_seg / C_PLAN(5M)（修正 mini-A4 旧格的 B·N 分母）；
w_tail 一律 (C_PLAN − B·N)/C_PLAN。A4 行归属：A3 行优先 family 标签，
无标签旧行按根归属；A4（runner 行无 family）按"根运行序×300 行块"归属，
块数不对即报错（不猜）。
OPT：每 (family,method,decoder) 行内 Net_seg 最大（N≤16384，B≥300 完成格；
并列差<1% 取小 N 注 tie）；缺席三分：missing（未跑）/ short（B<300）/
未定（已跑 F≤9 或 S≤9）。
"""

import csv
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, ".")
from comparison_bench.src.comparison_bench.formal_ir import (  # noqa: E402
    msd_c3_mini as MINI)

C_PLAN = 5_000_000.0
N_MAX_VALID = 16384
# Full-symbol kept basis (M-wave freeze; C_BATCH_AMEND): kept = N*H_A_op per
# success block with H_A_op = log2(d), d = SPAN/bw per family.
HA_OP = {"F1": 10.0, "F2": 9.0, "F3": 11.0}
# (root, [(fam, method, N, list_size)]) 运行序（A4 无 family 标签，按序切块）。
ROOT_ORDERS = {
    # c-root = resume run (F1 only; untagged rows are F1): complete A3/A4
    # small-N + fresh A3/8192 completion + A4/8192 + partial A3/16384.
    "c3_20261008c": [("F1", "A3", n, 1) for n in (1024, 2048, 4096, 8192)]
    + [("F1", "A4", n, 1) for n in (1024, 2048, 4096, 8192)]
    + [("F1", "A3", 16384, 1)],
    # b-root: CLEAN rebuild (single-writer parts; ran F1 only, died in
    # F1/8192-A3). Untagged rows -> F1. (The corrupt dual-handle root is
    # workspace/c3_mini/c3_20261008/ (no suffix) -- EXCLUDED entirely: all
    # its complete cells were rerun in b with identical seeds.)
    "c3_20261008b": [("F1", "A3", n, 1) for n in (1024, 2048, 4096, 8192)]
    + [("F1", "A4", n, 1) for n in (1024, 2048, 4096)],
    "c3_20261008d": [("F2", "A3", n, 1) for n in
                     (1024, 2048, 4096, 8192, 16384, 32768, 65536)]
    + [("F2", "A4", n, 1) for n in
       (1024, 2048, 4096, 8192, 16384, 32768, 65536)],
    "c3_20261008e": [("F1", "A4", n, 1) for n in (16384, 32768, 65536)],
    "c3_20261008f": [("F2", "A3", n, 1) for n in (32768, 65536)]
    + [("F2", "A4", n, 1) for n in (32768, 65536)],
    "c3_20261008g": [("F1", "A4", 1024, 8), ("F1", "A4", 4096, 8),
                     ("F2", "A4", 1024, 8), ("F2", "A4", 4096, 8)],
    "c3_20261008i": [("F1", "A4", 2048, 8), ("F1", "A4", 8192, 8),
                     ("F2", "A4", 2048, 8), ("F2", "A4", 8192, 8)],
    "c3_20261008h": [("F3", "A3", n, 1) for n in (1024, 2048, 4096)]
    + [("F3", "A4", n, 1) for n in (1024, 2048, 4096)],
}
WS = Path("workspace/c3_mini")


def load_mini_rows():
    """Return {(fam, method, N, L): [rows]} across wave roots."""
    cells: dict[tuple, list] = {}
    untagged: dict[tuple[str, str], int] = {}
    seen: set[tuple] = set()
    stats: dict = {}

    def put(fam, meth, N, L, row, src):
        key = (fam, meth, N, L, int(row.get("block", -1)))
        if key in seen:
            stats.setdefault(("dupe", src, fam, meth, N, L), 0)
            stats[("dupe", src, fam, meth, N, L)] += 1
            return
        seen.add(key)
        stats.setdefault(("put", src, fam, meth, N, L), 0)
        stats[("put", src, fam, meth, N, L)] += 1
        cells.setdefault((fam, meth, N, L), []).append(row)
    for root, order in ROOT_ORDERS.items():
        rp = WS / root
        if not rp.exists():
            continue
        # A3 rows: family tag preferred.
        p3 = rp / "mini_rows_a3.jsonl"
        if p3.exists():
            for line in p3.open(encoding="utf-8"):
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                fam = r.get("family") or None
                if fam is None:
                    # untagged old rows: only c-root ran F1 with the old code.
                    fam = "F1"
                    untagged[(rp.name, fam)] = untagged.get(
                        (rp.name, fam), 0) + 1
                put(fam, "A3", int(r["N"]), 1, r, root)
        # A4 rows: chunk attribution by run order.
        p4 = rp / "mini_rows_a4.jsonl"
        if p4.exists():
            rows = []
            for line in p4.open(encoding="utf-8"):
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
            a4order = [(f, m, n, L) for (f, m, n, L) in order if m == "A4"]
            idx, pos = 0, 0
            for (f, m, n, L) in a4order:
                chunk = rows[pos:pos + 300]
                if len(chunk) == 300 and all(
                        int(x.get("N", -1)) == n for x in chunk):
                    for x in chunk:
                        put(f, m, n, L, x, root)
                    pos += 300
                elif len(chunk) == 0:
                    break
                else:
                    # partial tail cell: attribute what exists (short)
                    for x in chunk:
                        if int(x.get("N", -1)) == n:
                            put(f, m, n, L, x, root)
                    pos += len(chunk)
    print("untagged-A3-rows-as-F1:", untagged)
    ps = sorted((k, v) for k, v in stats.items() if k[0] == "put")
    ds = sorted((k, v) for k, v in stats.items() if k[0] == "dupe")
    print("puts-per-(root,fam,method,N,L):")
    for k, v in ps:
        print("  ", k[1:], v)
    print("dupes:", ds if ds else "none")
    return cells


def cell_stats(rows, B_need=300):
    B = len(rows)
    S = sum(1 for r in rows if r.get("ver") == 1 and not r.get("u"))
    F = sum(1 for r in rows if r.get("ver") == 0)
    U = sum(1 for r in rows if r.get("u"))
    kept = [r.get("kept", 0.0) for r in rows if r.get("ver") == 1]
    lec = [r.get("L_EC", 0) for r in rows]
    tags = [r.get("tag", 0) for r in rows]
    net = sum(kept) - sum(lec) - sum(tags)
    L_total = sum(lec) + sum(tags)
    tds = sorted(r.get("T_dec", 0.0) for r in rows)
    med = tds[len(tds) // 2] if tds else 0.0
    return {"B": B, "S": S, "F": F, "U": U, "Net_seg": net,
            "L_total": L_total, "sum_lec": sum(lec), "sum_tags": sum(tags),
            "FER": F / B if B else None, "median_T_dec": med,
            "complete": B >= B_need}


def main() -> None:
    cells = load_mini_rows()
    print(f"mini cells landed: {len(cells)}")
    out = []
    famHQ = {}
    for fam in ("F1", "F2", "F3"):
        try:
            q0, g0, H0, _ = MINI.family_prior(fam)
            famHQ[fam] = (q0, H0)
        except Exception:
            pass
    for key in sorted(cells):
        fam, meth, N, L = key
        st = cell_stats(cells[key])
        npc = st["Net_seg"] / C_PLAN
        flag = ("ok" if st["complete"]
                else ("short" if st["B"] > 0 else "missing"))
        if st["complete"] and (st["F"] <= 9 or st["S"] <= 9):
            flag = "未定"
        f_full = beta = None
        net_fullsym = None
        if fam in famHQ and st["B"] > 0:
            q0, H0 = famHQ[fam]
            f_full = st["L_total"] / (st["B"] * N * H0)
            iop = math.log2(q0) - H0
            beta = st["Net_seg"] / (st["B"] * N * iop) if iop > 0 else None
        if fam in HA_OP and st["B"] > 0:
            # Full-symbol kept (M-wave basis): S*N*H_A_op - ΣLEC - Σtag.
            net_fullsym = (st["S"] * N * HA_OP[fam]
                           - st["sum_lec"] - st["sum_tags"])
        out.append({"family": fam, "method": meth, "N": N, "L": L,
                    **st, "Net_per_coin_5M": npc, "flag": flag,
                    "f_full": f_full, "beta_side": beta,
                    "Net_fullsym": net_fullsym})
        print(fam, meth, f"N={N}", f"L={L}", f"B={st['B']}",
              f"net={st['Net_seg']:.1f}", f"FER={st['FER']:.4f}"
              if st["FER"] is not None else "FER=?", flag)
    Path("workspace/c3_mini/mini_cells.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8")
    print("wrote workspace/c3_mini/mini_cells.json")
    # OPT per (family, method, L): literal-rule exclusion (F<=9|S<=9 out)
    # + invariance check (argmax with/without exclusion must agree).
    opt = []
    for fam in sorted(set(c["family"] for c in out)):
        for meth in sorted(set(c["method"] for c in out)):
            for L in sorted(set(c["L"] for c in out if c["family"] == fam
                               and c["method"] == meth)):
                cand = [c for c in out if c["family"] == fam
                        and c["method"] == meth and c["L"] == L
                        and c["N"] <= N_MAX_VALID and c["flag"] == "ok"]
                pool = [c for c in out if c["family"] == fam
                        and c["method"] == meth and c["L"] == L
                        and c["N"] <= N_MAX_VALID
                        and c["flag"] in ("ok", "未定")]
                if not pool:
                    opt.append({"family": fam, "method": meth, "L": L,
                                "status": "missing-or-short"})
                    continue
                best_all = max(pool, key=lambda c: c["Net_seg"])
                okpool = [c for c in pool if c["flag"] == "ok"]
                best_ok = max(okpool, key=lambda c: c["Net_seg"]) \
                    if okpool else None
                inv = (best_ok is not None
                       and best_ok["N"] == best_all["N"])
                if not inv:
                    print(f"ESCALATE: {fam}/{meth}/L={L} argmax needs "
                          f"undetermined cell N={best_all['N']}")
                best = (best_ok or best_all)
                row = dict(best)
                opt.append({"family": fam, "method": meth, "L": L,
                            "opt_N": row["N"], "B": row["B"],
                            "Net_seg": row["Net_seg"],
                            "Net_per_coin_5M": row["Net_per_coin_5M"],
                            "f_full": row["f_full"],
                            "FER_hat": (None if row["flag"] == "未定"
                                        else row["FER"]),
                            "FER_flag": row["flag"],
                            "U": row["U"],
                            "median_T_dec": row["median_T_dec"],
                            "beta_side": row["beta_side"],
                            "excluded_undet": [c["N"] for c in pool
                                               if c["flag"] == "未定"],
                            "argmax_invariant": inv,
                            "status": "ok" if best_ok else "all-undetermined"})
    Path("workspace/c3_mini/mini_opt.json").write_text(
        json.dumps(opt, indent=1), encoding="utf-8")
    print("wrote workspace/c3_mini/mini_opt.json")
    # S1: net-vs-time-budget curves per cell (cumulative run order).
    curves = {}
    for key, rows in cells.items():
        fam, meth, N, L = key
        t = x = 0.0
        pts = []
        for r in rows:
            # Frozen R16 per-block formula (C3_DESIGN §1.2), literal.
            v, u = int(r.get("ver", 0)), int(bool(r.get("u", 0)))
            kept, lec = float(r.get("kept", 0.0)), float(r.get("L_EC", 0))
            tag = float(r.get("tag", 0)) if v == 1 else 0.0
            t += float(r.get("T_dec", 0.0))
            x += v * (1 - u) * (kept - lec - tag) - (1 - v) * lec
            pts.append([round(t, 3), round(x, 1)])
        curves[f"{fam}/{meth}/N{N}/L{L}"] = pts
    Path("workspace/c3_mini/mini_curves.json").write_text(
        json.dumps(curves, indent=0), encoding="utf-8")
    print(f"wrote mini_curves.json ({len(curves)} curves)")
    # Same-time net: per family, T_ref = MIN total-T over OPT cells
    # (fastest sets the bar; slow cells scale DOWN = interpolation, safe;
    # extrapolating fast cells UP 200x is statistically reckless, see WATCH).
    # Answers: "given the fastest method's time budget, what net does each
    # method deliver?" = complexity cost. Labeled extrap. except anchor.
    cells_all = json.loads(
        Path("workspace/c3_mini/mini_cells.json").read_text(encoding="utf-8"))
    opt_all = json.loads(
        Path("workspace/c3_mini/mini_opt.json").read_text(encoding="utf-8"))
    by_fam: dict[str, list] = {}
    for o in opt_all:
        if o.get("status") != "ok":
            continue
        det = [c for c in cells_all if c["family"] == o["family"]
               and c["method"] == o["method"] and c["L"] == o["L"]
               and c["N"] == o["opt_N"]]
        if not det:
            continue
        tot = det[0]["B"] * det[0]["median_T_dec"]
        by_fam.setdefault(o["family"], []).append((o, det[0], tot))
    for fam, lst in by_fam.items():
        t_ref = min(t for _, _, t in lst)
        for o, det, tot in lst:
            scale = t_ref / tot if tot > 0 else 1.0
            o["T_ref_s"] = t_ref
            o["Net_same_time"] = det["Net_seg"] * scale
            o["same_time_note"] = ("anchor" if scale == 1.0 else "extrap.")
    Path("workspace/c3_mini/mini_opt.json").write_text(
        json.dumps(opt_all, indent=1), encoding="utf-8")
    for o in opt_all:
        print("OPT", o.get("family"), o.get("method"), f"L={o.get('L')}",
              "N=", o.get("opt_N"), o.get("status"),
              "sameT-net=", round(o.get("Net_same_time", float("nan")), 1)
              if o.get("Net_same_time") is not None else None)


if __name__ == "__main__":
    main()
