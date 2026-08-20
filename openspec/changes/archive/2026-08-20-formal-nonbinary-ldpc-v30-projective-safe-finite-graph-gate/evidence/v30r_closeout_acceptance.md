# V30R closeout acceptance note

Date: 2026-08-20
Run: canonical `run_01`
Scientific terminal: `finite_graph_fail`

The closeout review accepts the V30R execution as a valid, bounded negative
finite-code gate. The result is not a qualification or promotion result.

## Independent checks

`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v30_20260820/run_01/readonly_verify.json`
records:

- `ok=true`
- `problems=[]`
- `recomputed_terminal=finite_graph_fail`
- `persisted_terminal=finite_graph_fail`
- `screen_call_count=72`
- `confirmation_call_count=60`
- `packet_count=2`
- `no_de_rerun=true`
- `no_decoder_rerun=true`

## Gate interpretation

M0 reproduced the V28R structural defect counts exactly. M1 completed the full
registered screen and confirmation budgets; allocations `m1_9` and `m1_12`
were confirmed 30/30. M2 retained two valid balanced packets and two
deterministic PEG rejections due to the absence of a projectively unique ratio
for support `(0,1)`. M3's two valid packets failed the fixed 1M screen
impossibility condition after blocks `0..5`: `0/6` exact, `0/6`
tag-verified, and `0` false accepts for each packet. Therefore no other source
or confirmation block was authorized by the frozen stop rule.

The conclusion is restricted to the tested `n=1024` F03 finite conversion and
the frozen graph families/allocations. V25 channel evidence and V26 DE PASS
remain valid within their own lifecycle boundaries.

## Disposition

V30R is archived with all failure evidence retained. Do not expand the same
packet, rerun, tune the decoder, reuse V29 holdout frames, or start fresh
qualification. A future finite-graph redesign (for example `m1=16`,
projective-capacity-aware PEG, L2 girth/expander/QC/SC constraints, or larger
`n`) requires a new OpenSpec and explicit authorization.
