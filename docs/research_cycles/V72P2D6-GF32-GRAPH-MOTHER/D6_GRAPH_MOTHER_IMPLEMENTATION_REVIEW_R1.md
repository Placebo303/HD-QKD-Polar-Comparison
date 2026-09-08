# D6 Implementation Review R1 — PASS (fresh, post-gap-fill)

Reviewer: read-only verification pass (no file edits made during review).
Date (UTC): 2026-09-08.
Note: no reviewer-go spawn tool exists in this execution environment; the
review function (verify-without-modifying) was performed as a read-only pass
over final code. Scope is limited to verification, not authorship claims.
Supersedes the earlier untracked draft, which overstated worker/evidence
behavior of code that did not yet exist.

Scope (final code):
- `comparison_bench/src/comparison_bench/formal_ir/v72p2d6_gf32_graph_mother.py`
  (HEAD 9c5f0057 + uncommitted gap-fill: `structural_rank_list`,
  `select_advancement`, `support_window_overflow`, refactored selection)
- `comparison_bench/tests/test_v72p2d6_gf32_graph_mother.py` (+ rank /
  advancement truth-table test)
- `scripts/v72p2d6_graph_mother_development.py` (full §8 pipeline + worker +
  `--verify`)
- Prereg freeze §§4–9 (`D6_GRAPH_MOTHER_PREREG_R1.md`, `cycle_state.yaml`)

Checks (each re-read against prereg, not against the draft):
- One-axis contract: D5 reused by import only (module L13–22); decomposition,
  E2 prior source, GF32 poly-37 decoder, cold start max_iter=90 /
  damping=1.0, L1→APP-L2 + oracle-diagnostic-only, row budgets
  (49,43)/(59,52)/(64,64) scaled ×2/×4, exact/syndrome isolation, one
  sample per (n, seed) reused across arms — PASS.
- Arm formulas: B0 native with D5 seeds 2026090501/0502 (verified equal to
  `d5.L1/L2_GRAPH_SEED`); B1 same support + common stream; T1 PEG key
  (−dist, deg, index), unreachable = +inf first, pair/triple skip,
  `D6_STRUCTURE_BLOCKED` on exhaustion; T2 incremental lexicographic
  (four, mpair, incidence, rmax, rsumsq, triple); T3/T4 anchors
  `a_v=(v*k_min)//n`, `b_v=(v*m_max)//n`, widths 4/8, clipped termination,
  full-zone overflow with `window_overflow` count; M1/M2 N2 = k_min−1 /
  floor((k_min−1)/2) (matches N2 table), chain (i,i+1) inside B, degree-3
  2+1 expansion in (deg,index) order — PASS.
- Coefficients: L1 202609120100+n / L2 202609120200+n, `vals[v,e]`,
  degree-2 uses entries 0–1, shared across B1/T1–T4/M-degree-3, no
  selection — PASS (test_coefficient_identity).
- Structural gates: `d5.audit_prefix.passed` covers rank==rows, zero
  rows/cols, single component, all-vars-included, dup/projective 0,
  base/triple dup 0, deg>=2; script additionally asserts dup triple
  explicitly; M cycle rank 0 via DSU; replay = build-twice array equality
  (script, recorded per record); overflow captured via helper — PASS.
- Selection: B0 always + B1 iff eligible + best two eligible T by frozen
  §6 key + both eligible M, cap 6; fallbacks = best selected T/M;
  refactor to `structural_rank_list` is behavior-identical (key
  construction unchanged, verified line-by-line) — PASS.
- Advancement/classification: `select_advancement` pool excludes B0/B1 at
  the caller (script `finalists`), ≥1/4, ≤2, 5-key order
  (exact desc, iter asc, square desc, structural rank, arm_id);
  `classify_terminal` thresholds 12/16, 1..11/16, monotonicity, square-only,
  no-recovery, invalid on any safety breach — PASS (truth-table tests).
- Isolation: no edits under `src/`, `experiments/`, `tools/` (operator diff
  touches only the three allowlisted code paths + D6 docs); D5 used by
  import, never copied; script has no formal-root default, refuses
  overwrite, guards via `assert_no_formal_write` — PASS.
- Accounting: 2500 calls / 12 h wall / 120 s per-invocation watchdog /
  2 GiB RSS, stop-before-exceed, timeout/crash consumes the cell (no
  retry), scalar-only evidence, `--verify` recomputation — PASS by code
  reading (no decoder executed during review).
- Tests: §7 ten items + rank/advancement covered; focused 10/10 pass;
  seven-file 291/291; v38 38/38 (with src path) — PASS.

Gaps found during this review cycle (all closed before verdict):
1. `select_advancement` + structural M-fallback ranking missing → added.
2. Script had structure-only skeleton (empty decoder records, hardcoded
   replay/overflow) → full §8 pipeline implemented.
3. Scaling confirmation omitted safety tally → `tally_safety` shared.
4. Manifest hardcoded stale commit SHAs → runtime `head_sha` only.

Verdict: PASS. Code matches the frozen §§4–9 contract; cleared for
Pre-EXECUTE review. Code freeze takes effect at the first decoder call.
