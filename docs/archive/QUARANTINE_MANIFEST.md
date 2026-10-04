# S3 quarantine manifest

Recorded 2026-10-04. The root entries below were moved with PowerShell `Move-Item` into `workspace/_quarantine_20261004/`. They remain preserved and are not part of the S3 Git commit. Nothing was deleted. Counts are filesystem metadata; contents of the quarantined artifacts were not read.

| Original root path | Quarantine path | Observed inventory |
|---|---|---|
| `.pytest_cache/` | `workspace/_quarantine_20261004/.pytest_cache/` | 5 files, 2 directories, 13,371 regular-file bytes; Git-ignored pytest cache |
| `.pytest_l1d2_wall_20260930_650a19c1/` | `workspace/_quarantine_20261004/.pytest_l1d2_wall_20260930_650a19c1/` | 5 files, 2 directories, 59,237 regular-file bytes, 1 reparse link. The files include `arm_summary.csv`, `command_log.txt`, `frame_records.csv`, `graph_records.csv`, and `manifest.json`; `test_full_96x2_fake_rehearsal_current` was preserved as a link and not followed. |
| `.pytest_tmp_v33_ir1_20260823/` | `workspace/_quarantine_20261004/.pytest_tmp_v33_ir1_20260823/` | Empty directory |
| `.pytest-v3-coder/` | `workspace/_quarantine_20261004/.pytest-v3-coder/` | Empty directory |
| `CodeHD-QKD_Polar_Comparisonworkspacev30r_testsregression/` | `workspace/_quarantine_20261004/CodeHD-QKD_Polar_Comparisonworkspacev30r_testsregression/` | Empty path-concatenation artifact directory |
| `tmp1sqqq7kz/`, `tmp3qt0xb50/`, `tmp4ltygb8f/`, `tmp5s6irybz/`, `tmp5tj0qwnb/`, `tmp9ucamvgg/`, `tmpd_2btc3l/`, `tmppnkh1xhc/` | Same basenames under `workspace/_quarantine_20261004/` | Eight empty directories |
| `v39_review_tmp_20260825/` | `workspace/_quarantine_20261004/v39_review_tmp_20260825/` | Empty directory |
| `workspacegf32_full_eff_tests_20261002_e5/` | `workspace/_quarantine_20261004/workspacegf32_full_eff_tests_20261002_e5/` | 66 files, 37 directories, 8 reparse links, 1,219,546 regular-file bytes; nested pytest artifacts preserved without following links |
| `workspacegf32_full_eff_tests_20261002_full/` | `workspace/_quarantine_20261004/workspacegf32_full_eff_tests_20261002_full/` | 6 files, 3 directories, 1 reparse link, 250,474 regular-file bytes; nested pytest artifacts preserved without following links |
| `PROJECT.md` | `workspace/_quarantine_20261004/PROJECT.md` | 6,768 bytes; Git-ignored local brief |
| `ORIGINAL_REQUEST.md` | `workspace/_quarantine_20261004/ORIGINAL_REQUEST.md` | 5,891 bytes; Git-ignored local brief |

## Existing Git lock copy

An existing zero-byte file at `workspace/_quarantine_20261004/git_metadata/index.lock` was already present before these S3 moves and was left untouched. Its observed last-write time is `2026-09-27T08:26:42.4984420Z`. `.git/index.lock` is currently absent. Keep the quarantined copy; this task does not authorize deleting it.

## Path-concatenation search

The malformed paths `CodeHD-QKD_Polar_Comparisonworkspacev30r_testsregression/` and `workspacegf32_full_eff_tests_20261002_{e5,full}/` were quarantined. The source search command was `rg -n --glob '*.py' 'CodeHD-QKD_Polar_Comparisonworkspacev30r_testsregression|workspacegf32_full_eff_tests|v30r_tests|full_eff_tests' comparison_bench tests scripts pipelines`. Its matches were only `comparison_bench/tests/test_nonbinary_v30.py` lines 324, 521, 549, 663, 671, 679, 687, 759, 771, 780, 828, and 845; each uses `Path("workspace/v30r_tests") / ...`, which includes the separator. No producer for the malformed root paths was located, so no source change was guessed. Earlier broad searches also reported OS error 1920 at the preserved `current` reparse links; the containing roots were moved without following those links.
