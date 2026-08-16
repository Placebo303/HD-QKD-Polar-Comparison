# Decoder Improvement Plan — after Polar f≤1.3 wall and LDPC dc≤13 diagnosis (2026-08-16)

Status: PLAN — literature-grounded; implementation steps are ordered

## Current hard facts
- Existing binary v4/v5 per-plane MLC runs correctly: 500 synthetic frames, f≈4.17.
- V19 Polar MLC at f≈1.3 target fails with:
  - constructions: PW, Monte-Carlo reliability, GA
  - decoders: SC, CA-SCL list=32/128
  - N=2048/4096/8192
- V19 LDPC DE screener: frozen DE tool has dc≤13, so regular LDPC cannot cover the
  very high-rate low-error planes 0–7 at f≈1.3.
- Therefore the remaining bottleneck is **finite-length code construction + CRC/decoder
  integration**, not channel modeling.

## A. Polar path improvements (highest priority, cheapest first)

1. **Correct CRC-aided SCL integration**
   - Current repo CA-SCL checks CRC inside the C++ decoder, but our MLC payload does not
     embed CRC bits. The decoder therefore only uses best-path selection, not true CA-SCL.
   - Implementation: reserve r∈{16,24} of the K info bits for CRC; compute CRC of the
     payload, place it in the info set, decode, then check CRC before accepting a frame.
   - References:
     - Tal & Vardy, "List decoding of polar codes", IEEE Trans. Inf. Theory 2015.
     - Li, Niu, Chen et al. CRC-aided SCL; CRC error-correction reuse:
       Liu et al., "Improved polar SCL decoding by exploiting the error correction
       capability of CRC", IEEE Access 2019.
     - Rowshan, Viterbo, Micheloni, Marelli, "Repetition-assisted decoding of polar
       codes", Electronics Letters 2019 (~0.2 dB for high-rate medium blocks).
     - Segmented CRC + SCL-flip, Int. J. Communication Systems 2023.

2. **Better construction than PW/GA**
   - PW is BEC-oriented; our GA uses an AWGN J-function surrogate. For high-rate BSC
     planes, use:
     - Tal-Vardy degrading/upgrading quantization with bounded output alphabet.
       See Ghayoori & Gulliver, "Constructing polar codes using iterative bit-channel
       upgrading", arXiv 2013; Mahdavifar, "Polar coding for non-stationary channels",
       IEEE Trans. Inf. Theory 2020 (uses Tal-Vardy construction).
     - Polar-spectrum construction UBW/SUBW for SC/SCL at high rate:
       Wu, Niu, Li, "Polar codes: analysis and construction based on polar spectrum",
       arXiv:1911.xxxx 2019.
   - Implement as a new `v19_polar_construction.py` under comparison_bench, not in frozen src.

3. **Decoding upgrades after CRC is correct**
   - SCL-Flip / path-metric-aided bit-flip (WCNC 2019) for high-rate planes.
   - Adaptive list size (ADSCL) instead of fixed 128.
   - Keep N=2048/4096; do not scale N to 8192 before construction is fixed.

## B. LDPC / MLC path improvements

4. **Extend binary BSC DE to dc>13 in a v19 module**
   - The frozen `nonbinary_v7_r2_de` clamps dc≤13. Add a v19-only binary DE/threshold
     probe for regular and simple irregular ensembles with dc up to ~400.
   - Use it to re-screen planes 0–7 at f≈1.3 target.

5. **Use MET-LDPC / degree-one VNs for low-error planes**
   - Multi-edge-type LDPC with degree-one VNs resolves high-rate and error-floor issues.
     Reference: Jeong, Jung, Ha, "Rate-compatible multi-edge type LDPC code ensembles
     for CV-QKD systems", npj Quantum Information 2022.
   - Rate-compatible puncturing/shortening for QKD IR:
     Elkouss, Martinez-Mateo, Lancho, Martin, ITW 2010.
   - This matches the repo's existing Pacher/B3 plan and can reuse binary v4/v5 scaffolding.

6. **HD-QKD q-ary route remains the literature anchor**
   - Müller, Ribezzo, Zahidy, Oxenløwe, Bacco, Forchhammer,
     "Efficient information reconciliation for high-dimensional QKD",
     Quantum Information Processing 23, 2024: irregular q-ary LDPC + DE + blind
     reconciliation gives f≈1.078–1.14 at QBER 3–15%.
   - Our V18 B2 q=16 proxy reached f≈4.18; to get f≈1.3 we need the full
     DE-optimized irregular + puncture/shorten pipeline, not a plain ensemble.

## C. Recommended execution order

1. Implement CRC-aided SCL properly (reserve 16/24 CRC bits in K, encode payload CRC,
   validate after decode) and rerun plane 9 at N=2048 with list=128.
2. Add Tal-Vardy or polar-spectrum (UBW/SUBW) construction; rerun same plane.
3. Add SCL-flip if step 2 is close but not passing.
4. If Polar still fails, implement v19 dc>13 binary DE screener + MET-LDPC high-rate
   prototype for low-error planes.
5. Only after one of these reaches f≤1.3, go back to full MLC and honest leakage accounting.
