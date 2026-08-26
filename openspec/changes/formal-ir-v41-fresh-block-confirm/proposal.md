# OpenSpec Proposal: formal-ir-v41-fresh-block-confirm

**Status**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`
**Domain**: Formal Information Reconciliation / Nonbinary LDPC research
**Change ID**: `formal-ir-v41-fresh-block-confirm`
**Cycle ID**: `V41P0`
**Predecessor cycle**: `V40P0` (`formal-ir-v40-decoder-cap-diagnostic`)
**Predecessor terminal**: `V40_PROBE_CONFIRM_ALLOWED` (probe exact_total 5/6,
`exact_lane_c` 3/3, `exact_lane_b` 2/3, zero wrong codewords; lifecycle
`DEVELOPMENT_RESULT_ACCEPTED`)
**Predecessor result SHA**: `a546d43c74be5f11e87426ff7ce837b31dd20142`
**Predecessor implementation/execution SHA** (`authorized_target_sha`, bound
HEAD = origin/formal-ir-mainline at execution):
`80d605489f1f65eefd091625134514e8a09902de`
**Predecessor accepted plan SHA** (historical reference):
`36a3751e190ff06e0e88024b51b6f8713c13a4dc`

## Why

The V40P0 diagnostic fired `CAP_MATERIAL` (5 rescues out of 12, zero wrong
codewords) and its 6-call fresh-block probe returned `V40_PROBE_CONFIRM_ALLOWED`
(exact_total 5/6, lane_c 3/3, lane_b exactly at the 2/3 boundary, zero wrong
codewords). By V40's own frozen semantics that terminal permits EXACTLY ONE
small fresh-block confirmation cycle, to be proposed under a NEW OpenSpec
change with new authorization - this change.

Before spending further budget on Lane B/C, this single confirmation answers
one question on fresh, never-used development blocks:

**Do Lane C and Lane B each independently retain their route signal on 9
never-used blocks (3 per source) at the fixed setting (max_iter=90,
damping_alpha=1.0) - or does current B/C parameter optimization stop and the
budget move toward protograph/MET structure design?**

This change freezes that confirmation: exactly 18 real decoder calls
(9 blocks x 2 lanes), exactly once, no decoder-parameter tuning, no reuse of
the V40 probe blocks as confirmation samples, additive outputs, and a total,
disjoint per-lane-gated terminal machine.

## Scope

This planning change freezes the V41P0 confirmation protocol only:

1. **Confirmation (exactly 18 calls)**: three never-used TRAIN development
   blocks per source (1M = 390107/390108/390109, 1p5M = 390207/390208/390209,
   2M = 390307/390308/390309), each block decoded once per lane with that
   source's representative ordinal-2 matrix, all at the single frozen setting
   `max_iter=90, damping_alpha=1.0`; GF(32) polynomial 37, complete-Bob
   posterior, oracle-L1 conditioning, success = `exact_l2`. No baseline, no
   Phase B staging, no additional matrices.
2. **Per-lane independent retention gates** (route retention only, not a B/C
   superiority test): lane overall exact >= 7/9; every source exact >= 2/3;
   that lane wrong codewords = 0.
3. **Total, disjoint terminal machine**: integrity-first
   (`V41_EVIDENCE_INVALID` precedence); each lane gated independently
   (overall exact >= 7/9, every source >= 2/3, that lane wrong codewords =
   0); `V41_BOTH_LANES_RETAINED` / `V41_C_ONLY_RETAINED` /
   `V41_B_ONLY_RETAINED` / `V41_STOP_BC_PARAMETER_OPTIMIZATION` (reason
   `BOTH_LANES_GATES_FAILED`) follow from the (lane_c_pass, lane_b_pass)
   combination - a wrong codeword affects ONLY its own lane's gate.
4. Budget accounting with planned/completed/started actuals, scientific-
   preflight-first invalidation (zero-call stop with evidence trio on
   preflight failure), hard cap 18 with structural refusal of call 19, and
   additive evidence outputs.

No execution is performed by this planning round. Any future implementation
candidate stops at `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`; the
confirmation run requires an independent plan ACCEPT plus an explicit user
`EXECUTE_AUTH` bound to the exact implementation SHA.

## Non-goals

- Not a parameter search and not a tuning round: one fixed setting (90/1.0);
  no iteration grid, no damping grid, no warm start, no second setting under
  any outcome.
- No baseline run, no Phase B staging, no additional matrices beyond the six
  frozen ordinal-2 representatives.
- No reuse of the V40 probe blocks (390106/390206/390306) as confirmation
  samples; no block addition, supplementary run, rerun, resume, post-result
  threshold edit, or post-result seed addition; NO second confirmation round
  regardless of outcome.
- Retention terminals SHALL NOT be read as B/C superiority claims,
  qualification, promotion, FER, asymptotic threshold, SKR, security, or
  real-frame statements of any kind, and SHALL NOT auto-start successor work;
  successor directions (more-realistic/non-oracle comparison after dual
  retention; protograph/MET after STOP) are directional descriptions only.
- No Lane A participation; no constructor, loader, evaluator, or decoder
  modification; v39/v40 modules are not imported.

## Affected specs

New delta spec only:
`specs/formal-ir-v41-fresh-block-confirm/spec.md`.
No existing spec, code, test, output, or memory file is modified by this
planning change.

## Lifecycle

This change ends at `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` with
`development_execution_authorized`, `formal_execution_authorized`,
`scientific_promotion`, `implementation_started`, and
`production_outputs_created` all false. Independent ChatGPT plan review
and explicit main-thread/user authorization are required before any
implementation or execution work starts. The V40P0 run_01 evidence stands
(terminal `V40_PROBE_CONFIRM_ALLOWED`, lifecycle
`DEVELOPMENT_RESULT_ACCEPTED`, result SHA
`a546d43c74be5f11e87426ff7ce837b31dd20142`, execution SHA
`80d605489f1f65eefd091625134514e8a09902de`); by V40's claim boundary that
terminal authorizes nothing by itself - it only marks that this one
confirmation change may be proposed. V41 itself stays
unauthorized: execution authorization requires only this change's independent
plan ACCEPT plus an explicit user `EXECUTE_AUTH` bound to the exact
implementation SHA, scope `v41_confirmation_18_calls_exactly_once`.
