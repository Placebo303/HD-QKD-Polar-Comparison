# V80 S1 readiness (EXPLORE-readiness, NOT execution)

- Track: EXPLORE-readiness. ZERO scientific DE calls (no `run_mcde_posterior`
  invocation outside a raising stub; profile-only = plan arithmetic).
- Branch: `formal-ir-v72p1-addendum-clean` (verified `git branch --show-current`).
- Context read: `PROGRAM_PLAN.md` §S1 (V26 MC-DE reuse, concentrated rho,
  dv_max≤40, rate 0.88–0.92, GF(32)²-PRIMARY / q1024-SECONDARY) +
  `docs/decision-log.md:4435` (V80-S0 ACCEPTED GO) + `:4436` (V80 q-prior:
  PRIMARY GF(32)²-layered, SECONDARY direct-q1024).
- S1 execution (T4–T6) needs a separate explicit grant — NOT given here.
- Status: NOT accepted (reviewer checks at execution gate).

## S1r-record — artifacts

- This file: `docs/research_cycles/V80-NBLDPC-JAN21/S1_READINESS.md` (new;
  dir previously held only PROGRAM_PLAN.md, S0_RESULT.md,
  LITERATURE_QPRIOR.md).
- Runner (new, thin additive, kernel imported read-only, never edited):
  `comparison_bench/src/comparison_bench/formal_ir/v80_s1_mcde_runner.py`.
- Tests (new, FAKE only): `comparison_bench/tests/test_v80_s1_readiness.py`.
- Posteriors (new, additive, counts-only):
  `docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz` (100 KB).
- Exact venv command:
  `.venv/bin/python -m pytest comparison_bench/tests/test_v80_s1_readiness.py -p no:cacheprovider -q`
  → **36 passed** (`numpy 2.5.3`, `numba 0.67.0`; R2 re-run green).
  [2026-09-19 factual maintenance: 12→36 after F3 p_b-binding rework added
  4 pins (file-bound p_b / sampler-honors / absent-refuses / anchor-reverify);
  no science content changed.]

## S1r-seeds — picks + disjointness proof (R2: re-picked, collision fixed)

- S1 screen seeds = confirm seeds (set-equal overlap reuse) =
  `{2026094951, 2026094952}` (frozen in runner `SCREEN_SEEDS/CONFIRM_SEEDS`).
- R1 picks `{2026094501, 2026094502}` COLLIDED EXACTLY with frozen D19 n128
  block seeds `2026094501..4508` (packet
  `.workbuddy/tasks/D19_L2_FINITE_ENSEMBLE_VALIDATION_READINESS_R1_TASK_PACKET.md:43`
  + `openspec/changes/v72p2d19-l2-finite-ensemble-validation/tasks.md:15`
  `n128 blocks 2026094501..4508 / n256 4511..4518`; R1 rg scope missed them).
  Re-picked into the `20260949xx` hundred-block.
- Quoted absence proof for `2026094951/4952` (this call, `rg -l`, exit=1 =
  zero hits repo-wide across `comparison_bench/src + tests + docs +
  openspec + .workbuddy`): no file lists either seed. Per-path
  `20260949*` counts all exit=1 (zero hits): `comparison_bench/src`,
  `comparison_bench/tests`, `docs`, `openspec`, `.workbuddy`.
- Avoided namespaces (quoted hits, still in force): D18 `2026094301..4308`
  (D18 packet + `v72p2d18-.../tasks.md`); V26 `26101` (V26 run_01/run_02
  manifests + V26 gate docs); D19 graphs `2026094401..4412` + blocks
  `2026094501..4508/4511..4518` (D19 packet + D19 tasks); G6
  `4601/4602/4720/4721`, R7 `4701/4709/4711`, R11 `4722/4723`, R23
  `4801..4816/4831..4885` (`v72p2r23_scale.py`, r23/r7/g6 tests,
  R9 PREREG); CLI defaults `5001/8001/9001` (`run_v22*_de_gate.py`,
  `run_v23_protograph_scan.py` + tests). R17/R20/R21/R24 dirs carry no
  `202609*` seed literals (seeds live in the shared G6/R test files above).

## S1r-root — fresh-root pattern + absence proof

- Pattern: `workspace/s1_mcde_<uuid>`; picked UUID
  `07723233-e537-4a2e-857a-954e3a94d030`.
- Proof: `ls workspace/s1_mcde_07723233-...` →
  `No such file or directory`; `ls workspace/ | rg s1_mcde` empty (exit 1).
  Profile run re-checked absence after completion — root NEVER created.

## Frozen D-de config (transcribed, not redesigned) + hash

- Kernel `nonbinary_v26_mcde.py::run_mcde_posterior` + `target_rate_layer`
  (R=1−f·H/width) + `make_rho` (harmonic-exact two-element concentrated) +
  `build_gf_perm_table`; reuse by import.
- Inner screen `4000/60/1e-4/20`; confirm `16000/100/1e-4/20`. Outer DE:
  simplex weights, sparse support K≤4, min_weight 0.05, sum=1±1e-12,
  rho always via `make_rho`, polish OFF, workers=1.
- dv support `{2,3,4,5,8,13,20}`, ceiling 40 (BOUND_HIT armed, untriggered).
- Rate grid n=256, m 24–31 (rates 0.90625→0.87891). L1 fixed λ={2:1}; L2 searched.
- pop/gen frozen: PRIMARY pop10×gen14 (=140 slots), SECONDARY pop10×gen5 (=50).
- Split in code: PRIMARY 420 / SECONDARY 180 / 600 total + 12 setup; no-retry
  (`NO_RETRY=True`); overlap set-equal (confirm seeds ⊆ screen seeds);
  resource gate → `resource_blocked` terminal, never silent resume.
- Ban in code: `assert_no_construction` — degree profiles ONLY, fail closed.
- Budgets in code: wall ≤3600 total, per-call ≤300 s, RSS <4 GiB, 1 CPU.
- **config-hash: `57e5da443c99f5c52615c43f2d819b22d1b40eda2f7d14ba762d2b705064a684`**
  (R2: recomputed after seed re-pick; sha256 over frozen config incl. seeds;
  asserted in tests).

## S1r-gamma — BUILT from counts only (R2 completion)

Built with the frozen `nonbinary_v26_channel.ChannelAdapter` (read-only
import, kernel never edited; pure column-normalization per V26 Table
pattern — no fitting, no parquet/symbol payloads, no `run_mcde_posterior`):

- Source: `.../nbldpc_v25_20260818/run_04/channel_counts.npz` train-count
  keys (`*_N_ab_train`, (1024,1024) float64 per source; key-listing +
  shape/sum only before load) + F03 definition (`nonbinary_v25_gate.py:53`:
  L1 gf32 bits 9..5 / L2 gf32 bits 4..0, natural MSB→LSB) + targets
  `factorization_layers.csv` (`F03:L01_natural` rows).
- Artifact (new, additive, 100 KB compressed):
  `docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz` — per source
  (`1M/1p5M/2M` kept independent, never merged): `γ_1 = P(U1|B)` (32,1024),
  `γ_2 = P(U2|B,U1)` (32,32,1024, joint÷marginal; `P(U1|B)=0` cells take the
  frozen `posterior_rows` fallback delta-at-0), plus scalar `H_L1/H_L2`.
- Verification (derived layer entropies vs F03 targets, ±0.02 gate):
  1M `H=(0.02428055, 0.77675728)` Δ=(3.2e-09, 1.9e-09);
  1p5M `H=(0.02519950, 0.80036655)` Δ=(3.1e-09, 4.7e-09);
  2M `H=(0.02566205, 0.80690067)` Δ=(1.2e-09, 3.1e-09) — ALL PASS.
  Normalization: γ_1 colsums=1, γ_2 cond-rowsums=1 (all three sources).
- Runner still takes γ_i as injected `channel_sampler` (fake in tests);
  real binding deferred to execution Pre-EXECUTE, now backed by this file.

## S1r-profile — dry pass (0 scientific DE; R2 re-run with new seeds)

`--profile-only` output (deterministic, sampler never invoked):

| arm | screen | confirm | subtotal |
|---|---|---|---|
| PRIMARY (140 slots) | 280 (2 seeds) | 140 (reuse seed) | 420 = cap |
| SECONDARY (50 slots + 40 rate-winners) | 100 (2 seeds) | 80 (2 reuse seeds) | 180 = cap |
| SETUP (8 rate targets + 2 perm tables + hash + plan check) | — | — | 12 |
| **Total** | 380 | 220 | **600 + 12** |

- Node-update plan: 380×4000×60 + 220×16000×5 (confirm at early-stop
  expectation 5; hard cap stays max_iter=100) = **108,800,000 ≈ 109M**.
- Wall plan: 380×4 s + 220×8 s = **3280 s ≤ 3600** (means; per-call 300 s hard
  gate + `resource_blocked` on overrun).
- Refusals rc=2 (5 cases ≥3 required): default `--execution-authorized=false`
  (verified live rc=2 pre-anything); existing root; invalid rho;
  unnormalized lambda; dv bound violation (all in tests).
- `scientific_de_calls: 0` (kernel stubbed to raise in the profile test).
- R2 re-verified live: plan seeds = `{2026094951, 2026094952}` (screen +
  confirm), totals `PRIMARY 420 / SECONDARY 180 / de 600 / setup 12`,
  `node_updates 108800000`, `wall_s 3280.0`, hash `57e5da44...684`.

## S1r-runner / S1r-tests / S1r-calls

- Runner path above; `main()` refuses any non-`--profile-only` path with rc2.
- Tests: T0 2 (pure helpers + validate-ok) + T1 3 (hash + replay + fake
  complete path) + ban 1 + refusal/no-overwrite 6 = **12/12 PASS** (R2 re-run
  green after seed re-pick + hash update).
  [2026-09-19 factual maintenance: suite now **36/36 PASS** (12 readiness +
  8 execute-path + 7 sampler-binding + 3 Q0 + 2 Q5 + 4 F3 p_b-binding pins);
  no science content changed.]
- **S1r-calls = 0 scientific DE calls.** No real-data/pool/parquet reads
  (counts-npz/CSV/JSON text only: `channel_counts.npz` train keys,
  `factorization_layers.csv`, manifests); frozen kernel untouched; no writes
  to `results/`, `outputs_comparison/`, or pools; no commit/push; execution
  scratch root never created (`gamma_f03.npz` lives in the readiness dir).

## S1r-checkpoint addendum (2026-09-19, factual lines only, no science change)

- Checkpoint-per-eval: every completed DE evaluation rewrites
  `manifest.json` + `rows.json` to the scratch root (same schema +
  `completed_identities` seen-set persisted verbatim + `ledger` counters +
  `resume` snapshot with RNG/cur/pop/slots/indices + `wall_start`;
  overwrite-in-place, single writer).
- `--resume-from <partial-root>` (default OFF): fresh run (no flag) requires
  root ABSENT; resume run (flag given) loads + validates the partial
  (config-hash == `57e5da44…684` + seeds/identities/budgets frozen + ledger
  tallies + completed ⊆ rows, no error rows) BEFORE any DE call, then
  continues ONLY missing identities (overlap-dedupe from persisted seen-set);
  same terminal/gate/verify on completion; invalid partial refuses rc2 with
  zero calls; NEVER silent auto-resume.
- Root-exists matrix (fail-closed): absent+no-flag → fresh run;
  absent+flag → refuse (nothing to resume); present-valid-partial+flag →
  resume; present+no-flag → refuse (existing); present-invalid → refuse
  always (with or without flag).
- Tests FAKE-only deterministic: **40/40 PASS** (36 prior green unchanged +
  4 checkpoint/resume: per-eval presence + half two-phase byte-identical mod
  `elapsed_s`/`provenance.root` + matrix + invalid-refusals); ledger
  continuity (resumed charges only missing, totals 420/180/600/12);
  profile-only still `scientific_de_calls: 0`, root absent.

## S1r-resume odd-N addendum (2026-09-19, factual lines only, no science change)

- (a) Mid-trial persist/skip semantics (code only, `v80_s1_mcde_runner.py`):
  `_snap`/`_flush` carry `mid_lam`/`mid_fits`/`mid_si`; the post-si=0
  screen flush persists `(lam, [fit0], 1)`; trial-boundary flushes carry
  `(None, None, None)` exactly as before. Resume with a mid-trial snapshot
  SKIPS `propose_trial` (no RNG consumption), reuses the persisted `lam`
  (rho re-derived via `make_rho`, si=0 fit via the cached persisted row),
  and runs ONLY the missing si=1. Confirm/done/error/overrun paths
  unchanged; old partials without mid keys resume as trial-boundary.
- (b) Odd-N equivalence verified (FAKE only, zero production calls):
  N=1/3/51/421 plus operator-picked N=451 (odd SECONDARY-screen mid-trial:
  420 PRIMARY + 31) and N=350 (PRIMARY confirm boundary: 280 screen + 70
  confirm) — each: `len(calls2)==600−N`, ledger `420/180/600/12`,
  rows+manifest byte-identical mod `elapsed_s`/`provenance.root`,
  `verify.ok` on both single-shot (m1) and resumed (m2) manifests.
  Even-N (e.g. N=300) still green; `m1 verify.ok` assert added alongside
  the existing m2 check.
- Suite: **41 passed + 6 subtests passed** (`test_v80_s1_readiness.py`
  full file); profile-only `scientific_de_calls: 0`, root absent;
  config-hash kept `57e5da44…684` (re-frozen, no drift). Zero scientific
  DE calls; changed files: runner + its test only.
- [2026-09-19 wall-restart delta: resume opens a fresh 3600s wall window at resume time (DE ledger 600+12 continues verbatim, never reset/double-charged); manifest carries append-only `wall_windows` (fresh=1 entry, each resume appends; pre-delta partials synthesize one from `wall_start`); suite **45 passed + 6 subtests passed**, profile-only `scientific_de_calls: 0` with root absent, hash kept `57e5da44…684`; zero scientific DE calls; changed files: runner + its test only.]
