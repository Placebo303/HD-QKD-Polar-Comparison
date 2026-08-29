"""V63 production shell IR adapter — wraps V54 frozen two-stage Δ8+8 nested.

Lifecycle: PLAN_REVISION_CANDIDATE / DECODER_FREE_SPIKE — real decode guarded by EXECUTE_AUTH;
tests use fake_runner only. R63-01 32*u1+u2 contract, R63-02 IRRunResult frozen.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

# Ensure src on path for imports when running via `comparison_bench.src...` package
for _p in [Path(__file__).resolve().parents[2], Path(__file__).resolve().parents[4]]:
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

# Lazy imports for types — support both package layouts
try:
    from comparison_bench.methods.base import IRMethod
    from comparison_bench.types import FrameBatch, IRRunConfig, IRRunResult
except ModuleNotFoundError:
    from comparison_bench.src.comparison_bench.methods.base import IRMethod  # type: ignore
    from comparison_bench.src.comparison_bench.types import FrameBatch, IRRunConfig, IRRunResult  # type: ignore

# R63-01: full symbol factorisation s = 32*u1 + u2
Q_SUB = 32
SOURCE_ORDER = ("1M", "1p5M", "2M")
STAGE_ORDER = ("base", "delta8", "delta16")

LEAK_MAP: dict[str, dict[str, int]] = {
    "1M": {"base": 1064, "delta8": 1104, "delta16": 1144},
    "1p5M": {"base": 1094, "delta8": 1134, "delta16": 1174},
    "2M": {"base": 1104, "delta8": 1144, "delta16": 1184},
}
SOURCE_CHECKS: dict[str, int] = {"1M": 184, "1p5M": 190, "2M": 192}


def _load_tag_and_leak():
    """Try to load real V54 helpers; fallback to LEAK_MAP constants."""
    tag_fn = None
    leak_f = None
    leak1_f = None
    leak2_f = None
    checks = None
    try:
        from comparison_bench.formal_ir.v35_algorithm_development import compute_tag_64 as _tag
        from comparison_bench.formal_ir.v54_two_stage_incremental_l2_rescue import (
            leak_for as _lf,
            leak_stage1_for as _lf1,
            leak_stage2_for as _lf2,
            SOURCE_CHECKS as _sc,
        )
        tag_fn, leak_f, leak1_f, leak2_f, checks = _tag, _lf, _lf1, _lf2, _sc
    except Exception:
        try:
            from comparison_bench.src.comparison_bench.formal_ir.v35_algorithm_development import compute_tag_64 as _tag  # type: ignore
            from comparison_bench.src.comparison_bench.formal_ir.v54_two_stage_incremental_l2_rescue import (  # type: ignore
                leak_for as _lf,
                leak_stage1_for as _lf1,
                leak_stage2_for as _lf2,
                SOURCE_CHECKS as _sc,
            )
            tag_fn, leak_f, leak1_f, leak2_f, checks = _tag, _lf, _lf1, _lf2, _sc
        except Exception:
            pass
    return tag_fn, leak_f, leak1_f, leak2_f, checks


_tag_fn_cached, _leak_f_cached, _leak1_f_cached, _leak2_f_cached, _checks_cached = _load_tag_and_leak()


def _compute_tag_64(empty: np.ndarray, x2: np.ndarray) -> str:
    if _tag_fn_cached is not None:
        return _tag_fn_cached(empty, x2)
    # Fallback dummy L2-only tag (16 hex chars) for decoder-free tests when V35 unavailable
    import hashlib

    h = hashlib.sha256(x2.tobytes()).hexdigest()[:16]
    return h


def decompose_symbols(symbols: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    s = np.asarray(symbols, dtype=np.int64)
    return s // Q_SUB, s % Q_SUB


def recompose_symbols(u1: np.ndarray, u2: np.ndarray) -> np.ndarray:
    return (np.asarray(u1, dtype=np.int64) * Q_SUB + np.asarray(u2, dtype=np.int64)).astype(np.int64)


def leak_for_stage(source: str, stage: str) -> int:
    if _leak_f_cached is not None:
        if stage == "base":
            return int(_leak_f_cached(source))
        if stage == "delta8":
            return int(_leak1_f_cached(source))
        if stage == "delta16":
            return int(_leak2_f_cached(source))
    # fallback to frozen LEAK_MAP
    return LEAK_MAP[source][stage]


def _assert_leak_consistency() -> None:
    for src in SOURCE_ORDER:
        b = leak_for_stage(src, "base")
        s1 = leak_for_stage(src, "delta8")
        s2 = leak_for_stage(src, "delta16")
        assert s1 - b == 40 and s2 - s1 == 40, f"leak +40 failed {src}"
        m = SOURCE_CHECKS[src]
        assert b == 5 * m + 80 + 64, f"leak single-tag failed {src}"
        assert LEAK_MAP[src]["base"] == b


_assert_leak_consistency()


@dataclass
class NbLdpcShellResult:
    """Production wrapper — does NOT mutate IRRunResult signature (R63-02)."""

    ir_result: IRRunResult
    reconciled_symbols: np.ndarray  # (n_frames, 1024) full 0..1023 via 32*u1+u2
    layer1_hat: np.ndarray | None = None  # u1_hat per frame (for exact audit)
    layer2_hat: np.ndarray | None = None  # u2_hat
    truth_u1: np.ndarray | None = None
    truth_u2: np.ndarray | None = None
    accepted: np.ndarray = field(default_factory=lambda: np.array([], dtype=bool))
    exact: np.ndarray = field(default_factory=lambda: np.array([], dtype=bool))
    syndrome_ok: np.ndarray = field(default_factory=lambda: np.array([], dtype=bool))
    tag_ok: np.ndarray = field(default_factory=lambda: np.array([], dtype=bool))
    undetected: np.ndarray = field(default_factory=lambda: np.array([], dtype=bool))
    actual_disclosure_bits: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.int64))
    decoder_calls: int = 0
    stage_used: list[str] = field(default_factory=list)
    runtime_s: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_ir_run_result(self) -> IRRunResult:
        return self.ir_result


# alias for spec naming
ShellResult = NbLdpcShellResult


class NbLdpcShellIRAdapter(IRMethod):
    """Encapsulates V54 two-stage H1-16+L1APP+LaneC+Δ8+Δ8."""

    def __init__(self, source: str, *, fake_runner=None) -> None:
        if source not in SOURCE_ORDER:
            raise ValueError(f"source must be one of {SOURCE_ORDER}, got {source}")
        self.source = source
        self.fake_runner = fake_runner

    def run(self, batch: FrameBatch, cfg: IRRunConfig) -> IRRunResult:
        shell = self.run_shell(batch, cfg=cfg)
        return shell.to_ir_run_result()

    def run_shell(
        self,
        batch: FrameBatch,
        cfg: IRRunConfig | None = None,
        *,
        stage_pattern: list[str] | None = None,
        fake_runner=None,
    ) -> NbLdpcShellResult:
        runner = fake_runner if fake_runner is not None else self.fake_runner
        if runner is None:
            raise RuntimeError(
                "DECODE_FORBIDDEN: real V54 decode requires EXECUTE_AUTH + HEAD binding; "
                "pass fake_runner for decoder-free tests"
            )
        return self._run_via_runner(batch, stage_pattern, runner)

    def _fake_shell_run(self, batch: FrameBatch, source: str, stage_pattern=None) -> NbLdpcShellResult:
        return _fake_shell_run(batch, source, stage_pattern)

    def _run_via_runner(self, batch: FrameBatch, stage_pattern, runner) -> NbLdpcShellResult:
        alice = np.asarray(batch.alice_symbols, dtype=np.int64)
        if alice.ndim != 2 or alice.shape[1] != 1024:
            raise ValueError(f"alice shape must be (n_frames,1024), got {alice.shape}")
        if callable(runner) and runner is not True:
            try:
                res = runner(batch, self.source, stage_pattern)
            except TypeError:
                res = runner(batch, self.source)
            if isinstance(res, NbLdpcShellResult):
                return res
            if isinstance(res, dict):
                return NbLdpcShellResult(**res)
        return _fake_shell_run(batch, self.source, stage_pattern)


def _fake_shell_run(batch: FrameBatch, source: str, stage_pattern=None) -> NbLdpcShellResult:
    """Decoder-free fake that honors 32*u1+u2, L2-only tag, three-tier leak."""
    alice = np.asarray(batch.alice_symbols, dtype=np.int64)
    n_frames = int(alice.shape[0])
    rng = np.random.default_rng(0)
    if stage_pattern is None:
        stage_used = rng.choice(list(STAGE_ORDER), size=n_frames, p=[0.7, 0.15, 0.15]).tolist()
    else:
        stage_used = list(stage_pattern)
        if len(stage_used) != n_frames:
            raise ValueError(f"stage_pattern len {len(stage_used)} != n_frames {n_frames}")
    reconciled = np.empty_like(alice)
    accepted = np.zeros(n_frames, dtype=bool)
    exact = np.zeros(n_frames, dtype=bool)
    syndrome_ok = np.zeros(n_frames, dtype=bool)
    tag_ok = np.zeros(n_frames, dtype=bool)
    undetected = np.zeros(n_frames, dtype=bool)
    leak_per_frame = np.zeros(n_frames, dtype=np.int64)
    u1_hat_all = np.zeros_like(alice)
    u2_hat_all = np.zeros_like(alice)
    truth_u1_all = np.zeros_like(alice)
    truth_u2_all = np.zeros_like(alice)

    for i in range(n_frames):
        s_true = alice[i]
        u1_t, u2_t = decompose_symbols(s_true)
        truth_u1_all[i] = u1_t
        truth_u2_all[i] = u2_t
        is_accept = True
        is_exact = bool(rng.random() < 0.8)
        if is_exact:
            s_hat = s_true.copy()
        else:
            s_hat = (s_true + 1) % 1024
        u1_h, u2_h = decompose_symbols(s_hat)
        assert np.all(recompose_symbols(u1_h, u2_h) == s_hat), "32*u1+u2 recomposition failed"
        empty = np.empty(0, dtype=np.uint8)
        _tag = _compute_tag_64(empty, u2_h.astype(np.uint8))
        assert isinstance(_tag, str) and len(_tag) == 16
        u1_hat_all[i] = u1_h
        u2_hat_all[i] = u2_h
        reconciled[i] = s_hat
        accepted[i] = bool(is_accept)
        exact[i] = bool(is_accept and is_exact)
        syndrome_ok[i] = bool(is_accept)
        tag_ok[i] = bool(is_accept)
        undetected[i] = bool(is_accept and not is_exact)
        leak_per_frame[i] = LEAK_MAP[source][stage_used[i]]

    ir = IRRunResult(
        dataset_id=batch.dataset_id,
        method="nbldpc_shell",
        method_variant=f"V54-two-stage-{source}",
        frame_len_symbols=1024,
        frame_len_bits=1024 * 10,
        n_frames_total=n_frames,
        n_frames_attempted=n_frames,
        n_frames_success=int(np.sum(accepted)),
        n_frames_failed_decode=int(np.sum(~accepted)),
        n_frames_failed_verify=0,
        raw_ser=0.0,
        raw_ber=0.0,
        post_ir_ser=0.0,
        post_ir_ber=0.0,
        leak_EC_actual_bits=float(np.sum(leak_per_frame)),
        leak_EC_per_frame=float(np.mean(leak_per_frame)) if n_frames else 0.0,
        leak_EC_per_input_bit=float(np.mean(leak_per_frame) / (1024 * 10)) if n_frames else 0.0,
        beta_eff_empirical=float("nan"),
        runtime_s=0.01,
        throughput_input_bits_per_s=0.0,
        throughput_output_bits_per_s=0.0,
        metadata={"stage_used": list(stage_used), "source": source, "tag_scope": "l2_only"},
    )
    return NbLdpcShellResult(
        ir_result=ir,
        reconciled_symbols=reconciled,
        layer1_hat=u1_hat_all,
        layer2_hat=u2_hat_all,
        truth_u1=truth_u1_all,
        truth_u2=truth_u2_all,
        accepted=accepted,
        exact=exact,
        syndrome_ok=syndrome_ok,
        tag_ok=tag_ok,
        undetected=undetected,
        actual_disclosure_bits=leak_per_frame,
        decoder_calls=int(n_frames * 2),
        stage_used=list(stage_used),
        runtime_s=0.01,
        metadata={"source": source, "stage_pattern": list(stage_used), "tag_scope": "l2_only"},
    )


def leak_for(source: str, stage: str) -> int:  # noqa: F811 reuse name
    return leak_for_stage(source, stage)
