#!/usr/bin/env python3
from __future__ import annotations

import ctypes
import os
import shutil
import sys
from pathlib import Path
from typing import Any

import numpy as np


class PolarSCLDecoder:
    """Thin ctypes wrapper for ordinary SCL and legacy CA-SCL decoders."""

    def __init__(
        self,
        repo_root: Path | str | None = None,
        force_rebuild: bool = False,
        lib_stem: str = "polar_scl",
    ) -> None:
        self._repo_root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[2]
        self._cpp_main = (self._repo_root / "src" / "reconciliation" / "cpp_polar" / "main.cpp").resolve()
        self._lib_stem = str(lib_stem)
        self._lib_path = self._resolve_lib_path()
        self._dll_handles: list[Any] = []
        self._lib: ctypes.CDLL | None = None
        self._decode = None
        self._decode_frozen = None
        self._decode_frozen_plain = None

        self._build_if_needed(force=force_rebuild)
        self._configure_windows_dll_dirs(self._lib_path.parent)
        self._load()

    @property
    def lib_path(self) -> Path:
        return self._lib_path

    def _resolve_lib_path(self) -> Path:
        ext = ".dll" if os.name == "nt" else ".so"
        return (self._repo_root / "src" / "reconciliation" / "cpp_polar" / f"{self._lib_stem}{ext}").resolve()

    def _build_if_needed(self, force: bool = False) -> None:
        self._lib_path.parent.mkdir(parents=True, exist_ok=True)
        need = (
            force
            or (not self._lib_path.exists())
            or self._cpp_main.stat().st_mtime_ns > self._lib_path.stat().st_mtime_ns
        )
        if not need:
            return
        self._compile_lib(self._cpp_main, self._lib_path)

    @staticmethod
    def _compile_lib(cpp_main: Path, lib_path: Path) -> None:
        if os.name == "nt":
            cmd = (
                f'g++ -O3 -shared -fPIC -std=c++17 -static-libgcc -static-libstdc++ '
                f'"{cpp_main}" -o "{lib_path}"'
            )
        else:
            cmd = f'g++ -O3 -shared -fPIC -std=c++17 "{cpp_main}" -o "{lib_path}"'
        rc = os.system(cmd)
        if rc != 0 or not lib_path.exists():
            raise RuntimeError(f"Failed to build Polar SCL shared library: {cmd}")

    def _configure_windows_dll_dirs(self, lib_dir: Path) -> None:
        if os.name != "nt":
            return
        candidates: list[Path] = [
            lib_dir,
            Path(sys.executable).parent,
            Path(sys.prefix) / "Library" / "bin",
        ]
        for name in ("libstdc++-6.dll", "libgcc_s_seh-1.dll", "libwinpthread-1.dll"):
            p = shutil.which(name)
            if p:
                candidates.append(Path(p).parent)

        seen: set[str] = set()
        for p in candidates:
            if not p.exists():
                continue
            ps = str(p.resolve())
            if ps in seen:
                continue
            seen.add(ps)
            try:
                self._dll_handles.append(os.add_dll_directory(ps))
            except Exception:
                pass

    def _load(self) -> None:
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
        try:
            self._decode_frozen = self._lib.decode_ca_scl_batch_frozen
        except AttributeError:
            self._decode_frozen = None
        if self._decode_frozen is not None:
            self._decode_frozen.argtypes = [
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.POINTER(ctypes.c_uint8),
                ctypes.POINTER(ctypes.c_uint8),
                ctypes.POINTER(ctypes.c_float),
                ctypes.POINTER(ctypes.c_uint8),
            ]
            self._decode_frozen.restype = None
        try:
            self._decode_frozen_plain = self._lib.decode_scl_batch_frozen_plain
        except AttributeError:
            self._decode_frozen_plain = None
        if self._decode_frozen_plain is not None:
            self._decode_frozen_plain.argtypes = [
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.POINTER(ctypes.c_uint8),
                ctypes.POINTER(ctypes.c_uint8),
                ctypes.POINTER(ctypes.c_float),
                ctypes.POINTER(ctypes.c_uint8),
            ]
            self._decode_frozen_plain.restype = None

    @staticmethod
    def _validate_common(
        n: int,
        k: int,
        frames: int,
        mask: np.ndarray,
        llrs: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        if n <= 0 or k <= 0 or frames <= 0:
            raise ValueError("n/k/frames must be positive")
        if n & (n - 1):
            raise ValueError(f"n must be a power of two, got {n}")
        if k > n:
            raise ValueError(f"k must not exceed n: k={k}, n={n}")

        mask_raw = np.asarray(mask).reshape(-1)
        if mask_raw.size != int(n):
            raise ValueError(f"mask size mismatch: expected {n}, got {mask_raw.size}")
        if not np.all((mask_raw == 0) | (mask_raw == 1)):
            raise ValueError("mask must be binary")
        mask_u8 = np.ascontiguousarray(mask_raw, dtype=np.uint8)
        if int(np.sum(mask_u8)) != int(k):
            raise ValueError(f"mask popcount mismatch: expected {k}, got {int(np.sum(mask_u8))}")

        llr_raw = np.asarray(llrs)
        if llr_raw.size != int(frames) * int(n):
            raise ValueError(f"llrs size mismatch: expected {frames * n}, got {llr_raw.size}")
        if not np.all(np.isfinite(llr_raw)):
            raise ValueError("llrs must be finite")
        llr_f32 = np.ascontiguousarray(llr_raw, dtype=np.float32).reshape(int(frames), int(n))
        return mask_u8, llr_f32

    @staticmethod
    def _validate_frozen(frozen_values: np.ndarray, frames: int, n: int) -> np.ndarray:
        frozen_raw = np.asarray(frozen_values)
        if frozen_raw.size != int(frames) * int(n):
            raise ValueError(f"frozen_values size mismatch: expected {frames * n}, got {frozen_raw.size}")
        if not np.all((frozen_raw == 0) | (frozen_raw == 1)):
            raise ValueError("frozen_values must be binary")
        return np.ascontiguousarray(frozen_raw, dtype=np.uint8).reshape(int(frames), int(n))

    def decode_batch(
        self,
        n: int,
        k: int,
        frames: int,
        mask: np.ndarray,
        llrs: np.ndarray,
    ) -> np.ndarray:
        if self._decode is None:
            raise RuntimeError("Decoder function is not initialized")
        mask_u8, llr_f32 = self._validate_common(n, k, frames, mask, llrs)
        out_bits = np.zeros((int(frames), int(k)), dtype=np.uint8)

        self._decode(
            int(n),
            int(k),
            int(frames),
            mask_u8.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
            llr_f32.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            out_bits.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
        )
        return out_bits

    def decode_batch_frozen(
        self,
        n: int,
        k: int,
        frames: int,
        mask: np.ndarray,
        frozen_values: np.ndarray,
        llrs: np.ndarray,
    ) -> np.ndarray:
        if self._decode_frozen is None:
            raise RuntimeError("Frozen-aware decoder function is not initialized")
        mask_u8, llr_f32 = self._validate_common(n, k, frames, mask, llrs)
        frozen_u8 = self._validate_frozen(frozen_values, frames, n)
        out_bits = np.zeros((int(frames), int(k)), dtype=np.uint8)

        self._decode_frozen(
            int(n),
            int(k),
            int(frames),
            mask_u8.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
            frozen_u8.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
            llr_f32.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            out_bits.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
        )
        return out_bits

    def decode_batch_frozen_plain(
        self,
        n: int,
        k: int,
        frames: int,
        mask: np.ndarray,
        frozen_values: np.ndarray,
        llrs: np.ndarray,
    ) -> np.ndarray:
        """Decode arbitrary information bits with frozen-aware ordinary SCL (L=4)."""
        if self._decode_frozen_plain is None:
            raise RuntimeError("Frozen-aware plain SCL decoder function is not initialized")
        mask_u8, llr_f32 = self._validate_common(n, k, frames, mask, llrs)
        frozen_u8 = self._validate_frozen(frozen_values, frames, n)
        out_bits = np.zeros((int(frames), int(k)), dtype=np.uint8)

        self._decode_frozen_plain(
            int(n),
            int(k),
            int(frames),
            mask_u8.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
            frozen_u8.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
            llr_f32.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            out_bits.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
        )
        return out_bits

