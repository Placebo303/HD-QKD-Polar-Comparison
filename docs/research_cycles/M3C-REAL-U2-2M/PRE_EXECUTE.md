# M3C Pre-EXECUTE — 2026-09-27

**Decision: PASS for M3C-R1 only.** Track `DECIDE`. The user granted this bounded continuation on 2026-09-26. R2 remains conditional on R1 `COMPLETE` and its machine gates. This is a real 2M u2 diagnostic with an offline oracle rescue trigger; it does not authorize a deployable protocol, leakage/SKR claim, P3/G0B decision, retuning or rerun.

## Scope and implementation

- Repository `D:\Code\HD-QKD_Polar_Comparison`; branch `formal-ir-v72p1-addendum-clean`; HEAD `ce85d61f`. Scoped new files: `comparison_bench/src/comparison_bench/cli/m3c_real_u2.py`, `comparison_bench/tests/test_m3c_real_u2_fake.py`, this cycle's packet/prompt and `openspec/changes/m3c-real-u2-2m/`. The checkout contains unrelated pre-existing changes; no clean-worktree or remote-SHA equality is asserted. `git status --short -- src experiments tools results comparison_bench/outputs_comparison` is empty.
- Frozen input contract and STOP rules: `PREREG_AND_AUTH.md`. The runner pins the M0 2M VAL+HOLD order and 383 complete 1024-symbol frames plus 529 dropped symbols, same-source R1-TRAIN prior, accepted M3-a arm1/arm2 graphs, Stage-1 200 rows and oracle-triggered cold Stage-2 208 rows. R1 then R2, no retry/resume. No L1 security or actual leakage result.
- Implementation operator reported WSL `py_compile` PASS and fake-only focused pytest **13 passed**; only an existing unknown `cache_dir` pytest warning. Tests use injected readers/decoder and did not call the production reader, decoder or PEG. Independent Luna implementation review initially FAILed on missing interruption/log evidence; after repair and a 5280 s internal deadline, final read-only re-review PASS for those findings and the frozen M3C code/packet. The reviewer ran a no-flag bytecode-disabled import/refusal probe (2.95 s) and no real input read.

## Read-only input identity check

All six pinned files exist; only file metadata was read at this gate:

| input | bytes | mtime UTC |
|---|---:|---|
| `D:\Data\Raw Data\2026.1.21\Type2_2M_3s_2026-01-21_183657\Type2_2M_3s_2026-01-21_183657.ttbin` | 21264 | 2026-01-21 10:36:57 |
| `workspace/r1_histogram_5e2a91c4/T2-2M.json` | 4849 | 2026-09-21 12:51:13 |
| `workspace/r1_histogram_5e2a91c4/split_manifest.json` | 1108 | 2026-09-21 12:50:13 |
| `workspace/x1_bundles_7c1d4a2b/x1_gamma_f03r1_2M_verify.npz` | 8660484 | 2026-09-21 13:55:08 |
| `workspace/m3a_nested_200p8_20260926/arm1.json` | 64621 | 2026-09-25 17:44:07 |
| `workspace/m3a_nested_200p8_20260926/arm2.json` | 64657 | 2026-09-25 17:45:15 |

Before R1 launch, `workspace/m3c_real_u2_20260926/` and both frozen arm roots are absent. No output under protected `results/` or `comparison_bench/outputs_comparison/` is authorized. The six input paths and target-root absence are checked again immediately at launch. The runner itself refuses changed split/count/graph/prior identity before decoding.

## Budget and exact launch

One CPU; `OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=MKL_NUM_THREADS=NUMBA_NUM_THREADS=1`; one decoder call ≤300 s, internal arm stop 5280 s, external watchdog 5400 s, RSS <4 GiB. Historical M0 2M `rows.json` reports real-series read 0.731087 s; the independent no-flag import probe measured 2.95 s. The 120 s internal reserve is for process overhead and terminal evidence. The exact command from the frozen packet, run in the WSL repository root, is:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 timeout -k 10 5400 /usr/bin/time -v .venv/bin/python -m comparison_bench.src.comparison_bench.cli.m3c_real_u2 --arm M3C-R1 --root workspace/m3c_real_u2_20260926/R1_5af1c76e --execute-real --execution-authorized
```

Capture tool stdout and `/usr/bin/time -v` stderr. R2 launches only after verifying R1 `COMPLETE`, all 383 final dispositions, exact Stage-2 set, no budget failure, fresh R2 root and no protected-output writes. Independent Pre-RESULT checks actual artifacts before any result is accepted or published. An incomplete/error arm is retained and stops this packet; no repair or rerun is implied.
