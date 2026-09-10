# Tasks — V72P2D6 R1d Option C (eligible-only successor)

- [x] D1 Freeze: this OpenSpec (proposal/design/tasks/spec) +
  `D6_GRAPH_MOTHER_OPTION_C_ACCEPTANCE_R1.md` (ruling, A/B rejection, 26-cell
  proof) + `D6_GRAPH_MOTHER_R1D_EXECUTION_PACKET_R1.md` (schedule, budgets,
  command, stop rules, gates) + decision-log + memory appends +
  `cycle_state.yaml` `next_gate` only (all auth false). Commit separately
  (commit 1). No code before commit 1. No authorization change.
- [ ] D2 Implement R1d dispatch layer (mother module, additive only):
  `R1D_ARMS`, `R1D_SCALING_FALLBACKS`, `R1D_STRUCTURE_SCHEMA`,
  `R1D_ELIGIBLE_SEMANTICS`, `R1D_VALID_SUBSET` (26 cells),
  `assert_r1d_arm`, `assert_r1d_dispatchable`, `enrich_r1d_records`,
  `write/append_structure_records_r1d`. A4/A6 builder path untouched.
- [ ] D3 Implement `--r1d` runner mode (dev script, default off): R1D arms at
  every build, selection/fallback asserts (`{B0,B1,T1}`, `fallback_M=None`),
  T1-only scaling, per-cell R1d guard in `run_cell` gated on `state["r1d"]`,
  schema-v2 evidence + markers, named A2/VOID-root refusal, r1d-aware
  `--verify` (v2 columns + value agreement, zero skip on marked roots;
  old roots unchanged).
- [ ] D4 Focused tests (new file, fake-only, fresh task-owned basetemps):
  exact arm set; SC/M/T2 non-dispatch; T1-only fallback + B0/B1 control
  semantics; all 26 schedule cells eligible (live rebuild); one invalid cell
  fails pre-decoder-binding (`_NoCall`, zero calls); schema-v2 present +
  recomputable; old A2 schema readable + immutable; crash/nonfinite override;
  no A2/VOID/formal reuse; seq==par determinism; fake e2e produces + verifies
  exact new schema with zero production decoder calls.
- [ ] D5 `py_compile` + focused D6 + seven-file non-perf suite
  (`pytest -p no:cacheprovider`, `workspace/<task>/<uuid>/` basetemps).
  Perf-v38 only if a scoped dep changed (record choice).
- [ ] D6 Read-only independent implementation review (own file only; max one
  scoped rework) + fresh independent Pre-EXECUTE review (8 checks);
  verdict `D6_R1D_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`
  (grants no authorization).
- [ ] D7 Scoped local commits: (1) freeze [this task]; (2) implementation +
  tests; (3) reviews; (4) append-only closeout if needed. No push. No R1d
  output root. No real decoder. End: all auth keys false, gate awaiting
  explicit R1d authorization.
