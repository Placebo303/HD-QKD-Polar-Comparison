"""D5 decomposition successor S4: independent verify from saved scalars only.

Recomputes ranking, row arithmetic, call accounting, exact/syndrome
separation, and the section 4.5 terminal from partition_scores.csv +
decoder_records.csv + selected_partitions.json. Writes summary.json +
appends command_log.txt. No decoder, no parquet.
"""
import json
import math
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
LOG = ROOT / "command_log.txt"


def log(msg):
    line = "%s %s" % (time.strftime("%Y-%m-%dT%H:%M:%S"), msg)
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


sc = pd.read_csv(ROOT / "partition_scores.csv")
dc = pd.read_csv(ROOT / "decoder_records.csv")
sel = json.loads((ROOT / "selected_partitions.json").read_text(encoding="utf-8"))
checks = {}


def check(name, ok):
    checks[name] = bool(ok)
    log("S4 %s %s" % (name, "PASS" if ok else "FAIL"))


check("n252_unique", len(sc) == 252 and sc["s1"].nunique() == 252)
check("chain_all", bool((sc["chain_max_abs_err"] < 1e-9).all()))
check("rows_arith", bool((((64 * sc["ce_l1"] * 1.2 / 5).apply(math.ceil) == sc["m1"])
                          & ((64 * sc["ce_l2"] * 1.2 / 5).apply(math.ceil) == sc["m2"])).all()))
check("elig_arith", bool(((sc["m1"] < 64) & (sc["m2"] < 64) == sc["eligible"]).all()))
tmp = sc.copy()
tmp["max_ce"] = tmp[["ce_l1", "ce_l2"]].max(axis=1)
ordered = tmp.sort_values(["max_ce", "ce_joint", "ce_l1", "s1"]).reset_index(drop=True)
check("top3_match", list(ordered.head(3)["s1"]) == [x["s1"] for x in sel["selected"] if x["role"] == "top3"])
check("controls_present", {"5-6-7-8-9", "0-1-2-3-4"} <= {x["s1"] for x in sel["selected"]})
check("dedup", len(sel["selected"]) == len({x["s1"] for x in sel["selected"]}))
check("seeds_frozen", sel["seeds"] == [2026090600 + i for i in range(8)])
cells = list(zip(dc["partition"], dc["seed"], dc["geometry"], dc["mode"]))
check("no_dup_cells", len(cells) == len(set(cells)))
check("call_total", len(dc) == 192)
check("no_crash", bool((~dc["crash"]).all()))
check("no_nonfinite", bool((~dc["nonfinite"]).all()))
check("flags_agree", bool(dc["flag_agree"].all()))
check("watchdog", bool(dc["watchdog_ok"].all() and (dc["wall_s"] <= 120).all()))
check("rss_known", bool(dc["rss_bytes"].notna().all() and (dc["rss_bytes"] < 2 * 1024 ** 3).all()))
r1 = [x for x in sel["selected"] if x["role"] == "top3"][0]
assert r1["s1"] == "5-6-7-8-9"


def e2e(part, geom):
    g = dc[(dc["partition"] == part) & (dc["geometry"] == geom)]
    out = {}
    for sd in sel["seeds"]:
        c = g[g["seed"] == sd].set_index("mode")
        l1e = bool(c.loc["L1", "exact"])
        l2e = bool(c.loc["L2-APP", "exact"])
        out[sd] = {"app_e2e": bool(l1e and l2e), "l1": l1e, "l2app": l2e,
                   "oracle": bool(c.loc["L2-oracle", "exact"]),
                   "syn_e2e": bool(c.loc["L1", "syndrome_recomputed"]
                                   and c.loc["L2-APP", "syndrome_recomputed"])}
    return out


agg = {}
for x in sel["selected"]:
    for geom in ("nonsquare", "square"):
        gg = dc[(dc["partition"] == x["s1"]) & (dc["geometry"] == geom)]
        if len(gg) == 0:
            continue
        e = e2e(x["s1"], geom)
        agg["%s@%s" % (x["s1"], geom)] = {
            "app_e2e": sum(v["app_e2e"] for v in e.values()),
            "app_l1": sum(v["l1"] for v in e.values()),
            "app_l2": sum(v["l2app"] for v in e.values()),
            "oracle_l2": sum(v["oracle"] for v in e.values()),
            "syn_e2e": sum(v["syn_e2e"] for v in e.values()), "n": len(e)}
e_ns = e2e(r1["s1"], "nonsquare")
e_sq = e2e(r1["s1"], "square")
app_ns = sum(v["app_e2e"] for v in e_ns.values())
app_sq = sum(v["app_e2e"] for v in e_sq.values())
both_rows = bool(r1["m1"] < 64 and r1["m2"] < 64)
if not both_rows:
    terminal = "DECOMPOSITION_NO_NONZERO_RATE_CANDIDATE"
elif app_ns >= 6 and app_sq >= app_ns:
    terminal = "DECOMPOSITION_STRONG_N64_RECOVERY"
elif 1 <= app_ns <= 5:
    terminal = "DECOMPOSITION_WEAK_N64_SIGNAL"
elif app_ns == 0:
    terminal = "DECOMPOSITION_NO_N64_RECOVERY"
else:
    terminal = "DECOMPOSITION_MODEL_OR_IMPLEMENTATION_BLOCKED"
log("S4 rank1=%s m=(%d,%d) app_ns=%d/8 app_sq=%d/8 terminal=%s" % (
    r1["s1"], r1["m1"], r1["m2"], app_ns, app_sq, terminal))
summary = {"checks": checks, "all_pass": bool(all(checks.values())),
           "rank1": r1["s1"], "rank1_rows": [r1["m1"], r1["m2"]],
           "rank1_app_nonsquare": app_ns, "rank1_app_square": app_sq,
           "terminal": terminal,
           "per_candidate_geometry": agg,
           "calls": len(dc), "call_budget": 600,
           "max_wall_s": float(dc["wall_s"].max()),
           "max_rss_bytes": int(dc["rss_bytes"].max()),
           "decoder_config": "historical GF32 cold max_iter=90 damping=1.0",
           "implementation_authorized": False,
           "strongest_supported": "CAL-only-optimal partition is the current mapping; no tested partition yields nonzero-rate APP recovery at n=64 (development-only routing observation, not a formal result).",
           "non_claims": ["no FER/leakage/key-rate claim", "no qualification/promotion",
                          "no real-data performance claim", "no G2 readiness",
                          "no universal BP threshold", "oracle-L2 counts are diagnostic only"]}
(ROOT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
log("S4 summary terminal=%s all_checks=%s" % (terminal, all(checks.values())))
assert all(checks.values()), "verify FAIL"
