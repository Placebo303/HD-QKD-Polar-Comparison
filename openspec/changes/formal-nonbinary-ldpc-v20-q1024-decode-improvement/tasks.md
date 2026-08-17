# Tasks: formal-nonbinary-ldpc-v20-q1024-decode-improvement

Status: APPROVED/M5_CONCLUDED — V20 M5 concluded: n64 bounded4 primary best FER=0.515625; n80 top-K alternative high-variance FER=0.5833 (12 seeds).

## Current blocker
V19 showed all current PEG/FFT-QSPA + bounded OSD attempts at q=1024 f≤1.3
result in `exact_mismatch` (or high FER at best point n=64 f=1.136: 28/64 exact).
Round 83-84 added MRB-OSD, rho variants, and fixed-frame code-seed sweeps; none
recovered the hard frame seed 2055. V20 must start from this blocker and select a
strictly stronger decoder/construction before execute.

## T0 Planning
- [x] P0: freeze proposal/design/tasks and get main-thread/acceptance review (user approved)
- [ ] P1: select M1/M2/M3/M4/M5 subset and pre-register budgets/seeds/stop rules

## T1 Engineering
- [x] I01 (V19 prototype): implement bounded q-ary OSD order-0/1 using GF(q) field tables (`nonbinary_v19_osd.py`)
- [x] I02 (V19 prototype): add OSD integration to `nonbinary_v19_finite`
- [ ] I03: add improved construction/QC-PEG helper if M2 selected
- [ ] I04: add retry/blind-reconciliation helper if M3 selected
- [ ] I05: add channel-aware DE gate CLI if M4 selected
- [x] I06 (V19 prototype): tests for OSD helpers in `test_nonbinary_v19_osd.py`
- [x] I07 (V19 prototype): implement reliability-sorted MRB-OSD `osd_decode_candidates_mrb` and integrate MRB OSD-1/2
- [x] I08 (V20 prototype): implement `osd_decode_candidates_bounded_weight` (max_weight<=3) and integrate into finite pipeline
- [x] I09 (V20): optimize/evaluate bounded-weight max_weight=4 on deterministic q=1024 frames (numba ML; integrated as post-decoder)
- [x] I10 (V20): extend bounded-weight ML to max_weight=5 / n=80,m=5 (single-ML did not improve n80 seed2300; lower-weight wrong candidates outrank Alice)
- [x] I11 (V20): implement top-K list decoding `bounded_weight_ml_decode_candidates` (max_weight=5, top_k=4); direct frame0 test includes Alice in top4
- [x] I12 (V20): add frame_offset support for chunked finite runs; n80 seed2300 chunked integration confirms 2/8 (no net gain over V19)
- [x] I13 (V20): additional n64 bounded4 probes on lambda062/058 and rho35_39 show no improvement over current best
- [x] I14 (V20): add edge_label_seed support; fixed-frame edge-label sweep els1/2/3 on seed2252 all 5/8 (no gain)
- [x] I15 (V20): n80 seed2301 top-K=4 list integration improves 4/8 -> 5/8 (frame5 recovered)
- [x] I16 (V20): n80 seed2303 top-K=4 list integration improves 3/8 -> 4/8 (frame1 recovered)
- [x] I17 (V20): n80 seed2304 top-K=4 integration no gain (3/8 -> 3/8); 4-seed aggregate 14/32 FER=0.5625
- [x] I18 (V20): n80 seed2305 top-K=4 integration 3/8 -> 4/8; 5-seed aggregate 18/40 FER=0.55
- [x] I19 (V20): n80 seed2306 top-K=4 integration 4/8 -> 5/8; 6-seed aggregate 23/48 FER=0.5208
- [x] I20 (V20): n80 seed2307 top-K=4 integration 4/8 -> 5/8; 7-seed aggregate 28/56 FER=0.5 (new best)
- [x] I21 (V20): n80 seed2308 top-K=4 integration 2/8 -> 3/8; 8-seed aggregate 31/64 FER=0.515625 (ties n64)
- [x] I22 (V20): n80 seed2309 top-K=4 integration 3/8 -> 4/8; 9-seed aggregate 35/72 FER=0.5139 (slightly better than n64)
- [x] I23 (V20): n80 seed2310 top-K=4 integration 0/8 -> 0/8; 10-seed aggregate 35/80 FER=0.5625 (high variance)
- [x] I24 (V20): n80 seed2311 top-K=4 integration 4/8 -> 4/8; 11-seed aggregate 39/88 FER=0.5568
- [x] I25 (V20): n80 seed2312 top-K=4 integration 1/8 -> 1/8; 12-seed aggregate 40/96 FER=0.5833
- [x] I26 (V20): final N6 v6 comparison table records n64 primary and n80 alternative

## T2 Execute
- [x] E01: execute once on deterministic q=1024 synthetic frames (M5 bounded-ML post-decoder; 3 verified seeds)
- [x] E02: record exact_correct / decode_failed / FER / f / runtime / status (31/64 exact, FER=0.515625)

## T3 Verify/Closeout
- [x] V01: read-only verification of M5 integrated outputs (31/64, no issues)
- [x] C01: update CURRENT_TASK.md, AGENT_HANDOFF.md, AGENT_PROJECT_MEMORY.md
- [x] C02: local git commit only; no push
