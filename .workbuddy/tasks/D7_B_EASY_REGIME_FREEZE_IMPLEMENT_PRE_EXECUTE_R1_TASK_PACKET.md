# D7-B — easy-regime freeze, implementation and Pre-EXECUTE readiness R1

## 0. Main-thread review and ruling

The D7-A operator return has been reviewed and accepted as:

`D7_A_DECODER_CERTIFICATION_ACCEPTED`

D7-A established, within its synthetic certification scope:

- independent GF(2^5) arithmetic agrees with production for all 1024 products;
- direct check-node SP agrees with FFT-QSPA to `3.3e-16` worst case;
- tree posteriors agree to `6.7e-16`;
- small loopy row-layered recurrences agree per sweep;
- coefficient and syndrome-direction negative controls are discriminating;
- `final_beliefs` is log-domain;
- the current D5 softmax and L1→L2 APP calculation are correct within the
  tested interface contract.

The historical GF32 kernel therefore has no known foundational correctness
blocker. The next mainline question is whether it has a clear, reproducible
operating region under progressively harder but fully synthetic conditions.

This packet authorizes a strong operator to complete planning, OpenSpec,
implementation, fake/unit qualification, independent implementation review,
and independent Pre-EXECUTE review. It does **not** authorize the D7-B
development run. The operator must stop at readiness and await a separate,
verbatim user authorization.

R1d remains:

`R1D_PAUSED_PENDING_DECODER_CERTIFICATION_AND_EASY_REGIME`

No R1d, D7-C/D, formal G1/G2, or Cascade work belongs in this packet.

## 1. Baseline and dirty-tree discipline

- Repository: `D:/Code/HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- Expected starting HEAD: `f98dde08`
- Required D7-A review verdict: `D7_A_DECODER_CERTIFICATION_PASS`
- All execution authorization keys remain false
- G2 remains absent
- No D7-B development root exists
- No R1d root exists
- Existing formal, development and VOID roots are immutable and out of scope

There are known unrelated CRLF/status changes and untracked files. In
particular, the pending SOP standardization change is outside this scientific
packet:

- `docs/research-cycle-sop.md`
- `openspec/changes/standardize-task-packet-review-loop/`
- `.workbuddy/tasks/`

Do not stage, edit, delete, normalize or commit those paths. The present task
pair itself remains untracked operational input. Use explicit path manifests,
`git diff --numstat`, and scoped staged checks. Do not require global porcelain
cleanliness. Never clean/reset/checkout/stash/rebase/amend or broad-stage.

If the baseline, D7-A verdict, authorization state, or protected-root state
does not match, STOP with raw evidence.

## 2. Decision question and claim ceiling

Question:

> Does the certified historical row-layered GF32 FFT-QSPA decoder exhibit a
> deterministic, finite, resource-bounded region of correct behavior as prior
> ambiguity and graph size/loopy structure increase from analytically tractable
> fixtures to a full-rank n=64 high-disclosure graph?

D7-B is a development calibration, not a protocol benchmark. It may establish:

- existence or absence of a tested easy operating region;
- the first tested difficulty tier where exact recovery ceases;
- whether failure appears as nonfinite/crash, syndrome-only convergence,
  stable wrong fixed point, oscillation proxy, or iteration exhaustion;
- agreement with exact posterior/MAP on tractable fixtures.

It may not establish FER, leakage, reconciliation efficiency, key rate,
qualification, CAL-channel recoverability, R1d value, flooding superiority,
G2 readiness, or general NB-LDPC viability.

## 3. Frozen D7-B scientific matrix

Freeze this matrix in OpenSpec and `D7_B_PREREG_R1.md` before implementation
results or any historical-decoder calibration call is observed.

### 3.1 Constants

- Field: existing certified GF(2^5), alphabet `q=32`
- Decoder: historical `decode_row_layered_fftqspa`
- Schedule: current row-layered only
- Damping: `1.0`
- Cold start: `warm_beliefs=None`
- Iteration caps: `[1, 2, 4, 8, 16, 32, 90]`
- Per-call watchdog: `120 s`
- Development-run outer watchdog: `1800 s`, kill grace `30 s`
- Aggregate call cap: `420`
- Aggregate RSS hard limit: `< 2 GiB`; unknown RSS blocks PASS
- Seeds: fixture seeds `2026091200..2026091203`, in this order
- Numeric finite requirement: all returned beliefs and stored scalars finite
- Posterior tolerance on exact-enumeration fixtures: max abs `<=1e-10`
- Determinism: repeated identical call outputs must agree exactly for discrete
  fields and within `1e-12` for finite floating summaries
- No retry, rerun, resume, parameter change, tuning or adaptive extension

The scientific run may use fewer than 420 calls through deterministic early
completion of a cap ladder, but it must never add cells dynamically.

### 3.2 Prior families

For a frozen true symbol `x_i`, construct independent per-variable priors:

- `P99`: `P(x_i)=0.99`, remaining `0.01/31`
- `P90`: `P(x_i)=0.90`, remaining `0.10/31`
- `P60`: `P(x_i)=0.60`, remaining `0.40/31`
- `PAIR`: deterministic wrong symbol `d_i = x_i XOR 1`,
  `P(x_i)=0.49`, `P(d_i)=0.49`, remaining `0.02/30`

Every row must be positive, finite and normalized. Do not use a delta prior.
The decoder is given only the prior and exact syndrome, never `x_true`.

### 3.3 Structure tiers

All coefficients are nonzero and include nontrivial labels. Every dispatched
check row must have degree at least two. Matrices and truths are generated once
from the preregistered seeds and then frozen in a manifest before decoder
dispatch.

1. `SINGLE_CHECK_D3`: `n=3, m=1`, one degree-3 check with coefficients
   `[1,7,13]`. Exact posterior and MAP are independently enumerable.
2. `TREE_6`: `n=6, m=3`, connected acyclic Tanner graph with row degrees
   `[2,3,2]`, nontrivial labels, no isolated variable. Exact posterior and MAP
   are independently enumerable using factor elimination/direct enumeration
   with a preregistered tractability guard.
3. `CYCLE_8`: `n=8, m=8`, connected labeled cycle, every check and variable
   degree 2, full GF32 rank 8. Its syndrome uniquely determines the truth.
4. `FULL_RANK_64`: `n=64, m=64`, connected labeled cycle-like matrix, every
   check and variable degree 2, full GF32 rank 64. Construct deterministically
   and fail closed if rank or degree invariants do not hold. Its syndrome
   uniquely determines the truth.

The implementation must not search many graph seeds and select a favorable
one. One deterministic construction rule and the four frozen fixture seeds are
allowed. If the rule fails to produce the specified rank/degree property,
return `D7_B_STRUCTURE_FREEZE_BLOCKED`; do not tune labels or seeds after
seeing decoder behavior.

### 3.4 Cell schedule

The future development run contains these frozen cells:

- `SINGLE_CHECK_D3`: 4 priors × 4 seeds
- `TREE_6`: 4 priors × 4 seeds
- `CYCLE_8`: 4 priors × 4 seeds
- `FULL_RANK_64`: 4 priors × 4 seeds

For each of 64 cells, invoke cold decoder caps in ascending order
`1,2,4,8,16,32,90`. Stop that cell's cap ladder after the first cap where
`exact=true AND syndrome_ok=true`; all later caps are structurally marked
`NOT_NEEDED_AFTER_EXACT`, not invoked. If no cap succeeds, all seven calls are
made. The absolute worst case is 448, which exceeds the global cap 420;
therefore apply this preregistered global stop:

- before each call, if the next invocation would make calls `>420`, stop the
  whole run as `D7_B_CALL_BUDGET_EXHAUSTED` and write no success verdict.

Do not silently reduce cells to fit the cap. The 420 cap intentionally tests
whether at least some easy cells terminate early. The report must distinguish
scheduled, invoked, not-needed, and budget-not-reached cells.

### 3.5 Recorded diagnostics

Per invocation, store scalar-only:

- structure tier, prior family, fixture seed, n, m, rank and degree minima/maxima;
- cap, exact, syndrome_ok, iterations, status;
- unsatisfied-check count recomputed independently;
- symbol-error count against synthetic truth;
- finite flag;
- max posterior probability, mean true-symbol posterior, minimum true-symbol
  rank, and mean posterior entropy;
- change from the preceding cap for x-hat, posterior max-abs and unsatisfied
  checks;
- wall seconds and current-process RSS bytes.

For exact-enumeration tiers also store max posterior error and MAP agreement.
Do not store raw per-symbol priors, beliefs, truths or syndrome vectors in the
result root; their reproducible identities belong in the manifest as seeds,
construction names and scalar invariants.

Because cap-ladder calls restart cold, label changes as `CAP_PREFIX_PROXY`, not
as a captured internal trace. D7-A must first verify on its tiny independent
recurrence that deterministic cap-k output equals the state after k production
sweeps for the chosen fixtures. If this equivalence fails, omit trajectory
language and return a scoped blocker before the development run.

## 4. Frozen terminal classification

Apply in this priority order:

1. `D7_B_PRE_EXECUTION_BLOCKED`: provenance, structure, isolation, RSS probe,
   target-root or authorization gate fails before first scientific call.
2. `D7_B_WATCHDOG_TIMEOUT_VOID`: outer watchdog kills the run; fresh partial
   root retained VOID, attempt consumed, no retry.
3. `D7_B_NONFINITE_OR_CRASH_BLOCKED`: any invoked call crashes or returns
   nonfinite required output.
4. `D7_B_RESOURCE_OVERRUN`: RSS unknown/`>=2GiB`, any call `>120s`, or stored
   run wall `>1500s`.
5. `D7_B_CALL_BUDGET_EXHAUSTED`: the next call would exceed 420.
6. `D7_B_NO_EASY_REGIME_CORRECTNESS_ALERT`: any `P99` cell fails exact and
   syndrome by cap 90, or any tractable tier violates posterior/MAP agreement.
7. `D7_B_EASY_REGIME_CONFIRMED`: all `P99` and `P90` cells across all four
   tiers are exact+syndrome by cap 90, all tractable posterior checks pass, and
   no higher-priority terminal applies.
8. `D7_B_PARTIAL_EASY_REGIME`: no higher-priority terminal; all tractable
   `P99/P90` cells pass, and at least `3/4` FULL_RANK_64 P99 seeds pass, but the
   full confirmed condition is not met.
9. `D7_B_COMPLETED_NO_STABLE_REGION`: completed within budget/resources but
   neither confirmed nor partial condition holds.

`P60` and `PAIR` characterize the boundary and never veto
`D7_B_EASY_REGIME_CONFIRMED`. Do not introduce a posterior, FER, 50%, 90%, or
graph-family selection threshold after results are visible.

## 5. Required implementation and artifacts

Create OpenSpec change:

`openspec/changes/v72p2d7-gf32-easy-regime/`

Create cycle directory:

`docs/research_cycles/V72P2D7-GF32-EASY-REGIME/`

Required documents before stop:

- `D7_B_PREREG_R1.md`
- `D7_B_EXECUTION_PACKET_R1.md`
- `D7_B_IMPLEMENTATION_REVIEW_R1.md`
- `D7_B_PRE_EXECUTE_REVIEW_R1.md`

Preferred implementation:

- new `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_easy_regime.py`
- new `comparison_bench/tests/test_v72p2d7_gf32_easy_regime.py`
- new `scripts/v72p2d7_gf32_easy_regime.py`

Reuse the accepted D7-A independent oracle rather than rebuilding it. Do not
modify the D7-A oracle unless an independently reviewed defect is found; such a
defect is a STOP and requires a separate addendum.

Production v35 and D5 modules are read-only for this task. No trace hook,
schedule change, damping change, algorithm optimization, graph search,
flooding implementation, bidirectional oracle or Model-F wiring is allowed.

The future execution root pattern is:

`workspace/d7_b_easy_regime_<uuid>/`

It must be fresh, refuse overwrite, contain no subdirectories, and contain
only compact text artifacts:

- `manifest.json`
- `decoder_records.csv`
- `summary.json`
- `report.md`
- `command_log.txt`

The implementation must support dependency injection so all qualification
tests use fake decoders or D7-A tiny references. Importing, `--help`, dry-run,
and unauthorized execution must bind no historical decoder and create no root.

## 6. Future execution command and authorization lifecycle

Freeze this command shape, but do not run it in this task:

```powershell
& 'C:\Program Files\Git\usr\bin\timeout.exe' -k 30 1800 python scripts/v72p2d7_gf32_easy_regime.py --out-root workspace/d7_b_easy_regime_<uuid>
```

The implementation must fail before work unless a dedicated D7-B execution
authorization is true through the accepted lifecycle mechanism. A future user
authorization permits exactly one invocation with one UUID and consumes on the
first historical-decoder attempt, regardless of success. No retry, rerun,
resume or reuse.

Pre-RESULT review will be mandatory before any result root or operator return
is committed. This packet authorizes no execution and no result acceptance.

## 7. Ordered work plan

### T0 — Baseline/read-only audit

Verify §1, read D7-A OpenSpec/oracle/report/review, v35 decoder, D5 adapter and
existing tests. Inventory existing roots by names/sizes/mtime only. Do not read
VOID contents. Record scoped dirty paths and explicitly exclude SOP/workbuddy
administrative changes.

### T1 — OpenSpec and prereg freeze

Write OpenSpec, `D7_B_PREREG_R1.md`, exact fixture-construction rules, cell
manifest template, classification and execution packet before observing any
new production-decoder result. Independently prove each proposed structure's
rank and degree properties without calling the decoder. Commit this planning
layer locally with explicit paths; no push.

### T2 — Minimal implementation

Implement deterministic fixture construction, prior construction, cap ladder,
diagnostic recomputation, budget/resource enforcement, five-file writer,
no-overwrite and verify mode. Keep it local-research-simple. Do not add hashes,
locks, retries, resume, generalized experiment frameworks or custom caches.

### T3 — Qualification tests

Add tests for:

- exact 64-cell schedule and 420 hard cap;
- all prior formulas, positivity and normalization;
- deterministic truth/matrix generation and rank/degree invariants;
- D7-A exact posterior reuse on tractable fixtures;
- cap-ladder ordering and early stop;
- scheduled/invoked/not-needed/budget-not-reached accounting;
- every terminal priority and boundary (`120s`, `1500s`, `2GiB`, 420 calls);
- cap-prefix proxy equivalence on tiny fixtures;
- fake success, partial, no-region, crash, nonfinite, timeout-marker and budget
  paths;
- scalar-only five-file schema and independent verifier recomputation;
- unauthorized/import/help/dry-run create no root and bind no historical decoder;
- no Model-F/CAL/VAL/real/raw/formal/VOID access;
- protected-root lifecycle snapshots including no-subdirectory invariants.

Run py_compile, focused D7-B tests, D7-A regression, related D5/v35 fake tests,
and one established non-perf milestone suite. Do not run perf-v38.

### T4 — Independent implementation review

Use an independent reviewer context. It must inspect source, independently
recompute representative matrices/priors/call arithmetic/terminal cases, and
confirm no scientific decoder calls occurred. Allowed verdict:

`D7_B_IMPLEMENTATION_REVIEW_PASS`

or a precise FAIL/BLOCKED verdict. One bounded implementation rework is allowed
for a concrete defect, followed by focused re-review. Do not alter frozen
science; ambiguity returns to the main thread.

### T5 — Independent Pre-EXECUTE review

After implementation review PASS, independently check:

- branch and scoped commits;
- D7-A accepted dependency;
- exact 64 cells, seeds, priors, cap ladder, 420/1500/1800/120/2GiB limits;
- historical decoder reachability from the real script-launch environment;
- live Windows RSS is positive integer;
- `timeout.exe` exists and a 3-second rehearsal exits 124;
- new UUID target is absent;
- five-file no-overwrite behavior;
- all authorization keys false and unauthorized CLI refusal before work;
- protected roots unchanged and G2/R1d roots absent;
- exact future command and mandatory Pre-RESULT boundary.

The real reachability probe must be outside the repository, run with repository
root absent from `sys.path`, use a sentinel at the first historical-decoder
call, write only a fresh probe-owned temp directory, and prove it remains
empty. It must not make a scientific decoder call.

Allowed PASS verdict:

`D7_B_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`

This verdict is readiness only and cannot flip authorization or run D7-B.

### T6 — Closeout and stop

Land OpenSpec/task completion, implementation and two review documents in
coherent scoped local commits. Append durable implementation/readiness facts to
decision log and project memory only if they are not already represented by
the closeout. Do not update a result/attempt/completed field. Set the documented
next gate to `D7_B_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION` only after both
reviews pass.

Then STOP. Do not ask an agent to self-authorize; return to the user/main thread.

## 8. Acceptance matrix

- B01 baseline D7-A PASS and protected state verified
- B02 OpenSpec/prereg frozen before decoder observations
- B03 64 cells and deterministic structure/prior identities frozen
- B04 rank/degree/connectedness invariants independently established
- B05 420-call cap and cap-ladder early-stop accounting exact
- B06 scalar diagnostics and cap-prefix-proxy label correct
- B07 terminal priority implemented exactly
- B08 tractable posterior/MAP oracle uses accepted D7-A reference
- B09 implementation is injected/testable and production decoder is lazy
- B10 unauthorized/help/import/dry-run produce no root or decoder binding
- B11 five-file schema, verify and no-overwrite behavior pass
- B12 time/RSS/call boundaries and edge cases pass
- B13 protected-root lifecycle guards and no-subdirectory checks pass
- B14 py_compile/focused/regression/milestone tests pass or exact unrelated
  baseline failure is isolated without weakening tests
- B15 independent implementation review PASS
- B16 independent Pre-EXECUTE review PASS
- B17 all authorization false, no scientific decoder calls, R1d/G2 absent
- B18 scoped local commits only, no push, unrelated dirty tree preserved
- B19 memory triage completed
- B20 final state awaits explicit user authorization and makes no result claim

## 9. Hard STOP rules

STOP without broad repair, execution or continuation if:

- baseline/D7-A verdict/branch/protected state differs;
- the deterministic matrix rule cannot satisfy the frozen structure invariants;
- the D7-A oracle requires correction;
- a production decoder is reached during implementation or tests outside the
  explicit tiny D7-A correctness fixtures;
- Model-F, CAL, VAL, real/raw, formal or VOID content would be read;
- any `--phase`, R1d, G1 or G2 would run;
- a scientific threshold, prior, seed, structure tier or schedule needs change;
- an unlisted production file needs modification;
- the implementation or Pre-EXECUTE review fails after one scoped rework;
- any protected root or authorization key changes;
- scope cannot be separated from the unrelated dirty tree.

Report the exact failing ID, command/output, completed deltas, and the one
main-thread decision required. Do not improvise a replacement experiment.

## 10. Return format

Report deltas only:

1. starting/final HEAD and scoped commits/manifests;
2. OpenSpec/prereg and exact 64-cell/call arithmetic;
3. implementation files and five-file schema;
4. rank/degree and fixture invariants;
5. B01–B20 table;
6. literal compile/test lines and failing IDs;
7. fake terminal/boundary matrix;
8. independent implementation-review verdict;
9. independent Pre-EXECUTE verdict, reachability/RSS/watchdog evidence;
10. roots/auth/G2/R1d/no-push status;
11. risks and the exact next gate.

End exactly:

`D7-B easy-regime 已完成冻结、实现与独立 Pre-EXECUTE 评审；尚未授权、未执行，R1d 继续暂停，G1/G2 均未授权。`

