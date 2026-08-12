# Architecture

`comparison_bench/` is an outer benchmark layer around the frozen Polar repository. New code lives under `comparison_bench/src/comparison_bench` and writes to `comparison_bench/outputs_comparison`.

The data flow is:

1. paired symbol table -> normalized frame batch
2. frame batch -> method adapter
3. method adapter -> `IRRunResult`
4. result rows + frame rows -> CSV/Parquet + manifest

The Polar adapter is intentionally non-invasive. It reads existing Polar outputs first and only calls existing scripts when a config explicitly requests CLI mode.
