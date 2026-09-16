# AMENDMENT A1 to TASK PACKET D5-DISPO-R1 — G05 correction + resume at STEP 6

Issued: 2026-09-07, by the packet author, after reviewing the executor's STOP report.
Applies to: `.workbuddy/tasks/D5_DISPO_R1_TASK_PACKET.md`.
Everything in the original packet stays in force EXCEPT what this file
explicitly supersedes.

---

## A1.0 Ruling on the STOP

The executor's STOP at STEP 5 / G05 was **correct execution of a defective
gate**. The defect is in the packet, not in the executor's work.

G05 was written as "the whole repository has exactly these 6 dirty `.py`
entries". That expectation was derived from a truncated `git status` listing
and is wrong: this worktree carries 12 additional untracked `.py` files that
predate the task.

Verified by the packet author (read-only `stat`):

| mtime | file |
| --- | --- |
| 2026-09-03T21:59:37 | `comparison_bench/outputs_comparison/transfer_evaluation/20260812_v1_v5c2_evaluation_only/build_pie_skr_comparison.py` |
| 2026-09-03T21:59:37 | `comparison_bench/src/comparison_bench/analysis/cascade_beta_pareto.py` |
| 2026-09-03T21:59:37 | `comparison_bench/src/comparison_bench/cli/run_cascade_beta_sweep.py` |
| 2026-09-03T21:59:37 | `comparison_bench/src/comparison_bench/cli/run_cascade_longframe.py` |
| 2026-09-05T13:49:28 | `comparison_bench/src/comparison_bench/formal_ir/v72p2d4_cal_gf32_model_rate_audit.py` |
| 2026-09-03T21:59:38 | `comparison_bench/src/comparison_bench/methods/cascade/__init__.py` |
| 2026-09-03T21:59:38 | `comparison_bench/src/comparison_bench/methods/cascade/cascade_common.py` |
| 2026-09-03T21:59:38 | `comparison_bench/src/comparison_bench/methods/cascade/config.py` |
| 2026-09-03T21:59:38 | `comparison_bench/src/comparison_bench/methods/cascade/shims.py` |
| 2026-09-03T21:59:38 | `comparison_bench/src/comparison_bench/methods/cascade/single_kernel.py` |
| 2026-09-03T21:59:38 | `comparison_bench/src/comparison_bench/methods/cascade/tuning.py` |
| 2026-09-03T21:59:38 | `comparison_bench/src/comparison_bench/methods/cascade_single_kernel.py` |
| 2026-09-05T13:51:20 | `comparison_bench/tests/test_v72p2d4_cal_gf32_model_rate_audit.py` |
| 2026-09-03T21:59:38 | `scripts/analyze_v64_stage_ablation.py` |
| 2026-09-05T13:49:41 | `scripts/v72p2d4_cal_gf32_model_rate_audit.py` |

All predate this task by 2–4 days. None was created by the executor. They are
unrelated pre-existing worktree dirt (cascade workflow, V72P2D4 audit,
transfer evaluation, V64 ablation) and are **out of scope**: do not stage them,
do not commit them, do not delete them, do not move them, do not mention them
in any record file.

The packet author also verified, read-only, that the three executor deltas are
exactly the ones the packet allows, and that the pre-existing `M` on
`cycle_state.yaml` only records G0-recovery acceptance and advances `next_gate`
to `P0_PACKET_REVIEW` — all nine `*_execution_authorized` remain `false`, so
committing it under commit 3 is correct and safe.

**Verdict: proceed. Resume at STEP 6.**

---

## A1.1 SUPERSEDED — original STEP 5 / G05

The original G05 is void. Do not re-run it. Replace it with G05' and G06 below.

## A1.2 NEW — G05' scoped scope check

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && git status --porcelain=v1 -- comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py comparison_bench/src/comparison_bench/formal_ir/v72p2d5_model_f_input.py comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py comparison_bench/tests/test_v72p2d5_model_f_input.py scripts/v72p2d5_gf32_rate_mother.py scripts/v72p2d5_prepare_model_f_input.py
```

Expected — exactly these 6 lines, in any order, and nothing else:

```
 M comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py
 M comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py
 M scripts/v72p2d5_gf32_rate_mother.py
?? comparison_bench/src/comparison_bench/formal_ir/v72p2d5_model_f_input.py
?? comparison_bench/tests/test_v72p2d5_model_f_input.py
?? scripts/v72p2d5_prepare_model_f_input.py
```

Any deviation → STOP.

## A1.3 NEW — G06 executor created no `.py`

Proves the executor authored no code, without depending on unrelated dirt.

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && python -c "
import subprocess, pathlib, datetime
CUTOFF = datetime.datetime(2026, 9, 7, 3, 0, 0).timestamp()
out = subprocess.run(['git','status','--porcelain=v1','--','*.py'], capture_output=True, text=True, cwd='.').stdout
bad = []
for line in out.splitlines():
    f = line[3:].strip().strip('\"')
    p = pathlib.Path(f)
    if p.exists() and p.stat().st_mtime > CUTOFF:
        bad.append((f, datetime.datetime.fromtimestamp(p.stat().st_mtime).isoformat()))
print('DIRTY_PY_TOTAL', len(out.splitlines()))
print('MODIFIED_SINCE_CUTOFF', bad)
print('G06_OK' if not bad else 'G06_FAIL')
"
```

Expected: `MODIFIED_SINCE_CUTOFF []` and `G06_OK`.
If any file appears, STOP and report it — that would mean a `.py` was touched
during the task, which the packet forbids.

## A1.4 NEW — G07 staged-content guard (run inside STEP 6, after each `git add`)

After every `git add` in STEP 6 and **before** the matching `git commit`, run:

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && git diff --cached --name-only
```

Read the list. If it contains any path that is not in that commit's `git add`
whitelist — in particular any of the 15 unrelated `.py` files listed in A1.0 —
STOP immediately, do not commit, and report. Do not attempt to unstage or fix
it yourself.

---

## A1.5 Resume instructions

1. Do NOT redo STEP 1–4. They are complete and verified; the three deltas stay
   exactly as they are. Do not re-edit, re-append, or reformat them.
2. Run G01 and G02 once more (compile + `165 passed`) as a pre-commit
   regression guard, then G03, G04, G05', G06.
3. If all pass, execute STEP 6 exactly as written in the original packet — the
   three `git add` whitelists and three commit messages are unchanged — with
   G07 inserted before each commit.
4. Then STEP 7 report, unchanged, plus one added line: state that G05 was
   superseded by amendment A1 and that G05'/G06/G07 passed.

Every prohibition in packet §0 remains in force. Still no push. Still no
decoder, no CAL/VAL read, no `.py` edit, no authorization change, no scientific
conclusion.
