# V80 S2 Entry Packet (2026-09-20) — FROZEN, NOT GRANTED

- Track: EXPLORE planning-only. Branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push).
- This packet authorizes NOTHING. Execution needs fresh explicit grant + Pre-EXECUTE.
- Acceptance ID: G-S2ENTRY (packet frozen, NOT granted). Lifecycle: S1 closed, S2 gated.
- Frozen convention: PROGRAM_PLAN §1.3 + S2_ACCOUNTING_MAP_20260920 (whole-frame-with-tag, superframe n=1024).

## 1. Construction family (frozen)
- PEG / improved-PEG (Müller同款) + 4-cycle/short-cycle control only.
- BAN (frozen): "Three-shift-cyclic GF(32) mothers FROZEN-excluded for S2" — V29 d_min≤2:
  15 support groups / max multiplicity 69 / 303 duplicate projective classes /
  922 columns in duplicate classes / 1107 proportional-column pairs → d_min≤2.
- Evidence: `docs/nbldpc-v29-retrospective-finite-code-report-20260820.md:56-64`, carried in `S0_RESULT.md §1.7`, `PROGRAM_PLAN.md §S2`.

## 2. Code-length rule (frozen)
- Recommend (a) FIRST: four independent n=256 codes, whole-group accept/discard (matches DE m₂=47 basis).
- Alternative (b) deferred: one n=1024 code (needs fresh prereg delta, not covered here).
- Group rule (a): any-frame-fail ⇒ group fail. Superframe FER≤5% ⇒ per-frame FER≤1−(1−0.05)^(1/4)=1.274%.
- Forbid reusing single-frame 5% gate for superframes. n=256 frame format unchanged; superframe is accounting+grouping only.

## 3. Decoder / channel / rate basis (frozen)
- Decoder: log-FFT-SPA (V10 kernel), ≤300 iter. Channel: synthetic V17/V25-class, QBER≈5%.
- Rate basis: m₂=47 + L1≈2 rows/256-frame ⇒ m_total=49; per-frame syndrome 5·49=245 bits.
- Budgets (H_full=0.83256272): superframe leak 4·245+64=1044; f_super=1044/852.544=1.2246.
- f≤1.3 budgets: superframe ≤1108.31 (H=0.8326) / ≤1064.96 (H=0.8); headroom 64.31 bits — budget-accommodating ONLY.
- Assumes L1≈2 rows + single shared 64-bit tag + zero-extra-disclosure; any change ⇒ stop (see §6).
- Blind surcharge (frozen term): f_super=(1044+D_blind)/(1024·H_full); D_blind≥0 placeholder.
- Rule: count ALL extra disclosed bits beyond scheduled syndrome (puncturing/shortening rounds) into D_blind; never assume 0 in claim.

## 4. Entry evidence required BEFORE construction
- (a) BER-1 fix verified in-repo (honest `_row` status, overruns excluded from pass).
- (b) G-REPRO PASS recorded (m₂=47 5/5+5/5, pooled range 0.000559≤0.04; `S1_REPRO_RESULT_20260920.md`).
- (c) S2 accounting map with review corrections (budget-accommodating only + 64.31-bit headroom + §3 assumptions).
- (d) Runner/test/OpenSpec under version control, or explicit provenance manifest (BER-4 closure).
- (e) IEEE-11440984 status noted as non-blocking gap (FULL-TEXT-NOT-RETRIEVED; Kasai in-repo covers rate-adaptivity).

## 5. Pass / fail (frozen)
- PASS iff superframe FER≤5% (group rule §2) AND whole-frame-with-tag superframe f≤1.3 (L1 actual + D_blind measured).
- FAIL ⇒ no S3, route to fallback review. No auto-fallback, no threshold tuning, no rerun-on-failure.

## 6. Scope / budget / stop rules
- Synthetic EXPLORE only. No real-data/Jan-21 frames (S3 DECIDE needs separate prereg).
- Budgets: wall ≤3600 s/window; RSS ≤4 GiB; CPU ledger scientific_de_calls-style; no-overwrite roots; fresh additive `workspace/s2_<uuid>` root; old roots untouched.
- Stop on any science-input change (grids/seeds/H-anchors/thresholds/data roles/hypothesis).

## 7. Grant boundary
- G-S2ENTRY = packet frozen only. Grant + Pre-EXECUTE (Q0–Q6, command/budget/output-absence/authorization) still required before any execution.
