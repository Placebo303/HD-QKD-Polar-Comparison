# L1B Build Packet (2026-09-20) — FROZEN, NOT GRANTED

- Track: EXPLORE synthetic only. Branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push).
- Acceptance ID: G-L1B (packet frozen, NOT granted). Authorizes NOTHING; Pre-EXECUTE + fresh grant required (§8). TWO STAGES: Stage A gates Stage B.
- Parents: L1 memo + P0 result/batch-review (A202/A200 PASS under genie; m1+m2≤208, m1≥6) + O1/O1R packets + S2 map + S1 readiness (H_L1=0.02566205; γ_1=P(U1|B); u1 = bits 9..5).
- Why: retire genie-u1 (D1 ceiling) with a real L1 + combined chain at the two budget-binding integer points.

## 1. Configs (both total 208 rows; leak 1104; f_super=1104/852.544=1.294947)
- PRIMARY C6: m1=6 (L1 rate 0.994140625) + m2=202 (P0-PASS L2). SECONDARY C8: m1=8 (rate 0.9921875) + m2=200 (P0-PASS L2).
- L1 code: n=1024, GF(32), λ={2:1} (same family); construct seed 2026092001/trials 20 both configs (new m ⇒ disjoint outputs, O1 §2 / P0 §3 precedent; Pre-EXECUTE rg confirms no (1024,6)/(1024,8) use).
- Pins: fc==0 AND rank-full AND construct-twice-identical (mismatch → STOP-BLOCKED); girth RECORDED-not-gated (P0/R2 precedent). Dense-check flag carried (memo §2a: avg check deg ~341/256).
- L1 content 1024×0.02566205=26.28 bits; f_L1=5m1/26.28: f_L1(6)≈1.142, f_L1(8)≈1.522 — INFORMATIONAL ONLY, never gated.

## 2. Stage A — L1-only FER (runs FIRST; per-config gate)
- Semantics (frozen code quotes): triple `empirical_triple_sampler` (s2c L251-285: b~p_b `rng.choice(1024,p=p_b)`; u1~g1[:,b]/sum; u2~g2; zero-mass→delta-at-0); Alice x1=u1; Bob y1=(b>>5)&31 (`factor_layers` v29 L269-273); rows=`posterior_rows("L1",b)`=p_u1_gb.T[b] (v26_channel L236-237, no u1 conditioning — L1 decodes first); prior π(e)=rows[y⊕e] via `_center_rows` (v28 L189-197, XOR); entrypoint `decode_error_domain_posterior` ONLY (v28 L155-186); max_iter=300/streak 3; per-decode cap 300 s. L1 exact = û1==u1.
- Blocks REUSE (decided): literal `2026095601+idx` idx=0..239, stream `o1_blk:{seed}` — SAME 240 frames as O1R/P0. Justification: byte-identical triple path ⇒ (b,u1) marginal identical, paired L1-vs-L2 contrast on same frames (paired-design norm); prior use declared (O1R/P0 roots+docs = expected hits); NO independence claim L1B↔P0↔O1R.
- Arms A6 (m1=6) + A8 (m1=8); one block = one n=1024 L1 decode.
- Gates per arm (AND): (a) fails/240≤12 (5% exact); (b) system f_super mapping 1.294947≤1.3 carried (total fixed 208; L1 leak share 5×m1 bits = 30/40 b; 64-bit tag counted once at system level). Early-stop at 13th fail → FAIL, retain partials. No rerun/no tuning.
- GATE RULE (decided, per-config): A6 PASS ⇒ B6 may run; A8 PASS ⇒ B8 may run — independently. A FAIL ⇒ no Stage B for that config (⇒ rework memo, §7).

## 3. Stage B — combined chain (only for Stage-A-passing configs)
- Per block: decode L1 from b → û1 (§2 semantics); then L2 with û1 in place of genie-u1: y2=b&31; rows2=`posterior_rows_l2(bundle,b,û1)` (s2c L288-316); XOR prior; `decode_error_domain_posterior`, max_iter=300/streak 3. L2 exact = x̂==u2 given û1.
- System success = BOTH layers exact (û1==u1 AND x̂==u2). Genie label RETIRED; label `real-L1 chain`.
- Gates per arm (AND): (a) system fails/240≤12; (b) f_super 1.294947≤1.3 on measured-D_blind basis. Early-stop at 13th; no rerun/no tuning.

## 4. DE precheck (decided: OPTIONAL-with-label)
- One MC-DE point at L1 rate via frozen V26 kernel (S1 convention) MAY run pre-Stage-A as its own quick step; Stage A proceeds regardless; label `exploratory` carried; gates unchanged. Justification: L1 rate ≈0.994 is far off the S1 L2 grid (memo §2b) ⇒ DE informative-not-decisive; the 240-block empirical FER is the gate (P0 precedent: exploratory, no DE run).

## 5. Executor deltas (NEW module; frozen modules untouched)
- NEW `formal_ir/v80_l1b_campaign.py` (imports v10_peg/v26_channel/v28/s2c-helpers read-only). E1: L1 construction (1024,m1) peg+make_rho path + pin asserts + twice-identical. E2: `posterior_rows_l1` thin wrapper (v26 L236-237 exact) + bundle binding + p_b gate. E3: L1 block-decode wrapper (§2 wiring). E4: combined block wrapper (§3: û1→L2 rows). E5: gates/manifest/labels (stage, config, construct seed, block base, fail bar, paired note, exploratory, real-L1-chain; genie retired in B). E6: checkpoint-per-block + one wall-partial `--resume-from`; early-stop bar+1. Tests: fake-only extension.

## 6. Budgets/scope/stop
- Synthetic EXPLORE only. No real/Jan-21 frames. No writes outside fresh roots. `results/`, `outputs_comparison/` forbidden.
- Stage A: 240 L1 decodes ≈ ≤500 s est, budget ≤900 s/arm. Stage B: 240×(L1+L2) ≈ 1200 s est, budget ≤1500 s/arm. One 3600 s window per stage-arm; per-decode 300 s; RSS <4 GiB; 1 CPU.
- Roots `workspace/l1b_<uuid8>` fresh additive per stage-arm (≤4: A6/A8/B6/B8); old roots untouched. ≤1 `--resume-from` each, WALL-PARTIAL only; FAIL/early-stop never resume.
- STOP on any science-input change.

## 7. Entry evidence + interpretation (report to main thread; NO auto-proceed)
- Entry: (a) P0 PASS records + batch review; (b) executor built per §5; (c) Q0–Q6 (§8).
- A FAIL ⇒ L1 construction rework memo (no Stage B that config). B FAIL ⇒ combined-chain diagnosis (error-propagation accounting). Either way NO auto-proceed to S3; outcome returned to main thread.

## 8. Pre-EXECUTE Q0–Q6 (REQUIRED, none claimed here)
- Q0 branch `formal-ir-v72p1-addendum-clean`; Q1 scope cleanliness; Q2 frozen contract §§1–7; Q3 explicit authorization (per stage: A-grant covers A only; B-grant needs A PASS record); Q4 output-absence + rg proofs (`2026095601–5840` hits only O1R/P0/L1B docs+roots; `l1b_` absent); Q5 focused tests green (fake-only + dry-construct pins per m1 + 1-block dry L1 + 1-block dry combined); Q6 commands:
- A: `...v80_l1b_campaign --execute-real --execution-authorized --stage A --config <C6|C8> --root workspace/l1b_<uuid8> --block-base 2026095601 --n-blocks 240 --construct-seed 2026092001 --de-label exploratory`
- B: same with `--stage B` (passing-config only). Full flag names per §5 implementation; Q6 re-verified at Pre-EXECUTE.

## 9. Deliverables + does-NOT-establish
- `L1B_RESULT_20260920.md` (per-stage-arm verdicts, FERs, f_super mapping, D_blind + sensitivity, labels) + `rows.json` + `block_accounting.csv` per root. Prompt `L1B_EXPERIMENT_PROMPT_20260920.md` (≤40 lines).
- D_blind=0 MEASURED placeholder (NEVER-ASSUME-ZERO); sensitivity Δf=D/852.544. Headroom 1108.31−1104=4.31 b UNCHANGED (total fixed 208 rows); blind surcharge still open — any D_blind>4 bits fails gate (b).
- Does NOT establish: no real-data/Jan-21 claim; synthetic only; single-code block≠S2c-group; no S3/qualification/publication/route decision; per-config verdicts only (no C6↔C8 pooling).

## Amendment 2026-09-21 (annotate-only; frozen §§1–9 unchanged above)
- Source: L1_REWORK_MEMO_20260921.md option (a) (memo §3). Replaces the §1 pin bullet for m1 legs only; m2 legs unchanged. Prior pin line (§1: "Pins: fc==0 AND rank-full AND construct-twice-identical ...") is SUPERSEDED for m1 legs by the text below; retained in place as history (annotate, don't rewrite).
- EXACT AMENDMENT TEXT (verbatim from memo §3):
- "Pins — m1 legs (1024,6)/(1024,8): rank-full AND construct-twice-identical GATED (mismatch ⇒ STOP-BLOCKED); four_cycles + min_girth RECORDED-not-gated as covariates (dense-check regime: expected fc>0/girth 4, memo 20260921 §1). Pins — m2 legs (1024,202)/(1024,200): fc==0 AND rank-full AND twice-identical GATED; girth recorded. f_L1 informational only, never gated."
- Scope: constructability gating only (dense-check regime, memo §1: avg check deg ~341/256, fc>0 unavoidable by pigeonhole, not a PEG-seed defect). Budgets/blocks/gates/stop rules (§§2–3/6: 208 rows, leak 1104, f_super 1.294947, fails/240≤12, early-stop 13th, no rerun/no tuning) UNCHANGED. Needs review + fresh Stage-A grant before any execution; authorizes NOTHING here.
