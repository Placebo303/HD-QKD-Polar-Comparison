"""D5 decomposition successor S2: decoder-blind freeze of top-3 + controls.

Reads ONLY partition_scores.csv (CAL-only scalars). Applies the frozen
lexicographic rule (max(CE_L1,CE_L2) -> CE_joint -> CE_L1 -> S1). Writes
selected_partitions.json BEFORE any decoder call. No decoder import.
"""
import json
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


df = pd.read_csv(ROOT / "partition_scores.csv")
assert len(df) == 252 and df["s1"].nunique() == 252
assert (df["chain_max_abs_err"] < 1e-9).all()
df = df.copy()
df["max_ce"] = df[["ce_l1", "ce_l2"]].max(axis=1)
ordered = df.sort_values(["max_ce", "ce_joint", "ce_l1", "s1"],
                         ascending=[True, True, True, True]).reset_index(drop=True)
top3 = list(ordered.head(3)["s1"])
controls = ["5-6-7-8-9", "0-1-2-3-4"]
assert set(controls) <= set(df["s1"])
frozen = []
for s in top3 + controls:
    if s not in frozen:
        frozen.append(s)
sel = df.set_index("s1").loc[frozen].reset_index()
rows = []
for _, r in sel.iterrows():
    rows.append({"s1": r["s1"], "rank": int(ordered[ordered["s1"] == r["s1"]].index[0]) + 1,
                 "ce_l1": float(r["ce_l1"]), "ce_l2": float(r["ce_l2"]),
                 "ce_joint": float(r["ce_joint"]), "m1": int(r["m1"]), "m2": int(r["m2"]),
                 "eligible": bool(r["eligible"]),
                 "role": "top3" if r["s1"] in top3 else "control"})
elig = [x for x in rows if x["eligible"]]
m1star = max([59] + [x["m1"] for x in elig])
m2star = max([59] + [x["m2"] for x in elig])
assert m1star < 64 and m2star < 64 or not elig
out = {"frozen_rule": "lexicographic (max(CE_L1,CE_L2), CE_joint, CE_L1, S1) ascending",
       "decoder_blind": True, "n_scored": 252,
       "selected": rows,
       "mothers": {"l1": "build_dv3_nested_mother(64,%d,%d,2026090501)" % (m1star, m1star),
                   "l2": "build_dv3_nested_mother(64,%d,%d,2026090502)" % (m2star, m2star),
                   "square": "build_dv3_nested_mother(64,64,64,2026090801)",
                   "M1": m1star, "M2": m2star},
       "seeds": [2026090600, 2026090601, 2026090602, 2026090603,
                 2026090604, 2026090605, 2026090606, 2026090607]}
(ROOT / "selected_partitions.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
for x in rows:
    log("S2 frozen role=%s rank=%d s1=%s ce=(%.6f,%.6f) joint=%.6f m=(%d,%d) elig=%s" % (
        x["role"], x["rank"], x["s1"], x["ce_l1"], x["ce_l2"], x["ce_joint"],
        x["m1"], x["m2"], x["eligible"]))
log("S2 mothers M1=%d M2=%d decoder_calls_so_far=0" % (m1star, m2star))
