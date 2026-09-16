# D11 Canonical Forward APP Integration — readiness task packet

## 1. Purpose and authority

Track: implementation/readiness only; the future batch is `EXPLORE_HEAVY`.
Predecessor accepted as
`D10_R3_WIDE_L1_SIGNAL_ACCEPTED_ROUTE_TO_D11_FORWARD_APP`.

Build the smallest experiment that answers whether the reproducible mixed-L1
signal survives one canonical L1→L2 APP transfer, while separately measuring
the L2 decoder ceiling. This task authorizes OpenSpec/code/docs, focused fake
tests and no-decoder profiling only. It authorizes zero scientific calls.

D7-H is explicitly out of scope. A forward pass plus L2 oracle must be resolved
before reverse/alternating feedback can be interpreted.

## 2. Frozen scientific design

Widths: n128 first; n256 only if n128 is `D11_FORWARD_SIGNAL`.

Per width, use six graph pairs and 12 paired blocks. Reuse the accepted R3 L1
graph seeds and blocks so L1 results must replay exactly:

- n128 L1 graphs `2026092401..06`, blocks `2026092601..12`;
- n256 L1 graphs `2026092501..06`, blocks `2026092701..12`.

Create one shared connected/full-rank DV3 L2 graph per pair:

- n128 L2 seeds `2026092801..06`, rows m=104, E=384, variables all degree 3,
  checks `3^32 + 4^72`;
- n256 L2 seeds `2026092901..06`, rows m=208, E=768, variables all degree 3,
  checks `3^64 + 4^144`.

Use the accepted connectivity-first constructor, A1--A6, frozen coefficient
rule, GF32/poly37, Model-F prior chain, max_iter=90/damping=1.0/cold and the
canonical CHECK_UPDATED provenance/q/APP helpers. Audit and reuse the existing
D5/D7 forward-transfer and D6 oracle definitions; do not reimplement message
semantics. The only treatment difference is L1 degree profile:

- CONTROL: DV3 L1 → the shared DV3 L2 APP decoder;
- MIX: λ2=0.45 mixed L1 → the same shared DV3 L2 APP decoder;
- ORACLE: the same L2 graph/block with the accepted true-L1 conditional prior,
  run once per graph/block and shared diagnostically across both arms.

Per width: 72 L1+L2 paired cells. Scientific calls are 72 CONTROL L1 + 72
CONTROL L2 + 72 MIX L1 + 72 MIX L2 + 72 shared ORACLE L2 = 360. Maximum 720.
Exact, syndrome-valid, L1 source exact, L2 target exact and joint both-exact
must remain distinct. Fail closed unless every non-oracle transfer provenance
is `CHECK_UPDATED`; uniform/prior-only fallback is forbidden.

L1 replay is a hard validity gate: per-graph exact vectors must equal R3
n128 MIX `[4,4,2,5,3,5]`, CONTROL all zero; n256 MIX `[6,3,5,5,6,4]`, CONTROL
all zero. A mismatch is engineering-blocked and stops before interpretation.

For each width let `J_M,J_C` be pooled joint both-exact counts; `O` pooled L2
oracle exact; and `J_Mg,J_Cg` per graph.

`D11_FORWARD_SIGNAL(w)` iff: `J_M>=9`; `J_M-J_C>=6`; MIX wins on ≥4/6 graph
pairs; ≥3/6 MIX graphs have `J_Mg>=1`; `J_C<=3`; `O>=18`; all 72 MIX and 72
CONTROL transfers are CHECK_UPDATED; no engineering/resource violation.

`D11_TRANSFER_BOTTLENECK(w)` iff MIX L1 exact ≥18, `J_M<=3`, and `O>=18`.
`D11_L2_CODE_BOTTLENECK(w)` iff `O<=6`. Otherwise `D11_FORWARD_AMBIGUOUS(w)`.
These are mutually prioritized in order: engineering block, L2-code bottleneck,
forward signal, transfer bottleneck, ambiguous. Report paired discordances and
conditional target success descriptively; they do not override the gate.

Terminals:

- n128 forward signal, n256 forward signal → `D11_FORWARD_APP_WIDE_RECOVERY`;
- n128 signal, n256 transfer/L2/ambiguous → corresponding
  `D11_N256_TRANSFER_BOTTLENECK`, `D11_N256_L2_CODE_BOTTLENECK`, or
  `D11_N256_FORWARD_AMBIGUOUS`;
- n128 stop → corresponding `D11_N128_TRANSFER_BOTTLENECK`,
  `D11_N128_L2_CODE_BOTTLENECK`, or `D11_N128_FORWARD_AMBIGUOUS`;
- explicit engineering/resource blocked terminal otherwise.

Future root:
`workspace/d11_forward_app_7c1878b5-23a8-4fd8-a395-b5a33a58ea64`.
Budgets: ≤720 scientific calls; ≤64 setup units; ≤2400 s wall; ≤120 s/call;
RSS <2147483648 B; one process; no retry/resume/repair/seed search/tuning.

Claim ceiling: synthetic two-layer forward diagnostic only; no FER, leakage,
SKR, real-data, qualification, promotion, optimality or D7-H claim.

## 3. Readiness tasks D1101--D1110

- D1101: create D11 OpenSpec proposal/design/tasks/spec before behavior edits;
  include exact equations, priorities, seeds, calls, terminals and rationale.
- D1102: audit the nearest accepted forward APP, provenance and oracle helpers;
  record exact reuse map and reject semantic duplication.
- D1103: implement a thin additive D11 plan/runner/verifier reusing D10 R2/R3
  graph/decoder paths and canonical D5/D7 transfer helpers.
- D1104: require an explicit default-false execution CLI flag; refuse before
  root creation, decoder binding or Model-F load.
- D1105: enforce L1/L2 A1--A6 and exact R3 L1 replay before result grading;
  no graph/seed replacement.
- D1106: implement call accounting, provenance fail-close, gate priorities,
  conditional n256 dispatch, six-file-or-minimal-equivalent never-overwrite
  output and fail-closed read-only verifier.
- D1107: focused tests covering graph tables/seeds, shared-L2 identity, exact
  call ceiling, replay mismatch, provenance refusal, exact/syndrome/joint
  isolation, every gate/terminal boundary, conditional dispatch and no-write
  unauthorized refusal; production calls must be fake-injected.
- D1108: run `py_compile` and focused D11 plus directly affected predecessor
  tests in a fresh basetemp; no broad suite absent a focused external failure.
- D1109: PROFILE_ONLY all future L1/L2 graphs and plan: require A1--A6,
  deterministic replay construction, correct 360→conditional-720 identities,
  zero decoder calls and absent future root.
- D1110: one independent readiness review with `EVIDENCE_ACCESS: VERIFIED`
  independently checking reuse semantics, L1 replay contract, shared L2/oracle
  isolation, gates/priorities, calls/budgets and no-production boundary; append
  one log/readiness record and perform memory triage.

## 4. STOP and return

STOP on semantic ambiguity, inability to reuse canonical transfer/oracle,
seed/table drift, admission failure, need for seed replacement, provenance
fallback, decoder/scientific entry, root creation, failed review or conflicting
dirty edits. Do not execute D11, modify predecessor roots, implement D7-H,
commit or push.

Return `D11_FORWARD_APP_READY_AWAITING_EXPLICIT_AUTHORIZATION` only when all
D1101--D1110 pass with zero scientific calls and no blocking review finding.
Otherwise return one exact blocker with raw evidence and the decision needed.
