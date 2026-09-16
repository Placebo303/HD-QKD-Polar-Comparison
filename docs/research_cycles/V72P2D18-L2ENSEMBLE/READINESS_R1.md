# D18 Current-Channel L2 Ensemble DE — Readiness R1 (no execution)

- Authority: `.workbuddy/tasks/D18_L2_ENSEMBLE_DE_READINESS_R1_TASK_PACKET.md`
  (§§1–10, §10 return contract). This readiness packet authorizes zero
  scientific DE/decoder calls.
- Track: documentation-only (no code, no DE/decoder execution, no root
  creation, no staging/commits, no push).
- Repo: `/mnt/d/Code/HD-QKD_Polar_Comparison`, branch
  `formal-ir-v72p1-addendum-clean` (not switched; no commit/push in this call).
- Predecessor (accepted):
  `D16_HOLDOUT_VALIDATION_COMPLETE_REVIEWED_AWAITING_ROUTE_DECISION`.
- Change: `openspec/changes/v72p2d18-current-channel-l2-ensemble-de/`.
- Log root: `docs/research_cycles/V72P2D18-L2ENSEMBLE/EXPLORATION_LOG.md`
  (this directory).
- Independent review: D18-R108, EVIDENCE_ACCESS VERIFIED, VERDICT
  `PASS_WITH_FINDINGS`, BLOCKING none (trusted VERIFIED, not rerun).

## 1. Route adjudication (§2, recorded first)

- D17's preregistered L055 result is preserved `FALSIFIED` under the frozen
  rule (observed `27/32=0.84375` vs parameter-probability band
  `[0.8899387155669418,0.9955050869733582]`). Never relabeled after D16.
- Interpretation ceiling: mild model-calibration miss, not an L1-construction
  failure (L055 27/32 per-graph `[7,7,6,7]`; L045 25/32 survived; L2-ORACLE
  9/32 survived its own `[0,0.5]` prediction).
- Forward-only methodology amendment: for future held-outs, distinguish a
  confidence band for latent `p_success` from a predictive interval for an
  observed binomial count. D16's registered verdict is not recomputed.
- Tails recomputed exact, description-only (never a verdict revision):
  `T(p_lo)=0.2730308351705778`, `T(p_hi)=3.3394200787523175e-07`.
- Legacy `D16_L2_DEGREE_SIGNAL` agrees directionally but remains secondary;
  the ensemble route is a main-thread decision on the complete evidence.

## 2. Frozen candidate family and matrix

- Variable-node edge-perspective family only: `lambda={2:x,3:1-x}`,
  `x=0.00,0.05,...,1.00` — exactly 21 candidates.
- IDs in accepted D8/D9 form `lam_d2_<x:.2f>_d3_<1-x:.2f>`; `x=0` is the
  mandatory DV3 control.
- Per `(candidate,m)`, `rho` derived from exact `R=1-m/128` via the D9 rule.
  No hand-set check distribution, no CE/f label.
- Current L2 row grid exactly `{89,94,99,104,109}`,
  `delta=5m/128-H_L2`. Sample recomputed (DV3/all-d2/mid × extremes):
  deltas `+0.25384/+0.44916/+0.64447/+0.83978/+1.03509`.
- Baseline comparator (not refittable): D17 DV3
  `delta_DE=0.5468113653656221` == D17 A2 recomputed
  (`DE_BRACKET`, bracket lo94/hi99).
- Pre-DE refusal gate (record, do not replace): invalid socket realization,
  minimum check degree <2, maximum check degree >8, or unnormalized rho.
  Refusal path real (reviewer ran, rc=2 pre-write/bind/load); 5 refusal
  cases real.

## 3. Frozen two-stage non-searching plan + budgets

- Stage S (bounded screen, ≤168 calls): all 21 candidates × m `{94,104}` ×
  seeds `2026094301..4304` × population 4000; V26 `max_iter=60`, entropy
  tolerance `1e-4`, streak20; deterministic plan id→m→seed, idx 0..167.
- Stage-S rank (verbatim): `(S_m94 desc, S_m104 desc, worst_H60_m94 asc,
  worst_H60_m104 asc, candidate_id asc)`; ties broken by the trailing key.
  Select exactly top-3 non-DV3 + DV3; fewer than three executable non-DV3 →
  engineering-blocked, family not widened.
- Stage C (confirmation, ≤288 new): selected 4 only, full five-m grid,
  seeds `2026094301..4308`, populations `{4000,16000}`; the 32 already-computed
  Stage-S identities are set-equal reused (overlap), never rerun; 456 total
  ceiling. No manual substitution, outcome-driven extension, binary search,
  or extra seed; no-rerun enforced in code.
- Candidate decision: pop16000 bracket recomputed per selected candidate
  under D17's exact `DE_BRACKET/DE_SOFT_BRACKET/DE_ONE_SIDED/POP_UNSTABLE`
  rules. Eligible only with clean stable `DE_BRACKET`, no refusal, and
  `delta_DE <= 0.5077488653656221` (baseline − 5/128 exact). Rank eligible
  non-DV3 by `(delta_DE asc, worst_H60_at_hi asc, max_check_degree asc,
  candidate_id asc)`. One winner only — candidate-only effect, disclaimed;
  selects a candidate for a later finite-L2 packet, claims no optimality.
- Terminals (4): `D18_L2_DE_SELECT_ONE_ENSEMBLE` /
  `D18_L2_DE_NO_IMPROVING_ENSEMBLE` / `D18_L2_DE_BASELINE_DRIFT` (recomputed
  DV3 conflicting with D17 baseline beyond frozen grid/stability rule) /
  `D18_L2_DE_ENGINEERING_BLOCKED`. All synthetic DE evidence only.
- Budgets (in code + spec): ≤456 scientific DE + ≤16 setup units; wall
  ≤1800s; per-call ≤300s; RSS <2GiB; one CPU process; no
  retry/resume/seed-search/adaptive grid extension. Fresh root
  `workspace/d18_l2_ensemble_de_<uuid>`; one exact repo-venv command frozen
  at readiness.
- Scope ceiling: D16 not recomputed; band-vs-predictive forward-only; legacy
  signal secondary; no APP/joint/L1; no exact/syndrome/undetected merge.

## 4. E01–E08 evidence table (trusted VERIFIED)

| Item | Evidence |
|---|---|
| E01 OpenSpec freeze | proposal/design/tasks/delta spec, packet §§1–6 verbatim in effect |
| E02 module | thin D18 module importing corrected D17/D9/V26 helpers; reuse vs added verified; rejected-duplication real (rho/bracket/convergence/trajectory delegated) |
| E03 plans + feasibility | 21-table, Stage-S/Stage-C plans, rank verbatim + ties, 32-overlap set-equal, 288 new / 456 total, no-rerun in code, 4 terminal edges incl. BASELINE_DRIFT + engineering-blocked, eligibility exact |
| E04 runner | `--profile-only`, `--de-sweep`, default-false `--execution-authorized`, fresh-root refusal, read-only `--verify` |
| E05 freeze | fresh seeds/root/command + budgets; predecessor seeds disjoint; future root absent |
| E06 tests | 26/26 reviewer own basetemp; D17 42+3 adjudicated environmental (materialized D16 root; default-addopts +12 Windows-basetemp errors environmental); fake complete run; refusal/no-overwrite/tamper proportionate |
| E07 PROFILE_ONLY | plan/candidate arithmetic only, zero DE/decoder calls, future root absent after |
| E08 review D18-R108 | CHANNEL/REUSE/FEASIBILITY/PLANS/RANK/BUDGETS/NO-PRODUCTION/CEILING all PASS; TEST_RERUN 26/26; BLOCKING none |

- Channel identity: corrected D17 R2 builder + L2-oracle dispatch
  (true-U1/XOR-U2/candidate/GF32-37/H_L2) is-identical; no copied kernels;
  D8/D9 L1 + V26 historical thresholds nowhere as gates.
- No-production: PROFILE_ONLY = arithmetic + Path probe; `sys.modules`
  clean; booby-trapped binders; fake injection; zero scientific calls;
  `py_compile` OK.
- Non-blocking notes: predecessor hit-count (presence suffices); pytest.ini
  Windows basetemp note; D16-root hygiene note.

## 5. Authorization state (all false)

- DE calls authorized: 0. DE/decoder calls executed: 0.
- Future root `workspace/d18_l2_ensemble_de_<uuid>`: ABSENT (verified this
  call; see log).
- This close grants no run. E09 doc-closure box checked here; memory triage
  noted separately by the triage agent.

## 6. Terminal and next gate

- Terminal: `D18_L2_ENSEMBLE_DE_READY_AWAITING_EXPLICIT_AUTHORIZATION`.
- Recommendation (R108): ready, awaiting explicit authorization.
- Next gate: one later explicit user grant (may cover Stage S + mechanically
  selected Stage C) + Pre-EXECUTE before any scientific execution.
- Claim boundary: no D18 DE, finite L2 graphs, D7-H, APP, real data, or
  FER/leakage/SKR/qualification/optimality/publication claims.

## 7. Commit/push/memory

- COMMIT_PUSH: none (no commit authorized this session; no commit, no push).
- Memory: triage agent separately; decision-log entry per E09.

(End of file)
