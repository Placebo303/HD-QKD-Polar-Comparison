"""Import-only template for one frozen CLI module per process."""

from __future__ import annotations

import importlib
import os
import pytest
from pathlib import Path


def test_import_frozen_module_and_repo_anchor() -> None:
    module_name = os.environ.get("S7_IMPORT_MODULE")
    if not module_name:
        pytest.skip("S7_IMPORT_MODULE is set by the scoped import smoke command")
    module = importlib.import_module(module_name)
    repo_root = getattr(module, "_repo_root", None)
    if callable(repo_root):
        assert Path(repo_root()).resolve() == Path.cwd().resolve()
