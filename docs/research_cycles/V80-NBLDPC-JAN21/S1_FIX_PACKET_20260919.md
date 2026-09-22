# V80 S1 F1/F2/F3 Frozen Operator Packet (2026-09-19) — for coder-fast

- Track: **EXPLORE** (synthetic S1 DE rework; bounded, reversible; no FER/SKR/qualification/promotion/publication claim). `EXPLORE_HEAVY` cost annotation applies to the later rerun only, NOT to this planning packet or to the rework implementation.
- Branch: `formal-ir-v72p1-addendum-clean` — do NOT switch branch, do NOT commit, do NOT push. Planning + frozen rework implementation only.
- Sources (read-only, frozen): `S1_HOLD_20260919.md`, `INDEPENDENT_REVIEW_20260919.md` (§1 F1, §2 F2, §3 F3), `S1_FIX_PLAN_20260919.md` (acceptance IDs reused verbatim), `openspec/changes/v80-nbldpc-jan21/` (proposal/design/tasks), `v80_s1_mcde_runner.py` (rate grid, `evaluate_gate` ~866–876, `f_row` ~line 538, flip rule), `test_v80_s1_readiness.py` (45+6 baseline), `S1_READINESS.md` (frozen config-hash `57e5da44…684`, seeds `{2026094951,2026094952}`, budgets).
- Authority: this packet freezes allowed/forbidden files, exact F1/F2/F3 deltas, test/evidence matrix, commands, artifacts, stop rules, return conditions. Coder implements exactly what is frozen here; any ambiguity → STOP and return to planner (do not guess).
- This packet authorizes NOTHING execution-shaped: no `--execute-real`, no `--execution-authorized`, no resume, no S2/S3, no number interpretation (see §7 Forbidden).

## Goal

Fix exactly three blocking defects in the S1 runner + its test so a later independent D5-delta re-review can confirm red-green semantics and a later fresh grant can rerun: (F1) PRIMARY layer↔full-symbol rate-grid mapping, (F2) gate-vs-convergence semantics + flip-unit guard, (F3) three non-trivial fake pins. Nothing else moves.

## Non-Goals

- No execution, no rerun, no authorization grant, no Pre-EXECUTE, no gate verdict.
- No S2 (PEG / FER) or S3 (DECIDE prereg) advance.
- No S1-numbers interpretation (current-arm outputs stay uninterrupted/uninterpreted per HOLD).
- No SKR / qualification / promotion / publication claim.
- No INFORMATION-CLOSURE change; no `three-shift-cyclic` ban reopening; no S2/S3 threshold change.

## Impact Scope

- Allowed (exactly two files):
  1. `comparison_bench/src/comparison_bench/formal_ir/v80_s1_mcde_runner.py`
  2. `comparison_bench/tests/test_v80_s1_readiness.py`
- Forbidden (any touch = STOP, see §1): `src/`, `experiments/`, `tools/`, `results/`, `comparison_bench/outputs_comparison/`, `workspace/s1_mcde_07723233-*` (live/frozen old root), `docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz`, `gamma_f03_pb.npz` sibling, any other `docs/` / `openspec/` / `AGENTS.md` edits beyond the two allowed files, any workspace-root write, any new execution root.
- Config-hash / seeds rule: frozen hash `57e5da443c99f5c52615c43f2d819b22d1b40eda2f7d14ba762d2b705064a684` and frozen seeds `{2026094951, 2026094952}` stay byte-identical UNLESS the F1 new-grid derivation legitimately changes the hashed config. If the grid change alters the hash: document the old→new hash rotation explicitly in code comment + test constant + packet return (never silent); `_validate_partial` / `RECORDED_CONFIG_HASH` / `verify_manifest` consistency must be preserved or explicitly rotated together. No silent drift.

## 1. File allow/forbid list (binding)

- ALLOWED-1: `comparison_bench/src/comparison_bench/formal_ir/v80_s1_mcde_runner.py` — F1 grid + F2 gate/flip/`verify.ok` labelling only.
- ALLOWED-2: `comparison_bench/tests/test_v80_s1_readiness.py` — F3 pins + regression updates only; all fake-only, zero production `run_mcde_posterior` calls, zero disk writes (follow existing `_shim_production_raises` / `_fake_bundle` / `_make_fake_de` patterns).
- FORBIDDEN: `src/**`, `experiments/**`, `tools/**`, `results/**`, `comparison_bench/outputs_comparison/**`, `workspace/s1_mcde_07723233-e537-4a2e-857a-954e3a94d030/**` (old root retained as-is, never opened for write), `docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz`, `docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03_pb.npz`, any config-hash/seeds/budget/cap change except the explicitly-listed F1 new-grid derivation path in §2 (with explicit old→new rotation if the hash moves).
- FORBIDDEN actions: any execution (`--execute-real`, `--execution-authorized`, `execute()`, `run_execution`, resume), any workspace-root creation/write, any S1-number interpretation, any flip/S2/S3 advance, any commit/push.

## 2. F1 exact fix — PRIMARY layer-local grid [maps: F1-ACC]

- Root cause (frozen, do not re-derive): PRIMARY runs the GF(32) L2 layer (sampler `P(U2|B,U1)`, width 5) at the full-symbol budget grid m∈[24,31] → rate 0.879–0.906, all above the L2 feasibility bound. 0/420 DE convergence is theory-consistent.
- Feasibility bound (pin at the grid definition, comment + test): `1 − H_L2/5 = 1 − 0.80690067/5 = 0.83862`.
- Correct mapping (implement exactly): `m2 = ceil(f · H_L2 · n / 5) = ceil(41.31 · f)` with n=256, H_L2=0.80690067:
  - f=1.3 → m2≈54.
  - Sweep f≈1.05–1.45 → m2≈44–60.
- Delta:
  - PRIMARY arm must use its own layer-local grid (m2≈44–60 or equivalent f-parameterized grid over f≈1.05–1.45); `rate = 1 − m2/n` evaluated against the L2 width-5 budget; `f_row` for PRIMARY via `layer_efficiency(rate, h_meas, width=5)` on the new grid.
  - Full-symbol m 24–31 must NOT be reused for L2 (assert or branch separation; the old `M_GRID`-shared path for PRIMARY must be removed/replaced, not left as a fallback).
  - SECONDARY grid (width 10, direct-q1024, m 24–31) is UNCHANGED — feasible as a budget; its gate/reporting still needs the §3 F2 rework.
  - Costs: PRIMARY's consumed 420 slots are unrecoverable — rerun is new spend under a later fresh grant (not this packet); old root retained, never overwritten.
- F1-ACC (verbatim): PRIMARY grid derived layer-locally (m₂=ceil(41.31f); f=1.3→≈54; sweep ≈44–60); no full-symbol m 24–31 reuse for L2; feasibility bound 0.83862 documented at the grid definition; SECONDARY grid disposition stated.

## 3. F2 exact fix — gate semantics + flip guard [maps: F2-ACC]

- Defect (frozen): `evaluate_gate` (runner 866–876) takes `f_ens = max(f_row)` over confirm/ok rows with `f_row` present and passes iff ≤1.15; it never consults `converged`; `f_row = (1−rate)·width/h_meas` (line 538) is pure config arithmetic.
- Delta (implement exactly):
  - Gate must screen `converged`: pass iff **∃ converged row with f_row ≤ 1.15** (per arm). Empty-converged-set ⇒ explicit non-pass (`f_ens=None` or decoupled, `pass=False`, `n` counts converged rows only) — never max-of-unconverged.
  - Orientation pin: **f < 1 refuses/flags as Slepian–Wolf-bound violation** (informative failure, never a pass; must not contribute to any pass computation).
  - Concrete pass bars (document in comment + test): SECONDARY needs an **m=24 config to converge** (f_row≈1.126, the only grid point ≤1.15); PRIMARY-fixed needs **m₂ ≤ 47** (1.15·H_L2·256/5 ≈ 47.5).
  - `verify.ok` (hash + gate-recompute consistency) is NOT gate adjudication — code/report label must say so (comment + manifest/verify note or docstring; no caller may treat `verify.ok` as a pass verdict).
  - Flip cross-unit comparison FORBIDDEN: PRIMARY f (layer units) vs SECONDARY f (full-symbol units) must not be compared. `evaluate_flip_rule` computes only within a shared unit basis or returns withheld-with-reason; cross-unit call must refuse or flag (never a silent margin).
- F2-ACC (verbatim): gate requires ∃ converged row f_row≤1.15 (empty⇒non-pass); f<1 pinned as SW violation; SECONDARY pass-bar (m24 converge) and PRIMARY-fixed bar (m₂≤47) stated; flip cross-unit comparison absent/guarded; `verify.ok` labelled non-adjudicating.

## 4. F3 pins — three non-trivial fakes, each red-green [maps: F3-ACC]

- Each pin must FAIL on current (buggy) code and PASS after the fix (red-green proof, demonstrated at the later D5-delta re-review; coder must design pins so the red direction is constructible, e.g. by exercising the old logic path or a reverted helper).
- (a) Layer↔rate feasibility pin: fake with known H_L2 where the full-symbol grid sits above `1−H/width` yet the layer grid passes (and vice versa); wrong-grid binding (full-symbol m 24–31 bound to the L2 layer) must fail the pin. Must reference the 0.83862 bound.
- (b) Gate-vs-convergence pin: fake rows with attractive `f_row` (≤1.15, incl. <1 cases) but `converged=false` must NOT pass; only ∃-converged ≤1.15 passes; empty converged set ⇒ non-pass. Must cover both arms' widths.
- (c) f≥1 orientation pin: fake row with f<1 must trip the SW-bound pin (fail/flag), never contribute to a pass — including a case where the max-of-unconverged value would otherwise look like a "pass" (PRIMARY 0.7506-class fingerprint).
- All pins fake-only (`_fake_bundle` / `_make_fake_de` / `_shim_production_raises` patterns), zero production calls, zero disk writes. Name tests so the mapping is auditable (e.g. `test_f3a_layer_rate_*`, `test_f3b_gate_convergence_*`, `test_f3c_sw_orientation_*`).
- F3-ACC (verbatim): three fake pins (a)/(b)/(c) each shown red on buggy logic and green on fixed logic (re-review evidence, not claimed here).

## 5. Test / evidence matrix (binding)

- T-BASE: full `comparison_bench/tests/test_v80_s1_readiness.py` stays green — 45 passed + 6 subtests baseline plus the new F3 pins (no baseline test deleted or weakened; any baseline update forced by the gate/grid change must be enumerated in the return with rationale).
- T-PROFILE: profile-only path keeps `scientific_de_calls=0` and root absent (`--profile-only` never invokes sampler/DE, never creates root).
- T-HASH: config-hash handling — if the F1 grid change alters the hash, the return documents the explicit old→new rotation (old `57e5da44…684` → new value, which fields entered/left `frozen_config()`, `RECORDED_CONFIG_HASH` + test constant + `_validate_partial` updated together); silent drift = FAIL.
- T-REDGREEN: each F3 pin (a)/(b)/(c) constructible red-on-buggy / green-on-fixed (coder states the red construction per pin in the return; re-review executes the confirmation).
- Evidence: no new execution root, no production output, no `results/` / `outputs_comparison/` writes, no gamma-file writes; `verify.ok` non-adjudicating label present.

## 6. Commands, artifacts, stop rules

- Commands (venv only; run from repo root):
  - `.venv/bin/python -m pytest comparison_bench/tests/test_v80_s1_readiness.py -p no:cacheprovider -q`
  - Read-only inspection only otherwise (no `--execute-real`, no `--execution-authorized`, no `--resume-from`, no `execute()` calls, no notebook/long-run invocations).
- Artifacts: code + test edits in the two allowed files only; no new execution root; no production output; no manifest/rows/manifest writes outside the fake in-memory writer pattern; no commit/push.
- Stop rules (escalate STOP, return as blocker — do not proceed):
  - Any required science-input/hypothesis change (H anchors, f thresholds other than frozen 1.15/SW-1.0, width semantics, sampler semantics, seed/budget/cap change beyond the listed F1 grid derivation) → STOP.
  - Any temptation to auto-rerun, resume the live root, create a new root, interpret S1 numbers, or advance flip/S2/S3 → STOP.
  - Any baseline-test breakage that cannot be fixed within the frozen F1/F2 semantics → STOP (report, do not weaken silently).
  - No auto-rerun: implementation ends with tests green; rerun needs a separate fresh grant + Pre-EXECUTE (G-RERUN, not this packet).

## 7. Forbidden in this packet (restated, binding)

- No execution authorization (no grant, no Pre-EXECUTE, no `--execute-real` / `--execution-authorized`).
- No S2/S3 advance of any form.
- No S1-numbers interpretation (no reading of current-arm outputs as results).
- No workspace-root write (old root `workspace/s1_mcde_07723233-*` retained untouched; no new root).
- No push (no commit either; branch stays as-is).

## 8. Return conditions (binding)

- Return AFTER all frozen items are complete (§2 F1 + §3 F2 + §4 F3 + §5 matrix), or on a concrete blocker.
- Success return states: packet path, per-ID verdicts (F1-ACC / F2-ACC / F3-ACC), changed files (exactly the two allowed), commands + results (full-suite line, profile-only line), config-hash disposition (kept `57e5da44…684` or explicit old→new rotation), per-pin red-construction notes, deltas only (no history repeat).
- Blocker return states: the single failing command, exact error/traceback, attempted remedies, and the ONE decision needed from the main thread. "Still incomplete" is not a completion report.
- Acceptance IDs: **F1-ACC, F2-ACC, F3-ACC** (FIX_PLAN IDs reused verbatim). Downstream gates **G-D5R** (independent D5-delta re-review) and **G-RERUN** (fresh grant + Pre-EXECUTE) are NOT claimed here.

## Tasks (ordered, for coder-fast; none authorized beyond implementation)

1. F1: implement PRIMARY layer-local grid (m2=ceil(41.31f), f=1.3→≈54, sweep ≈44–60) + 0.83862 bound pin; remove full-symbol m24–31 reuse for L2; state SECONDARY disposition. [maps: F1-ACC]
2. F2: gate ∃-converged ≤1.15 (empty⇒non-pass) + f<1 SW-violation pin + m24 / m2≤47 bars + flip cross-unit guard + `verify.ok` non-adjudicating label. [maps: F2-ACC]
3. F3: add fake pins (a)/(b)/(c), each red-on-buggy/green-on-fixed by construction. [maps: F3-ACC]
4. Matrix: full suite green (45+6 baseline + new pins), profile-only 0-DE + root absent, hash rotation explicit-or-kept. [maps: §5]
5. Return per §8 (IDs + deltas + hash disposition, or concrete blocker + single decision needed).
