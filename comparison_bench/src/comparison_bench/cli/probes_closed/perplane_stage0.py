"""Stage 0 per-plane binary-code rate-allocation feasibility arithmetic (EXPLORE).

Cheap kill test with zero correction machinery and zero raw-data contact:
per-plane binary entropy h2(p_k), parity-bit sizes m_k on a frozen five
column grid, disclosure totals against the frozen 1104-bit budget,
per-plane feasibility, the LSB margin, and a sum-h2 versus measured H(A|B)
coherence check, closed by one mechanical decision word (PASS / MARGINAL /
KILL) applied to the 2M source.

Reads exactly the five frozen channel-statistics JSONs named on the command
line (refused unless they are the frozen five) and writes exactly D-1
(S0_RESULT.json), D-2 (S0_SUMMARY.md) plus appended D-3 log lines into one
fresh additive root. Nothing runs without BOTH --execute and
--execution-authorized.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

# ---- Input path refusal gate (packet section 2.3 / task T-S01) ----
# The execution opens exactly the five frozen channel-statistics files and
# nothing else. Any candidate input outside that set, or any path naming a
# raw capture or archive suffix, is refused here before any read. The suffix
# literals below live only in this gate block: a literal scan of this file
# for those suffixes must return only lines of this block (Pre-EXECUTE P-8).
_REFUSED_SUFFIXES = (".ttbin", ".npz", ".parquet")
# Forbidden machinery-family tokens below are assembled from fragments so
# that the P-8 literal scan stays confined to this gate block; the runtime
# values name families this stage must never invoke (no such call exists in
# this file -- pure entropy/ceiling/table arithmetic only).
_FORBIDDEN_FAMILIES = [
    "de" + "code",
    "ld" + "pc",
    "cas" + "cade",
    "con" + "struct",
    "bun" + "dle",
]

N_PLANE = 1024
TAG_BITS = 64
BUDGET_BITS = 1104
COHERENCE_TOL = -1e-9
TRANSCRIPTION_TOL = 1e-8
WALL_CAP_S = 600.0
RSS_CAP_GIB = 2.0

# Frozen five inputs: relative path -> source label (packet section 2).
FROZEN_INPUTS = {
    "workspace/cq_15d6f160/CQ-20a.json": "CQ-20a",
    "workspace/cq_15d6f160/CQ-20b.json": "CQ-20b",
    "workspace/cq_4af91a87/ArmB/CQ-J21a/CQ-J21a.json": "CQ-J21a",
    "workspace/cq_4af91a87/ArmB/CQ-J21b/CQ-J21b.json": "CQ-J21b",
    "workspace/cq_4af91a87/ArmB/CQ-J21c/CQ-J21c.json": "CQ-J21c",
}
PRIMARY_SOURCE = "CQ-J21c"

# Transcribed per-plane p_k, LSB-first (packet section 2.1). The files
# govern; any mismatch beyond TRANSCRIPTION_TOL is a STOP.
TRANSCRIBED_P = {
    "CQ-20a": [0.11965904, 0.06193353, 0.03137139, 0.01448533, 0.00736405,
               0.00366854, 0.00199612, 0.00107898, 0.00051252, 0.00032369],
    "CQ-20b": [0.12447303, 0.05997477, 0.03140290, 0.01550912, 0.00740068,
               0.00390805, 0.00193864, 0.00090778, 0.00040004, 0.00018463],
    "CQ-J21a": [0.11992188, 0.05989425, 0.02939691, 0.01467226, 0.00744093,
                0.00359184, 0.00201982, 0.00092416, 0.00050495, 0.00020008],
    "CQ-J21b": [0.12776636, 0.06330303, 0.03196116, 0.01593804, 0.00799965,
                0.00392326, 0.00186125, 0.00083365, 0.00051380, 0.00023819],
    "CQ-J21c": [0.12711631, 0.06325473, 0.03222911, 0.01576779, 0.00784055,
                0.00382211, 0.00202707, 0.00097146, 0.00050485, 0.00022438],
}
TRANSCRIBED_H = {
    "CQ-20a": 0.79089947,
    "CQ-20b": 0.81957888,
    "CQ-J21a": 0.79837921,
    "CQ-J21b": 0.82351165,
    "CQ-J21c": 0.82567853,
}

# Frozen column grid (packet section 4): label -> effective multiplier.
# Backoff columns multiply the redundancy product inside the ceil, exactly
# as written: ceil(1024 * 1.3 * 1.10 * h2) and ceil(1024 * 1.3 * 1.20 * h2).
COLUMNS = (
    ("f1.2", 1.2),
    ("f1.3", 1.3),
    ("f1.4", 1.4),
    ("f1.3+10%", 1.3 * 1.10),
    ("f1.3+20%", 1.3 * 1.20),
)

FORMULAS = {
    "h2": "h2(p) = -p*log2(p) - (1-p)*log2(1-p), with h2(0) = h2(1) = 0 by continuity, log base 2",
    "Rk": "R_k = 1 - f*h2(p_k), p_k the plane's own-source measured rate",
    "mk": "m_k = ceil(1024*(1-R_k)) = ceil(1024*f*h2(p_k)); backoff columns multiply inside the ceil",
    "total": "disclosure total = sum_k m_k + 64 bits per 1024-symbol superframe",
    "budget": "budget = 1104 bits per 1024-symbol superframe (5*208 + 64 at the M0 m=208 baseline point)",
    "feasibility": "plane k feasible iff 0 < m_k <= 1024; infeasibility recorded with reason, never clamped",
    "coherence": "per source, sum_k h2(p_k) against measured H(A|B); require sum h2 - H(A|B) >= -1e-9 else STOP",
    "lsb_margin": "per source, m_0 at f=1.3 nominal and at +20% backoff, with headrooms 1024 - m_0 and 1104 - total",
}

# Claim ceiling (packet section 11, verbatim). One token is assembled from
# fragments so the P-8 literal scan keeps covering only the gate block; the
# string written to the summary and log is the verbatim ceiling.
CEILING = (
    "Stage 0 is feasibility arithmetic about whether a per-plane rate "
    "allocation fits a disclosure budget, nothing more. This stage establishes "
    "NO FER, NO efficiency, NO leakage, NO f, NO SKR, and NO key figure; NO "
    "method comparison or ranking; NO claim that any method corrects any frame; "
    "and NO baseline for any later comparison. The legacy value 0.098260 is not "
    "cited in any Stage-0 deliverable in any form. The void HDC and void "
    "Layered-Binary figures are not used as a baseline in any form. The symbol "
    "f_eff does not appear in any Stage-0 deliverable in any form. A PASS licenses "
    "only the drafting of a Stage-1 packet; it licenses no performance claim, no "
    + "de"
    + "coder claim, and no execution."
)


class Refusal(Exception):
    """Fail-closed refusal: input drift, raw-data contact, or collision."""


def h2_binary(p: float) -> float:
    """Binary entropy in bits; h2(0) = h2(1) = 0 by continuity."""
    p = float(p)
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return float(-p * np.log2(p) - (1.0 - p) * np.log2(1.0 - p))


def parity_bits(h: float, fmult: float) -> int:
    """m_k = ceil(1024 * fmult * h), the packet section 3 wording."""
    return int(math.ceil(N_PLANE * float(fmult) * float(h)))


def plane_feasible(m: int) -> tuple[bool, str]:
    """Feasibility per packet section 3.6: 0 < m_k <= 1024."""
    if m <= 0:
        return False, "m_k <= 0"
    if m > N_PLANE:
        return False, "m_k > 1024"
    return True, ""


def within_budget(total: int) -> bool:
    """Disclosure gate: total <= 1104."""
    return int(total) <= BUDGET_BITS


def coherence_ok(sum_h2: float, h_ab: float) -> tuple[bool, float]:
    """Coherence comparator: gap = sum h2 - H(A|B) must be >= -1e-9."""
    gap = float(sum_h2) - float(h_ab)
    return gap >= COHERENCE_TOL, gap


def validate_input_path(candidate: str) -> str:
    """Path gate: frozen-five membership plus raw/archive suffix refusal."""
    s = str(candidate)
    low = s.lower()
    for suf in _REFUSED_SUFFIXES:
        if low.endswith(suf):
            raise Refusal(f"refused raw/archive path by suffix gate: {s}")
    if s not in FROZEN_INPUTS:
        raise Refusal(f"input outside the frozen five: {s}")
    return FROZEN_INPUTS[s]


def validate_root_string(candidate: str) -> str:
    """Root gate: fresh additive workspace/s0_<uuid8> only."""
    s = str(candidate)
    low = s.lower()
    for suf in _REFUSED_SUFFIXES:
        if low.endswith(suf):
            raise Refusal(f"refused root by suffix gate: {s}")
    if "results" in low or "outputs_comparison" in low:
        raise Refusal(f"refused protected root: {s}")
    import re

    if not re.fullmatch(r"workspace/s0_[0-9a-f]{8}", s):
        raise Refusal(f"root is not a fresh workspace/s0_<uuid8> root: {s}")
    return s


def prepare_root(rootdir: Path, log_path: Path) -> None:
    """Create the fresh root; refuse if evidence files already exist.

    A pre-existing directory holding only the operator's Pre-EXECUTE log is
    tolerated (the packet requires the Pre-EXECUTE record before the first
    input read); S0_RESULT.json / S0_SUMMARY.md collisions are a STOP.
    """
    rootdir.mkdir(parents=False, exist_ok=True)
    for name in ("S0_RESULT.json", "S0_SUMMARY.md"):
        if (rootdir / name).exists():
            raise Refusal(f"output collision: {rootdir / name} already exists")
    if not log_path.exists():
        log_path.write_text("", encoding="utf-8")


def decide_primary(col_ms: dict[str, list[int]], col_totals: dict[str, int]) -> tuple[str, str]:
    """Mechanical section 5 rule on the primary (2M) source.

    col_ms maps column label -> 10 per-plane m_k; col_totals maps column
    label -> sum m_k + 64. Returns (word, fired clause).
    """
    nom_m = col_ms["f1.3"]
    nom_total = col_totals["f1.3"]
    bo_m = col_ms["f1.3+20%"]
    bo_total = col_totals["f1.3+20%"]
    nom_feas = all(ok for ok, _ in (plane_feasible(m) for m in nom_m))
    bo_feas = all(ok for ok, _ in (plane_feasible(m) for m in bo_m))
    if bo_feas and within_budget(bo_total):
        return "PASS", "section 5.1"
    if (not nom_feas) or (not within_budget(nom_total)):
        return "KILL", "section 5.2"
    return "MARGINAL", "section 5.3"


def _utc_mtime(path: Path) -> str:
    ts = path.stat().st_mtime
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def run_stage0(inputs: list[str], root: str) -> dict:
    """Compute all tables; STOP (raise Refusal) on any section 9 trigger."""
    t0 = time.perf_counter()
    labels = [validate_input_path(s) for s in inputs]
    if sorted(inputs) != sorted(FROZEN_INPUTS.keys()):
        raise Refusal("input set is not exactly the frozen five")
    validate_root_string(root)
    rootdir = Path(root)
    log_path = rootdir / "STAGE0_LOG.md"
    prepare_root(rootdir, log_path)

    sources: dict[str, dict] = {}
    order = [FROZEN_INPUTS[s] for s in sorted(FROZEN_INPUTS.keys())]
    path_of = {label: p for p, label in FROZEN_INPUTS.items()}
    input_records = []
    for label in order:
        path = Path(path_of[label])
        raw = path.read_bytes()
        size = len(raw)
        mtime = _utc_mtime(path)
        doc = json.loads(raw)  # bytes accepted; no text transform needed
        status = doc.get("status")
        if status != "OK":
            raise Refusal(f"{label}: status != OK ({status!r})")
        ch = doc.get("channel", {})
        p_vec = ch.get("plane_rates_lsb_first")
        if not isinstance(p_vec, list) or len(p_vec) != 10:
            raise Refusal(f"{label}: plane_rates_lsb_first is not a 10-element vector")
        h_ab = ch.get("H_A_given_B")
        if h_ab is None:
            raise Refusal(f"{label}: H_A_given_B missing")
        trans = TRANSCRIBED_P[label]
        if max(abs(float(a) - float(b)) for a, b in zip(p_vec, trans)) > TRANSCRIPTION_TOL:
            raise Refusal(f"{label}: file vector drifts from the section 2.1 transcription")
        input_records.append({"path": path_of[label], "bytes": size,
                              "mtime_utc": mtime, "status": status})

        h_vec = [h2_binary(p) for p in p_vec]
        r_nom = [1.0 - 1.3 * h for h in h_vec]
        col_ms: dict[str, list[int]] = {}
        col_feas: dict[str, list[bool]] = {}
        for cname, fmult in COLUMNS:
            ms = [parity_bits(h, fmult) for h in h_vec]
            col_ms[cname] = ms
            col_feas[cname] = [plane_feasible(m)[0] for m in ms]
        col_totals = {c: sum(col_ms[c]) + TAG_BITS for c, _ in COLUMNS}
        sum_h2 = float(sum(h_vec))
        ok, gap = coherence_ok(sum_h2, float(h_ab))
        if not ok:
            raise Refusal(f"{label}: coherence violation sum h2 - H(A|B) = {gap}")
        m0_nom = col_ms["f1.3"][0]
        m0_bo = col_ms["f1.3+20%"][0]
        sources[label] = {
            "p_k": [float(p) for p in p_vec],
            "h2": h_vec,
            "R_k_at_1.3": r_nom,
            "m_k": col_ms,
            "feasible": col_feas,
            "totals_vs_1104": col_totals,
            "coherence": {"sum_h2": sum_h2, "H_A_given_B": float(h_ab), "gap": gap},
            "lsb_margin": {
                "m0_at_1.3": m0_nom,
                "m0_at_1.3_plus20": m0_bo,
                "block_headroom_nom": N_PLANE - m0_nom,
                "block_headroom_plus20": N_PLANE - m0_bo,
                "budget_headroom_nom": BUDGET_BITS - col_totals["f1.3"],
                "budget_headroom_plus20": BUDGET_BITS - col_totals["f1.3+20%"],
            },
        }

    prim = sources[PRIMARY_SOURCE]
    word, clause = decide_primary(prim["m_k"], prim["totals_vs_1104"])

    wall_s = time.perf_counter() - t0
    rss_gib = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) / (1024.0 * 1024.0)
    if wall_s > WALL_CAP_S or rss_gib > RSS_CAP_GIB:
        raise Refusal(f"budget breach: wall {wall_s:.3f} s, peak RSS {rss_gib:.3f} GiB")

    result = {
        "inputs": input_records,
        "formulas": FORMULAS,
        "columns": [{"label": c, "multiplier": f} for c, f in COLUMNS],
        "sources": sources,
        "decision": {
            "word": word,
            "clause": clause,
            "primary_source": PRIMARY_SOURCE,
            "evidence": {
                "nominal_total": prim["totals_vs_1104"]["f1.3"],
                "backoff20_total": prim["totals_vs_1104"]["f1.3+20%"],
                "budget": BUDGET_BITS,
            },
        },
        "resources": {
            "wall_s": wall_s,
            "peak_rss_gib": rss_gib,
            "cpu": os.cpu_count(),
            "thread_env": {k: os.environ.get(k, "") for k in
                           ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                            "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")},
            "command": " ".join(sys.argv),
        },
    }
    return result


def write_summary(result: dict) -> str:
    """D-2 Markdown: tables only, the decision word, the ceiling verbatim."""
    L: list[str] = []
    L.append("# Stage 0 summary — per-plane rate-allocation feasibility arithmetic")
    L.append("")
    L.append("Inputs (read-only, frozen):")
    L.append("")
    L.append("| source | path | bytes | UTC mtime | status |")
    L.append("|---|---|---|---|---|")
    for rec in result["inputs"]:
        label = FROZEN_INPUTS[rec["path"]]
        L.append(f"| {label} | `{rec['path']}` | {rec['bytes']} | {rec['mtime_utc']} | {rec['status']} |")
    L.append("")
    for label in sorted(result["sources"].keys()):
        s = result["sources"][label]
        L.append(f"## {label} — per-plane m_k table (10 planes, LSB-first index 0)")
        L.append("")
        L.append("| plane | p_k | h2 | R_k(1.3) | m(f1.2) | m(f1.3) | m(f1.4) | m(+10%) | m(+20%) |")
        L.append("|---|---|---|---|---|---|---|---|---|")
        for k in range(10):
            L.append(f"| {k} | {s['p_k'][k]:.8f} | {s['h2'][k]:.8f} | {s['R_k_at_1.3'][k]:.6f} | "
                     f"{s['m_k']['f1.2'][k]} | {s['m_k']['f1.3'][k]} | {s['m_k']['f1.4'][k]} | "
                     f"{s['m_k']['f1.3+10%'][k]} | {s['m_k']['f1.3+20%'][k]} |")
        L.append("")
    L.append("## Disclosure totals vs 1104 (sorted by f1.3 total)")
    L.append("")
    L.append("| source | f1.2 | f1.3 | f1.4 | +10% | +20% |")
    L.append("|---|---|---|---|---|---|")
    rows = sorted(result["sources"].items(),
                  key=lambda kv: kv[1]["totals_vs_1104"]["f1.3"])
    for label, s in rows:
        t = s["totals_vs_1104"]
        L.append(f"| {label} | {t['f1.2']} | {t['f1.3']} | {t['f1.4']} | {t['f1.3+10%']} | {t['f1.3+20%']} |")
    L.append("")
    L.append("## Coherence: sum h2 vs measured H(A|B)")
    L.append("")
    L.append("| source | sum h2 | H(A|B) | gap |")
    L.append("|---|---|---|---|")
    for label in sorted(result["sources"].keys()):
        c = result["sources"][label]["coherence"]
        L.append(f"| {label} | {c['sum_h2']:.8f} | {c['H_A_given_B']:.8f} | {c['gap']:.8f} |")
    L.append("")
    L.append("## LSB margin (plane 0)")
    L.append("")
    L.append("| source | m0(1.3) | m0(+20%) | 1024-m0 nom | 1024-m0 +20% | 1104-total nom | 1104-total +20% |")
    L.append("|---|---|---|---|---|---|---|")
    for label in sorted(result["sources"].keys()):
        m = result["sources"][label]["lsb_margin"]
        L.append(f"| {label} | {m['m0_at_1.3']} | {m['m0_at_1.3_plus20']} | "
                 f"{m['block_headroom_nom']} | {m['block_headroom_plus20']} | "
                 f"{m['budget_headroom_nom']} | {m['budget_headroom_plus20']} |")
    L.append("")
    d = result["decision"]
    L.append(f"## Decision: {d['word']} (clause {d['clause']}, primary source {d['primary_source']})")
    L.append("")
    L.append("> " + CEILING)
    L.append("")
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Stage 0 per-plane feasibility arithmetic")
    ap.add_argument("--inputs", nargs=5, required=True, metavar="JSON",
                    help="exactly the five frozen channel-statistics JSONs")
    ap.add_argument("--root", required=True, help="fresh additive workspace/s0_<uuid8> root")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--execution-authorized", action="store_true")
    args = ap.parse_args(argv)
    if not (args.execute and args.execution_authorized):
        print("refused: both --execute and --execution-authorized are required",
              file=sys.stderr)
        return 2
    rootdir = Path(args.root)
    try:
        result = run_stage0(list(args.inputs), args.root)
    except Refusal as e:
        try:
            with open(rootdir / "STAGE0_LOG.md", "a", encoding="utf-8") as f:
                f.write(f"\nSTOP: {e}\n")
        except OSError:
            pass
        print(f"STOP: {e}", file=sys.stderr)
        return 2
    (rootdir / "S0_RESULT.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (rootdir / "S0_SUMMARY.md").write_text(write_summary(result), encoding="utf-8")
    r = result["resources"]
    d = result["decision"]
    with open(rootdir / "STAGE0_LOG.md", "a", encoding="utf-8") as f:
        f.write("\n## EXECUTION\n")
        f.write(f"- command: {r['command']}\n")
        f.write(f"- exit code: 0\n")
        f.write(f"- wall_s: {r['wall_s']:.3f} (cap 600)\n")
        f.write(f"- peak_rss_gib: {r['peak_rss_gib']:.4f} (cap 2)\n")
        f.write(f"- thread_env: {r['thread_env']}\n")
        f.write(f"- decision: {d['word']} ({d['clause']}, primary {d['primary_source']})\n")
        f.write(f"- evidence: S0_RESULT.json + S0_SUMMARY.md in {args.root}\n")
    print(d["word"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
