# M2 accounting correction — CORRECTION_PREREG_AND_AUTH (T0 DECIDE gate)

- Track: **DECIDE** (claim-bearing recalculation from real-data artifacts). This gate governs the frozen conditional T1→T2→T3 sequence under
  `openspec/changes/m2real-accounting-correction/` (spec MAC-1..9, design §§1–13, tasks T0–T4, proposal AC-1..AC-5).
- Branch: `formal-ir-v72p1-addendum-clean`. HEAD at drafting: `ce85d61f5f625a323765481cb726f77e0380b86a` (measured 2026-09-27 by the drafting
  subagent; main re-verifies at Pre-EXECUTE — see §9).
- Date: 2026-09-27. Drafter: planner subagent (main-thread-owned item; main signs off before T1 starts).
- **This packet is a new analysis, not an amendment of the T3 run.** The three T3 roots, the T3 records (`RESULT.md`,
  `INDEPENDENT_ACCEPTANCE.md`), the adjudication, and the accounting-replay records stay unmodified. Nothing in this packet reopens,
  rewrites, or re-labels any value inside an existing root or record.
- Precedent and format: `ACCOUNTING_REPLAY_PREREG_AND_AUTH.md` (G-M2-ACCT-REPLAY), whose structure this packet follows: track, frozen inputs
  with sizes/mtimes, exact formulas, budget ceilings, stop rules, verbatim grant, fillable Pre-EXECUTE checklist.

## 1. Grant (verbatim, on file)

- User grant given to main, verbatim: **「1 → 3 → 2可以」** (2026-09-27), relayed by the main thread. In that session item 1 was described to
  the user as the M2 accounting T0 gate followed by the frozen T1→T3 sequence.
- Main's interpretation, recorded here: the grant authorizes **this T0 gate and the frozen conditional T1→T2→T3 sequence** (T1 corrected-record
  document, T2 read-only recomputation check, T3 independent Pre-RESULT review) strictly within the budget ceilings of §7 and the stop rules
  of §8. No decoder run, no `.ttbin` or bundle read, no new execution of any method arm, no write to any existing root/record/review, no
  commit/push.
- **Explicit flag for main:** if main wants a separate fresh confirmation before the T2 read-only recompute, one line must be added below by
  main. No additional grant text is invented here; the single verbatim string above is the entire grant on file.
- Main sign-off on this packet (T0 acceptance) is still required before T1 starts. T1–T3 SHALL NOT execute before that sign-off
  (tasks.md convention; orchestrator SHALL NOT route around the gate).

## 2. Frozen read-only inputs (measured now; read-only for this task)

No `.ttbin`, no channel bundle, and no decoder/construction artifact is read — by this T0 drafting, and by the downstream T1/T2 work this packet
gates. The only machine inputs are persisted summaries and the reviewed replay arithmetic. Sizes and UTC mtimes as measured at drafting
(`TZ=UTC stat`):

| # | File | Bytes | UTC mtime |
|---|---|---:|---|
| I-1 | `workspace/m2real_d4e5f6a7/rows.json` (1M) | 14,042,522 | 2026-09-25 16:13:17.826477200 |
| I-2 | `workspace/m2real_b8c9d0e1/rows.json` (1p5M) | 19,734,691 | 2026-09-25 16:25:17.810531000 |
| I-3 | `workspace/m2real_f2a3b4c5/rows.json` (2M) | 26,471,294 | 2026-09-25 16:39:46.585827700 |
| I-4 | `workspace/m2_accounting_replay_20260926/diagnostic.json` (reviewed replay arithmetic; Pre-RESULT PASS for stored disclosure arithmetic only) | 10,664 | 2026-09-25 17:21:33.366234000 |
| I-5 | `workspace/m2_accounting_replay_20260926/resource.txt` (replay resource record: wall 0.51 s, RSS 124,128 KiB, exit 0) | 916 | 2026-09-25 17:21:33.498898900 |

I-1..I-3 sizes match the replay Pre-EXECUTE record (14,042,522 / 19,734,691 / 26,471,294). Each root is `COMPLETE` with
`blocks_done = 16 · superframes_done` and `lambda_parts.tag = 64 · blocks_done` (design §0).

Field inventory of I-4 (read-only; the corrected record draws source values from these arm rows): top-level `formulas_and_units`
(`D`, `f_ec_actual`, `f_with_recorded_tags`, `tags_per_superframe`, `f_if_one_tag_per_superframe` — counterfactual-only);
`claim_ceiling`; per-source `H_corr_bits_per_symbol`; 12 arms (1M hdc/lb × m197/m201; 1p5M hdc/lb × m203/m207; 2M hdc/lb × m204/m208),
each with `blocks_done`, `superframes_done`, `fer_blocks`, `sf_success` (= 0), `sf_total`, `original_f_labels` (`f_super`, `f_notag`,
`f_eff`), `leak_EC_bits_recorded`, `tag_bits_recorded`, `tags_per_superframe` (= 16.0), `f_ec_actual`, `f_with_recorded_tags`,
`f_if_one_tag_per_superframe`, `one_tag_per_superframe_value_is` (= `COUNTERFACTUAL_ONLY`).

Cycle documents cited as authority (read-only; sizes/UTC mtimes measured now):

| # | File | Bytes | UTC mtime |
|---|---|---:|---|
| A-1 | `docs/research_cycles/M2-REALCOMP/MAIN_ADJUDICATION_20260926.md` (incl. 2026-09-27 superseding note) | 8,044 | 2026-09-27 03:50:35.963707200 |
| A-2 | `docs/research_cycles/M2-REALCOMP/RESULT.md` | 11,305 | 2026-09-25 16:50:01.660119400 |
| A-3 | `docs/research_cycles/M2-REALCOMP/INDEPENDENT_ACCEPTANCE.md` (first review; accounting PASS and D2 conclusion invalidated per adjudication) | 8,069 | 2026-09-25 16:59:14.409989300 |
| A-4 | `docs/research_cycles/M2-REALCOMP/ACCOUNTING_REPLAY_PREREG_AND_AUTH.md` (G-M2-ACCT-REPLAY preregistration; format precedent) | 5,409 | 2026-09-25 17:21:15.174367100 |
| A-5 | `docs/research_cycles/M2-REALCOMP/ACCOUNTING_REPLAY_RESULT.md` | 2,328 | 2026-09-25 17:28:34.907281100 |
| A-6 | `docs/research_cycles/M2-REALCOMP/ACCOUNTING_REPLAY_INDEPENDENT_ACCEPTANCE.md` (PASS for stored disclosure arithmetic only) | 1,647 | 2026-09-25 17:28:34.908318300 |
| A-7 | `docs/research_cycles/M2-REALCOMP/PREREG_AND_AUTH.md` (G-M2-REALCOMP) | 14,631 | 2026-09-24 18:59:48.404660600 |
| A-8 | `docs/research_cycles/M2-HDCASCADE-SYNTH/BATCH_END_REVIEW.md` (FAIL, B1; authority for the HDC void findings) | 10,375 | 2026-09-27 03:30:28.182941700 |
| A-9 | `docs/decision-log.md` (2026-09-24 D2 frozen rule; 2026-09-24 F9(i); 2026-09-26 WITHHELD/suspension; 2026-09-27 D-1..D-4) | 425,598 | 2026-09-27 04:04:25.195070200 |

Frozen M0/V80 nominal basis (cited, not copied): content `852.544 b` at 2M with one 64-bit tag per 1024-symbol superframe
(`docs/V80_BASELINE_20260921.md` §2; `docs/ROADMAP-20260921.md` §1.1).

## 3. Exact recomputation formulas (transcribed from design §§1–4 without alteration)

Symbols and units. Per source/family/m arm, kept separate, never pooled. `H_corr` is per-source (M0 §3, via `RESULT.md` §2):
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

## 4. Per-column status vocabulary (design §8, closed)

Every recomputed column carries an explicit status from this vocabulary. No status may be silently converted to `ok` (AGENTS.md §5.5);
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

## 5. Frozen scientific constraints (any downstream record MUST respect all of these)

- HDC arm `success`/`FER`/`undetected` columns are `void-stub-artifact` (design §6, §10; authority `BATCH_END_REVIEW.md` §§2–4, B1/H1–H2).
- HDC `leak_EC` and every column derived from it are `void-no-correction` on the measured `exact_match = 0` fact: **0 of all 28,000 real HDC
  blocks** — 1M (`workspace/m2real_d4e5f6a7`) m197/m201 at 3,280 blocks each; 1p5M (`workspace/m2real_b8c9d0e1`) m203/m207 at 4,592 each;
  2M (`workspace/m2real_f2a3b4c5`) m204/m208 at 6,128 each (6,560 + 9,184 + 12,256); synth corroboration 0 of 78 (design §11). In the same rows
  `accepted = undetected = accepted_wrong = n`. §10.1 supersedes the §10 table's HDC "still-usable" cells: of the HDC numbers, only the
  existence of the negative result and the schedule configuration remain citable. The M2 real LB row of the §10 table stands unchanged.
- No D2 rule exists and no D2 branch may be evaluated or reported (`retired-m2`, M2-scoped only per decided D-3; rejected options (i)/(ii)
  recorded as considered-and-rejected for lack of valid input; routing via the M0/P1 measured gap; the retirement states nothing beyond M2).
- The real Layered-Binary `backend_used` is `UNKNOWN` and may not be inferred (design §5). Future persistence set (separately frozen DECIDE run
  only): per-block `backend_used` in `block_accounting.csv` + `rows.json`, per-root sidecar, stdout END/exit transcript, wall/RSS record.
- `undetected` is never merged into success or FER. The adjudication's follow-up descriptive reaggregation (HDC 205/205, 287/287, 383/383; LB
  137/142 of 205, 152/154 of 287, 223/234 of 383 superframes with ≥1 recorded block-level `undetected`) belongs to the recorded 64-bit-per-block
  verification and SHALL NOT be read as a prediction about a hypothetical single-tag protocol (design §4).
- D-1 is deferred (non-blocking): every tag total is carried distinctly and no single headline tag ratio is designated. D-1 decides only the
  headline column when a frozen protocol specification settles it — never by code inference.
- F9(i) annotates every M0-number reference: **"u2-only, u1 via argmax, u1 正确率未验证"** (decision-log 2026-09-24 F9(i)裁定;去标注引用 = 违规引用).
  No NB actual-disclosure column is constructed from stored artifacts (M0 `rows.json` has no `leak_EC`/tag ledger; design §9 choice 5).

## 6. Output document (name and location decided here)

- The T1 corrected-accounting record SHALL be written as exactly one ADDITIVE document:
  **`docs/research_cycles/M2-REALCOMP/CORRECTION_RESULT.md`**.
- It lives directly under `docs/research_cycles/M2-REALCOMP/`, never inside an existing root (`workspace/m2real_*`, `workspace/m2_accounting_replay_20260926/`).
  It SHALL never overwrite `RESULT.md`, `INDEPENDENT_ACCEPTANCE.md`, the adjudication (`MAIN_ADJUDICATION_20260926.md`), the accounting-replay
  records (A-4/A-5/A-6), any T3 root, or this packet.
- The T3 independent Pre-RESULT review (tasks T3) is preregistered here as **`docs/research_cycles/M2-REALCOMP/CORRECTION_INDEPENDENT_ACCEPTANCE.md`**
  (name already fixed by tasks.md T3), recording PASS or FAIL with findings; FAIL blocks solidification.
- A fresh additive `workspace/` scratch root is permitted ONLY if the T2 recomputation needs machine files (calculator or throwaway read-only
  script importing no decoder/construction module, writing no file outside that fresh root — or no file at all). No other new machine root is
  authorized by this packet.

## 7. Budget

- One process. Wall ≤ 300 s. Peak RSS < 2 GiB. No retry, no resume. Single CPU with the thread environment pinned.
- No decoder and no construction runs, so the wall ceiling is generous by design. The T2 recompute reads only the persisted `summary` values of
  I-1..I-3 (plus I-4 for the arm-row source values); it opens no `.ttbin`, no bundle, no CSV beyond the preregistered summaries.
- An incomplete/failed attempt is retained and stops the grant; inputs are never adjusted to fit.

## 8. Stop rules (any one STOPs the gated sequence; retain evidence, do not adjust inputs to fit, return to main)

1. Input drift: any size or mtime change in I-1..I-5 against §2.
2. Any need to decode, construct, open a `.ttbin` or bundle, or import a decoder/construction module.
3. Any attempt to write inside an existing root (`workspace/m2real_*`, `workspace/m2_accounting_replay_20260926/`) or to modify any existing
   record, review, adjudication, or cycle document.
4. Any status-column invention outside the §4 vocabulary, or any silent conversion toward `ok`.
5. Any attempt to fill an HDC comparison column, quote an HDC void column as a measurement, or rank methods on void columns.
6. Any D2 evaluation, D2 branch reporting, or new D2 rule text beyond the rejected options recorded as considered-and-rejected.
7. Any backend inference for the real LB arm (anything other than `UNKNOWN`).
8. Budget breach (wall/RSS/process/retry) or single-CPU pin deviation.
9. Evidence-label error: missing `COUNTERFACTUAL_ONLY` on any one-tag figure, missing `historical-nominal` on any retained nominal, missing
   `not-defined` discipline on `f_eff`, missing F9(i) on any M0-number reference.

## 9. Pre-EXECUTE checklist (fillable record; main measures and marks each item PASS or STOP before T1)

| # | Item | Measured at drafting (for main to re-verify) | Main verdict (measured 2026-09-27) |
|---|---|---|---|
| P-1 | Branch and HEAD: `formal-ir-v72p1-addendum-clean`; HEAD recorded | Branch confirmed; HEAD `ce85d61f5f625a323765481cb726f77e0380b86a` at drafting | **PASS** — re-measured: branch `formal-ir-v72p1-addendum-clean`, HEAD `ce85d61f5f625a323765481cb726f77e0380b86a` (identical) |
| P-2 | Scoped cleanliness: this task creates exactly one file (§6 target of THIS packet is this file itself; T1 creates `CORRECTION_RESULT.md` only) | This packet: `docs/research_cycles/M2-REALCOMP/CORRECTION_PREREG_AND_AUTH.md` (new file; no CORRECTION_* file existed at drafting) | **PASS** — `git status --porcelain -- docs/research_cycles/M2-REALCOMP/` reports `?? docs/research_cycles/M2-REALCOMP/`, i.e. the whole cycle directory is untracked cycle documentation, **not** a dirty scoped tree; main confirms this is the intended meaning. No tracked file under this directory is modified. |
| P-3 | `git diff -- src/ experiments/ tools/` empty for this task | Empty at drafting (read-only `git diff --stat` returned no output) | **PASS** — re-measured: `git diff --stat -- src/ experiments/ tools/` returns 0 lines |
| P-4 | `git diff --stat -- results/ comparison_bench/outputs_comparison/` empty | Empty at drafting | **PASS** — re-measured: 0 lines |
| P-5 | Target output document absent (`CORRECTION_RESULT.md`; T3: `CORRECTION_INDEPENDENT_ACCEPTANCE.md`) | Both absent at drafting (directory listing shows no CORRECTION_* file) | **PASS** — re-measured: both absent |
| P-6 | Three T3 roots and the replay root unmodified (sizes/mtimes against §2) | §2 table is the baseline; re-check before T1/T2 | **PASS** — re-measured, all five sizes byte-identical to §2: 14,042,522 / 19,734,691 / 26,471,294 / 10,664 / 916. mtimes re-measured and identical as instants (the §2 table states them in UTC; the local re-measurement renders the same instants in +0800, e.g. §2 `2026-09-25 16:13:17.826477200` = local `2026-09-26 00:13:17.826477200 +0800`). No drift. |
| P-7 | Focused-test item | `N/A — no code is added by this change` (no runner/helper is preregistered; no test command exists to run) | **PASS (N/A recorded with reason)** — accepted: this change adds no code, so there is nothing to test. |

### 9.1 Main-thread T0 acceptance (sign-off)

- ALL items PASS, P-7 accepted as N/A with reason, and the §1 grant is on file ⇒ the gate is **PASS**.
- Accepted by: main thread, 2026-09-27. T1, T2 and T3 may now execute within §7's ceilings and §8's stop rules, in that order, under the single §1 grant.
- **No separate fresh confirmation before T2 was added**, because main reads the §1 grant as already covering the frozen T1→T2→T3 sequence. If that reading is later withdrawn, T2 stops until a fresh grant line is added here.
- Standing limits carried into T1: no D2 evaluation or reporting (`retired-m2`); no HDC comparison column; no Layered-Binary backend inference; both HDC void labels on every HDC number; `f_eff` = `not-defined`; `undetected` never merged into success; D-1 deferred, so all tag totals are carried distinctly and **no** column is designated the headline.
- This acceptance covers T0 only. It is **not** acceptance of T1's numbers, and not a publication, qualification or SKR claim.

ALL items PASS (or N/A-with-reason for P-7), plus the §1 grant on file, or the sequence STOPS. `git status --porcelain -- docs/research_cycles/M2-REALCOMP/` at drafting
reported the directory as untracked (`??`) — main confirms the intended meaning (untracked cycle docs, not a dirty scoped tree) when marking P-2.

## 10. Claim ceiling (quoted verbatim from the change's own docs)

Spec MAC-8 (spec.md lines 88–92): "The record SHALL carry the M2 claim ceiling (no SKR/secure-key/qualification/composable-security/publication
claim; F9(i) u2-only annotation on every M0-number reference) and the measured/assumed/projected/qualified column attribution."

Consequence: the corrected record establishes only stored disclosure arithmetic for the recorded implementations. It does not establish a fair
method-family comparison, a verification protocol for the one-tag counterfactual, a validated method efficiency, an `f_eff_actual`, a D2 verdict,
a backend identity, an SKR/secure-key/qualification/composable-security/publication claim, or any M0-number reference without the F9(i)
"u2-only, u1 via argmax, u1 正确率未验证" annotation. Until T4 main-thread acceptance is signed, no corrected number is citable beyond the record
itself (tasks T4); the original M2 scientific acceptance stays WITHHELD.

## 11. What remains undecided

- D-1 (tag verification unit) is DEFERRED and non-blocking: nothing in this packet designates a headline tag ratio. Settling evidence is a frozen
  protocol specification, not a code reading; resolving it later changes the headline f column, not any already-published column.
- D-2 (`f_eff` DROP), D-3 (D2 RETIRED FOR M2), D-4 (option iii) are decided 2026-09-27 and frozen; implementers treat them as frozen and T4 records them.
- T4 acceptance (accept the corrected record as stored disclosure arithmetic; keep original M2 scientific acceptance WITHHELD; record D-1
  DEFERRED-open with D-2/D-3/D-4 decided) is BLANK until signed by main + user; the coder does not sign.
