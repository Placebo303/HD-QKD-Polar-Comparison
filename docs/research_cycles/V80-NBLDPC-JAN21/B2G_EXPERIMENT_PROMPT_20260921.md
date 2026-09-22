# B2G Experiment Prompt (2026-09-21) — FROZEN, NOT GRANTED — CONTINGENCY RESOLVED

CONTINGENCY RESOLVED 2026-09-21: B2F_BATCH_END_REVIEW_20260921.md = PASS — packet FROZEN by main thread under standing pre-authorization; per-arm execution grant still recorded at Pre-EXECUTE.
- Track EXPLORE synthetic; branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push). ID G-B2G: frozen only, authorizes NOTHING; a fresh explicit user grant per arm is required before ANY execution.
- Entrypoint: `docs/research_cycles/V80-NBLDPC-JAN21/B2G_EXPERIMENT_PACKET_20260921.md` (§§1–8 frozen). b2g = b2f with EXACTLY ONE changed input: construct seed 2026092011 (O1R R2 second instance; series 2026092001→2026092011).

## Preflight (Q0–Q6; record in `B2G_PREEXEC_20260921.md`, no writes elsewhere)
- Q0/Q1: branch verified; scope = ONLY the 2 NEW files `formal_ir/v80_b2g_campaign.py` + `tests/test_v80_b2g_campaign.py` (no edits to any existing module, incl. `v80_b2f_campaign.py`); frozen contract §§1–6 re-read (arms F208/F202; n=1024 GF(32) λ={2:1}; block base 2026095601; 240 blocks; trials 20; gates (a) fails/240≤12 early-stop at 13th fail, (b) f_super=(5m+64)/852.544≤1.3; D-u1=0.0 measured label).
- Q2 absence + rg proofs: `ls -d workspace/b2g*` → 0 roots; rg `b2g_` → only this change's files; rg `2026092011` → only O1R docs/tests/module + this change (declared reuse of the O1R R2 seed); rg `2026095601|2026095840` → declared paired-reuse hits only (O1R/P0/L1B/b2e/b2f), no b2g root; `results/` + `outputs_comparison/` untouched.
- Q3 dry-construct (REAL constructor, in-memory, no writes/decodes): F208 `construct_arm("A208", 2026092011, 20)` and F202 `construct_arm("A202", 2026092011, 20)`: fc==0 AND rank-full AND construct-twice-identical GATED (mismatch → STOP-BLOCKED, no alternate seed); girth RECORDED-not-gated (O1R R2 precedent; A208 girth 6 measured at this seed in O1R — carried as recorded covariate; A202 girth at this seed measured here and recorded).
- Q4 dry 1-block probe (REAL bundle + sampler + marginal formula, FAKE kernel, no writes): marginal formula vs independent manual contraction (max |Δ| < 1e-12); record `prior_entropy_bits` (report-only; expect ≈852.5 ≈ H_full·n — NOT parity with the genie 826.266 b; FXR-1 constraint) and `u1_mismatches` (report-only).
- Q5 focused tests: `.venv/bin/python -m pytest comparison_bench/tests/test_v80_b2g_campaign.py -p no:cacheprovider -q` green; frozen regression `test_v80_o1_campaign.py` + `test_v80_s2c_campaign.py` + `test_v80_b2f_campaign.py` + `test_v80_b2e_campaign.py` green. No production decode in tests.
- Q6 budgets: ONE window ≤3600 s/arm; per-decode ≤300 s (overrun = terminal); RSS <4 GiB; 1 CPU; MEASURE block 0 (b2f measured F208 672.6 s / F202 1346.9 s; b2e risk 300-iter ≈70 s/decode carried).

## Commands (one arm per invocation; fresh root per arm; dual flags mandatory)
- F208 (PRIMARY, first): `.venv/bin/python -m comparison_bench/src/comparison_bench/formal_ir.v80_b2g_campaign --execute-real --execution-authorized --arm F208 --root workspace/b2g_<uuid8>`
- F202 (SECONDARY): same with `--arm F202 --root workspace/b2g_<uuid8>` (fresh uuid8) — run ONLY if F208 is terminal AND total elapsed at launch ≤50 min.
- Resume (≤1, wall-partial ONLY): add `--resume-from workspace/b2g_<same uuid8>` (root must equal it). Terminal FAIL/early-stop never resumes; no auto-relaunch.
- Logs (b2f precedent): `/tmp/opencode/b2g_F208.{log,time,start}`, `/tmp/opencode/b2g_F202.{log,time,start}` (+ pid/uuid files); record command/PIDs.

## Babysit loop
- Watch: per-block checkpoint flush (manifest.json + rows.json + block_accounting.csv overwrite-in-place); cumulative fails (13th fail → FAIL-early-stop, retain partials, STOP); wall vs 3600 s (→ INCOMPLETE-wall, ≤1 resume in a fresh window); per-decode vs 300 s; RSS vs 4 GiB. Any gate/verdict event → report to the main thread immediately; do not tune, rerun, swap arms, or pool arms.

## Finalize
- Write `B2G_RESULT_20260921.md` (RAW, per arm): verdict, fails/240, FER, quarter tally (report-only), iterations + decode wall mean/min/max, prior_entropy mean/p50/p90/p99/max, u1_mismatches mean/max, both f_super lines (F208 1.294947, F202 1.259759, pass by construction), D-u1 = 0.0 structural label, FXR-1 caveat verbatim, budget/ledger/windows, provenance (PIDs, roots, no commit/push), does-NOT-establish block.

## Stop rules / forbidden
- STOP on ANY science-input change beyond the ONE preregistered construct-seed change (n/m/λ/block seeds/thresholds/channel/decoder/hypothesis/data roles); no rerun/tuning/arm substitution/S3; no writes to `results/` or `comparison_bench/outputs_comparison/`; no commit/push/branch switch; no `longrun_*`/`minrerun_*`/`routeA_*` scripts; no real/Jan-21 frames.
- Interpretation: PASS ⇒ report only. Genie-retirement wording ONLY if BOTH instances pass — then the single allowed sentence is the verbatim one in packet §7; forbidden always: entropy-parity readings, cross-instance FER pooling, independence claims from paired seeds, S3/real-data/qualification/publication/route claims, and any genie-retirement wording if either instance fails or the b2f batch-end review is FAIL. This prompt authorizes NOTHING.
