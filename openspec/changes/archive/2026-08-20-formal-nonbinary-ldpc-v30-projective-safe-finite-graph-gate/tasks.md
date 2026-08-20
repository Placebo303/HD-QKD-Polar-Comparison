# V30R Tasks — projective-safe finite-graph gate

Status: ARCHIVED — terminal `finite_graph_fail`
P102: accepted by main-thread freeze review on 2026-08-20, then superseded by
this V30R revision before implementation/execution. P103: ACCEPTED on
2026-08-20 by independent freeze review. Implementation and the
pre-registered V30R execution were authorized. The canonical `run_01`
execution and independent read-only verification are now complete; the
scientific terminal is `finite_graph_fail`.

Canonical evidence:
`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v30_20260820/run_01/`.
The verifier returned `ok=true`, `problems=[]`, with no DE or decoder rerun.
M0 reproduced `15/69/303/922/1107`; M1 persisted 72 screen calls and 60
confirmation calls, selecting `m1_9` and `m1_12`, both confirmed 30/30. M2
produced valid balanced packets for `m1=9,12`; both PEG packets were rejected
because no projectively unique ratio survived for support `(0,1)`. M3 screened
both valid packets on the 1M source's blocks `0..5`: each had `6` completed
blocks, `0` exact/tag-verified blocks, `0` false accepts, and an impossible
`15/20` threshold, so the stage stopped before 1p5M/2M and before confirmation.
Meters were 74.828 s (M1) and 719.876 s (M3), below the 24-hour gates.
No qualification, promotion, or fallback rerun is authorized by this result.

## Stable planning IDs

### P001 — predecessor and structural audit input inventory

- [x] Bind V28R canonical config and reproduce the baseline audit values:
  support groups=15, max group=69, duplicate projective classes=303,
  affected columns=922, proportional/weight-2 pairs=1107.
- [x] Bind the exact V25 authority files
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/data_inventory.json`
  and `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/split_manifest.json`.
- [x] Bind the exact source mapping: `type2_1M_20260121_184040` ->
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_1M_20260121_184040/pairs.parquet`,
  `delay_used_ps=-50`, label `1M`, V28R `m2=194`;
  `type2_1p5M_20260121_183806` ->
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_1p5M_20260121_183806/pairs.parquet`,
  `delay_used_ps=+50`, label `1p5M`, `m2=200`; and
  `type2_2M_20260121_183657` ->
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/type2_2M_20260121_183657/pairs.parquet`,
  `delay_used_ps=+50`, label `2M`, `m2=202`.
- [x] Bind V26 canonical
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v26_20260818/run_02/`
  (`RUN_MANIFEST.json`, `m0_report.json`, `readonly_verify.json`) and V28R
  canonical
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v28_gf32_finite_code/run_02_v28r/`
  (`v28_config.json`, `v28_evidence.json`, `RUN_MANIFEST.json`,
  `readonly_verify.json`).
- [x] Bind the V26 channel input exactly to
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz`;
  confirm V26 `run_02/RUN_MANIFEST.json` has
  `counts_basename="channel_counts.npz"`, and use
  `m0_report.json.detail["A02:<source_id>"].adapter_H.L1/L2` as the F03
  source-specific float64 entropy authority.
- [x] Bind `GF2mField.create(32)`, primitive polynomial `0b100101`, field_id
  `c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf`, and
  zero-based `ratio_index` into `nonzero_cycle`.
- [x] Bind V25 validation-only paths and prove V29 holdout is excluded.

### P002 — architecture and candidate freeze

- [x] Freeze q/n/F03, `lambda={2:1}`, tag, leakage, and source budgets.
- [x] Freeze shared candidates `{9,12,16,24,32,40}` and exclude baseline 6
  from candidate ranking.
- [x] Freeze balanced-projective and PEG-projective-cycle-cancelled families, with no
  random/seed-library search; for each allocation they produce at most two
  matrix packets total. Use only the exact support/label tuples frozen in
  design §4; no alternate or informal ranking is allowed. For every support
  pair `a<b`, assign the first coefficient as 1 and the second from the frozen
  GF(32) `nonzero_cycle` in order, never repeating a projective ratio within
  that support group. Standard variable-side ACE is not a discriminator for
  `d_v=2`. Duplicate projective keys/4-cycle FRC failures must be zero. Tanner-8
  is topology-only. A rank or projective failure rejects that matrix packet and
  may not trigger seed or label replacement.
- [x] Freeze the per-source/layer DE accounting in design §1.2:
  `R_i=1-m_i/n`, `leak_i=5*m_i` bits, `f_i=leak_i/(n*H_i)` with H from the
  bound V26 canonical M0 A02 `adapter_H`; exclude the 64-bit tag from single-
  layer DE. Freeze `leak_total=5*m_total+64` and
  `f_total=leak_total/(n*(H_L1+H_L2))`, direct float64 and no extra rounding.
- [x] Freeze balanced support selection as columns `j=0..n-1`, lexicographic
  `(a,b)` candidates, exact score
  `(occupancy_after,max_check_degree_after,sumsq_after,a,b)`; freeze PEG as
  the same column/candidate order with prior-support check-multigraph edge
  distance `d_check(a,b)`, define `d(a,b)=2*d_check(a,b)` as Tanner path
  length, use local Tanner score `d+2`, and exact tuple
  `(component_flag,distance_cost,max_check_degree_after,sumsq_after,a,b)`.
  Projective uniqueness is label-stage-only and standard ACE is removed.
- [x] Freeze newly-closed Tanner-6 as cycles containing only current column,
  counted once by canonical orientation
  `min((j,a,k1,c,k2,b),(j,b,k2,c,k1,a))`; use the explicit FRC alternating
  product and independent empty support/multigraph/ratio state for shared L1
  and each source-specific L2.

### P102 — superseded V30 freeze review

- [x] Review the original V30 proposal/design/spec/tasks and ambiguity audit.
- [x] Record the original P102 ACCEPT before V30 implementation or execution.
- [x] Mark P102 superseded by V30R; it cannot authorize a V30R run.

### P103 — V30R main-thread freeze review (ACCEPTED 2026-08-20)

- [x] Review the V30R proposal/design/spec/tasks, packet cap, unique ambiguity
  IDs, bounded 4-cycle/Tanner-6 label rule, V25 channel-count binding, DE and
  total leakage formulas, and design §4/§5 tuple references.
- [x] Record explicit P103 ACCEPT before implementation or execution.
- At the time of the P103 ACCEPT review on 2026-08-20, implementation and
  pre-registered V30R execution were only authorized; that review record did
  not claim that either had occurred. Subsequently, canonical `run_01`
  completed with independent read-only verification and was archived with
  terminal `finite_graph_fail`. Fresh qualification/promotion remains out of
  scope.

## Milestones

- [x] M0/I01–I04: reproduce projective audit and persist column-level evidence.
- [x] M1/I05–I09: run exactly 72 screen calls (each allocation has 12 calls;
  2 seeds × 3 sources × 2 layers), even if an earlier call fails. Only a global
  terminal may interrupt those registered calls. An allocation is eligible
  only when all 12 calls converge with final entropy `<=0.01`; rank eligible
  allocations by `(worst_final_entropy, mean_final_entropy, m1 ascending)` and
  select the first `min(2,Neligible)` before confirmation. Each selected
  allocation runs its complete 30 calls (5 seeds × 3 sources × 2 layers), so
  confirmation is at most 60 calls; a failed allocation is removed only after
  its 30 calls and does not cancel the other selected allocation. Confirmation
  requires 30/30 convergence for at least one allocation. If none is
  confirmed, terminal is `de_allocation_fail`.
- [x] M2/I10–I17: for each selected allocation build at most two deterministic
  matrix packets total (one balanced-projective and one
  PEG-projective-cycle-cancelled), apply projective-safe coefficient assignment
  plus bounded Tanner-6 cancellation, and reject rank/projective/4-cycle-FRC
  failures without changing seed or label order. Tanner-8 is topology-only.
  M2 is outside both runtime meters; an implementation timeout is
  `implementation_blocked`.
- [x] M3/I18–I25: for the global set of at most four valid matrix packets run a
  fixed block `0..19`/source validation screen. A matrix is eligible only if every
  source has at least 15/20 exact and tag-verified blocks with zero false
  accepts. Use the exact ranking tuple frozen in design §5,
  `(-min_source_exact, -total_exact, four_cycle_count, m1 ascending,
  family_order)`, where `four_cycle_count` is shared-L1 plus all three
  source-specific-L2 counts and all four components are persisted. Only the
  single top-ranked eligible matrix
  uses fixed blocks `20..69`/source for confirmation. A screen-stage matrix
  failure removes only that matrix; a top-ranked confirmation failure is global
  `finite_graph_fail` and cannot trigger fallback. Require at least 45/50 exact
  and tag-verified blocks per source. Use Bob-only sequential decoding, tag,
  resource, and matrix-local screen/global confirmation gates.
- [x] M4/I26–I29: independent verifier, terminal classification, and closeout.

### V30R execution result (canonical `run_01`)

- M0 PASS: baseline values `support_groups=15`, `max_group=69`,
  `duplicate_projective_classes=303`, `affected_columns=922`, and
  `proportional_weight2_pairs=1107` reproduced.
- M1 PASS: all 72 pre-registered screen calls and both selected allocations'
  complete 30-call confirmations were persisted. Eligible screen allocations
  were `m1=9,12,16`; selected and confirmed allocations were `m1_9,m1_12`,
  each 30/30. No unregistered call or rerun occurred.
- M2 PARTIAL/VALIDATED: balanced-projective packets for `m1=9,12` passed rank
  and projective-safety audits. PEG packets for both allocations were rejected
  deterministically because support `(0,1)` had no projectively unique ratio.
  The rejection is retained; no replacement packet was generated.
- M3 TERMINAL FAIL: both valid balanced packets entered screen blocks `0..19`
  and were impossible after 6 blocks on source `1M` (`0` exact, `0` tag,
  `0` false accepts), so no other source and no confirmation window ran.
- M4 PASS: `readonly_verify.json` reports `ok=true`, `problems=[]`,
  `recomputed_terminal=finite_graph_fail`, `screen_call_count=72`,
  `confirmation_call_count=60`, `packet_count=2`, and `no_de_rerun=true`,
  `no_decoder_rerun=true`.

The final V30R terminal is `finite_graph_fail`. This closes the tested
`n=1024`, F03, fixed-allocation, balanced/PEG-family finite conversion; it
does not close the V25 empirical channel, V26 channel-informed DE, or all
nonbinary-LDPC designs.

## Acceptance IDs

- **A01** M0 exact baseline counts reproduce.
- **A02** Every candidate allocation has exact source m_total/m1/m2/leak/f.
- **A03** Every DE call records source/delay, seed, layer, iterations, entropy,
  and terminal; all 72 screen calls, the 12-call eligibility sets, rank tuple,
  selected allocation IDs, at most 60 confirmation calls, and no unregistered
  call are replayable.
- **A04** Both matrix families are deterministic and projective-safe, use the
  frozen coefficient-ratio rule, produce at most two packets per selected
  allocation and at most four packets globally, and use no additional RNG.
- **A05** No matrix has zero/proportional columns or duplicate projective keys;
  all required ranks pass and the 4-cycle FRC hard gate is zero. Tanner-6
  degeneracy may be nonzero but is counted; Tanner-8 is topology-only.
- **A06** Validation selection has exactly 100 blocks/source and no V29 frame.
- **A07** Bob-only L1→L2 order and returned-x1 conditioning are proven.
- **A08** Screen/confirmation counts, eligible sets, exact rank tuples,
  selected allocation/matrix IDs, exact/tag thresholds, false accepts,
  fixed `0..19`/`20..69` block windows, separate M1-DE and M3-decoder resource
  gates, screen-stage matrix-local failure handling, top-ranked confirmation
  terminal, and global early-stop proof are
  replayable.
- **A09** Read-only verifier returns `ok=true` without DE/decoder rerun.
- **A10** Every degree-two label assignment fixes the first coefficient to `1`,
  rejects duplicate projective keys before scoring, computes exact newly closed
  Tanner-6 degeneracy, and selects the lexicographically minimal
  `(degenerate_6_new, ratio_index)` from zero-based `nonzero_cycle` order.
- **A11** Tanner-8 is used only for aggregate topology/girth diagnostics; no
  8-cycle label-FRC elimination or per-cycle catalog is required.
- **A12** `matrix_audits.json` persists only aggregate projective/4-cycle,
  Tanner-6 score, Tanner-8 topology, rank, support, and deterministic per-column
  label-replay fields; it does not persist a cycle/candidate rejection list.
- **A13** The independent verifier recomputes the 4-cycle hard gate and
  per-column Tanner-6 candidate scores from the frozen graph and confirms the
  aggregate evidence without DE/decoder rerun.
- **A14** Before the P103 review, the draft state was persisted as
  `DRAFT_PENDING_P103_FREEZE_REVIEW` and did not authorize execution. After
  P103 ACCEPT on 2026-08-20, implementation and the pre-registered execution
  completed once; canonical `run_01` and independent read-only verification
  close the change with terminal `finite_graph_fail`.
- **A15** V25 inventory/split, V26 canonical, and V28R canonical paths are
  persisted exactly, with all three source IDs, labels, pair paths, and
  `delay_used_ps` mappings reproduced without raw `.ttbin`.
- **A16** Balanced support selection replays columns in order with lexicographic
  supports and exact score
  `(occupancy_after,max_check_degree_after,sumsq_after,a,b)`.
- **A17** PEG support selection replays the prior-support check-multigraph
  shortest edge distance `d_check`, exact `d=2*d_check` and `d+2` local Tanner
  score, and frozen support tuple;
  projective uniqueness is absent from support selection and ACE is absent.
- **A18** Newly closed Tanner-6 evidence contains the current column only,
  counts each undirected cycle once by the canonical tuple, uses the frozen
  alternating-product inequality/equality test with reversal equivalence, and
  resets state for L1 and every L2 source.
- **A19** M1 persists exactly 72 screen calls and at most 60 confirmation calls;
  each selected allocation completes 30 calls, failures remove only that
  allocation, and all-confirmation failure is `de_allocation_fail`.
- **A20** Field evidence explicitly binds `GF2mField.create(32)`, polynomial
  `0b100101`, the V28R field_id, and zero-based selected `ratio_index`.
- **A21** Before P103, all entry documents stated V30R
  `DRAFT_PENDING_P103_FREEZE_REVIEW`, marked V30 P102 superseded, and did not
  authorize implementation or execution. After P103 ACCEPT on 2026-08-20,
  implementation and pre-registered execution completed once; current entry
  documents record the archived `finite_graph_fail` terminal and preserve the
  no-qualification/no-promotion boundary.
- **A22** The V25 `channel_counts.npz` path and V26 canonical basename link are
  exact, and F03 H values are read from
  `m0_report.detail["A02:<source_id>"].adapter_H.L1/L2`.
- **A23** Every M1 layer/source call uses `R_i=1-m_i/n`,
  `leak_i=5*m_i` bits, and `f_i=leak_i/(n*H_i)` from the bound float64 H;
  the 64-bit tag is absent from single-layer DE.
- **A24** Total finite accounting uses exactly
  `leak_total=5*m_total+64` and
  `f_total=leak_total/(n*(H_L1+H_L2))`, with direct float64 arithmetic and no
  extra rounding or gate decisions from display values.
- **A25** M3 `four_cycle_count` equals shared-L1 ordinary 4-cycle count plus
  each of the three source-specific-L2 counts; all four components and the
  total are persisted and the exact ranking tuple is the design §5 tuple.
- **A26** Tanner-6 candidates require `c notin {a,b}`, `k1 != k2`, and prior
  supports exactly `{a,c}` and `{c,b}`; only simple current-column cycles are
  counted once.
- **A27** Proposal/tasks/spec summaries reference the exact support/ranking
  tuples frozen in design §4/§5 and contain no alternate informal ordering.

## Evidence IDs

- **E01** `RUN_MANIFEST.json` with frozen config, source boundary, families,
  allocations, and terminal.
- **E02** `projective_column_audit.json` with baseline and candidate audits.
- **E03** `de_allocation_screen.json` with all 72 screen calls, 12-call
  eligibility sets, rank tuples, and selected allocation IDs; **E04** with each
  selected allocation's complete 30-call outcomes (at most 60) and final
  selection order.
- **E05** `matrix_audits.json` with family/matrix IDs, frozen coefficient
  ratios, rank/projective/ordinary-4-cycle metrics, aggregate Tanner-6
  cancellation scores, aggregate Tanner-8 topology/girth metrics, and the
  shared-L1/three-L2 `four_cycle_count` components plus total used by ranking;
  rejected rank/projective/4-cycle-FRC packets.
- **E06** validation frame/block manifests and per-block JSONL.
- **E07** source/global summary with stage-scoped FER.
- **E08** `gate.json` with exact selection records, separate M1/M3 resource
  meters, precedence, and early-fail proof.
- **E09** `readonly_verify.json` with no rerun flags, recomputed selection
  tuples/IDs, and recomputed terminal.

## Forbidden actions

- no V29 holdout, raw `.ttbin`, fresh qualification, promotion, or public
  residual;
- no random degree/matrix search, repository/library search, tuning, retry,
  or post-failure candidate insertion;
- no MET/joint protograph/cross-layer fallback within V30R;
- no V31/V32 work before V30R PASS and a separate review.

## Ambiguity audit (resolved for P103; historical draft state retained)

| # | Question | Frozen answer |
|---:|---|---|
| 1 | What is the field? | GF(32), same V26/V28R field and arithmetic tables. |
| 2 | What is a projective key? | Sorted support pair plus `h_b/h_a`. |
| 3 | What proves weight 2? | Duplicate normalized key gives proportional columns. |
| 4 | Is V28R m1=6 eligible? | No; control only. |
| 5 | Which allocations? | Exactly 9,12,16,24,32,40. |
| 6 | Which m2? | Source m_total minus shared m1. |
| 7 | Which graph families? | Exactly balanced-projective and PEG-projective-cycle-cancelled. |
| 8 | Are ties random? | No; lexicographic deterministic ties. |
| 9 | Which channel? | V26 train-only source/delay-conditioned posterior. |
| 10 | Which data? | Validation ranges only; V29 holdout excluded. |
| 11 | What is M1 DE screen eligibility/ranking? | Exactly 72 screen calls total, 12 per allocation (2 seeds × 3 sources × 2 layers); all calls for a failed allocation are persisted. Eligibility requires final entropy `<=0.01` for all 12; rank by `(worst_final_entropy, mean_final_entropy, m1 ascending)` and select at most the first two before confirmation. |
| 12 | What is M1 confirmation? | Each selected allocation completes exactly 30 calls (5 seeds × 3 sources × 2 layers), so at most 60 calls; failure removes only that allocation. At least one 30/30 allocation is required; all selected failures give `de_allocation_fail`. |
| 13 | What is the projective ratio rule? | For support `a<b`, first coefficient is 1 and the second follows zero-based `ratio_index` in the frozen GF(32) `nonzero_cycle`; reject duplicate projective keys before Tanner-6 scoring; PEG chooses supports only and rank failure rejects without reseeding. |
| 14 | What is the bounded cycle-cancellation rule? | Duplicate projective keys/4-cycle FRC failures must be zero. For each remaining label candidate, count only newly closed Tanner-6 cycles containing the current column, canonicalize each undirected cycle once, and choose `(degenerate_6_new, ratio_index)` minimally; nonzero counts are allowed and aggregated. Tanner-8 is topology-only. |
| 15 | What is the packet cap? | Each selected allocation has at most one packet per family, hence at most two; at most two selected allocations yield at most four packets globally. M3 tests that global set. |
| 16 | What is the M3 screen/selection? | Test the global set of at most four matrix packets on fixed blocks `0..19`; eligible means every source is >=15/20 exact and tag-verified with false accepts zero. Rank by `(-min_source_exact,-total_exact,four_cycle_count,m1,family_order)` with balanced before PEG-projective-cycle-cancelled; standard variable-side ACE is absent because `d_v=2`. |
| 17 | What is M3 confirmation? | After the complete screen, only the single top-ranked eligible matrix runs fixed blocks `20..69` and must reach >=45/50 exact and tag-verified per source with false accepts zero. Its failure is global `finite_graph_fail`; no fallback matrix runs. |
| 18 | How are resources and terminal precedence applied? | M1 DE and M3 decoder each have an independent cumulative 24h meter; persist the current call/block, then apply matrix-local or stage-global decision, then resource blocking, and never start an unregistered call/block. M1 still completes all 12 calls for a failed allocation unless a global terminal occurs. M2 has no scientific meter; implementation timeout is `implementation_blocked`. |
| 19 | What is false accept? | Tag pass with offline nonexact; must be zero. |
| 20 | What is early stop? | Persist the current record, decide an impossible threshold or other irreversible failure, then apply the resource gate; never start the next call/block. |
| 21 | What does PASS authorize? | Only a V31 fresh qualification proposal. |
| 22 | What exact predecessor inputs are bound? | V25 `run_04/data_inventory.json` and `split_manifest.json`, V26 canonical `run_02` manifest/M0/verify, and V28R canonical `run_02_v28r` config/evidence/manifest/verify; the three source IDs, pair paths, labels, and `delay_used_ps=-50/+50/+50` are fixed. |
| 23 | What is balanced support selection? | For `j=0..n-1`, lexicographic `(a,b)` candidates minimize `(occupancy_after,max_check_degree_after,sumsq_after,a,b)`; labels are assigned only after support selection. |
| 24 | What is PEG support selection? | Prior supports form an undirected check multigraph; `d_check(a,b)` is its shortest-path edge distance, `d(a,b)=2*d_check(a,b)` is the Tanner path length, local Tanner score is `d+2`, and the exact tuple `(component_flag,distance_cost,max_check_degree_after,sumsq_after,a,b)` is minimized. Projective uniqueness is label-stage-only. |
| 25 | What is the Tanner-6 counting scope? | Only cycles containing current column `j`; canonical tuple is `min((j,a,k1,c,k2,b),(j,b,k2,c,k1,a))`, counted once. Reversal changes `Pi` to `Pi^-1` and leaves the `Pi=1` degeneracy test unchanged. |
| 26 | Are graph states shared? | No. Shared L1 and every source-specific L2 start independent empty support, multigraph, and ratio state; no source or layer state crosses. |
| 27 | What field metadata is persisted? | `GF2mField.create(32)`, primitive polynomial `0b100101`, V28R field_id `c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf`, and zero-based selected `ratio_index`. |
| 28 | What are the entry-document states? | Before P103, the four docs and all current/hand-off/memory entry files used `DRAFT_PENDING_P103_FREEZE_REVIEW`, marked V30 P102 superseded, and prohibited implementation/execution. At the time of the P103 ACCEPT review on 2026-08-20, the state became `FROZEN_P103_ACCEPTED` and implementation/execution were only authorized; the review record did not claim execution. Subsequently, canonical `run_01` completed and the entry state is archived `finite_graph_fail`. |
| 29 | What is the M1 channel-count input and V26 link? | Bind V25 `run_04/channel_counts.npz`; V26 canonical `run_02/RUN_MANIFEST.json` records `counts_basename="channel_counts.npz"`; resolve only to the exact V25 path. |
| 30 | Which H values and equations govern DE? | Use `m0_report.detail["A02:<source_id>"].adapter_H.L1/L2` float64 values; `R_i=1-m_i/n`, `leak_i=5*m_i`, `f_i=leak_i/(n*H_i)`; exclude tag from single-layer DE. |
| 31 | What is total leakage/f? | `leak_total=5*m_total+64`, `f_total=leak_total/(n*(H_L1+H_L2))`; direct float64, no extra rounding, display values are not gate inputs. |
| 32 | What is M3 four-cycle ranking count? | `four_cycle_count=four_cycle_count_L1+sum_s four_cycle_count_L2[s]`; persist shared-L1, each three L2 components, and total; use only the design §5 tuple. |
| 33 | What makes a Tanner-6 candidate simple? | Require `c notin {a,b}`, `k1 != k2`, and prior supports exactly `{a,c}` and `{c,b}`; count only cycles containing current `j`, once by canonical tuple. |
| 34 | Which ranking wording is authoritative? | Proposal/tasks/spec refer to design §4/§5 exact tuples and do not introduce another informal support or matrix ordering. |

## Stop condition

Any unresolved freeze ambiguity, failed M0 structural reproduction, all-DE-
allocation failure, matrix projective/4-cycle-FRC failure, validation failure, verifier
failure, resource limit, or implementation error stops the change and preserves
the evidence. A V30R failure does not authorize random search; only an
explicitly approved successor may consider cross-layer checks or joint
protographs.
