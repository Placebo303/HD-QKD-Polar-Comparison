#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Any

import numpy as np
from numba import njit


def _as_int(v: Any) -> int:
    return int(float(v))


def _as_float(v: Any) -> float:
    return float(v)


def _h2(p: float) -> float:
    p = float(min(1.0 - 1e-12, max(1e-12, p)))
    return -p * math.log2(p) - (1.0 - p) * math.log2(1.0 - p)


def _polar_weight_order(n: int, beta: float = 2 ** 0.25) -> np.ndarray:
    m = int(round(math.log2(n)))
    if 2**m != n:
        raise ValueError("N must be power of 2")
    ws: list[tuple[float, int]] = []
    for i in range(n):
        w = 0.0
        for j in range(m):
            if ((i >> j) & 1) == 1:
                w += beta**j
        ws.append((w, i))
    ws.sort(key=lambda x: x[0])  # smaller PW -> more reliable
    return np.asarray([x[1] for x in ws], dtype=np.int64)


@njit(cache=True)
def _fill_left_alpha(src: np.ndarray, src_len: int, dst: np.ndarray) -> None:
    half = src_len // 2
    for i in range(half):
        l = src[i]
        r = src[i + half]
        sl = 1.0 if l >= 0.0 else -1.0
        sr = 1.0 if r >= 0.0 else -1.0
        al = l if l >= 0.0 else -l
        ar = r if r >= 0.0 else -r
        dst[i] = sl * sr * (al if al <= ar else ar)


@njit(cache=True)
def _fill_right_alpha(src: np.ndarray, src_len: int, left_bits: np.ndarray, dst: np.ndarray) -> None:
    half = src_len // 2
    for i in range(half):
        # g-node: r - (2*u-1)*l
        dst[i] = src[i + half] - (2.0 * left_bits[i] - 1.0) * src[i]


@njit(cache=True)
def _encoding_step(level: int, n: int, source: np.ndarray, result: np.ndarray) -> None:
    pairs_per_group = 1 << (n - level - 1)
    step = pairs_per_group
    groups = 1 << level
    for g in range(groups):
        start = 2 * g * step
        for p in range(pairs_per_group):
            result[p + start] = source[p + start] ^ source[p + start + step]
            result[p + start + step] = source[p + start + step]


@njit(cache=True)
def polar_encode_non_systematic(u: np.ndarray, n: int) -> np.ndarray:
    x = u.copy()
    for level in range(n - 1, -1, -1):
        _encoding_step(level, n, x, x)
    return x


@njit(cache=True)
def polar_sc_decode(llr: np.ndarray, mask: np.ndarray, n: int) -> np.ndarray:
    frozen_values = np.zeros(llr.size, dtype=np.int8)
    return polar_sc_decode_with_frozen(llr, mask, frozen_values, n)


@njit(cache=True)
def polar_sc_decode_with_frozen(llr: np.ndarray, mask: np.ndarray, frozen_values: np.ndarray, n: int) -> np.ndarray:
    # mask[pos] == 1 => information bit, else frozen bit from frozen_values[pos]
    N = llr.size
    inter_llr = np.zeros((n + 1, N), dtype=np.float64)
    inter_bits = np.zeros((n + 1, N), dtype=np.int8)
    inter_llr[0, :] = llr

    current_state = np.zeros(n, dtype=np.int8)
    previous_state = np.ones(n, dtype=np.int8)

    for pos in range(N):
        # Binary state of position index (MSB->LSB)
        for b in range(n):
            shift = n - 1 - b
            current_state[b] = np.int8((pos >> shift) & 1)

        # Update intermediate alphas only on changed path segments
        for i in range(1, n + 1):
            if current_state[i - 1] == previous_state[i - 1]:
                continue
            src_len = N >> (i - 1)
            dst_len = N >> i
            src = inter_llr[i - 1]
            dst = inter_llr[i]
            if current_state[i - 1] == 0:
                _fill_left_alpha(src, src_len, dst)
            else:
                start = pos - dst_len
                left_bits = inter_bits[i, start:pos].astype(np.float64)
                _fill_right_alpha(src, src_len, left_bits, dst)

        # Leaf decision
        decision = 1 if inter_llr[n, 0] < 0.0 else 0
        if mask[pos] == 0:
            decision = int(frozen_values[pos] & 1)
        inter_bits[n, pos] = np.int8(decision)

        # Propagate partial sums upward
        for level in range(n - 1, -1, -1):
            _encoding_step(level, n, inter_bits[level + 1], inter_bits[level])

        for b in range(n):
            previous_state[b] = current_state[b]

    return inter_bits[n]


@njit(cache=True)
def simulate_layer_fer(
    ber: float,
    n: int,
    k: int,
    info_idx: np.ndarray,
    mask: np.ndarray,
    n_frames: int,
    llr_clip: float,
    n_log: int,
) -> float:
    if k <= 0:
        return 1.0

    p = ber
    if p < 1e-6:
        p = 1e-6
    if p > 1.0 - 1e-6:
        p = 1.0 - 1e-6
    lam = math.log((1.0 - p) / p)
    frame_err = 0

    for _ in range(n_frames):
        u = np.zeros(n, dtype=np.int8)
        for t in range(k):
            u[info_idx[t]] = np.int8(np.random.randint(0, 2))

        x = polar_encode_non_systematic(u, n_log)

        llr = np.empty(n, dtype=np.float64)
        for i in range(n):
            flip = 1 if np.random.random() < p else 0
            y = x[i] ^ np.int8(flip)
            v = lam if y == 0 else -lam
            if v > llr_clip:
                v = llr_clip
            elif v < -llr_clip:
                v = -llr_clip
            llr[i] = v

        u_hat = polar_sc_decode(llr, mask, n_log)

        bad = 0
        for t in range(k):
            idx = info_idx[t]
            if u_hat[idx] != u[idx]:
                bad = 1
                break
        frame_err += bad

    return float(frame_err) / float(max(1, n_frames))


def _load_point_sidecar(repo_root: Path, d: int, bw: int) -> tuple[np.ndarray, np.ndarray, float, str]:
    table = repo_root / "results" / "grid_mixed_full_table.csv"
    with table.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    cand: list[dict[str, str]] = []
    for r in rows:
        try:
            if _as_int(r.get("dimension", -1)) == int(d) and _as_int(r.get("bin_width_ps", -1)) == int(bw):
                cand.append(r)
        except Exception:
            continue
    if not cand:
        raise RuntimeError(f"point not found in grid_mixed_full_table.csv: d={d}, bw={bw}")
    cand.sort(
        key=lambda x: (
            0 if str(x.get("status", "")).strip() == "OK" else 1,
            float(x.get("sidecar_map_ser", "1e9") or "1e9"),
        )
    )
    row = cand[0]
    out_root = Path(str(row.get("out_root", "")))
    if not out_root.is_absolute():
        out_root = (repo_root / out_root).resolve()
    sidecar = out_root / "sidecars" / f"d{d}_bw{bw}" / "blk0"
    if not sidecar.exists():
        raise RuntimeError(f"sidecar path not found: {sidecar}")
    a_eff = np.load(sidecar / "a_eff.npy")
    b_eff = np.load(sidecar / "b_eff.npy")
    map_ser = _as_float(row.get("sidecar_map_ser", "nan"))
    return a_eff, b_eff, map_ser, str(sidecar)


def _self_check(n: int, n_log: int) -> None:
    # Noiseless sanity: SC must recover random information sets.
    rng = np.random.default_rng(1234)
    trials = 5
    for _ in range(trials):
        k = max(8, n // 16)
        info_idx = np.sort(rng.choice(np.arange(n), size=k, replace=False)).astype(np.int64)
        mask = np.zeros(n, dtype=np.int8)
        mask[info_idx] = 1
        u = np.zeros(n, dtype=np.int8)
        u[info_idx] = rng.integers(0, 2, size=k, dtype=np.int8)
        x = polar_encode_non_systematic(u, n_log)
        llr = np.where(x == 0, 40.0, -40.0).astype(np.float64)
        u_hat = polar_sc_decode(llr, mask, n_log)
        if not np.all(u_hat[info_idx] == u[info_idx]):
            raise RuntimeError("Polar SC self-check failed in noiseless test")


def main() -> int:
    ap = argparse.ArgumentParser(description="Numba-accelerated real Polar-SC + MLC rescue probe")
    ap.add_argument("--dimension", type=int, default=1024)
    ap.add_argument("--bin-width-ps", type=int, default=30)
    ap.add_argument("--N", type=int, default=4096, choices=[1024, 2048, 4096])
    ap.add_argument("--frames", type=int, default=100)
    ap.add_argument("--ber-drop-thresh", type=float, default=0.25)
    ap.add_argument("--cap-drop-thresh", type=float, default=0.15)
    ap.add_argument("--safety-margin", type=float, default=0.18)
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    d = int(args.dimension)
    bw = int(args.bin_width_ps)
    n = int(args.N)
    n_log = int(round(math.log2(n)))
    if 2**n_log != n:
        raise SystemExit(f"N must be power-of-two, got {n}")
    bits = int(round(math.log2(d)))
    if 2**bits != d:
        raise SystemExit(f"dimension must be power-of-two, got {d}")

    # JIT warm-up + correctness sanity
    _self_check(n=n, n_log=n_log)

    a_eff, b_eff, map_ser, sidecar = _load_point_sidecar(repo_root=repo_root, d=d, bw=bw)
    n_sym = int(min(a_eff.size, b_eff.size))
    a = np.asarray(a_eff[:n_sym], dtype=np.int64)
    b = np.asarray(b_eff[:n_sym], dtype=np.int64)

    # Under this encoder/decoder index convention, higher PW ranks are more reliable.
    order = _polar_weight_order(n)[::-1]
    n_frames = int(args.frames)

    rows: list[dict[str, Any]] = []
    pie_sum = 0.0
    print(f"[POLAR_RESCUE] point=d{d}, bw={bw}, map_ser={map_ser:.6f}, sidecar={sidecar}")
    for layer_idx in range(bits):
        shift = bits - 1 - layer_idx
        abit = (a >> shift) & 1
        bbit = (b >> shift) & 1
        ber = float(np.mean(abit != bbit))
        cap = float(1.0 - _h2(ber))

        discard = (ber > float(args.ber_drop_thresh)) or (cap < float(args.cap_drop_thresh))
        if discard:
            k = 0
            rate = 0.0
            fer = 1.0
            success = 0
        else:
            rate = max(0.0, min(0.95, cap - float(args.safety_margin)))
            k = int(math.floor(rate * n))
            if k < 8:
                k = 0
                rate = 0.0
                fer = 1.0
                success = 0
            else:
                info_idx = np.asarray(order[:k], dtype=np.int64)
                mask = np.zeros(n, dtype=np.int8)
                mask[info_idx] = 1
                fer = float(simulate_layer_fer(ber, n, k, info_idx, mask, n_frames, 20.0, n_log))
                success = 1 if fer < 0.05 else 0
                if success:
                    pie_sum += float(k) / float(n)

        rows.append(
            {
                "dimension": d,
                "bin_width_ps": bw,
                "layer_idx": layer_idx,
                "layer_ber": ber,
                "capacity": cap,
                "K": int(k),
                "N": n,
                "rate": float(rate),
                "FER": float(fer),
                "rescue_success": int(success),
            }
        )

    pie_hard = float(pie_sum / float(bits))

    out_csv = repo_root / "results" / f"real_polar_sc_rescue_d{d}_bw{bw}.csv"
    cols = ["dimension", "bin_width_ps", "layer_idx", "layer_ber", "capacity", "K", "N", "rate", "FER", "rescue_success"]
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in cols})

    print("[POLAR_RESCUE] Per-layer results:")
    for r in rows:
        print(
            f"  layer={r['layer_idx']:2d} "
            f"BER={r['layer_ber']:.6f} "
            f"R={r['rate']:.4f} (K/N={r['K']}/{r['N']}) "
            f"FER={r['FER']:.4f} "
            f"success={r['rescue_success']}"
        )
    print(f"[POLAR_RESCUE] HARD_PIE={pie_hard:.6f}")
    print(f"[POLAR_RESCUE] OUT={out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
