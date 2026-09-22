# D7-C — bidirectional cross-layer oracle freeze, implementation and Pre-EXECUTE R1

## 0. Deferred-start gate

Do not start this packet while the D7-B early-exit audit task is running or
while it owns Git/test state. Start only after that task has returned and its
independent review verdict is:

`D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT_REVIEW_PASS`

Read its accepted primary outcome and limitations before planning D7-C. If the
review is FAIL/BLOCKED, or the prior task has uncommitted in-scope work, STOP.

D7-C remains useful under any reviewed PASS branch because it directly builds
four single-layer priors from the frozen joint model and never consumes
`final_beliefs` as cross-layer APP. If the audit found a layer-interface or
belief-return defect, record it as a blocker for sequential/alternating use,
but do not let it silently alter this single-layer oracle diagnostic.

This packet authorizes planning, OpenSpec, implementation, fake/unit tests,
independent implementation review and independent Pre-EXECUTE review. It does
not authorize D7-C scientific decoder execution.

## 1. Objective

For the same frozen synthetic paired blocks, disclosures and historical
row-layered decoder, isolate whether either GF32 layer becomes recoverable only
when given the other layer's true symbol as diagnostic oracle information.

Compare four conditions:

1. `L1_MARGINAL`: `P(U1 | B)`
2. `L1_ORACLE_U2`: `P(U1 | B, U2_true)`
3. `L2_MARGINAL`: `P(U2 | B)`
4. `L2_ORACLE_U1`: `P(U2 | B, U1_true)`

This asks where cross-layer dependence lies. Oracle conditions are
counterfactual diagnostics only. They are not protocol recovery, do not count
oracle truth as disclosure, and support no FER/leakage/key-rate claim.

## 2. Baseline and protected scope

At task start, record the actual HEAD produced by the accepted D7-B audit. It
must descend from `03c2e68e` and include the D7-B result-acceptance/audit
commits. Do not require remote equality.

Required durable facts:

- D7-A certification accepted;
- D7-B R2 accepted only under its narrow scope;
- D7-B root UUID `c605d1e6-8577-4c52-a865-12500fc8c964` immutable;
- all execution authorization keys false;
- R1d paused; G2 absent;
- no `workspace/d7_c_bidirectional_oracle_*` root.

Existing Model-F, G0/P0/G1/D6/D7-B/VOID roots are immutable. During this
freeze/implementation task, inspect protected roots by names/sizes/mtime only.
Do not read Model-F binary content until a future explicitly authorized D7-C
execution.

Preserve unrelated dirty/CRLF, pending SOP/OpenSpec administration and
`.workbuddy/tasks`. Use explicit manifests/content numstat. No clean/reset/
checkout/stash/rebase/amend/broad-stage/push.

## 3. Frozen scientific contract

Write this contract to OpenSpec and preregistration before any production
decoder or real Model-F artifact access.

### 3.1 Input/model identity

- Accepted Model-F root:
  `workspace/v72p2d5_model_f_input/20260907_r1`
- Model estimator/application: the accepted post-R2 concentration semantics,
  lambda as total concentration per Bob column—not per-cell pseudocount
- No CAL/VAL/parquet/raw rows are read; only the accepted Model-F artifact may
  be loaded by the future authorized runner
- Dimension: n=64 symbols
- Block seeds: `2026091300..2026091315` (16 paired blocks)
- The same generated Bob/Alice/U1/U2 block is reused across both f values and
  all four conditions

Before implementation, trace the accepted production function that converts
Model-F counts into `P(U1,U2|B)` and freeze its exact callable/estimator ID.
If more than one accepted candidate is active or the accepted estimator cannot
be identified unambiguously, STOP rather than choose one.

### 3.2 Disclosures and decoder

- f order `[1.0, 1.2]`
- L1 rows `{1.0:49, 1.2:59}`
- L2 rows `{1.0:43, 1.2:52}`
- Reuse the accepted D5 n=64 L1/L2 mother construction and graph seeds; build
  in memory, never read VOID G1 matrices/results
- Historical certified row-layered GF32 FFT-QSPA
- cold start, `max_iter=90`, `damping_alpha=1.0`
- one single-layer decode per condition/block/f
- no sequential L1→L2 APP and no feedback in D7-C
- no flooding, schedule comparison, adaptive damping, clipping, restart,
  min-sum, graph search or parameter tuning

### 3.3 Prior construction

Let accepted joint table be `J[u1,u2,b]`, positive and normalized over
`(u1,u2)` for each Bob symbol.

- `L1_MARGINAL[:,i] = sum_u2 J[:,u2,b_i]`
- `L1_ORACLE_U2[:,i] = J[:,u2_true_i,b_i]`, normalized over u1
- `L2_MARGINAL[:,i] = sum_u1 J[u1,:,b_i]`
- `L2_ORACLE_U1[:,i] = J[u1_true_i,:,b_i]`, normalized over u2

Transpose only at the decoder boundary to the certified `(position,q)` shape.
Floor/renormalization must match the accepted D5 decoder boundary and be
applied once. Unit tests must independently calculate every formula from a
small literal joint tensor and detect swapped U1/U2/B axes.

### 3.4 Exact call matrix

`16 blocks × 2 f values × 4 conditions = 128` scientific calls.

Call order is frozen:

```text
for f in [1.0, 1.2]:
  for seed in 2026091300..2026091315:
    L1_MARGINAL
    L1_ORACLE_U2
    L2_MARGINAL
    L2_ORACLE_U1
```

Every call is attempted exactly once unless a higher-priority run stop occurs.
No early success stop and no replacement cell.

### 3.5 Budgets

- scientific calls `<=128` and exactly 128 for normal completion
- per-call watchdog `120 s`
- stored scientific wall `<=1500 s`
- outer GNU timeout `1800 s`, kill grace `30 s`
- current-process RSS known and `<2 GiB`
- WSL RSS uses stdlib `resource.getrusage(RUSAGE_SELF)` with explicit Linux
  `ru_maxrss` KiB→bytes conversion; absence/nonpositive/nonfinite measurement
  blocks before the first scientific call
- zero retry/rerun/resume

Do not add psutil as a dependency. Add unit tests for the WSL units and a fake
known-value probe.

### 3.6 Recorded scalar evidence

Per call:

- f, seed, condition, layer, rows, n;
- exact, independently recomputed syndrome_ok, iterations, finite, status;
- symbol errors and unsatisfied checks;
- wall seconds and RSS bytes;
- current-belief confidence/entropy only as explicitly labeled diagnostic;
- `beliefs_conditioned` flag determined from iterations and reviewed audit
  semantics; never call an iteration-0 prior a conditioned posterior.

Per `(f,layer)` paired comparison:

- marginal exact count /16;
- oracle exact count /16;
- oracle-only count (`oracle exact && marginal not exact`);
- marginal-only count;
- both and neither counts;
- paired syndrome and nonfinite/crash counts;
- median/max iterations and wall by condition.

No raw beliefs, symbols, priors, syndromes or block vectors are persisted.

## 4. Frozen diagnostic outcomes

For each `(f,layer)` stratum, classify:

- `STRONG_ORACLE_LIFT`: oracle-only `>=4/16`, marginal-only `<=1/16`, oracle
  exact `>=4/16`, zero crash/nonfinite;
- `NO_ORACLE_RECOVERY`: oracle exact `<=1/16` and marginal exact `<=1/16`;
- `MARGINAL_ALREADY_RECOVERS`: marginal exact `>=12/16`;
- `AMBIGUOUS_ORACLE_EFFECT`: every other finite completed case.

Run-level priority:

1. `D7_C_PRE_EXECUTION_BLOCKED`
2. `D7_C_WATCHDOG_TIMEOUT_VOID`
3. `D7_C_NONFINITE_OR_CRASH_BLOCKED`
4. `D7_C_RESOURCE_OVERRUN`
5. `D7_C_INCOMPLETE_CALL_MATRIX`
6. `D7_C_BIDIRECTIONAL_DEPENDENCE` — at least one f has strong lift for both
   L1 and L2
7. `D7_C_L1_DEPENDS_ON_U2` — strong L1 lift in at least one f, no strong L2
8. `D7_C_L2_DEPENDS_ON_U1` — strong L2 lift in at least one f, no strong L1
9. `D7_C_MARGINAL_REGION_EXISTS` — marginal already recovers in any stratum
10. `D7_C_ORACLE_NO_USEFUL_RECOVERY` — all four strata are no-recovery
11. `D7_C_MIXED_DIAGNOSTIC`

These thresholds are mechanism-routing rules, not success-rate estimates.
Record all stratum labels even when a higher-priority run terminal applies.

## 5. Required files

Create OpenSpec:

`openspec/changes/v72p2d7-gf32-bidirectional-oracle/`

Create cycle docs:

`docs/research_cycles/V72P2D7-GF32-BIDIRECTIONAL-ORACLE/`

Required:

- `D7_C_PREREG_R1.md`
- `D7_C_EXECUTION_PACKET_R1.md`
- `D7_C_IMPLEMENTATION_REVIEW_R1.md`
- `D7_C_PRE_EXECUTE_REVIEW_R1.md`
- `cycle_state.yaml`

Preferred implementation:

- new
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_bidirectional_oracle.py`
- new
  `comparison_bench/tests/test_v72p2d7_gf32_bidirectional_oracle.py`
- new `scripts/v72p2d7_gf32_bidirectional_oracle.py`

Reuse accepted D5/D7-A helpers only where their semantics are already certified.
Keep production v35, D5, D6, D7-A and D7-B modules read-only. If a missing
helper requires changing them, STOP and propose the smallest delta instead.

Future output root:

`workspace/d7_c_bidirectional_oracle_<uuid>/`

Fresh, no overwrite, no subdirectories, compact scalar text only:

- `manifest.json`
- `decoder_records.csv`
- `paired_summary.csv`
- `summary.json`
- `report.md`
- `command_log.txt`

## 6. Implementation requirements

- lazy local-source package import works from WSL repo and external cwd;
- unauthorized/import/help/dry-run bind no decoder, read no Model-F and create
  no root;
- dependency injection for joint tensor, blocks, matrices, decoder, clock and
  RSS;
- fake qualification performs all 128 calls and every terminal branch;
- no retry/resume/concurrency framework; sequential execution is sufficient;
- fail before first call if RSS unavailable or target exists;
- no scientific call may begin until accepted Model-F has loaded and all 128
  identities are frozen in memory;
- verifier independently recomputes schema, uniqueness, pair matching,
  counts/outcomes and terminal from the six files;
- verifier never calls decoder or loads Model-F.

## 7. Tests C01–C20

- C01 exact 128 identities and order
- C02 both f share the same 16 block identities
- C03 four prior formulas match literal tensor calculations
- C04 axis-swap negative controls fail
- C05 positivity/normalization/floor-once
- C06 correct L1/L2 rows and mother-prefix identity
- C07 oracle truth used only in prior construction and never persisted
- C08 marginal/oracle pairs share H, syndrome target, block and decoder config
- C09 all stratum thresholds and boundaries
- C10 all 11 run terminals and priority
- C11 128 hard cap and no retry
- C12 120/1500/1800/2GiB boundaries
- C13 WSL `resource` KiB→bytes conversion and fail-before-call
- C14 current-belief diagnostics never labeled posterior when unconditioned
- C15 six-file scalar-only schema/no subdirs/no overwrite
- C16 verifier detects duplicate/missing/unpaired/tampered scalar records
- C17 lazy import/help/dry-run/unauthorized isolation
- C18 external-cwd local-source bind sentinel reaches first decoder call with
  zero Model-F real read and zero root
- C19 protected-root lifecycle snapshots and G2/R1d absence
- C20 related D7-A/D7-B/D5 fake regression and py_compile

Use only fake joint tensors/artifacts in tests. No real Model-F content and no
production decoder calls. Use fresh task-owned basetemps; no perf-v38.

## 8. Independent reviews

### Implementation review

Independent reviewer inspects source and recomputes representative prior and
pairing cases. Allowed PASS:

`D7_C_IMPLEMENTATION_REVIEW_PASS`

One scoped rework is allowed for an implementation defect. Scientific
ambiguity returns to the main thread.

### Pre-EXECUTE

After implementation PASS, a separate reviewer checks actual WSL environment
with each probe as a separate command:

- branch/scoped commits and accepted D7-B audit dependency;
- exact 128 matrix and thresholds;
- accepted Model-F metadata/root presence but no content read;
- external-cwd package/decode sentinel and Model-F loader sentinel separately;
- live stdlib RSS positive and correct units;
- GNU timeout existence and 3-second rehearsal exit 124;
- future UUID root absent;
- unauthorized exact-shape refusal before decoder/model/root;
- tests, protected metadata, all auth false, R1d/G2 absent;
- exact future command and mandatory Pre-RESULT.

Freeze future WSL command, but do not run:

```bash
timeout -k 30 1800 python scripts/v72p2d7_gf32_bidirectional_oracle.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_c_bidirectional_oracle_<uuid>
```

Allowed PASS:

`D7_C_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`

No UUID, authorization flip, Model-F content read or scientific decoder call.

## 9. Commits and closeout

Use coherent scoped local commits:

1. OpenSpec/prereg/execution packet;
2. implementation and tests;
3. independent implementation review;
4. independent Pre-EXECUTE review and append-only closeout.

Set `next_gate: D7_C_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION` only after both
reviews PASS. All authorization false. No attempts/results/completed fields.
No push.

## 10. Acceptance matrix

- H01 deferred-start D7-B audit review PASS
- H02 reviewed audit limitation carried forward without reopening it
- H03 accepted Model-F estimator uniquely traced
- H04 prereg committed before real artifact/decoder observation
- H05 128 calls and paired identities frozen exactly
- H06 four prior formulas independently verified
- H07 oracle diagnostic/nonclaim boundary explicit
- H08 current-belief validity labeling respects D7-B audit
- H09 WSL stdlib RSS preflight prevents null telemetry
- H10 implementation uses DI/lazy binding and no generalized framework
- H11 C01–C20 PASS
- H12 related regression/compile PASS or exact unrelated baseline isolated
- H13 six-file writer/verifier qualification PASS
- H14 independent implementation review PASS
- H15 independent Pre-EXECUTE PASS
- H16 zero real Model-F content/decoder/phase/formal execution
- H17 protected roots unchanged, no D7-C/R1d/G2 root
- H18 all authorization false and no UUID generated
- H19 scoped local commits/no push/dirty tree preserved
- H20 memory triage contains only durable readiness facts

## 11. Hard STOP

STOP if the D7-B audit review is not PASS, accepted estimator is ambiguous,
implementation requires changing accepted production modules/science, real
Model-F content or decoder is reached, any protected root/auth changes, or a
review fails after one scoped rework. Do not fall through to D7-C execution.

## 12. Return

Report deltas only: deferred gate, audit outcome carried forward, estimator
trace, 128 matrix, prior formulas, implementation/schema, C01–C20, literal
tests, both reviews, WSL RSS/timeout/reachability, commits, roots/auth/no-push,
risks and next gate.

End exactly:

`D7-C bidirectional oracle 已完成冻结、实现和独立 Pre-EXECUTE；尚未授权、未执行，D7-B 根保持 immutable，R1d、G1、G2 均未授权。`

