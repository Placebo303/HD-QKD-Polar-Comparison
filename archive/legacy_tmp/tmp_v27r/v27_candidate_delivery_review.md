# V27 — Independent Candidate-Delivery Review (P-CDR)

**Reviewer**: main thread (in-conversation; subagent infrastructure unavailable, user
authorized in-conversation review — see goal revision 4).
**Date**: 2026-08-19
**Subject**: `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v27_gate.py`
and T0/T1 `comparison_bench/tests/test_nonbinary_v27_gate.py`.
**Scope**: candidate enumeration / dedup / legality, ordering keys, screen coverage,
ranked confirmation, terminal precedence, resource/checkpoint binding — verified
against the ACCEPTED V27R OpenSpec.

## Method
- Read full module + existing V27R OpenSpec delta specs.
- `pytest` T0/T1 (10 tests) — all pass under writable `--basetemp`.
- In-conversation smoke: enumerate all 60 candidates, build 240-call screen plan,
  verify dedup dict holds 60, m1 parse, frozen m_total table exact, realized f∈(0,1.3).

## Findings
1. **CRITICAL bug found and fixed** — `run_v27_gate` built `candidates[(bl, src)] = cand`,
   collapsing all 5 candidates per (source, block_len) to the LAST one. Screen/ranking/
   confirmation would then see only 1 candidate per source, defeating the entire
   5-candidate enumeration + ranked confirmation. Fixed: key by `(block_len, source, m1)`
   (the frozen dedup key); updated `rank_candidates` grouping + `by_id` lookup and the
   `_run_confirm_stage` 3-tuple candidate lookup.
2. `ORDER_KEYS` = [worst_final_entropy, mean_final_entropy, abs_offset, m1]; ranked
   ascending per (block_len, source). Matches V27R OpenSpec §7. ✅
3. Screen executes every legal candidate × 2 layers × 2 seeds (240 calls). ✅
   Ranked confirmation stops at first passing candidate per (block_len, source), tries
   next on failure — matches V27R OpenSpec §8. ✅
4. `decide_terminal` emits ONLY `pass_finite_budget_ready` (one block_len with all 3
   sources confirmed) or `de_pass_no_finite_headroom`. `resource_blocked` is set by the
   gated runner on the 24h completed-call ceiling. The four allowed terminal states are
   all reachable; no extra states emitted. ✅
5. 24h completed-call accumulated resource gate (`RESOURCE_LIMIT_SECONDS`) + checkpoint
   (`screen_checkpoint.json` / `confirm_checkpoint.json`) co-located with `frozen_config.json`
   in the same run root; `verify_run` reconstructs budget + terminal from frozen config.
   Manifest field relabeled from a false `frozen_config_sha_binding: True` to an honest
   `frozen_config_binding` description. ✅
6. Budget: `m_total=floor((1.3*n*H_source-64)/5)` per source; `m1_ep=round(m_total*H1/H_total)`;
   5 candidates m1_ep+offset∈{-2..+2}; all legal; all realized f∈(0,1.3) for 12 cells. ✅
7. Rate reconstruction `R_i=1-m_i/block_len`; block_len and mc_samples are distinct fields
   in frozen config. ✅
8. `source/delay` is a public acquisition selector only (LABEL_TO_SOURCE + build_adapter);
   no per-symbol side info, no repeated billing. 64-bit tag counted only in total block
   leakage (comment + layer DE omits it). ✅
9. V26 kernel is reused via thin wrapper only — no copy/rewrite, no V26 rerun. ✅

## Verdict
**ACCEPT** — candidate delivery is correct and complete after the dedup fix. The module
is cleared for the one-shot production screen + ranked confirmation (Phase B item 5).

## Residual (non-blocking, noted for V28)
- Checkpoint reuse across configs is guarded only by co-location + `verify_run` mismatch
  detection, not an embedded config hash. Acceptable for a single additive run root; revisit
  if multi-root reuse is ever added.
