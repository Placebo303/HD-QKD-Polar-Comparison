# V11 Literature Review and Evidence Boundary

Reviewed 2026-08-06. Exact numerical anchors were checked in accessible full
text where noted; abstract-only theory is not used as a numerical acceptance
anchor.

## Primary executable reference

1. A. Ben Yacoub, F. Lázaro, A. Graell i Amat, and G. Liva, “Symbol Message
   Passing Decoding of Nonbinary Spatially-Coupled Low-Density Parity-Check
   Codes,” AEIT 2019, DOI: https://doi.org/10.23919/AEIT.2019.8893373.
   - Full text checked.
   - Defines the q-ary symmetric channel and protograph SC-LDPC SMP density
     evolution.
   - Rate-1/2 `(3,6)`, `W=30` numerical anchors: q=4 uncoupled .0890,
     coupled .0942; q=16 uncoupled .1075, coupled .1288.
   - Boundary: SMP passes only symbol estimates and is not FFT-QSPA or a
     full-probability-vector decoder.

## Coupling, termination, and window semantics

2. D. G. M. Mitchell, M. Lentmaier, and D. J. Costello, Jr., “Spatially
   Coupled LDPC Codes Constructed From Protographs,” IEEE Transactions on
   Information Theory 61(9), 2015, DOI: 10.1109/TIT.2015.2453267,
   arXiv:1407.5366.
   - Full text checked.
   - Supports `B=sum_i B_i`, terminated length `L`, coupling width `w`, and
     `R_L = 1 - ((L+w)/L)(1-R)`.

3. D. Wei et al., “Threshold Analysis of Non-Binary Spatially-Coupled LDPC
   Codes With Windowed Decoding,” ISIT 2014,
   DOI: 10.1109/ISIT.2014.6874959, arXiv:1403.3583.
   - Full text checked.
   - Supports the window definition, termination-rate accounting, the
     latency/complexity motivation, and the need to compare a finite window
     with a full-chain control.
   - Its reported channel examples are not used as QSC threshold anchors.

## Threshold-saturation theory

4. I. Andriyanova and A. Graell i Amat, “Threshold Saturation for Nonbinary
   Spatially-Coupled LDPC Codes on the Binary Erasure Channel,” IEEE
   Transactions on Information Theory 62(5), 2016,
   DOI: 10.1109/TIT.2016.2540800, arXiv:1311.2003.
   - Full text checked; this is BEC theory, not direct QSC evidence.

5. C. Zhang et al., “Threshold Saturation for Nonbinary Spatially Coupled LDPC
   Ensembles on Discrete-Input Memoryless Channels,” IEEE Communications
   Letters 20(9), 2016, DOI: 10.1109/LCOMM.2016.2600662.
   - Abstract/metadata checked; supports broader channel-class motivation but
     supplies no V11 numerical gate.

6. J. Lyu and G. He, “SC-LDPC Codes Over F_q: Minimum Distance, Decoding
   Analysis and Threshold Saturation,” arXiv:2512.24232 (2025),
   DOI: 10.48550/arXiv.2512.24232.
   - Recent preprint; supplementary theory for q-ary-input memoryless
     symmetric channels only. It is not the sole basis of any gate.

## HD-QKD channel contract

7. R. Müller et al., “Efficient Information Reconciliation for
   High-Dimensional Quantum Key Distribution,” Quantum Information Processing
   23, 195 (2024), DOI: 10.1007/s11128-024-04395-w,
   arXiv:2307.02225v2.
   - Full text checked in the predecessor V8 work.
   - Supports the q-ary symmetric-channel model and leakage-efficiency framing
     for high-dimensional QKD; it is not spatial-coupling evidence.

## Resulting evidence boundary

- The 2019 QSC SMP paper is the executable reference for coupling machinery.
- The 2014/2015 papers define window, edge-spreading, and rate-loss semantics.
- The threshold-saturation papers motivate the hypothesis but do not prove
  that the frozen GF(1024) V10 ensembles will pass .22/.32.
- Only the separately validated full-vector coupled MC-DE may decide the V11
  GF(1024) gate.
