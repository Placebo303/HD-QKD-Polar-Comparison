# D7-B layer-interface correction proposal independent review R1

Verdict: D7_B_LAYER_INTERFACE_CORRECTION_PROPOSAL_PASS_D7_C_NONBLOCKING

- Packet: `.workbuddy/tasks/D7_C_BIDIRECTIONAL_ORACLE_FREEZE_IMPLEMENT_PRE_EXECUTE_A1_TASK_PACKET.md` §A1.3 (sole allowed PASS token; A1 supersedes R1 on conflict).
- Reviewed artifacts (untracked at review time, unmodified by reviewer): `openspec/changes/v72p2d7-layer-interface-belief-provenance/` (proposal.md, design.md, tasks.md, `specs/gf32-layer-interface-belief-provenance/spec.md`) and `docs/research_cycles/V72P2D7-GF32-EASY-REGIME/D7_B_LAYER_INTERFACE_CORRECTION_PROPOSAL_R1.md`.
- Method: independent re-open of v35/D5/D7-B/sibling/V64 source at HEAD `212f69ba`; independent repo-wide `final_beliefs` sweep; re-stat and re-grep side-effect checks. Zero decoder bindings/calls, zero Model-F binary content (no Model-F read of any kind), zero root/workspace writes, zero commits/pushes. The only file written by this review is this document.

## 0. Scope and what was independently done

Commands (all read-only; run from repo root unless noted):
- `grep -rn "final_beliefs" --include="*.py" comparison_bench/src scripts tools src experiments analysis` → 44 hits / 17 files; `grep -rn "final_beliefs" --include="*.py" .` excluding `.git/` and `workspace/` → 89 hits / 30 files.
- guard sweep: `grep -nE "it1|iterations" <consumer files> | grep -E "== ?0|!= ?0|> ?0|< ?1|<= ?0|>= ?1"` → zero matches.
- `grep -rn "belief_provenance|PRIOR_ONLY|CHECK_UPDATED|WARM_START_UNSPECIFIED" --include="*.py" comparison_bench/src scripts tools src experiments comparison_bench/tests` → exit 1, zero hits (nothing implemented).
- `find comparison_bench/src scripts src experiments tools -type f -name '*.py' -newer docs/research_cycles/V72P2D7-GF32-EASY-REGIME/D7_B_LAYER_INTERFACE_CORRECTION_PROPOSAL_R1.md` → zero hits.
- `git diff -- comparison_bench/src scripts src experiments tools | grep -c "belief_provenance|PRIOR_ONLY|CHECK_UPDATED|WARM_START"` → 0.
- `stat` on the five artifacts; `ls -la` on the D7-B R2 root; `find workspace -maxdepth 1 -name "d7_c*"` → 0; `find workspace -mindepth 1 -maxdepth 1 -newermt "2026-09-10 22:00:00"` → empty.
- Files opened (20 distinct): the two task packets; `D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT_R1.md`; `D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT_REVIEW_R1.md`; the five Phase-P artifacts; `v35_algorithm_development.py`; `v72p2d5_gf32_rate_mother.py`; `v72p2d7_gf32_easy_regime.py`; `v72p2d3_gf32_contrast.py`; `nonbinary_v10_fftqspa.py`; `v45_l1_app_soft_transfer.py`; `v54_two_stage_incremental_l2_rescue.py`; `methods/nbldpc_shell_adapter.py`; `scripts/execute_v64_fresh_verify.py`; `test_v72p2d7_gf32_decoder_certification.py`; `cycle_state.yaml`. Eight further v45–v55 files (`v46/v47/v48/v50/v51/v52/v53/v55`) line-verified by grep.

## 1. Source-truth verification (claims vs. source, lines actually opened)

| # | Claim | File:lines opened | Result |
|---|---|---|---|
| i | Cold row-layered it0 return carries untouched floored/renormalized log-prior, zero check messages | v35 L659–665 (`beliefs = log(priors_clean)`, floor 1e-15 + renorm; warm copy at L660–661), L676–678 (`check_to_var` all zeros), L681 (`best_x = argmax`), L683–692 (`iterations=0`, `status="converged_exact"`, `final_beliefs=beliefs`) | Confirmed |
| i-b | Flooding has no it0 path; first return follows a full check-update round | v35 L529–633: loop `for it in range(1, max_iter+1)` L591; check updates + `beliefs` update L593–603; first return L607–616; max-iter return L626–633 | Confirmed |
| ii | No consumer guards `iterations == 0` | D5 `_run_layered_block` L1344 binds `it1`; used only in output `"iterations": it1+it2` L1356. Guard grep over v35/D5/v45–v55/v72p2d3/adapter/V64/D7-B → zero matches | Confirmed |
| iii | D5 forwards `softmax(final_beliefs)@P` unconditionally as APP | D5 L1344 `e1,s1,it1,f1,bel1 = _decode_block(...)`; L1348–1349 `bel = ...; q = _softmax_rows(bel)`; L1352 `prior_l2 = app_fed_l2_prior(p2, block["bob"], q)`. `_softmax_rows` L948–952; `app_fed_l2_prior` L353–375 (docstring L354 "Production L2 prior `q @ P` from L1 APP beliefs"; `einsum("nq,qnv->nv")` L374); `oracle_l2_prior` L378–397 (L381 production must use `app_fed_l2_prior`) | Confirmed |
| iv | `final_beliefs` is the current log-belief state, not a conditioned-posterior promise | v35 L519–526 `DecoderResult` is a bare dataclass (no conditioning promise); row-layered docstring L645–649 documents damping only; v72p2d3 L668–671 log-prior fallback idiom. No promise found anywhere | Confirmed (the "current log-belief" reading is established by the code paths, not by an explicit field docstring) |
| v | v35 `DecoderResult` has five return sites, all current log-beliefs | row-layered returns L683–692 / L729–736 / L740–747; flooding returns L609–616 / L626–633; damped variant delegates L750–766 | Confirmed |
| vi | D5 adapters are verbatim passthroughs | `historical_g0_decoder` L1085–1111 (dict L1106–1111, `warm_beliefs=None` L1103); `_bound_hist` L1616–1632 (dict L1627–1632, `warm_beliefs=None` L1624); `bind_historical_decoder` L2453–2475 (dict L2468–2473, `warm_beliefs=None` L2465); `_decode_block` extracts beliefs at L1053 and drops other result fields (L1038–1056) | Confirmed |
| vii | D7-B binds row-layered cold, damping 1.0, `warm_beliefs=None`, and consumes beliefs as claimed posterior | easy-regime L490–506 (`bind_historical_decoder` returns `v35.decode_row_layered_fftqspa`); L516–547 (`invoke_decoder`; positional call L520–524 with `1.0, None`; `final_beliefs` at L538); L554–578 (`posterior_stats`: prob-like passthrough L563–565 else `_softmax_rows`); L627–634 (exact-posterior max-abs comparison; `POST_TOL = 1e-10` at L44) | Confirmed |
| viii | Inventory discovery beyond D7-B review §2: V64 runner | `scripts/execute_v64_fresh_verify.py` L186 `res_l1 = decode_row_layered_fftqspa(...)`; L188 `q = softmax_beliefs(res_l1.final_beliefs)`; L192 `prior_l2 = get_l1_app_prior_l2(counts[src], bob_sym, q)` — unconditional L1→L2 APP, no iteration guard; header L1 "guarded runner" | Confirmed |
| ix | Sibling exclusion reason | `nonbinary_v10_fftqspa.py`: local var `final_beliefs` L444/L446 returned under dict key `"beliefs"` L450; `_belief_probabilities` L458–471 builds probability-domain beliefs from `log_prior + c2v`; no v35 `DecoderResult`/`final_beliefs` field | Confirmed (exclusion correct) |
| x | v45–v55 pattern + headers | v45 L8 "BP posterior / APP approximation", L1046 `q = softmax_beliefs(res.final_beliefs)`; v46 L8/L1166; v47 L7/L1091; v48 L1170; v50 L1454; v51 L1336; v52 L1218; v53 L1265; v54 L1314 + `get_l1_app_prior_l2` L432–451 (`out[i] = qi @ p_u2`); v55 L1428; shell adapter L254 → `get_l1_app_prior_l2` L259 | Confirmed |
| xi | v72p2d3 passthrough/fallback/recombination lines | v72p2d3 L668–671 (fake fallback `np.log(prior_p)`), L688–689 (production extraction), L720–721 (dict output "L1->L2 recombination input"), L1351–1352 (`q = softmax_beliefs_history(l1["final_beliefs"])` → `build_l2_prior_from_l1`) | Confirmed |

## 2. Consumer inventory result

- Repo sweep: 89 `final_beliefs` hits in 30 `.py` files (excluding `.git/`, `workspace/`). 17 production/interface files (44 hits): v35, D5 rate-mother, v45–v55 (10 files), `methods/nbldpc_shell_adapter.py`, `v72p2d7_gf32_easy_regime.py`, `v72p2d3_gf32_contrast.py`, `scripts/execute_v64_fresh_verify.py`, plus sibling `nonbinary_v10_fftqspa.py`. 13 test files (45 hits).
- Proposal inventory: 24 rows = 22 production/interface entries (rows 1–22, covering exactly those 16 production files + V64) + sibling exclusion (row 23) + test-only note (row 24). Count and files match my independent sweep exactly. No production consumer missing; no wrongly-included production consumer found.
- Extension check: no hits in `tools/`, `src/`, `experiments/`, `analysis/` (confirming R1 proposal §5 "no hits in analysis/"). The only V64 hit is `scripts/execute_v64_fresh_verify.py:188` as claimed.
- Test-only gap (non-blocking): row 24 names D7-A tests and D5/v45–v55 fakes but not `comparison_bench/tests/test_v39_lanec_robustness.py:934` (fake `final_beliefs=np.zeros((1024,32))`); still test-only, no production impact.

## 3. Eight A1.1 rulings compliance

| Ruling | Frozen location | Status |
|---|---|---|
| 1. v35 hard-decision stopping not redefined/patched | proposal L118; spec "Hard-decision semantics remain unchanged" L20–26 | Frozen |
| 2. `final_beliefs` = current log-belief, not inherently calibrated posterior | proposal L119–120; design L50–51 | Frozen |
| 3. cold zero-sweep return = `PRIOR_ONLY` | proposal L121; design L27–35; spec L6–9 | Frozen |
| 4. `PRIOR_ONLY` must not be labeled syndrome-conditioned APP | proposal L122; spec L45–51 | Frozen |
| 5. explicit provenance before cross-layer evidence | proposal L123–124; design L56–69; spec L28–43 | Frozen |
| 6. `iterations > 0` sufficient for ≥1 sweep, durable contract uses explicit field | proposal L125–127; design L36–40 | Frozen |
| 7. warm-start provenance separate, never guessed from iterations, out of scope | proposal L128–129; design L43–46; spec L15–18; tasks BP-06 | Frozen |
| 8. D7-C single-layer only, never feeds beliefs cross-layer | proposal L130–132; spec L69–75 | Frozen |

All eight present in substance in the proposal (with design/spec reinforcement); none diluted.

## 4. Enum / alternatives / acceptance tests / rules

- Enum: exactly `PRIOR_ONLY`, `CHECK_UPDATED`, `WARM_START_UNSPECIFIED` (proposal L139–146, L144–146 tokens table; design L8–12; spec L4). `PRIOR_ONLY_CURRENT_BELIEF` is a record/diagnostic label only (proposal L264–265; spec L46), not a fourth provenance token. `None`/absent = unspecified/legacy, never upgraded (design L14–16).
- Alternatives: A (provenance-only + fail-closed consumers), B (force ≥1 check sweep for conditioned APP), C (keep fallback but prohibit APP claims) in proposal L199–237, design L111–120, R1 doc §6 L148–164. Tradeoffs honest: A's cost (a `PRIOR_ONLY` stop cannot feed L2 at all); B's costs (touches stopping/schedule, needs separate frozen decision, still only approximation — TREE 0.00689 after one sweep, changes numerics vs historical); C unenforceable (silent `prior @ P` path stays live). Recommendation A, with B as a separately frozen future decision; C rejected as standalone. Matches A1.2 preferred recommendation.
- Acceptance tests: PV-01–PV-14 (proposal L243–275; R1 doc §7 L166–181). Concrete and testable: token mapping (PV-01–04), additive/no numeric change on frozen fixtures (PV-05), fail-closed on `PRIOR_ONLY`/missing/unknown (PV-06–08, spy/assert on `app_fed_l2_prior`/`get_l1_app_prior_l2`), conditioned pass-through reproduction (PV-09), diagnostic relabel rule (PV-10), adapter propagation (PV-11), no-retroactivity (PV-12), hard-decision-only consumers unaffected (PV-13), import-graph independence (PV-14).
- No-retroactivity rule explicit: proposal L56–59, L279–280; spec L53–59.
- Gating rule explicit: implementation mandatory before the next sequential/alternating/joint cross-layer APP run, not before D7-C single-layer oracle readiness/execution (proposal L281–290; design L71–85; spec L61–67; R1 doc §8 L183–194). D7-C must not import the future interface implementation (proposal L284–287; spec L67).

## 5. D7-C independence finding

From R1 packet §3.3 (L103–115), all four priors are pure functions of the accepted joint table and the generated truth symbols: `L1_MARGINAL = sum_u2 J[:,u2,b]`, `L1_ORACLE_U2 = J[:,u2_true,b]`, `L2_MARGINAL = sum_u1 J[u1,:,b]`, `L2_ORACLE_U1 = J[u1_true,:,b]` — no decoder-returned beliefs enter. §3.2 (L88–100) freezes exactly one single-layer decode per condition/block/f, cold, `max_iter=90`, damping 1.0, explicitly "no sequential L1→L2 APP and no feedback". §3.6 (L150–160) permits current-belief confidence/entropy only as an explicitly labeled diagnostic, with `beliefs_conditioned` derived from iterations and reviewed audit semantics, and never calls an iteration-0 prior a conditioned posterior; no raw beliefs are persisted. No D7-C path consumes `final_beliefs` as cross-layer APP.

Finding: the proposal's claim "D7-C requires no provenance interface" holds. The only iterations-derived label (`beliefs_conditioned`) is a per-call diagnostic label consistent with ruling 6 ("`iterations > 0` sufficient … in the current cold row-layered decoder") and does not require the deferred field; A1 §A1.4 C14's `PRIOR_ONLY_CURRENT_BELIEF` requirement covers the same boundary. No D7-C path was found that would depend on the deferred interface.

## 6. Side-effect / no-write verification

- Five new artifacts (mtime, +0800; newest = the R1 proposal doc at 22:12:18): `proposal.md` 2026-09-10 22:12:17.475705400 (21849 B), `design.md` 22:11:03.643109000 (8799 B), `tasks.md` 22:11:18.937257400 (3544 B), `spec.md` 22:11:34.166128200 (5491 B), `D7_B_LAYER_INTERFACE_CORRECTION_PROPOSAL_R1.md` 22:12:18.188435800 (13148 B).
- `find comparison_bench/src scripts src experiments tools -type f -name '*.py' -newer <newest artifact>` → **zero hits** (no production/source `.py` changed after the newest Phase-P artifact).
- `git diff` over `comparison_bench/src scripts src experiments tools` contains **zero** occurrences of the provenance tokens; sampled status-`M` files (e.g. `v35`, D5, `__init__.py`) show no text diff and mtimes 19:05 (pre-existing dirty-tree/CRLF artifacts; worktree reports 1970 porcelain entries).
- `git status --porcelain` for the two new paths shows only untracked additions: `?? openspec/changes/v72p2d7-layer-interface-belief-provenance/` (exactly 4 files: proposal, design, tasks, spec) and `?? docs/research_cycles/V72P2D7-GF32-EASY-REGIME/D7_B_LAYER_INTERFACE_CORRECTION_PROPOSAL_R1.md`.
- D7-B R2 root `workspace/d7_b_easy_regime_c605d1e6-8577-4c52-a865-12500fc8c964/`: exactly five files, zero subdirectories, sizes `command_log.txt` 111 B, `decoder_records.csv` 44743 B, `manifest.json` 1008 B, `report.md` 80 B, `summary.json` 449 B (all mtime Sep 10 20:33) — unchanged.
- `find workspace -maxdepth 1 -name "d7_c*"` → 0 (no `D7_C_BIDIRECTIONAL_ORACLE` root); no workspace top-level entry newer than `2026-09-10 22:00`; no `V72P2D7-GF32-BIDIRECTIONAL-ORACLE` cycle directory.
- Authorization: `cycle_state.yaml` L5–6 (`plan_accepted false`, `implementation_authorized false`), L11–14 (`formal/synthetic/real/false`, `scientific_promotion false`), L18–19 (`g1_authorized false`, `g2_authorized false`), `d7b_execution_authorized false` L6. All false. R1d/G2 remain unauthorized; D7-C execution not authorized.

## 7. Non-blocking observations and blocking assessment

Non-blocking observations:
1. The E09 defect chain (proposal L103–110; R1 doc §3 L76–81) cites `bel = ...` (L1348) and skips the `bel1 is None` branch (D5 L1345–1347), which forwards a uniform `q` to `app_fed_l2_prior` with no provenance either. Covered in substance by the fail-closed rule (absent provenance = not conditioned); no contract change needed.
2. The D5 citation range `L1341–1364` is correct; the earlier D7-B audit's "L1341–1360" was the same function truncated before the oracle branch (L1359–1363). No discrepancy of substance.
3. Design L50–53 licenses "syndrome-conditioned APP/conditioned posterior" for `CHECK_UPDATED`. The proposal's four-concept split (L61–76) and alternative B's tradeoff (L222–224: TREE 0.00689 after one sweep, "not a calibrated posterior") already separate conditioning from calibrated exactness; future implementation text should prefer "BP APP approximation" wording to avoid re-opening the D7-B metric confusion. Non-blocking.
4. Sibling exclusion nuance (non-blocking): the identifier `final_beliefs` does occur in `nonbinary_v10_fftqspa.py` as a local variable (L444/L446) but is returned under dict key `"beliefs"` (L450) and is probability-domain (`_belief_probabilities` L458–471); "no `final_beliefs` field" is accurate and the exclusion is correct.
5. Post-PASS follow-through (not a defect in the artifacts reviewed): `cycle_state.yaml` L20 still reads `next_gate: D7_B_LAYER_INTERFACE_CORRECTION_PROPOSAL`. Per A1.3, the Phase-P/gate-transition commit must set the documented next route to `D7_C_BIDIRECTIONAL_ORACLE_PACKET_FREEZE_INTERFACE_REWORK_DEFERRED` and record that interface implementation remains mandatory before any cross-layer APP route.
6. Test-only row 24 is a class-level note; it does not enumerate every test file (e.g. `test_v39` above). Production inventory is complete; no production/interface consumer is missed.

Blocking assessment: **none**. The proposal is source-accurate, enumerates the complete production consumer inventory, freezes all eight rulings, uses the exact enum tokens, trades off A/B/C honestly, recommends A with B deferred, provides concrete acceptance tests, and states the no-retroactivity and gating rules explicitly. The D7-C direct-prior construction is proven independent of the defective/deferred interface. The allowed PASS token is issued exactly once above; D7-C may proceed under the A1/R1 gates (its own OpenSpec, implementation, C01–C20, reviews, Pre-EXECUTE).

## 8. Review constraints note

Reviewer-side constraints honored: no production/source/config/test edit; no decoder binding or call; no Model-F binary content read (none read at all); no root/workspace write; no UUID generation; no `--phase`; no commit/add/push/stash/checkout/reset; no VOID reads. The only write performed is this review document. This review is independent of the proposal author and does not accept the deferred interface implementation; it only releases the D7-C non-blocking gate per A1.3.
