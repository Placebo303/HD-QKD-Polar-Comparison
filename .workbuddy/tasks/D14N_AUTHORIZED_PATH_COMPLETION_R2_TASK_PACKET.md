# D14N Authorized Batch Path Completion R2 — Task Packet

## 1. Purpose and boundary

- Repository: `HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- Change: amend `v72p2d14n-calibrated-l1-l2-discriminator`
- Work type: implementation-only; future batch remains `EXPLORE`.
- Blocking defect: after authorization, the current CLI unconditionally exits
  instead of binding, dispatching and writing the frozen N batch.
- This packet authorizes only code/docs/tests/PROFILE_ONLY and fake-injected
  scratch execution. Production/scientific decoder calls remain exactly zero.
- No scientific row, degree table, seed, arm, threshold, terminal, budget,
  prior, decoder parameter, output root or claim boundary may change.

## 2. Retained accepted evidence

Do not redo or replace the reviewed amendment:

- n128; L1 m=110; L045 71/57/E313, checks `2^17+3^93`; L055
  83/45/E301, checks `2^29+3^81`; L2 DV3 m=104/E384, `3^32+4^72`;
- 18/18 A1–A6 admission, no replacement seeds;
- exactly 288 records (72 each L045/L055/L2_APP/L2_ORACLE), setup ceiling 32;
- seeds, pairing, priors, GF32/poly37, max_iter=90/damping=1/cold,
  CHECK_UPDATED guard, oracle exclusion, gates/terminals and resource budgets;
- future root `workspace/v72p2d14_discriminator/20260914_r1` stays absent.

## 3. R201–R207 required correction

- **R201 OpenSpec amendment first**: record the blocking fall-through and the
  authorized-path completion. Correct stale pre-amendment `≤26` or m=118
  statements where they could mislead execution; preserve the historical
  prereg and supersede it additively.
- **R202 production adapters**: implement one narrow binder returning the
  accepted Model-F loader/prior, L1 decoder, CHECK_UPDATED transfer, L2 APP and
  true-L1 oracle callables. Reuse D11/D12/D14 helpers; do not copy kernels or
  introduce alternate algorithms. Validate callable signatures before root
  creation or decoder calls.
- **R203 batch orchestrator**: build/validate the complete 288 plan before
  binding; construct the frozen 18 graphs and 12 blocks once according to the
  setup accounting; dispatch in frozen order; collect distinct exact,
  syndrome, source, target, joint and undetected fields; stop on provenance,
  nonfinite, admission, resource or contract violation.
- **R204 CLI true branch**: replace the unconditional authorized-path
  `SystemExit` with exactly one call to the batch orchestrator and one
  never-overwrite writer. Unauthorized refusal must remain before root,
  binding and Model-F load. The actual authorized launch form is the frozen
  command plus `--execution-authorized`; manifest may retain the flag-free
  scientific command identity if this precedent is explicit.
- **R205 fake authorized-path test**: inject fake adapters and run the true
  authorized branch against a fresh scratch root. Require exactly 288 fake
  calls, 32 setup units, six files, deterministic identities, expected fake
  gate/terminal, and read-only verifier PASS. Prove no production binder or
  Model-F loader was entered. Include failure tests for first contract error,
  existing root, partial root and invalid APP provenance.
- **R206 production-boundary probe**: without decoding or creating the future
  root, resolve and inspect the real adapter identities/signatures, including
  the explicit APP transfer-source profile. Confirm they are callable and
  accepted helpers; do not invoke them scientifically.
- **R207 independent re-review**: reviewer with actual files reruns focused
  tests in its own basetemp and independently traces both CLI branches. It must
  specifically prove the authorized branch no longer reaches the old
  `SystemExit`, fake dispatch is 288/288, verifier passes, future root remains
  absent, and production decoder calls are zero.

## 4. Tests and efficiency

- `py_compile` the amended module, CLI and focused tests.
- Run D14N focused tests plus directly affected D11/D12 tests only when imports
  changed. Do not rerun broad historical suites without a concrete conflict.
- Run PROFILE_ONLY and live unauthorized refusal after the correction.
- Run the authorized true branch only with explicit injected fake adapters and
  a fresh scratch root. This is test machinery, not scientific execution.
- No retry framework, checksums, transactional writer, generalized abstraction
  or new verifier infrastructure.

## 5. Commit and dirty-tree rule

After independent PASS, a local scoped commit containing only the R2 OpenSpec,
code, tests and compact D14 cycle records is permitted. Use explicit pathspecs;
no `git add .`/`-A`, line-ending sweep, reset, clean, stash, branch switch or
push. Mixed memory/decision-log hunks may remain excluded.

## 6. Return contract

Return only at:

`D14N_R2_EXECUTION_PATH_READY_AWAITING_EXPLICIT_AUTHORIZATION`

with:

- exact authorized-path code delta and removed fall-through;
- adapter identity/signature map and APP source-profile resolution;
- fake true-branch 288/288 evidence, six-file scratch root and verifier result;
- PROFILE_ONLY/refusal evidence; tests and independent verdict;
- proof of zero production calls and absence of the future root;
- exact future authorized command, 288/32/1800/120/<2GiB budgets;
- commit/no-push/excluded-dirt state and all findings.

On any mismatch, STOP with raw evidence and one needed decision. Do not run the
real N batch, create its future root, or issue execution authorization.
