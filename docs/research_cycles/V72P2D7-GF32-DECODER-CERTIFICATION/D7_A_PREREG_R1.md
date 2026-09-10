# D7-A preregistration R1 (frozen BEFORE new numerical results)

- Branch: `formal-ir-v72p1-addendum-clean`; baseline HEAD `dfab1ed8`
  (provenance only).
- R1d state: `R1D_PAUSED_PENDING_DECODER_CERTIFICATION` — frozen, reviewed,
  unexecuted, must NOT run. G2 absent. All execution authorization keys false.
- Roadmap §12 verified in substance (stop graph/mother patching; R1d paused;
  historical decoder already row-layered FFT-QSPA; L1→L2 already soft APP;
  D7-A→B→C→D; NB-LDPC mainline, no Cascade) and landed verbatim in commit 1.

## 1. Reference independence rules (frozen)

Oracle `v72p2d7_gf32_decoder_certification.py` must not import/copy: production
mul/inv/permutation tables, `fwht_batched`, `_check_update_log_batch`,
syndrome-offset indexing, row-layered update code. Field mult from declared
polynomial 37 (`0b100101`) by bitwise reduction; own tables; direct check-SP by
explicit enumeration (deg 2/3); exact posteriors enumerate all `H x = s`.
Importing `FIELD_Q`/`FIELD_POLY` constants after independent check: OK.
Importing derived tables as oracle: NOT OK.

## 2. Fixtures and seeds (frozen)

- Priors: deterministic, strictly positive, normalized; ordinary
  (e.g. normalized `1 + (i mod 7)` ramps) and strongly skewed
  (e.g. 0.9 mass on one symbol, rest uniform-positive); no exact deltas.
- Coverage: every field element 0..31; every nonzero multiplier 1..31;
  syndromes 0 and nonzero (5, 17, 31); deg-2 and deg-3 single checks;
  coefficients include 1 plus nontrivial {2, 7, 13, 29}; one two-check tree;
  one small cycle (4 vars / 4 checks or 3 vars / 3 checks) with nontrivial
  labels; satisfied + non-satisfied initial-MAP cases.
- Generated vectors use `np.random.default_rng(2026091001)` (check-update
  prior sampling) and `default_rng(2026091002)` (tree/cycle prior sampling);
  seeds recorded here and in tests. Everything else literal.
- Decoder settings: cold start (`warm_beliefs=None`), `damping_alpha=1.0`,
  `max_iter` ∈ {1, 2, 3}.

## 3. Tolerances (frozen)

Posterior/probability comparisons: max-abs tol `1e-10`. Table identity:
exact integer equality. MAP equality: secondary only, never a substitute.

## 4. Iteration/sweep convention (frozen)

One iteration = one complete row sweep in row-index order. Production
`iterations=k` ⇔ post-`k`-sweep beliefs; `iterations=0` ⇔ initial MAP already
satisfied (early return). Dynamics fixtures use non-satisfied initial MAP so
`max_iter=1,2,3` yields post-sweep beliefs without early stop. No trace hook
planned; beliefs at `max_iter=1,2,3` are the comparison points.

## 5. Exact comparison fields (frozen)

- Arithmetic: elementwise table equality + spot identities.
- Check update: production outgoing log-messages → softmax → probabilities vs
  oracle `direct_check_to_var`; report max-abs error per
  (deg, syndrome-class, coeff-class, prior-class) family + worst tuple.
- Tree: production final beliefs → softmax vs oracle `exact_posterior`,
  per variable; plus normalization/finiteness checks.
- Loopy: production beliefs at max_iter=1,2,3 → softmax vs oracle
  `row_layered_reference` post-sweep-1/2/3; record first divergent
  (sweep, node, symbol, ref, prod, err) on mismatch.
- L1→L2: `final_beliefs` log-domain assertion; `_softmax_rows` tiny-array
  check; `app_fed_l2_prior` vs explicit einsum; `_run_layered_block` with
  fake decode_fn (shape path + uniform-fallback path).

## 6. Pass/fail classification (frozen)

- `D7_A_DECODER_CERTIFICATION_PASS`: all families ≤ 1e-10, no counterexample,
  L1→L2 verified, review verdict PASS.
- Any mismatch → minimal counterexample + report + independent FAIL review
  with earliest causal class; no production patch; no downstream attribution.
- `D7_A_DECODER_CERTIFICATION_BLOCKED`: exactly one named missing item.

## 7. No-production-run boundary (frozen)

Only tiny synthetic in-memory correctness-unit calls to the historical decoder
from D7-A tests. Zero formal/claim-bearing decoder, zero Model-F/CAL/VAL/
real/raw/VOID reads (metadata-only root checks; never open VOID contents),
zero `--phase`, zero R1d/G1/G2.

## 8. Allowed files and commands (frozen)

- New: `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_decoder_certification.py`,
  `comparison_bench/tests/test_v72p2d7_gf32_decoder_certification.py`.
- New docs: this dir (`D7_A_PREREG_R1.md`, later REPORT + REVIEW),
  `openspec/changes/v72p2d7-gf32-decoder-certification/`.
- Production edit allowed ONLY: disabled-by-default trace hook in v35 if
  max_iter beliefs prove insufficient (default plan: none).
- Closeout appends ONLY: `docs/decision-log.md`, `AGENT_PROJECT_MEMORY.md`,
  roadmap §12 landing (already-written content, no rewrite).
- Commands: `py_compile`, `pytest -p no:cacheprovider` on the new test file +
  related v35/D5/D6 fake/unit tests + one non-perf formal-IR suite pass at
  closeout; `git add` exact paths; `git commit` local only; never push.
