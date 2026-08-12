"""V9 shared scientific helpers for the GF(1024) long-block IR change
(``formal-nonbinary-ldpc-v9-gf1024-long-ir``, additive layer).

Contents (frozen):

- sizing: ``qary_entropy_bits_baseq`` (H_q) and ``checks_for`` (m) computed
  from the proposal formula — never hard-coded:
  ``H_q(p) = [h2(p) + p*log2(q-1)] / log2(q)`` and
  ``m(f, p, n) = ceil(f * H_q(p) * n)``;
- harmonic-exact edge-view check distribution ``concentrated_check_distribution``
  — an own implementation of the V8-60 formula
  ``target = (1-R) * sum_i lambda_i/i``, ``dc = 1/target``,
  ``w_lo = (target - 1/d_hi) / (1/d_lo - 1/d_hi)`` on the adjacent degrees
  ``{floor(dc), floor(dc)+1}``; an integer ``dc`` degenerates to the regular
  single check degree.  It must agree with the V8 module's
  ``concentrated_check_distribution`` within 1e-12 (tests); V8 is a test-only
  reference and is never imported here;
- ``reconstructed_rate`` and ``edge_mean_inverse`` (the edge-view harmonic
  integral used by both rho construction and rate reconstruction);
- status vocabulary: ``FORMAL_STATUSES`` imported from the accepted
  ``shared`` verifier (import-only reuse) plus the V9 resource-abort name;
- seed derivation helpers for constituent superframes (frozen rule):
  ``constituent_seed(P, f, k) = int(sha256(f"{P}:frame{f}:const{k}")[0:8], 16)``
  and ``error_pattern_seed(P, f, k)`` with the extra ``:err`` marker; P is the
  stage prefix (V9A optimization/validation prefix ``20260901`` etc.); cross-
  stage disjointness follows from the disjoint numeric prefixes;
- ``ProcessTreeRSSWatcher``: a ctypes-only Windows process-tree RSS watcher
  (toolhelp32 snapshot; sums the WorkingSetSize of the parent process and all
  descendants via OpenProcess/GetProcessMemoryInfo; samples every ``interval``
  seconds; records the peak).  No psutil, no installation, no new dependency.
  Scientific runs must run under it with the frozen 3 GiB cap.

This module imports only the standard library plus ``shared`` (the accepted
verifier helper).  It never reads frame data and never executes a decoder.
"""
from __future__ import annotations

import ctypes
import hashlib
import math
import os
import threading
import time
from ctypes import wintypes
from numbers import Integral
from typing import Any, Mapping

from .shared import FORMAL_STATUSES

__all__ = [
    "FORMAL_STATUSES",
    "V9_STATUS_RESOURCE_ABORT",
    "qary_entropy_bits_baseq",
    "checks_for",
    "edge_mean_inverse",
    "concentrated_check_distribution",
    "reconstructed_rate",
    "constituent_seed",
    "error_pattern_seed",
    "ProcessTreeRSSWatcher",
    "V9A_OPTIMIZATION_SEEDS",
    "V9A_VALIDATION_SEEDS",
    "V9A_SEARCH_SPECS",
    "V9A_CANDIDATES",
    "V9A_BUDGETS",
    "V9A_PROBE_RANGES",
    "V9A_GATES",
]

#: Resource-abort status from the frozen vocabulary (hard RSS breach or hard
#: timeout => ``aborted_resource_limit`` with a documented reason).
V9_STATUS_RESOURCE_ABORT = "aborted_resource_limit"

#: Frozen V9A seed constants (V9-00.2 / V9-20.1).  V9 uses the 202609xx prefix,
#: disjoint from ALL prior V1-V8 seeds (V6 20260802xx, V7 20260804xx /
#: 20260805xxxx, V8 20260804xx).  Search order is frozen as listed.
V9A_OPTIMIZATION_SEEDS = {
    "S1": 2026090101,  # p=.20 robust f=1.15
    "S2": 2026090102,  # p=.20 target f=1.08
    "S3": 2026090103,  # p=.30 robust f=1.15
    "S4": 2026090104,  # p=.30 target f=1.08
}
#: The same three disjoint validation seeds are used for all four searches.
V9A_VALIDATION_SEEDS = (2026090111, 2026090112, 2026090113)

#: Frozen search specs (id -> (p, f, tier label, probe range, conservative
#: gate)); gate reconstruction is frozen in the V9A plan JSON.
V9A_SEARCH_SPECS = {
    "S1": {"stratum_p": 0.20, "tier_f": 1.15, "tier_label": "robust",
           "probe_range": (0.15, 0.26), "gate_conservative": 0.22},
    "S2": {"stratum_p": 0.20, "tier_f": 1.08, "tier_label": "target",
           "probe_range": (0.15, 0.26), "gate_conservative": 0.215},
    "S3": {"stratum_p": 0.30, "tier_f": 1.15, "tier_label": "robust",
           "probe_range": (0.24, 0.36), "gate_conservative": 0.32},
    "S4": {"stratum_p": 0.30, "tier_f": 1.08, "tier_label": "target",
           "probe_range": (0.24, 0.36), "gate_conservative": 0.32},
}

#: Frozen candidate edge-view lambda population (V9-20.1), degrees <= 40,
#: applied to all four searches, canonical order C1..C8 (tie-break order).
V9A_CANDIDATES = {
    "C1": {2: 0.35, 3: 0.30, 20: 0.35},
    "C2": {2: 0.40, 3: 0.25, 30: 0.35},
    "C3": {2: 0.45, 3: 0.20, 40: 0.35},
    "C4": {2: 0.30, 3: 0.35, 20: 0.35},
    "C5": {3: 1.0},
    "C6": {2: 0.25, 3: 0.40, 40: 0.35},
    "C7": {2: 0.50, 3: 0.15, 40: 0.35},
    "C8": {2: 0.20, 3: 0.45, 30: 0.35},
}

#: Frozen MC-DE budget (V9-20.1).
V9A_BUDGETS = {
    "n_samples": 2000,
    "max_iter": 150,
    "entropy_tol": 0.01,
    "streak": 20,
    "floor": 1e-300,
    "p_tol": 0.002,
}

#: Frozen probe ranges per stratum (V9-20.1): p=.20 -> [0.15, 0.26],
#: p=.30 -> [0.24, 0.36].
V9A_PROBE_RANGES = {0.20: (0.15, 0.26), 0.30: (0.24, 0.36)}

#: Frozen conservative gates (V9-20.1): robust >= .22/.32 for p=.20/.30;
#: target >= .215/.32 (.215 stays below the p=.20 f=1.08 capacity threshold
#: ~.21827).  Robust failure => STOP before codebooks; target failure =>
#: robust-only with ``efficiency_target_not_met``.
V9A_GATES = {
    "robust": {0.20: 0.22, 0.30: 0.32},
    "target": {0.20: 0.215, 0.30: 0.32},
}

#: Frozen process-tree RSS cap: 3 GiB.
V9_RSS_CAP_BYTES = 3 * 1024 ** 3


# --------------------------------------------------------------------------- #
# sizing (computed, never hard-coded)
# --------------------------------------------------------------------------- #


def _qint(q: Any) -> int:
    if isinstance(q, bool) or not isinstance(q, Integral) or int(q) < 2 or int(q) & (int(q) - 1) \
            or int(q) > 1024:
        raise ValueError("V9 requires a power-of-two GF(q) with 2 <= q <= 1024")
    return int(q)


def qary_entropy_bits_baseq(q: int, p: float) -> float:
    """Exact ``H_q(p) = (h2(p) + p*log2(q-1)) / log2(q)`` (base-q units).

    Computed from the formula; the frozen informative values (e.g. 0.2721646
    for p=.20) are 7-decimal rounded and never hard-coded.
    """
    q = _qint(q)
    if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(float(p)) \
            or not 0.0 < float(p) < (q - 1.0) / q:
        raise ValueError("q-ary symmetric p is outside the frozen open domain")
    p = float(p)
    h2 = -p * math.log2(p) - (1.0 - p) * math.log2(1.0 - p)
    return (h2 + p * math.log2(q - 1)) / math.log2(q)


def checks_for(f: float, p: float, n: int, q: int = 1024) -> int:
    """``m = ceil(f * H_q(p) * n)`` — the exact check count for a stratum/tier.

    Informative expected values for tests (rounded, never hard-coded here):
    p=.20 f=1.15 m/n=0.3129893; p=.20 f=1.08 m/n=0.2939378;
    p=.30 f=1.15 m/n=0.4462998; p=.30 f=1.08 m/n=0.4191337.
    """
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
    ``{floor(dc), floor(dc)+1}`` that satisfies
    ``sum_j rho_j/j = target`` exactly has
    ``w_lo = (target - 1/d_hi) / (1/d_lo - 1/d_hi)``, ``w_hi = 1 - w_lo``;
    an integer ``dc`` degenerates to the regular single check degree.  The
    returned dict carries ``dc_lo``/``dc_hi``/``w_lo``/``w_hi`` as floats plus
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


# --------------------------------------------------------------------------- #
# seed derivation (frozen constituent rule)
# --------------------------------------------------------------------------- #


def _derived_seed(tag: str) -> int:
    digest = hashlib.sha256(tag.encode("utf-8")).hexdigest()
    return int(digest[0:8], 16)


def constituent_seed(prefix: str, frame: int, const: int) -> int:
    """``int(sha256(f"{P}:frame{f}:const{k}")[0:8], 16)`` — frozen rule."""
    if isinstance(frame, bool) or not isinstance(frame, Integral) or int(frame) < 0:
        raise ValueError("frame must be a non-negative integer")
    if isinstance(const, bool) or not isinstance(const, Integral) or int(const) < 0:
        raise ValueError("const must be a non-negative integer")
    return _derived_seed(f"{prefix}:frame{int(frame)}:const{int(const)}")


def error_pattern_seed(prefix: str, frame: int, const: int) -> int:
    """QSC error-pattern seed: the constituent seed tag plus ``:err``."""
    if isinstance(frame, bool) or not isinstance(frame, Integral) or int(frame) < 0:
        raise ValueError("frame must be a non-negative integer")
    if isinstance(const, bool) or not isinstance(const, Integral) or int(const) < 0:
        raise ValueError("const must be a non-negative integer")
    return _derived_seed(f"{prefix}:frame{int(frame)}:const{int(const)}:err")


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
    kernel32.GetExitCodeProcess.restype = wintypes.BOOL
    kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
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

    # -- public API -------------------------------------------------------- #

    def start(self) -> "ProcessTreeRSSWatcher":
        if self._thread is not None and self._thread.is_alive():
            return self
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="v9-rss-watcher",
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

    # -- sampling ---------------------------------------------------------- #

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
                    continue  # process exited mid-snapshot; skip (fail open for a
                              # transient missing child, still bounded by the cap)
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
