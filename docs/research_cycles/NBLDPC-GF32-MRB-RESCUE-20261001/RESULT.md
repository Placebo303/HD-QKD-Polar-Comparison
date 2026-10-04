# Bounded GF32 MRB syndrome rescue — EXPLORE result

**Scientific batch:** `ebbbe5c2-f53f-4b92-a2ff-3eca358002de`  
**Machine source:** `workspace/gf32_mrb_rescue_ebbbe5c2/`  
**Terminal:** `NO_SUFFICIENT_SIGNAL` (as mechanically recomputed in the additive reaggregation cycle).

The original synthetic run completed 192 paired frames / 384 BP calls on the six fixed deep H0D graphs. Its original `summary.json` carries the damping batch UUID, contract, and seed namespace; those identity fields are wrong, so that summary is **not an authoritative MRB aggregate**. The source manifest and frame CSV identify the MRB run. The corrected aggregate is `docs/research_cycles/NBLDPC-GF32-MRB-REAGGREGATE-20261001/RESULT.md`, derived from the retained manifest and CSV without new samples or decoder calls. The original four source artifacts remain unchanged.

The corrected exact-and-syndrome success counts are 149/192 for control and 149/192 for MRB rescue, Δ=0. By graph seeds 2026093901–2026093906, both arms scored 22/32, 24/32, 28/32, 25/32, 24/32, and 26/32; all six graph deltas are zero. Paired states are both=149, candidate-only=0, control-only=0, neither=43. The control count is within the frozen 39–153 interval, but Δ≥12 and positive Δ on at least 4/6 graphs both fail.

The candidate arm had 43 raw syndrome failures and attempted rescue on all 43. It selected 43 vectors, examining 11,008 candidates total; all 43 selected outputs were syndrome-consistent but wrong, so they remain failures under the exact-AND-syndrome success definition. Control had 43 raw syndrome failures and no syndrome-consistent wrong outputs. Final syndrome acceptance was 149/192 control and 192/192 candidate. This does not measure physical undetected errors: verification is `NOT_IMPLEMENTED` and `undetected` is `NOT_MEASURED`.

The 384 calls account for 99,840 syndrome bits (260 per attempted arm), with tag bits=0. Iteration sums were 5,017 per arm. Full arm wall sums were 30.339190 s control and 36.134804 s candidate; BP runtime sums were 30.259852 s and 30.202624 s, and total rescue time was 5.835860 s. The original manifest reports 116.326794 s batch wall, 0.707384 s maximum call, and 111,742,976 B sampled high-water RSS over 1,499 samples. The batch wall covers the 66.473994 s sum of retained per-call wall times. Integrity, resource, and authorization violations were all zero.

This is one finite synthetic iid marginal-shape experiment. The accepted result remains `NO_SUFFICIENT_SIGNAL`; the 43 wrong rescued vectors preclude any verified-use claim. The stored truth, prior, belief, and estimate arrays are unavailable, so the reaggregation is a mechanical sum of stored booleans and counters, not vector-level replay or redecoding. It does not establish a conditional-channel result, FER, `f_eff`, SKR, throughput, qualification, publication, route outcome, or cross-batch ranking.
