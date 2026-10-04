# P1 conditional information budget

This stage improves real-data design efficiency by measuring the disclosure overcount of independent bit planes relative to the full conditional chain, before choosing an MSD decoder or spending a decoding budget.

Track: EXPLORE for deterministic arithmetic on already approved saved aggregate counts. User authorization: 2026-10-05 sustained P1 → P2/P3 → P4 progression. No decoder, DE, new raw/frame reads, qualification, publication or push is authorized by this packet. Input construction from raw data requires a separately frozen DECIDE scope.

## Phase A: mathematical implementation

Ownership: Luna operator writes only `comparison_bench/src/comparison_bench/formal_ir/msd_information_budget.py` and `comparison_bench/tests/test_msd_information_budget.py`. Main thread owns this packet, OpenSpec and acceptance. Other agents may be editing independent files; preserve their edits.

Acceptance IDs:

- A1: validate finite nonnegative square power-of-two count matrices with positive mass; validate complete bit orders and encoding convention. Compute H(A), H(A|B), conditional plane entropies and information-density variances in bits and bits squared. Sum of plane entropies must equal H(A|B) within 1e-10.
- A2: distinguish marginal bit-error BSC entropy, unconditioned single-plane entropy given full Bob, and conditional-chain entropy. Compute joint information-density variance directly; do not sum plane variances as independent quantities.
- A3: expose N, joint failure assumption, verification tag and explicit budget. Normal approximation uses epsilon/plane and ceil(N H_k + sqrt(N V_k) z); clipping to [0,N] is reported. Label all outputs NORMAL_APPROX_SCENARIO, without a practical decoder or FER claim.
- A4: focused mathematical tests cover perfect correlation, independence, dependent planes and bit-order allocation, zero mass and invalid inputs, clipping, and tag/failure accounting. These trusted tiny distributions test identities; they are not synthetic decoding experiments.
- A5: an independent calculation must use grouped entropy differences and its own accounting, without calling the primary implementation, before any real-source numerical conclusion is accepted.

Ledger, in bits/block: H_A=N H(A), kept=H_A-L_EC, Y=kept-tag-kept p_fail; f_expected=(L_EC+tag+kept p_fail)/(N H(A|B)). Negative kept remains visible and invalidates the yield scenario. A zero denominator produces no finite f. All failure rates are assumptions until separately measured; a verification tag is charged once.

Use repository `.venv`, pytest `-p no:cacheprovider -o addopts=`, and a fresh `workspace/msd_p1_dev/<uuid>` base temp. Each initial mathematical smoke is capped at 120 seconds. No existing evidence or protected directories may be modified. A failing test stops acceptance; retain its report before any scoped correction.

## Phase B: saved aggregate execution — input freeze

Do not execute Phase B until a source manifest names the exact lossless C[a,b] artifact, axes, alphabet/encoding, count versus PMF convention, and original design/validation/holdout roles. CQ summary scalar entropies and support statistics cannot reconstruct this matrix. No substitute model may be invented.

Use only the three `<source>_N_ab_train_sparse.npz` files in `workspace/r1_histogram_5e2a91c4/`, for T2-1M, T2-1.5M and T2-2M. They are accepted materialized TRAIN inputs under `docs/research_cycles/V80-NBLDPC-JAN21/R1_INDEPENDENT_ACCEPTANCE.md`; the original raw-reading grant is not reused. COO row=Alice, col=Bob, alphabet=1024 natural bin indices. Reconstruct from row/col/count and verify shape, sum=N_train and nonnegative counts. Do not read p_b, frame vectors or raw files. This substitutes the accepted R1 TRAIN scope for the missing CQ full histograms; it cannot produce a CQ/VAL+HOLD conclusion.

Primary encoding is Gray g(x)=x^(x>>1); natural encoding is a separately labeled sensitivity comparison. Relabel both axes by the same bijection. Each encoding computes both LSB_FIRST and MSB_FIRST, N=1024 and 16384. Descriptive count estimands are unsmoothed plug-in entropies. Previously recorded Miller–Madow values or CI are not reused as CI for new plane quantities.

Scenario assumptions: joint failure 0.01, allocated equally to ten planes; one shared 64-bit verification tag per complete block. These are planning assumptions, not measured FER or the sister implementation's tag cadence. Historical 1104 is 1040 EC bits + 64 tag bits per 1024-symbol block. For 16384, display only the explicitly assumed equivalent EC density with one shared tag: budget=1040*N/1024+64. This is a projection, not an observed long-block baseline. Also report expected-f numerator, its slack against the projected budget, and f_expected with the failure penalty; nominal disclosure fit must not hide that penalty. No established practical code gap on these sources is available: report UNKNOWN, never fill it with a generic constant.

Operator command after focused tests: repository `.venv/bin/python -m comparison_bench.src.comparison_bench.cli.msd_information_budget --output-root <fresh workspace/msd_p1/<uuid>>`, under a 120-second timeout. `--smoke` computes just T2-2M Gray MSB_FIRST at N=1024 into a different fresh UUID root, first, also under 120 seconds. Full run ceiling 120 seconds, each source/order JSON is written immediately when complete, no resume/overwrite. Exact UUID paths and command are recorded in the log before launch. Timing artifacts are descriptive operator measurements, not scientific performance gains.

Independently recompute every numerical conclusion. Empirical aggregate results are descriptive and do not restore fresh holdout status to previously used data. A normal-approximation budget fit cannot accept practical decoder performance; failure to fit cannot close the MSD route. The next recommendation must account for approximation limits and source scope.

P1 runs no decoder and has no decoder effect-size/power gate. Before writing a P2 decoder experiment packet, specify the target real-efficiency effect, compute MDE at the handoff's power/significance requirements, and refuse execution if the frozen sample cannot resolve that target.

Return only after all frozen items are complete, or with a concrete failed command, full error, remedies attempted and the single decision needed. Main acceptance will recommend the next step with expected benefit and cost; it will not infer a route KILL from this diagnostic.
