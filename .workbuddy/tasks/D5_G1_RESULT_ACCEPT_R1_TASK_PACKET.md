# D5-G1-RESULT-ACCEPT-AND-ATTRIBUTION-R1

## 0. Mission and delegated authority

Work continuously through two phases without returning for routine engineering
decisions:

1. accept the sole frozen G1 run as the trusted negative result
   `SYNTHETIC_COMPLETED_NO_SIGNAL_FAIL`;
2. autonomously localize the all-zero failure and, if evidence identifies a
   concrete correctable cause, implement the smallest scientifically valid
   review candidate with OpenSpec and tests.

You may inspect code/artifacts, design bounded development diagnostics, run
them, iterate implementation/tests, and make multiple scoped local commits.
Do not stop for ordinary coding problems, expected failed hypotheses, or test
failures caused by your in-scope draft; fix those autonomously.

The main thread retains long-term route selection, formal thresholds, result
acceptance, formal execution authorization, G2, real data, and scientific
claims. Return only with a review-ready candidate or a genuine route decision
requiring those powers.

## 1. Baseline and accepted negative result

- Repo `D:/Code/HD-QKD_Polar_Comparison`
- Branch `formal-ir-v72p1-addendum-clean`
- Initial HEAD `58c68961a1dedad58f52145e9f23942f2c476e4a`
- Accepted implementation `cf61ee63`
- Valid result `workspace/v72p2d5_g1/20260907_r2`
- Review `G1_PRE_RESULT_REVIEW_R1.md` must say
  `G1_PRE_RESULT_REVIEW_PASS`
- Literal result: both `f` values APP exact `0/100`, syndrome `0`, oracle exact
  `0`, every APP block at aggregate max 180 iterations, no crash/nonfinite,
  wall/RSS gates met, `G1_COMPLETED_NO_SIGNAL_FAIL`, `passed=false`
- All formal authorizations false; G2 absent

Known porcelain CRLF churn is cosmetic when content numstat is zero. Do not
normalize or clean it.

## 2. Non-negotiable boundaries

Never:

- rerun/resume formal G1 or invoke any CLI `--phase`;
- create/write/reuse formal P0/G1/G2 roots, modify accepted evidence, or read
  retained VOID-G1 contents;
- run G2, real-data IR, CAL/VAL/parquet/raw-row loads, or Model-F prepare;
- change formal seeds, thresholds, result files, authorization, promotion, or
  semantics to make a failed result pass;
- describe development diagnostics as FER, leakage, key rate, qualification,
  promotion, formal evidence, or method success;
- modify frozen `src/`, `experiments/`, or `tools/`;
- push, force, reset, stash, checkout, clean, rebase, revert, amend,
  renormalize, broad-stage, or remove unrelated dirt.

Allowed autonomous development:

- read accepted Model-F NPZ/summary, valid G1 result, comparison code/tests,
  OpenSpec, roadmap, and persisted structural/G0/P0 evidence;
- run deterministic development decoder diagnostics through direct injected
  functions/harnesses, never CLI phase entrypoints;
- use `n=64`, accepted Model-F, frozen mothers/prefixes, and decoder settings;
  vary one axis only when explicitly diagnosing a cause;
- write compact evidence under one unique
  `workspace/d5_g1_no_signal_attribution_r1_<uuid>/`, never a formal root;
- modify the comparison-layer allowlist in §6 after OpenSpec when warranted;
- iterate until tests pass and the candidate is review-ready.

Budget: at most 2 hours operator wall and 300 decoder calls total; each call
must have a 120 s outer watchdog. Record calls, wall, RSS, and every control.
A timed-out diagnostic may be replaced by a cheaper in-scope diagnostic, never
by a formal run.

## 3. Phase A — accept the negative result

### AC01 baseline

Verify branch/HEAD, review PASS, the two execution commit manifests, all
authorizations false, G2 absent, valid G1 exactly four files, protected roots
matching the review, and pre-task content numstat empty. Deviation means STOP.

### AC02 acceptance record

Create `G1_RESULT_ACCEPTANCE_R1.md` with:

```text
G1_RESULT_ACCEPTED
scope: SYNTHETIC_COMPLETED_NO_SIGNAL_FAIL
outcome: G1_COMPLETED_NO_SIGNAL_FAIL
passed: false
```

Record evidence chain `cf61ee63 → 6494b623 → f4d577fb → 58c68961`, both
reviews, literal values/arithmetic, resources-pass/signal-fail distinction,
exact/syndrome/oracle isolation, consumed attempt/no rerun, and all nonclaims.
Acceptance trusts the negative record; it does not make the method pass.

### AC03 lifecycle and first commit

Add only:

```yaml
g1_execution_attempts: 1
g1_execution_completed: 1
g1_result_accepted: true
g1_result_accepted_scope: SYNTHETIC_COMPLETED_NO_SIGNAL_FAIL
g1_result_outcome: G1_COMPLETED_NO_SIGNAL_FAIL
g1_result_passed: false
```

Change only `next_gate` to `G1_NO_SIGNAL_ATTRIBUTION_IN_PROGRESS`. Append the
same durable facts to `docs/decision-log.md` and `AGENT_PROJECT_MEMORY.md`.

Stage exactly those four files plus unchanged
`G1_PRE_RESULT_REVIEW_R1.md` (five paths), then commit:

```text
docs(v72p2d5): accept G1 completed-no-signal result

Accepts the sole frozen G1 attempt as an internally coherent synthetic
completed-no-signal failure. This is not G1 trend pass, qualification, G2
readiness, or permission to rerun. Opens bounded failure attribution only.

Co-Authored-By: OpenAI Codex <codex@openai.com>
```

## 4. Phase B — autonomous causal localization

The objective is attribution, not broad algorithm search. Work in order and
stop testing a branch once discriminated.

### AC04 causal ledger

Parse accepted evidence and source. State what APP+oracle zero, syndrome zero,
iteration saturation, and clean resource completion rule out and leave open.

### AC05 decoder/matrix sanity first

Use tiny deterministic development calls to test each frozen L1/L2 prefix:

1. noiseless codeword/syndrome consistency;
2. direct recovery from a known valid codeword or zero-error pair;
3. GF32 field/order/orientation across H, symbols, syndrome, and prior;
4. independent exact/syndrome recomputation.

If noiseless recovery fails, localize the first failing boundary—matrix,
GF32/orientation, decoder adapter, stopping, or exact extraction—before testing
APP quality.

### AC06 oracle/APP/budget discrimination

Only if AC05 passes, use paired deterministic subsets to compare:

- oracle prior vs APP Model-F prior;
- L1 alone vs L1→L2;
- frozen rows vs one small exploratory stronger-prefix control;
- frozen iteration cap vs a convergence-trace control only if needed.

Change one axis at a time, share identical samples/seeds within pairs, use the
smallest discriminating sample, and never seed-search or tune for success.

Select exactly one primary bucket where evidence permits:

- `DECODER_OR_FIELD_INTEGRATION_DEFECT`
- `MATRIX_PREFIX_OR_RANK_DEFECT`
- `FINITE_LENGTH_DISCLOSURE_INSUFFICIENT`
- `APP_MODEL_PROPAGATION_DEFECT`
- `ITERATION_DYNAMICS_STAGNATION`
- `MULTIPLE_CAUSES_NOT_DISCRIMINATED`

Every diagnostic records input identity, changed axis, calls, exact, syndrome,
iterations, nonfinite, wall, RSS, and result. Use the explanation accounting
for APP and oracle zero with the fewest assumptions. No unpaired or multi-axis
causal claim.

## 5. Phase C — implementation when warranted

If evidence identifies a concrete implementation defect or uniquely supported
minimal algorithm correction:

1. create OpenSpec `v72p2d5-g1-no-signal-attribution-r1` before code;
2. implement only the correction implied by evidence;
3. add focused numerical tests that fail on old behavior;
4. preserve formal result and frozen formal constants;
5. run compile, focused tests, then the exact three-file D5 suite with a fresh
   nonformal basetemp;
6. run only development diagnostics needed to confirm the repaired boundary;
7. commit OpenSpec/evidence separately from implementation where practical.

Do not implement merely because “more rows might help” or while multiple causes
remain. Then report ranked evidence and one next discriminating experiment for
main-thread approval.

## 6. File boundary

Always allowed:

- new `G1_RESULT_ACCEPTANCE_R1.md` and `G1_NO_SIGNAL_ATTRIBUTION_R1.md`;
- unchanged `G1_PRE_RESULT_REVIEW_R1.md` landing;
- append-only decision log and project memory;
- cycle state only as specified;
- new `openspec/changes/v72p2d5-g1-no-signal-attribution-r1/**`;
- unique attribution workspace root.

Conditionally allowed after evidence and OpenSpec:

- `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`
- `comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py`
- `comparison_bench/tests/test_v72p2d5_model_f_input.py`
- `scripts/v72p2d5_gf32_rate_mother.py`

No other change. If the correct fix requires another path, return that exact
main-thread decision blocker.

## 7. Acceptance matrix

- `AC01`: negative-result acceptance committed with five exact paths.
- `AC02`: formal roots unchanged; G2 absent; all authorizations false.
- `AC03`: causal ledger accounts for APP+oracle+saturation evidence.
- `AC04`: decoder/matrix/noiseless sanity matrix completed.
- `AC05`: paired one-axis controls used, or sanity failure makes them moot.
- `AC06`: <=300 calls, <=2h total, <=120s/call; no formal CLI/root.
- `AC07`: one supported bucket, or honest multiple-causes + one next test.
- `AC08`: no overclaim or formal-result reinterpretation.
- `AC09`: code change has prior OpenSpec and focused/full green tests.
- `AC10`: final diff restricted to §6; unrelated dirt preserved; no push.

## 8. Deliverable and terminal return

Create `G1_NO_SIGNAL_ATTRIBUTION_R1.md` with causal ledger, diagnostics, call/
resource accounting, rejected hypotheses, selected bucket, implementation
rationale/diff/tests if any, residual uncertainty, and exact main-thread next
decision.

Final next gate:

- review-ready code candidate → `INDEPENDENT_G1_ATTRIBUTION_CODE_REVIEW`;
- no justified code → `G1_ATTRIBUTION_ROUTE_DECISION`.

Do not add pass/accepted fields for exploratory work. Commit scoped attribution
docs/evidence and candidate code in logical commits. Do not push.

Return deltas only: AC01–AC10; bucket/evidence; diagnostic calls/wall/RSS;
changed files/commits; tests if code changed; protected-root equality/G2
absence/auth state; and any one main-thread decision.

End with one:

`G1 负结果已接受；无信号原因已形成可独立评审候选，未重跑正式 G1，G2 未授权。`

or

`G1 负结果已接受；归因仍需主线程裁决所列单一分岔，未重跑正式 G1，G2 未授权。`

