# Tasks: G1 readiness rework (coder-fast, candidate only)

Frozen authority: `G1_PACKET_REVIEW_R1.md` D1–D6 and A01–A13. Implement
exactly what is specified; if any task is ambiguous, stop and return to
planner (do not guess). Allowlist: core
`comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`
plus the two D5 test files; four new OpenSpec files; land the read-only
review file. No other file. No `cycle_state.yaml` change. No formal output.

- [x] T1 — Fresh root (I01, A01)
  - Set `G1_FORMAL_ROOT = "workspace/v72p2d5_g1/20260907_r2"` only; update
    owning tests; old VOID root untouched.
  - Verify: new literal present; old string absent as a G1 production
    target; pre/post VOID stat equal.

- [x] T2 — Windows RSS with frozen sampling (I02, A02)
  - Keep Unix `resource` path; add stdlib `ctypes`
    `GetCurrentProcess`/`GetProcessMemoryInfo` current-process working-set
    fallback with correctly sized `PROCESS_MEMORY_COUNTERS`; `None` when
    unavailable/false. Sample after every completed APP block; persist
    per-`f` and run maxima; `None`/>=2GiB blocks pass.
  - Verify: Unix path kept; monkeypatched success/failure tests green;
    sampling counts and maxima asserted.

- [x] T3 — Aggregate observability (I03, A03)
  - Per-`f` and run-level fields per design §3; scalar only; enforce
    identities (`failure_fraction = 1 - exact/attempted`,
    `app <= 100`, `oracle <= 20`, `attempted == 100`,
    `decoder_calls == 440`).
  - Verify: fake-decoder identity/bound tests green.

- [x] T4 — Signal rule, outcome, wall (I04, A13)
  - Implement the reviewed signal text, five-step completed-path precedence,
    `passed iff outcome == G1_TREND_PASS`, fail-loud exceptions, and
    entry→pre-evidence-write `wall_seconds` in `run_g1_synthetic`.
  - Verify: all-zero→NO_SIGNAL_FAIL; strict improve→TREND_PASS; 1.0,1.0→
    PASS; positive flat<1.0→fail; nonfinite/>900s/RSS precedence green.

- [x] T5 — Fail-loud writers (I05, A04)
  - Direct `float(item["app_failure_fraction"])` in both G1 and G2 writers;
    G1 outputs carry recompute fields; G2 grading/schema otherwise unchanged.
  - Verify: both writers raise loudly on a missing key.

- [x] T6 — No-subdirectory invariant (I06, A05)
  - Explicit invariant in BOTH test helpers; keep name/size/mtime snapshot;
    add tmp-only absent→created / present→nested-dir demonstration; no
    recursive hashing.
  - Verify: nested-dir creation caught in tmp roots.

- [x] T7 — Reachability contract (I07, A06)
  - Static + fake tests for the future external sentinel contract (first
    injected decoder call, accepted input shape, tmp empty); no real-root
    reads; real probe deferred.
  - Verify: contract tests green without touching the real Model-F root.

- [x] T8 — Focused + full suite, snapshots, commits (A07–A12)
  - Lifecycle-safe tests only (explicit fake decoder, injected arrays, tmp
    output); `py_compile` core + both D5 scripts; focused new+guards; full
    three-file D5 suite zero failures; pre/post formal-root stats identical;
    proposed G1/G2 roots absent; content-numstat scope clean; two
    path-by-path commits (review+OpenSpec, then core+tests); no push.
