# X1 Successor Operator Prompt (2026-09-21) — FROZEN, NOT GRANTED

- Track **EXPLORE** (synthetic only; **EXPLORE_HEAVY**, 15 arms; ≤1800 s/arm, ≤27000 s total). Branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push). Publication branch untouched. ID proposed **G-X1S**: frozen only, authorizes NOTHING.
- Entrypoint: `docs/research_cycles/V80-NBLDPC-JAN21/X1_SUCCESSOR_ENTRY_PACKET.md` (§§1–9 frozen) + `X1_SUCCESSOR_ENTRY_PREREG_AND_AUTH.md` (grant required).
- Zero `.ttbin` reads (any read STOP-BLOCKED). Zero decoder/DE/graph-kernel changes. Zero `tools/longrun_*`/`minrerun_*`/`routeA_*`, zero `experiments/run_e2e_pipeline.py`.

## Before anything (stop conditions)

1. Confirm the grant in `X1_SUCCESSOR_ENTRY_PREREG_AND_AUTH.md`: EXACTLY ONE authorization box complete (written signature OR verbatim conversation grant), with bundle-root UUID, per-arm root pattern, exact bundle paths, key-prefix freeze (`1M;1p5M;2M` proposal; `1.5M` never a key), grid/seeds/instance verbatim, budget-ceiling confirmation, thin-runner path. Any blank / mismatch ⇒ **STOP-BLOCKED**, return to main thread. Do not fill them in yourself.
2. Confirm intended branch, scoped cleanliness (`git diff -- src/` empty; only the additive bundle builder + verification reporter + thin runner, if any, + fake-only tests), output absence (`workspace/x1_bundles_*` absent; per-arm `workspace/x1_*` pattern absent; `rg 'x1_bundles_|X1_SUCCESSOR'` only in this packet family; `results/` + `comparison_bench/outputs_comparison/` byte-identical snapshots), and focused fake-only tests (bundle round-trip, bind-gate refusals incl. cross-source-label, construct pins, bar/gate arithmetic incl. rule-(c), root refusal). Record Q0–Q6 Pre-EXECUTE. FAIL ⇒ stop.
3. Build + verify the §2.6 bundles BEFORE any arm: dense-reconstruct from `workspace/r1_histogram_5e2a91c4/` COOs → `ChannelAdapter(fact_id="F03", …)` (unmodified, seconds) → `workspace/x1_bundles_<UUID8>/x1_gamma_f03r1.npz` + `x1_gamma_f03r1_pb.npz` with keys `{source}_gamma1_L1` (32,1024) / `{source}_gamma2_L2condU1` (32,32,1024) / `{source}_p_b` (1024,; sum=1±1e-9). Enforce gate G-D: `bind_empirical_bundle()` shape/normalization gates + R1 checksum identities (sum==N_train 315504/441487/589461; nnz==K_AB 2395/2439/2597; occupied-B==K_B 1024 ×3; p_b==colsum/N) + 2M report-only comparison (materiality |ΔH|>0.01/plane OR p_b L_inf>1e-3 ⇒ FINDING, never refit). G-D FAIL for a source ⇒ STOP-BLOCKED for that source (others may proceed); no fallback bundle, no vintage substitution. 2M decode arms bind the FROZEN `gamma_f03.npz` + `gamma_f03_pb.npz` read-only — NEVER the re-derived-2M verification file.
4. Re-prove target root absence with the final UUIDs immediately before launch (bundle root + first arm root).

## Run (one bounded batch; frozen order — the grant covers this conditional sequence)

5. Roots: bundle root `workspace/x1_bundles_<UUID8>` (shared read-only input); per-arm decode roots `workspace/x1_<uuid8>` (fresh additive per arm). `results/` and `comparison_bench/outputs_comparison/` forbidden. Existing evidence roots (`workspace/p3_census_3954637c/`, `workspace/p3_stage05_ee32030a/`, `workspace/r1_histogram_5e2a91c4/`) untouched (R1 root read-only).
6. Arm order (frozen; one authorization covers the sequence while the preceding machine gate permits — operator continues between arms, no per-arm grant):
   (i) bundle verification (step 3, gate G-D);
   (ii) X1-2M {192, 196, 204} (P2-overlap ONCE — if P2 already ran any of these, consume BY REFERENCE instead; never re-measure);
   (iii) X1-2M {200-STANDALONE, 208} (200-STANDALONE ≠ P1 nested leading-200; F202 6/240 + F208 0/240 citable BY CITATION as consistency checks, never pooled);
   (iv) X1-1.5M {191, 195, 199, 203, 207} ascending;
   (v) X1-1M {185, 189, 193, 197, 201} ascending (m=201 EXPECTED-OUT on G-B; run as retained-frozen characterization, report OUT).
7. Per arm, run ONE invocation: `--arm X1-<source>-<m>` with `<source>` ∈ {1M, 1.5M, 2M} (bundle key `1M|1p5M|2M` per the frozen prefix), m from the frozen grid — 1M {185,189,193,197,201}; 1.5M {191,195,199,203,207}; 2M {192,196,200,204,208} (packet §2.2). SINGLE construction instance 2026092001, standalone per-m construct (`X1-*-S<m>-standalone` — NOT P1 nested submatrices); pins fc=0 + rank-full + twice-identical GATED, girth recorded; 240 blocks, seeds `2026095601+idx` idx 0..239, stream `o1_blk:{seed}`; root `workspace/x1_<uuid8>` (fresh, absence proven). Cross-source channel reuse FORBIDDEN — executor refuses a channel whose source label ≠ arm source.
8. Decode: b2f soft-marginal prior verbatim, v28 `decode_error_domain_posterior` max_iter 300/streak 3, `exact_match` accept; NO genie/argmax/L1. Report-only per block: `prior_entropy_bits`, `u1_mismatches`. Metrics per arm: FER = fails/240; f_super = (5m+64)/(1024·H_source_corr) with H_corr ∈ {0.8012690084416184, 0.8272902027770036, 0.8333327179427281} (arm's OWN source — NEVER another source's H, NEVER the defective 0.80361/0.82896/0.83458); f_eff = f_super+4.785675·FER (frozen slope); `undetected`-class logged separately, never success.
9. Gates per arm (AND): (a) fails/240 ≤ 12 internal route gate (bar-12 early-stop ⇒ FAIL + CENSORED, never extrapolated); (b) f_super ≤ 1.3 own corrected H; (c) N ≥ ceil(3·4.785675/(1.3−f_super)) — expected to FAIL essentially everywhere high-m passes (a); never present a single-source f_eff as certifiable/literature-comparable (f-margin IN vs N-count certifiability are DISTINCT — esp. 2M high-m). Label each arm monotone / non-monotone / censored; NO cross-m monotonicity inference.
10. STOP on any science-input change (n, m, tag, H basis, λ, seeds, thresholds, channel, decoder, hypothesis, data roles, key prefixes, bundle inputs); any `.ttbin` read (either member, any dataset) is STOP-BLOCKED; vintage `channel_counts.npz` substitution is a main-thread decision, NEVER an executor substitution. No pooling across sources/m-points/instances; never quote f_super as f_eff when FER > 0.

## Metrics / schema

11. Per arm persist in its root: `X1_RESULT_*.md` (arm ID, construction label, bundle path + key prefix, seeds/instance/pins, wall/RSS, fails/240, FER, iters, f_super/f_eff own-basis with H_corr stated, undetected count, monotone/non-monotone/censored label, G-A…G-E verdicts) + `rows.json` (one row per block: block idx, seed, iters, wall, decoded/failed/undetected flags, prior_entropy_bits, u1_mismatches) + `block_accounting.csv` (same columns, machine-readable). State TRAIN-side bundle provenance + derived-alignment conditionality on every row. Select NO operating point.
12. Batch artifacts: bundle-build log + G-D verification report in `workspace/x1_bundles_<UUID8>/` (bind gates, checksum identities, 2M report-only comparison); ONE append-only `EXPLORATION_LOG.md` at the frozen batch-log path (attempts in arm order; the ≤1 preregistered engineering correction if used with exact error + unchanged-inputs attestation + retained-failure location, else the explicit "no repair path used" line; retained INCOMPLETE/CENSORED/BLOCKED arms never overwritten/continued).

## Budgets / stop

13. ≤1800 s/arm (single window), ≤27000 s total; per-decode ≤300 s terminal; RSS <4 GiB; 1 CPU; 0 `.ttbin` reads; 0 kernel changes. Wall-partial ⇒ `INCOMPLETE`, retained, never continued. ≤1 engineering repair+rerun for infrastructure failure ONLY (scientific inputs/seeds/thresholds/data roles/hypothesis unchanged, failed attempt retained in the same root(s) + log); a second failure ⇒ STOP-BLOCKED, batch-end review adjudicates.
14. FORBIDDEN: either-member `.ttbin` open/concat; pooling; decoder/DE/graph-kernel modification; `src/` modification; writes to `results/`/`comparison_bench/outputs_comparison/`; excluded-artifact reads; `undetected`-merging; inventing params/seeds/paths/counts/prefixes; committing or pushing.

## Deliverables

15. Bundle root (`workspace/x1_bundles_<UUID8>/`): `x1_gamma_f03r1.npz` + `x1_gamma_f03r1_pb.npz` + `BUNDLE_BUILD_LOG.md` + verification report (G-D evidence).
16. Per-arm roots (`workspace/x1_<uuid8>/` × attempted arms): `X1_RESULT_*.md` + `rows.json` + `block_accounting.csv`.
17. Batch: ONE append-only `EXPLORATION_LOG.md` + ONE batch-end independent review file + main-thread acceptance pointer. No per-arm review files.
18. Then: batch-end independent review → main-thread acceptance → close-out (P1 per-source bases consume X1 by reference; no P1/P2 execution here). No publication before that review.

## Interpretation / claim ceiling

19. Claim ceiling: synthetic per-source FER curves ONLY (fails/240 + f_super/f_eff own-basis + iters/wall + undetected log). Curves do NOT select an operating point; the operating-point decision is a LATER DECIDE step. Generality headlines LEAD with 1M; 2M-only headline FORBIDDEN. The m≤201 relocation reads ONLY under the per-block disclosure model (baseline §2(a)); under the ratified sacrifice/amortized default it does NOT follow. `H_corr` is CONDITIONAL on the R1 §3A alignment + TRAIN split side. f-margin IN and N-count certifiability are distinct verdicts — keep them distinct.
20. **Pre-EXECUTE Q0–Q6 + G-D verification + the user grant are required before ANY execution. This prompt authorizes NOTHING.**
