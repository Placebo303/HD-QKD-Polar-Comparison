# PATH_MAP — S3 root organization

Tracked files were moved with `git mv` on 2026-10-04. Historical document bodies were left unchanged; references inside them may retain the old paths below.

## Versioned root reports and artifacts

| Old root paths | New path (same basename) |
|---|---|
| `V65_CHANNEL_COMPATIBILITY_REPORT.md`, `v65_channel_compatibility.json`, `v65_data_readiness.json`, `v65_data_registry.json` | `archive/v65_v72p0/v65/` |
| `V67_FEASIBILITY_REPORT.md`, `v67_acquisition_inventory.json`, `v67_data_registry.json`, `v67_feasibility_table.csv`, `v67_feasibility_table.json`, `v67_manifest.json`, `v67_spike_summary.json` | `archive/v65_v72p0/v67/` |
| `V68_BALANCED_REPORT.md`, `v68_data_registry.json`, `v68_manifest.json`, `v68_results.json`, `v68_table.csv`, `v68_table.json` | `archive/v65_v72p0/v68/` |
| `V69_THREE_LAYER_REPORT.md`, `v69_data_registry.json`, `v69_manifest.json`, `v69_results.json`, `v69_table.csv`, `v69_table.json` | `archive/v65_v72p0/v69/` |
| `V70_BINARY_SOFT_JOINT_REPORT.md`, `v70_data_registry.json`, `v70_manifest.json`, `v70_results.json`, `v70_table.csv`, `v70_table.json` | `archive/v65_v72p0/v70/` |
| `V70R1_PARAMETRIC_CHANNEL_REPORT.md`, `v70r1_manifest.json`, `v70r1_results.json`, `v70r1_table.csv`, `v70r1_table.json` | `archive/v65_v72p0/v70r1/` |
| `V71_AUDIT_REPORT.md`, `V71_KERNEL_REPORT.md`, `v71_audit_report.json`, `v71_data_registry.json`, `v71_manifest.json`, `v71_results.json`, `v71_table.csv`, `v71_table.json` | `archive/v65_v72p0/v71/` |
| `V72P0_BACKEND_AUDIT_REPORT.md`, `V72P0_SYN_REPORT.md`, `v72p0_backend_audit_report.json`, `v72p0_data_registry_synthetic.json`, `v72p0_manifest.json`, `v72p0_results.json`, `v72p0_table.csv`, `v72p0_table.json` | `archive/v65_v72p0/v72p0/` |
| `test_v68_spike_small.py`, `test_v69_three_layer_small.py`, `test_v70_binary_soft_joint_small.py`, `test_v70r1_parametric_channel_model_small.py`, `test_v71_soft_joint_factor_kernel_small.py`, `test_v72p0_soft_joint_binary_synthetic_small.py`, `test_v72p1_soft_joint_adapter_small.py`, `test_v72p2_real_smoke_small.py` | `archive/v65_v72p0/tests/` |

## Other tracked root paths

| Old path | New path |
|---|---|
| `tmp_v27r/` | `archive/legacy_tmp/tmp_v27r/` |
| `tmp_v28r/` | `archive/legacy_tmp/tmp_v28r/` |
| `v72p1_synthetic_qual/` | `archive/legacy_tmp/v72p1_synthetic_qual/` |
| `bootstrap_clone_clean.py`, `dsh-opencode-go-pro.patch.yml`, `总体判断.txt` | `archive/misc/` with the same basename |
| `HANDOFF.md`, `AGENT_HANDOFF.md`, `CURRENT_TASK.md` | `docs/archive/handoffs/` with the same basename |
| `REVIEW_CHECKLIST.md`, `RUN_COMMANDS.md` | `docs/` with the same basename |

Untracked and ignored root clutter moved to `workspace/_quarantine_20261004/` is enumerated in [QUARANTINE_MANIFEST.md](QUARANTINE_MANIFEST.md). No tracked file was deleted. No change to the path-producing source was made: the scanned Python sources only showed the correctly joined `Path("workspace/v30r_tests") / ...` test roots; the producer of the malformed root artifact was not located.
