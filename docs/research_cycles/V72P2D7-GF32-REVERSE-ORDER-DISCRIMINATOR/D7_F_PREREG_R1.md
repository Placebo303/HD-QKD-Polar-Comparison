# D7-F reverse-order cross-layer discriminator preregistration R1 (frozen before any real artifact or decoder observation)

- Branch `formal-ir-v72p1-addendum-clean`; starting HEAD `f4c06042`
  (Phase A commit, `docs(d7-e): accept D7-E as directional cross-layer
  transfer diagnostic`). Provenance only; no remote-equality requirement.
- Packet binding:
  `.workbuddy/tasks/D7_E_ACCEPT_D7_F_REVERSE_ORDER_READINESS_R1_TASK_PACKET.md`
  (R1) §5; this prereg is the Phase B freeze. §5 binds fully.
- Status: `FROZEN_PREREG_R1` and `NOT_AUTHORIZED_NOT_EXECUTED`.
  **Observation ordering:** this prereg is committed (scoped docs/OpenSpec
  commit) before any real D7-F artifact or decoder observation. No D7-F
  decoder call, no Model-F binary content read, no output root, and no
  D7-F identifier exist at freeze time.
- Predecessor facts (immutable): D7-E accepted scope
  `D7_E_RESULT_ACCEPTED_DIRECTIONAL_CROSS_LAYER_TRANSFER_DIAGNOSTIC`
  (192/192 frozen calls completed; 64/64 transfer slots eligible and
  invoked; `f=1.0` both directions control `0/16`, transfer `0/16`;
  `f=1.2` `L1_TO_L2` control `0/16`, transfer `3/16`,
  `AMBIGUOUS_TRANSFER_EFFECT`; `f=1.2` `L2_TO_L1` control `3/16`,
  transfer `7/16`, four transfer-only, zero control-only,
  `STRONG_TRANSFER_LIFT`; no crash/nonfinite/watchdog; wall/RSS within
  frozen limits; integrity
  `PASS_WITH_DISCLOSED_VERIFY_PROVENANCE_GAP`); permitted inference is
  direction-dependent useful transfer strongest in `L2_TO_L1` at `f=1.2`
  under the frozen synthetic contract only; forbidden inference is
  general cross-layer success, FER/leakage/key rate, qualification,
  real-data performance, proof that alternating converges, or R1d/G1/G2
  permission. BP Alternative A is the current interface contract
  (`PRIOR_ONLY` / `CHECK_UPDATED` / `WARM_START_UNSPECIFIED`; only
  `CHECK_UPDATED` may feed a conditioned cross-layer APP). The D7-E root
  (`workspace/d7_e_cross_layer_discriminator_*`, exact value pinned in
  the D7-E cycle state `d7e_execution_root`)
  is immutable. All authorization false. No
  `workspace/d7_f_reverse_order_discriminator_*` root exists.
- D7-F never constructs an oracle prior and never calls an oracle decoder.
  Accepted D7-C tables are a contextual ceiling only.

## 1. Frozen scientific question (§5 in substance)

Question: on the exact D7-E frozen identities, does reverse order
`L2→L1` recover both layers exactly on more seeds than forward order
`L1→L2`, when each arm is a complete two-pass sequence (source marginal,
then one gated cold target decode from the transfer prior), without
oracle truth or feedback?

This tests only a paired order mechanism:

```text
FORWARD_L1_TO_L2:  decode L1 marginal
  -> gate finite/non-crash/shape-valid + provenance == CHECK_UPDATED
  -> transient P(U2|B,s1) -> one cold L2 decode
REVERSE_L2_TO_L1:  decode L2 marginal
  -> same gate
  -> transient P(U1|B,s2) -> one cold L1 decode
```

It does not claim calibrated posterior, alternating convergence, leakage,
protocol recovery or Bob-only FER.

## 2. Frozen matrix, arms, formulas, accounting (§5 B01–B04)

### B01 — identities and decoder contract

- `f` order `[1.0, 1.2]`.
- Seeds `2026091300..2026091315`, ascending, exactly 16 per f.
- Same generated blocks, graph seeds, frozen rows/mothers and corrected
  per-Bob-column concentration Model-F semantics as accepted D7-C/D7-E:
  n=64; L1 rows 49 (f=1.0) / 59 (f=1.2); L2 rows 43 (f=1.0) / 52 (f=1.2);
  D5-native mothers `build_dv3_nested_support(64, 64, 49, 2026090501)` +
  `assign_gf32_coefficients(sup, 2026090501, None, 64)` (L1) and
  `build_dv3_nested_support(64, 64, 43, 2026090502)` +
  `assign_gf32_coefficients(sup, 2026090502, None, 64)` (L2); accepted
  Model-F root `workspace/v72p2d5_model_f_input/20260907_r1`.
- Row-layered only: GF(32) poly 37, cold start, `max_iter=90`, damping
  `1.0`.
- No oracle, no flooding, no CAL/VAL, no real/raw, no graph/mother
  changes.

### B02 — paired arms

For every `(f, seed)` execute arms in this exact order:

```text
FORWARD_L1_TO_L2:  decode L1 marginal
                   -> gate -> transient P(U2|B,s1) -> cold decode L2
REVERSE_L2_TO_L1:  decode L2 marginal
                   -> gate -> transient P(U1|B,s2) -> cold decode L1
```

Gate: source status finite/non-crash, belief shape valid, provenance
exactly `CHECK_UPDATED`. Source exact is NOT a gate. An ineligible second
stage is a blocked non-call, never replaced. No transfer back to the
source layer. Maximum `32×4=128` calls (64 mandatory source marginals +
up to 64 gated transfers).

### Transfer formulas and estimator identity

Let the accepted corrected joint model be `P(U1,U2|B=b)` and the source
BP APP approximation be normalized `q` from a `CHECK_UPDATED` log belief.

- Forward: `P_transfer(U2|B,s1) = sum_u1 q1(u1|B,s1) P(U2|B,u1)`.
- Reverse: `P_transfer(U1|B,s2) = sum_u2 q2(u2|B,s2) P(U1|B,u2)`.

Estimator identity is a hard pre-execution contract. D7-F must obtain the
joint only through `prepare_model_f_prior_candidate` /
`build_f_model_concentration`, whose per-Bob-column smoothing is
`(counts[:,b] + lambda*p_global)/(n_b[b] + lambda)`. The historical
`build_f_model` rule `counts + lambda` per cell is forbidden. Static and
behavioral tests must fail if D7-F references that legacy builder, and a
tiny asymmetric table must distinguish the two formulas numerically.

Floor/renormalize exactly as the accepted D5 helper contract. The source
q is transient and never persisted. No source truth enters either
formula.

### B03 — outcome accounting

For each arm persist scalar-only: first/second stage eligibility and
provenance; L1 exact/syndrome and L2 exact/syndrome separately;
`both_layers_exact = L1_exact AND L2_exact` only; calls, blocked,
crash/nonfinite, iterations/work, wall, RSS. Never merge syndrome success
into exact success.

### B04 — evidence-use contract

Each target starts cold from the transfer prior and consumes its own
syndrome once. No target posterior is fed back, blended, multiplied, or
reused. Tests must prove the first-stage syndrome is consumed only by its
source decoder and the second-stage syndrome only by its target decoder.
>2-stage alternating stays blocked pending a cavity/extrinsic-message
contract capable of excluding returned syndrome evidence; D7-F encodes no
such contract.

## 3. Frozen labels, terminal and budgets (§5 B05–B07)

### B05 — paired labels per f (first match)

Across the same 16 seeds compare reverse candidate C with forward
reference R (`candidate_only`: C both-exact and R not; `reference_only`:
R both-exact and C not; `both`; `neither`):

1. `COVERAGE_BLOCKED` if either arm has fewer than 12/16 complete
   eligible paired outcomes;
2. `REVERSE_REGRESSION` if `reference_only >= 2` and
   `candidate_only == 0`;
3. `STRONG_REVERSE_LIFT` if `candidate_only >= 4` and
   `reference_only == 0`;
4. `WEAK_REVERSE_LIFT` if `candidate_only > reference_only` but strong is
   not met;
5. `NO_REVERSE_LIFT` otherwise.

Synthetic diagnostic labels, not FER thresholds.

### B06 — run terminal priority (first applicable)

1. `D7_F_PRE_EXECUTION_BLOCKED`
2. `D7_F_WATCHDOG_TIMEOUT_VOID`
3. `D7_F_NONFINITE_OR_CRASH_BLOCKED`
4. `D7_F_RESOURCE_OVERRUN`
5. `D7_F_INCOMPLETE_MATRIX_BLOCKED`
6. `D7_F_PROVENANCE_COVERAGE_BLOCKED`
7. `D7_F_REVERSE_ORDER_STRONG_LIFT` — either f is strong and the other
   does not regress
8. `D7_F_REVERSE_ORDER_WEAK_LIFT` — either f is weak and neither regresses
9. `D7_F_REVERSE_ORDER_REGRESSION`
10. `D7_F_NO_USEFUL_REVERSE_ORDER_LIFT`

No automatic successor is encoded.

### B07 — budgets

- Hard cap 128 decoder calls; no concurrency/retry/rerun/resume.
- Per-call watchdog 120 s.
- Stored scientific wall <=1500 s.
- Outer GNU timeout `1800` plus `-k 30`.
- `.venv/bin/python` only.
- On Linux/WSL, current-process peak RSS from `/proc/self/status` field
  `VmHWM` (unit exactly `kB`, `bytes = value * 1024`), strict `< 2 GiB`,
  fail-closed (missing/unparseable blocks before the first scientific
  call and at the first affected call mid-run).
- Sequential execution only; one fresh identifier; no
  overwrite/retry/resume.
- Target fresh direct child
  `workspace/d7_f_reverse_order_discriminator_<uuid>/`, no
  overwrite/subdirs; exactly seven scalar text files plus an independent
  read-only verifier.

## 4. Exact future WSL command (frozen, NOT run in this task)

```bash
timeout -k 30 1800 .venv/bin/python scripts/v72p2d7_gf32_reverse_order_discriminator.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_f_reverse_order_discriminator_<uuid>
```

- Status `NOT_AUTHORIZED`: frozen but unauthorized and not executed; no
  identifier generated here.
- Operational precondition: cwd is the repository root;
  `.venv/bin/python` is executable (`test -x .venv/bin/python`) and
  imports the project dependencies (`.venv/bin/python -c "import numpy,
  pytest; print(numpy.__version__)"`). Do not activate another venv, use
  bare `python`/`python3`, add `PYTHONPATH`, or alter child argv through
  a wrapper. GNU timeout and every scientific parameter remain unchanged.
- `<uuid>` is a fresh identifier for the one future authorized invocation
  (generated only at authorization time, not here). The outer `timeout`
  is GNU coreutils `timeout`, `-k 30` kill grace, `1800` wall seconds.
- `--model-f-root` must resolve to exactly
  `workspace/v72p2d5_model_f_input/20260907_r1`; any other value refuses
  (`D7_F_PRE_EXECUTION_BLOCKED`) before decoder bind, Model-F read or
  root creation.
- `--out-root` must be a fresh direct child of `workspace/` named
  `d7_f_reverse_order_discriminator_<uuid>`; must not exist; the writer
  refuses overwrite and refuses subdirectories.
- This command was NOT run to produce this freeze; no D7-F root exists.

## 5. Root contract and seven-file schema

Future root `workspace/d7_f_reverse_order_discriminator_<uuid>/`: fresh,
no-overwrite, no subdirectories, exactly seven compact scalar text files:

- `manifest.json`
- `decoder_records.csv`
- `arm_pairs.csv`
- `stratum_summary.csv`
- `summary.json`
- `report.md`
- `command_log.txt`

Schema: `decoder_records.csv` holds the 64 mandatory source-marginal rows
plus only the invoked eligible second-stage rows (blocked stages recorded
as non-invocations elsewhere, never fabricated); `arm_pairs.csv` holds
one row per eligible forward/reverse arm pair per `(f,seed)` with
shared-identity pins (f/seed/block/H/syndrome/decoder config) and
per-arm eligibility/provenance plus L1/L2 exact/syndrome and
`both_layers_exact` columns; `stratum_summary.csv` holds 2 rows (one per
f) with eligible/blocked counts, `candidate_only`/`reference_only`/
`both`/`neither` counts, and `stratum_label`; `manifest.json` holds
frozen run identities, model-root file names/sizes, estimator ID, lambda,
n, f/rows/seeds, graph seeds, arm/slot order, decoder ID/kwargs, budgets,
seven-file list, terminal priority, and run-time
identifier/UTC/PID/authorization-consumed markers; `summary.json` holds
the terminal, two stratum labels, totals, stored wall, peak RSS, and
retries/reruns/resumes = 0; `report.md` holds a compact scalar summary
only; `command_log.txt` holds the exact command, start/end, and scalar
checkpoints.

Writer/verifier split: the verifier reads only the seven files and
independently recomputes arm order, mandatory 64 calls, eligible
second-stage invocation count, uniqueness, no replacement, pair identity,
provenance gate, exact/syndrome isolation, `both_layers_exact` AND rule,
syndrome single-consumption, two labels, terminal, wall/RSS and schema;
it never calls a decoder and never loads Model-F.

Persist no beliefs, priors, symbols, syndromes, block vectors or digests;
all `belief_*`-style fields, if any, are scalars only.

## 6. Test plan (later gate — recorded here, not executed)

At minimum the later implementation SHALL cover (packet §7):

- exact 128-call matrix/order and cap;
- arm transitions and blocked non-calls;
- source exact not an eligibility gate;
- only exact `CHECK_UPDATED` transfers;
- each syndrome consumed once, no target feedback;
- both-layer exact truth table and syndrome isolation;
- paired-label boundaries and terminal priority;
- RSS boundaries/fail-closed behavior;
- scalar-only schema/forbidden payloads;
- writer/verifier tamper cases;
- protected-root/no-overwrite refusal;
- external-cwd decoder/loader sentinel;
- dry-run and unauthorized refusal;
- D7-E/BP provenance regression.

Focused tests plus one milestone regression; no perf-v38 or scientific
decoder. Zero real decoder; tiny explicit in-memory fixtures/fakes and
task-owned fresh basetemps only.

## 7. Mandatory reviews and Pre-RESULT gate (later gates)

- Independent implementation review must PASS
  (`D7_F_IMPLEMENTATION_REVIEW_PASS`) in
  `D7_F_IMPLEMENTATION_REVIEW_R1.md` after implementation; checks
  identity, evidence-use/no-feedback proof, state machine, pairing,
  labels, terminals, resources, schema, verifier, lazy binding, and
  scope. FAIL variant: `D7_F_IMPLEMENTATION_REVIEW_FAIL`.
- Independent WSL Pre-EXECUTE review must PASS
  (`D7_F_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`) in
  `D7_F_PRE_EXECUTE_REVIEW_R1.md`: implementation review PASS, matrix,
  exact future command, target absence, venv-on-PATH, GNU timeout, VmHWM
  RSS, unauthorized refusal, dry-run, external-cwd decoder plus Model-F
  loader sentinels, tests, protected roots and all authorization false.
  It grants nothing.
- Before any `OPERATOR_RETURN.md` / `RESULT_SUMMARY.md` / `run_01`
  solidification or publication, an independent reviewer must re-check the
  frozen thresholds, leakage-formula decomposition, `undetected` isolation
  discipline, per-source breakdown, disclosure accounting and
  plan-specified semantics against the actual seven files. Issues trigger
  immediate rework; no publish-then-patch. A FAIL blocks solidification.
- Planned code paths (frozen names): module
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_reverse_order_discriminator.py`,
  tests
  `comparison_bench/tests/test_v72p2d7_gf32_reverse_order_discriminator.py`,
  script `scripts/v72p2d7_gf32_reverse_order_discriminator.py`; reuse D7-E
  loaders/estimator/transfer/provenance/RSS/scalar/verifier conventions
  via narrow imports, no predecessor-module copies; lazy binding + DI
  required.

## 8. Authorization lifecycle

- State file
  `docs/research_cycles/V72P2D7-GF32-REVERSE-ORDER-DISCRIMINATOR/cycle_state.yaml`
  holds all execution authorization and promotion fields false
  (`decoder_executed: false`, `result_created: false`); no identifier, no
  root.
- The future runner reads only this state file and refuses before any
  work, Model-F read, decoder bind or root creation while the key is
  false.
- A future verbatim user authorization flips the key for exactly one
  identifier and is consumed on the first decoder attempt regardless of
  outcome. No retry, rerun, resume or reuse. Import, `--help`,
  `--dry-run` and unauthorized runs bind no decoder, read no Model-F and
  create no root.
- `--dry-run` prints the frozen 128-slot arm order (64 mandatory + gated
  second-stage rule) and exits without binding.
- Explicit future authorization is required; none is granted by this
  prereg.

## 9. Nonclaim boundaries

Paired order classifications are route discriminators, not FER estimates.
The D7-C oracle ceiling remains a counterfactual diagnostic only; it is
not protocol recovery, does not count oracle truth as disclosure, and
supports no FER, leakage, reconciliation-efficiency, key-rate,
CAL/real-data, qualification, promotion, R1d, G1/G2 or general
GF32/NB-LDPC claim. No result of D7-F may be described as a performance
estimate of either order. D7-E acceptance facts above are the only reused
claims. No alternating-convergence claim is supported; >2-stage
alternating stays blocked pending a cavity/extrinsic-message contract.

## 10. Freeze statement

This prereg froze every callable, constant, seed, row, formula, order,
budget, threshold, terminal and label rule above at HEAD `f4c06042`,
before any real D7-F artifact or decoder observation. Implementation and
readiness may follow only after the scoped commit of this prereg. All
authorizations are false; no identifier exists; no
`workspace/d7_f_reverse_order_discriminator_*` root exists.
