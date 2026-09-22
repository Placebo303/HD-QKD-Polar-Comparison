# V72P2D5-GF32-RATE-MOTHER -- Structure Implementation Review (FORMAL VERDICT)

status: REVIEW_COMPLETE_INDEPENDENT_VERDICT
verdict: PASS
reviewer: reviewer-go (independent, not coder-fast)
scope: structure runner delta only (orchestrator, hard-gate fix, 24-field freeze, preflight, attempt semantics, writer, CLI wiring, version binding)
HEAD reviewed: 737f731702106bacff3c509a3f877a8b037f1434
date: 2026-09-05

Coder must not self-grant -- this file is the grant. Prior placeholder WITHHELD is superseded by this PASS. No execution is authorized by this file; next gate is STRUCTURE_PRE_EXECUTE_REVIEW.

## 1. CLI structure branch (PASS)

File: scripts/v72p2d5_gf32_rate_mother.py

- Line 24-25: STRUCTURE_OUT_DIR = (ROOT / workspace / v72p2d5_structure / 20260905_r2), ROOT resolved from CLI file location via _HERE.parents[1]. No absolute paths, no D-drive string, no slash-rooted literal.
- Line 62: build_parser has exactly one add_argument (--phase). No new CLI params.
- Line 74-76: is_phase_authorized gate runs first and refuses before any work (return 3).
- Line 78-80: structure branch calls _RUNNERS[structure](authorized=True, out_dir=STRUCTURE_OUT_DIR). Auth-first preserved; call happens only after gate passes.
- Line 81-82: other phases (g0, p0-cost, g1, g2) still call with authorized=True only, no out_dir. Other phases unaffected.
- Frozen out_dir equals core formal root: STRUCTURE_OUT_DIR == ROOT / workspace / v72p2d5_structure / 20260905_r2 == ROOT / STRUCTURE_FORMAL_ROOT (core line 1207). Verified by T2_18 assertion str(seen out_dir) == str(ROOT / mod.STRUCTURE_FORMAL_ROOT).

## 2. T2_17 unauthorized (PASS)

Test: comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py line 1308 test_T2_17_cli_unauthorized_creates_no_formal_dir. Collected and PASSED.

- Unauthorized state only: _load_state patched to structure_execution_authorized False. Real CLI authorized path NOT run.
- Runner, preflight, build, audit, write counts all 0: counts == runner 0, preflight 0, build 0, audit 0, write 0.
- Formal dir not created: not (ROOT / mod.STRUCTURE_FORMAL_ROOT).exists().
- Tmp empty: list(tmp_path.rglob(*)) == [].
- CLI return 3 (refuse before any work).

## 3. T2_18 fake authorized (PASS)

Test: comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py line 1353 test_T2_18_cli_structure_frozen_out_dir_fake_files. Collected and PASSED.

- Real CLI authorized path NOT run: spy captures frozen out_dir value, then file creation redirected to tmp redir; formal root untouched. Uses _SeqFake(l1_pass True, l2_pass True) plus real_seq with injected fake build, audit, preflight fns.
- Orchestrator receives exact out_dir: seen authorized is True, str(seen out_dir) == str(ROOT / workspace / v72p2d5_structure / 20260905_r2) == str(ROOT / mod.STRUCTURE_FORMAL_ROOT).
- Exactly 4 files: sorted(p.name for p in redir.iterdir()) == sorted(mod.STRUCTURE_EVIDENCE_FILES) == results.json, table.csv, report.md, execution_summary.json.
- Existing-dir refuses: writer FileExistsError path preserved (core line 1460-1462); CLI refuse path returns nonzero, no swallow (addendum section 11, core _structure_terminal still writes via write fn which raises if exists).
- Formal root still absent: not (ROOT / mod.STRUCTURE_FORMAL_ROOT).exists() after fake run.
- Other phases unaffected: g0 spy receives authorized True and out_dir not in gseen.

## 4. Prior B1-B8 spot-check (PASS, core untouched so preserved)

Core file: comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py, git diff vs 737f7317 empty (clean).

- Hard-gate 11: audit_prefix passed conjuncts at core line 743-747 count 11 (rank==k, zero_rows==0, zero_cols==0, isolated==0, comp_count==1, largest_frac==1.0, dup==0, vals_ok, deg_min>=2, base_dup==0, triple_dup==0).
- 24-field schema: audit_prefix return dict has 24 keys, verified by python count 24 (prefix_rows, total_edges, column_degree_full, rank, zero_rows, zero_columns, variable_degree_min, variable_degree_median, variable_degree_max, degree1_variables, degree2_variables, degree3_variables, connected_components, largest_component_fraction, isolated_variables, row_degree_histogram, four_cycles, four_cycle_variable_incidence_max, duplicate_projective_columns, base_pair_duplicates, support_triple_duplicates, coefficients_nonzero, passed, status). T2_16 frozen 24 still green within 78-pass suite.
- Preflight formula and budget: core line 1210-1212 budgets single 900.0, total 1800.0, rss 2 GiB; line 1218-1255 extrapolate_structure_cost frozen formula edge_scale N/proxy_n, rank_scale (M_MAX/proxy_m) squared times edge, single max(per-layer build) + 4 prefixes rank, total both builds + 8 prefixes rank; line 1258-1312 preflight small fixture (12,10,7) plus n<=256 proxy (64,64,48) only, never builds full 1000x1024 mother, preflight never counts as attempt.
- Attempt semantics: core line 1335 docstring plus line 1371 attempts 0 to 1 immediately before first full L1 builder call; each layer built at most once; L1 hard fail stops with L2 never built; exceptions yield STRUCTURE_BLOCKED completed 0; audit-complete hard fails yield completed 1.
- Writer 4-file scalars-only: core line 1208 STRUCTURE_EVIDENCE_FILES 4-tuple, line 1449-1550 write_structure_evidence refuses if out_dir exists (FileExistsError), mkdir parents, writes exactly results.json, table.csv, report.md, execution_summary.json; only scalars plus small per-prefix row-degree histograms; full mothers, supports, coefficients, priors, syndromes, decoder messages, digests, absolute paths never written.
- No retry, family, reseed: rg on core plus CLI finds only docstring line 1338 (seeds, order, family left unchanged on failure) and no retry loop, no reseed logic, no family switch. Failures stop sequence, no second attempt.
- No hash or tag: rg finds only line 1454 docstring (digests never written); no sha256, md5, checksum, digest code; no tag bits.

Full 78-test suite green confirms no prior regression.

## 5. No core modification (PASS)

- git rev-parse HEAD == 737f731702106bacff3c509a3f877a8b037f1434 (matches claimed binding).
- git diff --name-only -- comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py empty.
- git diff 737f7317 -- same core path empty. Core untouched.

## 6. No execution (PASS)

- cycle_state.yaml: structure_execution_authorized false, g0 false, p0-cost false, g1 false, g2 false, synthetic false, real false, formal false; decoder_executed false; full_mother_built false; cal_rows_read 0; val_rows_read 0.
- Test-Path workspace/v72p2d5_structure/20260905_r2 False (relative and absolute D path both False). Test-Path workspace/v72p2d5_structure False (parent absent).
- Tests used tmp, spy, _SeqFake; real CLI authorized path NOT run; no full mother built; no decoder called (structure decoder_calls 0); no CAL or VAL read.
- No formal root created by reviewer: reviewer ran only read-only plus rg plus py_compile plus pytest small-fake; did not build full mother, did not run real --phase structure authorized path, did not call decoder, did not read CAL or VAL, did not create formal root.

## 7. py_compile plus pytest (PASS)

- python -m py_compile scripts/v72p2d5_gf32_rate_mother.py plus core plus test file: PY_COMPILE_PASS.
- python -m pytest comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py -p no:cacheprovider -q: 78 passed in 2.01s (76 prior plus T2_17 plus T2_18).
- Focused: -k T2_17 or T2_18: 2 passed, 76 deselected.

## 8. cycle_state binding (PASS)

File: docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/cycle_state.yaml

- structure_runner_implementation: 737f731702106bacff3c509a3f877a8b037f1434 (was UNCOMMITTED_CANDIDATE, now pinned).
- accepted_r2_implementation stays d39b5caec5560d96991b8747bfc12f473e2fe776.
- All execution authorizations false (see section 6).
- next_gate: STRUCTURE_PRE_EXECUTE_REVIEW (was STRUCTURE_EXECUTION_PACKET_REVIEW).
- No auth change: implementation-only round, no execution granted.

## DECISION: PASS

The CLI fix is minimal and correct, auth-first preserved, frozen out_dir wiring exact, other phases unaffected, T2_17 and T2_18 prove unauthorized-noop plus fake-authorized file semantics without touching the formal root, B1-B8 preserved, core untouched at 737f7317, no execution occurred, py_compile plus 78 tests green, binding correct.

Next: STRUCTURE_PRE_EXECUTE_REVIEW before any formal --phase structure execution. Do not execute formal structure, G0, P0-cost, G1, G2 without independent pre-EXECUTE authorization on the exact implementation SHA.

Scope note (non-blocking): dirty worktree contains unrelated pre-existing changes (AGENT_PROJECT_MEMORY.md, docs/decision-log.md R1 and decoupling entries, many untracked comparison outputs). They are outside this structure-runner delta and were not reviewed here. Recommend human review of worktree hygiene before any commit, but they do not block this PASS. If change is large or complex in full-worktree sense, recommend human review before push.
