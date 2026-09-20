# B2E Experiment Packet (2026-09-21) — FROZEN, NOT GRANTED

- Track: EXPLORE synthetic only. Branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push).
- Acceptance ID: G-B2E (packet frozen, NOT granted). Authorizes NOTHING; Pre-EXECUTE + fresh grant required (§8).
- Parents: L1_REWORK_MEMO_V3_20260921 §2 (option b2e + MEASURED γ1 stats) + O1 (A208 PASS) + O1R + P0 (A202 PASS) + L1B Stage-A FAIL/review + S2_ACCOUNTING_MAP_20260920 (f_super basis) + `v80_o1_campaign.py` (read-only executor path).
- Why: every L2 arm CONDITIONS on u1 — `posterior_rows_l2` (`v80_o1_campaign` L347) = γ₂(·|b,u1); the u1 dependence lives entirely in Bob's per-symbol prior, so retiring genie may not require an L1 CODE, only a u1 estimate at Bob.

## 1. Hypothesis (to test, NOT a claim)
- H: L2@m=208 decode with û1 = argmax_u γ1(u1|b_i) in place of genie true-u1 maintains the block-FER gate ⇒ genie retirement may not require an L1 code.
- Testable because MAP error is MEASURED, not assumed: p_b-weighted mean 1−p_max = 0.007909/symbol ⇒ 8.10 mismatches/1024-block; 973/1024 columns deterministic (v3 memo §2.1).

## 2. Arms (EXACTLY two — no more, no substitutions)
- **B208 PRIMARY**: m=208 code (the A208 construction instance), u1 source genie → MAP. Budget relevance: m2=208 leaves NO L1-row funding ⇒ if it passes, no L1 code is needed at all.
- **B202 SECONDARY**: m=202 code (the A202 construction instance), u1 → MAP. Budget relevance: m2=202 = m1=6 accounting room (208−202), i.e. the fallback if estimator failures ever need L1 correction.
- B200 and every other m are OUT OF SCOPE (not frozen, not runnable). Both: n=1024, GF(32), λ={2:1}, construct seed 2026092001 / trials 20.

## 3. Semantics (identical to A208/A202 except the u1 source)
- Bundle: frozen `gamma_f03.npz` (`2M_gamma1_L1` (32,1024), `2M_gamma2_L2condU1`) + `gamma_f03_pb.npz`; read-only, no refit.
- Per block: triple draw on the `o1_blk:{seed}` stream via `empirical_triple_sampler` (draw order UNCHANGED); y=b&31; x=u2; rows=γ₂(·|b,û1) via `posterior_rows_l2(bundle,b,û1)` (function and zero-mass semantics UNCHANGED — only the u1 argument source changes); XOR-centered prior; `decode_error_domain_posterior` ONLY; max_iter=300/streak 3; per-decode cap 300 s. Block accept = `exact_match` (x̂==u2). û1 correctness is NOT a block criterion (estimator error may be absorbed by BP).
- û1_i = argmax_u g1[u,b_i] — free argmax, no decoder, no DE, no L1 construction. Mismatch k = Σ_i 1[û1_i ≠ u1_i] MEASURED from the same draw (measurement only, labeled not-a-disclosure).

## 4. Accounting (frozen; the conservative reading is the GATING one)
- D-u1 = 5 × measured k per block (full-correction disclosure of every GF(32) mismatch; conservative; NEVER assume zero — k is measured, so D-u1 is measured, not a placeholder).
- GATE (b), per block: f_super = (m·5 + 64 + D-u1)/852.544 ≤ 1.3 (H_full=0.83256272, 64-bit tag counted once per block). Arm passes gate (b) iff EVERY completed block satisfies it.
- SECONDARY (report-only, NEVER gated): f_super_du0 = (m·5+64)/852.544 with D-u1 = 0.0 MEASURED-zero label (B208 1.294947; B202 1.259759) — the A208/A202-comparable line.
- Provenance: f_super basis + "tagless is never a claim" = S2 map §1/§3; budget-mapping gate = O1/P0/O1R/L1B §6; D-u1 rule = v3 memo §2.2/§2.3 ("freeze a D-u1 term anyway") on §2.1 measured stats.
- ARITHMETIC CORRECTION (annotate-only; draft figures were tagless): at MEASURED mean D-u1 = 5×8.10 ≈ 40.5 b the GATING values are B208 = 1144.5/852.544 ≈ **1.342453** and B202 = 1114.5/852.544 ≈ **1.307264** — both above 1.3. The circulated 1.268/1.232 are the tagless (m·5+D-u1)/852.544 variants (1.267384/1.232195), forbidden as a gate basis by S2 map §3. Pre-registered observation (not a claim): B208's 4.31 b headroom admits only k=0 blocks (P≈3e-4 at mean 8.10); B202's 34.31 b admits k≤6 (7×5=35 > 34.31). Gate (b) is the binding constraint; the per-block counts decide, not the mean. If the main thread wants the tagless variant gated instead, that is a non-frozen-convention change requiring an explicit amendment.

## 5. Gates (per arm, AND; no pooling)
- (a) fails/240 ≤ 12 (5% exact); early-stop at the 13th fail → FAIL, retain partials.
- (b) §4 per-block f_super ≤ 1.3. No cross-arm pooling (different m ⇒ different codes; paired frames aid contrast only). No rerun, no tuning.

## 6. Budgets / scope / stop
- 240 blocks/arm; est ~600–900 s/arm (A208 measured mean 2.38 s/decode; MAP-argmax cost negligible); ONE window ≤3600 s/arm; per-decode ≤300 s; RSS <4 GiB; 1 CPU; ≤1 `--resume-from` (wall-partial only); no auto-relaunch.
- Roots `workspace/b2e_<uuid8>` fresh additive per arm (UUID + absence proven at Pre-EXECUTE); `results/`, `outputs_comparison/` forbidden; old roots untouched.
- STOP on any science-input change (n/m/λ/seeds/H anchors/thresholds/channel/decoder/hypothesis/data roles).

## 7. Executor delta (EXACT list; choice = thin NEW wrapper module, NOT new O1-family ARMS)
- Choice rationale: O1/O1R/P0/SCAN share one arm-level genie-u1 gate path that must stay byte-identical for replay; B2E changes the u1 source AND moves gate (b) to per-block measured D-u1 ⇒ different decode + accounting path (L1B precedent: new thin module, frozen modules untouched).
- X1 NEW `comparison_bench/src/comparison_bench/formal_ir/v80_b2e_campaign.py`, importing frozen helpers read-only: from `v80_o1_campaign` (O1_N, O1_CONSTRUCT_SEED, O1_MAX_TRIALS, MAX_ITER, wall/per-decode/RSS caps, `fail_bar`, `stream_seed`, `construct_arm`), from `v80_s2c_campaign` (`bind_empirical_bundle`, `empirical_triple_sampler`, `posterior_rows_l2`, `center_rows_prior`), plus `peg`/`v28`/`fftqspa`/`GF2mField`. NO edits to any existing module.
- X2 ARMS table `B208`/`B202` only; construction via `construct_arm("A208"|"A202", 2026092001, 20)` — identical (n,m,λ,seed,trials) ⇒ byte-identical instance to the genie arms (recorded as paired construction).
- X3 Pins: fc==0 AND rank-full AND construct-twice-identical GATED (mismatch → STOP-BLOCKED); girth RECORDED-not-gated (P0/R2-amendment precedent).
- X4 Block decode per §3: MAP û1 + per-block mismatch count + `posterior_rows_l2(bundle,b,û1)`; everything else identical to A208/A202 (same construction seed/trials, block seeds 2026095601+idx, `o1_blk:` stream, max_iter 300/streak 3).
- X5 Per-block accounting columns: `u1_source=MAP`, `u1_mismatches`, `d_u1_bits`, `f_super_conservative`, `f_super_du0_report`; `block_accounting.csv` extended with these.
- X6 Arm verdict = gate (a) AND gate (b) per §5. Manifest labels: `campaign B2E-map-u1`, arm id, `u1_source: MAP`, genie ceiling REMOVED for this arm (no D1 ceiling label), D-u1 block (rule + per-block values + mean + violating-block count), paired-seed note (2026095601+idx shared with O1R/P0/L1B; no independence claim), construct seed/trials, block base, n-blocks, fail bar, de-label `covered` (B208, carried from the A208-DE precheck) / `exploratory` (B202, P0 precedent) — no new DE run.
- X7 Seeds/roots per §6; checkpoint-per-block; early-stop at bar+1; dual-flag `--execute-real --execution-authorized` gate kept; ≤1 wall-partial resume.
- X8 Tests: fake-only `tests/test_v80_b2e_campaign.py` (fake bundle + fake decode_fn: MAP argmax, mismatch count, D-u1 arithmetic, per-block gate, bar derivation, early-stop, root refusal). No production decode in tests.

## 8. Entry evidence + interpretation (report to main thread; NO auto-proceed)
- Entry: (a) v3 memo §2.1 measured γ1 stats recorded; (b) executor built per §7; (c) Q0–Q6 Pre-EXECUTE (branch; scope cleanliness; frozen contract §§1–7; authorization; output-absence + rg proofs — `2026095601–5840` hits only in O1R/P0/L1B/B2E docs+roots, `b2e_` absent; focused tests incl. dry-construct pins per arm + 1-block dry decode with MAP-u1).
- PASS on BOTH arms ⇒ the L1-code-free path opens (genie retirement via MAP estimator + D-u1 accounting) — report to main thread; NO auto-proceed to any further packet.
- ANY FAIL ⇒ return to main thread with the b2a / b2c options (v2 memo §3). No rerun, no tuning, no arm substitution.

## 9. Deliverables + does-NOT-establish
- `B2E_RESULT_20260921.md` per arm (verdict, per-arm FER, per-60 tally report-only, D-u1 mean + violating-block count, both f_super readings, labels) + `rows.json` + `block_accounting.csv` per root. Prompt: `B2E_EXPERIMENT_PROMPT_20260921.md` (≤30 lines).
- Annotated (not a rewrite): v3 memo §2.3 choice (iii) — targeted repair disclosing only uncertain positions — is DEAD per the measured stats (k(H>0.5) ≈ 31.4/block, P(k≤4)=0 ⇒ ~157 b ≫ 4.31 b headroom).
- Does NOT establish: no FER/route/S3/qualification/publication claim; genie retirement NOT established by any existing arm (O1/O1R/P0 are genie ceilings); no L1 construction; no cross-arm pooling; paired-seed reuse carries no independence claim; synthetic only (no real/Jan-21 frames); block ≠ S2c-group; A196 still has no verdict; mean-D-u1 readings are pre-registered observations, not gate outcomes.

## Amendment 2026-09-21 (annotate-only; frozen §§1–9 unchanged above)
- Source: main-thread adjudication 2026-09-21 (EXPLORE planning-only; no code, no execution, no authorization). Supersedes ONLY the §4 gating reading (5×k D-u1 + per-block gate → entropy-sum D-u1 + arm-mean gate); §5(b) is read through this amendment. §4 du0 line and the 5×k arithmetic figures remain as history/report-only. Needs review + fresh grant before any execution; authorizes NOTHING.
- Rationale: repo accounting is entropy-proportional (S1 L1 basis: m₁ rows ↔ H_L1×n = 1024×0.02566205 = 26.28 b/block; S2 map §1). The 5×k rule is a crude proxy that overestimates correction disclosure and pre-doomed gate (b) (frozen means B208 ≈1.3425 / B202 ≈1.3073 — both >1.3).
- AMENDED GATING reading (replaces the 5×k reading): D-u1 = measured per-block Σ_i H(γ1(·|b_i)) — minimum SW-style disclosure to resolve u1 from b (expected mean 1024×H_L1 = 26.28 b; measured per block from the frozen `gamma_f03.npz`, no refit). Gate (b): arm-mean f_super = (m·5 + 64 + mean_D-u1)/852.544 ≤ 1.3 (mean-based accounting, consistent with protocol rate design); the per-block D-u1 distribution (p50/p90/p99/max) is REPORTED in the result.
- Report-only, NEVER gated: (i) D-u1 = 0.0 measured label (B208 1.294947 / B202 1.259759, §4 unchanged); (ii) the 5×mismatch ultra-conservative reading (B208 ≈1.3425 / B202 ≈1.3073 at the measured mean) — carried as an explicit sensitivity line.
- Pre-registered observation (not a claim): at mean D-u1 = 26.28, B202 ≈1.2906 ≤ 1.3 (headroom ~8.0 b) and B208 ≈1.3258 > 1.3 (expected — B208 funds no L1 rows) ⇒ gate (b) now discriminates the two arms as designed; gate (a) (decodability under MAP conditioning) is measured independently.
- Everything else unchanged: arms B208/B202; seeds (2026095601+idx, `o1_blk:`, construct 2026092001/trials 20); executor delta X1–X8 — X5 columns unchanged and already carry both inputs (`d_u1_bits` = amended per-block entropy sum, the gating input; 5×k sensitivity derived at result-analysis time from recorded `u1_mismatches`; no executor edit); budgets (§6); interpretation rule (§8); no-authorization. v3 memo §2.3 choice (iii) remains annotated dead.
