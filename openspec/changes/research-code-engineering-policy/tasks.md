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

4. **Report** — confirm the single-file diff: only `AGENTS.md` modified.
   No other files touched.

## Verification (no test suite)

This is a documentation-only change. Verification is structural:

- `git diff --stat` shows only `AGENTS.md` (plus change directory if tracked)
- `AGENTS.md` parses as valid Markdown
- Section numbering 1–10 remains contiguous
- All existing content is preserved unchanged apart from the insertion
