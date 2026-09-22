## ADDED Requirements

### Requirement: Single-pair-member access with span-continuity guard (anti-double-count)
The census SHALL NEVER open both members of a `.ttbin` pair and concatenate (UNION): members are NESTED/SUPERSET via vendor auto-follow, NOT disjoint (authority `docs/TTBIN_MEMBER_SEMANTICS_20260921.md` §C — byte-identical `getConfiguration()`, shared acquisition start, vendor auto-follow docstring, 8 KB Jan-12 base alone spanning 29.9999524 s). The ONLY legal patterns are (i) open `X.ttbin` with auto-follow (primary) or (ii) `.1` shard-only as fallback. Every ingested stream SHALL pass the span-continuity assertion (span > 0 AND consistent with `.1`−base mtime gap) before any estimator or memory statistic is computed; a doubled stream corrupts `pairs`, `counts_ab`, `H_full`, support/occupancy, Miller–Madow, bootstrap CI, drift and autocorrelation alike.

#### Scenario: Both members concatenated
- **WHEN** an implementation opens `X.ttbin` and `X.1.ttbin` and unions the event streams
- **THEN** the run is invalid: every downstream number is refused as double-counted.

#### Scenario: Span-continuity mismatch
- **WHEN** span ≤ 0, span ≈ 2× the mtime gap (doubling), or span ≪ gap (truncation)
- **THEN** the dataset is STOP-BLOCKED and no `H_full` is produced for it.

### Requirement: Measured duration with disputed-tag quarantine
Duration SHALL be measured from the event-stream span, NEVER taken from the filename tag (authority `docs/TTBIN_MEMBER_SEMANTICS_20260921.md` §D — Jan-12 `3s` tag is WRONG at 29.9999524 s; Jan-21 tag correct at 2.9999997 s). Every row SHALL carry `duration_measured_s`, `filename_duration_tag`, and `tag_disputed`; Jan-12 SHALL be quarantined as `duration_measured_s=30.0`, `filename_tag_disputed=true` and SHALL NOT be pooled with 3 s acquisitions without explicit declaration.

#### Scenario: Filename tag trusted for duration
- **WHEN** a row reports duration from the filename without a measured span
- **THEN** it is refused pending the span measurement and tag comparison.

### Requirement: Single frozen H_full estimator with comparability reconciliation
The census SHALL estimate `H_full` per dataset as `H_L1 + H_L2` under factorization F03 (`u1 = A>>5`, `u2 = A&31`) using the plug-in conditional `P(a|b) = N_ab[a,b]/N_ab[:,b]` on the TRAIN pool, in bits per GF(32) symbol, exactly as `nonbinary_v26_channel.py::ChannelAdapter._build_entropy`; no second estimator convention SHALL be introduced, and V19's `0.549955` (a declared synthetic independence constant) SHALL NOT be averaged with, or subtracted from, a census number.

#### Scenario: A held-out number is quoted as a train-side number
- **WHEN** a `HOLD`-pool value is reported without declaring the split side
- **THEN** it is refused: every reported number SHALL state whether it is a TRAIN plug-in or a held-out cross-entropy.

#### Scenario: Cross-convention comparison proposed
- **WHEN** comparing a census `H_full` against V19's `0.549955` or a Family-A `d=256` value
- **THEN** the comparison is refused or explicitly labelled non-comparable, with the `comparable_by_anchor` flag set to `DIRECTIONAL-ONLY` or `NO`.

### Requirement: Bias and uncertainty reporting for every dataset
Each dataset row SHALL carry raw coincidence count `N`, support size, occupancy, a Miller–Madow corrected value `Ĥ_MM = Ĥ_plug + (K−1)/(2N·ln2)`, the held-out gap `Δ = NLL_HOLD − H_TRAIN`, and a frame-level bootstrap confidence interval (≥200 resamples, frozen seed); a bootstrap CI is mandatory for every dataset whose `H_full` is below the anchor `0.83256272`, and no `H_full` SHALL be used for a design-point decision without an uncertainty statement.

#### Scenario: Sparse histogram yields an attractive low H_full
- **WHEN** a dataset reports a low `H_full` with low support/occupancy and a wide bootstrap CI
- **THEN** it is marked `INSUFFICIENT-SUPPORT` when the CI half-width exceeds the frozen threshold, excluded from ranking, and still reported.

### Requirement: Memory and stationarity battery with pre-declared split
The census SHALL report, per dataset, the per-frame error-weight distribution (mean/median/min/max/p99), block-to-block drift statistics (per-block marginal/joint/`H_L1`/`H_L2`, max−min and least-squares slope), lag-1 and lag-2 autocorrelation of the per-frame mismatch count and per-frame `H_L1`, and a 60/20/20 consecutive-time TRAIN/VAL/HOLD split by ascending frame index whose manifest is written before any statistic is computed.

#### Scenario: Statistic computed before the split manifest exists
- **WHEN** an entropy, weight, drift, or autocorrelation value is computed before `split_manifest.json` is written
- **THEN** the run is invalid and must be re-executed from the split declaration.

#### Scenario: Positive drift or memory result
- **WHEN** the drift or autocorrelation statistics indicate non-trivial memory
- **THEN** the result is reported and escalated to the main thread as a finding that would invalidate synthetic-to-real transfer; the operator draws no route conclusion.

### Requirement: Alignment gating decision tree with explicit user choice
The census SHALL NOT silently select an alignment strategy. It SHALL present four branches — A1 (configured-only control on the Family-B trio), A2 (A1 plus Family A under its own declared `d=256` convention), B (empirical alignment estimation for unconfigured datasets), C (exclude unconfigured datasets) — and execution SHALL require the user to name exactly one branch in the signed authorization.

#### Scenario: Branch not named in the authorization
- **WHEN** execution is requested without a named branch in the SIGNATURE BLOCK
- **THEN** it is refused pending the user's explicit choice.

#### Scenario: Unconfigured dataset processed under Branch B without acceptance
- **WHEN** the selected channel pair is not the unique coincidence-throughput argmax with second-best ≤ 50 %, or the coincidence peak is not a single dominant mode
- **THEN** the dataset is STOP-BLOCKED and no `H_full` is produced for it.

### Requirement: Mandatory pre-pairing correlation-based delay auto-alignment
Before any pairing, histogram, or entropy step, the census SHALL derive the delay per dataset by cross-correlation and SHALL NOT pair until that alignment passes acceptance. Frozen procedure: `compute_cross_correlation_histogram(events, ch_a, ch_b, bin_width_ps=100, max_lag_ps=819200)` (16384 bins, lag convention `t_B − t_A`; authority `src/qkd_io/ttbin_pipeline.py:252-328`) → `pk = argmax(counts)` → `offset_ps = +lag_center_ps[pk]` (sign: offset added to side A in `_pair_nearest_unique`, `src/qkd_io/ttbin_pipeline.py:219-249`), no interpolation, derived ONCE on the vendor-auto-followed merged stream from the base member only (nested/superset prohibition binding), never per-frame. The recorded trio −50/+50 ps values SHALL be quoted as prior evidence only, never as inputs. Frozen acceptance (all required, else STOP-BLOCKED with no fallback to 0 or to any borrowed/recorded offset): `peak_to_bg ≥ 100` (median background excluding ±2 bins); single dominant mode [HEURISTIC — frozen rule: no secondary local maximum above 50% of primary outside ±1000 ps of `pk`]; crude ±12-bin sigma within 10–500 ps; ok-equivalent non-empty status. Every row SHALL carry `offset_ps_derived`, `peak_bin_index`, `peak_center_ps`, `peak_to_bg`, `sigma_crude_ps`, `align_status`, plus the prior offset for comparison only. A1 SHALL additionally require agreement with the recorded −50/+50 centres within one-bin tolerance (disagreement beyond one bin is a reported FINDING). The derived offset SHALL be reported as a derived measurement with acceptance status, and `H_full` SHALL be stated conditional on it. Alignment SHALL NOT be embedded into `compute_ttbin_metrics` (frozen `src/`).

#### Scenario: Pairing attempted without passed alignment
- **WHEN** any pairing/histogram/entropy step is requested with a frozen or default (0) `offset_ps` before alignment acceptance for that dataset
- **THEN** it is refused as STOP-BLOCKED; no `H_full` is produced for that dataset.

#### Scenario: Weak or ambiguous correlation peak
- **WHEN** `peak_to_bg < 100`, a second mode exceeds 50% of primary outside ±1000 ps, sigma falls outside 10–500 ps, or the histogram/status is empty
- **THEN** the dataset is STOP-BLOCKED; the offset SHALL NOT fall back to 0, SHALL NOT borrow another dataset's or any recorded value, and SHALL NOT be adopted.

### Requirement: Declared identifiability limit of empirical alignment
Under Branch B, the census SHALL label `bin_width_ps`, `frame_bins`, `align`, and `postselect` as `IMPOSED-NOT-MEASURED` (fixed at the V80 convention `d=1024`, `bin 200 ps`, `align=global`, `keep_all`), SHALL label every affected row `ALIGNMENT-FITTED`, and SHALL state in the result that coincidence-throughput fitting identifies the channel plan and window/offset but not the bin width or frame length.

#### Scenario: Fitted framing presented as measured
- **WHEN** a Branch-B output presents the imposed framing as estimated from the data
- **THEN** it is refused and must be relabelled `IMPOSED-NOT-MEASURED`.

#### Scenario: Branch-B delay presented as fitted rather than measured
- **WHEN** a Branch-B output presents the delay/offset as fitted when §3A correlation alignment applies
- **THEN** it is refused: the delay is MEASURED by correlation (§3A procedure + gates); only the channel plan and framing remain fitted/imposed.

### Requirement: Conditional certification arithmetic without operating-point claims
The census SHALL report, for each measured `H_full`, the conditional arithmetic `content = 1024·H_full`, `f_super(m) = (5m+64)/content`, `headroom = 1.3·content − (5m+64)`, and `N ≥ ⌈3·4.785675/(1.3 − f_super)⌉` at the integer `m_max(H) = ⌊(1.3·1024·H − 64)/5⌋`, and SHALL record that at the fixed A208 arm any `H_full < 0.829327` is out of box (`f_super > 1.3`); it SHALL NOT select an operating point, predict an FER, or claim a route decision.

#### Scenario: Census output used to select an operating point
- **WHEN** a census `H_full` is used to pick `m` or to assert `f_eff ≤ 1.3`
- **THEN** it is refused: that decision belongs to the main thread and requires `m_min`, which this census does not measure.

### Requirement: Zero-decode, read-only, additive-output execution
The census SHALL make zero decoder, DE, graph-construction, and `tools/*` calls; SHALL keep `src/qkd_io/ttbin_pipeline.py` and all frozen modules read-only; SHALL write only to a fresh additive `workspace/p3_census_<uuid8>` root; and SHALL NOT read any excluded derived artifact or overwrite anything under `results/` or `comparison_bench/outputs_comparison/`.

#### Scenario: Excluded derived artifact opened
- **WHEN** any `results*/`, `e2e_new_ttbin_fullgrid_*/`, `sidecars/`, `run_config*.json`, or analysis sidecar is opened for content
- **THEN** the action is refused per the inventory's exclusion rule.

### Requirement: Gated execution with explicit grant
No census execution SHALL occur without a signed `PREREG_AND_AUTH.md` naming the alignment branch, dataset list, config path, seed, tolerances and wall ceiling, followed by a recorded Pre-EXECUTE review, a single bounded execution and result record, an independent Pre-RESULT review, and main-thread acceptance; this change alone authorizes nothing. No Stage 1 census read SHALL occur before the separately-signed Stage 0.5 probe (`P3_STAGE05_PACKET.md`) has PASSED with its span-continuity assertion; every entrypoint SHALL call `install_timetagger_alias()` before any TimeTagger import and run with repo-root `PYTHONPATH` (Stage 0 PASS, `docs/TTBIN_ENV_SETUP_20260921.md`).

#### Scenario: Execution requested citing freeze alone
- **WHEN** execution is requested citing this frozen change or the frozen packet without a fresh signed grant
- **THEN** it is refused pending the signature and Pre-EXECUTE.
