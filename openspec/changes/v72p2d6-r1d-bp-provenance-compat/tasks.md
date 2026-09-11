# D6 R1d BP provenance compatibility repair — tasks

> Operator authority: Track A R01–R04 only. R05–R07 (independent review,
> renewed Pre-EXECUTE, commits) are out of scope here. Zero real decoder,
> no Model-F/CAL/VAL/real/raw reads, no R1d/G1/G2/`--phase`, no roots,
> no UUID, no push, no commits.

- [x] R01 — **Independent reproduction (fake only).** With an injected fake
  `_decode_block` (tiny arrays; never bind the real decoder): (a) prove the
  five-unpack raises and the broad worker `except` maps it to a crash cell;
  (b) prove the unguarded `softmax(bel)` → `app_fed_l2_prior` parent path.
  Record exact source lines + no-side-effect evidence. Evidence summarized
  in `proposal.md`; repro script lives in `/tmp` (not committed).
- [x] R02 — **OpenSpec freeze (docs only, uncommitted).** This change folder
  (`proposal.md`, `design.md`, `specs/`, `tasks.md`) plus the R1d
  execution-packet addendum
  `docs/research_cycles/V72P2D6-GF32-GRAPH-MOTHER/D6_GRAPH_MOTHER_R1D_EXECUTION_PACKET_ADDENDUM_BP_COMPAT_A1.md`
  declaring the prior R1d Pre-EXECUTE stale and superseded after repair,
  granting no execution.
- [x] R03 — **Minimal implementation (D6 script only).**
  `scripts/v72p2d6_graph_mother_development.py`: worker unpacks six values
  + provenance IPC transport; warmup shape validation with ready flag;
  parent `CHECK_UPDATED` gate via lazy-imported
  `require_check_updated_provenance`; deterministic provenance-blocked
  record; worker `except` not broadened; `DECODER_FIELDNAMES` unchanged.
- [x] R04 — **Focused fake tests.**
  `comparison_bench/tests/test_v72p2d6_bp_provenance_compat.py`: six-value
  success; five-value incompatibility; `CHECK_UPDATED` pass-through; each
  refused provenance class; mixer/L2 spy silence on block; warmup
  readiness true/false; frozen dispatch/matrix pins. Run new tests + D6
  focused suites + BP interface regression, each in its own pytest process
  with fresh task-owned basetemps and `-p no:cacheprovider`. Zero real
  decoder.

## Non-goals

- No R05 independent implementation review, no R06 renewed Pre-EXECUTE,
  no R07 commits (later gates, other owners).
- No scientific/budget/terminal/schema change; no V35 or D6-module edits;
  no R1d execution or authorization.
