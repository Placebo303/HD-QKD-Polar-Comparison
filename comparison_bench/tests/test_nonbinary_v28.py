"""Focused V28R tests; no holdout, parquet, raw ttbin, DE, or FER."""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import nonbinary_codebook as cb
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v10_fftqspa as qspa
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v28 as v28
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField


def _small_config():
    return {
        "schema": "nbldpc_v28r_test_small", "q": 32, "n": 32, "m1": 4, "m2_max": 8,
        "sources": {"1M": {"m2": 8, "h_total": 4.0}},
        "seed_l1": v28.SEED_L1, "seed_l2": v28.SEED_L2,
        "topology": "v28r_degree2_ordered_pair_graph",
        "coefficient_derivation": cb._COEFFICIENT_DERIVATION,
        "coefficient_call": "_coefficient(q, seed, variable_index, endpoint_slot)",
        "tag_bits": 64, "tag_method": "sha256(bytes(x1)||bytes(x2))[:8]",
        "field_id": GF2mField.create(32).spec.field_id,
        "posterior_semantics": "synthetic_one_hot", "sequential_semantics": "Bob-only",
        "p_noiseless": 1e-3, "p_controlled": .2, "max_iter": 15,
    }


def _rnd(n, q=32, seed=5):
    r = random.Random(seed)
    return [r.randrange(q) for _ in range(n)]


class SpyAdapter:
    def __init__(self, fail_l1=False):
        self.calls = []
        self.fail_l1 = fail_l1

    def posterior_rows(self, lid, b, u1=None):
        b = np.asarray(b, dtype=np.int64)
        self.calls.append((lid, b.copy(), None if u1 is None else list(u1)))
        if self.fail_l1 and lid == "L1":
            return np.zeros((len(b), 32), dtype=np.float64)
        out = np.full((len(b), 32), 1e-12)
        symbols = (b >> 5) & 31 if lid == "L1" else b & 31
        out[np.arange(len(b)), symbols] = 1.0
        return out / out.sum(axis=1, keepdims=True)


def test_frozen_matrix_contract_and_rank():
    cfg = v28.frozen_v28_config()
    h1, h2 = v28.build_matrices(cfg)
    field = GF2mField.create(32)
    assert len(h1) == 6 and len(h1[0]) == 1024
    assert set(h2) == {"1M", "1p5M", "2M"}
    assert cb.gf_rank(h1, field) == 6
    assert np.all(np.count_nonzero(np.asarray(h1), axis=0) == 2)
    assert dict(sorted({int(x): int(c) for x, c in zip(*np.unique(np.count_nonzero(h1, axis=1), return_counts=True))}.items())) == {341: 4, 342: 2}
    expected_l1 = [(i, j) for i in range(6) for j in range(i + 1, 6)] * 68 + [(0, 1), (0, 2), (1, 3), (4, 5)]
    assert [tuple(np.flatnonzero(np.asarray(h1)[:, j])) for j in range(1024)] == expected_l1
    expected_rows = {"1M": {10: 86, 11: 108}, "1p5M": {10: 152, 11: 48}, "2M": {10: 174, 11: 28}}
    for source, m in cfg["sources"].items():
        hm = v28.layer_matrix(h2, source, cfg)
        assert hm is h2[source]
        assert np.all(np.count_nonzero(np.asarray(hm), axis=0) == 2)
        assert cb.gf_rank(hm, field) == m["m2"]
        vals, counts = np.unique(np.count_nonzero(np.asarray(hm), axis=1), return_counts=True)
        assert dict(zip(vals.tolist(), counts.tolist())) == expected_rows[source]
    with pytest.raises(TypeError):
        v28.layer_matrix(h1, "1M", cfg)


def test_l2_pair_order_is_independent_and_unique():
    cfg = v28.frozen_v28_config()
    _, h2 = v28.build_matrices(cfg)
    for source, si in cfg["sources"].items():
        hm = np.asarray(h2[source])
        pairs = [tuple(np.flatnonzero(hm[:, j])) for j in range(1024)]
        assert len(set(pairs)) == 1024
        assert pairs[0] == (0, 1)


def test_posterior_decoder_noiseless_and_fail_closed():
    cfg = _small_config(); field = GF2mField.create(32)
    h1, h2 = v28.build_matrices(cfg); h2 = v28.layer_matrix(h2, "1M", cfg)
    x = _rnd(cfg["n"], seed=11); s = v28.compute_syndrome(field, h1, x)
    prior = np.zeros((cfg["n"], 32)); prior[:, 0] = 1.0
    result = v28.decode_error_domain_posterior(field, x, h1, s, prior, 5)
    assert result["status"] == qspa.STATUS_SUCCESS
    assert result["x_hat"] == x and result["reconstruction_ok"] is True
    bad = prior.copy(); bad[0, :] = np.nan
    failed = v28.decode_error_domain_posterior(field, x, h1, s, bad, 5)
    assert failed["status"] == qspa.STATUS_DECODE_FAILED
    assert failed["reconstruction_ok"] is False and failed["x_hat"] is None


def test_sequential_l2_receives_returned_x1_hat_and_not_truth():
    cfg = _small_config(); field = GF2mField.create(32); adapter = SpyAdapter()
    h1, h2m = v28.build_matrices(cfg); h2 = v28.layer_matrix(h2m, "1M", cfg)
    x1, x2 = _rnd(32, seed=1), _rnd(32, seed=2)
    s1, s2 = v28.compute_syndrome(field, h1, x1), v28.compute_syndrome(field, h2, x2)
    bob = ((np.asarray(x1) << 5) | np.asarray(x2)).tolist()
    out = v28.decode_two_layer_sequential_empirical(field, bob, x1, x2, s1, s2, "1M", adapter, config=cfg)
    assert out["L1"]["status"] == qspa.STATUS_SUCCESS and out["L2"]["status"] == qspa.STATUS_SUCCESS
    assert [call[0] for call in adapter.calls] == ["L1", "L2"]
    assert adapter.calls[1][2] == out["x1_hat"]
    assert adapter.calls[1][2] is not x1
    assert out["alice_truth_used"] is False


def test_sequential_failure_stops_l2():
    cfg = _small_config(); field = GF2mField.create(32); adapter = SpyAdapter(fail_l1=True)
    h1, h2m = v28.build_matrices(cfg); h2 = v28.layer_matrix(h2m, "1M", cfg)
    x1, x2 = _rnd(32, seed=4), _rnd(32, seed=5)
    out = v28.decode_two_layer_sequential_empirical(field, ((np.asarray(x1) << 5) | np.asarray(x2)).tolist(), x1, x2,
                                                      v28.compute_syndrome(field, h1, x1), v28.compute_syndrome(field, h2, x2), "1M", adapter, config=cfg)
    assert out["L1"]["status"] == qspa.STATUS_DECODE_FAILED
    assert out["L2"]["status"] == "not_run" and len(adapter.calls) == 1


def test_tag_exact_and_leakage():
    x1, x2 = [1, 2, 31], [0, 3, 4]
    expected = hashlib.sha256(bytes(x1) + bytes(x2)).digest()[:8].hex()
    assert v28.tag64(x1, x2) == expected and len(expected) == 16
    cfg = v28.frozen_v28_config()
    for si in cfg["sources"].values():
        assert v28.leakage_bits(cfg["m1"] + si["m2"]) / (cfg["n"] * si["h_total"]) < 1.3


def test_run_and_readonly_verify_small():
    root = Path("workspace/v28r_pytest_case")
    out = v28.run_v28_evidence(root, _small_config())
    assert out["status"] == v28.TERMINAL_READY
    manifest = json.loads((root / "RUN_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["matrix_contract"]["L1"]["edges"] == 2 * _small_config()["n"]
    verified = v28.verify_v28(root)
    assert verified["ok"] is True
    assert (root / "readonly_verify.json").exists()


def test_manifest_tamper_is_rejected():
    root = Path("workspace/v28r_manifest_tamper")
    v28.run_v28_evidence(root, _small_config())
    manifest_path = root / "RUN_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["sources"][0]["tag64_hex"] = "0000000000000000"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    verified = v28.verify_v28(root)
    assert verified["ok"] is False
    assert any("manifest" in problem for problem in verified["problems"])


def test_canonical_adapter_missing_does_not_fallback(monkeypatch):
    cfg = _small_config()
    cfg["sources"]["1M"].update({
        "source_id": v28.SOURCE_IDS["1M"], "delay_used_ps": -50, "n_pairs": 512000,
    })
    root = Path("workspace/v28r_canonical_missing_adapter")
    v28.run_v28_evidence(root, cfg, adapters={"1M": SpyAdapter()})

    def missing(_config):
        raise FileNotFoundError("synthetic missing V26 train model")

    monkeypatch.setattr(v28, "_load_adapters", missing)
    verified = v28.verify_v28(root)
    assert verified["ok"] is False
    assert any("canonical V26 adapter unavailable" in problem for problem in verified["problems"])
