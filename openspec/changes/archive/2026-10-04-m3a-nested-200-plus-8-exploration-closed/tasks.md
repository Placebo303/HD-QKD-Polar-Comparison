# M3-a tasks

- [ ] M3A-01 Implement the minimal in-memory extension helper and thin CLI in `comparison_bench/src/comparison_bench/cli/m3a_nested_construct.py`; do not edit frozen `formal_ir` or existing runners. Separate `construct(base_fn=...)` from `main()` so fake tests cannot call production construction implicitly.
- [ ] M3A-02 Add `comparison_bench/tests/test_m3a_nested_construct_fake.py` with tiny fake graphs covering prefix preservation, nonzero labels, deterministic two builds, no repeated variables/new four-cycles, and a fail-closed impossible-row case. No production PEG call in tests.
- [ ] M3A-03 Run only the focused fake test and return scoped file manifest/results. No synthetic full construction until the packet Pre-EXECUTE gate, no decoder/DE/data read, no commit/push.
