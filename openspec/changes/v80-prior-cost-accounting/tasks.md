# V80 Prior-Cost Accounting — Tasks

Planning-only change: no code/test edits in this task, no execution, no `.ttbin` access.
PC-T3/T4 need separate DECIDE grants before any execution; nothing is granted here.

- [ ] PC-T1 accounting-contract freeze (docs-only) — acceptance: `specs/v80-prior-cost-accounting/spec.md`
  written with all seven SHALLs (prior-cost disclosure; sacrifice exclusion + forgone-key reporting;
  key-eligible 200/276/364 with corrected-count certifiability; charging model + amortization basis;
  f_super/f_eff invariance; estimator estimand + `K_B` auditability; claim ceiling), each with a
  `#### Scenario:` block in house style; every number traces to `docs/V80_BASELINE_20260921.md` §§2–3
  or `docs/PRIOR_COST_ACCOUNTING_DECISION_20260921.md` §§A–C, or is marked `pending recompute` /
  `[TO BE MEASURED]` / `[BLOCKING]`. Blocked on: nothing (sources exist).
- [ ] PC-T2 S3-packet restatement (docs-only) — acceptance: the next S3 (or successor) packet draft
  restates key-eligible counts 200/276/364 (never 500/691/911), the sacrifice-the-sample DEFAULT with
  forgone key in the SKR numerator, per-source f on OWN H_MM, the 1M-led headline rule, and the
  disclose-the-statistic transcription-first precondition ([DEC]§E-1–5). Blocked on: S3 packet opening
  (not opened here).
- [ ] PC-T3 corrected-estimator re-run packet (DECIDE prereg, docs-only here) — acceptance: a prereg
  draft exists requiring persistence of minimum `K_B_train` (occupied B columns in TRAIN `N_ab`;
  recommended +`p_b` vector; ideal sparse `N_ab`, which also unblocks X1 1M/1.5M bundles) WITHOUT
  changing the frozen `h_full_f03` estimator, with the 60/20/20 split realization frozen, a `K_B`-only
  cost note (~5–15 min precedent, verification §T3), and explicit Pre-EXECUTE + grant + Pre-RESULT gates;
  execution NOT authorized by this task. Blocked on: user grant + Pre-EXECUTE (DECIDE track).
- [ ] PC-T4 transcription + amortization basis definition (docs-only, BEFORE any disclose-the-statistic use)
  — acceptance: a written definition of total transcription (bits disclosed, encoding, precision,
  public-message protocol for the real C03 1024-bin histogram) and amortization basis (per-block vs
  per-batch, batch size), from which the per-block 36 b charge or the amortized 36/200≈0.18 b /
  36/364≈0.099 b figure is re-derived; until then the m≤201 consequence may only be cited as a
  per-block-model conditional. Blocked on: method owner defining the public-message protocol [BLOCKING].
- [ ] PC-T5 N_req full-precision recompute confirmation (read-only arithmetic, main-thread command) —
  acceptance: the baseline-§3 commands (`.venv/bin/python -c` with H = 0.8036079281174853/m = 201,
  H = 0.8289616869054485/m = 207, H = 0.8345846048587662/m = 208, plus m = 200/199 rows; counts
  `(2000-1200)//4,(2767-1660)//4,(3645-2187)//4`) executed by an authorized party and the values
  15487/2700/1754 (+ 2051/309/262, 1098/274/236) confirmed or corrected; until then all N_req citations
  carry `pending recompute`. NOT executed in this task (no-execution constraint). Blocked on: authorized
  execution grant.
- [ ] PC-T6 main-thread governance close-out (decision, not execution) — acceptance: main thread records
  explicit waiver-or-acceptance of this change for the §B/§C decisions (baseline §0.2-D1), plus formal
  F-3 signature and tolerance confirmation (baseline §0.2/§7-2/7-3) — or leaves them OPEN with named owners.
  Blocked on: user signature.
