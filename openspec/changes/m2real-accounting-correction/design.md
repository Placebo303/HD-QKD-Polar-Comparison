# M2 real accounting correction — Design

Status: DECIDE-gated definitions plus a read-only recomputation record.
This file freezes meaning only; it authorizes nothing. Any
claim-bearing recomputation runs under its own preregistration,
Pre-EXECUTE, and explicit grant (precedent:
`ACCOUNTING_REPLAY_PREREG_AND_AUTH.md`, G-M2-ACCT-REPLAY).

All numbers below state provenance. Diagnostic ratios are stored
disclosure arithmetic for the recorded implementations, not accepted
results. Every "unknown" stays unknown.

## 0. Frozen inputs (read-only, never recopied except as cited)

- Three T3 roots: `workspace/m2real_d4e5f6a7` (1M),
  `workspace/m2real_b8c9d0e1` (1p5M), `workspace/m2real_f2a3b4c5` (2M);
  each `COMPLETE` with `blocks_done = 16 * superframes_done` and
  `lambda_parts.tag = 64 * blocks_done`.
- Reviewed replay arithmetic:
  `workspace/m2_accounting_replay_20260926/diagnostic.json`
  (independent Pre-RESULT PASS for stored disclosure arithmetic only;
  `ACCOUNTING_REPLAY_INDEPENDENT_ACCEPTANCE.md`).
- Per-source denominators use each source's own `H_corr` (M0 §3, via
  `RESULT.md` §2): 1M `0.8012690084416184`, 1p5M `0.8272902027770036`,
  2M `0.8333327179427281`. The frozen M0/V80 nominal basis is content
  `852.544 b` at 2M with one 64-bit tag per 1024-symbol superframe
  (`docs/V80_BASELINE_20260921.md` §2; `docs/ROADMAP-20260921.md` §1.1).

## 1. Tag verification unit (finding a)

Two totals exist and neither may silently stand in for the other:

- **Recorded unit (executed bookkeeping):** `m2real_runner.py` lines
  749–755 record `tag_bits = 64` per 64-symbol block, and lines 786–801
  accumulate `lambda_parts.tag = 64 * blocks_done`. At 1M that is 3,280
  blocks → 209,920 tag bits, i.e. **1,024 tag bits per 1024-symbol
  superframe** (16 tags × 64 bits). Every `λ_total` value in `RESULT.md`
  §2 uses this recorded total (e.g. 1M-hdc-m197: 1,707,485 + 209,920 =
  1,917,405; `RESULT.md` §2.1).
- **Displayed unit (nominal formula):** `f_super = (5m+64)/(1024·H_corr)`
  (`m2real_runner.py` lines 247–255) adds **one 64-bit tag per
  superframe**, matching the M0/V80 frozen comparison basis (one 64-bit
  tag per superframe; `V80_BASELINE_20260921.md` §2; ROADMAP §1.1).
- **Definition:** the protocol under test is UNDETERMINED on this point.
  If the true protocol verifies each 64-symbol block, that is a 16× tag
  cost and every f column must show it (the `f_with_recorded_tags`
  column: 11.39939 HDC / 5.08958 LB at 1M/m197, diagnostic). If the
  true protocol verifies only the assembled superframe, the recorded
  16-tag total is bookkeeping overhead, not protocol disclosure, and
  only the counterfactual one-tag column applies. The corrected record
  SHALL carry both columns with these labels and SHALL NOT select
  between them; selection requires a separately frozen protocol
  specification, not an accounting choice.

## 2. Actual-disclosure f as primary (finding b)

- **Primary definition:** for each arm, `D = superframes_done · 1024 ·
  H_corr`, `E = lambda_parts.leak_EC`, and the primary disclosure
  ratio is `f_ec_actual = E / D` (tagless) with the inclusive companion
  `f_with_recorded_tags = (E + T) / D` where `T = lambda_parts.tag`.
  Both are computed from recorded disclosure, per source/family/m,
  never pooled.
- **Nominal columns retained as history:** the runner's
  `f_notag = 5m/(1024·H_corr)` and `f_super = (5m+64)/(1024·H_corr)`
  SHALL be retained beside the corrected columns under the explicit
  label **historical / frozen-nominal**, with the note that they are
  closed-form in `(m, H)` only and therefore identical for HDC and LB
  at the same m.
- **Discrepancy mechanism (reproduced, 1M/m197):** `D = 205 · 1024 ·
  0.8012690084416184 = 168202.39025206454` bits (independently
  recomputed in `ACCOUNTING_REPLAY_INDEPENDENT_ACCEPTANCE.md`).
  Recorded `leak_EC` is 1,707,485 bits (HDC) and 646,160 bits (LB)
  (`RESULT.md` §3; `rows.json` `lambda_parts`). Hence `f_ec_actual` =
  1,707,485 / 168,202.39 = **10.15137** (HDC) and 646,160 / 168,202.39
  = **3.84156** (LB) — diagnostic, not accepted replacements — while
  `RESULT.md` §2.1 displays `f_notag` = 985 / 820.49946… =
  **1.20048829** for both arms. The mechanism: the displayed column
  never reads `leak_EC`, so a ~2.64× disclosure difference (1,707,485
  vs 646,160) is invisible in it. The inclusive recorded-tag ratios
  are (1,707,485 + 209,920) / 168,202.39 = **11.39939** and (646,160 +
  209,920) / 168,202.39 = **5.08958**. The one-tag counterfactual is
  (1,707,485 + 64·205) / 168,202.39 = **10.22937** (HDC) and
  (646,160 + 64·205) / 168,202.39 = **3.91956** (LB).
- The first review's A-CMPE disclosure PASS
  (`INDEPENDENT_ACCEPTANCE.md` §1 item 2) checked column presence, not
  this consistency; per the adjudication it is invalidated on the
  accounting point and SHALL NOT be cited for disclosure correctness.
- **Caveat on primacy (per `docs/research_cycles/M2-HDCASCADE-SYNTH/BATCH_END_REVIEW.md`
  §2 B1):** primacy of `f_ec_actual` is an accounting-ordering rule, not
  a validity endorsement. For the HDC arm, `f_ec_actual` is a measured
  cascade communication cost under the assumed-v1 schedule
  (`m2real_runner.py` lines 151–155; uniform [8,4] blocks, max_passes 4,
  one cross-plane sweep), measured on a production verification path
  that cannot return success (`hd_cascade.py:224–229` unconditionally
  returns `accepted=True, toeplitz_verified=False`, so the `:280–281`
  gate forces `success=False, undetected=True` for every block). For
  the LB arm it is measured under an UNKNOWN backend (design §5).
  Neither is a validated method efficiency, and primacy SHALL NOT be
  read as endorsing cross-method comparison on those columns (see §6,
  §9 choice 6, §10).

## 3. One-tag column is counterfactual (finding c)

`f_if_one_tag_per_superframe = (E + 64·superframes_done) / D` SHALL be
labelled **COUNTERFACTUAL_ONLY** in every table, caption, and
machine-readable field where it could be quoted (precedent:
`m2_accounting_replay.py` lines 127–129 and
`ACCOUNTING_REPLAY_RESULT.md` §5). It describes a verification
protocol that was not executed (single tag over the assembled
superframe with zero observed superframe successes) and SHALL NOT
appear without the counterfactual label.

## 4. FER unit separation; `f_eff` DROPPED for HDC/LB (decided D-2, 2026-09-27; finding d)

- M2 reports block FER over 64-symbol blocks (denominators 3280 / 4592 /
  6128; `RESULT.md` §2). The `f_eff = f_super + 4.785675·FER` column
  imports the NB 1024-symbol superframe slope (frozen NB convention;
  `V80_BASELINE_20260921.md` §2; ROADMAP DECISION-1). These are
  incompatible scales: the slope is not a validated method-specific
  efficiency for 64-block HDC/LB protocols.
- All recorded superframe-success columns are zero (0/205, 0/287,
  0/383; `RESULT.md` §2.1–§2.3), so any superframe-scale efficiency for
  these arms is degenerate on the recorded evidence.
- **Design position (decided 2026-09-27, user, D-2: DROP; proposal
  AC-5 updated accordingly):** the `f_eff` column SHALL be dropped for
  the HDC and LB arms in the corrected record (values retained only as
  historical/frozen-nominal beside the original labels), and
  block-level denominators (blocks_done, fails, undetected, FER(block))
  SHALL be kept as columns fully separate from superframe-level
  denominators (sf_success/sf_total, superframes_done), never merged.
  The rejected keep option is recorded as considered-and-rejected
  (reason: unit-incompatible NB-slope scales; degenerate
  zero-success evidence). If any `f_eff` is ever reintroduced for
  these methods, it SHALL be
  defined as a method-specific, unit-consistent efficiency under a new
  preregistration — the frozen NB slope SHALL NOT be reused silently.
- The adjudication's follow-up descriptive reaggregation (HDC
  superframes containing ≥1 recorded block-level `undetected`: 205/205,
  287/287, 383/383; LB: 137/142 of 205, 152/154 of 287, 223/234 of 383;
  `MAIN_ADJUDICATION_20260926.md` follow-up section) belongs to the
  recorded 64-bit-per-block verification and SHALL NOT be read as a
  prediction about a hypothetical single-tag protocol.

## 5. Backend provenance UNKNOWN (finding e)

- The three M2 roots contain no `backend_used` in any per-block row or
  arm summary (`grep -c backend_used` = 0; `RESULT.md` §7 item 2), and
  no backend sidecar, stdout, or resource transcript exists in them
  (adjudication stored-provenance follow-up). The LB adapter
  (`m2real_runner.py` lines 857–881) may run true binary SPA
  (`spa_decode_production` when the package is present) or the numpy
  min-sum fallback. The synthetic LB batch documented min-sum fallback
  (decision-log 2026-09-25 entry), but that does not prove the real
  run's backend.
- **Definition:** the real LB backend is **UNKNOWN** — not inferred from
  what is installed now, not carried over from the synthetic batch.
  The corrected record SHALL print `backend_used = UNKNOWN (not
  recorded at execution; not inferable post hoc)`.
- **Future persistence (separately frozen DECIDE run only):** to make
  backend recoverable, a future run SHALL persist at execution time, per
  root: (i) per-block `backend_used` string naming the entered decode
  body (e.g. `spa_decode_production` vs `numpy-minsum-fallback`) in
  `block_accounting.csv` and `rows.json`; (ii) one
  `backend_used.sidecar.json` per root recording package presence,
  selected branch, and construct/decode function identity (precedent:
  the synthetic LB `backend_used.sidecar.json`); (iii) the stdout
  transcript including the terminal END/exit state; (iv) wall/RSS
  resource record. Reconstruction from the current environment after
  the fact is explicitly NOT acceptable provenance.

## 6. Method identity and HDC verification-path void (finding f, as extended by the M2-HDCASCADE-SYNTH batch-end review)

HDC uses assumed-v1 Gray/block/pass parameters (`[8,4]` schedule,
cross 1, floor 1, max_passes 4; `m2real_runner.py` lines 151–155;
`require_assumed_block_table` guard), not a source-verified Müller
implementation (`PREREG_AND_AUTH.md` §1; `m2real-runner/design.md` §2).
The corrected record SHALL carry `block_table_status =
provisional (assumed-v1)` on every HDC number. Any HDC figure describes
this implementation only — a standing scope limit, not a ranking of
the named method family.

Independently and additionally, the implemented HDC production
verification path **cannot return success**: `_run_planes_production`
unconditionally returns `"accepted": True, "toeplitz_verified": False`
(`comparison_bench/src/comparison_bench/methods/hd_cascade.py:224–229`),
so the unified gate at `:280–281` (`success = exact and verified and
accepted`; `und = accepted and not success`) yields `success=False,
undetected=True` for every production block regardless of decode
quality — even a perfectly corrected block is recorded `undetected`.
`m2real_runner.py:491` calls the same entrypoint
(`hc.run_hd_cascade(batch, cfg, params=params, ...)`), so every HDC
success / FER / undetected value in any artifact (synth or real) is a
**structural stub artifact and is void as a measurement**. The
`leak_EC` disclosure column is a different matter: it is summed from
real cascade work in `_cascade_lite._run_frame_cascade` stats
(`hd_cascade.py` around `:200–223`), so it measures communication cost
under the assumed schedule on a non-functional verification path — not
a method ranking, and HDC's apparent `f_ec_actual` of roughly 9.8–10.2
SHALL NOT be presented as "HD-Cascade is 8x worse than NB-LDPC".
Authority: `docs/research_cycles/M2-HDCASCADE-SYNTH/BATCH_END_REVIEW.md`
§§2–4 (B1, H1–H2). This two-part limit (assumed-v1 parameters AND void
verification path) is a standing limit attached to every HDC number
wherever it appears.

**Update — measured zero-correction (2026-09-27; design §11):** a
read-only count over the three real M2 T3 roots'
`block_accounting.csv` finds `exact_match = 0` in every one of the
28,000 HDC blocks (per-arm counts in §11); the synth batch agrees
(`exact_match = False` for all 13 blocks in each of its 6 arms). The
implementation therefore corrected nothing on any real block in
either artifact. The HDC `leak_EC` column is consequently ALSO void
as a method quantity (status `void-no-correction`, §11; §10.1 column
(b)): it is the accumulated disclosure of the assumed-v1 schedule
run to exhaustion on blocks it never fixed — an upper bound on a
non-working configuration, not HD-Cascade's reconciliation cost — and
SHALL never appear in a cross-method ranking. The stub verifier
(MAC-6 / `void-stub-artifact`) hid this; the `exact_match = 0` count
is what makes it visible.

## 7. D2 RETIRED FOR M2 (decided D-3, 2026-09-27; finding g)

- The frozen D2 rule (decision-log 2026-09-24: (1) HDC de-tagged f beats
  NB by > 0.05; (2) layered-binary ≥ NB on f; (3) otherwise NB enters
  M3; `0.05` frozen, change = new packet) was evaluated against the
  wrong f, and the first review (`INDEPENDENT_ACCEPTANCE.md` §3) added
  an unstated LB-FER condition to branch (2) — rejecting it on FER
  although the frozen text conditions on f only. The frozen text
  governs; the added condition is not part of the rule.
- D2 branch evaluation is RETIRED for M2 (decided 2026-09-27, user,
  D-3; scoped to M2 only). Options (i) re-evaluate on
  actual-disclosure f and (ii) freeze a new rule are recorded as
  considered-and-rejected: D2 has no valid input in M2 (the displayed
  f was not actual disclosure, the tag unit is undecided per deferred
  D-1, the HDC arm cannot be evaluated at all, and the real LB backend
  is UNKNOWN). Routing proceeds via the independent M0/P1 measured gap
  instead; the retirement is not a statement that the comparison
  question is unanswerable forever.
- This change sets no revised D2 rule, and its record SHALL evaluate
  no D2 branch and report no D2 branch outcome.
  Any revised rule or comparison metric requires a NEW preregistration
  before any claim-bearing evaluation — including the observation that
  NB-side actual disclosure is itself unavailable: M0 `rows.json` has
  no recorded `leak_EC` or tag-event ledger (adjudication follow-up),
  so a three-method actual-disclosure D2 is not constructible from
  stored artifacts at all.
- **HDC exclusion from D2 (per the M2-HDCASCADE-SYNTH batch-end
  review):** D2 SHALL NOT be evaluated with the HDC arm at all in its
  current state, and the HDC column of the same-data comparison table
  CANNOT be filled from existing artifacts. The appearance of HDC
  disclosure being several times NB's nominal f is a property of an
  assumed schedule on a non-functional verification path, not evidence
  about the method family (see §6, §9 choice 6, §10).

## 8. Status-column discipline (finding h)

Per `AGENTS.md` §5.5, `reference` / `stub` / `unavailable` /
`decode_failed` / `no_verified_success` SHALL never be silently
converted to `ok`, and `undetected` (as `accepted_wrong`) is never
merged into success or FER numerators. Every recomputed column SHALL
carry an explicit status from this closed vocabulary:

| Status | Meaning |
|---|---|
| `measured-corrected` | recomputed from recorded `leak_EC` / tag bits in persisted summaries |
| `historical-nominal` | frozen `(5m(+64))/(1024·H)` formula display, retained for discrepancy display |
| `counterfactual` | one-tag-per-superframe arithmetic; not an executed protocol |
| `not-defined` | `f_eff` for HDC/LB arms if main drops it (no value printed) |
| `unknown` | LB `backend_used` (and any other unrecoverable provenance) |
| `assumed-v1` | HDC Gray/block/pass pins |
| `void-stub-artifact` | HDC success / exact_match / FER / undetected values from the production path that cannot return success (design §6; code cite `hd_cascade.py:224–229`, `:280–281`) — void as measurements, never quoted as method data |
| `void-no-correction` | `leak_EC` and every quantity derived from it (`f_ec_actual`, `f_with_recorded_tags`, `f_one_tag_CF`, tag-inclusive totals, messages-as-efficiency) for a recorded arm whose full block set shows no correction: HDC `exact_match = 0` of 28,000 (design §11); Layered-Binary 36 of 28,000 (0.13%), no arm above 12 of 3280 (0.37%), block FER 0.9963–0.9995 with superframe success necessarily zero (design §14) — the disclosure cost of a schedule run to exhaustion on effectively uncorrected blocks, void as a method quantity, barred from cross-method ranking. The bar is the recorded run's failure to correct, stated with the counts that trigger it; the status is a property of the recorded run, not of the method family |
| `suspended` | any D2 branch cell |
| `retired-m2` | D2 branch cells for M2 (evaluation retired by decided D-3, 2026-09-27; never evaluated or reported; rejected options recorded) |

## 9. Interpretation choices (artifacts contradict each other)

Where the existing artifacts disagree, this design chooses as follows
(file and line for each choice):

1. **`RESULT.md` §3 vs §2 on tag scope.** §3 (`RESULT.md` line 65)
   writes `λ_total = leak_EC + 64-bit tag` (singular), but the §2
   `λ_total` values (lines 32–35, e.g. 1,917,405.000) equal recorded
   `leak_EC` + `64·blocks_done` (1,707,485 + 209,920). Choice: the
   printed numbers govern — the run accumulated the recorded 16-tag
   total — and the singular text label is the defect. Both totals are
   therefore carried with distinct labels per §1.
2. **First review §3 vs frozen D2 text on branch (2).**
   `INDEPENDENT_ACCEPTANCE.md` lines 44–45 reject branch (2) partly on
   LB FER, while the frozen rule (decision-log lines 4967–4970)
   conditions branch (2) on f only ("f 更优或持平"). Choice: frozen
   text governs; the FER condition is unstated and the branch (3)
   declaration built on it is suspended with everything else (prior
   state; retired for M2 per decided D-3 — see §7, §13).
3. **A-CMPE-3 single-tag `λ_total` vs M2 recorded tags.**
   `SAME_DATA_CMP_METRICS.md` §3 item 1 mandates `λ_total = leak_EC +
   64` (single tag) for the NB superframe protocol. Applied verbatim to
   M2 arms it would silently substitute the counterfactual for the
   recorded bookkeeping. Choice: A-CMPE-3 applies to M2 only through
   §1–§3 of this design (both totals shown, one-tag labelled
   counterfactual); the single-tag form is not the M2 primary.
4. **A-CMPE-2 dual `f_super`/`f_eff` vs M2 FER units.**
   `SAME_DATA_CMP_METRICS.md` §2 / proposal A-CMPE-2 require dual
   reporting with the arm's own m basis — written against NB
   superframe-scale FER. Choice: the dual-reporting obligation is met
   by retaining the original pair as `historical-nominal` while the
   primary record drops (or, only by main decision, redefines) `f_eff`
   per §4. Quoting the frozen NB-slope `f_eff` as an M2 efficiency is
   the defect, not the omission.
5. **M0 nominal f vs any actual-disclosure comparison.** The M0/V80
   frozen `(5m+64)/(1024·H)` is a nominal formula, not observed
   disclosure (adjudication follow-up: no `leak_EC`/tag ledger in M0
   `rows.json`). Choice: no NB actual-disclosure column is constructed
   from stored artifacts; any fair three-method claim needs separately
   gated DECIDE execution with contemporaneous disclosure provenance.
6. **HDC `undetected = blocks_done` is a structural stub artifact, not
   a labelling matter (CORRECTED per the M2-HDCASCADE-SYNTH batch-end
   review; supersedes the earlier "retained as labelling" reading).**
   `_run_planes_production` unconditionally returns `"accepted": True,
   "toeplitz_verified": False`
   (`comparison_bench/src/comparison_bench/methods/hd_cascade.py:224–229`),
   so the unified gate at `:280–281` forces `success=False,
   undetected=True` for every production block. `m2real_runner.py:491`
   calls the same entrypoint, so the real-data M2 HDC arm's success /
   exact_match / FER / undetected columns are structurally meaningless,
   not measured. The synth batch's `13/13` per arm and the real batch's
   `205/205, 287/287, 383/383` superframes-with-`undetected` have the
   same single cause. The HDC `leak_EC` column remains a real
   communication-cost measurement under the assumed-v1 schedule
   (`hd_cascade.py` around `:200–223`), but conditioned on a path that
   can never report success. Authority:
   `docs/research_cycles/M2-HDCASCADE-SYNTH/BATCH_END_REVIEW.md` §§2–4.
   (See Appendix S ceiling).
   Update (2026-09-27; §11): the measured `exact_match = 0` count over
   all 28,000 real HDC blocks (synth: 0 of 78 corrected) additionally
   voids the HDC `leak_EC` column as a method quantity
   (`void-no-correction`); of the HDC numbers, only the negative
   result and the schedule configuration remain citable (§10.1).

## 10. Known void columns (per-source artifact table)

Authority for every row: code cite
`comparison_bench/src/comparison_bench/methods/hd_cascade.py:224–229`
(unconditional `accepted=True, toeplitz_verified=False`) with the
`:280–281` gate, and
`docs/research_cycles/M2-HDCASCADE-SYNTH/BATCH_END_REVIEW.md` §§2–4
(B1, H1–H2). M2-LB's disposition ("retained-assumed, no promotion")
and the real-LB unknown-backend limit (design §5) are intact and
unchanged by this table.

| Source artifact | Void columns (status `void-stub-artifact`; SHALL NOT be quoted as measurements) | Still-usable columns (with their standing limits) |
|---|---|---|
| M2 synth HDC 6 arms (`workspace/m2hdc_3c0f660c\|a1b2c3d4\|e5f60718\|9a8b7c6d\|5e4f3a2b\|c1d2e3f4`, `block_accounting.csv` + `rows.json`) | `success`, `exact_match`, `accepted`, `undetected` (=13/13 per arm), `block_fail`, any FER derived from them, `f_eff ≈ 6.06–6.09`, λ/messages columns as quality signals, `N_req` | `leak_EC` disclosure bits (measured cascade communication cost under assumed-v1 schedule only); execution-boundary facts (frozen seeds, bar-12 CENSORED stops, `nb_decode_calls=0`, budget); the batch as a harness-defect exhibit per review §4 |
| M2 real HDC T3 roots (`workspace/m2real_d4e5f6a7`, `workspace/m2real_b8c9d0e1`, `workspace/m2real_f2a3b4c5`, HDC arms) | `success` / `exact_match` / block FER / `undetected` columns and the adjudication's follow-up reaggregation (HDC superframes with ≥1 recorded `undetected`: 205/205, 287/287, 383/383) as method data; any `f_eff` on these arms | `leak_EC` (`E`) and `lambda_parts.tag` (`T`) stored disclosure arithmetic → `f_ec_actual` / `f_with_recorded_tags` as recorded-implementation diagnostic ratios only (design §2 caveat; NOT method efficiencies, NOT cross-method rankings) |
| M2 real LB T3 roots (same three roots, LB arms) | Nothing voided by this review | Unchanged: `f_ec_actual` measured under UNKNOWN backend (design §5); `undetected` isolated per A-CMPE-1; "retained-assumed, no promotion" disposition stands |

### 10.1 Zero-correction split (2026-09-27; supersedes the HDC "Still-usable" cells of the §10 table)

The §10 table stands for the stub-verifier void. This subsection
additionally applies the measured zero-correction fact (§11). Per HDC
artifact, three separately-labelled column groups:

| Source artifact | (a) `void-stub-artifact` columns | (b) `void-no-correction` columns | (c) Usable remainder |
|---|---|---|---|
| M2 synth HDC 6 arms | `success`, `exact_match`, `accepted`, `undetected` (=13/13 per arm), `block_fail`, any FER derived from them, `f_eff`, λ/messages columns as quality signals, `N_req` | `leak_EC` and any disclosure ratio derived from it; messages as an efficiency signal | Only the existence of the negative result (0 of 78 blocks corrected under the frozen assumed-v1 schedule) and the schedule configuration itself |
| M2 real HDC T3 roots (all three; HDC arms, both m per source) | `success` / `exact_match` / block FER / `undetected` columns and the adjudication's follow-up reaggregation (205/205, 287/287, 383/383) as method data; any `f_eff` on these arms | `leak_EC` (`E`) and everything derived from it: `f_ec_actual`, `f_with_recorded_tags`, `f_one_tag_CF`, tag-inclusive totals, messages-as-efficiency | Only the existence of the negative result (0 of 28,000 blocks corrected under the frozen assumed-v1 schedule) and the schedule configuration itself |

Supersession: the HDC "Still-usable columns" cells of the §10 table
(which admitted `leak_EC`-derived diagnostic ratios) are superseded
by column (b) above. The M2 real LB row of the §10 table is
unaffected and stands unchanged.

### 10.2 Layered-Binary rows (2026-09-27; supersedes the §10 LB row's disclosure cells)

The §10 LB row ("Nothing voided"; "`f_ec_actual` measured under
UNKNOWN backend") predates the §14 count and is superseded on
disclosure only. Per LB artifact, the same three groups as §10.1:

| Source artifact | (a) `void-stub-artifact` columns | (b) `void-no-correction` columns | (c) Usable remainder |
|---|---|---|---|
| M2 real LB T3 roots (all three; LB arms, both m per source) | None — explicitly NOT applicable. LB's verification path functions (1M/m197: 3268 of 3280 rejected, 215 `undetected`); its `success` / FER / `undetected` columns are real measurements of genuine failure (§14) | `leak_EC` (`E`) and everything derived from it: `f_ec_actual`, `f_with_recorded_tags`, `f_one_tag_CF`, `lambda_total`, message counts as efficiency signals | Usable as diagnostics of a non-working implementation only: the structural identities (`blocks_done = 16·superframes_done`, `tag = 64·blocks_done`), the stored arithmetic, the block/superframe denominators, the `undetected` isolation, and the per-arm block counts (36 of 28,000 exact). No method quantity does — no comparison column can be filled for LB either |

The §10 LB row's backend clause stands: `backend_used = UNKNOWN`
(design §5); D-5 authorises a parallel read-only trace for a
surviving backend trace, which refines but never withdraws the
negative finding.

## 11. Measured zero-correction fact (2026-09-27)

- **Method of count (checkable without rerunning anything):** read
  column `exact_match` in each root's `block_accounting.csv`, restricted
  to the `hdc` family, both m arms per source. Fact relayed via main;
  the operator ran no reader over the T3 roots and opened no `.ttbin`.
- **Counts:** 1M (`workspace/m2real_d4e5f6a7`): m=197 and m=201, 3280
  blocks each; 1.5M (`workspace/m2real_b8c9d0e1`): m=203 and m=207,
  4592 blocks each; 2M (`workspace/m2real_f2a3b4c5`): m=204 and m=208,
  6128 blocks each. `exact_match = 0` in **every one of the 28,000
  blocks** (6560 + 9184 + 12256). In the same rows `accepted = n`,
  `undetected = n`, `accepted_wrong = n`.
- **Synth corroboration:** `exact_match = False` for all 13 blocks in
  each of the 6 synth arms (78 blocks), per
  `docs/research_cycles/M2-HDCASCADE-SYNTH/BATCH_END_REVIEW.md` §§2–4.
- **Status defined:** `void-no-correction` (vocabulary §8) applies to
  HDC `leak_EC` and every quantity derived from it for these arms. The
  disclosure is the accumulated cost of the assumed-v1 schedule
  (uniform [8,4] blocks, max_passes 4, one cross-plane sweep) run to
  exhaustion on blocks it never fixed: an upper bound on a
  non-working configuration, not HD-Cascade's reconciliation cost.
- **Verifier consequence:** wiring a real Toeplitz verifier (D-4
  option ii) does not change any number — `exact_match` stays 0,
  `leak_EC` stays as measured, block FER stays 1.0; it relabels the
  `undetected` column from "false accept" to "failed verification" at
  the cost of a new real-data DECIDE execution (fresh root, own
  preregistration, own grant).
- **What a citable number needs:** a cascade that actually converges
  on this channel — a real verifier AND parameters/schedule that
  correct blocks. That is a research sub-project, not a patch, and is
  recorded here as such without being designed.

## 12. Claim-scope observation for main (not a decision)

- `docs/NOW.md` §2 records G0=(B), decided 2026-09-22: the headline
  claim is a measured efficiency curve plus a same-data **binary**
  MLC/R3 comparison; option (A) literature-comparable certification
  continues as a parallel/second-generation extension.
- `docs/RESEARCH_DIRECTION_REPORT_20260924.md` §0 item 1 and §5
  describe the endpoint as a table of three methods (NB-LDPC /
  layered-binary / HD-Cascade) × four numbers on the same real
  frames.
- With HDC void under both void labels, the deliverable this line
  can actually produce is a **two-method table plus one documented
  negative implementation result** — which is *closer* to G0=(B)
  (binary comparison), not further from the paper goal. The
  three-method table of the direction report remains the stated
  endpoint, but its HDC column cannot be filled from any existing
  artifact (MAC-9) and filling it needs the §11 research
  sub-project, not an accounting choice.
- Update (decisions 2026-09-27): with D-4=(iii) the deliverable is
  settled as a two-method same-data table (NB-LDPC vs Layered-Binary)
  plus one documented negative implementation result for HD-Cascade.
  D-1's deferral means the Layered-Binary tag column is reported with
  all totals carried distinctly rather than with a single headline f;
  if the user later fixes D-1, the Layered-Binary headline number
  changes but no already-published column does. D-2 (DROP) and D-3
  (retire D2 for M2) are recorded in §13; this note remains an
  observation, not a decision.
- Supersession (2026-09-27, LB count + decided D-5; earlier text
  above retained as the pre-count belief): with LB void under
  `void-no-correction` (36 of 28,000 exact, §14, MAC-10), the
  two-method table is no longer available. The deliverable is **one
  working method plus two documented negative implementation
  results** (HD-Cascade per D-4(iii), Layered-Binary per D-5(i)),
  and no comparison column can be filled for either baseline. This
  moves the endpoint *closer* to the G0=(B) headline claim (measured
  efficiency curve plus same-data binary comparison), not further:
  the surviving citable comparison is the binary one G0=(B) names.

## 13. User decisions recorded 2026-09-27 (decision-record)

Decided by the user, relayed by the main thread. D-2/D-3/D-4 are
frozen; D-1 is the single open item (non-blocking for T0, §13 first
bullet). Rejected options are recorded as considered-and-rejected
with reasons, per decision-log discipline — none is deleted.

- D-1 (tag verification unit): DEFERRED. The user will not pick a
  unit by inference from code. It does not block T0: all tag totals
  are carried distinctly and D-1 decides only the headline column.
  Settling evidence, when it comes, is a frozen protocol
  specification, not a code reading.
- D-2 (`f_eff` for HDC/LB): DROP. HDC/LB artifacts carry no `f_eff`
  (MAC-4, §4); reintroduction needs a NEW preregistered
  method-specific, unit-consistent definition, and the NB slope may
  never be silently reused.
- D-3 (D2 rule): RETIRE D2 FOR M2 (option iii). No D2 branch is
  evaluated or reported (MAC-7, MAC-9, §7); options (i)/(ii) rejected
  for lack of valid input; routing via the M0/P1 measured gap; scoped
  to M2 only.
- D-4 (HD-Cascade column): option (iii). HDC is a documented negative
  implementation result with both void labels on every HDC number
  (MAC-6, MAC-9, §10.1); option (ii) considered and recorded as a
  non-repair (relabel only, no value changes); a citable number needs
  a converging cascade, a research sub-project outside this change.
- D-5 (Layered-Binary disclosure): decided 2026-09-27 (user,
  relayed by main; verbatim acceptance recorded in the tasks.md
  decided-status block) as option **(i) plus (iii) in parallel**. (i) LB is
  reported as a documented negative implementation result with
  `void-no-correction` on its disclosure and every derived column
  (MAC-10, §10.2, §14), exactly parallel to D-4(iii) for HD-Cascade.
  (iii) A read-only trace for contemporaneous backend provenance is
  authorised in parallel — no redecoding, no new execution, only a
  search of the three M2 roots and adjacent records for any surviving
  backend trace. Option (ii) — retaining the disclosure as a bare
  diagnostic without the void label — was considered and rejected:
  it is the reading that invites the ranking this change exists to
  prevent. (i)+(iii) is operative: (iii)'s outcome does not change
  (i) either way — if a backend trace is found, the finding is
  refined, not withdrawn.

Pipeline consequences: T1 carries no `f_eff`, fills no HDC
comparison column, reports no D2 branch, and infers no backend; T3
checks the retirement, both void labels, and the D-1-non-blocking
tag chain; T4 records D-1 open and D-2..D-5 decided (see tasks.md
decided-status block).

## 14. Layered-Binary near-zero-correction fact (2026-09-27)

- **Method of count (checkable without rerunning anything):** main's
  own read-only recount of column `exact_match` in each T3 root's
  `block_accounting.csv`, filtered to the `lb` family, both m arms per
  source, 2026-09-27. The operator ran no reader over the T3 roots
  and opened no `.ttbin`.
- **Counts:**

  | source / m | blocks | exact | block FER |
  |---|---|---:|---:|
  | 1M 197 | 3280 | 12 | 0.996341 |
  | 1M 201 | 3280 | 7 | 0.997866 |
  | 1.5M 203 | 4592 | 5 | 0.998911 |
  | 1.5M 207 | 4592 | 6 | 0.998693 |
  | 2M 204 | 6128 | 3 | 0.999510 |
  | 2M 208 | 6128 | 3 | 0.999510 |

  **36 of 28,000 blocks, 0.13%.** Block FER 0.9963-0.9995, so
  superframe success is necessarily zero. Contrast: HDC
  `exact_match = 0` of 28,000 (§11).
- **Critical distinction — `void-stub-artifact` does NOT apply to
  Layered-Binary.** At 1M/m=197 LB rejected 3268 of 3280 blocks and
  recorded 215 `undetected`, so its verification path functions and
  rejects wrong data: it is a weak decoder on an unsuitable channel,
  not a hardcoded gate. LB's `success` / FER / `undetected` columns
  are real measurements and they record a genuine failure — this
  finding is not softened. Only `void-no-correction` extends to LB:
  its `leak_EC` is the disclosure of a run that corrected
  effectively nothing, void as a method quantity (§10.2, MAC-10).
  Do not attribute HDC's defect to LB, and do not soften LB's
  finding either.

## 15. Displayed-f structural blindness (confirmed by T2/T3, 2026-09-27)

Main confirms from T2 (AC-3, 12/12 bit-exact) and T3 (Pre-RESULT
PASS_WITH_FINDINGS, zero blocking): the displayed nominal columns
never read `leak_EC` — `f_notag = 5m/(1024·H)` depends only on
`(m, H)` — so the cross-family equality of the displayed f is
mechanically forced, and the displayed f was structurally incapable
of distinguishing methods. At 1M/m=197 the recorded leak differs by
2.64x (1,707,485 vs 646,160 bits) while both arms display
1.20048829. Also genuine, T2-verified: LB's recorded leak rose by
exactly `64·205 = 13120` between m=197 and m=201, which is why
1M-lb-m201 `f_ec_actual` equals 1M-lb-m197's one-tag value — it is
an identity, not a transcription error.

## Appendix S — Scope of the M2-HDCASCADE-SYNTH batch-end review (REVIEW NOW FILED — see note; scoping text below retained for provenance)

> **Status note (2026-09-27):** the independent batch-end review has
> since been filed at
> `docs/research_cycles/M2-HDCASCADE-SYNTH/BATCH_END_REVIEW.md` and
> returned **FAIL** (B1: the production verification path cannot return
> success; all headline numbers are harness artifacts). Design §9
> choice 6, §6, §7, §10 and spec MAC-6/MAC-9 record its consequences.
> The scoping text below is retained unchanged for provenance; where it
> says "missing / not yet produced", read as "as scoped before filing".

This section scopes the review; it does not perform it. The reviewer
must be an independent thread that did not execute the batch.

- **Batch identity:** `G-M2-HDCASCADE-SYNTH`, Track EXPLORE (synthetic
  only), one authorization covering frozen arms A1→A6 (LOG entry 1,
  2026-09-25). Evidence: `docs/research_cycles/M2-HDCASCADE-SYNTH/EXPLORATION_LOG.md`
  (append-only; entry 0 Pre-EXECUTE, entry 1 execution), `PACKET.md` (§7
  authorization boundary, pin snapshot assumed-v1 verbatim), six roots
  `workspace/m2hdc_3c0f660c|a1b2c3d4|e5f60718|9a8b7c6d|5e4f3a2b|c1d2e3f4`
  × 3 files each (`M2HDC_RESULT_*.md` + `rows.json` +
  `block_accounting.csv`).
- **Recorded outcome:** all 6 arms terminated `FAIL-early-stop
  (CENSORED)` with `undetected = 13/13` — 100% false accept in the
  production decode path on the first 13 synthetic blocks, triggering
  the bar-12 early stop (LOG entry 1, arms table lines 42–48; G-A/B/C
  tallies there). No repair path used. No batch-end review was ever
  produced (LOG line 53: "batch-end review: 未做").
- **The independent batch-end reviewer SHALL check:** (i) the
  authorization boundary — the single 2026-09-25 grant covers exactly
  A1→A6 at N=240 and the frozen command/bundle/seeds/flags match LOG
  entry 1; (ii) machine gates — bar-12 `FAIL-early-stop (CENSORED)` is
  the packet's expected G-A verdict semantics, not a method
  falsification, and is applied consistently across all 6 arms with no
  pooling to 240 and no cross-arm merge; (iii) retained failures — all
  six CENSORED stops retained in their roots, zero repair used, zero
  INCOMPLETE-wall, zero budget FAIL; (iv) the `undetected = 13/13`
  isolation — `accepted_wrong` in its own column, never merged into
  success/FER, with the production-decode-path false-accept phenomenon
  recorded as phenomenon, not explained away; (v) backend provenance
  for the synth HDC decode path as recorded at execution (no post hoc
  inference); (vi) A-CMPE machine columns present per arm
  (`block_accounting.csv`) with the provisional/assumed message-formula
  and assumed-v1 pins labelled; (vii) the packet claim ceiling
  ("合成探针不替代不预示任何真实 FER/效率/泄漏/SKR") present verbatim
  in all six RESULT mds.
- **Claim ceiling for that review:** the batch is a synthetic probe on
  a single construction instance with assumed-v1 pins. Citable at most
  as: "under the frozen assumed-v1 HDC configuration, the first 13
  synthetic blocks of each of 6 arms false-accepted in the production
  decode path, causing bar-12 CENSORED stops; no repair was used."
  The review SHALL NOT promote, select an operating point, rank
  families, or state or imply any real-data FER, efficiency, leakage,
  SKR, qualification, or publication conclusion. The 100% false-accept
  observation SHALL be foregrounded before any future HDC real-data
  proposal relies on this path; whether that blocks or conditions such
  a proposal is a main-thread decision, not a finding of this scope.
