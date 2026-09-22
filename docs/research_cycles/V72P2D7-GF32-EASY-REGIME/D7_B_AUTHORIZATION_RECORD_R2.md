# D7-B authorization record R2 (one fresh WSL easy-regime invocation)

## 0. Verbatim fresh authorization (§0 sole authority for WSL R2)

> 我现在明确重新授权执行 D7-B easy-regime（WSL R2，与此前已耗尽的授权和 UUID
> 无关）：仅允许按 `D7_B_EXECUTION_PACKET_R1.md` 及
> `D7_B_EXECUTION_PACKET_ADDENDUM_WSL_A1.md`，使用命令
> `timeout -k 30 1800 python scripts/v72p2d7_gf32_easy_regime.py --out-root
> workspace/d7_b_easy_regime_<new_uuid>` 对一个全新的 UUID 根调用一次；授权由首次
> scientific decoder 尝试消耗，不因失败、超时、部分结果或启动异常恢复；不得重试、
> 重跑、恢复、复用任何旧 UUID 或修改参数；不得执行 R1d、任何 `--phase`、正式
> G1/G2、Model-F、CAL、VAL、real/raw。执行结束后立即回收授权并进行独立
> Pre-RESULT 复审，复审通过前不得接受或提交结果。

This fresh authority applies only to WSL R2. It does not revive the prior
authorization or UUID `0f1ad3ec-f9e0-463f-a7dd-d9880ff7230c` (permanently dead:
never reuse/retry/resume/re-param; prior R1 blocked launch + lifecycle commits
+ return + review + disposition stay immutable).

## 1. UUID and target root (sole R2 UUID, generated exactly once)

- UUIDv4: `c605d1e6-8577-4c52-a865-12500fc8c964`
- Source: single read of `/proc/sys/kernel/random/uuid` (exactly one generation;
  no second UUID exists in this task; no UUID was generated before E01–E12).
- Target root (relative, runtime-derived): `workspace/d7_b_easy_regime_c605d1e6-8577-4c52-a865-12500fc8c964`
- Root confirmed ABSENT immediately after generation and reconfirmed ABSENT
  after the authorization commit (see §5).
- Parent `workspace/` writable. Root NOT pre-created.

## 2. Exact instantiated command (exactly-once invocation)

```bash
timeout -k 30 1800 python scripts/v72p2d7_gf32_easy_regime.py --out-root workspace/d7_b_easy_regime_c605d1e6-8577-4c52-a865-12500fc8c964
```

- Instantiation: frozen WSL-A1 shape with `<new_uuid>` replaced by the sole R2
  UUID above. No added args, PYTHONPATH, env overrides, pipes, tee,
  redirection, or wrappers. A timing harness may spawn it as a child with argv
  exactly as above.
- Interpreter resolution: bare `python` is absent on default PATH; the WSL
  project venv (`python` resolved via the execution environment) provides
  CPython 3.12.3 / NumPy 2.4.4 (see §3 E08). No science parameter changes.
- This scientific command is invoked at most once. Startup failure, exit 124,
  nonzero exit, partial root, missing file, or unexpected terminal never
  permits another invocation, replacement UUID, or re-param.

## 3. WSL environment (runtime-observed facts, not science parameters)

- Repo root derived at runtime via `pwd` (current WSL checkout).
- Branch: `formal-ir-v72p1-addendum-clean`; HEAD: `48a5d398` (short `48a5d39`).
- Interpreter: `/home/karel_303/.venvs/hd-qkd-polar-comparison/bin/python`,
  Python 3.12.3, NumPy 2.4.4.
- WSL: `Linux 6.18.33.2-microsoft-standard-WSL2`, Ubuntu 24.04.4 LTS.
- Watchdog: `/usr/bin/timeout`, GNU coreutils 9.4 (also `/bin/timeout`).
- Time zone: CST (UTC+8). Record time local `2026-09-10 20:30:58 CST`,
  UTC `2026-09-10 12:30:58 UTC`. Invocation start/end times are captured in
  the operator return, not here.

## 4. Fresh gates R2-E01–E12 (all PASS before this record; no UUID existed yet)

- E01 PASS: branch `formal-ir-v72p1-addendum-clean`; HEAD `48a5d398`;
  `git log --oneline --reverse | grep` yields in order `13c1c3c`, `cc387e7`,
  `04b7a8e`, `4b61039`, `48a5d39`.
- E02 PASS: `D7_B_EXECUTION_PACKET_R1.md` + `D7_B_EXECUTION_PACKET_ADDENDUM_WSL_A1.md`
  + `D7_B_WSL_LAUNCH_REWORK_REVIEW_PASS` + `D7_B_PRE_EXECUTE_REVIEW_PASS_WSL_R2_AWAITING_FRESH_AUTHORIZATION`
  agree (WSL shell-spelling-only change; inner script/args/root-pattern/UUID
  rule/matrix/budgets/one-attempt/prohibitions unchanged; both reviews authorize
  nothing and generate no UUID).
- E03 PASS: `git diff --name-only HEAD -- scripts/ comparison_bench/src/
  comparison_bench/tests/test_v72p2d7_gf32_easy_regime.py` empty;
  `git diff 04b7a8e..HEAD --stat -- <same scoped paths>` empty (exit 0).
  v35/D5/D7-A/constants/schema: zero diff under `comparison_bench/src/`
  (core free of science drift per rework review L11).
- E04 PASS: `cycle_state.yaml` matches §1 exactly: `d7b_execution_authorized:
  false`, attempts/completed `0/0`, `decoder_executed: false`,
  `result_created: false`, `next_gate:
  D7_B_WSL_READY_AWAITING_FRESH_EXPLICIT_AUTHORIZATION`, all other execution
  keys false.
- E05 PASS: `ls -d workspace/d7_b_easy_regime_*` → no such file; target old root
  `workspace/d7_b_easy_regime_0f1ad3ec-f9e0-463f-a7dd-d9880ff7230c` ABSENT;
  `grep -c 0f1ad3ec cycle_state.yaml` → 0; old UUID permanently barred.
- E06 PASS: no R2 UUID generated before gates; parent `workspace/` WRITABLE;
  protected metadata only (see E07).
- E07 PASS: `ls -d workspace/*v72p2d7*` → no such file (D7-B/R1d/G2 roots all
  absent); protected present: `workspace/v72p2d5_g0/20260905_r2` (4096,
  2026-09-06 00:34:34 +0800), `workspace/v72p2d5_g1/20260907_r2` (4096,
  2026-09-08 02:39:50 +0800), `comparison_bench/outputs_comparison` (4096,
  2026-09-10 19:05:51 +0800), `results` (4096, 2026-04-14 22:14:11 +0800).
- E08 PASS: sys.executable `/home/karel_303/.venvs/hd-qkd-polar-comparison/bin/python`;
  Python 3.12.3; NumPy 2.4.4; kernel `6.18.33.2-microsoft-standard-WSL2`;
  distro Ubuntu 24.04.4 LTS (matches renewed review).
- E09 PASS: live RSS `9453568` bytes (positive integer < 2147483648), separate
  single-purpose command.
- E10 PASS: `which -a timeout` → `/usr/bin/timeout`, `/bin/timeout`;
  `timeout --version` → GNU coreutils 9.4 (matches reviewed impl); binary/WSL
  unchanged vs renewed review → rehearsal NOT repeated per packet rule.
- E11 PASS: external cwd `/tmp/d7b_e11_ext`, `env -u PYTHONPATH`, initial
  `sys.path` clean (`INIT_PATH_CLEAN`); `bind_historical_decoder()` returns
  exactly `comparison_bench.formal_ir.v35_algorithm_development.decode_row_layered_fftqspa`
  (`FN_MOD` same, `IS_V35: True`, `PKG: comparison_bench.formal_ir`);
  callable NEVER invoked; `workspace/d7_b_easy_regime_*` still absent
  (`BIND_EXACT_V35_ZERO_CALL_ZERO_ROOT`).
- E12 PASS: unauthorized exact-shape disposable probe
  `timeout -k 30 1800 <venv-python> scripts/v72p2d7_gf32_easy_regime.py --out-root
  workspace/d7_b_easy_regime_E12_DISPOSABLE_BARRED_PROBE` → literal
  `D7-B execution is not authorized; refusing before any work`, exit 3,
  target ABSENT (refusal pre-bind pre-root; never the scientific UUID; creates
  nothing).

Any gate fail would have blocked this record. All pass.

## 5. State change and commit (this record)

- Change ONLY `d7b_execution_authorized: false -> true` in
  `docs/research_cycles/V72P2D7-GF32-EASY-REGIME/cycle_state.yaml`.
  No attempt/result fields change yet.
- Stage EXACTLY this record + state; commit locally:
  `chore(d7-b): authorize one fresh WSL R2 easy-regime invocation`; no push.
- New root reconfirmed ABSENT after commit.

## 6. Once-only / prohibition / ceiling

- Authorization consumed by the first scientific-decoder attempt regardless of
  outcome; no retry/rerun/resume/re-root/re-param/replacement-UUID under any
  outcome. No R1d, no `--phase`, no G1/G2, no Model-F/CAL/VAL/real/raw/VOID,
  no formal content reads beyond metadata-only checks.
- After process return and before interpretation, flip ONLY true→false and
  commit alone (`chore(d7-b): consume and revoke WSL R2 execution authorization`).
  `command_invocations: 1` always after launch; `scientific_attempt_consumed:
  true` only if ≥1 decoder attempt evidenced else `NOT_VERIFIABLE` (never a
  rerun basis).
- This record authorizes execution only; accepts no scientific result. No
  FER/leakage/key-rate/qualification claim. Independent Pre-RESULT R2 mandatory
  before any result root/return is committed.

(End of file)
