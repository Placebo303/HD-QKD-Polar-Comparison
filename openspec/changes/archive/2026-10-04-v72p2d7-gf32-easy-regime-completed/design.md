# D7-B easy-regime — design (R1 + A1)

## Constants (frozen)

- Field GF(2^5), q=32, poly 37. Decoder historical
  `decode_row_layered_fftqspa`, row-layered only, damping 1.0, cold
  (`warm_beliefs=None`). Caps `[1,2,4,8,16,32,90]`. Per-call watchdog 120 s.
  Outer watchdog 1800 s, kill grace 30 s. Aggregate call cap 420 with
  `D7_B_CALL_BUDGET_EXHAUSTED` stop (no silent cell reduction). RSS hard limit
  < 2 GiB; unknown RSS blocks PASS. Seeds `2026091200..2026091203` in order.
  Finite required everywhere. Posterior tol max-abs <= 1e-10 on exact tiers.
  Determinism: discrete exact, float summaries within 1e-12. No retry/rerun/
  resume/tuning/adaptive extension.

## Priors (frozen, per variable, independent)

For frozen truth `x_i`: P99 `P(x_i)=0.99` rest `0.01/31`; P90 `0.90` rest
`0.10/31`; P60 `0.60` rest `0.40/31`; PAIR `d_i = x_i XOR 1`,
`P(x_i)=0.49, P(d_i)=0.49` rest `0.02/30`. All rows positive, finite,
normalized. No delta prior. Decoder sees only prior + exact syndrome.

## Structures (frozen; A1 active)

Coefficients nonzero, nontrivial labels; every dispatched check row degree ≥ 2;
matrices+truths generated once from frozen seeds then frozen in manifest.

1. SINGLE_CHECK_D3: n=3,m=1, H=[[1,7,13]]. Exact via enumeration (32^3).
2. TREE_6 (A1 active): n=6,m=3, row degrees [3,3,2], incidence c0=[0,1,2],
   c1=[2,3,4], c2=[4,5]; coeffs [1,7,13]/[29,1,7]/[13,29]. V=9, E=8, var degs
   [1,1,2,1,2,1], one component, acyclic (E=V-1 + no-back-edge traversal), no
   isolated node, coeffs in 1..31, GF32 rank 3 via D7-A oracle arithmetic.
   Superseded R1 tuple ([2,3,2], 7 edges) is impossible: 9 vertices need ≥ 8
   edges for connectedness (7 < 8); kept only as a spec-regression test, never
   a dispatch path. Exact via tree factor elimination/message passing verified
   against a smaller enumerable projection (enumerate separators v2,v4:
   32^2=1024 + analytic leaf sums) or second independent calc; never 32^6;
   never production decoder/FFT in the exact calc.
3. CYCLE_8: n=8,m=8, H[r,r]=1, H[r,(r+1)%8]=7 (r<7), 13 (r=7). Every check/var
   degree 2, connected labeled cycle, full GF32 rank 8 (independent rank).
   Syndrome uniquely determines truth.
4. FULL_RANK_64: n=64,m=64, H[r,r]=1, H[r,(r+1)%64]=7 (r<63), 13 (r=63).
   Degree 2 everywhere, connected cycle-like, full rank 64. Syndrome unique.

One deterministic construction rule + four frozen seeds only; no graph/label/
seed search. Rule failure → `D7_B_STRUCTURE_FREEZE_BLOCKED`, no tuning.

## Cell schedule (frozen)

64 cells: each tier × {P99,P90,P60,PAIR} × {2026091200..03}. Per cell, cold
caps ascending; stop after first `exact AND syndrome_ok`; later caps marked
`NOT_NEEDED_AFTER_EXACT` (not invoked). Worst case 448 > 420, so global stop:
before each call, if next would make calls > 420, stop whole run as
`D7_B_CALL_BUDGET_EXHAUSTED`, no success verdict. Report distinguishes
scheduled / invoked / not-needed / budget-not-reached.

## Diagnostics (scalar-only per invocation)

Tier, prior, seed, n, m, rank, deg min/max; cap, exact, syndrome_ok,
iterations, status; independently recomputed unsatisfied-check count;
symbol-error count vs synthetic truth; finite flag; max posterior prob, mean
true-symbol posterior, min true-symbol rank, mean posterior entropy; change
from preceding cap (x-hat, posterior max-abs, unsatisfied) labeled
`CAP_PREFIX_PROXY` (cold restarts, not an internal trace); wall s, RSS bytes.
Exact tiers add max posterior error + MAP agreement. No raw priors/beliefs/
truths/syndromes in the root; manifest holds seeds/construction names/scalar
invariants. CAP_PREFIX_PROXY equivalence (cap-k == k-sweep state) is verified
on D7-A tiny recurrence first; on failure omit trajectory language and return
a scoped blocker.

## Terminal priority (frozen order)

1 D7_B_PRE_EXECUTION_BLOCKED; 2 D7_B_WATCHDOG_TIMEOUT_VOID; 3
D7_B_NONFINITE_OR_CRASH_BLOCKED; 4 D7_B_RESOURCE_OVERRUN (RSS unknown/≥2GiB,
call >120 s, run wall >1500 s); 5 D7_B_CALL_BUDGET_EXHAUSTED; 6
D7_B_NO_EASY_REGIME_CORRECTNESS_ALERT (any P99 fails by cap 90, or tractable
posterior/MAP violation); 7 D7_B_EASY_REGIME_CONFIRMED (all P99+P90 exact+
syndrome by cap 90, tractable checks pass, no higher terminal); 8
D7_B_PARTIAL_EASY_REGIME (tractable P99/P90 pass + ≥3/4 FULL_RANK_64 P99 pass,
full confirm unmet, no higher terminal); 9 D7_B_COMPLETED_NO_STABLE_REGION.
P60/PAIR never veto CONFIRMED. No post-hoc thresholds.

## Implementation shape

- Reuse accepted D7-A oracle (`v72p2d7_gf32_decoder_certification.py`); never
  rebuild; oracle defect → STOP + addendum. v35/D5 read-only (import only).
- New `formal_ir/v72p2d7_gf32_easy_regime.py`: deterministic builders, priors,
  tree-exact (two independent calcs), cap ladder, recomputation, budget/
  resource guards, five-file writer, verify mode, lazy decoder bind + DI.
- New `tests/test_v72p2d7_gf32_easy_regime.py`: schedule/cap/prior/truth/rank/
  degree/exact-reuse/ladder/accounting/terminals/boundaries/proxy/fake-paths/
  schema/verifier/unauthorized/no-data-access/protected-root guards.
- New `scripts/v72p2d7_gf32_easy_regime.py`: authorization-gated runner reading
  `docs/research_cycles/V72P2D7-GF32-EASY-REGIME/cycle_state.yaml`; import/
  --help/dry-run/unauthorized bind no decoder and create no root.
- Root `workspace/d7_b_easy_regime_<uuid>/`: fresh, refuse-overwrite, no
  subdirs, exactly `manifest.json, decoder_records.csv, summary.json,
  report.md, command_log.txt`.
- Future command (frozen, not run): `& 'C:\Program Files\Git\usr\bin\timeout.exe'
  -k 30 1800 python scripts/v72p2d7_gf32_easy_regime.py --out-root
  workspace/d7_b_easy_regime_<uuid>`. One UUID, one invocation, consumes on
  first historical-decoder attempt; no retry/rerun/resume/reuse. Pre-RESULT
  review mandatory before any result commit.

## WSL local-source launch rework (shell-spelling-only + runner-local src path)

- WSL is the canonical execution environment. The exact future command shape
  is `timeout -k 30 1800 python scripts/v72p2d7_gf32_easy_regime.py
  --out-root workspace/d7_b_easy_regime_<uuid>`; this supersedes ONLY the
  Windows shell/executable spelling. Inner script, arguments, root pattern,
  UUID rule, scientific matrix, budgets, one-attempt semantics, and all
  prohibitions are unchanged.
- The runner derives `<repo>/comparison_bench/src` from its own resolved
  `__file__` and inserts it into the current process's `sys.path` only when
  absent, before loading the D7-B core, so the core, v35, and
  `nonbinary_field` resolve through the normal package name
  `comparison_bench.formal_ir.*` against the local source tree.
- No hard-coded drive/mount/cwd/PYTHONPATH/venv-site-packages/installed-
  package assumption; no install, packaging, copies, or vendoring.
  Interpreter/WSL/repo/timeout identity is recorded at Pre-EXECUTE, not
  frozen as science parameters. No new UUID is generated by this rework.
