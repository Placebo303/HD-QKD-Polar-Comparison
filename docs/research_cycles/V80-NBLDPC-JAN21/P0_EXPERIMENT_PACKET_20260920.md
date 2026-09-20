# P0 Experiment Packet (2026-09-20) — FROZEN, NOT GRANTED

- Track: EXPLORE synthetic only. Branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push).
- Acceptance ID: G-P0 (packet frozen, NOT granted). Authorizes NOTHING; Pre-EXECUTE + fresh grant required (§8).
- Parents: L1 memo 20260920 (§1 cliff, §3 pre-arm) + O1/O1R packets/results/batch-end-reviews 20260920.
- Why: L1 needs m1≥6 rows but m1+m2≤208 ⇒ m2≤202; the 188–208 cliff is unmapped (A188 FAIL 4/14; A208 PASS 0/60 + 0/240×2). P0 de-risks the L1 budget trade BEFORE any L1 build.

## 1. Arms (L2-only, n=1024 GF(32), λ={2:1}, trials 20, genie-u1)
- A202 PRIMARY (m1=6 budget point): m=202, rate 0.802734375, leak=202·5+64=1074, f_super=1074/852.544≈1.2597 (executor recomputes exact quotient; rounding gate-insensitive).
- A200 SECONDARY (m1=8 budget point): m=200, rate 0.8046875, leak=200·5+64=1064, f_super≈1.2480.
- Single-secondary rationale: both arms are budget-binding integer points; A200 probes deeper into the cliff AND answers the live m1=8 trade.
- A206 REJECTED, do NOT run: circulated f=1.2715 is f(204)=1084/852.544, NOT f(206)=1094/852.544≈1.2832; m=204/206 imply m1≤4 < L1 content floor 6 — non-budget points, no decision value. Two arms max.

## 2. Semantics (identical O1/O1R block semantics; byte-identical sampler path)
- Empirical 2M bundle read-only; triple b~p_b/u1~g1/u2~g2 (delta-at-0); y=b&31; rows=γ₂(·|b,u1); XOR-centered prior; `decode_error_domain_posterior` ONLY; max_iter=300/streak 3; per-decode cap 300 s; genie true-u1 = D1 ceiling.
- One block = one n=1024 decode, `exact_match is True`. Sampler draw order frozen identical to O1R so paired seeds ⇒ identical triples (§3).

## 3. Seeds (REUSE — paired with O1R, pre-declared)
- Blocks: literal `2026095601+idx`, idx=0..239, stream `o1_blk:{seed}` — SAME 240 frames as O1R R1/R2 (paired comparison across m; same frames at different m is the paired-design norm).
- Admissibility: reuse frozen HERE (not fresh); prior use declared (O1R roots/docs = expected hits); no independence claim P0↔O1R; pairing exact only via §2 byte-identical path.
- rg-note: Pre-EXECUTE rg must show 2026095601–5840 hits ONLY in O1R + P0 cycle docs/roots; any other hit → STOP. Record proof.
- Construction: seed 2026092001 (O1 family seed; new m ⇒ disjoint outputs, no collision — O1 §2 precedent), trials 20, both arms.

## 4. Gates (per arm standalone, AND) + tally + early-stop
- (a) fails/240 ≤ 12 (5% exact). (b) f_super ≤ 1.3 on measured-D_blind basis (A202 headroom ~34.3 b; A200 ~44.3 b). f_L2 INFORMATIONAL ONLY, never gated.
- Per-60 tally REPORT-ONLY (quarter fails + quarters with ≤3). Early-stop at 13th fail → FAIL, retain partials. No rerun/no tuning.

## 5. Executor deltas (exact list; defaults = frozen O1/O1R values)
- D1: new ARMS entries `A202` (m=202, leak 1074) + `A200` (m=200, leak 1064), λ={2:1}, rate=1−m/1024; closed-world refuse() kept (no `--m` param — preserves pin table + refuse audit).
- D2: `--block-base` → 2026095601 (paired reuse, §3); `--n-blocks` 240; bar floor(n·0.05)=12; early-stop at bar+1; per-60 tally from rows.
- D3: `--construct-seed` 2026092001, `--construct-trials` 20, both arms. Pins: fc==0 AND rank-full AND construct-twice-identical (mismatch → STOP-BLOCKED); girth RECORDED-not-gated (R2-amendment precedent), dry-construct pins measured at Pre-EXEC.
- D4: `--de-label` — one MC-DE point per new rate (V26 kernel, S1 convention, CPU-only, pre-window); campaign proceeds regardless; label carried `exploratory` [label reconciled 2026-09-21: valid literals are covered|exploratory; P0 uses exploratory — no DE run]; gates unchanged.
- D5: manifest adds `campaign P0-pre-arm`, arm id, construct seed/trials, block base, n-blocks, fail bar, paired-O1R note, de-cover label, genie-u1 D1 ceiling. Checkpoint-per-block, resume/window logic UNCHANGED (O1R §5).
- Scope: extend `formal_ir/v80_o1_campaign.py` only (no frozen-module edits); tests extend `tests/test_v80_o1_campaign.py` (fake-only + bar/pin checks).

## 6. Budgets/scope/stop
- Synthetic EXPLORE only. No real/Jan-21 frames. No writes outside fresh roots. `results/`, `outputs_comparison/` forbidden.
- 240 decodes/arm ≈ 240×2.5 s ≈ 600 s, budget ≤900 s/arm; one 3600 s window/arm; per-decode 300 s; RSS <4 GiB; 1 CPU.
- Roots: `workspace/p0_<uuid8>` fresh additive per arm (UUID + absence proven at Pre-EXECUTE); old `o1_*`/`o1r_*` roots untouched.
- Continuation: ≤1 explicit `--resume-from` per arm, fresh window, WALL-PARTIAL only; terminal FAIL/early-stop never resume.
- STOP on any science-input change (n/m/rates/seeds/H-anchors/thresholds/channel/decoder/hypothesis/data roles).

## 7. Interpretation rule (report to main thread; NO auto-proceed either way)
- A202 PASS ⇒ L1 build MAY proceed with m2≤202 budget (P1–P3 packets still need freezing + grants). A202 FAIL ⇒ m2=202 unusable ⇒ L1 memo alternatives re-open.
- A200 PASS keeps the m1=8 option alive; A200 FAIL restricts L1 to m1≤6 (or re-open). Cross-arm pooling FORBIDDEN (different m ⇒ different codes; paired frames aid contrast only).
- Outcome returned to main thread; P0 NEVER authorizes L1 construction, DE, or combined-FER work.

## 8. Entry evidence + Pre-EXECUTE Q0–Q6 (REQUIRED, none claimed here)
- Entry: (a) O1/O1R PASS records + batch-end reviews; (b) executor built per §5 deltas; (c) Q0–Q6 (branch; scope cleanliness; frozen contract §§1–7; authorization; output-absence + rg proofs for `2026095601–5840` (§3) and `p0_`; focused tests incl. dry-construct pins per arm + 1-block dry decode).
- Q6 commands (one arm/invocation, single window): `.venv/bin/python -m comparison_bench.src.comparison_bench.formal_ir.v80_o1_campaign --execute-real --execution-authorized --arm A202|A200 --root workspace/p0_<uuid8> --block-base 2026095601 --n-blocks 240 --construct-seed 2026092001 --de-label exploratory [label reconciled 2026-09-21: valid literals are covered|exploratory; P0 uses exploratory — no DE run]` (wall ≤3600 s; ≤1 wall-partial resume).

## 9. Deliverables + does-NOT-establish
- `P0_RESULT_20260920.md` (per-arm verdict, pooled FER, per-60 tally, f_super mapping, D_blind + sensitivity, de-cover + genie-u1 labels) + `rows.json` + `block_accounting.csv` under each run root. Prompt: `P0_EXPERIMENT_PROMPT_20260920.md` (≤40 lines).
- D_blind=0 MEASURED placeholder (NEVER-ASSUME-ZERO); sensitivity Δf=D_blind/852.544. Labels: genie-u1 (D1) ceiling; f_L2 informational; f_super budget mapping.
- Does NOT establish: no L1 construction; no threshold; no combined FER; genie ceiling only; synthetic only; single-code block≠S2c-group; no S3/qualification/publication/route decision.
