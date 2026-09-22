# D7-E provenance-safe cross-layer discriminator — Implementation Review R1

- reviewer: independent D7-E implementation reviewer (did not write implementation)
- authority: `.workbuddy/tasks/D7_E_CROSS_LAYER_READINESS_AND_D6_COMPAT_R1_TASK_PACKET.md` §6/R18 only
- branch: `formal-ir-v72p1-addendum-clean`
- entry HEAD: `f82804f6736e1fdac41dc5b42931fd57aea580e9` (`f82804f6 docs(d7-e): freeze provenance-safe cross-layer discriminator`)
- date (UTC): 2026-09-11
- scope (uncommitted, untracked, review-only):
  - `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_cross_layer_discriminator.py` (1712 lines)
  - `comparison_bench/tests/test_v72p2d7_gf32_cross_layer_discriminator.py` (1540 lines, 25 tests)
  - `scripts/v72p2d7_gf32_cross_layer_discriminator.py` (104 lines)
- freeze (committed `f82804f6`, 7 files): OpenSpec `v72p2d7-provenance-safe-cross-layer-discriminator/` + `D7_E_PREREG_R1.md` + `D7_E_EXECUTION_PACKET_R1.md` + `cycle_state.yaml`
- review-only: no commits, no edits except this file, no decoder/Model-F content, no roots created

## Verdict

`D7_E_IMPLEMENTATION_REVIEW_PASS`

One scoped rework was allowed; none was required.

## Freeze / HEAD verification (pre-review gate)

- `git rev-parse HEAD` = `f82804f6736e1fdac41dc5b42931fd57aea580e9` — matches required prefix `f82804f6736e...`.
- `git log --oneline -1` still `f82804f6 docs(d7-e): freeze provenance-safe cross-layer discriminator`; `git diff --cached --name-only` empty (no staging); no commits made by reviewer.
- The three D7-E files are untracked (`git ls-files --others --exclude-standard` lists exactly those three under the `*v72p2d7_gf32_cross_layer*` filter) with `wc -l` 1712 / 1540 / 104 matching the claim.
- `git show HEAD --stat` = 7 frozen files (proposal/design/spec/tasks + prereg + execution-packet + cycle_state.yaml); `cycle_state.yaml` state `FROZEN_PREREG_R1_NOT_AUTHORIZED_NOT_EXECUTED`, all authorization keys false, no UUID/root.
- Worktree note (non-blocking, pre-existing): `git diff --name-only` (content diff) lists 8 tracked files with real content changes (`AGENT_HANDOFF.md`, `AGENT_PROJECT_MEMORY.md`, `README.md`, `docs/CURRENT_MAINLINE.md`, `docs/decision-log.md`, `docs/research-cycle-sop.md`, `docs/v35-algorithm-development-report.md`, `workspace/pytest-evidence-test/output/expanded_evidence_manifest.json`) — all NB-Polar-boundary / SOP / memory / V35 provenance updates, none containing D7-E changes. `git status --porcelain` additionally lists ~1867 ` M` entries with empty `git diff` (WSL `/mnt/d` stat noise, `core.fileMode=false`, `core.autocrlf=input`); `git diff --numstat` confirms only the 8 files above have content deltas. Packet §1 explicitly says to preserve unrelated dirty/CRLF and V35 rewrites. D7-E scoped cleanliness holds: no tracked file modified by D7-E, no staged residue, three new files only. See §9.
- Post-test guard: `workspace/d7_e_cross_layer_discriminator_*` and `workspace/d6_graph_mother_r1d_*` both absent (`No such file or directory`); reviewer test runs used only `/tmp/*` basetemps and pytest `tmp_path` fixtures.

## Check 1 — Formulas (PASS)

Frozen (packet R09 / spec): `P_transfer(U2|B,s1)=sum_u1 q1(u1)P(U2|B,u1)`; `P_transfer(U1|B,s2)=sum_u2 q2(u2)P(U1|B,u2)`; D5 floor/renorm; q transient never persisted; no source truth in either formula.

- L1→L2 (`transfer_prior_l1_to_l2`, core ~545-552): `_check_mixer_q` → `_transfer_conditional(joint,bob,"U2|U1")` → `einsum("nu,nuv->nv")` → `d7c.d5._floor_renorm(out, DECODER_FLOOR)`. Conditional slice `j[:,:,bob].transpose(2,0,1)` = `(n,u1,u2)`, mass over `u2`, so `cond[i,u1,u2]=P(U2|b_i,u1)`; zero-mass → uniform `1/32` (accepted D5 convention). Matches frozen direction.
- L2→L1 (`transfer_prior_l2_to_l1`, ~555-562): same with axis `"U1|U2"`, `transpose(2,1,0)` = `(n,u2,u1)`, mass over `u1`, so `cond[i,u2,u1]=P(U1|b_i,u2)`; `einsum` over `u2`. Matches frozen direction.
- `build_transfer_prior` (~565-572) dispatches only on `"L1_TO_L2"` / `"L2_TO_L1"`, raises on unknown; `softmax_source_q` (~498-508) is rowwise softmax of `(n,32)` finite log belief via `d7c._softmax_rows`, loud on bad shape/nonfinite.
- Floor/renorm: both priors call the single accepted `d7c.d5._floor_renorm` with `DECODER_FLOOR` (`1e-15`, pinned in `test_e02`); no second renorm.
- Transient q: `execute_slots` TRANSFER branch (~795) `q = softmax_source_q(src["beliefs"])  # transient, never persisted`; `RECORD_FIELDS`/`PAIR_FIELDS`/`STRATUM_FIELDS` contain only scalars (no belief/prior/syndrome/vector fields); `write_root` rejects extra fields and non-scalars (`_scalar` raises on ndarray, `_record_row` raises on unknown fields).
- No source truth: signatures pinned `["joint","bob","q1"]` / `["joint","bob","q2"]` / `["joint","direction","bob","q"]`; TRANSFER prior call is `build_transfer_prior(context["joint"], direction, block["bob"], q)` — `bob` (observed) + `q` + joint only; `u1`/`u2`/`alice` appear only for `x_true` exact/syndrome evaluation (`evaluate_call` ~664, `execute_slots` ~782) and syndrome `d7c.d5._gf32_syndrome(h_prefix, x_true)` per D7-C contract, never inside the prior.
- Tests genuine (`test_e01`): random `(32,32,3)` joint + `(5,32)` q vs explicit per-`i` direct enumeration loops for both directions (`joint[:,:,b]/sum(axis=1)` and `/sum(axis=0)` + `@ cond`), `atol=1e-12`, shape/sum/floor asserts, zero-mass uniform fallback with one-hot `q`, signature pins, unknown-direction raise, dispatch equivalence, softmax round-trip and two failure modes. Not a self-comparison: independent loop math.

## Check 2 — Provenance gate (PASS)

Frozen (R10 + Alternative A): exactly `CHECK_UPDATED` admits one transfer call; prior-only/missing/None/unknown/warm block before mixer/target decoder; source-exact-false stays eligible; token governs over iterations/label.

- Gate (`check_source_eligibility` ~470-491): crash (`status.startswith("crash:")` → `SOURCE_CRASH`) → nonfinite → shape → `require_check_updated(provenance)` (delegates to `d7c.d5._require_check_updated_provenance`, lazy v35 bind, never at import). Refusals map to `PROVENANCE_BLOCKED` only when the raised type is `belief_provenance_error()`; unexpected types propagate loudly. Source exactness never consulted.
- Single-call admission: `execute_slots` TRANSFER branch re-checks cached source (`record.status/finite/shape_ok/provenance`) and `continue`s (recorded non-invocation, no wall cost) when refused; `q`/mixer/decoder unreachable. `test_g01` all-`CHECK_UPDATED` run: 192 records (64 source + 64 control + 64 transfer), all sources `transfer_eligible=True` + `belief_provenance=CHECK_UPDATED`, 64 pairs all `CHECK_UPDATED`, `verify_root ok`.
- Five refused classes (`test_g02`, parametrized over `["PRIOR_ONLY","<missing>",None,"SOME_FUTURE_TOKEN", WARM_START_UNSPECIFIED]` with `PRIOR_ONLY` pinned to `v35.BELIEF_PROVENANCE_PRIOR_ONLY`): each patches `build_transfer_prior` and `softmax_source_q` to raisers, asserts `mixer_calls==[]`, target calls == 64 (controls only), 128 records, no TRANSFER rows, all sources `transfer_eligible=False`, zero pairs, strata `eligible=0/blocked=16/label=""/COVERAGE_BLOCKED`, terminal `PROVENANCE_COVERAGE_BLOCKED`, `verify_root ok`; direct `check_source_eligibility` returns `(False, PROVENANCE_BLOCKED)` for each. Spies silent — mixer/softmax never reached.
- `test_g03`: uniform joint + nonzero truth (all sources `exact=False`) yet all `transfer_eligible=True`, 64 transfers, pairs `source_exact=False` — exactness does not gate.
- `test_g04`: `iterations=[0]*64` + `CHECK_UPDATED` → all eligible, labels `PRIOR_ONLY_CURRENT_BELIEF` (token governs, not label); `iterations=[7]*64` + `PRIOR_ONLY` → all blocked, 128 records. `_belief_label` (iterations>0) is display-only; gate uses provenance token only.

## Check 3 — Pairing (PASS)

Frozen (R08/R10): control/transfer share f/seed/block/target H/syndrome/decoder config, only prior differs; exact 192-slot order with 128 mandatory; blocked = recorded non-invocation, no replacement/retry/fake; no double-counting.

- Order: `frozen_slots` (~380-404) outer `F_VALUES=[1.0,1.2]`, `BLOCK_SEEDS=2026091300..2026091315` ascending, `DIRECTIONS` × `ROLE_ORDER=(SOURCE,CONTROL,TRANSFER)` via `SLOT_ROLE`; `test_m01` pins all 192 `slot_idx 1..193`, f-split 96/96, per-`(f,seed)` six-tuple with rows `{1.0: L1 49/L2 43, 1.2: L1 59/L2 52}`, `n=64`, 128 mandatory + 64 transfer.
- Sharing: `execute_slots` uses same `block=context["blocks"][seed]`, same `h_prefix=mothers[layer][:rows]` (transfer rows equal control rows per m01), same `syndrome=_gf32_syndrome(h_prefix,x_true)` (target-layer truth per D7-C contract), same `TARGET` decoder via `dispatch_decoder`; only prior differs (control `condition_prior_qn`+`decoder_prior` vs transfer `build_transfer_prior`). `test_m03` captures H/prior/syndrome arrays: `h_c==h_t`, `syn_c==syn_t`, `prior_c.shape==(64,32)`, `not allclose(prior_c,prior_t)`, pair slot indices differ; production bind pinned (`SOURCE.target`/`TARGET.target is v35.decode_row_layered_fftqspa`, `max_iter=MAX_ITER/damping/warm_beliefs=None/field=None` each ×2, `MAX_ITER=90/DAMPING=1.0`).
- Blocked semantics: `continue` with no record append, no retry/resume/concurrency (sequential loop, hard cap `MAX_CALLS=192`, `retries/reruns/resumes=0` in manifest/summary, verifier checks `records after stop position` and `retries==0`). `compute_transfer_pairs` (~896-949) joins on `(f,seed,direction)`, requires source `transfer_eligible` true and both control+transfer present (truncated runs yield no pair; verifier judges missing row), one row per key sorted, `source_exact`/`source_provenance` ride as context only. No double-counting: `transfer_invoked` = TRANSFER row count, `transfer_blocked` = source count − eligible, both recomputed by verifier; `test_m03`/`g01` assert 64 pairs on full runs, `g02` zero pairs on fully blocked runs.

## Check 4 — No oracle truth (PASS)

- Code: transfer path never references `L1_ORACLE_U2`/`L2_ORACLE_U1`, `oracle_*_prior`, `app_fed_l2_prior`, flooding, or truth symbols; `test_x04` static scan forbids `decode_flooding_fftqspa/app_fed_l2_prior/oracle_l2_prior/L1_ORACLE_U2/L2_ORACLE_U1/FLOODING/flooding/--phase/psutil/concurrent/multiprocessing/threading` and `r1d` (case-insensitive) in core+runner, forbids legacy builders, pins `decode_row_layered_fftqspa(` count == 4 (two wrappers + two `.target` pins) and absence of `d7c.run_bidirectional_oracle/d7c.write_root/d7c.verify_root/d7c.bind_historical_decoder/d7c._default_model_f_loader(`.
- Tests: all transfer math on tiny explicit in-memory fixtures (`_uniform_joint`, `_column_joint` crafted Bob columns, `_const_block`, `_peaked_log`, scripted source/target fakes); no production artifact/root read (`test_x05` poisons `_load_model_f_input_or_blocked`/`_default_model_f_loader`, asserts workspace listing unchanged, no `d7_e_*`/`d6_graph_mother_r1d_*`/`v72p2d5_g2/20260906_r1`, `_EXECUTION_CONSUMED is False`, D7-E cycle-state auth keys all false). D7-C tables never loaded as inputs; crafted lift/regression/no-recovery joints in `l03` serve as mechanism fixtures, not oracle ceilings.

## Check 5 — Thresholds / terminal (PASS)

Frozen (R11/R12): five first-match labels + empty-label rule with all boundaries; twelve terminals in priority order with genuine truth-table coverage incl. coverage-blocked and priority preemption; strata + blocked counts persist under higher terminal.

- Labels (`classify_stratum` ~952-971, first-match): `eligible<12 → ""`; STRONG (`transfer_only>=4, control_only<=1, transfer_exact>=4, crash_nonfinite==0`); REGRESSION (`control_only>=4, transfer_only<=1`); NO_RECOVERY (`transfer_exact<=1 and control_exact<=1`); CONTROL (`control_exact>=12`); else AMBIGUOUS. `STRATUM_LABELS` order pinned. `test_l01` pins signature and every boundary: STRONG 4/1/4/0 vs fall-throughs (3-only, 2-control-only, 3-transfer-exact, 1-crash); REGRESSION 1/4 vs 2-only and 3-only fall-throughs; NO_RECOVERY 1/1 and 0/0 vs 2/1; CONTROL 16/16 and 12/12 vs 11/11; empty for eligible 0/1/11. `test_g05` pins 12-labels vs 11-empty boundary with a live 11-eligible stratum (`eligible=11/blocked=5/label=""/COVERAGE_BLOCKED`, terminal `COVERAGE_BLOCKED`).
- Terminals (`classify_terminal` ~1036-1067, `TERMINALS` order pinned in `test_l02`): T1 pre → T2 watchdog → T3 crash → T4 resource → T5 incomplete → T6 coverage → T7 bidirectional (same-f both-strong) → T8 L1→L2 → T9 L2→L1 → T10 regression (any regression, no strong) → T11 all-no-recovery → T12 mixed. Truth table genuine: T1..T6 cascade each beats lower, full-stack preemption chain, same-f T7 (f=1.0 and f=1.2) vs split-f (`1.0/L12 + 1.2/L21 → MIXED`, not bidirectional), T8/T9 single-side, T10 vs strong+regression preemption (`STRONG+REGRESSION → L1_TO_L2`, not regression), T11 all-no-recovery, coverage over mechanism (`coverage+strong → COVERAGE`).
- Persistence: `compute_strata` always emits 4 rows (2f×2dir) with `eligible/blocked` + all exact/syndrome splits + `nonfinite/crash` + label/coverage; `terminal_from_records` recomputes from scalars; `verify_root` recomputes pairs/strata/terminal/wall/RSS and requires match. `test_l03` loop families (T7 both, T8 L12-only, T9 L21-only, T10 regression, T11 no-recovery, T12 mixed with all-CONTROL) each `verify_root ok`; crash (`crash_at_40`, no retry, prefix records, `T_CRASH`), watchdog (120.0 pass / 120.0001 void, 1 record), stored-wall (1500.0 pass / +0.0001 overrun, `T_RESOURCE`), RSS limit and preflight `PreflightBlocked(T_PRE_EXEC, zero calls, no root)`, truncated-without-stop → `T_INCOMPLETE` all persist strata/blocked counts and verify (including `w02_stopped` watchdog-truncated root verifying ok).

## Check 6 — Estimator identity (PASS)

Frozen (R09): only corrected per-column path reachable; static test genuinely fails on legacy reference; asymmetric-table test numerically distinguishes formulas; D6-R1d static coverage included.

- Identity: `LAMBDA_STAR==d5.LAMBDA_STAR==137.3823795883264`, `DECODER_FLOOR==1e-15`, `_ESTIMATOR_ID==d7c._ESTIMATOR_ID`; `prepare_inputs` delegates to `d7c.prepare_inputs` (accepted estimator chain); narrow aliases (`build_joint/condition_prior_qn/decoder_prior/build_mother/_default_model_f_loader is d7c.*` pinned in `test_m02` with behavior equality on random joint/block).
- Numeric distinction (`test_e02`): `counts=[[8,1,0],[2,6,1],[0,2,7],[1,0,2]]`, `lam=2.0`: `build_f_model_concentration` vs `build_f_model` differ `max|diff|>1e-6`, corrected columns sum to 1; spy on `prepare_model_f_prior_candidate` asserts single call `((N_A,BOB_DIM),(BOB_DIM,),LAMBDA_STAR)` with joint shape `(32,32,BOB_DIM)` while `prepare_model_f_prior` and `build_f_model` are poisoned to raise.
- Static ban (`test_e03` + `test_x04`): regexes `build_f_model\s*\(` and `prepare_model_f_prior\s*\(` over `CORE_PATH/RUNNER/D6_RUNNER/D6_CORE` assert no match; `build_f_model_concentration` / `prepare_model_f_prior_candidate` presence asserted in core and `prepare_model_f_prior_candidate` in `D6_RUNNER`. Genuine: patterns require `(` immediately after the legacy stem, so `build_f_model_concentration(` / `prepare_model_f_prior_candidate(` do not match (verified: core line 28 docstring mention is the corrected names only; `grep build_f_model` in core returns only the docstring corrected chain). D6-R1d coverage present (both runner and core scanned).

## Check 7 — Schema (PASS)

Frozen (R15/R16): exactly seven scalar text files; no beliefs/priors/symbols/syndromes/vectors/digests persisted (static + writer tests); verifier recomputes independently without Model-F/decoder; tamper cases genuine.

- Seven files: `SEVEN_FILES=(manifest.json,decoder_records.csv,transfer_pairs.csv,stratum_summary.csv,summary.json,report.md,command_log.txt)`; `write_root` writes exactly those into a fresh root (refuses existing non-empty dir, subdirs, overwrite), `manifest.call_order==_CALL_ORDER`, `decoder_ids==_DECODER_IDS`, `terminal_priority==TERMINALS`; `verify_root` requires `entries==sorted(SEVEN_FILES)` and no subdirs. `test_w01` pins file list, header equality (`RECORD_FIELDS/PAIR_FIELDS/STRATUM_FIELDS`), 192/64/4 row counts, scalar-only (`no value startswith "["/"{"`), manifest pins, non-empty report/command_log, overwrite/subdir refusals, extra-field (`u1_vector`) and array-value (`np.zeros(3)`) rejections, production-root contract (`validate_production_out_root` outside/prefix checks).
- Verifier (`verify_root` ~1441-1562): read-only from seven files; recomputes manifest contract, slot walk (`_expected_walk`: duplicate/unparseable slot, blocked-transfer-only skippable, record semantics incl. `transfer_eligible` gate recompute, `beliefs_conditioned==iterations>0`, `exact==symbol_errors==0`, `syndrome_ok→unsatisfied==0`, wall/RSS), mandatory-128 vs stop-terminal allowance, no-records-after-stop, pair/strata/terminal/wall/`calls_completed|attempted/mandatory/transfer_invoked|blocked/strata-labels/retries` equality; never imports Model-F loader or binds/calls decoder (only `frozen_slots/compute_*/classify_*/_check_*`).
- Tamper (`test_w02`, 14 cases, each `verify ok is False`): dup slot, missing slot 63, unpaired slot 3, exact flip, syndrome flip, provenance flip (`CHECK_UPDATED→PRIOR_ONLY`), eligibility flip, pair `transfer_only_exact` flip, pair row drop, strata label flip, summary terminal flip, wall +1.0, manifest `lambda_star` flip, extra file; plus watchdog-truncated root still verifies. Each mutates a distinct recomputed invariant — genuine.

## Check 8 — Tests (PASS) + deselection adjudication (PASS-neutral)

Reviewer re-ran the new suite in separate processes with fresh basetemps and `-p no:cacheprovider` (fakes only, no production root/decoder):

- ` -k "not x06"` (`/tmp/d7e_review_grp1`): `22 passed, 3 deselected` in 28.99s.
- ` -k "x06a"` (`/tmp/d7e_review_x06a`): `1 passed, 24 deselected` in 11.19s (inner: BP `23 passed`, D7-A `14 passed`).
- ` -k "x06b"` (`/tmp/d7e_review_x06b`): `1 passed, 24 deselected` in 101.29s (inner: D7-B `29 passed` with 2 deselected, D7-C `19 passed` with `1 deselected`).
- ` -k "x06c"` (`/tmp/d7e_review_x06c`): `1 passed, 24 deselected` in 177.74s (inner: D7-D `28 passed` with `2 deselected`, D5 `165 passed`).
- Total: `25 passed`, 0 failed. Inner totals reproduced via the `x06*` asserts (`23/14/29/19+1/28+2/165`).

Deselection adjudication — 5 IDs, all `-k not ...` deselects (no `skip`/`xfail`/delete markers in the D7-E file; `grep skip|xfail|deselect` shows only the docstring reason and the `-k` lines):

- D7-D `test_f08_no_real_model_f_production_root_or_formal_root_read` — reviewer reproduced baseline FAIL: `assert [d7_d_schedule_...64660d16...] == []` (committed leftover root `workspace/d7_d_schedule_discriminator_64660d16-397d-4ef3-8454-3066d27c12c7`, tracked in git). Documented in D7-E module docstring (lines 10-16) + `test_x06c` comment (R22 debt) + prior BP reviews.
- D7-D `test_s21_protected_root_lifecycle_and_d7bc_immutability` — reproduced FAIL on the same leftover root (`WS.glob(d7d.OUT_ROOT_PREFIX+"*")==[]`). Same documentation. Both fail identically at baseline (D7-E files untracked, not imported by D7-D suite).
- D7-B `test_launch_l04_dry_run_both_cwds_no_bind_no_root` — reproduced FAIL: `assert ['.../d7_b_easy_regime_c605d1e6...'] == []` (tracked accepted D7-B root). Same stale root-absence pattern; documented in prior `D7_BP_INTERFACE_IMPLEMENTATION_REVIEW_R1.md:94` + `D7_BP_INTERFACE_READINESS_REVIEW_R1.md:184-185` as correctly not converted (outside BP scope) and validly isolated with baseline proof. D7-E file records the exact IDs via `-k` and asserts `29 passed`; module docstring covers only the D7-D pair — see non-blocking note.
- D7-B `test_launch_l12_roots_and_authorization_unchanged` — reproduced FAIL on the same D7-B root. Same adjudication.
- D7-C `test_c19_protected_root_lifecycle_and_g2_r1d_absence` — reproduced FAIL: `('decoder_executed', True)` (D7-C `cycle_state.yaml` records `decoder_executed:true/result_created:true` after the legitimate accepted D7-C run `94c0ea15...`, while the test expects false). Root-absence part was already converted to snapshot invariance (passes); residual is a stale authorization snapshot. Documented in `D7_BP_INTERFACE_IMPLEMENTATION_REVIEW_R1.md:93` as accepted isolation (honestly red, pre-existing; completing it would weaken an authorization tripwire) and `READINESS_REVIEW:192`. D7-E correctly isolates with `-k` and asserts `19 passed + 1 deselected`.

All five fail identically with D7-E present vs baseline (suites do not import `d7e`; failures are committed-root / accepted-state facts predating D7-E). Deselection is PASS-neutral per R22 (no broad cleanup, snapshot invariance only where authorized, no skip/xfail/delete).

## Check 9 — Scope (PASS with noted pre-existing dirty worktree)

- No existing file modified by D7-E: the three implementation files are new untracked; `git diff --name-only` content changes are the 8 pre-existing NB-Polar/SOP/memory/V35 files above, none in `comparison_bench/src|tests|scripts` D7-E scope and none containing D7-E logic. Explicit-path staging only; no clean/reset/checkout/stash/rebase/amend/broad stage performed.
- No flooding/warm-start/alternating/feedback/estimator-tuning code or tokens: `grep -i r1d|phase|tuning|alternat|feedback|flooding` in core+runner returns only the provenance-gate comment line and no code; `warm_beliefs` appears only as `warm_beliefs=None` ×2 in the frozen cold bind (+2 in `_DECODER_IDS` strings) with `test_m03` pinning `warm_beliefs=None` and `test_x04` forbidding warm/flooding tokens. No `r1d` (case-insensitive) in core/runner.
- No D7-E/R1d roots: both globs absent before and after reviewer runs.
- No authorization changes: D7-E `cycle_state.yaml` all auth false (`d7e_execution_authorized/decoder_executed/result_created/.../plan_accepted/g1/g2` false), `D7_E_IMPLEMENTATION_REVIEW_PENDING`, `D7_E_NOT_EXECUTED`; `test_x05` re-pins the same keys.
- Frozen baseline untouched: `src/`/`experiments/`/`tools/` not in diff; D7-C/D7-D import/behavior independence pinned (`test_x03`: no `schedule_discriminator` import, `d7c.MAX_CALLS/CONDITIONS/LAMBDA/frozen_identities` unchanged, marginal priors equal).

## Discrepancies / non-blocking suggestions

- None blocking. Two documentation-completeness notes (do not require rework):
  1. D7-E module docstring documents only the 2 D7-D deselected IDs; the 2 D7-B + 1 D7-C `-k` IDs are recorded exactly in `test_x06b`/`x06c` asserts but their reasons live in the prior BP implementation/readiness reviews cited above. Consider copying the one-line reason into the D7-E docstring at the next milestone review for self-containment.
  2. Worktree carries the expected pre-existing dirty/CRLF + NB-Polar/SOP/V35 content deltas noted above; no action (packet §1 says preserve them). Recommend batching any docs-only reconciliation into the next milestone review per AGENTS.md §10.1(4), not a D7-E rework.

## Checklist

- [x] Matches OpenSpec spec (frozen R14 prereg/packet/spec/tasks + §§3-5 verbatim in substance; matrix/formulas/labels/terminals/budgets/schema all pinned above)
- [x] Tests pass (reviewer reproduced: 25 passed total — 22 + 1 + 1 + 1 across four fresh-basetemp `-p no:cacheprovider` processes; inner 23/14/29/19+1/28+2/165)
- [x] No scope creep (three new files only; no flooding/warm-start/alternating/feedback/tuning/r1d/phase; no existing-file D7-E edit; no roots; no auth change)
- [ ] docs/decision-log.md or docs/troubleshooting.md needs update? No — D7-E remains frozen/unauthorized/unexecuted; state/roadmap updates belong to R20-R21 closeout after pre-execute, not this implementation review.

## Return delta

- verdict: `D7_E_IMPLEMENTATION_REVIEW_PASS`
- per-check evidence: §§1-9 above (formulas/provenance/pairing/no-oracle/thresholds/estimator/schema/tests/scope all PASS with line/function/test-ID pins)
- literal test counts reproduced: `22 passed, 3 deselected` (non-x06) + `1 passed` each for x06a/x06b/x06c = `25 passed`; inner `23 passed` (BP) / `14 passed` (D7-A) / `29 passed` (D7-B) / `19 passed + 1 deselected` (D7-C) / `28 passed + 2 deselected` (D7-D) / `165 passed` (D5)
- deselection adjudication: 5 IDs (2 D7-D + 2 D7-B + 1 D7-C) each reproduced as pre-existing baseline FAIL with identical root/state cause, documented (D7-E docstring for D7-D pair; prior BP reviews for all five), no skip/xfail/delete — PASS-neutral
- discrepancies: pre-existing 8-file content-dirty worktree (NB-Polar/SOP/memory/V35, preserved per packet) + docstring self-containment note — both non-blocking, no rework
- review doc path: `docs/research_cycles/V72P2D7-GF32-CROSS-LAYER-DISCRIMINATOR/D7_E_IMPLEMENTATION_REVIEW_R1.md`
