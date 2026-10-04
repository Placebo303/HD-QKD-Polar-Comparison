# CHAN-QUALITY-SURVEY — PREREG_AND_AUTH (DECIDE, frozen, NOT GRANTED) — Rev 2, 2026-09-27

- **Track**: **DECIDE** (real data; opens raw `.ttbin` for the first time on four datasets — `AGENTS.md` §1.2 matrix: "Real-data development/validation → DECIDE, full DECIDE gate contract"). Calling a zero-decode reader does not by itself force DECIDE; the real-data + route-informing combination does.
- **Tranche**: `formal-ir-v72p1-addendum-clean`.
- **Status**: **FROZEN — NOT GRANTED**. This freeze authorizes nothing. Nothing may run without the full DECIDE chain (accepted preregistration → Pre-EXECUTE → one execution + result record → independent Pre-RESULT → main-thread acceptance; `AGENTS.md` §10.3). Compact three-document form applies: this file + `RESULT.md` + `INDEPENDENT_ACCEPTANCE.md`, plus machine artifacts.
- **Acceptance ID**: `G-CQ-SURVEY`. Operator reports stable IDs `CQ-01`…`CQ-11` (§13), never restates the spec.
- **Revision**: **Rev 2, 2026-09-27**. Rev 1 (2026-09-27, earlier same day) is preserved below as the record of what was believed; dated `SUPERSESSION NOTE 2026-09-27` blocks correct it in place. Nothing was silently deleted. The grant block (§16) remains BLANK.

> **REVISION NOTE 2026-09-27 (global, read first).** Rev 1 faithfully recorded two claims main supplied that main has since re-read from the artifacts and found **false**: (A) that the 1.20-Type0 groups had "no correlation peak" / alignment "never established" with a geometry search required; (B) that acquisition parameters are "not recoverable from the header (Stage 0.5 negative)" without qualification. The true picture comes from `e2e_alignment_audit.csv` in each 1.20-Type0 dataset directory (121 rows = 11 dimensions × 11 bin widths per group) and from a read-only header pass over all 10 small base `.ttbin` files: alignment succeeded everywhere (`realign_ok=1` on all 121 rows), a correlation peak was located (`peak_status=from_global_peak` on 39 rows), 11 grid points PASSED including the repository's own frozen geometry (`dimension=1024, bin_width_ps=200`: `map_ser=0.098260`, `peak_status=from_global_peak`, `sidecar_verdict=PASS`, blank `fail_reason` against the old 0.1 threshold), and the header yields the channel plan plus coincidence window while correctly not containing offset or framing. Details, per-section corrections, and the reason for each original error are in §2 (new facts F-o/F-p/F-q), §4 (supersession), §6, §17, and §18. **Arm A is therefore re-scoped from a seven-group survey with geometry search to four Type0 groups at the frozen geometry with a header-validated pair and a data-derived offset — no grid scan.** The legacy `0.098260` is recorded as a falsifiable **expectation** under a different pipeline/pairing, never as a result (§2 F-q, §11).

---

## §0 Goal / Non-Goals / Impact Scope (planner output requirements)

- **Goal**: establish an **outcome-independent** channel-quality axis over the four never-opened 1.20-Type0 acquisition groups (Arm A, zero-decode, frozen geometry `1024 × 200 ps`, header-validated `1↔5` pair, per-group correlation-derived offset), and test whether the bit-plane error structure measured at SER ~0.077 (10 dB) survives at SER ~0.24–0.25 on the Jan-21 M0 eval region (Arm B, zero-decode). The two arms jointly decide **where a workable operating point might exist** and **whether the layered-favouring structure survives at current noise** — nothing more.
- **Non-Goals**: no correction measurement anywhere (no FER, efficiency, leakage, f, SKR); no method comparison; no selection of a "best" group as a favourable subset; no claim that any method works; no decoder/construction/DE/b2f work; no geometry fitting beyond the frozen derivation (§6); no publication number; no commit/push by the operator.
- **Impact Scope**: read-only on four raw dataset locations under `/mnt/d/Data/Raw Data/2026.1.20/` + the Jan-21 trio (read-only); read-only reuse of `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v25_gate.py` (`m0_metrics`, `build_N_ab`, `modular_delta_hist_ab`), `comparison_bench/src/comparison_bench/cli/p3_census_a1.py` (`h_full_f03`), `comparison_bench/src/comparison_bench/cli/m0_realframe_runner.py` (`load_real_series`, `superframes`), `comparison_bench/src/comparison_bench/io/align_wrapper.py`; one small ADDITIVE runner + one fake-only test (new files only); one fresh additive output root. `src/`, `experiments/`, `tools/`, `results/`, `comparison_bench/outputs_comparison/`, every existing `workspace/` root: read-only or untouched.
- **Acceptance Criteria**: §13 (`CQ-01`…`CQ-11`) — all must PASS at the independent batch-end review, else no promotion of any batch evidence.
- **Tasks**: §15 (ordered, concrete; implementation-only code tasks need no track gate; execution tasks need the §14 grant).

> **SUPERSESSION NOTE 2026-09-27 (§0).** Rev 1 Goal/Impact read "seven never-opened acquisition groups". That scope is superseded: Arm A executes **four** groups (CQ-20a–d); CQ-12 and CQ-13a/b are retained non-execution with reasons (§5). What was wrong: the seven-group scope assumed all groups needed a geometry search with nothing known; re-read of `e2e_alignment_audit.csv` plus the header pass now fixes geometry, pair, and peak existence for the Type0 groups, while the SHG groups remain unassessed and the 1.12 group remains quarantined. Original seven-group wording above is preserved via this note as the record of what was believed.

**Size note for orchestrator**: the code delta is small enough to implement directly — one additive runner (~200 lines, pure arithmetic + frozen loader calls) plus one fake-only test modelled on `test_m0_realframe_fake.py`. No full pipeline is needed for the code. Execution still needs the §14 grant. No `/opsx-explore` is needed: every primitive already exists (§2).

---

## §1 What the two arms jointly decide, and what they do not

**They jointly decide**:
1. (Arm A) an outcome-independent quality ordering of the four Type0 candidate groups from channel statistics alone (SER, ±1-bin mass, plane structure, time stability, conditional entropies) at the single frozen geometry — the axis by which any *later* choice of an "easier" group must be justified, so that choice cannot be circular;
2. (Arm B) whether `expected_planes_flipped_per_error` is still 1.0 and whether the MSB→LSB plane ladder keeps its shape at SER ~0.24–0.25 — i.e. whether the error structure that favours a layered approach survives at the current noise level.

**They explicitly do not decide**: whether any correction method works anywhere (neither arm runs a decoder); any FER/efficiency/leakage/f/SKR value; any method ranking; any operating point; any route-closing, qualification, or publication claim. A "better channel" reading is a hypothesis for later DECIDE work, never a conclusion of this batch.

**Legitimate negative outcome (pre-registered)**: all four Type0 groups may turn out no better than Jan-21 under our own frozen chain. That outcome means the "easy first" strategy has no purchase in this data. It is recorded as a legitimate finding — not a failure, not a trigger for re-tuning, re-reading, or re-selection. A mismatch between the legacy `0.098260` expectation and the frozen-chain measurement is likewise legitimate and informative (§2 F-q).

> **SUPERSESSION NOTE 2026-09-27 (§1).** Rev 1 "Legitimate negative outcome" read "all seven groups". Superseded to four executed groups; the other three groups are non-execution with reasons (§5), not silent drops. Reason for the error: same seven-group assumption corrected in §0.

---

## §2 Established facts relied on (with source file for each)

| # | Fact | Source |
|---|---|---|
| F-a | M0 Jan-21 eval-region symbol error means: 244.29/1024 (1M), 260.44/1024 (1p5M) per-superframe `raw_symbol_errors` means; 2M mean 259.85/1024 per tasking (≡ 23.9–25.4% SER on the u2/low-5-bit component; equality of raw and u2 counts rests on the u1-zero premise below) | `docs/research_cycles/M0-REALFRAME/RESULT.md` §2.1–§2.3 + `workspace/m0_359922a7_1M/`, `workspace/m0_642a8fe8_1p5M/`, `workspace/m0_b1a9142d_2M/` (`rows.json`) |
| F-b | Any "binary-equivalent QBER 0.26" gloss is invalid: NOT COMPARABLE verdict; the 0.26 is TRAIN-region entropy-equivalence `h(p)=0.8326`, not a measured QBER | `docs/research_cycles/V80-NBLDPC-JAN21/LITERATURE_DIRECTION_MEMO_20260921.md:13` (NOT COMPARABLE) + `:43` (gloss, "not a measured QBER") — note §16(b): the root-level path cited in tasking does not exist; this corrected path is authoritative |
| F-c | u1 (coarse 6.4 ns group) carries zero symbol-level error; its information enters IR only as a marginalized prior; no upstream defect, no cheaper operating point inside the Jan-21 trio; success/failure overlap completely in per-superframe error count (no easy subset) | Tasking premises (no single repo file re-verified in recon; Arm B's report-only full-10 column re-observes the u1 path without gating on it). M0 full-10 vs u2 gap (`RESULT.md` §2: fails_full10 132/145/139 vs u2 fails 20/22/10) is *model-recovery* mismatch, not a raw-u1 channel error — no contradiction |
| F-d | Per-plane/difference-magnitude statistics need **no code modification**: `m0_metrics(a, b, *, time_blocks=6)` (`:272–323`) returns `ser`, `modular_delta_frac_top`, `pm1_mass`, `direction_asymmetry_plus_minus1`, `abs_signed_delta_quantiles`, `gray_mask_popcount_frac`, `bit_plane_co_error_matrix` (10×10), `time_block_stability` in one pure-arithmetic call on `(a,b)` — no decoder, no source loader. Primitives `modular_delta_hist_ab` (`:254–257`), `build_N_ab` (`:113–117`) | `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v25_gate.py:113–117,254–257,272–323` |
| F-e | `nonbinary_v13_diagnostics.channel_aggregates` (`:974–1085`) is **NOT used** by this batch: its default frame length is `n=N=256` (`:62` `Q,N,M = 1024,256,170`) and `_frame_channel_stats` asserts `a.shape == (n,)` (`:938–944`) — a caller forgetting `n=1024` silently mis-frames. The batch uses `m0_metrics` + `h_full_f03` only, sidestepping the trap | `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v13_diagnostics.py:62,938–944,974–1085` |
| F-f | M0 real loader produces the required input: `load_real_series(source)` returns `a`/`b` plus provenance (`:173–175`: superset `{a, b, dataset, ttbin, offset_ps, n_pairs_total, n_pairs_eval, eval_first_frame, read_wall_s}`); `superframes(a, b, 1024)` (`:178–181`) chunks 1024-symbol superframes. Geometry constants `:86–88` (`BIN_WIDTH_PS=200`, `FRAME_BINS=1024`, `CH_A,CH_B=1,5`); frame grid `:153–156`; 1M offset −50 asserted equal to R1 (`:144–145`, `:154`); pair-count/split asserted equal to R1 (`:159–160`, `:164–171`) | `comparison_bench/src/comparison_bench/cli/m0_realframe_runner.py:60–61,86–88,144–160,164–181,226–234` |
| F-g | 10 dB plane structure measured on real data: `sum_plane_rates == raw_ser` bitwise ⇒ `expected_planes_flipped_per_error = 1.0` exactly; frozen ladder `V17_PLANE_ER` (`:328–332`) monotone MSB→LSB, LSB ≈ 49% of SER (sum = 0.07707 ⇒ SER 0.077, ~3× cleaner than Jan-21; LSB 0.0375061/0.07707 = 48.7%). Whether it holds at SER ~0.25 is unmeasured — that is Arm B | `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v25_gate.py:328–332` (+ tasking premise for the bitwise equality) |
| F-h | Dataset inventory: `docs/DATA_INVENTORY_20260921.md` §1 tabulates **20 `.ttbin` = 10 base + 10 `.1`** across 10 locations in 4 date roots; no `.ttbin` in this repo ever opened for any group but the Jan-21 Type2 trio; §4: small/base file meaning NOT established (header-only vs first chunk) — never assumed | `docs/DATA_INVENTORY_20260921.md:§1,§4` — **partly superseded 2026-09-27**: the small-base meaning is now established as a `SITT`-blocked header (see F-p); the "never assumed" discipline stands |
| F-i | Pair members are NESTED/SUPERSET via vendor auto-follow, NOT disjoint: legal access = open base `X.ttbin` only (auto-follow covers `.1`); NEVER open both / NEVER concatenate (doubling). Base→`.1` mtime gap ≈ 3 s everywhere except 1.12 (≈ 30 s) | `docs/TTBIN_MEMBER_SEMANTICS_20260921.md:§C,§D` |
| F-j | Jan-12 duration tag is WRONG: measured span 29.9999524 s vs `3s` tag; quarantined (`duration_measured_s=30.0`, `filename_tag_disputed=true`); must never be pooled with 3 s acquisitions without explicit declaration. Config status per family: B = repo-resident V80 convention; A = repo-resident but WRONG convention (`d=256`, `bw=20`, `sync`, `1click_each` — `run_golden_sweep_four_datasets.py:142–146`); C/D = **no repo-resident config**. `d`/framing under fitting is IMPOSED-NOT-MEASURED | `docs/research_cycles/V80-NBLDPC-JAN21/P3_CENSUS_PACKET.md:§2 table,§4.2` + `docs/research_cycles/V80-NBLDPC-JAN21/P3_STAGE05_PACKET.md:20` (JAN12 KNOWN-DISPUTED) — **partly superseded 2026-09-27** by F-p/F-q: header now yields channel plan + coin window; `d`/framing remain an imposed analysis convention (correctly, not a gap) |
| F-k | `h_full_f03` (`:94–128`, anchor `:66` `ANCHOR_H_FULL = 0.83256272`) computes H(U1\|B), H(U2\|U1,B), H(A\|B) from census joint counts `N_ab`; `build_N_ab` is the shared primitive. R1-corrected per-source own-H anchors at `x1_arm_runner.py:158–162` | `comparison_bench/src/comparison_bench/cli/p3_census_a1.py:66,94–128` + `comparison_bench/src/comparison_bench/cli/x1_arm_runner.py:158–162` |
| F-l | Frozen alignment gates: histogram call `bin_width_ps=100/max_lag_ps=819200` (16384 bins), `peak_to_bg ≥ 100`, single-mode rule, crude sigma 10–500 ps; FAIL ⇒ STOP-BLOCKED, never 0/borrowed/recorded (`require_alignment_passed`) | `comparison_bench/src/comparison_bench/io/align_wrapper.py:40–49,213–228` |
| F-m | Measured read costs (budget basis, §9): R1 `read_wall_s` 0.34/0.42/0.45 s (1M/1.5M/2M), `dataset_wall_s` 115.7/169.1/246.3 s; M0 provenance `read_wall_s` 0.40/0.68/0.73 s; R1 trio wall 531.1 s; P3 `PER_DATASET_CEILING_S = 1800.0` | `workspace/r1_histogram_5e2a91c4/T2-{1M,1.5M,2M}.json` + `workspace/r1_histogram_5e2a91c4/R1_RESULT.md` + `docs/research_cycles/M0-REALFRAME/RESULT.md` §2 + `comparison_bench/src/comparison_bench/cli/p3_census_a1.py:72` |
| F-n | `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816/*/pairs.parquet` is a different pairing rule (`legacy_v1` vs M0 `_pair_nearest_unique`), different slice (512,000 rows/source vs M0 time-ordered last ~40%), under a protected path — explicitly out of scope (mentioned here only to forbid it) | `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v25_gate.py:65–81` (SOURCES table context) |
| F-o | **(Added 2026-09-27 — corrects the Rev 1 "no peak" record.)** Re-read of `e2e_alignment_audit.csv` in each 1.20-Type0 dataset directory (121 rows = 11 dimensions × 11 bin widths per group): `realign_ok=1` on **all 121** rows (alignment succeeded everywhere, not "never established"); `can_run_polar=1` on all 121 (Rev 1 tasking misread this column's value `1` as the string `FAIL`, conflating it with the separate `sidecar_verdict` column); `peak_status=from_global_peak` on **39** rows, `not_requested` on 82 (a correlation peak **was** located); `corr_nonzero=0` and `corr_bins=0` on all 121 are **unpopulated columns, not measured-zero** — this was the specific error (an unpopulated column read as a measurement); `fail_reason=map_ser>=0.1` on 110 rows and **blank on 11** (11 grid points PASSED). Decisively at the frozen geometry `dimension=1024, bin_width_ps=200`: `map_ser=0.098260`, `peak_status=from_global_peak`, `sidecar_verdict=PASS`, blank `fail_reason` (passes the old 0.1 threshold). Bin width dominates at d=1024: ser 0.482791 (bw=20), 0.333044 (50), 0.182724 (100), 0.123612 (150), **0.098260 (200)** — monotone improving; rows d=256/512/1024/2048/4096 at bw=200 all report the identical 0.098260 (dimension-independent value) | Main-supplied re-read 2026-09-27 of `e2e_alignment_audit.csv` per 1.20-Type0 group directory (planner did not open dataset files; values recorded here as the authority for the re-scope) |
| F-p | **(Added 2026-09-27 — partly supersedes the Rev 1 "not recoverable from header (Stage 0.5 negative)" record.)** Read-only header pass over all 10 small base `.ttbin` files: each is a `SITT`-blocked header carrying a TimeTagger JSON config at bytes `@64 .. 64+u32@52`, verified on all 10. It yields the **channel plan** for all groups (FileWriter channels ⊇ {1,5} with a Coincidences group `[1,5]`), reproducing the frozen Jan-21 pairing exactly, and the Coincidences `window` = 200 ps matches the frozen `COIN_WINDOW_PS`. It does **not** contain the pairing offset: the three Jan-21 headers are byte-identical while R1 derived `-50 / +50 / +50` from the data, which **proves** the offset cannot be header-resident. It also does not contain frame period, bin width, frame bins, duration, or pump type — and that is correct rather than a gap, because the `1024 × 200 ps` framing is an analysis convention, not an acquisition parameter | Main-supplied header reconnaissance 2026-09-27 (planner did not open any `.ttbin`; recorded here as the authority; Stage 0.5 `getConfiguration()` negative on pm/eb keys is retained but no longer cited as "nothing recoverable") |
| F-q | **(Added 2026-09-27 — falsifiable EXPECTATION, not a result.)** The legacy-`v1`-pairing candidate value at the frozen geometry is `ser=0.098260` for the 1M group (F-o). The comparison target is Jan-21's frozen-chain measured 23.9–25.4% (F-a). Arm A exists to determine whether the Type0 groups really sit near 10% **under our own frozen chain** — because the legacy number came from a different pairing rule (`legacy_v1` versus `_pair_nearest_unique`), a different pipeline, and with `cond_A_missing_a_or_b=1` on every row. A mismatch between the legacy value and the frozen-chain value is a legitimate and informative outcome; a confirmed ~10% is also not by itself evidence that any method corrects well (§11) | Expectation synthesised 2026-09-27 from F-a + F-o + F-n pairing-rule distinction; binds §3, §11, §13 |

---

## §3 Frozen arms

### Arm A — Type0 zero-decode channel survey at the frozen geometry (runs FIRST)

For each of the **four** executed groups (CQ-20a–d, §4 revised scope): open **only** the base `X.ttbin` (vendor auto-follow covers `.1`; F-i), at the **frozen geometry `dimension=1024`, `bin_width_ps=200`, `frame_bins=1024`** (F-o PASS point; F-p convention note), using the **header-validated `1↔5` channel pair** (F-p), with the **per-group pairing offset derived by correlation auto-alignment from the data under the repository's frozen A1/R1 pairing chain — never guessed, never taken from the header** (F-p proves the header cannot supply it), and report **per group**:

1. `total_pairs`, `clean_pairs` (post-`keep` count + framing remainder), `ser` (u2/low-5-bit symbol error rate);
2. `pm1_mass` (+1/−1 200 ps-bin mass) + absolute signed-delta quantiles (q50/90/95/99/100);
3. `gray_mask_popcount_frac` (0–10) and `expected_planes_flipped_per_error` = (Σ plane rates)/SER;
4. 10×10 `bit_plane_co_error_matrix`;
5. `time_block_stability` (6 blocks: per-block `pm1` + `ser`);
6. H(U1|B) / H(U2|U1,B) / H(A|B) via `h_full_f03(build_N_ab(a, b))` — same `N_ab`, plug-in only, **no bootstrap** (deterministic; §9 rationale), support `K` + occupancy persisted alongside (bias diagnostic, never a correction);
7. provenance row: base path, `duration_measured_s`, `filename_duration_tag`, `tag_disputed`, `alignment_mode` (DERIVED for offset / HEADER-VALIDATED for pair / IMPOSED-CONVENTION for framing per §4), channels `1↔5` + header-validation flag, `offset_ps_derived`, `peak_bin_index`, `peak_to_bg`, `sigma_crude_ps`, `align_status`, framing actually used + `IMPOSED-CONVENTION` flag + `ser_expectation_legacy_v1=0.098260 (EXPECTATION ONLY, §2 F-q)`.

**No grid scan is needed any more: geometry is known (F-o PASS at the frozen point), the peak is known to exist (F-o 39 `from_global_peak` rows), and the channel pair is header-validated (F-p).** The frozen `align_wrapper` gates (F-l) still apply per group: any alignment FAIL ⇒ STOP-BLOCKED for that group (record, continue batch; never 0/borrowed/recorded offset).

Purpose: an **outcome-independent** channel-quality axis (channel statistics only, §7), so any later "easier group" choice cannot be circular.

> **SUPERSESSION NOTE 2026-09-27 (§3).** Rev 1 Arm A read "for each executed group (§4 table, six groups after the §5 exclusion)" with geometry derive-or-REFUSE and an implicit search. That is superseded by the four-group frozen-geometry scope above. What was wrong: Rev 1 assumed no peak, no channel plan, and no known geometry (see §4 note); F-o/F-p now fix all three for the Type0 groups. Original six-group derive-or-REFUSE wording is preserved via this note and §4 as the record of what was believed.

### Arm B — plane structure on the Jan-21 M0 eval region (runs SECOND, only if Arm A completes)

Apply the **identical** §3A metrics to the Jan-21 Type2 trio over the M0 VAL+HOLD eval superframes (same `load_real_series` provenance: same base member, same derived offset asserted equal to R1, same pair count, same 60/20/20 boundaries; F-f). Report the same fields 1–7 per source plus the verdict line: is `expected_planes_flipped_per_error` still 1.0, and does the MSB→LSB ladder keep its shape at SER ~0.24–0.25? Reuses M0's exact frozen pairing/geometry — no re-derivation, no substitution. **Arm B is unchanged by Rev 2.**

---

## §4 Frozen per-group table (geometry verified, never assumed)

> **SUPERSESSION NOTE 2026-09-27 (§4 — the central correction, read before the table).** What was wrong: Rev 1 recorded, on main's assertion, that the 1.20-Type0 groups had "no correlation peak in zero of 121 grid points each" and that acquisition parameters are "not recoverable from the header (Stage 0.5 negative)". Both claims are **false**. Why it was wrong: (i) the `can_run_polar=1` column value `1` was misread as the string `FAIL` by conflation with the separate `sidecar_verdict` column; (ii) the unpopulated columns `corr_nonzero`/`corr_bins` (= 0 everywhere because that pipeline never populates them) were read as measured-zero; the populated columns in fact show `realign_ok=1` on all 121 rows, `peak_status=from_global_peak` on 39 rows, and 11 blank-`fail_reason` PASS points including the frozen `1024 × 200` point at `0.098260` (F-o). (iii) The header pass cited as "Stage 0.5 negative" is superseded by the `SITT`-blocked TimeTagger-JSON finding that yields the channel plan and coin window on all 10 files while correctly not containing offset or framing (F-p). What is now established: geometry is known, the peak is known to exist, the pair is header-validated, and only the per-group offset must still be derived from the data. **The Rev 1 table below is preserved verbatim as the record of what was believed; the "REVISED frozen Arm A scope" block after it is the sole authority for execution.**

Conventions frozen for every executed group: open base `X.ttbin` ONLY (F-i); channels from derivation, never assumed; `bin_width_ps=200`, `frame_bins=1024`, `align="global"`, `postselect="keep_all"` are **IMPOSED-NOT-MEASURED** (P3 §4.2) and labelled as such in every row; `d=1024` imposed. Any cell marked REFUSE stops that group with a retained record (§10).

| gid | location (base member) | `.1` size (MiB) | tags (filename-level only) | authoritative record in repo? | frozen treatment |
|---|---|---|---|---|---|
| CQ-12 | `/mnt/d/Data/Raw Data/2026.1.12/Type2PPLN_3s_2026-01-12_165236.ttbin` | 16.126 | no rate tag; `3s` **DISPUTED** (measured 30 s, F-j); flat layout (no subfolder) | none | **EXCLUDED from execution** — see §5 |
| CQ-13a | `/mnt/d/Data/Raw Data/2026.1.13/SHG_Type2PPLN_3s_2026-01-13_162106/SHG_Type2PPLN_3s_2026-01-13_162106.ttbin` | 56.581 | SHG source; no rate tag; `3s` | none (family C: no repo-resident config, F-j) | derive-or-REFUSE (§6) |
| CQ-13b | `/mnt/d/Data/Raw Data/2026.1.13/SHG_Type2PPLN_3s_2_2026-01-13_162148/SHG_Type2PPLN_3s_2_2026-01-13_162148.ttbin` | 57.328 | SHG source, 2nd run (~42 s apart); no rate tag; `3s` | none | derive-or-REFUSE (§6) |
| CQ-20a | `/mnt/d/Data/Raw Data/2026.1.20/Type0_nofilter_500K_3s_2026-01-20_193050/Type0_nofilter_500K_3s_2026-01-20_193050.ttbin` | 12.627 | `nofilter`; 500K; `3s` | wrong-convention only (F-j); derived trees excluded | derive-or-REFUSE; MUST NOT reuse the `d=256/bw20/sync/1click_each` convention (§6) |
| CQ-20b | `/mnt/d/Data/Raw Data/2026.1.20/Type0_nofilter_1M_3s_2026-01-20_192857/Type0_nofilter_1M_3s_2026-01-20_192857.ttbin` | 22.207 | `nofilter`; 1M; `3s` | wrong-convention only | derive-or-REFUSE |
| CQ-20c | `/mnt/d/Data/Raw Data/2026.1.20/Type0_nofilter_1_5M_3s_2026-01-20_193255/Type0_nofilter_1_5M_3s_2026-01-20_193255.ttbin` | 31.919 | `nofilter`; 1_5M; `3s` | wrong-convention only | derive-or-REFUSE |
| CQ-20d | `/mnt/d/Data/Raw Data/2026.1.20/Type0_nofilter_2M_3s_2026-01-20_193411/Type0_nofilter_2M_3s_2026-01-20_193411.ttbin` | 45.700 | `nofilter`; 2M; `3s` | wrong-convention only | derive-or-REFUSE |
| CQ-J21a/b/c (Arm B) | Jan-21 trio bases (`Type2_1M…184040`, `Type2_1-5M…183806`, `Type2_2M…183657`) | 21.005/29.577/39.834 | Type2 rate ladder; `3s` (span-verified 3.0 s) | **exists**: R1 JSONs + `split_manifest.json` + M0 provenance (F-f) | reuse exact frozen values; assert equality or STOP |

Size ordering 12.6/22.2/31.9/45.7 MiB consistent with Type0 rate tags is filename-level evidence only (inventory §1) — never a gate input.

**Places with no authoritative geometry record (packet therefore REFUSEs rather than proceeds)** — per executed group (CQ-13a/b, CQ-20a–d): (i) no recorded `offset_ps` (trio −50/+50 never transferable); (ii) no recorded channel plan — and the SHG-A anomaly (config `registered channels=[1,5,9,13,17]` vs stream `[1001,1,5]`, P3_CENSUS_PACKET §11) means the plan must come from measurement, never config; (iii) no recorded `bin_width_ps`/`frame_bins` for that source (Type0's only resident values are the wrong `d=256` convention); (iv) PM/EB unrecoverable from header (Stage 0.5 negative: `getConfiguration()` dict, 20 keys, zero pm/eb keys); (v) small-file meaning NOT established (F-h) — the runner opens the base member and asserts span-continuity (span > 0 and consistent with `.1`−base mtime gap within tolerance), never both members. Any of (i)–(v) unresolved ⇒ REFUSE that group (§10), retained record, batch continues to the next group.

> **SUPERSESSION NOTE 2026-09-27 (§4 list (i)–(v) — point-by-point).** Preserved above as the record of what was believed; each item is superseded for the Type0 groups as follows: (i) offset — still correctly header-absent (F-p proof by Jan-21 byte-identical headers vs three distinct R1 offsets), but the peak is known to exist (F-o) so the offset is **derived per group by correlation auto-alignment from the data**, never a search over geometries; (ii) channel plan — **superseded**: header-validated `1↔5` on all groups (F-p); the SHG-A anomaly note is retained only for the now-out-of-scope SHG groups; (iii) bin width / frame bins — **superseded**: frozen `1024 × 200 ps` is the F-o PASS point, retained as an imposed analysis convention (F-p) rather than an acquisition parameter, labelled `IMPOSED-CONVENTION`; (iv) PM/EB-from-header — **partly superseded**: Stage 0.5 negative on pm/eb keys stands, but the blanket "not recoverable" is withdrawn — the header does yield channel plan + 200 ps coin window (F-p); (v) small-file meaning — **superseded**: small base is a `SITT`-blocked header (F-p); the span-continuity assertion and never-open-both rule (F-i) stand.

**REVISED frozen Arm A scope (sole authority for execution, 2026-09-27).** Arm A executes exactly the four 1.20-Type0 groups `500K` (CQ-20a), `1M` (CQ-20b), `1_5M` (CQ-20c), `2M` (CQ-20d), at the frozen geometry `dimension = 1024`, `bin_width_ps = 200`, `frame_bins = 1024`, using the header-validated `1↔5` channel pair, with the per-group pairing offset **derived by correlation auto-alignment from the data** under the repository's frozen A1/R1 pairing chain — never guessed, never taken from the header. **No grid scan is needed any more: geometry is known (F-o), the peak is known to exist (F-o), and the channel pair is header-validated (F-p).** The Type0 `d=256/bw20/sync/1click_each` convention remains forbidden as input. CQ-12, CQ-13a, CQ-13b are retained non-execution with reasons (§5), not executed groups.

---

## §5 Excluded and deferred groups: CQ-12, CQ-13a, CQ-13b (retained non-execution)

### §5.1 The 2026.1.12 decision: EXCLUDED (with reason) — RETAINED

**Decision: CQ-12 is EXCLUDED from execution.** The survey executes four groups (CQ-20a–d); CQ-12 gets a retained non-execution record stating the reason. Justification:

1. Its `3s` filename tag is **measured-wrong** (29.9999524 s span; F-j) and it is quarantined from pooling with 3 s acquisitions — executing it under the same imposed framing/duration would confound the very quality axis Arm A must keep clean;
2. No rate tag, flat date-root layout (only location without a per-dataset subfolder), anomalous 30 s base→`.1` mtime gap, earliest-session protocol with JTI/histogram sidecars — a different acquisition regime, not a comparable ladder rung;
3. A duration-normalized comparison would be new scientific scope (rate/symbol definitions change with span) and is not pre-registered here.

Including it as a "named risk" was considered and rejected: the quarantine rule (F-j) is explicit, and fail-closed discipline requires exclusion over risk-carrying when the confound touches the primary axis. Re-admission requires its own packet with duration-normalized metrics.

### §5.2 The two 2026.1.13-SHG groups: DEFERRED to a successor packet (with reason) — ADDED 2026-09-27

**Decision: CQ-13a and CQ-13b are DEFERRED — retained non-execution in this batch, never executed here.** Rev 1 had them as derive-or-REFUSE execution groups; that treatment is superseded. Justification:

1. Never assessed in this repository (family C: no repo-resident config, F-j) — unlike the Type0 groups they have no `e2e_alignment_audit.csv` PASS point and no header-validated-geometry finding distinguishing them; executing them now would reintroduce the geometry-search scope Rev 2 removes;
2. The stated `cw` pump implies a multi-pair regime whose expected noise is *higher*, not lower — so they are not candidates for an easier operating point and do not serve the "easy first" purpose that motivates Arm A;
3. Deferral preserves fail-closed discipline: a successor packet may assess them with their own preregistration rather than stretching this batch back to a seven-group survey.

Each gets a retained non-execution record (`CQ-13a_NON_EXECUTION.json`, `CQ-13b_NON_EXECUTION.json`) stating this reason. Re-admission requires its own packet.

> **SUPERSESSION NOTE 2026-09-27 (§5).** Rev 1 §5 excluded only CQ-12 and executed six groups. That six-group scope is superseded: the executed set is four groups; CQ-13a/b move from execution to deferred non-execution per §5.2, and CQ-12 exclusion stands on its existing grounds (reaffirmed in §5.1). Original §5 text is preserved above as the record of what was believed.

---

## §6 Zero-decoder + geometry fail-closed rules (machine-verifiable)

1. **Zero decoders.** No LDPC, cascade, layered-binary, DE, b2f, `m2real_runner`, `m3c_real_u2`, PEG construction, QSPA, or telemetry-hook call. The executing script's allowed scientific imports are exactly: `numpy`; `src.qkd_io.ttbin_pipeline` (`read_ttbin_events`, `_pair_nearest_unique`, `_frame_global`, `compute_cross_correlation_histogram`); `comparison_bench…io.align_wrapper` (`derive_alignment`, `require_alignment_passed`); `comparison_bench…formal_ir.nonbinary_v25_gate` (`m0_metrics`, `build_N_ab`, `modular_delta_hist_ab`, `gray_label`); `comparison_bench…cli.p3_census_a1` (`h_full_f03`). Machine verification at Pre-EXECUTE: `rg` over the runner for forbidden tokens (`decode`, `ldpc`, `cascade`, `peg_construct`, `qspa`, `m2real_runner`, `m3c_real_u2`, `construct_standalone`, `bind_empirical_bundle`, `run_diagnostic_hook`) returns zero hits, AND the runner asserts at startup that none of those module names appears in `sys.modules` — any hit ⇒ REFUSE before the first read.
2. **Geometry (REVISED 2026-09-27 — replaces the Rev 1 derive-or-REFUSE search):** channel pair is **header-validated `1↔5`** (F-p) for all four Type0 groups; framing `1024 × 200 ps` is the **frozen imposed analysis convention** at the F-o PASS point (labelled `IMPOSED-CONVENTION` in every row); the per-group channel offset is **DERIVED via the frozen `align_wrapper` gates (F-l) on the base-member stream** (correlation auto-alignment under the frozen A1/R1 pairing chain). Any alignment FAIL ⇒ STOP-BLOCKED for that group (record, continue batch; never 0/borrowed/recorded offset, never widened bins, never a geometry scan). The Type0 `d=256` convention is forbidden as input. Span-continuity assertion (F-i) gates every group before pairing. No grid scan, no guessed offset, no header-taken offset (the header provably lacks it, F-p).
3. Arm B reuses the Jan-21 frozen values with equality assertions (F-f); any mismatch ⇒ STOP (whole arm, return to main thread — the headline-data geometry is not negotiable).

> **SUPERSESSION NOTE 2026-09-27 (§6.2).** Rev 1 §6.2 required per-group derivation of channel plan + offset with REFUSE branches over six groups. Preserved in §6.1 (unchanged) and the §4 record above; the operative rule for the four Type0 groups is the revised §6.2 in this section. What was wrong is the same §4 error: plan and geometry are now known (F-o/F-p); only the offset remains derived.

---

## §7 Outcome-independence rule (restated precisely 2026-09-27)

No group may be selected for later decoding on the basis of its **correction** result — because **no correction outcome is produced or consulted in this batch** (there is no decoder to consult). The rule forbids selecting a group by its correction result and **explicitly permits and requires** selection by a **channel-quality** statistic measured without decoding: that is the entire purpose of the quality axis (§3A fields 1–7), and a group chosen because its decoded FER is low would be circular. The batch records no ranking, no "best group", no design point, no `m`. Any later use of the axis must cite the Arm A summary version; re-sorting groups by a future decode result is a new decision requiring its own packet.

> **SUPERSESSION NOTE 2026-09-27 (§7).** Rev 1 stated the rule correctly but tersely ("No group may be selected for later decoding on the basis of its correction outcome"). The restatement above is more precise and supersedes it as the binding wording, so a later reader cannot misread the rule as forbidding quality-based selection altogether. Original Rev 1 paragraph is superseded in wording only, not in substance — preserved here as the record: *"No group may be selected for later decoding on the basis of its correction outcome — because no correction outcome is produced or consulted in this batch (there is no decoder to consult)."*.

---

## §8 No-overwrite / roots

- Single fresh additive root `workspace/cq_<uuid8>` (uuid fixed at Pre-EXECUTE; absence proven). All batch outputs land there and only there.
- Read-only: the four Type0 raw locations (§4 revised scope) + Jan-21 trio; `src/`, `experiments/`, `tools/` (Pre-EXECUTE proves `git diff --stat -- src/ experiments/ tools/` empty).
- Forbidden to write: `results/`, `comparison_bench/outputs_comparison/`, every existing `workspace/` root (incl. `workspace/m0_*`, `workspace/r1_histogram_5e2a91c4`, `workspace/x1_bundles_7c1d4a2b`, `workspace/formal_ir_phase6b_tests/`, `workspace/chan_header_recon_20260927/`). `-p no:cacheprovider` for any pytest contact (`AGENTS.md` §10.1.9).

> **SUPERSESSION NOTE 2026-09-27 (§8).** Rev 1 read "all seven raw locations". Superseded to four Type0 locations + Jan-21 trio; the three non-executed locations are never opened. `workspace/chan_header_recon_20260927/` is added to the forbidden-to-write list (another agent's root; planner never wrote there).

---

## §9 Budget (frozen ceilings — REVISED 2026-09-27)

One CPU; threads pinned to 1 (`OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`, `MKL_NUM_THREADS=1`, `NUMEXPR_NUM_THREADS=1`; numpy-only arithmetic, no BLAS-threaded decoder to pin). Sequential groups, **one process per group, one group at a time** (per-group process count = 1; no parallel reads).

| item | ceiling | basis / assumption |
|---|---|---|
| Arm A per-group wall | **1800 s** | P3 `PER_DATASET_CEILING_S` precedent (F-m); ~7× the worst measured R1 per-dataset wall (246.3 s) and three orders above measured reads (0.34–0.73 s). Assumes pair/frame/metric cost scales ~linearly with events. Type0 `.1` members are at most **45.700 MiB** (2M; smallest 12.627 MiB) — smaller than the SHG members (57.3 MiB) the same ceiling previously covered — so reads stay < 2 s and the statistics are O(pairs). Four group reads, sequential, one CPU, threads pinned to 1. **No bootstrap** is run (plug-in + K/occupancy only) — stated assumption keeping the batch deterministic and cheap. If scaling breaks the assumption, the ceiling—not the method—absorbs it (INCOMPLETE, never tuned) |
| Arm A batch wall | **7200 s** (4 × 1800) | arithmetic over the four executed groups; the three non-executed slots consume near-zero cost (retained records only) |
| Arm B per-source wall | **600 s** | **UNCHANGED**: eval region is 40% of pairs; same loader already timed (reads < 1 s; pair/frame tens of seconds in R1/M0); metrics-only, no bootstrap |
| Arm B batch wall | **1800 s** (3 × 600) | **UNCHANGED**: arithmetic |
| Whole-batch wall | **9000 s** | 7200 + 1800; breach ⇒ INCOMPLETE, retained, never continued |
| Peak RSS | **< 4 GiB** (per process) | M0/R1/P3 precedent (F-f/F-m); loader materialises event arrays; breach ⇒ FAIL(budget-rss), stop that group, retained |

> **SUPERSESSION NOTE 2026-09-27 (§9).** Rev 1 budgeted 7 × 1800 = 12600 s (Arm A) / 14400 s whole-batch for six executed groups plus the CQ-12 slot. Superseded by 4 × 1800 = 7200 s / 9000 s whole-batch. Per-group ceiling (1800 s), RSS, CPU/threading, and both Arm B ceilings are unchanged. Ceiling basis is now stated from the §4 `.1` sizes (max 45.700 MiB) plus the F-m read/wall precedents.

No repair+rerun is pre-registered (DECIDE): any rerun = new packet + new authorization + new root.

---

## §10 Stop rules (any one ⇒ stop that group; Arm B mismatches ⇒ stop the arm)

Input base absent; span-continuity failure (span ≤ 0 or inconsistent with `.1`−base mtime gap); alignment-gate FAIL on the per-group offset derivation (frozen geometry + validated pair assumed per §6.2 — never widened, never scanned); unresolved label dispute (any executed group showing `tag_disputed=true` ⇒ record + REFUSE pairing for it); pairing/offset not matching the authoritative record (Arm B); any decoder/construction import (machine gate, §6.1); budget breach; output-root collision (root exists); any write attempt inside a protected root; any attempt to select a group by correction outcome. Wall-partial ⇒ `INCOMPLETE`, retained, never continued. A REFUSED/INCOMPLETE group never blocks the remaining groups (Arm A); Arm B runs only if Arm A completes (all four executed groups terminal with records).

> **SUPERSESSION NOTE 2026-09-27 (§10).** Rev 1 stop rules referenced "unverifiable geometry (no unique channel-plan argmax; alignment gate FAIL)" over six groups. Superseded for Arm A by the frozen-geometry rule above: the plan is validated and the geometry fixed, so only the offset derivation can REFUSE. Substance (fail-closed, retained, never-borrowed) is unchanged.

---

## §11 Claim ceiling (verbatim — binds the batch, the review, and any citation)

> These are channel characterization measurements only. This batch establishes NO FER, NO efficiency, NO leakage, NO f, and NO SKR statement; NO method comparison; NO selection of a "best" group as a favourable subset; and NO claim that any method works anywhere. Arm A measures channel characterization only, with zero correction. A lower symbol error rate does not imply that any method corrects. The legacy `0.098260` value is an expectation under a different pipeline and pairing rule (F-q, F-n), never a result, and must not be carried forward as one. No Type0 group may be presented as representative of the experiment's operating conditions. Any later "works on easier data" claim requires its own packet and must report the quality axis alongside, never the favourable subset alone. The Arm A quality axis exists precisely so that a later favourable-subset claim cannot be circular: no group may be promoted on these numbers without a new packet, a new authorization, and an uncertainty statement the present batch does not provide.

> **SUPERSESSION NOTE 2026-09-27 (§11).** Rev 1 ceiling is preserved as the first three sentences above and remains binding; Rev 2 **tightens** it with the additional sentences (zero-correction restatement, no SER→correction inference, legacy-value isolation, no representativeness, later-packet reporting rule). Rev 1 verbatim record: *"These are channel characterization measurements only. This batch establishes NO FER, NO efficiency, NO leakage, NO f, and NO SKR statement; NO method comparison; NO selection of a "best" group as a favourable subset; and NO claim that any method works anywhere. The Arm A quality axis exists precisely so that a later favourable-subset claim cannot be circular: no group may be promoted on these numbers without a new packet, a new authorization, and an uncertainty statement the present batch does not provide."*

---

## §12 Deliverables (no new decoder or method)

Per executed group (four): `<gid>.json` (frozen schema: provenance row + §3A fields 1–7 + `expected_planes_flipped_per_error` + `N_ab` support/occupancy + wall/RSS + status; provenance carries `IMPOSED-CONVENTION` framing flag + `HEADER-VALIDATED` pair flag + `DERIVED` offset + `ser_expectation_legacy_v1` labelled EXPECTATION ONLY). Plus three retained non-execution records: `CQ-12_NON_EXECUTION.json` (exclusion, §5.1), `CQ-13a_NON_EXECUTION.json` + `CQ-13b_NON_EXECUTION.json` (deferral, §5.2). Per arm: one short Markdown summary (`ARM_A_SUMMARY.md`, `ARM_B_SUMMARY.md` — tables only, no ranking sentence beyond sorting by SER with the §11 ceiling restated). One append-only `EXECUTION_LOG.md` (attempts, machine-gate results, retained failures, final evidence). Then `RESULT.md` (operator) and `INDEPENDENT_ACCEPTANCE.md` (independent Pre-RESULT, §13-gated). Machine-verifiable property (§6.1) is re-checked by the reviewer from the artifacts.

> **SUPERSESSION NOTE 2026-09-27 (§12).** Rev 1 required six per-group JSONs + one `CQ-12_NON_EXECUTION.json`. Superseded by four per-group JSONs + three non-execution records. Schema gains the §3A.7 provenance flags; nothing else changes.

---

## §13 Acceptance items (stable IDs — existing IDs kept, new IDs added, never renumbered)

| ID | Item | Verify against |
|---|---|---|
| CQ-01 | Zero decoders: runner `rg` + `sys.modules` scan clean; no decode-shaped output exists | runner source + log + Pre-EXECUTE proof |
| CQ-02 | Geometry fail-closed: every executed group has a passing alignment record or a retained REFUSE; CQ-12 exclusion record present with §5 reason; no assumed offset/channel anywhere | per-group JSONs + log |
| CQ-03 | Outcome-independence: no correction outcome consulted (none exists); no group selected/ranked as "best"; §11 restated in both summaries | summaries + RESULT |
| CQ-04 | Metrics completeness: all §3A fields 1–7 + `expected_planes_flipped_per_error` present per executed group, all from the shared `N_ab`/`(a,b)` (no second counting basis) | per-group JSONs |
| CQ-05 | Arm B fidelity: Jan-21 frozen pairing/geometry reused with equality assertions; `expected_planes_flipped_per_error == 1.0?` answered per source with the ladder comparison | Arm B JSONs + summary |
| CQ-06 | No-overwrite: fresh root only; `results/`, `outputs_comparison/`, existing `workspace/` untouched; raw data read-only; `git diff --stat -- src/ experiments/ tools/` empty | filesystem + git state |
| CQ-07 | Budget: per-group/batch walls, RSS < 4 GiB, 1 CPU / threads-1 / 1 process per group, sequential | log + resource lines |
| CQ-08 | Deliverables + review: §12 files complete; claim ceiling (§11) respected verbatim; independent batch-end review PASS (FAIL ⇒ no promotion, rework, re-review) | review document |
| CQ-09 | **(Added 2026-09-27)** Frozen-geometry compliance: all four Type0 groups run at `1024 × 200 ps` with header-validated `1↔5`, per-group correlation-derived offset under the frozen A1/R1 chain; no grid scan, no guessed offset, no header-taken offset; provenance flags (`IMPOSED-CONVENTION` / `HEADER-VALIDATED` / `DERIVED`) present | per-group JSONs + log |
| CQ-10 | **(Added 2026-09-27)** Legacy-value isolation: `0.098260` appears only as `ser_expectation_legacy_v1` labelled EXPECTATION with the F-q/F-n caveats (different pairing rule, different pipeline, `cond_A_missing_a_or_b=1`); never carried as a measured result; no SER→correction inference anywhere | per-group JSONs + summaries + RESULT |
| CQ-11 | **(Added 2026-09-27)** Out-of-scope retention: `CQ-12_NON_EXECUTION.json`, `CQ-13a_NON_EXECUTION.json`, `CQ-13b_NON_EXECUTION.json` present with the §5.1/§5.2 reasons; none of the three opened for data | non-execution records + log + Pre-EXECUTE proof |

CQ-02 note: "no assumed offset/channel" is read under Rev 2 as "no guessed/borrowed offset, no assumed pair" — the pair is header-validated (F-p) and the framing is the labelled imposed convention (§6.2); CQ-09 is the precise check.

---

## §14 Pre-EXECUTE checklist (main measures in one session before granting)

| # | Check | How |
|---|---|---|
| P-1 | Branch / HEAD re-measured | `git branch --show-current`, `git rev-parse HEAD` recorded |
| P-2 | Scoped cleanliness | `git diff --stat -- src/ experiments/ tools/` empty; new files = runner + fake test + this packet only (scoped manifest) |
| P-3 | Focused tests (decision below, UNCHANGED) | **exact command**: `.venv/bin/python -m pytest comparison_bench/tests/test_chan_quality_survey_fake.py -p no:cacheprovider` — must be **all-pass** on a fresh additive `workspace/cq__pytest_<uuid8>` root. **Why a new test is required**: this batch adds a small runner whose new logic (frozen-geometry + validated-pair plumbing, per-group offset REFUSE branch, CQ-12/CQ-13a/b non-execution paths, decoder-import `sys.modules` gate, root refusal, shared-`N_ab` plumbing) is covered by no existing test. **What the fake injects** (no `.ttbin`, no TimeTagger, no real data): synthetic `(a,b)` arrays with hand-computable `ser`/`pm1`/Gray-popcount/`H` values; a fake `series_fn` + fake geometry table (frozen-geometry passing groups, one failing-alignment group, the three non-execution paths); asserts `m0_metrics`/`h_full_f03`/`build_N_ab` values, REFUSE on failed offset derivation, non-execution without read, root-refusal, and the import-gate trip on a planted fake decoder module |
| P-4 | Zero-decoder proof | `rg` forbidden-token scan of the runner (zero hits) + test-evidence of the `sys.modules` gate |
| P-5 | Inputs present (names/sizes ONLY — never opened) | `ls -la` the four Type0 base members (§4 revised scope) + Jan-21 trio bases; sizes match §4 within tolerance; the three non-executed locations are listed for absence-of-contact only |
| P-6 | Output absence | `workspace/cq_<uuid8>` does not exist; `results/` and `comparison_bench/outputs_comparison/` state recorded (no writes there) |
| P-7 | Exact commands frozen | Arm A command + Arm B command with root uuid, `PYTHONPATH=<repo-root>`, thread-pin env, `--execute-real --execution-authorized` dual flags (refuse without both, M0 precedent `m0_realframe_runner.py:387–389`) |
| P-8 | Budgets restated | §9 ceilings + stop rules read back verbatim (Rev 2: 4 × 1800 / 9000 s whole-batch) |
| P-9 | **(Added 2026-09-27)** Untouched roots + member discipline | Prove the four Type0 group roots and the Jan-21 roots are untouched (mtime/size listing only, no content open); prove no `.1.ttbin` is opened beyond what the loader legitimately streams (runner opens base `X.ttbin` only per F-i; `rg` the runner for `.1` open/concatenate patterns returns zero hits) |

> **SUPERSESSION NOTE 2026-09-27 (§14).** P-1/P-2/P-4/P-6/P-7 unchanged. P-3 keeps the originally decided focused-test item (same exact command, same fake-only discipline) with its geometry-table description updated for the narrowed scope. P-5 narrows "seven base members" to four + trio. P-8 restates the revised ceilings. P-9 is new and does not renumber existing items.

---

## §15 Tasks (ordered, for coder agents; implementation-only = no track gate)

1. **T-CQ1** — Implement the additive survey runner (new file only, e.g. `comparison_bench/src/comparison_bench/cli/cq_channel_survey.py`): frozen loader + `align_wrapper` + `m0_metrics`/`build_N_ab`/`h_full_f03` calls at the §6.2 frozen geometry with the header-validated pair and per-group derived offset; §6 gates (incl. `sys.modules` decoder scan + dual-flag refusal + fresh-root refusal + base-only open per F-i); per-group JSON writer (frozen §12 schema with Rev 2 provenance flags); `main() -> int` + `if __name__ == "__main__"` house style (P3/M0 precedent). No `src/` touch. *(Rev 2: narrowed from six-group derive-or-REFUSE to four-group frozen-geometry; §5 non-execution paths for three groups.)*
2. **T-CQ2** — Implement `comparison_bench/tests/test_chan_quality_survey_fake.py` per §14 P-3 (fake-only; `-p no:cacheprovider`; fresh `workspace/cq__pytest_<uuid8>` roots; zero scientific/real-data contact). *(Rev 2: fake geometry table covers frozen-geometry pass + offset-REFUSE + three non-execution paths.)*
3. **T-CQ3** — Pre-EXECUTE measurement (§14 P-1…P-9) by main; fill the grant block (§16) only on PASS.
4. **T-CQ4** — Execute Arm A (single command, sequential four groups), then Arm B iff Arm A completes (all four groups terminal); operator writes `EXECUTION_LOG.md` + per-group JSONs + non-execution records + arm summaries + `RESULT.md`. *(Rev 2: four groups, §9 ceilings.)*
5. **T-CQ5** — Independent batch-end review → `INDEPENDENT_ACCEPTANCE.md` against CQ-01…CQ-11; FAIL ⇒ rework + re-review, never publish-then-patch.

---

## §16 Authorization block (BLANK — authorization is outstanding)

- Grant verbatim: *(empty — no grant has been given)*
- Date / granter: *(empty)*
- Budget confirmation: *(empty)*

Record (verbatim): **authorization is outstanding — the user has not yet granted this batch, and this packet confers no authority to execute, read real data, or write any output. Authorization for the revised Arm A is outstanding. Main's reading is that the user's two statements of 2026-09-27 — 「两个都可以按顺序或者同步做」 and, after main reported the narrowed scope, 「可以」 — together constitute the grant, with that reading flagged for main to confirm or correct.**

---

## §17 Out-of-scope / boundary notes

1. `…/v13r3fresh_pairs_20260816/*/pairs.parquet`: explicitly out of scope (F-n) — different pairing rule, different slice, protected path. No fallback to it on any REFUSE. **Rev 2 adds: the legacy `0.098260` value associated with that rule/pipeline is an expectation (F-q), never a substitute result.**
2. `workspace/formal_ir_phase6b_tests/*/20dB_capture*.ttbin` fixtures are unrelated test fixtures and out of scope (pattern-matched; 24 files observed 2026-09-27 — see §18(a); count never a gate).
3. SHG `pie_skr_scan*` / `.opju`, Type0 `e2e_new_ttbin_fullgrid_*`, Jan-21 `results*`/`run_config*.json`, JTI/histogram/CSV sidecars: names only, excluded, never read for content (inventory §1). **Rev 2 adds: `e2e_alignment_audit.csv` per Type0 group directory is cited via the main-supplied F-o re-read only (planner opened no dataset file); the `e2e_new_ttbin_fullgrid_*` directories themselves are never entered for content.**
4. H estimators are plug-in only (`h_full_f03` verbatim); Miller–Madow is NOT computed (no `K_B` persistence question is opened); no bootstrap, no CI — promotion is forbidden (§11), so no uncertainty machinery is needed.
5. Track note: implementation-only work (T-CQ1/T-CQ2) needs no track gate per the §1.2 matrix; the **execution** (T-CQ4) is DECIDE and needs the §16 grant. Documentation-only review scales proportionally.
6. **(Added 2026-09-27)** `workspace/chan_header_recon_20260927/` is another agent's root: never written, never depended on as an execution input; the header facts relied on here are the main-supplied F-p values, not that directory's contents (planner did not open it).

---

## §18 Recon contradictions / corrections (read-only findings, no data opened)

- (a) Tasking states "ten `workspace/formal_ir_phase6b_tests/*/20dB_capture*.ttbin` files"; filesystem shows **24 files (12 base + 12 `.1`)** on 2026-09-27. Packet uses the **pattern**, never the count.
- (b) Tasking cites `LITERATURE_DIRECTION_MEMO_20260921.md:13` at docs root; that path does not exist. Authoritative path is `docs/research_cycles/V80-NBLDPC-JAN21/LITERATURE_DIRECTION_MEMO_20260921.md:13` (+`:43` for the not-a-QBER gloss).
- (c) No contradiction in code citations: `m0_metrics` `:272–323`, `modular_delta_hist_ab` `:254–257`, `build_N_ab` `:113–117`, `V17_PLANE_ER` `:328–332`, `h_full_f03` `:94–128` + anchor `:66`, `H_CORR` `x1_arm_runner.py:158–162`, M0 geometry/pairing/provenance lines — all verified as cited. `load_real_series` returns a **superset** (`:173–175`), not exactly `{a,b}` — stated in F-f.
- (d) Current `docs/NOW.md` (2026-09-27) carries no 1.12 disputed-label note; the standing disputed/quarantine record lives in `P3_STAGE05_PACKET.md:20`, `P3_CENSUS_PACKET.md:§2`, and `TTBIN_MEMBER_SEMANTICS_20260921.md:§D` (F-j). Packet cites those.
- (e) No blocker encountered in recon: all reads were names/sizes/code/docs; no `.ttbin` opened, no command run, nothing written outside this file.
- (f) **SUPERSESSION 2026-09-27 — the "no peak / 121 grid points" record is withdrawn.** Rev 1 §§4/18 recorded main's assertion that the 1.20-Type0 groups had no correlation peak in zero of 121 grid points each with alignment never established. Re-read of `e2e_alignment_audit.csv` (121 rows per group) establishes the opposite (F-o): `realign_ok=1` all 121, `can_run_polar=1` all 121, `from_global_peak` on 39, 11 blank-`fail_reason` PASS points including the frozen `1024 × 200 → 0.098260 PASS`. Root causes of the original error: misreading `can_run_polar=1` as `FAIL` by conflation with `sidecar_verdict`, and reading unpopulated `corr_nonzero`/`corr_bins` (= 0) as measured-zero. The "geometry search over seven groups" scope built on that error is superseded by §4 revised scope. No `.ttbin`, `pairs.parquet`, or channel bundle was opened to establish this; the authority is the main-supplied audit re-read recorded in F-o.
- (g) **SUPERSESSION 2026-09-27 — the "not recoverable from header (Stage 0.5 negative)" record is partly withdrawn.** Rev 1 §§4(iv)/F-h/F-j cited Stage 0.5 as establishing that nothing is recoverable from the header. The read-only header pass (F-p) establishes that the small base `.ttbin` is a `SITT`-blocked header with a TimeTagger JSON config at `@64 .. 64+u32@52` on all 10 files, yielding the channel plan (⊇ {1,5}, Coincidences `[1,5]`) and the 200 ps window, while proving the offset is not header-resident (byte-identical Jan-21 headers vs three distinct R1 offsets) and correctly omitting framing/pump (analysis convention, not acquisition parameters). Stage 0.5's pm/eb-key negative is retained; the blanket "not recoverable" is withdrawn. No `.ttbin` was opened by the planner; the authority is the main-supplied header finding recorded in F-p.
- (h) **Rev 2 recon method (2026-09-27):** planner `ls` of `/mnt/d/Data/Raw Data/2026.1.20/`, `/mnt/d/Data/Raw Data/2026.1.13/`, `/mnt/d/Data/Raw Data/2026.1.12/`, and the four Type0 group directories (names/sizes only; confirmed four group roots + `e2e_new_ttbin_fullgrid_*` subdirectories present, base + `.1` pairs present). No `.ttbin`, no `pairs.parquet`, no channel bundle, no CSV content opened; no command run beyond `ls`; nothing written outside this file; `docs/NOW.md`, `docs/decision-log.md`, OpenSpec, and `workspace/` untouched.

---

## Correction note 2026-09-27 — F-p Coincidences `window` generalisation (documentation error, no effect on any measured number)

F-p states a Coincidences `window` of 200 ps, generalising the Jan-21 value to all groups. That generalisation is **wrong**. The header reconnaissance actually reported **window 1000 for the 1.12 / 1.13-SHG / 1.20-Type0 groups, and window 200 only for the three Jan-21 files** — the window is per-group (machine evidence: `coincidence_window_raw: [1000]` in all four `CQ-20*.json` header records).

The 200 ps window actually used in analysis is `COIN_WINDOW_PS = 200` (`comparison_bench/src/comparison_bench/cli/m0_realframe_runner.py:86`), supplied by the repository's own pairing code, not by the header: the loader reads the raw single-detector event stream (`read_ttbin_events`) and pairs it itself (`_pair_nearest_unique(..., window_ps=COIN_WINDOW_PS, ...)`). The header's `Coincidences window` is a TimeTagger-side measurement parameter that does not gate, filter, truncate, or otherwise affect the event stream this repository reads — it is **irrelevant to this repository's measurements**, not merely evidence-only.

The Arm A operator recorded the discrepancy rather than gating on it, which was correct: fail-closed did not need to fire on it because the value is not an input to the analysis. The packet's generalisation was a documentation error with **no effect on any measured number** in this batch.

For the legacy-versus-frozen-chain discrepancy (`0.098260` vs the frozen-chain measurements), the cause is **not established** by this batch. The known differences, independently established, are the differing pairing rule (`legacy_v1` versus the frozen `_pair_nearest_unique`) and the older pipeline. The coincidence window is **not** among them.
