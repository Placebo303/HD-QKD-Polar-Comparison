# Code-factor extrinsic contract — proposal (freeze only, Phase B)

> Status: freeze only. Docs, no code, no execution, no authorization.
> Operator authority: `.workbuddy/tasks/D7_F_ACCEPT_D7_G_EXTRINSIC_CONTRACT_READINESS_R1_TASK_PACKET.md`
> §§1.2 + 5 only (Phase B). All execution/promotion authorizations remain
> false. Starting HEAD `250799b4` (Phase A commit). Predecessor D7-F
> acceptance: `D7_F_RESULT_ACCEPTED_REVERSE_ORDER_REGRESSION_DIAGNOSTIC`.
> Implementation comes later under separate authority; no decoder call, no
> Model-F/real read, no root/UUID, no R1d/`--phase`/G1/G2, no push.

## What

Freeze the exact code-factor extrinsic-message contract that lets a future
alternating cross-layer BP pass check evidence forward without returning a
layer's incoming evidence back to itself. For a cold decoder with normalized
positive input prior `p_in(x)` and final log belief `L_post(x)`, the outgoing
code-factor extrinsic message is defined only up to a per-symbol-variable
additive constant:

```text
L_code_ext(x) = L_post(x) - log(p_in(x))
```

Transport normalization is stable softmax. This removes the entire incoming
prior — including channel and cross-layer evidence — from the outgoing
message, leaving only the decoder's accumulated parity-check evidence under
its BP recurrence.

## Why

- D7-F accepted scope (`D7_F_RESULT_ACCEPTED_REVERSE_ORDER_REGRESSION_DIAGNOSTIC`)
  shows reversing a single sequential pass does not convert the D7-E
  directional target lift into complete two-layer recovery. The route out
  requires alternating passes, which are blocked until a cavity/extrinsic
  contract exists: posterior back-transfer would double-count the
  originating layer's syndrome.
- Existing `belief_provenance` (`PRIOR_ONLY` / `CHECK_UPDATED` /
  `WARM_START_UNSPECIFIED`) proves a posterior consumed checks, but exposes
  no cavity message. This change adds the extrinsic field and provenance;
  it changes no decoder numerics and no existing consumer.

## Contract boundaries (from packet §1.2, frozen here)

- It is a BP factor message, not a calibrated exact posterior and not MAP truth.
- Valid only for cold start after at least one completed check sweep and
  finite shape-correct beliefs.
- Iteration 0 emits no usable check evidence: neutral zeros plus provenance
  `NO_CHECK_EVIDENCE`, ineligible for cross-layer transfer.
- Warm-start extrinsic remains `WARM_START_UNSPECIFIED` and fail-closed.
- Existing `final_beliefs` and `belief_provenance` semantics remain unchanged
  for current consumers.
- No consumer may infer extrinsic by subtracting an unknown/reconstructed
  prior; the decoder result must carry an explicit optional extrinsic field
  and provenance.
- No multi-round alternating execution is allowed until this contract passes
  independent certification.

## Frozen tokens, fields, behaviors (detail in design.md / spec.md)

- Extrinsic-provenance namespace (exact, distinct from `belief_provenance`):
  `NO_CHECK_EVIDENCE`, `CHECK_EXTRINSIC`, `WARM_START_UNSPECIFIED`.
- Optional result fields (fixed names): `extrinsic_log_beliefs`,
  `extrinsic_provenance`.
- Stored field is row-normalized by subtracting log-sum-exp (frozen;
  rationale in design.md: log-sum-exp, not max).
- No-persistence rule: no beliefs/messages persisted by any writer.
- Cold: ≥1 completed check sweep + finite shape-correct beliefs →
  `CHECK_EXTRINSIC`. Iteration 0: neutral zeros + `NO_CHECK_EVIDENCE`,
  ineligible for transfer. Warm: `WARM_START_UNSPECIFIED`, fail-closed.
  Nonfinite/shape mismatch: fail-loud, never silently repaired.
- Tolerances: `1e-10` max-abs for tree-exact distribution match and for
  independent-recurrence match (D7-A/BP precedent; no loosening without a
  pre-results justification recorded here — none recorded).

## Certification matrices (frozen families; detail in design.md)

- Tree-exact: tiny GF32 degree-2/3 tree checks, multiple coefficients,
  nonzero syndromes, asymmetric priors, negative direction/label controls.
- Loopy: 1–3 sweeps vs an independently coded recurrence (never vs MAP).
- Two-layer tree (channel factor `P(U1,U2|B)` + two syndrome factors):
  posterior double-count counterexample + forward/backward sum-product match
  + iteration-0 no-false-lift + warm rejection. Decisive certification: if
  no deterministic counterexample or exact match can be produced, STOP with
  mathematical ambiguity (packet §7 D04).
- Fixture conventions mirror D7-A/BP: Q=32, poly 37, `1e-10` asserts, fixed
  seeds frozen in design.md.

## Compatibility + consumer migration (frozen)

- Additive optional fields only; `final_beliefs`/`belief_provenance`
  semantics unchanged.
- NO consumer auto-switches to the new field.
- A static inventory test must fail if any production cross-layer consumer
  uses explicit extrinsic without its own future OpenSpec.

## Non-goals (frozen)

- No implementation, tests, oracle code, decoder calls, or certification
  results in this change.
- D7-H remains not frozen / not authorized; no multi-round alternating
  execution until this contract passes independent certification.
- No modification of accepted D7-B/C/D/E/F roots, frozen baseline `src/`,
  `experiments/`, `tools/`; no overwrite of existing outputs.
- No tolerance loosening, no posterior renamed as extrinsic (packet §3).

## Acceptance tests for the future implementation (IDs stable, detail in design.md)

- EXT-01 algebra/invariance (scaling, row-constant, reconstruction identity).
- EXT-02 tree-exact distribution match (≤1e-10) with negative controls.
- EXT-03 loopy independent-recurrence match after 1–3 sweeps (≤1e-10, never MAP).
- EXT-04 no-returned-evidence demonstration (double-count counterexample,
  forward/backward match, it0 no-false-lift, warm rejection).
- EXT-05 enum/field coverage at all decoder return sites; cold/it0/warm/
  nonfinite paths; helper rejection matrix; BP provenance guards unchanged.
- EXT-06 compatibility: existing outputs/roots untouched; consumers retain
  prior behavior; static inventory guard for future extrinsic consumers.

## Gating rules (frozen)

- Preregistration/OpenSpec commit precedes any behavior implementation
  (packet §5).
- If exact extrinsic semantics cannot be certified independently, STOP; do
  not weaken tolerances or rename posterior as extrinsic (packet §3).
- Neither this freeze nor its future reviews authorize D7-H.
