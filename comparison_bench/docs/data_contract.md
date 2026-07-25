# Data Contract

Required input columns after normalization:

- `frame_id`
- `pair_idx`
- `alice_symbol`
- `bob_symbol`

Supported aliases include `frame`, `frame_idx`, `pair_id`, `pair_index`, `alice`, `alice_sym`, `a_eff`, `bob`, `bob_sym`, and `b_eff`.

Optional metadata columns are propagated when present: `loss_db`, `dimension`, `bin_width_ps`, `n_eff_pairs`, `threshold_ps`, `effective_pairing_window_ps`, `processing_rule_version`, and `pairing_path_tag`.

All new benchmark outputs are written under `comparison_bench/outputs_comparison/` and do not overwrite old Polar or security outputs.
