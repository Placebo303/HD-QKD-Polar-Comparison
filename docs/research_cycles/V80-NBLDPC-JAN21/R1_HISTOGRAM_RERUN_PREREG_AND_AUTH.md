# R1 Histogram Re-run — PREREG_AND_AUTH (2026-09-21) — DRAFT_PENDING_AUTHORIZATION

- Track: **DECIDE** (real/raw acquisition data; outputs correct published design points and feed the X1 route campaign). Status: `DRAFT_PENDING_AUTHORIZATION`. Branch context: `formal-ir-v72p1-addendum-clean` (publication branch `formal-ir-v80-nbldpc-jan21` — not touched). No switch, no commit, no push, no PR.
- Packet (frozen contract): `docs/research_cycles/V80-NBLDPC-JAN21/R1_HISTOGRAM_RERUN_PACKET.md` (Acceptance ID **G-R1**). Operator prompt: `R1_HISTOGRAM_RERUN_PROMPT.md`.
- **Nothing has been executed. No `.ttbin` has been opened. No decoder, DE, graph, or `tools/*` call has been made. No workspace root has been created. No output has been written.**
- Compact DECIDE form permitted by `AGENTS.md` §10.3 / `docs/research-cycle-sop.md` §4: this file + `RESULT.md` + `INDEPENDENT_ACCEPTANCE.md` + machine artifacts.

## 1. Hypothesis / questions (single, falsifiable set)

- Q1 (estimator correction): what are the per-source CONDITIONAL-entropy Miller–Madow-corrected values `H_corr = H_plug + (K_AB − K_B)/(2·N_train·ln2)` on the TRAIN pool, with bootstrap CI — and how far do they move vs the defective-basis Baseline §3 values (H_MM 0.8036079281174853 / 0.8289616869054485 / 0.8345846048587662)? **No numeric outcome is pre-registered**; corrected values are `[TO BE MEASURED]`. Bounded expectation only (not a prediction): the move is DOWN by `(K_B−1)/(2N·ln2)`, at most 0.002339/0.001672/0.001252 b at K_B = 1024 (estimator-verification §T2).
- Q2 (bundle materialization): do the persisted sparse TRAIN histograms + `p_b` satisfy the X1 bundle-input requirements (shapes (1024,1024)/(1024,), normalization, reconstruction checksums) for all three sources?
- Q3 (2M lineage): how do the re-derived 2M inputs compare against the frozen `gamma_f03.npz` lineage (report-only finding per packet §2.7)?
- Control expectations (machinery checks, not science predictions): §3A alignment re-derives bin 8191/8192 (−50/+50/+50); determinism gate (f) reproduces A1 frame counts/split boundaries exactly.

## 2. Exact command (placeholders — filled at Pre-EXECUTE, never invented)

```
PYTHONPATH=<repo-root> .venv/bin/python -m comparison_bench.src.comparison_bench.cli.r1_histogram_rerun \
  --bases <BASE_1M;.1.5M;.2M_BASE_X_TTBIN> \
  --datasets T2-1M;T2-1.5M;T2-2M \
  --root workspace/r1_histogram_<UUID8> \
  --bootstrap-seed 20260921 --bootstrap-resamples <200|0-WAIVED> \
  --per-read-timeout-s 300 --budget-s <5400|1800-WAIVED>
```

- `<BASE_...>` = the three Jan-21 trio base `X.ttbin` members (same members A1 read; `[TO BE CONFIRMED at Pre-EXECUTE]` against `docs/DATA_INVENTORY_20260921.md`). Base-only; never `.1`; never both.
- `<UUID8>`, budget row, and tolerance confirmations are `[TO BE FROZEN]` at Pre-EXECUTE. This file deliberately invents none of them.
- Bootstrap `0-WAIVED` only with explicit main-thread waiver recorded below; waived runs mark every design-point row `NO-CI`.

## 3. Budget table (frozen ceilings — circle the authorized row in the signature block)

| row | per-read | per-dataset | trio total | RSS | decoder/DE/graph |
|---|---|---|---|---|---|
| A — with bootstrap (default) | ≤ 300 s | ≤ 1800 s | ≤ 5400 s | < 4 GiB | 0 |
| B — bootstrap-waived (cost path) | ≤ 300 s | ≤ 600 s | ≤ 1800 s | < 4 GiB | 0 |

Wall-partial ⇒ `INCOMPLETE`, retained, never continued. ≤1 preregistered engineering repair+rerun for infrastructure failure only, scientific inputs unchanged, failed attempt retained in the same root.

## 4. Output-absence checks (recorded at Pre-EXECUTE, before any execution)

- [ ] `workspace/r1_histogram_*` does not exist (`ls workspace | rg '^r1_histogram_'` returns nothing).
- [ ] `rg -n 'r1_histogram_' --glob '!docs/research_cycles/V80-NBLDPC-JAN21/R1_*'` returns only this packet family.
- [ ] `results/` and `comparison_bench/outputs_comparison/` are byte-identical to their pre-execution state (no new files, no overwrites).
- [ ] Existing evidence roots (`workspace/p3_census_3954637c/`, `workspace/p3_stage05_ee32030a/`) untouched; `git diff -- src/` empty.
- [ ] Intended branch confirmed: `formal-ir-v72p1-addendum-clean`; no switch; no commit; no push; no PR.
- [ ] TimeTagger import verified in `.venv` via the alias shim; if unavailable ⇒ **STOP-BLOCKED**.
- [ ] Scoped code/config/test/packet cleanliness confirmed (only the additive R1 executor + its tests).
- [ ] Focused tests pass: fake-only K_B/correction-identity/sparse-round-trip/bundle-gate tests (packet §7 T-R1-3).
- [ ] Target output root absence re-proved with the final UUID immediately before launch.

## 5. Scope / non-goals (explicitly forbidden)

- No X1 cliff arms; no decoder, no DE, no graph construction, no `tools/longrun_*` / `minrerun_*` / `routeA_*`, no `experiments/run_e2e_pipeline.py`.
- No change to any frozen scientific input (n, m, tag, H_full anchor, gates, thresholds, seeds, split rule, trio parameters).
- No retraction or re-run of the A1 synthetic FER arms (b2f/b2g etc.).
- No reading of any excluded derived artifact; no overwrite of `results/` or `comparison_bench/outputs_comparison/`; no pooling across sources; no merging of `undetected` into success (N/A, invariant kept); no quoting TRAIN numbers as held-out or vice versa without the split side.
- **No FER / SKR / route / qualification / publication claim.** Corrected design points do NOT authorize X1 by themselves.

## 6. Decision criteria (frozen, binary per gate)

- **G-A (alignment):** packet §3A gates pass per source, else STOP-BLOCKED for that source, others continue.
- **G-B (span):** span-continuity assertion passes per source, else STOP-BLOCKED for it.
- **G-C (atomicity):** per source both artifact sets persist or the source is INCOMPLETE; no partial close-out.
- **G-D (K_B sanity):** 1 ≤ K_B ≤ 1024 AND K_B < K_AB, else STOP-BLOCKED for it.
- **G-E (2M lineage):** comparison reported; material discrepancy (|ΔH| > 0.01/plane OR p_b L_inf > 1e-3) ⇒ FINDING escalated, never smoothed, never refit.
- **G-F (determinism):** frame counts + split boundaries + derived alignment reproduce A1 exactly, else STOP-BLOCKED for it (infrastructure drift ⇒ ≤1 repair path).
- Batch closes only with independent Pre-RESULT review + main-thread acceptance. Any gate FAIL blocks solidification; never publish-then-patch.

## 7. SIGNATURE BLOCK — the user must fill this to grant execution

```
I AUTHORIZE execution of the R1 histogram re-run under Acceptance ID G-R1,
strictly within the frozen contract of R1_HISTOGRAM_RERUN_PACKET.md and
this preregistration.

  Base members authorized (3 paths):        ______________________________
  Output root (fresh, absent):              workspace/r1_histogram________
  Budget row authorized (circle):           A (≤5400 s, bootstrap) / B (≤1800 s, waived)
  Bootstrap resamples / seed:               ________ / 20260921
  Span tolerance (s, proposed 0.5):            ______________________________
  2M materiality bars confirmed:            |ΔH|>0.01 / p_b L_inf>1e-3  (yes / amended: ___)
  Branch / commit context confirmed:        formal-ir-v72p1-addendum-clean

  Authorized by (name/handle):              ______________________________
  Date (UTC):                               ______________________________
  Signature:                                ______________________________

NOTES
- This signature is the ONLY authorization. The frozen packet and this
  preregistration authorize NOTHING by themselves.
- Pre-EXECUTE Q0–Q6 (packet §8) must be recorded and PASS before any execution.
- The grant covers ONE bounded run. Any change of base members, root, budget
  row, seed, tolerance, or threshold requires a NEW signature.
- After execution: one result record, then independent Pre-RESULT, then
  main-thread acceptance. No PR, no push, no commit without a separate
  explicit authorization.
```

*(This block is BLANK by design — the planner does not sign. The user fills it.)*
