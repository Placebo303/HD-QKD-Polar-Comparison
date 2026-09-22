# D6 R1c-A6 — structure-path performance: exact-key T2 acceleration and slow-task inventory

> **SUPERSEDED (2026-09-09):** absorbed in full by
> `D6_R1C_A5A6_VALIDITY_REPAIR_AND_PERF_TASK_PACKET.md` (merged A5+A6 run).
> Retained for traceability only — do not execute from this file.

Status: `FROZEN_TASK_PACKET_R1C_A6` (zero decoder; implementation-only track)
Branch: `formal-ir-v72p1-addendum-clean`
Expected starting HEAD: the accepted R1c-A5 closeout commit (see §0)
Predecessor: `D6 R1c-A5` closeout (validity closure + repair study + R1d readiness)

## 0. Authority and sequencing

- Zero decoder calls. No `--phase`, G1, G2, VAL, real/raw, no scientific sample,
  no new scientific root, no run authorization, no acceptance, no push.
- **Sequence after A5.** A5 and A6 touch the same D6 module, runner and test
  file. If the A5 closeout commits are not present at start, run only §5
  (read-only inventory) and return; do not start §3/§4 code work.
- A4 already removed the historical bottleneck (scaling-arm pruning, two-build
  replay, overflow passthrough): scaling structure 10897.7 s -> 2.5 s, n64
  42.2 s -> 21.0 s, non-T2 n256 total 1.5 s. A6 must not regress any of that.
- This packet changes builder **internals only**. Every persisted output
  (support array, H, `structure_records.csv` row, `selected_arms.json`,
  structural ordering, eligibility) must remain bit-identical to the accepted
  reference for every `(arm, n, layer)`.

## 1. The remaining bottleneck, with numbers

`_build_T2_support` (nested loops in
`comparison_bench/src/comparison_bench/formal_ir/v72p2d6_gf32_graph_mother.py`)
enumerates, per variable, every unused base pair in `B = [0, k_min)` crossed with
every expansion in `C = [0, m_max)` and evaluates a 6-field lexicographic key
`(four, mpair, cur_incid, rmax_tmp, rsumsq_tmp, sorted_triple)` for each.

| width | candidates/variable | total candidates | measured wall/layer | A4 profile |
|---|---|---|---|---|
| n64 | 72,912 | 4.67e6 | ~41 s | T2 tasks 41.4 + 31.6 s = 73 s CPU |
| n128 | 598,878 | 7.67e7 | ~650 s | T2 tasks 656.8 + 494.6 s |
| n256 | 4,853,940 | 1.24e9 | ~2.85 h | T2 tasks 10255.7 + 7820.7 s |

Main-thread micro-benchmark (`workspace/mainthread_a5_audit_7f3c1d9ab2e54a6f8c0d1e2f3a4b5c6d/t2_cost_model.py`):
per-candidate full-key evaluation ~1.45 us in isolation, ~8.3–8.9 us in the real
loop (the `affected` set update dominates); the `four`-only prefix costs 0.27 us,
i.e. **5.3x cheaper**, and vectorized enumeration is cheaper still.

Why this matters beyond n64's 21 s: the A4 pruning only excludes T2 from scaling
because T2 was not a frozen fallback. T2 minimizes four-cycles first, so a
repaired (A5) T2 is a plausible `best_T`. If it becomes the frozen fallback, the
2.85 h/layer cost returns and the run cannot finish inside the frozen chunk
budget (`>= 5400 s` blocks further dispatch). A5-10 flags this; A6 removes it.

## 2. Equivalence principle (why an exact rewrite is provable)

The candidate set is fixed by `used_pairs` / `used_triples`; the key ends with
the sorted triple, which uniquely identifies a candidate (base pairs come from
`B[i]`, `B[i+1:]` with `B` numerically sorted, and `e != b1, b2`). Therefore the
lexicographic argmin is **unique and order-independent**: any implementation that
evaluates the exact key over exactly the same candidate set selects exactly the
same triple, in exactly the same greedy order. Order-independence is the licence
to vectorize and to filter in stages; it is not a licence to change the key, the
tie-break, the candidate set, or the greedy order.

## 3. A6-01 — profile first, freeze the baseline

- Fresh task-owned root; structure-only; workers as frozen (18) and also
  `workers=1` for per-task attribution.
- Per `(n, layer)` for T2: candidate counts, per-variable wall distribution,
  `affected`-update share, GC/allocation share, peak RSS.
- Per arm at n64 and per fallback at n128/n256: the A4 baseline shape for
  regression comparison.
- Freeze the baseline table in the prereg commit before touching code.

Acceptance: A6-A01 baseline table frozen and reproducible.

## 4. A6-02/A6-03 — implement and prove

Allowed techniques (exact, no approximation):

- staged lexicographic filtering: compute `four = total_four + sum(occ)` for all
  candidates first (cheap, vectorizable), then evaluate `mpair`, `cur_incid`,
  `rmax_tmp`, `rsumsq_tmp`, `sorted_triple` only for candidates tied on the
  minimal prefix;
- vectorized candidate enumeration over `(b1, b2, e)` with integer-encoded
  `used_pairs`/`used_triples` membership (no per-candidate tuple allocation in
  the filter stage);
- incremental maintenance of `pair_counts`, `pair_to_cols`, `inc_per_col`,
  `total_four`, `max_pair`, `incid_max`, and the degree arrays;
- avoiding the `affected` set rebuild for candidates eliminated at an earlier
  key stage.

Forbidden: changing the key, its field order, tie-breaks, the candidate set, the
greedy variable order, or the frozen knobs; float approximations of an integer
key; any heuristic shortlist (top-K by degree etc.) that is not proven to
preserve the exact argmin; caching across different `(n, layer)` that could
change results; touching `d5`/`v35`/`src`/`experiments`/`tools`.

Equivalence gates (all must pass):

1. support-array equality for all 8 arms x 2 layers x {64, 128, 256} against the
   reference builder (the n256 T2 reference run may be performed once, up to
   2.85 h, inside a 4 h total structure-only budget; document it);
2. per-variable chosen-triple trace equality for T2 at every width;
3. `structure_records.csv` rows for the committed R1c-A2 n64 evidence
   byte-identical (existing `r1c_a4_equivalence_committed_n64` plus a T2-specific
   test);
4. structural ordering, eligibility flags and `selected_arms.json` unchanged;
5. determinism replay still equal; parallel and sequential paths equal;
6. no change to the exactly-two-constructions property or the A4 pruning.

Performance acceptance (fresh roots, cold and warm, A4 protocol):

- T2 per-layer wall: n64 <= 5 s, n128 <= 90 s, n256 <= 600 s (target >= 10x
  overall; report the measured factor);
- n64 all-8 build <= 8 s (from 21.0 s);
- non-T2 arms: no regression > 10%; scaling fb-only wall stays within 2x of
  the A4 after-side (2.5 s / 2.7 s);
- peak aggregate RSS < 2 GiB; zero decoder calls; no retry framework;
- if the >= 10x target is not met, return `PERF_TARGET_NOT_MET` with the profile
  and the exact remaining hot loop, and keep the reference path intact.

Tests must fail if: the key or tie-break changes; a candidate is skipped that
the reference would evaluate; the greedy order changes; sequential/parallel
differ; T2 outputs differ from the committed evidence; the A4 guards regress.

## 5. A6-04 — repo-wide slow-task inventory (read-only, no implementation)

Measure and tabulate the other known slow items so the next performance decision
is evidence-based, not anecdotal. At minimum:

- v38 suite: T0 default lane, T1 cold/warm, and the residual hot spot (lane-A
  construction ~20 s = ~3.78M tiny `compute_gf32_rank` calls) — note that
  perf-v38 already delivered 1.87x on the full file (1513 s -> 807 s);
- the two orchestration tests (~340 s each after perf-v38);
- the D6/D5 structure helpers (`audit_prefix` GF32 rank, `compute_girth`,
  `_build_M_support` pair enumeration, `build_dv3_nested_support`);
- the V30R-style DE/decoder phases (74.8 s DE, 719.9 s decoder) and any other
  recorded heavy command in the cycle docs;
- anything else the operator finds with a concrete measured wall.

Deliver a prioritized menu with: measured wall, hot symbol, suspected cause,
expected gain, risk to frozen semantics, and whether it needs OpenSpec. **Do not
implement any of it in this packet** unless it is the D6 T2 work above.

Acceptance: A6-A04 menu with measured numbers for every listed item.

## 6. A6-05 — review, report, closeout

- Independent read-only code review (reviewer edits only its own file) of the
  prereg against implementation, tests, equivalence evidence and benchmark
  arithmetic; one rework round maximum.
- Report: `D6_GRAPH_MOTHER_PERFORMANCE_R1C_A6.md` (baseline vs after, cold/warm,
  equivalence matrix, remaining hot loop, inventory menu).
- Commits: prereg/OpenSpec, implementation+tests, benchmark/report, review,
  then append-only memory/decision-log after review PASS. Exact-path staging,
  no push, no acceptance.
- Update `cycle_state.yaml` `next_gate` to
  `D6_GRAPH_MOTHER_R1D_READY_AWAITING_MAIN_THREAD_AUTHORIZATION` (or the
  A5-appropriate variant) without changing any authorization key.

## 7. Return contract

Report deltas only: baseline and after tables; the exact techniques; the
equivalence matrix (array/trace/records/selection/replay); measured speedups
versus the targets; RSS/decoder-call/no-retry accounting; the inventory menu;
the review verdict; protected-root and authorization state; commits; and the
A6-A01..A6-A08 table.

End exactly:

`D6 R1c-A6 结构路径性能收口完成并独立复核：T2 精确等价加速达成（或 PERF_TARGET_NOT_MET 并附热点证据），A4 收益未回退，全程零 decoder 调用，未授权任何 run，不 push。`
