# O1R Replication Packet (2026-09-20) — FROZEN, NOT GRANTED

- Track: EXPLORE synthetic only. Branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push).
- Acceptance ID: G-O1R (packet frozen, NOT granted). Authorizes NOTHING; Pre-EXECUTE + fresh grant required (§7).
- Parents: O1 packet/result/batch-end-review 20260920 (A208 PASS 0/60, f_super 1.294947; A188 FAIL retained; review ceiling: single seed-block run, no multi-seed replication).
- Why: replicate the A208 PASS at 4× blocks (pooled) on the frozen construction + one fresh construction instance, genie-u1, same empirical channel.

## 1. Arms (A208 only: n=1024 GF(32), λ={2:1}, m=208, trials 20, genie-u1)
- R1 POOLED REPLICATION: construction seed 2026092001 (frozen O1 A208 instance) × 240 blocks.
- R2 FRESH INSTANCE: construction seed 2026092011 (FRESH; planning rg 2026-09-20 zero hits repo-wide) × the SAME 240 block seeds (PAIRED with R1).
- Blocks (SHARED/PAIRED R1↔R2): literal `2026095601+idx`, idx=0..239 (block k→idx=k); stream `common.v10_seed(f"o1_blk:{seed}")` (O1 domain kept; fresh seeds ⇒ fresh streams).
- Disjointness: 2026095601–5840 outside O1 2026095501–5600, consumed 2026096–98xx blocks, 20260920xx/70xx/72xx/75xx spots, DE 2026094951; planning rg `2026095[6-9]` zero hits; Pre-EXECUTE rg-absence re-check required; record proof.
- R2 fallback rule: Pre-EXECUTE dry-constructs seed 2026092011 and asserts pins fc=0/girth=8/rank=208/208 + construct-twice-identical; ANY mismatch → STOP (no alternate seed, no silent accept, no tuning). [superseded by §Amendment 2026-09-21 — R2 pins amended; girth recorded-not-gated].

## 2. Gates (per arm, AND) + tally + early-stop
- (a) pooled block FER = fails/240 ≤ 5% (≤12 fails; 12/240 = 5.0% exact). (b) f_super = 1.294947 ≤ 1.3 on measured-D_blind basis. f_L2 INFORMATIONAL ONLY, never gated.
- Per-60 tally (REPORT-ONLY, not gated): fails in idx 0–59 / 60–119 / 120–179 / 180–239 + count of quarters with ≤3 fails (O1-bar reference).
- Early-stop: halt FAIL the moment cumulative fails reach 13 (bar unpassable); at ≤12 fails run all 240. Retain partials. No rerun/no tuning.

## 3. Channel + decoder (frozen O1 §4, untouched)
- Same 2M bundle/sampler, y=b&31, GENIE true-u1 rows, XOR-centered prior into `decode_error_domain_posterior`, max_iter=300/streak 3, per-decode cap 300 s. One block = one n=1024 decode, `exact_match is True`.

## 4. Accounting/labels
- Leak 1104 b; f_super = 1104/852.544 = 1.294947 (BUDGET MAPPING, headroom ~4.3 b — TIGHT); f_L2 ≈ 1.258674 informational.
- D_blind = 0 MEASURED placeholder (NEVER-ASSUME-ZERO); sensitivity Δf = D_blind/852.544 (16 b ≈ +0.019; any blind disclosure fails gate (b) — blind risk carried).
- Labels: genie-u1 (D1) ceiling (upper bound only); DE-cover `covered` carried (same ρ={9:0.141,10:0.859} — DE is construction-instance-independent, no new precheck).

## 5. Executor deltas (exact list; defaults = frozen O1 values, backward-compatible)
- D1 `--block-base` (default 2026095501) → O1R 2026095601. D2 `--n-blocks` (default 60) → O1R 240; fail bar derived floor(n×0.05) (60→3, 240→12); early-stop at bar+1; per-60 tally derived from rows (no new decode path). D3 `--construct-seed` (default 2026092001) → R1 2026092001 / R2 2026092011. D4 `--construct-trials` (default 20) → 20 both arms (flag only if implementation requires; no science change).
- `--arm` stays `A208` (m=208 both arms); R1/R2 labels derive from the construct seed in the manifest. `--de-label covered` both arms (carried, §4).
- Pin asserts parametrized by (arm, seed): fc=0/girth=8/rank-full + construct-twice-identical; mismatch → STOP-BLOCKED.
- Manifest adds: `campaign O1R-replication`, R1|R2 label, construct seed/trials, block base, n-blocks, fail bar, paired-seed note, carried de_cover, genie-u1 D1 ceiling. Decode semantics, checkpoint-per-block, resume/window logic UNCHANGED.
- Scope: extend `formal_ir/v80_o1_campaign.py` only (no frozen-module edits); tests extend `tests/test_v80_o1_campaign.py` (fake-only + R2 pin dry check + bar-derivation checks).

## 6. Budgets/scope/stop
- Synthetic EXPLORE only. No real/Jan-21 frames. No writes outside fresh roots. `results/`, `outputs_comparison/` forbidden.
- 2 arms × 240 decodes; est ≈ 240 × 2.5 s ≈ 600 s (A208 measured mean 2.38 s; budget ≤900 s) fits one 3600 s window/arm; per-decode 300 s; RSS < 4 GiB; 1 CPU.
- Roots: `workspace/o1r_<uuid8>` fresh additive per arm (UUID + absence proven at Pre-EXECUTE); old `o1_*` roots untouched.
- Continuation: ≤1 explicit `--resume-from` per arm in a fresh window for WALL-PARTIAL only; terminal FAIL/early-stop never resume.
- STOP on any science-input change (n/m/rates/seeds/H-anchors/thresholds/channel/decoder/hypothesis/data roles).

## 7. Entry evidence + Pre-EXECUTE Q0–Q6 (REQUIRED, none claimed here)
- Entry: (a) O1 A208 PASS record + batch-end review; (b) executor built per §5 deltas; (c) Q0–Q6 Pre-EXECUTE (branch; scope cleanliness; frozen contract §§1–6; authorization; output-absence + rg proofs for `2026095601–5840`, `2026092011`, `o1r_`; focused tests incl. R2 pin dry-construction + 1-block dry decode).
- Q6 commands (one arm/invocation, single window): `.venv/bin/python -m comparison_bench.src.comparison_bench.formal_ir.v80_o1_campaign --execute-real --execution-authorized --arm A208 --root workspace/o1r_<uuid8> --block-base 2026095601 --n-blocks 240 --construct-seed <2026092001|2026092011> --de-label covered` (wall ≤3600 s; ≤1 wall-partial resume).

## 8. Deliverables + does-NOT-establish
- `O1R_RESULT_20260920.md` (per-arm verdict, pooled FER, per-60 tally, f_super mapping, D_blind + sensitivity, carried labels) + `rows.json` + `block_accounting.csv` under each run root. Prompt: `O1R_EXPERIMENT_PROMPT_20260920.md` (≤40 lines).
- Does NOT establish: no L1 construction (genie-u1 ceiling only); single-code block≠S2c group; two-arm replication ≠ generalization (no real-data claim); no S3/qualification/publication/route decision; no λ-optimality; tight-headroom blind risk retained.

## §Amendment 2026-09-21
- Pre-exec dry-construct STOP honored: R2 seed 2026092011 measured fc=0/rank-full/twice-identical but min_girth=6 vs expectation 8; zero decodes run.
- Amendment: R2 acceptance pins become fc==0 AND rank-full AND construct-twice-identical; girth recorded AS MEASURED (6), reported not gated.
- Rationale: seed pre-committed at planning (no search/selection ⇒ no tuning); girth is instance property, not replication requirement; fresh-instance A208-PASS question unaffected; girth delta carried as covariate.
- R1 unchanged (fc=0/girth=8/rank-full). No other changes; no authorization; block seeds/gates/budgets unchanged.
