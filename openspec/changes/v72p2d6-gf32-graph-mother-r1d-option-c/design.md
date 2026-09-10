# Design — V72P2D6 R1d Option C (eligible-only, minimal delta)

## 1. Reuse (import, never copy; no generalized framework)

All frozen machinery is reused unchanged: D5 prior/sampler/decoder adapter,
`build_support` / `assign_mother_from_support` (A4/A6 optimized path,
byte-identical outputs), `audit_prefix` + `audit_extra` + `check_I1_row_degree`,
`assert_dispatchable_matrices`, `execution_block_terminal`,
`select_advancement` / `structural_rank_list` / `classify_terminal`,
`a3_stage_partitions` / `a3_classify_evidence` / `a3_compare_terminals`,
RSS/wall/chunk/watchdog mechanics. R1d adds only a thin eligible-only dispatch
layer on top.

## 2. R1d dispatch layer (mother module, additive)

- `R1D_ARMS = [B0, B1, T1]` — the exact arm inventory; `assert_r1d_arm`
  raises on any SC/M/T2 arm (structurally inadmissible as frozen).
- `R1D_VALID_SUBSET` — frozen frozenset of the 26 `(arm,n,layer,prefix_rows)`
  cells proven in the A5 matrix (canary n64 f1.2+square ×3 arms;
  confirmation n64 f1.0/f1.2/square ×T1; scaling n128/n256 f1.2+square ×T1).
- `assert_r1d_dispatchable(arm,n,layer,prefix_rows,h_slice=None)` — fail-closed:
  membership in `R1D_VALID_SUBSET` AND live `check_I1_row_degree >= 2` on the
  slice when provided. Any other cell is a pre-dispatch hard failure.
- `R1D_SCALING_FALLBACKS = [T1]` — scaling fallback is T1 only; no M leg
  (no eligible M arm exists under I1).
- `enrich_r1d_records(records, mothers)` — adds `row_degree_min` /
  `rows_below_degree_2` to copies of the frozen record dicts by slicing the
  in-memory mothers (no rebuild, no shared-dict mutation, old writer unaffected).
- `write_structure_records_r1d` / `append_structure_records_r1d` — schema-v2
  header (frozen columns + `row_degree_min,rows_below_degree_2`) for NEW roots
  only. `R1D_STRUCTURE_SCHEMA = "r1d-v2"`,
  `R1D_ELIGIBLE_SEMANTICS = "frozen-AND-I1"` persisted as manifest/summary markers.

## 3. Runner mode (dev script, `--r1d` flag, default off)

When `--r1d` is set: every structure build passes `arms=R1D_ARMS`
(seq + parallel); selection is asserted to `{B0,B1,T1}` with
`fallback_T=T1` / `fallback_M=None`; scaling builds `arms=[T1]` with the
T1-only assert; `run_cell` additionally enforces `assert_r1d_arm` +
`assert_r1d_dispatchable` per dispatched prefix (gated on `state["r1d"]`,
frozen path untouched when off); structure evidence uses the r1d writers;
manifest/summary carry the schema marker; `--out-root` equal to the historical
A2 root (or any VOID root) is refused by name even before the exists-check.
`--verify` on an `r1d-v2`-marked root requires v2 columns and stored-vs-
recomputed I1 value agreement over every group (zero skip); unmarked/old roots
keep the exact old behavior (historical INFO path intact).

## 4. Why this shape (rejected alternatives)

- No per-arm config files or generalized successor framework: exactly one
  frozen triple exists; a framework would be speculative abstraction.
- No live matrix-CSV read in the guard: the subset is frozen into code so
  dispatch cannot drift with docs edits; the acceptance doc + tests pin the
  transcription against the committed CSV.
- No old-schema migration: historical A2 files stay byte-identical; `--verify`
  tolerates both schemas (marker selects strictness).
