> **Amendment 2026-09-21 (main-thread decision — bootstrap NOT waived; stale row-B text annotated).** Steps 13/19/30 below still carry the WITHDRAWN Row B / NO-CI budget alternative. Bootstrap (≥200 resamples, frozen seed 20260921) is REQUIRED with no waiver; the single budget ceiling is per-read ≤300 s, per-dataset ≤1800 s, trio ≤5400 s, RSS <4 GiB, 0 decoder/DE/graph calls. Authoritative sources: `R1_HISTOGRAM_RERUN_PACKET.md` §2.8 and `R1_HISTOGRAM_RERUN_PREREG_AND_AUTH.md` §3 (the packet amendment of 2026-09-21 explicitly left the prereg/prompt files untouched; this annotation closes the resulting stale-text gap per the P3-A1-REVIEW F-7 precedent). This note is additive; no other prompt text is modified.

# R1 Operator Prompt (2026-09-21) — FROZEN, NOT GRANTED

- Track **DECIDE** (real/raw data, claim-bearing). Branch context `formal-ir-v72p1-addendum-clean`; publication branch `formal-ir-v80-nbldpc-jan21` untouched. No switch, no commit, no push, no PR. ID **G-R1**: frozen only, authorizes NOTHING.
- Entrypoint: `docs/research_cycles/V80-NBLDPC-JAN21/R1_HISTOGRAM_RERUN_PACKET.md` (§§1–8 frozen) + `R1_HISTOGRAM_RERUN_PREREG_AND_AUTH.md` (signature required).
- Zero decoder calls, zero DE calls, zero graph construction, zero `tools/longrun_*`/`minrerun_*`/`routeA_*`, zero `experiments/run_e2e_pipeline.py`.

## Before anything (stop conditions)

1. Confirm the signed `PREREG_AND_AUTH.md`: three base paths, root `workspace/r1_histogram_<uuid8>`, budget row A/B, seed 20260921, span tolerance, 2M materiality bars, signature. Any blank ⇒ **STOP-BLOCKED**, return to main thread. Do not fill them in yourself.
2. Confirm intended branch, scoped cleanliness (`git diff -- src/` empty; only the additive R1 executor + tests), output absence (`workspace/r1_histogram_*` absent; `rg 'r1_histogram_'` only in this packet family), and focused fake-only tests (K_B edges, correction identity, sparse round-trip, bundle gates). Record Q0–Q6 Pre-EXECUTE. FAIL ⇒ stop.
3. Verify `TimeTagger` imports in `.venv` via `install_timetagger_alias()`. Unavailable ⇒ **STOP-BLOCKED** (the loader raises `RuntimeError`).
4. Re-prove target root absence with the final UUID immediately before launch.

## Run (one bounded window, trio order 1M → 1.5M → 2M)

5. Root: fresh additive `workspace/r1_histogram_<uuid8>`. `results/` and `comparison_bench/outputs_comparison/` forbidden. Existing evidence roots (`workspace/p3_census_3954637c/`, `workspace/p3_stage05_ee32030a/`) untouched.
6. Per source, IN ORDER: (i) open ONLY the base `X.ttbin` (vendor auto-follow covers `.1`; never both, never concatenate); (ii) span-continuity assertion (span > 0 AND |span − mtime-gap| ≤ tol, else STOP-BLOCKED for that source, continue others); (iii) §3A alignment FIRST (`compute_cross_correlation_histogram` 100 ps / ±819200 ps → argmax → `offset_ps = +lag_center_ps[pk]`; gates p2bg ≥ 100, single dominant mode, sigma 10–500 ps — FAIL ⇒ STOP-BLOCKED for that source, continue others, no fallback); record `offset_ps_derived`, `peak_bin_index`, `peak_center_ps`, `peak_to_bg`, `sigma_crude_ps` + one-bin comparison vs recorded −50/+50.
7. ONLY for passed sources: frozen trio pairing/framing (A=1/B=5, coin 200, `nearest_unique`, bw 200, d=1024, `global`, `keep_all`) with the DERIVED offset; 60/20/20 consecutive-time TRAIN/VAL/HOLD split by ascending frame index — write `split_manifest.json` FIRST, before any statistic; build TRAIN `N_ab` only (VAL/HOLD untouched).
8. Estimator (ONE frozen definition — conditional, not joint): `H_plug = H_L1+H_L2` via F03 on TRAIN `N_ab`; `K_B_train` = occupied B columns; `H_corr = H_plug + (K_AB−K_B)/(2·N_train·ln2)`; ALSO persist defective `H_MM_old = H_plug + (K_AB−1)/(2·N_train·ln2)` + `Δ`. Bootstrap CI on the CORRECTED statistic (≥200 resamples, seed 20260921; waived only if the signature says row B — then mark rows `NO-CI`). Full precision everywhere; state split side on every number.
9. Persist per source (§2.6 — both-or-neither: ALL or NONE): `K_B_train`, `p_b_train` (1024,), sparse TRAIN `N_ab` (COO npz + sum/nnz checksums), `N_train`, `K_AB`, `H_L1/H_L2/H_plug/H_corr/H_MM_old/Δ`, CI, alignment/span/split provenance. Enforce gate (d): 1 ≤ K_B ≤ 1024 AND K_B < K_AB, else STOP-BLOCKED for that source.
10. Enforce gate (f): frame counts + split boundaries + derived alignment must reproduce A1 exactly (one-bin AGREE minimum). Mismatch ⇒ STOP-BLOCKED for that source (drift ⇒ ≤1 engineering-repair path, inputs unchanged, failure retained).

## Metrics / schema

11. Emit `corrected_design_points.json/.csv` (full precision: H_corr, content=1024·H, m_max raw+capped-208, f@208/@200/@199, N_req=⌈3·4.785675/(1.3−f)⌉) + `delta_vs_baseline_S3.md` (ΔH/Δcontent/Δf/Δm_max/ΔN_req + verdict movement vs Baseline §3). Select NO operating point.
12. 2M consistency (read-only, report-only): compare re-derived 2M inputs vs frozen `gamma_f03.npz` lineage (ΔN expected-vintage note; per-plane ΔH_L1/ΔH_L2; p_b max-abs-diff). Material (|ΔH|>0.01/plane OR p_b L_inf>1e-3) ⇒ FINDING for the main thread. NEVER refit/replace `gamma_f03.npz`; NEVER substitute into any decoder path.

## Budgets / stop

13. Row A: ≤1800 s/dataset, ≤5400 s total. Row B (waived): ≤600 s/dataset, ≤1800 s total. Per-read ≤300 s; RSS <4 GiB; 0 decoder/DE/graph. Wall-partial ⇒ `INCOMPLETE`, retained, never continued. ≤1 engineering repair+rerun for infrastructure failure only.
14. **STOP** on any science-input change (n, m, tag, anchor, gates, thresholds, seeds, split rule, trio parameters, estimator definition, data roles).
15. FORBIDDEN: both-member open/concat; pooling; decoder/DE/graph; `src/` modification; writes to `results/`/`comparison_bench/outputs_comparison/`; excluded-artifact reads; `undetected`-merging (invariant); inventing params/seeds/paths/counts; committing or pushing.

## Deliverables

16. Per-source `<SRC>.json` + `<SRC>_N_ab_train_sparse.npz` + `<SRC>_p_b_train.npy`; `split_manifest.json` (first); `corrected_design_points.json/.csv`; `delta_vs_baseline_S3.md`; `alignment_table.md`; `R1_RESULT.md`.
17. Then: independent **Pre-RESULT** review → acceptance → main-thread close-out of BOTH open items. No publication before that review.

## Interpretation / claim ceiling

18. Claim ceiling: corrected per-source design points + materialized bundle inputs ONLY. No FER/SKR/route/qualification/publication claim. Corrected points do NOT authorize X1 — X1 needs its own entry gate. `H_corr` is CONDITIONAL on the re-derived alignment and the TRAIN split side.
19. **Pre-EXECUTE Q0–Q6 + the signed user grant are required before ANY execution. This prompt authorizes NOTHING.**
