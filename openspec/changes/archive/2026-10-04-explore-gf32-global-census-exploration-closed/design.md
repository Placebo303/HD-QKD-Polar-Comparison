# Design

One small numpy CLI, explicit reader seam, pure small-graph math helper.
Preserve mapped source identity; output edge multiplicities, spectrum and
all51 cut calculations. Existing code remains read-only. No general runner.

Post-attempt implementation correction: Linux ru_maxrss is a high-water peak
in KiB and must multiply1024 for byte budget checks. The first attempt had
an incorrect conversion condition; preserve its raw artifacts and report
explicit audited unit correction. Fix default helper plus one mock test;
no scientific rerun or change to spectra/source/caps.
