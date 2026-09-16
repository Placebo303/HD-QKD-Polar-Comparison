# D6 R1c-A3 — post-run verifier and terminal rework

## 0. Status and authority

The sole R1c-A2 §8 authorization is consumed. No decoder execution is
authorized by this packet. The immutable development root is:

`workspace/d6_graph_mother_r1c_dd8c4defe67742a8b2bc1b634c116d6b`

The A2 Pre-RESULT verdict is `D6_R1C_A2_PRE_RESULT_REVIEW_FAIL`. Result
solidification remains blocked. This packet authorizes only OpenSpec,
implementation/test work on post-run verification/classification, mechanical
verification of the existing root, independent review, and bounded analysis.

Return only when complete or on one concrete blocker. Never retry, resume, or
run a scientific decoder.

## 1. Baseline and decisive findings

- Branch: `formal-ir-v72p1-addendum-clean`
- Expected HEAD: `047e6d62`
- Authorization commit: `85c554ac`
- Revocation commit: `047e6d62`
- All authorization keys false; G2 absent; no push
- Existing six-file root is immutable and uncommitted
- Existing verifier was invoked once and returned exit 1:
  - `semantic-key-no-dup` FAIL because its key omits `n`
  - `scaling-recompute` FAIL because its cell key omits `n` and mixes canary
    with scaling seeds/widths
- Records additionally contain 64 `crash=True`, `finite=False` rows with
  `ValueError('Check node requires degree >= 2')`, while stored terminal is
  `D6_GRAPH_TOPOLOGY_NO_USEFUL_RECOVERY`. This is a mandatory independent
  terminal-semantics audit, not a non-blocking observation.

## 2. Hard boundaries

Allowed production files:

- `scripts/v72p2d6_graph_mother_development.py`

Allowed tests:

- `comparison_bench/tests/test_v72p2d6_gf32_graph_mother.py`

Allowed specification/docs:

- the existing `v72p2d6-gf32-graph-mother-r1` OpenSpec change
- new R1c-A3 prereg/review/result documents under the D6 cycle directory
- append-only decision log and project memory, but only after final review

Forbidden:

- every real/fake production decoder call outside unit tests with explicit
  fakes; any `--phase`; formal G1/G2; VAL/real/raw; any new scientific sample
- modifying, deleting, rewriting, or regenerating any file in the immutable
  R1c-A2 root
- changing arms, rows, seeds, priors, graphs, decoder settings, selection
  thresholds, budgets, or the historical execution record
- slow-arm optimization, P0 performance work, or a successor algorithm in this
  task
- broad staging, cleanup, push, reset, stash, checkout, rebase, amend

## 3. A3-01 — freeze the post-run contract before code

Create and commit separately:

- `docs/research_cycles/V72P2D6-GF32-GRAPH-MOTHER/D6_GRAPH_MOTHER_PREREG_R1C_A3.md`
- an A3 delta in `R1C_parallel_revision.md`
- A3 tasks in the existing OpenSpec `tasks.md`

Freeze these rules:

1. Scientific semantic identity is `(n, arm, seed, point, mode)`; `call_idx`
   remains independently continuous.
2. Canary recomputation uses only `n=64` and canary seeds.
3. Scaling recomputation uses only scaling seeds and is grouped separately by
   `n=128` and `n=256`; it must reproduce fallback selection, stop-at-first-
   signaling-width, advancing arms, confirmation width, and terminal inputs.
4. Confirmation recomputation uses only confirmation seeds at the selected
   width and must not silently treat an empty confirmation stage as safe
   evidence.
5. Any actual attempted-cell process/invariant crash or nonfinite result has
   blocking precedence over recovery/no-recovery scientific labels. Skipped
   placeholders with `call_idx=-1` are not attempted cells.
6. `ValueError('Check node requires degree >= 2')` must be classified from the
   immutable evidence as an implementation/structure invariant failure unless
   a preregistered scientific outcome explicitly allowed that row. It must not
   support a topology-no-recovery claim.
7. The verifier must be pure read-only over an arbitrary supplied root. It may
   not rewrite summary/manifest to make them agree.
8. Existing A2 evidence remains tied to commit `15f1de79`; a post-run verifier
   revision must report both stored and independently recomputed terminal.

## 4. A3-02 — independent forensic reconstruction before implementation

Before editing code, create a small task-owned analysis script or notebook
under a fresh non-formal workspace root and independently reconstruct all 184
rows. Do not edit the evidence root.

Report:

- uniqueness under old and corrected keys;
- exact duplicate groups under the old key;
- counts by `(n, arm, seed, point, mode)`;
- attempted/crash/nonfinite/error counts by width and arm;
- canary, scaling-n128, scaling-n256, and confirmation stage partitions;
- selection/advancement/stop-width recomputation;
- stored terminal versus recomputed terminal under A3 rules;
- whether the 64 degree failures originate in invalid frozen graph structure,
  serialization, worker transport, or decoder precondition. Use existing
  structure/scalar evidence and code only; no decoder calls.

If the evidence is insufficient to distinguish the degree-failure source,
label it `NOT_VERIFIABLE` but keep the terminal blocked. Do not guess.

## 5. A3-03 — minimal implementation and tests

Implement the smallest correction in the verifier/classifier path. Do not
change execution generation or historical artifacts unless a shared helper is
the only scientifically correct location; any shared change must preserve
execution behavior byte-for-byte and be proved by tests.

Tests must include:

- same arm/seed/point/mode at n128 and n256 is valid and unique with `n`;
- a true duplicate including identical `n` fails;
- canary rows cannot be contaminated by scaling rows;
- n128/n256 scaling stages are independently reconstructed in order;
- empty confirmation is not mistaken for observed zero-crash confirmation;
- attempted crash/nonfinite overrides topology-no-recovery;
- skipped placeholders do not count as crashes or calls;
- stored/recomputed terminal disagreement is fail-closed;
- immutable A2 six-file fixture or a faithful tiny copy reproduces both old
  FAILs before the fix and the corrected classification after it;
- verifier does not mutate its root.

Use explicit fakes and fresh task-owned basetemp. No real decoder.

## 6. A3-04 — code review and tests

Run py_compile, focused D6 tests, and the established seven-file non-perf
regression grouping. Do not run perf-v38 unless a scoped code dependency makes
it materially necessary; record that choice.

Obtain an independent code review. It must verify the A3 prereg against code,
tests, and the forensic reconstruction. Reviewer edits only its own review
file. Any blocking finding returns to implementation at most once; otherwise
STOP.

Commit prereg/OpenSpec separately from implementation/tests, then commit the
independent review separately. No push.

## 7. A3-05 — verify the immutable A2 root

After review PASS, run the corrected mechanical verifier exactly once against:

```powershell
python scripts/v72p2d6_graph_mother_development.py --out-root workspace/d6_graph_mother_r1c_dd8c4defe67742a8b2bc1b634c116d6b --verify
```

This is read-only and must make zero decoder calls. Capture full output and
exit. If it fails, STOP; do not patch again in the same evidence cycle and do
not rerun verify.

## 8. A3-06 — independent Pre-RESULT re-review

Obtain a new independent read-only review in:

`D6_GRAPH_MOTHER_PRE_RESULT_REVIEW_R1C_A3.md`

It must not inherit the old conclusion blindly. It must independently verify
the corrected keys/stages, all 184 records, crash/nonfinite precedence,
stored-versus-recomputed terminal, call/wall/RSS/no-retry accounting,
six-file immutability, protected roots, all authorization keys false, and G2
absence.

Allowed verdicts:

- `D6_R1C_A3_PRE_RESULT_REVIEW_PASS_BLOCKED_RUN`
- `D6_R1C_A3_PRE_RESULT_REVIEW_PASS_SCIENTIFIC_RESULT`
- `D6_R1C_A3_PRE_RESULT_REVIEW_FAIL`

The first verdict is expected if degree failures invalidate the scientific
terminal. PASS_BLOCKED_RUN permits solidifying the run as an implementation/
structure-blocked development attempt, not as topology evidence. FAIL blocks
all solidification. No verdict authorizes rerun or successor execution.

## 9. A3-07 — closeout after review

If FAIL: keep evidence uncommitted and immutable, report blocker, stop.

If PASS_BLOCKED_RUN or PASS_SCIENTIFIC_RESULT:

- update the operator return with an append-only A3 correction section; never
  erase the original verifier failure or stored terminal;
- create `D6_GRAPH_MOTHER_RESULT_R1C_A3.md` distinguishing stored versus
  recomputed terminal and the strongest allowed claim;
- commit the immutable six files, operator return, A2 FAIL review, A3 review,
  A3 result, factual D6 state, and append-only memory/log in one scoped
  evidence commit;
- keep every authorization false, G2 absent, and set the next gate to a
  main-thread route decision appropriate to the recomputed terminal;
- do not mark result accepted and do not push.

## 10. A4 — structure/scaling performance rework after A3 closeout

After A3 is fully reviewed and committed, continue autonomously with a
separate performance track. A4 is implementation-only and authorizes zero
decoder calls. It must have its own OpenSpec/prereg, implementation commit,
tests/benchmarks, and independent review. Never mix A4 code into the A2 root's
interpretation or A3 evidence commit.

### A4-01 Profile first

Use structure-only calls and the immutable command-log timings to attribute
wall by width, arm, layer, builder, replay, and audit. Run a bounded profiler
outside formal roots. Freeze a baseline table before optimization. The table
must separately expose:

- support/mother construction;
- determinism replay;
- prefix audits, girth, cycle and rank work;
- n64 initial structure work;
- n128/n256 scaling-only structure work;
- process-pool startup/serialization overhead.

No decoder, Model-F payload, or scientific output root is needed.

### A4-02 Required optimization targets

Implement the smallest scientifically equivalent changes that address all
three targets below:

1. **Scaling arm pruning:** after n64 blind selection freezes `best_T` and
   `best_M`, n128/n256 scaling may build only the frozen fallback arms actually
   eligible for scaling. It must not rebuild T2 or any other arm that cannot be
   dispatched at that width. Preserve n64 all-eight-arm structural selection.
2. **Remove triple construction replay:** current structure workers perform
   `build_mother`, `build_support`, then `build_mother` again. Refactor to at
   most two support constructions per `(n,arm,layer)`: one primary support,
   deterministic H construction from that exact support, and one independent
   support replay. Do not weaken determinism equality. If a cheaper proof gives
   the same guarantee, preregister and test it before use.
3. **Avoid repeated audits:** compute prefix-independent data once and reuse it;
   compute each prefix-dependent metric once per unique `(H,prefix)`. Eliminate
   diagnostic rebuilds such as window-overflow replay when the primary builder
   can return the exact diagnostic directly. Do not change metric definitions,
   eligibility, ordering, or selected arms.

Treat T2's combinatorial builder as a special hotspot. Optimize it only if it
remains material after scaling pruning; do not replace its frozen choice key or
search semantics merely to gain speed.

### A4-03 Equivalence gates

Before deleting the reference path, compare old and optimized paths on all
eight arms, both layers, and n64; compare every scaling-reachable arm at n128
and n256. Require exact equality for support, H, structural records, eligibility,
ordering, selected/fallback arms, and terminal inputs. Timing improvements do
not excuse one changed scientific scalar.

Add tests that fail if:

- a non-fallback arm is built during scaling;
- T2 is built at n128/n256 when it was not a frozen fallback;
- support/H replay equality is weakened;
- any audit is recomputed unnecessarily;
- sequential and parallel paths differ;
- worker-count/RSS/wall/call-budget behavior changes.

### A4-04 Performance acceptance

Use fresh structure-only benchmark roots. Report cold and warm wall separately.
Minimum acceptance:

- n128+n256 scaling structure wall improves by at least 3x relative to the
  frozen A4 baseline, or return `PERF_TARGET_NOT_MET` with profile evidence;
- n64 outputs remain exactly equal and n64 wall does not regress by more than
  10%;
- peak aggregate RSS remains below 2 GiB;
- all focused and established non-perf regression tests pass;
- production decoder calls remain exactly zero.

Do not falsify a speedup by omitting required work from the comparison. A
structure-only benchmark may run for up to 3 hours total; own and identify its
processes. No retry framework.

### A4-05 Deliverables

Create:

- A4 performance prereg/OpenSpec delta;
- a machine-readable baseline/after timing table in a fresh development-only
  workspace root;
- `D6_GRAPH_MOTHER_PERFORMANCE_R1C_A4.md`;
- independent `D6_GRAPH_MOTHER_PERFORMANCE_REVIEW_R1C_A4.md`.

Commit OpenSpec, implementation/tests, benchmark evidence/report, and review
in separate scoped commits. Update memory/log only after independent PASS.
Final state is `READY_FOR_FUTURE_D6_PRE_EXECUTE_REVIEW` or
`PERF_TARGET_NOT_MET`; neither authorizes another run. Do not request execution
authorization inside the operator return.

## 11. Return

Report only deltas: A3 commits/files, forensic table, tests, corrected verifier
output, A3 verdict, stored versus recomputed terminal and strongest claim;
then A4 profile, exact optimizations, equivalence matrix, benchmark before/after,
performance verdict, commits/review; finally protected-root equality,
authorizations, G2 absence, zero decoder calls in A3/A4, and no push.

End exactly:

`D6 R1c-A2 的历史执行未重跑；A3 已修复并独立复核后置 verifier/终局语义，现有根保持 immutable；结果仍待主线程裁决，G2 未授权、未执行。`
