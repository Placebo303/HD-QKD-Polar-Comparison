# P3 Real-Data H_full Census — PREREG_AND_AUTH (2026-09-21) — DRAFT_PENDING_AUTHORIZATION

- Track: **DECIDE** (real/raw acquisition data; claim-bearing). Status: `DRAFT_PENDING_AUTHORIZATION`. Branch context: `formal-ir-v72p1-addendum-clean` (publication branch `formal-ir-v80-nbldpc-jan21`, HEAD `3d60a77e` — not touched). No switch, no commit, no push, no PR.
- Packet (frozen contract, authoritative): `docs/research_cycles/V80-NBLDPC-JAN21/P3_CENSUS_PACKET.md` (Acceptance ID **G-P3**). Operator prompt: `P3_CENSUS_PROMPT.md`.
- **Nothing has been executed. No `.ttbin` has been opened. No decoder, DE, graph, or `tools/*` call has been made. No workspace root has been created. No output has been written.**
- Compact DECIDE form permitted by `AGENTS.md` §10.3 / `docs/research-cycle-sop.md` §4: this file + `RESULT.md` + `INDEPENDENT_ACCEPTANCE.md` + machine artifacts.

## 1. Hypothesis / questions (single, falsifiable set)

- Q1: per-dataset `H_full` under ONE frozen estimator (`H_L1 + H_L2`, F03, plug-in on the TRAIN pool), with support/occupancy, Miller–Madow correction, held-out gap and bootstrap CI.
- Q2/Q3: do real frames carry memory/drift (per-frame weight distribution, block-to-block drift, lag-1/2 autocorrelation) that the memoryless `gamma_f03` generator lacks?
- Q4: conditional arithmetic only — what `f_super`/headroom/required `N` would each measured `H_full` yield at a hypothetical `m`?
- Control expectation: Family-B 2M reproduces `0.83256272` within the frozen tolerance. **No numeric outcome is pre-registered.**

## 2. Exact command (placeholder — filled at Pre-EXECUTE)

```
.venv/bin/python -m comparison_bench.src.comparison_bench.cli.<P3_CENSUS_ENTRYPOINT> \
  --packet docs/research_cycles/V80-NBLDPC-JAN21/P3_CENSUS_PACKET.md \
  --branch <A1|A2|B|C> \
  --datasets <SEMICOLON_SEPARATED_DATASET_IDS> \
  --config <FROZEN_CONFIG_JSON_PATH> \
  --root workspace/p3_census_<UUID8> \
  --bootstrap-resamples 200 --bootstrap-seed <FROZEN_SEED>
```

- `<P3_CENSUS_ENTRYPOINT>` is the new thin module to be built by the operator (packet §11); it is read-only over `src/qkd_io/ttbin_pipeline.py` and all frozen modules.
- `<FROZEN_CONFIG_JSON_PATH>` is written by the operator from the repo-resident parameters in packet §2 (Family B) or from the Branch-B fitted parameters (which are themselves outputs of Stage 0.5/§4.3, not pre-filled here).
- **[BLOCKING: needs user input]** the entrypoint module name, the dataset list, the config path, the UUID, and the bootstrap seed are all `[TO BE FROZEN]` at Pre-EXECUTE. This file deliberately invents none of them.

## 3. Budget table (frozen ceilings)

| item | ceiling |
|---|---|
| Stage 0 environment probe (TimeTagger import, `.venv` sanity; no data) | ≤ 60 s |
| Stage 0.5 file-identity probe (2 reads/dataset) | ≤ 300 s/read |
| Stage 1 per-dataset census | ≤ 1800 s/dataset, single window |
| Branch A1 total (3 datasets, Family B) | ≤ 5400 s |
| Branch B total (10 datasets) | ≤ 18000 s |
| Peak RSS | < 4 GiB |
| Decoder / DE / graph / `tools/*` calls | **0** |
| Bootstrap resamples | ≥ 200/dataset, frozen seed |

Wall-partial ⇒ `INCOMPLETE`, retained, never continued. ≤1 preregistered engineering repair+rerun for infrastructure failure only, scientific inputs unchanged, failed attempt retained in the same log.

## 4. Output-absence checks (recorded at Pre-EXECUTE, before any execution)

- [ ] `workspace/p3_census_*` does not exist (`ls workspace | rg '^p3_census_'` returns nothing).
- [ ] `rg -n 'p3_census_' --glob '!docs/research_cycles/V80-NBLDPC-JAN21/P3_CENSUS_*'` returns only this packet family.
- [ ] `results/` and `comparison_bench/outputs_comparison/` are byte-identical to their pre-execution state (no new files, no overwrites).
- [ ] No existing evidence root under `docs/research_cycles/` is modified; only `P3_CENSUS_*.md` are new.
- [ ] Intended branch confirmed: `formal-ir-v72p1-addendum-clean`; no switch; no commit; no push; no PR.
- [ ] TimeTagger package import verified in `.venv` (Stage 0); if unavailable ⇒ **STOP-BLOCKED**, the loader raises `RuntimeError: TimeTagger package not available`.
- [ ] Scoped code/config/test/packet cleanliness confirmed (no unreviewed staged/unstaged changes outside the new thin module).
- [ ] Focused tests pass: fake-only estimator identity (MM formula, split-manifest-before-statistics, root refusal), plus a dry 1-dataset control read on the frozen Family-B 2M config.
- [ ] Target output root absence re-proved with the final UUID immediately before launch.

## 5. Scope / non-goals (explicitly forbidden)

- No decoder, no DE, no graph construction, no `tools/longrun_*` / `minrerun_*` / `routeA_*`, no `experiments/run_e2e_pipeline.py`.
- No reading of any excluded derived artifact (`results*/`, `e2e_new_ttbin_fullgrid_*/`, `sidecars/`, `run_config*.json`, `*.opju`, `*.pptx`, `*.xlsx`, JSI/histogram sidecars) — inventory §1/§6.
- No overwrite of anything under `results/` or `comparison_bench/outputs_comparison/`.
- No change to `n`, `d`, `bin_width_ps`, `frame_bins`, `align`, `postselect`, channel plan, `offset_ps`, `coin_window_ps`, estimator definition, split rule, tag, or `H_full` constants.
- No pooling across datasets or families; no merging of `undetected`-class rows into success; no quoting a TRAIN plug-in as a held-out number (or vice versa) without the split side; no averaging of V19's `0.549955` with an empirical number; no invented alignment parameters, seeds, or block counts.
- **No FER / SKR / operating-point / route / qualification / publication claim.** The route decision belongs to the main thread.
- Under Branch B only: the empirical-alignment fit is pre-registered here (§4.3 of the packet) with its acceptance rule, the fitted parameters are published with the result, and the fact of fitting is declared in any resulting publication. `bin_width_ps`/`frame_bins` remain **IMPOSED-NOT-MEASURED**.

## 6. Decision criteria (frozen, binary per gate)

- **Control-arm gate (G-C)**: Family-B 2M `H_full` within the frozen tolerance of `0.83256272` (proposed ±0.01 b/symbol, `[TO BE CONFIRMED]`). FAIL ⇒ the machinery is not validated; **do not point it at new data**; return to main thread.
- **Alignment gate (G-A)**: Branch B §4.3 rules 1–2 satisfied (unique argmax with margin; single dominant peak). FAIL ⇒ `STOP-BLOCKED` for that dataset, no `H_full`.
- **Support gate (G-S)**: bootstrap CI half-width ≤ the frozen threshold (proposed 0.02 b/symbol, `[TO BE CONFIRMED]`). FAIL ⇒ `INSUFFICIENT-SUPPORT`, excluded from ranking, still reported.
- **Memory gate (G-M)**: reported, **not** gated. A positive drift/memory result is the finding and escalates to the main thread (it would invalidate synthetic→real transfer); it is not a pass/fail of this census.
- Batch closes only with independent Pre-RESULT review + main-thread acceptance. Any gate FAIL blocks solidification; never publish-then-patch.

## 7. SIGNATURE BLOCK — the user must fill this to grant execution

```
I AUTHORIZE execution of the P3 real-data H_full census under Acceptance ID G-P3,
strictly within the frozen contract of P3_CENSUS_PACKET.md and this preregistration.

  Selected alignment branch (§4 of the packet):  A1 / A2 / B / C   (circle one)
  Dataset list authorized:                      ______________________________
  Frozen config path:                           ______________________________
  Bootstrap seed:                               ______________________________
  Control-arm tolerance (b/symbol):             ______________________________
  Support-gate CI threshold (b/symbol):         ______________________________
  Total wall ceiling authorized (s):            ______________________________
  Branch / commit context confirmed:            formal-ir-v72p1-addendum-clean

  Authorized by (name/handle):                  ______________________________
  Date (UTC):                                   ______________________________
  Signature:                                    ______________________________

NOTES
- This signature is the ONLY authorization. The frozen packet and this preregistration
  authorize NOTHING by themselves.
- Pre-EXECUTE Q0–Q6 (packet §12) must be recorded and PASS before any execution.
- The grant covers ONE bounded run. Any change of branch, dataset list, config, seed,
  tolerance, threshold, or budget requires a NEW signature.
- After execution: one result record, then independent Pre-RESULT, then main-thread
  acceptance. No PR, no push, no commit without a separate explicit authorization.
```
