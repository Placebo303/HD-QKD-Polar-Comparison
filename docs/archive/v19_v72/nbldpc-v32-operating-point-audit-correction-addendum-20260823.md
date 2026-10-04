# V32 Operating-Point Audit Correction — Accepted Addendum (2026-08-23)

**Change**: `formal-nonbinary-ldpc-v32-operating-point-audit-correction`
**Status**: ACCEPTED by Codex master review (F-G1 = ACCEPT on commit `3110cb0e`)
**Companion verdict doc**: `docs/nbldpc-v32-main-review-verdict-20260822.md`
**Related**: `docs/nbldpc-v31-closeout-audit-addendum-20260821.md` (V31 lifecycle)

## 1. What this change corrects

The V32 finite-DE bridge (`nbldpc_v32_finite_de_bridge/run_01`) is valid raw
evidence — B0 6/6; B1–B4 0/60 each; B5 read-only import; exact-once execution,
no resume, 10047 s within the 12 h cap — but its persisted terminal
`finite_graph_decoder_mismatch` is **not an accepted attribution**, because arm
B1 was not a matched empirical-joint control:

- B1 generator law Q_B1: Alice ~ Uniform(0..1023), error event ~
  Bernoulli(raw_ser), nonzero delta ~ Uniform[1,1023] mod 1024.
- Decoder likelihoods: V25 empirical joint P(A,B) = N_ab/total.
- Consequence: positive Q mass on P-zero cells (analytic ≈ 0.239468 / 0.254127 /
  0.255348 for 1M / 1p5M / 2M) ⇒ full E_Q[-log2 P] = infinity ⇒ over-confident
  wrong messages drive divergence regardless of graph quality.

## 2. Lifecycle correction

The first operating-point audit
(`formal-nonbinary-ldpc-v32-operating-point-consistency-audit`, impl commit
`60117174` preceding its OpenSpec commit `dda3503e`) is annotated:

```
post_hoc_exploratory_only
not_formal_pre_registered_gate
numerical_outputs_retained
scientific_terminal_superseded_pending_correction
```

Its run_01 ten files are preserved byte-identical; nothing was rewritten.

The correction change re-established a pre-registered lifecycle:
freeze `59ba0236` → implementation `0765d893` → evidence + independent review
`29a5dafe` → verifier semantic guards `3110cb0e`.

## 3. Accepted corrected semantics (independently recomputed, R2 bit-exact)

| Quantity | 1M | 1p5M | 2M |
|---|---|---|---|
| q_mass_on_p_zero_cells | 0.2394680 | 0.2541265 | 0.2553477 |
| full_expected_nll | "infinity" | "infinity" | "infinity" |
| conditional_finite_support_mean (bits/symbol) | 0.3969 | 0.4262 | 0.4312 |
| truncated_common_support_cross_entropy (bits) | 7.9091 | 7.7778 | 7.7688 |

Naming is normative: the conditional MC mean and the common-support truncated
cross entropy must never be called full NLL / full cross entropy.

D0 signature (corrected reading): B1 active divergence, dominated by support
mismatch; B2 `l2_errors_final=1024` is a not-run sentinel (never divergence);
B3/B4 improve-but-no-syndrome (~250 → ~179 mean L2 errors) — substantive
correction capability without convergence.

## 4. Dual-law feasibility (accepted conclusion scope)

- **Empirical P budget**: nominal information budget feasible only — pure
  syndrome gaps +179.7/+184.6/+187.5 bits, verbatim gaps +243.7/+248.6/+251.5
  bits. No finite-length, DE, fixed-graph, or decoder feasibility claim.
- **Original Q_B1 budget**: information-theoretically infeasible at the current
  allocation — H_Q(B|A) ≈ 3.1921/3.3626/3.3773 bits/symbol ⇒ required ≈
  3268.7/3443.3/3458.4 bits vs pure syndrome 1000/1030/1040 bits. DE on Q_B1 is
  meaningless and was not run.

## 5. Verifier semantic guards (commit `3110cb0e`, ACCEPT)

- `full_expected_nll="infinity"` iff q_mass_on_p_zero_cells > 0; otherwise the
  JSON-safe finite analytic value (zero-mass representation recorded in the
  fix handoff).
- Minimal explicit run-root guardrail: protected old roots and their subpaths,
  repo root, results root, diagnostics root and other too-broad paths are
  rejected; only the frozen additive v2 root, or a workspace test root with an
  explicit fake runner, is allowed.
- verify_manifest field-level guards: schema, lifecycle labels, no_de_run /
  no_decoder_run / old_roots_read_only, implementation identity structure,
  expected-output list, frozen-block equality with module constants, plus the
  existing freeze digest and 29 input hashes. Git HEAD / implementation
  identity bind the execution time and are never compared against current state.

## 6. Next authorized boundary

The next question is exactly: **under the V25 empirical joint P(A,B), F03/A02
allocation, and V31 actual layer rates (L1 0.984375 ×3 sources; L2
0.8203125 / 0.814453125 / 0.8125), does the corresponding ensemble DE converge
for all three sources and both layers?**

A candidate change (`formal-nonbinary-ldpc-v33-rate-aligned-empirical-channel-
de-diagnostic`) exists as `DRAFT_PENDING_FREEZE_REVIEW` only. Fixed-graph,
decoder, and NB-Polar successor selection remain undecided until that question
is answered under a frozen, authorized OpenSpec.

## 7. Immutable evidence

- `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v32_finite_de_bridge/run_01/` — raw bridge record, byte-identical.
- `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v32_operating_point_audit/run_01/` — post-hoc exploratory audit, byte-identical.
- `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v32_operating_point_audit_v2/run_01/` — accepted correction evidence (eight files).

No qualification or promotion is claimed anywhere in this addendum.
