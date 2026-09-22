# D7-B renewed Pre-EXECUTE review WSL R2 (separate reviewer context)

Review mode: separate pass on actual WSL against the reviewed implementation
commit `04b7a8e` (T3 verdict `D7_B_WSL_LAUNCH_REWORK_REVIEW_PASS`). Nothing
was edited; only this file is created. Probes ran as separate commands, never
chained. Zero decoder invocations; no root created. This review authorizes
NOTHING and generates NO UUID.

## Environment identity (recorded facts, not science parameters)

- Interpreter: `/home/karel_303/.venvs/hd-qkd-polar-comparison/bin/python`,
  Python 3.12.3, NumPy 2.4.4.
- WSL: `Linux 6.18.33.2-microsoft-standard-WSL2` (gcc 13.2.0).
- Repo: `/mnt/d/Code/HD-QKD_Polar_Comparison`
  (branch `formal-ir-v72p1-addendum-clean`, HEAD `04b7a8e`).
- Watchdog: `/usr/bin/timeout`, GNU coreutils 9.4.

## Probes (literal outcomes)

1. Identity: as above.
2. Live RSS: `9416704` (positive integer).
3. `timeout` exists; version 9.4.
4. `timeout -k 30 3 <venv-python> -c 'import time; time.sleep(30)'` → exit
   `124` (watchdog rehearsal PASS).
5. Real runner `--help` from repo root AND from external cwd (`/tmp`),
   no PYTHONPATH: exit 0, `D7-B easy-regime (authorization-gated).`
6. Real runner `--dry-run` from external cwd, no PYTHONPATH: exit 0,
   `cells=64 caps=[1, 2, 4, 8, 16, 32, 90] budget=420` + 64 cell lines.
7. External-cwd, no-PYTHONPATH binding probe: `bind_historical_decoder()`
   returns exactly `comparison_bench.formal_ir.v35_algorithm_development.
   decode_row_layered_fftqspa` (`fn is v35.decode_row_layered_fftqspa`);
   `v35.__package__ == 'comparison_bench.formal_ir'`;
   `nonbinary_field` resolves under the same local `comparison_bench/src`;
   callable NEVER invoked; no `workspace/d7_b_easy_regime_*` created.
   (`BIND_EXACT_V35_ZERO_CALL_ZERO_ROOT`, exit 0.)
8. Unauthorized exact-shape probe
   (`timeout -k 30 1800 <venv-python> scripts/... --out-root <fresh target>`):
   `D7-B execution is not authorized; refusing before any work`, exit 3,
   target absent (refusal precedes bind, root creation, and decoder).
9. `workspace/d7_b_easy_regime_*` absent; `workspace/*v72p2d7*` absent
   (D7-B/R1d/G2 roots all absent); protected
   `workspace/v72p2d5_g0/20260905_r2`, `workspace/v72p2d5_g1/20260907_r2`,
   `comparison_bench/outputs_comparison`, `results` present;
   `cycle_state.yaml`: `d7b_execution_authorized: false`, attempts/completed
   0/0, `decoder_executed: false`, `result_created: false`,
   `g1_authorized/g2_authorized: false`.
10. Scoped code equals reviewed implementation: HEAD `04b7a8e`; `git diff`
    over `scripts/`, `comparison_bench/src/`, the D7-B test file, and the
    OpenSpec change is empty (only untracked review docs differ).

## Command shape (frozen per WSL-A1 addendum; NOT run here)

```bash
timeout -k 30 1800 python scripts/v72p2d7_gf32_easy_regime.py --out-root workspace/d7_b_easy_regime_<uuid>
```

Shell-spelling-only change from R1; science, budgets, one-attempt semantics,
and prohibitions unchanged. No UUID exists for any future run.

## Verdict

`D7_B_PRE_EXECUTE_REVIEW_PASS_WSL_R2_AWAITING_FRESH_AUTHORIZATION`

Launch binding is package-correct on WSL; all gates hold. Execution still
requires a fresh explicit user authorization naming one new UUID. R1d, G1,
G2 remain unauthorized.

(End of file — uncommitted; committed at T5 closeout.)
