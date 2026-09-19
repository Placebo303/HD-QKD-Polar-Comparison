# V80 S1 — independent review (2026-09-19 evening)

- Track: review record only — no execution, no authorization, no gate status.
- Reviewer: independent thread (this session); NOT the S1 executing session.
- Branch `formal-ir-v72p1-addendum-clean`, HEAD `59ea41d0`; tree carries the new
  uncommitted S1 assets (runner / test / gamma npz / cycle docs).
- Method (read-only + one fake-only test run):
  - read `S0_RESULT.md`, `S1_READINESS.md`, `LITERATURE_QPRIOR.md`,
    `PROGRAM_PLAN.md`, `v80_s1_mcde_runner.py`, decision-log tail, git/workspace state;
  - inspected the live run root `workspace/s1_mcde_07723233-e537-4a2e-857a-954e3a94d030`
    (`manifest.json` / `rows.json`) — sampled ~18:16 while the run was ACTIVE
    (checkpoints still advancing; numbers below are a snapshot);
  - re-ran `comparison_bench/tests/test_v80_s1_readiness.py` in the authoritative
    WSL venv: **45 passed + 6 subtests passed (118.6 s, 0 scientific DE calls)**.

## 0. Live state at review time

- The S1 run is executing NOW (root created 14:48; last checkpoint 18:15:32; WSL
  started 17:24; 3 wall windows). Ledger snapshot: PRIMARY 420/420 ·
  SECONDARY 44/180 · SETUP 12 · TOTAL 476/612; `resume.next_arm = SECONDARY`.
- `manifest`: config hash `57e5da44…684` matches; `verify.ok=true` (hash + gate
  recompute only — see F2); gate PRIMARY `{f_ens 0.7505938, n=140, pass true}`;
  SECONDARY `{null, 0, false}`; provenance source `2M`; gamma
  `docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz`.
- decision-log last entry = **4438 "S1-delta review FAIL (blocks execution)"**;
  no log entries yet for the D5 rework re-review, the S1 grant, the run start, or
  the PRIMARY completion. `S1_READINESS.md` header still reads "S1 execution needs
  a separate explicit grant — NOT given here / Status: NOT accepted" while its
  addenda post-date the FAIL (checkpoint/resume/45+6). **Records must be
  reconciled by the executing session before any S1 interpretation.**

## 1. F1 (blocking) — PRIMARY arm is invalid as executed: 0/420 DE convergence

- rows: PRIMARY screen 280 + confirm 140 → `converged = true` in **0** rows;
  `f_row` present on all (0.5811 @ m24 … 0.7506 @ m31); `h_meas ≈ 0.8068`.
- Cause (analytic): PRIMARY runs the GF(32) **L2 layer** (sampler `P(U2|B,U1)`,
  width 5) at `rate = 1 − m/256`, m ∈ [24,31] → 0.879–0.906. L2 feasibility
  requires `rate ≤ 1 − H_L2/5 = 1 − 0.80690067/5 = 0.83862` (equivalently
  leak ≥ H_L2 per symbol). **Every grid rate is above the L2 capacity**, so no
  ensemble can converge — 0/420 is theory-consistent, not search noise.
- Correct layer-local mapping: `m₂ = ceil(f · H_L2 · n / 5) = ceil(41.31 f)`:
  f = 1.3 ⇒ m₂ ≈ 54 (grid over f ≈ 1.05–1.45 ⇒ m₂ ≈ 44–60). This is exactly the
  parameterization of the V26 **F03-GF32+GF32 @ f=1.3 "30/30 narrow pass"**
  precedent (decision-log 4436). The executed arm used the full-symbol budget
  grid (m = 24–31) for the L2 code — a layer↔full-symbol rate-mapping error.
- Side effect: PRIMARY "winners" were ranked by `final_entropy_bits` of
  non-converged runs → the arm's population records carry no signal.

## 2. F2 (blocking) — the gate metric cannot support pass/fail

- `evaluate_gate` (`v80_s1_mcde_runner.py:866-876`): filter = `arm`,
  `phase=confirm`, `status=ok`, `f_row` present; `f_ens = max(f_row)`;
  `pass = f_ens ≤ 1.15`. It **never consults `converged`**;
  `f_row = (1−rate)·width/h_meas` (line 538) is pure arithmetic over the config.
- Consequence 1: PRIMARY `pass (0.7506)` is computed entirely from
  **non-converged** rows — it would "pass" with zero successful DE calls, which
  is what happened. Note the value is also `< 1`: f = leak/content < 1 violates
  the Slepian–Wolf bound — itself the fingerprint of the F1 mapping error.
- Consequence 2: SECONDARY (width 10, `f_row = (m/256)·10/0.8326` ∈ [1.126,
  1.454]); max over confirm rows ≈ **1.454 (m=31) > 1.15** ⇒ as coded the
  SECONDARY gate **can never pass**, regardless of DE quality.
- The frozen intent ("ensemble 效率 ≤1.15, Müller-level") requires convergence,
  e.g. "∃ converged row with f_row ≤ 1.15" (SECONDARY: needs an m=24 config to
  converge; PRIMARY-fixed: needs m₂ ≤ 47). `verify.ok` only checks hash + gate
  recompute consistency — it is NOT a gate verdict.
- The flip rule also compares PRIMARY f (layer units) vs SECONDARY f (full-symbol
  units) — apples vs oranges as recorded.

## 3. F3 — the fake test suite cannot catch this class

- The 45+6 suite (independently re-verified green) pins mechanics with trivial
  fakes; it has no pin on (a) the layer-rate feasibility mapping, (b) the
  gate-vs-convergence semantics, (c) f ≥ 1 orientation. Same bug class as
  decision-log 4438 (D5: mechanics green, scientific semantics unchecked); that
  rework fixed the SECONDARY sampler binding but not these.

## 4. F4 — literature map gaps (fixed in PLAN §2.4)

- Müller et al., QIP 2024 `10.1007/s11128-024-04395-w` — formal version of the
  V8-reproduced line; direct comparison target.
- Tauz/Mitra/Dolecek, ITW 2024 `10.1109/itw61385.2024.10806945` — PA-aware IR via
  sampling (relaxes the IR requirement without sacrificing final key length) —
  relevant to the n=256 / 64-bit-tag budgeting at S3.
- Both appended to `PROGRAM_PLAN.md` §2.4 with citations verified live via
  SciVerse (this session; the IET-2025 industrial paper citation re-verified too).

## 5. Recommended dispositions (none executed here)

1. Do not interpret current-arm outputs; do not advance flip / S2 on them.
2. Rework (runner + tests): PRIMARY layer-rate grid (F1); gate semantics with
   `converged` (F2); non-trivial fakes pinning all three items (F3); then an
   independent re-review in the D5-delta pattern.
3. Reconcile records (decision-log entries: D5-rework acceptance, S1 grant, run
   start/results; readiness "NOT accepted" header).
4. Re-run affected arm(s) under a fresh grant (PRIMARY's 420 charged slots are
   unrecoverable; SECONDARY's grid is feasible but its gate/reporting need the
   same rework).
5. Optional S3-accounting idea: evaluate the PA-aware sampling angle (§2.4).

## 6. Non-actions / scope

- No writes to the live root, runner, tests, or any evidence root; no commit.
- Docs touched by this review: `PROGRAM_PLAN.md` (q-prior order per
  decision-log 4436; §4.2 layer-rate caution; §6 status pointer; §2.4 lit).
- This document authorizes nothing and is not an acceptance record.
