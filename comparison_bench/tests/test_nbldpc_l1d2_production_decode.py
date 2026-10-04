"""Production decode adapter contract tests (fake-only, T0/T1).

No production decoder call, no scientific execution, no production-root
write. The v35 entrypoint is monkeypatched with a recording fake; the thin
production CLI is exercised only through ``--help``-equivalent parsing,
``--dry-run`` and refusal paths (the ``--execute`` path is never invoked).
"""
from __future__ import annotations

import inspect
import sys
import types
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "comparison_bench" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import comparison_bench.cli.nbldpc_l1d2_synth_batch_prod as prod_cli  # noqa: E402
import comparison_bench.formal_ir.nbldpc_l1d2_production_decode as prod  # noqa: E402
import comparison_bench.formal_ir.v35_algorithm_development as v35  # noqa: E402

_BASE_ARGS = ["--width", "128",
              "--graph-seed", "2026093701",
              "--data-seed", "2026093201",
              "--frames", "0-1",
              "--model-f-root", "workspace/v72p2d5_model_f_input/20260907_r1"]


def test_signature_accepts_layer():
    params = inspect.signature(prod.production_decode_fn).parameters
    assert "layer" in params


def test_fixed_params_across_layers(monkeypatch):
    calls = []
    sentinel = object()

    def _fake(h, prior, syndrome, **kwargs):
        calls.append((np.asarray(h), np.asarray(prior),
                      np.asarray(syndrome), dict(kwargs)))
        return sentinel

    monkeypatch.setattr(v35, "decode_row_layered_fftqspa", _fake)
    h = np.zeros((2, 3), dtype=np.uint8)
    prior = np.full((3, 32), 1.0 / 32)
    syndrome = np.zeros(2, dtype=np.uint8)
    for layer in (None, 0, 1):
        assert prod.production_decode_fn(h, prior, syndrome,
                                          layer=layer) is sentinel
    assert len(calls) == 3
    for h_c, prior_c, syndrome_c, kwargs in calls:
        assert np.array_equal(h_c, h)
        assert np.array_equal(prior_c, prior)
        assert np.array_equal(syndrome_c, syndrome)
        assert kwargs == {"max_iter": 90, "damping_alpha": 1.0,
                          "warm_beliefs": None, "field": None}


def test_import_performs_no_decode(monkeypatch):
    calls = []

    def _boom(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("decode must not run at import")

    fake_v35 = types.ModuleType(
        "comparison_bench.formal_ir.v35_algorithm_development")
    fake_v35.decode_row_layered_fftqspa = _boom
    monkeypatch.setitem(
        sys.modules,
        "comparison_bench.formal_ir.v35_algorithm_development", fake_v35)
    import importlib
    importlib.reload(prod)
    assert calls == []
    assert not hasattr(prod, "v35")


def test_prod_cli_help_visible(capsys):
    with pytest.raises(SystemExit) as exc:
        prod_cli.main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "--execute" in out
    assert "--dry-run" in out


def test_prod_cli_dry_run_zero_write(tmp_path):
    out_root = tmp_path / "fresh-root"
    code = prod_cli.main(_BASE_ARGS + ["--out-root", str(out_root),
                                       "--dry-run"])
    assert code == 0
    assert not out_root.exists()


def test_prod_cli_no_execute_refuses_without_write(tmp_path):
    out_root = tmp_path / "fresh-root"
    code = prod_cli.main(_BASE_ARGS + ["--out-root", str(out_root)])
    assert code == 2
    assert not out_root.exists()


def test_prod_cli_refuses_divergent_decoder_profile(tmp_path):
    out_root = tmp_path / "fresh-root"
    code = prod_cli.main(_BASE_ARGS + ["--out-root", str(out_root),
                                       "--max-iter", "30",
                                       "--dry-run"])
    assert code == 2
    assert not out_root.exists()


def test_prod_cli_refuses_fake_decoder_flag(tmp_path):
    out_root = tmp_path / "fresh-root"
    code = prod_cli.main(_BASE_ARGS + ["--out-root", str(out_root),
                                       "--fake-decoder", "--dry-run"])
    assert code == 2
    assert not out_root.exists()
