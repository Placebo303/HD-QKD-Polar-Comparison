# M3D Pre-EXECUTE — 2026-09-27

**Status: PENDING EXPLICIT M3D BATCH GRANT; NO SCIENTIFIC ARM EXECUTED.** Track `EXPLORE`. This checklist is an implementation and input-readiness record, not an execution authorization. M3B/M3C grants were consumed.

## Scope and frozen inputs

- Branch: `formal-ir-v72p1-addendum-clean`. Scoped new code/tests are `comparison_bench/src/comparison_bench/cli/m3d_iter250_synth.py`, `comparison_bench/src/comparison_bench/formal_ir/v80_b2f_campaign.py`, `comparison_bench/tests/test_m3d_iter250_synth_fake.py`, and `comparison_bench/tests/test_v80_b2f_iter_override.py`. OpenSpec and this cycle's packet/prompt are present. Other dirty worktree content is preserved and is outside M3D. Protected `src/`, `experiments/`, `tools/`, `results/`, and `comparison_bench/outputs_comparison/` show no scoped Git changes.
- Saved M3A `arm1.json`/`arm2.json`, M3B `rows.json` R1/R2 (240 Stage-1 rows each), and `docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz` / `gamma_f03_pb.npz` exist and remain read-only. Independent Luna packet review verified selected indices/seeds, 8 exact+8 nonexact per arm, graph n=1024 and base/full ranks 200/208, baseline wall sums, and 90% thresholds. The packet pins all paths and semantics.
- `workspace/m3d_iter250_synth_20260927/`, its R1 root and its R2 root were absent at this check. Recheck immediately before each arm. The family `EXPLORATION_LOG.md` must be created once and appended by main orchestration for attempts, gates, retained failures and batch-end review.

## Code and test gate

- Implementation retains default `max_iter=300` and makes only the M3D caller pass 250. The M3D CLI is Stage-1 m200 only; 16 frozen calls per graph; R2 requires R1 `COMPLETE` and arm PASS. It requires both execution flags, a frozen fresh root and POSIX hard-timeout support before input reads. Each decoder call has a 90 s `SIGALRM` deadline; timeout is retained as unknown and `INCOMPLETE-decode-cap`. An external arm timeout remains required.
- Implementation worker reported **29 focused fake tests passed**, `py_compile` PASS and dry zero-read/zero-decoder PASS; the final support-check ordering correction then passed **14 M3D fake tests** and `py_compile`. The only pytest warning was the existing `pytest.ini` unknown `cache_dir` option. No production decoder or scientific arm ran in these checks.
- Independent Luna code review initially blocked the missing in-call deadline. It then verified the deadline, timeout retention, handler/timer cleanup, and finally **PASS** on the moved pre-input support gate and fake zero-read test. No unresolved review defect was reported. The reviewer could not invoke the WSL repo venv from its Windows shell, so the test-run evidence is the implementation worker's reported WSL run, not an independent rerun.

## Exact commands and budget, NOT YET AUTHORIZED

Execute from `/mnt/d/Code/HD-QKD_Polar_Comparison` with the repo `.venv/bin/python`, one CPU thread for each named math runtime. First R1:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 timeout -k 5 1200 .venv/bin/python -m comparison_bench.src.comparison_bench.cli.m3d_iter250_synth --arm M3D-R1 --root workspace/m3d_iter250_synth_20260927/R1_17b6c2e9 --execute-synthetic --execution-authorized
```

Only if R1 is complete and individually passes every packet gate, freshly recheck R2 root absence and run:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 timeout -k 5 1200 .venv/bin/python -m comparison_bench.src.comparison_bench.cli.m3d_iter250_synth --arm M3D-R2 --root workspace/m3d_iter250_synth_20260927/R2_45ad8f31 --execute-synthetic --execution-authorized
```

Frozen cost ceilings: 90 s per call, 1200 s per arm, 2400 s sequential batch, peak RSS <2 GiB. Failure or missing R1 signal stops before R2. No rerun, resume, graph change, retuning, real-data read, Stage 2, FER/throughput extrapolation or leakage/f/SKR claim. At most one packet-defined engineering repair may be considered with failed attempt retained and unchanged scientific inputs.

## Pending authorization

The remaining gate is an explicit user grant for **G-M3D-ITER250-SYNTH**, covering the frozen conditional R1→R2 synthetic EXPLORE batch at the commands and budget above. No prior blanket grant is being reused. Once granted, main must recheck branch, scoped files/tests, fresh roots and cost immediately before execution, keep one append-only exploration log, and obtain an independent batch-end review before any scientific acceptance.

## Grant recorded and Pre-EXECUTE recheck — 2026-09-27

Grant (verbatim, 2026-09-27, relayed by main thread): 「授权 G-M3D-ITER250-SYNTH 按 PRE_EXECUTE 执行」

Recheck executed by implementation operator, 2026-09-27 (~03:25 UTC), before any M3D scientific execution:

- A1 branch: `git branch --show-current` = `formal-ir-v72p1-addendum-clean` (matches frozen branch; no switch performed). `git rev-parse HEAD` = `ce85d61f5f625a323765481cb726f77e0380b86a`.
- A2 scoped cleanliness (`git status --porcelain` on the six authorized scope paths): ` M comparison_bench/src/comparison_bench/formal_ir/v80_b2f_campaign.py`, `?? comparison_bench/src/comparison_bench/cli/m3d_iter250_synth.py`, `?? comparison_bench/tests/test_m3d_iter250_synth_fake.py`, `?? comparison_bench/tests/test_v80_b2f_iter_override.py`, `?? docs/research_cycles/M3D-ITER250-SYNTH/`, `?? openspec/changes/m3d-iter250-synth/`. All within the authorized M3D scope; the untracked cycle/OpenSpec/test/CLI files are the expected frozen implementation state, not a defect.
- A3 protected roots (`git diff --stat -- src/ experiments/ tools/ results/ comparison_bench/outputs_comparison/`): empty diff (no content changes; only benign CRLF advisory warnings). PASS — protected roots unchanged.
- A4 focused fake tests (repo venv, one thread, `--basetemp=/tmp/pytest-m3d-op-20260927`): `20 passed, 1 warning in 8.08s`, exit 0. Sole warning = `PytestConfigWarning: Unknown config option: cache_dir` (known benign `pytest.ini` warning); no other warning text. PASS.
- A5 frozen inputs present, read-only (byte size + UTC mtime, `TZ=UTC stat`): `workspace/m3a_nested_200p8_20260926/arm1.json` 64621 bytes 2026-09-25 17:44:07 UTC; `arm2.json` 64657 bytes 2026-09-25 17:45:15 UTC; `workspace/m3b_nested_paired_20260926/P1S1-R1_73d2f40a/rows.json` 97545 bytes 2026-09-26 07:12:05 UTC; `workspace/m3b_nested_paired_20260926/P1S1-R2_89ae671c/rows.json` 99478 bytes 2026-09-26 07:46:14 UTC; `docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz` 100106 bytes 2026-09-19 04:26:03 UTC; `gamma_f03_pb.npz` 9011 bytes 2026-09-19 05:41:30 UTC. All present. No reads beyond existence/stat. PASS.
- A6 output absence: `workspace/m3d_iter250_synth_20260927/` ABSENT (`ls: cannot access ... No such file or directory`). PASS — no collision; family root to be created fresh next.
- A7 No production decoder has run under M3D. The A4 fake suite uses fake runners only; this batch is the first decoder execution. Confirmed.

Overall: Pre-EXECUTE recheck PASS on A1–A7. Proceeding to family-root creation and conditional R1→R2 execution per PACKET.
