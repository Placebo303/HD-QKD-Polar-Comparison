from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
from typing import Any

@dataclass
class ShellResult:
    ir_result: Any
    reconciled_symbols: np.ndarray
    accepted: np.ndarray
    exact: np.ndarray
    syndrome_ok: np.ndarray
    tag_ok: np.ndarray
    undetected: np.ndarray
    actual_disclosure_bits: np.ndarray
    decoder_calls: int
    stage_used: list
    pa_leak: int
    metadata: dict = field(default_factory=dict)

LEAK_MAP = {
    "1M": {"base":1064, "delta8":1104, "delta16":1144},
    "1p5M": {"base":1094, "delta8":1134, "delta16":1174},
    "2M": {"base":1104, "delta8":1144, "delta16":1184},
}

def decompose_symbols(symbols: np.ndarray):
    s = np.asarray(symbols, dtype=np.int64)
    u1 = s // 32
    u2 = s % 32
    return u1, u2

def recompose_symbols(u1, u2):
    return (np.asarray(u1, dtype=np.int64)*32 + np.asarray(u2, dtype=np.int64)).astype(np.int64)

def fake_nbldpc_shell_run(batch, source: str, stage_pattern=None):
    alice = np.asarray(batch.alice_symbols)
    n_frames = alice.shape[0]
    rng = np.random.default_rng(0)
    if stage_pattern is None:
        stage_used = rng.choice(["base","delta8","delta16"], size=n_frames, p=[0.7,0.15,0.15])
    else:
        stage_used = np.array(stage_pattern)
    reconciled = np.empty_like(alice)
    accepted = np.zeros(n_frames, dtype=bool)
    exact = np.zeros(n_frames, dtype=bool)
    syndrome_ok = np.zeros(n_frames, dtype=bool)
    tag_ok = np.zeros(n_frames, dtype=bool)
    undetected = np.zeros(n_frames, dtype=bool)
    leak_per_frame = np.zeros(n_frames, dtype=int)
    for i in range(n_frames):
        s_true = alice[i]
        is_accept = True
        is_exact = bool(rng.random() < 0.8) if is_accept else False
        if is_exact:
            s_hat = s_true.copy()
        else:
            s_hat = (s_true + 1) % 1024
            if rng.random() < 0.1:
                is_accept = True
                is_exact = False
        u1_hat, u2_hat = s_hat //32, s_hat %32
        assert np.all((u1_hat*32+u2_hat)==s_hat), "recomposition fails 32*u1+u2"
        reconciled[i] = s_hat
        accepted[i] = bool(is_accept)
        exact[i] = bool(is_exact)
        syndrome_ok[i] = bool(is_accept)
        tag_ok[i] = bool(is_accept)
        undetected[i] = bool(is_accept and not is_exact)
        leak_per_frame[i] = LEAK_MAP[source][stage_used[i]]
    from comparison_bench.src.comparison_bench.types import IRRunResult
    ir = IRRunResult(
        dataset_id=batch.dataset_id,
        method="nbldpc_shell_fake",
        method_variant="fake",
        frame_len_symbols=1024,
        frame_len_bits=1024*10,
        n_frames_total=n_frames,
        n_frames_attempted=n_frames,
        n_frames_success=int(np.sum(accepted)),
        n_frames_failed_decode=int(np.sum(~accepted)),
        n_frames_failed_verify=0,
        raw_ser=0.0, raw_ber=0.0, post_ir_ser=0.0, post_ir_ber=0.0,
        leak_EC_actual_bits=float(np.sum(leak_per_frame)),
        leak_EC_per_frame=float(np.mean(leak_per_frame)) if n_frames else 0,
        leak_EC_per_input_bit=float(np.mean(leak_per_frame)/(1024*10)) if n_frames else 0,
        beta_eff_empirical=float("nan"), runtime_s=0.01,
        throughput_input_bits_per_s=0.0, throughput_output_bits_per_s=0.0,
        metadata={"stage_used": list(stage_used), "fake": True},
    )
    return ShellResult(
        ir_result=ir, reconciled_symbols=reconciled, accepted=accepted, exact=exact,
        syndrome_ok=syndrome_ok, tag_ok=tag_ok, undetected=undetected,
        actual_disclosure_bits=leak_per_frame, decoder_calls=n_frames*2,
        stage_used=list(stage_used), pa_leak=int(np.sum(leak_per_frame)),
        metadata={"source": source, "stage_pattern": list(stage_used)},
    )

def test_32_u1_u2_factorization():
    for s in [0,31,32,63,1023,512,1022]:
        u1, u2 = s//32, s%32
        assert 32*u1+u2 == s
        assert 0 <= u1 <=31 and 0 <= u2 <=31
    arr = np.arange(1024)
    u1, u2 = decompose_symbols(arr)
    recon = recompose_symbols(u1, u2)
    assert np.array_equal(recon, arr)
    print("R63-01 factorization PASS")
