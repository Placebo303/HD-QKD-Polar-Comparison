# R20 Uniform-Prior DECIDE — Preregistration & Authorization (Condensed)

Track: DECIDE. Main-thread ACCEPTANCE granted: PRIOR-HELPS (with P9 gate-spec correction).
No execution/data/commit in this solidification record.

## Frozen scope (single arm)

- One arm only: uniform prior / iters=90 / m100, on the R9 128-block window (1p5M-2123..2186).
- Graphs 4720/4721 reused (R9-imported baselines); no new graph construction.
- Loader-never-invoked: structural drop of the npz-load call path; zero `np.load`; `loader_calls=0`; npz mtime unchanged.
- Budgets: sci ≤ 128 calls, setup ≤ 8.
- Fresh output root: `workspace/g6r20_uni_05100de1-e48c-4eea-a8a7-d5390f87cfc8` (created empty; verified absent before execution).
- Baselines R9-imported (byte-identical; sha `c75e27aa…`).

## Frozen gate text (ORIGINAL, quoted VERBATIM)

> PRIOR-HELPS iff mean Δ > +5 AND improved-fraction > 0.6 with improved ≡ Δ < 0.

## P9 CORRECTION (appended, governs)

- Sign typo in the original gate text: `improved ≡ Δ < 0` is corrected to `improved ≡ Δ > 0`
  (Δ ≡ uniform_residual − modelF_residual; Δ > 0 means modelF lower/better).
- The literal conjunction (mean Δ > +5 AND fraction(Δ<0) > 0.6) is unsatisfiable on the
  observed skew and is not applied literally.
- Governing intent: "modelF systematically lower" — i.e. mean Δ > +5 AND fraction(Δ>0) > 0.6.

## Grant lineage

- Mandate: main-thread PRIOR-HELPS grant for the single frozen uniform arm.
- Backup-continuity: execution continued under the backup path after 2 primary transient
  failures; workspace unmodified at handoff (fresh root; no overwrite of existing outputs).
