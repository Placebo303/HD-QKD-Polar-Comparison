# D7-D mainline reconciliation review R1 (A08)

Status: `D7_D_MAINLINE_RECONCILIATION_REVIEW_PASS`

- Date: 2026-09-11. Branch `formal-ir-v72p1-addendum-clean`; review HEAD `ffb4e909`.
- Reviewer: independent docs reviewer (did not author the reconciled files).
- Authority: `.workbuddy/tasks/D7_D_ACCEPT_BP_INTERFACE_READINESS_R1_TASK_PACKET.md`
  §3 A05–A08; `D7_D_RESULT_ACCEPTANCE_R1.md` (commit `ffb4e909`).
- Method: read-only. Reviewed the uncommitted working-tree diffs, the accepted
  cycle docs, commit history, and protected-root metadata (names/sizes only).
  No decoder, no code execution, no evidence-root content read. The only file
  written is this review document.

Candidate commit-2 files (this review is the seventh):

1. `docs/CURRENT_MAINLINE.md`
2. `docs/troubleshooting.md`
3. `openspec/changes/v72p2d7-gf32-schedule-discriminator/tasks.md`
4. `openspec/changes/v72p2d6-gf32-graph-mother-r1d-option-c/tasks.md`
5. `openspec/changes/v72p2d6-gf32-graph-mother-successor/tasks.md`
6. `openspec/changes/formal-ir-v72p2d5-model-f-input-preparation/tasks.md`
7. `docs/research_cycles/V72P2D7-GF32-SCHEDULE-DISCRIMINATOR/D7_D_MAINLINE_RECONCILIATION_REVIEW_R1.md`

Excluded, verified empty diff: `docs/v35-algorithm-development-report.md`.

---

## Check 1 — no claim exceeds accepted evidence: PASS

Ledger items 1–9 against accepted sources:

| # | Ledger claim | Accepted source | Verdict |
|---|---|---|---|
| 1 | D5 rate-mother path stopped within tested scope | `D5_ROUTE_STOP_ACCEPTANCE_R1.md`: `D5_CURRENT_TWO_LAYER_RATE_MOTHER_BP_PATH_STOPPED`, scope exactly the current fixed two-layer path, `D5_ROUTE_STOP_REVIEW_PASS` | PASS — ledger adds "within tested scope", not stronger |
| 2 | D6 graph/mother A2 structurally blocked; R1d Option C frozen but optional/paused, not a mainline gate | `D6_GRAPH_MOTHER_OPERATOR_RETURN_R1C_A2.md` + A3 correction (recomputed `D6_GRAPH_STRUCTURE_INVARIANT_BLOCKED`, terminal-agreement False); `D6_GRAPH_MOTHER_REPAIR_STUDY_R1C_A5.md` (`STRUCTURALLY_INFEASIBLE_AS_FROZEN`, 0/10 admissible); `D6_GRAPH_MOTHER_OPTION_C_ACCEPTANCE_R1.md` (`OPTION_C_ACCEPTED_R1D_FROZEN`, not an authorization); D7-D acceptance (`PAUSED_OPTIONAL_LOCAL_CONFIRMATION_NOT_MAINLINE_GATE`) | PASS |
| 3 | D7-A decoder certification PASS | `D7_A_CERTIFICATION_REPORT_R1.md`: `D7_A_DECODER_CERTIFICATION_PASS` | PASS |
| 4 | D7-B hard-decision easy region observed; RSS/belief limitations recorded; no belief-calibration claim | `D7_B_RESULT_ACCEPTANCE_R2.md`: accepted scope `HARD_DECISION_EASY_REGION_OBSERVED_WITH_RESOURCE_AND_SOFT_BELIEF_LIMITATIONS`; no `<2GiB` PASS claim (RSS unknown); posterior tolerance FAILED; `confirmed/partial` false | PASS |
| 5 | D7-C bounded bidirectional dependence accepted as a diagnostic; no proof that alternating/joint BP can bootstrap | `D7_C_RESULT_ACCEPTANCE_R1.md`: `D7_C_RESULT_ACCEPTED_BIDIRECTIONAL_DEPENDENCE_DIAGNOSTIC`; ceiling explicitly excludes "bootstrap from marginal priors" | PASS |
| 6 | D7-D schedule effect inconclusive; no schedule-superiority claim | `D7_D_RESULT_ACCEPTANCE_R1.md`: `D7_D_RESULT_ACCEPTED_SCHEDULE_EFFECT_INCONCLUSIVE`; `43 vs 40` and `3` layered-only "reported, not promoted" | PASS |
| 7 | Active gate = BP provenance implementation (Alternative A) | Packet §0; acceptance "Next gate: `BP_INTERFACE_PROVENANCE_IMPLEMENTATION`"; D7-D `cycle_state.yaml` `next_gate` | PASS |
| 8 | After BP, freeze a provenance-safe cross-layer mechanism discriminator before further cross-layer APP work | Packet §0 and A19 route `D7_E_PROVENANCE_SAFE_CROSS_LAYER_DISCRIMINATOR_PACKET_FREEZE` | PASS |
| 9 | Dimension/bw expansion only after a working mechanism; >2 layers need a separate mathematical/leakage contract | Packet §0/A04 | PASS |

Earlier-states paragraph (V34/V35R1/V36) is a conservative condensation of the
entry-HEAD authoritative text: V35R1's two bounded tokens were verified against
the committed report; no statement was strengthened (V36 now reads "no accepted
finite-graph advance"). No stronger claim found anywhere in the ledger or in the
new troubleshooting entry.

## Check 2 — V35 conflict gone: PASS

- `git diff -- docs/v35-algorithm-development-report.md` empty; working-tree md5
  equals `git show HEAD:` md5 (`397dfb837dcd218ba91fd60a5efa4c26`).
- Committed bounded status intact at lines 11–12:
  `PROTOCOL_PARTIAL_A4_NOT_EXECUTED`,
  `NO_NB_CANDIDATE_FOR_TESTED_HAND_DESIGNED_CONFIGURATION`.
- No active file claims `NB_CANDIDATE_DEVELOPMENT_READY` for the accepted
  record. Remaining tracked references are: the historical v35 module
  constant/CLI docstring describing the old branching rule (pre-existing,
  untouched), the v35 OpenSpec enum of allowed terminals (pre-existing), and
  the new troubleshooting rejection entry. None is a status claim.
- `docs/troubleshooting.md` +25 lines appended at end of file records the
  rejected rewrite, root cause, restore-to-HEAD fix, and prevention; it states
  explicitly that no backup file was created and no false table is retained.
- No backup/`.bak`/`orig`/`save` file under `docs/`;
  `docs/nbldpc-v35-successor-plan-20260824.md` has an empty diff.

## Check 3 — D7-D execution reflected: PASS

- Acceptance doc exists (172 lines) with A01 independent recomputation, paired
  table, eight strata, resource facts, supported/unsupported claims, successor.
- Ledger item 6 carries the terminal and accepted-scope tokens and
  "no schedule-superiority claim". The exact counts
  `43/40/3/0/40/85` (and syndrome-only `43/40/3/0/40/85`) are carried as
  reported-not-promoted in the accepted docs (`D7_D_RESULT_ACCEPTANCE_R1.md`,
  `docs/decision-log.md`, `AGENT_PROJECT_MEMORY.md`); no promotion.
- No successor implied: acceptance states INCONCLUSIVE has no frozen automatic
  successor; next action is the main-thread-selected Alternative A, not an
  automatic route.

## Check 4 — no stale gate in authoritative docs: PASS

- `CURRENT_MAINLINE.md` lines 3–7 add the A07 rule: "status, not
  authorization; active gate and accepted cycle documents outrank aggregate
  checkbox counts; stale historical checkboxes are bookkeeping".
- Active gate is BP provenance implementation (ledger item 7), matching the
  D7-D acceptance and `cycle_state.yaml`.
- Grep across the six reviewed files for `D7-C/D7-D`, `next = D7-C`,
  `next = D7-D`, `D7-C freeze`, `D7-D freeze`: no obsolete next-gate statement.
- Prose-label judgment: see non-blocking N1 below. No real stale gate exists in
  authoritative docs.

## Check 5 — checkbox audit integrity: PASS

Normalize-and-compare of `git diff -U0` per file (strip diff markers, replace
checkbox state, compare): every changed line is a `- [ ]` → `- [x]` flip; zero
checked→unchecked; all non-checkbox text byte-identical.

| File | flips | text after normalize | remaining unchecked |
|---|---|---|---|
| schedule-discriminator tasks.md | 6 (T2–T7) | identical | 0 |
| r1d-option-c tasks.md | 6 (D2–D7) | identical | 0 |
| graph-mother-successor tasks.md | 23 (A3-01…A3-07, A4-01…A4-05, A5-00…A5-04/06/08/10, A6-01…A6-04) | identical | 6 (T9–T14) |
| model-f-input tasks.md | 8 (T1–T6, T-ISOL, PX11-R1) | identical | 0 |

Evidence spot-checks (claimed completions vs named artifacts/commits):

- schedule-discriminator: `D7_D_FLOODING_CERTIFICATION_R1.md` F01–F08 PASS;
  `D7_D_IMPLEMENTATION_REVIEW_R1.md` → `D7_D_IMPLEMENTATION_REVIEW_PASS`
  (commit `727bca7a`); `D7_D_PRE_EXECUTE_REVIEW_R1.md` →
  `D7_D_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION` (commit
  `63f91d26`); closeout/readiness state recorded in `cycle_state.yaml`;
  memory/decision-log readiness and acceptance facts present at HEAD
  (`ffb4e909`).
- r1d-option-c: implementation+tests commit `cddaaed9`; reviews commit
  `c56d408e`; verdicts `D6_R1D_IMPLEMENTATION_REVIEW_PASS` and pre-execute PASS;
  D7 end state `D6_GRAPH_MOTHER_R1D_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`,
  all auth false.
- successor: A3 docs (forensic, impl review `D6_R1C_A3_IMPLEMENTATION_REVIEW_PASS`,
  Pre-RESULT `…_PASS_BLOCKED_RUN`, result `D6_GRAPH_MOTHER_RESULT_R1C_A3.md`);
  A4 `READY_FOR_FUTURE_D6_PRE_EXECUTE_REVIEW` +
  `D6_R1C_A4_PERFORMANCE_REVIEW_PASS`; A5 validity/repair/readiness docs
  (`STRUCTURALLY_INFEASIBLE_AS_FROZEN`; readiness `NOT_AUTHORIZED`);
  A6 `D6_R1C_A6_REVIEW_PASS` + A6-04 slow-task inventory section.
- model-f-input: implementation files exist; commit `b986ca11`;
  `MODEL_F_INPUT_PRE_RESULT_REVIEW_R1.md` records the PX11 fix (prior R1 FAIL
  on PX11 preserved); `TEST_ISOLATION_REWORK_EVIDENCE_R1.md` holds the T-ISOL
  evidence.
- No unchecked item was turned into new work: the only remaining unchecked
  items are successor T9–T14 (original R1 plan stages, superseded historical
  bookkeeping).
- No archived V62/V63/V64 file was content-touched: `git diff --name-only`
  contains no `openspec/changes/archive/*` path; archive `git status` entries
  are CRLF/stat noise resolved empty by content diff
  (`git diff --stat -- openspec/changes/archive` empty).

## Check 6 — protected roots / auth / dirty scope: PASS

- D7-D root `workspace/d7_d_schedule_discriminator_64660d16-397d-4ef3-8454-3066d27c12c7/`:
  exactly 7 files, zero subdirectories, sizes
  `290 / 57659 / 3164 / 17690 / 455 / 1777 / 1546` — matches the acceptance.
- D7-C root `workspace/d7_c_bidirectional_oracle_94c0ea15-a786-4cb8-a991-6fec521cccae/`:
  exactly 6 files, sizes `282 / 23599 / 2709 / 1130 / 362 / 728`.
- Active gate states (D5, D6, D7-B, D7-C, D7-D `cycle_state.yaml`): every
  `*_authorized` key false, `scientific_promotion: false`; D7-D
  `d7d_execution_authorized: false`, `g1_authorized: false`,
  `g2_authorized: false`.
- No push: branch is ahead of `origin/formal-ir-v72p1-addendum-clean`; no push
  performed.
- Unrelated dirty paths untouched: `docs/research-cycle-sop.md` (+137) and
  `workspace/pytest-evidence-test/output/expanded_evidence_manifest.json`
  remain unstaged; `.workbuddy/` untracked and untouched; CRLF-only stat
  entries untouched.

## Non-blocking notes

- **N1 (label prose).** `v72p2d7…tasks.md` header still reads "T2–T7 pending /
  No D7-D scientific execution" while T2–T7 boxes are now checked, and
  `…r1d-option-c/tasks.md` D7 still says "gate awaiting explicit R1d
  authorization" while the D7-D acceptance sets R1d to
  `PAUSED_OPTIONAL_LOCAL_CONFIRMATION_NOT_MAINLINE_GATE`. Both are plan-time
  bookkeeping strings, not gate statements. With the new A07 rule
  (`CURRENT_MAINLINE.md` lines 5–7) and the accepted D7-D docs outranking
  checkbox counts, no real stale gate is created in authoritative docs.
  Recommended: reword only if these files are next touched; no edit required now.
- **N2 (historical auth residue).** Pre-D5 states (e.g. `V72P2D3-GF32`
  `r3_real_execution_authorized: true`, `V72P1-ADP`
  `development_execution_authorized: true`, older V37/V38 states) carry legacy
  consumed authorization markers; they are outside this reconciliation's scope
  and untouched. The A04/A20 claim "all authorizations false" holds for the
  active D5–D7 gate.
- **N3 (memory scoping).** `AGENT_PROJECT_MEMORY.md` and `docs/decision-log.md`
  are not part of this commit; the D7-D acceptance facts are already appended
  at HEAD (`ffb4e909`, A04). Next memory triage needs no extra reconciliation.

## Verdict

`D7_D_MAINLINE_RECONCILIATION_REVIEW_PASS` — release the A08 commit of exactly
the six reconciled files plus this review. FAIL not indicated.
