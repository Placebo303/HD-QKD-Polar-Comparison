#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from _security_audit_common import REPO_ROOT, ensure_output_dir, write_summary


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit current security model lineage.")
    ap.add_argument("--output-dir", default=str(REPO_ROOT / "results" / "_tmp_security_audit"))
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    output_dir = Path(args.output_dir)
    ensure_output_dir(output_dir, overwrite=bool(args.overwrite))
    out_path = output_dir / "security_model_lineage.md"

    lines = [
        "# Security Model Lineage Audit",
        "",
        f"Repository root: {REPO_ROOT}",
        f"Primary secure-rate implementation: {REPO_ROOT / 'experiments' / 'run_real_polar_max_pie.py'}",
        "",
        "## 1. Current ?_E lineage",
        "- File: `experiments/run_real_polar_max_pie.py`",
        "- Function: `main()`",
        "- Variables: `args.visibility`, `e_p`, `_E_P`",
        "- Logic: `e_p = max(0, min(0.5, (1 - visibility)/2))`.",
        "- File: `experiments/run_real_polar_max_pie.py`",
        "- Function: `_worker(...)`",
        "- Variables: `chi_e`, `_E_P`",
        "- Logic: `chi_e = h2(_E_P) + _E_P * log2(d - 1)` and `PIE_practical = max(0, best_hard_PIE - chi_e)`.",
        "- Current `chi_E_source_tag` is written as `visibility_assumed_interface`.",
        "- Interpretation: ?_E is **not** derived from measured Franson visibility traces in the current secure-rate path, **not** from a Gaussian-state estimator, and **not** from a decoy-state parameter-estimation pipeline. It is a fixed formula driven by a user-supplied visibility assumption.",
        "",
        "## 2. Current finite-key penalty lineage",
        "- File: `experiments/run_real_polar_max_pie.py`",
        "- Functions searched: `_worker(...)`, `main()`",
        "- Variables searched: `delta_fk`, `DeltaFK`, `finite_key`, `finite_size`, `eps_sec`, `eps_cor`, `epsilon`",
        "- Result: **MISSING** in the secure PIE / SKR formula.",
        "- Present finite-length logic only appears in reconciliation simulation controls: `--frames`, `_FER_THRESH`, `_SC_MARGIN`, `_SCL_MARGINS`, but these are decoder-operating heuristics, not composable finite-key secrecy penalties.",
        "- Conclusion: current `PIE_practical` has no explicit `?FK` term, no PE confidence interval term, and no composable epsilon budget.",
        "",
        "## 3. Current leak_EC / ? lineage",
        "- File: `experiments/run_real_polar_max_pie.py`",
        "- Function: `_worker(...)`",
        "- Variables: `sc_hard_PIE`, `cpp_scl_hard_PIE`, `best_hard_PIE`",
        "- Logic: `best_hard_PIE = max(sc_hard_PIE, cpp_scl_hard_PIE)` is used directly as the Alice-Bob secure-rate-side information term before subtracting `chi_E`.",
        "- Search result for explicit `beta`, `leak_EC`, `syndrome`, `privacy amplification`: **MISSING** from the secure-rate formula.",
        "- Interpretation: there is no explicit reconciliation efficiency factor and no explicit syndrome leakage accounting. `best_hard_PIE` acts as an implicit post-reconciliation information proxy.",
        "",
        "## 4. Decoy-state / multipair / single-pair handling",
        "- File: `src/workflow/export_joint_sequence_sidecar.py`",
        "- Functions: `_build_occupancy_filter_summary(...)`, pairing/materialization path under `materialize_real_sequences_for_point(...)`",
        "- Sidecar outputs include diagnostics such as `n_pairs_in_clean_frames`, `n_pairs_in_ambiguous_frames`, `clean_pair_fraction`, `both_multi_frame_fraction`.",
        "- File: `experiments/run_real_polar_max_pie.py`",
        "- Functions: `_canonical_nuisance_from_sidecar(...)`, `_claim_tags_from_sidecar(...)`",
        "- These diagnostics are exported into result tables as nuisance / claim tags only.",
        "- Search result for explicit decoy-state PE or single-pair fraction entering `PIE_practical` / `SKR_measured_bps`: **MISSING**.",
        "- Conclusion: multipair / ambiguous-frame effects are diagnosed, but not yet consumed by the current secure-rate formula.",
        "",
        "## 5. Post-selection security semantics (`exactly one detection by each party per frame`)",
        "- File: `src/workflow/export_joint_sequence_sidecar.py`",
        "- Variables: `occupancy_filter`, `frame_diag_available`, `clean_pair_fraction`",
        "- There is a diagnostic and optional filtered branch for candidate-pair ambiguity / multievent occupancy.",
        "- File: `experiments/run_real_polar_max_pie.py`",
        "- Current mainline claim tags record `candidate_pair_multievent_diagnostic_only` or filtered variants.",
        "- Search result for an explicit security-proof-side subtraction or post-selection correction entering `PIE_practical`: **MISSING**.",
        "- Conclusion: the implementation does not currently enforce a proof-grade `exactly one click each party per frame` security correction inside the secure-rate formula itself.",
        "",
        "## 6. Paper-target alignment",
        "### `security_paper_target = zhang_2013`",
        "- Expected shape: collective-attack / Franson-visibility-style Holevo treatment with protocol-specific parameter estimation and decoy treatment.",
        "- Gap vs current: ?_E uses a fixed visibility assumption, but there is no measured Franson-to-Holevo PE chain and no decoy-state security reduction in the rate formula.",
        "",
        "### `security_paper_target = zhong_2015`",
        "- Expected shape: experimental secure PIE style `beta * I_AB - chi_E - DeltaFK`.",
        "- Gap vs current: current code is **closest** to this style structurally, but only partially. It effectively computes `best_hard_PIE - chi_E` with `best_hard_PIE` as an implicit information proxy, and omits explicit `beta`, `leak_EC`, and `DeltaFK`.",
        "",
        "### `security_paper_target = niu_2016`",
        "- Expected shape: finite-key, composable, general-attacks-oriented treatment with epsilon budget, PE confidence bounds, and decoy / single-pair estimation where needed.",
        "- Gap vs current: **large**. The current mainline lacks explicit composable eps accounting, explicit finite-key secrecy terms, decoy-state PE, and proof-side single-pair fraction handling.",
        "",
        "## 7. Verdict",
        "- Current mainline classification: **neither strict Zhang/Zhong nor strict Niu**.",
        "- Closest label: **partial Zhong-like experimental secure PIE surrogate**.",
        "- Conservative audit verdict: the present implementation is much closer to `best_hard_PIE - chi_E` engineering evaluation than to a complete composable secure-key proof stack.",
        "",
        "## 8. Missing / simplified items summary",
        "- `beta`: MISSING as explicit factor",
        "- `leak_EC`: MISSING as explicit syndrome leakage term",
        "- `DeltaFK` / finite-key secrecy penalty: MISSING",
        "- `eps_sec`, `eps_cor`, composable epsilon budget: MISSING",
        "- decoy-state PE: MISSING in secure-rate path",
        "- single-pair / multipair proof-side correction: MISSING in secure-rate path",
        "- measured Franson/visibility PE entering ?_E: MISSING",
    ]
    write_summary(out_path, lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
