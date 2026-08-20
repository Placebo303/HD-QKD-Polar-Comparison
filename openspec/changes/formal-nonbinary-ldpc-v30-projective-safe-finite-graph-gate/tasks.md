# V30 Tasks — projective-safe finite-graph gate

Status: `FROZEN_P102_ACCEPTED`  
P102: accepted by main-thread freeze review on 2026-08-20. This acceptance
freezes the packet; implementation/execution has not started.

## Stable planning IDs

### P001 — predecessor and structural audit input inventory

- [ ] Bind V28R canonical config and reproduce the baseline audit values:
  support groups=15, max group=69, duplicate projective classes=303,
  affected columns=922, proportional/weight-2 pairs=1107.
- [ ] Bind V26 train-only channel counts and source/delay metadata.
- [ ] Bind V25 validation-only paths and prove V29 holdout is excluded.

### P002 — architecture and candidate freeze

- [ ] Freeze q/n/F03, `lambda={2:1}`, tag, leakage, and source budgets.
- [ ] Freeze shared candidates `{9,12,16,24,32,40}` and exclude baseline 6
  from candidate ranking.
- [ ] Freeze balanced-projective and PEG-ACE-projective families, with no
  random/seed-library search; for each allocation they produce at most four
  matrix packets total.  For every support pair `a<b`, assign the first
  coefficient as 1 and the second from the frozen GF(32) `nonzero_cycle` in
  order, never repeating a projective ratio within that support group.  PEG
  and ACE may choose only the support schedule; they do not introduce an
  additional RNG or tie-breaking seed.  A rank failure rejects that matrix
  packet and may not trigger seed replacement.

### P102 — main-thread freeze review

- [x] Review proposal/design/spec/tasks and the ambiguity audit.
- [x] Record explicit P102 ACCEPT before implementation or execution.

## Milestones

- [ ] M0/I01–I04: reproduce projective audit and persist column-level evidence.
- [ ] M1/I05–I09: for each allocation run exactly 12 screen calls (2 seeds ×
  3 sources × 2 layers).  An allocation is eligible only when all 12 calls
  converge with final entropy `<=0.01`; rank eligible allocations by
  `(worst_final_entropy, mean_final_entropy, m1 ascending)` and confirm the
  first `min(2,Neligible)` with exactly 30 calls each (5 seeds × 3 sources ×
  2 layers).  Confirmation requires 30/30 convergence; order any two passing
  allocations by the same tuple before M2.  If none is confirmed, terminal is
  `de_allocation_fail`.
- [ ] M2/I10–I15: for each selected allocation build at most four deterministic
  matrix packets (the two frozen families), apply the frozen projective-ratio
  assignment and reject rank failures without changing seed; audit projective
  keys, rank, degree balance, girth/4-cycle, and ACE constraints.  M2 is outside
  both runtime meters; an implementation timeout is `implementation_blocked`.
- [ ] M3/I16–I23: for at most four valid matrix packets per allocation run a
  20-block/source validation screen.  A matrix is eligible only if every
  source has at least 15/20 exact and tag-verified blocks with zero false
  accepts.  Rank by `(-min_source_exact, -total_exact, four_cycle_count,
  worst_ACE_penalty, m1 ascending, family_order)` with balanced before PEG;
  only the top-ranked matrix proceeds to 50 blocks/source confirmation, which
  requires at least 45/50 exact and tag-verified blocks per source.  Use
  Bob-only sequential decoding, tag, resource, and irreversible-fail gates.
- [ ] M4/I24–I27: independent verifier, terminal classification, and closeout.

## Acceptance IDs

- **A01** M0 exact baseline counts reproduce.
- **A02** Every candidate allocation has exact source m_total/m1/m2/leak/f.
- **A03** Every DE call records source/delay, seed, layer, iterations, entropy,
  and terminal; the 12-call eligibility set, rank tuple, selected allocation
  IDs, 30-call confirmation set, and no unregistered call are replayable.
- **A04** Both matrix families are deterministic and projective-safe, use the
  frozen coefficient-ratio rule, produce no more than four matrix packets per
  allocation, and use no additional RNG.
- **A05** No matrix has zero/proportional columns; all required ranks pass.
- **A06** Validation selection has exactly 100 blocks/source and no V29 frame.
- **A07** Bob-only L1→L2 order and returned-x1 conditioning are proven.
- **A08** Screen/confirmation counts, eligible sets, exact rank tuples,
  selected allocation/matrix IDs, exact/tag thresholds, false accepts,
  separate M1-DE and M3-decoder resource gates, and early-stop proof are
  replayable.
- **A09** Read-only verifier returns `ok=true` without DE/decoder rerun.

## Evidence IDs

- **E01** `RUN_MANIFEST.json` with frozen config, source boundary, families,
  allocations, and terminal.
- **E02** `projective_column_audit.json` with baseline and candidate audits.
- **E03** `de_allocation_screen.json` with all 12-call eligibility sets, rank
  tuples, and selected allocation IDs; **E04** confirmation calls with all
  30-call outcomes and final selection order.
- **E05** `matrix_audits.json` with family/matrix IDs, frozen coefficient
  ratios, rank/projective/girth/ACE/4-cycle metrics, and rejected rank-failure
  packets.
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
- no MET/joint protograph/cross-layer fallback within V30;
- no V31/V32 work before V30 PASS and a separate review.

## Ambiguity audit (must be resolved before P102)

| # | Question | Frozen draft answer |
|---:|---|---|
| 1 | What is the field? | GF(32), same V26/V28R field and arithmetic tables. |
| 2 | What is a projective key? | Sorted support pair plus `h_b/h_a`. |
| 3 | What proves weight 2? | Duplicate normalized key gives proportional columns. |
| 4 | Is V28R m1=6 eligible? | No; control only. |
| 5 | Which allocations? | Exactly 9,12,16,24,32,40. |
| 6 | Which m2? | Source m_total minus shared m1. |
| 7 | Which graph families? | Exactly balanced-projective and PEG-ACE-projective. |
| 8 | Are ties random? | No; lexicographic deterministic ties. |
| 9 | Which channel? | V26 train-only source/delay-conditioned posterior. |
| 10 | Which data? | Validation ranges only; V29 holdout excluded. |
| 11 | What is M1 DE screen eligibility/ranking? | Exactly 12 calls per allocation (2 seeds × 3 sources × 2 layers); all must converge at final entropy `<=0.01`. Rank by `(worst_final_entropy, mean_final_entropy, m1 ascending)` and confirm at most the first two. |
| 12 | What is M1 confirmation? | Exactly 30 calls per selected allocation (5 seeds × 3 sources × 2 layers); 30/30 must converge, with the same tuple ordering before M2. |
| 13 | What is the projective ratio rule? | For support `a<b`, first coefficient is 1 and the second follows frozen GF(32) `nonzero_cycle` order without duplicate ratios; PEG/ACE chooses supports only and rank failure rejects without reseeding. |
| 14 | What is the M3 screen/selection? | Test at most four matrix packets; eligible means every source is >=15/20 exact and tag-verified with false accepts zero. Rank by `(-min_source_exact,-total_exact,four_cycle_count,worst_ACE_penalty,m1,family_order)` and pass only top-1 onward. |
| 15 | What is M3 confirmation? | The selected top-1 matrix runs the next 50 blocks/source and must reach >=45/50 exact and tag-verified per source with false accepts zero. |
| 16 | How are resources and terminal precedence applied? | M1 DE and M3 decoder each have an independent cumulative 24h meter; persist the current call/block, then stage completion or irreversible failure, then resource blocking, and never start the next call/block. M2 has no scientific meter; implementation timeout is `implementation_blocked`. |
| 17 | What is false accept? | Tag pass with offline nonexact; must be zero. |
| 18 | What is early stop? | Persist record, then impossible threshold, then resource. |
| 19 | What does PASS authorize? | Only a V31 fresh qualification proposal. |
| 13 | What is false accept? | Tag pass with offline nonexact; must be zero. |
| 14 | What is early stop? | Persist record, then impossible threshold, then resource. |
| 15 | What does PASS authorize? | Only a V31 fresh qualification proposal. |

## Stop condition

Any unresolved freeze ambiguity, failed M0 structural reproduction, all-DE-
allocation failure, matrix projective failure, validation failure, verifier
failure, resource limit, or implementation error stops the change and preserves
the evidence. A V30 failure does not authorize random search; only an explicitly
approved successor may consider cross-layer checks or joint protographs.
