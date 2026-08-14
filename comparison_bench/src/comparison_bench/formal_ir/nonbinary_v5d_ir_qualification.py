"""Route D (nbldpc_formal_v5d_post) formal qualification lane.

Binds the shared v5 runtime to the frozen Route D contract: run ID, roots,
caps, source provenance (including the parallel exec wrapper per the
speed-up change handoff), and the v5d post core.  Plan/verify semantics are the
v4-proven lifecycle (see :mod:`nonbinary_v5_runtime`); execution goes
through :mod:`nonbinary_v5_exec_wrapper` (parallel/flush/resume).
"""
from __future__ import annotations

from . import nonbinary_v5_runtime as runtime
from . import nonbinary_v5d_post as core

RUN_ID = "20260731_v5d_nbldpc_post_synthetic"
ROOTS = {("development", .20): 202607840000, ("development", .30): 202607850000,
         ("confirmation", .20): 202607860000, ("confirmation", .30): 202607870000}
CAPS = {"workers": 1, "q": 1024, "n": 64, "checks_max": 56, "row_weight": 8,
        "stage_iterations": 12, "total_iterations": 36, "decoder_stages": 3,
        "verification_attempts": 3, "dense_bytes_max": 24 * 1024 * 1024}
_SRC = ("comparison_bench/src/comparison_bench/formal_ir/nonbinary_v5_runtime.py",
        "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v5_exec_wrapper.py",
        "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v5d_post.py",
        "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v5d_ir_qualification.py",
        "comparison_bench/src/comparison_bench/cli/run_formal_nonbinary_v5d_qualification.py",
        "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v5c_decoders.py",
        "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v5b_mother.py",
        "comparison_bench/src/comparison_bench/formal_ir/nonbinary_v3.py",
        "comparison_bench/src/comparison_bench/formal_ir/nonbinary_qspa.py",
        "comparison_bench/src/comparison_bench/formal_ir/nonbinary_field.py",
        "comparison_bench/src/comparison_bench/formal_ir/nonbinary_codebook.py",
        "comparison_bench/src/comparison_bench/formal_ir/shared.py",
        "comparison_bench/src/comparison_bench/cli/run_formal_nonbinary_v5_exec.py")
CONTRACT = "openspec/changes/formal-nonbinary-ldpc-v5-multistage-ir/specs/spec.md"

CONFIG = runtime.RouteConfig(
    run_id=RUN_ID, canonical_schema="NBLDPCQ5D", method=core.METHOD,
    q=core.Q, n=core.N, ps=(.20, .30), roots=ROOTS, caps=CAPS, seed_bits=703,
    core=core, source_files=_SRC, contract=CONTRACT, max_stages=3)


def create_plan(output=None, *, _test_only=False):
    return runtime.create_plan(CONFIG, output, _test_only=_test_only)

def run(output=None, *, runner=None, _test_only=False, fatal_hook=None):
    return runtime.run(CONFIG, output, runner=runner, _test_only=_test_only, fatal_hook=fatal_hook)

def verify(output=None, *, verifier_runner=None, _test_only=False):
    return runtime.verify(CONFIG, output, verifier_runner=verifier_runner, _test_only=_test_only)
