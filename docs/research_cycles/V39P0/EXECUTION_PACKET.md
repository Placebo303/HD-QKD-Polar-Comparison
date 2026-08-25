# V39P0 Authorized Development Execution Packet (DRAFT — NOT AUTHORIZED)

**Cycle**: `V39P0`
**Change ID**: `formal-ir-v39-lanec-robustness-laneb-control`
**Status**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`
**Development execution authorized**: `false`
**Formal execution authorized**: `false`
**Scientific promotion**: `false`
**Execution count if ever authorized**: exactly once

> This packet becomes operative only after (1) an independent plan review
> ACCEPT for cycle V39P0 and (2) a new explicit user `EXECUTE_AUTH` bound to
> the repository, branch, full accepted implementation target SHA, and scope
> `v39_decoder_only_105_calls_exactly_once`. Until both exist, no command
> below may be run.

## Planned authorized command (future)

```powershell
python scripts/execute_v39_development.py --development-execution-authorized
```

The flag is mandatory; the CLI has no fake-runner option and binds
`fake_runner=False`.

## Frozen scope of the single future run

1. Preflight (decoder-free): reconstruct all 18 Lane B/C matrices from
   accepted constructors and frozen seeds; strict-compare against the
   committed V38P0 27-record structural JSON (including Lane C
   `position_permutations`); run posterior-binding preflight P-BIND-1/2/3 on
   probe blocks 390101/390201/390301. Any failure -> BLOCKED before decode.
2. Exactly 105 real decoder calls:
   - lane_c: 3 sources x 3 construction seeds x 5 blocks = 45;
   - lane_b: 3 sources x 3 construction seeds x 5 blocks = 45;
   - v31_baseline: 3 sources x 5 blocks = 15, one call per block.
3. Blocks: 390101-390105 (1M), 390201-390205 (1p5M), 390301-390305 (2M);
   V25 TRAIN empirical counts; oracle-L1 conditioning; complete Bob symbol
   posterior binding.
4. Decoder: GF(32) polynomial 37, row-layered FFT-QSPA, max_iter=30,
   damping_alpha=1.0; success = `exact_l2 = np.array_equal(x_hat, u2_alice)`.
5. Write ONLY the additive files listed in design Section 15 under
   `comparison_bench/outputs_comparison/formal_ir_methods/v39_lanec_robustness_laneb_control/run_01/`.
6. Evaluate gates C1/B1/CB/BASE and emit exactly one terminal state with
   integrity-first precedence.

## Preflight stop rules

Before any decode: verify HEAD contains the accepted implementation SHA named
in the authorization; verify the output root does not exist; verify the V38P0
structural JSON has exactly 27 records; verify zero decoder calls so far.
Stop without execution if any check fails.

## Failure and no-rerun rules

If execution raises or writes a partial run root: retain everything unchanged,
return a concrete blocker (failing command, error, attempted remedies), and
wait for a main-thread decision. Do not delete, repair, resume, rerun, tune,
change seeds, add seeds, or relax thresholds. No warm start, no iteration-cap
increase, no damping search.

## Forbidden during execution

Touching V38/V38R1 code/tests/docs/outputs; touching results/run_01/run_02;
writing or reading any NPZ; modifying AGENT_PROJECT_MEMORY.md; drawing FER,
threshold, SKR, security, qualification, or promotion conclusions; marking
the result accepted.
