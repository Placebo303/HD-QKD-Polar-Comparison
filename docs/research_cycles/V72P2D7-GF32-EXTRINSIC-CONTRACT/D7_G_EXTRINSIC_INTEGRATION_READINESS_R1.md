# D7-G code-factor extrinsic integration-readiness review R1 (F02)

- Authority: `.workbuddy/tasks/D7_F_ACCEPT_D7_G_EXTRINSIC_CONTRACT_READINESS_R1_TASK_PACKET.md` §9 F02 only.
- Reviewer context: independent of implementer and F01 reviewer; review-only; sole write is this file. No commits, no edits beyond this file, no Model-F/real reads, no roots/UUID, no production/scientific runs (own test runs: existing tiny-fixture suites only, separate processes, fresh `/tmp/f02-*` basetemps, `-p no:cacheprovider`, repo venv).
- Branch: `formal-ir-v72p1-addendum-clean`; HEAD `08987c6d6d5bd8b775a47b305eebbd599e57e72f` (`docs(d7-g): freeze code-factor extrinsic contract`).
- F01 gate: `D7_G_EXTRINSIC_CONTRACT_REVIEW_R1.md` verdict `D7_G_EXTRINSIC_CONTRACT_REVIEW_PASS` present (92 lines, ends with explicit PASS + "does not authorize D7-H"). STOP-gate cleared.
- Under review (uncommitted): `comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py` (tracked mod, +127/−0), `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_extrinsic_oracle.py` (new untracked), `comparison_bench/tests/test_v72p2d7_gf32_extrinsic_contract.py` (new untracked).

## 0. Scope / HEAD verification (STOP-gate) — PASS

- `git rev-parse HEAD` = `08987c6d...` on branch `formal-ir-v72p1-addendum-clean`. PASS.
- `git diff HEAD --numstat -- .../v35_algorithm_development.py` = `127 0` (purely additive; zero deletions). PASS.
- `git diff HEAD --name-only -- comparison_bench/src/comparison_bench/formal_ir/ comparison_bench/tests/` = only `v35_algorithm_development.py`; untracked in those dirs = the two new D7-G review files plus a pre-existing unrelated `v72p2d4_cal_gf32_model_rate_audit` pair (different change, no D7-G/H content, untouched by this review).
- Worktree carries out-of-scope tracked drift (CRLF line-ending noise across harness/docs/outputs) and many pre-existing untracked artifacts; none lies in the frozen D7-G file map and none was relied on. No STOP condition met.

## 1. API additive / backwards compatible — PASS (with PASS-neutral pin T1)

- `DecoderResult` (`v35_algorithm_development.py:660-669`): new fields `extrinsic_log_beliefs: Optional[np.ndarray] = None` (`:668`) and `extrinsic_provenance: Optional[str] = None` (`:669`) — both defaulted; field order appends after `belief_provenance`; first-6 fields and all existing parameter positions unchanged.
- Producer diff touches only the three existing row-layered return paths (`:842`, `:897`, `:923` — it0 / converged / max-iter tail) plus flooding left on defaults (`:752`, `:770` carry no extrinsic kwargs); no signature change to `decode_row_layered_fftqspa` / `decode_damped_row_layered_fftqspa` / `decode_flooding_fftqspa`; no change to beliefs computation, stopping, iteration counts, `final_beliefs`, or `belief_provenance` mapping (matches F01 §4; diff is +127/−0).
- Construction sites (repo-wide `DecoderResult(` scan): only v35 itself (5 sites, existing args in unchanged order) and tests. `test_v39_lanec_robustness.py:928` imports v35's `DecoderResult` and constructs it with 6 positional args (no provenance/extrinsic) — still valid by inspection (v39 suite itself not run: session `real_counts` fixture = real data, prohibited). BP-suite legacy 6-arg construction (`test_v72p2d7_bp_belief_provenance.py:133`) executes fine in my rerun (22 passed around it).
- Own reruns (separate processes, fresh basetemps, `-p no:cacheprovider`):
  - D7-A `test_v72p2d7_gf32_decoder_certification.py` → **14 passed** (`/tmp/f02-d7a`).
  - BP `test_v72p2d6_bp_provenance_compat.py` → **14 passed** (`/tmp/f02-bp2`).
  - BP `test_v72p2d7_bp_belief_provenance.py` → **22 passed, 1 failed** (`/tmp/f02-bp1`): sole failure is `test_pv_05_additive_field_and_numerical_equivalence`, the field-list pin expecting OLD + `["belief_provenance"]` — the direct, expected consequence of the frozen additive-field contract (prereg §1: "additive optional fields only"). Construction/compat and numeric assertions around it pass. PASS-neutral (concurs F01-T1).
  - D7-E `test_v72p2d7_gf32_cross_layer_discriminator.py` → **38 passed, 2 failed** (`/tmp/f02-d7e`): `test_x06a_bp_and_d7a_regressions` fails only transitively (it shells the BP suite, which hits the same PV-05 pin — quoted output shows the inner `1 failed, 22 passed` on PV-05); `test_x05_protected_state_and_no_production_read` fails on a suite precondition (`WS.glob(OUT_ROOT_PREFIX+"*") == []`) because this worktree already contains the protected pre-existing D7-E root `workspace/d7_e_cross_layer_discriminator_faa5dc1c-…` (mtime 2026-09-11, predates this review; `git status` clean for all five `workspace/d7_*` roots) — environmental, not a behavior change. Both non-blocking; see §6.
  - New-contract compat subset: `test_ext_05a_tokens_fields_and_positional_compat` + `test_ext_05a_flooding_extrinsic_deferred_outputs_unchanged` → **2 passed** (`/tmp/f02-ext05a`); `test_ext_06_static_inventory_no_production_extrinsic_consumer` + `test_ext_06_no_d7h_no_new_roots_no_forbidden_reads` + `test_ext_06_consumer_adapters_ignore_new_fields` + `test_ext_06_oracle_import_graph_independence` → **4 passed** (`/tmp/f02-ext06`).

## 2. Existing cross-layer consumers remain on prior contracts — PASS (one non-blocking inventory-list gap, O1)

- Precise repo scan `rg "extrinsic_log_beliefs|extrinsic_provenance|require_check_extrinsic|UnusableExtrinsicError|EXTRINSIC_CHECK_EXTRINSIC|EXTRINSIC_NO_CHECK|EXTRINSIC_WARM_START|_build_check_extrinsic" comparison_bench/src/` excluding `v35_algorithm_development.py` + `v72p2d7_gf32_extrinsic_oracle.py` → **zero hits** (exit 1). No production consumer references the new field/helper. (Generic-word hits such as `local_factor_extrinsic`, ACE `check_extrinsic_score`, V→C comments are legacy unrelated senses, not the D7-G contract namespace.)
- Consumer inventory (all verified on prior `final_beliefs` / `belief_provenance` + `require_check_updated_provenance` contract; none touches extrinsic):

| # | Consumer (packet role) | File:line evidence (prior-contract use) | Extrinsic refs |
|---|---|---|---|
| 1 | D5 `_run_layered_block` | `v72p2d5_gf32_rate_mother.py:1371-1380` gate (`_require_check_updated_provenance(prov1, …L1->L2 APP prior…)`); beliefs forwarded at `:1053-1054`, `:1111-1112`, `:1667-1669`, `:2510-2511` via `final_beliefs`/`belief_provenance` | none |
| 2 | v72p2d3 contrast path | `v72p2d3_gf32_contrast.py:669,692,728` (`belief_provenance` reads), `:1361-1366` frozen `q=softmax(L1 final_beliefs)` recombination | none |
| 3 | Shell adapter | `methods/nbldpc_shell_adapter.py:195,203` imports `require_check_updated_provenance`; `:256-260` gates on `belief_provenance`, then `q = softmax_beliefs(res_l1.final_beliefs)` | none |
| 4 | V64 runner | `scripts/execute_v64_fresh_verify.py` (in inventory list; scan-clean). Note `formal_ir/v64_full_symbol_verification.py` carries zero `final_beliefs`/`belief_provenance`/`softmax` refs — not a belief consumer at all | none |
| 5-14 | v45–v55 guarded entries | `v45:1049-1050`, `v46:1169-1170`, `v47:1094-1095`, `v48:1173-1174`, `v50:1457-1458`, `v51:1339-1340`, `v52:1221-1222`, `v53:1268-1269`, `v54:1317-1321`, `v55:1431-1435` — each `require_check_updated_provenance(getattr(res, "belief_provenance", None))` then `softmax_beliefs(….final_beliefs)` | none |
| 15 | D6 R1d runner | `formal_ir/v72p2d6_gf32_graph_mother.py` carries zero `final_beliefs`/`belief_provenance`/`require_check_updated`/`softmax` refs — graph-construction module, not a belief consumer | none |
| 16 | D7-E module | `v72p2d7_gf32_cross_layer_discriminator.py:511` (`_require_check_updated_provenance`), `:521-525` `_parse`-style `belief_provenance` extraction | none |
| 17 | D7-F module | `v72p2d7_gf32_reverse_order_discriminator.py:428-438` (`require_check_updated` alias + `belief_provenance` extraction at `:434-438`) | none |

- Inventory-test genuineness: `test_ext_06_static_inventory_no_production_extrinsic_consumer` pins `_PRODUCTION_INTERFACE_FILES` (v35, D5, v72p2d3, v45/46/47/48/50/51/52/53/54/55, shell adapter, `scripts/execute_v64_fresh_verify.py`) and asserts six D7-G needles absent from each (v35 exempted as producer). Demonstrated genuine for listed files: clean scan of `nbldpc_shell_adapter.py` reports NONE, while the same scan logic on an in-memory copy with a simulated `require_check_extrinsic` import raises `('nbldpc_shell_adapter.py', 'require_check_extrinsic')` — a switched consumer WOULD fail the test. **O1 (non-blocking):** the pinned list omits D6 (`v72p2d6_gf32_graph_mother.py`) and the D7-E/F/C discriminator modules; a switch inside one of those files would not trip this test. No such switch exists today (own zero-hit scan above covers them), so readiness is unaffected — recommend extending the list in a future touch.

## 3. No D7-H runner / root / UUID / authorization — PASS

- `rg "d7_h" --glob '*.py' .` (excl. `.venv`, `__pycache__`) → only the new contract test's own prohibition needles (`test_…_extrinsic_contract.py:754,759-760`); zero production hits.
- `rg -i "alternating" comparison_bench/src/comparison_bench/ --glob '*.py'` → 7 hits, all legacy unrelated senses: `nonbinary_v5d_post.py:7,178` (alternating projection, ADMM sense) and `nonbinary_v30.py:112,520-524,571` / `v31:477` (`tanner6_alternating_product`, cycle-product sense). No alternating cross-layer execution path.
- Roots: `workspace/d7_h_*` and `workspace/d7_g_*` both absent (before and after my runs); `FORMAL/*d7_h*` and `FORMAL/*alternating*` both empty; existing `workspace/d7_b/c/d/e/f` roots untouched (see §4).
- UUID: PCRE `[0-9a-f]{8}-…` scan over v35 diff file, oracle, contract test, and the whole `V72P2D7-GF32-EXTRINSIC-CONTRACT/` dir → zero hits (the only "UUID" mentions are F01 prose stating none exists). No new identifier minted.
- Auth: D7-G `cycle_state.yaml` — `implementation_authorized/d7g_execution_authorized/decoder_executed/result_created/formal_execution_authorized/synthetic_execution_authorized/real_execution_authorized/scientific_promotion/g1_authorized/g2_authorized` all false, attempts zero, state `D7_G_FROZEN_NOT_AUTHORIZED_NOT_EXECUTED`. Neighbors all false: reverse-order (D7-F) `…_authorized: false`, cross-layer (D7-E) `…_authorized: false`, easy-regime/schedule/bidirectional preregs `implementation_authorized: false` + `g1/g2_authorized: false`.

## 4. No scientific artifacts read/written — PASS

- Workspace before/after (my runs used only `/tmp/f02-*` basetemps): identical set `d7_b/d7_c/d7_d/d7_e/d7_f`, no `d7_g_*`, no `d7_h_*`. `git status --porcelain` over all five `workspace/d7_*` roots → empty (clean); `git ls-files workspace/ | grep d7_` = 32 tracked entries; no `d7_g`/`d7_h` root tracked (the only `d7_g` substring hits are `v72p2d7_*` module filenames themselves).
- Protected D7-B/C/D/E/F roots metadata unchanged; my runs wrote nothing under `workspace/` or `comparison_bench/outputs_comparison/`.
- Model-F content: new-code diff (`git diff HEAD -- v35…`) contains zero `model/real/cal_/val_/raw/void` lines; oracle + contract-test scan for `Model-F/CAL_/VAL_/real/raw/VOID/--phase` hits only the test file's own header/prohibition comments and split-needle self-scan guards — no root binding, no artifact read. The x05 failure above is the pre-existing D7-E root tripping a clean-workspace precondition, not a read of its contents by new code.

## 5. Future D7-H can consume only explicit CHECK_EXTRINSIC; no posterior fallback — PASS

- Helper strictness (`v35:617-656`): first statement rejects any `extrinsic_provenance != EXTRINSIC_CHECK_EXTRINSIC` (`:630-633`) — covers `NO_CHECK_EVIDENCE`, `WARM_START_UNSPECIFIED`, `None`/missing/unknown/bogus (incl. cross-namespace `CHECK_UPDATED`, asserted in EXT-05c `:636-638`); then rejects `None` arrays (`:634-637`), non-convertible (`:638-642`), wrong 2-D/shape (`:643-646`), row-count mismatch (`:647-650`), and nonfinite (`:651-653`) — all before any softmax/prior computation (`:654-656`). Rejection matrix covered by `test_ext_05c_helper_rejects_unusable_provenance` (parametrized), `…_bad_arrays`, `…_row_count_mismatch`, `test_ext_05c_helper_accepts_only_explicit_check_extrinsic`, plus it0/warm rejection in D04.4.
- No posterior→extrinsic fallback exists: the only extrinsic-from-posterior subtraction in production is the decoder-carried producer `_build_check_extrinsic_log_beliefs` (v35:593-614) operating on the exact internal `log_input_prior` array (same-array `beliefs.copy()`, `:816`, no duplicated cleaning rule). `require_check_updated_provenance` (`:540-551`) is a pure token comparison — no array math, no prior reconstruction. All `softmax_beliefs*` helpers (v45–v55, v72p2d3 `:368`) are forward posterior→distribution maps for the frozen one-pass APP path; none subtracts a prior or fabricates an extrinsic token. No helper upgrades `None`/legacy to `CHECK_EXTRINSIC`.
- OpenSpec/prereg record the constraint for D7-H: `spec.md` "Existing posterior semantics remain unchanged" — "No consumer SHALL infer extrinsic by subtracting an unknown/reconstructed prior, and NO consumer SHALL auto-switch"; "Independent certification before alternating execution" + "D7-H stays unfrozen and unauthorized" requirements; `design.md:43-48` (never infer from `belief_provenance`/`iterations`), `:81-87` (helper accepts only explicit `CHECK_EXTRINSIC`; not wired into D5/D6/D7), `:140-141` compatibility rows 4–5 (no auto-switch; inventory must fail on unwarranted use), `:148` (rejected: "Reconstruct prior by re-cleaning caller-side priors"); `D7_G_PREREG_R1.md` §1 (compatibility + "NO consumer auto-switches… static inventory test must fail…", "D7-H remains not frozen / not authorized") and §5/§7 (no multi-round alternating until certification; STOP rule).

## 6. Discrepancies / observations (all non-blocking)

- **T1 (concur F01, PASS-neutral):** `test_pv_05_additive_field_and_numerical_equivalence` fails on the field-list pin only; the additive fields are the frozen contract, and EXT-05a (new pin) passes 2/2 in my rerun.
- **X05 (environmental, pre-existing):** D7-E `test_x05_…` expects a clean workspace but this worktree holds the protected D7-E root; unrelated to the D7-G change (root mtime predates review, status clean, my runs wrote nothing there).
- **X06a (transitive):** D7-E `test_x06a_…` shells the BP suite and inherits T1; no independent behavior failure (38/40 D7-E tests pass, incl. all functional discriminator tests).
- **O1:** inventory file list omits D6 + D7 discriminator modules (see §2 table rows 15–17); covered today by the independent zero-hit scan, but extend the list in a future touch.
- **O2 (hygiene):** out-of-scope CRLF drift + unrelated untracked `v72p2d4` pair + many pre-existing untracked artifacts; none in the D7-G file map.

## Verdict

`D7_G_EXTRINSIC_INTEGRATION_READINESS_PASS`

This verdict covers F02 integration readiness only: the API is additive and backwards compatible, all existing cross-layer consumers remain on their prior contracts, no D7-H runner/root/UUID/authorization exists, no scientific artifacts were read or written, and a future D7-H can consume only explicit `CHECK_EXTRINSIC` with no posterior-fallback path. Neither this review nor F01 authorizes D7-H, any alternating execution, or any promotion.

## Return delta (summary)

1. Scope/HEAD: `08987c6` + only the three review paths (v35 +127/−0; two new files); F01 PASS present; STOP-gate cleared.
2. Check 1: DecoderResult fields defaulted (`:668-669`); construction sites enumerated (v35×5 + tests; v39 6-arg import-construction valid); own counts — D7-A 14/14, BP-compat 14/14, BP-belief 22+1-pin, D7-E 38+2 (1 transitive pin, 1 env precondition), EXT-05a 2/2, EXT-06 subset 4/4.
3. Check 2: 17-row consumer table with file:line verdicts; precise-grep zero extrinsic refs outside v35+oracle; inventory genuineness demonstrated by simulated-switch failure; O1 list-gap noted.
4. Check 3: zero `d7_h` production hits; `alternating` hits legacy-only; no `workspace/d7_g|h_*`; no `FORMAL/*d7_h|alternating*`; UUID regex zero; all auth false (D7-G + 5 neighbors).
5. Check 4: workspace globs identical before/after (b/c/d/e/f only); protected roots `git status` clean; Model-F scan clean; runs confined to `/tmp/f02-*` basetemps.
6. Check 5: helper fail-closed code cites (`:630-656`) + EXT-05c matrix; no fallback path (token-gate + forward-only softmax helpers; sole subtraction is the carried-prior producer); OpenSpec/prereg/design constraint cites.
7. Discrepancies: T1/X05/X06a/O1/O2, all non-blocking.
8. Review doc: `docs/research_cycles/V72P2D7-GF32-EXTRINSIC-CONTRACT/D7_G_EXTRINSIC_INTEGRATION_READINESS_R1.md`. No commits, no pushes.
