# D7-B easy-regime — spec delta

## Frozen matrix

- REQ-01: 64 cells = 4 tiers (SINGLE_CHECK_D3, TREE_6/A1, CYCLE_8,
  FULL_RANK_64) × 4 priors (P99/P90/P60/PAIR exact formulas) × 4 seeds
  (2026091200..2026091203 in order). No dynamic cells.
- REQ-02: TREE_6 active is literally n=6,m=3, row degs [3,3,2], c0=[0,1,2],
  c1=[2,3,4], c2=[4,5], coeffs [1,7,13]/[29,1,7]/[13,29]; var degs
  [1,1,2,1,2,1]; V=9,E=8,connected,acyclic,no-isolated,coeffs 1..31,rank 3 via
  D7-A oracle arithmetic. Any live [2,3,2] dispatch → BLOCKED.
- REQ-03: Caps [1,2,4,8,16,32,90] cold ascending with early stop on first
  exact+syndrome; later caps NOT_NEEDED_AFTER_EXACT. Global 420 hard stop
  (`D7_B_CALL_BUDGET_EXHAUSTED`) checked before each call; no silent reduction.
- REQ-04: Limits 120 s/call, 1500 s stored run wall, 1800 s outer + 30 s grace,
  < 2 GiB RSS (unknown blocks PASS). Finite required. Posterior tol 1e-10;
  determinism 1e-12.
- REQ-05: Terminal priority T1–T9 exactly as design; P60/PAIR never veto.
- REQ-06: Scalar-only five-file root (manifest.json, decoder_records.csv,
  summary.json, report.md, command_log.txt); fresh/refuse-overwrite/no-subdirs.
  Changes labeled CAP_PREFIX_PROXY; equivalence verified on D7-A tiny
  recurrence first.
- REQ-07: D7-A oracle reused; v35/D5 read-only; lazy decoder bind + DI;
  import/help/dry-run/unauthorized bind nothing and create no root.
- REQ-08: Authorization via cycle_state.yaml (`d7b_execution_authorized:
  false`); single UUID invocation consumes on first historical-decoder
  attempt; no retry/rerun/resume/reuse. Pre-RESULT review before any result.
- REQ-09: No Model-F/CAL/VAL/real/raw/formal/VOID reads (metadata-only root
  checks); no --phase/R1d/G1/G2; no SOP/workbuddy edits; no
  clean/reset/checkout/stash/rebase/amend/broad-stage/push.
