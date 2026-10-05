# AGENT_PROJECT_MEMORY.md

This durable memory records stable repository structure, interfaces, data policy, and operating constraints. For the 2026-10-04 reboot, docs/REBOOT_HANDOFF_20261004.md is the sole handoff authority; its §5 governs the S1–S8 organization sequence. Older handoffs and snapshots do not supersede it.

## 1. Project and authority

- HD-QKD_Polar_Comparison is the formal information-reconciliation research mainline. Work stays on a named formal-ir branch; inspect the live branch before work. The sibling HD-QKD_Polar_Release is the binary Polar mainline; do not merge its line here.
- The copied Polar source and workflows are a frozen baseline. comparison_bench is an additive comparison wrapper. Historical filing under archive does not imply acceptance, validation, authorization, or promotion.
- AGENTS.md is the source for repository agent rules; OpenSpec is the source for approved behavior; this memory is durable structural and workflow context; docs/decision-log.md records durable decisions.
- Ponytail is disabled for this project. Delegated agents use luna_worker unless the user or an explicit named-role rule requires otherwise.

## 2. Current repository layout

- Root active files include AGENTS.md, AGENT_PROJECT_MEMORY.md, README.md, LICENSE, requirements.txt, pytest.ini, wsl-env.sh, .gitignore, and .gitattributes.
- Active areas include src/, experiments/, tools/, results/, comparison_bench/, docs/, analysis/, openspec/, archive/, and workspace/. The root archive/ holds history. Consult docs/archive/PATH_MAP.md for S3–S8 moves.
- comparison_bench/ contains configs, docs, src, tests, and outputs_comparison. Existing output roots remain read-only unless a separate explicit request authorizes a specific additive write.
- OpenSpec requirements and changes live under openspec/. For this reboot, docs/REBOOT_HANDOFF_20261004.md remains the unique handoff authority; NOW.md and INDEX.md are navigational summaries.
- workspace/ is local scratch and contains ignored machine artifacts. Use a fresh task/UUID subdirectory for new temporary artifacts. Do not clean, move, or delete the existing workspace tree unless specifically authorized.

## 3. Runtime and paths

- This host uses Windows with WSL support through wsl-env.sh. Use the repository .venv interpreter, not a system Python. For WSL, use .venv/bin/python and POSIX paths.
- wsl-env.sh defines PROJECT_DATA_ROOT, PROJECT_RESULTS_ROOT, TMPDIR, and PIP_CACHE_DIR. Treat the configured roots as defaults, not proof that external data is mounted.
- Historical Windows data paths are provenance only. Do not add them as new execution defaults.
- Tests that write temporary files use a fresh workspace/<task>/<uuid> root and pytest -p no:cacheprovider where appropriate.

## 4. Data, output, and scientific boundaries

- Raw/private data is external to the repository. Do not read it or run data pipelines without a separate, explicit authorization and a frozen scope.
- Do not overwrite results/ or comparison_bench/outputs_comparison/. Preserve original Polar outputs imported by the bridge. New comparison outputs use additive names only.
- Do not run longrun_*, minrerun_*, or routeA_* tools by default. Do not run experiments/run_e2e_pipeline.py against raw data by default.
- The user-selected main metric is f with expected yield: Y = kept − tag − kept·Σp̂ and f = (H_A − Y)/H(A|B); p̂ comes from out-of-sample validation frames. A zero-failure N_req certificate is not an experiment gate; the single-point f_eff ≤ 1.3 certification claim remains barred.
- R1: before writing a decoder-experiment packet, state the target effect and calculate MDE for the planned sample size at 80% power and α=0.05. If MDE exceeds the target effect, do not run; increase sample size or redesign.
- R2: the packet's first sentence states the expected real-frame f or expected-yield improvement and its evidence. If that benefit cannot be stated, do not run. Synthetic channels use models calibrated from a real empirical JOINT histogram; iid marginal-shape toy channels are not mainline evidence.
- R3: use expected-yield Y = kept − tag − kept·Σp̂, with p̂ from validation frames that do not overlap selection, and report f = (H_A − Y)/H(A|B) with paired multi-seed SE and lower bound. Zero-failure N_req is not an experiment gate; the single-point f_eff ≤ 1.3 certification claim remains barred.
- R4: before KILL, compare the conclusion with relevant theory and the read-only sibling implementation; do not use a known-suboptimal design to close a route.
- R5: derive every reported number with a script and independently recompute it; state units and make leakage/tag/failure penalties explicit. Before saying a document was updated, verify its change with git diff.
- R6: one route uses one OpenSpec change and one log. Avoid per-probe boilerplate. Batch closeout recommends the next step, expected efficiency benefit, and cost.
- R7: for a run expected to exceed 10 minutes, first run a timed smoke of at most 2 minutes; set the budget from measured per-block cost × block count × 1.5 and write results blockwise.
- R8: use scoped milestone commits, never git add -A, do not merge the sibling line, and push only after explicit user confirmation.
- R9: state only measured results and their scope; avoid unrestricted negative claims.
- No decoder, DE, real-data access, qualification, publication, push, deletion, or route-closing authority is inferred from this memory.
- Saved P1 inputs are the accepted R1 TRAIN COO count artifacts at workspace/r1_histogram_5e2a91c4/T2-1M_N_ab_train_sparse.npz, T2-1.5M_N_ab_train_sparse.npz and T2-2M_N_ab_train_sparse.npz. Rows are Alice, columns Bob, both natural time-bin indices. G-R1 acceptance covers materialized TRAIN/bundle design inputs, not decoder performance. The CQ roots retain summaries, insufficient to reconstruct these joint counts; R1 results cannot be described as CQ or fresh holdout results.
- Closed M0/M2/M3C records document subsequent use of the R1 VAL/HOLD pool. Treat it as previously used development/replay input unless a specific untouched subset is established; exact exposed indices and independent complete-symbol groups remain unknown. See the current MSD design and single exploration log; metadata counts and historical processing times do not establish pairing availability or decoder cost.
- MSD P1 uses these existing aggregates without decoding. Its normal-approximation scenarios freeze assumed failure and tag cadence in docs/research_cycles/MSD-REAL-CALIBRATED-MAINLINE/PREREG_AND_AUTH.md. Historical 1104 bits includes EC disclosure and verification at its original block length; long-block budget projections and expected-f failure penalties require separate explicit columns. No same-source practical code gap or propagation FER is established by P1.

## 5. Work lifecycle and Git

- Apply AGENTS.md EXPLORE/DECIDE gates. Real data, claim-bearing work, formal qualification, and route-closing decisions require DECIDE controls and explicit user authorization.
- Keep one OpenSpec change and one log per research route; do not multiply probe paperwork.
- Make scoped milestone commits only. Never stage everything with git add -A. Check live git status before each step. Do not merge the sibling line. Push only after the user explicitly confirms.
- At batch closeout, state the recommended next step, expected efficiency benefit, and cost. Keep conclusions bounded to the tested scope.
- The reboot S1–S8 plan was engineering-only and is complete; its archival actions do not grant scientific acceptance. Reboot D-1 (expected-yield f) and D-2 (stop the GF32 128-symbol single-knob line) are decided. The user separately authorized sustained staged P1→P2/P3→P4 progression on 2026-10-05. Stage-specific input, MDE and review gates remain; specific D-3 real-frame budget must be confirmed before execution. The eight-commit organization push grant is spent; later D-4 pushes require separate confirmation.

## 6. Schema and Interface Contract
- CSV columns that must not silently change:
  - normalized input columns: `frame_id`, `pair_idx`, `alice_symbol`, `bob_symbol` [repo-observed]
  - propagated metadata columns: `loss_db`, `dimension`, `bin_width_ps`, `n_eff_pairs`, `threshold_ps`, `effective_pairing_window_ps`, `processing_rule_version`, `pairing_path_tag` [repo-observed]
  - benchmark output columns include at least:
    - `dataset_id`, `data_mode`, `source_path`, `loss_db`, `dimension`, `bin_width_ps`, `n_eff_pairs`, `frame_len_symbols`, `frame_len_bits`, `method`, `method_variant`, `method_status`, `processing_rule_version`, `pairing_path_tag`, `threshold_ps`, `effective_pairing_window_ps`, `n_frames_total`, `n_frames_attempted`, `n_frames_success`, `n_frames_failed_decode`, `n_frames_failed_verify`, `accepted_frame_fraction`, `rejected_frame_fraction`, `raw_ser`, `raw_ber`, `post_ir_ser`, `post_ir_ber`, `leak_EC_actual_bits`, `leak_EC_per_frame`, `leak_EC_per_input_bit`, `beta_eff_empirical`, `runtime_s`, `throughput_input_bits_per_s`, `throughput_output_bits_per_s`, `notes`, `backend_status`, `error_message`, `real_ir_success`, `success_classification` [repo-observed]
  - frame-level output columns include at least:
    - `dataset_id`, `method`, `frame_idx`, `decode_success`, `verify_success`, `raw_frame_ser`, `raw_frame_ber`, `post_frame_ser`, `post_frame_ber`, `leak_bits_frame`, `iterations_used`, `runtime_ms` [repo-observed]
- JSON/YAML keys that must not silently change:
  - `datasets`, `methods`, `global` in benchmark YAMLs [repo-observed]
  - `output_dir`, `max_workers`, `frame_batch_path`, `polar_results_root`, `data_mode`, `frame_len_symbols`, `max_frames_per_dataset` in real-data benchmark YAML [repo-observed]
  - sweep config sections: `cascade`, `layered_ldpc`, `qldpc`, plus `cascade_config`, `layered_ldpc_config`, `qldpc_config` in the v3 master YAML [repo-observed]
- CLI arguments that must not silently change:
  - `build_dataset.py`: `--input`, `--output`, `--dimension`, `--frame-len-symbols`, `--dataset-id`, `--scan-sidecars` [repo-observed]
  - `build_representative_subset.py`: `--input`, `--output` [repo-observed]

  - `run_benchmark.py`: `--config` [repo-observed]
  - `compare_methods.py`: `--input`, `--output` [repo-observed]
  - `smoke_test.py`: `--config` [repo-observed]
  - `run_cascade_param_sweep.py`: `--config` [repo-observed]
  - `run_layered_ldpc_param_sweep.py`: `--config` [repo-observed]
  - `run_qldpc_param_sweep.py`: `--config` [repo-observed]
  - `run_ir_v3_master.py`: `--config` [repo-observed]
  - `make_report_tables.py`: `--config` [repo-observed]
- config keys that must not silently change:
  - method names: `polar_existing`, `cascade_lite`, `layered_ldpc_lite`, `qldpc_reference` [repo-observed]
  - v3 sweep keys including `block_size_schedule`, `num_passes`, `permutation_mode`, `seed`, `verify_mode`, `frame_caps`, `parity_fraction`, `max_iter`, `osd_order`, `bp_method`, `mapping`, `llr_mode`, `bitplane_rate_mode`, `check_fraction`, `row_weight`, `decoder`, `channel_model` [repo-observed]
- function signatures that must not silently change:
  - `FrameBatch`, `IRRunConfig`, `IRRunResult` dataclass fields in `comparison_bench/src/comparison_bench/types.py` [repo-observed]
  - `load_pairs_table(path: Path) -> pd.DataFrame` [repo-observed]
  - `normalize_pair_columns(df: pd.DataFrame) -> pd.DataFrame` [repo-observed]
  - `build_frame_batch(...) -> FrameBatch` [repo-observed]
  - `locate_existing_polar_outputs() -> list[Path]` and `run_polar_existing(batch: FrameBatch, cfg: IRRunConfig) -> IRRunResult` [repo-observed]
- output file naming conventions:
  - base benchmark outputs: `ir_benchmark_results.csv`, `ir_frame_results.parquet`, `run_manifest.json`, `ir_method_summary.csv` [repo-observed]
  - v3 outputs: `cascade_param_sweep_results.csv`, `layered_ldpc_param_sweep_results.csv`, `qldpc_param_sweep_results.csv`, `run_errors_ir_v3.csv`, `ir_v3_run_manifest.json`, `report_tables_v3/*.csv` [repo-observed]

## 7. Stable scientific semantics

- Keep leakage quantities method-specific and compare them only when their decomposition and denominator match.
- beta_eff_empirical must be derived from leakage and error inputs; never hand-fill it.
- Keep reference, stub, unavailable, decode_failed, and no_verified_success distinct from ok.
- qldpc_reference is a reference-grade path unless method status and evidence establish more.
- Separate FER, expected-yield f, security/key-rate claims, qualification, and publication acceptance. Evidence at one layer does not imply another.

## 8. Sources and retained history

- Current path and process decisions are in docs/decision-log.md; older entries remain available in its S5 archive copy. The current decision summary uses REBOOT-D-1 / REBOOT-D-2 prefixes to distinguish those decisions from historical M0/M2 D1/D2 and accounting D-1/D-2 labels.
- Archived summaries and machine artifacts retain historical evidence. This compact memory does not transcribe their per-run metrics or unfinished hypotheses.
- nonbinary_v10_fftqspa.py::check_update_all_log is an unconnected arithmetic candidate; the reference function and decoder default remain unchanged. Full-decoder equivalence and measured performance remain future gates. Its current scope is recorded under NBLDPC-MAINLINE-ENABLING.
- msd_conditional_prior.py builds ordered bit priors from joint counts, querying complete natural Bob symbols and decoded prefixes without Alice truth. Unsupported combinations return 0.5 with an explicit flag. Accepted scope is prior/soft-error mathematics only; decoder integration and performance remain separate. See MSD-REAL-CALIBRATED-MAINLINE/P2_IMPLEMENTATION_CONTRACT.md.
- msd_syndrome.py separates sender truth from receiver Bob/public syndromes, forwards per-variable priors through a mandatory explicit factory and propagates recovered prefixes. It counts all transmitted CSR rows; syndrome satisfaction is not verified success. Its accepted scope is fake-tested interface mathematics, with caller-owned graphs and no production backend execution or performance result. Opt-in skip_fully_deterministic bypasses backend calls only for an entirely exact-zero-error stage. Separately opt-in condition_exact_variables removes exactly zero error variables and structurally zero equations, preserves every positive/unsupported probability, and scatters errors before the original syndrome check; conflicting removed equations stop, and all original disclosure is charged. Empty-system MAP choices are not certainty. Both flags default off; TRAIN determinism does not imply OOS correctness or measured efficiency. This scope assumes the validated standard prior builder, not manually corrupted model tables. See the same P2 implementation contract.
- msd_sparse_code.py builds an explicit-parameter CSR H=[A|T] accumulator structural candidate with full row rank by T and reported four-cycle-avoidance fallback placements. Accepted scope is fixed structural mathematics, not optimized code performance or per-stage allocation; production decoding and empirical f/FER remain separate gates. C1-C6 are in the same MSD P2 contract.
- msd_error_allocation.py allocates the continuous normal backoff and separately reports ceil/clipped stage costs. Direct lower-tail quantiles avoid complement cancellation. Saved-summary arithmetic acceptance is limited to P1 TRAIN/normal assumptions; integer or practical optimality, OOS and code gap remain unestablished. See the same contract/log and ERROR_ALLOCATION_TABLE.md; PRE-K artifacts preserve their original provenance.

## Reboot organization completion context

Closed probe CLIs live under comparison_bench/src/comparison_bench/cli/probes_closed/, with their corresponding tests under comparison_bench/tests/probes_closed/. Short `comparison_bench.cli` and root `comparison_bench.src.comparison_bench.cli` lanes retain their existing import semantics; consult PATH_MAP for module changes. The small runner_support.py shares root/JSON/log/resource plumbing between the two census callers. Organization import/collection and fake plumbing checks do not establish numerical equivalence, FER, f or scientific acceptance. Execution restrictions remain binding even where archived code retains historical execute flags.

The approved archival lifecycle has four dispositions. Completed consolidates only its established reviewed scope; superseded-before-execution, executed-exploration-closed and retired-history-no-delta merge no delta. The fourth means currently not advanced with an individual source-supported reason, not permanent abandonment or scientific KILL; missing records remain unknown. Archived clauses require explicit successor adoption where applicable, with fresh scientific gates and separate user authorization. The current organization spec is openspec/specs/repository-organization/spec.md.

The quarantine is preserved in workspace/_quarantine_20261004/ and indexed by docs/archive/QUARANTINE_MANIFEST.md; no disposal is authorized. Current staged P1→P2/P3→P4 progression has the 2026-10-05 user grant. D-3 specific real-frame budget and any new D-4 push remain separately confirmable. Scientific scope and the stopped GF32 microprobe line remain binding.

- msd_outcome_accounting.py separates independent sender reference and candidate tags, accepted-wrong from verified yield, and actual native disclosure/tag with per-block kept-weighted failure penalties. Pairing checks complete-symbol volume and entropy denominators; caller owns source/role and actual tag protocol. Accepted scope is fixed fake-only accounting mathematics, not a data/protocol/FER or efficiency result. See the same MSD P2 contract/log. The older P2 power artifact assumes same native length/shared tags; revised short/long comparison requires its own range and cost derivation.
- User cancelled automatic reset-card redemption after resetting manually. Do not run card helpers, consume APIs, buy/exchange cards or re-enable the card task. See docs/NOW.md and docs/SESSION_HANDOFF_20261005_MSD_M_ACCEPTED.md for the operative boundary; past task-state checks are historical, not a current service snapshot.
