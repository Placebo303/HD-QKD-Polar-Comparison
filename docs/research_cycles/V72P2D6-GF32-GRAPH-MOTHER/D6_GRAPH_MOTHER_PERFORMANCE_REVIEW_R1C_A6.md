# D6 graph/mother performance review R1c-A6 (read-only)

Reviewer: independent re-check pass over the Track B evidence (commit
`15966c5` code/tests/fixtures + `19c7d21` report/baseline). No files edited
during review (this file excepted at commit time). Independence mechanism:
fresh recomputation from the committed tables only
(`review_recompute.py::bench_arithmetic` — no operator scripts), fresh
reads of the production diff against the prereg's allowed/forbidden lists,
and the recorded test outcomes below (run by the operator in fresh
basetemps, including a re-run of the slow n256
cell against the final committed code (1 passed, 400.8 s)). This review
never authorizes execution.

## Re-checks

1. Prereg vs implementation: the diff adds `_build_T2_support_fast` +
   `_T2_FAST_ENABLED` dispatch only. Staged `four`-prefix filtering,
   vectorized enumeration, integer-encoded membership, incremental
   maintenance, and skipped affected-rebuilds are all present and all on
   the allowed list. Key, field order, tie-breaks, candidate set, greedy
   order: untouched (reference function byte-intact; dispatch is the only
   behavioral edit). No float arithmetic (int32 grid/index with stated
   bounds), no shortlist, no decoder-chosen criterion, no retry logic, no
   six-file schema change. PASS.
2. Equivalence gates re-verified by evidence: (1) support equality — T2
   n64 live-vs-reference both layers, n128/n256 vs replay-verified
   fixtures, non-T2 dispatch pins, mother via untouched assign;
   (2) per-variable traces + v=0 (0,1,2) pins; (3) committed n64 rows
   incl. the strict T2 byte-equality test; (4) eligible map + selection
   identical to I1-gate behavior; (5) replay all True + seq==par;
   (6) A4 guard tests green unmodified (61/61 file, 95/95 seven-file);
   (7) sandbox-T2 vacuous (no T2 family in the repair matrix — premise
   data-locked by test). The (0,1,2)/uniqueness/shape pins fail on any
   key/tie-break/candidate/greedy change by construction. PASS.
3. Benchmark arithmetic recomputed from committed tables: n64 41.4->1.2 s
   (34.5x, <=5 s), n128 656.8->26.6 s (24.7x, <=90 s), n256 10255.7->516.1 s
   cold / 479.7 s warm (19.9x, <=600 s); n64 all-8 1.5 s (<=8 s); fb-only
   0.6/1.3 s vs A4 after-side 2.5/2.7 s (within 2x, faster); peak RSS
   93061120 B (<<2 GiB); replay all True every cell; cold/warm within
   ~7% (no flake). Every absolute target met with >=10x factors —
   `PERF_TARGET_NOT_MET` not triggered. PASS.
4. A4 non-regression: fb-only faster than the A4 after-side (not merely
   within 2x); non-T2 arms same functions/outputs with unchanged-shape
   walls; n64 outputs exactly equal (committed-rows test); pruning and
   two-build machinery untouched and guard-tested. PASS.
5. Zero-decoder accounting: benchmark phases wrote no decoder files (the 16
   files under the bench root are explicit-fake unit-test fixtures from the
   co-located suite run, placeholder rows); A6 unit tests fake-only;
   reference/n256 runs structure-only. PASS.

## Findings

- One advisory (non-blocking): the n256 reference support-only baseline
  is cost-model projected (validated +0%/+6.7% at n64/n128) rather than
  directly measured — the binding A4 task numbers it scales from are
  measured, and the absolute targets are met regardless of the model's
  error. No change requested.
- No blocking finding. Zero rework rounds used.

## Verdict

`D6_R1C_A6_REVIEW_PASS` — exact-equivalent T2 acceleration proven at all
seven gates, all performance targets met with >=10x factors, A4 gains not
regressed, zero decoder calls.
