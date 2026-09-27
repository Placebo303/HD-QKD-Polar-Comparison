# M2 accounting correction — CORRECTION_INDEPENDENT_ACCEPTANCE (T3 review + T4 acceptance)

- Track: **DECIDE**.
- Change: `openspec/changes/m2real-accounting-correction/` (spec MAC-1..9, design §§1–13, tasks T0–T4).
- Record under review: `docs/research_cycles/M2-REALCOMP/CORRECTION_RESULT.md` (T1).
- Recomputation check: `docs/research_cycles/M2-REALCOMP/CORRECTION_RECOMPUTE_CHECK.md` (T2, AC-3 PASS 12/12 bit-exact).
- Authority: `docs/research_cycles/M2-REALCOMP/CORRECTION_PREREG_AND_AUTH.md` (T0 gate PASS, §9.1 main-thread sign-off 2026-09-27; grant 「1 → 3 → 2可以」 on file).
- Branch: `formal-ir-v72p1-addendum-clean`. Date: 2026-09-27.
- **This file ran no decoder, no construction, no scientific command; opened no `.ttbin` and no channel bundle.** Part A is the independent review thread's return, filed as returned; Part B is the main-thread acceptance. Until Part B was signed, no corrected number was citable beyond the record itself; the original M2 scientific acceptance stays WITHHELD.

---

## PART A — T3 independent Pre-RESULT review (filed as returned)

# Independent Pre-RESULT Review — M2 Accounting Correction (tasks.md T3)

**Reviewer stance:** independent thread; findings only, no patches. **Verdict: PASS_WITH_FINDINGS** — all findings are non-blocking. Main may proceed to T4, with the limitations in §6.

**Scope note:** T3 acceptance per tasks.md is "AC-4 first half". This review covers frozen-packet thresholds, formulas, decomposition, `undetected` isolation, per-source separation, disclosure accounting, tag/counterfactual labelling, FER separation, backend stance, HDC scope + MAC-9, D2 retirement, status discipline, A-CMPE scoping, claim ceiling, provenance, and T2 consistency. T4 (main+user acceptance) is still required; until it is signed no corrected number is citable beyond the record itself.

## 1. Per-item table A–P

| Item | Verdict | One-line evidence |
|---|---|---|
| A. Thresholds & formulas | PASS | Record §1 transcribes prereg §3 verbatim; subset re-derived below, all match (e.g. 1M HDC197 10.1513717934757, LB197 3.8415625308991053) |
| B. Leakage decomposition | PASS | C-2 carries E and T as separate columns; per-source H used; M0/V80 basis cited-not-copied; source rescue/control are 0.0 so E+T is complete (NB-9) |
| C. `undetected` isolation | PASS | Never merged into success/FER (:50-51, :79); sf-success zeros reported as recorded 0/205, 0/287, 0/383 (:74-75, C-2) |
| D. Per-source breakdown | PASS | 12 arms fully separate; no pooling across sources, families, or m; cross-family nominal equality explained as mechanical (:106, :181-182) |
| E. Disclosure accounting | PASS | `f_ec_actual` primacy carries the accounting-ordering-only caveat verbatim (:20-22); ranking barred in §5/§10/§11 |
| F. Tag-unit labelling | PASS | All three totals carried distinctly with correct statuses; §7 designates no headline; D-1 deferral honoured |
| G. Counterfactual labelling | PASS | Literal `COUNTERFACTUAL_ONLY` in every C-1 row and every §8 value; diagnostic field is `COUNTERFACTUAL_ONLY` in all 12 arms (NB-3 uniformity note) |
| H. FER-unit separation | PASS | 64-block FER denominator stated (:72); block vs superframe columns separate (C-2); `f_eff` = `not-defined` all 12 arms, originals kept as `historical-nominal` |
| I. Backend-UNKNOWN | PASS | All six LB arms carry `UNKNOWN (not recorded at execution; not inferable post hoc)` [`unknown`]; §9 rejects synth-carryover and current-env inference |
| J. HDC scope + MAC-9 | PASS | C-2 gives both void labels per HDC row + `assumed-v1` scope; §5 gives per-source counts 6560+9184+12256=28000 and 0/78 synth; no HDC comparison column, no D2-with-HDC (NB-1 C-1 header note) |
| K. D2 retirement | PASS | `retired-m2` declared, no rule/branch/report; rejected (i)/(ii) recorded with four-ground reason; M2-only scope (:159-167) |
| L. Status discipline | PASS | Closed vocabulary only; no silent `ok`; every column carries a status (NB-4 descriptive-cell note) |
| M. A-CMPE scoping (§9 choices) | PASS | All six design-§9 choices explicitly implemented; no silent adoption of either side; A-CMPE-2 deviation authorized by decided D-2 with gating |
| N. Claim ceiling | PASS | §10 verbatim vs prereg §10; no certification/ranking/SKR/qualification/publication content; §11 NOT-do list covers everything the record does |
| O. Provenance | PASS | Every figure names its source (:86, §5, §12); spot-checked against T3 roots directly, not merely self-consistent (NB-5/NB-6 notes) |
| P. T2 consistency | PASS | Record agrees with T2's 12/12 bit-exact table; coincidence mechanism independently verified — and it holds at all three sources, not just 1M |

## 2. Representative re-derivation (item A, shown inline)

Denominators: D(1M)=205·1024·0.8012690084416184=209920·0.8012690084416184=**168202.39025206454**; D(1p5M)=287·1024·0.8272902027770036=293888·0.8272902027770036=**243130.66311372805**; D(2M)=383·1024·0.8333327179427281=392192·0.8333327179427281=**326826.42531539442**. 1024·H: 1M **820.4994646442172**; 1p5M **847.1451676436517**; 2M **853.332703213354**.

- **1M HDC m197** (rows.json: E=1707485, T=209920, total 1917405=1707485+209920 ✓): `f_notag`=985/820.4994646442172=**1.2004882909059704** ✓; `f_super`=1049/820.4994646442172=**1.2784895605688964** ✓; `f_ec`=1707485/D=**10.1513717934757** ✓; `f_with`=1917405/D=**11.399392108082516** ✓; one-tag=(1707485+64·205)/D=1720605/D=**10.229373063138626** ✓ (64·205=13120 ✓).
- **1M LB m197** (rows.json: E=646160, T=209920, total 856080 ✓; fails 3268/3280=0.9963414634146341 ✓; undetected 215 isolated): 646160/D=**3.8415625308991053** ✓; 856080/D=**5.089582845505921** ✓; (646160+13120)=659280/D=**3.919563800562031** ✓. Hiding ratio 1707485/646160=2.6425…≈**2.64×** ✓.
- **1p5M HDC m203** (diag: E=2402144, T=293888): `f_notag`=1015/847.1451676436517=**1.1981417574785196** ✓; `f_super`=1079/847.145…=**1.2736896121372638** ✓; 2402144/D=**9.88005366841105** ✓; 2696032/D=**11.088819342950956** ✓; (2402144+64·287)=2420512/D=**9.955601523069793** ✓ (64·287=18368 ✓).
- **1p5M LB m203** (diag: E=932176): 932176/D=**3.8340536239312626** ✓; 1226064/D=**5.042819298471168** ✓; (932176+18368)=950544/D=**3.9096014785900066** ✓.
- **2M HDC m204** (rows.json: E=3205668, T=392192, total 3597860 ✓; fails=undetected=6128): `f_notag`=1020/853.332703213354=**1.1953133827015512** ✓; `f_super`=1084/853.3327…=**1.2703134380867467** ✓; 3205668/D=**9.808472484764543** ✓; 3597860/D=**11.00847337092767** ✓; (3205668+64·383)=3230180/D=**9.883472540149738** ✓ (64·383=24512 ✓).
- **2M LB m204** (diag: E=1250112): 1250112/D=**3.825002824644964** ✓; 1642304/D=**5.02500371080809** ✓; (1250112+24512)=1274624/D=**3.900002880030159** ✓.
- Structural: 3280=16·205; 4592=16·287; 6128=16·383 ✓. 209920=64·3280; 293888=64·4592; 392192=64·6128 ✓. `lambda_total`=E+T verified in root reads (1917405; 856080; 869200=659280+209920 ✓; 3597860) ✓.
- Coincidence mechanism (item P), all three sources: 659280−646160=**13120**=64·205 ✓ ⇒ record:93-96 `f_ec`(lb,201)=`f_one`(lb,197)=3.919563800562031 ✓; 950544−932176=**18368**=64·287 ✓ ⇒ `f_ec`(lb,207)=`f_one`(lb,203)=3.9096014785900066 ✓; 1274624−1250112=**24512**=64·383 ✓ ⇒ `f_ec`(lb,208)=`f_one`(lb,204)=3.900002880030159 ✓. Genuine arithmetic identities, not transcription errors. HDC leak is m-insensitive by contrast (Δ +196/−425/−517), consistent with the exhausted-schedule narrative (descriptive only).

## 3. BLOCKING findings

**None.** No formula error, no mislabelled status, no merged denominator, no pooled source, no inferred backend, no D2 evaluation, no ranking/SKR/qualification content, no provenance break. Nothing in this review blocks solidification; no revise-required is triggered.

## 4. NON-BLOCKING findings (each: location, why it matters, what it blocks → nothing)

- **NB-1 — C-1 column header over-covers HDC rows.** `CORRECTION_RESULT.md:91` labels the `f_ec_actual`/`f_with_recorded_tags` columns `measured-corrected` for all rows, but HDC rows' correct status is `void-no-correction` (correctly given in C-2 :116-127 and the :130 note + §5). Why it matters: a reader quoting C-1 alone could present HDC ≈9.8–10.2 as a validated measurement — the exact "8× worse" misreading MAC-9 bars. The in-record bars (§5, §6:166, §11:222-227) mitigate it. Suggest row-level void markers in C-1 pointing to C-2. Blocks: nothing (T4 may proceed).
- **NB-2 — "2.64×" sentence lacks a local guard.** `:185` states the HDC-vs-LB recorded-disclosure ratio as discrepancy exposition (legitimate), with only global not-a-ranking guards elsewhere. Suggest appending "not a method ranking" adjacent. Blocks: nothing.
- **NB-3 — Bare `f_one_tag_CF` mention.** `:150-151` lists `f_one_tag_CF` in body text without adjacent `COUNTERFACTUAL_ONLY` (strict MAC-3 uniformity; the table/caption/machine occurrences all carry it). Suggest appending the label. Blocks: nothing.
- **NB-4 — Descriptive cells vs vocabulary statuses.** C-2 LB cells read "(LB: nothing voided; `undetected` isolated)" and HDC backend cells read "— (…`assumed-v1` scope…)" — accurate, but neither is a §4-vocabulary token. Suggest one line clarifying LB block counts are transcribed recorded values and the HDC backend cell is not-applicable + scope. Blocks: nothing.
- **NB-5 — Line 8 vs §12 provenance standing.** `:8` quotes the embedded `DIAGNOSTIC_UNREVIEWED` string while `:234-236` states reviewed PASS for stored disclosure arithmetic (prereg §2 I-4 agrees). Suggest one line reconciling (embedded string predates the replay PASS). Blocks: nothing.
- **NB-6 — 28,000-count authority.** `:145-149` presents the `exact_match = 0` count over `block_accounting.csv` with root names and per-arm counts (verifiable as stated), but does not repeat design §11's "relayed via main; operator ran no reader" nuance at the count itself (authority reaches it via §12:236-237 + design §11). Suggest citing the adjudication superseding note at the count. Blocks: nothing.
- **NB-7 — M5 four-column mapping implicit.** MAC-8's measured/assumed/projected/qualified attribution is satisfied functionally via per-column statuses, but no literal mapping sentence exists. Suggest one line mapping the M2 vocabulary onto M5. Blocks: nothing.
- **NB-8 (observation) — LB per-arm `undetected` counts not tabulated.** They exist in rows.json (1M: 215/227, read directly) and stay isolated, satisfying this record; the future two-method table will need them as an independent A-CMPE-1 column. No action for this record.
- **NB-9 (observation) — rescue/control are 0.0** in every rows.json arm read, so the E+T decomposition is complete with nothing merged away. No action.

## 5. Two-method table question

**Is the record sufficient to fill an NB-LDPC (M0) vs Layered-Binary (corrected M2) same-data table? Answer: it supplies the LB half as storeable diagnostics, but it is not sufficient to fill — or to draw — the comparison by itself.**

- LB side usable: per-source `f_ec_actual`, `f_with_recorded_tags`, counterfactual one-tag, block FER, and zero sf-success — each permanently coupled to `backend_used = UNKNOWN`, no `f_eff`, three tag totals with no headline (D-1 deferred), and block-vs-superframe units kept separate. Note additionally that LB block FER is 0.996–0.9995 (rows.json fails/blocks confirm), so the LB arms also corrected almost nothing at 64-block granularity.
- NB side missing: M0 `rows.json` has no `leak_EC`/tag-event ledger (design §9 choice 5; record §11:230), so **no NB actual-disclosure column can be constructed from stored artifacts**. Only the nominal frozen formula exists, under F9(i) "u2-only, u1 via argmax, u1 正确率未验证".
- Therefore such a table **may** at most juxtapose recorded-implementation LB disclosure diagnostics against nominal NB figures with every scope label attached (UNKNOWN backend; u2-only; no headline tag; no `f_eff`; no pooling), and **may not** claim method superiority, validated efficiency, efficiency certification, SKR, a D2 verdict, or a headline LB number. Any comparison metric needs a NEW preregistration first (MAC-7).

## 6. Exact DOES / DOES-NOT lists

**The record DOES support stating:**
1. Per-arm stored disclosure arithmetic (E, T, D, `f_ec_actual`, `f_with_recorded_tags`, counterfactual one-tag) as recorded-implementation diagnostics with the stated statuses.
2. The discrepancy mechanism: displayed nominal columns never read `leak_EC` (1M/m197: 1.20048829 both arms vs actual 10.15137 HDC / 3.84156 LB; inclusive 11.39939 / 5.08958; counterfactual 10.22937 / 3.91956).
3. Structural identities (`blocks_done`=16·`superframes_done`; tag=64·`blocks_done`; `lambda_total`=E+T with rescue/control 0.0).
4. Zero recorded superframe successes with block/superframe denominators separated and the 64-block FER denominator named.
5. The HDC negative-result existence + assumed-v1 schedule configuration as the only citable HDC content.
6. D2 retired for M2; backend UNKNOWN; D-1 deferred with three tag totals and no headline; F9(i) scope on every M0-number reference.

**The record DOES NOT support stating:**
1. Any HDC/LB/NB method ranking, efficiency comparison, or "× worse/better" method claim.
2. Any validated method efficiency or any `f_eff`/`f_eff_actual` for HDC/LB arms.
3. Any headline tag-ratio selection (D-1 open).
4. Any SKR, secure-key, qualification, composable-security, or publication number; any single-point efficiency certification.
5. Any NB actual-disclosure number from stored artifacts.
6. Any real-LB backend identity or any HDC figure as method data.
7. Any prediction about a single-tag protocol from the recorded 16-tag verification.
8. Citation of any corrected number beyond this record until T4 is signed (original M2 acceptance stays WITHHELD).

## 7. No-write / no-run confirmation

I wrote nothing and ran nothing: no file edits, no decoder/construction/arm-runner invocation (not even `--dry`), no `.ttbin` or bundle opened, no commit/push, no `workspace` output. All evidence came from read-only reads of the prereg, record, T2 check, tasks/design/spec/proposal, adjudication (+superseding note), HDC batch-end review, same-data metrics, decision-log D-1..D-4, `diagnostic.json` (full), and `rows.json` summaries (1M arms hdc197/hdc201/lb197/lb201; 2M hdc204 header+arm — values match the record and diagnostic exactly). T2's different-thread status is taken on the documents' assertions (T1 writer: coder-doc per record :7; T2 executor: independent thread per recompute-check :3-5).

## 8. Blocker / decision needed from main

No concrete blocker encountered (no failing command — none run, per the read-only mandate). **Single decision needed:** main-thread T4 acceptance — (a) file this review text as `docs/research_cycles/M2-REALCOMP/CORRECTION_INDEPENDENT_ACCEPTANCE.md`, (b) confirm NB-1..NB-9 stay non-blocking, (c) sign T4 in the decision-log (accept record as stored disclosure arithmetic; original M2 acceptance WITHHELD; D-1 DEFERRED-open with D-2/D-3/D-4 decided), or else return scoped rework instructions if main disagrees with any PASS above.

---

## PART B — T4 main-thread acceptance (2026-09-27)

- **Acceptance of the T3 verdict:** PASS_WITH_FINDINGS. Zero BLOCKING. NB-1..NB-9 accepted as non-blocking; no rework triggered. The reviewer's §8 filing instruction is discharged by this file itself (Part A above).
- **User grant, verbatim, dated 2026-09-27:** 「可以接受这些」, given in the session where main had just reported the Layered-Binary real-frame exact counts and proposed decision D-5. That string is the entire verbatim user grant for T4 and for D-5. No additional grant text is invented here.
- **What is accepted, precisely:** the corrected accounting **as stored disclosure arithmetic with honest labels**. That is the deliverable. The arithmetic is right (T2: 12/12 bit-exact), the labels are right, the void labels are right, the D2 retirement is right, the D-1 deferral is honoured, the backend stance is UNKNOWN.

### Additional finding established by main after T3 ran

Layered-Binary also corrected essentially nothing on the real frames. Main's own read-only recount of the `exact_match` column of each T3 root's `block_accounting.csv` for the `lb` family:

| source | m | exact_match / blocks_done | block FER |
|---|---|---:|---:|
| 1M | 197 | 12 / 3280 | 0.9963 |
| 1M | 201 | 7 / 3280 | 0.9979 |
| 1.5M | 203 | 5 / 4592 | 0.9989 |
| 1.5M | 207 | 6 / 4592 | 0.9987 |
| 2M | 204 | 3 / 6128 | 0.9995 |
| 2M | 208 | 3 / 6128 | 0.9995 |

**36 of 28,000 blocks, 0.13%**, block FER 0.9963–0.9995, and therefore zero superframe successes. This is the same logical condition already applied to HD-Cascade under D-4(iii): a disclosure figure measured on a run that corrected essentially nothing is the cost of a non-working configuration, not a method property. Therefore the Layered-Binary `leak_EC` and every column derived from it carry `void-no-correction` as well.

`void-stub-artifact` does **NOT** apply to Layered-Binary: LB rejected 3268 of 3280 blocks at 1M/m=197 and recorded 215 `undetected`, so its verification path functions; it is a weak decoder, not a hardcoded gate. The HDC defect is not attributed to LB — the finding is not overstated.

### Consequence for the endpoint table

As a correction to the record's own §5/§11 expectation, the deliverable is NOT a two-method same-data table. It is one working method (NB-LDPC, real frames, measured) plus TWO documented negative implementation results (HD-Cascade 0/28,000; Layered-Binary 36/28,000). No comparison column may be filled for either baseline.

### D-5 as decided (recorded, not re-opened)

(i) Layered-Binary is reported as a documented negative implementation result with `void-no-correction` on its disclosure and every derived column, exactly parallel to the D-4(iii) treatment of HD-Cascade. (iii) IN PARALLEL, a read-only trace for contemporaneous backend provenance is authorised — no redecoding, no new execution, only a search of the three M2 roots and adjacent records for any surviving backend trace. (iii)'s outcome refines but never withdraws (i): whatever the trace finds, the void standing of the LB disclosure figures is unchanged. (ii) was not chosen: retaining the disclosure as a bare diagnostic without the void label was rejected because it is the reading that invites the ranking the change exists to prevent.

### Explicit limits carried by this acceptance

No method ranking; no validated method efficiency; no `f_eff`/`f_eff_actual` for HDC or LB; no headline tag ratio (D-1 deferred); no single-point efficiency certification; no SKR, no qualification, no publication number; no NB actual-disclosure number from stored artifacts (M0 has no `leak_EC`/tag ledger); no inference of the real LB backend. The original M2 comparison acceptance remains **WITHHELD** — this acceptance covers only the corrected accounting record.

### Structural confirmation

Main confirms the T3 reviewer's structural finding, which belongs in the record: the displayed nominal columns never read `leak_EC` at all — `f_notag = 5m/(1024·H)` depends only on `(m, H)` — so the cross-family equality of the displayed f is mechanically forced and the displayed f was structurally incapable of distinguishing the methods, whatever actually happened. At 1M/m=197 the recorded leak differs by 2.64x (1,707,485 vs 646,160 bits) while both arms display 1.20048829.

### D1 tag-unit memo standing

The D1 tag-unit memo (`docs/research_cycles/V80-NBLDPC-JAN21/D1_TAG_UNIT_MEMO_20260927.md`) is analysis only, authorizes nothing, and does not change any number in this record.
