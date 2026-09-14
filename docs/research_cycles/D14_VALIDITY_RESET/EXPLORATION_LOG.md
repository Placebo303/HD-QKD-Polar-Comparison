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
