# Delta Specification: formal-ir-v41-fresh-block-confirm

**Cycle**: `V41P0`
**Lifecycle of this change**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`

## R1. Predecessor binding

V41P0 SHALL build only on the V40P0 run_01 evidence (terminal
`V40_PROBE_CONFIRM_ALLOWED`, probe exact_total 5/6 with lane_c 3/3 and lane_b
2/3 and zero wrong codewords; lifecycle `DEVELOPMENT_RESULT_ACCEPTED`;
result SHA `a546d43c74be5f11e87426ff7ce837b31dd20142`; execution SHA
`80d605489f1f65eefd091625134514e8a09902de`; accepted plan SHA, historical
reference, `36a3751e190ff06e0e88024b51b6f8713c13a4dc`). That terminal marks
that EXACTLY ONE fresh-block confirmation may be proposed under a NEW
OpenSpec change - this change - and by itself authorizes nothing. V41 SHALL
NOT retroactively alter the V40 terminal state, lifecycle, or any historical
Lane B/C conclusion. V41 execution authorization SHALL require only V41's
own independent plan ACCEPT plus explicit user `EXECUTE_AUTH`.

## R2. Question and shape

The change SHALL answer exactly one question - do Lane C and Lane B each
independently retain their route signal on nine never-used blocks at the fixed
setting - using EXACTLY 18 real decoder calls in a single executed phase,
exactly once. There SHALL be no baseline run, no Phase B staging, no
additional matrices, no decoder-parameter tuning under any outcome, and NO
reuse of the V40 probe blocks (390106/390206/390306) as confirmation samples.

## R3. Frozen sample set

The confirmation sample SHALL be exactly nine new TRAIN development blocks,
pre-registered as frozen constants: 1M = 390107/390108/390109,
1p5M = 390207/390208/390209, 2M = 390307/390308/390309, one seed per source
triple, sampled with `sample_empirical_block(V25 TRAIN counts, block_seed,
1024)` + `factorize_f03`. Each block SHALL be decoded exactly once per lane;
cross-lane `errors_initial` equality per block SHALL be asserted (J6).

## R4. Seed-registry disjointness

A mechanical registry assertion (J2) SHALL verify at implementation time:
no duplicate among the nine seeds; ZERO overlap with the V36_A3 seeds reused
by V38/V38R1 (360101-360105 / 360201-360205 / 360301-360305), the V39
registry (390101-390105 / 390201-390205 / 390301-390305), and the V40 probe
seeds (390106/390206/390306); and exactly three new blocks per source.
Registries enter as copied data constants; the v39/v40 modules SHALL NOT be
imported.

## R5. Representative matrices

Both lanes SHALL use their ordinal-2 representative matrix per source, frozen
as constants: lane_c `lane_c_1M_s383102`, `lane_c_1p5M_s383202`,
`lane_c_2M_s383302`; lane_b `lane_b_1M_s382102`, `lane_b_1p5M_s382202`,
`lane_b_2M_s382302`. Each block SHALL be decoded with its own source's matrix
at its lane's ordinal (prototypes are source-specific). Preflight SHALL
reconstruct all six deterministically via the accepted constructors and fail
(J3) on any strict-metric mismatch with the committed structural authority,
including Lane C `position_permutations`.

## R6. Posterior-binding preflight

Before any authorized execution, a decoder-free, write-free preflight SHALL
verify, on the FIRST new block of each source (390107/390207/390307), ALL of:
`np.any(bob > 31) == True`; the captured second argument of
`get_conditional_posterior_l2` element-equal to complete `bob`;
`prior_corrected` element-equal to the direct complete-bob call;
`prior_corrected` NOT element-equal to the `u2_bob` prior;
`max(abs(prior_corrected - prior_u2_bob)) > 1e-6`; and at least one position
where the posteriors' `argmax` differs. The preflight SHALL make zero
production decoder calls and write nothing; failure SHALL route to the R11
invalid path; sentinel probes are replaceable only at plan-review stage.

## R7. Decoder contract

All 18 calls SHALL use GF(32) primitive polynomial 37, row-layered FFT-QSPA
via the accepted evaluator, syndrome from true `u2_alice`, complete-Bob
posterior with oracle-L1 conditioning, success = `exact_l2` only, and the
single fixed setting `max_iter=90, damping_alpha=1.0`. No warm start, no
retry, no second setting under any outcome. `wrong_codeword = syndrome_ok and
not exact_l2` SHALL be counted separately and NEVER as exact recovery. Any
deviation is J9.

## R8. Frozen workload and call order

The workload SHALL be exactly C01-C18 (design Section 4): sources in
1M/1p5M/2M order, blocks ascending by seed within a source, lane_c before
lane_b within a block. Any membership or order drift is J12.

## R9. Per-lane retention gates

For each lane independently: G1 overall exact >= 7 out of 9; G2 every source
exact >= 2 out of 3; G3 that lane wrong codewords = 0. A lane passes iff all
three hold. Gates judge ROUTE RETENTION only and SHALL NOT support any B/C
superiority or comparative-ranking statement regardless of outcome.

## R10. Terminal machine

Terminals: `V41_EVIDENCE_INVALID`, `V41_BOTH_LANES_RETAINED`,
`V41_C_ONLY_RETAINED`, `V41_B_ONLY_RETAINED`,
`V41_STOP_BC_PARAMETER_OPTIMIZATION`. With integrity-first precedence and
first-match-wins, the machine SHALL implement design Section 8 rules 0-4
exactly:

```
0. integrity/execution failure anywhere -> V41_EVIDENCE_INVALID
1. pass_lane_c AND pass_lane_b -> V41_BOTH_LANES_RETAINED
2. pass_lane_c only            -> V41_C_ONLY_RETAINED
3. pass_lane_b only            -> V41_B_ONLY_RETAINED
4. both gates failed           -> STOP_BC_PARAMETER_OPTIMIZATION
                                  (reason BOTH_LANES_GATES_FAILED)
```

Wrong-codeword handling is LANE-SPECIFIC ONLY: there is NO global
wrong-codeword termination rule; a wrong codeword on one lane SHALL NOT veto
the other lane's gate outcome and acts exclusively through its own lane's G3
zero-wrong clause (supersedes the round-0 global-literal scope, user-approved
2026-08-26). The mapping SHALL be total and disjoint over all
(lane_c_pass, lane_b_pass) combinations, proven by a mandatory truth-table
test asserting exhaustive mutual exclusion. Terminal determination precedes
per-lane gate-detail display in outputs; the summary SHALL still report each
lane's wrong count separately.

Under EVERY terminal: retention terminals freeze retained lane(s) as fixed
candidates and stop decoder parameter tuning; successor directions (dual
retention -> more-realistic data / non-oracle comparison; STOP ->
protograph/MET) are directional descriptions recorded in the summary ONLY and
authorize nothing. Regardless of outcome: no block addition, no supplementary
or compensating run, and NO second confirmation round.

## R11. Integrity-first invalidation, guard ordering, and evidence tiers

The runner SHALL implement the three-tier evidence boundary of design
Section 10 one-to-one:

- **Tier 0 execution refusal** - refusal-class guards (J1: default deny,
  mandatory flags, exact SHA equality of BOTH `git rev-parse HEAD` AND
  `git rev-parse origin/formal-ir-mainline` with `--authorized-target-sha`,
  scoped tracked-dirty over the four-file scope v41 module + v41 CLI + v38
  module + v35 module; J7: output root already exists) run FIRST, fail
  closed, create NO file and NO root, exit non-zero with ZERO decoder calls.
- **Tier 1 scientific-preflight failure** - preflights (J2 registry, J3
  reconstruction strict match, J4 counts shapes, J5 sentinels) follow,
  decoder-free; on ANY failure the runner SHALL create the formal additive
  root and write the invalid trio - `v41_invalid_notice.json`, empty records,
  `v41_summary.json` with terminal `V41_EVIDENCE_INVALID`, planned = 18
  (fixed), started = 0, completed = 0, no aggregation - and stop with ZERO
  real decoder calls and no rerun.
- **Tier 2 mid-run execution failure** - caught at `BaseException`; raw
  partial records SHALL be retained byte-for-byte inside the pre-created root
  together with a notice + summary carrying started/completed actuals and
  only the failure marker, then the exception re-raised.
- **Normal completion** - the runner SHALL write only the minimal fixed set
  (records json/csv + summary; no NPZ).

Integrity failures J1-J12 (design Section 10) force terminal
`V41_EVIDENCE_INVALID`; performance SHALL NOT be interpreted on invalid
evidence; no performance aggregate, gate evaluation, or terminal
interpretation may be generated from a partial set.

## R12. Budget and stop rules

Total budget SHALL NOT exceed 18 real decoder calls; the 19th call SHALL be
structurally refused (J10). Execution is exactly once, with no rerun, no
resume. The master stop rule SHALL be recorded verbatim in the summary:

> 唯一一次 18-call 全新确认；不再调 decoder 参数；不复用 V40 probe 作为确认样本。无论结果如何：不追加 blocks、不补跑、不做第二轮确认。

## R13. Records and evidence outputs

Every call SHALL produce one record with the schema of design Section 11.
The authorized run SHALL write ONLY, under additive root
`comparison_bench/outputs_comparison/formal_ir_methods/v41_fresh_block_confirm/run_01/`:
`v41_confirm_records.json/.csv`, `v41_summary.json`, and, only on integrity
failure, `v41_invalid_notice.json`. CSV/JSON parity required. Writing any NPZ
SHALL NOT occur; reading any NPZ except read-only V25 counts via the accepted
loader SHALL NOT occur. The output root SHALL be created after all guards and
preflights pass and before the first decoder call, fail-closed on existence
(J7). The summary SHALL contain planned/completed/started actuals, per-lane
aggregates (`exact_total`, per-source counts, wrong counts), BOTH lanes'
gate-evaluation details, routing trace, terminal state + reason, the verbatim
stop rule, claim boundary, statistics note, and provenance SHAs. Existing
results/, V38/V39/V40 outputs SHALL remain byte-identical.

## R14. Lifecycle and authorization

Implementation candidates stop at `IMPLEMENTATION_CANDIDATE /
EXECUTE_NOT_AUTHORIZED`. The single confirmation execution requires an
independent plan ACCEPT plus explicit user `EXECUTE_AUTH` bound to the
repository, branch, full implementation SHA, cycle V41P0, and scope
`v41_confirmation_18_calls_exactly_once`. The CLI SHALL default-deny, require
`--execution-authorized` and `--authorized-target-sha`, verify exact SHA
equality of HEAD AND origin/formal-ir-mainline (ancestor or contains checks
insufficient), and perform the scoped tracked-dirty check. No rerun, tuning,
threshold edit, seed addition, self-acceptance, or automatic successor
authorization is permitted.

## R15. Claim boundary

Results support only bounded route-retention judgments on V25 TRAIN
empirical-count development blocks with oracle-L1 inputs; these are not
real-frame FER evidence, and threshold, SKR, formal-execution, qualification,
or promotion results SHALL NOT be inferred. Forbidden regardless of outcome:
FER, asymptotic threshold, SKR, security, formal qualification, promotion,
real-frame claims, Lane C superiority, Lane B superiority, any B-vs-C
comparative ranking, and any statement that historical gates would now pass.
Success means `exact_l2` only; samples are tiny and clustered (9 unique
blocks x 2 lanes) and clustering is uncorrected.
