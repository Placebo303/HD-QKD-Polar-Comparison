# D7-E provenance-safe cross-layer readiness + D6 compatibility R1

Status: `MAIN_THREAD_FROZEN_HEAVY_READINESS_PACKET_R1` — zero claim-bearing execution

## 0. Main-thread assessment and route

The D7-D/BP closeout at entry HEAD is accepted as an implementation/readiness
milestone:

- D7-D accepted scope remains
  `D7_D_RESULT_ACCEPTED_SCHEDULE_EFFECT_INCONCLUSIVE`;
- BP Alternative A at `654fa299` is accepted as the current interface contract;
- `PRIOR_ONLY`, missing/None/unknown and `WARM_START_UNSPECIFIED` cannot feed a
  conditioned cross-layer APP; only `CHECK_UPDATED` may do so;
- D7-C/D7-D do not consume cross-layer returned beliefs and remain valid;
- the accepted D7-B hard-decision result remains valid with its soft-belief
  limitation;
- the corrected concentration Model-F candidate is the only admissible D5-D7
  estimator semantics; old per-cell lambda remains historical and unwired;
- D6 R1d is optional/paused, not a mainline gate.

Newly confirmed D6 compatibility blocker:

`scripts/v72p2d6_graph_mother_development.py` still unpacks five values from
`_decode_block`, while the accepted BP interface returns six including
provenance. The broad worker exception converts this to crash rows, and the
runner forwards beliefs without checking provenance. Therefore every existing
R1d Pre-EXECUTE verdict is stale and R1d must not be authorized until Track A
passes a renewed review.

Mainline Track B is D7-E: a development-only, single-pass, two-direction
cross-layer transfer discriminator. It tests whether a `CHECK_UPDATED` source
belief recovers a useful fraction of D7-C's oracle ceiling. It is not
alternating/joint BP, does not force a sweep, and carries no execution authority.

## 1. Baseline and global prohibitions

- Repository `HD-QKD_Polar_Comparison`, WSL checkout.
- Branch `formal-ir-v72p1-addendum-clean`.
- Expected entry HEAD `4a5206fbb1d933262f7f51b1855a152985fc508e`.
- Required accepted reviews:
  `D7_BP_INTERFACE_IMPLEMENTATION_REVIEW_PASS` and
  `D7_BP_INTERFACE_READINESS_REVIEW_PASS`.
- Required gate:
  `D7_E_PROVENANCE_SAFE_CROSS_LAYER_DISCRIMINATOR_PACKET_FREEZE`.
- All execution authorization and promotion fields false.
- D7-E root absent; no D7-E UUID.

Hard prohibitions:

- zero scientific/claim-bearing decoder calls, zero `--phase`, R1d/G1/G2,
  Model-F/CAL/VAL/parquet/real/raw/VOID-content reads;
- no modification of accepted result roots or frozen baseline `src/`,
  `experiments/`, `tools/`;
- no R1d or D7-E execution, UUID generation, result acceptance or push;
- no forced extra sweep, warm-start mechanism, alternating iterations,
  feedback loop, joint factor graph, tuning/search or estimator change;
- tests use only tiny explicit in-memory fixtures/fakes and task-owned fresh
  basetemps; no production root/loader/decoder binding from tests;
- preserve unrelated dirty/CRLF and external V35 rewrites; if V35 changes again,
  report it and restore only the already-authorized committed corrected content;
- explicit path staging only; no clean/reset/checkout/stash/rebase/amend/broad
  stage.

The operator may work autonomously for hours. Return only after all R01-R24 are
complete or on one concrete scientific-contract blocker. A Track-A-only blocker
does not block Track B unless it reveals a defect in the accepted common BP
contract.

## 2. Track A — D6 runner compatibility repair (R01-R07)

### R01 — independent reproduction

Without a real decoder or result root, reproduce the five-versus-six arity
failure with an injected fake `_decode_block`. Prove the current broad worker
exception maps it to a crash cell. Also prove the unguarded `softmax(bel)` to
`app_fed_l2_prior` path. Record exact source lines and no-side-effect evidence.

### R02 — OpenSpec revision

Create a small dedicated change:

`openspec/changes/v72p2d6-r1d-bp-provenance-compat/`

Freeze only:

- six-value unpacking and explicit provenance transport through worker IPC;
- `CHECK_UPDATED` required before APP mixing;
- prior-only/missing/unknown/warm provenance yields a named fail-closed cell,
  never crash and never L2 APP decode;
- setup/warmup cannot report ready when decoder-result shape is incompatible;
- no scientific arm, seed, rows, mother, schedule, estimator, threshold, budget
  or terminal interpretation change;
- historical A2 roots immutable and no R1d execution.

Create an R1d execution-packet addendum declaring prior Pre-EXECUTE stale and
superseded after repair. Do not grant execution.

### R03 — minimal implementation

Modify only D6 runner/test/OpenSpec files required to:

- unpack `(exact, syndrome_ok, iterations, finite, beliefs, provenance)`;
- carry provenance in the worker result;
- preserve beliefs only for transient IPC when requested;
- require exact token `CHECK_UPDATED` before q construction and APP mixing;
- emit a deterministic provenance-blocked record for all other tokens;
- make compatibility warmup fail loudly/ready=false on wrong return shape;
- keep all existing scientific constants and non-BP records byte/field
  compatible.

Do not broaden the worker exception; arity/programming errors must not be
silently sold as scientific crash cells.

### R04 — tests

Add focused fake tests for six-value success, five-value incompatibility,
CHECK_UPDATED pass-through, each refused provenance class, mixer/L2 spies,
warmup readiness and unchanged frozen dispatch/matrix. Run D6 focused and BP
interface regression. Zero real decoder.

### R05 — independent review

Create `D6_R1D_BP_COMPAT_IMPLEMENTATION_REVIEW_R1.md`. Verdict only:

- `D6_R1D_BP_COMPAT_IMPLEMENTATION_REVIEW_PASS`
- `D6_R1D_BP_COMPAT_IMPLEMENTATION_REVIEW_FAIL`

One scoped rework is allowed. Reviewer verifies no science drift and that every
cross-layer path fails closed.

### R06 — renewed R1d Pre-EXECUTE status

Create `D6_R1D_PRE_EXECUTE_REVIEW_BP_COMPAT_A1.md`. This is code/readiness
review only: no Model-F content, decoder, root or authorization. Required PASS
token:

`D6_R1D_PRE_EXECUTE_REVIEW_PASS_BP_COMPAT_A1_AWAITING_EXPLICIT_AUTHORIZATION`

R1d remains `PAUSED_OPTIONAL_LOCAL_CONFIRMATION_NOT_MAINLINE_GATE` even on PASS.

### R07 — Track-A commits

Use three scoped commits:

1. `docs(d6): freeze R1d BP provenance compatibility repair`
2. `fix(d6): adapt R1d runner to fail-closed belief provenance`
3. `docs(d6): record renewed optional R1d readiness review`

Do not touch D7-E files in these commits.

## 3. D7-E frozen scientific question

Question: on the exact D7-C frozen identities, can one provenance-valid
single-pass source-layer BP belief improve target-layer exact recovery over the
target marginal control, in either direction, without oracle truth or feedback?

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

## 4. Frozen D7-E matrix and formulas (R08-R10)

### R08 — identities and decoder contract

- `f` order `[1.0, 1.2]`.
- seeds `2026091300..2026091315`, ascending, exactly 16 per f.
- same generated blocks, graph seeds, frozen rows/mothers and corrected
  concentration Model-F semantics as accepted D7-C/D7-D.
- row-layered only: poly 37, cold start, `max_iter=90`, damping `1.0`.
- directions in order `[L1_TO_L2, L2_TO_L1]`.
- no flooding: D7-D established no preregistered flooding advantage.
- no oracle decoder calls: accepted D7-C tables are a contextual ceiling only.

Per `(f, seed)` exact slot order:

```text
L1_TO_L2_SOURCE_L1_MARGINAL
L1_TO_L2_TARGET_L2_CONTROL_MARGINAL
L1_TO_L2_TARGET_L2_TRANSFER       # invoked only if source CHECK_UPDATED
L2_TO_L1_SOURCE_L2_MARGINAL
L2_TO_L1_TARGET_L1_CONTROL_MARGINAL
L2_TO_L1_TARGET_L1_TRANSFER       # invoked only if source CHECK_UPDATED
```

There are 192 scheduled slots: 128 mandatory source/control decoder calls plus
up to 64 provenance-eligible transfer calls. A blocked transfer slot is a
recorded non-invocation, never replacement, retry or fake decoder result.

### R09 — transfer formulas

Let accepted corrected joint model be `P(U1,U2|B=b)` and source BP APP
approximation be normalized `q` from a `CHECK_UPDATED` log belief.

Estimator identity is a hard pre-execution contract, not an implementation
choice. D7-E and repaired D6 must obtain it only through
`prepare_model_f_prior_candidate` / `build_f_model_concentration`, whose
per-Bob-column smoothing is
`(counts[:,b] + lambda*p_global) / (n_b[b] + lambda)`. The historical
`build_f_model` rule `counts + lambda` per cell is forbidden. Static and
behavioral tests must fail if D7-E or D6 R1d references that legacy builder,
and a tiny asymmetric table must distinguish the two formulas numerically.

- L1 to L2:
  `P_transfer(U2|B,s1) = sum_u1 q1(u1|B,s1) P(U2|B,u1)`.
- L2 to L1:
  `P_transfer(U1|B,s2) = sum_u2 q2(u2|B,s2) P(U1|B,u2)`.

Floor/renormalize exactly as the accepted D5 helper contract. The source q is
transient and never persisted. No source truth enters either formula.

### R10 — pair and eligibility semantics

For each direction, the target control and transfer share f/seed/block/target
H/syndrome/decoder configuration; only target prior differs. Source exactness
does not gate eligibility. Eligibility requires source status finite/non-crash,
belief shape valid and provenance exactly `CHECK_UPDATED`.

Per `(f,direction)` stratum, at least 12/16 transfer slots must be eligible for
a mechanism label. Fewer gives `PROVENANCE_COVERAGE_BLOCKED`; no denominator
substitution or replacement seed.

## 5. Frozen labels, terminal and budgets (R11-R13)

### R11 — stratum labels

On eligible control/transfer pairs, first match:

1. `STRONG_TRANSFER_LIFT`: eligible >=12, transfer-only >=4,
   control-only <=1, transfer exact >=4, zero crash/nonfinite.
2. `TRANSFER_REGRESSION`: eligible >=12, control-only >=4,
   transfer-only <=1.
3. `NO_TRANSFER_RECOVERY`: eligible >=12, transfer exact <=1 and control exact <=1.
4. `CONTROL_ALREADY_RECOVERS`: eligible >=12 and control exact >=12.
5. `AMBIGUOUS_TRANSFER_EFFECT`: every other complete finite eligible case.
6. Empty label when eligible <12; coverage status records the reason.

The threshold `4/16` deliberately reuses D7-C's frozen useful-lift routing
threshold. It is a mechanism gate, not a probability estimate.

### R12 — run terminal priority

First applicable:

1. `D7_E_PRE_EXECUTION_BLOCKED`
2. `D7_E_WATCHDOG_TIMEOUT_VOID`
3. `D7_E_NONFINITE_OR_CRASH_BLOCKED`
4. `D7_E_RESOURCE_OVERRUN`
5. `D7_E_INCOMPLETE_CORE_CALL_MATRIX`
6. `D7_E_PROVENANCE_COVERAGE_BLOCKED`
7. `D7_E_BIDIRECTIONAL_TRANSFER_LIFT` — same f has strong lift both directions
8. `D7_E_L1_TO_L2_TRANSFER_LIFT` — strong only L1 to L2
9. `D7_E_L2_TO_L1_TRANSFER_LIFT` — strong only L2 to L1
10. `D7_E_TRANSFER_REGRESSION` — any regression, no strong lift
11. `D7_E_NO_USEFUL_TRANSFER_RECOVERY` — all four strata no recovery
12. `D7_E_MIXED_TRANSFER_DIAGNOSTIC`

All four strata and blocked-slot counts persist under higher-priority terminal.

### R13 — budgets

- hard cap 192 decoder calls; no concurrency/retry/rerun/resume;
- per-call watchdog 120 s;
- stored scientific wall <=1500 s;
- outer GNU timeout `1800` plus `-k 30`;
- WSL stdlib `resource` RSS finite positive and `<2GiB` before first call and
  recorded maximum during run;
- target fresh direct child
  `workspace/d7_e_cross_layer_discriminator_<uuid>/`, no overwrite/subdirs.

## 6. Track B — OpenSpec, implementation and tests (R14-R19)

### R14 — freeze before code

Create OpenSpec change:

`openspec/changes/v72p2d7-provenance-safe-cross-layer-discriminator/`

Create cycle directory:

`docs/research_cycles/V72P2D7-GF32-CROSS-LAYER-DISCRIMINATOR/`

Before code, add `D7_E_PREREG_R1.md` and `D7_E_EXECUTION_PACKET_R1.md` containing
§§3-5 verbatim in substance, WSL command below, schema, tests, reviews,
authorization lifecycle and nonclaims:

```bash
timeout -k 30 1800 python scripts/v72p2d7_gf32_cross_layer_discriminator.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_e_cross_layer_discriminator_<uuid>
```

Status `NOT_AUTHORIZED_NOT_EXECUTED`; no UUID. Commit:

`docs(d7-e): freeze provenance-safe cross-layer discriminator`

### R15 — minimal implementation

Preferred new files:

- `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_cross_layer_discriminator.py`
- `comparison_bench/tests/test_v72p2d7_gf32_cross_layer_discriminator.py`
- `scripts/v72p2d7_gf32_cross_layer_discriminator.py`

Reuse accepted D7-C identity/model helpers and D5 BP-provenance/mixing helpers;
do not copy a second decoder or estimator. Implement lazy binding, dependency
injection, dry-run, unauthorized refusal before loader/decoder/root, exact
matrix order, transient q, fail-closed provenance, budgets, no-overwrite and
read-only verify.

Root contains exactly seven scalar text files:

- `manifest.json`
- `decoder_records.csv`
- `transfer_pairs.csv`
- `stratum_summary.csv`
- `summary.json`
- `report.md`
- `command_log.txt`

Persist no beliefs, priors, symbols, syndromes, block vectors or digests.

### R16 — verifier

Independently recompute from record scalars: slot order, mandatory 128 calls,
eligible transfer invocation count, uniqueness, no replacement, pair identity,
provenance gate, exact/syndrome isolation, four labels, terminal, wall/RSS and
schema. Verify never loads Model-F or binds/calls decoder.

### R17 — tests

At minimum cover:

- exact 192-slot dry-run order and 128 mandatory calls;
- both transfer formulas against direct enumeration;
- corrected per-column concentration estimator identity, plus a negative
  fixture proving the legacy per-cell-lambda builder would differ and is never
  reached;
- CHECK_UPDATED allows exactly one transfer call;
- prior-only/missing/None/unknown/warm blocks before mixer/target decoder;
- source exact false remains eligible when provenance valid;
- fewer than 12 eligible yields coverage block;
- thresholds/boundaries and full terminal truth table;
- crash/nonfinite/resource/watchdog priority;
- scalar-only seven-file writer, no-overwrite and verifier tamper cases;
- external-cwd WSL import and exact decoder/loader sentinels;
- D7-C/D7-D import/behavior independence;
- no production artifact/root read from tests.

Run focused tests plus affected BP/D7-A/B/C/D and D5 regression in separate
groups. No broad suite that accidentally collects known historical run roots.

### R18 — implementation review

Independent reviewer creates `D7_E_IMPLEMENTATION_REVIEW_R1.md`; checks formulas,
provenance, pairing, thresholds, no double-counting, no oracle truth, terminal,
schema and all tests. Verdict only:

- `D7_E_IMPLEMENTATION_REVIEW_PASS`
- `D7_E_IMPLEMENTATION_REVIEW_FAIL`

One scoped rework allowed, then re-review.

### R19 — independent WSL Pre-EXECUTE

Separate reviewer creates `D7_E_PRE_EXECUTE_REVIEW_R1.md`. It must independently
confirm implementation review PASS, matrix, exact future command, target
absence, venv-on-PATH, GNU timeout, stdlib RSS, unauthorized refusal, dry-run,
external-cwd dual source/target decoder plus Model-F loader sentinels, tests,
protected roots and all authorization false.

Required PASS token:

`D7_E_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`

It grants nothing.

## 7. Closeout (R20-R24)

### R20 — code/review commits

After tests/reviews:

1. `feat(d7-e): implement provenance-safe cross-layer discriminator`
2. `docs(d7-e): record implementation and pre-execute reviews`

Explicit path stage only; no result root or push.

### R21 — state and roadmap

Set D7-E state to `D7_E_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`; all auth false,
decoder/result false, no UUID/root. Update CURRENT_MAINLINE, decision-log and
memory with readiness facts only. Record D6 compatibility repaired but R1d
still optional/paused.

### R22 — stale-test debt

Do not expand this task into broad historical cleanup. Record the ten isolated
baseline tripwires as lifecycle-test debt. Repair only any stale test directly
blocking D7-E's required scoped suite, using snapshot invariance rather than
root absence. No skip/xFAIL/delete.

### R23 — final invariant audit

Verify:

- no scientific decoder call/root/UUID;
- D7-B/C/D and all protected roots metadata unchanged;
- D7-E and R1d roots absent;
- all authorization/promotion false;
- scoped commits only, no staged residue, no push;
- V35 committed corrected report remains authoritative;
- external push observations are reported but never treated as authority.

### R24 — return

Report delta only:

1. R01-R24 table;
2. D6 defect reproduction, fix, tests and renewed verdict;
3. D7-E frozen matrix/formulas/thresholds/terminal;
4. code/schema and test manifests;
5. literal grouped test summaries;
6. independent review verdicts;
7. commits and scoped file lists;
8. roots/auth/no-push;
9. remaining risks and exact next gate.

Success ending:

`D6 R1d 的 BP provenance 兼容性断裂已零-decoder修复并重新评审，但 R1d 继续可选暂停；D7-E provenance-safe 双向单次跨层 discriminator 已冻结、实现并通过独立 Pre-EXECUTE，尚未授权、未执行，G1/G2 均未授权。`

Blocker ending:

`STOP — D7-E/D6-compat readiness 包命中具体 blocker；未跨越失败门、未执行任何科学任务，正式根和授权状态保持不变。`
