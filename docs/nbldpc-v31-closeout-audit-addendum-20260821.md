# NBLDPC V31 Closeout Audit Addendum — 2026-08-21

Date: 2026-08-21
Canonical correction evidence: `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_02/` (authoritative, additive)
Superseded candidate: `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_01/` (preserved, superseded)
Prior report (preserved, not overwritten): `docs/nbldpc-v31-deterministic-finite-graph-redesign-report-20260820.md`
Terminal: `finite_graph_fail` (ARCHIVED_PARTIAL)

## 1 Correction purpose

This addendum is an additive correction to the V31 deterministic finite-graph redesign gate record. It does not delete or rewrite history. The prior report `docs/nbldpc-v31-deterministic-finite-graph-redesign-report-20260820.md` remains byte-preserved; the original execution evidence `run_01` remains preserved on disk; only the closeout interpretation and lifecycle state are corrected by additive evidence. The authoritative correction evidence is additive `run_02`; `run_01` is preserved but superseded. This document must be read together with the preserved prior report, with `run_02` as the authoritative source for V31 closeout claims and `run_01` as the superseded candidate.

## 2 Correct lifecycle

The correct lifecycle for V31 after the independent audit is **ARCHIVED_PARTIAL**, not a fully executed dual-n pass. The audit established the following facts, which this additive correction records verbatim:

```
V31: ARCHIVED_PARTIAL
n=1024: 300/300, finite_graph_fail
n=2048: 14 blocks from 1M only
original both-n execution: incomplete
global PASS under original contract: impossible
bounded-prefix contingency: post hoc
```

Interpretation: n=1024 completed its full 300-block window (100 blocks per source: 1M/1p5M/2M) and deterministically reached `finite_graph_fail`; n=2048 executed only 14 blocks from 1M (1p5M/2M not executed); the original both-n execution is therefore incomplete; a global PASS under the original both-n contract was impossible once the complete n=1024 failure was observed; the bounded 1M prefix evaluated at n=2048 was not a pre-registered contingency but a post-hoc closeout contingency added at audit closeout to document the consistent failure mode. The authoritative evidence for this lifecycle is additive `run_02`; `run_01` is preserved but superseded because it did not distinguish the pre-registered versus post-hoc status with the same lifecycle clarity.

## 3 What remains scientifically valid

The n=1024 QC finite-graph negative remains scientifically valid and is the bound of this correction. Exact/tag verification on n=1024 is 0/300 (0/100 per source: 1M, 1p5M, 2M), syndrome convergence is 0.00, L2 shows progress without convergence (`converged_no_syndrome` on all 300 blocks, with 3-5 L1 iterations before L2 stalls), and no false accepts. This is a valid bounded negative for the tested deterministic `QC-cyclic-projective` construction at fixed `m1=16` on the V25 source/delay-conditioned empirical channel, not a claim that the entire GF32+GF32 / V25 / V26 route has failed. V25 `pass_ready_for_de_change`, V26 `pass_target_f13` (channel-informed DE), and V27 `pass_finite_budget_ready` (finite-leakage-margin) remain valid within their own scopes; the V28/V31 finite graph/decoder conversion layer is the isolated failing layer. The n=2048 14-block 1M prefix is consistent with the same L2 `converged_no_syndrome` mode but is not an independent complete-n result. Authoritative confirmation is additive `run_02`; `run_01` is preserved but superseded.

## 4 What is corrected

The following four rows correct the closeout wording without altering the persisted 300-block scientific fact. Each row is evaluated against additive `run_02` (authoritative) versus `run_01` (superseded).

| # | Before (prior report / run_01 closeout wording) | After (this addendum / run_02 authoritative) |
|---|-----------------------------------------------|----------------------------------------------|
| 1 | fully executed | partially executed |
| 2 | pre-registered bounded contingency | post-hoc closeout contingency |
| 3 | complete finite-graph gate | n=1024 complete plus n=2048 prefix |
| 4 | verifier proves all evidence | verifier proves persisted evidence with PEG replay limitation |

Row 1: V31 is partially executed (n=1024 complete, n=2048 incomplete), not fully executed across both n. Row 2: the 1M 14-block bounded prefix is a post-hoc closeout contingency, not a pre-registered design contingency. Row 3: the finite-graph gate is `n=1024 complete plus n=2048 prefix`, not a complete both-n gate. Row 4: the read-only verifier proves persisted evidence with the PEG replay limitation, not an unbounded proof of all conceivable evidence. Authoritative is additive `run_02`; `run_01` is preserved but superseded.

## 5 Verifier v2 evidence

The independent read-only verifier v2 was executed against the additive `run_02` (authoritative; `run_01` is preserved but superseded). It recomputes without rerunning DE or the decoder.

- **Block coverage (additive run_02, authoritative)**: n=1024 300/300 (100 per source: 1M, 1p5M, 2M) complete; n=2048 14 blocks from 1M only (1p5M/2M not run, 36/50 remaining per original contract not executed). Superseded `run_01` reported the same coverage but without the post-hoc contingency label.
- **Exact / tag / false-accept (run_02)**: exact 0/300, tag 0/300, false_accept 0/300; per-source exact 0/100 and tag 0/100 at n=1024 (1M/1p5M/2M) and 0/14 at n=2048 1M prefix; zero `exact_mismatch` / `tag_false_accept`. Superseded `run_01` values are identical but superseded on interpretation.
- **Syndrome (run_02)**: syndrome convergence 0.00; all 300 n=1024 blocks and all 14 n=2048 prefix blocks end `converged_no_syndrome` on L2 (L1 converges in 3-5 iterations); `l1_ok` 98/99/99 at n=1024, `l2_ok` 0 everywhere. Same raw counts in `run_01`, now superseded by `run_02` as authoritative.
- **Runtime (run_02)**: wall EXECUTION_WALLCLOCK_S 13015 s (additive `run_02` authoritative). `run_01` runtime is preserved but superseded for closeout reference.
- **QC matrix (run_02)**: `QC-cyclic-projective` family full-rank on both n (GF(32) rank == m), `zero duplicate/proportional keys`, `occupancy 9/18` (n=1024 occupancy 9, n=2048 occupancy 18, both ≤31), projective-safe. `PEG-capacity-aware` family hard-rejected (rank-deficient 199/200 and 413/414). Same audit result in `run_01`, now superseded by `run_02` attestation.
- **Input / code binding (run_02)**: field `GF2mField.create(32)` poly `0b100101`, field_id `c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf`, channel `F03 natural MSB→LSB GF32+GF32` from V25 `data_inventory.json`/`split_manifest.json`, `m1=16`, `m_total` n=1024 {200,206,208} / n=2048 {413,426,430}, `HEAD c8d2acab`. Binding identical in `run_01` but authoritative in `run_02`.
- **PEG limitation exact text (persisted evidence)**: the verifier proves persisted evidence with PEG replay limitation — the PEG matrices are rank-deficient at these sizes and their construction is hard-rejected; no PEG M3 blocks exist to verify beyond the persisted rejection audit, so the verifier attests only the persisted rejection evidence, not a full PEG decode replay. This limitation was omitted in `run_01` and is present in authoritative `run_02`.
- **Strict replay / tamper results (run_02)**: strict read-only replay `ok=true`, `problems=[]`, `recomputed_terminal=finite_graph_fail`, `persisted_terminal=finite_graph_fail`, `no_de_rerun=true`, `no_decoder_rerun=true`; tamper checks recompute allocation tables, M1 registries, matrix audits, frame/block identity, per-block registration, per-source FER/waterfall, and terminal equality; zero mismatches. `run_01` verifier result is preserved but superseded by this `run_02` verifier v2 result.

## 6 Superseded candidate

The superseded candidate is `run_01` (`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_01/`). It remains byte-preserved on disk and is not deleted, but it is superseded for all closeout lifecycle and interpretation claims.

run_01 is preserved but superseded because it omitted the persisted PEG evidence limitation.

All lifecycle, gate, and bounded-contingency conclusions in sections 1-5 and 7 are taken from additive `run_02` as authoritative; `run_01` is superseded.

## 7 Scope boundary

This addendum enforces the following scope boundaries; it is read against additive `run_02` (authoritative) with `run_01` superseded:

- **Not a V31 rerun**: no code, DE, matrix construction, decoder call, or scientific output was re-executed; `run_02` is an additive verifier/closeout correction package, not a new V31 execution.
- **Not a qualification**: no FER qualification, confirmation, or promotion is made; `finite_graph_fail` is a bounded negative, not a readiness claim.
- **Not a promotion**: no method is promoted, no comparison claim is made, and no `ready_for_fresh_confirmation` or higher state is conferred.
- **Not a V32 result**: V32 (`formal-nonbinary-ldpc-v32-finite-de-bridge`) is a separate future change and its DE-bridge design/execution/evidence are not contained or pre-decided here.
- **Not complete n=2048 completion**: the 14-block 1M prefix does not complete the original 50-block n=2048 window per source and does not substitute for a full both-n gate.

Any successor work (including V32 finite-DE bridging instead of graph/seed tuning) requires a new user-authorized OpenSpec change with fresh roots, frozen before new data. Authoritative for this addendum is additive `run_02`; `run_01` remains preserved but superseded.

