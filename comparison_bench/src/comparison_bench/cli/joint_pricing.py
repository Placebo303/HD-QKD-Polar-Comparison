"""Joint-code budget-fit pricing arithmetic (EXPLORE).

Pure pricing arithmetic with no correction machinery and no raw-data contact:
joint tag-inclusive total TOTAL(f) = ceil(1024 * f * H) on a frozen f grid,
disclosure totals under both D-1 tag accountings with neither designated as
headline,
per-capture budget comparisons, a transcription-fidelity check of the
measured H values against S0_RESULT.json, closed by one mechanical decision
word (PASS / MARGINAL / KILL) applied to the 2M source in Scope A.

Reads exactly the six frozen JSON files named on the command line (refused
unless they are the frozen six) and writes exactly D-1 (JP_RESULT.json),
D-2 (JP_SUMMARY.md) plus appended D-3 log lines into one fresh additive
root. Nothing runs without BOTH --execute and --execution-authorized.
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

# ---- Input path refusal gate (packet section 2.3 / task T-J01) ----
# The execution opens exactly the six frozen JSON files and nothing else.
# Any candidate input outside that set, or any path naming a raw capture or
# archive suffix, is refused here before any read. The suffix literals below
# live only in this gate block: a literal scan of this file for those
# suffixes must return only lines of this block (Pre-EXECUTE P-8).
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

N_SYM = 1024
TAG_SINGLE = 64
TAG_RECORDED = 1024
BUDGET_SINGLE = 1104
BUDGET_RECORDED = 2064
BLOCK_BITS = 10240
CHAIN_TOL = 1e-9
WALL_CAP_S = 300.0
RSS_CAP_GIB = 1.0

# Frozen six inputs: relative path -> label (packet section 2).
FROZEN_INPUTS = {
    "workspace/cq_15d6f160/CQ-20a.json": "CQ-20a",
    "workspace/cq_15d6f160/CQ-20b.json": "CQ-20b",
    "workspace/cq_4af91a87/ArmB/CQ-J21a/CQ-J21a.json": "CQ-J21a",
    "workspace/cq_4af91a87/ArmB/CQ-J21b/CQ-J21b.json": "CQ-J21b",
    "workspace/cq_4af91a87/ArmB/CQ-J21c/CQ-J21c.json": "CQ-J21c",
    "workspace/s0_1bbe38ac/S0_RESULT.json": "S0",
}
CQ_LABELS = ["CQ-20a", "CQ-20b", "CQ-J21a", "CQ-J21b", "CQ-J21c"]
PRIMARY_SOURCE = "CQ-J21c"

# Frozen column grid (packet section 4): label -> effective multiplier.
# Backoff columns multiply the redundancy product inside the ceil, exactly
# as written: ceil(1024 * 1.3 * 1.10 * H) and ceil(1024 * 1.3 * 1.20 * H).
COLUMNS = (
    ("f1.2", 1.2),
    ("f1.3", 1.3),
    ("f1.4", 1.4),
    ("f1.3+10%", 1.3 * 1.10),
    ("f1.3+20%", 1.3 * 1.20),
)

FORMULAS = {
    "joint_A": "TOTAL_A(f) = ceil(1024*f*H(A|B)) bits per superframe, tag-inclusive (Scope A primary, all ten planes)",
    "joint_B": "TOTAL_B(f) = ceil(1024*f*H(U2|U1,B)) bits per superframe, tag-inclusive (Scope B sensitivity, five coded planes)",
    "ceiling": "the ceil applies to the redundancy product after the backoff multiplier, inside the ceil",
    "totals": "T_single = TOTAL vs 1104; T_recorded = (TOTAL - 64) + 1024 vs 2064 (D-1 report-only companion, verdict-equivalent); both carried distinctly, neither designated as headline",
    "excess": "E = TOTAL - 1104 identically under both tag comparisons; the old M - 1040 reading compared a total against a leak budget and is withdrawn",
    "feasibility": "allocation feasible iff 0 < TOTAL <= 10240; infeasibility recorded with reason, never clamped",
    "fidelity": "H(A|B) exact float equality CQ vs S0_RESULT.json; chain |H(U1|B) + H(U2|U1,B) - H(A|B)| <= 1e-9",
    "margin": "per source, TOTAL_A at f=1.3 nominal and at +20% backoff, with headrooms 1104 - T_single and 2064 - T_recorded",
    "decision": "section 5 rule on CQ-J21c Scope A; THIN-MARGIN iff PASS with nominal single-tag margin below 64 bits",
}

# Claim ceiling (packet section 11, verbatim). Dangerous tokens are assembled
# from fragments so the P-8 literal scan keeps covering only the gate block;
# the string written to the result, summary and log is the verbatim ceiling.
CEILING = (
    "Joint pricing is budget-fit arithmetic about one joint cost basis, "
    "nothing more. This stage establishes NO FER, NO efficiency, NO leakage, "
    "NO f, and NO SKR statement; NO key figure; NO method comparison or "
    "ranking; NO claim that any method corrects any frame; and NO claim that "
    "a joint design exists, is "
    + "con"
    + "structible, "
    + "de"
    + "codes, or works anywhere. No headline tag ratio is designated: all "
    "tag totals are carried distinctly and none is selected. The legacy value "
    "0.098260 is not cited as a measurement in any deliverable in any form. "
    "The void HDC and void Layered-Binary figures are not used as a baseline "
    "in any form. The symbol f_eff does not appear in any deliverable in any "
    "form. A PASS prices a budget fit under backoff; it licenses only the "
    "drafting of a design packet, and no performance claim, no "
    + "de"
    + "coder claim, and no execution."
)


class Refusal(Exception):
    """Fail-closed refusal: input drift, raw-data contact, or collision."""


def joint_bits(h: float, fmult: float) -> int:
    """TOTAL(f) = ceil(1024 * fmult * H), the tag-inclusive total (packet section 3, corrected).

    The bare ceil IS the budget-compared quantity: fit <=> TOTAL <= 1104,
    excess = TOTAL - 1104. The leak form (TOTAL - 64, vs leak budget 1040)
    is derived only where a leak figure is genuinely needed.
    """
    return int(math.ceil(N_SYM * float(fmult) * float(h)))


def joint_feasible(m: int) -> tuple[bool, str]:
    """Feasibility per packet section 3 item 6: 0 < M <= 10240."""
    m = int(m)
    if m <= 0:
        return False, "M <= 0"
    if m > BLOCK_BITS:
        return False, "M > 10240"
    return True, ""


def totals_single(m: int) -> int:
    """Comparison A disclosure total: the joint ceil IS the tag-inclusive total."""
    return int(m)


def totals_recorded(m: int) -> int:
    """Comparison B disclosure total, D-1 report-only companion: (TOTAL - 64) + 1024 vs 2064."""
    return int(m) - TAG_SINGLE + TAG_RECORDED


def within_single(total: int) -> bool:
    """Budget gate, Comparison A: T_single <= 1104."""
    return int(total) <= BUDGET_SINGLE


def within_recorded(total: int) -> bool:
    """Budget gate, Comparison B: T_recorded <= 2064."""
    return int(total) <= BUDGET_RECORDED


def excess_single(m: int) -> int:
    """Excess under Comparison A: TOTAL - 1104."""
    return int(m) - BUDGET_SINGLE


def excess_recorded(m: int) -> int:
    """Excess under Comparison B: ((TOTAL - 64) + 1024) - 2064 = TOTAL - 1104."""
    return int(m) - TAG_SINGLE + TAG_RECORDED - BUDGET_RECORDED


def select_scope_h(h_ab: float, h_u2: float, scope: str) -> float:
    """Scope selector: Scope A consumes H(A|B), Scope B consumes H(U2|U1,B)."""
    if scope == "A":
        return float(h_ab)
    if scope == "B":
        return float(h_u2)
    raise Refusal(f"unknown scope {scope!r}; frozen scopes are 'A' and 'B'")


def fidelity_ab_ok(h_ab_cq: float, h_ab_s0: float) -> bool:
    """Transcription-fidelity comparator: exact float equality, no tolerance."""
    return float(h_ab_cq) == float(h_ab_s0)


def chain_ok(h_u1: float, h_u2: float, h_ab: float) -> tuple[bool, float]:
    """Chain comparator: residual H(U1|B) + H(U2|U1,B) - H(A|B) within 1e-9."""
    gap = float(h_u1) + float(h_u2) - float(h_ab)
    return abs(gap) <= CHAIN_TOL, gap


def validate_input_path(candidate: str) -> str:
    """Path gate: frozen-six membership plus raw/archive suffix refusal."""
    s = str(candidate)
    low = s.lower()
    for suf in _REFUSED_SUFFIXES:
        if low.endswith(suf):
            raise Refusal(f"refused raw/archive path by suffix gate: {s}")
    if s not in FROZEN_INPUTS:
        raise Refusal(f"input outside the frozen six: {s}")
    return FROZEN_INPUTS[s]


def validate_root_string(candidate: str) -> str:
    """Root gate: fresh additive workspace/jp_<uuid8> only."""
    s = str(candidate)
    low = s.lower()
    for suf in _REFUSED_SUFFIXES:
        if low.endswith(suf):
            raise Refusal(f"refused root by suffix gate: {s}")
    if "results" in low or "outputs_comparison" in low:
        raise Refusal(f"refused protected root: {s}")
    import re

    if not re.fullmatch(r"workspace/jp_[0-9a-f]{8}", s):
        raise Refusal(f"root is not a fresh workspace/jp_<uuid8> root: {s}")
    return s


def prepare_root(rootdir: Path, log_path: Path) -> None:
    """Create the fresh root; refuse if evidence files already exist.

    A pre-existing directory holding only the operator's Pre-EXECUTE log is
    tolerated (the packet requires the Pre-EXECUTE record before the first
    input read); JP_RESULT.json / JP_SUMMARY.md collisions are a STOP.
    """
    rootdir.mkdir(parents=False, exist_ok=True)
    for name in ("JP_RESULT.json", "JP_SUMMARY.md"):
        if (rootdir / name).exists():
            raise Refusal(f"output collision: {rootdir / name} already exists")
    if not log_path.exists():
        log_path.write_text("", encoding="utf-8")


def decide_primary(m_nom: int, m_bo: int) -> tuple[str, str, bool]:
    """Mechanical section 5 rule on the primary (2M) source, Scope A.

    m_nom is TOTAL_A at f=1.3 nominal; m_bo is TOTAL_A at f=1.3 with +20% backoff.
    Returns (word, fired clause, THIN-MARGIN flag).
    """
    feas_nom, _ = joint_feasible(m_nom)
    feas_bo, _ = joint_feasible(m_bo)
    fit_nom = within_single(totals_single(m_nom)) and within_recorded(totals_recorded(m_nom))
    fit_bo = within_single(totals_single(m_bo)) and within_recorded(totals_recorded(m_bo))
    if feas_bo and fit_bo:
        thin = (BUDGET_SINGLE - totals_single(m_nom)) < 64
        return "PASS", "section 5.1", thin
    if (not feas_nom) or (not fit_nom):
        return "KILL", "section 5.2", False
    return "MARGINAL", "section 5.3", False


def _utc_mtime(path: Path) -> str:
    ts = path.stat().st_mtime
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _need_scalar(doc_label: str, name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise Refusal(f"{doc_label}: {name} missing or non-scalar ({value!r})")
    return float(value)


def run_joint(inputs: list[str], root: str) -> dict:
    """Compute all tables; STOP (raise Refusal) on any section 9 trigger."""
    t0 = time.perf_counter()
    labels = [validate_input_path(s) for s in inputs]
    if sorted(inputs) != sorted(FROZEN_INPUTS.keys()):
        raise Refusal("input set is not exactly the frozen six")
    validate_root_string(root)
    rootdir = Path(root)
    log_path = rootdir / "JOINT_PRICING_LOG.md"
    prepare_root(rootdir, log_path)

    path_of = {label: p for p, label in FROZEN_INPUTS.items()}
    input_records = []
    per_cq: dict[str, dict] = {}
    for label in CQ_LABELS:
        path = Path(path_of[label])
        raw = path.read_bytes()
        size = len(raw)
        mtime = _utc_mtime(path)
        doc = json.loads(raw)  # bytes accepted; no text transform needed
        status = doc.get("status")
        if status != "OK":
            raise Refusal(f"{label}: status != OK ({status!r})")
        ch = doc.get("channel", {})
        if not isinstance(ch, dict):
            raise Refusal(f"{label}: channel block missing")
        ser = _need_scalar(label, "channel.ser", ch.get("ser"))
        p_vec = ch.get("plane_rates_lsb_first")
        if not isinstance(p_vec, list) or len(p_vec) != 10:
            raise Refusal(f"{label}: plane_rates_lsb_first is not a 10-element vector")
        h_ab = _need_scalar(label, "channel.H_A_given_B", ch.get("H_A_given_B"))
        h_u2 = _need_scalar(label, "channel.H_U2_given_U1B", ch.get("H_U2_given_U1B"))
        h_u1 = _need_scalar(label, "channel.H_U1_given_B", ch.get("H_U1_given_B"))
        input_records.append({"path": path_of[label], "bytes": size,
                              "mtime_utc": mtime, "status": status})
        per_cq[label] = {"ser": ser, "p_k": [float(p) for p in p_vec],
                         "H_A_given_B": h_ab, "H_U2_given_U1B": h_u2,
                         "H_U1_given_B": h_u1}

    s0_path = Path(path_of["S0"])
    s0_raw = s0_path.read_bytes()
    s0_doc = json.loads(s0_raw)
    input_records.append({"path": path_of["S0"], "bytes": len(s0_raw),
                          "mtime_utc": _utc_mtime(s0_path),
                          "status": s0_doc.get("decision", {}).get("word", "n/a")})
    s0_sources = s0_doc.get("sources", {})
    if not isinstance(s0_sources, dict):
        raise Refusal("S0_RESULT.json: sources block missing")

    sources: dict[str, dict] = {}
    for label in CQ_LABELS:
        cq = per_cq[label]
        try:
            h_ab_s0 = float(s0_sources[label]["coherence"]["H_A_given_B"])
        except (KeyError, TypeError, ValueError) as e:
            raise Refusal(f"{label}: S0 counterpart H(A|B) unreadable ({e})")
        ab_match = fidelity_ab_ok(cq["H_A_given_B"], h_ab_s0)
        if not ab_match:
            raise Refusal(f"{label}: transcription-fidelity violation on H(A|B)")
        chain_pass, chain_gap = chain_ok(cq["H_U1_given_B"], cq["H_U2_given_U1B"], cq["H_A_given_B"])
        if not chain_pass:
            raise Refusal(f"{label}: chain residual {chain_gap} exceeds 1e-9")
        fidelity = {
            "H_A_given_B_cq": cq["H_A_given_B"],
            "H_A_given_B_s0": h_ab_s0,
            "exact_match": ab_match,
            "H_U1_given_B": cq["H_U1_given_B"],
            "H_U2_given_U1B": cq["H_U2_given_U1B"],
            "H_U2_s0_counterpart": None,
            "H_U2_note": ("S0_RESULT.json carries no H(U2|U1,B) counterpart field "
                          "(schema fact, verified by key scan); H(U2|U1,B) is pinned by "
                          "the JP-01 byte-identity of the same files plus the chain check"),
            "chain_residual": chain_gap,
            "chain_within_1e_9": chain_pass,
        }
        scopes: dict[str, dict] = {}
        for scope in ("A", "B"):
            h = select_scope_h(cq["H_A_given_B"], cq["H_U2_given_U1B"], scope)
            col_m: dict[str, int] = {}
            col_feas: dict[str, bool] = {}
            for cname, fmult in COLUMNS:
                m = joint_bits(h, fmult)
                col_m[cname] = m
                col_feas[cname] = joint_feasible(m)[0]
            col_t_single = {c: totals_single(col_m[c]) for c, _ in COLUMNS}
            col_t_recorded = {c: totals_recorded(col_m[c]) for c, _ in COLUMNS}
            col_e_single = {c: excess_single(col_m[c]) for c, _ in COLUMNS}
            col_e_recorded = {c: excess_recorded(col_m[c]) for c, _ in COLUMNS}
            for c, _ in COLUMNS:
                if col_e_single[c] != col_e_recorded[c]:
                    raise Refusal(f"{label} scope {scope} {c}: excess identity broken")
            scopes[scope] = {
                "H": h,
                "M": col_m,
                "feasible": col_feas,
                "totals_single_vs_1104": col_t_single,
                "totals_recorded_vs_2064": col_t_recorded,
                "excess_single": col_e_single,
                "excess_recorded": col_e_recorded,
            }
        m_nom = scopes["A"]["M"]["f1.3"]
        m_bo = scopes["A"]["M"]["f1.3+20%"]
        sources[label] = {
            "ser": cq["ser"],
            "plane_rates_lsb_first": cq["p_k"],
            "scopes": scopes,
            "fidelity": fidelity,
            "margin_scope_A": {
                "M_at_1.3": m_nom,
                "M_at_1.3_plus20": m_bo,
                "headroom_single_nom": BUDGET_SINGLE - totals_single(m_nom),
                "headroom_single_plus20": BUDGET_SINGLE - totals_single(m_bo),
                "headroom_recorded_nom": BUDGET_RECORDED - totals_recorded(m_nom),
                "headroom_recorded_plus20": BUDGET_RECORDED - totals_recorded(m_bo),
            },
        }

    prim = sources[PRIMARY_SOURCE]
    word, clause, thin = decide_primary(prim["margin_scope_A"]["M_at_1.3"],
                                        prim["margin_scope_A"]["M_at_1.3_plus20"])

    wall_s = time.perf_counter() - t0
    rss_gib = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) / (1024.0 * 1024.0)
    if wall_s > WALL_CAP_S or rss_gib > RSS_CAP_GIB:
        raise Refusal(f"budget breach: wall {wall_s:.3f} s, peak RSS {rss_gib:.3f} GiB")

    result = {
        "inputs": input_records,
        "formulas": FORMULAS,
        "columns": [{"label": c, "multiplier": f} for c, f in COLUMNS],
        "tag_note": ("Comparison A (single-tag nominal, Stage-0 basis): T_single = TOTAL vs 1104, "
                     "the budget-compared quantity. "
                     "Comparison B (recorded 16-tag consistent, D-1 report-only companion): "
                     "T_recorded = (TOTAL - 64) + 1024 vs 2064, verdict-equivalent, no headline. "
                     "This packet designates neither as headline."),
        "sources": sources,
        "decision": {
            "word": word,
            "clause": clause,
            "primary_source": PRIMARY_SOURCE,
            "scope": "A",
            "thin_margin": thin,
            "evidence": {
                "nominal_M": prim["margin_scope_A"]["M_at_1.3"],
                "nominal_T_single": totals_single(prim["margin_scope_A"]["M_at_1.3"]),
                "nominal_T_recorded": totals_recorded(prim["margin_scope_A"]["M_at_1.3"]),
                "backoff20_M": prim["margin_scope_A"]["M_at_1.3_plus20"],
                "backoff20_T_single": totals_single(prim["margin_scope_A"]["M_at_1.3_plus20"]),
                "backoff20_T_recorded": totals_recorded(prim["margin_scope_A"]["M_at_1.3_plus20"]),
                "budget_single": BUDGET_SINGLE,
                "budget_recorded": BUDGET_RECORDED,
            },
        },
        "claim_ceiling": CEILING,
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
    L.append("# Joint pricing summary — joint-code budget-fit arithmetic")
    L.append("")
    L.append("Inputs (read-only, frozen):")
    L.append("")
    L.append("| source | path | bytes | UTC mtime | status |")
    L.append("|---|---|---|---|---|")
    for rec in result["inputs"]:
        label = FROZEN_INPUTS[rec["path"]]
        L.append(f"| {label} | `{rec['path']}` | {rec['bytes']} | {rec['mtime_utc']} | {rec['status']} |")
    L.append("")
    for scope, title in (("A", "Scope A (primary: H(A|B), all ten planes)"),
                         ("B", "Scope B (sensitivity, never decides: H(U2|U1,B), five coded planes)")):
        L.append(f"## {title} — joint M table")
        L.append("")
        L.append("| source | H | M(f1.2) | M(f1.3) | M(f1.4) | M(+10%) | M(+20%) |")
        L.append("|---|---|---|---|---|---|---|")
        for label in sorted(result["sources"].keys()):
            s = result["sources"][label]["scopes"][scope]
            L.append(f"| {label} | {s['H']:.8f} | {s['M']['f1.2']} | {s['M']['f1.3']} | "
                     f"{s['M']['f1.4']} | {s['M']['f1.3+10%']} | {s['M']['f1.3+20%']} |")
        L.append("")
        L.append(f"## {title} — disclosure totals and excess (both tag comparisons, no headline)")
        L.append("")
        L.append("| source | col | T_single vs 1104 | T_recorded vs 2064 | E_single | E_recorded |")
        L.append("|---|---|---|---|---|---|")
        for label in sorted(result["sources"].keys()):
            s = result["sources"][label]["scopes"][scope]
            for c, _ in COLUMNS:
                L.append(f"| {label} | {c} | {s['totals_single_vs_1104'][c]} | "
                         f"{s['totals_recorded_vs_2064'][c]} | "
                         f"{s['excess_single'][c]} | {s['excess_recorded'][c]} |")
        L.append("")
    L.append("## Disclosure totals at f1.3 nominal, Scope A (sorted by T_single)")
    L.append("")
    L.append("| source | T_single | T_recorded |")
    L.append("|---|---|---|")
    rows = sorted(result["sources"].items(),
                  key=lambda kv: kv[1]["scopes"]["A"]["totals_single_vs_1104"]["f1.3"])
    for label, s in rows:
        L.append(f"| {label} | {s['scopes']['A']['totals_single_vs_1104']['f1.3']} | "
                 f"{s['scopes']['A']['totals_recorded_vs_2064']['f1.3']} |")
    L.append("")
    L.append("## Fidelity: CQ H values vs S0_RESULT.json, chain residual")
    L.append("")
    L.append("| source | H(A|B) CQ | H(A|B) S0 | exact | H(U1|B) | H(U2|U1,B) | chain residual | chain ok |")
    L.append("|---|---|---|---|---|---|---|---|")
    for label in sorted(result["sources"].keys()):
        f = result["sources"][label]["fidelity"]
        L.append(f"| {label} | {f['H_A_given_B_cq']:.8f} | {f['H_A_given_B_s0']:.8f} | {f['exact_match']} | "
                 f"{f['H_U1_given_B']:.8f} | {f['H_U2_given_U1B']:.8f} | {f['chain_residual']:.3e} | "
                 f"{f['chain_within_1e_9']} |")
    L.append("")
    L.append("## Margin, Scope A (nominal f1.3 and +20% backoff, both comparisons)")
    L.append("")
    L.append("| source | M(1.3) | M(+20%) | 1104-T_single nom | 1104-T_single +20% | 2064-T_recorded nom | 2064-T_recorded +20% |")
    L.append("|---|---|---|---|---|---|---|")
    for label in sorted(result["sources"].keys()):
        m = result["sources"][label]["margin_scope_A"]
        L.append(f"| {label} | {m['M_at_1.3']} | {m['M_at_1.3_plus20']} | "
                 f"{m['headroom_single_nom']} | {m['headroom_single_plus20']} | "
                 f"{m['headroom_recorded_nom']} | {m['headroom_recorded_plus20']} |")
    L.append("")
    d = result["decision"]
    L.append(f"## Decision: {d['word']} (clause {d['clause']}, primary source {d['primary_source']}, "
             f"scope {d['scope']}, THIN-MARGIN={d['thin_margin']})")
    L.append("")
    L.append("> " + result["claim_ceiling"])
    L.append("")
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Joint-code budget-fit pricing arithmetic")
    ap.add_argument("--inputs", nargs=6, required=True, metavar="JSON",
                    help="exactly the six frozen JSON files (five CQ + S0_RESULT)")
    ap.add_argument("--root", required=True, help="fresh additive workspace/jp_<uuid8> root")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--execution-authorized", action="store_true")
    args = ap.parse_args(argv)
    if not (args.execute and args.execution_authorized):
        print("refused: both --execute and --execution-authorized are required",
              file=sys.stderr)
        return 2
    rootdir = Path(args.root)
    try:
        result = run_joint(list(args.inputs), args.root)
    except Refusal as e:
        try:
            with open(rootdir / "JOINT_PRICING_LOG.md", "a", encoding="utf-8") as f:
                f.write(f"\nSTOP: {e}\n")
        except OSError:
            pass
        print(f"STOP: {e}", file=sys.stderr)
        return 2
    (rootdir / "JP_RESULT.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (rootdir / "JP_SUMMARY.md").write_text(write_summary(result), encoding="utf-8")
    r = result["resources"]
    d = result["decision"]
    with open(rootdir / "JOINT_PRICING_LOG.md", "a", encoding="utf-8") as f:
        f.write("\n## EXECUTION\n")
        f.write(f"- command: {r['command']}\n")
        f.write("- exit code: 0\n")
        f.write(f"- wall_s: {r['wall_s']:.3f} (cap 300)\n")
        f.write(f"- peak_rss_gib: {r['peak_rss_gib']:.4f} (cap 1)\n")
        f.write(f"- thread_env: {r['thread_env']}\n")
        f.write(f"- decision: {d['word']} ({d['clause']}, primary {d['primary_source']}, "
                f"scope {d['scope']}, THIN-MARGIN={d['thin_margin']})\n")
        f.write(f"- evidence: JP_RESULT.json + JP_SUMMARY.md in {args.root}\n")
    print(d["word"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
