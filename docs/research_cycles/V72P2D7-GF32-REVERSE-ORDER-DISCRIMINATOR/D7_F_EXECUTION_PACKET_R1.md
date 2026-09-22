# D7-F execution packet R1 (frozen; NOT authorized, NOT executed)

- Plan revision `R1`; prereg `D7_F_PREREG_R1.md` (committed before any real
  artifact/decoder observation).
- Status: the command below is **frozen but unauthorized and not executed**.
  No identifier was generated, no
  `workspace/d7_f_reverse_order_discriminator_*` root exists, no decoder
  was called, no Model-F binary content was read. All authorization fields
  are false. Overall cycle status: `NOT_AUTHORIZED_NOT_EXECUTED`.
- Governance structure: readiness requires independent implementation
  review PASS and independent Pre-EXECUTE review PASS; a future scientific
  execution additionally requires explicit verbatim authorization of the
  key below (one-shot). Pre-RESULT review is mandatory before any result
  publication.

## Exact future WSL command (do not run in this task)

```bash
timeout -k 30 1800 .venv/bin/python scripts/v72p2d7_gf32_reverse_order_discriminator.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_f_reverse_order_discriminator_<uuid>
```

- Status `NOT_AUTHORIZED`.
- Operational precondition: cwd is the repository root;
  `.venv/bin/python` is executable (`test -x .venv/bin/python`) and
  imports the project dependencies (`.venv/bin/python -c "import numpy,
  pytest; print(numpy.__version__)"`). Do not activate another venv, use
  bare `python`/`python3`, add `PYTHONPATH`, or alter child argv through
  a wrapper. GNU timeout and every scientific parameter remain unchanged.
- `<uuid>` is a fresh identifier for the one authorized invocation
  (generated only at authorization time, not here). The outer `timeout`
  is GNU coreutils `timeout`, `-k 30` kill grace, `1800` wall seconds.
- `--model-f-root` must resolve to exactly
  `workspace/v72p2d5_model_f_input/20260907_r1`; any other value refuses
  (`D7_F_PRE_EXECUTION_BLOCKED`) before decoder bind, Model-F read or
  root creation.
- `--out-root` must be a fresh direct child of `workspace/` named
  `d7_f_reverse_order_discriminator_<uuid>`; must not exist; the writer
  refuses overwrite and refuses subdirectories.

## Frozen question (§5 in substance)

On the exact D7-E frozen identities, does reverse order `L2→L1` recover
both layers exactly on more seeds than forward order `L1→L2`, when each
arm is a complete two-pass sequence (source marginal, then one gated cold
target decode from the transfer prior), without oracle truth or feedback?
Paired order mechanism only. No calibrated posterior, no alternating, no
leakage/recovery/FER claims.

## Frozen matrix (B01 in substance)

f `[1.0, 1.2]`; seeds `2026091300..2026091315` ascending (16/f); same
corrected per-Bob-column estimator, accepted Model-F root above, D7-C/D7-E
block identity, H/mother prefixes, rows (n=64; L1 rows 49/59; L2 rows
43/52; D5-native mothers with graph seeds 2026090501/2026090502), GF32
poly 37, cold row-layered `max_iter=90` damping `1.0`; no
oracle/flooding/CAL/VAL/real/raw/graph changes.

Per `(f, seed)` exact arm order:

```text
FORWARD_L1_TO_L2:  decode L1 marginal
                   -> gate -> transient P(U2|B,s1) -> cold decode L2
REVERSE_L2_TO_L1:  decode L2 marginal
                   -> gate -> transient P(U1|B,s2) -> cold decode L1
```

128 scheduled slots maximum: 64 mandatory source marginals plus up to 64
gated second-stage transfers. Blocked = recorded non-invocation, never
replacement/retry/fake. No transfer back to the source layer.

## Frozen formulas, gate, accounting, evidence-use (B02–B04 in substance)

- `P_transfer(U2|B,s1) = sum_u1 q1(u1|B,s1) P(U2|B,u1)` (forward);
  `P_transfer(U1|B,s2) = sum_u2 q2(u2|B,s2) P(U1|B,u2)` (reverse); `q`
  transient normalized source belief from a `CHECK_UPDATED` return.
- Estimator identity hard contract: only
  `prepare_model_f_prior_candidate` / `build_f_model_concentration` with
  per-Bob-column smoothing `(counts[:,b] + lambda*p_global)/(n_b[b] +
  lambda)`; legacy per-cell `build_f_model(counts + lambda)` forbidden
  (static + behavioral negative tests required). Floor/renorm per accepted
  D5 helper contract; source q transient, never persisted; no source truth
  in formulas.
- Gate = finite/non-crash + valid shape + provenance exactly
  `CHECK_UPDATED`; source exactness does not gate.
- Per-arm scalar accounting: eligibility+provenance; L1 exact/syndrome and
  L2 exact/syndrome separately; `both_layers_exact` = AND only; calls/
  blocked/crash/nonfinite/iterations/work/wall/RSS. Never merge syndrome
  into exact.
- Evidence-use: each target starts cold from the transfer prior and
  consumes its own syndrome once; no posterior fed back/blended/
  multiplied/reused; tests prove first-stage syndrome consumed only by
  source decoder and second-stage only by target; >2-stage alternating
  stays blocked pending a cavity/extrinsic-message contract.

## Frozen labels, terminal, budgets (B05–B07 in substance)

- Paired labels per f over the same 16 seeds (`candidate_only`/
  `reference_only`/`both`/`neither`; first match): `COVERAGE_BLOCKED`
  (either arm <12/16 complete eligible); `REVERSE_REGRESSION`
  (`reference_only >= 2` and `candidate_only == 0`);
  `STRONG_REVERSE_LIFT` (`candidate_only >= 4` and `reference_only == 0`);
  `WEAK_REVERSE_LIFT` (`candidate_only > reference_only` but strong not
  met); `NO_REVERSE_LIFT` otherwise. Diagnostic labels, not FER.
- Terminal (first applicable): `D7_F_PRE_EXECUTION_BLOCKED`,
  `D7_F_WATCHDOG_TIMEOUT_VOID`, `D7_F_NONFINITE_OR_CRASH_BLOCKED`,
  `D7_F_RESOURCE_OVERRUN`, `D7_F_INCOMPLETE_MATRIX_BLOCKED`,
  `D7_F_PROVENANCE_COVERAGE_BLOCKED`,
  `D7_F_REVERSE_ORDER_STRONG_LIFT`,
  `D7_F_REVERSE_ORDER_WEAK_LIFT`, `D7_F_REVERSE_ORDER_REGRESSION`,
  `D7_F_NO_USEFUL_REVERSE_ORDER_LIFT`. No automatic successor. Paired
  outcomes + blocked counts persist under higher terminal.
- Budgets: hard cap 128; no concurrency/retry/rerun/resume; per-call
  watchdog 120 s; stored wall <=1500 s; outer `1800` + `-k 30`;
  `.venv/bin/python` only; `/proc/self/status` `VmHWM` strict `< 2 GiB`
  fail-closed; sequential; one fresh identifier; fresh direct-child
  out-root, no overwrite/subdirs.

## Preflight and frozen call order

Preflight (before the first scientific call, fail-closed as
`D7_F_PRE_EXECUTION_BLOCKED`): cycle-state key true for this one
identifier; `--model-f-root` exactly the accepted root and valid when
loaded; out-root a fresh direct child of `workspace/` named
`d7_f_reverse_order_discriminator_<uuid>` and absent; VmHWM RSS
measurement finite, positive and `< 2 GiB`; frozen identities built in
memory. Any failure stops with zero scientific calls.

Call order (exact, at most 128 slots, 64 mandatory + up to 64 gated
second stages): f `[1.0, 1.2]` outer, seeds `2026091300..2026091315`
ascending, two arms per `(f,seed)` in the order above, two stages per
arm. No early stop across identities; each decoder retains its own normal
internal stopping; no retry/rerun/resume/concurrency; blocked second
stages are non-invocations.

## Authorization lifecycle

- State file
  `docs/research_cycles/V72P2D7-GF32-REVERSE-ORDER-DISCRIMINATOR/cycle_state.yaml`
  holds all execution authorization false (`decoder_executed: false`,
  `result_created: false`; all other authorization flags false).
- The runner reads only this state file and refuses before any work,
  Model-F read, decoder bind or root creation while the key is false.
- A future verbatim user authorization flips the key for exactly one
  identifier and is consumed on the first decoder attempt regardless of
  outcome. No retry, rerun, resume or reuse. Import, `--help`,
  `--dry-run` and unauthorized runs bind no decoder, read no Model-F and
  create no root.
- `--dry-run` prints the frozen 128-slot arm order (64 mandatory + gated
  second-stage rule) and exits without binding.
- Explicit future authorization is required; none is granted by this
  packet.

## Budgets / stop rules (frozen)

- 64 mandatory source-marginal calls on normal completion plus only
  invoked eligible second stages (at most 64); hard cap 128; no early
  success stop; no replacement cell.
- Per-call watchdog 120 s; stored scientific wall `<= 1500 s`; outer GNU
  timeout `1800 s` + 30 s kill grace.
- Current-process WSL peak RSS via `/proc/self/status` `VmHWM` with exact
  `kB`→bytes conversion (`bytes = value * 1024`); finite positive
  measurement required **before the first call**; strict `< 2 GiB`;
  missing/unparseable blocks fail-closed; no psutil.
- Zero retry/rerun/resume/concurrency; sequential execution only.
- Terminal priority exactly as above; all paired outcome counts and
  blocked counts recorded even under a higher-priority run terminal.
- Preflight failures (target exists, RSS unavailable/nonpositive, Model-F
  absent/invalid, root mismatch) block before any call
  (`D7_F_PRE_EXECUTION_BLOCKED`).

## Root contract

`workspace/d7_f_reverse_order_discriminator_<uuid>/` fresh, no
subdirectories, exactly seven compact scalar text files:

- `manifest.json`
- `decoder_records.csv`
- `arm_pairs.csv`
- `stratum_summary.csv`
- `summary.json`
- `report.md`
- `command_log.txt`

Schema and evidence fields are frozen in prereg §5. No raw beliefs,
symbols, priors, syndromes, block vectors or digests are persisted.
Verify mode reads only the seven files and independently recomputes arm
order, mandatory calls, eligible invocation count, uniqueness, no
replacement, pair identity, provenance gate, exact/syndrome isolation,
`both_layers_exact` AND rule, syndrome single-consumption, two labels,
terminal, wall/RSS and schema; it never calls a decoder and never loads
Model-F.

## Verify contract

- `decoder_records.csv` must contain exactly the 64 mandatory source rows
  plus one row per invoked eligible second stage, with unique slot
  identity and the frozen arm slot at each position.
- `arm_pairs.csv` must contain one row per eligible arm pair whose
  forward/reverse records share f/seed/block identity; paired counts must
  recompute from the call rows; syndrome-only analogues stay separate
  from exact; `both_layers_exact` recomputes as AND.
- `stratum_summary.csv` must contain exactly 2 rows (one per f); each
  label must recompute from the frozen first-match rules and be
  `COVERAGE_BLOCKED` only for a coverage-blocked stratum.
- `summary.json` terminal must recompute from the frozen priority list.
- Missing, duplicate, unpaired or tampered scalars fail verify with the
  affected identity/field.

## Mandatory reviews and Pre-RESULT gate

- Independent implementation review must PASS
  (`D7_F_IMPLEMENTATION_REVIEW_PASS`): identity, evidence-use/no-feedback
  proof, state machine, pairing, labels, terminals, resources, schema,
  verifier, lazy binding, and scope.
- Independent WSL Pre-EXECUTE review must PASS
  (`D7_F_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`): exact
  128-slot matrix, Model-F metadata only, decoder/loader sentinels, RSS
  units, GNU timeout rehearsal if the environment changed, target
  absence, unauthorized refusal, tests, protected roots and the exact
  future command.
- Before any `OPERATOR_RETURN.md` / `RESULT_SUMMARY.md` / `run_01`
  solidification or publication, an independent reviewer must re-check the
  frozen thresholds, leakage-formula decomposition, `undetected` isolation
  discipline, per-source breakdown, disclosure accounting and
  plan-specified semantics against the actual seven files. Issues trigger
  immediate rework; no publish-then-patch. A FAIL blocks solidification.

## Boundaries

- Zero D7-F scientific calls and zero Model-F binary content reads until
  a future explicitly authorized execution; protected roots are inspected
  by names/sizes/mtime only.
- Zero CAL/VAL/parquet/raw/real/data reads; zero `--phase`; zero R1d/G1/
  G2; zero production v35/D5/D6/D7-A/D7-B/D7-C/D7-D/D7-E edits; zero
  interface-rework implementation; zero identifier; zero push.
- Predecessor roots immutable: accepted D7-E root, D7-C root, D7-B R2
  root, Model-F, G0/P0/G1, D6, structure and VOID roots.
- This packet authorizes no execution and no result acceptance. Next gate:
  `D7_F_IMPLEMENTATION_PENDING`.
