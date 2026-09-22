# Review Verdict: V37-P0 / P0R1 Finite-Length Degree Feasibility Analyzer

**Repository**: `Placebo303/HD-QKD-Polar-pipeline`
**Branch**: `formal-ir-mainline`
**Reviewed SHA**: `a258c5a7549f33f43a32b193b134f1ca0df15aea`
**Parent SHA**: `dad06e7fe7784245923c0e2d10766e450afb7175`
**SHA Verification**: VERIFIED
**Cycle ID**: V37P0
**Review Kind**: IMPLEMENTATION
**Advisory Verdict**: ADVISORY_ACCEPT

---

## 1. Summary of Accepted Implementation

- **Tooling Scope**: Read-only scientific analyzer module [`comparison_bench/src/comparison_bench/formal_ir/v37_degree_feasibility.py`](file:///D:/Code/HD-QKD_Polar_Comparison/comparison_bench/src/comparison_bench/formal_ir/v37_degree_feasibility.py) and CLI runner [`comparison_bench/src/comparison_bench/cli/run_v37_degree_feasibility.py`](file:///D:/Code/HD-QKD_Polar_Comparison/comparison_bench/src/comparison_bench/cli/run_v37_degree_feasibility.py).
- **Core Functionality**:
  - Mechanical edge-to-node conversion: $L_i = (\lambda_i / i) / \sum_j (\lambda_j / j)$, $\bar{d}_v = 1 / \sum_j (\lambda_j / j)$.
  - Exact integer node apportionment: $N_i$ summing to $n$ via largest-remainder (Hamilton) method.
  - Sockets and check allocation: $E = \sum_i i \cdot N_i$, $\bar{d}_c = E / m$, exact integer floor/ceil check counts $n_{\text{checks\_ceil}} = E \pmod m$, $n_{\text{checks\_floor}} = m - n_{\text{checks\_ceil}}$.
  - Degree-2 forest bound and cycle-rank lower bound: $\text{forest\_bound} = m - 1$, $\gamma_2 \ge \max(0, N_2 - (m - 1))$.
- **R1–R3 Corrections Verified**:
  - R1: Multi-source forest verdict `structurally_cycle_free_degree2_possible` strictly requires all $m$ values (`all(N2 <= m - 1 for m in m_list)`). Tested via dedicated mixed-m unit test (`test_mixed_m_forest_feasibility_semantics`).
  - R2: Scientific wording narrowed: degree distribution forces cycle-rank lower bounds (758/752/750 for m=184/190/192), while observed ranks (801/785/779) exceed lower bounds by 43/33/29 without claiming causal decoder failure.
  - R3: Exact check degree allocation reported and feasibility field named `is_socket_allocation_feasible`.
- **Test Suite**: 11 unit tests passing (`comparison_bench/tests/test_v37_degree_feasibility.py`).

---

## 2. Claim Boundaries

- Tooling only; no algorithm improvement or decoder success is claimed.
- $N_2 \le m - 1$ is a necessary condition that removes the edge-count obstruction; it does not construct a graph or prove full Tanner graph realizability.
- Execution authorization for subsequent stages (V37-P1+) remains **NOT GRANTED**.
