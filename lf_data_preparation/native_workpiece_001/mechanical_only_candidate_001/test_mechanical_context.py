"""Preserved matmul probes and two unselected-response byte regressions.

These are isolated unit regressions, not new F16 HP or cycle qualification.
The two small response cases invoke NumPy force entries, with no tangent/solver.
"""
from decimal import Decimal, Inexact, localcontext
import importlib.util
from hashlib import sha256
from pathlib import Path
import sys

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parent
RUNTIME = STAGE / "runtime/hf_repo/src"
CAPTURE = ROOT / ("lf_data_preparation/native_workpiece_001/coarse_square_cycle_002/"
                  "range_diagnostic_001/evidence/first_bad_primitive.npz")
CAPTURE_SHA256 = "bc2bae73881cdd0a4ff74d204bee0736d3a125b1e6e5e0e969d2128ce98342d2"
KERNEL_SHA256 = "d5f7d20a6ec0c92847d67f8782f4dcc89772fc4ea62797626b0beae7effabd9a"
BASELINE_SHA256 = "7fff354270a276764445b45a281a5924fd9f0356236b89e0dbd4f00088b383ce"
CI_SHA256 = "8115e1032e45a3178f399a904cce9b9b0cc0c9297638cc5b7a035fbe29b57081"
sys.path.insert(0, str(RUNTIME))

from hf_eval import compensated_invariants as ci
from hf_eval import split_kernel_invariants_hu as kernel
from hf_eval.tmc_kernel import operators

spec = importlib.util.spec_from_file_location("hf_eval._horner192_baseline", STAGE / "baseline_core.py")
baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)


@pytest.fixture(autouse=True)
def forbid_compilation(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Isolated NumPy regression invoked compiled work")
    for module in (kernel, baseline):
        for name in ("_runtime", "_batch_with_tangent", "_batch_without_tangent"):
            monkeypatch.setattr(module, name, forbidden)


@pytest.fixture(scope="module")
def captured():
    assert Path(kernel.__file__).resolve() == RUNTIME / "hf_eval/split_kernel_invariants_hu.py"
    assert Path(ci.__file__).resolve() == RUNTIME / "hf_eval/compensated_invariants.py"
    assert sha256(Path(kernel.__file__).read_bytes()).hexdigest() == KERNEL_SHA256
    assert kernel.MECHANICAL_KERNEL_VERSION == "p26_q1_split_mechanical_numpy_aux_omitted_candidate1"
    assert sha256(Path(ci.__file__).read_bytes()).hexdigest() == CI_SHA256
    assert Path(baseline.__file__).resolve() == STAGE / "baseline_core.py"
    assert sha256(Path(baseline.__file__).read_bytes()).hexdigest() == BASELINE_SHA256
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


@pytest.mark.parametrize("amplitude,expected_near", [(2.0**-10, True), (1.0/8, False)],
                         ids=["near_but_not_tiny", "direct_branch"])
def test_unselected_response_keeps_all_fields_bytewise(captured, amplitude, expected_near):
    xy = np.array([[0., 0.], [1., 0.], [1., 1.], [0., 1.]])
    lift, w = np.zeros((1, 8)), (amplitude * xy).reshape(1, 8)
    ops, lam, mu, kr = operators(1., 1.), np.array([2.]), np.array([3.]), 1./8
    expected = baseline.batch_response_split_numpy(lift, w, ops, lam, mu, kr)
    actual = kernel.batch_response_split_numpy(lift, w, ops, lam, mu, kr)
    assert np.all(actual["small_branch"] == float(expected_near))
    assert not bool(kernel._small_product_branch(
        (actual["G_hi"], actual["G_lo"]), actual["small_branch"].astype(bool),
        (ops["grad"], ops["hessian"], ops["weights"], lam, mu, kr)))
    assert actual.keys() == expected.keys() and "material_energy" in actual
    for name in actual:
        assert actual[name].dtype == expected[name].dtype and actual[name].shape == expected[name].shape
        assert actual[name].tobytes(order="C") == expected[name].tobytes(order="C"), name
