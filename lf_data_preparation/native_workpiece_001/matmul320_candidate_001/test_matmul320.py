"""Three isolated candidate regressions; no force, tangent or equilibrium call.

The two selected cases retain the captured, unscaled DD matrix operands. Their
reference is an independent exact Decimal dot product, including both words.
"""
from decimal import Decimal, Inexact, localcontext
from hashlib import sha256
from pathlib import Path
import sys

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[3]
STAGE = ROOT / "lf_data_preparation/native_workpiece_001/matmul320_candidate_001"
RUNTIME = STAGE / "runtime/hf_repo/src"
CAPTURE = ROOT / ("lf_data_preparation/native_workpiece_001/coarse_square_cycle_002/"
                  "range_diagnostic_001/evidence/first_bad_primitive.npz")
CAPTURE_SHA256 = "bc2bae73881cdd0a4ff74d204bee0736d3a125b1e6e5e0e969d2128ce98342d2"
KERNEL_SHA256 = "7fff354270a276764445b45a281a5924fd9f0356236b89e0dbd4f00088b383ce"
sys.path.insert(0, str(RUNTIME))

from hf_eval import compensated_invariants as ci
from hf_eval import split_kernel_invariants_hu as kernel


@pytest.fixture(scope="module")
def captured():
    assert Path(kernel.__file__).resolve() == RUNTIME / "hf_eval/split_kernel_invariants_hu.py"
    assert Path(ci.__file__).resolve() == RUNTIME / "hf_eval/compensated_invariants.py"
    assert sha256(Path(kernel.__file__).read_bytes()).hexdigest() == KERNEL_SHA256
    assert sha256(CAPTURE.read_bytes()).hexdigest() == CAPTURE_SHA256
    with np.load(CAPTURE, allow_pickle=False) as source:
        assert source["frame4_selected"].item() is True
        return {name: source["frame4_" + name].copy()
                for name in ("a_hi", "a_lo", "b_hi", "b_lo")}


def check_captured_dot(captured, cell, quadrature):
    a = tuple(captured[name][cell, quadrature] for name in ("a_hi", "a_lo"))
    b = tuple(captured[name][cell, quadrature] for name in ("b_hi", "b_lo"))
    actual = kernel._scaled_matmul(a, b, True, np)
    assert bool(ci.pair_supported(actual, np))
    assert all(word.shape == (2, 2) and np.isfinite(word).all() for word in actual)
    # Captured binary64 values have finite decimal expansions. Precision 2000
    # exceeds their exact dot-product length; Inexact must remain unset.
    with localcontext() as context:
        context.prec = 2000
        context.clear_flags()
        d = lambda value: Decimal.from_float(float(value))
        for i in range(2):
            for j in range(2):
                terms = [(d(a[0][i, k]) + d(a[1][i, k])) *
                         (d(b[0][k, j]) + d(b[1][k, j])) for k in range(2)]
                expected = sum(terms, Decimal(0))
                represented = d(actual[0][i, j]) + d(actual[1][i, j])
                scale = sum(map(abs, terms), Decimal(0))
                # 64*binary64-epsilon**2 permits DD rounding over two products
                # and one sum. No absolute floor conceals a small matrix entry.
                bound = Decimal(2) ** -98 * scale
                assert not context.flags[Inexact]
                assert abs(represented - expected) <= bound, (cell, quadrature, i, j)


def test_captured_solid_cell_1275_quadrature_6(captured):
    check_captured_dot(captured, 1275, 6)


def test_captured_solid_cell_1348_quadrature_8(captured):
    check_captured_dot(captured, 1348, 8)


def test_unselected_matrix_keeps_both_words_bytewise(captured):
    a = (np.array([[1., .75], [.25, -.5]]),
         np.array([[1., -1.], [1., 1.]]) * 2.0**-60)
    b = (np.array([[.5, -.25], [.75, 1.]]),
         np.array([[-1., 1.], [1., -1.]]) * 2.0**-60)
    expected = ci.dd_matmul(a, b, np)
    actual = kernel._scaled_matmul(a, b, False, np)
    assert bool(ci.pair_supported(expected, np))
    for word, reference in zip(actual, expected, strict=True):
        assert word.dtype == reference.dtype and word.shape == reference.shape
        assert word.tobytes(order="C") == reference.tobytes(order="C")
