# BRANCH_TOPOLOGY_MEMO_20260921 (EXPLORE, planning-only — NO push/ops)
Track: EXPLORE. Read-only review; no switch/commit/push/merge executed.

## 1. Current facts
- This checkout HEAD=`formal-ir-v72p1-addendum-clean` (`f4dfd73`; `.git/HEAD`).
- Remote-tracking `origin/formal-ir-v72p1-addendum-clean`=`59ea41d` (stale 09-05); local differs = unpushed.
- Ahead ~531 vs `origin/main` (`ed0adfc`) per 09-20 audit + task prompt (no recount here; shell unavailable).
- Unpushed volume: ~60 untracked incl ~20 cycle dirs V72P3R10..R24/G6/G7/G8/V80 (memory:4123).
- `origin`=HD-QKD-Polar-Comparison.git (private); decoupled from sibling per `repo-remote-decoupling` T3.
- Sibling `../HD-QKD_Polar_Release` HEAD=`codex/security-workbench-master-roadmap` (its `.git/HEAD`), NOT `polar-mainline`.
- Sibling `origin`=HD-QKD-Polar-Release.git, default=`polar-mainline`; checked-out branch is security-workbench (cf. decoupling tasks.md:148-150).

## 2. Risks
- Single-worktree loss: disk failure loses 531 commits + ~60 untracked (no remote copy).
- Crosstalk on wrong push: Comparison `formal-ir-*` to Release remote, or merge into `main`/`polar-mainline`, repeats 2026-08-12..22 incident.
- S0 misleads agents: says checkout=`main`, sibling=`polar-mainline`, shared remote — all three stale (see S4).

## 3. Options -> recommend (a)
- (a) Push same clearly-named branch to Comparison origin, non-force (per S10.2). RECOMMENDED.
- (b) Keep local + offline `git bundle` elsewhere. No remote exposure, but still single-site unless copied off-disk.
- (c) Rebase/merge onto `main` or `polar-mainline`. REJECT: sweeps research into mainline, violates decoupling T3/T6.
- USER-ONLY commands (do NOT auto-run; verify first):
  `git fetch origin; git branch -vv; git status --short`
  `git log --oneline origin/main..HEAD | wc -l; git ls-remote origin refs/heads/formal-ir-v72p1-addendum-clean`
  `git push origin formal-ir-v72p1-addendum-clean:refs/heads/formal-ir-v72p1-addendum-clean`
  `git fetch origin; git branch -vv` # verify; never --force/--all/--mirror; never push to Release remote.

## 4. AGENTS.md S0 fix (via OpenSpec change, per footer)
- Proposed change: `docs-section0-topology-correction`.
- Summary: (1) this checkout default=`main`, active work on `formal-ir-*`; (2) remotes decoupled Comparison vs Release; (3) sibling default=`polar-mainline`, active checkout may be `codex/*` — verify `.git/HEAD` before assuming.
- Draft S0 replacement: "This checkout (Comparison, origin=...Comparison.git, default `main`) does formal-IR/LDPC work on `formal-ir-*`; do not merge them into `main`. Sibling `../HD-QKD_Polar_Release` (origin=...Release.git, default `polar-mainline`) does Polar/security work; do not merge `polar-mainline`/`codex/*` here or push `formal-ir-*` there. Remotes decoupled 2026-09-05; shared-remote history is provenance only."
- Must go through OpenSpec proposal/design/tasks + review; this memo grants no edit.

## 5. Non-goals
- No push, no branch create/switch/rebase/merge, no history rewrite, no Release-tree touch.
- No execution/authorization change. User/main-thread approval required before (a) or S0 edit.
