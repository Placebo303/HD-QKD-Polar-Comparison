"""Stage-1 driver tests S-T06..S-T08 (fake-only, T0/T1).

No production decoder import, no scientific call, no root creation, no
real-data contact. Every decoder below is an explicitly injected fake;
missing fakes refuse before any binding.
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "comparison_bench" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import comparison_bench.cli.nbldpc_l1_degree2_driver as driver  # noqa: E402
import comparison_bench.formal_ir.nbldpc_l1_degree2_layout as layout  # noqa: E402
import comparison_bench.formal_ir.v72p2d5_gf32_rate_mother as d5  # noqa: E402

_TINY_H = np.array([[1, 2, 0],
                    [0, 3, 1]], dtype=np.int64)


class _FakeResult:
    def __init__(self, x_hat, syndrome_ok, beliefs, provenance):
        self.x_hat = np.asarray(x_hat, dtype=np.int64)
        self.syndrome_ok = bool(syndrome_ok)
        self.iterations = 1
        self.status = "fake_converged"
        self.final_beliefs = np.asarray(beliefs, dtype=np.float64)
        self.belief_provenance = provenance


def _map_decode_factory(calls: list):
    def fake(h, prior, syndrome, layer=None):
        calls.append({"h": np.asarray(h).copy(),
                      "prior": np.asarray(prior).copy(),
                      "syndrome": np.asarray(syndrome).copy(),
                      "layer": layer})
        n = np.asarray(h).shape[1]
        x_hat = np.argmax(np.asarray(prior, dtype=np.float64), axis=1)
        assert x_hat.shape == (n,)
        logp = np.log(np.asarray(prior, dtype=np.float64) + 1e-300)
        return _FakeResult(x_hat, True, logp, "CHECK_UPDATED")
    return fake


def _tiny_prior_block(truth):
    # p1: (U1=32, Bob=4) columns normalized; p2: (U1, Bob, U2) over U2.
    # Matches the d5 layered-block contract p1[:, bob] / q @ P.
    truth = np.asarray(truth, dtype=np.int64)
    n = len(truth)
    bob = np.arange(n, dtype=np.int64) % 4  # distinct per position here
    p1 = np.full((32, 4), 1e-6)
    for i in range(n):
        p1[int(truth[i]), int(bob[i])] = 1.0
    p1 = p1 / p1.sum(axis=0, keepdims=True)
    p2 = np.full((32, 4, 32), 1e-6)
    for i in range(n):
        p2[int(truth[i]), int(bob[i]), int(truth[i])] = 1.0
    p2 = p2 / p2.sum(axis=2, keepdims=True)
    return p1, p2, {"bob": bob, "u1": np.asarray(truth, dtype=np.int64),
                    "u2": np.asarray(truth, dtype=np.int64)}


def _nullspace_vector(h):
    h = np.asarray(h, dtype=np.int64)
    n = h.shape[1]
    rng = np.random.default_rng(11)
    for _ in range(2000):
        z = rng.integers(0, 32, size=n)
        if np.any(z) and layout.gf32_syndrome(h, z) == [0] * h.shape[0]:
            return z
    raise AssertionError("tiny nullspace vector not found")


# --------------------------------------------------------------------------- #
# S-T06: isolation truth-swap invariance (same public inputs -> same behavior)
# --------------------------------------------------------------------------- #
def test_st06_truth_swap_invariance():
    h = _TINY_H.copy()
    z = _nullspace_vector(h)
    u_base = np.array([5, 7, 9], dtype=np.int64)
    u_swap = np.array([(int(a) ^ int(b)) for a, b in zip(u_base, z)],
                      dtype=np.int64)
    assert not np.array_equal(u_base, u_swap)
    assert layout.gf32_syndrome(h, u_base) == layout.gf32_syndrome(h, u_swap)
    p1, p2, block_a = _tiny_prior_block(u_base)
    _, _, block_b = _tiny_prior_block(u_swap)
    # same Bob inputs and shared prior tables; only the isolated truth differs
    assert np.array_equal(block_a["bob"], block_b["bob"])
    calls_a, calls_b = [], []
    out_a = driver.run_pair(_map_decode_factory(calls_a), h, h, h,
                            p1, p2, block_a)
    out_b = driver.run_pair(_map_decode_factory(calls_b), h, h, h,
                            p1, p2, block_b)
    for arm in ("control", "candidate"):
        # Decoder behavior identical (same prior+syndrome in): syndrome flags
        # and stop behavior match; exact flags differ ONLY via the isolated
        # truth comparator (x_hat is the same object of choice).
        for key in ("app_l1_syndrome_ok", "app_l2_syndrome_ok",
                    "app_l1_iterations", "app_l2_iterations"):
            assert out_a[arm][key] == out_b[arm][key], (arm, key)
        assert out_a[arm]["app_l1_exact"] is True
        assert out_b[arm]["app_l1_exact"] is False
    assert len(calls_a) == len(calls_b) == 4  # L1+L2 per arm, both runs
    for rec_a, rec_b in zip(calls_a, calls_b):
        assert np.array_equal(rec_a["prior"], rec_b["prior"])
        assert np.array_equal(rec_a["syndrome"], rec_b["syndrome"])
        assert set(rec_a) == {"h", "prior", "syndrome", "layer"}
    # both arms identical here by construction; oracle keys absent
    assert out_a["oracle"] is False
    assert set(out_a) == {"control", "candidate", "oracle",
                          "shared_h2", "shared_block"}
    for arm in ("control", "candidate"):
        assert not any(str(k).startswith("oracle_")
                       for k in out_a[arm])


# --------------------------------------------------------------------------- #
# S-T07: failed-frame disclosure + accepted-wrong isolation + abort != success
# --------------------------------------------------------------------------- #
def test_st07_failure_accounting_and_abort():
    disc = layout.disclosure_bits(118, 104, extra_parity_bits=10,
                                  verify_tag_bits=64, other_public_bits=5)
    assert disc == {"l1_syn_bits": 590, "l2_syn_bits": 520,
                    "extra_parity_bits": 10, "verify_tag_bits": 64,
                    "other_public_bits": 5,
                    "total_public_bits": 590 + 520 + 10 + 64 + 5}
    failed = layout.classify_frame(u1_exact=False, u2_exact=False,
                                   syn_l1=False, syn_l2=False,
                                   verify_accept=False,
                                   status="nonconverged", disclosure=disc)
    assert layout.is_success(failed) is False
    # failed frames keep full disclosure (attempted, no refund)
    assert (failed["l1_syn_bits"], failed["l2_syn_bits"],
            failed["verify_tag_bits"]) == (590, 520, 64)
    wrong = layout.classify_frame(u1_exact=True, u2_exact=False, syn_l1=True,
                                  syn_l2=True, verify_accept=True,
                                  status="ok", disclosure=disc)
    assert wrong["pair_exact"] is False and wrong["accepted_wrong"] is True
    assert layout.is_success(wrong) is False
    aborted = layout.classify_frame(u1_exact=True, u2_exact=True, syn_l1=True,
                                    syn_l2=True, verify_accept=True,
                                    status="resource_abort", disclosure=disc)
    assert layout.is_success(aborted) is False
    with pytest.raises(ValueError):
        layout.classify_frame(u1_exact=True, u2_exact=True, syn_l1=True,
                              syn_l2=True, verify_accept=True,
                              status="bogus", disclosure=disc)
    with pytest.raises(ValueError):
        layout.disclosure_bits(-1, 3)


# --------------------------------------------------------------------------- #
# S-T08: no-production-call guard
# --------------------------------------------------------------------------- #
def test_st08_missing_fake_refuses_before_binding():
    with pytest.raises(ValueError):
        driver.require_decode_fn(None)
    with pytest.raises(ValueError):
        driver.run_pair(None, _TINY_H, _TINY_H, _TINY_H,
                        np.zeros((3, 32)), np.zeros((32, 4, 32)),
                        {"bob": np.zeros(3, dtype=np.int64),
                         "u1": np.zeros(3, dtype=np.int64),
                         "u2": np.zeros(3, dtype=np.int64)})
    with pytest.raises(ValueError):
        driver.run_pair("not-callable", _TINY_H, _TINY_H, _TINY_H,
                        np.zeros((3, 32)), np.zeros((32, 4, 32)),
                        {"bob": np.zeros(3, dtype=np.int64),
                         "u1": np.zeros(3, dtype=np.int64),
                         "u2": np.zeros(3, dtype=np.int64)})


def test_st08_no_default_production_binding_in_source():
    for module in (layout, driver):
        src = Path(module.__file__).read_text()
        for token in ("decode_row_layered", "historical_g0_decoder",
                      "_load_g0_decoder", "v35_algorithm",
                      "from .v35", "import v35", "BATCH_AUTHORIZED",
                      "REPLACEMENT_SEEDS", "outputs_comparison",
                      "results/", "--batch", "--execute", "--forward-batch"):
            assert token not in src, (module.__name__, token)
    assert driver.ORACLE_HARDCODED is False
    assert "oracle" not in inspect.signature(driver.run_pair).parameters
    opts = driver.build_parser()._actions
    names = {o for a in opts for o in a.option_strings}
    assert "--oracle" not in names
    assert "--batch" not in names and "--forward-batch" not in names
    assert not any(n.startswith("--execute") for n in names)
