# V30 Design — projective-safe finite-graph gate

Status: `FROZEN_P102_ACCEPTED` (main-thread freeze review, 2026-08-20).
No implementation or execution has started.

## 1. Immutable boundary

V29 is closed with `v29_finite_gate_fail` on an authorized 9-block prefix.
Its holdout is not a V30 validation or qualification source. V28R is the
engineering predecessor. V30 keeps `q=32`, `n=1024`, F03 natural
MSB→LSB GF32+GF32, the V26 train-only source/delay posterior, `lambda={2:1}`,
the 64-bit SHA-256 tag, and source leakage budgets. It does not alter the
decoder or fit a new channel from validation data.

The M0 baseline audit is frozen as: 15 L1 support groups; maximum group
multiplicity 69; 303 duplicate projective classes; 922 columns in duplicate
classes; and 1107 guaranteed proportional-column/weight-2 pairs.

## 2. M0 projective-column audit

For a degree-two GF(32) column with nonzero entries at rows `a<b`, compute the
canonical key `(a,b,h_b/h_a)` in the frozen field. Equal keys are proportional
columns; their difference is a weight-2 kernel word. A valid matrix therefore
has no zero column, no zero coefficient, no duplicate key, and at most 31
ratios per support pair.

M0 rebuilds the V28R baseline and persists each column's support,
coefficients, normalized key, duplicate groups, proportional pairs, and the
derived weight-2 lower bound. M0 is read-only and cannot alter the baseline.

## 3. M1 channel-informed allocation screen

The frozen budgets and candidates are:

| source | m_total | shared m1 candidates | m2=m_total-m1 |
|---|---:|---|---|
| 1M | 200 | 9,12,16,24,32,40 | 191,188,184,176,168,160 |
| 1p5M | 206 | 9,12,16,24,32,40 | 197,194,190,182,174,166 |
| 2M | 208 | 9,12,16,24,32,40 | 199,196,192,184,176,168 |

The old V28R `m1=6` is a control only, not a V30 candidate. No candidate is
added after observing results. Existing V26 channel-informed DE is run
separately for L1/L2 with `lambda={2:1}` and frozen sequential conditioning.
Any layer/source/seed failure eliminates that allocation; no tuning or rerun.

Proposed reviewable parameters: screen `n_samples=400`, `max_iter=100`,
`tol=0.01`, `streak=20`, seeds `[30001,30002]`; confirmation
`n_samples=2000`, `max_iter=200`, `tol=0.01`, `streak=20`, seeds
`[30101,30102,30103,30104,30105]`. Every call binds source and delay.

One allocation's screen is exactly 12 calls: 2 seeds × 3 sources × 2 layers.
It is eligible only if all 12 converge with final entropy `<=0.01` bits.
Eligible allocations are ranked by the exact tuple
`(worst_final_entropy, mean_final_entropy, m1)`; the first
`min(2,Neligible)` enter confirmation. Confirmation is exactly 30 calls per
allocation (5 seeds × 3 sources × 2 layers) and requires 30/30 convergence.
If two allocations pass, the same tuple orders them before M2. If none is
eligible, the terminal is `de_allocation_fail` and no M2 construction runs.

M1 has one cumulative 24-hour DE meter. After each call result is persisted,
stage completion or an irreversible failure is evaluated first; only then may
the incomplete stage become `resource_blocked`, and no next call starts.

## 4. M2 deterministic projective-safe families

For at most two DE-passing allocations, construct both fixed families; they
are not random searches and do not use a seed library.

### balanced-projective

Use a deterministic balanced support-pair schedule, lexicographic tie breaks,
balanced check degrees, and projective-key uniqueness. For support rows `a<b`,
freeze the first coefficient to `1` and assign the second coefficient from the
frozen GF(32) nonzero-cycle order, without repeating a ratio for that support.
Fail closed if a support pair would need more than 31 ratios.

### PEG-ACE-projective

Use deterministic progressive edge growth with ACE tie breaking. At each
column choose the lexicographically first candidate minimizing the frozen
PEG/ACE score while satisfying degree balance and projective-key uniqueness.
PEG/ACE chooses the support schedule only; coefficient assignment uses the
same first-coefficient-1 and frozen nonzero-cycle rule. No random tie break,
random permutation, or extra RNG is permitted.

For each selected allocation, the two families collectively produce at most
four matrix packets total (shared L1 plus source-specific L2 bindings are one
matrix packet); this is not four packets per family. If any required matrix is
not full rank, that matrix/allocation-family packet is rejected; it cannot be
regenerated with another seed. Both families build shared L1 and
source-specific L2 matrices. Each matrix
must report degree distributions, GF(32) full row rank, no zero row/column,
unique projective keys, support occupancy, 4-cycle count, girth lower bound,
ACE statistics, syndrome consistency, and deterministic replay. Any structural
failure rejects the matrix before finite decoding.

## 5. M3 validation-only development gate

Only V25 validation frames are allowed: 1M `1200..1599`, 1p5M `1660..2059`,
and 2M `2187..2586`, inclusive; 400 frames/source, 256 pairs/frame, four
frames/block, 100 blocks/source. V29 holdout and raw `.ttbin` are forbidden.
Validation data cannot fit the channel or tune matrices, thresholds, split, or
iterations.

For each of at most four valid matrix packets total, screen the first 20
blocks/source with `max_iter=100`; a matrix is eligible only if every source
has at least 15/20 exact and tag-verified blocks and false accepts are zero.
Rank eligible matrices by
`(-min_source_exact, -total_exact, four_cycle_count, worst_ACE_penalty, m1, family_order)`
where `family_order` is balanced-projective before PEG-ACE-projective. Only
the single top-ranked matrix enters the next fixed 50-block/source
confirmation; it requires at least 45/50 exact and tag-verified per source,
false accepts zero. A failed confirmation is `finite_graph_fail`.

L1→conditional-L2 is Bob-only and uses the actual returned `x1_hat`; L1
failure makes L2 `not_run`. Persist block status, iterations, syndromes, tags,
exact/errors, source/delay identity, and runtime. M3 has one cumulative
24-hour decoder meter. After each block is persisted, stage completion or an
irreversible failure is evaluated before the resource gate; no next block
starts after a terminal decision. All FER is development-stage scoped.

## 6. Evidence, verifier, and terminal

The additive evidence root contains `RUN_MANIFEST.json`,
`projective_column_audit.json`, `de_allocation_screen.json`,
`de_allocation_confirmation.json`, `matrix_audits.json`,
`validation_frame_selection.json`, `validation_block_results.jsonl`,
`validation_summary.json`, `gate.json`, and `readonly_verify.json`.

The verifier rebuilds the field/config, projective keys, rank/topology,
4-cycle/ACE audits, validation frame identity, source/delay binding,
syndromes/tags/leakage/f, exact M1 rank tuples and eligible/selected allocation
IDs, exact M2 family/matrix IDs, M3 matrix rank tuples and selected top-1 ID,
and terminal without rerunning DE or decoder. It
rejects V29 holdout paths, raw `.ttbin`, extra scientific inputs, duplicate
projective keys, and tampered evidence.

`pass_projective_finite_graph_ready_for_fresh` requires every source to meet
45/50 exact and tag-verified, false_accept=0, `f<1.3`, and all structural and
manifest checks. Other terminals are `finite_graph_fail`,
`de_allocation_fail`, `resource_blocked`, and `implementation_blocked`. If M1
has no confirmed allocation, terminal is `de_allocation_fail`; if M2 has no
valid matrix, terminal is `finite_graph_fail`; if M3 screen has no eligible
matrix or its confirmation fails, terminal is `finite_graph_fail`.
Only PASS may propose V31 fresh time-separated qualification; V32 integration
is downstream of V31 PASS.
