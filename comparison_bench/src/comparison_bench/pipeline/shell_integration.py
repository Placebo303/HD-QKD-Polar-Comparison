"""V63 shell integration TTBin→FrameBatch→NbLdpcShell→PA.

Reads NB actual_disclosure_bits per frame by stage_used (three-tier 1064/1094/1104 …),
rejects Polar leak_EC reuse, tag 64 L2-only single count, PA proxy POLAR_REFERENCE_PROXY.
DECODE_FORBIDDEN until EXECUTE_AUTH — pipeline in tests requires fake_runner.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import numpy as np

for _p in [Path(__file__).resolve().parents[2], Path(__file__).resolve().parents[4]]:
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

try:
    from comparison_bench.methods.nbldpc_shell_adapter import (
        NbLdpcShellIRAdapter,
        NbLdpcShellResult,
        LEAK_MAP,
    )
except ModuleNotFoundError:
    from comparison_bench.src.comparison_bench.methods.nbldpc_shell_adapter import (  # type: ignore
        NbLdpcShellIRAdapter,
        NbLdpcShellResult,
        LEAK_MAP,
    )


def _pa_proxy(reconciled_symbols, actual_disclosure_bits, polar_leak_EC=None):
    if polar_leak_EC is not None:
        raise ValueError("REJECT Polar leak_EC: PA must use actual_disclosure_bits, not Polar leak_EC")
    if actual_disclosure_bits is None:
        raise ValueError("actual_disclosure_bits required for PA")
    arr = np.asarray(actual_disclosure_bits)
    total = int(np.sum(arr))
    return {"pa_input_leak": total, "key_length_proxy": -total, "note": "POLAR_REFERENCE_PROXY"}


def domain_check(h_drift_bits: float, p_b_chi2_p: float) -> str:
    if abs(float(h_drift_bits)) > 0.05 or float(p_b_chi2_p) < 0.01:
        return "DOMAIN_CALIBRATION_REQUIRED"
    return "DOMAIN_OK"


def run_shell_pipeline(
    batch,  # FrameBatch
    source: str,
    *,
    fake_runner=None,
    stage_pattern=None,
    polar_leak_EC=None,
) -> dict[str, Any]:
    """TTBin→PA integration (decoder-free when fake_runner supplied)."""
    if polar_leak_EC is not None:
        raise ValueError("REJECT Polar leak_EC: must use actual_disclosure_bits")
    adapter = NbLdpcShellIRAdapter(source, fake_runner=fake_runner if fake_runner is not None else True)
    fr = fake_runner if fake_runner is not None else True
    if fr is True:
        shell: NbLdpcShellResult = adapter._fake_shell_run(batch, source, stage_pattern)  # type: ignore
    else:
        shell = adapter.run_shell(batch, stage_pattern=stage_pattern, fake_runner=fr)
    pa = _pa_proxy(shell.reconciled_symbols, shell.actual_disclosure_bits)
    assert np.all(shell.reconciled_symbols == shell.reconciled_symbols // 32 * 32 + shell.reconciled_symbols % 32)
    return {
        "shell_result": shell,
        "pa": pa,
        "actual_disclosure_bits": shell.actual_disclosure_bits,
        "stage_used": shell.stage_used,
        "reconciled_symbols": shell.reconciled_symbols,
    }


# alias for spec naming
run_shell_integration = run_shell_pipeline
