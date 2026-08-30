"""V63 production shell IR adapter — wraps V54 frozen two-stage Δ8+8 nested.

Lifecycle: PLAN_REVISION_CANDIDATE -> production — real decode via frozen V54 L1APP+base+Δ8+Δ8,
fake_runner only when explicitly injected by tests. ponytail: minimal real wiring without extra framework.
"""
from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

for _p in [Path(__file__).resolve().parents[2], Path(__file__).resolve().parents[4]]:
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

try:
    from comparison_bench.methods.base import IRMethod
    from comparison_bench.types import FrameBatch, IRRunConfig, IRRunResult
except ModuleNotFoundError:
    from comparison_bench.src.comparison_bench.methods.base import IRMethod  # type: ignore
    from comparison_bench.src.comparison_bench.types import FrameBatch, IRRunConfig, IRRunResult  # type: ignore

Q_SUB = 32
SOURCE_ORDER = ("1M", "1p5M", "2M")
STAGE_ORDER = ("base", "delta8", "delta16")

LEAK_MAP: dict[str, dict[str, int]] = {
    "1M": {"base": 1064, "delta8": 1104, "delta16": 1144},
    "1p5M": {"base": 1094, "delta8": 1134, "delta16": 1174},
    "2M": {"base": 1104, "delta8": 1144, "delta16": 1184},
}
SOURCE_CHECKS: dict[str, int] = {"1M": 184, "1p5M": 190, "2M": 192}

# Accepted Plan SHA binding — must equal HEAD and origin/formal-ir-mainline exactly for EXECUTE_AUTH
ACCEPTED_PLAN_SHA = "397c1bb6d60cdf6dfa00d34bfae2eb1ca231d20a"

# Hard caps for budget accounting
SMOKE_HARD_CAP = 36  # 9 L1 + 9 base + ≤9 stage1 + ≤9 stage2 = 18-36
DEV_HARD_CAP = 360


def _load_tag_and_leak():
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
    reconciled_symbols: np.ndarray
    layer1_hat: np.ndarray | None = None
    layer2_hat: np.ndarray | None = None
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


ShellResult = NbLdpcShellResult


# --- Real V54 wiring (decoder-free fake removed from default path) ---
_V54_CACHE: dict[str, Any] = {}


def _get_v54_matrices(source: str):
    key = f"matrices_{source}"
    if key in _V54_CACHE:
        return _V54_CACHE[key]
    try:
        from comparison_bench.formal_ir.v54_two_stage_incremental_l2_rescue import reconstruct_v54_matrices
        from comparison_bench.formal_ir.v35_algorithm_development import GF2mField
    except ModuleNotFoundError:
        from comparison_bench.src.comparison_bench.formal_ir.v54_two_stage_incremental_l2_rescue import reconstruct_v54_matrices  # type: ignore
        from comparison_bench.src.comparison_bench.formal_ir.v35_algorithm_development import GF2mField  # type: ignore
    field = GF2mField.create(32)
    matrices = reconstruct_v54_matrices(field=field)
    _V54_CACHE["full_matrices"] = matrices
    _V54_CACHE["field"] = field
    return matrices


def _get_v54_counts():
    if "counts" in _V54_CACHE:
        return _V54_CACHE["counts"]
    try:
        from comparison_bench.formal_ir.v35_algorithm_development import load_v25_channel_counts
    except ModuleNotFoundError:
        from comparison_bench.src.comparison_bench.formal_ir.v35_algorithm_development import load_v25_channel_counts  # type: ignore
    counts = load_v25_channel_counts()
    _V54_CACHE["counts"] = counts
    return counts


def _real_shell_run(batch: FrameBatch, source: str, hard_cap: int | None = None) -> NbLdpcShellResult:
    """Real V54 frozen L1APP+base+Δ8+Δ8 wiring — verification-only incremental."""
    alice = np.asarray(batch.alice_symbols, dtype=np.int64)
    bob = np.asarray(batch.bob_symbols, dtype=np.int64) if batch.bob_symbols is not None else alice.copy()
    if alice.ndim != 2 or alice.shape[1] != 1024:
        raise ValueError(f"alice shape must be (n_frames,1024), got {alice.shape}")
    n_frames = int(alice.shape[0])
    # hard cap default based on n_frames (smoke 9 ->36, else 360)
    if hard_cap is None:
        hard_cap = SMOKE_HARD_CAP if n_frames <= 9 else DEV_HARD_CAP
    # Load frozen deps
    try:
        from comparison_bench.formal_ir.v35_algorithm_development import GF2mField, syndrome_of_gf32, decode_row_layered_fftqspa
        from comparison_bench.formal_ir.v54_two_stage_incremental_l2_rescue import (
            get_l1_prior_p_u1_given_b,
            get_l1_app_prior_l2,
            softmax_beliefs,
            compute_entropy_and_diff,
        )
    except ModuleNotFoundError:
        from comparison_bench.src.comparison_bench.formal_ir.v35_algorithm_development import GF2mField, syndrome_of_gf32, decode_row_layered_fftqspa  # type: ignore
        from comparison_bench.src.comparison_bench.formal_ir.v54_two_stage_incremental_l2_rescue import (  # type: ignore
            get_l1_prior_p_u1_given_b,
            get_l1_app_prior_l2,
            softmax_beliefs,
            compute_entropy_and_diff,
        )
    matrices = _get_v54_matrices(source) if "full_matrices" not in _V54_CACHE else _V54_CACHE["full_matrices"]
    if "full_matrices" not in _V54_CACHE:
        matrices = _get_v54_matrices(source)
        field = _V54_CACHE["field"]
    else:
        field = _V54_CACHE["field"]
        matrices = _V54_CACHE["full_matrices"]
    counts = _get_v54_counts()
    # Extract matrices
    H1 = matrices[("H1", "L1")][0]
    H_base = matrices[("lane_c", source)][0]
    H_joint1 = matrices[("h_joint1", source)][0]
    H_total = matrices[("h_total", source)][0]

    reconciled = np.empty_like(alice)
    accepted = np.zeros(n_frames, dtype=bool)
    exact = np.zeros(n_frames, dtype=bool)
    syndrome_ok = np.zeros(n_frames, dtype=bool)
    tag_ok = np.zeros(n_frames, dtype=bool)
    undetected = np.zeros(n_frames, dtype=bool)
    leak_per_frame = np.zeros(n_frames, dtype=np.int64)
    stage_used: list[str] = []
    u1_hat_all = np.zeros_like(alice)
    u2_hat_all = np.zeros_like(alice)
    truth_u1_all = np.zeros_like(alice)
    truth_u2_all = np.zeros_like(alice)

    total_calls = 0
    t0 = time.time()
    for i in range(n_frames):
        s_true = alice[i]
        b_sym = bob[i]
        u1_t, u2_t = decompose_symbols(s_true)
        truth_u1_all[i] = u1_t
        truth_u2_all[i] = u2_t
        # Budget check before L1
        if total_calls + 1 > hard_cap:
            from comparison_bench.formal_ir.v54_two_stage_incremental_l2_rescue import IntegrityFailure
            raise IntegrityFailure("J10", f"hard call cap {hard_cap} reached; call {total_calls+1} refused")
        # L1
        p_i = get_l1_prior_p_u1_given_b(counts[source], b_sym)
        s1 = syndrome_of_gf32(H1, u1_t, field)
        res_l1 = decode_row_layered_fftqspa(H1, p_i, s1, max_iter=90, damping_alpha=1.0, field=field)
        total_calls += 1  # L1
        q = softmax_beliefs(res_l1.final_beliefs)
        u1_hat = np.argmax(q, axis=1).astype(np.int64) % 32
        u1_hat_all[i] = u1_hat
        exact_u1 = bool(np.array_equal(u1_hat, u1_t))
        # prior for L2
        prior_l2 = get_l1_app_prior_l2(counts[source], b_sym, q)
        # base
        if total_calls + 1 > hard_cap:
            from comparison_bench.formal_ir.v54_two_stage_incremental_l2_rescue import IntegrityFailure
            raise IntegrityFailure("J10", f"hard call cap {hard_cap} reached")
        s_base = syndrome_of_gf32(H_base, u2_t, field)
        res_base = decode_row_layered_fftqspa(H_base, prior_l2, s_base, max_iter=90, damping_alpha=1.0, field=field)
        total_calls += 1
        empty = np.empty(0, dtype=np.uint8)
        target_tag = _compute_tag_64(empty, u2_t.astype(np.uint8))
        cand_base = _compute_tag_64(empty, res_base.x_hat.astype(np.uint8))
        syn_ok_base = bool(res_base.syndrome_ok)
        tag_ok_base = (cand_base == target_tag)
        verify_base = syn_ok_base and tag_ok_base
        exact_l2_base = bool(np.array_equal(res_base.x_hat, u2_t))
        if verify_base:
            # accepted at base, no incremental
            s_hat = recompose_symbols(u1_hat, res_base.x_hat.astype(np.int64))
            reconciled[i] = s_hat
            u2_hat_all[i] = res_base.x_hat.astype(np.int64)
            accepted[i] = True
            exact[i] = bool(exact_u1 and exact_l2_base)
            syndrome_ok[i] = True
            tag_ok[i] = True
            undetected[i] = bool(not exact[i])
            leak_per_frame[i] = LEAK_MAP[source]["base"]
            stage_used.append("base")
            continue
        # stage1 verification failure -> incremental
        if total_calls + 1 > hard_cap:
            from comparison_bench.formal_ir.v54_two_stage_incremental_l2_rescue import IntegrityFailure
            raise IntegrityFailure("J10", f"hard call cap {hard_cap} reached at stage1")
        s_joint1 = syndrome_of_gf32(H_joint1, u2_t, field)
        res_s1 = decode_row_layered_fftqspa(H_joint1, prior_l2, s_joint1, max_iter=90, damping_alpha=1.0, field=field)
        total_calls += 1
        cand_s1 = _compute_tag_64(empty, res_s1.x_hat.astype(np.uint8))
        syn_ok_s1 = bool(res_s1.syndrome_ok)
        tag_ok_s1 = (cand_s1 == target_tag)
        verify_s1 = syn_ok_s1 and tag_ok_s1
        exact_l2_s1 = bool(np.array_equal(res_s1.x_hat, u2_t))
        if verify_s1:
            s_hat = recompose_symbols(u1_hat, res_s1.x_hat.astype(np.int64))
            reconciled[i] = s_hat
            u2_hat_all[i] = res_s1.x_hat.astype(np.int64)
            accepted[i] = True
            exact[i] = bool(exact_u1 and exact_l2_s1)
            syndrome_ok[i] = True
            tag_ok[i] = True
            undetected[i] = bool(not exact[i])
            leak_per_frame[i] = LEAK_MAP[source]["delta8"]
            stage_used.append("delta8")
            continue
        # stage2
        if total_calls + 1 > hard_cap:
            from comparison_bench.formal_ir.v54_two_stage_incremental_l2_rescue import IntegrityFailure
            raise IntegrityFailure("J10", f"hard call cap {hard_cap} reached at stage2")
        s_total = syndrome_of_gf32(H_total, u2_t, field)
        res_s2 = decode_row_layered_fftqspa(H_total, prior_l2, s_total, max_iter=90, damping_alpha=1.0, field=field)
        total_calls += 1
        cand_s2 = _compute_tag_64(empty, res_s2.x_hat.astype(np.uint8))
        syn_ok_s2 = bool(res_s2.syndrome_ok)
        tag_ok_s2 = (cand_s2 == target_tag)
        verify_s2 = syn_ok_s2 and tag_ok_s2
        exact_l2_s2 = bool(np.array_equal(res_s2.x_hat, u2_t))
        s_hat = recompose_symbols(u1_hat, res_s2.x_hat.astype(np.int64))
        reconciled[i] = s_hat
        u2_hat_all[i] = res_s2.x_hat.astype(np.int64)
        accepted[i] = bool(verify_s2)
        exact[i] = bool(verify_s2 and exact_u1 and exact_l2_s2)
        syndrome_ok[i] = bool(syn_ok_s2)
        tag_ok[i] = bool(tag_ok_s2)
        undetected[i] = bool(verify_s2 and not exact[i])
        leak_per_frame[i] = LEAK_MAP[source]["delta16"]
        stage_used.append("delta16")

    runtime = time.time() - t0
    # Build IRRunResult (frozen signature, no actual_disclosure_bits field)
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
        runtime_s=float(runtime),
        throughput_input_bits_per_s=float((n_frames * 1024 * 10) / runtime) if runtime > 0 else 0.0,
        throughput_output_bits_per_s=0.0,
        metadata={"stage_used": list(stage_used), "source": source, "tag_scope": "l2_only", "decoder_calls": int(total_calls)},
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
        decoder_calls=int(total_calls),
        stage_used=list(stage_used),
        runtime_s=float(runtime),
        metadata={"source": source, "stage_used": list(stage_used), "tag_scope": "l2_only", "decoder_calls": int(total_calls)},
    )


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
        hard_cap: int | None = None,
    ) -> NbLdpcShellResult:
        # Explicit fake_runner only when injected by tests; otherwise real V54
        runner = fake_runner if fake_runner is not None else self.fake_runner
        if runner is not None:
            # test-only fake path — callable or True
            return self._run_via_runner(batch, stage_pattern, runner, hard_cap=hard_cap)
        # production real path
        return _real_shell_run(batch, self.source, hard_cap=hard_cap)

    def _fake_shell_run(self, batch: FrameBatch, source: str, stage_pattern=None) -> NbLdpcShellResult:
        return _fake_shell_run(batch, source, stage_pattern)

    def _run_via_runner(self, batch: FrameBatch, stage_pattern, runner, hard_cap: int | None = None) -> NbLdpcShellResult:
        alice = np.asarray(batch.alice_symbols, dtype=np.int64)
        if alice.ndim != 2 or alice.shape[1] != 1024:
            raise ValueError(f"alice shape must be (n_frames,1024), got {alice.shape}")
        if runner is True:
            return _fake_shell_run(batch, self.source, stage_pattern)
        if callable(runner):
            try:
                res = runner(batch, self.source, stage_pattern)
            except TypeError:
                res = runner(batch, self.source)
            if isinstance(res, NbLdpcShellResult):
                return res
            if isinstance(res, dict):
                return NbLdpcShellResult(**res)
            # if callable returns None or unexpected, fall through to fake for test compat
            if res is not None:
                return res  # type: ignore
        # no runner or unhandled -> real (should not happen in test fake path)
        return _real_shell_run(batch, self.source, hard_cap=hard_cap)


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

    _fake_calls_map = {"base": 2, "delta8": 3, "delta16": 4}
    total_fake_calls = int(sum(_fake_calls_map[s] for s in stage_used))
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
        metadata={"stage_used": list(stage_used), "source": source, "tag_scope": "l2_only", "decoder_calls": total_fake_calls},
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
        decoder_calls=total_fake_calls,
        stage_used=list(stage_used),
        runtime_s=0.01,
        metadata={"source": source, "stage_pattern": list(stage_used), "tag_scope": "l2_only", "decoder_calls": total_fake_calls},
    )


def leak_for(source: str, stage: str) -> int:  # noqa: F811 reuse name
    return leak_for_stage(source, stage)
