"""D7-D schedule-discriminator qualification S01-S22 (fake/DI only).

No test creates ``workspace/d7_d_schedule_discriminator_*`` or reads real
Model-F content; every scientific-run decoder is an injected fake.  The real
production flooding decoder is contacted only by the tiny synthetic
``F01``-``F05`` certification fixtures (q=32, tiny graphs); no Model-F, no
formal root and no scientific-scale decode is touched.  Each D7 inner
regression suite runs in its own pytest process (troubleshooting 2026-09-10:
combined formal_ir collection is unsupported).

The D7-C suite carries one pre-existing stale lifecycle assertion
(``test_c19_...`` asserts no D7-C evidence root exists; the accepted D7-C root
now exists as frozen baseline), so S20 deselects exactly that test with the
reason recorded.
"""

from __future__ import annotations

import csv
import importlib.util
import inspect
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "comparison_bench" / "src"
CORE_PATH = (SRC / "comparison_bench" / "formal_ir"
             / "v72p2d7_gf32_schedule_discriminator.py")
RUNNER = REPO / "scripts" / "v72p2d7_gf32_schedule_discriminator.py"
TEST_FILE = Path(__file__).resolve()
WS = REPO / "workspace"
MODEL_F_ROOT = WS / "v72p2d5_model_f_input" / "20260907_r1"
D7C_ROOT = (WS / "d7_c_bidirectional_oracle_"
            "94c0ea15-a786-4cb8-a991-6fec521cccae")
D7C_ROOT_SIZES = {
    "manifest.json": 2709, "decoder_records.csv": 23599,
    "paired_summary.csv": 1130, "summary.json": 728, "report.md": 362,
    "command_log.txt": 282,
}
D7C_CYCLE_STATE = (REPO / "docs" / "research_cycles"
                   / "V72P2D7-GF32-BIDIRECTIONAL-ORACLE" / "cycle_state.yaml")
D7D_CYCLE_STATE = (REPO / "docs" / "research_cycles"
                   / "V72P2D7-GF32-SCHEDULE-DISCRIMINATOR" / "cycle_state.yaml")
CERT_DOC = (REPO / "docs" / "research_cycles"
            / "V72P2D7-GF32-SCHEDULE-DISCRIMINATOR"
            / "D7_D_FLOODING_CERTIFICATION_R1.md")
D7A_FILE = TEST_FILE.parent / "test_v72p2d7_gf32_decoder_certification.py"
D7C_FILE = TEST_FILE.parent / "test_v72p2d7_gf32_bidirectional_oracle.py"
D7B_FILE = TEST_FILE.parent / "test_v72p2d7_gf32_easy_regime.py"
D5_FILE = TEST_FILE.parent / "test_v72p2d5_gf32_rate_mother.py"
V35_FILE = TEST_FILE.parent / "test_v35_algorithm_development.py"
SUB_TIMEOUT = 1200

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _load_core_isolated():
    """Load the D7-D core by file path without leaving package-cache residue."""
    saved = {k: v for k, v in sys.modules.items()
             if k == "comparison_bench" or k.startswith("comparison_bench.")}
    for key in saved:
        sys.modules.pop(key, None)
    try:
        spec = importlib.util.spec_from_file_location(
            "d7d_schedule_discriminator_under_test", str(CORE_PATH))
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
    finally:
        for key in [k for k in sys.modules
                    if k == "comparison_bench" or k.startswith("comparison_bench.")]:
            sys.modules.pop(key, None)
        sys.modules.update(saved)
    return mod


d7d = _load_core_isolated()
d7c = d7d.d7c

from comparison_bench.formal_ir import (  # noqa: E402
    v35_algorithm_development as v35,
)
from comparison_bench.formal_ir import (  # noqa: E402
    v72p2d7_gf32_decoder_certification as oracle,
)
from comparison_bench.formal_ir.nonbinary_field import GF2mField  # noqa: E402

Q = 32
TOL = 1e-10
_OBS_ITERATIONS = 1


# --------------------------------------------------------------------------
# Shared fake fixtures (no real Model-F / no production run decoder)
# --------------------------------------------------------------------------

def _uniform_joint() -> np.ndarray:
    return np.full((Q, Q, d7d.BOB_DIM), 1.0 / (Q * Q))


def _perfect_oracle_joint() -> np.ndarray:
    """Marginals flat, oracle slices exact for ``_perfect_oracle_block``."""
    base = np.full((Q, Q), 1.0 / Q)
    for u2 in range(Q):
        base[(u2 + 1) % Q, u2] += 1.0 / 64.0
        base[u2, u2] -= 1.0 / 64.0
    return np.repeat((base / float(Q))[:, :, None], d7d.BOB_DIM, axis=2)


def _perfect_oracle_block(seed) -> dict:
    bob = ((np.arange(d7d.N) * 13 + int(seed)) % d7d.BOB_DIM).astype(np.int64)
    u2 = (bob % 30) + 1
    u1 = u2 + 1
    return {"bob": bob, "u1": u1, "u2": u2, "alice": u1 * Q + u2}


def _peaked_joint() -> np.ndarray:
    """Every condition prior peaks exactly at the sampled truth."""
    joint = np.zeros((Q, Q, d7d.BOB_DIM))
    for b in range(d7d.BOB_DIM):
        u1 = (b % 31) + 1
        u2 = ((b // 31) % 31) + 1
        joint[u1, u2, b] = 1.0
    return joint


def _peaked_block(seed) -> dict:
    bob = ((np.arange(d7d.N) * 13 + int(seed)) % d7d.BOB_DIM).astype(np.int64)
    u1 = (bob % 31) + 1
    u2 = ((bob // 31) % 31) + 1
    return {"bob": bob, "u1": u1, "u2": u2, "alice": u1 * Q + u2}


def _sampler(sampler_fn=None, events=None):
    sampler_fn = sampler_fn or _perfect_oracle_block

    def sample(p_b, p_f, n, seed):
        if events is not None:
            events.append(("sample", int(seed)))
        return sampler_fn(seed)

    return sample


def _argmax_decoder(iterations: int = _OBS_ITERATIONS):
    def decode(h, prior, syndrome):
        p = np.asarray(prior, dtype=np.float64)
        return {"x_hat": np.argmax(p, axis=1).astype(np.int64),
                "syndrome_ok": True, "iterations": int(iterations),
                "final_beliefs": np.log(p + 1e-300), "status": "fake_argmax"}

    return decode


def _zeros_decoder(iterations: int = _OBS_ITERATIONS):
    def decode(h, prior, syndrome):
        p = np.asarray(prior, dtype=np.float64)
        return {"x_hat": np.zeros(p.shape[0], dtype=np.int64),
                "syndrome_ok": True, "iterations": int(iterations),
                "final_beliefs": np.log(p + 1e-300), "status": "fake_zeros"}

    return decode


def _pattern_decoder(pattern):
    """Stateful fake: k-th call returns exact argmax iff ``pattern[k]``."""
    state = {"k": 0}

    def decode(h, prior, syndrome):
        k = state["k"]
        state["k"] += 1
        p = np.asarray(prior, dtype=np.float64)
        x = (np.argmax(p, axis=1).astype(np.int64) if pattern[k]
             else np.zeros(p.shape[0], dtype=np.int64))
        return {"x_hat": x, "syndrome_ok": True, "iterations": 1,
                "final_beliefs": np.log(p + 1e-300), "status": "fake_pattern"}

    return decode


class _ScriptedClock:
    """Deterministic clock: call k costs ``walls[k]`` seconds."""

    def __init__(self, walls):
        self.walls = list(walls)
        self.t = 0.0
        self.k = 0
        self._pending = None

    def __call__(self):
        if self._pending is None:
            self._pending = (self.walls[self.k] if self.k < len(self.walls)
                             else 0.0)
            return self.t
        self.t += self._pending
        self._pending = None
        self.k += 1
        return self.t


def _full_run(tmp_path, name="root", *, decoder=None, decoders=None,
              sampler=None, clock=None, rss_probe=None, joint=None,
              mothers=None, state=None, out_name=None, command_str="fake qualification"):
    out = Path(out_name) if out_name is not None else (tmp_path / name)
    if decoders is None:
        decoders = {"ROW_LAYERED": decoder or _argmax_decoder(),
                    "FLOODING": decoder or _argmax_decoder()}
    return d7d.run_schedule_discriminator(
        out_root=out,
        joint=_perfect_oracle_joint() if joint is None else joint,
        block_sampler=_sampler() if sampler is None else sampler,
        mothers=mothers,
        decoder_fns=decoders,
        state={"d7d_execution_authorized": True} if state is None else state,
        clock=clock,
        rss_probe=(rss_probe if rss_probe is not None
                   else (lambda: 256 * 1024 * 1024)),
        command_str=command_str, repo_root=REPO)


def _read_csv(path):
    with open(str(path), "r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _rewrite_csv(path, rows, fields):
    with open(str(path), "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _clean_env(extra=None):
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    if extra:
        env.update(extra)
    return env


def _dir_meta(path):
    path = Path(path)
    if not path.is_dir():
        return None
    return sorted((p.name, int(p.stat().st_size), int(p.stat().st_mtime_ns))
                  for p in path.iterdir())


def _run_cli(args, cwd, env=None):
    return subprocess.run([sys.executable] + args, cwd=str(cwd),
                          env=_clean_env(env), capture_output=True, text=True,
                          timeout=SUB_TIMEOUT)


# ==========================================================================
# F01-F08: flooding certification against the D7-A independent oracle
# ==========================================================================

def _clean(p):
    p = np.maximum(np.asarray(p, dtype=np.float64), 1e-15)
    return p / p.sum()


def _softmax(z):
    z = np.asarray(z, dtype=np.float64)
    z = z - z.max(axis=-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)


def _prod_flooding(h, prior, syn, max_iter):
    return v35.decode_flooding_fftqspa(
        np.asarray(h, dtype=np.uint8), np.asarray(prior, dtype=np.float64),
        np.asarray(syn, dtype=np.uint8), max_iter=int(max_iter), field=None)


def _ordinary_prior(n, offset=0):
    base = 1.0 + (np.arange(Q) + offset) % 7
    return np.tile(base / base.sum(), (n, 1))


def _skewed_prior(n, peak, mass=0.9):
    row = np.full(Q, (1.0 - mass) / (Q - 1))
    row[peak] = mass
    return np.tile(row, (n, 1))


def _indep_flooding(h, prior, syn, n_iter, check_fn=None):
    """Independently written flooding recurrence (oracle check updates)."""
    check_fn = check_fn or oracle.direct_check_to_var
    mat = np.asarray(h, dtype=np.int64)
    m, n = mat.shape
    syn = np.asarray(syn, dtype=np.int64).reshape(-1)
    edges = [[c for c in range(n) if int(mat[r, c]) != 0] for r in range(m)]
    coeffs = [[int(mat[r, c]) for c in edges[r]] for r in range(m)]
    logp = np.log(np.array([_clean(prior[i]) for i in range(n)]))
    c2v = [[np.zeros(Q) for _ in edges[r]] for r in range(m)]
    v2c = [[logp[c].copy() for c in edges[r]] for r in range(m)]
    beliefs = None
    for _ in range(int(n_iter)):
        for r in range(m):
            in_probs = [_softmax(v2c[r][j]) for j in range(len(edges[r]))]
            outs = check_fn(in_probs, coeffs[r], int(syn[r]))
            c2v[r] = [np.log(np.maximum(o, 1e-15)) for o in outs]
        beliefs = logp.copy()
        for r in range(m):
            for j, c in enumerate(edges[r]):
                beliefs[c] = beliefs[c] + c2v[r][j]
        for r in range(m):
            for j, c in enumerate(edges[r]):
                v2c[r][j] = beliefs[c] - c2v[r][j]
    return beliefs


def _wrong_direction_check(in_probs, coeffs, syndrome):
    cleaned = [_clean(p) for p in in_probs]
    outs = []
    for t, c in enumerate(coeffs):
        ci = int(oracle.INV_REF[int(c)])
        others = [j for j in range(len(coeffs)) if j != t]
        msg = np.zeros(Q)
        for v in range(Q):
            tgt = int(oracle.ADD_REF[syndrome, oracle.MUL_REF[ci, v]])
            total = 0.0
            import itertools
            for assign in itertools.product(range(Q), repeat=len(others)):
                acc = 0
                prod = 1.0
                for j, xj in zip(others, assign):
                    acc ^= int(oracle.MUL_REF[int(coeffs[j]), xj])
                    prod *= cleaned[j][xj]
                if acc == tgt:
                    total += prod
            msg[v] = total
        outs.append(np.maximum(msg, 1e-15))
    return [o / o.sum() for o in outs]


def _wrong_shift_check(in_probs, coeffs, syndrome):
    cleaned = [_clean(p) for p in in_probs]
    outs = []
    for t in range(len(coeffs)):
        others = [j for j in range(len(coeffs)) if j != t]
        msg = np.zeros(Q)
        for v in range(Q):
            tgt = int(oracle.ADD_REF[syndrome, v])
            total = 0.0
            import itertools
            for assign in itertools.product(range(Q), repeat=len(others)):
                acc = 0
                prod = 1.0
                for j, xj in zip(others, assign):
                    acc ^= int(oracle.MUL_REF[int(coeffs[j]), xj])
                    prod *= cleaned[j][xj]
                if acc == tgt:
                    total += prod
            msg[v] = total
        outs.append(np.maximum(msg, 1e-15))
    return [o / o.sum() for o in outs]


def test_s01_certification_doc_and_f_matrix_present():
    text = CERT_DOC.read_text(encoding="utf-8")
    for item in ("F01", "F02", "F03", "F04", "F05", "F06", "F07", "F08"):
        assert item in text, item
    assert text.count("PASS") >= 8
    for name in ("test_f01", "test_f02", "test_f03", "test_f04", "test_f05",
                 "test_f06", "test_f07", "test_f08"):
        assert any(name in n for n in globals()), name


def test_f01_direct_check_update_kernel_matches_certified_oracle():
    field = GF2mField.create(32)
    tables = v35._get_gf32_tables(field)
    worst = 0.0
    worst_case = None
    for coeff in (1, 2, 7, 13, 29, 31):
        for syn in (0, 5, 17, 31):
            priors = [_ordinary_prior(2).copy(), _skewed_prior(2, 5).copy()]
            ref = oracle.direct_check_to_var([priors[0][0], priors[1][0]],
                                             [1, coeff], syn)
            log_msgs = [np.log(priors[0][0]), np.log(priors[1][0])]
            prod = v35._check_update_log_batch(log_msgs, [1, coeff], syn,
                                               field, tables)
            for t in range(2):
                err = float(np.max(np.abs(_softmax(prod[t]) - ref[t])))
                if err > worst:
                    worst, worst_case = err, (1, coeff, syn, t)
    for coeffs in ((1, 2, 3), (2, 7, 13), (1, 13, 29)):
        for syn in (0, 17):
            prior = _ordinary_prior(3, offset=coeffs[0])
            ref = oracle.direct_check_to_var([prior[0], prior[1], prior[2]],
                                             list(coeffs), syn)
            log_msgs = [np.log(prior[0]), np.log(prior[1]), np.log(prior[2])]
            prod = v35._check_update_log_batch(log_msgs, list(coeffs), syn,
                                               field, tables)
            for t in range(3):
                err = float(np.max(np.abs(_softmax(prod[t]) - ref[t])))
                if err > worst:
                    worst, worst_case = err, (coeffs, syn, t)
    assert worst <= TOL, "F01 kernel mismatch %r at %r" % (worst, worst_case)


def test_f02_single_check_full_posterior_equals_enumeration():
    cases = (
        (np.array([[1, 7]], dtype=np.uint8), _skewed_prior(2, 17),
         np.array([5], dtype=np.uint8)),
        (np.array([[1, 2, 13]], dtype=np.uint8), _skewed_prior(3, 3),
         np.array([17], dtype=np.uint8)),
    )
    for h, prior, syn in cases:
        res = _prod_flooding(h, prior, syn, 90)
        assert res.iterations >= 1
        got = _softmax(res.final_beliefs)
        expected = oracle.exact_posterior(h, prior, syn)
        err = float(np.max(np.abs(got - expected)))
        assert err <= TOL, "F02 posterior mismatch %.3g" % (err,)
        assert np.allclose(got.sum(axis=1), 1.0, atol=1e-12)


def test_f03_two_check_tree_posterior_and_map_equal_enumeration():
    h = np.array([[1, 2, 0], [0, 3, 1]], dtype=np.uint8)
    rng = np.random.default_rng(2026091002)
    raw = rng.random((3, Q)) + 0.2
    prior = raw / raw.sum(axis=1, keepdims=True)
    x_map = np.argmax(prior, axis=1)
    syn = oracle.syndrome_reference(h, x_map)
    syn = np.array([(int(syn[0]) + 1) % Q, int(syn[1])], dtype=np.uint8)
    assert not np.array_equal(oracle.syndrome_reference(h, x_map), syn)
    res = _prod_flooding(h, prior, syn, 10)
    assert res.iterations >= 2, "tree fixture must require >=2 sweeps"
    expected = oracle.exact_posterior(h, prior, syn)
    err = float(np.max(np.abs(_softmax(res.final_beliefs) - expected)))
    assert err <= TOL, "F03 posterior mismatch %.3g" % (err,)
    assert np.array_equal(res.x_hat, np.argmax(expected, axis=1))
    assert res.syndrome_ok


def test_f04_one_iteration_matches_independent_flooding_recurrence():
    h = np.array([[2, 1, 0], [0, 3, 1], [1, 0, 5]], dtype=np.uint8)
    prior = _skewed_prior(3, 9)
    syn = np.array([5, 0, 17], dtype=np.uint8)
    res = _prod_flooding(h, prior, syn, 1)
    assert res.iterations == 1
    independent = _indep_flooding(h, prior, syn, 1)
    err = float(np.max(np.abs(_softmax(res.final_beliefs)
                              - _softmax(independent))))
    assert err <= TOL, "F04 recurrence mismatch %.3g" % (err,)
    h3 = np.array([[1, 2, 13]], dtype=np.uint8)
    prior3 = _skewed_prior(3, 3)
    syn3 = np.array([17], dtype=np.uint8)
    res3 = _prod_flooding(h3, prior3, syn3, 1)
    ind3 = _indep_flooding(h3, prior3, syn3, 1)
    err3 = float(np.max(np.abs(_softmax(res3.final_beliefs)
                               - _softmax(ind3))))
    assert err3 <= TOL, "F04 deg3 mismatch %.3g" % (err3,)


def test_f05_iterations_1_2_3_match_independent_loopy_bp():
    fixtures = (
        (np.array([[2, 1, 0], [0, 3, 1], [1, 0, 5]], dtype=np.uint8),
         _skewed_prior(3, 9), np.array([5, 0, 17], dtype=np.uint8)),
        (np.array([[1, 2, 0, 3], [0, 7, 1, 0], [5, 0, 1, 13]], dtype=np.uint8),
         _ordinary_prior(4), np.array([31, 5, 0], dtype=np.uint8)),
    )
    for h, prior, syn in fixtures:
        for k in (1, 2, 3):
            res = _prod_flooding(h, prior, syn, k)
            assert res.iterations == k, "fixture must not stop before %d" % (k,)
            independent = _indep_flooding(h, prior, syn, k)
            err = float(np.max(np.abs(_softmax(res.final_beliefs)
                                      - _softmax(independent))))
            assert err <= TOL, "F05 sweep %d mismatch %.3g" % (k, err)


def test_f06_nonzero_coefficients_and_syndromes_negative_controls(tmp_path):
    h = np.array([[3, 7]], dtype=np.uint8)
    prior = np.tile(np.full(Q, 0.1), (2, 1))
    prior[0, 5] = 0.9
    prior[1, 17] = 0.9
    prior = prior / prior.sum(axis=1, keepdims=True)
    syn = np.array([17], dtype=np.uint8)
    res = _prod_flooding(h, prior, syn, 1)
    good = _indep_flooding(h, prior, syn, 1)
    assert float(np.max(np.abs(_softmax(res.final_beliefs)
                               - _softmax(good)))) <= TOL
    wrong_c = _indep_flooding(h, prior, syn, 1, check_fn=_wrong_direction_check)
    wrong_s = _indep_flooding(h, prior, syn, 1, check_fn=_wrong_shift_check)
    err_c = float(np.max(np.abs(_softmax(res.final_beliefs)
                                - _softmax(wrong_c))))
    err_s = float(np.max(np.abs(_softmax(res.final_beliefs)
                                - _softmax(wrong_s))))
    assert err_c > 1e-6, "coefficient-direction control does not discriminate"
    assert err_s > 1e-6, "syndrome-shift control does not discriminate"
    assert all(int(c) != 0 for c in h[0]) and int(syn[0]) != 0
    # Nonzero-coefficient check with zero syndrome is covered by F01 (kernel).
    assert not (tmp_path / "root").exists()


def test_f07_cold_start_normalization_stopping_current_state_semantics():
    params = inspect.signature(v35.decode_flooding_fftqspa).parameters
    assert "damping_alpha" not in params and "warm_beliefs" not in params
    h = np.array([[2, 1, 0], [0, 3, 1], [1, 0, 5]], dtype=np.uint8)
    prior = _skewed_prior(3, 9)
    syn = np.array([5, 0, 17], dtype=np.uint8)
    # Cold start: the first sweep is seeded exactly by log(clean(prior)).
    res1 = _prod_flooding(h, prior, syn, 1)
    assert res1.iterations == 1
    assert float(np.max(np.abs(_softmax(res1.final_beliefs)
                               - _softmax(_indep_flooding(h, prior, syn, 1))))) <= TOL
    assert not np.allclose(res1.final_beliefs, np.log(prior), atol=1e-12)
    # Internal normalization: an unnormalized prior row gives identical output.
    res1b = _prod_flooding(h, prior * 3.7, syn, 1)
    assert np.allclose(res1.final_beliefs, res1b.final_beliefs, atol=1e-12)
    # Stopping: non-converging fixture sweeps exactly max_iter and stays open.
    res3 = _prod_flooding(h, prior, syn, 3)
    assert res3.iterations == 3 and not res3.syndrome_ok
    assert res3.status != "converged_exact"
    # final_beliefs are the current-state beliefs of the returned sweep.
    for k in (1, 2, 3):
        res = _prod_flooding(h, prior, syn, k)
        assert float(np.max(np.abs(_softmax(res.final_beliefs)
                                   - _softmax(_indep_flooding(h, prior, syn, k))))) <= TOL
    # Iteration-0 PRIOR_ONLY is real for the pair's row-layered schedule.
    assert d7d._belief_label(0) == d7d.PRIOR_ONLY_CURRENT_BELIEF
    assert d7d._belief_label(3) == d7d.CHECK_UPDATED_CURRENT_BELIEF
    h1 = np.array([[1, 7]], dtype=np.uint8)
    prior_cold = _skewed_prior(2, 0)  # MAP (0,0) satisfies syndrome 0
    cold = v35.decode_row_layered_fftqspa(
        h1, prior_cold, np.array([0], dtype=np.uint8), max_iter=3,
        damping_alpha=1.0, warm_beliefs=None, field=None)
    assert cold.iterations == 0 and cold.syndrome_ok
    assert cold.status == "converged_exact"


def test_f08_no_real_model_f_production_root_or_formal_root_read(monkeypatch):
    def _raiser(*args, **kwargs):
        raise AssertionError("Model-F loader must not run in certification")

    monkeypatch.setattr(d7d.d7c.d5, "_load_model_f_input_or_blocked", _raiser)
    monkeypatch.setattr(d7d.d7c, "_default_model_f_loader", _raiser)
    model_f_before = _dir_meta(MODEL_F_ROOT)
    # Tiny certification contacts run with the Model-F path poisoned.
    h = np.array([[1, 7]], dtype=np.uint8)
    res = _prod_flooding(h, _skewed_prior(2, 17),
                         np.array([5], dtype=np.uint8), 30)
    assert res.iterations >= 1
    assert float(np.max(np.abs(_softmax(res.final_beliefs)
                               - oracle.exact_posterior(
                                   h, _skewed_prior(2, 17),
                                   np.array([5], dtype=np.uint8))))) <= TOL
    assert _dir_meta(MODEL_F_ROOT) == model_f_before
    assert list(WS.glob(d7d.OUT_ROOT_PREFIX + "*")) == []
    assert not (WS / (d7d.OUT_ROOT_PREFIX + "certification_probe")).exists()
    assert d7d._EXECUTION_CONSUMED is False
    assert "workspace/v72p2d5_model_f_input/20260907_r1" in d7d.PROTECTED_ROOTS


# ==========================================================================
# S02-S09: frozen matrix, pair sharing, contract reuse, metrics
# ==========================================================================

def test_s02_exact_256_identities_and_order():
    identities = d7d.frozen_identities()
    calls = d7d.frozen_call_matrix()
    assert len(identities) == 128 and d7d.IDENTITY_COUNT == 128
    assert len(calls) == 256 and d7d.MAX_CALLS == 256
    assert d7d.SCHEDULES == ("ROW_LAYERED", "FLOODING")
    assert identities[0] == {"identity_idx": 1, "f": 1.0, "seed": 2026091300,
                             "condition": "L1_MARGINAL", "layer": "L1",
                             "rows": 49, "n": 64}
    assert identities[127] == {"identity_idx": 128, "f": 1.2,
                               "seed": 2026091315, "condition": "L2_ORACLE_U1",
                               "layer": "L2", "rows": 52, "n": 64}
    assert [c["call_idx"] for c in calls] == list(range(1, 257))
    for k, identity in enumerate(identities, start=1):
        left, right = calls[2 * k - 2], calls[2 * k - 1]
        for call in (left, right):
            assert call["identity_idx"] == k
            assert call["f"] == identity["f"] and call["seed"] == identity["seed"]
            assert call["condition"] == identity["condition"]
            assert call["layer"] == identity["layer"]
            assert call["rows"] == identity["rows"] and call["n"] == 64
        assert left["schedule"] == "ROW_LAYERED"
        assert right["schedule"] == "FLOODING"
        assert left["call_idx"] == 2 * k - 1 and right["call_idx"] == 2 * k
    keys = [(i["f"], i["seed"], i["condition"]) for i in identities]
    assert len(set(keys)) == 128
    assert [i["f"] for i in identities[:64]] == [1.0] * 64
    assert [i["f"] for i in identities[64:]] == [1.2] * 64
    for start in range(0, 128, 4):
        assert [i["condition"] for i in identities[start:start + 4]] == list(d7d.CONDITIONS)
        assert len({i["seed"] for i in identities[start:start + 4]}) == 1
    assert [i["rows"] for i in identities[:4]] == [49, 49, 43, 43]
    assert [i["rows"] for i in identities[64:68]] == [59, 59, 52, 52]


def test_s03_schedule_pairs_share_all_non_schedule_inputs(tmp_path):
    captured = {"ROW_LAYERED": [], "FLOODING": []}

    def make(schedule):
        def decoder(h, prior, syndrome):
            captured[schedule].append((np.array(h, copy=True),
                                       np.array(prior, copy=True),
                                       np.array(syndrome, copy=True)))
            return _argmax_decoder()(h, prior, syndrome)

        return decoder

    _full_run(tmp_path, decoders={"ROW_LAYERED": make("ROW_LAYERED"),
                                  "FLOODING": make("FLOODING")},
              out_name=tmp_path / "s03")
    assert len(captured["ROW_LAYERED"]) == 128
    assert len(captured["FLOODING"]) == 128
    for index, identity in enumerate(d7d.frozen_identities()):
        h_l, prior_l, syn_l = captured["ROW_LAYERED"][index]
        h_f, prior_f, syn_f = captured["FLOODING"][index]
        assert np.array_equal(h_l, h_f)
        assert np.array_equal(prior_l, prior_f)
        assert np.array_equal(syn_l, syn_f)
        assert h_l.shape == (identity["rows"], d7d.N)
        assert prior_l.shape == (d7d.N, d7d.Q)
        assert syn_l.shape == (identity["rows"],)
    # Frozen production call shapes carry the only per-schedule delta.
    fns = d7d.bind_schedule_decoders()
    assert fns["ROW_LAYERED"].target is v35.decode_row_layered_fftqspa
    assert fns["FLOODING"].target is v35.decode_flooding_fftqspa
    bind_src = inspect.getsource(d7d.bind_schedule_decoders)
    row_block = bind_src.split("def flooding")[0]
    flood_block = bind_src.split("def flooding")[1]
    assert "damping_alpha=DAMPING_ALPHA" in row_block
    assert "warm_beliefs=None" in row_block and "field=None" in row_block
    assert "damping_alpha" not in flood_block
    assert "warm_beliefs" not in flood_block
    assert "max_iter=MAX_ITER, field=None)" in flood_block
    assert d7d.MAX_ITER == 90 and d7d.DAMPING_ALPHA == 1.0
    source = CORE_PATH.read_text(encoding="utf-8")
    assert "DEFAULT_MAX_ITER" not in source


def test_s04_estimator_and_four_priors_equal_d7c_contract(monkeypatch):
    assert d7d.LAMBDA_STAR == 137.3823795883264 == d7c.LAMBDA_STAR
    assert d7d.DECODER_FLOOR == d7c.DECODER_FLOOR == 1e-15
    assert d7d.MAX_ITER == d7c.MAX_ITER == 90
    assert d7d._ESTIMATOR_ID == d7c._ESTIMATOR_ID
    assert d7d.condition_prior_qn is d7c.condition_prior_qn
    assert d7d.decoder_prior is d7c.decoder_prior
    assert d7d.build_joint is d7c.build_joint

    counts = np.ones((d7d.N_A, d7d.BOB_DIM), dtype=np.float64)
    p_b = np.full(d7d.BOB_DIM, 1.0 / d7d.BOB_DIM)
    calls = []
    original = d7c.d5.prepare_model_f_prior_candidate

    def spy(c_ab, p_b_in, lam=d7c.d5.LAMBDA_STAR):
        calls.append((np.asarray(c_ab).shape, np.asarray(p_b_in).shape,
                      float(lam)))
        return original(c_ab, p_b_in, lam)

    monkeypatch.setattr(d7c.d5, "prepare_model_f_prior_candidate", spy)

    def _forbidden(*args, **kwargs):
        raise AssertionError("rejected estimator path must never be called")

    monkeypatch.setattr(d7c.d5, "prepare_model_f_prior", _forbidden)
    monkeypatch.setattr(d7c.d5, "build_f_model", _forbidden)

    def loader(root):
        return {"counts_ab": counts, "p_b": p_b, "files": []}

    ctx = d7d.prepare_inputs(
        model_f_root=d7d.MODEL_F_ROOT, model_f_loader=loader,
        block_sampler=_sampler(), mothers=None, repo=REPO)
    assert calls == [((d7d.N_A, d7d.BOB_DIM), (d7d.BOB_DIM,),
                      d7d.LAMBDA_STAR)]
    assert ctx["joint"].shape == (Q, Q, d7d.BOB_DIM)
    # The four literal prior formulas agree with the D7-C contract.
    rng = np.random.default_rng(20260913)
    raw = rng.random((Q, Q, 5)) + 0.05
    joint = raw / raw.sum(axis=(0, 1), keepdims=True)
    bob = np.array([0, 4, 2, 3, 1, 4])
    u1 = np.array([3, 7, 31, 0, 15, 2])
    u2 = np.array([5, 1, 29, 8, 30, 6])
    block = {"bob": bob, "u1": u1, "u2": u2, "alice": u1 * Q + u2}
    want_l1_marginal = np.stack([joint[:, :, b].sum(axis=1) for b in bob], axis=1)
    want_l2_marginal = np.stack([joint[:, :, b].sum(axis=0) for b in bob], axis=1)
    assert np.allclose(d7d.condition_prior_qn(joint, "L1_MARGINAL", block),
                       want_l1_marginal, atol=1e-12, rtol=0)
    assert np.allclose(d7d.condition_prior_qn(joint, "L2_MARGINAL", block),
                       want_l2_marginal, atol=1e-12, rtol=0)
    for condition, truth_axis in (("L1_ORACLE_U2", u2), ("L2_ORACLE_U1", u1)):
        got = d7d.condition_prior_qn(joint, condition, block)
        assert np.allclose(got.sum(axis=0), 1.0, atol=1e-12)
        assert np.array_equal(got, d7c.condition_prior_qn(joint, condition, block))
        wrong = np.stack([joint[:, truth_axis[i], bob[i]] / joint[:, truth_axis[i], bob[i]].sum()
                          for i in range(6)], axis=1) if condition == "L1_ORACLE_U2" else None
        if wrong is not None:
            assert float(np.max(np.abs(got - wrong))) <= 1e-12
    # Boundary transpose + single floor equals the D7-C boundary.
    raw_prior = np.zeros((Q, 4))
    raw_prior[0, 0] = 1.0
    raw_prior[:, 1] = 1e-20
    assert np.array_equal(d7d.decoder_prior(raw_prior), d7c.decoder_prior(raw_prior))


def test_s05_rows_mothers_seeds_identical_to_d7c(tmp_path):
    assert d7d.BLOCK_SEEDS == d7c.BLOCK_SEEDS == tuple(range(2026091300, 2026091316))
    assert d7d.F_VALUES == d7c.F_VALUES == (1.0, 1.2)
    assert d7d.ROWS == d7c.ROWS
    assert d7d.L1_ROWS == {1.0: 49, 1.2: 59}
    assert d7d.L2_ROWS == {1.0: 43, 1.2: 52}
    assert d7d.L1_GRAPH_SEED == d7c.L1_GRAPH_SEED == 2026090501
    assert d7d.L2_GRAPH_SEED == d7c.L2_GRAPH_SEED == 2026090502
    assert d7d.L1_K_MIN == d7c.L1_K_MIN == 49
    assert d7d.L2_K_MIN == d7c.L2_K_MIN == 43
    assert d7d.CONDITIONS == d7c.CONDITIONS
    assert d7d.CONDITION_LAYER == d7c.CONDITION_LAYER
    d7c_identities = d7c.frozen_identities()
    for got, want in zip(d7d.frozen_identities(), d7c_identities):
        assert (got["f"], got["seed"], got["condition"], got["layer"],
                got["rows"], got["n"]) == (
            want["f"], want["seed"], want["condition"], want["layer"],
            want["rows"], want["n"])
    assert np.array_equal(d7d.build_mother("L1"), d7c.build_mother("L1"))
    assert np.array_equal(d7d.build_mother("L2"), d7c.build_mother("L2"))
    assert d7d.build_mother is d7c.build_mother  # narrow reuse, not a copy
    d7c_source = (SRC / "comparison_bench" / "formal_ir"
                  / "v72p2d7_gf32_bidirectional_oracle.py").read_text(encoding="utf-8")
    assert "build_dv3_nested_support(N, N, L1_K_MIN, L1_GRAPH_SEED)" in d7c_source
    assert "build_dv3_nested_support(N, N, L2_K_MIN, L2_GRAPH_SEED)" in d7c_source


def test_s06_exact_syndrome_separation():
    calls = d7d.frozen_call_matrix()
    identity = calls[0]  # rows=49 L1
    h = np.zeros((49, d7d.N), dtype=np.int64)
    h[:] = 1
    x_true = np.arange(d7d.N, dtype=np.int64) % Q
    syndrome = d7c.d5._gf32_syndrome(h, x_true)
    x_hat = x_true.copy()
    x_hat[0] = (x_hat[0] + 1) % Q
    x_hat[1] = (x_hat[1] - 1) % Q
    assert not np.array_equal(x_hat, x_true)
    assert np.array_equal(d7c.d5._gf32_syndrome(h, x_hat), syndrome)
    prior = np.full((d7d.N, Q), 1.0 / Q)
    block = {"bob": np.zeros(d7d.N, dtype=np.int64), "u1": x_true,
             "u2": np.zeros(d7d.N, dtype=np.int64)}
    result = {"x_hat": x_hat, "syndrome_ok": True, "iterations": 2,
              "final_beliefs": np.log(prior), "status": "fake"}
    layered = d7d.evaluate_call(identity, h, block, syndrome, result, 0.1, 1024)
    assert layered["exact"] is False and layered["syndrome_ok"] is True
    assert layered["symbol_errors"] == 2 and layered["unsatisfied_checks"] == 0
    flood_identity = calls[1]
    flooding = d7d.evaluate_call(flood_identity, h, block, syndrome,
                                 {"x_hat": np.zeros(d7d.N, dtype=np.int64),
                                  "syndrome_ok": False, "iterations": 1,
                                  "final_beliefs": np.log(prior),
                                  "status": "fake"}, 0.1, 1024)
    paired = d7d.compute_paired_rows([layered, flooding])
    row = [r for r in paired if r["identity_idx"] == 1][0]
    assert row["layered_exact"] is False and row["flooding_exact"] is False
    assert row["layered_only_syndrome_ok"] is True
    assert row["layered_only_exact"] is False
    strata = d7d.compute_strata([layered, flooding], paired)
    stratum = [s for s in strata if s["f"] == 1.0
               and s["condition"] == "L1_MARGINAL"][0]
    assert stratum["layered_only_syndrome_ok_count"] == 1
    assert stratum["layered_only_exact_count"] == 0
    assert stratum["stratum_label"] == ""


def test_s07_iteration_zero_provenance_labeling(tmp_path):
    assert d7d.CURRENT_BELIEF_LABELS == ("PRIOR_ONLY_CURRENT_BELIEF",
                                         "CHECK_UPDATED_CURRENT_BELIEF")
    calls = d7d.frozen_call_matrix()
    h = np.full((49, d7d.N), 1, dtype=np.int64)
    x_true = np.zeros(d7d.N, dtype=np.int64)
    syndrome = d7c.d5._gf32_syndrome(h, x_true)
    prior = np.full((d7d.N, Q), 1.0 / Q)
    block = {"bob": np.zeros(d7d.N, dtype=np.int64), "u1": x_true,
             "u2": np.zeros(d7d.N, dtype=np.int64)}
    for iterations, label, conditioned in (
            (0, d7d.PRIOR_ONLY_CURRENT_BELIEF, False),
            (3, d7d.CHECK_UPDATED_CURRENT_BELIEF, True)):
        record = d7d.evaluate_call(
            calls[0], h, block, syndrome,
            {"x_hat": x_true, "syndrome_ok": True, "iterations": iterations,
             "final_beliefs": np.log(prior), "status": "fake"}, 0.1, 1024)
        assert record["current_belief_label"] == label
        assert record["beliefs_conditioned"] is conditioned
        assert record["check_node_updates"] == 49 * iterations
        assert "posterior" not in record["current_belief_label"].lower()
        assert "app" not in record["current_belief_label"].lower()
    out = tmp_path / "s07"
    _full_run(tmp_path, decoder=_argmax_decoder(iterations=0),
              out_name=out)
    for record in _read_csv(out / "decoder_records.csv"):
        assert record["current_belief_label"] == d7d.PRIOR_ONLY_CURRENT_BELIEF
        assert record["beliefs_conditioned"] == "False"
        assert record["check_node_updates"] == "0"
        assert record["check_edge_updates"] == "0"
    source = CORE_PATH.read_text(encoding="utf-8")
    assert "PRIOR_ONLY_CURRENT_BELIEF" in source
    assert "CHECK_UPDATED_CURRENT_BELIEF" in source
    assert "warm_beliefs" in source  # only the frozen row-layered call shape


def test_s08_check_and_edge_update_arithmetic():
    calls = d7d.frozen_call_matrix()
    identity = calls[0]  # rows=49
    h = np.zeros((49, d7d.N), dtype=np.int64)
    h[0, :3] = [1, 2, 3]
    h[10, 5] = 7
    assert int(np.count_nonzero(h)) == 4
    x_true = np.zeros(d7d.N, dtype=np.int64)
    syndrome = d7c.d5._gf32_syndrome(h, x_true)
    prior = np.full((d7d.N, Q), 1.0 / Q)
    block = {"bob": np.zeros(d7d.N, dtype=np.int64), "u1": x_true,
             "u2": np.zeros(d7d.N, dtype=np.int64)}
    for iterations in (0, 7, 90):
        record = d7d.evaluate_call(
            identity, h, block, syndrome,
            {"x_hat": x_true, "syndrome_ok": True, "iterations": iterations,
             "final_beliefs": np.log(prior), "status": "fake"}, 0.25, 2048)
        assert record["check_node_updates"] == 49 * iterations
        assert record["check_edge_updates"] == 4 * iterations
    manifest = {"row_degree_sums": {"L1": {"49": 4, "59": 9},
                                    "L2": {"43": 2, "52": 2}}}
    good = d7d.evaluate_call(identity, h, block, syndrome,
                             {"x_hat": x_true, "syndrome_ok": True,
                              "iterations": 7, "final_beliefs": np.log(prior),
                              "status": "fake"}, 0.25, 2048)
    problems = []
    d7d._check_record_semantics(good, identity, problems,
                                manifest["row_degree_sums"])
    assert problems == []
    tampered = dict(good, check_edge_updates=good["check_edge_updates"] + 1)
    problems = []
    d7d._check_record_semantics(tampered, identity, problems,
                                manifest["row_degree_sums"])
    assert any("check_edge_updates" in p for p in problems)


def test_s09_no_winner_from_iterations_alone(tmp_path):
    for name in d7d.RECORD_FIELDS + d7d.PAIRED_FIELDS + d7d.STRATUM_FIELDS:
        assert "winner" not in name.lower()
        assert "advantage" not in name.lower() or name == "stratum_label"
    forward = _full_run(tmp_path, decoders={
        "ROW_LAYERED": _argmax_decoder(iterations=1),
        "FLOODING": _argmax_decoder(iterations=9)},
        out_name=tmp_path / "s09_forward")
    reverse = _full_run(tmp_path, decoders={
        "ROW_LAYERED": _argmax_decoder(iterations=9),
        "FLOODING": _argmax_decoder(iterations=1)},
        out_name=tmp_path / "s09_reverse")
    assert forward["terminal"] == reverse["terminal"]
    assert forward["summary"]["strata"] == reverse["summary"]["strata"]
    rows_f = _read_csv(tmp_path / "s09_forward" / "paired_schedule.csv")
    rows_r = _read_csv(tmp_path / "s09_reverse" / "paired_schedule.csv")
    assert rows_f[0]["iteration_diff"] == "8"
    assert rows_r[0]["iteration_diff"] == "-8"
    assert rows_f[0]["layered_exact"] == rows_r[0]["layered_exact"]
    params = inspect.signature(d7d.classify_stratum).parameters
    assert list(params) == ["flooding_only_exact", "layered_only_exact",
                            "both_exact", "neither_exact"]


# ==========================================================================
# S10-S14: classifications, terminals, caps, budgets, RSS
# ==========================================================================

def test_s10_five_stratum_classifications_and_boundaries():
    cs = d7d.classify_stratum
    assert cs(4, 1, 12, 0) == d7d.S_FLOODING
    assert cs(4, 2, 10, 0) == d7d.S_MIXED
    assert cs(3, 0, 13, 0) == d7d.S_MIXED
    assert cs(16, 0, 0, 0) == d7d.S_FLOODING
    assert cs(1, 4, 12, 0) == d7d.S_LAYERED
    assert cs(2, 4, 10, 0) == d7d.S_MIXED
    assert cs(0, 0, 12, 4) == d7d.S_TIE_HIGH
    assert cs(1, 1, 12, 2) == d7d.S_TIE_HIGH
    assert cs(0, 2, 12, 2) == d7d.S_MIXED
    assert cs(0, 0, 11, 5) == d7d.S_MIXED
    assert cs(0, 0, 4, 12) == d7d.S_TIE_LOW
    assert cs(1, 1, 2, 12) == d7d.S_TIE_LOW
    assert cs(1, 2, 2, 11) == d7d.S_MIXED
    assert cs(2, 2, 6, 6) == d7d.S_MIXED
    assert cs(0, 0, 0, 16) == d7d.S_TIE_LOW
    assert d7d.STRATUM_LABELS == ("FLOODING_EXACT_ADVANTAGE",
                                  "LAYERED_EXACT_ADVANTAGE", "EXACT_TIE_HIGH",
                                  "EXACT_TIE_LOW", "MIXED_SCHEDULE_EFFECT")


def _strata_map(labels):
    out = {}
    for f in d7d.F_VALUES:
        for condition in d7d.CONDITIONS:
            out[(f, condition)] = labels.get((f, condition),
                                             d7d.S_MIXED)
    return out


def test_s11_ten_terminal_priorities_and_boundaries():
    assert list(d7d.TERMINALS) == [
        "D7_D_PRE_EXECUTION_BLOCKED", "D7_D_WATCHDOG_TIMEOUT_VOID",
        "D7_D_NONFINITE_OR_CRASH_BLOCKED", "D7_D_RESOURCE_OVERRUN",
        "D7_D_INCOMPLETE_CALL_MATRIX", "D7_D_FLOODING_ADVANTAGE",
        "D7_D_LAYERED_ADVANTAGE", "D7_D_SCHEDULE_DEPENDENT_MIXED",
        "D7_D_SCHEDULE_NO_EXACT_DIFFERENCE",
        "D7_D_SCHEDULE_EFFECT_INCONCLUSIVE"]
    base = {"pre_blocked": False, "watchdog_timeout": False,
            "crash_nonfinite": False, "resource_overrun": False,
            "incomplete": False, "exact_flags_identical": False,
            "strata": _strata_map({})}
    assert d7d.classify_terminal(base) == d7d.T_INCONCLUSIVE
    for key, terminal in (("pre_blocked", d7d.T_PRE_EXEC),
                          ("watchdog_timeout", d7d.T_WATCHDOG),
                          ("crash_nonfinite", d7d.T_CRASH),
                          ("resource_overrun", d7d.T_RESOURCE),
                          ("incomplete", d7d.T_INCOMPLETE)):
        assert d7d.classify_terminal(dict(base, **{key: True})) == terminal
    everything = dict(base, pre_blocked=True, watchdog_timeout=True,
                      crash_nonfinite=True, resource_overrun=True,
                      incomplete=True)
    assert d7d.classify_terminal(everything) == d7d.T_PRE_EXEC
    assert d7d.classify_terminal(dict(everything, pre_blocked=False)) == d7d.T_WATCHDOG
    assert d7d.classify_terminal(dict(everything, pre_blocked=False,
                                      watchdog_timeout=False)) == d7d.T_CRASH
    assert d7d.classify_terminal(dict(everything, pre_blocked=False,
                                      watchdog_timeout=False,
                                      crash_nonfinite=False)) == d7d.T_RESOURCE
    # T6/T7 require two advantage strata and none in the other direction.
    one_flood = {(1.0, "L1_MARGINAL"): d7d.S_FLOODING}
    assert d7d.classify_terminal(dict(base, strata=_strata_map(one_flood))) == d7d.T_INCONCLUSIVE
    two_flood = {(1.0, "L1_MARGINAL"): d7d.S_FLOODING,
                 (1.0, "L2_MARGINAL"): d7d.S_FLOODING}
    assert d7d.classify_terminal(dict(base, strata=_strata_map(two_flood))) == d7d.T_FLOODING_ADV
    two_layer = {(1.0, "L1_MARGINAL"): d7d.S_LAYERED,
                 (1.2, "L2_ORACLE_U1"): d7d.S_LAYERED}
    assert d7d.classify_terminal(dict(base, strata=_strata_map(two_layer))) == d7d.T_LAYERED_ADV
    both = {(1.0, "L1_MARGINAL"): d7d.S_FLOODING,
            (1.2, "L2_ORACLE_U1"): d7d.S_LAYERED}
    assert d7d.classify_terminal(dict(base, strata=_strata_map(both))) == d7d.T_MIXED
    assert d7d.classify_terminal(dict(base, exact_flags_identical=True)) == d7d.T_NO_DIFF
    assert d7d.classify_terminal(dict(base, exact_flags_identical=False)) == d7d.T_INCONCLUSIVE


def test_s12_256_call_hard_cap_and_no_retry(tmp_path):
    calls = {"ROW_LAYERED": [], "FLOODING": []}

    def make(schedule):
        def decoder(h, prior, syndrome):
            calls[schedule].append(1)
            return _argmax_decoder()(h, prior, syndrome)

        return decoder

    result = _full_run(tmp_path, decoders={"ROW_LAYERED": make("ROW_LAYERED"),
                                           "FLOODING": make("FLOODING")},
                       out_name=tmp_path / "s12_full")
    assert result["records"] == 256
    assert len(calls["ROW_LAYERED"]) == 128 and len(calls["FLOODING"]) == 128
    assert d7d.MAX_CALLS == 256 and len(d7d.frozen_call_matrix()) == 256

    counter = {"n": 0}

    def crash_at_40(h, prior, syndrome):
        counter["n"] += 1
        if counter["n"] == 40:
            raise RuntimeError("boom")
        return _argmax_decoder()(h, prior, syndrome)

    result = _full_run(tmp_path, decoder=crash_at_40,
                       out_name=tmp_path / "s12_crash")
    assert counter["n"] == 40  # no retry, no replacement
    assert result["records"] == 40 and result["terminal"] == d7d.T_CRASH
    records = _read_csv(tmp_path / "s12_crash" / "decoder_records.csv")
    assert [int(r["call_idx"]) for r in records] == list(range(1, 41))
    assert records[-1]["status"].startswith("crash:")


def test_s13_budget_gates_120_1500_1800_2gib(tmp_path):
    assert d7d.PER_CALL_WATCHDOG_S == 120.0
    assert d7d.STORED_WALL_LIMIT_S == 1500.0
    assert d7d.OUTER_WATCHDOG_S == 1800.0 and d7d.OUTER_GRACE_S == 30.0
    assert d7d.RSS_LIMIT_BYTES == 2 * 1024**3
    walls = [120.0] + [0.0] * 255
    result = _full_run(tmp_path, clock=_ScriptedClock(walls),
                       out_name=tmp_path / "w120")
    assert result["records"] == 256 and result["terminal"] != d7d.T_WATCHDOG
    walls = [120.0001] + [0.0] * 255
    result = _full_run(tmp_path, clock=_ScriptedClock(walls),
                       out_name=tmp_path / "w121")
    assert result["terminal"] == d7d.T_WATCHDOG and result["records"] == 1
    walls = [6.25] * 240 + [0.0] * 16
    result = _full_run(tmp_path, clock=_ScriptedClock(walls),
                       out_name=tmp_path / "wall1500")
    assert result["records"] == 256 and result["terminal"] != d7d.T_RESOURCE
    summary = json.loads((tmp_path / "wall1500" / "summary.json")
                         .read_text(encoding="utf-8"))
    assert abs(float(summary["stored_wall_s"]) - 1500.0) <= 1e-9
    walls = [6.25] * 240 + [0.001] + [0.0] * 15
    result = _full_run(tmp_path, clock=_ScriptedClock(walls),
                       out_name=tmp_path / "wall1501")
    assert result["terminal"] == d7d.T_RESOURCE and result["records"] == 241
    result = _full_run(tmp_path, rss_probe=lambda: d7d.RSS_LIMIT_BYTES,
                       out_name=tmp_path / "rss2g")
    assert result["terminal"] == d7d.T_RESOURCE and result["records"] == 1


def test_s14_wsl_stdlib_rss_positive_and_fail_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(d7d, "_read_ru_maxrss", lambda: 123456)
    assert d7d.get_rss_bytes() == 123456 * 1024
    monkeypatch.setattr(d7d, "_read_ru_maxrss", lambda: None)
    assert d7d.get_rss_bytes() is None
    monkeypatch.setattr(d7d, "_read_ru_maxrss", lambda: float("nan"))
    assert d7d.get_rss_bytes() is None
    monkeypatch.setattr(d7d, "_read_ru_maxrss", lambda: -1)
    assert d7d.get_rss_bytes() == -1024  # rejected by preflight
    monkeypatch.undo()
    live = d7d.get_rss_bytes()
    assert live is not None and live > 0
    source = CORE_PATH.read_text(encoding="utf-8")
    assert "psutil" not in source and "import resource" in source

    for index, probe in enumerate((lambda: None, lambda: 0, lambda: -5,
                                   lambda: float("nan"), lambda: float("inf"))):
        events = []
        out = tmp_path / ("s14_%d" % index)

        def decoder(h, prior, syndrome):
            events.append("decode")
            return _argmax_decoder()(h, prior, syndrome)

        def sampler(p_b, p_f, n, seed):
            events.append("sample")
            return _perfect_oracle_block(seed)

        def model_f_loader(root):
            events.append("model_f")
            raise AssertionError("Model-F loader must not run")

        with pytest.raises(d7d.PreflightBlocked) as excinfo:
            d7d.run_schedule_discriminator(
                out_root=out, joint=_perfect_oracle_joint(),
                block_sampler=sampler, mothers=None,
                decoder_fns={"ROW_LAYERED": decoder, "FLOODING": decoder},
                model_f_loader=model_f_loader,
                state={"d7d_execution_authorized": True}, rss_probe=probe,
                repo_root=REPO)
        assert d7d.T_PRE_EXEC in str(excinfo.value)
        assert excinfo.value.terminal == d7d.T_PRE_EXEC
        assert events == []
        assert not out.exists()


# ==========================================================================
# S15-S18: seven-file writer/verifier, launch isolation, dual sentinels
# ==========================================================================

def test_s15_seven_file_schema_scalar_no_subdirs_no_overwrite(tmp_path):
    out = tmp_path / "s15"
    _full_run(tmp_path, out_name=out)
    assert sorted(p.name for p in out.iterdir()) == sorted(d7d.SEVEN_FILES)
    assert not any(p.is_dir() for p in out.iterdir())
    records = _read_csv(out / "decoder_records.csv")
    paired = _read_csv(out / "paired_schedule.csv")
    strata = _read_csv(out / "stratum_summary.csv")
    assert list(records[0].keys()) == d7d.RECORD_FIELDS
    assert list(paired[0].keys()) == d7d.PAIRED_FIELDS
    assert list(strata[0].keys()) == d7d.STRATUM_FIELDS
    assert len(records) == 256 and len(paired) == 128 and len(strata) == 8
    for row in records + paired + strata:
        for value in row.values():
            assert not str(value).startswith("[") and not str(value).startswith("{")
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert manifest["max_calls"] == 256 and manifest["schedules"] == ["ROW_LAYERED", "FLOODING"]
    assert manifest["call_order"] == d7d._CALL_ORDER
    assert (out / "report.md").read_text(encoding="utf-8").strip()
    assert (out / "command_log.txt").read_text(encoding="utf-8").strip()

    populated = tmp_path / "populated"
    populated.mkdir()
    (populated / "manifest.json").write_text("{}", encoding="utf-8")
    with pytest.raises(FileExistsError):
        d7d.write_root(populated, {}, [], [], [], {})
    empty_existing = tmp_path / "empty_existing"
    empty_existing.mkdir()
    with pytest.raises(FileExistsError):
        d7d.write_root(empty_existing, {}, [], [], [], {})
    subdir = tmp_path / "subdir"
    (subdir / "nested").mkdir(parents=True)
    with pytest.raises(ValueError):
        d7d.write_root(subdir, {}, [], [], [], {})

    complete = {key: "" for key in d7d.RECORD_FIELDS}
    complete.update({"call_idx": 1, "identity_idx": 1,
                     "schedule": "ROW_LAYERED", "f": 1.0,
                     "seed": 2026091300, "condition": "L1_MARGINAL",
                     "layer": "L1", "rows": 49, "n": 64})
    with pytest.raises(ValueError):
        d7d.write_root(tmp_path / "bad_extra", {}, [dict(complete, u1_vector=[1])], [], [], {})
    with pytest.raises(ValueError):
        d7d.write_root(tmp_path / "bad_array", {}, [dict(complete, wall_s=np.zeros(3))], [], [], {})

    existing = tmp_path / "existing"
    existing.mkdir()
    events = []

    def decoder(h, prior, syndrome):
        events.append("decode")
        return _argmax_decoder()(h, prior, syndrome)

    with pytest.raises(FileExistsError):
        d7d.run_schedule_discriminator(
            out_root=existing, joint=_perfect_oracle_joint(),
            block_sampler=_sampler(),
            decoder_fns={"ROW_LAYERED": decoder, "FLOODING": decoder},
            state={"d7d_execution_authorized": True}, repo_root=REPO)
    assert events == []
    with pytest.raises(ValueError):
        d7d.validate_production_out_root(tmp_path / "outside", repo_root=REPO)
    with pytest.raises(ValueError):
        d7d.validate_production_out_root(WS / "wrong_name", repo_root=REPO)
    assert d7d.validate_production_out_root(
        WS / (d7d.OUT_ROOT_PREFIX + "abc"), repo_root=REPO).name.endswith("abc")


def test_s16_verifier_detects_missing_duplicate_unpaired_tampered(tmp_path):
    good = tmp_path / "s16_good"
    _full_run(tmp_path, out_name=good)
    report = d7d.verify_root(good)
    assert report["ok"] and report["records"] == 256, report

    record_lines = (good / "decoder_records.csv").read_text(encoding="utf-8").splitlines()
    paired_lines = (good / "paired_schedule.csv").read_text(encoding="utf-8").splitlines()
    strata_lines = (good / "stratum_summary.csv").read_text(encoding="utf-8").splitlines()

    root = Path(shutil.copytree(str(good), str(tmp_path / "t_dup")))
    (root / "decoder_records.csv").write_text(
        "\n".join(record_lines + [record_lines[1]]) + "\n", encoding="utf-8")
    assert d7d.verify_root(root)["ok"] is False

    root = Path(shutil.copytree(str(good), str(tmp_path / "t_missing")))
    kept = [line for line in record_lines if not line.startswith("63,")]
    (root / "decoder_records.csv").write_text("\n".join(kept) + "\n", encoding="utf-8")
    assert d7d.verify_root(root)["ok"] is False

    root = Path(shutil.copytree(str(good), str(tmp_path / "t_unpaired")))
    kept = [line for line in record_lines if not line.startswith("2,")]
    (root / "decoder_records.csv").write_text("\n".join(kept) + "\n", encoding="utf-8")
    assert d7d.verify_root(root)["ok"] is False

    root = Path(shutil.copytree(str(good), str(tmp_path / "t_exact")))
    rows = _read_csv(root / "decoder_records.csv")
    for row in rows:
        if row["exact"] == "True":
            row["exact"] = "False"
            break
    _rewrite_csv(root / "decoder_records.csv", rows, d7d.RECORD_FIELDS)
    assert d7d.verify_root(root)["ok"] is False

    root = Path(shutil.copytree(str(good), str(tmp_path / "t_syndrome")))
    rows = _read_csv(root / "decoder_records.csv")
    row = next(r for r in rows if r["syndrome_ok"] == "False")
    row["syndrome_ok"] = "True"
    _rewrite_csv(root / "decoder_records.csv", rows, d7d.RECORD_FIELDS)
    assert d7d.verify_root(root)["ok"] is False

    root = Path(shutil.copytree(str(good), str(tmp_path / "t_edge")))
    rows = _read_csv(root / "decoder_records.csv")
    rows[4]["check_edge_updates"] = str(int(rows[4]["check_edge_updates"]) + 1)
    _rewrite_csv(root / "decoder_records.csv", rows, d7d.RECORD_FIELDS)
    assert d7d.verify_root(root)["ok"] is False

    root = Path(shutil.copytree(str(good), str(tmp_path / "t_paired")))
    rows = _read_csv(root / "paired_schedule.csv")
    row = next(r for r in rows if r["flooding_only_exact"] == "False")
    row["flooding_only_exact"] = "True"
    _rewrite_csv(root / "paired_schedule.csv", rows, d7d.PAIRED_FIELDS)
    assert d7d.verify_root(root)["ok"] is False

    root = Path(shutil.copytree(str(good), str(tmp_path / "t_strata")))
    lines = list(strata_lines)
    fields = lines[1].split(",")
    fields[-1] = "MIXED_SCHEDULE_EFFECT"
    lines[1] = ",".join(fields)
    (root / "stratum_summary.csv").write_text("\n".join(lines) + "\n",
                                              encoding="utf-8")
    assert d7d.verify_root(root)["ok"] is False

    root = Path(shutil.copytree(str(good), str(tmp_path / "t_terminal")))
    summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    summary["terminal"] = d7d.T_INCONCLUSIVE
    (root / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    assert d7d.verify_root(root)["ok"] is False

    root = Path(shutil.copytree(str(good), str(tmp_path / "t_manifest")))
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    manifest["lambda_star"] = 1.0
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert d7d.verify_root(root)["ok"] is False

    root = Path(shutil.copytree(str(good), str(tmp_path / "t_extra")))
    (root / "extra.txt").write_text("x", encoding="utf-8")
    assert d7d.verify_root(root)["ok"] is False

    # A legitimately truncated root (watchdog stop) still verifies.
    stopped = tmp_path / "s16_stopped"
    _full_run(tmp_path, clock=_ScriptedClock([120.5] + [0.0] * 255),
              out_name=stopped)
    assert d7d.verify_root(stopped)["ok"] is True


def test_s17_lazy_import_help_dry_run_and_unauthorized_isolation(tmp_path):
    external = tmp_path / "ext"
    external.mkdir()
    assert _run_cli([str(RUNNER), "--help"], cwd=REPO).returncode == 0
    result = _run_cli([str(RUNNER), "--help"], cwd=external)
    assert result.returncode == 0 and "D7-D" in result.stdout
    result = _run_cli([str(RUNNER), "--dry-run"], cwd=external)
    assert result.returncode == 0
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert lines[0].startswith("calls=256") and len(lines) == 257
    assert lines[1].split()[2] == "ROW_LAYERED"
    assert lines[2].split()[2] == "FLOODING"
    assert lines[256].split()[2] == "FLOODING"
    probe = (
        "import runpy, sys\n"
        "g = runpy.run_path(sys.argv[1], run_name='d7d_s17')\n"
        "assert g['main'](['--dry-run']) == 0\n"
        "assert 'v35_algorithm_development' not in sys.modules\n"
        "assert 'comparison_bench.formal_ir.v35_algorithm_development' not in sys.modules\n"
        "print('S17_OK')\n")
    result = subprocess.run([sys.executable, "-c", probe, str(RUNNER)],
                            cwd=str(external), env=_clean_env(),
                            capture_output=True, text=True, timeout=SUB_TIMEOUT)
    assert result.returncode == 0, result.stderr
    assert "S17_OK" in result.stdout

    target = WS / (d7d.OUT_ROOT_PREFIX + "unauthorized_probe_testonly")
    assert not target.exists()
    result = _run_cli([str(RUNNER), "--model-f-root", d7d.MODEL_F_ROOT,
                       "--out-root", str(target)], cwd=REPO)
    assert result.returncode == 3
    assert "not authorized" in result.stdout
    assert not target.exists()
    bad_shape = tmp_path / "bad_shape"
    result = _run_cli([str(RUNNER), "--model-f-root", d7d.MODEL_F_ROOT,
                       "--out-root", str(bad_shape)], cwd=REPO)
    assert result.returncode == 3 and "refused" in result.stdout
    assert not bad_shape.exists()
    missing = tmp_path / "no_such_root"
    result = _run_cli([str(RUNNER), "--verify", str(missing)], cwd=REPO)
    assert result.returncode == 2 and "VERIFY_FAIL" in result.stdout
    good = tmp_path / "s17_good"
    _full_run(tmp_path, out_name=good)
    result = _run_cli([str(RUNNER), "--verify", str(good)], cwd=REPO)
    assert result.returncode == 0 and "VERIFY_OK" in result.stdout


def test_s18_external_cwd_dual_decoder_sentinels(tmp_path):
    external = tmp_path / "ext"
    external.mkdir()
    out_root = tmp_path / "never_created"
    code = r'''
import pathlib
import runpy
import sys

import numpy as np

g = runpy.run_path(sys.argv[1], run_name="d7d_s18")
mod = g["_mod"]
external = pathlib.Path(sys.argv[2])
out_root = pathlib.Path(sys.argv[3])
from comparison_bench.formal_ir import v35_algorithm_development as v35

fns = mod.bind_schedule_decoders()
assert fns["ROW_LAYERED"].target is v35.decode_row_layered_fftqspa
assert fns["FLOODING"].target is v35.decode_flooding_fftqspa
assert fns["ROW_LAYERED"].__name__ == "row_layered"
assert fns["FLOODING"].__name__ == "flooding"


class Sentinel(BaseException):
    pass


events = []
h = np.zeros((2, 4), dtype=np.uint8)
h[0, :2] = [1, 7]
h[1, 2:] = [3, 1]
prior = np.full((4, 32), 1.0 / 32.0)
syn = np.array([5, 17], dtype=np.uint8)


def sentinel(tag):
    def dec(hh, pp, ss):
        events.append((tag, np.asarray(hh).shape, np.asarray(pp).shape,
                       np.asarray(ss).shape))
        raise Sentinel(tag)
    return dec


for schedule, tag in (("ROW_LAYERED", "row"), ("FLOODING", "flood")):
    try:
        mod.dispatch_schedule(schedule, {schedule: sentinel(tag)}, h, prior, syn)
    except Sentinel as exc:
        assert str(exc) == tag
    else:
        raise AssertionError("sentinel not reached for %s" % schedule)

assert events == [("row", (2, 4), (4, 32), (2,)),
                  ("flood", (2, 4), (4, 32), (2,))], events
assert not external.joinpath("never_created").exists()
assert not out_root.exists()
print("S18_OK")
'''
    result = subprocess.run(
        [sys.executable, "-c", code, str(RUNNER), str(external), str(out_root)],
        cwd=str(external), env=_clean_env(), capture_output=True, text=True,
        timeout=SUB_TIMEOUT)
    assert result.returncode == 0, result.stderr
    assert "S18_OK" in result.stdout


# ==========================================================================
# S19-S22: terminal-family qualification, regressions, lifecycle, isolation
# ==========================================================================

def test_s19_fake_full_256_qualification_each_terminal_family(tmp_path):
    peaked = _peaked_joint()
    sampler = _sampler(sampler_fn=_peaked_block)
    all_true = [True] * 128
    all_false = [False] * 128

    result = _full_run(tmp_path, joint=peaked, sampler=sampler, decoders={
        "ROW_LAYERED": _pattern_decoder(all_false),
        "FLOODING": _pattern_decoder(all_true)},
        out_name=tmp_path / "t6")
    assert result["records"] == 256 and result["terminal"] == d7d.T_FLOODING_ADV
    assert all(row["stratum_label"] == d7d.S_FLOODING
               for row in result["summary"]["strata"])
    assert d7d.verify_root(tmp_path / "t6")["ok"] is True

    result = _full_run(tmp_path, joint=peaked, sampler=sampler, decoders={
        "ROW_LAYERED": _pattern_decoder(all_true),
        "FLOODING": _pattern_decoder(all_false)},
        out_name=tmp_path / "t7")
    assert result["terminal"] == d7d.T_LAYERED_ADV

    result = _full_run(tmp_path, joint=peaked, sampler=sampler, decoders={
        "ROW_LAYERED": _pattern_decoder([k >= 64 for k in range(128)]),
        "FLOODING": _pattern_decoder([k < 64 for k in range(128)])},
        out_name=tmp_path / "t8")
    assert result["terminal"] == d7d.T_MIXED

    result = _full_run(tmp_path, joint=peaked, sampler=sampler, decoders={
        "ROW_LAYERED": _pattern_decoder(all_true),
        "FLOODING": _pattern_decoder(all_true)},
        out_name=tmp_path / "t9")
    assert result["terminal"] == d7d.T_NO_DIFF

    def _t10_exact(schedule, identity_idx):
        # Identities of one stratum are stride-4 (one per seed); key on the
        # seed block m = (identity_idx - 1) // 4 so every stratum is MIXED
        # (8 both, 4 flooding-only, 4 layered-only) and flags differ.
        m = (identity_idx - 1) // 4
        if m % 2 == 0:
            return True
        if m % 4 == 1:
            return schedule == "FLOODING"
        return schedule == "ROW_LAYERED"

    result = _full_run(tmp_path, joint=peaked, sampler=sampler, decoders={
        "ROW_LAYERED": _pattern_decoder([_t10_exact("ROW_LAYERED", i)
                                         for i in range(1, 129)]),
        "FLOODING": _pattern_decoder([_t10_exact("FLOODING", i)
                                      for i in range(1, 129)])},
        out_name=tmp_path / "t10")
    assert result["terminal"] == d7d.T_INCONCLUSIVE
    assert all(row["stratum_label"] == d7d.S_MIXED
               for row in result["summary"]["strata"])

    result = _full_run(tmp_path, clock=_ScriptedClock([120.5] + [0.0] * 255),
                       out_name=tmp_path / "t2")
    assert result["terminal"] == d7d.T_WATCHDOG

    def crash(h, prior, syndrome):
        raise RuntimeError("boom")

    result = _full_run(tmp_path, decoder=crash, out_name=tmp_path / "t3")
    assert result["terminal"] == d7d.T_CRASH

    result = _full_run(tmp_path, rss_probe=lambda: d7d.RSS_LIMIT_BYTES,
                       out_name=tmp_path / "t4")
    assert result["terminal"] == d7d.T_RESOURCE

    rows = _read_csv(tmp_path / "t10" / "decoder_records.csv")[:40]
    paired = d7d.compute_paired_rows(rows)
    strata = d7d.compute_strata(rows, paired)
    assert d7d.terminal_from_records(rows, paired, strata) == d7d.T_INCOMPLETE

    assert d7d.classify_terminal({"pre_blocked": True}) == d7d.T_PRE_EXEC
    events = []
    out = tmp_path / "t1"
    with pytest.raises(d7d.PreflightBlocked) as excinfo:
        d7d.run_schedule_discriminator(
            out_root=out, joint=_perfect_oracle_joint(),
            block_sampler=_sampler(),
            decoder_fns={"ROW_LAYERED": lambda h, p, s: events.append(1),
                         "FLOODING": lambda h, p, s: events.append(1)},
            state={"d7d_execution_authorized": True},
            rss_probe=lambda: 0, repo_root=REPO)
    assert excinfo.value.terminal == d7d.T_PRE_EXEC and events == []
    assert not out.exists()


def _inner_pytest(files, *, extra=(), basetemp):
    return subprocess.run(
        [sys.executable, "-m", "pytest", *files, "-q", "-p", "no:cacheprovider",
         "--basetemp", str(basetemp), *extra],
        cwd=str(REPO), env=dict(os.environ), capture_output=True, text=True,
        timeout=SUB_TIMEOUT)


def test_s20_related_regressions(tmp_path):
    base = tmp_path / "inner"
    base.mkdir()
    result = _inner_pytest([str(D7A_FILE)], basetemp=base / "d7a")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "14 passed" in result.stdout
    # Pre-existing stale lifecycle assertion: the accepted D7-C evidence root
    # now exists as frozen baseline, so C19's "no root" assertion is deselected.
    result = _inner_pytest(
        [str(D7C_FILE), "-k",
         "not test_c19_protected_root_lifecycle_and_g2_r1d_absence"],
        basetemp=base / "d7c")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "19 passed" in result.stdout and "1 deselected" in result.stdout
    result = _inner_pytest([str(D5_FILE)], basetemp=base / "d5")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "165 passed" in result.stdout
    result = _inner_pytest(
        [str(D7B_FILE), "-k",
         "not test_launch_l04_dry_run_both_cwds_no_bind_no_root and "
         "not test_launch_l12_roots_and_authorization_unchanged"],
        basetemp=base / "d7b")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "29 passed" in result.stdout
    result = _inner_pytest([str(V35_FILE)], basetemp=base / "v35")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "25 passed" in result.stdout


def test_s21_protected_root_lifecycle_and_d7bc_immutability(tmp_path):
    workspace_before = sorted(p.name for p in WS.iterdir())
    model_f_before = _dir_meta(MODEL_F_ROOT)
    d7c_before = _dir_meta(D7C_ROOT)
    d7b_before = _dir_meta(WS / "d7_b_easy_regime_c605d1e6-8577-4c52-a865-12500fc8c964")
    assert d7c_before is not None
    assert {name: size for name, size, _ in d7c_before} == D7C_ROOT_SIZES
    _full_run(tmp_path, out_name=tmp_path / "s21")
    assert sorted(p.name for p in WS.iterdir()) == workspace_before
    assert list(WS.glob(d7d.OUT_ROOT_PREFIX + "*")) == []
    assert _dir_meta(MODEL_F_ROOT) == model_f_before
    assert _dir_meta(D7C_ROOT) == d7c_before
    if d7b_before is not None:
        assert _dir_meta(WS / "d7_b_easy_regime_c605d1e6-8577-4c52-a865-12500fc8c964") == d7b_before
    assert not (WS / "v72p2d5_g2" / "20260906_r1").exists()
    assert list(WS.glob("d6_graph_mother_r1d_*")) == []
    assert d7d._EXECUTION_CONSUMED is False
    state = d7d.read_cycle_state(D7D_CYCLE_STATE)
    for key in ("d7d_execution_authorized", "decoder_executed", "result_created",
                "implementation_authorized", "formal_execution_authorized",
                "synthetic_execution_authorized", "real_execution_authorized",
                "scientific_promotion", "g1_authorized", "g2_authorized"):
        assert state.get(key) is False, (key, state.get(key))
    assert str(state.get("layer_interface_implementation", "")).startswith(
        "DEFERRED")
    d7c_state = d7d.read_cycle_state(D7C_CYCLE_STATE)
    # D7-C is the accepted predecessor: authorization false, one completed
    # execution and its immutable result recorded.
    assert d7c_state.get("d7c_execution_authorized") is False
    assert d7c_state.get("decoder_executed") is True
    assert d7c_state.get("result_created") is True
    assert d7c_state.get("d7c_execution_attempts") == "1"
    assert d7c_state.get("d7c_execution_completed") == "1"
    assert d7c_state.get("d7c_result_accepted") is True
    for key in ("formal_execution_authorized", "g1_authorized", "g2_authorized"):
        assert d7c_state.get(key) is False, (key, d7c_state.get(key))


def test_s22_no_forbidden_cross_layer_or_phase_paths(tmp_path):
    forbidden = (
        "app_fed_l2" + "_prior",
        "oracle_l2" + "_prior",
        "--" + "phase",
        "r1" + "d",
        "g1_" + "execution",
        "g2_" + "execution",
        "channel_" + "counts",
        "matrix_" + "payloads",
        "CAL-" + "TRAIN",
        "prepare_model_f_" + "prior(",
        "build_f_" + "model(",
        "REAL_" + "EXECUTION",
        "real_" + "execution",
        "workspace/" + "results",
    )
    for path in (CORE_PATH, RUNNER):
        source = path.read_text(encoding="utf-8").lower()
        for token in forbidden:
            assert token.lower() not in source, (path.name, token)
    source = CORE_PATH.read_text(encoding="utf-8")
    assert source.count("decode_row_layered_fftqspa(") == 2
    assert source.count("decode_flooding_fftqspa(") == 2
    for token in ("d7c.run_bidirectional_oracle", "d7c.write_root",
                  "d7c.verify_root", "d7c.bind_historical_decoder",
                  "d7c._default_model_f_loader", "d7c._default_model_f_loader("):
        assert token not in source, token
    runner_source = RUNNER.read_text(encoding="utf-8")
    assert "verify_root" in runner_source
    assert not (tmp_path / "root").exists()
