# D7-H Alternating Discriminator Packet Freeze R1

> R1A1 revision (authority: `.workbuddy/tasks/D7_H_ALTERNATING_READINESS_R1A1_TASK_PACKET.md` §2): STAGE 0 is the only unconditionally mandatory call; STAGE 1/STAGE 2 are gated with downstream-cascade blocking; coverage counts complete three-stage chains; per-invocation designated-syndrome accounting is adopted; the R1A1 packet authorizes the corrected freeze commit only — implementation and execution remain unauthorized.

## 0. Objective

Freeze exactly one docs-only packet that preregisters the **smallest alternating
cross-layer discriminator** built on the certified D7-G code-factor extrinsic
contract.

This task creates only the frozen planning artifacts:

1. the packet pair (this file + `D7_H_ALTERNATING_DISCRIMINATOR_PACKET_FREEZE_R1_PROMPT.md`);
2. cycle directory `docs/research_cycles/V72P2D7-GF32-ALTERNATING-DISCRIMINATOR/`
   with `D7_H_PREREG_R1.md` and `cycle_state.yaml`;
3. OpenSpec change `v72p2d7-alternating-discriminator`;
4. one minimal linkage line in the D7-G
   `docs/research_cycles/V72P2D7-GF32-EXTRINSIC-CONTRACT/cycle_state.yaml`.

No decoder call, no Model-F/real read, no synthetic/formal/real execution, no
result, no promotion, no push. No commit is authorized by this freeze itself; the corrected-freeze commit is authorized separately by `.workbuddy/tasks/D7_H_ALTERNATING_READINESS_R1A1_TASK_PACKET.md`. End state:
`D7_H_FROZEN_NOT_AUTHORIZED_NOT_EXECUTED`.

## 1. Preconditions

- Branch `formal-ir-v72p1-addendum-clean`; basis HEAD `46141fcc`.
- D7-G state `D7_G_FROZEN_NOT_AUTHORIZED_NOT_EXECUTED`; contract review
  `D7_G_EXTRINSIC_CONTRACT_REVIEW_PASS` and integration-readiness review
  `D7_G_EXTRINSIC_INTEGRATION_READINESS_PASS` both present; D7-G
  `next_gate: D7_H_ALTERNATING_DISCRIMINATOR_PACKET_FREEZE`.
- Every D7-H candidate path absent; no `workspace/d7_h_*` root; no D7-H
  runner/identifier; all D7-G authorization fields false.
- Mismatch → STOP without repair.

## 2. Hard prohibitions

- No D7-G/D7-H/D5/D6/D7-A..F rerun, verify, or production/scientific run; no
  `--phase`; no R1d/G1/G2.
- No Model-F, CAL, VAL, real/raw, VOID content read.
- No implementation, no decoder bind, no output root, no UUID.
- No tuning of code/graph/rows/mother/estimator/damping/iterations/thresholds/
  schedule/seeds.
- Do not alter accepted result roots or the frozen baseline `src/`,
  `experiments/`, `tools/`.
- No push, broad stage, reset, checkout, clean, stash, rebase, amend, or
  out-of-scope edit.
- If any candidate file already exists, overlaps unrelated dirty work, or the
  accepted D7-G contract cannot uniquely determine the minimal schedule, STOP
  before writing and return one exact blocker.

## 3. Frozen scientific scope (main-thread ruling, verbatim in substance)

- D7-H packet freeze only: preregister the smallest alternating cross-layer
  discriminator on the certified `CHECK_EXTRINSIC` contract.
- Cold start; one forward code-extrinsic transfer then one backward transfer
  (the smallest schedule demonstrably required by the accepted contracts).
- Posterior back-transfer explicitly forbidden.
- Iteration-0 and warm-start ambiguity fail closed.
- Freeze code/graph/rows/estimator/damping/iterations/thresholds/schedule/
  seeds, terminal semantics, stop rules, and no-rerun/no-tuning rules before
  any future decoder call.
- D7-H ends in `FROZEN_NOT_AUTHORIZED_NOT_EXECUTED`.

## 4. Why the minimal schedule is uniquely determined

- D7-E (accepted) already invokes exactly **one** transfer per arm and warns
  that `>2-stage alternating stays blocked pending a cavity/extrinsic-message
  contract capable of excluding returned syndrome evidence` (D7-E prereg §9;
  D7-F prereg §2/B04 restates the same block).
- D7-G (accepted, certified) now supplies that contract: an explicit per-row
  code-factor extrinsic message `L_code_ext = L_post − log(p_in)`, in a
  dedicated provenance namespace, with the cavity property that the incoming
  prior (channel **and** cross-layer evidence) is removed from the outgoing
  message.
- Therefore the smallest alternating schedule that is no longer blocked is
  exactly **two transfers**: one forward `L1→L2`, then one backward `L2→L1`.
  No third transfer is implied by any accepted contract, and none is
  preregistered here.

## 5. Frozen arm schedule (per `(f, seed)`)

```text
STAGE 0  SOURCE_L1_MARGINAL            (only unconditional mandatory call; shared)
  cold row-layered decode of L1 from its own channel marginal
  -> require extrinsic_provenance == CHECK_EXTRINSIC  (gate)
     NO_CHECK_EVIDENCE (including iteration-0 hard/syndrome success) /
     WARM_START_UNSPECIFIED / None / missing / unknown / nonfinite /
     shape mismatch => blocked non-invocation; all downstream stages for that
     identity are blocked, never synthesized, replaced, retried, or resumed.
     Source hard exact is not an eligibility gate.

STAGE 1  FORWARD_L1_TO_L2              (gated on STAGE 0; reference endpoint)
  invoked only if STAGE 0 yields finite, shape-valid, non-crashed, exact CHECK_EXTRINSIC
  q1_ext = softmax(extrinsic_log_beliefs of STAGE 0)      # CHECK_EXTRINSIC only
  P_transfer(U2|B,s1) = sum_u1 q1_ext(u1|B,s1) P(U2|B,u1)
  cold row-layered decode of L2 from P_transfer(U2|B,s1)
  -> REFERENCE both_layers_exact = L1_exact AND L2_exact
     blocked STAGE 1 => blocked non-invocation cascading to STAGE 2

STAGE 2  BACKWARD_L2_TO_L1             (gated on STAGE 1; candidate endpoint)
  invoked only if STAGE 1 yields finite, shape-valid, non-crashed, exact CHECK_EXTRINSIC
  require L2.extrinsic_provenance == CHECK_EXTRINSIC   (same gate)
  q2_ext = softmax(extrinsic_log_beliefs of STAGE 1)       # CHECK_EXTRINSIC only
  P_transfer(U1|B,s2) = sum_u2 q2_ext(u2|B,s2) P(U1|B,u2)
  cold row-layered decode of L1_return from P_transfer(U1|B,s2)
  -> CANDIDATE both_layers_exact = L2_exact AND L1_return_exact
```

Call accounting: 1 unconditional mandatory call per identity (STAGE 0; 32
identities → minimum 32 actual calls) plus up to 2 gated calls per identity
(STAGE 1 gated on STAGE 0, STAGE 2 gated on STAGE 1). Maximum `32 × 3 = 96`
decoder calls. A blocked stage is a recorded non-invocation, never a
replacement, retry, or fabricated result, and it blocks every downstream stage
for that identity. No transfer back into a layer from its own posterior.

## 6. Frozen matrix, decoder, estimator (reused verbatim from D7-E/F)

- `f` order `[1.0, 1.2]`.
- Seeds `2026091300..2026091315`, ascending, exactly 16 per `f`.
- `n=64`; L1 rows 49 (`f=1.0`) / 59 (`f=1.2`); L2 rows 43 (`f=1.0`) / 52
  (`f=1.2`); D5-native mothers
  `build_dv3_nested_support(64, 64, 49, 2026090501)` +
  `assign_gf32_coefficients(sup, 2026090501, None, 64)` (L1) and
  `build_dv3_nested_support(64, 64, 43, 2026090502)` +
  `assign_gf32_coefficients(sup, 2026090502, None, 64)` (L2); accepted Model-F
  root `workspace/v72p2d5_model_f_input/20260907_r1`.
- Row-layered only: GF(32) poly 37, cold start, `max_iter=90`, damping `1.0`.
- No flooding, no oracle, no CAL/VAL, no real/raw, no graph/mother change.
- Estimator identity is a hard pre-execution contract: the joint is obtained
  **only** through `prepare_model_f_prior_candidate` /
  `build_f_model_concentration` (per-Bob-column
  `(counts[:,b] + lambda*p_global)/(n_b[b] + lambda)`). The historical
  `build_f_model` `counts + lambda` per-cell rule is forbidden; static and
  behavioral tests must fail if it is referenced.
- Floor/renormalize exactly as the accepted D5 helper contract.

## 7. No-returned-evidence rule (decisive)

- The cross-layer transfer message is **only** the explicit
  `CHECK_EXTRINSIC` code-factor extrinsic, transported by the narrow D7-G
  helper `require_check_extrinsic_for_transfer`. Posterior
  `softmax(final_beliefs)` may not be used as a transfer message; no consumer
  may reconstruct a prior by subtracting an unknown/reconstructed value.
- The backward prior is a function of **L2's code-factor extrinsic only**,
  never L2's posterior, so the forward stage's L1 incoming evidence cannot be
  returned to L1 (cavity property).
- Each decode invocation consumes its designated syndrome once; L1 is decoded
  twice across STAGE 0 and STAGE 2, but STAGE 1's outgoing code extrinsic
  removes its entire incoming prior, including STAGE 0's L1 evidence, before
  STAGE 2 consumes L1 syndrome again. No target posterior is fed back,
  blended, multiplied, or reused.
- Tests must prove: (a) the forward-stage L1 evidence is excluded from the
  backward prior; (b) iteration-0 neutral extrinsic cannot create a false
  lift; (c) warm/unknown provenance is rejected; (d) a posterior-based
  back-transfer would double-count and is never reached; (e) the returned
  prior is invariant to the removed STAGE 0 incoming-message component while
  remaining sensitive to STAGE 1's own check evidence.

## 8. Frozen labels, terminal, budgets

### Paired labels per `f` (first match)

1. `COVERAGE_BLOCKED` — fewer than 12/16 identities have a complete chain
   (all three stages invoked and finite/shape-valid). Both endpoints share the
   chain, so one complete-chain coverage count is recorded per `f`, plus
   explicit blocked-at-stage1 and blocked-at-stage2 counts.
2. `ALTERNATING_REGRESSION` — `reference_only >= 2` and `candidate_only == 0`.
3. `STRONG_ALTERNATING_LIFT` — `candidate_only >= 4` and
   `reference_only == 0`.
4. `WEAK_ALTERNATING_LIFT` — `candidate_only > reference_only` but strong not
   met.
5. `NO_ALTERNATING_LIFT` — otherwise.

Synthetic diagnostic labels, not FER thresholds. `candidate_only` = candidate
both-exact and reference not; `reference_only` = reference both-exact and
candidate not.

### Run terminal priority (first applicable)

1. `D7_H_PRE_EXECUTION_BLOCKED`
2. `D7_H_WATCHDOG_TIMEOUT_VOID`
3. `D7_H_NONFINITE_OR_CRASH_BLOCKED`
4. `D7_H_RESOURCE_OVERRUN`
5. `D7_H_INCOMPLETE_MATRIX_BLOCKED`
6. `D7_H_PROVENANCE_COVERAGE_BLOCKED`
7. `D7_H_ALTERNATING_STRONG_LIFT` — either `f` strong and the other does not
   regress
8. `D7_H_ALTERNATING_WEAK_LIFT` — either `f` weak and neither regresses
9. `D7_H_ALTERNATING_REGRESSION`
10. `D7_H_NO_USEFUL_ALTERNATING_LIFT`

No automatic successor is encoded.

### Budgets

- 1 unconditional mandatory call per identity plus up to 2 gated calls; hard
  cap 96 decoder calls (minimum 32: STAGE 0 only); sequential only; no
  concurrency/retry/rerun/resume.
- Per-call watchdog 120 s.
- Stored scientific wall <=1500 s.
- Outer GNU timeout `1800` plus `-k 30`.
- `.venv/bin/python` only.
- On Linux/WSL, current-process peak RSS from `/proc/self/status` field
  `VmHWM` (unit exactly `kB`, `bytes = value * 1024`), strict `< 2 GiB`,
  fail-closed.
- One fresh identifier; target fresh direct child
  `workspace/d7_h_alternating_discriminator_<uuid>/`, no overwrite,
  no subdirectories; exactly seven scalar text files plus an independent
  read-only verifier.

## 9. Exact future WSL command (frozen, NOT run in this task)

```bash
timeout -k 30 1800 .venv/bin/python scripts/v72p2d7_gf32_alternating_discriminator.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_h_alternating_discriminator_<uuid>
```

- Status `NOT_AUTHORIZED`: frozen but unauthorized and not executed; no
  identifier generated here.
- Operational precondition: cwd is the repository root; `.venv/bin/python` is
  executable and imports the project dependencies. Do not activate another
  venv, use bare `python`/`python3`, add `PYTHONPATH`, or alter child argv.
- `--model-f-root` must resolve to exactly
  `workspace/v72p2d5_model_f_input/20260907_r1`; any other value refuses
  (`D7_H_PRE_EXECUTION_BLOCKED`) before decoder bind, Model-F read, or root
  creation.
- `--out-root` must be a fresh direct child of `workspace/` named
  `d7_h_alternating_discriminator_<uuid>`; the writer refuses overwrite and
  refuses subdirectories.
- This command was NOT run to produce this freeze; no D7-H root exists.

## 10. Root contract and seven-file schema

Future root `workspace/d7_h_alternating_discriminator_<uuid>/`: fresh,
no-overwrite, no subdirectories, exactly seven compact scalar text files:

- `manifest.json`
- `decoder_records.csv`
- `arm_pairs.csv`
- `stratum_summary.csv`
- `summary.json`
- `report.md`
- `command_log.txt`

`decoder_records.csv` holds STAGE 0 rows for all identities plus only the
invoked eligible STAGE 1/STAGE 2 rows (blocked stages recorded as
non-invocations elsewhere, never fabricated). `arm_pairs.csv` holds one row per reference/
candidate arm pair per `(f,seed)` with shared-identity pins
(f/seed/block/H/syndrome/decoder config), per-stage eligibility and
provenance, L1/L2/L1_return exact/syndrome separately, and both
`reference_both_layers_exact` and `candidate_both_layers_exact`.
`stratum_summary.csv` holds 2 rows (one per `f`) with one complete-chain
coverage count, explicit blocked-at-stage1/blocked-at-stage2 counts,
`candidate_only`/`reference_only`/`both`/`neither`, and `stratum_label`.
`manifest.json`/`summary.json`/`report.md`/`command_log.txt` mirror the D7-F
conventions (frozen identities, estimator ID, lambda, rows, seeds, graph
seeds, stage order, decoder kwargs, budgets, seven-file list, terminal
priority; terminal, labels, totals, wall, peak RSS, retries/reruns/resumes =
0).

Writer/verifier split: the verifier reads only the seven files and
independently recomputes stage order, the unconditional STAGE 0 count (=32),
the invoked STAGE 1 and STAGE 2 counts, uniqueness, no replacement, pair
identity, the `CHECK_EXTRINSIC` gate, exact/syndrome isolation, both-layer AND
rules, per-invocation designated-syndrome accounting, the no-returned-evidence
rule, labels, terminal, wall/RSS and schema; it never calls a decoder and
never loads Model-F.

Persist no beliefs, priors, symbols, syndromes, block vectors, or extrinsic
message payloads; all `belief_*`/`extrinsic_*`-style fields, if any, are
scalars only.

## 11. Planned code paths (frozen names; implementation NOT authorized here)

- Module:
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_alternating_discriminator.py`
- Tests:
  `comparison_bench/tests/test_v72p2d7_gf32_alternating_discriminator.py`
- Script:
  `scripts/v72p2d7_gf32_alternating_discriminator.py`
- Reuse D7-E/F loaders, estimator, provenance, RSS, scalar-writer and
  verifier conventions via narrow imports (no predecessor-module copies);
  consume the D7-G `extrinsic_log_beliefs` / `extrinsic_provenance` fields and
  the `require_check_extrinsic_for_transfer` helper. Lazy binding + DI
  required.

## 12. Phase plan for the future implementer (all later gates, NONE authorized now)

- H01 implementation (module/tests/script) — requires explicit authorization.
- H02 implementation review → `D7_H_IMPLEMENTATION_REVIEW_PASS|FAIL`.
- H03 Pre-EXECUTE review →
  `D7_H_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION|FAIL`.
- H04 execute exactly once under a verbatim user authorization bound to one
  identifier.
- H05 Pre-RESULT review, then result acceptance.
- No step in H01–H05 is authorized by this freeze.

## 13. Authorization lifecycle

- `docs/research_cycles/V72P2D7-GF32-ALTERNATING-DISCRIMINATOR/cycle_state.yaml`
  holds all execution authorization and promotion fields false; attempts
  zero; no identifier, no root.
- The future runner reads only this state file and refuses before any work,
  Model-F read, decoder bind, or root creation while the key is false. A
  future verbatim user authorization flips the key for exactly one identifier
  and is consumed on the first decoder attempt regardless of outcome; no
  retry, rerun, resume, or reuse.
- Import, `--help`, `--dry-run`, and unauthorized runs bind no decoder, read
  no Model-F, and create no root.
- Explicit future authorization is required; none is granted by this freeze.

## 14. Nonclaim boundaries

Alternating classifications are route discriminators, not FER estimates. No
result of D7-H may be described as protocol recovery, leakage,
reconciliation-efficiency, key-rate, CAL/real-data, qualification, promotion,
R1d, G1/G2, or general GF32/NB-LDPC performance. `D7-H is not authorized and
not executed`; this freeze creates no runner, root, or identifier and
supports no alternating-convergence claim.

## 15. Return (this freeze task)

Delta only: changed paths; the frozen schedule and its derivation; the frozen
label/terminal/budget set; confirmation that all candidate paths were absent
and no unauthorized file was touched; confirmation that every authorization
flag remains false and no D7-H root/identifier exists; residual mathematical
limitations; exact next gate (`D7_H_IMPLEMENTATION_PENDING`, not authorized).
