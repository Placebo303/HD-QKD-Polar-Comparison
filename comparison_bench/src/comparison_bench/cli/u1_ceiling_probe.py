"""U1 ceiling probe (Packet F, EXPLORE, implementation-only).

Arithmetic over already-persisted M0 ``rows.json`` booleans only. No raw
data, no ``.ttbin``, no bundle, no decoder. See
``docs/research_cycles/U1-CEILING-PROBE/PREREG_AND_AUTH.md`` (frozen).
"""

from __future__ import annotations

import argparse
import datetime
import json
import math
import os
import resource
import time
from pathlib import Path

N_SYM = 1024  # symbols per superframe (frozen framing, packet section 13.1)

FROZEN_ROWS = (
    "workspace/m0_359922a7_1M/rows.json",
    "workspace/m0_642a8fe8_1p5M/rows.json",
    "workspace/m0_b1a9142d_2M/rows.json",
)
FROZEN_SUMMARIES = (
    "workspace/m0_359922a7_1M/M0_RESULT_1M.md",
    "workspace/m0_642a8fe8_1p5M/M0_RESULT_1p5M.md",
    "workspace/m0_b1a9142d_2M/M0_RESULT_2M.md",
)
FROZEN_SIX = frozenset(FROZEN_ROWS + FROZEN_SUMMARIES)
FORBIDDEN_SUFFIXES = (".ttbin", ".npz", ".parquet")

SOURCE_ORDER = ("1M", "1p5M", "2M")
EXPECTED_ARMS = {"1M": (197, 201), "1p5M": (203, 207), "2M": (204, 208)}
# Frozen references carried from CHAN-QUALITY-SURVEY/RESULT.md section 3
# (packet section 2); the script reads no additional file for them.
SER_REF = {"1M": 0.23856707, "1p5M": 0.25433839, "2M": 0.25375836}
ENT_H_U1 = {"1M": 0.02415075, "1p5M": 0.02422924, "2M": 0.02491156}
ENT_H_A = {"1M": 0.79837921, "1p5M": 0.82351165, "2M": 0.82567853}

ROOT_PREFIX = "workspace/u1_probe_"
WALL_CAP_S = 600.0
RSS_CAP_GIB = 2.0

# Mechanical readings of the frozen section 5 words: section 5.2's
# "~10^-3 scale" gloss and one-order-of-magnitude reading of section 5.3's
# "same order of magnitude". Anything between falls back to section 5.1.
Q_DIFFUSE_CAP = 1e-3
ORDER_RATIO = 0.1

HEADER_BOUND = (
    "> `H(U1|B) \u2248 0.024` bits/symbol against `H(A|B) \u2248 0.826`, so u1 "
    "contributes about 2.9% of the conditional entropy. Perfect u1 can therefore "
    "reduce total disclosure by at most about 0.024 \u00d7 1024 \u2248 24.6 bits "
    "per superframe, i.e. roughly 0.03 in `f` (24.576 / (1024 \u00d7 0.826) "
    "\u2248 0.029). **Any outcome of this probe leaves option F closed as an "
    "improvement route, because this ceiling binds regardless of what the probe "
    "finds \u2014 the probe's value is diagnostic, not developmental** "
    "(\u00a75.4)."
)

CEILING_S11 = (
    "> This stage produces a bounded u1 diagnostic, nothing more. It establishes "
    "NO FER, NO efficiency, NO leakage, NO f, NO SKR and NO key figure; NO claim "
    "that u1 is or is not a bottleneck beyond the bounded statement that perfect "
    "u1 saves at most about 24.6 bits per superframe, about 0.03 in f; NO method "
    "claim of any kind; and the void HDC and void Layered-Binary figures are never "
    "used as a baseline in any form. The exact per-symbol u1 truth is not "
    "established here and belongs to a future DECIDE packet, if any."
)


def refuse(msg: str) -> None:
    raise SystemExit(f"U1-PROBE-REFUSE: {msg}")


def _norm(p: str) -> str:
    return str(p).replace("\\", "/")


def gate_paths(rows: list[str], summaries: list[str], root: str) -> None:
    """Startup input gate (packet T-PU01). No file is read here."""
    given = [_norm(p) for p in list(rows) + list(summaries)]
    for p in given:
        if p.lower().endswith(FORBIDDEN_SUFFIXES):
            refuse(f"forbidden input path: {p}")
        if p not in FROZEN_SIX:
            refuse(f"input outside the frozen six: {p}")
    if len(set(given)) != 6:
        refuse("inputs must be exactly the six frozen section-2 paths")
    r = _norm(root)
    if not r.startswith(ROOT_PREFIX):
        refuse(f"root must start with {ROOT_PREFIX}: {root}")
    if ".." in r:
        refuse(f"root must not contain '..': {root}")


def count_arm(rows: list[dict], m: int) -> dict[str, int]:
    """Frozen section-3 predicates for one arm (never pooled)."""
    n = s = d = und = 0
    for row in rows:
        if row.get("m") != m:
            continue
        for key in ("exact_match", "undetected", "full10_match"):
            if key not in row:
                refuse(f"row for m={m} misses key {key!r}")
        n += 1
        exact = row["exact_match"] is True
        undet = row["undetected"] is True
        full10 = row["full10_match"] is True
        if undet:
            und += 1
        if exact and not undet:
            s += 1
            if not full10:
                d += 1
    return {"n": n, "S": s, "D": d, "undetected": und}


def invert_q(r: float) -> float:
    """Per-symbol diffuse-error-equivalent under IID-INVERSION (section 3.3)."""
    if not 0.0 <= r <= 1.0:
        refuse(f"R outside [0,1]: {r!r}")
    return 1.0 - (1.0 - r) ** (1.0 / N_SYM)


def decide(per_arm: list[dict]) -> dict[str, str]:
    base = (" Option F stays closed as an improvement route under every outcome:"
            " the header ceiling binds regardless of what the probe finds.")
    if all(a["q"] <= Q_DIFFUSE_CAP for a in per_arm):
        return {"clause": "5.2",
                "statement": ("u1 path nearly optimal; headroom bounded by the"
                              " header ceiling; no u1 development follows."
                              + base)}
    if any(a["q_over_ser"] >= ORDER_RATIO for a in per_arm):
        return {"clause": "5.3",
                "statement": ("diagnostic anomaly: the argmax-u1 estimator is"
                              " lossy at a scale the entropy share does not"
                              " suggest; frozen table returned to main; any"
                              " follow-up (including F2-EXACT-U1) requires a new"
                              " packet and grant; no development, no estimator"
                              " change, no coding of u1." + base)}
    return {"clause": "5.1",
            "statement": ("values between the section 5.2 and 5.3 bands;"
                          " frozen table returned to main." + base)}


def _utc_mtime(path: str) -> str:
    st = os.stat(path)
    return (datetime.datetime.fromtimestamp(st.st_mtime,
                                            tz=datetime.timezone.utc)
            .strftime("%Y-%m-%d %H:%M:%S UTC"))


def main() -> int:
    ap = argparse.ArgumentParser(description="U1 ceiling probe (Packet F).")
    ap.add_argument("--rows", nargs=3, required=True)
    ap.add_argument("--summaries", nargs=3, required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--execution-authorized", action="store_true")
    args = ap.parse_args()
    if not (args.execute and args.execution_authorized):
        refuse("requires both --execute and --execution-authorized")
    gate_paths(list(args.rows), list(args.summaries), args.root)

    t_start = time.monotonic()
    root = Path(args.root)
    if root.exists():
        existing = sorted(p.name for p in root.iterdir())
        if existing != ["U1_LOG.md"]:
            refuse(f"root not fresh: {args.root} holds {existing}")
    else:
        root.mkdir(parents=True)

    def log(line: str) -> None:
        with open(root / "U1_LOG.md", "a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    def stop(msg: str) -> int:
        log(f"STOP: {msg}")
        print(f"U1-PROBE-STOP: {msg}")
        return 2

    per_arm: list[dict] = []
    inputs: list[dict] = []
    for pos, source in enumerate(SOURCE_ORDER):
        rpath = _norm(args.rows[pos])
        payload = json.loads(Path(rpath).read_text(encoding="utf-8"))
        rows = payload["rows"]
        summary = payload.get("summary", {})
        if summary.get("source") != source:
            return stop(f"summary source label {summary.get('source')!r} != {source!r}")
        arm_entries = {a["m"]: a for a in summary.get("arms", [])}
        inputs.append({"path": rpath, "bytes": os.stat(rpath).st_size,
                       "mtime_utc": _utc_mtime(rpath)})
        spath = _norm(args.summaries[pos])
        inputs.append({"path": spath, "bytes": os.stat(spath).st_size,
                       "mtime_utc": _utc_mtime(spath)})
        for m in EXPECTED_ARMS[source]:
            c = count_arm(rows, m)
            entry = arm_entries.get(m)
            if entry is None:
                return stop(f"summary entry missing for m={m}")
            fail10 = sum(1 for r in rows
                         if r.get("m") == m and r.get("full10_match") is not True)
            if c["n"] != entry.get("superframes"):
                return stop(f"summary-vs-rows superframe mismatch m={m}")
            if fail10 != entry.get("fails_full10"):
                return stop(f"summary-vs-rows fails_full10 mismatch m={m}")
            if c["S"] == 0:
                return stop(f"|S_a| = 0 for arm {source}-m{m}")
            r_rate = c["D"] / c["S"]
            q = invert_q(r_rate)
            ser = SER_REF[source]
            share = ENT_H_U1[source] / ENT_H_A[source]
            per_arm.append({"arm": f"{source}-m{m}", "source": source, "m": m,
                            "rows": c["n"], "S": c["S"], "D": c["D"],
                            "undetected_excluded": c["undetected"],
                            "R": r_rate, "q": q, "ser_ref": ser,
                            "q_over_ser": q / ser,
                            "entropy_h_u1": ENT_H_U1[source],
                            "entropy_h_a": ENT_H_A[source],
                            "entropy_share": share})

    decision = decide(per_arm)
    wall_s = time.monotonic() - t_start
    rss_gib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 ** 2)
    resources = {"wall_s": wall_s, "peak_rss_gib": rss_gib,
                 "cpus": 1, "processes": 1, "sequential": True,
                 "thread_pin_env": {k: os.environ.get(k) for k in
                                    ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                                     "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")},
                 "command": ("comparison_bench.src.comparison_bench.cli."
                             "u1_ceiling_probe --rows 3 --summaries 3 --root "
                             + _norm(args.root))}
    if wall_s > WALL_CAP_S or rss_gib > RSS_CAP_GIB:
        return stop(f"budget breach wall={wall_s:.1f}s rss={rss_gib:.3f}GiB")

    result = {"packet": "U1-CEILING-PROBE", "track": "EXPLORE",
              "inputs": inputs, "arms": per_arm,
              "decision": decision,
              "improvement_route_F": ("closed under every outcome; the header"
                                      " ceiling binds regardless"),
              "successor": ("F2-EXACT-U1 (DECIDE): exact per-symbol u1 count from"
                            " real (a,b) arrays; own packet and grant required;"
                            " not attempted here"),
              "ceilings": {"header_bound": HEADER_BOUND,
                           "claim_ceiling_s11": CEILING_S11},
              "resources": resources}
    (root / "U1_RESULT.json").write_text(json.dumps(result, indent=1) + "\n",
                                         encoding="utf-8")

    lines = ["# U1 ceiling probe — summary (Packet F, EXPLORE)", "",
             "| arm | u2 successes |S_a| | u1 disagreements |D_a| |"
             " undetected (excluded) | R_a (exact) | q_a (IID-INVERSION) |"
             " ser_ref | q_a/ser | entropy share |",
             "|---|---|---|---|---|---|---|---|---|"]
    for a in per_arm:
        lines.append(f"| {a['arm']} | {a['S']} | {a['D']} |"
                     f" {a['undetected_excluded']} | {a['R']:.6f} |"
                     f" {a['q']:.6e} | {a['ser_ref']:.8f} |"
                     f" {a['q_over_ser']:.6e} | {a['entropy_share']:.6f} |")
    lines += ["",
              "No pooling: every row above is per arm; arms and sources are"
              " never merged.",
              "",
              "IID-INVERSION weaknesses (packet section 3.3, carried): if u1"
              " errors burst within a superframe, the same R_a arises from"
              " fewer, worse superframes, so q_a overstates the typical-symbol"
              " rate and understates concentration; conditioning on u2 success"
              " may select easier superframes, in which case q_a understates"
              " the unconditional u1 error rate. A superframe-level boolean"
              " cannot by itself identify a per-symbol count: q_a is a"
              " diffuse-error-equivalent index, not a measured per-symbol count.",
              "",
              "Header bound (binding):", "", HEADER_BOUND, "",
              f"Fired clause: section {decision['clause']}:"
              f" {decision['statement']}", "",
              "Claim ceiling (verbatim, binding):", "", CEILING_S11, ""]
    (root / "U1_SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")

    log(f"EXECUTE-OK clause={decision['clause']} wall_s={wall_s:.2f}"
        f" rss_gib={rss_gib:.3f} arms={len(per_arm)}")
    print(f"FIRED-CLAUSE section {decision['clause']}: {decision['statement']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
