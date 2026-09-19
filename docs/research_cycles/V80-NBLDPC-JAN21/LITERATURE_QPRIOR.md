# V80 LITERATURE_QPRIOR — Mitra arXiv:2305.00956 (QIP 2024 version DOI 10.1007/s11128-024-04343-8)

Source: arXiv:2305.00956 full text via ar5iv. Extraction only; no new science.

- NB-MLC a-parameter: q = a·b + r splits one q-ary symbol into b+1 layers over GF(2^a) / GF(2^r).
- Key-rate equation: r = Σα_i(1−E_i)(N−m_i)/N (per-layer FER-discounted rate sum).
- Non-monotonic in a: key rate peaks strictly interior (neither a=1 nor a=q); best trade-off at small a=3–4.
- Latency = sum-of-layers (log-linear in field size).
- JRDO: density evolution with objective f(L,R) = (1−E)R; MC-evaluated (200–300 sims feasible at 1–10% FER); VN degrees 2–5 + two-element CN; ~40% over Zhou.
- Channel-matched design required: BIAWGN-optimized degrees perform WORSE than regular VN-3 on the QKD channel.
- Mapping = bit-group convenience (mapping effects reserved as future work).
- ET channel = local-Gaussian + global-uniform mixture, low SNR, FER 1–10%.

q=10 mapping candidates: a=3 → 3+3+4, a=4 → 4+4+2, a=5 → 5+5 = F03. Scheme recommendation carried in decision-log line above.

## dv-support question (2026-09-20, additive; closes S1 audit P7 first bullet)

P7 asked whether S1's `DV_SUPPORT=(2,3,4,5,8,13,20)` / `DV_CEILING=40` vs the
paper's VN 2–5 could explain low-m (44–46) non-convergence (search dilution).
Re-read of full text (ar5iv 2305.00956, §§II–V). Decision-relevant numbers only:

- (a) VN-degree support used: JRDO optimizes `L(x)=Σ_{d=2}^{5} L_d`
  (§V, first paragraph: "we set L1 to zero and a maximum VN degree of 5").
  Baseline curves: regular VN-3 (`L(x)=x^3`, Fig. 3 all curves; Fig. 4
  circle-marked); Zhou-et-al. reference = random construction, constant VN-3
  (Fig. 4 diamond-marked); BIAWGN comparison = Richardson/Shokrollahi/Urbanke
  Table I distribution, max VN degree 5 (Fig. 4 triangle-marked).
  CN side: a two-element CN-degree distribution fitted to the rate (§II-3);
  Zhou reference has no CN restriction. S1's degrees 8/13/20/40 appear
  nowhere in the paper.
- (b) Rate regime and q used: block length N=2000 symbols, FFT-based
  sum-product SW decoding (§V). Layer fields GF(2^a) with a=3–4 recommended
  (best latency/key-rate trade-off, Fig. 3 right); demo systems q=5 (Fig. 4
  middle, 2^5 bins/frame, 300 ps) and q=6 (Figs. 3–4, 2^6 bins/frame).
  Code rates R per layer are jointly optimized with L(x) (objective
  f=(1−E)·R, MC-evaluated at 200–300 sims); no single numeric rate is quoted
  in text — operating FER is 1–10% with key-rate peak at FER ≈5% (Fig. 2).
  Explicit per-layer R values: **not stated**.
- (c) Low-m / high-rate non-convergence or search-space width: **not stated**
  — the paper contains no statement about low-m (high-rate) non-convergence,
  no convergence-vs-m sweep, and no discussion of search-space width/dilution
  effects.
- (d) Whether narrow dv support (2–5) was essential or convenience:
  **not stated** — the 2–5 range is given as the JRDO framework setting with
  no ablation against wider support and no essential-vs-convenience claim
  (do not infer).
