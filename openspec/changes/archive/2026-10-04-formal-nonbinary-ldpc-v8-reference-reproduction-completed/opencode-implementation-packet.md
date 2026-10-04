# OpenCode Implementation Packet — Nonbinary LDPC V8

Use the prompt below verbatim from repository root. The OpenSpec files in this
directory are authoritative if the prompt and implementation details differ.

```text
You are the implementation operator for the OpenSpec change
formal-nonbinary-ldpc-v8-reference-reproduction in
D:\Code\HD-QKD_Polar_Comparison.

Read, in this exact order:
1. AGENTS.md
2. AGENT_PROJECT_MEMORY.md sections 33-36
3. openspec/changes/formal-nonbinary-ldpc-v8-reference-reproduction/proposal.md
4. openspec/changes/formal-nonbinary-ldpc-v8-reference-reproduction/design.md
5. openspec/changes/formal-nonbinary-ldpc-v8-reference-reproduction/specs/spec.md
6. openspec/changes/formal-nonbinary-ldpc-v8-reference-reproduction/tasks.md
7. docs/nonbinary-ldpc-v7-audit-v8-plan.md
8. the exact V7 files referenced by the V8 design; do not use Glob or broad
   recursive searches.

MISSION
Implement V8-A01..V8-A12 exactly. V8 is a reference-reproduction and
mathematical-audit change, not a scientific run. Build:
- error-domain syndrome/reconstruction helpers;
- an independent direct probability-domain q=4/q=8 oracle plus bounded
  one-check GF(1024) comparisons;
- brute-force tiny-code MAP validation;
- full-vector q-ary QSC Monte-Carlo density evolution with edge-perspective
  degree distributions, exact sampled degrees, channel contribution, seeded
  deterministic populations, fail-closed normalization, and base-q entropy;
- a precisely cited reproduction of at least one published q-ary QSC result.

EXPECTED ADDITIVE CODE FILES
- comparison_bench/src/comparison_bench/formal_ir/nonbinary_v8_error_domain.py
- comparison_bench/src/comparison_bench/formal_ir/nonbinary_v8_reference.py
- comparison_bench/src/comparison_bench/formal_ir/nonbinary_v8_mcde.py
- comparison_bench/tests/test_nonbinary_v8_error_domain.py
- comparison_bench/tests/test_nonbinary_v8_reference.py
- comparison_bench/tests/test_nonbinary_v8_mcde.py
- evidence files only under the V8 OpenSpec change

SCIENTIFIC REQUIREMENTS
1. Use d = H*y + H*x = H*(x+y), decode e=x+y under a QSC prior centered at
   zero, and reconstruct x_hat=y+e_hat.
2. The oracle may reuse accepted field tables only. It must not import or call
   V1-V7 FFT/FWHT/check-update/decoder functions. Verify the import boundary.
3. Every MC-DE message is a length-q probability vector. Do not reduce it to a
   scalar reliability ratio.
4. Degree distributions must be explicitly edge-perspective. If converting
   from node perspective, use a separately named, tested conversion.
5. Sample the actual degree for each node update. Do not use dv_max as the
   number of incoming messages.
6. Multiply in a fresh channel message at every variable update. Add golden
   regressions that detect both omitted-channel and fixed-degree behavior.
7. Record paper title/authors/year/URL and exact page/section/table/figure/
   equation, q, channel convention, degree perspective, rate, target,
   tolerance, retrieval date, and SHA256 of a retained parameter extract.
8. Freeze seed, population, iterations, convergence rule, target, and tolerance
   before running the published reproduction once. Do not tune and rerun.

LITERATURE
Start with:
- https://arxiv.org/abs/2307.02225
- https://arxiv.org/abs/1004.5367
Use primary papers only. If exact q-ary parameters or conventions needed for a
reproducible target cannot be extracted, STOP implementation_blocked. Do not
guess, use an ambiguous plot as an exact vector, or substitute BSC/BEC tests
for the q-ary reproduction gate. Do not install dependencies, clone repos,
vendor code, or copy third-party implementations.

FORBIDDEN
- Do not modify src/, experiments/, tools/, results/, any V1-V7 source/test/
  plan/result/evidence file, or existing official output.
- Do not run or create canary, development, confirmation, real-data, N4, or
  formal comparison work.
- Do not create a V8 directory under
  comparison_bench/outputs_comparison/formal_ir_methods/.
- Do not rerun or tune frozen V1-V7 data.
- Do not stage, commit, push, install, authenticate, or launch production
  decoders.
- Do not use Glob, recursive filesystem enumeration, or broad repo scans.
- Do not use more than two concurrent agents; serialize file and Git access.

WORKFLOW
A. Record HEAD/status and exact allowed-file manifest. Preserve unrelated dirty
   changes. Check frozen scope by exact paths/hashes.
B. Implement V8-00 through V8-40 in order. Keep functions small and use stdlib
   plus existing NumPy only; no CLI unless tests cannot express the bounded
   reproduction cleanly.
C. Run T0-T3 as specified using a fresh additive
   workspace/nbldpc_v8_reference_<uuid> root and pytest -p no:cacheprovider.
   T3 is a selected frozen regression subset, not every historical long test.
D. Write machine-readable evidence with source hashes, exact commands/exits,
   parameter provenance, tolerances, reproduction trace, frozen-file checks,
   and official-output absence. Mark each V8-A01..V8-A12 PASS/FAIL/BLOCKED.
E. Obtain an independent read-only review. The implementation operator must not
   mark its own candidate accepted.
F. Update tasks.md, docs/decision-log.md, CURRENT_TASK.md, AGENT_HANDOFF.md, and
   AGENT_PROJECT_MEMORY.md only with verified final facts. Do not rewrite old
   history.

RETURN ONLY ON ONE OF TWO CONDITIONS
1. COMPLETE: V8-A01..V8-A12 are complete, tests/evidence independently
   reviewed, no scientific output exists, and changed-file hashes are listed.
2. BLOCKED: provide the exact command, full error/evidence, safe remedies
   attempted, files changed, and one decision required. Do not return a vague
   partial-progress report.

Report deltas only: changed files, T0-T3 counts/exits, reproduction target and
result, independent review verdict, acceptance matrix, output-absence check,
and remaining boundary. Do not claim FER, readiness, qualification, promotion,
or comparison from V8.
```
