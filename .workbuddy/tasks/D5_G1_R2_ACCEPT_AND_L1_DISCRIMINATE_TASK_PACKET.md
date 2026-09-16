# D5-G1-R2-ACCEPT-AND-L1-DISCRIMINATE — autonomous mainline continuation

## 0. Mission

Complete two connected mainline steps without routine check-ins:

1. land and accept the independently reviewed R2 lambda-contract candidate;
2. resolve whether L1 can recover at a useful `n=64` operating point under an
   honest CAL-only estimator, and if not, whether block-length scaling—not
   post-hoc smoothing—restores a viable signal.

This is the next blocker on the path toward G2. It is not broad lateral model
search. Work autonomously through preregistration, CAL-only estimation,
development decoder experiments, OpenSpec/implementation where warranted,
tests, and local commits.

## 1. Baseline

- Repo `D:/Code/HD-QKD_Polar_Comparison`
- Branch `formal-ir-v72p1-addendum-clean`
- Initial HEAD `1d4fa9124afd57ec5ce03a786a4cdc2b2f55cc1d`
- R2 review file `G1_INFORMATION_RECOVERY_R2_REVIEW_R1.md`
- Required verdict `G1_INFORMATION_RECOVERY_R2_REVIEW_PASS`
- Candidate code commit `a93106f5`
- Lifecycle closeout `1d4fa912`
- Current gate `INDEPENDENT_G1_INFORMATION_RECOVERY_R2_REVIEW`
- Formal G1 negative result accepted and immutable; G2 absent; all
  authorizations false

Note the test-count explanation: the legacy D4 file has 30 tests and D4R2 has
32. A suite using one reports 227 or 229; future milestone verification must
run **both**, i.e. the four-file D5 suite, to remove ambiguity.

## 2. Hard boundaries

- No formal G1 rerun/resume, CLI `--phase`, G2 formal grading, n=1024 formal
  run, real IR, or Release execution.
- No VAL read/use. Canonical CAL-TRAIN only.
- No formal-root write/hash/delete/move/rename/overwrite; no VOID-G1 read.
- No change to accepted G1 result, frozen packets/thresholds/seeds,
  authorization fields, promotion, or existing accepted artifacts.
- Development results are not formal evidence and cannot authorize G2.
- No seed search, unconstrained hyperparameter sweep, model zoo, or selection
  on decoder success.
- No frozen baseline `src/experiments/tools` modification.
- No dependency/framework/generalized infrastructure unless concretely needed.
- No push/reset/stash/checkout/clean/rebase/revert/amend/renormalize/broad stage.

## 3. Phase A — accept reviewed R2 candidate

### A01 baseline gate

Verify exact HEAD, review verdict, commit manifests, clean scoped content,
formal-root snapshots, G2 absence, all authorizations false, and unchanged
accepted G1 evidence. Any deviation is STOP.

### A02 acceptance record and lifecycle

Create:

`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_INFORMATION_RECOVERY_R2_ACCEPTANCE_R1.md`

Accept only:

```text
G1_INFORMATION_RECOVERY_R2_ACCEPTED
scope: ADDITIVE_NONFORMAL_BACKOFF_PRIOR_CANDIDATE
terminal_class: LAMBDA_APPLICATION_CONTRACT_DEFECT
formal_g1_result_changed: false
production_wiring_changed: false
```

Record decisive formula/provenance, old-vs-candidate CE/MI/truth-mass values,
three-call independent confirmation, L1/disclosure limitations, and all
nonclaims. R2 acceptance validates the candidate path; it does not replace the
accepted Model-F artifact or authorize a G1 rerun.

Update only:

```yaml
g1_information_recovery_r2_review: PASS_R1
g1_information_recovery_r2_candidate_accepted: true
g1_information_recovery_r2_implementation: a93106f5
g1_information_recovery_r2_terminal_class: LAMBDA_APPLICATION_CONTRACT_DEFECT
next_gate: G1_L1_ESTIMATOR_DISCRIMINATOR_IN_PROGRESS
```

Append concise entries to decision log and project memory. Mark OpenSpec T5
complete with commit/review evidence; do not rewrite other tasks.

Stage exactly six files: unchanged review, new acceptance, cycle state,
decision log, memory, and R2 `tasks.md`. Commit:

```text
docs(v72p2d5): accept additive R2 backoff-prior candidate

Accepts the independently reviewed lambda-contract correction as an additive
nonformal candidate. Formal G1 remains the accepted no-signal result; no
production wiring, rerun, G2 authorization, or qualification is granted.

Co-Authored-By: OpenAI Codex <codex@openai.com>
```

## 4. Phase B — preregister the L1 discriminator

Before reading new CAL scores or running decoder controls, create and commit
`G1_L1_ESTIMATOR_DISCRIMINATOR_PREREG_R1.md`. Freeze:

- one primary endpoint: held-out CAL L1 NLL/CE;
- decoder endpoints: exact, syndrome, iterations, nonfinite, wall, RSS;
- useful n=64 requirement: recovery must occur below square disclosure
  (`m<64`), not merely at zero-rate `m=64`;
- paired deterministic seed prefix and sample counts;
- estimator candidates, at most three, selected from §5;
- disclosure points as sparse bracket/bisection, not exhaustive scan;
- optional block lengths `64→128→256` only if n=64 fails;
- stop rules and terminal classes in §7;
- no VAL and no decoder-outcome hyperparameter selection.

The prereg may use source and already persisted R2 evidence, but no new CAL
score or decoder output. Commit it alone before experiments.

## 5. Phase C — CAL-only L1 estimator comparison

Use at most three principled contracts:

1. accepted joint-F concentration backoff marginalized to L1 (baseline C1);
2. direct aggregated `P(U1|B)` concentration backoff estimated from the same
   CAL-TRAIN folds;
3. at most one simple hierarchical/backoff variant justified by the chain
   structure and existing project math.

Use the existing D4 lambda grid/fold discipline unless a different parameter
has a clear unit and is preregistered. Select by held-out CAL L1 NLL only.
Report effective concentration, support, entropy, truth mass, and MI. Decoder
success is evaluation, never the estimator-selection objective.

If direct L1 and joint-F estimates use different sufficient statistics or
populations, document the difference explicitly. Reject any estimator that
improves decoder results only through CAL resubstitution or hidden VAL use.

## 6. Phase D — paired decoder and block-scaling study

For the selected honest estimator(s):

1. run paired n=64 L1 square and sparse disclosure frontier;
2. keep matrix family/decoder/max_iter fixed within comparisons;
3. if n=64 never recovers below 64 rows, optionally test development-only
   `n=128` then `n=256` using preregistered seeds and rate-scaled rows;
4. vary one axis at a time: estimator, disclosure, or block length;
5. independently recompute exact and syndrome.

Do not call n=256 development diagnostics “G2”; they have no formal G2 seed,
threshold, result root, or authorization role.

Autonomous budget:

- <=8 hours operator wall;
- <=1500 decoder calls;
- <=120 s per call with outer watchdog;
- peak RSS <2 GiB;
- all output under one unique
  `workspace/d5_g1_l1_discriminator_r1_<uuid>/`.

Use adaptive stopping: once a terminal class is unambiguous, stop spending
calls. Persist compact scalar evidence, scripts, command log, and manifest; no
raw rows, symbols, beliefs, or per-block payload dump.

## 7. Terminal classes and route consequences

Choose exactly one:

- `L1_ESTIMATOR_CONTRACT_RECOVERABLE_AT_N64` — honest held-out-selected
  estimator recovers below 64 rows with reproducible paired signal;
- `L1_BP_THRESHOLD_NOT_RECOVERABLE_AT_N64` — honest estimators fail through
  square disclosure at n=64;
- `BLOCK_LENGTH_SCALING_RECOVERS_L1` — n=64 fails but a larger development
  block recovers at a nonzero-rate disclosure;
- `CAL_L1_INFORMATION_INSUFFICIENT` — held-out CAL evidence itself supports no
  useful L1 information;
- `MIXED_OR_UNRESOLVED_L1_CAUSE` — only with one named irreducible next test.

Consequences:

- recoverable n=64 → implement an additive layered-prior candidate and prepare
  it for independent review;
- block scaling only → produce a block-geometry successor proposal; do not
  start G2;
- CAL information insufficient → produce D5 route-stop proposal;
- unresolved → return the one main-thread decision.

## 8. Phase E — implementation when evidence warrants

If n=64 is recoverable under an honest estimator:

1. create OpenSpec `v72p2d5-g1-l1-estimator-recovery-r1` before code;
2. add the smallest injected, nonformal layered-prior candidate;
3. preserve old candidate and all production wiring;
4. test formula, folds/selection, axes, limits, isolation, and wrong-contract
   regression;
5. run compile, focused tests, then the four-file D5 suite:
   - `test_v72p2d5_gf32_rate_mother.py`
   - `test_v72p2d5_model_f_input.py`
   - `test_v72p2d4_cal_gf32_model_rate_audit.py`
   - `test_v72p2d4r2_cal_gf32_model_rate_audit.py`
6. rerun only the preregistered development confirmation.

If code is not justified, do not create it merely to show progress.

## 9. Allowed paths

Always allowed:

- new acceptance/prereg/final L1 discriminator reports in the D5 cycle dir;
- unchanged R2 review landing;
- append-only decision log and project memory;
- cycle state keys named here;
- R2 tasks T5 checkbox;
- new L1 OpenSpec directory;
- unique L1 workspace evidence root.

Conditionally allowed after OpenSpec:

- D5 GF32 rate-mother core and Model-F input core;
- their D5 tests plus both D4/D4R2 audit tests;
- D5 rate-mother and Model-F prepare scripts.

No other modifications without a concrete boundary blocker.

## 10. Acceptance IDs

- `L1-01`: R2 review landed and candidate accepted with exact six-path commit.
- `L1-02`: prereg committed before new scores/calls.
- `L1-03`: <=3 estimators, CAL-only held-out selection, zero VAL.
- `L1-04`: n=64 disclosure frontier paired and independently checked.
- `L1-05`: block scaling used only if prereg stop rule permits.
- `L1-06`: estimator/disclosure/block axes not confounded.
- `L1-07`: budget/call/watchdog/RSS limits met.
- `L1-08`: exactly one terminal class with counterevidence.
- `L1-09`: any code has prior OpenSpec and meaningful regression tests.
- `L1-10`: focused + four-file suite zero failures if code changed.
- `L1-11`: formal roots unchanged, G2 absent, all authorizations false.
- `L1-12`: scoped logical commits, no overclaim, no push.

## 11. Final deliverable and gate

Create `G1_L1_ESTIMATOR_DISCRIMINATOR_R1.md` with prereg adherence, CAL scores,
estimator formulas, paired decoder/frontier/block results, resources, terminal
class, implementation/tests if any, counterevidence, and one route recommendation.

Set only the final next gate:

- review-ready n64 estimator → `INDEPENDENT_G1_L1_ESTIMATOR_REVIEW`;
- block-scaling proposal → `G1_BLOCK_GEOMETRY_ROUTE_REVIEW`;
- route-stop proposal → `D5_ROUTE_STOP_REVIEW`;
- unresolved → `G1_L1_ROUTE_DECISION`.

Commit logical scoped deltas; do not push. Return L1-01–L1-12, terminal class,
CAL endpoint table, decoder calls/wall/RSS, changed files/SHAs, test summaries,
formal-root equality, and exact next gate.

End:

`L1 主线鉴别完成；正式 G1 负结果未改写、未重跑，G2 未授权；下一路线由证据终类决定。`

