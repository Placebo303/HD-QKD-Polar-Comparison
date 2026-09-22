# D7-E provenance-safe cross-layer discriminator preregistration R1 (frozen before any real artifact or decoder observation)

- Branch `formal-ir-v72p1-addendum-clean`; starting HEAD `da359ec5` (Track A
  commit 3, `docs(d6): record renewed optional R1d readiness review`).
  Provenance only; no remote-equality requirement.
- Packet binding:
  `.workbuddy/tasks/D7_E_CROSS_LAYER_READINESS_AND_D6_COMPAT_R1_TASK_PACKET.md`
  (R1) §§3–5 and §6/R14; this prereg is the Track B freeze under R14. R1
  binds fully.
- Status: `FROZEN_PREREG_R1` and `NOT_AUTHORIZED_NOT_EXECUTED`.
  **Observation ordering:** this prereg is committed (scoped docs/OpenSpec
  commit) before any real D7-E artifact or decoder observation. No D7-E
  decoder call, no Model-F binary content read, no output root, and no
  D7-E identifier exist at freeze time.
- Predecessor facts (immutable): D7-C accepted scope
  `D7_C_RESULT_ACCEPTED_BIDIRECTIONAL_DEPENDENCE_DIAGNOSTIC` (128/128
  frozen single-layer calls; f=1.2 strong oracle lift in both layers;
  contextual ceiling only); D7-D accepted scope
  `D7_D_RESULT_ACCEPTED_SCHEDULE_EFFECT_INCONCLUSIVE` (256/256 paired
  calls; no preregistered flooding advantage; row-layered exact 43/128 vs
  flooding 40/128); BP Alternative A is the current interface contract
  (`PRIOR_ONLY` / `CHECK_UPDATED` / `WARM_START_UNSPECIFIED`; only
  `CHECK_UPDATED` may feed a conditioned cross-layer APP); D7-C/D7-D do
  not consume cross-layer returned beliefs and remain valid; the accepted
  D7-B hard-decision result remains valid with its soft-belief limitation;
  the corrected concentration Model-F candidate is the only admissible
  D5–D7 estimator semantics; old per-cell lambda remains historical and
  unwired; D6 R1d is optional/paused, not a mainline gate. All
  authorization false. No `workspace/d7_e_cross_layer_discriminator_*`
  root exists.
- D7-E never constructs an oracle prior and never calls an oracle decoder.
  Accepted D7-C tables are a contextual ceiling only.

## 1. Frozen scientific question (§3, verbatim in substance)

Question: on the exact D7-C frozen identities, can one provenance-valid
single-pass source-layer BP belief improve target-layer exact recovery over
the target marginal control, in either direction, without oracle truth or
feedback?

This tests only a one-pass mechanism:

```text
source marginal decode
  -> require belief_provenance == CHECK_UPDATED
  -> softmax(current log belief) as BP APP approximation
  -> combine with accepted joint Model-F conditional for the target
  -> one cold target decode
```

It does not claim calibrated posterior, alternating convergence, leakage,
protocol recovery or Bob-only FER.

## 2. Frozen matrix and formulas (§4 / R08–R10)

### R08 — identities and decoder contract

- `f` order `[1.0, 1.2]`.
- Seeds `2026091300..2026091315`, ascending, exactly 16 per f.
- Same generated blocks, graph seeds, frozen rows/mothers and corrected
  concentration Model-F semantics as accepted D7-C/D7-D: n=64; L1 rows 49
  (f=1.0) / 59 (f=1.2); L2 rows 43 (f=1.0) / 52 (f=1.2); D5-native mothers
  `build_dv3_nested_support(64, 64, 49, 2026090501)` +
  `assign_gf32_coefficients(sup, 2026090501, None, 64)` (L1) and
  `build_dv3_nested_support(64, 64, 43, 2026090502)` +
  `assign_gf32_coefficients(sup, 2026090502, None, 64)` (L2); accepted
  Model-F root `workspace/v72p2d5_model_f_input/20260907_r1`.
- Row-layered only: poly 37, cold start, `max_iter=90`, damping `1.0`.
- Directions in order `[L1_TO_L2, L2_TO_L1]`.
- No flooding: D7-D established no preregistered flooding advantage.
- No oracle decoder calls: accepted D7-C tables are a contextual ceiling
  only.

Per `(f, seed)` exact slot order:

```text
L1_TO_L2_SOURCE_L1_MARGINAL
L1_TO_L2_TARGET_L2_CONTROL_MARGINAL
L1_TO_L2_TARGET_L2_TRANSFER       # invoked only if source CHECK_UPDATED
L2_TO_L1_SOURCE_L2_MARGINAL
L2_TO_L1_TARGET_L1_CONTROL_MARGINAL
L2_TO_L1_TARGET_L1_TRANSFER       # invoked only if source CHECK_UPDATED
```

192 scheduled slots: 128 mandatory source/control decoder calls plus up to
64 provenance-eligible transfer calls. A blocked transfer slot is a
recorded non-invocation, never replacement, retry or fake decoder result.

### R09 — transfer formulas

Let the accepted corrected joint model be `P(U1,U2|B=b)` and the source BP
APP approximation be normalized `q` from a `CHECK_UPDATED` log belief.

Estimator identity is a hard pre-execution contract, not an implementation
choice. D7-E must obtain it only through
`prepare_model_f_prior_candidate` / `build_f_model_concentration`, whose
per-Bob-column smoothing is
`(counts[:,b] + lambda*p_global) / (n_b[b] + lambda)`. The historical
`build_f_model` rule `counts + lambda` per cell is forbidden. Static and
behavioral tests must fail if D7-E references that legacy builder, and a
tiny asymmetric table must distinguish the two formulas numerically.

- L1 to L2:
  `P_transfer(U2|B,s1) = sum_u1 q1(u1|B,s1) P(U2|B,u1)`.
- L2 to L1:
  `P_transfer(U1|B,s2) = sum_u2 q2(u2|B,s2) P(U1|B,u2)`.

Floor/renormalize exactly as the accepted D5 helper contract. The source q
is transient and never persisted. No source truth enters either formula.

### R10 — pair and eligibility semantics

For each direction, the target control and transfer share f/seed/block/
target H/syndrome/decoder configuration; only the target prior differs.
Source exactness does not gate eligibility. Eligibility requires source
status finite/non-crash, belief shape valid and provenance exactly
`CHECK_UPDATED`.

Per `(f,direction)` stratum, at least 12/16 transfer slots must be eligible
for a mechanism label. Fewer gives `PROVENANCE_COVERAGE_BLOCKED`; no
denominator substitution or replacement seed.

## 3. Frozen labels, terminal and budgets (§5 / R11–R13)

### R11 — stratum labels (first match)

On eligible control/transfer pairs:

1. `STRONG_TRANSFER_LIFT`: eligible >=12, transfer-only >=4,
   control-only <=1, transfer exact >=4, zero crash/nonfinite.
2. `TRANSFER_REGRESSION`: eligible >=12, control-only >=4,
   transfer-only <=1.
3. `NO_TRANSFER_RECOVERY`: eligible >=12, transfer exact <=1 and control
   exact <=1.
4. `CONTROL_ALREADY_RECOVERS`: eligible >=12 and control exact >=12.
5. `AMBIGUOUS_TRANSFER_EFFECT`: every other complete finite eligible case.
6. Empty label when eligible <12; coverage status records the reason.

The threshold `4/16` deliberately reuses D7-C's frozen useful-lift routing
threshold. It is a mechanism gate, not a probability estimate.

### R12 — run terminal priority (first applicable)

1. `D7_E_PRE_EXECUTION_BLOCKED`
2. `D7_E_WATCHDOG_TIMEOUT_VOID`
3. `D7_E_NONFINITE_OR_CRASH_BLOCKED`
4. `D7_E_RESOURCE_OVERRUN`
5. `D7_E_INCOMPLETE_CORE_CALL_MATRIX`
6. `D7_E_PROVENANCE_COVERAGE_BLOCKED`
7. `D7_E_BIDIRECTIONAL_TRANSFER_LIFT` — same f has strong lift both
   directions
8. `D7_E_L1_TO_L2_TRANSFER_LIFT` — strong only L1 to L2
9. `D7_E_L2_TO_L1_TRANSFER_LIFT` — strong only L2 to L1
10. `D7_E_TRANSFER_REGRESSION` — any regression, no strong lift
11. `D7_E_NO_USEFUL_TRANSFER_RECOVERY` — all four strata no recovery
12. `D7_E_MIXED_TRANSFER_DIAGNOSTIC`

All four strata and blocked-slot counts persist under higher-priority
terminal.

### R13 — budgets

- Hard cap 192 decoder calls; no concurrency/retry/rerun/resume.
- Per-call watchdog 120 s.
- Stored scientific wall <=1500 s.
- Outer GNU timeout `1800` plus `-k 30`.
- WSL stdlib `resource` RSS finite positive and `<2GiB` before the first
  call and recorded maximum during run; no psutil.
- Target fresh direct child
  `workspace/d7_e_cross_layer_discriminator_<uuid>/`, no overwrite/subdirs.

## 4. Exact future WSL command (frozen, NOT run in this task)

```bash
timeout -k 30 1800 .venv/bin/python scripts/v72p2d7_gf32_cross_layer_discriminator.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_e_cross_layer_discriminator_<uuid>
```

- Operational precondition: cwd is the repository root; `.venv/bin/python`
  is executable (`test -x .venv/bin/python`) and imports the project
  dependencies (`.venv/bin/python -c "import numpy, pytest;
  print(numpy.__version__)"`). Do not activate another venv, use bare
  `python`/`python3`, add `PYTHONPATH`, or alter child argv through a
  wrapper. GNU timeout and every scientific parameter remain unchanged.

- `<uuid>` is a fresh identifier for the one future authorized invocation
  (generated only at authorization time, not here). The outer `timeout` is
  GNU coreutils `timeout`, `-k 30` kill grace, `1800` wall seconds.
- `--model-f-root` must resolve to exactly
  `workspace/v72p2d5_model_f_input/20260907_r1`; any other value refuses
  (`D7_E_PRE_EXECUTION_BLOCKED`) before decoder bind, Model-F read or root
  creation.
- `--out-root` must be a fresh direct child of `workspace/` named
  `d7_e_cross_layer_discriminator_<uuid>`; must not exist; the writer
  refuses overwrite and refuses subdirectories.
- This command was NOT run to produce this freeze; no D7-E root exists.

## 5. Root contract and seven-file schema

Future root `workspace/d7_e_cross_layer_discriminator_<uuid>/`: fresh,
no-overwrite, no subdirectories, exactly seven compact scalar text files:

- `manifest.json`
- `decoder_records.csv`
- `transfer_pairs.csv`
- `stratum_summary.csv`
- `summary.json`
- `report.md`
- `command_log.txt`

Schema: `decoder_records.csv` holds the mandatory 128 source/control rows
plus only the invoked eligible transfer rows (blocked slots recorded as
non-invocations elsewhere, never fabricated); `transfer_pairs.csv` holds
one row per eligible control/transfer pair with shared-identity pins;
`stratum_summary.csv` holds 4 rows (one per `(f,direction)` stratum) with
eligible/blocked counts and `stratum_label`; `manifest.json` holds frozen
run identities, model-root file names/sizes, estimator ID, lambda, n,
f/rows/seeds, graph seeds, direction/slot order, decoder ID/kwargs,
budgets, seven-file list, terminal priority, and run-time
identifier/UTC/PID/authorization-consumed markers; `summary.json` holds
the terminal, four stratum labels, totals, stored wall, peak RSS, and
retries/reruns/resumes = 0; `report.md` holds a compact scalar summary
only; `command_log.txt` holds the exact command, start/end, and scalar
checkpoints.

Writer/verifier split: the verifier reads only the seven files and
independently recomputes slot order, mandatory 128 calls, eligible
transfer invocation count, uniqueness, no replacement, pair identity,
provenance gate, exact/syndrome isolation, four labels, terminal, wall/RSS
and schema; it never calls a decoder and never loads Model-F.

Persist no beliefs, priors, symbols, syndromes, block vectors or digests;
all `belief_*`-style fields, if any, are scalars only.

## 6. Test plan (R17, later gate — recorded here, not executed)

At minimum the later implementation SHALL cover:

- exact 192-slot dry-run order and 128 mandatory calls;
- both transfer formulas against direct enumeration;
- corrected per-column concentration estimator identity, plus a negative
  fixture proving the legacy per-cell-lambda builder would differ and is
  never reached;
- `CHECK_UPDATED` allows exactly one transfer call;
- prior-only/missing/`None`/unknown/warm blocks before mixer/target
  decoder;
- source exact false remains eligible when provenance valid;
- fewer than 12 eligible yields coverage block;
- thresholds/boundaries and full terminal truth table;
- crash/nonfinite/resource/watchdog priority;
- scalar-only seven-file writer, no-overwrite and verifier tamper cases;
- external-cwd WSL import and exact decoder/loader sentinels;
- D7-C/D7-D import/behavior independence;
- no production artifact/root read from tests.

Focused tests plus affected BP/D7-A/B/C/D and D5 regression run in separate
groups; no broad suite that accidentally collects known historical run
roots. Zero real decoder; tiny explicit in-memory fixtures/fakes and
task-owned fresh basetemps only.

## 7. Mandatory reviews and Pre-RESULT gate (R18/R19, later gates)

- Independent implementation review (R18) must PASS
  (`D7_E_IMPLEMENTATION_REVIEW_PASS`) in `D7_E_IMPLEMENTATION_REVIEW_R1.md`
  after implementation; one scoped rework allowed; checks formulas,
  provenance, pairing, thresholds, no double-counting, no oracle truth,
  terminal, schema and all tests. FAIL variant:
  `D7_E_IMPLEMENTATION_REVIEW_FAIL`.
- Independent WSL Pre-EXECUTE review (R19) must PASS
  (`D7_E_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`) in
  `D7_E_PRE_EXECUTE_REVIEW_R1.md`: implementation review PASS, matrix,
  exact future command, target absence, venv-on-PATH, GNU timeout, stdlib
  RSS, unauthorized refusal, dry-run, external-cwd dual source/target
  decoder plus Model-F loader sentinels, tests, protected roots and all
  authorization false. It grants nothing.
- Before any `OPERATOR_RETURN.md` / `RESULT_SUMMARY.md` / `run_01`
  solidification or publication, an independent reviewer must re-check the
  frozen thresholds, leakage-formula decomposition, `undetected` isolation
  discipline, per-source breakdown, disclosure accounting and
  plan-specified semantics against the actual seven files. Issues trigger
  immediate rework; no publish-then-patch. A FAIL blocks solidification.

## 8. Authorization lifecycle

- State file
  `docs/research_cycles/V72P2D7-GF32-CROSS-LAYER-DISCRIMINATOR/cycle_state.yaml`
  holds all execution authorization and promotion fields false
  (`decoder_executed: false`, `result_created: false`); no identifier, no
  root.
- The future runner reads only this state file and refuses before any work,
  Model-F read, decoder bind or root creation while the key is false.
- A future verbatim user authorization flips the key for exactly one
  identifier and is consumed on the first decoder attempt regardless of
  outcome. No retry, rerun, resume or reuse. Import, `--help`, `--dry-run`
  and unauthorized runs bind no decoder, read no Model-F and create no
  root.
- `--dry-run` prints the frozen 192-slot order (128 mandatory + eligible
  transfer rule) and exits without binding.
- Explicit future authorization is required; none is granted by this
  prereg.

## 9. Nonclaim boundaries

Transfer classifications are route discriminators, not FER estimates. The
D7-C oracle ceiling remains a counterfactual diagnostic only; it is not
protocol recovery, does not count oracle truth as disclosure, and supports
no FER, leakage, reconciliation-efficiency, key-rate, CAL/real-data,
qualification, promotion, R1d, G1/G2 or general GF32/NB-LDPC claim. No
result of D7-E may be described as a performance estimate of either
direction. D7-C/D7-D/BP readiness facts above are the only reused claims.

## 10. Freeze statement

This prereg froze every callable, constant, seed, row, formula, order,
budget, threshold, terminal and label rule above at HEAD `da359ec5`,
before any real D7-E artifact or decoder observation. Implementation and
readiness may follow only after the scoped commit of this prereg. All
authorizations are false; no identifier exists; no
`workspace/d7_e_cross_layer_discriminator_*` root exists.
