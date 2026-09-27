"""M3-b paired synthetic runner over the accepted M3-a graph artifacts.

This adapter reuses the P1 Stage-1 execution core and b2f decoder. Its
constructor callback loads an already accepted M3-a graph twice; it does not
run PEG or claim two fresh constructions.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable

from comparison_bench.src.comparison_bench.cli import p1_stage1_runner as p1

__all__ = [
    "M3B_ROOT_PREFIX", "ARMS", "validate_graph_artifact",
    "load_p1_comparator", "run_m3b_arm", "main",
]

M3B_ROOT_PREFIX = "workspace/m3b_nested_paired_20260926/"
M3A_ROOT = Path("workspace/m3a_nested_200p8_20260926")
FRAME_SEEDS = tuple(2026096401 + i for i in range(240))
RESCUE_DISCLOSURE_BITS = 40

ARMS: dict[str, dict[str, Any]] = {
    "M3B-R1": {
        "index": 1,
        "p1_arm": "P1S1-R1",
        "construction_seed": 2026092001,
        "extension_seed": 2026096801,
        "graph": M3A_ROOT / "arm1.json",
        "comparator": Path("workspace/P1_STAGE1/P1S1-R1_ef7da79b/rows.json"),
    },
    "M3B-R2": {
        "index": 2,
        "p1_arm": "P1S1-R2",
        "construction_seed": 2026092011,
        "extension_seed": 2026096811,
        "graph": M3A_ROOT / "arm2.json",
        "comparator": Path("workspace/P1_STAGE1/P1S1-R2_22754019/rows.json"),
    },
}


class M3BError(ValueError):
    """Frozen M3-b input or accounting contract violation."""


def read_json(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as stream:
        return json.load(stream)


def _arm_spec(arm: str) -> dict[str, Any]:
    if arm not in ARMS:
        raise M3BError(f"arm must be exactly M3B-R1 or M3B-R2 (got {arm!r})")
    return ARMS[arm]


def _integer(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise M3BError(f"{name} must be an integer")
    return value


def _triples(values: Any, name: str) -> list[tuple[int, int, int]]:
    if not isinstance(values, list):
        raise M3BError(f"{name} must be a list")
    result: list[tuple[int, int, int]] = []
    for index, item in enumerate(values):
        if not isinstance(item, (list, tuple)) or len(item) != 3:
            raise M3BError(f"{name}[{index}] must be an (row, variable, GF32) triple")
        row, variable, label = (_integer(v, f"{name}[{index}]") for v in item)
        if not 0 <= row < 208 or not 0 <= variable < 1024 or not 1 <= label <= 31:
            raise M3BError(f"{name}[{index}] is outside the frozen GF(32) graph")
        result.append((row, variable, label))
    if len(set(result)) != len(result):
        raise M3BError(f"{name} contains duplicate triples")
    return result


def validate_graph_artifact(data: dict[str, Any], arm: str) -> dict[str, Any]:
    """Check all frozen M3-a graph identity, size, label and prefix pins."""
    spec = _arm_spec(arm)
    pins = {
        "status": "ok",
        "arm": spec["index"],
        "base_seed": spec["construction_seed"],
        "extension_seed": spec["extension_seed"],
        "n": 1024,
        "m_base": 200,
        "m": 208,
        "base_rank": 200,
        "rank": 208,
        "base_four_cycles": 0,
        "four_cycles": 0,
    }
    for key, expected in pins.items():
        if data.get(key) != expected:
            raise M3BError(f"{arm} graph pin {key}={data.get(key)!r}, expected {expected!r}")
    if data.get("base_prefix_unchanged") is not True:
        raise M3BError(f"{arm} graph does not attest an unchanged base prefix")
    if data.get("twice_identical") is not True:
        raise M3BError(f"{arm} upstream M3-a twice-identical assertion is not true")

    base = _triples(data.get("base_triples"), "base_triples")
    added = _triples(data.get("added_triples"), "added_triples")
    full = _triples(data.get("triples"), "triples")
    if len(base) != 2048 or len(added) != 80 or len(full) != 2128:
        raise M3BError(f"{arm} graph edge counts must be 2048 + 80 = 2128")
    if any(row >= 200 for row, _, _ in base):
        raise M3BError(f"{arm} base_triples include an extension row")
    if any(row < 200 for row, _, _ in added):
        raise M3BError(f"{arm} added_triples include a base row")
    if full[:len(base)] != base or full != base + added:
        raise M3BError(f"{arm} full triples do not preserve the exact stored base prefix")
    added_degrees = [sum(row == r for row, _, _ in added) for r in range(200, 208)]
    if added_degrees != [10] * 8 or data.get("added_row_degrees") != [10] * 8:
        raise M3BError(f"{arm} extension must contain eight degree-10 rows")
    base_variable_degrees = [sum(variable == c for _, variable, _ in base)
                             for c in range(1024)]
    observed_histogram: dict[str, int] = {}
    for degree in base_variable_degrees:
        key = str(degree)
        observed_histogram[key] = observed_histogram.get(key, 0) + 1
    if (observed_histogram != {"2": 1024}
            or data.get("base_variable_degree_histogram") != observed_histogram):
        raise M3BError(f"{arm} base variable degree histogram does not match M3-a")
    if len({variable for _, variable, _ in added}) != 80:
        raise M3BError(f"{arm} added rows do not use 80 globally unique variables")
    return {
        "arm": arm,
        "graph": str(spec["graph"]).replace("\\", "/"),
        "construction_seed": spec["construction_seed"],
        "extension_seed": spec["extension_seed"],
        "n": 1024,
        "m_base": 200,
        "m": 208,
        "base_rank": 200,
        "rank": 208,
        "base_four_cycles": 0,
        "four_cycles": 0,
        "base_prefix_unchanged": True,
        "added_row_degrees": added_degrees,
        "m3a_twice_identical": True,
        "triple_count": len(full),
    }


def _seed_rows(rows: list[dict[str, Any]], stage: str) -> dict[int, dict[str, Any]]:
    selected = [row for row in rows if row.get("stage") == stage]
    result: dict[int, dict[str, Any]] = {}
    for row in selected:
        seed = _integer(row.get("seed"), f"{stage} seed")
        if seed in result:
            raise M3BError(f"duplicate {stage} seed {seed}")
        result[seed] = row
    return result


def _failed_seeds(stage1: dict[int, dict[str, Any]]) -> set[int]:
    return {seed for seed, row in stage1.items() if int(row.get("failed", 0)) == 1}


def load_p1_comparator(path: str | Path, arm: str,
                       read: Callable[[str | Path], dict[str, Any]] = read_json
                       ) -> dict[str, Any]:
    """Load and validate one accepted, read-only P1 arm for matched frames."""
    spec = _arm_spec(arm)
    saved = read(path)
    summary = saved.get("summary", {})
    rows = saved.get("rows")
    if summary.get("verdict") != "COMPLETE":
        raise M3BError(f"P1 comparator is not COMPLETE: {path}")
    if summary.get("arm") != spec["p1_arm"] or summary.get("construct_instance") != spec["construction_seed"]:
        raise M3BError(f"P1 comparator arm or construction seed mismatch: {path}")
    if not isinstance(rows, list):
        raise M3BError(f"P1 comparator lacks rows: {path}")
    stage1 = _seed_rows(rows, "stage1")
    stage2 = _seed_rows(rows, "stage2-rescue")
    if set(stage1) != set(FRAME_SEEDS):
        raise M3BError("P1 comparator Stage-1 seeds do not match frozen 240-frame set")
    if set(stage2) != _failed_seeds(stage1):
        raise M3BError("P1 comparator Stage-2 rows are not exactly its Stage-1 failures")
    return {"summary": summary, "rows": rows, "stage1": stage1, "stage2": stage2}


def _final_outcomes(stage1: dict[int, dict[str, Any]],
                    stage2: dict[int, dict[str, Any]]) -> dict[int, bool | None]:
    outcomes: dict[int, bool | None] = {}
    for seed, row in stage1.items():
        if int(row.get("failed", 0)) == 0:
            outcomes[seed] = True
        elif seed in stage2:
            outcomes[seed] = int(stage2[seed].get("failed", 0)) == 0
        else:
            outcomes[seed] = None
    return outcomes


def _paired_transitions(old: dict[str, Any], new_rows: list[dict[str, Any]]) -> dict[str, Any]:
    new_s1 = _seed_rows(new_rows, "stage1")
    new_s2 = _seed_rows(new_rows, "stage2-rescue")
    if not set(new_s1).issubset(old["stage1"]):
        raise M3BError("new Stage-1 frame identities are outside the old paired set")
    old_outcomes = _final_outcomes(old["stage1"], old["stage2"])
    new_outcomes = _final_outcomes(new_s1, new_s2)
    counts = {"old_success_new_success": 0,
              "old_success_new_failure": 0,
              "old_failure_new_success": 0,
              "old_failure_new_failure": 0}
    comparable = 0
    for seed in new_s1:
        before, after = old_outcomes[seed], new_outcomes[seed]
        if after is None:
            continue
        comparable += 1
        key = ("old_success_" if before else "old_failure_") + (
            "new_success" if after else "new_failure")
        counts[key] += 1
    return {"matched_frame_count": comparable, "transitions": counts}


def _comparator_metrics(old: dict[str, Any]) -> dict[str, Any]:
    outcomes = _final_outcomes(old["stage1"], old["stage2"])
    return {
        "arm": old["summary"]["arm"],
        "stage1_failures": len(_failed_seeds(old["stage1"])),
        "attempted": len(old["stage2"]),
        "rescued": sum(int(row.get("failed", 0)) == 0
                        for row in old["stage2"].values()),
        "final_failures": sum(value is False for value in outcomes.values()),
        "historical_efficiency_values": "retained historical; not used as corrected comparison numbers",
    }


def _normalize_result(core: dict[str, Any], rows: list[dict[str, Any]],
                      arm: str, graph: dict[str, Any], loads: int,
                      comparator: dict[str, Any]) -> dict[str, Any]:
    spec = _arm_spec(arm)
    stage1 = _seed_rows(rows, "stage1")
    stage2 = _seed_rows(rows, "stage2-rescue")
    if set(stage1) - set(FRAME_SEEDS) or set(stage2) - set(FRAME_SEEDS):
        raise M3BError("new decode rows do not use the frozen frame seeds")
    stage1_failures = sum(int(row.get("failed", 0)) == 1 for row in stage1.values())
    attempted = len(stage2)
    rescued = sum(int(row.get("failed", 0)) == 0 for row in stage2.values())
    final_fails = sum(
        outcome is False for outcome in _final_outcomes(stage1, stage2).values())
    complete = core.get("verdict") == "COMPLETE"
    if complete:
        if set(stage1) != set(FRAME_SEEDS) or set(stage2) != _failed_seeds(stage1):
            raise M3BError("completed run did not rescue exactly the Stage-1 failure set")
        if attempted != stage1_failures:
            raise M3BError("completed run attempted count differs from Stage-1 failures")
    undetected_s1 = sum(int(row.get("undetected", 0)) for row in stage1.values())
    undetected_s2 = sum(int(row.get("undetected", 0)) for row in stage2.values())
    rescue_disclosure_bits = RESCUE_DISCLOSURE_BITS * attempted
    expected_leak = p1.LEAK_BASE_BITS + rescue_disclosure_bits / p1.P1_N_BLOCKS
    f_exp = expected_leak / p1.CONTENT_BITS
    f_eff = (f_exp + p1.F_EFF_SLOPE * final_fails / p1.P1_N_BLOCKS
             if complete else None)

    normalized = dict(core)
    normalized.pop("pins", None)
    normalized.pop("route_ctx", None)
    normalized.pop("bar12_report_only", None)
    normalized.update({
        "arm": arm,
        "matched_p1_arm": spec["p1_arm"],
        "construct_instance": spec["construction_seed"],
        "graph_label": "M3-b nested A200+8 stored graph",
        "graph_provenance": {
            **graph,
            "artifact_load_count_by_constructor": loads,
            "stored_artifact_loaded_twice": loads == 2,
            "m3a_twice_identical": graph["m3a_twice_identical"],
            "m3a_twice_identical_is_upstream_fact": True,
            "m3b_new_peg_constructions": 0,
        },
        "pins": {
            "base_rank": graph["base_rank"],
            "full_rank": graph["rank"],
            "base_four_cycles": graph["base_four_cycles"],
            "full_four_cycles": graph["four_cycles"],
            "base_prefix_unchanged": graph["base_prefix_unchanged"],
            "added_row_degrees": graph["added_row_degrees"],
        },
        "stage1_fails": stage1_failures,
        "k_over_240": f"{stage1_failures}/240",
        "fer_stage1": (stage1_failures / 240 if len(stage1) == 240
                       else (stage1_failures / len(stage1) if stage1 else 0.0)),
        "attempted": attempted,
        "rescued": rescued,
        "rescue_attempt_rate": attempted / 240,
        "trigger_rate": attempted / 240,
        "rescue_disclosure_bits": rescue_disclosure_bits,
        "final_fails": final_fails,
        "f_over_240": f"{final_fails}/240" if complete else None,
        "fer_final": final_fails / 240 if complete else None,
        "undetected": undetected_s1 + undetected_s2,
        "undetected_stage1": undetected_s1,
        "undetected_stage2": undetected_s2,
        "e_leak": expected_leak,
        "f_exp": f_exp,
        "f_eff": f_eff,
        "headroom": p1.LEAK_CAP_BITS - expected_leak,
        "n_req": p1.n_required_for(f_exp) if complete and final_fails == 0 else None,
        "paired_frame_transitions": _paired_transitions(comparator, rows),
        "matched_p1_comparator": _comparator_metrics(comparator),
        "rescue_disclosure_accounting": {
            "formula": "E[leak]=1064+40*(attempted/240) bits",
            "rescue_bits_per_attempt": RESCUE_DISCLOSURE_BITS,
            "attempted_includes_failed_rescues": True,
            "basis": "modeled synthetic disclosure on frozen P1 entropy basis",
        },
        "claim_ceiling": (
            "two separate synthetic graph-instance diagnostics on the frozen "
            "decoder and 240 paired frames only; not a route, FER advantage, "
            "real-data, SKR, qualification, or publication claim"),
    })
    if not normalized["graph_provenance"]["stored_artifact_loaded_twice"]:
        raise M3BError("P1 core did not load the stored graph exactly twice")
    return normalized


def _result_markdown(summary: dict[str, Any]) -> str:
    provenance = summary["graph_provenance"]
    transitions = summary["paired_frame_transitions"]
    old = summary["matched_p1_comparator"]
    t = transitions["transitions"]
    return "\n".join([
        f"# M3-b nested A200+8 synthetic result — {summary['arm']}",
        "",
        f"- graph: `{provenance['graph']}`; construction seed "
        f"{provenance['construction_seed']}; extension seed {provenance['extension_seed']}; "
        "n=1024 GF(32), base m=200 and full m=208",
        f"- graph pins: ranks {provenance['base_rank']}/{provenance['rank']}; "
        f"four-cycles {provenance['base_four_cycles']}/{provenance['four_cycles']}; "
        f"base prefix unchanged={provenance['base_prefix_unchanged']}; "
        f"added row degrees={provenance['added_row_degrees']}",
        f"- provenance: this run loaded the same stored artifact twice="
        f"{provenance['stored_artifact_loaded_twice']}; upstream M3-a "
        f"twice-identical assertion={provenance['m3a_twice_identical']} "
        "(separate M3-a fact); new PEG constructions=0",
        f"- Stage-1: {summary['blocks_done']}/240; k={summary['stage1_fails']}/240; "
        f"undetected={summary['undetected_stage1']}",
        f"- Stage-2: attempted={summary['attempted']}, rescued={summary['rescued']}; "
        f"final F={summary['f_over_240']}; undetected={summary['undetected_stage2']}",
        f"- matched read-only P1 comparator {old['arm']}: "
        f"k={old['stage1_failures']}/240, attempted={old['attempted']}, "
        f"rescued={old['rescued']}, final F={old['final_failures']}/240; "
        f"old efficiency values are {old['historical_efficiency_values']}",
        f"- paired old-P1→new outcomes over {transitions['matched_frame_count']} "
        f"matched frames: {t}",
        f"- modeled disclosure: 40 bits per attempted rescue, including failed "
        f"rescues; total rescue disclosure={summary['rescue_disclosure_bits']} bits; "
        f"E[leak]={summary['e_leak']:.6f} bits; f_exp={summary['f_exp']:.9f}; "
        f"f_eff={summary['f_eff'] if summary['f_eff'] is not None else 'incomplete'}",
        f"- wall={summary['elapsed_s']:.3f}s; RSS={summary['rss_gib']:.6f} GiB; "
        f"verdict={summary['verdict']}",
        "- claim ceiling: two separate synthetic graph-instance diagnostics only; "
        "no route, FER advantage, real-data, SKR, qualification, or publication claim.",
        "",
    ])


def _make_writer(arm: str, graph: dict[str, Any], load_count: list[int],
                 comparator: dict[str, Any],
                 writer: Callable[[str, dict[str, str]], None] | None,
                 last_summary: list[dict[str, Any] | None]
                 ) -> Callable[[str, dict[str, str]], None]:
    write = writer or p1.default_writer

    def persist(root: str, files: dict[str, str]) -> None:
        payload = json.loads(files["rows.json"])
        rows = payload["rows"]
        summary = _normalize_result(payload["summary"], rows, arm, graph,
                                    load_count[0], comparator)
        last_summary[0] = summary
        for row in rows:
            row["arm"] = arm
            row["graph_label"] = "M3-b nested A200+8 stored graph"
        output = {
            "M3B_RESULT_" + arm + ".md": _result_markdown(summary),
            "rows.json": json.dumps({"summary": summary, "rows": rows},
                                    indent=1, sort_keys=True, default=str),
            "block_accounting.csv": files["block_accounting.csv"],
        }
        write(root, output)

    return persist


def _check_output_root(root: str, arm: str, root_prefix: str) -> None:
    spec = _arm_spec(arm)
    if not root.startswith(root_prefix):
        raise M3BError(f"root must be under the fresh M3-b family {root_prefix!r}")
    if not Path(root).name.startswith(spec["p1_arm"] + "_"):
        raise M3BError(f"root name must start with {spec['p1_arm']}_")
    if Path(root).resolve().parent != Path(root_prefix).resolve():
        raise M3BError(f"resolved root must be a direct child of M3-b family {root_prefix!r}")
    if any(part in p1.FORBIDDEN_ROOT_PARTS for part in Path(root).parts):
        raise M3BError(f"root is under a forbidden output tree: {root}")
    if os.path.exists(root):
        raise M3BError(f"root already exists; M3-b does not overwrite or resume: {root}")


def run_m3b_arm(*, arm: str, root: str,
                decode_fn: Callable | None,
                rescue_decode_fn: Callable | None,
                rank_fn: Callable | None,
                read: Callable[[str | Path], dict[str, Any]] = read_json,
                writer: Callable[[str, dict[str, str]], None] | None = None,
                clock: Callable | None = None,
                rss_fn: Callable | None = None,
                root_prefix: str = M3B_ROOT_PREFIX) -> dict[str, Any]:
    """Execute one injected arm through the P1 core; production wiring is CLI-only."""
    spec = _arm_spec(arm)
    _check_output_root(root, arm, root_prefix)
    if decode_fn is None or rescue_decode_fn is None or rank_fn is None:
        raise M3BError("decode_fn, rescue_decode_fn and rank_fn require explicit injection")
    comparator = load_p1_comparator(spec["comparator"], arm, read=read)
    load_count = [0]
    first_artifact: dict[str, Any] | None = None

    def construct_fn(instance: int, trials: int) -> dict[str, Any]:
        nonlocal first_artifact
        if instance != spec["construction_seed"] or trials != p1.P1_MAX_TRIALS:
            raise M3BError("P1 core requested a non-frozen graph seed or constructor trial count")
        artifact = read(spec["graph"])
        metadata = validate_graph_artifact(artifact, arm)
        load_count[0] += 1
        if load_count[0] > 2:
            raise M3BError("M3-b constructor callback loaded the graph more than twice")
        if first_artifact is None:
            first_artifact = artifact
        elif artifact != first_artifact:
            raise M3BError("the two callbacks did not load the same stored graph artifact")
        graph_output.update(metadata)
        return {
            "n": 1024,
            "m": 208,
            "triples": _triples(artifact["triples"], "triples"),
            "status": "ok",
            "family": "M3-b nested A200+8 stored GF(32) graph",
            "lambda_edge": None,
            "rho_edge": None,
            "rank": metadata["rank"],
            "four_cycles": metadata["four_cycles"],
            "min_girth": artifact.get("min_girth"),
        }

    # The first callback's pins are available to the writer by the time the
    # P1 core flushes its first result (both callbacks precede any decode).
    # Build this small output descriptor from frozen expected fields; the
    # constructor revalidates the persisted artifact before decode.
    graph_output = {
        "arm": arm,
        "graph": str(spec["graph"]).replace("\\", "/"),
        "construction_seed": spec["construction_seed"],
        "extension_seed": spec["extension_seed"],
        "n": 1024,
        "m_base": 200,
        "m": 208,
        "base_rank": 200,
        "rank": 208,
        "base_four_cycles": 0,
        "four_cycles": 0,
        "base_prefix_unchanged": True,
        "added_row_degrees": [10] * 8,
        "m3a_twice_identical": True,
        "triple_count": 2128,
    }
    last_summary: list[dict[str, Any] | None] = [None]
    out_writer = _make_writer(arm, graph_output, load_count, comparator,
                              writer, last_summary)
    core = p1.execute(
        root=root,
        arm=spec["p1_arm"],
        construct_fn=construct_fn,
        decode_fn=decode_fn,
        rescue_decode_fn=rescue_decode_fn,
        rank_fn=rank_fn,
        clock=clock,
        rss_fn=rss_fn,
        writer=out_writer,
        root_prefix=root_prefix,
    )
    if load_count[0] != 2:
        raise M3BError(f"expected exactly two stored-artifact loads, got {load_count[0]}")
    if last_summary[0] is None:
        raise M3BError("P1 core returned without writing its M3-b result")
    return last_summary[0]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="M3-b paired synthetic nested 200+8 runner")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--arm", choices=tuple(ARMS))
    ap.add_argument("--root", default="")
    ap.add_argument("--execute-synthetic", action="store_true")
    ap.add_argument("--execution-authorized", action="store_true")
    args = ap.parse_args(argv)

    if args.dry:
        if args.execute_synthetic or args.execution_authorized or args.arm or args.root:
            print("M3B refusal: --dry takes no arm, root or execution flags", file=sys.stderr)
            return 2
        print(json.dumps({"mode": "dry-zero-decoder", "graph_reads": 0,
                          "decoder_calls": 0, "arms": list(ARMS),
                          "root_family": M3B_ROOT_PREFIX}, indent=2))
        return 0

    # Both execution switches are checked before any graph, comparator or
    # channel file is opened and before the production decoder is bound.
    if not args.execute_synthetic or not args.execution_authorized:
        print("M3B refusal: require both --execute-synthetic and "
              "--execution-authorized before any reads", file=sys.stderr)
        return 2
    if args.arm is None or not args.root:
        print("M3B refusal: --arm and --root are required", file=sys.stderr)
        return 2
    spec = _arm_spec(args.arm)
    try:
        _check_output_root(args.root, args.arm, M3B_ROOT_PREFIX)
        bound = p1.s2c.bind_empirical_bundle(p1.CHANNEL_NPZ, p1.CHANNEL_SOURCE)
        if bound.get("source") != p1.CHANNEL_SOURCE:
            raise M3BError("bound channel source label mismatch")

        def decode_fn(construction: dict, seed: int, _bound=bound) -> dict:
            return p1.b2f.decode_block_marginal(
                construction, seed, _bound, p1.P1_N, p1.P1_M_BASE)

        def rescue_decode_fn(construction: dict, seed: int, _bound=bound) -> dict:
            return p1.b2f.decode_block_marginal(
                construction, seed, _bound, p1.P1_N, p1.P1_M_TOTAL)

        summary = run_m3b_arm(
            arm=args.arm,
            root=args.root,
            decode_fn=decode_fn,
            rescue_decode_fn=rescue_decode_fn,
            rank_fn=p1.production_rank_fn,
        )
        print(json.dumps(summary, indent=1, sort_keys=True, default=str))
        return 0 if summary["verdict"] == "COMPLETE" else 1
    except (M3BError, p1.Refusal) as exc:
        print(f"M3B refusal: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
