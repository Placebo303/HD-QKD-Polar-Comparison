"""PEG sparse-code construction candidate (M1'b code-design branch).

Progressive edge growth: variables placed in nondecreasing... actually fixed
index order (deterministic, no RNG); each edge goes to a lowest-load check at
the greatest distance in the current graph (unreached check preferred),
which greedily maximizes local girth. Reports the number of edges that
closed a 4-cycle (distance-1 placements).
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import operator

import numpy as np
from scipy import sparse


@dataclass(frozen=True)
class PegConstruction:
    parity_check_matrix: sparse.csr_matrix
    four_cycle_edge_count: int
    max_check_degree: int


def _explicit_integer(value: object, name: str) -> int:
    if isinstance(value, (bool, np.bool_)):
        raise ValueError(f"{name} must be an integer, not bool")
    try:
        return operator.index(value)
    except TypeError as exc:
        raise ValueError(f"{name} must be an integer") from exc


def build_peg_code(
    *,
    n: int,
    m: int,
    variable_degree: int,
) -> PegConstruction:
    """Build a deterministic PEG ``(m x n)`` binary CSR parity-check matrix."""
    n = _explicit_integer(n, "n")
    m = _explicit_integer(m, "m")
    variable_degree = _explicit_integer(variable_degree, "variable_degree")
    if m < 1:
        raise ValueError("m must be at least 1")
    if n < 1:
        raise ValueError("n must be at least 1")
    if not 1 <= variable_degree <= m:
        raise ValueError("variable_degree must lie in [1, m]")

    var_nb: list[set[int]] = [set() for _ in range(n)]
    chk_nb: list[set[int]] = [set() for _ in range(m)]
    four_cycles = 0

    for v in range(n):
        for _ in range(variable_degree):
            # BFS from v through the current graph over check layers.
            dist: dict[int, int] = {}
            queue: deque[int] = deque()
            # distance measured in check layers from v:
            # neighbors of v at distance 0; their variable peers expand.
            for c in var_nb[v]:
                if c not in dist:
                    dist[c] = 0
                    queue.append(c)
            while queue:
                c = queue.popleft()
                for u in chk_nb[c]:
                    if u == v:
                        continue
                    for c2 in var_nb[u]:
                        if c2 not in dist:
                            dist[c2] = dist[c] + 1
                            queue.append(c2)
            unreached = [c for c in range(m) if c not in dist]
            if unreached:
                # lowest load, then lowest index (deterministic).
                best = min(unreached, key=lambda c: (len(chk_nb[c]), c))
            else:
                far = max(dist.values())
                cands = [c for c, d in dist.items() if d == far]
                best = min(cands, key=lambda c: (len(chk_nb[c]), c))
                if far <= 1:
                    four_cycles += 1
            var_nb[v].add(best)
            chk_nb[best].add(v)

    rows: list[int] = []
    cols: list[int] = []
    for v in range(n):
        for c in sorted(var_nb[v]):
            rows.append(c)
            cols.append(v)
    mat = sparse.coo_matrix(
        (np.ones(len(rows), dtype=np.uint8), (np.asarray(rows), np.asarray(cols))),
        shape=(m, n),
        dtype=np.uint8,
    ).tocsr()
    mat.sort_indices()
    return PegConstruction(
        parity_check_matrix=mat,
        four_cycle_edge_count=four_cycles,
        max_check_degree=max(int(len(s)) for s in chk_nb),
    )
