# V80 S2 FER Campaign Packet (2026-09-20) — FROZEN, NOT GRANTED

- Track: EXPLORE synthetic only. Branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push).
- Acceptance ID: G-S2FER (packet frozen, NOT granted). Authorizes NOTHING; Pre-EXECUTE + fresh grant required (§6).
- Parents: G-S2ENTRY frozen packet + accounting map + PROGRAM_PLAN §1.3/§S2. No science change from parents.

## 1. Construction variants (frozen)
- V1 = `construct_l2(seed=2026092001, max_trials=20)`: PEG irregular, L2 λ={2:1} (runner REPRO_LAMBDA), m₂=47, n=256/frame; L1 {2:1}, m₁≈2 is accounting basis only (NOT constructed).
- V1 4-cycle count REPORT-ONLY: 1158 (sponsor-reported for seed 2026092001; Pre-EXECUTE MUST assert `construct_l2(2026092001)["four_cycles"]==1158`, else STOP).
- V2 (fallback/quality arm, runs IFF V1 verdict=FAIL): `construct_l2(seed=2026096101, max_trials=100)` — the ONLY allowed improvement rule (more PEG trials; constructor-kept minimum). Valid IFF `four_cycles < 1158`, else V2 arm FAILs closed.
- Both arms report `four_cycles` + `min_girth` (existing code outputs; no bars, no new metrics). Banned-family refusal unchanged.

## 2. FER campaign design (frozen)
- Superframe = 4 frames, group rule any-frame-fail⇒group-fail (`evaluate_superframe`); frame-ok := `exact_match is True`. Per-frame target 1.274% (never reuse single-frame 5%).
- Groups: 60 per variant (240 decodes; V2 runs only on V1 FAIL). Rationale: 1σ SE=√(.05·.95/60)≈2.8%; bar ≤3 fails/60; power P(pass): true 2%→~97%, true 5%→~65% (boundary coin-flip accepted), true 8%→~29%.
- Frame seeds (fixed, fresh): V1 `2026096001+idx`, idx=0..239 (group g frame f → idx=4g+f); V2 `2026096301+idx`, idx=0..239. Disjoint by hundred-block from frozen 20260920xx/43xx/44xx/45xx/49xx + G6/R7/R11/R23/CLI namespaces (precedent: S1_READINESS §S1r-seeds absence-proof pattern); Pre-EXECUTE rg-absence re-check required.
- Decoder: log-FFT-SPA via `smoke_decode_frame`, `max_iter=300`, `qber=0.05`. Channel: `qsc_pair_sampler` (QSC p=0.05) — the ONLY executable hook today; labelled V17/V25-class QBER≈5% PROXY, not the V17/V25 kernel (no such kernel exists in-repo; building one = science-input change → STOP).
- D_blind = 0 MEASURED (no blind/puncturing rounds exist in campaign path; NEVER-ASSUME-ZERO label carried). Sensitivity line (frozen, mandatory in result): Δf_super = D_blind/852.544, i.e. each 16 bits ≈ +0.019; headroom to 1.3 is 64.31 bits.

## 3. Pass/fail (frozen, no retry/no tuning/no post-hoc switch)
- PASS iff (a) superframe FER = fails/60 ≤ 5% (≤3 fails) AND (b) f_super = (1044+D_blind)/852.544 ≤ 1.3 on m₁=2 basis with measured D_blind. f basis 1.2246 (D_blind=0).
- Early-stop: halt at 4th group failure (bar unpassable) → verdict FAIL; retain partial rows + accounting. Budget-exhaustion halt → FAIL(budget), no resume.
- V2 trigger: V1 verdict FAIL ONLY (any reason incl. early-stop). V2 single shot; V2 FAIL ⇒ no S3, fallback review. No re-seed, no threshold change, no arm hopping.

## 4. Budgets/scope/stop (frozen)
- Synthetic EXPLORE only. No real/Jan-21 frames (S3 DECIDE separate). No writes outside fresh root.
- Caps (single invocation, single window): wall ≤3600 s; RSS ≤4 GiB; 1 CPU; ledger-style call count in result. No resume-loop: one shot per arm; partials retained, never resumed.
- Root: `workspace/s2_fer_<uuid8>` fresh additive (UUID picked + absence-proven at Pre-EXECUTE); old roots untouched; `results/`, `outputs_comparison/` forbidden.
- Stop on any science-input change (grids/seeds/H-anchors/thresholds/channel/decoder/hypothesis/data roles).

## 5. Deliverables (under run root + result doc)
- `S2_FER_RESULT_*.md` (verdict, dual-unit table, D_blind line, sensitivity line) + `rows.json` (per-frame raw) + `group_accounting.csv` (per-group accept/leak/f).
- Operator prompt: `S2_FER_CAMPAIGN_PROMPT_20260920.md` (companion, ≤40 lines). No other outputs.

## 6. Entry evidence + grant boundary (all REQUIRED, none claimed here)
- (a) BER-1/BER-2 cleared (`S1_BATCH_END_REVIEW_20260920.md` addendum); (b) G-REPRO PASS (`S1_REPRO_RESULT_20260920.md`); (c) accounting map w/ corrections; (d) provenance manifest re-attached + hash re-check at Pre-EXECUTE (or version-control committed).
- (e) Constructor suite TO-BE-VERIFIED: `.venv/bin/python -m pytest comparison_bench/tests/test_v80_s2_construction.py -p no:cacheprovider -q` → 7 passed; (f) independent reviewer PASS on constructor recorded; (g) 1158 assert per §1.
- G-S2FER = packet frozen only. Execution needs fresh explicit grant + Pre-EXECUTE (Q0–Q6, exact command, budget, output-absence, authorization). Authorize NOTHING.

## 7. Delta note (2026-09-20 timing probe, annotate-only; frozen text above unchanged)
- Evidence: `S2_TIMING_PROBE_20260920.md` — mean-case 3433 s fits the 3600 s window (~5% headroom); worst-case 4735 s exceeds it.
- Resolution frozen: checkpoint-per-group + at most ONE explicit `--resume-from` continuation in a fresh window; no auto-relaunch.
- Executor frozen: `v80_s2_fer_campaign.py` (dual-flag gated); early-stop rule unchanged (§2).
