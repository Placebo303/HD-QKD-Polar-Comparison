# Spec — v30_projective_safe_finite_graph_gate

Status: `FROZEN_P102_ACCEPTED`. P102 was accepted by the main thread on
2026-08-20; implementation and execution remain a separate goal.

## Requirement: frozen architecture and allocation

The implementation MUST use `q=32`, `n=1024`, F03 natural MSB→LSB
GF32+GF32, the V26 train-only source/delay posterior, `lambda={2:1}`, and
the frozen 64-bit tag/leakage contract. It MUST use only shared `m1` in
`{9,12,16,24,32,40}` with source `m_total={200,206,208}` and `m2=m_total-m1`.
V28R `m1=6` is a control and MUST NOT be promoted as a candidate. No degree,
matrix, seed, split, threshold, or iteration search is allowed.

For each allocation, M1 MUST execute exactly 12 screen calls (2 seeds × 3
sources × 2 layers). Eligibility requires all 12 final entropies `<=0.01` and
convergence. Eligible allocations MUST be ranked by
`(worst_final_entropy, mean_final_entropy, m1)`; at most the first two enter
five-seed confirmation, which requires 30/30 convergence. The same tuple MUST
order two passing allocations before M2.

## Requirement: projective safety

Every degree-two column MUST have two nonzero entries. Its normalized key MUST
be `(sorted_check_pair, coefficient_ratio)` in GF(32). A matrix MUST have no
duplicate key, no proportional-column pair, no zero row/column, and full row
rank. L1 is shared; L2 is independently source-specific. Balanced-projective
and PEG-ACE-projective are the only allowed families in this change. For rows
`a<b`, the first coefficient MUST be `1` and the second MUST follow the frozen
GF(32) nonzero-cycle without repeating a ratio for that support. PEG/ACE MAY
choose supports only; no extra RNG is allowed. A rank failure rejects the
matrix and cannot be repaired by changing a seed. The two families MUST
produce at most two matrix packets per allocation and, because M1 retains at
most two allocations, at most four packets total.

## Requirement: validation boundary

M3 MUST use only validation frames 1M `1200..1599`, 1p5M `1660..2059`, and 2M
`2187..2586`, inclusive. It MUST use 256 pairs/frame and four-frame 1024-
symbol blocks. V29 holdout, raw `.ttbin`, and validation fitting/calibration
are forbidden.

## Requirement: finite development gate

Screen MUST evaluate 20 blocks/source at `max_iter=100` and require 15/20
exact/tag-verified per source with false_accept=0 for each of at most four
matrices. Eligible matrices MUST be ranked by
`(-min_source_exact,-total_exact,four_cycle_count,worst_ACE_penalty,m1,family_order)`;
only top-1 enters confirmation. Confirmation MUST evaluate the next 50
blocks/source at `max_iter=200` and require 45/50 exact/tag-verified per source
with false_accept=0. L1→L2 is Bob-only and L2 receives only the returned L1
estimate. Every block record MUST be persisted before the next block; L1
failure makes L2 `not_run`.

M1 DE calls and M3 decoder calls MUST have independent cumulative 24-hour
meters. After a current call/block is persisted, stage completion or an
irreversible failure is evaluated before the resource gate; no next call/block
may start after a terminal decision. M2 construction is outside both meters,
but an M2 implementation timeout is `implementation_blocked`.

## Requirement: terminal and verification

PASS MUST be `pass_projective_finite_graph_ready_for_fresh` and requires all
structural, binding, leakage, and confirmation gates. Other terminals MUST be
`finite_graph_fail`, `de_allocation_fail`, `resource_blocked`, or
`implementation_blocked`. M1 with no confirmed allocation is
`de_allocation_fail`; M2 with no valid matrix is `finite_graph_fail`; M3 with
no eligible screen matrix or failed confirmation is `finite_graph_fail`. The
verifier MUST rebuild projective audits and replay evidence, including rank
tuples, eligible sets, selected allocation/family/matrix IDs, and terminal
selection, without rerunning DE/decoder. PASS only permits proposing V31 fresh
qualification; it does not itself qualify or promote.
