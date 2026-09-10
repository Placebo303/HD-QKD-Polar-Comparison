# Proposal — V72P2D6 GF32 graph/mother R1d Option C (eligible-only successor)

Change: `v72p2d6-gf32-graph-mother-r1d-option-c`
Parent change: `v72p2d6-gf32-graph-mother-successor` (frozen science, R1c-A5/A6 closed)
Packet: `.workbuddy/tasks/D6_R1D_OPTION_C_FREEZE_AND_PREEXEC_TASK_PACKET.md` (sole authority)
Ruling: main-thread Option C (no SC/M knob lift; SC/accumulator structurally
inadmissible as frozen; no R1c-A2 decoder call/root reuse as successor evidence)

## 1. What

The smallest execution-ready R1d candidate under the unchanged E2 prior,
decoder, rows, seeds, schedule, and thresholds: dispatch exactly
`{B0_D5_DV3_NATIVE, B1_D5_DV3_COMMON_LABELS, T1_PEG_DV3}` (B0/B1 controls that
cannot win advancement, T1 the sole new arm), guarded by the accepted A5
validity matrix (frozen eligibility AND I1) with fail-closed pre-dispatch
refusal, T1-only scaling fallback, fresh UUID root with evidence schema
`r1d-v2` (`row_degree_min`, `rows_below_degree_2`, eligible-semantics/schema
version marker; historical A2 files immutable, old schema), crash/nonfinite/
invariant precedence (A3/A5), and stored-vs-recomputed terminal agreement.
A distinct `--r1d` runner mode cannot overwrite or ingest A2 roots and leaves
no SC/M/T2 branch reachable from R1d config.

## 2. Why

R1c-A5 closed validity (`STRUCTURALLY_INFEASIBLE_AS_FROZEN`, 0/10 repair rules
admissible) with a 3-option menu; the main thread ruled Option C. R1d asks only:
under the unchanged contract, does the structurally valid T1 PEG mother improve
over B0/B1 controls without invariant failures? SC/accumulator/T2 repair is
explicitly out of scope (rejected A/B reasons in the acceptance doc).

## 3. Scope (frozen)

- New R1d constants + dispatch guard + schema-v2 writer in
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d6_gf32_graph_mother.py`
  (additive only; A4/A6 builder path byte-identical outputs).
- `--r1d` mode in `scripts/v72p2d6_graph_mother_development.py` (R1D arms at
  every build, T1-only scaling fallback assert, schema-v2 evidence + marker,
  A2-root refusal, r1d-aware `--verify` with zero skip groups on new roots).
- New focused test file (fake-only, task-owned basetemps; 12 properties).
- Cycle docs: `D6_GRAPH_MOTHER_OPTION_C_ACCEPTANCE_R1.md`,
  `D6_GRAPH_MOTHER_R1D_EXECUTION_PACKET_R1.md`; decision-log + memory appends;
  `cycle_state.yaml` `next_gate` only (all auth keys false, no authorization).
- 26 role-cells over 22 distinct structure cells proven ⊆ A5 valid subset before
  implementation (acceptance doc table; any invalid cell would have been STOP,
  none found).

## 4. Non-goals (hard prohibitions)

No real decoder call; no `--phase`; no G1/G2/VAL/real/raw; no A2/VOID/formal
root reuse or reads as R1d scientific input; no historical-root touch; no
tuning; no A/B repair launch; no SC/M/T2 dispatch from R1d config; no
authorization grant (reviews grant none); no R1d output-root creation now;
no push/force/reset/checkout/stash/clean/amend/rebase/EOL-normalize/`git add -A`.
