# Proposal — NB-LDPC L1 degree-2 layout Stage-1 (design + minimal implementation)

- Change: `add-nbldpc-l1-degree2-layout`
- Cycle: `NBLDPC-PARALLEL-STRUCTURED-RECOVERY-DRAFT` R1 (Stage-1 only)
- Track: **implementation-only** (no track gate; zero scientific decoder calls,
  zero benchmark/sweep/replay, zero real-data contact, no commit/push).
- Authority (read first, frozen):
  `docs/research_cycles/NBLDPC-PARALLEL-STRUCTURED-RECOVERY-DRAFT/PROPOSAL.md`
  (§3–§6), `PROMPT.md`, `AGENTS.md` §0/§1.2/§5/§10,
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d10_mixed_degree_l1.py`
  (`build_degree_sequence_peg`, A1–A6, coefficient stream),
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d12_finite_l1_degree.py`
  (`degree_cell`, L055 cells),
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d11_forward_app.py` +
  `v72p2d5_gf32_rate_mother.py::_run_layered_block`
  (`(decode_fn,h1,h2,p1,p2,block,oracle,…)` protocol, CHECK_UPDATED forward
  semantics).
- Branch: `formal-ir-v72p1-addendum-clean` (ordinary non-force push only;
  never merge `polar-mainline`; Polar baseline frozen; Joint MARGINAL, P3/P4,
  D7-H retained).

## Goal

Implement exactly one frozen scientific delta — a degree-2-directed L1
connection layout for the frozen L055 degree sequence — as a minimal additive
Stage-1 package: one constructor module, one thin driver, fake-only T0/T1
tests, and PROFILE_ONLY structural records. No decoder is called scientifically
in Stage-1; no data is produced.

## Non-Goals (hard prohibitions)

- No scientific decoder/benchmark/sweep/replay execution in Stage-1
  (forbidden flags: `--batch`, `--execute*`, `--forward-batch`).
- No change to `src/`, `experiments/`, `tools/`, any existing `formal_ir/*`
  module, old frozen packets, `AGENTS.md`, memory, decision-log, or the
  sibling checkout (read-only import of existing functions only).
- No writes to `results/` or `comparison_bench/outputs_comparison/`
  (tests use fresh `workspace/<task>/<uuid>` roots, never the production roots;
  no `.ttbin`/real input contact; no production decoder binding).
- No new admission predicates, no degree/rate/budget/L2/schedule/prior change,
  no reverse U2→U1, no D7-H, no post-hoc choice of the most favorable
  structural metric.

## Impact scope

- ADDED (exact file manifest; S101–S108 map in `tasks.md`):
  `openspec/changes/add-nbldpc-l1-degree2-layout/` (`proposal.md`,
  `design.md`, `tasks.md`, `specs/degree2-layout/spec.md`);
  `comparison_bench/src/comparison_bench/formal_ir/nbldpc_l1_degree2_layout.py`;
  `comparison_bench/src/comparison_bench/cli/nbldpc_l1_degree2_driver.py`;
  `comparison_bench/tests/test_nbldpc_l1_degree2_layout.py`,
  `comparison_bench/tests/test_nbldpc_l1_degree2_driver.py`.
- READ-ONLY: modules listed under Authority above.
- FORBIDDEN: everything listed under Non-Goals.
