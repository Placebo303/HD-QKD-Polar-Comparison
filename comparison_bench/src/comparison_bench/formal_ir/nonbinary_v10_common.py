"""V10 shared scientific helpers for ``formal-nonbinary-ldpc-v10-de-peg-fftqspa``
(additive layer; frozen semantics).

Contents:

- sizing: ``qary_entropy_bits_baseq`` (H_q) and ``checks_for`` (m), computed
  from the proposal formula — never hard-coded:
  ``H_q(p) = (h2(p) + p*log2(q-1)) / log2(q)`` and
  ``m(f, p, n) = ceil(f * H_q(p) * n)``;
- edge-perspective degree helpers: ``edge_mean_inverse``,
  ``concentrated_check_distribution`` (own implementation of the V8-60
  harmonic-exact formula), ``reconstructed_rate`` and ``edge_to_node_hist``;
- ``lambda_validate``: fail-closed validator for the frozen K=8 sparse lambda
  representation (unique ascending degrees in ``degree_range``, every weight
  >= ``min_weight``, sum = 1 within 1e-12, finite);
- ``qsc_channel_message`` and single-vector ``entropy_base_q``;
- seed derivation ``v10_seed``: ``int(sha256(f"V10:{tag}")[0:8], 16)`` — the
  V10 prefix rule keeps every derived seed disjoint from all V8 (20260804xx)
  and V9 (20260901xx) seeds by construction;
- ``ProcessTreeRSSWatcher``: a ctypes-only Windows process-tree RSS watcher
  (toolhelp32 snapshot + psapi ``GetProcessMemoryInfo``), an own
  implementation following the accepted V9 pattern — no psutil, no new
  dependency.  Scientific runs run under it with the frozen 3 GiB cap;
- frozen V10-0 q=4 reference-contract constants and the published-Müller q=4
  degree constants (test-reference only; NEVER injected into the initial
  population).

This module imports only the standard library, ``numpy`` and the accepted
field tables (``nonbinary_field.GF2mField``).  It never imports any V8/V9
module and never executes a decoder.
"""
from __future__ import annotations

import ctypes
import hashlib
import math
import os
import threading
from ctypes import wintypes
from numbers import Integral
from typing import Any, Mapping

import numpy as np

from .nonbinary_field import GF2mField

__all__ = [
    "V10_SEED_PREFIX",
    "V10_RSS_CAP_BYTES",
    "V10_0_Q4_TARGET_DET",
    "V10_0_Q4_TOL",
    "V10_0_Q4_RATE",
    "V10_0_Q4_N_SAMPLES",
    "V10_0_Q4_MAX_ITER",
    "V10_0_Q4_P_LO",
    "V10_0_Q4_P_HI",
    "V10_0_Q4_P_TOL",
    "V10_0_Q4_ENTROPY_TOL",
    "V10_0_Q4_STREAK",
    "MULLER_Q4_LAMBDA_PUBLISHED_DEGREES",
    "qary_entropy_bits_baseq",
    "checks_for",
    "edge_mean_inverse",
    "concentrated_check_distribution",
    "reconstructed_rate",
    "edge_to_node_hist",
    "lambda_validate",
    "qsc_channel_message",
    "entropy_base_q",
    "v10_seed",
    "ProcessTreeRSSWatcher",
]

#: V10 seed prefix (frozen): all V10 seeds use 202610xx, provably disjoint
#: from V8 (20260804xx) and V9 (20260901xx).
V10_SEED_PREFIX = "202610"

#: Frozen process-tree RSS cap: 3 GiB.
V10_RSS_CAP_BYTES = 3 * 1024 ** 3

# --------------------------------------------------------------------------- #
# frozen V10-0 q=4 reference-recovery contract (V8-60 verbatim)
# --------------------------------------------------------------------------- #

#: Published Müller q=4 R=0.75 DET (Table 1) — the V10-0 recovery target.
V10_0_Q4_TARGET_DET = 0.069
#: Frozen reproduction tolerance (V8-60 auditable arithmetic): 0.01175 <= 0.012.
V10_0_Q4_TOL = 0.012
#: Target ensemble rate for the V10-0 q=4 recovery.
V10_0_Q4_RATE = 0.75
#: MC-DE node budget (paper's own).
V10_0_Q4_N_SAMPLES = 100000
#: MC-DE iteration budget (paper's own).
V10_0_Q4_MAX_ITER = 150
#: Binary-search probe range for the q=4 recovery.
V10_0_Q4_P_LO = 0.01
V10_0_Q4_P_HI = 0.12
V10_0_Q4_P_TOL = 0.0025
V10_0_Q4_ENTROPY_TOL = 0.01
V10_0_Q4_STREAK = 20

#: Published Müller q=4 R=0.75 lambda keyed by variable DEGREES
#: (exponent + 1).  Test-reference constant ONLY — it must never be injected
#: into the initial DE population (V10-0.2).
MULLER_Q4_LAMBDA_PUBLISHED_DEGREES = {
    2: 0.107, 4: 0.245, 7: 0.192, 10: 0.034, 19: 0.207, 26: 0.161, 28: 0.049,
}


# --------------------------------------------------------------------------- #
# sizing (computed, never hard-coded)
# --------------------------------------------------------------------------- #


def _qint(q: Any) -> int:
    if isinstance(q, bool) or not isinstance(q, Integral) or int(q) < 2 \
            or int(q) & (int(q) - 1) or int(q) > 1024:
        raise ValueError("V10 requires a power-of-two GF(q) with 2 <= q <= 1024")
    return int(q)


def qary_entropy_bits_baseq(q: int, p: float) -> float:
    """Exact ``H_q(p) = (h2(p) + p*log2(q-1)) / log2(q)`` (base-q units).

    Computed from the formula; the frozen informative values are never
    hard-coded.
    """
    q = _qint(q)
    if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(float(p)) \
            or not 0.0 < float(p) < (q - 1.0) / q:
        raise ValueError("q-ary symmetric p is outside the frozen open domain")
    p = float(p)
    h2 = -p * math.log2(p) - (1.0 - p) * math.log2(1.0 - p)
    return (h2 + p * math.log2(q - 1)) / math.log2(q)


def checks_for(f: float, p: float, n: int, q: int = 1024) -> int:
    """``m = ceil(f * H_q(p) * n)`` — the exact check count for a stratum/tier."""
    q = _qint(q)
    if isinstance(f, bool) or not isinstance(f, (int, float)) or not math.isfinite(float(f)) \
            or float(f) <= 0.0:
        raise ValueError("f must be positive and finite")
    if isinstance(n, bool) or not isinstance(n, Integral) or int(n) <= 0:
        raise ValueError("n must be a positive integer")
    return int(math.ceil(float(f) * qary_entropy_bits_baseq(q, float(p)) * int(n)))


# --------------------------------------------------------------------------- #
# edge-perspective degree helpers (harmonic-exact rate algebra)
# --------------------------------------------------------------------------- #


def _validate_edge_hist(hist: Mapping[Any, Any], name: str) -> None:
    if not isinstance(hist, Mapping):
        raise ValueError(f"{name} must be a mapping")
    for degree, value in hist.items():
        if isinstance(degree, bool) or not isinstance(degree, Integral) or int(degree) < 1:
            raise ValueError(f"{name} degrees must be positive integers")
        if isinstance(value, bool) or not isinstance(value, (int, float)) \
                or not math.isfinite(float(value)) or float(value) <= 0.0:
            raise ValueError(f"{name} requires positive finite weights")


def edge_mean_inverse(edge_hist: Mapping[Any, Any]) -> float:
    """``sum_d lambda_d / d`` — the edge-perspective harmonic integral."""
    _validate_edge_hist(edge_hist, "edge_hist")
    total = sum(float(value) / int(degree) for degree, value in edge_hist.items())
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError("edge_hist has invalid integral")
    return float(total)


def concentrated_check_distribution(rate: float,
                                    lambda_edge: Mapping[Any, Any]) -> dict[str, float]:
    """Harmonic-exact two-point concentrated check-degree distribution.

    Own implementation of the V8-60 formula: with
    ``target = (1 - rate) * sum_i lambda_i/i`` and ``dc = 1/target``, the
    unique two-point distribution on the adjacent degrees
    ``{floor(dc), floor(dc)+1}`` that satisfies ``sum_j rho_j/j = target``
    exactly has ``w_lo = (target - 1/d_hi) / (1/d_lo - 1/d_hi)``,
    ``w_hi = 1 - w_lo``; an integer ``dc`` degenerates to the regular single
    check degree.  Returns ``dc_lo``/``dc_hi``/``w_lo``/``w_hi`` plus
    ``dc_mean`` (1/target), ``integral_lambda``, ``integral_rho`` (= target)
    and ``rate_reconstructed`` (exact to float precision).
    """
    if isinstance(rate, bool) or not isinstance(rate, (int, float)) or not math.isfinite(float(rate)):
        raise ValueError("rate must be finite")
    rate = float(rate)
    if (1.0 - rate) <= 0.0:
        raise ValueError("(1 - rate) must be positive")
    integral = edge_mean_inverse(lambda_edge)
    target = (1.0 - rate) * integral
    if not math.isfinite(target) or target <= 0.0:
        raise ValueError("target (1-rate)*integral_lambda must be positive and finite")
    dc = 1.0 / target
    if not math.isfinite(dc) or dc < 2.0:
        raise ValueError("implied mean check degree must be >= 2")
    d_lo = int(math.floor(dc))
    if d_lo < 2:
        raise ValueError("implied mean check degree must be >= 2")
    d_hi = d_lo + 1
    if abs(dc - d_lo) < 1e-12:
        w_lo, w_hi = 1.0, 0.0
    else:
        w_lo = (target - 1.0 / d_hi) / (1.0 / d_lo - 1.0 / d_hi)
        w_hi = 1.0 - w_lo
        if w_lo < 0.0 or w_hi < 0.0:
            raise ValueError("concentrated distribution weights must be non-negative")
    return {"dc_lo": float(d_lo), "dc_hi": float(d_hi), "w_lo": w_lo, "w_hi": w_hi,
            "dc_mean": dc, "integral_lambda": integral, "integral_rho": target,
            "rate_reconstructed": 1.0 - target / integral}


def reconstructed_rate(lambda_edge: Mapping[Any, Any], rho_edge: Mapping[Any, Any]) -> float:
    """``R = 1 - (sum_j rho_j/j) / (sum_i lambda_i/i)`` (edge perspective)."""
    integral_lambda = edge_mean_inverse(lambda_edge)
    integral_rho = edge_mean_inverse(rho_edge)
    return 1.0 - integral_rho / integral_lambda


def edge_to_node_hist(edge_hist: Mapping[Any, Any]) -> dict[int, float]:
    """Edge-perspective ``lambda_d`` -> node-perspective
    ``L_d = (lambda_d/d) / (sum_j lambda_j/j)``.

    Fail-closed: rejects non-positive / non-finite weights and inputs whose
    weights do not sum to 1 (within 1e-9) — the mechanical conversion must
    never be bypassed with a non-normalized edge histogram.
    """
    _validate_edge_hist(edge_hist, "edge_hist")
    total_weight = sum(float(value) for value in edge_hist.values())
    if not math.isfinite(total_weight) or abs(total_weight - 1.0) > 1e-9:
        raise ValueError("edge_hist weights must sum to 1 within 1e-9")
    integral = edge_mean_inverse(edge_hist)
    return {int(degree): (float(value) / int(degree)) / integral
            for degree, value in edge_hist.items()}


def lambda_validate(lambda_edge: Mapping[Any, Any], K: int = 8,
                    degree_range: tuple[int, int] = (2, 40),
                    min_weight: float = 0.01) -> dict[int, float]:
    """Fail-closed validator for the frozen K=8 sparse lambda representation.

    Requires exactly ``K`` entries with unique degrees in
    ``[degree_range[0], degree_range[1]]`` sorted ascending, every weight
    finite and ``>= min_weight``, and ``sum(lambda) == 1`` within 1e-12.
    Returns the canonical ``{degree: weight}`` dict (int keys) on success and
    raises ``ValueError`` on any violation.
    """
    if isinstance(K, bool) or not isinstance(K, Integral) or int(K) < 1:
        raise ValueError("K must be a positive integer")
    K = int(K)
    if not isinstance(degree_range, (tuple, list)) or len(degree_range) != 2:
        raise ValueError("degree_range must be a (lo, hi) pair")
    d_lo, d_hi = int(degree_range[0]), int(degree_range[1])
    if d_lo < 2 or d_hi < d_lo:
        raise ValueError("invalid degree_range")
    if isinstance(min_weight, bool) or not isinstance(min_weight, (int, float)) \
            or not math.isfinite(float(min_weight)) or float(min_weight) <= 0.0:
        raise ValueError("min_weight must be positive and finite")
    min_weight = float(min_weight)
    if not isinstance(lambda_edge, Mapping):
        raise ValueError("lambda_edge must be a mapping")
    if len(lambda_edge) != K:
        raise ValueError(f"lambda_edge must have exactly K={K} entries, got {len(lambda_edge)}")
    degrees: list[int] = []
    weights: list[float] = []
    for key, value in lambda_edge.items():
        if isinstance(key, bool) or not isinstance(key, Integral):
            raise ValueError("lambda_edge degrees must be integers")
        degree = int(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) \
                or not math.isfinite(float(value)):
            raise ValueError("lambda_edge weights must be finite")
        weight = float(value)
        if weight < 0.0:
            raise ValueError("lambda_edge weights must be non-negative")
        if not d_lo <= degree <= d_hi:
            raise ValueError(f"lambda_edge degree {degree} outside [{d_lo}, {d_hi}]")
        degrees.append(degree)
        weights.append(weight)
    if len(set(degrees)) != K:
        raise ValueError("lambda_edge degrees must be unique")
    order = sorted(range(K), key=lambda index: degrees[index])
    degrees = [degrees[index] for index in order]
    weights = [weights[index] for index in order]
    for index, weight in enumerate(weights):
        if weight < min_weight:
            raise ValueError(
                f"lambda_edge weight {weight} at degree {degrees[index]} below min_weight {min_weight}")
    total = sum(weights)
    if not math.isfinite(total) or abs(total - 1.0) > 1e-12:
        raise ValueError(f"lambda_edge weights must sum to 1 within 1e-12, got {total}")
    return {degree: weight for degree, weight in zip(degrees, weights)}


# --------------------------------------------------------------------------- #
# channel and entropy helpers
# --------------------------------------------------------------------------- #


def qsc_channel_message(q: int, p: float) -> np.ndarray:
    """QSC channel message for received symbol 0: ``[1-p, p/(q-1), ...]``."""
    q = _qint(q)
    if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(float(p)) \
            or not 0.0 < float(p) < (q - 1.0) / q:
        raise ValueError("q-ary symmetric p is outside the frozen open domain")
    p = float(p)
    vector = np.full(q, p / (q - 1.0), dtype=np.float64)
    vector[0] = 1.0 - p
    return vector


def entropy_base_q(probs: Any, q: int) -> float:
    """Shannon entropy of a single length-q probability vector in base q:
    ``-sum p*log_q(p)`` (0 for a degenerate deterministic mass)."""
    q = _qint(q)
    vector = np.asarray(probs, dtype=np.float64)
    if vector.shape != (q,):
        raise ValueError(f"probs must be a length-{q} vector")
    if not np.all(np.isfinite(vector)):
        raise ValueError("probs must be finite")
    if np.any(vector < 0.0):
        raise ValueError("probs must be non-negative")
    total = float(vector.sum())
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError("probs must have positive total mass")
    logq = math.log(q)
    terms = np.zeros_like(vector)
    nonzero = vector > 0.0
    terms[nonzero] = -vector[nonzero] * np.log(vector[nonzero]) / logq
    return float(terms.sum())


# --------------------------------------------------------------------------- #
# seed derivation (frozen V10 rule)
# --------------------------------------------------------------------------- #


def v10_seed(tag: str) -> int:
    """``int(sha256(f"V10:{tag}")[0:8], 16)`` — frozen derived-seed rule.

    Used to derive frame/error-pattern seeds and deterministic internal RNG
    streams (DE init/mutation/crossover) from the frozen numeric V10 roots.
    """
    if not isinstance(tag, str):
        raise ValueError("tag must be a string")
    digest = hashlib.sha256(f"V10:{tag}".encode("utf-8")).hexdigest()
    return int(digest[0:8], 16)


# --------------------------------------------------------------------------- #
# process-tree RSS watcher (ctypes only, Windows toolhelp32)
# --------------------------------------------------------------------------- #

_TH32CS_SNAPPROCESS = 0x00000002
_PROCESS_QUERY_INFORMATION = 0x0400
_PROCESS_VM_READ = 0x0010


class _PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", ctypes.c_wchar * 260),
    ]


class _PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


def _load_win_api():
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
    except (AttributeError, OSError) as exc:  # pragma: no cover - non-Windows
        raise OSError("ProcessTreeRSSWatcher requires Windows (toolhelp32)") from exc
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel32.Process32FirstW.restype = wintypes.BOOL
    kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(_PROCESSENTRY32W)]
    kernel32.Process32NextW.restype = wintypes.BOOL
    kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(_PROCESSENTRY32W)]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    psapi.GetProcessMemoryInfo.argtypes = [
        wintypes.HANDLE, ctypes.POINTER(_PROCESS_MEMORY_COUNTERS), wintypes.DWORD]
    return kernel32, psapi


class ProcessTreeRSSWatcher:
    """Samples the peak process-tree RSS (parent + descendants) in bytes.

    A background thread snapshots the process list via toolhelp32
    (``CreateToolhelp32Snapshot``/``Process32FirstW``), walks the descendant
    tree of the owning process, and sums each process's WorkingSetSize
    (``OpenProcess`` + ``GetProcessMemoryInfo`` from psapi).  The peak is
    recorded; ``cap_bytes`` triggers ``cap_exceeded`` (scientific runs are
    capped at the frozen 3 GiB).  stdlib ctypes only — no psutil, no
    installation.
    """

    def __init__(self, interval: float = 10.0, cap_bytes: int | None = None):
        if isinstance(interval, bool) or not isinstance(interval, (int, float)) \
                or not math.isfinite(float(interval)) or float(interval) <= 0.0:
            raise ValueError("interval must be positive and finite")
        if cap_bytes is not None and (isinstance(cap_bytes, bool)
                                      or not isinstance(cap_bytes, Integral)
                                      or int(cap_bytes) < 0):
            raise ValueError("cap_bytes must be a non-negative integer or None")
        self._interval = float(interval)
        self._cap_bytes = None if cap_bytes is None else int(cap_bytes)
        self._peak = 0
        self._samples: list[int] = []
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def start(self) -> "ProcessTreeRSSWatcher":
        if self._thread is not None and self._thread.is_alive():
            return self
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="v10-rss-watcher",
                                        daemon=True)
        self._thread.start()
        return self

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=max(2.0, 2.0 * self._interval))
            self._thread = None

    @property
    def peak_rss_bytes(self) -> int:
        with self._lock:
            return int(self._peak)

    @property
    def samples(self) -> list[int]:
        with self._lock:
            return list(self._samples)

    @property
    def cap_exceeded(self) -> bool:
        with self._lock:
            return self._cap_bytes is not None and self._peak > self._cap_bytes

    def __enter__(self) -> "ProcessTreeRSSWatcher":
        return self.start()

    def __exit__(self, *exc_info: Any) -> None:
        self.stop()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                total = self._snapshot_total()
            except OSError:
                total = None
            if total is not None:
                with self._lock:
                    self._samples.append(total)
                    self._peak = max(self._peak, total)
            self._stop_event.wait(self._interval)

    def _snapshot_total(self) -> int:
        kernel32, psapi = _load_win_api()
        root = os.getpid()
        snapshot = kernel32.CreateToolhelp32Snapshot(_TH32CS_SNAPPROCESS, 0)
        if not snapshot or snapshot == wintypes.HANDLE(-1).value:
            raise OSError("CreateToolhelp32Snapshot failed")
        try:
            entry = _PROCESSENTRY32W()
            entry.dwSize = ctypes.sizeof(_PROCESSENTRY32W)
            children: dict[int, list[int]] = {}
            pids: list[int] = []
            if kernel32.Process32FirstW(snapshot, ctypes.byref(entry)):
                while True:
                    pid = int(entry.th32ProcessID)
                    parent = int(entry.th32ParentProcessID)
                    pids.append(pid)
                    children.setdefault(parent, []).append(pid)
                    if not kernel32.Process32NextW(snapshot, ctypes.byref(entry)):
                        break
            else:
                raise OSError("Process32FirstW failed")
            tree = self._descendants(root, children) | {root}
            total = 0
            for pid in tree:
                if pid not in pids:
                    continue
                handle = kernel32.OpenProcess(_PROCESS_QUERY_INFORMATION | _PROCESS_VM_READ,
                                              False, pid)
                if not handle:
                    continue  # process exited mid-snapshot; skip (transient)
                try:
                    counters = _PROCESS_MEMORY_COUNTERS()
                    counters.cb = ctypes.sizeof(_PROCESS_MEMORY_COUNTERS)
                    if psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters),
                                                  ctypes.sizeof(_PROCESS_MEMORY_COUNTERS)):
                        total += int(counters.WorkingSetSize)
                finally:
                    kernel32.CloseHandle(handle)
            return total
        finally:
            kernel32.CloseHandle(snapshot)

    @staticmethod
    def _descendants(root: int, children: dict[int, list[int]]) -> set[int]:
        out: set[int] = set()
        frontier = list(children.get(root, ()))
        while frontier:
            pid = frontier.pop()
            if pid in out or pid == root:
                continue
            out.add(pid)
            frontier.extend(children.get(pid, ()))
        return out
