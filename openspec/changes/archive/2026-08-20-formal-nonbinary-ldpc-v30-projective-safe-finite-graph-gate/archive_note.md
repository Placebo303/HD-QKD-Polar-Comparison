# V30R archive note

Archived on 2026-08-20 after the canonical V30R execution and independent
read-only acceptance.

## Terminal and evidence

- Canonical run: `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v30_20260820/run_01/`
- Terminal: `finite_graph_fail`
- Independent verifier: `readonly_verify.json`, `ok=true`, `problems=[]`
- Recomputed terminal: `finite_graph_fail`
- M0: `support_groups=15`, `max_group=69`,
  `duplicate_projective_classes=303`, `affected_columns=922`,
  `proportional_weight2_pairs=1107`
- M1: 72 screen calls + 60 confirmation calls; selected allocations
  `m1_9,m1_12`, both confirmed 30/30
- M2: balanced packets for `m1=9,12` valid and projective-safe; PEG packets
  rejected for no projectively unique ratio on support `(0,1)`
- M3: both valid packets reached 1M screen blocks `0..5`, each with
  `0` exact/tag-verified blocks and `0` false accepts; the `15/20` threshold
  became impossible and the stage stopped before other sources and before
  confirmation
- Resource meters: M1 `74.828 s`; M3 `719.876 s`; neither reached 24 h

## Scientific boundary

This is a negative result for the tested finite conversion only:
`q=32`, `n=1024`, F03 natural MSB→LSB GF32+GF32, the fixed source-adaptive
leakage allocations, and the two deterministic balanced/PEG graph families
under the V28 decoder. It does not disprove the V25 empirical channel, the V26
channel-informed DE result, or nonbinary-LDPC designs outside this packet.

The failure does not authorize same-packet expansion, a rerun, random degree or
matrix search, decoder tuning, V29 holdout reuse, fresh qualification, or
promotion. No qualification, integration, or promotion claim is made.

## Successor boundary

Any successor requires a new user-authorized OpenSpec change. The recorded
direction is a finite-graph redesign, with priority candidates:

1. raise the shared L1 allocation toward `m1=16` and re-evaluate its
   projective-capacity margin;
2. use a projective-capacity-aware PEG support/label construction;
3. evaluate L2 girth/expander constraints and QC/SC structure; and
4. consider `n=2048` or `n=4096` after the construction contract is frozen.

These are planning hypotheses, not executed work or an automatic fallback.

No push was performed.
