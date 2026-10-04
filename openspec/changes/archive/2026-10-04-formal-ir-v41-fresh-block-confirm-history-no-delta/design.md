# OpenSpec Design: formal-ir-v41-fresh-block-confirm

**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`
**Cycle**: `V41P0`
**Predecessor**: V40P0, terminal `V40_PROBE_CONFIRM_ALLOWED` (probe
exact_total 5/6; lane_c 3/3, lane_b 2/3; zero wrong codewords), lifecycle
`DEVELOPMENT_RESULT_ACCEPTED`, result SHA
`a546d43c74be5f11e87426ff7ce837b31dd20142`, implementation/execution SHA
`80d605489f1f65eefd091625134514e8a09902de`, accepted plan SHA (historical
reference) `36a3751e190ff06e0e88024b51b6f8713c13a4dc`.

## 1. Scientific question (single)

Do Lane C and Lane B each independently retain their route signal on nine
never-used TRAIN development blocks at the fixed extended setting
(max_iter=90, damping_alpha=1.0)? The answer routes the budget once: dual
retention freezes both as fixed candidates and stops decoder tuning (next
stage directionally: more-realistic / non-oracle conditions); single retention
keeps one lane and stops the other route lane; otherwise current B/C parameter
optimization stops and the budget turns to protograph/MET structure design.

## 2. Predecessor binding and committed inputs

All inputs are read-only:

- Structural authority (unchanged from V38P0/V39/V40):
  `comparison_bench/outputs_comparison/formal_ir_methods/v38_architecture_triage/run_01/v38_structural_prototypes.json`
  (27 records; lanes b/c subset = 18).
- V25 TRAIN counts: read-only via accepted `load_v25_channel_counts()`
  (provenance recorded in summary).
- V40 run_01 summary is read at most as an identity/provenance reference;
  no v40 or v39 module is ever imported.

The V40P0 evidence stands (terminal `V40_PROBE_CONFIRM_ALLOWED`, lifecycle
`DEVELOPMENT_RESULT_ACCEPTED`, result SHA
`a546d43c74be5f11e87426ff7ce837b31dd20142`). Per V40's claim boundary that
terminal authorizes nothing by itself; it marks only that this ONE
confirmation change may be proposed. V41 execution authorization requires
only V41's own independent plan ACCEPT plus explicit user `EXECUTE_AUTH`.

## 3. Frozen sample set (9 new blocks, pre-registered here)

New block seeds (frozen constants; continuing the `390x` per-source prefix
convention), three never-used blocks per source:

| source | new block seeds |
|---|---|
| 1M | 390107, 390108, 390109 |
| 1p5M | 390207, 390208, 390209 |
| 2M | 390307, 390308, 390309 |

Planning-time mechanical verification (against committed source constants,
not imports): disjoint from V36_A3 seeds reused by V38/V38R1
(360101-360105 / 360201-360205 / 360301-360305), from the V39 registry
(390101-390105 / 390201-390205 / 390301-390305), and from the V40 probe seeds
(390106 / 390206 / 390306); no duplicates within the nine. Verified: zero
overlap. Implementation SHALL re-assert this mechanically (J2) against the
same registries copied as data.

Sampling semantics identical to the accepted protocol:
`sample_empirical_block(V25 TRAIN counts, block_seed, BLOCK_LENGTH=1024)` +
`factorize_f03`. Each block is decoded exactly once per lane; cross-lane
`errors_initial` equality per block is asserted (J6).

## 4. Frozen workload C01-C18 (exactly 18 calls)

Call order frozen (D7): sources in 1M/1p5M/2M order, blocks ascending by seed
within a source, lane_c before lane_b within a block.

| call | source | block_seed | lane | matrix_id (ordinal 2) |
|---|---|---|---|---|
| C01 | 1M | 390107 | lane_c | lane_c_1M_s383102 |
| C02 | 1M | 390107 | lane_b | lane_b_1M_s382102 |
| C03 | 1M | 390108 | lane_c | lane_c_1M_s383102 |
| C04 | 1M | 390108 | lane_b | lane_b_1M_s382102 |
| C05 | 1M | 390109 | lane_c | lane_c_1M_s383102 |
| C06 | 1M | 390109 | lane_b | lane_b_1M_s382102 |
| C07 | 1p5M | 390207 | lane_c | lane_c_1p5M_s383202 |
| C08 | 1p5M | 390207 | lane_b | lane_b_1p5M_s382202 |
| C09 | 1p5M | 390208 | lane_c | lane_c_1p5M_s383202 |
| C10 | 1p5M | 390208 | lane_b | lane_b_1p5M_s382202 |
| C11 | 1p5M | 390209 | lane_c | lane_c_1p5M_s383202 |
| C12 | 1p5M | 390209 | lane_b | lane_b_1p5M_s382202 |
| C13 | 2M | 390307 | lane_c | lane_c_2M_s383302 |
| C14 | 2M | 390307 | lane_b | lane_b_2M_s382302 |
| C15 | 2M | 390308 | lane_c | lane_c_2M_s383302 |
| C16 | 2M | 390308 | lane_b | lane_b_2M_s382302 |
| C17 | 2M | 390309 | lane_c | lane_c_2M_s383302 |
| C18 | 2M | 390309 | lane_b | lane_b_2M_s382302 |

18 usage rows deduplicate to **6 unique matrices** (lane x source at ordinal
2). Any drift in membership or order is integrity failure J12.

## 5. Representative matrices (constants verified against V40 module data)

Per user-frozen decision both lanes use their **ordinal-2 representative
matrix** per source. Verified against the committed V40 module constant table
(`CONSTRUCTION_SEEDS`, representative ordinals C=2/B=2, which itself derives
from the V39 summary argmax lane_c 11/12/10, lane_b 10/11/10):

- **lane_c ordinal 2**: `lane_c_1M_s383102` (seed 383102),
  `lane_c_1p5M_s383202` (383202), `lane_c_2M_s383302` (383302).
- **lane_b ordinal 2**: `lane_b_1M_s382102` (382102),
  `lane_b_1p5M_s382202` (382202), `lane_b_2M_s382302` (382302).

These match the user-frozen identities exactly. Prototypes are source-specific
(H row counts 184/190/192), so each block uses its own source's matrix at the
lane's representative ordinal. Matrices are reconstructed deterministically
via the accepted V38 constructors and strictly compared against the committed
structural authority (including Lane C `position_permutations`) at preflight
(J3). Reconstruction is decoder-free. No NPZ is read except read-only V25
counts via the accepted loader; no NPZ is ever written.

## 6. Decoder contract (single fixed setting)

| parameter | value (all 18 calls) |
|---|---|
| field | GF(32), primitive polynomial 37 |
| max_iter | 90 |
| damping_alpha | 1.0 |
| posterior | complete-Bob L2 prior `get_conditional_posterior_l2(counts, bob, u1_alice)` |
| conditioning | oracle-L1 (`u1_alice`) |
| syndrome | from true `u2_alice` |
| success | `exact_l2` only |

No warm start, no retry, no second setting under any outcome.
`wrong_codeword = syndrome_ok and not exact_l2` is derived per record, counted
separately, and NEVER counted as exact recovery. Any deviation is J9.

## 7. Per-lane retention gates (route retention only)

For lane L in {lane_c, lane_b}, with 9 calls per lane (3 blocks x 3 sources):

- G1: overall exact count for L >= 7 out of 9;
- G2: every source's exact count for L >= 2 out of 3;
- G3: wrong codewords for L == 0.

Lane L passes iff G1 AND G2 AND G3 all hold. Gates judge ROUTE RETENTION
only; they are explicitly NOT a B/C superiority test, and no comparative
B-vs-C statement of any kind is permitted regardless of outcome.

## 8. Terminal machine (total, disjoint; EVIDENCE_INVALID first)

Terminals: `V41_EVIDENCE_INVALID`, `V41_BOTH_LANES_RETAINED`,
`V41_C_ONLY_RETAINED`, `V41_B_ONLY_RETAINED`,
`V41_STOP_BC_PARAMETER_OPTIMIZATION`.

Decision procedure - FIRST matching rule wins:

```text
 0. integrity/execution failure anywhere -> V41_EVIDENCE_INVALID

 1. pass_lane_c AND pass_lane_b -> V41_BOTH_LANES_RETAINED
       (both lanes retained as fixed candidates; decoder tuning STOPS;
        successor direction, descriptive only and unauthorized: comparison
        under more-realistic data / non-oracle conditions)

 2. pass_lane_c only -> V41_C_ONLY_RETAINED
       (retain Lane C; STOP the current Lane B route)

 3. pass_lane_b only -> V41_B_ONLY_RETAINED
       (retain Lane B; STOP the current Lane C route)

 4. else (both lanes fail gates)
    -> V41_STOP_BC_PARAMETER_OPTIMIZATION
       (reason BOTH_LANES_GATES_FAILED; stop current B/C parameter
        optimization; successor direction, descriptive only and
        unauthorized: protograph/MET structure design)
```

There is NO global wrong-codeword rule: a wrong codeword on Lane C cannot
veto a gate-passing Lane B, and a wrong codeword on Lane B cannot veto a
gate-passing Lane C; wrong codewords act ONLY through each lane's own
zero-wrong clause G3. This supersedes the round-0 D4 global-literal scope
(user-approved supersession, 2026-08-26). Rules 1-4 partition the
(pass_c, pass_b) plane over {TT, TF, FT, FF} and rule 0 precedes them, so
the mapping is total and disjoint; a truth-table test enumerating all
(lane_c_pass, lane_b_pass) combinations and asserting mutual exclusion is
mandatory (tasks T5/T6). Terminal determination precedes the per-lane
gate-detail display in the summary, which still reports each lane's wrong
count separately.

Under EVERY terminal, without exception: no block addition, no supplementary
or compensating run, and NO second confirmation round. Retention terminals
freeze retained lane(s) as fixed candidates and stop decoder parameter tuning;
they authorize nothing else.

## 9. Budget and stop rules

| item | value |
|---|---|
| Confirmation calls | exactly 18 (C01-C18) |
| Hard cap | 18; call 19 structurally refused (J10) |
| Execution | exactly once; no rerun, no resume |

Master stop rule (recorded verbatim in the summary):

> 唯一一次 18-call 全新确认；不再调 decoder 参数；不复用 V40 probe 作为确认样本。无论结果如何：不追加 blocks、不补跑、不做第二轮确认。

(One single 18-call fresh confirmation; no further decoder-parameter tuning;
no reuse of V40 probe blocks as confirmation samples. Regardless of outcome:
no added blocks, no supplementary runs, no second confirmation round.)

## 10. Scientific preflight (decoder-free) and guard ordering

Guard ordering (frozen; encodes the V40 revision lesson):

1. **Refusal-class guards FIRST, before any directory creation**: default
   deny; mandatory `--execution-authorized`; exact-equality SHA binding of
   BOTH `git rev-parse HEAD` AND `git rev-parse origin/formal-ir-mainline`
   with `--authorized-target-sha`; scoped tracked-dirty check over the four
   files `(v41 module, v41 CLI, v38_architecture_triage.py,
   v35_algorithm_development.py)`; absence of the output root (J7).
   Any refusal exits non-zero with ZERO calls and creates NOTHING.
2. **Scientific preflights (decoder-free, write-free)**, in order:
   seed-registry validator (J2); deterministic reconstruction of the 6 unique
   matrices with strict match vs the committed structural authority (J3);
   counts shape/loading via the accepted loader for all three sources (J4);
   posterior-binding sentinels on the FIRST new block of each source -
   390107 / 390207 / 390307 (J5).
3. **Preflight failure** -> create the formal additive root, write
   `v41_invalid_notice.json` + records(empty) + `v41_summary.json` with
   terminal `V41_EVIDENCE_INVALID`, planned = 18, started = 0, completed = 0,
   and NO aggregation; stop with ZERO decoder calls.
4. **Root creation**: the output root is created only AFTER all refusal-class
   guards AND scientific preflights pass, BEFORE the first decoder call
   (existence already refused at Tier 0, J7).

Posterior-binding sentinels per probe block (accepted V40 pattern): six
checks - `bob_gt_31` (`np.any(bob > 31)`), `captured_equals_bob` (spy-captured
second argument element-equal to complete `bob`), `corrected_equals_direct`,
`corrected_differs_u2bob_arraywise`, `corrected_differs_u2bob_maxabs`
(max-abs difference vs the `u2_bob` prior > 1e-6), `argmax_divergence`. A
failing sentinel probe is replaceable only at plan-review stage.

Integrity checks (failures of the scientific-preflight and post-evaluation
classes J2-J6/J8-J12 yield `V41_EVIDENCE_INVALID`, whereas J1 and J7 are
Tier 0 execution refusals - e.g. J7 = output-root-exists - that create
NOTHING and exit non-zero with ZERO calls):

| id | check |
|---|---|
| J1 | authorization/refusal failure (default deny; missing flag(s); SHA binding != exact HEAD and origin/formal-ir-mainline equality; scoped tracked-dirty violation) |
| J2 | seed-registry violation (duplicate among the nine; overlap with V36_A3 ∪ V39 ∪ V40-probe registries; not exactly 3 per source) |
| J3 | matrix reconstruction mismatch vs committed structural authority (incl. Lane C `position_permutations`) |
| J4 | counts shape/loading failure via the accepted loader |
| J5 | posterior-binding sentinel failure |
| J6 | cross-lane `errors_initial` inequality within a block |
| J7 | output root already exists (fail closed, no overwrite) |
| J8 | NPZ policy violation (any NPZ output; winner-NPZ-class reads; V25 counts access not through the accepted loader) |
| J9 | decoder-parameter contract deviation (Section 6), incl. warm start |
| J10 | call accounting violation (per-call records; hard cap 18; structural refusal of call 19; planned/started/completed mismatch) |
| J11 | record schema violation or missing field |
| J12 | workload drift (call set/order != frozen C01-C18 of Section 4) |

After a mid-run execution failure (caught at `BaseException`): raw partial
records already produced are retained byte-for-byte inside the pre-created
root together with a notice + summary carrying started/completed actuals, then
the exception is re-raised; NO performance aggregate, signal, gate evaluation,
or terminal interpretation other than the failure marker may be generated from
a partial set.

### Unified three-tier evidence boundary

The four disk/process outcomes correspond one-to-one with spec R11 and tasks
A6/A7:

| tier | trigger | disk effect | process effect |
|---|---|---|---|
| Tier 0 execution refusal | unauthorized; missing flag(s)/SHA; SHA mismatch vs HEAD OR origin/formal-ir-mainline; scoped tracked-dirty (J1); output root already exists (J7) | NOTHING created - no file, no root | non-zero exit, ZERO calls |
| Tier 1 scientific-preflight failure | J2 registry / J3 reconstruction strict mismatch / J4 counts shape / J5 posterior sentinel | formal additive root created; `v41_invalid_notice.json` + summary (terminal `V41_EVIDENCE_INVALID`, planned fixed 18, started 0, completed 0, no aggregation) | real decoder calls = 0; stop, no rerun |
| Tier 2 mid-run `BaseException` | any exception during the decode loop | raw partial records retained byte-for-byte + invalid notice + summary with started/completed actuals | re-raise |
| normal completion | all calls recorded, integrity ok | minimal fixed set: records json/csv + summary; no NPZ | exit 0 |

## 11. Records, aggregation, summary

Record schema (every call):

```
call_id ("C01".."C18"), lane, source, construction_seed,
construction_seed_ordinal, block_seed, matrix_id, max_iter, damping_alpha,
errors_initial, errors_final, exact_l2, syndrome_ok, wrong_codeword,
iterations, status, runtime_s
```

Summary contains: accounting (planned = 18 / completed actual / started
actual, plus structural_reconstruction_decoder_calls = 0 and
preflight_decoder_calls = 0); per-lane aggregates (`exact_total`,
`exact_by_source`, `wrong_count` per lane); per-source aggregates; BOTH
lanes' gate-evaluation details (each clause G1/G2/G3 with its numbers and
pass/fail); routing trace; `terminal_state` + `terminal_reason`; master stop
rule verbatim; claim boundary; statistics note; provenance SHAs (authorized
target SHA, HEAD/origin binding, predecessor plan/execution SHAs, structural
authority identity, V25 counts provenance). Terminal determination precedes
the gate-detail display (D4).

## 12. Statistics and claim boundary

Descriptive only; sample is tiny and clustered (18 calls = 9 unique blocks x
2 lanes). Exact-recovery proportions are reported with n and raw counts; any
interval printed is naive and uncorrected for block/lane clustering; no
significance testing is performed. Success means `exact_l2` only.

Claim boundary (verbatim conventions): results support ONLY bounded route-
retention judgments on V25 TRAIN empirical-count development blocks with
oracle-L1 inputs - these are NOT real-frame FER evidence; do not infer
threshold, SKR, formal-execution, qualification, or promotion results.
Forbidden regardless of outcome: FER, asymptotic threshold, SKR, security,
formal qualification, promotion, real-frame behavior, Lane C superiority,
Lane B superiority, any B-vs-C comparative ranking, and any statement that
historical gates would now pass. Retention terminals do not auto-start any
successor work.

## 13. Evidence writer and additive output root

Fixed future additive root (created before the decoder stage so partials
survive; fail-closed if it already exists; also created on scientific-
preflight failure solely to hold the invalid trio):

```
comparison_bench/outputs_comparison/formal_ir_methods/v41_fresh_block_confirm/run_01/
```

Files (minimal fixed set):

- `v41_confirm_records.json` / `.csv` (one row per call)
- `v41_summary.json` (accounting, per-lane/per-source aggregates, gate
  details, routing trace, terminal state + reason, stop rule verbatim, claim
  boundary, provenance)
- `v41_invalid_notice.json` (only when integrity fails)

CSV/JSON row parity required. Writing ANY `.npz` is forbidden; reading any NPZ
except read-only V25 `channel_counts.npz` via the accepted loader is
forbidden. Existing `results/`, V38/V39/V40 outputs, and all other official
outputs remain byte-identical.

## 14. Implementation sketch (future rounds, unauthorized now)

- New module
  `comparison_bench/src/comparison_bench/formal_ir/v41_fresh_block_confirm.py`:
  reuses `construct_lane_b_prototype`, `construct_lane_c_prototype`,
  `evaluate_single_block` (v38) and `GF2mField`, `factorize_f03`,
  `get_conditional_posterior_l2`, `load_v25_channel_counts`,
  `sample_empirical_block` (v35). The v39 and v40 modules are NOT imported;
  the runner/writer/SHA-binding/scoped-dirty/preflight patterns are copied
  from the accepted V39/V40 pattern (pattern copy, not import). Registries
  (V36_A3, V39, V40 probe seeds) enter as copied data constants.
- New CLI `scripts/execute_v41_fresh_block_confirm.py`: default deny;
  mandatory `--execution-authorized` and `--authorized-target-sha <sha>`;
  verifies exact equality of BOTH `git rev-parse HEAD` AND
  `git rev-parse origin/formal-ir-mainline` with the target SHA (ancestor or
  contains checks insufficient); scoped tracked-dirty check over the four-file
  scope (D8); binds `fake_runner=False`; no fake-runner CLI option; non-zero
  exit with zero calls and nothing created on any guard failure.
- Focused fake-runner tests only; no production decode in tests.

## 15. Plan revision record

Round-0 freeze (this planning round). Discretionary decisions D1-D12, made
where the frozen directive required pinning, listed for main-thread review:

- **D1 shape**: single-phase confirmation, no Phase A/B staging, no baseline,
  no additional matrices; exactly 18 calls in one executed phase.
- **D2 seed registry**: the nine new block seeds 390107-390109 /
  390207-390209 / 390307-390309 are frozen constants; FORBIDDEN union =
  V36_A3 (360101-360105 / 360201-360205 / 360301-360305) ∪ V39
  (390101-390105 / 390201-390205 / 390301-390305) ∪ V40 probe
  (390106/390206/390306); planning-time mechanical verification shows ZERO
  overlap and NO duplicates; implementation re-asserts mechanically (J2).
- **D3 representative matrices**: written dead as ordinal-2 constants
  (Section 5), verified identical to the V40 module's `CONSTRUCTION_SEEDS`/
  `REPRESENTATIVE_ORDINALS` facts; implementation reconstructs and
  strict-matches against the committed structural authority instead of
  importing the v40 module.
- **D4 wrong-codeword scope**: SUPERSEDED (user-approved 2026-08-26). The
  round-0 global-literal scope (a wrong codeword on ANY lane at ANY position
  terminating at STOP ahead of gate classification) is REPLACED by
  lane-specific gating: a wrong codeword acts ONLY through its own lane's
  zero-wrong clause G3; one lane's wrongs can never veto the other lane's
  gate outcome; there is no global wrong rule and no global wrong reason.
  Truth-table test remains exhaustive and mutually exclusive, now over the
  (lane_c_pass, lane_b_pass) plane; wrong-injection tests assert lane-local
  effects only.
- **D5 gate thresholds**: exactly overall >= 7/9, per-source >= 2/3,
  per-lane wrong = 0; route-retention semantics only; no B/C superiority
  framing anywhere in outputs.
- **D6 sentinel placement**: posterior-binding sentinels run on the FIRST new
  block of each source (390107/390207/390307), satisfying "三个新块首块或等价
  冻结探针"; replacement only at plan-review stage.
- **D7 call order**: sources 1M/1p5M/2M, blocks ascending by seed within a
  source, lane_c before lane_b within a block (C01-C18).
- **D8 scoped-dirty scope**: v41 module + v41 CLI + v38 module + v35 module
  (four-file pattern as accepted in V39/V40); v39/v40 modules never imported.
- **D9 preflight-failure evidence policy**: scientific-preflight failure
  creates the additive root and writes the invalid trio (notice + empty
  records + summary with terminal EVIDENCE_INVALID, planned 18, started 0,
  completed 0, no aggregation) and stops with ZERO calls - the V40 revision
  lesson encoded; refusal-class guard failures exit WITHOUT creating anything.
- **D10 file set**: minimal fixed set (records json/csv + summary +
  conditional invalid notice); no NPZ writes ever.
- **D11 terminal naming/reasons**: five terminals (Section 8); STOP carries
  reason `BOTH_LANES_GATES_FAILED` only.
- **D12 successor language**: "更真实数据/非 oracle 条件比较" (dual-retention
  branch) and "protograph/MET 方向" (STOP branch) are directional
  descriptions recorded in the summary only; neither authorizes nor
  auto-starts anything.
