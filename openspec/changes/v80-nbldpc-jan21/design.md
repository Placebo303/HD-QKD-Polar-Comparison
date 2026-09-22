# V80 NB-LDPC Jan-21 Restart — Design

Sources: `docs/research_cycles/V80-NBLDPC-JAN21/PROGRAM_PLAN.md`,
`docs/research_cycles/V80-NBLDPC-JAN21/S0_RESULT.md`,
`docs/research_cycles/V80-NBLDPC-JAN21/LITERATURE_QPRIOR.md`,
`docs/decision-log.md:4435-4436`. Condensation only; no new numbers.

## S0 evidence summary (GO)

- Per-source H (V25 M1 holdout): 1M 0.807 / 1p5M 0.827 / 2M 0.828 (C03 pooled δ;
  C04/C05 identical; QSC/V17-product 3.2–3.5 shown for contrast only).
- F03 factorization closed: L1=0.025 + L2=0.795 = 0.820, chain-rule err ≤ 5e-9.
- V49 TRAIN/VAL/HOLD all nine totals ≤ 1.0 (max 0.86246, 2M VAL; margin ≥ 0.13);
  TRAIN→HOLD drift +0.0433 / +0.0317 / +0.0204. G1 PASS, no source narrowed.
- V19 binary: 500/500, f≈4.17 on declared 0.55 independence constant (synthetic,
  not conditional); sizing uses empirical 0.80–0.86 only, never averaged.
- R3: 8284/8412 exact, 128 iteration_limit fails, 0 mismatch
  (1p5M 2729/2767, 1M 1970/2000, 2M 3585/3645).
- V8/V26 basis is method-only (λ row-0.75, DET 0.069, EEff 1.053), not GF(1024).
- Ban carried: three-shift-cyclic GF(32) mothers excluded (d_min ≤ 2;
  303 duplicate projective classes, 1107 proportional pairs).
- Conflicts disposed: V70R1 sessions are Jan-23/Jan-07 pools (out-of-scope);
  v49_block is S0-relevant Jan-21 evidence (block NLL ≈0.82/0.89 corroborates scale).

## Frozen design numbers (S0 §3)

- n=256, f=1.3, 64-bit additive tag, gross=Â·10·n=1536 (Â=0.6).
- Formula: m=ceil(f·n·H/10), leak_total=10·m+64, rate=1−m/n.
- Nominal H=0.80 → m=27, rate 0.895, leak 334, net 1202.
- Per-source HOLD maxima (0.84434 / 0.85724 / 0.85297) → m=29, rate 0.887,
  leak 354, net 1182.
- m-grid 24–31 → rates 0.906–0.879; covers m=29; nominal and worst-case inside 0.88–0.92.
- V19-0.55 row (m=19, net 1282) is reference-only.

## S1 design essentials (freeze)

- Kernel: `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v26_mcde.py`
  `run_mcde_posterior` (unchanged).
- Config: inner screen 4000 samples / 60 iters + confirm 16000 / 100;
  outer DE simplex K≤4 / min_weight 0.05.
- dv searched {2,3,4,5,8,13,20}, ceiling 40 + BOUND_HIT rule.
- m-grid 24–31 @ n=256 (rates 0.906–0.879).
- Gate: f_ens ≤ 1.15/arm with f_ens = max_i formula + flip rule (secondary beats
  primary by >0.05 on ≥2 grid points incl. m27/m29).
- Budgets: 600 DE + 12 setup calls (420/180 primary/secondary split);
  wall 3600 s, per-call 300 s, RSS 4 GiB, 1 proc, no-retry.
- Tests: T0/T1.
- Bias lines: 4k/16k downscale, TRAIN-vs-HOLD, Mitra-channel mismatch.
- Auth: freeze consumes nothing; execution needs explicit grant + Pre-EXECUTE + Pre-RESULT.
- Tasks S1-T1..T6 per freeze.

## Q-architecture (per q-prior)

- PRIMARY: GF(32)²-layered (F03; L1 λ={2:1} fixed; L2 optimized).
- SECONDARY: direct-q1024 (≤30% effort).
- TERTIARY: a=3–4 refinements OFF (deferred).
- Mitra basis: key rate peaks interior at small a=3–4; JRDO objective (1−E)R
  embraces FER≈5%; channel-matched design required (BIAWGN degrees worse than
  regular VN-3 on QKD channel); V26 F03-GF32+GF32@f=1.3 30/30 narrow pass is
  isomorphic to the Mitra scheme. dv_max discrepancy (Mitra VN 2–5 vs program
  ceiling 40) flagged for S1-freeze. IEEE-11440984 paywalled (S2S 429) →
  nice-to-have (Kasai in-repo + R11 staged success cover rate-adaptivity).

## Fallback structure

- If direct-q1024 DE fails to converge at rate≈0.9 (V14 historical risk, noted as
  different-channel evidence), downgrade to GF(32)²-layered per Mitra dimension
  mapping and repeat once (pre-registered retreat, not ad-hoc patch).

## F-conflict slots (frozen for S1 resolution)

- dv-bound (ceiling 40 + BOUND_HIT vs Mitra VN 2–5 range).
- Flip rule (secondary-over-primary promotion threshold).
- L1-reopen (whether L1 λ={2:1} stays fixed).
- IEEE-nice-to-have (11440984 if access opens).
