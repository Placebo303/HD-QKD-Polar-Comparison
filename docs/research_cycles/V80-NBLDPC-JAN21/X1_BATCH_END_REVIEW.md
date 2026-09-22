# X1 Successor Batch-End Independent Review (G-X1S, EXPLORE_HEAVY) — AGENTS.md §10.3

- Reviewer: independent batch-end review thread (read-only except this file; no edits, no execution beyond read-only inspection + pure arithmetic, no commit/push).
- Date (UTC): 2026-09-21.
- Track: **EXPLORE** (`EXPLORE_HEAVY` cost annotation — synthetic channel draws only, zero `.ttbin` reads).
- Gate: batch-end review per prereg `X1_SUCCESSOR_ENTRY_PREREG_AND_AUTH.md` §9 (no per-arm review).
- Acceptance ID under review: **G-X1S** (cycle V80-NBLDPC-JAN21, X1 successor 15-arm batch).
- Branch context (observed, not changed): `formal-ir-v72p1-addendum-clean`, HEAD `e038f3c5` (per log header; `git log --oneline -3` confirms `e038f3c5` at top).

## Contracts read (verbatim sources, not summaries)

1. `docs/research_cycles/V80-NBLDPC-JAN21/X1_EXPLORATION_LOG.md` (the single append-only batch log — header, carried advisories, preflight, 15-root list, 15 per-arm entries, close-out).
2. `docs/research_cycles/V80-NBLDPC-JAN21/X1_SUCCESSOR_ENTRY_PACKET.md` §§1–9 (frozen contract).
3. `docs/research_cycles/V80-NBLDPC-JAN21/X1_SUCCESSOR_ENTRY_PREREG_AND_AUTH.md` (grant; top amendment note + §§1–9).
4. `docs/research_cycles/V80-NBLDPC-JAN21/X1_SUCCESSOR_ENTRY_PREEXEC.md` (Q0–Q6 PASS record + grant update).
5. `docs/research_cycles/V80-NBLDPC-JAN21/X1_SUCCESSOR_ENTRY_PROMPT.md` (operator prompt; frozen arm order).
6. `comparison_bench/src/comparison_bench/cli/x1_arm_runner.py` (T-X1S-4 runner; pre-execution review passed — used here only to verify the batch ran inside the reviewed enforcement pattern, esp. L556–558 wall gate).
7. `comparison_bench/tests/test_x1_arm_runner.py` (17 fake-only tests; header attests explicit-fake convention, no production calls).
8. `docs/V80_BASELINE_20260921.md` §0.1 ([X1] rows), §3 (corrected H_corr + certifiability), §6-2.
9. `docs/research_cycles/V80-NBLDPC-JAN21/R1_PRERESULT_REVIEW.md` §§3–4 (own-H basis: H_corr triple; N_req table; certifiability).
10. All 15 arm roots `workspace/x1_{98be61fc,ebc2a354,8997e889,a8396d31,e04f1f0a,174eaa87,b3b7c34d,a94868ce,6a0c6a2c,079e4a14,bfd2cc63,538ec607,db7abccd,ac8744f4,214409f4}/` — each root's `rows.json` (+ `X1_RESULT_*.md` + `block_accounting.csv`).

## Method

Every per-arm number below was re-derived from the machine artifacts (`rows.json` `summary` + `rows` arrays; `block_accounting.csv` cross-check for the undetected arm; direct `np.load` key-listing for bundle files), NOT trusted from the log's prose. `f_super=(5m+64)/(1024·H)` recomputed per arm on the arm's own source H; `f_eff=f_super+4.785675·FER`; `N_req=ceil(3·4.785675/(1.3−f_super))` (inf iff f≥1.3); G-A/G-B re-applied; seed ranges, pin fields, bundle labels, wall/RSS/cumulative walls checked against the frozen literals. `git diff -- src/` re-run; protected-root counts re-run; `.ttbin` grep re-run on runner + roots.

## Verdict

**PASS_WITH_FINDINGS** — no blocking findings. All 15 arms terminal inside the frozen contract; all gates re-derive exactly as logged; no science-input change; no prohibitions breached. Two non-blocking findings (F-b budget overshoot adjudication + one editorial slip) and administrative follow-ups are recorded below; none blocks promotion of the batch evidence on main-thread acceptance.

## Numbered findings (severity-tagged)

- **F-a [NON-BLOCKING, recorded]: X1-1M-193 undetected=1 correctly isolated.** `workspace/x1_db7abccd/rows.json`: 214 rows, 13 `block_fail=1`, exactly 1 `undetected=true` (block 167, seed 2026095768, iters 33, `converged=true`, `exact_match=false`, `u1_mismatches=9`, `wall_s=8.35`) — counted inside gate-(a) fails (13 includes it; `block_accounting.csv` shows 13 `exact_match=False` rows) and logged separately, never merged into success. Matches log L226. No adjudication needed beyond confirming the isolation; the runner's b2f-verbatim rule (`x1_arm_runner.py:54–58`, L588–594: `und` counted in `failures`, separately in `undetected`) operated as reviewed.
- **F-b [NON-BLOCKING, adjudicated here → G-E PASS with finding]: X1-1.5M-199 elapsed 1825.7 s vs 1800 s window (+25.7 s, +1.4%).** `workspace/x1_a94868ce/rows.json` summary `elapsed_s=1825.7`, 203 rows, verdict `FAIL-early-stop`, per-decode max 79.4 s (zero overrun rows), RSS 0.677 GiB. Ruling (the G-E adjudication the packet assigns to this review): **within the frozen contract's measurement-terminal pattern, NOT a budget violation that fails G-E.** Reasons: (i) the reviewed runner enforces the wall gate at loop-top only (`x1_arm_runner.py:556–558`: `if clock() - t_start > X1_WALL_CAP_S: return INCOMPLETE-wall`) — an in-flight decode that reaches terminal bar-12 past the window completes rather than converting to INCOMPLETE-wall; this is the block-boundary granularity of the reviewed design, which the pre-execution review passed and this review does not re-litigate; (ii) the arm reached a legitimate terminal state (bar-12 `FAIL-early-stop` at block 203), NOT a wall-partial — no evidence lost, no continuation needed, no repair path triggered (correctly: this is not an infrastructure failure); (iii) every other budget dimension held (per-decode ≤300 s on all 203 blocks; RSS <4 GiB); (iv) cost-control purpose satisfied — cumulative 15915.7 s vs 27000 s ceiling (59%, 11084.3 s margin). The arm's CENSORED-bar12 evidence is retained with the overshoot annotated. No rerun (timing nondeterminism makes a rerun pointless; inputs must stay frozen). Main thread to administratively note the +25.7 s overshoot.
- **F-c [NON-BLOCKING editorial]: stray text in log Arm-2 G-C line (L92).** `X1_EXPLORATION_LOG.md:92` reads `(N=80 < 144... N_req=188; ban held)` — the `144` is the 2M-192 N_req leaked into the 2M-196 line (re-derived N_req for 2M-196 = 188, matching the log's own `N_req=188`). Machine artifacts are unaffected (`rows.json` summary `n_required=188.0`). Suggest a one-line cleanup at acceptance; not a gate issue.
- **F-d [NOTE, no action]: foreign untracked `openspec/changes/binary-ldpc-v5-*` dirs** (`binary-ldpc-v5-audit-remediation-plan/`, `binary-ldpc-v5-incremental-redundancy/`, `binary-ldpc-v5-transfer-to-qrl/` observed in `openspec/changes/` listing) are concurrent-checkout work outside this batch's scope. Untouched by this review and must remain untouched by the main thread's X1 acceptance. (Also observed: `formal-nonbinary-ldpc-v5-multistage-ir/` — same treatment.)

## Explicit checklist (review items 1–9)

### 1. Authorization boundary — PASS

- Grant of record: verbatim chat grant `授权 G-X1S` in the top amendment note of `X1_SUCCESSOR_ENTRY_PREREG_AND_AUTH.md:1`, covering ONE bounded 15-arm batch (≤27000 s total, per-arm ≤1800 s, RSS <4 GiB, 1 CPU), no frozen-input change.
- §7 signature block blank by design (prereg L128: "BLANK by design"); conversation-grant box mode per prereg §7 justification; deviation flagged for post-review administrative ratification (log L4; PREEXEC grant-update L233). Same-cycle precedent (R1 chat-grant) cited; this review performs the nil-impact verification the prereg requires (see below) — ratification itself is a main-thread decision (D3).
- Nil-impact verification (re-derived, not trusted): grid integers per arm match packet §2.2 on all 15 roots; seeds `2026095601+idx` contiguous from base on all 15 roots (first seed 2026095601, last = base+n−1); stream/construct-instance/pins per §2.3 (fc=0, rank==m, `-standalone` labels on all 15); H basis per §2.1 (summaries carry exact frozen floats); gates/budgets per §§2.7/4. **No frozen scientific input changed.**

### 2. Per-arm gate re-derivation — PASS (15/15 match the log)

Recomputed from each root's `rows.json` (summary fails/undetected/blocks + row arrays). Full table (re-derived | log):

| arm (root) | n | fails | und | FER basis | f_super (own H) | f_eff | G-A | G-B | N_req | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| 2M-192 (98be61fc) | 32 | 13 | 0 | stop-point | 1.20000089 | 3.14418135 | FAIL | PASS | 144 | FAIL-early-stop CENSORED |
| 2M-196 (ebc2a354) | 80 | 13 | 0 | stop-point | 1.22343840 | 2.00111059 | FAIL | PASS | 188 | FAIL-early-stop CENSORED |
| 2M-204 (8997e889) | 240 | 2 | 0 | 240 | 1.27031344 | 1.31019406 | PASS | PASS | 484 | PASS NON-CENSORED |
| 2M-200S (a8396d31) | 163 | 13 | 0 | stop-point | 1.24687592 | 1.62855552 | FAIL | PASS | 271 | FAIL-early-stop CENSORED |
| 2M-208 (e04f1f0a) | 240 | 0 | 0 | 240 | 1.29375096 | 1.29375096 | PASS | PASS | 2298 | PASS NON-CENSORED |
| 1.5M-191 (174eaa87) | 40 | 13 | 0 | stop-point | 1.20286350 | 2.75820787 | FAIL | PASS | 148 | FAIL-early-stop CENSORED |
| 1.5M-195 (b3b7c34d) | 63 | 13 | 0 | stop-point | 1.22647220 | 2.21399244 | FAIL | PASS | 196 | FAIL-early-stop CENSORED |
| 1.5M-199 (a94868ce) | 203 | 13 | 0 | stop-point | 1.25008091 | 1.55655271 | FAIL | PASS | 288 | FAIL-early-stop CENSORED |
| 1.5M-203 (6a0c6a2c) | 240 | 2 | 0 | 240 | 1.27368961 | 1.31357024 | PASS | PASS | 546 | PASS NON-CENSORED |
| 1.5M-207 (079e4a14) | 240 | 1 | 0 | 240 | 1.29729832 | 1.31723863 | PASS | PASS | 5315 | PASS NON-CENSORED |
| 1M-185 (bfd2cc63) | 33 | 13 | 0 | stop-point | 1.20536337 | 3.09062928 | FAIL | PASS | 152 | FAIL-early-stop CENSORED |
| 1M-189 (538ec607) | 62 | 13 | 0 | stop-point | 1.22973877 | 2.23318675 | FAIL | PASS | 205 | FAIL-early-stop CENSORED |
| 1M-193 (db7abccd) | 214 | 13 | 1 | stop-point | 1.25411416 | 1.54483274 | FAIL | PASS | 313 | FAIL-early-stop CENSORED |
| 1M-197 (ac8744f4) | 240 | 3 | 0 | 240 | 1.27848956 | 1.33831050 | PASS | PASS | 668 | PASS NON-CENSORED |
| 1M-201 (214409f4) | 240 | 0 | 0 | 240 | 1.30286496 | 1.30286496 | PASS | **FAIL (EXPECTED-OUT)** | inf | FAIL (gate-b only) NON-CENSORED |

- Every cell matches the log's per-arm entries (L71–257) to all quoted decimals; every `n_required` matches (`inf` for 1M-201).
- Per-source H basis verified correct per arm (1M 0.8012690084416184 / 1p5M 0.8272902027770036 / 2M 0.8333327179427281 — summaries carry the exact frozen floats).
- Censored arms (9): fails-at-stop/blocks-at-stop 13/32, 13/80, 13/163, 13/40, 13/63, 13/203, 13/33, 13/62, 13/214 — log's close-out restatement (L264) verified.
- Undetected: the single hit (1M-193 block 167) is inside gate-(a) fails (13/13 non-match rows) and separately columned — never merged (F-a).
- 1M-201: G-A PASS (0/240) + G-B FAIL-expected (f_super 1.30286 > 1.3 by 0.00286) + N_req inf — confirmed as the retained-frozen EXPECTED-OUT characterization (packet §2.2/§4; baseline §3 1M m_max 200), a result not a stop, not an anomaly.

### 3. Frozen procedure fidelity — PASS

- Seeds: `2026095601+idx`, idx 0..n−1 contiguous, verified on all 15 row arrays (0..31 / 0..79 / 0..239 / 0..162 / 0..239 / 0..39 / 0..62 / 0..202 / 0..239 / 0..239 / 0..32 / 0..61 / 0..213 / 0..239 / 0..239).
- Instance 2026092001 + `-standalone` labels + fc=0 + rank==m on all 15 summaries; girth recorded-not-gated (6/8 pattern as logged).
- Bundle role paths per carried R4: 5× 2M arms bind `docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz`; 10× 1M/1.5M arms bind `workspace/x1_bundles_7c1d4a2b/x1_gamma_f03r1.npz`; bound source label == arm source on all 15 (no cross-source reuse).
- b2f/v28 verbatim machinery attested by the reviewed runner path (no kernel change; `git diff -- src/` EMPTY re-verified).

### 4. Budgets adjudication (F-b) — G-E PASS WITH FINDING (ruling in F-b above)

- Per-arm walls: 14/15 ≤1800 s; X1-1.5M-199 = 1825.7 s (+25.7 s in-flight-completion overshoot; terminal bar-12 at block 203, NOT wall-partial) — ruled within the reviewed block-boundary terminal pattern, non-blocking.
- Per-decode ≤300 s: max block `wall_s` per arm ≤83.3 s; zero `error`/`overrun` rows in all 15 `rows.json` arrays.
- RSS: peak 0.602–0.677 GiB across arms (<4 GiB).
- Cumulative: 15915.7 s arm-elapsed sum vs 27000 s ceiling (59%; 11084.3 s margin) — re-summed from summaries, matches log L257/L267.
- Wall-reporting note: summary `elapsed_s` is total wall-clock (`clock()−t_start`, runner L544), and decode-sum trails it by only 0.2–2.2 s/arm (overhead, not a second accounting) — the log's "total elapsed" wording (e.g. L76) is accurate; no decode-sum-vs-wall-clock confusion found.

### 5. Claim ceiling — PASS

- No artifact presents any single-source f_eff as certifiable/literature-comparable: all 15 `X1_RESULT_*.md` carry the structural DISTINCT-lines disclaimer (spot-verified 2M-208 + 1M-201; runner template L431–435 enforces it).
- No pooling across sources/m/instances (per-arm roots; per-source H; log L266 explicitly disclaims).
- No cross-m monotonicity inference: non-censored arms recorded NON-CENSORED with curve label deferred (log L100/L107/L132/L195/L256); the non-monotone cliff pattern noted per-arm only (F-c log line L265).
- Censored arms' FER/f_eff never quoted as 240-basis (R1 rule restated L74/L264; stop-point values labeled artifact-only).
- 2M-only headline prohibition intact; 1M-led rule stated (log L268; close-out claims nothing beyond curves).

### 6. Carried-items application — PASS

- R1 censored-read rule: applied on all 9 censored entries + close-out restatement.
- R4 production-invocation role paths: verified per arm (§3 row above).
- §9 bundle-content fact: `gamma_f03.npz` contains all three sources' keys — CONFIRMED by direct `np.load` key listing (`1M_*`, `1p5M_*`, `2M_*` keys present); `x1_gamma_f03r1.npz` likewise carries all three `{source}_*` key sets. The log's correction (L14) is factually accurate.
- Wall-reporting nuance: explained — see §4 last bullet (no confusion found).

### 7. Arithmetic synthesis (report-only, NO conclusions) — verified

Recomputed from full-precision frozen H_corr (packet §2.1 triple; slope 4.785675):

- Per-source route-gate (G-A) m_min implied by the grid (smallest grid m with G-A PASS): **2M: m=204** (2/240; 192/196/200S censored-FAIL) · **1.5M: m=203** (2/240; 191/195/199 censored-FAIL) · **1M: m=197** (3/240; 185/189/193 censored-FAIL; 201 also G-A-passes at 0/240 but is larger m).
- Per-source G-B-passing m_min (smallest grid m with f_super ≤ 1.3): **2M: m=192** (1.20000) · **1.5M: m=191** (1.20286) · **1M: m=185** (1.20536) — G-B passes on every grid point except 1M-201 (1.30286, EXPECTED-OUT).
- Joint question — any (source, m) grid point with G-A PASS **and** G-C satisfied against key-eligible 200/276/364 (N_req ≤ eligible)? Re-derived N_req at the six G-A-passing points: 2M-204: 484 (>364) · 2M-208: 2298 (>364) · 1.5M-203: 546 (>276) · 1.5M-207: 5315 (>276) · 1M-197: 668 (>200) · 1M-201: inf. **Answer: NONE — no grid point satisfies both.** (Equivalently on blocks-done basis: all six have N=240 < N_req.)
- N_req spot-checks from the frozen rule: 1.5M-207 N_req=5315 CONFIRMED (matches packet §2.1 frozen expectation; consistent with R1-review §4 certifiability row `207, N=5315 → NO`); 1M-201 N_req=inf CONFIRMED (f_super 1.30286 > 1.3). All 15 N_req values match the log exactly.
- No scientific conclusion is drawn; curve synthesis and operating-point questions are out of scope for this review.

### 8. Prohibitions/integrity — PASS

- `git diff -- src/`: EMPTY (re-run; no output). `git diff --stat`: empty. Tracked tree clean apart from enumerated untracked additive files.
- Protected roots: `results/` 0 files / 0 B; `comparison_bench/outputs_comparison/` 1446 files / 554423395 B — identical to the PREEXEC Q3 snapshot (PREEXEC L88–93); legacy permission-denied pytest dirs excluded identically (benign, pre-existing).
- Zero `.ttbin` reads: runner contains no ttbin import/path/string other than the two docstring/G-E attestations (`x1_arm_runner.py:68`, `:446` — assertions of absence, not access paths); the `workspace/x1_*/` grep hits are the same G-E attestation sentence in result markdowns. No `FileReader`/`ttbin_compat`/compute path in the runner.
- No repair-rerun used (log L65/L263 close-out explicit line present).
- No pooling/merging (verified §2/§5).
- Foreign untracked dirs noted, untouched (F-d).

### 9. Output completeness — PASS

- 15/15 roots contain exactly the 3 artifacts (`X1_RESULT_<key>_<m>.md` + `rows.json` + `block_accounting.csv`); no extra files in arm roots; bundle root holds its own 5 files (build log + verify log + 3 npz incl. the F2 verification-only file, correctly never bound).
- Log close-out section present (L261–268): terminal tally 6 non-censored + 9 censored + 0 INCOMPLETE-wall + 0 budget-FAIL; retained-failure restatement; findings F-a/F-b/F-c; cumulative wall; next-step pointer.
- Every arm entry carries status / fails / undetected / wall / f_super-f_eff / gates / girth / bundle / seeds (L71–257 verified field-by-field against `rows.json`).

## Decisions the main thread must take before accepting

- **D1 — Accept the batch evidence** (verdict PASS_WITH_FINDINGS; F-b adjudicated G-E PASS with finding; no arm excluded, no rerun).
- **D2 — Baseline amendment**: record the batch outcomes in `docs/V80_BASELINE_20260921.md` (per-source G-A m_min 204/203/197 as MEASURED curve points; G-B EXPECTED-OUT at 1M-201 confirmed; joint G-A+G-C answer NONE on the grid; N_req spot-confirmations) — curves only, no operating-point selection, no FER/SKR/route/qualification/publication claim.
- **D3 — Administrative ratification** of the chat-grant paperwork deviation (blank §7 signature block; nil-impact verified in §1 above) — same-cycle R1/F-3 precedent.
- **D4 — P1 per-source m_base consumption decision** (packet §1/Q2 purpose: X1 feeds P1 per source; P1 consumes by reference, never assumes 2M; X1-2M-200-STANDALONE ≠ P1 nested leading-200 stands).
- **D5 — Commit/push authorization** for the batch (log + 15 roots + runner/tests + this review; ordinary non-force push on the formal-IR line only — never into any Polar/sibling-line branch) + **memory triage** per AGENTS.md §3.
- **D6 (optional, docs-only)**: apply the F-c one-line cleanup (`144...` stray in log L92) at acceptance.
