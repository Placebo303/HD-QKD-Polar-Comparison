# P3 Stage 0.5 — INDEPENDENT Pre-RESULT Review (Acceptance ID G-P3-STAGE05)

- Reviewer: `reviewer-go` (taste instance, `step-5-preview`). Independent thread, read-only except this file.
- Date: 2026-09-21. Track: **DECIDE**. Gate reviewed: **Pre-RESULT** (`AGENTS.md` §10.3), before main-thread acceptance.
- Contract of record (frozen, verified tracked + unmodified): `P3_STAGE05_PACKET.md` §§1–9, `P3_STAGE05_PREREG_AND_AUTH.md`, `docs/TTBIN_MEMBER_SEMANTICS_20260921.md` §§C–D.
- Evidence root verified: `workspace/p3_stage05_ee32030a/` — 14 files (10× `<id>.json`, `duration_table.md`, `config_notes.md`, `PRE_EXECUTE.md`, `RESULT_SUMMARY.md`).
- Method note: every gate was re-derived from the recorded JSON scalar fields and independently cross-checked against the live `.ttbin` base members (header accessors only, no event drain). Concurrent A1 census root (`workspace/p3_census_*`) was NOT touched, read, or reviewed.

## Overall verdict: **PASS_WITH_FINDINGS**

Stage 0.5's own evidence is complete, internally consistent, and independently confirmed against the raw files. All 10 datasets clear G1–G3 (and G4); every prohibition holds; config fidelity is byte-exact. The findings below are **non-blocking for Stage 0.5** but require main-thread awareness — chiefly the shared-worktree concurrency (Finding 9b).

## Admissibility statement

Stage 0.5 evidence **IS admissible to gate Stage 1 eligibility**: batch PASS (10/10 clear G1–G3; zero fallbacks, FAILs, INCOMPLETEs). Per packet §6 and RESULT_SUMMARY, this **authorizes nothing by itself** — main-thread acceptance plus a separate explicit Stage-1/census authorization remain required. The `FITTED → READ-FROM-FILE` recommendation is recorded as a recommendation only and is a main-thread decision.

## Numbered findings

| # | Item | Verdict | Evidence | Severity |
|---|---|---|---|---|
| 1 | Contract conformance | **PASS** | All 14 required artifacts present. All 20 §6 JSON keys present & non-empty in every `<id>.json` (`dataset_id, base_path, member_opened, fallback_used, config_type, config_verbatim, channel_list, last_marker, t_first_s, t_last_s, duration_measured_s, filename_duration_tag, tag_disputed, mtime_base, mtime_shard, mtime_gap_s, span_gap_agreement, pm_eb_evidence, gates_G1_G4, status`); additive `config_survey_keys` extra is allowed. `last_marker=""` is the correct verbatim value, not a gap. Shared `duration_table.md` + `config_notes.md` present with required columns. | none |
| 2 | Gate integrity (re-derived) | **PASS** | Re-derived from JSON, not prose. **G1**: `fallback_used=false` AND `member_opened==base_path` for all 10 ⇒ base-only open; both members never opened. **G2**: `duration_measured_s>0` all 10. **G3**: recomputed `mtime_gap = mtime_shard − mtime_base` and `span = t_last − t_first` match recorded values to full precision; every `|span − gap| ≤ 0.5 s` (max 0.0398 s; JAN12 0.0301 s — table below). **G4**: `config_type="dict"`, full parseable `config_verbatim`. | none |
| 3 | Duration rule | **PASS** | `duration_measured_s` = measured span `(t_last−t_first)/1e12` (module L291), never the tag. `filename_duration_tag="3s"`, `tag_disputed` recorded per dataset in JSON + table. JAN12: span 29.999952410392, `tag_disputed=true` (|29.9999−3.0|=26.9999>0.5) — consistent with semantics §D (30 s acquisition, stale `3s` tag). Others ≈2.9999990–2.9999999, `tag_disputed=false`. `FILENAME_DURATION_S=3.0` used only as the dispute reference, never as a recorded duration. | none |
| 4 | Prohibition conformance | **PASS** | Repo-wide grep for `counts_ab, N_ab, H_full, H_L1/L2, entropy, mutual, autocorrelation, histogram, drift, weights, pairing, pairs` → **zero computed values**; only hits are RESULT_SUMMARY negative claim-ceiling text and config_notes "correlation pairs" (the vendor Correlation measurement's channel-pair *config*, not a computed pair). No event/timestamp/channel **arrays** written: JSONs carry only `t_first_s`/`t_last_s` scalars; `channel_list` is the 3-element `getChannelList()` (metadata, §3.4 required). `config_verbatim` holds vendor measurement *definitions* (Coincidences/Counter/Countrate/Correlation with window/binwidth/n-values) dumped verbatim per §3.3 — not computed results. Module discards every `getData` array (`del data, ts`, L146). | none |
| 5 | Config survey fidelity | **PASS** | `config_notes.md` records present/absent per key class (channel roles/gates/markers, PM/EB, phase-matching, split/part) for all 10; nothing invented (empty category = absent). Independent read-only spot-check on **3 base members** (SHG-A, T2-2M, T0-500K) via alias shim, header accessors only (no drain): `config_verbatim` **byte-identical** (json sort_keys MATCH ×3), `config_type=dict` confirmed, `channel_list`+`last_marker` MATCH. | see 5b |
| 6 | PM/EB negative result | **PASS** | `pm_eb_evidence` (all 10): "pm_eb keys ABSENT … nothing established … UNPROVEN until the main thread judges … no inference beyond quoted keys." Independent full-text grep confirms **zero** pm/eb/phase/phase_matching/shh/basis/gate/marker config *keys*; the only `ppln`/`Type2PPLN` hits are inside `FileWriter.filename` provenance paths (`D:\SPDC源测试\…\Type2PPLN_…ttbin`) and dataset file paths — exactly as config_notes states. "Establishes nothing about PM/EB" is supported and **not** over-stated (defers to main thread). | none |
| 7 | SHG-A anomaly | **PASS** | Recorded verbatim in `SHG-A.json` (top-level `registered channels=[1,5,9,13,17]`, Countrate `channels=[1,5,9,13,17]`) vs `channel_list=[1001,1,5]`; flagged in config_notes L22 "(recorded as observed)". Independently confirmed against the live base file (spot-check returned `registered_channels=[1,5,9,13,17]`, `channel_list=[1001,1,5]`). Not silently smoothed. | none |
| 8 | Budget conformance | **PASS** | Module enforces ceilings by construction: per-read 300 s / global 1800 s → `INCOMPLETE`+stop (L210–211, 284–287, 370–372); `max_reads` base-then-shard-only (≤2, L75–96). Each dataset opened base only ⇒ 1 read. wall ~3 s (machine `time.monotonic`, L374) ≤1800; peak RSS 71220 KiB (~70 MiB, machine `getrusage`, L375) ≪ 4 GiB. 0 decoder/DE/graph calls (module has none — only comments). One infra incident (`/usr/bin/time` mis-invocation, exit 127 before any read) → clean rerun = the ≤1 preregistered engineering repair+rerun, failed attempt retained. | see 8b |
| 9 | Protected roots + frozen baseline | **PASS** | `results/` = **0 files / 0 B**; `comparison_bench/outputs_comparison/` = **1446 files / 554423395 B** (matches Q3 exactly). `git diff -- src/` **EMPTY**; `git status` clean for `src/`, `results/`, `outputs_comparison/`. Stage 0.5 frozen contract (packet + prereg) tracked + **unmodified**. | see 9b (governance) |
| 10 | Claim ceiling | **PASS** | Grep for `H_full, FER, SKR, secret.key, qualification, publication, operating.point, alignment, reconciliation.efficiency, beta_eff` → only the **negative** claim-ceiling statements in RESULT_SUMMARY ("Establishes NO `H_full` … NO FER/SKR/route/qualification/publication number"). No number asserted. The one forward-looking inference (config_notes L38–41: measurements supply a machine-readable channel plan → branch-B FITTED→READ-FROM-FILE candidate) is explicitly framed "RECOMMENDATION for main thread (decided there, not here)", which packet §6 permits. No violation found. | none |
| 11 | Pre-EXECUTE adequacy | **PASS** | Q0–Q5 record **actual** outputs (git values, file counts, `7 passed`, absence-check results), not bare assertions. Independently re-confirmed Q0 (branch `formal-ir-v72p1-addendum-clean`, HEAD `83cf848c`, `src/` clean), Q1 (alias shim resolves `FileReader` — used in my spot-check), Q3 (protected-root counts match), Q4 (test file is **FAKE-ONLY**: in-test fake `FileReader`, no `/mnt/d/Data` paths, no real `.ttbin` — satisfies §8 lesson 8). Q2/Q5 absence was pre-execution (root now exists with the expected 14 files). Off-by-one read-budget fix documented. | none |

### Gate re-derivation table (item 2/3)

| id | duration_measured_s | span=t_last−t_first ✓ | mtime_gap_s | gap=shard−base ✓ | \|span−gap\| | G3 (≤0.5) | fallback | G1–G4 |
|---|---|---|---|---|---|---|---|---|
| JAN12 | 29.999952410392 | ✓ | 30.030083894730 | ✓ | 0.0301 | PASS | false | TTTT |
| SHG-A | 2.999999582705 | ✓ | 3.039810657501 | ✓ | 0.0398 | PASS | false | TTTT |
| SHG-B | 2.999999520386 | ✓ | 3.035681724548 | ✓ | 0.0357 | PASS | false | TTTT |
| T0-500K | 2.999998993174 | ✓ | 3.039161443710 | ✓ | 0.0392 | PASS | false | TTTT |
| T0-1M | 2.999999916885 | ✓ | 3.029813289642 | ✓ | 0.0298 | PASS | false | TTTT |
| T0-1.5M | 2.999999647127 | ✓ | 3.035198688507 | ✓ | 0.0352 | PASS | false | TTTT |
| T0-2M | 2.999999433356 | ✓ | 3.032462120056 | ✓ | 0.0325 | PASS | false | TTTT |
| T2-1.5M | 2.999999874844 | ✓ | 3.025658845901 | ✓ | 0.0257 | PASS | false | TTTT |
| T2-1M | 2.999999575767 | ✓ | 3.022446393967 | ✓ | 0.0224 | PASS | false | TTTT |
| T2-2M | 2.999999749626 | ✓ | 3.036242485046 | ✓ | 0.0362 | PASS | false | TTTT |

### Config fidelity spot-check (item 5) — header accessors only, no drain

| id | config_type | config_verbatim | channel_list | last_marker | live registered_channels |
|---|---|---|---|---|---|
| SHG-A | dict ✓ | MATCH | MATCH [1001,1,5] | MATCH '' | [1,5,9,13,17] (anomaly confirmed real) |
| T2-2M | dict ✓ | MATCH | MATCH [1,5,1001] | MATCH '' | [1,5,9] |
| T0-500K | dict ✓ | MATCH | MATCH [1,5,1001] | MATCH '' | [1,5] |

## Findings requiring main-thread awareness (all non-blocking for Stage 0.5)

- **9b — Shared-worktree concurrency (governance; must not be conflated).** `git status` now shows changes beyond Stage 0.5 that belong to the concurrent A1 run (out of my review scope, root untouched by me): **untracked** `comparison_bench/src/comparison_bench/cli/p3_census_a1.py`, `comparison_bench/src/comparison_bench/io/align_wrapper.py`, `comparison_bench/tests/test_p3_census_a1_align.py`, `docs/CORRELATION_ALIGNMENT_CAPABILITY_20260921.md`; **modified tracked** `docs/research_cycles/V80-NBLDPC-JAN21/P3_CENSUS_PACKET.md`, `openspec/changes/v80-p3-real-hfull-census/{design.md, specs/…/spec.md, tasks.md}`. These do **not** touch `src/`, `results/`, or `outputs_comparison/`, and do **not** modify the Stage 0.5 contract. Stage 0.5's Pre-EXECUTE Q0 (three untracked: `.codebuddy/`, the probe module, its fake-only test; no tracked modifications) was valid **at Stage 0.5 launch time**. Stage 0.5 evidence is independently verified at the artifact level and stands on its own. **The A1 changes require their own DECIDE review and must not be accepted merely because Stage 0.5 passes.** Severity: informational for Stage 0.5; blocking-for-acceptance only for the A1 change set (not reviewed here).
- **5b — Survey-method phrasing.** `config_notes.md` L35 says "full-text case-insensitive search", but the module's `survey_config` (L170–181) matches **top-level** keys only. The *conclusion* (zero pm/eb/phase/ppln/shh keys) nonetheless holds under the stronger full-text grep I ran independently, so the claim is true — only the stated method is narrower than the wording. Severity: cosmetic.
- **8b — Budget numbers are not persisted as a machine artifact.** wall and peak RSS are computed by the module (L374–376) and printed to stdout / reported in RESULT_SUMMARY, but no separate timing/RSS log file exists in the root. Ceilings are enforced by the module (INCOMPLETE+stop on timeout) and observed wall ~3 s is far below 1800 s; RSS ~70 MiB ≪ 4 GiB. Severity: cosmetic (recommend persisting the `done: … wall_s=… peak_rss_kb=…` line to the root in future runs).
- **Prose vs artifact (not an evidence defect).** The operator's narrative summary in the review request under-reported the T2 Coincidences groups as `[[1,5],[1,5,9]]`; the machine artifacts (JSON + config_notes) correctly record **three** groups `[[1,5],[1,9],[1,5,9]]`, window 200 ps, virtuals `[1001,1002,1003]` — confirmed against the live T2-2M file. The evidence is correct; only the prose abbreviation was imprecise. Severity: cosmetic (do not transcribe from prose).

## Checklist

- [x] Matches OpenSpec/frozen spec (packet §§1–9; contract unmodified)
- [x] Tests pass (7/7 fake-only; file verified FAKE-ONLY, no real data / no production invocation)
- [x] No scope creep (probe stayed within base-member header accessors + bounded span; no forbidden computation)
- [x] Protected roots byte-identical; `src/` frozen (diff empty)
- [x] docs/decision-log.md or docs/troubleshooting.md update needed? — **No new durable failure mode** introduced by Stage 0.5 itself (the `/usr/bin/time` mis-invocation is a transient infra slip already handled by the preregistered repair+rerun). If the main thread wants the "persist wall/RSS to root" and "survey method is top-level-only" notes retained, they are candidates for a future troubleshooting/memory entry, but neither blocks acceptance.
