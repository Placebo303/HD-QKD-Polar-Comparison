# V11 R1 SMP-DE Reference Reproduction (V11-10.1 / V11-10.2)

Status: **reproduce_pass** (all four AEIT 2019 anchors reproduced within the
frozen absolute tolerance 0.002).

Date: 2026-08-06. Change:
`formal-nonbinary-ldpc-v11-sc-de-gate`, Stage E / R1 reference ladder
(design.md §2 R1, §5 Stage E).

## 1. Paper access and equation recovery (V11-10.1 step 1)

Equations were recovered from the accessible primary full texts, not from
memory:

- **Uncoupled SMP-DE**: F. Lázaro, A. Graell i Amat, G. Liva, B. Matuz,
  "Symbol Message Passing Decoding of Nonbinary Low-Density Parity-Check
  Codes," arXiv:1906.02537 (Globecom 2019), full text checked at
  `https://ar5iv.labs.arxiv.org/html/1906.02537`. Implemented equations:
  QSC transition (1), L-vector `D(eps)` (2)/(4), check-node DE (11) with the
  closed-form zero-sum probabilities `psi_{j,0}` (13), extrinsic channel
  `xi = 1 - s0` (12), and the exact variable-node DE (17) evaluated by
  exhaustive enumeration of the `dv - 1` incoming message symbols (frozen
  `dv = 3`, i.e. `q^2` pairs).
- **Coupled SMP-DE**: E. Ben Yacoub, F. Lázaro, A. Graell i Amat, G. Liva,
  "Symbol Message Passing Decoding of Nonbinary Spatially-Coupled
  Low-Density Parity-Check Codes," AEIT 2019, DOI 10.23919/AEIT.2019.8893373.
  Camera-ready full text checked at `https://elib.dlr.de/129944/1/AIET_SMP_camera_ready.pdf`
  (IEEE Xplore DOI redirect also resolves). Implemented equations: SC base
  matrix (3), check-node update (5), variable-node update (6), a-posteriori
  update (7), window `B[1:5W, 1:W]` with the frozen `W = 30` (Sec. V), and
  the first-block-column convergence criterion ("probability of correct
  decision for the VNs in the first block column is one").
- **Construction cross-check**: the AEIT paper prints the submatrix label
  `Bi = (1 1 ... 1)` with an underbrace reading "dc", which is inconsistent
  with rate 1/2 for `(3,6)` (a row of `dc` ones would give check degree 18
  and base rate 5/6). The primary construction source (Wei et al., ISIT
  2014, arXiv:1403.3583, full text checked) defines the rate-1/2 `(3,6)`
  SC ensemble `C[3,6]^{ms=2}` by `B = [3 3] => B0 = B1 = B2 = [1 1]`, i.e.
  `n0 = dc/dv = 2` VN types per spatial position, `w = dv - 1 = 2`. The
  module implements exactly this construction (`n0 = 2`, `B_i` a row of
  `n0` ones, `w = 2`), and the numerical reproduction below confirms it:
  a `dc`-wide row cannot produce the published coupled anchors. The "dc"
  underbrace is recorded as a typographical ambiguity in the paper, resolved
  by the primary construction source plus numerical confirmation.
- **Published anchors** (design.md R1 table) were verified directly against
  the AEIT camera-ready Tables I (uncoupled) and II (coupled): q=4
  `0.0890 / 0.0942`, q=16 `0.1075 / 0.1288`.

Sources attempted: IEEE Xplore DOI (metadata), DLR elib camera-ready PDF
(full text, used), arXiv:1906.02537 (uncoupled DE, used), arXiv:1403.3583
(construction, used), arXiv:1902.10391 (related, not needed). No blocker.

## 2. Implementation

- `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v11_smp_de.py`
  — paper-faithful SMP-DE module: `qsc_reliability` (`D(eps)`),
  `check_update_uncoupled` / `variable_update_uncoupled` (Globecom eqs.
  11–17), `run_smp_de_uncoupled`, `SCWindow` (AEIT eqs. 3–7 protograph),
  `check_update_coupled` / `variable_update_coupled` / `app_first_column`,
  `run_smp_de_coupled` (windowed, W=30), `threshold_binary_search`
  (bisection, `SEARCH_P_TOL = 0.001 <= 0.001` per design.md R1),
  `reproduce_ben_yacoub_2019` (four frozen `(q, mode)` cases with per-case
  trace + pass/fail grading).
- Module docstring records the scientific boundary: SMP exchanges only
  symbol estimates (not FFT-QSPA, not a full-probability-vector decoder),
  and **must not be reused as the GF(1024) scientific decoder**; the
  full-vector coupled MC-DE (V11-20.1) is a separate module.
- `comparison_bench/src/comparison_bench/cli/run_formal_nonbinary_v11_smp_de.py`
  — CLI: `--reproduce [--traces] [--out-dir]`, `--self-check`, and single
  `(q, mode)` threshold search with full trace.
- Imports: standard library + numpy only; never imports any V8/V9/V10
  module. No V8/V9/V10 file was modified.
- Reuse: `nonbinary_field.GF2mField` is available but not needed (the SMP-DE
  needs only the group structure of GF(2^m), which enters through the
  closed-form `psi` sums).

## 3. Reproduction run (V11-10.2)

Command (evidence workspace `workspace/nbldpc_v11_smp_de_v11_d2d183a8/`):

```
python -m comparison_bench.src.comparison_bench.cli.run_formal_nonbinary_v11_smp_de ^
    --reproduce --traces --out-dir workspace/nbldpc_v11_smp_de_v11_d2d183a8
```

Result (`status = reproduce_pass`; search tolerance 0.001, reproduction
tolerance 0.002, rate-1/2 `(3,6)`, W = 30):

| q | mode | published | reproduced | |deviation| | PASS |
|---:|---:|---:|---:|---:|---:|
| 4 | uncoupled | 0.0890 | 0.0888 | 0.000226 | PASS |
| 4 | coupled | 0.0942 | 0.0945 | 0.000278 | PASS |
| 16 | uncoupled | 0.1075 | 0.1072 | 0.000284 | PASS |
| 16 | coupled | 0.1288 | 0.1287 | 0.000081 | PASS |

All four values are within the frozen absolute tolerance 0.002; the largest
deviation is 0.000284 (q=16 uncoupled). No parameter tuning was performed;
the module and its constants were frozen before the run. The coupled gain
over the uncoupled control is reproduced in both field orders (q=4:
+0.0057 vs published +0.0052; q=16: +0.0215 vs published +0.0213).

## 4. Evidence files

- `evidence/reference/smp_de_trace.json` — schema `v11_smp_de_reproduction_v1`;
  per case: `published`, `reproduced`, `deviation`, `pass`, the full
  threshold-search probe list (p, converged, iterations), and the full
  per-iteration trace (`p0_trace` / `s0_trace` for uncoupled,
  `app_trace` for coupled) evaluated at the last verified-converged search
  bound; plus the frozen constants (`reproduction_tol`, `search_p_tol`,
  `dv`, `dc`, `W`) and the overall `status`.
- `evidence/reference/reference_reproduction.md` — this document.

Temporary run artifacts remain under `workspace/nbldpc_v11_smp_de_v11_d2d183a8/`
(the frozen evidence JSON was copied from there; the copy at
`evidence/reference/smp_de_trace.json` is byte-identical).

## 5. Tests (T0/T1)

`comparison_bench/tests/test_nonbinary_v11_smp_de.py`:

```
python -m pytest comparison_bench\tests\test_nonbinary_v11_smp_de.py ^
    -q -p no:cacheprovider --basetemp workspace/nbldpc_v11_tests_<uuid>
```

Result: **16 passed** (~190 s; includes the full four-case reproduction
shape test).

- T0: module import / `__all__` exports, frozen constants (`W_FROZEN = 30`,
  `REPRODUCTION_DV = 3`, `REPRODUCTION_DC = 6`, `REPRODUCTION_TOL = 0.002`,
  `SEARCH_P_TOL <= 0.001`, published anchor dict), function signatures,
  fail-closed domain validation.
- T1: noiseless limit (p = 0 -> p0/APP -> 1, converges), saturation limit
  (p = (q-1)/q -> 1/q uniform, no convergence), monotone threshold search
  consistent with the published anchor, trace completeness, determinism,
  window structure, bisection bracket invariants, reproduction function
  shape.

Three pre-existing test expectations were corrected during this pass
(test-authoring bugs only; no DE equation change, the module and its
reproduction results were already correct):

1. `run_smp_de_coupled` and `threshold_binary_search` signatures include the
   `W` parameter (the test previously asserted 4 names).
2. `p0_trace[0]` is the value after the first full iteration
   (0.9653 for q=4, p=0.05), not the initialization `1 - eps`; the assertion
   now checks the post-iteration improvement.
3. `search["converged_at_lo"]` is the status of the *last* bisection probe
   (parity-dependent; it is `False` in all four frozen evidence searches
   too). The test now asserts the meaningful bracket invariants: bracket
   width <= p_tol, proxy strictly inside the bracket, and a deterministic
   rerun at `p_lo` converges while a rerun at `p_hi` does not.

## 6. Scope compliance

- Allowed files touched: the new `nonbinary_v11_smp_de.py`, the new CLI,
  the new test file, and the two new evidence files under
  `evidence/reference/`. Nothing under `src/`, `experiments/`, `tools/`,
  `results/`, or `comparison_bench/outputs_comparison/` was modified; no
  V8/V9/V10 module was modified. `tasks.md` and `design.md` are untouched.
- Boundary: SMP is a reference-only ladder rung; no GF(1024) scientific
  execution, no decoder, no finite code, and no qualification claim is made
  from this evidence.
