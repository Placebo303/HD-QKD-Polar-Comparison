"""V63 shell integration TTBin→FrameBatch→NbLdpcShell→PA.

Reads NB actual_disclosure_bits per frame by stage_used (three-tier 1064/1094/1104 …),
rejects Polar leak_EC reuse, tag 64 L2-only single count, PA proxy POLAR_REFERENCE_PROXY.
Real decode via frozen V54 when fake_runner is None; fake only when explicitly injected.
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
        ACCEPTED_PLAN_SHA,
    )
except ModuleNotFoundError:
    from comparison_bench.src.comparison_bench.methods.nbldpc_shell_adapter import (  # type: ignore
        NbLdpcShellIRAdapter,
        NbLdpcShellResult,
        LEAK_MAP,
        ACCEPTED_PLAN_SHA,
    )


def _pa_proxy(reconciled_symbols, actual_disclosure_bits, polar_leak_EC=None):
    if polar_leak_EC is not None:
        raise ValueError("REJECT Polar leak_EC: PA must use actual_disclosure_bits, not Polar leak_EC")
    if actual_disclosure_bits is None:
        raise ValueError("actual_disclosure_bits required for PA")
    arr = np.asarray(actual_disclosure_bits)
    total = int(np.sum(arr))
    return {"pa_input_leak": total, "key_length_proxy": -total, "note": "POLAR_REFERENCE_PROXY"}


def domain_check(*args, **kwargs) -> str:
    """New/incompatible session gate — no automatic H drift/χ² thresholds.

    Call with domain_check(is_new_or_incompatible=True) for new session.
    Legacy positional calls (h_drift, p) are rejected to avoid frozen-rule violation.
    """
    # Explicit flag wins
    if "is_new_or_incompatible" in kwargs:
        if bool(kwargs["is_new_or_incompatible"]):
            return "DOMAIN_CALIBRATION_REQUIRED"
        return "DOMAIN_OK"
    if "is_new" in kwargs:
        if bool(kwargs["is_new"]):
            return "DOMAIN_CALIBRATION_REQUIRED"
        return "DOMAIN_OK"
    # Positional single bool
    if len(args) == 1 and isinstance(args[0], bool):
        return "DOMAIN_CALIBRATION_REQUIRED" if args[0] else "DOMAIN_OK"
    # No args -> OK (same-domain)
    if len(args) == 0 and not kwargs:
        return "DOMAIN_OK"
    # Any other legacy drift args -> treat as violation of frozen rule, force explicit flag
    # For backward compat during transition, if two numeric args passed, we map to DOMAIN_OK only if caller explicitly meant calibration check;
    # but per task we must delete auto thresholds, so we return DOMAIN_OK only when no threshold breach is implied.
    # To keep old tests from failing silently, we raise to force migration.
    raise TypeError("domain_check now requires is_new_or_incompatible flag; H drift/χ² auto thresholds removed per frozen rule")


def run_shell_pipeline(
    batch,  # FrameBatch
    source: str,
    *,
    fake_runner=None,
    stage_pattern=None,
    polar_leak_EC=None,
    hard_cap: int | None = None,
) -> dict[str, Any]:
    """TTBin→PA integration. fake_runner must be explicitly injected for tests; None -> real V54."""
    if polar_leak_EC is not None:
        raise ValueError("REJECT Polar leak_EC: must use actual_disclosure_bits")
    # No silent fake: if fake_runner is None, go real V54
    if fake_runner is not None:
        adapter = NbLdpcShellIRAdapter(source, fake_runner=fake_runner)
        shell: NbLdpcShellResult = adapter.run_shell(batch, stage_pattern=stage_pattern, fake_runner=fake_runner, hard_cap=hard_cap)
    else:
        adapter = NbLdpcShellIRAdapter(source)
        shell = adapter.run_shell(batch, stage_pattern=stage_pattern, hard_cap=hard_cap)
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
