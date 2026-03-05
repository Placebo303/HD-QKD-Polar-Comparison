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
    """Thin ctypes wrapper for C++ CA-SCL batch decoder."""

    def __init__(self, repo_root: Path | str | None = None, force_rebuild: bool = False) -> None:
        self._repo_root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[2]
        self._cpp_main = (self._repo_root / "src" / "reconciliation" / "cpp_polar" / "main.cpp").resolve()
        self._lib_path = self._resolve_lib_path()
        self._dll_handles: list[Any] = []
        self._lib: ctypes.CDLL | None = None
        self._decode = None

        self._build_if_needed(force=force_rebuild)
        self._configure_windows_dll_dirs(self._lib_path.parent)
        self._load()

    @property
    def lib_path(self) -> Path:
        return self._lib_path

    def _resolve_lib_path(self) -> Path:
        ext = ".dll" if os.name == "nt" else ".so"
        return (self._repo_root / "src" / "reconciliation" / "cpp_polar" / f"ca_scl{ext}").resolve()

    def _build_if_needed(self, force: bool = False) -> None:
        self._lib_path.parent.mkdir(parents=True, exist_ok=True)
        need = force or (not self._lib_path.exists())
        if not need and self._cpp_main.exists():
            need = self._cpp_main.stat().st_mtime > self._lib_path.stat().st_mtime
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
            raise RuntimeError(f"Failed to build CA-SCL shared library: {cmd}")

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
        if n <= 0 or k <= 0 or frames <= 0:
            raise ValueError("n/k/frames must be positive")

        mask_u8 = np.ascontiguousarray(mask, dtype=np.uint8).reshape(-1)
        if mask_u8.size != int(n):
            raise ValueError(f"mask size mismatch: expected {n}, got {mask_u8.size}")
        if int(np.sum(mask_u8)) != int(k):
            raise ValueError(f"mask popcount mismatch: expected {k}, got {int(np.sum(mask_u8))}")

        llr_f32 = np.ascontiguousarray(llrs, dtype=np.float32).reshape(int(frames), int(n))
        out_bits = np.empty((int(frames), int(k)), dtype=np.uint8)

        self._decode(
            int(n),
            int(k),
            int(frames),
            mask_u8.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
            llr_f32.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            out_bits.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
        )
        return out_bits

