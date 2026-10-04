"""Segmented proxy-recalibration driver (PROXY-RECAL-R2, T-R2-01).

Infra-only delta over Packet A: the same 240 frame identities run as 6
sequential segments x 40 frames with per-block SEG rewrite + manifest +
240/240 assembly gate. Zero science change: every sampler/validation/
decision number comes from the frozen Packet-A helpers imported below
(never copied); decoder pins stay Stage-1 m=200 cold, max_iter=300 via
those helpers. Simplest correct per AGENTS.md 5.7: full-file rewrite +
flush, no atomic rename, no locking, no checksums, no retry, no caching.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import resource
import sys
import time
from pathlib import Path

import numpy as np

from comparison_bench.src.comparison_bench.cli.probes_closed import proxy_recal_sampler as pr

NUM_SEGMENTS = 6
FRAMES_PER_SEGMENT = 40
SEG_WALL_CAP_S = 1800.0

assert NUM_SEGMENTS * FRAMES_PER_SEGMENT == pr.N_FRAMES


def validate_num_segments(n: int) -> int:
    """Refuse unless the frozen 6-way partition is requested."""
    if int(n) != NUM_SEGMENTS:
        raise pr.Refusal(f"refused: --num-segments must be {NUM_SEGMENTS} (got {n})")
    return NUM_SEGMENTS


def require_dual_flags(execute: bool, authorized: bool) -> None:
    """Both --execute-synthetic and --execution-authorized are required."""
    if not (execute and authorized):
        raise pr.Refusal("refused: both --execute-synthetic and "
                         "--execution-authorized are required")


def validate_input_path(candidate: str) -> str:
    """Path gate: reuse Packet-A frozen-nine + archive-suffix refusal."""
    return pr.validate_input_path(candidate)


def validate_root_string(candidate: str) -> str:
    """Root gate: fresh additive workspace/proxy_recal_r2_<uuid8> only."""
    s = str(candidate)
    low = s.lower()
    for suf in pr._REFUSED_SUFFIXES:
        if low.endswith(suf):
            raise pr.Refusal(f"refused root by suffix gate: {s}")
    if "results" in low or "outputs_comparison" in low:
        raise pr.Refusal(f"refused protected root: {s}")
    if not re.fullmatch(r"workspace/proxy_recal_r2_[0-9a-f]{8}", s):
        raise pr.Refusal(f"root is not a fresh workspace/proxy_recal_r2_<uuid8> root: {s}")
    return s


def segment_idx_list(g: int, num_segments: int = NUM_SEGMENTS) -> list[int]:
    """Ascending frame idx owned by segment g (6 x 40 partition)."""
    validate_num_segments(num_segments)
    g = int(g)
    if not 0 <= g < NUM_SEGMENTS:
        raise pr.Refusal(f"segment index out of range 0..{NUM_SEGMENTS - 1}: {g}")
    start = g * FRAMES_PER_SEGMENT
    return list(range(start, start + FRAMES_PER_SEGMENT))


def segment_seeds(g: int, num_segments: int = NUM_SEGMENTS) -> list[int]:
    """Frozen frame seeds for segment g (FRAME_BASE+idx, same as Packet A)."""
    return [pr.FRAME_BASE + i for i in segment_idx_list(g, num_segments)]


def decide_word(kprime: int, k0: int, w_lo: float, w_hi: float,
                r_lo: float, r_hi: float) -> tuple[str, str]:
    """Section 5 word via the Packet-A helper (same function, same numbers)."""
    return pr.decide_word(kprime, k0, w_lo, w_hi, r_lo, r_hi)


def write_seg_file(path: Path, payload: dict) -> None:
    """Per-block checkpoint: full-file rewrite + flush (simplest correct)."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(payload, indent=1, sort_keys=True, default=str))
        f.flush()


def read_seg_file(path: Path) -> dict:
    """Read back one SEG checkpoint."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_manifest(uuid8: str, validation_seed: int) -> dict:
    """SEG_MANIFEST.json content: uuid8, seed, 6 ascending idx ranges."""
    return {"uuid8": uuid8, "validation_seed": int(validation_seed),
            "num_segments": NUM_SEGMENTS,
            "ranges": [[g * FRAMES_PER_SEGMENT,
                        g * FRAMES_PER_SEGMENT + FRAMES_PER_SEGMENT - 1]
                       for g in range(NUM_SEGMENTS)],
            "closed": {str(g): False for g in range(NUM_SEGMENTS)}}


def assemble_rows(seg_rows: list[list[dict]]) -> list[dict]:
    """Section 3.6 assembly gate: 6 x 40, ascending, no overlap/gap.

    REFUSE on short (<240), overlap, gap, or seed mismatch; otherwise the
    idx-ordered concatenation. No decode, no word here.
    """
    if len(seg_rows) != NUM_SEGMENTS:
        raise pr.Refusal(f"assembly REFUSE: {len(seg_rows)} segments != {NUM_SEGMENTS}")
    flat: list[dict] = []
    for g, rows in enumerate(seg_rows):
        if len(rows) != FRAMES_PER_SEGMENT:
            raise pr.Refusal(f"assembly REFUSE: segment {g} has {len(rows)} rows "
                             f"!= {FRAMES_PER_SEGMENT}")
        want = segment_idx_list(g)
        got = sorted(int(r["block_idx"]) for r in rows)
        if got != want:
            raise pr.Refusal(f"assembly REFUSE: segment {g} idx mismatch "
                             f"(overlap/gap/order drift)")
        for r in rows:
            if int(r["seed"]) != pr.FRAME_BASE + int(r["block_idx"]):
                raise pr.Refusal(f"assembly REFUSE: segment {g} seed mismatch")
        flat.extend(rows)
    flat.sort(key=lambda r: int(r["block_idx"]))
    if [int(r["block_idx"]) for r in flat] != list(range(pr.N_FRAMES)):
        raise pr.Refusal("assembly REFUSE: concatenated idx != 0..239 exactly once")
    seeds = {int(r["seed"]) for r in flat}
    if seeds != {pr.FRAME_BASE + i for i in range(pr.N_FRAMES)}:
        raise pr.Refusal("assembly REFUSE: seed set != frozen 240")
    return flat


def _read_inputs(inputs: list[str]) -> tuple[dict, list[dict], dict, str]:
    """Shared input gates + reads (transcription + I-5-vs-I-6 identical to A)."""
    labels = [validate_input_path(s) for s in inputs]
    if sorted(inputs) != sorted(pr.FROZEN_INPUTS.keys()):
        raise pr.Refusal("input set is not exactly the frozen nine")
    path_of = {label: p for p, label in pr.FROZEN_INPUTS.items()}
    order = [pr.FROZEN_INPUTS[s] for s in sorted(pr.FROZEN_INPUTS.keys())]
    docs: dict[str, dict] = {}
    input_records = []
    for label in order:
        path = Path(path_of[label])
        raw = path.read_bytes()
        input_records.append({"path": path_of[label], "bytes": len(raw),
                              "mtime_utc": pr._utc_mtime(path)})
        if label in ("CQ-20a", "CQ-20b", "CQ-J21a", "CQ-J21b", "CQ-J21c", "S0"):
            docs[label] = json.loads(raw)
    for label in ("CQ-20a", "CQ-20b", "CQ-J21a", "CQ-J21b", "CQ-J21c"):
        doc = docs[label]
        if doc.get("status") != "OK":
            raise pr.Refusal(f"{label}: status != OK")
        ser = float(doc["channel"]["ser"])
        if not pr.SER_RANGE[0] <= ser <= pr.SER_RANGE[1]:
            raise pr.Refusal(f"{label}: ser {ser} outside the frozen band")
    j21c = docs["CQ-J21c"]["channel"]
    ser_f = float(j21c["ser"])
    pm = j21c["pm1_mass"]
    m0_f, mp1_f, mm1_f = float(pm["0"]), float(pm["+1"]), float(pm["-1"])
    p_f = [float(v) for v in j21c["plane_rates_lsb_first"]]
    h1_f = float(j21c["H_U1_given_B"])
    h2_f = float(j21c["H_U2_given_U1B"])
    hab_f = float(j21c["H_A_given_B"])
    transcription = [ser_f, m0_f, mp1_f, mm1_f] + p_f + [h1_f, h2_f, hab_f]
    frozen = [pr.T_SER, pr.T_M0, pr.T_MP1, pr.T_MM1] + pr.T_P + [pr.T_H1, pr.T_H2, pr.T_HAB]
    if len(p_f) != pr.N_BITS or max(abs(a - b) for a, b in zip(transcription, frozen)) > pr.TRANSCRIPTION_TOL:
        raise pr.Refusal("CQ-J21c file values drift from the section 2.1 transcription")
    s0j = docs["S0"]["sources"]["CQ-J21c"]
    if [float(v) for v in s0j["p_k"]] != p_f or float(s0j["coherence"]["H_A_given_B"]) != hab_f:
        raise pr.Refusal("I-5 vs I-6 bitwise disagreement on the J21c vector")
    baseline = json.loads(Path(path_of["BASELINE"]).read_bytes())
    old_stage1 = [r for r in baseline["rows"] if r.get("stage") == "stage1"]
    if len(old_stage1) != pr.N_FRAMES:
        raise pr.Refusal(f"baseline Stage-1 row count {len(old_stage1)} != {pr.N_FRAMES}")
    old_failed = {int(r["seed"]): bool(int(r["failed"])) for r in old_stage1}
    if set(old_failed) != {pr.FRAME_BASE + i for i in range(pr.N_FRAMES)}:
        raise pr.Refusal("baseline Stage-1 seeds are not the frozen 240-frame set")
    if sum(old_failed.values()) != pr.K0_BASELINE:
        raise pr.Refusal("baseline k0 drift from frozen 10/240")
    summary_text = Path(path_of["SUMMARY"]).read_text(encoding="utf-8")
    if f"k={pr.K0_BASELINE}/{pr.N_FRAMES}" not in summary_text:
        raise pr.Refusal("I-9 summary echo does not carry the frozen k0 line")
    if pr.b2f.MAX_ITER != pr.MAX_ITER:
        raise pr.Refusal(f"kernel setting drift: b2f.MAX_ITER={pr.b2f.MAX_ITER}")
    sampler = {"ser": ser_f, "m_0": m0_f, "m_plus1": mp1_f, "m_minus1": mm1_f,
               "p_k": p_f, "graph": path_of["GRAPH"]}
    return docs, input_records, {"old_failed": old_failed, **sampler}, path_of["GRAPH"]


def run_segment(inputs: list[str], root: str, segment_index: int,
                num_segments: int, validation_seed: int) -> dict:
    """Run one 40-frame segment with per-block SEG rewrite. Returns payload."""
    t_start = time.perf_counter()
    validate_num_segments(num_segments)
    g = int(segment_index)
    idx_list = segment_idx_list(g, num_segments)
    validate_root_string(root)
    rootdir = Path(root)
    rootdir.mkdir(parents=False, exist_ok=True)
    for name in ("PROXY_RESULT.json", "PROXY_SUMMARY.md", f"SEG_{g}.json"):
        if (rootdir / name).exists():
            raise pr.Refusal(f"output collision: {rootdir / name} already exists")
    uuid8 = str(root).rsplit("_", 1)[-1]
    man_path = rootdir / "SEG_MANIFEST.json"
    if man_path.exists():
        man = json.loads(man_path.read_text(encoding="utf-8"))
        if man.get("uuid8") != uuid8 or int(man.get("validation_seed", -1)) != int(validation_seed):
            raise pr.Refusal("manifest uuid8/seed mismatch at segment start")
    else:
        man = build_manifest(uuid8, validation_seed)
        write_seg_file(man_path, man)

    _, input_records, samp, graph_path = _read_inputs(inputs)
    m0_f, mp1_f, mm1_f = samp["m_0"], samp["m_plus1"], samp["m_minus1"]
    p_f, ser_f = samp["p_k"], samp["ser"]

    rng_v = np.random.default_rng(int(validation_seed))
    av, bv = pr.draw_frame(rng_v, pr.N_VALID, m0_f, mp1_f, mm1_f)
    emer_rates = pr.gray_plane_rates(av, bv)
    emer_ser = float(np.mean(np.asarray(pr.v25.gray_label(av))
                             != np.asarray(pr.v25.gray_label(bv))))
    gate = pr.validation_gate(emer_rates, p_f, pr.N_VALID, emer_ser, ser_f)

    marg_table, u1map = pr.build_exact_prior_table(m0_f, mp1_f, mm1_f)

    def graph_loader(instance: int, trials: int) -> dict:
        if instance != 2026092001 or trials != pr.p1.P1_MAX_TRIALS:
            raise pr.Refusal("graph loader got a non-frozen seed or trial count")
        artifact = json.loads(Path(graph_path).read_bytes())
        pr.m3b.validate_graph_artifact(artifact, "M3B-R1")
        triples = [tuple(int(v) for v in t) for t in artifact["triples"]]
        return {"n": 1024, "m": 208, "triples": triples, "status": "ok",
                "four_cycles": artifact["four_cycles"],
                "rank": artifact["rank"], "min_girth": artifact["min_girth"]}

    pinned = pr.p1.construct_and_pin("P1S1-R1", graph_loader, pr.p1.production_rank_fn)
    base = pinned["base"]
    field = pr.GF2mField.create(pr.s2.Q)
    dense = pr.peg.sparse_to_dense(base["triples"], 1024, pr.M_STAGE1, field)

    seg_path = rootdir / f"SEG_{g}.json"
    rows: list[dict] = []
    rss_peak = 0.0
    for idx in idx_list:
        if time.perf_counter() - t_start > SEG_WALL_CAP_S:
            raise pr.Refusal(f"segment {g} wall breach: INCOMPLETE, retained")
        try:
            rss = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) / (1024.0 * 1024.0)
        except Exception:  # noqa: BLE001 -- probe failure never halts
            rss = 0.0
        rss_peak = max(rss_peak, rss)
        if rss >= pr.RSS_CAP_GIB:
            raise pr.Refusal(f"segment {g} RSS breach before block {idx}: INCOMPLETE")
        out = pr.stage1_block_outcome(base, dense, field, pr.FRAME_BASE + idx,
                                      marg_table, u1map, m0_f, mp1_f, mm1_f)
        if out["wall_s"] > pr.PER_BLOCK_CAP_S:
            out.update({"status": "overrun", "failed": 1, "undetected": 0,
                        "block_idx": idx})
            rows.append(out)
            write_seg_file(seg_path, {"segment_index": g, "num_segments": NUM_SEGMENTS,
                                      "idx_range": [idx_list[0], idx_list[-1]],
                                      "validation": gate, "rows": rows,
                                      "block_count": len(rows),
                                      "wall_s": time.perf_counter() - t_start,
                                      "peak_rss_gib": rss_peak})
            raise pr.Refusal(f"per-block cap overrun at block {idx}: INCOMPLETE")
        out["block_idx"] = idx
        rows.append(out)
        write_seg_file(seg_path, {"segment_index": g, "num_segments": NUM_SEGMENTS,
                                  "idx_range": [idx_list[0], idx_list[-1]],
                                  "validation": gate, "rows": rows,
                                  "block_count": len(rows),
                                  "wall_s": time.perf_counter() - t_start,
                                  "peak_rss_gib": rss_peak})
    payload = read_seg_file(seg_path)
    man = json.loads(man_path.read_text(encoding="utf-8"))
    man["closed"][str(g)] = True
    write_seg_file(man_path, man)
    print(f"segment {g} closed: {len(rows)}/40 rows in {root}")
    return payload


def run_assemble(inputs: list[str], root: str, validation_seed: int) -> dict:
    """Assemble D-1/D-2 only on 240/240. No decode in this mode."""
    validate_root_string(root)
    rootdir = Path(root)
    if not rootdir.is_dir():
        raise pr.Refusal(f"assemble REFUSE: root {root} absent")
    for name in ("PROXY_RESULT.json", "PROXY_SUMMARY.md"):
        if (rootdir / name).exists():
            raise pr.Refusal(f"output collision: {rootdir / name} already exists")
    _, input_records, samp, _ = _read_inputs(inputs)
    man_path = rootdir / "SEG_MANIFEST.json"
    if not man_path.exists():
        raise pr.Refusal("assemble REFUSE: manifest absent")
    man = json.loads(man_path.read_text(encoding="utf-8"))
    if man.get("num_segments") != NUM_SEGMENTS or int(man.get("validation_seed", -1)) != int(validation_seed):
        raise pr.Refusal("assemble REFUSE: manifest seed/count mismatch")
    seg_rows, validations = [], []
    for g in range(NUM_SEGMENTS):
        p = rootdir / f"SEG_{g}.json"
        if not p.exists():
            raise pr.Refusal(f"assemble REFUSE: SEG_{g}.json missing")
        seg = read_seg_file(p)
        if int(seg.get("segment_index", -1)) != g or seg.get("num_segments") != NUM_SEGMENTS:
            raise pr.Refusal(f"assemble REFUSE: SEG_{g}.json header mismatch")
        if seg.get("validation", {}).get("verdict") != "PASS":
            raise pr.Refusal(f"assemble REFUSE: segment {g} validation not PASS")
        seg_rows.append(seg["rows"])
        validations.append(seg["validation"])
    rows = assemble_rows(seg_rows)
    new_failed = {int(r["seed"]): bool(int(r["failed"])) for r in rows}
    kprime = sum(new_failed.values())
    w_lo, w_hi = pr.wilson(kprime, pr.N_FRAMES)
    paired = pr.paired_table(samp["old_failed"], new_failed)
    word, clause = pr.decide_word(kprime, pr.K0_BASELINE, w_lo, w_hi, pr.R_LO, pr.R_HI)
    result = {
        "inputs": input_records,
        "sampler": {"source": pr.SAMPLER_SOURCE, "ser": samp["ser"],
                     "m_0": samp["m_0"], "m_plus1": samp["m_plus1"],
                     "m_minus1": samp["m_minus1"], "p_k": samp["p_k"],
                     "validation_seed": int(validation_seed), "n_valid": pr.N_VALID,
                     "graph": samp["graph"],
                     "segmentation": {"num_segments": NUM_SEGMENTS,
                                      "frames_per_segment": FRAMES_PER_SEGMENT,
                                      "order": "ascending",
                                      "ranges": man["ranges"]}},
        "validation": {"per_segment": validations, "verdict": "PASS"},
        "stage1": {"rows": rows, "kprime_over_240": f"{kprime}/{pr.N_FRAMES}",
                   "kprime": kprime, "k0": pr.K0_BASELINE,
                   "wilson_lo": w_lo, "wilson_hi": w_hi, "wilson_z": pr.WILSON_Z,
                   "undetected_new": sum(int(r.get("undetected", 0)) for r in rows)},
        "paired": paired,
        "real_comparator": {"arm": "M0-2M m=208 (packet section 4 frozen)",
                            "band_lo": pr.R_LO, "band_hi": pr.R_HI},
        "decision": {"word": word, "clause": clause, "kprime": kprime,
                     "k0": pr.K0_BASELINE,
                     "overlap_Wprime_R": pr.intervals_overlap(w_lo, w_hi, pr.R_LO, pr.R_HI)},
        "resources": {"command": " ".join(sys.argv)},
        "claim_ceiling": pr.CEILING,
    }
    (rootdir / "PROXY_RESULT.json").write_text(
        json.dumps(result, indent=1, sort_keys=True, default=str), encoding="utf-8")
    (rootdir / "PROXY_SUMMARY.md").write_text(pr.write_summary(result), encoding="utf-8")
    print(f"assembled 240/240: {word} ({clause})")
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Segmented proxy-recalibration driver (R2)")
    ap.add_argument("--cq20a", required=True)
    ap.add_argument("--cq20b", required=True)
    ap.add_argument("--cqj21a", required=True)
    ap.add_argument("--cqj21b", required=True)
    ap.add_argument("--cqj21c", required=True)
    ap.add_argument("--s0-result", required=True)
    ap.add_argument("--graph", required=True)
    ap.add_argument("--baseline-rows", required=True)
    ap.add_argument("--baseline-summary", required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--segment-index", type=int, default=None)
    ap.add_argument("--num-segments", type=int, required=True)
    ap.add_argument("--validation-seed", type=int, required=True)
    ap.add_argument("--execute-synthetic", action="store_true")
    ap.add_argument("--execution-authorized", action="store_true")
    ap.add_argument("--assemble", action="store_true")
    args = ap.parse_args(argv)
    try:
        require_dual_flags(args.execute_synthetic, args.execution_authorized)
        validate_num_segments(args.num_segments)
    except pr.Refusal as e:
        print(f"STOP: {e}", file=sys.stderr)
        return 2
    inputs = [args.cq20a, args.cq20b, args.cqj21a, args.cqj21b, args.cqj21c,
              args.s0_result, args.graph, args.baseline_rows, args.baseline_summary]
    rootdir = Path(args.root)
    try:
        if args.assemble:
            run_assemble(inputs, args.root, int(args.validation_seed))
        else:
            if args.segment_index is None:
                raise pr.Refusal("refused: --segment-index g (0..5) is required")
            run_segment(inputs, args.root, int(args.segment_index),
                        int(args.num_segments), int(args.validation_seed))
    except pr.Refusal as e:
        try:
            rootdir.mkdir(parents=False, exist_ok=True)
            with open(rootdir / "PROXY_LOG.md", "a", encoding="utf-8") as f:
                f.write(f"\nSTOP: {e}\n")
        except OSError:
            pass
        print(f"STOP: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
