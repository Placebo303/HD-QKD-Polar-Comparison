"""In-memory M3-a nested GF(32) construction probe.

The CLI is deliberately dual-gated and selects exactly one frozen arm per
invocation. Unit tests inject a fake base constructor through :func:`construct`
and never enter the production PEG path.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from numbers import Integral
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir import (
    nonbinary_v10_peg as peg,
)
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import (
    GF2mField,
)


N = 1024
M_BASE = 200
N_NEW_ROWS = 8
NEW_ROW_DEGREE = 10
FIELD_Q = 32
BASE_TRIALS = 20
SEED_PAIRS = (
    (2026092001, 2026096801),
    (2026092011, 2026096811),
)


class ConstructionFailure(ValueError):
    """A frozen M3-a construction pin failed; no retry or tuning is allowed."""


def frozen_seed_pair(arm: int) -> tuple[int, int]:
    """Return the packet-frozen (base, extension) seeds for arm 1 or 2."""
    if isinstance(arm, bool) or not isinstance(arm, Integral) or int(arm) not in (1, 2):
        raise ConstructionFailure("arm must be 1 or 2")
    return SEED_PAIRS[int(arm) - 1]


def _positive_int(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral) or int(value) < 1:
        raise ConstructionFailure(f"{name} must be a positive integer")
    return int(value)


def _normalize_triples(triples: Sequence[Sequence[int]], n: int, m: int,
                       field: GF2mField) -> list[tuple[int, int, int]]:
    normalized: list[tuple[int, int, int]] = []
    seen: set[tuple[int, int]] = set()
    for item in triples:
        if len(item) != 3:
            raise ConstructionFailure("each triple must be (row, variable, label)")
        row, variable, label = (int(x) for x in item)
        if not 0 <= row < m or not 0 <= variable < n:
            raise ConstructionFailure("base triple is outside its matrix shape")
        field.mul(1, label)
        if label == 0:
            raise ConstructionFailure("edge labels must be nonzero")
        pair = (row, variable)
        if pair in seen:
            raise ConstructionFailure("base contains a duplicate (row, variable)")
        seen.add(pair)
        normalized.append((row, variable, label))
    return normalized


def _variable_degree_histogram(triples: Sequence[Sequence[int]], n: int
                               ) -> dict[int, int]:
    degrees = [0] * n
    for _, variable, _ in triples:
        degrees[int(variable)] += 1
    return dict(sorted(Counter(degrees).items()))


def _four_cycles(triples: Sequence[Sequence[int]]) -> int:
    return int(peg._count_four_cycles_var_check(
        [(int(variable), int(row)) for row, variable, _ in triples]))


def append_rows(base_code: Mapping[str, Any], *, seed: int,
                n_rows: int = N_NEW_ROWS,
                row_degree: int = NEW_ROW_DEGREE,
                field: GF2mField | None = None) -> dict[str, Any]:
    """Append fixed-degree checks, preserving every base triple and label.

    Variables are globally unique across appended rows. Within each new row,
    selected variables must have disjoint existing check-neighbor sets, which
    prevents adding a four-cycle. The seeded RNG selects all rows first, then
    supplies their nonzero GF(32) labels.
    """
    field = field or GF2mField.create(FIELD_Q)
    if field.q != FIELD_Q:
        raise ConstructionFailure(f"M3-a requires GF({FIELD_Q}) labels")
    n = _positive_int(base_code.get("n"), "n")
    m_base = _positive_int(base_code.get("m"), "base m")
    n_rows = _positive_int(n_rows, "n_rows")
    row_degree = _positive_int(row_degree, "row_degree")
    if isinstance(seed, bool) or not isinstance(seed, Integral):
        raise ConstructionFailure("extension seed must be an integer")
    if n_rows * row_degree > n:
        raise ConstructionFailure("extension needs more globally unique variables than n")
    if base_code.get("status", "ok") != "ok":
        raise ConstructionFailure("base constructor status is not ok")

    base_raw = list(base_code.get("triples", ()))
    base = _normalize_triples(base_raw, n, m_base, field)
    var_checks = {v: set() for v in range(n)}
    var_adj: dict[int, list[int]] = {v: [] for v in range(n)}
    check_adj: dict[int, list[int]] = {n + row: [] for row in range(m_base)}
    for row, variable, _ in base:
        check_node = n + row
        var_checks[variable].add(row)
        var_adj[variable].append(check_node)
        check_adj[check_node].append(variable)

    rng = np.random.default_rng(int(seed))
    used_variables: set[int] = set()
    selected_rows: list[list[int]] = []
    for offset in range(n_rows):
        selected: list[int] = []
        occupied_checks: set[int] = set()
        for candidate in rng.permutation(n):
            variable = int(candidate)
            neighbors = var_checks[variable]
            if variable in used_variables or occupied_checks.intersection(neighbors):
                continue
            selected.append(variable)
            used_variables.add(variable)
            occupied_checks.update(neighbors)
            if len(selected) == row_degree:
                break
        if len(selected) != row_degree:
            raise ConstructionFailure(
                f"row {m_base + offset} has {len(selected)}/{row_degree} "
                "admissible variables; frozen arm failed without retuning")
        selected_rows.append(selected)
        row = m_base + offset
        check_node = n + row
        check_adj[check_node] = []
        for variable in selected:
            var_checks[variable].add(row)
            var_adj[variable].append(check_node)
            check_adj[check_node].append(variable)

    # Label draws use the same RNG only after all row selections are fixed.
    labels = rng.integers(1, field.q, size=n_rows * row_degree)
    added: list[tuple[int, int, int]] = []
    label_idx = 0
    min_girth = base_code.get("min_girth")
    if isinstance(min_girth, bool) or not isinstance(min_girth, Integral):
        min_girth = None
    else:
        min_girth = int(min_girth)

    # Compute cycles created by new edges by measuring their pre-insertion
    # Tanner distance. Adjacency was populated above, so rebuild it in row
    # order for this incremental girth measurement.
    var_adj = {v: [] for v in range(n)}
    check_adj = {n + row: [] for row in range(m_base + n_rows)}
    for row, variable, _ in base:
        check_node = n + row
        var_adj[variable].append(check_node)
        check_adj[check_node].append(variable)
    for offset, selected in enumerate(selected_rows):
        row = m_base + offset
        check_node = n + row
        for variable in selected:
            distance = peg._bfs_distance(variable, check_node, n,
                                         var_adj, check_adj)
            if distance > 0:
                cycle_girth = distance + 1
                min_girth = (cycle_girth if min_girth is None
                             else min(min_girth, cycle_girth))
            var_adj[variable].append(check_node)
            check_adj[check_node].append(variable)
            added.append((row, variable, int(labels[label_idx])))
            label_idx += 1

    full_raw = base_raw + added
    base_rank = int(peg.rank_GF1024(
        field, peg.sparse_to_dense(base, n, m_base, field).tolist()))
    m_full = m_base + n_rows
    full_normalized = base + added
    full_rank = int(peg.rank_GF1024(
        field, peg.sparse_to_dense(full_normalized, n, m_full, field).tolist()))
    row_degrees = [0] * n_rows
    for row, _, _ in added:
        row_degrees[row - m_base] += 1
    return {
        "status": "ok",
        "n": n,
        "m_base": m_base,
        "m": m_full,
        "base_triples": base_raw,
        "added_triples": added,
        "triples": full_raw,
        "base_prefix_unchanged": full_raw[:len(base_raw)] == base_raw,
        "base_variable_degree_histogram": _variable_degree_histogram(base, n),
        "variable_degree_histogram": _variable_degree_histogram(full_normalized, n),
        "added_row_degrees": row_degrees,
        "base_rank": base_rank,
        "rank": full_rank,
        "base_four_cycles": _four_cycles(base),
        "four_cycles": _four_cycles(full_normalized),
        "min_girth": min_girth,
        "extension_seed": int(seed),
    }


def construct(*, base_fn: Callable[[int, int, int], Mapping[str, Any]],
              base_seed: int, extension_seed: int,
              n: int = N, m_base: int = M_BASE,
              n_rows: int = N_NEW_ROWS,
              row_degree: int = NEW_ROW_DEGREE,
              q: int = FIELD_Q, trials: int = BASE_TRIALS) -> dict[str, Any]:
    """Build and pin one nested code using an explicitly injected base builder."""
    if not callable(base_fn):
        raise ConstructionFailure("base_fn must be explicitly injected")
    for name, value in (("n", n), ("m_base", m_base), ("n_rows", n_rows),
                        ("row_degree", row_degree), ("q", q), ("trials", trials)):
        _positive_int(value, name)
    if q != FIELD_Q:
        raise ConstructionFailure(f"M3-a requires GF({FIELD_Q})")
    field = GF2mField.create(q)
    first = base_fn(int(m_base), int(base_seed), int(trials))
    second = base_fn(int(m_base), int(base_seed), int(trials))
    first_base = list(first.get("triples", ()))
    second_base = list(second.get("triples", ()))
    if first_base != second_base:
        raise ConstructionFailure("twice-built base triples differ")
    for code in (first, second):
        if code.get("status", "ok") != "ok":
            raise ConstructionFailure("base constructor status is not ok")
        if int(code.get("n", -1)) != int(n) or int(code.get("m", -1)) != int(m_base):
            raise ConstructionFailure("base constructor shape differs from frozen pins")

    extension_a = append_rows(first, seed=extension_seed, n_rows=n_rows,
                              row_degree=row_degree, field=field)
    extension_b = append_rows(second, seed=extension_seed, n_rows=n_rows,
                              row_degree=row_degree, field=field)
    if extension_a["triples"] != extension_b["triples"]:
        raise ConstructionFailure("twice-built nested triples differ")

    expected_base_hist = {2: int(n)}
    if extension_a["base_variable_degree_histogram"] != expected_base_hist:
        raise ConstructionFailure("base variables are not all degree 2")
    if extension_a["base_rank"] != int(m_base):
        raise ConstructionFailure(f"base rank {extension_a['base_rank']} != {m_base}")
    if extension_a["base_four_cycles"] != 0:
        raise ConstructionFailure("base four_cycles must be zero")
    if extension_a["added_row_degrees"] != [int(row_degree)] * int(n_rows):
        raise ConstructionFailure("appended check-row degree pin failed")
    if not extension_a["base_prefix_unchanged"]:
        raise ConstructionFailure("base prefix or labels changed during extension")
    if extension_a["rank"] != int(m_base) + int(n_rows):
        raise ConstructionFailure(
            f"full rank {extension_a['rank']} != {int(m_base) + int(n_rows)}")
    if extension_a["four_cycles"] != 0:
        raise ConstructionFailure("full four_cycles must be zero")
    if any(not 1 <= int(edge[2]) < field.q for edge in extension_a["added_triples"]):
        raise ConstructionFailure("appended label is outside GF(32) nonzero range")
    extension_a.update({
        "base_seed": int(base_seed),
        "base_trials": int(trials),
        "twice_identical": True,
    })
    return extension_a


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="M3-a nested GF(32) construction; structural pins only.")
    parser.add_argument("--arm", type=int, choices=(1, 2),
                        help="run exactly one frozen arm (required for execution)")
    parser.add_argument("--execute-construction", action="store_true",
                        help="run the selected frozen construction arm")
    parser.add_argument("--execution-authorized", action="store_true",
                        help="acknowledge the packet Pre-EXECUTE grant")
    args = parser.parse_args(argv)
    if not args.execute_construction and not args.execution_authorized:
        print(json.dumps({
            "status": "dry",
            "arms": [
                {"arm": index, "base_seed": pair[0],
                 "extension_seed": pair[1]}
                for index, pair in enumerate(SEED_PAIRS, start=1)
            ],
            "selected_arm": args.arm,
            "seed_pairs": [list(pair) for pair in SEED_PAIRS],
            "n": N, "q": FIELD_Q, "m_base": M_BASE,
            "new_rows": N_NEW_ROWS, "new_row_degree": NEW_ROW_DEGREE,
            "required_flags": ["--execute-construction",
                               "--execution-authorized"],
        }, sort_keys=True))
        return 0
    if not args.execute_construction or not args.execution_authorized:
        print("both --execute-construction and --execution-authorized are required",
              file=sys.stderr)
        return 2
    if args.arm is None:
        print("--arm 1 or --arm 2 is required for execution", file=sys.stderr)
        return 2

    # Production constructor import is reachable only behind both CLI flags.
    from comparison_bench.src.comparison_bench.cli.x1_arm_runner import (
        construct_standalone,
    )

    base_seed, extension_seed = frozen_seed_pair(args.arm)
    try:
        result = construct(base_fn=construct_standalone,
                           base_seed=base_seed,
                           extension_seed=extension_seed)
    except Exception as exc:  # retain this arm's terminal failure as its JSON
        result = {
            "status": "failed",
            "arm": args.arm,
            "base_seed": base_seed,
            "extension_seed": extension_seed,
            "failure": f"{type(exc).__name__}: {exc}",
        }
    result["arm"] = args.arm
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("status") == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
