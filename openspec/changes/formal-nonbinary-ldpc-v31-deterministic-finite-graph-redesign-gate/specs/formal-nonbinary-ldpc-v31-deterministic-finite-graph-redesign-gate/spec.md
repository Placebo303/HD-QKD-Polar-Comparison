# Spec — v31_deterministic_finite_graph_redesign_gate

Status: FROZEN_BY_USER_OBJECTIVE (new user-authorized change, 2026-08-20). The explicit V31 goal text is the authorization.

## Requirement: frozen architecture

The implementation MUST use q=32 (`GF2mField.create(32)`, primitive polynomial
`0b100101`, V28R field_id
`c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf`), F03 natural
MSB→LSB GF32+GF32, the V26 train-only source/delay posterior adapter, and
`lambda={2:1}`. It MUST evaluate n=1024 and n=2048. The ONLY allocation is
`m1=16`; `m2=m_total-16`.

`m_total`: n=1024 -> 1M=200, 1p5M=206, 2M=208; n=2048 -> 1M=413, 1p5M=426,
2M=430. Leakage MUST be `leak_i=5*m_i` per layer, `leak_total=5*m_total+64`
bits, `f_total=leak_total/(n*(H_L1+H_L2))` computed directly in float64; all
`f_total<1.3`. The 64-bit tag MUST NOT enter single-layer DE.

## Requirement: frozen input binding

The implementation MUST bind the exact V25 inventory, split manifest, and
channel-count paths, the V26 canonical run_02, the V28R canonical run_02_v28r,
and the V30R canonical run_01 from proposal §"Frozen input binding". V29
holdout, raw `.ttbin`, and writing to any predecessor evidence directory are
forbidden. Calling or rerunning any V30R packet is forbidden.

## Requirement: M1 pre-registered DE confirmation

For each n in {1024, 2048}, M1 MUST run exactly 30 MC-DE calls in this order:
seeds (30101..30105) × sources (1M,1p5M,2M) × layers (L1,L2), with
`n_samples=2000`, `max_iter=200`, `entropy_tol_bits=0.01`, `streak=20`.
A call passes iff `converged` and `final_entropy_bits<=0.01`. Each n passes iff
all 30 calls pass. Both n MUST pass; otherwise terminal is `de_allocation_fail`.
All calls MUST be persisted in the registered order before any later call.

## Requirement: M2 deterministic families

For each passing n, construct one packet per family:

1. `PEG-capacity-aware`: support score
   `(occupancy_after, component_flag, distance_cost, max_degree_after,
   sumsq_after, a, b)` with `distance_cost=-(2*d_check(a,b)+2)` when connected
   and `(0,0)` when disconnected; candidates with `occupancy>=31` are skipped.
2. `QC-cyclic-projective`: supports enumerated by increasing shift s>=1 then
   increasing base row a in 0..m-1, `support=(min(a,(a+s) mod m),
   max(a,(a+s) mod m))`, skipping `s%m==0`, until n columns are selected.

Both families MUST use the identical label rule: first coefficient 1; second
coefficient chosen in increasing zero-based `nonzero_cycle` order; ratio
already used by that support rejected; score `(degenerate_6_new, ratio_index)`
minimized; projective duplicates and proportional pairs MUST be zero; no zero
row/column; full GF(32) row rank required; support occupancy MUST be <=31 for
every support pair; Tanner-8 topology-only; standard variable-side ACE omitted
(`d_v=2`). No RNG, seed library, permutation, or matrix-library search.

If any required matrix fails, that packet is rejected and persisted; no
replacement construction is allowed. Rejections count toward `finite_graph_fail`
for that n.

## Requirement: M3 Bob-only validation

M3 MUST use only V25 validation frames (1M 1200..1599, 1p5M 1660..2059, 2M
2187..2586). n=1024 uses 4 frames/block -> 100 blocks/source; n=2048 uses 8
frames/block -> 50 blocks/source. All constructed (n, family) packets MUST run
the FULL validation window per source (`max_iter=200`, `streak=20`), Bob-only
sequential L1→L2 (L2 not_run when L1 fails; Alice truth never passed to the
adapter/decoder).

Per block MUST persist: source identity, block_index, frame_ids, l1_ok/l2_ok,
l1_status/l2_status, l1/l2 syndrome_ok, offline_exact, tag_verified,
false_accept, l1/l2 symbol-error counts, iterations, decoder_calls, runtime_s.
Per (n, family) per source MUST persist: block_count, exact_count,
tag_verified_count, false_accept_count, syndrome_convergence, exact_fer,
tag_fer, failure_positions, and a waterfall table (cumulative exact/tag counts
by block index).

## Requirement: pass/fail terminal

A (n, family) PASS requires, for every source: `exact_count >=
ceil(0.95*block_count)`, `tag_verified_count >= ceil(0.95*block_count)`, and
`false_accept_count == 0`. V31 terminal is `finite_graph_pass` iff each n has at
least one passing family; otherwise `finite_graph_fail`. Terminals also include
`de_allocation_fail`, `resource_blocked` (24h DE or decoder meter), and
`implementation_blocked`.

## Requirement: read-only verifier and closeout

`verify_v31(run_root)` MUST recompute from persisted evidence (no DE/decoder
rerun): field/config/input bindings, allocation tables, M1 registries and
per-n pass, matrix audits (occupancy<=31, zero duplicates/proportional,
full rank, label replay), validation frame/block identity for both n, block
record registration completeness, per-source FER/syndrome/waterfall/failure
positions, and terminal equality. It MUST return `ok=true` and `problems=[]` for
the terminal to be final. The change closes by writing the report, updating
memory/handoff/decision-log docs, and committing locally (no push). No
qualification or promotion is performed.
