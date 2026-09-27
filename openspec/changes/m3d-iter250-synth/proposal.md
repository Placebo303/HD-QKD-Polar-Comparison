# M3D: optional 250-iteration synthetic diagnostic

Track: `EXPLORE` (bounded synthetic diagnostic). M3C's stopped real 2M rows generated a runtime hypothesis: many nonexact calls exhaust 300 iterations. This change tests a 250-iteration cap on 32 frozen, selected M3-b synthetic Stage-1 calls (8 previously exact and 8 previously nonexact per graph). It does not reopen M3C, perform real-data execution, or make a route/FER/security claim.

Add a default-preserving optional `max_iter` argument to `v80_b2f_campaign.decode_block_marginal`; add a small Stage-1-only M3D CLI and focused fake tests. The existing M3-b `max_iter=300` result roots and all baseline entrypoints remain unchanged. Scientific execution requires the separate frozen packet and Pre-EXECUTE in `docs/research_cycles/M3D-ITER250-SYNTH/`.
