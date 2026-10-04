# Tasks: Research Code Engineering Policy

## Task Order

1. **Read `AGENTS.md`** — verify current structure: confirm §5.6 exists,
   identify the exact insertion point (the line containing `---` before
   `## 6. OpenSpec Workflow`).

2. **Edit `AGENTS.md`** — insert the new `### 5.7 Research Code Engineering
   Policy` subsection with the full policy text (as specified in
   `proposal.md`) between the end of §5.6 content and the `---` separator
   preceding `## 6. OpenSpec Workflow`.

3. **Structural self-check** — verify after editing:
   - `### 5.7` heading exists and is the only `5.7` in the file
   - `## 6. OpenSpec Workflow` still exists and is correctly numbered
   - `---` separators are present before and after the new subsection
   - No duplicate or orphaned section numbering
   - Bullet list prefix (`*` / `-`) is consistent with existing blocks
   - File encoding is valid UTF-8

4. **Report** — confirm that only policy/documentation files are modified and
   no algorithm source or scientific output is touched.

5. **Amend for the user-directed first principle** — update this OpenSpec
   packet first, then synchronize `AGENTS.md`, `openspec/project.md`,
   `README.md`, the performance roadmap, decision log, and project memory.
   Do not edit algorithm code or scientific outputs.

6. **Consistency check** — verify every authoritative project document states
   that algorithm performance outranks package maturity and verifier/audit
   sophistication, while preserving only the minimum safeguards for numerical
   correctness, reproducibility, explicit execution authorization, and
   no-overwrite data safety.

## Verification (no test suite)

This is a documentation-only change. Verification is structural:

- `git diff --stat` shows only the policy/documentation files named above
- `AGENTS.md` parses as valid Markdown
- Section numbering 1–10 remains contiguous
- All existing content is preserved unchanged apart from the insertion
