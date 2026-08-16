"""Minimal ctypes wrapper for the V19 CA-SCL decoder (list size 32).

This wrapper loads a separate experimental DLL compiled from
``v19_ca_scl.cpp`` (a copy of the frozen CA-SCL source with ``kListSize=32``).
It does not modify the frozen ``src/reconciliation`` baseline.
"""
from __future__ import annotations

import ctypes
import os
import shutil
import sys
from pathlib import Path

import numpy as np


class V19CA_SCLDecoder:
    def __init__(self, repo_root: str | Path | None = None, lib_stem: str = "v19_ca_scl") -> None:
        root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[4]
        self._lib_path = root / "comparison_bench" / "src" / "comparison_bench" / "formal_ir" / f"{lib_stem}.dll"
        if not self._lib_path.exists():
            raise FileNotFoundError(f"V19 CA-SCL DLL not found: {self._lib_path}")
        self._add_dll_dirs()
        self._lib = ctypes.CDLL(str(self._lib_path))
        self._decode = self._lib.decode_ca_scl_batch
        self._decode.argtypes = [
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.POINTER(ctypes.c_float),
            ctypes.POINTER(ctypes.c_uint8),
        ]
        self._decode.restype = None

    def _add_dll_dirs(self) -> None:
        if os.name != "nt":
            return
        candidates = [self._lib_path.parent, Path(sys.executable).parent]
        for name in ("libstdc++-6.dll", "libgcc_s_seh-1.dll", "libwinpthread-1.dll"):
            p = shutil.which(name)
            if p:
                candidates.append(Path(p).parent)
        for p in candidates:
            try:
                os.add_dll_directory(str(p.resolve()))
            except Exception:
                pass

    def decode_batch(self, n: int, k: int, frames: int, mask: np.ndarray, llrs: np.ndarray) -> np.ndarray:
        mask_u8 = np.ascontiguousarray(mask, dtype=np.uint8).reshape(-1)
        if mask_u8.size != n or int(mask_u8.sum()) != k:
            raise ValueError("mask size/popcount mismatch")
        llr_f32 = np.ascontiguousarray(llrs, dtype=np.float32).reshape(frames, n)
        out = np.empty((frames, k), dtype=np.uint8)
        self._decode(
            int(n), int(k), int(frames),
            mask_u8.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
            llr_f32.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            out.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
        )
        return out
