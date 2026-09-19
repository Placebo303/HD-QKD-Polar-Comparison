## 2026-09-14 D13 Batch A1 complete + VERIFIED PASS_WITH_FINDINGS batch-end review (MODEST rescue, evidence-only)

- Evidence [repo-observed]: single authorized `--d13-batch --execution-authorized` run in fresh root `workspace/d13_l055_decoder_ladder_5c41b416-cacc-4b6e-892e-d8a59c53170e` (6 files, hashes match); EXIT 0, 14:31:32–14:46:36Z; 224/224 calls (56 replay + 168 ladder), setup 2/8, wall 869.161/1800, per-call-max 8.297/120, RSS 125267968<2GiB, violations []; REPLAY 56/56 match, 0 mismatch, first-mismatch gate never triggered; RESCUES RL360_a1 3 (n128 1 / n256 2, MODEST) / RL360_a0.7 1 (0/1, NO) / FLOOD360 0 (NO); undetected 0 all arms, all 224 rows CHECK_UPDATED; ranking []; terminal `D13_MODEST_DECODER_RESCUE` (evidence-only, selects no route).
- Review [repo-observed]: batch-end review `D13-B1-REVIEW` = `EVIDENCE_ACCESS: VERIFIED` / PASS_WITH_FINDINGS, no blocker; sole non-blocking (a) manifest.command omits runtime flag by design (D11/D12 precedent). D12/Model-F inputs unmodified; grant consumed; no retry/repair/rerun. Full record in `docs/research_cycles/V72P2D13-L055-LADDER/EXPLORATION_LOG.md`.
- Lifecycle [decision]: terminal `D13_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`; evidence-only, no route acceptance; grant consumed; no second run.
- Boundary [decision]: synthetic L1 decoder diagnostic on frozen D12 L055 failures only; no FER/leakage/SKR/forward/L2/real-data/qualification/promotion/D7-H claim. Next gate is main-thread route decision only.

## 2026-09-14 D13 L055 decoder-ladder readiness complete (D1301-D1310, no execution)

- Readiness [repo-observed]: D1301-D1310 all PASS per `docs/research_cycles/V72P2D13-L055-LADDER/READINESS_R1.md` + `EXPLORATION_LOG.md`; OpenSpec `openspec/changes/v72p2d13-l055-decoder-ladder/`. D1310 `EVIDENCE_ACCESS: VERIFIED` / `PASS_WITH_FINDINGS`, no blocker: 56 D12 L055 failures recomputed (n128 30 [5,5,7,4,5,4] / n256 26 [5,3,5,4,4,5], all iter90 converged_no_syndrome CHECK_UPDATED, undetected 0), replay/bindings/gates-ranking/terminals verified, binders accepted unchanged (RL90 replay + RL360/damped-RL360/flooding-360, no tuning, no new decoder), 16/16 tests rerun, PLAN_ONLY byte-deterministic (decoder 0), D12 root untouched, future root `workspace/d13_l055_decoder_ladder_5c41b416-…` absent. Combined D12+X3 8 failures adjudicated pre-existing/environmental.
- Lifecycle [decision]: terminal `D13_L055_DECODER_LADDER_READY_AWAITING_EXPLICIT_AUTHORIZATION`; grants no execution; predecessor D12 L055 selection immutable (88 successes excluded, never pooled). Future batch EXPLORE (56 replay + 168 ladder = 224 calls).
- Boundary [decision]: synthetic L1 decoder diagnostic on frozen failures only; no ensemble-optimality/forward/L2/FER/leakage/SKR/real-data/qualification/promotion/D7-H/commit/push.

## 2026-09-14 D12 Batch A1 complete + VERIFIED PASS_WITH_FINDINGS batch-end review (L055 selected evidence-only)

- Evidence [repo-observed]: single authorized `--d12-batch --execution-authorized` run in fresh root `workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450` (6 files, hashes match); EXIT 0, 12:49:56–12:54:54Z; 432/432 calls, 62/62 setup, wall 290.154/1800, per-call-max 1.689/120, RSS 128274432<2GiB, violations []; 36/36 admission; exact total 221 = syndrome 221, undetected 0 (n128 L045 26 [6,3,2,5,4,6] / L050 39 [7,4,5,7,7,9] / L055 42 [7,7,5,8,7,8]; n256 L045 33 [6,6,4,6,5,6] / L050 35 [6,6,6,6,4,7] / L055 46 [7,9,7,8,8,7]); STABLE all six; MATERIAL L050 False (n256 margin +2, wins 2/6) / L055 True (margins +16/+13, wins 6/6); SPLIT False; ranking skipped; terminal `D12_SELECT_L055` (evidence-only).
- Review [repo-observed]: batch-end review `D12-B1-REVIEW` = `EVIDENCE_ACCESS: VERIFIED` / PASS_WITH_FINDINGS, no blocker; non-blocking only (48-vs-36 seed label; 1s start skew; manifest.command omits flag by design; call_idx per-width D11-F1 pattern). Predecessors D11/R3/Model-F untouched; grant consumed; no retry/repair. Full record in `docs/research_cycles/V72P2D12-FINITE-L1-DEGREE/EXPLORATION_LOG.md`.
- Lifecycle [decision]: terminal `D12_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`; evidence-only, no route acceptance; grant consumed; no second run.
- Boundary [decision]: synthetic finite L1 degree comparison only; no FER/leakage/SKR/forward/L2/real-data/qualification/promotion/D7-H claim. Next gate is main-thread route decision only.

## 2026-09-14 D12 finite L1 degree refinement readiness complete (D1201-D1210, no execution)

- Readiness [repo-observed]: D1201-D1210 all PASS per `docs/research_cycles/V72P2D12-FINITE-L1-DEGREE/READINESS_R1.md` + `EXPLORATION_LOG.md`; OpenSpec `openspec/changes/v72p2d12-finite-l1-degree/`. D1210 `EVIDENCE_ACCESS: VERIFIED` / `PASS`, no blocker: six cells recomputed from D9 rule EXACT, 36/36 A1-A6 independently recomputed, isolation/gates-ranking/terminals verified, budgets match, 26/26 + 41/41 tests rerun, decoder/scientific 0, future root `workspace/d12_finite_l1_degree_94fb9d22-…` absent.
- Lifecycle [decision]: terminal `D12_FINITE_L1_DEGREE_READY_AWAITING_EXPLICIT_AUTHORIZATION`; grants no execution; predecessor D11 wide-recovery immutable (never pooled). Future batch EXPLORE_HEAVY (432 calls).
- Boundary [decision]: synthetic finite L1 degree comparison only; no FER/leakage/SKR/forward/L2/real-data/qualification/promotion/D7-H/commit/push. Pre-EXECUTE must reconfirm dirty-tree preflight; L050-3101 4-cycle diagnostic retained.

## 2026-09-14 D11 Forward APP Batch A1 complete + VERIFIED PASS_WITH_FINDINGS batch-end review (wide recovery)

- Evidence [repo-observed]: single authorized `--forward-batch --execution-authorized` run in fresh root `workspace/d11_forward_app_7c1878b5-23a8-4fd8-a395-b5a33a58ea64` (6 files, hashes match); EXIT 0, 11:32:33–11:43:58Z; 720/720 calls, 62/64 setup, wall 661.1/2400, per-call-max 1.833/120, RSS 137068544<2GiB, violations []; 36/36 admission; L1 replay EQUAL R3 both widths; provenance 288/288 CHECK_UPDATED; exact total 209 = syndrome 209 (n128 J_M22/J_C0/O43; n256 J_M28/J_C0/O64); SIGNAL/SIGNAL → `D11_FORWARD_APP_WIDE_RECOVERY` (evidence-only); R3 root untouched; grant consumed; no retry/repair; no D7-H/reverse/mixed-L2/real-data; no commit/push.
- Review [repo-observed]: batch-end review `D11-B1-REVIEW` = `EVIDENCE_ACCESS: VERIFIED` / PASS_WITH_FINDINGS, no blocker; non-blocking F1-F5 (call_idx per-width wording; latent verify_root index basis; manifest command flag form; L2-seed column suggestion; R3-first test-order doc). Full record in `docs/research_cycles/V72P2D11-FORWARD-APP/EXPLORATION_LOG.md`.
- Lifecycle [decision]: terminal `D11_FORWARD_APP_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`; evidence-only, no route acceptance; grant consumed; no second run.
- Boundary [decision]: synthetic two-layer forward diagnostic only; no FER/leakage/SKR/qualification/promotion/real-data/D7-H claim. Next gate is main-thread route decision only.

### D11 forward wide recovery accepted; L1 remains bottleneck (2026-09-14)

- Decision: `D11_FORWARD_APP_WIDE_RECOVERY_ACCEPTED_ROUTE_TO_D12_L1_REFINEMENT`;
  retain machine terminal `D11_FORWARD_APP_WIDE_RECOVERY`.
- Evidence: MIX joint/source exact is 22/23 at n128 and 28/29 at n256;
  CONTROL is zero, all 288 transfers CHECK_UPDATED, L2 oracle 43/72 and 64/72,
  independent review PASS. Canonical forward transfer is not the main loss.
- Next gate: D12 readiness for fresh-graph finite L1 comparison of only
  λ2=0.45/0.50/0.55. D7-H remains closed; mixed L2 lacks calibration; real-data
  DECIDE waits for a stronger synthetic operating point. No D12 execution.

### D12 finite L1 degree-refinement readiness accepted (2026-09-14)

- Evidence [repo-observed]: D1201--D1210 complete; `D12-R1210`
  `EVIDENCE_ACCESS: VERIFIED / PASS`; D9 degree math, 36/36 admission,
  isolation, all selection edges, 432-call plan and zero-production boundary
  independently pass; 67 focused tests rerun by reviewer.
- Decision: `D12_FINITE_L1_DEGREE_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`.
  Retain L050/n256 seed 2026093101 four-cycle/girth-4 as diagnostic-only; no
  graph replacement.
- Boundary: future EXPLORE_HEAVY batch needs explicit user grant and runs both
  widths. No execution, D7-H, L2, real data or claim is authorized here.

### D12 L055 selected; route failures to D13 decoder ladder (2026-09-14)

- Decision: `D12_L055_ACCEPTED_ROUTE_TO_D13_DECODER_LADDER`; retain machine
  terminal `D12_SELECT_L055`; L050 rejected by the frozen two-width rule.
- Evidence: L055 exact 42/72 vs L045 26/72 at n128 and 46/72 vs 33/72 at n256;
  all 56 L055 failures used 90 iterations, while successes used 7--50.
- Next gate: D13 readiness to replay those 56 identities at RL90 and compare
  RL360, damped RL360 and flooding360. Do not broaden λ or rerun forward/L2
  until decoder dynamics are resolved. No D13 execution or D7-H.

## 2026-09-14 D11 canonical forward APP readiness complete (D1101-D1110, no execution)

- Readiness [repo-observed]: D1101-D1110 all PASS per `docs/research_cycles/V72P2D11-FORWARD-APP/READINESS_R1.md` + `EXPLORATION_LOG.md`; OpenSpec `openspec/changes/v72p2d11-forward-app/`. R1110 `EVIDENCE_ACCESS: VERIFIED` / `PASS_WITH_FINDINGS`, no blocker: canonical transfer/provenance/q-APP/oracle/admission reuse is-identical (16/16 defs, 17/17 imports), L1 replay gate verbatim (n128 MIX [4,4,2,5,3,5], n256 MIX [6,3,5,5,6,4], CONTROL zeros), shared-L2 identity (6 distinct/width, oracle rides MIX excluded from grading), gates/priorities/8 terminals verified, budgets 720/64/2400/120/2GiB match; 33/33 tests rerun + PROFILE 36/36 (L2 12/12 + L1 24/24); decoder/scientific 0; future root `workspace/d11_forward_app_7c1878b5-…` absent.
- Lifecycle [decision]: terminal `D11_FORWARD_APP_READY_AWAITING_EXPLICIT_AUTHORIZATION`; grants no execution; predecessor D10 R3 wide-L1 immutable (never pooled). Future batch EXPLORE_HEAVY (360/width, max 720, n256 iff `D11_FORWARD_SIGNAL(n128)`).
- Boundary [decision]: synthetic two-layer forward diagnostic only; no FER/leakage/SKR/real-data/qualification/promotion/D7-H/commit/push. Pre-EXECUTE must reconfirm dirty v72p2d5 tree state (kwargs on `_run_layered_block`) per R1110 finding (a).

## 2026-09-14 D10 R3 Batch A1 complete + VERIFIED PASS batch-end review (wide L1 signal reproduced)

- Evidence [repo-observed]: single authorized `--r3-batch --execution-authorized` run in fresh root `workspace/d10_r3_fresh_graph_scaling_4d39ed0e-3cbb-49f6-a1df-1dcc10868a8d` (6 files, hashes match); EXIT 0, 08:37:35–08:43:01Z; 288/288 calls, 50/50 setup, wall 316.6/1800, per-call-max 1.9954/120, RSS 125063168<2GiB, 1 process, violations []; exact total 52 = syndrome 52 (n128 M=23 C=0 MIX[4,4,2,5,3,5]; n256 M=29 C=0 MIX[6,3,5,5,6,4]; DV3 all 0); both widths `R3_REPRODUCED` (clauses T×6 each); n256 dispatched iff n128 REPRODUCED met; terminal `D10_R3_WIDE_L1_SIGNAL_REPRODUCED` (evidence-only).
- Review [repo-observed]: batch-end review `D10-R3-B1-REVIEW` = `EVIDENCE_ACCESS: VERIFIED` / VERDICT PASS, no blocking/non-blocking beyond benign notes; 24/24 A1-A6 independently recomputed; identities/dispatch/gates/budgets/A1-nonpooling PASS.
- Lifecycle [decision]: terminal `D10_R3_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`; evidence-only, no route acceptance; grant consumed; no retry/repair/rerun; A1 untouched/unpooled; no commit/push.
- Boundary [decision]: synthetic L1-only diagnostic only; no FER/leakage/SKR/qualification/promotion/real-data/L2/D7-H claim. Next gate is main-thread route decision only. Record: `docs/research_cycles/V72P2D10-R3-FRESH-SCALING/EXPLORATION_LOG.md`.

### D10 R3 wide L1 signal accepted; route to D11 forward APP (2026-09-14)

- Decision: `D10_R3_WIDE_L1_SIGNAL_ACCEPTED_ROUTE_TO_D11_FORWARD_APP`; retain
  machine terminal `D10_R3_WIDE_L1_SIGNAL_REPRODUCED`.
- Evidence: on six fresh graphs per width, mixed L1 exact is 23/72 at n128 and
  29/72 at n256, versus DV3 0/72 at both; all gates, 24 graph admissions,
  budgets and independent batch-end review pass.
- Next gate: D11 implementation/readiness for one canonical forward L1→L2 APP
  pass, comparing mixed versus DV3 L1 while holding a connected full-rank DV3
  L2 target fixed, plus shared L2 oracle. Do not use mixed degree on L2 without
  separate calibration. D7-H remains closed until forward transfer and L2-code
  ceiling are known. No D11 execution is authorized.

### D11 canonical forward APP readiness accepted (2026-09-14)

- Evidence [repo-observed]: D1101--D1110 complete; reviewer `D11-R1110`
  `EVIDENCE_ACCESS: VERIFIED / PASS_WITH_FINDINGS`, no blocker; canonical helper
  reuse, R3 replay, shared L2/oracle isolation, all gates, 720-call ceiling and
  zero-production boundary pass.
- Decision: `D11_FORWARD_APP_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`;
  trust reviewer tests without duplication.
- Boundary: before the separately authorized batch, reconfirm the dirty-tree
  `_run_layered_block` signature and `on_blocked_transfer="record"` semantics,
  then run focused D11 tests. Acceptance grants no execution or D7-H.

## 2026-09-14 D10 R3 fresh-graph scaling readiness complete (R301-R310, no execution)

- Readiness [repo-observed]: R301-R310 all pass (R310 pass-with-comments, no blocker); 48 fresh seeds separated; 24/24 future graphs A1-A6 independently recomputed; 23 new + 18 R2 tests; PROFILE_ONLY 24/24; decoder/scientific calls 0; future root `workspace/d10_r3_fresh_graph_scaling_4d39ed0e-…` absent before+after. Records: `docs/research_cycles/V72P2D10-R3-FRESH-SCALING/READINESS_R1.md` + `EXPLORATION_LOG.md`; OpenSpec `openspec/changes/v72p2d10-r3-fresh-graph-scaling/`.
- Lifecycle [decision]: terminal `D10_R3_FRESH_GRAPH_SCALING_READY_AWAITING_EXPLICIT_AUTHORIZATION`; grants no execution; A1 terminal/thresholds immutable, A1 records never pooled into R3 gates. Future batch is EXPLORE_HEAVY (144/width, max 288, n256 iff `R3_REPRODUCED(n128)`).
- Boundary [decision]: L1-only synthetic; no FER/leakage/SKR/real-data/L2/D7-H/qualification/promotion/commit/push.

## 2026-09-14 D10 Batch A1 complete + VERIFIED PASS batch-end review (evidence-only)

- Evidence [repo-observed]: single authorized `--batch --execution-authorized` run in fresh root `workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34` (6 files, hashes in EXPLORATION_LOG); EXIT 0; 96/144 L1 calls, 44/44 setup, wall 47.8775/1800 s, per-call max 0.9959/120 s, RSS 124772352<2GiB; 18/18 A1-A6; exact total 31 = syndrome-valid 31 (n64 DV3 1 [0,0,1], n64 MIX 20 [7,7,6], n128 DV3 0, n128 MIX 10 [5,2,3], n256 0 blocks undispatched); n64 POSITIVE → n128 dispatched; n128 AMBIGUOUS → n256 undispatched; terminal `D10_L1_AMBIGUOUS`.
- Review [repo-observed]: batch-end review `D10-MIXED-DEGREE-L1-A1-REVIEW` = `EVIDENCE_ACCESS: VERIFIED` / VERDICT PASS, no blocking/non-blocking findings; identities/counts/gates/terminal/budgets independently recomputed PASS.
- Lifecycle [decision]: terminal `D10_MIXED_DEGREE_L1_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`; evidence-only, no route acceptance; grant consumed; no retry/repair/rerun; no L2/D7-H/real-data; no commit/push.
- Boundary [decision]: synthetic finite-length L1-only diagnostic only; no FER/leakage/SKR/qualification/promotion claim. Next gate is main-thread route decision only.

### D10 A1 route accepted to fresh-graph R3 replication (2026-09-14)

- Decision: `D10_L1_AMBIGUOUS_RESULT_ACCEPTED_ROUTE_TO_R3_REPLICATION`.
  Preserve A1 terminal/thresholds and do not rerun it or dispatch its withheld
  n256 cells.
- Rationale: MIX vs DV3 exact was 20/24 vs 1/24 at n64 and 10/24 vs 0/24 at
  n128. The n128 5/2/3 graph split is a material signal but three graphs cannot
  distinguish finite-width decay from graph variability.
- Next gate: D10 R3 implementation/readiness for six fresh n128 graph pairs ×
  12 paired blocks, with conditional fresh n256 replication. D7-H remains
  closed until stable wider-width L1 recovery exists; no R3 execution is
  authorized by this route decision.

### D10 R3 fresh-graph scaling readiness accepted (2026-09-14)

- Evidence [repo-observed]: R301--R310 complete; reviewer `D10-R3-R310`
  `EVIDENCE_ACCESS: VERIFIED`, no blocker; 24/24 fresh graphs independently
  pass A1--A6 with zero replacements; seed separation, frozen gates/terminals,
  A1 non-pooling, budgets and no-production boundary pass.
- Decision: `D10_R3_FRESH_GRAPH_SCALING_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`.
  Trust the independent review; run its deferred live refusal and focused tests
  once at execution preflight rather than duplicating them now.
- Boundary: next gate is a separately authorized EXPLORE_HEAVY batch; no
  decoder execution, D7-H, L2/APP, real-data or claim is authorized here.

## 2026-09-14 D9 calibration accepted; DV23-0.45 selected for finite readiness

- Evidence [repo-observed]: D9 completed 96/96 DE calls, verifier 96/96 and 12/12 groups PASS, independent reviewer-go `EVIDENCE_ACCESS: VERIFIED`/`PASS_WITH_FINDINGS`, no blocker. DV3 stability 0/8+0/8; lambda2 0.45 8/8+8/8 stable-converged with AUT30 ratio 0.7453; lambda2 0.50 7/8+8/8 ambiguous; lambda2 0.55 6/8+4/8 stable-unconverged; f1.0 0/8 all and non-gating.
- Acceptance [decision]: accept terminal `D9_DE_CALIBRATION_SELECT_ONE` and candidate `lam_d2_0.45_d3_0.55` only for successor finite-length construction readiness. Do not promote 0.50 despite lower AUT30 because it failed the frozen 8/8 stability rule. Lifecycle `D9_DE_CALIBRATION_RESULT_ACCEPTED_SELECT_DV23_045`.
- Route [decision]: D10 builds a matched-constructor regular-DV3 control and mixed-DV23-0.45 candidate, uses multiple graph seeds, n64/n128/n256, accepted Model-F, f1.2 and L1-only decoding. This isolates degree distribution before L2 APP/cross-layer work. DE-to-row-layered trajectory/terminal equivalence remains unproven.
- Boundary [decision]: no finite decoder success, FER/leakage/SKR, real-data, qualification or promotion claim; D7-H remains unauthorized/not recommended; D10 execution requires its own readiness and explicit authorization.

## 2026-09-14 D9 DE-decoder calibration readiness accepted

- Semantics [decision]: accept the seven-stage V26↔v35 map and independent primitive certification (max error <=1.94e-16) with explicit ceiling: prior/centering, incoming coefficient direction, primitive check and flooding-variable algebra are certified; outgoing coefficient absorption, flooding↔row-layered trajectory, DE entropy↔decoder exact/syndrome terminal and finite-length performance are not equivalent claims.
- f1.0 [decision]: prospectively `BOUNDARY_DIAGNOSTIC`, derived from frozen `mu=0.013383 bit/symbol` (0.35% of H_L1) versus f1.2 `mu=0.794633`; it never gates/ranks, while >=7/8 crossing routes to main review. The two written margin clauses are algebraically one effective threshold; Δ_min=0.05 is a design allowance because accepted H_L1 has no uncertainty interval.
- Future batch [decision]: DV3 + lambda2 0.45/0.50/0.55, eight seeds (three reproduction + five fresh), f1.2 populations 4000/16000 and f1.0 diagnostic 4000, <=96 DE calls + <=12 setup, <=1200 s, post-call <=300 s, RSS <2 GiB, no retry/resume/adaptive search. All 24 degree/socket realization cells n64/n128/n256 pass; normative max check degree <=8, actual frozen matrix <=4.
- Lifecycle [decision]: `D9_DE_DECODER_CALIBRATION_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`; next gate is separate calibration authorization. No scientific DE run, finite decoder, D7-H, real data, qualification, promotion, commit or push is authorized.

## 2026-09-14 D8 DE sweep accepted; no winner, route to D9 calibration

- Evidence [repo-observed]: frozen D8 sweep completed 126/126 DE calls in 107.105 s, peak RSS 251805696 B, verifier PASS with 126/126 metric agreement and independent reviewer-go `EVIDENCE_ACCESS: VERIFIED`, `PASS_WITH_FINDINGS`, no blocker. Regular-DV3 converged 0/3 at f1.2 and f1.0; no candidate converged all seeds at both; terminal `D8_DE_BASELINE_NOT_CONVERGED`.
- Acceptance [decision]: accept lifecycle `D8_DE_SWEEP_RESULT_ACCEPTED_ROUTE_TO_D9_CALIBRATION`; winner remains none under the frozen gate. Lambda2 0.45 and 0.50 primary f1.2 convergence 3/3 is descriptive successor evidence only, not a retroactive D8 advancement; every candidate was 0/3 at f1.0.
- Route [decision]: next `D9_DE_DECODER_CALIBRATION_AND_THRESHOLD` must check DE-to-v35 semantics beyond check update, Monte-Carlo stability, finite graph realizability of `{2,3}` mixtures, and whether f1.0 is a justified hard gate or a boundary diagnostic in the next preregistration. No finite-length decoder or broader grid before this calibration.
- Boundary [decision]: no NB-LDPC impossibility, finite-length, FER/leakage/SKR, real-data, qualification or promotion claim; D7-H remains unauthorized/not recommended; all new execution requires a separate packet and user authorization.

## 2026-09-13 D8 rate-aligned GF32 ensemble readiness accepted

- Readiness [decision]: accept V26 MC-DE reuse plus the exact Model-F L1 full-32-ary adapter, rate mapping and deterministic 21-candidate lambda support `{2,3}` grid after reviewer-go `EVIDENCE_ACCESS: VERIFIED`, `PASS_WITH_FINDINGS`, 56/56 independent math checks and F1 correction/re-review PASS (15/15 focused tests). Lifecycle `D8_RATE_ALIGNED_ENSEMBLE_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`.
- Frozen future sweep [decision]: two conditions (f1.2 primary R=5/64, f1.0 secondary R=15/64), seeds 2026091601..03, 126 DE calls, regular-DV3 baseline, all-seed convergence plus >=5% worst-seed AUT_30 improvement advancement, deterministic single-winner tie-break. Claim ceiling is synthetic asymptotic DE-only.
- Carried semantics [decision]: partial roots fail normal `--verify` and are retained/adjudicated; 120 s per-call is checked between/after calls rather than interrupted; implemented setup count is 0; V26 uses random nonzero-coefficient ensemble semantics and does not exercise finite-length coefficient-stream seeds. These are non-blocking but must be stated in execution/result review.
- Boundary [decision]: readiness acceptance grants no DE sweep, finite-length decoder, D7-H, real-data, qualification, promotion, commit or push. Next gate is a separate D8 DE sweep authorization.

## 2026-09-13 D6 R1d EXPLORE accepted; eligible-only DV3 redirect closed

- Evidence [repo-observed]: fresh root `workspace/d6_graph_mother_r1d_141730d1-5ed4-4a60-a935-50e8f24f872d` completed 120 scientific + 18 setup calls, wall 13.5477 s, no watchdog/retry/resource failure, peak aggregate RSS 2049343488 <2 GiB. L1 exact/syndrome 0/40; L2-APP 5/40; L2-oracle 35/40; end-to-end APP exact 0/120; T1 PEG-DV3 silent at n64/n128/n256. Independent batch-end reviewer-go had `EVIDENCE_ACCESS: VERIFIED`, `PASS_WITH_FINDINGS`, no blocker, and verifier 20/20 PASS.
- Acceptance [decision]: accept stored terminal `D6_GRAPH_TOPOLOGY_NO_USEFUL_RECOVERY` only for the frozen B0/B1/T1 DV3 synthetic contract; lifecycle `D6_R1D_EXPLORE_RESULT_ACCEPTED_GRAPH_REDIRECT_CLOSED`. This closes the eligible-only DV3 topology substitution, not all graph families, degree distributions, n>256, real-data performance, FER, leakage, qualification or promotion.
- Route [decision]: next gate `D8_RATE_ALIGNED_ENSEMBLE_FEASIBILITY`; audit/reuse accepted GF32 density-evolution or ensemble machinery and test rate-aligned degree-distribution feasibility before another finite-length decoder batch. D7-H remains unauthorized/not recommended because X4/D6 show the base L1 layer is not recovering; alternation is not the next orthogonal variable.
- Authorization [decision]: all execution/promotion flags remain false; acceptance grants no D8 execution, real-data work, commit or push.

## 2026-09-13 主线程审查后自动续发下一任务包

- 默认交互 [decision]: 每次主线程完成审查、验收或路线裁决后，只要下一步已由证据和当前路线唯一确定，主线程应在同一回复中自动给出下一阶段成对的 task packet + 可直接复制 prompt；用户无需再发送“给下一个任务包”。
- 门禁边界 [decision]: 自动续发任务包不是自动执行授权。若下一阶段包含 decoder、EXPLORE batch、DECIDE、真实数据、昂贵或 claim-bearing 执行，包应冻结范围并停在相应显式用户授权门前；不得从用户对前一阶段的接受推导后续执行授权。
- 例外 [decision]: 若证据支持多个实质不同路线、需要用户科学取舍、缺少关键输入或下一步会扩大既定范围，则先给出清晰裁决问题而不擅自选路；一旦用户裁决，立即随验收回复附上下一个任务包和 prompt。

## 2026-09-13 reviewer-go 独立子代理证据可信规则

- 证据身份 [decision]: 本项目记录中的 `reviewer-go`（包括明确标注的可用 backup）是与 operator 分离上下文的独立 review subagent；其报告为独立复核结果，不是 operator 自评或主线程转述。
- 默认采信 [decision]: 当 reviewer 记录 `EVIDENCE_ACCESS: VERIFIED`，列明实际读取的制品与自行执行的命令/测试，给出可追溯结果，且 verdict 无 blocking finding 时，主线程可以直接采信其复核和测试结果；不得仅为形式完整再次机械重跑同一测试。`PASS_WITH_FINDINGS` 中已裁定为 non-blocking 的 finding 不触发重复评审，按记录的修正、后续 gate 或 batch-end review 处理。
- 边界 [decision]: 采信限于 reviewer 明示的 evidence scope 和 claim ceiling；缺少制品访问、测试未实际运行、结果互相矛盾、范围漂移或存在 blocking finding 时仍须核查。独立 reviewer 不能替代主线程的科学解释/路线裁决，也不能授予用户专属的 DECIDE 或 EXPLORE 执行授权。
- 当前应用 [decision]: D6 R1d heavy readiness 的 H45 `PASS_WITH_FINDINGS` 及其独立重跑结果可作为可信 readiness 证据，不需主线程再跑 343-test suite；终态仍为 `D6_R1D_EXPLORE_READY_AWAITING_EXPLICIT_AUTHORIZATION`，尚未授权 batch execution。

## 2026-09-13 仓库级双轨研究流程 EXPLORE/DECIDE 接受生效（WORKFLOW-TWO-TIER-R1，F4 结清）

- 接受终态 [decision]: 主线程接受 `TWO_TIER_WORKFLOW_ACCEPTED_REPOSITORY_WIDE`；`TWO_TIER_WORKFLOW_ACCEPTED` 为 D6 前置兼容别名，2026-09-13 正式生效。变更 `openspec/changes/repository-wide-two-tier-research-workflow/`（delta spec 为规范契约），独立评审 `docs/research_cycles/WORKFLOW-TWO-TIER-R1/REVIEW_VERDICT.md` = PASS_WITH_FINDINGS；F4 由本条结清。**D6 heavy-mainline packet 仅在此接受终态记录后方可启动。**
- 范围与优先级 [decision]: 双轨（EXPLORE/DECIDE）为仓库级永久默认，适用于此后每个新 route/task/packet/OpenSpec change/experiment/result；权威规则为 `AGENTS.md` §1.2 适用矩阵 + §3 + §10.1/§10.3，SOP 与 `docs/prompts/*` 为实现面；历史周期不变；未执行旧包按新流程机制 + 原冻结科学输入/阈值/预算/no-overwrite/授权边界执行；不得以 cycle/方法改名重引入 per-arm 纸面。
- EXPLORE 契约 [decision]: 五条件全满足才可 EXPLORE（synthetic 或已批准非敏感输入；fresh additive `workspace/` 或 no-write probe；有界可逆；无 FER/SKR/qualification/promotion/publication claim；无破坏性覆盖或新外部动作）。一 packet+prompt（含 preregistration 与授权边界）、一个结果根或 no-write transcript、一份 append-only `EXPLORATION_LOG.md`；一次授权覆盖冻结条件臂序列；至多一次预先注册的工程修复+重跑（科学输入/种子/阈值/数据角色/假设不变，失败尝试同日志保留）；一次 batch-end 独立评审替代逐臂评审；仅调用 decoder 不改变轨道。
- DECIDE 契约 [decision]: 任一满足即 DECIDE（冻结点/生死门；real/private/raw 数据；昂贵/正式/不可逆/claim-bearing；报告/发布/qualification/promotion 结果）。保留 accepted preregistration、Pre-EXECUTE（精确命令/预算/输出不存在/显式用户授权）、一条执行/结果记录、独立 Pre-RESULT、主线程接受；允许紧凑三文档（`PREREG_AND_AUTH.md`/`RESULT.md`/`INDEPENDENT_ACCEPTANCE.md`）。EXPLORE 触及 real 数据、route-closing 阈值、发布 claim、破坏性输出、显著更高成本或科学输入/假设变更前须升级 DECIDE。
- 取代与安全门 [decision]: 取代 `standardize-task-packet-review-loop` 的逐任务评审频率读法；扩展 `research-cycle-sop-single-user-simplification`；paired packet+prompt 交接面与全部安全门不变（user-only 授权、no-overwrite、real-data 保护、claim 边界、独立 Pre-RESULT、失败不可变保留、exact/syndrome/undetected 隔离、可复现）。
- D7 教训 [decision]: 机器终态标签为带作用域的预注册分类，不是不可变科学事实；`D7_F_REVERSE_ORDER_REGRESSION` 仅限 n=16 单图（2 discordant pair，`D7_F_CORRIGENDUM_R1.md`）作用域，引用必须携带作用域。
- F4 注记 [decision]: 下方 2026-08-28 与 2026-09-05 两条历史条目已就地限定（无例外措辞仅 DECIDE 成立；EXPLORE 以单日志 + 一次 batch-end 评审替代逐臂/逐次复核）；原文保留为历史记录。

## 2026-09-13 Repository-wide EXPLORE/DECIDE workflow accepted

- Acceptance [decision]: OpenSpec change `repository-wide-two-tier-research-workflow` and independent review `PASS_WITH_FINDINGS` are accepted with terminal `TWO_TIER_WORKFLOW_ACCEPTED_REPOSITORY_WIDE`; compatibility alias `TWO_TIER_WORKFLOW_ACCEPTED` is valid for successor prerequisite checks. The packet §2 change name is authoritative; its §4 slug was stale. No commit, push, decoder, D6, or other execution is authorized by this acceptance.
- Applicability [decision]: every future research task in this repository declares `EXPLORE` or `DECIDE`; implementation-only and documentation-only work has no execution gate. `EXPLORE_HEAVY` is only a cost annotation. Real data, formal qualification, route-closing decisions, security/report numbers, publication and promotion remain `DECIDE`.
- Review frequency [decision]: `EXPLORE` uses one frozen batch authorization, one append-only result log and one independent batch-end review; it does not require a separate reviewer after every operator arm or unchanged-scope repair. `DECIDE` retains explicit user authorization, Pre-EXECUTE, independent Pre-RESULT and main acceptance. This supersedes the unconditional reading of the 2026-09-05 coder-fast → reviewer-go entry; milestone review remains mandatory where the accepted track requires it.
- Historical gate annotation [decision]: the 2026-08-28 V55 Pre-RESULT rule remains fully binding for `DECIDE` claim-bearing evidence, but its "every execution/result cycle without exception" wording does not impose per-arm Pre-RESULT review on `EXPLORE`. The V55 safeguards for thresholds, leakage decomposition, `undetected` isolation, per-source accounting and disclosure remain unchanged.
- Deferred [decision]: add the track qualifier to `research-cycle-sop-single-user-simplification` when that older OpenSpec change is archived; no historical cycle rewrite is required.

## 2026-09-05 coder-fast → reviewer-go 必接规则持久化（一次性例外 R1 836e151c）

- Rule [decision]: 每次 coder-fast 完成（COMPLETE 返回）后必须接 reviewer-go 独立只读复核，无默认跳过；plan-only / 零生产代码不是省略理由。
- Exception [repo-observed]: V72P2D5 R1 push（commit `836e151c`）未做 post-commit reviewer 复核；用户 2026-09-05 显式特批跳过，记为一次性例外，下不为例。
- SOP status [repo-observed]: `docs/research-cycle-sop.md` 全文无 coder-fast/reviewer-go 字样，仅有通用“independent review”（§6步骤7、§10 Pre-RESULT）；`AGENTS.md` 仅 §6 行180 `/implement-change` 描述 planner → coder-fast → reviewer-go → memory triage 流水线，无强制“必接”条款；均判为明确缺失，不直接改工作流文件，补写需走 OpenSpec change。
- Follow-up [decision]: 后续每次 coder-fast COMPLETE 后调度 reviewer-go（push 前或 post-commit 补齐）；任何跳过需用户显式批准并在 `AGENT_PROJECT_MEMORY.md` + `docs/decision-log.md` 双记例外。
- 2026-09-13 作用域注记（F4）[decision]: coder-fast → reviewer-go 必接规则保留；按双轨政策，DECIDE 及一般 coder-fast 交付维持每次 COMPLETE 后必接 reviewer-go，EXPLORE 批次由一次 batch-end 独立评审满足（不逐臂/不逐次调度）；跳过仍需用户显式批准并双记。见顶部 2026-09-13 条目。
## 2026-09-05 V72P2D5-R1 plan revision PASS (plan-only, no code, no execution)

- Revision [repo-observed]: commit `836e151c` (`docs(v72p2d5-r1): revise GF32 rate-mother plan per review, no code no execution`), exactly 5 D5 plan files (`proposal.md`/`design.md`/`tasks.md`/`specs/spec.md`/`PLAN_FREEZE.md`); zero production `.py` modification; `REAL_EXECUTION_AUTHORIZED=false`, `DECODER_EXECUTED=false`, `VAL_LOADER_CALLS=0`, no `run_01`; Review PASS; `HEAD == origin`, ahead 0.
- Cap scope [decision]: `M_max=1000` is D5 synthetic cap only, not production sufficiency evidence.
- OQ2 verdicts [decision]: four-state `QUALIFIED / INCONCLUSIVE / CURRENT_CONFIGURATION_FAILED / BLOCKED`, replaces 90% death-line; `ROUTE_DEAD` deleted.
- Probability axis [decision]: `(Alice,Bob)` with `axis0` summation.
- Prefix gate [decision]: per-prefix 13-item structural gate + minimum 5-item PASS.
- M0 [decision]: two-stage natural prefix, non-hypothesis + deterministic row ordering without decoder.
- Seeds [decision]: frozen L1 `2026090501`, L2 `2026090502`, G0 `510..517`, G1 `600..699`, G2 `1000..1199`; search banned.
- Oracle [decision]: non-hard-gate, diagnostic-only `ORACLE_APP_NONMONOTONIC_DIAGNOSTIC`.
- Budget [decision]: P0 preflight n=64 2 blocks; G1 `<=900s`, G2 `<=3600s`, single call 120s, RSS `<2GiB`; calls G1 `APP100x2+oracle20x2`, G2 `APP200x3+oracle40x3`.
- Metric [decision]: `exact_failure_fraction`, not FER.
- Lifecycle [decision]: three-false, no single authorization across G0/G1/G2.
- Residual [repo-observed]: `M AGENT_PROJECT_MEMORY.md`, `M docs/decision-log.md` + untracked baseline uncommitted.
## 2026-09-05 V72P2D5 GF32 rate-mother PLAN_FREEZE (plan-only, no code, no execution)

- Freeze [repo-observed]: change `formal-ir-v72p2d5-gf32-rate-mother-plan`, commit `c3499522` (`docs(v72p2d5): freeze GF32 rate-mother plan, no code, no execution`), 5 files +540 lines (`proposal.md`/`design.md`/`tasks.md`/`specs/spec.md`/`PLAN_FREEZE.md` 111 lines); zero production `.py` modification; `REAL_EXECUTION_AUTHORIZED=false`, `DECODER_EXECUTED=false`, `VAL_LOADER_CALLS=0`, no `run_01`.
- Input [repo-observed]: `d=1024, U1/U2=[5,5], GF(32), N=1024`, model F, blocked outer-CV `CE_L1=3.814742 / CE_L2_oracle=3.347605 / CE_joint=7.162347` (worst `7.178766`, std `0.0158`, range `0.0423`), `lambda*=137.3823795883264` (D4R2 R2 audit); old `16/200/216` rows `MODEL_BUDGET_MISMATCH`, real use banned.
- Baseline [decision]: V31 QC-cyclic-projective `build_layer` (`nonbinary_v31.py:624`) is the sole selected baseline; per-layer single `M_max=1000` build + row-prefix disclosure `H[:k]` (reinterpretation, no constructor change); Lane-C (`construct_lane_c_prototype`) backup only; V36 (+32 rows, row-weight 10-14) and V35 (hardcoded 224) vetoed.
- Prior [decision]: `P1=sum_u2 P_F`, `P2=P_F/P1`; production `q@P` (`get_l1_app_prior_l2`), oracle-L2 (`get_conditional_posterior_l2`) diagnostic-only; sole adapter delta is frozen `lambda*` smoothing on `counts -> P_F`; floor dual-track audit `1e-300` / decoder `1e-15` with renormalization.
- Budget [repo-observed]: `rows=ceil(N*CE*f/5)`; n=1024 `f=1.0 782/686 tot1468`, `f=1.05 821/720`, `f=1.1 860/755`, `f=1.2 938/823`; old-216 gap `6254` bits / `1251` rows / `6.79x` (L1 need 3906 vs old 80; L2 need 3428 vs old 1000; total need 7334 vs old 1080).
- Gate [decision]: G0 tiny (marginal/conditional `<1e-12`, chain `<1e-10`, noiseless 100%) / G1 n=64 integration-trend (monotonic + oracle>=APP + zero crash, no kill) / G2 n=256 sole life-death (`f in {1.0,1.1,1.2}`, `m1={196,215,235}`, `m2={172,189,206}`, >=200 blocks; PASS = `f=1.2` end-to-end exact >=90% + monotonic + oracle>=APP; FAIL `<50%` route-dead / `50-90%` budget-insufficient both abandon n=1024 real).
- Lifecycle [decision]: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`; no apply before D5-T8 independent Plan Review ACCEPT (incl OQ1 per-layer `M_max` interpretation / OQ2 90% PASS line) + independent `EXECUTE_AUTH` for any decoder/VAL/n=1024 real run.

## 2026-09-04 V72P2D2-R1 orthogonal one-block BLOCKED RESOURCE_BLOCKED (descriptive-only, non-fresh, no promotion)

- Lifecycle [repo-observed]: base `e094f7e548380db4bfcbc1fe73472e670c32379a`, accepted-plan `4592bdad357a02f8f08a880ca0036beaed3ee900`, artifact `implementation_sha 580471cf` (R1 revision `a11cf239` in `cycle_state.yaml`) on `formal-ir-v72p1-addendum-clean`; single authorized R1 invocation consumed (`r1_execution_count_completed=1/1`); `r1_real_execution_authorized=false` after use, `scientific_promotion=false`, `no_run_01=true`; Pre-RESULT PASS; terminal `BLOCKED_RESOURCE_BLOCKED`, no rerun.
- Outcome [repo-observed]: `invocation_status=RESOURCE_BLOCKED`, `prep_status=PASS`, `fatal_error=timeout`; L `RESOURCE_BLOCKED` `timeout` 45 ckpts / 187 sweeps / 45 decoder calls, `final_checkpoint_rows=5792`, `final_syndrome_satisfied=false`, posthoc `final_oracle_exact=false`, disclosure 5792+44=5836 bits; I/P `NOT_ATTEMPTED`, 0 ckpts, 0 sweeps, 0 disclosure; A `LADDER_EXHAUSTED` `D1_REUSED` not rerun (carried 334 iters, 3100 bits / 620 syms); `normal_new_arm_count=0/3`; tag 0 `NOT_APPLICABLE` syndrome-only.
- Metering [repo-observed]: `prep_wall_s=7.765999999945052` (limit 600), `invocation_wall_s_before_report=610.25` (limit 2400), `peak_rss_bytes=277782528` (<2GiB); L `elapsed_s=602.484000000055` hit the per-arm 600s soft wall — resource stop, not a schedule/interleaver/prior verdict.
- Scope [decision]: single non-fresh VAL1726-1729 (session 20260123_1M_600k_0dB), mother 9036x10240 nnz49620, 72-pt ladder; DESCRIPTIVE_ONLY — no FER/SKR/information-limit/causal-graph/route/promotion; D2 `PREP_FAILED` root untouched; authorization consumed, no rerun.
- Evidence [repo-observed]: `comparison_bench/outputs_comparison/v72p2d2r1_orthogonal_oneblock_20260904/` exactly four files (manifest.json/results.json/table.csv/report.md) + `docs/research_cycles/V72P2D2-TRIAGE/RESULT_SUMMARY_R1.md` (`RESULT_SUMMARY.md` untouched) + `cycle_state.yaml`.

## 2026-09-04 V72P2D2 orthogonal one-block BLOCKED PREP_FAILED (descriptive-only, non-fresh, no promotion)

- Lifecycle [repo-observed]: base `e094f7e548380db4bfcbc1fe73472e670c32379a`, accepted-plan `4592bdad357a02f8f08a880ca0036beaed3ee900`, implementation `580471cf` on `formal-ir-v72p1-addendum-clean`; single authorized invocation consumed (`execution_count_completed=1/1`); `real_execution_authorized=false`, `scientific_promotion=false`, `result_created=true`; Pre-RESULT PASS; terminal `BLOCKED_PREP_FAILED`, `next_gate=BLOCKED_CLOSE_NO_RERUN`.
- Outcome [repo-observed]: `invocation_status=PREP_FAILED`, `prep_status=FAILED`, `fatal_error=NameError: name 'Q' is not defined`; L/I/P `NOT_ATTEMPTED`, 0 ckpts, 0 sweeps, 0 disclosure; A `LADDER_EXHAUSTED` `D1_REUSED` not rerun (carried 334 iters, 3100 bits / 620 syms); `normal_new_arm_count=0/3`; `no_run_01=true`; tag 0 `NOT_APPLICABLE` syndrome-only.
- Metering [repo-observed]: `prep_wall_s=0.43700000003445894` (limit 600), `invocation_wall_s_before_report=0.4529999999795109` (limit 2400), `peak_rss_bytes=174399488` (<2GiB); within budget, per-arm 600s wall not reached.
- Scope [decision]: single non-fresh VAL1726-1729 (session 20260123_1M_600k_0dB), mother 9036x10240 nnz49620, 72-pt ladder; DESCRIPTIVE_ONLY — no FER/SKR/information-limit/route/promotion; prep NameError is not a schedule/interleaver/prior verdict; authorization consumed, no rerun.
- Evidence [repo-observed]: `comparison_bench/outputs_comparison/v72p2d2_orthogonal_oneblock_20260904/` exactly four files (manifest.json/results.json/table.csv/report.md) + `docs/research_cycles/V72P2D2-TRIAGE/RESULT_SUMMARY.md` + `cycle_state.yaml`.

## 2026-09-04 V72P2D1 parity-layout diagnostic accepted close (descriptive-only, non-fresh, no promotion)

- Lifecycle [repo-observed]: base `ba0df2d3bea4147574e0b8224480f45c93505178`, implementation/accepted-plan `07744ccf3095eaa35b4c457005e268fb5ff52c41`, result `58656f59943b66f6319226d139e1fe67c41702a4` on `formal-ir-v72p1-addendum-clean` (`HEAD == origin` verified); single authorized invocation A-then-B serial, no rerun, no third layout, no other block; `CLOSED_ACCEPTED` / `RESULT_ACCEPTED`, pre-EXECUTE PASS + pre-RESULT PASS.
- Structure [repo-observed]: 9036x10240 nnz49620 both arms, deg2 9035 both arms, check-degree {4:1,5:4594,6:4441}; four-cycles 1196/1196, collisions 1194/1194, graph-isomorphic under degree-2 parity-column permutation (recomputed, not hand-filled); B col_map[1204:10239]=1204+permutation(9035), rng=default_rng(20260902), diagnostic-only seed.
- Baseline gate [repo-observed]: arm A reproduces V72P2 block0 — ckpt 72/72, iters 334/334, `LADDER_EXHAUSTED`, bit 3100/3100, sym 620/620, syndrome+tag+control 9036+64+71; lambda `221.22162910704503` exact-equal; CE `7.135005172802673` bitwise equal.
- Outcome [repo-observed]: A `LADDER_EXHAUSTED` 334 iters 118.97s / B `LADDER_EXHAUSTED` 321 iters 114.14s; invocation 240.17s (budget 1800s, 600s/arm, no overrun); 0 protocol-accepted, 0 verified-exact, 0 undetected (isolated, never merged); overall COMPLETED, fatal null.
- Metering [repo-observed]: per arm `leak_IR_bits=9100` (9036+64), `total_public_bits=9171` (+71 CONTINUE); `f_model_relative=1.2455097837734634`, `f_public_model_relative=1.2552274974710365` (denominator selected CAL-CV CE `7.135005172802673`, failed attempts included).
- Scope [decision]: single non-fresh block VAL1726-1729 (session 20260123_1M_600k_0dB, registry v71_data_registry.json schema v71_data_v1, data_sha 84d62779, CAL702..1725 shared prior); D1-D8 per-checkpoint wrapper scalars only (72 ckpts x 2 arms), no full prior/matrix/LLR/edge storage; DESCRIPTIVE_ONLY — no FER/SKR/information-limit/qualification/promotion; authorization consumed, no V73.
- Evidence [repo-observed]: `comparison_bench/outputs_comparison/v72p2d1_parity_layout_ab/` exactly four files (manifest.json/results.json/table.csv/report.md) + `docs/research_cycles/V72P2D1-PARITY/RESULT_SUMMARY.md` + `cycle_state.yaml`.

## 2026-09-03 V72P2-VAL descriptive real smoke completed (non-fresh, no promotion)

- Lifecycle [repo-observed]: exactly one authorized invocation used implementation/plan SHA `b33664d00b5b22a02b61df95b00c99ae0a0368b8`; all 9 assigned blocks were attempted with no rerun or tuning.
- Outcome [repo-observed]: 0/9 protocol-accepted, 0/9 undetected, 9/9 `LADDER_EXHAUSTED`, and no decoder/numeric errors; final candidates converged but syndrome/tag checks failed.
- Accounting [repo-observed]: total wall `1057.375s`, `3037` iterations; aggregate `leak_IR_bits=81900`, `total_public_bits=82539`; each block disclosed `9100/9171` IR/public bits.
- Prior denominator [repo-observed]: CAL-only selected CV `CE_ref_log2=7.135005172802673` at lambda `221.22162910704503`; all-attempt model-relative ratio `1.2455097837734632`.
- Claim boundary [decision]: this is descriptive reuse of non-fresh VAL, not FER, SKR, information-limit, algorithm-qualification, or promotion evidence; equal raw/final error counts do not establish bitwise identity.
- Historical timing [decision]: the V72P1 P1C one-iteration `1.046s` versus `<1s` failure remains explicit non-blocking evidence; do not claim the old timing suite passed.
- Evidence [repo-observed]: `comparison_bench/outputs_comparison/v72p2_val_descriptive_smoke_20260903/` and `docs/research_cycles/V72P2-VAL/REVIEW_VERDICT.md`.
- Authorization [decision]: V72P2 execution authorization is consumed; no successor execution or promotion is authorized.

## 2026-09-03 V72P1-ADP synthetic qualification accepted (synthetic-only, transcribed)

- Implementation SHA [repo-observed]: `ff88696f3c242cfb441dc9c82720e4fa6a371968` on `formal-ir-v72p1-addendum-clean` (`HEAD == origin` verified).
- Candidate [repo-observed]: `workspace/v72p1_baseline_check/20260903_h90q/` (v72p1_results.json/v72p1_manifest.json/v72p1_table.csv/v72p1_compact_report.md, seed 20260902, data_sha 84d62779, FrozenMotherSpec 9 / SoftJointConfig 8 / 11 arrays / CSR284248 / prefix1111 / checkpoint72).
- Solidified [repo-observed]: `comparison_bench/outputs_comparison/v72p1_synthetic_accepted_20260903_h90q/` (four files byte-identical, no rename, candidate preserved).
- Dual review [decision, transcribed]: `IMPLEMENTATION_REVIEW PASS` + `PRE_RESULT_REVIEW PASS` — user independent conclusion transcribed, covers only this implementation and candidate directory, synthetic qualification only (not re-reviewed this turn).
- Results [repo-observed]: P1A pack/prefix1111/checkpoint72/incremental/tag_ok deterministic pass; P1B tiny k2/3 n6/9 worst 1.998e-15 <1e-9 pass; P1C 9036x10240 1/3/10 all finite pass residual 4.2e-10 wall < thresholds; P1D n12k3 descriptive finite pass; overall true, five_state true, wall 53.125s peak 126.94MiB, llr_clip20.0 convergence_tol1e-6.
- Lifecycle [decision]: `accepted_plan_sha 73efd91f...` / `accepted_addendum_sha b0d55105...` unchanged; `implementation_sha ff88696f...`; `formal_execution_authorized false`; `scientific_promotion false`; real-data/formal decoder/run_01 not authorized, not verified. [repo-observed]

## 2026-08-28 V55 pre-EXECUTE / pre-RESULT 双重 review 门禁（强制）

- 根因 [repo-observed]: V55 连续复用 V54 模板常量 `efd34ef` 作为 `ACCEPTED_PLAN_SHA` 未替换，导致计划绑定错误。
- pre-EXECUTE review [decision, mandatory]: 每次正式 decoder 执行（`EXECUTE_AUTH` / 生产 `run_01`）前必须完成并记录：`HEAD == origin/<branch> == implementation SHA`、`ACCEPTED_PLAN_SHA` 重推导一致且 `rg <旧SHA>` 0 命中、目标 `run_01` 不存在、预算/门禁/`cycle_state` 与冻结 plan 一致、`py_compile` + 关键测试 PASS。FAIL 则阻塞执行，进入 `revise-required`/返工，新 SHA 重审。
- pre-RESULT review [decision, mandatory]: 每次输出 development result（`OPERATOR_RETURN.md` / `RESULT_SUMMARY.md` / `run_01` 固化/提交）前必须由独立线程或 reviewer 对照冻结 plan 复核阈值、泄漏公式分解、`undetected` 隔离（不得并入 success/FER）、per-source 分解、disclosure 等语义与实际产物。问题即返工，不得先产出后补 review；FAIL 阻塞固化，不得带病提交 `run_01`。
- 权威流程 [decision]: `AGENTS.md` §3 Mandatory Processes 与 §10.3、`docs/research-cycle-sop.md` §10 为长期流程；每次 execution/result 周期无例外适用。
- 2026-09-13 作用域注记（F4）[decision]: 上条“每次 execution/result 周期无例外适用”按仓库级双轨政策限定为 DECIDE 轨道——Pre-EXECUTE 仅对 DECIDE（正式/claim-bearing/costly）执行强制；EXPLORE 批次适用“单 append-only 日志 + 一次 batch-end 独立评审”。原文保留为历史记录，见顶部 2026-09-13 条目。

## 2026-08-27 执行后分析口头通报规则（V42起）

- 触发条件 [decision]: 每次正式 execution 完成后必做，首个适用 scope 为 `v42_diagnostic_18_calls_exactly_once`，后续所有同类正式 run 均适用。
- 分析维度 [decision]: 覆盖有效性门禁（J6等）、总体/分源门禁、成对增量、迭代/残留误码行为、终态归属。
- 输出边界 [decision]: 分析结果仅通过消息口头告知用户，不得自动写入 `run_summary`、`decision-log` 或其他产出文档/制品，除非用户显式要求写入。
- 衔接约束 [decision]: 口头分析本身不改变生命周期；生命周期继续按 execution、result-candidate 和独立结果评审流程推进，不增加任何额外输出文件。

## 2026-08-25 V38R1 accepted development result: bounded machine candidate

- Current result [repo-observed]: exactly-once authorized `run_02` completed in
  result-candidate commit `2416486f724f4fb7cbf1058d9dc1bb1fc5ded5ed`; main
  acceptance commit is `c8c5cd2ed5b60665af58e6a1639e58f99726bc05`. The machine
  terminal is `V38_MULTIPLE_ROUTE_SIGNALS`; this is not a scientific,
  formal-execution, promotion, or automatic-V39 decision.
- Frozen execution [repo-observed]: 45 calls over the fixed 15-block-per-lane
  set, with no rerun, tuning, seed change, or automatic V39 follow-up.
  Lane A was 0/15 exact with median residual 115 and 15/15 improved; Lane B
  was 9/15 exact with median residual 0; Lane C was 14/15 exact with median
  residual 0, with its only non-exact block at 1p5M/360202 (residual 63).
  One Lane B block had `syndrome_ok` without exact recovery; success remains
  defined by `exact_l2`, not syndrome status alone.
- Claim boundary [decision]: blocks are V25 TRAIN empirical-count samples
  with oracle-L1 inputs, not real-frame FER evidence. Do not infer threshold,
  SKR, formal-execution, qualification, or promotion results. The current
  result supersedes the pre-execution boundary in the implementation-only
  entry below; further reruns/tuning and automatic V39 are prohibited.

## 2026-08-25 V38P0 invalidation and V38R1 implementation acceptance

- Root-cause invalidation [repo-observed, decision]: V38P0 `run_01` passed
  `u2_bob` instead of complete `bob` to `get_conditional_posterior_l2`.
  Therefore the 45-record decoder evidence and `V38_NO_ROUTE_SIGNAL` are
  invalid; the terminal state is `V38_DIRECTION_EVIDENCE_INVALID`.
- Bounded structural evidence [decision]: the 27/27 structural records remain
  retained, but they do not support lane-performance claims, a `d_v >= 3`
  conclusion, or a claim that cycle optimization is ineffective.
- V38R1 implementation [repo-observed]: corrected implementation candidate
  `8f7bc7d8d7366772ff425528cd1080fa67ef7509`; independent implementation
  acceptance commit `65301365517af5718fce382cc8c9e40dd371ad65`. This is an
  accepted implementation boundary, not a scientific result, qualification,
  promotion, or decoder-performance claim.
- Execution boundary [decision]: V38R1 `run_02` is absent, unauthorized, and
  unexecuted. Any future decoder run requires a new explicit user
  `EXECUTE_AUTH` bound to the accepted implementation SHA. Do not record
  V38R1 as scientific evidence until that separately authorized execution and
  review occur.

## 2026-08-25 V37R1 P1 empirical-P DE screening: bounded negative result (`P1_NO_FINITE_FEASIBLE_DE_ADVANCE`)

- Direct evidence [repo-observed]: 2,349 real empirical-P GF(32) DE screening
  runs across 261 configurations (259 finite-feasible candidates with $N_2 \le 183,
  d_{c,\max} \le 20$ + matched regular $d_v=2$ baseline + V36 positive control)
  $\times$ 3 sources (1M, 1.5M, 2M) $\times$ 3 seeds completed in 3262.8s.
  - Baseline $d_v=2$: 1M $\text{AUT}_{30}=73.61$, 1.5M=59.38, 2M=59.45 (mean 64.15).
  - Best finite candidate (`lam_d2_0.10_d3_0.90`): 1M=153.997 (+109.2%), 1.5M=154.117
    (+159.6%), 2M=154.091 (+159.2%), mean 154.07, `all_seeds_converged=False`.
  - V36 positive control ($\lambda=\{2: 0.85, 4: 0.15\}$): mean 81.59 (+8.7% to +42.4%).
  - Passing screening candidates: 0 / 259 (P1-B confirmation skipped conditionally).
  - Terminal state: `P1_NO_FINITE_FEASIBLE_DE_ADVANCE`.
- Scientific diagnosis [decision]: the gap (+109% to +160% higher $\text{AUT}_{30}$
  vs -5% target) is structural, not a grid step resolution issue. High code rate
  ($R \approx 0.8125 - 0.8203$) and finite-length cycle-free forest gate ($N_2 \le 183$)
  force $\bar{d}_v \ge 2.857$ and $d_c \in [16, 20]$. In GF(32), check degrees $\ge 16$
  exponentially inflate message convolution uncertainty, stalling early iteration
  mutual information propagation. The optimizer saturates at the lowest-degree
  boundary ($\lambda_2=0.10, \lambda_3=0.90$).
- Architectural roadmap [decision]:
  - Abandon unstructured single-edge irregular $\lambda$-distribution simplex tuning.
  - Pivot to structured low-degree NB-LDPC for V38+:
    1. Protograph / Multi-Edge-Type (MET) NB-LDPC (controlled degree-2 chains without random cycle explosion).
    2. Near-$d_v=2$ low-degree graph topology + GF(32) edge label / coefficient optimization.
    3. Non-binary Spatially-Coupled LDPC (SC-NB-LDPC) fallback.

## 2026-08-24 GitHub-centered ChatGPT/OpenCode research-cycle SOP

- Workflow [decision]: GitHub is the durable exchange surface. ChatGPT handles
  planning/read-only scientific review; OpenCode implements a frozen packet;
  the user/main reviewer owns acceptance and formal execution authorization.
- Handoffs [decision]: every prompt/return binds repository, branch/PR, full
  target SHA, cycle ID, entrypoint, lifecycle state, and allowed action. Agent
  text becomes durable only after it is copied into a cycle file and committed.
- Data/Git [decision]: each milestone includes compact machine-readable data or
  a result summary with provenance, seeds, commands, metrics, omissions, claim
  limits, and reproduction/retrieval instructions. Normal non-force pushes
  only; incompatible Polar/crosstalk history goes to a separate formal-IR
  branch rather than being merged or overwritten.
- Authority: `docs/research-cycle-sop.md`; prompts under `docs/prompts/`.

## 2026-09-12 Manual Codex/OpenCode handoff restored

- Workflow [decision]: project-level Codex/ChatGPT ↔ OpenCode exchange is
  manual copy-paste through the repository task-packet, prompt, and return
  documents. Do not use `opencode_session`, `codex_desktop_bridge`, or an
  automatic callback loop for project work.
- Boundary [decision]: the existing global bridge, server, skills, and durable
  sessions are not uninstalled, modified, restarted, or closed. They are
  simply outside this project's active workflow unless the user explicitly
  opts back in through a later workflow change.

## 2026-08-24 V36 post-run scientific review correction

- Retained observation [repo-observed]: 15 paired development blocks gave
  baseline/candidate mean residual 174.80/157.07; 10/15 improved; exact 0/15.
- Gate [decision]: `NO_FINITE_GRAPH_ADVANCE` remains correct, but the route to
  A3 was not protocol compliant. A1 did not implement the frozen per-source
  >=10% same-setting DE confirmation; A2 realized 2288--3002 4-cycles and
  degree-2 cycle ranks 779--801 despite a zero-cycle requirement.
- Claim boundary [decision]: status is
  `POSITIVE_EXPLORATORY_RESIDUAL_SIGNAL / A1_DE_SELECTION_NOT_ACCEPTED /
  A2_STRUCTURAL_GATE_FAILED / NO_FINITE_GRAPH_ADVANCE`. No empirical-P DE
  superiority, trapping-set causality, general FER, or MET-necessity claim.

## 2026-08-24 V35R1 corrected bounded status

- `run_01` is invalid and superseded; `run_02` provides corrected A1--A3
  development evidence with 25 focused tests passing.
- All tested NB configurations had 0/15 exact recovery and the hand-designed
  mixed-degree graph worsened residuals. This supports only
  `NO_NB_CANDIDATE_FOR_TESTED_HAND_DESIGNED_CONFIGURATION`.
- The original OpenSpec required conditional A4 after A3 failure, but A4 was
  not executed in `run_02`. Durable status therefore also includes
  `PROTOCOL_PARTIAL_A4_NOT_EXECUTED`; do not claim the original full
  four-stage `NO_CANDIDATE_SUCCESS` terminal or a binary-MLC result.

## 2026-08-24 Strict first principle: high-performance correction algorithms

- User directive [decision]: the project's strict first principle is to find,
  implement, and experimentally validate scientifically reasonable
  high-performance IR/error-correction algorithms for the actual HD-QKD data.
- Priority measures [decision]: correction success/FER, leakage/reconciliation
  efficiency, throughput/runtime, memory/resource cost, and accepted-frame net
  secret-key yield.
- Engineering boundary [decision]: package maturity, general frameworks,
  defensive hardening, exhaustive audit, and verifier sophistication are
  secondary. They block algorithm work only for a concrete risk of wrong
  science/numerics, irreproducibility, unauthorized expensive execution, or
  destructive overwrite; otherwise mark non-blocking/deferred.
- Workflow consequence [decision]: use the shortest scientifically valid path
  from method hypothesis to implementation to performance measurement. Do not
  expand ordinary algorithm work into adversarial-verifier engineering.

## 2026-08-24 V34 matched empirical-P finite control: bounded FAIL / ER1 ACCEPT

- Lifecycle [repo-observed]: accepted accounting-corrected HEAD `c8cc1fbe`;
  user auth `user-v34-execute-auth-20260824-01`; one official 60-block execute;
  strict absolute-path verify consistent; independent ER1 ACCEPT; no run_02.
- Result [repo-observed]: 0/20 successes for each of 1M/1p5M/2M, no fatal or
  false accept. Mean GF(32) L2 errors changed 249.25->168.45,
  261.35->181.10, and 256.90->174.05; runtime means 10.1936/10.0084/9.9852 s.
  Status split is 37 converged-no-syndrome and 23 max-iter.
- Scientific boundary [decision]: direct empirical-P matching removed V32 B1's
  confounder but did not rescue this fixed V31 QC packet/V28R decoder at oracle
  L1 and max_iter=30. This is not NB-LDPC, FER, key-rate, qualification, or
  promotion evidence.
- Performance-first consequence [decision]: do not rerun/tune V34. Reuse its
  residuals for graph-structure diagnosis, then prioritize one empirical-P
  protograph/MET candidate and one rate-adaptive/incremental-syndrome mother
  code. Administrative archival must not delay algorithm work.
- Durable closeout: `docs/v34-formal-execution-er1-closeout-20260824.md`.

## 2026-08-24 V34 matched empirical-P finite control: P3 implementation candidate

- Current state [repo-observed]: V34 OpenSpec passed initial FR1 rejection,
  revised FR1 ACCEPT, independent science-amendment ACCEPT, and Codex main
  `ACCEPT_FREEZE`. Freeze baseline is `f5f61eb672afe8e399727fa5d7507ca9f2f9151a`;
  lifecycle freeze commit is `0c817a322d1d1674f65708563afe3b77c47ae961`.
- Scientific identity [decision]: change only the channel-law generator from
  V32's raw-SER uniform substitution to direct source-specific V25 train
  empirical P(A,B). Fresh seeds are nuisance randomization, not a paired trial.
  Keep V31 packet, V32 oracle-L1/V28R decoder, max_iter=30, 20 blocks/source,
  and source >=19/20 mechanical discriminator fixed.
- Reproducibility [decision]: NumPy exactly 2.4.0 and literal
  `V34-PCG64-REF1`; frozen 60-call digest
  `d30335b4d0d74df3e7729e01b02ae1ae73e43035652c59e81f871a5545fe73bb`.
- P3 evidence [repo-observed]: one CLI plus one focused test; compile,
  selfcheck and read-only real-input prepare PASS; focused fake suite
  `13 passed in 10.16s` under `workspace/v34_p3_main_20260824_01`; official
  V34 `run_01` absent. No real decoder or DE ran.
- Lifecycle boundary [decision]: current state is
  `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`, not IR1 ACCEPT. Next is
  the Ox Alpha P4 evidence packet followed by independent Codex IR1. V34
  production execution still requires a new explicit user EXECUTE_AUTH bound
  to the accepted implementation HEAD and frozen matrix.
- Durable handoff:
  `docs/v34-p3-implementation-candidate-and-ox-alpha-handoff-20260824.md`.

## 2026-08-24 V33 exact-rate empirical-P ensemble DE: PASS / ER1 ACCEPT

- Current state [repo-observed, independently reviewed]: user-authorized V33
  official `run_01` executed exactly once on HEAD `41d31151`; 30/30 calls and
  all six source×layer cells PASS 5/5. Strict verify returned consistent with
  no problems; independent Luna ER1 ACCEPTED. State is
  `ARCHIVED / SUCCESSOR_NOT_AUTHORIZED`; archived under
  `openspec/changes/archive/2026-08-24-formal-nonbinary-ldpc-v33-rate-aligned-empirical-channel-de-diagnostic/`.
- Scientific boundary [decision]: this proves convergence only for the frozen
  V25 train-only empirical-P, F03/A02, V31 exact-rate ensemble MC-DE. It does
  not prove a fixed QC graph, decoder, FER, finite code, net key rate,
  qualification, or promotion. L1 converged in 23–25 iterations and L2 in
  37–44; the persisted numerical entropy floor is not zero FER.
- Performance-first sequence [decision]: V33 PASS permits a new proposal for
  exactly one corrected matched empirical-P finite-control using the same V31
  QC packet/decoder, oracle L1, 20 blocks/source, fresh frozen seeds, and no
  tuning/rerun. It does not authorize implementation or execution.
- Literature increment [decision]: a 2024--2026 search did not change
  V33-first. Post-V33 structural candidates now explicitly include informed
  NB-MLC/JRDO, Block-MDS/QC, and a short-block rate-adaptive mother code; see
  `docs/hd-qkd-ir-performance-roadmap-20260824.md` §10.
- Research-code boundary [decision]: engineering checks are justified only
  when they prevent a wrong operating point, invalid scientific attribution,
  or irreproducible execution. Mature-package infrastructure is not a goal.
  Current roadmap: `docs/hd-qkd-ir-performance-roadmap-20260824.md`.
- This entry supersedes older statements below that V33 is
  `DRAFT_PENDING_FREEZE_REVIEW` or `EXECUTE_NOT_AUTHORIZED`; those remain
  historical snapshots.

## 2026-08-23 B1 NLL unit correction + long-term roadmap review (R1–R4) + audit-correction archived

- Unit correction [repo-observed]: Ground 2 of
  `docs/nbldpc-v32-main-review-verdict-20260822.md` misstated units — B1 raw
  posterior NLL mean is ≈229–245 bits per n=1024 block (≈0.224–0.239
  bits/symbol), NOT bits/symbol; reference conditional entropies are ≈0.80–0.83
  bits/symbol. Additive correction recorded at
  `docs/nbldpc-v32-main-verdict-unit-correction-20260823.md`; the original
  verdict file is preserved byte-identical on purpose. Future citations must
  use the corrected unit phrasing.
- Long-term roadmap review finalized [decision]:
  `docs/hd-qkd-ir-roadmap-review-20260823.md` (supersedes the same-day
  conversation-only version). Fixes route naming R1 matched empirical-P /
  R2 allocation-factorization / R3 binary-MLC & NB-Polar / R4 HD-Cascade
  reference, avoiding collision with historical Route A–D names.
- Roadmap priority convention [decision]: V33 exact-V31-rate empirical-P
  ensemble DE is the mandatory highest-value prerequisite gate; corrected
  matched finite-control becomes the next high-value experiment only after
  V33 passes.
- Law A wording [decision]: nominal feasibility only means NB-Polar's immediate
  information-theoretic veto is untriggered; it does not show NB-Polar
  feasible; the two-layer D2 results must not be cited as R3 support.
- Audit-correction change archived [result]: after verifier fix `3110cb0e`,
  F-G1 = ACCEPT; Change A12 terminal `audit_corrected_rate_aligned_de_required`;
  archived under `openspec/changes/archive/
  2026-08-23-formal-nonbinary-ldpc-v32-operating-point-audit-correction/`
  (closeout commits d76a55c3 + b1171cc9; HEAD b1171cc9). Supersedes the interim
  stop-point status quoted inside the two 2026-08-23 docs. V32 scientific
  attribution remains inconclusive (`bridge_inconclusive`, main-review layer);
  no qualification/promotion; V33 draft still DRAFT_PENDING_FREEZE_REVIEW.

## 2026-08-23 S4 research-doc closeout: B1 NLL unit convention + route registry R1–R4

- Unit convention [decision, authoritative citation]: B1 posterior NLL must be
  stated as "raw posterior NLL mean ≈229–245 bits per n=1024 block
  (≈0.224–0.239 bits/symbol)"; the form "229–245 bits/symbol" is banned.
  Reference entropies are per-symbol: ≈0.80–0.83 bits/symbol. Authoritative
  note: `docs/nbldpc-v32-main-verdict-unit-correction-20260823.md` (original
  verdict file preserved byte-identical).
- Route registry [decision]: future roadmap citations use R1 = matched
  empirical-P NB-LDPC; R2 = allocation/factorization redesign; R3 =
  binary-MLC / NB-Polar P0; R4 = HD-Cascade reference. Historical repo
  "Route A/B/C/D" names stay reserved for their older meanings.
- Sequencing [decision]: V33 exact-V31-rate empirical-P ensemble DE is the
  mandatory prerequisite; corrected matched finite-control is authorized only
  after V33 full PASS. V33 four-piece OpenSpec candidate exists as
  DRAFT_PENDING_FREEZE_REVIEW (untracked); DE execution still requires freeze +
  explicit authorization.
- Scope guard [decision]: Law A (empirical-P nominal budget feasible) supports
  no feasibility claim for NB-Polar or any finite scheme; it only records that
  the immediate information-theoretic veto has not triggered.
- Accepted docs [repo-observed]: `docs/nbldpc-v32-main-verdict-unit-correction-
  20260823.md` and `docs/hd-qkd-ir-roadmap-review-20260823.md` (v2, R1–R4
  renaming + F-G1 ACCEPT state), committed in the S4 closeout commit.

## 2026-08-23 V32 finite-DE bridge + operating-point audit correction: ACCEPTED closeout

- Observed [repo-observed, R2-verified]: V32 bridge raw record valid (B0 6/6;
  B1–B4 0/60 each; B5 import ok; exact-once, no resume, 10047 s). Correction
  v2 evidence (`.../nbldpc_v32_operating_point_audit_v2/run_01/`, eight files):
  q_mass_on_p_zero_cells = 0.2394680/0.2541265/0.2553477 (1M/1p5M/2M);
  full_expected_nll = "infinity" ×3; conditional_finite_support_mean =
  0.397–0.431 bits/symbol; truncated_common_support_cross_entropy =
  7.77–7.91 bits. D0: B1 divergence observation; B2 l2_errors_final=1024 is a
  not_run sentinel; B3/B4 improve-but-no-syndrome (~250→~179). Dual law:
  empirical P nominal budget feasible only (pure gaps +180–187 bits); original
  Q_B1 information-theoretically infeasible (required ≈3269–3458 bits vs pure
  syndrome 1000–1040 bits).
- Rejected interpretation [decision]: B1 divergence does NOT prove fixed QC
  graph / message-passing / V28R decoder failure — B1's generator law Q_B1 was
  not matched to the V25 empirical posterior (positive mass on P-zero cells ⇒
  full expected NLL infinite). The persisted bridge terminal
  `finite_graph_decoder_mismatch` and the first operating-point audit
  (`post_hoc_exploratory_only` lifecycle) are superseded for all attribution
  claims; neither may be cited as an accepted root cause.
- Next authorized boundary [decision]: the only next question is exact-V31-rate
  empirical-P ensemble DE convergence (L1 0.984375 ×3; L2
  0.8203125/0.814453125/0.8125) under F03/A02 — candidate change
  `formal-nonbinary-ldpc-v33-rate-aligned-empirical-channel-de-diagnostic`
  exists as DRAFT_PENDING_FREEZE_REVIEW only; DE execution requires a frozen
  OpenSpec plus explicit authorization. Fixed-graph/decoder/NB-Polar successor
  selection undecided. No qualification/promotion; correction commit chain
  59ba0236 → 0765d893 → 29a5dafe → 3110cb0e (verifier semantic guards ACCEPT).

## 2026-08-21 V31 closeout: `finite_graph_fail`

- V31 deterministic finite-graph redesign gate executed and archived
  (user goal authorization 2026-08-20). No V30R packet rerun.
- Fixed F03 GF32+GF32, V25 source-conditioned channel, m1=16, n=1024/2048.
- M1: 60/60 DE confirmation PASS (30/30 per n).
- M2: `PEG-capacity-aware` rejected both n (L2 GF32 rank-deficient,
  deterministic); `QC-cyclic-projective` constructed OK both n (occupancy<=31,
  full rank, projective-safe).
- M3: n=1024 full window 300/300 exact/tag=0 (`converged_no_syndrome` L2),
  exact/tag FER=1.0; n=2048 bounded 1M prefix (14 blocks) same failure.
- Terminal `finite_graph_fail`; read-only verifier `ok=true`, problems=[].
- Evidence: `comparison_bench/outputs_comparison/nonbinary_diagnostics/
  nbldpc_v31_20260820/run_01/`
- Report: `docs/nbldpc-v31-deterministic-finite-graph-redesign-report-20260820.md`
- OpenSpec archived. No push; no random search; no seed tuning; no
  qualification/promotion.

## 2026-08-21 V31 closeout correction — authoritative state (Change A, run_02 authoritative)

- Change A state: `closeout_corrected`; C01-C16 ACCEPT after A9R (C09 limitation persisted); C17-C18 pending until commit. [decision]
- Authoritative evidence: `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_closeout_audit_v2/run_02/` (closeout_verify/recount/gate/run_manifest); superseded `run_01` retained with empty limitation. [repo-observed]
- V31: `ARCHIVED_PARTIAL`; n=1024 300/300 `finite_graph_fail` valid (0 exact/tag, syndrome 0, L1_ok 296 L2_ok 0, runtime 13015s); n=2048 14 blocks from 1M only; original both-n execution incomplete, global PASS impossible, bounded-prefix contingency post hoc. [repo-observed]
- PEG replay limitation (persisted in run_02): "The canonical V31 manifest does not retain independently reconstructable rejected PEG packets..." — does not alter QC/neg result. [decision]
- No V31 rerun, no n=2048 completion. [decision]
- Successor: only after Change A archive, V32 finite-DE bridge diagnostic is next (not yet started); qualification/promotion still not authorized. [decision]
- HEAD `c8d2acab`, field_id `c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf`, m1=16. [repo-observed]

## 2026-08-20 V30R closeout: `finite_graph_fail`

- V29 is closed with `v29_finite_gate_fail`; V28R's duplicate projective keys
  and guaranteed weight-2 pairs are a finite matrix-construction defect, not a
  GF32xGF32 route impossibility.
- Original V30 `P102_ACCEPTED` is superseded by the V30R document revision.
  Independent P103 freeze review was ACCEPTED on 2026-08-20. Canonical
  `run_01` implementation/execution and independent read-only verification are
  complete; verifier `ok=true`, `problems=[]`, terminal
  `finite_graph_fail`.
- V30R freezes at most one balanced-projective and one
  `PEG-projective-cycle-cancelled` packet per selected allocation, at most two
  allocations/four packets globally; M1 failed allocations still complete all
  12 registered calls; M3 screen is blocks `0..19`, only top-ranked eligible
  matrix confirmation is blocks `20..69`, and its failure is global with no
  fallback.
- Bounded cycle rule: duplicate projective key/proportional column is the
  4-cycle FRC hard failure and must be zero; labels minimize exact newly closed
  Tanner-6 degenerate count by `(degenerate_6_new, ratio_index)`; Tanner-8 is
  topology/girth aggregate only; standard variable-side ACE is not used for
  `d_v=2`. Evidence is aggregate plus deterministic replay, without cycle
  catalogs or candidate rejection lists.

- Canonical result: M0 reproduced `15/69/303/922/1107`; M1 persisted 72 screen
  and 60 confirmation calls, with `m1_9,m1_12` selected and both 30/30; M2
  retained valid balanced packets for `m1=9,12` and rejected both PEG packets
  because support `(0,1)` had no projectively unique ratio. M3 stopped after
  blocks `0..5` on source 1M for both valid packets (`0/6` exact, `0` false
  accepts), so terminal `finite_graph_fail` occurred before other sources and
  confirmation. M1/M3 meters were 74.828s/719.876s.
- Scientific boundary: this closes only the tested `n=1024` F03 fixed
  allocation/family finite conversion with the V28 decoder. It does not close
  the V25 empirical channel, V26 DE, or all NBLDPC. No qualification,
  promotion, same-packet rerun, tuning, or push is authorized.
- Report:
  `docs/nbldpc-v30r-projective-safe-finite-graph-report-20260820.md`.

- V30R frozen input binding: V25
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/data_inventory.json`
  and
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/split_manifest.json`;
  V26 canonical `.../nbldpc_v26_20260818/run_02/` (manifest/M0/verify);
  V28R canonical `.../nbldpc_v28_gf32_finite_code/run_02_v28r/`
  (config/evidence/manifest/verify). Source IDs and
  delay mapping are `type2_1M_20260121_184040/-50 ps/1M`,
  `type2_1p5M_20260121_183806/+50 ps/1p5M`,
  `type2_2M_20260121_183657/+50 ps/2M`; pair paths are the matching
  `v13r3fresh_pairs_20260816/<source_id>/pairs.parquet` entries. Field binding:
  `GF2mField.create(32)`, `0b100101`, field_id
  `c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf`, and
  zero-based `ratio_index`.

## 2026-08-20 V27 finite-leakage-margin gate: PASS (pass_finite_budget_ready, block_len=1024)

- V27 gate executed once on additive run root `comparison_bench/outputs_comparison/
  nonbinary_diagnostics/nbldpc_v27r_finite_leakage_margin/run_01/` (322.9s wallclock). Terminal
  `pass_finite_budget_ready`, passing_block_len=1024; all four block_lens confirmed all three
  sources at the m1_ep offset-0 candidate. [result]
- Independent candidate-delivery review (P-CDR, in-conversation) ACCEPT after fixing critical
  dedup bug: `candidates[(bl,src)]=cand` collapsed 5 candidates/source to 1; fixed to 3-tuple
  key `(block_len, source, m1)`. Read-only verifier ok=true (recomputed terminal == persisted).
  11 T0/T1 tests pass. [result]
- `pass_finite_budget_ready` authorizes Phase C (V28 GF32xGF32 finite-code engineering) and
  Phase D (V29 retrospective finite-code gate); stop before fresh qualification. No push.
  [consequence]

## 2026-08-20 V28 GF32xGF32 finite-code engineering: COMPLETE + acceptance ACCEPT

- V28 implemented (`nonbinary_v28.py`) + 11 T0/T1 tests pass + additive run_01 (1.40s) +
  `verify_v28` ok=true + main-thread acceptance ACCEPT. Terminal
  `engineering_ready_for_retrospective_gate`. [result]
- Reuse: `GF2mField.create(32)`, `nonbinary_codebook` three-shift-cyclic GF(32) mother matrices
  + `gf_rank`, `nonbinary_v10_fftqspa.decode_error_domain` (Bob-only GF(32) FFT-QSPA). [result]
- Matrices: H_mother_L1 6x1024, H_mother_L2 202x1024; per-source L2 = public row prefix
  H_mother_L2[:m2]; gf_rank full (identity parity half). Noiseless decode recovers x exactly
  (both layers, 3 sources). [result]
- Honest limit: V27 split is sparse high-rate; uniform-QSC iterative correction limited
  (decoder fail-closed, converged_no_syndrome). V29 measures real FER on frozen V25 holdout.
  [finding]
- Leakage = m_total*5+64; f<1.3 for all 3 sources; 64-bit tag = SHA-256(x1_hat||x2_hat)[:8B. [result]

## 2026-08-19 V27R OpenSpec revision: source-adaptive finite-leakage-margin (ACCEPTED + Phase B executed)

- V27 OpenSpec revised from worst-source to SOURCE-ADAPTIVE budget: each source
  (1M/1p5M/2M) uses its own full-precision H1/H2; m_total=floor((1.3*block_len*H_source-64)/5).
- Frozen table (block_len 1024/2048/4096/8192 -> m_total): 1M 200/413/840/1693;
  1p5M 206/426/866/1745; 2M 208/430/873/1760. m1_ep=round(m_total*H1/H_total) (Python
  round, round-half-to-even, frozen explicit rule); candidates m1_ep+offset, offset in
  {-2,-1,0,+1,+2}, all five eligible; m2=m_total-m1. Realized f=(5*m_total+64)/n/H_total
  all <1.3 (1.29409-1.29974). All arithmetic re-verified this session. [decision]
- V27 is asymptotic true-predecessor-conditioned multistage DE (L2 conditioned on correct
  L1; no finite-code error propagation); single 64-bit tag only in total block leakage,
  not between layers. source/delay = public acquisition selector (posterior + syndrome
  budget), not per-symbol side info, no repeated billing. block_len and mc_samples are
  two distinct fields. [decision]
- Ordering keys per (block_len,source) ascending: worst_final_entropy, mean_final_entropy,
  abs(offset), m1. Screen fully executes, then confirmation in rank order; next candidate
  on failure until pass or all five fail. pass = same block_len with all three sources
  confirmed; multiple -> min block_len. [decision]
- Terminal states ONLY: pass_finite_budget_ready / de_pass_no_finite_headroom /
  implementation_blocked / resource_blocked (old fixed_ensemble_margin_fail removed).
  24h global completed-call cumulative resource gate; checkpoint bound to full frozen
  config; V26 archived reference only (no rerun). [decision]
- V27R docs written to openspec/changes/formal-nonbinary-ldpc-v27-finite-leakage-margin-de-gate/
  (proposal/design/tasks/spec). Old worst-source drafts backed up in tmp_v27r/old_*.md.
- BLOCKER (review gate): independent Luna freeze review could NOT be delivered this session
  - subagent infrastructure failed repeatedly (subagent foreground/background + muse_spark
  all failed; background agents stayed "ready" with no result). P102 ACCEPT NOT recorded;
  Phase B NOT started, per strict gate. Freeze review must complete (Luna) before V27
  implementation/execution. [blocker]

## 2026-08-19 V26 channel-informed DE gate complete: pass_target_f13 + V26R closeout

- V26 result: A02 (F03 GF32+GF32) converges f=1.3 on all 2 layer x 3 source x 5 confirm
  seeds (30/30, final mean entropy 0.00000); A01 (F01 GF512+GF2) f=1.3 fails on the GF2
  residual layer, passes at f=1.6; terminal pass_target_f13. [repo-observed]
- Read-only verifier verify_run independently recomputes 72 screen + 60 confirmation +
  A02@f=1.3 30/30 + rate/rho/seed/entropy/terminal from channel_counts.npz; run_01 and
  run_02 both 0 mismatch ok=true; persisted readonly_verify.json per run. [repo-observed]
- Correct formulas: f_i=leak_i/H_i, leak_i=(1-R_i)log2(q_i)=m_i log2(q_i)/n,
  R_i=1-f_i H_i/log2(q_i); NOT f=R/H and NOT R=f*H (would mix bit/symbol with normalized
  leakage). Applied in proposal/design/spec/report/code and V27 planning. [decision]
- V26 Run roles: run_02 canonical, run_01 deterministic_repeat (RUN_MANIFEST.json +
  README at nbldpc_v26_20260818/). [decision]
- 24h completed-call resource gate implemented as RESOURCE_LIMIT_SECONDS in
  run_screen/run_confirmation (_run_gated_stage) -> resource_blocked terminal; V26 not
  triggered (screen~44s + confirm~112s). [repo-observed]
- Explicit source<->delay metadata: SOURCE_METADATA in nonbinary_v26_channel.py
  (1M/1p5M/2M -> delay_used_ps -50/+50/+50, n_pairs 512000/708352/933120); exposed on
  ChannelAdapter and recorded in M0 detail + RUN_MANIFEST. [repo-observed]
- M1 reference fixes: adapter_input_entropy_matches_iter0 now runs the real MC-DE first
  round (record_channel_entropy read-only flag on run_mcde_posterior; default off so
  screen/confirm numerics unchanged); gf2_bsc_reference now clearly decides pass/fail
  (noiseless must converge; feasible-rate ~0.427 must converge; at-capacity ~0.714 must
  fail) instead of "both non-converge = agree". [repo-observed]
- V26 closes with an archived OpenSpec change (local commit, no push). Pass_target_f13 only
  authorizes proposing A02 finite-code/construction change; still no FER/MET/qual/promo. [decision]
- V27 = NEW OpenSpec change (finite-leakage-margin DE gate), four parts written, returned to
  main-thread freeze review; NOT executed in this work. [pending]
---

## 2026-08-18 V25 M0-M4 complete (pass_ready_for_de_change)

- V25 P102 ACCEPT (main-thread): +-1 adjacent-bin errors with source/delay_used_ps
  direction = source/delay-conditioned channel (not alignment blocker). [decision]
- V25 engineering+science done: F01-F05 MSB->LSB factorization x {natural,Gray},
  N_ab/P(A|B) direction, chain-rule M3, C01-C06 M1, M0/M2 diagnostics, M4.
  [repo-observed]
- Empirical channel: H(A|B)~0.80 bits; holdout NLL of empirical delta models
  0.81-0.83 vs QSC 3.2 / V17 product 3.3-3.5; direction stable over time and
  flips with delay sign (-50->+1, +50->-1). [repo-observed]
- M4: high-field F01(GF512)+GF2, mid-field F03(GF32)+GF32 for V26; status
  pass_ready_for_de_change. Chain-rule closed (err<=5e-9). [repo-observed]
- Evidence: nbldpc_v25_20260818/run_04/ (12 files, verifier ok=true). [repo-observed]
- Successor: V26 channel-informed DE is a NEW change requiring user auth; V25
  PASS only proposes V26, never auto-starts. No finite/FER/MET/qualification/
  public-residual/oracle; no push. [decision]
---

## 2026-08-18 V25 立项（文档 + OpenSpec 草稿）

- 用户交付 V25 冻结任务包并指示“更新至文档”；已落盘
  `docs/nbldpc-v25-empirical-channel-and-factorization-plan-20260818.md`。 [decision]
- V25 OpenSpec change 已建（DRAFT_PENDING_P0_AUDIT_AND_FREEZE_REVIEW）：
  `openspec/changes/formal-nonbinary-ldpc-v25-empirical-timestamp-channel-and-multilevel-factorization-gate/`
  （proposal/design/tasks/spec）。 [repo-observed]
- V25 冻结科学边界：V24 只排除 V17 聚合信道/GF(1024)/bounded single-edge；不排除
  GF(512)/GF(256)/multilevel/source-conditioned/MET/重校准 delay。 [decision]
- V25 主模型 P(A|B,Z)；编码分层（保持 1024-bin）≠ 物理 bin 合并（对照）；
  候选 F01–F05 × L01 natural/L02 Gray；chain rule 闭合；M4 仅
  pass_ready_for_de_change / fail_no_stable_factorization /
  blocked_insufficient_joint_data / blocked_alignment_unresolved。 [decision]
- 禁止：MET/有限码/FER/fresh qualification/公开 residual/coarse SER 冒充总 FER/
  Alice-oracle 选候选/holdout 选 mapping/raw pipeline/改动冻结 Polar 基线/push。 [decision]
- 未实现未执行；下一步 P0 只读审计 + P1 freeze review，ACCEPT 前不实现。 [pending]
---


## 2026-08-18 V24 gate result: FAIL — bounded single-edge route closed

- Pre-registered V24 M0-M2 gate completed: terminal_state `fail`
  (`single_edge_bounded_optimization_failed`). [decision]
- M0 mechanism PASS; 135 valid candidates from 8192 attempts; screen/refine/
  holdout all 0-converged (~0.20-0.32 entropy floor); 0/4 finalists passed all
  five holdout seeds. 314 DE calls, 4.87 h accumulated (<24 h). Read-only
  verifier ok=True. [repo-observed]
- Evidence:
  comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v24_20260818/run_20260818T135145_prod/
- V21/V22/V23 archived under openspec/changes/archive/2026-08-18-*. [decision]
- Successor: true MET is a separate user-authorized change candidate only;
  adjusting q/channel/f target is a separate user decision. No automatic
  fallback; no push. [decision]


## 2026-08-18 V24 engineering + archive + gate launch

- V21/V22/V23 formally archived (user-authorized): moved under
  openspec/changes/archive/2026-08-18-* with archive notes. [decision]
- V24 engineering (I01-I11) complete, all 21 focused tests pass. New files:
  [repo-observed]
  - comparison_bench/src/comparison_bench/formal_ir/nonbinary_v24_single_edge_de.py
  - comparison_bench/src/comparison_bench/cli/run_v24_single_edge_de.py
  - comparison_bench/tests/test_nonbinary_v24_single_edge_de.py
- V24 implementation facts (frozen packet): indexed proposal generator =
  SeedSequence([24000,k]) per attempt; 1-8 nonzero degrees/side; lambda degree
  2..64, rho degree 2..512; counts sum 64; profile validity is pre-DE and never
  depends on entropy; N_valid fixed regardless of DE error/nonfinite.
  [repo-observed]
- Proposal sparsity measured: only 135 unique valid in-band candidates across
  8192 attempts (band R in [0.9375, 0.94140625]).
- Pre-registered M0-M2 gate launched 2026-08-18 background; M0 mechanism PASS;
  screen in progress; evidence root under
  comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v24_20260818/.
  24h completed-DE-call resource gate enabled. [repo-observed]
- Expected terminal state likely `fail` (single-edge DE non-convergence ~0.3
  entropy is consistent across all prior V22/V23 ensembles). PASS/FINAL relay
  only after full gate + verifier. [pending]


## 2026-08-17 NBLDPC current single-edge tooling correction and V24 planning

- Current state is `NBLDPC_CURRENT_SINGLE_EDGE_TOOLING_BLOCKED`, limited to
  tested candidates/current V22b aggregate single-edge kernel. The prior
  route-wide unreachable conclusion is superseded. [decision]
- V21=`CONCLUDED_STOP_GATE_TRIGGERED_PENDING_ARCHIVE`: S0/S1/S2 FER
  0.625/0.5625/0.5625 retained; P0/P1 not pre-frozen; runtime Alice-injection
  verifier and V01 not run. AST tests do not establish runtime semantic
  verification. [repo-observed]
- V22=`CONCLUDED_CURRENT_KERNEL_NEGATIVE_PENDING_ARCHIVE`: tested target
  candidates negative; finite I03/E02 and Bob-only V01 cancelled/not run after
  DE gate. [repo-observed]
- V23=`CONCLUDED_SINGLE_EDGE_DIAGNOSTIC_PENDING_ARCHIVE`: historical name
  notwithstanding, implementation aggregates base matrices to single-edge
  lambda/rho and invokes V22b; true topology-preserving protograph/MET DE was
  not implemented. Raw scan has 3 matrices; extra consolidated points lack
  independent raw/verify packages. [repo-observed]
- Closeout plan:
  `docs/nbldpc-v21-v24-closeout-and-successor-plan-20260817.md`. This round is
  planning/docs only: no code, DE, archive, scientific output, or push. The
  independent closeout/V24 freeze review returned ACCEPT after all contract
  blockers were closed; archive still requires later user authorization. [decision]
- V24 is `FROZEN_PENDING_USER_AUTHORIZATION`: P01–P06 complete and P07 is the
  next boundary. It covers bounded q1024 V17 structured single-edge lambda/rho
  DE optimization only. MET/finite/FER/qualification/promotion are out of scope;
  true MET is a separate change candidate only after V24 FAIL and user
  authorization. [decision]

## 2026-08-16 Route blocked awaiting user (superseded 2026-08-17)

- q1024 structured f<=1.3 not reachable with current tooling.
- Awaiting user choice: DE optimization / adjust target / MET / archive. [repo-observed]

## 2026-08-16 V19→V23 final review summary

- `docs/nbldpc-v19-v23-review-summary-20260816.md` written.
- Short-block OSD/top-K: scientific_not_ready; structured DE target f: not reachable.
- No new automatic direction without user input. [repo-observed]

## 2026-08-16 V23 DE not reachable conclusion

- q1024 structured rate0.9375 DE non-convergent across plain/SC/regular-protograph/irregular ensembles.
- entropy floor ~0.19-0.34; further needs full DE optimization or different channel decomposition.
- Evidence: nbldpc_v23_20260816/de_not_reachable_summary.json. [repo-observed]

## 2026-08-16 V23 protograph scan implemented

- 新增 nonbinary_v23_protograph.py + CLI + 测试。
- Regular protographs (2..8)x32..128 r0.9375 q1024 structured: all non-converged, entropy plateau ~0.2.
- Evidence: nbldpc_v23_20260816/protograph_scan_r09375_smoke/scan.json. [repo-observed]

## 2026-08-16 V23 protograph DE smoke

- V23 OpenSpec draft created.
- 2x32 all-ones protograph (r0.9375, q1024, structured V22b): non-converged, final entropy ~0.336.
- Next: small protograph grid scan / MET. [repo-observed]

## 2026-08-16 V22 DE_NOT_READY closeout

- q1024 r0.9375 structured DE non-converged across tools/budgets.
- V22 frozen scientific_not_ready; no finite construction.
- Next: MET/protograph DE (V23). [repo-observed]

## 2026-08-16 V22b budget scan still non-converged

- q1024 r0.9375 degree_max=512 n200 iter30: 3/3 non-converged.
- Structured target-rate DE not passing; need MET/protograph or accept not-ready. [repo-observed]

## 2026-08-16 V22b high-degree DE implemented

- 新增 nonbinary_v22b_mcde.py + de_gate + CLI + tests（临时提升 V14 DEGREE_MAX）。
- q1024 r0.9375 degree_max=512 可运行，non-converged at iter10。
- 证据：nbldpc_v22_20260816/v22b_de_gate_q1024_r09375_dmax512_smoke/de_gate.json。 [repo-observed]

## 2026-08-16 V22 task packet frozen

- 方案：additive V22b structured MC-DE with DEGREE_MAX>=128，然后 SC-LDPC 结构化适配。
- 阻塞：V14/V11 check degree cap=64，q1024 rate0.9375 无法运行。 [repo-observed]

## 2026-08-16 V22 structured DE diagnostic

- q1024 structured rate0.70: runs, non-converged.
- rate0.9375: rho check degree >64 cap in V14 MC-DE.
- Need MET/protograph or higher check-degree support to reach f<=1.3. [repo-observed]

## 2026-08-16 V22 SC-LDPC DE gate pass at p=0.05

- q1024, p=0.05, max_iter=50: 6/6 SC-LDPC rows converged, gate_passed=true.
- p=0.20/0.10 max_iter=20 non-converged.
- Evidence: nbldpc_v22_20260816/sc_de_gate_q1024_p005_iter50_smoke/sc_de_gate.json. [repo-observed]

## 2026-08-16 V22 SC-LDPC DE gate smoke

- 新增 `nonbinary_v22_sc_de_gate.py` + CLI + 测试（复用 V11 SC-MC-DE）。
- q1024 p=0.20 smoke：S1/S3 × G1/G2/G3 全部 non-converged。
- 证据：nbldpc_v22_20260816/sc_de_gate_q1024_p020_smoke/sc_de_gate.json。 [repo-observed]

## 2026-08-16 V22 q1024 DE gate smoke

- q1024 rate0.9375, 3 valid 8-degree candidates: all non-converged/error, gate_passed=false.
- Evidence: nbldpc_v22_20260816/de_gate_q1024_r09375_smoke/de_gate.json.
- Need real structured ensemble or larger budget. [repo-observed]

## 2026-08-16 V22 DE gate harness

- 新增 `nonbinary_v22_de_gate.py` + CLI + 测试。
- q16 smoke gate：3 个合法 8-degree 候选 non-converged。
- 下一步 q1024 DE gate。 [repo-observed]

## 2026-08-16 V21 Bob-only stop gate triggered

- 实现 V21 Bob-only 模块/CLI/测试；64 全新帧：
  S0 FER=0.625, S1 FER=0.5625, S2 FER=0.5625。
- 停止门触发：短块 OSD/top-K 分支冻结为 scientific_not_ready。
- V20 已移入 archive；V22 OpenSpec 草稿创建。 [repo-observed]

## 2026-08-16 V21 Bob-only plan frozen (post-review)

- 新契约：`docs/nbldpc-v21-bob-only-plan-20260816.md`。
- V20 addendum：31/64=oracle upper bound；40/96=top-4 oracle coverage；30/64=unverified Bob-only estimate；V01=counting-only。
- V20 status: CONCLUDED_PENDING_SCIENTIFIC_CORRECTION_AND_ARCHIVE。
- 下一步：Phase 0 收口 → V21 S0/S1/S2 Bob-only 验证。 [repo-observed]

## 2026-08-16 Round 108 — V20 M5 归档

- 使用规划 subagent 评估：建议归档 V20 M5。
- 已添加 archive_note.md；V20 tasks 状态 ARCHIVED。
- 最佳诊断：n64+bounded4 31/64, FER=0.515625。 [repo-observed]

## 2026-08-16 Round 107 — M2 random dense 不优于 PEG

- random dense H + bounded4 seed2252：3/8，差于 PEG+bounded4 5/8。
- M2 简单变体无增益。 [repo-observed]

## 2026-08-16 Round 106 — V20 M5 完成，等待新方向

- 全量回归 33 passed。
- V20 M5 COMPLETE；当前无自动下一步。 [repo-observed]

## 2026-08-16 Round 105 — V20 M5 最终结论

- 最终 N6 v6 表：n64+bounded4 主推 FER=0.515625；n80+bounded5 top-K 备选 FER=0.5833（12 seeds）。
- V20 M5 CONCLUDED。 [repo-observed]

## 2026-08-16 Round 104 — n80 12 seeds 仍差于 n64

- n80 seed2312: baseline 1/8 -> integrated 1/8（无增益）。
- 12 seeds 汇总：baseline 33/96 -> integrated 40/96（FER 0.6563 -> 0.5833），差于 n64 0.515625。
- 建议停止 n80 扩样，回到 n64 主推或探索混合策略。 [repo-observed]

## 2026-08-16 Round 103 — n80 11 seeds 仍差于 n64

- n80 seed2311: baseline 4/8 -> integrated 4/8（无增益）。
- 11 seeds 汇总：baseline 32/88 -> integrated 39/88（FER 0.6364 -> 0.5568），差于 n64 0.515625。
- n80 top-K 有正收益但整体不稳定。 [repo-observed]

## 2026-08-16 Round 102 — n80 高方差回落

- n80 seed2310: baseline 0/8 -> integrated 0/8。
- 10 seeds 汇总：baseline 28/80 -> integrated 35/80（FER 0.65 -> 0.5625），差于 n64 0.515625。
- n80 top-K 有正收益但不稳定，尚不能作为确定更优配置。 [repo-observed]

## 2026-08-16 Round 101 — n80 9 seeds 略优于 n64

- n80 seed2309: baseline 3/8 -> integrated 4/8。
- 9 seeds 汇总：baseline 28/72 -> integrated 35/72（FER 0.6111 -> 0.5139），略优于 n64 0.515625。
- 正收益：2301、2303、2305、2306、2307、2308、2309；无增益：2300、2304。 [repo-observed]

## 2026-08-16 Round 100 — n80 8 seeds 与 n64 打平

- n80 seed2308: baseline 2/8 -> integrated 3/8。
- 8 seeds 汇总：baseline 25/64 -> integrated 31/64（FER 0.6094 -> 0.515625），与 n64 最佳打平。
- 正收益：2301、2303、2305、2306、2307、2308；无增益：2300、2304。 [repo-observed]

## 2026-08-16 Round 99 — n80 top-K 成为新最佳（FER=0.5）

- n80 seed2307: baseline 4/8 -> integrated 5/8。
- 7 seeds 汇总：baseline 23/56 -> integrated 28/56（FER 0.5893 -> 0.5），**优于 n64 0.515625**。
- 新最佳配置：n=80,m=5 + bounded5 top-K=4。 [repo-observed]

## 2026-08-16 Round 98 — n80 第 4 个正收益 seed，几乎追平 n64

- n80 seed2306: baseline 4/8 -> integrated 5/8。
- 6 seeds 汇总：baseline 19/48 -> integrated 23/48（FER 0.6042 -> 0.5208），几乎追平 n64 0.515625。
- 正收益：2301、2303、2305、2306；无增益：2300、2304。 [repo-observed]

## 2026-08-16 Round 97 — n80 第 3 个正收益 seed

- n80 seed2305: baseline 3/8 -> integrated 4/8。
- 5 seeds 汇总：baseline 15/40 -> integrated 18/40（FER 0.625 -> 0.55），接近 n64 0.515625。
- 正收益：2301、2303、2305；无增益：2300、2304。 [repo-observed]

## 2026-08-16 Round 96 — n80 扩样后平均未优于 n64

- n80 seed2304: baseline 3/8 -> integrated 3/8（无增益）。
- 4 seeds 汇总：baseline 12/32 -> integrated 14/32（FER 0.625 -> 0.5625），尚未优于 n64 0.515625。
- 正收益 seeds 仍为 2301/2303。 [repo-observed]

## 2026-08-16 Round 95 — n80 top-K 多 seed 正收益

- n80 seed2303: baseline 3/8 -> integrated 4/8。
- 正收益 seeds：2301、2303；合计 baseline 7/16 -> integrated 9/16（FER 0.5625 -> 0.4375）。
- 2300 无增益；2302 潜在 2/8 待集成。 [repo-observed]

## 2026-08-16 Round 94 — n80 top-K 正结果

- n=80,m=5 seed=2026082301：
  - baseline（无 bounded-ML）：4/8 exact
  - + bounded5 top-K=4：5/8 exact（frame5 恢复）
- 首个 n80 正收益；需更多 seeds 统计平均。 [repo-observed]

## 2026-08-16 Round 93 — V20 M5 收尾完成

- V01 只读验证：8 个 bwml 输出合计 31/64 exact, FER=0.515625，无计数问题。
- V20 tasks M5 COMPLETE；V01/C01/C02 完成。
- 自动路线已到终点；进一步需新机制或用户方向。 [repo-observed]

## 2026-08-16 Round 92 — edge-label sweep 无提升

- 新增 `edge_label_seed`（API + CLI）。
- 固定 frame 2252 的 edge-label 1/2/3 均为 5/8 exact，无提升。
- 最佳仍 n64 31/64, FER=0.515625。 [repo-observed]

## 2026-08-16 Round 91 — 附加 n64 lambda/rho 探针无提升

- lambda062 seed2204 bounded4: 5/8（无提升）
- lambda058 seed2220 bounded4: 4/8（无提升）
- rho35_39 seed2252 bounded4: 3/8（更差）
- V20 M5 邻域基本穷尽；最佳仍 n64 31/64, FER=0.515625。 [repo-observed]

## 2026-08-16 Round 90 — frame_offset 分块支持；n80 top-K 无净提升

- 新增 `frame_offset`（API + CLI），支持分块跑有限码实验。
- n=80,m=5 seed=2026082300 top-K=2 分块完整集成：2/8 exact，与 V19 相同。
- n64 bounded4 仍为最佳：31/64, FER=0.515625。
- 新增 frame_offset 测试；全量 32 passed。 [repo-observed]

## 2026-08-16 Round 89 — top-K list decoding implemented; n80 potential

- `bounded_weight_ml_decode_candidates`（max_weight=5, top_k=4）实现并测试。
- n=80,m=5 seed=2026082300 frame0 直接验证 Alice 在 top4；单帧完整管线可 exact。
- 完整 8 帧 top-K 集成因计算量超时；后续需优化 numba top-K 或降低 K/帧数。
- n64 bounded4 单 ML 仍为 31/64, FER=0.515625。 [repo-observed]

## 2026-08-16 Round 88 — bounded-ML 扩展 max_weight=5；n80 单 ML 未提升

- `nonbinary_v19_bounded_ml.py` 增加 numba k=5 枚举，支持 n=80,m=5,max_weight=5。
- n80 seed2300 完整集成仍 2/8 exact；原因：weight<=3 错误候选先验得分高于 Alice，
  单 ML 不选 Alice；需 top-K 列表 + 公开校验/哈希。
- n64 bounded4 单 ML 仍是最佳实际改进：31/64, FER=0.515625。
- 新增测试 max5 identity；全量 30 passed。 [repo-observed]

## 2026-08-16 Round 87 — V20 bounded-ML 64 帧完整验证：31/64 exact, FER=0.515625

- 8 个 seed 全部用含 bounded-ML 的完整管线运行，确认 **31/64 exact_correct, FER=0.515625**。
- 新增 N6 v5 对比表：
  `n6_comparison_v5_q1024_v20_bwml/comparison_table.csv` + `comparison_summary.json`。
- 当前 q=1024 f≈1.136 最佳 FER=0.515625（diagnostic_only）。 [repo-observed]

## 2026-08-16 Round 86 — V20 批准；M5 bounded-ML 将 64 帧 FER 降至 0.515625

- 用户批准 V20 直接规划/执行；V20 status -> APPROVED/IN PROGRESS。
- 新增 `nonbinary_v19_bounded_ml.py`：bounded-weight ML 解码（max_weight=4，numba 加速），
  作为 V19 OSD 全失败后的 post-decoder 集成到 `nonbinary_v19_finite`。
- 在 n=64,m=4,lambda {2:0.6,3:0.4},f≈1.136 的 64 帧上：
  - V19 基线 28/64 exact, FER=0.5625
  - + bounded-ML **31/64 exact, FER=0.515625**
  - 恢复 seeds 2026082260/2144/2192，均用完整管线验证。
- 新增测试 `test_nonbinary_v19_bounded_ml.py`；V20 E01/E02 标记完成。 [repo-observed]

## 2026-08-16 Round 85 — BP-retry 诊断未恢复，V19 全路线穷尽

- 实现并运行 BP 随机先验扰动重试（blind-reconciliation 风格预研）：
  - hard frame 2055：beta=0.01/0.05/0.1/0.2 各 50 次，均未恢复；
    beta=0.5 因数值溢出/超时未完成。
  - seed 2252 的 3 个 mismatch 帧：beta=0.05 各 20 次，均未恢复。
- 至此 V19 已覆盖：PEG/FFT-QSPA、bounded/full OSD、MRB-OSD、rho 变体、
  code-seed sweep、BP-retry，均未把 f≤1.3 的 FER 降到可用水平。
- 下一步唯一可自动推进的是 V20 冻结；否则需用户提供新方向/新数据。 [repo-observed]

## 2026-08-16 Round 84 — V19 OSD/构造穷尽，V20 就绪待冻结

- 新增 `frame_seed` 参数（API + CLI `--frame-seed`），可固定帧数据、更换 code seed。
- hard frame seed 2055 固定帧、code seed 3001-3005 全部 `exact_mismatch`；
  rho 变体 {35,39}/{33,41}/{30,44} 仍失败。
- 直接 MRB-OSD probe（OSD-2 all-free/symbols 4-8、OSD-3/4 bounded、OSD-3 all-free/symbols 2）
  均未找到 Alice 码字；MRB-OSD 对 seed 2252/2276 也无变化。
- 结论：V19 PEG/FFT-QSPA/OSD 家族在 q=1024 f≤1.3 已穷尽。
- V20 proposal/design/tasks 已补充 Round 83-84 证据，标记 ready for freeze review；
  下一步需用户/主线程批准 V20 冻结。 [repo-observed]

## 2026-08-16 Round 83 — n=64 f=1.136 扩样 + MRB-OSD 诊断

- 最佳配置 n=64,m=4,lambda {2:0.6,3:0.4},f≈1.136 扩到 64 帧：
  **28/64 exact_correct, FER=0.5625**（32 帧时 15/32=0.53125；更大样本略差，诚实记录）。
- 同 f 中间块长：n=80,m=5 -> 2/8 exact (FER=0.75)；n=96,m=6 -> 1/8 exact (FER=0.875)。
  n=64 仍是该 f 点最佳。
- 新增 MRB-OSD：`nonbinary_v19_osd.osd_decode_candidates_mrb`（按可靠性升序置换列，
  使最不可靠列优先成为 pivot，信息集偏向最可靠列）；2 个新测试通过。
- `nonbinary_v19_finite` 对 n<=64 自动追加 MRB OSD-1 full + MRB OSD-2 broad。
- 初步对照：seed 2252 5/8、seed 2276 2/8，与旧 OSD 相同；MRB 尚未带来提升，
  下一步在更多 hard seeds / 更高阶 MRB 上评估，或转向 V20 冻结。 [repo-observed]

## 2026-08-16 V19 NBLDPC primary route — ROUTE EXHAUSTED (blocker)

- V19 diagnostics exhausted all current PEG/FFT-QSPA + bounded OSD attempts for
  q=1024 f≤1.3: every configuration yields `exact_mismatch` (0 exact).
- Comprehensive evidence:
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_primary_20260816/n4_finite_q1024_f129_blocker_summary.json`
- Next step is V20 OpenSpec change `formal-nonbinary-ldpc-v20-q1024-decode-improvement`
  (draft exists). No further automatic step is available until that change is frozen/approved.

## 2026-08-16 V19 NBLDPC primary route diagnostics (Route N0-N6 first pass)

- Added V19 nonbinary LDPC modules/CLIs/tests under comparison_bench only:
  `nonbinary_v19_channel.py`, `nonbinary_v19_de_search.py`, `nonbinary_v19_finite.py`,
  `cli/run_v19_nbldpc.py`, `cli/run_v19_three_way_compare.py`, 4 test files (11 passed).
- Evidence package:
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_primary_20260816/`
  - N1 channel: folded q=16 H=0.382911, full q=1024 H=0.549955.
  - N2a warm-started rate ladder from V18-B2 R=0.60 best at 0.65 small budget:
    non-converged, consistent with plain structured ceiling.
  - N2c extended-degree probe (degrees 48/60 at R=0.65): non-converged.
  - N3/N4 finite q=16 n=512 m=205 R≈0.5996 synthetic 4 frames:
    3 exact_correct / 1 exact_mismatch / 0 decode_failed, FER=0.25, f≈4.183.
  - q=1024 progress: `n4_finite_q1024_simple/finite_execute.json` (q=1024,
    n=64, m=24, R=0.625, 2/2 exact_correct, f≈6.819),
    `n4_finite_q1024_n128_simple/finite_execute.json` (q=1024, n=128, m=51,
    R≈0.602, 2/2 exact_correct, f≈7.245), and
    `n2_extended_probe_q1024/extended_degree_probe.json` (tiny DE probe,
    non-converged). `n6_comparison_v2_q1024` includes the q=1024 row and
    `leakage_decomposition.json` (q16 honest f≈3.016; q1024 n128 f≈7.245).
  - N2b capacity bound: `n2b_channel_aware_bounds/lsb_public_capacity.json`
    LSB-public does not reduce ideal f; full q=1024 coding is the binding target.
    Added `build_high_plane_w` and `high_plane_channels.json` for residual
    high-bit effective channels (l=0..6). A tiny q=512 R=0.92 DE probe on the
    l=1 high-plane channel was non-converged. [repo-observed]
  - q=1024 high-rate finite attempts: R=0.840 f=2.912 FER=0.5 (8/16 exact),
    R=0.891 f=1.989 FER=0.8125 (3/16 exact); all mismatches retained;
    `n6_comparison_v3_q1024_rates` records the tradeoff. A further n=1024,
    m=73, R≈0.929, f≈1.296 run ended 4/4 decode_failed (FER=1.0); corrected
    statuses in `n6_comparison_v4_corrected_statuses`. A 30-iteration probe and
    alternate degree-2/3 distributions all still decode_failed at f≈1.296, so
    the next step requires a new OpenSpec change for improved finite-length
    code/decoder design. Added optional `rho_edge` construction and a custom
    3-point rho probe at R=0.875 (`n4_finite_q1024_optrho_n512_m64`) also
    decode_failed. Added bounded single-symbol and two-symbol OSD-like
    postprocessors (`n4_finite_q1024_r089_simple_pp*`), which did not recover
    the tested frames. Added `find_two_degree_rho` and tested normalized
    Müller degree distribution at f≈1.296/f≈1.989; both still decode_failed.
    A longer n=2048,m=133 f≈1.181 attempt also decode_failed. Implemented
    bounded q-ary OSD-0/1 (`nonbinary_v19_osd.py`); R=0.89 q=1024 improved to
    2 exact / 2 exact_mismatch / 0 decode_failed, while f=1.296 n=1024 OSD-0
    still exact_mismatch. Added `osd_decode_candidates` and enumerated all
    OSD-1 single-flip candidates at f=1.296; still no exact match. Added
    bounded OSD-2 candidate search; f=1.296 probe still exact_mismatch, and a
    wider OSD-2 probe (top4/top16, 1531 candidates) also no exact. A PEG seed
    sweep (5 seeds) at f=1.296 all exact_mismatch. max_iter=50 + OSD still
    exact_mismatch (not iteration-limited). n=2048,m=126 f=1.119 OSD also
    exact_mismatch. Improved OSD reliability ordering (max-second-max) still
    exact_mismatch at f=1.296. V18-B2 optimized lambda with exact two-degree
    rho at f=1.296 also exact_mismatch. A 4-frame OSD run at f=1.296 gave
    4/4 exact_mismatch, FER=1.0. At R=0.84 OSD gave 3 exact / 5 mismatch /
    0 decode_failed in an 8-frame run. n=512,m=36 f=1.279 OSD also
    exact_mismatch, and n=128,m=9 bounded OSD also exact_mismatch. However,
    full OSD-1 on n=128,m=9 f=1.279 enumerated 121738 candidates and found
    Alice's codeword — first exact q=1024 f≤1.3 recovery. A second full
    OSD-1 frame at n=128 was not recovered; across four n=128 frames full
    OSD-1 recovered 1/4 exact (FER=0.75). A non-recovered frame also failed
    full OSD-1 + bounded OSD-2 and broad OSD-2 (top20/top4, top20/top16).
    n=64,m=4 f=1.136 full OSD-1 recovered 3/6 frames (FER=0.5); prior retry +
    full OSD-1 and broad OSD-2 also failed on a non-recovered frame; lambda
    {2:0.7,3:0.3} gave 0/2. Broad OSD-2 also failed on non-recovered seeds
    2056/2059. max_iter=50 + full OSD-1 also failed on seed2055; alternate
    code seeds 3001-3004 for the same frame also failed. Full OSD-1 summary:
    n=64 FER=0.6875 (5/16), n=128 FER=0.75 (2/8); broad OSD-2 did not recover
    any of the five n=64 non-recovered frames. Fast full OSD-1 enumeration
    (`osd_decode_candidates_fast`) integrated for n<=256 (~0.6s at n=64).
    Fast broad OSD-2 (`osd_decode_candidates_order2_fast`) also integrated
    for n<=128; fast bounded OSD-3 added; seed2055 still not recovered with
    top12/top8 or OSD-4 top8/top2/top4; fast OSD-1/2/3/4 integrated for
    n<=64, seed2055 still non-recovered. A new n=64 fast OSD-1/2/3/4 batch
    gave FER=0.5 (4/8), second batch 0/8; combined 4/16 FER=0.75.
    seed2055 remained non-recovered after prior-retry + OSD-1/2/3/4 and
    generic OSD order5/6. n=64 fast OSD-1..10 combined FER=0.71875
    (18/64); lambda {2:0.6,3:0.4} gave FER=0.5625 (7/16); lambda
    {2:0.7,3:0.3} gave FER=0.75 (2/8); {2:0.8,3:0.2} also FER=0.75 (2/8);
    {2:0.4,3:0.3,4:0.3} gave FER=0.625 (3/8); {2:0.55,3:0.45} gave
    FER=0.875 (1/8); {2:0.65,3:0.35} gave FER=0.625 (3/8). Best lambda
    {2:0.6,3:0.4} over 24 frames: FER=0.5833 (10/24); at n=128 same lambda
    gave 0/4. {2:0.62,3:0.38} gave 5/16 (FER=0.6875); {2:0.58,3:0.42} gave
    6/16 (FER=0.625); {2:0.59,3:0.41} gave 1/8 (FER=0.875); {2:0.61,3:0.39}
    gave 2/8 (FER=0.75). Best lambda {2:0.6,3:0.4} reached 15/32 exact
    (FER=0.53125). Comprehensive blocker summary
    written into V20 proposal/tasks. Created V20
    OpenSpec draft `formal-nonbinary-ldpc-v20-q1024-decode-improvement`
    (proposal/design/tasks) as the next step. [repo-observed]
  - N6 comparison table vs binary LDPC MLC (f≈4.169, FER=0); Polar MLC row
    `not_available` until clean evidence from `D:\Code\HD-QKD_Polar_Release`.
- Claim boundary: diagnostic_only. Frozen baselines untouched; outputs additive;
  local git commit only; push still user-gated. [decision]

## 2026-08-16 Proper CRC-aided SCL progress

- Implemented v19_polar_crc.py matching frozen C++ check_crc16.
- Plane 9, N=2048, PW-order, CA-SCL list=128 with valid CRC: 13/20 correct vs 0 before.
- FER still ~0.35; next is Tal-Vardy/polar-spectrum construction and/or SCL-flip. [repo-observed]

## 2026-08-16 Decoder improvement plan (literature-grounded)

- Polar path: current CA-SCL does not actually receive CRC bits from our MLC payload; next concrete step is proper CRC-aided SCL integration (reserve 16/24 CRC bits).
- Construction: replace PW/GA with Tal-Vardy quantization or polar-spectrum UBW/SUBW; consider SCL-flip/ADSCL.
- LDPC path: extend binary DE to dc>13 in v19, use MET-LDPC/degree-one VN and rate-compatible puncture/shorten for low-error high-rate planes.
- HD-QKD anchor: Mueller et al. 2024 f≈1.078–1.14 requires full DE-optimized irregular q-ary + blind reconciliation.
- Plan doc: docs/decoder-improvement-plan-20260816.md. [repo-observed, plan]

## 2026-08-16 V19 LDPC DE screener

- Added per-plane BSC DE-gated LDPC screener using frozen `binary_bsc_threshold`.
- With frozen DE bound dc<=13, only planes 8/9 found regular ensembles meeting f≈1.3 target.
- Planes 0–7 require very high-rate codes (small m/N) not reachable by regular dc<=13 LDPC.
- This explains the need for irregular/structured high-rate codes or extended DE tooling. [repo-observed, diagnostic_only]

## 2026-08-16 V19 Polar N=8192 negative result

- Tested N=8192, GA mask, CA-SCL list=128, plane 9, f≈1.3 per-plane target.
- Single frame decode took ~122 s and still failed.
- This closes the Polar/SCL scaling path with the current decoder; next recommendation is a different code family / optimized LDPC DE-gated design. [repo-observed, diagnostic_only]

## 2026-08-16 V19 Polar GA frozen-set attempt

- Added `v19_polar_ga.py` implementing GA/J-function reliability for per-plane BSC Polar construction.
- Tested GA masks with CA-SCL list=128 at N=2048 for planes 9/8/7; still frame errors at f≈1.3 target.
- Combined with earlier PW/MC attempts, cheap frozen-set construction is not sufficient for f≤1.3 with current Polar SC/SCL at N≤4096.
- Future path: larger N, CRC-aided SCL with tailored construction, different code family, or finite-length f relaxation. [repo-observed, diagnostic_only]

## 2026-08-16 V19 CA-SCL experimental decoders (list 32/128)

- Added experimental CA-SCL copies under comparison_bench (not frozen src):
  - `v19_ca_scl.cpp` (list=32), `v19_ca_scl128.cpp` (list=128), compiled DLLs, and wrapper `v19_ca_scl_wrapper.py`.
- Noiseless wrapper test passes; corrected output ordering (C++ returns info bits in ascending index order).
- At N=2048/4096 with PW-order or Monte-Carlo info selection, both list=32 and list=128 still fail to reach f≈1.3 target rates on multiple planes.
- Conclusion: reaching f≤1.3 needs GA/tailored frozen-set construction or a different code family; list size alone is not sufficient. [repo-observed, diagnostic_only]

## 2026-08-16 V19 binary-MLC prototype and high-rate code design attempts

- Added v19 channel scoping CLI: per-plane h2 sum = H_full≈0.549955, ideal binary-MLC f≈1.0.
  Existing binary v4 H1 f≈4.148; v5 H1+H2 f≈6.932. [repo-observed]
- Added v19 binary-MLC prototype using frozen v4 H1 + v5 H2 fallback on V17 per-plane BSC:
  50 frames/plane, 0 failures, average syndrome 587 bits/frame, measured f≈4.169. [repo-observed]
- Exploratory high-rate designs:
  - Random LDPC N=2048 target f≈1.22: many failures.
  - Polar SC and CA-SCL(list=4) N=2048 target f≈1.32: many failures.
  Conclusion: reaching f≤1.3 requires optimized code design (better polar construction/larger list/CRC or optimized LDPC), not naive random or current PW-order SC/SCL. [repo-observed, diagnostic_only]
- Next: v19 DE gate / optimized per-plane code design remains user-gated/new change. [decision]

## 2026-08-16 Route B M2 diagnosis: structured channel is the DE ceiling; QSC control converges

- Route A completed: 128 decode_failed frames are not iteration-limited and not QSC prior mismatch
  (max_iter 200/500, oracle prior, p-grid all failed). [repo-observed, diagnostic_only]
- Route B M0/M1/M1b completed: V18-B1 q=4 DE reproduction gate PASS after M1b correction
  (`threshold_proxy≈0.06758`, delta≈0.00142). [repo-observed]
- Route B M2: implemented structured-DE using V17 per-bit-plane + Gray + fold to q=16.
  Best plain result: rate=0.60, seed 2026081707, f≈4.18 (syndrome 1.6 bits/H_fold 0.3829).
  All rate>0.60 attempts failed (0.61/0.62/0.63/0.65, random and seeded).
  q=32 exploratory searches also all failed. [repo-observed]
- Decisive control: equal-entropy QSC(q=16, p=0.038, H≈0.3815) converged 16/16 at rate 0.63/0.65
  with the same DE budget; folded real structured channel 0/16. Conclusion: **channel structure limits
  plain irregular NB-LDPC DE, not search budget**. [repo-observed, diagnostic_only]
- Next automatic artifacts created: channel-aware DE gate proposal draft and Route C1 design draft.
  Execution of those routes remains a user-gated decision per plan
  `docs/route-b-c-d-next-steps-plan-20260819.md`. [decision]
- Local commits made; push still requires separate user authorization. [repo-observed]

# AGENT_PROJECT_MEMORY.md

## 2026-08-13 Mainline fusion merge — main = db00174d, two lines re-fused

- The local working line is now `main` at merge commit
  `db00174d2d9edb471da5cae159561c04fdf40ccd` (parents `c7853867…` PolarCode
  line + `8338c9e4…` formal-ir line), pushed to origin/main and synced
  (local main == origin/main). Supersedes the 2026-08-12 entry's
  "working branch is formal-ir-accumulation"; that branch is now a
  historical label only. [repo-observed]
- Line history: the local formal IR line (`comparison_bench/`, `openspec/`,
  `formal_ir/`, nonbinary LDPC v1-v12, cascade, ldpc v2-v5) and the remote
  PolarCode line (`pipelines/`, `tools/diagnostics|security_reports`,
  `src/qkd_io`, Route A/B-lite audit, P0/P1 release hygiene: checksum
  verification, `CURRENT_MAINLINE.md`, runtime paths) forked at `b6f61d40`
  and are now re-fused. The merge tree contains both sides completely
  (695 + 215 file diff verified). [repo-observed]
- Six conflict files resolved by policy: add/add → formal-ir version for
  `AGENT_HANDOFF.md`, `AGENT_PROJECT_MEMORY.md`, `wsl-env.sh`; content →
  two-side merge for `.gitignore`, `README.md`,
  `experiments/run_golden_sweep_four_datasets.py`. [decision]
- Local branch cleanup completed: `develop`, `codex/feat/polar-diagnostics-occupancy`,
  `wt-a1..wt-ab` deleted; all worktrees removed (formerly
  `C:/Users/admin/.codex/worktrees/*`). Local branches now only `main`
  (working line) and `formal-ir-accumulation` (historical tip `8338c9e4`,
  kept as label/backup, pushed to origin). [repo-observed]
- Remote branches preserved: origin/main (`db00174d`),
  origin/formal-ir-accumulation (`8338c9e4`),
  origin/codex/feat/polar-diagnostics-occupancy (stale, `e0494156` — do not
  treat as current), origin/project-restructure-20260427 (`0e4f7351`, merged
  into main history). [repo-observed]
- AGENT_PROJECT_MEMORY.md itself was committed in `8338c9e4` (carrying the
  2026-08-12 triage entry); the merge kept the formal-ir version. This entry
  is an uncommitted working-tree addition by design. [repo-observed]
- Still deliberately untracked (user decision: leave for now; they now hang
  on the main worktree): v12 real-micro/partition and ldpc_v5 transfer
  evaluation sources + tests — 8 py files under
  `comparison_bench/src/comparison_bench/{cli,formal_ir}/` and
  `comparison_bench/tests/` — plus
  `outputs_comparison/{final_ir_method_selection,formal_ir_methods,transfer_evaluation}/`,
  the `comparison_bench/新增卷 (D).lnk` Windows shortcut leftover, and
  `workspace/` scratch. Do not commit or delete unprompted. [repo-observed]
- Environment facts: `http.sslBackend schannel` already recorded in §3; local
  proxy 127.0.0.1:7899 had a transient outage during the merge (no durable
  impact); git 2.52.0 in use, supports `merge-tree --write-tree`. [repo-observed]

## 2026-08-12 Formal IR accumulation commit, branch, and push

- Current working branch is `formal-ir-accumulation`, HEAD =
  `189d6c31aa445d0666bd78d32490041a8b14092c` ("feat(formal-ir): accumulate
  formal IR source, tests, CLIs, OpenSpec changes, and agent docs", 342 files,
  +60736/−109), pushed to origin
  (https://github.com/Placebo303/HD-QKD-Polar-pipeline.git) with upstream
  tracking set and remote hash identical. This commit was previously a
  detached-HEAD chain (2bb0d5b → 921d002 → 9666eec → 189d6c3) and is now
  mounted on the new branch; develop (b039dfb), main (2f496c0), and
  codex/feat/polar-diagnostics-occupancy (7085f0b) were not touched.
  [repo-observed]
- Commit contents: `comparison_bench/src/comparison_bench/formal_ir/` (63
  modules: cascade, ldpc, ldpc_v2-v5, codebook_*, nonbinary field/qspa/v2-v11,
  real_qualification.py, long_v3_*), 37 CLIs under `cli/`, `data_lock.py`,
  `final_selection_audit.py`, 79 test files, `requirements-formal-ir.txt`, 2
  comparison_bench docs, 4 root docs, OpenSpec 4 archived + 16 active changes +
  2 new merged spec dirs (`openspec/specs/final-ir-method-selection/`,
  `openspec/specs/formal-ir-methods/`). Frozen baseline `src/`, `experiments/`,
  `tools/`, `results/` zero change; the 111 tracked
  `outputs_comparison/` files zero change. [repo-observed]
- Deliberately NOT committed (untracked, per repo output/scratch policy): all
  `workspace/` scratch roots (145 tracked files exist under them), the
  `outputs_comparison/final_ir_method_selection/` and
  `outputs_comparison/formal_ir_methods/` output directories, and the root
  `新建卷 (D).lnk` Windows shortcut leftover. Do not commit or delete these
  unprompted. [repo-observed]

## 2026-08-11 Nonbinary LDPC V11 spatial-coupling DE gate — failed_coupling, successor guidance

- Change: `formal-nonbinary-ldpc-v11-sc-de-gate`. Final state
  **failed_coupling** (`evidence/decision/final_gate_decision.json`, schema
  `v11_final_gate_decision_v1`, decided 2026-08-11 by main thread, confirmed
  by reviewer-go V11-50.3 independent final acceptance, 16/16 A01-A16 PASS).
  All checks pass (rate/resource/replay/structured/semantic true; gates
  0/3); the provisional `failed_reference` in the execution-root summary was
  a checks-pending placeholder and is superseded by the final decision file.
  [repo-observed, decision]
- Scientific conclusion: the spatial-coupling hypothesis is REJECTED under
  the frozen V10 S1/S3 lambda distributions and the frozen G1 (w=1,L=32,W=8),
  G2 (w=2,L=32,W=16), G3 (w=2,L=32,W=32) geometries. Coupled conservative
  thresholds: S1 G1 .2100 / G2 .2025 / G3 .2019 (gate >= .22, 0/3); S3
  G1 .3125 / G2 .3000 / G3 .3000 (gate >= .32, 0/3); every paired
  conservative gain is negative (S1 -0.0075/-0.0144/-0.0156; S3
  -0.0137/-0.0256/-0.0206). No silent promotion, no "closest to gate", no
  matrix shrink. [repo-observed, decision]
- Successor guidance: after V10 failed_ensemble and V11 failed_coupling,
  design.md §8's simple alternative (stop and honestly report that the
  current uncoupled ensemble family misses the robust gates) is the current
  valid option; V11's spatial-coupling test changed nothing. Any
  finite-length/lifting, windowed FFT-QSPA, decoder, canary, real-data,
  qualification, or promotion work requires a NEW OpenSpec change with fresh
  roots and fresh development/confirmation data. [decision]
- Reference reproduction (V11-10.1/10.2): `formal_ir/nonbinary_v11_smp_de.py`
  reproduces the four published q=4/q=16 SMP-DE anchors (uncoupled + coupled,
  rate-1/2 (3,6), W=30) within frozen tol 0.002 — q=4 uncoupled 0.0890 vs
  0.0888, q=4 coupled 0.0942 vs 0.0945, q=16 uncoupled 0.1075 vs 0.1072,
  q=16 coupled 0.1288 vs 0.1287; coupled gain reproduced in both orders
  (q=4 +0.0057 vs published +0.0052; q=16 +0.0215 vs +0.0213). Sources:
  uncoupled SMP-DE Lázaro et al., arXiv:1906.02537 (Globecom 2019); coupled
  Ben Yacoub et al., AEIT 2019, DOI 10.23919/AEIT.2019.8893373. Trace:
  `evidence/reference/smp_de_trace.json`. [repo-observed]
- Resource facts (reusable for future GF(1024) DE work): full-vector coupled
  MC-DE per-iteration costs at N=2000 — G1 ~2.25 s, G2 ~4.97 s, G3 ~9.89 s,
  uncoupled control ~0.23 s (microbenchmark2.json). numba njit hot-kernel
  integration in `nonbinary_v11_mcde.py` gave 11.65x total speedup (predicted
  serial 777.33 h -> 66.72 h; per-cell 9.5-12.5x). 4-worker batch parallelism
  (#3) gives only 2.04x with per-worker efficiency 0.51 — batch efficiency
  does NOT extrapolate to the uniform 60-task matrix (load imbalance); the
  correct extrapolation is task-level LPT scheduling simulation
  (formal_plan.md §4): 17.1-19.7 h (central 18.9 h), under the 24 h limit.
  Actual execute: 60/60 runs once 2026-08-08, 15.83 h wall < 24 h, peak RSS
  2.82 GiB < 3 GiB. [repo-observed]
- Process precedents (reusable): budget amendments AMEND-2026-08-06-01
  (numba, limited to `nonbinary_v11_mcde.py` hot kernels, scientific
  parameters unchanged) and AMEND-2026-08-06-02 (4-worker parallel executor,
  RSS judged per single-run peak) — both user-approved, engineering-only,
  exactly-once re-measurement with prior evidence unchanged
  (`evidence/resource/microbenchmark{2,3}.json`). The long scientific execute
  ran as a detached background process with executor bookkeeping
  (`nonbinary_v11_execute.py`): progress.json + heartbeat.json (daemon
  thread) + `--resume` (terminal runs never re-run; failed evidence
  immutable) + `--status`. Lesson: batch-efficiency extrapolation
  overestimates for uniform task matrices; use LPT task-level simulation
  (formal_plan.md §4.4). [repo-observed, decision]
- Reusable assets under `comparison_bench/src/comparison_bench/formal_ir/`:
  `nonbinary_v11_smp_de.py` (SMP-DE reference, four reproduced anchors);
  `nonbinary_v11_mcde.py` (full-vector coupled MC-DE kernel, numba hot
  kernels, w=0 byte-identity to V9 uncoupled — covered by the 24 V11 MC-DE
  tests); `nonbinary_v11_execute.py` (threshold bisection + parallel executor
  + gate decision, reusable for any future DE gate work);
  `nonbinary_v11_parallel.py` (worker-pool executor);
  `nonbinary_v11_microbench.py`. [repo-observed]
- Frozen baseline: `src/`, `experiments/`, `tools/`, `results/` zero change;
  regression 87 passed; no new entry under
  `comparison_bench/outputs_comparison/formal_ir_methods/` (A14 PASS). All
  evidence under the change's `evidence/` (reference/, resource/, replay/,
  decision/, formal_plan.{json,md}, literature-review.md). Execute/replay
  roots: `workspace/nbldpc_v11_execute_002d51de/`,
  `workspace/nbldpc_v11_replay_8e63bf62/` (60/60 byte-identical science
  fields). docs/decision-log.md 2026-08-11 entry appended. [repo-observed]

## 2026-08-06 Nonbinary V10 failed_ensemble — final state, no-hash amendment, V11 successor

- Change: `formal-nonbinary-ldpc-v10-de-peg-fftqspa`. Final state
  **failed_ensemble** (`evidence/v10_gate_decision.json`, schema
  `v10_gate_decision_v1`): the V10A GF(1024) four-search density-evolution
  ensemble gate FAILED (hard stop V10-S02). V10-30 (PEG), V10-40 (FFT-QSPA),
  V10-50 (canary), and V10-60 (development) are all HALTED. There is no
  "closest to gate", no rerun, no tuning; no codebook/decoder/canary/
  development/qualification/real-data/promotion output exists under this
  change. [repo-observed]
- V10-0 q=4 reference-recovery gate PASS: conservative threshold 0.06414,
  |δ| = |0.06414 − 0.069| = 0.00486 ≤ 0.012; main-thread accepted
  2026-08-05. [repo-observed]
- V10A searches: S1 (p=.20, f=1.15) conservative 0.2153 < 0.22 FAIL; S2
  (p=.20, f=1.08) conservative 0.1984 < 0.215 FAIL; S3 (p=.30, f=1.15)
  conservative 0.3166 < 0.32 FAIL; S4 (p=.30, f=1.08) no eligible candidate
  FAIL. [repo-observed]
- Execute/replay: V10A executed once (~10470 s, peak RSS 335 MB < 3 GiB);
  first replay attempt interrupted (PID 21032 died, S1 only); per precedent
  `replay_attempt2/` completed 04:36–07:07Z (RSS 339 MB); direct byte
  comparison PASS across 129 files — scientific files byte-identical, only
  provenance normalization differs (plan_binding digest key, run_complete
  role/stage). [repo-observed]
- 2026-08-06 protocol amendment (main-thread): defensive SHA-256/checksum/
  integrity-manifest mechanisms (plan-bound digest, manifest self/source
  hash, per-file compare sha256) removed per AGENTS.md §5.7; replacements
  are git baseline checks, direct byte comparison, structured field
  validation, and semantic recomputation. `v10_seed` is RETAINED as a
  deterministic RNG derivation primitive — DE population initialization and
  mutation RNG streams depend on it and completed results depend on its
  byte reproduction. Amendment record:
  `evidence/v10_protocol_amendment_no_hash_v1.json`. [decision]
- Evidence (change `evidence/`): `v10a_execute_results.json`,
  `v10a_replay_evidence.json`, `v10a_gate_decision.json`,
  `v10_gate_decision.json`, `v10_t3_regression.json` (git baseline PASS,
  frozen directories zero change), `v10_protocol_amendment_no_hash_v1.json`.
  [repo-observed]
- Tests: full V10 suite 89 passed (common 23 / de 24 / gate 13 / peg 12 /
  fftqspa 17). [repo-observed]
- Frozen baseline: git HEAD
  `a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344`; `src/`, `experiments/`,
  `tools/`, `results/` zero change;
  `comparison_bench/outputs_comparison/formal_ir_methods/` has no new V10
  output; the 12 tracked modifications are pre-existing dirty-worktree
  entries of other workflows. [repo-observed]
- V10-30.DESIGN task (PEG no-hash design note) remains unchecked and is
  left for future V11 inheritance. [repo-observed]
- Close-out (2026-08-06): `evidence/v10_s4_delta_correction.json` (schema
  `v10_s4_delta_correction_v1`) records the S4 `delta` boolean-false /
  null-semantics correction (build_evidence short-circuit bug); evidence
  immutable, script expression fixed; reviewer-go final review ACCEPT
  (`evidence/v10_independent_review_acceptance.json`, schema
  `v10_independent_review_acceptance_v1`, 89 tests pass). [repo-observed]
- Successor: a brand-new V11 NB-SC-LDPC OpenSpec change (fresh everything:
  new change, new roots, new development/confirmation data); starting V11 is
  a user decision; nothing further is authorized under V10. [decision]
- Archived (2026-08-06): change directory moved to
  `openspec/changes/archive/2026-08-06-formal-nonbinary-ldpc-v10-de-peg-fftqspa/`
  (equivalent rename; delta specs not merged; local commit, not pushed).
  [repo-observed]

## 2026-08-06 Research Code Engineering Policy (AGENTS.md §5.7)

- Change `research-code-engineering-policy` implemented via the OpenSpec flow;
  policy now lives at AGENTS.md §5.7 (lines 80-110) and was reviewed ACCEPT by
  reviewer-go (no blocking items). Not yet archived; archive action pending
  user decision. [repo-observed]
- Core requirements: this repository is local research code, not a production
  service. Unless a task explicitly requires it, do not add checksums/integrity
  manifests, atomic/transactional writes, backup/rollback, file locking,
  elaborate schema validation, retry frameworks, security hardening,
  compatibility layers, custom caching, or exception handling that hides
  errors. Assume trusted local inputs, manual single-machine runs, rerunnable
  failures, and Git version control. Prioritize scientific/numerical
  correctness, explicit units/assumptions/parameters, readable calculations,
  reproducible seeds, validation against known limits, clear errors, and
  minimal dependencies/abstraction. Identify the concrete failure mode before
  adding any defensive mechanism; do not generalize one-off scripts into
  production frameworks. [repo-observed]
- Scope: only AGENTS.md and the openspec change directory; frozen baseline
  (src/, experiments/, tools/, results/) untouched. Pre-existing dirty files
  (AGENT_HANDOFF.md, CURRENT_TASK.md, AGENT_PROJECT_MEMORY.md,
  docs/decision-log.md, AGENTS.md §10.1) belong to earlier work, not this
  change. [repo-observed]

## 2026-08-04 V9A GF(1024) long-block ensemble gate STOP

- Change: `formal-nonbinary-ldpc-v9-gf1024-long-ir`.
- V9A executed once under the frozen v2 budget protocol (pid 5084, 3968.5 s,
  peak RSS 428.3 MiB) and strict-replayed once (pid 29340, 4838.5 s). Scientific
  outputs are deterministic and byte-identical between execute and replay; only
  `run_meta.json` differs in provenance fields.
- All four searches (S1 robust gate .22, S2 target gate .215, S3 robust gate
  .32, S4 target gate .32) recorded zero eligible candidates; every gate FAILS.
- Conservative threshold undefined for every gate; downstream tier selection is
  null for both strata.
- Decision: frozen STOP before any finite codebook. V9B/V9C unreachable. No
  codebook, decoder, canary, development, qualification, real/N4 data,
  promotion, or formal comparison is authorized under this change.
- Evidence files under
  `openspec/changes/formal-nonbinary-ldpc-v9-gf1024-long-ir/evidence/`:
  `v9_00_freeze.json`, `v9a_plan_v2.json`, `v9a_execute_results.json`,
  `v9a_replay_evidence.json`, `v9a_gate_decision.json`,
  `v9a_interrupted_trial_freeze.json`, `v9a_interrupted_v2_attempt_freeze.json`,
  `v9a_independent_review_acceptance.json`.
- Process note: the replay script overwrote the shared
  `evidence/v9a_execute_results.json` path because it lacked a guard on that
  file; the orchestrator restored the original execute version from
  `workspace/v9a_04c9e7d25d7145659685415084d6fac7/v2_execute/`. Scientific
  impact: none (payload identical; only provenance fields changed); the missing
  guard is a process improvement for future changes, not a scientific defect.
- Close-out complete (2026-08-04): reviewer-go independent review verdict
  ACCEPT — all checklist items pass (matches OpenSpec spec, tests pass, no
  scope creep, decision log updated, V9B/V9C artifacts absent, scientific
  wording scoped), no blocking issues.
- Independent hash verification: 9/11 files byte-identical between execute and
  replay; 2 differ only in provenance (`evidence_v9a_execute_results.json`,
  `run_meta.json`). `S4.progress.jsonl` known hash verified:
  80ee59eb194c60a897ac43d4b09a5d1fd4ff76c8bd0a7394a155606e7cfc632a (this
  supersedes the `TO_BE_COMPUTED_BY_INDEPENDENT_REVIEWER` placeholder in
  `v9a_replay_evidence.json`).
- Change status: STOPPED at the V9A ensemble gate; will NOT advance to V9B/V9C.
  Close-out checklist V9A-C1 through V9A-C8 all checked. The change is
  archive-ready pending the archive action (`/opsx-archive`).
- Scientific boundary: the frozen 8-candidate V9A bounded enumeration failed
  its preregistered gates. This is NOT a general negation of GF(1024) LDPC and
  not a claim that complete ensemble optimization was exhausted; a successor
  requires a new OpenSpec change with fresh roots, a different ensemble family,
  and new development/confirmation data.
- Next: archive the change (OpenSpec archive action). No further work is
  authorized under this change.

## 2026-07-26 Nonbinary N3 evidence boundary

`nbldpc_formal_v1` completed its only frozen q=1024 synthetic N3 execution at
`comparison_bench/outputs_comparison/formal_ir_methods/20260726_v1_nbldpc_synthetic`.
Selected policy SHA `23a1b46300f1c841eed3ffc6f672840c7be17608260de6b09944cac74228983d`
was margin 7/scale 1.0/max_iter 10 with 32 checks in both strata. Confirmation
was non-promoted: p=.20 18/32 verified success and p=.30 5/32, both below the
31/32 gate; N4, reruns, and tuning are forbidden. The official strict verifier
failed only because post-execution whole-worktree git-status provenance drifted.
Source/CLI/contract hashes, commit, Python and NumPy matched; `_test_only=True`
diagnostic replay is not an official verifier pass. Preserve all seven artifacts.

## 1. Project Identity
- Project name: `HD-QKD_Polar_Comparison` [repo-observed]
- Research purpose: evaluate and compare information reconciliation (IR) methods for high-dimensional QKD data, while preserving the copied Polar pipeline as a frozen baseline and adding a separate comparison layer. [repo-observed]
- Main scientific/engineering objective: build a reproducible, non-invasive benchmark layer that can (a) read/import existing Polar results, (b) run executable comparison baselines on synthetic and real paired-symbol frame data, and (c) generate comparable CSV/Parquet/summary outputs without changing the original Polar workflow semantics. [repo-observed]
- Current maturity: mixed. The original Polar repository appears to be a mature replay/security/reporting codebase; `comparison_bench/` is an additive benchmark layer with working CLIs, tests, real-data imported Polar baseline, real-data/synthetic executable baselines, and v3 parameter-sweep/report outputs. [repo-observed]

## 2. Repository Structure Observed
- Top-level directories observed: `analysis/`, `comparison_bench/`, `docs/`, `experiments/`, `results/`, `src/`, `tools/`, `workspace/` [repo-observed]
- Top-level files observed: `README.md`, `requirements.txt`, `bootstrap_clone_clean.py`, `wsl-env.sh`, `LICENSE`, `.gitignore` [repo-observed]
- Original pipeline entrypoints:
  - `experiments/run_e2e_pipeline.py` [repo-observed]
  - `experiments/run_real_polar_max_pie.py` [repo-observed]
  - `experiments/run_golden_sweep_driver.py` [repo-observed]
  - `experiments/run_golden_sweep_four_datasets.py` [repo-observed]
- Original source areas:
  - `src/qkd_io/ttbin_pipeline.py` [repo-observed]
  - `src/workflow/coarse_grain_joint.py` [repo-observed]
  - `src/workflow/export_joint_sequence_sidecar.py` [repo-observed]
  - `src/workflow/llr_from_joint.py` [repo-observed]
  - `src/reconciliation/real_polar_sc_rescue.py` [repo-observed]
  - `src/reconciliation/cpp_scl_wrapper.py` [repo-observed]
  - `src/reconciliation/verification.py` [repo-observed]
  - `src/reconciliation/cpp_polar/` containing `.dll`, `.exe`, and C++ files [repo-observed]
- Original tooling area includes many audit/security/reporting scripts, for example:
  - `tools/longrun_build_replay_index.py` [repo-observed]
  - `tools/longrun_run_actual_ir_replay.py` [repo-observed]
  - `tools/longrun_build_finite_key_audit_table.py` [repo-observed]
  - `tools/longrun_build_security_master_table.py` [repo-observed]
  - `tools/minrerun_run_frame_audit.py` [repo-observed]
  - `tools/minrerun_rebuild_security_master_20dB.py` [repo-observed]
  - `tools/routeA_run_formal_cross_loss.py` [repo-observed]
- Comparison layer structure:
  - `comparison_bench/README.md` [repo-observed]
  - `comparison_bench/requirements-comparison.txt` [repo-observed]
  - `comparison_bench/configs/benchmark_realdata.yaml` [repo-observed]
  - `comparison_bench/configs/benchmark_synth.yaml` [repo-observed]
  - `comparison_bench/configs/cascade_param_sweep.yaml` [repo-observed]
  - `comparison_bench/configs/layered_ldpc_param_sweep.yaml` [repo-observed]
  - `comparison_bench/configs/qldpc_param_sweep.yaml` [repo-observed]
  - `comparison_bench/configs/ir_methods_v3_master.yaml` [repo-observed]
  - `comparison_bench/docs/architecture.md` [repo-observed]
  - `comparison_bench/docs/data_contract.md` [repo-observed]
  - `comparison_bench/docs/method_notes.md` [repo-observed]
  - `comparison_bench/src/comparison_bench/cli/` with:
    - `build_dataset.py` [repo-observed]
    - `run_benchmark.py` [repo-observed]
    - `compare_methods.py` [repo-observed]
    - `smoke_test.py` [repo-observed]
    - `run_cascade_param_sweep.py` [repo-observed]
    - `run_layered_ldpc_param_sweep.py` [repo-observed]
    - `run_qldpc_param_sweep.py` [repo-observed]
    - `run_ir_v3_master.py` [repo-observed]
    - `make_report_tables.py` [repo-observed]
  - `comparison_bench/src/comparison_bench/io/` with:
    - `pairs_loader.py` [repo-observed]
    - `dataset_builder.py` [repo-observed]
    - `polar_existing_bridge.py` [repo-observed]
    - `table_store.py` [repo-observed]
  - `comparison_bench/src/comparison_bench/methods/` with:
    - `cascade_lite.py` [repo-observed]
    - `layered_ldpc_lite.py` [repo-observed]
    - `qldpc_reference.py` [repo-observed]
    - `qary_ldpc.py` [repo-observed]
    - `polar_existing.py` [repo-observed]
    - `base.py` [repo-observed]
  - `comparison_bench/src/comparison_bench/pipeline/` with:
    - `run_ir_benchmark.py` [repo-observed]
    - `merge_with_security.py` [repo-observed]
  - `comparison_bench/src/comparison_bench/sweep/` with:
    - `runtime.py` [repo-observed]
    - `common.py` [repo-observed]
    - `rows.py` [repo-observed]
  - `comparison_bench/tests/` with six current test files [repo-observed]
- Historical context from prior work:
  - real-data imported Polar baseline was matched against a real result root under a legacy Windows data path. [memory-derived]
  - representative sidecar frame batches were built from real paired-symbol sidecar exports. [memory-derived]

## 3. Execution Environment
- Expected OS: Windows host environment is directly observed; WSL support is also explicitly provisioned via `wsl-env.sh`. [repo-observed]
- Expected Python/MATLAB/Octave/other runtime:
  - Python with `numpy`, `pandas`, `numba`, `tqdm` from root `requirements.txt` [repo-observed]
  - optional comparison dependencies: `pyyaml`, `pyarrow`, `pytest` from `comparison_bench/requirements-comparison.txt` [repo-observed]
  - compiled Polar binaries exist under `src/reconciliation/cpp_polar/` (`.dll`, `.exe`) [repo-observed]
  - MATLAB/Octave usage is [uncertain]; no current comparison harness file directly invokes them, but prior planning discussed possible external hooks. [memory-derived]
- Known environment constraints:
  - PowerShell profile loading emits execution-policy warnings in this environment. [memory-derived]
  - git commit/stage operations may fail due to `.git/index.lock` permission issues. [memory-derived]
  - git push over HTTPS to GitHub can fail with `SSL certificate OpenSSL verify result: unable to get local issuer certificate (20)`; fixed on this host via `git config --global http.sslBackend schannel` (global host-level config, not repo content — other hosts may need the same fix). [memory-derived]
  - pytest cache/temp directories can trigger permission-denied warnings. [memory-derived]
  - some outputs may fall back from parquet to pickle if parquet support is missing. [repo-observed]
- WSL migration notes:
  - `wsl-env.sh` sets `PROJECT_DATA_ROOT`, `PROJECT_RESULTS_ROOT`, `TMPDIR`, and `PIP_CACHE_DIR` to POSIX-style defaults. [repo-observed]
  - For WSL work, prefer `/mnt/...` or project-relative POSIX paths, not Windows absolute paths. [repo-observed]
  - Historical Windows data/result paths should be treated as provenance only, not future execution defaults. [repo-observed]

## 4. Main Workflows

### Workflow: original Polar end-to-end pipeline
- entrypoint: `experiments/run_e2e_pipeline.py` [repo-observed]
- input: raw `.ttbin`-derived or paired-sequence materialization inputs [repo-observed]
- output: Polar evaluation artifacts under repository result directories [repo-observed]
- safe smoke command: [uncertain]
- heavy command, if known: [uncertain]
- do-not-run-by-default commands:
  - `experiments/run_e2e_pipeline.py` on raw data, because this is the core heavy baseline workflow and should not be rerun casually. [repo-observed]

### Workflow: original real Polar sweep / max PIE
- entrypoint: `experiments/run_real_polar_max_pie.py` [repo-observed]
- input: cached grid/source tables or materialized real-data intermediates [memory-derived]
- output: Polar result tables such as `polar_diag_summary.csv`, `polar_e2e_results.csv`, or related CSVs [memory-derived]
- safe smoke command: [uncertain]
- heavy command, if known: [uncertain]
- do-not-run-by-default commands:
  - `experiments/run_real_polar_max_pie.py` against raw or large real-data inputs by default. [repo-observed]

### Workflow: replay / security / audit aggregation
- entrypoint:
  - `tools/longrun_build_replay_index.py` [repo-observed]
  - `tools/longrun_run_actual_ir_replay.py` [repo-observed]
  - `tools/longrun_build_finite_key_audit_table.py` [repo-observed]
  - `tools/longrun_build_security_master_table.py` [repo-observed]
- input: prior Polar logs/results and audit/replay inputs [repo-observed]
- output: audit/shadow/master security summaries under result directories [repo-observed]
- safe smoke command: [uncertain]
- heavy command, if known: [uncertain]
- do-not-run-by-default commands:
  - any `longrun_*` or `minrerun_*` scripts unless explicitly asked. [repo-observed]

### Workflow: real-data / synthetic comparison benchmark
- entrypoint:
  - `python -m comparison_bench.src.comparison_bench.cli.build_dataset` [repo-observed]
  - `python -m comparison_bench.src.comparison_bench.cli.run_benchmark` [repo-observed]
  - `python -m comparison_bench.src.comparison_bench.cli.compare_methods` [repo-observed]
- input:
  - paired symbol tables with normalized columns [repo-observed]
  - or sidecar directories containing `a_eff.npy`, `b_eff.npy`, and optional `sidecar_meta.json` [repo-observed]
  - benchmark YAML configs under `comparison_bench/configs/` [repo-observed]
- output:
  - `comparison_bench/outputs_comparison/ir_benchmark_results.csv` [repo-observed]
  - `comparison_bench/outputs_comparison/ir_frame_results.parquet` [repo-observed]
  - `comparison_bench/outputs_comparison/run_manifest.json` [repo-observed]
  - `comparison_bench/outputs_comparison/ir_method_summary.csv` [repo-observed]
- safe smoke command:
  - `python -m comparison_bench.src.comparison_bench.cli.smoke_test --config comparison_bench/configs/benchmark_synth.yaml` [repo-observed]
- heavy command, if known:
  - `python -m comparison_bench.src.comparison_bench.cli.run_benchmark --config comparison_bench/configs/benchmark_realdata.yaml` [repo-observed]
- do-not-run-by-default commands:
  - full real-data benchmark on all sidecars or all frames unless explicitly requested. [memory-derived]

### Workflow: v3 IR method parameter sweeps
- entrypoint:
  - `python -m comparison_bench.src.comparison_bench.cli.run_cascade_param_sweep --config comparison_bench/configs/cascade_param_sweep.yaml` [repo-observed]
  - `python -m comparison_bench.src.comparison_bench.cli.run_layered_ldpc_param_sweep --config comparison_bench/configs/layered_ldpc_param_sweep.yaml` [repo-observed]
  - `python -m comparison_bench.src.comparison_bench.cli.run_qldpc_param_sweep --config comparison_bench/configs/qldpc_param_sweep.yaml` [repo-observed]
  - `python -m comparison_bench.src.comparison_bench.cli.run_ir_v3_master --config comparison_bench/configs/ir_methods_v3_master.yaml` [repo-observed]
- input:
  - frame-batch parquet built under `comparison_bench/outputs_comparison/` [repo-observed]
  - sweep YAML configs [repo-observed]
- output:
  - `cascade_param_sweep_results.csv` and frame/diagnostic companions [repo-observed]
  - `layered_ldpc_param_sweep_results.csv` and frame/diagnostic companions [repo-observed]
  - `qldpc_param_sweep_results.csv` and frame/diagnostic companions [repo-observed]
  - `run_errors_ir_v3.csv` [repo-observed]
  - `ir_v3_run_manifest.json` [repo-observed]
- safe smoke command:
  - there is no dedicated tiny smoke CLI; the lightest current path is to restrict configs before running. [uncertain]
- heavy command, if known:
  - `python -m comparison_bench.src.comparison_bench.cli.run_ir_v3_master --config comparison_bench/configs/ir_methods_v3_master.yaml` [repo-observed]
- do-not-run-by-default commands:
  - v3 master runner or any full representative/all-point sweep in a fresh environment without confirming output policy first. [repo-observed]

### Workflow: v3 report table generation
- entrypoint: `python -m comparison_bench.src.comparison_bench.cli.make_report_tables --config comparison_bench/configs/ir_methods_v3_master.yaml` [repo-observed]
- input: existing v3 sweep CSV outputs [repo-observed]
- output: `comparison_bench/outputs_comparison/report_tables_v3/` CSV tables [repo-observed]
- safe smoke command: same as entrypoint, but only after sweep outputs already exist. [repo-observed]
- heavy command, if known: same as entrypoint; relatively lighter than the sweep commands. [repo-observed]
- do-not-run-by-default commands:
  - none obvious beyond not pointing it at incomplete/missing sweep outputs. [repo-observed]

## 5. Data and Result Policy
- raw data directories:
  - raw real data is external to the repo. Historical provenance includes a legacy Windows path under `D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s` [memory-derived, legacy Windows path]
  - WSL default logical data root is `PROJECT_DATA_ROOT=/mnt/d/Data` from `wsl-env.sh`. [repo-observed]
- result/output directories:
  - original result area: `results/` [repo-observed]
  - comparison result area: `comparison_bench/outputs_comparison/` [repo-observed]
- checkpoint directories:
  - `comparison_bench/outputs_comparison/` contains run manifests and append-only sweep outputs, effectively acting as benchmark checkpoints. [repo-observed]
  - external run/checkpoint roots may exist outside the repo; treat them as [uncertain] unless explicitly mounted. [uncertain]
- files/directories agents must not overwrite:
  - `results/` and anything under it unless explicitly requested. [repo-observed]
  - `comparison_bench/outputs_comparison/` existing benchmark results, diagnostics, manifests, test fixtures, or summaries unless explicitly requested. [repo-observed]
  - raw data outside the repo. [repo-observed]
  - original Polar outputs imported by `polar_existing` bridge. [repo-observed]
- preferred new-output naming convention:
  - new comparison outputs should stay under `comparison_bench/outputs_comparison/` and use additive names consistent with current patterns such as `*_results.csv`, `*_frame_results.parquet`, `*_diagnostics.csv`, `*_manifest.json`, or nested subdirectories like `report_tables_v3/`. [repo-observed]

## 6. Schema and Interface Contract
- CSV columns that must not silently change:
  - normalized input columns: `frame_id`, `pair_idx`, `alice_symbol`, `bob_symbol` [repo-observed]
  - propagated metadata columns: `loss_db`, `dimension`, `bin_width_ps`, `n_eff_pairs`, `threshold_ps`, `effective_pairing_window_ps`, `processing_rule_version`, `pairing_path_tag` [repo-observed]
  - benchmark output columns include at least:
    - `dataset_id`, `data_mode`, `source_path`, `loss_db`, `dimension`, `bin_width_ps`, `n_eff_pairs`, `frame_len_symbols`, `frame_len_bits`, `method`, `method_variant`, `method_status`, `processing_rule_version`, `pairing_path_tag`, `threshold_ps`, `effective_pairing_window_ps`, `n_frames_total`, `n_frames_attempted`, `n_frames_success`, `n_frames_failed_decode`, `n_frames_failed_verify`, `accepted_frame_fraction`, `rejected_frame_fraction`, `raw_ser`, `raw_ber`, `post_ir_ser`, `post_ir_ber`, `leak_EC_actual_bits`, `leak_EC_per_frame`, `leak_EC_per_input_bit`, `beta_eff_empirical`, `runtime_s`, `throughput_input_bits_per_s`, `throughput_output_bits_per_s`, `notes`, `backend_status`, `error_message`, `real_ir_success`, `success_classification` [repo-observed]
  - frame-level output columns include at least:
    - `dataset_id`, `method`, `frame_idx`, `decode_success`, `verify_success`, `raw_frame_ser`, `raw_frame_ber`, `post_frame_ser`, `post_frame_ber`, `leak_bits_frame`, `iterations_used`, `runtime_ms` [repo-observed]
- JSON/YAML keys that must not silently change:
  - `datasets`, `methods`, `global` in benchmark YAMLs [repo-observed]
  - `output_dir`, `max_workers`, `frame_batch_path`, `polar_results_root`, `data_mode`, `frame_len_symbols`, `max_frames_per_dataset` in real-data benchmark YAML [repo-observed]
  - sweep config sections: `cascade`, `layered_ldpc`, `qldpc`, plus `cascade_config`, `layered_ldpc_config`, `qldpc_config` in the v3 master YAML [repo-observed]
- CLI arguments that must not silently change:
  - `build_dataset.py`: `--input`, `--output`, `--dimension`, `--frame-len-symbols`, `--dataset-id`, `--scan-sidecars` [repo-observed]
  - `build_representative_subset.py`: `--input`, `--output` [repo-observed]

  - `run_benchmark.py`: `--config` [repo-observed]
  - `compare_methods.py`: `--input`, `--output` [repo-observed]
  - `smoke_test.py`: `--config` [repo-observed]
  - `run_cascade_param_sweep.py`: `--config` [repo-observed]
  - `run_layered_ldpc_param_sweep.py`: `--config` [repo-observed]
  - `run_qldpc_param_sweep.py`: `--config` [repo-observed]
  - `run_ir_v3_master.py`: `--config` [repo-observed]
  - `make_report_tables.py`: `--config` [repo-observed]
- config keys that must not silently change:
  - method names: `polar_existing`, `cascade_lite`, `layered_ldpc_lite`, `qldpc_reference` [repo-observed]
  - v3 sweep keys including `block_size_schedule`, `num_passes`, `permutation_mode`, `seed`, `verify_mode`, `frame_caps`, `parity_fraction`, `max_iter`, `osd_order`, `bp_method`, `mapping`, `llr_mode`, `bitplane_rate_mode`, `check_fraction`, `row_weight`, `decoder`, `channel_model` [repo-observed]
- function signatures that must not silently change:
  - `FrameBatch`, `IRRunConfig`, `IRRunResult` dataclass fields in `comparison_bench/src/comparison_bench/types.py` [repo-observed]
  - `load_pairs_table(path: Path) -> pd.DataFrame` [repo-observed]
  - `normalize_pair_columns(df: pd.DataFrame) -> pd.DataFrame` [repo-observed]
  - `build_frame_batch(...) -> FrameBatch` [repo-observed]
  - `locate_existing_polar_outputs() -> list[Path]` and `run_polar_existing(batch: FrameBatch, cfg: IRRunConfig) -> IRRunResult` [repo-observed]
- output file naming conventions:
  - base benchmark outputs: `ir_benchmark_results.csv`, `ir_frame_results.parquet`, `run_manifest.json`, `ir_method_summary.csv` [repo-observed]
  - v3 outputs: `cascade_param_sweep_results.csv`, `layered_ldpc_param_sweep_results.csv`, `qldpc_param_sweep_results.csv`, `run_errors_ir_v3.csv`, `ir_v3_run_manifest.json`, `report_tables_v3/*.csv` [repo-observed]

## 7. Baseline and Scientific Semantics
- baseline algorithms:
  - original imported baseline: `polar_existing` [repo-observed]
  - executable classical baseline: `cascade_lite` [repo-observed]
  - executable binary LDPC baseline: `layered_ldpc_lite` [repo-observed]
  - q-ary reference baseline: `qldpc_reference` [repo-observed]
- current assumptions:
  - original Polar code is frozen and must be treated as read-only baseline logic. [repo-observed]
  - comparison layer is outer-wrapper only; it should read existing Polar outputs first and only use CLI mode if explicitly configured. [repo-observed]
  - `cascade_lite` is an internal simplified multi-pass parity/bisection baseline, not a full industrial Cascade transcript implementation. [repo-observed]
  - `layered_ldpc_lite` is a binary bit-plane baseline using `ldpc.BpOsdDecoder` when available, with explicit failure statuses rather than fake success. [repo-observed]
  - `qldpc_reference` currently represents a reference-grade q-ary decoder path, not a production qLDPC system. [memory-derived]
- high-risk variables:
  - `dimension` / `q` [repo-observed]
  - `bin_width_ps` [repo-observed]
  - `frame_len_symbols` [repo-observed]
  - `parity_fraction` [repo-observed]
  - `max_iter` [repo-observed]
  - `mapping` (`gray` vs `natural`) [repo-observed]
  - `llr_mode` and `bitplane_rate_mode` in layered LDPC sweeps [repo-observed]
  - `block_size_schedule`, `num_passes`, and `permutation_mode` in Cascade sweeps [repo-observed]
- known coupling/confounding factors:
  - raw SER and dimension are strongly coupled to decode success on real-data representative points. [memory-derived]
  - imported `polar_existing` point-level results are not always frame-identical to executable baseline frame subsets. [memory-derived]
  - leakage numbers are method-specific decompositions and should only be compared when the decomposition semantics remain consistent. [repo-observed]
  - sidecar-derived frame batches depend on `a_eff.npy` / `b_eff.npy` plus sidecar metadata, so path/layout assumptions matter. [repo-observed]
- metrics that must preserve meaning:
  - `raw_ser`, `raw_ber`, `post_ir_ser`, `post_ir_ber` [repo-observed]
  - `leak_EC_actual_bits`, `leak_EC_per_frame`, `leak_EC_per_input_bit` [repo-observed]
  - `accepted_frame_fraction`, `rejected_frame_fraction` [repo-observed]
  - `n_frames_success`, `n_frames_failed_decode`, `n_frames_failed_verify` [repo-observed]
  - `beta_eff_empirical` must remain derived from leakage and error inputs, not hand-filled. [repo-observed]

## 8. Known Issues and Fragile Points
- path issues:
  - original and comparison workflows have historical Windows-specific path usage; these must be translated deliberately for WSL. [repo-observed]
  - `polar_existing_bridge.py` still contains a legacy Windows default for `DEFAULT_POLAR_RESULTS_ROOT`; treat that as historical provenance, not a future path contract. [repo-observed, legacy Windows path]
- environment issues:
  - git commit/stage may fail because `.git/index.lock` cannot be created. [memory-derived]
  - PowerShell profile warnings are noisy but not necessarily fatal. [memory-derived]
  - optional parquet/YAML dependencies may be missing, causing fallback behavior. [repo-observed]
- data format issues:
  - sidecar directories are directory-based datasets, not flat CSV files. [repo-observed]
  - `load_pairs_table()` supports CSV, parquet/pickle, and sidecar directories; unsupported formats will fail. [repo-observed]
  - comparison outputs also contain test fixtures and temporary pytest artifacts under `comparison_bench/outputs_comparison/`; do not treat those as production outputs. [repo-observed]
- numerical/scientific interpretation risks:
  - `polar_existing` imported results may legitimately contain `NaN` for fields absent from source tables, especially leakage/runtime supplements. [memory-derived]
  - `qldpc_reference` results must not be described as full industrial qLDPC results unless method status and notes explicitly justify that. [repo-observed]
  - `cascade_lite` strong performance in representative sweeps should not be overinterpreted as final paper-grade evidence without broader sweeps. [memory-derived]
  - `layered_ldpc_lite` failure regions may reflect multiple causes: high raw SER, short frame length, parity allocation, or bit-plane independence assumptions. [memory-derived]
- long-running commands:
  - any `longrun_*`, `minrerun_*`, or `routeA_*` tooling under `tools/` [repo-observed]
  - real-data benchmark sweeps and `run_ir_v3_master` can be substantial even with representative subsets. [repo-observed]

## 9. Agent Operating Constraints
- minimal patch only. [repo-observed]
- no broad refactoring of original repository structure. [repo-observed]
- no raw data modification. [repo-observed]
- no result overwrite in `results/` or `comparison_bench/outputs_comparison/` unless explicitly asked. [repo-observed]
- no baseline semantic change to the copied Polar workflow. [repo-observed]
- no schema change unless explicitly requested. [repo-observed]
- WSL/POSIX path default for future harness and agent docs. [repo-observed]
- treat legacy Windows paths as provenance only; do not bake them into new harness defaults. [repo-observed]
- preserve current CLI names, config keys, output file names, and CSV field names. [repo-observed]
- do not silently convert `reference`, `stub`, `unavailable`, `decode_failed`, or `no_verified_success` into `ok`. [memory-derived]
- follow AGENTS.md §5.7 Research Code Engineering Policy: local research code, simplest scientifically correct implementation, no unrequested defensive machinery (checksums, locking, retries, etc.). [repo-observed]

## 10. Unknowns To Verify
- Which original `docs/` files inside this repo are authoritative versus copied from another upstream state. [uncertain]
- Whether MATLAB/Octave is actually required anywhere in this repository copy. [uncertain]
- Whether the original Polar front-half and replay/security scripts are fully runnable in WSL without binary/toolchain adjustments. [uncertain]
- Whether `src/reconciliation/cpp_polar/` binaries are Windows-only in practice or have a portable rebuild path documented elsewhere. [uncertain]
- Whether all existing v3 comparison outputs should be treated as canonical or as exploratory benchmark artifacts. [uncertain]
- Whether any additional AGENTS-style repository guidance already exists outside the scanned paths. [uncertain]
- Whether the external real raw-data root used historically is mounted in the target WSL environment. [uncertain]
- Whether AGENTS.md §10.1 items 7 and 11 should be revised to remove hash wording
  ("self-hashes recomputed", "hashes for untracked files"): this conflicts with
  §5.7 and the 2026-08-06 no-hash amendment, and is a pending main-thread
  decision (noted in `evidence/v10_protocol_amendment_no_hash_v1.json`);
  revising AGENTS.md would require a separate OpenSpec change. [decision-pending]

## 11. Multi-Agent Workflow Files

### Created (2026-06-15)
- `AGENTS.md` — repository-level agent rules (baseline protection, output policy, schema stability, path discipline, agent constraints, OpenSpec workflow). [created]
- `docs/decision-log.md` — durable decisions and rejected alternatives. [created]
- `docs/troubleshooting.md` — reusable failure modes and fixes. [created]
- `openspec/project.md` — project-level context for OpenSpec change management. [created]
- `openspec/changes/real-ir-success-first/` — active change proposal details. [created]
- `CURRENT_TASK.md` — current active documentation/workflow task. [created]
- `RUN_COMMANDS.md` — curated smoke/benchmark/do-not-run command list. [created]
- `REVIEW_CHECKLIST.md` — review checklist for baseline protection and schema stability. [created]
- `AGENT_HANDOFF.md` — concise handoff note for the next agent. [created]
- `comparison_bench/src/comparison_bench/metrics/success.py` — success classification module. [created]
- `comparison_bench/src/comparison_bench/cli/build_representative_subset.py` — representative subset extractor. [created]
- `comparison_bench/configs/benchmark_representative.yaml` — representative subset benchmark config. [created]
- `comparison_bench/tests/test_success_classifier.py` — success classification unit tests. [created]
- `docs/real-ir-success-audit-20260615.md` — audit report summarizing baseline evaluations on representative frames. [created]

### Current OpenSpec state (verified 2026-07-25)
- Phase 0 reconciliation is `docs/openspec-phase0-reconciliation-20260725.md`.
  All five historical IR changes remain active: `real-ir-success-first` has
  32/34 evidenced tasks; optimization has 14/14 tasks but lacks its written
  512/1024-symbol evidence; expanded evidence has 19/20; evidence-package
  has 26/26 tasks but lacks clean direct fixed-path pytest and a before/after
  non-modification proof; group-meeting has 21/29 and lacks its frame-count,
  expected-config/test, and clean-full-suite requirements. Do not archive any
  historical change from artifact presence alone. [repo-observed]
- `final-ir-method-selection` was archived on 2026-07-25 at
  `openspec/changes/archive/2026-07-25-final-ir-method-selection/`; its
  canonical specification is `openspec/specs/final-ir-method-selection/spec.md`.
  It is the bounded comparison protocol that
  ranks only executable `cascade_lite` and `layered_ldpc_lite`; qLDPC remains
  `reference_only`, and `polar_existing` is historical, non-frame-identical
  context. It requires group-disjoint tuning/confirmation, one frozen global
  configuration per candidate, retained attempted failures, unranked
  method-specific leakage, bounded stopping, and a non-numerical Route A
  field-compatibility gate. [repo-observed]

### Final-IR authoritative evidence chain (verified 2026-07-25)
- v1 data lock is
  `comparison_bench/outputs_comparison/final_ir_method_selection/20260725_v1/`.
  The locked domain is real d=1024, 64-symbol frames, dataset raw SER
  [0.20, 0.30), with 60 tuning frames from
  `real_typeii_20db_d1024_bw200_blk0` and 60 confirmation frames from
  `real_typeii_20db_d1024_bw180_blk0`; the groups are disjoint. Verify
  read-only with `python -m comparison_bench.src.comparison_bench.cli.lock_final_ir_data --verify --manifest comparison_bench/outputs_comparison/final_ir_method_selection/20260725_v1/data_lock_manifest.json`.
  [repo-observed]
- v1 Phase-3 outputs are invalid for decisions (`invalid_run_notice.json`).
  v2 is the sole authoritative bounded run:
  `.../20260725_v2/`; it froze Cascade `[12,6,24,13]`, 4 passes,
  seeded-random gray, and LDPC parity 1.0, 50 iterations,
  `bsc_estimated`/`uniform` gray before confirmation. It retained all 60
  attempts per candidate: Cascade 60/60 independently verified successes and
  LDPC 59/60. [repo-observed]
- v3 audit is superseded by its additive notice. v4 is authoritative:
  `.../20260725_v4_audit/`. Its read-only audit verifies the same 60 locked
  confirmation keys, frozen corrected-grid configurations, all status
  denominators, and evidence hashes. One Cascade-only discordance gives the
  pre-registered exact two-sided paired p-value 1.0 at alpha 0.05; outcome is
  strictly `no_decision`, not a winner. Claims do not extend beyond the locked
  domain, do not rank cross-method leakage, and do not select Polar or qLDPC.
  [repo-observed]
- The Route A compatibility gate is `fail`: comparison outcomes lack the
  documented universal-hash verification, leakage-accounting, and
  correctness-budget fields. No Route A numerical rerun or formal-proof claim
  was made. [repo-observed]
- Phase-5 verification: five-module `py_compile`, focused unittests 7/7,
  read-only v1/v4 verification, and safe comparison pytest 22/22 passed with
  `test_evidence_package.py` excluded because it writes a fixed tracked path.
  External pytest temp/permission behavior remains an infrastructure caveat;
  the six tracked `workspace/pytest-tmp/` deletions are pre-existing and must
  remain untouched. [repo-observed]

### Formal IR qualification evidence chain (verified 2026-07-25)
- Formal candidates are additive under
  `comparison_bench/src/comparison_bench/formal_ir/`; the
  frozen Polar pipeline and the `cascade_lite`/`layered_ldpc_lite` methods and
  their evidence remain unchanged. [repo-observed]
- The sole authoritative synthetic qualification is
  `comparison_bench/outputs_comparison/formal_ir_methods/20260725_v3_synthetic/`.
  Its strict read-only report promotes `cascade_formal_v1` in both strata
  (32/32 `verified_success` at p=.01 and p=.02). It does not promote
  `ldpc_formal_v1` (29/32 and 14/32); all 21 retained non-successes are
  `verify_failed`, with zero unclassified/internal/provenance/accounting
  failures. [repo-observed]
- The invalid real v1 root received only its additive invalid-lock notice and
  made zero formal-method calls. The sole authoritative real qualification is
  `comparison_bench/outputs_comparison/formal_ir_methods/20260725_v2_real_cascade/`:
  its strict verifier accepts exactly seven artifacts, its preflight passed
  29 tests with exit 0, and Cascade achieved 60/60 requested confirmation
  frames as `verified_success`, with union bound `3.2526065174565133e-18` and
  zero unclassified/internal/provenance/accounting failures. The resulting
  promotion is limited to d=1024, 64 symbols, bw120, frame SER `[.20,.30)`;
  LDPC was not run on real data. [repo-observed]
- Read-only verification commands (do not rerun the qualification runners):
  `python -m comparison_bench.src.comparison_bench.cli.run_formal_synthetic_qualification --output-dir comparison_bench/outputs_comparison/formal_ir_methods/20260725_v3_synthetic --verify`
  and
  `python -m comparison_bench.src.comparison_bench.cli.run_formal_real_qualification --output-dir comparison_bench/outputs_comparison/formal_ir_methods/20260725_v2_real_cascade --verify`.
  [repo-observed]
- Before any frame-identical Polar/Cascade/LDPC comparison, a separate
  LDPC-improvement OpenSpec change must obtain fresh synthetic and real LDPC
  promotion. Do not substitute a lite method or tune on confirmation data.
  [repo-observed]

### Formal LDPC v2 improvement evidence (verified 2026-07-26)
- Archived change is
  `openspec/changes/archive/2026-07-26-improve-formal-ldpc-v2/`. Additive
  `ldpc_formal_v2` freezes
  nine policies: rate margin 0/1/2 crossed with `OSD_0/0`, `OSD_CS/1`, and
  `OSD_CS/2`. The n=64 nested codebook has 16 masters per plane and selected
  prefix matrices 32/40/48/56. Its structural screening is a proxy, not
  verified decoding evidence. [repo-observed]
- The v1 integration root `20260725_v1_ldpc_v2_synthetic` is invalid: the
  v1 codebook verifier makes all 576 policy outcomes plus 64 associated
  outcomes `unsupported_domain`. Its seven artifacts remain immutable and an
  additive invalid notice records the exclusion. [repo-observed]
- Fresh v2 plan SHA256 is
  `c0770b5b1c80c277448ca832b01a5dd6d8413df78870fa040c6546d0098ede18`, with
  zero old/new CSPRNG overlap. Strict verification passed. Development results
  are 26/64 (margin 0), 33/64 (margin 1), and 56/64 (margin 2), identical for
  every OSD variant; the selected policy is rate margin 2 with `OSD_0/0`.
  [repo-observed]
- Confirmation records 28/32 at p=.01 and 29/32 at p=.02, seven
  `verify_failed`, and verification invoked for all 64 outcomes, with zero
  unclassified/internal/provenance/accounting failures. Status is
  `non_promoted`; no real lock or run is authorized, and confirmation must not
  be used to tune. [repo-observed]
- Artifact SHA256 prefixes: plan `c077...`, codebook `360b77...`, outcomes
  `9adb0...`, policy `303919...`, transcript `4b438...`, manifest `d185fc...`,
  report `53fbe5...`. Final checks: v2-focused 25 passed plus 5 subtests,
  general 52 passed/11 skipped, formal-real 12 passed, strict verification
  passed, and frozen `src/`, `experiments/`, `tools/`, and `results/` diff is
  empty. Terra low only implemented frozen tasks and specified tests; the main
  thread retained planning and acceptance. [repo-observed]
- Short- and medium-term engineering work is complete with reproducible
  evidence, but LDPC has not met promotion; the fair three-method comparison
  remains blocked. [repo-observed]

## 11. Parallel Binary and Nonbinary LDPC Direction (2026-07-26)

- Binary and nonbinary LDPC are now planned as independent parallel research
  lanes. The detailed handoff is
  `comparison_bench/docs/ldpc_parallel_handoff.md`. [repo-observed]
- Binary starts from immutable, non-promoted `ldpc_formal_v2` evidence and
  targets longer frames, deterministic QC/PEG/protograph families,
  incremental redundancy, and per-bit-plane soft information. Existing
  confirmation evidence cannot be used for tuning. [repo-observed]
- Nonbinary N0 field-backend work is implemented under the independent
  `nbldpc_formal_v1` identity in
  `comparison_bench/src/comparison_bench/formal_ir/nonbinary_field.py`.
  It pins deterministic polynomial-basis GF(2^m) arithmetic for powers-of-two
  q through 1024, canonical field metadata/IDs, and a read-only fail-closed
  preflight. `qldpc_reference` remains unchanged and reference-grade.
  This proves field-backend feasibility only, not decoder feasibility,
  qualification, promotion, or comparison readiness. [repo-observed]
- The two lanes require separate OpenSpec changes, codebooks,
  development/confirmation splits, artifacts, leakage accounting, verifiers,
  and promotion decisions. Only independently promoted methods may enter a
  later frame-identical comparison. [repo-observed]

## 12. Binary LDPC Long-Frame v3 Phase 1 (2026-07-26)

- Active OpenSpec change:
  `openspec/changes/binary-ldpc-long-frame-and-ir-v3/`. [repo-observed]
- Candidate-only `codebook_long_v3.py` supports n=256/512/1024, ten planes,
  four deterministic candidates, and nested 1/2, 5/8, 3/4, 7/8 check
  prefixes. HGF2V3 bytes and a reconstruction-verified manifest bind all 120
  candidate identities. [repo-observed]
- Actual-rank, no-zero/duplicate-column, weight-bound, exact 4-cycle, and
  `column_pair_extrinsic_degree_v1` proxy tests passed. Main-thread evidence:
  focused 4 passed in 10.88 s; v2 regression 7 passed/1 skipped in 81.41 s;
  compilation/diff checks passed and frozen directories were unchanged.
  [repo-observed]
- Phase 1 is engineering evidence only: no FER, candidate selection, decoder,
  confirmation/real data, qualification, or promotion. Next freeze a
  sacrificed-development FER evaluation contract. [repo-observed]

## 13. Binary LDPC Long-Frame v3 Phase 2 (2026-07-26)

- `long_v3_development.py` implements exact sacrificed p=.01/.02 generation,
  canonical seed/source hashes, pinned BP+OSD-0 metadata, four-prefix
  incremental evaluation, retained statuses, and exact four-candidate
  selection. It is in-memory and writes no result artifact. [repo-observed]
- Selection is frozen as worst-stratum successes, total successes, syndrome
  disclosure, then candidate ID. Runtime and structural proxies are excluded.
  Tests independently verify the data/policy/selection hash preimages and
  fail-closed malformed-grid behavior. [repo-observed]
- Main-thread evidence: focused 5 passed in 0.53 s; Phase1/v2 regression
  11 passed/1 skipped in 92.68 s; compilation and frozen-directory checks
  passed. [repo-observed]
- Phase 2 used injected test decoders only. No pinned-backend development
  sweep, candidate FER evidence, selection, confirmation, real data,
  qualification, or promotion exists yet. Next freeze a bounded backend
  preflight/pilot. [repo-observed]

## 14. Binary LDPC Long-Frame v3 Phase 3A Pilot (2026-07-26)

- A single in-memory pinned-backend pilot ran exactly once at
  n=256/plane0/candidate0/p=.01 on 16 sacrificed frames. Backend was
  `ldpc==2.4.1`; exit 0; stderr empty; process 0.3227008000249043 s; external
  wall 1.0 s. [repo-observed]
- Outcomes were 16/16 exact success, terminal p050=15/p0625=1, and 2080 total
  syndrome bits. No file was written and no candidate was selected.
  [repo-observed]
- This clears one-slice backend feasibility only. It is not comparative FER,
  n=512/1024 evidence, qualification, or promotion. Next freeze an immutable,
  verifier-bound full sacrificed-development sweep contract. [repo-observed]

## 15. Binary LDPC Long-Frame v3 Phase 3B Tooling (2026-07-26)

- Additive runner/verifier tooling now freezes a 3840-row, 30-selection
  sacrificed-development grid with prepare/execute no-overwrite lifecycle,
  six canonical artifacts, code/backend/hash DAG, failure finalization, and
  production/test isolation. [repo-observed]
- Read-only verification reconstructs deterministic source provenance and the
  accepted candidate-selection function, but does not rerun LDPC decoding.
  Its success is artifact integrity only. [repo-observed]
- Main-thread evidence: Phase3B focused 3 passed in 12.30 s; all long-v3
  12 passed in 12.94 s; v2 regression 7 passed/1 skipped in 81.34 s;
  compilation/diff/frozen-directory checks passed. Test artifacts are under
  `workspace/formal_long_v3_phase3b_tests_run3`. [repo-observed]
- No production plan or 3840-row sweep exists yet. Next create and inspect one
  fresh plan, then separately authorize its single execution. [repo-observed]

## 16. Binary LDPC Long-Frame v3 Phase 3C Development Evidence (2026-07-26)

- Immutable development root:
  `comparison_bench/outputs_comparison/formal_ir_methods/20260726_v1_binary_ldpc_long_v3_development/`.
  Execute ran once in 28.9 s with 3840 outcomes/30 selections; strict verifier
  ran once in 11.2 s, exit 0, without decoder reexecution. [repo-observed]
- All 3840 per-plane candidate outcomes were
  `development_exact_success`. Selected per-plane mean syndrome bits:
  n256 129.0/134.6, n512 260.4/280.4, n1024 541.6/635.2 for p001/p002.
  [repo-observed]
- The current per-plane terminal is chosen using Alice-truth exact equality.
  This is a sacrificed-development oracle and not a deployable stopping signal;
  its leakage and 100% result are not qualification evidence. [repo-observed]
- Next aggregate ten planes into global incremental rounds with one
  frame-wide Toeplitz verification tag, count slowest-plane syndrome/tag
  leakage, then select the formal length/policy before fresh confirmation.
  [repo-observed]

## 17. Binary LDPC Long-Frame v3 Phase 4 Frame Development (2026-07-26)

- Ten-plane read-only aggregation produced 96 q=1024 development frames and
  modeled one 64-bit frame-wide Toeplitz tag over at most four global rounds.
  Aggregation SHA256 is
  `029e33c42f254e40725a370065d30196216501085d5def5f0f0c935aca6c933c`.
  [repo-observed]
- All lengths retained 16/16 success in both strata. Mean frame key-disclosure
  fractions p001/p002: n256 .5640625/.68125; n512 .590625/.7546875; n1024
  .6625/.8421875. [repo-observed]
- Frozen development choice is n=256 with tuple
  `[-16,-32,.68125,.62265625,256]`. This is sacrificed-development design
  selection only; the stopping tag was modeled, not executed. [repo-observed]
- Next implement actual n256 ten-plane formal decoding, locked Toeplitz
  seed/tag, transcript, caps and fail-closed statuses before any fresh
  qualification. [repo-observed]

## 18. Binary LDPC Long-Frame v3 Phase 5 Formal Method (2026-07-26)

- `formal_ir/ldpc_v3.py` implements `ldpc_formal_v3` for exactly q=1024,
  n=256 and ten MSB-first Gray planes with frozen candidates
  `[1,0,1,2,0,0,1,3,2,3]`. [repo-observed]
- It reconstructs canonical long-v3 matrices, validates a self-hashed
  sacrificed calibration, requires `ldpc==2.4.1`, and decodes all ten planes
  in four possible synchronous incremental-syndrome rounds. [repo-observed]
- One 64-bit frame-wide Toeplitz tag is disclosed once and checked only after
  complete rounds. The decoder receives no tag/match or Alice truth. Strict
  transcript validation binds terminal prefix, syndrome/tag/seed disclosure,
  epsilon, caps, backend and frozen selection. [repo-observed]
- Main-thread evidence: focused 6 passed in 2.15 s; long-v3 regression 13
  passed in 16.12 s; v2 regression 7 passed/1 skipped in 81.27 s;
  compilation/diff/frozen-directory checks passed. [repo-observed]
- This accepts method engineering only. No confirmation runner/artifact,
  strict package verifier, qualification, promotion, real-data result, or fair
  comparison eligibility exists. Phase 6 must be planned and frozen before
  execution. [repo-observed]

## 19. Binary LDPC v3 Phase 6 TTBIN Bridge and Synthetic Stop (2026-07-26)

- Phase 6A read-only bridge binds the real 20 dB main/chunk TTBIN and exact
  q=1024 sidecars, selects 64 bw100 calibration plus 32 each bw120/180/200
  reserved confirmation frames, and reconstructs source/lock/calibration
  hashes. Calibration plane p_hat ranges from .000366 to .122620.
  [repo-observed]
- Immutable synthetic package
  `comparison_bench/outputs_comparison/formal_ir_methods/20260726_v1_binary_ldpc_v3_synthetic/`
  was prepared, executed, and strictly verified exactly once. Verification
  accepted 64 outcomes and returned `decoder_reexecution=false`.
  [repo-observed]
- Calibrated confirmation achieved 3/32 and 1.25x stress achieved 1/32 versus
  31/32 gates. The other 60 outcomes are `verify_failed`; forbidden
  internal/provenance/accounting failures are zero. [repo-observed]
- Binary v3 is non-promoted. Phase 6C real tooling/output was not created and
  is locked. Do not tune or retry from confirmation. A successor requires a
  new OpenSpec improvement and fresh synthetic confirmation. [repo-observed]
- Nonbinary N1 is implemented in
  `comparison_bench/src/comparison_bench/formal_ir/nonbinary_codebook.py` as a
  pure in-memory n=64 family: one deterministic 32x64 mother matrix and exact
  16/24/32 ordered prefixes, with three SHA256-derived cyclic shifts,
  explicit nonzero GF(q) coefficients, an identity parity half, and rank
  calculated with the pinned N0 GF(q) arithmetic. [repo-observed]
- Canonical `NBLDPC1` bytes include the full field representation,
  construction, dimensions, topology, coefficients, seed, and ordering.
  Golden codebook/manifest SHA256 tests plus reconstruction-based tamper
  checks cover field, coefficient, rank, prefix, codebook-ID, and manifest-ID
  drift. Focused N0+N1+qLDPC tests passed 22/22; the selected
  formal/nonbinary/qLDPC regression passed 29/29. [repo-observed]
- N1 is structural rank/hash evidence only. It does not establish a soft
  decoder, distance/FER performance, qualification, promotion, outputs, or
  comparison readiness. N2 must freeze decoder and formal accounting
  contracts before implementation or dependency selection. [repo-observed]
- Nonbinary N2 is implemented in
  `comparison_bench/src/comparison_bench/formal_ir/nonbinary_qspa.py` as a pure
  full-message probability-domain FFT-QSPA feasibility decoder. It consumes
  Bob symbols, Alice's public syndrome, and verified N1 codebooks; its public
  decoder signature has no Alice truth or callback. q=4 coefficient/coset
  check updates match brute-force convolution, and q=1024 executes inside the
  frozen n=64/check/iteration/16-MiB declared dense-message bounds.
  [repo-observed]
- `syndrome_consistent` is deliberately separate from locked Toeplitz
  verification. Symbols map to fixed-width MSB-first bits; syndrome
  disclosure is checks*log2(q), invoked verification tags add their exact
  length, and public-control bits remain separate. N0-N2 plus qLDPC tests
  passed 35/35; selected formal verification/Cascade/LDPC regressions passed
  17 with 2 skipped. [repo-observed]
- N2 is bounded engineering feasibility only. It does not prove general
  correction, FER/performance, calibration, synthetic/real qualification,
  promotion, outputs, production readiness, or comparison eligibility. N3
  requires planner-owned pre-registration before execution. [repo-observed]

## 20. Nonbinary LDPC v2 Development Non-Readiness (2026-07-26)

- `nbldpc_formal_v2` Phase 1/2 was accepted with 21 focused tests; the joint
  N0-N3/v2/formal regression passed 86 with 8 skipped. [repo-observed]
- The immutable root
  `comparison_bench/outputs_comparison/formal_ir_methods/20260726_v2_nbldpc_synthetic/`
  contains one reviewed plan (112 frames, 24 policies, 1216 unique seeds,
  overlap zero), one execution, and one successful strict full replay.
  [repo-observed]
- The selected tempered+damped QC48 policy used margin 8, max_iter 10, and
  32/40 checks for p=.20/.30. Development achieved 0/24 and 5/24 verified
  successes against a 22/24-per-stratum readiness floor. Confirmation was
  never generated or executed. [repo-observed]
- Status is `non_promoted_development`, not confirmation FER or real-data
  evidence. No rerun, tuning, N4 sidecar adapter, or `.ttbin` processing is
  authorized. [repo-observed]

## 21. Binary LDPC v4 Development Backend Stop (2026-07-27)

- `binary-ldpc-adjacent-channel-v4` implements deterministic adjacent-channel
  modeling, 40 anchored sparse binary codebooks, a fixed 648-bit formal
  method, immutable development/synthetic/real packages, and read-only
  source/transcript/gate verifiers. Focused main-thread acceptance passed
  15+8+3+4 tests; cross-version regression passed 119 with 10 skipped.
  [repo-observed]
- Sole production development evidence:
  `comparison_bench/outputs_comparison/formal_ir_methods/20260727_v1_binary_ldpc_v4_development/`.
  Plan content SHA256 is
  `af644e2f4a3dab596f34350b18ecfb1df56cb46b93670cb16e89f3ca1ae67c5e`.
  The read-only verifier returned verified/completed with
  `decoder_reexecution=false`, but readiness was false. [repo-observed]
- Nominal and stress each retained 512 denominators, zero frame successes,
  and 5,120 selected-plane `development_decoder_error` outcomes. This is an
  implementation failure and must not be interpreted as FER or code quality.
  [repo-observed]
- A no-decode diagnostic confirmed the backend mismatch: `ldpc==2.4.1`
  rejects NumPy-array `error_channel` with `expected list`, while the same
  vector converted by `.tolist()` constructs. The formal v4 path converts it;
  the frozen development path did not. [repo-observed]
- No v4 production synthetic or real directory exists. The frozen stop rule
  forbids editing/tuning/rerunning this package. A continuation needs a new
  versioned OpenSpec implementation-correction lane and fresh evidence; fair
  Cascade/LDPC/Polar comparison remains blocked. [decision]

## 22. Binary LDPC v4 Backend Correction Readiness (2026-07-27)

- `binary-ldpc-v4-backend-correction-v1` added only versioned development
  files. It converts the frozen Bob-conditioned float64 error channel to a
  Python list at the `ldpc==2.4.1` constructor boundary; historical v4 source
  and evidence hashes remain unchanged. [repo-observed]
- Immutable corrected package:
  `comparison_bench/outputs_comparison/formal_ir_methods/20260727_v2_binary_ldpc_v4_development/`.
  Plan content SHA256 is
  `1e208832ac421e69c0488d33e39953755ba487c25f9bf9db43bdda79cc53daaf`.
  Prepare/execute/read-only verification each ran once; verification returned
  completed/verified, `decoder_reexecution=false`, and readiness true.
  [repo-observed]
- Frozen development results are 510/512 adjacent nominal and 511/512
  adjacent stress, with zero forbidden failures. Selected candidates are
  `[0,0,0,0,0,0,2,0,2,2]`. This clears only the 495/512 sacrificed-
  development screen. [repo-observed]
- No corrected-v4 synthetic or real production output was created. Synthetic
  qualification still requires a fresh main-thread plan audit and one
  independent execution; comparison eligibility and real `.ttbin` claims
  remain unestablished. [decision]

## 23. Binary LDPC v4 Corrected Synthetic Promotion (2026-07-28)

- Immutable package
  `comparison_bench/outputs_comparison/formal_ir_methods/20260728_v2_binary_ldpc_v4_synthetic/`
  strictly verified with 256 outcomes, no decoder reexecution, and promotion:
  nominal 127/128, stress 126/128, zero forbidden failures. [repo-observed]
- Plan content SHA256 is
  `02a198ea4d03ae4d7dad7db6e2b4099e85f5b75c0d8acad34e8449d67cb769fb`.
  Fresh roots/seeds have zero overlap with v3 and development. Do not rerun or
  tune from this confirmation. [repo-observed]
- Real qualification remains unrun. Current bw120/bw180/bw200 sidecars each
  have 117 complete frames; excluding 32 v3-reserved identities leaves 85,
  below the frozen 128 by 43 per stratum. Real prepare must remain blocked
  until traceable same-domain source data fills that deficit. [decision]
- Prefer at least 64 newly supplied complete frames per real stratum to absorb
  duplicate/incomplete rejection. Preserve 128 denominators and 126/128 gates;
  do not reuse reserved frames or weaken the claim to fit current data.
  [decision]

## 24. Binary LDPC v4 Real-Source Intake Acceptance (2026-07-28)

- The only other local 20 dB tree is a byte-identical raw-capture copy. Its
  main/chunk SHA256 pair equals the registered capture, so it is not new
  statistical capacity. [repo-observed]
- The Phase 4 intake layer now builds and reconstructs a no-overwrite,
  self-hashed multi-acquisition source extension. It rejects duplicate raw
  pairs and frame payloads, binds exact q=1024 bw120/bw180/bw200 sidecars,
  counts only complete 256-symbol frames, and performs no decoding.
  [repo-observed]
- Main acceptance passed 3 source, 5 real, 7 bridge/source, and 25
  backend/development/formal-real tests. Historical v3/development source
  hashes remain exact and no real production directory exists.
  [repo-observed]
- Real prepare remains unauthorized until a genuinely distinct 20 dB
  acquisition supplies enough validated capacity and a main-thread-reviewed
  extension manifest. The 128 denominators and 126/128 gate remain frozen.
  [decision]

## 25. Project-Wide Delegation Workflow (2026-07-29)

- Substantial delegated implementation starts from one complete frozen task
  packet: file scope, functionality, full test/evidence matrix, commands,
  artifacts, stop rules, and return conditions. [decision]
- The main thread owns planning, requirements, thresholds, OpenSpec,
  acceptance, and scientific conclusions. The implementation subagent is an
  operator and returns only a complete candidate or a concrete reproducible
  blocker; partial “still incomplete” reports are not completion. [decision]
- Main review normally occurs at spec freeze, complete candidate delivery, and
  independent acceptance. Tests progress from focused development to combined
  focused candidate to main regression/compile/frozen-hash/no-output review.
  [decision]
- Verifier acceptance matrices must pre-register byte drift, locally re-signed
  semantic tampering, re-signed manifest/index tampering, and deep
  cross-artifact reconstruction. Known Windows ACL failures require an
  explicitly writable non-production test root. [decision]
- These coordination optimizations do not alter prepare/review/execute/verify,
  immutable failure retention, scientific thresholds, or no-rerun/no-tuning
  boundaries. [decision]
- Acceptance items use stable IDs. Successor evidence machinery starts from
  the nearest accepted predecessor and an explicit delta list. [decision]
- Tests use T0 compile/structural, T1 focused, T2 fake qualification/replay,
  and T3 regression stages; T2/T3 run only at milestones and test-only calls
  explicitly pass fake runners. [decision]
- Windows tests use additive workspace UUID roots with pytest cache disabled.
  Process termination requires positive ownership; dirty-worktree acceptance
  includes untracked hashes, frozen diffs, and output-root checks. [decision]
- Handoffs report only changed files, commands/results, concrete blockers, and
  remaining acceptance IDs; they do not repeat durable project context.
  [decision]

## 26. Binary LDPC v4 16 dB Transfer Result (2026-07-29)

- The sole 16 dB transfer package completed and strictly verified with all 384
  outcomes: bw120 125/128, bw180 128/128, bw200 128/128, and zero forbidden
  failures. Because every layer required 126/128, the package is immutable
  `non_promoted_transfer`. [repo-observed]
- Read-only verification reported no decoder reexecution and changed none of
  the nine files. Plan content SHA256 is
  `ddbf41983d866ce5d320404323ff319b64a867f8f8c32185a890ab7baf97b2da`;
  source-lock content SHA256 is
  `5c654377751cea776a203269b8213959313aa9a0be738935816d36b52181ea87`.
  [repo-observed]
- The 16 dB evidence must not be tuned or rerun and does not promote 16 dB or
  20 dB. A separately scoped unchanged-method 10 dB transfer is frozen under
  `binary-ldpc-v4-10db-transfer-qualification-v1`; if promoted, its claim is
  limited to that independent 10 dB acquisition. [decision]

## 27. Binary LDPC v4 10 dB v1 Prepare Rejection (2026-07-29)

- The v1 10 dB prepare was rejected before execute because validation included
  its own newly written plan in the prior-real root set. It contains exactly
  plan and lock, no outcomes. Preserve it as `invalid_pre_execute`; plan file
  SHA256 is `dae9d27a068bf9b15f25ae684bd3cf290623524b0e92af8989869579b0ac523c`
  and lock file SHA256 is
  `6596316074b0e473de26ba44a87556016f23b082dc36239e06a65fa4e7d11baf`.
  [repo-observed]
- A versioned correction must exclude only the current plan from prior-plan
  discovery while continuing to bind and forbid the invalid v1 roots/seeds.
  No scientific inputs or gates may change. [decision]

## 28. Binary LDPC v4 10 dB v2 Result and v5 Route (2026-07-29)

- The corrected v2 10 dB package strictly verified all 384 outcomes but was
  non-promoted: bw120 125/128, bw180 127/128, bw200 128/128, zero forbidden
  failures. Plan content SHA256 is
  `c6f3592ac24fd32ac136d16f06fd88157757216a81c40643e86d0ba3882af2f6`.
  [repo-observed]
- All four failures were retained `verify_failed` after complete syndrome
  disclosure and Toeplitz mismatch. v4 fixed-rate robustness, not source,
  backend, accounting, or resource failure, is the remaining issue.
  [repo-observed]
- Do not test progressively easier losses until one passes. The v5 route
  pre-locks disjoint unused 10 dB development and confirmation frames, screens
  frozen stronger-OSD/incremental-redundancy policies on development, then
  requires fresh synthetic promotion before one sealed real qualification.
  [decision]

## 29. Nonbinary LDPC v3 Covered-Layered Result (2026-07-30)

- The sole v3 synthetic package was planned once, executed once, and strictly
  replay-verified once. The selected layered-l075 margin-8 policy used 32/40
  checks and passed development readiness at 23/24 for p=.20 and 24/24 for
  p=.30. [repo-observed]
- Sealed confirmation was materialized only after readiness and achieved
  32/32 for p=.20 and 30/32 for p=.30, with zero prohibited failures. The
  frozen 31/32-per-stratum gate failed by one p=.30 frame, so the package is
  immutable synthetic non-promotion evidence. [repo-observed]
- Strict verification returned `verified=True`, `run_status=completed`,
  `promoted=False`. Plan SHA256 is
  `0f35b8679166599efb294caee21822156ba971bec6271875cf55516523cfdee1`;
  selected-policy SHA256 is
  `6193f92af05c1d3a5145cbe31c95a4d20f1eaf5a09970936613c326cc1c59a28`.
  [repo-observed]
- Do not rerun, tune confirmation, overwrite evidence, build N4, access
  sidecars, or process `.ttbin`. Real-data work requires promoted synthetic
  confirmation and a new approved OpenSpec change. [decision]

## 30. Nonbinary LDPC v4 Incremental-Redundancy Result (2026-07-31)

- The sole v4 IR package was planned, executed, and strictly replay-verified
  once. Verification returned `verified=True`, `run_status=completed`,
  `promoted=False`. [repo-observed]
- Development selected `nbldpc_v4_ir_warm`: 64/64 at p=.20 and 63/64 at
  p=.30. Sealed confirmation achieved 128/128 and 120/128; all eight misses
  were p=.30 `decode_failed`, with zero prohibited failures. [repo-observed]
- The package is immutable at
  `comparison_bench/outputs_comparison/formal_ir_methods/20260731_v4_nbldpc_ir_synthetic/`.
  Do not rerun, tune, overwrite, build N4, access sidecars, or process `.ttbin`.
  Any successor requires new OpenSpec, fresh synthetic splits, and a
  pre-registered method change. [decision]
- Reusable process lesson: historical qualification suites whose own official
  roots now exist can correctly reject a test replay as identity reuse. Retain
  that evidence and use isolated algorithm regressions; never edit immutable
  outputs or weaken freshness guards merely to make an old suite green.
  [repo-observed]

## 31. Binary LDPC v5 Development, Synthetic, and Sealed Real Promotion (2026-08-01/2026-08-12)
- Phase 2 sacrificed development selected V5-C2: 1536/1536 verified success
  (512/stratum across bw120/bw180/bw200 real 10 dB frames), zero forbidden
  failures, 1 round, no fallback. Leakage 648 bits/frame = 2.531 b/symbol =
  0.253 b/input bit (h1 syndrome 584 + verification 64); real raw SER
  bw120 0.1228 / bw180 0.0833 / bw200 0.0767; 204.7 s total. Package immutable
  at comparison_bench/outputs_comparison/formal_ir_methods/
  20260731_v1_binary_ldpc_v5_development/. [repo-observed]
- Robustness evidence committed to comparison_bench/docs/ldpc_v5_robustness/:
  E1 new-seed rerun 768/768, E3 model-consistent (SER 0.243) 768/768,
  E2 uniform OOD control 0/1152 as expected. [repo-observed]
- Phase 3 fresh synthetic confirmation (2026-08-01): 256/256 verified success
  (nominal 128/128 + stress_125 128/128), zero forbidden failures,
  promoted=true, ready_for_real_qualification=true, decoder_reexecution=false.
  Package immutable at .../20260801_v1_binary_ldpc_v5_synthetic/; plan sha256
  c91171dcdde8c1cf5fb31cc21cbad72115756fff034763ce93c75cbef17c10ab. [repo-observed]
- Phase 4 sealed real qualification COMPLETED and PROMOTED (2026-08-12):
  384/384 verified_success — bw120/bw180/bw200 each 128/128, zero forbidden
  failures; report `promoted=true`, `run_status=completed`,
  `decoder_reexecution=false`. Official package (ten files, run_id
  `binary_ldpc_v5_real_qualification_v1`, plan_sha256
  `a79cd16f19b968364a4c46fb4887f933eeb472e45c19d098a938ae5dc58ad01b`,
  report_sha256
  `18b5566ed636a79473ff7290cb55d90d4ab20a170895b53f786ea2455ad953d5`):
  comparison_bench/outputs_comparison/formal_ir_methods/
  20260801_v2_binary_ldpc_v5_real/. Execute ~5m12s, read-only verify ~4m29s,
  detached background process. Chain: partition lock (20260731) → v5
  development (V5-C2, 1536/1536) → v5 synthetic (256/256, 20260801) → v5 real
  (384/384, 20260801_v2), each once with read-only verification. [repo-observed]
- v4's two real transfers remain retained as non-promoted failure evidence
  (16 dB 125/128 and 10 dB v2 125/128, both below the 126/128 gate); v5 is
  the first all-green real 10 dB Type-II promotion. Do not tune or rerun
  them. [decision]
- Comparison eligibility updated (2026-08-12): binary LDPC v5 may participate
  in comparison within the promoted 10 dB Type-II q=1024 Gray 256-symbol
  bw120/bw180/bw200 domain only; all other domains and methods (v4, 16 dB,
  20 dB, other captures, nonbinary, Cascade/Polar) keep their prior status.
  A rate-adaptive successor requires a separate OpenSpec change. [decision]
- Polar numerical comparison remains blocked: results/ is empty in this
  checkout and polar_existing imports are historical, non-frame-identical,
  leakage NaN. No Polar-vs-v5 numeric claim is supportable. [repo-observed]
- Reusable process lessons (2026-08-12): (a) Long qualification stages
  (prepare/execute/verify, ~5-20 min) exceed subagent/session channel
  timeouts; run them as a detached background process (background bat +
  log-file polling) outside the opencode session. (b) Three latent production
  bugs (synthetic_dir directory semantics, generator empty-dict check,
  missing root_id) were masked by tests that mocked core functions
  (`_seed_schedule`, `_validate_roots`, `_validate_plan`) and surfaced only at
  production prepare; keep a real-path smoke in tests rather than mocking
  whole core paths, so such defects surface at T0/T1 instead of at sealed
  qualification time. [decision]

## 32. Nonbinary LDPC v5 Multistage Change Terminated — Four Routes Non-Promoted (2026-08-02)
- The v5 multistage change (formal-nonbinary-ldpc-v5-multistage-ir) ran all four
  pre-registered routes A/B/C/D, each planned once, executed once, and strictly
  replay-verified once; every route hit the same p=.30 tail pattern
  (promotion gates p=.20 128/128, p=.30 127/128) and is `promoted=false`.
  Per task 7.4 the change terminates with four immutable non-promoted
  packages: 20260731_v5a_nbldpc_multistage_synthetic (three-level warm IR),
  20260731_v5b_nbldpc_mother_synthetic (NBLDPC5B mother, zero w2/w3),
  20260731_v5c_nbldpc_decoder_synthetic (sched/EMS decoders),
  20260731_v5d_nbldpc_post_synthetic (list L=2 x top-8 + ADMM rho=1.0
  <=50-iteration post-processing over the v5c decoders). [repo-observed]
- Route D execution (HEAD 192f455): run_status=completed, readiness true,
  512 outcomes; strict replay returned {'verified': True,
  'run_status': 'completed', 'promoted': False} with an unchanged worktree.
  Evidence: evidence/v5d_acceptance_d1_d2.json and v5d_acceptance_c3_c4.json. [repo-observed]
- Route D implementation corrections (main-thread approved, recorded in the
  module docstring and decision-log 2026-08-02): the frozen x-update prior
  term sign was wrong (+prior/RHO; correct is x = z - lambda - prior/rho) —
  a q=4 brute-force experiment showed recovery 0% -> 87-100% after the fix;
  and the frozen z-update alternating projection onto {simplex AND
  output-sum=e_s} is a strict subset of the GF(q) check polytope (it forces
  all output symbols to s) and could not recover codewords — replaced by the
  per-bit parity-relaxation projection (bitwise-XOR linearization), 100%
  exact recovery in the same experiment. A _V5D_BY_V5C reverse map fixes the
  production trigger (post.start delegates v5c and the state carries the v5c
  policy id). [decision]
- Procedural deviation recorded: the v5d 7.3 plan was created before the
  D1/D2 acceptance evidence file; closed read-only at the same HEAD with the
  plan unchanged (see v5d_acceptance_d1_d2.json). [repo-observed]
- Bounds: list L=2, top-8 symbols, exactly 64 candidates, at most one round,
  syndrome filter; ADMM rho=1.0, <=50 iterations, deterministic init, no
  random source; verification cap 3; no additional syndrome/tag disclosure. [repo-observed]
- N4, sidecar access, .ttbin processing, real-data qualification, and any
  comparison claim remain locked. A nonbinary successor requires a new
  OpenSpec change with fresh development and confirmation data; neither
  codebook redesign (B), decoder-family change (C), nor list/ADMM post (D)
  closed the p=.30 tail at the 128/128 floor. [decision]
- Reusable process lesson (already recorded at section 30): official roots
  existing in the shared output root make the same-run-id lane test suite
  self-conflict on identity freshness; that is the designed anti-replay
  guard, not a regression. [repo-observed]

## 33. Nonbinary LDPC v6 Long-Block Engineering Candidate Accepted (2026-08-02)

- Engineering candidate of change `formal-nonbinary-ldpc-v6-long-block`
  implemented and independently reviewed ACCEPTED (V6-50) 2026-08-02 at HEAD
  `a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344`. Seven new files:
  `formal_ir/nonbinary_v6_codebook.py`, `formal_ir/nonbinary_v6_long.py`,
  `formal_ir/nonbinary_v6_development.py`,
  `cli/run_formal_nonbinary_v6_development.py`,
  `tests/test_nonbinary_v6_codebook.py`, `tests/test_nonbinary_v6_long.py`,
  `tests/test_nonbinary_v6_development.py`, plus
  `evidence/v6_engineering_acceptance.json` under the change directory. No
  existing file modified; frozen `src/`/`experiments/`/`tools/`/`results/`
  diff empty; no official v6 output root exists under
  `comparison_bench/outputs_comparison/formal_ir_methods/`. [repo-observed]
- Method identity `nbldpc_formal_v6_long`: GF(1024), n=1024 symbols, two
  deterministic degree-2 PEG codebooks (1024,320) for p=.20 and (1024,480)
  for p=.30; check degrees 6/7 and 4/5; full GF rank 320/480; zero parallel
  edges; frozen seeds {320: 2026080200, 480: 2026080300} from a one-time
  bounded rank search, never re-searched at runtime; magic `b"NBLDPC6\n"`.
  [repo-observed]
- Decoder: ascending-row layered FFT-QSPA, lambda .75, max 50 iterations,
  single-threaded (workers=1 by construction), whole-graph syndrome check
  after every iteration, 64-bit Toeplitz verification only after syndrome
  consistency, syndrome disclosure 10*m bits plus 64 key-dependent tag bits,
  no fallback, fail-closed on NaN/Inf/non-finite/wrong length/malformed
  syndrome/allocation cap (dense message bound 50,331,648 bytes <= 64 MiB).
  [repo-observed]
- Acceptance: T0 16, T1 38, T2 6 (fake lifecycle + strict read-only replay
  with explicit fake runner; production decoder never entered), T3 51
  v5-regression (N0 field, N1 codebook, N2 qspa, v3 core, v5a codebook, v5a
  core); all 8 tamper classes rejected (byte, semantic self-hash, manifest
  link, source identity, transcript recanonicalized, leakage, gate
  rebuilding/promotion forgery); CLI default action is plan, execute is a
  hard SystemExit(2) refusal. Evidence JSON binds HEAD, source hashes,
  command exit codes, tier results, A01-A10. [repo-observed]
- Diagnostic observation, strictly diagnostic-only and NOT FER/qualification
  evidence: a full-rate random p=.20 frame does not converge within 50
  iterations (~85 s per frame); 1-2 planted errors and noiseless frames
  converge in 1 iteration. Consistent with the change's weak-baseline
  hypothesis. [repo-observed]
- Boundary state: V6-51 (reviewed sacrificed development plan with fresh
  roots) NOT authorized; V6-52 successor choice (qualification / n=4096 /
  multiplicative repetition / GF(32)xGF(32)) NOT made; no confirmation
  material, no real data, no promotion. v5 change remains terminated with
  four immutable non-promoted packages. [decision]
- Process note: memory-agent triage delegation returned empty three times
  without writing; the durable section above was appended directly by the
  orchestrator from verified session evidence. [decision]

## 34. Nonbinary LDPC v6 Canary 0/4 Both Strata — Long-Block Baseline Stopped (2026-08-02)

- Main-thread decision: no large-scale v6 development run. A small sacrificed
  8-frame canary (4 p=.20 + 4 p=.30, fixed (1024,320)/(1024,480) codebooks,
  lambda .75, max_iter 50, workers=1, fresh roots 202608024000/202608024100,
  no confirmation) was staged via a minimal additive CANARY config in
  `nonbinary_v6_development.py` (production execution authorized only for
  CANARY config with explicit workspace output; CONFIG 64-frame plan path and
  official-root lock preserved). Canary tests 8/8 new + 46 total + 51 v5
  regression passed. [repo-observed]
- Canary plan created once and read-only reviewed READY-FOR-SINGLE-EXECUTION
  (evidence/v6_51_canary_plan_evidence.json), executed exactly once (exit 0,
  450.9 s) and strict-replayed exactly once (exit 0, 518.6 s). Result: 0/4
  verified success in BOTH strata; all 8 frames `decode_failed` at
  max_iter=50 with zero forbidden statuses; run_status
  `development_completed`, promoted false. Package retained at
  `workspace/nbldpc_v6_canary_b01c42a5dee14ed0913e78d60944cc38/canary_plan`;
  no official root under `formal_ir_methods/` created.
  Evidence: evidence/v6_51_canary_execution_addendum.json. [repo-observed]
- Pre-registered gate fired: any stratum 0/4 -> stop the degree-2 n=1024
  long-block baseline, do NOT go to n=4096, prefer multiplicative repetition
  (2,3) mother code. V6-52 chose multiplicative repetition as the single
  successor; a new OpenSpec change must be proposed before implementation.
  [decision]
- Scientific note (diagnostic only): even the p=.30 stratum at 480 checks
  (4.6875 bits/symbol disclosed vs 3.88 entropy) failed 0/4 in 50 iterations
  on full-rate random frames; noiseless and 1-2 planted-error frames converge
  in 1 iteration. Consistent with a structurally weak degree-2 long-block
  baseline, not a tuning issue; canary is sacrificed and must not be tuned or
  rerun. [repo-observed]
- tasks.md V6-51/V6-52 marked complete with gate outcome; v6 change now has
  only the successor-change proposal as open work. [decision]

## 35. Nonbinary LDPC v7 Successor Ladder — All Four Routes failed_canary, Ladder Exhausted (2026-08-02..04)

- Change `formal-nonbinary-ldpc-v7-successor-ladder` freezes the ordered
  route ladder R1A -> R1B -> R2 -> R3 with one shared controller
  (`formal_ir/nonbinary_v7_ladder.py`, hash-bound advance, no confirmation
  path, exactly-once, no-rerun, gates: canary 0/4 in either stratum ->
  `failed_canary`; development ready = per-stratum >=15/16 verified + zero
  forbidden + strict replay + disclosure <=8.75 bits/symbol excluding tag +
  median <=120 s/frame). All v7 evidence lives in
  `openspec/changes/formal-nonbinary-ldpc-v7-successor-ladder/evidence/`;
  all v7 plans/packages live under fresh `workspace/nbldpc_v7_*` roots; no
  official `formal_ir_methods` v7 directory exists. [repo-observed]
- R1A (identity `nbldpc_formal_v7_r1a_mr0`): GF(1024) n=256 (2,3) PEG mother,
  m=170 (168 degree-3 + 2 degree-4 checks, seed 2026080400), flooding
  FFT-QSPA primary, max_iter 100. Engineering accepted (T0 19/T1 64/T2 11/
  T3 97). Sacrificed 4+4 canary executed once + strict-replayed once (exit 0,
  111.0 s / 108.8 s): 0/4 + 0/4 verified, 8/8 `decode_failed` -> canary gate
  fires -> `failed_canary`, frozen; 16+16 not eligible. Package at
  `workspace/nbldpc_v7_r1a_canary_af8ff2e751cf433ba74deb74bbe1deba/canary_plan`.
  [repo-observed]
- R1B (identity `nbldpc_formal_v7_r1b_mr1`): exact R1A mother under new
  identity + one multiplicative repetition (deterministic nonzero GF(1024)
  multipliers, seed 2026080401, rate 1/6 nominal), prior-combining decoder,
  same syndrome 1700 bits + tag. Engineering accepted (T0 15/T1 76/T2 17/
  T3 119). Sacrificed 4+4 canary executed once + strict-replayed once (exit 0,
  59.3 s / 59.6 s): p=.20 3/4, p=.30 0/4 -> gate fires on p=.30 ->
  `failed_canary`, frozen; 16+16 not eligible. Multiplicative repetition
  improved p=.20 but did not close the p=.30 tail. Package at
  `workspace/nbldpc_v7_r1b_canary_a209a853f5e34de69bf930deb60d5673/canary_plan`.
  [repo-observed]
- R2 (identity `nbldpc_formal_v7_r2_qsc_de`): faithful q-ary density
  evolution validated against published vectors (q=2 BSC (3,6) ~0.084;
  BEC (3,6)=0.429438, (3,4)=0.647426, (4,8)=0.383441, (4,6)=0.506132; q=4
  exhaustive checks), bounded search <=32 distributions (degrees 2..8, mean
  check degree <=12), per-stratum n=1024 PEG codebooks with 321 (p=.20) /
  458 (p=.30) checks, layered FFT-QSPA max_iter 100. One frozen-vector
  correction recorded ((3,4) mislabel). Engineering accepted (T0 32/T1 100/
  T2 24/T3 142). Sacrificed 4+4 canary executed once + strict-replayed once
  (exit 0, 1311.2 s / 1308.5 s): 0/4 + 0/4 verified, 8/8 `decode_failed` ->
  gate fires -> `failed_canary`, frozen; 16+16 not eligible. Package at
  `workspace/nbldpc_v7_r2_canary_d6c752a0772043768a1ca88a1ca63ed3/canary_plan`.
  [repo-observed]
- R3 (identity `nbldpc_formal_v7_r3_gf32x2`): reversible 10-bit -> high/low
  5-bit split (split roundtrip SHA256 `4716bf82...`), two GF(32) n=1024 codes
  m0=m1=404/558, layer-0-first with layer-1 priors ONLY from
  Bob/public/verified layer-0, joint 64-bit tag, flooding damped EMS nm=32
  (=q, the exact min-sum GF(32) update, exhaustively validated; FFT-QSPA
  oracle test-only), max_iter 100, disclosure 3.945/5.449 bits/symbol
  excluding tag. Engineering completed (2026-08-04): T0 19/T1 105/T2 33/
  T3 179, independent review 10/10 PASS
  (evidence/v7_r3_engineering_acceptance.json; schema v7_r3_engineering_v1;
  manifest_id b052a92748119b57d426fda4583d697f6577e6761e2b52332fee9f6e13c57582;
  13 reused-source hashes unchanged; check-count freeze m0=m1=ceil(1.15*H_32(p)/5*1024)).
  Sacrificed 4+4 canary staged and reviewed READY-FOR-SINGLE-EXECUTION; a
  minimal canary-only authorization edit applied (run() + CLI + 2 tests;
  post-edit hashes dd8ebe41.../68a17e92.../ad603eab...; first-half plan backed
  up, plan re-created in the same directory with 8 fresh 10303-bit seed
  records disjoint from all 10744 prior seed_ids, file SHA256
  43379354...fca2); executed once + strict-replayed once (exit 0, 668.8 s /
  663.4 s; git porcelain unchanged by replay): 0/4 + 0/4 verified, 8/8
  `decode_failed` (layer-0 failed every frame, 24 transcript events 3/frame,
  verification never invoked) -> gate fires -> `failed_canary`, frozen; 16+16
  development eligibility a separate main-thread decision, not claimed.
  Package at
  `workspace/nbldpc_v7_r3_canary_d006ec637ecb4b1e9463a7f4462eebf3/canary_plan`.
  [repo-observed]
- Process note: the Task tool intermittently returned empty results or
  cancelled/resumed sessions throughout this session (memory triage, several
  coder-fast engineering runs, reviewer-go returns); every completed stage was
  verified on disk before acceptance, and fresh-session retries succeeded for
  R1A/R1B/R2. R3 completion must resume from the existing partial state
  (resume session `ses_0391fa61bffeavVGlmfaDy7q1c` or fresh session with the
  partial-state inventory). [decision]
- Ladder closeout: V7-40 frozen ladder report (evidence/v7_ladder_report.md)
  at HEAD a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344 — first development-ready
  route NONE, `ladder_exhausted` TRUE, all four routes `failed_canary`, every
  failed artifact retained, no official v7 output root, no
  rerun/tuning/confirmation/real data/N4; no fourth route invented (R4
  proximal-ADMM never authorized). V7-41 independent acceptance PASS
  (main-thread-confirmed); V7-42 pending: stop unless a new qualification
  change is proposed. Decision-log entries for the R1A/R1B/R2/R3 canary
  non-promotions and the 2026-08-04 ladder-exhausted closeout exist.
  [decision]

## 36. Nonbinary LDPC v7 Ladder Exhausted — Durable Pattern And Stop Rule (2026-08-04)

- Every v7 route failed its sacrificed 4+4 canary (R1A 0/4+0/4; R1B p=.20 3/4,
  p=.30 0/4 tail; R2 0/4+0/4; R3 0/4+0/4) at max_iter=100, consistent with the
  v6 long-block baseline failure (0/4 both strata at max_iter=50, §34). The
  degree-2/3 PEG ensembles at these rates do not approach the needed
  correction under the frozen FFT-QSPA / EMS decoders on full-rate random
  frames; noiseless and 1-2 planted-error frames converge in 1-2 iterations,
  so this is a structural capacity gap, not a tuning issue. [decision]
- Do NOT re-run or tune any v7 route: the four canary packages are immutable
  non-ready evidence and the current rows are NOT tuning data. No fourth
  route was invented (R4 proximal-ADMM was never authorized). [decision]
- A nonbinary successor must be a NEW OpenSpec change with fresh development
  and confirmation data, new roots, and its code/rate/decoder change frozen
  before new development data. Qualification, promotion, and comparison
  eligibility claims remain unauthorized for every v7 route. [decision]
- No official `comparison_bench/outputs_comparison/formal_ir_methods/` v7
  directory exists before or after the ladder (recursive v7 scans clean);
  all v7 evidence lives under
  `openspec/changes/formal-nonbinary-ldpc-v7-successor-ladder/evidence/` and
  all canary packages under fresh `workspace/nbldpc_v7_*` roots.
  [repo-observed]

## 37. Nonbinary LDPC V8 Reference-Reproduction Correction (2026-08-04)

- New active change:
  `formal-nonbinary-ldpc-v8-reference-reproduction`. It is engineering and
  reference-only: error-domain syndrome algebra, an independent probability
  oracle, full-vector q-ary QSC Monte-Carlo density evolution, and one exactly
  sourced published reproduction. No V8 canary/development/confirmation/
  real/N4/comparison output is authorized. [decision]
- Scientific correction to §§35-36: V7 T0-T3 engineering suites passed, while
  the four scientific canaries failed. The failures reject the frozen
  implementations at their gates; they do not establish that nonbinary LDPC
  as a class has a structural capacity gap. [decision]
- R1B synthesized a second independently corrupted observation from Alice and
  combined it with Bob's observation. Preserve its package, but treat it only
  as an algorithmic diagnostic outside the project's one-Bob-observation plus
  public-disclosure reconciliation contract. [repo-observed, decision]
- R2 used a scalar two-level reliability surrogate rather than full q-entry
  message populations. Its variable update did not faithfully establish the
  paper contract of exact sampled degrees plus a channel term, and its degree
  perspective was not independently reproduced from a q-ary published target.
  Therefore R2 0/8 is evidence about that implementation, not closure of the
  literature's full-vector MC-DE route. [repo-observed, decision]
- V8 must reproduce a precisely cited q-ary QSC reference before any GF(1024)
  project adaptation. If exact degree vectors, perspective, channel convention,
  or target cannot be extracted, stop `implementation_blocked` rather than
  guessing. A future finite-length V9 requires a separate OpenSpec change and
  fresh data. [decision]

## 38. Nonbinary LDPC V8 Reference Reproduction — Implemented, Independently Accepted (2026-08-04)

- V8 reference-reproduction change implemented and INDEPENDENTLY REVIEWED
  ACCEPTED (reviewer-go, read-only, 2026-08-04) at HEAD
  a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344. Operator did not self-accept;
  V8-A01..A12 all pass (A12 satisfied by the independent review). [decision]
- Additive files only:
  `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v8_error_domain.py`,
  `nonbinary_v8_reference.py`, `nonbinary_v8_mcde.py` + 3 tests
  (`test_nonbinary_v8_error_domain.py`, `test_nonbinary_v8_reference.py`,
  `test_nonbinary_v8_mcde.py`) + 7 evidence files under the change's
  `evidence/` dir (v8_engineering_acceptance.json schema v8_engineering_v1,
  v8_source_manifest.json, v8_reproduction_trace.json,
  v8_literature_provenance.json, v8_muller2024_table1_extract.txt SHA256
  d343f0204e87994e64efd32531bc12490fb4e7125cd90b52cfaf2397279b57bd,
  v8_v7_interpretation_audit.md, v8_v9_recommendation.md). [repo-observed]
- Semantics: error-domain contract d = H*(x+y) with reconstruction
  x_hat = y + e_hat; independent direct probability-domain oracle (pairwise
  XOR convolution + sparse support enumeration + brute-force tiny-code
  coset/MAP; imports only GF2mField from nonbinary_field; import-boundary
  enforced — no V1-V7 FFT/FWHT/check-update/decoder calls); full-vector QSC
  Monte-Carlo density evolution (length-q messages, edge-perspective degree
  distributions with tested node/edge conversion, exact sampled degrees per
  update, fresh channel message at every variable update, direct convolution
  with no FWHT, base-q mean message entropy convergence, seeded deterministic
  populations, fail-closed normalization); golden regressions detect the old
  R2 missing-channel and fixed-dv_max behavior. [repo-observed, decision]
- Tiers (pytest -p no:cacheprovider, fresh
  `workspace/nbldpc_v8_reference_9c3f51e2a74b48d9b6c0a5f8e1d23a4b` root):
  T0 11/0, T1 31/0, T2 3/0, T3 179/0 (frozen 16-file v5+v6+v7-R1A/R1B/R2
  regression subset). Reviewer independently re-ran T0/T1/T2: identical.
  [repo-observed]
- Published reproduction (single frozen run, no rerun/tuning): Muller et al.,
  "Efficient Information Reconciliation for High-Dimensional Quantum Key
  Distribution", Quantum Inf Process 23, 195 (2024), arXiv:2307.02225v2,
  Section 3.1 Table 1 row rate 0.75: q=4, DET published 0.069, edge-view
  lambda 0.107x+0.245x^3+0.192x^6+0.034x^9+0.207x^18+0.161x^25+0.049x^27
  (Eq. 13 exponents = degree-1, so DE degrees {2,4,7,10,19,26,28});
  concentrated two-point check distribution inferred from the fixed rate
  dc_mean = 1/((1-R)*sum(lambda_d/d)) = 24.3285893 -> {24,25} (documented
  inference). Frozen params: seed 2026080418, 20000 nodes, max 200
  iterations, entropy < 0.01 base-q for 20 consecutive iterations, p in
  [0.01,0.12] step 0.0025, frozen tolerance 0.015. Result:
  threshold_proxy 0.062421875, delta 0.006578 <= 0.015 -> PASS.
  [repo-observed, decision]
- Output policy: no V8 directory under
  `comparison_bench/outputs_comparison/formal_ir_methods/`; no
  canary/development/confirmation/real-data/N4/comparison execution; frozen
  src/experiments/tools/results and all V1-V7 files unchanged; nothing staged.
  Engineering/reference-only boundary: V8 authorizes only a separate future
  V9 proposal (paper-faithful syndrome reconciliation with reproduced
  ensemble and blind puncturing/shortening, fresh roots); no
  FER/readiness/qualification/promotion/comparison claim. [decision]
- Process note: tasks.md V8-50.7 checkbox remains pending until this memory
  section exists; docs/decision-log.md, CURRENT_TASK.md, and AGENT_HANDOFF.md
  already updated with the same verified facts. [repo-observed]

## 39. Nonbinary LDPC V8-60 Audit-Correction Close-Out (2026-08-04)

- V8-60 was a NON-TUNING FORMULA CORRECTION discovered by an independent audit
  of the accepted V8 candidate (2026-08-04); HEAD
  a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344 unchanged. Three corrections:
  (1) `concentrated_check_distribution` now solves the edge-perspective rate
  condition sum_j rho_j/j = (1-R)*sum_i lambda_i/i EXACTLY for adjacent check
  degrees {floor(dc), ceil(dc)} with w_lo = (target - 1/d_hi)/(1/d_lo - 1/d_hi),
  w_hi = 1 - w_lo, target = (1-R)*integral_lambda, dc = 1/target (integer dc
  degenerates to regular); the old mean-matched weights (w_lo = dc_hi -
  dc_mean) approximated it with ~1e-4 relative error; new public helper
  `reconstructed_rate()`; tests assert |reconstructed_rate - rate| <= 1e-12
  (5 configs). (2) REPRODUCTION_CITATION first author corrected to "Ronny
  Müller" (was wrong given name "Rasmus T. Müller"); full arXiv:2307.02225v2
  author list. (3) Tolerance re-derived with valid arithmetic:
  0.0005 + 0.00125 + 0.005 + 0.005 = 0.01175 <= 0.012 (frozen tolerance 0.012);
  the old claim 0.005+0.003+0.0025=0.015 was arithmetically invalid and is NOT
  reused. [decision]
- Corrective reference run executed EXACTLY ONCE with parameters frozen before
  the run: q=4, R=0.75, Muller et al. 2024 Table 1 row 0.75 (DET published
  0.069), concentrated rho {24: 0.6623423944, 25: 0.3376576056}, n_samples
  100000 and max_iter 150 (the paper's own MC-DE budget), seed 2026080418,
  p in [0.01, 0.12] step 0.0025, entropy < 0.01 base-q for 20 consecutive
  iterations. Result: threshold_proxy 0.062421875, delta 0.006578125 <= 0.012
  -> PASS. No rerun, no tuning. [repo-observed, decision]
- History preservation: evidence/v8_reproduction_trace.json preserved
  byte-identical (SHA256
  dd5678fd2d77b67dd7f3fc7ee221a49b0d33eab37ab5d226d96e6d243b071de3), marked as
  the pre-correction approximate trace via
  v8_reproduction_trace_precorrection_annotation.json;
  v8_engineering_acceptance.json NOT rewritten — its A12=blocked status is
  explicitly resolved by the main-thread evidence/
  v8_acceptance_closeout_addendum.json; v8_literature_provenance.json,
  v8_muller2024_table1_extract.txt, v8_v7_interpretation_audit.md,
  v8_v9_recommendation.md unchanged. [repo-observed]
- New evidence files: v8_reproduction_trace_corrected.json,
  v8_reproduction_trace_precorrection_annotation.json,
  v8_60_correction_evidence.json (formula/constants old->new, tolerance
  arithmetic, source-hash old->new), v8_independent_review_acceptance.json,
  v8_acceptance_closeout_addendum.json. v8_source_manifest.json regenerated
  with v8_60_delta; only two files changed: nonbinary_v8_mcde.py (new SHA256
  2c84a5ee76d09f4d6cea537289ff82d88ab19abd31d1a41951a7d24acdd66543) and
  test_nonbinary_v8_mcde.py
  (a508a4228ee06114424db2242b4db784bfa1b9cabcbae54f4cd7172ed988a81f).
  [repo-observed]
- Golden regressions: q=4 golden re-recorded under corrected rho {4: 1/6,
  5: 5/6} (same seed 2026080420; recording not tuning); omitted-channel/
  fixed_max tamper modes still differ (old-R2 detection preserved); q=8 golden
  byte-identical (regular {6:1.0}). [repo-observed]
- Tiers (V8-60.8 scope, NO T3 rerun): compile exit 0; T0 17/0; T1 32/0; T2 4/0
  (read-only reproduction-trace, source-manifest, no-production-runner,
  precorrection-preservation). Independent reviewer-go re-ran T1 32/0 and
  T2 4/0: identical; overall verdict ACCEPTED
  (evidence/v8_independent_review_acceptance.json), blocking findings none;
  non-blocking: v9 recommendation cites pre-correction numbers (superseded by
  corrected run), cosmetic duplicated line, pre-existing package __init__
  binding. [repo-observed, decision]
- Boundary: V8 remains engineering/reference-only; no V9, no canary/
  development/confirmation/real-data/N4, no official output, nothing
  staged/committed/pushed; only a separate future V9 OpenSpec proposal is
  authorized. [decision]

## 40. Nonbinary LDPC V9 GF(1024) Long-Block Route Frozen (2026-08-04)

- New active OpenSpec change:
  `formal-nonbinary-ldpc-v9-gf1024-long-ir`. V8-60's q=4 reproduction is a
  method/audit validation only; it is not GF(1024) threshold or finite-length
  FER evidence. [decision]
- Frozen autonomous state machine: V9A scalable full-vector GF(1024) WHT
  MC-DE and separate p=.20/.30 ensembles; robust f=1.15 conservative
  multi-seed thresholds must be >=.22/.32 before any codebook. Target f=1.08
  failure permits robust continuation only with
  `efficiency_target_not_met`. Rates/checks are computed as
  ceil(f*H_q(p)*n), with harmonic-exact edge-view rho. [decision]
- On V9A robust PASS only: V9B n=4096 irregular PEG/ACE-or-equivalent graph,
  nonzero GF(1024) labels, error-domain layered log-FFT-SPA (100-150 frozen
  iterations, workers=1), T0-T3 and independent acceptance, then one fresh
  4+4 canary and one strict replay. Gate: >=3/4 each stratum, zero forbidden,
  exact disclosure, median <=2h/superframe, peak RSS <=3GiB. [decision]
- On V9B PASS only: V9C n=16384 fresh 4+4 gate (>=3/4 each, median <=8h,
  <=3GiB), then n=32768 with exactly 32 ordered disjoint 1024-symbol synthetic
  constituents and fixed-rate syndrome/tag leakage. n=32768 uses one fresh
  4+4 canary, then on PASS one fresh 16+16
  development; ready gate >=15/16 each, zero forbidden, strict replay, median
  <=24h, <=3GiB. [decision]
- Every scientific stage is prepare -> independent read-only review -> exactly
  one execute -> exactly one strict replay. Failed evidence is immutable and
  stops the route; no tuning/rerun. V9 stops after the development decision;
  qualification/confirmation/real/N4/promotion/formal comparison require a
  separate future change. [decision]

## 41. Nonbinary V9 Freeze-Review Corrections (2026-08-04)

- V9A robust conservative multi-seed gates are >=.22/.32; target gates are
  >=.215/.32, with .215 below the p=.20 f=1.08 capacity threshold ~.21827.
  All four searches plus validation use one pre-frozen,
  independently reviewed, exactly-once deterministic execute and exactly-once
  strict replay. Target failure selects robust with
  `efficiency_target_not_met`; robust failure stops. [decision]
- All finite matrices require GF(1024) full row rank `rank(H)=m` before plan.
  n=4096/16384/32768 superframes bind respectively 4/16/32 ordered disjoint
  1024-symbol constituents with complete provenance and no cross-stage reuse.
  [decision]
- n=32768 canary has a hard 24h timeout per superframe and median <=16h advance
  gate. V9C is fixed-rate per stratum: `m=ceil(f*H_q(p)*n)`, syndrome leakage
  `L_recon=10*m`, separate fixed 64-bit tag, `L_total=10*m+64`; these are hard
  caps and no shortened/index/other reconciliation payload is allowed. Blind
  adaptation is prohibited in V9 and deferred to a future V10. [decision]

## 42. Nonbinary V12 Real Micro-Feasibility — source_partition_blocked (2026-08-13)

- Change: `formal-nonbinary-ldpc-v12-real-micro-feasibility`. Terminal state
  **source_partition_blocked** (`partition_state` and `plan_state`
  `source_partition_blocked`): 0 frames, 0 seed records, no decoder, no
  arrays. Implementation V12-I01..I05 complete; engineering acceptance
  V12-T0..T2 passed 41/41 tests (prepare-only production lane added to the six
  V12 files: `nonbinary_v12_real_micro.py` `prepare_production`,
  `partition.py` `prepare` with `production_prepare_authorized`, CLI `prepare`
  action). [repo-observed, decision]
- Root cause: the reconstructed traceable 10 dB pool (2304 rows, 768 per
  stratum incl. 768 bw200) is 100% covered by historical identities from the
  V4 10 dB/16 dB transfer locks (20260729_v1/v2) and V5
  development/partition role locks (20260731_v1): 2848 excluded frame + 2688
  excluded payload identities, zero eligible bw200 rows -> no source rows to
  partition. [repo-observed]
- Official preparation package (exactly 3 artifacts):
  `comparison_bench/outputs_comparison/formal_ir_methods/20260813_v2_nonbinary_v12_real_micro/`
  (`exclusion_manifest.json`, `partition_lock.json`, `pre_run_plan.json`;
  schemas `nbldpc_v12_exclusion_manifest_v1` / `partition_lock` / `plan`;
  run_id `nbldpc_v12_real_micro`). The v1 intermediate package
  (`20260813_v1_...`) was deleted by explicit user decision; v2's exclusion
  manifest (33 packages) still lists the deleted v1 package as a
  formal_package with 0 identities. [decision]
- V12-X01/X02 never ran (blocked — no eligible frames). V12-D01 recorded;
  V12-D02 completed 2026-08-13. `docs/decision-log.md`,
  `AGENT_HANDOFF.md`, `CURRENT_TASK.md`, and the §42 memory triage were
  updated. [repo-observed]
- Scientific implication: a fresh acquisition is required for any future
  four-frame bw200 canary; no successor/rerun/tuning/promotion is
  automatically authorized. Claim boundary: no finite decoder correction
  established for the existing pool. [decision]
- Procedural: the user's own binary V5 transfer-evaluation work
  (`ldpc_v5_transfer_evaluation.py`,
  `run_ldpc_v5_transfer_evaluation.py`,
  `outputs_comparison/transfer_evaluation/`) is user-owned/kept, out of V12
  scope, adjudicated as NOT a V12 operator violation — an evaluation-only,
  non-qualification retrospective transfer evaluation of frozen V5-C2
  (2026-08-12). [decision]
- Status supersession: the 2026-08-12 AGENT_HANDOFF current state (binary LDPC
  v5 REAL PROMOTED) is now previous state; V12 blocked supersedes it as
  current. The pre-existing 2026-08-13 mainline-fusion merge entry at the top
  of this file is unchanged and not duplicated here. [repo-observed]

## 43. Nonbinary LDPC V13 Existing-Data Diagnostics Plan (2026-08-14)

- User decision: diagnose the nonbinary LDPC algorithm on the existing 10 dB
  Type-II, q=1024, Gray, 256-symbol data before considering a new acquisition.
  V12 remains terminal `source_partition_blocked`; V12-X01/X02 are not
  reopened. [decision]
- The existing pool is sufficient for retrospective diagnostics/development,
  including channel aggregates, tiny interface oracles, optional decoder
  telemetry, and post-hoc exact-correction checks. Its frame/payload identities
  are already used by V4/V5, so every V13 artifact is
  `diagnostic_only`/`retrospective_reuse`; it is not fresh canary,
  confirmation, qualification, or promotion evidence. [decision]
- New OpenSpec change:
  `formal-nonbinary-ldpc-v13-existing-data-diagnostics`. Status is **PLAN
  DRAFTED / EXECUTION NOT AUTHORIZED**. P01-P07 are drafted; P08 independent
  read-only freeze review is pending. All D/R/I/E/A/C tasks are unexecuted and
  unauthorized. [repo-observed]
- Frozen plan: bw200 is primary; bw120/bw180 are deferred to a post-bw200
  cross-stratum check. Reconstruct mutually exclusive characterization,
  development, and retrospective-audit roles; ambiguous history yields
  `blocked_role_ledger`. Prefer V5 development as NB development and sealed
  V5 real frames as frame-identical audit without relabeling V5 evidence.
  [decision]
- Alice truth is allowed only for offline aggregates and post-hoc exact
  equality. It cannot enter decoder prior, stopping, candidate selection,
  retry, frame ordering, or same-frame tuning. Persistent telemetry contains no
  raw Alice/Bob arrays or per-position error masks; only required aggregate and
  decoder-internal traces are planned. [decision]
- D-stage D05 emits separate fields: `diagnosis_class` is exactly `interface`,
  `prior`, `decoder`, `code`, `mixed`, or `inconclusive`; `run_state` is
  `diagnosis_complete` for a supported single-factor conclusion and
  `diagnosis_inconclusive` for mixed/insufficient evidence. A D02/oracle
  failure may directly set `run_state=implementation_interface_fault`.
  Diagnostic engineering gates are V13-DT0/DT1/DT2 before D04; candidate
  implementation gates are V13-IT0/IT1/IT2/IT3 before E01.
  After D05 and a new amendment, at most one prior-only, decoder-only, or
  code-only candidate may be selected; mixed/inconclusive stops the route.
  [decision]
- Future additive diagnostics, if separately authorized, use
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/<run_id>/` with
  six minimal artifacts: `data_role_ledger.json`, `channel_diagnostics.json`,
  `diagnostic_outcomes.csv`, `decoder_telemetry.jsonl`,
  `root_cause_report.json`, and `diagnostic_run_manifest.json`. Frozen
  `src/`, `experiments/`, `tools/`, `results/`, and official
  `formal_ir_methods` roots remain unchanged. `diagnostic_outcomes.csv`
  contains baseline, candidate-development, and retrospective-audit rows with
  `phase` and `method` fields. [decision]
- Allowed `run_state` values are `plan_only`, `blocked_role_ledger`,
  `implementation_interface_fault`, `diagnosis_complete`,
  `diagnosis_inconclusive`,
  `failed_existing_data_feasibility`, `retrospective_non_ready`,
  `ready_for_fresh_confirmation`, and `invalid_diagnostic_execution`.
  `promoted`, `qualified`, and `observed_fresh_correction` are forbidden.
  Fresh acquisition/qualification requires a separate OpenSpec change and
  explicit user decision. [decision]

## 44. Nonbinary LDPC V13 Existing-Data Diagnostics — D-Stage Complete (2026-08-14)

- Change: `formal-nonbinary-ldpc-v13-existing-data-diagnostics`. **PLAN
  FROZEN**: P01-P08 accepted via independent read-only freeze review, zero
  blockers; four non-blocking planning corrections applied (code-branch
  evidence source pinned to offline short-cycle/girth analysis plus frozen
  rank=170 facts; spec scenario added; 512/stratum V5 development basis for
  32+64 denominators; V7 R1A label harmonized). [decision]
- D stage authorized and completed: D01-D03 plus DT0-DT2 (D04/D05 NOT
  authorized). New files: `comparison_bench/src/comparison_bench/formal_ir/
  nonbinary_v13_diagnostics.py`, `cli/run_nonbinary_v13_diagnostics.py`,
  `cli/verify_nonbinary_v13_diagnostics.py`,
  `tests/test_nonbinary_v13_diagnostics.py`. Tests 21/21 passed
  (DT0 8 + DT1 8 + DT2 5) in fresh `workspace/nbldpc_v13_<uuid>/` roots with
  `pytest -p no:cacheprovider`. [repo-observed]
- D01 real run exactly once: run_id `v13_d01_20260814`, package
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13_d01_20260814/`
  (six-file set). Role ledger 2304 rows = characterization 384 (128/stratum) +
  development 1536 (512/stratum) + retrospective_audit 384 (128/stratum);
  mutually exclusive, zero V4<->V5 identity overlap. [repo-observed]
- bw200 aggregates (128 frames, 32768 symbols, aggregate-only, no raw arrays
  persisted) — **empirical observations only, no root-cause conclusion (D05
  not run)**: raw SER mean 0.0771 (min 0.0391, max 0.1133); bit-plane
  mismatch monotone MSB->LSB 3.1e-5 .. 3.75e-2; zero-diff mass 0.9229, only 8
  runs max run length 2 (isolated errors, no bursts); QSC p=.20 calibration
  mismatch 0.1229; model entropy 2.722 b/symbol; NLL mean 1.247 b/symbol;
  empirical conditional entropy / necessary-leakage lower bound 0.547 b/symbol
  (empirical diagnostic, not a Shannon or finite-length proof). [repo-observed]
- D03 hook: wrapper/adapter only, V7 R1A sources byte-unchanged; hook-off
  element-for-element identical; hook-on adds aggregate telemetry without
  changing word/status/iterations. Independent read-only review: ACCEPT, zero
  blockers; two non-blocking warnings (stale planning docs — updated;
  manifest time field missing — noted for D04). [repo-observed]
- Claim boundary: highest V13 state is `ready_for_fresh_confirmation`; no
  decoder correction/qualification/promotion established. D04 (32-frame bw200
  baseline probe) requires separate main-thread authorization after DT0-DT2;
  D05 (root-cause report) requires D04; real-data decoder execution remains
  unauthorized. V12 remains `source_partition_blocked` (not reopened).
  [decision]
- Procedural: AGENT_HANDOFF.md / CURRENT_TASK.md updated 2026-08-14 with V13
  D-stage-complete as current state; V12 entries retained as previous state.
  [repo-observed]

## 45. Nonbinary LDPC V13 — D04 Baseline Probe Authorized, Implemented, Executed Once (2026-08-14)

- Change: `formal-nonbinary-ldpc-v13-existing-data-diagnostics`. Main thread
  authorized V13-D04 (unchanged V7 R1A `p=.20`, 32 pre-registered bw200
  development frames, exactly once). [decision]
- Implementation (in `comparison_bench/` only): `run_d04` core lane in
  `nonbinary_v13_diagnostics.py` (deterministic pre-registration sorted by
  frame_id, D04-limited manifest authorization, frozen-failure packages at
  `implementation_interface_fault`/`blocked_role_ledger`/
  `invalid_diagnostic_execution`), CLI `d04` action (requires `--authorized`
  + `--production` + fresh output root; `d05` remains a hard stop exit 2),
  read-only `verify_package` D04 branch, and DT3 lane tests (fake lifecycle,
  tamper, Alice boundary, no-overwrite, frozen failures). Tests 27/27 pass.
  V7 R1A frozen sources byte-unchanged; hook equivalence held on all frames.
  [repo-observed]
- D04 production run exactly once: run_id `v13_d04_20260814`, six-file package
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13_d04_20260814/`,
  strict read-only verifier PASS (32 outcome rows, 32 telemetry records,
  ledger ready 2304). Outcome: **8/32 `syndrome_consistent` + `exact_correct`
  (all converging at iteration 1), 24/32 `decode_failed` at the 100-iteration
  limit, zero `decoder_error`, zero exact mismatches, zero
  non-finite/normalisation/underflow events.** Telemetry observations
  (empirical only, no D05 conclusion): decode_failed frames end highly
  concentrated (mean posterior max 0.986, entropy 0.103 bits) with mean 3.79
  unsatisfied checks; oscillation detected on 11/32 frames. [repo-observed]
- Claim boundary: package run_state=`plan_only`, `d05_emitted=false`; no
  diagnosis_class/run_state conclusion. D05 (root-cause report + independent
  review) remains unauthorized and unimplemented; R/I/E/A/C locked; no
  decoder execution beyond the 32 pre-registered frames. 8/32 is not
  promotion/qualification/fresh correction. [decision]
- Procedural note: writing the package to the official
  `nonbinary_diagnostics/` root required a one-time sandbox escalation
  (danger-full-access, user-approved); normal workspace-write mode denies
  process writes under `comparison_bench/outputs_comparison/` (observed
  again on `__pycache__` and probe mkdirs). Future official-output runs from
  this harness need the same escalation. [repo-observed]

## 46. Nonbinary LDPC V13 — D05 Root-Cause Report: code / diagnosis_complete (2026-08-14)

- D05 emission (main-thread authorized per the recommended steps): offline
  girth analysis shows the frozen V7 R1A graph is **85 disconnected 2-check
  components** (256 all-degree-2 variables; 84 pairs with 3 parallel edges +
  1 pair with 4; Tanner girth 4; per-component kernel d_min = 3). Structural
  ceiling over the 32 D04 development frames: structural failure fraction
  0.75 == observed failure fraction 0.75 with **perfect frame-level
  correspondence** (24/24 decode-failed frames contain >=1 component with
  >=2 errors; 8/8 exact-correct frames contain none). [repo-observed]
- Emission `v13_d05_20260814_corrected` (authoritative, verifier PASS):
  `diagnosis_class=code`, `run_state=diagnosis_complete`, successor **R3
  code-only**; QSC p=.20 prior mismatch (calibration 0.1229, |entropy gap|
  2.17 bits/symbol) documented as co-factor (structure alone explains 100% of
  the observed failures). First emission `v13_d05_20260814` invalidated by a
  decision-machinery defect (ceiling doc lacked observed fractions -> default
  1.0; signed entropy-gap comparison), preserved immutably with sibling
  notice `v13_d05_20260814_invalid_execution_notice.json`; V8-60 precedent
  (fix + one additive re-emit). Decision-log 2026-08-14. [repo-observed]
- Decisive cross-checks: consistent with V7 synthetic canaries 0/4+0/4 (SER
  0.20 -> ~51 errors/frame -> every component multi-error); the D04 bimodal
  behavior (iteration-1 success vs 100-iteration failure) is the 4-cycle
  message-passing signature; D01 corrected run stats (2340 runs, max 3, 92.7%
  singletons) and 99.3% of nonzero diffs < 128 remain channel facts. [decision]
- Boundary: independent read-only review (reviewer-go) of the D05 conclusion
  is the next scientific gate; R1/R2 locked; R3 requires OpenSpec amendment +
  freeze review + main-thread approval; highest state remains
  `ready_for_fresh_confirmation`; promoted/qualified/observed_fresh_correction
  forbidden. [decision]

## 47. Nonbinary LDPC V13 — R3 候选 E01/A01/A02 全绿 → ready_for_fresh_confirmation (2026-08-14)

- R3 code-only candidate `nbldpc_v13_r3_code_v1`（amendment 冻结）：连通
  简单 check 图（170 校验节点、256 全 degree-2 变量、校验度 168x3+2x4、
  无平行边、check-girth 4/Tanner girth 8、rank 170），确定性种子搜索冻结
  seed=20260818；prior（QSC p=.20）、decoder 接口（flooding FFT-QSPA 镜像
  循环）、校验数/rate/max_iter 全不变。实现 `nonbinary_v13_r3_candidate.py`
  + `run_e01`/`run_a01`/`run_a02` + CLI + verify 分支；测试 49/49（含 IT0-
  IT3 与 A01/A02 fake 生命周期）。[repo-observed]
- **E01**（v13_e01_20260814，64 个预注册 bw200 development 帧）：
  candidate **64/64 exact_correct**，baseline（unchanged R1A）13/64，零
  forbidden；门通过。**A01**（v13_a01_20260814，128 个 frame-identical V5
  audit 帧，candidate-only 预注册）：**128/128 exact_correct**（raw SER
  0.039–0.113），median 0.90 s/frame，disclosure 6.640625 ≤ 8.75 → 门全过
  → **run_state=`ready_for_fresh_confirmation`**（V13 最高状态）。
  **A02**（v13_a02_20260814，bw120+bw180 各 128 audit 帧）：128/128 与
  128/128，readiness gate 满足，no_state_promotion=true。六个生产包全部
  只读 verifier PASS、git 提交。闭环：与 D05 `code` 诊断一致——图连通性/
  girth 是根因，替换后同先验下全部精确纠错。[repo-observed]
- 科学边界：ready_for_fresh_confirmation 不是 promotion/qualification/
  fresh correction；fresh acquisition 已由用户决定、新开独立 change
  （见 §50）。V13 **C01 完成**（独立验收 ACCEPT、零 blockers；本记忆
  triage 即 C01 的记忆部分）；V12 已正式归档（2026-08-15，见 §50）。
  [decision]
- 可复用经验：E01/A01 候选帧解码 median ~0.9–1.0 s/帧（q=1024 flooding，
  大多帧 1–2 轮收敛）；一次 E01 全屏（64 帧×2 解码）约 20–40 分钟，A01
  （128 帧）约 5–10 分钟——远比最坏 100 迭代估计快，因为收敛帧占多数。
  [repo-observed]

## 48. Nonbinary LDPC V14 效率可行性门——冻结、实现、执行中 (2026-08-14)

> 2026-08-15 supersession：本节为门执行前的中间状态；门已执行完毕，
> **gate_state=fail**、效率路线冻结（见 §49），V15/V16 归档为 aborted
> drafts（见 §50）。

- 立项依据：SciVerse 调研（docs/nonbinary-ldpc-efficiency-roadmap-survey.md）
  ——文献效率锚点 Müller 2024 f=1.078–1.14（q=8），V13 R3 f≈12.1 需高码
  率（m≈15–18 → rate 0.93–0.94）+ 结构化先验（H=0.547 vs QSC 2.72）。
  [decision]
- 冻结门：3 λ × m∈{15,16,17,18} 共 12 点评估；Stage 0 QSC 回归
  （0.069±0.012）；Stage 1 折叠 φ_m 小 q 验证；Stage 2 q=1024 点评估；
  PASS=f≤1.3 且收敛；FAIL=路线冻结。预算 3 GiB/24h/execute-once+回放；
  降级链 Li→Cohen→resource_blocked。freeze review：首轮 BLOCKERS 修复后
  ACCEPT。 [decision]
- DE 机制事实（可复用）：V9 run_mcde 信道块（:446-457）~10 行改动即
  支持任意 w（更新核已接受任意 (N,q) 先验）；q=1024 单点 DE 可行
  （numba ~1.18s/500样本×30迭代）而 profile 搜索不可行（V11 66.7h）；
  V9A/V10/V11 失败根因=测量前承诺不可达门限/零候选/继承门限。
  [repo-observed]
- 实现（flash 子代理 + 独立 verifier ACCEPT）：nonbinary_v14_channel.py
  / nonbinary_v14_mcde.py（numba 本地核，QSC 与 V9 等价 1e-12）/ cli/
  run_v14_gate.py；测试 64/64；V8/V9/V11/V13 源码零改动。gate 首启失败
  （证据目录整体 fail-closed 误伤先存的模型文件）已修为按文件
  fail-closed。 [repo-observed]
- 下一步：门结果 → V15（高码率候选，合成资格；fresh 实数据需用户决定
  采集）/ 或路线冻结声明；V16（rate-adaptive + syndrome 估计 + 子块确认）。
  [decision]

## 49. Nonbinary LDPC V14 效率可行性门——FAIL：普通系综在 f<=1.3 无解 (2026-08-15)

- V14 门执行一次（evidence 提交 1cdc63b6；E02 独立 review ACCEPT）：
  Stage 0 QSC 回归 PASS（proxy 0.060 vs 0.069, |d|=0.009<=0.012）；
  Stage 1 折叠验证全绿；Stage 2 的 12 个冻结点（3 λ × m∈{15..18}，
  q=1024 结构化信道）全部非收敛——最终 base-q 熵 0.288-0.357（阈值
  0.01 的 29-36 倍，非边际）；f 值 1.032-1.239 全满足 <=1.3 但收敛是
  绑定判据 → gate_state=fail。预算 wall 87min/577MiB。 [repo-observed]
- 科学含义：码率点全在容量内（R<=0.9414 vs C~0.9432）→ 非信息论不可
  能，是普通不规则系综（degree-2 含 λ、dc~51 集中 ρ）在高码率的 BP
  阈值结构性缺口（与 V10/V11 的 QSC .22/.32 失败同类）。机制可信
  （T2 与 V9 等价 1e-12 + Stage 0 文献回归双背书）。 [decision]
- 后果：V15/V16 不立项（提案/骨架保留为 gated drafts）；效率路线冻结；
  下一步只能用户决定新 change（SC-LDPC 阈值饱和 / Cohen 位面分解 /
  多边族），且必须新 DE 门先行。V13 R3（f~12）仍为唯一验证正确器；
  fresh-confirmation-only 路线不受影响。 [decision]
- 可复用经验：q=1024 结构化 DE 单点 ~7 min（numba；12 点 87 min）；
  普通 irregular 系综在 rate>0.93 不收敛是"可预测的负结果"——高码率
  必须换系综族而非调 profile；gate-first 纪律防止了 V15 的浪费性构造。
  [repo-observed]

## 50. P0 状态收口 + P1/P2 新目标 (2026-08-15)

- **P0 收口（用户更新目标，纯 housekeeping，无科学执行）**：V12 正式
  归档 → `openspec/changes/archive/2026-08-15-formal-nonbinary-ldpc-v12-real-micro-feasibility/`
  （保留 `source_partition_blocked`、X01/X02 未执行、v2 prepare 包；
  归档≠成功、不重开执行；delta spec 未合并——V9/V10 先例）。
  V15/V16 归档为 **aborted drafts**（`...v15-high-rate-candidate-aborted/`、
  `...v16-rate-adaptive-deployment-aborted/`；未立项/前置门失败；delta
  spec 未合并）。陈旧文档全部修复：CURRENT_TASK.md、V14 tasks.md
  （头部状态、测试数字、回放完成）、V13 tasks.md（C01 COMPLETE、
  IT0-IT3 49/49——原始记录为 `test_nonbinary_v13_diagnostics.py` 49 个
  test）、AGENT_HANDOFF.md（Current State 重写）、记忆 §47/§48。
  V14 测试数字统一：修复前 13+49=62/62 → 修复后 15+49=**64/64**
  （decision-log 2026-08-14 原始记录）。本地领先 `origin/main` 28 个
  提交；push 待单独授权。 [decision]
- **P1（立即优先）**：V13 R3 fresh acquisition——新开独立 OpenSpec
  change `formal-nonbinary-ldpc-v13-r3-fresh-acquisition`（不复用 V12
  执行身份、不自动宣称 promotion）。冻结：新 frame/payload identities；
  acquisition/window/stratum 设置；characterization/canary/confirmation
  角色隔离；R3 码本（nbldpc_v13_r3_code_v1）、先验（QSC p=.20）、
  max_iter=100 保持不变；分布漂移与无 eligible frame 停止规则；失败
  原样保留、禁替换帧/调参/重跑。流程：冻结 → prepare → 主线程 review
  → 单次 fresh execute → 只读 verify → fresh-confirmed / frozen
  failure。证据收益最高、技术不确定性最低；只回答"R3 在 fresh 数据上
  是否仍能纠错"，效率仍 f≈12。 [decision]
- **P2**：独立效率研究门 `formal-nonbinary-ldpc-v17-multibit-structured-de-gate`
  ——只做可行性门、不构造有限码。次序：Cohen/多位信道机制复现门 →
  V13 已观测 MSB→LSB 单调失配映射为冻结信道模型 → 预注册少量边标签/
  位面候选 → 执行前冻结收敛/效率/预算/replay 标准 → 一次执行。
  PASS → 另开有限码 candidate change；FAIL → 冻结，不启动 V15/V16、
  不扩大搜索。选它作第一效率路线：直接对应当前数据的位面不均匀性；
  SC-LDPC 在 QSC 下负耦合增益、结构化信道下未否定，排第二；多边/
  高维 λ 搜索空间大，排第三。 [decision]

## 51. P1 prepare 执行（no_eligible_frames）+ P2 V17 门实现与生产执行 (2026-08-15)

- **P1（fresh acquisition）PREP 完成**：change 冻结 + 独立 freeze review
  ACCEPT（三个警告 amendment 修复：A02 表述、规模不足规则
  `insufficient_eligible_frames`（eligible<192 冻结）、漂移阈值引用 V13
  D01 参考区间）。PREP 工具由 flash 子代理实现（FA1–FA5 全过、19 测试、
  decoder-free/array-free、复用 V12 partition 排除机制、身份
  `v13r3fresh-<stratum>-<uuid>`（sha256(seed||canonical)）、schema
  `nbldpc_v13r3_fresh_plan_v1`/`no_eligible_v1`/`insufficient_v1`、
  production_prepare_authorized 默认 False）。主线程独立重跑 19/19。
  生产 prepare 执行一次（提交 17542dc4）→ **`state=no_eligible_frames`**
  （`D:\Data` 无 fresh 10 dB Type-II 帧数据源——最新 2026-07-28 JSI
  非帧数据）；包
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_prepare_20260815/no_eligible_package.json`
  （decoder 不变式完整冻结）。主线程 review ACCEPT → 判定 **frozen
  failure（数据不可得）**；execute/verify 阻塞；用户提供 fresh 数据后
  重新 prepare（确定性工具，非失败重跑）。 [decision]
- **P2（V17 门）实现完成**：freeze review ACCEPT（两个警告 amendment
  修复：评估点集固定 m∈{15,16,17,18} 全集、Stage 0 锚点 A/B 具体化
  （内部一致 ≤0.005 + 文献交叉 |δ|≤0.012，无布尔 fallback））。
  实现由 flash 子代理完成（VA1–VA6 全过、17 测试、5 新文件：stage0/
  channel/mcde/CLI/tests；V8/V9/V11/V13/V14 源码零改动）；主线程独立
  重跑 17/17。Stage 1 模型从 D01 包只读构建：per-bit-plane 错误概率
  = `aggregates.bit_plane_mismatch.mismatch_rate`（10 值 MSB→LSB 单调
  3.05e-5→3.75e-2），joint_structure=`product_of_per_plane_marginals`
  （D01 无联合统计，显式声明保守近似），entropy=0.549955 bits/symbol
  （≈V13 0.547 一致）。Stage 2：3 候选（bitplane/edgelabel/planeweight）
  × m∈{15,16,17,18}。生产 gate 执行中（2026-08-15，后台）。 [repo-observed]
- 提交链：fb6e579d（P0）→ 240e3a2e（P1/P2 立项）→ 3a6d2990（决策日志）
  → 037ee5a6（freeze ACCEPT+amendment）→ 757464f4（W1 完全关闭）→
  d801427c（P1/P2 实现）→ 17542dc4（P1 prepare 包）。 [repo-observed]

## 52. P2 V17 门生产执行完成：mechanism_unverified（FAIL 类）(2026-08-16)

- **生产 gate 执行一次**（后台任务，wall 7026.6 s，peak RSS 541 MB
  ≤ 3 GiB/24h）→ **`gate_state=mechanism_unverified`**。Stage 0
  锚点 A（q=4 退化 p1=p2 内部一致性）**失败**：bit-plane 分解阈值
  0.0525 vs 符号级 0.0600，Δ=0.0075 > 0.005（方向性成立：位面分解
  p=0.055 起 joint 未收敛，符号级至 0.060 仍收敛）；锚点 B（文献
  交叉）通过：|0.060−0.069|=0.009 ≤ 0.012。Stage 1 模型构建成功
  （D01 只读聚合，10 位面误码率 3.05e-5→3.75e-2 MSB→LSB 单调，
  product-of-marginals 显式保守近似，熵 0.549955）。Stage 2 诊断
  12/12 未收敛（bitplane/edgelabel/planeweight × m∈{15..18}，
  f_achieved∈[1.065,1.279] 全 < f_limit 1.3，收敛为绑定判据），
  diagnostic_only=true，无 pass_point。
- **strict replay 5/5 字节一致**（`workspace/v17_replay_20260816/`
  副本 + `replay` 动作 ok=true，`v17_replay_evidence.json` 记账）；
  **E02 独立 gate review ACCEPT（零 blockers）**（G1–G7 全过：
  判定链/数值/纪律/预算/schema/回放/执行器范围）。C01 收尾完成：
  decision-log 2026-08-16 条目 + 记忆 §52 + tasks.md I/E/C 全部
  checked + CURRENT_TASK/AGENT_HANDOFF 同步（本地提交）。 [decision]
- **冻结纪律生效**：位面/边标签效率路线冻结；不启动 V15/V16、不
  扩大搜索、无"最接近"续行、无 rerun/调参；Stage 2 诊断点不构成
  效率结论。效率路线下一步只能由用户决定另开新 change（② SC-LDPC
  仍排第二——QSC 负耦合、结构化未否定；③ 多边/高维 λ 第三）。
  P1（V13 R3 fresh acquisition）独立推进不受影响，仍阻塞于 fresh
  数据（用户提供后重新 prepare 即可）。 [decision]
- 证据：`openspec/changes/formal-nonbinary-ldpc-v17-multibit-structured-de-gate/evidence/`
  6 文件（v17_stage0 / v17_multibit_channel_model / v17_stage2 /
  v17_gate_decision / v17_gate_manifest + v17_replay_evidence 记账）。
  本地领先 `origin/main` 36 个提交；push 待单独授权。 [repo-observed]


## 53. V13-R3 fresh 数据准入——2026-01-21 三源拒绝 (2026-08-16)

- 用户提供三个 `D:\Data\Raw Data\2026.1.21\...` Type2 ttbin 源后，按修正后的
  “v13r3fresh_20260816” 规划执行 **D0 数据准入**：判定
  `data_intake_rejected_for_fresh_confirmation`。
- 原因：时间戳 2026-01-21 早于 frozen fresh 边界；损耗/10 dB 元数据不可核验；
  folder1 已有 Release D2 烟测 `raw_ser=0.254663`，远超 V13 D01 参考 0.0771。
- 证据包：
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_intake_20260816/intake_decision.json`。
- 修正规划：
  `docs/nonbinary-ldpc-v13-r3-fresh-data-intake-20260816-plan.md`。
- D1–D5 已于 2026-08-16（shell 可用后）执行完毕：D1 环境/git 基线、
  D2/D3 三源 sidecar（`map_sanity` 全 FAIL）、D4 三源 pairs-table + manifest、
  D5 全量漂移预检。D5 三源全部 `precheck_state=drift_exceeded`
  （raw SER mean ≈0.240–0.256，偏差远超 0.03 阈值），自动停止，不进入 P/E/V。
  真正 fresh 数据到达前，P1 保持 `no_eligible_frames`；push 仍待用户单独授权。

## 54. V13-R3 legacy drift audit——2026-01-21 三源执行 (2026-08-16)

- 用户决定：使用三份 `2026-01-21` Type2 数据继续，不要求 fresh 边界。
- 新 change：`formal-nonbinary-ldpc-v13-r3-legacy-drift-audit`；claim boundary
  仅 `legacy_drift_audit`。
- 实现：`formal_ir/nonbinary_v13r3_legacy_audit.py`、
  `cli/run_v13r3_legacy_drift_audit.py`、8 个测试。
- 生产执行一次：每源前 64 完整帧（frame_id 0..63），共 192 帧；不变 R3
  候选 `nbldpc_v13_r3_code_v1` 解码。结果 **188 exact_correct**、
  **4 decode_failed**（`iteration_limit`：type2_1M frame 15/20、
  type2_2M frame 52/56）；失败原样保留；只读 verify OK。
- 证据包：
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3_legacy_drift_audit_20260816/`
- 边界：不构成 fresh-confirmed / promotion / qualification；P1
  `no_eligible_frames` 与 P2 V17 `mechanism_unverified` 均不变。push 待授权。

## 55. V13-R3 legacy drift audit——全量 8412 帧完成 (2026-08-16)

- 在 192 帧审计后，用户要求继续；使用 `--all-frames --chunks 8` 并行执行全量。
- 结果：8412 帧中 **8284 exact_correct**、**128 decode_failed**（iteration_limit）、
  0 exact_mismatch。分源：2729/2767、1970/2000、3585/3645。
- 8 chunk 各自 verify OK；合并包：
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3_legacy_drift_audit_full_20260816/`
- 边界：legacy_drift_audit only；不构成 fresh/promotion/qualification。

## 2026-08-20 V29 retrospective finite-code gate: FAIL and V30 successor (historical pre-execution snapshot)

- Canonical V29 `run_02` stopped after 9 persisted 1M blocks under explicit
  user authorization: exact=1, tag_verified=1, 8 failures, remaining=91,
  maximum possible=92<95. Terminal `v29_finite_gate_fail`; readonly verifier
  `ok=true`; prefix FER is `observed_prefix_only`, never full FER.
- V29 `run_01` is retained as superseded 0-call `implementation_blocked`.
- Correct V28 lifecycle: the original ACCEPT was superseded by V28R; V28R is
  engineering evidence only. Its independent L1 audit is 15 support groups,
  max group 69, 303 duplicate projective classes, 922 columns in duplicate
  classes, and 1107 guaranteed proportional/weight-2 pairs, proving
  `d_min<=2` for that finite construction. This is not a GF32×GF32 route
  impossibility result; it is a projective-duplicate matrix defect.
- The original V30 `FROZEN_P102_ACCEPTED` projective-safe finite-graph gate is
  superseded by V30R `FROZEN_P103_ACCEPTED`. At the time of the P103 review,
  V30R only had authorization to proceed and had not yet claimed execution.
  V30R reuses V26 channel semantics and V29 leakage policy but must not reuse
  the V29 holdout as fresh qualification. This historical snapshot predates
  the later V30R execution and is superseded by the V30R closeout at the top
  of this file.

## 2026-09-04 V72P2D1-PARITY corrigendum link (descriptive-only correction, history unchanged)

- Corrigendum [decision]: `docs/research_cycles/V72P2D1-PARITY/CORRIGENDUM.md`
  corrects the M1-M7 "four-cycles 1196/1196, collisions 1194/1194
  (graph-isomorphic)" reading; pure-H check-check 1196/1196 does not imply
  fixed-symbol-grouping full-factor-graph isomorphism
  (symbol-factor-check 8452/328, collision rows 8170/326);
  D1 is input-syndrome consistency only (NOT_RECORDED: candidate syndrome
  violation count, quantiles, sum(c2v), prior-only baseline, edge gain);
  two-arm 72ckpt candidate-vs-Bob all 0, A334/B321, verification failed,
  metering 9100/9171 retained. Descriptive-only; incomplete observations
  are not PASS. No decoder run / rerun / tuning / four-file overwrite /
  per-symbol key read.

## 2026-09-04 V72P2D1 algorithm-route exploration (read-only, proposed successors)

- `docs/research_cycles/V72P2D1-PARITY/ALGORITHM_ROUTE_RESEARCH.md` records
  the route study at b04e5757. Pure-H four-cycle/collision counts are
  1196/1196 and 1194/1194; symbol-factor 8452/328 is a workspace recount,
  while symbol/collision rows 8170/326 remain external, not repo-verified.
- The b04 O1 supplement read only the four VAL1726--1729 frames (not CAL) and
  is `POSTHOC_RECONSTRUCTED`; this route exploration itself read no raw/parquet,
  ran no decoder, and did not change code, results, or lifecycle.
- Static review found no active-path LLR-direction, local-factor
  self-exclusion, syndrome-aware SPA, or warm-start semantic error. The
  Bob-oriented weak-fixed-point explanation is an inference, not a proven root
  cause. `run_incremental_decoder` returning stale variable-to-check output is
  a separate known bug; current D1 used `run_decoder`.
- The mother has 1204 high-degree columns (mean degree about 26.2035) versus
  9035 degree-2 and one degree-1 parity columns. Fixed symbol grouping leaves
  symbol edge totals 19/20/303 in both A/B; a degree-balanced interleaver and
  grouped-symbol mask BP are `PROPOSED`, not accepted designs.
- M0 hierarchical prior (lambda 221.22162910704503, CE about 7.135/7.150)
  and historical V70R1 M2 (VAL CE 6.7871) should be compared only under a new
  frozen plan. Proposed next diagnostic is one-block L/I/P orthogonal triage;
  three arms failing to escape would stop binary edge-level micro-tuning and
  permit proposing tiny exhaustive grouped-symbol-mask or GF32 comparison work.

## 2026-09-04 双 PRIVATE 仓分离终态：拓扑/remote 布局（durable）

- 终态 [decision]: 双 PRIVATE 仓分离：Release 仓为原 pipeline 仓改名，Comparison 仓为新建仓；各自 origin 已切换至自家新地址，legacy-origin 保留旧 URL 只读。
- 分支与保护 [decision]: Release 默认分支 main，保护 main 与 polar-mainline；Comparison 默认分支 main，formal-ir 为受保护工作分支。
- 发布前必检 [decision]: 两仓互不可见为发布前必检项；历史豁免仅放行已审计项。
- 审计链 [repo-observed]: 唯一来源为 `openspec/changes/repo-remote-decoupling` 三件套（proposal/design/tasks）；脏态书面豁免已归档，不在此记录临时盘点数字。
## 2026-09-06 — Simplified single-user research-cycle gate

- Git commit IDs are provenance, not authorization tokens. Do not require
  `HEAD == origin == implementation SHA`, stale-SHA grep, or a commit that
  records its own ID for ordinary local research cycles.
- Pre-EXECUTE checks the intended branch, scoped code/config/test/packet
  cleanliness, frozen scientific contract, focused tests, explicit user
  authorization, and absence of the target output.
- Documentation-only commits after code acceptance do not invalidate accepted
  code. Use exact revision locking only for a concrete multi-writer,
  destructive, release, or evidence-integrity risk named in the packet.
- Keep independent scientific review, no-overwrite outputs, honest partial and
  failure states, and Pre-RESULT review for claim-bearing evidence.
- Review by milestone, not by commit: docs-only and tiny unchanged-scope fixes
  use focused checks and are batched into the next independent scientific
  review. Active packets inherit this simplified Git rule.
## 2026-09-07 V72P2D5 unauthorized G1 output VOID_RETAINED_IN_PLACE (docs-only disposition)

- Disposition [decision]: `workspace/v72p2d5_g1/20260906_r1/` (4 files,
  `decoder_calls=440`, app_exact 0, app_failure 1.0, oracle 0) is
  `VOID_RETAINED_IN_PLACE` — retained unmodified as forensic evidence only,
  barred from citation as a G1 result, performance measurement, or method
  evidence; delete and quarantine-move both rejected (incident I08).
- Blocker [repo-observed]: `MODEL_F_INPUT_PRE_RESULT_REVIEW_R1.md` =
  `PRE_RESULT_REVIEW_FAIL`, sole blocker PR16 (G1 root exists while
  `g1_execution_authorized=false`, `next_gate=P0_PACKET_REVIEW`); Model-F
  artifact content PASS on PR01-PR15 and PR17-PR23.
- Root cause [repo-observed]: incident I09 test-isolation defect; repair
  complete per `TEST_ISOLATION_REWORK_EVIDENCE_R1.md` (SAFE A/B/C + AST static
  guard, 165 collected / 165 passed, focused 10 passed, binder/writer entries 0,
  P0/G2 roots absent).
- Lifecycle [decision]: all `*_execution_authorized` stay false;
  `scientific_promotion=false`; `next_gate=P0_PACKET_REVIEW`; PR16 addressed by
  record only, clearance needs independent Pre-RESULT re-review; a future
  authorized G1 run needs a new output root, no reuse or comparison.

## 2026-09-07 V72P2D5 Model-F input RESULT ACCEPTED (docs-only, no authorization)

- Acceptance [decision]: Model-F CAL-TRAIN input
  `workspace/v72p2d5_model_f_input/20260907_r1/` (2 files, `CAL702..1725`,
  1024x256=262144 symbols, `counts_ab` int64 `(1024,1024)` axis `(Alice,Bob)`,
  `p_b` derived from `axis0`, `lambda_star=137.3823795883264`) accepted as the
  P0/G1/G2 prior input; recorded at cycle level, artifact `status` left
  `MODEL_F_INPUT_CANDIDATE` (protected immutable root, loader accepts both).
- Review chain [repo-observed]: implementation accepted; Pre-EXECUTE R2 PASS
  post-PX11; one authorized prepare + one verify, authorization consumed;
  Pre-RESULT R1 FAIL on PR16; disposition `VOID_RETAINED_IN_PLACE`;
  Pre-RESULT R2 PASS, C01-C11 PASS, `195 passed`.
- Caveat [decision]: PR16 cleared BY RECORD not by condition — the G1 root
  still exists; R2 reinterpreted PR16 by intent. Do not later read this as a
  physical clearance.
- Residual [decision]: `R-R1` prod-side bare-authorized defaults unchanged,
  test-side guard only, future P0/G1/G2 packets must re-verify isolation;
  `R-R2` no global formal-root absence gate, per-test snapshots instead.
- Lifecycle [decision]: nine `*_execution_authorized` false,
  `scientific_promotion` false, `next_gate` `P0_PACKET_REVIEW`; P0/G1/G2 each
  need their own packet review and separate explicit authorization.

## 2026-09-07 V72P2D5 P0 cost preflight ACCEPTED as cost measurement only (docs-only, no authorization)

- Acceptance [decision]: second authorized P0 invocation
  `workspace/v72p2d5_p0_cost/20260906_r1/` accepted as `P0_RESULT_ACCEPTED`,
  scope `COST_MEASUREMENT_ONLY`, recorded in `P0_RESULT_ACCEPTANCE_R1.md`;
  cost acceptance is not scientific promotion and grants no G1 authorization.
- Measured [repo-observed]: phase `p0-cost`, block_length 64, f_list 1.0/1.2,
  frozen_rows 1.0 m1 49/m2 43 and 1.2 m1 59/m2 52, seeds 2026090510/2026090511,
  decoder_calls 12, decode-attributed 8.064733600011096 s vs 1440 s cap (no
  `RESOURCE_OVERRUN`), projected_g1_s 161.8241519993171, projected_g2_s
  485.47245599795133, projection_blocked false, passed true, operator wall
  8.6278899 s exit 0 empty stdout/stderr.
- Not established [decision]: no correctness, no `exact_failure_fraction`, no
  FER, no leakage, no key rate, no net rate, no qualification of NB-LDPC /
  dv3 mother / rate points / Model-F, no statement G1/G2 will pass, no
  authorization for anything.
- Reviews [repo-observed]: Pre-EXECUTE PASS (five questions decided),
  loader-fix PASS (`299416ae`), Pre-RESULT PASS with limitations, guard-rework
  PASS with L1-L4; both P0 authorizations consumed, first
  (`a71188fb`/`3ecaebb6`) produced no run (0.376 s false missing-input refusal
  from consumer path defect), second (`f1cdf970`/`b4696273`) produced result.
- Limitations [decision]: L1/L2/L3/L4/L-RSS/L-SCALE/L-ITER all
  `MUST_CARRY_INTO_G1_PACKET`; `projected_g2_s` grants G2 nothing (no
  width/row-count scaling); RSS null on Windows; all 12 decodes ran to
  `MAX_ITER = 90` cap.
- Lifecycle [decision]: nine `*_execution_authorized` false,
  `scientific_promotion` false, `next_gate` `G1_PACKET_REVIEW`; G1 neither
  frozen nor authorized; next is G1 packet freeze, then independent
  Pre-EXECUTE review, then separate explicit G1 authorization, no
  merge/reorder.

## 2026-09-07 V72P2D5 G1 readiness implementation-only acceptance + Pre-EXECUTE packet frozen (docs-only, no authorization)

- Acceptance [decision]: G1 readiness implementation `cf61ee63`
  (predecessor `614aab9e`, spec/review `d47e7da1`) accepted as
  implementation readiness only (`G1_IMPLEMENTATION_ACCEPTANCE_R1.md`);
  scope excludes any decoder/G1 result, FER, leakage, key rate,
  qualification, or G2 claim; acceptance grants no authorization.
- Review chain [repo-observed]: packet review PASS, readiness code review
  PASS (`G1_READINESS_CODE_REVIEW_PASS`), scope addendum PASS
  (`G1_CODE_REVIEW_SCOPE_ADDENDUM_PASS`, exact frozen three pytest files,
  `219 passed`), live Windows RSS positive without decoder execution.
- Packet [repo-observed]: `G1_PRE_EXECUTE_PACKET_R1.md`
  `G1_PRE_EXECUTE_PACKET_FROZEN / EXECUTE_NOT_AUTHORIZED`; phase `g1`,
  root `workspace/v72p2d5_g1/20260907_r2`, width 64, f 1.0 then 1.2,
  rows L1 49/59 L2 43/52, seeds graph 2026090501/2026090502 + blocks
  2026090600..2026090699, oracle first 20 per f diagnostic-only, GF32 cold
  max_iter 90 damping 1.0, 440 calls, outer wall `<=900 s`, watchdog
  960 s + grace 30 s, RSS peak `<2147483648` / None fails, four
  no-overwrite files, one attempt consuming authorization; exact frozen
  `timeout.exe -k 30 960 ... --phase g1` command; 13 independent checks;
  7 outcomes with `passed` iff `G1_TREND_PASS`; frozen signal; full
  operator return; no result acceptance before Pre-RESULT review.
- Boundaries [decision]: process-vs-entrypoint wall (outer controls 900 s);
  `app_iterations_max<=180` asserted not clamped; exception/timeout/refusal
  operator-side; G1 synthetic trend only, never real FER/qualification.
- Lifecycle [decision]: nine `*_execution_authorized` false,
  `scientific_promotion` false, G1 unauthorized/unexecuted, G2
  unauthorized; `next_gate` `INDEPENDENT_G1_PRE_EXECUTE_REVIEW`; next is
  independent Pre-EXECUTE review (no authorization flip, no G1 run).
## 2026-09-07 V72P2D5 G1 result accepted as synthetic completed-no-signal failure (no pass, bounded attribution only)

- Acceptance [decision]: sole frozen G1 root `workspace/v72p2d5_g1/20260907_r2` accepted (`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_RESULT_ACCEPTANCE_R1.md`) with scope `SYNTHETIC_COMPLETED_NO_SIGNAL_FAIL`, outcome `G1_COMPLETED_NO_SIGNAL_FAIL`, `passed: false`. Chain `cf61ee63 → 6494b623 → f4d577fb → 58c68961`; dual review Pre-EXECUTE PASS + Pre-RESULT `G1_PRE_RESULT_REVIEW_PASS` (internal coherence only).
- Literals [repo-observed]: both f APP exact `0/100` (rate `0.0`, failure `1.0`), APP syndrome-ok `0`, oracle exact/syndrome `0`, `app_iterations_max 180`, APP `18000 = 100×180`, oracle `1800 = 20×90`, `decoder_calls 440 = 400 + 40`, crashes/nonfinite `0`; wall `238.86517630005255 s <= 900` (operator `239.110 s`), RSS `115142656 < 2147483648`. Resource-pass/signal-fail: signal FALSE (top exact `0`), terminal no-signal failure, `passed=false`.
- Boundary [decision]: not trend pass, qualification, G2 readiness, method success, rerun permission, or reinterpretation; exact/syndrome/oracle isolated, stored zeros literal (no FER/undetected/correctness relabel). Single attempt consumed; no second G1, no G2, no real data.
- Lifecycle [decision]: `g1_execution_attempts/completed 1/1`, `g1_result_accepted true` with scope/outcome/passed recorded; `next_gate` `G1_NO_SIGNAL_ATTRIBUTION_IN_PROGRESS`; nine authorizations false, promotion false. Next is bounded failure attribution only (no formal CLI phase, no formal-root write).


## 2026-09-07 V72P2D5 G1 no-signal attribution (disclosure-insufficient, no code change)

- Attribution [decision]: accepted G1 dual-zero attributed to FINITE_LENGTH_DISCLOSURE_INSUFFICIENT (sole primary) in `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_NO_SIGNAL_ATTRIBUTION_R1.md`. Evidence: accepted Model-F actual CE L1/L2 ~= 5.0/5.0 bits (uniform priors, mass-on-truth ~= 1/32) vs frozen sizing 3.81/3.35; need 64/64 (f=1.0) and 77/77 (f=1.2) vs frozen 49/43, 59/52. Paired APP 0/4 + oracle 0/4 saturated; full-H2[:52] 0/4; cap-180 still fails; decoy-prior exact=1 all prefixes; GF32 cross-match exact.
- Rejected [repo-observed]: decoder/field, APP-propagation, iteration-cap, prefix-rank as primary (prefix STRUCTURE_BLOCKED carried secondary; rank full). No implementation defect -> no OpenSpec/code diff; frozen constants/result untouched.
- Lifecycle [decision]: `next_gate` `G1_NO_SIGNAL_ATTRIBUTION_IN_PROGRESS -> G1_ATTRIBUTION_ROUTE_DECISION`; single next probe for main thread (square m=n=64 oracle, approve/reject/redirect). Nine authorizations false, promotion false, G2 absent, no rerun.


## 2026-09-08 V72P2D5 G1 wide attribution R2 (lambda-contract defect + candidate)

- Attribution [decision]: terminal class `LAMBDA_APPLICATION_CONTRACT_DEFECT` supersedes R1 bucket as primary (R1 carried secondary) in `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_WIDE_ATTRIBUTION_R2.md`. Evidence root `workspace/d5_g1_wide_attribution_r2_5c38a20ae60b41ceb0b6a0d7757aa2aa/` (53 dev calls, CAL-only): frozen `lambda*` selected as total per-column concentration but applied per cell (99.82% prior, MI 0.0004 vs 2.48 bits); C0 square-oracle 0/4 vs C1 4/4; C1 L2 at H2[:52] 2/4; C1 L1 fails everywhere incl. square (binding constraint, mass 0.096).
- Implementation [decision]: OpenSpec `v72p2d5-g1-information-recovery-r2` + additive `build_f_model_concentration` / `prepare_model_f_prior_candidate` (frozen path untouched); 8 new tests green; 3-file D5 suite 226 passed + 1 pre-existing stale fail (`test_G1R01...` absence assertion vs accepted root, untouched).
- Lifecycle [decision]: `next_gate` `G1_ATTRIBUTION_ROUTE_DECISION -> INDEPENDENT_G1_INFORMATION_RECOVERY_R2_REVIEW`. Accepted G1/model-F artifacts, authorizations, thresholds, seeds unchanged; no rerun, no G2, no push.

## 2026-09-08 V72P2D5 G1 R2 acceptance (additive backoff-prior candidate, no formal change)

- Acceptance [decision]: R2 review `G1_INFORMATION_RECOVERY_R2_REVIEW_PASS` landed and accepted (`G1_INFORMATION_RECOVERY_R2_ACCEPTANCE_R1.md`) as `G1_INFORMATION_RECOVERY_R2_ACCEPTED`, scope `ADDITIVE_NONFORMAL_BACKOFF_PRIOR_CANDIDATE`, terminal `LAMBDA_APPLICATION_CONTRACT_DEFECT`; `formal_g1_result_changed false`, `production_wiring_changed false`. Chain `88053563→a93106f5→21576add→1d4fa912`; like-for-like `10.0 → 7.51` (MI `0.0004 → 2.48`, tmass `0.031 → 0.254`); three-call square split old 0/4 vs candidate oracle-L2 4/4; C1 L1 `0.096` fails incl. square; C1 L2 only 52–64 rows.
- Lifecycle [decision]: `g1_information_recovery_r2_review PASS_R1`, `candidate_accepted true`, `implementation a93106f5`; `next_gate` `INDEPENDENT_G1_INFORMATION_RECOVERY_R2_REVIEW -> G1_L1_ESTIMATOR_DISCRIMINATOR_IN_PROGRESS`. Accepted Model-F/G1 unchanged, all authorizations false, G2 absent, no rerun, no push.

## 2026-09-08 V72P2D5 G1 L1 discriminator (BP-threshold terminal, route-stop)

- Result [repo-observed]: prereg `f0e4a1c` before scores/calls; CAL-only winner E2 (`kap*≈62.10` unanimous, mean L1 NLL 3.7717 vs 3.8147); E1≡E3 bit-identical (backoff linearity). Paired decoder 75 calls: n64 0/24 incl. square; n128/n256 nonzero-rate 0/4; square-only 1/4, 2/4; mass ~0.10–0.15 vs ~0.28 needed; 0 nonfinite, flags agree, max call 2.41s, peak RSS 182894592 B. Evidence `workspace/d5_g1_l1_discriminator_r1_a9a6bcf3/`; report `G1_L1_ESTIMATOR_DISCRIMINATOR_R1.md`.
- Lifecycle [decision]: terminal `L1_BP_THRESHOLD_NOT_RECOVERABLE_AT_N64`; `next_gate` `-> D5_ROUTE_STOP_REVIEW`. No code (not recoverable), production untouched, four-file suite 259 passed, formal G1 unchanged, authorizations false, G2 absent, no push.

## 2026-09-08 V72P2D5 D5 route-stop acceptance (current-path stop, decomposition successor)

- Acceptance [decision]: `D5_ROUTE_STOP_REVIEW_PASS` accepted (`D5_ROUTE_STOP_ACCEPTANCE_R1.md`); terminal `D5_CURRENT_TWO_LAYER_RATE_MOTHER_BP_PATH_STOPPED`; reason `ACCEPTED_G1_NO_SIGNAL_PLUS_CAL_ONLY_L1_DISCRIMINATOR_NO_USEFUL_RECOVERY`; scope exactly the current fixed high-five/low-five two-layer rate-mother/BP path.
- Lifecycle [decision]: GF32/NB-LDPC open; formal G1 accepted completed-no-signal unchanged; G2 unauthorized/absent; successor is the reversible 5+5 decomposition discriminator. `next_gate` `D5_ROUTE_STOP_REVIEW -> D5_DECOMPOSITION_SUCCESSOR_PREREG`. No push.

## 2026-09-08 V72P2D5 decomposition successor R1 (no N64 recovery, graph/mother route next)

- Result [repo-observed]: prereg `e4d3af7` before scores/calls; 252 CAL-only (chain ≤8.88e-16, joint invariant 7.162347, control CE_L1 3.814742 = c1 E1); rank-1 IS current mapping `(5,6,7,8,9)` m=(59,52). 192/600 calls: APP 0/8 everywhere; oracle-L2 6/8+8/8 rank-1 only (diagnostic); 0 crash/nonfinite/disagreement; four-file suite 259 passed. Evidence `workspace/d5_decomposition_successor_r1_c765e3010674/`.
- Lifecycle [decision]: terminal `DECOMPOSITION_NO_N64_RECOVERY`; no code/OpenSpec (§4.6 not-strong). `next_gate` `-> D5_GRAPH_MOTHER_SUCCESSOR_PROPOSAL` (main-thread proposal, not authorized). Formal roots unchanged, authorizations false, no push.
## 2026-09-09 V72P2D6 R1c-A3 post-run verifier rework (blocked run)

- Result [repo-observed]: A3 repaired the A2 verifier by OpenSpec amendment (key +`n`, stage-separated recompute, crash precedence, EMPTY confirmation, stored+recomputed fail-closed report); corrected `--verify` once on the immutable root: exit 0, 15/15 PASS, `stored D6_GRAPH_TOPOLOGY_NO_USEFUL_RECOVERY` vs `recomputed D6_GRAPH_STRUCTURE_INVARIANT_BLOCKED degree-invariant:64`, agreement False. 184 rows reconcile; 64 attempted degree crashes from degree-1 check rows in frozen T3/M1 graphs. Focused 42/42; seven-file non-perf 323/323.
- Lifecycle [decision]: Pre-RESULT `PASS_BLOCKED_RUN` (blocked attempt, never topology evidence); `next_gate` `-> D6_GRAPH_MOTHER_R1C_A3_BLOCKED_AWAITING_MAIN_THREAD_ROUTE`. Zero decoder calls in A3; authorizations false; G2 absent; no push.
## 2026-09-09 V72P2D6 R1c-A4 structure performance (READY)

- Result [repo-observed]: scaling structure 10897.7 s -> 2.5 s (≈4280x, T2 pruning + two-build replay + overflow passthrough; T2 semantics untouched); n64 outputs exactly equal (21.0 s vs 42.2 s); RSS ≈ 90 MB; zero decoder calls. Equivalence vs committed A2 evidence exact. Focused 51/51; seven-file non-perf 332/332.
- Lifecycle [decision]: performance review `PASS` -> `READY_FOR_FUTURE_D6_PRE_EXECUTE_REVIEW` (structure path only). No execution authorized; authorizations false; G2 absent; no push.
## 2026-09-10 V72P2D6 R1c-A5 validity closure + repair infeasibility + R1d readiness (eligible-only)

- Result [repo-observed]: independent 144-cell matrix (8 arms x widths x layers x prefixes) proves the frozen gate never checked check-node degree: T3/T4/M1 carry degree-1 rows at f1.2+square everywhere (10-81 cells), M1 exactly at the zone-counting bound (zone-1 rows below, all 6 cells); T2 rank-deficient at every square (63/62, 123/122, 246/240); B0/B1 bounds (n128-L2 dup, n256 f1.0 disconnection) recorded unmodified. Frozen eligible + A2 selection {B0,B1,T1,T3,M1} reproduced exactly (132/132 cross-check, 51/51 recompute, committed JSON match). I1 gate landed (eligible-AND, dispatch guard, verify INFO/PASS-FAIL); crash-precedence terminal landed. Repair study: 0/10 sandbox rules admissible (R-T3-03/R-T4-03/R-M1-01 are byte-identical non-repairs; rest fail R3) -> `STRUCTURALLY_INFEASIBLE_AS_FROZEN` + 3-option `REQUIRES_MAIN_THREAD_RULING` menu, nothing landed. Production builders byte-identical. Historical root verify exit 0, 15/15, agreement False, mtimes intact. Focused 56/56; seven-file 90/90 (membership reconstructed and named).
- Lifecycle [decision]: reviews `PASS_ELIGIBLE_ONLY_BRANCH` x2 (validity); R1d package `NOT_AUTHORIZED`; `next_gate` -> `D6_GRAPH_MOTHER_R1C_A5_TRACK_A_COMPLETE_TRACK_B_PENDING`. Zero decoder calls; authorizations false; G2 absent; no push.
## 2026-09-10 V72P2D6 R1c-A6 exact-equivalent T2 acceleration (PASS, 20-35x)

- Result [repo-observed]: staged/vectorized/integer-encoded T2 (`_build_T2_support_fast`, reference intact, no float, no key/order change) proven exactly equal (n64 live-ref, n128/n256 replay-verified fixtures, committed n64 rows, traces, seq==par, A4 guards green). Task walls: n64 1.2 s (<=5), n128 26.6 s (<=90), n256 516.1/479.7 s (<=600); factors 34.5x/24.7x/19.9x; n64 all-8 1.5 s (<=8); fb-only 0.6/1.3 s vs A4 2.5/2.7 s; RSS ~93 MB; zero decoder calls. Slow-task inventory measured (v38 T0 2.0 s, T1 812/810 s, orchestration 345/344 s, lane-A ~40 s, helpers <=46 ms; V30R 74.8/719.9 s cited, not re-runnable). Focused 61/61 + slow n256 cell; seven-file 95/95.
- Lifecycle [decision]: performance review `D6_R1C_A6_REVIEW_PASS` (no NOT_MET). `next_gate` -> `D6_GRAPH_MOTHER_R1C_A5A6_COMPLETE_AWAITING_MAIN_THREAD_RULING`. No execution authorized; authorizations false; G2 absent; no push.
## 2026-09-10 V72P2D6 R1d Option C freeze (eligible-only {B0,B1,T1}, Pre-EXECUTE pending)

- Ruling [repo-observed]: main-thread Option C — no SC/M knob lift; SC/accumulator inadmissible as frozen; R1d exactly {B0_D5_DV3_NATIVE, B1_D5_DV3_COMMON_LABELS, T1_PEG_DV3} (B0/B1 controls, T1 sole new arm, T1-only scaling fallback); T2 rank-bound record only; no A2 call/root reuse; schema `r1d-v2` (`row_degree_min`, `rows_below_degree_2`, version marker) for new roots, A2 immutable old-schema.
- Freeze [repo-observed]: OpenSpec `v72p2d6-gf32-graph-mother-r1d-option-c` + `D6_GRAPH_MOTHER_OPTION_C_ACCEPTANCE_R1.md` (A/B rejection + 22/22-cell validity proof, 0 conflicts) + `D6_GRAPH_MOTHER_R1D_EXECUTION_PACKET_R1.md` (exact `--r1d` command, 552-call worst case, budgets/stop-rules, no-reuse, claim ceiling).
- Lifecycle [decision]: `next_gate` -> `D6_GRAPH_MOTHER_R1D_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`. R1d NOT authorized, NOT executed; no R1d root. Authorizations false; G2 absent; no push.
## 2026-09-10 V72P2D6 R1d Option C implementation + Pre-EXECUTE (PASS, awaiting explicit authorization)

- Result [repo-observed]: eligible-only layer landed additive-only (mother +121 pure-append; dev `--r1d` default-off, A4 callsite pins green); 13 R1d tests cover all 12 packet properties; focused D6 + seven-file non-perf 356/356 green (fresh `workspace/d6_r1d_tests_*` basetemp; perf-v38 skipped, out-of-scope deps). Independent subset re-derivation 22 == 22, live spot-check pass. Reviews `D6_R1D_IMPLEMENTATION_REVIEW_PASS` (0 rework) then `D6_R1D_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION` (grants nothing). Zero decoder calls; no R1d root; A2 immutable git-clean old-schema; no A2/VOID/formal reuse.
- Lifecycle [decision]: R1d NOT authorized, NOT executed; `next_gate` unchanged (`D6_GRAPH_MOTHER_R1D_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`). Separate explicit grant + mandatory Pre-RESULT review required. Authorizations false; G2 absent; no push.

## 2026-09-10 D7-A GF32 decoder certification PASS (tiny-synthetic only, no production change)

- Verdict [decision]: D7_A_DECODER_CERTIFICATION_PASS — historical decode_row_layered_fftqspa matches independent poly-37 oracle within tol 1e-10 (check-update <=3.3e-16, tree posterior <=6.7e-16, loopy per-sweep <=7.2e-13); final_beliefs is log-domain so _softmax_rows in _run_layered_block is correct (no double-exp); zero production diff, no trace hook.
- Next [decision]: D7_B_EASY_REGIME_PACKET_FREEZE readiness only; D7-B/C/D execution, R1d, G1, G2 unauthorized. R1d stays R1D_PAUSED_PENDING_DECODER_CERTIFICATION.
- Scope note [repo-observed]: D7-A oracle comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_decoder_certification.py + comparison_bench/tests/test_v72p2d7_gf32_decoder_certification.py (14/14); pre-existing unrelated failure test_qldpc_reference_source_is_not_mutated from CRLF churn, untouched.
## 2026-09-10 D7-B easy-regime freeze + harness + Pre-EXECUTE PASS (no execution)

- Freeze [decision]: R1+A1 64-cell matrix (caps [1,2,4,8,16,32,90], 420-call stop, 120/1500/1800+30s, <2GiB); TREE_6 active literal rows [3,3,2] c0=[0,1,2]/[1,7,13] c1=[2,3,4]/[29,1,7] c2=[4,5]/[13,29] (V=9, E=8, rank 3, nine proofs pass); superseded [2,3,2]/7-edge rejected by test (7<8), never dispatched; dual tree-exact (never 32^6/production).
- Evidence [repo-observed]: harness + 19 tests + runner; D7-A oracle reused, v35/D5 untouched; tiers 19/19 D7-B, 14/14 D7-A, 25/25 v35, field 13/14 (known CRLF pin failure); RSS 85139456; timeout rehearsal 124; out-of-repo sentinel probe zero scientific calls; unauthorized refuses, no root; reviews IMPLEMENTATION_PASS then PRE_EXECUTE_PASS_AWAITING_EXPLICIT_AUTHORIZATION (0 rework).
- Lifecycle [decision]: D7-B NOT authorized/NOT executed; `next_gate` -> `D7_B_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`. R1d paused; G1/G2 absent; no push.
## 2026-09-10 D7-B WSL launch binding rework + renewed Pre-EXECUTE PASS (no execution)

- Disposition [decision]: spent R1 UUID `0f1ad3ec-...` (exit-3 relative-import ImportError) retained as `D7_B_PRE_EXECUTION_LAUNCH_BINDING_BLOCKED` (launch defect; no terminal/count/result); return + BLOCKED pre-result review + disposition committed (T0 `13c1c3c`); authorization lifecycle `ce52ac5`→invoke→`9e41e0d` preserved exactly, never reused.
- Repair [repo-observed]: runner-local src setup only (`scripts/v72p2d7_gf32_easy_regime.py` +4: `<repo>/comparison_bench/src` from resolved `__file__`, insert-if-absent; T2 `04b7a8e`); core/v35/D5/D7-A/field byte-unchanged; core fallbacks stay `except ModuleNotFoundError`-only. Reusable failure pattern in `docs/troubleshooting.md`: never file-load a relative-import module as top-level; keep absent-package fallbacks narrow.
- Evidence [repo-observed]: L01–L12 zero-decoder green (miniature original-failure capture; help/dry-run both cwds, 64 cells; src-only insertion; exact package-loaded v35 bind never called; fake-shadow refusal; unauthorized exit 3 pre-bind; frozen contract; roots/auth unchanged); full D7-B 31/31, D7-A 14/14, v35 milestone 25/25. WSL canonical (venv python 3.12.3, NumPy 2.4.4, kernel 6.18.33.2-WSL2, GNU timeout 9.4); WSL-A1 addendum freezes shell-spelling-only command; no new UUID. Reviews `D7_B_WSL_LAUNCH_REWORK_REVIEW_PASS` (0 repair) then `D7_B_PRE_EXECUTE_REVIEW_PASS_WSL_R2_AWAITING_FRESH_AUTHORIZATION` (grants nothing). Local pytest absent in WSL venv (installs forbidden) so suites ran via an uncommitted /tmp shim; committed L10 shells plain `python -m pytest`.
- Lifecycle [decision]: documented gate `D7_B_WSL_READY_AWAITING_FRESH_EXPLICIT_AUTHORIZATION` (docs only; `cycle_state.yaml` untouched: auth false, attempts/completed 0/0, decoder/result false). Future run needs fresh explicit user authorization with one new UUID. R1d paused; G1/G2 unauthorized; no push.
- Lifecycle [decision]: D7-B WSL R2 (`c605d1e6-...`) accepted with stored terminal `D7_B_RESOURCE_OVERRUN` retained; scope exactly `HARD_DECISION_EASY_REGION_OBSERVED_WITH_RESOURCE_AND_SOFT_BELIEF_LIMITATIONS` (64/64 exact+syndrome at cap 1; 49 iter-0 + 15 iter-1; posterior tol failed, MAP agreed; RSS null = telemetry unknown, no measured breach, no <2GiB PASS). `d7b_r2_accepted true`; `next_gate` → `D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT`. All authorizations false; R1d/G1/G2 absent; no push.
- Evidence [repo-observed]: acceptance `D7_B_RESULT_ACCEPTANCE_R2.md` (§3 twelve points); review `D7_B_PRE_RESULT_REVIEW_PASS_R2`; R2 root five files (111/44743/1008/80/449) byte-identical across two reads, untouched; zero decoder calls, zero production edits.
- Lifecycle [decision]: D7-B early-exit soft-belief audit classified `D7_B_MIXED_METRIC_AND_INTERFACE_DEFECT` + `D7_B_RSS_TELEMETRY_DEPENDENCY_GAP`; review `D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT_REVIEW_PASS` (E06 transcription: 25 it0 + 4 TREE PAIR it1 at 0.00689, total 29 unchanged); `next_gate` → `D7_B_LAYER_INTERFACE_CORRECTION_PROPOSAL`. All authorizations false; R1d/D7-C/D/G1/G2 absent; no push.
- Evidence [repo-observed]: audit `D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT_R1.md` (E01–E12, 49/15, zero decoder); review `D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT_REVIEW_R1.md`; R2 root five files unchanged; terminal `D7_B_RESOURCE_OVERRUN` retained.

## 2026-09-11 D7-B layer-interface proposal PASS + D7-C bidirectional-oracle freeze/implementation/reviews (no execution)

- Proposal [decision]: Phase P froze OpenSpec `v72p2d7-layer-interface-belief-provenance` + `D7_B_LAYER_INTERFACE_CORRECTION_PROPOSAL_R1.md` (`86f6baf6`); independent review issued the sole allowed PASS `D7_B_LAYER_INTERFACE_CORRECTION_PROPOSAL_PASS_D7_C_NONBLOCKING`. Preferred alternative A exposes `belief_provenance` enum `PRIOR_ONLY`/`CHECK_UPDATED`/`WARM_START_UNSPECIFIED`; cross-layer APP consumers fail closed unless `CHECK_UPDATED`. Interface implementation mandatory before any sequential/alternating/joint cross-layer APP route, not before D7-C; no historical result reinterpreted; no v35 stopping change. D7-B documented next route `D7_C_BIDIRECTIONAL_ORACLE_PACKET_FREEZE_INTERFACE_REWORK_DEFERRED`.
- Inventory [repo-observed]: 22 production/interface `final_beliefs` entries + V64 runner extension (`scripts/execute_v64_fresh_verify.py:188`); sibling `nonbinary_v10_fftqspa.py` excluded (different probability-domain contract, no `final_beliefs` field). Defect chain E02/E03/E08/E09: cold row-layered iteration-0 return is the untouched log-prior; D5 `_run_layered_block` forwards `softmax -> app_fed_l2_prior` unconditionally with no `iterations == 0` guard.
- Freeze [decision]: D7-C R1+A1 frozen (commits `0c304875` OpenSpec/prereg/execution packet; `391fc6b0` module/tests/runner; `ca00b234` implementation review; Pre-EXECUTE review committed separately, SHA not recorded here). n=64; seeds `2026091300..2026091315`; f `[1.0,1.2]`; L1 rows 49/59, L2 rows 43/52; D5-native mothers `build_dv3_nested_support(64,64,49,2026090501)`/`(64,64,43,2026090502)` + `assign_gf32_coefficients`; 128 calls in fixed order; budgets 120 s/1500 s/1800 s+30 s/<2 GiB; six-file scalar output; four single-layer priors direct from `J`; iteration-0/current belief labeled only `PRIOR_ONLY_CURRENT_BELIEF`; no cross-layer belief flow.
- Estimator [decision]: H03 accepted estimator uniquely `d5.prepare_model_f_prior_candidate` / `build_f_model_concentration`, `LAMBDA_STAR=137.3823795883264` (per-Bob-column total concentration); rejected `prepare_model_f_prior`/`build_f_model` (per-cell pseudocount, `LAMBDA_APPLICATION_CONTRACT_DEFECT`).
- Reviews [repo-observed]: `D7_C_IMPLEMENTATION_REVIEW_PASS` (0 rework, C01–C20, 20/20 tests) then `D7_C_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION` (128-matrix, external-cwd sentinels, stdlib RSS KiB→bytes, unauthorized refusal before decoder/Model-F/root, protected metadata identical). Reusable env notes: combined multi-file pytest hits a pre-existing `comparison_bench` namespace collision -> run suites per-process; bare `python` absent from default WSL PATH -> the future authorized run must declare the same venv-on-PATH adapter used for D7-B R2; per-call watchdog is post-hoc measurement + outer GNU timeout; six-file verifier checks only internal consistency of the six files.
- Lifecycle [decision]: D7-C NOT authorized, NOT executed. All authorization false; no UUID; no `workspace/d7_c_bidirectional_oracle_*` root; D7-B R2 root `c605d1e6-8577-4c52-a865-12500fc8c964` immutable; R1d paused; G1/G2 unauthorized. `next_gate` `D7_C_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`; parallel state `LAYER_INTERFACE_IMPLEMENTATION_DEFERRED_BEFORE_CROSS_LAYER_APP`. Mandatory Pre-RESULT review before any result; no push.

## 2026-09-11 D7-C bounded bidirectional-dependence diagnostic accepted (route to D7-D schedule discriminator)

- Acceptance [decision]: `D7_C_RESULT_ACCEPTED_BIDIRECTIONAL_DEPENDENCE_DIAGNOSTIC` per §0 of `D7_C_ACCEPT_D7_D_SCHEDULE_FREEZE_IMPLEMENT_PRE_EXECUTE_R1_TASK_PACKET.md`, recorded in `D7_C_RESULT_ACCEPTANCE_R1.md`. Accepted scope: 128/128 frozen single-layer calls completed, finite, internally coherent; exact and syndrome agreed 128/128, 43 exact; f=1.0 L1 `0/16 -> 10/16`, L2 `0/16 -> 1/16`; f=1.2 L1 `3/16 -> 16/16`, L2 `0/16 -> 13/16`; f=1.2 `STRONG_ORACLE_LIFT` in both layers; terminal `D7_C_BIDIRECTIONAL_DEPENDENCE` accepted as a bounded mechanism-classification result; no crash/nonfinite/resource/watchdog issue; RSS known < 2 GiB; D7-C consumed no cross-layer returned beliefs and is unaffected by the deferred D7-B APP-interface implementation.
- Paired counts [repo-observed]: per-stratum (oracle_only/marginal_only/both/neither) f=1.0 L1 `10/0/0/6`, f=1.0 L2 `1/0/0/15`, f=1.2 L1 `13/0/3/0`, f=1.2 L2 `13/0/0/3`; each sums to 16, no `marginal_only` pair anywhere.
- Evidence [repo-observed]: immutable root `workspace/d7_c_bidirectional_oracle_94c0ea15-a786-4cb8-a991-6fec521cccae` (six files 282/23599/2709/1130/362/728 B, zero subdirs); lifecycle authorize `b07b5441` → one invocation → revoke `d3bd3c8b` → result `b4ba2896`; independent Pre-RESULT `D7_C_PRE_RESULT_REVIEW_PASS_R1`; verifier `VERIFY_OK {'ok': True, 'problems': [], 'records': 128, 'terminal': 'D7_C_BIDIRECTIONAL_DEPENDENCE'}`; outer wall 33.743 s, stored wall 32.631 s, max call 0.439 s, RSS 105172992 B, exit 0.
- Ceiling [decision]: accepted that true other-layer symbols materially improve recovery under the frozen priors/matrices/decoder/disclosures/n=64/16 paired blocks; NOT accepted that an implementable alternating/joint decoder can generate that information, bootstrap from marginal priors, achieve FER, improve leakage/key rate, qualify the code, or generalize beyond this matrix; f=1.0 L2 remains effectively unrecovered even at oracle 1/16; no FER/leakage/key-rate/CAL/qualification/promotion claim.
- Route [decision]: `next_gate` → `D7_D_SCHEDULE_DISCRIMINATOR_PACKET_FREEZE` (D7-D isolates schedule only; do not implement alternating/joint BP). All authorizations stay false; D7-C/D7-B roots immutable; R1d/G1/G2 unauthorized; interface implementation remains deferred before cross-layer APP; no push.

## 2026-09-11 D7-D GF32 schedule discriminator freeze + implementation + dual review PASS (readiness only, no execution)

- Freeze [decision]: OpenSpec `v72p2d7-gf32-schedule-discriminator` + prereg/execution packet committed `3a05899`; discriminator module `v72p2d7_gf32_schedule_discriminator.py` (1395 lines) + tests (1535) + runner `scripts/v72p2d7_gf32_schedule_discriminator.py` (104) + flooding certification doc committed `43f07186`. Frozen matrix: 128 D7-C identities (16 seeds × f{1.0,1.2} × 4 conditions) × schedules `[ROW_LAYERED, FLOODING]` = 256 calls, `call_idx` `2k-1`/`2k`; identical non-schedule inputs within each pair; D7-C constant aliases (`LAMBDA_STAR` etc.); work-normalized check-node/edge updates; five first-match strata + exact ten-entry terminal priority; budgets per-call 120 s / stored wall 1500 s / outer GNU timeout 1800 s + 30 s kill grace / RSS <2 GiB via stdlib `resource`; seven-file scalar future root; frozen future command (no UUID).
- Certification/reviews [repo-observed]: F01–F08 flooding certification all PASS (tiny ≤4-var synthetic, D7-A oracle, tol `1e-10`, no patch); S01–S22 all PASS (30-test suite, 30 passed); `D7_D_IMPLEMENTATION_REVIEW_PASS` (`727bca7a`); `D7_D_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION` (doc written, uncommitted at closeout). Regression scope: D7-A 14 / D5 165 / v35 25 green; D7-B scoped 29 green; D7-C raw 19 passed with stale pre-execution `test_c19` invariant (accepted D7-C root now exists) — non-blocking, S20 deselection scoped, refresh as a separate scoped change.
- Lifecycle [decision]: readiness only — D7-D NOT authorized, NOT executed; pre-closeout `next_gate` `D7_D_IMPLEMENTATION_PENDING`; all authorization flags false (`decoder_executed`/`result_created`/`scientific_promotion` false); no UUID, no `workspace/d7_d_schedule_discriminator_*` root; D7-C root `94c0ea15-...` and D7-B R2 root immutable; `layer_interface_implementation` remains `DEFERRED_MANDATORY_BEFORE_CROSS_LAYER_APP`; R1d/G1/G2 unauthorized; no push. Environmental carry-forward: the future authorized execution must declare the venv-on-PATH adapter (Python 3.12.3 / NumPy 2.4.4 / GNU timeout 9.4) as recorded for D7-C.

## 2026-09-11 D7-D bounded result acceptance (schedule effect inconclusive; route to BP provenance Alternative A)

- Acceptance [decision]: `D7_D_RESULT_ACCEPTED_SCHEDULE_EFFECT_INCONCLUSIVE` per §0 of `D7_D_ACCEPT_BP_INTERFACE_READINESS_R1_TASK_PACKET.md`, recorded in `D7_D_RESULT_ACCEPTANCE_R1.md` after Phase-A A01 independent recomputation (0 discrepancies, root read twice identical). Accepted facts for UUID `64660d16-397d-4ef3-8454-3066d27c12c7`: 256/256 paired calls completed; row-layered exact `43/128`, flooding exact `40/128`, layered-only `3`, flooding-only `0`, both `40`, neither `85` (syndrome-only `3/0/40/85`); no crash/nonfinite/watchdog; stored terminal `D7_D_SCHEDULE_EFFECT_INCONCLUSIVE`; Pre-RESULT `D7_D_PRE_RESULT_REVIEW_PASS_R1`; budgets 120/1500/1800+30 s and RSS `<2 GiB` passed.
- Ceiling [decision]: no preregistered flooding or layered advantage; `43 vs 40` and the three layered-only identities (26 `1.0/2026091306/L1_ORACLE_U2`, 46 `1.0/2026091311/L1_ORACLE_U2`, 101 `1.2/2026091309/L1_MARGINAL`) are reported, not promoted to schedule superiority; schedule choice is not the dominant failure explanation; D7-C oracle dependence remains stronger route evidence but does not prove alternating/joint BP bootstrap; no FER/leakage/key-rate/qualification/promotion/general-equivalence/general NB-LDPC claim.
- Evidence [repo-observed]: immutable root `workspace/d7_d_schedule_discriminator_64660d16-397d-4ef3-8454-3066d27c12c7` (seven files 3164/57659/17690/1777/1546/455/290 B, zero subdirs); lifecycle authorize `7a3f0d92` → one invocation → revoke `eba385bb` → result `63a69f57`; verifier `VERIFY_OK {'ok': True, 'problems': [], 'records': 256, 'terminal': 'D7_D_SCHEDULE_EFFECT_INCONCLUSIVE'}`; eight labels `EXACT_TIE_LOW, MIXED_SCHEDULE_EFFECT, EXACT_TIE_LOW, EXACT_TIE_LOW, EXACT_TIE_LOW, EXACT_TIE_HIGH, EXACT_TIE_LOW, EXACT_TIE_HIGH`; outer wall 67.178 s, stored wall 65.945 s, max call 0.436 s, RSS 105304064 B.
- Route [decision]: `D7_D_SCHEDULE_EFFECT_INCONCLUSIVE` has no frozen automatic successor; this ruling selects Alternative A (explicit belief provenance plus fail-closed cross-layer consumers) as the next mainline action; `next_gate` → `BP_INTERFACE_PROVENANCE_IMPLEMENTATION`. R1d stays `PAUSED_OPTIONAL_LOCAL_CONFIRMATION_NOT_MAINLINE_GATE` (not a mainline gate); G1/G2 unauthorized; old D5/D6 checkboxes are historical accounting. Dimension/bw expansion waits for a working provenance-safe fixed-dimension mechanism and, for more than two layers, a separate mathematical/leakage contract. No forced sweep, warm-start, alternating/joint decoder or scientific run; no D7-E work; all authorizations false; no push.

## 42. NB-Polar independent-track initialization (2026-09-11)

- Ownership [decision]: native NB-Polar planning and implementation belong to
  the separate checkout D:/Code/HD-QKD_Polar_Comparison-nbpolar; this
  Comparison checkout owns the NB-LDPC history, accepted evidence, and
  cross-project decision boundary. The Cascade worktree and Release checkout
  are reference/boundary projects, not NB-Polar implementation locations.
- Algorithm contract [decision]: the MVP candidate is GF32 over the polynomial
  basis with primitive polynomial 37 and kernel
  F_alpha=[[1,0],[alpha,1]], x0=u0+alpha*u1, x1=u1, natural index order,
  normalized float64 log-probability metrics, source-polarization SC, and
  static full-symbol disclosure before one final 64-bit universal tag.
- Asset boundary [repo-observed]: reuse GF2mField, Model-F counts and
  concentration semantics, explicit layer priors, shared IR accounting, and
  Release Polar protocol patterns only through adapters. Do not reuse
  NB-LDPC graph topology, implicit prior-only APP flow, binary PW ordering,
  tag-selected paths, or direct GF1024 arithmetic in the MVP.
- Lifecycle [decision]: the former hybrid
  formal-ir-future-nbpolar-app-transfer draft was never implemented or
  executed and is archived under
  openspec/changes/archive/2026-09-11-formal-ir-future-nbpolar-app-transfer-superseded/.
  The new formal-ir-nbpolar-mvp OpenSpec is a plan candidate only; all
  implementation, real-data execution, qualification, promotion, and push
  authorizations remain false.
- Evidence ceiling [decision]: D5/D6/D7 results provide failure attribution
  and interface lessons, not NB-Polar performance evidence. D7-E remains the
  active formal-IR gate independently of this successor plan. See
  docs/NBPOLAR_TRACK.md and the canonical sibling docs for phase gates.

## 2026-09-11 BP interface provenance Alternative A complete + reviews PASS (route to D7-E packet freeze)

- Completion [decision]: BP-01…BP-05, BP-07, BP-08 complete; BP-06 complete only as a frozen non-implementation boundary (`WARM_START_DEFERRED`, no warm-start implementation). OpenSpec delta `5483dd8`; implementation `654fa299`. `layer_interface_implementation` = `IMPLEMENTED_ALTERNATIVE_A_FAIL_CLOSED`; `bp_implementation_review` = `D7_BP_INTERFACE_IMPLEMENTATION_REVIEW_PASS`; `bp_readiness_review` = `D7_BP_INTERFACE_READINESS_REVIEW_PASS`.
- Contract [repo-observed]: Alternative A only (B/C absent); v35 producer exposes additive defaulted `belief_provenance`; D5 `_decode_block` + active cross-layer consumers carry/guard it; conditioned cross-layer APP fails closed unless provenance is exactly `CHECK_UPDATED`; no hard-decision/numerical/stopping drift; no historical result recomputed; no real artifact/decoder run in this packet.
- Route [decision]: `next_gate` → `D7_E_PROVENANCE_SAFE_CROSS_LAYER_DISCRIMINATOR_PACKET_FREEZE`; `d7e_state` = `NOT_FROZEN_NOT_AUTHORIZED`; any next scientific work needs a new prereg/packet and explicit authorization. R1d optional/paused; G1/G2 unauthorized; no scientific execution; all authorizations false; no push.
- Notes [repo-observed]: external-push observation to `nbpolar-origin/codex/nbpolar-phase0` noted as not performed by the WSL operator. D6 latent arity: BP-02 changed the D5 `_decode_block` return arity and the dormant `scripts/v72p2d6_graph_mother_development.py` still unpacks the old shape; fixing/migrating it (plus the fail-closed guard) is required under a new scoped change before any D6 rerun (see `docs/troubleshooting.md`). V35 external rewrite reappeared after the A06 restore (~10:28:58 and ~11:16:45) and was re-restored to HEAD without commit; writer unresolved.

## 2026-09-11 R21 readiness-facts closeout (D6 R1d BP-compat + D7-E frozen; no execution)

- Track A [repo-observed]: D6 R1d five-vs-six `_decode_block` arity repaired zero-decoder (`9563c36f` freeze, `6fc3d893` six-value unpack + fail-closed provenance, `da359ec5` reviews); reviews `D6_R1D_BP_COMPAT_IMPLEMENTATION_REVIEW_PASS` + `D6_R1D_PRE_EXECUTE_REVIEW_PASS_BP_COMPAT_A1_AWAITING_EXPLICIT_AUTHORIZATION`; prior R1d Pre-EXECUTE stale/superseded; R1d `PAUSED_OPTIONAL_LOCAL_CONFIRMATION_NOT_MAINLINE_GATE`, no R1d execution authorized.
- Track B [repo-observed]: D7-E frozen at `f82804f6` (OpenSpec `v72p2d7-provenance-safe-cross-layer-discriminator`, prereg + execution packet, 192 slots = 128 mandatory + ≤64 transfer, row-layered-only, CHECK_UPDATED-only transfer, estimator hard contract); 25 focused tests green; reviews `D7_E_IMPLEMENTATION_REVIEW_PASS` + `D7_E_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`; frozen awaiting explicit authorization, pending closeout; no UUID, no roots, no execution.
- Debt [repo-observed]: isolated baseline tripwires, repair only via snapshot invariance, no skip/xfail/delete — D7-B `test_launch_l04_dry_run_both_cwds_no_bind_no_root` + `test_launch_l12_roots_and_authorization_unchanged`; D7-D `test_f08_no_real_model_f_production_root_or_formal_root_read` + `test_s21_protected_root_lifecycle_and_d7bc_immutability`; D7-C `test_c19_protected_root_lifecycle_and_g2_r1d_absence` (root part converted, residual stale state assertion).
- Posture [decision]: all authorizations false; G1/G2 unauthorized; committed corrected `docs/v35-algorithm-development-report.md` authoritative over worktree external rewrite; D7-E/R1d execution never authorized.

## 2026-09-11 D7-E WSL RSS telemetry rework A2 (telemetry-only; no execution)

- Failure mode [repo-observed]: WSL `resource.getrusage().ru_maxrss` intermittently disagrees with `/proc/self/status` VmHWM by GiBs, making the one-shot E09 execution gate non-deterministic; frozen A2 rule reads peak RSS only from `/proc/self/status` field `VmHWM` (unit exactly `kB`, `bytes=value*1024`), fail-closed `None`, strict `<2GiB`; `ru_maxrss` never on the WSL path (no `ru_maxrss` reference remains in `v72p2d7_gf32_cross_layer_discriminator.py`).
- Milestone [repo-observed]: OpenSpec delta + addendum `D7_E_EXECUTION_PACKET_ADDENDUM_RSS_A2.md` (`becf60f2`), implementation `fix(d7-e)...` (`9e095382`, 15 new `test_a2_*`); reviews `D7_E_RSS_TELEMETRY_REWORK_REVIEW_PASS_A2` + `D7_E_PRE_EXECUTE_REVIEW_PASS_VENV_RSS_A2_AWAITING_FRESH_EXPLICIT_AUTHORIZATION` (single live E09: `VmHWM 96484 kB` → `98803712 B`); no execution, no UUID/root, attempts/completed zero, all auth false.
- Lifecycle [decision]: `cycle_state.yaml` still `D7_E_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION` (A2 closeout label `D7_E_WSL_RSS_READY_AWAITING_FRESH_EXPLICIT_AUTHORIZATION` not yet applied); prior user authorization not reusable — a later execution needs a fresh explicit authorization referencing RSS A2. R1d paused/optional; G1/G2 unauthorized; no push.

## 2026-09-11 D7-E accepted as directional cross-layer transfer diagnostic; route to D7-F reverse-order freeze

- Accepted facts [repo-observed]: immutable D7-E root `faa5dc1c-...` (auth `b148c9d4` → revoke `34085c15`, solidification `40977a2c`); 192/192 calls, 64/64 transfer eligible+invoked; f=1.0 both directions 0/16–0/16; f=1.2 L1_TO_L2 0/16–3/16 AMBIGUOUS; f=1.2 L2_TO_L1 3/16–7/16 STRONG (transfer-only 4, control-only 0); terminal `D7_E_L2_TO_L1_TRANSFER_LIFT`; integrity `PASS_WITH_DISCLOSED_VERIFY_PROVENANCE_GAP` (original BLOCKED retained); acceptance doc `D7_E_RESULT_ACCEPTANCE_R1.md`.
- Scope [decision]: `D7_E_RESULT_ACCEPTED_DIRECTIONAL_CROSS_LAYER_TRANSFER_DIAGNOSTIC` — direction-dependent useful transfer strongest L2_TO_L1 at f=1.2 for this frozen contract only; no general/FER/leakage/key/qualification/real-data/alternating-convergence/R1d/G1/G2 claim.
- Route [decision]: `next_gate` → `D7_F_REVERSE_ORDER_PACKET_FREEZE`; D7-F reverse-order complete-two-layer test, no feedback yet, cavity/extrinsic still missing. All authorizations false; no push.
## 2026-09-11 D7-E accept + D7-F reverse-order readiness R1 (frozen/implemented/dual-PASS; no execution)

- D7-E accept [repo-observed]: `D7_E_RESULT_ACCEPTED_DIRECTIONAL_CROSS_LAYER_TRANSFER_DIAGNOSTIC` in `docs/research_cycles/V72P2D7-GF32-CROSS-LAYER-DISCRIMINATOR/D7_E_RESULT_ACCEPTANCE_R1.md` (commit `f4c06042`); 192/192 calls, 64/64 transfer eligible+invoked; f=1.2 L2_TO_L1 3/16–7/16 `STRONG_TRANSFER_LIFT` (transfer-only 4, control-only 0); integrity `PASS_WITH_DISCLOSED_VERIFY_PROVENANCE_GAP`.
- D7-F freeze [repo-observed]: commit `aca2b6b` (OpenSpec `v72p2d7-reverse-order-cross-layer-discriminator`, prereg + execution packet); 32 identities × 4 = 128 calls max; `FORWARD_L1_TO_L2` vs `REVERSE_L2_TO_L1`; CHECK_UPDATED-only transfer; no-feedback evidence-use contract; 5 paired labels; 10 terminals.
- D7-F implement+reviews [repo-observed]: module `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_reverse_order_discriminator.py` + tests `test_v72p2d7_gf32_reverse_order_discriminator.py` (41 tests) + script `scripts/v72p2d7_gf32_reverse_order_discriminator.py`; 41/41 green in both reviews, BP regression green (inner 23 passed); `D7_F_IMPLEMENTATION_REVIEW_PASS` + `D7_F_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION` (single live VmHWM probe).
- Posture [decision]: readiness gate `D7_F_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION` pending closeout (committed `cycle_state.yaml` still `D7_F_IMPLEMENTATION_PENDING` with PENDING reviews); no UUID, no `workspace/d7_f_*` root, all authorizations false, attempts/decoder/result zero/false; R1d/G1/G2 unauthorized; >2-stage alternating still blocked pending cavity/extrinsic-message contract; no push.
## 2026-09-11 D7-F accepted as reverse-order regression diagnostic; route to D7-G extrinsic contract proposal

- Accepted facts [repo-observed]: immutable D7-F root `b6d62184-...` (auth `a099b257` → revoke `851efb92`, solidification `8e3bdbee`); 128/128 calls, zero blocked/retry/crash/nonfinite/watchdog; f=1.0 forward/reverse both-exact 0/16; f=1.2 forward 2/16 (seeds 1302/1304) reverse 0/16; table candidate_only 0 / reference_only 2 / both 0 / neither 14; forward source exact 3 / target exact 3 overlap 2; reverse source L2 exact 0 / target L1 exact 7; terminal `D7_F_REVERSE_ORDER_REGRESSION`; Pre-RESULT `D7_F_PRE_RESULT_REVIEW_PASS_R1`; acceptance doc `D7_F_RESULT_ACCEPTANCE_R1.md`.
- Scope [decision]: `D7_F_RESULT_ACCEPTED_REVERSE_ORDER_REGRESSION_DIAGNOSTIC` — single sequential reversal does not convert D7-E directional target lift into complete two-layer recovery under this frozen contract; no L2→L1-useless/alternating-impossibility/general-NB-LDPC/FER/leakage/key/qualification/R1d/G1/G2 claim.
- Route [decision]: `next_gate` → `D7_G_EXTRINSIC_CONTRACT_PROPOSAL`; code-factor extrinsic contract next, feedback still out. All authorizations false; no push.
## 2026-09-11 D7-G code-factor extrinsic contract certified + dual review PASS (interface only; D7-H not frozen/not authorized)

- Contract [decision]: cold decoder outgoing code-factor message `L_code_ext = L_post − log(p_in)` up to per-row constant; stored LSE-normalized, transported via stable softmax (row constants invariant; reconstruction `softmax(log p_in + store) = softmax(L_post)` exact). Enums `NO_CHECK_EVIDENCE`/`CHECK_EXTRINSIC`/`WARM_START_UNSPECIFIED`; additive optional `DecoderResult` fields `extrinsic_log_beliefs`/`extrinsic_provenance` (default `None`); it0 neutral zeros + `NO_CHECK_EVIDENCE` (ineligible, no false lift); warm `WARM_START_UNSPECIFIED` fail-closed; flooding extrinsic `DEFERRED` (defaults only, outputs unchanged).
- Certification [repo-observed]: independent numpy-only oracle (`itertools`/`numpy` only, zero production imports); tree-exact ≤3.34e-16, loopy-vs-recurrence ≤3.03e-14 (never MAP, `syn_ok` False), forward+backward sum-product match ≤3.34e-16, all vs `1e-10` tolerance; double-count counterexample deterministic (msg gaps 0.387/0.367 vs 1e-2 floor; transfer gaps fwd 0.0657, bwd 0.0139/0.00646, redecoded 0.005105 vs 1e-3 floor); contract suite 48/48; D7-A 14/14 unchanged.
- Reviews/compat [repo-observed]: `D7_G_EXTRINSIC_CONTRACT_REVIEW_PASS` (F01) + `D7_G_EXTRINSIC_INTEGRATION_READINESS_PASS` (F02); v35 diff +127/−0 additive; all existing consumers remain on prior posterior/`belief_provenance` contracts (zero extrinsic refs outside v35+oracle); helper accepts only explicit `CHECK_EXTRINSIC`, fully unwired from production (inventory PASS).
- Posture [decision]: interface/certification only, not an algorithm result; prescribed next gate `D7_H_ALTERNATING_DISCRIMINATOR_PACKET_FREEZE` (closeout pending — `cycle_state.yaml` still `next_gate D7_G_IMPLEMENTATION_PENDING`, `d7g_result_accepted false`); D7-H not frozen/not authorized; no D7-G/H roots/UUID; all authorizations false; R1d/G1/G2 unauthorized; >2-stage alternating still blocked pending future D7-H packet; no push.

## 2026-09-13 D7 root-cause and route-reset R1: A–F accepted per master packet; Phase P (X1–X4) readiness reviewed PASS_WITH_FINDINGS — terminal X1_READY_AWAITING_EXPLICIT_AUTHORIZATION (no execution, no authorization)

- Milestone [repo-observed]: OpenSpec `formal-ir-d7-root-cause-and-route-reset` Phases A–F implemented under packet `.workbuddy/tasks/D7_ROOT_CAUSE_AND_ROUTE_RESET_R1_TASK_PACKET.md`; zero production decoder/CAL/VAL/G1/multi-graph/G2/D7-H calls; no commit, no push; historical evidence retained byte-identical. New module `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_consistency_multigraph.py`, CLI `scripts/v72p2d7_consistency_multigraph.py`, tests `comparison_bench/tests/test_v72p2d7_r1_consistency_multigraph.py`; scoped D5 edit `v72p2d5_gf32_rate_mother.py` +278/−33 (canonical helpers, additive per-layer G1 schema, no-write provenance probe, G2 wall/RSS recording + gates); cycle docs under `docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/`; one decision-log entry.
- Review [repo-observed]: independent implementation review (`reviewer-go-backup`, separate context) returned `PASS-WITH-FINDINGS` (no blockers); durable record `docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/INDEPENDENT_REVIEW_R1.md`; not accepted, no scientific promotion. `cycle_state.yaml` advanced from `IMPLEMENTATION_REVIEWED_AWAITING_MAIN_THREAD_ACCEPTANCE` to state/terminal `IMPLEMENTATION_REVIEWED_AND_CORRECTED_AWAITING_MAIN_THREAD_ACCEPTANCE`, `independent_review: PASS_WITH_FINDINGS`, `d7f_count_correction: MAIN_THREAD_AUTHORIZED_APPLIED_REVERIFIED`, `next_gate: MAIN_THREAD_ACCEPTANCE`; `implementation_accepted: false`; all execution flags false.
- Equivalence [decision]: same-input contract (identical in-memory graph/block/priors/injected decoder results) — G1-compatible and D7 paths give bitwise-identical `q`, equal syndromes/decoded target/per-layer counters, and L1/L2 priors equal within float64 reassociation (max-abs-diff 6.9e-18..2.1e-17 vs frozen `atol=1e-12`); conditional on identical input priors (estimator difference `build_f_model` vs `build_f_model_concentration` outside scope). Claim ceiling: implementation candidate.
- G1 correction [decision]: historical G1 did NOT use `None` beliefs or a silent uniform L2 prior (old wrapper array-converted `final_beliefs`; row-layered decoder updated beliefs through its 90 iterations); current code checks provenance before the `bel1 is None` branch and fails closed.
- G2 [decision]: `G2_PENDING_NOT_FAILED_NOT_SKIPPED_NOT_SUPERSEDED`, `G2_RUNTIME_UNVERIFIED`; frozen accepted-plan matrix n=256, f=(1.0,1.1,1.2), L1 rows (196,215,235), L2 rows (172,189,206), block seeds 2026091000..2026091199, graph seeds 2026090501/2026090502, APP 200 + oracle 40 per f; four-state grading preserved; P0 485 s projection is not a reliable estimate; X4 needs separate explicit authorization + independent Pre-RESULT review.
- D7-F corrigendum [decision]: `D7_F_REVERSE_ORDER_REGRESSION` is a historical machine label only (single graph pair 2026090501/2026090502, n=16 block seeds 2026091300..2026091315, f=1.2), not an immutable general mechanism fact; per immutable D7-F prereg (`C` = reverse candidate, `R` = forward reference) the discordant table is reference-only (forward-only) 2 / candidate-only (reverse-only) 0 / both 0 / neither 14, exact two-sided McNemar p=0.5; weak evidential status; historical artifacts byte-identical. OPEN ITEM [repo-observed] (finding retained as history; RESOLVED 2026-09-13): packet §4, `D7_F_CORRIGENDUM_R1.md`, `proposal.md`, `spec.md`, and the decision-log entry stated "candidate-only 2 / reference-only 0", swapped against the immutable D7-F `stratum_summary.csv` (`candidate_only=0, reference_only=2`). Resolution [decision, 2026-09-13]: main thread authorized a scoped text-only correction; applied to six locations (the five listed above plus the `OPERATOR_RETURN_R1.md` A04 line + delta note; packet §4 original line preserved with a dated main-thread-authorized correction note). All now state candidate-only 0 / reference-only 2 / both 0 / neither 14, matching `stratum_summary.csv`. Focused independent re-verification (separate context): PASS — ground truth re-read; residual inverted-phrasing scan clean except the intentionally preserved packet original line; historical artifacts, code, tests untouched; no commit, no push. Still awaiting main-thread acceptance; no acceptance or execution authorization implied.
- Dormant phases [decision]: X1 read-only probe (`x1_consistency_probe_authorized` + `python scripts/v72p2d7_consistency_multigraph.py --consistency`); X2 frozen multi-graph batch (3 graph pairs, block seeds 2026091300..2026091315, 4 arms, `MAX_CALLS=384`, f=1.2 rows 59/52 primary + f=1.0 rows 49/43 sanity) needs Pre-EXECUTE review + explicit authorization + fresh `workspace/d7_r1_multigraph_<uuid>` root + recorded wall budget; X3 reference ladder (90/360/flooding-90, f=1.2 failing blocks only) with/after X2; X4 G2 unbundled; D7-H awaits X2–X4 reviewed evidence + new main-thread route decision. All authorization flags false at triage.
- Open notes [repo-observed]: D5 `_load_v35_provenance_module` now prefers the `comparison_bench.src.comparison_bench` layout before the flat layout (behavior change not described in design; traced safe in tested layouts, record on acceptance); `bind_reference_ladder_decoders` unexercised until X3; minor gaps (G2 evidence lacks APP iteration totals, None-RSS→BLOCKED rule not in design §7, unused `PER_CALL_WATCHDOG_S`); pre-existing stale-world-state D7 suite failures reproduced (accepted historical roots exist while tests assert absence; files unmodified, unrelated); worktree not quiescent during review (`docs/v35-algorithm-development-report.md` mtime 2026-09-13 03:26 after the 03:06 operator return).

### Phase P (D7 X1–X4 execution master R1) — readiness reviewed; awaiting explicit user X1 authorization (no execution)

- Packet/acceptance [repo-observed]: `.workbuddy/tasks/D7_X1_X4_EXECUTION_MASTER_R1_TASK_PACKET.md` is the sole operational packet for X1–X4 (Phase P readiness-only). The A–F implementation boundary is accepted per master packet §1 with main-thread acceptance recorded 2026-09-13; `cycle_state.yaml` now `implementation_accepted: true` (the earlier `implementation_accepted: false` recorded at the A–F review point is superseded).
- Phase P implementation [repo-observed]: P01–P09 closed — X1 `--historical-provenance-probe` calls `probe_historical_decoder_provenance(decode_fn=None)` exactly once with JSON contract/exit rules and authorization refusal; X3 selector/plan/guard/reconstruction, field-exact `ROW_LAYERED_90` baseline replay gate, 7-file never-overwrite writer labeled `STRONG_REFERENCE_DIAGNOSTIC`, CLI `--reference-ladder --x2-root/--out-root`; X4 `--g2` bridge requiring `x4_g2_execution_authorized`, asserting every other D5 flag false, exactly-once `run_g2_synthetic(authorized=True)`, abort-if-exists on frozen root `workspace/v72p2d5_g2/20260906_r1`. Zero production decoder/CAL/VAL calls; no writes to frozen roots.
- Readiness review [repo-observed]: independent Phase P readiness review `PASS_WITH_FINDINGS`, no blockers — `docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/PHASE_P_INDEPENDENT_READINESS_REVIEW_R1.md`; readiness record `PHASE_P_PRE_EXECUTE_READINESS_R1.md`; `REVIEW_ENTRYPOINT.md` updated. Tests replayed independently: new suite 55, consistency 36, bp+decert+new 92, predecessors 165/32/62/32, `py_compile` exit 0; per-group invocation is the T1 protocol (mixed cross-suite fragility pre-existing and disclosed).
- X3 call accounting [decision]: total = 3S + R ≤ 576 − 2R ≤ 576 by construction (equality only when all 192 selected); the earlier "worst case 672" wording was an unachievable over-count and has been corrected. X3 Pre-EXECUTE/Pre-RESULT must verify `ladder_calls + reconstruction_calls <= 576` from actual records.
- Prior finding resolved [repo-observed]: `bind_reference_ladder_decoders` binding/import/signature coverage done with fakes plus a clean-subprocess real v35 import + real bind without invoking a wrapper; true-condition binding probe belongs to X3 Pre-EXECUTE before authorization consumption.
- Carried non-blocking findings for phase Pre-EXECUTE [repo-observed]: (a) X3 `X3_ENGINEERING_BLOCKED` exits 0 (only baseline mismatch → exit 1) — document or make nonzero; (b) `run_g2_bridge` checks repo-rooted G2 root while writer resolves CWD-relative — pass resolved `out_dir` in the runner closure at X4 Pre-EXECUTE; (c) per-call watchdogs (X1/X4 120 s, X3 480 s) are external, not in-process — record external watchdog owner at X3 Pre-EXECUTE; (d) `X3_BASELINE_REPLAY_MISMATCH_BLOCKED` also covers ladder crashes/reconstruction errors — Pre-RESULT must read the `where` field; (e) `run_g2_bridge` coerces a non-dict runner return to `{}` (latent); (f) OpenSpec delta spec not extended for Phase P entrypoints (design §9 + tasks P cover them; optional).
- Lifecycle posture [repo-observed]: `cycle_state.yaml` `state`/`terminal` = `X1_READY_AWAITING_EXPLICIT_AUTHORIZATION`, `next_gate: X1_MAIN_THREAD_AUTHORIZATION`, `phase_p_readiness: REVIEWED_PASS_WITH_FINDINGS`, `execution_authorization: EXECUTION_NOT_AUTHORIZED`; all eight authorization flags false, no authorization consumed; frozen roots `workspace/d7_r1_multigraph_20260913_r1`, `workspace/d7_r1_reference_ladder_20260913_r1`, `workspace/v72p2d5_g2/20260906_r1` absent; branch `formal-ir-v72p1-addendum-clean`, HEAD `278fdf07`; no commit, no staging, no push.
- Next gate [decision]: X1 execution requires explicit user authorization (`x1_consistency_probe_authorized: true` plus the exact frozen command from master packet §7) at the main thread's gate; X2/X3/X4 and D7-H each remain separately non-authorized and no phase authorizes the next. This entry implies no execution authorization and no results.

### D10 mixed-degree L1 R1 readiness — revise required (2026-09-14)

- Reviewer trust [decision]: the D10 `EVIDENCE_ACCESS: VERIFIED` independent
  review and independently executed tests are accepted; no ceremonial suite
  duplication is required. Main-thread route/scientific adjudication remains
  separate from reviewer correctness checks.
- R1 disposition [decision]: `REVISE_REQUIRED_CONNECTIVITY_AND_RANK`; no L1
  decoder batch authorization. All 18 profiled graphs were fragmented
  (9--68 components, largest-component fraction 0.039--0.297) and several had
  GF32 rank below `m`, so degree-profile effects would be confounded by graph
  decomposition/effective constraint rank.
- Next gate [decision]: D10 connectivity/rank R2 implementation/readiness only,
  preserving degree tables and original seeds and requiring one component,
  structural check-covering rank `m`, and GF32 row rank `m`. Failure stops
  without seed search; decoder execution requires a later explicit grant.

### D10 mixed-degree L1 R2 readiness accepted (2026-09-14)

- Evidence [repo-observed]: R201--R212 complete; independent R211
  `EVIDENCE_ACCESS: VERIFIED / PASS`; 44 focused tests independently passed;
  PROFILE_ONLY admitted 18/18 original cells with one Tanner component,
  structural rank `m`, GF32 rank `m`, zero replacement seeds, and zero
  decoder/scientific calls.
- Decision: accept readiness as
  `D10_MIXED_DEGREE_L1_R2_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`.
  Reviewer N1--N3 are non-blocking; do not duplicate the independent suites.
- Boundary: the next D10 batch A1 still requires explicit user authorization;
  acceptance alone grants no execution and does not revive D7-H.

### Phase P execution (D7 X1–X4 execution master R1, A1 + A2) — all four phases executed serially under one authorization, each attempt independently reviewed; X4 complete verified awaiting main-thread route decision (no acceptance, no route conclusion; records under `docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/`)

- Lifecycle [repo-observed]: one serial X1–X4 authorization granted 2026-09-13 (`.workbuddy/tasks/D7_X1_X4_EXECUTION_MASTER_R1_A1_TASK_PACKET.md`; grant record `X1_X4_AUTHORIZATION_A1.md`), one authorized attempt per phase, each gated by its own independent review; `cycle_state.yaml` state/terminal `X4_COMPLETE_VERIFIED_AWAITING_MAIN_THREAD_ROUTE_DECISION`, `next_gate: MAIN_THREAD_ROUTE_DECISION_D7H`, `x1_x4_authorization_consumed: ALL_CONSUMED_X1_X2_X3_X4_EXECUTED`; all execution flags false; `historical_evidence: RETAINED_BYTE_IDENTICAL`; D7-H/G1/real/n=1024 unauthorized; no commit, no staging, no push (entire R1 cycle uncommitted; branch `formal-ir-v72p1-addendum-clean`, HEAD `278fdf07` unchanged).
- X1 [repo-observed]: pre-fix probe failed `X1_PROVENANCE_PROBE_FAILED` (exit 2, `PRIOR_ONLY`, iterations 0) because `_probe_fixture` used zero syndrome + uniform prior, so the historical row-layered decoder's iteration-0 early return (`v35_algorithm_development.py:835-854`) always fired and the frozen success contract (`CHECK_UPDATED`, iterations>=1) was unsatisfiable by construction — decoder correct, fixture at fault; independently verified `X1_FAILURE_VERIFIED`. Main-thread-authorized fixture-only fix in `v72p2d5_gf32_rate_mother.py` (`_probe_fixture`: syndrome [1,2], x_true [0,1]; h/prior unchanged), independent fix review `PASS_WITH_FINDINGS`, then one authorized rerun: exit 0, `CHECK_UPDATED`, iterations 90, decoder_calls 1, writes 0, no root; independently verified `X1_RERUN_VERIFIED`. X1 complete.
- X2 [repo-observed]: one attempt, exit 0, 384/384 calls, terminal `GRAPH_SENSITIVITY_OBSERVED`, scope `EXPLORATORY_SYNTHETIC_SINGLE_IMPLEMENTATION`; per-graph f=1.2 paired discordant vectors (forward_only, reverse_only, both, neither) (2,0,0,14)/(2,0,0,14)/(1,0,0,15), descriptive exact McNemar p=0.5/0.5/1.0 with Wilson intervals; exact/syndrome separated (36/36); zero crash/blocked/nonfinite; stored wall 131.5423 s, max per-call 0.4907 s, RSS 133185536 B; root `workspace/d7_r1_multigraph_20260913_r1` (7 files, fresh, no-overwrite); independent `X2_PRE_RESULT_REVIEW_PASS`.
- X3 [repo-observed]: one attempt, exit 0, terminal `X3_REFERENCE_LADDER_COMPLETED`; S=156 (51/54/51; 87 SOURCE/69 TARGET), reconstruction R=4, ladder 3S=468, total 472<=576; `ROW_LAYERED_90` baseline replay field-exact 156/156; arms RL90 0 exact, RL360 1 exact (rescue: record_idx 29, slot 40, graph 0, L1_MARGINAL, SOURCE, seed 2026091310, iterations 231, changed=True), FLOODING_90 0 exact; stored wall 372.2475 s, max call 1.7976 s, RSS 134381568 B; root `workspace/d7_r1_reference_ladder_20260913_r1` (7 files, fresh, no-overwrite); label `STRONG_REFERENCE_DIAGNOSTIC`; true-condition bind probe before consumption: 0 decoder invocations; independent `X3_PRE_RESULT_REVIEW_PASS`.
- X4 [repo-observed]: one attempt, exit 0, grade `G2_CURRENT_CONFIGURATION_FAILED` (measured frozen four-state grade, not a route conclusion); 1320/1320 calls (440/f; 200 blocks/f; oracle subset 40/f); all f: L1/L2 exact 0, syndrome 0, provenance 200/200 `CHECK_UPDATED`, transfers 200 invoked / 0 blocked, crashes 0, nonfinite 0, monotonic true; stored wall 2141.94 s, outer 2143.83 s, RSS 159182848 B; root `workspace/v72p2d5_g2/20260906_r1` (4 files, fresh, no-overwrite); independent `X4_PRE_RESULT_REVIEW_PASS`. Pre-EXECUTE carried-findings adjudication `ACCEPTED-AS-IS` with conditions (`X4_PREEXECUTE_ADJUDICATION_R1.md`): repo-rooted existence check and CWD-relative writer coincide under CWD=repo root; non-dict runner coercion unreachable on the production runner path (injected-runner/test-only); external 120 s per-call watchdog owned by the operator with stall monitoring (0 stalls).
- A2 remediation [decision]: user grant 2026-09-13 (`A2_X2_X4_REMEDIATION_AUTHORIZATION_R1.md`) allowed, on any X2/X3/X4 first-attempt failure, one scoped implementation-level fix + independent review + exactly one second attempt with frozen contract unchanged, plus final disclosure of changes and exploration-goal impact. Not used — X2/X3/X4 first attempts all completed.
- Carried non-blocking [repo-observed]: stale D5-derived markers `g2_status: G2_PENDING_NOT_FAILED_NOT_SKIPPED_NOT_SUPERSEDED` and `g2_runtime_status: G2_RUNTIME_UNVERIFIED` remain in `cycle_state.yaml` although executed G2 evidence now exists (updating them is a main-thread acceptance decision); frozen X4 evidence set has no per-call wall field, so per-call <=120 s compliance is externally owned and not machine-observable; P0's 485 s runtime projection vs measured stored wall 2141.94 s (4.4x) — projection non-binding and not used for any decision.
### 2026-09-14 — D13 L055 decoder-ladder readiness accepted

- Main-thread accepted D1301–D1310 after independent `D13-R1310`
  `EVIDENCE_ACCESS: VERIFIED` / `PASS_WITH_FINDINGS`, no blocking finding.
  Durable terminal:
  `D13_L055_DECODER_LADDER_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`.
- Frozen diagnostic selects exactly 56 D12 L055 failures (n128 30, n256 26)
  and compares strict RL90 replay with RL360, RL360 damping 0.7, and
  flooding-360 in 224 calls. Readiness acceptance grants no execution.
- Trust rule applied: do not mechanically duplicate reviewer-go tests or
  recomputations when evidence access is VERIFIED and no blocking inconsistency
  exists. Main-thread route adjudication and user-only authorization remain
  separate.
### 2026-09-14 — D13 accepted MODEST; D14 validity reset selected

- D13 Batch A1 accepted as `D13_RESULT_ACCEPTED_MODEST_CLOSE_LADDER`:
  strict replay 56/56; RL360 alpha=1 rescued 3/56 (MODEST), damping 0.7 1/56,
  flooding-360 0/56. Close the ladder; do not select a decoder arm or rerun.
- Current D5 synthetic production entrypoints P0/G1/G2 still call the rejected
  per-cell `prepare_model_f_prior`; X4/G2 therefore describes failure of that
  legacy configuration, not valid n=256 finite-length evidence. Preserve the
  root and record a corrigendum rather than altering artifacts.
- Before another L1/L2 route, independently reconcile the actual synthetic
  generator entropy and per-block information load against row budgets for both
  layers. D7-H remains closed until this channel/rate calibration is valid.
### 2026-09-14 — D14 C-impl: G2 prior-configuration corrigendum recorded (docs only)

- Additive corrigendum `docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/G2_PRIOR_CONFIG_CORRIGENDUM_R1.md`
  (D14 VR-C): root `workspace/v72p2d5_g2/20260906_r1` preserved unchanged (4 files,
  1320/1320 calls); literal grade `G2_CURRENT_CONFIGURATION_FAILED` retained for the
  executed rejected per-cell-prior configuration; that result is invalid as n=256
  finite-length feasibility / route-closure evidence; supersession covers the inference
  only, not the execution; no unique-cause claim. Pointer blocks appended to D5
  `G1_WIDE_ATTRIBUTION_R2.md` §10 and D7 `OPERATOR_RETURN_R1.md` §10; additive
  status lines in both `cycle_state.yaml` files; no historical line rewritten.

## 2026-09-14 D14 Scientific Validity Reset R1 complete (calibrated batch ready, unauthorized)

- Close [repo-observed]: D14-FINAL `EVIDENCE_ACCESS: VERIFIED` / `PASS_WITH_FINDINGS`, no blocker; terminal `D14_VALIDITY_RESET_COMPLETE_CALIBRATED_BATCH_READY_AWAITING_EXPLICIT_AUTHORIZATION`. S 4 local commits (`55ab6de`/`5f4b121`/`43308b8`/`ccc33eb`), 70 paths, no push; group1 deferred, group5 STOPPED (mixed hunks, compliance). P 5 hunks (+7/-5) to candidate prior chain, D14P 4/4. C corrigendum + root untouched. R root `workspace/v72p2d14_rate_audit/20260914_r1/` (entropy 4dp reproduced, triple mismatch +0.003/+0.001/+0.003 retained never copied, 10/10 tests, single corrective rerun disclosed in log). N prereg Choice A (m_L1=110, 550 disclosed, 1.00237; n128; 288 calls; seeds/root/runner absent).
- Lifecycle [decision]: N batch unauthorized; no route decision, no D7-H, no FER/leakage/SKR/real-data/qualification/promotion claim. Next gate is a separate explicit batch grant + DECIDE Pre-EXECUTE/Pre-RESULT.
- Records [repo-observed]: `docs/research_cycles/D14_VALIDITY_RESET/` (inventory + prereg + log + readiness); OpenSpec `openspec/changes/v72p2d14-scientific-validity-reset/`.
### 2026-09-15 — D14 N prereg accepted; runner implementation is the next gate

- D14-FINAL is trusted and accepted, but its N runner is explicitly absent.
  Therefore the next action is implementation/readiness, not a 288-call grant.
- N is a bounded synthetic fresh-root EXPLORE batch. Execution still requires
  separate user authorization after an independently reviewed runner; the
  resulting investment route remains a main-thread decision.
- Group5 mixed memory/decision-log hunks do not block D8–D13 code reproduction;
  split only by explicit headers or leave excluded. Never stage them wholesale.

## 2026-09-14 D14N calibrated L1/L2 discriminator readiness complete (N201-N210 + Amendment A1, no execution)

- Readiness [repo-observed]: N201-N210 all PASS per `docs/research_cycles/D14_VALIDITY_RESET/D14N_READINESS_R1.md` + `EXPLORATION_LOG.md`; OpenSpec `openspec/changes/v72p2d14n-calibrated-l1-l2-discriminator/`. N210 `EVIDENCE_ACCESS: VERIFIED` / `PASS`, no blocker: 18/18 admission with amended check-allocs (L045 2^17+3^93 / L055 2^29+3^81 at m_L1=110), 22/22 tests rerun, PROFILE 288-plan, refusal RC=2, decoder/scientific 0, future root `workspace/v72p2d14_discriminator/20260914_r1` absent; APP-source FLAG carried to batch-runner freeze.
- Amendment [repo-observed]: pre-code STOP on m110/m118 check-alloc contradiction with zero writes → main-thread adjudication (A) adopted: variable side stands, check side recomputed via D9 rule; retry green. Prereg file untouched (supersede, not edit).
- Lifecycle [decision]: terminal `D14N_CALIBRATED_DISCRIMINATOR_READY_AWAITING_EXPLICIT_AUTHORIZATION`; grants no execution; N batch unauthorized; no route decision; no D7-H. Scoped local commit `4b11d60` (9 paths), no push; group5 memory/decision entries EXCLUDED uncommitted (mixed hunks, carried).
- Boundary [decision]: synthetic n128 L1/L2 diagnostic only; no FER/leakage/SKR/real-data/qualification/promotion claim.
### 2026-09-15 — D14N readiness blocked: authorized batch branch missing

- Main-thread inspection found that the D14N CLI handles profile, verify and
  unauthorized refusal, but authorized `--n14-batch` unconditionally exits with
  "production ... adapters belong to a later authorized change". It cannot run
  or write the frozen 288-call batch.
- Retain the reviewed m=110 amendment, 18/18 admission, plan/gates and refusal
  evidence. Do not grant A1 until a minimal R2 implements binding/dispatch/write
  and a fake-injected authorized true-branch test proves 288 calls + verifier.
## 2026-09-14 D14N R2 authorized-path completion close (docs only, path ready, batch unauthorized)

- Readiness [repo-observed]: R201-R207 PASS_WITH_FINDINGS per `docs/research_cycles/D14_VALIDITY_RESET/D14N_READINESS_R1.md` §7 + `EXPLORATION_LOG.md` R2 section; OpenSpec `openspec/changes/v72p2d14n-calibrated-l1-l2-discriminator/` §9 + R2 tasks. R201 froze APP←L055 CHECK_UPDATED source (gate-coherence) + corrected stale ≤26/m=118. R202-R206 replaced authorized-path SystemExit with narrow binder + 288-plan-first orchestrator + single `run_authorized_batch`/`write_batch_root` writer. R207 `EVIDENCE_ACCESS: VERIFIED` / `PASS_WITH_FINDINGS`, no blocker: 14/14 adapters is-identical, no-SystemExit, fake 288/288 (M110 144 / M104 144, SETUP=32, ROWS==PLAN, N_ROUTE_SCALE_VALIDATION), verifier 288/0, future root absent, zero production (V35_ABSENT, binder 0, probe 0/0), refusal RC=2 pre-bind/load.
- Lifecycle [decision]: terminal `D14N_R2_EXECUTION_PATH_READY_AWAITING_EXPLICIT_AUTHORIZATION`; path ready, real N batch still unauthorized; no route decision; no D7-H. Scoped local commit `3f874bb` (8 paths), no push; d5 + group5 memory/decision hunks EXCLUDED uncommitted (carried).
- Boundary [decision]: synthetic n128 L1/L2 diagnostic only; no FER/leakage/SKR/real-data/qualification/promotion claim. Pre-EXECUTE carries APP-source L055 freeze + d5-tree reconfirm + target-absence + frozen command/budgets/authorization.
### 2026-09-15 — D14N R2 execution path accepted; N-A1 is next

- R2 replaced the authorized-path SystemExit with exactly one orchestrator and
  one writer. Independent fake true-branch evidence: 288/288, setup 32, six
  files, verifier PASS, zero production calls. Accepted terminal:
  `D14N_R2_EXECUTION_PATH_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`.
- Before N-A1, verify D5 P-wiring still calls the candidate prior at P0/G1/G2
  and APP source remains L055. Execution needs a separate one-shot user grant;
  D7-H and the route decision remain closed.

## 2026-09-14 D14N calibrated discriminator Batch A1 complete + VERIFIED PASS batch-end review (evidence-only)

- Evidence [repo-observed]: single authorized run in fresh root `workspace/v72p2d14_discriminator/20260914_r1` (6 files, hashes match); EXIT 0, 18:52:43–18:55:40Z; 288/288 calls, 32/32 setup, wall 170.990/1800, per-call-max 0.928/120, RSS 137207808<2GiB, violations []; 18/18 admission (amended cells); exact total 80 = syndrome 80, undetected 0 (L045 3 [1,0,0,0,1,1] / L055 7 [1,0,1,2,2,1] / APP joint 7 / ORACLE 63 [11,11,10,9,12,10]); APP←L055, provenance 216 CHECK_UPDATED + 72 ORACLE ungraded; predicates L1-ADEQUATE FALSE (7<18, ge2 2/6) / ORACLE TRUE (63) / JOINT FALSE (7<9) → N_ROUTE_L1_CONSTRUCTION (evidence-only); Model-F unchanged; grant consumed; no retry/repair; no D7-H/real-data; no commit/push.
- Review [repo-observed]: batch-end review = `EVIDENCE_ACCESS: VERIFIED` / PASS, no blocker. Full record in `docs/research_cycles/D14_VALIDITY_RESET/EXPLORATION_LOG.md`.
- Lifecycle [decision]: terminal `D14N_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`; evidence-only, no route acceptance; grant consumed; no second run.
- Boundary [decision]: synthetic calibrated n128 L1/L2 discriminator only; no FER/leakage/SKR/forward/L2/real-data/qualification/promotion/D7-H claim. Next gate is main-thread route decision only.
- Interpretation [decision]: at calibrated effective≈1.0 disclosure, L055 L1 exact collapsed 42/72 (D12 CE-rate) → 7/72 — D12 advantage was a rate artifact (main-thread interpretation, not a claim).
### 2026-09-15 — D14N accepted; route deferred because layer margins differ

- Accepted 288-call evidence: L045 3/72, L055 7/72, L2 APP joint 7/72,
  L2 ORACLE 63/72; exact=syndrome, undetected 0, VERIFIED PASS. Literal machine
  terminal `N_ROUTE_L1_CONSTRUCTION` is retained.
- Main-thread terminal is
  `D14N_RESULT_ACCEPTED_MARGIN_CONFOUNDED_ROUTE_DEFERRED`: L1 effective margin
  was about 1.002 and L2 oracle about 1.261, so the result cannot yet choose L1
  construction versus L2 degree investment. L055 still beats L045 7 vs 3; only
  its absolute near-entropy adequacy failed.
- Next evidence is a paired L1/L2 matched-margin finite-length curve. D7-H stays
  closed.
## 2026-09-15 D15 finite-length margin curve readiness complete (D1501-D1510, no execution)
- Terminal `D15_MARGIN_CURVE_READY_AWAITING_EXPLICIT_AUTHORIZATION`; predecessor `D14N_RESULT_ACCEPTED_MARGIN_CONFOUNDED_ROUTE_DEFERRED`; 9 cells verified (L1 m110/114/118 + L2 m83/86/89, pairing gaps <0.004); 36/36 admission recomputed; seeds 3801-3836 + 3901-3908 frozen; 288/46 plan; no-APP; conservative route vocab; 25/25 tests; fake 288/288 + verifier; refusal RC=2; decoder/scientific 0; future root `workspace/d15_finite_margin_curve_8c1e4f2a-9b3d-4e7a-a5c6-d7e8f9a0b1c2` absent; D15-R1510 `VERIFIED PASS_WITH_FINDINGS` (D14N 3 fails = environmental stale-world-state); scoped local commit `614a0e81` (9 paths) no push. Refs: `docs/research_cycles/V72P2D15-MARGIN-CURVE/READINESS_R1.md` + `EXPLORATION_LOG.md`; OpenSpec `openspec/changes/v72p2d15-finite-length-margin-curve/`.
### 2026-09-15 — D15 matched-margin readiness accepted

- Accepted terminal:
  `D15_MARGIN_CURVE_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION` after
  D15-R1510 VERIFIED PASS_WITH_FINDINGS, no blocker. Three L1/L2 row pairs have
  effective-factor gaps <0.004; 36/36 graphs admitted; fake 288/288 and verifier
  PASS; production calls zero.
- Materialized D14N-root absence-guard failures are stale predecessor state, not
  a D15 gate. D15 execution still requires a one-shot user grant; D7-H remains
  closed.
## 2026-09-15 D15 margin-curve Batch A1 complete + VERIFIED PASS_WITH_FINDINGS batch-end review (ambiguous, evidence-only)
- Evidence [repo-observed]: single authorized run in fresh root `workspace/d15_finite_margin_curve_8c1e4f2a-9b3d-4e7a-a5c6-d7e8f9a0b1c2` (6 files, hashes match); EXIT 0, 06:56:08–06:59:36Z; 288/288 calls, 46/46 setup, wall 201.7/1800, per-call-max 1.319/120, RSS 139161600<2GiB, violations []; 36/36 admission; exact total 61 = syndrome 61, undetected 0 (L045 0/6/19; L055 1/13/22; L2-ORACLE 0/0/0); monotonic non-decreasing all arms; WEAKx7 + MIDDLEx2, ADEQUATE none → MARGIN_CURVE_AMBIGUOUS (evidence-only); Model-F unchanged; grant consumed; no retry/repair; no APP/D7-H/real-data; no commit/push.
- Review [repo-observed]: batch-end review = `EVIDENCE_ACCESS: VERIFIED` / PASS_WITH_FINDINGS, no blocker; L2-ORACLE-zero recorded as evidence only (zero interpretation). Full record in `docs/research_cycles/V72P2D15-MARGIN-CURVE/EXPLORATION_LOG.md`.
- Lifecycle [decision]: terminal `D15_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`; evidence-only, no route acceptance; grant consumed; no second run.
- Boundary [decision]: synthetic matched-margin single-layer diagnostic only; no FER/leakage/SKR/forward/real-data/qualification/promotion/D7-H claim. Next gate is main-thread route decision only.
### 2026-09-15 — D15 accepted AMBIGUOUS; one matched backoff point next

- D15 accepted: L045 0/6/19, L055 1/13/22, L2 ORACLE 0/0/0 across increasing
  margins; all monotonic, exact=syndrome, undetected 0; terminal
  `MARGIN_CURVE_AMBIGUOUS` retained.
- Next minimal discriminator uses L1 m125 (factor 1.1390555) and L2 m94
  (1.1393714), gap 0.00031594. It tests whether L1 crosses adequacy while L2 DV3
  remains weak before starting L2 degree work. D7-H stays closed.
## 2026-09-15 D16 matched-backoff discriminator readiness complete (D1601-D1609 + alignment + re-verify, no execution)
- Terminal `D16_MATCHED_BACKOFF_READY_AWAITING_EXPLICIT_AUTHORIZATION`; predecessor `D15_RESULT_ACCEPTED_ROUTE_TO_ONE_POINT_BACKOFF_DISCRIMINATOR`; one-point n128 at factor ≈1.139 (L1 m125 disclosed 625 / L2 m94 disclosed 470, gap 0.0003159373731645); cells L045 71/57/313 2^62+3^63 + L055 83/45/301 2^74+3^51 + L2 128×3/384 4^86+5^8; 12/12 admission recomputed; seeds 4001-4012 + 4101-4108 frozen; 96/22 plan; no-APP; six terminals (packet string D16_MATCHED_BACKOFF_SUFFICIENT authoritative, implementation aligned, re-verified); 26/26 tests; fake 96/96 + verifier; refusal RC=2; decoder/scientific 0; future root workspace/d16_matched_backoff_discriminator_b7c2d4e6-8f1a-4c3d-9e5b-2a4f6c8d0e1a absent; D16-R1608 VERIFIED PASS_WITH_FINDINGS + R1608A PASS (D15 4 fails = environmental stale-world-state); scoped local commit a0260907 (9 paths) no push; D15 log pointer + d5/group5 hunks EXCLUDED uncommitted (carried).
- Refs: docs/research_cycles/V72P2D16-MATCHED-BACKOFF/READINESS_R1.md + EXPLORATION_LOG.md; OpenSpec openspec/changes/v72p2d16-matched-backoff-discriminator/.
- Boundary: synthetic one-point matched-backoff diagnostic only; batch unauthorized; no route choice; no D7-H; no FER/SKR/qualification/promotion/real-data claim.
### 2026-09-15 — D16 matched-backoff readiness accepted

- Accepted terminal:
  `D16_MATCHED_BACKOFF_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`.
  Factors differ by 0.00031594; 12/12 graphs admitted; fake 96/96 and verifier
  PASS; production calls zero. Terminal spelling is aligned to
  `D16_MATCHED_BACKOFF_SUFFICIENT`.
- D16 Batch A1 still requires a one-shot user grant. Pre-dispatch reconfirms
  uncommitted D5 candidate-prior wiring. No route choice or D7-H.
### 2026-09-15 — Route reset: asymptotic DE then finite-length scaling; D16 held out

- The unconsumed D16 execution packet was withdrawn before execution. Its
  m125/m94 matched point is retained as a held-out validation point; prediction
  must be frozen before any later authorization.
- New route: current Model-F empirical channel → per-ensemble L1/L2 asymptotic
  DE threshold → explicit finite-length scaling/backoff for stated diagnostic
  error targets → held-out D16 validation → finite-graph residual analysis.
- V26 f1.3 is ancestor evidence, not automatically the current candidate-channel
  threshold. D8/D9 partly cover L1; current-channel L2 DV3 DE is missing.
- D7-H remains closed; graph/decoder pathologies are finite residuals, not an
  analytic correction inferred automatically from DE.
## 2026-09-15 D17 asymptotic-finite scaling readiness complete (A01-A05 + D01 + B/C/D02-D06 + D07, no execution)
- Terminal `D17_DE_SCALING_READY_AWAITING_EXPLICIT_AUTHORIZATION`; predecessor route-reset (D16 held out); channel identity EXACT (candidate generator, H_L1/H_L2, floor/no-renorm, P1/P2 + true-U1 oracle); DE-transfer map V26-kernel + D9-adapter reuse, f1.3 numerics do NOT transfer; finite table F1-F19/H1-3 with compatibility classes (APP/joint excluded; L2-ORACLE L2-model-only); D16 holdout locked (banned seeds 4001-4012/4101-4108, root absent, blank schema); frozen 15-pt DE grid (L045 m106-122 / L055 m116-126 capped / L2 m89-109, seeds 2026094201..08, 240 calls, V26 60/1e-4/20); probit law + ladder/downgrade/MODEL_NOT_IDENTIFIABLE + logistic-descriptive + epsilon 0.10/0.01 inversion; 30/30 tests; PROFILE_ONLY rc=0 + refusal rc=2; DE/decoder 0; future roots (DE + D16) absent; D07 VERIFIED PASS_WITH_FINDINGS (first-run fixes in-scope); scoped local commit 73c6275b (10 paths) no push; d5/group5 hunks EXCLUDED uncommitted (carried).
- Refs: docs/research_cycles/V72P2D17-DESCALING/READINESS_R1.md + EXPLORATION_LOG.md; OpenSpec openspec/changes/v72p2d17-asymptotic-finite-scaling/.
- Boundary: synthetic DE + finite-fit diagnostic only; DE batch + fit + D16 prediction all unauthorized; no route decision; D7-H closed; no FER/SKR/qualification/promotion/real-data claim.
## 2026-09-15 D17 DE Batch A1 ENGINEERING-BLOCKED + VERIFIED failure review (0/240, evidence retained)
- Evidence [repo-observed]: single authorized `--de-batch --execution-authorized` run in fresh root `workspace/d17_current_channel_asymptotic_de_7e4b2a1d-9c3f-4d8e-a1b2-c3d4e5f60718` (6 files, hashes match); EXIT 0 fail-closed, ~3s wall / 184MB RSS, setup 4/12, violations []; plan 240/240 validated, 0/240 scientific calls; failure `DE_CALL_FAILED@0 TypeError tuple-not-callable` (D9 `load_l1_channel` tuple passed as `channel_sampler` into `v26.run_mcde_posterior`; `build_l1_sampler` never invoked on production path; fakes boom production bind by design); `de_plan.csv` full 240-row plan, `de_records/traces` header-only; Model-F unchanged; D16 blank; no decoder/CAL/VAL/real-data; grant consumed; no repair/rerun.
- Review [repo-observed]: `D17-DE-B1-REVIEW` `EVIDENCE_ACCESS: VERIFIED` / PASS (STOP correct); B1 evidence unusable for fit (0/240), B2 readiness gap (zero-call bind validation needed), N1 latent L2-oracle dispatch gap, N2 RSS placeholder, N3 timestamp note. Full record in `docs/research_cycles/V72P2D17-DESCALING/EXPLORATION_LOG.md`.
- Lifecycle [decision]: terminal `D17_DE_BATCH_ENGINEERING_BLOCKED_AWAITING_DECISION`; batch-end review of DE evidence moot; single decision needed: authorize fix+rerun packet (new grant, incl. N1 scope) or stand down Batch A1.
- Boundary [decision]: synthetic current-channel DE diagnostic only; no fit/D16-prediction/D16/decoder/route/FER/leakage/SKR/qualification/promotion/real-data/D7-H claim.
## 2026-09-15 D17 DE repair R2 + Batch A2 complete + VERIFIED PASS_WITH_FINDINGS batch-end review (240/240 DE_COMPLETE, clean DE_BRACKET)
- Repair [repo-observed]: R2 L1 tuple→sampler (`build_l1_sampler` on production path; `None` channel builds via `build_production_channels`) + L2 oracle dispatch (per-entry profile dispatch from frozen plan entry, distinct tagged `{"L045":l1,"L055":l1,"L2":l2}` mapping, shared callable forbidden); R204 frozen symbols untouched (15-pt grid/seeds/pops/lambda-rho/V26 60/1e-4/20/bracket/budget/banned D16 unchanged); 37/37 focused tests; repair review `D17-R2-REPAIR` `EVIDENCE_ACCESS: VERIFIED` / REPAIR_CLOSE; zero scientific calls in repair/validation; A1 root re-hashed unchanged (six prefixes match).
- Evidence [repo-observed]: single authorized `--de-batch --execution-authorized` fresh rerun in new root `workspace/d17_current_channel_asymptotic_de_r2_61fce6d0-07ad-4b67-a1a2-ef7fc1b74b24` (6 files, hashes match); EXIT 0, 11:31:35–11:37:12Z; 240/240 scientific calls, setup 4/12, wall 322.9/1200, per-call-max 2.70/300, RSS ~0.27GiB<2GiB, violations []; dispatch (L045,L1)x80 + (L055,L1)x80 + (L2,L2)x80, 0 crashes; A2 `de_plan.csv` byte-identical to A1 (`4837bd52…`); S_pop converged 139/240 (L045 m118 8/6 + m122 8/8; L055 m119 7/6 + m122-126 8/8; L2 m99-109 8/8; else 0/0); all three profiles clean DE_BRACKET (L045 lo m114/hi m118 delta_DE 0.24452956979862517; L055 lo m116/hi m119 delta_DE 0.30312331979862517; L2 lo m94/hi m99 delta_DE 0.5468113653656221); Model-F unchanged; D16 official root absent/blank; no fit/prediction/D16/decoder/route.
- Review [repo-observed]: batch-end review `D17-A2-REVIEW` = `EVIDENCE_ACCESS: VERIFIED` / PASS_WITH_FINDINGS, no blocker; non-blocking only (N1 trace early-stop wording; N2 manifest.command A1-root path by verifier-equality design — do not "fix" without packet). Full record in `docs/research_cycles/V72P2D17-DESCALING/EXPLORATION_LOG.md`.
- Lifecycle [decision]: terminal `D17_DE_R2_COMPLETE_REVIEWED_AWAITING_SCALING_FIT_DECISION`; evidence-only, no fit/prediction/route acceptance; A1+A2 grants consumed; no second run/retry/repair under A2 grant.
- Boundary [decision]: synthetic current-channel DE diagnostic only; no fit/D16-prediction/D16/decoder/route/FER/leakage/SKR/qualification/promotion/real-data/D7-H claim. Next gate is scaling-fit decision under separate authorization only.
## 2026-09-15 D17 scaling-fit A3 complete + VERIFIED PASS_WITH_FINDINGS batch-end review (predictions frozen, D16 unauthorized)
- Evidence [repo-observed]: single authorized `--scaling-fit --execution-authorized` run in fresh root `workspace/d17_finite_scaling_fit_5b6d71c8-9e42-4e64-b1c3-73a1f20d8e95` (8 files, hashes match); EXIT 0, 13:16:04–13:20:19Z; wall 255.08/300, RSS ~0.097GiB<2GiB, violations []; DE/decoder/CAL/VAL 0; 96 clusters reconciled (L045 48 / L055 30 / L2 18); brackets literal-exact DE_BRACKET all three; fits L045 one-param α=14.5378 [10.0,21.752] (two-param unidentifiable→downgrade) / L055 two-param α=4.5973 [3.1623,5.6234] β=-1.075 [-1.5,-0.575] / L2 one-param α=5.0845 [3.4974,6.8786]; backoffs diagnostic only; 3 D16 outcome-BLANK predictions frozen (L045 p0.8516 [0.6157,0.9744]; L055 p0.9616 [0.8899,0.9955]; L2 p0.3121 [0.0,0.5]); D16 root absent pre-write; verifier 96/0 PASS; grant consumed; no retry/tuning; no commit/push.
- Review [repo-observed]: batch-end review `D17-A3-REVIEW` = `EVIDENCE_ACCESS: VERIFIED` / PASS_WITH_FINDINGS, no blocker; non-blocking only N1 cmdlog float-display / N2 never-revise literal-key / N3 L045 LORO sensitivity (disclosed, wider union used). Full record in `docs/research_cycles/V72P2D17-DESCALING/EXPLORATION_LOG.md`.
- Lifecycle [decision]: terminal `D17_SCALING_FIT_COMPLETE_PREDICTIONS_FROZEN_AWAITING_D16_AUTHORIZATION`; evidence-only, no D16/fit-claim/route acceptance; A3 grant consumed; no second completion/rerun.
- Boundary [decision]: synthetic scaling-fit + frozen-prediction diagnostic only; no D16 execution/decoder/route/FER/leakage/SKR/qualification/promotion/real-data/D7-H claim. Next gate is D16 authorization (separate) only.
## 2026-09-15 D16 held-out scaling validation B1 complete + VERIFIED PASS batch-end review (partial falsification, evidence-only)
- Evidence [repo-observed]: single authorized 96-call run EXIT 0; exact total 61 = syndrome 61, undetected 0 (L045 25/32 obs 0.78125 [7,6,7,5]; L055 27/32 obs 0.84375 [7,7,6,7]; L2-ORACLE 9/32 obs 0.28125 [3,1,2,3]); frozen-band verdicts L045 NOT_FALSIFIED / L055 FALSIFIED (strictly below 0.8899) / L2 NOT_FALSIFIED; predictions predated run by ~33min, byte-identical + all-BLANK (never edited); legacy terminal D16_L2_DEGREE_SIGNAL secondary only; grant consumed; no retry/refit/rerun; no D17-model-change/D7-H/real-data; no commit/push.
- Review [repo-observed]: batch-end review `D16-B1-REVIEW` = `EVIDENCE_ACCESS: VERIFIED` / PASS, no blocking findings. Partial falsification is evidence only (no interpretation). Full record in `docs/research_cycles/V72P2D16-MATCHED-BACKOFF/EXPLORATION_LOG.md` (+ pointer in D17 log).
- Lifecycle [decision]: terminal `D16_HOLDOUT_VALIDATION_COMPLETE_REVIEWED_AWAITING_ROUTE_DECISION`; evidence-only, no route acceptance; grant consumed; no second run.

## 2026-09-15 — D16 held-out route adjudication

- D17 predictions were frozen before D16. D16 observed L045 25/32
  (NOT_FALSIFIED), L055 27/32 (FALSIFIED under the frozen latent-p-band rule),
  and true-conditioned L2-ORACLE 9/32 (NOT_FALSIFIED); predictions stayed
  outcome-blank and immutable.
- Preserve the L055 registered verdict, while recognizing it as a scaling-model
  calibration miss rather than an L1 construction failure. Future held-outs
  should use an observation-level predictive count interval in addition to a
  latent-p confidence band.
- Main route is D18 current-channel L2 ensemble DE, followed by finite L2 graph
  validation if a candidate advances. L1 tuning is paused; D7-H/APP remain
  closed until single-layer L2 reaches its finite operating region.
## 2026-09-15 D18 L2 ensemble DE readiness complete (E01-E08, no execution)
- Readiness [repo-observed]: E01-E08 all PASS per `docs/research_cycles/V72P2D18-L2ENSEMBLE/READINESS_R1.md` + `EXPLORATION_LOG.md`; OpenSpec `openspec/changes/v72p2d18-current-channel-l2-ensemble-de/`; E08 `EVIDENCE_ACCESS: VERIFIED` / `PASS_WITH_FINDINGS` (D17 3 fails environmental). 21 candidates (DV3 control mandatory) + feasibility 105/105 + DV3 baseline 0.5468113653656221; Stage-S 168 (21x{94,104}x4301..04x4000) + Stage-C 320 (32-overlap, 288 new, 456 total); eligibility <=0.5077488653656221 + rank + one winner; terminals incl. BASELINE_DRIFT; seeds 4301..4308 frozen; future root `workspace/d18_l2_ensemble_de_98abed5a-...` absent; budgets <=456/<=16/1800s/300s/2GiB/1-proc; 26/26 tests; PROFILE_ONLY + refusal rc=2; DE/decoder 0.
- Methodology [decision]: L055 FALSIFIED preserved (mild miss 27/32 [7,7,6,7], descriptive tails T(p_lo)=0.273/T(p_hi)=3.3e-07); latent-band vs predictive-interval amendment forward-only, D16 NOT recomputed.
- Lifecycle [decision]: terminal `D18_L2_ENSEMBLE_DE_READY_AWAITING_EXPLICIT_AUTHORIZATION`; grants no execution; predecessor D16 route adjudication immutable (pause-L1/optimize-L2). Future sweep EXPLORE (<=456 calls).
- Boundary [decision]: synthetic current-channel L2 ensemble DE diagnostic only; sweep unauthorized; no route/FER/leakage/SKR/qualification/promotion/real-data/D7-H claim; no commit/push (E09 scope: triage + entry only).
- Refs: `docs/research_cycles/V72P2D18-L2ENSEMBLE/` (being created in parallel); OpenSpec `openspec/changes/v72p2d18-current-channel-l2-ensemble-de/`.
## 2026-09-15 D18 L2 ensemble DE Sweep A1 complete + VERIFIED PASS_WITH_FINDINGS batch-end review (winner `lam_d2_0.20_d3_0.80`, evidence-only)
- Evidence [repo-observed]: single authorized one-shot `--de-sweep --execution-authorized` run in fresh root `workspace/d18_l2_ensemble_de_98abed5a-af4f-4780-9e83-54cccba28901` (6 files, sha256 match: manifest 50f5fd96…, de_plan 92039219…, de_records 7b8abea9…, de_traces a7ecbadf…, summary 293fcc47…, command_log 47e0ac65…); EXIT 0, 15:50:36–15:58:27Z; S 168 + C-new 288 = 456/456 unique (32 Stage-S overlaps reused, never rerun), setup 4/16, wall 466.36/1800, per-call-max 2.815/300, RSS 286371840<2GiB, violations []; Stage-S rank selected `[0.15, 0.20, 0.25, DV3]` (six-way tie S94=S104=4 + worst-H 3.089393128245247e-296 broken by pre-registered id ASC; rank-4..6 0.30/0.35/0.40 screen-indistinguishable = N4); selected brackets lo89/hi94 h=0.09765625 `delta_DE=0.35149886536562214` `[DE_BRACKET]`; DV3 lo94/hi99 `delta_DE=0.5468113653656221` (`baseline_drift=false`); 3 eligible; winner `lam_d2_0.20_d3_0.80` (id-ASC tie-break; 0.15 loses max_dc 5); terminal `D18_L2_DE_SELECT_ONE_ENSEMBLE`; read-only `--verify` PASS/0.
- Review [repo-observed]: batch-end review `D18-A1-REVIEW` `EVIDENCE_ACCESS: VERIFIED` / `PASS_WITH_FINDINGS`, no blocker; non-blocking N1 RSS placeholder + setup constant, N2 saturation fixed point, N3 thin `command_log.txt`, N4 rank-4..6 screen-indistinguishable (main thread owns interpretation). Full record in `docs/research_cycles/V72P2D18-L2ENSEMBLE/EXPLORATION_LOG.md`.
- Lifecycle [decision]: terminal `D18_L2_DE_SWEEP_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`; evidence-only (no route/optimality acceptance); one-shot grant consumed; no second run/retry/resume/repair/manual substitution; N4 interpretation and the next route gate (finite L2 validation if a candidate advances, per D16 route adjudication) belong to the main thread. No OpenSpec behavior delta (sweep matched the frozen spec).
- Boundary [decision]: synthetic current-channel L2 ensemble DE diagnostic only; no finite L2/decoder/APP/L1/real-data/FER/leakage/SKR/qualification/promotion/D7-H claim; no commit/push.
- Refs: `docs/research_cycles/V72P2D18-L2ENSEMBLE/EXPLORATION_LOG.md`; root above; OpenSpec `openspec/changes/v72p2d18-current-channel-l2-ensemble-de/`; packet `.workbuddy/tasks/D18_L2_ENSEMBLE_DE_SWEEP_A1_TASK_PACKET.md`.

## 2026-09-16 — D18 L2 DE selection and D19 route

- D18 completed 456 unique current-channel true-conditioned L2 DE calls.
  L015/L020/L025 all bracketed at `delta_DE=0.35149886536562214`; DV3 remained
  at `0.5468113653656221`. The frozen complexity/ID rank selected L020; this is
  candidate selection, not ensemble optimality.
- Next route is D19 paired finite L2 validation of L020 versus DV3 at m94/n128,
  with six fresh graphs/eight shared blocks and conditional n256 confirmation.
  L1 tuning, APP, and D7-H remain paused.
## 2026-09-16 D19 L2 finite-ensemble validation readiness STOP (frozen-seed x constructor-trajectory BLOCKED, no execution)
- Readiness [repo-observed]: STOP on frozen n256 DV3 graph seed 2026094408 deterministically failing construction (`no eligible check placement at variable 255 socket 2`) with accepted D10-R2 constructor; 23/24 graphs admit (n128 12/12); reviewer `D19-BLOCKER-REVIEW` `EVIDENCE_ACCESS: VERIFIED` / PASS confirmed frozen-seed x constructor-trajectory STOP (not table/implementation defect; arithmetic + sockets verified; five identical-multiset siblings admit); no replacement/search applied (forbidden); D19 module/runner/tests (33/33) + PROFILE_ONLY (24 attempted/23 admitted/192 plan/0 calls/root absent) + refusal rc2 exist as untracked-additive artifacts; F08 frozen root `workspace/d19_l2_finite_ensemble_5f2b8c1d-7a3e-4f90-b6d4-8e1a2c3d4f5a6b` absent; zero decoder/DE calls.
- Lifecycle [decision]: NO ready terminal issued (`D19_L2_FINITE_ENSEMBLE_READY_AWAITING_EXPLICIT_AUTHORIZATION` must NOT be issued under frozen seeds); terminal `D19_L2_FINITE_ENGINEERING_BLOCKED` pending formal acceptance; ONE decision pending: amend frozen n256 DV3 seed set under new packet amendment (fresh disjointness + 24-graph re-profile + re-review) OR formally accept BLOCKED as D19 outcome; no commit/push; no D19 execution.
- Boundary [decision]: synthetic finite L2 readiness only; no FER/leakage/SKR/route/qualification/promotion/real-data/D7-H claim.
- Refs: `docs/research_cycles/V72P2D19-L2FINITE/` (parallel creation); OpenSpec `openspec/changes/v72p2d19-l2-finite-ensemble-validation/`; packet `.workbuddy/tasks/D19_L2_FINITE_ENSEMBLE_VALIDATION_READINESS_R1_TASK_PACKET.md`.
## 2026-09-18 D19 L2 finite-ensemble execution terminal AMBIGUOUS (no thresholds, no budgets, no seed detail, no claims)
- Evidence [repo-observed]: terminal `D19_L2_FINITE_AMBIGUOUS` 2026-09-18 — n128 96/96 calls, M=19/48 exact-only AMBIGUOUS, undetected=0 isolated, n256 0 calls (conditional n256-iff-POSITIVE closed), CAL Model-F input only; evidence root `workspace/d19_l2_finite_ensemble_5f2b8c1d-7a3e-4f90-b6d4-8e1a2c3d4f5a6b` + log `docs/research_cycles/V72P2D19-L2FINITE/EXPLORATION_LOG.md`.
- Review [repo-observed]: batch-end reviewer-go PASS B1-B7.
- Lifecycle [decision]: terminal `D19_L2_FINITE_AMBIGUOUS`; grant closed; no rerun.
- Boundary [decision]: synthetic finite L2 diagnostic only; no FER/leakage/SKR/route/qualification/promotion/real-data/D7-H claim.
## 2026-09-18 G6-DECIDE-R1 terminal + Pre-EXECUTE precedent
G6-DECIDE-R1 V72P3G6-REAL-CONFIRM: NO_USEFUL_RECOVERY on real P-2M-tail 2093..2156 L020-n128 (128/128 fail, net 0) — terminal; D19 AMBIGUOUS (synthetic) retained, not superseded.
Pre-EXECUTE precedent (RULING-1..3): P1 scoped-to-cycle-files only; closed-cycle tests don't gate new cycle; explicit grant attestation in cycle doc satisfies P6.
## 2026-09-18 L2 campaign close-outs (R16 correction → R22)
D-R8-01 G7-STOP: L2-positive-net STOP on surveyed regimes (Â-free m/n contradiction: net needs m/n<0.5, convergence needs m/n>=0.63-0.72); adaptive lift parked/characterized (R11 ADAPTIVE_LIFT 87-vs-1 → R12 CONFIRMED-GENERALIZING 79/128, net-negative both); escapes quantified (2.5x quieter regime OR 2x-better code); R13 PIVOT (0/90 near-miss); R14 NO-POSITIVE-REGIME (means 72.7/77.6/90.1); SKR blocked until net-positive demonstrated; authority: docs/research_cycles/V72P3G7-ROUTE/ROUTE_MEMO.md + V72P3R14-SURVEY/EXPLORATION_LOG.md.
R16-CORRECTION + G7-WITHDRAWN (2026-09-18): n-based net_secret_bits added, old k-based frozen; recomputed nets R9 −71552 / R11 −27752 / R12 −33232; G7-STOP central bound WITHDRAWN (k double-charge), route ALIVE as efficiency battle; all prior terminals unchanged.
G8-S0 HELD (2026-09-18): H_A 4.2867/3.2227 incl D17-6dp proof; H_B worst 3.6925 / H_C worst 3.6869; SANITY_STOP overridden; k-based 1.023/1.875 gate SUPERSEDED, n-based bar H<3.0; HELD pending R18 anchor comparability.
R18 V-INCOMPATIBLE-CONDITIONING (2026-09-18): units OK; V25 0.81 needs per-source ±1-concentrated data + richer conditioning, untransferable; F1-marginal capped 3.69 measured; S1-marginal REJECTED; route F3-conditional/F2-control via R19.
R19 session-recorded (no cycle dir): conditioning +0.02 bits (INSUFFICIENT vs 2.0 bar); λ re-select ≈137 (HONEST, table unlearnable confirmed); F3-cheap dead.
R17 NO-GAIN (2026-09-18): warm 27 vs cold 87; strict subset 0/60/0; warm-start family DEAD as mechanism (carried beliefs trap decoder).
R20 PRIOR-HELPS + P9-fix (2026-09-18): uniform 0/128 resid-97.0 vs modelF 1/128; paired mean Δ+10.64, modelF-better 123/128; P9 sign-typo corrected (improved≡Δ>0); prior line REOPENED → S1 justified.
S1 SHIFT-HELPS (2026-09-18): shift 2/128, paired mean Δ−15.0, 127/128 improved; eps frozen 1e-4 via CV table; prior ladder PRODUCTIVE: uniform 0 → modelF 1 → shift 2.
R21 NO-DAMP-GAIN (2026-09-18): 0.5/0.8 trajectories outcome-identical to S1 1.0 (only accept-iters + 1-2 residual wiggles); decoder-hyperparameter line CLOSED: iters-300 dead, warm harmful, damping inert.
R22 PREDICTOR-DEAD (2026-09-18): best lost-free abort rule saves 480–800 bits vs 1500 bar; residuals fully overlapped; abort line CLOSED pending new signals.

## 2026-09-19 V80 S1 HOLD terminal (F1/F2/F3 blocking; S2 barred; docs-only, no execution)
- Lifecycle [decision]: terminal `V80_S1_HOLD` 2026-09-19 — 禁止解释当前S1臂输出, 禁止flip/S2/S3推进, 直到F1/F2/F3修复 + D5-delta独立复审 + 新授权重跑; S2 barred; PRIMARY已消耗420 slots不可回收 (rerun = new spend); SECONDARY现场保留 (old root `workspace/s1_mcde_07723233-…` retained, never overwritten).
- Evidence [repo-observed, review核实类, 非语义证据]: F1 PRIMARY臂无效 — 0/420 DE收敛, L2层可行上限 `1 − H_L2/5 = 0.83862`, 执行网格rate 0.879–0.906全在其上, 正确层内映射 `m2 = ceil(f·H_L2·n/5)`, f=1.3 ⇒ m2≈54; F2门度量不筛`converged` (runner 866–876), PRIMARY伪pass 0.7506<1违Slepian–Wolf界, SECONDARY max≈1.454 (m=31) > 1.15注定fail, `f_row`纯算术 (line 538), flip跨单位比较; F3 fake套件 (45+6独立复跑绿) 钉不住语义 (层速率映射/门-收敛语义/f≥1朝向均无pin). SciVerse生效 / 工业论文核实 (Mitra arXiv:2305.00956 via ar5iv; IEEE-11440984 paywalled S2S-429 deferred) / 45+6复跑绿均属review核实类, 不作语义证据.
- Records [gap]: 记录链缺口 decision-log止于4438 ("S1-delta review FAIL blocks execution"); 缺D5-rework复审条目、S1授权条目、开工条目、PRIMARY完成条目; `S1_READINESS.md`头仍NOT accepted vs post-4438 addenda skew — 需执行会话对账. Live snapshot指针 (复审时刻采样, 非裁决): PRIMARY 420/420 · SECONDARY 44/180 · SETUP 12 · TOTAL 476/612; `resume.next_arm = SECONDARY`; manifest config-hash一致; `verify.ok=true`仅hash一致+门重算一致, 非门裁决.
- Boundary [decision]: EXPLORE docs-only; no execution/authorization/gate verdict; branch `formal-ir-v72p1-addendum-clean` (do NOT switch/commit/push); no SKR/qualification/promotion/publication claim; no S1 numbers interpretation. 下一步: F1-ACC (m2=ceil(41.31f), sweep≈44–60) / F2-ACC (∃-converged f≤1.15, f<1 SW-violation pin, flip跨单位禁止, verify.ok非裁决标注) / F3-ACC (a/b/c三pin各red-green) + G-D5R (独立D5-delta复审) + G-RERUN (fresh grant + Pre-EXECUTE + 新root UUID).
- Refs: `docs/research_cycles/V80-NBLDPC-JAN21/S1_HOLD_20260919.md` + `S1_FIX_PLAN_20260919.md`; decision-log HOLD entry 2026-09-19 (already recorded, no duplicate).
