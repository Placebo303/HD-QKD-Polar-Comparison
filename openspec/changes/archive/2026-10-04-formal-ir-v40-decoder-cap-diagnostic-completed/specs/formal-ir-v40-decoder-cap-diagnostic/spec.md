# Delta Specification: formal-ir-v40-decoder-cap-diagnostic

**Cycle**: `V40P0`
**Lifecycle of this change**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`

## R1. Predecessor binding

V40P0 SHALL build only on the V39P0 run_01 evidence
(`v39_lanec_robustness_laneb_control/run_01`, execution SHA
`90d2d834c136833000ad612adfd8e09bf815d5d2`, plan SHA
`8efb626ba0eaa6b031abd934ed583739ba70065b`, terminal
`V39_NO_ROBUST_ROUTE_SIGNAL`, lifecycle `DEVELOPMENT_RESULT_ACCEPTED`,
result SHA `940bfc996a0bd87d60e958150c4f770ee35f16b8`). The V39 evidence
SHALL be treated as accepted; no V39 review precondition applies. V40
execution authorization SHALL require only V40's own independent plan
ACCEPT plus explicit user `EXECUTE_AUTH`. The diagnostic SHALL NOT
retroactively alter the V39 terminal state or any historical Lane B/C
conclusion.

## R2. Diagnostic question and shape

The change SHALL answer exactly one question — how much V39 failure is
attributable to the decoder iteration cap — using at most 30 real decoder
calls: Phase A exactly 12 (always), Phase B conditionally exactly 12,
probe conditionally exactly 6. Rescues SHALL NOT be counted as Lane B/C
route successes and SHALL NOT auto-start successor work.

## R3. Frozen instance set

The Phase A/B instance set SHALL be exactly the 12 instances (6 lane_c +
6 lane_b, all source `1M`) underlying the six `NEITHER_EXACT` pairs of
the committed `v39_paired_comparison.json`, in the frozen order A01–A12
(design Section 3). Extraction drift in membership or order SHALL be
integrity failure J1. "Rescue" SHALL mean a record with V39
`exact_l2 == false` whose phase record has `exact_l2 == true` at
identical `(lane, source, ordinal, block_seed)` and identical
`errors_initial`.

## R4. Representative matrices

Per lane, the representative construction-seed ordinal SHALL be the
`by_construction_seed_ordinal` overall `exact_count` argmax from the V39
run_01 summary (ties -> lowest ordinal). Resolved against the actual data
and frozen: **lane_c = ordinal 2** (matrices `lane_c_{1M,1p5M,2M}_s383102/
383202/383302`), **lane_b = ordinal 2** (`lane_b_..._s382102/382202/382302`).
Because prototypes are source-specific, each probe block SHALL use its
own source's matrix at that ordinal. Preflight SHALL recompute the argmax
from the committed summary and fail (J3) on any mismatch with these
constants.

## R5. Probe blocks and seed disjointness

Probe block seeds SHALL be exactly 1M = 390106, 1p5M = 390206,
2M = 390306 — one never-used TRAIN development block per source, sampled
with `sample_empirical_block(V25 TRAIN counts, seed, 1024)` +
`factorize_f03`. A mechanical assertion (J4) SHALL verify no duplicate
and no overlap with the V36_A3 seeds reused by V38/V38R1
(360101–360105 / 360201–360205 / 360301–360305) nor the V39 registry
(390101–390105 / 390201–390205 / 390301–390305).

## R6. Posterior-binding preflight

Before any authorized execution, a decoder-free, write-free preflight
SHALL verify, on probe blocks 390106/390206/390306, ALL of:
`np.any(bob > 31) == True`; the captured second argument of
`get_conditional_posterior_l2` element-equal to complete `bob`;
`prior_corrected` element-equal to the direct complete-bob call;
`prior_corrected` NOT element-equal to the `u2_bob` prior;
`max(abs(prior_corrected - prior_u2_bob)) > 1e-6`; and at least one
position where the posteriors' `argmax` differs. The preflight SHALL make
zero production decoder calls and write nothing; failure SHALL block
authorization; sentinel probes are replaceable only at plan-review stage.

## R7. Decoder contract per phase

All calls SHALL use GF(32) primitive polynomial 37, row-layered FFT-QSPA
via the accepted evaluator, syndrome from true `u2_alice`, complete-Bob
posterior with oracle-L1 conditioning, and success = `exact_l2` only.
Phase-specific parameters SHALL be exactly: Phase A (max_iter=90,
damping_alpha=1.0); Phase B (max_iter=90, damping_alpha=0.7); Probe
(max_iter=90, damping_alpha=1.0 on trigger (i), 0.7 on trigger (ii)).
No warm start, no third setting, no retry. `wrong_codeword =
syndrome_ok and not exact_l2` SHALL be counted separately and NEVER as
exact recovery. Any deviation is J10.

## R8. Phase A protocol and judgments

Phase A SHALL decode exactly the 12 instances of R3 once each at the
Phase A settings. Judgments (evaluated after the global wrong-codeword
guard): any new wrong codeword → terminal `STOP_BC_PARAMETER_OPTIMIZATION`
(reason `WRONG_CODEWORD_PHASE_A`), making Phase B and the probe
unreachable; rescued >= 4 (out of 12) with zero wrong codewords →
`CAP_MATERIAL` (Phase B skipped; probe eligible at 90/1.0); rescued
2–3 (out of 12) with zero wrong codewords → `WEAK_RESIDUAL` (no Phase B,
no probe; terminal `GO_STRUCTURE`, reason `WEAK_EXACT_RESCUE`);
rescued <= 1 (out of 12) with zero wrong codewords and residual
improvement < 25% → stop the decoder parameter direction (`GO_STRUCTURE`,
reason `NO_MATERIAL_CAP_EFFECT`); rescued <= 1 (out of 12) with zero wrong
codewords and residual improvement >= 25% → `RESIDUAL_ONLY_NO_EXACT_RESCUE`,
the only Phase B trigger.

## R9. Residual-improvement definition

For phase P, let S_P be the still-non-exact instances after P.
`IMP_P = 1 - median(errors_final over S_P in P) / median(errors_final
over the SAME instances in their V39 run_01 records)` (matched-subset
denominator口径; pooled all-12 V39 median 155.0 reported descriptively).
If S_P is empty, `IMP_P := 1.0`. A zero denominator median is impossible
for the frozen set (minimum reference residual 75) and raises J2.
"Improvement >= 25%" ⇔ `IMP_A >= 0.25`.

## R10. Phase B protocol and judgments

Phase B SHALL run iff Phase A emitted `RESIDUAL_ONLY_NO_EXACT_RESCUE`
(i.e. `W_A == 0` AND `R_A <= 1 (out of 12)` AND `IMP_A >= 0.25`),
decoding the same 12 instances in the same order at the Phase B settings —
the ONLY difference from Phase A being damping. Judgments: any wrong
codeword in Phase B → terminal `STOP_BC_PARAMETER_OPTIMIZATION` (reason
`WRONG_CODEWORD_PHASE_B`); `DAMPING_VALUE` iff
`R_B_new >= 3 (out of 12)` AND zero wrong codewords in Phase B → probe at
90/0.7; otherwise the routing signal `DAMPING_NO_VALUE` (not a terminal)
SHALL yield terminal `GO_STRUCTURE` with reason `DAMPING_NO_VALUE`:
decoder tuning stops entirely and no damping grid is constructed under any
outcome. Under `CAP_MATERIAL` (`R_A >= 4 (out of 12)`) or `WEAK_RESIDUAL`
(`R_A = 2–3 (out of 12)`), Phase B SHALL be skipped.

## R11. Probe protocol and judgments

The probe SHALL run only when (i) `CAP_MATERIAL` fired — which by rule
ordering implies zero wrong codewords so far, with Phase B skipped
(setting 90/1.0) — or (ii) Phase B ran and produced `DAMPING_VALUE`
(which implies zero wrong codewords in BOTH phases, since any wrong
codeword terminates earlier) (setting 90/0.7); triggers are mutually
exclusive by construction (`CAP_MATERIAL` requires `R_A >= 4 (out of
12)`, the Phase B path requires `R_A <= 1 (out of 12)`), so the probe
setting is always unique.
Workload: 6 calls = {1M, 1p5M, 2M} x {lane_c, lane_b} with each block
decoded by its source's representative matrix per lane (R4), in the
frozen call order PR1–PR6. The probe SHALL output and freeze the
aggregate fields `exact_total`, `exact_lane_c`, `exact_lane_b`,
`wrong_lane_c`, `wrong_lane_b`. Judgments (exhaustive and mutually
exclusive): any wrong codeword → `STOP_BC_PARAMETER_OPTIMIZATION`; else
`exact_total <= 2/6` → `STOP_BC_PARAMETER_OPTIMIZATION`; else
`exact_total == 3/6` → `PROBE_INCONCLUSIVE` (no further calls); else
`exact_total >= 4/6` with either lane < 2/3 → `PROBE_INCONCLUSIVE`; else
(`exact_total >= 4/6` and both lanes >= 2/3) → `PROBE_CONFIRM_ALLOWED`
(permits exactly one future fresh-block confirmation cycle under a NEW
OpenSpec change and authorization; nothing auto-started).

## R12. Budget and stop rules

Total budget SHALL NOT exceed 30 real decoder calls
(A=12 + B=12 + probe=6; A+probe without B = 18), executed exactly once
with no rerun and no resume. The master stop rule SHALL be recorded
verbatim in the summary:

> 不同时继续优化 B、C、decoder 和新算法；先用 12 calls 判断 decoder cap；
> 没有强信号就把额度投入 protograph/MET。

## R13. Signals and terminal machine

Routing signals: `CAP_MATERIAL`, `WEAK_RESIDUAL`,
`RESIDUAL_ONLY_NO_EXACT_RESCUE` (`R_A <= 1 (out of 12)` with
`IMP_A >= 0.25`),
`DAMPING_VALUE`, `DAMPING_NO_VALUE` (routing signal only — no terminal is
named after it; its terminal is `GO_STRUCTURE` with reason
`DAMPING_NO_VALUE`). Terminals: `V40_EVIDENCE_INVALID`,
`V40_GO_STRUCTURE`,
`V40_STOP_BC_PARAMETER_OPTIMIZATION`, `V40_PROBE_INCONCLUSIVE`,
`V40_PROBE_CONFIRM_ALLOWED`. With integrity-first precedence and
first-match-wins, the machine SHALL implement design Section 13 rules 0–6
exactly, including: any `W_A > 0` → terminal
`STOP_BC_PARAMETER_OPTIMIZATION` (reason `WRONG_CODEWORD_PHASE_A`) with
Phase B and the probe unreachable; `R_A = 2–3 (out of 12)` →
`WEAK_RESIDUAL` → `GO_STRUCTURE` (reason `WEAK_EXACT_RESCUE`) without
Phase B or probe; `R_A <= 1 (out of 12)` with `IMP_A < 0.25` →
`GO_STRUCTURE` (reason
`NO_MATERIAL_CAP_EFFECT`); any `W_B > 0` →
`STOP_BC_PARAMETER_OPTIMIZATION` (reason `WRONG_CODEWORD_PHASE_B`). The
mapping SHALL be total and disjoint over all reachable combinations,
proven by a mandatory truth-table test that also asserts impossible
combinations cannot fire (e.g., a probe while `W_A > 0`, Phase B while
`W_A > 0` or `R_A >= 2 (out of 12)`, or an ambiguous probe setting).

## R14. Records and evidence outputs

Every call SHALL produce one record with the schema of design Section 12
(incl. phase, per-phase max_iter/damping_alpha, V39 references,
`rescued_vs_v39`). The authorized run SHALL write ONLY, under additive
root `comparison_bench/outputs_comparison/formal_ir_methods/v40_decoder_
cap_diagnostic/run_01/`: `v40_diagnostic_records.json/.csv`,
`v40_summary.json`, and, only on integrity failure,
`v40_invalid_notice.json`. CSV/JSON parity required. Writing any NPZ
SHALL NOT occur; reading `v38_winning_matrices.npz` SHALL NOT occur;
read-only V25 counts access via the accepted loader is permitted with
provenance. The summary SHALL contain planned/completed/started actuals
per phase and total, signals, IMP values and both medians, rescue/wrong
counts, frozen probe aggregates (`exact_total`, `exact_lane_c`,
`exact_lane_b`, `wrong_lane_c`, `wrong_lane_b`), routing trace, terminal
state and reason, claim boundary,
statistics note, and provenance SHAs. Existing V38/V39 outputs SHALL
remain byte-identical. The output root SHALL be created before the
decoder stage and `BaseException` handlers SHALL preserve raw partial
records byte-for-byte with started/completed actuals, without generating
performance aggregates from a partial set.

## R15. Integrity-first invalidation

Integrity failures J1–J12 (design Section 11) SHALL force terminal
`V40_EVIDENCE_INVALID` with `v40_invalid_notice.json`; performance SHALL
NOT be interpreted on invalid evidence. After a mid-run execution
failure, partial evidence MAY be retained but SHALL NOT be aggregated
into results.

## R16. Lifecycle and authorization

Implementation candidates stop at `IMPLEMENTATION_CANDIDATE /
EXECUTE_NOT_AUTHORIZED`. The single diagnostic execution requires an
independent plan ACCEPT plus explicit user `EXECUTE_AUTH` bound to the
repository, branch, full implementation SHA, cycle V40P0, and scope
`v40_decoder_only_max30_calls_exactly_once`. The CLI SHALL default-deny,
require `--execution-authorized` and `--authorized-target-sha`, and
verify exact equality of BOTH `git rev-parse HEAD` and
`git rev-parse origin/formal-ir-mainline` with the target SHA (ancestor
or contains checks insufficient), plus a scoped tracked-dirty check over
(v40 module, v40 CLI, v38 module, v35 module). No rerun, tuning,
post-result threshold edit, post-result seed addition, self-acceptance,
or automatic successor authorization is permitted.

## R17. Claim boundary

Results support only bounded diagnostic statements about the iteration
cap's contribution on empirical-count development samples with oracle-L1
conditioning. FER, asymptotic threshold, SKR, security, formal
qualification, promotion, real-frame claims, Lane C/Lane B superiority
claims, and any statement that V39 gates would now pass remain forbidden
regardless of outcome. Rescue proportions come from tiny clustered
samples (3 unique blocks x 2 lanes per gated phase; 3 new blocks x 2
lanes on probe) and clustering is uncorrected; success means `exact_l2`
only.
