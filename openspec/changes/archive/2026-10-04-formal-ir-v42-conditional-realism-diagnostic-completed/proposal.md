# OpenSpec Proposal: formal-ir-v42-conditional-realism-diagnostic

**Status**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`
**Domain**: Formal Information Reconciliation / Nonbinary LDPC research
**Change ID**: `formal-ir-v42-conditional-realism-diagnostic`
**Cycle ID**: `V42P0`
**Predecessor cycle**: `V41P0` (`formal-ir-v41-fresh-block-confirm`)
**Predecessor terminal**: `V41_C_ONLY_RETAINED` (run_01: lane_c exact 8/9,
per-source 3/3/2, zero wrong codewords; lane_b gates failed 6/9; recorded
lifecycle `DEVELOPMENT_RESULT_CANDIDATE` in the run_01 summary)
**Predecessor implementation/execution SHA** (recorded in run_01 provenance,
bound HEAD = origin/formal-ir-mainline at V41 execution):
`6d75e754899e8470445c2bf58f2f4ff84130fc33`
**Predecessor accepted plan SHA**: TBD - bound at this change's implementation
freeze from the committed evidence (tasks A12).

## Why

V41 confirmed Lane C route retention on nine fresh blocks under **oracle-L1**
conditioning only: the decoder received the true Alice Layer-1 symbols
(`u1_alice`), an input no real protocol can obtain. Before any budget moves to
more-realistic data or end-to-end benchmarking, one small paired diagnostic
must answer a single question:

**Does Lane C retain its signal on fresh blocks when the oracle-L1 conditioning
is replaced by `cond_estimated_l1` (the idealized uncoded MAP-L1 estimated
condition) - or does the measured performance loss arise from this MAP-L1
conditioning mechanism itself rather than the Lane C graph structure?**

This change freezes that diagnostic: Lane C only, fixed per-source ordinal-2
representative matrices, single frozen setting (max_iter=90, damping_alpha=1.0),
nine never-used development blocks (3 per source), each block decoded exactly
twice as a PAIR - once with oracle-L1 conditioning (current capability upper
bound) and once with the frozen `cond_estimated_l1` mechanism (design Section
7, decision D13, RESOLVED by user adjudication 2026-08-26). Exactly 18 real
decoder calls, exactly once, no tuning, additive outputs, total/disjoint
terminal machine over the two per-condition gates.

## Scope

This planning change freezes the V42P0 conditional-realism diagnostic protocol
only:

1. **Paired diagnostic (exactly 18 calls)**: three never-used TRAIN development
   blocks per source (1M = 390110/390111/390112, 1p5M = 390210/390211/390212,
   2M = 390310/390311/390312); each block sampled ONCE deterministically and
   shared by both arms of its pair; each pair decoded once per condition with
   that source's lane_c ordinal-2 representative matrix at the single frozen
   setting; GF(32) polynomial 37; syndrome from true `u2_alice`;
   success = `exact_l2`. No baseline, no additional matrices, no Lane B.
2. **Two conditions per block**: `cond_oracle` = complete-Bob posterior with
   true `u1_alice` selector (upper bound); `cond_estimated_l1` = same posterior
   function with the frozen MAP-L1 hard estimate selector (design Section 7;
   Candidate A adjudicated by the user 2026-08-26: idealized uncoded MAP
   Layer-1 estimate from public counts marginals - RESOLVED, definition frozen
   verbatim in design Section 7).
3. **Per-condition gates** mirroring the accepted V41 gate form: overall exact
   >= 7/9 within the arm; every source >= 2/3 within the arm; that arm wrong
   codewords = 0.
4. **Total, disjoint terminal machine**: integrity-first (`V42_EVIDENCE_INVALID`
   precedence); `V42_BOTH_CONDITIONS_PASS` /
   `V42_ORACLE_ONLY_CONDITIONING_BOTTLENECK` / `V42_GO_STRUCTURE` /
   `V42_ANOMALOUS_INVERSION` partition the (oracle_pass, estimated_l1_pass)
   plane exhaustively and mutually exclusively (integrity x {both_pass,
   oracle_only, estimated_only(ANOMALOUS), both_fail}); the fifth terminal
   `V42_ANOMALOUS_INVERSION` is ACCEPTED (user ruling 2026-08-26) and means
   only that finite-sample, iteration-trajectory, or conditional-posterior
   differences require inspection - never that estimated-L1 is superior to
   oracle. Wrong
   codewords are arm-local only: recorded, NEVER counted as exact, acting
   through their own arm's zero-wrong clause plus an arm-level
   `stopped_for_analysis` marker; any oracle-arm wrong codeword raises a
   prominent dedicated anomaly flag (an upper-bound condition should not
   produce wrong codewords).
5. Budget accounting with planned/completed/started actuals, scientific-
   preflight-first invalidation (zero-call stop with invalid trio), hard cap 18
   with structural refusal of call 19, and additive evidence outputs.

No execution is performed by this planning round. Implementation may not start
before independent plan ACCEPT; decision D13 (O1 mechanism) is RESOLVED -
Candidate A frozen as `cond_estimated_l1` by user adjudication 2026-08-26.
Any future implementation candidate stops at
`IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`; the diagnostic run
requires an explicit user `EXECUTE_AUTH` bound to the exact implementation SHA,
scope `v42_diagnostic_18_calls_exactly_once`.

## Non-goals

- Not a parameter search and not a tuning round: one fixed setting (90/1.0);
   no iteration grid, no damping grid, no warm start, no second setting, and NO
   change to the frozen `cond_estimated_l1` mechanism (adjudicated 2026-08-26).
- No baseline run, no Phase B staging, no Lane B participation, no additional
  matrices beyond the three frozen lane_c ordinal-2 representatives.
- No reuse of any prior-cycle block as a diagnostic sample; no block addition,
  supplementary run, rerun, resume, post-result threshold edit, or post-result
  seed addition; NO second diagnostic round regardless of outcome.
- Terminals SHALL NOT be read as superiority claims, qualification, promotion,
  FER, asymptotic threshold, SKR, security, or real-frame statements of any
   kind, and SHALL NOT auto-start successor work; successor directions (Lane C
   toward more-realistic data / end-to-end benchmark after dual pass;
   protograph/MET structure design after GO_STRUCTURE; conditioning-mechanism
   improvement after CONDITIONING_BOTTLENECK; analysis-only after
   ANOMALOUS_INVERSION) are directional descriptions only. An
   ORACLE_ONLY_CONDITIONING_BOTTLENECK outcome attributes the loss ONLY to
   the frozen MAP-L1 conditioning mechanism, never to a concrete upstream
   coding scheme or a real system.
- No constructor, loader, evaluator, decoder, or v35/v38 modification; the
  v39/v40/v41 modules are NOT imported.

## Affected specs

New delta spec only:
`specs/formal-ir-v42-conditional-realism-diagnostic/spec.md`.
No existing spec, code, test, output, or memory file is modified by this
planning change.

## Lifecycle

This change ends at `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` with
`development_execution_authorized`, `formal_execution_authorized`,
`scientific_promotion`, `implementation_started`, and
`production_outputs_created` all false. Independent plan review and an
explicit user `EXECUTE_AUTH` bound to the exact implementation SHA are
required before any implementation or execution work starts; D13 (O1) was
adjudicated by the user on 2026-08-26 (Candidate A frozen as
`cond_estimated_l1`) and no further adjudication is pending. The V41P0
run_01 evidence stands as recorded (terminal
`V41_C_ONLY_RETAINED`); by its own claim boundary that terminal authorizes
nothing by itself. Execution authorization requires only this change's
independent plan ACCEPT plus explicit user `EXECUTE_AUTH` bound to the exact
implementation SHA, scope `v42_diagnostic_18_calls_exactly_once`.
