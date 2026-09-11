# D7-E execution packet R1 (frozen; NOT authorized, NOT executed)

- Plan revision `R1`; prereg `D7_E_PREREG_R1.md` (committed before any real
  artifact/decoder observation).
- Status: the command below is **frozen but unauthorized and not executed**.
  No identifier was generated, no
  `workspace/d7_e_cross_layer_discriminator_*` root exists, no decoder was
  called, no Model-F binary content was read. All authorization fields are
  false. Overall cycle status: `NOT_AUTHORIZED_NOT_EXECUTED`.
- Governance structure: readiness requires independent implementation
  review PASS (R18) and independent Pre-EXECUTE review PASS (R19); a future
  scientific execution additionally requires explicit verbatim
  authorization of the key below (one-shot). Pre-RESULT review is
  mandatory before any result publication.

## Exact future WSL command (do not run in this task)

```bash
timeout -k 30 1800 .venv/bin/python scripts/v72p2d7_gf32_cross_layer_discriminator.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_e_cross_layer_discriminator_<uuid>
```

- Operational precondition: cwd is the repository root; `.venv/bin/python`
  is executable (`test -x .venv/bin/python`) and imports the project
  dependencies (`.venv/bin/python -c "import numpy, pytest;
  print(numpy.__version__)"`). Do not activate another venv, use bare
  `python`/`python3`, add `PYTHONPATH`, or alter child argv through a
  wrapper. GNU timeout and every scientific parameter remain unchanged.

- `<uuid>` is a fresh identifier for the one authorized invocation
  (generated only at authorization time, not here). The outer `timeout` is
  GNU coreutils `timeout`, `-k 30` kill grace, `1800` wall seconds.
- `--model-f-root` must resolve to exactly
  `workspace/v72p2d5_model_f_input/20260907_r1`; any other value refuses
  (`D7_E_PRE_EXECUTION_BLOCKED`) before decoder bind, Model-F read or root
  creation.
- `--out-root` must be a fresh direct child of `workspace/` named
  `d7_e_cross_layer_discriminator_<uuid>`; must not exist; the writer
  refuses overwrite and refuses subdirectories.

## Frozen question (§3 in substance)

On the exact D7-C frozen identities, can one provenance-valid single-pass
source-layer BP belief improve target-layer exact recovery over the target
marginal control, in either direction, without oracle truth or feedback?
One-pass mechanism only (source marginal decode, require `CHECK_UPDATED`,
softmax current log belief as BP APP approximation, combine with the
accepted joint Model-F conditional, one cold target decode). No calibrated
posterior, no alternating, no leakage/recovery/FER claims.

## Frozen matrix (R08 in substance)

f `[1.0, 1.2]`; seeds `2026091300..2026091315` ascending (16/f); same
blocks/graph seeds/rows/mothers/estimator as D7-C/D7-D (n=64; L1 rows
49/59; L2 rows 43/52; D5-native mothers with graph seeds 2026090501/2026090502;
accepted Model-F root above); row-layered only GF(32) poly 37 cold
`max_iter=90` damping `1.0`; directions `[L1_TO_L2, L2_TO_L1]`; no
flooding; no oracle decoder calls (D7-C tables are contextual ceiling
only).

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
64 provenance-eligible transfer calls. Blocked = recorded non-invocation,
never replacement/retry/fake.

## Frozen formulas and eligibility (R09–R10 in substance)

- `P_transfer(U2|B,s1) = sum_u1 q1(u1|B,s1) P(U2|B,u1)` (L1 to L2);
  `P_transfer(U1|B,s2) = sum_u2 q2(u2|B,s2) P(U1|B,u2)` (L2 to L1); `q`
  transient normalized source belief from a `CHECK_UPDATED` return.
- Estimator identity hard contract: only
  `prepare_model_f_prior_candidate` / `build_f_model_concentration` with
  per-Bob-column smoothing `(counts[:,b] + lambda*p_global)/(n_b[b] +
  lambda)`; legacy per-cell `build_f_model(counts + lambda)` forbidden
  (static + behavioral negative tests required). Floor/renorm per accepted
  D5 helper contract; source q transient, never persisted; no source truth
  in formulas.
- Control/transfer share f/seed/block/target H/syndrome/decoder config,
  only prior differs; source exactness does not gate; eligibility =
  finite/non-crash + valid shape + provenance exactly `CHECK_UPDATED`;
  at least 12/16 eligible per `(f,direction)` stratum for a mechanism label
  else `PROVENANCE_COVERAGE_BLOCKED`, no substitution.

## Frozen labels, terminal, budgets (R11–R13 in substance)

- Labels (first match): `STRONG_TRANSFER_LIFT` (eligible >=12,
  transfer-only >=4, control-only <=1, transfer exact >=4, zero
  crash/nonfinite); `TRANSFER_REGRESSION` (eligible >=12, control-only
  >=4, transfer-only <=1); `NO_TRANSFER_RECOVERY` (eligible >=12, transfer
  exact <=1 and control exact <=1); `CONTROL_ALREADY_RECOVERS`
  (eligible >=12 and control exact >=12); `AMBIGUOUS_TRANSFER_EFFECT`
  (every other complete finite eligible case); empty label when eligible
  <12. Threshold `4/16` reuses D7-C's routing threshold as a mechanism
  gate.
- Terminal (first applicable): `D7_E_PRE_EXECUTION_BLOCKED`,
  `D7_E_WATCHDOG_TIMEOUT_VOID`, `D7_E_NONFINITE_OR_CRASH_BLOCKED`,
  `D7_E_RESOURCE_OVERRUN`, `D7_E_INCOMPLETE_CORE_CALL_MATRIX`,
  `D7_E_PROVENANCE_COVERAGE_BLOCKED`,
  `D7_E_BIDIRECTIONAL_TRANSFER_LIFT`,
  `D7_E_L1_TO_L2_TRANSFER_LIFT`, `D7_E_L2_TO_L1_TRANSFER_LIFT`,
  `D7_E_TRANSFER_REGRESSION`, `D7_E_NO_USEFUL_TRANSFER_RECOVERY`,
  `D7_E_MIXED_TRANSFER_DIAGNOSTIC`. Strata + blocked counts persist under
  higher terminal.
- Budgets: hard cap 192; no concurrency/retry/rerun/resume; per-call
  watchdog 120 s; stored wall <=1500 s; outer `1800` + `-k 30`; stdlib
  `resource` RSS finite positive `<2GiB` pre-first-call and max; fresh
  direct-child out-root, no overwrite/subdirs.

## Preflight and frozen call order

Preflight (before the first scientific call, fail-closed as
`D7_E_PRE_EXECUTION_BLOCKED`): cycle-state key true for this one
identifier; `--model-f-root` exactly the accepted root and valid when
loaded; out-root a fresh direct child of `workspace/` named
`d7_e_cross_layer_discriminator_<uuid>` and absent; stdlib RSS measurement
finite, positive and `< 2 GiB`; frozen identities built in memory. Any
failure stops with zero scientific calls.

Call order (exact, 192 scheduled slots, 128 mandatory + up to 64 eligible
transfers): f `[1.0, 1.2]` outer, seeds `2026091300..2026091315`
ascending, six slots per `(f,seed)` in the order above. No early stop
across identities; each decoder retains its own normal internal stopping;
no retry/rerun/resume/concurrency; blocked transfers are non-invocations.

## Authorization lifecycle

- State file
  `docs/research_cycles/V72P2D7-GF32-CROSS-LAYER-DISCRIMINATOR/cycle_state.yaml`
  holds all execution authorization false (`decoder_executed: false`,
  `result_created: false`; all other authorization flags false).
- The runner reads only this state file and refuses before any work,
  Model-F read, decoder bind or root creation while the key is false.
- A future verbatim user authorization flips the key for exactly one
  identifier and is consumed on the first decoder attempt regardless of
  outcome. No retry, rerun, resume or reuse. Import, `--help`, `--dry-run`
  and unauthorized runs bind no decoder, read no Model-F and create no
  root.
- `--dry-run` prints the frozen 192-slot order (128 mandatory + eligible
  transfer rule) and exits without binding.
- Explicit future authorization is required; none is granted by this
  packet.

## Budgets / stop rules (frozen)

- 128 mandatory calls on normal completion plus only invoked eligible
  transfers (at most 64); hard cap 192; no early success stop; no
  replacement cell.
- Per-call watchdog 120 s; stored scientific wall `<= 1500 s`; outer GNU
  timeout `1800 s` + 30 s kill grace.
- Current-process WSL RSS via stdlib
  `resource.getrusage(RUSAGE_SELF).ru_maxrss` with explicit KiB→bytes
  conversion; finite positive measurement required **before the first
  call**; RSS `< 2 GiB`; no psutil.
- Zero retry/rerun/resume/concurrency; sequential execution only.
- Terminal priority T1–T12 exactly as above; all four stratum labels and
  blocked counts recorded even under a higher-priority run terminal.
- Preflight failures (target exists, RSS unavailable/nonpositive, Model-F
  absent/invalid, root mismatch) block before any call
  (`D7_E_PRE_EXECUTION_BLOCKED`).

## Root contract

`workspace/d7_e_cross_layer_discriminator_<uuid>/` fresh, no
subdirectories, exactly seven compact scalar text files:

- `manifest.json`
- `decoder_records.csv`
- `transfer_pairs.csv`
- `stratum_summary.csv`
- `summary.json`
- `report.md`
- `command_log.txt`

Schema and evidence fields are frozen in prereg §5. No raw beliefs,
symbols, priors, syndromes, block vectors or digests are persisted. Verify
mode reads only the seven files and independently recomputes slot order,
mandatory calls, eligible invocation count, uniqueness, no replacement,
pair identity, provenance gate, exact/syndrome isolation, four labels,
terminal, wall/RSS and schema; it never calls a decoder and never loads
Model-F.

## Verify contract

- `decoder_records.csv` must contain exactly the 128 mandatory rows plus
  one row per invoked eligible transfer, with unique slot identity and the
  frozen slot at each position.
- `transfer_pairs.csv` must contain one row per eligible pair whose
  control/transfer records share all non-prior inputs; paired counts must
  recompute from the call rows; syndrome-only analogues stay separate from
  exact.
- `stratum_summary.csv` must contain exactly 4 rows; each label must
  recompute from the frozen first-match rules and be empty only for a
  coverage-blocked stratum.
- `summary.json` terminal must recompute from the frozen priority list.
- Missing, duplicate, unpaired or tampered scalars fail verify with the
  affected identity/field.

## Mandatory reviews and Pre-RESULT gate

- Independent implementation review must PASS
  (`D7_E_IMPLEMENTATION_REVIEW_PASS`): formulas, provenance, pairing,
  thresholds, no double-counting, no oracle truth, terminal, schema and
  all tests.
- Independent WSL Pre-EXECUTE review must PASS
  (`D7_E_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`): exact
  192-slot matrix, Model-F metadata only, dual decoder sentinel
  reachability, RSS units, GNU timeout rehearsal if the environment
  changed, target absence, unauthorized refusal, tests, protected roots
  and the exact future command.
- Before any `OPERATOR_RETURN.md` / `RESULT_SUMMARY.md` / `run_01`
  solidification or publication, an independent reviewer must re-check the
  frozen thresholds, leakage-formula decomposition, `undetected` isolation
  discipline, per-source breakdown, disclosure accounting and
  plan-specified semantics against the actual seven files. Issues trigger
  immediate rework; no publish-then-patch. A FAIL blocks solidification.

## Boundaries

- Zero D7-E scientific calls and zero Model-F binary content reads until a
  future explicitly authorized execution; protected roots are inspected by
  names/sizes/mtime only.
- Zero CAL/VAL/parquet/raw/real/data reads; zero `--phase`; zero R1d/G1/G2;
  zero production v35/D5/D6/D7-A/D7-B/D7-C/D7-D edits; zero interface-rework
  implementation; zero identifier; zero push.
- Predecessor roots immutable: accepted D7-C root, D7-B R2 root, Model-F,
  G0/P0/G1, D6, structure and VOID roots.
- This packet authorizes no execution and no result acceptance. Next gate:
  `D7_E_IMPLEMENTATION_PENDING`; the final
  `D7_E_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION` value is set only at
  closeout after both independent reviews PASS.
