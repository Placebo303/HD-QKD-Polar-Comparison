# Proposal — D17 Current-Channel Asymptotic-to-Finite Scaling (Readiness R1)

- Authority: `.workbuddy/tasks/D17_ASYMPTOTIC_FINITE_SCALING_READINESS_R1_TASK_PACKET.md`
  (§§1–§8, sole authority). Track: implementation/readiness now (OpenSpec-only);
  all future scientific work (`DE` batch, scaling fit, `D16` run) is `EXPLORE`.
- Repo: `/mnt/d/Code/HD-QKD_Polar_Comparison`, branch
  `formal-ir-v72p1-addendum-clean` (do not switch; no commit/push in this call).
- This call (D01, planner, no production code): predecessor audit `A01–A05` +
  OpenSpec freeze. Zero `DE`/decoder calls, no roots created, no commits, no push.
- Predecessor: `D16_MATCHED_BACKOFF_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`
  (readiness valid; `D16` Batch A1 authorization withdrawn — `D16` is held-out
  validation, never the next executable gate; `D16` log:37-42).

## Goal

Freeze, before any new execution, the complete readiness contract that maps
current-channel asymptotic `MC-DE` thresholds to finite-length block-failure
predictions on the exact Model-F candidate channel: exact channel identity,
`DE`-transfer boundary, eligible finite dataset with compatibility classes,
`D16` holdout lock, a bounded non-adaptive three-profile `DE` grid, the
predeclared scaling law with identifiability/uncertainty rules, and the
outcome-blank `D16` prediction schema. The scaling law is an empirical
calibration for this channel/decoder family, not a universal theorem; `DE`
convergence is not finite-code usability.

## Non-Goals

No `DE`/decoder execution or authorization; no new `DE` kernel (reuse V26 +
`D9` adapter); no threshold fit from finite data (`delta_DE` comes only from
the reviewed current-channel `DE` result); no `D16` execution, `FER`
qualification, leakage/`SKR`, real-data, `D7-H` revival, route closure,
publication or optimality claim; no change to any predecessor root, frozen
baseline, `AGENTS.md`, or decision log.

## Impact Scope

- Added only: `openspec/changes/v72p2d17-asymptotic-finite-scaling/`
  (`proposal.md`, `design.md`, `tasks.md`, `specs/de-scaling/spec.md`).
- Read-only inputs (never modified): rate-mother prior chain + `R`-audit
  entropy record, `D8–D16` cycle docs/logs, `V25/V26/V27` + `D8/D9` `DE`
  artifacts, `D10–D15` result roots (`CSV`/`JSON` reads only), `D16` plan/test
  files (held-out identities recorded, never used).
- Forbidden this call: code/scripts/tests/roots/`AGENTS.md`/decision-log edits,
  commits, pushes, branch switch.

## Acceptance Criteria

1. `A01`: channel verdict recorded exact-or-`STOP`, with every mismatch named;
   incompatible evidence never combined.
2. `A02`: `DE` inventory by channel/layer/profile/rate/population/iterations/
   metric, with exact transfer / no-transfer statements for V26 f1.3 conclusions.
3. `A03`: finite table from `D10–D15` roots with recomputed spot `delta`,
   graph clusters + root identity preserved.
4. `A04`: every observation in exactly one class
   (fit / validation-only / descriptive-only); `APP`/joint excluded from
   single-layer fit; `L2 ORACLE` only in the true-conditioned `L2` model.
5. `A05`: `D16` inputs/seeds/root/command recorded, official root proven absent,
   banned seeds listed, fake-identity scratch locked out.
6. `B-grid`: three frozen profiles on the exact current channel,
   `delta`-parameterized, `rho` from exact rate, bounded coarse-plus-confirmation
   points + fixed seeds, convergence rule, command/root/budgets frozen;
   non-adaptive (no outcome-driven extension/binary search).
7. `D01` artifacts carry equations, units, eligibility, identifiability logic,
   uncertainty method, holdout schema with blank fields, residual separation,
   rank/cycle/schedule post-prediction measurement, and the claim ceiling.
8. Zero scientific calls; `DE`/decoder counters 0; no commit/push.

## A01 channel verdict: EXACT (no STOP)

Exact Model-F candidate channel shared by `D8–D16` (proof chain:
`N_DISCRIMINATOR_PREREG_R1.md` §1 + `D14` log R §40 + `entropy.json` +
`D16/design.md` §5 + `D15` log pre-dispatch §56-60):

- Generator: `p_f(Alice=1024,Bob=1024)`, `A=32*U1+U2`; estimator
  `prepare_model_f_prior_candidate`/`build_f_model_concentration`,
  `LAMBDA_STAR=137.3823795883263870`; floor `max(p,1e-300)` pre-`log2`,
  no renormalization; units bits/symbol; joint `7.5094403148357545`,
  `H_L1=4.286720430201375`, `H_L2=3.222719884634378`
  (`R`-recomputed `Δ≤1.8e-15`; `workspace/v72p2d14_rate_audit/20260914_r1/`).
- Decoder prior chain: `P1=sum_u2 P_F` (`marginalize_f_to_p1`),
  `P2=P_F/P1`; `L1` marginal input `q@P` (`get_l1_app_prior_l2`); `L2` oracle
  `oracle_l2_prior` → `get_conditional_posterior_l2` (true-`U1` conditioning,
  diagnostic-only); decoder floor `_floor_renorm(DECODER_FLOOR=1e-15)` with
  renormalization; `GF32/poly37`; row-layered cold `max_iter=90`,
  `damping=1.0`; `CAL`-only artifact `workspace/v72p2d5_model_f_input/20260907_r1`
  (`cal_only:true`, `sha256:38e4bfba…6280d345`, unchanged pre/post `D14N/D15`).
- Recorded distinctions (not mismatches, no pooling violation):
  (i) row-rate base: `D8–D12` rows derived from frozen `CE` constants
  (`CE_L1=3.814742/CE_L2=3.347605`, D4R2 outer-`F` TEST means) while `D14N+`
  rows derive from generator entropy — the generator/prior is unchanged
  (comparability statement, N-prereg §2), so all rows join one `delta` axis
  (`delta = 5m/n − H_l` with generator `H_l`);
  (ii) legacy per-cell-`lam` estimator (joint `9.9996/L1 5.0/L2 5.0) REJECTED,
  confined to pre-`D14` diagnostics + the `D5-G2/X4` legacy-prior caveat
  (excluded from `D17` evidence);
  (iii) `V25/V26/V27` real-data empirical-timestamp channel (per-source `H1/H2`,
  `f=1.3`, block-lens `1024–8192`) is a different domain — kernel-reuse only;
  (iv) `D8/D9` `DE` rate base (`CE H_L1`, n64-implied `R`) differs from the
  `D17` `DE` rate base (generator `H`, n128-reference `m`) — `D9` numbers do not
  transfer as thresholds (see `A02`).

## A02 DE-transfer table (summary; full map in `design.md` §4)

| Source | Channel / rate base | Verdict for D17 |
|---|---|---|
| V26 kernel (A02/F03 `GF32+GF32` `MC-DE`) | Empirical-timestamp, `f=1.3` | Reuse kernel only (via `D8-E02` decision); no numeric transfer |
| V25 factorization gate | Same empirical domain | Method precedent only |
| V27 finite-margin gate | Same empirical domain, source-adaptive budgets | Method precedent only |
| D8 sweep (126 calls, seeds `1601–03`, f1.2 `m59/R0.078125`, f1.0 `m49/R0.234375`) | Candidate chain, `CE` rate base | Descriptive context only; winner none stands; outcomes never reused as `DE` evidence |
| D9 calibration (96 calls, 8 seeds, pops `4000/16000`, `max_iter=60`, `tol=1e-4`, `streak=20`, `AUT_30`/`T_0.01`) | Candidate chain, `CE` rate base | Transfers: semantic map + equivalence ceiling (primitives `≤1.94e-16`; flooding↔row-layered and `DE`↔decoder-terminal non-equivalence), degree-realization rule, 8-seed stability methodology, `f1.0=BOUNDARY_DIAGNOSTIC` derivation method. Does NOT transfer: numeric thresholds/verdicts (`0.45 8/8+8/8` etc. — different rate base; f1.0 `d=3.828125` is generator-`delta −0.459`, trivially unconverged), candidate selection |

## A03 finite table (summary; full per-root table + `delta` recompute in `design.md` §3)

Roots (all six-file convention; `exact==syndrome` every row; `undetected 0`
everywhere; decoder `GF32/poly37` cold `90/1.0` unless noted):

- `D10-A1` (`d10_mixed_degree_l1_b2dd13e4`): n64 MIX-0.45 m59 `Δ+0.32265`
  `20/24 [7,7,6]`; n64 DV3 `1/24 [0,0,1]`; n128 MIX m118 `10/24 [5,2,3]`;
  n128 DV3 `0/24`; n256 undispatched. (`CE`-f1.2 rows, same generator chain.)
- `D10-R3` (`d10_r3_fresh_graph_scaling_4d39ed0e`): n128 MIX m118 `23/72`,
  DV3 `0/72`; n256 MIX m236 `Δ+0.32265` `29/72`, DV3 `0/72`. (Rows `m118/m236`
  provisional — `D02` confirms from manifest.)
- `D11` (`d11_forward_app_7c1878b5`): forward `APP` wide recovery (n128 joint
  `22/23`, n256 `28/29`; oracle `43/72`, `64/72`); `L1` replay `EQUAL R3`.
- `D12` (`d12_finite_l1_degree_94fb9d22`, `summary.json` re-read this call):
  n128 m118 `Δ+0.32265` L045 `26/72`, L050 `39/72`, L055 `42/72`;
  n256 m236 L045 `33/72`, L050 `35/72`, L055 `46/72`. 432 calls.
- `D13` (`d13_l055_decoder_ladder_5c41b416`): 56 `D12`-L055 failures replayed +
  168 ladder (`RL360`/damped/flooding360); rescues `3+1+0`; und `0`.
  Varied decoder → descriptive-only.
- `D14N` (`v72p2d14_discriminator/20260914_r1`, `summary.json` re-read this
  call): n128 L1 m110 `Δ+0.01015` L045 `3/72`, L055 `7/72`; `L2-APP` joint
  `7/72`; `L2-ORACLE` m104 `Δ+0.83978` `63/72 [11,11,10,9,12,10]`. 288 calls.
- `D15` (`d15_finite_margin_curve_8c1e4f2a`, `summary.json` re-read this call):
  n128 L045 m110/114/118 `0/6/19`; L055 `1/13/22`; `L2-ORACLE` m83/86/89
  `0/0/0`. 288 calls, terminal `MARGIN_CURVE_AMBIGUOUS`.
- Spot recompute (this call, by hand): L055 m118 `590/128=4.609375 −
  4.286720430201375 = 0.322654569798625` ✓; L2 m86 `430/128=3.359375 −
  3.222719884634378 = 0.136655115365622` ✓; `D14N` L1 m110 `550/128=4.296875
  − 4.286720430201375 = 0.010154569798625` ✓. (`D02` re-verifies all cells.)

## A04 compatibility classes

- FIT (single-layer only; graph clusters + root identity retained; exact
  binomial counts; never rows-as-graphs): `D15` all 9 cells; `D14N`
  L045/L055/`L2-ORACLE` (with leave-one-root-out sensitivity at `D02`);
  `D12` L045/L055 n128+n256 (`CE`-f1.2 rows, same generator chain — `D02`
  join-key check: `model_f_root` + estimator + decoder contract);
  `D10`-MIX/`R3`-MIX L045-profile cells (`D02` row confirmation).
- VALIDATION-ONLY: `D11` L1 replay (R3 duplicate — reproducibility, no double
  count); `D11` L2-ORACLE (pending true-conditioning + row audit at `D02`);
  `D16` (frozen predictions only, post-run falsification).
- DESCRIPTIVE-ONLY: non-`D17` profiles (`D10`/`R3`-DV3, `D12`-L050);
  all `APP`/joint outcomes (excluded from single-layer fit by rule);
  `D13` ladder; `D8/D9` `DE` numbers; `V25/V26/V27`; Wilson/paired intervals.
- `L2 ORACLE` enters ONLY the true-conditioned `L2` model.

## A05 D16 holdout lock

- Held-out cells (n128): L045 m125 (`2^62+3^63`, disclosed 625,
  `f=1.1390555039696448`, `Δ+0.596092069798625`); L055 m125 (`2^74+3^51`,
  same disclosure); L2-ORACLE m94 (`4^86+5^8`, disclosed 470,
  `f=1.1393714413428093`, `Δ+0.449155115365622`).
- Seeds (banned from fitting and `DE` tuning): graphs `2026094001..04` /
  `4005..08` / `4009..12`; blocks `2026094101..08`. No `APP`/transfer arm.
- Command (frozen, unauthorized):
  `.venv/bin/python scripts/v72p2d16_matched_backoff_development.py --d16-batch
  --execution-authorized --model-f-root workspace/v72p2d5_model_f_input/20260907_r1
  --out-root workspace/d16_matched_backoff_discriminator_b7c2d4e6-8f1a-4c3d-9e5b-2a4f6c8d0e1a`;
  budgets `96/22/900s/120s/<2GiB/1-proc`. Batch A1 authorization withdrawn.
- Root absent PROVEN this call: read of
  `workspace/d16_matched_backoff_discriminator_b7c2d4e6-8f1a-4c3d-9e5b-2a4f6c8d0e1a`
  → `File not found`.
- Contamination lock (found this call): `workspace/d16_align_20260915_a/`
  holds `D1606` fake-runner scratch (`test_d16_*` basetemps) whose
  `decoder_records.csv` rows carry real `D16` identities but FAKE outcomes
  (proof: wall `~1e-5 s`, iters `1`, all-`converged_exact`, test paths). These
  rows must never enter fitting, `DE` tuning, verification globs, or
  prediction (fail-closed seed-presence gate at `D02/D04`). This proposal
  records their existence and fake-proof; no outcome value is used.
- Banned-seed grep this call: hits only in `D16` packet/plan/module/tests/
  OpenSpec/readiness + the fake scratch above — zero presence in any fit/`DE`
  input (no `D17` code exists yet).

## B-grid freeze (part of D01; full tables in `design.md` §4)

n128-reference integer-`m` grid (exact rate `R=1−m/128`, `delta` from generator
loads `548.700215065776/412.508145233200` bits; `rho` derived from exact
`(n,m)` by the frozen `D9` concentrated floor/ceil rule — never legacy `CE`
labels):

- L1 L045 (nodes `71/57/E313`): `m = 106, 110, 114, 118, 122`
  (`Δ −0.14610/+0.01015/+0.16640/+0.32265/+0.47890`).
- L1 L055 (nodes `83/45/E301`): `m = 116, 119, 122, 124, 126`
  (`Δ +0.24453/+0.36172/+0.47890/+0.55703/+0.63515`; capped at `m126/R0.015625`,
  lowest positive n128-granularity rate — one-sided-high contingent predeclared).
- L2 DV3 true-conditioned (nodes `0/128/E384`): `m = 89, 94, 99, 104, 109`
  (`Δ +0.25384/+0.44916/+0.64447/+0.83978/+1.03509`).
- Per point: pops `{4000 coarse, 16000 confirmation/stability}`, seeds
  `2026094201..4208` (absence proven repo-wide this call: `20260942*` zero
  hits), V26 `max_iter=60/tol=1e-4/streak=20`; `3·5·8·2 = 240 DE` calls +
  setup `≤12`; wall `≤1200 s`, per-call `≤300 s`, `RSS <2 GiB`, 1 proc, no
  retry/resume/seed-search/adaptive. Convergence `S_pop=#{H60<1e-4}`;
  `delta_DE` = midpoint of the predeclared bracket pair at pop16000
  (edge/flag rules frozen in `design.md` §4; pop4000 = stability check).
  Trajectory summaries (`de_traces`-style) recorded per call; no
  `DE`↔row-layered trajectory claim beyond `D9` certified primitives.
- Future batch (absent, unauthorized): root
  `workspace/d17_current_channel_asymptotic_de_7e4b2a1d-9c3f-4d8e-a1b2-c3d4e5f60718`
  + frozen command in `design.md` §4; default-false auth, `PROFILE_ONLY`,
  read-only verifier (built at `D03`).

## STOP evaluation (packet §7): none triggered

Channel exact; records join with cluster+root retention (single generator;
`V`-domain + legacy-prior + fake-scratch excluded by rule); `D16` root absent
and banned seeds uncontaminated; grid bounded and non-adaptive (all 15 points +
seeds + rule fixed now); model limits verified (`design.md` §2); no review yet
(`D07` pending as packet-exact future task).

## Claim ceiling

Empirical calibration for this channel/decoder family only. `epsilon=0.10`
primary / `0.01` sensitivity are modeling targets, not project `FER`
qualification requirements. No `FER`, leakage/`SKR`, real-data, qualification,
promotion, publication, optimality, `D7-H`, or route-closure claim.

## Return

`AUDIT+SPEC DONE` (details in the final message). Execution false; `DE`/decoder
calls `0`; no commit/push. Next: `D02–D07` + `B/C` implementation per `tasks.md`
(each needs its own packet/authorization; the `DE` batch additionally needs an
explicit user grant + Pre-`EXECUTE`).
