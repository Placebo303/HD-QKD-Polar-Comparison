"""P3 Stage 0.5 probe — file identity + span continuity + config survey.

DECIDE track, Acceptance ID G-P3-STAGE05. Minimum viable real-data contact:
per dataset, open ONLY the base ``X.ttbin`` member via ``FileReader``,
read ``getConfiguration`` / ``getChannelList`` / ``getLastMarker``, then a
bounded first/last-timestamp span drain. No histograms, no coincidences, no
pairs, no entropy, no decoder/DE/graph calls.

Hard rules (by construction):
  - Exactly ONE ``FileReader`` is ever live per dataset. The ``.1`` shard is
    opened ONLY as a single-member fallback if the base fails to open, and
    then the base reader is never created. Both members are never opened in
    one process; streams are never concatenated.
  - Only first/last timestamp scalars are retained; every ``getData`` array
    is discarded immediately. No event arrays are written to disk.

House style follows ``comparison_bench/.../cli/smoke_test.py``:
``main() -> int`` + ``if __name__ == "__main__": raise SystemExit(main())``.
"""

from __future__ import annotations

import argparse
import json
import os
import resource
import time
from pathlib import Path
from typing import Any, Callable

from comparison_bench.src.comparison_bench.io.ttbin_compat import install_timetagger_alias

# Authorization-time constants (G-P3-STAGE05, user grant 2026-09-21).
G3_TOL_S = 0.5  # |span - mtime_gap| tolerance, packet §5 / prereg §6
GLOBAL_CEILING_S = 1800.0  # total wall ceiling, prereg §3
CHUNK_EVENTS = 1_000_000  # getData chunk size (matches frozen loader)
PS_PER_S = 1e12

# Packet §2 order. The i-th base in --bases gets the i-th id.
DATASET_IDS = [
    "JAN12", "SHG-A", "SHG-B", "T0-500K", "T0-1M",
    "T0-1.5M", "T0-2M", "T2-1.5M", "T2-1M", "T2-2M",
]

FILENAME_DURATION_TAG = "3s"
FILENAME_DURATION_S = 3.0

# Config-survey keyword map: category -> key-name substrings (lowercase).
# Matching quotes keys verbatim; absence is recorded, never invented.
SURVEY_CATEGORIES: dict[str, list[str]] = {
    "acquisition_start": ["current time", "current_time", "start", "acquisition", "created", "date"],
    "channel_roles_gates_markers": ["channel", "gate", "marker", "role", "sync"],
    "pm_eb": ["pm", "eb", "polarization", "energy_basis", "energy basis", "basis"],
    "phase_matching": ["type0", "type2", "shg", "phase", "ppln", "crystal", "pump"],
    "split_part_structure": ["part", "split", "sequence", "filename", "file count", "filecount", "index", "shard"],
}


def parse_bases(raw: str) -> list[str]:
    bases = [b.strip() for b in raw.split(";") if b.strip()]
    if len(bases) != 10:
        raise SystemExit(f"expected exactly 10 semicolon-separated base paths, got {len(bases)}")
    for b in bases:
        if not b.endswith(".ttbin") or b.endswith(".1.ttbin"):
            raise SystemExit(f"base must be an X.ttbin member, got: {b}")
        if not os.path.exists(b):
            raise SystemExit(f"base path does not exist: {b}")
    return bases


def shard_path(base: str) -> str:
    return base[: -len(".ttbin")] + ".1.ttbin"


def open_single_member(
    base: str, opener: Callable[[str], Any], max_reads: int
) -> tuple[str, Any, bool]:
    """Open exactly one member. Returns (path_opened, reader, fallback_used).

    Tries the base only. The ``.1`` shard is tried ONLY if the base open
    raised and the read budget allows a second open. By construction at most
    one reader is ever live: the fallback path is reached only when no base
    reader exists.
    """
    opens = 0
    try:
        reader = opener(base)
        return base, reader, False
    except Exception as exc:
        base_exc = exc
        opens += 1
    if opens + 1 > max_reads:
        raise RuntimeError(f"base open failed and no read budget left: {base_exc}")
    shard = shard_path(base)
    reader = opener(shard)  # raises straight through if the shard also fails
    return shard, reader, True


def config_type_and_verbatim(raw: Any) -> tuple[str, Any, bool]:
    """Return (python_type_name, jsonable_verbatim, parses_ok)."""
    typename = type(raw).__name__
    if isinstance(raw, dict):
        return typename, _jsonable(raw), True
    if isinstance(raw, str):
        try:
            return typename, _jsonable(json.loads(raw)), True
        except Exception:
            return typename, raw, False
    try:
        return typename, _jsonable(dict(raw)), True
    except Exception:
        return typename, str(raw), False


def _jsonable(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    return str(obj)


def span_drain_deadline(
    reader: Any, chunk: int, out_of_time: Callable[[], bool]
) -> tuple[float | None, float | None, int, bool]:
    """Bounded drain keeping ONLY first/last timestamps (picoseconds).

    Returns (t_first_ps, t_last_ps, n_chunks, timed_out). Each ``getData``
    array is discarded immediately after its endpoints are read.
    """
    t_first: float | None = None
    t_last: float | None = None
    n_chunks = 0
    while reader.hasData():
        if out_of_time():
            return t_first, t_last, n_chunks, True
        data = reader.getData(chunk)
        ts = data.getTimestamps()
        n = len(ts)
        if n:
            if t_first is None:
                t_first = float(ts[0])
            t_last = float(ts[-1])
        del data, ts
        n_chunks += 1
    return t_first, t_last, n_chunks, False


def tag_disputed(duration_s: float | None, tag_s: float = FILENAME_DURATION_S) -> bool | None:
    if duration_s is None:
        return None
    return abs(duration_s - tag_s) > G3_TOL_S


def evaluate_gates(
    opened_ok: bool, duration_s: float | None, mtime_gap_s: float | None, config_ok: bool
) -> dict[str, bool]:
    g1 = bool(opened_ok)
    g2 = duration_s is not None and duration_s > 0
    g3 = (
        duration_s is not None
        and mtime_gap_s is not None
        and abs(duration_s - mtime_gap_s) <= G3_TOL_S
    )
    return {"G1": g1, "G2": bool(g2), "G3": bool(g3), "G4": bool(config_ok)}


def survey_config(config: Any) -> dict[str, dict[str, Any]]:
    """Per-category present-key survey over a verbatim config mapping."""
    found: dict[str, dict[str, Any]] = {cat: {} for cat in SURVEY_CATEGORIES}
    if not isinstance(config, dict):
        return found
    lowered = {str(k).lower(): (str(k), v) for k, v in config.items()}
    for cat, kws in SURVEY_CATEGORIES.items():
        for kw in kws:
            for lk, (orig, v) in lowered.items():
                if kw in lk and orig not in found[cat]:
                    found[cat][orig] = v
    return found


def pm_eb_evidence_text(survey: dict[str, dict[str, Any]]) -> str:
    lines: list[str] = []
    for cat in ("pm_eb", "phase_matching"):
        hits = survey.get(cat, {})
        if hits:
            quoted = "; ".join(f"{k}={json.dumps(_jsonable(v))[:200]}" for k, v in hits.items())
            lines.append(f"{cat} keys PRESENT (quoted verbatim): {quoted}.")
        else:
            lines.append(f"{cat} keys ABSENT: no config key matched this category; nothing established.")
    lines.append(
        "What is NOT established: PM/EB relevance is UNPROVEN until the main thread "
        "judges the quoted keys; no inference beyond quoted keys is made here."
    )
    return " ".join(lines)


def probe_dataset(
    dataset_id: str,
    base: str,
    opener: Callable[[str], Any],
    max_reads: int,
    per_read_timeout_s: float,
    global_deadline: float,
) -> dict[str, Any]:
    t_start = time.monotonic()

    def out_of_time() -> bool:
        return (time.monotonic() - t_start) > per_read_timeout_s or time.monotonic() > global_deadline

    rec: dict[str, Any] = {
        "dataset_id": dataset_id,
        "base_path": base,
        "member_opened": None,
        "fallback_used": False,
        "config_type": None,
        "config_verbatim": None,
        "channel_list": None,
        "last_marker": None,
        "t_first_s": None,
        "t_last_s": None,
        "duration_measured_s": None,
        "filename_duration_tag": FILENAME_DURATION_TAG,
        "tag_disputed": None,
        "mtime_base": None,
        "mtime_shard": None,
        "mtime_gap_s": None,
        "span_gap_agreement": None,
        "pm_eb_evidence": "",
        "gates_G1_G4": {"G1": False, "G2": False, "G3": False, "G4": False},
        "status": "FAIL",
    }
    try:
        st_b = os.stat(base)
        rec["mtime_base"] = st_b.st_mtime
        try:
            st_s = os.stat(shard_path(base))
            rec["mtime_shard"] = st_s.st_mtime
            rec["mtime_gap_s"] = st_s.st_mtime - st_b.st_mtime
        except OSError:
            pass
    except OSError as exc:
        rec["status"] = "FAIL"
        rec["pm_eb_evidence"] = f"stat failed: {exc}; nothing established."
        return rec

    try:
        member, reader, fallback = open_single_member(base, opener, max_reads)
    except Exception as exc:
        rec["pm_eb_evidence"] = f"open failed (single member only, never both): {exc}; nothing established."
        return rec
    rec["member_opened"] = member
    rec["fallback_used"] = fallback

    config_ok = False
    try:
        raw_cfg = reader.getConfiguration()
        ctype, verbatim, config_ok = config_type_and_verbatim(raw_cfg)
        rec["config_type"] = ctype
        rec["config_verbatim"] = verbatim
    except Exception as exc:
        rec["config_type"] = "unreadable"
        rec["config_verbatim"] = f"getConfiguration raised: {exc}"
    try:
        rec["channel_list"] = _jsonable(list(reader.getChannelList()))
    except Exception as exc:
        rec["channel_list"] = f"getChannelList raised: {exc}"
    try:
        rec["last_marker"] = _jsonable(reader.getLastMarker())
    except Exception as exc:
        rec["last_marker"] = f"getLastMarker raised: {exc}"

    survey = survey_config(rec["config_verbatim"])
    rec["pm_eb_evidence"] = pm_eb_evidence_text(survey)
    rec["_survey"] = {cat: sorted(hits) for cat, hits in survey.items()}

    t_first_ps, t_last_ps, _n, timed_out = span_drain_deadline(reader, CHUNK_EVENTS, out_of_time)
    try:
        reader.close()
    except Exception:
        pass
    if timed_out:
        rec["status"] = "INCOMPLETE"
        rec["gates_G1_G4"] = evaluate_gates(True, None, rec["mtime_gap_s"], config_ok)
        return rec
    if t_first_ps is not None and t_last_ps is not None:
        rec["t_first_s"] = t_first_ps / PS_PER_S
        rec["t_last_s"] = t_last_ps / PS_PER_S
        rec["duration_measured_s"] = (t_last_ps - t_first_ps) / PS_PER_S
    rec["tag_disputed"] = tag_disputed(rec["duration_measured_s"])
    gap = rec["mtime_gap_s"]
    dur = rec["duration_measured_s"]
    rec["span_gap_agreement"] = (
        bool(abs(dur - gap) <= G3_TOL_S) if (dur is not None and gap is not None) else None
    )
    gates = evaluate_gates(True, dur, gap, config_ok)
    rec["gates_G1_G4"] = gates
    rec["status"] = "ok" if (gates["G1"] and gates["G2"] and gates["G3"]) else "FAIL"
    return rec


def write_shared_tables(records: list[dict[str, Any]], root: Path) -> None:
    lines = [
        "# P3 Stage 0.5 duration table",
        "",
        "| id | duration_measured_s | filename_tag | tag_disputed | mtime_gap_s | span_gap_agreement | status |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in records:
        lines.append(
            f"| {r['dataset_id']} | {r['duration_measured_s']} | "
            f"{r['filename_duration_tag']} | {r['tag_disputed']} | "
            f"{r['mtime_gap_s']} | {r['span_gap_agreement']} | {r['status']} |"
        )
    (root / "duration_table.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    cats = list(SURVEY_CATEGORIES)
    head = "| id | " + " | ".join(cats) + " | status |"
    lines = ["# P3 Stage 0.5 config survey (present-key names; empty = absent)", "", head,
             "|" + "|".join(["---"] * (len(cats) + 2)) + "|"]
    for r in records:
        surv = r.get("_survey", {})
        cells = [", ".join(f"`{k}`" for k in surv.get(c, [])) or "(absent)" for c in cats]
        lines.append(f"| {r['dataset_id']} | " + " | ".join(cells) + f" | {r['status']} |")
    (root / "config_notes.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="P3 Stage 0.5 thin probe (G-P3-STAGE05).")
    ap.add_argument("--bases", required=True,
                    help="semicolon-separated base X.ttbin paths, exactly 10 in packet §2 order")
    ap.add_argument("--root", required=True, help="fresh additive output root")
    ap.add_argument("--per-read-timeout-s", type=float, default=300.0)
    ap.add_argument("--max-reads-per-dataset", type=int, default=2,
                    help="max FileReader member opens per dataset (base + one shard-only fallback)")
    args = ap.parse_args()

    if args.per_read_timeout_s <= 0:
        raise SystemExit("--per-read-timeout-s must be > 0")
    if args.max_reads_per_dataset < 1:
        raise SystemExit("--max-reads-per-dataset must be >= 1")
    bases = parse_bases(args.bases)
    root = Path(args.root)
    if root.exists():
        raise SystemExit(f"output root already exists (refusing to overwrite): {root}")
    root.mkdir(parents=True, exist_ok=False)

    install_timetagger_alias()
    from TimeTagger import FileReader  # noqa: E402  (alias installed above)

    def opener(path: str) -> Any:
        return FileReader(path)

    wall0 = time.monotonic()
    global_deadline = wall0 + GLOBAL_CEILING_S
    records: list[dict[str, Any]] = []
    for did, base in zip(DATASET_IDS, bases, strict=True):
        rec = probe_dataset(did, base, opener, args.max_reads_per_dataset,
                            args.per_read_timeout_s, global_deadline)
        survey = rec.pop("_survey", {})
        rec["config_survey_keys"] = survey
        with open(root / f"{did}.json", "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=2)
        rec["_survey"] = survey
        records.append(rec)
        print(f"{did}: status={rec['status']} duration={rec['duration_measured_s']} "
              f"gates={rec['gates_G1_G4']}", flush=True)
        if rec["status"] == "INCOMPLETE":
            print("wall hit mid-dataset: STOPPING batch, retaining everything.", flush=True)
            break
    write_shared_tables(records, root)
    wall_dt = time.monotonic() - wall0
    peak_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(f"done: n={len(records)} wall_s={wall_dt:.1f} peak_rss_kb={peak_kb}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
