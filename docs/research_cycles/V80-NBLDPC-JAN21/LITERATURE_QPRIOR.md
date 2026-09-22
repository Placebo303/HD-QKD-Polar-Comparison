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

## Entropy-2024 rate-adaptive + syndrome-estimation neighbor (2026-09-20)

Source: Treeviriyanupab & Zhang, *Efficient integration of rate-adaptive reconciliation
with syndrome-based error estimation and subblock confirmation for QKD*, Entropy 2024,
26, 53 (doc_id 5dd2d27e...77dc2, 7 cites). Binary-LDPC BB84 DV-QKD — off-target for NB;
mechanism directly informs our D_blind surcharge design. Extraction only; not-stated marked.
(a) Rate-adaptive mechanism: puncturing + shortening (NOT blind — needs a priori q_est);
R_C^0=(N-M)/N tuned to R_C^(opt)=(N-M-n_s)/(N-n_p-n_s); mother-rate set R, pick closest
to R_C^(opt)=1-eta_IR^base*H(q_est); eta_IR^base from experimental evaluation (value: not-stated);
fixed n_p/n_s numbers: not-stated (computed per q_est). Two lengths: primary N=64800, subblock N_sb=16200.
(b) Syndrome-based QBER estimation: MLE q_est=argmax L(q|S_dis), q in [0,q_threshold];
per-syndrome-bit Bernoulli likelihood, p(q,d_c)=sum over odd k of C(d_c,k)q^k(1-q)^(d_c-k);
syndrome from max-rate mother code R_C^(max); puncturing/shortening-aware variant drops rows
touching punctured positions (omega_i cap p = empty); abort if q_est>11%. Subblock confirmation:
polynomial hash per subblock; primary key split into N_sb=16200 subblocks; FAILED subblocks
re-reconciled at length N_sb (no discarding); 64-bit hash, P_collision<=7.11e-12 per subblock.
(c) Quoted numbers: primary round ~99.93% success, FER 7.25e-4 avg over QBER range (2000 iters/point);
after additional rounds 100% success, FER zero (2000 iters); eta_IR "closer to 1" than
Cascade/blind/symmetric-blind (numeric eta: not-stated, figure-only); L_rec near theoretical
limit (numeric: not-stated); Cascade >40 rounds per 10^4-bit frame (blind round counts: not-stated);
1-Kbps distance ~49.10 km vs perfect-IR ~49.85 km (1-GHz BB84, Table-4 device params).

## IEEE 11440984 full text (user-supplied PDF, 2026-09-20)

Chen et al., ECCST 2025, pp. 6-9 (DOI 10.1109/eccst68196.2025.11440984).
Extraction from full text; decision-relevant facts only.
(a) System model: DV-QKD under BSC; six codes — binary GF(2) + NB
GF(8)/16/32/64/128, ALL rate 0.5, length 20,000, identical degree dists.
Mapping: q bits grouped into one symbol over GF(2^q); split back post-decode.
(b) Rate-adaptive: shortening + puncturing (NOT blind — needs QBER estimate,
params recomputed per run). Two granularities: symbol-level
Rsym=(K-Ssym*q)/(N-(Ssym+Psym)*q) (Eq.9); bit-level Rbit=(K-Sbit)/(N-Sbit-Pbit)
(Eq.10, finer, suits binary source). Alice signals shortened positions+values
and punctured positions classically (Fig.3). GF(128)+adaptation holds f<1.1
over 0.06 QBER span. Fig.4/5 caption rate numbers (0.10-0.15 / 0.09-0.05)
read qualitative-only (inconsistent with 0.5 mother as printed).
(c) Table I (FFT-BP, max 200 iter, f=(1-R)/H_bin, FER held ~constant by design):
GF(2): QBER .046 f=1.8577 FER .74; GF(8): .072/1.3393/.76; GF(16): .085/1.1917/.76;
GF(32): .092/1.1284/.75; GF(64): .097/1.0883/.75; GF(128): .100/1.0661/.74.
Gains grow monotonically with field order. NOTE: FER~75% is a fixed-rate snapshot
(authors hold FER constant to isolate field gains), NOT a qualification point —
no clash with our FER<=5% gate.
(d) Construction: PEG-built H, identical degree dists, distribution details
(lambda/rho, dv/dc) NOT STATED; no QC/EMS; decoder = FFT-BP syndrome-based
(Alice sends S=H*X'T over GF(Q); tentative-decode, syndrome match, iterate).
(e) vs S2: SUPPORTS rate~0.90 direction (GF(128) 1.0661 < 1.3 gate; PEG family;
bit-level puncture/shorten fits binary-source HD data). QUALIFIES: demo at rate
0.5 / n=20k / QBER<=10% is far from our rate~0.90, n=256/1024, 4-8% point; their
f uses binary-entropy denominator, NOT our frozen whole-frame-with-tag f —
existence evidence only, not S2 design inputs. No q=1024 or GF(32)^2-layered
test (max GF(128)); superframe n=1024 unaddressed.

Provenance: user-supplied PDF (2572680 B, sha256 579bd831.., NOT committed);
text at /tmp/opencode/ieee11440984.txt via pypdf (temp /tmp target, .venv untouched).
