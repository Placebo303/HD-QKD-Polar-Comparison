# D7 root-cause and route-reset R1 — tasks

> Authority: `.workbuddy/tasks/D7_ROOT_CAUSE_AND_ROUTE_RESET_R1_TASK_PACKET.md`
> §7. Acceptance IDs are stable; completed tasks are checked only after the
> focused tests pass (T0/T1, fake decoders only). No execution phase X1–X4 is
> part of this change.

## Phase A — OpenSpec and evidence correction

- [x] **A01** Record the seven objectives and the claim ceiling in the
  proposal (`proposal.md` §What/§Claim ceiling).
- [x] **A02** Record that historical evidence is retained byte-identical and
  that corrections are additive/superseding (`proposal.md` §Evidence
  retention).
- [x] **A03** Add the cycle state whose initial terminal is
  `IMPLEMENTATION_IN_PROGRESS / EXECUTION_NOT_AUTHORIZED`
  (`docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/cycle_state.yaml`).
- [x] **A04** Add the D7-F corrigendum: `D7_F_REVERSE_ORDER_REGRESSION` stays
  a historical machine label, not an immutable general mechanism fact; the
  accepted interpretation is single-graph n=16 paired evidence with exact
  discordant counts and an exact-test p-value
  (`D7_F_CORRIGENDUM_R1.md`; decision-log entry).
- [x] **A05** Record G2 as pending, not failed, skipped, or superseded
  (`G2_STATUS_NOTE_R1.md`, `cycle_state.yaml`, proposal).

## Phase B — same-input G1/D7 equivalence and observability

- [x] **B01** Expose canonical `q_L1` and `P(U2|B)` helpers in the D5 module
  and delegate `_run_layered_block` to them without rewriting the decoder.
- [x] **B02** Add the deterministic same-input fixture asserting equality of
  L1 input prior, `q`, L2 transfer prior, target syndrome, decoded target,
  and per-layer counters between the legacy-G1-compatible and D7 paths.
- [x] **B03** Cover exact `CHECK_UPDATED`, missing, `None`, `PRIOR_ONLY`,
  unknown, and a valid zero-iteration prior-only return; every
  non-`CHECK_UPDATED` cross-layer consumption fails closed.
- [x] **B04** Localize the first unequal tensor/value and stop on a frozen
  comparison failure (no compensation, no tuning).
- [x] **B05** Extend the future G1 evidence schema additively with per-layer
  exact/syndrome/iterations/provenance and transfer-invoked/blocked counts;
  existing keys, filenames, and column order preserved.
- [x] **B06** Add the no-write decoder probe callable (historical resolution
  only when no fake is injected; no phase run, no output root, no writes).

## Phase C — frozen multi-graph exploratory design

- [x] **C01** Graph pairs `(2026090501,2026090502)`, `(2026091401,2026091402)`,
  `(2026091501,2026091502)`; no search or replacement after observation.
- [x] **C02** Block seeds `2026091300..2026091315` for every graph pair.
- [x] **C03** n=64; f=1.2 primary rows 59/52; f=1.0 sanity rows 49/43.
- [x] **C04** Arms: marginal L1, L1-to-L2 transfer, marginal L2, L2-to-L1
  transfer, forward/reverse joint outcomes; `max_iter=90`,
  `damping_alpha=1.0`; accepted Model-F input.
- [x] **C05** Fresh user-specified `workspace/` root; manifest, per-call
  records, per-block paired table, per-graph summary, across-graph summary,
  report, command log; never overwrite.
- [x] **C06** Raw paired discordant counts by graph; exact two-sided
  McNemar/binomial p-values and confidence intervals as descriptive
  diagnostics only; no pooled claim.
- [x] **C07** Terminal vocabulary `GRAPH_SENSITIVITY_OBSERVED`,
  `NO_GRAPH_SENSITIVITY_OBSERVED_IN_BOUNDED_SAMPLE`, `INCONCLUSIVE`, or the
  engineering/resource blocker; all carry
  `EXPLORATORY_SYNTHETIC_SINGLE_IMPLEMENTATION`.

## Phase D — bounded feasibility/strong-reference design

- [x] **D01** No exhaustive ML promise for n=64 GF32.
- [x] **D02** Reference ladder: current decoder at 90; same decoder at the
  frozen 360 ceiling; the existing flooding schedule at 90 (already exists,
  same contract). No new decoder family.
- [x] **D03** Per arm exact/syndrome-valid/posterior-score-where-computable/
  residual-syndrome-weight/changed-outcome fields.
- [x] **D04** Tiny exact-enumeration tests for score/ranking correctness;
  n=64 results labeled `STRONG_REFERENCE_DIAGNOSTIC`.
- [x] **D05** Ladder applies only to the frozen multi-graph f=1.2 failing
  blocks; no adaptive seed replacement.

## Phase E — G2 readiness

- [x] **E01** Reconcile the current G2 implementation with the accepted D5
  plan (n=256, f, rows, seeds, APP/oracle counts, ceilings); record the
  reconciliation deltas.
- [x] **E02** Preserve the four-state interpretation; no unconditional
  `ROUTE_DEAD` claim is revived.
- [x] **E03** Add injected/fake-runner tests for the exact matrix, budget
  accounting, additive output, per-layer metrics, and no accidental decoder
  call.
- [x] **E04** State `G2_RUNTIME_UNVERIFIED`; no runtime estimate until
  explicitly authorized measured/scaled probes.

## Phase F — tests and review readiness

- [x] **F01** T0: focused import/compile and tiny mathematical tests.
- [x] **F02** T1: all focused provenance, equivalence, schema, multi-graph
  aggregation, exact-statistic, reference-ladder, no-overwrite, and G2
  fake-runner tests.
- [x] **F03** Test-only calls inject fake decoders and fresh
  `workspace/<task>/<uuid>` roots; production decoder call count is zero.
- [x] **F04** Record exact commands, exit codes, and concise outputs
  (`OPERATOR_RETURN_R1.md`).
- [x] **F05** Prepare the review entrypoint and scoped changed-file manifest;
  stop at `IMPLEMENTATION_CANDIDATE_AWAITING_INDEPENDENT_REVIEW`.

## Phase P — operational closeout (X1–X4 entrypoints; master R1 packet)

> Authority: `.workbuddy/tasks/D7_X1_X4_EXECUTION_MASTER_R1_TASK_PACKET.md`
> Phase P. Implementation/test/readiness only; production decoder/CAL/VAL
> calls are zero and no X phase runs. P10 is performed by the orchestrator
> and is not self-accepted. Lifecycle after P01–P09:
> `X_PHASE_READY_PENDING_INDEPENDENT_READINESS_REVIEW`.

- [x] **P01** `--historical-provenance-probe` mode calling
  `probe_historical_decoder_provenance(decode_fn=None)` exactly once; one
  JSON record; no write, no root; refuses unless authorized; `--consistency`
  relabelled `same-input synthetic consistency` (never X1).
- [x] **P02** Exit 0 only for exact `CHECK_UPDATED` + finite + shape-valid +
  `iterations >= 1`; otherwise nonzero with `X1_PROVENANCE_PROBE_FAILED` on
  stderr; record carries resolved decoder identity, provenance, accepted
  flag, iterations, shape/finite status, `decoder_calls: 1`, `writes: 0`.
- [x] **P03** X3 selector over the immutable X2 root: f=1.2 executed
  (invoked, non-crash, finite) non-exact records only; identity fields
  preserved exactly; no dedup/replacement.
- [x] **P04** X3 ceiling: `3 * selected <= 576` ladder calls recorded before
  any decoder bind; deterministic source replays for TARGET reconstruction
  bounded by 96 and reported separately; zero selected ->
  `X3_NOT_APPLICABLE_NO_FAILED_CALLS` with zero calls.
- [x] **P05** X3 deterministic reconstruction of H/prior/syndrome/truth and
  a field-exact `ROW_LAYERED_90` replay equality gate; first mismatch is
  `X3_BASELINE_REPLAY_MISMATCH_BLOCKED` and stops all later records.
- [x] **P06** X3 fresh root with the seven frozen files, written
  never-overwrite; `selected_records.csv` before decoder binding; claim
  label `STRONG_REFERENCE_DIAGNOSTIC`.
- [x] **P07** `--reference-ladder --x2-root <exact> --out-root <exact>`
  requiring `x3_reference_ladder_authorized: true`; refuses before reading
  X2, binding decoders, or creating a root when false.
- [x] **P08** `--g2` bridge requiring `x4_g2_execution_authorized: true` and
  every D5 execution flag false; calls `run_g2_synthetic(authorized=True)`
  exactly once; never sets the D5 `g2_execution_authorized` flag.
- [x] **P09** X4 writes only the frozen fresh root
  `workspace/v72p2d5_g2/20260906_r1` (abort if present); four-file schema
  plus the accepted additive per-layer/wall/RSS fields.
- [x] **P-prior** Reference-ladder bind/import/signature coverage proven
  without calling a production decoder (fake-module wrapper contract + clean
  real-import bind subprocess); true-condition binding probe assigned to X3
  Pre-EXECUTE before authorization consumption.
- [x] **P-ready** Pre-EXECUTE readiness record
  (`PHASE_P_PRE_EXECUTE_READINESS_R1.md`): frozen commands, target-root
  absence, budgets/stop rules, flags, focused tests, P10 entrypoint.
- [ ] **P10** Independent implementation/Pre-EXECUTE readiness review
  (orchestrator-owned; not self-accepted).
