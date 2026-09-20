# V80 S1 G-RERUN Pre-EXECUTE record (2026-09-19, EXPLORE_HEAVY)

- Track: **EXPLORE_HEAVY** — synthetic S1 rerun, bounded reversible, no FER/SKR/claim; costly (~600 DE calls).
- Branch: `formal-ir-v72p1-addendum-clean` — no switch/commit/push.
- Frozen contract: runner `v80_s1_mcde_runner.py` F1/F2 fixed, config-hash
  `60ab1e44dc179e6d783d1792dae59fd691c5657e386056498140d37fe04fb0da`,
  seeds `{2026094951,2026094952}`, `gamma_f03.npz` + `gamma_f03_pb.npz` sidecar,
  empirical-joint+XOR sampler, axis `[u1,u2,b]`, V26 kernel read-only.
  Grids: PRIMARY_M2 44–60 (17 pts, layer-local), SECONDARY M 24–31 (8 pts);
  bound 0.83862; gate ∃-converged 1.0≤f≤1.15; flip withhold cross-unit.
  Budgets: wall ≤3600 total (fresh window at start), per-call ≤300 s,
  RSS <4 GiB, 1 CPU, NO_RETRY, checkpoint-per-eval + `--resume-from`.
- Old root `workspace/s1_mcde_07723233-e537-4a2e-857a-954e3a94d030` RETAINED
  untouched, never overwritten, hash-foreign (resume refuses).
- Authorization (Q3, quoted): "autonomous proceed granted 2026-09-19
  (covers G-RERUN fresh execution under frozen contract)".

## Q0 — branch

`git branch --show-current` → `formal-ir-v72p1-addendum-clean`. **PASS.**

## Q1 — scoped cleanliness

- Tracked diff: only `AGENT_PROJECT_MEMORY.md` (+5 lines, pre-existing
  memory-agent records append, not this task; untouched by this task).
- Forbidden paths clean (verified `git status --porcelain` empty for):
  `src/`, `experiments/`, `tools/`, `results/`,
  `comparison_bench/outputs_comparison/`, `workspace/`,
  `gamma_f03.npz`, `gamma_f03_pb.npz`.
- Pre-existing untracked files from other sessions (not created by this task,
  none inside forbidden dirs): `v72p2d5_shift_prior.py`, `v72p2r23_scale.py`,
  `v72p2r7_rate_scan.py`, `v80_s1_mcde_runner.py` + `test_v80_s1_readiness.py`
  (the frozen F1/F2 rework under test), assorted `test_g6*/test_v72*` tests,
  V72P3*/V80 docs. No `src/experiments/tools/results/outputs` writes.
- **PASS** (with noted pre-existing dirt, none blocking).

## Q2 — frozen contract

- `RECORDED_CONFIG_HASH` (runner + test constant) =
  `60ab1e44dc179e6d783d1792dae59fd691c5657e386056498140d37fe04fb0da` ✓
  (F1 rotation old `57e5da44…684` documented in code comment + test).
- Seeds `SCREEN_SEEDS = CONFIRM_SEEDS = (2026094951, 2026094952)` ✓.
- `PRIMARY_M2_GRID = range(44,61)` (17 pts) disjoint from `M_GRID = 24–31`
  (assert in code); `L2_FEASIBILITY_BOUND` 0.83862 at grid definition ✓.
- Gate `GATE_F_ENS = 1.15`: pass iff ∃ converged confirm row
  1.0 ≤ f_row ≤ 1.15; empty ⇒ non-pass ✓. `evaluate_flip_rule` cross-unit
  guard → withheld-with-reason (fixed grids disjoint by design) ✓.
- Budgets `wall_total_s=3600 / per_call_s=300 / rss<4GiB / 1 CPU`,
  `NO_RETRY`, checkpoint-per-eval + `--resume-from` validated in tests ✓.
- Gamma + pb sidecar present; V26 kernel tracked-clean (read-only import) ✓.
- **PASS.**

## Q3 — authorization

Quoted above. **PASS.**

## Q4 — new root absent

New root `workspace/s1_mcde_1b079a49-7a2a-4e3f-8a20-00cb69f3c210`:
`ls` → `No such file or directory`. Old root present, untouched. **PASS.**

## Q5 — focused tests

`.venv/bin/python -m pytest comparison_bench/tests/test_v80_s1_readiness.py
-p no:cacheprovider -q` → **48 passed, 6 subtests passed** (105.2 s). **PASS.**

## Q6 — frozen E-argv + budget

`--profile-only` (same code path, defaults) →

```json
{"config_hash": "60ab1e44…0da",
 "totals": {"PRIMARY": 420, "SECONDARY": 180, "de": 600, "setup": 12,
            "node_updates": 108800000, "wall_s": 3280.0},
 "scientific_de_calls": 0}
```

wall 3280.0 ≤ 3600 ✓. Frozen single command:

```sh
.venv/bin/python -m comparison_bench.src.comparison_bench.formal_ir.v80_s1_mcde_runner \
  --execute-real --execution-authorized \
  --root workspace/s1_mcde_1b079a49-7a2a-4e3f-8a20-00cb69f3c210
```

(Defaults frozen in code: `--gamma docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz`,
`--source 2M`.) **PASS.**

## Verdict

**Pre-EXECUTE PASS (Q0–Q6). Execution authorized under quoted grant.**
Stop rules: wall>3600 → checkpoint + `--resume-from` (fresh wall window,
ledger continues, never double-charge); invalid partial → refuse rc2;
science-input change → STOP-BLOCKED.
