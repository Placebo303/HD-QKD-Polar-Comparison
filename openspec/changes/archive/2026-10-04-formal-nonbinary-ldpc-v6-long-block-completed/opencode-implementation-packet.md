# OpenCode Implementation Packet: V6 Long-Block Engineering Candidate

## Operator Role

OpenCode is the implementation operator.  It may implement only V6-00 through
V6-44.  It must not authorize V6-50+, select scientific gates, run an official
development batch, or mark its own work accepted.

## Required Reading

Read completely, in this order:

1. `AGENTS.md`
2. `AGENT_PROJECT_MEMORY.md`
3. this change's `proposal.md`, `design.md`, `specs/spec.md`, and `tasks.md`
4. the accepted v5 modules/tests that will be reused, before editing any file

If the documents and current code disagree, stop with the exact conflict.  Do
not silently reinterpret the requirements.

## Allowed Files

New files only, unless the preflight note proves a small additive edit is
required:

- `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v6_codebook.py`
- `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v6_long.py`
- `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v6_development.py`
- `comparison_bench/src/comparison_bench/cli/run_formal_nonbinary_v6_development.py`
- `comparison_bench/tests/test_nonbinary_v6_codebook.py`
- `comparison_bench/tests/test_nonbinary_v6_long.py`
- `comparison_bench/tests/test_nonbinary_v6_development.py`
- `workspace/nbldpc_v6_engineering_<uuid>/...` for test-only evidence
- this change's additive `evidence/v6_engineering_acceptance.json`

One additive `__init__.py` export edit is allowed only if import-by-module is
insufficient.  No other file is authorized without returning for review.

## Forbidden Files and Actions

- Do not modify `src/`, `experiments/`, `tools/`, `results/`, existing outputs,
  v1-v5 source/tests/OpenSpec/evidence, or shared project requirements.
- Do not delete, reset, clean, stage, commit, or rewrite unrelated user work.
- Do not run `longrun_*`, `minrerun_*`, `routeA_*`, raw-data pipelines, N4,
  sidecars, `.ttbin`, confirmation, or real-data jobs.
- Do not create anything under
  `comparison_bench/outputs_comparison/formal_ir_methods/`.
- Do not clone, install, copy, or vendor the Lcrypto repository.  Do not add a
  runtime dependency.  External fixture use requires separate approval.
- Do not tune using v5 confirmation rows or manufacture a passing status.

## Frozen Acceptance IDs

- **A01 Scope:** only allowed files changed; frozen-directory diff is empty.
- **A02 Construction:** both matrices reconstruct byte-for-byte, have full GF
  rank, degree-2 variables, balanced checks, and no parallel edges.
- **A03 Oracle:** exhaustive GF(4)/GF(8) oracle cases pass exactly.
- **A04 Decoder:** noiseless/planted cases, syndrome orientation, deterministic
  repeat, 50-iteration cap, and fail-closed numerical cases pass.
- **A05 Accounting:** syndrome/tag/control disclosures reconstruct exactly.
- **A06 Safety:** allocation cap and explicit fake-runner guards pass.
- **A07 Tamper:** all pre-registered byte/semantic/link/source/transcript/
  leakage tamper cases are rejected.
- **A08 Fake lifecycle:** one complete fake package and strict read-only replay
  pass; no decoder re-execution occurs during replay.
- **A09 Regression:** targeted v5 tests pass without changing v5 files.
- **A10 Output boundary:** official v6 output root remains absent.
- **A11 Evidence:** acceptance JSON binds commands, exit codes, hashes, HEAD,
  explicit source manifest, and every A01-A10 result.

## Test Tiers

Use `python -m pytest ... -q -p no:cacheprovider --basetemp
workspace/nbldpc_v6_engineering_<uuid>/pytest`.  Set a fresh task-specific
temporary root.  Never delete inaccessible legacy pytest directories.

- T0: the three new test files, selecting construction/tiny/oracle smoke tests.
- T1: all three new test files.
- T2: fake lifecycle and strict fake replay tests only.
- T3: the frozen targeted v5 tests identified during V6-02 plus a scoped hash
  audit.  Do not substitute an unscoped `git diff` for the manifest audit.

## Return Conditions

Return only when either:

1. V6-00 through V6-44 and A01-A11 are complete, with changed-file list,
   commands/results, evidence path, and remaining V6-50+ items; or
2. a concrete blocker exists, with failing command, exact error/traceback,
   attempted remedies, and the single decision required.

“Partially complete” is not a completion report.

## OpenCode Prompt

Run from the repository root.  A suitable prompt is:

```text
Read AGENTS.md and
openspec/changes/formal-nonbinary-ldpc-v6-long-block/opencode-implementation-packet.md
completely. Implement only V6-00 through V6-44 and satisfy A01-A11. Preserve
all unrelated dirty-worktree changes. Do not create official v6 outputs, run
confirmation/real data, install dependencies, clone repositories, stage, or
commit. Return only on full packet completion or the packet's concrete blocker
condition.
```

Suggested invocation:

```powershell
opencode run "Read AGENTS.md and openspec/changes/formal-nonbinary-ldpc-v6-long-block/opencode-implementation-packet.md completely. Implement only V6-00 through V6-44 and satisfy A01-A11. Preserve all unrelated dirty-worktree changes. Do not create official v6 outputs, run confirmation or real data, install dependencies, clone repositories, stage, or commit. Return only on full packet completion or the packet's concrete blocker condition."
```

OpenCode provider policies may retain submitted content.  Use this packet only
with synthetic/public material and a provider acceptable for the repository's
confidentiality level; never expose credentials, private lab data, or secrets.

