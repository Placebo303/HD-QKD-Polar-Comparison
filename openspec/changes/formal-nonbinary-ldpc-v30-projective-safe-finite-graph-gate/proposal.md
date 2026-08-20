# V30 — projective-safe finite-graph gate for GF32×GF32

Status: `FROZEN_P102_ACCEPTED`  
P102: main-thread freeze review accepted on 2026-08-20. Implementation and
execution remain a separate goal; no V30 run has started.

## What

Create a new finite-graph development gate that preserves the successful V25
channel model and V27/V29 leakage accounting, but replaces the V28R degree-two
matrix construction with deterministic projective-safe graph families.

The gate has four phases:

- M0: reproduce and persist the finite-column projective audit;
- M1: use channel-informed multilevel DE to screen a small, explicitly frozen
  allocation set;
- M2: construct and audit deterministic projective-safe finite matrices;
- M3: evaluate only the V25 validation split as a development finite-code gate.

## Why

V29 stopped after 9 of 300 blocks because the 1M source could reach at most
92/100 exact blocks, below the 95/100 gate. Independent V28R structural audit
found 303 duplicate projective classes and 1107 guaranteed proportional-column
weight-2 pairs in the shared L1 matrix, hence `d_min<=2` for that finite
construction. This is a graph-construction defect, not a conclusion that the
channel-informed GF32×GF32 route is impossible.

## In scope

- GF(32), `n=1024`, F03 natural MSB→LSB GF32+GF32;
- V26 train-only source/delay-conditioned channel posterior;
- source leakage budgets `m_total={200,206,208}` for 1M/1p5M/2M and the
  existing 64-bit tag accounting;
- shared L1 allocation candidates `{9,12,16,24,32,40}`, with
  `m2=m_total-m1` source by source;
- deterministic balanced-projective and PEG-ACE-projective graph families;
- projective, rank, girth/4-cycle, ACE, syndrome, tag, runtime, and finite
  validation evidence.

## Out of scope

- reusing the V29 holdout as fresh qualification data;
- raw `.ttbin`, fresh qualification, promotion, or public residual claims;
- random degree/matrix search, seed libraries, or blind repository search;
- MET, joint protograph, cross-layer checks, or a new decoder;
- changing q, n, F03 labels, channel training split, leakage target, or the
  V29 95/100 semantics without a new change.

## Frozen lifecycle boundary

Before P102 ACCEPT, only document review and static checks are allowed. After
P102, one M0–M3 execution packet may run under the frozen parameters. A failed
M1 allocation gate is terminal for V30; it does not authorize random search.
V30 PASS may propose V31 fresh time-separated qualification. V31 PASS is the
only route to V32 integration/benchmark work.

The M1 screen is eligible only when all 12 calls for one allocation (2 seeds ×
3 sources × 2 layers) converge with final entropy `<=0.01`. Eligible
allocations are ranked by `(worst_final_entropy, mean_final_entropy, m1)`;
`min(2,Neligible)` enter five-seed confirmation, which requires 30/30 calls
to converge. If two allocations pass, the same tuple orders the survivors
before M2. M2 constructs at most four matrix packets per allocation, with the
two frozen families collectively sharing that cap. M3 screens at most four
matrix packets per allocation and sends only the single top-ranked eligible
matrix to the 50-block confirmation.

M1 DE calls and M3 decoder calls each have an independent cumulative 24-hour
gate. The current call/block is persisted first; stage completion or an
irreversible failure is decided before the resource gate, and no next call is
started after any terminal decision. M2 construction is outside both resource
meters; an M2 implementation timeout is `implementation_blocked`.

## Terminal states

- `pass_projective_finite_graph_ready_for_fresh`;
- `finite_graph_fail`;
- `de_allocation_fail`;
- `resource_blocked`;
- `implementation_blocked`.
