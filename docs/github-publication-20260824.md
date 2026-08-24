# Formal-IR GitHub publication summary — 2026-08-24

## Purpose

Publish the current formal-IR research state without merging the incompatible
Polar/crosstalk commits currently present on GitHub `origin/main`. This update
uses an ordinary push to a dedicated formal-IR branch; no force push and no
sibling-checkout merge are permitted.

## Source state

- Local branch before publication: `main`
- Pre-update local HEAD: `5f506c9e62bf83bf5d417425c509854285068158`
- Remote: `https://github.com/Placebo303/HD-QKD-Polar-pipeline.git`
- Remote `main` at inspection: `6a58adbda0b20f8899f250f9471cd4f3fb915373`
- Divergence at inspection: remote-only 8 commits, local-only 469 commits.
- The remote-only line modifies the frozen Polar baseline and records the known
  crosstalk history. It is intentionally not merged into this checkout.

## Included research material

This publication includes:

- GitHub/ChatGPT/OpenCode SOP, prompts, PR template, OpenSpec and durable
  project-state updates;
- V35R1 algorithm module, CLI, focused tests, OpenSpec, report, invalid-run
  notice, and compact `run_02` CSV/JSON data;
- V36 algorithm module, CLI, focused tests, OpenSpec, corrected report, and
  compact `run_01` DE/graph/paired-block CSV/JSON data;
- V34 official compact JSON evidence, including the complete 60-block record,
  summaries and read-only review (about 1.7 MB total).

The V35/V36 inclusion is a preservation/publication action, not retrospective
scientific acceptance. Current claim boundaries are recorded in
`AGENT_HANDOFF.md` and the corrected V36 report.

## Omitted local artifacts

The following pre-existing untracked output families remain on the local
machine and are not deleted. They are excluded from this Git update because
they are bulky, historical, superseded, or already represented by committed
reports/manifests:

| Local family | Approximate size | Publication treatment |
|---|---:|---|
| `outputs_comparison/formal_ir_methods/` | 114 MB | Omitted; historical/bulky result packs |
| `outputs_comparison/e2e_16dB_pairing_v2_rematerialize/` | 29 MB | Omitted; derived sidecars |
| V25 `run_01..run_03` | 76 MB | Omitted; V25 authoritative reports point to later accepted evidence |
| `outputs_comparison/transfer_evaluation/` | 8.7 MB | Omitted; existing transfer-evaluation documentation remains authoritative |
| other old untracked comparison packs | under 1 MB each except noted above | Omitted from this scoped publication |
| `workspace/` and inaccessible pytest/temp roots | scratch | Ignored or left untouched |
| `.agents/`, root `ORIGINAL_REQUEST.md`, root `PROJECT.md` | orchestration scratch containing superseded V35 claims | Ignored; durable handoffs now live under `docs/` |

No omitted artifact is presented as newly accepted evidence by this Git
publication. If a future scientific claim depends on one, publish its compact
raw table or create a result summary using
`docs/templates/research-result-summary-template.md`.

## Validation and publication record

Completed before commit:

- `py_compile` for the V35/V36 algorithm modules and CLIs: PASS.
- V35 focused suite outside the sandbox ACL boundary: `25 passed in 15.15s`.
- V36 focused suite outside the sandbox ACL boundary: `11 passed in 20.64s`.
- Staged-diff review: no conflict markers or binary blobs were included. Some
  retained Markdown reports and report-template strings use intentional
  two-space Markdown line breaks, which `git diff --check` reports as trailing
  whitespace; this is formatting only, not a scientific or execution defect.

Two sandboxed V35 pytest attempts reached 18 passing tests before the known
Windows pytest temporary-root ACL failure (`WinError 5`) caused seven fixture
errors and session-cleanup failure. The identical scoped suite passed outside
that ACL boundary; no algorithm assertion failed in the sandboxed attempts.

The final publication uses remote branch `formal-ir-mainline`. ChatGPT reviews
must name that branch and the resulting full commit SHA explicitly.
