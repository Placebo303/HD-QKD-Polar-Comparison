# D14 Scientific Validity Reset — EXPLORE log (append-only)

- Authority: `.workbuddy/tasks/D14_SCIENTIFIC_VALIDITY_RESET_R1_TASK_PACKET.md` (§1–§9, sole authority; §9 return contract).
- Track: `EXPLORE` (packet §1; P/C implementation and the no-decoder R run require no execution gate).
- Repo: `/mnt/d/Code/HD-QKD_Polar_Comparison`, branch `formal-ir-v72p1-addendum-clean` (do not switch; no commit/push in this call).
- This is the single append-only log root for D14. Detail record: `READINESS_R1.md` in this directory.
- Predecessor pointer: `docs/research_cycles/V72P2D13-L055-LADDER/EXPLORATION_LOG.md` (D13 accepted `D13_RESULT_ACCEPTED_MODEST_CLOSE_LADDER`; closes ladder, routes to prior/rate calibration).
- This call: documentation-only close (two new record files in this directory, one pointer append to the D13 log, D14 OpenSpec `tasks.md` checkbox update). No code, no execution, no decoder/DE/real-data calls, no staging/commits, no push.

## 2026-09-14 — D14 close R1 (no execution)

### Authorization boundary

- This call performed no code edit, no D14 execution, no decoder or scientific call, no root creation, no commit, no push.
- The frozen N discriminator batch remains unauthorized. It requires a separate explicit batch grant. No authorization was granted by readiness or by D14-FINAL.
- No-execution-authorized statement: **no D14 execution is authorized by this close; the N root remains absent and the N command remains a frozen unauthorized string.**

### S — preserve the milestone safely (trusted VERIFIED)

- 4 local commits on `278fdf07`: `55ab6de` (1 file), `5f4b121` (20 files), `43308b8` (48 files), `ccc33eb` (manifest); 70 paths total, 0 workspace/results/outputs.
- No-push verified: 4 SHAs absent from remotes; origin at `d98db0e`; ahead-142 is pre-existing divergence.
- Group1 deferred + group5 STOPPED still uncommitted (packet §3 STOP = compliance).
- CORRECTED overlap sizes: decision-log hunk `@@ -3487,3 +4057,97` (97 lines, not 74) + extra `@@ -23,6 +23,547` and `@@ -3424,6 +3965,35` hunks; memory hunk `@@ -3499,3 +3749,99` (99, not 89) + extra `@@ -1,9 +1,218`.
- Content-diff is 23 files; 1881 M are CRLF/stat false-positives.
- Verdict: S PASS.

### P — correct production prior selection (trusted VERIFIED)

- 5 hunks (+7/-5) at `:2449`/`:2485`/`:2998`/`:3013`/`:3036` (line shift from group2 delta explained, symbol-verified); signatures/bodies untouched; static greps clean; D14P 4/4 rerun by reviewer.
- Verdict: P PASS.

### C — immutable G2/X4 corrigendum (trusted VERIFIED)

- Corrigendum exists (3059 B, VR-C-03 a–e verbatim); G1 §10 +12/-0 append-only; OPERATOR_RETURN §10 present; root re-hashed match (`4407e667…`/`ca93308a…`/`6bd8d5b…`/`31a7f9f4…`); grade literals present; cycle-state additive.
- Finding (non-blocking): C appends sit on mixed EOF hunks (content-separable via D14 headers, hunk-inseparable) — future S3 splits by content headers.
- Verdict: C PASS_WITH_FINDINGS.

### R — symmetric rate-calibration audit (trusted VERIFIED)

- Imports verified; own entropy recompute joint `7.509440314835753` / L1 `4.286720430201376` / L2 `3.222719884634378` (Δ≤1.8e-15) → 4dp confirmed; legacy 9.9996/5.0/5.0 story confirmed; frozen rows spot-match.
- Triple mismatch retained (+0.003/+0.001/+0.003, never copied; hypothesis numbers absent from module).
- Audit root 9/9; per-block joins (D12 24/432/221/0, D11 120/720/0 undetected); separation stated; decoder 0, wall 0.7 s, RSS 175 MB; R-audit 10/10 rerun.
- Verdict: R PASS_WITH_FINDINGS.
- R corrective-repair disclosure (recorded HERE; audit root stays frozen; do NOT edit `workspace/v72p2d14_rate_audit/`): R operator run#1 crashed pre-write on sorted-of-dicts; run#2 exposed multiplicity bug in D11 quantile + unlabeled P0/G1 row duplication + width-confounded D12 bins; fixed via stage column, n_symbols/n_calls split, `expand_cell_pairs` helper, per-width terciles; buggy fresh scratch removed pre-review; single corrective rerun; scientific inputs/seeds/thresholds/data roles/hypothesis unchanged. Adjudication: NON-BLOCKING CONDITIONAL on recording this disclosure.

### N — freeze the next experiment (trusted VERIFIED)

- Prereg exists (203 lines), Choice A arithmetic confirmed (110 rows, 550 disclosed, 1.00237), seeds absent, root absent, runner correctly absent, budgets within ceilings, thresholds + no-D7-H.
- Verdict: N PASS.

### D14-FINAL verdict (trusted VERIFIED, not rerun)

- `EVIDENCE_ACCESS: VERIFIED`, VERDICT `PASS_WITH_FINDINGS`, BLOCKING none.
- Group5-terminal adjudication: YES terminal issues with group5 STOPPED (§3 STOP = compliance; §9 reporting satisfied by listing commits + exclusions).
- Corrective-rerun adjudication: NON-BLOCKING CONDITIONAL on recording the repair disclosure (recorded in R section above).
- Note for future S: OPERATOR_RETURN + `V72P2D7-ROOT-CAUSE-RESET/` dir untracked (proven by content, not git diff).
- Recommendation: `D14_VALIDITY_RESET_COMPLETE_CALIBRATED_BATCH_READY_AWAITING_EXPLICIT_AUTHORIZATION`.

### Terminal

`D14_VALIDITY_RESET_COMPLETE_CALIBRATED_BATCH_READY_AWAITING_EXPLICIT_AUTHORIZATION` — S/P/C/R/N complete per D14-FINAL; frozen N batch still unauthorized; no route-closure, FER/SKR/qualification/promotion/publication claim.

### Claim boundary

- Synthetic diagnostic only. This close routes the next investment (L1 construction vs L2 degree design) and makes no FER, leakage, SKR, real-data, qualification, promotion, optimality, or route-closure claim.
- D7-H NOT revived. Real-data, formal qualification, route-closing decisions and publication claims remain DECIDE-gated.

## 2026-09-14 — D14N readiness R1 close (no execution)

- Authority: `.workbuddy/tasks/D14N_CALIBRATED_DISCRIMINATOR_IMPLEMENTATION_R1_TASK_PACKET.md`
  (§6 readiness record + D14 log append); D14N-R210 review result (trusted
  VERIFIED, not rerun). Track: `EXPLORE` (implementation/readiness now; future
  288-call batch `EXPLORE`).
- This call: documentation-only close (new record
  `D14N_READINESS_R1.md` in this directory + this append + D14N OpenSpec
  `tasks.md` N202–N210 checkbox update). No code, no execution, no
  decoder/scientific calls (0), no root creation, no staging/commits, no push.
- STOP-then-amend narrative: operator pre-code STOP with zero writes (frozen L1
  check-allocation strings `2^41+3^77` / `2^53+3^65` sum to m=118, not frozen
  m_L1=110) → main-thread adjudication A (variable side STANDS: L045 71/57/E313,
  L055 83/45/E301; check side re-derived at m=110: `2^17+3^93` / `2^29+3^81`;
  option-B m=118 rejected: 1.07527 vs 1.00237 destroys Choice A) → planner
  recompute with full D9-rule arithmetic (design §8 CONFIRMED) → N202–N209
  retry on amended freeze green; prereg file untouched (retain + supersede).
- N210 verdict (trusted VERIFIED): VERDICT PASS, BLOCKING none — amended cells
  exact-rational recompute; 18/18 admitted (A=1×6 independent double-build, 0
  replacements); 288-plan, gates, reuse, refusal (live RC=2 pre-write/bind/load),
  budgets, root absence, zero production calls confirmed; 22/22 focused tests on
  reviewer-own basetemp; D11/D12 trusted per trust rule; APP-source FLAG carried
  as execution-gating (not readiness-blocking); non-blocking: proposal.md
  pre-amendment strings, additive-untracked dirty worktree.
- Terminal: `D14N_CALIBRATED_DISCRIMINATOR_READY_AWAITING_EXPLICIT_AUTHORIZATION`
  — N201–N210 pass, exact future command frozen, authorization false, result
  root absent, decoder/scientific calls 0.
- No-execution-authorized statement: **no D14N execution is authorized by this
  close; the N root remains absent and the N command remains a frozen
  unauthorized string.** Next gate: paired A1 execution packet after main-thread
  readiness acceptance (Pre-EXECUTE: APP-source freeze, d5-tree reconfirm).
- 2026-09-15 main-thread acceptance audit: **BLOCKED**. The persisted runner
  refuses unauthorized `--n14-batch` correctly, but an authorized invocation
  reaches an unconditional `SystemExit("production --n14-batch adapters ...
  belong to a later authorized change")`; it never binds adapters, dispatches
  the 288 records, or writes a result. Therefore
  `D14N_CALIBRATED_DISCRIMINATOR_READY_AWAITING_EXPLICIT_AUTHORIZATION` is not
  accepted as operational readiness. N210 did not exercise the authorized
  true branch. No scientific execution or root write occurred in this audit.
  Next gate: minimal R2 authorized-path completion with fake-only true-branch
  test and independent re-review; all scientific rows/seeds/arms/gates/budgets
  remain frozen.

## 2026-09-14 — D14N R2 authorized-path completion close (docs only)

- Authority: `.workbuddy/tasks/D14N_AUTHORIZED_PATH_COMPLETION_R2_TASK_PACKET.md`
  (§6 return); D14N-R207 (EVIDENCE_ACCESS VERIFIED, PASS_WITH_FINDINGS,
  BLOCKING none — trusted, not rerun). Track: documentation-only (no code, no
  execution, no decoder/scientific calls, no root creation, no commits/push).
- R201 freeze + R202–R206 delta: authorized `SystemExit` replaced by exactly
  one `run_authorized_batch` + one `write_batch_root`; refusal stays
  pre-root/bind/load; narrow reuse binder; 288-plan-first orchestrator;
  fake 288/288 scratch test + 4 failure tests; R206 inspect-only probe.
- R207 (trusted): NO-SYSTEMEXIT PASS; FAKE-288 PASS (288 calls, 144/144,
  SETUP=32, ROWS==PLAN, N_ROUTE_SCALE_VALIDATION); VERIFIER PASS (288/0);
  ROOT-ABSENT PASS; ZERO-PRODUCTION PASS (V35_ABSENT, binder 0, probe 0/0);
  REFUSAL PASS (rc=2 pre-load); ADAPTERS 14/14; AMENDMENT-INTACT;
  TEST_RERUN 7/7 + calibrated 22/22 trusted. Non-blocking: (F1) d5 7+/5−
  hunks EXCLUDED from R2 commit; (F2) R202–R207 boxes flipped here;
  (F3) flag-free manifest precedent explicit, accepted. Detail:
  `D14N_READINESS_R1.md` §7.
- Terminal: `D14N_R2_EXECUTION_PATH_READY_AWAITING_EXPLICIT_AUTHORIZATION` —
  path ready, batch NOT authorized. Pre-EXECUTE carried: APP-source frozen
  L055; d5-tree reconfirm carried. No-execution-authorized statement:
  **no D14N execution is authorized by this close.**
- 2026-09-15 main-thread R2 acceptance: accepted independent review
  `EVIDENCE_ACCESS: VERIFIED` / `PASS_WITH_FINDINGS`, BLOCKING none. The prior
  authorized-branch blocker is resolved: CLI now calls exactly one
  `run_authorized_batch` and one `write_batch_root`; fake true-branch executed
  288/288 records with setup=32 and verifier PASS while production calls stayed
  zero. Accepted terminal:
  `D14N_R2_EXECUTION_PATH_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`. This grants
  no execution. The real root remains absent; D7-H and route selection remain
  closed.

## 2026-09-14 — D14N Batch A1 pre-dispatch (AUTHORIZED once)

- Authority: A1 packet + this-turn user grant (D14N_CALIBRATED_DISCRIMINATOR_BATCH_A1
  once; root workspace/v72p2d14_discriminator/20260914_r1; 288 calls / 32 setup /
  1800 s / 120 s / RSS<2GiB / 1 CPU; APP←L055). Track EXPLORE, n128 synthetic only.
- C1 R2-marker+review: PASS. `D14N_R2_EXECUTION_PATH_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`
  in decision-log.md:4228-4229 + MEMORY:3889 + this log:139; R207 VERIFIED
  PASS_WITH_FINDINGS, BLOCKING none (this log:114,121-128; decision-log.md:4217).
- C2 branch+scope: PASS. branch=formal-ir-v72p1-addendum-clean; HEAD=3f874bb7;
  merge-base --is-ancestor 3f874bb HEAD → YES. Scoped code paths clean
  (runner/N14 module/2 test files: zero diff). Uncommitted dirt preserved, no repair:
  D14 log + proposal.md carry post-commit A1/R2 supersede notes (design §9.3-authorized
  annotation); d5 mother carries the 7+/5− P-wiring hunks (R2-F1, excluded by design);
  broad pre-existing worktree dirt untouched.
- C3 root+Model-F: PASS. Future root ABSENT (ls: no such directory).
  Model-F present: cal_only=true, decoder_calls=0, p0_calls=0 (summary.json);
  npz sha256=38e4bfba74d06234af22e931d43d00e51e4a3c61825c59f02c1ed00b6280d345
  matches V72P2D10 log record (matches prior); mtimes 2026-09-07 (pre-existing).
- C4 D5 wiring: PASS, no drift. run_p0_cost_synthetic:2998 + run_g1_synthetic:3013 +
  run_g2_synthetic:3036 each call prepare_model_f_prior_candidate exactly once;
  zero legacy prepare_model_f_prior calls in bodies 2993-3042 (LEGACY_ZERO);
  diff is exactly the carried 7+/5− hunks (3 call swaps + 2 docstrings).
- C5 APP source+adapters: PASS. APP_SOURCE_PROFILE='L055' (runner:64) with fail-closed
  guards (runner:309-312 orchestrator, :824-825 verifier). Inspect-only probe:
  6 adapters + 4 transfer_parts resolve, all signatures valid;
  decode_fn=comparison_bench.formal_ir.v35_algorithm_development.decode_row_layered_fftqspa;
  app_source_profile='L055'; future root absent; DECODER_CALLS=0 LOADS=0 (no invocation).
- C6 PROFILE_ONLY: PASS (rc=0; 3 side-effect-free stdout runs — first two truncated by
  caller pipes, third full-capture to /tmp/opencode; no root write, decoder 0 throughout).
  admitted=18/18 (A1-A6 true, status ok, A6 replay true); L045 6/6 identical
  E313 vh{2:71,3:57} ch{2:17,3:93} m110; L055 6/6 identical E301 vh{2:83,3:45}
  ch{2:29,3:81} m110; L2 6/6 identical E384 vh{3:128} ch{3:32,4:72} m104;
  replacements=0, frozen_seed_failures=[], plan_calls=288 (72×4), decoder_calls=0,
  future_root_absent=true; setup structural 18+12+2=32; root still absent after.
- C7 refusal: PASS. Unauthorized --n14-batch vs /tmp/opencode scratch → RC=2,
  refusal text pre-root/bind/load; scratch target never created (absent after).
- C8 compile+tests: PASS. py_compile OK (runner, N14 module, 2 test files).
  29/29 passed (authorized-path 7/7 + calibrated 22/22), -p no:cacheprovider
  -o addopts=, .venv/bin/python. Note: TMPDIR under workspace/ (DrvFs) broke pytest
  capture (FileNotFoundError); used fresh /tmp/opencode/d14n_check8 instead;
  workspace/d14n_check8_basement rmdir'd (no repo pollution). D11/D12 evidence
  trusted (no focused conflict).
- C9 frozen contract: PASS. ARMS=(L045,L055,L2_APP,L2_ORACLE); seeds
  L1 2026093401..06 / L2 2026093501..06 / blocks 2026093601..12; ceilings 288/32;
  WALL 1800.0 / PERCALL 120.0 / RSS ceiling 2147483648 enforced strict (rss>= → breach);
  L1_MIN_EXACT=18, GE2_MIN=5, ORACLE_MIN=18, JOINT_MIN=9; six TERMINALS exact +
  first-match order eng→L1→L2deg→transfer→scale→ambiguous (module:526-549);
  MODEL_F_ROOT frozen; no prior consumption (root absent, no batch content).
- PRE-DISPATCH: 9/9 PASS. Grant consumed at command start (next entry).

## 2026-09-14 — D14N Batch A1 run evidence (AUTHORIZED once, consumed)

- Actual command (with --execution-authorized; manifest keeps flag-free identity
  `... --n14-batch --model-f-root ... --out-root ...` per R2-F3 precedent):
  `.venv/bin/python scripts/v72p2d14_discriminator_development.py --n14-batch --execution-authorized --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/v72p2d14_discriminator/20260914_r1`
- EXIT=0. START_UTC=2026-09-14T18:52:43Z, END_UTC=2026-09-14T18:55:40Z.
  Runner wall_s=170.990 (≤1800 PASS); shell WALL_S=177.
- CALLS: scientific 288/288 (= ceiling, no breach); SETUP 32/32 (= ceiling:
  18 graphs + 12 blocks + 2 plan/manifest). PER-CALL max=0.928 s (≤120 PASS;
  min 0.0386, mean 0.592). PEAK RSS=137207808 B (<2147483648 PASS).
  budget_violations=[], engineering_reason="". One foreground CPU process.
  No retry/resume/repair/seed-search/tuning/adaptive (all false in summary).
- ADMISSION: 18/18 (graph_records.csv; PROFILE_ONLY + command_log agree:
  `built 18 graphs admitted=18`). Amended tables in manifest match A1
  (L045 71/57/E313 2^17+3^93; L055 83/45/E301 2^29+3^81 m110; L2 E384
  vh{3:128} ch{3:32,4:72} m104).
- ORDER (recomputed from decoder_records.csv, 288 rows): call_idx 0..287 exact;
  arms L045×72 → L055×72 → L2_APP×72 → L2_ORACLE×72; frozen
  L1/L2/block seeds paired ascending per arm; batch_id uniform
  `d14-discriminator-v1`; status 80 converged_exact + 208 converged_no_syndrome;
  crash=False ×288; errors none; residual/nonfinite: none observed.
- Per-arm/per-graph pools (exact / syndrome / undetected SEPARATE):
  L045 exact=3 syndrome=3 undet=0, per-pair [1,0,0,0,1,1];
  L055 exact=7 syndrome=7 undet=0, per-pair [1,0,1,2,2,1];
  L2_APP exact=7 source=7 target=7 joint=7 syndrome=7 undet=0,
  joint per-pair [1,0,1,2,2,1];
  L2_ORACLE exact=63 syndrome=63 undet=0, per-pair [11,11,10,9,12,10].
  Totals: exact=80, syndrome_valid=80, undetected=0 (never merged).
  Paired L1 discordance (descriptive): 72 cells, concordant 68,
  challenger_only 4, reference_only 0, trials 4.
- APP SOURCE: L055 (summary + manifest `app_source_profile: L055`; command_log
  `composed L055-fed transfer/oracle closures`, `derived L055-fed APP sources
  count=72`). PROVENANCE: non-oracle 216/216 CHECK_UPDATED (L045/L055/L2_APP
  72 each; zero uniform/prior-only fallback); oracle 72/72 ORACLE, graded=False
  (ungraded, excluded from gates ✓).
- PREDICATES (recomputed): L1-ADEQUATE=FALSE (L055 7<18; graphs≥2 only 2/6 <5);
  ORACLE-ADEQUATE=TRUE (63≥18); L2-JOINT-GOOD=FALSE (7<9).
  TERMINAL stored=N_ROUTE_L1_CONSTRUCTION = first-match rule 2 ✓ consistent.
  Evidence only; authorizes no route, no D7-H, no claims.
- ROOT `workspace/v72p2d14_discriminator/20260914_r1/` (6 files, sha256):
  arm_summary.csv 4542eddb…9478cb0; command_log.txt ae07744e…413e29;
  decoder_records.csv 06c2cff7…33ccdd28b; graph_records.csv 8a4d7ba5…93cf8fe74;
  manifest.json 69b0351f…dafa4108; summary.json 2c2d9b26…4993deb91a.
- VERIFIER (read-only --verify): `VERIFY checked_calls=288 violations=0 /
  VERIFY PASS`, rc=0.
- Model-F post-run immutable: npz sha256 38e4bfba…6280d345 unchanged,
  mtimes 2026-09-07 unchanged.
- GRANT_CONSUMED (single execution; no rerun/retry/repair performed).
  No commit/push (none requested). Batch-end independent review PENDING —
  return NOT YET `D14N_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`.

## 2026-09-14 — D14N Batch A1 batch-end review (VERIFIED PASS)

- REVIEW_ID: D14N-B1-REVIEW. EVIDENCE_ACCESS VERIFIED (direct reads, own
  recounts, own read-only --verify rc=0, Model-F re-hash, branch/HEAD 3f874bb7
  + merge-base ancestor YES). No edits/reruns/root-modification/commit/push.
- AUTHORIZATION PASS: one-shot (operator record with-flag command; manifest
  flag-free identity per explicit precedent; command_log single dispatched=288
  pass; one root; grant consumed once).
- INVENTORY PASS: six files, hashes match
  (4542eddb…/ae07744e…/06c2cff7…/8a4d7ba5…/69b0351f…/2c2d9b26…);
  288 decoder + 18 graph rows.
- ADMISSION PASS: 18/18 (A1-A6 true all rows); amended cells in graph rows +
  manifest (L045 m110/E313, L055 m110/E301, L2 m104/E384;
  2^17+3^93 / 2^29+3^81 / 3^32+4^72).
- IDENTITIES PASS: 288 unique (arm,pair,block); idx 0..287 (L045 0-71 →
  L055 72-143 → APP 144-215 → ORACLE 216-287); frozen seeds; batch_id
  d14-discriminator-v1; setup 18+12+2=32.
- RECOUNTS PASS (own): L045 3/3/0 [1,0,0,0,1,1]; L055 7/7/0 [1,0,1,2,2,1];
  APP 7/7/0 joint 7 [1,0,1,2,2,1] (source=target=7, joint==exact all 72);
  ORACLE 63/63/0 [11,11,10,9,12,10]; totals 80=80, undetected 0,
  mismatches 0; converged_exact 80 + no_syndrome 208; crash 0.
- SOURCE PASS: APP←L055 (manifest/summary/command_log count=72); provenance
  216 CHECK_UPDATED + 72 ORACLE; oracle graded=False excluded;
  joint==L055 vector.
- PREDICATES PASS: L1-ADEQUATE FALSE (7<18; ge2 2/6<5); ORACLE TRUE (63≥18);
  JOINT FALSE (7<9).
- TERMINAL PASS: rule-2 N_ROUTE_L1_CONSTRUCTION; stored matches; frozen
  six-set; discordance 68/4/0 descriptive-only.
- BUDGETS PASS: 288/288, 32/32, wall 170.990/1800, per-call-max 0.928/120
  (mean 0.5916), RSS 137207808<2GiB, 1 proc, violations [] + verifier 0.
- NO-RETRY PASS; VERIFIER OWN PASS (288/0 rc=0); MODEL-F/CLAIM/PATH PASS
  (hash+mtimes unchanged; CAL-only; ceiling intact; no D7-H/real-data).
- TRUST: R207 + 9/9 cited per trust rule (readiness provenance only; batch
  numbers independently recomputed).
- FINDINGS: BLOCKING none; non-blocking suggestion (echo argv+exit into
  command_log.txt in future batches for self-contained one-shot proof).
- VERDICT PASS; recommendation
  D14N_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION; no
  route/D7-H/commit-push.
- Close: grant consumed, no second run, no commit/push, memory triage pending.
- 2026-09-15 main-thread result acceptance: accept the verified 288-call batch
  and literal machine terminal `N_ROUTE_L1_CONSTRUCTION` as correctly computed
  evidence, but do not accept its causal investment inference yet. L1 was run
  at effective disclosure about 1.002 while L2 ORACLE retained about 1.261;
  their recovery rates are not a symmetric layer comparison. At n=128, failure
  near entropy can be a finite-length margin effect rather than a degree-profile
  defect. L055 also remains directionally above L045 (7 vs 3), so the statement
  that its D12 advantage "was a rate artifact" is superseded as too strong.
  Accepted terminal: `D14N_RESULT_ACCEPTED_MARGIN_CONFOUNDED_ROUTE_DEFERRED`.
  Next: D15 paired L1/L2 finite-length margin curve; no D7-H.

## 2026-09-15 — D15 readiness R1 pointer (append-only, no D14 change)

- D15 readiness closed documentation-only: `docs/research_cycles/V72P2D15-MARGIN-CURVE/READINESS_R1.md`
  + `EXPLORATION_LOG.md`; D15 OpenSpec `tasks.md` D1503–D1510 marked [x].
- D15-R1510 (trusted VERIFIED, do not rerun): EVIDENCE_ACCESS VERIFIED, VERDICT
  PASS_WITH_FINDINGS, BLOCKING none; terminal
  `D15_MARGIN_CURVE_READY_AWAITING_EXPLICIT_AUTHORIZATION`.
- No D15 execution authorized; future root absent; decoder/scientific 0; no commit/push.
  D14 record above unchanged.
