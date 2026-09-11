# D7-E renewed Pre-EXECUTE review VENV RSS A2 (T6 only)

- reviewer: independent renewed Pre-EXECUTE reviewer (separate context from implementer and T5 reviewer; review-only)
- authority: `.workbuddy/tasks/D7_E_RSS_TELEMETRY_REWORK_VENV_A2_TASK_PACKET.md` §10 (T6 only)
- branch: `formal-ir-v72p1-addendum-clean`
- HEAD verified: `9e095382b357c36f86c1936e45bc4f63d8d14943` (prefix `9e09538`, implementation commit)
- required history present: `08590fba=commit`, `031deee7=commit`, `d6e40dd=commit`, `becf60f=commit`, `9e09538=commit`; `git log --oneline -1` = `9e095382 fix(d7-e): read WSL peak RSS from /proc/self/status VmHWM fail-closed`
- review-only: sole write is this file; no commits, no other edits, no decoder/Model-F content, no roots/UUID created
- frozen inputs read: packet §§0-1 (A2 rule); A2 addendum `D7_E_EXECUTION_PACKET_ADDENDUM_RSS_A2.md`; frozen A2 OpenSpec delta (`design.md` RSS A2 section, `tasks.md` A2-01…A2-08, `specs/provenance-safe-cross-layer-discriminator/spec.md` VmHWM-only requirement); T5 review `D7_E_RSS_TELEMETRY_REWORK_REVIEW_A2.md`; A1/VENV review `D7_E_PRE_EXECUTE_REVIEW_VENV_A1.md`; `cycle_state.yaml`
- T5 confirmation: `D7_E_RSS_TELEMETRY_REWORK_REVIEW_A2.md` carries `D7_E_RSS_TELEMETRY_REWORK_REVIEW_PASS_A2` present, `D7_E_RSS_TELEMETRY_REWORK_REVIEW_FAIL_A2` absent — implementation review PASS is genuine
- A1/VENV review status: `D7_E_PRE_EXECUTE_REVIEW_PASS_VENV_A1_AWAITING_EXPLICIT_AUTHORIZATION` remains valid for interpreter/command reachability only; it is now stale on RSS source semantics only (its stdlib `ru_maxrss` source is superseded by the A2 addendum, which supersedes ONLY the RSS source semantics in R1/A1 and preserves `.venv/bin/python` plus the exact frozen command)
- scope: each probe below ran as a separate command from repo root with `.venv/bin/python`, except the external-cwd sentinel which ran from `/tmp` via the absolute interpreter path with absolute repo paths only

## Verdict

`D7_E_PRE_EXECUTE_REVIEW_PASS_VENV_RSS_A2_AWAITING_FRESH_EXPLICIT_AUTHORIZATION`

This grants no authorization. No execution authorized. No result accepted. A later execution needs a fresh explicit authorization referencing RSS A2; the previous user authorization is not reusable.

## 1. Ordinary Pre-EXECUTE checklist with A1 interpreter rules — PASS

### 1a. Implementation review PASS genuine — PASS

- T5 doc `T5_PASS_TOKEN_PRESENT=True`, `T5_FAIL_ABSENT=True`.
- Committed scope `git diff --name-only becf60f..9e09538` = exactly two allowed paths:
  - `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_cross_layer_discriminator.py`
  - `comparison_bench/tests/test_v72p2d7_gf32_cross_layer_discriminator.py`
- Both paths are in packet §3 allowed list; no other committed path changes in range (per T5 hunk structure: one RSS-block hunk in module, one append hunk of A2 tests).

### 1b. Frozen 192-slot matrix/order — PASS

Static (`.venv/bin/python`, no live kernel, never `get_rss_bytes`):

- `F_VALUES=[1.0, 1.2]`; `BLOCK_SEEDS_N=16:2026091300..2026091315`; `DIRECTIONS=['L1_TO_L2', 'L2_TO_L1']`; `ROLE_ORDER=['SOURCE', 'CONTROL', 'TRANSFER']`
- `SLOTS_N=192`; `SLOT_IDX_RANGE=1..192`; `SLOT_IDX_1TO192=True`
- `HEAD_SLOT=(1, 1.0, 2026091300, 'L1_TO_L2', 'SOURCE', 'L1_MARGINAL', 'L1', 49)`
- `TAIL_SLOT=(192, 1.2, 2026091315, 'L2_TO_L1', 'TRANSFER', 'L1_TRANSFER', 'L1', 59)`
- `MANDATORY=128 MAX=192 SLOT_COUNT=192`
- `TERMINALS_N=12 T1=D7_E_PRE_EXECUTION_BLOCKED`; `SEVEN_FILES=['manifest.json', 'decoder_records.csv', 'transfer_pairs.csv', 'stratum_summary.csv', 'summary.json', 'report.md', 'command_log.txt']`; `HAS_RSS_BYTES=True`
- `RSS_LIMIT_BYTES=2147483648 EQ_2GIB=True`; `MODEL_F_ROOT=workspace/v72p2d5_model_f_input/20260907_r1`; `PROC_PATH=/proc/self/status`
- `HAS_LEGACY_READER=False`; `ABSENT_ru_maxrss=True`; `ABSENT_import resource=True`; `ABSENT_VmRSS=True`; `ABSENT_statm=True`; `ABSENT_subprocess=True`; `ABSENT_psutil=True`; `ABSENT_lru_cache=True` (core + thin runner)

Dry-run (`.venv/bin/python scripts/v72p2d7_gf32_cross_layer_discriminator.py --dry-run`):

- `exit=0`; `193 /tmp/d7e_a2_dryrun.txt`
- `LINES=193`; `HEADER=slots=192 mandatory=128 budget=192`; `SLOTS=192`; `IDX_OK=True`; `F_SPLIT=96,96`
- head line 1: `1 1.0 2026091300 L1_TO_L2 SOURCE L1_MARGINAL L1 49`
- tail lines: `191 1.2 2026091315 L2_TO_L1 CONTROL L1_MARGINAL L1 59` / `192 1.2 2026091315 L2_TO_L1 TRANSFER L1_TRANSFER L1 59`
- No evidence root created (D7E_ROOTS count 0 before and after).

### 1c. Exact future command byte-identical — PASS

Frozen spelling (sole authorized form):

- `timeout -k 30 1800 .venv/bin/python scripts/v72p2d7_gf32_cross_layer_discriminator.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_e_cross_layer_discriminator_<uuid>`
- `D7_E_PREREG_R1.md:BYTE_IDENTICAL=True`; `D7_E_EXECUTION_PACKET_R1.md:BYTE_IDENTICAL=True`; `D7_E_EXECUTION_PACKET_ADDENDUM_VENV_A1.md:BYTE_IDENTICAL=True`
- Preconditions: `TEST_X_EXIT=0`; `NUMPY_CHECK_EXIT=0 VER=2.5.3`; `TIMEOUT=/usr/bin/timeout`; cwd is repo root; no other venv, no bare `python`/`python3`, no `PYTHONPATH`, no wrapper.

### 1d. Unauthorized refusal exit 3 with root absent — PASS

Probe out-root `workspace/d7_e_cross_layer_discriminator_A2_PREEXEC_PROBE` (no identifier generated; placeholder name only, not a UUID):

- `PRE_ABSENT=True`
- `EXIT=3`
- `STDOUT=D7-E execution is not authorized; refusing before any work`
- `POST_ABSENT=True`
- `REFUSAL_SHAPE=True` (exit 3 + exact message + root absent)

### 1e. External-cwd dual decoder + loader sentinels — PASS

Run from external cwd via absolute paths only (`cwd=/tmp`, absolute interpreter `/mnt/d/Code/HD-QKD_Polar_Comparison/.venv/bin/python`, absolute runner path; no Model-F reads, no root creation):

- `SOURCE_target_is_v35=True`; `TARGET_target_is_v35=True`
- `events=[('src', (2, 4), (4, 32), (2,)), ('tgt', (2, 4), (4, 32), (2,))]`
- `unknown_key_refused=True`
- `loader_is_d7c=True`
- `REPO_D7E_ROOTS=[]`; `REPO_R1D_ROOTS=[]`
- `FOREIGN_SENTINEL_OK`
- Zero real decoder calls (sentinels raise before any real decode), zero Model-F content reads, zero roots.

### 1f. --help — PASS

- `HELP_EXIT=0 HAS_USAGE=True` (`--model-f-root` and `--dry-run` in usage); binds no decoder, reads no Model-F, creates no root.

## 2. Single fresh live E09 — PASS (exactly one probe, never repeated)

One command with `.venv/bin/python` from repo root; production parser on the live `/proc/self/status` plus the raw `VmHWM` line in the same command. No `ru_maxrss` call in the command. No repeat under any circumstance.

- `RAW_VMHWM_LINE='VmHWM:\t   96484 kB'`
- `RSS_BYTES=98803712`
- `LIMIT=2147483648`
- `E09_PASS=True` (`isinstance int` + finite + `0 < 98803712 < 2147483648`)
- Arithmetic: `96484 * 1024 = 98803712` exact (`bytes = value * 1024`).

This single result stands, pass or fail. No second E09 was run by this review.

## 3. State / root / auth / worktree confirmation — PASS

- `CWD=/mnt/d/Code/HD-QKD_Polar_Comparison`; `D7E_ROOTS=[] COUNT=0` — no UUID/root created by any probe in §§1-2.
- `cycle_state.yaml`: `state: D7_E_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`; all authorization/promotion/decoder/result flags false (`plan_accepted`, `implementation_authorized`, `d7e_execution_authorized`, `decoder_executed`, `result_created`, `formal_execution_authorized`, `synthetic_execution_authorized`, `real_execution_authorized`, `scientific_promotion`, `g1_authorized`, `g2_authorized` all `...: false`); `d7e_execution_attempts: 0`; `d7e_execution_completed: 0`; `d7e_terminal: D7_E_NOT_EXECUTED`; `next_gate`/`d7e_readiness_state` remain `D7_E_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`; `CYCLE_STATE_OK=True`.
- Protected roots stat-only (names/sizes/mtime, no content reads; mtimes predate this review and were not touched by probes):
  - `workspace/v72p2d5_model_f_input/20260907_r1 EXISTS` (dir)
  - `workspace/d7_c_bidirectional_oracle_94c0ea15-a786-4cb8-a991-6fec521cccae EXISTS` (dir)
  - `workspace/d7_b_easy_regime_c605d1e6-8577-4c52-a865-12500fc8c964 EXISTS` (dir)
  - `workspace/d7_d_schedule_discriminator_64660d16-397d-4ef3-8454-3066d27c12c7 EXISTS` (dir)
  - Metadata unchanged by review actions (review performed stat only; all probes above report zero Model-F/protected-content reads and zero root creation).
- Scoped worktree: `git diff --name-only HEAD` content deltas are exactly the 11 pre-existing unrelated-dirt paths (`AGENTS.md;AGENT_HANDOFF.md;AGENT_PROJECT_MEMORY.md;README.md;RUN_COMMANDS.md;docs/CURRENT_MAINLINE.md;docs/decision-log.md;docs/research-cycle-sop.md;docs/troubleshooting.md;docs/v35-algorithm-development-report.md;workspace/pytest-evidence-test/output/expanded_evidence_manifest.json`), preserved per packet; `PORCELAIN_TOTAL=1968` is the known WSL stat noise (same phenomenon as A1). No A2-scoped committed path was modified by this review; the sole new path is this review doc itself. No staging, no commits by reviewer.

## Blockers

- None.

## Non-blocking notes

- The A2 OpenSpec tasks A2-01…A2-08 remain unchecked in `tasks.md` pending T7 closeout; this review does not check them.
- `cycle_state.yaml` still points at the A1 addendum (`d7e_execution_packet_addendum_doc: ...ADDENDUM_VENV_A1.md`) and `d7e_pre_execute_review: D7_E_PRE_EXECUTE_REVIEW_PASS_VENV_A1_AWAITING_EXPLICIT_AUTHORIZATION`; repointing to the A2 addendum plus both PASS reviews belongs to T7 closeout, not this review.

## Review doc path

`docs/research_cycles/V72P2D7-GF32-CROSS-LAYER-DISCRIMINATOR/D7_E_PRE_EXECUTE_REVIEW_VENV_RSS_A2.md`
