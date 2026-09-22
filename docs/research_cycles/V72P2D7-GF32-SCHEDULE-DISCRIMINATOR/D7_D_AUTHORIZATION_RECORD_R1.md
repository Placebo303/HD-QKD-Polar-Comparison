# D7-D authorization record R1 — one frozen schedule-discriminator invocation

- Authority: `.workbuddy/tasks/D7_D_SCHEDULE_DISCRIMINATOR_EXECUTE_PRE_RESULT_R1_TASK_PACKET.md`
  §0 (verbatim authorization), §3–§5; frozen execution packet
  `D7_D_EXECUTION_PACKET_R1.md`; prereg `D7_D_PREREG_R1.md`; implementation
  review `D7_D_IMPLEMENTATION_REVIEW_R1.md` (PASS); Pre-EXECUTE review
  `D7_D_PRE_EXECUTE_REVIEW_R1.md` (PASS_AWAITING_EXPLICIT_AUTHORIZATION).
- Repository `HD-QKD_Polar_Comparison` (WSL); branch
  `formal-ir-v72p1-addendum-clean`; entry HEAD
  `63f91d265d5eb540d6ca2726a27cd84fb1028b45`.
- Authorization time: 2026-09-11T07:25:37+0800 (UTC 2026-09-10T23:25:37Z),
  after E01–E14 all passed and before the UUID target was instantiated.
- UUID (generated once, UUID v4): `64660d16-397d-4ef3-8454-3066d27c12c7`.
- Root (fresh direct child of `workspace/`, confirmed absent twice before this
  record and once again after the authorization commit):
  `workspace/d7_d_schedule_discriminator_64660d16-397d-4ef3-8454-3066d27c12c7`.

## 0. Verbatim authorization (exact copy of task packet §0)

> 我现在明确授权执行 D7-D flooding-vs-layered schedule discriminator：仅允许按冻结的
> `D7_D_EXECUTION_PACKET_R1.md`，在已评审的 WSL venv-on-PATH 环境中，使用冻结命令对一个
> 全新的 `workspace/d7_d_schedule_discriminator_<uuid>/` 根调用一次；共 256 个冻结
> scientific decoder calls，授权由首次 scientific decoder 尝试消耗，不因失败、超时、
> 部分结果或环境异常恢复；不得重试、重跑、恢复、复用根、修改参数或改变 estimator、
> prior、矩阵、seed、decoder 配置及 schedule 顺序；不得执行 R1d、任何 `--phase`、正式
> G1/G2、CAL、VAL、real/raw 或跨层 APP。执行结束后立即回收授权并进行独立 Pre-RESULT
> 复审；复审通过前不得接受或提交结果。

## 1. Exact future command (invoked exactly once)

```bash
timeout -k 30 1800 python scripts/v72p2d7_gf32_schedule_discriminator.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_d_schedule_discriminator_64660d16-397d-4ef3-8454-3066d27c12c7
```

- WSL cwd: repository root `/mnt/d/Code/HD-QKD_Polar_Comparison`.
- Reviewed venv-on-PATH adapter (activated as a separate operation; `PYTHONPATH`
  is never used): `PATH="$HOME/.venvs/hd-qkd-polar-comparison/bin:$PATH"`.
- No added flags, pipes, tee, redirection, concurrency, alternate Python or
  alternate root. The parent harness preserves the child argv exactly.

## 2. E01–E14 gate evidence (each check run before UUID generation)

- **E01 PASS** — branch `formal-ir-v72p1-addendum-clean`; `git rev-parse HEAD` =
  `63f91d265d5eb540d6ca2726a27cd84fb1028b45`; commit order
  `63f91d26 -> 727bca7a -> 43f07186 -> 3a058992 -> 1f472c2a` (`docs(d7-d): record
  pre-execute review and readiness closeout` at entry).
- **E02 PASS** — unique verdicts `D7_D_IMPLEMENTATION_REVIEW_PASS`
  (`D7_D_IMPLEMENTATION_REVIEW_R1.md` Verdict lines) and
  `D7_D_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`
  (`D7_D_PRE_EXECUTE_REVIEW_R1.md` Verdict lines); no competing
  FAIL/BLOCKED verdict in the cycle; the frozen command string is byte-identical
  in task packet §2, `D7_D_EXECUTION_PACKET_R1.md` and the Pre-EXECUTE review.
- **E03 PASS** — implementation commit `43f07186` adds exactly four files,
  insertions only (core 1395, tests 1535, certification doc 50, runner 104);
  `git diff 43f07186..HEAD` and `git diff HEAD` are empty for core/tests/runner/
  certification doc, and empty for predecessor modules
  (`v72p2d7_gf32_bidirectional_oracle.py`, `v72p2d7_gf32_decoder_certification.py`,
  `v35_algorithm_development.py`, `v72p2d5_gf32_rate_mother.py`,
  `v72p2d5_model_f_input.py`, `v72p2d7_gf32_easy_regime.py`). Frozen constants
  verified: `LAMBDA_STAR=137.3823795883264`, `DECODER_FLOOR=1e-15`, `MAX_ITER=90`,
  `F_VALUES=(1.0,1.2)`, L1 rows 49/59, L2 rows 43/52, seeds 2026091300..2026091315,
  graph seeds 2026090501/2026090502, `MAX_CALLS=256`, per-call watchdog 120 s,
  stored wall 1500 s, outer 1800 s + 30 s, `RSS_LIMIT_BYTES=2*1024**3`.
- **E04 PASS** — `cycle_state.yaml`: `plan_accepted: false`,
  `implementation_authorized: false`, `d7d_execution_authorized: false`,
  `decoder_executed: false`, `result_created: false`,
  `formal/synthetic/real_execution_authorized: false`,
  `scientific_promotion: false`, `g1_authorized: false`, `g2_authorized: false`;
  `next_gate` and `d7d_readiness_state` =
  `D7_D_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`; state file clean vs HEAD and the
  cycle directory has no worktree diff.
- **E05 PASS** — `find workspace -maxdepth 1 -name 'd7_d*'` empty; UUID-pattern
  scan (`d7_d_schedule_discriminator_<8hex>-`) over `docs/`, `.workbuddy/`,
  `scripts/`, `comparison_bench/src`, `comparison_bench/tests`, `openspec/`
  returned no match. Zero D7-D roots, zero prior UUID.
- **E06 PASS** — D7-C root `workspace/d7_c_bidirectional_oracle_94c0ea15-a786-4cb8-a991-6fec521cccae/`:
  six files `command_log.txt` 282, `decoder_records.csv` 23599, `manifest.json`
  2709, `paired_summary.csv` 1130, `report.md` 362, `summary.json` 728 B, all
  mtime 1789058019. D7-B root
  `workspace/d7_b_easy_regime_c605d1e6-8577-4c52-a865-12500fc8c964/`: five files
  111/44743/1008/80/449 B, mtime 1789043618. Model-F root
  `workspace/v72p2d5_model_f_input/20260907_r1/`: `model_f_input.npz` 208467 B,
  `model_f_input_summary.json` 752 B, mtime 1788718027. R1d
  (`workspace/d6_graph_mother_r1d_*`) and G2 (`workspace/v72p2d5_g2/20260906_r1`)
  absent.
- **E07 PASS** — all 11 protected roots exist (D5 G0/G0-recovery/P0-cost/G1×2/
  structure, D6 R1/R1c, D7-B, D7-C, Model-F); a 60-entry names/sizes/mtime
  snapshot (`find -printf`, metadata only, no content read) is identical
  before/after all gate commands (`PROTECTED_METADATA_IDENTICAL`); D7-C, D7-B and
  Model-F match the Pre-EXECUTE review record exactly.
- **E08 PASS** — reviewed venv-on-PATH adapter resolves `python` to
  `/home/karel_303/.venvs/hd-qkd-polar-comparison/bin/python`; bare `python` is
  absent on the default PATH (adapter required); no `PYTHONPATH` used.
- **E09 PASS** — CPython 3.12.3; NumPy 2.4.4 (`sys.prefix`
  `/home/karel_303/.venvs/hd-qkd-polar-comparison`); kernel
  `6.18.33.2-microsoft-standard-WSL2`; Ubuntu 24.04.4 LTS. Identical to the
  reviewed execution environment; no compatibility allowance needed.
- **E10 PASS** — fresh stdlib probe: `ru_maxrss = 1257320 KiB` →
  `1287495680` bytes, finite, positive, `< 2 GiB` (`2147483648`). Environmental
  note carried from the Pre-EXECUTE review: this sandbox reports a constant
  inflated `ru_maxrss` (unchanged after a 300 MB allocation) while `/proc`
  `VmHWM` is ~10 MB; the measured value is deterministic and in-bounds for both
  the preflight and the T4 rule.
- **E11 PASS** — `command -v timeout` = `/usr/bin/timeout`; `timeout --version`
  = GNU coreutils 9.4, identical to the recorded D7-C/D7-D environment. Because
  the environment and executable are unchanged, the trivial 3 s `timeout`
  rehearsal was skipped per packet §3; the `-k 30 1800` argument form is
  unchanged and matches the frozen command.
- **E12 PASS** — from external cwd `/tmp/opencode/d7d_exec_r1/extcwd` with the
  repo reachable only through the runner's `__file__`-derived `sys.path` insert:
  `bind_schedule_decoders()["ROW_LAYERED"].target is
  v35.decode_row_layered_fftqspa` and `["FLOODING"].target is
  v35.decode_flooding_fftqspa`; sentinel dispatch reached both schedules with
  frozen shapes `(2,4)/(4,32)/(2,)`; counter wrappers installed on both
  production attributes before a rebind recorded `production_calls={'row': 0,
  'flood': 0}`; D5 and default Model-F loader sentinels recorded
  `loader_calls={'d5': 0, 'default': 0}`; audit hook recorded zero
  `model_f_input` opens; no `workspace/d7_d*` root and no probe root created.
- **E13 PASS** — exact-shape unauthorized probe
  (`workspace/d7_d_schedule_discriminator_e13_unauthorized_probe`) printed
  `D7-D execution is not authorized; refusing before any work`, exit 3; an
  audit-hook process confirmed `v35_algorithm_development` not bound, zero
  Model-F opens and no root created.
- **E14 PASS** — `workspace/` writable (temporary probe file created and
  removed); the selected UUID target was never pre-created; no `d7_d*` root
  exists at authorization time.

## 3. Environment and interpreter

- Adapter: `PATH="$HOME/.venvs/hd-qkd-polar-comparison/bin:$PATH"` (execution
  authorization environment note `VENV_PYTHON_ON_PATH_ADAPTER_REQUIRED_AT_EXECUTION_AUTHORIZATION`).
- Interpreter: `/home/karel_303/.venvs/hd-qkd-polar-comparison/bin/python`
  (CPython 3.12.3, NumPy 2.4.4).
- OS: Ubuntu 24.04.4 LTS on kernel `6.18.33.2-microsoft-standard-WSL2`.
- GNU timeout: `/usr/bin/timeout` (coreutils 9.4), frozen form `-k 30 1800`.
- Carried non-blocking notes from the Pre-EXECUTE review: F01 certification-doc
  quoted value vs observed `2.2204e-16` (both `<= 1e-10`); ROW_LAYERED binds
  `v35.decode_row_layered_fftqspa` directly (same function object/kwargs as the
  D5 adapter, raw `DecoderResult` status); out-root UUID format is an
  operator convention (code enforces direct-child + prefix).

## 4. Frozen 256-call contract

- 128 identities (16 seeds × 2 f × 4 conditions); two schedules per identity:
  exactly 256 calls, `call_idx = 2*identity_idx - 1` (`ROW_LAYERED`) /
  `2*identity_idx` (`FLOODING`).
- Order: `for f in [1.0,1.2]: for seed in 2026091300..2026091315: for condition
  in [L1_MARGINAL, L1_ORACLE_U2, L2_MARGINAL, L2_ORACLE_U1]: ROW_LAYERED then
  FLOODING`. No early-success stop; no replacement cell; each decoder keeps its
  own internal stopping.
- `max_iter=90`, cold start, `damping_alpha=1.0` for row-layered; flooding has
  no damping/warm-start parameter. Schedule is the only per-pair delta.
- Budgets: hard cap 256 calls; per-call watchdog 120 s; stored scientific wall
  `<= 1500 s`; outer GNU `timeout -k 30 1800`; RSS `< 2 GiB` via stdlib
  `resource` KiB→bytes. Zero retry/rerun/resume/concurrency.
- Evidence: fresh `workspace/d7_d_schedule_discriminator_64660d16-397d-4ef3-8454-3066d27c12c7/`
  with no subdirectories and exactly seven scalar text files (`manifest.json`,
  `decoder_records.csv`, `paired_schedule.csv`, `stratum_summary.csv`,
  `summary.json`, `report.md`, `command_log.txt`); no raw beliefs/symbols/
  priors/syndromes persisted.

## 5. One-attempt consumption rule

- This authorization covers exactly one invocation of the §1 command against
  the single UUID root above.
- It is consumed by the first scientific decoder attempt, regardless of success,
  failure, timeout, partial result or environment anomaly. No retry, rerun,
  resume, root reuse, flag/parameter/estimator/prior/matrix/seed/decoder/
  schedule change.
- On process return the authorization key is immediately flipped back to
  `false` and committed alone (consume and revoke) before any result content is
  interpreted. If no decoder attempt is evidenced, the scientific attempt is
  recorded `NOT_VERIFIABLE` and the authorization is not restored.

## 6. Claim ceiling

- Permitted: per-`(f,layer,condition)` stratum classification from the frozen
  five labels; one run terminal from the frozen ten-entry priority; per-identity
  paired exact/syndrome outcomes; work-normalized descriptive differences.
- Not permitted: FER, leakage, reconciliation efficiency, key rate, protocol
  recovery, cross-layer APP viability, interface acceptance, code qualification,
  R1d/G1/G2 readiness, promotion, or any general GF32/NB-LDPC conclusion. The
  classifications are route discriminators, not success-rate estimates. Oracle
  conditions are counterfactual diagnostics only.
- Result acceptance requires the independent Pre-RESULT review and the main
  thread; this record and any subsequent operator return grant no acceptance.
