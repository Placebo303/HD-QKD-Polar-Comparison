# Tasks — V72P2D10 mixed-degree L1 finite discriminator (R1 + R2)

R1 packet: `.workbuddy/tasks/D10_MIXED_DEGREE_L1_FINITE_READINESS_R1_TASK_PACKET.md`.
F01–F12 complete and retained (2026-09-14; R1 evidence immutable in
`docs/research_cycles/V72P2D10-MIXED-DEGREE-L1/{READINESS_R1.md,EXPLORATION_LOG.md,INDEPENDENT_REVIEW_R1.md}`).
R1 main-thread decision: `REVISE_REQUIRED_CONNECTIVITY_AND_RANK`
(F4 elevated to blocker: 9–68 components, largest fraction 0.039–0.297,
rank<m in several cells; R1 batch not authorized).

R2 packet: `.workbuddy/tasks/D10_MIXED_DEGREE_L1_CONNECTIVITY_R2_TASK_PACKET.md`
(sole R2 authority; implementation/readiness, no EXPLORE/DECIDE execution).
R201 (this task, planner, OpenSpec only) amends proposal/design/tasks/spec;
R202–R212 pending. Branch `formal-ir-v72p1-addendum-clean` (do not switch; no
commit, no push). No decoder/DE/CAL/VAL/real-data execution in R201.

R1 history (preserved; all `[x]`):

- [x] F01 Verify and record the D9 accepted terminal (`D9_DE_CALIBRATION_SELECT_ONE`),
  unique selected candidate `lam_d2_0.45_d3_0.55`, stability counts (DV3
  0/8 & 0/8 `stable_unconverged`; 0.45 8/8 & 8/8 `stable_converged`; 0.50
  7/8 & 8/8 `stability_ambiguous`; 0.55 6/8 & 4/8 `stable_unconverged`),
  acceptance lifecycle `D9_DE_CALIBRATION_RESULT_ACCEPTED_SELECT_DV23_045` and
  the DE-only claim ceiling from existing artifacts; no DE rerun. Recorded in
  `docs/research_cycles/V72P2D10-MIXED-DEGREE-L1/READINESS_R1.md` §F01.
- [x] F02 Inventory degree-sequence/PEG builders (B1–B7) and select the
  smallest compatible path; select B8, the minimal deterministic
  degree-sequence PEG `build_degree_sequence_peg` reusing the accepted
  `nonbinary_v10_peg` placement primitives, with rejected alternatives and
  reasons. `design.md` §2.
- [x] F03 Freeze (a) the exact f1.2 degree tables for both arms at
  n64/n128/n256 from the D9 acceptance table, cross-checked against the D9
  root `summary.json` `graph.cells`; (b) 3 graph seeds per width (fresh,
  separate from block seeds); (c) the deterministic uniform nonzero GF32
  coefficient rule; (d) 8 block seeds per width (fresh, separate from graph
  seeds); (e) deterministic call order and paired identical-block decoding;
  (f) structural gates G1–G10. `design.md` §3–§5.
- [x] F04 Freeze the paired multi-graph thresholds (POSITIVE/NEGATIVE/
  AMBIGUOUS/ENGINEERING_BLOCKED), control-separation caps, conditional width
  progression from n64, the terminal set/routing and the claim ceiling against
  the 2×3×3×8 = 144-call design. `design.md` §6–§7.
- [x] F05 Create this complete OpenSpec change and the
  `docs/research_cycles/V72P2D10-MIXED-DEGREE-L1/{READINESS_R1.md,EXPLORATION_LOG.md}`
  documents, one decision-log entry, the fresh future root UUID (verified
  absent), the exact future command (left absent/unauthorized) and the frozen
  budgets before any behavior edit.
- [x] F06 Implement the two-arm graph construction (B8 builder, structural
  records, coefficient generation, L1-only runner and read-only verifier)
  exactly as frozen in `design.md` §2–§5, within the allowed files.
- [x] F07 Guarantee invalid structure fails before decoder binding; tests
  cannot reach the production decoder without an explicit injected runner.
- [x] F08 Add focused tests: tiny exact-degree/socket tests, determinism,
  seed separation, multi-graph variation, coefficient distribution/range,
  rank/4-cycle metrics, paired call matrix, transition rules, exact/syndrome
  separation, provenance/residual fields, no-overwrite and fake-runner
  isolation.
- [x] F09 Run focused T0/T1 tests and bounded `--profile-only` graph
  construction at all widths; no scientific decoder call, no future root.
- [x] F10 Freeze/confirm the exact future command/root/budgets; verify root
  absent and all authorization flags false.
- [x] F11 Obtain one independent reviewer-go review of graph mathematics,
  isolation, decoder-entry boundary, thresholds and the frozen command.
  (Verdict `PASS_WITH_FINDINGS`; F1/F3/F4/F5 carried, F2 resolved at F12.)
- [x] F12 Apply at most one scoped non-scientific correction (F2:
  `PROFILE_REPLACEMENT_SEEDS 2026092210..2026092215` enumerated; scoped
  re-review RESOLVED/PASS) and stop at
  `D10_MIXED_DEGREE_L1_READY_AWAITING_EXPLICIT_AUTHORIZATION`. R2 RETIRES
  this replacement clause (zero replacement seeds; design §4.1).

R2 tasks (R201–R212 done; R212 docs call records R211 VERIFIED PASS evidence; frozen contract from
proposal §3 / design §§1/3/4/6–8 MUST be preserved exactly):

- [x] R201 Amend the active D10 OpenSpec (`proposal.md`, `design.md`,
  `tasks.md`, `specs/mixed-degree-l1-finite-discriminator/spec.md`) for R2:
  preserve the frozen R1 scientific contract exactly (two arms
  `PEG_DV3_MATCHED` vs `PEG_DV23_LAM2_045`; widths 64/128/256 at
  `m = 59/118/236`; exact degree tables DV3 `E = 192/384/768` with
  `3^44+4^15` / `3^88+4^30` / `3^176+4^60` and mixed `E = 157/313/627` with
  `2^20+3^39` / `2^41+3^77` / `2^81+3^155` incl. `(n2,n3) = (0,n)` /
  `(35,29)/(71,57)/(141,115)`; graph seeds `2026092201..09` with R1 width
  assignment; block seeds `2026092301..08` / `2311..18` / `2321..28`;
  Model-F root `workspace/v72p2d5_model_f_input/20260907_r1`; frozen priors;
  GF32/poly37; coefficient rule `v10_seed(f"d10:coeff:{width}:{graph_seed}")`;
  decoder `max_iter=90` / `damping=1.0` / cold; paired blocks; thresholds
  POSITIVE/NEGATIVE/AMBIGUOUS/ENGINEERING_BLOCKED; progression; budgets
  `<=144` L1 + `<=44` setup / wall `<=1800` s / per-call `<=120` s /
  RSS `<2` GiB; claim ceiling) and add the R202–R207 delta
  (connectivity-first PEG; structural `m`; GF32 `m` record-and-stop; six-
  predicate admission; explicit CLI auth arg; fail-closed `--verify`).
  OpenSpec files only; no code/tests/decoder/batch/root/commit/push.
- [x] R202 Implement the smallest deterministic connectivity-first
  degree-sequence PEG builder: spanning backbone over every variable and
  check node respecting exact target degrees, then shared PEG/ACE fill;
  reject parallel edges and degree/socket mismatch; one constructor + tie
  policy shared by both arms (only the forced degree sequence differs);
  deterministic replay. No replacement seeds, no seed search, no topology
  selection, no decoder feedback, no adaptive construction.
- [x] R203 Add deterministic maximum bipartite matching; require all `m`
  checks covered (`structural_rank == m`); fixed visitation order under the
  frozen graph seed.
- [x] R204 Generate coefficients by the frozen R1 rule and compute exact GF32
  (poly 37) row rank; require `gf32_rank == m`; on failure record the cell
  and stop without altering graph/coefficient seeds (no repair/reseed).
- [x] R205 Enforce admission BEFORE decoder binding: exact degrees/socket,
  simple graph, exactly 1 component over `n+m` Tanner nodes, structural `m`,
  GF32 `m`, deterministic replay equality; four-cycle/girth/ACE diagnostics
  only.
- [x] R206 Replace source-constant flipping with an explicit CLI
  execution-authorization argument (repo `--execution-authorized`
  convention), default false; refuse `--batch` before root creation and
  before decoder binding; keep false and unused through R211.
- [x] R207 Keep `--verify` fail-closed (zero skip; FAIL on any partial or
  engineering-blocked root); create no scientific root.
- [x] R208 Add focused tests covering all six admission predicates, exact
  frozen tables/seeds, both arms sharing the constructor, unauthorized
  no-write/no-bind refusal, and deliberate disconnected/rank-deficient
  rejection; fake decoders for entry-boundary tests only.
- [x] R209 Run `py_compile` and focused D10 tests only with a fresh
  task-owned `workspace/` basetemp and `-p no:cacheprovider`; broader tiers
  only if a focused failure demonstrates an external regression.
- [x] R210 Run no-decoder `PROFILE_ONLY` for exactly the original 18 cells;
  record component count, largest fraction, structural/GF32 rank,
  four-cycles, girth, wall time; require zero replacement seeds and zero
  decoder calls/binds.
- [x] R211 Obtain one independent readiness review with
  `EVIDENCE_ACCESS: VERIFIED` recomputing every admission predicate for all
  18 cells and checking R1 frozen-contract equality; no ceremonial
  duplication of a traceable passing review.
- [x] R212 Append evidence/review to the existing exploration log and perform
  project-memory triage; no commit or push unless separately requested.

Gate: R1 future batch was never authorized (`REVISE_REQUIRED_CONNECTIVITY_AND_RANK`).
R2 return `D10_MIXED_DEGREE_L1_R2_READY_AWAITING_EXPLICIT_AUTHORIZATION` only
if all 18 original cells pass A1–A6 and review has no blocker (grants NO
execution); else `BLOCKED_D10_CONNECTED_FULL_RANK_CONSTRUCTION` with exact
failing cells. STOP on ambiguity, frozen-input drift, seed
replacement/search, decoder entry, scientific-root creation, unrelated
dirty-file conflict, or failed review.

Future command (frozen shape; do not run; R206 auth arg defaults false):

```text
.venv/bin/python scripts/v72p2d10_mixed_degree_l1_development.py --batch \
  --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 \
  --out-root workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34
```
