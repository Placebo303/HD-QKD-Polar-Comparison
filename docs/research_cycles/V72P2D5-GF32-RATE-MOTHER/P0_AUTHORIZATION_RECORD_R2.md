# P0 execution authorization record R2 — 2026-09-07

Authority: user, explicit, in the executing session (second authorization; see
R1-consumed note below).
Verbatim authorization: "我现在明确授权执行 P0（第二次授权，与 2026-09-07 那次已消耗的授权无关）： 授权对冻结的 p0-cost 命令进行且仅进行一次调用，授权由"尝试"消耗而非由"成功" 消耗；不许重试、不许重跑、不许改任何参数，不许碰 G1 和 G2。"

Scope: exactly ONE invocation of the frozen P0 command. Consumed by the
attempt, not by success. No retry, no rerun, no parameter change, no G1, no G2.

Frozen command:
`python scripts/v72p2d5_gf32_rate_mother.py --phase p0-cost`

Operator watchdog (OQ-P0-2), applied to that command:
`"C:\Program Files\Git\usr\bin\timeout.exe" -k 30 1500 python scripts/v72p2d5_gf32_rate_mother.py --phase p0-cost`
(GNU timeout from Git for Windows; bare `timeout` on this host resolves to
Windows timeout.exe, which does not implement `-k`/124 semantics — verified at
rehearsal: bare `timeout -k 30 3 ...` errored with exit=1.)
Rehearsal on this machine, this session:
`& "C:\Program Files\Git\usr\bin\timeout.exe" -k 30 3 python -c "import time; time.sleep(10)"` ->
```
exit=124 (124 expected)
```

Governing decisions from `P0_PRE_EXECUTE_REVIEW_R1.md` (five OQs, DECIDED):
- OQ-P0-1: decode-attributed total cap 1440 s (= 12 calls x 120 s single-call
  budget) on `sum(records[].wall_s)`; process `total_wall` recorded without a
  cap. Breach is a recorded `RESOURCE_OVERRUN`, not an in-run abort; any single
  record `> 120 s` must be named in Pre-RESULT review.
- OQ-P0-2: outer wall guard REQUIRED: single frozen invocation under an outer
  1500 s guard (1440 s decode cap + 60 s harness allowance) terminating the whole
  process tree on expiry; the authorizing operator session owns the guard and
  the stop action.
- OQ-P0-3: P0 PASS is independent of `projection_blocked` (code returns
  `passed=True` unconditionally; P0 measures cost). `projection_blocked=True`
  records `RESOURCE_PROJECTION_BLOCKED`, which CLOSES the G2 gate and does NOT
  close G1; G1 is judged from `projected_g1_s <= 900 s` at Pre-RESULT review.
- OQ-P0-4: pre-flip isolation evidence reproduced fresh in this session
  (E1–E6' below; STEP 2' reachability replaces the R2 STEP 2 probe per R3).
- OQ-P0-5: crash/hang/non-finite -> partial root RETAINED undisturbed in place,
  marked VOID, never reused; authorization consumed by the attempt; non-finite
  numeric payload is a P0 FAIL in the `IMPLEMENTATION_OR_NUMERICAL_BLOCKED`
  family.

Fresh pre-flip evidence (this session, branch `formal-ir-v72p1-addendum-clean`,
HEAD `299416ae`):

E1 — roots stat (P0 absent, G2 absent, G1 4 files, Model-F 2 files 208467/752):
```
P0_ABSENT
G2_ABSENT
Name                   Length LastWriteTime
----                   ------ -------------
execution_summary.json    267 2026/9/7 2:35:32
report.md                 146 2026/9/7 2:35:32
results.json             2593 2026/9/7 2:35:32
table.csv                 126 2026/9/7 2:35:32
Name                       Length LastWriteTime
----                       ------ -------------
model_f_input_summary.json    752 2026/9/7 2:07:07
model_f_input.npz          208467 2026/9/7 2:07:07
```

E2 — nine authorizations false, promotion false, gate intact:
```
structure_execution_authorized: false
g0_execution_authorized: false
g0_recovery_execution_authorized: false
p0_cost_execution_authorized: false
g1_execution_authorized: false
g2_execution_authorized: false
synthetic_execution_authorized: false
real_execution_authorized: false
formal_execution_authorized: false
scientific_promotion: false
next_gate: P0_PACKET_REVIEW
```

E3 — CLI refuses while unauthorized (exit 3); re-stat P0 absent:
```
phase 'p0-cost' is not authorized; refusing before any work
exit=3
P0_ABSENT_CONFIRMED
```

E4 — three focused files, fresh `--basetemp=workspace/v72p2d5_p0_preexec_r2_9f3c1a`
(`-p no:cacheprovider`):
`comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py`
`comparison_bench/tests/test_v72p2d5_model_f_input.py`
`comparison_bench/tests/test_v72p2d4_cal_gf32_model_rate_audit.py`
```
collected 200 items
1 failed, 199 passed, 1 warning in 24.02s
FAILED comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py::test_T1_22_openspec_history_zero_mod
```
Sole failure is the known-benign `test_T1_22_openspec_history_zero_mod`: it
asserts zero `git status` entries under `src`/`experiments`/`tools`/`results`
plus plan-history docs, and the worktree carries ~1887 line-ending-only
cosmetic modifications (see E6'); non-blocking per packet. No other failure.
Re-stat after: `P0_ABSENT_CONFIRMED`, `G2_ABSENT_CONFIRMED`.

E5 — compile clean (exit 0) on all four:
core `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`,
core `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_model_f_input.py`,
`scripts/v72p2d5_gf32_rate_mother.py`,
`scripts/v72p2d5_prepare_model_f_input.py`:
```
COMPILE_EXIT=0
```

E6' — content-change gate (R3 A.3; `awk` absent on this host, PowerShell
equivalent used — counting `git diff --numstat` rows with added != 0 or
deleted != 0; noted, semantics identical):
```
files_with_content_change: 0
```
Informational raw modified count (record only, no action taken; forbidden to
reduce via checkout/add --renormalize/clean/reset):
```
raw_modified_count: 1887
```

STEP 2' — reachability under the real launch condition (R3 A.2; probe file
`C:/Users/admin/AppData/Local/Temp/opencode/reach_probe.py`, OUTSIDE the repo;
run with repo as cwd; no `sys.path` insertion; no `python -c`). Literal output:
```
sys.path[0]= 'C:\\Users\\admin\\AppData\\Local\\Temp\\opencode'
cwd= D:\Code\HD-QKD_Polar_Comparison
repo_root_on_sys_path= False
package_import_available= False ModuleNotFoundError
REACH_OK REACHED_FIRST_DECODER_CALL probe_calls 1
tmp_contents []
p0_root False g2_root False
```
All five required conditions hold. Authorization spend precondition satisfied.

R3 A.4 extras:
- E6' content-change count: `files_with_content_change: 0`; informational raw
  modified count: `1887` (line-ending representation only under
  `core.autocrlf=true` with no `.gitattributes`; commit `299416ae` carries none
  of it).
- `LOADER_FIX_REVIEW_R1` returned `LOADER_FIX_REVIEW_PASS` on `299416ae`, but
  its own probe ran with the repository root on `sys.path` and was therefore
  not conclusive about script launch; STEP 2' above supersedes it for the
  launch-condition question.

R1 note: the R1 authorization was consumed on 2026-09-07 with NO run — the
phase refused in 0.376 s with a false
`MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS` because the consumer reached
the Model-F artifact through a package import that fails under script launch.
This R2 authorization is new and separate; the R1 authorization is not reused.

Post-run obligation: `p0_cost_execution_authorized` returns to `false`
immediately after the single attempt, whatever the outcome, before any analysis
or writing. `next_gate` and `scientific_promotion` untouched.
