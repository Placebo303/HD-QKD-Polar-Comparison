# AMENDMENT A2 to TASK PACKET D5-DISPO-R1 — G06 cutoff correction + G03 ruling

Issued: 2026-09-07, by the packet author, after reviewing the executor's second
STOP report.
Applies to: `.workbuddy/tasks/D5_DISPO_R1_TASK_PACKET.md` as amended by
`.workbuddy/tasks/D5_DISPO_R1_AMENDMENT_A1.md`.
Everything in the packet and in A1 stays in force EXCEPT what this file
explicitly supersedes.

---

## A2.0 Ruling on the second STOP

The executor's STOP at G06 was **again correct execution of a defective gate**.
The defect is again in the gate, not in the executor's work. The executor is
performing exactly as intended; two consecutive STOPs are the containment
working, not a problem with the session.

G06 used a hardcoded cutoff of `2026-09-07 03:00`. That timestamp is wrong: it
precedes the creation of the task packet itself.

Verified by the packet author (read-only `stat`):

- Task packet mtime: `2026-09-07T04:04:24`.
- `comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py` mtime:
  `2026-09-07T03:48:38` — **16 minutes BEFORE the packet existed**.
- That edit belongs to the preceding test-isolation repair, recorded in
  `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/TEST_ISOLATION_REWORK_EVIDENCE_R1.md`.
- Independent corroboration: the `git status` snapshot taken at `03:58`, before
  the packet was written, already lists that file as `M`.
- Re-run with the corrected anchor: `DIRTY_PY_TOTAL 21`,
  `NEWER_THAN_PACKET []`, `OK`. No `.py` in the worktree is newer than the
  packet.

The executor authored no `.py`. **Verdict: proceed.**

## A2.1 Ruling on G03

The executor could not compare mtimes because it did not hold the STEP 1
literals. The packet author has done that comparison instead, against the
values in the executor's own STEP 1 report:

| file | size | mtime_ns | STEP1 == G03 |
| --- | --- | --- | --- |
| `g1/20260906_r1/execution_summary.json` | 267 | 1788719732911457700 | yes |
| `g1/20260906_r1/report.md` | 146 | 1788719732911457700 | yes |
| `g1/20260906_r1/results.json` | 2593 | 1788719732909954400 | yes |
| `g1/20260906_r1/table.csv` | 126 | 1788719732909954400 | yes |
| `model_f_input/20260907_r1/model_f_input.npz` | 208467 | 1788718027043698800 | yes |
| `model_f_input/20260907_r1/model_f_input_summary.json` | 752 | 1788718027043698800 | yes |
| `g0/20260905_r2` 4 files | 385/712/2512/306 | — | match |
| `g0_recovery/20260906_r1` 4 files | 404/722/2531/306 | — | match |

`p0_cost` and `g2` absent. **G03: PASS.** Do not re-run it and do not seek the
STEP 1 literals.

---

## A2.2 SUPERSEDED — A1.3 / G06

The hardcoded-cutoff G06 is void. Do not re-run it. Replace with G06' below.

## A2.3 NEW — G06' self-anchored "executor created no `.py`"

Anchors on the task packet's own mtime, so no hand-picked timestamp can be
wrong again.

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && python -c "
import subprocess, pathlib, datetime
pkt = pathlib.Path('.workbuddy/tasks/D5_DISPO_R1_TASK_PACKET.md')
cut = pkt.stat().st_mtime
print('PACKET_MTIME', datetime.datetime.fromtimestamp(cut).isoformat())
out = subprocess.run(['git','status','--porcelain=v1','--','*.py'],capture_output=True,text=True).stdout
newer=[]
for line in out.splitlines():
    f=line[3:].strip().strip('\"'); p=pathlib.Path(f)
    if p.exists() and p.stat().st_mtime > cut:
        newer.append((f, datetime.datetime.fromtimestamp(p.stat().st_mtime).isoformat()))
print('DIRTY_PY_TOTAL', len(out.splitlines()))
print('NEWER_THAN_PACKET', newer)
print('G06_OK' if not newer else 'G06_FAIL')
"
```

Expected: `NEWER_THAN_PACKET []` and `G06_OK`. Author-measured reference values
at issue time: `PACKET_MTIME 2026-09-07T04:04:24.272358`, `DIRTY_PY_TOTAL 21`.

If a `.py` does appear newer than the packet, STOP and report it — that would
mean code was touched during the task, which the packet forbids.

If the shell mangles the multi-line `python -c`, a semantically identical
single-line form is acceptable, as the executor already did once; say so in the
report.

---

## A2.4 Resume instructions

1. Do NOT redo STEP 1–4. Do NOT redo G01, G02, G04, G05'. They passed and are
   accepted: `COMPILE_OK`, `165 passed`, all nine authorizations `false` with
   `next_gate: P0_PACKET_REVIEW`, exactly the 6 whitelisted D5 paths dirty.
2. G03 is ruled PASS by A2.1. Do not re-run.
3. Run G06' once. On `G06_OK`, proceed directly to STEP 6.
4. STEP 6 unchanged: the three `git add` whitelists and the three commit
   messages are exactly as in the original packet, with A1's G07
   (`git diff --cached --name-only`, inspect, STOP on any non-whitelisted path,
   never self-unstage) inserted after each `git add` and before each
   `git commit`.
5. Then the STEP 7 report, plus: G05 superseded by A1, G06 superseded by A2,
   and G03 ruled PASS by the packet author.

Every prohibition in packet §0 remains in force. Still no push. Still no
decoder, no CAL/VAL read, no `.py` edit, no authorization change, no scientific
conclusion.
