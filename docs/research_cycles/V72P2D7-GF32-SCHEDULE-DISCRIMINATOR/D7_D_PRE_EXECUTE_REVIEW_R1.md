# D7-D Pre-EXECUTE review R1 (independent WSL reviewer)

## 0. Verdict, scope, independence

- Verdict: **D7_D_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION**.
- PASS grants nothing. It generates no UUID, flips no authorization, authorizes no
  execution and makes no scientific call. It means the frozen readiness is
  internally coherent and ready for a future explicit one-shot authorization.
- Authority: `.workbuddy/tasks/D7_C_ACCEPT_D7_D_SCHEDULE_FREEZE_IMPLEMENT_PRE_EXECUTE_R1_TASK_PACKET.md`
  §4–§13; `D7_D_PREREG_R1.md`; `D7_D_EXECUTION_PACKET_R1.md` (commit `3a05899`);
  `D7_D_IMPLEMENTATION_REVIEW_R1.md` (PASS); `D7_D_FLOODING_CERTIFICATION_R1.md`.
- Independence: this reviewer is a separate context from the implementer and from
  the implementation reviewer, authored none of the reviewed files, and did not
  participate in the implementation. Review-only: the sole write of this review is
  this file. No commit, no UUID generation, no authorization flip, no real
  Model-F content, no scientific call, no push.
- Environment: WSL2; review commands run with a fresh `/tmp` basetemp
  (`/tmp/d7d_preexec_r1/...`) and `-p no:cacheprovider` where pytest was used;
  probes ran from an external cwd `/tmp/d7d_preexec_r1/cwd`.
- Review timestamp: 2026-09-10T18:34Z (WSL local 2026-09-11T02:34+0800).

## 1. Revision and freeze diff

- Branch `formal-ir-v72p1-addendum-clean`; HEAD `727bca7ab574c589246add9bb1d8680423163937`.
- Implementation commit `43f071868a497b4ca5fd1f2db7eaea3a08146651` adds exactly four
  files (insertions only): core, tests, certification doc, runner.
- Review commit `727bca7ab...` adds only
  `D7_D_IMPLEMENTATION_REVIEW_R1.md` (274 lines).
- Freeze check on the four D7-D artifacts:
  `git diff --stat 43f07186..HEAD -- <core> <tests> <cert> <runner>` → **empty**
  (`FROZEN`), and `git diff HEAD -- <same paths>` after all review commands →
  **empty** (`FROZEN_AFTER_RUNS`). The four reviewed artifacts are byte-identical
  between `43f07186` and HEAD and in the worktree.
- `git rev-list --left-right --count origin/formal-ir-v72p1-addendum-clean...HEAD`
  → `0	103`: HEAD is 103 commits ahead, nothing pushed. HEAD unchanged throughout
  this review.

## 2. Exact 256-call matrix and frozen command

Independent static reproduction (probe, no repo imports other than the module
itself; literal expected loop built in the probe):

```text
MATRIX_OK calls=256 identities=128
first=(1, 1.0, 2026091300, 'L1_MARGINAL', 'ROW_LAYERED')
last=(256, 1.2, 2026091315, 'L2_ORACLE_U1', 'FLOODING')
```

- The probe rebuilt the expected sequence as
  `for f in [1.0,1.2]: for seed in 2026091300..2026091315: for condition in
  [L1_MARGINAL,L1_ORACLE_U2,L2_MARGINAL,L2_ORACLE_U1]: ROW_LAYERED; FLOODING`
  and compared element-by-element against `frozen_call_matrix()`: exact equality
  of `(call_idx, f, seed, condition, schedule)`, `call_idx` 1..256, schedule pairs
  `2k-1/2k` sharing the identity, stride-4 condition blocks with one seed each,
  `f=1.0` identities 1..64 and `f=1.2` identities 65..128.
- `--dry-run` from an external cwd printed 257 lines (header
  `calls=256 schedules=['ROW_LAYERED', 'FLOODING'] budget=256` + 256 call lines),
  exit 0; first line `1 1 ROW_LAYERED L1_MARGINAL 2026091300 1.0 L1 49`, last
  `256 128 FLOODING L2_ORACLE_U1 2026091315 1.2 L2 52`.
- Hard cap / no retry: `execute_calls` is a single sequential `for` over the frozen
  matrix with `MAX_CALLS` cap, `break` on the first higher-priority stop, no
  replacement/retry/resume, no thread/async/subprocess/concurrency construct in
  core or runner. S12 (in the 30-passed rerun) pins crash-at-call-40 → exactly 40
  attempted calls, no retry; S13 pins the 120/1500/1800/2 GiB gates; manifest and
  summary carry `retries/reruns/resumes = 0`.

Future command (frozen, not run):

```bash
timeout -k 30 1800 python scripts/v72p2d7_gf32_schedule_discriminator.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_d_schedule_discriminator_<uuid>
```

- CLI contract confirmed from live `--help`: exactly `--model-f-root`, `--out-root`,
  `--dry-run`, `--verify`; the frozen command's two options map to
  `--model-f-root` (must equal the accepted root) and `--out-root` (fresh direct
  child `workspace/d7_d_schedule_discriminator_<uuid>`).
- **No UUID exists yet**: targeted scan for `d7_d_schedule_discriminator_<8hex>-`
  over `docs/`, `.workbuddy/`, `scripts/`, `comparison_bench/src`,
  `comparison_bench/tests`, `openspec/` → no match; `workspace/` has no
  `d7_d*` entry (§5). Core/runner contain no `uuid` import or `os.urandom`; the
  manifest only slices the prefix from the operator-supplied root name.

## 3. Model-F metadata only; dual sentinel reachability

Model-F root `workspace/v72p2d5_model_f_input/20260907_r1/`, recorded by
names/sizes/mtime only (before and after all review commands, unchanged):

| File | Bytes | mtime (epoch s) |
|------|-------|-----------------|
| `model_f_input.npz` | 208467 | 1788718027 |
| `model_f_input_summary.json` | 752 | 1788718027 |

- Zero binary content read: this reviewer only `stat`-ed the files. A Python
  audit-hook probe (`open`/`os.open` paths containing `model_f_input`) recorded
  **zero** Model-F opens during runner import, the unauthorized path and
  `--dry-run`; the runner refuses before any load and the default loader is only
  reachable through the authorized `prepare_inputs` path. Tests inject fake
  Model-F loaders and F08 poisons the real loaders.

Dual sentinel reachability, reproduced from a fresh `/tmp` cwd with the repo
reachable only through the runner's own `__file__`-derived `sys.path` insert
(established S17/S18 pattern):

```text
SENTINEL_OK events=[('row', (2, 4), (4, 32), (2,)), ('flood', (2, 4), (4, 32), (2,))]
production_calls={'row': 0, 'flood': 0} root_absent=True
```

- `bind_schedule_decoders()["ROW_LAYERED"].target is
  v35.decode_row_layered_fftqspa` and `["FLOODING"].target is
  v35.decode_flooding_fftqspa` (exact object identity), wrapper names
  `row_layered` / `flooding`.
- Counter evidence: counting wrappers installed on both production attributes
  before a rebind are the bound `.target`s, and both counters stayed 0 during the
  sentinel dispatches; the sentinel fakes were reached with the frozen shapes and
  raised (production functions were never invoked). No root was created; no
  `workspace/d7_d_schedule_discriminator_*` entry exists.

## 4. RSS, GNU timeout and environment

- RSS path: `resource.getrusage(resource.RUSAGE_SELF).ru_maxrss` in
  `_read_ru_maxrss`, explicit `* 1024` KiB→bytes in `get_rss_bytes`; the source
  contains no `psutil`; `_probe_rss_valid` rejects `None`, non-numeric, non-finite
  and non-positive probes; the preflight raises `PreflightBlocked`
  (`D7_D_PRE_EXECUTION_BLOCKED`) before any call when RSS is unavailable. S14 (in
  the 30-passed rerun) exercises `None/0/-5/nan/inf` fail-closed with zero
  decoder/sampler/Model-F events.
- Live current-process value (fresh interpreter): `ru_maxrss = 68860 KiB` with the
  package import path → `get_rss_bytes() = 70512640` bytes, positive, finite,
  `< 2 GiB`; the file-path fallback interpreter measured `28196 KiB →
  28872704` bytes. `RSS_LIMIT_BYTES = 2147483648`. (A first parallel probe
  reported an inflated `1257320 KiB`; it did not reproduce in isolated runs and
  does not affect the logic — every observed value is positive/finite/`< 2 GiB`.)
- Budget semantics: preflight blocks on *unavailable* RSS; an RSS `>= 2 GiB`
  observed after a call is the T4 `D7_D_RESOURCE_OVERRUN` stop (S13: 1 record
  then stop). This matches prereg §10's unavailable-blocks-first-call vs packet
  T4 resource-terminals split.
- GNU timeout / environment comparison vs the D7-C record:

| Item | D7-C record | Live | Match |
|------|-------------|------|-------|
| `command -v timeout` | `/usr/bin/timeout` | `/usr/bin/timeout` | yes |
| `timeout --version` head | GNU coreutils 9.4 | `timeout (GNU coreutils) 9.4` | yes |
| Execution python | venv CPython 3.12.3 | `/home/karel_303/.venvs/hd-qkd-polar-comparison/bin/python` 3.12.3 | yes |
| NumPy (execution venv) | 2.4.4 | 2.4.4 | yes |
| Kernel | `6.18.33.2-microsoft-standard-WSL2` | `6.18.33.2-microsoft-standard-WSL2` | yes |
| Distro | Ubuntu 24.04.4 LTS | Ubuntu 24.04.4 LTS | yes |
| Bare `python` on default PATH | absent (adapter required) | absent | yes |

- Environment **unchanged** vs the recorded D7-C execution environment → the GNU
  `timeout` invocation rehearsal (trivial 3 s command expecting exit 124) is
  **skipped**, with the comparison recorded above as the reason. `timeout -k 30
  1800` argument form is unchanged and matches the frozen command.
- Test interpreter note: the repo `.venv` (used only for pytest) is CPython 3.12.3
  with NumPy 2.5.3 and pytest 9.1.1; the frozen execution environment is the venv
  with NumPy 2.4.4. Tests are test-only and do not exercise the execution venv.

## 5. Target absence, unauthorized refusal, dry-run, help

- Target absence before and after all commands:
  `find workspace -maxdepth 1 -name 'd7_d*' -print` → **no output** (exit 0).
  No `workspace/d7_d_schedule_discriminator_*` root and no UUID exist. (`d7_b_*`
  and `d7_c_*` roots are the frozen predecessors, untouched.)
- Unauthorized run with the exact frozen command shape (probe name replacing
  `<uuid>`), repo cwd:

```text
$ python scripts/v72p2d7_gf32_schedule_discriminator.py \
    --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 \
    --out-root workspace/d7_d_schedule_discriminator_reviewer_unauthorized_probe
D7-D execution is not authorized; refusing before any work
exit=3
```

  Audit-hook evidence in the same process: `v35_algorithm_development` **not**
  bound, zero Model-F opens, target not created.
- `--dry-run` from `/tmp` cwd: exit 0, 257 lines (frozen matrix), no decoder bind
  (`v35_algorithm_development` absent from `sys.modules`), zero Model-F opens, no
  root. `--help` exit 0 from both repo and external cwd and lists the four frozen
  options.
- Refusal ordering confirmed in source: pure out-root contract check → cycle-state
  read → authorization key → Model-F root match → run. All refusals exit 3 before
  any decoder bind, Model-F read or root creation.

## 6. Tests and C19 classification

- `py_compile` of core, tests and runner: **clean** (exit 0).
- New D7-D suite re-run once with `-p no:cacheprovider` and a fresh `/tmp`
  basetemp: **`30 passed, 1 warning in 111.07s`** (exit 0) — 22 S-items + 8
  F-items. S20's inner assertions pin the related regressions (D7-A 14 passed;
  D7-C 19 passed + 1 deselected; D5 165 passed; D7-B 29 passed; v35 25 passed).
- C19 independently re-checked by running the frozen D7-C test **raw**:
  `test_c19_protected_root_lifecycle_and_g2_r1d_absence` → `1 failed` at
  `comparison_bench/tests/test_v72p2d7_gf32_bidirectional_oracle.py:1000`
  (`assert list(WS.glob(bo.OUT_ROOT_PREFIX + "*")) == []`), because the accepted
  D7-C root `workspace/d7_c_bidirectional_oracle_94c0ea15-...` now exists as the
  frozen baseline (the same test's `decoder_executed/result_created is False`
  assertions are stale too).
- Classification **confirmed**: legitimate stale pre-execution environmental
  invariant. The file is unchanged since its introduction (`391fc6b0`,
  pre-execution) and is not modified by D7-D (`git diff 43f07186..HEAD` and
  worktree diff are empty for it). The S20 deselection is scoped to exactly that
  one test via `-k not test_c19_...`, asserts `19 passed`/`1 deselected`, and the
  reason is recorded in the test docstring/comment. Non-blocking; the packet
  forbids D7-C edits, so deselection-with-documentation is the correct in-scope
  behavior. Suggested separate scoped follow-up: refresh `test_c19` to
  post-acceptance invariants.

## 7. Protected roots, state, no-push, dirty preservation

- D7-C root six files after all review commands (byte sizes / mtime epoch s, all
  identical to the pre-review reading and to the implementation review record):
  `command_log.txt` 282, `decoder_records.csv` 23599, `manifest.json` 2709,
  `paired_summary.csv` 1130, `report.md` 362, `summary.json` 728; mtime
  1789058019 for all six. Immutable.
- D7-B root `d7_b_easy_regime_c605d1e6-...` unchanged: 111/44743/1008/80/449 B,
  mtime 1789043618.
- D7-D `cycle_state.yaml` (unchanged by this review): `plan_accepted: false`,
  `implementation_authorized: false`, `d7d_execution_authorized: false`,
  `decoder_executed: false`, `result_created: false`,
  `formal/synthetic/real_execution_authorized: false`,
  `scientific_promotion: false`, `g1_authorized: false`, `g2_authorized: false`,
  `layer_interface_implementation: DEFERRED_MANDATORY_BEFORE_CROSS_LAYER_APP`,
  `next_gate: D7_D_IMPLEMENTATION_PENDING` (the closeout value
  `D7_D_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION` is set only at closeout, per the
  execution packet; pre-closeout this is the expected value). D7-C state remains
  the accepted predecessor (`decoder_executed/result_created true`,
  `d7c_result_accepted: true`, authorizations false).
- No push: HEAD `727bca7a` is local; `origin/formal-ir-v72p1-addendum-clean`
  (`d98db0e2`) is 103 commits behind, 0 ahead.
- Unrelated dirty/CRLF/SOP/workbuddy state preserved: `docs/research-cycle-sop.md`
  and `docs/v35-algorithm-development-report.md` still modified,
  `workspace/pytest-evidence-test/output/expanded_evidence_manifest.json` still
  modified, 102 untracked `.workbuddy` entries present; no new repo-visible
  untracked artifact was created by this review. `scripts/__pycache__/` and
  `workspace/.pytest_cache` are gitignored.

## 8. Discrepancies and observations (all non-blocking)

1. **F01 certification-doc value** (already documented in the implementation
   review §11.1): the doc quotes max-abs `2.776e-17`; re-execution observes
   `2.2204e-16`, far below the `1e-10` gate. Confirmed documented and
   non-blocking; optional scoped docs refresh only.
2. **Venv-on-PATH adapter carry-forward**: the frozen command uses bare `python`,
   which is absent on the default PATH; D7-C recorded
   `VENV_PYTHON_ON_PATH_ADAPTER_REQUIRED_AT_EXECUTION_AUTHORIZATION`. The D7-D
   authorization record (future, at explicit authorization time) should restate
   this adapter requirement with the command so the launch cannot fail with exit
   127. Documentation carry-forward only; the environment itself is unchanged and
   verified.
3. **Pre-closeout `next_gate`**: `D7_D_IMPLEMENTATION_PENDING` is correct until the
   closeout sets `D7_D_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`; the execution
   packet §Boundaries says this value is set only after both reviews PASS. Not a
   defect.
4. **Out-root UUID format**: the code gate enforces direct-child + prefix
   (`d7_d_schedule_discriminator_`) only; the `<uuid>` format is an
   authorization-time operator convention (S15 pins the prefix behavior). Frozen
   behavior, not a defect.
5. **RSS over-limit timing**: `>= 2 GiB` is a T4 run terminal after the first
   call, not a T1 pre-call block; prereg §10/protern T4 semantics distinguish
   unavailable (pre-call block) from over-limit (run terminal). Coherent.
6. **ROW_LAYERED binding path** (implementation review §11.2): direct
   `v35.decode_row_layered_fftqspa` bind rather than
   `d5.bind_historical_decoder()`; same function object and kwargs; the manifest
   `decoder_ids` documents the direct shape. Recommended one clarifying line in
   the closeout/authorization record.

## 9. Verdict restatement

- Blocking issues: **none**.
- All packet §12 Pre-EXECUTE checks (exact 256 matrix, frozen command, Model-F
  metadata only, dual sentinel reachability, RSS, environment comparison,
  target absence, unauthorized refusal, tests, protected roots/state/no-push)
  pass on the frozen revision with independent evidence.
- Verdict: **D7_D_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION**.
  This PASS grants nothing: no UUID, no authorization flip, no execution, no
  scientific call, no commit, no push. Execution remains blocked until a future
  explicit verbatim one-shot authorization.
