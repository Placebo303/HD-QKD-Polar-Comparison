# M3-a nested 200+8 construction — EXPLORE packet

- Track: **EXPLORE** (synthetic construction only, zero decoder). `EXPLORE_HEAVY` is not needed; budget is at most 1200 s. Acceptance ID: `G-M3A-CONSTRUCT`; items `M3A-01..05` below.
- Hypothesis: constructing a full-rank, zero-four-cycle 200-row base before adding eight parity rows avoids the observed A208 prefix degree-0/1 defect. This packet measures structural feasibility only, not FER or the expected efficiency improvement.
- User grant: the 2026-09-26 instruction “需要的授权我现在都一次性给你……你只需要往下推进即可” covers this bounded synthetic construction after Pre-EXECUTE passes. No further authorization for the two frozen arms; any change to scientific inputs, budget, hypothesis or output root stops and needs a new packet.

## Frozen arms and code

Use exactly the two pairs `(base_seed, extension_seed)=(2026092001,2026096801)` and `(2026092011,2026096811)`, each base via `construct_standalone(200, seed, 20)`, n=1024, GF(32), λ={2:1}; append eight degree-10 rows by the OpenSpec `m3a-nested-200-plus-8/design.md` rule. No frame seeds, stream labels, channel bundle or .ttbin. Both arms run sequentially in this order, 2 constructs per arm for twice-identical comparison. Base/full rank 200/208, four_cycles 0/0, base variable degrees all 2, added row degree 10, base triples unchanged, new labels nonzero are hard gates. Girth and resource are measured, not gates. A pin failure is a retained terminal failure, not a search invitation.

## Output and budget

Fresh root `workspace/m3a_nested_200p8_20260926/` (must be absent at Pre-EXECUTE), with one JSON artifact per arm plus one append-only `EXPLORATION_LOG.md` in this directory and one independent batch-end review. One CPU, each arm ≤600 s, total ≤1200 s, RSS <2 GiB. No retry/resume; at most one preregistered infrastructure repair with inputs/seeds/thresholds unchanged and failed attempt retained in the same log. Scientific pin failure never qualifies for repair. Existing P1/X1/M0/M2 roots and `results/`/`outputs_comparison/` remain untouched.

## Pre-EXECUTE and stop

Before full construction, record branch/HEAD, scoped code/test/packet cleanliness, frozen arm table and command, focused fake-test PASS, output absence, protected-root status, and this grant verbatim. The exact command and passing gate are recorded below. STOP on a different branch, code/seed/degree change, output collision, test failure, any decoder/data read, budget miss or unexpected write.

### Pre-EXECUTE record — 2026-09-26, PASS

- User grant: “需要的授权我现在都一次性给你……你只需要往下推进即可” (2026-09-26); applicable to the two frozen synthetic arms.
- Branch/HEAD: `formal-ir-v72p1-addendum-clean` / `ce85d61f`; scoped implementation is the two new `m3a_nested_construct.py` and `test_m3a_nested_construct_fake.py` files under `comparison_bench/`, plus this cycle packet/OpenSpec. Existing unrelated dirty files are preserved. `git diff --check` exited 0 (only CRLF conversion warnings on pre-existing tracked docs). `git diff --stat -- src/ experiments/ tools/ results/ comparison_bench/outputs_comparison/` is empty.
- Frozen arms: `--arm 1` → `(2026092001,2026096801)`; `--arm 2` → `(2026092011,2026096811)`; n=1024, GF(32), base m=200, trials=20, 8 added degree-10 rows, two builds per arm. No other CLI arm accepted.
- Focused fake test, with injected base builder and no PEG: `wsl.exe --exec env PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison /mnt/d/Code/HD-QKD_Polar_Comparison/.venv/bin/python -m pytest -p no:cacheprovider /mnt/d/Code/HD-QKD_Polar_Comparison/comparison_bench/tests/test_m3a_nested_construct_fake.py --basetemp=/tmp/pytest-m3a-nested-200p8` → `9 passed, 1 warning in 2.86s` (pytest.ini unknown `cache_dir` warning only), operator report.
- Target root `workspace/m3a_nested_200p8_20260926/` absent before execution. One CPU is enforced with BLAS/OMP thread variables set to 1. Each call is capped at 600 s by `timeout`; two calls are sequential, total construction budget 1200 s. RSS cap is 2 GiB per arm; `/usr/bin/time -v` records it. The second call is not made if the first hits a budget or scientific pin failure.
- Exact arm-1 shell command from repository root (arm 2 substitutes `--arm 2`, `arm2.json`, `arm2.resource.txt`): `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 timeout -k 10 600 /usr/bin/time -v .venv/bin/python -m comparison_bench.src.comparison_bench.cli.m3a_nested_construct --arm 1 --execute-construction --execution-authorized > workspace/m3a_nested_200p8_20260926/arm1.json 2> workspace/m3a_nested_200p8_20260926/arm1.resource.txt`. Run only after creating the fresh root and its append-only `EXPLORATION_LOG.md`; check arm 1 status/resource before arm 2. No decoder or data source appears in this command.

## Acceptance / ceiling

- `M3A-01`: both bases have 1024 degree-2 variables, rank 200 and zero four-cycles, or an explicit retained failure.
- `M3A-02`: exactly eight degree-10 new rows, original prefix/labels unchanged and twice-identical per seed pair.
- `M3A-03`: full rank 208 and zero four-cycles per arm, or explicit retained failure; report girth separately.
- `M3A-04`: output/root/budget/zero-decoder boundary and one append-only log hold.
- `M3A-05`: one independent batch-end review checks both arms, repair if any, and claim ceiling.

Claim ceiling: construction feasibility on two pinned graph instances. No FER, `f_eff`, real-data benefit, operating point, route closure, SKR, or publication assertion.
