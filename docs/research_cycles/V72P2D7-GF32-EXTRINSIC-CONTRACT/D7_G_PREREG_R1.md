# D7-G code-factor extrinsic contract preregistration R1 (frozen before any implementation or decoder observation)

- Branch `formal-ir-v72p1-addendum-clean`; starting HEAD `250799b4`
  (Phase A commit). Provenance only; no remote-equality requirement.
- Packet binding:
  `.workbuddy/tasks/D7_F_ACCEPT_D7_G_EXTRINSIC_CONTRACT_READINESS_R1_TASK_PACKET.md`
  (R1) §5; this prereg is the Phase B freeze. §§1.2 + 5 bind fully.
- Status: `FROZEN_PREREG_R1` and `NOT_AUTHORIZED_NOT_EXECUTED`.
  **Observation ordering:** this prereg is committed (scoped docs/OpenSpec
  commit) before any D7-G implementation, decoder observation, or
  certification number. No D7-G decoder call, no Model-F binary content
  read, no output root, and no D7-G identifier exist at freeze time.
- Predecessor facts (immutable): D7-F accepted scope
  `D7_F_RESULT_ACCEPTED_REVERSE_ORDER_REGRESSION_DIAGNOSTIC` (128/128
  calls, zero blocked/retry/crash/nonfinite/watchdog; `f=1.0` forward and
  reverse both-layer exact `0/16`; `f=1.2` forward `2/16`, reverse `0/16`;
  reverse-vs-forward `candidate_only=0`, `reference_only=2`, `both=0`,
  `neither=14`; terminal `D7_F_REVERSE_ORDER_REGRESSION`). Permitted
  inference: reversing a single sequential pass does not convert D7-E's
  directional target lift into complete two-layer recovery under the frozen
  synthetic contract. BP Alternative A is the current interface contract
  (`PRIOR_ONLY` / `CHECK_UPDATED` / `WARM_START_UNSPECIFIED`; only
  `CHECK_UPDATED` may feed a conditioned cross-layer APP). All
  authorization false. No `workspace/d7_g_*` root exists.

## 1. Frozen contract (packet §1.2 in substance; full text in the OpenSpec change)

- Formula: `L_code_ext(x) = L_post(x) - log(p_in(x))`, defined up to a
  per-symbol-variable additive constant; transport normalization = stable
  softmax; stored field row-normalized by subtracting log-sum-exp (frozen;
  rationale in `design.md`: log-sum-exp, not max).
- Enum values (extrinsic-provenance namespace, distinct from
  `belief_provenance`): `NO_CHECK_EVIDENCE`, `CHECK_EXTRINSIC`,
  `WARM_START_UNSPECIFIED`.
- Optional result fields (fixed names): `extrinsic_log_beliefs`,
  `extrinsic_provenance` (additive, defaulted `None`; `None` never
  upgraded to `CHECK_EXTRINSIC`).
- No-persistence rule: no beliefs/messages persisted by any writer.
- Cold behavior: ≥1 completed check sweep + finite shape-correct beliefs
  → `CHECK_EXTRINSIC`. Iteration-0 behavior: neutral zeros +
  `NO_CHECK_EVIDENCE`, ineligible for transfer. Warm behavior:
  `WARM_START_UNSPECIFIED`, fail-closed. Nonfinite/shape mismatch:
  fail-loud, never silently repaired.
- Tolerances: `1e-10` max-abs for tree-exact distribution match and for
  independent-recurrence match (D7-A/BP precedent; no loosening without a
  pre-results justification recorded here — none recorded).
- Compatibility + consumer migration: additive optional fields only;
  existing `final_beliefs`/`belief_provenance` semantics unchanged; NO
  consumer auto-switches to the new field; a static inventory test must
  fail if any production cross-layer consumer uses explicit extrinsic
  without its own future OpenSpec.
- D7-H remains not frozen / not authorized; no multi-round alternating
  execution until this contract passes independent certification.

## 2. Frozen certification matrices (packet §§7–8 in substance; families in `design.md`)

- EXT-T tree-exact: tiny GF32 degree-2/3 tree checks, multiple
  coefficients, nonzero syndromes, asymmetric priors, negative
  direction/label controls; distributions vs exact enumeration, ≤1e-10.
- EXT-L loopy: 1–3 sweeps vs independently coded recurrence, ≤1e-10,
  never vs MAP.
- EXT-N two-layer tree (`P(U1,U2|B)` + two syndrome factors): posterior
  double-count counterexample + forward/backward sum-product match + it0
  no-false-lift + warm rejection.
- Fixture conventions mirror D7-A/BP (Q=32, poly 37, exact-enumeration
  oracles, `1e-10` asserts, fixed seeds `2026091401..2026091404`).

## 3. D04 decisive-certification statement (packet §7 D04, verbatim in substance)

This is the decisive certification. If no deterministic counterexample
(posterior back-transfer double-counts the originating syndrome) or exact
match (explicit code-extrinsic transfer matches independent sum-product
factor messages for one forward and one backward update within tolerance)
can be produced, STOP and return the mathematical ambiguity. Do not weaken
tolerances or rename posterior as extrinsic.

## 4. Frozen implementation file map (names fixed here for the later implementer)

- Independent oracle:
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_extrinsic_oracle.py`
  (must not import the production check-update/extrinsic helper;
  numpy-only).
- Tests:
  `comparison_bench/tests/test_v72p2d7_gf32_extrinsic_contract.py`.
- Producer/helper edits confined to:
  `comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py`
  (additive optional fields + one narrow consumer helper).
- Flooding receives the same additive fields ONLY if needed for
  `DecoderResult` coherence (decision rule in `design.md`, default
  DEFERRED).

## 5. Authorization lifecycle

- State file
  `docs/research_cycles/V72P2D7-GF32-EXTRINSIC-CONTRACT/cycle_state.yaml`
  holds all execution authorization and promotion fields false
  (`decoder_executed: false`, `result_created: false`); attempts zero; no
  identifier, no root.
- The future implementer works only from the frozen file map above; no
  production code/test edits, decoder calls, Model-F/real reads, or
  R1d/`--phase`/G1/G2 under this freeze.
- Explicit future authorization is required for implementation; none is
  granted by this prereg.

## 6. Nonclaim boundaries

No FER, leakage, reconciliation-efficiency, key-rate, CAL/real-data,
qualification, promotion, R1d, G1/G2, or general GF32/NB-LDPC claim. This
freeze accepts no algorithm result — only the interface/certification
contract for a later gate. D7-H is not frozen and not authorized.

## 7. Freeze statement

This prereg froze every formula, token, field name, behavior rule,
tolerance, fixture family, compatibility rule, and file path above at HEAD
`250799b4`, before any D7-G implementation or decoder observation.
Implementation may follow only after the scoped commit of this prereg. All
authorizations are false; no identifier exists; no `workspace/d7_g_*`
root exists.
