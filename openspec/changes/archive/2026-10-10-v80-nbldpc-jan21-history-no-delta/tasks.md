# V80 NB-LDPC Jan-21 Restart — Tasks

Record-only change: no code/test edits in this task. S1-T4..T6 and S3 need
explicit grants before execution.

- [x] S0 evidence review (GO, all sources 1M/1p5M/2M named) — acceptance: record
  `docs/research_cycles/V80-NBLDPC-JAN21/S0_RESULT.md` reviewed zero-diffs, gates hold.
- [ ] S1-T1 readiness record — acceptance: readiness record written, budget/command
  frozen, nothing executed.
- [ ] S1-T2 runner — acceptance: runner built on unchanged V26 kernel, T0/T1 pass.
- [ ] S1-T3 profile-only — acceptance: profile-only run within budget, no DE consumed.
- [ ] S1-T4..T6 gated execution (needs explicit grant + Pre-EXECUTE) — acceptance:
  f_ens ≤ 1.15/arm gate adjudicated per arm incl. flip rule.
- [ ] S2 PEG + FER ≤ 5% (ban enforced) — acceptance: PEG/improved-PEG construction,
  three-shift-cyclic mothers excluded, synthetic FER ≤ 5% at efficiency ≤ 1.3.
- [ ] S3 Jan-21 DECIDE prereg (after S2) — acceptance: separate prereg written and
  authorized before any real-data execution.
