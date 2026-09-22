# V80 LITERATURE_PA_AWARE — Tauz et al., Block-MDS QC-LDPC (ITW 2024)

Paper: Tauz, Mitra, Shreekumar, Sarihan, Wong, Dolecek,
*Block-MDS QC-LDPC Codes with Application to High-Dimensional QKD*,
IEEE ITW 2024, DOI `10.1109/itw61385.2024.10806945`.
Retrieval: arXiv API (found `arXiv:2403.00192`, same authors/title,
"Block-MDS QC-LDPC Codes for Information Reconciliation in Key
Distribution") + full text via ar5iv. IEEE Xplore not accessed
(paywall). Extraction only; no new science.

## (a) Mechanism: PA-aware IR via sampling (joint IR/PA)

- Standard split: IR reconciles the full N-symbol key x, then PA hashes
  away Eve's info (syndrome z + side info E). Paper's point: PA discards
  redundancy anyway, so IR need not reconcile all of x.
- SC decoder: reconcile only a subset x_S, |S| = N−M, feed x_S into PA.
  Final key length is *identical* to full decode (Thm 1 proof:
  H(x_S)−I(x_S;E,z) = H(x)−I(x;E,z)), while P(success) can only rise
  (full-decode success ⊆ subset success). Hence SKR_SC ≥ SKR_FC.
- MSC decoder: K candidate subsets; a belief-propagation decoder emits
  the most-likely-correct one (Cor. 2: MSC ≥ any single SC).
- Spirit: "decoding only the systematic bits" of classical coding.

## (b) Conditions + claimed savings (quoted numbers)

- Thm 1 needs both: (i) complement submatrix H_S̄ (M×M) is **full rank**;
  (ii) raw symbols x_i are **conditionally independent given Eve info E**.
- Enabling construction: Block-MDS QC-LDPC — every γ×γ block-lifted
  square submatrix of H is full-rank. Recipe: girth-(2γ+2) QC-LDPC +
  gcd(f_τ(x), x^z−1)=1 checks; with prime lift z + Vandermonde scaling
  S, field size scales only linearly with κ (Thm 5).
- Sims (8-ary symmetric channel, codes ≈ length 2000, rates 1/4–2/5):
  MSC cuts IR failure probability by "**about 0.25 orders of
  magnitude**" (Fig. 1, low noise); high-noise SKR: C1 0.3913→**0.4832**
  (+23%, p=0.275), C2 0.8883→**0.9679** (+9%, p=0.2), C3 0.4114→**0.45**
  (+9%, p=0.28).

## (c) Applicability to our setting (n=256, 64-bit tag, f target ≤1.3)

- Fit: offers "f need not be pushed to 1.0" headroom — a subset-success
  at f≈1.15–1.45 could bank the same final key as a failed full decode,
  softening the S2 FER≤5% gate at fixed leakage.
- Misfits (3): demo rates are 0.2–0.4, ours is 0.89–0.91 (at rate 0.9,
  S = N−M is still 90% of symbols — gain mechanism unproven there);
  lengths ≈2000 vs our n=256 (64-bit tag proportionally heavier);
  cond.-independence given E is untested on Jan-21 correlated errors.
- Verdict: promising relaxation, not a drop-in; needs a rate-0.9,
  n=256 synthetic check before any claim.

## (d) What adoption would change for S2/S3 (later, DECIDE only)

- S2: add Block-MDS/full-rank-complement constraint to the PEG
  construction arm (interacts with the d_min/short-cycle controls);
  redefine the gate as subset-success FER at fixed f.
- S3: accounting change — success event redefined, final-key-length
  equality re-proven under our leak/tag bookkeeping; undetected-error
  isolation must cover partial decoding. Full DECIDE prereg required.
- S1 (DE ensemble optimization): unchanged.

## (e) Citation + retrieval path

- Citation: see header (ITW 2024, DOI above). Read: arXiv:2403.00192
  full text via ar5iv HTML (abstract, §§I–V, Thms 1/3/5, Tables I–II,
  Fig. 1 caption, refs); found via arXiv API query 2026-09-19/20.
  Web search was unavailable (tool-cancelled ×2), sciverse MCP unused
  (retrieval via arXiv path succeeded first).

## (f) Unread / unretrieved (explicit)

- ITW 2024 published-version deltas vs arXiv preprint: **unread**
  (no IEEE access; numbers above are preprint's).
- Fig. 1 curve values (no numeric table in text) and Appendix code
  parameters beyond C1/C2 partial: **not extracted**.
- No commit/push made; branch untouched (docs-only read).
