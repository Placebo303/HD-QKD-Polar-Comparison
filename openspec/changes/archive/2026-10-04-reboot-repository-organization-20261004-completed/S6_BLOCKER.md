# S6 policy blocker — 2026-10-04

S1–S5 are committed. S6 is incomplete and uncommitted; S7/S8 have not started. The approved EXPLORE batch is staged, with original contents retained, path mapping and displaced-draft quarantine records. No delta was merged. No scientific execution or production output change occurred.

## Failing archival eligibility command

```text
wsl -e bash -lc 'cd /mnt/d/Code/HD-QKD_Polar_Comparison && .venv/bin/python workspace/reboot_s6_inventory/check_archive_disposition.py workspace/reboot_s6_inventory/S6_v45_v72.tsv formal-ir-v70r1-parametric-channel-model-check'
```

The workspace-only script checks inventory eligibility before further moves; it executes no research. Exit code 1, complete policy error:

```text
S6 ARCHIVE BLOCKED: formal-ir-v70r1-parametric-channel-model-check
disposition=hold
state=Executed formal/DECIDE candidate; independently reviewed technical/result scope not established from available records.
sources=openspec/changes/formal-ir-v70r1-parametric-channel-model-check/proposal.md:L9; tasks.md:L3; archive/v65_v72p0/v70r1/V70R1_PARAMETRIC_CHANNEL_REPORT.md:L1-L3,L65-L67
No established approved archival disposition; source directory remains unchanged.
```

WSL additionally emits its existing localhost-proxy/NAT warning; that warning does not cause this policy failure.

## Remedies attempted

Located same-cycle execution and lifecycle records rather than trusting old task checkboxes. Searched existing change/cycle/decision/memory Markdown records for independently reviewed scope. Distinguished accepted partial/failed engineering scopes, which can use completed, from an unestablished review scope. Removed an unrelated Stage-0 S0_RESULT reference from V70R1 inventory. Corrected V41's stale never-executed classification using its successor's same-cycle execution record. No missing review was supplied retrospectively and no new scientific qualification was attempted.

## Single required user decision

Approve or reject the concrete `retired-history-no-delta` extension in `S6_DISPOSITION_EXTENSION_PROPOSAL.md`. It preserves known and unknown lifecycle facts and all original files, merges no delta, and grants no scientific execution. The handoff approved the third disposition only for EXPLORE; AGENTS §6 and handoff §5 S6 do not currently authorize this fourth disposition for the historical formal/DECIDE gap.

Recommendation: approve this archival-only extension. Expected benefit is completing S6 without asserting missing acceptance or promoting historical clauses. Cost is documentation and structural checks only.

## Resolution — 2026-10-04

The user approved the fourth disposition and required “只是目前不推进这些，并附上原因”. This policy blocker is resolved. Implement the rule and per-change current deferral reasons, preserve all original files and unknowns, and continue S6–S8 without science execution or delta merge for these archives. The failed check above remains historical evidence, not the current gate state.

After the rule and inventory were updated, the same command exited 0 with `Approved inventory disposition: formal-ir-v70r1-parametric-channel-model-check: retired-history-no-delta`. This is an archival-policy check only, not scientific acceptance.
