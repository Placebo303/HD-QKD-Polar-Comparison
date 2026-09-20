# P3 Operator Prompt (2026-09-21) — FROZEN, NOT GRANTED

- Track **DECIDE** (real/raw data, claim-bearing). Branch context `formal-ir-v72p1-addendum-clean`; publication branch `formal-ir-v80-nbldpc-jan21` (HEAD `3d60a77e`) untouched. No switch, no commit, no push, no PR. ID **G-P3**: frozen only, authorizes NOTHING.
- Entrypoint: `docs/research_cycles/V80-NBLDPC-JAN21/P3_CENSUS_PACKET.md` (§§1–12 frozen) + `P3_CENSUS_PREREG_AND_AUTH.md` (signature required).
- Zero decoder calls, zero DE calls, zero graph construction, zero `tools/longrun_*`/`minrerun_*`/`routeA_*`, zero `experiments/run_e2e_pipeline.py`.

## Before anything (stop conditions)

1. Confirm the signed `PREREG_AND_AUTH.md` names the branch (A1 / A2 / B / C), dataset list, config path, seed, tolerances, and wall ceiling. If any is blank ⇒ **STOP-BLOCKED**, return to the main thread. Do not fill them in yourself.
2. Confirm intended branch, scoped cleanliness, output absence (`workspace/p3_census_*` absent; `rg 'p3_census_'` only in this packet family), and focused fake-only tests. Record Q0–Q6 Pre-EXECUTE. FAIL ⇒ stop.
3. Stage 0: verify `TimeTagger` imports in `.venv`. Unavailable ⇒ **STOP-BLOCKED** (the loader raises `RuntimeError`).
4. Stage 0.5: read each `X.ttbin` / `X.1.ttbin` pair member separately via `read_ttbin_events`; record `total_events`/`valid_events`/`missed_events_total`/`timetag_min`/`timetag_max`/`timetag_span`. Exactly one member yields events ⇒ that is the stream (record evidence). Both or neither ⇒ **STOP-BLOCKED**.

## Run (one bounded window per authorized dataset list)

5. Root: fresh additive `workspace/p3_census_<uuid8>` (absence re-proved with the final UUID immediately before launch). `results/` and `comparison_bench/outputs_comparison/` forbidden. Existing evidence roots untouched.
6. Write `split_manifest.json` (60/20/20 consecutive-time by ascending frame index, V49 convention) **as the first artifact, before any statistic**.
7. Per dataset: `run_ttbin_parse_pipeline` (frozen, read-only) with the frozen config; then compute per-frame weights, block drift, and autocorrelations in the NEW thin module, asserting equality with `compute_ttbin_metrics` aggregates on the control arm.
8. Estimator (frozen, one definition): `H_full = H_L1 + H_L2`, F03 (`u1=A>>5`, `u2=A&31`), plug-in `P(a|b)=N_ab[a,b]/N_ab[:,b]` on the **TRAIN** pool, bits per GF(32) symbol. Also report `H_L1`, `H_L2`, support, occupancy, Miller–Madow `(K−1)/(2N·ln2)`, `NLL_HOLD` gap, and a ≥200-resample frame-level bootstrap CI. Bootstrap CI is mandatory for every dataset with `H_full < 0.83256272`.
9. Branch B only: channel plan = unique argmax of coincidence throughput with second-best ≤ 50 %; single dominant peak; `offset_ps` = peak, `coin_window_ps` = frozen multiple of peak width. `bin_width_ps=200`, `frame_bins=1024`, `align="global"`, `postselect="keep_all"` are **IMPOSED-NOT-MEASURED**. Label every such row `ALIGNMENT-FITTED`.

## Metrics / schema

10. Emit the §8 per-source table with exactly the frozen columns (`census_table.csv` + `census_table.json`), including `comparable_by_anchor` (YES / DIRECTIONAL-ONLY / NO) and `status` (OK / INSUFFICIENT-SUPPORT / BLOCKED). No pooling across datasets or families.
11. Conditional arithmetic only (§9): `content=1024·H`, `f_super(m)=(5m+64)/content`, `headroom=1.3·content−(5m+64)`, `N≥⌈3·4.785675/(1.3−f_super)⌉`. Report the table; select NO operating point. Remember: at fixed m=208, any `H < 0.829327` is out of box (`f>1.3`).

## Budgets / stop

12. ≤1800 s/dataset single window; ≤5400 s total (A1) / ≤18000 s (B); RSS < 4 GiB; 0 decoder/DE/graph calls. Wall-partial ⇒ `INCOMPLETE`, retained, no continuation. ≤1 preregistered engineering repair+rerun for infrastructure failure only, inputs unchanged, failure retained in the same log.
13. **STOP** on any science-input change (`n`, `d`, bin width, frame bins, align, postselect, channels, offset, coin window, estimator, split rule, tag, `H_full` constants, hypothesis, data roles, branch).
14. FORBIDDEN: reading any excluded derived artifact; overwriting any evidence root; pooling; merging `undetected` into success; quoting TRAIN plug-in as held-out (or vice versa) without the split side; averaging V19's `0.549955` with an empirical number; inventing alignment parameters, seeds, or block counts; committing or pushing.

## Deliverables

15. `P3_CENSUS_RESULT.md` (per-source table, control-arm reproduction verdict vs `0.83256272`, memory/stationarity battery, uncertainty statements) + `census_table.csv` + `census_table.json` + `split_manifest.json` + per-dataset `ttbin_config.json` / `ttbin_metrics.json` + file-identity evidence.
16. Then: independent **Pre-RESULT** review → `INDEPENDENT_ACCEPTANCE.md` → main-thread acceptance. No `RESULT.md` publication before that review.

## Interpretation / claim ceiling

17. Claim ceiling: real-data `H_full` with uncertainty, per-plane decomposition, memory/stationarity diagnostics. Does NOT establish FER, SKR, an operating point, a route decision, qualification, or a publication number. A positive drift/memory result escalates to the main thread (it would invalidate synthetic→real transfer) — the operator reports it and draws no conclusion.
18. **Pre-EXECUTE Q0–Q6 + the signed user grant are required before ANY execution. This prompt authorizes NOTHING.**
