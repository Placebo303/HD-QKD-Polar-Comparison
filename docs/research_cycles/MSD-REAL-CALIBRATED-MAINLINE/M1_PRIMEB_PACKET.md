# M1′b packet amendment — PEG-dv3 + SPC-safety mixed per-plane codes (2026-10-05, EXPLORE)
#
# Parent chain: M1_PACKET.md → M1_PRIMEA_PACKET.md (both retained as measured
# negatives). WHAT CHANGES vs M1′a: code family only. Everything else frozen:
# TRAIN plug-in channel, NATURAL LSB-first, conditional priors, disclose/
# receive chain, seeds, f formula, B, result root, log.
#
# Why (measured): accumulator dead at all m (M1 smoke/diag); repetition exact-ML
# structurally fragile (4.6% per-group loss → ~100% block FER, primea smoke);
# random ensemble poor distance. PEG dv3 measured: R=0.5 exact 8/8 at p≤0.05
# (decoder validated), R=0.11 BSC(0.24) 4/6 at m=950/970 (build 0.6 s,
# zero 4-cycle edges). Mechanism found: high-dv dense graphs kill BP; dv3 wins.
#
# Family: plane 0/1 → PEG dv3, m_k = ceil(N·h_k + C_k); planes 2–9 (h=0) → SPC
# groups g=64 exact-ML safety margin (zero-entropy planes need no rate curve).
# Ladder (= FER–rate curve): plane-0 C_0 ∈ {96, 128, 160, 192} (N=1024),
# C_0 ∈ {1500, 2000, 2569} (N=16384 — D3 measured same-rate R_0=0.055 10/10);
# plane-1 C_1 ∈ {16, 32} (T2-1M/N=1024 only, 2 pts), N=16384 plane-1 fixed
# m_1=600 (D3 full-chain 10/10; ceil-rule m_1=195 gives dc=252, BP-hostile);
# SPC g=64 (N=1024) / g=256 (N=16384, D3 10/10). Backend: make_bp_decoder
# (parallel/product_sum, max_iter=200 — probes used 200; changed from 100 with
# this record) for PEG planes; tested GroupML exact-ML for SPC planes.
# Points: N=1024: plane-0 ladder 4 rungs × 3 sources + plane-1 2 pts (14 pts);
# N=16384: plane-0 ladder {128, 160} × 3 sources (6 pts; {96,192} added only if
# N=16384 PEG build ≤ 180 s). B=300 everywhere. Wall cap 21600 s; stop rule:
# cut N=16384 to best single rung if projection exceeds cap.
# Success for today: closed MSD loop + measured curves/f/costs (no gate on f).
