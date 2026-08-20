# V30R projective-safe finite-graph gate report

Date: 2026-08-20
Canonical evidence:
`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v30_20260820/run_01/`
Terminal: **`finite_graph_fail`**

## Executive result

V30R did not produce a finite code that passes the pre-registered validation
screen. The result is a valid, bounded negative result for the tested finite
conversion:

- `q=32`, `n=1024`, F03 natural MSB→LSB GF(32)+GF(32);
- V25/V26 source- and delay-conditioned channel semantics;
- source-adaptive finite leakage budgets and the V28 decoder;
- fixed `m1={9,12,16,24,32,40}` allocation candidates; and
- deterministic `balanced-projective` and
  `PEG-projective-cycle-cancelled` graph families.

It is not a route-wide impossibility theorem. V25's empirical channel result
and V26's channel-informed DE PASS remain valid within their own scopes. The
failure is at the finite graph/decoder conversion layer tested here.

## Evidence and gate sequence

### M0: predecessor structural audit

The V28R finite matrix was rebuilt read-only and reproduced exactly:

| quantity | value |
|---|---:|
| L1 support groups | 15 |
| maximum support multiplicity | 69 |
| duplicate projective classes | 303 |
| columns in duplicate classes | 922 |
| proportional-column / weight-2 pairs | 1107 |

These values establish why V30R required a projective-safe construction. They
are an audit of the predecessor, not a modification of it.

### M1: allocation DE

All pre-registered calls were persisted:

- 72 screen calls (`6 allocations × 2 seeds × 3 sources × 2 layers`);
- eligible screen allocations: `m1=9,12,16`;
- selected allocations: `m1_9` and `m1_12`;
- 60 confirmation calls (`2 selected allocations × 5 seeds × 3 sources × 2 layers`);
- both selected allocations confirmed `30/30`.

No unregistered call, tuning, or DE rerun occurred. The M1 resource meter was
`74.828 s`, below the 24-hour limit.

### M2: deterministic finite matrices

The two balanced-projective packets (`m1=9` and `m1=12`) passed the required
rank and projective-safety checks. The two PEG packets were retained as
deterministic rejections: for support `(0,1)`, no coefficient ratio remained
projectively unique under the frozen `GF2mField.create(32)` and
`nonzero_cycle` rule. This is a construction-family outcome, not a random
search failure; no replacement packet was permitted.

The bounded label rule was applied as specified: duplicate projective keys are
a hard zero gate, newly closed degenerate Tanner-6 cycles are minimized by
`(degenerate_6_new, ratio_index)`, and Tanner-8 is diagnostic topology only.

### M3: finite validation screen

The two valid balanced packets entered the fixed screen. For each packet, the
1M source reached blocks `0..5` and then became mathematically unable to meet
the `15/20` exact-and-tag-verified threshold:

| packet | completed blocks | exact | tag verified | false accepts | outcome |
|---|---:|---:|---:|---:|---|
| `m1_9\|balanced-projective` | 6 | 0 | 0 | 0 | matrix-local fail |
| `m1_12\|balanced-projective` | 6 | 0 | 0 | 0 | matrix-local fail |

The frozen early-stop rule therefore prevented 1p5M/2M screen blocks and all
confirmation blocks. This is why the evidence contains no claim about those
unrun source/block windows. The M3 decoder meter was `719.876 s`, also below
24 hours.

## Independent verification

The canonical `readonly_verify.json` reports:

```text
ok=true
problems=[]
recomputed_terminal=finite_graph_fail
persisted_terminal=finite_graph_fail
screen_call_count=72
confirmation_call_count=60
packet_count=2
no_de_rerun=true
no_decoder_rerun=true
```

The verifier reconstructed gate selection and terminal semantics from the
persisted evidence without rerunning DE or decoding. This separates the
engineering/replay result from the scientific conclusion.

## Scientific interpretation

The result isolates a finite-construction bottleneck after the following
earlier successes:

1. V25 identified a low-entropy, source/delay-conditioned adjacent-bin
   channel.
2. V26 showed that F03 GF(32)+GF(32) can converge under the channel-informed
   multilevel DE gate at `f=1.3`.
3. V27 showed finite leakage headroom at the block-length budgeting layer.
4. V28/V29 exposed that the first finite construction was structurally
   degenerate and failed the retrospective finite gate.
5. V30R removed the known projective duplicate/weight-2 defect for the valid
   balanced packets, but the resulting `n=1024` finite decoder still failed
   the earliest registered 1M validation screen.

Therefore the current evidence supports the narrower statement:

> The tested `n=1024` F03 allocations and the two V30R deterministic graph
> families did not convert the channel-informed DE success into a finite-code
> validation pass under the frozen V28 decoder.

It does not support saying that NBLDPC, GF(32)+GF(32), the empirical channel,
or the DE route as a whole is impossible.

## Closeout and successor boundary

V30R is archived with terminal `finite_graph_fail`. The same packet must not be
expanded, rerun, tuned, or supplemented with random degree/matrix search. V29
holdout data, raw `.ttbin`, fresh qualification, promotion, and public
residual claims remain excluded.

A future route requires a new user-authorized OpenSpec change. The most direct
engineering hypotheses are:

1. raise the shared L1 allocation toward `m1=16` and check projective-capacity
   margins before construction;
2. make PEG support selection explicitly projective-capacity-aware;
3. impose L2 girth/expander constraints or structured QC/SC construction; and
4. test `n=2048` or `n=4096` only after the new construction contract is
   frozen.

These are successor hypotheses, not automatic fallback actions. V30R makes no
qualification, integration, or promotion claim, and no push was performed.
