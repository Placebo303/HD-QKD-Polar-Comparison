# D7-E provenance-safe cross-layer discriminator — Pre-EXECUTE Review R1

- reviewer: independent WSL Pre-EXECUTE reviewer (separate context from implementer and R18 reviewer; did not write implementation)
- authority: `.workbuddy/tasks/D7_E_CROSS_LAYER_READINESS_AND_D6_COMPAT_R1_TASK_PACKET.md` §6/R19 only
- branch: `formal-ir-v72p1-addendum-clean`
- entry HEAD: `f82804f6736e1fdac41dc5b42931fd57aea580e9` (`f82804f6 docs(d7-e): freeze provenance-safe cross-layer discriminator`)
- date (UTC): 2026-09-11
- review-only: sole write is this file; no commits, no edits, no Model-F content, no decoder invocation beyond sentinel binding checks, no roots, no UUID
- scope: direct inspection/execution only; prior summaries never trusted

## Verdict

`D7_E_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`

It grants nothing. No execution authorized. No result accepted.

## Freeze / HEAD verification (pre-review gate)

- `git rev-parse HEAD` = `f82804f6736e1fdac41dc5b42931fd57aea580e9` — matches required prefix `f82804f6736e...`.
- `git log --oneline -1` = `f82804f6 docs(d7-e): freeze provenance-safe cross-layer discriminator`.
- `git diff --cached --name-only` = empty (no staging); no commits made by reviewer.
- `git show HEAD --stat` = 7 frozen files (proposal/design/spec/tasks + `D7_E_PREREG_R1.md` + `D7_E_EXECUTION_PACKET_R1.md` + `cycle_state.yaml`), 1012 insertions.
- `git ls-files --others --exclude-standard | grep -E "v72p2d7_gf32_cross_layer"` lists exactly three:
  - `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_cross_layer_discriminator.py`
  - `comparison_bench/tests/test_v72p2d7_gf32_cross_layer_discriminator.py`
  - `scripts/v72p2d7_gf32_cross_layer_discriminator.py`
  - `wc -l` = 1712 / 1540 / 104, matching R18 claim.
- Full worktree note (non-blocking, pre-existing, preserved per packet §1): `git status --porcelain | wc -l` = 1969 (many `M` stat-noise + many `??` pre-existing); `git diff --name-only` (content diff) = exactly 8 files (`AGENT_HANDOFF.md`, `AGENT_PROJECT_MEMORY.md`, `README.md`, `docs/CURRENT_MAINLINE.md`, `docs/decision-log.md`, `docs/research-cycle-sop.md`, `docs/v35-algorithm-development-report.md`, `workspace/pytest-evidence-test/output/expanded_evidence_manifest.json`); `git diff --numstat` confirms only those 8 have content deltas. None in D7-E scope, none containing D7-E logic. Fourth D7-E untracked file is `D7_E_IMPLEMENTATION_REVIEW_R1.md` (R18 output, expected); this file becomes the fifth. Scoped D7-E cleanliness holds.
- Post-check guard: no `workspace/d7_e_cross_layer_discriminator_*`, no `workspace/d6_graph_mother_r1d_*` before and after all checks (see §4/§8).

## 1. R18 implementation review PASS present and genuine — PASS

- Path `docs/research_cycles/V72P2D7-GF32-CROSS-LAYER-DISCRIMINATOR/D7_E_IMPLEMENTATION_REVIEW_R1.md` exists, 137 lines.
- Verdict line 17: `` `D7_E_IMPLEMENTATION_REVIEW_PASS` `` — exact token, no FAIL variant.
- Genuine (spot-verified, not trusted): HEAD prefix match, `wc -l` 1712/1540/104 reproduced, `git show HEAD --stat` 7 files reproduced, frozen constants and test counts independently re-checked in §§2/8 below. Reviewer identity states independent (did not write implementation), authority §6/R18 only, review-only with no commits/edits/decoder/Model-F/roots. One scoped rework allowed, none required — consistent with three untracked impl files still uncommitted.
- Literal: `22 passed, 3 deselected` + `1 passed` x3 = `25 passed` reproduced by R18; re-reproduced in §8.

## 2. Frozen 192-slot matrix/order (f→seed→6-call order), static only — PASS

- Static inspection of `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_cross_layer_discriminator.py`, no scientific-path execution:
  - Lines 79/84: `F_VALUES = d7c.F_VALUES`, `BLOCK_SEEDS = d7c.BLOCK_SEEDS` (narrow D7-C reuse, no copy).
  - D7-C source `v72p2d7_gf32_bidirectional_oracle.py:59,64,80-81`: `F_VALUES = (1.0, 1.2)`, `BLOCK_SEEDS = tuple(range(2026091300, 2026091316))` (16/f ascending), `MAX_ITER = 90`, `DAMPING_ALPHA = 1.0`, `L1_ROWS = {1.0: 49, 1.2: 59}`, `L2_ROWS = {1.0: 43, 1.2: 52}`.
  - Lines 95-108: `DIRECTIONS = ("L1_TO_L2", "L2_TO_L1")`, `ROLE_ORDER = ("SOURCE", "CONTROL", "TRANSFER")`, `SLOT_ROLE` six entries mapping each (direction,role) to (condition,layer).
  - Lines 110-112: `SLOT_COUNT = 192`, `MANDATORY_CALLS = 128`, `MAX_CALLS = 192`.
  - Lines 380-404 `frozen_slots()`: outer `for f in F_VALUES`, `for seed in BLOCK_SEEDS`, `for direction in DIRECTIONS`, `for role in ROLE_ORDER`; `slot_idx` 1-based; `rows = ROWS[layer][f]`, `n = N`. Per-(f,seed) six-tuple is exactly `L1_TO_L2_SOURCE_L1_MARGINAL`, `L1_TO_L2_TARGET_L2_CONTROL_MARGINAL`, `L1_TO_L2_TARGET_L2_TRANSFER`, `L2_TO_L1_SOURCE_L2_MARGINAL`, `L2_TO_L1_TARGET_L1_CONTROL_MARGINAL`, `L2_TO_L1_TARGET_L1_TRANSFER` — matches packet R08, prereg §2, execution-packet frozen matrix.
  - Lines 216-222 `_CALL_ORDER` string pins same order; `MAX_ITER/DAMPING` pinned via `d7c` aliases (lines 92-93).
- No execution of scientific path for this item; dynamic order confirmed separately via `--dry-run` in §6 (allowed non-scientific print path).

## 3. Exact future command matches frozen packet — PASS

- Frozen packet (task packet §6/R14, line 297), prereg §4 (line 175), execution packet (line 19) all contain byte-identical:
  - `timeout -k 30 1800 python scripts/v72p2d7_gf32_cross_layer_discriminator.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_e_cross_layer_discriminator_<uuid>`
- Runner `scripts/v72p2d7_gf32_cross_layer_discriminator.py:37-48` accepts exactly `--model-f-root`, `--out-root`, `--dry-run`, `--verify`; `main()` (lines 68-96) enforces pure root-contract refusal first, then state read, then `is_authorized` refusal, then `model_f_root_matches` refusal, then gated `run_cross_layer_discriminator`. No `--phase`, no R1d/G1/G2 flags.
- `<uuid>` is placeholder for one future authorized invocation; no UUID generated in this review; no out-root created.

## 4. Target absence — PASS

- `ls -d workspace/d7_e_cross_layer_discriminator_*` → `No such file or directory`.
- `ls -d workspace/d6_graph_mother_r1d_*` → `No such file or directory`.
- `.venv/bin/python -c "import glob; ..."` → `[]` / `[]`.
- `ls workspace/ | grep -E "d7_e_|d6_graph_mother_r1d"` → no match (`grep_exit=1`).
- Re-checked after refusal/dry-run/sentinel/tests (§§6-8): still absent. No R1d result roots beyond known test basetemps (`/tmp/d7e_preexec_*`, pytest `tmp_path` only, all outside repo). No `workspace/d7_e_*` ever created.

## 5. venv-on-PATH identity, GNU timeout, stdlib resource RSS (no psutil) — PASS

- `which python` → not found (factual); project venv is `.venv/bin/python`:
  - `.venv/bin/python --version` = `Python 3.12.3`; `sys.executable` = `/mnt/d/Code/HD-QKD_Polar_Comparison/.venv/bin/python`; `numpy.__version__` = `2.5.3`.
  - `python3` = `/usr/bin/python3` `3.12.3` without numpy (ModuleNotFoundError) — not used; all review executions used `.venv/bin/python` explicitly. Non-blocking environment quirk, not a D7-E defect.
- GNU timeout: `which timeout` = `/usr/bin/timeout`; `timeout --version | head -1` = `timeout (GNU coreutils) 9.4`.
- RSS stdlib path: `grep -rn psutil` over core+runner → no match (exit 1). Core lines 337-339 `_read_ru_maxrss()` uses `import resource; resource.getrusage(RUSAGE_SELF).ru_maxrss`; `get_rss_bytes()` does explicit `int(raw)*1024` (Linux KiB→bytes); line 118 `RSS_LIMIT_BYTES = 2*1024**3`.
- Live reading via venv: `ru_maxrss_KiB= 8908`, `bytes= 9121792`, `finite_positive_lt2GiB= True` — finite, positive, <2GiB.

## 6. Unauthorized refusal and --dry-run — PASS

- `--help`: `.venv/bin/python scripts/v72p2d7_gf32_cross_layer_discriminator.py --help` → exit 0, usage with `--model-f-root/--out-root/--dry-run/--verify`, no bind/loader/root.
- Unauthorized: `.venv/bin/python scripts/v72p2d7_gf32_cross_layer_discriminator.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_e_cross_layer_discriminator_PREEXECUTE_REFUSAL_PROBE` (fake non-UUID suffix, pre-absent) → stdout `D7-E execution is not authorized; refusing before any work`, exit 3. Post-check `ls -d` probe → `No such file or directory`; `workspace/d7_e_*` still absent. Refusal precedes loader/decoder/root by construction (runner lines 68-84: pure `validate_production_out_root` → `read_cycle_state` → `is_authorized` refuse → `model_f_root_matches` refuse → gated run).
- `--dry-run`: same runner `--dry-run > /tmp/d7e_dryrun.txt` → exit 0, `wc -l` = 193 (1 header + 192 slots). Header `slots=192 mandatory=128 budget=192`. Head `1 1.0 2026091300 L1_TO_L2 SOURCE L1_MARGINAL L1 49` through `6 1.0 2026091300 L2_TO_L1 TRANSFER L1_TRANSFER L1 49`; tail `187 1.2 2026091315 L1_TO_L2 SOURCE ...` through `192 1.2 2026091315 L2_TO_L1 TRANSFER L1_TRANSFER L1 59`. f-split 96/96, rows 49/43 (f=1.0) and 59/52 (f=1.2) visible. Code path (runner lines 58-67) calls only `frozen_slots()`, no loader/decoder/root. Post-check `workspace/d7_e_*` absent. Exact 192 order confirmed.

## 7. External-cwd dual decoder + Model-F loader sentinels (fakes only) — PASS

- From foreign cwd `/tmp/d7e_preexec_foreign` (verified `cwd= /tmp/d7e_preexec_foreign`), via absolute repo paths and `comparison_bench/src` on `sys.path`, file-path load of runner (no cwd assumption):
  - `bind_row_layered_decoders()` → `SOURCE.target is v35.decode_row_layered_fftqspa` True, `TARGET.target is v35.decode_row_layered_fftqspa` True; names `source`/`target`. Exact production functions reached with zero calls (bind only, per docstring `no calls`).
  - `_default_model_f_loader is d7c._default_model_f_loader` True (line 415 narrow alias).
  - Fake dispatch: tiny in-memory `h=(2,4) uint8`, `prior=(4,32) 1/32`, `syn=(2,)`; sentinel decoders raising `Sentinel(tag)` reached for both `SOURCE`→`src` and `TARGET`→`tgt`; `events==['src','tgt']`; unknown key refuses ValueError (covered in suite `test_x02`). Zero real decoder calls, zero artifact reads (no Model-F load, no workspace read beyond existence-negative check, no root created).
  - Exit 0, `FOREIGN_SENTINEL_OK`. Also reproduced repo-cwd sentinel with shape pins `[('src',(2,4),(4,32),(2,)),('tgt',...)]`.
- Static: `bind_row_layered_decoders` (lines 608-630) wraps only `v35.decode_row_layered_fftqspa` with `max_iter=MAX_ITER, damping_alpha=DAMPING_ALPHA, warm_beliefs=None, field=None` ×2; `dispatch_decoder` (579-587) routes only `SOURCE`/`TARGET`.

## 8. Tests re-run (separate processes, fresh basetemps, -p no:cacheprovider) — PASS

- Collected: `25 tests collected` (list: e01-e03, m01-m03, g01-g05, l01-l03, w01-w03, x01-x05, x06a/b/c).
- Reviewer run 1 (fresh basetemp `/tmp/d7e_preexec_r1_grp1`): `.venv/bin/python -m pytest comparison_bench/tests/test_v72p2d7_gf32_cross_layer_discriminator.py -k "not x06" -p no:cacheprovider --basetemp /tmp/d7e_preexec_r1_grp1 -q` → `22 passed, 3 deselected` in 26.55s, exit 0. Matches R18 `22 passed, 3 deselected`.
- Reviewer run 2 spot-check (fresh basetemp `/tmp/d7e_preexec_r1_x06a`): `-k "x06a"` same flags → `1 passed, 24 deselected` in 10.39s, exit 0. Outer PASS implies inner asserts `23 passed` (BP) and `14 passed` (D7-A) per `test_x06a` lines 1500-1505. Chose x06a as fastest regression group; x06b/c covered by R18 with identical deselection adjudication (2 D7-B + 1 D7-C + 2 D7-D stale IDs, all pre-existing baseline FAILs, no skip/xfail/delete).
- Post-test: `workspace/d7_e_*` and `workspace/d6_graph_mother_r1d_*` still absent; `/tmp` artifacts only, no production root/loader/decoder binding from tests (fakes + `tmp_path`).

## 9. Protected roots, authorization keys, V35 authority — PASS

- Protected roots metadata (stat only, no content reads): all exist except VOID glob (no `workspace/*VOID*`/`*void*`, recorded factually):
  - `workspace/v72p2d5_g0/20260905_r2` 2026-09-06, `.../g0_recovery/20260906_r1` 2026-09-06, `.../model_f_input/20260907_r1` 2026-09-07, `.../p0_cost/20260906_r1` 2026-09-07, `.../g1/20260907_r2` 2026-09-08, `.../g1/20260906_r1` 2026-09-07, `.../structure/20260905_r2` 2026-09-05, `workspace/d6_graph_mother_r1_923a...` 2026-09-08, `.../r1c_dd8c...` 2026-09-09, `workspace/d7_b_easy_regime_c605d1e6...` 2026-09-10, `workspace/d7_c_bidirectional_oracle_94c0ea15...` 2026-09-11, `workspace/d7_d_schedule_discriminator_64660d16...` 2026-09-11.
  - `PROTECTED_ROOTS` in core = D7-C set + D7-C/D7-B roots (verified via import print, no content read). Reviewer performed no writes to any protected root; `test_x05` (in passing 22) asserts workspace listing and `_dir_meta` invariance across a full fake run.
- Authorization/promotion keys false: `cycle_state.yaml` state `FROZEN_PREREG_R1_NOT_AUTHORIZED_NOT_EXECUTED`; parsed `plan_accepted/implementation_authorized/d7e_execution_authorized/decoder_executed/result_created/formal_execution_authorized/synthetic_execution_authorized/real_execution_authorized/scientific_promotion/g1_authorized/g2_authorized/d7e_result_accepted` all `false`; `d7e_execution_attempts/completed` 0, `d7e_terminal D7_E_NOT_EXECUTED`, reviews `PENDING`.
- V35 report: `git diff --stat -- docs/v35-algorithm-development-report.md` = `65 insertions, 89 deletions`; `git log --oneline -3` latest `ed0adfca`; `git show HEAD:... | wc -l` = 92 vs worktree 68. Committed corrected report remains authoritative; worktree delta is pre-existing external rewrite preserved per packet §1. Noted factually; not modified by reviewer.

## Checklist

- [x] Matches OpenSpec spec (frozen R14 prereg/packet/spec/tasks §§3-5; matrix/formulas/labels/terminals/budgets/schema pinned in §§2-3)
- [x] Tests pass (reviewer reproduced: `22 passed, 3 deselected` + `1 passed, 24 deselected` spot-check with inner `23/14`; no failures)
- [x] No scope creep (three impl files only + two review docs; no flooding/warm-start/alternating/feedback/tuning/r1d/phase; no existing-file D7-E edit; no roots; no auth change; frozen `src/experiments/tools` untouched)
- [ ] docs/decision-log.md or docs/troubleshooting.md needs update? No — D7-E remains frozen/unauthorized/unexecuted; state/roadmap updates belong to R20-R21 closeout after pre-execute, not this gate.

## Return delta

- verdict: `D7_E_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION` (grants nothing)
- per-item literal evidence: §§1-9 above (R18 PASS genuine; 192-slot static order; exact future command byte-identical across packet/prereg/execution-packet; target absence `No such file or directory` ×2; venv `3.12.3`/`2.5.3`, timeout `9.4`, RSS `8908 KiB=9121792B` finite-positive-<2GiB, no psutil; refusal exit 3 before loader/decoder/root, help 0, dry-run 193 lines exit 0; foreign-cwd dual bind + loader sentinels zero-call; tests `22 passed, 3 deselected` + `1 passed` spot-check; protected-roots metadata + all-auth-false + V35 committed authoritative)
- review doc path: `docs/research_cycles/V72P2D7-GF32-CROSS-LAYER-DISCRIMINATOR/D7_E_PRE_EXECUTE_REVIEW_R1.md`
- blockers: none. Non-blocking notes: full worktree carries pre-existing dirty/CRLF + 8-file content deltas (preserved per packet); `python` not on default PATH (venv at `.venv/bin/python` used explicitly); VOID glob absent in `workspace/` (recorded factually).
