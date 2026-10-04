# Delta Specification: formal-ir-v42-conditional-realism-diagnostic

**Cycle**: `V42P0`
**Lifecycle of this change**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`

## R1. Predecessor binding

V42P0 SHALL build only on the V41P0 run_01 evidence (terminal
`V41_C_ONLY_RETAINED`; lane_c exact 8/9 with per-source 3/3/2, lane_b gates
failed 6/9, zero wrong codewords; recorded lifecycle
`DEVELOPMENT_RESULT_CANDIDATE`; implementation/execution SHA
`6d75e754899e8470445c2bf58f2f4ff84130fc33`). That terminal authorizes nothing
by itself. V42 SHALL NOT retroactively alter the V41 terminal state, recorded
lifecycle, or any historical conclusion, and SHALL NOT import the v39/v40/v41
modules. V42 execution authorization SHALL require only V42's own independent
plan ACCEPT plus explicit user `EXECUTE_AUTH` bound to the repository, branch,
full implementation SHA, cycle V42P0, and scope
`v42_diagnostic_18_calls_exactly_once`.

## R2. Question and shape

The change SHALL answer exactly one question — does Lane C retain its fresh-
block signal when oracle-L1 conditioning (`cond_oracle`) is replaced by the
frozen idealized uncoded MAP-L1 estimated condition `cond_estimated_l1`
(Candidate A frozen per design Section 7 / D13 RESOLVED 2026-08-26; definition
verbatim in R7) — using EXACTLY 18 real decoder calls in a single executed
phase, exactly once: nine blocks, each decoded exactly twice as a paired run
under `cond_oracle` and `cond_estimated_l1`. Lane C only. There SHALL be no
baseline run, no additional matrices beyond the three frozen lane_c ordinal-2
representatives, no decoder-parameter tuning under any outcome, and no reuse of
any prior-cycle block as a diagnostic sample.

## R3. Frozen sample set and pairing

The sample SHALL be exactly nine new TRAIN development blocks, pre-registered
as frozen constants: 1M = 390110/390111/390112, 1p5M = 390210/390211/390212,
2M = 390310/390311/390312, sampled with
`sample_empirical_block(V25 TRAIN counts, block_seed, 1024)` + `factorize_f03`.
The per-block deterministic sample `(idx, alice, bob)` SHALL be computed ONCE
and shared by both arms of its pair; the two calls of a pair SHALL differ ONLY
in the conditioning selector fed to the posterior function.

## R4. Seed-registry disjointness

A mechanical registry assertion (J2) SHALL verify at implementation time: no
duplicate among the nine seeds; ZERO overlap with the union of the V36_A3
seeds reused by V38/V38R1 (360101-360105 / 360201-360205 / 360301-360305), the
V39 registry (390101-390105 / 390201-390205 / 390301-390305), the V40 probe
seeds (390106/390206/390306), AND the V41 confirmation seeds (390107-390109 /
390207-390209 / 390307-390309); and exactly three new blocks per source.
Registries enter as copied data constants.

## R5. Representative matrices

Lane C SHALL use its ordinal-2 representative matrix per source, frozen as
constants: `lane_c_1M_s383102`, `lane_c_1p5M_s383202`, `lane_c_2M_s383302`.
The 18 usage rows deduplicate to exactly 3 unique matrices. Preflight SHALL
reconstruct all three deterministically via the accepted constructors and fail
(J3) on any strict-metric mismatch with the committed structural authority,
including Lane C `position_permutations`, or on any representative identity
drift.

## R6. Dual posterior-binding preflight

Before any authorized execution, a decoder-free, write-free preflight SHALL
verify, on the FIRST new block of each source (390110/390210/390310):
(a) the six accepted oracle sentinels (`bob_gt_31`; captured second argument
element-equal to complete `bob`; corrected-equals-direct; corrected-differs-
u2bob arraywise; max-abs difference > 1e-6; argmax divergence); and (b) the
four `cond_estimated_l1` sentinels: `map_estimator_public_inputs`,
`carrier_identity` (the prior actually passed to the `cond_estimated_l1` decode
call, captured via spy, element-equal to
`get_conditional_posterior_l2(counts_true, bob, u1_hat)`),
`arms_differ` (`cond_estimated_l1` prior differs from oracle prior on at least
one position), and `l1_accuracy_computable`. Zero production decoder calls;
failure routes to the R11 invalid path; sentinel probes are replaceable only at
plan-review stage.

## R7. Decoder contract and composed dual-condition path

All 18 calls SHALL use GF(32) primitive polynomial 37, row-layered FFT-QSPA via
the accepted decode function, syndrome from true `u2_alice`, complete-Bob
posterior computed by the accepted `get_conditional_posterior_l2`, success =
`exact_l2` vs true `u2_alice` only, single fixed setting
`max_iter=90, damping_alpha=1.0`. No warm start, no retry, no second setting.
The oracle arm's selector SHALL be true `u1_alice`; the `cond_estimated_l1`
arm's selector SHALL be exactly the frozen Candidate A mechanism (design
Section 7 / D13 RESOLVED 2026-08-26) with verbatim definition:

- `u1_hat(b) = argmax_u1 Σ_u2 counts[u1*32+u2, b]`
- prior uses `get_conditional_posterior_l2(counts_true, bob, u1_hat)`
- sampling still only uses the same `counts_true`; both arms share the once-generated block
- no pilot, noise, quantization, or mismatched channel law SHALL be introduced

Naming boundary (binding): `cond_estimated_l1` is "using the true public
empirical counts, idealized uncoded MAP-L1 estimate" — it is NOT any concrete
operational L1 reconciliation and SHALL NOT be generalized as a real condition;
an `V42_ORACLE_ONLY_CONDITIONING_BOTTLENECK` outcome attributes the loss ONLY
to this frozen MAP-L1 conditioning mechanism, never to a concrete upstream
coding scheme or a real system. The mechanism identity SHALL be asserted against
the frozen constant and SHALL NOT change afterwards. Because
`evaluate_single_block` hardcodes oracle conditioning and dual-uses its
`counts` argument for sampling, the runner SHALL compose the accepted v35
primitives in one thin dual-condition path replicating v38 lines 992-1030
except the selector (design D15); all numerics imported from accepted modules;
no frozen file modified. `wrong_codeword = syndrome_ok and not exact_l2`
SHALL be counted separately and NEVER as exact recovery. Any deviation is J9.

## R8. Frozen workload and call order

The workload SHALL be exactly C01-C18 (design Section 4): sources in
1M/1p5M/2M order, blocks ascending by seed within a source, `cond_oracle` before
`cond_estimated_l1` within a pair. Any membership, order, or pairing drift is
J12.

## R9. Per-condition gates

For each condition arm independently, on its own 9 calls: G1' overall exact
>= 7 out of 9; G2' every source exact >= 2 out of 3; G3' that arm wrong
codewords = 0. An arm passes iff all three hold. Gates judge CONDITION
RETENTION/attribution only and SHALL NOT support any superiority or
comparative-ranking statement between conditions or lanes regardless of
outcome.

## R10. Terminal machine

Terminals (five, total and disjoint): `V42_EVIDENCE_INVALID`,
`V42_BOTH_CONDITIONS_PASS`, `V42_ORACLE_ONLY_CONDITIONING_BOTTLENECK`,
`V42_GO_STRUCTURE`, and `V42_ANOMALOUS_INVERSION` (ACCEPTED per user ruling
2026-08-26; covers `oracle_fail && estimated_l1_pass`). With integrity-first
precedence and first-match-wins:

```
0. integrity/execution failure anywhere -> V42_EVIDENCE_INVALID
1. pass_oracle AND pass_estimated_l1 -> V42_BOTH_CONDITIONS_PASS
2. pass_oracle only -> V42_ORACLE_ONLY_CONDITIONING_BOTTLENECK
      (reason ESTIMATED_L1_ARM_GATE_FAILED)
3. neither passes -> V42_GO_STRUCTURE (reason BOTH_ARMS_GATES_FAILED)
4. pass_estimated_l1 only -> V42_ANOMALOUS_INVERSION
      (reason ORACLE_ARM_FAILED_WITH_ESTIMATED_L1_ARM_PASSING)
```

`V42_ANOMALOUS_INVERSION` claim boundary: this state means ONLY that
finite-sample effects, iteration trajectories, or conditional-posterior
differences require inspection; it SHALL NEVER be interpreted as evidence that
`cond_estimated_l1` outperforms oracle.

`V42_ORACLE_ONLY_CONDITIONING_BOTTLENECK` claim boundary: the measured loss is
attributable ONLY to the frozen MAP-L1 conditioning mechanism
(`cond_estimated_l1`), NOT the Lane C graph structure, and NOT to any concrete
upstream coding scheme or real system.

Wrong-codeword handling is ARM-LOCAL ONLY: recorded, never counted as exact,
acting exclusively through its own arm's G3' zero-wrong clause; additionally
setting `stopped_for_analysis[<condition>] = true` for that condition's
operational path; there is NO global wrong rule and NO cross-arm veto. ANY
oracle-arm wrong codeword SHALL raise the prominent dedicated flag
`oracle_arm_wrong_codeword_anomaly = true` with a top-level analysis marker
(an upper-bound condition should not produce wrong codewords). The mapping
SHALL be total and disjoint over all (oracle_pass, estimated_l1_pass)
combinations, proven by a mandatory truth-table test enumerating integrity
ok/failed x all four cells {both_pass, oracle_only, estimated_only(ANOMALOUS),
both_fail} and asserting exhaustive mutual exclusion. Terminal determination
precedes gate-detail display; the summary SHALL still report each arm's wrong
count separately.

Successor directions are directional descriptions recorded in the summary ONLY
and authorize nothing: BOTH_CONDITIONS_PASS -> Lane C toward more-realistic
data / end-to-end benchmark; ORACLE_ONLY_CONDITIONING_BOTTLENECK -> loss
attributable to the frozen MAP-L1 conditioning mechanism, NOT Lane C graph
structure; GO_STRUCTURE -> V41 lane_c signal retains block-sample dependence,
turn toward protograph/MET rather than further decoder tuning;
ANOMALOUS_INVERSION -> analysis required, no direction authorized. Under EVERY
terminal: no block addition, no supplementary run, NO second diagnostic round,
no tuning, no post-result threshold/mechanism edit.

## R11. Integrity-first invalidation, guard ordering, and evidence tiers

The runner SHALL implement the three-tier evidence boundary of design Section
11 one-to-one:

- **Tier 0 execution refusal** (J1 default deny / mandatory flags / exact SHA
  equality of BOTH `git rev-parse HEAD` AND
  `git rev-parse origin/formal-ir-mainline` with `--authorized-target-sha` /
  scoped tracked-dirty over v42 module + v42 CLI + v38 module + v35 module;
  J7 output root exists) runs FIRST, fails closed, creates NOTHING, exits
  non-zero with ZERO decoder calls.
- **Tier 1 scientific-preflight failure** (J2 registry incl. V41 family, J3
  reconstruction strict match, J4 counts shapes, J5 sentinels) follows,
  decoder-free; on ANY failure the runner SHALL create the additive root and
  write the invalid trio — `v42_invalid_notice.json`, empty records,
  `v42_summary.json` with terminal `V42_EVIDENCE_INVALID`, planned = 18
  (fixed), started = 0, completed = 0, no aggregation — and stop with ZERO
  real decoder calls and no rerun.
- **Tier 2 mid-run execution failure**, caught at `BaseException`: raw partial
  records retained byte-for-byte inside the pre-created root together with a
  notice + summary carrying started/completed actuals and only the failure
  marker, then re-raised.
- **Normal completion**: only the minimal fixed set (records json/csv +
  summary; no NPZ).

Integrity failures J1-J12 (design Section 11 table) force
`V42_EVIDENCE_INVALID`; performance SHALL NOT be interpreted on invalid or
partial evidence. Cross-condition outcome-field comparisons (`errors_final` /
`iterations` / `exact_l2` / `syndrome_ok` / `wrong_codeword`) SHALL NEVER be
treated as integrity failures — they are the diagnostic signal itself. J6 is
the STRICT per-pair cross-arm `errors_initial` equality gate (revised D14 per
user ruling 2026-08-26; design Section 10/O3): for every (same-block, two-arm)
pair the two arms' `errors_initial` values MUST be strictly equal, evaluated
BEFORE the pair's decode calls; any inequality is J6 ->
`V42_EVIDENCE_INVALID` (rationale verbatim:
`errors_initial = sum(u2_alice != u2_bob)` is selector-independent, so
cross-arm inequality indicates pairing or evaluator drift). The per-pair
`pairing_errors_initial_equal` field SHALL still be recorded as informational
redundancy in the summary.

## R12. Budget and stop rules

Total budget SHALL NOT exceed 18 real decoder calls SHARED across both arms;
the 19th call SHALL be structurally refused (J10). Execution is exactly once,
with no rerun and no resume. The master stop rule SHALL be recorded verbatim
in the summary:

> 唯一一次 18-call 双条件配对诊断；仅 Lane C、固定各 source ordinal-2 代表矩阵、max_iter=90、damping_alpha=1.0，不再调参；cond_estimated_l1 机制按用户裁决 Candidate A 冻结（u1_hat(b)=argmax_u1 Σ_u2 counts[u1*32+u2,b]，prior=get_conditional_posterior_l2(counts_true,bob,u1_hat)，采样共享同一 counts_true，无 pilot/噪声/量化/失配信道律）后不再更改。无论结果如何：不追加 blocks、不补跑、不做第二轮诊断。

## R13. Records and evidence outputs

Every call SHALL produce one record with the schema of design Section 12
(including `condition`). The authorized run SHALL write ONLY, under additive
root
`comparison_bench/outputs_comparison/formal_ir_methods/v42_conditional_realism_diagnostic/run_01/`:
`v42_records.json/.csv`, `v42_summary.json`, and, only on integrity failure,
`v42_invalid_notice.json`. CSV/JSON parity required. Writing any NPZ SHALL NOT
occur; reading any NPZ except read-only V25 counts via the accepted loader
SHALL NOT occur. The output root SHALL be created after all guards and
preflights pass and before the first decoder call, fail-closed on existence
(J7). The summary SHALL contain planned/completed/started actuals,
`l1_map_accuracy_by_source` (diagnostic context, never gated), per-condition
aggregates (`exact_total`, per-source counts, wrong counts), per-block paired
outcomes with errors_final deltas, BOTH arms' gate-evaluation details ordered
after terminal determination, routing trace, terminal state + reason,
`stopped_for_analysis` markers, `oracle_arm_wrong_codeword_anomaly` flag when
applicable, the verbatim stop rule, claim boundary, statistics note, and
provenance including the O1-adjudicated mechanism id. Existing results/, V38/
V39/V40/V41 outputs SHALL remain byte-identical.

## R14. Lifecycle, authorization, and O1 precondition

Lifecycle of this change SHALL remain `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`
until independent plan ACCEPT. Implementation candidates stop at
`IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`. D13 (O1
`cond_estimated_l1` mechanism) is RESOLVED per user adjudication 2026-08-26:
Candidate A frozen as `cond_estimated_l1` with the verbatim definition of R7
and naming boundary; it SHALL NOT change afterwards. The single diagnostic
execution requires an explicit user `EXECUTE_AUTH` bound to the repository,
branch, full implementation SHA, cycle V42P0, scope
`v42_diagnostic_18_calls_exactly_once`. The CLI SHALL default-deny, require
`--execution-authorized --authorized-target-sha <sha>`, verify exact SHA
equality of HEAD AND origin/formal-ir-mainline (ancestor or contains checks
insufficient), and perform the scoped tracked-dirty check. No rerun, tuning,
threshold edit, mechanism swap, seed addition, self-acceptance, or automatic
successor start is permitted.

## R15. Claim boundary

Results support ONLY bounded conditional-realism attribution on V25 TRAIN
empirical-count development blocks. The oracle arm is a capability UPPER BOUND
using true Alice L1, unobtainable in practice. The `cond_estimated_l1` arm
(Candidate A, adjudicated 2026-08-26) removes ONLY the Alice-L1 oracle while
the channel law stays the TRUE V25 empirical counts; its conditioning is an
idealized uncoded MAP-L1 estimate `u1_hat(b) = argmax_u1 Σ_u2
counts[u1*32+u2, b]` built from the real public empirical counts via
`get_conditional_posterior_l2(counts_true, bob, u1_hat)`, with sampling still
only from the same `counts_true` and both arms sharing the once-generated block
(no pilot/noise/quantization/mismatched law), and is NOT any concrete
coded/operational L1 reconciliation result and SHALL NOT be generalized as a
real condition. An `V42_ORACLE_ONLY_CONDITIONING_BOTTLENECK` outcome attributes
the loss ONLY to this frozen MAP-L1 conditioning mechanism, never to a concrete
upstream coding scheme or a real system; `V42_ANOMALOUS_INVERSION` means ONLY
that finite-sample, iteration-trajectory, or conditional-posterior differences
require inspection and is NEVER evidence that `cond_estimated_l1` outperforms
oracle. These are not real-frame FER evidence; threshold, SKR,
formal-execution, qualification, or promotion results SHALL NOT be inferred.
Forbidden regardless of outcome: FER, asymptotic threshold, SKR, security,
formal qualification, promotion, real-frame claims, any superiority or
comparative ranking between conditions or lanes, and any statement that
historical gates would now pass. Success means `exact_l2` only; samples are
tiny and clustered (9 unique blocks x 2 paired conditions) and clustering is
uncorrected.
