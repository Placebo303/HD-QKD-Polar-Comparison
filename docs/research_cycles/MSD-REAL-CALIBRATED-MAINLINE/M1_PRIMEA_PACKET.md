# M1′a packet amendment — repetition/SPC exact-ML per-plane codes (2026-10-05, EXPLORE)
#
# Parent: M1_PACKET.md (same track, channel, priors, staging, backends-interface,
# seeds, f formula, result root, log). WHAT CHANGES: per-plane code family only.
#
# Why (measured, R4-safe): frozen dv-3 accumulator family measured unusable —
# plane-0 T2-1M fails 8/8 at m ∈ {870, 910, 950, 990} (R 0.15→0.03), 2/8 at
# m=1020; BSC threshold probe: R=0.07 decodes p=0.05 but not p≥0.10, R=0.50
# fails even at p=0.05 (all 4 BP schedule/method combos); OSD_E-1 and
# max_iter 1000 do not rescue. Evidence: workspace/m1_synthetic/m1_20261005/
# smoke.json, diag_plane0.json, diag_plane0_deep.json. This closes NO route:
# it replaces an unusable construction with the simplest exactly-decodable
# family to close the first MSD loop and MEASURE the code gap.
#
# Family: per group of g consecutive bits, (g−1) checks.
#   repetition groups: checks are adjacent differences (codewords 0^g, 1^g),
#     exact ML by chain DP; used where h_k > 0.05 (plane 0).
#   SPC groups: one parity check per group, exact ML (flip min-weight on
#     violation); used where h_k == 0 (planes 2–9).
#   plane 1 (0 < h ≤ 0.05): repetition g ∈ {2,3,4} ladder.
# Ladders (= per-plane FER–rate curves): plane 0 g ∈ {5,7,9,11};
# planes 2–9 g ∈ {32,64,128}. m = N − n_groups (repetition), m = n_groups (SPC).
# Decoders honor the receive_syndromes factory interface
# (parity_check_matrix=, error_channel=) → decode(delta); group structure is
# captured in the factory closure; H stays canonical CSR so disclose_syndromes
# and the receiver run UNCHANGED. w_i = log((1−p_i)/p_i), p_i = error_channel.
# Success for today: full MSD loop closed end-to-end with measured
# per-plane FER curves + three-source f_expected (both N) + per-block cost,
# whatever the f value (no threshold gate on this branch).
# MDE: same B_1024=300/B_16384=300 as parent; CI-reported.
