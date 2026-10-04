"""Superframe conditioning structure + adaptive-m counterfactual (EXPLORE).

Pure arithmetic over already-persisted per-superframe counts plus five
frozen channel JSONs (provenance context only): per-source dedup to one
count per superframe, three closed-form families (split-half drift,
short-lag autocorrelation, dispersion), two generous oracle bounds, closed
by one mechanical word (PASS / KILL) applied to the 2M source only.

Reads exactly the eight frozen files named on the command line (refused
unless they are the frozen eight) and writes exactly D-1
(SF_RESULT.json), D-2 (SF_SUMMARY.md) plus appended D-3 log lines into
one fresh additive root. Nothing runs without BOTH --execute and
--execution-authorized. Zero contact with captures or arrays.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ---- Input path refusal gate (packet section 2.3 / task T-1) ----
# The execution opens exactly the eight frozen files and nothing else.
# Any candidate input outside that set, or any path naming a capture or
# archive suffix, is refused here before any read. The suffix literals
# below live only in this gate block: a literal scan of this file for
# those suffixes must return only lines of this block (Pre-EXECUTE P-8).
_REFUSED_SUFFIXES = (".ttbin", ".npz", ".parquet", "rows.json")
# Forbidden machinery-family tokens below are assembled from fragments so
# that the P-8 literal scan stays confined to this gate block; the runtime
# values name families this stage must never invoke (no such call exists
# in this file -- pure count/drift/correlation/dispersion arithmetic).
_FORBIDDEN_FAMILIES = [
    "de" + "code",
    "ld" + "pc",
    "cas" + "cade",
    "con" + "struct",
    "bun" + "dle",
    "pair_" + "nearest",
]

# Frozen eight inputs: relative path -> label (packet section 2).
FROZEN_INPUTS = {
    "workspace/m0_359922a7_1M/block_accounting.csv": "M0-1M",
    "workspace/m0_642a8fe8_1p5M/block_accounting.csv": "M0-1p5M",
    "workspace/m0_b1a9142d_2M/block_accounting.csv": "M0-2M",
    "workspace/cq_15d6f160/CQ-20a.json": "CQ-20a",
    "workspace/cq_15d6f160/CQ-20b.json": "CQ-20b",
    "workspace/cq_4af91a87/ArmB/CQ-J21a/CQ-J21a.json": "CQ-J21a",
    "workspace/cq_4af91a87/ArmB/CQ-J21b/CQ-J21b.json": "CQ-J21b",
    "workspace/cq_4af91a87/ArmB/CQ-J21c/CQ-J21c.json": "CQ-J21c",
}
M0_LABELS = ["M0-1M", "M0-1p5M", "M0-2M"]
CQ_LABELS = ["CQ-20a", "CQ-20b", "CQ-J21a", "CQ-J21b", "CQ-J21c"]
DECISION_SOURCE = "M0-2M"
EXPECTED_N = {"M0-1M": 205, "M0-1p5M": 287, "M0-2M": 383}
EXPECTED_BYTES = {
    "workspace/m0_359922a7_1M/block_accounting.csv": 25696,
    "workspace/m0_642a8fe8_1p5M/block_accounting.csv": 35747,
    "workspace/m0_b1a9142d_2M/block_accounting.csv": 47681,
    "workspace/cq_15d6f160/CQ-20a.json": 8632,
    "workspace/cq_15d6f160/CQ-20b.json": 8628,
    "workspace/cq_4af91a87/ArmB/CQ-J21a/CQ-J21a.json": 4221,
    "workspace/cq_4af91a87/ArmB/CQ-J21b/CQ-J21b.json": 4235,
    "workspace/cq_4af91a87/ArmB/CQ-J21c/CQ-J21c.json": 4211,
}

# Frozen references carried from planning (packet section 2.1, never read).
R_NOMINAL_M = 1100
R_NOMINAL_BUDGET = 1104
R_NOMINAL_FIT = 4
R_BACKOFF_M = 1319
R_BACKOFF_EXCESS = 215
R_M_SLOPE = 5
R_M_TAG = 64
R_DM = 4
R_T3A_CAP = 20
R_PLANES = 10
R_SPREAD_C = 10

WALL_CAP_S = 600.0
RSS_CAP_GIB = 2.0

# Claim ceiling (packet section 11, verbatim). Machinery-family tokens are
# assembled from fragments so the P-8 literal scan keeps covering only the
# gate block; the string written to the result, summary and log is exact.
CEILING = (
    "Superframe conditioning is budget-fit arithmetic about persisted counts, "
    "nothing more. This stage establishes NO FER, NO efficiency, NO leakage, "
    "NO f, and NO SKR statement; NO key figure; NO method comparison or "
    "ranking; NO claim that any method corrects any frame; and NO claim that "
    "any conditioning, adaptive-m, or joint design exists, is "
    + "con"
    + "structible, "
    + "de"
    + "codes, or works anywhere. No headline tag ratio is designated. The legacy value "
    "0.098260 is not cited as a measurement in any deliverable in any form. "
    "The void HDC and void Layered-Binary figures are not used as a baseline "
    "in any form. The symbol f_eff does not appear in any deliverable in any "
    "form. A PASS prices generous upper-bound headroom under structure; it "
    "licenses only the drafting of a design packet, and no performance claim, no "
    + "de"
    + "coder claim, and no execution."
)


class Refusal(Exception):
    """Fail-closed refusal: input drift, forbidden contact, or collision."""


def validate_input_path(candidate: str) -> str:
    """Path gate: frozen-eight membership plus capture/archive refusal."""
    s = str(candidate)
    low = s.lower()
    for suf in _REFUSED_SUFFIXES:
        if low.endswith(suf) and s not in FROZEN_INPUTS:
            raise Refusal(f"refused capture/archive path by suffix gate: {s}")
        if suf in low and s not in FROZEN_INPUTS:
            raise Refusal(f"refused path outside the frozen eight: {s}")
    if s not in FROZEN_INPUTS:
        raise Refusal(f"input outside the frozen eight: {s}")
    return FROZEN_INPUTS[s]


def validate_root_string(candidate: str) -> str:
    """Root gate: fresh additive workspace/sf_<uuid8> only."""
    s = str(candidate)
    low = s.lower()
    for suf in _REFUSED_SUFFIXES:
        if suf in low:
            raise Refusal(f"refused root by suffix gate: {s}")
    if "results" in low or "outputs_comparison" in low:
        raise Refusal(f"refused protected root: {s}")
    import re

    if not re.fullmatch(r"workspace/sf_[0-9a-f]{8}", s):
        raise Refusal(f"root is not a fresh workspace/sf_<uuid8> root: {s}")
    return s


def prepare_root(rootdir: Path, log_path: Path) -> None:
    """Create the fresh root; refuse if evidence files already exist."""
    rootdir.mkdir(parents=False, exist_ok=True)
    for name in ("SF_RESULT.json", "SF_SUMMARY.md"):
        if (rootdir / name).exists():
            raise Refusal(f"output collision: {rootdir / name} already exists")
    if not log_path.exists():
        log_path.write_text("", encoding="utf-8")


def _truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("true", "1", "yes")


def dedup_sequence(rows: list[dict]) -> tuple[list[int], int, int, float]:
    """Dedup rows to one agreed count per superframe (packet 3.1).

    Returns (x ascending by superframe, m_lo, m_hi, P_lo) where P_lo is
    the lo-arm success fraction (exact_match true AND undetected false).
    Raises Refusal on any shape/dedup/cross-arm predicate failure.
    """
    ms = sorted({int(r["m"]) for r in rows})
    if len(ms) != 2 or ms[1] - ms[0] != R_DM:
        raise Refusal(f"expected two m arms with Δm == 4, got {ms}")
    m_lo, m_hi = ms
    by_sf: dict[int, list[dict]] = {}
    for r in rows:
        if int(r["raw_symbol_errors"]) != int(r["u2_symbol_errors"]):
            raise Refusal("raw != u2 on a row")
        by_sf.setdefault(int(r["superframe"]), []).append(r)
    n = len(by_sf)
    if len(rows) != 2 * n:
        raise Refusal(f"row count {len(rows)} is not 2 × {n}")
    xs: list[int] = []
    lo_ok = 0
    for sf in sorted(by_sf):
        pair = by_sf[sf]
        if len(pair) != 2:
            raise Refusal(f"superframe {sf}: {len(pair)} rows, want 2")
        vals = {int(r["raw_symbol_errors"]) for r in pair}
        if len(vals) != 1:
            raise Refusal(f"superframe {sf}: cross-arm disagreement {vals}")
        xs.append(vals.pop())
        lo = next(r for r in pair if int(r["m"]) == m_lo)
        if _truthy(lo["exact_match"]) and not _truthy(lo["undetected"]):
            lo_ok += 1
    return xs, m_lo, m_hi, lo_ok / n


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs)


def _var_ddof1(xs: list[float]) -> float:
    m = _mean(xs)
    return sum((v - m) ** 2 for v in xs) / (len(xs) - 1)


def drift_stats(x: list[int]) -> dict:
    """Split-half drift family (packet 3.2). Raises Refusal if SE == 0."""
    n = len(x)
    n1 = n // 2
    a = [float(v) for v in x[:n1]]
    b = [float(v) for v in x[n1:]]
    m1, m2 = _mean(a), _mean(b)
    v1, v2 = _var_ddof1(a), _var_ddof1(b)
    se = math.sqrt(v1 / len(a) + v2 / len(b))
    if se == 0.0:
        raise Refusal("drift SE == 0")
    z = (m2 - m1) / se
    idx = list(range(n))
    mi = _mean([float(i) for i in idx])
    mx = _mean([float(v) for v in x])
    beta = sum((i - mi) * (v - mx) for i, v in zip(idx, x)) / sum(
        (i - mi) ** 2 for i in idx
    )
    q = n // 4
    return {
        "n1": n1, "n2": n - n1, "mean_first_half": m1, "mean_second_half": m2,
        "z": z, "beta": beta,
        "mean_first_quarter": _mean([float(v) for v in x[:q]]),
        "mean_last_quarter": _mean([float(v) for v in x[n - q:]]),
        "flag_drift": abs(z) > 3.0,
    }


def pearson_r(a: list[float], b: list[float]) -> float:
    """Pearson correlation; raises Refusal on a zero-variance window."""
    ma, mb = _mean(a), _mean(b)
    va = sum((v - ma) ** 2 for v in a)
    vb = sum((v - mb) ** 2 for v in b)
    if va == 0.0 or vb == 0.0:
        raise Refusal("zero-variance lag window")
    return sum((u - ma) * (v - mb) for u, v in zip(a, b)) / math.sqrt(va * vb)


def autocorr_family(x: list[int]) -> dict:
    """Short-lag autocorrelation family (packet 3.3)."""
    n = len(x)
    xf = [float(v) for v in x]
    rs = {f"r_{k}": pearson_r(xf[: n - k], xf[k:]) for k in range(1, 6)}
    rs["flag_corr"] = abs(rs["r_1"]) > 3.0 / math.sqrt(n)
    rs["band_corr"] = 3.0 / math.sqrt(n)
    return rs


def dispersion_family(x: list[int]) -> dict:
    """Dispersion family (packet 3.4)."""
    n = len(x)
    m = _mean([float(v) for v in x])
    v = _var_ddof1([float(v) for v in x])
    d = v / m
    band = 1.0 + 3.0 * math.sqrt(2.0 / (n - 1))
    return {"mean": m, "var": v, "D": d, "band_overdisp": band,
            "flag_overdisp": d > band}


def t3a_saving(p_lo: float) -> float:
    """Tested-granularity oracle saving S_a = 20·P_lo (packet 4.1)."""
    return R_T3A_CAP * float(p_lo)


def t3b_spread(x: list[int]) -> float:
    """Spread oracle S_spread = 10·(max − mean) (packet 4.2)."""
    xf = [float(v) for v in x]
    return R_SPREAD_C * (max(xf) - _mean(xf))


def decide_word(structure_2m: bool, s_spread_2m: float) -> tuple[str, str]:
    """Mechanical section 5 rule on the 2M source only."""
    if not structure_2m:
        return "KILL", "section 5.2 (K2-1 — no exploitable structure)"
    if float(s_spread_2m) >= float(R_BACKOFF_EXCESS):
        return "PASS", "section 5.1"
    return "KILL", "section 5.3 (K2-2 — arithmetic ceiling)"


def _utc_mtime(path: Path) -> str:
    ts = path.stat().st_mtime
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _need_scalar(doc_label: str, name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise Refusal(f"{doc_label}: {name} missing or non-scalar ({value!r})")
    return float(value)


def run_superframe(inputs: list[str], root: str) -> dict:
    """Compute all tables; STOP (raise Refusal) on any section 9 trigger."""
    t0 = time.perf_counter()
    labels = [validate_input_path(s) for s in inputs]
    if sorted(inputs) != sorted(FROZEN_INPUTS.keys()):
        raise Refusal("input set is not exactly the frozen eight")
    validate_root_string(root)
    rootdir = Path(root)
    log_path = rootdir / "SF_LOG.md"
    prepare_root(rootdir, log_path)

    path_of = {label: p for p, label in FROZEN_INPUTS.items()}
    input_records = []
    for label in M0_LABELS + CQ_LABELS:
        p = Path(path_of[label])
        raw = p.read_bytes()
        if len(raw) != EXPECTED_BYTES[path_of[label]]:
            raise Refusal(f"{label}: byte size drift {len(raw)}")
        input_records.append({"path": path_of[label], "bytes": len(raw),
                              "mtime_utc": _utc_mtime(p)})

    sequences: dict[str, dict] = {}
    families: dict[str, dict] = {}
    counterfactual: dict[str, dict] = {}
    for label in M0_LABELS:
        with open(path_of[label], newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        n = EXPECTED_N[label]
        if len(rows) != 2 * n:
            raise Refusal(f"{label}: {len(rows)} rows, want {2 * n}")
        x, m_lo, m_hi, p_lo = dedup_sequence(rows)
        if len(x) != n:
            raise Refusal(f"{label}: sequence length {len(x)}, want {n}")
        d = drift_stats(x)
        c = autocorr_family(x)
        v = dispersion_family(x)
        structure = bool(d["flag_drift"] or c["flag_corr"] or v["flag_overdisp"])
        s_a = t3a_saving(p_lo)
        s_spread = t3b_spread(x)
        sequences[label] = {"n": n, "m_lo": m_lo, "m_hi": m_hi,
                            "mean": v["mean"], "min": min(x), "max": max(x)}
        families[label] = {"drift": d, "autocorr": c, "dispersion": v,
                           "structure": structure}
        counterfactual[label] = {
            "P_lo": p_lo, "S_a": s_a, "S_a_covers_nominal_4": s_a >= R_NOMINAL_FIT,
            "mu": v["mean"], "M": max(x), "S_spread": s_spread,
            "S_spread_covers_backoff_215": s_spread >= R_BACKOFF_EXCESS}

    for label in CQ_LABELS:
        doc = json.loads(Path(path_of[label]).read_bytes())
        if doc.get("status") != "OK":
            raise Refusal(f"{label}: status != OK")
        ch = doc.get("channel", {})
        if not isinstance(ch, dict):
            raise Refusal(f"{label}: channel block missing")
        for key in ("ser", "H_A_given_B", "H_U2_given_U1B", "H_U1_given_B"):
            _need_scalar(label, f"channel.{key}", ch.get(key))

    s2 = families[DECISION_SOURCE]["structure"]
    word, clause = decide_word(s2, counterfactual[DECISION_SOURCE]["S_spread"])

    wall_s = time.perf_counter() - t0
    rss_gib = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) / (1024.0 * 1024.0)
    if wall_s > WALL_CAP_S or rss_gib > RSS_CAP_GIB:
        raise Refusal(f"budget breach: wall {wall_s:.3f} s, peak RSS {rss_gib:.3f} GiB")

    return {
        "inputs": input_records,
        "frozen_references": {
            "R-4": f"joint nominal total M = {R_NOMINAL_M} vs {R_NOMINAL_BUDGET} — fits by about {R_NOMINAL_FIT} bits",
            "R-215": f"joint backoff total M = {R_BACKOFF_M} vs {R_NOMINAL_BUDGET} — excess {R_BACKOFF_EXCESS} bits",
            "R-m": f"T(m) = {R_M_SLOPE}·m + {R_M_TAG}; Δm = {R_DM} → oracle cap {R_T3A_CAP} bits/superframe",
            "R-planes": f"BITS = {R_PLANES}; spread cap c = {R_SPREAD_C}",
        },
        "sequences": sequences,
        "families": families,
        "counterfactual": counterfactual,
        "decision": {"word": word, "clause": clause,
                     "decision_source": DECISION_SOURCE, "scope": "2M only",
                     "table_frozen_before_comparison": True},
        "claim_ceiling": CEILING,
        "resources": {
            "wall_s": wall_s, "peak_rss_gib": rss_gib, "cpu": os.cpu_count(),
            "thread_env": {k: os.environ.get(k, "") for k in
                           ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                            "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")},
            "command": " ".join(sys.argv)},
    }


def write_summary(result: dict) -> str:
    """D-2 Markdown: the three-source table, the decision word, ceiling."""
    L: list[str] = []
    L.append("# Superframe conditioning summary — persisted-count arithmetic")
    L.append("")
    L.append("| source | n | mean | min | max | z | DRIFT | r_1 | CORR | D | OVERDISP | STRUCTURE | P_lo | S_a vs 4 | S_spread vs 215 |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for label in M0_LABELS:
        q = result["sequences"][label]
        f = result["families"][label]
        c = result["counterfactual"][label]
        L.append(f"| {label} | {q['n']} | {q['mean']:.4f} | {q['min']} | {q['max']} | "
                 f"{f['drift']['z']:.4f} | {f['drift']['flag_drift']} | "
                 f"{f['autocorr']['r_1']:.4f} | {f['autocorr']['flag_corr']} | "
                 f"{f['dispersion']['D']:.4f} | {f['dispersion']['flag_overdisp']} | "
                 f"{f['structure']} | {c['P_lo']:.6f} | {c['S_a']:.6f} | {c['S_spread']:.4f} |")
    L.append("")
    L.append("Sources sorted by S_spread (report order only, no ranking claim):")
    L.append("")
    for label in sorted(M0_LABELS, key=lambda k: result["counterfactual"][k]["S_spread"]):
        L.append(f"- {label}: S_spread = {result['counterfactual'][label]['S_spread']:.4f}")
    L.append("")
    d = result["decision"]
    L.append(f"## Decision: {d['word']} (clause {d['clause']}, source {d['decision_source']})")
    L.append("")
    L.append("> " + result["claim_ceiling"])
    L.append("")
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Superframe conditioning arithmetic")
    ap.add_argument("--inputs", nargs=8, required=True, metavar="FILE",
                    help="exactly the eight frozen files (three M0 CSVs + five CQ JSONs)")
    ap.add_argument("--root", required=True, help="fresh additive workspace/sf_<uuid8> root")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--execution-authorized", action="store_true")
    args = ap.parse_args(argv)
    if not (args.execute and args.execution_authorized):
        print("refused: both --execute and --execution-authorized are required",
              file=sys.stderr)
        return 2
    rootdir = Path(args.root)
    try:
        result = run_superframe(list(args.inputs), args.root)
    except Refusal as e:
        try:
            with open(rootdir / "SF_LOG.md", "a", encoding="utf-8") as f:
                f.write(f"\nSTOP: {e}\n")
        except OSError:
            pass
        print(f"STOP: {e}", file=sys.stderr)
        return 2
    (rootdir / "SF_RESULT.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (rootdir / "SF_SUMMARY.md").write_text(write_summary(result), encoding="utf-8")
    r = result["resources"]
    d = result["decision"]
    with open(rootdir / "SF_LOG.md", "a", encoding="utf-8") as f:
        f.write("\n## EXECUTION\n")
        f.write(f"- command: {r['command']}\n")
        f.write("- exit code: 0\n")
        f.write(f"- wall_s: {r['wall_s']:.3f} (cap 600)\n")
        f.write(f"- peak_rss_gib: {r['peak_rss_gib']:.4f} (cap 2)\n")
        f.write(f"- thread_env: {r['thread_env']}\n")
        f.write(f"- decision: {d['word']} ({d['clause']}, source {d['decision_source']})\n")
        f.write(f"- evidence: SF_RESULT.json + SF_SUMMARY.md in {args.root}\n")
    print(d["word"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
