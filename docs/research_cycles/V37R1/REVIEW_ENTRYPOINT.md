# Review Entrypoint: V37R1 (V37-P1-PLAN Revision 1)

**Cycle ID**: V37R1
**Lifecycle State**: PLAN_CANDIDATE
**Review Kind**: PLAN
**Repository**: `Placebo303/HD-QKD-Polar-pipeline`
**Branch**: `formal-ir-mainline`
**Base / Parent SHA**: `a258c5a7549f33f43a32b193b134f1ca0df15aea` (V37-P0R1 accepted; provenance in `docs/research_cycles/V37P0/REVIEW_VERDICT.md`)
**Execution Authorization**: NOT_GRANTED

---

## Documents for Review

1. **Scientific Plan Document**:
   - `docs/nbldpc-v37-p1-plan.md`
2. **OpenSpec Candidate Change**:
   - `openspec/changes/formal-ir-v37-finite-feasible-empirical-p-de-screening/proposal.md`
   - `openspec/changes/formal-ir-v37-finite-feasible-empirical-p-de-screening/design.md`
   - `openspec/changes/formal-ir-v37-finite-feasible-empirical-p-de-screening/tasks.md`
   - `openspec/changes/formal-ir-v37-finite-feasible-empirical-p-de-screening/specs/formal-ir-v37/spec.md`
3. **P0 Acceptance Provenance**:
   - `docs/research_cycles/V37P0/cycle_state.yaml`
   - `docs/research_cycles/V37P0/REVIEW_VERDICT.md`
4. **P0 Feasibility Analyzer (Accepted Baseline)**:
   - `comparison_bench/src/comparison_bench/formal_ir/v37_degree_feasibility.py`
   - `docs/nbldpc-v37-p0-degree-feasibility.md`

---

## Core Review Items & Revision 1 Fixes

- [x] **Item 1**: Clarify that $N_2 \le 183$ (547 candidates, $\bar{d}_v \in [2.8571, 5.0000]$) does not imply $d_c \le 20$; explicitly distinguish P0 forest-count gate from additional design cap $d_{c,\max} \le 20$ (259 candidates).
- [x] **Item 2**: Scope $N_2 \le 183$ as a *necessary* forest-count feasibility condition, not a constructive proof of zero-cycle Tanner graph realizability.
- [x] **Item 3**: Define $\text{AUT}_{30}$ as lower cumulative early-iteration entropy (not pointwise strict inequality).
- [x] **Item 4**: Add disjoint confirmation seeds (P1-A screening with 3 seeds/source + P1-B confirmation on fresh seeds for candidate & baseline) to eliminate winner's curse / selection bias.
- [x] **Item 5**: Define $\ge 5\%$ reduction as a pre-registered practical development effect-size gate.
- [x] **Item 6**: Narrow negative terminal scope to the tested $\{2, 3, 4, 5\}$, $0.05$-simplex, $N_2 \le 183, d_{c,\max} \le 20$ candidate set.
- [x] **Item 7**: Record durable acceptance provenance for V37-P0 / P0R1 in `docs/research_cycles/V37P0/`.
- [x] **Item 8**: Ensure P1 remains strictly DE-only; execution authorization remains `NOT_GRANTED`.
