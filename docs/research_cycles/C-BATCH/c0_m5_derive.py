"""M5 main-thread verification (R5). Checks RESULT doc against landed products
+ C-0 baselines. Prints PASS/FAIL per check; nonzero exit on any FAIL."""

import json
import sys

ok = True


def check(name, cond, detail=""):
    global ok
    print(("PASS " if cond else "FAIL ") + name + (f" [{detail}]" if detail else ""))
    if not cond:
        ok = False


d = json.load(open("workspace/c0_prefix/c0_20261008/m5_summary.json"))
c0 = json.load(open("workspace/c0_delayscan/c0_20261008/c0_summary.json"))
rows = [json.loads(x) for x in
        open("workspace/c0_prefix/c0_20261008/m5_rows.jsonl", encoding="utf-8")
        if x.strip()]
c0rows = [r for r in c0["rows"] if not r["repaired"]]

# Row counts / grid / keys / wall.
est = [r for r in rows if r["seg"] == "EST"]
tst = [r for r in rows if r["seg"] == "TEST"]
check("rows EST=492", len(est) == 492, str(len(est)))
check("rows TEST=24", len(tst) == 24, str(len(tst)))
steps = set()
for r in est:
    pass
deltas = sorted(set(r["delta_ps"] for r in est))
gaps = set(b - a for a, b in zip(deltas, deltas[1:]))
check("grid 41pts step [5]", len(deltas) == 41 and gaps == {5},
      f"n={len(deltas)} gaps={gaps}")
allowed = {"source", "bw_ps", "d", "delta_ps", "seg", "offset_ps", "n",
           "p", "p_minus_cond", "support_size", "top_errors"}
badkeys = [sorted(set(r) - allowed) for r in rows]
check("keys stats-only", all(b == [] for b in badkeys),
      str([b for b in badkeys if b][:2]))
check("wall<2400", d["wall_s_total"] < 2400, str(d["wall_s_total"]))
check("12 cells", len(d["cells"]) == 12, str(len(d["cells"])))

# C-0 baselines.
base = {(r["source"], r["bw_ps"]): r for r in c0rows}
full_star = {}
for (s, b), rs in {}.items():
    pass
from collections import defaultdict
bycell = defaultdict(list)
for r in c0rows:
    bycell[(r["source"], r["bw_ps"])].append(r)
for k, v in bycell.items():
    full_star[k] = min(v, key=lambda r: r["p"])["delta_ps"]
c0pairs = {}
for r in c0rows:
    c0pairs.setdefault(r["source"], r["pairs"])

# Per-cell checks.
exact = off = 0
maxdev = 0.0
for c in d["cells"]:
    s, b = c["source"], c["bw_ps"]
    check(f"n_est==10000 {s}/{b}", c["n_est"] == 10000, str(c["n_est"]))
    tot = c["n_est"] + c["n_test"]
    check(f"n_sum==C0pairs {s}", tot == c0pairs[s], f"{tot} vs {c0pairs[s]}")
    dd = abs(c["delta_star_est"] - full_star[(s, b)])
    if dd == 0:
        exact += 1
    elif dd == 5:
        off += 1
    else:
        check(f"delta* within 1 step {s}/{b}", False, f"Δ={dd}")
    best_full = min(bycell[(s, b)], key=lambda r: r["p"])["p"]
    dev = abs(c["test_best_p"] - best_full)
    maxdev = max(maxdev, dev)
    check(f"TEST transfer ~1e-3 {s}/{b}", dev < 2e-3, f"{dev:.2e}")
print(f"exact={exact}/12 off-by-one-step={off}/12 maxTESTdev={maxdev:.2e}")
print(f"INFO RESULT-doc count claim '10/12 exact,另2格' vs actual: "
      f"exact={exact} off={off} -> doc needs correction to 9/12 + 3 (one step)")
check("substantive stability (all within 1 step)", exact + off == 12)

sys.exit(0 if ok else 1)
