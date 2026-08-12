# OpenCode Operator Packet: V12 Real Micro-Feasibility

## Authority

The main thread owns requirements, thresholds, file scope, source/partition
authorization, scientific conclusions, and final acceptance. OpenCode is an
implementation operator only.

The initial authorization ends after **V12-I01 through V12-I05 and V12-T0
through V12-T2** are complete. It does not authorize T3, a real-source read,
partition preparation, a production plan, real decoding, an official output,
or any V12 task after T2.

## Required Reading

Read completely before acting:

- `AGENTS.md` and `AGENT_PROJECT_MEMORY.md`;
- every file in this V12 change;
- the complete V7 R1A codebook/decoder and V7 final ladder report;
- the V11 final decision;
- the V4 incremental-redundancy transcript/accounting design;
- the binary V5 partition and real lifecycle contracts;
- every reused or edited source file.

Do not send private raw data, sidecars, credentials, secrets, or unpublished
lab payloads to a remote provider. Stop and return a blocker if required
information cannot safely remain local.

## Frozen Initial File Scope

The operator may create or edit only:

- `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v12_real_micro.py`
- `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v12_real_partition.py`
- `comparison_bench/src/comparison_bench/cli/run_formal_nonbinary_v12_real_micro.py`
- `comparison_bench/src/comparison_bench/cli/verify_formal_nonbinary_v12_real_micro.py`
- `comparison_bench/tests/test_nonbinary_v12_real_micro.py`
- `comparison_bench/tests/test_nonbinary_v12_real_partition.py`
- this change's `tasks.md`, only to check I01-I05 and T0-T2 after evidence is
  complete.

Read-only reuse is allowed from the exact V7 R1A, V4 transcript/accounting,
10 dB source-adapter, V5 partition, and shared formal-IR modules identified by
the V12 design. Do not modify them.

## Required Implementation

- Implement exactly the V12 delta specification; add no candidate, fallback,
  tuning option, generic framework, dependency, or unregistered status.
- Reconstruct the frozen V7 R1A method; do not copy or change its matrix.
- Keep exclusion-inventory and partition preparation decoder-free. Production
  source access must be impossible during the initially authorized phase.
- Enforce the Alice-information boundary before invoking a method runner.
- Implement full-syndrome and conditional Toeplitz tag/seed accounting from
  canonical events. Local outcome events carry zero disclosure bits. Do not
  copy binary V5 leakage values.
- Implement the exact seven-file package contract, but use it only in fake T2
  roots during initial authorization. Seed records contain exactly
  `seed_hex`, `seed_bit_length`, and `seed_id` and must be unique/fresh.
- Keep plan, execute, and read-only verification separate. The verifier never
  imports or calls a decoder.
- Test-only execution requires an explicit fake method runner and a test-owned
  fresh `workspace/nbldpc_v12_tests_<uuid>` root.
- Do not create a production V12 plan, partition, evidence package, or official
  output directory.

## Test Tiers

- **T0:** compile/import, frozen constants and V7 reconstruction, tiny
  syndrome, Toeplitz, and accounting checks.
- **T1:** focused information-boundary, role, no-overwrite, status, denominator,
  transcript, accounting, lifecycle, and tamper tests.
- **T2:** one complete four-frame fake package plus decoder-free strict replay,
  including pass, 0/4 failure, forbidden failure, and partial-invalid cases.

Use `pytest -p no:cacheprovider`. Tests must prove they cannot enter a real
source loader, production decoder by default, or official output root.

## Forbidden Actions

- No edits outside the seven listed files.
- No changes to `src/`, `experiments/`, `tools/`, `results/`, any V1-V11 file,
  existing output, project memory, handoff, current task, or decision log.
- No real sidecar, `.ttbin`, source array, V5 role array, confirmation data, or
  production partition access.
- No decoder execution on real data; no official output; no long run.
- No install, clone, external repository code, network research, Git stage,
  commit, push, clean, reset, checkout, or deletion.
- No rerun/tuning semantics, extra route, matrix search, blind adaptation,
  spatial coupling, EMS/list, bit-symmetric, multilevel, or qualification work.

## Stop Rules

Stop immediately if the specification is ambiguous, a required existing file
cannot be read, a safe fake-only boundary cannot be enforced, an edit outside
scope is required, or a test would touch real data/production output. Do not
guess or broaden authority.

## Return Conditions

Return only with one of:

1. all I01-I05 and T0-T2 complete, including changed files, exact commands and
   results, fresh test roots, proof of no real-source/production-output access,
   and an explicit statement that real execution remains unauthorized; or
2. one concrete blocker with the failing command, exact error/traceback,
   remedies attempted, and the single main-thread decision required.

## Suggested Prompt

```text
Read AGENTS.md and
openspec/changes/formal-nonbinary-ldpc-v12-real-micro-feasibility/opencode-autonomous-packet.md
completely. Implement only the initially authorized V12-I01 through V12-I05
and run only V12-T0 through V12-T2 with explicit fake runners in fresh test
roots. Never access or decode real data, create a production partition/plan or
official output, modify existing V1-V11 work, install/clone, or use Git writes.
Return after T2 for main-thread review. Never expose private raw data,
credentials, secrets, or unpublished lab payloads to a remote provider.
```
