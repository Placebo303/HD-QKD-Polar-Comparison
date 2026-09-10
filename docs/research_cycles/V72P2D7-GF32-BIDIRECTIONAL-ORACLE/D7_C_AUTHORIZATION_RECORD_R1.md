# D7-C authorization record R1 (one fresh WSL bidirectional-oracle invocation)

## 0. Verbatim fresh authorization (§0 sole authority for D7-C)

> 我现在明确授权执行 D7-C bidirectional oracle：仅允许按冻结的
> `D7_C_EXECUTION_PACKET_R1.md`，在已记录且验证可用的 WSL venv-on-PATH
> 环境中，使用冻结命令对一个全新的
> `workspace/d7_c_bidirectional_oracle_<uuid>/` 根调用一次；共 128 个冻结
> scientific decoder calls，授权由首次 scientific decoder 尝试消耗，不因失败、
> 超时、部分结果或环境异常恢复；不得重试、重跑、恢复、复用根、修改参数或更换
> estimator；不得执行 R1d、任何 `--phase`、正式 G1/G2、CAL、VAL、real/raw 或
> 跨层 APP。执行结束后立即回收授权并进行独立 Pre-RESULT 复审，复审通过前不得
> 接受或提交结果。

This authorization applies to exactly one fresh D7-C UUID and one invocation of
the frozen command below. It revives no prior UUID or authorization.

## 1. UUID and target root (sole D7-C UUID, generated exactly once)

- UUIDv4: `94c0ea15-a786-4cb8-a991-6fec521cccae`
- Source: single read of `/proc/sys/kernel/random/uuid` after E01–E14 PASS
  (exactly one generation; no second UUID exists in this task).
- Regex validation: `^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$`
  → `UUID_VALID`.
- Target root (relative, runtime-derived):
  `workspace/d7_c_bidirectional_oracle_94c0ea15-a786-4cb8-a991-6fec521cccae`
- Root confirmed ABSENT immediately after generation (rc 2) and reconfirmed
  ABSENT after the authorization commit (see §5).
- Parent `workspace/` writable (`WORKSPACE_WRITABLE`). Root NOT pre-created.

## 2. Exact instantiated command (exactly-once future invocation)

```bash
timeout -k 30 1800 python scripts/v72p2d7_gf32_bidirectional_oracle.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_c_bidirectional_oracle_94c0ea15-a786-4cb8-a991-6fec521cccae
```

- Instantiation: frozen WSL shape from `D7_C_EXECUTION_PACKET_R1.md` L13 with
  `<uuid>` replaced by the sole UUID above. No added args, PYTHONPATH, env
  overrides, pipes, tee, redirection, alternate estimator, alternate Python
  executable or replacement root. A timing/capture harness may spawn it as a
  child with argv exactly as above.
- Interpreter resolution: bare `python` is absent on the default PATH; the
  reviewed venv-on-PATH adapter resolves `python` (see §3 E08).
- This scientific command is invoked at most once. Startup failure, exit 124,
  nonzero exit, partial root, missing file or unexpected terminal never permits
  another invocation, replacement UUID or re-param.

## 3. WSL environment (runtime-observed facts, not science parameters)

- Repo root: current WSL checkout `/mnt/d/Code/HD-QKD_Polar_Comparison`.
- Branch: `formal-ir-v72p1-addendum-clean`; HEAD:
  `4ba36bfb8082b9e3749aa7157f7b8560c4814f41` (short `4ba36bfb`).
- PATH adapter: `PATH="$HOME/.venvs/hd-qkd-polar-comparison/bin:$PATH"`.
- Interpreter: `/home/karel_303/.venvs/hd-qkd-polar-comparison/bin/python`,
  CPython 3.12.3, NumPy 2.4.4, `sys.executable` as above (E08/E09).
- WSL kernel: `6.18.33.2-microsoft-standard-WSL2`; distro: `Ubuntu 24.04.4 LTS`.
- Watchdog: `/usr/bin/timeout`, GNU coreutils 9.4 (unchanged vs reviewed
  Pre-EXECUTE environment; 3-second rehearsal NOT repeated per packet rule).
- Time zone: CST (UTC+8). Generation/authorization record time local
  `2026-09-11 00:27:05 CST`, UTC `2026-09-10 16:27:05 UTC`. Invocation
  start/end times are captured in the operator return, not here.
- Estimator identity: accepted concentration estimator
  `comparison_bench.formal_ir.v72p2d5_gf32_rate_mother.prepare_model_f_prior_candidate`
  with `build_f_model_concentration`, `LAMBDA_STAR = 137.3823795883264`
  (module L46/L274/L2323; manifest `estimator`/`lambda_star`).

## 4. Fresh gates E01–E14 (all PASS; each probe a separate shell command)

- E01 PASS: `git rev-parse HEAD` →
  `4ba36bfb8082b9e3749aa7157f7b8560c4814f41`; `git branch --show-current` →
  `formal-ir-v72p1-addendum-clean`; `git log --oneline -8` shows in order
  `86f6baf6`, `0c304875`, `391fc6b0`, `ca00b234`, `4ba36bfb` (newest first).
- E02 PASS: verdict grep counts exactly 1 each:
  `D7_C_IMPLEMENTATION_REVIEW_PASS` (implementation review),
  `D7_C_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`
  (pre-EXECUTE review),
  `D7_B_LAYER_INTERFACE_CORRECTION_PROPOSAL_PASS_D7_C_NONBLOCKING`
  (layer-interface proposal review). Prereg L79/L90/L217-240 and execution
  packet L13/L44-47 agree with module constants: `MODEL_F_ROOT` accepted root,
  seeds `2026091300..2026091315`, `MAX_CALLS=128`, per-call `120 s`, stored
  wall `1500 s`, outer `1800 s` + grace `30 s`, RSS `2 * 1024**3`.
- E03 PASS: `git status --porcelain` scoped to the core/test/runner files →
  empty (rc 0); `git diff 391fc6b0..HEAD --stat` for the same three files →
  empty (rc 0); `git diff HEAD --stat -- comparison_bench/src/comparison_bench/formal_ir/`
  → empty (rc 0). Frozen implementation/script/tests equal the reviewed
  commits; no content drift.
- E04 PASS: `cycle_state.yaml` matches §1 exactly: `d7c_execution_authorized:
  false` (L6), `decoder_executed: false` (L7), `result_created: false` (L8),
  no attempts/completed fields, gate `D7_C_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`
  (L22/L25), `r1d_state: R1D_PAUSED_PENDING_DECODER_CERTIFICATION_AND_EASY_REGIME`
  (L18), `g1_authorized: false` (L19), `g2_authorized: false` (L20); all other
  execution keys false.
- E05 PASS: `ls -d workspace/d7_c_bidirectional_oracle_*` → no such file
  (rc 2); UUID regex scan over the D7-C cycle dir and OpenSpec change dir →
  `0` matches. No prior D7-C root or UUID.
- E06 PASS: D7-B R2 root
  `workspace/d7_b_easy_regime_c605d1e6-8577-4c52-a865-12500fc8c964/` has
  exactly five files with sizes `1008` (manifest.json), `44743`
  (decoder_records.csv), `80` (report.md), `449` (summary.json), `111`
  (command_log.txt); Model-F root `workspace/v72p2d5_model_f_input/20260907_r1/`
  has `model_f_input.npz` 208467 and `model_f_input_summary.json` 752
  (names/sizes/mtime only, no content read). `ls -d workspace/v72p2d5_g2_20260907_r2`
  → rc 2. Scientific R1d glob `ls -d workspace/d6_graph_mother_r1d_*` → rc 2.
  Observation: the broader `ls -d workspace/*r1d*` glob matched two
  pre-existing, non-scientific D6 test-scratch directories
  (`workspace/d6_r1d_tests_9f3a1c7e4b2a4d8f8e6a0c1d2f4a6b8e`,
  `workspace/d6_r1d_tests_c4e8a2f01d6b4a3c9f5e7a2b8d6c0e4f`, mtime
  Sep 10 10:02–10:11, before the D7-C freeze; empty leaf test dirs only). They
  are not the R1d scientific root, are pre-existing, and cannot alter any
  D7-C number; the R1d/G2 prohibition is intact.
- E07 PASS: protected-root metadata unchanged vs Pre-EXECUTE snapshots:
  `workspace/v72p2d5_g0/20260905_r2` (4 files, dir mtime Sep 6 00:34),
  `workspace/v72p2d5_g1/20260907_r2` (4 files, dir mtime Sep 8 02:39),
  `results` (dir mtime Apr 14 22:14), `comparison_bench/outputs_comparison`
  (dir mtime Sep 10 19:05), plus E06 roots. Names/sizes/mtime only.
- E08 PASS: with the PATH adapter, `command -v python` →
  `/home/karel_303/.venvs/hd-qkd-polar-comparison/bin/python`;
  `python --version` → `Python 3.12.3`;
  `python -c "import sys,numpy; ..."` → `sys.executable` as above, NumPy
  `2.4.4`. Kernel/distro probe (separate command):
  `6.18.33.2-microsoft-standard-WSL2`, `Ubuntu 24.04.4 LTS`.
- E09 PASS: all identities match the reviewed environment exactly (interpreter
  path, CPython 3.12.3, NumPy 2.4.4, WSL2 kernel, Ubuntu 24.04.4 LTS). No
  difference; no compatibility-range exception needed.
- E10 PASS: live stdlib RSS, one command —
  `ru_maxrss 1173432 bytes 1201594368 limit 2147483648`. Finite, positive,
  `< 2 GiB` (`2 * 1024**3`); KiB→bytes rule `ru_maxrss * 1024`.
- E11 PASS: `command -v timeout` → `/usr/bin/timeout`;
  `timeout --version | head -1` → `timeout (GNU coreutils) 9.4`. Binary and
  environment unchanged vs the reviewed Pre-EXECUTE probe; the 3-second
  rehearsal is NOT repeated per packet rule.
- E12 PASS (external cwd `/tmp/d7c_e12_ext`):
  - Reviewed C18 node with the repo `.venv` interpreter from the external cwd
    (absolute paths):
    `.venv/bin/python -m pytest ".../test_v72p2d7_gf32_bidirectional_oracle.py::test_c18_external_cwd_sentinel_reaches_first_decoder_call" -q -p no:cacheprovider --basetemp=/tmp/d7c_e12_bt`
    → `1 passed, 1 warning in 2.63s`.
  - Identity sentinel probe (adapter python from the external cwd; temp probe,
    core unmodified): production decoder bind identity exactly
    `comparison_bench.formal_ir.v35_algorithm_development.decode_row_layered_fftqspa`
    (resolved by the same `d5._load_g0_decoder()` chain; the production bind
    `d5.bind_historical_decoder()` returns its `_bound` adapter wrapper);
    production Model-F loader identity
    `v72p2d5_model_f_input_consumer.load_model_f_input` sourced from
    `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_model_f_input.py`
    via chain entry
    `comparison_bench.formal_ir.v72p2d5_gf32_rate_mother._load_model_f_input_or_blocked`.
    Invocation guard `decode=0 loader=0`; unauthorized in-process CLI path
    returned 3 with the literal refusal; zero D7-C roots created; no Model-F
    artifact content read (probe touched no artifact bytes).
- E13 PASS: unauthorized exact-shape disposable probe
  `timeout -k 30 1800 python scripts/v72p2d7_gf32_bidirectional_oracle.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_c_bidirectional_oracle_E13_DISPOSABLE_BARRED_PROBE`
  printed literally
  `D7-C execution is not authorized; refusing before any work` with `EXIT=3`;
  the probe root was absent (`RC=2`). Never a real UUID.
- E14 PASS: `test -w workspace` → `WORKSPACE_WRITABLE`;
  `ls -d workspace/d7_c_bidirectional_oracle_*` → rc 2 immediately before
  record creation. Nothing pre-created.

Any gate fail would have blocked this record and the UUID. All pass.

## 5. State change and commit (this record)

- Change ONLY `d7c_execution_authorized: false -> true` in
  `docs/research_cycles/V72P2D7-GF32-BIDIRECTIONAL-ORACLE/cycle_state.yaml`.
  No attempt/result fields are added or changed.
- Stage EXACTLY this record + state; commit locally:
  `chore(d7-c): authorize one frozen bidirectional-oracle invocation`; no push.
- New root reconfirmed ABSENT after commit. Commit SHA recorded in the return.

## 6. Once-only / prohibition / ceiling

- Authorization is consumed by the first scientific-decoder attempt regardless
  of outcome; no retry/rerun/resume/re-root/re-param/replacement-UUID under any
  outcome. Exactly 128 frozen calls on normal completion; no early-success stop,
  no replacement cell; per-call watchdog 120 s, stored wall <= 1500 s, outer
  GNU timeout 1800 s + 30 s grace.
- No R1d, no `--phase`, no formal G1/G2, no CAL/VAL/parquet/raw/real/VOID, no
  cross-layer APP, no formal content reads beyond metadata-only checks.
- After process return and before interpretation, flip ONLY true→false and
  commit alone (`chore(d7-c): consume and revoke one-shot execution
  authorization`). `scientific_attempt_consumed: true` only if at least one
  decoder attempt is evidenced; otherwise `NOT_VERIFIABLE`, never a retry basis.
- This record authorizes execution only; accepts no scientific result. No FER,
  leakage, key-rate, qualification or general algorithm-success claim; the D7-C
  run is an internal diagnostic only. Independent Pre-RESULT R1 is mandatory
  before any result root/return/summary is committed.

(End of record)
