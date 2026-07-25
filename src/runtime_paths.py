from __future__ import annotations

import os
import re
from pathlib import Path


_WINDOWS_DRIVE_RE = re.compile(r"^(?P<drive>[A-Za-z]):[\\/](?P<rest>.*)$")
_WINDOWS_DATA_PREFIX = re.compile(r"^d:[\\/]+data(?P<rest>(?:[\\/].*)?)$", re.IGNORECASE)


def is_wsl_posix() -> bool:
    return os.name == "posix"


def default_project_results_root(repo_root: Path) -> Path:
    env_root = str(os.getenv("PROJECT_RESULTS_ROOT") or "").strip()
    if env_root:
        return Path(env_root).expanduser()
    if is_wsl_posix():
        return Path.home() / "var" / "results_hot" / repo_root.name
    return repo_root / "results"


def repo_relative_results_path(repo_root: Path, relative_path: str) -> Path:
    rel = relative_path.replace("\\", "/").lstrip("/")
    if rel == "results" or rel.startswith("results/"):
        suffix = rel[len("results") :].lstrip("/\\")
        root = default_project_results_root(repo_root)
        return root if not suffix else root / Path(suffix)
    return (repo_root / Path(rel)).resolve()


def resolve_repo_path(repo_root: Path, value: str | Path) -> Path:
    text = str(value).strip()
    pp = Path(text)
    if pp.is_absolute():
        return pp
    return repo_relative_results_path(repo_root, text)


def windows_to_wsl_path(text: str) -> str:
    norm = text.replace("\\", "/")
    m = _WINDOWS_DRIVE_RE.match(norm)
    if not m:
        return norm
    drive = m.group("drive").lower()
    rest = m.group("rest").lstrip("/")
    return f"/mnt/{drive}/{rest}"


def map_data_path(value: str | Path) -> Path:
    text = str(value).strip()
    data_root = str(os.getenv("PROJECT_DATA_ROOT") or "").strip()
    if data_root:
        match = _WINDOWS_DATA_PREFIX.match(text)
        if match:
            suffix = (match.group("rest") or "").replace("\\", "/").lstrip("/")
            return (Path(data_root).expanduser() / suffix).resolve()
    if is_wsl_posix():
        return Path(windows_to_wsl_path(text))
    return Path(text)
