# G8 S0 Routing — Prior Efficiency (V72P3G8-PRIOR-EFFICIENCY)

S0 FACTS (from operator return + S0_RESULT.json): H_A L1=4.286720/L2=3.222720; H_B eps1e-3 L1=3.692541/L2=3.055377, eps1e-2 L1=3.710247/L2=3.073907; H_C L1=3.686901/L2=3.010950; q δ=0 mass 0.4155, H(q)=6.7438; caliber per-5-bit-plane-symbol, worse-plane gates; files S0_RESULT.json + test_g8_s0_entropy.py 6/6; 0 decoder/DE/pool calls.

RULING-1 SANITY_STOP OVERRIDDEN (cause): H_A L2=3.222720 reproduces D17 H_L2=3.222719884634378 to 6dp → computation pipeline VERIFIED (stronger than the 4.34 check); H_A L1 Δ=0.053 vs 4.3437 anchor PASSES. METHOD §4 "≈4.34" expectation miscalibrated across planes (4.34 is L1/combined; D17 proves L2 current-prior entropy is 3.22) — recorded here as METHOD corrigendum note; METHOD.md itself NOT edited (owner: user session).

RULING-2 FROZEN GATE SUPERSEDED (cause): thresholds 1.023/1.875 inherit k-based N=320−8m convention, same double-charge error class as withdrawn G7-STOP bound (R16). n-based recomputation (Â=0.6, n=128, T=64): net>0 ⟺ m<64; feasibility m≥(128H−64)/5 ⟹ bar H_eff<3.0 bits/plane-symbol. S0 worst-plane 3.6869 (H_C) still above 3.0 — but gap 0.69 bits, not 2.7. Mapping: NEITHER auto-proceed NOR unreachable-pivot; HELD pending R18 anchor-comparability (V25 0.81 vs S0 3.69 units/conditioning unresolved). S1-spend explicitly NOT authorized by this routing.

PENDING R18: V-COMPATIBLE → justify S1-marginal (+eps selection on CAL TRAIN); V-INCOMPATIBLE-* → kill S1-marginal, route F3-conditional/alignment; V-UNRESOLVABLE → single cheapest resolution step.
