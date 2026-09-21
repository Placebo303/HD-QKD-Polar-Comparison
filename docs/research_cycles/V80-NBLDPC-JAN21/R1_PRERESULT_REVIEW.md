# R1 Histogram Re-run — Independent Pre-RESULT Review (G-R1)

- Reviewer: reviewer-go subagent (independent thread; read-only except this file)
- Date (UTC): 2026-09-21
- Track: **DECIDE**
- Gate: **Pre-RESULT** per `AGENTS.md` §3 / §10.3 — before any publication/commit and before main-thread acceptance
- Evidence root: `workspace/r1_histogram_5e2a91c4/` (18 files, as expected)
- Overall verdict: **PASS_WITH_FINDINGS** — no gate FAILs; all findings non-blocking; solidification may proceed upon main-thread acceptance + the ratifications in §6

## Contracts read

- `docs/research_cycles/V80-NBLDPC-JAN21/R1_HISTOGRAM_RERUN_PACKET.md` §§1–8 (frozen design, gates, claim ceiling)
- `docs/research_cycles/V80-NBLDPC-JAN21/R1_HISTOGRAM_RERUN_PREREG_AND_AUTH.md` (top chat-grant amendment note; §7/§8 intentionally blank)
- `docs/V80_BASELINE_20260921.md` §§1–3 (invariants I1–I6; §3 design-point table under correction)
- `docs/A1_ARITHMETIC_RECOMPUTE_20260921.md` (full-precision rules; baseline-§3 values replaced)
- `docs/A1_ESTIMATOR_AND_SLOPE_VERIFICATION_20260921.md` §§T1–T3 (estimator defect; K_B≳253 conditional)
- `workspace/p3_census_3954637c/` (A1 census root, read-only determinism reference)
- `docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz` + `gamma_f03_pb.npz` (frozen 2M lineage, read-only)
- `comparison_bench/src/comparison_bench/cli/r1_histogram_rerun.py` + `p3_census_a1.py` (code under audit; former read for reuse-by-import, defect lines 344–349 confirmed cited correctly)
- `AGENTS.md` §10.3 (this gate), §5.5 (scientific semantics)

## Method

No file edits, no commit/push, no `.ttbin` opened, no pipeline/decoder executed.
All recomputations done via the repo interpreter
(`PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python`, pure
arithmetic + `np.load` of the `npz`/`npy` artifacts + `json` reads).
Every operator number below was re-derived from the sparse COO triplets and
frozen arithmetic rules, not trusted from the JSONs.

## 1. Estimator auditability — PASS (recomputed exactly, all three sources)

From each `T2-*.json` + its sparse npz, independently recomputed FROM THE COO:

| check | T2-1M | T2-1.5M | T2-2M |
|---|---|---|---|
| `K_AB == nnz(COO)` (2395/2439/2597) | exact | exact | exact |
| `K_B == #{b: colsum>0}` FROM COO (1024 ×3) | exact | exact | exact |
| `N_train == sum(count)` (315504/441487/589461) | exact | exact | exact |
| `H_corr == H_plug + (K_AB−K_B)/(2·N·ln2)` | diff 0.0 | diff 0.0 | diff 0.0 |
| `H_MM_old == H_plug + (K_AB−1)/(2·N·ln2)` | diff 0.0 | diff 0.0 | diff 0.0 |
| `Δ == (K_B−1)/(2·N·ln2)` | diff ≤2.5e-17 | diff ≤7.7e-17 | diff ≤8.9e-18 |
| `p_b` sums to 1, equals COO colsum/N | maxabs 0.0 | maxabs 0.0 | maxabs 0.0 |
| split side stated TRAIN on every row | yes | yes | yes |

Additional cross-checks: `H_L1+H_L2 == H_plug` exactly; `H_MM_old` equals the
A1 `census_table.json` `H_full_MM` bit-for-bit (0.8036079281174853 /
0.8289616869054485 / 0.8345846048587662); `H_plug` and `K_AB` likewise equal
the A1 values — confirming the same TRAIN realization, not just the same files.
`K_B = 1024` on all three converts the estimator-verification inference
("plausible ≈1024") into MEASURED fact; the `K_B≳253` conditional for the 1M
`m_max` 201→200 flip is now satisfied by measurement (see §3).
`p_b_min` > 0 on all three (0.000681/0.000689/0.000762) — consistent with full
B support at N_train ~3–6×10⁵.

## 2. Gates (a)–(f) — all PASS, re-derived from recorded scalars

- **(a) Alignment**: p2bg 1186.3/748.2/546.1 (≥100 ✓); `single_mode_ok=true`,
  `n_secondary_violations=0` (✓); σ 66.41/70.71/70.92 ps ∈ [10,500] (✓);
  derived offsets −50/+50/+50 with Δ=0 vs recorded (one-bin AGREE exact, not
  merely within one bin). Consumed offset is the DERIVED value
  (`offset_ps == offset_ps_derived`; recorded prior lives only in
  `offset_ps_prior_recorded`/`prior_bin_index`, never input) — verified per JSON.
- **(b) Span-continuity**: spans 2.999999575767/2.9999998748439998/2.999999749626 s
  (>0 ✓); |span − mtime-gap| = 0.0224/0.0257/0.0362 s ≤ 0.5 s (✓).
- **(c) Both-or-neither**: all three trios complete (JSON+npz+npy present);
  code path (`save_sparse_nab` → reload round-trip + checksum →
  p_b shape/normalization gate → `trio_complete`, else `remove_trio`) inspected
  and sound; no partial trio exists.
- **(d) K_B sanity**: 1024 < 2395/2439/2597, within [1,1024] (✓ ×3).
- **(e) 2M consistency**: recomputed per-plane ΔH (−0.000631756793718817 /
  −0.000523191583527316) and p_b L_inf (0.00019661427905427232) against the
  frozen sidecars myself — all reproduce the recorded values exactly and sit
  15–50× below the materiality bars (|ΔH|>0.01, L_inf>1e-3) ⇒ **no finding**,
  correctly recorded. ΔN = 29589.0 reported with the EXPECTED-vintage note and
  explicitly NOT treated as a discrepancy (✓ per packet §2.7).
- **(f) Determinism vs A1**: all 12 fields exact on all three sources
  (n_pairs_N, n_frames, 3 split counts, 3 split ranges byte-identical to the A1
  manifest, derived offset, peak bin, duration). Mismatch would have STOP-BLOCKED;
  nothing did.

## 3. Design points — PASS (recomputed from full-precision H_corr only)

All `f`/`N_req`/`m_max`/content values in the per-source JSONs,
`corrected_design_points.json`, and `.csv` reproduce my independent recompute
(`content=1024·H`, `f(m)=(5m+64)/content`, `m_max=⌊(1.3·1024·H−64)/5⌋` cap 208,
`N_req=⌈3·4.785675/(1.3−f)⌉`, inf iff f≥1.3) bit-for-bit. Thresholds
0.829326923076923/0.7992788461538461/0.7955228365384616 and slope 4.785675
confirmed frozen-correct. `delta_vs_baseline_S3.md`: every ΔH/Δcontent/Δf/ΔN_req
row reproduces (1M ΔH=−0.0023389196758668573; 1.5M −0.0016714841284448667;
2M −0.0012518869160380586; full Δ table verified cell-by-cell against the
defective-basis full-precision values). CSV renders null `N_req` as `inf` (✓).
Measured outcomes: 1M `m_max` **201→200 CONFIRMED** (the predicted conditional
flip, now on measured K_B); 1.5M `m_max` stays 207; 2M raw 209→cap 208 unchanged.

## 4. Certifiability on corrected counts (recomputed by this review)

Key-eligible 200/276/364; zero-failure still required everywhere:

| source | m=208 | m=200 | m=199 | m_max |
|---|---|---|---|---|
| T2-1M (elig 200) | f=1.34552190, N=inf → **NO** | f=1.29677111, N=4447>200 → **NO** | f=1.29067726, N=1541>200 → **NO** | 200, N=4447 → NO |
| T2-1.5M (elig 276) | f=1.30320049, N=inf → **NO** | f=1.25598308, N=327>276 → **NO** | f=1.25008091, N=288>276 → **NO** | 207, N=5315 → NO |
| T2-2M (elig 364) | f=1.29375096, N=2298>364 → **NOT certifiable on count** | f=1.24687592, N=271≤364 → **YES-on-count** | f=1.24101654, N=244≤364 → **YES-on-count** | capped 208, N=2298 → NO |

Key movements vs defective basis, all confirmed: (i) the 1.5M m=199
"YES-by-2-blocks PROVISIONAL" (274≤276) **FLIPS to NO** (288>276); 1.5M m=200
(327>276) stays NO; (ii) 2M m=200/199 remain YES-on-count while m=208 is NOT
certifiable on count — f-margin (IN, f=1.29375) and N-count (2298>364) are
distinct verdicts and the artifacts keep them distinct (see F3); (iii) 1M all NO;
(iv) 1.5M@208: nominal f=1.30320049>1.3 (N=inf) BUT the threshold-H gap
(−0.0020367202999194145) vs CI halfwidth (0.002214902496712412) gives ratio
**0.92** — nominally OUT on arithmetic, statistically within-CI:
**INDETERMINATE-vs-OUT**, a main-thread judgment the artifacts correctly decline
to make (delta doc: "Statistical INDETERMINATE status is a main-thread
judgment; the movement rows below are arithmetic only").

## 5. Budgets — PASS

Trio wall 531.1 s ≤ 5400 (✓); per-dataset 115.7/169.1/246.3 s ≤ 1800 each (✓);
per-read 0.34/0.42/0.45 s ≤ 300 (✓); peak RSS 710224 KiB = 0.68 GiB < 4 GiB (✓).
One base-member read per dataset (single `FileReader` + single frozen
`read_ttbin_events`; no `.1` open — `parse_bases` rejects it, shard path used
for mtime-stat only). No retry/resume/repair: all three records `OK`, no
INCOMPLETE/BLOCKED rows, `run_stdout.log` shows a straight 1M→1.5M→2M pass.

## 6. Prohibitions — PASS

`git diff -- src/` EMPTY (re-verified at review time; `p3_census_a1.py`
unmodified — R1 reuses it BY IMPORT). `results/` 0 files/0 B and
`comparison_bench/outputs_comparison/` 1446 files/554423395 B — byte-identical
to the P3-A1-REVIEW item-10 snapshot recorded in PRE_EXECUTE Q3 (✓).
Module grep: `decoder/DE/graph` occur only in a NEVER-substitute comment and a
telemetry label — **zero calls**; zero hits for `longrun_`/`minrerun_`/`routeA_`/
`run_e2e_pipeline`/retry/resume. All writes land under the fresh root (A1 and
gamma reads are read-only `json`/`np.load`); no excluded-artifact reads
(`channel_counts` etc. never opened). Test file is fake-only (docstring-declared;
no ttbin/decoder/TimeTagger content). No commit/push performed (HEAD still
5a7041e4, worktree uncommitted as expected).

## 7. Claim ceiling — PASS

Root-wide grep: the ONLY FER/SKR/route/qualification/publication statement is
the negative ceiling in `R1_RESULT.md` ("…ONLY — no FER/SKR/route/qualification/
publication claim (packet §6). Corrected points do NOT authorize X1 by
themselves") (✓). `H_corr` is presented as TRAIN-side with the derived §3A
alignment on every per-source row (`split_side` TRAIN wording + derived-offset
fields) (✓). Per-source status labels, no pooling (zero `pool` hits),
`undetected` N/A with zero hits and no merging (✓ per §5.5).

## 8. Two carried items — adjudicated

- **(i) split_manifest mtime**: final mtime (20:50:13) postdates the 1M/1.5M
  trios because the executor rewrites the manifest incrementally per dataset —
  EXPECTED from the code. Packet §2.4 (manifest-first) is satisfied BY
  CONSTRUCTION: `run_dataset` writes `split_manifest.json` (L619–621) BEFORE
  the determinism check, histogram, estimator, and bootstrap. See F1 for the
  one documentation inaccuracy this creates.
- **(ii) Bootstrap CI entirely below the point on all three** (CI_hi 0.80033/
  0.82686/0.83303 vs H_corr 0.80127/0.82729/0.83333): verified as recorded;
  halfwidths (0.002851/0.002215/0.001947) sit far below the 0.02 support bar
  (✓); NO artifact reads CI_hi as an upper bound on H (no upper-bound/bracket
  language anywhere — see F2). Bootstrap semantic matches the packet §2.5
  standard reading (per-replicate `H_plug + own (K_AB−K_B)/(2N ln2)`, seed
  20260921, 200 resamples; code L681–708 inspected).

## 9. Pre-EXECUTE adequacy — PASS

Q0–Q6 all recorded with ACTUAL verbatim outputs (branch 5a7041e4 on
`formal-ir-v72p1-addendum-clean`, alias smoke OK, absence proofs, protected-root
snapshots matching item-10, `git diff -- src/` empty, **31 fake-only tests
passed** (13+11+7, operator-reconciled verbatim), Q6 adjacency to launch, dry
header-only control read with channels 1/5 present on all three). Apparent
discrepancies are all reconciled in-record (HEAD vs stale brief expectation;
13/11/7 vs 13/18+7 aggregation; census 12 vs 11 files = the documented F-1
`DESIGN_POINT_ARITHMETIC.md` closure). Q-notes carry the authorization-of-record
quote, the F1 trio-retention decision, the F2 frozen command (matches the
packet template with frozen trio order/seeds/budgets/span-tol), and the
bootstrap semantic (✓).

## Findings table

| # | severity | finding |
|---|---|---|
| F1 | non-blocking (docs accuracy) | `PRE_EXECUTE.md` root-creation note claims `split_manifest.json` is preserved as "the FIRST machine artifact **by mtime**" — FALSE on final mtimes (manifest 20:50:13 postdates the 1M/1.5M trios by incremental rewrite). The packet §2.4 requirement itself (manifest written before any statistic) HOLDS by code construction (§8(i)). Further, the "poll log evidencing the ~20:43 first write" does not exist in `PRE_EXECUTE.md` — ordering evidence is code inspection, not a runtime log. Recommend a one-line correction to the note at main-thread acceptance; no re-run, no gate impact. |
| F2 | non-blocking (observation) | Bootstrap CI sits entirely below the point estimate on all three sources (same duplicate-support pattern as A1 F-2). Halfwidths are healthy (≪0.02 bar) and no artifact misreads CI_hi as an upper bound — verified. Recommend the main thread confirm the frame-weighted bootstrap semantic matches A1 before citing CI widths comparatively; not a blocker for design-point correction. |
| F3 | non-blocking (wording) | `delta_vs_baseline_S3.md` "mechanical @200 … IN-on-count" / "mechanical @208 … OUT" rows are f-arithmetic only (f vs 1.3), NOT N-count certifiability vs key-eligible counts. The doc's own disclaimer covers this, but the "on-count" suffix invites misreading f-margin as N-certifiability (esp. 2M@208: f-IN yet N=2298>364 NOT certifiable). Recommend reading §4 of this review as authoritative for certifiability; consider a parenthetical "(f-arithmetic only)" at acceptance. |
| F4 | administrative (expected) | §7/§8 signature blocks BLANK by design; authorization of record is the verbatim chat grant quoted in the prereg amendment note and PRE_EXECUTE Q-note (i). Frozen scientific inputs, gates, thresholds, seeds, budgets, stop rules all verified UNCHANGED — nil scientific impact (P3-A1-REVIEW F-3 precedent applies directly). **Requires administrative ratification after this review** (see §6, item 4). |
| F5 | non-blocking (procedure) | `PRE_EXECUTE.md` was staged at `/tmp` pre-launch and materialized into the root post-launch (mtime 20:52:48, after execution) because the CLI refuses pre-existing roots. Content is verbatim pre-launch evidence with Q6 adjacency; procedure is documented in-record. Accept as-is; note for future cycles that the staging workaround makes root mtimes postdate execution. |

## Checklist

- [x] Matches OpenSpec spec — packet §§1–8 followed; frozen trio params, §3A procedure/gates, TRAIN-only scope, estimator definition, bootstrap requirement, both-or-neither, determinism, 2M report-only rule all honored; no frozen-input change
- [x] Tests pass — 31 fake-only (13 R1 + 11 align + 7 stage05) recorded verbatim at Pre-EXECUTE; no production invocation in tests
- [x] No scope creep — histogram + bundle + design-point scope only; no X1 arms, no decoder/DE/graph, no `src/` change, no protected-root writes, no excluded reads
- [x] docs/decision-log.md or docs/troubleshooting.md needs update? — **yes, candidates below** (main-thread decision; not blocking)

## What the main thread must decide before accepting

1. **Baseline §3 amendment**: record the corrected values (§§3–4 of this review: H_corr 0.8012690084416184/0.8272902027770036/0.8333327179427281; m_max 200/207/209→cap-208; f/N_req rows; certifiability table) as superseding the defective-MM-basis §3 table, keeping the defective values as labeled history. Suggested verdict language: 1M OUT@208/all-NO; 1.5M OUT-nominal@208 with INDETERMINATE-vs-OUT statistical status (gap/halfwidth 0.92), m=200/199 NO (provisional-YES withdrawn); 2M IN@208 on f-margin but NOT count-certifiable there (N=2298>364), YES-on-count at m=200/199 (zero-failure still required).
2. **P-V1 MM-estimand closure**: R1 measures K_B=1024 and closes the estimator defect with the exact conditional correction — recommend closing P-V1 for these three sources on acceptance (defective-basis §3 values marked UNVERIFIED→CORRECTED).
3. **X1 close-out**: the bundle inputs (sparse `N_ab_train` + `p_b_train` ×3, checksums verified) satisfy the materialization requirement — recommend closing the X1 entry-blocker item while noting X1 still needs its OWN entry gate (fresh Pre-EXECUTE + explicit grant) before any arm runs.
4. **Administrative ratification of the chat-grant deviation** (F4): ratify the §7 execution grant + §8 F-3/tolerance ratifications as given by chat-grant within the frozen contract (THIS-cycle-only mode; not a standing workflow change).
5. **Memory triage candidates** (for `/sync-memory`): corrected H/design-point table; K_B=1024 measured + 1M m_max flip + 1.5M provisional-YES withdrawal; bootstrap-below-point pattern (F2); manifest-mtime procedure note (F1/F5); "mechanical IN-on-count" ≠ N-certifiability gloss (F3).
6. **Optional one-line touch-ups at acceptance** (F1/F3 wording); no re-run required for any of them.
