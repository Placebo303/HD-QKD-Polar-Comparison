# OpenSpec Design: formal-ir-v42-conditional-realism-diagnostic

**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`
**Cycle**: `V42P0`
**Predecessor**: V41P0 run_01, terminal `V41_C_ONLY_RETAINED` (lane_c exact
8/9 with per-source 3/3/2; lane_b gates failed at 6/9; zero wrong codewords;
recorded lifecycle `DEVELOPMENT_RESULT_CANDIDATE`), implementation/execution
SHA `6d75e754899e8470445c2bf58f2f4ff84130fc33`; accepted plan SHA bound at
implementation freeze (A12). That terminal authorizes nothing by itself.

## 1. Scientific question (single)

Does Lane C retain its fresh-block signal when the decoder's oracle-L1
conditioning input (true `u1_alice`) is replaced by `cond_estimated_l1` (the
idealized uncoded MAP-L1 estimated condition, frozen Candidate A) — or does
the measured performance loss arise from this MAP-L1 conditioning mechanism
itself rather than the Lane C graph structure? The answer routes the budget
once, directionally: dual pass → Lane C may proceed toward more-realistic data
/ end-to-end benchmarking; oracle-only pass → the loss is attributed to the
frozen MAP-L1 conditioning mechanism (NOT to Lane C structure, and NOT to any
concrete upstream coding scheme or real system); both fail → the V41 lane_c
signal retains block-sample dependence and the budget turns toward
protograph/MET structure design rather than further decoder tuning;
estimated-l1-only pass → anomalous inversion, analysis required. All routing
statements are directional descriptions and authorize nothing.

## 2. Predecessor binding and committed inputs

All inputs are read-only:

- Structural authority (unchanged from V38P0/V39/V40/V41):
  `comparison_bench/outputs_comparison/formal_ir_methods/v38_architecture_triage/run_01/v38_structural_prototypes.json`
- V25 TRAIN counts via accepted `load_v25_channel_counts()` only.
- V40/V41 run_01 summaries are read at most as identity/provenance references;
  no v39/v40/v41 module is ever imported.

## 3. Frozen sample set (9 new blocks, pre-registered here)

New block seeds (frozen constants; continuing the `390x` per-source prefix
convention), three never-used blocks per source:

| source | new block seeds |
|---|---|
| 1M | 390110, 390111, 390112 |
| 1p5M | 390210, 390211, 390212 |
| 2M | 390310, 390311, 390312 |

Planning-time mechanical verification against committed source constants
(v41 module copied registries, lines 75-102 — read as facts, not imported):
FORBIDDEN union = V36_A3 (360101-360105 / 360201-360205 / 360301-360305) ∪
V39 registry (390101-390105 / 390201-390205 / 390301-390305) ∪ V40 probe
(390106 / 390206 / 390306) ∪ **V41 confirmation (390107-390109 /
390207-390209 / 390307-390309)** = 42 seeds.
The nine new seeds are the immediate ascending continuation per source
(x10-x12 after x01-x09), contain no internal duplicates, and have ZERO overlap
with all four families. Verified: zero overlap. Implementation SHALL re-assert
this mechanically (J2) against the same registries copied as data, now
including the V41 family.

Sampling semantics identical to the accepted protocol:
`sample_empirical_block(V25 TRAIN counts, block_seed, BLOCK_LENGTH=1024)` +
`factorize_f03`. Each block sample is computed ONCE per block and shared by
both arms of its pair (pairing guarantee, Section 10).

## 4. Frozen workload C01-C18 (exactly 18 calls)

Call order frozen (D7): sources in 1M/1p5M/2M order, blocks ascending by seed
within a source, `cond_oracle` before `cond_estimated_l1` within a pair.

| call | source | block_seed | condition | matrix_id (lane_c ordinal 2) |
|---|---|---|---|---|
| C01 | 1M | 390110 | cond_oracle | lane_c_1M_s383102 |
| C02 | 1M | 390110 | cond_estimated_l1 | lane_c_1M_s383102 |
| C03 | 1M | 390111 | cond_oracle | lane_c_1M_s383102 |
| C04 | 1M | 390111 | cond_estimated_l1 | lane_c_1M_s383102 |
| C05 | 1M | 390112 | cond_oracle | lane_c_1M_s383102 |
| C06 | 1M | 390112 | cond_estimated_l1 | lane_c_1M_s383102 |
| C07 | 1p5M | 390210 | cond_oracle | lane_c_1p5M_s383202 |
| C08 | 1p5M | 390210 | cond_estimated_l1 | lane_c_1p5M_s383202 |
| C09 | 1p5M | 390211 | cond_oracle | lane_c_1p5M_s383202 |
| C10 | 1p5M | 390211 | cond_estimated_l1 | lane_c_1p5M_s383202 |
| C11 | 1p5M | 390212 | cond_oracle | lane_c_1p5M_s383202 |
| C12 | 1p5M | 390212 | cond_estimated_l1 | lane_c_1p5M_s383202 |
| C13 | 2M | 390310 | cond_oracle | lane_c_2M_s383302 |
| C14 | 2M | 390310 | cond_estimated_l1 | lane_c_2M_s383302 |
| C15 | 2M | 390311 | cond_oracle | lane_c_2M_s383302 |
| C16 | 2M | 390311 | cond_estimated_l1 | lane_c_2M_s383302 |
| C17 | 2M | 390312 | cond_oracle | lane_c_2M_s383302 |
| C18 | 2M | 390312 | cond_estimated_l1 | lane_c_2M_s383302 |

18 usage rows deduplicate to **3 unique matrices** (lane_c x source at ordinal
2). Any drift in membership or order is integrity failure J12.

## 5. Representative matrices (constants verified against committed facts)

Lane C only, ordinal-2 representative matrix per source. Verified against the
committed v41 module constant table (`CONSTRUCTION_SEEDS["lane_c"]`,
`REPRESENTATIVE_ORDINALS["lane_c"]=2`, which derives from the V39 summary
argmax lane_c 11/12/10):

- `lane_c_1M_s383102` (construction seed 383102)
- `lane_c_1p5M_s383202` (383202)
- `lane_c_2M_s383302` (383302)

These match the user-frozen identities exactly. Matrices are reconstructed
deterministically via the accepted V38 constructors and strictly compared
against the committed structural authority (including Lane C
`position_permutations`) at preflight (J3). Reconstruction is decoder-free.
No NPZ is read except read-only V25 counts via the accepted loader; no NPZ is
ever written.

## 6. Decoder contract (single fixed setting; composed dual-condition path)

Shared numeric contract for ALL 18 calls:

| parameter | value |
|---|---|
| field | GF(32), primitive polynomial 37 |
| max_iter | 90 |
| damping_alpha | 1.0 |
| posterior function | `get_conditional_posterior_l2(counts, bob, selector)` (accepted v35 function, both arms) |
| syndrome | from true `u2_alice` |
| success | `exact_l2` vs true `u2_alice` only |

Per-arm difference (the ONLY difference): the conditioning selector fed to the
posterior —

- `cond_oracle`: selector = true `u1_alice` (upper bound).
- `cond_estimated_l1`: selector = `u1_hat` from the frozen idealized uncoded
  MAP-L1 estimate (Section 7, RESOLVED).

**D15 (composed path)**: `evaluate_single_block` cannot be reused because it
hardcodes oracle conditioning (v38 line 995) AND uses its `counts` argument
for sampling as well as posterior — any carrier substitution through that
argument would silently change the sampled block and break pairing. The v42
module therefore composes the SAME accepted primitives in one thin
dual-condition loop (`sample_empirical_block` once per block →
`factorize_f03` → `get_conditional_posterior_l2(counts, bob, selector)` per
arm → `syndrome_of_gf32(H, u2_alice)` → `decode_row_layered_fftqspa(...)`),
replicating v38 lines 992-1030 verbatim except the selector. All numerics are
imported from accepted modules; nothing frozen is modified. The decode
function is injectable (`decode_fn`) defaulting to the accepted
`decode_row_layered_fftqspa`; tests inject fakes; production binds the real
decoder (`fake_runner=False`, no fake-runner CLI option). This composition is
a plan-review attention item.

`wrong_codeword = syndrome_ok and not exact_l2` derived per record, counted
separately, NEVER counted as exact recovery. Any deviation is J9.

## 7. O1 - the estimated-L1 conditioning mechanism (D13, RESOLVED)

Constraint discovered from source reading (facts, not imports): the oracle
lives in the SELECTOR argument of `get_conditional_posterior_l2`; replacing it
does not require touching any frozen file. Candidates:

| | Candidate A: estimated-L1 hard conditioning | Candidate B: pilot-estimated counts + estimated L1 | Candidate C: mismatched fixed channel law (V32 Q_B1-style uniform-SER substitute) |
|---|---|---|---|
| Mechanism | `û1(b) = argmax_u1 Σ_u2 counts[u1·32+u2, b]` (pure function of Bob symbols + public counts); prior = `get_conditional_posterior_l2(counts, bob, û1)` | draw K pilot pairs per source with a fresh frozen pilot seed → Ĉ; both û1 and the L2 prior computed from Ĉ; block sampling still from true counts | replace counts downstream by a fixed synthetic law (uniform-SER style); û1 and prior from that law |
| Removes which oracle | Alice-L1 knowledge ONLY (channel law stays true V25 counts) | Alice-L1 + count fidelity | Alice-L1 + entire empirical channel law |
| Implementation cost | lowest (~15 LOC marginal+argmax, pure numpy) | low (+ pilot sampler ~10 LOC; K and pilot seed become new frozen parameters needing justification) | medium (~20 LOC synthetic-law constructor; law definition must be defended against post-hoc dispute) |
| Compatibility | full — accepted v35 functions only; decode path identical except selector | full — same | full — same |
| Attribution supported | EXACTLY isolates the estimated-L1 factor: oracle pass + A fail ⇒ the loss is attributable to the frozen MAP-L1 conditioning mechanism itself; A pass ⇒ Lane C graph robust to the `cond_estimated_l1` MAP-L1 conditioning | conflates two factors in a single arm; a failure cannot be cleanly attributed without extra arms (budget-prohibitive under the 18-call cap) | stress-test of channel-model availability; weakest link to the estimated-L1 conclusion; failure could be blamed on arbitrary law choice |
| Risks | MAP-from-marginals is an idealized UNCODED estimate — semantics must be stated in claim boundary (it is not any concrete coded L1 reconciliation result) | pilot-K/seed arbitrariness | law-choice arbitrariness |

User-suggested variant "(c) noise/quantization on posterior inputs" is
DEPRIORITIZED: per-position stochastic perturbation is not expressible without
modifying the frozen evaluator/decoder call path or duplicating decoder
internals; quantization-only variants still condition on true `u1_alice` and
therefore do not test the estimated-L1 question at all.

**RESOLVED (user adjudication 2026-08-26)**: Candidate A is THE frozen
mechanism, renamed **`cond_estimated_l1`** ("idealized uncoded MAP-L1
estimated condition"; cleanest attribution, lowest cost, full compatibility;
B/C rejected for attribution conflation and pilot/law arbitrariness). Frozen
definition, binding verbatim:

- `u1_hat(b) = argmax_u1 Σ_u2 counts[u1*32+u2, b]`
- prior 使用 `get_conditional_posterior_l2(counts_true, bob, u1_hat)`
- 采样仍仅使用相同 counts_true；两臂共享一次生成的 block；
- 禁止引入 pilot、噪声、量化或失配信道律。

Naming boundary (binding): `cond_estimated_l1` 是“使用真实公共经验 counts 的
理想化、未编码 MAP-L1 估计”，不是具体 operational L1 reconciliation，不得泛称
真实条件；oracle-only 结果只能归因为**本次 MAP-L1 conditioning 机制**造成的性能
损失，不得宣称具体上游编码方案失败或真实系统失败。

Diagnostic context reported but never gated: per-source Layer-1 MAP accuracy
`mean(u1_hat == u1_alice)` over the nine blocks (quantifies how much
information the `cond_estimated_l1` conditioning actually carries). The
mechanism, this definition, and the arm label semantics are frozen verbatim
into module constants and may not be changed afterwards.

## 8. Per-condition gates (route/attribution retention only)

For arm X ∈ {cond_oracle, cond_estimated_l1}, each judged on its own 9 calls
(3 blocks x 3 sources):

- G1': overall exact count for X >= 7 out of 9;
- G2': every source's exact count for X >= 2 out of 3;
- G3': wrong codewords for X == 0.

Arm X passes iff G1' AND G2' AND G3' all hold. Gates judge CONDITION RETENTION
only; they are NOT a superiority test between conditions or lanes, and no
comparative ranking statement of any kind is permitted regardless of outcome.

## 9. Terminal machine (total, disjoint; EVIDENCE_INVALID first)

Terminals: `V42_EVIDENCE_INVALID`, `V42_BOTH_CONDITIONS_PASS`,
`V42_ORACLE_ONLY_CONDITIONING_BOTTLENECK`, `V42_GO_STRUCTURE`, and
`V42_ANOMALOUS_INVERSION` (fifth terminal ACCEPTED by user ruling
2026-08-26; the machine is total):

```text
 0. integrity/execution failure anywhere -> V42_EVIDENCE_INVALID

 1. pass_oracle AND pass_estimated_l1 -> V42_BOTH_CONDITIONS_PASS
      (directional successor description only, unauthorized: Lane C toward
        more-realistic data / end-to-end benchmark)

 2. pass_oracle only -> V42_ORACLE_ONLY_CONDITIONING_BOTTLENECK
      (reason ESTIMATED_L1_ARM_GATE_FAILED; directional attribution: the
        measured loss is attributable to the frozen MAP-L1 conditioning
        mechanism, NOT the Lane C graph structure, and NOT to any concrete
        upstream coding scheme or real system)

 3. neither passes -> V42_GO_STRUCTURE
      (reason BOTH_ARMS_GATES_FAILED; directional attribution: the V41 lane_c
        signal retains block-sample dependence; turn to protograph/MET rather
        than further decoder tuning)

 4. pass_estimated_l1 only -> V42_ANOMALOUS_INVERSION
      (reason ORACLE_ARM_FAILED_WITH_ESTIMATED_L1_ARM_PASSING; claim boundary:
        this state means ONLY that finite-sample effects, iteration
        trajectories, or conditional-posterior differences must be inspected;
        it is NEVER evidence that estimated-L1 outperforms oracle)
```

Rules 1-4 partition the (pass_oracle, pass_estimated_l1) plane over
{both_pass, oracle_only, estimated_only(ANOMALOUS), both_fail} — exhaustive
and mutually exclusive — and rule 0 precedes them: total and disjoint; a
truth-table test enumerating integrity ok/failed x all four combinations and
asserting mutual exclusion is mandatory (tasks T5).

Wrong-codeword handling (user-literal, arm-local; no global rule, no cross-arm
veto — the V41 D4 lesson applied preemptively):

- recorded per record; NEVER counted as exact recovery;
- acts ONLY through its own arm's zero-wrong clause G3';
- additionally sets `stopped_for_analysis[<condition>] = true` for that
  condition's operational path in the summary;
- ANY oracle-arm wrong codeword raises the prominent dedicated flag
  `oracle_arm_wrong_codeword_anomaly = true` (an upper-bound condition should
  not produce wrong codewords) plus a top-level analysis marker.

Under EVERY terminal, without exception: no block addition, no supplementary
run, NO second diagnostic round, no tuning, no post-result threshold or
mechanism edit. Terminals do not auto-start any successor work.

## 10. O3 pairing semantics

- Same block_seed per pair; the deterministic sample
  `(idx, alice, bob) = sample_empirical_block(counts_true, seed=block_seed,
  size=1024)` is computed ONCE per block and passed to both arms (structural
  pairing guarantee, stronger than re-derivation).
- Identical H (source's lane_c ordinal-2 matrix), setting 90/1.0, GF(32)/37,
  syndrome from true `u2_alice`, success metric. The ONLY difference between
  the two calls of a pair is the conditioning selector (Section 6).
- Cross-condition residual differences (`errors_final`, `iterations`,
  `exact_l2`, `syndrome_ok`, `wrong_codeword`) are THE DIAGNOSTIC QUANTITY
  itself and are NEVER integrity failures.

Integrity-check applicability across conditions:

| check class | cross-condition applicability |
|---|---|
| J2 registry / J3 reconstruction / J4 counts / J5 sentinels | applicable (shared preflight, both arms inherit) |
| workload & pairing completeness: each of the 9 blocks decoded exactly once per condition; 18 records total; order = C01-C18 | applicable (J6/J12) |
| budget accounting: ONE shared cap of 18 started/completed actuals across both arms | applicable (J10) |
| record schema, decoder contract, NPZ policy | applicable (J8/J9/J11) |
| outcome-field comparisons across arms (errors_final / iterations / exact_l2 / syndrome_ok / wrong_codeword) | NOT applicable — differences are the measured signal |
| `errors_initial` consistency | WITHIN-condition self-consistency PLUS a STRICT per-pair cross-arm equality gate (revised D14, user ruling 2026-08-26): for every (same-block, two-arm) pair the two arms' `errors_initial` values MUST be strictly equal, evaluated BEFORE the pair's decode calls; any inequality is J6 → `V42_EVIDENCE_INVALID` (rationale verbatim: `errors_initial = sum(u2_alice != u2_bob)` is selector-independent, so cross-arm inequality indicates pairing or evaluator drift). The per-pair `pairing_errors_initial_equal` field is STILL recorded as informational redundancy |

Per-pair paired outcomes recorded in the summary: `both_exact` /
`oracle_only_exact` / `estimated_l1_only_exact` / `neither_exact`, plus
per-block `errors_final` delta (context only, never gated).

## 11. Scientific preflight (decoder-free), guard ordering, evidence tiers

Guard ordering (frozen; V40-revision lesson encoded):

1. **Refusal-class guards FIRST, before any directory creation**: default deny;
   mandatory `--execution-authorized`; exact-equality SHA binding of BOTH
   `git rev-parse HEAD` AND `git rev-parse origin/formal-ir-mainline` with
   `--authorized-target-sha`; scoped tracked-dirty check over the four files
   `(v42 module, v42 CLI, v38_architecture_triage.py,
   v35_algorithm_development.py)`; absence of the output root (J7). Any
   refusal exits non-zero with ZERO calls and creates NOTHING.
2. **Scientific preflights (decoder-free, write-free)**, in order: seed-
   registry validator (J2, five-family union incl. V41); deterministic
   reconstruction of the 3 unique matrices with strict match vs the committed
   structural authority including Lane C `position_permutations` (J3);
   counts shape/loading via the accepted loader for all three sources (J4);
   dual posterior-binding sentinels on the FIRST new block of each source -
   390110 / 390210 / 390310 (J5).
3. **Preflight failure** -> create the formal additive root, write
   `v42_invalid_notice.json` + records(empty) + `v42_summary.json` with
   terminal `V42_EVIDENCE_INVALID`, planned = 18, started = 0, completed = 0,
   and NO aggregation; stop with ZERO decoder calls.
4. **Root creation**: only AFTER all refusal-class guards AND scientific
   preflights pass, BEFORE the first decoder call.

Sentinels per probe block — oracle-arm six (accepted V41 pattern verbatim):
`bob_gt_31`, `captured_equals_bob` (spy-captured second argument element-equal
to complete `bob`), `corrected_equals_direct`, `corrected_differs_u2bob_arraywise`,
`corrected_differs_u2bob_maxabs` (> 1e-6), `argmax_divergence`.
Estimated-L1-arm additions: `map_estimator_public_inputs` (the estimator's
signature admits only counts/bob-derived public inputs — tampered
alice-dependent variants must be rejected by construction/test),
`carrier_identity` (the prior actually passed to the estimated-l1-arm decode
call, captured via spy, element-equal to
`get_conditional_posterior_l2(counts_true, bob, u1_hat)`),
`arms_differ` (estimated-l1 prior differs from oracle prior on at least one
position — proves the arm is genuinely non-oracle),
`l1_accuracy_computable` (mean(u1_hat==u1_alice) computable and within [0,1]).
A failing sentinel probe is replaceable only at plan-review stage.

Integrity checks (scientific-preflight class J2-J5 and decode-loop class
J6/J8-J12 yield `V42_EVIDENCE_INVALID`; J1 and J7 are Tier 0 execution
refusals creating NOTHING):

| id | check |
|---|---|
| J1 | authorization/refusal failure (default deny; missing flags; SHA != exact HEAD and origin/formal-ir-mainline equality; scoped tracked-dirty violation) |
| J2 | seed-registry violation (duplicates among nine; overlap with V36_A3 ∪ V39 ∪ V40-probe ∪ V41 registries; not exactly 3 per source) |
| J3 | matrix reconstruction mismatch vs committed structural authority (incl. Lane C `position_permutations`); representative identity drift |
| J4 | counts shape/loading failure via the accepted loader |
| J5 | sentinel failure (oracle six or non-oracle four) |
| J6 | pairing violation: a block decoded twice in one condition / once total / missing; within-condition `errors_initial` self-consistency failure; STRICT per-pair cross-arm `errors_initial` equality gate — each pair's two arms strictly equal, evaluated BEFORE the pair's decode calls; inequality → `V42_EVIDENCE_INVALID` with zero decoder calls when present at the first pair; rationale: `errors_initial = sum(u2_alice != u2_bob)` is selector-independent — cross-arm inequality means pairing or evaluator drift |
| J7 | output root already exists (fail closed, no overwrite) |
| J8 | NPZ policy violation (any NPZ output; winner-NPZ-class reads; V25 counts access not through the accepted loader) |
| J9 | decoder-parameter contract deviation (Section 6), incl. warm-start keys |
| J10 | call accounting violation (hard cap 18 SHARED across arms; structural refusal of call 19; planned/started/completed mismatch) |
| J11 | record schema violation or missing field |
| J12 | workload drift (call set/order/pairing != frozen C01-C18 of Section 4) |

Mid-run `BaseException`: raw partial records retained byte-for-byte inside the
pre-created root together with notice + summary carrying started/completed
actuals, then re-raised; NO performance aggregate, gate evaluation, or terminal
interpretation other than the failure marker from a partial set.

### Unified three-tier evidence boundary

| tier | trigger | disk effect | process effect |
|---|---|---|---|
| Tier 0 execution refusal | J1 / J7 | NOTHING created | non-zero exit, ZERO calls |
| Tier 1 scientific-preflight failure | J2/J3/J4/J5 | additive root created; invalid trio (notice + empty records + summary, planned 18 / started 0 / completed 0, no aggregation) | ZERO decoder calls; stop, no rerun |
| Tier 2 mid-run `BaseException` | any exception during the decode loop | raw partial records byte-for-byte + notice + summary with actuals + failure marker only | re-raise |
| normal completion | all calls recorded, integrity ok | minimal fixed set: records json/csv + summary; no NPZ | exit 0 |

## 12. Records, aggregation, summary

Record schema (every call):

```
call_id ("C01".."C18"), condition ("cond_oracle"|"cond_estimated_l1"), source,
construction_seed, construction_seed_ordinal, block_seed, matrix_id,
max_iter, damping_alpha, errors_initial, errors_final, exact_l2, syndrome_ok,
wrong_codeword, iterations, status, runtime_s
```

Summary contains (key conventions follow the V40/V41 run_01 summaries):
accounting (planned = 18 / completed actual / started actual,
structural_reconstruction_decoder_calls = 0, preflight_decoder_calls = 0);
`l1_map_accuracy_by_source` (diagnostic context, never gated); per-condition
aggregates (`exact_total`, `exact_by_source`, `wrong_count`); per-source
aggregates; per-block paired outcomes + errors_final deltas; BOTH arms'
gate-evaluation details (each clause G1'/G2'/G3' with numbers and pass/fail)
AFTER terminal determination; routing trace; `terminal_state` +
`terminal_reason`; `stopped_for_analysis` per condition;
`oracle_arm_wrong_codeword_anomaly`; master stop rule verbatim; claim
boundary; statistics note; provenance (authorized target SHA, HEAD/origin
binding, predecessor plan/execution SHAs, structural authority identity, V25
counts provenance, O1-adjudicated mechanism id).

## 13. Statistics and claim boundary

Descriptive only; sample tiny and clustered (18 calls = 9 unique blocks x 2
paired conditions). Exact-recovery proportions reported with n and raw counts;
any printed interval naive and uncorrected for block/arm clustering; no
significance testing. Success means `exact_l2` only.

Claim boundary (verbatim conventions): results support ONLY bounded
conditional-realism attribution on V25 TRAIN empirical-count development
blocks — the oracle arm is a capability UPPER BOUND (true Alice L1, unobtainable
in practice), and the `cond_estimated_l1` arm (frozen Candidate A, adjudicated
2026-08-26) removes ONLY the Alice-L1 oracle while the channel law remains the
TRUE V25 empirical counts; its conditioning is an idealized UNCODED MAP-L1
estimate built from the real public empirical counts, is NOT any concrete
coded/operational L1 reconciliation result, and SHALL NOT be generalized as a
real condition. These are NOT real-frame FER evidence; do not infer threshold,
SKR, formal-execution, qualification, or promotion results. Forbidden
regardless of outcome: FER, asymptotic threshold,
SKR, security, formal qualification, promotion, real-frame behavior, any
superiority or comparative ranking between conditions or lanes, any statement
that historical gates would now pass, any attribution of
`V42_ORACLE_ONLY_CONDITIONING_BOTTLENECK` to a concrete upstream coding scheme
or a real system, and any reading of `V42_ANOMALOUS_INVERSION` as estimated-L1
superiority over oracle. Routing terminals are directional attributions only
and auto-start nothing.

## 14. Evidence writer and additive output root

Fixed future additive root (created before the decode stage so partials
survive; fail-closed if it already exists; also created on scientific-preflight
failure solely to hold the invalid trio):

```
comparison_bench/outputs_comparison/formal_ir_methods/v42_conditional_realism_diagnostic/run_01/
```

Files (minimal fixed set):

- `v42_records.json` / `.csv` (one row per call)
- `v42_summary.json` (Section 12 contents)
- `v42_invalid_notice.json` (only when integrity fails)

CSV/JSON row parity required. Writing ANY `.npz` forbidden; reading any NPZ
except read-only V25 `channel_counts.npz` via the accepted loader forbidden.
Existing `results/`, V38-V41 outputs, and all other official outputs remain
byte-identical.

## 15. Implementation sketch (future rounds, unauthorized now)

- New module
  `comparison_bench/src/comparison_bench/formal_ir/v42_conditional_realism_diagnostic.py`:
  imports accepted v35 primitives (`GF2mField`, `factorize_f03`,
  `get_conditional_posterior_l2`, `decode_row_layered_fftqspa`,
  `load_v25_channel_counts`, `sample_empirical_block`, `syndrome_of_gf32`) and
  v38 constructor/reconstruction helpers (`construct_lane_c_prototype`,
  `_check_v38r1_metric_match`, `_load_v38r1_reference_metrics`,
  `BLOCK_LENGTH`). Composed dual-condition path per design D15. The v39/v40/
  v41 modules are NOT imported; registries enter as copied data constants;
  runner/writer/SHA-binding/scoped-dirty/preflight patterns copied from the
  accepted V39-V41 pattern.
- New CLI `scripts/execute_v42_conditional_realism_diagnostic.py`: default
  deny; mandatory `--execution-authorized --authorized-target-sha <sha>`;
  exact-equality SHA binding of HEAD AND origin/formal-ir-mainline; scoped
  tracked-dirty over the four-file scope (D8); binds `fake_runner=False`; no
  fake-runner CLI option; non-zero exit with zero calls and nothing created on
  any guard failure.
- Focused fake-runner tests only; no production decode in tests.

## 16. Discretionary decisions D1-D15 (main-thread review list)

- **D1 shape**: single-phase paired diagnostic, Lane C only, exactly 18 calls,
  no baseline/staging/additional matrices.
- **D2 seed registry**: nine seeds x10-x12 per source frozen; FORBIDDEN union =
  V36_A3 ∪ V39 ∪ V40-probe ∪ V41-confirm (42 seeds, now INCLUDING V41);
  planning-time verification shows ZERO overlap, no duplicates; implementation
  re-asserts (J2).
- **D3 representative matrices**: three lane_c ordinal-2 ids written dead
  (Section 5); strict-match reconstruction instead of importing v41 facts.
- **D4 wrong-codeword scope**: arm-local only (G3' + stopped_for_analysis +
  oracle anomaly flag); no global wrong rule, no cross-arm veto.
- **D5 gate thresholds**: mirror V41 form per arm (>=7/9 overall, >=2/3 per
  source, zero wrong).
- **D6 sentinel placement**: first new block of each source
  (390110/390210/390310).
- **D7 call order**: sources 1M/1p5M/2M, blocks ascending, cond_oracle before
  cond_estimated_l1 within a pair (C01-C18).
- **D8 scoped-dirty scope**: v42 module + v42 CLI + v38 module + v35 module.
- **D9 preflight-failure evidence policy**: invalid trio with zero calls;
  refusal-class guards create nothing (V40 revision lesson encoded).
- **D10 file set**: minimal fixed set; no NPZ writes ever.
- **D11 terminal naming**: five terminals incl. ACCEPTED
  `V42_ANOMALOUS_INVERSION` covering the (oracle_fail, estimated_l1_pass)
  cell (user ruling 2026-08-26).
- **D12 successor language**: directional descriptions only (Section 1/9);
  none authorizes anything.
- **D13 O1 mechanism**: RESOLVED by user adjudication 2026-08-26 — Candidate A
  (estimated-L1 hard MAP conditioning, channel law unchanged) frozen as
  `cond_estimated_l1` with the verbatim definition and naming boundary of
  Section 7; alternatives B/C rejected; the former "未裁决前禁止进入实现" bar
  is LIFTED; the mechanism may not be changed afterwards.
- **D14 errors_initial policy** (revised by user ruling 2026-08-26): STRICT
  per-pair cross-arm equality is now a J6 gate — for each (same-block,
  two-arm) pair the arms' `errors_initial` must be strictly equal, checked
  BEFORE the pair's decode calls; inequality → `V42_EVIDENCE_INVALID`
  (rationale: `errors_initial = sum(u2_alice != u2_bob)` is
  selector-independent; cross-arm inequality indicates pairing or evaluator
  drift). The per-pair `pairing_errors_initial_equal` field remains recorded
  as informational redundancy.
- **D15 composed dual-condition path**: replaces wholesale reuse of
  `evaluate_single_block` (oracle conditioning hardcoded at v38:995;
  counts-dual-use sampling hazard); single code path, injectable `decode_fn`;
  plan-review attention item.
