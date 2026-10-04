# M3C-R2 Pre-EXECUTE — 2026-09-27

**Decision: PASS for the single frozen R2 arm.** The 2026-09-26 bounded user grant and `PREREG_AND_AUTH.md` remain in force. This check does not accept R1 as a scientific result; it only adjudicates the R1 machine gate required to start R2. No rerun, retuning or graph construction is allowed.

## R1 machine gate

- Original R1 process exited 0. `execution.jsonl` ends with `M3C-R1` `TERMINAL`, `COMPLETE`, `processed_n=383`, `decoder_calls=422`, no stop reason. `rows.json` has 383 ordered frame rows numbered 0..382 and a `COMPLETE` summary.
- Main-thread recomputation from actual rows: 39 Stage-1 non-exact frames; exactly those same 39 indices have Stage-2 attempts; 28 rescued; 372 final u2 successes and 11 final failures; no unknown final outcomes. No per-call over-cap row. Stage-1 and Stage-2 undetected counts are both zero. These are machine-gate checks, not final accepted FER/claim evidence.
- R1 summary wall 4813.20 s < internal 5280 s and external 5400 s; peak RSS 0.7281 GiB <4 GiB. `/usr/bin/time -v` measured 1:20:16 wall, 763452 KiB maximum RSS, exit 0. Thread variables were all `1`. The batch has ample room under the frozen sequential 10800 s cap for the separately capped R2 arm.

## Fresh R2 and scoped state

- Repository branch remains `formal-ir-v72p1-addendum-clean`, HEAD `ce85d61f`. No tracked or untracked changes under `src/`, `experiments/`, `tools/`, `results/`, or `comparison_bench/outputs_comparison/`. The R2 root `workspace/m3c_real_u2_20260926/R2_4e8bc319` is absent; the existing family root and append-only `execution.jsonl` must be retained for R2. The general packet phrase about a fresh family root applies to R1; R2 explicitly appends to the completed R1 family log.
- The exact six pinned input files still exist and their byte sizes and UTC mtimes match `PRE_EXECUTE.md`: raw member 21264 B / 2026-01-21 10:36:57; R1 dataset JSON 4849 B / 2026-09-21 12:51:13; split JSON 1108 B / 12:50:13; TRAIN prior NPZ 8660484 B / 13:55:08; M3-a arm1 64621 B / 2026-09-25 17:44:07; arm2 64657 B / 17:45:15. This check read file metadata only. R2's own loader/graph pins refuse any runtime identity drift.
- Code, fake-only tests, and independent implementation review are unchanged from the R1 gate: WSL `py_compile` PASS, 13 focused tests PASS, reviewer PASS after timeout/log repair. No further code/test/parameter change occurred before R2.

## Exact single launch

In the WSL repository root, with one CPU, 300 s per-call limit, 5280 s internal stop, 5400 s external watchdog and RSS <4 GiB:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 timeout -k 10 5400 /usr/bin/time -v .venv/bin/python -m comparison_bench.src.comparison_bench.cli.m3c_real_u2 --arm M3C-R2 --root workspace/m3c_real_u2_20260926/R2_4e8bc319 --execute-real --execution-authorized
```

Retain stdout, resource output, per-frame artifacts and append-only family log. If R2 is incomplete or fails, stop without rerun. Only after both arms are terminal does a separate `luna_worker` perform independent Pre-RESULT recomputation before a result summary or claim is solidified.
