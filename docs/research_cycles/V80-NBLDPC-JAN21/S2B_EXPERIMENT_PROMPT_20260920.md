# S2b Operator Prompt (2026-09-20) — companion to G-S2B packet (NOT a grant)

- Track EXPLORE synthetic; branch `formal-ir-v72p1-addendum-clean`; no switch/commit/push. Run ONLY on fresh explicit grant + Pre-EXECUTE Q0–Q6.
- Arm: single S2b. Constructor `construct_l2(seed=2026092001)` (FIXED v10_peg); assert `four_cycles==0` else STOP; λ={2:1} unchanged.
- Channel/prior (Option B): sampler `qsc_pair_sampler(p=0.081)` + decoder `qber=0.081`, `max_iter=300`. Both p* — never mix.
- Frames: seeds `2026097001+idx`, idx=0..239 (idx=4g+f); 60 groups × 4; group rule any-frame-fail⇒fail (`exact_match is True`); rg-absence re-check at Pre-EXECUTE.
- Gates (AND): (a) FER=fails/60 ≤5% (≤3/60), early-stop at 4th group fail; (b) f_super=1044/852.544≈1.2246 ≤1.3 (budget mapping, measured D_blind). Report f_L2≈1.1376 informational.
- Budgets: wall ≤3600 s; per-decode 300 s; RSS <4 GiB; ≤1 `--resume-from` for wall-partial ONLY; terminal FAIL not resumable.
- Root: fresh `workspace/s2b_<uuid8>` (UUID + absence proven at Pre-EXECUTE); never touch old roots, `results/`, `outputs_comparison/`.
- STOP on any science-input change. No L1/S3/dv/stopping-rule side quests. D_blind NEVER-ASSUME-ZERO + sensitivity line mandatory.
- Deliver: `S2B_RESULT_20260920.md` + `rows.json` + `group_accounting.csv` with B-limitation statement. Return deltas + verdict IDs only.
