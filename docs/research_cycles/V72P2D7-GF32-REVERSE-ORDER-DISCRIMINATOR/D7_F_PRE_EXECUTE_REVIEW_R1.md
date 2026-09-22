# D7-F Pre-EXECUTE review R1 (independent)

- Authority: `.workbuddy/tasks/D7_E_ACCEPT_D7_F_REVERSE_ORDER_READINESS_R1_TASK_PACKET.md` §8 (Pre-EXECUTE only).
- Reviewer: independent D7-F Pre-EXECUTE reviewer (separate context from implementer and implementation reviewer).
- Scope: review-only. Sole write is this document. No commits, no edits, no scientific decoder calls, no Model-F/real reads, no roots/UUID.
- HEAD: `aca2b6bf731dc75d5126a0e10766865749aa2ce8` (`aca2b6b`), branch `formal-ir-v72p1-addendum-clean`.
- Under review (uncommitted, untracked at review start):
  - `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_reverse_order_discriminator.py`
  - `comparison_bench/tests/test_v72p2d7_gf32_reverse_order_discriminator.py`
  - `scripts/v72p2d7_gf32_reverse_order_discriminator.py`
  - `docs/research_cycles/V72P2D7-GF32-REVERSE-ORDER-DISCRIMINATOR/D7_F_IMPLEMENTATION_REVIEW_R1.md`
- Frozen refs: R1 packet §5, OpenSpec `v72p2d7-reverse-order-cross-layer-discriminator`, `D7_F_PREREG_R1.md`, `D7_F_EXECUTION_PACKET_R1.md`.
- Verdict token: `D7_F_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`
- This review grants no authorization; explicit verbatim authorization is still required for any future execution. Neither this verdict nor the implementation PASS grants authorization.

## 0. HEAD / scope gate (STOP check)

- `git rev-parse HEAD` = `aca2b6bf731dc75d5126a0e10766865749aa2ce8`, short `aca2b6b`, `git branch --show-current` = `formal-ir-v72p1-addendum-clean`. PASS.
- Scoped D7-F status:
  - `git status --porcelain=v1 | grep reverse_order` = exactly 3 `??` code files (module, test, script). PASS.
  - `git status --porcelain=v1 -- docs/research_cycles/V72P2D7-GF32-REVERSE-ORDER-DISCRIMINATOR/` = exactly 1 `??` (`D7_F_IMPLEMENTATION_REVIEW_R1.md`); pre-execute doc absent before this write (verified `ls .../D7_F_PRE_EXECUTE_REVIEW_R1.md` = No such file). PASS.
  - `git diff --name-only HEAD -- comparison_bench/src/comparison_bench/formal_ir/ comparison_bench/tests/ scripts/ docs/research_cycles/V72P2D7-GF32-REVERSE-ORDER-DISCRIMINATOR/` = empty (no tracked D7-F diff). PASS.
- Broader worktree is dirty (~1971 `git status --porcelain=v1` entries) plus 2 unrelated untracked D6 review docs; out-of-scope per delegation rule §10.1-11 (review by scope), same disposition as implementation review §0. No `workspace/d7_f_reverse_order_discriminator_*` at review start. Proceed, not STOP.

## 1. Implementation review PASS genuine

- `grep -c D7_F_IMPLEMENTATION_REVIEW_PASS docs/.../D7_F_IMPLEMENTATION_REVIEW_R1.md` = `2`.
- `grep Verdict:` = `Verdict: D7_F_IMPLEMENTATION_REVIEW_PASS` (line 102). No FAIL token. PASS.

## 2. .venv / environment

- `test -x .venv/bin/python` = `EXEC_OK`. PASS.
- `.venv/bin/python -c "import sys,numpy"` = `3.12.3` / `2.5.3`. Recorded.
- `command -v python` = `BARE_PYTHON_ABSENT`; default PATH has no venv/python (system dirs only). `.venv/bin/python` form required. PASS.

## 3. Exact frozen command byte-identical

- Frozen command (prereg §4 + execution packet exact-future-command, byte-identical via `grep -F "timeout -k 30 1800"` hitting both files with identical line):
  `timeout -k 30 1800 .venv/bin/python scripts/v72p2d7_gf32_reverse_order_discriminator.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_f_reverse_order_discriminator_<uuid>`
- `scripts/... --help` confirms same script path, flags `--model-f-root/--out-root/--dry-run/--verify`, and `--model-f-root` help text `must equal workspace/v72p2d5_model_f_input/20260907_r1 for a run`. `<uuid>` placeholder preserved; no identifier generated. PASS.

## 4. GNU timeout

- `timeout --version | head -n 2` = `timeout (GNU coreutils) 9.4` + `Copyright (C) 2023 Free Software Foundation, Inc.`
- Frozen docs pin GNU coreutils `timeout`, `-k 30`, `1800` with no version number; no frozen version to differ from, so no trivial timeout→124 rehearsal per packet rule. PASS.

## 5. ONE live VmHWM probe (production parser path, never repeated, no ru_maxrss)

- Single command via `.venv/bin/python` importing production `parse_vmhwm_rss_bytes` + `_read_proc_self_status_text` + `get_rss_bytes` (aliases of accepted D7-E `parse`), no decoder, no loader, no root:
  - `RAW:VmHWM:\t   96468 kB`
  - `PARSED_BYTES:98783232` (= 96468*1024)
  - `POS_FINITE_LT2G:True` (positive finite <2GiB = 2147483648)
- One result stands; never repeated; `ru_maxrss`/`resource` never called. PASS.

## 6. Target absence

- `ls -d workspace/d7_f_reverse_order_discriminator_*` = `No such file or directory`, exit 2 (before and after all probes).
- `ls -d workspace/d7_f_*` = same, exit 2 (before + after focused tests).
- `ls -d workspace/d6_graph_mother_r1d_*` = same, exit 2. No R1d result roots beyond task-owned `/tmp` basetemps. PASS.

## 7. Authorization / promotion / decoder / result / attempts

- `cycle_state.yaml` literal: `state: D7_F_FROZEN_NOT_AUTHORIZED_NOT_EXECUTED`, `plan_accepted: false`, `implementation_authorized: false`, `d7f_execution_authorized: false`, `decoder_executed: false`, `result_created: false`, `formal_execution_authorized: false`, `synthetic_execution_authorized: false`, `real_execution_authorized: false`, `scientific_promotion: false`, `r1d_state: R1D_ABSENT_NOT_AUTHORIZED`, `g1_authorized: false`, `g2_authorized: false`, `d7f_execution_attempts: 0`, `d7f_execution_completed: 0`, `d7f_terminal: NONE`, `d7f_pre_result_review: PENDING`, `d7f_result_accepted: false`, `d7f_accepted_scope: NONE`, `d7f_implementation_review: PENDING`, `d7f_pre_execute_review: PENDING`, `next_gate: D7_F_IMPLEMENTATION_PENDING`, `d7f_exact_interpreter: .venv/bin/python`. All false/zero; R1d/G1/G2 unauthorized. PASS.

## 8. Protected roots (stat only, never contents)

- `stat workspace/v72p2d5_model_f_input/20260907_r1` = dir, Size 4096, Modify 2026-09-07 02:07:07. PASS (exists, pre-existing mtime).
- `stat workspace/d7_e_cross_layer_discriminator_faa5dc1c-d2d6-4329-b88d-68f2c1f51d5c` = dir 4096, Modify 2026-09-11 19:43:07. PASS.
- `stat workspace/d7_c_bidirectional_oracle_94c0ea15-a786-4cb8-a991-6fec521cccae` = dir 4096, Modify 2026-09-11 00:33:39. PASS.
- `stat workspace/d7_b_easy_regime_c605d1e6-8577-4c52-a865-12500fc8c964 workspace/d7_d_schedule_discriminator_64660d16-397d-4ef3-8454-3066d27c12c7` = both dir 4096, Modifies 2026-09-10 20:33:38 / 2026-09-11 07:30:05. PASS.
- Metadata only; no file contents read; no Model-F binary read. PASS.

## 9. --dry-run + unauthorized refusal

- `--dry-run > /tmp/d7f_dryrun.txt`: exit 0, `wc -l` = `129` (header + 128 slots), header `slots=128 mandatory=64 budget=128`.
- Head: `1 1.0 2026091300 FORWARD_L1_TO_L2 SOURCE L1_MARGINAL L1 49`, `2 ... FORWARD ... TARGET L2_TRANSFER L2 43`, `3 ... REVERSE ... SOURCE L2_MARGINAL L2 43`, `4 ... REVERSE ... TARGET L1_TRANSFER L1 49`. Tail: `125..128` closing `1.2 2026091315` forward-then-reverse pair. Exact 128-slot order (f outer 1.0→1.2, seeds ascending, per-(f,seed) FWD_SRC/FWD_TGT/REV_SRC/REV_TGT). No loader/decoder/root by construction (script `dry_run` returns before validate/state/loader/decoder/root). PASS.
- Unauthorized exact-shape probe: `.venv/bin/python scripts/... --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_f_reverse_order_discriminator_probe_unauth_refusal` = `D7-F execution is not authorized; refusing before any work`, exit `3` before loader/decoder/root (script order validate→state→auth precedes prepare_inputs/bind/loop/write). Probe root `ls` after = No such file, exit 2. No UUID generated (literal `probe_unauth_refusal` suffix). PASS.

## 10. External-cwd decoder/loader sentinel (fakes only, zero calls/reads/roots)

- Command: `workdir=/tmp`, `env -u PYTHONPATH /mnt/d/Code/HD-QKD_Polar_Comparison/.venv/bin/python -c` loading core by absolute file path, fake `SOURCE`/`TARGET` fns, tiny `(2,4)/(4,2)/(2,)` arrays, `dispatch_decoder` for SOURCE/TARGET/BOGUS.
- Literal: `SENTINEL r1=SRC r2=TGT unk_refused=True calls=['S', 'T'] v35_absent=True prod_bind_untouched=True`.
- Proves exact production `dispatch_decoder` reachable, routes both keys to fakes, unknown key refuses; `v35` never imported (no real decoder bind/call); `bind_row_layered_decoders` reachable but untouched (not called); no Model-F loader called; no root created; cwd external with PYTHONPATH stripped. PASS.

## 11. Focused tests (separate process, fresh basetemp, no cache) + frozen packet consistency

- Command (separate process): `rm -rf /tmp/d7f_preexec_basementp && mkdir -p /tmp/d7f_preexec_basementp && .venv/bin/python -m pytest comparison_bench/tests/test_v72p2d7_gf32_reverse_order_discriminator.py -q -p no:cacheprovider --basetemp /tmp/d7f_preexec_basementp`
- Literal: `41 passed, 1 warning in 29.26s` (warning only `Unknown config option: cache_dir`). Reproduces implementation-review claim `41 passed` (29.03s there; delta is timing only). No failures; no new in-scope failures. Frozen packet consistency holds (128 matrix/order/cap, arms, gates, labels/terminals, RSS, schema, sentinels covered per implementation review §7 mapping; this review trusts that mapping and does not duplicate full suites). Post-test `ls -d workspace/d7_f_*` still absent. PASS.

## Discrepancies / notes

- None blocking. Broader dirty worktree (~1971 entries) and 2 unrelated untracked D6 review docs exist but are out-of-scope; scoped D7-F tracked diff is empty and scoped untracked is exactly the 3 code files + 1 implementation review doc (this doc is the 5th file, the sole authorized write).
- Implementation review §0 phrasing "`grep reverse_order` shows exactly the three files" omits the review doc by name filter; scoped check above resolves it (3 code via that grep + 1 review doc via cycle-dir status). Not a blocker.
- No frozen timeout version exists, so version 9.4 triggers no rehearsal. Not a blocker.

## Blocking Issues

- None.

## Non-Blocking Suggestions

- None required for PASS. Future execution still needs explicit verbatim authorization for one fresh `<uuid>`, Pre-RESULT review before any publication, and no push.

## Checklist

- [x] Matches OpenSpec spec (prereg/execution packet §5 B01–B07 + implementation PASS)
- [x] Tests pass (41 passed reproduced, fakes/basementp only)
- [x] No scope creep (new files only at frozen paths; zero predecessor/cycle-state edits; no roots/auth/decoder)
- [x] docs/decision-log.md or docs/troubleshooting.md needs update? No — readiness-only review; no durable decision or failure mode to record here.

Verdict: `D7_F_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`
