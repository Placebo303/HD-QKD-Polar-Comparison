"""Source-aware overlap diagnostics for accepted local GF(32) cycle words.

This reads only a completed short-cycle census. It never constructs graphs,
calls a decoder, or treats a Bhattacharyya overlap as an error probability.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import resource
import time
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from comparison_bench.cli import nbldpc_gf32_cycle_census as census
from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout

CONTRACT = "NBLDPC-GF32-CYCLE-SOURCE-OVERLAP-20261001/PREREG_AND_AUTH.md"
BATCH_UUID = "202e39a1-bf55-436a-ad3f-cad2d539e683"
OUT_ROOT_RELATIVE = Path("workspace") / "gf32_cycle_overlap_202e39a1"
REFERENCE_ROOT_RELATIVE = Path("workspace") / "gf32_cycle_census_475c2ad3"
REFERENCE_BATCH_UUID = "475c2ad3-bd5a-4000-8498-ea989bad1bba"
EDGE_BATCH_UUID = "1efed423-10c8-4c51-a119-844f2b922ab5"
GRAPH_SEEDS = tuple(range(2026093901, 2026093907))
MIN_ELL = 2
MAX_ELL = 6
POLY = 37
P0 = 0.550
SHAPE_COUNTS = ((1, 2295), (3, 1126), (7, 557), (15, 304), (31, 146))
SHAPE_TOTAL = 4428
WALL_CAP_S = 600.0
RSS_CAP_BYTES = 4 * 1024**3
MAX_CYCLE_ROWS = 600_000
RESOURCE_CHECK_ROWS = 1024

COMMAND = (
    "wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env "
    "PYTHONPATH=comparison_bench/src .venv/bin/python -m "
    "comparison_bench.cli.nbldpc_gf32_cycle_source_overlap --execute "
    "--out-root workspace/gf32_cycle_overlap_202e39a1"
)

SOURCE_COLUMNS = (
    "input_row", *census.CYCLE_COLUMNS,
    "control_orbit_key_json", "control_duplicate_orbit", "control_W",
    "control_positive_overlap_terms", "control_source_status",
    "edge_candidate_orbit_key_json", "edge_candidate_duplicate_orbit",
    "edge_candidate_W", "edge_candidate_positive_overlap_terms",
    "edge_candidate_source_status", "row_status", "failure_reason",
)

_GF32_MUL = np.asarray(
    [[layout.gf32_mul(a, b) for b in range(32)] for a in range(32)],
    dtype=np.uint8,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def validate_out_root(out_root: str | Path,
                      repo_root: str | Path | None = None) -> Path:
    root = Path(repo_root).resolve() if repo_root is not None else _repo_root()
    requested = Path(out_root)
    resolved = requested.resolve() if requested.is_absolute() \
        else (root / requested).resolve()
    expected = (root / OUT_ROOT_RELATIVE).resolve()
    if resolved != expected:
        raise ValueError("out-root must equal the frozen fresh root %s" % expected)
    if resolved.exists():
        raise FileExistsError("refusing existing output root %s" % resolved)
    return resolved


def dry_run(out_root: str | Path,
            repo_root: str | Path | None = None) -> dict[str, Any]:
    """Validate the destination without reading the census or writing files."""
    root = validate_out_root(out_root, repo_root=repo_root)
    return {
        "status": "DRY_RUN",
        "batch_uuid": BATCH_UUID,
        "out_root": str(root),
        "input_batch_uuid": REFERENCE_BATCH_UUID,
        "graph_seeds": list(GRAPH_SEEDS),
        "ell_range": [MIN_ELL, MAX_ELL],
        "row_cap": MAX_CYCLE_ROWS,
        "total_wall_cap_s": WALL_CAP_S,
        "rss_cap_bytes": RSS_CAP_BYTES,
        "census_artifact_reads": 0,
        "cycle_rows_read": 0,
        "graph_constructions": 0,
        "decoder_calls": 0,
        "writes": 0,
    }


def source_pmf() -> np.ndarray:
    """Return the exact frozen sparse iid marginal; no decoder floor is used."""
    if sum(count for _, count in SHAPE_COUNTS) != SHAPE_TOTAL:
        raise AssertionError("frozen shape counts do not sum to 4428")
    pmf = np.zeros(32, dtype=np.float64)
    pmf[0] = P0
    for symbol, count in SHAPE_COUNTS:
        pmf[symbol] = (1.0 - P0) * count / SHAPE_TOTAL
    if not math.isclose(math.fsum(float(value) for value in pmf), 1.0,
                        rel_tol=0.0, abs_tol=2e-15):
        raise ArithmeticError("frozen source PMF does not normalize")
    return pmf


def bhattacharyya_values(pmf: Any | None = None) -> np.ndarray:
    """Compute B(z)=sum_e sqrt(p(e)p(e xor z)) for all GF(32) shifts."""
    p = source_pmf() if pmf is None else np.asarray(pmf, dtype=np.float64)
    if p.shape != (32,) or not np.all(np.isfinite(p)) or np.any(p < 0.0):
        raise ValueError("source PMF must be 32 finite nonnegative values")
    if not math.isclose(math.fsum(float(value) for value in p), 1.0,
                        rel_tol=0.0, abs_tol=2e-15):
        raise ValueError("source PMF must sum to one")
    values = np.zeros(32, dtype=np.float64)
    for shift in range(32):
        values[shift] = math.fsum(
            math.sqrt(float(p[symbol]) * float(p[symbol ^ shift]))
            for symbol in range(32))
    if not math.isclose(float(values[0]), 1.0,
                        rel_tol=0.0, abs_tol=2e-15):
        raise ArithmeticError("B(0) must equal one for a normalized PMF")
    values[0] = 1.0
    return values


def direct_two_symbol_overlap(pmf: Any, shift: tuple[int, int] | list[int]
                              ) -> float:
    """Tiny-test oracle for the exact two-symbol shifted-source overlap."""
    p = np.asarray(pmf, dtype=np.float64)
    if p.shape != (32,) or len(shift) != 2:
        raise ValueError("direct overlap oracle requires a 32-bin PMF and two shifts")
    z0, z1 = (int(value) for value in shift)
    if not 0 <= z0 < 32 or not 0 <= z1 < 32:
        raise ValueError("GF(32) shifts must be in 0..31")
    return math.fsum(
        math.sqrt(float(p[a]) * float(p[b])
                  * float(p[a ^ z0]) * float(p[b ^ z1]))
        for a in range(32) for b in range(32))


def normalize_orbit(variables: list[int] | tuple[int, ...],
                    values: list[int] | tuple[int, ...]
                    ) -> tuple[tuple[int, int], ...]:
    """Canonical local word modulo nonzero GF(32) scalar multiplication."""
    variable_ids = tuple(int(value) for value in variables)
    word = tuple(int(value) for value in values)
    if not variable_ids or len(variable_ids) != len(word) \
            or len(set(variable_ids)) != len(variable_ids):
        raise ValueError("orbit variables and word values must be nonempty and distinct")
    if any(value < 0 or value >= 128 for value in variable_ids):
        raise ValueError("orbit variable id is outside the frozen graph")
    if any(value < 1 or value >= 32 for value in word):
        raise ValueError("local cycle word values must be nonzero GF(32) symbols")
    anchor_index = variable_ids.index(min(variable_ids))
    scale = census._gf32_inverse(word[anchor_index])
    normalized = tuple(int(_GF32_MUL[scale, value]) for value in word)
    return tuple(sorted(zip(variable_ids, normalized)))


def overlap_for_orbit(orbit: tuple[tuple[int, int], ...],
                      b_values: Any) -> dict[str, Any]:
    """Return W(c), its positive-term count and its source-overlap class."""
    values = tuple(int(value) for _, value in orbit)
    if not values or any(value < 1 or value >= 32 for value in values):
        raise ValueError("a unit-cycle orbit needs nonzero GF(32) values")
    b = np.asarray(b_values, dtype=np.float64)
    if b.shape != (32,):
        raise ValueError("B must contain 32 additive-shift overlaps")
    scalars = np.arange(1, 32, dtype=np.uint8)
    symbol_shifts = _GF32_MUL[scalars[:, None],
                              np.asarray(values, dtype=np.uint8)[None, :]]
    terms = np.prod(b[symbol_shifts], axis=1, dtype=np.float64)
    positive_terms = int(np.count_nonzero(terms > 0.0))
    total = math.fsum(float(value) for value in terms)
    return {
        "W": total,
        "positive_overlap_terms": positive_terms,
        "source_status": "ZERO_SOURCE_OVERLAP" if positive_terms == 0
        else "POSITIVE_OVERLAP",
        "terms": [float(value) for value in terms],
    }


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("predecessor artifact must contain a JSON object: %s" % path.name)
    return value


class PredecessorError(ValueError):
    """A census root that is missing, incomplete, or outside the frozen schema."""


def load_predecessor(reference_root: str | Path
                     ) -> dict[str, Any]:
    """Read/validate census metadata and expected cycle row counts only."""
    root = Path(reference_root)
    manifest_path = root / "manifest.json"
    summary_path = root / "summary.json"
    cycles_path = root / "cycles.csv"
    missing = [path.name for path in (manifest_path, summary_path, cycles_path)
               if not path.is_file()]
    if missing:
        raise PredecessorError("missing census artifacts: %s" % ",".join(missing))
    manifest = _load_json(manifest_path)
    summary = _load_json(summary_path)
    if manifest.get("batch_uuid") != REFERENCE_BATCH_UUID \
            or summary.get("batch_uuid") != REFERENCE_BATCH_UUID:
        raise PredecessorError("census batch UUID does not match frozen input")
    if (manifest.get("status") != "INVENTORY_COMPLETE"
            or manifest.get("batch_complete") is not True
            or summary.get("terminal_status") != "INVENTORY_COMPLETE"
            or summary.get("batch_complete") is not True):
        raise PredecessorError("census predecessor is incomplete")
    if (manifest.get("reference_batch_uuid") != EDGE_BATCH_UUID
            or manifest.get("graph_seeds") != list(GRAPH_SEEDS)
            or summary.get("graph_seeds") != list(GRAPH_SEEDS)
            or manifest.get("decoder_calls") != 0
            or manifest.get("sampled_frames") != 0):
        raise PredecessorError("census provenance/profile does not match frozen predecessor")
    if summary.get("ell_range") != [MIN_ELL, MAX_ELL]:
        raise PredecessorError("census cycle-length range differs from frozen scope")
    if manifest.get("truth_prior_or_conditional_arrays_saved") is not False \
            or summary.get("truth_prior_or_conditional_arrays_saved") is not False:
        raise PredecessorError("census artifacts violate the no-sampled-array rule")

    graph_diags = manifest.get("graph_diagnostics")
    candidate_diags = manifest.get("candidate_diagnostics")
    if not isinstance(graph_diags, list) or not isinstance(candidate_diags, list) \
            or len(graph_diags) != len(GRAPH_SEEDS) \
            or len(candidate_diags) != len(GRAPH_SEEDS):
        raise PredecessorError("census metadata lacks six accepted graph diagnostics")
    for seed, graph_diag, candidate_diag in zip(
            GRAPH_SEEDS, graph_diags, candidate_diags):
        if (int(graph_diag.get("graph_seed", -1)) != seed
                or graph_diag.get("status") != "ok"
                or graph_diag.get("admitted") is not True
                or graph_diag.get("gf32_rank") != 52
                or int(candidate_diag.get("graph_seed", -1)) != seed
                or candidate_diag.get("control_admitted") is not True
                or candidate_diag.get("candidate_admitted") is not True
                or candidate_diag.get("construction_stop") is not False):
            raise PredecessorError("census graph/candidate admission is incomplete")

    per_graph = summary.get("per_graph")
    totals_by_ell = summary.get("totals_by_ell")
    if not isinstance(per_graph, dict) or not isinstance(totals_by_ell, dict):
        raise PredecessorError("census summary lacks complete cycle counts")
    expected: dict[int, dict[int, int]] = {}
    for seed in GRAPH_SEEDS:
        entry = per_graph.get(str(seed))
        if not isinstance(entry, dict) or entry.get("status") != "COMPLETE":
            raise PredecessorError("census graph %d is incomplete" % seed)
        by_ell = entry.get("by_ell")
        if not isinstance(by_ell, dict):
            raise PredecessorError("census graph %d lacks per-length counts" % seed)
        expected[seed] = {}
        row_sum = 0
        for ell in range(MIN_ELL, MAX_ELL + 1):
            cell = by_ell.get(str(ell))
            if not isinstance(cell, dict):
                raise PredecessorError("census graph %d lacks ell=%d" % (seed, ell))
            count = cell.get("cycle_count")
            if not isinstance(count, int) or count < 0:
                raise PredecessorError("invalid census row count for graph %d" % seed)
            expected[seed][ell] = count
            row_sum += count
        if entry.get("cycle_count") != row_sum:
            raise PredecessorError("census graph totals do not match per-ell counts")

    for ell in range(MIN_ELL, MAX_ELL + 1):
        total_cell = totals_by_ell.get(str(ell))
        if not isinstance(total_cell, dict) or total_cell.get("cycle_count") != sum(
                expected[seed][ell] for seed in GRAPH_SEEDS):
            raise PredecessorError("census batch totals do not match per-graph counts")
    total_rows = sum(sum(by_ell.values()) for by_ell in expected.values())
    return {
        "root": root,
        "manifest": manifest,
        "summary": summary,
        "expected_by_graph_ell": expected,
        "expected_rows": total_rows,
    }


def _parse_json_list(value: str, field: str) -> list[Any]:
    parsed = json.loads(value)
    if not isinstance(parsed, list):
        raise ValueError("%s must be a JSON list" % field)
    return parsed


def _strict_bool(value: str, field: str) -> bool:
    if value == "True" or value == "true":
        return True
    if value == "False" or value == "false":
        return False
    raise ValueError("%s must be a serialized boolean" % field)


def _verify_arm(row: Mapping[str, str], prefix: str,
                rows: list[int], variables: list[int], ell: int
                ) -> dict[str, Any]:
    num = [int(value) for value in _parse_json_list(
        row[prefix + "_numerator_coefficients_json"], prefix + " numerator")]
    den = [int(value) for value in _parse_json_list(
        row[prefix + "_denominator_coefficients_json"], prefix + " denominator")]
    if len(num) != ell or len(den) != ell \
            or any(value < 1 or value >= 32 for value in num + den):
        raise ValueError("%s saved edge coefficients are invalid" % prefix)
    product = 1
    for top, bottom in zip(num, den):
        product = int(layout.gf32_mul(product, census._gf32_div(top, bottom)))
    saved_product = int(row[prefix + "_product"])
    saved_unit = _strict_bool(row[prefix + "_unit"], prefix + " unit flag")
    if saved_product != product or saved_unit != (product == 1):
        raise ValueError("%s saved product/unit flag disagrees with edge coefficients"
                         % prefix)
    witness = json.loads(row[prefix + "_witness_values_json"])
    if not saved_unit:
        if witness is not None:
            raise ValueError("%s nonunit cycle must not carry a codeword witness" % prefix)
        return {"unit": False, "orbit": None, "overlap": None}
    if not isinstance(witness, list) or len(witness) != ell \
            or any(not isinstance(value, int) or value < 1 or value >= 32
                   for value in witness) or witness[0] != 1:
        raise ValueError("%s unit cycle has an invalid normalized witness" % prefix)
    for index in range(ell):
        previous = (index - 1) % ell
        left = int(_GF32_MUL[den[previous], witness[previous]])
        right = int(_GF32_MUL[num[index], witness[index]])
        if left ^ right:
            raise ValueError("%s witness fails a local check equation" % prefix)
    orbit = normalize_orbit(variables, witness)
    return {"unit": True, "orbit": orbit, "overlap": None}


def verify_cycle_row(row: Mapping[str, str]) -> dict[str, Any]:
    """Validate saved cycle algebra and return its two local codeword witnesses."""
    graph_seed = int(row["graph_seed"])
    if graph_seed not in GRAPH_SEEDS:
        raise ValueError("cycle row graph seed is outside frozen six")
    ell = int(row["ell"])
    if ell < MIN_ELL or ell > MAX_ELL:
        raise ValueError("cycle row length is outside frozen ell=2..6")
    rows = [int(value) for value in _parse_json_list(
        row["check_rows_json"], "check rows")]
    variables = [int(value) for value in _parse_json_list(
        row["variable_columns_json"], "variable columns")]
    if (len(rows) != ell or len(variables) != ell
            or len(set(rows)) != ell or len(set(variables)) != ell
            or any(value < 0 or value >= 52 for value in rows)
            or any(value < 0 or value >= 128 for value in variables)):
        raise ValueError("cycle row has invalid simple-cycle vertices")
    key = tuple(int(value) for value in _parse_json_list(
        row["cycle_key_json"], "cycle key"))
    if census.canonical_cycle_key(rows, variables) != key:
        raise ValueError("saved cycle key is not canonical for its vertices")
    control = _verify_arm(row, "control", rows, variables, ell)
    candidate = _verify_arm(row, "candidate", rows, variables, ell)
    transition = (
        "unit_to_nonunit" if control["unit"] and not candidate["unit"] else
        "nonunit_to_unit" if candidate["unit"] and not control["unit"] else
        "both_unit" if control["unit"] and candidate["unit"] else "neither_unit"
    )
    if row["state_transition"] != transition:
        raise ValueError("saved unit/nonunit state transition is inconsistent")
    return {
        "graph_seed": graph_seed, "ell": ell, "rows": rows,
        "variables": variables, "cycle_key": list(key),
        "control": control, "edge_candidate": candidate,
    }


def _measure_arm(arm: Mapping[str, Any], b_values: Any,
                 seen_orbits: set[tuple[tuple[int, int], ...]]) -> dict[str, Any]:
    if not arm["unit"]:
        return {"unit": False, "orbit": None, "duplicate": False,
                "W": None, "positive_terms": None,
                "source_status": "NONUNIT_NO_LOCAL_CODEWORD"}
    orbit = arm["orbit"]
    duplicate = orbit in seen_orbits
    overlap = overlap_for_orbit(orbit, b_values)
    if not duplicate:
        seen_orbits.add(orbit)
    return {
        "unit": True,
        "orbit": orbit,
        "duplicate": duplicate,
        "W": overlap["W"],
        "positive_terms": overlap["positive_overlap_terms"],
        "source_status": overlap["source_status"],
    }


def _new_metric_counts() -> dict[str, Any]:
    return {
        "cycle_rows": 0,
        "unit_cycle_rows": 0,
        "nonunit_cycle_rows": 0,
        "unique_unit_orbits": 0,
        "duplicate_unit_rows": 0,
        "positive_overlap_orbits": 0,
        "zero_source_overlap_orbits": 0,
        "sum_W_unique_orbits": 0.0,
    }


def _new_graph_summary(seed: int,
                       expected_by_ell: Mapping[int, int] | None = None
                       ) -> dict[str, Any]:
    expected_by_ell = expected_by_ell or {}
    return {
        "graph_seed": int(seed), "status": "NOT_STARTED",
        "cycle_rows_expected": int(sum(expected_by_ell.values())),
        "cycle_rows_processed": 0,
        "by_ell": {
            str(ell): {
                "cycle_rows_expected": int(expected_by_ell.get(ell, 0)),
                "cycle_rows_processed": 0,
                "control": _new_metric_counts(),
                "edge_candidate": _new_metric_counts(),
            }
            for ell in range(MIN_ELL, MAX_ELL + 1)
        },
        "control_source_overlap_outcome": None,
        "edge_candidate_source_overlap_outcome": None,
    }


def _matrix_outcome(counts: Mapping[str, Any]) -> str:
    unique = int(counts["unique_unit_orbits"])
    positive = int(counts["positive_overlap_orbits"])
    zero = int(counts["zero_source_overlap_orbits"])
    if unique == 0:
        return "NO_UNIT_ORBITS_IN_CENSUS"
    if positive == 0:
        return "ZERO_SOURCE_OVERLAP_ONLY"
    if zero == 0:
        return "POSITIVE_OVERLAP_ONLY"
    return "MIXED_ZERO_AND_POSITIVE_OVERLAP"


def _add_arm_counts(counts: dict[str, Any], arm: Mapping[str, Any]) -> None:
    if not arm["unit"]:
        counts["nonunit_cycle_rows"] += 1
        return
    counts["unit_cycle_rows"] += 1
    if arm["duplicate"]:
        counts["duplicate_unit_rows"] += 1
        return
    counts["unique_unit_orbits"] += 1
    if arm["source_status"] == "ZERO_SOURCE_OVERLAP":
        counts["zero_source_overlap_orbits"] += 1
    else:
        counts["positive_overlap_orbits"] += 1
    counts["sum_W_unique_orbits"] = math.fsum(
        (float(counts["sum_W_unique_orbits"]), float(arm["W"])))


def _empty_summary() -> dict[str, Any]:
    return {
        "contract": CONTRACT, "batch_uuid": BATCH_UUID, "track": "EXPLORE",
        "reference_batch_uuid": REFERENCE_BATCH_UUID,
        "graph_seeds": list(GRAPH_SEEDS), "ell_range": [MIN_ELL, MAX_ELL],
        "batch_complete": False, "terminal_status": "RUNNING",
        "stop_reason": "", "reference_rows_expected": None,
        "input_rows_attempted": 0, "input_rows_processed": 0,
        "attempted_graphs": [], "completed_graphs": [],
        "resource_observations": {
            "check_count": 0, "last_elapsed_s": None,
            "last_sampled_rss_bytes": None,
            "max_sampled_rss_bytes": None,
            "terminal_sampled": False,
            "terminal_sample_stop_reason": None,
            "rss_sample_kind": "process high-water RSS at resource checkpoints",
        },
        "per_graph": {str(seed): _new_graph_summary(seed)
                      for seed in GRAPH_SEEDS},
        "totals_by_ell": None, "matrix_totals": None,
        "decoder_calls": 0, "graph_constructions": 0,
        "sampled_frames": 0, "truth_prior_arrays_saved": False,
        "claim_ceiling": (
            "dimensionless sum of local shifted-source Bhattacharyya overlaps "
            "for accepted simple unit-cycle codewords on the six fixed graphs "
            "and ell=2..6 only; not an error probability, FER, decoder result, "
            "global code or route claim"),
    }


def _plain(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def _json_write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(_plain(value), indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def _append_log(path: Path, message: str) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(message.rstrip() + "\n")


def _rss_bytes() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024


def _expected_counts(predecessor: Mapping[str, Any]) -> dict[int, dict[int, int]]:
    return predecessor["expected_by_graph_ell"]


def _set_graph_complete(summary: dict[str, Any], seed: int) -> None:
    entry = summary["per_graph"][str(seed)]
    expected = entry["cycle_rows_expected"]
    processed = entry["cycle_rows_processed"]
    if processed != expected:
        return
    for ell in range(MIN_ELL, MAX_ELL + 1):
        cell = entry["by_ell"][str(ell)]
        if cell["cycle_rows_processed"] != cell["cycle_rows_expected"]:
            return
    entry["status"] = "COMPLETE"
    entry["control_source_overlap_outcome"] = _matrix_outcome(
        _sum_metrics(entry, "control"))
    entry["edge_candidate_source_overlap_outcome"] = _matrix_outcome(
        _sum_metrics(entry, "edge_candidate"))
    if seed not in summary["completed_graphs"]:
        summary["completed_graphs"].append(seed)


def _sum_metrics(graph: Mapping[str, Any], arm_name: str) -> dict[str, Any]:
    totals = _new_metric_counts()
    for ell in range(MIN_ELL, MAX_ELL + 1):
        cell = graph["by_ell"][str(ell)][arm_name]
        for key in totals:
            if key == "sum_W_unique_orbits":
                totals[key] = math.fsum((float(totals[key]), float(cell[key])))
            else:
                totals[key] += int(cell[key])
    return totals


def _finalize_summary(summary: dict[str, Any]) -> None:
    totals_by_ell: dict[str, Any] = {}
    matrix_totals: dict[str, Any] = {}
    for ell in range(MIN_ELL, MAX_ELL + 1):
        totals_by_ell[str(ell)] = {
            "cycle_rows": sum(
                int(summary["per_graph"][str(seed)]["by_ell"][str(ell)][
                    "cycle_rows_processed"]) for seed in GRAPH_SEEDS),
            "control": _new_metric_counts(),
            "edge_candidate": _new_metric_counts(),
        }
        for arm_name in ("control", "edge_candidate"):
            target = totals_by_ell[str(ell)][arm_name]
            for seed in GRAPH_SEEDS:
                source = summary["per_graph"][str(seed)]["by_ell"][str(ell)][arm_name]
                for key in target:
                    if key == "sum_W_unique_orbits":
                        target[key] = math.fsum((float(target[key]),
                                                 float(source[key])))
                    else:
                        target[key] += int(source[key])

    for arm_name in ("control", "edge_candidate"):
        counts = _new_metric_counts()
        for seed in GRAPH_SEEDS:
            graph_counts = _sum_metrics(summary["per_graph"][str(seed)], arm_name)
            for key in counts:
                if key == "sum_W_unique_orbits":
                    counts[key] = math.fsum((float(counts[key]),
                                             float(graph_counts[key])))
                else:
                    counts[key] += int(graph_counts[key])
        matrix_totals[arm_name] = {
            **counts,
            "source_overlap_outcome": _matrix_outcome(counts),
            "by_ell": {
                ell: totals_by_ell[ell][arm_name]
                for ell in (str(value) for value in range(MIN_ELL, MAX_ELL + 1))
            },
        }
    summary["totals_by_ell"] = totals_by_ell
    summary["matrix_totals"] = matrix_totals


def _invalid_output_row(row: Mapping[str, str], row_number: int,
                        reason: str) -> dict[str, Any]:
    output = {name: row.get(name, "") for name in census.CYCLE_COLUMNS}
    output.update({
        "input_row": row_number,
        "control_orbit_key_json": "", "control_duplicate_orbit": "",
        "control_W": "", "control_positive_overlap_terms": "",
        "control_source_status": "", "edge_candidate_orbit_key_json": "",
        "edge_candidate_duplicate_orbit": "", "edge_candidate_W": "",
        "edge_candidate_positive_overlap_terms": "",
        "edge_candidate_source_status": "", "row_status": "INVALID_WITNESS_STOP",
        "failure_reason": reason,
    })
    return output


def _output_row(row: Mapping[str, str], row_number: int,
                verified: Mapping[str, Any], control: Mapping[str, Any],
                candidate: Mapping[str, Any]) -> dict[str, Any]:
    output = {name: row.get(name, "") for name in census.CYCLE_COLUMNS}
    output.update({
        "input_row": row_number,
        "control_orbit_key_json": json.dumps(control["orbit"],
                                               separators=(",", ":"))
        if control["orbit"] is not None else "",
        "control_duplicate_orbit": control["duplicate"],
        "control_W": control["W"],
        "control_positive_overlap_terms": control["positive_terms"],
        "control_source_status": control["source_status"],
        "edge_candidate_orbit_key_json": json.dumps(
            candidate["orbit"], separators=(",", ":"))
        if candidate["orbit"] is not None else "",
        "edge_candidate_duplicate_orbit": candidate["duplicate"],
        "edge_candidate_W": candidate["W"],
        "edge_candidate_positive_overlap_terms": candidate["positive_terms"],
        "edge_candidate_source_status": candidate["source_status"],
        "row_status": "OK", "failure_reason": "",
    })
    return output


def _record_row(summary: dict[str, Any], verified: Mapping[str, Any],
                control: Mapping[str, Any], candidate: Mapping[str, Any]) -> None:
    seed = int(verified["graph_seed"])
    ell = int(verified["ell"])
    graph = summary["per_graph"][str(seed)]
    graph["status"] = "IN_PROGRESS"
    graph["cycle_rows_processed"] += 1
    cell = graph["by_ell"][str(ell)]
    cell["cycle_rows_processed"] += 1
    cell["cycle_rows"] = cell["cycle_rows_processed"]
    for name, arm in (("control", control), ("edge_candidate", candidate)):
        counts = cell[name]
        counts["cycle_rows"] += 1
        _add_arm_counts(counts, arm)
    if seed not in summary["attempted_graphs"]:
        summary["attempted_graphs"].append(seed)
    _set_graph_complete(summary, seed)


def _prepare_expected(summary: dict[str, Any], predecessor: Mapping[str, Any]) -> None:
    expected = _expected_counts(predecessor)
    for seed in GRAPH_SEEDS:
        summary["per_graph"][str(seed)] = _new_graph_summary(seed, expected[seed])
    summary["reference_rows_expected"] = int(predecessor["expected_rows"])
    for seed in GRAPH_SEEDS:
        if summary["per_graph"][str(seed)]["cycle_rows_expected"] == 0:
            _set_graph_complete(summary, seed)


def execute_batch(*, out_root: str | Path,
                  repo_root: str | Path | None = None,
                  reference_root: str | Path | None = None,
                  command: str = COMMAND,
                  now: Callable[[], float] = time.perf_counter,
                  rss_fn: Callable[[], int | None] = _rss_bytes
                  ) -> dict[str, Any]:
    """Stream a completed census and append source overlaps; no graph/decoder."""
    root = validate_out_root(out_root, repo_root=repo_root)
    repository = Path(repo_root).resolve() if repo_root is not None else _repo_root()
    reference = (Path(reference_root).resolve() if reference_root is not None
                 else repository / REFERENCE_ROOT_RELATIVE)
    started = float(now())
    root.mkdir(parents=True)
    manifest: dict[str, Any] = {
        "contract": CONTRACT, "batch_uuid": BATCH_UUID, "track": "EXPLORE",
        "status": "RUNNING", "exact_command": command,
        "input_root": str(reference), "input_batch_uuid": REFERENCE_BATCH_UUID,
        "input_artifacts": ["manifest.json", "summary.json", "cycles.csv"],
        "graph_seeds": list(GRAPH_SEEDS), "ell_range": [MIN_ELL, MAX_ELL],
        "pmf": None, "bhattacharyya_B": None,
        "budgets": {"total_wall_s": WALL_CAP_S,
                    "rss_bytes": RSS_CAP_BYTES,
                    "max_input_cycle_rows": MAX_CYCLE_ROWS,
                    "resource_check_every_rows": RESOURCE_CHECK_ROWS},
        "input_rows_expected": None, "input_rows_attempted": 0,
        "input_rows_processed": 0, "decoder_calls": 0,
        "graph_constructions": 0, "sampled_frames": 0,
        "resource_observations": {
            "check_count": 0, "last_elapsed_s": None,
            "last_sampled_rss_bytes": None,
            "max_sampled_rss_bytes": None,
            "terminal_sampled": False,
            "terminal_sample_stop_reason": None,
            "rss_sample_kind": "process high-water RSS at resource checkpoints",
        },
        "truth_prior_arrays_saved": False, "stop_reason": "",
    }
    summary = _empty_summary()
    manifest_path = root / "manifest.json"
    summary_path = root / "summary.json"
    csv_path = root / "source_overlap.csv"
    log_path = root / "EXPLORATION_LOG.md"
    with csv_path.open("w", newline="", encoding="utf-8") as csv_handle:
        writer = csv.DictWriter(csv_handle, fieldnames=SOURCE_COLUMNS)
        writer.writeheader()
        _json_write(manifest_path, manifest)
        _json_write(summary_path, summary)
        _append_log(log_path, "EXPLORE batch %s started; decoder_calls=0" % BATCH_UUID)

        def persist(status: str, reason: str = "") -> dict[str, Any]:
            if status not in ("RESOURCE_STOP", "OVERLAP_COMPLETE"):
                terminal_reason = resource_status()
                observations = summary["resource_observations"]
                observations["terminal_sampled"] = True
                observations["terminal_sample_stop_reason"] = terminal_reason
                manifest["resource_observations"] = observations
            elapsed = max(float(now()) - started, 0.0)
            summary["terminal_status"] = status
            summary["stop_reason"] = reason
            summary["batch_wall_s"] = elapsed
            summary["resource_observations"]["final_elapsed_s"] = elapsed
            manifest["status"] = status
            manifest["stop_reason"] = reason
            manifest["batch_wall_s"] = elapsed
            manifest["resource_observations"] = summary["resource_observations"]
            manifest["input_rows_attempted"] = summary["input_rows_attempted"]
            manifest["input_rows_processed"] = summary["input_rows_processed"]
            csv_handle.flush()
            _json_write(manifest_path, manifest)
            _json_write(summary_path, summary)
            _append_log(log_path,
                        "terminal=%s stop_reason=%s rows=%d completed_graphs=%d"
                        % (status, reason or "none", summary["input_rows_processed"],
                           len(summary["completed_graphs"])))
            return summary

        def resource_status() -> str:
            observations = summary["resource_observations"]
            observations["check_count"] += 1
            elapsed: float | None = None
            rss: int | None = None
            failures: list[str] = []
            try:
                elapsed = max(float(now()) - started, 0.0)
                observations["last_elapsed_s"] = elapsed
            except Exception as exc:
                failures.append("clock:%s:%s" % (type(exc).__name__, str(exc)))
            try:
                sampled = rss_fn()
                rss = None if sampled is None else int(sampled)
                observations["last_sampled_rss_bytes"] = rss
                if rss is not None:
                    current_max = observations["max_sampled_rss_bytes"]
                    observations["max_sampled_rss_bytes"] = (
                        rss if current_max is None else max(int(current_max), rss))
            except Exception as exc:
                failures.append("rss:%s:%s" % (type(exc).__name__, str(exc)))
            manifest["resource_observations"] = observations
            if failures:
                return "resource_check_exception:" + ";".join(failures)
            exceeded: list[str] = []
            if elapsed is not None and elapsed > WALL_CAP_S:
                exceeded.append("total_wall_cap")
            if rss is not None and rss >= RSS_CAP_BYTES:
                exceeded.append("rss_cap")
            return "+".join(exceeded)

        try:
            reason = resource_status()
            if reason:
                return persist("RESOURCE_STOP", reason)
            try:
                predecessor = load_predecessor(reference)
            except FileNotFoundError as exc:
                return persist("PREDECESSOR_MISSING_STOP", str(exc))
            except PredecessorError as exc:
                return persist("PREDECESSOR_INCOMPLETE_STOP", str(exc))
            except Exception as exc:
                return persist("PREDECESSOR_INVALID_STOP",
                               "%s:%s" % (type(exc).__name__, str(exc)))

            _prepare_expected(summary, predecessor)
            manifest["input_rows_expected"] = predecessor["expected_rows"]
            summary["reference_rows_expected"] = predecessor["expected_rows"]
            if predecessor["expected_rows"] > MAX_CYCLE_ROWS:
                return persist("ROW_CAP_STOP", "predecessor exceeds 600000 rows")
            pmf = source_pmf()
            b_values = bhattacharyya_values(pmf)
            manifest["pmf"] = pmf.tolist()
            manifest["bhattacharyya_B"] = b_values.tolist()
            manifest["mathematical_units"] = (
                "dimensionless sum of 31 pairwise Bhattacharyya overlaps; "
                "not error probability or FER")
            _json_write(manifest_path, manifest)
            _append_log(log_path, "validated complete census metadata; streamed cycles.csv")
            reason = resource_status()
            if reason:
                return persist("RESOURCE_STOP", reason)

            seen: dict[int, dict[str, set[tuple[tuple[int, int], ...]]]] = {
                seed: {"control": set(), "edge_candidate": set()}
                for seed in GRAPH_SEEDS
            }
            rows_read = 0
            expected_by_graph_ell = _expected_counts(predecessor)
            with (reference / "cycles.csv").open(
                    "r", newline="", encoding="utf-8") as input_handle:
                reader = csv.DictReader(input_handle)
                if reader.fieldnames != list(census.CYCLE_COLUMNS):
                    return persist("PREDECESSOR_SCHEMA_STOP",
                                   "cycles.csv columns differ from frozen census schema")
                for raw in reader:
                    rows_read += 1
                    summary["input_rows_attempted"] = rows_read
                    manifest["input_rows_attempted"] = rows_read
                    if rows_read > MAX_CYCLE_ROWS:
                        return persist("ROW_CAP_STOP", "input exceeded 600000 rows")
                    try:
                        verified = verify_cycle_row(raw)
                        seed = int(verified["graph_seed"])
                        ell = int(verified["ell"])
                        if summary["per_graph"][str(seed)]["by_ell"][str(ell)][
                                "cycle_rows_processed"] >= expected_by_graph_ell[seed][ell]:
                            raise ValueError("input has more rows than census per-ell count")
                        control = _measure_arm(
                            verified["control"], b_values, seen[seed]["control"])
                        candidate = _measure_arm(
                            verified["edge_candidate"], b_values,
                            seen[seed]["edge_candidate"])
                    except Exception as exc:
                        writer.writerow(_invalid_output_row(
                            raw, rows_read,
                            "%s:%s" % (type(exc).__name__, str(exc))))
                        csv_handle.flush()
                        summary["input_rows_attempted"] = rows_read
                        manifest["input_rows_attempted"] = rows_read
                        _append_log(log_path,
                                    "invalid_input_row=%d error=%s:%s"
                                    % (rows_read, type(exc).__name__, str(exc)))
                        return persist("INVALID_WITNESS_STOP",
                                       "%s:%s" % (type(exc).__name__, str(exc)))

                    writer.writerow(_output_row(raw, rows_read, verified,
                                                control, candidate))
                    _record_row(summary, verified, control, candidate)
                    summary["input_rows_processed"] += 1
                    manifest["input_rows_processed"] = summary["input_rows_processed"]
                    if rows_read % RESOURCE_CHECK_ROWS == 0:
                        csv_handle.flush()
                        _json_write(summary_path, summary)
                        reason = resource_status()
                        if reason:
                            return persist("RESOURCE_STOP", reason)

            if rows_read != predecessor["expected_rows"]:
                return persist(
                    "PREDECESSOR_ROW_COUNT_STOP",
                    "cycles.csv rows=%d expected=%d"
                    % (rows_read, predecessor["expected_rows"]))
            for seed in GRAPH_SEEDS:
                expected = expected_by_graph_ell[seed]
                actual = summary["per_graph"][str(seed)]["by_ell"]
                if any(actual[str(ell)]["cycle_rows_processed"] != expected[ell]
                       for ell in range(MIN_ELL, MAX_ELL + 1)):
                    return persist("PREDECESSOR_ROW_COUNT_STOP",
                                   "per-graph/per-ell cycle rows differ from census summary")
                _set_graph_complete(summary, seed)
            if len(summary["completed_graphs"]) != len(GRAPH_SEEDS):
                return persist("PREDECESSOR_ROW_COUNT_STOP",
                               "not all six census graphs were fully processed")
            reason = resource_status()
            if reason:
                return persist("RESOURCE_STOP", reason)
            _finalize_summary(summary)
            summary["batch_complete"] = True
            manifest["batch_complete"] = True
            return persist("OVERLAP_COMPLETE", "")
        except Exception as exc:
            _append_log(log_path, "implementation_exception=%s:%s"
                        % (type(exc).__name__, str(exc)))
            return persist("IMPLEMENTATION_STOP",
                           "%s:%s" % (type(exc).__name__, str(exc)))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Decoder-free source overlap on accepted GF(32) short cycles")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--execute", action="store_true",
                      help="stream an accepted complete census and compute overlaps")
    mode.add_argument("--dry-run", action="store_true",
                      help="validate only the fresh output root")
    parser.add_argument("--out-root", default=str(OUT_ROOT_RELATIVE),
                        help="must equal the frozen fresh output root")
    return parser


def main(argv: list[str] | None = None) -> dict[str, Any]:
    args = build_parser().parse_args(argv)
    root = validate_out_root(args.out_root)
    if not args.execute:
        result = dry_run(root)
    else:
        result = execute_batch(
            out_root=root, reference_root=_repo_root() / REFERENCE_ROOT_RELATIVE,
            repo_root=_repo_root(), command=COMMAND)
    print(json.dumps(_plain(result), indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
