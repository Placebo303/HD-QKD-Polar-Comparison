# M2 accounting correction — CORRECTION_RESULT (T1 corrected-accounting record)

- Track: **DECIDE** (claim-bearing recalculation from real-data artifacts; T1 document-write only).
- Change: `openspec/changes/m2real-accounting-correction/` (spec MAC-1..9, design §§1–13, tasks T0–T4).
- Authority: `docs/research_cycles/M2-REALCOMP/CORRECTION_PREREG_AND_AUTH.md` (T0 gate PASS, §9.1 main-thread sign-off 2026-09-27; grant 「1 → 3 → 2可以」 on file).
- Branch: `formal-ir-v72p1-addendum-clean`.
- Date: 2026-09-27. Writer: coder-doc subagent (T1).
- **This record ran no decoder, no construction, no scientific command; opened no `.ttbin` and no channel bundle.** Primary value source (read-only): `workspace/m2_accounting_replay_20260926/diagnostic.json` (status `DIAGNOSTIC_UNREVIEWED`; provenance for the per-arm values is its 12-row ratio table in `ACCOUNTING_REPLAY_RESULT.md`, itself `DIAGNOSTIC_UNREVIEWED`). Nothing in any existing root, record, review, or adjudication was modified.
- **This packet is a new analysis, not an amendment of the T3 run.** The three T3 roots, `RESULT.md`, `INDEPENDENT_ACCEPTANCE.md`, `MAIN_ADJUDICATION_20260926.md` (incl. 2026-09-27 superseding note), and the accounting-replay records stay unmodified. Until T4 main-thread acceptance is signed, no corrected number in this record is citable beyond the record itself; the original M2 scientific acceptance stays WITHHELD.

## 1. Exact recomputation formulas (transcribed from the preregistration §3 without alteration)

Symbols and units. Per source/family/m arm, kept separate, never pooled. `H_corr` is per-source (M0 §3, via `RESULT.md` §2) — F9(i): "u2-only, u1 via argmax, u1 正确率未验证":
1M `0.8012690084416184`, 1p5M `0.8272902027770036`, 2M `0.8333327179427281` bits/symbol (design §0).

- **Denominator:** `D = superframes_done · 1024 · H_corr` (bits). Structural identities that must hold per arm:
  `blocks_done = 16 · superframes_done`; `lambda_parts.tag = 64 · blocks_done` (i.e. 16 recorded 64-bit tags per superframe).
- **Primary actual-disclosure ratios (design §2):** `E = lambda_parts.leak_EC` (recorded bits), `T = lambda_parts.tag` (recorded bits);
  `f_ec_actual = E / D` (tagless) with inclusive companion `f_with_recorded_tags = (E + T) / D`. Both computed from recorded disclosure.
  Primacy of `f_ec_actual` is an accounting-ordering rule only, not a validity endorsement (design §2 caveat: HDC arm measured under the
  assumed-v1 schedule on a non-functional verification path; LB arm measured under an UNKNOWN backend; neither is a validated method
  efficiency; primacy SHALL NOT be read as endorsing cross-method comparison).
- **Recorded vs displayed tag totals (design §1):** recorded unit = `64` bits per 64-symbol block (`m2real_runner.py` lines 749–755, 786–801),
  i.e. 1,024 tag bits per 1024-symbol superframe (at 1M: 3,280 blocks → 209,920 tag bits; e.g. 1M-hdc-m197 `λ_total` = 1,707,485 + 209,920 =
  1,917,405, `RESULT.md` §2.1). Displayed nominal unit = one 64-bit tag per superframe in `f_super = (5m+64)/(1024·H_corr)`
  (`m2real_runner.py` lines 247–255). The protocol under test is UNDETERMINED on this point; neither total may silently stand in for the
  other; the corrected record carries both and selects neither.
- **Nominal columns retained as history (design §2):** the runner's `f_notag = 5m/(1024·H_corr)` and `f_super = (5m+64)/(1024·H_corr)` are
  retained beside the corrected columns under the explicit label **historical / frozen-nominal**, closed-form in `(m, H)` only and therefore
  identical for HDC and LB at the same m.
- **Counterfactual one-tag column (design §3):** `f_if_one_tag_per_superframe = (E + 64·superframes_done) / D`, labelled
  **COUNTERFACTUAL_ONLY** in every table, caption, and machine-readable field where it could be quoted. It describes a verification protocol
  that was not executed (single tag over the assembled superframe with zero observed superframe successes) and SHALL NOT appear without the
  counterfactual label.
- **Discrepancy mechanism, reproduced 1M/m197 (design §2):** `D = 205 · 1024 · 0.8012690084416184 = 168202.39025206454` bits; recorded `leak_EC`
  1,707,485 (HDC) / 646,160 (LB); `f_ec_actual` = **10.15137** (HDC) / **3.84156** (LB), while `RESULT.md` §2.1 displays `f_notag` =
  985 / 820.49946… = **1.20048829** for both arms (the displayed column never reads `leak_EC`, hiding a ~2.64× disclosure difference).
  Inclusive recorded-tag ratios: **11.39939** / **5.08958**. One-tag counterfactual: **10.22937** / **3.91956**. All diagnostic, not accepted
  replacements. The first review's A-CMPE disclosure PASS checked column presence, not this consistency; per the adjudication it is
  invalidated on the accounting point and SHALL NOT be cited for disclosure correctness.
- **`f_eff` is `not-defined` for HDC and LB arms (design §4; decided D-2, DROP, user, 2026-09-27):** `f_eff = f_super + 4.785675·FER` imports the
  NB 1024-symbol superframe slope, unit-incompatible with 64-block arms; all recorded superframe successes are zero (0/205, 0/287, 0/383).
  The corrected record carries NO `f_eff` for HDC/LB (original values retained only as `historical-nominal` beside the original labels).
  Block-level denominators (`blocks_done`, fails, `undetected`, FER(block)) and superframe-level denominators (`sf_success`/`sf_total`,
  `superframes_done`) are kept as fully separate columns, never merged. Any reintroduction needs a NEW preregistration with a
  method-specific, unit-consistent definition; the frozen NB slope SHALL NOT be silently reused.

## 2. Per-column status vocabulary (preregistration §4 / design §8, closed)

No status value is invented in this record. No status is silently converted to `ok` (AGENTS.md §5.5);
`undetected` (`accepted_wrong`) is never merged into success or FER numerators.

| Status | Meaning |
|---|---|
| `measured-corrected` | recomputed from recorded `leak_EC` / tag bits in persisted summaries |
| `historical-nominal` | frozen `(5m(+64))/(1024·H)` formula display, retained for discrepancy display |
| `counterfactual` | one-tag-per-superframe arithmetic; not an executed protocol (always with `COUNTERFACTUAL_ONLY`) |
| `not-defined` | `f_eff` for HDC/LB arms (no value printed; originals retained only as `historical-nominal`) |
| `unknown` | unrecoverable provenance; the real LB `backend_used` is recorded as `UNKNOWN` (uppercase per design §5 and tasks T1: `UNKNOWN (not recorded at execution; not inferable post hoc)` — not inferred from the current environment or the synthetic batch) |
| `assumed-v1` | HDC Gray/block/pass pins (provisional, not source-verified Müller; `m2real_runner.py` lines 151–155) |
| `void-stub-artifact` | HDC success / exact_match / FER / undetected values from the production path that cannot return success (design §6; `hd_cascade.py:224–229` with the `:280–281` gate) — void as measurements, never quoted as method data |
| `void-no-correction` | HDC `leak_EC` and every quantity derived from it (`f_ec_actual`, `f_with_recorded_tags`, `f_one_tag_CF`, tag-inclusive totals, messages-as-efficiency) for arms whose full block set has `exact_match = 0` (design §11) — exhausted assumed schedule on uncorrected blocks, void as a method quantity, barred from cross-method ranking |
| `suspended` | any D2 branch cell (general vocabulary entry; for M2 the applicable value is `retired-m2`) |
| `retired-m2` | D2 branch cells for M2 — evaluation retired by decided D-3 (2026-09-27); never evaluated or reported; rejected options (i)/(ii) recorded as considered-and-rejected |

## 3. Denominators and scope notes

- Per-source `H_corr` (M0 §3, via `RESULT.md` §2) — every M0-number reference carries F9(i): "u2-only, u1 via argmax, u1 正确率未验证":
  1M `0.8012690084416184`; 1p5M `0.8272902027770036`; 2M `0.8333327179427281` bits/symbol.
- The frozen M0/V80 nominal basis (cited, not copied): content `852.544 b` at 2M with one 64-bit tag per 1024-symbol superframe
  (`docs/V80_BASELINE_20260921.md` §2; `docs/ROADMAP-20260921.md` §1.1) — F9(i): "u2-only, u1 via argmax, u1 正确率未验证".
- **FER denominator statement:** the FER denominator in every arm below is the 64-block one: 3280 (1M) / 4592 (1p5M) / 6128 (2M).
  Block-level columns (`blocks_done`, fails, `undetected`, FER(block)) and superframe-level columns (`sf_success`/`sf_total`,
  `superframes_done` = 205 / 287 / 383) are fully separate and never merged. **The superframe count is never the FER denominator.**
  All recorded superframe successes are zero (0/205, 0/287, 0/383).
- Structural identities per arm (from `diagnostic.json`): `blocks_done = 16 · superframes_done`
  (3280 = 16·205; 4592 = 16·287; 6128 = 16·383); `tag_bits_recorded = 64 · blocks_done`
  (209,920; 293,888; 392,192); `tags_per_superframe = 16.0` in every arm.
- `undetected` is isolated in its own column and is never merged into success or FER numerators (§8).
  The adjudication's follow-up descriptive reaggregation (HDC 205/205, 287/287, 383/383; LB 137/142 of 205, 152/154 of 287, 223/234 of 383
  superframes with ≥1 recorded block-level `undetected`) belongs to the recorded 64-bit-per-block verification and SHALL NOT be read as a
  prediction about a hypothetical single-tag protocol (design §4).

## 4. Per-arm corrected table (12 arms, kept strictly separate, never pooled or merged)

Source values transcribed from `diagnostic.json` arm rows; original labels from its `original_f_labels` block.
Full precision as stored; the 6-decimal rounding in `ACCOUNTING_REPLAY_RESULT.md` is that record's display only.

### Table C-1 — nominal history (`historical-nominal`) beside corrected disclosure (`measured-corrected`) and the counterfactual

| source | family | m | `f_notag` (`historical-nominal`) | `f_super` (`historical-nominal`) | `f_eff` corrected | `f_eff` original (`historical-nominal`) | `f_ec_actual` (`measured-corrected`) | `f_with_recorded_tags` (`measured-corrected`) | `f_one_tag` (`counterfactual`, COUNTERFACTUAL_ONLY) |
|---|---|---:|---:|---:|---|---|---:|---:|---:|
| 1M | hdc | 197 | 1.2004882909059704 | 1.2784895605688964 | `not-defined` | 6.064164560568897 | 10.1513717934757 | 11.399392108082516 | 10.229373063138626 COUNTERFACTUAL_ONLY |
| 1M | lb | 197 | 1.2004882909059704 | 1.2784895605688964 | `not-defined` | 6.046655993495726 | 3.8415625308991053 | 5.089582845505921 | 3.919563800562031 COUNTERFACTUAL_ONLY |
| 1M | hdc | 201 | 1.2248636876756347 | 1.3028649573385607 | `not-defined` | 6.088539957338561 | 10.152537056345665 | 11.40055737095248 | 10.23053832600859 COUNTERFACTUAL_ONLY |
| 1M | lb | 201 | 1.2248636876756347 | 1.3028649573385607 | `not-defined` | 6.078326626545879 | 3.919563800562031 | 5.167584115168847 | 3.997565070224957 COUNTERFACTUAL_ONLY |
| 1p5M | hdc | 203 | 1.1981417574785196 | 1.2736896121372638 | `not-defined` | 6.059364612137264 | 9.88005366841105 | 11.088819342950956 | 9.955601523069793 COUNTERFACTUAL_ONLY |
| 1p5M | lb | 203 | 1.1981417574785196 | 1.2736896121372638 | `not-defined` | 6.054153729079773 | 3.8340536239312626 | 5.042819298471168 | 3.9096014785900066 COUNTERFACTUAL_ONLY |
| 1p5M | hdc | 207 | 1.221750462059377 | 1.2972983167181213 | `not-defined` | 6.082973316718122 | 9.87830563714853 | 11.087071311688435 | 9.953853491807275 COUNTERFACTUAL_ONLY |
| 1p5M | lb | 207 | 1.221750462059377 | 1.2972983167181213 | `not-defined` | 6.076720257049132 | 3.9096014785900066 | 5.118367153129912 | 3.9851493332487506 COUNTERFACTUAL_ONLY |
| 2M | hdc | 204 | 1.1953133827015512 | 1.2703134380867467 | `not-defined` | 6.055988438086747 | 9.808472484764543 | 11.00847337092767 | 9.883472540149738 COUNTERFACTUAL_ONLY |
| 2M | lb | 204 | 1.1953133827015512 | 1.2703134380867467 | `not-defined` | 6.053645581526695 | 3.825002824644964 | 5.02500371080809 | 3.900002880030159 COUNTERFACTUAL_ONLY |
| 2M | hdc | 208 | 1.2187509000094248 | 1.29375095539462 | `not-defined` | 6.079425955394621 | 9.806890605332667 | 11.006891491495793 | 9.881890660717863 COUNTERFACTUAL_ONLY |
| 2M | lb | 208 | 1.2187509000094248 | 1.29375095539462 | `not-defined` | 6.077083098834567 | 3.900002880030159 | 5.100003766193285 | 3.975002935415355 COUNTERFACTUAL_ONLY |

Notes on Table C-1: the nominal columns are closed-form in `(m, H)` only and therefore identical for HDC and LB at the same m.
`f_eff` is `not-defined` for every HDC and LB arm per decided D-2 (DROP, user, 2026-09-27); the original values are retained only as
`historical-nominal` history beside the original labels. Any reintroduction of an `f_eff` for these methods requires a NEW preregistration
carrying a method-specific, unit-consistent definition; the frozen NB 1024-symbol superframe slope SHALL NOT be silently reused.
The one-tag column carries the literal string `COUNTERFACTUAL_ONLY` in every row and SHALL NOT appear without it.

### Table C-2 — recorded disclosure inputs, separated denominators, per-column status, backend

| source | family | m | `leak_EC` E (bits, recorded) | tag T (bits, recorded) | block denominator `blocks_done` (FER denominator) | block FER | superframe denominator `superframes_done` (`sf_success`/`sf_total`) | status(E, T, `f_ec_actual`, `f_with_recorded_tags`) | status(`f_one_tag`) | status(success / exact_match / FER / undetected) | `backend_used` |
|---|---|---:|---:|---:|---:|---:|---|---|---|---|---|
| 1M | hdc | 197 | 1707485.0 | 209920.0 | 3280 | 1.0 | 205 (0/205) | `void-no-correction` | `counterfactual` | `void-stub-artifact` | — (not an LB arm; `assumed-v1` scope, §5) |
| 1M | lb | 197 | 646160.0 | 209920.0 | 3280 | 0.9963414634146341 | 205 (0/205) | `measured-corrected` | `counterfactual` | (LB: nothing voided; `undetected` isolated) | UNKNOWN (not recorded at execution; not inferable post hoc) [`unknown`] |
| 1M | hdc | 201 | 1707681.0 | 209920.0 | 3280 | 1.0 | 205 (0/205) | `void-no-correction` | `counterfactual` | `void-stub-artifact` | — (not an LB arm; `assumed-v1` scope, §5) |
| 1M | lb | 201 | 659280.0 | 209920.0 | 3280 | 0.9978658536585366 | 205 (0/205) | `measured-corrected` | `counterfactual` | (LB: nothing voided; `undetected` isolated) | UNKNOWN (not recorded at execution; not inferable post hoc) [`unknown`] |
| 1p5M | hdc | 203 | 2402144.0 | 293888.0 | 4592 | 1.0 | 287 (0/287) | `void-no-correction` | `counterfactual` | `void-stub-artifact` | — (not an LB arm; `assumed-v1` scope, §5) |
| 1p5M | lb | 203 | 932176.0 | 293888.0 | 4592 | 0.998911149825784 | 287 (0/287) | `measured-corrected` | `counterfactual` | (LB: nothing voided; `undetected` isolated) | UNKNOWN (not recorded at execution; not inferable post hoc) [`unknown`] |
| 1p5M | hdc | 207 | 2401719.0 | 293888.0 | 4592 | 1.0 | 287 (0/287) | `void-no-correction` | `counterfactual` | `void-stub-artifact` | — (not an LB arm; `assumed-v1` scope, §5) |
| 1p5M | lb | 207 | 950544.0 | 293888.0 | 4592 | 0.9986933797909407 | 287 (0/287) | `measured-corrected` | `counterfactual` | (LB: nothing voided; `undetected` isolated) | UNKNOWN (not recorded at execution; not inferable post hoc) [`unknown`] |
| 2M | hdc | 204 | 3205668.0 | 392192.0 | 6128 | 1.0 | 383 (0/383) | `void-no-correction` | `counterfactual` | `void-stub-artifact` | — (not an LB arm; `assumed-v1` scope, §5) |
| 2M | lb | 204 | 1250112.0 | 392192.0 | 6128 | 0.9995104438642297 | 383 (0/383) | `measured-corrected` | `counterfactual` | (LB: nothing voided; `undetected` isolated) | UNKNOWN (not recorded at execution; not inferable post hoc) [`unknown`] |
| 2M | hdc | 208 | 3205151.0 | 392192.0 | 6128 | 1.0 | 383 (0/383) | `void-no-correction` | `counterfactual` | `void-stub-artifact` | — (not an LB arm; `assumed-v1` scope, §5) |
| 2M | lb | 208 | 1274624.0 | 392192.0 | 6128 | 0.9995104438642297 | 383 (0/383) | `measured-corrected` | `counterfactual` | (LB: nothing voided; `undetected` isolated) | UNKNOWN (not recorded at execution; not inferable post hoc) [`unknown`] |

Notes on Table C-2: nominal columns (`f_notag`, `f_super`, original `f_eff`) carry status `historical-nominal`; corrected `f_eff`
carries status `not-defined` (Table C-1). HDC rows carry `assumed-v1` scope on every number in addition to the two void labels (§5).
`tags_per_superframe = 16.0` and `one_tag_per_superframe_value_is = COUNTERFACTUAL_ONLY` in every arm (from `diagnostic.json`).

## 5. HDC standing limits (both void labels on every HDC number)

- **Scope (`assumed-v1`):** every HDC number describes the assumed-v1 Gray/block/pass pins only (uniform [8,4] blocks, max_passes 4,
  one cross-plane sweep; `m2real_runner.py` lines 151–155; `require_assumed_block_table` guard), provisional, not source-verified Müller.
  No HDC figure is presented as a method-family ranking.
- **Verification-path void (`void-stub-artifact`):** the implemented HDC production verification path cannot return success —
  `_run_planes_production` unconditionally returns `"accepted": True, "toeplitz_verified": False`
  (`comparison_bench/src/comparison_bench/methods/hd_cascade.py:224–229`), so the unified gate at `:280–281`
  (`success = exact and verified and accepted`; `und = accepted and not success`) yields `success=False, undetected=True` for every
  production block regardless of decode quality. `m2real_runner.py:491` calls the same entrypoint, so every HDC success / exact_match /
  FER / undetected value in any artifact is a structural stub artifact, void as a measurement, never quoted as method data.
  Authority: `docs/research_cycles/M2-HDCASCADE-SYNTH/BATCH_END_REVIEW.md` §§2–4 (B1, H1–H2).
- **Zero-correction void (`void-no-correction`):** a read-only count over the three real M2 T3 roots' `block_accounting.csv` finds
  `exact_match = 0` in every one of the **28,000** real HDC blocks — 1M (`workspace/m2real_d4e5f6a7`) m197/m201 at 3,280 blocks each
  (6,560); 1p5M (`workspace/m2real_b8c9d0e1`) m203/m207 at 4,592 blocks each (9,184); 2M (`workspace/m2real_f2a3b4c5`) m204/m208 at
  6,128 blocks each (12,256); 6,560 + 9,184 + 12,256 = 28,000. In the same rows `accepted = undetected = accepted_wrong = n`.
  Synth corroboration: `exact_match = False` for all 13 blocks in each of the 6 synth arms (0 of 78).
  HDC `leak_EC` and every column derived from it (`f_ec_actual`, `f_with_recorded_tags`, `f_one_tag_CF`, tag-inclusive totals,
  messages-as-efficiency) are therefore the disclosure figures of **the cost of an exhausted assumed schedule on never-corrected blocks —
  an upper bound on a non-working configuration, not a method property** — void as a method quantity and barred from cross-method ranking.
  Of the HDC numbers, only the existence of the negative result and the schedule configuration remain citable (design §10.1 supersedes
  the §10 table's HDC "still-usable" cells; the M2 real LB row of the §10 table stands unchanged).
- Wiring a real Toeplitz verifier alone (D-4 option ii, considered and recorded as a non-repair) changes no value of `exact_match`,
  `leak_EC`, or FER; it relabels the `undetected` column only, at the cost of a separately frozen DECIDE execution. A citable HD-Cascade
  number needs a converging cascade (a real verifier AND correcting parameters/schedule) — a research sub-project outside this change.

## 6. D2 is `retired-m2` (decided D-3, user, 2026-09-27; M2 scope only)

No D2 rule exists in this record. No D2 branch is evaluated. No D2 branch outcome is reported. Every D2 branch cell carries
`retired-m2`. The rejected options are recorded as considered-and-rejected: (i) re-evaluate on actual-disclosure f and (ii) freeze a new
rule — rejected for lack of valid input (the displayed f was not actual disclosure, the tag unit is undecided per deferred D-1, the HDC arm
cannot be evaluated at all, and the real LB backend is UNKNOWN). Routing proceeds via the independent M0/P1 measured gap instead.
The retirement is scoped to M2 only and states nothing beyond M2; any future comparison metric requires a new preregistration before
claim-bearing evaluation. D2 SHALL NOT be evaluated with the HDC arm at all in its current state, and the HDC column of the same-data
comparison table CANNOT be filled from existing artifacts (MAC-9).

## 7. D-1 is deferred (non-blocking)

All tag totals are carried distinctly in this record — the recorded 16×64-bit-per-block total (`f_with_recorded_tags`), the nominal
one-tag-per-superframe form (`f_super`, `historical-nominal`), and the one-tag arithmetic column (`counterfactual`, COUNTERFACTUAL_ONLY) —
and **no column is designated the headline tag ratio**. D-1 decides only the headline column when a frozen protocol specification settles it,
never by code inference. Resolving D-1 later changes the headline f column, not any already-published column.

## 8. Discrepancy mechanism (1M / m=197, reproduced inline)

Denominator: `D = 205 · 1024 · 0.8012690084416184 = 168202.39025206454` bits
(205 · 1024 = 209,920 symbols; 209,920 · 0.8012690084416184 = 168,202.39025206454 bits).

- Displayed nominal (both arms, never reads `leak_EC`): `f_notag` = 985 / 820.49946… = **1.20048829**,
  where 985 = 5·197 and 820.49946… = 1024 · 0.8012690084416184.
- HDC actual: `f_ec_actual` = 1,707,485 / 168,202.39025206454 = **10.15137** (10.1513717934757 as stored).
- LB actual: `f_ec_actual` = 646,160 / 168,202.39025206454 = **3.84156** (3.8415625308991053 as stored).
- The displayed column hides a ~2.64× disclosure difference (1,707,485 vs 646,160 bits).
- Inclusive recorded-16-tag ratios: (1,707,485 + 209,920) / 168,202.39025206454 = 1,917,405 / 168,202.39025206454 = **11.39939**
  (11.399392108082516 as stored); (646,160 + 209,920) / 168,202.39025206454 = 856,080 / 168,202.39025206454 = **5.08958**
  (5.089582845505921 as stored).
- One-tag counterfactual: (1,707,485 + 64·205) / 168,202.39025206454 = 1,720,605 / 168,202.39025206454 = **10.22937**
  (10.229373063138626 as stored) COUNTERFACTUAL_ONLY; (646,160 + 64·205) / 168,202.39025206454 = 659,280 / 168,202.39025206454 = **3.91956**
  (3.919563800562031 as stored) COUNTERFACTUAL_ONLY.
- **These diagnostic ratios are not an accepted replacement result.** The first review's A-CMPE disclosure PASS checked column presence,
  not this consistency; per the adjudication it is invalidated on the accounting point and SHALL NOT be cited for disclosure correctness.

## 9. Backend provenance (`backend_used = UNKNOWN` for every real LB arm)

- Every real LB arm in Table C-2 records `backend_used = UNKNOWN (not recorded at execution; not inferable post hoc)` with status `unknown`.
  It may not be inferred from what is installed now, and it is not carried over from the synthetic batch (which documented min-sum fallback —
  that does not prove the real run's backend). The LB adapter (`m2real_runner.py` lines 857–881) may run true binary SPA or the numpy min-sum
  fallback; the three M2 roots contain no `backend_used` in any per-block row or arm summary, and no backend sidecar, stdout, or resource
  transcript exists in them.
- Exactly what a future separately frozen DECIDE run would have to persist to make backend recoverable (design §5; execution-time only —
  reconstruction from the current environment after the fact is explicitly NOT acceptable provenance): (i) per-block `backend_used` string
  naming the entered decode body in `block_accounting.csv` and `rows.json`; (ii) one `backend_used.sidecar.json` per root recording package
  presence, selected branch, and construct/decode function identity; (iii) the stdout transcript including the terminal END/exit state;
  (iv) a wall/RSS resource record.
- The M2 real LB disposition ("retained-assumed, no promotion") stands unchanged by this record.

## 10. Claim ceiling (quoted verbatim from §10 of the preregistration)

Spec MAC-8 (spec.md lines 88–92): "The record SHALL carry the M2 claim ceiling (no SKR/secure-key/qualification/composable-security/publication
claim; F9(i) u2-only annotation on every M0-number reference) and the measured/assumed/projected/qualified column attribution."

Consequence: the corrected record establishes only stored disclosure arithmetic for the recorded implementations. It does not establish a fair
method-family comparison, a verification protocol for the one-tag counterfactual, a validated method efficiency, an `f_eff_actual`, a D2 verdict,
a backend identity, an SKR/secure-key/qualification/composable-security/publication claim, or any M0-number reference without the F9(i)
"u2-only, u1 via argmax, u1 正确率未验证" annotation. Until T4 main-thread acceptance is signed, no corrected number is citable beyond the record
itself (tasks T4); the original M2 scientific acceptance stays WITHHELD.

## 11. What this record explicitly does NOT do

- No redecoding or new execution of any method arm; no `.ttbin` or bundle read.
- No HDC comparison column is filled; no HDC void column is quoted as a measurement or used in any ranking.
- No D2 evaluation, D2 branch reporting, or new D2 rule text.
- No backend inference for the real LB arm (anything other than `UNKNOWN`).
- No method ranking (in particular, HDC's ~9.8–10.2 disclosure ratios SHALL NOT be read as "HD-Cascade is about 8x worse than NB-LDPC";
  NB-side actual disclosure is itself unavailable — M0 `rows.json` has no `leak_EC`/tag-event ledger, F9(i): "u2-only, u1 via argmax, u1 正确率未验证" — so no three-method actual-disclosure comparison is constructed from stored artifacts).
- No SKR, secure-key, qualification, composable-security, or publication number.
- No single-point efficiency certification and no `f_eff_actual`.
- No NB actual-disclosure column is constructed from stored artifacts (design §9 choice 5).

## 12. Provenance, decisions, and what remains

- Provenance chain: three T3 roots (`workspace/m2real_d4e5f6a7` 14,042,522 B; `workspace/m2real_b8c9d0e1` 19,734,691 B;
  `workspace/m2real_f2a3b4c5` 26,471,294 B) → reviewed replay arithmetic (`diagnostic.json`, Pre-RESULT PASS for stored disclosure
  arithmetic only) → this record. Problem being corrected: `MAIN_ADJUDICATION_20260926.md` incl. its 2026-09-27 superseding note
  (findings 1–5; first review's accounting PASS and D2 conclusion invalidated).
- HDC void authority: `docs/research_cycles/M2-HDCASCADE-SYNTH/BATCH_END_REVIEW.md` §§2–4 (FAIL, B1/H1–H2).
- Decisions (decision-log 2026-09-27, D-1..D-4): D-1 DEFERRED (open, non-blocking; §7); D-2 DROPPED (frozen; §4 Table C-1);
  D-3 D2 RETIRED FOR M2 (frozen; §6); D-4 option (iii) — HDC as documented negative implementation result (frozen; §5).
- Remaining gates: T2 independent recomputation check (read-only; at least one arm per source from persisted `rows.json` summaries),
  T3 independent Pre-RESULT review (`CORRECTION_INDEPENDENT_ACCEPTANCE.md`, PASS or FAIL; FAIL blocks solidification), T4 main-thread
  acceptance (BLANK until signed by main + user; coder does not sign).
