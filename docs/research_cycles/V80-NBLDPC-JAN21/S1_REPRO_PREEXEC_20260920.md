# V80 S1 G-REPRO Pre-EXECUTE record (2026-09-20, EXPLORE)

- Track: **EXPLORE** (synthetic DE-ensemble diagnostics; bounded, reversible;
  no FER/SKR/qualification/promotion/publication/route-closure claim).
- Branch: `formal-ir-v72p1-addendum-clean` — do NOT switch/commit/push.
- Frozen packet: `docs/research_cycles/V80-NBLDPC-JAN21/S1_REPRO_GATE_PACKET_20260920.md`
  (acceptance ID **G-REPRO**). Implemented EXACTLY; no scope expansion.
- User pre-authorization (quoted, granted 2026-09-20):
  "all needed authorizations pre-granted; pick recommend options".
  This record + that grant authorize the single G-REPRO invocation below
  (I6). Execution needs nothing further.

## Frozen contract (packet §2 + bar)

- Cells: m₂ ∈ {46,47,48} × CONFIRM_SEEDS BOTH {2026094951,2026094952} ×
  R=5 DE restarts = **30 confirm calls**. m₂=47 is the verdict cell;
  46/48 are pre-frozen controls (no post-hoc promotion).
- Frozen DE config: PRIMARY pop10×gen14 search shape (provenance only),
  CONFIRM n_samples=16000/max_iter=100/tol=1e-4/streak=20, DV_SUPPORT,
  H anchors, gamma binding unchanged. Each cell re-evaluates the frozen
  m₂=47 slot-105 winner profile (lambda {2:1.0}) in ONE DE call (q=32,
  L2 sampler, rho via make_rho).
- Restart derivation (gate-local, OUTSIDE frozen_config):
  seed_eff = base_seed + r×7919, r=0..4 (r=0 recovers exact frozen seeds).
  `frozen_config()` untouched — hash MUST stay
  `60ab1e44dc179e6d783d1792dae59fd691c5657e386056498140d37fe04fb0da`.
- Pass per cell: `converged ∧ 1.0≤f_row≤1.15` (f<1 = SW violation, never
  pass). Bar (G-REPRO): m₂=47 per-cell passes ≥3/5 on BOTH seeds AND pooled
  converged-m₂47 f range ≤ 0.04 (±0.02 band). Miss ⇒ FAIL (blocks S2 entry
  on m₂=47; PASS clears BER-2 only — BER-1 fix + re-verify still required
  pre-S2).
- Dual reporting per row (packet §5): (a) layer-unit f_row (gate basis);
  (b) frozen whole-frame-with-tag superframe-n=1024 f =
  (4×5×(m₂+2)+64)/(1024×0.83256272) (m₂=47 ≈ 1.22). Raw numbers only.

## Q0 — branch

`git branch --show-current` → `formal-ir-v72p1-addendum-clean`. **PASS.**

## Q1 — scoped cleanliness

- This task edits ONLY (working tree, no commit):
  `comparison_bench/src/comparison_bench/formal_ir/v80_s1_mcde_runner.py`
  (untracked; +G-REPRO section, +`--repro-gate` CLI branch) and
  `comparison_bench/tests/test_v80_s1_readiness.py`
  (untracked; +`S1ReproGateTest`, 5 tests). Both read before editing.
- Forbidden paths clean (`git status --porcelain` empty for):
  `src/`, `experiments/`, `tools/`, `results/`,
  `comparison_bench/outputs_comparison/`, gamma npz files, all existing
  `workspace/` roots (read-only probe of the rerun root for the winner
  lambda only; zero writes).
- Pre-existing dirt NOT from this task (untouched): tracked-modified
  `AGENT_PROJECT_MEMORY.md`, `docs/decision-log.md`,
  `docs/research_cycles/V80-NBLDPC-JAN21/S1_HOLD_20260919.md`;
  assorted untracked `test_g6*/test_v72*`, `v72p2*` files from other
  sessions. None inside forbidden dirs, none blocking.
- **PASS** (with noted pre-existing dirt).

## Q2 — frozen contract verification

- `config_hash()` = `60ab1e44…0da` after edit (hash-neutrality test green;
  `frozen_config()` key set unchanged; no `repro/7919/superframe/restart`
  tokens inside the hashed dict). **PASS.**
- Gate semantics, budgets (`wall 3600 / per-call 300 / RSS 4 GiB / cpus 1`),
  seeds constants, terminals unchanged (additive-only diff). **PASS.**

## Q3 — authorization

Quoted above (2026-09-20 continuing autonomy). Covers this single 30-call
G-REPRO invocation under the frozen contract. **PASS.**

## Q4 — fresh root absent

New root `workspace/s1_repro_26483764`: `test -e` → absent; no existing
`workspace/s1_repro_*` at all (`ls | grep -c` → 0). Old roots
(`07723233`, `1b079a49`) present, never opened for write. **PASS.**

## Q5 — focused tests

`.venv/bin/python -m pytest comparison_bench/tests/test_v80_s1_readiness.py
-p no:cacheprovider -q` → **54 passed, 6 subtests passed in 104.09 s**
(includes 5 new `S1ReproGateTest`: enumeration 30=3×2×5 distinct,
hash-neutrality, root-absence/refusal, dual-unit reporting, bar
arithmetic). **PASS.**

## Q6 — frozen single command + budget

```sh
/usr/bin/time -v .venv/bin/python -m comparison_bench.src.comparison_bench.formal_ir.v80_s1_mcde_runner \
  --repro-gate --execute-real --execution-authorized \
  --root workspace/s1_repro_26483764
```

(Gamma/source frozen defaults in code: `gamma_f03.npz`, `2M`.)
Budget: 30 calls × observed PRIMARY-confirm mean ~18 s (≈540 s) /
max 31 s (≈930 s) + overhead ≪ single 3600 s wall window; RSS ≤ 4 GiB;
cpus=1; single-turn; NO_RETRY; checkpoint-per-eval; no `--resume-from`.
**PASS.**

## Verdict

**Pre-EXECUTE PASS (Q0–Q6). Single G-REPRO invocation authorized.**

Stop rules: wall overrun → `resource_blocked` + retain partial + report
(no auto-resume); any science-input change → STOP-BLOCKED; hash drift →
STOP before any DE call.
