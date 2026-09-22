# D19 L2 Finite-Ensemble Validation — EXPLORE log (append-only)

- Authority: `.workbuddy/tasks/D19_L2_FINITE_ENSEMBLE_VALIDATION_READINESS_R1_TASK_PACKET.md`
  (§§1–11, §10 STOP + §11 return).
- Track: documentation-only (no code, no execution, no repair, no seed change,
  no root creation, no commit/push).
- Repo: `/mnt/d/Code/HD-QKD_Polar_Comparison`, branch
  `formal-ir-v72p1-addendum-clean` (do not switch; no commit/push in this call).
- This is the single append-only log root for D19. Detail record:
  `READINESS_R1.md` in this directory.
- Predecessor pointer: `docs/research_cycles/V72P2D18-L2ENSEMBLE/EXPLORATION_LOG.md`
  (D18 accepted `D18_L2_DE_SWEEP_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`;
  D19 validates the single winner `lam_d2_0.20_d3_0.80` against DV3, no
  family reopening).
- This call (D19 close-docs): documentation-only close (two new record files
  in this directory, one pointer append to the D18 log, D19 OpenSpec
  `tasks.md` F03–F10 checkbox update). No code, no execution, no
  decoder/DE/scientific calls, no staging/commits, no push.

## 2026-09-16 — D19 readiness R1 close (STOP, no execution)

### Authorization boundary

- This call performed no code edit, no D19 execution, no decoder/DE or
  scientific call, no root creation, no commit, no push.
- The frozen ≤192-call paired finite-ensemble batch remains unauthorized. It
  requires one later explicit user grant plus Pre-EXECUTE, which cannot issue
  against the as-frozen seed set (§STOP below). No authorization was granted
  by readiness or by D19-BLOCKER-REVIEW.
- No-execution-authorized statement: **no D19 execution is authorized by this
  close; the future root remains absent and the frozen command remains an
  unauthorized string.**

### F01–F02 evidence (trusted VERIFIED, do not rerun)

- F01: OpenSpec freeze (proposal/design/tasks/delta spec, packet §§1–7
  verbatim in effect): route acceptance of the single D18 winner
  `lam_d2_0.20_d3_0.80` with near-tie ceiling (0.15/0.20/0.25 identical DE
  thresholds, 0.20 by frozen max-check-degree then ID tie-break; no
  family reopening, no optimality claim).
- F02: four cells independently rederived by hand from the D9
  largest-remainder rule + socket balance (n128 DV3 `3^128`/E384/`4^86+5^8`;
  n128 L020 `2^35+3^93`/E349/`3^27+4^67`; n256 DV3 `3^256`/E768/`4^172+5^16`;
  n256 L020 `2^70+3^186`/E698/`3^54+4^134`), VERIFIED no mismatch; exact
  rational realized deviations (`lambda2 = 70/349` +1/1745, `L2 = 35/128`
  +1/1408, check `rho`/`R` fractions per arm) + `delta_L2 =
  0.44915511536562214` recompute recorded (`design.md` §§2.2–2.4).

### F03–F08 implementation + STOP

- F03–F08 artifacts exist (thin D19 module importing D10-R2/D16 helpers;
  cells/seeds/paired plan/admissions/exact-only gates/conditional dispatch/
  terminals/writer/verifier; runner with `--profile-only`/`--d19-batch`/
  default-false `--execution-authorized`/fresh-root refusal/read-only
  `--verify`; focused tests; PROFILE_ONLY 24-graph/192-plan zero-call
  profile; frozen future root/command/budgets) but readiness is blocked:
  frozen n256 DV3 seed `2026094408` deterministically fails construction
  (`construction_failed`, `no eligible check placement at variable 255
  socket 2`), 23/24 cells admit, packet forbids replacement/search and
  mandates engineering-block. Tests assert ENGINEERING_BLOCKED naming 4408
  with zero n256 calls.
- Terminal: STOP (`D19_L2_FINITE_ENGINEERING_BLOCKED` path); the §11 ready
  marker is NOT returned.

### D19-BLOCKER-REVIEW verdict/findings (trusted VERIFIED)

- EVIDENCE_ACCESS VERIFIED, VERDICT PASS — blocker confirmed, correctly
  retained. Reviewer repro (own, twice each) deterministic; constructor `is`
  r2 zero-diff vs HEAD; arithmetic confirmed (not a table defect); seeds
  exact with no replacement mechanism; 33/33 new tests (reviewer rerun own
  basetemp); PROFILE_ONLY 24 attempted/23 admitted/plan 192/counters 0/root
  absent; refusal rc2 no-write; root absent; D19 files untracked-additive;
  no commit/push.
- Adjudication: genuine frozen-seed × accepted-constructor STOP, not fixable
  within readiness scope. ONE decision pending: amend the frozen n256 DV3
  seed set under a new packet amendment (fresh disjointness proof +
  24-graph re-profile + re-review) OR formally accept terminal
  `D19_L2_FINITE_ENGINEERING_BLOCKED` as the D19 outcome. Readiness
  as-frozen is STOP, not READY.

Decoder/DE calls this call: 0. COMMIT_PUSH: none.

## 2026-09-18 — D19 finite-ensemble batch execution (EXPLORE HEAVY-cost, AMBIGUOUS)

- Track: EXPLORE (HEAVY-cost annotation, synthetic-diagnostic only).
- Authorization boundary: user grants ("你自己往前做决定并推进，我批准",
  "直接往下推进就可以了，我授权你") activating packet §9
  n128+mechanical-n256 arm sequence.
- E-cmd: `.venv/bin/python scripts/v72p2d19_finite_development.py --d19-batch --execution-authorized --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d19_l2_finite_ensemble_5f2b8c1d-7a3e-4f90-b6d4-8e1a2c3d4f5a6b`
  exit 0.
- Pre-EXECUTE: branch clean, F08 root absent-proven, focused tests 33/33 PASS.
- n128: 96/96 calls, M=19/48, M_g=[3,2,2,4,3,5], C=5/48, b=14, c=0,
  discord=14 → AMBIGUOUS (POSITIVE fails M<30, NEGATIVE fails M>16).
- undetected=0 isolated (never merged into success/FER); exact==syndrome_ok.
- n256: NOT entered, 0 calls; seed 4408 retained construction_failed, no
  replacement per frozen seed set.
- Budgets: 96/192 calls, 42/42 setup, 67.9s/1800s, 137.9MB/2GiB, 1-proc,
  no-retry, no violations.
- Terminal: D19_L2_FINITE_AMBIGUOUS.
- Batch-end review: reviewer-go PASS (B1-B7 recomputed match).
- Claim ceiling: synthetic-diagnostic only; no FER/leakage/SKR/optimality/
  route-closure claim.
- Zero real-data; results//outputs_comparison/ untouched; no commit/push.
- Note: n128 admission was 12/12 clean so 4408 profile-fail does not force
  ENGINEERING_BLOCKED under conditional n256-iff-POSITIVE dispatch.
