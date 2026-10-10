# Archive disposition: nbldpc-mainline-enabling

- Date: 2026-10-10
- Disposition: retired-history-no-delta
- Known facts: an exact check-transform reuse candidate was implemented and reviewed for numerical equivalence (commit 7aa4283f); no decoder experiment was in scope.
- Unknown: adoption of the candidate into a production decoder path is not recorded.
- Reason not advanced: the 1024-symbol GF32 NB-LDPC path is no longer the mainline; the mainline is GF(5) single-stage soft decoding (S-5, docs/research_cycles/C-BATCH/S5C_RESULT.md). Not a scientific KILL.
- Frozen merge boundary: no delta merged into openspec/specs/.
- No scientific acceptance, retrospective approval or execution grant follows from this archive. Reconsideration requires a successor change and its own authorization.

## Original tracked files
- openspec/changes/nbldpc-mainline-enabling/proposal.md
- openspec/changes/nbldpc-mainline-enabling/specs/check-node-reuse/spec.md
- openspec/changes/nbldpc-mainline-enabling/tasks.md
