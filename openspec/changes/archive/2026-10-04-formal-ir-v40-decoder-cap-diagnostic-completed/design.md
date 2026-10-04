# OpenSpec Design: formal-ir-v40-decoder-cap-diagnostic

**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`
**Cycle**: `V40P0`
**Predecessor**: V39P0, terminal `V39_NO_ROBUST_ROUTE_SIGNAL`, lifecycle
`DEVELOPMENT_RESULT_ACCEPTED`, result SHA
`940bfc996a0bd87d60e958150c4f770ee35f16b8`, implementation/execution SHA
`90d2d834c136833000ad612adfd8e09bf815d5d2`, accepted plan
`8efb626ba0eaa6b031abd934ed583739ba70065b`.

## 1. Scientific question (single)

How much of the V39 Lane B/C failure is attributable to the decoder
iteration cap (`max_iter=30`)? The diagnostic immediately routes the
budget: retain Lane B/C at one fixed extended setting only on a strong
signal; otherwise stop the decoder-parameter direction and invest in
protograph/MET structure design.

## 2. Predecessor binding and committed inputs

All inputs are read-only:

- Paired comparison authority:
  `comparison_bench/outputs_comparison/formal_ir_methods/v39_lanec_robustness_laneb_control/run_01/v39_paired_comparison.json`
  (45 pairs).
- Summary authority:
  `.../v39_lanec_robustness_laneb_control/run_01/v39_summary.json`
  (aggregates incl. `by_construction_seed_ordinal`).
- Structural authority (unchanged from V38P0/V39):
  `comparison_bench/outputs_comparison/formal_ir_methods/v38_architecture_triage/run_01/v38_structural_prototypes.json`
  (27 records; lanes b/c subset = 18).
- V25 TRAIN counts: read-only via accepted
  `load_v25_channel_counts()` (provenance recorded in summary).

The V39 run_01 lifecycle is `DEVELOPMENT_RESULT_ACCEPTED` (result SHA
`940bfc996a0bd87d60e958150c4f770ee35f16b8`); its evidence stands and no
V39 review precondition applies. V40 `EXECUTE_AUTH` requires only V40's
own independent plan ACCEPT plus explicit user authorization.

## 3. Frozen instance set (mechanically extracted)

Extraction rule: take every pair with `discordance_label == "NEITHER_EXACT"`
from the paired-comparison authority, in file order; within each pair emit
the lane_c instance then the lane_b instance. Exactly **6 pairs / 12
instances** exist; all are source `1M`. Any drift from the table below is
integrity failure J1.

| idx | pair | lane | ordinal | construction_seed | block_seed | matrix_id | errors_initial (V39) | errors_final (V39) | exact_l2 (V39) |
|---|---|---|---|---|---|---|---|---|---|
| A01 | P1 | lane_c | 1 | 383101 | 390101 | lane_c_1M_s383101 | 252 | 139 | false |
| A02 | P1 | lane_b | 1 | 382101 | 390101 | lane_b_1M_s382101 | 252 | 127 | false |
| A03 | P2 | lane_c | 1 | 383101 | 390103 | lane_c_1M_s383101 | 274 | 196 | false |
| A04 | P2 | lane_b | 1 | 382101 | 390103 | lane_b_1M_s382101 | 274 | 79 | false |
| A05 | P3 | lane_c | 2 | 383102 | 390101 | lane_c_1M_s383102 | 252 | 171 | false |
| A06 | P3 | lane_b | 2 | 382102 | 390101 | lane_b_1M_s382102 | 252 | 198 | false |
| A07 | P4 | lane_c | 2 | 383102 | 390102 | lane_c_1M_s383102 | 258 | 75 | false |
| A08 | P4 | lane_b | 2 | 382102 | 390102 | lane_b_1M_s382102 | 258 | 77 | false |
| A09 | P5 | lane_c | 2 | 383102 | 390103 | lane_c_1M_s383102 | 274 | 195 | false |
| A10 | P5 | lane_b | 2 | 382102 | 390103 | lane_b_1M_s382102 | 274 | 97 | false |
| A11 | P6 | lane_c | 3 | 383103 | 390101 | lane_c_1M_s383103 | 252 | 184 | false |
| A12 | P6 | lane_b | 3 | 382103 | 390101 | lane_b_1M_s382103 | 252 | 220 | false |

Frozen reference residuals: lane_c side median = (171+184)/2 = **177.5**;
lane_b side median = (97+127)/2 = **112.0**; pooled 12-instance median =
(139+171)/2 = **155.0**. Minimum reference residual is 75 (> 0), so the
improvement denominator of Section 6 can never be zero for this frozen
set (asserted as integrity check J2).

"Rescue" (救回) definition, frozen: an instance is *rescued in phase P* iff
its V39 run_01 record has `exact_l2 == false` AND its phase-P record has
`exact_l2 == true`, for the same `(lane, source, construction_seed_
ordinal, block_seed)` and identical `errors_initial`.

## 4. Representative matrices (rule resolved against actual data)

Frozen selection rule: per lane, take the `by_construction_seed_ordinal`
overall `exact_count` from the V39 run_01 summary; pick the highest;
break ties by lowest ordinal.

Actual values: lane_c ordinals 1/2/3 = 11/12/10 → unique max **ordinal 2**.
lane_b ordinals 1/2/3 = 10/11/10 → unique max **ordinal 2**. The tie rule
is not exercised by the real data but is implemented and unit-tested.

Resolved representative matrices (written into the spec as constants):

- **lane_c = ordinal 2**: `lane_c_1M_s383102`, `lane_c_1p5M_s383202`,
  `lane_c_2M_s383302`.
- **lane_b = ordinal 2**: `lane_b_1M_s382102`, `lane_b_1p5M_s382202`,
  `lane_b_2M_s382302`.

Interpretation note (frozen): prototypes are source-specific (H row count
184/190/192), so "one matrix per lane" is dimensionally impossible across
three sources. The rule therefore selects one representative *ordinal* per
lane; each probe block is decoded with its own source's matrix at that
ordinal. Six distinct matrices total. The implementation recomputes the
argmax from the committed summary at preflight and asserts equality with
these frozen constants (J3); any mismatch blocks execution.

## 5. Phase A — iteration-cap diagnostic (exactly 12 calls)

- Instances: the 12 instances of Section 3, decoded once each, in frozen
  order A01..A12.
- Settings: `max_iter=90`, `damping_alpha=1.0`; every other element of the
  V39P0 frozen protocol unchanged (GF(32) primitive polynomial 37,
  row-layered FFT-QSPA via the accepted evaluator, syndrome from true
  `u2_alice`, complete-Bob posterior
  `get_conditional_posterior_l2(counts, bob, u1_alice)`, oracle-L1
  conditioning, success = `exact_l2`).
- Blocks: same `(source, block_seed)` sampling semantics as V39
  (`sample_empirical_block(V25 TRAIN counts, block_seed, 1024)` +
  `factorize_f03`), so `errors_initial` must equal the V39 reference
  values exactly (J7) and be equal across lanes within a block.
- Judgments (all encoded in Section 13, evaluated after the global
  wrong-codeword guard):
  - any new wrong codeword (`syndrome_ok and not exact_l2`) → immediate
    terminal `V40_STOP_BC_PARAMETER_OPTIMIZATION`
    (reason `WRONG_CODEWORD_PHASE_A`); Phase B and the probe are
    unreachable;
  - rescued >= 4 (out of 12) with W_A = 0 → iteration cap is a material
    factor (`CAP_MATERIAL`); Phase B skipped; probe eligible at setting
    (max_iter=90, damping_alpha=1.0);
  - rescued 2–3 (out of 12) with W_A = 0 → weak signal (`WEAK_RESIDUAL`);
    neither Phase B nor the probe runs; terminal `V40_GO_STRUCTURE`
    (reason `WEAK_EXACT_RESCUE`);
  - rescued <= 1 (out of 12), W_A = 0, and residual improvement < 25% →
    stop the decoder parameter direction, turn to protograph/MET (terminal
    `V40_GO_STRUCTURE`, reason `NO_MATERIAL_CAP_EFFECT`);
  - rescued <= 1 (out of 12), W_A = 0, and residual improvement >= 25% →
    `RESIDUAL_ONLY_NO_EXACT_RESCUE`; the only path into Phase B.

## 6. Residual-improvement metric (exact definition)

For phase P ∈ {A, B} let `S_P` = set of the 12 instances whose phase-P
record is NOT an exact recovery. Define:

```
IMP_P = 1 - median({ errors_final_P(i) : i in S_P })
           / median({ errors_final_V39(i) : i in S_P })
```

Denominator口径 (frozen): the matched same-instance V39 run_01 residuals
of exactly the still-non-exact subset `S_P` — NOT the pooled all-12
median. This compares like with like when rescues shrink the subset. The
pooled all-12 V39 median (155.0) is additionally reported as descriptive
context only. Guards: if `S_P` is empty, `IMP_P := 1.0` (moot — rescue
count already governs); a zero denominator median is impossible for the
frozen set (minimum V39 residual 75) and raises J2 if it occurs.
Threshold semantics: "residual improvement >= 25%" ⇔ `IMP_A >= 0.25`.
An analogous report-only `IMP_B` is computed against matched V39
residuals; B gating never uses IMP_B (Section 8).

## 7. Phase B — conditional damping check (conditionally exactly 12 calls)

- Trigger (frozen, literal): run iff `W_A == 0` AND
  `R_A <= 1 (out of 12)` AND `IMP_A >= 0.25` — i.e. Phase A emitted
  `RESIDUAL_ONLY_NO_EXACT_RESCUE`. Otherwise skip entirely (skipped calls
  do not consume budget).
- Same 12 instances, same order, `max_iter=90`, `damping_alpha=0.7`;
  the ONLY difference from Phase A is damping.
- Judgments:
  - `W_B > 0` → terminal `V40_STOP_BC_PARAMETER_OPTIMIZATION`
    (reason `WRONG_CODEWORD_PHASE_B`);
  - damping has material value (`DAMPING_VALUE`) iff
    `R_B_new >= 3 (out of 12)` AND `W_B == 0`, where
    `R_B_new = |{i : exact_B(i) and not exact_A(i)}|` → probe at
    (90, 0.7);
  - otherwise the routing signal `DAMPING_NO_VALUE` fires (signal only,
    NOT a terminal): terminal `V40_GO_STRUCTURE`, reason
    `DAMPING_NO_VALUE`; decoder tuning stops entirely; no damping grid is
    constructed under any outcome.
- Phase B is reachable only through the Phase A
  `RESIDUAL_ONLY_NO_EXACT_RESCUE` branch; under `CAP_MATERIAL`
  (`R_A >= 4 (out of 12)`) or `WEAK_RESIDUAL`
  (`R_A = 2–3 (out of 12)`) it is skipped by definition.

## 8. Probe — new-block confirmation (conditionally exactly 6 calls)

Triggers (exactly one can fire; see uniqueness proof below):

- (i) `CAP_MATERIAL` (which by Section 13 rule ordering implies zero
  wrong codewords so far; Phase B skipped): fixed setting =
  **max_iter=90, damping_alpha=1.0**.
- (ii) Phase B ran and produced `DAMPING_VALUE` (this implies zero wrong
  codewords in BOTH phases, since any wrong codeword terminates earlier):
  fixed setting = **max_iter=90, damping_alpha=0.7**.

Uniqueness proof: trigger (i) requires `R_A >= 4 (out of 12)`; the Phase
B path requires `R_A <= 1 (out of 12)`; the two are mutually exclusive by
`R_A` class, so at
most one path exists and the probe setting is always uniquely determined.
If neither trigger fires, the diagnostic terminates without a probe and
records `GO_STRUCTURE` (`WEAK_EXACT_RESCUE`, `NO_MATERIAL_CAP_EFFECT`,
or reason `DAMPING_NO_VALUE`) or `STOP_BC_PARAMETER_OPTIMIZATION` per
Section 13.

Probe workload (frozen):

| call | lane | source | matrix (representative, ordinal 2) | block seed |
|---|---|---|---|---|
| PR1 | lane_c | 1M | lane_c_1M_s383102 | 390106 |
| PR2 | lane_b | 1M | lane_b_1M_s382102 | 390106 |
| PR3 | lane_c | 1p5M | lane_c_1p5M_s383202 | 390206 |
| PR4 | lane_b | 1p5M | lane_b_1p5M_s382202 | 390206 |
| PR5 | lane_c | 2M | lane_c_2M_s383302 | 390306 |
| PR6 | lane_b | 2M | lane_b_2M_s382302 | 390306 |

New probe block seeds (pre-registered here, frozen): **1M = 390106,
1p5M = 390206, 2M = 390306** — continuing the V39 `390x` per-source
prefix style. Mechanical disjointness assertion (J4): the probe seeds
must not intersect `FORBIDDEN_BLOCK_SEEDS` (= V36_A3 seeds, reused by
V38/V38R1: 360101–360105 / 360201–360205 / 360301–360305) nor V39
`BLOCK_SEEDS` (390101–390105 / 390201–390205 / 390301–390305), contain no
duplicates, and cover exactly one seed per source. Verified at planning
time: disjoint. Sampling semantics identical to Section 5; probe blocks
have no V39 reference; cross-lane `errors_initial` equality per block is
asserted instead (J7).

Probe aggregates (frozen output fields): `exact_total`, `exact_lane_c`,
`exact_lane_b`, plus the per-lane wrong-codeword counts `wrong_lane_c`
and `wrong_lane_b`.

Probe judgments (exhaustive and mutually exclusive):

- any wrong codeword (`wrong_lane_c + wrong_lane_b > 0`) →
  `STOP_BC_PARAMETER_OPTIMIZATION`;
- else `exact_total <= 2/6` → `STOP_BC_PARAMETER_OPTIMIZATION`;
- else `exact_total == 3/6` → `PROBE_INCONCLUSIVE`: no further decoder
  calls; structured-graph design becomes the default successor topic;
- else `exact_total >= 4/6` but (`exact_lane_c < 2/3` or
  `exact_lane_b < 2/3`) → `PROBE_INCONCLUSIVE`;
- else (`exact_total >= 4/6`, `exact_lane_c >= 2/3`, `exact_lane_b >= 2/3`,
  zero wrong codewords) → `PROBE_CONFIRM_ALLOWED`: permits EXACTLY ONE
  future small confirmation cycle on fresh blocks under a NEW OpenSpec
  change and new authorization; nothing is auto-started.

## 9. Budget and stop rules

| stage | calls | condition |
|---|---:|---|
| Phase A | 12 | always |
| Phase B | 12 | only if W_A = 0, R_A <= 1 (out of 12), and IMP_A >= 0.25 |
| Probe | 6 | only per Section 8 triggers |
| **Hard cap** | **30** | never exceeded |

A+probe without Phase B = 18. All counts exactly-once; no rerun, no
resume; additive outputs only.

Master stop rule (recorded verbatim):

> 不同时继续优化 B、C、decoder 和新算法；先用 12 calls 判断 decoder cap；
> 没有强信号就把额度投入 protograph/MET。

(Never optimize B, C, the decoder, and a new algorithm simultaneously;
first spend 12 calls deciding whether the decoder cap matters; without a
strong signal, move the budget to protograph/MET.)

## 10. Decoder and posterior contract (per phase)

| parameter | Phase A | Phase B | Probe |
|---|---|---|---|
| field | GF(32), poly 37 | GF(32), poly 37 | GF(32), poly 37 |
| max_iter | 90 | 90 | 90 |
| damping_alpha | 1.0 | 0.7 | 1.0 (i) / 0.7 (ii) |
| posterior | complete-Bob L2 prior | same | same |
| conditioning | oracle-L1 (`u1_alice`) | same | same |
| syndrome | from true `u2_alice` | same | same |
| success | `exact_l2` only | same | same |

`wrong_codeword = syndrome_ok and not exact_l2` is derived per record,
counted separately, and NEVER counted as exact recovery. No warm start,
no third setting, no post-failure retry. Any deviation from this table is
integrity failure J10.

## 11. Structural reconstruction and integrity checks

The matrices used span **12 matrix usage rows** (six 1M matrices of
Section 3 for Phases A/B + six representative matrices of Section 4 for
the probe), deduplicating to **10 unique matrix ids**: Phases A/B and the
probe share the two 1M ordinal-2 matrices `lane_c_1M_s383102` and
`lane_b_1M_s382102`. All are reconstructed deterministically
via the accepted V38 constructors and strictly compared against the
committed 27-record structural authority (including Lane C
`position_permutations`). Reconstruction is decoder-free. The ignored
local `v38_winning_matrices.npz` is never read; no NPZ is ever written.

Integrity checks (any failure -> `V40_EVIDENCE_INVALID`):

| id | check |
|---|---|
| J1 | instance extraction != exactly the 12 frozen rows of Section 3 (order included) |
| J2 | reference-residual guard violated (zero denominator median; V39 min residual <= 0) |
| J3 | representative-ordinal recomputation from summary != frozen constants (C=2, B=2) |
| J4 | probe-seed duplicate/overlap with V36_A3 ∪ V39 registries, or registry shape wrong |
| J5 | call accounting violation (per-phase counts, hard cap 30, planned/completed/started mismatch) |
| J6 | record schema violation or missing field |
| J7 | `errors_initial` mismatch vs V39 references (Phase A/B) or across lanes per block (all phases) |
| J8 | output root already exists (fail closed, no overwrite) |
| J9 | NPZ policy violation (any NPZ output; winner-NPZ read; V25 counts access not through the accepted loader) |
| J10 | decoder-parameter contract deviation (Section 10), incl. warm start |
| J11 | authorization failure (missing/denied flag; SHA binding != exact HEAD and origin/formal-ir-mainline equality; scoped tracked-dirty violation) |
| J12 | phase-gating violation (Phase B run without trigger; probe run without trigger; probe setting ambiguous) |

On failure: retain collected evidence unchanged, write
`v40_invalid_notice.json` plus summary with terminal
`V40_EVIDENCE_INVALID`, and stop without performance interpretation.
After a mid-run execution failure (caught at `BaseException`), raw partial
records already produced MAY be retained byte-for-byte inside the
pre-created run root, with started/completed actuals recorded, but NO
performance aggregate, signal, or terminal interpretation other than the
failure marker may be generated from a partial set.

## 12. Records, aggregation, summary

Diagnostic record schema (every call):

```
phase ("phase_a"|"phase_b"|"probe"), lane, source, construction_seed,
construction_seed_ordinal, block_seed, matrix_id, max_iter, damping_alpha,
errors_initial, errors_final, exact_l2, syndrome_ok, wrong_codeword,
iterations, status, runtime_s, v39_reference_errors_final,
v39_reference_exact_l2, rescued_vs_v39
```

(`rescued_vs_v39` defined only where a V39 reference exists, i.e. Phases
A/B; null on probe rows.)

Summary contains: accounting (planned/completed/started per phase and
total), signals (`A_signal`, optional `B_signal`), rescued counts and
wrong-codeword counts per phase, `IMP_A`/`IMP_B` plus both medians of
Section 6, probe results with the frozen aggregate fields (`exact_total`,
`exact_lane_c`, `exact_lane_b`, `wrong_lane_c`, `wrong_lane_b`), the
routing trace, `terminal_state` +
`terminal_reason`, claim boundary, statistics note, provenance SHAs
(authorized target SHA, HEAD/origin binding, predecessor plan/execution
SHAs, structural authority, V25 counts provenance, V39 input file
identity). Output files are fixed and small (Section 15).

## 13. Signal and terminal machine (total, disjoint)

Routing signals (non-terminal, recorded in the summary):
`CAP_MATERIAL`, `WEAK_RESIDUAL`, `RESIDUAL_ONLY_NO_EXACT_RESCUE`
(`R_A <= 1 (out of 12)` with `IMP_A >= 0.25`), `DAMPING_VALUE`,
`DAMPING_NO_VALUE`
(signal only — it routes to `V40_GO_STRUCTURE`; no terminal of that name
exists).

Terminals: `V40_EVIDENCE_INVALID`, `V40_GO_STRUCTURE`,
`V40_STOP_BC_PARAMETER_OPTIMIZATION`, `V40_PROBE_INCONCLUSIVE`,
`V40_PROBE_CONFIRM_ALLOWED`.

Decision procedure — FIRST matching rule wins:

```text
 0. integrity/execution failure anywhere -> V40_EVIDENCE_INVALID

 1. W_A > 0
    -> V40_STOP_BC_PARAMETER_OPTIMIZATION
       (reason WRONG_CODEWORD_PHASE_A; diagnostic ends immediately;
        Phase B and the probe are unreachable)

 2. R_A >= 4 (out of 12) and W_A == 0
    -> CAP_MATERIAL (Phase B skipped) -> probe at (90, 1.0)

 3. R_A = 2–3 (out of 12) and W_A == 0
    -> WEAK_RESIDUAL -> V40_GO_STRUCTURE
       (reason WEAK_EXACT_RESCUE; no Phase B, no probe; no more
        iteration search of any kind)

 4. R_A <= 1 (out of 12) and W_A == 0 and IMP_A < 0.25
    -> V40_GO_STRUCTURE (reason NO_MATERIAL_CAP_EFFECT;
        budget -> protograph/MET)

 5. R_A <= 1 (out of 12) and W_A == 0 and IMP_A >= 0.25
    -> RESIDUAL_ONLY_NO_EXACT_RESCUE -> run Phase B, then:
    5a. W_B > 0 -> V40_STOP_BC_PARAMETER_OPTIMIZATION
        (reason WRONG_CODEWORD_PHASE_B)
    5b. R_B_new >= 3 (out of 12) and W_B == 0
        -> DAMPING_VALUE -> probe at (90, 0.7)
    5c. else -> DAMPING_NO_VALUE (signal only) -> V40_GO_STRUCTURE
        (reason DAMPING_NO_VALUE; decoder tuning stopped entirely,
         no damping grid; successor guidance: budget -> protograph/MET)

 6. Probe ran (aggregates exact_total / exact_lane_c / exact_lane_b /
    wrong_lane_c / wrong_lane_b):
    - wrong_lane_c + wrong_lane_b > 0
      -> V40_STOP_BC_PARAMETER_OPTIMIZATION
    - exact_total <= 2 -> V40_STOP_BC_PARAMETER_OPTIMIZATION
    - exact_total == 3 -> V40_PROBE_INCONCLUSIVE
    - exact_total >= 4 and (exact_lane_c < 2 or exact_lane_b < 2)
      -> V40_PROBE_INCONCLUSIVE
    - else (exact_total >= 4, both lanes >= 2, zero wrong codewords)
      -> V40_PROBE_CONFIRM_ALLOWED
```

Notes. Rules are evaluated first-match-wins after rule 0, so any
`W_A > 0` terminates at rule 1 before rescue/improvement classification:
Phase B and the probe are unreachable whenever Phase A produces a wrong
codeword, and `W_B > 0` terminates at 5a before the damping judgment.
The mapping over (W_A?, R_A class, IMP_A class, R_B_new class, W_B?,
probe aggregates) is total and disjoint; a truth-table test enumerating
all reachable combinations (and asserting the impossible ones, e.g. a
probe while `W_A > 0`, Phase B while `W_A > 0` or `R_A >= 2 (out of
12)`, or two probe settings) is mandatory (tasks T9/T10).

`V40_PROBE_CONFIRM_ALLOWED` authorizes nothing by itself; it only marks
that ONE future small fresh-block confirmation may be proposed in a new
OpenSpec change. Diagnostic rescues never retroactively alter the V39
terminal state or historical B/C conclusions.

## 14. Statistics and claim boundary

Descriptive only; sample is tiny and clustered (12 Phase-A/B calls on 3
unique blocks x 2 lanes; 6 probe calls on 3 new blocks x 2 lanes).
Rescue proportions are reported with n and raw counts; Wilson intervals,
where printed, are naive and uncorrected for block/lane clustering; no
significance testing is performed. Forbidden claims regardless of
outcome: FER, asymptotic threshold, SKR, security, formal qualification,
promotion, real-frame behavior, Lane C superiority, Lane B superiority,
or any statement that V39 gates would now pass. Success means `exact_l2`
only.

## 15. Evidence writer and additive output root

Fixed future additive root (created before the decoder stage so partials
survive; fail-closed if it already exists):

```
comparison_bench/outputs_comparison/formal_ir_methods/v40_decoder_cap_diagnostic/run_01/
```

Files (fixed small set):

- `v40_diagnostic_records.json` / `.csv` (one row per call, all phases)
- `v40_summary.json` (accounting, signals, improvements, routing trace,
  terminal state, claim boundary, provenance)
- `v40_invalid_notice.json` (only when integrity fails)

CSV/JSON row parity required. Writing ANY `.npz` is forbidden; reading
`v38_winning_matrices.npz` is forbidden; read-only V25
`channel_counts.npz` access via the accepted loader is permitted with
provenance. Existing `results/`, V38/V39 outputs, and all other official
outputs remain byte-identical.

## 16. Implementation sketch (future rounds, unauthorized now)

- New module
  `comparison_bench/src/comparison_bench/formal_ir/v40_decoder_cap_diagnostic.py`:
  reuses `construct_lane_b_prototype`, `construct_lane_c_prototype`,
  `evaluate_single_block` (v38) and `GF2mField`, `factorize_f03`,
  `get_conditional_posterior_l2`, `load_v25_channel_counts`,
  `sample_empirical_block` (v35). V39-module helpers are NOT imported;
  the writer / SHA-binding / scoped-dirty patterns are re-implemented in
  the v40 module following the accepted V39 pattern, keeping V39 code out
  of the dirty-check scope. V39 run_01 JSONs are read as data only.
- New CLI `scripts/execute_v40_decoder_cap_diagnostic.py`: default deny;
  mandatory `--execution-authorized` and `--authorized-target-sha <sha>`;
  verifies exact equality of `git rev-parse HEAD` AND
  `git rev-parse origin/formal-ir-mainline` with the target SHA;
  scoped tracked-dirty check over
  `(v40 module, v40 CLI, v38 module, v35 module)` (four-file pattern as
  accepted in V39, with v40 replacing v39); runs the posterior-binding
  preflight, then Phase A, gated Phase B, gated probe; writes only the
  Section 15 file set.
- Posterior-binding preflight (decoder-free, write-free) mirrors V39
  Section 5 sentinels P-BIND-1/2/3 on the three probe blocks
  (390106 / 390206 / 390306), including `np.any(bob > 31)`, captured-
  argument equality with complete `bob`, corrected-vs-direct equality,
  corrected-vs-u2_bob inequality, max-abs difference > 1e-6, and argmax
  divergence. Failure blocks authorization; a failing sentinel probe is
  replaced only at plan-review stage.
- Focused fake-runner tests only; no production decode in tests.

## 17. Plan revision record

Round-0 freeze (this planning round). Discretionary decisions D1–D10,
made where the external review text required pinning, are listed for
main-thread review: D1 representative-matrix interpretation (per-source
trio at the representative ordinal; dimensional necessity); D2 residual-
improvement denominator口径 (matched still-non-exact subset vs their own
V39 residuals; pooled median reported descriptively); D3 wrong-codeword
propagation (any W_A>0 ends the diagnostic immediately at STOP with
reason WRONG_CODEWORD_PHASE_A, Phase B and probe unreachable; W_B>0 ends
at STOP with reason WRONG_CODEWORD_PHASE_B; Phase B trigger narrowed from
the round-0 literal `IMP_A>=0.25 ∧ R_A<4` to `W_A=0 ∧ R_A<=1 (out of
12) ∧ IMP_A>=0.25`, which also removes the round-0 tainted-DAMPING_VALUE
path);
D4 terminal naming (signals + five terminals unchanged;
`DAMPING_NO_VALUE` reclassified from terminal to routing signal whose
terminal is `GO_STRUCTURE` with reason `DAMPING_NO_VALUE`; no terminal
is named after the DAMPING_NO_VALUE signal; `R_A = 2–3 (out of 12)` maps
to `WEAK_RESIDUAL` → `GO_STRUCTURE` (reason `WEAK_EXACT_RESCUE`) regardless
of IMP_A); D5 probe block seeds
390106/390206/390306; D6 scoped-dirty scope = v40 module + v40 CLI +
v38 + v35 modules, V39 module not imported; D7 V39P0 result is accepted
(lifecycle `DEVELOPMENT_RESULT_ACCEPTED`, result SHA
`940bfc996a0bd87d60e958150c4f770ee35f16b8`); the round-0 V39-review
precondition is deleted — V40 authorization requires only its own plan
ACCEPT plus explicit user `EXECUTE_AUTH`, keeping V40 itself unauthorized
until then; D8 deterministic enumeration/call order
(pair-file order, lane_c before lane_b; probe sources in 1M/1p5M/2M
order, lane_c first); D9 minimal fixed file set (records json/csv +
summary + optional invalid notice); D10 B-phase improvement metrics are
report-only; B gating uses R_B_new and W_B exclusively.

Plan revision, cycle V40P0 (2026-08-26), user-approved transcription
correction: §3 table rows A11/A12 `errors_initial` 259 → **252**, per the
V39 run_01 paired authority and J7 cross-lane equality semantics (block
390101 already carries 252 on pairs P1/P3). No other plan value changes;
the implementation module has been frozen at the authoritative 252 since
the implementation candidate (noted in module comments), so lifecycle
remains PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED and no code change is
required.
